from typing import Optional
from pydantic import BaseModel


class GoogleAuthRequest(BaseModel):
    id_token: str


class GoogleAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "GoogleUserInfo"


class GoogleUserInfo(BaseModel):
    id: int
    email: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True
