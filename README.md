# Mirth

[![CI](https://github.com/rsumit123/playroom-mirth/actions/workflows/ci.yml/badge.svg)](https://github.com/rsumit123/playroom-mirth/actions/workflows/ci.yml)

A real-time multiplayer party game app for an Indian audience: charades, scribble, trivia and Texas Hold'em, playable in the browser and as an Android app. Make a room, share the code, and play with friends in seconds, or tap Quick Play to be matched with a stranger.

**Live at** [playroom.skdev.one](https://playroom.skdev.one). The Android app (`com.skdev.playroom`) is the same build wrapped with Capacitor.

## Games

| Game | How it plays |
|---|---|
| **Charades** | One player describes a secret word in chat without saying it; everyone else guesses. +10 to the guesser, +5 to the describer, then a new word. |
| **Scribble** | The drawer picks one of three words and draws it on a shared canvas. Faster guesses score more (15 down to 5); the drawer earns +3 per correct guesser. |
| **Trivia** | Ten questions a round from a 9,288-question bank in 12 India-focused categories (current affairs, defence, politics, Indian law, geography, mythology and more), plus generated maths. 100 points per correct answer plus up to 100 for speed. |
| **Quick Play** | One-tap 1v1 trivia. Players are paired by topic; if no one turns up within 15 seconds, a bot with human-like timing takes the seat. |
| **Poker** | No-limit Texas Hold'em for 2-4 seats. Empty seats can be filled by language-model players at three skill tiers. A session ends when one seat holds all the chips. |

Around the games: Google sign-in or guest play, friends and in-app invites, game history, leaderboards with win streaks, and reconnect handling (a 60-second grace period; Quick Play pauses and resumes).

## Architecture

```
  React 18 + Vite  ──REST──▶  FastAPI  ──▶  SQLite (SQLAlchemy)
  (web + Capacitor)  ◀─Socket.IO─▶ python-socketio
                                      │
                                      └──▶ OpenRouter (poker AI seats)
```

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, Socket.IO client |
| Android | Capacitor 8 wrapping the same web build |
| Backend | FastAPI + python-socketio on Uvicorn (single process) |
| Data | SQLite via SQLAlchemy 2; schema changes are guarded `ALTER TABLE`s in `db/init_db.py` |
| Auth | Google ID token exchanged for a 7-day JWT, or a guest token |
| Hosting | Vercel (frontend), GCP VM with Docker and nginx (backend) |

Live game state is held in memory (`ROOM_STATES`) and snapshotted to the `room_state` table after each change, so games in progress survive a restart. Because of that in-memory state the backend runs as a single process.

## Repository layout

```
backend/
  app/
    api/          REST routes: auth, guest, rooms, game history, friends, admin
    sockets/      Socket.IO handlers (events.py; poker in poker_events.py)
    services/     room ops, game state, trivia, matchmaker, bots,
                  holdem/ (poker engine), poker_ai/ (model-backed seats)
    models/       SQLAlchemy models
    schemas/      Pydantic schemas
    data/         trivia question bank (gk_questions.json) and staging batches
    tests/        pytest suite
  scripts/        question-bank tooling (newspaper OCR pipeline, dedupe, seeding)
frontend/
  src/
    state/        AppContext: auth, room, game state and socket wiring
    lib/          API client, socket singleton, sounds
    ui/           pages (routes), screens, components, poker/ (table UI)
  e2e/            Playwright specs
  android/        Capacitor Android project
scripts/          trivia question generators and editors
docs/             API reference, specs, testing, mobile and deployment guides
```

## Running locally

Requires Python 3.13 and Node 22+.

**Backend** (port 8005, matching `frontend/.env` and production):

```bash
cd backend
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:app --reload --port 8005
```

**Frontend** (port 5173):

```bash
cd frontend
npm install
npm run dev
```

### Environment variables

| Variable | Where | Purpose |
|---|---|---|
| `VITE_API_BASE`, `VITE_SOCKET_URL` | frontend, at build time | Backend URL (default `http://localhost:8000`) |
| `VITE_GOOGLE_CLIENT_ID` | frontend, at build time | Google sign-in client ID |
| `DATABASE_URL` | backend | SQLAlchemy URL (default `sqlite:///./charade.db`) |
| `JWT_SECRET_KEY` | backend | JWT signing secret; must be set in production |
| `GOOGLE_CLIENT_ID` | backend | Audience for verifying Google ID tokens |
| `OPENROUTER_API_KEY` | backend | Enables poker AI seats; without it they check or fold |
| `ENVIRONMENT=test` | backend | Enables `/auth/test_token` for end-to-end tests |

`VITE_*` values are baked into the bundle, so production and Android builds must be made with them set.

## Testing

CI (`.github/workflows/ci.yml`) runs on every push to `main` and every pull request:

1. **Backend**: `pytest` (about 300 tests: game flows, sockets, matchmaking, poker engine, friends, history).
2. **Frontend**: production build plus Vitest component tests.
3. **End-to-end**: starts the backend, runs the `live` pytest suite against it, then Playwright plays full 2-3 player games of charades, scribble, trivia and Quick Play in mobile Chrome.

Locally:

```bash
cd backend && .venv/bin/python -m pytest          # live tests skip unless a server is on :8005
cd frontend && npm run build && npx vitest run

# end-to-end: start the backend with ENVIRONMENT=test on :8005, then
cd backend && .venv/bin/python -m pytest -m live
cd frontend && npx playwright test --project "Mobile Chrome"
```

See [docs/testing.md](docs/testing.md) for more.

## Deployment

- **Backend**: Docker Compose on a GCP VM behind nginx at `charade-api.skdev.one`. See [DEPLOY.md](DEPLOY.md).
- **Frontend**: Vercel, built with the production `VITE_*` values.
- **Android**: `npm run build && npx cap sync android`, then a signed `bundleRelease`. See [docs/mobile-app.md](docs/mobile-app.md).

## Documentation

| Doc | Contents |
|---|---|
| [docs/api.md](docs/api.md) | REST endpoints and Socket.IO events |
| [docs/technical-spec.md](docs/technical-spec.md) | Architecture and game logic |
| [docs/TRIVIA.md](docs/TRIVIA.md) | Trivia mode and question format |
| [docs/poker-port.md](docs/poker-port.md) | How poker was brought in as a native game type |
| [docs/mobile-app.md](docs/mobile-app.md) | Capacitor and Android release process |
| [docs/testing.md](docs/testing.md) | Test layout and conventions |

## License

[MIT](LICENSE)
