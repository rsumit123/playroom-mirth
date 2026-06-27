#!/usr/bin/env python3
"""Add Indian naval platform trivia with same-domain distractors."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "backend/app/data/gk_questions.json"
GENERATED = ROOT / "backend/app/data/defense_naval_platform_generated_75.json"


def place_options(answer: str, distractors: list[str], salt: int) -> tuple[list[str], int]:
    if len(distractors) != 3:
        raise ValueError(f"Need exactly 3 distractors for {answer}")
    options = distractors[:]
    insert_at = salt % 4
    options.insert(insert_at, answer)
    if len(options) != 4 or len(set(options)) != 4:
        raise ValueError(f"Bad options for {answer}: {options}")
    return options, insert_at


FACTS = [
    # Easy: high-value recognition, with same-domain distractors.
    (1, "Which Indian Navy destroyer class is built under Project 15B?", "Visakhapatnam class", ["Kolkata class", "Delhi class", "Rajput class"]),
    (1, "Which Indian Navy destroyer class is built under Project 15A?", "Kolkata class", ["Visakhapatnam class", "Delhi class", "Rajput class"]),
    (1, "Which Indian Navy frigate class is built under Project 17A?", "Nilgiri class", ["Shivalik class", "Talwar class", "Brahmaputra class"]),
    (1, "Which Indian Navy frigate class is built under Project 17?", "Shivalik class", ["Nilgiri class", "Talwar class", "Godavari class"]),
    (1, "Which Indian Navy class is best known as an anti-submarine warfare corvette?", "Kamorta class", ["Kora class", "Khukri class", "Abhay class"]),
    (1, "Which Indian Navy aircraft is used for long-range maritime patrol and ASW?", "P-8I Poseidon", ["MiG-29K", "Chetak", "Dornier Do 228"]),
    (1, "Which carrier-borne fighter operates from Indian aircraft carriers?", "MiG-29K", ["Su-30MKI", "Mirage 2000", "Jaguar"]),
    (1, "Which helicopter type is India's new multi-role naval helicopter?", "MH-60R Seahawk", ["Ka-31", "Chetak", "Sea King"]),
    (1, "Which Indian naval weapon is a heavyweight torpedo?", "Varunastra", ["BrahMos", "Barak-8", "RBU-6000"]),
    (1, "Which naval weapon is a shipborne close-in weapon system?", "AK-630", ["Barak-8", "Varunastra", "RBU-6000"]),
    (1, "Which naval weapon is an anti-submarine rocket launcher?", "RBU-6000", ["AK-630", "Barak-8", "BrahMos"]),
    (1, "Which missile family gives Indian warships long-range surface-to-air defence?", "Barak-8/MRSAM", ["BrahMos", "Varunastra", "RBU-6000"]),
    (1, "Which missile gives many Indian warships supersonic anti-ship strike capability?", "BrahMos", ["Barak-8", "Varunastra", "AK-630"]),
    (1, "Which Indian Navy platform is a landing platform dock?", "INS Jalashwa", ["INS Deepak", "INS Vikrant", "INS Kamorta"]),
    (1, "Which Indian Navy class is a fleet tanker class?", "Deepak class", ["Kamorta class", "Kolkata class", "Kalvari class"]),
    (1, "Which Indian Navy ship class is used for shallow-water anti-submarine warfare?", "Arnala class", ["Kamorta class", "Kora class", "Talwar class"]),
    (1, "Which class does INS Mormugao belong to?", "Visakhapatnam class", ["Kolkata class", "Delhi class", "Rajput class"]),
    (1, "Which class does INS Chennai belong to?", "Kolkata class", ["Visakhapatnam class", "Delhi class", "Rajput class"]),
    (1, "Which class includes INS Satpura and INS Sahyadri?", "Shivalik class", ["Nilgiri class", "Talwar class", "Kamorta class"]),
    (1, "Which class includes INS Trishul and INS Tabar?", "Talwar class", ["Shivalik class", "Nilgiri class", "Brahmaputra class"]),
    (1, "Which class does INS Kavaratti belong to?", "Kamorta class", ["Kora class", "Khukri class", "Abhay class"]),
    (1, "Which class does INS Kirch belong to?", "Kora class", ["Kamorta class", "Khukri class", "Veer class"]),
    (1, "Which shipyard builds many major Indian destroyers and frigates in Mumbai?", "Mazagon Dock Shipbuilders", ["GRSE", "Cochin Shipyard", "Goa Shipyard"]),
    (1, "Which shipyard is strongly associated with Kamorta-class corvettes?", "GRSE", ["Mazagon Dock Shipbuilders", "Cochin Shipyard", "Goa Shipyard"]),
    (1, "Which shipyard built India's indigenous aircraft carrier INS Vikrant?", "Cochin Shipyard", ["Mazagon Dock Shipbuilders", "GRSE", "Goa Shipyard"]),

    # Medium: programme mapping, ship roles, and weapons/sensors.
    (2, "Project 15B produced which type of Indian Navy warship?", "Guided-missile destroyer", ["Stealth frigate", "ASW corvette", "Fleet tanker"]),
    (2, "Project 17A produced which type of Indian Navy warship?", "Stealth guided-missile frigate", ["Guided-missile destroyer", "ASW corvette", "Landing platform dock"]),
    (2, "Project 28 is most closely associated with which Indian Navy platform type?", "ASW corvette", ["Stealth frigate", "Guided-missile destroyer", "Fleet tanker"]),
    (2, "Which class is the successor/improved derivative of the Kolkata-class destroyer?", "Visakhapatnam class", ["Delhi class", "Rajput class", "Talwar class"]),
    (2, "Which class is the predecessor of the Project 17A Nilgiri-class frigates?", "Shivalik class", ["Talwar class", "Godavari class", "Brahmaputra class"]),
    (2, "Which Indian Navy class includes INS Visakhapatnam, INS Mormugao, INS Imphal, and INS Surat?", "Visakhapatnam class", ["Kolkata class", "Delhi class", "Rajput class"]),
    (2, "Which Indian Navy class includes INS Kolkata, INS Kochi, and INS Chennai?", "Kolkata class", ["Visakhapatnam class", "Delhi class", "Talwar class"]),
    (2, "Which Indian Navy class includes INS Kamorta, INS Kadmatt, INS Kiltan, and INS Kavaratti?", "Kamorta class", ["Kora class", "Khukri class", "Abhay class"]),
    (2, "Which Indian Navy class includes INS Shivalik, INS Satpura, and INS Sahyadri?", "Shivalik class", ["Nilgiri class", "Talwar class", "Brahmaputra class"]),
    (2, "Which Indian Navy class includes INS Talwar, INS Trishul, and INS Tabar?", "Talwar class", ["Shivalik class", "Nilgiri class", "Godavari class"]),
    (2, "Which shipborne weapon is mainly for close defence against incoming missiles and aircraft?", "AK-630 CIWS", ["Varunastra torpedo", "BrahMos missile", "RBU-6000 launcher"]),
    (2, "Which weapon is mainly used by warships against submarines at close range?", "RBU-6000 launcher", ["AK-630 CIWS", "Barak-8 missile", "BrahMos missile"]),
    (2, "Which weapon is mainly a ship-launched heavyweight torpedo?", "Varunastra", ["Barak-8", "BrahMos", "AK-630"]),
    (2, "Which missile is mainly used by Indian warships for area air defence?", "Barak-8/MRSAM", ["BrahMos", "Varunastra", "RBU-6000"]),
    (2, "Which missile is mainly used by Indian warships for anti-ship and land-attack strike?", "BrahMos", ["Barak-8/MRSAM", "Varunastra", "AK-630"]),
    (2, "Which radar is widely associated with Indian Navy Kolkata, Visakhapatnam, and Nilgiri-class combatants?", "EL/M-2248 MF-STAR", ["Revathi", "RAWL-02", "Aparna"]),
    (2, "Which radar is associated with Kamorta-class corvettes for air surveillance?", "Revathi", ["MF-STAR", "RBE2 AESA", "N011M Bars"]),
    (2, "Which sonar family is associated with hull-mounted sonar on Kamorta-class corvettes?", "HUMSA", ["Revathi", "MF-STAR", "Uttam AESA"]),
    (2, "Which Indian Navy aircraft is optimized for carrier operations rather than maritime patrol?", "MiG-29K", ["P-8I Poseidon", "Dornier Do 228", "IL-38SD"]),
    (2, "Which Indian Navy aircraft is optimized for long-range maritime patrol rather than carrier combat?", "P-8I Poseidon", ["MiG-29K", "Ka-31", "MH-60R Seahawk"]),
    (2, "Which helicopter is primarily a shipborne multi-role ASW helicopter?", "MH-60R Seahawk", ["MiG-29K", "P-8I Poseidon", "Dornier Do 228"]),
    (2, "Which helicopter is best known as an airborne early-warning helicopter in Indian naval service?", "Ka-31", ["MH-60R Seahawk", "Chetak", "Sea King"]),
    (2, "Which naval platform is mainly for amphibious lift and landing operations?", "INS Jalashwa", ["INS Deepak", "INS Kamorta", "INS Kolkata"]),
    (2, "Which naval platform type refuels and replenishes warships at sea?", "Fleet tanker", ["ASW corvette", "Guided-missile destroyer", "Survey vessel"]),
    (2, "Which class name fits India's ASW shallow-water craft programme?", "Arnala class", ["Kamorta class", "Talwar class", "Kolkata class"]),
    (2, "Which anti-submarine system combines a missile flight profile with torpedo delivery?", "SMART", ["Varunastra", "RBU-6000", "Barak-8"]),
    (2, "Which Indian naval missile was a ship-launched ballistic missile tested from patrol vessels?", "Dhanush", ["K-15", "Pralay", "BrahMos"]),
    (2, "Which class is a guided-missile corvette class rather than an ASW corvette class?", "Kora class", ["Kamorta class", "Arnala class", "Abhay class"]),
    (2, "Which Indian Navy frigate class was built in Russia?", "Talwar class", ["Shivalik class", "Nilgiri class", "Godavari class"]),
    (2, "Which Indian Navy frigate class was the first stealth warship class designed and built in India?", "Shivalik class", ["Talwar class", "Nilgiri class", "Brahmaputra class"]),

    # Hard: exact class distinctions, systems, and platform literacy.
    (3, "Which Project 15B ship is named after a city in Goa?", "INS Mormugao", ["INS Visakhapatnam", "INS Imphal", "INS Surat"]),
    (3, "Which Project 15B ship is named after a city in the Northeast?", "INS Imphal", ["INS Mormugao", "INS Surat", "INS Visakhapatnam"]),
    (3, "Which Project 15B ship is named after a Gujarat port city?", "INS Surat", ["INS Imphal", "INS Mormugao", "INS Visakhapatnam"]),
    (3, "Which Kolkata-class destroyer is named after Tamil Nadu's capital?", "INS Chennai", ["INS Kolkata", "INS Kochi", "INS Mysore"]),
    (3, "Which Kolkata-class destroyer is named after Kerala's port city?", "INS Kochi", ["INS Kolkata", "INS Chennai", "INS Delhi"]),
    (3, "Which Shivalik-class frigate is named after a mountain range in central India?", "INS Satpura", ["INS Shivalik", "INS Sahyadri", "INS Talwar"]),
    (3, "Which Shivalik-class frigate is named after the Western Ghats?", "INS Sahyadri", ["INS Shivalik", "INS Satpura", "INS Tabar"]),
    (3, "Among these frigate names, which one literally means sword?", "INS Talwar", ["INS Trishul", "INS Tabar", "INS Tarkash"]),
    (3, "Which Talwar-class frigate name refers to a trident?", "INS Trishul", ["INS Talwar", "INS Tabar", "INS Teg"]),
    (3, "Which Kamorta-class corvette is the lead ship of Project 28?", "INS Kamorta", ["INS Kadmatt", "INS Kiltan", "INS Kavaratti"]),
    (3, "Which Project 28 corvette was commissioned as the fourth ship of the class?", "INS Kavaratti", ["INS Kamorta", "INS Kadmatt", "INS Kiltan"]),
    (3, "Which Kora-class corvette is the lead ship of its class?", "INS Kora", ["INS Kirch", "INS Kulish", "INS Karmuk"]),
    (3, "Which naval gun calibre is common on many modern Indian surface combatants?", "76 mm", ["57 mm", "100 mm", "127 mm"]),
    (3, "Which torpedo calibre is commonly associated with heavyweight ship-launched torpedo tubes?", "533 mm", ["324 mm", "650 mm", "400 mm"]),
    (3, "Which system is the main area-air-defence missile on Kolkata and Visakhapatnam-class destroyers?", "Barak-8/MRSAM", ["AK-630", "Varunastra", "RBU-6000"]),
    (3, "Which weapon is the main supersonic strike missile on Kolkata and Visakhapatnam-class destroyers?", "BrahMos", ["Barak-8/MRSAM", "Varunastra", "AK-630"]),
    (3, "Which radar acronym expands to Multi-Function Surveillance, Track and Guidance Radar?", "MF-STAR", ["HUMSA", "RAWL", "Revathi"]),
    (3, "Which sonar name is an Indian hull-mounted sonar family used on naval ships?", "HUMSA", ["MF-STAR", "Revathi", "Kavach"]),
    (3, "Which decoy system is used by Indian warships against anti-ship missile threats?", "Kavach", ["HUMSA", "MF-STAR", "Varunastra"]),
    (3, "Which Indian Navy class is more correctly an ASW shallow-water craft than a corvette?", "Arnala class", ["Kamorta class", "Kora class", "Khukri class"]),
]


def build_questions() -> list[dict]:
    starts = {1: 204, 2: 217, 3: 160}
    labels = {1: "easy", 2: "medium", 3: "hard"}
    counters: Counter[int] = Counter()
    questions: list[dict] = []
    for salt, (difficulty, question, answer, distractors) in enumerate(FACTS):
        counters[difficulty] += 1
        seq = starts[difficulty] + counters[difficulty] - 1
        options, correct_index = place_options(answer, distractors, salt)
        questions.append({
            "id": f"def_{labels[difficulty]}_{seq:03d}",
            "category": "defense",
            "difficulty": difficulty,
            "question": question,
            "options": options,
            "correct_index": correct_index,
        })
    return questions


def validate_new(questions: list[dict], bank: list[dict]) -> None:
    existing_ids = {q["id"] for q in bank}
    existing_questions = {q["question"].strip().lower() for q in bank}
    ids = [q["id"] for q in questions]
    if len(questions) != 75:
        raise ValueError(f"Expected 75 questions, got {len(questions)}")
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate new IDs")
    for q in questions:
        if q["id"] in existing_ids:
            raise ValueError(f"ID collision: {q['id']}")
        if q["question"].strip().lower() in existing_questions:
            raise ValueError(f"Question collision: {q['question']}")
        if q["category"] != "defense":
            raise ValueError(f"Wrong category: {q['id']}")
        if q["difficulty"] not in {1, 2, 3}:
            raise ValueError(f"Bad difficulty: {q['id']}")
        if len(q["options"]) != 4 or len(set(q["options"])) != 4:
            raise ValueError(f"Bad options: {q['id']}")
        if q["correct_index"] not in {0, 1, 2, 3}:
            raise ValueError(f"Bad correct_index: {q['id']}")
        if not q["options"][q["correct_index"]].strip():
            raise ValueError(f"Blank answer: {q['id']}")


def main() -> None:
    bank = json.loads(BANK.read_text())
    questions = build_questions()
    validate_new(questions, bank)
    bank.extend(questions)
    GENERATED.write_text(json.dumps(questions, indent=2) + "\n")
    BANK.write_text(json.dumps(bank, indent=2) + "\n")
    by_diff = Counter(q["difficulty"] for q in questions)
    print(f"Wrote {len(questions)} new naval platform defense questions")
    print(f"Breakdown: {dict(sorted(by_diff.items()))}")
    print(f"Merged bank total: {len(bank)}")


if __name__ == "__main__":
    main()
