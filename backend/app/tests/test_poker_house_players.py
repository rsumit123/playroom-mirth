import itertools

import pytest

from app.db.session import SessionLocal
from app.models.guest import Guest
from app.models.room_player import RoomPlayer
from app.models.user import User
from app.services.auth import create_access_token
from app.services.game_state import ROOM_STATES
from app.services.poker_ai import seats as house
from app.sockets.events import sio

_unique = itertools.count(1)


def test_a_guest_gets_the_cheap_seat_and_a_signed_in_player_gets_the_choice():
    """Every decision a house player makes costs money at OpenRouter, so the
    expensive models are for people who have signed in."""
    assert house.tiers_for(signed_in=True) == ("Easy", "Medium", "Hard")
    assert house.tiers_for(signed_in=False) == ("Easy",)
    assert house.is_allowed("Hard", signed_in=True)
    assert not house.is_allowed("Hard", signed_in=False)
    assert house.is_allowed("Easy", signed_in=False)


async def _poker_room(signed_in: bool = True):
    tag = next(_unique)
    db = SessionLocal()
    try:
        if signed_in:
            host = User(email=f"housed{tag}@example.com", google_id=f"g-housed-{tag}", password_hash="x")
            db.add(host)
            db.commit()
            db.refresh(host)
            credential = {"token": create_access_token(str(host.id))}
        else:
            guest = Guest(guest_token=f"guest-token-{tag}", display_name=f"Guest {tag}")
            db.add(guest)
            db.commit()
            db.refresh(guest)
            credential = {"guest_token": guest.guest_token}
    finally:
        db.close()

    sid = await sio.manager.connect(f"eio-house-{tag}", "/")
    created = await sio._trigger_event("room:create", "/", sid, {
        **credential, "rounds_total": 1, "difficulty": 1, "turn_seconds": 30,
        "max_players": 2, "game_type": "poker", "starting_chips": 500, "small_blind": 5,
    })
    return created["lobby"]["room"]["code"], sid, credential


@pytest.mark.asyncio
async def test_the_host_can_sit_a_model_at_the_table():
    room_code, sid, credential = await _poker_room()
    ack = await sio._trigger_event("poker:add_bot", "/", sid, {
        "room_code": room_code, "tier": "Hard", **credential,
    })
    assert ack["ok"] is True

    with SessionLocal() as db:
        from app.models.room import Room

        room = db.query(Room).filter(Room.code == room_code).first()
        players = db.query(RoomPlayer).filter(RoomPlayer.room_id == room.id).all()
        seated = [player for player in players if player.ai_tier]
        assert len(seated) == 1
        assert seated[0].ai_tier == "Hard"
        # It is an ordinary bot user, so names, history and the leaderboard
        # keep working without knowing a model is behind it.
        bot = db.query(User).filter(User.id == seated[0].user_id).first()
        assert bot.is_bot is True


@pytest.mark.asyncio
async def test_a_guest_is_refused_the_expensive_seat():
    room_code, sid, credential = await _poker_room(signed_in=False)
    ack = await sio._trigger_event("poker:add_bot", "/", sid, {
        "room_code": room_code, "tier": "Hard", **credential,
    })
    assert ack["ok"] is False
    assert ack["error"] == "TIER_NOT_ALLOWED"

    allowed = await sio._trigger_event("poker:add_bot", "/", sid, {
        "room_code": room_code, "tier": "Easy", **credential,
    })
    assert allowed["ok"] is True


@pytest.mark.asyncio
async def test_a_model_takes_its_turn_when_the_table_reaches_it(monkeypatch):
    """With no key configured the house player still has to act rather than
    hold the table up: it checks if that is free and folds otherwise."""
    room_code, sid, credential = await _poker_room()
    await sio._trigger_event("poker:add_bot", "/", sid, {"room_code": room_code, "tier": "Easy", **credential})
    started = await sio._trigger_event("game:start", "/", sid, {"room_code": room_code, **credential})
    assert started["ok"] is True

    state = ROOM_STATES[room_code]
    assert state.poker_seats, "the table should know which seat holds a model"

    import asyncio

    # The house turn runs as its own task; give it a moment to land.
    for _ in range(20):
        await asyncio.sleep(0.02)
        if state.poker is None or state.poker["hand"]["current_seat"] not in state.poker_seats:
            break
    seat_with_model = next(iter(state.poker_seats))
    assert state.poker is None or state.poker["hand"]["current_seat"] != seat_with_model
