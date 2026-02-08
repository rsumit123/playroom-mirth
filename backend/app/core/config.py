import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./charade.db")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

SOCKETIO_PATH = os.getenv("SOCKETIO_PATH", "/socket.io")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
