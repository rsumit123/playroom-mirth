# Indian Law Trivia Audit - 2026-06-16

Category: indian_law
Question file: backend/app/data/indian_law_generated_500.json
Merged bank: backend/app/data/gk_questions.json

## Scope

- Replaced the original repetitive 500-question Indian Law batch.
- The old batch had only 149 distinct factual answer/source anchors and many 4x reworded variants.
- Regenerated 500 Indian Law questions with practical-first prompts and one source/answer anchor per question.
- Avoided fictional long scenarios; prompts are short and written for the playroom UI.
- Checked the anchors against official or primary public sources where available.
- Rejected temporary event-style questions; retained evergreen civic/legal literacy facts.

## Sources Checked

- Constitution of India, Government of India, Ministry of Law and Justice, Legislative Department, as on 1 May 2024.
- Ministry of Home Affairs New Criminal Laws page listing BNS, BSA and BNSS.
- India Code: The Bharatiya Nyaya Sanhita, 2023.
- India Code: The Bharatiya Sakshya Adhiniyam, 2023.
- India Code: The Protection of Children from Sexual Offences Act, 2012.
- India Code: The Sexual Harassment of Women at Workplace (Prevention, Prohibition and Redressal) Act, 2013.
- National Legal Services Authority website.
- National Consumer Helpline website.
- Right to Information gateway, Department of Personnel and Training.
- National Cyber Crime Reporting Portal, Ministry of Home Affairs.

## Audit Result

- All 500 question records parse correctly and retain valid answer indexes.
- All 500 questions remain in category `indian_law`.
- Difficulty split remains 220 easy, 200 medium, 80 hard.
- Content mix: practical legal literacy 78, legal glossary 150, landmark judgments 40, Indian statutes 77, legal institutions 51, legal history 19, statutory provisions 71, Constitution article prompts 14.
- Article-number answers are capped at 14 in the generated set.
- Maximum question length is under 126 characters after regeneration.
- Duplicate question text count is 0.
- Unique source/answer anchors: 500.
- Repeated source/answer anchor groups with 3 or more variants: 0.
- Unique normalized correct answers: 500.
- Repeated normalized correct answers: 0.
- Reviewed anchors cover constitutional articles, arrest safeguards, NALSA/legal aid, consumer protection, cybercrime reporting, POCSO, POSH, domestic violence reliefs, RTI, BNS/BSA/BNSS basics, writs, bail/procedure concepts, legal institutions, property basics, family law basics, contract concepts, and evidence concepts.

## Corrections Made During Audit

- The repetitive generated batch was replaced instead of trying to patch individual duplicates.
- Four old questions that used outdated IPC 498A framing were removed with the old batch and replaced with current BNS Section 85/86 coverage:

- BNS Section 85 - cruelty by husband or relatives of husband.
- BNS Section 86 - cruelty defined.

The regenerated set was applied to both:

- backend/app/data/indian_law_generated_500.json
- backend/app/data/gk_questions.json

## Remaining Risk

The questions are legal-literacy trivia, not legal advice. They avoid case-specific instructions and jurisdiction-dependent procedural advice. A lawyer review is still the strongest final gate before production, but the content audit found no remaining factual contradiction in the generated 500-question set.
