from pydantic import BaseModel


class WordCreateRequest(BaseModel):
    text: str
    difficulty: int
    game_type: str = "charades"


class WordUpdateRequest(BaseModel):
    text: str | None = None
    difficulty: int | None = None
    active: bool | None = None
    game_type: str | None = None


class WordOut(BaseModel):
    id: int
    text: str
    difficulty: int
    active: bool
    game_type: str

    class Config:
        from_attributes = True
