"""Question generators for Trivia game mode (math + general knowledge)."""

import json
import random
import math
from pathlib import Path
from typing import List


# Time per question by difficulty. Minimum 15s — 10s on hard felt brutal in
# practice (people barely finished reading the question).
_TIME_BY_DIFFICULTY = {1: 20, 2: 15, 3: 15}


def _make_distractors(correct: int, count: int = 3) -> list[int]:
    """Generate plausible wrong answers that share the correct answer's units digit."""
    distractors = set()
    target_units = correct % 10
    attempts = 0
    while len(distractors) < count and attempts < 50:
        attempts += 1
        offset = max(1, int(abs(correct) * random.uniform(0.05, 0.25)))
        wrong = correct + random.choice([-1, 1]) * random.randint(1, offset)
        # Snap to same units digit so players can't eliminate by digit pattern
        adjustment = (target_units - wrong % 10) % 10
        wrong += adjustment
        if wrong != correct and wrong > 0:
            distractors.add(wrong)
    # Fallback: step by 10 (preserves units digit)
    step = 10
    while len(distractors) < count:
        for candidate in [correct + step, correct - step]:
            if candidate != correct and candidate > 0 and candidate not in distractors:
                distractors.add(candidate)
                break
        step += 10
    return list(distractors)[:count]


def _build_question(question_text: str, correct: int, difficulty: int) -> dict:
    """Build a question dict with shuffled options."""
    distractors = _make_distractors(correct)
    options = [str(correct)] + [str(d) for d in distractors]
    random.shuffle(options)
    return {
        "question": question_text,
        "options": options,
        "correct_index": options.index(str(correct)),
        "time_seconds": _TIME_BY_DIFFICULTY.get(difficulty, 15),
    }


def _easy_question() -> dict:
    op = random.choice(["add", "sub", "mul"])
    if op == "add":
        a, b = random.randint(1, 50), random.randint(1, 50)
        return _build_question(f"What is {a} + {b}?", a + b, 1)
    elif op == "sub":
        a, b = random.randint(1, 50), random.randint(1, 50)
        if a < b:
            a, b = b, a
        return _build_question(f"What is {a} - {b}?", a - b, 1)
    else:
        a, b = random.randint(2, 12), random.randint(2, 12)
        return _build_question(f"What is {a} \u00d7 {b}?", a * b, 1)


def _medium_question() -> dict:
    op = random.choice(["add", "sub", "mul", "div", "chain"])
    if op == "add":
        a, b = random.randint(10, 200), random.randint(10, 200)
        return _build_question(f"What is {a} + {b}?", a + b, 2)
    elif op == "sub":
        a, b = random.randint(10, 200), random.randint(10, 200)
        if a < b:
            a, b = b, a
        return _build_question(f"What is {a} - {b}?", a - b, 2)
    elif op == "mul":
        a = random.randint(2, 20)
        b = random.randint(10, 50)
        return _build_question(f"What is {a} \u00d7 {b}?", a * b, 2)
    elif op == "div":
        b = random.randint(2, 20)
        quotient = random.randint(2, 20)
        a = b * quotient
        return _build_question(f"What is {a} \u00f7 {b}?", quotient, 2)
    else:
        # Two-operation chain
        a = random.randint(10, 50)
        b = random.randint(5, 30)
        c = random.randint(5, 30)
        if random.random() < 0.5:
            return _build_question(f"What is {a} + {b} - {c}?", a + b - c, 2)
        else:
            m = random.randint(2, 10)
            n = random.randint(1, 20)
            return _build_question(f"What is {m} \u00d7 {b} + {n}?", m * b + n, 2)


def _hard_question() -> dict:
    op = random.choice(["mul", "percent", "sqrt", "chain"])
    if op == "mul":
        a, b = random.randint(10, 99), random.randint(10, 99)
        return _build_question(f"What is {a} \u00d7 {b}?", a * b, 3)
    elif op == "percent":
        pct = random.choice([5, 10, 15, 20, 25, 30, 50, 75])
        base = random.choice([100, 120, 150, 200, 250, 300, 400, 500])
        result = pct * base // 100
        return _build_question(f"What is {pct}% of {base}?", result, 3)
    elif op == "sqrt":
        root = random.randint(2, 20)
        square = root * root
        return _build_question(f"What is \u221a{square}?", root, 3)
    else:
        # Multi-step chain
        a = random.randint(2, 15)
        b = random.randint(2, 15)
        c = random.randint(1, 30)
        d = random.randint(1, 20)
        result = a * b + c - d
        return _build_question(f"What is {a} \u00d7 {b} + {c} - {d}?", result, 3)


def generate_question(difficulty: int) -> dict:
    """Generate a single question for the given difficulty (1=easy, 2=medium, 3=hard)."""
    if difficulty == 1:
        return _easy_question()
    elif difficulty == 3:
        return _hard_question()
    else:
        return _medium_question()


def generate_round_questions(difficulty: int, count: int = 10) -> list[dict]:
    """Generate `count` unique questions for a round.

    difficulty=0 means mixed: 20% easy, 50% medium, 30% hard.
    """
    questions = []
    seen_texts: set[str] = set()
    max_attempts = count * 5  # prevent infinite loop
    attempts = 0
    while len(questions) < count and attempts < max_attempts:
        attempts += 1
        if difficulty == 0:
            r = random.random()
            d = 1 if r < 0.2 else 3 if r > 0.7 else 2
        else:
            d = difficulty
        q = generate_question(d)
        if q["question"] not in seen_texts:
            seen_texts.add(q["question"])
            questions.append(q)
    # Fallback: if we still need more (very unlikely), allow duplicates
    while len(questions) < count:
        if difficulty == 0:
            d = random.choice([1, 2, 3])
        else:
            d = difficulty
        questions.append(generate_question(d))
    return questions


# ── General Knowledge questions ──────────────────────────────────────

_GK_QUESTIONS: list[dict] | None = None


def _load_gk_questions() -> list[dict]:
    """Lazy-load GK questions from JSON file (cached in memory)."""
    global _GK_QUESTIONS
    if _GK_QUESTIONS is None:
        data_path = Path(__file__).parent.parent / "data" / "gk_questions.json"
        with open(data_path, "r") as f:
            _GK_QUESTIONS = json.load(f)
    return _GK_QUESTIONS


def generate_gk_round_questions(
    difficulty: int,
    count: int = 10,
    used_ids: set[str] | None = None,
    subcategory: str | None = None,
) -> list[dict]:
    """Select `count` GK questions, excluding previously used IDs.

    difficulty=0 means mixed: 20% easy, 50% medium, 30% hard.
    subcategory filters to a specific category (e.g. "science", "history").
    None means all categories (general knowledge mix).
    Returns list of dicts matching the trivia question format.
    """
    all_questions = _load_gk_questions()
    used = used_ids or set()

    # Filter by subcategory if specified
    if subcategory:
        all_questions = [q for q in all_questions if q.get("category") == subcategory]

    # Filter out already-used questions
    available = [q for q in all_questions if q["id"] not in used]

    # Filter by difficulty
    if difficulty == 0:
        pool = available  # mixed: sample from all
    else:
        pool = [q for q in available if q["difficulty"] == difficulty]
        if len(pool) < count:
            pool = available  # fall back to all difficulties

    selected = random.sample(pool, min(count, len(pool)))

    # Fallback if not enough unique questions remain
    while len(selected) < count:
        all_at_diff = [q for q in all_questions if difficulty == 0 or q["difficulty"] == difficulty]
        selected.append(random.choice(all_at_diff))

    result = []
    for q in selected:
        result.append({
            "id": q["id"],
            "question": q["question"],
            "options": q["options"],
            "correct_index": q["correct_index"],
            "time_seconds": _TIME_BY_DIFFICULTY.get(q["difficulty"], 15),
        })
    return result
