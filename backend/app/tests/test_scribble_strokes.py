"""Tests for scribble stroke relay: eraser flag, colors, stroke accumulation, and clear."""
import asyncio
import pytest

from app.db.session import SessionLocal
from app.models.user import User
from app.models.word import Word
from app.services.auth import create_access_token
from app.sockets.events import sio
from app.services.game_state import ROOM_STATES, SID_TO_PLAYER, PLAYER_TO_SID


def _setup(prefix, word="canvas"):
    db = SessionLocal()
    try:
        host = User(email=f"{prefix}-host@x.com", google_id=f"google-{prefix}-host")
        guest = User(email=f"{prefix}-guest@x.com", google_id=f"google-{prefix}-guest")
        db.add(host)
        db.add(guest)
        db.add(Word(text=word, difficulty=1, active=True, game_type="scribble"))
        db.commit()
        db.refresh(host)
        db.refresh(guest)
        return create_access_token(str(host.id)), create_access_token(str(guest.id))
    finally:
        db.close()


async def _start_scribble(host_token, guest_token, prefix):
    sid_host = await sio.manager.connect(f"eio-{prefix}-host", "/")
    create_res = await sio._trigger_event(
        "room:create", "/", sid_host,
        {"token": host_token, "rounds_total": 1, "difficulty": 1, "turn_seconds": 60, "max_players": 20, "game_type": "scribble"},
    )
    room_code = create_res["lobby"]["room"]["code"]

    sid_guest = await sio.manager.connect(f"eio-{prefix}-guest", "/")
    await sio._trigger_event("room:join", "/", sid_guest, {"room_code": room_code, "token": guest_token})
    await sio._trigger_event("game:start", "/", sid_host, {"room_code": room_code, "token": host_token})

    return room_code, sid_host, sid_guest


@pytest.mark.asyncio
async def test_eraser_flag_preserved_in_relay():
    """Eraser strokes should include eraser=True when relayed to guessers."""
    ht, gt = _setup("eraser1", "pencil")
    room_code, sid_host, sid_guest = await _start_scribble(ht, gt, "eraser1")

    state = ROOM_STATES[room_code]
    describer_id = state.player_order[state.describer_index]
    describer_sid = PLAYER_TO_SID[describer_id]

    # Send an eraser stroke
    await sio._trigger_event("scribble:draw", "/", describer_sid, {
        "room_code": room_code,
        "points": [{"x": 0.1, "y": 0.1}, {"x": 0.5, "y": 0.5}],
        "color": "#FF0000",
        "width": 4,
        "eraser": True,
    })

    # Check the accumulated stroke has eraser=True
    assert len(state.strokes) == 1
    assert state.strokes[0]["eraser"] is True


@pytest.mark.asyncio
async def test_non_eraser_stroke_has_eraser_false():
    """Normal strokes should have eraser=False."""
    ht, gt = _setup("eraser2", "brush")
    room_code, sid_host, sid_guest = await _start_scribble(ht, gt, "eraser2")

    state = ROOM_STATES[room_code]
    describer_sid = PLAYER_TO_SID[state.player_order[state.describer_index]]

    await sio._trigger_event("scribble:draw", "/", describer_sid, {
        "room_code": room_code,
        "points": [{"x": 0.1, "y": 0.1}, {"x": 0.3, "y": 0.3}],
        "color": "#000000",
        "width": 4,
    })

    assert len(state.strokes) == 1
    assert state.strokes[0]["eraser"] is False


@pytest.mark.asyncio
async def test_color_preserved_in_relay():
    """Stroke color should be preserved in the relay."""
    ht, gt = _setup("color1", "palette")
    room_code, sid_host, sid_guest = await _start_scribble(ht, gt, "color1")

    state = ROOM_STATES[room_code]
    describer_sid = PLAYER_TO_SID[state.player_order[state.describer_index]]

    # Send strokes with different colors
    for color in ["#FF0000", "#00FF00", "#0000FF"]:
        await sio._trigger_event("scribble:draw", "/", describer_sid, {
            "room_code": room_code,
            "points": [{"x": 0.1, "y": 0.1}, {"x": 0.5, "y": 0.5}],
            "color": color,
            "width": 4,
        })

    assert len(state.strokes) == 3
    assert state.strokes[0]["color"] == "#FF0000"
    assert state.strokes[1]["color"] == "#00FF00"
    assert state.strokes[2]["color"] == "#0000FF"


@pytest.mark.asyncio
async def test_strokes_accumulated_in_buffer():
    """Multiple strokes should accumulate in the game state buffer."""
    ht, gt = _setup("accum1", "sketch")
    room_code, sid_host, sid_guest = await _start_scribble(ht, gt, "accum1")

    state = ROOM_STATES[room_code]
    describer_sid = PLAYER_TO_SID[state.player_order[state.describer_index]]

    for i in range(5):
        await sio._trigger_event("scribble:draw", "/", describer_sid, {
            "room_code": room_code,
            "points": [{"x": 0.1 * i, "y": 0.1 * i}, {"x": 0.2 * i, "y": 0.2 * i}],
            "color": "#000000",
            "width": 4,
        })

    assert len(state.strokes) == 5


@pytest.mark.asyncio
async def test_clear_resets_stroke_buffer():
    """scribble:clear should reset the stroke buffer."""
    ht, gt = _setup("clear1", "eraser")
    room_code, sid_host, sid_guest = await _start_scribble(ht, gt, "clear1")

    state = ROOM_STATES[room_code]
    describer_sid = PLAYER_TO_SID[state.player_order[state.describer_index]]

    # Draw some strokes
    await sio._trigger_event("scribble:draw", "/", describer_sid, {
        "room_code": room_code,
        "points": [{"x": 0.1, "y": 0.1}, {"x": 0.5, "y": 0.5}],
        "color": "#000000",
        "width": 4,
    })
    assert len(state.strokes) == 1

    # Clear canvas
    await sio._trigger_event("scribble:clear", "/", describer_sid, {"room_code": room_code})
    assert len(state.strokes) == 0


@pytest.mark.asyncio
async def test_non_drawer_cannot_send_strokes():
    """Only the drawer should be able to send strokes."""
    ht, gt = _setup("auth1", "guard")
    room_code, sid_host, sid_guest = await _start_scribble(ht, gt, "auth1")

    state = ROOM_STATES[room_code]
    describer_id = state.player_order[state.describer_index]

    # Find the non-drawer's SID
    non_drawer_id = [p for p in state.player_order if p != describer_id][0]
    non_drawer_sid = PLAYER_TO_SID[non_drawer_id]

    # Non-drawer tries to send a stroke -- should be ignored
    await sio._trigger_event("scribble:draw", "/", non_drawer_sid, {
        "room_code": room_code,
        "points": [{"x": 0.1, "y": 0.1}, {"x": 0.5, "y": 0.5}],
        "color": "#000000",
        "width": 4,
    })

    assert len(state.strokes) == 0


@pytest.mark.asyncio
async def test_mixed_eraser_and_color_strokes():
    """Interleaved eraser and colored strokes should all preserve their properties."""
    ht, gt = _setup("mixed1", "art")
    room_code, sid_host, sid_guest = await _start_scribble(ht, gt, "mixed1")

    state = ROOM_STATES[room_code]
    describer_sid = PLAYER_TO_SID[state.player_order[state.describer_index]]

    strokes_data = [
        {"color": "#FF0000", "eraser": False},
        {"color": "#00FF00", "eraser": True},   # eraser
        {"color": "#0000FF", "eraser": False},
        {"color": "#FFFF00", "eraser": True},   # eraser
    ]

    for s in strokes_data:
        await sio._trigger_event("scribble:draw", "/", describer_sid, {
            "room_code": room_code,
            "points": [{"x": 0.1, "y": 0.1}, {"x": 0.5, "y": 0.5}],
            "color": s["color"],
            "width": 4,
            "eraser": s["eraser"],
        })

    assert len(state.strokes) == 4
    assert state.strokes[0]["eraser"] is False
    assert state.strokes[0]["color"] == "#FF0000"
    assert state.strokes[1]["eraser"] is True
    assert state.strokes[1]["color"] == "#00FF00"
    assert state.strokes[2]["eraser"] is False
    assert state.strokes[3]["eraser"] is True
