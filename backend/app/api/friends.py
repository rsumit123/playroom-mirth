from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.friendship import Friendship
from app.services.game_state import USER_ONLINE

router = APIRouter(tags=["friends"])


@router.post("/friends/request", status_code=201)
def send_friend_request(
    payload: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    addressee_id = payload.get("user_id")
    if not addressee_id:
        raise HTTPException(status_code=400, detail="user_id required")

    if addressee_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot send friend request to yourself")

    target = db.query(User).filter(User.id == addressee_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    existing = db.query(Friendship).filter(
        or_(
            and_(Friendship.requester_id == user.id, Friendship.addressee_id == addressee_id),
            and_(Friendship.requester_id == addressee_id, Friendship.addressee_id == user.id),
        )
    ).first()

    if existing:
        if existing.status == "accepted":
            return {"ok": True, "status": "already_friends"}
        if existing.requester_id == user.id:
            return {"ok": True, "status": "pending"}
        # They sent us a request -- auto-accept
        existing.status = "accepted"
        db.commit()
        return {"ok": True, "status": "accepted"}

    friendship = Friendship(requester_id=user.id, addressee_id=addressee_id, status="pending")
    db.add(friendship)
    db.commit()
    return {"ok": True, "status": "pending"}


@router.get("/friends")
def list_friends(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    friendships = db.query(Friendship).filter(
        Friendship.status == "accepted",
        or_(Friendship.requester_id == user.id, Friendship.addressee_id == user.id),
    ).all()

    friends = []
    for f in friendships:
        friend_id = f.addressee_id if f.requester_id == user.id else f.requester_id
        friend_user = db.query(User).filter(User.id == friend_id).first()
        if friend_user:
            friends.append({
                "id": friend_user.id,
                "display_name": friend_user.display_name,
                "avatar_url": friend_user.avatar_url,
                "is_online": bool(USER_ONLINE.get(friend_user.id)),
            })
    return {"friends": friends}


@router.get("/friends/requests")
def list_friend_requests(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    pending = db.query(Friendship).filter(
        Friendship.addressee_id == user.id,
        Friendship.status == "pending",
    ).all()

    requests = []
    for f in pending:
        requester = db.query(User).filter(User.id == f.requester_id).first()
        if requester:
            requests.append({
                "id": requester.id,
                "display_name": requester.display_name,
                "avatar_url": requester.avatar_url,
                "created_at": f.created_at.isoformat() if f.created_at else None,
            })
    return {"requests": requests}


@router.post("/friends/{user_id}/accept")
def accept_friend_request(
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    friendship = db.query(Friendship).filter(
        Friendship.requester_id == user_id,
        Friendship.addressee_id == user.id,
        Friendship.status == "pending",
    ).first()

    if not friendship:
        raise HTTPException(status_code=404, detail="No pending request from this user")

    friendship.status = "accepted"
    db.commit()
    return {"ok": True}


@router.post("/friends/{user_id}/reject")
def reject_friend(
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    friendship = db.query(Friendship).filter(
        or_(
            and_(Friendship.requester_id == user_id, Friendship.addressee_id == user.id),
            and_(Friendship.requester_id == user.id, Friendship.addressee_id == user_id),
        )
    ).first()

    if not friendship:
        raise HTTPException(status_code=404, detail="No friendship found with this user")

    db.delete(friendship)
    db.commit()
    return {"ok": True}


@router.get("/users/search")
def search_users(
    q: str = Query(min_length=1, max_length=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    results = db.query(User).filter(
        User.display_name.ilike(f"%{q}%"),
        User.id != user.id,
        User.google_id.isnot(None),
    ).limit(20).all()

    return {
        "users": [
            {"id": u.id, "display_name": u.display_name, "avatar_url": u.avatar_url}
            for u in results
        ]
    }
