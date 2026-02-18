# PlayRoom (Charade Chat)

A real-time multiplayer party game platform with **Charades** and **Scribble** — play with friends in seconds.

**Live at**: [playroom.skdev.one](https://playroom.skdev.one)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite, Tailwind CSS, Socket.IO client |
| Backend | FastAPI (ASGI) + python-socketio, Uvicorn |
| Database | SQLite via SQLAlchemy ORM |
| Auth | Google Sign-In (OAuth) + Guest tokens (JWT) |
| Deployment | Vercel (frontend), GCP VM + Docker + nginx (backend) |

## Games

### Charades
- One player **describes** a word using chat hints (without saying the word)
- Other players **guess** the word in the chat
- Correct guess: **+10 guesser**, **+5 describer**, then a new word is assigned
- Turn continues until the timer expires, then the next player describes

### Scribble
- One player **draws** a word on a shared canvas
- Other players **guess** the word in the chat
- Speed-based scoring: **+15** (< 5s), **+12** (< 10s), **+10** (< 20s), **+7** (< 30s), **+5** (30s+)
- Drawer bonus: **+3 per correct guess**, awarded at turn end
- Turn ends automatically when all guessers have guessed, or when the timer expires

### Game Flow
1. Create or join a room with a 6-character code
2. Host configures rounds, difficulty, and turn timer
3. Players take turns as describer/drawer (rotation follows join order)
4. After all players have described once = 1 round
5. Game ends after all rounds complete, final leaderboard shown

## Project Structure

```
charade-chat/
  backend/
    app/
      api/           # REST endpoints (auth, rooms, guest, game history)
      models/        # SQLAlchemy models (User, Room, RoomPlayer, Word, etc.)
      schemas/       # Pydantic request/response schemas
      services/      # Business logic (room ops, game state, auth)
      sockets/       # Socket.IO event handlers
      core/          # Config, constants
      db/            # Database session setup
    stress_test.py   # Automated multiplayer stress test
    Dockerfile
    docker-compose.yml
  frontend/
    src/
      ui/
        pages/       # Route pages (WelcomePage, HomePage, etc.)
        screens/     # UI screens (Welcome, Home, ScribbleGame, etc.)
        components/  # Reusable components (Scoreboard, DrawingCanvas, etc.)
      state/         # AppContext (global state + socket management)
      lib/           # API client, socket utilities
    e2e/             # Playwright mobile UI tests
  docs/              # Requirements and technical spec
```

## Local Development

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

The frontend dev server runs on `http://localhost:5173` and proxies API calls to `http://localhost:8000`.

### Environment Variables
- `VITE_API_BASE` — Backend API URL (default: `http://localhost:8000`)
- `VITE_SOCKET_URL` — Socket.IO server URL (default: same as API base)
- `VITE_GOOGLE_CLIENT_ID` — Google OAuth client ID

## Deployment

### Frontend (Vercel)

Build with production env vars, then deploy the `dist/` directory:

```bash
cd frontend
VITE_API_BASE=https://charade-api.skdev.one \
VITE_SOCKET_URL=https://charade-api.skdev.one \
npm run build
```

Deploy using the Vercel v13 API with inline base64 files (the file upload API tends to timeout). Include `vercel.json` with SPA rewrites:

```json
{ "rewrites": [{ "source": "/((?!assets/).*)", "destination": "/index.html" }] }
```

Production aliases: `playroom.skdev.one`, `charade-chat.skdev.one`

### Backend (GCP VM + Docker)

SSH into the VM, pull latest code, and rebuild the container:

```bash
# From local machine
gcloud compute ssh socialflow --project=polar-pillar-450607-b7 --zone=us-east1-d

# On the VM
cd charade-chat
git pull origin main
cd backend
docker compose down && docker compose up --build -d
```

The backend runs on port 8005 behind nginx with SSL (Let's Encrypt).

Production domain: `charade-api.skdev.one`

### Infrastructure Details
- **VM**: GCP `e2-small` in `us-east1-d`
- **Reverse proxy**: nginx with WebSocket support (`Upgrade` + `Connection` headers)
- **SSL**: Let's Encrypt via Certbot (auto-renewing)
- **Database**: SQLite file inside the Docker container (persisted via volume)

## Testing

### Backend Unit Tests
```bash
cd backend
.venv/bin/python -m pytest
```

### Frontend Tests
```bash
cd frontend
npx vitest run
```

### Mobile UI Tests (Playwright)
```bash
cd frontend
npx playwright install
npx playwright test
```

### Multiplayer Stress Test

Simulates N concurrent players (5-10) playing a full game via Socket.IO + REST to validate event consistency, scoring, and turn rotation:

```bash
cd backend

# Charades — 5 players, 2 rounds, against production
.venv/bin/python stress_test.py \
  --url https://charade-api.skdev.one \
  --players 5 --rounds 2 --game-type charades

# Scribble — 10 players, 2 rounds
.venv/bin/python stress_test.py \
  --url https://charade-api.skdev.one \
  --players 10 --rounds 2 --game-type scribble

# Against local dev server with verbose logging
.venv/bin/python stress_test.py \
  --url http://localhost:8000 \
  --players 5 --rounds 2 --game-type charades -v
```

**Options:**
| Flag | Default | Description |
|------|---------|-------------|
| `--url` | `http://localhost:8000` | Backend API URL |
| `--players` | `5` | Number of simulated players (2-10) |
| `--rounds` | `2` | Number of game rounds |
| `--turn-seconds` | `60` | Turn duration |
| `--game-type` | `charades` | `charades` or `scribble` |
| `--difficulty` | `1` | Word difficulty (0=mixed, 1-3) |
| `--timeout` | `300` | Overall test timeout in seconds |
| `-v` | off | Verbose debug logging |

**Validations performed:**
1. All players receive the correct number of `turn_start` events
2. Every player is describer exactly `rounds` times
3. All players see identical final scores
4. `round_end` events fire at correct boundaries
5. `game_end` received by all players
6. No unexpected errors
7. All scores are non-negative

## Auth

- **Google Sign-In**: Primary auth method. Returns JWT for API calls.
- **Guest mode**: Creates a server-side guest record with a token. Requires a display name. Guest progress is not saved across devices.
- Auth tokens are sent in Socket.IO event payloads (not connection headers).

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/google` | - | Exchange Google ID token for JWT |
| POST | `/guest` | - | Create guest identity |
| PATCH | `/guest` | guest_token | Update guest display name |
| POST | `/rooms/guest` | guest_token | Create room as guest |
| POST | `/rooms` | JWT | Create room as signed-in user |
| POST | `/rooms/join` | JWT/guest | Join existing room |
| GET | `/rooms/{code}` | JWT/guest | Get room lobby state |
| PUT | `/rooms/{code}/settings` | host only | Update room settings |
| GET | `/rooms/active` | JWT/guest | List active rooms for user |
| POST | `/rooms/{code}/leave` | JWT/guest | Leave a room |
| GET | `/game-history` | JWT | Get recent game history (signed-in only) |

## Socket.IO Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `room:register` | client → server | Register socket with a room |
| `room:lobby_update` | server → room | Broadcast player list and settings |
| `game:start` | client → server | Host starts the game |
| `game:turn_start` | server → room | New turn begins |
| `game:new_word` | server → describer | Secret word for current turn |
| `chat:message` | bidirectional | Chat messages and guess attempts |
| `game:correct_guess` | server → room | Correct guess with updated scores |
| `game:turn_end` | client → server | Force-end current turn |
| `game:round_end` | server → room | Round boundary with scores |
| `game:next_round` | client → server | Host continues to next round |
| `game:game_end` | server → room | Final scores and game over |
| `scribble:draw` | bidirectional | Drawing stroke data (Scribble only) |
| `scribble:clear` | bidirectional | Clear canvas (Scribble only) |
| `game:reconnect_grace` | server → room | Player disconnect grace period |
| `game:player_removed` | server → room | Player removed after grace |
