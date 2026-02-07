def test_register_and_login(client):
    register_res = client.post("/register", json={"email": "a@example.com", "password": "secret"})
    assert register_res.status_code == 201
    assert register_res.json()["email"] == "a@example.com"

    login_res = client.post(
        "/token",
        data={"username": "a@example.com", "password": "secret"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_res.status_code == 200
    body = login_res.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"


def test_register_duplicate_email(client):
    first = client.post("/register", json={"email": "dup@example.com", "password": "secret"})
    assert first.status_code == 201

    second = client.post("/register", json={"email": "dup@example.com", "password": "secret"})
    assert second.status_code == 400


def test_guest_token_creation(client):
    res = client.post("/guest")
    assert res.status_code == 201
    body = res.json()
    assert "guest_token" in body
