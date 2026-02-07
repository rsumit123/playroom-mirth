def register_and_login(client, email: str):
    reg = client.post("/register", json={"email": email, "password": "secret"})
    assert reg.status_code == 201
    login = client.post(
        "/token",
        data={"username": email, "password": "secret"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login.status_code == 200
    return login.json()["access_token"]


def test_admin_word_crud(client):
    token = register_and_login(client, "admin@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create = client.post("/admin/words", json={"text": "testword", "difficulty": 2}, headers=headers)
    assert create.status_code == 201
    word_id = create.json()["id"]

    update = client.patch(f"/admin/words/{word_id}", json={"active": False}, headers=headers)
    assert update.status_code == 200
    assert update.json()["active"] is False

    list_res = client.get("/admin/words", headers=headers)
    assert list_res.status_code == 200
    assert any(w["id"] == word_id for w in list_res.json())

    list_filtered = client.get("/admin/words?q=testword", headers=headers)
    assert list_filtered.status_code == 200
    assert any(w["text"] == "testword" for w in list_filtered.json())
