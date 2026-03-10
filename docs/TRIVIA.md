# Trivia Game Mode

## 1. Overview

Trivia is one of three game modes in Charade Chat, alongside Charades and Scribble. Unlike those two, trivia is **simultaneous play**: all players see the same question at the same time, select an answer independently, and earn points based on correctness and speed. There are no roles (no describer/drawer vs. guesser distinction). The only category currently available is **Mental Math**, where questions are procedurally generated arithmetic problems.

Key differences from Charades/Scribble:

| Aspect | Charades / Scribble | Trivia |
|---|---|---|
| Turn structure | One describer/drawer per turn, others guess | All players answer every question simultaneously |
| Roles | Describer + guessers (rotate) | No roles (`describer_id` is set to `-1`) |
| Word/Question source | Database word list | Procedurally generated math questions |
| Timer | Per-turn (configurable) | Per-question (set by difficulty) |
| Chat | Used for guessing | Not used during gameplay |

## 2. Game Flow

```
Room Creation  -->  Lobby (settings)  -->  game:start
     |                                        |
     |                              game:turn_start (describer_id=-1, navigation trigger)
     |                                        |
     |                              _trivia_start_round()
     |                                        |
     |                              trivia:question  (Q1 of 10)
     |                                        |
     |                              Players answer via trivia:answer
     |                              trivia:answer_update broadcasts progress
     |                                        |
     |                              Timer expires OR all players answer
     |                                        |
     |                              trivia:question_result  (4s pause)
     |                                        |
     |                              trivia:question  (Q2 of 10)
     |                                        |
     |                              ... repeat for all 10 questions ...
     |                                        |
     |                              game:round_end  (if more rounds remain)
     |                                  OR
     |                              game:game_end   (if final round)
     |                                        |
     |                              Host clicks "Next Round"
     |                              game:next_round -> game:turn_start -> new round
```

### Step-by-step

1. **Room creation**: Host creates a room with `game_type: "trivia"` via the GameSetup screen or REST API.
2. **Lobby settings**: Host can adjust rounds (1-5) and difficulty (Easy/Medium/Hard). Timer slider is hidden for trivia. The "Mixed" difficulty option is also hidden.
3. **Game start** (`game:start` event): Only the host can trigger this. The backend:
   - Creates a `RoomGameState` with `game_type="trivia"` and `turn_seconds=0`.
   - Emits `game:turn_start` with `describer_id: -1` as a **navigation trigger** -- the frontend uses this to route from `/lobby` to `/trivia`.
   - Calls `_trivia_start_round()` which generates 10 questions and emits the first one.
4. **Question loop**: For each of the 10 questions per round:
   - `trivia:question` is emitted to the room.
   - A per-question timer starts on the server (duration depends on difficulty).
   - Players submit answers via `trivia:answer`.
   - `trivia:answer_update` is broadcast after each submission with the count of answered players.
   - When the timer expires OR all players have answered, `_trivia_question_timeout()` fires:
     - Calculates scores for each player.
     - Emits `trivia:question_result` with per-player results and updated scores.
     - Schedules a **4-second pause** before advancing to the next question.
5. **Round end**: After 10 questions, `state.round_index` increments. If more rounds remain, `game:round_end` is emitted and the game pauses until the host triggers `game:next_round`.
6. **Next round**: Host emits `game:next_round`. Backend emits another `game:turn_start` navigation trigger and calls `_trivia_start_round()` for a fresh batch of 10 questions.
7. **Game end**: When all rounds are complete, `game:game_end` is emitted with final scores. The room status reverts to `"lobby"`. Game history is saved for signed-in users.

## 3. Question Generation

All trivia questions are currently **Mental Math** problems, generated in `backend/app/services/trivia.py`.

### Questions per difficulty

Each round generates **10 questions** via `generate_round_questions(difficulty, count=10)`.

| Difficulty | Value | Timer | Operations |
|---|---|---|---|
| Easy | `1` | 20s | Addition (1-50), Subtraction (1-50, no negatives), Multiplication (2-12) |
| Medium | `2` | 15s | Addition (10-200), Subtraction (10-200), Multiplication (2-20 x 10-50), Division (exact, 2-20), Two-operation chains |
| Hard | `3` | 10s | Large multiplication (10-99 x 10-99), Percentages, Square roots (2-20), Multi-step chains (a x b + c - d) |
| Mixed | `0` | varies | 20% easy, 50% medium, 30% hard (randomly selected per question) |

**Note**: Mixed difficulty (`0`) is generated by the backend but the frontend hides this option in the `DifficultySelector` for trivia games (`hideMixed={gameType === 'trivia'}`). The default difficulty for new trivia rooms is `1` (Easy).

### Distractor logic

Each question has **4 options**: 1 correct answer + 3 distractors generated by `_make_distractors()`:

- Distractors are within 5-25% of the correct value's magnitude, offset by a random integer in that range.
- They must be non-negative and distinct from the correct answer.
- A fallback loop adds incrementally offset values if the random approach doesn't produce enough distractors within 50 attempts.
- All 4 options are shuffled; `correct_index` tracks the correct answer's position.

### Question structure

```python
{
    "question": "What is 42 + 17?",
    "options": ["59", "55", "63", "48"],   # shuffled
    "correct_index": 0,                     # index of correct answer in options
    "time_seconds": 20                      # depends on difficulty
}
```

## 4. Socket Events

All events are transported over Socket.IO. Direction: `C->S` = client to server, `S->C` = server to client.

| Event | Direction | Payload | When it fires |
|---|---|---|---|
| `game:start` | C->S | `{ room_code, token/guest_token }` | Host starts the game from the lobby |
| `game:turn_start` | S->C | `{ game_type: "trivia", round_index, turn_seconds: 0, turn_start_ts, describer_id: -1 }` | Navigation trigger: on game start, on next round, and on reconnection. The frontend watches `game.turn` to route to `/trivia`. `describer_id: -1` signals no describer role. |
| `trivia:question` | S->C | `{ question_index, total_questions, question_text, options, time_seconds, round_index }` | Emitted at the start of each question within a round. `question_index` is 0-based. |
| `trivia:answer` | C->S | `{ room_code, answer_index }` | Player submits their answer. Rejected if already answered (`ALREADY_ANSWERED`). |
| `trivia:answer_update` | S->C | `{ answered_count, total_players }` | Broadcast after each player submits an answer. Used to show "X of Y answered" in the UI. |
| `trivia:question_result` | S->C | `{ question_index, correct_index, player_results: [...], scores }` | Emitted when the question timer expires or all players have answered. Each entry in `player_results` contains `{ player_id, answer_index, correct, points, time_taken }`. |
| `game:round_end` | S->C | `{ round_index, scores }` | Emitted after all 10 questions in a round are complete (and more rounds remain). `round_index` is the just-completed round (1-based). |
| `game:next_round` | C->S | `{ room_code, token/guest_token }` | Host triggers the next round from the round-end screen. Only the host can send this. |
| `game:game_end` | S->C | `{ scores }` | Emitted when the final round's last question finishes. Room reverts to lobby status. |

### `player_results` entry schema

```json
{
    "player_id": 42,
    "answer_index": 2,       // -1 if no answer submitted (timeout)
    "correct": true,
    "points": 167,            // 0 if wrong or timed out
    "time_taken": 3.2         // seconds, null if wrong/timed out
}
```

## 5. Scoring

Scoring is calculated in `_trivia_question_timeout()` in `events.py`:

- **Correct answer**: `100` (base) + speed bonus
- **Wrong answer or timeout**: `0` points

### Speed bonus formula

```
speed_bonus = max(0, floor(100 * (1 - time_taken / time_seconds)))
```

Where:
- `time_taken` = timestamp of answer submission minus `question_start_ts` (seconds)
- `time_seconds` = allowed time for the question (20/15/10 depending on difficulty)

This yields a bonus of **0 to 100 points**, for a total possible range of **100 to 200 points per question**:

| Scenario | Points |
|---|---|
| Instant correct answer | 200 (100 base + 100 speed) |
| Correct at half the time limit | 150 (100 base + 50 speed) |
| Correct at the deadline | 100 (100 base + 0 speed) |
| Wrong or no answer | 0 |

Maximum possible score per round (10 questions): **2,000 points**.

## 6. Frontend Architecture

### Route

`/trivia` is served by `TriviaGamePage` (route defined in `App.jsx`).

### Component hierarchy

```
TriviaGamePage
  -> TriviaGame (screen component)
       -> CircularTimer
       -> ConfettiBurst
       -> Scoreboard (desktop sidebar + mobile drawer)
       -> GameAlerts
       -> PlayerAvatar (in results list)
```

### TriviaGamePage (`/frontend/src/ui/pages/TriviaGamePage.jsx`)

- Reads `room`, `lobby`, `game`, `emitTriviaAnswer`, `selfPlayerId`, and `roomRestoreStatus` from `AppContext`.
- Redirects to `/home` if no room code after restore completes.
- Navigates to `/game-end` on `game.gameEnd` and to `/round-end` on `game.roundEnd`.
- Builds a `playerNames` map from `lobby.players`.
- Passes `handleAnswer(answerIndex)` which calls `emitTriviaAnswer(room.code, answerIndex)`.

### TriviaGame (`/frontend/src/ui/screens/TriviaGame.jsx`)

Two visual phases:

1. **Question phase** (`trivia` is set, `result` is null):
   - Displays the question text in a card.
   - Shows a 2x2 grid of color-coded answer buttons.
   - Runs a client-side countdown timer (`CircularTimer`) synced to when the question was received.
   - Shows "X of Y answered" below the options.
   - Once the player taps an answer, buttons dim and the selected one gets a ring highlight.

2. **Result phase** (`result` is set):
   - The correct answer turns green; the player's wrong answer (if any) turns red; other options dim.
   - A results card lists all players sorted by points, showing checkmark/X/clock icons.
   - Each correct player shows points earned and time taken.
   - "Next question in a moment..." pulsing text appears.
   - If the player answered correctly, confetti fires and a "correct-guess" sound plays.

### State management

Trivia-specific fields in `game` state (managed by `AppContext`):

| Field | Type | Set by |
|---|---|---|
| `game.trivia` | `object` | `trivia:question` listener |
| `game.triviaResult` | `object` | `trivia:question_result` listener |
| `game.triviaAnswered` | `boolean` | `emitTriviaAnswer()` (optimistic) |
| `game.triviaAnswerCount` | `object` | `trivia:answer_update` listener |

On each new `trivia:question`, `triviaResult`, `triviaAnswered`, and `triviaAnswerCount` are all reset.

### emitTriviaAnswer

```js
function emitTriviaAnswer(roomCode, answerIndex) {
    setGame((g) => ({ ...g, triviaAnswered: true }))   // optimistic lock
    socket.emit('trivia:answer', { room_code: roomCode, answer_index: answerIndex })
}
```

The `triviaAnswered` flag is set optimistically before the server responds, preventing double-taps.

## 7. Lobby Settings

When `game_type` is `"trivia"`, the lobby and game setup screens apply these differences:

| Setting | Charades/Scribble | Trivia |
|---|---|---|
| Rounds slider | 1-10 | 1-5 (capped) |
| Timer slider | Shown (configurable per-turn seconds) | Hidden (`turn_seconds` sent as `0`) |
| Difficulty selector | Shows Mixed/Easy/Medium/Hard | Hides "Mixed" option (`hideMixed=true`) |
| Default difficulty | 0 (Mixed) | 1 (Easy) |

The `DifficultySelector` component accepts a `hideMixed` prop that filters out the `value: 0` option. In `GameSetup.jsx`, `difficulty` defaults to `1` (Easy) when `gameType === 'trivia'`.

## 8. Reconnection

When a player disconnects and reconnects mid-game (handled in the `room:register` event):

1. The server detects `state.game_type == "trivia"` for the room.
2. It emits `game:turn_start` with `describer_id: -1` **to the reconnecting socket only** -- this triggers the frontend to navigate to `/trivia`.
3. If a question is currently in progress (`current_question_index < len(trivia_questions)`), the server also emits `trivia:question` with the current question data to the reconnecting socket.
4. The reconnecting player joins mid-question and can still answer if the timer hasn't expired.

The standard 60-second disconnect grace period applies (same as Charades/Scribble). If the player doesn't reconnect within 60 seconds, they are removed from the game via `game:player_removed`.

### Server restart recovery

On server startup, `restore_game_states()` deserializes all persisted `RoomState` records. For trivia games, `schedule_restored_states()` calls `_trivia_send_question()` to re-emit the current question and restart its timer.

## 9. Known Limitations

- **Only "Mental Math" category**: The question generator (`trivia.py`) only produces arithmetic problems. There is no database of trivia questions or support for other categories yet.
- **Mixed difficulty hidden**: Although the backend supports `difficulty=0` (mixed: 20% easy, 50% medium, 30% hard), the frontend hides this option for trivia. It could be re-enabled.
- **Rounds capped at 5**: Each round has 10 questions, so a maximum game is 50 questions. This cap is enforced in the frontend sliders only.
- **No chat during trivia**: The trivia UI does not include a chat panel -- there is no guessing mechanic that requires it.
- **No question deduplication across rounds**: Each round generates a fresh batch of 10 random questions independently. The same question could theoretically appear in multiple rounds.
- **Client-side timer drift**: The countdown timer in `TriviaGame.jsx` is based on `Date.now()` from when the `trivia:question` event is received, not on a server timestamp. Network latency could cause slight discrepancies between what the player sees and when the server actually resolves the question.
- **Future expansion**: The architecture is designed to support additional trivia categories. The `generate_question()` function could be extended or replaced with a database-backed question pool for categories like history, science, pop culture, etc.
