#!/usr/bin/env python3
"""Generate and merge a targeted geography balancing batch."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from add_geography_india_expansion import assign_ids, question, validate


ROOT = Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "backend" / "app" / "data" / "gk_questions.json"
OUT_PATH = ROOT / "backend" / "app" / "data" / "geography_balance_batch_generated_109.json"


CLIMATE_OPTIONS = [
    "Southwest monsoon", "Northeast monsoon", "Western disturbance", "Nor'wester",
    "Loo", "Mango showers", "Rain shadow", "Orographic rainfall",
    "Bay of Bengal branch", "Arabian Sea branch", "October heat", "Cyclonic rainfall",
]

SOIL_OPTIONS = [
    "Black soil", "Alluvial soil", "Laterite soil", "Red soil", "Arid soil",
    "Mountain soil", "Peaty soil", "Saline soil", "Forest soil", "Regur soil",
]

CROP_OPTIONS = [
    "Cotton", "Jute", "Tea", "Coffee", "Rice", "Wheat", "Sugarcane", "Rubber",
    "Groundnut", "Millets", "Spices", "Coconut",
]

PORT_OPTIONS = [
    "Deendayal Port", "Mumbai Port", "Jawaharlal Nehru Port", "Mormugao Port",
    "New Mangalore Port", "Cochin Port", "V.O. Chidambaranar Port", "Chennai Port",
    "Kamarajar Port", "Visakhapatnam Port", "Paradip Port", "Kolkata-Haldia Port",
]

STATE_OPTIONS = [
    "Andhra Pradesh", "Assam", "Gujarat", "Himachal Pradesh", "Karnataka",
    "Kerala", "Maharashtra", "Odisha", "Rajasthan", "Tamil Nadu",
    "Uttar Pradesh", "Uttarakhand", "West Bengal", "Goa",
]

WETLAND_OPTIONS = [
    "Chilika Lake", "Loktak Lake", "Wular Lake", "Sambhar Lake", "Pulicat Lake",
    "Vembanad-Kol", "Kolleru Lake", "Deepor Beel", "Harike Wetland",
    "Keoladeo Ghana", "Bhitarkanika mangroves", "East Kolkata Wetlands",
]

MAP_OPTIONS = [
    "Tropic of Cancer", "Indian Standard Time meridian", "Equator", "Arctic Circle",
    "82.5 degrees E", "23.5 degrees N", "68 degrees E", "97 degrees E",
    "Siliguri Corridor", "Palk Strait", "Ten Degree Channel", "Nine Degree Channel",
]


FACTS: list[tuple[int, str, str, list[str], str]] = [
    # Climate and monsoon.
    (1, "Which monsoon first brings widespread seasonal rain to Kerala?", "Southwest monsoon", CLIMATE_OPTIONS, "climate_monsoon"),
    (1, "Which monsoon is most important for Tamil Nadu's main rainy season?", "Northeast monsoon", CLIMATE_OPTIONS, "climate_monsoon"),
    (1, "Heavy rain on the windward Western Ghats is caused mainly by what?", "Orographic rainfall", CLIMATE_OPTIONS, "climate_monsoon"),
    (1, "Which hot dry summer wind is common over northwestern India?", "Loo", CLIMATE_OPTIONS, "climate_monsoon"),
    (1, "Pre-monsoon showers in Kerala and Karnataka are often called what?", "Mango showers", CLIMATE_OPTIONS, "climate_monsoon"),
    (1, "Which monsoon branch gives very heavy rain to Meghalaya?", "Bay of Bengal branch", CLIMATE_OPTIONS, "climate_monsoon"),
    (1, "Which monsoon branch strikes the Western Ghats directly?", "Arabian Sea branch", CLIMATE_OPTIONS, "climate_monsoon"),
    (1, "Which condition makes interior Deccan areas drier than the Konkan coast?", "Rain shadow", CLIMATE_OPTIONS, "climate_monsoon"),
    (2, "Winter rainfall in Punjab and Haryana is mainly linked to what?", "Western disturbance", CLIMATE_OPTIONS, "climate_monsoon"),
    (2, "Kalbaisakhi storms in eastern India are also known as what?", "Nor'wester", CLIMATE_OPTIONS, "climate_monsoon"),
    (2, "Retreating monsoon rainfall is strongest along which coast?", "Coromandel Coast", ["Coromandel Coast", "Konkan Coast", "Kutch Coast", "Malabar Coast"], "climate_monsoon"),
    (2, "Mawsynram's rainfall is mainly boosted by which monsoon branch?", "Bay of Bengal branch", CLIMATE_OPTIONS, "climate_monsoon"),
    (2, "The leeward side of the Western Ghats is best described by which term?", "Rain shadow", CLIMATE_OPTIONS, "climate_monsoon"),
    (2, "October heat is most closely linked with which seasonal transition?", "Retreating monsoon", ["Retreating monsoon", "Peak winter", "Pre-monsoon hail", "Western disturbance"], "climate_monsoon"),
    (2, "Which weather system gives winter snow to parts of the western Himalaya?", "Western disturbance", CLIMATE_OPTIONS, "climate_monsoon"),
    (2, "Which rainfall type happens when moist air rises over mountains?", "Orographic rainfall", CLIMATE_OPTIONS, "climate_monsoon"),
    (2, "The Tamil Nadu coast gets much rain after the southwest monsoon because of what?", "Northeast monsoon", CLIMATE_OPTIONS, "climate_monsoon"),
    (2, "The Arabian Sea monsoon branch is most directly blocked by which range?", "Western Ghats", ["Western Ghats", "Aravalli Range", "Vindhya Range", "Rajmahal Hills"], "climate_monsoon"),
    (3, "The rain-shadow belt around Bengaluru is mainly east of which range?", "Western Ghats", ["Western Ghats", "Eastern Ghats", "Aravalli Range", "Karakoram"], "climate_monsoon"),
    (3, "The Chennai region depends more than Mumbai on which monsoon phase?", "Northeast monsoon", CLIMATE_OPTIONS, "climate_monsoon"),
    (3, "Which branch of the southwest monsoon turns toward the Ganga plain after entering the northeast?", "Bay of Bengal branch", CLIMATE_OPTIONS, "climate_monsoon"),
    (3, "Western Rajasthan's aridity is partly linked to which range lying parallel to monsoon winds?", "Aravalli Range", ["Aravalli Range", "Western Ghats", "Pir Panjal Range", "Patkai Hills"], "climate_monsoon"),
    (3, "Which season is associated with tropical cyclones affecting the Odisha-Andhra coast?", "Post-monsoon season", ["Post-monsoon season", "Peak summer only", "Winter fog season", "Spring snowmelt"], "climate_monsoon"),
    (3, "Which coastal belt gets intense rain from the Arabian Sea monsoon branch?", "Konkan and Malabar", ["Konkan and Malabar", "Coromandel and Kutch", "Bundelkhand and Malwa", "Ladakh and Zanskar"], "climate_monsoon"),
    (3, "Which term best explains why Cherrapunji is very wet but Shillong is less wet?", "Orographic setting", ["Orographic setting", "Tidal locking", "Cold current", "River piracy"], "climate_monsoon"),
    (3, "Which climate factor helps Ladakh remain very dry?", "Himalayan rain shadow", ["Himalayan rain shadow", "Equatorial doldrums", "Sea breeze dominance", "Coral reef barrier"], "climate_monsoon"),
    (3, "The Deccan interior gets less monsoon rain mainly after winds cross which barrier?", "Western Ghats", ["Western Ghats", "Eastern Himalaya", "Satpura Range", "Aravalli Range"], "climate_monsoon"),
    (3, "Which monsoon phenomenon is most tied to tea-growing rain in Assam?", "Bay of Bengal moisture", ["Bay of Bengal moisture", "Western disturbance snow", "Retreating monsoon only", "Loo winds"], "climate_monsoon"),
    # Soils, crops and resources.
    (1, "Black soil is especially suitable for which crop?", "Cotton", CROP_OPTIONS, "soils_crops_resources"),
    (1, "Jute grows best in which broad soil setting?", "Alluvial soil", SOIL_OPTIONS, "soils_crops_resources"),
    (1, "Tea plantations prefer which broad terrain?", "Humid hill slopes", ["Humid hill slopes", "Cold deserts", "Salt flats", "Dry ravines"], "soils_crops_resources"),
    (1, "Coffee plantations in India are strongly linked with which state?", "Karnataka", STATE_OPTIONS, "soils_crops_resources"),
    (1, "The Ganga plain is mainly known for which soil?", "Alluvial soil", SOIL_OPTIONS, "soils_crops_resources"),
    (1, "The Deccan cotton belt is mainly associated with which soil?", "Black soil", SOIL_OPTIONS, "soils_crops_resources"),
    (1, "Desert areas of western Rajasthan mainly have which soil?", "Arid soil", SOIL_OPTIONS, "soils_crops_resources"),
    (1, "High rainfall and leaching often produce which soil?", "Laterite soil", SOIL_OPTIONS, "soils_crops_resources"),
    (2, "Regur is another name for which soil?", "Black soil", SOIL_OPTIONS, "soils_crops_resources"),
    (2, "Khadar is the newer form of which soil?", "Alluvial soil", SOIL_OPTIONS, "soils_crops_resources"),
    (2, "Bhangar is the older form of which soil?", "Alluvial soil", SOIL_OPTIONS, "soils_crops_resources"),
    (2, "Red soil gets its colour mainly from which compound?", "Iron oxide", ["Iron oxide", "Sodium chloride", "Calcium carbonate", "Potassium nitrate"], "soils_crops_resources"),
    (2, "Laterite soil is common along which high-rainfall belt?", "Western Ghats", ["Western Ghats", "Thar Desert", "Ladakh plateau", "Rann of Kutch"], "soils_crops_resources"),
    (2, "Saline soils are most likely in which setting?", "Arid and poorly drained areas", ["Arid and poorly drained areas", "Alpine snowfields", "Fresh lava flows", "Dense evergreen canopy only"], "soils_crops_resources"),
    (2, "Peaty soil in India is commonly associated with which state?", "Kerala", STATE_OPTIONS, "soils_crops_resources"),
    (2, "The black-soil region of Maharashtra is strongly linked with which crop?", "Cotton", CROP_OPTIONS, "soils_crops_resources"),
    (2, "The deltaic plains of West Bengal are strongly linked with which fibre crop?", "Jute", CROP_OPTIONS, "soils_crops_resources"),
    (2, "The Terai belt is naturally suited to which broad condition?", "Moist alluvial lowland", ["Moist alluvial lowland", "Cold desert", "Salt marsh only", "Coral atoll"], "soils_crops_resources"),
    (3, "Which soil is formed by intense leaching under high rainfall?", "Laterite soil", SOIL_OPTIONS, "soils_crops_resources"),
    (3, "Which soil type is most associated with basaltic Deccan lava?", "Black soil", SOIL_OPTIONS, "soils_crops_resources"),
    (3, "Which soil deposit is renewed by frequent river floods?", "Khadar", ["Khadar", "Bhangar", "Regur", "Laterite crust"], "soils_crops_resources"),
    (3, "Which older alluvial terrace is usually above flood level?", "Bhangar", ["Bhangar", "Khadar", "Peaty soil", "Red soil"], "soils_crops_resources"),
    (3, "Which mineral belt is most associated with the Chota Nagpur Plateau?", "Coal and iron ore", ["Coal and iron ore", "Coral limestone", "Beach sand only", "Rock salt only"], "soils_crops_resources"),
    (3, "Jharia and Raniganj are best known for which resource?", "Coal", ["Coal", "Bauxite", "Gold", "Gypsum"], "soils_crops_resources"),
    (3, "Koraput and Kalahandi are strongly associated with which mineral?", "Bauxite", ["Bauxite", "Coal", "Mica", "Rock salt"], "soils_crops_resources"),
    (3, "Kolar is historically associated with which resource?", "Gold", ["Gold", "Coal", "Bauxite", "Petroleum"], "soils_crops_resources"),
    # Ports, transport and corridors.
    (1, "Deendayal Port is in which state?", "Gujarat", STATE_OPTIONS, "ports_transport"),
    (1, "Mormugao Port is in which state?", "Goa", STATE_OPTIONS, "ports_transport"),
    (1, "New Mangalore Port is in which state?", "Karnataka", STATE_OPTIONS, "ports_transport"),
    (1, "Cochin Port is in which state?", "Kerala", STATE_OPTIONS, "ports_transport"),
    (1, "Paradip Port is in which state?", "Odisha", STATE_OPTIONS, "ports_transport"),
    (1, "Visakhapatnam Port is in which state?", "Andhra Pradesh", STATE_OPTIONS, "ports_transport"),
    (1, "Chennai Port is in which state?", "Tamil Nadu", STATE_OPTIONS, "ports_transport"),
    (1, "Kolkata-Haldia Port is in which state?", "West Bengal", STATE_OPTIONS, "ports_transport"),
    (2, "Jawaharlal Nehru Port is located near which city?", "Mumbai", ["Mumbai", "Chennai", "Kochi", "Paradip"], "ports_transport"),
    (2, "Kamarajar Port is also known by which place name?", "Ennore", ["Ennore", "Tuticorin", "Mormugao", "Haldia"], "ports_transport"),
    (2, "V.O. Chidambaranar Port is associated with which city?", "Thoothukudi", ["Thoothukudi", "Kochi", "Mangaluru", "Kandla"], "ports_transport"),
    (2, "The Konkan Railway runs mainly along which coast?", "Western coast", ["Western coast", "Eastern coast", "Sundarbans coast", "Kutch coast"], "ports_transport"),
    (2, "The Golden Quadrilateral links Delhi, Mumbai, Chennai and which city?", "Kolkata", ["Kolkata", "Guwahati", "Srinagar", "Kochi"], "ports_transport"),
    (2, "NH 44 is best known for linking Srinagar with which southern endpoint?", "Kanyakumari", ["Kanyakumari", "Kochi", "Chennai", "Rameswaram"], "ports_transport"),
    (2, "The Darjeeling Himalayan Railway is in which state?", "West Bengal", STATE_OPTIONS, "ports_transport"),
    (2, "The Nilgiri Mountain Railway is mainly in which state?", "Tamil Nadu", STATE_OPTIONS, "ports_transport"),
    (2, "The Kalka-Shimla Railway is in which state?", "Himachal Pradesh", STATE_OPTIONS, "ports_transport"),
    (3, "Which port is located on the Hooghly river system?", "Kolkata-Haldia Port", PORT_OPTIONS, "ports_transport"),
    (3, "Which major port is located at Kandla?", "Deendayal Port", PORT_OPTIONS, "ports_transport"),
    (3, "Nhava Sheva is another name associated with which port?", "Jawaharlal Nehru Port", PORT_OPTIONS, "ports_transport"),
    (3, "Which major port serves Goa?", "Mormugao Port", PORT_OPTIONS, "ports_transport"),
    (3, "Which port is a major outlet for Odisha's mineral hinterland?", "Paradip Port", PORT_OPTIONS, "ports_transport"),
    (3, "Which railway is famous for connecting Mettupalayam and Ooty?", "Nilgiri Mountain Railway", ["Nilgiri Mountain Railway", "Konkan Railway", "Kalka-Shimla Railway", "Darjeeling Himalayan Railway"], "ports_transport"),
    (3, "Which transport corridor is often called India's main north-south highway spine?", "NH 44", ["NH 44", "NH 66", "Golden Quadrilateral", "Konkan Railway"], "ports_transport"),
    (3, "Which railway route is most associated with tunnels along the west coast?", "Konkan Railway", ["Konkan Railway", "Darjeeling Himalayan Railway", "Kalka-Shimla Railway", "Nilgiri Mountain Railway"], "ports_transport"),
    # Wetlands and ecosystems.
    (1, "Chilika Lake is in which state?", "Odisha", STATE_OPTIONS, "wetlands_ecosystems"),
    (1, "Loktak Lake is in which state?", "Manipur", ["Manipur", "Odisha", "Rajasthan", "Assam"], "wetlands_ecosystems"),
    (1, "Wular Lake is in which Union Territory?", "Jammu and Kashmir", ["Jammu and Kashmir", "Ladakh", "Delhi", "Puducherry"], "wetlands_ecosystems"),
    (1, "Sambhar Lake is in which state?", "Rajasthan", STATE_OPTIONS, "wetlands_ecosystems"),
    (1, "Pulicat Lake lies mainly along Andhra Pradesh and which state?", "Tamil Nadu", STATE_OPTIONS, "wetlands_ecosystems"),
    (1, "Vembanad Lake is in which state?", "Kerala", STATE_OPTIONS, "wetlands_ecosystems"),
    (1, "Kolleru Lake is in which state?", "Andhra Pradesh", STATE_OPTIONS, "wetlands_ecosystems"),
    (1, "Deepor Beel is in which state?", "Assam", STATE_OPTIONS, "wetlands_ecosystems"),
    (2, "Keibul Lamjao National Park is linked with which wetland?", "Loktak Lake", WETLAND_OPTIONS, "wetlands_ecosystems"),
    (2, "Bhitarkanika is best known for which ecosystem?", "Mangroves", ["Mangroves", "Alpine meadow", "Cold desert", "Black-soil plain"], "wetlands_ecosystems"),
    (2, "East Kolkata Wetlands are in which state?", "West Bengal", STATE_OPTIONS, "wetlands_ecosystems"),
    (2, "Harike Wetland is mainly associated with which state?", "Punjab", ["Punjab", "Odisha", "Kerala", "Assam"], "wetlands_ecosystems"),
    (2, "Keoladeo Ghana is best known as which type of habitat?", "Bird wetland", ["Bird wetland", "Cold desert", "Coral reef", "Lava plateau"], "wetlands_ecosystems"),
    (2, "Point Calimere is associated with which coastal state?", "Tamil Nadu", STATE_OPTIONS, "wetlands_ecosystems"),
    (2, "Ashtamudi Lake is in which state?", "Kerala", STATE_OPTIONS, "wetlands_ecosystems"),
    (2, "Nalsarovar Bird Sanctuary is in which state?", "Gujarat", STATE_OPTIONS, "wetlands_ecosystems"),
    (3, "The phumdi floating habitat is associated with which lake?", "Loktak Lake", WETLAND_OPTIONS, "wetlands_ecosystems"),
    (3, "Chilika is best described as what?", "Brackish coastal lagoon", ["Brackish coastal lagoon", "Glacial lake", "Crater lake", "Salt desert"], "wetlands_ecosystems"),
    (3, "The Nalabana bird sanctuary lies within which lagoon?", "Chilika Lake", WETLAND_OPTIONS, "wetlands_ecosystems"),
    (3, "Vembanad-Kol wetland is most associated with which state?", "Kerala", STATE_OPTIONS, "wetlands_ecosystems"),
    (3, "The Rann of Kutch is best described as which ecosystem?", "Seasonal salt marsh", ["Seasonal salt marsh", "Alpine grassland", "Coral lagoon", "Freshwater delta"], "wetlands_ecosystems"),
    (3, "Sundarbans wetlands are dominated by which ecosystem?", "Mangroves", ["Mangroves", "Cold desert", "Tropical thorn scrub", "Alpine tundra"], "wetlands_ecosystems"),
    (3, "Kolleru Lake lies between which river deltas?", "Godavari and Krishna", ["Godavari and Krishna", "Narmada and Tapi", "Ganga and Yamuna", "Mahanadi and Brahmani"], "wetlands_ecosystems"),
    (3, "The Bhoj Wetland is associated with which city?", "Bhopal", ["Bhopal", "Jaipur", "Kochi", "Guwahati"], "wetlands_ecosystems"),
    # Map literacy and location lines.
    (1, "Which important latitude passes through central India?", "Tropic of Cancer", MAP_OPTIONS, "map_location_literacy"),
    (1, "Indian Standard Time is based on which longitude?", "82.5 degrees E", MAP_OPTIONS, "map_location_literacy"),
    (1, "Which channel separates the Andaman and Nicobar groups?", "Ten Degree Channel", MAP_OPTIONS, "map_location_literacy"),
    (1, "Which channel is associated with Lakshadweep and Minicoy?", "Nine Degree Channel", MAP_OPTIONS, "map_location_literacy"),
    (2, "The Tropic of Cancer is closest to which latitude?", "23.5 degrees N", MAP_OPTIONS, "map_location_literacy"),
    (2, "India's standard meridian passes near which Uttar Pradesh city?", "Prayagraj", ["Prayagraj", "Jaipur", "Mumbai", "Guwahati"], "map_location_literacy"),
    (2, "The Siliguri Corridor is important because it links mainland India with which region?", "North East India", ["North East India", "Konkan", "Malwa", "Kutch"], "map_location_literacy"),
    (2, "The Palk Strait separates India from which country?", "Sri Lanka", ["Sri Lanka", "Maldives", "Myanmar", "Indonesia"], "map_location_literacy"),
    (3, "India's westernmost longitude is closest to which value?", "68 degrees E", MAP_OPTIONS, "map_location_literacy"),
    (3, "India's easternmost longitude is closest to which value?", "97 degrees E", MAP_OPTIONS, "map_location_literacy"),
    (3, "Which line explains why Gujarat and Arunachal have different sunrise times?", "Longitude", ["Longitude", "Latitude", "Altitude", "Tide line"], "map_location_literacy"),
    (3, "Why is IST a single time despite India's east-west width?", "Standard meridian", ["Standard meridian", "Equator crossing", "Tropic shift", "Sea-level datum"], "map_location_literacy"),
]


def main() -> None:
    existing = json.loads(BANK_PATH.read_text())
    generated = [
        question(difficulty, text, correct, pool, note, i + difficulty * 4000)
        for i, (difficulty, text, correct, pool, note) in enumerate(FACTS, 1)
    ]
    generated = assign_ids(generated, existing)
    validate(generated, existing)
    OUT_PATH.write_text(json.dumps(generated, indent=2) + "\n")
    merged = existing + generated
    BANK_PATH.write_text(json.dumps(merged, indent=2) + "\n")
    print(f"generated {len(generated)}")
    print(Counter(q["difficulty"] for q in generated))
    print(Counter(q["source_note"] for q in generated))
    print(f"total {len(merged)}")
    print(f"geography {sum(q.get('category') == 'geography' for q in merged)}")


if __name__ == "__main__":
    main()
