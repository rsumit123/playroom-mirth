"""
End-to-end tests for the REST-based play-again flow.

Simulates the full lifecycle:
1. Create room (guest + authenticated user)
2. Join room
3. Start game via socket
4. End game (turn_end until rounds complete)
5. Both players POST /rooms/{code}/play-again
6. Poll GET /rooms/{code}/play-again
7. Verify state allows starting a new game
"""
import asyncio
import pytest
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.models.user import User
from app.models.guest import Guest
from app.models.room import Room
from app.models.room_player import RoomPlayer
from app.models.word import Word
from app.services.auth import create_access_token
from app.sockets.events import sio
from app.services.game_state import ROOM_STATES, SID_TO_PLAYER, PLAYER_TO_SID
from app.api.rooms import PLAY_AGAIN_REST
from app.main import fastapi_app


@pytest.fixture
def client():
    PLAY_AGAIN_REST.clear()
    return TestClient(fastapi_app)


async def _create_room_and_play_game(prefix):
    """Create a room with 2 users, play and finish a game. Returns (room_code, user1_token, user2_token)."""
    db = SessionLocal()
    try:
        u1 = User(email=f"{prefix}-host@test.com", google_id=f"gid-{prefix}-h")
        u2 = User(email=f"{prefix}-guest@test.com", google_id=f"gid-{prefix}-g")
        db.add(u1)
        db.add(u2)
        # Need words for the game
        db.add(Word(text=f"word1-{prefix}", difficulty=1, active=True))
        db.add(Word(text=f"word2-{prefix}", difficulty=1, active=True))
        db.commit()
        db.refresh(u1)
        db.refresh(u2)
        token1 = create_access_token(str(u1.id))
        token2 = create_access_token(str(u2.id))
    finally:
        db.close()

    # Create room via socket
    sid1 = await sio.manager.connect(f"eio-{prefix}-h", "/")
    res = await sio._trigger_event(
        "room:create", "/", sid1,
        {"token": token1, "rounds_total": 1, "difficulty": 1, "turn_seconds": 60, "max_players": 20},
    )
    room_code = res["lobby"]["room"]["code"]

    # Join room
    sid2 = await sio.manager.connect(f"eio-{prefix}-g", "/")
    await sio._trigger_event("room:join", "/", sid2, {"room_code": room_code, "token": token2})

    # Start game
    await sio._trigger_event("game:start", "/", sid1, {"room_code": room_code, "token": token1})
    assert room_code in ROOM_STATES

    # End game: 2 players x 1 round = 2 turns
    await sio._trigger_event("game:turn_end", "/", sid1, {"room_code": room_code})
    await sio._trigger_event("game:turn_end", "/", sid1, {"room_code": room_code})

    # Game should be over
    assert room_code not in ROOM_STATES

    return room_code, token1, token2


@pytest.mark.asyncio
async def test_rest_play_again_both_vote_ready(client):
    """Both players vote via REST → status becomes 'ready'."""
    room_code, token1, token2 = await _create_room_and_play_game("rest1")

    # Player 1 votes
    r1 = client.post(
        f"/rooms/{room_code}/play-again",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["status"] == "waiting"
    assert data1["voted"] == 1
    assert data1["total"] == 2

    # Poll — should be waiting
    poll1 = client.get(f"/rooms/{room_code}/play-again")
    assert poll1.status_code == 200
    assert poll1.json()["status"] == "waiting"
    assert poll1.json()["voted"] == 1

    # Player 2 votes
    r2 = client.post(
        f"/rooms/{room_code}/play-again",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["status"] == "ready"
    assert data2["voted"] == 2
    assert data2["total"] == 2

    # Poll — should be ready
    poll2 = client.get(f"/rooms/{room_code}/play-again")
    assert poll2.status_code == 200
    assert poll2.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_rest_play_again_duplicate_vote(client):
    """Same player voting twice via REST is idempotent."""
    room_code, token1, token2 = await _create_room_and_play_game("rest2")

    r1 = client.post(
        f"/rooms/{room_code}/play-again",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert r1.json()["voted"] == 1

    # Duplicate vote
    r1b = client.post(
        f"/rooms/{room_code}/play-again",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert r1b.json()["voted"] == 1  # Still 1, not 2
    assert r1b.json()["status"] == "waiting"


@pytest.mark.asyncio
async def test_rest_play_again_ready_then_start_new_game(client):
    """After REST play-again is ready, host can start a new game via socket."""
    room_code, token1, token2 = await _create_room_and_play_game("rest3")

    # Both vote
    client.post(f"/rooms/{room_code}/play-again", headers={"Authorization": f"Bearer {token1}"})
    r2 = client.post(f"/rooms/{room_code}/play-again", headers={"Authorization": f"Bearer {token2}"})
    assert r2.json()["status"] == "ready"

    # Verify DB state: in_game should be True, room status should be lobby
    db = SessionLocal()
    try:
        room = db.query(Room).filter(Room.code == room_code).first()
        assert room.status == "lobby"
        players = db.query(RoomPlayer).filter(RoomPlayer.room_id == room.id).all()
        assert all(p.in_game for p in players), f"Expected all in_game=True, got {[(p.id, p.in_game) for p in players]}"
    finally:
        db.close()

    # Add words for the next game
    db = SessionLocal()
    try:
        db.add(Word(text=f"newword-rest3", difficulty=1, active=True))
        db.commit()
    finally:
        db.close()

    # Start new game via socket
    sid1 = list(SID_TO_PLAYER.keys())[0] if SID_TO_PLAYER else None
    if sid1:
        start_res = await sio._trigger_event(
            "game:start", "/", sid1,
            {"room_code": room_code, "token": token1},
        )
        assert start_res["ok"] is True
        assert room_code in ROOM_STATES


@pytest.mark.asyncio
async def test_rest_play_again_poll_returns_none_before_any_vote(client):
    """GET before any vote returns status 'none'."""
    room_code, token1, token2 = await _create_room_and_play_game("rest4")

    poll = client.get(f"/rooms/{room_code}/play-again")
    assert poll.status_code == 200
    assert poll.json()["status"] == "none"


@pytest.mark.asyncio
async def test_rest_play_again_after_ready_still_returns_ready(client):
    """After all vote and status is 'ready', subsequent votes and polls still return 'ready'."""
    room_code, token1, token2 = await _create_room_and_play_game("rest5")

    client.post(f"/rooms/{room_code}/play-again", headers={"Authorization": f"Bearer {token1}"})
    client.post(f"/rooms/{room_code}/play-again", headers={"Authorization": f"Bearer {token2}"})

    # Poll multiple times — should always be ready
    for _ in range(3):
        poll = client.get(f"/rooms/{room_code}/play-again")
        assert poll.json()["status"] == "ready"

    # Voting again after ready
    r = client.post(f"/rooms/{room_code}/play-again", headers={"Authorization": f"Bearer {token1}"})
    assert r.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_rest_play_again_invalid_room(client):
    """Voting for a non-existent room returns 404."""
    db = SessionLocal()
    try:
        u = User(email="rest-bad@test.com", google_id="gid-rest-bad")
        db.add(u)
        db.commit()
        db.refresh(u)
        token = create_access_token(str(u.id))
    finally:
        db.close()

    r = client.post(
        "/rooms/NONEXISTENT/play-again",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_rest_play_again_unauthenticated(client):
    """Voting without auth returns 401."""
    room_code, _, _ = await _create_room_and_play_game("rest7")

    r = client.post(f"/rooms/{room_code}/play-again")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_rest_play_again_with_guest_token(client):
    """Guest players can vote using guest_token query param."""
    # Create room with guest players instead of authenticated users
    db = SessionLocal()
    try:
        import secrets
        gt1 = secrets.token_urlsafe(24)
        gt2 = secrets.token_urlsafe(24)
        g1 = Guest(guest_token=gt1, display_name="GuestA")
        g2 = Guest(guest_token=gt2, display_name="GuestB")
        db.add(g1)
        db.add(g2)
        db.add(Word(text="word-grest", difficulty=1, active=True))
        db.add(Word(text="word-grest2", difficulty=1, active=True))
        db.commit()
        db.refresh(g1)
        db.refresh(g2)
    finally:
        db.close()

    # Create room via REST
    room_resp = client.post("/rooms/guest", json={
        "guest_token": gt1,
        "display_name": "GuestA",
        "game_type": "charades",
        "rounds_total": 1,
        "difficulty": 1,
        "turn_seconds": 60,
    })
    assert room_resp.status_code == 201
    room_code = room_resp.json()["room"]["code"]

    # Join room
    join_resp = client.post("/rooms/join", json={
        "room_code": room_code,
        "guest_token": gt2,
    })
    assert join_resp.status_code == 200

    # Now start game via socket, end it, then test REST play-again with guest tokens
    sid1 = await sio.manager.connect("eio-grest-h", "/")
    await sio._trigger_event("room:register", "/", sid1, {"room_code": room_code, "guest_token": gt1})
    sid2 = await sio.manager.connect("eio-grest-g", "/")
    await sio._trigger_event("room:register", "/", sid2, {"room_code": room_code, "guest_token": gt2})

    await sio._trigger_event("game:start", "/", sid1, {"room_code": room_code, "guest_token": gt1})

    # End game
    await sio._trigger_event("game:turn_end", "/", sid1, {"room_code": room_code})
    await sio._trigger_event("game:turn_end", "/", sid1, {"room_code": room_code})
    assert room_code not in ROOM_STATES

    # Guest 1 votes via REST
    r1 = client.post(f"/rooms/{room_code}/play-again?guest_token={gt1}")
    assert r1.status_code == 200
    assert r1.json()["status"] == "waiting"
    assert r1.json()["voted"] == 1

    # Guest 2 votes via REST
    r2 = client.post(f"/rooms/{room_code}/play-again?guest_token={gt2}")
    assert r2.status_code == 200
    assert r2.json()["status"] == "ready"
    assert r2.json()["voted"] == 2

    # Poll confirms ready
    poll = client.get(f"/rooms/{room_code}/play-again")
    assert poll.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_rest_play_again_lobby_state_after_ready(client):
    """After play-again is ready, GET /rooms/{code} returns valid lobby state."""
    room_code, token1, token2 = await _create_room_and_play_game("rest9")

    # Both vote
    client.post(f"/rooms/{room_code}/play-again", headers={"Authorization": f"Bearer {token1}"})
    client.post(f"/rooms/{room_code}/play-again", headers={"Authorization": f"Bearer {token2}"})

    # Fetch room state — should be a valid lobby
    room_resp = client.get(f"/rooms/{room_code}", headers={"Authorization": f"Bearer {token1}"})
    assert room_resp.status_code == 200
    lobby = room_resp.json()
    assert lobby["room"]["code"] == room_code
    assert lobby["room"]["status"] == "lobby"
    assert len(lobby["players"]) == 2
    assert lobby["self_player_id"] is not None
