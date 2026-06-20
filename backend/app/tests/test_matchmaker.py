"""Matchmaker service — queue mechanics, pairing, bot fallback."""

import asyncio
from pathlib import Path
import pytest

from app.services import matchmaker


@pytest.fixture(autouse=True)
def reset_matchmaker():
    matchmaker.QUEUES.clear()
    matchmaker.USER_IN_QUEUE.clear()
    matchmaker.PENDING_STARTS.clear()
    yield
    # Cancel any pending fallback tasks before clearing.
    for q in matchmaker.QUEUES.values():
        for e in q:
            if e.fallback_task and not e.fallback_task.done():
                try:
                    e.fallback_task.cancel()
                except RuntimeError:
                    pass
    for e in list(matchmaker.USER_IN_QUEUE.values()):
        if e.fallback_task and not e.fallback_task.done():
            try:
                e.fallback_task.cancel()
            except RuntimeError:
                pass
    for pending in matchmaker.PENDING_STARTS.values():
        task = pending.get("task")
        if task and not task.done():
            try:
                task.cancel()
            except RuntimeError:
                pass
    matchmaker.QUEUES.clear()
    matchmaker.USER_IN_QUEUE.clear()
    matchmaker.PENDING_STARTS.clear()


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
async def test_join_queue_switches_duplicate_user_to_new_category():
    await matchmaker.join_queue(
        user_id=1, sid="sid1", category="science",
        on_pair=lambda *a, **kw: None, on_bot_fallback=lambda *a, **kw: None,
    )
    res = await matchmaker.join_queue(
        user_id=1, sid="sid2", category="history",
        on_pair=lambda *a, **kw: None, on_bot_fallback=lambda *a, **kw: None,
    )
    assert res["ok"] is True
    assert res["status"] == "searching"
    assert matchmaker.QUEUES["science"] == []
    assert len(matchmaker.QUEUES["history"]) == 1
    assert matchmaker.USER_IN_QUEUE[1].category == "history"


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


def test_indian_law_is_quickmatch_category():
    assert "indian_law" in matchmaker.GK_CATEGORIES


def test_indian_law_is_trivia_gk_subcategory():
    source = Path(__file__).parents[1] / "sockets" / "events.py"
    text = source.read_text()
    assert '"indian_law"' in text


@pytest.mark.asyncio
async def test_resolve_category_passthrough():
    """Non-surprise categories pass through unchanged."""
    assert matchmaker.resolve_category("science") == "science"
    assert matchmaker.resolve_category("history") == "history"


@pytest.mark.asyncio
async def test_register_ready_both_clients_starts_game(monkeypatch):
    monkeypatch.setattr(matchmaker, "START_TIMEOUT_SECONDS", 1.0)
    started = []
    async def on_start(room_code):
        started.append(room_code)
    matchmaker.register_pending_start("ROOM1", expected_user_ids={1, 2}, on_start=on_start)

    await matchmaker.register_ready(room_code="ROOM1", user_id=1)
    assert started == []

    await matchmaker.register_ready(room_code="ROOM1", user_id=2)
    await asyncio.sleep(0.05)  # let on_start coroutine schedule
    assert started == ["ROOM1"]


@pytest.mark.asyncio
async def test_register_ready_timeout_starts_game(monkeypatch):
    monkeypatch.setattr(matchmaker, "START_TIMEOUT_SECONDS", 0.1)
    started = []
    async def on_start(room_code):
        started.append(room_code)
    matchmaker.register_pending_start("ROOM2", expected_user_ids={1, 2}, on_start=on_start)
    await asyncio.sleep(0.25)
    assert started == ["ROOM2"]


@pytest.mark.asyncio
async def test_register_ready_unknown_room_noop():
    """Late ready events for already-started or non-existent rooms must not crash."""
    # Should be a no-op, not raise.
    await matchmaker.register_ready(room_code="NOPE", user_id=1)


@pytest.mark.asyncio
async def test_pending_starts_cleaned_after_all_ready(monkeypatch):
    monkeypatch.setattr(matchmaker, "START_TIMEOUT_SECONDS", 5.0)
    async def on_start(room_code):
        pass
    matchmaker.register_pending_start("ROOM3", expected_user_ids={1}, on_start=on_start)
    await matchmaker.register_ready("ROOM3", 1)
    await asyncio.sleep(0.05)
    assert "ROOM3" not in matchmaker.PENDING_STARTS
