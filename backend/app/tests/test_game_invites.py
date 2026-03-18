"""Tests for game invite system."""
from app.db.session import SessionLocal
from app.models.user import User
from app.services.auth import create_access_token


def _create_user(email, display_name=None):
    db = SessionLocal()
    try:
        user = User(email=email, google_id=f"google-{email}", display_name=display_name or email.split("@")[0])
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id, create_access_token(str(user.id))
    finally:
        db.close()


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _make_friends(client, uid_a, tok_a, uid_b, tok_b):
    client.post("/friends/request", json={"user_id": uid_b}, headers=_auth(tok_a))
    client.post(f"/friends/{uid_a}/accept", headers=_auth(tok_b))


def _create_room(client, token):
    return client.post(
        "/rooms",
        json={"rounds_total": 1, "difficulty": 1, "turn_seconds": 60, "max_players": 20},
        headers=_auth(token),
    ).json()["room"]["code"]


def test_invite_friend_to_room(client):
    uid_a, tok_a = _create_user("inv1a@x.com", "Alice")
    uid_b, tok_b = _create_user("inv1b@x.com", "Bob")
    _make_friends(client, uid_a, tok_a, uid_b, tok_b)

    room_code = _create_room(client, tok_a)
    res = client.post(f"/rooms/{room_code}/invite", json={"user_id": uid_b}, headers=_auth(tok_a))
    assert res.status_code == 201
    assert res.json()["status"] == "invited"


def test_invite_duplicate_is_idempotent(client):
    uid_a, tok_a = _create_user("inv2a@x.com", "Alice")
    uid_b, tok_b = _create_user("inv2b@x.com", "Bob")
    _make_friends(client, uid_a, tok_a, uid_b, tok_b)

    room_code = _create_room(client, tok_a)
    client.post(f"/rooms/{room_code}/invite", json={"user_id": uid_b}, headers=_auth(tok_a))
    res = client.post(f"/rooms/{room_code}/invite", json={"user_id": uid_b}, headers=_auth(tok_a))
    assert res.json()["status"] == "already_invited"


def test_invite_non_friend_rejected(client):
    uid_a, tok_a = _create_user("inv3a@x.com", "Alice")
    uid_b, tok_b = _create_user("inv3b@x.com", "Bob")
    # NOT friends

    room_code = _create_room(client, tok_a)
    res = client.post(f"/rooms/{room_code}/invite", json={"user_id": uid_b}, headers=_auth(tok_a))
    assert res.status_code == 403


def test_invite_invalid_room(client):
    uid_a, tok_a = _create_user("inv4a@x.com", "Alice")
    uid_b, tok_b = _create_user("inv4b@x.com", "Bob")
    _make_friends(client, uid_a, tok_a, uid_b, tok_b)

    res = client.post("/rooms/XXXXXX/invite", json={"user_id": uid_b}, headers=_auth(tok_a))
    assert res.status_code == 404


def test_invite_requires_auth(client):
    res = client.post("/rooms/ABC123/invite", json={"user_id": 1})
    assert res.status_code == 401


def test_notifications_empty(client):
    _, tok = _create_user("notif1@x.com", "Alice")
    res = client.get("/notifications", headers=_auth(tok))
    assert res.status_code == 200
    assert res.json()["total"] == 0
    assert res.json()["friend_requests"] == 0
    assert res.json()["game_invites"] == []


def test_notifications_shows_friend_request(client):
    uid_a, tok_a = _create_user("notif2a@x.com", "Alice")
    uid_b, tok_b = _create_user("notif2b@x.com", "Bob")

    client.post("/friends/request", json={"user_id": uid_b}, headers=_auth(tok_a))

    res = client.get("/notifications", headers=_auth(tok_b))
    assert res.json()["friend_requests"] == 1
    assert res.json()["total"] == 1


def test_notifications_shows_game_invite(client):
    uid_a, tok_a = _create_user("notif3a@x.com", "Alice")
    uid_b, tok_b = _create_user("notif3b@x.com", "Bob")
    _make_friends(client, uid_a, tok_a, uid_b, tok_b)

    room_code = _create_room(client, tok_a)
    client.post(f"/rooms/{room_code}/invite", json={"user_id": uid_b}, headers=_auth(tok_a))

    res = client.get("/notifications", headers=_auth(tok_b))
    assert res.json()["total"] == 1
    assert len(res.json()["game_invites"]) == 1
    invite = res.json()["game_invites"][0]
    assert invite["room_code"] == room_code
    assert invite["from_user"]["display_name"] == "Alice"


def test_notifications_combined(client):
    uid_a, tok_a = _create_user("notif4a@x.com", "Alice")
    uid_b, tok_b = _create_user("notif4b@x.com", "Bob")
    uid_c, tok_c = _create_user("notif4c@x.com", "Carol")

    # Carol sends friend request to Bob
    client.post("/friends/request", json={"user_id": uid_b}, headers=_auth(tok_c))

    # Alice and Bob are friends, Alice invites Bob
    _make_friends(client, uid_a, tok_a, uid_b, tok_b)
    room_code = _create_room(client, tok_a)
    client.post(f"/rooms/{room_code}/invite", json={"user_id": uid_b}, headers=_auth(tok_a))

    # Bob should see 1 friend request + 1 game invite = 2 total
    res = client.get("/notifications", headers=_auth(tok_b))
    assert res.json()["friend_requests"] == 1
    assert len(res.json()["game_invites"]) == 1
    assert res.json()["total"] == 2


def test_notifications_requires_auth(client):
    res = client.get("/notifications")
    assert res.status_code == 401


def test_invite_dismissed_on_room_join(client):
    uid_a, tok_a = _create_user("dismiss1a@x.com", "Alice")
    uid_b, tok_b = _create_user("dismiss1b@x.com", "Bob")
    _make_friends(client, uid_a, tok_a, uid_b, tok_b)

    room_code = _create_room(client, tok_a)
    client.post(f"/rooms/{room_code}/invite", json={"user_id": uid_b}, headers=_auth(tok_a))

    # Bob has 1 pending invite
    notif = client.get("/notifications", headers=_auth(tok_b)).json()
    assert len(notif["game_invites"]) == 1

    # Bob joins the room
    client.post("/rooms/join", json={"room_code": room_code}, headers=_auth(tok_b))

    # Invite should be dismissed (status = accepted)
    notif = client.get("/notifications", headers=_auth(tok_b)).json()
    assert len(notif["game_invites"]) == 0
