from app.db.session import SessionLocal
from app.models.user import User
from app.services.bot_users import BOT_NAMES, seed_bot_users, pick_random_bot


def test_bot_users_seeded():
    db = SessionLocal()
    try:
        seed_bot_users(db)
        names = {n for n in BOT_NAMES}
        seeded = db.query(User).filter(User.is_bot == True).all()
        assert len(seeded) >= len(names)
        assert {u.email.split("@")[0].replace("bot_", "") for u in seeded} >= {n.lower() for n in names}
    finally:
        db.close()


def test_bot_seeding_is_idempotent():
    db = SessionLocal()
    try:
        seed_bot_users(db)
        seed_bot_users(db)
        seed_bot_users(db)
        count = db.query(User).filter(User.is_bot == True).count()
        assert count == len(BOT_NAMES)
    finally:
        db.close()


def test_pick_random_bot_returns_is_bot_user():
    db = SessionLocal()
    try:
        seed_bot_users(db)
        bot = pick_random_bot(db)
        assert bot.is_bot is True
    finally:
        db.close()
