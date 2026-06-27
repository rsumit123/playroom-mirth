#!/usr/bin/env python3
"""Add defense questions for army weapons, drones, and air defence systems.

The batch intentionally uses same-domain distractors: guns against guns,
rifles against rifles, ATGMs against ATGMs, UAVs against UAVs, and SAM/air
defence systems against SAM/air defence systems.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "backend/app/data/gk_questions.json"
GENERATED = ROOT / "backend/app/data/defense_army_systems_generated_250.json"


STARTS = {1: 229, 2: 247, 3: 180}
LABELS = {1: "easy", 2: "medium", 3: "hard"}

QUESTION_OVERRIDES = {
    "def_easy_237": "Which Swedish 155 mm howitzer became famous in Indian service during the Kargil War?",
    "def_easy_243": "Which Soviet-origin 122 mm multiple rocket launcher is commonly called Grad?",
    "def_easy_249": "Which Kalashnikov-pattern rifle is being manufactured in India at Korwa/Amethi?",
    "def_easy_253": "Which indigenous Indian 5.56 mm rifle family was used widely by Indian forces?",
    "def_easy_257": "Which IWI light machine gun uses 7.62x51 mm NATO ammunition?",
    "def_easy_267": "Which historic Commonwealth light machine gun used .303 British ammunition?",
    "def_easy_289": "Which Israeli MALE UAV has been used by India for long-endurance surveillance?",
    "def_easy_297": "Which DRDO tactical UAV used catapult launch for battlefield reconnaissance?",
    "def_easy_303": "Which Hermes 900-derived MALE UAV is assembled in India as Drishti-10?",
    "def_easy_309": "Which DRDO indigenous medium-range SAM system came before Akash-NG?",
    "def_easy_317": "Which India-Israel missile family is also known as MRSAM or Barak-8?",
    "def_easy_321": "Which Israeli quick-reaction air defence system uses Python and Derby missiles?",
    "def_medium_282": "What is the origin most associated with the 84 mm Carl Gustaf recoilless rifle?",
    "def_hard_197": "Which description best identifies Carl Gustaf as an infantry support weapon?",
    "def_medium_304": "What is the origin most associated with Carl Gustaf in the anti-armour role?",
    "def_hard_208": "Which description best identifies Carl Gustaf as an anti-armour weapon?",
}


def place_options(answer: str, distractors: list[str], salt: int) -> tuple[list[str], int]:
    if len(distractors) != 3:
        raise ValueError(f"Need exactly 3 distractors for {answer}")
    options = distractors[:]
    insert_at = salt % 4
    options.insert(insert_at, answer)
    if len(options) != 4 or len(set(options)) != 4:
        raise ValueError(f"Bad options for {answer}: {options}")
    return options, insert_at


def other_values(records: list[dict], key: str, answer: str, fallback: list[str]) -> list[str]:
    values = []
    for record in records:
        value = record[key]
        if value != answer and value not in values:
            values.append(value)
    for value in fallback:
        if value != answer and value not in values:
            values.append(value)
    return values[:3]


ARTILLERY = [
    {"name": "ATAGS", "role": "Advanced 155 mm towed artillery gun", "calibre": "155 mm/52 calibre", "mobility": "Towed artillery", "origin": "India", "feature": "DRDO-led indigenous artillery programme"},
    {"name": "Dhanush", "role": "Indian 155 mm towed howitzer", "calibre": "155 mm/45 calibre", "mobility": "Towed artillery", "origin": "India", "feature": "Bofors-lineage upgraded Indian gun"},
    {"name": "K9 Vajra", "role": "Tracked self-propelled howitzer", "calibre": "155 mm/52 calibre", "mobility": "Tracked self-propelled artillery", "origin": "South Korea/India", "feature": "Indian version of the K9 Thunder"},
    {"name": "M777", "role": "Ultra-light towed howitzer", "calibre": "155 mm/39 calibre", "mobility": "Air-portable towed artillery", "origin": "United States/United Kingdom", "feature": "Can be moved by Chinook helicopter"},
    {"name": "Bofors FH77B", "role": "Towed field howitzer", "calibre": "155 mm/39 calibre", "mobility": "Towed artillery", "origin": "Sweden", "feature": "Famous Indian Army gun from the Kargil War"},
    {"name": "Pinaka", "role": "Multi-barrel rocket launcher", "calibre": "214 mm rockets", "mobility": "Truck-mounted rocket artillery", "origin": "India", "feature": "Indian DRDO rocket artillery system"},
    {"name": "BM-30 Smerch", "role": "Heavy multiple rocket launcher", "calibre": "300 mm rockets", "mobility": "Truck-mounted rocket artillery", "origin": "Russia", "feature": "Russian-origin heavy rocket artillery"},
    {"name": "BM-21 Grad", "role": "Multiple rocket launcher", "calibre": "122 mm rockets", "mobility": "Truck-mounted rocket artillery", "origin": "Soviet Union/Russia", "feature": "Widely used 122 mm rocket artillery system"},
    {"name": "M-46 field gun", "role": "130 mm towed field gun", "calibre": "130 mm", "mobility": "Towed artillery", "origin": "Soviet Union", "feature": "Long-serving 130 mm Indian Army field gun"},
    {"name": "105 mm Indian Field Gun", "role": "Light towed field gun", "calibre": "105 mm", "mobility": "Towed artillery", "origin": "India", "feature": "Indian light field artillery gun"},
]

SMALL_ARMS = [
    {"name": "AK-203", "role": "Assault rifle", "calibre": "7.62x39 mm", "family": "Kalashnikov rifle family", "origin": "Russia/India", "feature": "Manufactured in India at Korwa/Amethi"},
    {"name": "SIG716", "role": "Battle rifle", "calibre": "7.62x51 mm NATO", "family": "SIG Sauer rifle family", "origin": "United States", "feature": "Indian Army 7.62 mm frontline rifle procurement"},
    {"name": "INSAS rifle", "role": "Assault rifle", "calibre": "5.56x45 mm", "family": "Indian small-arms family", "origin": "India", "feature": "Indigenous rifle family used by Indian forces"},
    {"name": "Tavor X95", "role": "Bullpup assault rifle/carbine", "calibre": "5.56x45 mm", "family": "IWI Tavor family", "origin": "Israel", "feature": "Bullpup layout used by Indian special forces"},
    {"name": "Negev NG7", "role": "Light machine gun", "calibre": "7.62x51 mm NATO", "family": "IWI Negev family", "origin": "Israel", "feature": "7.62 mm light machine gun inducted by Indian forces"},
    {"name": "Dragunov SVD", "role": "Designated marksman rifle", "calibre": "7.62x54R mm", "family": "Soviet marksman rifle family", "origin": "Soviet Union/Russia", "feature": "Long-serving marksman rifle in Indian service"},
    {"name": "Vidhwansak", "role": "Anti-materiel rifle", "calibre": "12.7 mm", "family": "Heavy sniper/anti-materiel rifle", "origin": "India", "feature": "Indian heavy anti-materiel rifle"},
    {"name": "Carl Gustaf", "role": "Recoilless rifle", "calibre": "84 mm", "family": "Shoulder-fired support weapon", "origin": "Sweden", "feature": "Reusable anti-armour support weapon"},
    {"name": "MP5", "role": "Submachine gun", "calibre": "9x19 mm", "family": "Heckler & Koch submachine gun", "origin": "Germany", "feature": "Compact weapon used by police and special units"},
    {"name": "Bren gun", "role": "Light machine gun", "calibre": ".303 British", "family": "Commonwealth light machine gun", "origin": "United Kingdom/Czechoslovakia", "feature": "Historic light machine gun used by Indian troops"},
]

ANTI_TANK = [
    {"name": "Nag", "role": "Third-generation anti-tank guided missile", "platform": "NAMICA ground launcher", "guidance": "Imaging infrared seeker", "origin": "India", "feature": "DRDO fire-and-forget ATGM"},
    {"name": "HELINA", "role": "Helicopter-launched anti-tank missile", "platform": "Attack helicopter", "guidance": "Imaging infrared seeker", "origin": "India", "feature": "Helicopter-launched Nag-family missile"},
    {"name": "Dhruvastra", "role": "Air-launched anti-tank guided missile", "platform": "Helicopter", "guidance": "Imaging infrared seeker", "origin": "India", "feature": "Air-launched Nag-family weapon"},
    {"name": "MPATGM", "role": "Man-portable anti-tank guided missile", "platform": "Infantry tripod/launcher", "guidance": "Imaging infrared seeker", "origin": "India", "feature": "Indian man-portable ATGM programme"},
    {"name": "Milan-2T", "role": "Infantry anti-tank guided missile", "platform": "Portable launcher", "guidance": "Wire-guided SACLOS", "origin": "France/Germany", "feature": "BDL-produced Milan family ATGM"},
    {"name": "Konkurs-M", "role": "Anti-tank guided missile", "platform": "Vehicle or ground launcher", "guidance": "Wire-guided SACLOS", "origin": "Soviet Union/Russia", "feature": "Long-serving Russian-origin ATGM"},
    {"name": "Spike LR", "role": "Long-range anti-tank guided missile", "platform": "Portable or vehicle launcher", "guidance": "Electro-optical fire-and-forget/observe", "origin": "Israel", "feature": "Israeli long-range ATGM family"},
    {"name": "RPG-7", "role": "Rocket-propelled grenade launcher", "platform": "Shoulder-fired launcher", "guidance": "Unguided rocket", "origin": "Soviet Union/Russia", "feature": "Reusable shoulder-fired anti-armour launcher"},
    {"name": "Carl Gustaf", "role": "Recoilless anti-armour weapon", "platform": "Shoulder-fired launcher", "guidance": "Unguided recoilless round", "origin": "Sweden", "feature": "84 mm reusable infantry support weapon"},
    {"name": "NAMICA", "role": "Tracked Nag missile carrier", "platform": "BMP-2 based carrier", "guidance": "Nag missile fire-control system", "origin": "India", "feature": "Carrier vehicle for Nag ATGMs"},
]

DRONES = [
    {"name": "IAI Heron", "role": "Medium-altitude long-endurance UAV", "mission": "Intelligence, surveillance and reconnaissance", "origin": "Israel", "launch": "Runway take-off", "feature": "MALE surveillance UAV used by India"},
    {"name": "Searcher Mk II", "role": "Tactical surveillance UAV", "mission": "Reconnaissance and surveillance", "origin": "Israel", "launch": "Runway or assisted launch", "feature": "Tactical ISR UAV used by Indian forces"},
    {"name": "TAPAS BH-201", "role": "DRDO MALE UAV", "mission": "Long-endurance surveillance", "origin": "India", "launch": "Runway take-off", "feature": "Also known as Rustom-II"},
    {"name": "Rustom-I", "role": "Tactical UAV demonstrator", "mission": "Surveillance technology development", "origin": "India", "launch": "Runway take-off", "feature": "DRDO UAV technology demonstrator"},
    {"name": "DRDO Nishant", "role": "Tactical UAV", "mission": "Battlefield reconnaissance", "origin": "India", "launch": "Catapult launch", "feature": "Catapult-launched Indian tactical UAV"},
    {"name": "DRDO Lakshya", "role": "Pilotless target aircraft", "mission": "Target training for air defence", "origin": "India", "launch": "Launcher-assisted take-off", "feature": "Reusable aerial target system"},
    {"name": "MQ-9B SeaGuardian", "role": "High-endurance remotely piloted aircraft", "mission": "Maritime surveillance and strike-capable ISR", "origin": "United States", "launch": "Runway take-off", "feature": "Predator-family maritime RPAS"},
    {"name": "Drishti-10 Starliner", "role": "MALE surveillance UAV", "mission": "Maritime and land ISR", "origin": "India/Israel", "launch": "Runway take-off", "feature": "Hermes 900-derived UAV assembled in India"},
    {"name": "Netra UAV", "role": "Mini quadcopter UAV", "mission": "Short-range surveillance", "origin": "India", "launch": "Vertical take-off", "feature": "Indian mini UAV used for tactical surveillance"},
    {"name": "Nagastra-1", "role": "Loitering munition", "mission": "Precision attack after loitering", "origin": "India", "launch": "Portable launcher", "feature": "Indian loitering munition"},
]

AIR_DEFENCE = [
    {"name": "Akash", "role": "Medium-range surface-to-air missile system", "range_class": "Medium range", "platform": "Ground-based mobile launcher", "origin": "India", "feature": "DRDO indigenous SAM system"},
    {"name": "Akash-NG", "role": "New-generation surface-to-air missile", "range_class": "Medium range", "platform": "Ground-based launcher", "origin": "India", "feature": "New-generation Akash family missile"},
    {"name": "QRSAM", "role": "Quick-reaction surface-to-air missile", "range_class": "Short to medium range", "platform": "Mobile ground launcher", "origin": "India", "feature": "Quick-reaction SAM for mobile formations"},
    {"name": "VL-SRSAM", "role": "Vertical-launch short-range surface-to-air missile", "range_class": "Short range", "platform": "Naval vertical launch system", "origin": "India", "feature": "Shipborne short-range air defence missile"},
    {"name": "MRSAM/Barak-8", "role": "Medium-range surface-to-air missile", "range_class": "Medium range", "platform": "Ground and naval launchers", "origin": "India/Israel", "feature": "Joint India-Israel air defence missile"},
    {"name": "S-400 Triumf", "role": "Long-range air defence system", "range_class": "Long range", "platform": "Mobile ground launchers", "origin": "Russia", "feature": "Russian long-range air defence system bought by India"},
    {"name": "SPYDER", "role": "Quick-reaction air defence system", "range_class": "Short range", "platform": "Mobile ground launcher", "origin": "Israel", "feature": "Uses Python and Derby missile family"},
    {"name": "Igla-S", "role": "Man-portable air defence system", "range_class": "Very short range", "platform": "Shoulder-fired launcher", "origin": "Russia", "feature": "MANPADS used for point air defence"},
    {"name": "L-70 gun", "role": "Anti-aircraft gun", "range_class": "Short range", "platform": "Towed gun system", "origin": "Sweden", "feature": "40 mm air defence gun"},
    {"name": "ZU-23-2", "role": "Twin-barrel anti-aircraft gun", "range_class": "Short range", "platform": "Towed or vehicle-mounted gun", "origin": "Soviet Union/Russia", "feature": "23 mm twin anti-aircraft gun"},
]


def system_questions(records: list[dict], group: str, fields: list[tuple[int, str, str]]) -> list[tuple[int, str, str, list[str], str]]:
    questions = []
    for record in records:
        for difficulty, key, template in fields:
            answer = record[key]
            distractors = other_values(records, key, answer, [])
            question = template.format(**record)
            questions.append((difficulty, question, answer, distractors, group))
    return questions


def make_facts() -> list[tuple[int, str, str, list[str], str]]:
    facts: list[tuple[int, str, str, list[str], str]] = []
    facts += system_questions(ARTILLERY, "artillery_rocket_artillery", [
        (1, "name", "Which artillery system is best described as: {role}?"),
        (1, "calibre", "What calibre is associated with {name}?"),
        (2, "mobility", "What mobility/type best fits {name}?"),
        (2, "origin", "What is the origin most associated with {name}?"),
        (3, "feature", "Which description best identifies {name}?"),
    ])
    facts += system_questions(SMALL_ARMS, "small_arms_infantry_weapons", [
        (1, "name", "Which infantry weapon is best described as: {role}?"),
        (1, "calibre", "What cartridge/calibre is associated with {name}?"),
        (2, "family", "Which weapon family best fits {name}?"),
        (2, "origin", "What is the origin most associated with {name}?"),
        (3, "feature", "Which description best identifies {name}?"),
    ])
    facts += system_questions(ANTI_TANK, "anti_tank_weapons", [
        (1, "name", "Which anti-armour weapon is best described as: {role}?"),
        (1, "platform", "What launch platform best fits {name}?"),
        (2, "guidance", "What guidance style best fits {name}?"),
        (2, "origin", "What is the origin most associated with {name}?"),
        (3, "feature", "Which description best identifies {name}?"),
    ])
    facts += system_questions(DRONES, "drones_uavs_loitering", [
        (1, "name", "Which unmanned system is best described as: {role}?"),
        (1, "mission", "What mission best fits {name}?"),
        (2, "origin", "What is the origin most associated with {name}?"),
        (2, "launch", "What launch method best fits {name}?"),
        (3, "feature", "Which description best identifies {name}?"),
    ])
    facts += system_questions(AIR_DEFENCE, "air_defence_systems", [
        (1, "name", "Which air defence system is best described as: {role}?"),
        (1, "range_class", "What range class best fits {name}?"),
        (2, "platform", "What launch platform best fits {name}?"),
        (2, "origin", "What is the origin most associated with {name}?"),
        (3, "feature", "Which description best identifies {name}?"),
    ])
    return facts


def build_questions() -> list[dict]:
    counters: Counter[int] = Counter()
    questions: list[dict] = []
    for salt, (difficulty, question, answer, distractors, group) in enumerate(make_facts()):
        counters[difficulty] += 1
        seq = STARTS[difficulty] + counters[difficulty] - 1
        qid = f"def_{LABELS[difficulty]}_{seq:03d}"
        question = QUESTION_OVERRIDES.get(qid, question)
        options, correct_index = place_options(answer, distractors, salt)
        questions.append({
            "id": qid,
            "category": "defense",
            "difficulty": difficulty,
            "question": question,
            "options": options,
            "correct_index": correct_index,
            "source_note": group,
        })
    return questions


def validate_new(questions: list[dict], bank: list[dict]) -> None:
    existing_ids = {q["id"] for q in bank}
    existing_questions = {q["question"].strip().lower() for q in bank}
    ids = [q["id"] for q in questions]
    if len(questions) != 250:
        raise ValueError(f"Expected 250 questions, got {len(questions)}")
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
            raise ValueError(f"Bad options: {q['id']} {q['options']}")
        if q["correct_index"] not in {0, 1, 2, 3}:
            raise ValueError(f"Bad correct_index: {q['id']}")


def main() -> None:
    bank = json.loads(BANK.read_text())
    questions = build_questions()
    validate_new(questions, bank)
    bank.extend(questions)
    GENERATED.write_text(json.dumps(questions, indent=2) + "\n")
    BANK.write_text(json.dumps(bank, indent=2) + "\n")
    by_diff = Counter(q["difficulty"] for q in questions)
    by_group = Counter(q["source_note"] for q in questions)
    print(f"Wrote {len(questions)} new army systems defense questions")
    print(f"Breakdown by difficulty: {dict(sorted(by_diff.items()))}")
    print(f"Breakdown by group: {dict(sorted(by_group.items()))}")
    print(f"Merged bank total: {len(bank)}")


if __name__ == "__main__":
    main()
