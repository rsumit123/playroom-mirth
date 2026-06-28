#!/usr/bin/env python3
"""Remove formulaic questions from the generated geography expansion."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "backend" / "app" / "data" / "gk_questions.json"
GEN_FILES = sorted((ROOT / "backend" / "app" / "data").glob("geography_india_expansion*_generated_*.json"))


def should_prune(q: dict) -> bool:
    text = q["question"]
    if q.get("source_note") == "states_capitals":
        return True
    if "belongs most clearly" in text:
        return True
    if text.startswith("A geography question on "):
        return True
    return False


def main() -> None:
    pruned_ids: set[str] = set()
    for path in GEN_FILES:
        data = json.loads(path.read_text())
        kept = []
        for q in data:
            if should_prune(q):
                pruned_ids.add(q["id"])
            else:
                kept.append(q)
        path.write_text(json.dumps(kept, indent=2) + "\n")

    bank = json.loads(BANK_PATH.read_text())
    bank = [q for q in bank if q.get("id") not in pruned_ids]
    BANK_PATH.write_text(json.dumps(bank, indent=2) + "\n")
    print(f"pruned {len(pruned_ids)}")


if __name__ == "__main__":
    main()
