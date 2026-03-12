# Trivia Question Generation & Verification Guide

This document describes how trivia questions are authored, verified, stored, and served in the Charade Chat platform.

---

## Table of Contents

1. [Question Bank Overview](#question-bank-overview)
2. [JSON Format](#json-format)
3. [ID Naming Convention](#id-naming-convention)
4. [Content Guidelines](#content-guidelines)
5. [Generating Questions with an LLM](#generating-questions-with-an-llm)
6. [Verification via Web Search](#verification-via-web-search)
7. [How the Backend Reads Questions](#how-the-backend-reads-questions)
8. [Adding Questions via the Admin UI](#adding-questions-via-the-admin-ui)
9. [Category & Difficulty Distribution](#category--difficulty-distribution)

---

## Question Bank Overview

All general-knowledge trivia questions live in a single JSON file:

```
backend/app/data/gk_questions.json
```

As of the latest update the file contains **3,051 questions** across **9 categories**:

| Category       | Total | Easy | Medium | Hard |
|----------------|-------|------|--------|------|
| science        | 458   | 143  | 157    | 158  |
| mythology      | 458   | 180  | 150    | 128  |
| food           | 458   | 180  | 150    | 128  |
| politics       | 458   | 180  | 155    | 123  |
| general        | 322   | 95   | 122    | 105  |
| history        | 229   | 75   | 77     | 77   |
| entertainment  | 224   | 74   | 76     | 74   |
| geography      | 223   | 71   | 76     | 76   |
| sports         | 221   | 73   | 74     | 74   |

A separate **math** category uses algorithmically generated arithmetic problems (not stored in JSON).

---

## JSON Format

Each question is a JSON object with these fields:

```json
{
  "id": "myth_easy_001",
  "category": "mythology",
  "difficulty": 1,
  "question": "How many heads did Ravana have?",
  "options": ["5", "10", "7", "12"],
  "correct_index": 1
}
```

| Field           | Type       | Description                                      |
|-----------------|------------|--------------------------------------------------|
| `id`            | `string`   | Unique identifier (see naming convention below)  |
| `category`      | `string`   | One of the 9 category slugs                      |
| `difficulty`    | `integer`  | `1` = easy, `2` = medium, `3` = hard             |
| `question`      | `string`   | The question text                                |
| `options`       | `string[]` | Exactly 4 answer choices                         |
| `correct_index` | `integer`  | 0-based index of the correct option (0, 1, 2, or 3) |

The top-level structure of `gk_questions.json` is a flat JSON array:

```json
[
  { "id": "sci_1_001", ... },
  { "id": "sci_1_002", ... },
  ...
]
```

---

## ID Naming Convention

Question IDs follow the pattern: `{prefix}_{difficulty}_{sequence}`

### Category Prefixes

| Category       | Prefix  |
|----------------|---------|
| science        | `sci`   |
| history        | `hist`  |
| geography      | `geo`   |
| sports         | `spt`   |
| entertainment  | `ent`   |
| general        | `gen`   |
| mythology      | `myth`  |
| food           | `food`  |
| politics       | `pol`   |

### Difficulty Labels

Two conventions exist in the codebase (both are valid, IDs just need to be unique):

- **Numeric**: `1`, `2`, `3` (e.g., `sci_1_001`, `sci_2_001`, `sci_3_001`)
- **Named**: `easy`, `medium`, `hard` (e.g., `myth_easy_001`, `food_hard_042`)

### Examples

```
sci_1_001      → science, easy, question #1
hist_2_045     → history, medium, question #45
myth_hard_079  → mythology, hard, question #79
food_easy_130  → food, easy, question #130
pol_medium_110 → politics, medium, question #110
```

Sequence numbers are zero-padded to 3 digits (e.g., `001`, `042`, `130`).

---

## Content Guidelines

### India-Specific Focus

Our target audience is primarily Indian players. Questions should be **engaging and relatable** to an Indian audience. This means:

- **History**: Indian history, independence movement, ancient kingdoms, Mughal era, modern India.
- **Geography**: Indian states, rivers, mountains, national parks, cities, climate.
- **Sports**: Cricket (IPL, World Cup, Indian players), kabaddi, hockey, Indian Olympic medalists.
- **Entertainment**: Bollywood, Indian cinema, music, TV, Indian pop culture.
- **Science**: General science with an Indian flavour where possible (ISRO, Indian scientists, Nobel laureates from India).
- **General**: Technology, computers, current affairs, Indian brands, festivals.
- **Mythology**: Hindu, Buddhist, Jain, tribal mythologies of India. Epics (Ramayana, Mahabharata), Puranas, Vedic literature, folk traditions.
- **Food**: Indian cuisine, regional specialities, spices, cooking techniques, food history, GI-tagged foods, street food, traditional preparations.
- **Politics**: Indian constitution, parliamentary system, elections, landmark court cases, government schemes, political history.

### Difficulty Levels

| Level  | Target Audience | Style |
|--------|-----------------|-------|
| Easy   | Anyone familiar with India | Common knowledge, well-known facts, frequently asked in school exams |
| Medium | Someone with moderate general knowledge | Requires specific knowledge, less commonly known facts |
| Hard   | Trivia enthusiasts / quiz buffs | Obscure details, dates, specific names, niche topics |

### Question Quality Rules

1. **Exactly 4 options** per question, always.
2. **One unambiguously correct answer**. Avoid questions where multiple options could be argued as correct.
3. **Plausible distractors**. Wrong options should be in the same domain as the correct answer (e.g., all options are Indian cities, or all are years, or all are names of scientists).
4. **No trick questions**. The question should test knowledge, not reading comprehension.
5. **Self-contained**. Each question must make sense without external context.
6. **Factually accurate**. Every question must be verifiable via reliable sources.
7. **No offensive content**. Avoid controversial, politically sensitive, or potentially hurtful questions.
8. **Keep questions concise**. Aim for 1-2 sentences maximum.

---

## Generating Questions with an LLM

We use an LLM (Claude) to generate questions in bulk, with careful prompting and mandatory verification.

### Step 1: Prompt Design

A good generation prompt includes:

- The **category** and **difficulty level**
- The **India-specific focus** requirement
- The **JSON format** with an example
- The **number of questions** to generate
- Instructions to avoid duplicate topics within the batch
- Instructions to make distractors plausible

Example prompt structure:

```
Generate {count} trivia questions for category "{category}" at difficulty
level {difficulty} (1=easy, 2=medium, 3=hard).

Requirements:
- Questions should be India-specific and engaging for an Indian audience
- Each question must have exactly 4 options with one unambiguously correct answer
- Distractors should be plausible (same domain as the correct answer)
- Avoid duplicate topics within this batch
- Cover diverse sub-topics within the category

Output as a JSON array with this format:
[
  {
    "id": "{prefix}_{difficulty_label}_{sequence:03d}",
    "category": "{category}",
    "difficulty": {difficulty},
    "question": "...",
    "options": ["...", "...", "...", "..."],
    "correct_index": 0
  }
]

Start sequence numbering from {start_number}.
```

### Step 2: Generate in Batches

- Generate **40-60 questions per batch** to maintain quality.
- Separate batches by difficulty level (all easy, then all medium, then all hard).
- Track sequence numbers across batches to avoid ID collisions.

### Step 3: Validate JSON Structure

After generation, validate that:

```python
import json

with open("new_questions.json") as f:
    data = json.load(f)

for q in data:
    assert all(k in q for k in ["id", "category", "difficulty", "question", "options", "correct_index"])
    assert len(q["options"]) == 4
    assert 0 <= q["correct_index"] <= 3
    assert q["difficulty"] in [1, 2, 3]

print(f"All {len(data)} questions pass structural validation.")
```

---

## Verification via Web Search

**Every single question must be verified** against reliable web sources before being added to the question bank. This is non-negotiable for quality.

### Verification Process

For each question:

1. **Search the web** for the core fact claimed in the question.
2. **Check against 2+ sources** (Wikipedia, official sites, established references).
3. **Verify the correct answer** is indeed correct.
4. **Verify the distractors** are indeed wrong (no ambiguity).
5. **Fix or discard** any question that cannot be verified.

### Common Error Types Found During Verification

Based on our experience verifying ~3,000 questions, these are the most common LLM errors:

| Error Type | Example | Frequency |
|------------|---------|-----------|
| **Wrong dates/years** | "Aminia established in 1920" (actually 1929) | Most common |
| **Misattribution** | "Given by Agni" vs "Given by Varuna through Agni" | Common |
| **Outdated facts** | "Hyderabad is joint capital of AP and Telangana" (ended 2024) | Occasional |
| **Confused similar entities** | Mixing up two Nawabs of Awadh | Occasional |
| **Wrong source text** | "Savitri story from Matsya Purana" (actually Mahabharata) | Occasional |
| **Incorrect statistics** | Wrong daily count of Tirupati laddus | Occasional |

### Verification Rate

From our verification of 974 questions across mythology, food, and politics:

- **Total corrections needed**: 12 out of 974 (~1.2% error rate)
- **Ambiguous questions flagged**: 8 (kept but noted)
- **Error rate by difficulty**: Hard questions had the highest error rate (~2-3%), easy questions the lowest (<0.5%)

### Automated Verification Script Pattern

```
For each question in the batch:
  1. Web search: "{key fact from question} {key terms}"
  2. Extract answer from search results
  3. Compare with the question's claimed correct answer
  4. If mismatch:
     - Determine the correct answer from sources
     - Update the question's correct_index or rewrite the question
     - Log the correction
  5. If ambiguous:
     - Flag for manual review
     - Document the ambiguity
```

---

## How the Backend Reads Questions

### File Loading

Questions are loaded from `gk_questions.json` with lazy initialization and in-memory caching:

```python
# backend/app/services/trivia.py

_GK_QUESTIONS: list[dict] | None = None

def _load_gk_questions() -> list[dict]:
    global _GK_QUESTIONS
    if _GK_QUESTIONS is None:
        data_path = Path(__file__).parent.parent / "data" / "gk_questions.json"
        with open(data_path, "r") as f:
            _GK_QUESTIONS = json.load(f)
    return _GK_QUESTIONS
```

The cache is reset when questions are added/deleted via the admin API (by setting `_GK_QUESTIONS = None`).

### Category Routing

When a trivia game starts, the selected category determines how questions are loaded:

```python
# backend/app/sockets/events.py

_GK_SUBCATEGORIES = {
    "science", "history", "geography", "sports",
    "entertainment", "general", "mythology", "food", "politics"
}

if state.trivia_category == "general_knowledge" or state.trivia_category in _GK_SUBCATEGORIES:
    subcategory = state.trivia_category if state.trivia_category in _GK_SUBCATEGORIES else None
    questions = generate_gk_round_questions(
        state.difficulty, count=10, used_ids=state.used_question_ids,
        subcategory=subcategory,
    )
else:
    # Math category — generated algorithmically
    questions = generate_round_questions(state.difficulty, count=10)
```

| User Selection      | `subcategory` param | Questions drawn from |
|---------------------|---------------------|----------------------|
| General Knowledge   | `None`              | All 3,051 questions (all 9 categories mixed) |
| Science             | `"science"`         | Only 458 science questions |
| Mythology           | `"mythology"`       | Only 458 mythology questions |
| Math                | N/A                 | Algorithmically generated arithmetic |

### Question Selection Algorithm

```python
def generate_gk_round_questions(difficulty, count=10, used_ids=None, subcategory=None):
    all_questions = _load_gk_questions()

    # 1. Filter by subcategory (if specific category selected)
    if subcategory:
        all_questions = [q for q in all_questions if q["category"] == subcategory]

    # 2. Exclude already-used questions (within the same game session)
    available = [q for q in all_questions if q["id"] not in used_ids]

    # 3. Filter by difficulty
    if difficulty == 0:  # mixed mode
        pool = available
    else:
        pool = [q for q in available if q["difficulty"] == difficulty]
        if len(pool) < count:
            pool = available  # fallback to all difficulties

    # 4. Random sample
    selected = random.sample(pool, min(count, len(pool)))

    # 5. Format for delivery (strips category, adds time_seconds)
    return [{"id": q["id"], "question": q["question"], "options": q["options"],
             "correct_index": q["correct_index"],
             "time_seconds": TIME_BY_DIFFICULTY[q["difficulty"]]} for q in selected]
```

### Deduplication

- **Within a game**: The `used_question_ids` set tracks every question ID shown during the game session. Questions are never repeated within the same game.
- **Across games**: No cross-game deduplication. With 1,071 easy questions and 10 per game, players can play 21+ games on easy mode before seeing repeats.

### Time Limits by Difficulty

| Difficulty | Time per Question |
|------------|-------------------|
| Easy (1)   | 20 seconds        |
| Medium (2) | 15 seconds        |
| Hard (3)   | 10 seconds        |

---

## Adding Questions via the Admin UI

The admin dashboard at `/admin` provides a UI for managing questions. Behind the scenes it uses these API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/questions` | GET | List questions with search, category, difficulty filters + pagination |
| `/api/admin/questions` | POST | Add a new question (auto-generates ID using category prefix) |
| `/api/admin/questions/{id}` | DELETE | Remove a question by ID |

### Auto-generated IDs (Admin API)

When creating a question via the admin API, the ID is auto-generated:

```python
_CATEGORY_PREFIXES = {
    "science": "sci", "history": "hist", "geography": "geo",
    "sports": "spt", "entertainment": "ent", "general": "gen",
    "mythology": "myth", "food": "food", "politics": "pol",
}

# Pattern: {prefix}_{difficulty_label}_{next_sequence:03d}
# Example: myth_medium_151
```

The API finds the highest existing sequence number for that prefix+difficulty combination and increments by 1.

---

## Category & Difficulty Distribution

### Target Distribution

For a balanced experience, aim for roughly equal questions per category. Current targets:

- **Major categories** (science, mythology, food, politics): ~450+ each
- **Other categories** (history, geography, sports, entertainment, general): ~220-320 each (expansion planned)

### Difficulty Split

Within each category, aim for:

- **Easy**: ~35-40% (most players play easy mode)
- **Medium**: ~30-35%
- **Hard**: ~25-30%

### Repetition Analysis

With 10 questions per game (per round), the number of games before repeats:

| Difficulty | Total Questions | Games Before Repeats |
|------------|-----------------|----------------------|
| Easy       | 1,071           | ~21 games            |
| Medium     | 1,037           | ~20 games            |
| Hard       | 943             | ~18 games            |
| Mixed      | 3,051           | ~61 games            |

---

## Adding a New Category

To add a new trivia category:

1. **Generate questions** following the content guidelines and JSON format above.
2. **Verify every question** via web search.
3. **Merge into `gk_questions.json`** (append to the array).
4. **Update `_GK_SUBCATEGORIES`** in `backend/app/sockets/events.py` (add the new category slug).
5. **Update `_CATEGORY_PREFIXES`** in `backend/app/api/admin.py` (add the prefix for admin ID generation).
6. **Update frontend selectors**:
   - `frontend/src/ui/components/TriviaCategorySelector.jsx` — add to `CATEGORIES` array.
   - `frontend/src/ui/pages/AdminDashboardPage.jsx` — add to `CAT_ICONS` and `CATEGORIES`.
7. **Deploy** both backend and frontend.
