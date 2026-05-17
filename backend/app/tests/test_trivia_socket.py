"""Socket-event tests for trivia game flow.

Exercises room:create with game_type=trivia, game:start, trivia:answer (single,
duplicate, all-answered short-circuit, wrong-game-type rejection), and
used_question_ids accumulation across rounds. Uses sio._trigger_event so no
real network server is required.
"""

import asyncio
import time
import uuid

import pytest

from app.db.session import SessionLocal
from app.models.user import User
from app.models.word import Word
from app.services.auth import create_access_token
from app.services.game_state import ROOM_STATES, SID_TO_PLAYER
from app.sockets.events import sio


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


async def _connect_sid(label: str) -> str:
    return await sio.manager.connect(_unique(label), "/")


def _make_user(email_prefix: str) -> tuple[int, str]:
    db = SessionLocal()
    try:
        suffix = uuid.uuid4().hex[:8]
        u = User(email=f"{email_prefix}-{suffix}@example.com", google_id=f"google-{email_prefix}-{suffix}")
        db.add(u)
        db.commit()
        db.refresh(u)
        return u.id, create_access_token(str(u.id))
    finally:
        db.close()


async def _create_trivia_room(host_token: str, sid_host: str, *, category="math",
                              rounds_total=1, turn_seconds=60) -> str:
    res = await sio._trigger_event(
        "room:create", "/", sid_host,
        {
            "token": host_token,
            "rounds_total": rounds_total,
            "difficulty": 1,
            "turn_seconds": turn_seconds,
            "max_players": 20,
            "game_type": "trivia",
            "trivia_category": category,
        },
    )
    return res["lobby"]["room"]["code"]


async def _setup_two_player_trivia(category="math", rounds_total=1, turn_seconds=60):
    _, host_token = _make_user("trivia-host")
    _, guest_token = _make_user("trivia-guest")
    sid_host = await _connect_sid("eio-trh")
    sid_guest = await _connect_sid("eio-trg")
    room_code = await _create_trivia_room(
        host_token, sid_host,
        category=category, rounds_total=rounds_total, turn_seconds=turn_seconds,
    )
    await sio._trigger_event(
        "room:join", "/", sid_guest,
        {"room_code": room_code, "token": guest_token},
    )
    return room_code, sid_host, sid_guest, host_token, guest_token


# ── game:start populates trivia state ─────────────────────────────


@pytest.mark.asyncio
async def test_trivia_start_populates_questions_and_state():
    room_code, sid_host, _, host_token, _ = await _setup_two_player_trivia(category="math")
    res = await sio._trigger_event(
        "game:start", "/", sid_host, {"room_code": room_code, "token": host_token},
    )
    assert res["ok"] is True
    state = ROOM_STATES[room_code]
    assert state.game_type == "trivia"
    assert len(state.trivia_questions) == 10
    assert state.current_question_index == 0
    # First question's start timestamp should be populated
    assert state.question_start_ts > 0


@pytest.mark.asyncio
async def test_trivia_start_with_gk_category_records_used_ids():
    """Generated GK questions should populate used_question_ids so they don't repeat."""
    room_code, sid_host, _, host_token, _ = await _setup_two_player_trivia(category="science")
    await sio._trigger_event("game:start", "/", sid_host, {"room_code": room_code, "token": host_token})
    state = ROOM_STATES[room_code]
    # All 10 GK questions should have IDs tracked
    assert len(state.used_question_ids) == 10


@pytest.mark.asyncio
async def test_trivia_start_with_math_category_does_not_record_used_ids():
    """Math questions are generated, not pulled from a finite pool — no IDs to track."""
    room_code, sid_host, _, host_token, _ = await _setup_two_player_trivia(category="math")
    await sio._trigger_event("game:start", "/", sid_host, {"room_code": room_code, "token": host_token})
    state = ROOM_STATES[room_code]
    assert len(state.used_question_ids) == 0


# ── trivia:answer happy path ──────────────────────────────────────


@pytest.mark.asyncio
async def test_trivia_answer_records_player_answer():
    room_code, sid_host, sid_guest, host_token, _ = await _setup_two_player_trivia()
    await sio._trigger_event("game:start", "/", sid_host, {"room_code": room_code, "token": host_token})

    res = await sio._trigger_event(
        "trivia:answer", "/", sid_host, {"room_code": room_code, "answer_index": 2},
    )
    assert res["ok"] is True
    state = ROOM_STATES[room_code]
    host_player_id = SID_TO_PLAYER[sid_host]
    assert host_player_id in state.player_answers
    assert state.player_answers[host_player_id]["answer_index"] == 2


# ── trivia:answer rejections ──────────────────────────────────────


@pytest.mark.asyncio
async def test_trivia_answer_rejects_duplicate_from_same_player():
    room_code, sid_host, _, host_token, _ = await _setup_two_player_trivia()
    await sio._trigger_event("game:start", "/", sid_host, {"room_code": room_code, "token": host_token})

    first = await sio._trigger_event(
        "trivia:answer", "/", sid_host, {"room_code": room_code, "answer_index": 0},
    )
    second = await sio._trigger_event(
        "trivia:answer", "/", sid_host, {"room_code": room_code, "answer_index": 1},
    )
    assert first["ok"] is True
    assert second["ok"] is False
    assert second.get("error") == "ALREADY_ANSWERED"


@pytest.mark.asyncio
async def test_trivia_answer_requires_room_code_and_answer_index():
    room_code, sid_host, _, host_token, _ = await _setup_two_player_trivia()
    await sio._trigger_event("game:start", "/", sid_host, {"room_code": room_code, "token": host_token})

    res = await sio._trigger_event("trivia:answer", "/", sid_host, {"room_code": room_code})
    assert res["ok"] is False

    res = await sio._trigger_event("trivia:answer", "/", sid_host, {"answer_index": 0})
    assert res["ok"] is False


@pytest.mark.asyncio
async def test_trivia_answer_rejected_in_non_trivia_game():
    """trivia:answer should be a no-op for a charades game."""
    # Set up a charades room instead
    _, host_token = _make_user("ch-host")
    _, guest_token = _make_user("ch-guest")
    db = SessionLocal()
    try:
        db.add(Word(text="apple", difficulty=1, active=True))
        db.commit()
    finally:
        db.close()
    sid_host = await _connect_sid("eio-chh")
    sid_guest = await _connect_sid("eio-chg")
    create_res = await sio._trigger_event(
        "room:create", "/", sid_host,
        {
            "token": host_token, "rounds_total": 1, "difficulty": 1,
            "turn_seconds": 60, "max_players": 20, "game_type": "charades",
        },
    )
    room_code = create_res["lobby"]["room"]["code"]
    await sio._trigger_event("room:join", "/", sid_guest,
                             {"room_code": room_code, "token": guest_token})
    await sio._trigger_event("game:start", "/", sid_host,
                             {"room_code": room_code, "token": host_token})

    res = await sio._trigger_event(
        "trivia:answer", "/", sid_host, {"room_code": room_code, "answer_index": 0},
    )
    assert res["ok"] is False


@pytest.mark.asyncio
async def test_trivia_answer_rejects_unknown_player_sid():
    """A socket that isn't mapped to a player_id in the room cannot answer."""
    room_code, sid_host, _, host_token, _ = await _setup_two_player_trivia()
    await sio._trigger_event("game:start", "/", sid_host, {"room_code": room_code, "token": host_token})

    rogue_sid = await _connect_sid("eio-rogue")
    res = await sio._trigger_event(
        "trivia:answer", "/", rogue_sid, {"room_code": room_code, "answer_index": 0},
    )
    assert res["ok"] is False


# ── all-answered short-circuits the timer ────────────────────────


@pytest.mark.asyncio
async def test_all_answered_advances_to_next_question():
    """When every player answers, the timer is cancelled and the question
    resolves immediately. After the 4-second result pause, the next question
    is sent. We assert the immediate resolution side-effects."""
    room_code, sid_host, sid_guest, host_token, _ = await _setup_two_player_trivia()
    await sio._trigger_event("game:start", "/", sid_host, {"room_code": room_code, "token": host_token})

    state = ROOM_STATES[room_code]
    correct = state.trivia_questions[0]["correct_index"]
    initial_q_text = state.trivia_questions[0]["question"]

    await sio._trigger_event("trivia:answer", "/", sid_host,
                             {"room_code": room_code, "answer_index": correct})
    await sio._trigger_event("trivia:answer", "/", sid_guest,
                             {"room_code": room_code, "answer_index": correct})

    # Both correct → both should have non-zero scores after resolve
    assert sum(state.scores.values()) > 0
    host_pid = SID_TO_PLAYER[sid_host]
    guest_pid = SID_TO_PLAYER[sid_guest]
    assert state.scores.get(host_pid, 0) > 0
    assert state.scores.get(guest_pid, 0) > 0
    # Sanity: we're still on question 0 (advance happens after a 4s pause)
    assert state.trivia_questions[state.current_question_index]["question"] == initial_q_text
