from app.db.session import SessionLocal
from app.db.seed_words import seed_words, CHARADES_WORDS, SCRIBBLE_WORDS
from app.models.word import Word


def _count_unique_words(word_dict: dict[int, list[str]]) -> set[str]:
    """Return the set of unique texts in a word dictionary."""
    texts: set[str] = set()
    for words in word_dict.values():
        texts.update(words)
    return texts


def test_seed_words_inserts_both_game_types():
    """seed_words() should insert words for both charades and scribble."""
    db = SessionLocal()
    try:
        inserted = seed_words(db)
        assert inserted > 0

        charades_count = db.query(Word).filter(Word.game_type == "charades").count()
        scribble_count = db.query(Word).filter(Word.game_type == "scribble").count()

        assert charades_count > 0, "Expected charades words to be inserted"
        assert scribble_count > 0, "Expected scribble words to be inserted"
    finally:
        db.close()


def test_seed_words_charades_count_matches_source():
    """Number of charades words inserted should match the unique count in CHARADES_WORDS."""
    db = SessionLocal()
    try:
        seed_words(db)

        expected_texts = _count_unique_words(CHARADES_WORDS)
        charades_count = db.query(Word).filter(Word.game_type == "charades").count()
        assert charades_count == len(expected_texts)
    finally:
        db.close()


def test_seed_words_scribble_count_matches_source():
    """Number of scribble words inserted should equal unique scribble texts."""
    db = SessionLocal()
    try:
        seed_words(db)

        unique_scribble = _count_unique_words(SCRIBBLE_WORDS)
        scribble_count = db.query(Word).filter(Word.game_type == "scribble").count()
        assert scribble_count == len(unique_scribble), (
            f"Expected {len(unique_scribble)} scribble words, got {scribble_count}"
        )
    finally:
        db.close()


def _first_occurrence_difficulty(word_dict: dict[int, list[str]]) -> dict[str, int]:
    """Return {text: difficulty} mapping using first occurrence only (matches seed_words logic)."""
    seen: dict[str, int] = {}
    for difficulty in sorted(word_dict.keys()):
        for text in word_dict[difficulty]:
            if text not in seen:
                seen[text] = difficulty
    return seen


def test_seed_words_difficulty_levels_correct():
    """Each word should have the difficulty from its first occurrence in the source list."""
    db = SessionLocal()
    try:
        seed_words(db)

        # Build expected difficulty based on first occurrence (same logic as seed_words)
        charades_expected = _first_occurrence_difficulty(CHARADES_WORDS)
        for text, expected_diff in charades_expected.items():
            word = db.query(Word).filter(Word.text == text).first()
            assert word is not None, f"Charades word '{text}' was not inserted"
            assert word.difficulty == expected_diff, (
                f"Charades word '{text}' expected difficulty {expected_diff}, got {word.difficulty}"
            )

        # For scribble words, skip any that were already inserted as charades
        # (seed_words skips duplicates across both dicts since charades is seeded first)
        scribble_expected = _first_occurrence_difficulty(SCRIBBLE_WORDS)
        for text, expected_diff in scribble_expected.items():
            if text in charades_expected:
                continue  # This word was claimed by charades
            word = db.query(Word).filter(Word.text == text).first()
            assert word is not None, f"Scribble word '{text}' was not inserted"
            assert word.difficulty == expected_diff, (
                f"Scribble word '{text}' expected difficulty {expected_diff}, got {word.difficulty}"
            )
    finally:
        db.close()


def test_seed_words_all_active():
    """All seeded words should be marked as active."""
    db = SessionLocal()
    try:
        seed_words(db)
        inactive_count = db.query(Word).filter(Word.active.is_(False)).count()
        assert inactive_count == 0, "All seeded words should be active"
    finally:
        db.close()


def test_seed_words_game_type_values():
    """Every seeded word should have game_type of either 'charades' or 'scribble'."""
    db = SessionLocal()
    try:
        seed_words(db)

        all_words = db.query(Word).all()
        game_types = {w.game_type for w in all_words}
        assert game_types == {"charades", "scribble"}, (
            f"Expected exactly charades and scribble game_types, got {game_types}"
        )
    finally:
        db.close()


def test_seed_words_idempotent():
    """Calling seed_words twice should not duplicate entries."""
    db = SessionLocal()
    try:
        first_inserted = seed_words(db)
        count_after_first = db.query(Word).count()

        second_inserted = seed_words(db)
        count_after_second = db.query(Word).count()

        assert second_inserted == 0, "Second call should insert zero new words"
        assert count_after_second == count_after_first, "Total count should stay the same"
    finally:
        db.close()


def test_seed_words_total_count():
    """Total word count should equal unique charades + unique scribble words (composite unique allows same text in both)."""
    db = SessionLocal()
    try:
        seed_words(db)

        unique_charades = _count_unique_words(CHARADES_WORDS)
        unique_scribble = _count_unique_words(SCRIBBLE_WORDS)
        # Composite unique constraint (text, game_type) allows same text in both game types
        expected_total = len(unique_charades) + len(unique_scribble)
        total = db.query(Word).count()
        assert total == expected_total, (
            f"Expected {expected_total} total words, got {total}"
        )
    finally:
        db.close()
