# Charade Chat (FastAPI Edition) Technical Spec

## 1. Architecture Overview
- Frontend: React SPA with `socket.io-client`.
- Backend: FastAPI (ASGI) + `python-socketio`.
- DB: SQLite3 via SQLAlchemy.
- Auth: JWT for REST and Socket auth.
- Deployment: Docker container.

### 1.1 Runtime Components
- ASGI app hosting FastAPI routes.
- Socket.IO server mounted on the ASGI app.
- SQLAlchemy session factory for DB access.
- In-memory cache for active room state, backed by DB snapshots.

### 1.2 Core Flows
- Auth flow: REST login returns JWT, stored by client.
- Socket connect: client sends JWT in handshake auth payload.
- Room flow: create/join room, lobby updates, game start.
- Game loop: timed turns, multiple word guesses per turn, scoring, rotation.
- Persistence: periodic room state snapshots and deterministic recovery on restart.

## 2. Data Model (SQLAlchemy)

### 2.1 Users
- `users`
- Fields:
  - `id` (PK, int)
  - `email` (unique, indexed)
  - `password_hash`
  - `created_at`

### 2.2 Guests
- `guests`
- Fields:
  - `id` (PK, int)
  - `guest_token` (unique, indexed)
  - `matches_played` (int)
  - `created_at`

### 2.3 Rooms
- `rooms`
- Fields:
  - `id` (PK, int)
  - `code` (unique, 6 chars)
  - `host_user_id` (nullable FK users.id)
  - `host_guest_id` (nullable FK guests.id)
  - `status` (enum: `lobby`, `active`, `finished`)
  - `max_players` (int, default 20)
  - `min_players` (int, default 2)
  - `rounds_total` (int)
  - `difficulty` (int, 1-3)
  - `turn_seconds` (int, 30-120)
  - `created_at`

### 2.4 Room Players
- `room_players`
- Fields:
  - `id` (PK, int)
  - `room_id` (FK rooms.id)
  - `user_id` (nullable FK users.id)
  - `guest_id` (nullable FK guests.id)
  - `join_order` (int)
  - `score` (int)
  - `connected` (bool)
  - `last_seen_at`
  - `in_game` (bool)

### 2.5 Words
- `words`
- Fields:
  - `id` (PK, int)
  - `text` (unique)
  - `difficulty` (int, 1-3)
  - `active` (bool)

### 2.6 Room State Snapshots
- `room_state`
- Fields:
  - `room_id` (PK, FK rooms.id)
  - `state_json` (JSON text)
  - `updated_at`

### 2.7 Room Events (Optional for audit)
- `room_events`
- Fields:
  - `id` (PK, int)
  - `room_id` (FK rooms.id)
  - `event_type` (string)
  - `payload_json` (JSON text)
  - `created_at`

## 3. In-Memory Game State
- Maintain active room state in memory for low-latency access.
- Periodically snapshot to `room_state` and on key transitions.
- On restart, rebuild in-memory state from DB snapshots.

### 3.1 Room State Schema (JSON)
```
{
  "room_id": 1,
  "status": "active",
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
  "scores": {"8": 20, "10": 10, "11": 0}
}
```

## 4. Auth and Identity
- REST uses OAuth2PasswordBearer.
- Socket handshake must include JWT in `auth.token`.
- Guest identity is stored as a durable cookie `guest_token`.
- Guests are blocked after `matches_played >= 1`.
- Registered users are blocked if active games >= 3.

## 5. Game Logic Details

### 5.1 Turn Timing
- Timer runs on the server.
- Store `turn_start_ts` and `turn_seconds` to recover remaining time.
- On restart, remaining time = `turn_seconds - (now - turn_start_ts)`.

### 5.2 Word Selection
- Filter by selected difficulty.
- If bucket exhausted, pull from another difficulty bucket.
- Prevent immediate repeats by tracking `word_history_ids` per room.

### 5.3 Guess Validation
- Correct guess when `message.lower().strip() == target_word`.
- The first correct guess wins.

### 5.4 Hint Filtering
- Block if hint contains the target word as exact or partial match.
- Allow plural/singular variations.
- No phonetic matching.

### 5.5 Rotation
- Describer order follows `join_order`.
- One round ends when all players have been describer at least once.
- Next round begins with same order.

### 5.6 Disconnect and Reconnect
- Grace period: 60 seconds.
- If reconnects within grace period, resume slot and role.
- If grace period expires, remove from active game and skip if they were describer.

## 6. REST API Spec

### 6.1 Register
- `POST /register`
- Request:
```
{ "email": "user@example.com", "password": "secret" }
```
- Response:
```
{ "id": 1, "email": "user@example.com" }
```

### 6.2 Login
- `POST /token`
- Request:
```
{ "username": "user@example.com", "password": "secret" }
```
- Response:
```
{ "access_token": "JWT", "token_type": "bearer" }
```

## 7. Socket.IO Event Spec

### 7.1 Connection
- Client connects with `auth.token = JWT` or `guest_token` cookie.
- Server validates and sets identity.

### 7.2 Room Events
- `room:create`
  - Request:
  ```
  { "rounds_total": 3, "difficulty": 2, "turn_seconds": 60 }
  ```
  - Response:
  ```
  { "room_code": "A1B2C3" }
  ```

- `room:join`
  - Request:
  ```
  { "room_code": "A1B2C3" }
  ```
  - Response:
  ```
  { "room_id": 1, "players": [...] }
  ```

- `room:lobby_update`
  - Broadcast:
  ```
  { "players": [...], "settings": {...} }
  ```

### 7.3 Game Events
- `game:start`
  - Host only.
  - Broadcasts initial round state.

- `game:turn_start`
  - Broadcast:
  ```
  { "describer_id": 10, "turn_seconds": 60, "turn_start_ts": 1700000000 }
  ```

- `game:new_word`
  - Sent to describer only:
  ```
  { "word": "umbrella" }
  ```

- `chat:message`
  - Client sends:
  ```
  { "message": "Is it a thing you carry?" }
  ```
  - Server broadcasts filtered messages.

- `game:correct_guess`
  - Broadcast:
  ```
  { "guesser_id": 8, "word": "umbrella", "scores": {...} }
  ```

- `game:turn_end`
  - Broadcast turn end and next describer.

- `game:round_end`
  - Broadcast round summary.

- `game:game_end`
  - Broadcast final summary.

### 7.4 Errors
- `error`
  - Example payload:
  ```
  { "code": "ROOM_FULL", "message": "Room is full" }
  ```

## 8. Concurrency and Limits
- Max 20 players per room.
- Target 100 concurrent users.
- Server enforces 3 active game limit per registered user.
- Guests limited to 1 full match total.

## 9. Observability (Minimal)
- Structured logs for:
  - Room creation and join.
  - Game start/end.
  - Turn start/end.
  - Errors and disconnects.

## 10. Out of Scope
- Spectator mode.
- Dynamic word generation.
- Advanced anti-cheat or moderation tools.
