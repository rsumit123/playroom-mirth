#!/usr/bin/env python3
"""Generate and merge an India-focused geography trivia expansion."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "backend" / "app" / "data" / "gk_questions.json"
OUT_PATH = ROOT / "backend" / "app" / "data" / "geography_india_expansion_generated_136.json"


DIFF_LABEL = {1: "easy", 2: "medium", 3: "hard"}


def make_options(correct: str, pool: list[str], seed: int) -> tuple[list[str], int]:
    wrongs = [x for x in pool if x != correct]
    if len(wrongs) < 3:
        raise ValueError(f"Need at least 3 distractors for {correct!r}: {pool!r}")
    picks: list[str] = []
    i = seed % max(1, len(wrongs))
    while len(picks) < 3:
        candidate = wrongs[i % len(wrongs)]
        if candidate not in picks:
            picks.append(candidate)
        i += 1
    options = picks[:]
    idx = seed % 4
    options.insert(idx, correct)
    return options, idx


def question(
    difficulty: int,
    text: str,
    correct: str,
    pool: list[str],
    source_note: str,
    seed: int,
) -> dict:
    options, correct_index = make_options(correct, pool, seed)
    return {
        "category": "geography",
        "difficulty": difficulty,
        "question": text,
        "options": options,
        "correct_index": correct_index,
        "source_note": source_note,
    }


STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan",
    "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
    "Uttarakhand", "West Bengal",
]

RIVERS = [
    "Ganga", "Yamuna", "Brahmaputra", "Godavari", "Krishna", "Narmada",
    "Tapi", "Mahanadi", "Kaveri", "Sabarmati", "Luni", "Teesta",
    "Sutlej", "Beas", "Ravi", "Chenab", "Jhelum", "Periyar", "Subarnarekha",
    "Damodar", "Brahmani", "Indravati", "Chambal", "Betwa", "Son", "Kosi",
    "Gandak", "Ghaghara", "Tungabhadra", "Bhagirathi",
]

EASY_FACTS = [
    ("Which state has Dispur as its capital?", "Assam", STATES, "states_capitals"),
    ("Which state has Itanagar as its capital?", "Arunachal Pradesh", STATES, "states_capitals"),
    ("Which state has Gandhinagar as its capital?", "Gujarat", STATES, "states_capitals"),
    ("Which state has Dehradun as its capital?", "Uttarakhand", STATES, "states_capitals"),
    ("Which state has Ranchi as its capital?", "Jharkhand", STATES, "states_capitals"),
    ("Which state has Raipur as its capital?", "Chhattisgarh", STATES, "states_capitals"),
    ("Which state has Agartala as its capital?", "Tripura", STATES, "states_capitals"),
    ("Which state has Aizawl as its capital?", "Mizoram", STATES, "states_capitals"),
    ("Which state has Kohima as its capital?", "Nagaland", STATES, "states_capitals"),
    ("Which state has Imphal as its capital?", "Manipur", STATES, "states_capitals"),
    ("Which state has Shillong as its capital?", "Meghalaya", STATES, "states_capitals"),
    ("Which state has Gangtok as its capital?", "Sikkim", STATES, "states_capitals"),
    ("Which state has Bhubaneswar as its capital?", "Odisha", STATES, "states_capitals"),
    ("Which state has Thiruvananthapuram as its capital?", "Kerala", STATES, "states_capitals"),
    ("Which state has Amaravati as its legislative capital?", "Andhra Pradesh", STATES, "states_capitals"),
    ("Gir National Park is in which state?", "Gujarat", STATES, "protected_areas"),
    ("Kaziranga National Park is in which state?", "Assam", STATES, "protected_areas"),
    ("Ranthambore National Park is in which state?", "Rajasthan", STATES, "protected_areas"),
    ("Bandipur National Park is in which state?", "Karnataka", STATES, "protected_areas"),
    ("Periyar Tiger Reserve is in which state?", "Kerala", STATES, "protected_areas"),
    ("Kanha National Park is in which state?", "Madhya Pradesh", STATES, "protected_areas"),
    ("Similipal National Park is in which state?", "Odisha", STATES, "protected_areas"),
    ("Sundarbans National Park is in which state?", "West Bengal", STATES, "protected_areas"),
    ("Jim Corbett National Park is in which state?", "Uttarakhand", STATES, "protected_areas"),
    ("Dudhwa National Park is in which state?", "Uttar Pradesh", STATES, "protected_areas"),
    ("Keoladeo National Park is in which state?", "Rajasthan", STATES, "protected_areas"),
    ("Valley of Flowers National Park is in which state?", "Uttarakhand", STATES, "protected_areas"),
    ("Namdapha National Park is in which state?", "Arunachal Pradesh", STATES, "protected_areas"),
    ("Silent Valley National Park is in which state?", "Kerala", STATES, "protected_areas"),
    ("Tadoba-Andhari Tiger Reserve is in which state?", "Maharashtra", STATES, "protected_areas"),
    ("Ahmedabad is located on which river?", "Sabarmati", RIVERS, "rivers_cities"),
    ("Varanasi is located on which river?", "Ganga", RIVERS, "rivers_cities"),
    ("Delhi is located on which river?", "Yamuna", RIVERS, "rivers_cities"),
    ("Guwahati is located on which river?", "Brahmaputra", RIVERS, "rivers_cities"),
    ("Cuttack is located near the delta of which river system?", "Mahanadi", RIVERS, "rivers_cities"),
    ("Vijayawada is located on which river?", "Krishna", RIVERS, "rivers_cities"),
    ("Nashik is located on which major river?", "Godavari", RIVERS, "rivers_cities"),
    ("Jabalpur is associated with marble rocks along which river?", "Narmada", RIVERS, "rivers_cities"),
    ("Surat lies near the mouth of which river?", "Tapi", RIVERS, "rivers_cities"),
    ("Tiruchirappalli is located on which river?", "Kaveri", RIVERS, "rivers_cities"),
    ("Which coast is Mumbai located on?", "Konkan Coast", ["Konkan Coast", "Coromandel Coast", "Malabar Coast", "Utkal Coast"], "coasts"),
    ("Which coast is Chennai located on?", "Coromandel Coast", ["Coromandel Coast", "Konkan Coast", "Malabar Coast", "Kannada Coast"], "coasts"),
    ("Which coast is Kochi associated with?", "Malabar Coast", ["Malabar Coast", "Konkan Coast", "Coromandel Coast", "Utkal Coast"], "coasts"),
    ("Which Indian state has the Thar Desert?", "Rajasthan", STATES, "physical_regions"),
    ("Which plateau covers much of peninsular India?", "Deccan Plateau", ["Deccan Plateau", "Chota Nagpur Plateau", "Malwa Plateau", "Shillong Plateau"], "physical_regions"),
    ("Which island group lies in the Bay of Bengal?", "Andaman and Nicobar Islands", ["Andaman and Nicobar Islands", "Lakshadweep", "Diu", "Minicoy only"], "islands"),
    ("Which island group lies in the Arabian Sea?", "Lakshadweep", ["Lakshadweep", "Andaman and Nicobar Islands", "Majuli", "Sagar Island"], "islands"),
    ("Which state shares a long border with Pakistan and has the Thar Desert?", "Rajasthan", STATES, "borders"),
    ("Which Indian state borders Bangladesh on three sides?", "Tripura", STATES, "borders"),
    ("Which Indian state connects mainland India to the North East through the Siliguri corridor?", "West Bengal", STATES, "borders"),
    ("Which Himalayan state borders Nepal, Bhutan and China?", "Sikkim", STATES, "borders"),
    ("Which state is famous for the backwaters around Alappuzha?", "Kerala", STATES, "water_bodies"),
    ("Which river is central to the Sundarbans delta?", "Ganga", RIVERS, "deltas"),
    ("Which river forms the famous Majuli river island area?", "Brahmaputra", RIVERS, "river_islands"),
    ("Which Indian state is known for the Rann of Kutch?", "Gujarat", STATES, "physical_regions"),
    ("Which state has the Chilika lagoon?", "Odisha", STATES, "wetlands"),
    ("Which state has Loktak Lake?", "Manipur", STATES, "wetlands"),
    ("Which Union Territory has Wular Lake?", "Jammu and Kashmir", ["Jammu and Kashmir", "Himachal Pradesh", "Uttarakhand", "Sikkim"], "wetlands"),
    ("Which state has Sambhar Salt Lake?", "Rajasthan", STATES, "wetlands"),
    ("Which state has Pulicat Lake along its coast?", "Andhra Pradesh", STATES, "wetlands"),
]


MEDIUM_FACTS = [
    ("Tehri Dam is built on which river?", "Bhagirathi", RIVERS, "dams_rivers"),
    ("Hirakud Dam is built on which river?", "Mahanadi", RIVERS, "dams_rivers"),
    ("Sardar Sarovar Dam is built on which river?", "Narmada", RIVERS, "dams_rivers"),
    ("Bhakra Dam is built on which river?", "Sutlej", RIVERS, "dams_rivers"),
    ("Nagarjuna Sagar Dam is built on which river?", "Krishna", RIVERS, "dams_rivers"),
    ("Tungabhadra Dam is built on which river?", "Tungabhadra", RIVERS, "dams_rivers"),
    ("Ukai Dam is built on which river?", "Tapi", RIVERS, "dams_rivers"),
    ("Idukki Dam is built across which river system?", "Periyar", RIVERS, "dams_rivers"),
    ("Rana Pratap Sagar Dam is built on which river?", "Chambal", RIVERS, "dams_rivers"),
    ("Maithon Dam is associated with which river system?", "Damodar", RIVERS, "dams_rivers"),
    ("The Beas is a tributary of which river system?", "Indus", ["Indus", "Ganga", "Godavari", "Mahanadi"], "tributaries"),
    ("The Yamuna is the largest tributary of which river?", "Ganga", RIVERS, "tributaries"),
    ("The Chambal is a tributary of which river?", "Yamuna", RIVERS, "tributaries"),
    ("The Betwa is a tributary of which river?", "Yamuna", RIVERS, "tributaries"),
    ("The Son is a tributary of which river?", "Ganga", RIVERS, "tributaries"),
    ("The Kosi is a tributary of which river?", "Ganga", RIVERS, "tributaries"),
    ("The Teesta ultimately joins which major river system?", "Brahmaputra", RIVERS, "tributaries"),
    ("The Indravati is a major tributary of which river?", "Godavari", RIVERS, "tributaries"),
    ("The Tungabhadra is a tributary of which river?", "Krishna", RIVERS, "tributaries"),
    ("The Bhima is a major tributary of which river?", "Krishna", RIVERS, "tributaries"),
    ("Rohtang Pass is in which state?", "Himachal Pradesh", STATES, "mountain_passes"),
    ("Nathu La pass is in which state?", "Sikkim", STATES, "mountain_passes"),
    ("Zoji La connects Kashmir Valley with which region?", "Ladakh", ["Ladakh", "Kumaon", "Sikkim", "Arunachal Pradesh"], "mountain_passes"),
    ("Shipki La is associated with which state?", "Himachal Pradesh", STATES, "mountain_passes"),
    ("Bomdila pass is associated with which state?", "Arunachal Pradesh", STATES, "mountain_passes"),
    ("Palghat Gap connects Kerala with which neighbouring state?", "Tamil Nadu", STATES, "mountain_passes"),
    ("Thal Ghat links Mumbai with which plateau region?", "Deccan Plateau", ["Deccan Plateau", "Malwa Plateau", "Shillong Plateau", "Ladakh Plateau"], "mountain_passes"),
    ("Bhor Ghat links Mumbai with which plateau region?", "Deccan Plateau", ["Deccan Plateau", "Chota Nagpur Plateau", "Tibetan Plateau", "Bundelkhand Plateau"], "mountain_passes"),
    ("Black soil is most closely associated with which crop?", "Cotton", ["Cotton", "Tea", "Jute", "Rubber"], "soils_crops"),
    ("Alluvial soil is most widespread in which Indian plain?", "Northern Plains", ["Northern Plains", "Ladakh Plateau", "Thar Desert", "Western Ghats"], "soils_crops"),
    ("Laterite soil is common in which kind of Indian region?", "High rainfall plateau region", ["High rainfall plateau region", "Cold desert region", "Glacial valley region", "Dry salt marsh region"], "soils_crops"),
    ("Red soil gets its colour mainly from which mineral compound?", "Iron oxide", ["Iron oxide", "Calcium carbonate", "Sodium chloride", "Potassium nitrate"], "soils_crops"),
    ("Tea plantations in India are strongly associated with which type of terrain?", "Humid hill slopes", ["Humid hill slopes", "Cold desert plains", "Dry salt flats", "River deltas only"], "soils_crops"),
    ("Jute cultivation in India is most associated with which deltaic region?", "Ganga-Brahmaputra delta", ["Ganga-Brahmaputra delta", "Narmada valley", "Thar basin", "Kaveri uplands"], "soils_crops"),
    ("The Chota Nagpur Plateau is especially known for which resource?", "Minerals", ["Minerals", "Coral reefs", "Cold deserts", "Mangrove islands"], "resources"),
    ("Jharia in Jharkhand is best known for which mineral resource?", "Coal", ["Coal", "Bauxite", "Mica", "Copper"], "resources"),
    ("Kolar in Karnataka is historically linked with which mineral?", "Gold", ["Gold", "Coal", "Limestone", "Gypsum"], "resources"),
    ("Singhbhum is well known for which mineral belt?", "Copper", ["Copper", "Coal", "Petroleum", "Salt"], "resources"),
    ("Koraput-Kalahandi belt is associated with which mineral?", "Bauxite", ["Bauxite", "Coal", "Mica", "Gold"], "resources"),
    ("Mumbai Port is on which coast?", "Western coast", ["Western coast", "Eastern coast", "Northern coast", "Island-only coast"], "ports"),
    ("Chennai Port is on which coast?", "Eastern coast", ["Eastern coast", "Western coast", "Gulf of Kutch coast", "Island-only coast"], "ports"),
    ("Paradip Port is in which state?", "Odisha", STATES, "ports"),
    ("Kandla, now Deendayal Port, is in which state?", "Gujarat", STATES, "ports"),
    ("Mormugao Port is in which state?", "Goa", STATES, "ports"),
    ("New Mangalore Port is in which state?", "Karnataka", STATES, "ports"),
    ("Tuticorin, or V.O. Chidambaranar Port, is in which state?", "Tamil Nadu", STATES, "ports"),
    ("Kolkata Port is located on which river?", "Hooghly", ["Hooghly", "Mahanadi", "Godavari", "Krishna"], "ports"),
    ("The Western Ghats are closer to which coast?", "Arabian Sea coast", ["Arabian Sea coast", "Bay of Bengal coast", "Rann of Kutch coast", "Sundarbans coast"], "physical_regions"),
    ("The Eastern Ghats are discontinuous mainly because they are cut by what?", "Rivers", ["Rivers", "Glaciers", "Volcanoes", "Coral reefs"], "physical_regions"),
    ("The Aravalli Range runs mainly through which state?", "Rajasthan", STATES, "physical_regions"),
    ("The Nilgiri Hills are near the meeting of which two Ghats?", "Western and Eastern Ghats", ["Western and Eastern Ghats", "Himalaya and Aravalli", "Vindhya and Satpura", "Karakoram and Zanskar"], "physical_regions"),
    ("The Satpura Range lies mainly between which two rivers?", "Narmada and Tapi", ["Narmada and Tapi", "Ganga and Yamuna", "Krishna and Kaveri", "Brahmaputra and Teesta"], "physical_regions"),
    ("The Vindhya Range is usually treated as a boundary between North India and which region?", "Deccan region", ["Deccan region", "Trans-Himalaya", "Sundarbans", "Rann of Kutch"], "physical_regions"),
]


HARD_FACTS = [
    ("Nokrek Biosphere Reserve is in which state?", "Meghalaya", STATES, "biosphere_reserves"),
    ("Dibru-Saikhowa Biosphere Reserve is in which state?", "Assam", STATES, "biosphere_reserves"),
    ("Pachmarhi Biosphere Reserve is in which state?", "Madhya Pradesh", STATES, "biosphere_reserves"),
    ("Achanakmar-Amarkantak Biosphere Reserve lies mainly across Madhya Pradesh and which state?", "Chhattisgarh", STATES, "biosphere_reserves"),
    ("Agasthyamalai Biosphere Reserve spans Kerala and which state?", "Tamil Nadu", STATES, "biosphere_reserves"),
    ("Great Nicobar Biosphere Reserve is in which island group?", "Andaman and Nicobar Islands", ["Andaman and Nicobar Islands", "Lakshadweep", "Diu", "Majuli"], "biosphere_reserves"),
    ("Khangchendzonga Biosphere Reserve is in which state?", "Sikkim", STATES, "biosphere_reserves"),
    ("Panna Biosphere Reserve is in which state?", "Madhya Pradesh", STATES, "biosphere_reserves"),
    ("Seshachalam Biosphere Reserve is in which state?", "Andhra Pradesh", STATES, "biosphere_reserves"),
    ("Cold Desert Biosphere Reserve is in which state?", "Himachal Pradesh", STATES, "biosphere_reserves"),
    ("Bhitarkanika is best known for which coastal ecosystem?", "Mangroves", ["Mangroves", "Cold desert", "Alpine meadow", "Coral atoll"], "ecosystems"),
    ("Gulf of Mannar is especially known for which marine ecosystem?", "Coral reefs", ["Coral reefs", "Cold desert", "Black soil plain", "Alpine tundra"], "ecosystems"),
    ("Sundarbans is best known for which ecosystem?", "Mangrove delta", ["Mangrove delta", "Cold desert", "Semi-arid plateau", "Alpine meadow"], "ecosystems"),
    ("Keibul Lamjao National Park is famous for which feature?", "Floating phumdi habitat", ["Floating phumdi habitat", "Coral reef lagoon", "Cold desert dunes", "Salt marsh grassland"], "ecosystems"),
    ("Desert National Park protects which landscape?", "Thar Desert ecosystem", ["Thar Desert ecosystem", "Western Ghats rainforest", "Himalayan glacier", "Sundarbans mangrove"], "ecosystems"),
    ("The source region of the Narmada is near which place?", "Amarkantak", ["Amarkantak", "Gangotri", "Talakaveri", "Mansarovar"], "river_origins"),
    ("The source of the Kaveri is at which place?", "Talakaveri", ["Talakaveri", "Amarkantak", "Yamunotri", "Rohtang"], "river_origins"),
    ("The Bhagirathi originates from which glacier area?", "Gangotri Glacier", ["Gangotri Glacier", "Siachen Glacier", "Zemu Glacier", "Pindari Glacier"], "river_origins"),
    ("The Yamuna originates from which glacier region?", "Yamunotri", ["Yamunotri", "Gangotri", "Amarkantak", "Talakaveri"], "river_origins"),
    ("The Godavari originates near which Maharashtra town?", "Trimbak", ["Trimbak", "Mahabaleshwar", "Amarkantak", "Gangotri"], "river_origins"),
    ("The Krishna originates near which Western Ghats town?", "Mahabaleshwar", ["Mahabaleshwar", "Trimbak", "Talakaveri", "Amarkantak"], "river_origins"),
    ("The Mahanadi originates in which state?", "Chhattisgarh", STATES, "river_origins"),
    ("The Tapi originates in which state?", "Madhya Pradesh", STATES, "river_origins"),
    ("The Luni river drains mainly into which region?", "Rann of Kutch", ["Rann of Kutch", "Sundarbans", "Chilika Lagoon", "Loktak Lake"], "river_systems"),
    ("The Damodar is often associated with which plateau region?", "Chota Nagpur Plateau", ["Chota Nagpur Plateau", "Shillong Plateau", "Malwa Plateau", "Ladakh Plateau"], "river_systems"),
    ("The Shivalik Hills are the outermost range of which mountain system?", "Himalayas", ["Himalayas", "Aravalli", "Western Ghats", "Satpura"], "mountain_systems"),
    ("The Zanskar Range is part of which broad region?", "Trans-Himalaya", ["Trans-Himalaya", "Eastern Ghats", "Aravalli", "Malwa Plateau"], "mountain_systems"),
    ("The Karakoram Range lies mainly to the north of which Indian region?", "Ladakh", ["Ladakh", "Konkan", "Bundelkhand", "Malabar"], "mountain_systems"),
    ("The Pir Panjal Range is most associated with which region?", "Jammu and Kashmir", ["Jammu and Kashmir", "Tamil Nadu", "Odisha", "Gujarat"], "mountain_systems"),
    ("The Patkai hills lie near India's border with which country?", "Myanmar", ["Myanmar", "Pakistan", "Sri Lanka", "Maldives"], "mountain_systems"),
    ("The Garo, Khasi and Jaintia hills are in which state?", "Meghalaya", STATES, "mountain_systems"),
    ("The Bhabar belt lies just south of which Himalayan zone?", "Shivalik foothills", ["Shivalik foothills", "Greater Himalaya snowline", "Karakoram glaciers", "Deccan escarpment"], "physical_regions"),
    ("The Terai belt is known for which landscape condition?", "Marshy grassland and forests", ["Marshy grassland and forests", "Cold desert dunes", "Coral reefs", "Salt pans"], "physical_regions"),
    ("The Malwa Plateau is mainly associated with which state?", "Madhya Pradesh", STATES, "physical_regions"),
    ("The Shillong Plateau is in which state?", "Meghalaya", STATES, "physical_regions"),
    ("The Barren Island volcano is in which island group?", "Andaman and Nicobar Islands", ["Andaman and Nicobar Islands", "Lakshadweep", "Daman and Diu", "Majuli"], "islands"),
    ("Minicoy is part of which Union Territory?", "Lakshadweep", ["Lakshadweep", "Andaman and Nicobar Islands", "Puducherry", "Dadra and Nagar Haveli and Daman and Diu"], "islands"),
    ("The Palk Strait separates Tamil Nadu from which country?", "Sri Lanka", ["Sri Lanka", "Maldives", "Indonesia", "Myanmar"], "maritime_geography"),
    ("The Gulf of Kutch lies along which state?", "Gujarat", STATES, "maritime_geography"),
    ("The Gulf of Khambhat lies along which state?", "Gujarat", STATES, "maritime_geography"),
    ("The Ten Degree Channel separates which island groups?", "Andaman and Nicobar", ["Andaman and Nicobar", "Lakshadweep and Minicoy", "Diu and Daman", "Majuli and Umananda"], "maritime_geography"),
    ("The Nine Degree Channel is associated with which island group?", "Lakshadweep", ["Lakshadweep", "Andaman and Nicobar Islands", "Sundarbans", "Diu"], "maritime_geography"),
    ("The retreating monsoon gives important rainfall to which coast?", "Coromandel Coast", ["Coromandel Coast", "Konkan Coast", "Kutch Coast", "Malabar Coast"], "climate"),
    ("Western disturbances are most important for winter rain in which region?", "Northwestern India", ["Northwestern India", "Kerala coast", "Sundarbans", "Andaman Islands"], "climate"),
    ("Orographic rainfall on the windward side is strongly associated with which range?", "Western Ghats", ["Western Ghats", "Aravalli", "Vindhya", "Rajmahal Hills"], "climate"),
    ("The rain-shadow area east of the Western Ghats is mainly caused by what?", "Moist winds losing rain on windward slopes", ["Moist winds losing rain on windward slopes", "Cold ocean currents", "Polar night", "River capture"], "climate"),
    ("Mawsynram's high rainfall is linked to moisture from which monsoon branch?", "Bay of Bengal branch", ["Bay of Bengal branch", "Arabian Sea branch only", "Western disturbance", "Retreating monsoon only"], "climate"),
    ("The Leeward side of the Western Ghats is generally what?", "Drier than the windward side", ["Drier than the windward side", "Always snow-covered", "Tidal marsh", "Coral reef"], "climate"),
    ("India's southwest monsoon usually first reaches which state?", "Kerala", STATES, "climate"),
    ("The Deccan rain-shadow region lies mainly east of which mountain chain?", "Western Ghats", ["Western Ghats", "Eastern Ghats", "Aravalli", "Karakoram"], "climate"),
    ("Laterite soils form best under which broad climate condition?", "High rainfall and leaching", ["High rainfall and leaching", "Permanent snow cover", "Arid salt deposition", "Glacial erosion"], "soils"),
    ("Regur soil is another name for which soil?", "Black soil", ["Black soil", "Alluvial soil", "Laterite soil", "Desert soil"], "soils"),
    ("The Bhangar alluvium is generally older than which alluvial deposit?", "Khadar", ["Khadar", "Regur", "Laterite", "Peaty soil"], "soils"),
    ("Khadar soil is renewed mainly by what?", "River floods", ["River floods", "Volcanic ash", "Glacial winds", "Coral erosion"], "soils"),
    ("Arid soil in India is most associated with which region?", "Western Rajasthan", ["Western Rajasthan", "Assam valley", "Kerala hills", "Sikkim Himalaya"], "soils"),
]


def build_questions() -> list[dict]:
    items: list[dict] = []
    for difficulty, facts in [(1, EASY_FACTS), (2, MEDIUM_FACTS), (3, HARD_FACTS)]:
        for i, (text, correct, pool, note) in enumerate(facts, 1):
            items.append(question(difficulty, text, correct, pool, note, i + difficulty * 1000))
    return items


def assign_ids(items: list[dict], existing: list[dict]) -> list[dict]:
    next_seq: dict[int, int] = {}
    for difficulty in (1, 2, 3):
        max_seq = 0
        for q in existing:
            if q.get("category") == "geography" and q.get("difficulty") == difficulty:
                try:
                    max_seq = max(max_seq, int(str(q["id"]).rsplit("_", 1)[-1]))
                except ValueError:
                    pass
        next_seq[difficulty] = max_seq + 1

    existing_text = {q["question"].strip().lower() for q in existing}
    seen_text: set[str] = set()
    output: list[dict] = []
    for item in items:
        key = item["question"].strip().lower()
        if key in existing_text or key in seen_text:
            continue
        seen_text.add(key)
        diff = item["difficulty"]
        item = dict(item)
        item["id"] = f"geo_{DIFF_LABEL[diff]}_{next_seq[diff]:03d}"
        next_seq[diff] += 1
        output.append(item)
    return output


def validate(items: list[dict], existing: list[dict]) -> None:
    ids = [q["id"] for q in existing] + [q["id"] for q in items]
    dupes = [item for item, count in Counter(ids).items() if count > 1]
    if dupes:
        raise SystemExit(f"Duplicate IDs: {dupes[:10]}")
    for q in items:
        if len(q["options"]) != 4:
            raise SystemExit(f"Bad option count: {q['id']}")
        if not 0 <= q["correct_index"] < 4:
            raise SystemExit(f"Bad correct index: {q['id']}")
        if q["options"][q["correct_index"]] not in q["options"]:
            raise SystemExit(f"Missing correct answer: {q['id']}")
        if len(set(q["options"])) != 4:
            raise SystemExit(f"Duplicate option: {q['id']}")


def main() -> None:
    existing = json.loads(BANK_PATH.read_text())
    generated = assign_ids(build_questions(), existing)
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
