from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.admin import router as admin_router
from app.api.guest import router as guest_router
from app.api.rooms import router as rooms_router
from app.api.game_history import router as game_history_router
import asyncio

from app.db.init_db import init_db
from app.db.seed_words import seed_words
from app.sockets.server import build_socket_app
from app.sockets.events import restore_game_states, schedule_restored_states
from app.services.game_state import cancel_all_timers

fastapi_app = FastAPI(title="Charade Chat")
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "https://charade-chat.skdev.one",
        "https://playroom.skdev.one",
        "https://frontend-ashen-alpha-57.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
fastapi_app.include_router(auth_router)
fastapi_app.include_router(admin_router)
fastapi_app.include_router(guest_router)
fastapi_app.include_router(rooms_router)
fastapi_app.include_router(game_history_router)


@fastapi_app.on_event("startup")
async def on_startup() -> None:
    init_db()
    # Seed base words if missing
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        seed_words(db)
    finally:
        db.close()
    restore_game_states()
    await schedule_restored_states()


@fastapi_app.on_event("shutdown")
async def on_shutdown() -> None:
    await cancel_all_timers()


app = build_socket_app(fastapi_app)
