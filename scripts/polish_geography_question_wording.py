#!/usr/bin/env python3
"""Vary generated geography question wording without changing answers."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "backend" / "app" / "data" / "gk_questions.json"
GEN_FILES = sorted((ROOT / "backend" / "app" / "data").glob("geography_india_expansion*_generated_*.json"))


def _extract(text: str) -> str | None:
    patterns = [
        r"^Which state has (.+) as its capital\?$",
        r"^Which state has (.+) as its legislative capital\?$",
        r"^(.+) is in which state\?$",
        r"^(.+) is located in which state\?$",
        r"^(.+) is mainly in which state\?$",
        r"^(.+) is mainly associated with which state\?$",
        r"^(.+) is strongly associated with which state\?$",
        r"^(.+) belongs most clearly to which Indian state\?$",
        r"^The (.+) is in which state\?$",
        r"^The (.+) is mainly associated with which state\?$",
        r"^The (.+) is strongly associated with which state\?$",
        r"^The (.+) is a geographic feature of which state\?$",
        r"^Which state is best associated with the (.+)\?$",
        r"^Which state should you associate with the (.+)\?$",
        r"^Which state is crossed by the Tropic of Cancer and has (.+)\?$",
    ]
    for pattern in patterns:
        m = re.match(pattern, text)
        if m:
            return m.group(1).strip()
    return None


def polish(text: str, idx: int, correct: str, source_note: str) -> str:
    feature = _extract(text)
    if feature and "capital" in source_note:
        variants = [
            f"{feature} is the capital of which state?",
            f"On an India map, {feature} should point to which state capital?",
            f"Which state uses {feature} as its capital?",
            f"Match the capital {feature} with the correct state.",
        ]
        return variants[idx % len(variants)]

    if feature and source_note in {
        "protected_areas", "state_features", "state_feature_literacy",
        "regional_geography", "geomorphology", "biosphere_reserves",
        "waterfalls", "location_lines",
    }:
        variants = [
            f"Map clue: {feature}. Pick the state.",
            f"{feature} points to which Indian state?",
            f"Which state matches this geography clue: {feature}?",
            f"Where in India would you place {feature}?",
            f"Identify the state linked with {feature}.",
            f"{feature} belongs most clearly to which state?",
            f"A geography question on {feature} should lead to which state?",
        ]
        return variants[idx % len(variants)]

    if feature and source_note in {"ports", "coasts", "islands", "wetlands", "physical_regions"}:
        variants = [
            f"Which state or region is linked with {feature}?",
            f"Map clue: {feature}. Choose the best match.",
            f"{feature} is best placed with which option?",
            f"Identify the geography match for {feature}.",
        ]
        return variants[idx % len(variants)]

    if text.startswith("Which country "):
        body = text.removeprefix("Which country ").removesuffix("?")
        variants = [
            f"Country clue: {body}. Pick the country.",
            f"Which neighbour fits this clue: {body}?",
            f"Identify the country for this geography clue: {body}.",
        ]
        return variants[idx % len(variants)]

    if text.startswith("Which river ") or " which river" in text.lower():
        return text.replace("Which river", "Name the river", 1)

    return text


def main() -> None:
    generated_by_id: dict[str, dict] = {}
    changed = 0
    for path in GEN_FILES:
        data = json.loads(path.read_text())
        for idx, q in enumerate(data):
            new_text = polish(q["question"], idx, q["options"][q["correct_index"]], q.get("source_note", ""))
            if new_text != q["question"]:
                q["question"] = new_text
                changed += 1
            generated_by_id[q["id"]] = q
        path.write_text(json.dumps(data, indent=2) + "\n")

    bank = json.loads(BANK_PATH.read_text())
    for q in bank:
        replacement = generated_by_id.get(q.get("id"))
        if replacement:
            q["question"] = replacement["question"]
    BANK_PATH.write_text(json.dumps(bank, indent=2) + "\n")
    print(f"polished {changed} question texts")


if __name__ == "__main__":
    main()
