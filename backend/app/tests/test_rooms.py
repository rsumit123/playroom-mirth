from app.db.session import SessionLocal
from app.models.user import User
from app.services.auth import create_access_token


def create_user_and_token(email: str):
    db = SessionLocal()
    try:
        user = User(email=email, google_id=f"google-{email}")
        db.add(user)
        db.commit()
        db.refresh(user)
        return create_access_token(str(user.id))
    finally:
        db.close()


def test_create_and_join_room(client):
    token = create_user_and_token("host@example.com")
    create = client.post(
        "/rooms",
        json={"rounds_total": 2, "difficulty": 1, "turn_seconds": 60, "max_players": 20},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create.status_code == 201
    room_code = create.json()["room"]["code"]
    assert create.json().get("self_player_id")

    guest = client.post("/guest")
    guest_token = guest.json()["guest_token"]
    join = client.post("/rooms/join", json={"room_code": room_code, "guest_token": guest_token})
    assert join.status_code == 200
    players = join.json()["players"]
    assert len(players) == 2
    assert join.json().get("self_player_id")


def test_guest_can_create_room(client):
    guest = client.post("/guest")
    guest_token = guest.json()["guest_token"]
    create = client.post(
        "/rooms/guest",
        json={
            "guest_token": guest_token,
            "rounds_total": 1,
            "difficulty": 2,
            "turn_seconds": 45,
            "max_players": 10,
        },
    )
    assert create.status_code == 201
    body = create.json()
    assert body["room"]["code"]
    assert len(body["players"]) == 1


def test_join_requires_auth_or_guest(client):
    token = create_user_and_token("host2@example.com")
    create = client.post(
        "/rooms",
        json={"rounds_total": 1, "difficulty": 1, "turn_seconds": 60, "max_players": 20},
        headers={"Authorization": f"Bearer {token}"},
    )
    room_code = create.json()["room"]["code"]

    res = client.post("/rooms/join", json={"room_code": room_code})
    assert res.status_code == 401


def test_join_active_room_sets_waiting(client):
    token = create_user_and_token("host6@example.com")
    create = client.post(
        "/rooms",
        json={"rounds_total": 1, "difficulty": 1, "turn_seconds": 60, "max_players": 20},
        headers={"Authorization": f"Bearer {token}"},
    )
    room_code = create.json()["room"]["code"]

    # manually set room status to active
    from app.models.room import Room
    db = SessionLocal()
    try:
        room = db.query(Room).filter(Room.code == room_code).first()
        room.status = "active"
        db.commit()
    finally:
        db.close()

    guest = client.post("/guest")
    guest_token = guest.json()["guest_token"]
    join = client.post("/rooms/join", json={"room_code": room_code, "guest_token": guest_token})
    assert join.status_code == 200
    assert join.json()["players"][-1]["in_game"] is False


def test_get_room_state(client):
    token = create_user_and_token("host3@example.com")
    create = client.post(
        "/rooms",
        json={"rounds_total": 1, "difficulty": 1, "turn_seconds": 60, "max_players": 20},
        headers={"Authorization": f"Bearer {token}"},
    )
    room_code = create.json()["room"]["code"]

    res = client.get(f"/rooms/{room_code}")
    assert res.status_code == 200


def test_update_room_settings_requires_host(client):
    token = create_user_and_token("host4@example.com")
    create = client.post(
        "/rooms",
        json={"rounds_total": 1, "difficulty": 1, "turn_seconds": 60, "max_players": 20},
        headers={"Authorization": f"Bearer {token}"},
    )
    room_code = create.json()["room"]["code"]

    # Another user should not update
    token2 = create_user_and_token("user2@example.com")
    res = client.put(
        f"/rooms/{room_code}/settings",
        json={"rounds_total": 2, "difficulty": 2, "turn_seconds": 45},
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert res.status_code == 403


def test_update_room_settings_success(client):
    token = create_user_and_token("host5@example.com")
    create = client.post(
        "/rooms",
        json={"rounds_total": 1, "difficulty": 1, "turn_seconds": 60, "max_players": 20},
        headers={"Authorization": f"Bearer {token}"},
    )
    room_code = create.json()["room"]["code"]

    res = client.put(
        f"/rooms/{room_code}/settings",
        json={"rounds_total": 3, "difficulty": 2, "turn_seconds": 90},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["room"]["rounds_total"] == 3
    assert body["room"]["difficulty"] == 2
    assert body["room"]["turn_seconds"] == 90
