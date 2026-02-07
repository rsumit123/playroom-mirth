import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.guest import Guest
from app.schemas.guest import GuestTokenResponse

router = APIRouter(tags=["guest"])


@router.post("/guest", response_model=GuestTokenResponse, status_code=201)
def create_guest(db: Session = Depends(get_db)):
    token = secrets.token_urlsafe(24)
    guest = Guest(guest_token=token)
    db.add(guest)
    db.commit()
    db.refresh(guest)
    return GuestTokenResponse(guest_token=guest.guest_token)
