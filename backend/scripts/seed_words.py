import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db.session import SessionLocal, engine
from app.db.seed_words import seed_words
from app.db.init_db import init_db
from app.models.word import Word


def main():
    # Recreate the words table to pick up schema changes (composite unique)
    # This is safe because words are all seed data, not user-generated
    Word.__table__.drop(engine, checkfirst=True)
    Word.__table__.create(engine, checkfirst=True)

    db = SessionLocal()
    try:
        inserted = seed_words(db)
        total = db.query(Word).count()
        charades = db.query(Word).filter(Word.game_type == "charades").count()
        scribble = db.query(Word).filter(Word.game_type == "scribble").count()
        print(f"Seeded {inserted} new words")
        print(f"Total: {total} (charades: {charades}, scribble: {scribble})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
