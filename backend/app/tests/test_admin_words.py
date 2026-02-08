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


def test_admin_word_crud(client):
    token = create_user_and_token("admin@example.com")
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
