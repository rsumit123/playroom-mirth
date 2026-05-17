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
