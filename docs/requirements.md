# PlayRoom — Requirements

## 1. Scope and Goals
- Real-time web-based multiplayer party game platform.
- Two games: **Charades** (word guessing via chat hints) and **Scribble** (word guessing via drawing).
- Support Google Sign-In users and anonymous guest users.
- Target: up to 20 players per room, reliable real-time gameplay.

## 2. Technology Stack
- **Frontend**: React 18 + Vite SPA, Tailwind CSS, `socket.io-client`.
- **Backend**: FastAPI (ASGI) + `python-socketio`, served by Uvicorn.
- **Database**: SQLite via SQLAlchemy ORM.
- **Validation**: Pydantic v2 schemas.
- **Auth**: Google Sign-In (OAuth) for registered users, server-issued guest tokens (JWT).
- **Deployment**: Vercel (frontend), GCP VM + Docker + nginx (backend).

## 3. Functional Requirements

### 3.1 Authentication

#### Google Sign-In
- `POST /auth/google` — exchange Google ID token for a JWT.
- JWT is used for all authenticated REST calls and included in Socket.IO event payloads.
- New users are auto-created on first sign-in (display name and avatar from Google profile).

#### Guest Mode
- `POST /guest` — create a guest identity with a display name. Returns a guest token.
- `PATCH /guest` — update guest display name.
- Guest tokens are stored in localStorage. No match limits — guests can play unlimited games.
- Display name is required (frontend disables "Play as Guest" when name is empty).

### 3.2 Room Management

- **Create Room**: Generates a unique 6-character room code.
  - `POST /rooms` (signed-in) or `POST /rooms/guest` (guest).
- **Join Room**: `POST /rooms/join` with room code and auth token.
- **Room Capacity**: Max 20 players.
- **Minimum to Start**: 2 players.
- **Late Join**: Not allowed mid-game; players join the lobby and wait.
- **Leave Room**: `POST /rooms/{code}/leave`.
- **Active Rooms**: `GET /rooms/active` lists rooms the user is currently in.

### 3.3 Game Configuration
Host selects before starting:
- **Game type**: Charades or Scribble.
- **Number of rounds** (1+).
- **Difficulty**: 0 (mixed), 1 (easy), 2 (medium), 3 (hard).
- **Turn timer**: configurable duration per turn.
- Settings can be changed in the lobby via `PUT /rooms/{code}/settings`.

### 3.4 Game Loop

#### Charades
- **Turn**: One player is the describer, others guess via chat.
  - Describer sends chat hints (without saying the word). Hints containing the word are blocked.
  - First correct guesser earns points; describer gets a new word immediately.
  - Multiple words can be guessed per turn.
  - Turn ends when the timer expires or the host force-ends it.
- **Scoring**: +10 guesser, +5 describer per correct guess.

#### Scribble
- **Turn**: One player is the drawer, others guess via chat.
  - Drawer draws on a shared canvas; strokes are broadcast in real-time.
  - Each guesser can guess once (first correct guess counts).
  - Speed-based scoring: +15 (<5s), +12 (<10s), +10 (<20s), +7 (<30s), +5 (30s+).
  - Drawer bonus: +3 per correct guess, awarded at turn end.
  - Turn auto-ends when all guessers have guessed correctly, or when the timer expires.

#### Round
- One round = every player has been describer/drawer once.
- Describer order follows join sequence.
- `game:round_end` is broadcast at round boundaries.
- Host triggers next round with `game:next_round`.

#### Game End
- Game ends after all configured rounds are completed.
- `game:game_end` is broadcast with final scores and leaderboard.

### 3.5 Hint and Guess Validation
- All messages flow through the server.
- **Hint blocking**: Block if the message contains the target word as a substring (case-insensitive).
- **Guess validation**: `message.lower().strip() == target_word` for a correct guess.

### 3.6 Word Management
- Words stored in the database with a difficulty field (1-3).
- If the selected difficulty bucket is exhausted, the system pulls from another bucket.
- Word history tracked per room to prevent immediate repeats.

### 3.7 Reconnect Handling
- Grace period on disconnect (configurable, default 60s).
- Player can reconnect within the grace period and resume their slot.
- If grace period expires, player is removed from the active game.

### 3.8 Game History
- `GET /game-history` — returns recent game results for signed-in users.
- Tracks game type, scores, player count, date, and outcome.

## 4. Non-Functional Requirements
- Room size: max 20 players.
- Reliable real-time updates with minimal latency.
- Docker-based backend deployment behind nginx reverse proxy with SSL.
- Frontend deployed as static SPA with client-side routing.
- All REST calls have a 15-second timeout on the frontend.

## 5. Future Enhancements (Out of Scope)
- Spectator mode.
- Dynamic word generation (AI-generated words).
- Advanced anti-cheat and moderation tools.
- Additional game modes beyond Charades and Scribble.
