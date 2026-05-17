"""Matchmaker service — queue mechanics, pairing, bot fallback."""

import asyncio
import pytest

from app.services import matchmaker


@pytest.fixture(autouse=True)
def reset_matchmaker():
    matchmaker.QUEUES.clear()
    matchmaker.USER_IN_QUEUE.clear()
    yield
    matchmaker.QUEUES.clear()
    matchmaker.USER_IN_QUEUE.clear()


def test_queue_starts_empty():
    assert len(matchmaker.QUEUES) == 0
    assert len(matchmaker.USER_IN_QUEUE) == 0
