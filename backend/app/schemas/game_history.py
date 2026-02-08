from datetime import datetime
from pydantic import BaseModel


class GameHistoryOut(BaseModel):
    id: int
    game_type: str
    score: int
    player_count: int
    is_winner: bool
    played_at: datetime
    room_code: str

    model_config = {"from_attributes": True}
