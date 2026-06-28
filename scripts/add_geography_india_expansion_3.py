#!/usr/bin/env python3
"""Generate and merge a third India-focused geography trivia batch."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from add_geography_india_expansion import STATES, assign_ids, question, validate


ROOT = Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "backend" / "app" / "data" / "gk_questions.json"
OUT_PATH = ROOT / "backend" / "app" / "data" / "geography_india_expansion_3_generated_81.json"


FEATURE_POOL = [
    "Brahmaputra Valley", "Eastern Himalaya", "Gangetic plain", "Bastar Plateau",
    "Mandovi-Zuari estuary", "Rann of Kutch", "Aravalli foothills", "Dhauladhar range",
    "Chota Nagpur Plateau", "Western Ghats coffee belt", "Malabar backwaters",
    "Malwa Plateau", "Konkan coast", "Loktak Lake basin", "Shillong Plateau",
    "Lushai Hills", "Naga Hills", "Mahanadi delta", "Sutlej-Beas plain",
    "Thar Desert", "Teesta valley", "Kaveri delta", "Telangana Plateau",
    "Tripura Hills", "Ganga-Yamuna Doab", "Garhwal Himalaya", "Sundarbans delta",
    "Krishna-Godavari delta",
]

STATE_FEATURES = [
    ("Assam", "Brahmaputra Valley", "Kaziranga landscape", "tea gardens"),
    ("Arunachal Pradesh", "Eastern Himalaya", "Siang valley", "Namdapha landscape"),
    ("Bihar", "Gangetic plain", "Kosi belt", "alluvial agriculture"),
    ("Chhattisgarh", "Bastar Plateau", "Indravati basin", "rice-growing plains"),
    ("Goa", "Mandovi-Zuari estuary", "Western Ghats edge", "coastal tourism belt"),
    ("Gujarat", "Rann of Kutch", "Gir landscape", "Groundnut-cotton belt"),
    ("Haryana", "Aravalli foothills", "Ghaggar plain", "wheat-rice belt"),
    ("Himachal Pradesh", "Dhauladhar range", "Kullu valley", "apple-growing hills"),
    ("Jharkhand", "Chota Nagpur Plateau", "Damodar valley", "coal-mineral belt"),
    ("Karnataka", "Western Ghats coffee belt", "Malnad region", "Deccan plateau"),
    ("Kerala", "Malabar backwaters", "Periyar basin", "spice-growing hills"),
    ("Madhya Pradesh", "Malwa Plateau", "Narmada valley", "central highlands"),
    ("Maharashtra", "Konkan coast", "Sahyadri escarpment", "Black-soil cotton belt"),
    ("Manipur", "Loktak Lake basin", "Imphal valley", "floating phumdi habitat"),
    ("Meghalaya", "Shillong Plateau", "Mawsynram-Cherrapunji belt", "limestone caves"),
    ("Mizoram", "Lushai Hills", "Dampa landscape", "bamboo-covered hills"),
    ("Nagaland", "Naga Hills", "Dzukou valley region", "hill agriculture"),
    ("Odisha", "Mahanadi delta", "Chilika lagoon", "Similipal landscape"),
    ("Punjab", "Sutlej-Beas plain", "alluvial canal belt", "wheat granary"),
    ("Rajasthan", "Thar Desert", "Aravalli range", "Arid inland drainage"),
    ("Sikkim", "Teesta valley", "Khangchendzonga landscape", "Eastern Himalaya"),
    ("Tamil Nadu", "Kaveri delta", "Nilgiri slopes", "Coromandel coast"),
    ("Telangana", "Telangana Plateau", "Godavari-Krishna uplands", "Deccan interior"),
    ("Tripura", "Tripura Hills", "Gomati basin", "Bangladesh-facing valleys"),
    ("Uttar Pradesh", "Ganga-Yamuna Doab", "Terai belt", "alluvial plains"),
    ("Uttarakhand", "Garhwal Himalaya", "Kumaon Himalaya", "Gangotri-Yamunotri source region"),
    ("West Bengal", "Sundarbans delta", "Darjeeling Himalaya", "Hooghly plain"),
    ("Andhra Pradesh", "Krishna-Godavari delta", "Eastern Ghats slopes", "long Bay of Bengal coast"),
]


COUNTRY_POOL = ["Pakistan", "China", "Nepal", "Bhutan", "Bangladesh", "Myanmar", "Sri Lanka", "Maldives"]

BORDER_FACTS = [
    (1, "Which state borders Pakistan and has Kutch?", "Gujarat", STATES, "borders"),
    (1, "Which state borders Pakistan and has the Thar Desert?", "Rajasthan", STATES, "borders"),
    (1, "Which state borders Pakistan and has Amritsar?", "Punjab", STATES, "borders"),
    (1, "Which state borders Nepal and has the Kumaon region?", "Uttarakhand", STATES, "borders"),
    (1, "Which state borders Nepal and has the Terai belt?", "Uttar Pradesh", STATES, "borders"),
    (1, "Which state borders Nepal and has the Kosi belt?", "Bihar", STATES, "borders"),
    (1, "Which state borders Bhutan and has the Dooars region?", "West Bengal", STATES, "borders"),
    (1, "Which state borders Bhutan and has the Manas landscape?", "Assam", STATES, "borders"),
    (1, "Which state borders Bangladesh and contains the Sundarbans?", "West Bengal", STATES, "borders"),
    (1, "Which state borders Bangladesh and has the Khasi Hills?", "Meghalaya", STATES, "borders"),
    (1, "Which state borders Myanmar and has the Moreh area?", "Manipur", STATES, "borders"),
    (1, "Which state borders Myanmar and has the Lushai Hills?", "Mizoram", STATES, "borders"),
    (2, "Which country is across the Radcliffe Line from Punjab and Rajasthan?", "Pakistan", COUNTRY_POOL, "borders"),
    (2, "Which country lies north of Sikkim across the Himalaya?", "China", COUNTRY_POOL, "borders"),
    (2, "Which country lies east of Nagaland and Manipur?", "Myanmar", COUNTRY_POOL, "borders"),
    (2, "Which country lies south of the Palk Strait?", "Sri Lanka", COUNTRY_POOL, "maritime_borders"),
]


def build_facts() -> list[tuple[int, str, str, list[str], str]]:
    facts: list[tuple[int, str, str, list[str], str]] = []
    for idx, (state, feature, feature2, feature3) in enumerate(STATE_FEATURES):
        facts.append((1, f"Which state is best associated with the {feature}?", state, STATES, "state_feature_literacy"))
        facts.append((2, f"The {feature2} is a geographic feature of which state?", state, STATES, "state_feature_literacy"))
        facts.append((3, f"Which state should you associate with the {feature3}?", state, STATES, "state_feature_literacy"))
        if idx % 2 == 0:
            facts.append((2, f"{feature} belongs most clearly to which Indian state?", state, STATES, "state_feature_literacy"))
        else:
            facts.append((3, f"{feature2} belongs most clearly to which Indian state?", state, STATES, "state_feature_literacy"))
    facts.extend(BORDER_FACTS)
    return facts


def main() -> None:
    existing = json.loads(BANK_PATH.read_text())
    generated = [
        question(difficulty, text, correct, pool, note, i + difficulty * 3000)
        for i, (difficulty, text, correct, pool, note) in enumerate(build_facts(), 1)
    ]
    generated = assign_ids(generated, existing)
    validate(generated, existing)
    OUT_PATH.write_text(json.dumps(generated, indent=2) + "\n")
    merged = existing + generated
    BANK_PATH.write_text(json.dumps(merged, indent=2) + "\n")
    print(f"generated {len(generated)}")
    print(Counter(q["difficulty"] for q in generated))
    print(f"total {len(merged)}")
    print(f"geography {sum(q.get('category') == 'geography' for q in merged)}")


if __name__ == "__main__":
    main()
