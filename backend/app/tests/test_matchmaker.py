"""Matchmaker service — queue mechanics, pairing, bot fallback."""

import asyncio
import pytest

from app.services import matchmaker


@pytest.fixture(autouse=True)
def reset_matchmaker():
    matchmaker.QUEUES.clear()
    matchmaker.USER_IN_QUEUE.clear()
    yield
    matchmaker.QUEUES.clear()
    matchmaker.USER_IN_QUEUE.clear()


def test_queue_starts_empty():
    assert len(matchmaker.QUEUES) == 0
    assert len(matchmaker.USER_IN_QUEUE) == 0


@pytest.mark.asyncio
async def test_join_queue_appends_entry():
    res = await matchmaker.join_queue(
        user_id=1, sid="sid1", category="science",
        on_pair=lambda *a, **kw: None,
        on_bot_fallback=lambda *a, **kw: None,
    )
    assert res["ok"] is True
    assert res["status"] == "searching"
    assert 1 in matchmaker.USER_IN_QUEUE
    assert len(matchmaker.QUEUES["science"]) == 1


@pytest.mark.asyncio
async def test_join_queue_rejects_duplicate_user():
    await matchmaker.join_queue(
        user_id=1, sid="sid1", category="science",
        on_pair=lambda *a, **kw: None, on_bot_fallback=lambda *a, **kw: None,
    )
    res = await matchmaker.join_queue(
        user_id=1, sid="sid2", category="history",
        on_pair=lambda *a, **kw: None, on_bot_fallback=lambda *a, **kw: None,
    )
    assert res["ok"] is False
    assert res["error"] == "ALREADY_IN_QUEUE"
