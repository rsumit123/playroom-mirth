#!/usr/bin/env python3
"""Add evergreen defense-literacy questions to the GK bank."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "backend" / "app" / "data" / "gk_questions.json"
OUT_PATH = ROOT / "backend" / "app" / "data" / "defense_platform_literacy_generated_105.json"


def q(difficulty: int, question: str, options: list[str], correct: str, note: str) -> dict:
    return {
        "category": "defense",
        "difficulty": difficulty,
        "question": question,
        "options": options,
        "correct_index": options.index(correct),
        "source_note": note,
    }


QUESTIONS = [
    q(1, "Which Army corps is most associated with combat bridges, obstacles, and field fortifications?", ["Corps of Engineers", "Army Service Corps", "Army Medical Corps", "Corps of Signals"], "Corps of Engineers", "combat_support"),
    q(1, "Which Army corps keeps battlefield communications and networks running?", ["Army Ordnance Corps", "Corps of Signals", "Corps of Engineers", "Armoured Corps"], "Corps of Signals", "combat_support"),
    q(1, "Which Army corps is responsible for repair and recovery of military equipment?", ["Corps of EME", "Infantry", "Army Medical Corps", "Corps of Military Police"], "Corps of EME", "combat_support"),
    q(1, "Which Army service handles supplies such as rations, fuel, and transport support?", ["Army Service Corps", "Corps of Signals", "Army Air Defence", "Mechanised Infantry"], "Army Service Corps", "combat_support"),
    q(1, "Which Army corps provides medical care to soldiers in peace and war?", ["Army Medical Corps", "Army Ordnance Corps", "Corps of Engineers", "Regiment of Artillery"], "Army Medical Corps", "combat_support"),
    q(1, "Which organization builds and maintains strategic roads in India's border areas?", ["Border Roads Organisation", "National Highways Authority", "Indian Coast Guard", "Central Reserve Police Force"], "Border Roads Organisation", "combat_support"),
    q(1, "What is the common Army term for soldiers of the Corps of Engineers?", ["Sappers", "Gunners", "Sailors", "Air warriors"], "Sappers", "combat_support"),
    q(1, "Which bridge type is famous for quick military construction without heavy machinery?", ["Bailey bridge", "Cable-stayed bridge", "Suspension bridge", "Arch bridge"], "Bailey bridge", "combat_support"),
    q(1, "Which support function moves ammunition, fuel, food, and spares to fighting units?", ["Logistics", "Camouflage", "Saluting", "Drill"], "Logistics", "combat_support"),
    q(1, "Which Army branch is linked with ammunition and stores management?", ["Army Ordnance Corps", "Army Medical Corps", "Corps of Signals", "Judge Advocate General branch"], "Army Ordnance Corps", "combat_support"),
    q(1, "Which force protects India's maritime zones and conducts search and rescue at sea?", ["Indian Coast Guard", "Railway Protection Force", "Central Industrial Security Force", "Assam Rifles"], "Indian Coast Guard", "coast_guard_capf"),
    q(1, "Which ministry does the Indian Coast Guard come under?", ["Ministry of Defence", "Ministry of Home Affairs", "Ministry of Shipping", "Ministry of External Affairs"], "Ministry of Defence", "coast_guard_capf"),
    q(1, "Which force is best known for guarding India's borders with Pakistan and Bangladesh?", ["Border Security Force", "Central Reserve Police Force", "Central Industrial Security Force", "Indo-Tibetan Border Police"], "Border Security Force", "coast_guard_capf"),
    q(1, "Which force is best known for guarding India's border with China in the Himalayas?", ["Indo-Tibetan Border Police", "Central Reserve Police Force", "Railway Protection Force", "National Security Guard"], "Indo-Tibetan Border Police", "coast_guard_capf"),
    q(1, "Which force is mainly associated with internal security and riot-control duties?", ["Central Reserve Police Force", "Indian Coast Guard", "Corps of EME", "Army Service Corps"], "Central Reserve Police Force", "coast_guard_capf"),
    q(1, "Which force guards many airports and critical industrial facilities in India?", ["Central Industrial Security Force", "Border Security Force", "Assam Rifles", "Sashastra Seema Bal"], "Central Industrial Security Force", "coast_guard_capf"),
    q(1, "Which force is closely associated with security in India's North-East and the Myanmar border?", ["Assam Rifles", "Central Industrial Security Force", "Indian Coast Guard", "Army Ordnance Corps"], "Assam Rifles", "coast_guard_capf"),
    q(1, "Which CAPF guards India's open borders with Nepal and Bhutan?", ["Sashastra Seema Bal", "Border Security Force", "Central Reserve Police Force", "Defence Security Corps"], "Sashastra Seema Bal", "coast_guard_capf"),
    q(1, "Which tri-service agency handles military cyber operations?", ["Defence Cyber Agency", "Defence Space Agency", "National Cadet Corps", "Border Roads Organisation"], "Defence Cyber Agency", "cyber_space_ew"),
    q(1, "Which Indian defence agency focuses on military use of space?", ["Defence Space Agency", "Defence Cyber Agency", "Indian Coast Guard", "Army Service Corps"], "Defence Space Agency", "cyber_space_ew"),
    q(1, "What does ASAT stand for in defence discussions?", ["Anti-satellite", "Air-sea attack", "Armoured support artillery", "Advanced shipborne torpedo"], "Anti-satellite", "cyber_space_ew"),
    q(1, "Mission Shakti demonstrated which Indian capability?", ["Anti-satellite interception", "Aircraft-carrier landing", "Mountain bridging", "Submarine rescue"], "Anti-satellite interception", "cyber_space_ew"),
    q(1, "Which countermeasure confuses radar-guided missiles by releasing metallic strips?", ["Chaff", "Flares", "Smoke grenade", "Sonobuoy"], "Chaff", "cyber_space_ew"),
    q(1, "Which countermeasure is mainly used to decoy heat-seeking missiles?", ["Flares", "Chaff", "IFF", "Sonar buoy"], "Flares", "cyber_space_ew"),
    q(1, "Which system warns an aircraft that hostile radar may be tracking it?", ["Radar warning receiver", "Drop tank", "Cargo winch", "Arrester hook"], "Radar warning receiver", "cyber_space_ew"),
    q(1, "Which system helps identify friendly aircraft and reduce mistaken engagements?", ["IFF", "RWR", "ECM pod", "Flight data recorder"], "IFF", "cyber_space_ew"),
    q(1, "What does India's No First Use policy refer to?", ["Nuclear weapons", "Aircraft carriers", "Military satellites", "Border roads"], "Nuclear weapons", "nuclear_doctrine"),
    q(1, "Which term means the ability to retaliate after absorbing a nuclear attack?", ["Second-strike capability", "Close air support", "River crossing", "Search and rescue"], "Second-strike capability", "nuclear_doctrine"),
    q(1, "Which three legs form a nuclear triad?", ["Land, air, and sea", "Infantry, cavalry, and artillery", "Radar, sonar, and lidar", "Fuel, food, and water"], "Land, air, and sea", "nuclear_doctrine"),
    q(1, "Which command is associated with management of India's nuclear forces?", ["Strategic Forces Command", "Training Command", "Eastern Naval Command", "Army Service Corps"], "Strategic Forces Command", "nuclear_doctrine"),
    q(1, "Which Indian company is best known for making aircraft such as Tejas and Dhruv?", ["HAL", "BEL", "BDL", "MIDHANI"], "HAL", "defense_industry"),
    q(1, "Which Indian DPSU is strongly associated with defence electronics and radars?", ["BEL", "HAL", "MDL", "GRSE"], "BEL", "defense_industry"),
    q(1, "Which Indian DPSU is strongly associated with missile production?", ["BDL", "BEL", "HAL", "GSL"], "BDL", "defense_industry"),
    q(1, "Which Mumbai shipyard is known for building major warships and submarines?", ["Mazagon Dock Shipbuilders", "Garden Reach Shipbuilders", "Goa Shipyard", "Hindustan Shipyard"], "Mazagon Dock Shipbuilders", "defense_industry"),
    q(1, "Which Kolkata shipyard is known for building Indian Navy warships?", ["Garden Reach Shipbuilders", "Mazagon Dock Shipbuilders", "Goa Shipyard", "Cochin Shipyard"], "Garden Reach Shipbuilders", "defense_industry"),

    q(2, "Which combat-support task is most directly handled by Army engineers during an advance?", ["Breaching obstacles", "Writing air traffic rules", "Running naval sonar", "Issuing court warrants"], "Breaching obstacles", "combat_support"),
    q(2, "Which support arm is most likely to lay and maintain field communication links?", ["Corps of Signals", "Army Medical Corps", "Army Ordnance Corps", "Armoured Corps"], "Corps of Signals", "combat_support"),
    q(2, "Which corps would usually recover a disabled tank or repair a generator in the field?", ["Corps of EME", "Corps of Signals", "Army Education Corps", "Army Postal Service"], "Corps of EME", "combat_support"),
    q(2, "Which support service is most directly linked to fuel convoys and supply columns?", ["Army Service Corps", "Corps of Engineers", "Intelligence Corps", "Army Air Defence"], "Army Service Corps", "combat_support"),
    q(2, "Which Army branch would be the most relevant for ammunition depots and ordnance stores?", ["Army Ordnance Corps", "Army Medical Corps", "Corps of Signals", "Remount Veterinary Corps"], "Army Ordnance Corps", "combat_support"),
    q(2, "Which military task means opening a safe route through mines or obstacles?", ["Breaching", "Dogfighting", "Sonar ranging", "Court martial"], "Breaching", "combat_support"),
    q(2, "Which military task means making roads, bridges, and camps usable for forces?", ["Field engineering", "Air policing", "Signals intelligence", "Maritime boarding"], "Field engineering", "combat_support"),
    q(2, "Which support system matters most when a formation fights far from its bases?", ["Supply chain depth", "Parade alignment", "Medal precedence", "Uniform tailoring"], "Supply chain depth", "combat_support"),
    q(2, "Which organization is most relevant when a mountain road near the LAC needs strategic maintenance?", ["Border Roads Organisation", "Central Industrial Security Force", "Indian Coast Guard", "National Security Guard"], "Border Roads Organisation", "combat_support"),
    q(2, "Which support role turns a damaged vehicle from a battlefield liability into a reusable asset?", ["Recovery and repair", "Ceremonial drill", "Naval boarding", "Air traffic control"], "Recovery and repair", "combat_support"),
    q(2, "Which Coast Guard mission protects the sea from oil spills and marine pollution?", ["Pollution response", "Tank gunnery", "Mountain warfare", "Airborne refuelling"], "Pollution response", "coast_guard_capf"),
    q(2, "Which Coast Guard mission involves boarding suspicious vessels for law-enforcement checks?", ["Maritime law enforcement", "Field artillery survey", "Air defence control", "Combat bridging"], "Maritime law enforcement", "coast_guard_capf"),
    q(2, "Which force is more suitable for airport perimeter security than border patrolling?", ["CISF", "BSF", "ITBP", "SSB"], "CISF", "coast_guard_capf"),
    q(2, "Which force is more associated with counter-insurgency and internal-security deployments than coastal rescue?", ["CRPF", "Indian Coast Guard", "Army Medical Corps", "Corps of Signals"], "CRPF", "coast_guard_capf"),
    q(2, "Which CAPF is most directly linked with the Indo-Nepal and Indo-Bhutan borders?", ["SSB", "ITBP", "BSF", "CISF"], "SSB", "coast_guard_capf"),
    q(2, "Which force would be the closest fit for guarding high-altitude Himalayan border posts?", ["ITBP", "CISF", "Indian Coast Guard", "Railway Protection Force"], "ITBP", "coast_guard_capf"),
    q(2, "Which force is sometimes called the Sentinels of the North East?", ["Assam Rifles", "CISF", "SSB", "Indian Coast Guard"], "Assam Rifles", "coast_guard_capf"),
    q(2, "Which term covers using the electromagnetic spectrum to detect, jam, or deceive an enemy?", ["Electronic warfare", "Mountain logistics", "Amphibious landing", "Battlefield medicine"], "Electronic warfare", "cyber_space_ew"),
    q(2, "What does ECM usually mean in air and electronic warfare?", ["Electronic countermeasures", "Engine control module only", "Emergency convoy movement", "External cargo module"], "Electronic countermeasures", "cyber_space_ew"),
    q(2, "What does ECCM mean in electronic warfare?", ["Electronic counter-countermeasures", "Emergency coastal combat mission", "Engine cooling control module", "Extended cargo carriage mode"], "Electronic counter-countermeasures", "cyber_space_ew"),
    q(2, "Which intelligence type is based on intercepted signals?", ["SIGINT", "HUMINT", "OSINT only", "Imagery briefing"], "SIGINT", "cyber_space_ew"),
    q(2, "Which intelligence type focuses specifically on communications?", ["COMINT", "ELINT", "MASINT", "GEOINT"], "COMINT", "cyber_space_ew"),
    q(2, "Which intelligence type focuses on electronic emissions such as radars?", ["ELINT", "COMINT", "HUMINT", "FININT"], "ELINT", "cyber_space_ew"),
    q(2, "Which action best describes jamming in electronic warfare?", ["Interfering with enemy signals", "Repairing tank tracks", "Building pontoon bridges", "Refuelling aircraft"], "Interfering with enemy signals", "cyber_space_ew"),
    q(2, "Which capability lets a force operate even when an enemy tries to jam its systems?", ["Anti-jam resilience", "Parade drill", "Deep-sea diving", "Cargo palletization"], "Anti-jam resilience", "cyber_space_ew"),
    q(2, "Which orbit is most commonly discussed for direct-ascent ASAT demonstrations?", ["Low Earth orbit", "Geostationary orbit only", "Lunar orbit", "Solar orbit"], "Low Earth orbit", "cyber_space_ew"),
    q(2, "Which Indian agency is paired most naturally with military cyber defence and cyber operations?", ["Defence Cyber Agency", "Defence Space Agency", "Indian Coast Guard", "Border Roads Organisation"], "Defence Cyber Agency", "cyber_space_ew"),
    q(2, "Which Indian agency is paired most naturally with military space situational awareness?", ["Defence Space Agency", "Defence Cyber Agency", "Army Service Corps", "Central Reserve Police Force"], "Defence Space Agency", "cyber_space_ew"),
    q(2, "Which phrase best captures credible minimum deterrence?", ["Keeping enough nuclear capability to deter attack", "Keeping the largest possible army", "Using aircraft only for transport", "Replacing all missiles with guns"], "Keeping enough nuclear capability to deter attack", "nuclear_doctrine"),
    q(2, "Which leg of a nuclear triad is hardest for an enemy to locate continuously?", ["Sea-based submarines", "Fixed parade grounds", "Open truck convoys", "Border check-posts"], "Sea-based submarines", "nuclear_doctrine"),
    q(2, "Which doctrine-level idea is No First Use meant to signal?", ["Nuclear restraint after a nuclear attack", "First use of artillery in every battle", "No use of aircraft before ships", "No deployment outside deserts"], "Nuclear restraint after a nuclear attack", "nuclear_doctrine"),
    q(2, "Why is survivability important for nuclear deterrence?", ["It makes retaliation credible", "It improves parade turnout", "It reduces bridge length", "It changes uniform colour"], "It makes retaliation credible", "nuclear_doctrine"),
    q(2, "Which organization handles India's strategic nuclear delivery forces?", ["Strategic Forces Command", "Army Training Command", "Southern Naval Command", "Border Roads Organisation"], "Strategic Forces Command", "nuclear_doctrine"),
    q(2, "Which company is the natural answer for Indian combat aircraft manufacturing?", ["HAL", "BDL", "MIDHANI", "AWEIL"], "HAL", "defense_industry"),
    q(2, "Which company is the natural answer for Akash and other missile production work?", ["BDL", "GRSE", "GSL", "AVNL"], "BDL", "defense_industry"),
    q(2, "Which company is the natural answer for Indian defence electronics?", ["BEL", "MDL", "HAL", "MIDHANI"], "BEL", "defense_industry"),
    q(2, "Which shipyard is most associated with Scorpene-class submarine construction in India?", ["Mazagon Dock Shipbuilders", "Garden Reach Shipbuilders", "Goa Shipyard", "Cochin Shipyard"], "Mazagon Dock Shipbuilders", "defense_industry"),
    q(2, "Which DPSU is known for specialist metals and alloys for strategic sectors?", ["MIDHANI", "BEL", "BDL", "GRSE"], "MIDHANI", "defense_industry"),
    q(2, "Which DPSU grouping is associated with armoured vehicles after ordnance-factory restructuring?", ["Armoured Vehicles Nigam Limited", "Bharat Electronics Limited", "Garden Reach Shipbuilders", "Mazagon Dock Shipbuilders"], "Armoured Vehicles Nigam Limited", "defense_industry"),
    q(2, "Which DPSU grouping is associated with artillery and small arms?", ["Advanced Weapons and Equipment India Limited", "Bharat Dynamics Limited", "Hindustan Aeronautics Limited", "Goa Shipyard Limited"], "Advanced Weapons and Equipment India Limited", "defense_industry"),

    q(3, "Which support arm would be central to creating a passage through an obstacle belt under fire?", ["Corps of Engineers", "Army Ordnance Corps", "Army Medical Corps", "Army Education Corps"], "Corps of Engineers", "combat_support"),
    q(3, "Which support arm would be central to secure command links between a brigade HQ and forward units?", ["Corps of Signals", "Army Service Corps", "Corps of EME", "Army Dental Corps"], "Corps of Signals", "combat_support"),
    q(3, "Which support arm would be central to battlefield recovery of an immobilized infantry combat vehicle?", ["Corps of EME", "Army Medical Corps", "Army Postal Service", "Remount Veterinary Corps"], "Corps of EME", "combat_support"),
    q(3, "Which logistics problem is usually the biggest risk during sustained high-altitude operations?", ["Keeping supplies moving forward", "Naming parade formations", "Choosing ceremonial music", "Painting aircraft markings"], "Keeping supplies moving forward", "combat_support"),
    q(3, "Which engineering capability lets troops cross a river before permanent bridges are available?", ["Pontoon bridging", "Aerial refuelling", "Sonar classification", "Runway arresting"], "Pontoon bridging", "combat_support"),
    q(3, "Which term best describes reducing an enemy obstacle so assault forces can pass?", ["Obstacle breaching", "Combat air patrol", "Convoy saluting", "Harbour dredging"], "Obstacle breaching", "combat_support"),
    q(3, "Which force is the better fit for coastal security coordination than land-border fence patrols?", ["Indian Coast Guard", "ITBP", "SSB", "CISF"], "Indian Coast Guard", "coast_guard_capf"),
    q(3, "Which force is the better fit for industrial-unit security than maritime search and rescue?", ["CISF", "Indian Coast Guard", "Assam Rifles", "Army Service Corps"], "CISF", "coast_guard_capf"),
    q(3, "Which force is the better fit for North-East counter-insurgency support than airport security?", ["Assam Rifles", "CISF", "Indian Coast Guard", "AWEIL"], "Assam Rifles", "coast_guard_capf"),
    q(3, "Which pairing is correct for CAPF border responsibilities?", ["SSB: Nepal and Bhutan", "CISF: Myanmar frontier", "Coast Guard: Rajasthan desert", "CRPF: exclusive economic zone"], "SSB: Nepal and Bhutan", "coast_guard_capf"),
    q(3, "Which capability is most useful against a radar-guided missile rather than an infrared missile?", ["Chaff", "Flares", "Combat boots", "Pontoon boats"], "Chaff", "cyber_space_ew"),
    q(3, "Which capability is most useful against a heat-seeking missile rather than a radar-guided missile?", ["Flares", "Chaff", "IFF code", "Sonobuoy pattern"], "Flares", "cyber_space_ew"),
    q(3, "Which EW concept means denying an enemy reliable use of its radios or radar?", ["Jamming", "Air dropping", "Mine ploughing", "Hull cleaning"], "Jamming", "cyber_space_ew"),
    q(3, "Which EW concept means protecting friendly systems from enemy jamming?", ["ECCM", "COMINT", "Airlift", "Ordnance stocking"], "ECCM", "cyber_space_ew"),
    q(3, "Which signal-intelligence branch is the better match for radar emissions?", ["ELINT", "COMINT", "HUMINT", "OSINT"], "ELINT", "cyber_space_ew"),
    q(3, "Which signal-intelligence branch is the better match for voice or data messages?", ["COMINT", "ELINT", "MASINT", "IMINT"], "COMINT", "cyber_space_ew"),
    q(3, "Which aircraft self-protection cue comes from detecting radar energy aimed at the aircraft?", ["Radar warning receiver alert", "Fuel-flow warning only", "Cabin altitude callout", "Landing gear horn"], "Radar warning receiver alert", "cyber_space_ew"),
    q(3, "Which Indian test is the standard reference point for proven ASAT capability?", ["Mission Shakti", "Operation Cactus", "Exercise Malabar", "Operation Pawan"], "Mission Shakti", "cyber_space_ew"),
    q(3, "Which domain does the Defence Space Agency primarily relate to?", ["Military use of space", "Ammunition depot management", "Coastal pollution response", "Infantry medical evacuation"], "Military use of space", "cyber_space_ew"),
    q(3, "Which tri-service body is the best fit for cyber warfare coordination?", ["Defence Cyber Agency", "Strategic Forces Command", "Army Service Corps", "Indian Coast Guard"], "Defence Cyber Agency", "cyber_space_ew"),
    q(3, "Which deterrence idea depends most on submarines being difficult to track?", ["Survivable second strike", "Close air support", "Convoy escort", "Minefield marking"], "Survivable second strike", "nuclear_doctrine"),
    q(3, "Which phrase best separates a nuclear triad from ordinary missile forces?", ["Delivery from land, air, and sea", "Only short-range battlefield rockets", "Only naval guns and torpedoes", "Only unarmed training aircraft"], "Delivery from land, air, and sea", "nuclear_doctrine"),
    q(3, "Which doctrine-level posture avoids threatening nuclear use at the start of a conflict?", ["No First Use", "First salvo doctrine", "Area bombing", "Forward artillery only"], "No First Use", "nuclear_doctrine"),
    q(3, "Which command name is most directly linked to India's strategic nuclear delivery forces?", ["Strategic Forces Command", "Integrated Training Command", "Army Service Corps", "Western Air Command"], "Strategic Forces Command", "nuclear_doctrine"),
    q(3, "Which term means keeping nuclear forces large enough for deterrence but not pursuing unlimited buildup?", ["Credible minimum deterrence", "Mass mobilization", "Forward defence only", "Total air superiority"], "Credible minimum deterrence", "nuclear_doctrine"),
    q(3, "In Indian defence manufacturing, BEL is best linked with what work?", ["Defence electronics", "Aircraft final assembly", "Submarine hull building", "Border-police deployment"], "Defence electronics", "defense_industry"),
    q(3, "For missile-system production, which Indian DPSU is the strongest match?", ["BDL", "GRSE", "MIDHANI", "CISF"], "BDL", "defense_industry"),
    q(3, "Which DPSU is most closely tied to Indian aircraft and helicopter production?", ["HAL", "BEL", "MDL", "SSB"], "HAL", "defense_industry"),
    q(3, "Which Indian shipyard pairing is the strongest fit?", ["MDL: Mumbai warship and submarine yard", "GSL: aircraft engine maker", "GRSE: missile-only factory", "HAL: coastal patrol police"], "MDL: Mumbai warship and submarine yard", "defense_industry"),
    q(3, "Which DPSU is most associated with special metals for aerospace, defence, and nuclear sectors?", ["MIDHANI", "CISF", "SSB", "Army Medical Corps"], "MIDHANI", "defense_industry"),
]


def assign_ids(questions: list[dict], existing: list[dict]) -> list[dict]:
    max_by_diff = {1: 0, 2: 0, 3: 0}
    for item in existing:
        if item.get("category") != "defense":
            continue
        diff = item.get("difficulty")
        try:
            seq = int(str(item["id"]).rsplit("_", 1)[-1])
        except (KeyError, ValueError):
            continue
        max_by_diff[diff] = max(max_by_diff.get(diff, 0), seq)

    labels = {1: "easy", 2: "medium", 3: "hard"}
    output = []
    for item in questions:
        diff = item["difficulty"]
        max_by_diff[diff] += 1
        output.append({"id": f"def_{labels[diff]}_{max_by_diff[diff]:03d}", **item})
    return output


def validate(questions: list[dict], existing: list[dict]) -> None:
    ids = [item["id"] for item in questions]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate generated IDs")
    existing_ids = {item["id"] for item in existing}
    collisions = sorted(existing_ids.intersection(ids))
    if collisions:
        raise ValueError(f"ID collisions: {collisions[:5]}")
    for item in questions:
        if set(["id", "category", "difficulty", "question", "options", "correct_index"]) - item.keys():
            raise ValueError(f"Missing field in {item}")
        if item["category"] != "defense":
            raise ValueError(f"Wrong category in {item['id']}")
        if item["difficulty"] not in {1, 2, 3}:
            raise ValueError(f"Wrong difficulty in {item['id']}")
        if len(item["options"]) != 4:
            raise ValueError(f"Wrong option count in {item['id']}")
        if not 0 <= item["correct_index"] < 4:
            raise ValueError(f"Wrong correct_index in {item['id']}")
        if item["options"][item["correct_index"]] not in item["options"]:
            raise ValueError(f"Correct option mismatch in {item['id']}")


def main() -> None:
    existing = json.loads(BANK_PATH.read_text())
    wanted_texts = {item["question"] for item in QUESTIONS}
    existing_texts = {item.get("question") for item in existing}
    pending = [item for item in QUESTIONS if item["question"] not in existing_texts]

    if not pending:
        already_present = [item for item in existing if item.get("question") in wanted_texts]
        OUT_PATH.write_text(json.dumps(already_present, indent=2) + "\n")
        print(f"generated=0 already_present={len(already_present)} total={len(existing)} out={OUT_PATH}")
        return

    generated = assign_ids(pending, existing)
    validate(generated, existing)

    OUT_PATH.write_text(json.dumps(generated, indent=2) + "\n")

    updated = existing + generated
    validate(generated, existing)
    BANK_PATH.write_text(json.dumps(updated, indent=2) + "\n")
    print(f"generated={len(generated)} total={len(updated)} out={OUT_PATH}")


if __name__ == "__main__":
    main()
