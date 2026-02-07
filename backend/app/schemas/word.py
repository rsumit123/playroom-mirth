from pydantic import BaseModel


class WordCreateRequest(BaseModel):
    text: str
    difficulty: int


class WordUpdateRequest(BaseModel):
    text: str | None = None
    difficulty: int | None = None
    active: bool | None = None


class WordOut(BaseModel):
    id: int
    text: str
    difficulty: int
    active: bool

    class Config:
        from_attributes = True
