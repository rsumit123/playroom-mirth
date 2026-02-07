from app.db.session import SessionLocal
from app.db.seed_words import seed_words
from app.models.word import Word


def test_seed_words_inserts_minimum():
    db = SessionLocal()
    try:
        inserted = seed_words(db)
        count = db.query(Word).count()
        assert count >= 100
        assert inserted >= 0
    finally:
        db.close()
