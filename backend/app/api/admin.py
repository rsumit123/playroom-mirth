from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.word import Word
from app.schemas.word import WordCreateRequest, WordUpdateRequest, WordOut

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
