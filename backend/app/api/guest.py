import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.guest import Guest
from app.schemas.guest import GuestCreateRequest, GuestTokenResponse

router = APIRouter(tags=["guest"])


@router.post("/guest", response_model=GuestTokenResponse, status_code=201)
def create_guest(payload: Optional[GuestCreateRequest] = None, db: Session = Depends(get_db)):
    display_name = None
    if payload and payload.display_name:
        display_name = payload.display_name.strip()[:30]

    token = secrets.token_urlsafe(24)
    guest = Guest(guest_token=token, display_name=display_name)
    db.add(guest)
    db.commit()
    db.refresh(guest)
    return GuestTokenResponse(guest_token=guest.guest_token, display_name=guest.display_name)


@router.patch("/guest", response_model=GuestTokenResponse)
def update_guest_name(
    payload: GuestCreateRequest,
    guest_token: str = Query(...),
    db: Session = Depends(get_db),
):
    guest = db.query(Guest).filter(Guest.guest_token == guest_token).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    if payload.display_name:
        guest.display_name = payload.display_name.strip()[:30]
    db.commit()
    db.refresh(guest)
    return GuestTokenResponse(guest_token=guest.guest_token, display_name=guest.display_name)
