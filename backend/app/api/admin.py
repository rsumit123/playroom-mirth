import json
from collections import Counter
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.game_history import GameHistory
from app.models.guest import Guest
from app.models.room import Room
from app.models.room_player import RoomPlayer
from app.models.user import User
from app.models.word import Word
from app.schemas.word import WordCreateRequest, WordUpdateRequest, WordOut
from app.services.game_state import ROOM_STATES
from app.services import trivia as _trivia_mod
from app.services.trivia import _load_gk_questions

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/words", response_model=list[WordOut])
def list_words(
    q: str | None = Query(default=None),
    game_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    query = db.query(Word)
    if q:
        query = query.filter(Word.text.contains(q))
    if game_type:
        query = query.filter(Word.game_type == game_type)
    return query.order_by(Word.id.asc()).offset(offset).limit(limit).all()


@router.post("/words", response_model=WordOut, status_code=201)
def create_word(payload: WordCreateRequest, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    existing = db.query(Word).filter(
        Word.text == payload.text, Word.game_type == payload.game_type
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Word already exists for this game type")
    word = Word(text=payload.text, difficulty=payload.difficulty, game_type=payload.game_type, active=True)
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
    if payload.game_type is not None:
        word.game_type = payload.game_type
    db.commit()
    db.refresh(word)
    return word


@router.delete("/words/{word_id}")
def delete_word(
    word_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    word = db.query(Word).filter(Word.id == word_id).first()
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")
    db.delete(word)
    db.commit()
    return {"ok": True}


@router.get("/stats")
def get_stats(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    # Active rooms with player names
    rooms = db.query(Room).filter(Room.status.in_(["lobby", "active"])).all()
    active_rooms = []
    for room in rooms:
        players = db.query(RoomPlayer).filter(RoomPlayer.room_id == room.id).all()
        # Resolve display names (same pattern as room_ops.lobby_state)
        user_ids = [p.user_id for p in players if p.user_id]
        user_map = {}
        if user_ids:
            users = db.query(User).filter(User.id.in_(user_ids)).all()
            user_map = {u.id: u.email.split("@")[0] for u in users}
        guest_ids = [p.guest_id for p in players if p.guest_id]
        guest_name_map = {}
        if guest_ids:
            guests = db.query(Guest).filter(Guest.id.in_(guest_ids)).all()
            guest_name_map = {g.id: g.display_name for g in guests if g.display_name}
        guest_counter = 0
        player_list = []
        connected_count = 0
        for p in players:
            if p.user_id and p.user_id in user_map:
                name = user_map[p.user_id]
            elif p.guest_id and p.guest_id in guest_name_map:
                name = guest_name_map[p.guest_id]
            else:
                guest_counter += 1
                name = f"Guest {guest_counter}"
            if p.connected:
                connected_count += 1
            player_list.append({"id": p.id, "name": name, "connected": p.connected})
        active_rooms.append({
            "code": room.code,
            "status": room.status,
            "game_type": room.game_type,
            "trivia_category": room.trivia_category,
            "connected_players": connected_count,
            "max_players": room.max_players,
            "created_at": str(room.created_at) if room.created_at else None,
            "players": player_list,
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
            "display_name": getattr(g, 'display_name', None),
        }
        for g in recent
    ]

    # Word counts by game type
    word_counts = {}
    for gt in ["charades", "scribble"]:
        word_counts[gt] = db.query(Word).filter(
            Word.game_type == gt, Word.active.is_(True)
        ).count()

    return {
        "active_rooms": active_rooms,
        "totals": {
            "active_room_count": len(active_rooms),
            "connected_players": connected_total,
            "in_memory_games": len(ROOM_STATES),
            "total_questions": len(questions),
            "charades_words": word_counts.get("charades", 0),
            "scribble_words": word_counts.get("scribble", 0),
        },
        "question_pool": category_counts,
        "recent_games": recent_games,
    }


# ── Room close / cleanup ──────────────────────────────────────

def _close_room(room: Room, db: Session):
    """Mark room closed, disconnect all players, remove in-memory state."""
    room.status = "closed"
    db.query(RoomPlayer).filter(RoomPlayer.room_id == room.id).update(
        {"connected": False, "in_game": False}
    )
    ROOM_STATES.pop(room.code, None)


@router.post("/rooms/{room_code}/close")
def close_room(room_code: str, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    room = db.query(Room).filter(Room.code == room_code).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    _close_room(room, db)
    db.commit()
    return {"ok": True}


@router.post("/rooms/cleanup")
def cleanup_rooms(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    rooms = db.query(Room).filter(Room.status.in_(["lobby", "active"])).all()
    closed = 0
    for room in rooms:
        connected = (
            db.query(RoomPlayer)
            .filter(RoomPlayer.room_id == room.id, RoomPlayer.connected.is_(True))
            .count()
        )
        if connected == 0:
            _close_room(room, db)
            closed += 1
    db.commit()
    return {"closed_count": closed}


# ── Question management ───────────────────────────────────────

_GK_DATA_PATH = Path(__file__).parent.parent / "data" / "gk_questions.json"

_CATEGORY_PREFIXES = {
    "science": "sci", "history": "hist", "geography": "geo",
    "sports": "spt", "entertainment": "ent", "general": "gen",
    "mythology": "myth", "food": "food", "politics": "pol",
}


def _save_gk_questions(questions: list[dict]):
    with open(_GK_DATA_PATH, "w") as f:
        json.dump(questions, f, indent=2)
    _trivia_mod._GK_QUESTIONS = None  # reset cache


class QuestionCreate(BaseModel):
    category: str
    difficulty: int
    question: str
    options: list[str]
    correct_index: int


@router.get("/questions")
def list_questions(
    q: str | None = Query(default=None),
    category: str | None = Query(default=None),
    difficulty: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _user=Depends(get_current_user),
):
    questions = _load_gk_questions()
    if q:
        ql = q.lower()
        questions = [qn for qn in questions if ql in qn["question"].lower()]
    if category:
        questions = [qn for qn in questions if qn.get("category") == category]
    if difficulty is not None:
        questions = [qn for qn in questions if qn.get("difficulty") == difficulty]
    total = len(questions)
    return {"questions": questions[offset : offset + limit], "total": total}


@router.post("/questions", status_code=201)
def create_question(payload: QuestionCreate, _user=Depends(get_current_user)):
    if len(payload.options) != 4:
        raise HTTPException(status_code=400, detail="Exactly 4 options required")
    if payload.correct_index < 0 or payload.correct_index > 3:
        raise HTTPException(status_code=400, detail="correct_index must be 0-3")
    questions = _load_gk_questions()
    prefix = _CATEGORY_PREFIXES.get(payload.category, payload.category[:3])
    diff_str = {1: "easy", 2: "medium", 3: "hard"}.get(payload.difficulty, "medium")
    # Find next sequence number for this prefix+difficulty
    pattern = f"{prefix}_{diff_str}_"
    existing_nums = []
    for qn in questions:
        qid = qn.get("id", "")
        if qid.startswith(pattern):
            try:
                existing_nums.append(int(qid[len(pattern):]))
            except ValueError:
                pass
    next_num = max(existing_nums, default=0) + 1
    new_q = {
        "id": f"{pattern}{next_num:03d}",
        "category": payload.category,
        "difficulty": payload.difficulty,
        "question": payload.question,
        "options": payload.options,
        "correct_index": payload.correct_index,
    }
    questions.append(new_q)
    _save_gk_questions(questions)
    return new_q


@router.delete("/questions/{question_id}")
def delete_question(question_id: str, _user=Depends(get_current_user)):
    questions = _load_gk_questions()
    original_len = len(questions)
    questions = [q for q in questions if q.get("id") != question_id]
    if len(questions) == original_len:
        raise HTTPException(status_code=404, detail="Question not found")
    _save_gk_questions(questions)
    return {"ok": True}
