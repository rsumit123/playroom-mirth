from datetime import datetime
from sqlalchemy import Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class RoomState(Base):
    __tablename__ = "room_state"

    room_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    state_json: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
