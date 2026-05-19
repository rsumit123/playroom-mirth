"""Bot worker for Quick Play trivia.

Bots are real User rows. This module:
  - decides per-question accuracy + timing
  - injects answers directly into RoomGameState.player_answers via the room lock
  - is invoked from _trivia_send_question for any room with a bot player
"""

import asyncio
import logging
import random
import time
from typing import Optional


_logger = logging.getLogger(__name__)


# Mean/sigma for the truncated-normal answer-delay distribution per difficulty.
# Tuned so that a confident human can usually beat the bot on speed bonus:
# bots answer mid-window, leaving room for fast humans to win the speed bonus.
_DELAY_PARAMS = {
    1: (5.0, 1.5),  # easy
    2: (7.0, 1.8),  # medium
    3: (8.5, 2.0),  # hard
}

# Target accuracy per difficulty for bot pre-decisions.
# Mixed quickmatch (20% easy / 50% medium / 30% hard) → expected ~36% correct.
_ACCURACY = {1: 0.50, 2: 0.40, 3: 0.20}

DELAY_FLOOR = 1.5
DELAY_CAP_ABS = 12.0
DELAY_CAP_FRACTION = 0.8


def pick_delay(difficulty: int, time_seconds: int) -> float:
    mean, sigma = _DELAY_PARAMS.get(difficulty, _DELAY_PARAMS[2])
    cap = min(DELAY_CAP_ABS, time_seconds * DELAY_CAP_FRACTION)
    while True:
        sample = random.gauss(mean, sigma)
        if DELAY_FLOOR <= sample <= cap:
            return sample
        # Resample if out of bounds.


def build_accuracy_slots(questions: list[dict]) -> list[bool]:
    """For each question, decide whether the bot will answer correctly.

    Each slot is a Bernoulli draw at the question's difficulty-tier accuracy.
    The resulting list is then shuffled to avoid positional patterns (e.g.,
    'wrong on every 5th question')."""
    slots = []
    for q in questions:
        target = _ACCURACY.get(q.get("difficulty", 2), 0.6)
        slots.append(random.random() < target)
    random.shuffle(slots)
    return slots


async def schedule_bot_answer(
    state,  # RoomGameState
    room_code: str,
    bot_player_id: int,
    will_answer_correctly: bool,
    on_all_answered,  # async callable() — runs after lock released if all players done
    max_delay_override: Optional[float] = None,
) -> asyncio.Task:
    """Pick a delay + answer, then submit the bot's answer to state.player_answers
    inside the room lock. Returns the spawned task (useful for tests / cancellation)."""

    q = state.trivia_questions[state.current_question_index]
    delay = max_delay_override if max_delay_override is not None else pick_delay(
        difficulty=q.get("difficulty", 2),
        time_seconds=q["time_seconds"],
    )

    if will_answer_correctly:
        answer_index = q["correct_index"]
    else:
        wrong = [i for i in range(len(q["options"])) if i != q["correct_index"]]
        answer_index = random.choice(wrong)

    async def _task():
        try:
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            return
        try:
            async with state.lock:
                # Race: question may have already resolved.
                if bot_player_id in state.player_answers:
                    return
                # Sanity: did the question advance under us?
                if (
                    state.trivia_questions
                    and state.current_question_index < len(state.trivia_questions)
                    and state.trivia_questions[state.current_question_index] is q
                ):
                    state.player_answers[bot_player_id] = {
                        "answer_index": answer_index,
                        "timestamp": time.time(),
                    }
                    all_answered = len(state.player_answers) >= len(state.player_order)
                else:
                    all_answered = False
            if all_answered:
                await on_all_answered()
        except Exception:
            _logger.exception("bot answer task failed for room %s", room_code)

    return asyncio.create_task(_task())


async def schedule_workers_for_room(state, room_code: str, sio, on_all_answered) -> None:
    """For a freshly-started or restored quickmatch room, spawn bot workers for
    each bot player and schedule their answer to the *current* question if one
    is in flight."""
    from app.db.session import SessionLocal
    from app.models.user import User
    from app.models.room_player import RoomPlayer

    if not state.trivia_questions:
        return
    if state.current_question_index >= len(state.trivia_questions):
        return

    with SessionLocal() as db:
        # Identify bot players in the room.
        rows = db.query(RoomPlayer, User).join(User, RoomPlayer.user_id == User.id) \
            .filter(RoomPlayer.room_id == state.room_id, User.is_bot == True).all()  # noqa: E712

    # Lazily build accuracy slots if absent (after restart we won't have them).
    if not hasattr(state, "_bot_accuracy_slots"):
        state._bot_accuracy_slots = build_accuracy_slots(state.trivia_questions)

    q_idx = state.current_question_index
    slot = state._bot_accuracy_slots[q_idx] if q_idx < len(state._bot_accuracy_slots) else False
    for rp, _user in rows:
        await schedule_bot_answer(
            state=state, room_code=room_code, bot_player_id=rp.id,
            will_answer_correctly=slot, on_all_answered=on_all_answered,
        )
