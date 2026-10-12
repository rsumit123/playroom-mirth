# Charade Chat - Codex Instructions

## Project Overview
Multiplayer game platform (charades, trivia, scribble) with React 18 + Vite frontend and FastAPI + python-socketio backend. Indian audience focus.

## Architecture
- **Frontend**: React 18, Vite, Socket.IO client (`frontend/`)
- **Backend**: FastAPI, python-socketio, SQLAlchemy + SQLite, JWT auth (`backend/`)
- **Real-time**: Socket.IO for room management, turns, chat, guessing
- **Deploy**: Frontend on Vercel (`playroom.skdev.one`), Backend on GCP VM via Docker

## Development Commands

### Backend
```bash
cd backend && .venv/bin/python -m pytest --tb=short -q  # Run backend tests
cd backend && .venv/bin/python -m pytest tests/test_specific.py -v  # Run specific test
```

### Frontend
```bash
cd frontend && npm run build  # Build frontend
cd frontend && npx vitest run  # Run frontend tests
cd frontend && npx playwright test  # Run e2e tests
```

### Production Build (with env vars)
```bash
cd frontend && VITE_API_BASE=https://charade-api.skdev.one VITE_SOCKET_URL=https://charade-api.skdev.one VITE_GOOGLE_CLIENT_ID=929006071236-55m4f4gujp7nnu9ldirbkrmr4qn30ng1.apps.googleusercontent.com npm run build
```

## Bug Fix Protocol

**Before applying any bug fix**, trace all related code paths and UI states that could be affected. Check for:
- Functions that call or are called by the modified code
- UI states that depend on the changed logic
- Socket event handlers that interact with the change
- Related game flows (e.g., playoff, season-end, day-advance)

**After every bug fix**, run the full test suite before committing. Multiple sessions have shown fixes introducing new bugs (duplicate fixtures, missing UI states), so always verify regressions.

## Testing Rules

**MANDATORY before every commit -- no exceptions:**
1. Backend tests: `cd backend && .venv/bin/python -m pytest --tb=short -q`
2. Frontend build: `cd frontend && npm run build`
3. Frontend tests: `cd frontend && npx vitest run`

If ANY test fails, do NOT commit. Fix the issue first.

**For game logic or socket changes, also run Playwright E2E tests:**
```bash
# Start both servers, then:
cd frontend && npx playwright test --project "Mobile Chrome"
```
This runs full 2-player game E2E tests for charades, scribble, and trivia.

**Additional rules:**
- For Python changes: always run backend tests after changes
- For JS/TS changes: always run frontend build + vitest after changes
- Run the full test suite at the START of a debugging session to establish a baseline
- When multiple bugs exist in the same system, analyze them together before fixing individually to find shared root causes
- When adding a new feature, add tests for it in the same commit
- See `docs/testing.md` for full testing guide, test structure, and writing conventions

## Content Generation Rules

- When generating text for PDFs or file output, use only ASCII-safe characters
- Avoid Unicode bullets, em dashes, and smart quotes -- use `-`, `--`, and straight quotes instead

## Common Pitfalls

- **Socket listener duplication**: Always `socket.off()` before `socket.on()`
- **selfPlayerId broadcast**: Don't set selfPlayerId from lobby_update broadcasts
- **Env vars baked at build time**: Must build with `VITE_API_BASE`, `VITE_SOCKET_URL`, `VITE_GOOGLE_CLIENT_ID` set
- **Socket reconnection**: Use `socket.on('connect')` not `socket.once('connect')` for room:register
- **Backend venv path**: `.venv` not `venv`
- **Vercel SPA routing**: Must use `{ handle: 'filesystem' }` BEFORE the SPA rewrite in routes
- **Vercel file upload API**: Use inline base64 files with v13 deployments API (upload API times out)

## Deployment

See `DEPLOY.md` for full deployment instructions. Quick reference:
- **Backend (GCP)**: `gcloud compute ssh socialflow ...` then `docker compose up --build -d`
- **Frontend (Vercel)**: Build with env vars, then `npx vercel --prod`
- Always run tests before deploying
