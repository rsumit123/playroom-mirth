"""Tests for scribble word choice, charades skip word, and message clearing."""
import asyncio
import pytest

from app.db.session import SessionLocal
from app.models.user import User
from app.models.word import Word
from app.services.auth import create_access_token
from app.sockets.events import sio
from app.services.game_state import ROOM_STATES, SID_TO_PLAYER, PLAYER_TO_SID


def _setup(prefix, word_texts, game_type="charades"):
    db = SessionLocal()
    try:
        host = User(email=f"{prefix}-host@x.com", google_id=f"google-{prefix}-host")
        guest = User(email=f"{prefix}-guest@x.com", google_id=f"google-{prefix}-guest")
        db.add(host)
        db.add(guest)
        for text in word_texts:
            db.add(Word(text=text, difficulty=1, active=True, game_type=game_type))
        db.commit()
        db.refresh(host)
        db.refresh(guest)
        return create_access_token(str(host.id)), create_access_token(str(guest.id))
    finally:
        db.close()


async def _start_game(host_token, guest_token, prefix, game_type="charades", turn_seconds=60):
    sid_host = await sio.manager.connect(f"eio-{prefix}-host", "/")
    create_res = await sio._trigger_event(
        "room:create", "/", sid_host,
        {"token": host_token, "rounds_total": 1, "difficulty": 1, "turn_seconds": turn_seconds,
         "max_players": 20, "game_type": game_type},
    )
    room_code = create_res["lobby"]["room"]["code"]

    sid_guest = await sio.manager.connect(f"eio-{prefix}-guest", "/")
    await sio._trigger_event("room:join", "/", sid_guest, {"room_code": room_code, "token": guest_token})
    await sio._trigger_event("game:start", "/", sid_host, {"room_code": room_code, "token": host_token})

    return room_code, sid_host, sid_guest


# ── Scribble Word Choice Tests ──────────────────────────────────────

@pytest.mark.asyncio
async def test_scribble_word_choices_sent_to_drawer():
    """In scribble, the drawer should receive word choices, not a direct word."""
    ht, gt = _setup("wc1", ["apple", "banana", "cherry", "date"], "scribble")
    room_code, sid_host, sid_guest = await _start_game(ht, gt, "wc1", "scribble")

    state = ROOM_STATES[room_code]
    assert state.game_type == "scribble"
    # Word choices should be stored on state
    choices = getattr(state, '_word_choices', {})
    assert len(choices) >= 1, f"Expected word choices, got {choices}. game_type={state.game_type}, current_word={state.current_word_text}"
    # current_word_text should be None (not yet picked)
    assert state.current_word_text is None


@pytest.mark.asyncio
async def test_scribble_word_pick_sets_word():
    """Picking a word should set it as the current word."""
    ht, gt = _setup("wc2", ["egg", "fig", "grape", "kiwi"], "scribble")
    room_code, sid_host, sid_guest = await _start_game(ht, gt, "wc2", "scribble")

    state = ROOM_STATES[room_code]
    choices = getattr(state, '_word_choices', {})
    assert len(choices) > 0

    describer_id = state.player_order[state.describer_index]
    describer_sid = PLAYER_TO_SID[describer_id]
    picked_word = list(choices.keys())[0]

    res = await sio._trigger_event("game:word_pick", "/", describer_sid, {
        "room_code": room_code, "word": picked_word,
    })
    assert res["ok"] is True
    assert state.current_word_text == picked_word
    assert getattr(state, '_word_choices', {}) == {}  # choices cleared


@pytest.mark.asyncio
async def test_scribble_word_pick_by_non_drawer_rejected():
    """Non-drawer cannot pick a word."""
    ht, gt = _setup("wc3", ["lemon", "mango", "nectarine", "olive"], "scribble")
    room_code, sid_host, sid_guest = await _start_game(ht, gt, "wc3", "scribble")

    state = ROOM_STATES[room_code]
    choices = getattr(state, '_word_choices', {})
    describer_id = state.player_order[state.describer_index]
    non_drawer_id = [p for p in state.player_order if p != describer_id][0]
    non_drawer_sid = PLAYER_TO_SID[non_drawer_id]

    res = await sio._trigger_event("game:word_pick", "/", non_drawer_sid, {
        "room_code": room_code, "word": list(choices.keys())[0],
    })
    assert res["ok"] is False


@pytest.mark.asyncio
async def test_scribble_word_pick_invalid_word_rejected():
    """Picking a word not in the choices should fail."""
    ht, gt = _setup("wc4", ["peach", "plum", "quince", "raisin"], "scribble")
    room_code, sid_host, sid_guest = await _start_game(ht, gt, "wc4", "scribble")

    state = ROOM_STATES[room_code]
    describer_sid = PLAYER_TO_SID[state.player_order[state.describer_index]]

    res = await sio._trigger_event("game:word_pick", "/", describer_sid, {
        "room_code": room_code, "word": "notachoice",
    })
    assert res["ok"] is False


# ── Charades Skip Word Tests ────────────────────────────────────────

@pytest.mark.asyncio
async def test_skip_word_gives_new_word():
    """Skipping should change the current word."""
    ht, gt = _setup("skip1", ["alpha", "beta", "gamma", "delta"])
    room_code, sid_host, sid_guest = await _start_game(ht, gt, "skip1")

    state = ROOM_STATES[room_code]
    old_word = state.current_word_text
    describer_sid = PLAYER_TO_SID[state.player_order[state.describer_index]]

    res = await sio._trigger_event("game:skip_word", "/", describer_sid, {"room_code": room_code})
    assert res["ok"] is True
    assert res["skips_remaining"] == 1
    assert state.current_word_text != old_word


@pytest.mark.asyncio
async def test_skip_word_max_2_per_turn():
    """Only 2 skips allowed per turn."""
    ht, gt = _setup("skip2", ["one", "two", "three", "four", "five"])
    room_code, sid_host, sid_guest = await _start_game(ht, gt, "skip2")

    state = ROOM_STATES[room_code]
    describer_sid = PLAYER_TO_SID[state.player_order[state.describer_index]]

    res1 = await sio._trigger_event("game:skip_word", "/", describer_sid, {"room_code": room_code})
    assert res1["ok"] is True and res1["skips_remaining"] == 1

    res2 = await sio._trigger_event("game:skip_word", "/", describer_sid, {"room_code": room_code})
    assert res2["ok"] is True and res2["skips_remaining"] == 0

    res3 = await sio._trigger_event("game:skip_word", "/", describer_sid, {"room_code": room_code})
    assert res3["ok"] is False
    assert res3["error"] == "SKIP_LIMIT"


@pytest.mark.asyncio
async def test_skip_word_only_describer():
    """Non-describer cannot skip."""
    ht, gt = _setup("skip3", ["red", "blue", "green", "yellow"])
    room_code, sid_host, sid_guest = await _start_game(ht, gt, "skip3")

    state = ROOM_STATES[room_code]
    describer_id = state.player_order[state.describer_index]
    non_describer_id = [p for p in state.player_order if p != describer_id][0]
    non_describer_sid = PLAYER_TO_SID[non_describer_id]

    res = await sio._trigger_event("game:skip_word", "/", non_describer_sid, {"room_code": room_code})
    assert res["ok"] is False


@pytest.mark.asyncio
async def test_skip_word_only_charades():
    """Skip is only available in charades, not scribble."""
    ht, gt = _setup("skip4", ["cat", "dog", "bird", "fish"], "scribble")
    room_code, sid_host, sid_guest = await _start_game(ht, gt, "skip4", "scribble")

    state = ROOM_STATES[room_code]
    describer_sid = PLAYER_TO_SID[state.player_order[state.describer_index]]

    # Need to pick a word first in scribble
    choices = getattr(state, '_word_choices', {})
    if choices:
        await sio._trigger_event("game:word_pick", "/", describer_sid, {
            "room_code": room_code, "word": list(choices.keys())[0],
        })

    res = await sio._trigger_event("game:skip_word", "/", describer_sid, {"room_code": room_code})
    assert res["ok"] is False
    assert "charades" in res.get("error", "").lower()


@pytest.mark.asyncio
async def test_skip_resets_on_new_turn():
    """Skip count should reset when a new turn starts."""
    ht, gt = _setup("skip5", ["sun", "moon", "star", "cloud", "rain"], game_type="charades")
    room_code, sid_host, sid_guest = await _start_game(ht, gt, "skip5", turn_seconds=1)

    state = ROOM_STATES[room_code]
    describer_sid = PLAYER_TO_SID[state.player_order[state.describer_index]]

    # Use both skips
    await sio._trigger_event("game:skip_word", "/", describer_sid, {"room_code": room_code})
    await sio._trigger_event("game:skip_word", "/", describer_sid, {"room_code": room_code})

    # Wait for turn to advance
    await asyncio.sleep(1.5)

    # New describer should have fresh skip count
    state = ROOM_STATES.get(room_code)
    if state:
        assert state._skips_this_turn == 0
