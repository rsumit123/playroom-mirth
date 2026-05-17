"""User.is_bot column + idempotent migration."""

from sqlalchemy import inspect

from app.db.session import SessionLocal, engine
from app.models.user import User


def test_user_has_is_bot_column():
    inspector = inspect(engine)
    cols = {c["name"]: c for c in inspector.get_columns("users")}
    assert "is_bot" in cols
    assert cols["is_bot"]["default"] in (False, 0, "0", "'0'", "false", "FALSE")


def test_default_is_bot_false():
    db = SessionLocal()
    try:
        u = User(email="testbot@example.com", google_id="g-testbot")
        db.add(u)
        db.commit()
        db.refresh(u)
        assert u.is_bot is False
    finally:
        db.close()
