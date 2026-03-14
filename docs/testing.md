# Testing Guide

## Quick Reference

```bash
# Backend unit/integration tests (always run before committing)
cd backend && .venv/bin/python -m pytest --tb=short -q

# Frontend build check + unit tests (always run before committing)
cd frontend && npm run build && npx vitest run

# Backend E2E tests (require running server on port 8005)
cd backend && .venv/bin/python -m uvicorn app.main:app --port 8005 &
.venv/bin/python -m pytest app/tests/test_charades_scribble_e2e.py app/tests/test_play_again_rest.py app/tests/test_scoreboard.py --tb=short -v

# Frontend Playwright E2E tests (require both backend + frontend dev servers)
# Start backend: cd backend && .venv/bin/python -m uvicorn app.main:app --port 8005 &
# Start frontend: cd frontend && npm run dev &
# Then run:
cd frontend && npx playwright test --project "Mobile Chrome"
```

## Pre-Commit Checklist

**MANDATORY before every commit:**

1. Run backend tests: `cd backend && .venv/bin/python -m pytest --tb=short -q`
2. Run frontend build: `cd frontend && npm run build`
3. Run frontend tests: `cd frontend && npx vitest run`
4. If touching socket events or game logic, also run E2E tests (start server first)

If any test fails, **do not commit**. Fix the issue first.

## Test Structure

### Backend (`backend/app/tests/`)

| File | Type | What it tests | Requires server? |
|------|------|--------------|-----------------|
| `test_auth.py` | Unit | JWT auth, Google token exchange | No |
| `test_admin_words.py` | Unit | Admin word CRUD | No |
| `test_room_creation.py` | Unit | Room creation schemas | No |
| `test_rooms.py` | Integration | REST room endpoints (create, join, settings, state) | No |
| `test_rooms_leave_active.py` | Integration | REST leave room + active rooms endpoints | No |
| `test_seed_words.py` | Unit | Word seeding, deduplication, game types | No |
| `test_socket_rooms.py` | Integration | Socket room:create, room:join, disconnect | No |
| `test_socket_game.py` | Integration | game:start, turn timer, correct guess, game end | No |
| `test_play_again.py` | Integration | Socket play-again voting flow | No |
| `test_game_leave.py` | Integration | game:leave handler (mid-game quit) | No |
| `test_grace_rotation.py` | Integration | Grace period describer rotation, reconnect | No |
| `test_charades_scribble_e2e.py` | E2E | Full charades + scribble games | **Yes** |
| `test_play_again_rest.py` | E2E | REST play-again flow end-to-end | **Yes** |
| `test_scoreboard.py` | E2E | Trivia game + scoreboard persistence | **Yes** |

### Frontend (`frontend/src/`)

| File | What it tests |
|------|--------------|
| `test/ui.test.jsx` | Smoke tests for multiple screens (GameEnd, RoundEnd, TopBar) |
| `test/animation.test.jsx` | ConfettiBurst animation component |
| `ui/components/__tests__/LeaveGameModal.test.jsx` | Leave game confirmation modal |
| `ui/components/__tests__/CanvasViewer.test.jsx` | Scribble canvas viewer |
| `ui/components/__tests__/DrawingCanvas.test.jsx` | Scribble drawing canvas |
| `ui/components/__tests__/DifficultySelector.test.jsx` | Difficulty picker |
| `ui/screens/__tests__/Home.test.jsx` | Home screen (game selection, active rooms) |
| `ui/screens/__tests__/GameSetup.test.jsx` | Game setup (create/join tabs) |

### Frontend Playwright E2E (`frontend/e2e/`)

| File | What it tests | Servers needed |
|------|--------------|----------------|
| `charades-full-game.spec.js` | Full 2-player charades: guest login, room create/join, lobby, game start, roles, word/hint, correct guess, game end. Mid-game leave (auto-end). Stay button dismiss. | Backend + Frontend |
| `scribble-full-game.spec.js` | Full 2-player scribble: guest login, room create/join, lobby, game start, drawer/guesser roles, canvas, word/hint, correct guess with points. Mid-game leave. | Backend + Frontend |
| `trivia-full-game.spec.js` | Full 2-player trivia: guest login, room create/join, lobby, game start, question + 4 options, both answer, results shown, question progression. Mid-game leave (solo continues). | Backend + Frontend |
| `play-again.spec.js` | Play-again voting flow (REST API based) | Backend + Frontend |
| `mobile-keyboard.spec.js` | Mobile layout and keyboard handling | Frontend |

## Writing New Tests

### Backend socket event tests

Use the existing pattern from `test_socket_game.py`:

```python
@pytest.mark.asyncio
async def test_my_feature():
    # 1. Set up DB (users, words)
    db = SessionLocal()
    host = User(email="unique@x.com", google_id="google-unique")
    db.add(host)
    db.add(Word(text="testword", difficulty=1, active=True))
    db.commit()
    token = create_access_token(str(host.id))
    db.close()

    # 2. Create socket connections
    sid = await sio.manager.connect("eio-unique", "/")

    # 3. Trigger events
    res = await sio._trigger_event("room:create", "/", sid, {...})

    # 4. Assert results
    assert res["ok"] is True
```

**Important:** Use unique email addresses per test to avoid conflicts with the `clear_users` fixture.

### Backend REST tests

Use `client` fixture from conftest:

```python
def test_my_endpoint(client):
    token = create_user_and_token("unique@x.com")
    res = client.post("/endpoint", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
```

### Frontend component tests

Use vitest + @testing-library/react:

```jsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import MyComponent from '../MyComponent.jsx'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent prop="value" />)
    expect(screen.getByText('expected text')).toBeTruthy()
  })
})
```

## Coverage Priorities

When adding a new feature, tests should cover:

1. **Happy path** - Feature works as expected
2. **Edge cases** - 2 players, max players, empty state
3. **Error handling** - Invalid input, unauthorized access
4. **Interaction with existing features** - Does play-again still work? Does turn rotation break?

### Frontend Playwright E2E tests

Use 2 browser contexts for 2-player games. Pattern from `charades-full-game.spec.js`:

```javascript
test('my game flow', async ({ browser }) => {
  const ctx1 = await browser.newContext()
  const ctx2 = await browser.newContext()
  const player1 = await ctx1.newPage()
  const player2 = await ctx2.newPage()

  try {
    await loginAsGuest(player1, 'Alice')  // clear storage, fill name, click Play as Guest
    await loginAsGuest(player2, 'Bob')
    const roomCode = await createRoom(player1)  // click game, click Create Room
    await joinRoom(player2, roomCode)            // click game, Join tab, fill code, click Join
    // ... game flow assertions
  } finally {
    await ctx1.close()
    await ctx2.close()
  }
})
```

**Important patterns:**
- Always clear `localStorage` and `sessionStorage` in `loginAsGuest` to avoid stale auth
- Use `page.getByPlaceholder(/enter your name/i)` not `input[type="text"]` for the name input
- Use `page.locator('button.btn-primary', { hasText: /create room/i })` to distinguish submit buttons from tab buttons
- Use `page.getByLabel(/leave game/i)` for the leave button (aria-label)
- Use `test.setTimeout(120000)` for full-game tests (turn timers are 60-120s)

### Currently well-covered areas
- Room creation/joining (REST + Socket)
- Game start and turn progression
- Correct guess scoring (charades + scribble)
- Play-again voting flow
- Word seeding and deduplication
- Mid-game leave (game:leave) -- backend + E2E
- Grace period rotation
- Full game flow E2E for all 3 game modes (charades, scribble, trivia)

### Areas needing more coverage
- Trivia answer validation and scoring (backend unit tests)
- Scribble drawing stroke relay (backend unit tests)
- Frontend Lobby screen (component tests)
- Reconnection mid-turn scenarios (beyond grace period)
- 3+ player E2E tests
