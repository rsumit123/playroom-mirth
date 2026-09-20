#!/usr/bin/env python3
"""Assign IDs and shuffle answer positions for a drafted question batch.

Drafts are written with the correct answer first (easier to author and review).
Left that way the bank becomes trivially guessable, so every question gets its
options permuted deterministically before it can be merged.

Usage: assemble_batch.py out.json draft1.json draft2.json ...
"""
import json, random, sys
from pathlib import Path

BANK = Path(__file__).resolve().parent.parent / "app" / "data" / "gk_questions.json"
LABEL = {1: "easy", 2: "medium", 3: "hard"}


def next_seq(bank):
    nxt = {}
    for diff, lab in LABEL.items():
        seqs = [int(q["id"].rsplit("_", 1)[1]) for q in bank
                if q.get("category") == "current_affairs" and q["difficulty"] == diff
                and q["id"].startswith(f"ca_{lab}_")]
        nxt[diff] = max(seqs, default=0) + 1
    return nxt


def main():
    out_path, drafts = sys.argv[1], sys.argv[2:]
    bank = json.loads(BANK.read_text())
    seq = next_seq(bank)

    items = []
    for d in drafts:
        items.extend(json.loads(Path(d).read_text()))

    rng = random.Random(20260913)
    built, seen = [], set()
    for q in sorted(items, key=lambda x: x["difficulty"]):
        text = " ".join(q["question"].split())
        if text.lower() in seen:
            print(f"skip in-batch duplicate: {text[:70]}")
            continue
        seen.add(text.lower())

        opts = list(q["options"])
        correct = opts[q["correct_index"]]
        rng.shuffle(opts)
        diff = q["difficulty"]
        built.append({
            "id": f"ca_{LABEL[diff]}_{seq[diff]:03d}",
            "category": "current_affairs",
            "difficulty": diff,
            "question": text,
            "options": opts,
            "correct_index": opts.index(correct),
        })
        seq[diff] += 1

    Path(out_path).write_text(json.dumps(built, indent=1))
    import collections
    print(f"{len(built)} questions -> {out_path}")
    print("difficulty:", collections.Counter(q["difficulty"] for q in built))
    print("answer position:", collections.Counter(q["correct_index"] for q in built))


if __name__ == "__main__":
    main()
