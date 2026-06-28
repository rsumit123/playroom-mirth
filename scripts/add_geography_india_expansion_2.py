#!/usr/bin/env python3
"""Generate and merge a second India-focused geography trivia batch."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from add_geography_india_expansion import STATES, RIVERS, assign_ids, question, validate


ROOT = Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "backend" / "app" / "data" / "gk_questions.json"
OUT_PATH = ROOT / "backend" / "app" / "data" / "geography_india_expansion_2_generated_113.json"


COUNTRIES = [
    "Pakistan", "China", "Nepal", "Bhutan", "Bangladesh", "Myanmar",
    "Sri Lanka", "Maldives", "Afghanistan", "Indonesia",
]

REGIONS = [
    "Konkan", "Malabar", "Coromandel", "Saurashtra", "Kutch", "Bundelkhand",
    "Baghelkhand", "Marwar", "Mewar", "Malwa", "Doab", "Terai", "Bhabar",
    "Vidarbha", "Marathwada", "Rayalaseema", "Telangana Plateau", "Bastar",
    "Chota Nagpur", "Rohilkhand", "Awadh", "Ladakh", "Kumaon", "Garhwal",
]

FEATURES = [
    "Rann of Kutch", "Sundarbans", "Chilika Lake", "Loktak Lake", "Wular Lake",
    "Sambhar Lake", "Lonar Lake", "Pulicat Lake", "Vembanad Lake", "Kolleru Lake",
    "Majuli", "Diu", "Minicoy", "Barren Island", "Pamban Island",
]


FACTS: list[tuple[int, str, str, list[str], str]] = [
    (1, "Ziro Valley is a well-known valley in which state?", "Arunachal Pradesh", STATES, "state_features"),
    (1, "Majuli river island is in which state?", "Assam", STATES, "state_features"),
    (1, "Mawsynram is located in which state?", "Meghalaya", STATES, "state_features"),
    (1, "Loktak Lake is a major lake in which state?", "Manipur", STATES, "state_features"),
    (1, "Dampa Tiger Reserve is in which state?", "Mizoram", STATES, "state_features"),
    (1, "Unakoti hills are in which state?", "Tripura", STATES, "state_features"),
    (1, "Dholavira is located in which state?", "Gujarat", STATES, "state_features"),
    (1, "Lonar crater lake is in which state?", "Maharashtra", STATES, "state_features"),
    (1, "The Nilgiri Hills are strongly associated with which state?", "Tamil Nadu", STATES, "state_features"),
    (1, "The Sundarbans delta is mainly associated with which Indian state?", "West Bengal", STATES, "state_features"),
    (1, "The Bastar region is in which state?", "Chhattisgarh", STATES, "state_features"),
    (1, "The Chota Nagpur Plateau is strongly associated with which state?", "Jharkhand", STATES, "state_features"),
    (1, "The Malwa region is mainly associated with which state?", "Madhya Pradesh", STATES, "state_features"),
    (1, "The Konkan region is strongly associated with which state?", "Maharashtra", STATES, "state_features"),
    (1, "The Malabar coast is strongly associated with which state?", "Kerala", STATES, "state_features"),
    (1, "The Coromandel coast is strongly associated with which state?", "Tamil Nadu", STATES, "state_features"),
    (1, "The Saurashtra peninsula is in which state?", "Gujarat", STATES, "state_features"),
    (1, "The Marwar region is in which state?", "Rajasthan", STATES, "state_features"),
    (1, "The Garhwal region is in which state?", "Uttarakhand", STATES, "state_features"),
    (1, "The Kumaon region is in which state?", "Uttarakhand", STATES, "state_features"),
    (1, "The Doab region lies between which two rivers?", "Ganga and Yamuna", ["Ganga and Yamuna", "Krishna and Kaveri", "Narmada and Tapi", "Brahmaputra and Teesta"], "regions"),
    (1, "Which river pair is associated with Punjab's name meaning land of five rivers?", "Indus tributaries", ["Indus tributaries", "Godavari tributaries", "Kaveri tributaries", "Mahanadi tributaries"], "regions"),
    (1, "Which state has the Koyna hydroelectric project?", "Maharashtra", STATES, "hydropower"),
    (1, "Which state has the Sharavathi river and Jog Falls?", "Karnataka", STATES, "waterfalls"),
    (1, "Which state has the Dudhsagar waterfall near Goa?", "Goa", STATES, "waterfalls"),
    (1, "Which state has the Athirappilly waterfall?", "Kerala", STATES, "waterfalls"),
    (1, "Which state has the Chitrakote waterfall?", "Chhattisgarh", STATES, "waterfalls"),
    (1, "Which state has the Nohkalikai waterfall?", "Meghalaya", STATES, "waterfalls"),
    (1, "Which state has the Hundru Falls near Ranchi?", "Jharkhand", STATES, "waterfalls"),
    (1, "Which state has Hogenakkal Falls on the Kaveri?", "Tamil Nadu", STATES, "waterfalls"),
    (1, "Which state is crossed by the Tropic of Cancer and has Bhopal?", "Madhya Pradesh", STATES, "location_lines"),
    (1, "Which state is crossed by the Tropic of Cancer and has Aizawl?", "Mizoram", STATES, "location_lines"),
    (1, "Which state is crossed by the Tropic of Cancer and has Ranchi?", "Jharkhand", STATES, "location_lines"),
    (1, "Which state is crossed by the Tropic of Cancer and has Gandhinagar?", "Gujarat", STATES, "location_lines"),
    (1, "Which state is crossed by the Tropic of Cancer and has Agartala?", "Tripura", STATES, "location_lines"),
    (1, "Which country lies across the Palk Strait from Tamil Nadu?", "Sri Lanka", COUNTRIES, "maritime_borders"),
    (1, "Which country borders Arunachal Pradesh to the north?", "China", COUNTRIES, "land_borders"),
    (1, "Which country borders Sikkim to the east?", "Bhutan", COUNTRIES, "land_borders"),
    (1, "Which country borders Mizoram to the east?", "Myanmar", COUNTRIES, "land_borders"),
    (1, "Which country borders Punjab to the west?", "Pakistan", COUNTRIES, "land_borders"),
    (1, "Which country borders Bihar to the north?", "Nepal", COUNTRIES, "land_borders"),
    (2, "The Barak Valley is mainly in which state?", "Assam", STATES, "regional_geography"),
    (2, "The Brahmaputra Valley is mainly associated with which state?", "Assam", STATES, "regional_geography"),
    (2, "The Kathiawar peninsula is another name linked with which region?", "Saurashtra", REGIONS, "regional_geography"),
    (2, "The Baghelkhand region is mainly associated with which state?", "Madhya Pradesh", STATES, "regional_geography"),
    (2, "The Bundelkhand region is shared mainly by Uttar Pradesh and which state?", "Madhya Pradesh", STATES, "regional_geography"),
    (2, "The Vidarbha region is in which state?", "Maharashtra", STATES, "regional_geography"),
    (2, "The Marathwada region is in which state?", "Maharashtra", STATES, "regional_geography"),
    (2, "The Rayalaseema region is in which state?", "Andhra Pradesh", STATES, "regional_geography"),
    (2, "The Telangana Plateau is mainly in which state?", "Telangana", STATES, "regional_geography"),
    (2, "The Rohilkhand region is in which state?", "Uttar Pradesh", STATES, "regional_geography"),
    (2, "The Awadh region is in which state?", "Uttar Pradesh", STATES, "regional_geography"),
    (2, "The Kuttanad lowland is in which state?", "Kerala", STATES, "regional_geography"),
    (2, "The Sunderbans are shared by India and which country?", "Bangladesh", COUNTRIES, "international_geography"),
    (2, "The Ganga-Brahmaputra delta is mainly shared by India and which country?", "Bangladesh", COUNTRIES, "international_geography"),
    (2, "The Indus river system enters the Arabian Sea mainly through which country?", "Pakistan", COUNTRIES, "international_geography"),
    (2, "The Brahmaputra is called Yarlung Tsangpo before entering India from which country?", "China", COUNTRIES, "international_geography"),
    (2, "The Teesta river dispute is mainly between India and which country?", "Bangladesh", COUNTRIES, "international_geography"),
    (2, "The Kaladan project links India's northeast with which country?", "Myanmar", COUNTRIES, "international_geography"),
    (2, "The Siliguri Corridor lies in which state?", "West Bengal", STATES, "strategic_geography"),
    (2, "The Chicken's Neck corridor connects mainland India to which region?", "North East India", ["North East India", "Konkan", "Malwa", "Kutch"], "strategic_geography"),
    (2, "The Nathula trade route links Sikkim with which country?", "China", COUNTRIES, "strategic_geography"),
    (2, "The Attari-Wagah border is between India and which country?", "Pakistan", COUNTRIES, "strategic_geography"),
    (2, "The Moreh border town links Manipur with which country?", "Myanmar", COUNTRIES, "strategic_geography"),
    (2, "Petrapole-Benapole is a major land port between India and which country?", "Bangladesh", COUNTRIES, "strategic_geography"),
    (2, "The Khyber Pass is historically linked with access to the subcontinent through which neighbour?", "Pakistan", COUNTRIES, "strategic_geography"),
    (2, "The Ganga Canal system is mainly associated with which region?", "Doab", REGIONS, "irrigation"),
    (2, "The Indira Gandhi Canal is mainly associated with which state?", "Rajasthan", STATES, "irrigation"),
    (2, "The Srisailam project is on which river?", "Krishna", RIVERS, "hydropower"),
    (2, "The Koyna project is on which river?", "Koyna", ["Koyna", "Krishna", "Godavari", "Tapi"], "hydropower"),
    (2, "The Farakka Barrage is on which river?", "Ganga", RIVERS, "water_infrastructure"),
    (2, "The Prakasam Barrage is on which river?", "Krishna", RIVERS, "water_infrastructure"),
    (2, "The Dowleswaram Barrage is on which river?", "Godavari", RIVERS, "water_infrastructure"),
    (2, "The Kota Barrage is on which river?", "Chambal", RIVERS, "water_infrastructure"),
    (2, "The Rihand Dam is associated with which river?", "Rihand", ["Rihand", "Son", "Betwa", "Damodar"], "water_infrastructure"),
    (2, "The Banas is a tributary of which river?", "Chambal", RIVERS, "tributaries"),
    (2, "The Ken is a tributary of which river?", "Yamuna", RIVERS, "tributaries"),
    (2, "The Damanganga river drains into which sea?", "Arabian Sea", ["Arabian Sea", "Bay of Bengal", "Andaman Sea", "Laccadive Sea"], "river_systems"),
    (2, "Most east-flowing peninsular rivers drain into which bay?", "Bay of Bengal", ["Bay of Bengal", "Arabian Sea", "Gulf of Kutch", "Gulf of Mannar"], "river_systems"),
    (2, "The Narmada and Tapi are notable because they mainly flow toward which sea?", "Arabian Sea", ["Arabian Sea", "Bay of Bengal", "Andaman Sea", "Red Sea"], "river_systems"),
    (2, "The Mahanadi delta is mainly in which state?", "Odisha", STATES, "deltas"),
    (2, "The Godavari delta is mainly in which state?", "Andhra Pradesh", STATES, "deltas"),
    (2, "The Kaveri delta is mainly associated with which state?", "Tamil Nadu", STATES, "deltas"),
    (2, "The Krishna delta is mainly associated with which state?", "Andhra Pradesh", STATES, "deltas"),
    (3, "The Narmada rift valley lies between the Vindhya range and which range?", "Satpura Range", ["Satpura Range", "Aravalli Range", "Karakoram Range", "Patkai Hills"], "geomorphology"),
    (3, "The Tapi valley lies south of which major range?", "Satpura Range", ["Satpura Range", "Pir Panjal Range", "Shivalik Hills", "Garo Hills"], "geomorphology"),
    (3, "The Rajmahal Hills are in which state?", "Jharkhand", STATES, "geomorphology"),
    (3, "The Anaimalai Hills are mainly in Kerala and which state?", "Tamil Nadu", STATES, "geomorphology"),
    (3, "The Cardamom Hills are mainly associated with which state?", "Kerala", STATES, "geomorphology"),
    (3, "The Baba Budan Hills are in which state?", "Karnataka", STATES, "geomorphology"),
    (3, "The Shevaroy Hills are in which state?", "Tamil Nadu", STATES, "geomorphology"),
    (3, "The Javadi Hills are in which state?", "Tamil Nadu", STATES, "geomorphology"),
    (3, "The Nallamala Hills are mainly associated with which state?", "Andhra Pradesh", STATES, "geomorphology"),
    (3, "The Mahadeo Hills are mainly in which state?", "Madhya Pradesh", STATES, "geomorphology"),
    (3, "The Maikal Range is near the source area of which river?", "Narmada", RIVERS, "geomorphology"),
    (3, "The Bhor Ghat connects Mumbai with which city region?", "Pune", ["Pune", "Nashik", "Nagpur", "Surat"], "mountain_passes"),
    (3, "The Thal Ghat connects Mumbai with which city region?", "Nashik", ["Nashik", "Pune", "Indore", "Bhopal"], "mountain_passes"),
    (3, "The Palghat Gap lies between the Nilgiri Hills and which hills?", "Anaimalai Hills", ["Anaimalai Hills", "Aravalli Range", "Patkai Hills", "Zanskar Range"], "mountain_passes"),
    (3, "The Diphu Pass area is linked with India's border near which country?", "Myanmar", COUNTRIES, "mountain_passes"),
    (3, "The Zoji La route connects Srinagar with which region?", "Ladakh", REGIONS, "mountain_passes"),
    (3, "The Mana Pass is associated with which state?", "Uttarakhand", STATES, "mountain_passes"),
    (3, "The Lipulekh Pass is associated with which state?", "Uttarakhand", STATES, "mountain_passes"),
    (3, "The Jelep La pass is associated with which state?", "Sikkim", STATES, "mountain_passes"),
    (3, "The Banihal Pass is associated with which region?", "Jammu and Kashmir", ["Jammu and Kashmir", "Sikkim", "Kerala", "Rajasthan"], "mountain_passes"),
    (3, "The Gulf of Mannar lies between India and which country?", "Sri Lanka", COUNTRIES, "maritime_geography"),
    (3, "The Duncan Passage separates South Andaman from which island?", "Little Andaman", ["Little Andaman", "Minicoy", "Majuli", "Diu"], "maritime_geography"),
    (3, "The Coco Channel lies north of which Indian island group?", "Andaman Islands", ["Andaman Islands", "Lakshadweep", "Sagar Island", "Pamban Island"], "maritime_geography"),
    (3, "The Lakshadweep Sea is also commonly called which sea?", "Laccadive Sea", ["Laccadive Sea", "Andaman Sea", "Red Sea", "Caspian Sea"], "maritime_geography"),
    (3, "The Pamban Bridge connects mainland India with which island?", "Pamban Island", FEATURES, "maritime_geography"),
    (3, "The Wheeler Island/Abdul Kalam Island is off the coast of which state?", "Odisha", STATES, "islands"),
    (3, "Sagar Island is in which state?", "West Bengal", STATES, "islands"),
    (3, "Umananda Island is in which river?", "Brahmaputra", RIVERS, "islands"),
    (3, "Divar Island is in which state?", "Goa", STATES, "islands"),
    (3, "The Salsette Island region is associated with which city?", "Mumbai", ["Mumbai", "Kolkata", "Chennai", "Kochi"], "islands"),
    (3, "The Karaikal coast is part of which Union Territory?", "Puducherry", ["Puducherry", "Lakshadweep", "Delhi", "Chandigarh"], "coasts"),
    (3, "Yanam is an enclave of Puducherry in which state?", "Andhra Pradesh", STATES, "coasts"),
    (3, "Mahe is an enclave of Puducherry within which state?", "Kerala", STATES, "coasts"),
    (3, "Diu lies off the coast of which state?", "Gujarat", STATES, "coasts"),
    (3, "Daman lies on India's west coast adjoining which state?", "Gujarat", STATES, "coasts"),
    (3, "The Sundarbans are formed mainly by which river system?", "Ganga-Brahmaputra-Meghna", ["Ganga-Brahmaputra-Meghna", "Godavari-Krishna", "Narmada-Tapi", "Indus-Jhelum"], "deltas"),
    (3, "The Kori Creek is associated with which region?", "Rann of Kutch", FEATURES, "creeks"),
    (3, "Sir Creek lies near India's border with which country?", "Pakistan", COUNTRIES, "creeks"),
    (3, "The Hooghly is a distributary of which river?", "Ganga", RIVERS, "distributaries"),
    (3, "The Bhagirathi-Hooghly river system is most associated with which state?", "West Bengal", STATES, "distributaries"),
    (3, "The Barak river eventually contributes to which river system?", "Meghna", ["Meghna", "Indus", "Narmada", "Tapi"], "river_systems"),
]


def main() -> None:
    existing = json.loads(BANK_PATH.read_text())
    generated = [
        question(difficulty, text, correct, pool, note, i + difficulty * 2000)
        for i, (difficulty, text, correct, pool, note) in enumerate(FACTS, 1)
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
