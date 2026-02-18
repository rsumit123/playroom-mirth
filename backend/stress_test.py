"""
Multiplayer stress test for Charade Chat.

Simulates N concurrent players (Socket.IO + REST) going through a full game
of Charades or Scribble, then validates event consistency, scores, and turn order.

Usage:
    # Against local backend
    .venv/bin/python stress_test.py --url http://localhost:8000 --players 5 --game-type charades

    # Against production
    .venv/bin/python stress_test.py --url https://charade-api.skdev.one --players 5 --game-type scribble

    # Verbose mode with custom config
    .venv/bin/python stress_test.py --url https://charade-api.skdev.one --players 8 --rounds 3 -v
"""

import asyncio
import argparse
import logging
import random
import ssl
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

import aiohttp
import httpx
import socketio

log = logging.getLogger("stress_test")


# ─── PlayerBot ────────────────────────────────────────────────────────────────

@dataclass
class PlayerBot:
    index: int
    display_name: str
    is_host: bool = False

    # identity
    guest_token: Optional[str] = None
    player_id: Optional[int] = None
    room_code: Optional[str] = None

    # connections
    sio: Optional[socketio.AsyncClient] = None
    http: Optional[httpx.AsyncClient] = None

    # event logs
    turn_starts: list = field(default_factory=list)
    correct_guesses: list = field(default_factory=list)
    round_ends: list = field(default_factory=list)
    game_end_data: Optional[dict] = None
    words: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    # sync primitives (assigned in setup_events)
    turn_start_ev: asyncio.Event = field(default_factory=asyncio.Event)
    new_word_ev: asyncio.Event = field(default_factory=asyncio.Event)
    round_end_ev: asyncio.Event = field(default_factory=asyncio.Event)
    game_end_ev: asyncio.Event = field(default_factory=asyncio.Event)

    # live state
    current_turn: Optional[dict] = None
    current_word: Optional[str] = None


def setup_events(bot: PlayerBot):
    """Register Socket.IO event handlers on bot.sio."""
    sio = bot.sio

    @sio.on("room:lobby_update")
    async def _lobby(data):
        pass

    @sio.on("game:turn_start")
    async def _turn(data):
        bot.turn_starts.append(data)
        bot.current_turn = data
        bot.current_word = None
        bot.new_word_ev.clear()
        bot.turn_start_ev.set()

    @sio.on("game:new_word")
    async def _word(data):
        bot.current_word = data["word"]
        bot.words.append(data["word"])
        bot.new_word_ev.set()

    @sio.on("chat:message")
    async def _chat(data):
        pass

    @sio.on("game:correct_guess")
    async def _correct(data):
        bot.correct_guesses.append(data)

    @sio.on("game:round_end")
    async def _rend(data):
        bot.round_ends.append(data)
        bot.round_end_ev.set()

    @sio.on("game:game_end")
    async def _gend(data):
        bot.game_end_data = data
        bot.game_end_ev.set()

    @sio.on("error")
    async def _err(data):
        bot.errors.append(data)
        log.warning(f"[{bot.display_name}] error event: {data}")

    @sio.on("scribble:draw")
    async def _draw(data):
        pass

    @sio.on("scribble:clear")
    async def _clear(*a):
        pass

    @sio.on("game:reconnect_grace")
    async def _grace(data):
        pass

    @sio.on("game:player_removed")
    async def _removed(data):
        pass


# ─── GameCoordinator ──────────────────────────────────────────────────────────

class GameCoordinator:
    def __init__(self, bots: list[PlayerBot], host: PlayerBot,
                 room_code: str, config):
        self.bots = bots
        self.host = host
        self.room_code = room_code
        self.config = config
        self.num_players = len(bots)

    # ── helpers ────────────────────────────────────────────────────────────

    async def _wait_all(self, predicate, label="condition", timeout=20):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if all(predicate(b) for b in self.bots):
                return
            await asyncio.sleep(0.05)
        stuck = [b.display_name for b in self.bots if not predicate(b)]
        raise TimeoutError(f"Timeout waiting for {label} on: {stuck}")

    def _bot_by_pid(self, pid: int) -> PlayerBot:
        for b in self.bots:
            if b.player_id == pid:
                return b
        raise ValueError(f"No bot with player_id={pid}")

    # ── main loop ─────────────────────────────────────────────────────────

    async def run(self):
        # Start game
        result = await self.host.sio.call(
            "game:start",
            {"room_code": self.room_code, "guest_token": self.host.guest_token},
            timeout=15,
        )
        if not result.get("ok"):
            raise RuntimeError(f"game:start failed: {result}")
        log.info("  Game started!")

        turn_number = 0
        for round_idx in range(self.config.rounds):
            for turn_idx in range(self.num_players):
                turn_number += 1
                await self._play_turn(round_idx, turn_idx, turn_number)

                # check game over
                if self.host.game_end_data:
                    return

            # after all turns in a round
            if self.host.game_end_data:
                return

            # expect round_end (if not the last round)
            if round_idx < self.config.rounds - 1:
                await self._wait_all(
                    lambda b, ri=round_idx: len(b.round_ends) > ri,
                    label=f"round_end #{round_idx+1}",
                    timeout=20,
                )
                log.info(f"  Round {round_idx+1} complete.")
                await asyncio.sleep(0.3)
                result = await self.host.sio.call(
                    "game:next_round",
                    {"room_code": self.room_code,
                     "guest_token": self.host.guest_token},
                    timeout=15,
                )
                if not result.get("ok"):
                    raise RuntimeError(f"game:next_round failed: {result}")

        # wait for game_end
        await self._wait_all(
            lambda b: b.game_end_data is not None,
            label="game_end",
            timeout=20,
        )
        log.info("  Game ended!")

    # ── single turn ───────────────────────────────────────────────────────

    async def _play_turn(self, round_idx, turn_idx, turn_number):
        # clear turn_start flags
        for b in self.bots:
            b.turn_start_ev.clear()

        # wait for all bots to receive this turn_start
        await self._wait_all(
            lambda b, tn=turn_number: len(b.turn_starts) >= tn,
            label=f"turn_start #{turn_number}",
            timeout=20,
        )

        turn_data = self.bots[0].turn_starts[-1]
        describer_id = turn_data["describer_id"]
        describer = self._bot_by_pid(describer_id)
        guessers = [b for b in self.bots if b.player_id != describer_id]

        # wait for describer to receive word
        try:
            await asyncio.wait_for(describer.new_word_ev.wait(), timeout=10)
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"[{describer.display_name}] never received game:new_word"
            )

        word = describer.current_word
        log.info(
            f"  [R{round_idx+1} T{turn_idx+1}/{self.num_players}] "
            f"{describer.display_name} → \"{word}\""
        )

        if self.config.game_type == "scribble":
            await self._scribble_turn(describer, guessers, word, round_idx, turn_idx)
        else:
            await self._charades_turn(describer, guessers, word, round_idx, turn_idx)

    # ── charades turn ─────────────────────────────────────────────────────

    async def _charades_turn(self, describer, guessers, word, round_idx, turn_idx):
        # describer sends a hint (must not overlap with any target word)
        await describer.sio.emit("chat:message", {
            "room_code": self.room_code, "message": "hmm hmm hmm"
        })
        await asyncio.sleep(0.3)

        # first guesser sends wrong guesses then the correct word
        guesser = guessers[0]
        for wrong in ["wrongguess1", "wrongguess2"]:
            await guesser.sio.emit("chat:message", {
                "room_code": self.room_code, "message": wrong
            })
            await asyncio.sleep(0.2)

        # correct guess
        await guesser.sio.emit("chat:message", {
            "room_code": self.room_code, "message": word
        })
        await asyncio.sleep(0.3)

        # wait for correct_guess to arrive at all bots
        turn_guess_count = turn_idx + 1 + round_idx * self.num_players
        await self._wait_all(
            lambda b, c=turn_guess_count: len(b.correct_guesses) >= c,
            label="correct_guess",
            timeout=10,
        )
        log.info(f"    {guesser.display_name} guessed correctly (+10)")

        # force-advance turn (don't wait for timer)
        result = await self.host.sio.call(
            "game:turn_end", {"room_code": self.room_code}, timeout=15
        )
        await asyncio.sleep(0.2)

    # ── scribble turn ─────────────────────────────────────────────────────

    async def _scribble_turn(self, describer, guessers, word, round_idx, turn_idx):
        # drawer sends fake strokes
        for _ in range(3):
            await describer.sio.emit("scribble:draw", {
                "room_code": self.room_code,
                "points": [
                    {"x": random.randint(10, 400), "y": random.randint(10, 400)},
                    {"x": random.randint(10, 400), "y": random.randint(10, 400)},
                ],
                "color": "#000000",
                "width": 3,
            })
            await asyncio.sleep(0.15)

        # each guesser guesses at staggered times (scale delay with player count)
        stagger = min(0.3, 2.0 / max(len(guessers), 1))
        for i, guesser in enumerate(guessers):
            await asyncio.sleep(0.3 + stagger * i)
            # wrong guess
            await guesser.sio.emit("chat:message", {
                "room_code": self.room_code, "message": "wrongguess"
            })
            await asyncio.sleep(0.15)
            # correct guess
            await guesser.sio.emit("chat:message", {
                "room_code": self.room_code, "message": word
            })
            log.info(f"    {guesser.display_name} guessed correctly")

        # turn auto-advances when all guessed; give server time to process
        await asyncio.sleep(0.5)


# ─── Validation ───────────────────────────────────────────────────────────────

def validate(bots: list[PlayerBot], config) -> list[str]:
    failures = []
    num_players = len(bots)
    expected_turns = num_players * config.rounds

    # 1. Turn count
    for bot in bots:
        actual = len(bot.turn_starts)
        if actual != expected_turns:
            failures.append(
                f"[{bot.display_name}] turn_start count: "
                f"expected {expected_turns}, got {actual}"
            )

    # 2. Describer rotation
    describer_counts: dict[int, int] = {}
    ref = bots[0]
    for ts in ref.turn_starts:
        did = ts["describer_id"]
        describer_counts[did] = describer_counts.get(did, 0) + 1
    for bot in bots:
        count = describer_counts.get(bot.player_id, 0)
        if count != config.rounds:
            failures.append(
                f"[{bot.display_name}] was describer {count} times, "
                f"expected {config.rounds}"
            )

    # 3. Score consistency
    final_scores = set()
    for bot in bots:
        if bot.game_end_data:
            scores = bot.game_end_data.get("scores", {})
            normalized = tuple(sorted((str(k), v) for k, v in scores.items()))
            final_scores.add(normalized)
    if len(final_scores) > 1:
        failures.append(f"Score inconsistency across players: {final_scores}")

    # 4. Round end count
    expected_rends = max(config.rounds - 1, 0)
    for bot in bots:
        actual = len(bot.round_ends)
        if actual != expected_rends:
            failures.append(
                f"[{bot.display_name}] round_end count: "
                f"expected {expected_rends}, got {actual}"
            )

    # 5. Game end received
    for bot in bots:
        if bot.game_end_data is None:
            failures.append(f"[{bot.display_name}] never received game_end")

    # 6. No unexpected errors (HINT_BLOCKED is expected for describer hints)
    for bot in bots:
        real_errors = [e for e in bot.errors if e.get("code") != "HINT_BLOCKED"]
        if real_errors:
            failures.append(
                f"[{bot.display_name}] received {len(real_errors)} error(s): "
                f"{real_errors}"
            )

    # 7. Non-negative scores
    if bots[0].game_end_data:
        for pid, score in bots[0].game_end_data.get("scores", {}).items():
            if score < 0:
                failures.append(f"Player {pid} has negative score: {score}")

    return failures


# ─── Main ─────────────────────────────────────────────────────────────────────

async def run(config):
    t0 = time.time()

    # Create bots
    bots = []
    for i in range(config.players):
        bot = PlayerBot(
            index=i,
            display_name=f"StressBot_{i+1}",
            is_host=(i == 0),
            http=httpx.AsyncClient(timeout=15.0),
        )
        bots.append(bot)
    host = bots[0]

    try:
        # Phase 1: Create guest accounts
        print(f"[Phase 1] Creating {config.players} guest accounts...")
        t = time.time()
        for bot in bots:
            resp = await bot.http.post(
                f"{config.url}/guest",
                json={"display_name": bot.display_name},
            )
            resp.raise_for_status()
            data = resp.json()
            bot.guest_token = data["guest_token"]
        print(f"  Done ({time.time()-t:.2f}s)")

        # Phase 2: Create room + join
        print(f"[Phase 2] Creating room and joining players...")
        t = time.time()
        resp = await host.http.post(
            f"{config.url}/rooms/guest",
            json={
                "guest_token": host.guest_token,
                "rounds_total": config.rounds,
                "difficulty": config.difficulty,
                "turn_seconds": config.turn_seconds,
                "max_players": 20,
                "game_type": config.game_type,
            },
        )
        resp.raise_for_status()
        room_data = resp.json()
        room_code = room_data["room"]["code"]
        host.room_code = room_code
        host.player_id = room_data["self_player_id"]

        for bot in bots[1:]:
            resp = await bot.http.post(
                f"{config.url}/rooms/join",
                json={"room_code": room_code, "guest_token": bot.guest_token},
            )
            resp.raise_for_status()
            data = resp.json()
            bot.room_code = room_code
            bot.player_id = data["self_player_id"]

        print(f"  Room {room_code} ready with {config.players} players ({time.time()-t:.2f}s)")

        # Phase 3: Connect sockets + register
        print(f"[Phase 3] Connecting sockets and registering...")
        t = time.time()

        # SSL context for aiohttp (needed for wss:// connections)
        ssl_ctx = None
        if config.url.startswith("https"):
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE

        async def connect_bot(bot):
            http_session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=ssl_ctx)
            ) if ssl_ctx else None
            bot.sio = socketio.AsyncClient(
                logger=False, engineio_logger=False,
                http_session=http_session,
            )
            setup_events(bot)
            await bot.sio.connect(
                config.url,
                socketio_path="/socket.io",
                transports=["websocket"],
            )
            result = await bot.sio.call(
                "room:register",
                {"room_code": bot.room_code, "guest_token": bot.guest_token},
                timeout=15,
            )
            if not result.get("ok"):
                raise RuntimeError(
                    f"room:register failed for {bot.display_name}: {result}"
                )

        await asyncio.gather(*[connect_bot(b) for b in bots])
        print(f"  All sockets connected ({time.time()-t:.2f}s)")

        # Phase 4: Play game
        game_label = config.game_type.title()
        print(
            f"[Phase 4] Playing {game_label} "
            f"({config.rounds} rounds, {config.players} players)..."
        )
        t = time.time()
        coordinator = GameCoordinator(bots, host, room_code, config)
        await asyncio.wait_for(coordinator.run(), timeout=config.timeout)
        game_duration = time.time() - t
        print(f"  Game completed ({game_duration:.2f}s)")

        # Phase 5: Validate
        print(f"[Phase 5] Validating results...")
        failures = validate(bots, config)

        total_time = time.time() - t0
        print()
        print("=" * 60)
        print("STRESS TEST RESULTS")
        print("=" * 60)
        print(f"  Game type:    {config.game_type}")
        print(f"  Players:      {config.players}")
        print(f"  Rounds:       {config.rounds}")
        print(f"  Turn seconds: {config.turn_seconds}")
        print(f"  Game time:    {game_duration:.2f}s")
        print(f"  Total time:   {total_time:.2f}s")
        print("=" * 60)

        if failures:
            print(f"\nFAILED ({len(failures)} issue(s)):")
            for f in failures:
                print(f"  FAIL: {f}")
            sys.exit(1)
        else:
            print(f"\nPASSED — All 7 checks passed!")
            if bots[0].game_end_data:
                scores = bots[0].game_end_data.get("scores", {})
                pid_to_name = {b.player_id: b.display_name for b in bots}
                print("\nFinal Scores:")
                for pid, score in sorted(
                    scores.items(), key=lambda x: x[1], reverse=True
                ):
                    name = pid_to_name.get(
                        int(pid) if isinstance(pid, str) else pid,
                        f"Player {pid}",
                    )
                    print(f"  {name}: {score}")

    finally:
        for bot in bots:
            if bot.sio:
                if bot.sio.connected:
                    await bot.sio.disconnect()
                # Close aiohttp sessions to avoid warnings
                try:
                    eio = bot.sio.eio
                    if hasattr(eio, 'http') and hasattr(eio.http, '_session'):
                        s = eio.http._session
                        if s and not s.closed:
                            await s.close()
                    if hasattr(eio, 'http_session'):
                        s = eio.http_session
                        if s and not s.closed:
                            await s.close()
                except Exception:
                    pass
            if bot.http:
                await bot.http.aclose()
        await asyncio.sleep(0.1)  # let event loop clean up


def main():
    parser = argparse.ArgumentParser(
        description="Multiplayer stress test for Charade Chat"
    )
    parser.add_argument("--url", default="http://localhost:8000",
                        help="API base URL")
    parser.add_argument("--players", type=int, default=5,
                        help="Number of players (2-10)")
    parser.add_argument("--rounds", type=int, default=2,
                        help="Number of rounds")
    parser.add_argument("--turn-seconds", type=int, default=60,
                        help="Turn duration in seconds")
    parser.add_argument("--game-type", choices=["charades", "scribble"],
                        default="charades", help="Game type")
    parser.add_argument("--difficulty", type=int, default=1,
                        help="Word difficulty (0=mixed, 1=easy, 2=med, 3=hard)")
    parser.add_argument("--timeout", type=int, default=300,
                        help="Overall timeout in seconds")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable debug logging")
    config = parser.parse_args()

    if config.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    asyncio.run(run(config))


if __name__ == "__main__":
    main()
