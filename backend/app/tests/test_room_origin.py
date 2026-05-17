"""Room.origin column."""

from sqlalchemy import inspect

from app.db.session import SessionLocal, engine
from app.models.user import User
from app.models.room import Room


def test_room_has_origin_column():
    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns("rooms")}
    assert "origin" in cols


def test_room_origin_defaults_to_friends():
    db = SessionLocal()
    try:
        host = User(email="rh@example.com", google_id="g-rh")
        db.add(host)
        db.commit()
        db.refresh(host)
        r = Room(code="TEST01", host_user_id=host.id, status="lobby",
                 rounds_total=1, difficulty=1, turn_seconds=60,
                 max_players=2, min_players=2)
        db.add(r)
        db.commit()
        db.refresh(r)
        assert r.origin == "friends"
    finally:
        db.close()
