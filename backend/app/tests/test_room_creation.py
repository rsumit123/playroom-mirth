import pytest
from unittest.mock import patch
from pydantic import ValidationError

from app.db.session import SessionLocal
from app.models.room import Room
from app.models.user import User
from app.schemas.room import RoomCreateRequest, RoomCreateGuestRequest, RoomOut
from app.services.auth import create_access_token


def create_user_and_token(email: str):
    db = SessionLocal()
    try:
        user = User(email=email, google_id=f"google-{email}")
        db.add(user)
        db.commit()
        db.refresh(user)
        return create_access_token(str(user.id))
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Schema-level tests for RoomCreateRequest
# ---------------------------------------------------------------------------


def test_room_create_request_default_game_type():
    """RoomCreateRequest should default game_type to 'charades'."""
    req = RoomCreateRequest(rounds_total=3, difficulty=1, turn_seconds=60)
    assert req.game_type == "charades"


def test_room_create_request_explicit_charades():
    """Explicitly passing game_type='charades' should work."""
    req = RoomCreateRequest(
        rounds_total=2, difficulty=2, turn_seconds=45, game_type="charades"
    )
    assert req.game_type == "charades"


def test_room_create_request_scribble():
    """Passing game_type='scribble' should be accepted."""
    req = RoomCreateRequest(
        rounds_total=1, difficulty=1, turn_seconds=90, game_type="scribble"
    )
    assert req.game_type == "scribble"


def test_room_create_request_custom_game_type():
    """Any string is accepted (schema does not restrict to enum)."""
    req = RoomCreateRequest(
        rounds_total=1, difficulty=1, turn_seconds=60, game_type="trivia"
    )
    assert req.game_type == "trivia"


def test_room_create_request_max_players_default():
    """max_players should default to 20."""
    req = RoomCreateRequest(rounds_total=1, difficulty=1, turn_seconds=60)
    assert req.max_players == 20


def test_room_create_request_missing_required_fields():
    """Omitting required fields should raise ValidationError."""
    with pytest.raises(ValidationError):
        RoomCreateRequest(difficulty=1, turn_seconds=60)  # missing rounds_total

    with pytest.raises(ValidationError):
        RoomCreateRequest(rounds_total=1, turn_seconds=60)  # missing difficulty

    with pytest.raises(ValidationError):
        RoomCreateRequest(rounds_total=1, difficulty=1)  # missing turn_seconds


def test_room_create_guest_request_inherits_game_type():
    """RoomCreateGuestRequest extends RoomCreateRequest and keeps game_type default."""
    req = RoomCreateGuestRequest(
        guest_token="abc123",
        rounds_total=2,
        difficulty=1,
        turn_seconds=60,
    )
    assert req.game_type == "charades"
    assert req.guest_token == "abc123"


def test_room_create_guest_request_with_scribble():
    """RoomCreateGuestRequest should accept game_type='scribble'."""
    req = RoomCreateGuestRequest(
        guest_token="abc123",
        rounds_total=2,
        difficulty=1,
        turn_seconds=60,
        game_type="scribble",
    )
    assert req.game_type == "scribble"


# ---------------------------------------------------------------------------
# Schema-level tests for RoomOut
# ---------------------------------------------------------------------------


def test_room_out_default_game_type():
    """RoomOut should default game_type to 'charades'."""
    out = RoomOut(
        id=1,
        code="ABCDEF",
        status="lobby",
        max_players=20,
        min_players=2,
        rounds_total=3,
        difficulty=1,
        turn_seconds=60,
    )
    assert out.game_type == "charades"


def test_room_out_preserves_game_type():
    """RoomOut should preserve an explicit game_type."""
    out = RoomOut(
        id=1,
        code="ABCDEF",
        status="lobby",
        max_players=20,
        min_players=2,
        rounds_total=3,
        difficulty=1,
        turn_seconds=60,
        game_type="scribble",
    )
    assert out.game_type == "scribble"


# ---------------------------------------------------------------------------
# Model-level tests for Room (database)
# ---------------------------------------------------------------------------


def test_room_model_default_game_type():
    """Room ORM model should default game_type to 'charades'."""
    db = SessionLocal()
    try:
        room = Room(
            code="TSTGAM",
            host_user_id=None,
            host_guest_id=None,
            rounds_total=2,
            difficulty=1,
            turn_seconds=60,
        )
        db.add(room)
        db.commit()
        db.refresh(room)

        assert room.game_type == "charades"
        assert room.status == "lobby"
    finally:
        db.close()


def test_room_model_scribble_game_type():
    """Room ORM model should persist game_type='scribble' correctly."""
    db = SessionLocal()
    try:
        room = Room(
            code="SCRBTL",
            host_user_id=None,
            host_guest_id=None,
            rounds_total=1,
            difficulty=2,
            turn_seconds=90,
            game_type="scribble",
        )
        db.add(room)
        db.commit()
        db.refresh(room)

        assert room.game_type == "scribble"
    finally:
        db.close()


def test_room_model_query_by_game_type():
    """Should be able to query rooms by game_type."""
    db = SessionLocal()
    try:
        db.add(Room(code="CHR001", rounds_total=1, difficulty=1, turn_seconds=60, game_type="charades"))
        db.add(Room(code="SCR001", rounds_total=1, difficulty=1, turn_seconds=60, game_type="scribble"))
        db.add(Room(code="CHR002", rounds_total=1, difficulty=1, turn_seconds=60, game_type="charades"))
        db.commit()

        charades_rooms = db.query(Room).filter(Room.game_type == "charades").all()
        scribble_rooms = db.query(Room).filter(Room.game_type == "scribble").all()

        assert len(charades_rooms) == 2
        assert len(scribble_rooms) == 1
        assert scribble_rooms[0].code == "SCR001"
    finally:
        db.close()


def test_room_create_via_api_default_game_type(client):
    """Creating a room via POST /rooms should default game_type to 'charades'."""
    token = create_user_and_token("gametype@example.com")

    create = client.post(
        "/rooms",
        json={"rounds_total": 2, "difficulty": 1, "turn_seconds": 60, "max_players": 10},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create.status_code == 201
    room_data = create.json()["room"]
    assert room_data["game_type"] == "charades"


def test_room_create_via_api_with_scribble(client):
    """Creating a room with game_type='scribble' should persist correctly."""
    token = create_user_and_token("scribble@example.com")

    create = client.post(
        "/rooms",
        json={
            "rounds_total": 2,
            "difficulty": 1,
            "turn_seconds": 60,
            "max_players": 10,
            "game_type": "scribble",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create.status_code == 201
    room_data = create.json()["room"]
    assert room_data["game_type"] == "scribble"



def test_a_poker_room_carries_the_shape_of_the_table():
    """Seats come from max_players and the big blind is twice the small one, so
    a poker table needs only these two beyond the ordinary room fields."""
    req = RoomCreateRequest(
        rounds_total=1,
        difficulty=1,
        turn_seconds=30,
        max_players=3,
        game_type="poker",
        starting_chips=5000,
        small_blind=25,
    )
    assert req.starting_chips == 5000
    assert req.small_blind == 25

    db = SessionLocal()
    try:
        room = Room(
            code="POK001",
            rounds_total=req.rounds_total,
            difficulty=req.difficulty,
            turn_seconds=req.turn_seconds,
            max_players=req.max_players,
            game_type=req.game_type,
            starting_chips=req.starting_chips,
            small_blind=req.small_blind,
        )
        db.add(room)
        db.commit()
        db.refresh(room)
        out = RoomOut.model_validate(room)
        assert out.game_type == "poker"
        assert (out.max_players, out.starting_chips, out.small_blind) == (3, 5000, 25)
    finally:
        db.close()


def test_a_table_that_says_nothing_about_chips_gets_the_ordinary_ones():
    req = RoomCreateRequest(rounds_total=1, difficulty=1, turn_seconds=30, game_type="poker")
    assert (req.starting_chips, req.small_blind) == (1000, 5)
