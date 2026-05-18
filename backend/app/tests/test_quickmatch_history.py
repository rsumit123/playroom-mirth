import uuid

import pytest

from app.db.session import SessionLocal
from app.models.game_history import GameHistory
from app.models.room import Room
from app.models.room_player import RoomPlayer
from app.models.user import User
from app.services.bot_users import seed_bot_users
from app.sockets.events import _save_game_history
from app.services.game_state import RoomGameState


def test_save_game_history_copies_room_origin():
    db = SessionLocal()
    try:
        seed_bot_users(db)
        suffix = uuid.uuid4().hex[:8]
        host = User(email=f"hist-{suffix}@example.com", google_id=f"g-hist-{suffix}")
        db.add(host)
        db.commit()
        db.refresh(host)

        room_code = f"QMH{suffix[:3].upper()}"
        r = Room(code=room_code, host_user_id=host.id, status="active",
                 rounds_total=1, difficulty=1, turn_seconds=60,
                 max_players=2, min_players=2, origin="quickmatch",
                 game_type="trivia")
        db.add(r)
        db.commit()
        db.refresh(r)

        rp = RoomPlayer(room_id=r.id, user_id=host.id, join_order=1, score=0,
                        connected=True, in_game=True)
        db.add(rp)
        db.commit()
        db.refresh(rp)

        state = RoomGameState(room_id=r.id, room_code=r.code,
                              rounds_total=1, turn_seconds=60, difficulty=1,
                              origin="quickmatch", game_type="trivia")
        state.scores = {rp.id: 100}
        state.player_order = [rp.id]
        _save_game_history(db, state)
        db.commit()

        rows = db.query(GameHistory).filter(GameHistory.room_code == room_code).all()
        assert rows
        for row in rows:
            assert row.origin == "quickmatch"
    finally:
        db.close()
