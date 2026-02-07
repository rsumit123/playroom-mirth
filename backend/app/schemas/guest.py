from typing import Optional

from pydantic import BaseModel, Field


class GuestCreateRequest(BaseModel):
    display_name: Optional[str] = Field(None, max_length=30, min_length=1)


class GuestTokenResponse(BaseModel):
    guest_token: str
    display_name: Optional[str] = None
