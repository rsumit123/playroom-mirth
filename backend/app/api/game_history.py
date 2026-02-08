from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.game_history import GameHistory
from app.models.user import User
from app.schemas.game_history import GameHistoryOut

router = APIRouter(prefix="/game-history", tags=["game-history"])


@router.get("", response_model=List[GameHistoryOut])
def get_game_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(GameHistory)
        .filter(GameHistory.user_id == user.id)
        .order_by(GameHistory.played_at.desc())
        .limit(10)
        .all()
    )
    return rows
