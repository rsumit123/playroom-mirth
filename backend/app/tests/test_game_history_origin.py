from sqlalchemy import inspect
from app.db.session import engine


def test_game_history_has_origin_column():
    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns("game_history")}
    assert "origin" in cols
