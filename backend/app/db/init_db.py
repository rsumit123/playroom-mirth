from sqlalchemy import inspect, text

from app.db.session import Base, engine, SessionLocal
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

    if "trivia_category" not in room_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE rooms ADD COLUMN trivia_category VARCHAR(30) DEFAULT 'math' NOT NULL"))

    if "origin" not in room_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE rooms ADD COLUMN origin VARCHAR(20) NOT NULL DEFAULT 'friends'"))

    if "starting_chips" not in room_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE rooms ADD COLUMN starting_chips INTEGER NOT NULL DEFAULT 1000"))

    if "small_blind" not in room_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE rooms ADD COLUMN small_blind INTEGER NOT NULL DEFAULT 5"))

    player_columns = [col["name"] for col in inspector.get_columns("room_players")]
    if "ai_tier" not in player_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE room_players ADD COLUMN ai_tier VARCHAR(10)"))

    word_columns = [col["name"] for col in inspector.get_columns("words")]
    if "game_type" not in word_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE words ADD COLUMN game_type VARCHAR(20) DEFAULT 'charades' NOT NULL"))

    # Manual migration: add scoreboard columns to game_history
    gh_columns = [col["name"] for col in inspector.get_columns("game_history")]
    with engine.begin() as conn:
        if "guest_id" not in gh_columns:
            conn.execute(text("ALTER TABLE game_history ADD COLUMN guest_id INTEGER"))
        if "display_name" not in gh_columns:
            conn.execute(text("ALTER TABLE game_history ADD COLUMN display_name VARCHAR(50) DEFAULT 'Player' NOT NULL"))
        if "game_number" not in gh_columns:
            conn.execute(text("ALTER TABLE game_history ADD COLUMN game_number INTEGER DEFAULT 1 NOT NULL"))
        if "origin" not in gh_columns:
            conn.execute(text("ALTER TABLE game_history ADD COLUMN origin VARCHAR(20) NOT NULL DEFAULT 'friends'"))

    # Manual migration: add Google auth columns to users if missing
    user_columns = [col["name"] for col in inspector.get_columns("users")]
    with engine.begin() as conn:
        if "google_id" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN google_id VARCHAR(255)"))
        if "display_name" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN display_name VARCHAR(255)"))
        if "avatar_url" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(512)"))
        if "is_bot" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_bot BOOLEAN NOT NULL DEFAULT 0"))

    from app.services.bot_users import seed_bot_users
    with SessionLocal() as db:
        seed_bot_users(db)
