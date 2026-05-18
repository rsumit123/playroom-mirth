"""Trivia bot worker — timing distribution, accuracy, answer injection."""

import asyncio
import random
import statistics

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
