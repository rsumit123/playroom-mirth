import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.main import fastapi_app
from app.models.user import User
from app.models.guest import Guest
from app.models.room import Room
from app.models.room_player import RoomPlayer
from app.models.room_state import RoomState
from app.models.word import Word


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    init_db()


@pytest.fixture(autouse=True)
def clear_users():
    db = SessionLocal()
    try:
        db.query(RoomPlayer).delete()
        db.query(RoomState).delete()
        db.query(Room).delete()
        db.query(Guest).delete()
        db.query(Word).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture(autouse=True)
async def reset_game_state():
    from app.services.game_state import ROOM_STATES, SID_TO_PLAYER, PLAYER_TO_SID, cancel_all_timers

    ROOM_STATES.clear()
    SID_TO_PLAYER.clear()
    PLAYER_TO_SID.clear()
    yield
    await cancel_all_timers()
    ROOM_STATES.clear()
    SID_TO_PLAYER.clear()
    PLAYER_TO_SID.clear()


@pytest.fixture()
def client():
    return TestClient(fastapi_app)
