# Practical Indian Law Trivia Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the bland article-first Indian Law trivia batch with 500 short, useful daily-life legal literacy questions.

**Architecture:** Keep the existing `indian_law` category wiring unchanged. Replace only the content generator and generated data so `backend/app/data/indian_law_generated_500.json` and the Indian Law slice in `backend/app/data/gk_questions.json` contain practical, non-repetitive questions.

**Tech Stack:** Python script for deterministic generation, JSON question bank, existing backend pytest coverage.

---

### Task 1: Rewrite Content Generator

**Files:**
- Modify: `scripts/regenerate_indian_law_questions.py`

- [ ] Replace article-first ordering with bucketed generation:
  - practical rights and safeguards
  - criminal law basics
  - landmark judgments
  - legal terms
  - consumer/cyber/workplace/family law
  - courts, lawyers, legal aid, forums
  - legal history and important people
  - limited article/section precision

- [ ] Enforce quality gates in the script:
  - 500 total questions
  - 220 easy, 200 medium, 80 hard
  - 4 options per question
  - no duplicate question text
  - no repeated normalized correct answer
  - article-number answers capped at 15
  - first 20 easy questions must not be article-number prompts

### Task 2: Regenerate Data

**Files:**
- Modify: `backend/app/data/indian_law_generated_500.json`
- Modify: `backend/app/data/gk_questions.json`

- [ ] Run `python3 scripts/regenerate_indian_law_questions.py`.
- [ ] Confirm output writes 500 Indian Law questions and merged bank total remains stable.

### Task 3: Update Audit Note

**Files:**
- Modify: `backend/app/data/indian_law_audit_2026_06_16.md`

- [ ] Record the practical-first content model.
- [ ] Record the article-number cap and duplicate checks.

### Task 4: Verify

**Commands:**
- `python3 -m json.tool backend/app/data/indian_law_generated_500.json >/tmp/indian_law_generated_500.valid.json`
- `python3 -m json.tool backend/app/data/gk_questions.json >/tmp/gk_questions.valid.json`
- `cd backend && .venv/bin/python -m pytest app/tests/test_matchmaker.py -q`

- [ ] Confirm all commands exit 0.
- [ ] Print sample first 20 questions and duplicate metrics.
