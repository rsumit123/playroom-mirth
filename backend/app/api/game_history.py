from typing import List, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.game_history import GameHistory
from app.models.user import User
from app.schemas.game_history import (
    GameHistoryOut,
    GameHistoryStats,
    GameTypeStats,
)

router = APIRouter(prefix="/game-history", tags=["game-history"])

OriginFilter = Literal["all", "friends", "quickmatch"]


def _apply_origin(q, origin: OriginFilter):
    if origin == "all":
        return q
    return q.filter(GameHistory.origin == origin)


@router.get("", response_model=List[GameHistoryOut])
def get_game_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    origin: OriginFilter = Query(
        "friends",
        description="Filter by origin. Default 'friends' keeps the historical home-page behavior; pass 'all' or 'quickmatch' for the dedicated history page.",
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    q = db.query(GameHistory).filter(GameHistory.user_id == user.id)
    q = _apply_origin(q, origin)
    rows = q.order_by(GameHistory.played_at.desc()).offset(offset).limit(limit).all()
    return rows


@router.get("/stats", response_model=GameHistoryStats)
def get_game_history_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    origin: OriginFilter = Query("all"),
):
    """Aggregate W/L summary keyed by (game_type, origin) plus per-origin totals.

    Drives the header stats card on the history page. Cheap query — single
    grouped scan + a small per-origin tally."""
    base = db.query(GameHistory).filter(GameHistory.user_id == user.id)
    base = _apply_origin(base, origin)

    wins_expr = func.sum(case((GameHistory.is_winner.is_(True), 1), else_=0))
    grouped = (
        base.with_entities(
            GameHistory.game_type,
            GameHistory.origin,
            func.count(GameHistory.id).label("games"),
            wins_expr.label("wins"),
        )
        .group_by(GameHistory.game_type, GameHistory.origin)
        .all()
    )

    by_game_type: List[GameTypeStats] = []
    by_origin: dict[str, int] = {}
    total_games = 0
    total_wins = 0
    for row in grouped:
        # SQLite returns booleans as 0/1 ints — sum() yields int. Coerce defensively.
        games = int(row.games or 0)
        wins = int(row.wins or 0)
        losses = games - wins
        by_game_type.append(
            GameTypeStats(
                game_type=row.game_type,
                origin=row.origin,
                games_played=games,
                wins=wins,
                losses=losses,
            )
        )
        by_origin[row.origin] = by_origin.get(row.origin, 0) + games
        total_games += games
        total_wins += wins

    # Sort so the UI gets a stable order: most-played game type first, then origin.
    by_game_type.sort(key=lambda s: (-s.games_played, s.game_type, s.origin))

    return GameHistoryStats(
        total_games=total_games,
        total_wins=total_wins,
        by_game_type=by_game_type,
        by_origin=by_origin,
    )
