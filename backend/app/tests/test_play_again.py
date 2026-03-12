import asyncio
import pytest

from app.db.session import SessionLocal
from app.models.user import User
from app.models.room import Room
from app.models.room_player import RoomPlayer
from app.models.word import Word
from app.services.auth import create_access_token
from app.sockets.events import sio, PLAY_AGAIN_VOTES
from app.services.game_state import ROOM_STATES, SID_TO_PLAYER


async def _setup_finished_game(host_email, guest_email, host_gid, guest_gid, eio_prefix):
    """Helper: create room, join, start game, end game. Returns (room_code, sid_host, sid_guest, host_token, guest_token)."""
    db = SessionLocal()
    try:
        host = User(email=host_email, google_id=host_gid)
        guest = User(email=guest_email, google_id=guest_gid)
        db.add(host)
        db.add(guest)
        db.add(Word(text=f"word-{eio_prefix}", difficulty=1, active=True))
        db.commit()
        db.refresh(host)
        db.refresh(guest)
        host_token = create_access_token(str(host.id))
        guest_token = create_access_token(str(guest.id))
    finally:
        db.close()

    sid_host = await sio.manager.connect(f"eio-{eio_prefix}-host", "/")
    create_res = await sio._trigger_event(
        "room:create", "/", sid_host,
        {"token": host_token, "rounds_total": 1, "difficulty": 1, "turn_seconds": 60, "max_players": 20},
    )
    room_code = create_res["lobby"]["room"]["code"]

    sid_guest = await sio.manager.connect(f"eio-{eio_prefix}-guest", "/")
    await sio._trigger_event("room:join", "/", sid_guest, {"room_code": room_code, "token": guest_token})

    await sio._trigger_event("game:start", "/", sid_host, {"room_code": room_code, "token": host_token})

    # End the game: 2 players, 1 round = 2 turn ends
    await sio._trigger_event("game:turn_end", "/", sid_host, {"room_code": room_code})
    await sio._trigger_event("game:turn_end", "/", sid_host, {"room_code": room_code})

    # Game should be over now
    assert room_code not in ROOM_STATES

    return room_code, sid_host, sid_guest, host_token, guest_token


@pytest.mark.asyncio
async def test_play_again_all_vote_triggers_ready():
    """When all connected players vote to play again, game:play_again_ready is emitted."""
    room_code, sid_host, sid_guest, host_token, guest_token = await _setup_finished_game(
        "pa-host1@test.com", "pa-guest1@test.com", "gid-pa1-h", "gid-pa1-g", "pa1",
    )

    # Both players vote to play again
    res1 = await sio._trigger_event(
        "game:play_again", "/", sid_host,
        {"room_code": room_code, "token": host_token},
    )
    assert res1["ok"] is True

    # After first vote, votes should be tracked
    assert room_code in PLAY_AGAIN_VOTES
    assert len(PLAY_AGAIN_VOTES[room_code]["player_ids"]) == 1

    res2 = await sio._trigger_event(
        "game:play_again", "/", sid_guest,
        {"room_code": room_code, "token": guest_token},
    )
    assert res2["ok"] is True

    # After all vote, tracking should be cleaned up
    assert room_code not in PLAY_AGAIN_VOTES


@pytest.mark.asyncio
async def test_play_again_partial_vote_shows_waiting():
    """When only some players vote, the vote count is tracked but ready is not emitted."""
    room_code, sid_host, sid_guest, host_token, guest_token = await _setup_finished_game(
        "pa-host2@test.com", "pa-guest2@test.com", "gid-pa2-h", "gid-pa2-g", "pa2",
    )

    res = await sio._trigger_event(
        "game:play_again", "/", sid_host,
        {"room_code": room_code, "token": host_token},
    )
    assert res["ok"] is True

    # Vote tracking should exist with 1 vote out of 2
    assert room_code in PLAY_AGAIN_VOTES
    votes = PLAY_AGAIN_VOTES[room_code]
    assert len(votes["player_ids"]) == 1
    assert votes["total"] == 2


@pytest.mark.asyncio
async def test_play_again_timeout_expires_votes():
    """After 30 seconds, if not all players voted, votes expire and tracking is cleaned up."""
    room_code, sid_host, sid_guest, host_token, guest_token = await _setup_finished_game(
        "pa-host3@test.com", "pa-guest3@test.com", "gid-pa3-h", "gid-pa3-g", "pa3",
    )

    # Monkey-patch the timeout to be very short for testing
    original_sleep = asyncio.sleep

    async def fast_sleep(duration):
        if duration == 30:
            await original_sleep(0.1)
        else:
            await original_sleep(duration)

    import app.sockets.events as events_module
    old_sleep = asyncio.sleep
    asyncio.sleep = fast_sleep

    try:
        res = await sio._trigger_event(
            "game:play_again", "/", sid_host,
            {"room_code": room_code, "token": host_token},
        )
        assert res["ok"] is True
        assert room_code in PLAY_AGAIN_VOTES

        # Wait for the fast timeout to fire
        await original_sleep(0.3)

        # Votes should be cleaned up after timeout
        assert room_code not in PLAY_AGAIN_VOTES
    finally:
        asyncio.sleep = old_sleep


@pytest.mark.asyncio
async def test_play_again_room_status_is_lobby_after_game_end():
    """After game ends, room status should be 'lobby' allowing a new game to start."""
    room_code, sid_host, sid_guest, host_token, guest_token = await _setup_finished_game(
        "pa-host4@test.com", "pa-guest4@test.com", "gid-pa4-h", "gid-pa4-g", "pa4",
    )

    db = SessionLocal()
    try:
        room = db.query(Room).filter(Room.code == room_code).first()
        assert room is not None
        assert room.status == "lobby"

        # Players should have in_game = False
        players = db.query(RoomPlayer).filter(RoomPlayer.room_id == room.id).all()
        assert len(players) == 2
        assert all(not p.in_game for p in players)
    finally:
        db.close()


@pytest.mark.asyncio
async def test_play_again_then_start_new_game():
    """After all vote play again, host can start a new game in the same room."""
    room_code, sid_host, sid_guest, host_token, guest_token = await _setup_finished_game(
        "pa-host5@test.com", "pa-guest5@test.com", "gid-pa5-h", "gid-pa5-g", "pa5",
    )

    # Both vote play again
    await sio._trigger_event("game:play_again", "/", sid_host, {"room_code": room_code, "token": host_token})
    await sio._trigger_event("game:play_again", "/", sid_guest, {"room_code": room_code, "token": guest_token})
    assert room_code not in PLAY_AGAIN_VOTES

    # Add a fresh word for the new game
    db = SessionLocal()
    try:
        db.add(Word(text="newword-pa5", difficulty=1, active=True))
        db.commit()
    finally:
        db.close()

    # Host starts a new game in the same room
    start_res = await sio._trigger_event(
        "game:start", "/", sid_host,
        {"room_code": room_code, "token": host_token},
    )
    assert start_res["ok"] is True
    assert room_code in ROOM_STATES


@pytest.mark.asyncio
async def test_play_again_duplicate_vote_ignored():
    """A player voting twice should not double-count."""
    room_code, sid_host, sid_guest, host_token, guest_token = await _setup_finished_game(
        "pa-host6@test.com", "pa-guest6@test.com", "gid-pa6-h", "gid-pa6-g", "pa6",
    )

    await sio._trigger_event("game:play_again", "/", sid_host, {"room_code": room_code, "token": host_token})
    await sio._trigger_event("game:play_again", "/", sid_host, {"room_code": room_code, "token": host_token})

    # Should still be waiting — only 1 unique player voted
    assert room_code in PLAY_AGAIN_VOTES
    assert len(PLAY_AGAIN_VOTES[room_code]["player_ids"]) == 1


@pytest.mark.asyncio
async def test_play_again_invalid_room():
    """Voting for a non-existent room returns an error."""
    db = SessionLocal()
    try:
        user = User(email="pa-bad@test.com", google_id="gid-pa-bad")
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_access_token(str(user.id))
    finally:
        db.close()

    sid = await sio.manager.connect("eio-pa-bad", "/")
    res = await sio._trigger_event(
        "game:play_again", "/", sid,
        {"room_code": "NONEXISTENT", "token": token},
    )
    assert res["ok"] is False
