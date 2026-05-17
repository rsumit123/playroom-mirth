"""Trivia scoring and timing tests.

Drives the internal helpers (`_trivia_resolve_question`,
`_trivia_question_timeout`) directly so we can assert speed-bonus math,
wrong-answer scoring, and timeout behaviour without sleeping out a real timer.
"""

import asyncio
import time
import uuid

import pytest

from app.db.session import SessionLocal
from app.models.user import User
from app.services.auth import create_access_token
from app.services.game_state import ROOM_STATES, SID_TO_PLAYER
from app.sockets.events import (
    sio,
    _trivia_resolve_question,
    _trivia_question_timeout,
)


def _make_user(prefix: str) -> tuple[int, str]:
    db = SessionLocal()
    try:
        suffix = uuid.uuid4().hex[:8]
        u = User(email=f"{prefix}-{suffix}@x.com", google_id=f"g-{prefix}-{suffix}")
        db.add(u)
        db.commit()
        db.refresh(u)
        return u.id, create_access_token(str(u.id))
    finally:
        db.close()


async def _setup_started_trivia_room(turn_seconds=60):
    _, host_token = _make_user("score-host")
    _, guest_token = _make_user("score-guest")
    sid_host = await sio.manager.connect(f"eio-sh-{uuid.uuid4().hex[:6]}", "/")
    sid_guest = await sio.manager.connect(f"eio-sg-{uuid.uuid4().hex[:6]}", "/")

    create_res = await sio._trigger_event(
        "room:create", "/", sid_host,
        {
            "token": host_token, "rounds_total": 1, "difficulty": 1,
            "turn_seconds": turn_seconds, "max_players": 20,
            "game_type": "trivia", "trivia_category": "math",
        },
    )
    room_code = create_res["lobby"]["room"]["code"]
    await sio._trigger_event("room:join", "/", sid_guest,
                             {"room_code": room_code, "token": guest_token})
    await sio._trigger_event("game:start", "/", sid_host,
                             {"room_code": room_code, "token": host_token})
    return room_code, sid_host, sid_guest


# ── Scoring ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_correct_answer_gets_base_points_plus_speed_bonus():
    room_code, sid_host, _ = await _setup_started_trivia_room()
    state = ROOM_STATES[room_code]
    host_pid = SID_TO_PLAYER[sid_host]
    correct = state.trivia_questions[0]["correct_index"]

    # Fake an answer at t=0 (instant) — should yield max speed bonus
    state.question_start_ts = time.time()
    state.player_answers = {
        host_pid: {"answer_index": correct, "timestamp": state.question_start_ts},
    }
    async with state.lock:
        await _trivia_resolve_question(state, room_code)

    # Base 100 + ~100 speed bonus when time_taken ≈ 0
    assert state.scores[host_pid] >= 195
    assert state.scores[host_pid] <= 200


@pytest.mark.asyncio
async def test_slower_correct_answer_gets_smaller_bonus():
    room_code, sid_host, sid_guest = await _setup_started_trivia_room()
    state = ROOM_STATES[room_code]
    host_pid = SID_TO_PLAYER[sid_host]
    guest_pid = SID_TO_PLAYER[sid_guest]
    correct = state.trivia_questions[0]["correct_index"]

    # Host answers instantly, guest answers at half the time window
    state.question_start_ts = time.time()
    half = state.question_time_seconds / 2
    state.player_answers = {
        host_pid: {"answer_index": correct, "timestamp": state.question_start_ts},
        guest_pid: {"answer_index": correct, "timestamp": state.question_start_ts + half},
    }
    async with state.lock:
        await _trivia_resolve_question(state, room_code)

    assert state.scores[host_pid] > state.scores[guest_pid]
    # Both should be non-zero (both correct)
    assert state.scores[guest_pid] > 0


@pytest.mark.asyncio
async def test_wrong_answer_gets_zero_points():
    room_code, sid_host, _ = await _setup_started_trivia_room()
    state = ROOM_STATES[room_code]
    host_pid = SID_TO_PLAYER[sid_host]
    correct = state.trivia_questions[0]["correct_index"]
    wrong = (correct + 1) % len(state.trivia_questions[0]["options"])

    state.question_start_ts = time.time()
    state.player_answers = {
        host_pid: {"answer_index": wrong, "timestamp": state.question_start_ts},
    }
    async with state.lock:
        await _trivia_resolve_question(state, room_code)

    assert state.scores.get(host_pid, 0) == 0


@pytest.mark.asyncio
async def test_unanswered_player_gets_zero_points():
    """Player who never submitted any answer should not gain points."""
    room_code, sid_host, sid_guest = await _setup_started_trivia_room()
    state = ROOM_STATES[room_code]
    host_pid = SID_TO_PLAYER[sid_host]
    guest_pid = SID_TO_PLAYER[sid_guest]
    correct = state.trivia_questions[0]["correct_index"]

    state.question_start_ts = time.time()
    # Only host answers
    state.player_answers = {
        host_pid: {"answer_index": correct, "timestamp": state.question_start_ts},
    }
    async with state.lock:
        await _trivia_resolve_question(state, room_code)

    assert state.scores[host_pid] > 0
    assert state.scores.get(guest_pid, 0) == 0


# ── Timeout ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_question_timeout_resolves_with_no_answers():
    """If the per-question timer fires with no answers, the question should
    still resolve cleanly and award zero points to all players."""
    room_code, sid_host, sid_guest = await _setup_started_trivia_room()
    state = ROOM_STATES[room_code]
    host_pid = SID_TO_PLAYER[sid_host]
    guest_pid = SID_TO_PLAYER[sid_guest]

    state.player_answers = {}
    # Drive the timeout helper directly — no real sleep needed
    await _trivia_question_timeout(room_code)

    assert state.scores.get(host_pid, 0) == 0
    assert state.scores.get(guest_pid, 0) == 0


@pytest.mark.asyncio
async def test_question_timeout_no_op_for_missing_room():
    """Timeout firing for a popped room should silently no-op."""
    # Should not raise
    await _trivia_question_timeout("DOES-NOT-EXIST")
