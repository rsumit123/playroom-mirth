from sqlalchemy import inspect, text

from app.db.session import Base, engine
import app.models  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)

    # Manual migration: add display_name column if missing
    guest_columns = [col["name"] for col in inspector.get_columns("guests")]
    if "display_name" not in guest_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE guests ADD COLUMN display_name VARCHAR(30)"))

    # Manual migration: add game_type columns if missing
    room_columns = [col["name"] for col in inspector.get_columns("rooms")]
    if "game_type" not in room_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE rooms ADD COLUMN game_type VARCHAR(20) DEFAULT 'charades' NOT NULL"))

    word_columns = [col["name"] for col in inspector.get_columns("words")]
    if "game_type" not in word_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE words ADD COLUMN game_type VARCHAR(20) DEFAULT 'charades' NOT NULL"))
