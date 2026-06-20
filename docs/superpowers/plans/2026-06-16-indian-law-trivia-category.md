# Indian Law Trivia Category Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an `indian_law` trivia category with 500 practical legal-literacy questions for Indian players.

**Architecture:** The existing trivia system stores non-math questions in `backend/app/data/gk_questions.json` and filters by `category`. Add the new category slug to the frontend selector, backend quickmatch category list, trivia subcategory allowlist, and admin ID prefix map. Generate a separate reviewed batch file, validate it, then merge into the flat question bank.

**Tech Stack:** React 18/Vite frontend, FastAPI/socket backend, JSON question bank, pytest, vitest.

---

### Task 1: Category Plumbing

**Files:**
- Modify: `frontend/src/ui/components/TriviaCategorySelector.jsx`
- Modify: `frontend/src/ui/components/__tests__/TriviaCategorySelector.test.jsx`
- Modify: `backend/app/services/matchmaker.py`
- Modify: `backend/app/tests/test_matchmaker.py`
- Modify: `backend/app/sockets/events.py`
- Modify: `backend/app/api/admin.py`

- [ ] **Step 1: Write failing frontend selector test**

Add `Indian Law` to `ALL_CATEGORY_LABELS`, expect 14 buttons, and verify clicking it passes `indian_law`.

- [ ] **Step 2: Write failing backend category tests**

Assert `indian_law` is in `matchmaker.GK_CATEGORIES`, and add a focused text-level check that `_GK_SUBCATEGORIES` in `backend/app/sockets/events.py` contains `indian_law`.

- [ ] **Step 3: Run focused tests and confirm failure**

Run:

```bash
cd frontend && npx vitest run src/ui/components/__tests__/TriviaCategorySelector.test.jsx
cd backend && .venv/bin/python -m pytest app/tests/test_matchmaker.py -q
```

- [ ] **Step 4: Implement category support**

Add:
- Frontend label: `Indian Law`
- Slug: `indian_law`
- Icon: legal/court-style icon
- Backend quickmatch category entry
- Trivia subcategory allowlist entry
- Admin prefix: `law`

- [ ] **Step 5: Re-run focused tests**

Expected: all focused tests pass.

### Task 2: Question Batch

**Files:**
- Create: `backend/app/data/indian_law_generated_500.json`
- Create: `backend/app/data/indian_law_verification_500.md`
- Modify: `backend/app/data/gk_questions.json`

- [ ] **Step 1: Generate 500 questions**

Use this split:
- Easy: 220
- Medium: 200
- Hard: 80

Use IDs:
- `law_easy_001` through `law_easy_220`
- `law_medium_001` through `law_medium_200`
- `law_hard_001` through `law_hard_080`

- [ ] **Step 2: Validate generated JSON**

Check required fields, option count, valid `correct_index`, unique IDs, and no repeated question text.

- [ ] **Step 3: Verification notes**

Write a verification note that lists the official source families used: India Code, Ministry of Home Affairs criminal law documents, NALSA legal aid resources, consumer/cyber/traffic official portals where applicable.

- [ ] **Step 4: Merge into `gk_questions.json`**

Append the 500 generated questions after validating no ID collisions.

### Task 3: Full Verification

**Files:**
- All touched files

- [ ] **Step 1: Run backend tests**

```bash
cd backend && .venv/bin/python -m pytest --tb=short -q
```

- [ ] **Step 2: Run frontend build**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: Run frontend tests**

```bash
cd frontend && npx vitest run
```

- [ ] **Step 4: Report status**

Report total `indian_law` count and final question-bank total. Do not deploy unless explicitly requested.
