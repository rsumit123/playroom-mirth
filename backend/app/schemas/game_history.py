from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class GameHistoryOut(BaseModel):
    id: int
    game_type: str
    score: int
    player_count: int
    is_winner: bool
    played_at: datetime
    room_code: str
    origin: str = "friends"

    model_config = {"from_attributes": True}


class GameTypeStats(BaseModel):
    """Per-(game_type, origin) summary used by the history page header."""
    game_type: str
    origin: str
    games_played: int
    wins: int
    losses: int


class GameHistoryStats(BaseModel):
    total_games: int
    total_wins: int
    by_game_type: List[GameTypeStats]
    by_origin: Dict[str, int]


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    display_name: str
    avatar_url: Optional[str] = None
    wins: int
    games_played: int


class LeaderboardOut(BaseModel):
    """Top N leaderboard plus the requesting user's own rank if they're not in
    the top slice. `you` is None when the caller has never played a qualifying
    game."""
    top: List[LeaderboardEntry]
    you: Optional[LeaderboardEntry] = None
    current_streak: int = 0  # consecutive wins from the user's most-recent game backward
