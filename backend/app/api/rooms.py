from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user_optional
from app.models.room import Room
from app.schemas.room import RoomCreateRequest, RoomCreateGuestRequest, RoomJoinRequest, RoomUpdateRequest, LobbyState
from app.services.room_ops import (
    resolve_guest,
    create_room_for_user,
    create_room_for_guest,
    join_room as join_room_op,
    lobby_state,
)

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post("", response_model=LobbyState, status_code=201)
def create_room(
    payload: RoomCreateRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return create_room_for_user(db, user.id, payload)


@router.post("/guest", response_model=LobbyState, status_code=201)
def create_room_guest(payload: RoomCreateGuestRequest, db: Session = Depends(get_db)):
    return create_room_for_guest(db, payload)


@router.post("/join", response_model=LobbyState)
def join_room(
    payload: RoomJoinRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    room = db.query(Room).filter(Room.code == payload.room_code).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    guest = resolve_guest(db, payload.guest_token)

    if not user and not guest:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return join_room_op(db, room, user.id if user else None, guest)


@router.get("/{room_code}", response_model=LobbyState)
def get_room(room_code: str, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.code == room_code).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return lobby_state(db, room)


@router.put("/{room_code}/settings", response_model=LobbyState)
def update_room_settings(
    room_code: str,
    payload: RoomUpdateRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    room = db.query(Room).filter(Room.code == room_code).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    if user:
        if room.host_user_id != user.id:
            raise HTTPException(status_code=403, detail="Only host can update settings")
    else:
        raise HTTPException(status_code=401, detail="Authentication required")

    room.rounds_total = payload.rounds_total
    room.difficulty = payload.difficulty
    room.turn_seconds = payload.turn_seconds
    db.commit()
    return lobby_state(db, room)
