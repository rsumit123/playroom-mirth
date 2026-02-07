import random
import string

from sqlalchemy.orm import Session

from app.models.room import Room
from app.models.room_player import RoomPlayer


def generate_room_code(db: Session, length: int = 6) -> str:
    charset = string.ascii_uppercase + string.digits
    while True:
        code = "".join(random.choice(charset) for _ in range(length))
        exists = db.query(Room).filter(Room.code == code).first()
        if not exists:
            return code


def next_join_order(db: Session, room_id: int) -> int:
    last = (
        db.query(RoomPlayer)
        .filter(RoomPlayer.room_id == room_id)
        .order_by(RoomPlayer.join_order.desc())
        .first()
    )
    return (last.join_order + 1) if last else 1
