"""Socket handlers for the poker table.

Everything a seat is sent goes to that seat's own socket. A poker projection
carries hole cards, so a room broadcast would deal everyone else's hand face up
to the table; there is a test that says so.

Kept in its own module because events.py is already two thousand lines. The
helpers it needs from there are imported inside the functions, so the two
modules do not have to import each other at load time.
"""
from __future__ import annotations

import asyncio
import logging
import time

from app.db.session import SessionLocal
from app.models.room import Room
from app.models.room_player import RoomPlayer
from app.services import poker
from app.services.game_state import ROOM_STATES, PLAYER_TO_SID, RoomGameState

_logger = logging.getLogger(__name__)


async def start_poker_game(sio, db, room: Room, players: list[RoomPlayer], names: dict[int, str]) -> RoomGameState:
    """Seat everyone, deal the first hand, and start the clock."""
    state = RoomGameState(
        room_id=room.id,
        room_code=room.code,
        rounds_total=1,
        turn_seconds=int(poker.ACTION_SECONDS),
        difficulty=room.difficulty,
        game_type="poker",
        player_order=[player.id for player in players],
        scores={player.id: 0 for player in players},
        origin=room.origin or "friends",
    )
    state.poker_names = dict(names)
    state.poker = poker.new_table(state.player_order, room.starting_chips, room.small_blind)
    ROOM_STATES[room.code] = state
    room.status = "active"

    # The frontend navigates on this, the way it does for every other game.
    await sio.emit("game:turn_start", {
        "game_type": "poker",
        "round_index": 1,
        "turn_seconds": int(poker.ACTION_SECONDS),
        "turn_start_ts": int(time.time()),
        "describer_id": -1,
    }, room=room.code)

    await publish(sio, state)
    _arm(sio, state)
    return state


async def publish(sio, state: RoomGameState) -> None:
    """Send every seated player the view they are allowed to have."""
    if not state.poker:
        return
    for seat_id in state.player_order:
        sid = PLAYER_TO_SID.get(seat_id)
        if not sid:
            continue
        await sio.emit("poker:state", poker.projection_for(state.poker, seat_id, state.poker_names), to=sid)


def register_poker_handlers(sio) -> None:
    @sio.on("poker:action")
    async def poker_action(sid, data):  # noqa: ANN001 - socket.io handler
        from app.sockets.events import emit_error, _save_state

        room_code = (data or {}).get("room_code")
        state = ROOM_STATES.get(room_code)
        if not state or state.game_type != "poker" or not state.poker:
            await emit_error(sid, "No poker table here", code="NOT_FOUND")
            return {"ok": False, "error": "NOT_FOUND"}

        seat_id = _seat_of(sid)
        if seat_id is None or seat_id not in state.player_order:
            await emit_error(sid, "You are not at this table", code="FORBIDDEN")
            return {"ok": False, "error": "FORBIDDEN"}

        async with state.lock:
            updated, ack = poker.submit(
                state.poker,
                seat_id,
                (data or {}).get("action") or {},
                expected_revision=(data or {}).get("expected_revision"),
                idempotency_key=(data or {}).get("idempotency_key"),
            )
            if not ack.get("ok"):
                await emit_error(sid, ack.get("detail") or ack["error"], code=ack["error"])
                return ack
            state.poker = updated
            with SessionLocal() as db:
                _save_state(db, state)
                db.commit()

        await publish(sio, state)
        _arm(sio, state)
        return ack

    @sio.on("poker:next_hand")
    async def poker_next_hand(sid, data):  # noqa: ANN001 - socket.io handler
        room_code = (data or {}).get("room_code")
        state = ROOM_STATES.get(room_code)
        if not state or state.game_type != "poker" or not state.poker:
            return {"ok": False, "error": "NOT_FOUND"}
        if not poker.is_complete(state.poker):
            return {"ok": False, "error": "HAND_IN_PROGRESS"}
        await _deal_next(sio, state)
        return {"ok": True}


def _seat_of(sid: str) -> int | None:
    for player_id, mapped in PLAYER_TO_SID.items():
        if mapped == sid:
            return player_id
    return None


def _arm(sio, state: RoomGameState) -> None:
    """One clock runs at a time: the seat to act, or the pause before the deal."""
    if state.task and not state.task.done():
        state.task.cancel()
    if not state.poker:
        return
    state.task = asyncio.create_task(_clock(sio, state))


async def _clock(sio, state: RoomGameState) -> None:
    try:
        blob = state.poker or {}
        deadline = blob.get("deadline_ts") or blob.get("reveal_ts")
        if deadline is None:
            return
        await asyncio.sleep(max(0.0, deadline - time.time()))
        if state.poker is not blob:
            return  # somebody acted; a new clock is already running
        if poker.is_complete(blob):
            await _deal_next(sio, state)
            return
        async with state.lock:
            updated, ack = poker.fold_for_timeout(blob)
            if not ack.get("ok"):
                return
            state.poker = updated
            with SessionLocal() as db:
                _save_state_lazy(db, state)
        await publish(sio, state)
        _arm(sio, state)
    except asyncio.CancelledError:  # pragma: no cover - ordinary cancellation
        raise
    except Exception:  # pragma: no cover - a dead clock must not kill the table
        _logger.exception("poker clock failed for room %s", state.room_code)


async def _deal_next(sio, state: RoomGameState) -> None:
    async with state.lock:
        following = poker.deal_next(state.poker or {})
        if following is None:
            await _finish(sio, state)
            return
        state.poker = following
        with SessionLocal() as db:
            _save_state_lazy(db, state)
    await publish(sio, state)
    _arm(sio, state)


async def _finish(sio, state: RoomGameState) -> None:
    """One seat has all the chips, so the session is over."""
    from app.sockets.events import _auto_end_game

    chips = poker.stacks(state.poker or {})
    # Net chips won or lost is the score a poker session leaves behind.
    starting = sum(chips.values()) // max(1, len(state.player_order))
    state.scores = {seat_id: chips.get(seat_id, 0) - starting for seat_id in state.player_order}
    winner = max(chips, key=lambda seat: chips[seat], default=None)
    state.poker = None
    if state.task and not state.task.done():
        state.task.cancel()
    await _auto_end_game(state, state.room_code, winner_player_id=winner)


def _save_state_lazy(db, state: RoomGameState) -> None:
    from app.sockets.events import _save_state

    _save_state(db, state)
    db.commit()
