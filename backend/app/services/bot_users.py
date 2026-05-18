"""Bot user pool used as opponents in Quick Play matches.

Bots are real User rows flagged with is_bot=True so existing display-name
resolution, RoomPlayer joins, and scoring all work unchanged.
"""

import random

from sqlalchemy.orm import Session

from app.models.user import User


BOT_NAMES: list[str] = [
    "Priya", "Arjun", "Ananya", "Rohan", "Kavya", "Aditya",
    "Diya", "Vihaan", "Saanvi", "Krishna", "Ishaan", "Aaradhya",
    "Aanya", "Reyansh", "Myra", "Vivaan", "Aarav", "Anika",
    "Atharv", "Pari", "Kabir", "Sara", "Yash", "Tara",
    "Ved", "Riya", "Dev", "Aisha", "Aryan", "Meera",
]


def _bot_google_id(name: str) -> str:
    return f"bot-{name.lower()}"


def _bot_email(name: str) -> str:
    return f"bot_{name.lower()}@quickmatch.local"


def seed_bot_users(db: Session) -> None:
    """Insert any missing bot users. Idempotent."""
    existing_ids = {
        gid for (gid,) in db.query(User.google_id)
        .filter(User.is_bot == True).all()  # noqa: E712
    }
    for name in BOT_NAMES:
        gid = _bot_google_id(name)
        if gid in existing_ids:
            continue
        db.add(User(
            email=_bot_email(name),
            google_id=gid,
            display_name=name,
            password_hash="",
            is_bot=True,
        ))
    db.commit()


def pick_random_bot(db: Session, exclude_user_ids: set[int] | None = None) -> User:
    """Return a random bot user. exclude_user_ids skips bots already in use."""
    q = db.query(User).filter(User.is_bot == True)  # noqa: E712
    if exclude_user_ids:
        q = q.filter(~User.id.in_(exclude_user_ids))
    bots = q.all()
    if not bots:
        # Fallback if exclusion empties the pool — same bot in two rooms is fine.
        bots = db.query(User).filter(User.is_bot == True).all()  # noqa: E712
    return random.choice(bots)
