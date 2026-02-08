from datetime import datetime
from sqlalchemy import String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(6), unique=True, index=True, nullable=False)

    host_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    host_guest_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    status: Mapped[str] = mapped_column(String(16), default="lobby", nullable=False)
    max_players: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    min_players: Mapped[int] = mapped_column(Integer, default=2, nullable=False)

    rounds_total: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    turn_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    game_type: Mapped[str] = mapped_column(String(20), default="charades", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
