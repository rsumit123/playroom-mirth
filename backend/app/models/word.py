from sqlalchemy import String, Integer, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Word(Base):
    __tablename__ = "words"
    __table_args__ = (UniqueConstraint("text", "game_type", name="uq_word_text_game_type"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(String(128), nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    game_type: Mapped[str] = mapped_column(String(20), default="charades", nullable=False)
