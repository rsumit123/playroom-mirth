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
