# Quick Play — Trivia Matchmaking & Bot Fallback

Design doc for adding 1v1 live-player matchmaking with bot fallback to the trivia game mode.

## Goals

- Let signed-in users find a live opponent to play trivia with, without needing to be friends.
- When no live opponent is found within 15 seconds, transparently fall back to a bot opponent that is disguised as a real player.
- Ship trivia-only. Mobile-first UX (Android via Capacitor). Existing flows for charades, scribble, and guest users stay unchanged.

## Non-goals

- Charades / scribble matchmaking (the bot story is much harder there).
- Guest matchmaking.
- ELO / ranking / leaderboards / streaks / abuse reporting.
- Push notifications for backgrounded match-found.
- Queue-size visibility to users.

These are explicitly out of scope for v1. The design should not preclude them, but it should not pay implementation cost for them either.

## Scope

- 1v1 only. No 2v2 or free-for-all.
- Signed-in users only. Guests see the existing trivia setup screen unchanged.
- Category-only pre-match config: the user picks a category (or "Surprise me"). Rounds, difficulty, and per-question timer are fixed defaults.
- Bot fallback after 15 seconds of no live match, with no manual "play with bot now" escape hatch.

## Architecture

```
                  ┌─────────────────────────────────────┐
                  │   Frontend (React / Capacitor)      │
                  │                                     │
                  │  GameSetup.jsx (redesigned)       │
                  │   ├─ Quick Play (primary CTA)       │
                  │   └─ Create / Join (secondary)      │
                  │                                     │
                  │  QuickMatchCategoryPicker.jsx (new) │
                  │  QuickMatchSearch.jsx (new)         │
                  │  MatchFoundSplash.jsx (new)         │
                  │  TriviaGame.jsx (reused, unchanged) │
                  │  GameEnd.jsx (+Rematch +NewOpp btns)│
                  └────────────────┬────────────────────┘
                                   │  socket.io
                  ┌────────────────▼────────────────────┐
                  │   Backend (FastAPI + python-socketio)
                  │                                     │
                  │  events.py                          │
                  │   ├─ quickmatch:join                │
                  │   ├─ quickmatch:cancel              │
                  │   ├─ quickmatch:rematch_request     │
                  │   ├─ quickmatch:rematch_accept      │
                  │   ├─ quickmatch:matched (emit)      │
                  │   └─ trivia:* / game:* (reused)     │
                  │                                     │
                  │  services/matchmaker.py (new)       │
                  │   ├─ QUEUES[category] = [entries]   │
                  │   ├─ join / cancel / pair / fallback│
                  │   └─ register_ready (room start gate)
                  │                                     │
                  │  services/trivia_bot.py (new)       │
                  │   ├─ schedule_answer(state, room)   │
                  │   └─ restore_workers_on_restart()   │
                  │                                     │
                  │  Reused: room_ops, trivia service,  │
                  │  game_state, scoring, persistence   │
                  └─────────────────────────────────────┘
```

Three new backend pieces (`matchmaker.py`, `trivia_bot.py`, and additions to `events.py`); four new frontend screens; one redesign of `GameSetup.jsx`; one extension of `GameEnd.jsx`. Everything else is reuse.

## Data model

All changes are additive and backward-compatible. Defaults keep existing rows valid.

### `User` model

Add one column:

```python
is_bot: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
```

Pre-seed ~30 bot users at startup in `init_db.py`. Each has a realistic Indian first name (Priya, Arjun, Ananya, Rohan, Kavya, Aditya, etc.), `email="bot_<name>@quickmatch.local"`, `google_id="bot-<name>"`, `is_bot=True`. The seeding is idempotent — it only inserts names that are not already present.

Bot users are filtered out of:

- Friend search results
- Friend suggestions
- Online presence broadcasts
- Game invite recipient lists
- Any "list users" surface

### `Room` model

Add one column:

```python
origin: Mapped[str] = mapped_column(String(20), default="friends", nullable=False)
# "friends" | "quickmatch"
```

Quickmatch rooms are filtered out of:

- `/rooms/active` listings
- Friend invite room dropdowns
- Join-by-code endpoints (a quickmatch room code is not shareable)

### `GameHistory` model

Add one column:

```python
origin: Mapped[str] = mapped_column(String(20), default="friends", nullable=False)
# "friends" | "quickmatch"
```

The `_save_game_history` writer copies this from the room. Quickmatch history rows are excluded from the default `/rooms/<code>/scoreboard` and per-user history queries so that "losing to Priya the bot" doesn't pollute the user's record. A future history UI can render quickmatch games as a separate section if desired.

### `RoomPlayer` model

No changes. Bots are real `User` rows, so display name resolution and lobby state work as-is.

### `RoomGameState` in-memory dataclass

Add one field (matches `Room.origin`):

```python
origin: str = "friends"
```

The field is populated when state is created (in `game:start` / matchmaker pairing) and is serialized/deserialized alongside the existing trivia fields in `services/game_state.py`. Functions that need to branch on quickmatch behavior (notably `_auto_end_game` and the `game:leave` handler) read `state.origin` instead of doing a fresh `Room` DB lookup.

### Matchmaker queue — in-memory only

```python
@dataclass
class QueueEntry:
    user_id: int
    sid: str
    joined_at: float
    category: str
    fallback_task: asyncio.Task | None = None
    matched: bool = False  # set when paired; fallback timer no-ops if True

QUEUES: dict[str, list[QueueEntry]] = defaultdict(list)
USER_IN_QUEUE: dict[int, QueueEntry] = {}  # dedup
QUEUE_LOCKS: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
```

No DB row for queue state. If the backend restarts, in-flight queues are dropped — clients see a socket disconnect and re-queue manually.

### Bot user pool

A `BOT_NAMES` constant in `services/trivia_bot.py` holds the names used at seed time. A helper `pick_random_bot(db)` returns a random `User` row with `is_bot=True`. The same bot user can be a player in multiple rooms concurrently (each room has its own `RoomPlayer` row), so we never run out.

### Migration

The existing `db/init_db.py` already runs idempotent `ALTER TABLE ADD COLUMN` migrations on startup (called from `main.py` `on_startup`). We add the three new column migrations to the same function, following the existing pattern (inspect columns via SQLAlchemy reflection, add if missing):

1. `ALTER TABLE users ADD COLUMN is_bot BOOLEAN NOT NULL DEFAULT 0`
2. `ALTER TABLE rooms ADD COLUMN origin VARCHAR(20) NOT NULL DEFAULT 'friends'`
3. `ALTER TABLE game_history ADD COLUMN origin VARCHAR(20) NOT NULL DEFAULT 'friends'`
4. Idempotent bot-user seeding (insert each `BOT_NAMES` entry only if a user with the matching `google_id` doesn't already exist).

Adding the migration inline to `init_db()` matches the project's established convention. The `on_startup` hook already invokes `init_db()` — no additional wiring needed.

### Test-fixture interaction

`backend/app/tests/conftest.py` has an autouse `clear_users` fixture that deletes every row from `users` before each test. Bot users seeded at startup get wiped, which would break any quickmatch test that depends on a bot pool. Two-part fix:

1. The autouse fixture is updated to preserve `is_bot=True` rows (`db.query(User).filter(User.is_bot == False).delete()`), or
2. A dedicated `bot_users` fixture re-seeds the pool inside each quickmatch test module.

Option 1 is simpler and recommended; bot users are entirely managed by the seeder and have no test-pollution risk.

## Socket protocol

### New events

| Event | Direction | Payload | Purpose |
| --- | --- | --- | --- |
| `quickmatch:join` | C→S | `{ token, category }` | Enter the matchmaking queue. `category` is one of the 13 trivia categories defined in `TriviaCategorySelector` or `"surprise"`. |
| `quickmatch:cancel` | C→S | `{ token }` | Leave the queue. |
| `quickmatch:searching` | S→C | `{ wait_seconds: 15 }` | Ack of join; client starts countdown UI. |
| `quickmatch:matched` | S→room | `{ room_code, opponent_name }` | Match found (live or bot — indistinguishable to client). |
| `quickmatch:cancelled` | S→C | `{}` | Ack of successful cancel. |
| `quickmatch:rematch_request` | C→S | `{ token, room_code }` | Request a rematch with the same opponent. |
| `quickmatch:rematch_accept` | C→S | `{ token, room_code }` | Accept an incoming rematch request. |
| `quickmatch:rematch_pending` | S→C | `{ requester_name, expires_in: 10 }` | Notify opponent that a rematch was requested. |
| `quickmatch:ready` | C→S | `{ token, room_code }` | Client signals it has navigated past the splash and is ready to receive the first question. |

### Reused events (unchanged)

`room:register`, `trivia:question`, `trivia:answer`, `trivia:answer_update`, `trivia:question_result`, `game:round_end`, `game:game_end`, `game:leave`.

### `game:game_end` payload addition

Add a `winner_player_id` field to the existing `game:game_end` emission. For non-quickmatch rooms the field is `null`, so existing clients are unaffected. The frontend uses this to render a "You Win!" / "You Lost" headline on the GameEnd screen for quickmatch games specifically.

There are **three independent `game:game_end` emit sites** in `backend/app/sockets/events.py` and all three must be updated to populate the field (resolved from `state.scores` — the player with the highest score; ties resolve to `null`):

- `_auto_end_game` (currently around `events.py:138`) — fires when grace period expires for a disconnected player.
- `_advance_turn` (currently around `events.py:290`) — charades/scribble game-over path.
- `_trivia_advance` (currently around `events.py:819`) — trivia normal game-over after the last question of the last round.

A small shared helper `_resolve_winner(state) -> int | None` keeps the three sites consistent.

### `game:leave` trivia branch addition

Today, `game:leave` for a trivia room with one remaining player does **not** end the game — the conditional at `events.py:1104–1106` only triggers `_auto_end_game` when `not state.player_order` (zero players) OR `(game_type != "trivia" AND len < 2)`. The surviving solo player just keeps playing.

For quickmatch rooms this is wrong: leaving must end the match with a forfeit win for the survivor. We add a quickmatch-specific branch immediately after the existing condition:

```python
# pseudocode
if state.origin == "quickmatch" and len(state.player_order) == 1:
    state.scores[surviving_player_id] = state.scores.get(surviving_player_id, 0)  # ensure present
    await _auto_end_game(state, room_code, winner_player_id=surviving_player_id)
    return
```

`_auto_end_game` is extended to accept an optional `winner_player_id` argument (when omitted, it falls back to `_resolve_winner(state)` for non-quickmatch flows). Existing callers pass nothing and keep working.

For non-quickmatch rooms, the existing trivia "play solo if one player leaves" behavior is preserved — only quickmatch enforces the forfeit-win rule.

## Flows

### Happy path — human vs human

```
User A                  Server                     User B
  │                       │                          │
  │── quickmatch:join ──▶ │                          │
  │     {cat="science"}   │                          │
  │                       │ enqueue A                │
  │ ◀── searching ────────│ schedule 15s fallback    │
  │     {wait_seconds:15} │                          │
  │                       │                          │── quickmatch:join ──▶
  │                       │ pair inside QUEUE_LOCK,  │
  │                       │ cancel both timers,      │
  │                       │ create_room(origin=qm,   │
  │                       │   status=active),        │
  │                       │ add A, B as RoomPlayers, │
  │                       │ insert RoomGameState     │
  │                       │   (do NOT auto-start)    │
  │                       │                          │
  │ ◀── quickmatch:matched ── (to both via sio.room) ─▶
  │     {room_code,opponent_name}                    │
  │                       │                          │
  │   navigate /trivia,                              │
  │   show MatchFoundSplash 1.8s                     │
  │                       │                          │
  │── room:register ────▶ │ ◀── room:register ───────│
  │── quickmatch:ready ─▶ │ ◀── quickmatch:ready ────│
  │                       │ both ready (or 10s pass) │
  │                       │ → _trivia_start_round    │
  │ ◀── trivia:question ── (to both) ────────────────▶
```

Auto-start is gated on `quickmatch:ready` from each expected non-bot player. A 10-second safety timeout starts the game anyway if a client doesn't register in time — protects against a stuck splash.

### Bot fallback — no pair in 15 seconds

```
User A                  Server                  trivia_bot worker
  │                       │                          │
  │── quickmatch:join ──▶ │                          │
  │ ◀── searching ────────│ schedule 15s task        │
  │                       │                          │
  │       ...15s pass...  │                          │
  │                       │ fallback task fires:     │
  │                       │  - acquire QUEUE_LOCK    │
  │                       │  - entry.matched=True    │
  │                       │  - pick_random_bot()     │
  │                       │  - create_room(qm)       │
  │                       │  - add A + Priya         │
  │                       │  - spawn bot worker ─────▶ subscribe to room
  │                       │                          │
  │ ◀── quickmatch:matched ──── {room_code,          │
  │                              opponent_name="Priya"}
  │                       │                          │
  │── room:register ────▶ │                          │
  │── quickmatch:ready ─▶ │ → _trivia_start_round    │
  │                       │  emit trivia:question ──▶ schedule_answer(q)
  │── trivia:answer ────▶ │                          │
  │                       │ ◀── (after delay)        │
  │                       │   state.player_answers[bot] = answer
  │                       │   if all answered → resolve
  │ ◀── trivia:question_result ─────────────────────▶ continues
```

For bot rooms, only the human's `quickmatch:ready` is awaited; the bot doesn't register.

### Cancel

The client emits `quickmatch:cancel`. The server acquires the queue lock, checks if the entry is still queued and not yet `matched`:

- If still queued: remove from queue, cancel fallback task, emit `quickmatch:cancelled`. Client returns to the category picker.
- If already matched: emit `{ ok: false, error: "ALREADY_MATCHED" }`. The client treats this as "stay on splash" and waits for the imminent `quickmatch:matched` — which has already been broadcast.

### Mid-game opponent leave

The existing `game:leave` event handler gets a quickmatch branch. When triggered in a quickmatch room:

- If exactly one human remains in `state.player_order` (or one human + one bot): set `winner_player_id = surviving_human.id`, emit `game:game_end` with the partial scores plus the winner field, write a quickmatch `GameHistory` row, clean up `RoomGameState` and `RoomState`.
- The same path runs via the existing reconnect grace-period auto-end: if the disconnected player doesn't return before grace expires, `_auto_end_game` is called. We patch `_auto_end_game` to consult `room.origin` and, for quickmatch, populate `winner_player_id` accordingly.

### Rematch

After a quickmatch game ends, both clients see a Rematch button on the GameEnd screen.

- **Human vs bot:** clicking Rematch reuses the same bot `user_id` and immediately creates a fresh quickmatch room with the same two `RoomPlayer`s. No accept handshake. Same opponent name persists, preserving the disguise.
- **Human vs human:** clicking Rematch emits `quickmatch:rematch_request`. The other client sees a 10-second `quickmatch:rematch_pending` prompt: "Priya wants a rematch — Accept / Decline." On accept, a new quickmatch room is created with the same two users. On decline or timeout, the requester is notified.

### Surprise me

When `category == "surprise"`, the server picks `random.choice(GK_CATEGORIES)` at queue-join time and uses that as the user's actual queue category. Two "Surprise me" users only pair if they happen to land in the same category. This keeps queues simple and doesn't add a "surprise" pseudo-queue.

## Bot behavior

### Identity

Bots are fully disguised as human:

- Realistic Indian first name picked from `BOT_NAMES`.
- Normal `PlayerAvatar` (initials circle), no "BOT" chip.
- Appears in the in-game scoreboard like any human player.
- Identity is pinned per rematch (same `user_id`).

### Answer timing

For each question delivered to a bot's room, the bot worker schedules an answer with:

- A random delay drawn from a **truncated normal distribution** keyed to difficulty:
  - Easy (difficulty 1, 20s window): mean 2.5s, σ 1.0s
  - Medium (difficulty 2, 15s window): mean 4.0s, σ 1.2s
  - Hard (difficulty 3, 10s window): mean 5.0s, σ 1.5s
- Hard floor at 1.5s (never answers instantly).
- Hard ceiling at `min(8s, time_seconds * 0.7)` (never the last possible moment).

This produces fast answers on easy questions and slower answers on hard ones — matching real human behavior.

### Answer accuracy

For each match, the bot pre-decides its correct/incorrect slots:

- Target accuracy per difficulty: easy 80%, medium 60%, hard 40%.
- For each of the 10 questions in the match, the target accuracy for that question's difficulty is sampled into a Bernoulli to decide correct/incorrect — but the resulting list of `[correct, correct, wrong, correct, ...]` is **shuffled** before being applied to the question order.
- This avoids predictable patterns like "wrong every 5th question" while keeping the overall accuracy on target.

### Answer submission

The bot worker holds no socket. It is invoked directly from `_trivia_send_question` (in-process function call, not via a socket subscription) at the moment each new question is sent to the room: `schedule_bot_answer(state, room_code, question)` spawns an `asyncio.Task` per bot in that room. When the task fires after its scheduled delay:

1. Acquire `state.lock` (same lock used by `trivia:answer`).
2. Check `state.player_answers[bot_player_id]` — if already populated (e.g. the question resolved early), no-op.
3. Set `state.player_answers[bot_player_id] = { answer_index, timestamp }`.
4. Emit `trivia:answer_update` to the room.
5. If `len(state.player_answers) >= len(state.player_order)`, cancel the timer and call `_trivia_resolve_question`.

Any exception in this path is caught and logged. The bot simply doesn't answer; the question times out at 0 points for the bot.

### Restart resilience

A new `schedule_bot_workers_on_restore()` is called after `restore_game_states()` on backend startup. It walks `ROOM_STATES.values()`, finds rooms with any bot player, and spawns a worker for each. Workers do not persist their scheduled-answer state — on restart, the bot answers based on whatever question is currently active.

## Frontend screens

All screens are mobile-first and tested against the Capacitor Android wrapper. Existing utilities apply: `safe-area-bottom` and `touch-target` (min 44px) are already defined in `src/styles.css`; `prefers-reduced-motion` is supported throughout. A new `.safe-area-top` CSS class (`padding-top: env(safe-area-inset-top)`) is added to `styles.css` for the new full-screen layouts (`QuickMatchSearch`, `MatchFoundSplash`) that override the body's top padding — today the body element gets `env(safe-area-inset-top)` applied directly, but per-element safe-area-top is not available as a utility.

### GameSetup.jsx (trivia branch only)

The existing `frontend/src/ui/screens/GameSetup.jsx` handles all three game modes with conditional rendering. We add a Quick Play branch that is rendered **only when both** `gameType === 'trivia'` **and** `auth.user` is signed in (`auth.user != null`). Existing Charades / Scribble / Trivia-as-guest paths render the current Create/Join layout unchanged.

The trivia + signed-in branch:

- **Top hero card** — Quick Play. Accent gradient, ~140px tall, subtle pulse animation on idle, large CTA "Play Now".
- **Divider** — "or" with subdued lines.
- **Secondary cards** — Create Room + Join Room as two equal-weight tiles below.

Guest users (in `AppContext`, `auth.user == null` and `auth.guestToken != null`) see the existing layout for all game modes, no Quick Play surface, no upsell.

### QuickMatchCategoryPicker.jsx (new)

Reuses the existing `TriviaCategorySelector` 2-col grid with one new tile prepended: "🎲 Surprise me" (maps to `category="surprise"`). A sticky "Start Searching" button at the bottom (`safe-area-bottom`) triggers `quickmatch:join`. The button is **disabled the moment it is tapped** and stays disabled until either `quickmatch:searching` is received or an error toast fires — prevents double-tap spam.

### QuickMatchSearch.jsx (new)

A full-screen waiting state:

- Animated radar pulse circle in the center with the seconds-remaining counter inside (15 → 0).
- "Finding a player..." headline + selected category subtitle.
- Top-right ✕ cancel button. Android hardware back button also fires `quickmatch:cancel` (intercepted via Capacitor `App.addListener('backButton', ...)`).
- **No "play with bot now" button.** User waits the full 15 seconds or cancels.
- On `prefers-reduced-motion`, the radar pulse is static; only the countdown ticks.
- If socket disconnects mid-search, show a "Reconnecting..." toast and re-emit `quickmatch:join` on reconnect (server treats duplicate as idempotent — same user, in queue, no-op).
- If app is backgrounded for more than 10 seconds (`appStateChange` from Capacitor `App` plugin), the client proactively sends `quickmatch:cancel`. On foreground return, the user lands back on the category picker.

### MatchFoundSplash.jsx (new)

A 1.8-second transition:

- Centered avatar (initials circle) with the opponent name.
- "MATCH FOUND" headline + category subtitle.
- "Get ready... 3 · 2 · 1" countdown.
- Plays a short notification-tier sound (softer than the existing media-channel sounds — see audio notes below).
- Fires Capacitor `Haptics.impact({ style: Medium })` on Android.
- Auto-advances to `TriviaGame` at 1.8s. Client emits `quickmatch:ready` as soon as the underlying socket has joined the room.

### TriviaGame.jsx (unchanged)

The existing screen renders the quickmatch game with no modifications. The opponent's name appears in the scoreboard exactly like a human friend would.

### GameEnd.jsx (extended)

For quickmatch games, the screen renders three buttons in order:

1. **🔁 Rematch** — bot opponent: instant re-match with the same bot `user_id`. Human opponent: emits `quickmatch:rematch_request`, then waits up to 10s for `quickmatch:rematch_accept`. Shows a small "Waiting for Priya..." state while pending. On decline / timeout, button restores to "Rematch" with a toast "Priya isn't up for another round."
2. **🎲 New Opponent** — re-queues for the same category (one tap, skips the category picker).
3. **🏠 Home** — existing behavior.

For non-quickmatch games (the existing friend flow), only the existing "Home" button is rendered. The Rematch and New Opponent buttons are conditional on `room.origin === "quickmatch"`.

For quickmatch games, the headline reads "You Win!" or "You Lost" based on `winner_player_id` from `game:game_end`.

## Audio and haptics

- **Match-found ding** plays at a lower volume than existing game sounds and uses a softer tone. Implementation: synthesized via the existing `sounds.js` Web Audio path with reduced gain (matches existing `playSound` pattern). The existing `charade_sounds_muted` localStorage toggle in `sounds.js` gates all game audio system-wide, so users who have muted the app stay muted. (Web Audio in a Capacitor webview does not natively honor Android ringer mode; reduced gain + the in-app mute is the v1 stance. A native audio plugin that respects ringer mode is a v2 consideration.)
- **Haptic** on match-found uses `Haptics.impact({ style: Medium })` only — does not depend on ringer mode.

## Edge cases & error handling

### Handled

| Scenario | Handling |
| --- | --- |
| User taps Quick Play with no internet | Toast "No connection." Don't navigate. |
| Socket disconnects mid-queue | Server `disconnect` handler removes from queue + cancels fallback task. Client toast + return to category picker. |
| User in queue opens app on a second device | Server rejects second `quickmatch:join` with `ALREADY_IN_QUEUE`. Client shows "You're already searching on another device." |
| User in queue gets a friend invite | Friend invite popup appears as today. If accepted, server pulls them from queue first (uses `USER_IN_QUEUE` lookup). |
| All 30 bot users currently in active matches | Same bot user can be in multiple rooms (per-room `RoomPlayer` rows are distinct). No throttling needed. |
| Bot fallback fires the same instant a real pair forms | Resolved in the queue lock. Fallback task does `if entry.matched: return` first thing. |
| Human opponent leaves mid-game | `game:leave` quickmatch branch → `game:game_end` with `winner_player_id` for the survivor + write quickmatch `GameHistory`. |
| Human opponent's socket disconnects without `game:leave` | Existing grace-period applies. If grace expires, `_auto_end_game` runs the quickmatch forfeit-win path. |
| Backend restart with active matches | `restore_game_states` resurrects state. `schedule_bot_workers_on_restore` re-spawns bot workers for rooms with bot players. |
| Bot crashes mid-game | Wrapped in try/except. Bot simply doesn't answer; question times out at 0 points for the bot. |
| User force-quits app during game | Existing reconnect + grace-period code handles this. If they don't return in grace, forfeit win to opponent. |
| Cancel race — client sends cancel after match formed | Server returns `{ ok: false, error: "ALREADY_MATCHED" }`. Client stays on the splash; `quickmatch:matched` arrives normally. |
| Client never finishes splash / never sends `ready` | Server's 10-second safety timeout starts the game anyway. The unregistered client will reconnect to the active room via `room:register` when it eventually arrives. |
| Rematch with bot | Same `user_id` reused. Name persists. New room. |
| Surprise me | Server picks `random.choice(GK_CATEGORIES)` at queue-join time. Treated as that category for pairing. |
| Bot game `GameHistory` polluting user record | `GameHistory.origin = "quickmatch"` is written for all matchmaking games. User-facing history queries filter to `origin = "friends"` by default. |
| `winner_player_id` for non-quickmatch games | Field is `null` or omitted. Existing clients ignore it. |
| Double-tap "Start Searching" | Frontend disables the button on first tap. Server-side dedup is the backstop. |
| Bot answer pattern is too predictable | Truncated-normal timing distribution per difficulty; per-match accuracy shuffled to avoid streak patterns. |
| Audio on silent device | Web Audio synthesis no-ops; haptic still fires. |

### Deferred to v2 (flagged, not built)

- FCM push when match is found but app is backgrounded.
- JWT expiry while in queue. Current JWT TTL is 30 days; a 15-second window cannot trigger expiry.
- Stale `RoomPlayer.in_game=false` rows for users who re-queue. Cosmetic, no functional issue.
- Bot user_id filtering at the `/game-history` API level. Bots cannot authenticate (no real OAuth identity); their `user_id` is not externally accessible.
- Analytics: queue join rate, match rate, bot rate, forfeit rate, rematch rate.
- ELO / ranking.
- Daily streaks (relies on `GameHistory.origin`).
- Queue size visibility ("X people searching in Science").
- Abuse reporting.
- Bot difficulty scaling per user skill history.
- "vs Bot" indicator in the user's own history view.

## Testing strategy

Heavy reuse of the existing test scaffolding. New tests are listed by file with the cases each must cover.

### Backend pytest

**`test_matchmaker.py`** — pure unit tests of the matchmaker:

- User joins empty queue → entry appended, fallback task scheduled.
- Two users join same category → matched immediately, both timers cancelled, room created with `origin="quickmatch"`.
- User joins, 15s passes → bot match created, opponent is `User.is_bot=True`.
- User cancels while queued → removed, timer cancelled, `quickmatch:cancelled` sent.
- User cancels after `entry.matched=True` → `ALREADY_MATCHED` returned.
- Disconnect while in queue → cleaned up.
- Same user joins twice → second rejected `ALREADY_IN_QUEUE`.
- Different categories don't pair.
- `category="surprise"` → server resolves to a real category at join time.

**`test_trivia_bot.py`** — bot worker behavior:

- Bot delay falls within `[1.5s, min(8s, time_seconds * 0.7)]` window.
- Easy questions: bot accuracy 80% ± 5% over 200 trials.
- Medium: 60% ± 5%.
- Hard: 40% ± 5%.
- Per-match accuracy is shuffled (no positional bias).
- Bot exception during answer is caught; question times out → 0 points.
- Multiple concurrent bot games don't cross-contaminate.
- `schedule_bot_workers_on_restore` re-spawns workers after simulated restart.

**`test_quickmatch_socket.py`** — socket events using `sio._trigger_event`:

- `quickmatch:join` → `quickmatch:searching` response.
- Two `quickmatch:join` on same category → both get `quickmatch:matched`, room exists with both players.
- `quickmatch:cancel` while queued → `quickmatch:cancelled` ack; user removed.
- `quickmatch:cancel` after match → `ALREADY_MATCHED` error; user stays in room.
- `quickmatch:ready` from both → game starts (first `trivia:question` emitted).
- One client never sends `quickmatch:ready` → 10s safety timeout fires; game starts anyway.
- Mid-game opponent `game:leave` in quickmatch → `game:game_end` includes `winner_player_id`.
- `Room.origin == "quickmatch"` filtered from `/rooms/active`.
- Rematch with bot → new room with same bot `user_id`.
- Rematch with human → handshake; on accept new room is created.

**Extend `test_scoreboard.py`** — assert quickmatch `GameHistory` rows have `origin="quickmatch"` and are excluded from default scoreboard responses.

### Frontend Vitest

**`screens/__tests__/TriviaSetup.test.jsx`** (redesign):

- Quick Play hero renders when `auth.user` is signed in.
- Quick Play hero is absent when user is a guest.
- Tapping Play Now navigates to the category picker.
- Create / Join cards are always present.

**`screens/__tests__/QuickMatchCategoryPicker.test.jsx`**:

- Renders the existing 13 category tiles + a Surprise Me tile (14 total).
- Tapping Surprise Me sends `category="surprise"` to the join emit.
- "Start Searching" button disables on first tap.

**`screens/__tests__/QuickMatchSearch.test.jsx`**:

- Countdown ticks 15 → 0.
- Cancel button fires `onCancel`.
- Receiving a `matched` prop transitions away.
- Reduced-motion: pulse animation is suppressed; countdown still ticks.

**`screens/__tests__/MatchFoundSplash.test.jsx`**:

- Renders opponent name and avatar.
- Auto-advances to next screen after 1.8s (fake timers).
- Fires the `onReady` callback when mounted.

**Extend `screens/__tests__/GameEnd.test.jsx`** (file does not exist yet; create it):

- For `origin="quickmatch"` and win: shows "You Win!" + Rematch + New Opponent + Home.
- For loss: shows "You Lost" + same buttons.
- Bot rematch click is instant (no waiting state).
- Human rematch click shows "Waiting for…" state until accept/decline/timeout.
- For `origin="friends"`: existing behavior preserved; no quickmatch buttons.

### Playwright E2E

Existing E2E specs in `frontend/e2e/` all use `loginAsGuest`. Quickmatch is signed-in only, so the existing helper doesn't apply, and there is **no existing OAuth fixture** to reuse. Two viable v1 approaches:

1. **Add a test-only auth endpoint** (recommended): `POST /auth/test_token` accepts `{ display_name }` and returns `{ token, user }`, creating a real `User` row. Gated by `ENVIRONMENT == "test"` env var (already used elsewhere in the backend). Never registered in production startup. A new `loginAsTestUser(page, name)` helper in the E2E test-utils calls this endpoint and stores the JWT in localStorage exactly like the OAuth flow does.
2. **Defer E2E to v1.1**: ship without the Playwright spec, relying on the backend socket tests (which already exercise multi-client trivia flows via `sio._trigger_event`) plus the new frontend Vitest screens. Backend socket tests will give us most of the multi-user safety net for v1; the Playwright E2E becomes a v1.1 deliverable once the test auth endpoint is in.

**Recommended for v1: approach 1.** The test endpoint is ~20 lines of code, the helper is ~15, and we get full end-to-end coverage for the riskiest new flow.

**`e2e/quickmatch-trivia.spec.js`** (new):

- Two browser contexts, both authenticated via `loginAsTestUser`. Both tap Quick Play with the same category. Both get matched. Both play a full game and see results. Verify `winner_player_id` shapes the win/loss headline correctly.
- Single-context bot fallback: one signed-in user taps Quick Play, waits >15s, verifies the game starts with a named bot opponent, plays through to the end.

### Manual device test checklist

Because the app ships on Android via Capacitor:

- Hardware back button on each new screen (cancels queue, goes back to previous screen, opens leave-confirm in game).
- App backgrounded during search → re-foreground → category picker.
- App backgrounded after `matched` but before splash completes → reconnect flow recovers and lands user in the active game.
- App backgrounded mid-game → existing reconnect grace period works.
- Match-found haptic fires on Android.
- Match-found sound respects ringer / silent mode.
- Status bar color is correct on the dark MatchFoundSplash.

## Open questions

None — all design decisions are locked. Implementation can begin once this spec is approved.
