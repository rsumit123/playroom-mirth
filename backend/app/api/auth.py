from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.schemas.auth import GoogleAuthRequest, GoogleAuthResponse, GoogleUserInfo
from app.services.auth import create_access_token, verify_google_token
from app.core.config import JWT_SECRET_KEY

router = APIRouter(tags=["auth"])


@router.post("/auth/google", response_model=GoogleAuthResponse)
def google_login(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    token_info = verify_google_token(payload.id_token)
    if not token_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        )

    google_id = token_info["sub"]
    email = token_info.get("email", "")
    name = token_info.get("name")
    picture = token_info.get("picture")

    # Find existing user by google_id or email
    user = db.query(User).filter(User.google_id == google_id).first()
    if not user and email:
        user = db.query(User).filter(User.email == email).first()
        if user:
            # Link existing email user to Google account
            user.google_id = google_id

    if not user:
        # Create new user
        user = User(
            email=email,
            google_id=google_id,
            display_name=name,
            avatar_url=picture,
            password_hash="",
        )
        db.add(user)
    else:
        # Update profile info from Google
        if name:
            user.display_name = name
        if picture:
            user.avatar_url = picture

    db.commit()
    db.refresh(user)

    access_token = create_access_token(subject=str(user.id))
    return GoogleAuthResponse(
        access_token=access_token,
        user=GoogleUserInfo(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
        ),
    )


@router.post("/auth/test-user")
def create_test_user(payload: dict, db: Session = Depends(get_db)):
    """Create a test user and return a JWT. Only works in dev mode (default secret key)."""
    if JWT_SECRET_KEY != "dev-secret-change":
        raise HTTPException(status_code=404, detail="Not found")

    display_name = payload.get("display_name", "TestUser")
    email = payload.get("email", f"{display_name.lower().replace(' ', '')}@test.playroom")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, google_id=f"test-{email}", display_name=display_name, password_hash="")
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(subject=str(user.id))
    return {
        "access_token": token,
        "user": {"id": user.id, "email": user.email, "display_name": user.display_name, "avatar_url": user.avatar_url},
    }
