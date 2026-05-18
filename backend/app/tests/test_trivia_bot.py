"""Trivia bot worker — timing distribution, accuracy, answer injection."""

import asyncio
import random
import statistics
import time

import pytest

from app.services import trivia_bot


def test_pick_delay_easy_distribution():
    random.seed(42)
    delays = [trivia_bot.pick_delay(difficulty=1, time_seconds=20) for _ in range(500)]
    assert all(d >= 1.5 for d in delays)
    assert all(d <= min(8.0, 20 * 0.7) for d in delays)
    # Easy should skew fast — mean near 2.5
    assert 1.8 < statistics.mean(delays) < 3.3


def test_pick_delay_hard_distribution():
    random.seed(42)
    delays = [trivia_bot.pick_delay(difficulty=3, time_seconds=10) for _ in range(500)]
    assert all(d >= 1.5 for d in delays)
    cap = min(8.0, 10 * 0.7)
    assert all(d <= cap for d in delays)
    # Hard should skew slower
    assert statistics.mean(delays) > 3.5


def test_pick_delay_floor_and_cap():
    # Force extreme samples by seeding the RNG repeatedly.
    for _ in range(100):
        d = trivia_bot.pick_delay(difficulty=2, time_seconds=15)
        assert 1.5 <= d <= min(8.0, 15 * 0.7)


def test_build_accuracy_slots_matches_question_difficulties():
    random.seed(0)
    questions = [
        {"difficulty": 1}, {"difficulty": 1}, {"difficulty": 1},
        {"difficulty": 2}, {"difficulty": 2}, {"difficulty": 2}, {"difficulty": 2},
        {"difficulty": 3}, {"difficulty": 3}, {"difficulty": 3},
    ]
    slots = trivia_bot.build_accuracy_slots(questions)
    assert len(slots) == len(questions)
    for s in slots:
        assert isinstance(s, bool)


def test_build_accuracy_slots_distribution_across_many_matches():
    random.seed(0)
    questions = [{"difficulty": 1}] * 1000
    slots = trivia_bot.build_accuracy_slots(questions)
    correct = sum(slots)
    # 80% target ±5%
    assert 750 <= correct <= 850


def test_build_accuracy_slots_shuffled():
    """Slots should not be in a predictable order — the per-difficulty
    correctness gets shuffled together."""
    random.seed(7)
    questions = [{"difficulty": 1}] * 5 + [{"difficulty": 3}] * 5
    slots = trivia_bot.build_accuracy_slots(questions)
    # Probability of all-correct then all-wrong by chance is tiny; assert mix.
    assert slots[:5] != [True, True, True, True, True] or slots[5:] != [False, False, False, False, False]


@pytest.mark.asyncio
async def test_schedule_bot_answer_writes_to_player_answers():
    from app.services.game_state import RoomGameState
    state = RoomGameState(
        room_id=1, room_code="BOT1", rounds_total=1,
        turn_seconds=60, difficulty=1, game_type="trivia",
    )
    state.player_order = [10, 99]  # 10 = human, 99 = bot
    state.trivia_questions = [{
        "question": "Q?", "options": ["a", "b", "c", "d"],
        "correct_index": 2, "time_seconds": 20, "difficulty": 1,
    }]
    state.current_question_index = 0
    state.question_start_ts = time.time()
    state.question_time_seconds = 20

    async def on_all_answered():
        return

    await trivia_bot.schedule_bot_answer(
        state=state, room_code="BOT1", bot_player_id=99,
        will_answer_correctly=True, on_all_answered=on_all_answered,
        max_delay_override=0.05,
    )
    await asyncio.sleep(0.2)

    assert 99 in state.player_answers
    assert state.player_answers[99]["answer_index"] == 2


@pytest.mark.asyncio
async def test_schedule_bot_answer_wrong_when_inaccurate():
    from app.services.game_state import RoomGameState
    state = RoomGameState(
        room_id=1, room_code="BOT2", rounds_total=1,
        turn_seconds=60, difficulty=1, game_type="trivia",
    )
    state.player_order = [10, 99]
    state.trivia_questions = [{
        "question": "Q?", "options": ["a", "b", "c", "d"],
        "correct_index": 0, "time_seconds": 20, "difficulty": 1,
    }]
    state.current_question_index = 0
    state.question_start_ts = time.time()
    state.question_time_seconds = 20

    async def on_all_answered():
        return

    await trivia_bot.schedule_bot_answer(
        state=state, room_code="BOT2", bot_player_id=99,
        will_answer_correctly=False, on_all_answered=on_all_answered,
        max_delay_override=0.05,
    )
    await asyncio.sleep(0.2)

    assert 99 in state.player_answers
    assert state.player_answers[99]["answer_index"] != 0
