#!/usr/bin/env python3
"""Add Air Force platform, weapons, and air-combat concept trivia."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "backend/app/data/gk_questions.json"
GENERATED = ROOT / "backend/app/data/defense_airforce_systems_generated_100.json"

STARTS = {1: 329, 2: 347, 3: 230}
LABELS = {1: "easy", 2: "medium", 3: "hard"}


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
    # Easy: active platforms, roles, and core concepts.
    (1, "Which concept means attacking from outside the immediate reach of enemy defences?", "Standoff strike", ["Dogfighting", "Aerial refuelling", "Formation landing"], "air_combat_concepts"),
    (1, "Which IAF fighter is a French-origin omnirole aircraft with Meteor and SCALP capability?", "Rafale", ["Mirage 2000", "Jaguar", "MiG-29UPG"], "air_platforms"),
    (1, "Which Indian fighter is manufactured by HAL as the Light Combat Aircraft?", "Tejas", ["Rafale", "Mirage 2000", "Jaguar"], "air_platforms"),
    (1, "Which IAF aircraft is strongly associated with the 2019 Balakot strike?", "Mirage 2000", ["Rafale", "Tejas", "MiG-29UPG"], "air_platforms"),
    (1, "Which upgraded MiG-29 variant serves the IAF in the air-superiority role?", "MiG-29UPG", ["MiG-29K", "MiG-21 Bison", "MiG-27"], "air_platforms"),
    (1, "Which IAF aircraft is a deep-strike platform originally developed by Britain and France?", "Jaguar", ["Mirage 2000", "Rafale", "Tejas"], "air_platforms"),
    (1, "Which aircraft is the IAF's heavy strategic airlifter?", "C-17 Globemaster III", ["C-130J Super Hercules", "IL-78MKI", "C-295"], "support_aircraft"),
    (1, "Which aircraft is the IAF's tactical airlifter used for special operations?", "C-130J Super Hercules", ["C-17 Globemaster III", "IL-78MKI", "Netra AEW&C"], "support_aircraft"),
    (1, "Which IAF aircraft is primarily an aerial refuelling tanker?", "IL-78MKI", ["C-17 Globemaster III", "Netra AEW&C", "C-130J Super Hercules"], "support_aircraft"),
    (1, "Which larger IAF AWACS platform is based on the Il-76 airframe?", "Phalcon AWACS", ["Netra AEW&C", "IL-78MKI", "C-295"], "support_aircraft"),
    (1, "Which IAF helicopter is a medium-lift transport workhorse?", "Mi-17V5", ["CH-47F Chinook", "AH-64E Apache", "HAL Prachand"], "helicopters"),
    (1, "Which IAF helicopter is a dedicated attack helicopter made by Boeing?", "AH-64E Apache", ["CH-47F Chinook", "Mi-17V5", "HAL Dhruv"], "helicopters"),
    (1, "Which Indian helicopter is HAL's Light Combat Helicopter?", "Prachand", ["Rudra", "Dhruv", "Chetak"], "helicopters"),
    (1, "Which armed helicopter is based on the HAL Dhruv family?", "Rudra", ["Prachand", "Apache", "Chinook"], "helicopters"),
    (1, "Which missile type is meant to engage aircraft beyond visual range?", "BVR air-to-air missile", ["WVR air-to-air missile", "Anti-radiation missile", "Cruise missile"], "air_combat_concepts"),
    (1, "In air combat, what does WVR usually mean?", "Within-visual-range", ["Weapon-velocity rating", "Wide-vector radar", "Wing-vortex regime"], "air_combat_concepts"),
    (1, "Which missile type is most relevant in close-range dogfighting?", "Infrared WVR missile", ["Submarine-launched missile", "Anti-ship cruise missile", "Anti-tank missile"], "air_combat_concepts"),
    (1, "Which mission attacks enemy radar and air-defence emitters?", "SEAD", ["Airlift", "Aerial refuelling", "Air policing"], "air_combat_concepts"),
    (1, "Which aircraft sensor type can scan electronically without mechanically steering the antenna?", "AESA radar", ["Pulse-only altimeter", "Optical gunsight", "Magnetic compass"], "sensors_avionics"),
    (1, "Which cockpit system helps a pilot cue weapons by looking toward a target?", "Helmet-mounted sight", ["Drop tank", "Airbrake", "Refuelling probe"], "sensors_avionics"),
    (1, "Which missile category does Astra belong to?", "BVR air-to-air missile", ["Anti-radiation missile", "WVR air-to-air missile", "Anti-tank missile"], "air_weapons"),
    (1, "Which missile category does Rudram-1 belong to?", "Anti-radiation missile", ["WVR air-to-air missile", "Anti-tank missile", "Submarine-launched missile"], "air_weapons"),
    (1, "Which Rafale missile is known for long-range BVR air combat?", "Meteor", ["SCALP", "HAMMER", "Rudram-1"], "air_weapons"),
    (1, "Which Rafale weapon is a long-range cruise missile for deep strike?", "SCALP", ["Meteor", "MICA", "Astra"], "air_weapons"),
    (1, "Which Rafale weapon is a precision-guided bomb kit?", "HAMMER", ["Meteor", "MICA", "R-77"], "air_weapons"),
    (1, "Which missile family includes both IR and RF air-to-air variants on Rafale?", "MICA", ["Meteor", "SCALP", "HAMMER"], "air_weapons"),
    (1, "Which Russian-origin BVR missile family is associated with Su-30MKI and MiG-29UPG?", "R-77", ["R-73", "R-27", "Kh-31"], "air_weapons"),
    (1, "Which Russian-origin WVR missile family is associated with close air combat?", "R-73", ["R-77", "Kh-59", "R-27"], "air_weapons"),
    (1, "Which IAF aircraft type carries airborne warning and control radar?", "AWACS/AEW&C aircraft", ["Aerial tanker", "Attack helicopter", "Trainer aircraft"], "support_aircraft"),
    (1, "Which aircraft role moves troops and cargo across long distances?", "Strategic airlift", ["Air superiority", "SEAD", "Close air support"], "air_combat_concepts"),

    # Medium: role distinctions, compatible systems, and evergreen tactics.
    (2, "Which platform role best fits Rafale in IAF service?", "Omnirole fighter", ["Heavy airlifter", "Aerial tanker", "AEW&C aircraft"], "air_platforms"),
    (2, "Which platform role best fits Su-30MKI?", "Heavy multirole fighter", ["Light utility helicopter", "Strategic airlifter", "Basic trainer"], "air_platforms"),
    (2, "Which platform role best fits Tejas Mk1/Mk1A?", "Light multirole fighter", ["Heavy bomber", "Aerial tanker", "Attack helicopter"], "air_platforms"),
    (2, "Which platform role best fits Jaguar in IAF service?", "Deep-strike aircraft", ["AEW&C aircraft", "Heavy-lift helicopter", "Aerial tanker"], "air_platforms"),
    (2, "Which platform role best fits Mirage 2000 in IAF service?", "Multirole strike fighter", ["Heavy airlifter", "Trainer helicopter", "Aerial tanker"], "air_platforms"),
    (2, "Which aircraft role best fits MiG-29UPG?", "Air-superiority fighter", ["Strategic airlifter", "Attack helicopter", "AEW&C platform"], "air_platforms"),
    (2, "Which aircraft role best fits C-17 Globemaster III?", "Heavy strategic airlift", ["Aerial refuelling", "Close air support", "Airborne warning"], "support_aircraft"),
    (2, "Which aircraft role best fits C-130J Super Hercules?", "Tactical airlift and special operations", ["Heavy strategic airlift", "Airborne early warning", "Dedicated air superiority"], "support_aircraft"),
    (2, "Which aircraft role best fits IL-78MKI?", "Aerial refuelling", ["Tactical airlift", "Airborne early warning", "Close air support"], "support_aircraft"),
    (2, "Which aircraft role best fits Netra AEW&C?", "Airborne early warning and control", ["Aerial refuelling", "Heavy strategic airlift", "Attack helicopter"], "support_aircraft"),
    (2, "Which helicopter role best fits AH-64E Apache?", "Attack helicopter", ["Heavy-lift helicopter", "AEW&C helicopter", "Basic trainer"], "helicopters"),
    (2, "Which helicopter role best fits CH-47F Chinook?", "Heavy-lift helicopter", ["Attack helicopter", "Light observation helicopter", "AEW&C helicopter"], "helicopters"),
    (2, "Which helicopter role best fits Prachand?", "High-altitude light combat helicopter", ["Heavy-lift helicopter", "Aerial tanker", "Maritime patrol aircraft"], "helicopters"),
    (2, "Which helicopter role best fits Mi-17V5?", "Medium-lift transport helicopter", ["Carrier-borne fighter", "AEW&C aircraft", "Strategic airlifter"], "helicopters"),
    (2, "Which air-combat term describes engaging targets before pilots can see them visually?", "BVR combat", ["WVR combat", "Taxiing", "Formation landing"], "air_combat_concepts"),
    (2, "Which air-combat term describes close-range visual engagements?", "WVR combat", ["BVR combat", "Strategic airlift", "Aerial refuelling"], "air_combat_concepts"),
    (2, "Which capability is most useful for a fighter in BVR combat?", "Radar and active radar missiles", ["Cargo ramp", "Tandem rotors", "Towed decoy only"], "air_combat_concepts"),
    (2, "Which capability is most useful in close WVR dogfighting?", "High off-boresight missile cueing", ["Cargo pallet loading", "Aerial refuelling boom", "Long runway braking"], "air_combat_concepts"),
    (2, "Which mission type tries to reduce enemy air-defence radar threats?", "SEAD", ["Strategic airlift", "Combat search logistics", "Basic flying training"], "air_combat_concepts"),
    (2, "Which mission type focuses on gaining control of the air against enemy aircraft?", "Air superiority", ["Aerial refuelling", "Troop transport", "Maritime sealift"], "air_combat_concepts"),
    (2, "Which mission type attacks enemy ground targets behind the front line?", "Air interdiction", ["Air superiority patrol", "Aerial refuelling", "Airborne early warning"], "air_combat_concepts"),
    (2, "Which mission type supports friendly ground troops near the battlefield?", "Close air support", ["Strategic airlift", "Airborne early warning", "Aerial refuelling"], "air_combat_concepts"),
    (2, "Which sensor is associated with Rafale's modern radar family?", "RBE2 AESA", ["N011M Bars", "Uttam AESA", "EL/M-2248 MF-STAR"], "sensors_avionics"),
    (2, "Which avionics system helps aircraft identify friendly aircraft electronically?", "IFF transponder", ["Radar warning receiver", "AESA radar", "Laser designator"], "sensors_avionics"),
    (2, "Which radar concept uses many transmit-receive modules for electronic scanning?", "AESA radar", ["Mechanical radar", "Radar altimeter", "Weather radar"], "sensors_avionics"),
    (2, "Which airborne system lets commanders see farther than ground radar limited by terrain?", "AWACS/AEW&C", ["Drop tank", "Gun pod", "Airbrake"], "sensors_avionics"),
    (2, "Which system warns a fighter that hostile radar may be tracking it?", "Radar warning receiver", ["Cargo winch", "Weather vane", "Landing hook"], "sensors_avionics"),
    (2, "Which defensive aids are released to confuse missiles?", "Chaff and flares", ["Drop tanks", "Wheel chocks", "Cargo pallets"], "sensors_avionics"),
    (2, "Which missile is an Indian BVR air-to-air weapon?", "Astra", ["Rudram-1", "SCALP", "HAMMER"], "air_weapons"),
    (2, "Which missile is designed to home on enemy radar emissions?", "Rudram-1", ["Astra", "Meteor", "MICA"], "air_weapons"),
    (2, "SCALP is best matched with which strike role?", "Air-launched deep strike", ["Close dogfight", "Aerial refuelling", "Anti-tank ambush"], "air_weapons"),
    (2, "HAMMER is closest to which aircraft weapon category?", "Precision-guided bomb kit", ["BVR missile", "Anti-radiation missile", "Aerial refuelling pod"], "air_weapons"),
    (2, "Meteor is primarily used in which air-combat envelope?", "Long-range BVR combat", ["Close WVR combat", "SEAD mission", "Aerial refuelling"], "air_weapons"),
    (2, "R-73 is primarily used in which air-combat envelope?", "Close WVR combat", ["BVR radar combat", "Deep strike", "Aerial refuelling"], "air_weapons"),
    (2, "R-77 is primarily used in which air-combat envelope?", "BVR radar-guided combat", ["Close infrared combat", "Precision bombing", "Anti-tank attack"], "air_weapons"),
    (2, "Which weapon type best describes MICA?", "Air-to-air missile family", ["Heavy torpedo", "Rocket artillery", "Infantry mortar"], "air_weapons"),
    (2, "Which platform pairing is most natural for Meteor in Indian service?", "Rafale", ["C-17", "Apache", "IL-78MKI"], "air_weapons"),
    (2, "Which platform pairing is most natural for Astra in Indian service?", "Su-30MKI", ["C-130J", "Chinook", "IL-78MKI"], "air_weapons"),
    (2, "Which platform pairing is most natural for Rudram-1 testing and carriage?", "Su-30MKI", ["C-17", "Prachand", "C-295"], "air_weapons"),
    (2, "Which concept describes using tankers to extend fighter range?", "Aerial refuelling", ["Air interdiction", "Dogfighting", "Taxiing"], "air_combat_concepts"),

    # Hard: more specific concepts and active-system distinctions.
    (3, "Why are active radar-homing missiles important in BVR combat?", "They can guide themselves in the terminal phase", ["They replace aircraft engines", "They make aircraft invisible", "They carry cargo pallets"], "air_combat_concepts"),
    (3, "What does high off-boresight missile capability help a pilot do?", "Engage targets away from the aircraft nose direction", ["Carry more fuel in the wing", "Land on shorter runways", "Refuel cargo aircraft"], "air_combat_concepts"),
    (3, "What is the main purpose of a helmet-mounted sight in air combat?", "Cue sensors or missiles toward where the pilot looks", ["Increase cargo capacity", "Reduce runway length", "Act as an oxygen generator"], "sensors_avionics"),
    (3, "What is the main advantage of AESA radar over older mechanically scanned radar?", "Fast electronic beam steering", ["Larger landing gear", "Manual target plotting", "Lower cockpit visibility"], "sensors_avionics"),
    (3, "Which term best fits a fighter patrol meant to protect friendly airspace?", "Combat air patrol", ["Strategic airlift", "Aerial refuelling orbit", "Ground convoy"], "air_combat_concepts"),
    (3, "Which term best fits a mission to escort strike aircraft against enemy fighters?", "Fighter escort", ["Cargo drop", "Airborne refuelling", "Radar calibration only"], "air_combat_concepts"),
    (3, "Which term best fits attacking runways, depots, or bridges behind enemy lines?", "Air interdiction", ["Close formation taxi", "Aerial refuelling", "Airfield maintenance"], "air_combat_concepts"),
    (3, "Which term best fits destroying or disrupting hostile radar-guided air defences?", "SEAD", ["Airlift", "Meteorology", "Search and rescue logistics"], "air_combat_concepts"),
    (3, "Which term best fits an aircraft that detects and manages air battles from altitude?", "AEW&C", ["CIWS", "ATGM", "MRLS"], "sensors_avionics"),
    (3, "Which aircraft is a better fit for heavy cargo into major airbases than austere special-ops strips?", "C-17 Globemaster III", ["C-130J Super Hercules", "Apache", "Rafale"], "support_aircraft"),
    (3, "Which aircraft is a better fit for special-operations tactical airlift than heavy strategic airlift?", "C-130J Super Hercules", ["C-17 Globemaster III", "IL-78MKI", "Netra AEW&C"], "support_aircraft"),
    (3, "Which platform is a better fit for aerial refuelling than airborne warning?", "IL-78MKI", ["Netra AEW&C", "Phalcon AWACS", "C-295"], "support_aircraft"),
    (3, "Which platform is a better fit for airborne warning than aerial refuelling?", "Netra AEW&C", ["IL-78MKI", "C-130J", "C-17"], "support_aircraft"),
    (3, "Which helicopter is a better fit for lifting artillery loads than anti-armour attack?", "CH-47F Chinook", ["AH-64E Apache", "Prachand", "Rudra"], "helicopters"),
    (3, "Which helicopter is a better fit for anti-armour attack than heavy-lift transport?", "AH-64E Apache", ["CH-47F Chinook", "Mi-17V5", "Chetak"], "helicopters"),
    (3, "Which Indian helicopter is more specialized for high-altitude combat than general utility lift?", "Prachand", ["Dhruv", "Chetak", "Cheetah"], "helicopters"),
    (3, "Which missile is a better fit for BVR air combat than SEAD?", "Astra", ["Rudram-1", "SCALP", "HAMMER"], "air_weapons"),
    (3, "Which missile is a better fit for SEAD than air-to-air combat?", "Rudram-1", ["Astra", "Meteor", "R-73"], "air_weapons"),
    (3, "Which weapon is a better fit for deep strike than dogfighting?", "SCALP", ["R-73", "MICA IR", "Helmet-mounted sight"], "air_weapons"),
    (3, "Which weapon is a better fit for close WVR combat than deep strike?", "R-73", ["SCALP", "Rudram-1", "BrahMos-A"], "air_weapons"),
    (3, "Which Rafale weapon is a better fit for BVR air combat than precision bombing?", "Meteor", ["HAMMER", "SCALP", "Rudram-1"], "air_weapons"),
    (3, "Which Rafale weapon is a better fit for precision bombing than BVR air combat?", "HAMMER", ["Meteor", "R-77", "Astra"], "air_weapons"),
    (3, "Which radar family is a better fit for Rafale than Su-30MKI?", "RBE2 AESA", ["N011M Bars", "Zhuk-ME", "Uttam AESA"], "sensors_avionics"),
    (3, "Which radar family is a better fit for Su-30MKI than Rafale?", "N011M Bars", ["RBE2 AESA", "Uttam AESA", "EL/M-2052"], "sensors_avionics"),
    (3, "Which term describes resistance to hostile jamming in radar and communications?", "ECCM", ["ECM", "IFF", "RWR"], "sensors_avionics"),
    (3, "Which feature helps fighters survive missile threats by creating false targets?", "Chaff and flare dispensers", ["Cargo ramp", "Wing fence only", "Runway arrester barrier"], "sensors_avionics"),
    (3, "Which feature helps a fighter know it is being painted by hostile radar?", "Radar warning receiver", ["Drop tank", "Cargo pallet", "Brake parachute"], "sensors_avionics"),
    (3, "Which role best separates an attack helicopter from a heavy-lift helicopter?", "Armed attack against ground targets", ["Moving oversized cargo", "Aerial refuelling", "Airborne early warning"], "helicopters"),
    (3, "Which role best separates a tanker from a transport aircraft?", "Refuelling aircraft in flight", ["Dropping paratroopers only", "Detecting enemy radar only", "Dogfighting"], "support_aircraft"),
    (3, "Which air-combat concept best explains why AWACS aircraft are valuable?", "They extend detection and battle management range", ["They replace runway lighting", "They tow artillery", "They launch infantry mortars"], "sensors_avionics"),
]


def build_questions() -> list[dict]:
    counters: Counter[int] = Counter()
    questions: list[dict] = []
    for salt, (difficulty, question, answer, distractors, group) in enumerate(FACTS):
        counters[difficulty] += 1
        seq = STARTS[difficulty] + counters[difficulty] - 1
        qid = f"def_{LABELS[difficulty]}_{seq:03d}"
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
    if len(questions) != 100:
        raise ValueError(f"Expected 100 questions, got {len(questions)}")
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


def dedupe_existing(bank: list[dict]) -> list[str]:
    changes = []
    deduped = []
    for q in bank:
        if q.get("id") == "def_medium_200":
            q["question"] = "Which IAF fighter is a twin-engine heavy multirole aircraft with canards and thrust vectoring?"
            changes.append("Reworded def_medium_200 away from duplicate BrahMos/Su-30MKI phrasing")
        deduped.append(q)
    bank[:] = deduped
    return changes


def main() -> None:
    bank = json.loads(BANK.read_text())
    questions = build_questions()
    validate_new(questions, bank)
    changes = dedupe_existing(bank)
    bank.extend(questions)
    GENERATED.write_text(json.dumps(questions, indent=2) + "\n")
    BANK.write_text(json.dumps(bank, indent=2) + "\n")
    print(f"Wrote {len(questions)} new Air Force defense questions")
    print(f"Breakdown: {dict(sorted(Counter(q['difficulty'] for q in questions).items()))}")
    print(f"Groups: {dict(sorted(Counter(q['source_note'] for q in questions).items()))}")
    print(f"Dedupe changes: {changes}")
    print(f"Merged bank total: {len(bank)}")


if __name__ == "__main__":
    main()
