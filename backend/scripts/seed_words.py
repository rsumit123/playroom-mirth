import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db.session import SessionLocal
from app.db.seed_words import seed_words
from app.db.init_db import init_db


def main():
    init_db()
    db = SessionLocal()
    try:
        inserted = seed_words(db)
        print(f"Seeded {inserted} words")
    finally:
        db.close()


if __name__ == "__main__":
    main()
