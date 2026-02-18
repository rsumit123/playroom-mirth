# PlayRoom — Technical Specification

## 1. Architecture Overview

### 1.1 Runtime Components
- **Frontend**: React 18 SPA built with Vite, served via Vercel CDN.
- **Backend**: FastAPI ASGI app with `python-socketio` mounted, served by Uvicorn.
- **Database**: SQLite file via SQLAlchemy ORM (persisted via Docker volume).
- **Reverse Proxy**: nginx with WebSocket support and Let's Encrypt SSL.

### 1.2 Core Flows
- **Auth**: Google Sign-In → `POST /auth/google` → JWT. Guest → `POST /guest` → guest token.
- **Socket connect**: Client connects to Socket.IO, then emits `room:register` with room code + auth token.
- **Room flow**: Create/join room via REST, lobby updates via Socket.IO, host starts game.
- **Game loop**: Timed turns with describer rotation, chat-based guessing, real-time scoring.
- **Scribble flow**: Drawing strokes broadcast via `scribble:draw`, guessing via `chat:message`.

## 2. Data Model (SQLAlchemy)

### 2.1 Users (`users`)
| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer, PK | Auto-increment |
| `email` | String, unique, indexed | From Google profile |
| `google_id` | String, unique, nullable | Google sub ID |
| `display_name` | String | From Google profile |
| `avatar_url` | String, nullable | Google profile picture |
| `password_hash` | String | Set to `""` for Google users (legacy column) |
| `created_at` | DateTime | Auto-set |

### 2.2 Guests (`guests`)
| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer, PK | Auto-increment |
| `guest_token` | String, unique, indexed | JWT-like token |
| `display_name` | String | User-chosen name |
| `created_at` | DateTime | Auto-set |

### 2.3 Rooms (`rooms`)
| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer, PK | Auto-increment |
| `code` | String, unique | 6-character room code |
| `host_user_id` | Integer, FK → users.id, nullable | |
| `host_guest_id` | Integer, FK → guests.id, nullable | |
| `status` | String | `lobby`, `active`, `finished` |
| `game_type` | String | `charades` or `scribble` |
| `rounds_total` | Integer | Configured by host |
| `difficulty` | Integer | 0=mixed, 1-3 |
| `turn_seconds` | Integer | Turn duration |
| `created_at` | DateTime | Auto-set |

### 2.4 Room Players (`room_players`)
| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer, PK | Auto-increment |
| `room_id` | Integer, FK → rooms.id | |
| `user_id` | Integer, FK → users.id, nullable | |
| `guest_id` | Integer, FK → guests.id, nullable | |
| `join_order` | Integer | Determines describer rotation |
| `score` | Integer | Current game score |
| `connected` | Boolean | Socket connection status |
| `last_seen_at` | DateTime | For disconnect grace |
| `in_game` | Boolean | Active in current game |

### 2.5 Words (`words`)
| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer, PK | Auto-increment |
| `text` | String, unique | The word |
| `difficulty` | Integer | 1-3 |
| `active` | Boolean | Can be selected |

### 2.6 Game History (`game_history`)
| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer, PK | Auto-increment |
| `user_id` | Integer, FK → users.id | Signed-in user |
| `room_code` | String | Room where game was played |
| `game_type` | String | `charades` or `scribble` |
| `score` | Integer | Player's final score |
| `rank` | Integer | Leaderboard position |
| `player_count` | Integer | Total players |
| `created_at` | DateTime | When game ended |

## 3. In-Memory Game State

Active room state is maintained in memory (Python dict) for low-latency access during gameplay:

```json
{
  "room_id": 1,
  "status": "active",
  "game_type": "charades",
  "round_index": 1,
  "rounds_total": 3,
  "turn_start_ts": 1700000000,
  "turn_seconds": 60,
  "describer_index": 2,
  "describer_player_id": 10,
  "current_word_id": 55,
  "current_word_text": "umbrella",
  "word_history_ids": [12, 14, 55],
  "player_order": [8, 10, 11],
  "scores": {"8": 20, "10": 10, "11": 0},
  "guessed_players": [8]
}
```

Key differences by game type:
- **Charades**: `guessed_players` not tracked per-turn (multiple words per turn, any guesser can guess any word).
- **Scribble**: `guessed_players` tracks who has guessed the current word (each guesser can only guess once). Turn auto-ends when all guessers are in this set.

## 4. Auth and Identity

### Google Sign-In
- Frontend uses Google Identity Services (`accounts.google.com/gsi/client`).
- Google ID token sent to `POST /auth/google`, verified server-side.
- Server returns a JWT containing `user_id`, `email`, `display_name`.

### Guest Auth
- `POST /guest` creates a guest record and returns a guest token.
- Guest token is a JWT containing `guest_id` and `display_name`.
- Stored in `localStorage` on the frontend.

### Socket.IO Auth
- Auth tokens are NOT sent in connection headers.
- Instead, tokens are included in Socket.IO event payloads (e.g., `room:register` payload contains `guest_token` or JWT).
- Server extracts identity from the payload on each event.

## 5. Game Logic Details

### 5.1 Turn Timing
- Timer runs on the server using `asyncio` tasks.
- `turn_start_ts` stored for timer recovery on reconnect.
- Remaining time sent to clients on reconnect: `turn_seconds - (now - turn_start_ts)`.

### 5.2 Scoring

#### Charades
| Event | Points |
|-------|--------|
| Correct guess (guesser) | +10 |
| Correct guess (describer) | +5 |

#### Scribble (speed-based)
| Guess Time | Guesser Points |
|------------|---------------|
| < 5 seconds | +15 |
| < 10 seconds | +12 |
| < 20 seconds | +10 |
| < 30 seconds | +7 |
| 30+ seconds | +5 |

Drawer bonus: +3 per correct guess, awarded at turn end.

### 5.3 Describer/Drawer Rotation
- Order follows `join_order` in `room_players`.
- One round = every active player has been describer/drawer once.
- Next round repeats the same order.

### 5.4 Disconnect and Reconnect
- On disconnect, a grace period timer starts (default 60s).
- `game:reconnect_grace` broadcast to room with countdown.
- If player reconnects, they resume their slot.
- If grace expires, `game:player_removed` broadcast; player skipped if they were next describer.

## 6. REST API

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/google` | — | Exchange Google ID token for JWT |
| POST | `/guest` | — | Create guest identity |
| PATCH | `/guest` | guest_token | Update guest display name |
| POST | `/rooms` | JWT | Create room (signed-in user) |
| POST | `/rooms/guest` | guest_token | Create room (guest) |
| POST | `/rooms/join` | JWT/guest | Join existing room |
| GET | `/rooms/{code}` | JWT/guest | Get room lobby state |
| PUT | `/rooms/{code}/settings` | host only | Update room settings |
| GET | `/rooms/active` | JWT/guest | List user's active rooms |
| POST | `/rooms/{code}/leave` | JWT/guest | Leave a room |
| GET | `/game-history` | JWT | Get recent game history |

## 7. Socket.IO Events

### 7.1 Room Events

| Event | Direction | Payload | Description |
|-------|-----------|---------|-------------|
| `room:register` | client → server | `{room_code, guest_token/token}` | Register socket with a room |
| `room:lobby_update` | server → room | `{players, settings, host_id}` | Broadcast lobby state |

### 7.2 Game Events

| Event | Direction | Payload | Description |
|-------|-----------|---------|-------------|
| `game:start` | client → server | `{room_code, token}` | Host starts the game |
| `game:turn_start` | server → room | `{describer_id, turn_seconds, round, turn}` | New turn begins |
| `game:new_word` | server → describer | `{word}` | Secret word for current turn |
| `chat:message` | bidirectional | `{message, room_code, token}` | Chat messages and guesses |
| `game:correct_guess` | server → room | `{guesser_id, word, scores}` | Correct guess notification |
| `game:turn_end` | client → server | `{room_code, token}` | Host force-ends turn |
| `game:round_end` | server → room | `{round, scores}` | Round boundary |
| `game:next_round` | client → server | `{room_code, token}` | Host continues to next round |
| `game:game_end` | server → room | `{scores, leaderboard}` | Final scores |

### 7.3 Scribble Events

| Event | Direction | Payload | Description |
|-------|-----------|---------|-------------|
| `scribble:draw` | bidirectional | `{strokes, room_code}` | Drawing stroke data |
| `scribble:clear` | bidirectional | `{room_code}` | Clear canvas |

### 7.4 Connection Events

| Event | Direction | Payload | Description |
|-------|-----------|---------|-------------|
| `game:reconnect_grace` | server → room | `{player_id, seconds}` | Disconnect grace period |
| `game:player_removed` | server → room | `{player_id}` | Player removed after grace |

## 8. Frontend State Management

### AppContext (React Context)
- **Auth state**: `user`, `guestToken`, `isGuest` — persisted in `localStorage`.
- **Room state**: `roomCode`, `selfPlayerId` — persisted in `sessionStorage`.
- **Lobby state**: `players`, `settings`, `isHost`.
- **Game state**: `gameStarted`, `currentDescriber`, `scores`, `round`, `word`, `timeLeft`.
- **Socket**: Single `socket.io-client` instance, managed in context.

### Key Patterns
- Socket listeners: Always `socket.off(event)` before `socket.on(event)` to prevent duplicates.
- `selfPlayerId`: Set only from REST responses, never from broadcast events.
- Route guards: Redirect to welcome if no auth, redirect to lobby/game if active room.

## 9. Deployment

### Frontend (Vercel)
- Build with `VITE_API_BASE` and `VITE_SOCKET_URL` env vars.
- Deploy using Vercel v13 API with inline base64 files (file upload API times out).
- Must include `vercel.json` with SPA rewrites.
- Aliases: `playroom.skdev.one`, `charade-chat.skdev.one`.

### Backend (GCP VM + Docker)
- GCP `e2-small` VM in `us-east1-d`.
- Docker Compose runs the FastAPI app on port 8005.
- nginx reverse proxy with WebSocket support (`Upgrade` + `Connection` headers).
- SSL via Let's Encrypt + Certbot (auto-renewing).
- Domain: `charade-api.skdev.one`.

## 10. Testing

### Automated Stress Test (`backend/stress_test.py`)
- Simulates N concurrent players (2-10) playing a full game via Socket.IO + REST.
- Supports both Charades and Scribble game types.
- Validates: turn count, describer rotation, score consistency, round boundaries, game end, no errors, non-negative scores.
- See README.md for usage and CLI options.
