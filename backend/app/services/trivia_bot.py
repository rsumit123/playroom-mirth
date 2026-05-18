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
_DELAY_PARAMS = {
    1: (2.5, 1.0),  # easy
    2: (4.0, 1.2),  # medium
    3: (5.0, 1.5),  # hard
}

# Target accuracy per difficulty for bot pre-decisions.
_ACCURACY = {1: 0.80, 2: 0.60, 3: 0.40}

DELAY_FLOOR = 1.5
DELAY_CAP_ABS = 8.0
DELAY_CAP_FRACTION = 0.7


def pick_delay(difficulty: int, time_seconds: int) -> float:
    mean, sigma = _DELAY_PARAMS.get(difficulty, _DELAY_PARAMS[2])
    cap = min(DELAY_CAP_ABS, time_seconds * DELAY_CAP_FRACTION)
    while True:
        sample = random.gauss(mean, sigma)
        if DELAY_FLOOR <= sample <= cap:
            return sample
        # Resample if out of bounds.
