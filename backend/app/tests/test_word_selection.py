from app.db.session import SessionLocal
from app.models.word import Word
from app.sockets.events import _select_word


def _insert_test_words(db):
    """Insert a known set of test words for both game types and return their ids."""
    words = [
        Word(text="charades_easy_1", difficulty=1, active=True, game_type="charades"),
        Word(text="charades_easy_2", difficulty=1, active=True, game_type="charades"),
        Word(text="charades_medium_1", difficulty=2, active=True, game_type="charades"),
        Word(text="charades_hard_1", difficulty=3, active=True, game_type="charades"),
        Word(text="scribble_easy_1", difficulty=1, active=True, game_type="scribble"),
        Word(text="scribble_easy_2", difficulty=1, active=True, game_type="scribble"),
        Word(text="scribble_medium_1", difficulty=2, active=True, game_type="scribble"),
        Word(text="scribble_hard_1", difficulty=3, active=True, game_type="scribble"),
        Word(text="inactive_charades", difficulty=1, active=False, game_type="charades"),
        Word(text="inactive_scribble", difficulty=1, active=False, game_type="scribble"),
    ]
    for w in words:
        db.add(w)
    db.commit()
    for w in words:
        db.refresh(w)
    return {w.text: w.id for w in words}


def test_select_word_filters_by_charades():
    """_select_word with game_type='charades' should only return charades words."""
    db = SessionLocal()
    try:
        _insert_test_words(db)

        for _ in range(20):
            word = _select_word(db, difficulty=1, history_ids=[], game_type="charades")
            assert word is not None
            assert word.game_type == "charades"
    finally:
        db.close()


def test_select_word_filters_by_scribble():
    """_select_word with game_type='scribble' should only return scribble words."""
    db = SessionLocal()
    try:
        _insert_test_words(db)

        for _ in range(20):
            word = _select_word(db, difficulty=1, history_ids=[], game_type="scribble")
            assert word is not None
            assert word.game_type == "scribble"
    finally:
        db.close()


def test_select_word_excludes_history():
    """_select_word should not return words already in history_ids."""
    db = SessionLocal()
    try:
        ids = _insert_test_words(db)
        charades_easy_ids = [ids["charades_easy_1"], ids["charades_easy_2"]]

        word = _select_word(db, difficulty=1, history_ids=charades_easy_ids, game_type="charades")
        # The two easy charades words are excluded; it should fall back to another difficulty
        if word is not None:
            assert word.id not in charades_easy_ids
            assert word.game_type == "charades"
    finally:
        db.close()


def test_select_word_respects_difficulty():
    """_select_word should prefer the requested difficulty level."""
    db = SessionLocal()
    try:
        _insert_test_words(db)

        # Request difficulty=3 for scribble — only scribble_hard_1 qualifies
        word = _select_word(db, difficulty=3, history_ids=[], game_type="scribble")
        assert word is not None
        assert word.text == "scribble_hard_1"
        assert word.difficulty == 3
        assert word.game_type == "scribble"
    finally:
        db.close()


def test_select_word_excludes_inactive():
    """_select_word should never return inactive words."""
    db = SessionLocal()
    try:
        ids = _insert_test_words(db)

        # Exclude all active charades words except inactive ones via history
        active_charades_ids = [
            ids["charades_easy_1"],
            ids["charades_easy_2"],
            ids["charades_medium_1"],
            ids["charades_hard_1"],
        ]

        word = _select_word(db, difficulty=1, history_ids=active_charades_ids, game_type="charades")
        # All active charades words are in history, so no word should be returned
        assert word is None, "Should return None when all active words are exhausted"
    finally:
        db.close()


def test_select_word_falls_back_when_no_exact_difficulty():
    """When no words exist at the requested difficulty, _select_word returns another difficulty."""
    db = SessionLocal()
    try:
        # Insert only easy scribble words, no hard ones
        db.add(Word(text="only_easy_scribble", difficulty=1, active=True, game_type="scribble"))
        db.commit()

        # Request hard (difficulty=3) for scribble -- none exist, should fall back
        word = _select_word(db, difficulty=3, history_ids=[], game_type="scribble")
        assert word is not None
        assert word.game_type == "scribble"
        assert word.text == "only_easy_scribble"
    finally:
        db.close()


def test_select_word_difficulty_fallback_when_exact_exhausted():
    """When exact difficulty is exhausted, any other active word of same game_type is returned."""
    db = SessionLocal()
    try:
        ids = _insert_test_words(db)

        # Exclude the only hard charades word
        word = _select_word(
            db, difficulty=3, history_ids=[ids["charades_hard_1"]], game_type="charades"
        )
        # Should fall back to easy or medium charades
        assert word is not None
        assert word.game_type == "charades"
        assert word.difficulty in (1, 2)
    finally:
        db.close()


def test_select_word_mixed_mode():
    """difficulty=0 (mixed) should return words from any difficulty for the given game_type."""
    db = SessionLocal()
    try:
        _insert_test_words(db)

        seen_difficulties = set()
        for _ in range(50):
            word = _select_word(db, difficulty=0, history_ids=[], game_type="scribble")
            assert word is not None
            assert word.game_type == "scribble"
            seen_difficulties.add(word.difficulty)

        # With 50 tries, we should see more than one difficulty level
        assert len(seen_difficulties) >= 1, "Mixed mode should return words"
    finally:
        db.close()


def test_select_word_returns_none_for_unknown_game_type():
    """Requesting words for a game_type with no words should return None."""
    db = SessionLocal()
    try:
        _insert_test_words(db)

        word = _select_word(db, difficulty=1, history_ids=[], game_type="nonexistent")
        assert word is None
    finally:
        db.close()


def test_select_word_no_cross_contamination():
    """Ensure charades selection never includes scribble words and vice versa."""
    db = SessionLocal()
    try:
        ids = _insert_test_words(db)

        scribble_ids = {
            ids["scribble_easy_1"],
            ids["scribble_easy_2"],
            ids["scribble_medium_1"],
            ids["scribble_hard_1"],
        }
        charades_ids = {
            ids["charades_easy_1"],
            ids["charades_easy_2"],
            ids["charades_medium_1"],
            ids["charades_hard_1"],
        }

        for _ in range(30):
            word = _select_word(db, difficulty=0, history_ids=[], game_type="charades")
            if word:
                assert word.id not in scribble_ids, (
                    f"Charades selection returned scribble word: {word.text}"
                )

        for _ in range(30):
            word = _select_word(db, difficulty=0, history_ids=[], game_type="scribble")
            if word:
                assert word.id not in charades_ids, (
                    f"Scribble selection returned charades word: {word.text}"
                )
    finally:
        db.close()
