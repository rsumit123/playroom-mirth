import pytest

from app.db.session import SessionLocal
from app.models.user import User
from app.services.auth import create_access_token
from app.services.bot_users import seed_bot_users


@pytest.fixture
def authed_client(client):
    db = SessionLocal()
    try:
        seed_bot_users(db)
        u = User(email="searcher@example.com", google_id="g-searcher",
                 display_name="Searcher")
        db.add(u)
        db.commit()
        db.refresh(u)
        token = create_access_token(str(u.id))
    finally:
        db.close()
    return client, token


def test_friend_search_excludes_bots(authed_client):
    c, token = authed_client
    # Search for a bot name prefix — should return nothing.
    # The actual endpoint is /users/search?q=<term>
    r = c.get("/users/search?q=Priya", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, f"unexpected status: {r.status_code} body: {r.text}"
    results = r.json()
    # Endpoint returns {"users": [...]}
    if isinstance(results, dict):
        results = results.get("results", results.get("users", []))

    # Look up each returned user id in the DB to verify none are bots.
    db = SessionLocal()
    try:
        returned_ids = [u.get("id") for u in results if u.get("id")]
        if returned_ids:
            bot_matches = (
                db.query(User)
                .filter(User.id.in_(returned_ids), User.is_bot == True)  # noqa: E712
                .all()
            )
            assert bot_matches == [], \
                f"Bot users appeared in search results: {[b.display_name for b in bot_matches]}"
    finally:
        db.close()
