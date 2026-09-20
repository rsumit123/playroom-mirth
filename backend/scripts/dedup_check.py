#!/usr/bin/env python3
"""Near-duplicate detection for trivia questions.

Usage:
  dedup_check.py --audit                      # find existing dupes in the bank
  dedup_check.py --candidates new.json        # check a generated batch vs the bank
"""
import argparse, json, math, re, sys
from collections import defaultdict
from pathlib import Path

BANK = Path(__file__).resolve().parent.parent / "app" / "data" / "gk_questions.json"

STOP = {
    "the","a","an","of","in","on","at","to","for","is","are","was","were","which","what",
    "who","whom","whose","by","with","as","and","or","from","that","this","these","those",
    "it","its","be","been","has","have","had","does","do","did","most","associated",
    "following","india","indian","known","called",
}


def norm(text: str) -> set:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in STOP and len(w) > 2}


def build_idf(all_items):
    """Document frequency over the whole bank -> IDF weights.

    Without this, templated stems dominate. ~195 existing current_affairs
    questions share 6 boilerplate stems ("Which institution or body is most
    directly associated with ...") and plain Jaccard scores every pair of them
    at 0.5+ even though they ask about completely different subjects.
    IDF drives those shared tokens to ~0 so only distinctive entities count.
    """
    df = defaultdict(int)
    for q in all_items:
        for t in q["_tok"]:
            df[t] += 1
    n = len(all_items)
    return {t: math.log(n / c) for t, c in df.items()}


def jaccard(a: set, b: set, idf=None) -> float:
    if not a or not b:
        return 0.0
    if idf is None:
        return len(a & b) / len(a | b)
    w = lambda ts: sum(idf.get(t, math.log(1000)) for t in ts)
    union = w(a | b)
    return w(a & b) / union if union else 0.0


def load(p):
    with open(p) as f:
        return json.load(f)


def index_by_token(items):
    """Inverted index so we compare only questions sharing a rare-ish token."""
    idx = defaultdict(list)
    for i, q in enumerate(items):
        for t in q["_tok"]:
            idx[t].append(i)
    return idx


def prep(qs):
    for q in qs:
        q["_tok"] = norm(q["question"])
    return qs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--candidates")
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--category", default=None)
    args = ap.parse_args()

    bank = prep(load(BANK))
    scope = [q for q in bank if not args.category or q.get("category") == args.category]

    idf = build_idf(bank)

    if args.audit:
        idx = index_by_token(scope)
        seen, hits = set(), 0
        exact = defaultdict(list)
        for q in scope:
            exact[q["question"].strip().lower()].append(q["id"])
        for text, ids in exact.items():
            if len(ids) > 1:
                print(f"EXACT DUPLICATE ({len(ids)}): {ids} :: {text[:90]}")
                hits += 1
        for i, q in enumerate(scope):
            cand = {j for t in q["_tok"] for j in idx[t] if j > i}
            for j in cand:
                pair = (i, j)
                if pair in seen:
                    continue
                seen.add(pair)
                s = jaccard(q["_tok"], scope[j]["_tok"], idf)
                if s >= args.threshold:
                    print(f"NEAR {s:.2f} {q['id']} / {scope[j]['id']}")
                    print(f"   A: {q['question'][:95]}")
                    print(f"   B: {scope[j]['question'][:95]}")
                    hits += 1
        print(f"\n{len(scope)} questions scanned, {hits} duplicate/near-duplicate pairs")
        return

    if not args.candidates:
        ap.error("need --audit or --candidates")

    new = prep(load(args.candidates))
    idx = index_by_token(bank)
    flagged = 0
    for q in new:
        cand = {j for t in q["_tok"] for j in idx[t]}
        best, best_s = None, 0.0
        for j in cand:
            s = jaccard(q["_tok"], bank[j]["_tok"], idf)
            if s > best_s:
                best, best_s = bank[j], s
        if best_s >= args.threshold:
            flagged += 1
            print(f"DUPE {best_s:.2f} {q['id']} ~ {best['id']} ({best['category']})")
            print(f"   NEW: {q['question'][:95]}")
            print(f"   OLD: {best['question'][:95]}")
    print(f"\n{len(new)} candidates, {flagged} flagged at threshold {args.threshold}")
    sys.exit(1 if flagged else 0)


if __name__ == "__main__":
    main()
