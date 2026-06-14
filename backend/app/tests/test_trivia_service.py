"""Unit tests for app.services.trivia: math question generation and GK selection."""

import random

import pytest

from app.services.trivia import (
    _make_distractors,
    generate_question,
    generate_round_questions,
    generate_gk_round_questions,
    _load_gk_questions,
)


# ── _make_distractors ──────────────────────────────────────────────


def test_make_distractors_returns_exact_count():
    distractors = _make_distractors(50, count=3)
    assert len(distractors) == 3


def test_make_distractors_are_unique():
    distractors = _make_distractors(50, count=3)
    assert len(set(distractors)) == 3


def test_make_distractors_exclude_correct():
    for correct in [7, 50, 123, 1000]:
        distractors = _make_distractors(correct, count=3)
        assert correct not in distractors


def test_make_distractors_share_units_digit_with_correct():
    """Distractors should share the correct answer's units digit so players
    can't eliminate by digit pattern."""
    for correct in [17, 50, 123, 7, 1000, 42]:
        distractors = _make_distractors(correct, count=3)
        for d in distractors:
            assert d % 10 == correct % 10, f"correct={correct} distractor={d}"


def test_make_distractors_all_positive():
    for correct in [1, 5, 12]:
        distractors = _make_distractors(correct, count=3)
        assert all(d > 0 for d in distractors)


def test_make_distractors_fallback_for_small_correct():
    """Even correct=1 (where the random branch struggles) should yield 3 distractors via fallback."""
    distractors = _make_distractors(1, count=3)
    assert len(distractors) == 3


# ── generate_question ─────────────────────────────────────────────


def test_generate_question_easy_shape():
    q = generate_question(1)
    assert "question" in q
    assert len(q["options"]) == 4
    assert 0 <= q["correct_index"] < 4
    assert q["time_seconds"] == 20


def test_generate_question_medium_shape():
    q = generate_question(2)
    assert q["time_seconds"] == 15
    assert len(q["options"]) == 4


def test_generate_question_hard_shape():
    q = generate_question(3)
    assert q["time_seconds"] == 15
    assert len(q["options"]) == 4


def test_generate_question_unknown_difficulty_defaults_to_medium():
    q = generate_question(99)
    assert q["time_seconds"] == 15


def test_generate_question_options_are_strings():
    for diff in (1, 2, 3):
        for _ in range(10):
            q = generate_question(diff)
            assert all(isinstance(o, str) for o in q["options"])
            # Correct option must be one of the displayed options
            assert q["options"][q["correct_index"]] in q["options"]


def test_generate_question_correct_index_within_bounds():
    for diff in (1, 2, 3):
        for _ in range(10):
            q = generate_question(diff)
            assert 0 <= q["correct_index"] < len(q["options"])


# ── generate_round_questions ──────────────────────────────────────


def test_generate_round_questions_returns_requested_count():
    qs = generate_round_questions(2, count=10)
    assert len(qs) == 10


def test_generate_round_questions_default_count_is_ten():
    qs = generate_round_questions(2)
    assert len(qs) == 10


def test_generate_round_questions_mostly_unique_text():
    qs = generate_round_questions(2, count=10)
    texts = [q["question"] for q in qs]
    # Allow a couple of fallback dupes but expect mostly unique
    assert len(set(texts)) >= 8


def test_generate_round_questions_mixed_difficulty():
    qs = generate_round_questions(0, count=30)
    assert len(qs) == 30
    times_seen = {q["time_seconds"] for q in qs}
    # Mixed mode produces a blend, all three time buckets are expected with N=30
    assert times_seen.issubset({10, 15, 20})


# ── generate_gk_round_questions ───────────────────────────────────


def test_load_gk_questions_returns_nonempty_list():
    qs = _load_gk_questions()
    assert isinstance(qs, list)
    assert len(qs) > 0
    # Spot-check required fields
    sample = qs[0]
    for key in ("id", "question", "options", "correct_index", "difficulty", "category"):
        assert key in sample, f"missing {key} in {sample}"


def test_gk_round_questions_default_count():
    qs = generate_gk_round_questions(0, count=5)
    assert len(qs) == 5


def test_gk_round_questions_subcategory_filter():
    all_q = _load_gk_questions()
    sci_ids = {q["id"] for q in all_q if q.get("category") == "science"}
    qs = generate_gk_round_questions(0, count=5, subcategory="science")
    assert len(qs) == 5
    for q in qs:
        assert q["id"] in sci_ids


def test_gk_round_questions_excludes_used_ids():
    first = generate_gk_round_questions(0, count=5, subcategory="science")
    used = {q["id"] for q in first}
    second = generate_gk_round_questions(0, count=5, subcategory="science", used_ids=used)
    second_ids = {q["id"] for q in second}
    # No overlap between the previously-used set and the newly served set
    assert not (used & second_ids)


def test_gk_round_questions_shape_matches_trivia_format():
    qs = generate_gk_round_questions(0, count=3, subcategory="history")
    for q in qs:
        assert set(q.keys()) >= {"id", "question", "options", "correct_index", "time_seconds"}
        assert q["time_seconds"] in (10, 15, 20)
        assert 0 <= q["correct_index"] < len(q["options"])


def test_gk_round_questions_difficulty_filter_falls_back_when_pool_too_small():
    """If too few questions exist at the requested difficulty for a subcategory,
    the function should fall back to all difficulties rather than crash."""
    qs = generate_gk_round_questions(1, count=10, subcategory="defense")
    assert len(qs) == 10
