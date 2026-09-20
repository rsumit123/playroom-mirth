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
from app.services.poker_ai import seats as house

_logger = logging.getLogger(__name__)


async def start_poker_game(
    sio,
    db,
    room: Room,
    players: list[RoomPlayer],
    names: dict[int, str],
    ai_seats: dict[int, str] | None = None,
) -> RoomGameState:
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
    state.poker_seats = dict(ai_seats or {})
    state.poker_reads = {}
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
    _nudge_house(sio, state)
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
        _nudge_house(sio, state)
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
        _nudge_house(sio, state)
    except asyncio.CancelledError:  # pragma: no cover - ordinary cancellation
        raise
    except Exception:  # pragma: no cover - a dead clock must not kill the table
        _logger.exception("poker clock failed for room %s", state.room_code)


async def _deal_next(sio, state: RoomGameState) -> None:
    async with state.lock:
        if state.poker and state.poker_seats:
            # What each seat showed about itself, which is the only thing a
            # house player remembers between hands.
            house.remember(state.poker_reads, state.poker)
        following = poker.deal_next(state.poker or {})
        if following is None:
            await _finish(sio, state)
            return
        state.poker = following
        with SessionLocal() as db:
            _save_state_lazy(db, state)
    await publish(sio, state)
    _arm(sio, state)
    _nudge_house(sio, state)


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


def _nudge_house(sio, state: RoomGameState) -> None:
    """If the seat that owes an action is a model, let it think."""
    if not state.poker or not state.poker_seats:
        return
    seat_id = poker.current_seat(state.poker)
    tier = state.poker_seats.get(seat_id)
    if seat_id is None or not tier:
        return
    asyncio.create_task(_play_house_turn(sio, state, seat_id, tier))


async def _play_house_turn(sio, state: RoomGameState, seat_id: int, tier: str) -> None:
    blob = state.poker
    try:
        action = await house.decide(blob, seat_id, tier, state.poker_reads, state.poker_names)
        if state.poker is not blob:
            return  # the table moved on while it was thinking
        async with state.lock:
            updated, ack = poker.submit(blob, seat_id, action)
            if not ack.get("ok"):
                updated, ack = poker.fold_for_timeout(blob)
                if not ack.get("ok"):
                    return
            state.poker = updated
            with SessionLocal() as db:
                _save_state_lazy(db, state)
        await publish(sio, state)
        _arm(sio, state)
        _nudge_house(sio, state)
    except asyncio.CancelledError:  # pragma: no cover
        raise
    except Exception:  # pragma: no cover - one bad turn must not stop the table
        _logger.exception("house player at seat %s failed its turn", seat_id)


def register_poker_lobby_handlers(sio) -> None:
    """Seating and unseating house players, before the first hand."""

    @sio.on("poker:add_bot")
    async def poker_add_bot(sid, data):  # noqa: ANN001 - socket.io handler
        from app.services.room_ops import lobby_state
        from app.sockets.events import emit_error, get_user_from_token, resolve_guest

        payload = data or {}
        tier = payload.get("tier") or house.GUEST_TIER
        with SessionLocal() as db:
            room = db.query(Room).filter(Room.code == payload.get("room_code")).first()
            if not room or room.game_type != "poker":
                await emit_error(sid, "No poker table here", code="NOT_FOUND")
                return {"ok": False, "error": "NOT_FOUND"}
            if room.status != "lobby":
                return {"ok": False, "error": "ALREADY_STARTED"}

            user = get_user_from_token(db, payload.get("token"))
            guest = resolve_guest(db, payload.get("guest_token"))
            host = (user and room.host_user_id == user.id) or (guest and room.host_guest_id == guest.id)
            if not host:
                await emit_error(sid, "Only the host can seat a model", code="FORBIDDEN")
                return {"ok": False, "error": "FORBIDDEN"}

            # Every decision costs money, so a guest gets the cheap seat and
            # somebody who signed in can pick.
            if not house.is_allowed(tier, signed_in=bool(user)):
                await emit_error(sid, "Sign in to seat that one", code="TIER_NOT_ALLOWED")
                return {"ok": False, "error": "TIER_NOT_ALLOWED"}

            seated = db.query(RoomPlayer).filter(RoomPlayer.room_id == room.id).all()
            if len(seated) >= room.max_players:
                return {"ok": False, "error": "TABLE_FULL"}

            from app.services.bot_users import pick_random_bot

            bot = pick_random_bot(db, exclude_user_ids={p.user_id for p in seated if p.user_id})
            db.add(RoomPlayer(
                room_id=room.id,
                user_id=bot.id,
                guest_id=None,
                join_order=max((p.join_order for p in seated), default=0) + 1,
                score=0,
                connected=True,
                in_game=True,
                ai_tier=tier,
            ))
            db.commit()
            lobby = lobby_state(db, room)
        await sio.emit("room:lobby_update", lobby.model_dump(), room=room.code)
        return {"ok": True, "tier": tier}
