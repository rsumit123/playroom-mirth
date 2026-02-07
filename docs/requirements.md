# Charade Chat (FastAPI Edition) Requirements

## 1. Scope and Goals
- Build a real-time web-based multiplayer charades/guessing game.
- Support registered and guest users.
- Target MVP scale: 100 concurrent users, up to 20 players per room.
- Deliver reliable real-time gameplay, score tracking, and room lifecycle.

## 2. Technology Stack
- Frontend: React (SPA) with `socket.io-client`.
- Styling: CSS Modules or Tailwind.
- Backend: FastAPI (ASGI) served by `uvicorn`.
- Real-time: `python-socketio` integrated with FastAPI.
- Database: SQLite3.
- ORM: SQLAlchemy.
- Validation: Pydantic.
- Auth: OAuth2PasswordBearer + JWT (python-jose), password hashing with passlib + bcrypt.
- Hosting: Docker container.

## 3. Functional Requirements

### 3.1 Authentication and User Management (REST)
- `POST /register`: Create a new user.
- `POST /token`: Login and return a JWT.
- Passwords must be hashed using bcrypt.
- JWT is required to authenticate Socket connections.

#### Guest Mode
- Guests are allowed to play one full match total.
- Guest identity must be durable across refresh (cookie + server-side record).

#### Concurrent Game Limit
- A registered user may participate in at most 3 active games simultaneously.
- The server must enforce this on join/start.

### 3.2 Room Management (Socket + REST)
- Create Room: Generates unique 6-character room code.
- Join Room: Requires room code and valid auth (registered or guest).
- Room Capacity: Max 20 players.
- Minimum to Start: 2 players (including host).
- Host can start the game without reaching max players.
- Late joiners are not allowed mid-game; they join the lobby and wait for the next game.

### 3.3 Game Configuration
- Host selects:
  - Number of rounds.
  - Difficulty (1-3).
  - Turn timer (30s-120s).

### 3.4 Game Loop
#### Turn
- A turn is a timed window (30-120 seconds).
- Multiple words can be guessed within a single turn.
- After each correct guess, the describer immediately receives a new word.
- The turn ends only when the timer expires.

#### Round
- A round ends when every player has been describer at least once.
- Describer order is fixed based on join sequence.

#### Game End
- The game ends after all rounds are completed.

#### Describer Selection
- Describer rotation follows join order.
- The server tracks describer index per round and turn.

#### Correct Guess Handling
- First correct guesser gets points (see scoring).
- Server broadcasts `correct_guess` and the correct word to all players.
- A new word is immediately assigned to the describer and announced to them only.

### 3.5 Hint and Guess Validation
- All chat messages go through the backend.
- Hint blocking rules:
  - Block if the hint contains the target word as an exact or partial match.
  - Allow plural/singular variations (e.g., `cat` vs `cats`).
  - Do not allow phonetic matching.
- Guess validation rule:
  - `message.lower().strip() == target_word` for a correct guess.

### 3.6 Scoring System
- First correct guesser: +10 points.
- Describer: +5 points for each correct guess elicited.
- Scoreboard is broadcast to the room after every turn switch.

### 3.7 Lobby State
- Real-time updates of connected players in lobby.
- Host can adjust settings before game start.

### 3.8 Word Management
- Words are stored in DB with a difficulty field.
- Minimum initial dataset: 100 words.
- If the selected difficulty bucket is exhausted during a game, the system pulls from another difficulty bucket.

### 3.9 Reconnect Handling
- Grace period: 60 seconds.
- Player can reconnect and resume their slot within the grace period.
- If grace period expires, player is removed from the active game.

## 4. Persistence and Recovery
- Game state must survive UI refresh.
- Game state should be recoverable after server restart.
- The system must persist:
  - Room configuration (rounds, difficulty, timer).
  - Player list and join order.
  - Current round and describer index.
  - Current word.
  - Scores.
  - Turn start timestamp and duration for timer recovery.

## 5. Non-Functional Requirements
- Concurrency target: 100 concurrent users.
- Room size: max 20 players.
- Reliable real-time updates with minimal latency for chat and gameplay.
- Docker-based deployment.

## 6. Event and API Considerations (High-Level)
- REST endpoints for registration and login.
- Socket events for:
  - Room create/join.
  - Lobby updates.
  - Game start.
  - Turn start/end.
  - New word to describer.
  - Chat/guess messages.
  - Scoreboard updates.
  - Player reconnect handling.

## 7. Future Enhancements (Out of Scope for MVP)
- Spectator mode.
- Dynamic word generation.
- Advanced anti-cheat and moderation tools.
- More sophisticated hint filtering (NLP/phonetics).
