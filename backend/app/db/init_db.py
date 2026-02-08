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

    # Manual migration: add Google auth columns to users if missing
    user_columns = [col["name"] for col in inspector.get_columns("users")]
    with engine.begin() as conn:
        if "google_id" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN google_id VARCHAR(255)"))
        if "display_name" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN display_name VARCHAR(255)"))
        if "avatar_url" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(512)"))
