# Porting Texas Hold'em into PlayRoom as a native game type

The poker game lives today as a separate product (`card_games`, live at
games.skdev.one: FastAPI + raw WebSocket + React/TS, with LLM house players).
This is the plan to make it a game type inside PlayRoom/Mirth, the way trivia
is, so that one account, one lobby, one friends list and one Android build
cover it.

`card_games` stays live and untouched throughout. We copy; we do not move.

## What carries over and what does not

| From `card_games` | Decision |
|---|---|
| `app/games/holdem/`, `app/games/cards.py` | Lift verbatim. No framework coupling. |
| `app/rooms/manager.py` (739 lines) | **Do not port.** Rewrite thin, at trivia's altitude, against `RoomGameState` + Socket.IO. |
| Revision counter + idempotency key | **Keep.** Both fixed real production bugs (stale acks, double submits). |
| Per-seat asyncio queues | Drop. Socket.IO + `PLAYER_TO_SID` do this. |
| `Hand` / `HandOutcome` tables | Drop. `game_history` at session end, one row per player. |
| `lifecycle.py`, `recovery.py` | Drop. Room status + `room_player` + timeout-fold already cover disconnects. |
| `app/ai/` + `rooms/reads.py` | Port under `services/poker_ai/`. Seat house players as bot users. |
| Frontend presentational components + `table.css` | Copy. |
| Zustand store, `ws/TableSocket.ts` | Drop. A `usePokerState` hook on AppContext's socket, like `TriviaGame`. |
| Reactions, spectators, sit-out, host transfer | Out of v1. PlayRoom has chat. |

## Decisions

- **Seats are keyed on `room_player.id`.** `start_hand` takes `{seat_id: stack}`
  with arbitrary ints, so no mapping layer, and it survives reconnects and works
  for guests.
- **State lives where trivia's lives**: a `poker` field on `RoomGameState`
  holding the serialized hand, and the room's existing `asyncio.Task` runs the
  action clock. Persisted through the same `room_state` JSON blob, which needs
  `HoldemState.to_dict()` / `from_dict()`.
- **Every state event is emitted per seat**, never to the room. A room broadcast
  leaks hole cards; there is a test that says so.
- **Two new room columns**, `starting_chips` and `small_blind` (big blind is
  2x). Seat count reuses `max_players`. Added as guarded `ALTER TABLE`s in
  `db/init_db.py`, the way `origin` was.
- **Poker costs money per hand** (~$0.006 against Gemini Flash). Tier gating
  caps it; `OPENROUTER_API_KEY` goes in the VM's compose env.

## Slices

Each lands on `feature/poker` under the CLAUDE.md protocol: backend pytest,
frontend build, vitest before every commit; Playwright for socket changes.

1. **Engine.** `services/holdem/` + evaluator + `to_dict`/`from_dict` + the
   ported engine tests. Nearly free, and nothing depends on it yet.
2. **Room shape.** `game_type="poker"`, the two columns, the GameSetup branch
   (seats, chips, blinds; no rounds/timer/difficulty).
3. **The game.** `services/poker.py` + `sockets/poker_events.py`: seating,
   dealing, acting, the action clock, per-seat emit. The big one.
4. **The table screen.** `/poker` route, Home card, the ported components, the
   412x839 capture harness that all the layout work was judged against.
5. **House players.** `services/poker_ai/` + opponent reads.
6. **Finish.** `game_history` rows (score = net chips), history labels, Android
   `versionCode 15`.

Merge to main when a full hand plays end to end: the VM deploys from main, so a
half-ported game there is a broken production.
