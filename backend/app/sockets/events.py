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
    RoomGameState,
    start_turn,
    serialize_state,
    deserialize_state,
)
from app.models.room_player import RoomPlayer
from app.models.word import Word
from sqlalchemy import func as sa_func
import time

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


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


async def _schedule_turn_timer(state: RoomGameState) -> None:
    if state.task and not state.task.done():
        state.task.cancel()

    async def _timer():
        remaining = state.turn_seconds - (time.time() - state.turn_start_ts)
        if remaining > 0:
            await asyncio.sleep(remaining)
        await _advance_turn(state.room_code)

    state.task = asyncio.create_task(_timer())


async def _advance_turn(room_code: str) -> None:
    state = ROOM_STATES.get(room_code)
    if not state:
        return
    async with state.lock:
        state.describer_index += 1
        if state.describer_index >= len(state.player_order):
            state.describer_index = 0
            state.round_index += 1
            await sio.emit("game:round_end", {"round_index": state.round_index - 1}, room=room_code)

        if state.round_index > state.rounds_total:
            if state.task and not state.task.done():
                state.task.cancel()
            await sio.emit("game:game_end", {"scores": state.scores}, room=room_code)
            ROOM_STATES.pop(room_code, None)
            with SessionLocal() as db:
                room = db.query(Room).filter(Room.code == room_code).first()
                if room:
                    room.status = "lobby"
                    # allow all room players to participate in next game
                    db.query(RoomPlayer).filter(RoomPlayer.room_id == room.id).update({RoomPlayer.in_game: True})
                    db.commit()
            return

        start_turn(state)
        with SessionLocal() as db:
            _save_state(db, state)

        await sio.emit(
            "game:turn_start",
            {
                "describer_id": state.player_order[state.describer_index],
                "turn_seconds": state.turn_seconds,
                "turn_start_ts": int(state.turn_start_ts),
                "round_index": state.round_index,
            },
            room=room_code,
        )
        await _schedule_turn_timer(state)

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
            await sio.emit("game:player_removed", {"player_id": player_id}, room=room_code)
        task = asyncio.create_task(_remove_after_grace())
        PLAYER_GRACE_TASKS[player_id] = task
    SID_TO_PLAYER.pop(sid, None)
    if player_id:
        PLAYER_TO_SID.pop(player_id, None)


@sio.event
async def ping(sid, data):
    await sio.emit("pong", {"ok": True}, to=sid)


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
        room2 = db2.query(Room).filter(Room.code == room_code).first()
        if room2:
            lobby = build_lobby_state(db2, room2, self_player_id=rp.id)
            await sio.emit("room:lobby_update", lobby.model_dump(), room=room_code)
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


def _select_word(db, difficulty: int, history_ids: list[int]) -> Word | None:
    word = (
        db.query(Word)
        .filter(Word.active.is_(True), Word.difficulty == difficulty, ~Word.id.in_(history_ids))
        .order_by(sa_func.random())
        .first()
    )
    if word:
        return word
    return db.query(Word).filter(Word.active.is_(True), ~Word.id.in_(history_ids)).order_by(sa_func.random()).first()


@sio.on("game:start")
async def game_start(sid, data):
    room_code = data.get("room_code")
    if not room_code:
        await emit_error(sid, "room_code required", code="BAD_REQUEST")
        return {"ok": False, "error": "BAD_REQUEST"}

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

        word = _select_word(db, room.difficulty, [])
        if not word:
            await emit_error(sid, "No words available", code="NO_WORDS")
            return {"ok": False, "error": "NO_WORDS"}

        state = RoomGameState(
            room_id=room.id,
            room_code=room.code,
            rounds_total=room.rounds_total,
            turn_seconds=room.turn_seconds,
            difficulty=room.difficulty,
            player_order=[p.id for p in players],
            scores={p.id: p.score for p in players},
            current_word_id=word.id,
            current_word_text=word.text,
            word_history_ids=[word.id],
        )
        start_turn(state)
        ROOM_STATES[room.code] = state
        room.status = "active"
        _save_state(db, state)

    room_code_val = state.room_code
    await sio.emit(
        "game:turn_start",
        {
            "describer_id": state.player_order[state.describer_index],
            "turn_seconds": state.turn_seconds,
            "turn_start_ts": int(state.turn_start_ts),
            "round_index": state.round_index,
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
        if _hint_contains_target(message, target):
            await emit_error(sid, "Hint contains target word", code="HINT_BLOCKED")
            return {"ok": False, "error": "HINT_BLOCKED"}
        await sio.emit("chat:message", {"player_id": player_id, "message": message}, room=room_code)
        return {"ok": True}

    # Guessing
    if _normalize_word(message) == _normalize_word(target):
        state.scores[player_id] = state.scores.get(player_id, 0) + 10
        state.scores[describer_id] = state.scores.get(describer_id, 0) + 5
        await sio.emit(
            "game:correct_guess",
            {"guesser_id": player_id, "word": target, "scores": state.scores},
            room=room_code,
        )
        with SessionLocal() as db:
            word = _select_word(db, state.difficulty, state.word_history_ids)
            if word:
                state.current_word_id = word.id
                state.current_word_text = word.text
                state.word_history_ids.append(word.id)
            _save_state(db, state)
        describer_sid = PLAYER_TO_SID.get(describer_id)
        if describer_sid and state.current_word_text:
            await sio.emit("game:new_word", {"word": state.current_word_text}, to=describer_sid)
        return {"ok": True, "correct": True}

    await sio.emit("chat:message", {"player_id": player_id, "message": message}, room=room_code)
    return {"ok": True, "correct": False}


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


def restore_game_states() -> None:
    with SessionLocal() as db:
        rows = db.query(RoomState).all()
        for row in rows:
            state = deserialize_state(row.state_json)
            ROOM_STATES[state.room_code] = state


async def schedule_restored_states() -> None:
    for state in list(ROOM_STATES.values()):
        await _schedule_turn_timer(state)
