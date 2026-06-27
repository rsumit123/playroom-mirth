#!/usr/bin/env python3
"""Add focused War & Defense platform/spec trivia questions.

This batch fills gaps around engines, artillery, missiles, armored vehicles,
naval platforms, sensors, and aircraft without replacing the existing category.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "backend/app/data/gk_questions.json"
GENERATED = ROOT / "backend/app/data/defense_platform_generated_75.json"


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
    # Easy: recognisable platform literacy.
    (1, "Which engine family powers the Dassault Rafale fighter aircraft?", "Safran/Snecma M88", ["GE F414", "Eurojet EJ200", "Saturn AL-31FP"]),
    (1, "Which engine powers India's Tejas Mk1 and Mk1A fighter aircraft?", "GE F404-IN20", ["GE F414-INS6", "Kaveri", "Safran M88"]),
    (1, "Which engine powers the Sukhoi Su-30MKI fighter aircraft?", "Saturn AL-31FP", ["Safran M88", "GE F404-IN20", "Eurojet EJ200"]),
    (1, "Which main gun calibre is used by the K9 Vajra self-propelled howitzer?", "155 mm", ["105 mm", "125 mm", "214 mm"]),
    (1, "Which main gun calibre is used by the M777 ultra-light howitzer?", "155 mm", ["120 mm", "130 mm", "214 mm"]),
    (1, "Which Indian rocket artillery system uses 214 mm rockets?", "Pinaka", ["Smerch", "Grad", "K9 Vajra"]),
    (1, "Which Russian-origin rocket artillery system in Indian service uses 300 mm rockets?", "Smerch", ["Pinaka", "Grad", "Dhanush"]),
    (1, "Which Indian Army self-propelled artillery gun is based on the South Korean K9 Thunder?", "K9 Vajra", ["Dhanush", "ATAGS", "M777"]),
    (1, "Which Indian towed artillery gun is an upgraded 155 mm version derived from the Bofors design lineage?", "Dhanush", ["K9 Vajra", "Pinaka", "Smerch"]),
    (1, "Which Indian tank has the service name Bhishma?", "T-90", ["Arjun", "T-72", "BMP-2"]),
    (1, "Which Indian main battle tank is indigenous and named after a Mahabharata warrior?", "Arjun", ["T-90 Bhishma", "T-72 Ajeya", "BMP-2 Sarath"]),
    (1, "Which infantry combat vehicle in Indian service is commonly known as Sarath?", "BMP-2", ["T-90", "Arjun", "K9 Vajra"]),
    (1, "Which Indian Navy submarine class is based on the Scorpene design?", "Kalvari class", ["Arihant class", "Shishumar class", "Sindhughosh class"]),
    (1, "Which Indian Navy aircraft carrier was commissioned in 2022 as India's first indigenous aircraft carrier?", "INS Vikrant", ["INS Vikramaditya", "INS Viraat", "INS Vishal"]),
    (1, "Which Indian Navy aircraft carrier was originally the Russian Admiral Gorshkov?", "INS Vikramaditya", ["INS Vikrant", "INS Viraat", "INS Vishal"]),
    (1, "Which aircraft is the Indian Navy's long-range maritime patrol aircraft based on the Boeing 737?", "P-8I Poseidon", ["C-17 Globemaster III", "C-130J Super Hercules", "Netra AEW&C"]),
    (1, "Which transport aircraft is India's heavy strategic airlifter made by Boeing?", "C-17 Globemaster III", ["C-130J Super Hercules", "P-8I Poseidon", "Dornier Do 228"]),
    (1, "Which transport aircraft is used by India for tactical airlift and special operations?", "C-130J Super Hercules", ["C-17 Globemaster III", "IL-78", "P-8I Poseidon"]),
    (1, "Which Indian AEW&C aircraft is commonly called Netra?", "DRDO Netra", ["P-8I Poseidon", "IL-78", "C-17 Globemaster III"]),
    (1, "Which air defence system is jointly developed by India and Israel as MRSAM?", "Barak-8", ["Akash", "Trishul", "Nag"]),
    (1, "Which missile is India's beyond-visual-range air-to-air missile developed by DRDO?", "Astra", ["Akash", "Nag", "Pralay"]),
    (1, "Which Indian missile is a helicopter-launched version from the Nag missile family?", "HELINA", ["Astra", "Akash", "Prithvi"]),
    (1, "Which Indian missile is a subsonic long-range cruise missile programme?", "Nirbhay", ["BrahMos", "Akash", "Nag"]),
    (1, "Which Indian weapon is a quasi-ballistic surface-to-surface missile?", "Pralay", ["Astra", "HELINA", "MRSAM"]),
    (1, "Which air defence missile system did India buy from Russia under the S-400 Triumf name?", "S-400", ["S-300", "Patriot PAC-3", "THAAD"]),

    # Medium: more specific platform capabilities and classifications.
    (2, "Which engine family received the 4E upgrade standard for the Rafale?", "Safran/Snecma M88", ["GE F404", "Eurojet EJ200", "Saturn AL-31FP"]),
    (2, "Which GE engine family is planned for India's Tejas Mk2 fighter?", "GE F414", ["GE F404", "Safran M88", "Kaveri"]),
    (2, "Which fighter uses thrust-vectoring AL-31FP engines in Indian service?", "Sukhoi Su-30MKI", ["Rafale", "Tejas Mk1A", "Mirage 2000"]),
    (2, "Which HAL combat helicopter is optimized for high-altitude operations?", "HAL Prachand", ["HAL Dhruv", "AH-64E Apache", "CH-47F Chinook"]),
    (2, "Which HAL helicopter family is the basis for the Rudra armed helicopter?", "Dhruv ALH", ["Cheetah", "Chetak", "Prachand"]),
    (2, "Which attack helicopter in Indian service is manufactured by Boeing?", "AH-64E Apache", ["HAL Prachand", "Mi-17V5", "Dhruv ALH"]),
    (2, "Which heavy-lift helicopter in Indian service uses tandem rotors?", "CH-47F Chinook", ["AH-64E Apache", "Mi-17V5", "HAL Prachand"]),
    (2, "Which 155 mm artillery system is light enough to be airlifted by Chinook helicopters?", "M777", ["K9 Vajra", "Smerch", "Pinaka"]),
    (2, "What does ATAGS stand for in India's 155 mm artillery programme?", "Advanced Towed Artillery Gun System", ["Automated Tactical Air Gun System", "Advanced Tank Artillery Guidance System", "Army Tactical Artillery Gun Shell"]),
    (2, "Which Indian rocket artillery variant is associated with about 75 km guided rockets?", "Guided Pinaka", ["Pinaka Mk-I", "BM-21 Grad", "Dhanush"]),
    (2, "Which larger Russian-origin rocket system complements Pinaka in Indian Army rocket artillery?", "Smerch", ["Dhanush", "ATAGS", "M777"]),
    (2, "Which Indian artillery rocket system first proved itself in the Kargil War?", "Pinaka", ["Smerch", "ATAGS", "Dhanush"]),
    (2, "Which missile forms the naval and land-based supersonic cruise missile family jointly made by India and Russia?", "BrahMos", ["Nirbhay", "Pralay", "Astra"]),
    (2, "Which IAF fighter is a twin-engine heavy multirole aircraft with canards and thrust vectoring?", "Sukhoi Su-30MKI", ["Tejas Mk1A", "Rafale", "MiG-29K"]),
    (2, "Which Indian missile is a medium-range surface-to-air weapon system developed by DRDO?", "Akash", ["Astra", "Nag", "BrahMos"]),
    (2, "Which missile system is also known as the New Generation Anti-Radiation Missile?", "Rudram-1", ["Astra Mk1", "HELINA", "Pralay"]),
    (2, "Which missile is India's anti-tank guided missile named after a serpent?", "Nag", ["Astra", "Akash", "Prithvi"]),
    (2, "Which Indian submarine-launched ballistic missile is also called Sagarika?", "K-15", ["K-4", "Agni-V", "Prithvi-II"]),
    (2, "Which Indian submarine-launched ballistic missile is associated with a roughly 3,500 km class range?", "K-4", ["K-15", "Pralay", "Astra"]),
    (2, "Which Indian nuclear submarine class carries ballistic missiles?", "Arihant class", ["Kalvari class", "Shishumar class", "Sindhughosh class"]),
    (2, "Which Indian destroyer class includes INS Visakhapatnam?", "Visakhapatnam class", ["Kolkata class", "Shivalik class", "Talwar class"]),
    (2, "Which Indian destroyer class includes INS Kolkata?", "Kolkata class", ["Visakhapatnam class", "Nilgiri class", "Kamorta class"]),
    (2, "Which Indian frigate class is built under Project 17A?", "Nilgiri class", ["Shivalik class", "Talwar class", "Kolkata class"]),
    (2, "Which Indian anti-submarine warfare corvette class includes INS Kamorta?", "Kamorta class", ["Kora class", "Khukri class", "Nilgiri class"]),
    (2, "Which Indian Navy fighter operates from aircraft carriers and has folding wings?", "MiG-29K", ["Su-30MKI", "Mirage 2000", "Jaguar"]),
    (2, "Which airborne refuelling aircraft type has India used based on the Ilyushin Il-78?", "IL-78MKI", ["C-17", "P-8I", "C-130J"]),
    (2, "Which radar type is central to modern fighter radars such as Uttam AESA?", "Active electronically scanned array", ["Pulse-Doppler only", "Mechanical optical sight", "Infrared searchlight"]),
    (2, "Which indigenous AESA radar is associated with Tejas Mk1A?", "Uttam AESA", ["Bars radar", "Zhuk-ME", "Sea Giraffe"]),
    (2, "Which Russian radar family is associated with India's Su-30MKI?", "N011M Bars", ["Uttam AESA", "EL/M-2052", "RBE2"]),
    (2, "Which French radar family is associated with Rafale F3R/F4 aircraft?", "RBE2 AESA", ["N011M Bars", "Uttam AESA", "Zhuk-ME"]),

    # Hard: exact specs, programme labels, and platform distinctions.
    (3, "What calibre is the Pinaka multiple rocket launcher?", "214 mm", ["122 mm", "155 mm", "300 mm"]),
    (3, "What calibre is the BM-30 Smerch rocket system?", "300 mm", ["214 mm", "122 mm", "155 mm"]),
    (3, "What calibre is the BM-21 Grad rocket system?", "122 mm", ["214 mm", "300 mm", "155 mm"]),
    (3, "What is the barrel length class of the K9 Vajra howitzer?", "52 calibre", ["39 calibre", "45 calibre", "23 calibre"]),
    (3, "What is the barrel length class of the M777 howitzer?", "39 calibre", ["45 calibre", "52 calibre", "23 calibre"]),
    (3, "What is the barrel length class of the Dhanush 155 mm gun?", "45 calibre", ["39 calibre", "52 calibre", "23 calibre"]),
    (3, "Which main gun calibre is associated with the T-90 Bhishma tank?", "125 mm", ["120 mm", "105 mm", "155 mm"]),
    (3, "Which main gun calibre is associated with the Arjun main battle tank?", "120 mm", ["125 mm", "105 mm", "155 mm"]),
    (3, "Which engine powers the M1 Abrams main battle tank?", "Gas turbine engine", ["Diesel V12 engine", "Turboprop engine", "Ramjet engine"]),
    (3, "Which artillery platform is a 155 mm tracked self-propelled howitzer in Indian service?", "K9 Vajra", ["M777", "ATAGS", "Dhanush"]),
    (3, "Which Pralay description is most accurate?", "Quasi-ballistic surface-to-surface missile", ["Subsonic cruise missile", "Anti-radiation missile", "Shipborne torpedo"]),
    (3, "Which Rudram-1 description is most accurate?", "Anti-radiation missile", ["Submarine-launched ballistic missile", "Anti-tank guided missile", "Medium-range SAM"]),
    (3, "Which Astra Mk-1 description is most accurate?", "Beyond-visual-range air-to-air missile", ["Surface-to-surface ballistic missile", "Anti-ship cruise missile", "Man-portable air defence missile"]),
    (3, "Which Kalvari-class submarine propulsion type is conventional diesel-electric?", "Diesel-electric attack submarine", ["Nuclear ballistic missile submarine", "Nuclear attack submarine", "Aircraft carrier"]),
    (3, "Which Arihant-class submarine role is correct?", "Nuclear ballistic missile submarine", ["Diesel-electric attack submarine", "Mine countermeasure vessel", "Fleet tanker"]),
    (3, "Which aircraft is India's carrier-borne MiG-29 variant?", "MiG-29K", ["MiG-29UPG", "MiG-29SMT", "MiG-35"]),
    (3, "Which fighter did India use for the 2019 Balakot air strike?", "Mirage 2000", ["Rafale", "Tejas", "MiG-29K"]),
    (3, "Which Indian Navy ship class is named after Project 15B?", "Visakhapatnam class destroyer", ["Nilgiri class frigate", "Kamorta class corvette", "Kalvari class submarine"]),
    (3, "Project 17A corresponds to which Indian Navy warship type?", "Nilgiri class frigate", ["Visakhapatnam class destroyer", "Arihant class submarine", "Vikrant class carrier"]),
    (3, "The Indian service name Vajra refers to which Mirage 2000 platform type?", "Fighter aircraft", ["Transport aircraft", "Attack helicopter", "Maritime patrol aircraft"]),
]


def build_questions() -> list[dict]:
    starts = {1: 179, 2: 187, 3: 140}
    counters = Counter()
    labels = {1: "easy", 2: "medium", 3: "hard"}
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
    if len(questions) != len(FACTS):
        raise ValueError(f"Expected {len(FACTS)} questions, got {len(questions)}")
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


def fix_existing(bank: list[dict]) -> int:
    fixes = 0
    for q in bank:
        if q.get("id") == "def_easy_005":
            q["question"] = "From which country did India procure Rafale fighter jets?"
            fixes += 1
    return fixes


def main() -> None:
    bank = json.loads(BANK.read_text())
    questions = build_questions()
    validate_new(questions, bank)
    fixes = fix_existing(bank)
    bank.extend(questions)
    GENERATED.write_text(json.dumps(questions, indent=2) + "\n")
    BANK.write_text(json.dumps(bank, indent=2) + "\n")
    by_diff = Counter(q["difficulty"] for q in questions)
    print(f"Wrote {len(questions)} new defense platform questions")
    print(f"Fixed existing defense questions: {fixes}")
    print(f"Breakdown: {dict(sorted(by_diff.items()))}")
    print(f"Merged bank total: {len(bank)}")


if __name__ == "__main__":
    main()
