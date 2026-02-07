# Charade Chat API & Socket Integration Guide

This document describes all REST APIs and Socket.IO events currently implemented, along with client integration guidance for the UI.

## 1. Auth Model Overview
- Registered users authenticate via JWT from `/token`.
- Guest users authenticate via `guest_token` from `/guest`.
- Socket events accept `token` (JWT) or `guest_token` in the event payload.

### JWT Usage
- Store the JWT on the client (e.g., in memory or local storage).
- Include it in:
  - REST: `Authorization: Bearer <token>`
  - Socket events: `token` field in payload

### Guest Token Usage
- Call `POST /guest` to receive `guest_token`.
- Include it in:
  - REST: `guest_token` field in payload where applicable
  - Socket events: `guest_token` field in payload


## 2. REST APIs

### 2.1 Register
`POST /register`

**Request**
```json
{ "email": "user@example.com", "password": "secret" }
```

**Response 201**
```json
{ "id": 1, "email": "user@example.com" }
```

**Errors**
- `400` Email already registered


### 2.2 Login
`POST /token`

**Request (form encoded)**
```
username=user@example.com&password=secret
```

**Response 200**
```json
{ "access_token": "<JWT>", "token_type": "bearer" }
```

**Errors**
- `401` Invalid credentials


### 2.3 Create Guest Token
`POST /guest`

**Response 201**
```json
{ "guest_token": "<token>" }
```


### 2.4 Create Room (Registered User)
`POST /rooms`

**Headers**
- `Authorization: Bearer <JWT>`

**Request**
```json
{ "rounds_total": 2, "difficulty": 1, "turn_seconds": 60, "max_players": 20 }
```

**Response 201**
```json
{
  "room": { "id": 1, "code": "A1B2C3", "status": "lobby", "max_players": 20, "min_players": 2, "rounds_total": 2, "difficulty": 1, "turn_seconds": 60 },
  "players": [ ... ],
  "self_player_id": 10
}
```


### 2.5 Create Room (Guest)
`POST /rooms/guest`

**Request**
```json
{ "guest_token": "<token>", "rounds_total": 2, "difficulty": 1, "turn_seconds": 60, "max_players": 20 }
```

**Response 201**
```json
{ "room": { ... }, "players": [ ... ], "self_player_id": 11 }
```

**Errors**
- `401` Invalid guest token
- `403` Guest limit reached


### 2.6 Join Room
`POST /rooms/join`

**Request (registered)**
```json
{ "room_code": "A1B2C3" }
```

**Request (guest)**
```json
{ "room_code": "A1B2C3", "guest_token": "<token>" }
```

**Response 200**
```json
{ "room": { ... }, "players": [ ... ], "self_player_id": 12 }
```

**Notes**
- If the room is already active, the user still joins, but is marked `in_game = false` (waiting for next game).

**Errors**
- `401` Authentication required
- `404` Room not found
- `409` Room is full


### 2.7 Get Room State
`GET /rooms/{room_code}`

**Response 200**
```json
{ "room": { ... }, "players": [ ... ], "self_player_id": null }
```


### 2.8 Update Room Settings (Host Only)
`PUT /rooms/{room_code}/settings`

**Headers**
- `Authorization: Bearer <JWT>`

**Request**
```json
{ "rounds_total": 3, "difficulty": 2, "turn_seconds": 90 }
```

**Response 200**
```json
{ "room": { ... }, "players": [ ... ] }
```

**Errors**
- `401` Authentication required
- `403` Only host can update settings
- `404` Room not found


## 3. Socket.IO Events

### 3.1 Connection
- Connect to Socket.IO normally.
- Send auth info in each event payload:
  - Registered: `token`
  - Guest: `guest_token`


### 3.2 Room Events

#### `room:create`
Creates a room via Socket and joins the host.

**Payload (registered)**
```json
{ "token": "<JWT>", "rounds_total": 2, "difficulty": 1, "turn_seconds": 60, "max_players": 20 }
```

**Payload (guest)**
```json
{ "guest_token": "<token>", "rounds_total": 2, "difficulty": 1, "turn_seconds": 60, "max_players": 20 }
```

**Response**
```json
{ "ok": true, "lobby": { "room": { ... }, "players": [ ... ], "self_player_id": 10 } }
```

#### `room:join`
Joins a room via Socket.

**Payload (registered)**
```json
{ "room_code": "A1B2C3", "token": "<JWT>" }
```

**Payload (guest)**
```json
{ "room_code": "A1B2C3", "guest_token": "<token>" }
```

**Response**
```json
{ "ok": true, "lobby": { "room": { ... }, "players": [ ... ], "self_player_id": 11 } }
```

#### `room:lobby_update` (server broadcast)
Emitted to room on join/leave or settings changes.

**Payload**
```json
{ "room": { ... }, "players": [ ... ], "self_player_id": 11 }
```


### 3.3 Game Events

#### `game:start`
Host starts the game. Server sets turn timer and selects initial word.

**Payload**
```json
{ "room_code": "A1B2C3", "token": "<JWT>" }
```

**Response**
```json
{ "ok": true }
```

**Errors**
- `FORBIDDEN`: non-host user
- `BAD_REQUEST`: not enough players


#### `game:turn_start` (server broadcast)
Indicates a new turn is active.

**Payload**
```json
{ "describer_id": 10, "turn_seconds": 60, "turn_start_ts": 1700000000 }
```


#### `game:new_word` (server → describer only)
Delivers the target word to the current describer.

**Payload**
```json
{ "word": "umbrella" }
```


#### `chat:message`
Client sends chat or guess.

**Payload**
```json
{ "room_code": "A1B2C3", "message": "Is it something you carry?" }
```

**Server behavior**
- If sender is describer, server blocks messages containing the target word (partial matches disallowed, plural/singular allowed).
- If sender is guesser:
  - Exact match triggers `game:correct_guess` and the describer receives a new word.
  - Otherwise, message is broadcast as normal chat.


#### `game:correct_guess` (server broadcast)
Emitted when a guess is correct.

**Payload**
```json
{ "guesser_id": 8, "word": "umbrella", "scores": {"8": 10, "10": 5} }
```


#### `game:turn_end` (optional client trigger)
Manual trigger for turn advance (server also advances automatically on timer).

**Payload**
```json
{ "room_code": "A1B2C3" }
```


#### `game:round_end` (server broadcast)
Emitted when a round finishes.

**Payload**
```json
{ "round_index": 1 }
```


#### `game:game_end` (server broadcast)
Emitted when all rounds are complete.

**Payload**
```json
{ "scores": {"8": 30, "10": 20} }
```


#### `game:reconnect_grace` (server broadcast)
Emitted when a player disconnects; includes grace period expiration.

**Payload**
```json
{ "player_id": 12, "expires_at": 1700000123 }
```


#### `game:player_removed` (server broadcast)
Emitted when a player fails to reconnect within grace period.

**Payload**
```json
{ "player_id": 12 }
```


### 3.4 Error Event
#### `error`
Server error responses for Socket actions.

**Payload**
```json
{ "code": "BAD_REQUEST", "message": "Not enough players" }
```


## 4. UI Integration Notes

### Lobby Screen
- Call `room:create` or `/rooms` to create room.
- Call `room:join` or `/rooms/join` to join.
- Subscribe to `room:lobby_update` to render player list and settings.
- If `room.status === 'active'`, show “Game in progress” banner and mark `in_game = false` players as waiting.

### Game Screen
- Host calls `game:start`.
- All players listen for `game:turn_start` to set timer UI.
- Describer listens for `game:new_word`.
- All players listen for `game:correct_guess` to update scores and show correct word.
- Use `game:round_end` and `game:game_end` for transitions.
- Use `game:reconnect_grace` to show reconnect countdown.
- Use `game:player_removed` to update lobby list and display a banner.

### Chat/Guess Input
- Send `chat:message` for both hints and guesses.
- If server responds with `error` code `HINT_BLOCKED`, show UI warning.

### Timing
- Use `turn_start_ts` from `game:turn_start` to synchronize countdown.
- Server drives turn end; UI should not assume exact timing from client clock alone.


## 5. Current Limitations
- Persistence is snapshot-based; full recovery is in place but not optimized.
- Word seeding is not yet automated (needs migration/seed step).
- Moderation/rate limits are optional and not implemented.
