from sqlalchemy import inspect, text

from app.db.session import Base, engine
import app.models  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    # Manual migration: add display_name column if missing
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns("guests")]
    if "display_name" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE guests ADD COLUMN display_name VARCHAR(30)"))
