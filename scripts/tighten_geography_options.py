#!/usr/bin/env python3
"""Tighten geography distractors so options stay in the same answer family."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "backend" / "app" / "data" / "gk_questions.json"
GEN_FILES = sorted((ROOT / "backend" / "app" / "data").glob("geography*_generated_*.json"))


GENERATED_IDS: set[str] = set()
for gen_file in GEN_FILES:
    for question in json.loads(gen_file.read_text()):
        GENERATED_IDS.add(question["id"])


STATE_CLOSE_OPTIONS: dict[str, list[str]] = {
    "Andhra Pradesh": ["Andhra Pradesh", "Telangana", "Tamil Nadu", "Odisha"],
    "Arunachal Pradesh": ["Arunachal Pradesh", "Assam", "Nagaland", "Sikkim"],
    "Assam": ["Assam", "Meghalaya", "Arunachal Pradesh", "Nagaland"],
    "Bihar": ["Bihar", "Uttar Pradesh", "Jharkhand", "West Bengal"],
    "Chhattisgarh": ["Chhattisgarh", "Madhya Pradesh", "Odisha", "Jharkhand"],
    "Goa": ["Goa", "Maharashtra", "Karnataka", "Kerala"],
    "Gujarat": ["Gujarat", "Rajasthan", "Maharashtra", "Madhya Pradesh"],
    "Haryana": ["Haryana", "Rajasthan", "Punjab", "Uttar Pradesh"],
    "Himachal Pradesh": ["Himachal Pradesh", "Uttarakhand", "Jammu and Kashmir", "Punjab"],
    "Jharkhand": ["Jharkhand", "Bihar", "Odisha", "West Bengal"],
    "Karnataka": ["Karnataka", "Kerala", "Tamil Nadu", "Andhra Pradesh"],
    "Kerala": ["Kerala", "Tamil Nadu", "Karnataka", "Goa"],
    "Madhya Pradesh": ["Madhya Pradesh", "Chhattisgarh", "Rajasthan", "Uttar Pradesh"],
    "Maharashtra": ["Maharashtra", "Gujarat", "Madhya Pradesh", "Karnataka"],
    "Manipur": ["Manipur", "Mizoram", "Nagaland", "Assam"],
    "Meghalaya": ["Meghalaya", "Assam", "Mizoram", "Tripura"],
    "Mizoram": ["Mizoram", "Manipur", "Tripura", "Assam"],
    "Nagaland": ["Nagaland", "Manipur", "Assam", "Arunachal Pradesh"],
    "Odisha": ["Odisha", "West Bengal", "Jharkhand", "Chhattisgarh"],
    "Punjab": ["Punjab", "Haryana", "Rajasthan", "Himachal Pradesh"],
    "Rajasthan": ["Rajasthan", "Gujarat", "Haryana", "Madhya Pradesh"],
    "Sikkim": ["Sikkim", "Arunachal Pradesh", "Himachal Pradesh", "Uttarakhand"],
    "Tamil Nadu": ["Tamil Nadu", "Kerala", "Karnataka", "Andhra Pradesh"],
    "Telangana": ["Telangana", "Andhra Pradesh", "Karnataka", "Maharashtra"],
    "Tripura": ["Tripura", "Mizoram", "Meghalaya", "Assam"],
    "Uttar Pradesh": ["Uttar Pradesh", "Bihar", "Madhya Pradesh", "Uttarakhand"],
    "Uttarakhand": ["Uttarakhand", "Himachal Pradesh", "Uttar Pradesh", "Jammu and Kashmir"],
    "West Bengal": ["West Bengal", "Odisha", "Bihar", "Assam"],
    "Jammu and Kashmir": ["Jammu and Kashmir", "Ladakh", "Himachal Pradesh", "Uttarakhand"],
    "Ladakh": ["Ladakh", "Jammu and Kashmir", "Himachal Pradesh", "Uttarakhand"],
    "Lakshadweep": ["Lakshadweep", "Andaman and Nicobar Islands", "Puducherry", "Dadra and Nagar Haveli and Daman and Diu"],
    "Puducherry": ["Puducherry", "Lakshadweep", "Andaman and Nicobar Islands", "Dadra and Nagar Haveli and Daman and Diu"],
}


def rotate_correct(options: list[str], answer: str, correct_index: int) -> list[str]:
    without_answer = [option for option in options if option != answer]
    rotated = without_answer[:]
    rotated.insert(correct_index, answer)
    return rotated


# id -> (options, correct_index)
REPLACEMENTS: dict[str, tuple[list[str], int]] = {
    # Climate and monsoon.
    "geo_medium_347": (["Retreating monsoon", "Advancing monsoon", "Winter monsoon", "Pre-monsoon season"], 0),
    "geo_hard_311": (["Western Ghats", "Eastern Ghats", "Aravalli Range", "Satpura Range"], 0),
    "geo_hard_315": (["Pre-monsoon season", "Post-monsoon season", "Winter season", "Peak southwest monsoon"], 1),
    "geo_hard_317": (["Orographic setting", "Rain-shadow effect", "Monsoon-break phase", "Western disturbance"], 0),
    "geo_hard_318": (["Himalayan rain shadow", "Continentality", "Western disturbance", "Orographic uplift"], 0),
    "geo_hard_320": (["Bay of Bengal moisture", "Western disturbance", "Northeast monsoon", "Arabian Sea branch"], 0),
    "geo_easy_330": (["Humid hill slopes", "Deltaic lowlands", "Arid plains", "Coastal salt flats"], 0),
    "geo_medium_356": (["Western Ghats", "Eastern Himalaya", "Meghalaya Plateau", "Nilgiri Hills"], 0),
    "geo_medium_357": (["Arid and poorly drained areas", "Humid alluvial plains", "Lateritic uplands", "Mountain forest slopes"], 0),
    "geo_medium_361": (["Moist alluvial lowland", "Arid pediplain", "Lateritic upland", "Coastal salt flat"], 0),
    # Soils and deposits.
    "geo_hard_323": (["Khadar", "Bhangar", "Regur", "Laterite crust"], 0),
    "geo_hard_325": (["Coal and iron ore", "Bauxite and laterite", "Copper and mica", "Limestone and dolomite"], 0),
    "geo_hard_326": (["Coal", "Bauxite", "Gold", "Mica"], 0),
    "geo_hard_328": (["Coal", "Bauxite", "Gold", "Mica"], 2),
    # Wetlands/ecosystems.
    "geo_medium_375": (["Bird wetland", "Mangrove swamp", "Brackish lagoon", "Freshwater marsh"], 0),
    "geo_hard_338": (["Brackish coastal lagoon", "Freshwater oxbow lake", "Crater lake", "Salt lake"], 0),
    "geo_hard_341": (["Seasonal salt marsh", "Brackish lagoon", "Mangrove swamp", "Freshwater marsh"], 0),
    "geo_hard_342": (["Mangroves", "Coral reefs", "Salt marshes", "Seagrass beds"], 0),
    "geo_hard_348": (["Standard meridian", "Prime meridian", "International Date Line", "Tropic of Cancer"], 0),
    "geo_easy_352": (["Tropic of Cancer", "Equator", "Tropic of Capricorn", "Arctic Circle"], 0),
    "geo_easy_353": (["68 degrees E", "82.5 degrees E", "77 degrees E", "97 degrees E"], 1),
    "geo_easy_354": (["Nine Degree Channel", "Duncan Passage", "Ten Degree Channel", "Palk Strait"], 2),
    "geo_easy_355": (["Ten Degree Channel", "Palk Strait", "Duncan Passage", "Nine Degree Channel"], 3),
    "geo_medium_379": (["23.5 degrees N", "0 degrees", "23.5 degrees S", "66.5 degrees N"], 0),
    "geo_hard_345": (["68 degrees E", "77 degrees E", "82.5 degrees E", "97 degrees E"], 0),
    "geo_hard_346": (["77 degrees E", "97 degrees E", "82.5 degrees E", "68 degrees E"], 1),
    # Transport routes.
    "geo_hard_334": (["Nilgiri Mountain Railway", "Darjeeling Himalayan Railway", "Kalka-Shimla Railway", "Matheran Hill Railway"], 0),
    "geo_hard_335": (["NH 44", "NH 66", "Golden Quadrilateral", "North-South Corridor"], 0),
    "geo_hard_336": (["Konkan Railway", "Nilgiri Mountain Railway", "Darjeeling Himalayan Railway", "Kalka-Shimla Railway"], 0),
    # Seas, bays and river systems.
    "geo_medium_289": (["Arabian Sea", "Bay of Bengal", "Laccadive Sea", "Andaman Sea"], 0),
    "geo_medium_290": (["Bay of Bengal", "Arabian Sea", "Laccadive Sea", "Andaman Sea"], 0),
    "geo_medium_291": (["Arabian Sea", "Bay of Bengal", "Laccadive Sea", "Andaman Sea"], 0),
    "geo_hard_270": (["Meghna", "Ganga", "Brahmaputra", "Barak"], 0),
    "geo_hard_266": (["Rann of Kutch", "Little Rann of Kutch", "Gulf of Kutch", "Kutch mainland"], 0),
    # Islands and island groups.
    "geo_hard_252": (["Andaman Islands", "Nicobar Islands", "Lakshadweep Islands", "Pamban Island"], 0),
    "geo_hard_254": (["Pamban Island", "Sagar Island", "Divar Island", "Minicoy"], 0),
    "geo_easy_224": (["Andaman and Nicobar Islands", "Lakshadweep", "Diu", "Pamban Island"], 0),
    "geo_hard_181": (["Andaman and Nicobar Islands", "Lakshadweep", "Daman and Diu", "Puducherry"], 0),
    "geo_hard_211": (["Andaman and Nicobar Islands", "Lakshadweep", "Daman and Diu", "Puducherry"], 0),
    "geo_hard_217": (["Lakshadweep", "Andaman Islands", "Nicobar Islands", "Pamban Island"], 0),
    # UT/region options.
    "geo_hard_250": (["Jammu and Kashmir", "Ladakh", "Himachal Pradesh", "Uttarakhand"], 0),
    "geo_easy_236": (["Jammu and Kashmir", "Ladakh", "Himachal Pradesh", "Uttarakhand"], 0),
    "geo_medium_222": (["Ladakh", "Jammu and Kashmir", "Himachal Pradesh", "Uttarakhand"], 0),
    "geo_hard_204": (["Jammu and Kashmir", "Ladakh", "Himachal Pradesh", "Uttarakhand"], 0),
    "geo_hard_212": (["Lakshadweep", "Andaman and Nicobar Islands", "Puducherry", "Dadra and Nagar Haveli and Daman and Diu"], 0),
    # Resources, terrain, physical regions.
    "geo_medium_234": (["Minerals", "Fossil fuels", "Forest produce", "Hydropower"], 0),
    "geo_medium_231": (["Iron oxide", "Aluminium oxide", "Calcium carbonate", "Magnesium carbonate"], 0),
    "geo_medium_235": (["Coal", "Bauxite", "Copper", "Mica"], 0),
    "geo_medium_236": (["Gold", "Coal", "Bauxite", "Mica"], 0),
    "geo_medium_237": (["Copper", "Mica", "Bauxite", "Iron ore"], 0),
    "geo_medium_238": (["Bauxite", "Coal", "Mica", "Iron ore"], 0),
    "geo_medium_248": (["Rivers", "Fault lines", "Coastal erosion", "Lava flows"], 0),
    "geo_hard_186": (["Mangroves", "Coral reefs", "Seagrass beds", "Salt marshes"], 0),
    "geo_hard_187": (["Coral reefs", "Mangroves", "Seagrass beds", "Salt marshes"], 0),
    "geo_hard_188": (["Mangrove delta", "Brackish lagoon", "Tidal mudflat", "Salt marsh"], 0),
    "geo_hard_189": (["Floating phumdi habitat", "Brackish lagoon", "Mangrove swamp", "Freshwater marsh"], 0),
    "geo_hard_190": (["Thar Desert ecosystem", "Cold desert ecosystem", "Salt-marsh ecosystem", "Dry deciduous forest"], 0),
    "geo_hard_199": (["Rann of Kutch", "Thar Desert", "Sambhar Salt Lake", "Little Rann"], 0),
    "geo_hard_201": (["Himalayas", "Aravalli Range", "Western Ghats", "Satpura Range"], 0),
    "geo_hard_202": (["Trans-Himalaya", "Greater Himalaya", "Lesser Himalaya", "Shivalik"], 0),
    "geo_hard_207": (["Shivalik foothills", "Lesser Himalaya", "Greater Himalaya", "Trans-Himalaya"], 0),
    "geo_hard_208": (["Marshy grassland and forests", "Arid scrubland", "Alpine meadow", "Salt-pan plain"], 0),
    "geo_hard_219": (["Northwestern India", "Northeastern India", "Peninsular east coast", "Western coastal plain"], 0),
    "geo_hard_221": (["Moist winds losing rain on windward slopes", "Cold current reducing evaporation", "Cyclone landfall on leeward slopes", "Winter western disturbance"], 0),
    "geo_hard_223": (["Drier than the windward side", "Wetter than the windward side", "Equally wet all year", "Dominated by winter snowfall"], 0),
    "geo_hard_220": (["Western Ghats", "Eastern Ghats", "Aravalli Range", "Satpura Range"], 0),
    "geo_hard_225": (["Western Ghats", "Eastern Ghats", "Aravalli Range", "Satpura Range"], 0),
    "geo_hard_230": (["Western Rajasthan", "Kutch region", "Ladakh plateau", "Deccan interior"], 0),
    "geo_hard_226": (["High rainfall and leaching", "Arid salt deposition", "Permanent snow cover", "River flood renewal"], 0),
    "geo_hard_229": (["River floods", "Wind deposition", "Volcanic ash fall", "Coastal tides"], 0),
    # Soil/crop regional options.
    "geo_medium_232": (["Humid hill slopes", "Deltaic lowlands", "Black-soil plains", "Arid alluvial plains"], 0),
    "geo_medium_233": (["Ganga-Brahmaputra delta", "Mahanadi delta", "Godavari delta", "Kaveri delta"], 0),
    "geo_medium_250": (["Western and Eastern Ghats", "Vindhya and Satpura", "Karakoram and Zanskar", "Garo and Khasi Hills"], 0),
    "geo_medium_252": (["Deccan region", "Gangetic plain", "Trans-Himalaya", "Sundarbans delta"], 0),
}


def apply(data: list[dict]) -> int:
    changed = 0
    for q in data:
        if q.get("id") in GENERATED_IDS:
            answer = q["options"][q["correct_index"]]
            state_options = STATE_CLOSE_OPTIONS.get(answer)
            if state_options:
                q["options"] = rotate_correct(state_options, answer, q["correct_index"])
                changed += 1
        replacement = REPLACEMENTS.get(q.get("id"))
        if not replacement:
            continue
        options, correct_index = replacement
        q["options"] = options
        q["correct_index"] = correct_index
        changed += 1
    return changed


def main() -> None:
    total = 0
    for path in [BANK_PATH, *GEN_FILES]:
        data = json.loads(path.read_text())
        changed = apply(data)
        if changed:
            path.write_text(json.dumps(data, indent=2) + "\n")
            print(path, changed)
            total += changed
    print(f"total replacements applied {total}")


if __name__ == "__main__":
    main()
