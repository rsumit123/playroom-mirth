import asyncio
import pytest

from app.db.session import SessionLocal
from app.models.user import User
from app.models.word import Word
from app.models.room_state import RoomState
from app.services.auth import create_access_token, hash_password
from app.sockets.events import sio
from app.services.game_state import ROOM_STATES


@pytest.mark.asyncio
async def test_game_start_and_correct_guess_flow():
    db = SessionLocal()
    try:
        host = User(email="hostgame@example.com", password_hash=hash_password("secret"))
        guest = User(email="guestgame@example.com", password_hash=hash_password("secret"))
        db.add(host)
        db.add(guest)
        db.add(Word(text="orange", difficulty=1, active=True))
        db.commit()
        db.refresh(host)
        db.refresh(guest)
        host_token = create_access_token(str(host.id))
        guest_token = create_access_token(str(guest.id))
    finally:
        db.close()

    # Host creates room
    sid_host = await sio.manager.connect("eio-host", "/")
    create_res = await sio._trigger_event(
        "room:create",
        "/",
        sid_host,
        {"token": host_token, "rounds_total": 1, "difficulty": 1, "turn_seconds": 60, "max_players": 20},
    )
    room_code = create_res["lobby"]["room"]["code"]

    # Guest joins room
    sid_guest = await sio.manager.connect("eio-guest", "/")
    await sio._trigger_event("room:join", "/", sid_guest, {"room_code": room_code, "token": guest_token})

    # Start game
    start_res = await sio._trigger_event(
        "game:start",
        "/",
        sid_host,
        {"room_code": room_code, "token": host_token},
    )
    assert start_res["ok"] is True
    assert room_code in ROOM_STATES
    db = SessionLocal()
    try:
        persisted = db.query(RoomState).first()
        assert persisted is not None
    finally:
        db.close()

    # Guest guesses correctly
    guess_res = await sio._trigger_event(
        "chat:message",
        "/",
        sid_guest,
        {"room_code": room_code, "message": "orange"},
    )
    assert guess_res["ok"] is True
    assert guess_res["correct"] is True


@pytest.mark.asyncio
async def test_turn_timer_advances_describer():
    db = SessionLocal()
    try:
        host = User(email="timerhost@example.com", password_hash=hash_password("secret"))
        guest = User(email="timerguest@example.com", password_hash=hash_password("secret"))
        db.add(host)
        db.add(guest)
        db.add(Word(text="pear", difficulty=1, active=True))
        db.commit()
        db.refresh(host)
        db.refresh(guest)
        host_token = create_access_token(str(host.id))
        guest_token = create_access_token(str(guest.id))
    finally:
        db.close()

    sid_host = await sio.manager.connect("eio-timer-host", "/")
    create_res = await sio._trigger_event(
        "room:create",
        "/",
        sid_host,
        {"token": host_token, "rounds_total": 1, "difficulty": 1, "turn_seconds": 1, "max_players": 20},
    )
    room_code = create_res["lobby"]["room"]["code"]

    sid_guest = await sio.manager.connect("eio-timer-guest", "/")
    await sio._trigger_event("room:join", "/", sid_guest, {"room_code": room_code, "token": guest_token})

    await sio._trigger_event("game:start", "/", sid_host, {"room_code": room_code, "token": host_token})
    await asyncio.sleep(1.2)

    state = ROOM_STATES[room_code]
    assert state.describer_index == 1


@pytest.mark.asyncio
async def test_game_end_resets_in_game():
    db = SessionLocal()
    try:
        host = User(email="endhost@example.com", password_hash=hash_password("secret"))
        guest = User(email="endguest@example.com", password_hash=hash_password("secret"))
        db.add(host)
        db.add(guest)
        db.add(Word(text="finish", difficulty=1, active=True))
        db.commit()
        db.refresh(host)
        db.refresh(guest)
        host_token = create_access_token(str(host.id))
        guest_token = create_access_token(str(guest.id))
    finally:
        db.close()

    sid_host = await sio.manager.connect("eio-end-host", "/")
    create_res = await sio._trigger_event(
        "room:create",
        "/",
        sid_host,
        {"token": host_token, "rounds_total": 1, "difficulty": 1, "turn_seconds": 60, "max_players": 20},
    )
    room_code = create_res["lobby"]["room"]["code"]

    sid_guest = await sio.manager.connect("eio-end-guest", "/")
    await sio._trigger_event("room:join", "/", sid_guest, {"room_code": room_code, "token": guest_token})

    await sio._trigger_event("game:start", "/", sid_host, {"room_code": room_code, "token": host_token})
    # end the game by advancing turns twice (2 players, 1 round)
    await sio._trigger_event("game:turn_end", "/", sid_host, {"room_code": room_code})
    await sio._trigger_event("game:turn_end", "/", sid_host, {"room_code": room_code})

    db = SessionLocal()
    try:
        from app.models.room_player import RoomPlayer
        from app.models.room import Room

        room = db.query(Room).filter(Room.code == room_code).first()
        assert room.status == "lobby"
        players = db.query(RoomPlayer).filter(RoomPlayer.room_id == room.id).all()
        assert all(p.in_game for p in players)
    finally:
        db.close()
