"""Tests for the friends system: requests, accept, reject, list, search."""
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


def test_send_friend_request(client):
    uid_a, tok_a = _create_user("alice@x.com", "Alice")
    uid_b, tok_b = _create_user("bob@x.com", "Bob")

    res = client.post("/friends/request", json={"user_id": uid_b}, headers=_auth(tok_a))
    assert res.status_code == 201
    assert res.json()["status"] == "pending"


def test_accept_friend_request(client):
    uid_a, tok_a = _create_user("alice@x.com", "Alice")
    uid_b, tok_b = _create_user("bob@x.com", "Bob")

    client.post("/friends/request", json={"user_id": uid_b}, headers=_auth(tok_a))
    res = client.post(f"/friends/{uid_a}/accept", headers=_auth(tok_b))
    assert res.status_code == 200
    assert res.json()["ok"] is True

    # Both see each other in friends list
    friends_a = client.get("/friends", headers=_auth(tok_a)).json()["friends"]
    friends_b = client.get("/friends", headers=_auth(tok_b)).json()["friends"]
    assert len(friends_a) == 1 and friends_a[0]["id"] == uid_b
    assert len(friends_b) == 1 and friends_b[0]["id"] == uid_a


def test_reject_friend_request(client):
    uid_a, tok_a = _create_user("alice@x.com", "Alice")
    uid_b, tok_b = _create_user("bob@x.com", "Bob")

    client.post("/friends/request", json={"user_id": uid_b}, headers=_auth(tok_a))
    res = client.post(f"/friends/{uid_a}/reject", headers=_auth(tok_b))
    assert res.status_code == 200

    assert len(client.get("/friends/requests", headers=_auth(tok_b)).json()["requests"]) == 0
    assert len(client.get("/friends", headers=_auth(tok_a)).json()["friends"]) == 0


def test_list_pending_requests(client):
    uid_a, tok_a = _create_user("alice@x.com", "Alice")
    uid_b, tok_b = _create_user("bob@x.com", "Bob")

    client.post("/friends/request", json={"user_id": uid_b}, headers=_auth(tok_a))

    requests = client.get("/friends/requests", headers=_auth(tok_b)).json()["requests"]
    assert len(requests) == 1
    assert requests[0]["id"] == uid_a
    assert requests[0]["display_name"] == "Alice"


def test_duplicate_request_idempotent(client):
    uid_a, tok_a = _create_user("alice@x.com", "Alice")
    uid_b, tok_b = _create_user("bob@x.com", "Bob")

    res1 = client.post("/friends/request", json={"user_id": uid_b}, headers=_auth(tok_a))
    res2 = client.post("/friends/request", json={"user_id": uid_b}, headers=_auth(tok_a))
    assert res1.status_code == 201
    assert res2.status_code == 201
    assert res2.json()["status"] == "pending"


def test_cannot_friend_self(client):
    uid_a, tok_a = _create_user("alice@x.com", "Alice")

    res = client.post("/friends/request", json={"user_id": uid_a}, headers=_auth(tok_a))
    assert res.status_code == 400
    assert "yourself" in res.json()["detail"].lower()


def test_mutual_request_auto_accepts(client):
    uid_a, tok_a = _create_user("alice@x.com", "Alice")
    uid_b, tok_b = _create_user("bob@x.com", "Bob")

    client.post("/friends/request", json={"user_id": uid_b}, headers=_auth(tok_a))
    res = client.post("/friends/request", json={"user_id": uid_a}, headers=_auth(tok_b))
    assert res.json()["status"] == "accepted"

    assert len(client.get("/friends", headers=_auth(tok_a)).json()["friends"]) == 1


def test_reject_allows_re_request(client):
    uid_a, tok_a = _create_user("alice@x.com", "Alice")
    uid_b, tok_b = _create_user("bob@x.com", "Bob")

    client.post("/friends/request", json={"user_id": uid_b}, headers=_auth(tok_a))
    client.post(f"/friends/{uid_a}/reject", headers=_auth(tok_b))

    res = client.post("/friends/request", json={"user_id": uid_b}, headers=_auth(tok_a))
    assert res.status_code == 201
    assert res.json()["status"] == "pending"


def test_remove_accepted_friend(client):
    uid_a, tok_a = _create_user("alice@x.com", "Alice")
    uid_b, tok_b = _create_user("bob@x.com", "Bob")

    client.post("/friends/request", json={"user_id": uid_b}, headers=_auth(tok_a))
    client.post(f"/friends/{uid_a}/accept", headers=_auth(tok_b))
    assert len(client.get("/friends", headers=_auth(tok_a)).json()["friends"]) == 1

    client.post(f"/friends/{uid_b}/reject", headers=_auth(tok_a))
    assert len(client.get("/friends", headers=_auth(tok_a)).json()["friends"]) == 0
    assert len(client.get("/friends", headers=_auth(tok_b)).json()["friends"]) == 0


def test_request_nonexistent_user(client):
    _, tok_a = _create_user("alice@x.com", "Alice")
    res = client.post("/friends/request", json={"user_id": 99999}, headers=_auth(tok_a))
    assert res.status_code == 404


def test_user_search(client):
    _, tok_a = _create_user("alice@x.com", "Alice Smith")
    _, tok_b = _create_user("bob@x.com", "Bob Jones")
    _create_user("charlie@x.com", "Alice Jones")

    res = client.get("/users/search?q=Alice", headers=_auth(tok_b))
    assert res.status_code == 200
    names = [u["display_name"] for u in res.json()["users"]]
    assert "Alice Smith" in names
    assert "Alice Jones" in names
    assert "Bob Jones" not in names


def test_user_search_excludes_self(client):
    _, tok_a = _create_user("alice@x.com", "Alice")

    res = client.get("/users/search?q=Alice", headers=_auth(tok_a))
    assert len(res.json()["users"]) == 0


def test_friends_requires_auth(client):
    assert client.get("/friends").status_code == 401
    assert client.get("/friends/requests").status_code == 401
    assert client.post("/friends/request", json={"user_id": 1}).status_code == 401
    assert client.post("/friends/1/accept").status_code == 401
    assert client.get("/users/search?q=test").status_code == 401


def test_accept_nonexistent_request(client):
    uid_a, tok_a = _create_user("alice@x.com", "Alice")
    uid_b, tok_b = _create_user("bob@x.com", "Bob")

    res = client.post(f"/friends/{uid_a}/accept", headers=_auth(tok_b))
    assert res.status_code == 404
