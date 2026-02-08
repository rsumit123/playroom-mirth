from unittest.mock import patch


def test_google_login_creates_user(client):
    mock_token_info = {
        "sub": "google-123",
        "email": "test@gmail.com",
        "name": "Test User",
        "picture": "https://lh3.googleusercontent.com/photo.jpg",
    }

    with patch("app.services.auth.google_id_token.verify_oauth2_token", return_value=mock_token_info):
        res = client.post("/auth/google", json={"id_token": "fake-token"})

    assert res.status_code == 200
    body = res.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "test@gmail.com"
    assert body["user"]["display_name"] == "Test User"
    assert body["user"]["avatar_url"] == "https://lh3.googleusercontent.com/photo.jpg"


def test_google_login_returns_existing_user(client):
    mock_token_info = {
        "sub": "google-456",
        "email": "existing@gmail.com",
        "name": "Existing User",
        "picture": "https://lh3.googleusercontent.com/existing.jpg",
    }

    with patch("app.services.auth.google_id_token.verify_oauth2_token", return_value=mock_token_info):
        # First login creates user
        res1 = client.post("/auth/google", json={"id_token": "fake-token-1"})
        user_id_1 = res1.json()["user"]["id"]

        # Second login returns same user
        res2 = client.post("/auth/google", json={"id_token": "fake-token-2"})
        user_id_2 = res2.json()["user"]["id"]

    assert user_id_1 == user_id_2


def test_google_login_invalid_token(client):
    with patch("app.services.auth.google_id_token.verify_oauth2_token", side_effect=ValueError("Invalid token")):
        res = client.post("/auth/google", json={"id_token": "bad-token"})

    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid Google token"


def test_guest_token_creation(client):
    res = client.post("/guest")
    assert res.status_code == 201
    body = res.json()
    assert "guest_token" in body
