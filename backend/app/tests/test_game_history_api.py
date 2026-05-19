"""Tests for the /game-history endpoint family."""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import fastapi_app
from app.models.game_history import GameHistory
from app.models.user import User
from app.services.auth import create_access_token


client = TestClient(fastapi_app)


def _make_user_with_token(label: str) -> tuple[User, str]:
    db = SessionLocal()
    try:
        suffix = uuid.uuid4().hex[:8]
        user = User(
            email=f"{label}-{suffix}@x.com",
            google_id=f"g-{label}-{suffix}",
            display_name=f"{label}-{suffix}",
            password_hash="",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user, create_access_token(subject=str(user.id))
    finally:
        db.close()


def _add_row(user_id: int, *, game_type: str, origin: str, is_winner: bool, score: int = 0, room_code: str | None = None) -> None:
    db = SessionLocal()
    try:
        db.add(GameHistory(
            user_id=user_id,
            room_code=room_code or f"R{uuid.uuid4().hex[:4].upper()}",
            game_type=game_type,
            score=score,
            player_count=2,
            is_winner=is_winner,
            display_name="Test",
            game_number=1,
            origin=origin,
        ))
        db.commit()
    finally:
        db.close()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------- Listing endpoint ----------

def test_default_origin_remains_friends_only_for_backward_compat():
    """The home-page card consumer relies on default filtering to friends.
    Don't change that behavior without bumping a query param explicitly."""
    user, token = _make_user_with_token("hist-default")
    _add_row(user.id, game_type="trivia", origin="friends", is_winner=True)
    _add_row(user.id, game_type="trivia", origin="quickmatch", is_winner=False)

    r = client.get("/game-history", headers=_auth(token))
    assert r.status_code == 200
    rows = r.json()
    origins = {row["origin"] for row in rows}
    assert origins == {"friends"}


def test_origin_all_returns_both_friends_and_quickmatch_rows():
    user, token = _make_user_with_token("hist-all")
    _add_row(user.id, game_type="trivia", origin="friends", is_winner=True)
    _add_row(user.id, game_type="trivia", origin="quickmatch", is_winner=True)

    r = client.get("/game-history?origin=all", headers=_auth(token))
    assert r.status_code == 200
    rows = r.json()
    origins = {row["origin"] for row in rows}
    assert "friends" in origins and "quickmatch" in origins


def test_origin_quickmatch_filters_to_quickmatch_only():
    user, token = _make_user_with_token("hist-qm")
    _add_row(user.id, game_type="trivia", origin="friends", is_winner=True)
    _add_row(user.id, game_type="trivia", origin="quickmatch", is_winner=False)
    _add_row(user.id, game_type="trivia", origin="quickmatch", is_winner=True)

    r = client.get("/game-history?origin=quickmatch", headers=_auth(token))
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 2
    assert all(row["origin"] == "quickmatch" for row in rows)


def test_invalid_origin_rejected():
    _, token = _make_user_with_token("hist-bad")
    r = client.get("/game-history?origin=hacked", headers=_auth(token))
    assert r.status_code == 422


def test_pagination_via_limit_and_offset():
    user, token = _make_user_with_token("hist-page")
    for _ in range(5):
        _add_row(user.id, game_type="trivia", origin="quickmatch", is_winner=False)

    page1 = client.get("/game-history?origin=quickmatch&limit=2&offset=0", headers=_auth(token)).json()
    page2 = client.get("/game-history?origin=quickmatch&limit=2&offset=2", headers=_auth(token)).json()
    page3 = client.get("/game-history?origin=quickmatch&limit=2&offset=4", headers=_auth(token)).json()

    assert len(page1) == 2 and len(page2) == 2 and len(page3) == 1
    ids = {row["id"] for row in page1 + page2 + page3}
    assert len(ids) == 5  # no overlap, no duplicates


def test_listing_includes_origin_field():
    user, token = _make_user_with_token("hist-origin-field")
    _add_row(user.id, game_type="trivia", origin="quickmatch", is_winner=True)
    r = client.get("/game-history?origin=quickmatch", headers=_auth(token)).json()
    assert r[0]["origin"] == "quickmatch"


# ---------- Stats endpoint ----------

def test_stats_groups_by_game_type_and_origin():
    user, token = _make_user_with_token("hist-stats")
    _add_row(user.id, game_type="trivia", origin="quickmatch", is_winner=True)
    _add_row(user.id, game_type="trivia", origin="quickmatch", is_winner=True)
    _add_row(user.id, game_type="trivia", origin="quickmatch", is_winner=False)
    _add_row(user.id, game_type="charades", origin="friends", is_winner=False)

    r = client.get("/game-history/stats?origin=all", headers=_auth(token))
    assert r.status_code == 200
    body = r.json()
    assert body["total_games"] == 4
    assert body["total_wins"] == 2

    trivia_qm = next(s for s in body["by_game_type"]
                     if s["game_type"] == "trivia" and s["origin"] == "quickmatch")
    assert trivia_qm["games_played"] == 3
    assert trivia_qm["wins"] == 2
    assert trivia_qm["losses"] == 1

    charades_friends = next(s for s in body["by_game_type"]
                            if s["game_type"] == "charades" and s["origin"] == "friends")
    assert charades_friends["games_played"] == 1
    assert charades_friends["wins"] == 0
    assert charades_friends["losses"] == 1

    assert body["by_origin"]["quickmatch"] == 3
    assert body["by_origin"]["friends"] == 1


def test_stats_filtered_by_origin_excludes_other_rows():
    user, token = _make_user_with_token("hist-stats-filt")
    _add_row(user.id, game_type="trivia", origin="friends", is_winner=True)
    _add_row(user.id, game_type="trivia", origin="quickmatch", is_winner=False)

    r = client.get("/game-history/stats?origin=quickmatch", headers=_auth(token)).json()
    assert r["total_games"] == 1
    assert r["total_wins"] == 0
    assert all(s["origin"] == "quickmatch" for s in r["by_game_type"])


def test_stats_empty_for_user_with_no_history():
    _, token = _make_user_with_token("hist-empty")
    r = client.get("/game-history/stats?origin=all", headers=_auth(token)).json()
    assert r["total_games"] == 0
    assert r["total_wins"] == 0
    assert r["by_game_type"] == []
    assert r["by_origin"] == {}


def test_history_endpoints_require_auth():
    assert client.get("/game-history").status_code == 401
    assert client.get("/game-history/stats").status_code == 401
