import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class RoomGameState:
    room_id: int
    room_code: str
    rounds_total: int
    turn_seconds: int
    difficulty: int
    game_type: str = "charades"
    status: str = "active"
    round_index: int = 1
    describer_index: int = 0
    turn_start_ts: float = 0.0
    player_order: List[int] = field(default_factory=list)  # room_player ids in order
    scores: Dict[int, int] = field(default_factory=dict)
    current_word_id: Optional[int] = None
    current_word_text: Optional[str] = None
    word_history_ids: List[int] = field(default_factory=list)
    guessed_players: Set[int] = field(default_factory=set)
    # Trivia-specific fields
    trivia_questions: List[dict] = field(default_factory=list)
    current_question_index: int = 0
    player_answers: Dict[int, dict] = field(default_factory=dict)
    question_start_ts: float = 0.0
    question_time_seconds: int = 0
    trivia_category: str = "math"
    used_question_ids: Set[str] = field(default_factory=set)
    origin: str = "friends"
    strokes: List[dict] = field(default_factory=list)  # scribble stroke buffer (in-memory only, not persisted)
    # Poker: one hand at a time, serialized, with the revision and the clocks
    # that go with it. See services/poker.py.
    poker: Optional[dict] = None
    poker_names: Dict[int, str] = field(default_factory=dict)
    # seat id -> AI tier, for the seats a model is sitting in, and what those
    # models have noticed about everyone at the table so far.
    poker_seats: Dict[int, str] = field(default_factory=dict)
    poker_reads: Dict[int, dict] = field(default_factory=dict)
    task: Optional[asyncio.Task] = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    # Quickmatch pause-on-disconnect: when a human disconnects in the middle of
    # a 2-player game, we pause question advancement + bot answers until they
    # reconnect (or the 60s grace fires and the game ends).
    paused: bool = False
    bot_answer_tasks: List[asyncio.Task] = field(default_factory=list)


ROOM_STATES: Dict[str, RoomGameState] = {}
SID_TO_PLAYER: Dict[str, int] = {}
PLAYER_TO_SID: Dict[int, str] = {}
PLAYER_TO_ROOM: Dict[int, str] = {}
PLAYER_GRACE_TASKS: Dict[int, asyncio.Task] = {}

# Presence tracking: user_id -> set of socket SIDs (multi-tab support)
USER_ONLINE: Dict[int, set] = {}


def start_turn(state: RoomGameState) -> None:
    state.turn_start_ts = time.time()
    state.guessed_players = set()
    state.strokes = []
    state._skips_this_turn = 0


def serialize_state(state: RoomGameState) -> str:
    payload = {
        "room_id": state.room_id,
        "room_code": state.room_code,
        "rounds_total": state.rounds_total,
        "turn_seconds": state.turn_seconds,
        "difficulty": state.difficulty,
        "game_type": state.game_type,
        "status": state.status,
        "round_index": state.round_index,
        "describer_index": state.describer_index,
        "turn_start_ts": state.turn_start_ts,
        "player_order": state.player_order,
        "scores": state.scores,
        "current_word_id": state.current_word_id,
        "current_word_text": state.current_word_text,
        "word_history_ids": state.word_history_ids,
        "guessed_players": list(state.guessed_players),
        "trivia_questions": state.trivia_questions,
        "current_question_index": state.current_question_index,
        "player_answers": {str(k): v for k, v in state.player_answers.items()},
        "question_start_ts": state.question_start_ts,
        "question_time_seconds": state.question_time_seconds,
        "trivia_category": state.trivia_category,
        "used_question_ids": list(state.used_question_ids),
        "origin": state.origin,
        "poker": state.poker,
        "poker_names": {str(k): v for k, v in state.poker_names.items()},
        "poker_seats": {str(k): v for k, v in state.poker_seats.items()},
        "poker_reads": {str(k): v for k, v in state.poker_reads.items()},
    }
    return json.dumps(payload)


def deserialize_state(raw: str) -> RoomGameState:
    data = json.loads(raw)
    return RoomGameState(
        room_id=data["room_id"],
        room_code=data["room_code"],
        rounds_total=data["rounds_total"],
        turn_seconds=data["turn_seconds"],
        difficulty=data["difficulty"],
        game_type=data.get("game_type", "charades"),
        status=data.get("status", "active"),
        round_index=data.get("round_index", 1),
        describer_index=data.get("describer_index", 0),
        turn_start_ts=data.get("turn_start_ts", 0.0),
        player_order=data.get("player_order", []),
        scores={int(k): v for k, v in data.get("scores", {}).items()},
        current_word_id=data.get("current_word_id"),
        current_word_text=data.get("current_word_text"),
        word_history_ids=data.get("word_history_ids", []),
        guessed_players=set(data.get("guessed_players", [])),
        trivia_questions=data.get("trivia_questions", []),
        current_question_index=data.get("current_question_index", 0),
        player_answers={int(k): v for k, v in data.get("player_answers", {}).items()},
        question_start_ts=data.get("question_start_ts", 0.0),
        question_time_seconds=data.get("question_time_seconds", 0),
        trivia_category=data.get("trivia_category", "math"),
        used_question_ids=set(data.get("used_question_ids", [])),
        origin=data.get("origin", "friends"),
        poker=data.get("poker"),
        poker_names={int(k): v for k, v in data.get("poker_names", {}).items()},
        poker_seats={int(k): v for k, v in data.get("poker_seats", {}).items()},
        poker_reads={int(k): v for k, v in data.get("poker_reads", {}).items()},
    )


async def cancel_all_timers() -> None:
    tasks = []
    for state in ROOM_STATES.values():
        if state.task and not state.task.done():
            state.task.cancel()
            tasks.append(state.task)
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
