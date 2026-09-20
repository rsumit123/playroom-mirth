import itertools
import json

import pytest

from app.db.session import SessionLocal
from app.models.user import User
from app.services.auth import create_access_token
from app.services.game_state import ROOM_STATES
from app.sockets.events import sio


# id() is reused once an object is collected, which made two tables share a
# socket id and the second one act as the first.
_unique = itertools.count(1)


async def _seat_two_and_start():
    """A two handed poker table, started, with both sockets connected."""
    tag = next(_unique)
    db = SessionLocal()
    try:
        host = User(email=f"pokerhost{tag}@example.com", google_id=f"g-poker-host-{tag}")
        other = User(email=f"pokerguest{tag}@example.com", google_id=f"g-poker-guest-{tag}")
        db.add_all([host, other])
        db.commit()
        db.refresh(host)
        db.refresh(other)
        host_token = create_access_token(str(host.id))
        other_token = create_access_token(str(other.id))
    finally:
        db.close()

    sid_host = await sio.manager.connect(f"eio-poker-host-{tag}", "/")
    created = await sio._trigger_event("room:create", "/", sid_host, {
        "token": host_token, "rounds_total": 1, "difficulty": 1, "turn_seconds": 30,
        "max_players": 2, "game_type": "poker", "starting_chips": 1000, "small_blind": 5,
    })
    room_code = created["lobby"]["room"]["code"]

    sid_other = await sio.manager.connect(f"eio-poker-guest-{tag}", "/")
    await sio._trigger_event("room:join", "/", sid_other, {"room_code": room_code, "token": other_token})

    started = await sio._trigger_event("game:start", "/", sid_host, {"room_code": room_code, "token": host_token})
    assert started["ok"] is True
    return room_code, sid_host, sid_other


@pytest.mark.asyncio
async def test_starting_a_poker_room_deals_a_hand():
    room_code, _, _ = await _seat_two_and_start()
    state = ROOM_STATES[room_code]
    assert state.game_type == "poker"
    assert state.poker is not None

    hand = state.poker["hand"]
    assert hand["street"] == "preflop"
    # Two cards each, off a deck that is short by exactly that many.
    assert all(len(player["hole_cards"]) == 2 for player in hand["players"])
    assert hand["current_seat"] in state.player_order
    # The blinds are posted before anybody acts.
    assert sum(player["total_contribution"] for player in hand["players"]) == 15


@pytest.mark.asyncio
async def test_a_seat_is_never_sent_another_seat_s_cards(monkeypatch):
    """The one mistake that matters here: a room broadcast deals the table face
    up. Every poker state goes to one socket, and carries only that seat."""
    sent: list[tuple[str | None, dict]] = []

    original = sio.emit

    async def recording_emit(event, data=None, **kwargs):
        if event == "poker:state":
            sent.append((kwargs.get("to"), data))
            assert kwargs.get("room") is None, "poker state must never be broadcast to a room"
        return await original(event, data, **kwargs)

    monkeypatch.setattr(sio, "emit", recording_emit)
    room_code, _, _ = await _seat_two_and_start()
    state = ROOM_STATES[room_code]

    assert sent, "each seat should have been sent its own view"
    for _, view in sent:
        seat_id = view["seat_id"]
        own = state.poker["hand"]["players"]
        mine = next(player for player in own if player["seat_id"] == seat_id)
        assert view["hole_cards"] == mine["hole_cards"]
        # Nobody else's cards, and not the undealt deck either.
        body = json.dumps(view)
        for player in own:
            if player["seat_id"] == seat_id:
                continue
            for card in player["hole_cards"]:
                assert json.dumps(card) not in body
        assert "deck" not in body


@pytest.mark.asyncio
async def test_acting_moves_the_turn_on_and_a_repeat_is_harmless():
    room_code, sid_host, sid_other = await _seat_two_and_start()
    state = ROOM_STATES[room_code]
    to_act = state.poker["hand"]["current_seat"]
    revision = state.poker["revision"]

    from app.services.game_state import PLAYER_TO_SID

    sid = PLAYER_TO_SID[to_act]
    ack = await sio._trigger_event("poker:action", "/", sid, {
        "room_code": room_code,
        "action": {"type": "call", "amount": 10},
        "expected_revision": revision,
        "idempotency_key": "once",
    })
    assert ack["ok"] is True
    assert ROOM_STATES[room_code].poker["hand"]["current_seat"] != to_act

    # The same command arriving twice - a retry on a flaky connection - must not
    # act twice.
    again = await sio._trigger_event("poker:action", "/", sid, {
        "room_code": room_code,
        "action": {"type": "call", "amount": 10},
        "expected_revision": revision,
        "idempotency_key": "once",
    })
    assert again["ok"] is True and again.get("repeat") is True


@pytest.mark.asyncio
async def test_a_seat_cannot_act_out_of_turn():
    room_code, _, _ = await _seat_two_and_start()
    state = ROOM_STATES[room_code]
    waiting = next(seat for seat in state.player_order if seat != state.poker["hand"]["current_seat"])

    from app.services.game_state import PLAYER_TO_SID

    ack = await sio._trigger_event("poker:action", "/", PLAYER_TO_SID[waiting], {
        "room_code": room_code,
        "action": {"type": "fold"},
    })
    assert ack["ok"] is False
    assert ack["error"] == "NOT_YOUR_TURN"
