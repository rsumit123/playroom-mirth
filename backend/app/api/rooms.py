import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user_optional
from app.models.room import Room
from app.models.room_player import RoomPlayer
from app.schemas.room import RoomCreateRequest, RoomCreateGuestRequest, RoomJoinRequest, RoomUpdateRequest, LobbyState
from typing import List

from app.services.room_ops import (
    resolve_guest,
    create_room_for_user,
    create_room_for_guest,
    join_room as join_room_op,
    lobby_state,
    get_active_rooms,
    leave_room_by_code,
)

_logger = logging.getLogger(__name__)

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


@router.get("/active", response_model=List[dict])
def get_active_rooms_endpoint(
    guest_token: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    guest = resolve_guest(db, guest_token)
    if not user and not guest:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return get_active_rooms(db, user.id if user else None, guest)


@router.post("/{room_code}/leave", status_code=200)
def leave_room_endpoint(
    room_code: str,
    guest_token: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    guest = resolve_guest(db, guest_token)
    if not user and not guest:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    leave_room_by_code(db, room_code, user.id if user else None, guest)
    return {"ok": True}


@router.get("/{room_code}", response_model=LobbyState)
def get_room(
    room_code: str,
    guest_token: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    room = db.query(Room).filter(Room.code == room_code).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    # Resolve self_player_id from auth
    self_player_id = None
    if user:
        rp = db.query(RoomPlayer).filter(RoomPlayer.room_id == room.id, RoomPlayer.user_id == user.id).first()
        if rp:
            self_player_id = rp.id
    elif guest_token:
        guest = resolve_guest(db, guest_token)
        if guest:
            rp = db.query(RoomPlayer).filter(RoomPlayer.room_id == room.id, RoomPlayer.guest_id == guest.id).first()
            if rp:
                self_player_id = rp.id
    return lobby_state(db, room, self_player_id=self_player_id)


@router.put("/{room_code}/settings", response_model=LobbyState)
def update_room_settings(
    room_code: str,
    payload: RoomUpdateRequest,
    guest_token: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    room = db.query(Room).filter(Room.code == room_code).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    guest = resolve_guest(db, guest_token)
    if user:
        if room.host_user_id != user.id:
            raise HTTPException(status_code=403, detail="Only host can update settings")
    elif guest:
        if room.host_guest_id != guest.id:
            raise HTTPException(status_code=403, detail="Only host can update settings")
    else:
        raise HTTPException(status_code=401, detail="Authentication required")

    room.rounds_total = payload.rounds_total
    room.difficulty = payload.difficulty
    room.turn_seconds = payload.turn_seconds
    room.trivia_category = payload.trivia_category
    db.commit()
    return lobby_state(db, room)


# ── Play-again vote tracking ──────────────────────────────────────────
# Separate from socket handler — uses its own dict so we can track result status.
# Structure: room_code -> {player_ids: set, total: int, status: "waiting"|"ready"|"expired", task: asyncio.Task}
PLAY_AGAIN_REST: dict[str, dict] = {}


@router.post("/{room_code}/play-again")
async def play_again_vote(
    room_code: str,
    guest_token: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    """REST endpoint for play-again votes."""
    room = db.query(Room).filter(Room.code == room_code).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    guest = resolve_guest(db, guest_token)
    if not user and not guest:
        raise HTTPException(status_code=401, detail="Authentication required")

    if user:
        rp = db.query(RoomPlayer).filter(RoomPlayer.room_id == room.id, RoomPlayer.user_id == user.id).first()
    else:
        rp = db.query(RoomPlayer).filter(RoomPlayer.room_id == room.id, RoomPlayer.guest_id == guest.id).first()

    if not rp:
        raise HTTPException(status_code=403, detail="Not in this room")

    player_id = rp.id
    all_players = db.query(RoomPlayer).filter(RoomPlayer.room_id == room.id).all()
    total = len(all_players)

    _logger.info(f"[play_again REST] player_id={player_id} total={total}")

    # If a previous vote already completed, return that result
    existing = PLAY_AGAIN_REST.get(room_code)
    if existing and existing.get("status") in ("ready", "expired"):
        return {"ok": True, "status": existing["status"], "voted": len(existing["player_ids"]), "total": existing["total"]}

    # Initialize vote tracking for this room if needed
    if room_code not in PLAY_AGAIN_REST:
        PLAY_AGAIN_REST[room_code] = {"player_ids": set(), "total": total, "status": "waiting"}

        # Start 30-second timeout
        async def _play_again_timeout():
            await asyncio.sleep(30)
            votes = PLAY_AGAIN_REST.get(room_code)
            if votes and votes["status"] == "waiting":
                votes["status"] = "expired"
                _logger.info(f"[play_again REST] TIMEOUT for {room_code}")

        PLAY_AGAIN_REST[room_code]["task"] = asyncio.ensure_future(_play_again_timeout())

    votes = PLAY_AGAIN_REST[room_code]
    if votes["status"] != "waiting":
        return {"ok": True, "status": votes["status"], "voted": len(votes["player_ids"]), "total": votes["total"]}

    votes["player_ids"].add(player_id)
    votes["total"] = total
    voted = len(votes["player_ids"])

    _logger.info(f"[play_again REST] voted={voted}/{total}")

    if voted >= total:
        # All players agreed
        task = votes.get("task")
        if task and not task.done():
            task.cancel()
        votes["status"] = "ready"

        # Re-enable in_game for all players so game:start can find them
        db.query(RoomPlayer).filter(
            RoomPlayer.room_id == room.id,
        ).update({RoomPlayer.in_game: True})
        db.commit()

        _logger.info(f"[play_again REST] ALL voted — ready for {room_code}")
        return {"ok": True, "status": "ready", "voted": voted, "total": total}
    else:
        _logger.info(f"[play_again REST] waiting — {voted}/{total}")
        return {"ok": True, "status": "waiting", "voted": voted, "total": total}


@router.get("/{room_code}/play-again")
def play_again_status(
    room_code: str,
    db: Session = Depends(get_db),
):
    """Poll play-again vote status."""
    room = db.query(Room).filter(Room.code == room_code).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    votes = PLAY_AGAIN_REST.get(room_code)
    if not votes:
        return {"status": "none", "voted": 0, "total": 0}

    return {"status": votes["status"], "voted": len(votes["player_ids"]), "total": votes["total"]}
