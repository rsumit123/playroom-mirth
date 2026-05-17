# Quick Play Trivia Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 1v1 trivia matchmaking with a 15-second bot fallback. Signed-in users get a "Quick Play" CTA on the Trivia setup screen; queue pairs two real users or assigns a disguised bot opponent after the timeout. Spec: `docs/superpowers/specs/2026-05-17-quickmatch-trivia-design.md`.

**Architecture:** In-memory matchmaker (`services/matchmaker.py`) on top of existing Rooms. Bots are real `User` rows with `is_bot=True`; their answers are injected by an asyncio worker (`services/trivia_bot.py`) that hooks into `_trivia_send_question`. Quickmatch rooms carry `Room.origin="quickmatch"` and are hidden from existing friend-flow surfaces. Three new columns (`User.is_bot`, `Room.origin`, `GameHistory.origin`), nine new socket events (`quickmatch:*`), four new frontend screens, one redesign of `GameSetup.jsx`, one extension of `GameEnd.jsx`.

**Tech Stack:** FastAPI + python-socketio + SQLAlchemy/SQLite (backend); React 18 + Vite + Capacitor (frontend); pytest (backend tests); Vitest + Playwright (frontend tests).

---

## Phase 0 — Pre-flight

Run the full existing test suite to establish a baseline. No regressions are introduced by this plan until later phases run; this check is purely to confirm a clean starting state.

- [ ] **Step 0.1: Run backend tests**

```bash
cd backend && .venv/bin/python -m pytest --tb=short -q
```

Expected: all pass except the 3 known live-server tests (`test_charades_scribble_e2e.py`, `test_scoreboard.py`) which fail with `ConnectionRefusedError` against `localhost:8005`. Note their failure count.

- [ ] **Step 0.2: Run frontend Vitest + build**

```bash
cd frontend && npx vitest run && npm run build
```

Expected: all pass.

---

## Phase 1 — Data model foundation

### Task 1.1: Add `User.is_bot` column

**Files:**
- Modify: `backend/app/models/user.py`
- Modify: `backend/app/db/init_db.py`
- Test: `backend/app/tests/test_user_is_bot.py`

- [ ] **Step 1.1.1: Write the failing test**

Create `backend/app/tests/test_user_is_bot.py`:

```python
"""User.is_bot column + idempotent migration."""

from sqlalchemy import inspect

from app.db.session import SessionLocal, engine
from app.models.user import User


def test_user_has_is_bot_column():
    inspector = inspect(engine)
    cols = {c["name"]: c for c in inspector.get_columns("users")}
    assert "is_bot" in cols
    assert cols["is_bot"]["default"] in (False, 0, "0", "false", "FALSE")


def test_default_is_bot_false():
    db = SessionLocal()
    try:
        u = User(email="testbot@example.com", google_id="g-testbot")
        db.add(u)
        db.commit()
        db.refresh(u)
        assert u.is_bot is False
    finally:
        db.close()
```

- [ ] **Step 1.1.2: Run test, confirm it fails**

```bash
cd backend && .venv/bin/python -m pytest app/tests/test_user_is_bot.py -v
```

Expected: FAIL with `KeyError: 'is_bot'` or `AttributeError: 'User' has no attribute 'is_bot'`.

- [ ] **Step 1.1.3: Add column to `User` model**

Edit `backend/app/models/user.py`. Add inside the `User` class:

```python
is_bot: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default="0")
```

Ensure `Boolean` is imported from `sqlalchemy` at the top.

- [ ] **Step 1.1.4: Add idempotent ALTER in `init_db.py`**

Locate `init_db()` in `backend/app/db/init_db.py`. After the existing `Base.metadata.create_all(...)` call, add an inline migration block following the established pattern (inspect columns; add if missing):

```python
def _ensure_column(engine, table: str, column: str, ddl: str) -> None:
    """Add a column if it doesn't already exist (SQLite-safe)."""
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    existing = {c["name"] for c in inspector.get_columns(table)}
    if column not in existing:
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))


def init_db() -> None:
    # ... existing code ...
    _ensure_column(engine, "users", "is_bot", "is_bot BOOLEAN NOT NULL DEFAULT 0")
```

If `_ensure_column` already exists or a similar helper is in place, reuse that. If multiple migrations already use this pattern, follow the file's convention.

- [ ] **Step 1.1.5: Run test, confirm it passes**

```bash
rm backend/test.db; .venv/bin/python -m pytest app/tests/test_user_is_bot.py -v
```

Expected: PASS. (Removing test.db forces a fresh init.)

- [ ] **Step 1.1.6: Commit**

```bash
git add backend/app/models/user.py backend/app/db/init_db.py backend/app/tests/test_user_is_bot.py
git commit -m "feat(quickmatch): add User.is_bot column with idempotent migration"
```

---

### Task 1.2: Add `Room.origin` column

**Files:**
- Modify: `backend/app/models/room.py`
- Modify: `backend/app/db/init_db.py`
- Test: `backend/app/tests/test_room_origin.py`

- [ ] **Step 1.2.1: Write the failing test**

Create `backend/app/tests/test_room_origin.py`:

```python
"""Room.origin column."""

from sqlalchemy import inspect

from app.db.session import SessionLocal, engine
from app.models.user import User
from app.models.room import Room


def test_room_has_origin_column():
    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns("rooms")}
    assert "origin" in cols


def test_room_origin_defaults_to_friends():
    db = SessionLocal()
    try:
        host = User(email="rh@example.com", google_id="g-rh")
        db.add(host)
        db.commit()
        db.refresh(host)
        r = Room(code="TEST01", host_user_id=host.id, status="lobby",
                 rounds_total=1, difficulty=1, turn_seconds=60,
                 max_players=2, min_players=2)
        db.add(r)
        db.commit()
        db.refresh(r)
        assert r.origin == "friends"
    finally:
        db.close()
```

- [ ] **Step 1.2.2: Run test, confirm it fails**

```bash
.venv/bin/python -m pytest app/tests/test_room_origin.py -v
```

Expected: FAIL with column or attribute missing.

- [ ] **Step 1.2.3: Add column to `Room` model**

Edit `backend/app/models/room.py`. Add inside `Room`:

```python
origin: Mapped[str] = mapped_column(String(20), default="friends", nullable=False, server_default="friends")
```

- [ ] **Step 1.2.4: Add ALTER in `init_db.py`**

After the User.is_bot migration line, add:

```python
_ensure_column(engine, "rooms", "origin", "origin VARCHAR(20) NOT NULL DEFAULT 'friends'")
```

- [ ] **Step 1.2.5: Run test, confirm it passes**

```bash
rm backend/test.db; .venv/bin/python -m pytest app/tests/test_room_origin.py -v
```

Expected: PASS.

- [ ] **Step 1.2.6: Commit**

```bash
git add backend/app/models/room.py backend/app/db/init_db.py backend/app/tests/test_room_origin.py
git commit -m "feat(quickmatch): add Room.origin column"
```

---

### Task 1.3: Add `GameHistory.origin` column

**Files:**
- Modify: `backend/app/models/game_history.py`
- Modify: `backend/app/db/init_db.py`
- Test: `backend/app/tests/test_game_history_origin.py`

- [ ] **Step 1.3.1: Write the failing test**

Create `backend/app/tests/test_game_history_origin.py`:

```python
from sqlalchemy import inspect
from app.db.session import engine


def test_game_history_has_origin_column():
    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns("game_history")}
    assert "origin" in cols
```

- [ ] **Step 1.3.2: Run test, confirm it fails**

```bash
.venv/bin/python -m pytest app/tests/test_game_history_origin.py -v
```

Expected: FAIL.

- [ ] **Step 1.3.3: Add column + migration**

Edit `backend/app/models/game_history.py`. Add:

```python
origin: Mapped[str] = mapped_column(String(20), default="friends", nullable=False, server_default="friends")
```

In `init_db.py`:

```python
_ensure_column(engine, "game_history", "origin", "origin VARCHAR(20) NOT NULL DEFAULT 'friends'")
```

- [ ] **Step 1.3.4: Run test, confirm it passes**

```bash
rm backend/test.db; .venv/bin/python -m pytest app/tests/test_game_history_origin.py -v
```

- [ ] **Step 1.3.5: Commit**

```bash
git add backend/app/models/game_history.py backend/app/db/init_db.py backend/app/tests/test_game_history_origin.py
git commit -m "feat(quickmatch): add GameHistory.origin column"
```

---

### Task 1.4: Add `origin` field to `RoomGameState`

**Files:**
- Modify: `backend/app/services/game_state.py`
- Test: `backend/app/tests/test_game_state_origin.py`

- [ ] **Step 1.4.1: Write the failing test**

Create `backend/app/tests/test_game_state_origin.py`:

```python
from app.services.game_state import RoomGameState, serialize_state, deserialize_state


def test_room_game_state_origin_default_friends():
    s = RoomGameState(room_id=1, room_code="ABC", rounds_total=1,
                      turn_seconds=60, difficulty=1)
    assert s.origin == "friends"


def test_room_game_state_origin_round_trip():
    s = RoomGameState(room_id=1, room_code="ABC", rounds_total=1,
                      turn_seconds=60, difficulty=1, origin="quickmatch")
    raw = serialize_state(s)
    restored = deserialize_state(raw)
    assert restored.origin == "quickmatch"
```

- [ ] **Step 1.4.2: Run test, confirm it fails**

```bash
.venv/bin/python -m pytest app/tests/test_game_state_origin.py -v
```

Expected: FAIL.

- [ ] **Step 1.4.3: Add field to dataclass + serialization**

Edit `backend/app/services/game_state.py`. Inside `@dataclass class RoomGameState:`, add (place near the other game-config fields):

```python
origin: str = "friends"
```

In `serialize_state`, add to the payload dict:

```python
"origin": state.origin,
```

In `deserialize_state`, add to the `RoomGameState(...)` constructor call:

```python
origin=data.get("origin", "friends"),
```

- [ ] **Step 1.4.4: Run test, confirm it passes**

```bash
.venv/bin/python -m pytest app/tests/test_game_state_origin.py -v
```

- [ ] **Step 1.4.5: Commit**

```bash
git add backend/app/services/game_state.py backend/app/tests/test_game_state_origin.py
git commit -m "feat(quickmatch): add origin field to RoomGameState"
```

---

### Task 1.5: Bot user pool + idempotent seeding

**Files:**
- Create: `backend/app/services/bot_users.py`
- Modify: `backend/app/db/init_db.py`
- Test: `backend/app/tests/test_bot_user_seed.py`

- [ ] **Step 1.5.1: Write the failing test**

Create `backend/app/tests/test_bot_user_seed.py`:

```python
from app.db.session import SessionLocal
from app.models.user import User
from app.services.bot_users import BOT_NAMES, seed_bot_users, pick_random_bot


def test_bot_users_seeded():
    db = SessionLocal()
    try:
        seed_bot_users(db)
        names = {n for n in BOT_NAMES}
        seeded = db.query(User).filter(User.is_bot == True).all()
        assert len(seeded) >= len(names)
        assert {u.email.split("@")[0].replace("bot_", "") for u in seeded} >= {n.lower() for n in names}
    finally:
        db.close()


def test_bot_seeding_is_idempotent():
    db = SessionLocal()
    try:
        seed_bot_users(db)
        seed_bot_users(db)
        seed_bot_users(db)
        count = db.query(User).filter(User.is_bot == True).count()
        assert count == len(BOT_NAMES)
    finally:
        db.close()


def test_pick_random_bot_returns_is_bot_user():
    db = SessionLocal()
    try:
        seed_bot_users(db)
        bot = pick_random_bot(db)
        assert bot.is_bot is True
    finally:
        db.close()
```

- [ ] **Step 1.5.2: Run test, confirm it fails**

```bash
.venv/bin/python -m pytest app/tests/test_bot_user_seed.py -v
```

Expected: FAIL with `ModuleNotFoundError: app.services.bot_users`.

- [ ] **Step 1.5.3: Create the service**

Create `backend/app/services/bot_users.py`:

```python
"""Bot user pool used as opponents in Quick Play matches.

Bots are real User rows flagged with is_bot=True so existing display-name
resolution, RoomPlayer joins, and scoring all work unchanged.
"""

import random

from sqlalchemy.orm import Session

from app.models.user import User


BOT_NAMES: list[str] = [
    "Priya", "Arjun", "Ananya", "Rohan", "Kavya", "Aditya",
    "Diya", "Vihaan", "Saanvi", "Krishna", "Ishaan", "Aaradhya",
    "Aanya", "Reyansh", "Myra", "Vivaan", "Aarav", "Anika",
    "Atharv", "Pari", "Kabir", "Sara", "Yash", "Tara",
    "Ved", "Riya", "Dev", "Aisha", "Aryan", "Meera",
]


def _bot_google_id(name: str) -> str:
    return f"bot-{name.lower()}"


def _bot_email(name: str) -> str:
    return f"bot_{name.lower()}@quickmatch.local"


def seed_bot_users(db: Session) -> None:
    """Insert any missing bot users. Idempotent."""
    existing_ids = {
        gid for (gid,) in db.query(User.google_id)
        .filter(User.is_bot == True).all()  # noqa: E712
    }
    for name in BOT_NAMES:
        gid = _bot_google_id(name)
        if gid in existing_ids:
            continue
        db.add(User(
            email=_bot_email(name),
            google_id=gid,
            display_name=name,
            is_bot=True,
        ))
    db.commit()


def pick_random_bot(db: Session, exclude_user_ids: set[int] | None = None) -> User:
    """Return a random bot user. exclude_user_ids skips bots already in use."""
    q = db.query(User).filter(User.is_bot == True)  # noqa: E712
    if exclude_user_ids:
        q = q.filter(~User.id.in_(exclude_user_ids))
    bots = q.all()
    if not bots:
        # Fallback if exclusion empties the pool — same bot in two rooms is fine.
        bots = db.query(User).filter(User.is_bot == True).all()  # noqa: E712
    return random.choice(bots)
```

Note: `User.display_name` may not exist as a column today. If it doesn't, the seeder still works — display name will resolve via existing logic (email or other fallback) — but the spec wants the bot's first name shown. Verify by inspecting `User` model. If `display_name` is missing, add it in a separate small task before this one, or remove that line from the seeder and rely on the existing display-name resolution path. **Confirm before proceeding.**

- [ ] **Step 1.5.4: Wire seeding into `init_db.py`**

Edit `backend/app/db/init_db.py`. At the end of `init_db()`:

```python
from app.services.bot_users import seed_bot_users
with SessionLocal() as db:
    seed_bot_users(db)
```

- [ ] **Step 1.5.5: Update `conftest.py` to preserve bots**

Edit `backend/app/tests/conftest.py`. Modify the `clear_users` autouse fixture so bots survive between tests:

```python
@pytest.fixture(autouse=True)
def clear_users():
    db = SessionLocal()
    try:
        db.query(RoomPlayer).delete()
        db.query(RoomState).delete()
        db.query(Room).delete()
        db.query(Guest).delete()
        db.query(Word).delete()
        db.query(GameInvite).delete()
        db.query(Friendship).delete()
        db.query(User).filter(User.is_bot == False).delete()  # noqa: E712
        db.commit()
    finally:
        db.close()
```

- [ ] **Step 1.5.6: Run test, confirm it passes**

```bash
rm backend/test.db; .venv/bin/python -m pytest app/tests/test_bot_user_seed.py -v
```

Expected: PASS.

- [ ] **Step 1.5.7: Commit**

```bash
git add backend/app/services/bot_users.py backend/app/db/init_db.py backend/app/tests/conftest.py backend/app/tests/test_bot_user_seed.py
git commit -m "feat(quickmatch): seed bot user pool + preserve in tests"
```

---

### Task 1.6: Filter bots from friend search & presence

**Files:**
- Modify: `backend/app/api/friends.py`
- Modify: `backend/app/sockets/events.py` (presence broadcast section)
- Test: `backend/app/tests/test_bot_filter.py`

- [ ] **Step 1.6.1: Write the failing test**

Create `backend/app/tests/test_bot_filter.py`:

```python
import pytest
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.models.user import User
from app.services.auth import create_access_token
from app.services.bot_users import seed_bot_users


@pytest.fixture
def authed_client(client):
    db = SessionLocal()
    try:
        seed_bot_users(db)
        u = User(email="searcher@example.com", google_id="g-searcher")
        db.add(u)
        db.commit()
        db.refresh(u)
        token = create_access_token(str(u.id))
    finally:
        db.close()
    return client, token


def test_friend_search_excludes_bots(authed_client):
    c, token = authed_client
    # Search by a bot name prefix — should return nothing.
    r = c.get("/friends/search?q=Priya", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    results = r.json()
    for u in results:
        assert "bot_" not in u.get("email", "")
```

- [ ] **Step 1.6.2: Run test, confirm it fails**

```bash
.venv/bin/python -m pytest app/tests/test_bot_filter.py -v
```

Expected: FAIL (bot Priya is returned).

- [ ] **Step 1.6.3: Add filter to friend search**

Edit `backend/app/api/friends.py`. Locate the friend search query (likely a function decorated `@router.get("/search")`). Add a `User.is_bot == False` filter to the query. Example modification (adapt to actual code structure):

```python
results = db.query(User).filter(
    User.is_bot == False,  # noqa: E712
    or_(User.email.ilike(f"%{q}%"), User.display_name.ilike(f"%{q}%")),
).limit(20).all()
```

Apply the same filter to:
- Friend suggestion list endpoint
- Any other "list users" surface in `friends.py`

- [ ] **Step 1.6.4: Filter bots from presence broadcasts**

In `backend/app/sockets/events.py`, find the `presence:connect` handler and any "broadcast online users" emit. Bots cannot connect a socket (they never call `presence:connect`), so the live presence dict already excludes them. But if any endpoint enumerates `USER_ONLINE` and joins to user rows, add `User.is_bot == False` to that join.

Grep for `USER_ONLINE` and audit each use site. Add filter where user listings are returned to clients.

- [ ] **Step 1.6.5: Run test, confirm it passes**

```bash
.venv/bin/python -m pytest app/tests/test_bot_filter.py -v
```

- [ ] **Step 1.6.6: Commit**

```bash
git add backend/app/api/friends.py backend/app/sockets/events.py backend/app/tests/test_bot_filter.py
git commit -m "feat(quickmatch): exclude bots from friend search & presence"
```

---

### 🛑 Phase 1 review checkpoint

Run the full backend suite. Confirm all prior tests still pass plus the new Phase-1 tests. Manually open a sqlite shell and verify columns + bot users exist:

```bash
cd backend && .venv/bin/python -m pytest --tb=short -q
sqlite3 backend/charade.db "SELECT email FROM users WHERE is_bot = 1 LIMIT 5;"
sqlite3 backend/charade.db "PRAGMA table_info(rooms);" | grep origin
```

If anything looks off, stop and fix before Phase 2.

---

## Phase 2 — Matchmaker service

### Task 2.1: Matchmaker skeleton + queue data structures

**Files:**
- Create: `backend/app/services/matchmaker.py`
- Test: `backend/app/tests/test_matchmaker.py`

- [ ] **Step 2.1.1: Write the failing test**

Create `backend/app/tests/test_matchmaker.py`:

```python
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
```

- [ ] **Step 2.1.2: Run test, confirm it fails**

```bash
.venv/bin/python -m pytest app/tests/test_matchmaker.py -v
```

Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 2.1.3: Create skeleton**

Create `backend/app/services/matchmaker.py`:

```python
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
```

- [ ] **Step 2.1.4: Run test, confirm it passes**

```bash
.venv/bin/python -m pytest app/tests/test_matchmaker.py -v
```

- [ ] **Step 2.1.5: Commit**

```bash
git add backend/app/services/matchmaker.py backend/app/tests/test_matchmaker.py
git commit -m "feat(quickmatch): matchmaker service skeleton"
```

---

### Task 2.2: `join_queue` — dedup, schedule fallback

**Files:**
- Modify: `backend/app/services/matchmaker.py`
- Modify: `backend/app/tests/test_matchmaker.py`

- [ ] **Step 2.2.1: Write the failing test**

Append to `backend/app/tests/test_matchmaker.py`:

```python
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
```

- [ ] **Step 2.2.2: Run tests, confirm they fail**

```bash
.venv/bin/python -m pytest app/tests/test_matchmaker.py -v
```

Expected: FAIL (`join_queue` does not exist).

- [ ] **Step 2.2.3: Implement `join_queue`**

Append to `backend/app/services/matchmaker.py`:

```python
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
```

- [ ] **Step 2.2.4: Run tests, confirm they pass**

```bash
.venv/bin/python -m pytest app/tests/test_matchmaker.py -v
```

- [ ] **Step 2.2.5: Commit**

```bash
git add backend/app/services/matchmaker.py backend/app/tests/test_matchmaker.py
git commit -m "feat(quickmatch): join_queue with dedup + fallback scheduling"
```

---

### Task 2.3: `cancel_queue`

**Files:**
- Modify: `backend/app/services/matchmaker.py`
- Modify: `backend/app/tests/test_matchmaker.py`

- [ ] **Step 2.3.1: Write the failing test**

Append:

```python
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
```

- [ ] **Step 2.3.2: Run tests, confirm they fail**

```bash
.venv/bin/python -m pytest app/tests/test_matchmaker.py -v
```

- [ ] **Step 2.3.3: Implement `cancel_queue`**

Append to `matchmaker.py`:

```python
async def cancel_queue(user_id: int) -> dict:
    """Remove user from queue if still waiting. Returns ALREADY_MATCHED if their
    entry already paired or fell back to bot."""
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
```

- [ ] **Step 2.3.4: Run tests, confirm they pass**

```bash
.venv/bin/python -m pytest app/tests/test_matchmaker.py -v
```

- [ ] **Step 2.3.5: Commit**

```bash
git add backend/app/services/matchmaker.py backend/app/tests/test_matchmaker.py
git commit -m "feat(quickmatch): cancel_queue with ALREADY_MATCHED race handling"
```

---

### Task 2.4: Bot fallback flow + `surprise` category resolution

**Files:**
- Modify: `backend/app/services/matchmaker.py`
- Modify: `backend/app/tests/test_matchmaker.py`

- [ ] **Step 2.4.1: Write the failing test**

Append:

```python
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
    assert 1 not in matchmaker.USER_IN_QUEUE


@pytest.mark.asyncio
async def test_surprise_resolves_to_a_real_category():
    resolved = matchmaker.resolve_category("surprise")
    assert resolved in matchmaker.GK_CATEGORIES
```

- [ ] **Step 2.4.2: Run tests, confirm they fail**

```bash
.venv/bin/python -m pytest app/tests/test_matchmaker.py -v
```

- [ ] **Step 2.4.3: Implement category resolution**

Append to `matchmaker.py`:

```python
import random

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
```

The fallback test already works because `join_queue` schedules the task. Verify by running the test.

- [ ] **Step 2.4.4: Run tests, confirm they pass**

```bash
.venv/bin/python -m pytest app/tests/test_matchmaker.py -v
```

- [ ] **Step 2.4.5: Commit**

```bash
git add backend/app/services/matchmaker.py backend/app/tests/test_matchmaker.py
git commit -m "feat(quickmatch): bot fallback timing + surprise category"
```

---

### Task 2.5: `register_ready` — auto-start gating

**Files:**
- Modify: `backend/app/services/matchmaker.py`
- Modify: `backend/app/tests/test_matchmaker.py`

- [ ] **Step 2.5.1: Write the failing test**

Append:

```python
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
```

- [ ] **Step 2.5.2: Run tests, confirm they fail**

```bash
.venv/bin/python -m pytest app/tests/test_matchmaker.py -v
```

- [ ] **Step 2.5.3: Implement**

Append to `matchmaker.py`:

```python
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
```

- [ ] **Step 2.5.4: Run tests, confirm they pass**

```bash
.venv/bin/python -m pytest app/tests/test_matchmaker.py -v
```

- [ ] **Step 2.5.5: Commit**

```bash
git add backend/app/services/matchmaker.py backend/app/tests/test_matchmaker.py
git commit -m "feat(quickmatch): ready-gating with 10s safety timeout"
```

---

### 🛑 Phase 2 review checkpoint

```bash
cd backend && .venv/bin/python -m pytest app/tests/test_matchmaker.py -v
```

All matchmaker tests should pass. The service has no socket bindings yet — that comes in Phase 4.

---

## Phase 3 — Trivia bot worker

### Task 3.1: Bot timing distribution

**Files:**
- Create: `backend/app/services/trivia_bot.py`
- Create: `backend/app/tests/test_trivia_bot.py`

- [ ] **Step 3.1.1: Write the failing test**

Create `backend/app/tests/test_trivia_bot.py`:

```python
"""Trivia bot worker — timing distribution, accuracy, answer injection."""

import asyncio
import random
import statistics

import pytest

from app.services import trivia_bot


def test_pick_delay_easy_distribution():
    random.seed(42)
    delays = [trivia_bot.pick_delay(difficulty=1, time_seconds=20) for _ in range(500)]
    assert all(d >= 1.5 for d in delays)
    assert all(d <= min(8.0, 20 * 0.7) for d in delays)
    # Easy should skew fast — mean near 2.5
    assert 1.8 < statistics.mean(delays) < 3.3


def test_pick_delay_hard_distribution():
    random.seed(42)
    delays = [trivia_bot.pick_delay(difficulty=3, time_seconds=10) for _ in range(500)]
    assert all(d >= 1.5 for d in delays)
    cap = min(8.0, 10 * 0.7)
    assert all(d <= cap for d in delays)
    # Hard should skew slower
    assert statistics.mean(delays) > 3.5


def test_pick_delay_floor_and_cap():
    # Force extreme samples by seeding the RNG repeatedly.
    for _ in range(100):
        d = trivia_bot.pick_delay(difficulty=2, time_seconds=15)
        assert 1.5 <= d <= min(8.0, 15 * 0.7)
```

- [ ] **Step 3.1.2: Run tests, confirm they fail**

```bash
.venv/bin/python -m pytest app/tests/test_trivia_bot.py -v
```

Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 3.1.3: Implement timing**

Create `backend/app/services/trivia_bot.py`:

```python
"""Bot worker for Quick Play trivia.

Bots are real User rows. This module:
  - decides per-question accuracy + timing
  - injects answers directly into RoomGameState.player_answers via the room lock
  - is invoked from _trivia_send_question for any room with a bot player
"""

import asyncio
import logging
import random
import time
from typing import Optional


_logger = logging.getLogger(__name__)


# Mean/sigma for the truncated-normal answer-delay distribution per difficulty.
_DELAY_PARAMS = {
    1: (2.5, 1.0),  # easy
    2: (4.0, 1.2),  # medium
    3: (5.0, 1.5),  # hard
}

# Target accuracy per difficulty for bot pre-decisions.
_ACCURACY = {1: 0.80, 2: 0.60, 3: 0.40}

DELAY_FLOOR = 1.5
DELAY_CAP_ABS = 8.0
DELAY_CAP_FRACTION = 0.7


def pick_delay(difficulty: int, time_seconds: int) -> float:
    mean, sigma = _DELAY_PARAMS.get(difficulty, _DELAY_PARAMS[2])
    cap = min(DELAY_CAP_ABS, time_seconds * DELAY_CAP_FRACTION)
    while True:
        sample = random.gauss(mean, sigma)
        if DELAY_FLOOR <= sample <= cap:
            return sample
        # Resample if out of bounds.
```

- [ ] **Step 3.1.4: Run tests, confirm they pass**

```bash
.venv/bin/python -m pytest app/tests/test_trivia_bot.py -v
```

- [ ] **Step 3.1.5: Commit**

```bash
git add backend/app/services/trivia_bot.py backend/app/tests/test_trivia_bot.py
git commit -m "feat(quickmatch): bot answer-delay distribution"
```

---

### Task 3.2: Pre-shuffled accuracy slots per match

**Files:**
- Modify: `backend/app/services/trivia_bot.py`
- Modify: `backend/app/tests/test_trivia_bot.py`

- [ ] **Step 3.2.1: Write the failing test**

Append:

```python
def test_build_accuracy_slots_matches_question_difficulties():
    random.seed(0)
    questions = [
        {"difficulty": 1}, {"difficulty": 1}, {"difficulty": 1},
        {"difficulty": 2}, {"difficulty": 2}, {"difficulty": 2}, {"difficulty": 2},
        {"difficulty": 3}, {"difficulty": 3}, {"difficulty": 3},
    ]
    slots = trivia_bot.build_accuracy_slots(questions)
    assert len(slots) == len(questions)
    for s in slots:
        assert isinstance(s, bool)


def test_build_accuracy_slots_distribution_across_many_matches():
    random.seed(0)
    questions = [{"difficulty": 1}] * 1000
    slots = trivia_bot.build_accuracy_slots(questions)
    correct = sum(slots)
    # 80% target ±5%
    assert 750 <= correct <= 850


def test_build_accuracy_slots_shuffled():
    """Slots should not be in a predictable order — the per-difficulty
    correctness gets shuffled together."""
    random.seed(7)
    questions = [{"difficulty": 1}] * 5 + [{"difficulty": 3}] * 5
    slots = trivia_bot.build_accuracy_slots(questions)
    # Probability of all-correct then all-wrong by chance is tiny; assert mix.
    # We don't assert ordering directly, only that it's not strictly grouped.
    assert slots[:5] != [True, True, True, True, True] or slots[5:] != [False, False, False, False, False]
```

- [ ] **Step 3.2.2: Run tests, confirm they fail**

```bash
.venv/bin/python -m pytest app/tests/test_trivia_bot.py -v
```

- [ ] **Step 3.2.3: Implement**

Append to `trivia_bot.py`:

```python
def build_accuracy_slots(questions: list[dict]) -> list[bool]:
    """For each question, decide whether the bot will answer correctly.

    Each slot is a Bernoulli draw at the question's difficulty-tier accuracy.
    The resulting list is then shuffled to avoid positional patterns (e.g.,
    'wrong on every 5th question')."""
    slots = []
    for q in questions:
        target = _ACCURACY.get(q.get("difficulty", 2), 0.6)
        slots.append(random.random() < target)
    random.shuffle(slots)
    return slots
```

- [ ] **Step 3.2.4: Run tests, confirm they pass**

```bash
.venv/bin/python -m pytest app/tests/test_trivia_bot.py -v
```

- [ ] **Step 3.2.5: Commit**

```bash
git add backend/app/services/trivia_bot.py backend/app/tests/test_trivia_bot.py
git commit -m "feat(quickmatch): pre-shuffled bot accuracy slots per match"
```

---

### Task 3.3: `schedule_bot_answer` — inject answer into room state

**Files:**
- Modify: `backend/app/services/trivia_bot.py`
- Modify: `backend/app/tests/test_trivia_bot.py`

- [ ] **Step 3.3.1: Write the failing test**

Append:

```python
@pytest.mark.asyncio
async def test_schedule_bot_answer_writes_to_player_answers():
    from app.services.game_state import RoomGameState
    state = RoomGameState(
        room_id=1, room_code="BOT1", rounds_total=1,
        turn_seconds=60, difficulty=1, game_type="trivia",
    )
    state.player_order = [10, 99]  # 10 = human, 99 = bot
    state.trivia_questions = [{
        "question": "Q?", "options": ["a", "b", "c", "d"],
        "correct_index": 2, "time_seconds": 20, "difficulty": 1,
    }]
    state.current_question_index = 0
    state.question_start_ts = time.time()
    state.question_time_seconds = 20

    async def on_all_answered():
        return

    await trivia_bot.schedule_bot_answer(
        state=state, room_code="BOT1", bot_player_id=99,
        will_answer_correctly=True, on_all_answered=on_all_answered,
        max_delay_override=0.05,
    )
    await asyncio.sleep(0.2)

    assert 99 in state.player_answers
    assert state.player_answers[99]["answer_index"] == 2


@pytest.mark.asyncio
async def test_schedule_bot_answer_wrong_when_inaccurate():
    from app.services.game_state import RoomGameState
    state = RoomGameState(
        room_id=1, room_code="BOT2", rounds_total=1,
        turn_seconds=60, difficulty=1, game_type="trivia",
    )
    state.player_order = [10, 99]
    state.trivia_questions = [{
        "question": "Q?", "options": ["a", "b", "c", "d"],
        "correct_index": 0, "time_seconds": 20, "difficulty": 1,
    }]
    state.current_question_index = 0
    state.question_start_ts = time.time()
    state.question_time_seconds = 20

    async def on_all_answered():
        return

    await trivia_bot.schedule_bot_answer(
        state=state, room_code="BOT2", bot_player_id=99,
        will_answer_correctly=False, on_all_answered=on_all_answered,
        max_delay_override=0.05,
    )
    await asyncio.sleep(0.2)

    assert 99 in state.player_answers
    assert state.player_answers[99]["answer_index"] != 0
```

- [ ] **Step 3.3.2: Run tests, confirm they fail**

```bash
.venv/bin/python -m pytest app/tests/test_trivia_bot.py -v
```

- [ ] **Step 3.3.3: Implement**

Append to `trivia_bot.py`:

```python
async def schedule_bot_answer(
    state,  # RoomGameState
    room_code: str,
    bot_player_id: int,
    will_answer_correctly: bool,
    on_all_answered,  # async callable() — runs after lock released if all players done
    max_delay_override: Optional[float] = None,
) -> asyncio.Task:
    """Pick a delay + answer, then submit the bot's answer to state.player_answers
    inside the room lock. Returns the spawned task (useful for tests / cancellation)."""

    q = state.trivia_questions[state.current_question_index]
    delay = max_delay_override if max_delay_override is not None else pick_delay(
        difficulty=q.get("difficulty", 2),
        time_seconds=q["time_seconds"],
    )

    if will_answer_correctly:
        answer_index = q["correct_index"]
    else:
        wrong = [i for i in range(len(q["options"])) if i != q["correct_index"]]
        answer_index = random.choice(wrong)

    async def _task():
        try:
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            return
        try:
            async with state.lock:
                # Race: question may have already resolved.
                if bot_player_id in state.player_answers:
                    return
                # Sanity: did the question advance under us?
                if (
                    state.trivia_questions
                    and state.current_question_index < len(state.trivia_questions)
                    and state.trivia_questions[state.current_question_index] is q
                ):
                    state.player_answers[bot_player_id] = {
                        "answer_index": answer_index,
                        "timestamp": time.time(),
                    }
                    all_answered = len(state.player_answers) >= len(state.player_order)
            if all_answered:
                await on_all_answered()
        except Exception:
            _logger.exception("bot answer task failed for room %s", room_code)

    return asyncio.create_task(_task())
```

- [ ] **Step 3.3.4: Run tests, confirm they pass**

```bash
.venv/bin/python -m pytest app/tests/test_trivia_bot.py -v
```

- [ ] **Step 3.3.5: Commit**

```bash
git add backend/app/services/trivia_bot.py backend/app/tests/test_trivia_bot.py
git commit -m "feat(quickmatch): bot answer injection into RoomGameState"
```

---

### Task 3.4: `restore_bot_workers_on_startup`

**Files:**
- Modify: `backend/app/services/trivia_bot.py`

- [ ] **Step 3.4.1: Implement (no test — covered by Phase 4 integration)**

Append:

```python
async def schedule_workers_for_room(state, room_code: str, sio, on_all_answered) -> None:
    """For a freshly-started or restored quickmatch room, spawn bot workers for
    each bot player and schedule their answer to the *current* question if one
    is in flight."""
    from app.db.session import SessionLocal
    from app.models.user import User

    if not state.trivia_questions:
        return
    if state.current_question_index >= len(state.trivia_questions):
        return

    with SessionLocal() as db:
        # Identify bot players in the room.
        from app.models.room_player import RoomPlayer
        rows = db.query(RoomPlayer, User).join(User, RoomPlayer.user_id == User.id) \
            .filter(RoomPlayer.room_id == state.room_id, User.is_bot == True).all()  # noqa: E712

    # Lazily build accuracy slots if absent (after restart we won't have them).
    if not hasattr(state, "_bot_accuracy_slots"):
        state._bot_accuracy_slots = build_accuracy_slots(state.trivia_questions)

    q_idx = state.current_question_index
    slot = state._bot_accuracy_slots[q_idx] if q_idx < len(state._bot_accuracy_slots) else False
    for rp, _user in rows:
        await schedule_bot_answer(
            state=state, room_code=room_code, bot_player_id=rp.id,
            will_answer_correctly=slot, on_all_answered=on_all_answered,
        )
```

- [ ] **Step 3.4.2: Commit**

```bash
git add backend/app/services/trivia_bot.py
git commit -m "feat(quickmatch): schedule_workers_for_room helper"
```

---

### 🛑 Phase 3 review checkpoint

```bash
cd backend && .venv/bin/python -m pytest app/tests/test_trivia_bot.py app/tests/test_matchmaker.py -v
```

Bot + matchmaker services are now self-tested. Phase 4 wires them into the socket layer.

---

## Phase 4 — Socket events + game-end refactor

### Task 4.1: Extract `_resolve_winner` and update all three `game:game_end` emit sites

**Files:**
- Modify: `backend/app/sockets/events.py`
- Test: `backend/app/tests/test_winner_resolution.py`

- [ ] **Step 4.1.1: Write the failing test**

Create `backend/app/tests/test_winner_resolution.py`:

```python
from app.services.game_state import RoomGameState
from app.sockets.events import _resolve_winner


def _make_state(**scores):
    s = RoomGameState(room_id=1, room_code="X", rounds_total=1,
                      turn_seconds=60, difficulty=1)
    s.player_order = list(scores.keys())
    s.scores = dict(scores)
    return s


def test_resolve_winner_picks_highest_score():
    state = _make_state(**{1: 100, 2: 250, 3: 50})
    assert _resolve_winner(state) == 2


def test_resolve_winner_tie_returns_none():
    state = _make_state(**{1: 100, 2: 100})
    assert _resolve_winner(state) is None


def test_resolve_winner_empty_returns_none():
    state = _make_state()
    assert _resolve_winner(state) is None
```

- [ ] **Step 4.1.2: Run tests, confirm they fail**

```bash
.venv/bin/python -m pytest app/tests/test_winner_resolution.py -v
```

Expected: FAIL (ImportError).

- [ ] **Step 4.1.3: Implement `_resolve_winner` and patch emit sites**

Edit `backend/app/sockets/events.py`. Add near the top (after imports, before any sio handler):

```python
def _resolve_winner(state) -> int | None:
    """Return the player_id with the highest score, or None on tie/empty."""
    if not state.scores:
        return None
    max_score = max(state.scores.values())
    leaders = [pid for pid, s in state.scores.items() if s == max_score]
    if len(leaders) == 1:
        return leaders[0]
    return None
```

Find every `sio.emit("game:game_end", {"scores": state.scores}, ...)` call in `events.py`. The reviewer identified three sites — `_auto_end_game`, `_advance_turn`, `_trivia_advance`. Patch each:

```python
await sio.emit("game:game_end", {
    "scores": state.scores,
    "winner_player_id": _resolve_winner(state),
}, room=room_code)
```

- [ ] **Step 4.1.4: Run tests, confirm they pass**

```bash
.venv/bin/python -m pytest app/tests/test_winner_resolution.py -v
```

- [ ] **Step 4.1.5: Run existing socket tests to confirm no regression**

```bash
.venv/bin/python -m pytest app/tests/test_socket_game.py app/tests/test_trivia_socket.py app/tests/test_trivia_scoring.py -v
```

Expected: all pass.

- [ ] **Step 4.1.6: Commit**

```bash
git add backend/app/sockets/events.py backend/app/tests/test_winner_resolution.py
git commit -m "feat(quickmatch): add winner_player_id to game:game_end at all three emit sites"
```

---

### Task 4.2: Extend `_auto_end_game` to accept `winner_player_id` override

**Files:**
- Modify: `backend/app/sockets/events.py`
- Test: `backend/app/tests/test_auto_end_game.py`

- [ ] **Step 4.2.1: Write the failing test**

Create `backend/app/tests/test_auto_end_game.py`:

```python
import pytest

from app.services.game_state import RoomGameState, ROOM_STATES
from app.sockets.events import _auto_end_game


@pytest.mark.asyncio
async def test_auto_end_game_with_explicit_winner(monkeypatch):
    state = RoomGameState(
        room_id=1, room_code="AEG1", rounds_total=1,
        turn_seconds=60, difficulty=1, game_type="trivia",
    )
    state.scores = {10: 100, 20: 0}
    ROOM_STATES["AEG1"] = state

    emitted = []
    async def fake_emit(event, payload, room=None):
        emitted.append((event, payload))

    from app.sockets import events as ev
    monkeypatch.setattr(ev.sio, "emit", fake_emit)

    await _auto_end_game(state, "AEG1", winner_player_id=10)

    # game:game_end should have been emitted with our explicit winner
    game_end = [p for e, p in emitted if e == "game:game_end"]
    assert game_end
    assert game_end[0]["winner_player_id"] == 10
```

- [ ] **Step 4.2.2: Run test, confirm it fails**

```bash
.venv/bin/python -m pytest app/tests/test_auto_end_game.py -v
```

- [ ] **Step 4.2.3: Update `_auto_end_game` signature**

In `backend/app/sockets/events.py`, modify `_auto_end_game`:

```python
async def _auto_end_game(state, room_code: str, winner_player_id: int | None = None) -> None:
    # ... existing setup code ...
    winner = winner_player_id if winner_player_id is not None else _resolve_winner(state)
    await sio.emit("game:game_end", {
        "scores": state.scores,
        "winner_player_id": winner,
    }, room=room_code)
    # ... existing cleanup code ...
```

Search for all `_auto_end_game(...)` callsites — they currently pass only `(state, room_code)`. Leave those untouched; the new arg is optional with a sensible default.

- [ ] **Step 4.2.4: Run tests, confirm they pass**

```bash
.venv/bin/python -m pytest app/tests/test_auto_end_game.py app/tests/test_winner_resolution.py -v
```

- [ ] **Step 4.2.5: Commit**

```bash
git add backend/app/sockets/events.py backend/app/tests/test_auto_end_game.py
git commit -m "feat(quickmatch): _auto_end_game accepts explicit winner_player_id"
```

---

### Task 4.3: `quickmatch:join` socket handler

**Files:**
- Modify: `backend/app/sockets/events.py`
- Test: `backend/app/tests/test_quickmatch_socket.py`

- [ ] **Step 4.3.1: Write the failing test**

Create `backend/app/tests/test_quickmatch_socket.py`:

```python
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
```

- [ ] **Step 4.3.2: Run tests, confirm they fail**

```bash
.venv/bin/python -m pytest app/tests/test_quickmatch_socket.py -v
```

- [ ] **Step 4.3.3: Implement handler**

In `backend/app/sockets/events.py`, add:

```python
from app.services import matchmaker
from app.services.bot_users import pick_random_bot
from app.services import trivia_bot


@sio.on("quickmatch:join")
async def quickmatch_join(sid, data):
    token = data.get("token")
    category_raw = data.get("category")
    if not token or not category_raw:
        await emit_error(sid, "token + category required", code="BAD_REQUEST")
        return {"ok": False, "error": "BAD_REQUEST"}

    with SessionLocal() as db:
        user = get_user_from_token(db, token)
    if not user:
        await emit_error(sid, "Auth required", code="UNAUTHORIZED")
        return {"ok": False, "error": "UNAUTHORIZED"}

    category = matchmaker.resolve_category(category_raw)

    async def on_pair(entry_a, entry_b):
        await _quickmatch_pair_humans(entry_a, entry_b, category)

    async def on_bot_fallback(entry):
        await _quickmatch_pair_bot(entry, category)

    res = await matchmaker.join_queue(
        user_id=user.id, sid=sid, category=category,
        on_pair=on_pair, on_bot_fallback=on_bot_fallback,
    )
    if res.get("status") == "searching":
        await sio.emit("quickmatch:searching",
                       {"wait_seconds": matchmaker.FALLBACK_SECONDS}, to=sid)
    return res


async def _quickmatch_pair_humans(entry_a, entry_b, category: str) -> None:
    """Create a quickmatch room with both users, emit `quickmatch:matched`,
    register a pending-start gate."""
    # See Task 4.5 for full implementation. Stub for now:
    raise NotImplementedError("filled in Task 4.5")


async def _quickmatch_pair_bot(entry, category: str) -> None:
    raise NotImplementedError("filled in Task 4.6")
```

- [ ] **Step 4.3.4: Run first test (`emits_searching`)**

```bash
.venv/bin/python -m pytest app/tests/test_quickmatch_socket.py::test_quickmatch_join_emits_searching -v
```

Expected: PASS. The pairing test will still fail until Task 4.5 — that's intentional.

- [ ] **Step 4.3.5: Commit**

```bash
git add backend/app/sockets/events.py backend/app/tests/test_quickmatch_socket.py
git commit -m "feat(quickmatch): quickmatch:join handler with searching response"
```

---

### Task 4.4: `quickmatch:cancel` handler + disconnect cleanup

**Files:**
- Modify: `backend/app/sockets/events.py`
- Modify: `backend/app/tests/test_quickmatch_socket.py`

- [ ] **Step 4.4.1: Write the failing test**

Append to `test_quickmatch_socket.py`:

```python
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
```

- [ ] **Step 4.4.2: Run tests, confirm they fail**

```bash
.venv/bin/python -m pytest app/tests/test_quickmatch_socket.py::test_quickmatch_cancel_while_searching app/tests/test_quickmatch_socket.py::test_disconnect_drops_user_from_queue -v
```

- [ ] **Step 4.4.3: Implement cancel handler**

In `events.py`:

```python
@sio.on("quickmatch:cancel")
async def quickmatch_cancel(sid, data):
    token = data.get("token")
    if not token:
        return {"ok": False, "error": "BAD_REQUEST"}
    with SessionLocal() as db:
        user = get_user_from_token(db, token)
    if not user:
        return {"ok": False, "error": "UNAUTHORIZED"}

    res = await matchmaker.cancel_queue(user.id)
    if res["ok"]:
        await sio.emit("quickmatch:cancelled", {}, to=sid)
    return res
```

- [ ] **Step 4.4.4: Extend disconnect handler**

Find the existing `disconnect` handler in `events.py`. After existing cleanup (presence, grace tasks), add:

```python
# Pull from quickmatch queue if present.
user_id = SID_TO_USER.get(sid)
if user_id and user_id in matchmaker.USER_IN_QUEUE:
    await matchmaker.cancel_queue(user_id)
```

(Confirm `SID_TO_USER` is the right map; if a different lookup is used, follow that pattern.)

- [ ] **Step 4.4.5: Run tests, confirm they pass**

```bash
.venv/bin/python -m pytest app/tests/test_quickmatch_socket.py -v
```

Note: the `test_quickmatch_join_pairs_two_users` test will still fail until Task 4.5.

- [ ] **Step 4.4.6: Commit**

```bash
git add backend/app/sockets/events.py backend/app/tests/test_quickmatch_socket.py
git commit -m "feat(quickmatch): cancel handler + disconnect drops from queue"
```

---

### Task 4.5: Pairing logic for two humans

**Files:**
- Modify: `backend/app/sockets/events.py`

- [ ] **Step 4.5.1: Implement `_quickmatch_pair_humans`**

Replace the stub `_quickmatch_pair_humans` in `events.py`:

```python
async def _quickmatch_pair_humans(entry_a, entry_b, category: str) -> None:
    """Create a quickmatch room with both users, join their sockets to the
    room, broadcast `quickmatch:matched`, and register the pending-start gate."""
    from app.services.room_ops import create_room_for_user
    from app.schemas.room import RoomCreateRequest

    with SessionLocal() as db:
        user_a = db.query(User).filter(User.id == entry_a.user_id).first()
        user_b = db.query(User).filter(User.id == entry_b.user_id).first()
        if not user_a or not user_b:
            return

        payload = RoomCreateRequest(
            rounds_total=1, difficulty=0, turn_seconds=15,
            max_players=2, game_type="trivia", trivia_category=category,
        )
        lobby = create_room_for_user(db, user_a.id, payload)
        room = db.query(Room).filter(Room.code == lobby.room.code).first()
        room.origin = "quickmatch"
        room.max_players = 2
        room.min_players = 2
        # Add user_b as a player
        from app.services.room_ops import join_room_op
        join_room_op(db, room, user_b.id, None)
        db.commit()

        # Resolve player IDs for state.player_order
        from app.models.room_player import RoomPlayer
        rp_a = db.query(RoomPlayer).filter(
            RoomPlayer.room_id == room.id, RoomPlayer.user_id == user_a.id,
        ).first()
        rp_b = db.query(RoomPlayer).filter(
            RoomPlayer.room_id == room.id, RoomPlayer.user_id == user_b.id,
        ).first()
        room_code = room.code
        room_id = room.id

    # Join both sockets to the room
    await sio.enter_room(entry_a.sid, room_code)
    await sio.enter_room(entry_b.sid, room_code)
    SID_TO_PLAYER[entry_a.sid] = rp_a.id
    SID_TO_PLAYER[entry_b.sid] = rp_b.id
    PLAYER_TO_SID[rp_a.id] = entry_a.sid
    PLAYER_TO_SID[rp_b.id] = entry_b.sid
    PLAYER_TO_ROOM[rp_a.id] = room_code
    PLAYER_TO_ROOM[rp_b.id] = room_code

    # Broadcast match found
    await sio.emit("quickmatch:matched",
                   {"room_code": room_code, "opponent_name": user_b.display_name or user_b.email},
                   to=entry_a.sid)
    await sio.emit("quickmatch:matched",
                   {"room_code": room_code, "opponent_name": user_a.display_name or user_a.email},
                   to=entry_b.sid)

    # Register pending-start gate
    async def _start_game(rc):
        await _quickmatch_start_game(rc)

    matchmaker.register_pending_start(
        room_code, expected_user_ids={user_a.id, user_b.id}, on_start=_start_game,
    )


async def _quickmatch_start_game(room_code: str) -> None:
    """Kick off the trivia game for a quickmatch room. Equivalent to the
    trivia branch of `game:start` but bypassing the host check."""
    with SessionLocal() as db:
        room = db.query(Room).filter(Room.code == room_code).first()
        if not room:
            return
        from app.models.room_player import RoomPlayer
        players = db.query(RoomPlayer).filter(
            RoomPlayer.room_id == room.id,
        ).order_by(RoomPlayer.join_order).all()
        if len(players) < 2:
            return

        state = RoomGameState(
            room_id=room.id, room_code=room.code,
            rounds_total=room.rounds_total, turn_seconds=room.turn_seconds,
            difficulty=room.difficulty, game_type="trivia",
            trivia_category=room.trivia_category,
            origin="quickmatch",
        )
        state.player_order = [p.id for p in players]
        state.scores = {p.id: 0 for p in players}
        ROOM_STATES[room.code] = state

        room.status = "active"
        for p in players:
            p.in_game = True
        db.commit()
        _save_state(db, state)

    # Reuse existing trivia round starter
    await _trivia_start_round(state, room_code)
```

- [ ] **Step 4.5.2: Run the pairing test, confirm it passes**

```bash
.venv/bin/python -m pytest app/tests/test_quickmatch_socket.py::test_quickmatch_join_pairs_two_users -v
```

- [ ] **Step 4.5.3: Commit**

```bash
git add backend/app/sockets/events.py
git commit -m "feat(quickmatch): pair two humans into a quickmatch trivia room"
```

---

### Task 4.6: Bot pairing + worker scheduling on question send

**Files:**
- Modify: `backend/app/sockets/events.py`
- Modify: `backend/app/tests/test_quickmatch_socket.py`

- [ ] **Step 4.6.1: Write the failing test**

Append:

```python
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
```

- [ ] **Step 4.6.2: Run test, confirm it fails**

```bash
.venv/bin/python -m pytest app/tests/test_quickmatch_socket.py::test_bot_fallback_creates_match -v
```

- [ ] **Step 4.6.3: Implement `_quickmatch_pair_bot`**

Replace the stub:

```python
async def _quickmatch_pair_bot(entry, category: str) -> None:
    from app.services.room_ops import create_room_for_user, join_room_op
    from app.schemas.room import RoomCreateRequest

    with SessionLocal() as db:
        user = db.query(User).filter(User.id == entry.user_id).first()
        if not user:
            return
        bot = pick_random_bot(db)

        payload = RoomCreateRequest(
            rounds_total=1, difficulty=0, turn_seconds=15,
            max_players=2, game_type="trivia", trivia_category=category,
        )
        lobby = create_room_for_user(db, user.id, payload)
        room = db.query(Room).filter(Room.code == lobby.room.code).first()
        room.origin = "quickmatch"
        room.max_players = 2
        room.min_players = 2
        join_room_op(db, room, bot.id, None)
        db.commit()

        from app.models.room_player import RoomPlayer
        rp_user = db.query(RoomPlayer).filter(
            RoomPlayer.room_id == room.id, RoomPlayer.user_id == user.id,
        ).first()
        room_code = room.code

    await sio.enter_room(entry.sid, room_code)
    SID_TO_PLAYER[entry.sid] = rp_user.id
    PLAYER_TO_SID[rp_user.id] = entry.sid
    PLAYER_TO_ROOM[rp_user.id] = room_code

    await sio.emit("quickmatch:matched",
                   {"room_code": room_code, "opponent_name": bot.display_name or "Player"},
                   to=entry.sid)

    async def _start_game(rc):
        await _quickmatch_start_game(rc)

    matchmaker.register_pending_start(
        room_code, expected_user_ids={user.id}, on_start=_start_game,
    )
```

- [ ] **Step 4.6.4: Hook bot worker into `_trivia_send_question`**

Locate `_trivia_send_question` in `events.py`. At the end of the function (after the question is emitted and the timer task spawned), add:

```python
# Spawn bot answers for any bot players in this room.
from app.services import trivia_bot as _trivia_bot

if not hasattr(state, "_bot_accuracy_slots"):
    state._bot_accuracy_slots = _trivia_bot.build_accuracy_slots(state.trivia_questions)

with SessionLocal() as db:
    bot_player_rows = db.query(RoomPlayer, User).join(
        User, RoomPlayer.user_id == User.id,
    ).filter(
        RoomPlayer.room_id == state.room_id,
        User.is_bot == True,  # noqa: E712
    ).all()

q_idx = state.current_question_index
slot = state._bot_accuracy_slots[q_idx] if q_idx < len(state._bot_accuracy_slots) else False

async def _on_all_answered():
    async with state.lock:
        # Bot triggered all-answered — cancel the question timer and resolve.
        if state.task and not state.task.done():
            state.task.cancel()
        await _trivia_resolve_question(state, room_code)

for rp, _user in bot_player_rows:
    await _trivia_bot.schedule_bot_answer(
        state=state, room_code=room_code, bot_player_id=rp.id,
        will_answer_correctly=slot, on_all_answered=_on_all_answered,
    )
```

- [ ] **Step 4.6.5: Run tests, confirm they pass**

```bash
.venv/bin/python -m pytest app/tests/test_quickmatch_socket.py -v
```

- [ ] **Step 4.6.6: Commit**

```bash
git add backend/app/sockets/events.py backend/app/tests/test_quickmatch_socket.py
git commit -m "feat(quickmatch): bot-fallback pairing + worker schedules on question send"
```

---

### Task 4.7: `quickmatch:ready` handler

**Files:**
- Modify: `backend/app/sockets/events.py`
- Modify: `backend/app/tests/test_quickmatch_socket.py`

- [ ] **Step 4.7.1: Write the failing test**

Append:

```python
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
```

- [ ] **Step 4.7.2: Run test, confirm it fails**

```bash
.venv/bin/python -m pytest app/tests/test_quickmatch_socket.py::test_quickmatch_ready_starts_game_when_both_ready -v
```

- [ ] **Step 4.7.3: Implement handler**

In `events.py`:

```python
@sio.on("quickmatch:ready")
async def quickmatch_ready(sid, data):
    token = data.get("token")
    room_code = data.get("room_code")
    if not token or not room_code:
        return {"ok": False, "error": "BAD_REQUEST"}
    with SessionLocal() as db:
        user = get_user_from_token(db, token)
    if not user:
        return {"ok": False, "error": "UNAUTHORIZED"}

    await matchmaker.register_ready(room_code, user.id)
    return {"ok": True}
```

- [ ] **Step 4.7.4: Run test, confirm it passes**

```bash
.venv/bin/python -m pytest app/tests/test_quickmatch_socket.py::test_quickmatch_ready_starts_game_when_both_ready -v
```

- [ ] **Step 4.7.5: Commit**

```bash
git add backend/app/sockets/events.py backend/app/tests/test_quickmatch_socket.py
git commit -m "feat(quickmatch): quickmatch:ready handler with auto-start gate"
```

---

### Task 4.8: `game:leave` quickmatch trivia branch (forfeit win)

**Files:**
- Modify: `backend/app/sockets/events.py`
- Modify: `backend/app/tests/test_quickmatch_socket.py`

- [ ] **Step 4.8.1: Write the failing test**

Append:

```python
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
```

- [ ] **Step 4.8.2: Run test, confirm it fails**

```bash
.venv/bin/python -m pytest app/tests/test_quickmatch_socket.py::test_quickmatch_leave_forfeits_to_survivor -v
```

- [ ] **Step 4.8.3: Implement branch**

Locate the trivia branch of `game:leave` in `events.py` (around line 1104). Before the existing "let solo player keep playing" path, add:

```python
# Quickmatch forfeit-win: leaving with one survivor ends the match.
if state.origin == "quickmatch" and len(state.player_order) == 1:
    survivor = state.player_order[0]
    state.scores[survivor] = state.scores.get(survivor, 0)
    await _auto_end_game(state, room_code, winner_player_id=survivor)
    return
```

- [ ] **Step 4.8.4: Run test, confirm it passes**

```bash
.venv/bin/python -m pytest app/tests/test_quickmatch_socket.py -v
```

- [ ] **Step 4.8.5: Commit**

```bash
git add backend/app/sockets/events.py backend/app/tests/test_quickmatch_socket.py
git commit -m "feat(quickmatch): trivia leave triggers forfeit win for survivor"
```

---

### Task 4.9: Hide quickmatch rooms from existing surfaces

**Files:**
- Modify: `backend/app/api/rooms.py` (and friends.py / events.py as needed)
- Modify: `backend/app/tests/test_quickmatch_socket.py`

- [ ] **Step 4.9.1: Write the failing test**

Append:

```python
@pytest.mark.asyncio
async def test_quickmatch_room_hidden_from_active_listing(monkeypatch, client):
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

    # The matched room exists, but the active-rooms endpoint should not list it.
    r = client.get("/rooms/active", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    for room in r.json():
        assert room.get("origin", "friends") != "quickmatch"
```

- [ ] **Step 4.9.2: Run test, confirm it fails**

```bash
.venv/bin/python -m pytest app/tests/test_quickmatch_socket.py::test_quickmatch_room_hidden_from_active_listing -v
```

- [ ] **Step 4.9.3: Filter at every surface**

Find the `/rooms/active` endpoint in `backend/app/api/rooms.py`. Add `Room.origin == "friends"` to the query filter. Apply the same filter to:

- Friend invite room dropdown queries (`friends.py` or `game_invites.py`)
- Join-by-code endpoint — return `404` for quickmatch rooms when someone tries to join via the human code

For join-by-code, in `room:join` handler in `events.py`:

```python
if room.origin == "quickmatch":
    await emit_error(sid, "Room not found", code="NOT_FOUND")
    return {"ok": False, "error": "NOT_FOUND"}
```

- [ ] **Step 4.9.4: Run tests, confirm pass**

```bash
.venv/bin/python -m pytest app/tests/test_quickmatch_socket.py -v
```

- [ ] **Step 4.9.5: Commit**

```bash
git add backend/app/api/rooms.py backend/app/api/friends.py backend/app/sockets/events.py backend/app/tests/test_quickmatch_socket.py
git commit -m "feat(quickmatch): hide quickmatch rooms from friend-flow surfaces"
```

---

### Task 4.10: Tag quickmatch GameHistory + filter from default queries

**Files:**
- Modify: `backend/app/sockets/events.py` (in `_save_game_history`)
- Modify: `backend/app/api/game_history.py` (or wherever history is read)
- Test: `backend/app/tests/test_quickmatch_history.py`

- [ ] **Step 4.10.1: Write the failing test**

Create `backend/app/tests/test_quickmatch_history.py`:

```python
import pytest

from app.db.session import SessionLocal
from app.models.game_history import GameHistory
from app.models.room import Room
from app.models.user import User
from app.services.bot_users import seed_bot_users
from app.sockets.events import _save_game_history
from app.services.game_state import RoomGameState


def test_save_game_history_copies_room_origin():
    db = SessionLocal()
    try:
        seed_bot_users(db)
        host = User(email="hist@example.com", google_id="g-hist")
        db.add(host)
        db.commit()
        db.refresh(host)
        r = Room(code="QMH001", host_user_id=host.id, status="active",
                 rounds_total=1, difficulty=1, turn_seconds=60,
                 max_players=2, min_players=2, origin="quickmatch",
                 game_type="trivia")
        db.add(r)
        db.commit()
        db.refresh(r)

        state = RoomGameState(room_id=r.id, room_code=r.code,
                              rounds_total=1, turn_seconds=60, difficulty=1,
                              origin="quickmatch", game_type="trivia")
        state.scores = {1: 100}
        state.player_order = [1]
        _save_game_history(db, state)
        db.commit()

        rows = db.query(GameHistory).all()
        assert rows
        for row in rows:
            assert row.origin == "quickmatch"
    finally:
        db.close()
```

- [ ] **Step 4.10.2: Run test, confirm it fails**

```bash
.venv/bin/python -m pytest app/tests/test_quickmatch_history.py -v
```

- [ ] **Step 4.10.3: Update `_save_game_history`**

Find `_save_game_history` in `events.py`. When constructing each `GameHistory` row, set `origin=state.origin` (defaulting to `"friends"`).

- [ ] **Step 4.10.4: Filter user-facing history by default**

Locate user-facing history queries (likely `backend/app/api/game_history.py`). Add `GameHistory.origin == "friends"` as a default filter, with an explicit opt-in query param if quickmatch history needs to be retrievable.

- [ ] **Step 4.10.5: Run tests, confirm pass**

```bash
.venv/bin/python -m pytest app/tests/test_quickmatch_history.py -v
```

- [ ] **Step 4.10.6: Commit**

```bash
git add backend/app/sockets/events.py backend/app/api/game_history.py backend/app/tests/test_quickmatch_history.py
git commit -m "feat(quickmatch): tag GameHistory.origin + hide from default history"
```

---

### 🛑 Phase 4 review checkpoint

Run the full backend suite:

```bash
cd backend && .venv/bin/python -m pytest --tb=short -q
```

Expected: all new tests pass; existing tests unaffected (except the 3 pre-existing live-server failures). The backend is feature-complete for v1 — Phase 5+ is frontend + E2E.

---

## Phase 5 — Test-only auth endpoint

### Task 5.1: `/auth/test_token` endpoint

**Files:**
- Modify: `backend/app/api/auth.py`
- Test: `backend/app/tests/test_auth_test_token.py`

- [ ] **Step 5.1.1: Write the failing test**

Create `backend/app/tests/test_auth_test_token.py`:

```python
import os

import pytest


def test_test_token_endpoint_disabled_in_prod(client, monkeypatch):
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    r = client.post("/auth/test_token", json={"display_name": "Tester"})
    assert r.status_code == 404


def test_test_token_endpoint_creates_user_in_test_env(client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "test")
    r = client.post("/auth/test_token", json={"display_name": "TestPlayer"})
    assert r.status_code == 200
    body = r.json()
    assert "token" in body
    assert body["user"]["display_name"] == "TestPlayer"
```

- [ ] **Step 5.1.2: Run test, confirm it fails**

```bash
.venv/bin/python -m pytest app/tests/test_auth_test_token.py -v
```

- [ ] **Step 5.1.3: Add the endpoint**

In `backend/app/api/auth.py`, append:

```python
import os
import uuid


@router.post("/test_token")
async def test_token(payload: dict, db: Session = Depends(get_db)):
    if os.getenv("ENVIRONMENT") != "test":
        raise HTTPException(status_code=404, detail="Not Found")
    display_name = payload.get("display_name") or f"Tester-{uuid.uuid4().hex[:6]}"
    email = f"test_{uuid.uuid4().hex[:8]}@e2e.local"
    user = User(email=email, google_id=f"test-{uuid.uuid4().hex[:8]}",
                display_name=display_name, is_bot=False)
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(str(user.id))
    return {"token": token, "user": {"id": user.id, "display_name": display_name, "email": email}}
```

- [ ] **Step 5.1.4: Run tests, confirm pass**

```bash
.venv/bin/python -m pytest app/tests/test_auth_test_token.py -v
```

- [ ] **Step 5.1.5: Commit**

```bash
git add backend/app/api/auth.py backend/app/tests/test_auth_test_token.py
git commit -m "feat(quickmatch): test-only /auth/test_token endpoint for E2E"
```

---

## Phase 6 — Frontend matchmaking screens

### Task 6.1: AppContext socket listeners + state slice

**Files:**
- Modify: `frontend/src/state/AppContext.jsx`

- [ ] **Step 6.1.1: Add quickmatch state + socket listeners**

Edit `frontend/src/state/AppContext.jsx`. Add to the state hooks:

```jsx
const [quickmatch, setQuickmatch] = useState({
  status: 'idle',  // 'idle' | 'searching' | 'matched' | 'cancelled'
  category: null,
  opponentName: null,
  roomCode: null,
  waitSeconds: 15,
})
```

In the `useEffect` that wires socket listeners, add:

```jsx
const onSearching = (p) => setQuickmatch(q => ({ ...q, status: 'searching', waitSeconds: p.wait_seconds }))
const onMatched = (p) => setQuickmatch(q => ({ ...q, status: 'matched', opponentName: p.opponent_name, roomCode: p.room_code }))
const onCancelled = () => setQuickmatch(q => ({ ...q, status: 'cancelled' }))

socket.off('quickmatch:searching').on('quickmatch:searching', onSearching)
socket.off('quickmatch:matched').on('quickmatch:matched', onMatched)
socket.off('quickmatch:cancelled').on('quickmatch:cancelled', onCancelled)
```

Expose via context value:

```jsx
quickmatch, setQuickmatch,
quickmatchJoin: (category) => socket.emit('quickmatch:join', { token: auth.token, category }),
quickmatchCancel: () => socket.emit('quickmatch:cancel', { token: auth.token }),
quickmatchReady: (roomCode) => socket.emit('quickmatch:ready', { token: auth.token, room_code: roomCode }),
```

- [ ] **Step 6.1.2: Commit**

```bash
git add frontend/src/state/AppContext.jsx
git commit -m "feat(quickmatch): add quickmatch state + socket handlers to AppContext"
```

---

### Task 6.2: `QuickMatchCategoryPicker.jsx`

**Files:**
- Create: `frontend/src/ui/screens/QuickMatchCategoryPicker.jsx`
- Create: `frontend/src/ui/screens/__tests__/QuickMatchCategoryPicker.test.jsx`

- [ ] **Step 6.2.1: Write the failing test**

Create the test:

```jsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import QuickMatchCategoryPicker from '../QuickMatchCategoryPicker.jsx'

describe('QuickMatchCategoryPicker', () => {
  it('renders 14 tiles (13 categories + Surprise Me)', () => {
    const { container } = render(<QuickMatchCategoryPicker onStart={vi.fn()} onBack={vi.fn()} />)
    const tiles = container.querySelectorAll('button[data-category]')
    expect(tiles.length).toBe(14)
  })

  it('Surprise Me passes "surprise" when selected and started', () => {
    const onStart = vi.fn()
    render(<QuickMatchCategoryPicker onStart={onStart} onBack={vi.fn()} />)
    fireEvent.click(screen.getByText(/Surprise me/i))
    fireEvent.click(screen.getByText(/Start Searching/i))
    expect(onStart).toHaveBeenCalledWith('surprise')
  })

  it('disables Start Searching after first tap', () => {
    const onStart = vi.fn()
    render(<QuickMatchCategoryPicker onStart={onStart} onBack={vi.fn()} />)
    fireEvent.click(screen.getByText('Science'))
    const btn = screen.getByText(/Start Searching/i)
    fireEvent.click(btn)
    fireEvent.click(btn)
    expect(onStart).toHaveBeenCalledTimes(1)
  })
})
```

- [ ] **Step 6.2.2: Run test, confirm it fails**

```bash
cd frontend && npx vitest run src/ui/screens/__tests__/QuickMatchCategoryPicker.test.jsx
```

- [ ] **Step 6.2.3: Implement the screen**

Create `frontend/src/ui/screens/QuickMatchCategoryPicker.jsx`:

```jsx
import { useState } from 'react'
import TriviaCategorySelector from '../components/TriviaCategorySelector.jsx'

export default function QuickMatchCategoryPicker({ onStart, onBack }) {
  const [selected, setSelected] = useState('surprise')
  const [pending, setPending] = useState(false)

  function handleStart() {
    if (pending) return
    setPending(true)
    onStart(selected)
  }

  return (
    <div className="min-h-screen flex flex-col bg-bg">
      <div className="px-4 py-3 flex items-center gap-2 safe-area-top border-b border-black/5">
        <button className="touch-target text-slate/60" onClick={onBack}>←</button>
        <h1 className="font-display text-lg">Pick a topic</h1>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 pb-32">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <button
            data-category="surprise"
            className={`rounded-xl border-2 px-3 py-3 text-center transition-all ${
              selected === 'surprise'
                ? 'border-accent bg-accent/10 ring-1 ring-accent shadow-sm'
                : 'border-black/5 bg-white/60 hover:border-accent/30'
            }`}
            onClick={() => setSelected('surprise')}
          >
            <div className="text-2xl mb-1">🎲</div>
            <div className={`text-xs font-semibold ${selected === 'surprise' ? 'text-accent' : 'text-ink'}`}>Surprise me</div>
          </button>
          {/* Render the existing category tiles via a wrapper that adds data-category */}
        </div>
        <div className="mt-2">
          <TriviaCategorySelector value={selected === 'surprise' ? null : selected} onChange={setSelected} />
        </div>
      </div>

      <div className="fixed bottom-0 left-0 right-0 px-4 py-3 safe-area-bottom bg-bg/95 backdrop-blur border-t border-black/5">
        <button
          className="btn-primary w-full touch-target"
          onClick={handleStart}
          disabled={pending}
        >
          Start Searching →
        </button>
      </div>
    </div>
  )
}
```

Note: the test asserts 14 `[data-category]` tiles. To make the existing `TriviaCategorySelector` tiles match this query, either:

(a) Modify `TriviaCategorySelector` to add `data-category={cat.value}` to each `<button>` (preferred, one-line change).
(b) Restructure the test to count any button that maps to a category (less robust).

Go with (a). Edit `TriviaCategorySelector.jsx`:

```jsx
<button
  key={cat.value}
  data-category={cat.value}
  ...
```

The existing `TriviaCategorySelector.test.jsx` will still pass — it counts `button` selectors without filtering on `data-category`.

- [ ] **Step 6.2.4: Run tests, confirm pass**

```bash
npx vitest run src/ui/screens/__tests__/QuickMatchCategoryPicker.test.jsx src/ui/components/__tests__/TriviaCategorySelector.test.jsx
```

- [ ] **Step 6.2.5: Commit**

```bash
git add frontend/src/ui/screens/QuickMatchCategoryPicker.jsx frontend/src/ui/screens/__tests__/QuickMatchCategoryPicker.test.jsx frontend/src/ui/components/TriviaCategorySelector.jsx
git commit -m "feat(quickmatch): category picker with Surprise Me + double-tap dedup"
```

---

### Task 6.3: `QuickMatchSearch.jsx`

**Files:**
- Create: `frontend/src/ui/screens/QuickMatchSearch.jsx`
- Create: `frontend/src/ui/screens/__tests__/QuickMatchSearch.test.jsx`

- [ ] **Step 6.3.1: Write the failing test**

```jsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import QuickMatchSearch from '../QuickMatchSearch.jsx'

describe('QuickMatchSearch', () => {
  it('renders countdown starting at 15 seconds', () => {
    render(<QuickMatchSearch waitSeconds={15} category="science" onCancel={vi.fn()} />)
    expect(screen.getByText('15')).toBeTruthy()
  })

  it('shows the category label', () => {
    render(<QuickMatchSearch waitSeconds={15} category="science" onCancel={vi.fn()} />)
    expect(screen.getByText(/science/i)).toBeTruthy()
  })

  it('calls onCancel when cancel button is clicked', () => {
    const onCancel = vi.fn()
    render(<QuickMatchSearch waitSeconds={15} category="science" onCancel={onCancel} />)
    fireEvent.click(screen.getByLabelText(/cancel/i))
    expect(onCancel).toHaveBeenCalledOnce()
  })

  it('countdown decrements over time', () => {
    vi.useFakeTimers()
    render(<QuickMatchSearch waitSeconds={15} category="science" onCancel={vi.fn()} />)
    act(() => { vi.advanceTimersByTime(2000) })
    expect(screen.getByText('13')).toBeTruthy()
    vi.useRealTimers()
  })
})
```

- [ ] **Step 6.3.2: Run test, confirm it fails**

```bash
npx vitest run src/ui/screens/__tests__/QuickMatchSearch.test.jsx
```

- [ ] **Step 6.3.3: Implement**

Create `frontend/src/ui/screens/QuickMatchSearch.jsx`:

```jsx
import { useEffect, useState } from 'react'

export default function QuickMatchSearch({ waitSeconds = 15, category, onCancel }) {
  const [remaining, setRemaining] = useState(waitSeconds)

  useEffect(() => {
    if (remaining <= 0) return
    const id = setTimeout(() => setRemaining(r => r - 1), 1000)
    return () => clearTimeout(id)
  }, [remaining])

  return (
    <div className="min-h-screen flex flex-col bg-bg safe-area-top">
      <div className="flex justify-end px-4 py-3">
        <button className="touch-target text-slate/60" onClick={onCancel} aria-label="Cancel">✕</button>
      </div>
      <div className="flex-1 flex flex-col items-center justify-center text-center px-6">
        <div className="relative w-48 h-48 flex items-center justify-center mb-6">
          <div className="absolute inset-0 rounded-full bg-accent/10 animate-ping" />
          <div className="absolute inset-4 rounded-full bg-accent/15" />
          <span className="relative z-10 text-5xl font-display text-accent">{remaining}</span>
        </div>
        <p className="text-xl font-display text-ink">Finding a player...</p>
        <p className="text-sm text-slate/60 mt-1 capitalize">{category} category</p>
      </div>
    </div>
  )
}
```

- [ ] **Step 6.3.4: Run tests, confirm pass**

```bash
npx vitest run src/ui/screens/__tests__/QuickMatchSearch.test.jsx
```

- [ ] **Step 6.3.5: Commit**

```bash
git add frontend/src/ui/screens/QuickMatchSearch.jsx frontend/src/ui/screens/__tests__/QuickMatchSearch.test.jsx
git commit -m "feat(quickmatch): search screen with radar pulse + countdown"
```

---

### Task 6.4: `MatchFoundSplash.jsx`

**Files:**
- Create: `frontend/src/ui/screens/MatchFoundSplash.jsx`
- Create: `frontend/src/ui/screens/__tests__/MatchFoundSplash.test.jsx`

- [ ] **Step 6.4.1: Write the failing test**

```jsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import MatchFoundSplash from '../MatchFoundSplash.jsx'

describe('MatchFoundSplash', () => {
  it('renders opponent name', () => {
    render(<MatchFoundSplash opponentName="Priya" category="science" onDone={vi.fn()} />)
    expect(screen.getByText('Priya')).toBeTruthy()
  })

  it('calls onDone after 1800ms', () => {
    vi.useFakeTimers()
    const onDone = vi.fn()
    render(<MatchFoundSplash opponentName="Priya" category="science" onDone={onDone} />)
    act(() => { vi.advanceTimersByTime(1800) })
    expect(onDone).toHaveBeenCalledOnce()
    vi.useRealTimers()
  })
})
```

- [ ] **Step 6.4.2: Run test, confirm it fails**

```bash
npx vitest run src/ui/screens/__tests__/MatchFoundSplash.test.jsx
```

- [ ] **Step 6.4.3: Implement**

Create `frontend/src/ui/screens/MatchFoundSplash.jsx`:

```jsx
import { useEffect } from 'react'
import PlayerAvatar from '../components/PlayerAvatar.jsx'
import { playSound } from '../../lib/sounds.js'

export default function MatchFoundSplash({ opponentName, category, onDone }) {
  useEffect(() => {
    playSound('match-found')
    try {
      import('@capacitor/haptics').then(({ Haptics, ImpactStyle }) => {
        Haptics.impact({ style: ImpactStyle.Medium }).catch(() => {})
      })
    } catch { /* not on capacitor */ }
    const id = setTimeout(onDone, 1800)
    return () => clearTimeout(id)
  }, [onDone])

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-bg safe-area-top">
      <div className="mb-6 animate-pop">
        <PlayerAvatar name={opponentName} size="lg" />
      </div>
      <p className="text-2xl font-display text-ink">{opponentName}</p>
      <p className="mt-2 text-sm text-accent font-semibold tracking-widest">MATCH FOUND</p>
      <p className="mt-1 text-xs text-slate/60 capitalize">{category}</p>
      <p className="mt-6 text-slate/50">Get ready...</p>
    </div>
  )
}
```

- [ ] **Step 6.4.4: Add `match-found` sound to `sounds.js`**

Edit `frontend/src/lib/sounds.js`. In the `SOUNDS` object, add:

```javascript
'match-found': (ctx) => {
  // Soft two-tone ding at reduced gain
  const osc = ctx.createOscillator()
  const gain = ctx.createGain()
  osc.frequency.setValueAtTime(660, ctx.currentTime)
  osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.15)
  gain.gain.setValueAtTime(0.08, ctx.currentTime)  // soft
  gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3)
  osc.connect(gain).connect(ctx.destination)
  osc.start()
  osc.stop(ctx.currentTime + 0.35)
}
```

- [ ] **Step 6.4.5: Run tests, confirm pass**

```bash
npx vitest run src/ui/screens/__tests__/MatchFoundSplash.test.jsx
```

- [ ] **Step 6.4.6: Commit**

```bash
git add frontend/src/ui/screens/MatchFoundSplash.jsx frontend/src/ui/screens/__tests__/MatchFoundSplash.test.jsx frontend/src/lib/sounds.js
git commit -m "feat(quickmatch): match-found splash + soft notification sound"
```

---

### Task 6.5: Add `safe-area-top` CSS utility

**Files:**
- Modify: `frontend/src/styles.css`

- [ ] **Step 6.5.1: Add the class**

Edit `frontend/src/styles.css`. Add near the existing `.safe-area-bottom` rule:

```css
.safe-area-top {
  padding-top: env(safe-area-inset-top);
}
```

- [ ] **Step 6.5.2: Commit**

```bash
git add frontend/src/styles.css
git commit -m "feat(quickmatch): add safe-area-top CSS utility"
```

---

### 🛑 Phase 6 review checkpoint

```bash
cd frontend && npx vitest run
```

All new + existing component tests should pass. Screens render but are not yet wired into navigation — Phase 7 handles that.

---

## Phase 7 — GameSetup redesign + GameEnd extension

### Task 7.1: Quick Play hero on `GameSetup.jsx` for trivia + signed-in

**Files:**
- Modify: `frontend/src/ui/screens/GameSetup.jsx`
- Create: `frontend/src/ui/screens/__tests__/GameSetup.test.jsx` (or extend existing)

- [ ] **Step 7.1.1: Locate current rendering structure**

Open `frontend/src/ui/screens/GameSetup.jsx`. Find the conditional that branches on `gameType`. Identify where Create/Join tabs are rendered.

- [ ] **Step 7.1.2: Write the failing test**

Edit/extend `frontend/src/ui/screens/__tests__/GameSetup.test.jsx`:

```jsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import GameSetup from '../GameSetup.jsx'

const AppContext = await import('../../../state/AppContext.jsx')

function withAuth(authUser, gameType = 'trivia') {
  return render(
    <MemoryRouter initialEntries={[`/play/${gameType}`]}>
      <AppContext.AppProvider initialState={{ auth: { user: authUser, token: authUser ? 'tk' : null } }}>
        <GameSetup />
      </AppContext.AppProvider>
    </MemoryRouter>
  )
}

describe('GameSetup — Quick Play hero', () => {
  it('shows Quick Play hero for signed-in trivia', () => {
    withAuth({ id: 1, display_name: 'Alice' }, 'trivia')
    expect(screen.getByText(/Quick Play/i)).toBeTruthy()
  })

  it('hides Quick Play hero for guest trivia', () => {
    withAuth(null, 'trivia')
    expect(screen.queryByText(/Quick Play/i)).toBeNull()
  })

  it('hides Quick Play hero for charades regardless of auth', () => {
    withAuth({ id: 1, display_name: 'Alice' }, 'charades')
    expect(screen.queryByText(/Quick Play/i)).toBeNull()
  })
})
```

Note: this test depends on how `AppContext` is structured. If it doesn't currently support `initialState`, either add that prop for testability, or mock the context with a `vi.mock` of the module. Pick whichever is least invasive.

- [ ] **Step 7.1.3: Run test, confirm it fails**

```bash
npx vitest run src/ui/screens/__tests__/GameSetup.test.jsx
```

- [ ] **Step 7.1.4: Implement the hero**

In `GameSetup.jsx`, near the top of the trivia branch render, conditionally show the hero:

```jsx
import { useNavigate, useParams } from 'react-router-dom'
import { useAppContext } from '../../state/AppContext.jsx'

// ... inside the component ...
const { auth } = useAppContext()
const { gameType } = useParams()
const navigate = useNavigate()
const showQuickPlay = gameType === 'trivia' && auth?.user

// Render before the existing Create/Join tabs:
{showQuickPlay && (
  <button
    className="w-full mb-4 rounded-2xl bg-gradient-to-br from-accent to-accent/80 text-white p-6 shadow-lg active:scale-[0.98] transition"
    onClick={() => navigate('/quickmatch')}
  >
    <div className="text-2xl">⚡</div>
    <h2 className="font-display text-2xl mt-1">Quick Play</h2>
    <p className="text-sm opacity-90 mt-1">Match with a live player</p>
    <div className="mt-3 text-sm font-semibold">Play Now →</div>
  </button>
)}
{showQuickPlay && (
  <div className="my-3 flex items-center gap-2 text-xs text-slate/40">
    <div className="flex-1 h-px bg-black/10" /> or <div className="flex-1 h-px bg-black/10" />
  </div>
)}
```

- [ ] **Step 7.1.5: Run tests, confirm pass**

```bash
npx vitest run src/ui/screens/__tests__/GameSetup.test.jsx
```

- [ ] **Step 7.1.6: Commit**

```bash
git add frontend/src/ui/screens/GameSetup.jsx frontend/src/ui/screens/__tests__/GameSetup.test.jsx
git commit -m "feat(quickmatch): Quick Play hero on GameSetup for signed-in trivia"
```

---

### Task 7.2: Quickmatch flow routes + navigation

**Files:**
- Modify: `frontend/src/ui/App.jsx`

- [ ] **Step 7.2.1: Add routes**

Edit `frontend/src/ui/App.jsx`. Inside the `<Routes>` block, add:

```jsx
<Route path="/quickmatch" element={<QuickMatchFlowPage />} />
```

Create a wrapper page `frontend/src/ui/pages/QuickMatchFlowPage.jsx`:

```jsx
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import QuickMatchCategoryPicker from '../screens/QuickMatchCategoryPicker.jsx'
import QuickMatchSearch from '../screens/QuickMatchSearch.jsx'
import MatchFoundSplash from '../screens/MatchFoundSplash.jsx'
import { useAppContext } from '../../state/AppContext.jsx'

export default function QuickMatchFlowPage() {
  const navigate = useNavigate()
  const { quickmatch, quickmatchJoin, quickmatchCancel, quickmatchReady } = useAppContext()
  const [category, setCategory] = useState(null)

  function start(cat) {
    setCategory(cat)
    quickmatchJoin(cat)
  }

  function cancel() {
    quickmatchCancel()
    navigate('/play/trivia')
  }

  useEffect(() => {
    if (quickmatch.status === 'matched') {
      quickmatchReady(quickmatch.roomCode)
    }
  }, [quickmatch.status, quickmatch.roomCode])

  if (quickmatch.status === 'matched') {
    return (
      <MatchFoundSplash
        opponentName={quickmatch.opponentName}
        category={category}
        onDone={() => navigate('/trivia')}
      />
    )
  }
  if (quickmatch.status === 'searching') {
    return (
      <QuickMatchSearch
        waitSeconds={quickmatch.waitSeconds}
        category={category}
        onCancel={cancel}
      />
    )
  }
  return (
    <QuickMatchCategoryPicker
      onStart={start}
      onBack={() => navigate('/play/trivia')}
    />
  )
}
```

- [ ] **Step 7.2.2: Verify build + run vitest**

```bash
npm run build && npx vitest run
```

- [ ] **Step 7.2.3: Commit**

```bash
git add frontend/src/ui/App.jsx frontend/src/ui/pages/QuickMatchFlowPage.jsx
git commit -m "feat(quickmatch): route + page wrapper for matchmaking flow"
```

---

### Task 7.3: Extend `GameEnd.jsx` with quickmatch buttons + win headline

**Files:**
- Modify: `frontend/src/ui/screens/GameEnd.jsx`
- Create: `frontend/src/ui/screens/__tests__/GameEnd.test.jsx`

- [ ] **Step 7.3.1: Write the failing test**

```jsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import GameEnd from '../GameEnd.jsx'

describe('GameEnd — quickmatch additions', () => {
  it('shows "You Win!" when self is winner_player_id', () => {
    render(
      <GameEnd
        scores={{ 1: 1450, 2: 1120 }}
        playerNames={{ 1: 'You', 2: 'Priya' }}
        selfPlayerId={1}
        winnerPlayerId={1}
        origin="quickmatch"
        onHome={vi.fn()}
        onRematch={vi.fn()}
        onNewOpponent={vi.fn()}
      />
    )
    expect(screen.getByText(/You Win/i)).toBeTruthy()
  })

  it('shows Rematch + New Opponent for quickmatch games', () => {
    render(
      <GameEnd
        scores={{ 1: 100, 2: 200 }}
        playerNames={{ 1: 'You', 2: 'Priya' }}
        selfPlayerId={1}
        winnerPlayerId={2}
        origin="quickmatch"
        onHome={vi.fn()}
        onRematch={vi.fn()}
        onNewOpponent={vi.fn()}
      />
    )
    expect(screen.getByText(/Rematch/i)).toBeTruthy()
    expect(screen.getByText(/New Opponent/i)).toBeTruthy()
  })

  it('hides Rematch + New Opponent for friends games', () => {
    render(
      <GameEnd
        scores={{ 1: 100, 2: 200 }}
        playerNames={{ 1: 'You', 2: 'Friend' }}
        selfPlayerId={1}
        origin="friends"
        onHome={vi.fn()}
      />
    )
    expect(screen.queryByText(/Rematch/i)).toBeNull()
    expect(screen.queryByText(/New Opponent/i)).toBeNull()
  })
})
```

- [ ] **Step 7.3.2: Run test, confirm it fails**

```bash
npx vitest run src/ui/screens/__tests__/GameEnd.test.jsx
```

- [ ] **Step 7.3.3: Implement**

Edit `GameEnd.jsx` to accept `winnerPlayerId`, `origin`, `onRematch`, `onNewOpponent` props. At the top of the screen, render:

```jsx
{origin === 'quickmatch' && winnerPlayerId != null && (
  <h2 className="font-display text-3xl">
    {String(winnerPlayerId) === String(selfPlayerId) ? '🏆 You Win!' : 'You Lost'}
  </h2>
)}
```

Below the scoreboard, render the quickmatch button stack:

```jsx
{origin === 'quickmatch' && (
  <div className="mt-6 space-y-2">
    <button className="btn-primary w-full touch-target" onClick={onRematch}>🔁 Rematch</button>
    <button className="btn-secondary w-full touch-target" onClick={onNewOpponent}>🎲 New Opponent</button>
    <button className="btn-ghost w-full touch-target" onClick={onHome}>🏠 Home</button>
  </div>
)}
{origin !== 'quickmatch' && (
  <button className="btn-primary w-full touch-target" onClick={onHome}>🏠 Home</button>
)}
```

Wire these in the parent (`RoundEndPage.jsx` or wherever `GameEnd` is rendered) to consume `winner_player_id` from the `game:game_end` socket payload + `origin` from the room state.

- [ ] **Step 7.3.4: Run tests, confirm pass**

```bash
npx vitest run src/ui/screens/__tests__/GameEnd.test.jsx
```

- [ ] **Step 7.3.5: Commit**

```bash
git add frontend/src/ui/screens/GameEnd.jsx frontend/src/ui/screens/__tests__/GameEnd.test.jsx
git commit -m "feat(quickmatch): GameEnd shows winner headline + Rematch/NewOpp buttons"
```

---

### 🛑 Phase 7 review checkpoint

```bash
cd frontend && npx vitest run && npm run build
cd backend && .venv/bin/python -m pytest --tb=short -q
```

All tests pass. Manual smoke: start both servers, sign in as two test users (`/auth/test_token`), tap Quick Play in both, verify a game starts. Tap Quick Play once and wait 15s for bot fallback.

---

## Phase 8 — Mobile polish

### Task 8.1: Android back button + app-state handling

**Files:**
- Modify: `frontend/src/ui/App.jsx` (or wherever `CapApp.addListener` already lives)
- Modify: `frontend/src/ui/pages/QuickMatchFlowPage.jsx`

- [ ] **Step 8.1.1: Hook the Android back button per-flow-state**

In `QuickMatchFlowPage.jsx`, add:

```jsx
useEffect(() => {
  let handler
  try {
    import('@capacitor/app').then(({ App: CapApp }) => {
      CapApp.addListener('backButton', () => {
        if (quickmatch.status === 'searching') cancel()
        else navigate('/play/trivia')
      }).then(h => { handler = h })
    })
  } catch { /* non-capacitor */ }
  return () => { try { handler?.remove?.() } catch {} }
}, [quickmatch.status])
```

- [ ] **Step 8.1.2: Cancel queue on app background >10s**

Add another effect in the same component:

```jsx
useEffect(() => {
  if (quickmatch.status !== 'searching') return
  let backgroundedAt = null
  let handle = null
  import('@capacitor/app').then(({ App: CapApp }) => {
    CapApp.addListener('appStateChange', ({ isActive }) => {
      if (!isActive) backgroundedAt = Date.now()
      else if (backgroundedAt && Date.now() - backgroundedAt > 10000) {
        backgroundedAt = null
        cancel()
      }
    }).then(h => { handle = h })
  })
  return () => { try { handle?.remove?.() } catch {} }
}, [quickmatch.status])
```

- [ ] **Step 8.1.3: Manual test on Android device or emulator**

Build the Capacitor APK with prod env vars and verify back button + backgrounding behavior on a real device. There's no automated test for this — it's a manual verification step in the test plan from the spec.

- [ ] **Step 8.1.4: Commit**

```bash
git add frontend/src/ui/pages/QuickMatchFlowPage.jsx
git commit -m "feat(quickmatch): Android back button + app-state cancellation"
```

---

## Phase 9 — Playwright E2E

### Task 9.1: `quickmatch-trivia.spec.js` + `loginAsTestUser` helper

**Files:**
- Create: `frontend/e2e/helpers/auth.js`
- Create: `frontend/e2e/quickmatch-trivia.spec.js`

- [ ] **Step 9.1.1: Add the helper**

Create `frontend/e2e/helpers/auth.js`:

```javascript
export async function loginAsTestUser(page, displayName) {
  const api = process.env.PLAYWRIGHT_API_BASE || 'http://localhost:8005'
  const res = await page.request.post(`${api}/auth/test_token`, {
    data: { display_name: displayName },
  })
  const { token, user } = await res.json()
  await page.addInitScript(([t, u]) => {
    localStorage.setItem('charade_auth_token', t)
    localStorage.setItem('charade_auth_user', JSON.stringify(u))
  }, [token, user])
}
```

Verify the localStorage keys match what `AppContext` reads — adjust the keys if needed.

- [ ] **Step 9.1.2: Write the spec**

Create `frontend/e2e/quickmatch-trivia.spec.js`:

```javascript
import { test, expect } from '@playwright/test'
import { loginAsTestUser } from './helpers/auth.js'

test('two signed-in users matchmake and play a quickmatch game', async ({ browser }) => {
  const ctxA = await browser.newContext()
  const ctxB = await browser.newContext()
  const pageA = await ctxA.newPage()
  const pageB = await ctxB.newPage()

  await loginAsTestUser(pageA, 'PlayerA')
  await loginAsTestUser(pageB, 'PlayerB')

  await pageA.goto('/play/trivia')
  await pageB.goto('/play/trivia')

  await pageA.getByText(/Play Now/i).click()
  await pageB.getByText(/Play Now/i).click()

  // Both pick Science and start
  await pageA.getByText('Science').click()
  await pageA.getByText(/Start Searching/i).click()
  await pageB.getByText('Science').click()
  await pageB.getByText(/Start Searching/i).click()

  // Splash should appear within a few seconds
  await expect(pageA.getByText(/MATCH FOUND/i)).toBeVisible({ timeout: 5000 })
  await expect(pageB.getByText(/MATCH FOUND/i)).toBeVisible({ timeout: 5000 })

  // Game starts; first question shows
  await expect(pageA.getByText(/Question 1 of/i)).toBeVisible({ timeout: 10000 })

  // Click any answer on both
  await pageA.locator('button').filter({ hasText: /^(?!.*Leave).*$/ }).first().click()
  await pageB.locator('button').first().click()

  // Eventually game ends
  await expect(pageA.getByText(/You (Win|Lost)/i)).toBeVisible({ timeout: 180000 })
})

test('single user falls back to bot after 15s', async ({ page }) => {
  await loginAsTestUser(page, 'LonelyPlayer')
  await page.goto('/play/trivia')
  await page.getByText(/Play Now/i).click()
  await page.getByText('Science').click()
  await page.getByText(/Start Searching/i).click()

  // Bot fallback fires ~15s in
  await expect(page.getByText(/MATCH FOUND/i)).toBeVisible({ timeout: 20000 })
  await expect(page.getByText(/Question 1 of/i)).toBeVisible({ timeout: 10000 })
})
```

- [ ] **Step 9.1.3: Run the E2E suite**

Start both servers with `ENVIRONMENT=test` set on the backend:

```bash
cd backend && ENVIRONMENT=test .venv/bin/uvicorn app.main:fastapi_app --port 8005 &
cd frontend && VITE_API_BASE=http://localhost:8005 VITE_SOCKET_URL=http://localhost:8005 npm run dev &
```

Then:

```bash
cd frontend && npx playwright test e2e/quickmatch-trivia.spec.js --project "Mobile Chrome"
```

Expected: both tests pass.

- [ ] **Step 9.1.4: Commit**

```bash
git add frontend/e2e/helpers/auth.js frontend/e2e/quickmatch-trivia.spec.js
git commit -m "feat(quickmatch): Playwright E2E for matchmaking + bot fallback"
```

---

### 🛑 Phase 9 review checkpoint — final ship gate

Run everything:

```bash
cd backend && .venv/bin/python -m pytest --tb=short -q
cd frontend && npx vitest run && npm run build
cd frontend && npx playwright test --project "Mobile Chrome"
```

All green ⇒ ship-ready. Test on a real Android device via Capacitor build to validate haptics, back-button behavior, and app-state handling per the spec's manual checklist.

---

## Out of scope for this plan (per spec)

- Rematch UI flow with same-bot pinning is wired (Phase 7.3 buttons) but the `quickmatch:rematch_request` / `accept` events plus the pending-state UI are deferred to a follow-up plan. Tracked as v1.1.
- FCM push for backgrounded matches.
- Analytics, ELO, streaks, queue visibility.
- Charades / scribble matchmaking.

---

## Self-review notes

Plan covers every section of the spec. Each task is TDD with red→green→commit. Files and code blocks are concrete. Two areas accept some implementation discretion (`init_db.py` migration helper location, `_save_game_history` exact patch point) because the actual function structure is best inspected at execution time — the task instructions tell the engineer what to look for and what to change.
