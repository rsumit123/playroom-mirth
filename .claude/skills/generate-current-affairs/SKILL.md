---
name: generate-current-affairs
description: Use when adding current_affairs trivia questions sourced from newspaper PDF editions, expanding the question bank from a new date range of papers, or when asked to generate questions from newspapers
argument-hint: <from:YYYY-MM-DD> <to:YYYY-MM-DD> [target-count]
user-invocable: true
---

# Generate Current Affairs Questions from Newspapers

Turns a date range of Indian Express newspaper PDFs into verified, durable
`current_affairs` questions merged into the trivia bank.

**Core principle (from `docs/newspaper-mcq-generation-guide.md`):** the newspaper
gives you the *topic*, not the *question*. Every headline is a door into a durable
concept — a constitutional article, a regulator, a treaty, a geographic feature.
Test the concept, never the day's event.

Read `docs/newspaper-mcq-generation-guide.md` before generating. It holds the
good/avoid table, option-writing rules, and the quality checklist.

## Arguments

`$ARGUMENTS` — `<from-date> <to-date> [target-count]`. Default target: 400 questions.

## Source Material

PDFs live in iCloud. **The directory name has a trailing space** — always quote it:

```bash
NEWS_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Downloads/Newspaper "
```

Filenames come in two shapes — `Kolkata-June-15-2026.pdf` and
`Kolkata---August-05--2026.pdf`. Match with `Kolkata-+([A-Za-z]+)-+(\d+)-+(\d+)`;
a single-dash-only regex silently drops editions. Same-date `(1)` duplicates exist.

## Step 1: OCR the Editions

The PDFs *have* a text layer, but it uses a broken font encoding — `pdftotext`
returns mojibake. **OCR is mandatory.** Run:

```bash
./backend/scripts/ocr_newspapers.sh "$NEWS_DIR" <from> <to> 6
```

Caches to `~/.cache/playroom-ocr/<YYYY-MM-DD>/pNN.txt`, skips editions with a
`.done` marker, so it is safe to re-run. **Launch it in the background and do
Steps 2-3 while it runs.**

Measured throughput: **~14 pages/min at 7 workers on an 8-core machine**, so 89
editions (~1,590 pages) takes **close to two hours**. Parallelism above ~7 gains
little; the job is CPU-bound on tesseract.

Two traps this script already handles, worth knowing if you rewrite it:
- **Render the whole PDF in one `pdftoppm` call.** Calling it per page re-parses
  the entire PDF each time and, for iCloud placeholder files, re-fetches it --
  about 10x slower (measured: 3 pages/min vs 14).
- **`cat` the PDF to /dev/null first** to materialise iCloud dataless files.

Count progress with `find ~/.cache/playroom-ocr -name ".done" | wc -l`. A zsh
glob like `ls ~/.cache/playroom-ocr/*/.done` errors when zero exist and reads as
a failure.

## Step 2: Baseline the Bank

```bash
cd backend && .venv/bin/python -c "
import json, collections
d = json.load(open('app/data/gk_questions.json'))
ca = [q for q in d if q['category'] == 'current_affairs']
print('bank', len(d), 'current_affairs', len(ca))
for lab, n in [('easy',1),('medium',2),('hard',3)]:
    qs = [q for q in ca if q['difficulty'] == n]
    print(lab, len(qs), 'next seq', max(int(q['id'].rsplit('_',1)[1]) for q in qs) + 1)
"
```

IDs are `ca_{easy|medium|hard}_{seq:03d}`, continuing from max+1 per difficulty
(matches `_CATEGORY_PREFIXES` in `backend/app/api/admin.py`).

## Step 3: Mine Anchors, Don't Read Everything

~90 editions is ~1,400 pages — far too much to read page by page. Tier it:

1. **Corpus-wide anchor sweep** (no context cost):
   ```bash
   cd backend && .venv/bin/python scripts/mine_anchors.py \
       --from <from> --to <to> --min-editions 8 --top 26
   ```
   Ranks anchors by the number of *distinct editions* they appear in, so a term
   repeated 50 times in one paper (a one-day story) ranks below a term in 20
   editions (a durable theme). Add `--grep "<term>" --context 250` to pull
   targeted snippets for one anchor.
2. **Read only high-yield pages** — locate them by section header, never by page
   number (they shift between editions):
   ```bash
   .venv/bin/python scripts/classify_pages.py --from <from> --to <to>
   .venv/bin/python scripts/classify_pages.py --from ... --to ... \
       --sections explained,editorial --paths
   ```
   Even so, reading every high-yield page across ~90 editions is ~3.7M tokens.
   Extract *topics* (headline-shaped lines) rather than full pages, and use
   anchors plus your own knowledge for the answer, verified in Step 7.
3. Build a written anchor list before generating a single question.

## Step 4: Generate

Follow the guide's rules. Per-question JSON:

```json
{"id": "ca_easy_550", "category": "current_affairs", "difficulty": 1,
 "question": "...", "options": ["A","B","C","D"], "correct_index": 0}
```

Draft into plain files with the **correct answer first** — it is far easier to
author and review that way. Step 5 shuffles them. Do not hand-randomise.

**Vary the question stem.** The existing bank has ~195 questions built from six
boilerplate stems ("Which institution or body is most directly associated with…").
They read as a fill-in-the-blank table, not as trivia. Write each question as a
sentence a person would actually ask. Do not add to that pile.

Spread difficulty roughly 40/40/20 easy/medium/hard, and spread domains across
polity, economy, international relations, science & tech, geography/environment,
society, and sport/culture.

## Step 5: Assemble (assigns IDs, shuffles answers)

```bash
cd backend && .venv/bin/python scripts/assemble_batch.py \
    app/data/current_affairs_generated_<from>_to_<to>.json draft1.json draft2.json ...
```

Continues IDs from the bank per difficulty and permutes every question's options
deterministically. It prints the difficulty split and answer-position histogram —
check the positions are roughly even before moving on.

## Step 6: Validate Structure

```bash
cd backend && .venv/bin/python -c "
import json
d = json.load(open('app/data/current_affairs_generated_<range>.json'))
errs = []
for q in d:
    if len(q['options']) != 4: errs.append(('options', q['id']))
    if not 0 <= q['correct_index'] <= 3: errs.append(('idx', q['id']))
    if q['difficulty'] not in (1,2,3): errs.append(('diff', q['id']))
    if len(set(q['options'])) != 4: errs.append(('dup-opt', q['id']))
ids = [q['id'] for q in d]
errs += [('dup-id', i) for i in set(ids) if ids.count(i) > 1]
print(len(d), 'questions,', len(errs), 'errors', errs[:20])
"
```

**Also check option-length giveaways.** If the correct option is conspicuously
the longest, the question is guessable without knowing anything:

```bash
cd backend && .venv/bin/python -c "
import json
d = json.load(open('app/data/current_affairs_generated_<range>.json'))
for q in d:
    L = [len(o) for o in q['options']]
    if L[q['correct_index']] == max(L) and max(L) > 1.8*(sum(L)-max(L))/3:
        print(q['id'], q['question'][:70])
"
```

Rewrite the *distractors* to comparable length and specificity — never trim the
correct answer into something inaccurate. Proper-name cases ("The Reserve Bank of
India" against "SEBI") are natural and can be left alone.

## Step 7: Dedup Against the Bank — Two Checks, Both Required

This is the step batch #2 needs and batch #1 never had. 1,391 CA questions already
exist; many obvious anchors (ECI, RBI, Hormuz, Article 356) are taken.

**Check 1 — text similarity:**

```bash
cd backend && .venv/bin/python scripts/dedup_check.py \
    --candidates app/data/current_affairs_generated_<range>.json --threshold 0.55
```

Uses IDF-weighted Jaccard so shared boilerplate doesn't mask real collisions.
Exits non-zero if anything is flagged. Review every flagged pair by hand: a flag
is not automatically a duplicate — two different schemes can share wording — but
you must look.

**Check 2 — same correct answer.** Text similarity cannot see two questions that
use different words to test the identical fact. Group by correct answer, within
the batch and against `current_affairs` + `politics`:

```bash
cd backend && .venv/bin/python -c "
import json, collections
new = json.load(open('app/data/current_affairs_generated_<range>.json'))
bank = json.load(open('app/data/gk_questions.json'))
ans = lambda q: q['options'][q['correct_index']].strip().lower().lstrip('the ')
g = collections.defaultdict(list)
for q in new: g[ans(q)].append(q)
for a, qs in g.items():
    if len(qs) > 1: print('INTRA', a, [q['id'] for q in qs])
gb = collections.defaultdict(list)
for q in bank:
    if q.get('category') in ('current_affairs','politics'): gb[ans(q)].append(q)
for q in new:
    for o in gb.get(ans(q), [])[:2]:
        print('BANK', ans(q), '|', q['question'][:60], '||', o['id'], o['question'][:60])
"
```

Most hits are coincidental (shared years, country names) — judge each. On the
Jun-Sep 2026 run this found **29 genuine redundancies that Check 1 missed
entirely**, against only 18 found by Check 1. Skipping it ships duplicate facts.

## Step 8: Verify Facts

Mandatory, and **report honestly what you actually did**. Measured LLM error rate
on this bank is ~1.2%, concentrated in hard questions.

Triage by risk, then search the risky set individually:

- **Any claim carrying a year, a count, a section number, a case name, or a
  "first/only/largest" superlative** — verify individually, at every difficulty.
  This is where essentially all errors live.
- **Named official terms** — verify rather than assume. On the Jun-Sep run
  "Vyomanaut" looked right and ISRO's actual term is "Gaganyatri".
- **Stable constitutional and institutional facts** — sampling is acceptable.
- Fix `correct_index`, rewrite ambiguous questions, drop anything unverifiable.

Measured error rate on the searched subset of the Jun-Sep batch was **3/24
(12.5%)** — about ten times the 1.2% seen on topic-driven batches, because
newspaper-anchored questions reach for more specific facts. Budget for that.

Watch for questions that are *ambiguous* rather than wrong: one asked what share
of "world seaborne oil trade" passes through Hormuz with the answer "about a
fifth", which is the figure for global *consumption* (seaborne trade is ~25%).

Write a dated note to `backend/app/data/current_affairs_verification_<range>.md`
covering: source range, editions missing, anchors used, both dedup checks and
what each caught, what was verified individually vs. sampled, and every
correction made. State the sampling honestly — never claim per-question
verification you did not perform.

## Step 9: Merge

```bash
cd backend && .venv/bin/python -c "
import json
bank = json.load(open('app/data/gk_questions.json'))
new = json.load(open('app/data/current_affairs_generated_<range>.json'))
ids = {q['id'] for q in bank}
clash = [q['id'] for q in new if q['id'] in ids]
assert not clash, f'ID collision: {clash}'
bank.extend(new)
json.dump(bank, open('app/data/gk_questions.json','w'), indent=2)
print('merged ->', len(bank))
"
```

## Step 10: Test, Commit, Deploy

CLAUDE.md makes these mandatory before any commit:

```bash
cd backend && .venv/bin/python -m pytest --tb=short -q
cd frontend && npm run build && npx vitest run
```

Stage explicitly — the repo carries untracked assets you don't want swept in:

```bash
git add backend/app/data/gk_questions.json \
        backend/app/data/current_affairs_generated_<range>.json \
        backend/app/data/current_affairs_verification_<range>.md
```

**Deployment:** `gk_questions.json` is baked into the Docker image by `COPY . /app`.
The only volume is `./backend/data:/app/data` (SQLite) — `app/data/` is *not*
mounted, so there is **nothing to copy to the VM**. The bank ships via git:

```bash
git push origin main          # VM tracks main, not feature branches
ssh ssh-social 'cd ~/charade-chat && git pull origin main && \
  docker compose build --no-cache && docker compose up -d --force-recreate'
ssh ssh-social 'docker exec charade-backend python -c \
  "import json;print(len(json.load(open(\"/app/app/data/gk_questions.json\"))))"'
```

`--no-cache` matters: plain `docker compose up --build` has served stale layers here.

## Red Flags

| Symptom | Fix |
|---|---|
| Question names a date, toll, score, or price from the news | Rewrite around the durable concept behind it |
| Question would be meaningless in a year | Drop it |
| Many questions share a stem template | Rewrite as natural sentences |
| `pdftotext` output looks like mojibake | Expected — use the OCR script |
| Regex found ~83 editions, not ~90 | Single-dash regex dropped the `---` filenames |
| Merged without running both dedup checks | Revert the merge and dedup first |
| Ran only the text-similarity dedup | Same-answer duplicates are still in there; run Check 2 |
| Every `correct_index` is 0 | You skipped `assemble_batch.py` |
| OCR crawling at ~3 pages/min | `pdftoppm` is being called per page instead of per PDF |
| `ls .../*/.done` reports "no matches found" | zsh glob on a dotfile; use `find ... -name ".done"` |
| Admin-added questions vanished after deploy | Known: `POST /admin/questions` writes to the image layer, not the volume |
