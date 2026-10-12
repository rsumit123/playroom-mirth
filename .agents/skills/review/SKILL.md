---
name: review
description: Review code changes for edge cases, regressions, and gotchas specific to this codebase. Traces affected paths, checks known pitfalls, and flags issues before they ship.
argument-hint: [commit-range or "staged" or "latest"]
user-invocable: true
---

# Code Review — Edge Case & Regression Hunter

Review target: `$ARGUMENTS` (default: latest commit). Accepts "staged", "latest", a commit hash, or a range like "abc123..def456".

## Step 1: Gather the Diff

```bash
# Based on argument:
# "staged"  → git diff --cached
# "latest"  → git show HEAD
# "abc123"  → git show abc123
# "abc..def" → git diff abc..def
# default   → git show HEAD
```

Read the full diff. Identify every file and function changed.

## Step 2: Classify Changes

For each changed file, identify:
- **Backend socket handler?** → Check Step 3A
- **Backend REST endpoint?** → Check Step 3B
- **Frontend component/screen?** → Check Step 3C
- **Frontend state (AppContext)?** → Check Step 3D
- **Game state (game_state.py)?** → Check Step 3E

## Step 3: Trace Affected Code Paths

### 3A: Socket Event Handler Changes
For any modified `@sio.on("event:name")` handler:

1. **Who emits this event?** Search frontend for `socket.emit('event:name'`
2. **Who listens for responses?** Search frontend for `socket.on('event:name'`
3. **Does it modify game state?** Check if it touches `ROOM_STATES`, `state.player_order`, `state.describer_index`, `state.strokes`, `state.guessed_players`
4. **Auth check present?** Verify the handler checks `SID_TO_PLAYER` and validates the player should be allowed to do this action
5. **Race condition?** Does it use `async with state.lock`? Should it?
6. **Reconnection impact?** Check if `room:register` handles the new/changed state correctly
7. **Turn transition impact?** Does `_advance_turn` / `_emit_next_turn` / `start_turn` need updating?

### 3B: REST Endpoint Changes
1. **Auth required?** Check token/guest_token validation
2. **Does it modify DB state that socket handlers also read?** (e.g., RoomPlayer.in_game, RoomPlayer.connected)
3. **Race with socket events?** REST call completing while a socket event fires simultaneously

### 3C: Frontend Component/Screen Changes
1. **Socket listener registered?** Check for `socket.off()` before `socket.on()` (duplication pitfall)
2. **All game types affected?** If touching Game.jsx, check ScribbleGame.jsx and TriviaGame.jsx too
3. **Mobile viewport handling?** Does it use `env(safe-area-inset-*)` where needed?
4. **Capacitor vs web?** Does it use `Capacitor.isNativePlatform()` for platform-specific behavior?
5. **Rendering optimization?** Check for `useRef` trackers (like `lastDrawnRef`) that might not handle all state transitions (increase, decrease, same-count-different-content)

### 3D: AppContext State Changes
1. **All consumers updated?** Search for every component that destructures the changed value from `useApp()`
2. **Socket listener cleanup?** Verify `socket.off('event')` before `socket.on('event')`
3. **State shape change?** If adding a new field, check that existing `setGame((g) => ({...g, ...}))` calls don't clobber it
4. **Reconnection state restore?** Does `game:turn_start` handler preserve or clear this value appropriately on reconnect vs new turn?

### 3E: Game State (game_state.py) Changes
1. **Serialization?** If adding a field, does `serialize_state` / `deserialize_state` handle it? (or is it intentionally in-memory only like `strokes`)
2. **Turn reset?** Does `start_turn()` clear/reset this field?
3. **Player removal?** Does `game:leave` handler clean up this field?
4. **Memory leak?** Does the field grow unbounded during a game? When is it cleared?

## Step 4: Check Known Pitfalls

Cross-reference every change against these project-specific gotchas:

- [ ] **Socket listener duplication**: Every `socket.on()` preceded by `socket.off()`?
- [ ] **selfPlayerId broadcast**: Not setting selfPlayerId from lobby_update broadcasts?
- [ ] **Scribble stroke sync**: Draw/undo/clear all update backend `state.strokes` AND relay to room?
- [ ] **Eraser flag**: Scribble strokes include `eraser` field in relay?
- [ ] **CanvasViewer rendering**: All state transitions handled? (more strokes, fewer strokes, same count different content via replayGen, zero strokes)
- [ ] **Same-turn detection**: `game:turn_start` uses `describer_id + turn_start_ts` to distinguish reconnect from new turn?
- [ ] **Grace period**: Disconnected players in grace period not skipped in describer rotation?
- [ ] **Auto-end**: Games auto-end when <2 players remain (charades/scribble)? Trivia can continue solo?
- [ ] **Android back button**: Still handled in App.jsx?
- [ ] **Status bar overlap**: Fixed-position elements use `max(env(safe-area-inset-top), ...)` on Android?
- [ ] **CORS origins**: If touching backend CORS, all three origins present? (`capacitor://localhost`, `http://localhost`, `https://localhost`)
- [ ] **Cross-platform canvas**: Aspect ratio locked to 4:3? Line widths normalized as ratios, not pixels?

## Step 5: Edge Case Scenarios

For each change, mentally walk through these scenarios:

1. **2-player game**: Does it work with minimum players?
2. **Mid-game disconnect + reconnect**: Does the state restore correctly?
3. **Android screen dim/wake**: Socket disconnects and reconnects — is state preserved?
4. **Player leaves mid-turn**: Does the turn advance correctly? Does the game end if needed?
5. **Rapid user actions**: Button spam, rapid undo, multiple guesses — any race conditions?
6. **Cross-device**: Tablet drawer + mobile guesser — rendering consistent?
7. **Turn boundary**: What happens if this action occurs right as a turn ends?
8. **Empty state**: What if the list/array is empty when this runs?

## Step 6: Verify Tests

1. **Does a test exist for the changed code path?**
2. **Does a test exist for the edge cases identified above?**
3. **Run the relevant tests:**
   ```bash
   cd /Users/rsumit123/work/charade-chat/backend && .venv/bin/python -m pytest --tb=short -q
   cd /Users/rsumit123/work/charade-chat/frontend && npx vitest run
   ```

## Step 7: Report

```
Code Review: [brief description]
================================

Changes reviewed:
- [file]: [what changed]

Affected code paths:
- [list of callers/listeners/consumers]

Pitfall checklist: [X/Y passed]

Edge cases checked:
- [scenario]: [OK / ISSUE: description]

Issues found:
- [CRITICAL/MEDIUM/LOW]: [description + suggested fix]

Missing test coverage:
- [gap description]

Verdict: [SHIP IT / FIX FIRST: list issues]
```
