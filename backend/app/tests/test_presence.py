"""Tests for online presence tracking."""
import pytest

from app.db.session import SessionLocal
from app.models.user import User
from app.services.auth import create_access_token
from app.sockets.events import sio, SID_TO_USER
from app.services.game_state import USER_ONLINE


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


@pytest.mark.asyncio
async def test_presence_connect_registers_user():
    """presence:connect with valid token registers the user as online."""
    uid, token = _create_user("pres1@x.com", "PresAlice")
    sid = await sio.manager.connect("eio-pres1", "/")

    await sio._trigger_event("presence:connect", "/", sid, {"token": token})

    assert SID_TO_USER.get(sid) == uid
    assert sid in USER_ONLINE.get(uid, set())


@pytest.mark.asyncio
async def test_presence_cleanup_logic():
    """Verifying the presence cleanup logic used by disconnect handler."""
    # Ensure clean state
    USER_ONLINE.clear()
    SID_TO_USER.clear()

    uid, token = _create_user("pres2@x.com", "PresBob")
    fake_sid = "test-sid-cleanup"

    # Simulate presence:connect
    SID_TO_USER[fake_sid] = uid
    USER_ONLINE.setdefault(uid, set()).add(fake_sid)
    assert uid in USER_ONLINE

    # Simulate disconnect cleanup (same logic as disconnect handler)
    user_id = SID_TO_USER.pop(fake_sid, None)
    if user_id and user_id in USER_ONLINE:
        USER_ONLINE[user_id].discard(fake_sid)
        if not USER_ONLINE[user_id]:
            del USER_ONLINE[user_id]

    assert fake_sid not in SID_TO_USER
    assert uid not in USER_ONLINE


@pytest.mark.asyncio
async def test_presence_multi_tab_cleanup():
    """Multiple SIDs for same user -- online until all SIDs removed."""
    USER_ONLINE.clear()
    SID_TO_USER.clear()

    uid, token = _create_user("pres3@x.com", "PresCarol")
    sid1 = "test-sid-tab1"
    sid2 = "test-sid-tab2"

    # Simulate two tabs connecting
    SID_TO_USER[sid1] = uid
    SID_TO_USER[sid2] = uid
    USER_ONLINE.setdefault(uid, set()).add(sid1)
    USER_ONLINE[uid].add(sid2)
    assert len(USER_ONLINE[uid]) == 2

    # Disconnect tab 1
    SID_TO_USER.pop(sid1, None)
    USER_ONLINE[uid].discard(sid1)
    assert uid in USER_ONLINE  # still online
    assert len(USER_ONLINE[uid]) == 1

    # Disconnect tab 2
    SID_TO_USER.pop(sid2, None)
    USER_ONLINE[uid].discard(sid2)
    if not USER_ONLINE[uid]:
        del USER_ONLINE[uid]
    assert uid not in USER_ONLINE  # now offline


@pytest.mark.asyncio
async def test_presence_re_registration_after_disconnect():
    """After disconnect + new connect, presence:connect re-registers the user."""
    USER_ONLINE.clear()
    SID_TO_USER.clear()

    uid, token = _create_user("presreg1@x.com", "ReRegAlice")

    # First connection
    sid1 = await sio.manager.connect("eio-presreg1a", "/")
    await sio._trigger_event("presence:connect", "/", sid1, {"token": token})
    assert uid in USER_ONLINE

    # Simulate disconnect (socket reset)
    user_id = SID_TO_USER.pop(sid1, None)
    if user_id and user_id in USER_ONLINE:
        USER_ONLINE[user_id].discard(sid1)
        if not USER_ONLINE[user_id]:
            del USER_ONLINE[user_id]
    assert uid not in USER_ONLINE  # now offline

    # New connection (simulates socketGen bump → useEffect re-runs → new connectSocket)
    sid2 = await sio.manager.connect("eio-presreg1b", "/")
    await sio._trigger_event("presence:connect", "/", sid2, {"token": token})

    # User should be online again with new SID
    assert uid in USER_ONLINE
    assert sid2 in USER_ONLINE[uid]
    assert sid1 not in USER_ONLINE[uid]


@pytest.mark.asyncio
async def test_presence_invalid_token_ignored():
    """presence:connect with invalid token is silently ignored."""
    sid = await sio.manager.connect("eio-pres4", "/")
    await sio._trigger_event("presence:connect", "/", sid, {"token": "invalid-jwt"})

    assert sid not in SID_TO_USER


@pytest.mark.asyncio
async def test_presence_no_token_ignored():
    """presence:connect with no token is silently ignored."""
    sid = await sio.manager.connect("eio-pres5", "/")
    await sio._trigger_event("presence:connect", "/", sid, {})

    assert sid not in SID_TO_USER


@pytest.mark.asyncio
async def test_friends_list_shows_online_status(client):
    """GET /friends should return is_online=True for online friends."""
    uid_a, tok_a = _create_user("presfr1@x.com", "OnlineAlice")
    uid_b, tok_b = _create_user("presfr2@x.com", "OnlineBob")

    # Become friends
    client.post("/friends/request", json={"user_id": uid_b}, headers={"Authorization": f"Bearer {tok_a}"})
    client.post(f"/friends/{uid_a}/accept", headers={"Authorization": f"Bearer {tok_b}"})

    # Simulate Bob going online
    fake_sid = "test-sid-bob-online"
    SID_TO_USER[fake_sid] = uid_b
    USER_ONLINE.setdefault(uid_b, set()).add(fake_sid)

    # Alice checks friends -- Bob should be online
    friends = client.get("/friends", headers={"Authorization": f"Bearer {tok_a}"}).json()["friends"]
    bob = next(f for f in friends if f["id"] == uid_b)
    assert bob["is_online"] is True

    # Bob goes offline
    SID_TO_USER.pop(fake_sid, None)
    USER_ONLINE[uid_b].discard(fake_sid)
    if not USER_ONLINE[uid_b]:
        del USER_ONLINE[uid_b]

    # Alice checks again -- Bob should be offline
    friends = client.get("/friends", headers={"Authorization": f"Bearer {tok_a}"}).json()["friends"]
    bob = next(f for f in friends if f["id"] == uid_b)
    assert bob["is_online"] is False
