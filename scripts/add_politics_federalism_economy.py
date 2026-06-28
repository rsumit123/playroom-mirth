#!/usr/bin/env python3
"""Add politics questions on federalism and political economy."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "backend" / "app" / "data" / "gk_questions.json"
OUT_PATH = ROOT / "backend" / "app" / "data" / "politics_federalism_economy_generated_104.json"
START_SEQS = {1: 310, 2: 294, 3: 250}


def q(difficulty: int, question: str, options: list[str], correct: str, note: str) -> dict:
    return {
        "category": "politics",
        "difficulty": difficulty,
        "question": question,
        "options": options,
        "correct_index": options.index(correct),
        "source_note": note,
    }


QUESTIONS = [
    q(1, "Which schedule divides subjects into Union, State, and Concurrent lists?", ["Seventh Schedule", "Eighth Schedule", "Tenth Schedule", "Twelfth Schedule"], "Seventh Schedule", "federalism"),
    q(1, "Which list includes defence and foreign affairs?", ["Union List", "State List", "Concurrent List", "Municipal List"], "Union List", "federalism"),
    q(1, "Which list includes police and public order?", ["State List", "Union List", "Concurrent List", "Residuary List"], "State List", "federalism"),
    q(1, "Which list lets both Parliament and states make laws?", ["Concurrent List", "Union List", "State List", "Eleventh Schedule"], "Concurrent List", "federalism"),
    q(1, "Which idea means Centre and states work together instead of acting separately?", ["Cooperative federalism", "Unitary rule", "Judicial review", "Party whip"], "Cooperative federalism", "federalism"),
    q(1, "Which council is linked with cooperative federalism in GST decisions?", ["GST Council", "Finance Commission", "Inter-State Council", "NITI Aayog"], "GST Council", "federalism"),
    q(1, "Which body recommends how Union taxes are shared with states?", ["Finance Commission", "GST Council", "CAG", "Planning Commission"], "Finance Commission", "federalism"),
    q(1, "Which constitutional post often becomes important in Centre-state disputes?", ["Governor", "Speaker", "Mayor", "CAG"], "Governor", "federalism"),
    q(1, "Which case is strongly linked with limiting misuse of President's Rule?", ["S.R. Bommai", "Kesavananda Bharati", "Puttaswamy", "Vishaka"], "S.R. Bommai", "federalism"),
    q(1, "Which commission reviewed Centre-state relations in the 1980s?", ["Sarkaria Commission", "Mandal Commission", "Kothari Commission", "Santhanam Committee"], "Sarkaria Commission", "federalism"),
    q(1, "Which commission later reviewed Centre-state relations after Sarkaria?", ["Punchhi Commission", "Finance Commission", "Election Commission", "National Commission for Women"], "Punchhi Commission", "federalism"),
    q(1, "Which type of dispute is Cauvery best known for?", ["River-water sharing", "Border demarcation", "Language policy", "Tax devolution"], "River-water sharing", "inter_state_disputes"),
    q(1, "Cauvery water sharing mainly concerns which states?", ["Karnataka and Tamil Nadu", "Punjab and Haryana", "Maharashtra and Gujarat", "Assam and Meghalaya"], "Karnataka and Tamil Nadu", "inter_state_disputes"),
    q(1, "Mahadayi water dispute is most associated with which state pair?", ["Goa and Karnataka", "Tamil Nadu and Kerala", "Punjab and Rajasthan", "Bihar and Jharkhand"], "Goa and Karnataka", "inter_state_disputes"),
    q(1, "Which dispute is linked with Punjab and Haryana river-water sharing?", ["Ravi-Beas dispute", "Cauvery dispute", "Mahadayi dispute", "Krishna dispute"], "Ravi-Beas dispute", "inter_state_disputes"),
    q(1, "Which reorganization issue created Andhra as an early linguistic state?", ["Telugu-speaking state demand", "River-water tribunal demand", "GST dispute", "Coalfield merger"], "Telugu-speaking state demand", "regional_aspirations"),
    q(1, "Which statehood movement led to creation of Telangana?", ["Regional aspiration in Andhra Pradesh", "Linguistic merger with Karnataka", "River dispute with Kerala", "Tribal council in Assam"], "Regional aspiration in Andhra Pradesh", "regional_aspirations"),
    q(1, "Which state was created from Bihar in 2000?", ["Jharkhand", "Telangana", "Chhattisgarh", "Uttarakhand"], "Jharkhand", "regional_aspirations"),
    q(1, "Chhattisgarh was carved out of which parent state?", ["Madhya Pradesh", "Bihar", "Uttar Pradesh", "Andhra Pradesh"], "Madhya Pradesh", "regional_aspirations"),
    q(1, "Which state was created from Uttar Pradesh in 2000?", ["Uttarakhand", "Jharkhand", "Chhattisgarh", "Telangana"], "Uttarakhand", "regional_aspirations"),
    q(1, "Which body did NITI Aayog replace?", ["Planning Commission", "Finance Commission", "Election Commission", "CAG"], "Planning Commission", "planning"),
    q(1, "Which model is linked with India's early Five Year Plans?", ["Nehruvian planning", "LPG reforms", "Green Revolution", "Disinvestment"], "Nehruvian planning", "planning"),
    q(1, "Which economic approach did early India follow?", ["Mixed economy", "Pure laissez-faire", "Command economy only", "Gold standard economy"], "Mixed economy", "planning"),
    q(1, "Which sector was central to Nehruvian industrialization?", ["Public sector", "Only cottage industry", "Only private banks", "Only agriculture"], "Public sector", "planning"),
    q(1, "Which economist is linked with the Second Five Year Plan model?", ["P.C. Mahalanobis", "M.S. Swaminathan", "Verghese Kurien", "C. Rangarajan"], "P.C. Mahalanobis", "planning"),
    q(1, "Which Gandhian idea emphasizes self-reliant village communities?", ["Gram Swaraj", "Licence Raj", "Disinvestment", "Fiscal devolution"], "Gram Swaraj", "gandhian_economics"),
    q(1, "Which Gandhian economic idea asks wealth holders to act for social good?", ["Trusteeship", "Privatization", "Deficit financing", "Tariff reduction"], "Trusteeship", "gandhian_economics"),
    q(1, "Which movement is linked with voluntary land donation?", ["Bhoodan Movement", "Green Revolution", "LPG reforms", "Narmada Bachao Andolan"], "Bhoodan Movement", "land_reforms"),
    q(1, "Which reform targeted the old zamindari system?", ["Zamindari abolition", "Bank nationalization", "GST reform", "Disinvestment"], "Zamindari abolition", "land_reforms"),
    q(1, "Which agricultural change is associated with high-yielding seeds and irrigation?", ["Green Revolution", "White Revolution", "Blue Revolution", "Operation Flood"], "Green Revolution", "green_revolution"),
    q(1, "Who is strongly associated with India's Green Revolution?", ["M.S. Swaminathan", "P.C. Mahalanobis", "Verghese Kurien", "D.R. Gadgil"], "M.S. Swaminathan", "green_revolution"),
    q(1, "Which crop was central to India's Green Revolution success?", ["Wheat", "Tea", "Jute", "Rubber"], "Wheat", "green_revolution"),
    q(1, "Which term describes the pre-1991 system of heavy industrial licensing?", ["Licence Raj", "Green Revolution", "Gram Swaraj", "Federalism"], "Licence Raj", "liberalization"),
    q(1, "Which reforms are commonly called LPG reforms?", ["Liberalization, Privatization, Globalization", "Land, Panchayat, Governance", "Labour, Police, Governor", "Language, Planning, Growth"], "Liberalization, Privatization, Globalization", "liberalization"),
    q(1, "Which Prime Minister is linked with 1991 economic reforms?", ["P.V. Narasimha Rao", "Jawaharlal Nehru", "Indira Gandhi", "Morarji Desai"], "P.V. Narasimha Rao", "liberalization"),
    q(1, "Which Finance Minister is linked with the 1991 reforms?", ["Manmohan Singh", "Yashwant Sinha", "Pranab Mukherjee", "C.D. Deshmukh"], "Manmohan Singh", "liberalization"),

    q(2, "Which list conflict usually gives Union law priority when Parliament and a state both legislate?", ["Concurrent List conflict", "Union List conflict", "State List conflict", "Eighth Schedule conflict"], "Concurrent List conflict", "federalism"),
    q(2, "Which institution was created to discuss Centre-state issues under Article 263?", ["Inter-State Council", "GST Council", "Finance Commission", "Zonal Council"], "Inter-State Council", "federalism"),
    q(2, "Which phrase best describes the Indian model of federalism?", ["Federal system with unitary features", "Loose confederation", "Pure unitary state", "Two-nation federation"], "Federal system with unitary features", "federalism"),
    q(2, "Which feature shows an integrationist tendency in Indian federalism?", ["Single citizenship", "Dual citizenship", "Separate state constitutions for all states", "Independent state armies"], "Single citizenship", "federalism"),
    q(2, "Which service structure helps integrate administration across Union and states?", ["All India Services", "Only state civil services", "Only municipal cadres", "Only judicial cadres"], "All India Services", "federalism"),
    q(2, "Which power lets Parliament alter state boundaries by law?", ["Reorganization of states", "Judicial review", "Money Bill certification", "No-confidence motion"], "Reorganization of states", "federalism"),
    q(2, "Which commission is best matched with Governor's role and Centre-state relations?", ["Sarkaria Commission", "Mandal Commission", "Balwantrai Mehta Committee", "Kothari Commission"], "Sarkaria Commission", "federalism"),
    q(2, "Which later commission also reviewed Centre-state relations?", ["Punchhi Commission", "Finance Commission", "NITI Aayog", "National Commission for Minorities"], "Punchhi Commission", "federalism"),
    q(2, "Which case made federalism part of the basic-structure discussion?", ["S.R. Bommai", "Shah Bano", "Navtej Johar", "Vishaka"], "S.R. Bommai", "federalism"),
    q(2, "Which river dispute is most linked with Karnataka and Tamil Nadu?", ["Cauvery", "Ravi-Beas", "Mahadayi", "Sutlej-Yamuna"], "Cauvery", "inter_state_disputes"),
    q(2, "Which river dispute is most linked with Goa and Karnataka?", ["Mahadayi", "Cauvery", "Ravi-Beas", "Krishna"], "Mahadayi", "inter_state_disputes"),
    q(2, "Which river dispute is most linked with Punjab and Haryana?", ["Ravi-Beas", "Cauvery", "Mahadayi", "Godavari"], "Ravi-Beas", "inter_state_disputes"),
    q(2, "Which mechanism is used for many inter-state river water disputes?", ["Water disputes tribunal", "Finance Commission award", "Election petition", "Lokpal inquiry"], "Water disputes tribunal", "inter_state_disputes"),
    q(2, "Which regional aspiration led to Telangana's creation?", ["Separate statehood", "Union territory status", "River tribunal demand", "Municipal merger"], "Separate statehood", "regional_aspirations"),
    q(2, "Which idea was central to linguistic reorganization of states?", ["Language-based state identity", "River basin boundaries", "Tax-sharing formula", "Military commands"], "Language-based state identity", "regional_aspirations"),
    q(2, "Which institution drove centralized economic planning before NITI Aayog?", ["Planning Commission", "Finance Commission", "GST Council", "CAG"], "Planning Commission", "planning"),
    q(2, "Which model emphasized heavy industry and capital goods?", ["Mahalanobis model", "Gandhian trusteeship", "Green Revolution package", "LPG reforms"], "Mahalanobis model", "planning"),
    q(2, "Which phrase best describes Nehruvian economic planning?", ["State-led mixed economy", "Village-only production", "Full market deregulation", "No public sector"], "State-led mixed economy", "planning"),
    q(2, "Which institution symbolized public-sector-led industrialization?", ["Public sector enterprise", "Self-help group", "State Election Commission", "Gram Sabha"], "Public sector enterprise", "planning"),
    q(2, "Which policy tool reduced direct government ownership in some PSUs?", ["Disinvestment", "Land ceiling", "Social audit", "Water tribunal"], "Disinvestment", "planning"),
    q(2, "Which Gandhian idea focuses on village self-rule?", ["Gram Swaraj", "Licence Raj", "Fiscal federalism", "Import substitution"], "Gram Swaraj", "gandhian_economics"),
    q(2, "Which Gandhian idea asks industrialists to hold wealth in trust for society?", ["Trusteeship", "Disinvestment", "Liberalization", "Deficit financing"], "Trusteeship", "gandhian_economics"),
    q(2, "Which agrarian reform aimed to remove intermediary landlords?", ["Zamindari abolition", "Bank nationalization", "LPG reforms", "GST rollout"], "Zamindari abolition", "land_reforms"),
    q(2, "Which agrarian reform limits how much land one can hold?", ["Land ceiling", "Tenancy eviction", "Urban zoning", "Tariff reduction"], "Land ceiling", "land_reforms"),
    q(2, "Which reform tries to protect cultivators who lease land?", ["Tenancy reform", "Disinvestment", "Industrial licensing", "Fiscal devolution"], "Tenancy reform", "land_reforms"),
    q(2, "Which movement is most linked with Vinoba Bhave?", ["Bhoodan Movement", "Green Revolution", "Operation Flood", "Chipko Movement"], "Bhoodan Movement", "land_reforms"),
    q(2, "Which package best describes the Green Revolution?", ["HYV seeds, irrigation, fertilizers", "Land donation, trusteeship, khadi", "Privatization, globalization, deregulation", "Audit, taxation, devolution"], "HYV seeds, irrigation, fertilizers", "green_revolution"),
    q(2, "Which region became a major early beneficiary of Green Revolution wheat gains?", ["Punjab-Haryana belt", "Konkan coast", "North-East hills", "Deccan dry plateau only"], "Punjab-Haryana belt", "green_revolution"),
    q(2, "Which phrase best captures a common criticism of the Green Revolution?", ["Regional and crop imbalance", "End of irrigation", "No role for technology", "Abolition of markets"], "Regional and crop imbalance", "green_revolution"),
    q(2, "Which reform direction reduced the Licence Raj after 1991?", ["Industrial delicensing", "Zamindari abolition", "Panchayat reservation", "River tribunal"], "Industrial delicensing", "liberalization"),
    q(2, "Which reform direction opened more sectors to private and foreign investment?", ["Liberalization", "Land ceiling", "Trusteeship", "Cooperative federalism"], "Liberalization", "liberalization"),
    q(2, "Which phrase best describes globalization in the 1991 reform context?", ["Greater integration with world economy", "Village self-rule only", "State boundary change", "Judicial review"], "Greater integration with world economy", "liberalization"),
    q(2, "Which reform direction means reducing state ownership in enterprises?", ["Privatization", "Tenancy reform", "Green Revolution", "Gram Swaraj"], "Privatization", "liberalization"),
    q(2, "Which pair correctly matches political economy ideas?", ["Nehruvian: planning", "Gandhian: Licence Raj", "LPG: land ceilings", "Green Revolution: trusteeship"], "Nehruvian: planning", "planning"),
    q(2, "Which pair correctly matches economic reform ideas?", ["LPG: liberalization", "Bhoodan: industrial delicensing", "Mahalanobis: village-only production", "Green Revolution: tax devolution"], "LPG: liberalization", "liberalization"),
    q(2, "Which pair correctly matches agrarian policy ideas?", ["Land ceiling: redistribution", "Disinvestment: tenancy security", "Licence Raj: irrigation package", "GST Council: crop pricing"], "Land ceiling: redistribution", "land_reforms"),
    q(2, "Which pair correctly matches Green Revolution ideas?", ["HYV seeds: productivity push", "Trusteeship: fertilizer subsidy", "Licence Raj: wheat breeding", "Disinvestment: irrigation canals"], "HYV seeds: productivity push", "green_revolution"),

    q(3, "Which constitutional feature most clearly reflects a strong Centre in Indian federalism?", ["Residuary powers with Union", "Separate state citizenship", "State veto over Union laws", "Independent state armies"], "Residuary powers with Union", "federalism"),
    q(3, "Which idea best explains why All India Services are called integrationist?", ["They link Union and state administration", "They replace state legislatures", "They conduct municipal elections", "They audit state budgets"], "They link Union and state administration", "federalism"),
    q(3, "Which Centre-state issue did Sarkaria and Punchhi both examine?", ["Governor and emergency powers", "Civil service exam syllabus", "Municipal ward boundaries", "Minority commission powers"], "Governor and emergency powers", "federalism"),
    q(3, "Which body is a forum for discussing inter-state and Centre-state issues?", ["Inter-State Council", "Public Accounts Committee", "Election Commission", "UPSC"], "Inter-State Council", "federalism"),
    q(3, "Which doctrine protects federalism from destructive constitutional change?", ["Basic structure doctrine", "Money Bill doctrine", "Pleasure doctrine", "Colourable legislation only"], "Basic structure doctrine", "federalism"),
    q(3, "Which case made President's Rule subject to stronger judicial scrutiny?", ["S.R. Bommai", "Kihoto Hollohan", "Indra Sawhney", "Maneka Gandhi"], "S.R. Bommai", "federalism"),
    q(3, "Which river dispute best illustrates federal tension between Karnataka and Tamil Nadu?", ["Cauvery", "Ravi-Beas", "Mahadayi", "Narmada"], "Cauvery", "inter_state_disputes"),
    q(3, "Which river dispute best illustrates federal tension between Goa and Karnataka?", ["Mahadayi", "Cauvery", "Ravi-Beas", "Godavari"], "Mahadayi", "inter_state_disputes"),
    q(3, "Which river dispute best illustrates federal tension involving Punjab and Haryana?", ["Ravi-Beas", "Cauvery", "Mahadayi", "Krishna"], "Ravi-Beas", "inter_state_disputes"),
    q(3, "Which constitutional subject is directly tied to tribunals for river-water sharing?", ["Inter-state water disputes", "Finance Commission grants", "Election symbols", "Civil-service recruitment"], "Inter-state water disputes", "inter_state_disputes"),
    q(3, "Which demand best fits regional aspiration politics?", ["Separate statehood", "Audit of Union accounts", "Civil-service recruitment", "Money Bill certification"], "Separate statehood", "regional_aspirations"),
    q(3, "Which political process converted linguistic identity into state boundaries?", ["States reorganization", "Disinvestment", "Judicial review", "Public audit"], "States reorganization", "regional_aspirations"),
    q(3, "Which model is most tied to capital-goods-led industrial planning?", ["Mahalanobis model", "Gandhian trusteeship", "LPG reforms", "Bhoodan"], "Mahalanobis model", "planning"),
    q(3, "Which planning idea is closest to import substitution and public-sector growth?", ["Nehruvian mixed economy", "Gandhian village economy", "LPG reforms", "Green Revolution package"], "Nehruvian mixed economy", "planning"),
    q(3, "Which economic view is closest to small-scale, village-centred production?", ["Gandhian economics", "Mahalanobis model", "LPG reforms", "Public-sector monopoly"], "Gandhian economics", "gandhian_economics"),
    q(3, "Which Gandhian concept treats ownership as a social responsibility?", ["Trusteeship", "Privatization", "Fiscal federalism", "Industrial licensing"], "Trusteeship", "gandhian_economics"),
    q(3, "Which policy approach protected domestic industry through controls and licences?", ["Licence Raj", "Green Revolution", "Bhoodan", "GST federalism"], "Licence Raj", "liberalization"),
    q(3, "Which reform is the opposite of heavy industrial licensing?", ["Industrial delicensing", "Land ceiling", "Gram Swaraj", "River adjudication"], "Industrial delicensing", "liberalization"),
    q(3, "Which reform idea is closest to reducing the government's ownership stake?", ["Disinvestment", "Tenancy protection", "Cooperative federalism", "Judicial review"], "Disinvestment", "liberalization"),
    q(3, "Which reform idea is closest to opening the economy to global trade and capital?", ["Globalization", "Zamindari abolition", "Gram Swaraj", "States reorganization"], "Globalization", "liberalization"),
    q(3, "Which agrarian reform most directly attacked intermediary landlordism?", ["Zamindari abolition", "Green Revolution", "Disinvestment", "Industrial delicensing"], "Zamindari abolition", "land_reforms"),
    q(3, "Which agrarian reform tries to redistribute surplus land above a legal limit?", ["Land ceiling", "Tenancy eviction", "Licence Raj", "Public sector expansion"], "Land ceiling", "land_reforms"),
    q(3, "Which agrarian reform gives security to cultivators who rent land?", ["Tenancy reform", "Disinvestment", "Import substitution", "Fiscal devolution"], "Tenancy reform", "land_reforms"),
    q(3, "Which movement sought voluntary land redistribution rather than state acquisition?", ["Bhoodan Movement", "Green Revolution", "LPG reforms", "Operation Flood"], "Bhoodan Movement", "land_reforms"),
    q(3, "Which Green Revolution input package is the closest match?", ["HYV seeds plus irrigation and fertilizers", "Trusteeship plus khadi and village crafts", "Delicensing plus foreign investment", "Land donation plus social audit"], "HYV seeds plus irrigation and fertilizers", "green_revolution"),
    q(3, "Which leader-scientist is most associated with India's Green Revolution?", ["M.S. Swaminathan", "P.C. Mahalanobis", "Verghese Kurien", "Norman Borlaug only"], "M.S. Swaminathan", "green_revolution"),
    q(3, "Which criticism is commonly linked with Green Revolution outcomes?", ["Regional inequality", "End of wheat farming", "No use of irrigation", "Abolition of procurement"], "Regional inequality", "green_revolution"),
    q(3, "Which phrase best captures the shift from planning-era controls to 1991 reforms?", ["From Licence Raj to liberalization", "From federalism to monarchy", "From Gram Sabha to Rajya Sabha", "From courts to commissions"], "From Licence Raj to liberalization", "liberalization"),
    q(3, "Which pair correctly contrasts Nehruvian and Gandhian economics?", ["Heavy industry vs village economy", "Privatization vs globalization", "Tax devolution vs audit", "River tribunals vs statehood"], "Heavy industry vs village economy", "planning"),
    q(3, "Which pair correctly contrasts Green Revolution and land reforms?", ["Technology package vs land redistribution", "Audit reports vs tax sharing", "Statehood vs river disputes", "Writs vs tribunals"], "Technology package vs land redistribution", "green_revolution"),
    q(3, "Which pair correctly links 1991 reforms?", ["Delicensing and liberalization", "Zamindari and Bhoodan", "Gram Swaraj and trusteeship", "Cauvery and Mahadayi"], "Delicensing and liberalization", "liberalization"),
    q(3, "Which pair correctly links federalism and economic policy?", ["Finance Commission: tax sharing", "CAG: statehood demand", "UPSC: river tribunal", "ECI: land ceiling"], "Finance Commission: tax sharing", "federalism"),
]


def assign_ids(questions: list[dict], existing: list[dict]) -> list[dict]:
    max_by_diff = {1: 0, 2: 0, 3: 0}
    for item in existing:
        if item.get("category") != "politics":
            continue
        try:
            seq = int(str(item["id"]).rsplit("_", 1)[-1])
        except (KeyError, ValueError):
            continue
        max_by_diff[item.get("difficulty")] = max(max_by_diff.get(item.get("difficulty"), 0), seq)
    labels = {1: "easy", 2: "medium", 3: "hard"}
    output = []
    for item in questions:
        diff = item["difficulty"]
        max_by_diff[diff] += 1
        output.append({"id": f"pol_{labels[diff]}_{max_by_diff[diff]:03d}", **item})
    return output


def validate(questions: list[dict], existing: list[dict]) -> None:
    ids = [item["id"] for item in questions]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate generated IDs")
    collisions = sorted({item["id"] for item in existing}.intersection(ids))
    if collisions:
        raise ValueError(f"ID collisions: {collisions[:5]}")
    for item in questions:
        if len(item["options"]) != 4 or len(set(item["options"])) != 4:
            raise ValueError(f"Bad options in {item['id']}")
        if item["difficulty"] not in {1, 2, 3}:
            raise ValueError(f"Bad difficulty in {item['id']}")
        if item["category"] != "politics":
            raise ValueError(f"Bad category in {item['id']}")
        if not 0 <= item["correct_index"] < 4:
            raise ValueError(f"Bad correct_index in {item['id']}")


def main() -> None:
    bank = json.loads(BANK_PATH.read_text())
    wanted_texts = {item["question"] for item in QUESTIONS}
    existing_texts = {item.get("question") for item in bank}
    pending = [item for item in QUESTIONS if item["question"] not in existing_texts]
    if not pending:
        already_present = [
            item for item in bank
            if item.get("question") in wanted_texts
            and item.get("difficulty") in START_SEQS
            and int(str(item.get("id", "0")).rsplit("_", 1)[-1]) > START_SEQS[item["difficulty"]]
        ]
        OUT_PATH.write_text(json.dumps(already_present, indent=2) + "\n")
        print(f"generated=0 already_present={len(already_present)} total={len(bank)} out={OUT_PATH}")
        return
    generated = assign_ids(pending, bank)
    validate(generated, bank)
    OUT_PATH.write_text(json.dumps(generated, indent=2) + "\n")
    bank.extend(generated)
    BANK_PATH.write_text(json.dumps(bank, indent=2) + "\n")
    print(f"generated={len(generated)} total={len(bank)} out={OUT_PATH}")


if __name__ == "__main__":
    main()
