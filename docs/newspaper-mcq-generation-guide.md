# Generating Current Affairs MCQs from Newspaper PDFs

A step-by-step guide for producing exam-quality (UPSC/SSC/State PCS style) MCQs from daily newspaper PDFs using Claude Code.

---

## Step 1: Read the Entire Newspaper PDF

- Use `pdftoppm` (from `poppler`) to convert each page of the PDF into PNG images.
- Read every page — front page, nation, parliament, economy, explained, editorial, world, and sports sections all contain question-worthy material.
- Scanned/image-based PDFs won't yield usable text via `pdftotext`, so image-based reading is the reliable path.

```bash
# Install poppler if not already available
brew install poppler

# Convert pages to images (adjust page ranges as needed)
pdftoppm -png -r 200 -f 1 -l 8 newspaper.pdf /tmp/news_page
```

---

## Step 2: Identify Question-Worthy News Items

Not every article is worth a question. Prioritise:

| Good for MCQs | Avoid |
|---|---|
| Supreme Court / High Court judgments | Daily casualty counts or death tolls |
| New laws, bills, amendments | Transient political drama (suspensions, walkouts) |
| International treaties, summits, organisations | Exact monetary figures (sale prices, stock indices) |
| Government schemes, policies, regulatory bodies | Bypolls, candidate lists, party reshuffles |
| Geographic/strategic concepts (straits, ports, borders) | Crime reports, FIRs, arrests |
| Scientific discoveries, space missions | Celebrity news, entertainment |
| Reports by notable institutions (NITI Aayog, RBI, UN bodies) | Opinion columns (unless they reference a testable fact) |
| Constitutional provisions triggered by a news event | Weather, daily market movement |
| Sports governing bodies, historic milestones | Match scores, player auction prices |

**Rule of thumb:** If the question would become meaningless or trivially dated in 6 months, skip it.

---

## Step 3: Use the News as a Springboard, Not the Answer

This is the core quality principle. The newspaper headline provides the *context*, but the question should test a **durable concept, institution, or fact** connected to it.

### Bad Example (ephemeral)
> "How many Opposition MPs were suspended from Lok Sabha on March 18, 2026?"
> — This is trivia. No one will remember or care about this number.

### Good Example (durable, built from the same headline)
> "Under which Article of the Constitution can the Speaker suspend a member from the House?"
> — This tests a constitutional concept anchored to a real event.

### The Pattern
1. Read the headline / article.
2. Ask: *What institution, law, geography, or concept does this involve?*
3. Frame the question around **that** concept, using the news as a brief setup line if needed.

---

## Step 4: Structure Each MCQ Properly

### Format
```
Q. [Context from news, 1 line] + [Actual question testing a concept]

(a) Plausible wrong answer
(b) Plausible wrong answer
(c) Correct answer
(d) Plausible wrong answer

Answer: (c)
```

### Rules for Options
- All four options must be **plausible** — no joke answers.
- Options should be of similar length and grammatical form.
- Avoid "All of the above" / "None of the above" — they are lazy constructs.
- The correct answer's position should vary across questions (don't always put it at (c)).
- Distractors should be from the **same category** (e.g., if the answer is a Ministry, all options should be Ministries).

---

## Step 5: Cover All Sections of the Paper

Aim for a balanced spread across domains:

| Domain | Source Sections | Target: ~count per paper |
|---|---|---|
| Polity & Governance | Nation, Parliament, Editorial | 4–5 |
| Economy | Economy, Explained | 3–4 |
| International Relations | World, Front Page | 3–4 |
| Science & Tech | Explained, Big Picture, Tech features | 2–3 |
| Geography & Environment | Any section with maps, straits, climate | 2–3 |
| Society & Social Justice | Nation, Explained (laws, bills, SC rulings) | 2–3 |
| Sports & Culture | Sports, Editorial, features | 1–2 |

---

## Step 6: Quality Checklist Before Finalising

Run every question through this checklist:

- [ ] **Durability** — Will this question make sense 1 year from now?
- [ ] **Conceptual depth** — Does it test understanding, not just recall of a number/name from today's headline?
- [ ] **Single correct answer** — Is exactly one option unambiguously correct?
- [ ] **No morbid trivia** — No questions about death tolls, disaster counts, or violence statistics.
- [ ] **Plausible distractors** — Would a well-prepared student need to think before eliminating wrong options?
- [ ] **Factual accuracy** — Is the answer verifiable from an authoritative source, not just the newspaper's phrasing?
- [ ] **No opinion-based answers** — The correct answer should be an objective fact, not an editorial stance.

---

## Step 7: Prompt Template for Claude

When asking Claude to generate questions from a newspaper PDF, use a prompt like:

```
Read this newspaper PDF and generate 20 exam-quality MCQs (single correct answer)
suitable for UPSC/SSC/State PCS preparation.

Rules:
1. Use news items as context, but test durable concepts — institutions, laws,
   geography, constitutional provisions, governing bodies.
2. Every question must remain valid and meaningful if asked 1 year later.
3. No questions on death tolls, exact monetary figures, match scores,
   or ephemeral political events.
4. All 4 options must be plausible and from the same category.
5. Cover a balanced spread: polity, economy, international relations,
   science & tech, geography, society, sports/culture.
6. Vary the position of the correct answer across questions.
7. Include the answer with a brief 1-line explanation if needed.
```

---

## Example Transformation

### News Headline
> "Centre looks to empower more ministries to block social media content"

### Bad Question
> "Which ministries will the Centre empower to block social media content?"
> — Speculative, ephemeral, answer may change.

### Good Question
> "Under the Information Technology Act, which body currently holds the primary
> authority to issue directions for blocking online content?"
>
> (a) CERT-In
> (b) Ministry of Electronics and Information Technology (MeitY)
> (c) Ministry of Home Affairs
> (d) Ministry of Information and Broadcasting
>
> **Answer: (b)** — Section 69A of the IT Act empowers the Central Government
> (through MeitY) to direct blocking of content.

---

## Summary

The key insight is: **the newspaper gives you the topic, not the question.** A good MCQ generator treats each news item as a door into a concept — a constitutional article, an international body, a geographic feature, a regulatory framework — and tests *that*. The news is the hook; the knowledge is the payload.
