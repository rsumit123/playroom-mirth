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
