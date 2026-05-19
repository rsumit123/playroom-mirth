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


# ---------- Leaderboard endpoint ----------

def test_leaderboard_ranks_users_by_wins_descending():
    a, ta = _make_user_with_token("lb-a")
    b, tb = _make_user_with_token("lb-b")
    c, tc = _make_user_with_token("lb-c")
    # a: 3 wins, b: 5 wins, c: 1 win — expect order b, a, c.
    for _ in range(3): _add_row(a.id, game_type="trivia", origin="quickmatch", is_winner=True)
    for _ in range(5): _add_row(b.id, game_type="trivia", origin="quickmatch", is_winner=True)
    for _ in range(1): _add_row(c.id, game_type="trivia", origin="quickmatch", is_winner=True)

    r = client.get("/game-history/leaderboard?origin=quickmatch", headers=_auth(ta)).json()
    ranks = [(e["display_name"], e["wins"], e["rank"]) for e in r["top"]]
    # First by wins desc.
    assert ranks[0][1] == 5 and ranks[0][2] == 1
    assert ranks[1][1] == 3 and ranks[1][2] == 2
    assert ranks[2][1] == 1 and ranks[2][2] == 3


def test_leaderboard_caller_in_top_does_not_get_duplicate_you_pin():
    a, ta = _make_user_with_token("lb-top")
    for _ in range(3): _add_row(a.id, game_type="trivia", origin="quickmatch", is_winner=True)
    r = client.get("/game-history/leaderboard?origin=quickmatch&limit=10", headers=_auth(ta)).json()
    # Caller is in the top — `you` should be suppressed.
    assert any(e["user_id"] == a.id for e in r["top"])
    assert r["you"] is None


def test_leaderboard_caller_outside_top_gets_you_pin_with_real_rank():
    # Build a board with 12 leaders ahead of the caller.
    leaders = []
    for i in range(12):
        u, _ = _make_user_with_token(f"lb-leader-{i}")
        for _ in range(20 - i):  # 20, 19, 18, ... wins
            _add_row(u.id, game_type="trivia", origin="quickmatch", is_winner=True)
        leaders.append(u)

    me, my_token = _make_user_with_token("lb-me")
    for _ in range(2):
        _add_row(me.id, game_type="trivia", origin="quickmatch", is_winner=True)

    r = client.get("/game-history/leaderboard?origin=quickmatch&limit=10", headers=_auth(my_token)).json()
    assert len(r["top"]) == 10
    assert r["you"] is not None
    assert r["you"]["user_id"] == me.id
    assert r["you"]["rank"] == 13  # 12 leaders ahead, caller is rank 13
    assert r["you"]["wins"] == 2


def test_leaderboard_empty_when_no_games_for_origin():
    _, token = _make_user_with_token("lb-empty")
    r = client.get("/game-history/leaderboard?origin=quickmatch", headers=_auth(token)).json()
    assert r["top"] == []
    assert r["you"] is None
    assert r["current_streak"] == 0


def test_leaderboard_excludes_guest_rows():
    # Guest users have user_id = 0 in GameHistory; they must not show up.
    me, token = _make_user_with_token("lb-vs-guest")
    _add_row(me.id, game_type="trivia", origin="quickmatch", is_winner=True)
    # Guest row — user_id = 0
    db = SessionLocal()
    try:
        db.add(GameHistory(
            user_id=0, room_code="G0001", game_type="trivia",
            score=999, player_count=2, is_winner=True,
            display_name="GuestX", game_number=1, origin="quickmatch",
        ))
        db.commit()
    finally:
        db.close()

    r = client.get("/game-history/leaderboard?origin=quickmatch", headers=_auth(token)).json()
    # Only the real user shows up, never user_id=0.
    user_ids = {e["user_id"] for e in r["top"]}
    assert 0 not in user_ids
    assert me.id in user_ids


# ---------- Current streak ----------

def test_current_streak_counts_consecutive_wins_from_most_recent_backwards():
    from datetime import datetime, timedelta
    me, token = _make_user_with_token("streak-3")
    # Manually set played_at so we control order: loss (oldest), win, win, win (newest)
    base = datetime.utcnow() - timedelta(hours=10)
    db = SessionLocal()
    try:
        for i, (won, age_hours) in enumerate([(False, 4), (True, 3), (True, 2), (True, 1)]):
            db.add(GameHistory(
                user_id=me.id, room_code=f"S{i:04d}", game_type="trivia",
                score=100, player_count=2, is_winner=won,
                played_at=base + timedelta(hours=10 - age_hours),
                display_name="me", game_number=1, origin="quickmatch",
            ))
        db.commit()
    finally:
        db.close()

    r = client.get("/game-history/leaderboard?origin=quickmatch", headers=_auth(token)).json()
    assert r["current_streak"] == 3


def test_current_streak_zero_when_most_recent_is_loss():
    from datetime import datetime, timedelta
    me, token = _make_user_with_token("streak-broken")
    base = datetime.utcnow() - timedelta(hours=5)
    db = SessionLocal()
    try:
        for i, (won, age) in enumerate([(True, 3), (True, 2), (False, 1)]):  # most recent is a loss
            db.add(GameHistory(
                user_id=me.id, room_code=f"SB{i:04d}", game_type="trivia",
                score=100, player_count=2, is_winner=won,
                played_at=base + timedelta(hours=5 - age),
                display_name="me", game_number=1, origin="quickmatch",
            ))
        db.commit()
    finally:
        db.close()

    r = client.get("/game-history/leaderboard?origin=quickmatch", headers=_auth(token)).json()
    assert r["current_streak"] == 0


def test_leaderboard_requires_auth():
    assert client.get("/game-history/leaderboard").status_code == 401
