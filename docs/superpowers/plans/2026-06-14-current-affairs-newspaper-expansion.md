# Current Affairs Newspaper Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add at least 300 durable, newspaper-derived `current_affairs` trivia questions from newly available PDFs, then push and deploy the backend VM.

**Architecture:** The Android and web apps both receive trivia from the backend. New questions are appended to `backend/app/data/gk_questions.json`; the backend lazily loads that JSON through `backend/app/services/trivia.py`, so production needs a backend redeploy after merge.

**Tech Stack:** Python/FastAPI backend, JSON question bank, pytest, React/Vite frontend checks, GitHub, GCP VM Docker deploy.

---

## Source Material

- Primary folder: `/Users/rsumit123/Library/Mobile Documents/com~apple~CloudDocs/Downloads/Newspaper `
- Last used range: `Kolkata-March-29-2026.pdf` through `Kolkata-April-07-2026.pdf`
- New target range: `Kolkata-April-08-2026.pdf` through `Kolkata-June-14-2026.pdf`
- Known missing date: `2026-05-02`
- Target output: at least 300 accepted questions, category `current_affairs`, ID prefix `ca`

## Files

- Modify: `backend/app/data/gk_questions.json`
- Create: `backend/app/data/current_affairs_generated_2026_04_08_to_2026_06_14.json`
- Optional create: `backend/app/data/current_affairs_verification_2026_04_08_to_2026_06_14.md`
- Reference: `docs/trivia-question-guide.md`
- Reference: `docs/newspaper-mcq-generation-guide.md`

## Todo

- [ ] **Step 1: Confirm current bank counts and next ID numbers**

Run:

```bash
python3 - <<'PY'
import json
from collections import Counter
with open('backend/app/data/gk_questions.json') as f:
    data = json.load(f)
ca = [q for q in data if q.get('category') == 'current_affairs']
print('total questions:', len(data))
print('current_affairs:', len(ca))
print('difficulty counts:', Counter(q.get('difficulty') for q in ca))
for label in ['easy', 'medium', 'hard']:
    nums = []
    prefix = f'ca_{label}_'
    for q in ca:
        qid = q.get('id', '')
        if qid.startswith(prefix):
            try:
                nums.append(int(qid[len(prefix):]))
            except ValueError:
                pass
    print(label, 'next:', max(nums, default=0) + 1)
PY
```

Expected: prints existing `current_affairs` count and next `ca_easy_*`, `ca_medium_*`, `ca_hard_*` sequences.

- [ ] **Step 2: Inventory new newspaper PDFs**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
from datetime import date, timedelta
import re
folder = Path('/Users/rsumit123/Library/Mobile Documents/com~apple~CloudDocs/Downloads/Newspaper ')
month = {'January':1,'February':2,'March':3,'April':4,'May':5,'June':6}
items = []
for p in folder.glob('Kolkata-*.pdf'):
    m = re.match(r'Kolkata-([A-Za-z]+)-(\d{2})-(\d{4})(?: \(\d+\))?\.pdf$', p.name)
    if m:
        d = date(int(m.group(3)), month[m.group(1)], int(m.group(2)))
        if date(2026,4,8) <= d <= date(2026,6,14):
            items.append((d, p))
for d, p in sorted(items):
    print(d.isoformat(), p)
print('count:', len(items))
PY
```

Expected: `67` files, April 8 through June 14, missing only May 2.

- [ ] **Step 3: Generate a durable topic shortlist from PDFs**

For each newspaper, read all pages and identify only durable source items:

```bash
mkdir -p /tmp/playroom_news_pages
pdftoppm -png -r 200 -f 1 -l 16 "/path/to/Kolkata-April-08-2026.pdf" /tmp/playroom_news_pages/page
```

Accept topics about courts, laws, bills, institutions, regulators, schemes, treaties, geography, science, public policy, defence, environment, sports institutions, and culture. Reject topics about death counts, exact market numbers, political spectacle, arrests, transient statements, match scores, or details that will feel stale within six months.

- [ ] **Step 4: Draft at least 330 candidate questions**

Generate more than the target so weak/duplicate questions can be discarded. Use this split:

```text
Easy:   105 accepted target, draft about 115
Medium: 120 accepted target, draft about 135
Hard:    75 accepted target, draft about 85
Total:  300 accepted target, draft about 335
```

Every candidate must use this JSON shape:

```json
{
  "id": "ca_easy_380",
  "category": "current_affairs",
  "difficulty": 1,
  "question": "Question text?",
  "options": ["Option A", "Option B", "Option C", "Option D"],
  "correct_index": 0
}
```

Write candidates to:

```text
backend/app/data/current_affairs_generated_2026_04_08_to_2026_06_14.json
```

- [ ] **Step 5: Validate JSON structure**

Run:

```bash
python3 - <<'PY'
import json
path = 'backend/app/data/current_affairs_generated_2026_04_08_to_2026_06_14.json'
with open(path) as f:
    data = json.load(f)
errors = 0
seen = set()
for i, q in enumerate(data):
    for key in ['id', 'category', 'difficulty', 'question', 'options', 'correct_index']:
        if key not in q:
            print('missing', key, 'at index', i); errors += 1
    if q.get('category') != 'current_affairs':
        print('bad category', q.get('id')); errors += 1
    if q.get('difficulty') not in [1, 2, 3]:
        print('bad difficulty', q.get('id')); errors += 1
    if not isinstance(q.get('options'), list) or len(q['options']) != 4:
        print('bad options', q.get('id')); errors += 1
    if not isinstance(q.get('correct_index'), int) or not 0 <= q['correct_index'] <= 3:
        print('bad correct_index', q.get('id')); errors += 1
    if q.get('id') in seen:
        print('duplicate id', q.get('id')); errors += 1
    seen.add(q.get('id'))
print(len(data), 'questions,', errors, 'errors')
raise SystemExit(1 if errors else 0)
PY
```

Expected: at least `300 questions, 0 errors`.

- [ ] **Step 6: Verify quality and durability**

For every question, check:

```text
- Exactly one correct answer.
- The correct answer is supported by the newspaper or a durable authoritative source.
- The question tests the durable concept behind the news, not the short-lived event.
- Distractors are plausible and from the same domain.
- No death counts, exact market figures, match scores, gossip, arrests, or temporary political drama.
- No duplicate concept already present in the existing current_affairs pool.
```

Log corrections in:

```text
backend/app/data/current_affairs_verification_2026_04_08_to_2026_06_14.md
```

- [ ] **Step 7: Merge verified questions into the bank**

Run:

```bash
python3 - <<'PY'
import json
bank = 'backend/app/data/gk_questions.json'
new_path = 'backend/app/data/current_affairs_generated_2026_04_08_to_2026_06_14.json'
with open(bank) as f:
    existing = json.load(f)
with open(new_path) as f:
    new = json.load(f)
existing_ids = {q['id'] for q in existing}
collisions = [q['id'] for q in new if q['id'] in existing_ids]
if collisions:
    print('ERROR collisions:', collisions[:20])
    raise SystemExit(1)
existing.extend(new)
with open(bank, 'w') as f:
    json.dump(existing, f, indent=2)
print('merged', len(new), 'new questions')
print('total', len(existing))
PY
```

Expected: no ID collisions; total increases by at least `300`.

- [ ] **Step 8: Run backend trivia-focused tests first**

Run:

```bash
cd backend && .venv/bin/python -m pytest app/tests/test_trivia_service.py app/tests/test_trivia_socket.py --tb=short -q
```

Expected: all tests pass.

- [ ] **Step 9: Run required full verification before commit**

Run:

```bash
cd backend && .venv/bin/python -m pytest --tb=short -q
cd ../frontend && npm run build
cd ../frontend && npx vitest run
```

Expected: backend tests pass, frontend build succeeds, vitest passes.

- [ ] **Step 10: Review git diff and avoid unrelated local changes**

Run:

```bash
git status --short
git diff -- backend/app/data/gk_questions.json backend/app/data/current_affairs_generated_2026_04_08_to_2026_06_14.json
```

Do not stage unrelated local files currently present in the workspace, such as `frontend/android/app/build.gradle`, `.agents/`, or `AGENTS.md`, unless the user explicitly asks.

- [ ] **Step 11: Commit and push**

Run:

```bash
git add backend/app/data/gk_questions.json backend/app/data/current_affairs_generated_2026_04_08_to_2026_06_14.json backend/app/data/current_affairs_verification_2026_04_08_to_2026_06_14.md
git commit -m "feat: add verified current affairs questions through Jun 14"
git push origin main
```

Expected: push succeeds to `origin/main`.

- [ ] **Step 12: Deploy backend VM**

Run:

```bash
gcloud compute ssh socialflow --project=polar-pillar-450607-b7 --zone=us-east1-d -- "cd charade-chat && git stash 2>/dev/null; git pull origin main && export GOOGLE_CLIENT_ID='929006071236-55m4f4gujp7nnu9ldirbkrmr4qn30ng1.apps.googleusercontent.com' && cd backend && docker compose down && docker compose up --build -d"
```

Expected: backend container rebuilds and starts.

- [ ] **Step 13: Verify production backend**

Run:

```bash
curl -s https://charade-api.skdev.one/health | head -20
```

Expected: healthy response from production backend.

- [ ] **Step 14: Final report**

Report:

```text
Questions generated:
Questions accepted:
Difficulty split:
Source PDF range:
Tests:
Commit:
Push:
Backend deploy:
Production health:
```
