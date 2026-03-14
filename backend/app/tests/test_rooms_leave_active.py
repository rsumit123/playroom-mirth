"""Tests for REST room leave and active rooms endpoints."""
from app.db.session import SessionLocal
from app.models.user import User
from app.services.auth import create_access_token


def _create_user_and_token(email):
    db = SessionLocal()
    try:
        user = User(email=email, google_id=f"google-{email}")
        db.add(user)
        db.commit()
        db.refresh(user)
        return create_access_token(str(user.id))
    finally:
        db.close()


def _create_room(client, token):
    return client.post(
        "/rooms",
        json={"rounds_total": 1, "difficulty": 1, "turn_seconds": 60, "max_players": 20},
        headers={"Authorization": f"Bearer {token}"},
    )


def test_leave_room_success(client):
    token = _create_user_and_token("leave-rest1@x.com")
    create = _create_room(client, token)
    room_code = create.json()["room"]["code"]

    res = client.post(
        f"/rooms/{room_code}/leave",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200


def test_leave_room_not_found(client):
    token = _create_user_and_token("leave-rest2@x.com")
    res = client.post(
        "/rooms/XXXXXX/leave",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code in (404, 400)


def test_leave_room_guest(client):
    guest = client.post("/guest")
    guest_token = guest.json()["guest_token"]
    create = client.post(
        "/rooms/guest",
        json={"guest_token": guest_token, "rounds_total": 1, "difficulty": 1, "turn_seconds": 60, "max_players": 10},
    )
    room_code = create.json()["room"]["code"]

    res = client.post(f"/rooms/{room_code}/leave?guest_token={guest_token}")
    assert res.status_code == 200


def test_active_rooms_returns_list(client):
    token = _create_user_and_token("active-rooms1@x.com")
    _create_room(client, token)

    res = client.get(
        "/rooms/active",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_active_rooms_empty_for_new_user(client):
    token = _create_user_and_token("active-rooms2@x.com")
    res = client.get(
        "/rooms/active",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json() == []


def test_active_rooms_guest(client):
    guest = client.post("/guest")
    guest_token = guest.json()["guest_token"]
    create = client.post(
        "/rooms/guest",
        json={"guest_token": guest_token, "rounds_total": 1, "difficulty": 1, "turn_seconds": 60, "max_players": 10},
    )
    assert create.status_code == 201

    res = client.get(f"/rooms/active?guest_token={guest_token}")
    assert res.status_code == 200
    assert len(res.json()) >= 1
