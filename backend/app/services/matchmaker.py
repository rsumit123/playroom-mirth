"""In-memory matchmaker for Quick Play trivia.

Maintains per-category queues keyed by trivia category. When a second user
joins the same category, both are paired into a new Room. After 15s with no
pair, the user is matched against a bot.

State is intentionally non-persistent. On backend restart, in-flight queues
are dropped; clients see a socket disconnect and re-queue.
"""

import asyncio
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


FALLBACK_SECONDS = 15
START_TIMEOUT_SECONDS = 10  # 10s safety for quickmatch:ready gating
REMATCH_TIMEOUT_SECONDS = 15


@dataclass
class QueueEntry:
    user_id: int
    sid: str
    joined_at: float
    category: str
    matched: bool = False
    fallback_task: Optional[asyncio.Task] = None


QUEUES: dict[str, list[QueueEntry]] = defaultdict(list)
USER_IN_QUEUE: dict[int, QueueEntry] = {}
QUEUE_LOCKS: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

# Rooms awaiting both clients' quickmatch:ready before game starts.
# Maps room_code -> { "expected": set[user_id], "ready": set[user_id], "task": asyncio.Task }
PENDING_STARTS: dict[str, dict] = {}

# Pending human rematch requests, keyed by the OLD (just-finished) quickmatch
# room_code. Once both ex-opponents request a rematch, the on_pair callback
# fires (which creates a fresh room via the normal pair-humans flow). After
# REMATCH_TIMEOUT_SECONDS, on_timeout fires for any still-waiting requester.
REMATCH_REQUESTS: dict[str, dict] = {}


async def join_queue(
    user_id: int,
    sid: str,
    category: str,
    on_pair,  # async callable(entry_a: QueueEntry, entry_b: QueueEntry)
    on_bot_fallback,  # async callable(entry: QueueEntry)
) -> dict:
    """Add user to queue, attempt immediate pair, otherwise schedule bot fallback.

    Returns one of:
      {"ok": True, "status": "searching", "wait_seconds": 15}
      {"ok": True, "status": "matched"}  # paired immediately
      {"ok": False, "error": "ALREADY_IN_QUEUE"}
    """
    # Invariant: USER_IN_QUEUE entries are NEVER removed on pairing or bot-fallback.
    # They stay (with entry.matched=True) so that cancel_queue can distinguish
    # "already matched" from "never queued". Entries are cleaned up by the
    # disconnect/room-end handler in Phase 4.
    if user_id in USER_IN_QUEUE and not USER_IN_QUEUE[user_id].matched:
        return {"ok": False, "error": "ALREADY_IN_QUEUE"}

    entry = QueueEntry(
        user_id=user_id, sid=sid, joined_at=time.time(), category=category,
    )

    lock = QUEUE_LOCKS[category]
    async with lock:
        # Try to pair with an existing waiting entry.
        waiting = QUEUES[category]
        if waiting:
            partner = waiting.pop(0)
            partner.matched = True
            entry.matched = True
            if partner.fallback_task and not partner.fallback_task.done():
                partner.fallback_task.cancel()
            # Do NOT pop from USER_IN_QUEUE — matched entries stay so that
            # cancel_queue can return ALREADY_MATCHED instead of NOT_IN_QUEUE.
            USER_IN_QUEUE[partner.user_id] = partner  # ensure present (already is)
            USER_IN_QUEUE[user_id] = entry
            await on_pair(partner, entry)
            return {"ok": True, "status": "matched"}

        # No pair available — enqueue and schedule fallback.
        QUEUES[category].append(entry)
        USER_IN_QUEUE[user_id] = entry

    async def _fallback():
        try:
            await asyncio.sleep(FALLBACK_SECONDS)
        except asyncio.CancelledError:
            return
        async with QUEUE_LOCKS[category]:
            if entry.matched:
                return
            entry.matched = True
            try:
                QUEUES[category].remove(entry)
            except ValueError:
                pass
            # Keep entry in USER_IN_QUEUE with matched=True (see invariant above).
        await on_bot_fallback(entry)

    entry.fallback_task = asyncio.create_task(_fallback())
    return {"ok": True, "status": "searching", "wait_seconds": FALLBACK_SECONDS}


async def cancel_queue(user_id: int) -> dict:
    """Remove user from queue if still waiting. Returns ALREADY_MATCHED if their
    entry already paired or fell back to bot. Returns NOT_IN_QUEUE if never queued."""
    entry = USER_IN_QUEUE.get(user_id)
    if entry is None:
        return {"ok": False, "error": "NOT_IN_QUEUE"}
    async with QUEUE_LOCKS[entry.category]:
        if entry.matched:
            return {"ok": False, "error": "ALREADY_MATCHED"}
        entry.matched = True  # poison so any concurrent fallback no-ops
        try:
            QUEUES[entry.category].remove(entry)
        except ValueError:
            pass
        USER_IN_QUEUE.pop(user_id, None)
        if entry.fallback_task and not entry.fallback_task.done():
            entry.fallback_task.cancel()
    return {"ok": True}


def register_pending_start(
    room_code: str,
    expected_user_ids: set[int],
    on_start,  # async callable(room_code)
) -> None:
    """Register a quickmatch room that needs all listed users to send
    `quickmatch:ready` before the game starts. After START_TIMEOUT_SECONDS,
    the game starts anyway."""
    async def _timeout():
        try:
            await asyncio.sleep(START_TIMEOUT_SECONDS)
        except asyncio.CancelledError:
            return
        pending = PENDING_STARTS.pop(room_code, None)
        if pending is None:
            return
        await on_start(room_code)

    task = asyncio.create_task(_timeout())
    PENDING_STARTS[room_code] = {
        "expected": set(expected_user_ids),
        "ready": set(),
        "on_start": on_start,
        "task": task,
    }


async def register_ready(room_code: str, user_id: int) -> None:
    pending = PENDING_STARTS.get(room_code)
    if pending is None:
        return
    pending["ready"].add(user_id)
    if pending["ready"] >= pending["expected"]:
        # All ready — cancel timeout and start.
        PENDING_STARTS.pop(room_code, None)
        if pending["task"] and not pending["task"].done():
            pending["task"].cancel()
        await pending["on_start"](room_code)


async def request_rematch(
    old_room_code: str,
    user_id: int,
    sid: str,
    expected_user_ids: set[int],
    category: str,
    on_pair,     # async callable(sids: dict[int, str])
    on_timeout,  # async callable(sid: str)
) -> dict:
    """Record one ex-opponent's intent to rematch. When both expected users have
    requested, fire on_pair with their sids. Otherwise start (or keep) a timeout
    that will fire on_timeout for each still-waiting requester.

    Returns:
      {"ok": True, "status": "waiting"}  — first requester, partner still has time
      {"ok": True, "status": "matched"}  — both in, on_pair already called
    """
    state = REMATCH_REQUESTS.get(old_room_code)
    if state is None:
        async def _expire():
            try:
                await asyncio.sleep(REMATCH_TIMEOUT_SECONDS)
            except asyncio.CancelledError:
                return
            cur = REMATCH_REQUESTS.pop(old_room_code, None)
            if cur is None:
                return
            for waiting_sid in cur["sids"].values():
                await cur["on_timeout"](waiting_sid)

        task = asyncio.create_task(_expire())
        REMATCH_REQUESTS[old_room_code] = {
            "expected": set(expected_user_ids),
            "sids": {user_id: sid},
            "category": category,
            "task": task,
            "on_pair": on_pair,
            "on_timeout": on_timeout,
        }
        return {"ok": True, "status": "waiting"}

    # Re-request from the same user is idempotent (refresh their sid).
    state["sids"][user_id] = sid
    if set(state["sids"].keys()) >= state["expected"]:
        REMATCH_REQUESTS.pop(old_room_code, None)
        if state["task"] and not state["task"].done():
            state["task"].cancel()
        await state["on_pair"](dict(state["sids"]))
        return {"ok": True, "status": "matched"}
    return {"ok": True, "status": "waiting"}


async def cancel_rematch(old_room_code: str, user_id: int) -> dict:
    """Explicitly cancel a pending rematch (user clicked Cancel or left).
    Notifies the partner via on_timeout (treated as a decline)."""
    state = REMATCH_REQUESTS.pop(old_room_code, None)
    if state is None:
        return {"ok": False, "error": "NOT_PENDING"}
    if state["task"] and not state["task"].done():
        state["task"].cancel()
    for uid, partner_sid in state["sids"].items():
        if uid != user_id:
            await state["on_timeout"](partner_sid)
    return {"ok": True}


GK_CATEGORIES = [
    "general_knowledge", "science", "general", "history", "geography",
    "sports", "entertainment", "mythology", "food", "politics",
    "defense", "current_affairs", "math",
]


def resolve_category(category: str) -> str:
    """Map 'surprise' to a randomly chosen real category. Other values pass through."""
    if category == "surprise":
        return random.choice(GK_CATEGORIES)
    return category
