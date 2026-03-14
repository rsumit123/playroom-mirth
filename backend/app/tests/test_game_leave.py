"""Tests for the game:leave socket event handler."""
import asyncio
import pytest

from app.db.session import SessionLocal
from app.models.user import User
from app.models.word import Word
from app.models.room import Room
from app.models.room_player import RoomPlayer
from app.services.auth import create_access_token
from app.sockets.events import sio
from app.services.game_state import ROOM_STATES, SID_TO_PLAYER, PLAYER_TO_SID, PLAYER_TO_ROOM


def _setup_db(host_email, guest_email, word="apple"):
    db = SessionLocal()
    try:
        host = User(email=host_email, google_id=f"google-{host_email}")
        guest = User(email=guest_email, google_id=f"google-{guest_email}")
        db.add(host)
        db.add(guest)
        db.add(Word(text=word, difficulty=1, active=True))
        db.commit()
        db.refresh(host)
        db.refresh(guest)
        return create_access_token(str(host.id)), create_access_token(str(guest.id))
    finally:
        db.close()


async def _create_and_start_game(host_token, guest_token, eio_prefix, rounds=1, turn_seconds=60):
    sid_host = await sio.manager.connect(f"eio-{eio_prefix}-host", "/")
    create_res = await sio._trigger_event(
        "room:create", "/", sid_host,
        {"token": host_token, "rounds_total": rounds, "difficulty": 1, "turn_seconds": turn_seconds, "max_players": 20},
    )
    room_code = create_res["lobby"]["room"]["code"]

    sid_guest = await sio.manager.connect(f"eio-{eio_prefix}-guest", "/")
    await sio._trigger_event("room:join", "/", sid_guest, {"room_code": room_code, "token": guest_token})
    await sio._trigger_event("game:start", "/", sid_host, {"room_code": room_code, "token": host_token})

    return room_code, sid_host, sid_guest


@pytest.mark.asyncio
async def test_guesser_leaves_game_ends_with_2_players():
    """When guesser leaves a 2-player game, game should auto-end."""
    host_token, guest_token = _setup_db("leave-host1@x.com", "leave-guest1@x.com", "banana")
    room_code, sid_host, sid_guest = await _create_and_start_game(host_token, guest_token, "leave1")

    assert room_code in ROOM_STATES

    # Guest (guesser) leaves
    await sio._trigger_event("game:leave", "/", sid_guest, {"room_code": room_code})

    # Game should have ended (removed from ROOM_STATES)
    assert room_code not in ROOM_STATES

    # Room should be back in lobby status
    db = SessionLocal()
    try:
        room = db.query(Room).filter(Room.code == room_code).first()
        assert room.status == "lobby"
    finally:
        db.close()


@pytest.mark.asyncio
async def test_describer_leaves_game_ends_with_2_players():
    """When describer leaves a 2-player game, game should auto-end."""
    host_token, guest_token = _setup_db("leave-host2@x.com", "leave-guest2@x.com", "cherry")
    room_code, sid_host, sid_guest = await _create_and_start_game(host_token, guest_token, "leave2")

    state = ROOM_STATES[room_code]
    describer_id = state.player_order[state.describer_index]
    # Find which SID is the describer
    describer_sid = PLAYER_TO_SID.get(describer_id)

    # Describer leaves
    await sio._trigger_event("game:leave", "/", describer_sid, {"room_code": room_code})

    # Game should auto-end
    assert room_code not in ROOM_STATES


@pytest.mark.asyncio
async def test_leave_cleans_up_player_state():
    """game:leave should clean up SID mappings and DB state."""
    host_token, guest_token = _setup_db("leave-host3@x.com", "leave-guest3@x.com", "grape")
    room_code, sid_host, sid_guest = await _create_and_start_game(host_token, guest_token, "leave3")

    # Find the guest's player_id
    guest_player_id = SID_TO_PLAYER.get(sid_guest)
    assert guest_player_id is not None

    await sio._trigger_event("game:leave", "/", sid_guest, {"room_code": room_code})

    # SID mappings cleaned
    assert sid_guest not in SID_TO_PLAYER
    assert guest_player_id not in PLAYER_TO_SID
    assert guest_player_id not in PLAYER_TO_ROOM

    # DB: player marked as left
    db = SessionLocal()
    try:
        rp = db.query(RoomPlayer).filter(RoomPlayer.id == guest_player_id).first()
        assert rp.in_game is False
        assert rp.connected is False
    finally:
        db.close()


@pytest.mark.asyncio
async def test_leave_3player_game_continues():
    """In a 3-player game, one player leaving should NOT end the game."""
    db = SessionLocal()
    try:
        host = User(email="leave-host4@x.com", google_id="google-leave-host4@x.com")
        guest1 = User(email="leave-g4a@x.com", google_id="google-leave-g4a@x.com")
        guest2 = User(email="leave-g4b@x.com", google_id="google-leave-g4b@x.com")
        db.add(host)
        db.add(guest1)
        db.add(guest2)
        db.add(Word(text="melon", difficulty=1, active=True))
        db.commit()
        db.refresh(host)
        db.refresh(guest1)
        db.refresh(guest2)
        ht = create_access_token(str(host.id))
        g1t = create_access_token(str(guest1.id))
        g2t = create_access_token(str(guest2.id))
    finally:
        db.close()

    sid_host = await sio.manager.connect("eio-leave4-host", "/")
    create_res = await sio._trigger_event(
        "room:create", "/", sid_host,
        {"token": ht, "rounds_total": 1, "difficulty": 1, "turn_seconds": 60, "max_players": 20},
    )
    room_code = create_res["lobby"]["room"]["code"]

    sid_g1 = await sio.manager.connect("eio-leave4-g1", "/")
    await sio._trigger_event("room:join", "/", sid_g1, {"room_code": room_code, "token": g1t})
    sid_g2 = await sio.manager.connect("eio-leave4-g2", "/")
    await sio._trigger_event("room:join", "/", sid_g2, {"room_code": room_code, "token": g2t})

    await sio._trigger_event("game:start", "/", sid_host, {"room_code": room_code, "token": ht})
    assert room_code in ROOM_STATES
    assert len(ROOM_STATES[room_code].player_order) == 3

    # One player leaves
    await sio._trigger_event("game:leave", "/", sid_g2, {"room_code": room_code})

    # Game should continue with 2 players
    assert room_code in ROOM_STATES
    assert len(ROOM_STATES[room_code].player_order) == 2


@pytest.mark.asyncio
async def test_describer_leaves_3player_turn_advances():
    """When the current describer leaves a 3-player game, turn should advance to next player."""
    db = SessionLocal()
    try:
        host = User(email="leave-host5@x.com", google_id="google-leave-host5@x.com")
        guest1 = User(email="leave-g5a@x.com", google_id="google-leave-g5a@x.com")
        guest2 = User(email="leave-g5b@x.com", google_id="google-leave-g5b@x.com")
        db.add(host)
        db.add(guest1)
        db.add(guest2)
        db.add(Word(text="plum", difficulty=1, active=True))
        db.commit()
        db.refresh(host)
        db.refresh(guest1)
        db.refresh(guest2)
        ht = create_access_token(str(host.id))
        g1t = create_access_token(str(guest1.id))
        g2t = create_access_token(str(guest2.id))
    finally:
        db.close()

    sid_host = await sio.manager.connect("eio-leave5-host", "/")
    create_res = await sio._trigger_event(
        "room:create", "/", sid_host,
        {"token": ht, "rounds_total": 1, "difficulty": 1, "turn_seconds": 60, "max_players": 20},
    )
    room_code = create_res["lobby"]["room"]["code"]

    sid_g1 = await sio.manager.connect("eio-leave5-g1", "/")
    await sio._trigger_event("room:join", "/", sid_g1, {"room_code": room_code, "token": g1t})
    sid_g2 = await sio.manager.connect("eio-leave5-g2", "/")
    await sio._trigger_event("room:join", "/", sid_g2, {"room_code": room_code, "token": g2t})

    await sio._trigger_event("game:start", "/", sid_host, {"room_code": room_code, "token": ht})

    state = ROOM_STATES[room_code]
    describer_id = state.player_order[state.describer_index]
    describer_sid = PLAYER_TO_SID[describer_id]

    # Describer leaves
    await sio._trigger_event("game:leave", "/", describer_sid, {"room_code": room_code})

    # Game continues, new describer assigned
    assert room_code in ROOM_STATES
    new_state = ROOM_STATES[room_code]
    assert len(new_state.player_order) == 2
    # The old describer should no longer be in player_order
    assert describer_id not in new_state.player_order


@pytest.mark.asyncio
async def test_leave_with_no_active_game():
    """game:leave when no game is active should still clean up gracefully."""
    host_token, guest_token = _setup_db("leave-host6@x.com", "leave-guest6@x.com", "fig")

    sid_host = await sio.manager.connect("eio-leave6-host", "/")
    create_res = await sio._trigger_event(
        "room:create", "/", sid_host,
        {"token": host_token, "rounds_total": 1, "difficulty": 1, "turn_seconds": 60, "max_players": 20},
    )
    room_code = create_res["lobby"]["room"]["code"]

    sid_guest = await sio.manager.connect("eio-leave6-guest", "/")
    await sio._trigger_event("room:join", "/", sid_guest, {"room_code": room_code, "token": guest_token})

    # Leave without starting a game -- should not crash
    guest_player_id = SID_TO_PLAYER.get(sid_guest)
    await sio._trigger_event("game:leave", "/", sid_guest, {"room_code": room_code})

    assert sid_guest not in SID_TO_PLAYER
