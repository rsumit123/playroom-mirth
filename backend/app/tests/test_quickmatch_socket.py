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
