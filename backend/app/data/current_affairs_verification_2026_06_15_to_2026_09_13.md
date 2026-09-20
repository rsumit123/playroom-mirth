# Current Affairs Verification Notes - Jun 15 to Sep 13, 2026

Second newspaper-sourced `current_affairs` batch. 223 questions generated from
Indian Express (Kolkata edition) PDFs covering Jun 15 - Sep 13, 2026.

## Source Material

- PDF folder: `~/Library/Mobile Documents/com~apple~CloudDocs/Downloads/Newspaper `
  (note the trailing space in the directory name)
- Range: `Kolkata-June-15-2026.pdf` through `Kolkata-September-13-2026.pdf`
- **89 editions** OCRed, **1,588 pages**, 0 failures
- Missing dates in range: `2026-06-26`, `2026-08-16`
- 7 editions use an alternate filename shape (`Kolkata---August-05--2026.pdf`);
  a single-dash regex silently drops these. The resolver handles both.
- OCR cache: `~/.cache/playroom-ocr/<YYYY-MM-DD>/pNN.txt` (re-runnable, `.done` markers)

The PDFs carry a text layer, but its font encoding is broken and `pdftotext`
returns mojibake. Full OCR via `pdftoppm` + `tesseract` was required.

## Method

Reading 1,588 pages directly was not viable, so the corpus was tiered:

1. `scripts/mine_anchors.py` - grep-based, zero context cost. Ranks anchors by
   the number of *distinct editions* they appear in, so a term repeated 50 times
   in one paper (a one-day story) ranks below a term appearing in 20 editions
   (a durable theme).
2. `scripts/classify_pages.py` - labels each page by section so only high-yield
   pages (Explained / Editorial / Ideas / World / Economy) were consulted.
3. Targeted `--grep` context snippets for specific anchors.

Questions were then written against the durable concept behind each anchor, per
`docs/newspaper-mcq-generation-guide.md`: the news supplies the hook, the
institution/law/treaty/geography supplies the payload.

## Dominant Anchors Observed (by edition frequency, of 89)

- Strait of Hormuz (76), Gulf of Oman, Gulf of Aden - West Asia energy security
- SARFAESI / Securitisation and Reconstruction of Financial Assets Act, 2002 (76)
- High Court (89), Supreme Court (88), SEBI (64), RBI (63), ISRO (40), ECI (40)
- BRICS (48), NATO (38), UN (35), UNESCO (27), ASEAN (27), Quad (26)
- Semiconductors (32), Tejas (27), BrahMos (10), Gaganyaan (9)
- Article 370 (21), Uniform Civil Code (17), Delimitation Bill (14)
- Section 301 US trade law (19), Indus Waters Treaty (9)
- Ayushman Bharat (15), Jal Jeevan (10), PMGSY (8)

Newspaper hooks used include: MeitY content blocking, DG Shipping and seafarer
regulation, SIR of electoral rolls, Ladakh's Sixth Schedule demand, creamy-layer
affidavit, UN Secretary-General selection, Atal Setu / Third Mumbai, preliminary
enquiry and FIR jurisprudence, AI chatbots and minors, surrogate advertising
notices, monsoon performance, buffalo meat exports, Semicon phase 2.

## Deduplication

This is the step the Apr-Jun batch did not have, and it mattered.

`scripts/dedup_check.py` uses **IDF-weighted Jaccard** against the whole bank,
not just `current_affairs`. Plain Jaccard is unusable here: ~195 existing CA
questions share six boilerplate stems ("Which institution or body is most
directly associated with ..."), and unweighted scoring flags every pair of them
at 0.5+ despite asking about entirely different subjects. IDF drives those shared
tokens to near zero so only distinctive entities count.

Two orthogonal checks were run, because they catch different things.

**1. IDF-weighted text similarity** (new -> whole bank). 18 candidates flagged and
removed or rewritten, including 2 exact duplicates. Most collisions were against
*other* categories - `politics`, `geography`, `defense`, `science` - not
`current_affairs`:

- `Who administers the oath of office to the President of India?` (exact, vs politics)
- `The Strait of Hormuz connects the Persian Gulf to which body of water?` (exact, vs current_affairs)
- Money Bill / Panchayati Raj / Sundarbans / Tejas / BrahMos / NHRC / Sixth Schedule
- INS Vikrant shipyard, NCBC, Indus Waters Treaty year, Jal Jeevan, ICMR

**2. Same-correct-answer grouping** (intra-batch, and vs `current_affairs` +
`politics`). This catches redundancy that text similarity misses entirely: two
questions with different vocabulary that test the identical fact. It found **29
more**, e.g. a Finance Commission question duplicated within the batch, and
Article 44 / Article 32 / Article 123 / Article 3 / Article 21A / Article 112 /
mandamus / PAC / CAG / CRR / Ramsar / FSSAI / CCI / BNS / NEP questions that
simply re-ask facts already in `politics` or `current_affairs`.

**Text similarity alone would have shipped all 29.** Both checks are needed.

Final batch: **223 questions, 0 flagged on either check.**

## Fact Verification - what was actually done

Honest scope: this was **targeted sampling, not per-question verification of all
252**. Claims were triaged by risk and the high-risk set was searched
individually. Low-risk items (stable constitutional provisions, well-known
institutional mandates, geography) were not individually searched.

Verified by web search (24 claims, 20 searches). Coverage is weighted to hard
questions and to any claim carrying a year, a count, a section number or a case
name; stable constitutional and institutional facts were not individually searched:

| Claim | Result |
|---|---|
| Carbon Credit Trading Scheme administrator | **CORRECTED** - was MoEFCC, is Bureau of Energy Efficiency |
| Strait of Hormuz share of oil | **CORRECTED** - conflated seaborne trade (~25%) with global consumption (~20%); question rewritten to global consumption |
| NDB first president from India (K.V. Kamath) | confirmed |
| RPwD Act 2016 - 21 specified disabilities | confirmed |
| IT Act intermediary defined at Section 2(1)(w) | confirmed |
| Section 69A Blocking Rules notified 2009 | confirmed |
| IBC outer limit 330 days | confirmed |
| MTCR Category I: 500 kg / 300 km; India joined 2016 | confirmed |
| IFC-IOR located at Gurugram | confirmed |
| 42nd Amendment froze Lok Sabha seats on 1971 census | confirmed |
| Aditya-L1 carries seven payloads | confirmed |
| NCBC constitutional status via 102nd Amendment | confirmed |
| CTF-151 counter-piracy off Somalia | confirmed |
| IMD cloudburst threshold 100 mm/hour | confirmed |
| IMD "normal" monsoon = 96-104% of LPA | confirmed |
| Permanent Indus Commission meets at least yearly | confirmed |
| ISRO term for a Gaganyaan astronaut | **CORRECTED** - was "Vyomanaut"; ISRO's official term is "Gaganyatri" |
| SARFAESI 13(2) 60-day notice / s.14 DM / s.17 DRT appeal | confirmed |
| NEP 2020 school structure 5+3+3+4 | confirmed |
| Delimitation Commission orders have force of law, not questionable in court | confirmed |
| Public Examinations (Prevention of Unfair Means) Act, 2024 | confirmed |
| Indra Sawhney 50% ceiling; M. Nagaraj promotion conditions | confirmed |

**Corrections made: 3.** All three were genuine factual errors that would have
shipped: the carbon credit administrator, the Hormuz oil share, and the Gaganyaan
astronaut term. Observed error rate on the searched subset was 3/24 (12.5%),
roughly ten times the 1.2% baseline measured on earlier topic-driven batches -
newspaper-anchored questions reach for more specific facts and need more checking.

## Other quality fixes applied

- **Answer position**: drafts were authored with the correct option first. All
  were deterministically shuffled. Final distribution: 0:51, 1:62, 2:57, 3:53.
- **Option-length giveaways**: 10 questions where the correct answer was
  conspicuously the longest option had their distractors rewritten to comparable
  length and specificity. The 14 remaining are natural proper-name cases
  ("The Reserve Bank of India" vs "SEBI") and were left alone.
- **Durability**: one question about a single state's 2026 data-centre policy was
  dropped for failing the one-year durability test.
- **One circular question** ("...derive their powers from which paragraph-based
  framework?" answered by "the Sixth Schedule itself") was rewritten.
- **Two wording fixes**: the IAEA is not formally a "specialised UN agency"
  (that question was dropped in dedup anyway), and Malabar is not formally a Quad
  exercise, so that question now names the four navies instead.
- **Stem variety**: deliberately avoided the six boilerplate stems that dominate
  ~195 questions of the existing CA bank. Every question is written as a sentence
  a person would actually ask.

## Known issues NOT addressed in this batch

- The pre-existing 1,391 CA questions contain ~76 IDF-weighted near-duplicate
  pairs, some genuine (e.g. `ca_easy_544` / `ca_easy_545` ask the same ethanol
  blending fact forward and backward). Not touched here.
- ~195 pre-existing CA questions use formulaic stems. Not rewritten here.
- `POST /admin/questions` writes to `app/data/` inside the image, which is not
  volume-mounted. Questions added through the admin UI are lost on every
  container rebuild. Unrelated to this batch but worth fixing.

## Test status at merge

- Backend: 268 passed, 3 failed. The 3 failures (`test_charades_scribble_e2e.py`
  x2, `test_scoreboard.py`) are **pre-existing and environmental** - they require
  a live backend on `localhost:8005` and fail identically on the unmerged bank.
- Frontend: `npm run build` clean; vitest 173/173 passed.
- Bank: 9,065 -> 9,288 questions; `current_affairs` 1,391 -> 1,614.

## Composition

- Total: 223 (easy 65, medium 92, hard 66)
- ID ranges: `ca_easy_550`+, `ca_medium_604`+, `ca_hard_305`+
- Domains: polity/governance, economy & markets, international relations,
  science & technology, geography & environment, society & law, sport & culture
