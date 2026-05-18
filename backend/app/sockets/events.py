import logging
import socketio
from jose import jwt, JWTError

from app.core.config import JWT_SECRET_KEY, JWT_ALGORITHM
from app.db.session import SessionLocal
from app.models.user import User
from app.models.room import Room
from app.schemas.room import RoomCreateRequest, RoomCreateGuestRequest, RoomJoinRequest
from app.services.room_ops import (
    resolve_guest,
    create_room_for_user,
    create_room_for_guest,
    join_room as join_room_op,
    lobby_state as build_lobby_state,
)
import asyncio

from app.models.room_state import RoomState
from app.services.game_state import (
    ROOM_STATES,
    SID_TO_PLAYER,
    PLAYER_TO_SID,
    PLAYER_TO_ROOM,
    PLAYER_GRACE_TASKS,
    USER_ONLINE,
    RoomGameState,
    start_turn,
    serialize_state,
    deserialize_state,
)
from app.models.room_player import RoomPlayer
from app.models.game_history import GameHistory
from app.models.guest import Guest
from app.models.word import Word
from app.api.rooms import PLAY_AGAIN_REST
from app.services.trivia import generate_round_questions, generate_gk_round_questions
from sqlalchemy import func as sa_func
import time
import random

from app.services import matchmaker
from app.services.bot_users import pick_random_bot
from app.services import trivia_bot

_logger = logging.getLogger("charade.sio")

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

# Play-again vote tracking: room_code -> {player_ids: set, total: int, task: asyncio.Task}
PLAY_AGAIN_VOTES: dict[str, dict] = {}


def _resolve_winner(state) -> int | None:
    """Return the player_id with the highest score, or None on tie/empty."""
    if not state.scores:
        return None
    max_score = max(state.scores.values())
    leaders = [pid for pid, s in state.scores.items() if s == max_score]
    if len(leaders) == 1:
        return leaders[0]
    return None




def get_user_from_token(db, token: str | None):
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        subject = payload.get("sub")
        if subject is None:
            return None
    except JWTError:
        return None
    return db.query(User).filter(User.id == int(subject)).first()


async def emit_error(sid: str, message: str, code: str = "ERROR"):
    await sio.emit("error", {"code": code, "message": message}, to=sid)


def _save_state(db, state: RoomGameState) -> None:
    existing = db.query(RoomState).filter(RoomState.room_id == state.room_id).first()
    payload = serialize_state(state)
    if existing:
        existing.state_json = payload
    else:
        db.add(RoomState(room_id=state.room_id, state_json=payload))
    db.commit()


def _save_game_history(db, state: RoomGameState) -> None:
    """Persist game results for all players (including guests)."""
    _logger.debug("save_game_history room=%s type=%s players=%s scores=%s", state.room_code, state.game_type, state.player_order, state.scores)
    player_ids = state.player_order
    players = db.query(RoomPlayer).filter(RoomPlayer.id.in_(player_ids)).all()
    max_score = max(state.scores.values(), default=0)
    player_count = len(player_ids)

    # Compute game_number for this room
    current_max = db.query(sa_func.max(GameHistory.game_number)).filter(
        GameHistory.room_code == state.room_code
    ).scalar()
    game_number = (current_max or 0) + 1

    # Resolve display names
    user_ids = [rp.user_id for rp in players if rp.user_id]
    user_name_map: dict[int, str] = {}
    if user_ids:
        users = db.query(User).filter(User.id.in_(user_ids)).all()
        for u in users:
            user_name_map[u.id] = u.display_name or u.email.split("@")[0]

    guest_ids = [rp.guest_id for rp in players if rp.guest_id]
    guest_name_map: dict[int, str] = {}
    if guest_ids:
        guests = db.query(Guest).filter(Guest.id.in_(guest_ids)).all()
        for g in guests:
            guest_name_map[g.id] = g.display_name or f"Guest {g.id}"

    guest_counter = 0
    for rp in players:
        score = state.scores.get(rp.id, 0)
        # Resolve display name
        if rp.user_id and rp.user_id in user_name_map:
            display_name = user_name_map[rp.user_id]
        elif rp.guest_id and rp.guest_id in guest_name_map:
            display_name = guest_name_map[rp.guest_id]
        else:
            guest_counter += 1
            display_name = f"Guest {guest_counter}"

        db.add(GameHistory(
            user_id=rp.user_id or 0,
            room_code=state.room_code,
            game_type=state.game_type,
            score=score,
            player_count=player_count,
            is_winner=(score == max_score and max_score > 0),
            guest_id=rp.guest_id,
            display_name=display_name,
            game_number=game_number,
            origin=state.origin or "friends",
        ))


async def _auto_end_game(state: RoomGameState, room_code: str, winner_player_id: int | None = None) -> None:
    """End game when no connected players remain. Caller MUST hold state.lock."""
    # NOTE: do NOT cancel state.task — this may be called from within the timer task.
    # Pop BEFORE emit so room:register can't find stale state during the emit
    ROOM_STATES.pop(room_code, None)
    winner = winner_player_id if winner_player_id is not None else _resolve_winner(state)
    await sio.emit("game:game_end", {"scores": state.scores, "winner_player_id": winner}, room=room_code)
    try:
        with SessionLocal() as db:
            db.query(RoomState).filter(RoomState.room_id == state.room_id).delete()
            _save_game_history(db, state)
            room = db.query(Room).filter(Room.code == room_code).first()
            if room:
                room.status = "lobby"
                db.query(RoomPlayer).filter(RoomPlayer.room_id == room.id).update({RoomPlayer.in_game: False})
            db.commit()
    except Exception:
        _logger.exception("Error saving game history for %s", room_code)


async def _schedule_turn_timer(state: RoomGameState, override_seconds: float | None = None) -> None:
    if state.task and not state.task.done():
        state.task.cancel()

    async def _timer():
        if override_seconds is not None:
            await asyncio.sleep(override_seconds)
        else:
            remaining = state.turn_seconds - (time.time() - state.turn_start_ts)
            if remaining > 0:
                await asyncio.sleep(remaining)
        await _advance_turn(state.room_code)

    state.task = asyncio.create_task(_timer())


async def _emit_next_turn(state: RoomGameState, room_code: str) -> None:
    """Select a word, emit turn_start + new_word, schedule timer."""
    # Skip disconnected describers (but not those in grace period who may reconnect)
    for _ in range(len(state.player_order)):
        describer_id = state.player_order[state.describer_index]
        if PLAYER_TO_SID.get(describer_id):
            break  # connected
        grace_task = PLAYER_GRACE_TASKS.get(describer_id)
        if grace_task and not grace_task.done():
            break  # in grace period, give them the turn (word sent on reconnect)
        # Truly disconnected — skip to next player
        state.describer_index += 1
        if state.describer_index >= len(state.player_order):
            state.describer_index = 0
            state.round_index += 1
        if state.round_index > state.rounds_total:
            await _auto_end_game(state, room_code)
            return
    else:
        # All players disconnected
        await _auto_end_game(state, room_code)
        return

    start_turn(state)

    describer_id = state.player_order[state.describer_index]
    describer_sid = PLAYER_TO_SID.get(describer_id)

    if state.game_type == "scribble":
        # Scribble: offer 3 word choices to the drawer
        choice_words = []
        with SessionLocal() as db:
            for _ in range(3):
                w = _select_word(db, state.difficulty, state.word_history_ids + [cw["id"] for cw in choice_words], state.game_type)
                if w:
                    choice_words.append({"text": w.text, "id": w.id})
            if not choice_words:
                w = _select_word(db, state.difficulty, [], state.game_type)
                if w:
                    choice_words.append({"text": w.text, "id": w.id})
            state._word_choices = {cw["text"]: cw["id"] for cw in choice_words}
            _save_state(db, state)

        await sio.emit(
            "game:turn_start",
            {
                "describer_id": describer_id,
                "turn_seconds": state.turn_seconds,
                "turn_start_ts": int(state.turn_start_ts),
                "round_index": state.round_index,
                "game_type": state.game_type,
                "choosing": True,
            },
            room=room_code,
        )
        if describer_sid and choice_words:
            await sio.emit("game:word_choices", {"words": [cw["text"] for cw in choice_words]}, to=describer_sid)
        # Timer starts after word is picked (in game:word_pick handler)
        # Schedule a fallback timer (15s) in case drawer doesn't pick
        await _schedule_turn_timer(state, override_seconds=15)
    else:
        # Charades: select one word immediately
        with SessionLocal() as db:
            word = _select_word(db, state.difficulty, state.word_history_ids, state.game_type)
            if word:
                state.current_word_id = word.id
                state.current_word_text = word.text
                state.word_history_ids.append(word.id)
            _save_state(db, state)

        hint = _generate_hint(state.current_word_text) if state.current_word_text else None
        await sio.emit(
            "game:turn_start",
            {
                "describer_id": describer_id,
                "turn_seconds": state.turn_seconds,
                "turn_start_ts": int(state.turn_start_ts),
                "round_index": state.round_index,
                "game_type": state.game_type,
                "hint": hint,
            },
            room=room_code,
        )
        if describer_sid and state.current_word_text:
            await sio.emit("game:new_word", {"word": state.current_word_text}, to=describer_sid)
            await _schedule_turn_timer(state)
        elif not describer_sid:
            # Describer in grace period — use shorter timer (15s) to limit dead time
            _logger.info("Describer %s has no SID (grace period), using 15s timer", describer_id)
            await _schedule_turn_timer(state, override_seconds=15)
        else:
            await _schedule_turn_timer(state)


async def _advance_turn(room_code: str) -> None:
    state = ROOM_STATES.get(room_code)
    if not state:
        return
    async with state.lock:
        # Safety: if no players are connected, end the game
        if not any(PLAYER_TO_SID.get(pid) for pid in state.player_order):
            await _auto_end_game(state, room_code)
            return

        # Award scribble drawer bonus for any guesses this turn
        if state.game_type == "scribble" and state.guessed_players:
            describer_id = state.player_order[state.describer_index]
            num_guessed = len(state.guessed_players)
            state.scores[describer_id] = state.scores.get(describer_id, 0) + 3 * num_guessed

        state.describer_index += 1
        round_ended = False
        if state.describer_index >= len(state.player_order):
            state.describer_index = 0
            state.round_index += 1
            round_ended = True

        if state.round_index > state.rounds_total:
            # NOTE: do NOT cancel state.task here — _advance_turn runs inside the
            # timer task, so cancelling it would abort this code path (CancelledError).
            # Pop BEFORE emit so room:register can't find stale state during the emit
            ROOM_STATES.pop(room_code, None)
            await sio.emit("game:game_end", {"scores": state.scores, "winner_player_id": _resolve_winner(state)}, room=room_code)
            try:
                with SessionLocal() as db:
                    db.query(RoomState).filter(RoomState.room_id == state.room_id).delete()
                    _save_game_history(db, state)
                    room = db.query(Room).filter(Room.code == room_code).first()
                    if room:
                        room.status = "lobby"
                        db.query(RoomPlayer).filter(RoomPlayer.room_id == room.id).update({RoomPlayer.in_game: False})
                    db.commit()
            except Exception:
                _logger.exception("Error saving game history for %s", room_code)
            return

        if round_ended:
            # Pause at round boundary — wait for host to trigger next round
            if state.task and not state.task.done():
                state.task.cancel()
            with SessionLocal() as db:
                _save_state(db, state)
            await sio.emit(
                "game:round_end",
                {"round_index": state.round_index - 1, "scores": state.scores},
                room=room_code,
            )
            return

        # Same round, next player — start immediately
        await _emit_next_turn(state, room_code)

@sio.event
async def connect(sid, environ, auth):
    # Accept connection; auth is validated per event.
    return True


@sio.event
async def disconnect(sid):
    player_id = SID_TO_PLAYER.get(sid)
    room_code = PLAYER_TO_ROOM.get(player_id) if player_id else None
    if player_id and room_code:
        grace_seconds = 60
        await sio.emit(
            "game:reconnect_grace",
            {"player_id": player_id, "expires_at": int(time.time() + grace_seconds)},
            room=room_code,
        )
        with SessionLocal() as db:
            rp = db.query(RoomPlayer).filter(RoomPlayer.id == player_id).first()
            if rp:
                rp.connected = False
                db.commit()
        # schedule removal after grace period
        if player_id in PLAYER_GRACE_TASKS and not PLAYER_GRACE_TASKS[player_id].done():
            PLAYER_GRACE_TASKS[player_id].cancel()
        async def _remove_after_grace():
            await asyncio.sleep(grace_seconds)
            with SessionLocal() as db:
                rp = db.query(RoomPlayer).filter(RoomPlayer.id == player_id).first()
                if rp and not rp.connected:
                    rp.in_game = False
                    db.commit()
                else:
                    return  # player reconnected
            await sio.emit("game:player_removed", {"player_id": player_id}, room=room_code)
            # Clean up in-memory game state
            state = ROOM_STATES.get(room_code)
            if not state or player_id not in state.player_order:
                return
            async with state.lock:
                if player_id not in state.player_order:
                    return
                idx = state.player_order.index(player_id)
                was_describer = (idx == state.describer_index)
                state.player_order.remove(player_id)
                if not state.player_order:
                    await _auto_end_game(state, room_code)
                    return
                if was_describer:
                    if state.task and not state.task.done():
                        state.task.cancel()
                    if state.describer_index >= len(state.player_order):
                        state.describer_index = 0
                    if state.game_type != "trivia":
                        await _emit_next_turn(state, room_code)
                elif idx < state.describer_index:
                    state.describer_index -= 1
                with SessionLocal() as db:
                    _save_state(db, state)
        task = asyncio.create_task(_remove_after_grace())
        PLAYER_GRACE_TASKS[player_id] = task
    SID_TO_PLAYER.pop(sid, None)
    if player_id:
        PLAYER_TO_SID.pop(player_id, None)
    # Drop from quickmatch queue if present (must run before SID_TO_USER pop).
    _qm_user_id = SID_TO_USER.get(sid)
    if _qm_user_id and _qm_user_id in matchmaker.USER_IN_QUEUE:
        await matchmaker.cancel_queue(_qm_user_id)
    # Clean up presence tracking
    user_id = SID_TO_USER.pop(sid, None)
    if user_id and user_id in USER_ONLINE:
        USER_ONLINE[user_id].discard(sid)
        if not USER_ONLINE[user_id]:
            del USER_ONLINE[user_id]


@sio.event
async def ping(sid, data):
    await sio.emit("pong", {"ok": True}, to=sid)


# ── Presence tracking ─────────────────────────────────────────────────
# Maps socket SID -> user_id for online status.
# A user is "online" if they have any SID in USER_ONLINE[user_id].
SID_TO_USER: dict[str, int] = {}


@sio.on("presence:connect")
async def presence_connect(sid, data):
    """Register a signed-in user for online presence tracking."""
    token = data.get("token")
    if not token:
        return
    with SessionLocal() as db:
        user = get_user_from_token(db, token)
        if not user:
            return
    SID_TO_USER[sid] = user.id
    if user.id not in USER_ONLINE:
        USER_ONLINE[user.id] = set()
    USER_ONLINE[user.id].add(sid)


@sio.on("room:register")
async def room_register(sid, data):
    """Register an existing socket with a room after REST-based create/join."""
    room_code = data.get("room_code")
    if not room_code:
        await emit_error(sid, "room_code required", code="BAD_REQUEST")
        return {"ok": False}
    with SessionLocal() as db:
        room = db.query(Room).filter(Room.code == room_code).first()
        if not room:
            await emit_error(sid, "Room not found", code="NOT_FOUND")
            return {"ok": False}
        token = data.get("token")
        guest_token = data.get("guest_token")
        user = get_user_from_token(db, token)
        guest = resolve_guest(db, guest_token)
        if not user and not guest:
            await emit_error(sid, "Authentication required", code="UNAUTHORIZED")
            return {"ok": False}
        if user:
            rp = (
                db.query(RoomPlayer)
                .filter(RoomPlayer.room_id == room.id, RoomPlayer.user_id == user.id)
                .order_by(RoomPlayer.join_order.desc())
                .first()
            )
        else:
            rp = (
                db.query(RoomPlayer)
                .filter(RoomPlayer.room_id == room.id, RoomPlayer.guest_id == guest.id)
                .order_by(RoomPlayer.join_order.desc())
                .first()
            )
        if not rp:
            await emit_error(sid, "Player not in room", code="NOT_FOUND")
            return {"ok": False}
    await sio.enter_room(sid, room_code)
    SID_TO_PLAYER[sid] = rp.id
    PLAYER_TO_SID[rp.id] = sid
    PLAYER_TO_ROOM[rp.id] = room_code
    task = PLAYER_GRACE_TASKS.get(rp.id)
    if task and not task.done():
        try:
            task.cancel()
        except RuntimeError:
            pass
    with SessionLocal() as db2:
        rp2 = db2.query(RoomPlayer).filter(RoomPlayer.id == rp.id).first()
        if rp2:
            rp2.connected = True
            db2.commit()
        room2 = db2.query(Room).filter(Room.code == room_code).first()
        if room2:
            lobby = build_lobby_state(db2, room2, self_player_id=rp.id)
            await sio.emit("room:lobby_update", lobby.model_dump(), room=room_code)
    # If a game is active, send current turn state to the reconnecting player
    state = ROOM_STATES.get(room_code)
    if state and rp.id in state.player_order:
        if state.game_type == "trivia":
            # Trivia reconnection: send navigation trigger + current question
            await sio.emit("game:turn_start", {
                "game_type": "trivia",
                "round_index": state.round_index,
                "turn_seconds": 0,
                "turn_start_ts": int(state.question_start_ts),
                "describer_id": -1,
            }, to=sid)
            if state.trivia_questions and state.current_question_index < len(state.trivia_questions):
                q = state.trivia_questions[state.current_question_index]
                await sio.emit("trivia:question", {
                    "question_index": state.current_question_index,
                    "total_questions": len(state.trivia_questions),
                    "question_text": q["question"],
                    "options": q["options"],
                    "time_seconds": q["time_seconds"],
                    "round_index": state.round_index,
                }, to=sid)
        else:
            describer_id = state.player_order[state.describer_index]
            hint = _generate_hint(state.current_word_text) if state.current_word_text else None
            await sio.emit(
                "game:turn_start",
                {
                    "describer_id": describer_id,
                    "turn_seconds": state.turn_seconds,
                    "turn_start_ts": int(state.turn_start_ts),
                    "round_index": state.round_index,
                    "game_type": state.game_type,
                    "hint": hint,
                },
                to=sid,
            )
            # Scribble reconnection: replay strokes or resend word choices
            if state.game_type == "scribble" and state.strokes:
                await sio.emit("scribble:stroke_replay", {"strokes": state.strokes}, to=sid)
            word_choices = getattr(state, '_word_choices', {})
            if state.game_type == "scribble" and word_choices and rp.id == describer_id:
                await sio.emit("game:word_choices", {"words": list(word_choices.keys())}, to=sid)
            if rp.id == describer_id and state.current_word_text:
                await sio.emit("game:new_word", {"word": state.current_word_text}, to=sid)
                # Restart turn with full timer since describer just reconnected
                state.turn_start_ts = time.time()
                await sio.emit("game:turn_start", {
                    "describer_id": describer_id,
                    "turn_seconds": state.turn_seconds,
                    "turn_start_ts": int(state.turn_start_ts),
                    "round_index": state.round_index,
                    "game_type": state.game_type,
                    "hint": hint,
                }, room=room_code)
                await _schedule_turn_timer(state)
    return {"ok": True}


@sio.on("room:create")
async def room_create(sid, data):
    with SessionLocal() as db:
        token = data.get("token")
        guest_token = data.get("guest_token")
        user = get_user_from_token(db, token)
        if user:
            payload = RoomCreateRequest.model_validate(data)
            lobby = create_room_for_user(db, user.id, payload)
            rp = (
                db.query(RoomPlayer)
                .filter(RoomPlayer.room_id == lobby.room.id, RoomPlayer.user_id == user.id)
                .order_by(RoomPlayer.join_order.desc())
                .first()
            )
        else:
            payload = RoomCreateGuestRequest.model_validate(data)
            guest = resolve_guest(db, guest_token)
            if not guest:
                await emit_error(sid, "Invalid guest token", code="UNAUTHORIZED")
                return {"ok": False, "error": "UNAUTHORIZED"}
            lobby = create_room_for_guest(db, payload)
            rp = (
                db.query(RoomPlayer)
                .filter(RoomPlayer.room_id == lobby.room.id, RoomPlayer.guest_id == guest.id)
                .order_by(RoomPlayer.join_order.desc())
                .first()
            )

    await sio.enter_room(sid, lobby.room.code)
    if rp:
        SID_TO_PLAYER[sid] = rp.id
        PLAYER_TO_SID[rp.id] = sid
        PLAYER_TO_ROOM[rp.id] = lobby.room.code
        task = PLAYER_GRACE_TASKS.get(rp.id)
        if task and not task.done():
            try:
                task.cancel()
            except RuntimeError:
                pass
    await sio.emit("room:lobby_update", lobby.model_dump(), room=lobby.room.code)
    return {"ok": True, "lobby": lobby.model_dump()}


@sio.on("room:join")
async def room_join(sid, data):
    with SessionLocal() as db:
        payload = RoomJoinRequest.model_validate(data)
        room = db.query(Room).filter(Room.code == payload.room_code).first()
        if not room:
            await emit_error(sid, "Room not found", code="NOT_FOUND")
            return {"ok": False, "error": "NOT_FOUND"}
        if room.origin == "quickmatch":
            await emit_error(sid, "Room not found", code="NOT_FOUND")
            return {"ok": False, "error": "NOT_FOUND"}

        user = get_user_from_token(db, data.get("token"))
        guest = resolve_guest(db, data.get("guest_token"))
        if not user and not guest:
            await emit_error(sid, "Authentication required", code="UNAUTHORIZED")
            return {"ok": False, "error": "UNAUTHORIZED"}

        lobby = join_room_op(db, room, user.id if user else None, guest)
        if user:
            rp = (
                db.query(RoomPlayer)
                .filter(RoomPlayer.room_id == room.id, RoomPlayer.user_id == user.id)
                .order_by(RoomPlayer.join_order.desc())
                .first()
            )
        else:
            rp = (
                db.query(RoomPlayer)
                .filter(RoomPlayer.room_id == room.id, RoomPlayer.guest_id == guest.id)
                .order_by(RoomPlayer.join_order.desc())
                .first()
            )

    await sio.enter_room(sid, lobby.room.code)
    if rp:
        SID_TO_PLAYER[sid] = rp.id
        PLAYER_TO_SID[rp.id] = sid
        PLAYER_TO_ROOM[rp.id] = lobby.room.code
        task = PLAYER_GRACE_TASKS.get(rp.id)
        if task and not task.done():
            try:
                task.cancel()
            except RuntimeError:
                pass
    await sio.emit("room:lobby_update", lobby.model_dump(), room=lobby.room.code)
    return {"ok": True, "lobby": lobby.model_dump()}


def _normalize_word(word: str) -> str:
    return word.strip().lower()


def _is_plural_variation(token: str, target: str) -> bool:
    if token == f"{target}s" or token == f"{target}es":
        return True
    if target == f"{token}s" or target == f"{token}es":
        return True
    return False


def _hint_contains_target(hint: str, target: str) -> bool:
    hint_l = hint.lower()
    target_l = target.lower()
    tokens = [t for t in "".join(c if c.isalnum() else " " for c in hint_l).split() if t]
    for tok in tokens:
        if tok == target_l:
            return True
        if _is_plural_variation(tok, target_l):
            continue
        if target_l in tok or tok in target_l:
            return True
    return False


def _scribble_guess_score(elapsed: float) -> int:
    if elapsed < 5:
        return 15
    if elapsed < 10:
        return 12
    if elapsed < 20:
        return 10
    if elapsed < 30:
        return 7
    return 5


def _generate_hint(word: str) -> str:
    """Generate a hangman-style hint: first letter revealed, rest as underscores."""
    parts = []
    for w in word.split(' '):
        if not w:
            continue
        chars = [w[0].upper()] + ['_'] * (len(w) - 1)
        parts.append(' '.join(chars))
    return '  '.join(parts)


def _select_word(db, difficulty: int, history_ids: list[int], game_type: str = "charades") -> Word | None:
    base = db.query(Word).filter(Word.active.is_(True), Word.game_type == game_type, ~Word.id.in_(history_ids))
    if difficulty == 0:
        # Mixed mode: 20% easy, 50% medium, 30% hard
        roll = random.random()
        pick_diff = 1 if roll < 0.2 else (2 if roll < 0.7 else 3)
        word = base.filter(Word.difficulty == pick_diff).order_by(sa_func.random()).first()
        if word:
            return word
        return base.order_by(sa_func.random()).first()
    word = base.filter(Word.difficulty == difficulty).order_by(sa_func.random()).first()
    if word:
        return word
    return base.order_by(sa_func.random()).first()


# ── Trivia helpers ──────────────────────────────────────────────────

async def _trivia_start_round(state: RoomGameState, room_code: str) -> None:
    """Generate questions for this round and send the first one."""
    _GK_SUBCATEGORIES = {"science", "history", "geography", "sports", "entertainment", "general", "mythology", "food", "politics", "defense", "current_affairs"}
    if state.trivia_category == "general_knowledge" or state.trivia_category in _GK_SUBCATEGORIES:
        subcategory = state.trivia_category if state.trivia_category in _GK_SUBCATEGORIES else None
        questions = generate_gk_round_questions(
            state.difficulty, count=10, used_ids=state.used_question_ids,
            subcategory=subcategory,
        )
        for q in questions:
            if "id" in q:
                state.used_question_ids.add(q["id"])
    else:
        questions = generate_round_questions(state.difficulty, count=10)
    state.trivia_questions = questions
    state.current_question_index = 0
    state.player_answers = {}
    with SessionLocal() as db:
        _save_state(db, state)
    await _trivia_send_question(state, room_code)


async def _trivia_send_question(state: RoomGameState, room_code: str) -> None:
    """Emit current question to all players and start per-question timer."""
    q = state.trivia_questions[state.current_question_index]
    state.player_answers = {}
    state.question_start_ts = time.time()
    state.question_time_seconds = q["time_seconds"]

    await sio.emit("trivia:question", {
        "question_index": state.current_question_index,
        "total_questions": len(state.trivia_questions),
        "question_text": q["question"],
        "options": q["options"],
        "time_seconds": q["time_seconds"],
        "round_index": state.round_index,
    }, room=room_code)

    # Schedule question timer
    if state.task and not state.task.done():
        state.task.cancel()

    async def _timer():
        remaining = state.question_time_seconds - (time.time() - state.question_start_ts)
        if remaining > 0:
            await asyncio.sleep(remaining)
        await _trivia_question_timeout(room_code)

    state.task = asyncio.create_task(_timer())

    # Spawn bot answers for any bot players in this room.
    if not hasattr(state, "_bot_accuracy_slots"):
        state._bot_accuracy_slots = trivia_bot.build_accuracy_slots(state.trivia_questions)

    with SessionLocal() as db:
        bot_player_rows = db.query(RoomPlayer, User).join(
            User, RoomPlayer.user_id == User.id,
        ).filter(
            RoomPlayer.room_id == state.room_id,
            User.is_bot == True,  # noqa: E712
        ).all()

    q_idx = state.current_question_index
    slot = state._bot_accuracy_slots[q_idx] if q_idx < len(state._bot_accuracy_slots) else False

    async def _on_all_answered():
        # Acquire lock and resolve — mirrors _trivia_question_timeout.
        # _trivia_resolve_question expects caller to hold state.lock (see its docstring).
        async with state.lock:
            if state.task and not state.task.done():
                state.task.cancel()
            await _trivia_resolve_question(state, room_code)

    for rp, _user in bot_player_rows:
        await trivia_bot.schedule_bot_answer(
            state=state, room_code=room_code, bot_player_id=rp.id,
            will_answer_correctly=slot, on_all_answered=_on_all_answered,
        )


async def _trivia_resolve_question(state: RoomGameState, room_code: str) -> None:
    """Score the current question and emit results. Caller MUST hold state.lock."""
    q = state.trivia_questions[state.current_question_index]
    correct_index = q["correct_index"]

    player_results = []
    for pid in state.player_order:
        answer = state.player_answers.get(pid)
        if answer and answer["answer_index"] == correct_index:
            time_taken = answer["timestamp"] - state.question_start_ts
            speed_bonus = max(0, int(100 * (1 - time_taken / state.question_time_seconds)))
            points = 100 + speed_bonus
            state.scores[pid] = state.scores.get(pid, 0) + points
            player_results.append({
                "player_id": pid,
                "answer_index": answer["answer_index"],
                "correct": True,
                "points": points,
                "time_taken": round(time_taken, 1),
            })
        else:
            player_results.append({
                "player_id": pid,
                "answer_index": answer["answer_index"] if answer else -1,
                "correct": False,
                "points": 0,
                "time_taken": None,
            })

    await sio.emit("trivia:question_result", {
        "question_index": state.current_question_index,
        "correct_index": correct_index,
        "player_results": player_results,
        "scores": state.scores,
    }, room=room_code)

    with SessionLocal() as db:
        _save_state(db, state)

    # Pause 4 seconds to show results, then advance
    async def _advance_after_pause():
        await asyncio.sleep(4)
        try:
            await _trivia_advance(room_code)
        except Exception:
            _logger.exception("_trivia_advance failed for %s", room_code)

    state.task = asyncio.create_task(_advance_after_pause())


async def _trivia_question_timeout(room_code: str) -> None:
    """Timer-triggered: acquire lock and resolve the current question."""
    state = ROOM_STATES.get(room_code)
    if not state:
        return
    async with state.lock:
        await _trivia_resolve_question(state, room_code)


async def _trivia_advance(room_code: str) -> None:
    """Move to next question or end the round/game."""
    state = ROOM_STATES.get(room_code)
    if not state:
        return
    async with state.lock:
        state.current_question_index += 1

        if state.current_question_index >= len(state.trivia_questions):
            # Round complete
            state.round_index += 1
            state.current_question_index = 0

            if state.round_index > state.rounds_total:
                # Game over
                # NOTE: do NOT cancel state.task here — it's the current task
                # (_advance_after_pause), cancelling it would abort the DB write below.
                # Pop BEFORE emit so room:register can't find stale state during the emit
                ROOM_STATES.pop(room_code, None)
                await sio.emit("game:game_end", {"scores": state.scores, "winner_player_id": _resolve_winner(state)}, room=room_code)
                try:
                    with SessionLocal() as db:
                        db.query(RoomState).filter(RoomState.room_id == state.room_id).delete()
                        _save_game_history(db, state)
                        room = db.query(Room).filter(Room.code == room_code).first()
                        if room:
                            room.status = "lobby"
                            db.query(RoomPlayer).filter(RoomPlayer.room_id == room.id).update({RoomPlayer.in_game: False})
                        db.commit()
                except Exception:
                    _logger.exception("Error saving trivia game history for %s", room_code)
                return

            # Round end — wait for host to continue
            with SessionLocal() as db:
                _save_state(db, state)
            await sio.emit("game:round_end", {
                "round_index": state.round_index - 1,
                "scores": state.scores,
            }, room=room_code)
            return

        # Next question in same round
        await _trivia_send_question(state, room_code)


@sio.on("game:start")
async def game_start(sid, data):
    room_code = data.get("room_code")
    if not room_code:
        await emit_error(sid, "room_code required", code="BAD_REQUEST")
        return {"ok": False, "error": "BAD_REQUEST"}

    # Clear play-again votes from previous game so next play-again round starts fresh
    PLAY_AGAIN_REST.pop(room_code, None)

    with SessionLocal() as db:
        room = db.query(Room).filter(Room.code == room_code).first()
        if not room:
            await emit_error(sid, "Room not found", code="NOT_FOUND")
            return {"ok": False, "error": "NOT_FOUND"}

        token = data.get("token")
        guest_token = data.get("guest_token")
        user = get_user_from_token(db, token)
        guest = resolve_guest(db, guest_token)

        if user and room.host_user_id != user.id:
            await emit_error(sid, "Only host can start", code="FORBIDDEN")
            return {"ok": False, "error": "FORBIDDEN"}
        if guest and room.host_guest_id != guest.id:
            await emit_error(sid, "Only host can start", code="FORBIDDEN")
            return {"ok": False, "error": "FORBIDDEN"}
        if not user and not guest:
            await emit_error(sid, "Authentication required", code="UNAUTHORIZED")
            return {"ok": False, "error": "UNAUTHORIZED"}

        players = (
            db.query(RoomPlayer)
            .filter(RoomPlayer.room_id == room.id, RoomPlayer.in_game.is_(True))
            .order_by(RoomPlayer.join_order.asc())
            .all()
        )
        if len(players) < room.min_players:
            await emit_error(sid, "Not enough players", code="BAD_REQUEST")
            return {"ok": False, "error": "BAD_REQUEST"}

        # Trivia: skip word selection, use question generator
        if room.game_type == "trivia":
            state = RoomGameState(
                room_id=room.id,
                room_code=room.code,
                rounds_total=room.rounds_total,
                turn_seconds=0,
                difficulty=room.difficulty,
                game_type="trivia",
                trivia_category=room.trivia_category,
                player_order=[p.id for p in players],
                scores={p.id: p.score for p in players},
            )
            ROOM_STATES[room.code] = state
            room.status = "active"
            _save_state(db, state)

            # Emit game:turn_start as navigation trigger for frontend
            await sio.emit("game:turn_start", {
                "game_type": "trivia",
                "round_index": 1,
                "turn_seconds": 0,
                "turn_start_ts": int(time.time()),
                "describer_id": -1,
            }, room=room.code)

            await _trivia_start_round(state, room.code)
            return {"ok": True}

        # For charades, pre-select first word to validate words exist
        if room.game_type != "scribble":
            word = _select_word(db, room.difficulty, [], room.game_type)
            if not word:
                await emit_error(sid, "No words available", code="NO_WORDS")
                return {"ok": False, "error": "NO_WORDS"}
        else:
            word = None

        state = RoomGameState(
            room_id=room.id,
            room_code=room.code,
            rounds_total=room.rounds_total,
            turn_seconds=room.turn_seconds,
            difficulty=room.difficulty,
            game_type=room.game_type,
            player_order=[p.id for p in players],
            scores={p.id: p.score for p in players},
            current_word_id=word.id if word else None,
            current_word_text=word.text if word else None,
            word_history_ids=[word.id] if word else [],
        )
        start_turn(state)
        ROOM_STATES[room.code] = state
        room.status = "active"
        _save_state(db, state)

    # Use _emit_next_turn for scribble (3-word choice) — it handles everything
    if state.game_type == "scribble":
        await _emit_next_turn(state, state.room_code)
        return {"ok": True}

    room_code_val = state.room_code
    hint = _generate_hint(state.current_word_text) if state.current_word_text else None
    await sio.emit(
        "game:turn_start",
        {
            "describer_id": state.player_order[state.describer_index],
            "turn_seconds": state.turn_seconds,
            "turn_start_ts": int(state.turn_start_ts),
            "round_index": state.round_index,
            "game_type": state.game_type,
            "hint": hint,
        },
        room=room_code_val,
    )
    describer_id = state.player_order[state.describer_index]
    describer_sid = PLAYER_TO_SID.get(describer_id)
    if describer_sid:
        await sio.emit("game:new_word", {"word": state.current_word_text}, to=describer_sid)
    await _schedule_turn_timer(state)
    return {"ok": True}


@sio.on("chat:message")
async def chat_message(sid, data):
    room_code = data.get("room_code")
    message = data.get("message", "").strip()
    if not room_code or not message:
        await emit_error(sid, "Invalid message", code="BAD_REQUEST")
        return {"ok": False}

    state = ROOM_STATES.get(room_code)
    player_id = SID_TO_PLAYER.get(sid)
    if not player_id:
        await emit_error(sid, "Not in room", code="FORBIDDEN")
        return {"ok": False}

    if not state:
        await sio.emit("chat:message", {"player_id": player_id, "message": message}, room=room_code)
        return {"ok": True}

    describer_id = state.player_order[state.describer_index]
    target = state.current_word_text or ""

    if player_id == describer_id:
        if state.game_type == "scribble":
            # In scribble, the drawer can't send chat messages
            await emit_error(sid, "Drawer cannot chat", code="FORBIDDEN")
            return {"ok": False, "error": "FORBIDDEN"}
        if _hint_contains_target(message, target):
            await emit_error(sid, "Hint contains target word", code="HINT_BLOCKED")
            return {"ok": False, "error": "HINT_BLOCKED"}
        await sio.emit("chat:message", {"player_id": player_id, "message": message}, room=room_code)
        return {"ok": True}

    # Scribble: prevent double-guessing
    if state.game_type == "scribble" and player_id in state.guessed_players:
        await sio.emit("chat:message", {"player_id": player_id, "message": message}, room=room_code)
        return {"ok": True, "correct": False}

    # Guessing
    if _normalize_word(message) == _normalize_word(target):
        if state.game_type == "scribble":
            elapsed = time.time() - state.turn_start_ts
            points = _scribble_guess_score(elapsed)
            state.scores[player_id] = state.scores.get(player_id, 0) + points
            # No per-guess drawer bonus for scribble; awarded at turn end
            # Send word only to guesser + drawer; hide from remaining guessers
            base_payload = {"guesser_id": player_id, "scores": state.scores, "points_awarded": points}
            guesser_sid = PLAYER_TO_SID.get(player_id)
            drawer_sid = PLAYER_TO_SID.get(describer_id)
            privileged = [s for s in [guesser_sid, drawer_sid] if s]
            for psid in privileged:
                await sio.emit("game:correct_guess", {**base_payload, "word": target}, to=psid)
            await sio.emit("game:correct_guess", base_payload, room=room_code, skip_sid=privileged if privileged else None)
            # Track guesser; keep the same word/drawing
            state.guessed_players.add(player_id)
            non_describers = set(state.player_order) - {describer_id}
            all_guessed = state.guessed_players >= non_describers
            with SessionLocal() as db:
                _save_state(db, state)
            if all_guessed:
                # Drawer bonus is awarded in _advance_turn
                await _advance_turn(room_code)
        else:
            # Charades: flat scoring
            state.scores[player_id] = state.scores.get(player_id, 0) + 10
            state.scores[describer_id] = state.scores.get(describer_id, 0) + 5
            # Send word only to guesser + describer; hide from other guessers
            base_payload = {"guesser_id": player_id, "scores": state.scores}
            guesser_sid = PLAYER_TO_SID.get(player_id)
            describer_sid = PLAYER_TO_SID.get(describer_id)
            privileged = [s for s in [guesser_sid, describer_sid] if s]
            for psid in privileged:
                await sio.emit("game:correct_guess", {**base_payload, "word": target}, to=psid)
            await sio.emit("game:correct_guess", base_payload, room=room_code, skip_sid=privileged if privileged else None)
            with SessionLocal() as db:
                word = _select_word(db, state.difficulty, state.word_history_ids, state.game_type)
                if word:
                    state.current_word_id = word.id
                    state.current_word_text = word.text
                    state.word_history_ids.append(word.id)
                _save_state(db, state)
            describer_sid = PLAYER_TO_SID.get(describer_id)
            if describer_sid and state.current_word_text:
                await sio.emit("game:new_word", {"word": state.current_word_text}, to=describer_sid)
            # Send updated hint to guessers (new word after correct guess)
            if state.current_word_text:
                await sio.emit("game:hint", {"hint": _generate_hint(state.current_word_text)}, room=room_code, skip_sid=describer_sid)

        return {"ok": True, "correct": True}

    await sio.emit("chat:message", {"player_id": player_id, "message": message}, room=room_code)
    return {"ok": True, "correct": False}


@sio.on("game:leave")
async def game_leave(sid, data):
    """Player explicitly leaves mid-game."""
    player_id = SID_TO_PLAYER.get(sid)
    room_code = data.get("room_code") or PLAYER_TO_ROOM.get(player_id)
    if not player_id or not room_code:
        return

    _logger.info("Player %s leaving game in room %s", player_id, room_code)

    # Cancel any existing grace task
    task = PLAYER_GRACE_TASKS.get(player_id)
    if task and not task.done():
        task.cancel()

    # Mark player as left in DB
    with SessionLocal() as db:
        rp = db.query(RoomPlayer).filter(RoomPlayer.id == player_id).first()
        if rp:
            rp.in_game = False
            rp.connected = False
            db.commit()

    # Clean up SID mappings
    SID_TO_PLAYER.pop(sid, None)
    PLAYER_TO_SID.pop(player_id, None)
    PLAYER_TO_ROOM.pop(player_id, None)

    # Notify room
    await sio.emit("game:player_removed", {"player_id": player_id}, room=room_code)

    # Clean up game state
    state = ROOM_STATES.get(room_code)
    if state and player_id in state.player_order:
        async with state.lock:
            if player_id not in state.player_order:
                return
            idx = state.player_order.index(player_id)
            was_describer = (idx == state.describer_index)
            state.player_order.remove(player_id)

            # Quickmatch forfeit-win: leaving with one survivor ends the match.
            if state.origin == "quickmatch" and len(state.player_order) == 1:
                survivor = state.player_order[0]
                state.scores[survivor] = state.scores.get(survivor, 0)
                await _auto_end_game(state, room_code, winner_player_id=survivor)
                return

            # If fewer than 2 players remain (charades/scribble need 2), end game
            if not state.player_order or (state.game_type != "trivia" and len(state.player_order) < 2):
                await _auto_end_game(state, room_code)
                return

            if was_describer:
                if state.task and not state.task.done():
                    state.task.cancel()
                if state.describer_index >= len(state.player_order):
                    state.describer_index = 0
                if state.game_type != "trivia":
                    await _emit_next_turn(state, room_code)
            elif idx < state.describer_index:
                state.describer_index -= 1

            with SessionLocal() as db:
                _save_state(db, state)

    await sio.leave_room(sid, room_code)


@sio.on("game:word_pick")
async def game_word_pick(sid, data):
    """Drawer picks one of the 3 offered words in scribble."""
    room_code = data.get("room_code")
    word_text = data.get("word")
    if not room_code or not word_text:
        return {"ok": False}
    state = ROOM_STATES.get(room_code)
    if not state or state.game_type != "scribble":
        return {"ok": False}
    player_id = SID_TO_PLAYER.get(sid)
    describer_id = state.player_order[state.describer_index]
    if player_id != describer_id:
        return {"ok": False}
    choices = getattr(state, '_word_choices', {})
    if word_text not in choices:
        return {"ok": False}
    # Set the chosen word
    state.current_word_id = choices[word_text]
    state.current_word_text = word_text
    state.word_history_ids.append(choices[word_text])
    state._word_choices = {}
    # Reset turn timer to full duration now that word is picked
    state.turn_start_ts = time.time()
    with SessionLocal() as db:
        _save_state(db, state)
    # Send the chosen word to the drawer
    await sio.emit("game:new_word", {"word": word_text}, to=sid)
    # Send hint + updated turn_start to all players
    hint = _generate_hint(word_text)
    await sio.emit("game:turn_start", {
        "describer_id": describer_id,
        "turn_seconds": state.turn_seconds,
        "turn_start_ts": int(state.turn_start_ts),
        "round_index": state.round_index,
        "game_type": state.game_type,
        "hint": hint,
    }, room=room_code)
    await _schedule_turn_timer(state)
    return {"ok": True}


@sio.on("game:skip_word")
async def game_skip_word(sid, data):
    """Describer skips the current word and gets a new one. Max 2 skips per turn."""
    room_code = data.get("room_code")
    if not room_code:
        return {"ok": False, "error": "room_code required"}
    state = ROOM_STATES.get(room_code)
    if not state:
        return {"ok": False, "error": "Game not active"}
    if state.game_type != "charades":
        return {"ok": False, "error": "Skip only available in charades"}
    player_id = SID_TO_PLAYER.get(sid)
    describer_id = state.player_order[state.describer_index]
    if player_id != describer_id:
        await emit_error(sid, "Only the describer can skip", code="FORBIDDEN")
        return {"ok": False, "error": "FORBIDDEN"}
    # Track skips per turn (stored on state, cleared by start_turn)
    if not hasattr(state, '_skips_this_turn'):
        state._skips_this_turn = 0
    if state._skips_this_turn >= 2:
        await emit_error(sid, "No skips remaining", code="SKIP_LIMIT")
        return {"ok": False, "error": "SKIP_LIMIT"}
    state._skips_this_turn += 1
    # Select a new word
    with SessionLocal() as db:
        word = _select_word(db, state.difficulty, state.word_history_ids, state.game_type)
        if word:
            state.current_word_id = word.id
            state.current_word_text = word.text
            state.word_history_ids.append(word.id)
        _save_state(db, state)
    hint = _generate_hint(state.current_word_text) if state.current_word_text else None
    # Send new word to describer
    if state.current_word_text:
        await sio.emit("game:new_word", {"word": state.current_word_text}, to=sid)
    # Send updated hint to all (so guessers see the new hint)
    await sio.emit("game:hint", {"hint": hint}, room=room_code, skip_sid=sid)
    return {"ok": True, "skips_remaining": 2 - state._skips_this_turn}


@sio.on("game:turn_end")
async def game_turn_end(sid, data):
    room_code = data.get("room_code")
    if not room_code:
        await emit_error(sid, "room_code required", code="BAD_REQUEST")
        return {"ok": False}

    state = ROOM_STATES.get(room_code)
    if not state:
        await emit_error(sid, "Game not active", code="BAD_REQUEST")
        return {"ok": False}

    await _advance_turn(room_code)
    return {"ok": True}


@sio.on("game:next_round")
async def game_next_round(sid, data):
    """Host triggers the next round after the round-end screen."""
    room_code = data.get("room_code")
    if not room_code:
        await emit_error(sid, "room_code required", code="BAD_REQUEST")
        return {"ok": False}

    state = ROOM_STATES.get(room_code)
    if not state:
        await emit_error(sid, "Game not active", code="BAD_REQUEST")
        return {"ok": False}

    # Verify host
    with SessionLocal() as db:
        room = db.query(Room).filter(Room.code == room_code).first()
        if not room:
            await emit_error(sid, "Room not found", code="NOT_FOUND")
            return {"ok": False}
        token = data.get("token")
        guest_token = data.get("guest_token")
        user = get_user_from_token(db, token)
        guest = resolve_guest(db, guest_token)
        if user and room.host_user_id != user.id:
            await emit_error(sid, "Only host can continue", code="FORBIDDEN")
            return {"ok": False}
        if guest and room.host_guest_id != guest.id:
            await emit_error(sid, "Only host can continue", code="FORBIDDEN")
            return {"ok": False}
        if not user and not guest:
            await emit_error(sid, "Authentication required", code="UNAUTHORIZED")
            return {"ok": False}

    if state.game_type == "trivia":
        async with state.lock:
            # Emit turn_start as navigation trigger (RoundEndPage watches game.turn)
            await sio.emit("game:turn_start", {
                "game_type": "trivia",
                "round_index": state.round_index,
                "turn_seconds": 0,
                "turn_start_ts": int(time.time()),
                "describer_id": -1,
            }, room=room_code)
            await _trivia_start_round(state, room_code)
        return {"ok": True}

    async with state.lock:
        await _emit_next_turn(state, room_code)
    return {"ok": True}


@sio.on("game:play_again")
async def game_play_again(sid, data):
    """Player votes to play again after game ends."""
    logger = logging.getLogger(__name__)

    room_code = data.get("room_code")
    if not room_code:
        await emit_error(sid, "room_code required", code="BAD_REQUEST")
        return {"ok": False}

    with SessionLocal() as db:
        room = db.query(Room).filter(Room.code == room_code).first()
        if not room:
            await emit_error(sid, "Room not found", code="NOT_FOUND")
            return {"ok": False}

        # Identify player via token (robust — doesn't depend on SID mapping)
        token = data.get("token")
        guest_token = data.get("guest_token")
        user = get_user_from_token(db, token)
        guest = resolve_guest(db, guest_token)
        if not user and not guest:
            await emit_error(sid, "Authentication required", code="UNAUTHORIZED")
            return {"ok": False}

        # Find the player's RoomPlayer record
        rp_filter = RoomPlayer.room_id == room.id
        if user:
            rp = db.query(RoomPlayer).filter(rp_filter, RoomPlayer.user_id == user.id).first()
        else:
            rp = db.query(RoomPlayer).filter(rp_filter, RoomPlayer.guest_id == guest.id).first()

        if not rp:
            await emit_error(sid, "Not in this room", code="FORBIDDEN")
            return {"ok": False}

        player_id = rp.id

        # Count players in the room — use in_game=False (just finished a game)
        # AND connected=True, OR simply count all players associated with the room
        # who are still in the Socket.IO room
        all_players = db.query(RoomPlayer).filter(
            RoomPlayer.room_id == room.id,
        ).all()
        # Use PLAYER_TO_SID to determine who's actually connected via socket
        active_player_ids = {p.id for p in all_players if PLAYER_TO_SID.get(p.id)}
        total = len(active_player_ids)

    logger.info(f"[play_again] sid={sid} player_id={player_id} active_players={active_player_ids} total={total}")

    if player_id not in active_player_ids:
        # Player has a valid token but no active socket — try registering them
        await sio.enter_room(sid, room_code)
        SID_TO_PLAYER[sid] = player_id
        PLAYER_TO_SID[player_id] = sid
        PLAYER_TO_ROOM[player_id] = room_code
        active_player_ids.add(player_id)
        total = len(active_player_ids)
        logger.info(f"[play_again] auto-registered player_id={player_id} sid={sid}")

    # Initialize vote tracking for this room if needed
    if room_code not in PLAY_AGAIN_VOTES:
        PLAY_AGAIN_VOTES[room_code] = {"player_ids": set(), "total": total}

        # Start 30-second timeout
        async def _play_again_timeout():
            await asyncio.sleep(30)
            votes = PLAY_AGAIN_VOTES.pop(room_code, None)
            if votes:
                voted = len(votes["player_ids"])
                await sio.emit("game:play_again_expired", {
                    "voted": voted,
                    "total": votes["total"],
                }, room=room_code)

        PLAY_AGAIN_VOTES[room_code]["task"] = asyncio.ensure_future(_play_again_timeout())

    votes = PLAY_AGAIN_VOTES[room_code]
    votes["player_ids"].add(player_id)
    votes["total"] = total  # refresh in case someone disconnected
    voted = len(votes["player_ids"])
    logger.info(f"[play_again] voted={voted}/{total} voters={votes['player_ids']}")

    if voted >= total:
        # All players agreed — cancel timeout, clean up, send to lobby
        task = votes.get("task")
        if task and not task.done():
            task.cancel()
        PLAY_AGAIN_VOTES.pop(room_code, None)

        # Re-enable in_game for all connected players so game:start can find them
        with SessionLocal() as db:
            room = db.query(Room).filter(Room.code == room_code).first()
            if room:
                db.query(RoomPlayer).filter(
                    RoomPlayer.room_id == room.id,
                    RoomPlayer.connected == True,
                ).update({RoomPlayer.in_game: True})
                db.commit()

        logger.info(f"[play_again] ALL voted — emitting play_again_ready for {room_code}")
        await sio.emit("game:play_again_ready", {"room_code": room_code}, room=room_code)
    else:
        logger.info(f"[play_again] emitting play_again_update voted={voted} total={total}")
        # Broadcast updated vote count
        await sio.emit("game:play_again_update", {
            "voted": voted,
            "total": total,
        }, room=room_code)

    return {"ok": True}


@sio.on("trivia:answer")
async def trivia_answer(sid, data):
    """Player submits an answer to the current trivia question."""
    room_code = data.get("room_code")
    answer_index = data.get("answer_index")
    if room_code is None or answer_index is None:
        await emit_error(sid, "Invalid answer data", code="BAD_REQUEST")
        return {"ok": False}

    state = ROOM_STATES.get(room_code)
    if not state or state.game_type != "trivia":
        await emit_error(sid, "Not a trivia game", code="BAD_REQUEST")
        return {"ok": False}

    player_id = SID_TO_PLAYER.get(sid)
    if not player_id or player_id not in state.player_order:
        await emit_error(sid, "Not in game", code="FORBIDDEN")
        return {"ok": False}

    # Lock the entire answer-record + all-answered-check to prevent race
    # where two simultaneous answers both trigger _trivia_resolve_question
    async with state.lock:
        if player_id in state.player_answers:
            return {"ok": False, "error": "ALREADY_ANSWERED"}

        state.player_answers[player_id] = {
            "answer_index": answer_index,
            "timestamp": time.time(),
        }

        await sio.emit("trivia:answer_update", {
            "answered_count": len(state.player_answers),
            "total_players": len(state.player_order),
        }, room=room_code)

        # If all players answered, cancel the timer and resolve immediately
        if len(state.player_answers) >= len(state.player_order):
            if state.task and not state.task.done():
                state.task.cancel()
            await _trivia_resolve_question(state, room_code)

    return {"ok": True}


@sio.on("scribble:draw")
async def scribble_draw(sid, data):
    """Relay drawing data from drawer to all other players in the room."""
    room_code = data.get("room_code")
    if not room_code:
        return
    state = ROOM_STATES.get(room_code)
    if not state or state.game_type != "scribble":
        return
    player_id = SID_TO_PLAYER.get(sid)
    describer_id = state.player_order[state.describer_index]
    if player_id != describer_id:
        return
    # Accumulate stroke and relay to everyone except the drawer
    stroke = {"points": data.get("points", []), "color": data.get("color", "#000000"), "width": data.get("width", 3), "eraser": data.get("eraser", False)}
    state.strokes.append(stroke)
    await sio.emit("scribble:draw", stroke, room=room_code, skip_sid=sid)


@sio.on("scribble:clear")
async def scribble_clear(sid, data):
    """Drawer clears the canvas; relay to room."""
    room_code = data.get("room_code")
    if not room_code:
        return
    state = ROOM_STATES.get(room_code)
    if not state or state.game_type != "scribble":
        return
    player_id = SID_TO_PLAYER.get(sid)
    describer_id = state.player_order[state.describer_index]
    if player_id != describer_id:
        return
    state.strokes = []
    await sio.emit("scribble:clear", {}, room=room_code, skip_sid=sid)


@sio.on("scribble:undo")
async def scribble_undo(sid, data):
    """Drawer undoes last stroke; relay to room."""
    room_code = data.get("room_code")
    if not room_code:
        return
    state = ROOM_STATES.get(room_code)
    if not state or state.game_type != "scribble":
        return
    player_id = SID_TO_PLAYER.get(sid)
    describer_id = state.player_order[state.describer_index]
    if player_id != describer_id:
        return
    if state.strokes:
        state.strokes.pop()
    await sio.emit("scribble:undo", {}, room=room_code, skip_sid=sid)


@sio.on("quickmatch:join")
async def quickmatch_join(sid, data):
    token = data.get("token")
    category_raw = data.get("category")
    if not token or not category_raw:
        await emit_error(sid, "token + category required", code="BAD_REQUEST")
        return {"ok": False, "error": "BAD_REQUEST"}

    with SessionLocal() as db:
        user = get_user_from_token(db, token)
    if not user:
        await emit_error(sid, "Auth required", code="UNAUTHORIZED")
        return {"ok": False, "error": "UNAUTHORIZED"}

    SID_TO_USER[sid] = user.id

    category = matchmaker.resolve_category(category_raw)

    async def on_pair(entry_a, entry_b):
        await _quickmatch_pair_humans(entry_a, entry_b, category)

    async def on_bot_fallback(entry):
        await _quickmatch_pair_bot(entry, category)

    res = await matchmaker.join_queue(
        user_id=user.id, sid=sid, category=category,
        on_pair=on_pair, on_bot_fallback=on_bot_fallback,
    )
    if res.get("status") == "searching":
        await sio.emit("quickmatch:searching",
                       {"wait_seconds": matchmaker.FALLBACK_SECONDS}, to=sid)
    return res


@sio.on("quickmatch:ready")
async def quickmatch_ready(sid, data):
    token = data.get("token")
    room_code = data.get("room_code")
    if not token or not room_code:
        return {"ok": False, "error": "BAD_REQUEST"}
    with SessionLocal() as db:
        user = get_user_from_token(db, token)
    if not user:
        return {"ok": False, "error": "UNAUTHORIZED"}

    await matchmaker.register_ready(room_code, user.id)
    return {"ok": True}


@sio.on("quickmatch:cancel")
async def quickmatch_cancel(sid, data):
    token = data.get("token")
    if not token:
        return {"ok": False, "error": "BAD_REQUEST"}
    with SessionLocal() as db:
        user = get_user_from_token(db, token)
    if not user:
        return {"ok": False, "error": "UNAUTHORIZED"}

    res = await matchmaker.cancel_queue(user.id)
    if res["ok"]:
        await sio.emit("quickmatch:cancelled", {}, to=sid)
    return res


async def _quickmatch_pair_humans(entry_a, entry_b, category: str) -> None:
    """Create a quickmatch room with both users, join their sockets to the
    room, broadcast `quickmatch:matched`, and register the pending-start gate."""

    with SessionLocal() as db:
        user_a = db.query(User).filter(User.id == entry_a.user_id).first()
        user_b = db.query(User).filter(User.id == entry_b.user_id).first()
        if not user_a or not user_b:
            return

        payload = RoomCreateRequest(
            rounds_total=1, difficulty=0, turn_seconds=15,
            max_players=2, game_type="trivia", trivia_category=category,
        )
        lobby = create_room_for_user(db, user_a.id, payload)
        room = db.query(Room).filter(Room.code == lobby.room.code).first()
        room.origin = "quickmatch"
        room.max_players = 2
        room.min_players = 2
        join_room_op(db, room, user_b.id, None)
        db.commit()

        rp_a = db.query(RoomPlayer).filter(
            RoomPlayer.room_id == room.id, RoomPlayer.user_id == user_a.id,
        ).first()
        rp_b = db.query(RoomPlayer).filter(
            RoomPlayer.room_id == room.id, RoomPlayer.user_id == user_b.id,
        ).first()
        room_code = room.code
        name_a = user_a.display_name or user_a.email
        name_b = user_b.display_name or user_b.email

    await sio.enter_room(entry_a.sid, room_code)
    await sio.enter_room(entry_b.sid, room_code)
    SID_TO_PLAYER[entry_a.sid] = rp_a.id
    SID_TO_PLAYER[entry_b.sid] = rp_b.id
    PLAYER_TO_SID[rp_a.id] = entry_a.sid
    PLAYER_TO_SID[rp_b.id] = entry_b.sid
    PLAYER_TO_ROOM[rp_a.id] = room_code
    PLAYER_TO_ROOM[rp_b.id] = room_code

    await sio.emit("quickmatch:matched",
                   {"room_code": room_code, "opponent_name": name_b},
                   to=entry_a.sid)
    await sio.emit("quickmatch:matched",
                   {"room_code": room_code, "opponent_name": name_a},
                   to=entry_b.sid)

    async def _start_game(rc):
        await _quickmatch_start_game(rc)

    matchmaker.register_pending_start(
        room_code, expected_user_ids={user_a.id, user_b.id}, on_start=_start_game,
    )

    # Clean up matched entries from USER_IN_QUEUE now that the room is created
    # and sockets are registered. Phase-4 handlers rely on PLAYER_TO_ROOM for
    # subsequent routing; USER_IN_QUEUE is no longer needed for these users.
    matchmaker.USER_IN_QUEUE.pop(entry_a.user_id, None)
    matchmaker.USER_IN_QUEUE.pop(entry_b.user_id, None)


async def _quickmatch_start_game(room_code: str) -> None:
    """Kick off the trivia game for a quickmatch room. Equivalent to the
    trivia branch of `game:start` but bypassing the host check."""
    with SessionLocal() as db:
        room = db.query(Room).filter(Room.code == room_code).first()
        if not room:
            return
        players = db.query(RoomPlayer).filter(
            RoomPlayer.room_id == room.id,
        ).order_by(RoomPlayer.join_order).all()
        if len(players) < 2:
            return

        state = RoomGameState(
            room_id=room.id, room_code=room.code,
            rounds_total=room.rounds_total, turn_seconds=room.turn_seconds,
            difficulty=room.difficulty, game_type="trivia",
            trivia_category=room.trivia_category,
            origin="quickmatch",
        )
        state.player_order = [p.id for p in players]
        state.scores = {p.id: 0 for p in players}
        ROOM_STATES[room.code] = state

        room.status = "active"
        for p in players:
            p.in_game = True
        db.commit()
        _save_state(db, state)

    # Emit game:turn_start as navigation trigger for frontend (matches game:start trivia branch)
    await sio.emit("game:turn_start", {
        "game_type": "trivia",
        "round_index": 1,
        "turn_seconds": 0,
        "turn_start_ts": int(time.time()),
        "describer_id": -1,
    }, room=room_code)

    await _trivia_start_round(state, room_code)


async def _quickmatch_pair_bot(entry, category: str) -> None:
    """Create a quickmatch room for one human + one bot, register sockets,
    and start the pending-start gate.  Mirrors _quickmatch_pair_humans."""

    with SessionLocal() as db:
        user = db.query(User).filter(User.id == entry.user_id).first()
        if not user:
            return
        bot = pick_random_bot(db)
        if not bot:
            return

        payload = RoomCreateRequest(
            rounds_total=1, difficulty=0, turn_seconds=15,
            max_players=2, game_type="trivia", trivia_category=category,
        )
        lobby = create_room_for_user(db, user.id, payload)
        room = db.query(Room).filter(Room.code == lobby.room.code).first()
        room.origin = "quickmatch"
        room.max_players = 2
        room.min_players = 2
        join_room_op(db, room, bot.id, None)
        db.commit()

        rp_user = db.query(RoomPlayer).filter(
            RoomPlayer.room_id == room.id, RoomPlayer.user_id == user.id,
        ).first()
        room_code = room.code
        bot_display = bot.display_name or "Player"

    await sio.enter_room(entry.sid, room_code)
    SID_TO_PLAYER[entry.sid] = rp_user.id
    PLAYER_TO_SID[rp_user.id] = entry.sid
    PLAYER_TO_ROOM[rp_user.id] = room_code

    # Clean up matchmaker queue entry (bot won't naturally pop the human entry)
    matchmaker.USER_IN_QUEUE.pop(user.id, None)

    await sio.emit("quickmatch:matched",
                   {"room_code": room_code, "opponent_name": bot_display},
                   to=entry.sid)

    async def _start_game(rc):
        await _quickmatch_start_game(rc)

    matchmaker.register_pending_start(
        room_code, expected_user_ids={user.id}, on_start=_start_game,
    )


def restore_game_states() -> None:
    with SessionLocal() as db:
        rows = db.query(RoomState).all()
        for row in rows:
            # Only restore states for rooms that are still active
            room = db.query(Room).filter(Room.id == row.room_id).first()
            if not room or room.status != "active":
                db.delete(row)
                continue
            state = deserialize_state(row.state_json)
            ROOM_STATES[state.room_code] = state
        db.commit()


async def schedule_restored_states() -> None:
    for state in list(ROOM_STATES.values()):
        if state.game_type == "trivia" and state.trivia_questions:
            await _trivia_send_question(state, state.room_code)
        else:
            await _schedule_turn_timer(state)
