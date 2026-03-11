from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.game_history import GameHistory
from app.models.room import Room
from app.models.room_player import RoomPlayer
from app.models.word import Word
from app.schemas.word import WordCreateRequest, WordUpdateRequest, WordOut
from app.services.game_state import ROOM_STATES
from app.services.trivia import _load_gk_questions

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/words", response_model=list[WordOut])
def list_words(
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    query = db.query(Word)
    if q:
        query = query.filter(Word.text.contains(q))
    return query.order_by(Word.id.asc()).offset(offset).limit(limit).all()


@router.post("/words", response_model=WordOut, status_code=201)
def create_word(payload: WordCreateRequest, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    existing = db.query(Word).filter(Word.text == payload.text).first()
    if existing:
        raise HTTPException(status_code=400, detail="Word already exists")
    word = Word(text=payload.text, difficulty=payload.difficulty, active=True)
    db.add(word)
    db.commit()
    db.refresh(word)
    return word


@router.patch("/words/{word_id}", response_model=WordOut)
def update_word(
    word_id: int,
    payload: WordUpdateRequest,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    word = db.query(Word).filter(Word.id == word_id).first()
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")
    if payload.text is not None:
        word.text = payload.text
    if payload.difficulty is not None:
        word.difficulty = payload.difficulty
    if payload.active is not None:
        word.active = payload.active
    db.commit()
    db.refresh(word)
    return word


@router.get("/stats")
def get_stats(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    # Active rooms
    rooms = db.query(Room).filter(Room.status.in_(["lobby", "active"])).all()
    active_rooms = []
    for room in rooms:
        connected = (
            db.query(RoomPlayer)
            .filter(RoomPlayer.room_id == room.id, RoomPlayer.connected.is_(True))
            .count()
        )
        active_rooms.append({
            "code": room.code,
            "status": room.status,
            "game_type": room.game_type,
            "trivia_category": room.trivia_category,
            "connected_players": connected,
            "max_players": room.max_players,
            "created_at": str(room.created_at) if room.created_at else None,
        })

    # Totals
    connected_total = (
        db.query(RoomPlayer).filter(RoomPlayer.connected.is_(True)).count()
    )

    # Question pool counts
    questions = _load_gk_questions()
    category_counts = dict(Counter(q["category"] for q in questions))

    # Recent games
    recent = (
        db.query(GameHistory)
        .order_by(GameHistory.played_at.desc())
        .limit(10)
        .all()
    )
    recent_games = [
        {
            "room_code": g.room_code,
            "game_type": g.game_type,
            "player_count": g.player_count,
            "score": g.score,
            "is_winner": g.is_winner,
            "played_at": str(g.played_at) if g.played_at else None,
        }
        for g in recent
    ]

    return {
        "active_rooms": active_rooms,
        "totals": {
            "active_room_count": len(active_rooms),
            "connected_players": connected_total,
            "in_memory_games": len(ROOM_STATES),
            "total_questions": len(questions),
        },
        "question_pool": category_counts,
        "recent_games": recent_games,
    }
