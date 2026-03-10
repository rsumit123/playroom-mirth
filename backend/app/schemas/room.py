from typing import Optional, List

from pydantic import BaseModel


class RoomCreateRequest(BaseModel):
    rounds_total: int
    difficulty: int
    turn_seconds: int
    max_players: int = 20
    game_type: str = "charades"
    trivia_category: str = "math"


class RoomCreateGuestRequest(RoomCreateRequest):
    guest_token: str


class RoomUpdateRequest(BaseModel):
    rounds_total: int
    difficulty: int
    turn_seconds: int
    trivia_category: str = "math"


class RoomJoinRequest(BaseModel):
    room_code: str
    guest_token: Optional[str] = None


class RoomOut(BaseModel):
    id: int
    code: str
    status: str
    max_players: int
    min_players: int
    rounds_total: int
    difficulty: int
    turn_seconds: int
    game_type: str = "charades"
    trivia_category: str = "math"

    class Config:
        from_attributes = True


class LobbyPlayer(BaseModel):
    id: int
    user_id: Optional[int]
    guest_id: Optional[int]
    join_order: int
    score: int
    connected: bool
    in_game: bool
    display_name: str = "Player"

    class Config:
        from_attributes = True


class LobbyState(BaseModel):
    room: RoomOut
    players: List[LobbyPlayer]
    self_player_id: int | None = None
    host_player_id: int | None = None
