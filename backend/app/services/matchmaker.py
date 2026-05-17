"""In-memory matchmaker for Quick Play trivia.

Maintains per-category queues keyed by trivia category. When a second user
joins the same category, both are paired into a new Room. After 15s with no
pair, the user is matched against a bot.

State is intentionally non-persistent. On backend restart, in-flight queues
are dropped; clients see a socket disconnect and re-queue.
"""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


FALLBACK_SECONDS = 15
START_TIMEOUT_SECONDS = 10  # 10s safety for quickmatch:ready gating


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
    if user_id in USER_IN_QUEUE:
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
            USER_IN_QUEUE.pop(partner.user_id, None)
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
            USER_IN_QUEUE.pop(user_id, None)
        await on_bot_fallback(entry)

    entry.fallback_task = asyncio.create_task(_fallback())
    return {"ok": True, "status": "searching", "wait_seconds": FALLBACK_SECONDS}
