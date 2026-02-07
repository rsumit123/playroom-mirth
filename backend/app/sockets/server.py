import socketio
from fastapi import FastAPI

from app.core.config import SOCKETIO_PATH
from app.sockets.events import sio


def build_socket_app(fastapi_app: FastAPI) -> socketio.ASGIApp:
    return socketio.ASGIApp(sio, other_asgi_app=fastapi_app, socketio_path=SOCKETIO_PATH)
