"""Matchmaker service — queue mechanics, pairing, bot fallback."""

import asyncio
import pytest

from app.services import matchmaker


@pytest.fixture(autouse=True)
def reset_matchmaker():
    matchmaker.QUEUES.clear()
    matchmaker.USER_IN_QUEUE.clear()
    yield
    # Cancel any pending fallback tasks before clearing.
    # Guard with try/except: sync teardown may run after the async event loop closes.
    all_entries = list(matchmaker.USER_IN_QUEUE.values())
    for q in matchmaker.QUEUES.values():
        all_entries.extend(q)
    for e in all_entries:
        if e.fallback_task and not e.fallback_task.done():
            try:
                e.fallback_task.cancel()
            except RuntimeError:
                pass  # event loop already closed
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


@pytest.mark.asyncio
async def test_cancel_queue_while_searching():
    await matchmaker.join_queue(
        user_id=1, sid="sid1", category="science",
        on_pair=lambda *a, **kw: None, on_bot_fallback=lambda *a, **kw: None,
    )
    res = await matchmaker.cancel_queue(user_id=1)
    assert res["ok"] is True
    assert 1 not in matchmaker.USER_IN_QUEUE
    assert matchmaker.QUEUES["science"] == []


@pytest.mark.asyncio
async def test_cancel_queue_after_match_returns_already_matched():
    paired = []
    async def on_pair(a, b):
        paired.append((a, b))
    await matchmaker.join_queue(
        user_id=1, sid="sid1", category="science",
        on_pair=on_pair, on_bot_fallback=lambda *a, **kw: None,
    )
    await matchmaker.join_queue(
        user_id=2, sid="sid2", category="science",
        on_pair=on_pair, on_bot_fallback=lambda *a, **kw: None,
    )
    # Now user 1 is matched; cancel should report ALREADY_MATCHED.
    res = await matchmaker.cancel_queue(user_id=1)
    assert res["ok"] is False
    assert res["error"] == "ALREADY_MATCHED"


@pytest.mark.asyncio
async def test_bot_fallback_fires_after_timeout(monkeypatch):
    # Shorten fallback for the test.
    monkeypatch.setattr(matchmaker, "FALLBACK_SECONDS", 0.1)
    called = []
    async def on_bot(entry):
        called.append(entry)
    await matchmaker.join_queue(
        user_id=1, sid="sid1", category="science",
        on_pair=lambda *a, **kw: None, on_bot_fallback=on_bot,
    )
    await asyncio.sleep(0.3)
    assert len(called) == 1
    assert called[0].user_id == 1
    # User entry stays in USER_IN_QUEUE with matched=True (invariant from Task 2.3)
    assert 1 in matchmaker.USER_IN_QUEUE
    assert matchmaker.USER_IN_QUEUE[1].matched is True


@pytest.mark.asyncio
async def test_surprise_resolves_to_a_real_category():
    resolved = matchmaker.resolve_category("surprise")
    assert resolved in matchmaker.GK_CATEGORIES


@pytest.mark.asyncio
async def test_resolve_category_passthrough():
    """Non-surprise categories pass through unchanged."""
    assert matchmaker.resolve_category("science") == "science"
    assert matchmaker.resolve_category("history") == "history"
