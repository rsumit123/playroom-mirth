from datetime import datetime, timedelta
from typing import Optional
from jose import jwt

from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

from app.core.config import JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, GOOGLE_CLIENT_ID


def verify_google_token(token: str) -> Optional[dict]:
    try:
        id_info = google_id_token.verify_oauth2_token(
            token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
        return id_info
    except Exception:
        return None


def create_access_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
