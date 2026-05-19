"""Socket-level tests for quickmatch:* events."""

import asyncio
import uuid

import pytest

from app.db.session import SessionLocal
from app.models.user import User
from app.services.auth import create_access_token
from app.services.bot_users import seed_bot_users
from app.services import matchmaker
from app.sockets.events import sio


def _make_user(prefix: str) -> tuple[int, str]:
    db = SessionLocal()
    try:
        suffix = uuid.uuid4().hex[:8]
        u = User(email=f"{prefix}-{suffix}@x.com", google_id=f"g-{prefix}-{suffix}")
        db.add(u)
        db.commit()
        db.refresh(u)
        return u.id, create_access_token(str(u.id))
    finally:
        db.close()


@pytest.fixture(autouse=True)
def reset_matchmaker():
    matchmaker.QUEUES.clear()
    matchmaker.USER_IN_QUEUE.clear()
    matchmaker.PENDING_STARTS.clear()
    yield
    matchmaker.QUEUES.clear()
    matchmaker.USER_IN_QUEUE.clear()
    matchmaker.PENDING_STARTS.clear()


@pytest.mark.asyncio
async def test_quickmatch_join_emits_searching():
    _, token = _make_user("qm-a")
    sid = await sio.manager.connect(f"eio-{uuid.uuid4().hex[:6]}", "/")
    res = await sio._trigger_event(
        "quickmatch:join", "/", sid,
        {"token": token, "category": "science"},
    )
    assert res["ok"] is True
    assert res["status"] == "searching"


@pytest.mark.asyncio
async def test_quickmatch_join_pairs_two_users():
    db = SessionLocal()
    try:
        seed_bot_users(db)
    finally:
        db.close()

    _, ta = _make_user("qm-a")
    _, tb = _make_user("qm-b")
    sid_a = await sio.manager.connect(f"eio-{uuid.uuid4().hex[:6]}", "/")
    sid_b = await sio.manager.connect(f"eio-{uuid.uuid4().hex[:6]}", "/")

    res_a = await sio._trigger_event("quickmatch:join", "/", sid_a,
                                     {"token": ta, "category": "science"})
    res_b = await sio._trigger_event("quickmatch:join", "/", sid_b,
                                     {"token": tb, "category": "science"})
    assert res_a["ok"] is True
    assert res_b["ok"] is True
    # After the second join, neither user is still in the queue.
    assert matchmaker.USER_IN_QUEUE == {}


@pytest.mark.asyncio
async def test_quickmatch_cancel_while_searching():
    _, token = _make_user("qm-c")
    sid = await sio.manager.connect(f"eio-{uuid.uuid4().hex[:6]}", "/")
    await sio._trigger_event("quickmatch:join", "/", sid,
                             {"token": token, "category": "science"})
    res = await sio._trigger_event("quickmatch:cancel", "/", sid,
                                   {"token": token})
    assert res["ok"] is True
    assert matchmaker.USER_IN_QUEUE == {}


@pytest.mark.asyncio
async def test_disconnect_drops_user_from_queue():
    _, token = _make_user("qm-d")
    sid = await sio.manager.connect(f"eio-{uuid.uuid4().hex[:6]}", "/")
    await sio._trigger_event("quickmatch:join", "/", sid,
                             {"token": token, "category": "science"})
    await sio._trigger_event("disconnect", "/", sid)
    await asyncio.sleep(0.05)
    assert matchmaker.USER_IN_QUEUE == {}


@pytest.mark.asyncio
async def test_bot_fallback_creates_match(monkeypatch):
    monkeypatch.setattr(matchmaker, "FALLBACK_SECONDS", 0.2)
    db = SessionLocal()
    try:
        seed_bot_users(db)
    finally:
        db.close()
    _, token = _make_user("qm-f")
    sid = await sio.manager.connect(f"eio-{uuid.uuid4().hex[:6]}", "/")
    await sio._trigger_event("quickmatch:join", "/", sid,
                             {"token": token, "category": "science"})
    await asyncio.sleep(0.6)
    # The user should now be removed from the queue and assigned to a room.
    assert matchmaker.USER_IN_QUEUE == {}


@pytest.mark.asyncio
async def test_quickmatch_ready_starts_game_when_both_ready(monkeypatch):
    """Two humans pair, both send :ready, game should auto-start."""
    monkeypatch.setattr(matchmaker, "START_TIMEOUT_SECONDS", 5.0)
    db = SessionLocal()
    try:
        seed_bot_users(db)
    finally:
        db.close()

    _, ta = _make_user("qm-r-a")
    _, tb = _make_user("qm-r-b")
    sid_a = await sio.manager.connect(f"eio-{uuid.uuid4().hex[:6]}", "/")
    sid_b = await sio.manager.connect(f"eio-{uuid.uuid4().hex[:6]}", "/")
    await sio._trigger_event("quickmatch:join", "/", sid_a,
                             {"token": ta, "category": "science"})
    await sio._trigger_event("quickmatch:join", "/", sid_b,
                             {"token": tb, "category": "science"})
    # Now both should be in a room. Find it.
    from app.services.game_state import ROOM_STATES
    assert len(matchmaker.PENDING_STARTS) == 1
    room_code = next(iter(matchmaker.PENDING_STARTS))

    await sio._trigger_event("quickmatch:ready", "/", sid_a,
                             {"token": ta, "room_code": room_code})
    await sio._trigger_event("quickmatch:ready", "/", sid_b,
                             {"token": tb, "room_code": room_code})
    await asyncio.sleep(0.1)
    # Game has started — pending entry is removed, ROOM_STATES has the room.
    assert room_code not in matchmaker.PENDING_STARTS
    assert room_code in ROOM_STATES


@pytest.mark.asyncio
async def test_quickmatch_leave_forfeits_to_survivor(monkeypatch):
    monkeypatch.setattr(matchmaker, "START_TIMEOUT_SECONDS", 5.0)
    db = SessionLocal()
    try:
        seed_bot_users(db)
    finally:
        db.close()
    _, ta = _make_user("qm-l-a")
    _, tb = _make_user("qm-l-b")
    sid_a = await sio.manager.connect(f"eio-{uuid.uuid4().hex[:6]}", "/")
    sid_b = await sio.manager.connect(f"eio-{uuid.uuid4().hex[:6]}", "/")
    await sio._trigger_event("quickmatch:join", "/", sid_a,
                             {"token": ta, "category": "science"})
    await sio._trigger_event("quickmatch:join", "/", sid_b,
                             {"token": tb, "category": "science"})
    room_code = next(iter(matchmaker.PENDING_STARTS))
    await sio._trigger_event("quickmatch:ready", "/", sid_a,
                             {"token": ta, "room_code": room_code})
    await sio._trigger_event("quickmatch:ready", "/", sid_b,
                             {"token": tb, "room_code": room_code})
    await asyncio.sleep(0.1)

    from app.services.game_state import ROOM_STATES, SID_TO_PLAYER
    state = ROOM_STATES[room_code]
    survivor_pid = SID_TO_PLAYER[sid_b]

    emitted = []
    orig_emit = sio.emit
    async def capture(event, payload, room=None, **kw):
        emitted.append((event, payload))
        await orig_emit(event, payload, room=room, **kw)
    monkeypatch.setattr(sio, "emit", capture)

    await sio._trigger_event("game:leave", "/", sid_a,
                             {"room_code": room_code, "token": ta})
    await asyncio.sleep(0.1)

    game_end = [p for e, p in emitted if e == "game:game_end"]
    assert game_end, "expected game:game_end"
    assert game_end[0]["winner_player_id"] == survivor_pid


@pytest.mark.asyncio
async def test_quickmatch_room_hidden_from_active_listing(monkeypatch):
    """Quickmatch rooms must not appear in a user's active-rooms listing."""
    from fastapi.testclient import TestClient
    from app.main import fastapi_app

    monkeypatch.setattr(matchmaker, "FALLBACK_SECONDS", 0.2)
    db = SessionLocal()
    try:
        seed_bot_users(db)
    finally:
        db.close()

    user_id, token = _make_user("qm-h")
    sid = await sio.manager.connect(f"eio-{uuid.uuid4().hex[:6]}", "/")
    await sio._trigger_event("quickmatch:join", "/", sid,
                             {"token": token, "category": "science"})
    await asyncio.sleep(0.5)

    client = TestClient(fastapi_app)
    r = client.get("/rooms/active", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    for room in r.json():
        # The quickmatch room must not appear in the active listing.
        assert room.get("origin", "friends") != "quickmatch"


@pytest.mark.asyncio
async def test_room_join_blocked_for_quickmatch_room():
    """room:join via socket must return NOT_FOUND for quickmatch rooms."""
    db = SessionLocal()
    try:
        seed_bot_users(db)
    finally:
        db.close()

    _, ta = _make_user("qm-j-a")
    _, tb = _make_user("qm-j-b")
    sid_a = await sio.manager.connect(f"eio-{uuid.uuid4().hex[:6]}", "/")
    sid_b = await sio.manager.connect(f"eio-{uuid.uuid4().hex[:6]}", "/")
    await sio._trigger_event("quickmatch:join", "/", sid_a,
                             {"token": ta, "category": "science"})
    await sio._trigger_event("quickmatch:join", "/", sid_b,
                             {"token": tb, "category": "science"})
    # They should now be paired; find the room code.
    assert matchmaker.USER_IN_QUEUE == {}
    from app.db.session import SessionLocal as SL
    from app.models.room import Room
    db2 = SL()
    try:
        room = db2.query(Room).filter(Room.origin == "quickmatch").first()
        assert room is not None, "quickmatch room should have been created"
        room_code = room.code
    finally:
        db2.close()

    # A third user trying to join via room:join should get NOT_FOUND.
    _, tc = _make_user("qm-j-c")
    sid_c = await sio.manager.connect(f"eio-{uuid.uuid4().hex[:6]}", "/")
    res = await sio._trigger_event("room:join", "/", sid_c,
                                   {"token": tc, "room_code": room_code})
    assert res["ok"] is False
    assert res["error"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_invite_blocked_for_quickmatch_room():
    """POST /rooms/{room_code}/invite must return 404 for quickmatch rooms."""
    from fastapi.testclient import TestClient
    from app.main import fastapi_app

    db = SessionLocal()
    try:
        seed_bot_users(db)
    finally:
        db.close()

    _, ta = _make_user("qm-i-a")
    _, tb = _make_user("qm-i-b")
    sid_a = await sio.manager.connect(f"eio-{uuid.uuid4().hex[:6]}", "/")
    sid_b = await sio.manager.connect(f"eio-{uuid.uuid4().hex[:6]}", "/")
    await sio._trigger_event("quickmatch:join", "/", sid_a,
                             {"token": ta, "category": "science"})
    await sio._trigger_event("quickmatch:join", "/", sid_b,
                             {"token": tb, "category": "science"})
    assert matchmaker.USER_IN_QUEUE == {}
    from app.models.room import Room as RoomModel
    from app.models.user import User as UserModel
    db2 = SessionLocal()
    try:
        room = db2.query(RoomModel).filter(RoomModel.origin == "quickmatch").first()
        assert room is not None
        room_code = room.code
        # Create a third user to act as an invitee (friendship not needed for the 404 check)
        suffix = uuid.uuid4().hex[:8]
        friend = UserModel(email=f"qm-i-f-{suffix}@x.com", google_id=f"g-qm-i-f-{suffix}")
        db2.add(friend)
        db2.commit()
        db2.refresh(friend)
        friend_id = friend.id
    finally:
        db2.close()

    client = TestClient(fastapi_app)
    r = client.post(
        f"/rooms/{room_code}/invite",
        json={"user_id": friend_id},
        headers={"Authorization": f"Bearer {ta}"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_rematch_bot_pairs_instantly_without_queue():
    """quickmatch:rematch_bot must skip the 15s queue and emit matched
    synchronously — the user has already played a bot game and shouldn't
    sit through another search countdown for a guaranteed bot pairing."""
    db = SessionLocal()
    try:
        seed_bot_users(db)
    finally:
        db.close()
    _, token = _make_user("qm-rb")
    sid = await sio.manager.connect(f"eio-{uuid.uuid4().hex[:6]}", "/")

    res = await sio._trigger_event(
        "quickmatch:rematch_bot", "/", sid,
        {"token": token, "category": "science"},
    )
    assert res["ok"] is True

    # User was never enqueued — no 15s timer started.
    assert matchmaker.USER_IN_QUEUE == {}
    # A pending-start gate exists for the new room.
    assert len(matchmaker.PENDING_STARTS) == 1


@pytest.mark.asyncio
async def test_rematch_bot_rejects_unauthenticated():
    sid = await sio.manager.connect(f"eio-{uuid.uuid4().hex[:6]}", "/")
    res = await sio._trigger_event(
        "quickmatch:rematch_bot", "/", sid,
        {"token": "garbage", "category": "science"},
    )
    assert res["ok"] is False
    assert res["error"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_quickmatch_matched_payload_flags_bot_match():
    """The quickmatch:matched event must carry is_bot_match=True for bot
    pairings so the frontend can route Rematch through quickmatch:rematch_bot
    instead of re-queueing."""
    monkeypatch_calls = []

    db = SessionLocal()
    try:
        seed_bot_users(db)
    finally:
        db.close()
    _, token = _make_user("qm-flag")
    sid = await sio.manager.connect(f"eio-{uuid.uuid4().hex[:6]}", "/")

    captured = []
    original_emit = sio.emit
    async def capture(event, payload=None, **kw):
        if event == "quickmatch:matched":
            captured.append(payload)
        return await original_emit(event, payload, **kw) if payload is not None else await original_emit(event, **kw)
    sio.emit = capture
    try:
        await sio._trigger_event(
            "quickmatch:rematch_bot", "/", sid,
            {"token": token, "category": "science"},
        )
    finally:
        sio.emit = original_emit

    assert captured, "expected quickmatch:matched"
    assert captured[0].get("is_bot_match") is True


@pytest.mark.asyncio
async def test_lobby_uses_user_display_name_not_email_prefix():
    """When a User has a display_name, lobby_state must surface that — not the
    email local-part. This is the bug that made bot 'Rohan' appear in-game as
    'bot_rohan' (their email prefix) instead of the proper display name."""
    from app.models.room import Room
    from app.models.room_player import RoomPlayer
    from app.services.room_ops import lobby_state

    db = SessionLocal()
    try:
        seed_bot_users(db)
        # Find the bot named "Rohan".
        bot = db.query(User).filter(User.display_name == "Rohan", User.is_bot == True).first()  # noqa: E712
        assert bot, "expected seeded bot 'Rohan'"
        assert bot.email == "bot_rohan@quickmatch.local"

        # Create a real human host alongside the bot so the room has 2 players.
        host_id, _ = _make_user("display-name-host")
        host = db.query(User).filter(User.id == host_id).first()
        host.display_name = "Aditi"
        db.commit()

        room = Room(
            code=f"DN{uuid.uuid4().hex[:4].upper()}",
            host_user_id=host.id, status="lobby", rounds_total=1,
            difficulty=1, turn_seconds=15, max_players=2, min_players=2,
            game_type="trivia", origin="quickmatch",
        )
        db.add(room)
        db.commit()
        db.refresh(room)
        db.add_all([
            RoomPlayer(room_id=room.id, user_id=host.id, join_order=1, score=0, in_game=True, connected=True),
            RoomPlayer(room_id=room.id, user_id=bot.id, join_order=2, score=0, in_game=True, connected=True),
        ])
        db.commit()

        snap = lobby_state(db, room)
        names = {p.user_id: p.display_name for p in snap.players}
        assert names[host.id] == "Aditi", f"expected 'Aditi', got {names[host.id]!r}"
        assert names[bot.id] == "Rohan", f"expected 'Rohan', got {names[bot.id]!r}"
    finally:
        db.close()
