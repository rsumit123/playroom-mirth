from datetime import datetime
from sqlalchemy import DateTime, Integer, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class RoomPlayer(Base):
    __tablename__ = "room_players"

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    guest_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    join_order: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    connected: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    in_game: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Poker: which model is sitting here, when the seat holds a house player.
    ai_tier: Mapped[str | None] = mapped_column(String(10), nullable=True)
