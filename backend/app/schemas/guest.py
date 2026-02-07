from pydantic import BaseModel


class GuestTokenResponse(BaseModel):
    guest_token: str
