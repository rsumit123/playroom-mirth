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

    # Look up users for display names. Prefer the explicit display_name (set
    # from Google profile for signed-in users; "Priya"/"Rohan" etc. for bots);
    # fall back to the email local-part only if display_name is unset.
    user_ids = [p.user_id for p in players if p.user_id]
    user_map = {}
    if user_ids:
        users = db.query(User).filter(User.id.in_(user_ids)).all()
        user_map = {u.id: (u.display_name or u.email.split("@")[0]) for u in users}

    # Look up guest display names
    guest_ids = [p.guest_id for p in players if p.guest_id]
    guest_name_map = {}
    if guest_ids:
        guests = db.query(Guest).filter(Guest.id.in_(guest_ids)).all()
        guest_name_map = {g.id: g.display_name for g in guests if g.display_name}

    lobby_players = []
    guest_counter = 0
    for p in players:
        lp = LobbyPlayer.model_validate(p)
        if p.user_id and p.user_id in user_map:
            lp.display_name = user_map[p.user_id]
        elif p.guest_id and p.guest_id in guest_name_map:
            lp.display_name = guest_name_map[p.guest_id]
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
        game_type=payload.game_type,
        trivia_category=payload.trivia_category,
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
        game_type=payload.game_type,
        trivia_category=payload.trivia_category,
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

    # Check if user/guest already has a player in this room
    existing_rp = None
    if user_id:
        existing_rp = (
            db.query(RoomPlayer)
            .filter(RoomPlayer.room_id == room.id, RoomPlayer.user_id == user_id)
            .first()
        )
    elif guest:
        existing_rp = (
            db.query(RoomPlayer)
            .filter(RoomPlayer.room_id == room.id, RoomPlayer.guest_id == guest.id)
            .first()
        )

    if existing_rp:
        existing_rp.connected = True
        db.commit()
        return lobby_state(db, room, self_player_id=existing_rp.id)

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


def get_active_rooms(db: Session, user_id: int | None, guest: Guest | None) -> list[dict]:
    """Return rooms where user/guest has an active RoomPlayer."""
    if user_id:
        room_players = (
            db.query(RoomPlayer)
            .filter(
                RoomPlayer.user_id == user_id,
                (RoomPlayer.in_game.is_(True) | RoomPlayer.connected.is_(True)),
            )
            .all()
        )
    elif guest:
        room_players = (
            db.query(RoomPlayer)
            .filter(
                RoomPlayer.guest_id == guest.id,
                (RoomPlayer.in_game.is_(True) | RoomPlayer.connected.is_(True)),
            )
            .all()
        )
    else:
        return []

    if not room_players:
        return []

    room_ids = [rp.room_id for rp in room_players]
    rooms = db.query(Room).filter(Room.id.in_(room_ids)).all()
    room_map = {r.id: r for r in rooms}

    result = []
    for rp in room_players:
        room = room_map.get(rp.room_id)
        if not room:
            continue
        if room.status not in ("lobby", "active"):
            continue
        if room.origin == "quickmatch":
            continue
        player_count = db.query(RoomPlayer).filter(RoomPlayer.room_id == room.id).count()
        result.append({
            "room_code": room.code,
            "room_status": room.status,
            "player_count": player_count,
            "max_players": room.max_players,
            "game_type": room.game_type,
        })
    return result


def leave_room_by_code(db: Session, room_code: str, user_id: int | None, guest: Guest | None) -> bool:
    """Remove the user/guest from a room."""
    room = db.query(Room).filter(Room.code == room_code).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    rp = None
    if user_id:
        rp = db.query(RoomPlayer).filter(
            RoomPlayer.room_id == room.id, RoomPlayer.user_id == user_id
        ).first()
    elif guest:
        rp = db.query(RoomPlayer).filter(
            RoomPlayer.room_id == room.id, RoomPlayer.guest_id == guest.id
        ).first()

    if not rp:
        raise HTTPException(status_code=404, detail="Player not in room")

    rp.in_game = False
    rp.connected = False
    db.commit()
    return True
