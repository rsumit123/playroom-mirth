import asyncio
import pytest

from app.db.session import SessionLocal
from app.models.user import User
from app.models.word import Word
from app.services.auth import create_access_token, hash_password
from app.sockets.events import sio


@pytest.mark.asyncio
async def test_socket_room_create_with_user():
    db = SessionLocal()
    try:
        user = User(email="sock@example.com", password_hash=hash_password("secret"))
        db.add(user)
        db.add(Word(text="apple", difficulty=1, active=True))
        db.commit()
        db.refresh(user)
        token = create_access_token(str(user.id))
    finally:
        db.close()

    eio_sid = "eio-user-1"
    sid = await sio.manager.connect(eio_sid, "/")

    result = await sio._trigger_event(
        "room:create",
        "/",
        sid,
        {"token": token, "rounds_total": 1, "difficulty": 1, "turn_seconds": 60, "max_players": 20},
    )

    assert result["ok"] is True
    assert result["lobby"]["self_player_id"]
    assert result["lobby"]["room"]["code"]
    assert len(result["lobby"]["players"]) == 1


@pytest.mark.asyncio
async def test_socket_room_create_with_guest_and_join():
    db = SessionLocal()
    try:
        # Create a guest directly
        from app.models.guest import Guest

        guest = Guest(guest_token="guest-token-1")
        db.add(guest)
        db.add(Word(text="banana", difficulty=2, active=True))
        db.commit()
    finally:
        db.close()

    eio_sid = "eio-guest-1"
    sid = await sio.manager.connect(eio_sid, "/")
    create_res = await sio._trigger_event(
        "room:create",
        "/",
        sid,
        {
            "guest_token": "guest-token-1",
            "rounds_total": 1,
            "difficulty": 2,
            "turn_seconds": 45,
            "max_players": 10,
        },
    )
    assert create_res["ok"] is True
    assert create_res["lobby"]["self_player_id"]

    room_code = create_res["lobby"]["room"]["code"]
    eio_sid2 = "eio-guest-2"
    sid2 = await sio.manager.connect(eio_sid2, "/")
    join_res = await sio._trigger_event(
        "room:join",
        "/",
        sid2,
        {"room_code": room_code, "guest_token": "guest-token-1"},
    )
    assert join_res["ok"] is True
    assert len(join_res["lobby"]["players"]) == 2


@pytest.mark.asyncio
async def test_disconnect_sets_connected_false():
    db = SessionLocal()
    try:
        user = User(email="disc@example.com", password_hash=hash_password("secret"))
        db.add(user)
        db.add(Word(text="grace", difficulty=1, active=True))
        db.commit()
        db.refresh(user)
        token = create_access_token(str(user.id))
    finally:
        db.close()

    eio_sid = "eio-disc"
    sid = await sio.manager.connect(eio_sid, "/")
    create_res = await sio._trigger_event(
        "room:create",
        "/",
        sid,
        {"token": token, "rounds_total": 1, "difficulty": 1, "turn_seconds": 60, "max_players": 20},
    )
    player_id = create_res["lobby"]["self_player_id"]
    await sio._trigger_event("disconnect", "/", sid)

    db = SessionLocal()
    try:
        from app.models.room_player import RoomPlayer

        rp = db.query(RoomPlayer).filter(RoomPlayer.id == player_id).first()
        assert rp is not None
        assert rp.connected is False
    finally:
        db.close()


@pytest.mark.asyncio
async def test_disconnect_removes_after_grace(monkeypatch):
    db = SessionLocal()
    try:
        user = User(email="disc2@example.com", password_hash=hash_password("secret"))
        db.add(user)
        db.add(Word(text="grace2", difficulty=1, active=True))
        db.commit()
        db.refresh(user)
        token = create_access_token(str(user.id))
    finally:
        db.close()

    # speed up grace period by patching sleep
    async def fast_sleep(_):
        return

    monkeypatch.setattr("app.sockets.events.asyncio.sleep", fast_sleep)

    eio_sid = "eio-disc2"
    sid = await sio.manager.connect(eio_sid, "/")
    create_res = await sio._trigger_event(
        "room:create",
        "/",
        sid,
        {"token": token, "rounds_total": 1, "difficulty": 1, "turn_seconds": 60, "max_players": 20},
    )
    player_id = create_res["lobby"]["self_player_id"]
    await sio._trigger_event("disconnect", "/", sid)
    await asyncio.sleep(0)

    from app.services.game_state import PLAYER_GRACE_TASKS
    task = PLAYER_GRACE_TASKS.get(player_id)
    if task:
        await task

    db = SessionLocal()
    try:
        from app.models.room_player import RoomPlayer

        rp = db.query(RoomPlayer).filter(RoomPlayer.id == player_id).first()
        assert rp is not None
        assert rp.in_game is False
    finally:
        db.close()
