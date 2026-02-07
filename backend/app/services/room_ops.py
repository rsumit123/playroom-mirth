from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.guest import Guest
from app.models.room import Room
from app.models.room_player import RoomPlayer
from app.models.user import User
from app.schemas.room import LobbyState, LobbyPlayer, RoomOut, RoomCreateRequest, RoomCreateGuestRequest
from app.services.rooms import generate_room_code, next_join_order


def resolve_guest(db: Session, guest_token: str | None) -> Guest | None:
    if not guest_token:
        return None
    return db.query(Guest).filter(Guest.guest_token == guest_token).first()


def ensure_user_can_join(db: Session, user_id: int | None, guest: Guest | None) -> None:
    if guest and guest.matches_played >= 1:
        raise HTTPException(status_code=403, detail="Guest limit reached")
    if user_id is not None:
        active_games = (
            db.query(RoomPlayer)
            .filter(RoomPlayer.user_id == user_id, RoomPlayer.in_game.is_(True))
            .count()
        )
        if active_games >= 3:
            raise HTTPException(status_code=403, detail="Active game limit reached")


def lobby_state(db: Session, room: Room, self_player_id: int | None = None) -> LobbyState:
    players = (
        db.query(RoomPlayer)
        .filter(RoomPlayer.room_id == room.id)
        .order_by(RoomPlayer.join_order.asc())
        .all()
    )
    host_player_id = None
    for p in players:
        if room.host_user_id and p.user_id == room.host_user_id:
            host_player_id = p.id
            break
        if room.host_guest_id and p.guest_id == room.host_guest_id:
            host_player_id = p.id
            break

    # Look up user emails for display names
    user_ids = [p.user_id for p in players if p.user_id]
    user_map = {}
    if user_ids:
        users = db.query(User).filter(User.id.in_(user_ids)).all()
        user_map = {u.id: u.email.split("@")[0] for u in users}

    lobby_players = []
    guest_counter = 0
    for p in players:
        lp = LobbyPlayer.model_validate(p)
        if p.user_id and p.user_id in user_map:
            lp.display_name = user_map[p.user_id]
        else:
            guest_counter += 1
            lp.display_name = f"Guest {guest_counter}"
        lobby_players.append(lp)

    return LobbyState(
        room=RoomOut.model_validate(room),
        players=lobby_players,
        self_player_id=self_player_id,
        host_player_id=host_player_id,
    )


def create_room_for_user(db: Session, user_id: int, payload: RoomCreateRequest) -> LobbyState:
    ensure_user_can_join(db, user_id, None)
    room = Room(
        code=generate_room_code(db),
        host_user_id=user_id,
        status="lobby",
        max_players=payload.max_players,
        rounds_total=payload.rounds_total,
        difficulty=payload.difficulty,
        turn_seconds=payload.turn_seconds,
    )
    db.add(room)
    db.commit()
    db.refresh(room)

    rp = RoomPlayer(
        room_id=room.id,
        user_id=user_id,
        guest_id=None,
        join_order=1,
        score=0,
        connected=True,
        in_game=True,
    )
    db.add(rp)
    db.commit()

    return lobby_state(db, room, self_player_id=rp.id)


def create_room_for_guest(db: Session, payload: RoomCreateGuestRequest) -> LobbyState:
    guest = resolve_guest(db, payload.guest_token)
    if not guest:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid guest token")

    ensure_user_can_join(db, None, guest)

    room = Room(
        code=generate_room_code(db),
        host_guest_id=guest.id,
        status="lobby",
        max_players=payload.max_players,
        rounds_total=payload.rounds_total,
        difficulty=payload.difficulty,
        turn_seconds=payload.turn_seconds,
    )
    db.add(room)
    db.commit()
    db.refresh(room)

    rp = RoomPlayer(
        room_id=room.id,
        user_id=None,
        guest_id=guest.id,
        join_order=1,
        score=0,
        connected=True,
        in_game=True,
    )
    db.add(rp)
    db.commit()

    return lobby_state(db, room, self_player_id=rp.id)


def join_room(db: Session, room: Room, user_id: int | None, guest: Guest | None) -> LobbyState:
    ensure_user_can_join(db, user_id, guest)

    current_count = db.query(RoomPlayer).filter(RoomPlayer.room_id == room.id).count()
    if current_count >= room.max_players:
        raise HTTPException(status_code=409, detail="Room is full")

    rp = RoomPlayer(
        room_id=room.id,
        user_id=user_id,
        guest_id=guest.id if guest else None,
        join_order=next_join_order(db, room.id),
        score=0,
        connected=True,
        in_game=(room.status == "lobby"),
    )
    db.add(rp)
    db.commit()

    return lobby_state(db, room, self_player_id=rp.id)
