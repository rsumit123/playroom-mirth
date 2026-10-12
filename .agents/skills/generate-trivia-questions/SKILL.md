---
name: generate-trivia-questions
description: Generate, verify, and merge India-specific trivia questions into the question bank. Specify a category or "all" to generate 50 questions per category.
argument-hint: <category|all> [count-per-difficulty]
user-invocable: true
---

# Generate Trivia Questions

You are generating trivia questions for Charade Chat, a multiplayer game platform with an Indian audience. Follow this guide precisely.

## Arguments

- `$ARGUMENTS` — category name (one of: science, history, geography, sports, entertainment, general, mythology, food, politics) OR "all" to generate for every category. Optionally followed by a count-per-difficulty number (default: 17, which produces ~50 questions total across 3 difficulty levels).

Parse the arguments: extract the category (first word) and optional count (second word, default 17).

## Reference

Read `docs/trivia-question-guide.md` for the full specification. The key points are summarized below.

## Step 1: Determine What to Generate

1. Read the current question bank to find existing counts:

```bash
python3 -c "
import json
from collections import Counter
with open('backend/app/data/gk_questions.json') as f:
    data = json.load(f)
for cat in sorted(set(q['category'] for q in data)):
    easy = sum(1 for q in data if q['category'] == cat and q['difficulty'] == 1)
    med = sum(1 for q in data if q['category'] == cat and q['difficulty'] == 2)
    hard = sum(1 for q in data if q['category'] == cat and q['difficulty'] == 3)
    total = easy + med + hard
    print(f'{cat:15s}: {total:4d}  (easy={easy}, med={med}, hard={hard})')
print(f'Total: {len(data)}')
"
```

2. For the requested category (or each category if "all"), determine the next sequence numbers:

```bash
python3 -c "
import json
with open('backend/app/data/gk_questions.json') as f:
    data = json.load(f)
cat = 'CATEGORY_HERE'
for diff_label in ['easy', 'medium', 'hard']:
    diff_num = {'easy': 1, 'medium': 2, 'hard': 3}[diff_label]
    cat_qs = [q for q in data if q['category'] == cat and q['difficulty'] == diff_num]
    max_seq = 0
    for q in cat_qs:
        parts = q['id'].rsplit('_', 1)
        try: max_seq = max(max_seq, int(parts[-1]))
        except: pass
    print(f'{diff_label}: {len(cat_qs)} existing, next sequence starts at {max_seq + 1}')
"
```

## Step 2: Generate Questions

For each category+difficulty combination, generate questions following these rules:

### Category Prefixes

| Category | Prefix |
|----------|--------|
| science | `sci` |
| history | `hist` |
| geography | `geo` |
| sports | `spt` |
| entertainment | `ent` |
| general | `gen` |
| mythology | `myth` |
| food | `food` |
| politics | `pol` |

### JSON Format

```json
{
  "id": "{prefix}_{difficulty_label}_{sequence:03d}",
  "category": "{category}",
  "difficulty": 1,
  "question": "Question text here?",
  "options": ["Option A", "Option B", "Option C", "Option D"],
  "correct_index": 0
}
```

- `difficulty`: 1 = easy, 2 = medium, 3 = hard
- `difficulty_label` in the ID: use `easy`, `medium`, `hard`
- `correct_index`: 0-based index (0, 1, 2, or 3)
- Exactly 4 options per question, always

### Content Requirements

- **India-specific and engaging for Indian players**
- Questions must be factually accurate and verifiable
- One unambiguously correct answer
- Plausible distractors (same domain as correct answer)
- No trick questions, no offensive content
- Concise (1-2 sentences max)
- Cover diverse sub-topics; avoid duplicate topics within a batch

### Category-Specific Guidance

- **science**: ISRO, Indian scientists, Nobel laureates, general science
- **history**: Indian independence, ancient kingdoms, Mughal era, modern India
- **geography**: Indian states, rivers, mountains, national parks, climate
- **sports**: Cricket, IPL, kabaddi, hockey, Indian Olympic medalists
- **entertainment**: Bollywood, Indian cinema, music, TV, pop culture
- **general**: Technology, current affairs, Indian brands, festivals
- **mythology**: Hindu/Buddhist/Jain/tribal mythologies, epics, Puranas, folk traditions
- **food**: Regional cuisine, spices, cooking techniques, GI-tagged foods, street food
- **politics**: Constitution, parliament, elections, court cases, government schemes

### Difficulty Guidelines

| Level | Style |
|-------|-------|
| Easy | Common knowledge, school-level facts |
| Medium | Requires specific knowledge, less commonly known |
| Hard | Obscure details, specific dates/names, niche topics |

### Generation Split

For the default count of 17 per difficulty (total ~50):
- **Easy**: 17 questions
- **Medium**: 17 questions
- **Hard**: 16 questions

Generate each difficulty level separately. Write all generated questions to a temporary file:
`backend/app/data/{category}_generated.json`

## Step 3: Validate JSON Structure

After generating, validate the file:

```bash
python3 -c "
import json
with open('backend/app/data/{category}_generated.json') as f:
    data = json.load(f)
errors = 0
for q in data:
    if not all(k in q for k in ['id', 'category', 'difficulty', 'question', 'options', 'correct_index']):
        print(f'Missing field in {q.get(\"id\", \"UNKNOWN\")}'); errors += 1
    if len(q['options']) != 4:
        print(f'Not 4 options in {q[\"id\"]}'); errors += 1
    if q['correct_index'] < 0 or q['correct_index'] >= 4:
        print(f'Invalid correct_index in {q[\"id\"]}'); errors += 1
    if q['difficulty'] not in [1, 2, 3]:
        print(f'Invalid difficulty in {q[\"id\"]}'); errors += 1
ids = [q['id'] for q in data]
dupes = set(id for id in ids if ids.count(id) > 1)
if dupes: print(f'Duplicate IDs: {dupes}'); errors += len(dupes)
print(f'{len(data)} questions, {errors} errors')
"
```

Fix any errors before proceeding.

## Step 4: Verify Every Question via Web Search

**This is mandatory. Every single question must be verified.**

For each question in the generated file:

1. Use `WebSearch` to search for the core fact in the question
2. Confirm the correct answer matches reliable sources (Wikipedia, official sites)
3. Confirm the distractors are wrong
4. If the answer is wrong: fix `correct_index` or rewrite the question/options
5. If the question is ambiguous (multiple answers could be correct): rewrite or discard
6. Log all corrections made

### Common LLM Errors to Watch For

- **Wrong dates/years** (most common — always verify years)
- **Misattribution** (who did/said/created something)
- **Outdated facts** (political boundaries, records, titles that changed)
- **Confused similar entities** (two people with similar names/roles)
- **Wrong source texts** (attributing a story to the wrong epic/purana)

After verification, update the generated file with all corrections.

## Step 5: Merge into Question Bank

Once all questions are verified:

```bash
python3 -c "
import json

with open('backend/app/data/gk_questions.json') as f:
    existing = json.load(f)
print(f'Existing: {len(existing)}')

with open('backend/app/data/{category}_generated.json') as f:
    new_qs = json.load(f)
print(f'New: {len(new_qs)}')

# Check for ID collisions
existing_ids = set(q['id'] for q in existing)
collisions = [q['id'] for q in new_qs if q['id'] in existing_ids]
if collisions:
    print(f'ERROR: ID collisions: {collisions}')
else:
    existing.extend(new_qs)
    with open('backend/app/data/gk_questions.json', 'w') as f:
        json.dump(existing, f, indent=2)
    print(f'Merged. Total: {len(existing)}')
"
```

## Step 6: Report Results

Print a summary table:

```
Category: {category}
Questions generated: {count}
Questions verified: {count}
Corrections made: {corrections} ({percentage}%)
Final merged total: {new_total}

Breakdown:
  Easy:   {easy_count} (IDs: {prefix}_{easy_start} to {prefix}_{easy_end})
  Medium: {med_count}  (IDs: {prefix}_{med_start} to {prefix}_{med_end})
  Hard:   {hard_count} (IDs: {prefix}_{hard_start} to {prefix}_{hard_end})
```

## Important Notes

- If running for "all" categories, process each category sequentially (generate, verify, merge) to avoid context overload
- For "all", use the Task tool to run categories in parallel where possible — spawn separate agents for generation+verification of each category
- Do NOT skip verification. Our measured error rate is ~1.2% which means ~1 wrong answer per 50 questions
- Hard questions have 2-3x higher error rates than easy questions — verify these extra carefully
- After merging, the temporary `{category}_generated.json` file can be kept for reference or deleted
