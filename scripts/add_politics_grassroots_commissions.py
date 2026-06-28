#!/usr/bin/env python3
"""Add politics questions focused on grassroots democracy and commissions."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "backend" / "app" / "data" / "gk_questions.json"
OUT_PATH = ROOT / "backend" / "app" / "data" / "politics_grassroots_commissions_generated_80.json"


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
    q(1, "Which amendment is linked with Panchayati Raj institutions?", ["73rd Amendment", "74th Amendment", "61st Amendment", "86th Amendment"], "73rd Amendment", "grassroots"),
    q(1, "Which amendment is linked with urban local bodies?", ["74th Amendment", "73rd Amendment", "52nd Amendment", "101st Amendment"], "74th Amendment", "grassroots"),
    q(1, "Which body is the general assembly of village voters?", ["Gram Sabha", "Gram Panchayat", "Block Samiti", "Zila Parishad"], "Gram Sabha", "grassroots"),
    q(1, "Which elected body works at the village level?", ["Gram Panchayat", "Block Samiti", "Zila Parishad", "Municipal Council"], "Gram Panchayat", "grassroots"),
    q(1, "Which local body works at the district level in Panchayati Raj?", ["Zila Parishad", "Gram Panchayat", "Ward Committee", "Municipality"], "Zila Parishad", "grassroots"),
    q(1, "Which urban local body usually governs a large city?", ["Municipal Corporation", "Municipal Council", "Nagar Panchayat", "Gram Panchayat"], "Municipal Corporation", "grassroots"),
    q(1, "Which elected representative usually handles a city ward?", ["Ward councillor", "Sarpanch", "Zila Parishad chairperson", "Block Pramukh"], "Ward councillor", "grassroots"),
    q(1, "Which village representative is usually called Sarpanch?", ["Panchayat head", "Ward councillor", "Municipal chairperson", "District Collector"], "Panchayat head", "grassroots"),
    q(1, "Which movement is associated with forest protection by local communities?", ["Chipko Movement", "Narmada Bachao Andolan", "India Against Corruption", "Bhoodan Movement"], "Chipko Movement", "grassroots_movements"),
    q(1, "Which movement is associated with displacement issues around large dams?", ["Narmada Bachao Andolan", "Chipko Movement", "Appiko Movement", "Bhoodan Movement"], "Narmada Bachao Andolan", "grassroots_movements"),
    q(1, "Which movement made access to government records a civic demand?", ["RTI movement", "Jan Lokpal movement", "Chipko Movement", "Appiko Movement"], "RTI movement", "grassroots_movements"),
    q(1, "Which campaign is closely associated with the demand for Jan Lokpal?", ["India Against Corruption", "RTI movement", "Chipko Movement", "Narmada Bachao Andolan"], "India Against Corruption", "grassroots_movements"),
    q(1, "Which commission conducts national and state elections?", ["Election Commission", "Finance Commission", "UPSC", "National Human Rights Commission"], "Election Commission", "commissions"),
    q(1, "Which authority audits government accounts?", ["CAG", "Finance Commission", "UPSC", "Election Commission"], "CAG", "commissions"),
    q(1, "Which commission recommends sharing Union taxes with states?", ["Finance Commission", "Election Commission", "UPSC", "CAG"], "Finance Commission", "commissions"),
    q(1, "Which commission conducts civil services examinations?", ["UPSC", "Finance Commission", "Election Commission", "CAG"], "UPSC", "commissions"),
    q(1, "A complaint about Scheduled Caste safeguards should point to which commission?", ["National Commission for Scheduled Castes", "National Commission for Scheduled Tribes", "National Commission for Minorities", "National Commission for Women"], "National Commission for Scheduled Castes", "commissions"),
    q(1, "Which commission is meant specifically for Scheduled Tribe safeguards?", ["National Commission for Scheduled Tribes", "National Commission for Scheduled Castes", "National Commission for Backward Classes", "National Commission for Women"], "National Commission for Scheduled Tribes", "commissions"),
    q(1, "Which commission focuses on women's rights and safeguards?", ["National Commission for Women", "National Human Rights Commission", "National Commission for Minorities", "National Commission for Backward Classes"], "National Commission for Women", "commissions"),
    q(1, "Which commission deals with human-rights complaints?", ["National Human Rights Commission", "National Commission for Women", "National Commission for Minorities", "National Commission for Scheduled Castes"], "National Human Rights Commission", "commissions"),
    q(1, "Which commission focuses on notified minority communities?", ["National Commission for Minorities", "National Commission for Women", "National Commission for Scheduled Tribes", "National Commission for Backward Classes"], "National Commission for Minorities", "commissions"),
    q(1, "Which commission focuses on socially and educationally backward classes?", ["National Commission for Backward Classes", "National Commission for Scheduled Castes", "National Commission for Scheduled Tribes", "National Commission for Minorities"], "National Commission for Backward Classes", "commissions"),
    q(1, "Which official is associated with audit reports placed before legislatures?", ["CAG", "UPSC Chairperson", "Chief Election Commissioner", "Finance Commission Chairperson"], "CAG", "commissions"),
    q(1, "Which body supervises election symbols and party recognition?", ["Election Commission", "Finance Commission", "UPSC", "NHRC"], "Election Commission", "commissions"),

    q(2, "Which grassroots institution can question Panchayat spending directly?", ["Gram Sabha", "Gram Panchayat", "Block Samiti", "Zila Parishad"], "Gram Sabha", "grassroots"),
    q(2, "Which level sits between Gram Panchayat and Zila Parishad in many Panchayati Raj systems?", ["Block Samiti", "Gram Sabha", "Municipal Council", "Ward Committee"], "Block Samiti", "grassroots"),
    q(2, "Which local body is most relevant for drainage and streetlights in a town?", ["Municipality", "Gram Panchayat", "Zila Parishad", "State Election Commission"], "Municipality", "grassroots"),
    q(2, "Which local body is most relevant for village roads and water works?", ["Gram Panchayat", "Municipal Corporation", "Ward Committee", "State Legislature"], "Gram Panchayat", "grassroots"),
    q(2, "Which schedule lists Panchayat functions?", ["Eleventh Schedule", "Twelfth Schedule", "Seventh Schedule", "Tenth Schedule"], "Eleventh Schedule", "grassroots"),
    q(2, "Which schedule lists municipal functions?", ["Twelfth Schedule", "Eleventh Schedule", "Seventh Schedule", "Eighth Schedule"], "Twelfth Schedule", "grassroots"),
    q(2, "Which concept means giving local bodies real powers and funds?", ["Devolution", "Dissolution", "Defection", "Delimitation"], "Devolution", "grassroots"),
    q(2, "Which process lets villagers publicly check records of local works?", ["Social audit", "VVPAT count", "Question Hour", "Judicial review"], "Social audit", "grassroots"),
    q(2, "Which movement inspired similar forest-protection campaigns such as Appiko?", ["Chipko Movement", "Narmada Bachao Andolan", "India Against Corruption", "RTI movement"], "Chipko Movement", "grassroots_movements"),
    q(2, "Which movement is most linked with Medha Patkar?", ["Narmada Bachao Andolan", "Chipko Movement", "India Against Corruption", "Appiko Movement"], "Narmada Bachao Andolan", "grassroots_movements"),
    q(2, "Which campaign used public hearings to demand transparency in records and wages?", ["RTI movement", "Chipko Movement", "Bhoodan Movement", "Appiko Movement"], "RTI movement", "grassroots_movements"),
    q(2, "Which grassroots issue best matches India Against Corruption?", ["Anti-corruption accountability", "Forest conservation", "Dam rehabilitation", "Land donation"], "Anti-corruption accountability", "grassroots_movements"),
    q(2, "Which body prepares and updates electoral rolls for elections it conducts?", ["Election Commission", "Finance Commission", "UPSC", "CAG"], "Election Commission", "commissions"),
    q(2, "Which body recommends fiscal transfers between Union and states?", ["Finance Commission", "GST Council", "CAG", "UPSC"], "Finance Commission", "commissions"),
    q(2, "Which body audits whether public money was used as authorized?", ["CAG", "Finance Commission", "CVC", "Lokpal"], "CAG", "commissions"),
    q(2, "Which body conducts Civil Services and other central recruitment exams?", ["UPSC", "SSC", "Finance Commission", "Election Commission"], "UPSC", "commissions"),
    q(2, "NCSC is the abbreviation for which type of national commission?", ["Scheduled Castes", "Scheduled Tribes", "Women", "Minorities"], "Scheduled Castes", "commissions"),
    q(2, "The Scheduled Tribes commission is commonly abbreviated as what?", ["NCST", "NCSC", "NCBC", "NCW"], "NCST", "commissions"),
    q(2, "Which commission is the best fit for complaints on women's safeguards?", ["NCW", "NHRC", "NCM", "NCBC"], "NCW", "commissions"),
    q(2, "Which commission is the best fit for broad human-rights violations?", ["NHRC", "NCW", "NCSC", "NCM"], "NHRC", "commissions"),
    q(2, "Which commission is the best fit for minority-community safeguards?", ["NCM", "NCW", "NCSC", "NCST"], "NCM", "commissions"),
    q(2, "Which commission received constitutional status through the 102nd Amendment?", ["NCBC", "NCW", "NCM", "NHRC"], "NCBC", "commissions"),
    q(2, "UPSC is best known for which function?", ["Recruitment exams", "Tax sharing", "Party symbols", "Audit reports"], "Recruitment exams", "commissions"),
    q(2, "CAG's core public role is closest to which function?", ["Government audit", "Election rolls", "Civil services exam", "Tax devolution"], "Government audit", "commissions"),
    q(2, "The Finance Commission is most directly linked with which function?", ["Tax devolution", "Party recognition", "Human-rights inquiries", "Recruitment exams"], "Tax devolution", "commissions"),
    q(2, "Election Commission work is most directly linked with which function?", ["Poll conduct", "Audit reports", "Civil-service exams", "Minority safeguards"], "Poll conduct", "commissions"),

    q(3, "Which local institution is closest to direct democracy in rural India?", ["Gram Sabha", "Gram Panchayat", "Block Samiti", "Zila Parishad"], "Gram Sabha", "grassroots"),
    q(3, "Which reform gave constitutional backing to district-level Panchayati Raj bodies?", ["73rd Amendment", "74th Amendment", "52nd Amendment", "101st Amendment"], "73rd Amendment", "grassroots"),
    q(3, "Which reform gave constitutional backing to ward-level urban governance?", ["74th Amendment", "73rd Amendment", "61st Amendment", "86th Amendment"], "74th Amendment", "grassroots"),
    q(3, "Which local mechanism best checks whether Panchayat works actually happened?", ["Social audit", "No-confidence motion", "Money Bill", "VVPAT slip"], "Social audit", "grassroots"),
    q(3, "Which local principle means functions, funds, and functionaries move to local bodies?", ["Devolution", "Delimitation", "Defection", "Dissolution"], "Devolution", "grassroots"),
    q(3, "Which institution links all registered village voters to Panchayat accountability?", ["Gram Sabha", "Block Samiti", "Zila Parishad", "State Finance Commission"], "Gram Sabha", "grassroots"),
    q(3, "Which movement is the better match for forest rights and ecological protection?", ["Chipko Movement", "Narmada Bachao Andolan", "India Against Corruption", "Jan Lokpal movement"], "Chipko Movement", "grassroots_movements"),
    q(3, "Which movement is the better match for rehabilitation of dam-affected people?", ["Narmada Bachao Andolan", "Chipko Movement", "Appiko Movement", "RTI movement"], "Narmada Bachao Andolan", "grassroots_movements"),
    q(3, "Which movement is the better match for public access to official records?", ["RTI movement", "Chipko Movement", "Narmada Bachao Andolan", "Bhoodan Movement"], "RTI movement", "grassroots_movements"),
    q(3, "Which movement is the better match for Lokpal-focused anti-corruption protests?", ["India Against Corruption", "RTI movement", "Chipko Movement", "Narmada Bachao Andolan"], "India Against Corruption", "grassroots_movements"),
    q(3, "Which constitutional body is independent of the executive for election conduct?", ["Election Commission", "Finance Commission", "UPSC", "CAG"], "Election Commission", "commissions"),
    q(3, "Which constitutional authority is independent for audit of public accounts?", ["CAG", "Election Commission", "Finance Commission", "UPSC"], "CAG", "commissions"),
    q(3, "Which constitutional body is periodically constituted for Union-state fiscal sharing?", ["Finance Commission", "GST Council", "CAG", "UPSC"], "Finance Commission", "commissions"),
    q(3, "Which constitutional body protects merit-based recruitment to Union services?", ["UPSC", "Election Commission", "Finance Commission", "CAG"], "UPSC", "commissions"),
    q(3, "Which commission handles constitutional safeguards for Scheduled Castes?", ["NCSC", "NCST", "NCBC", "NCM"], "NCSC", "commissions"),
    q(3, "For Scheduled Tribe safeguard issues, which commission is the direct fit?", ["NCST", "NCSC", "NCBC", "NCM"], "NCST", "commissions"),
    q(3, "A women's legal-safeguard issue most directly fits which commission?", ["NCW", "NCSC", "NCST", "NCBC"], "NCW", "commissions"),
    q(3, "Which commission is statutory and focuses on human-rights protection?", ["NHRC", "NCW", "NCM", "NCSC"], "NHRC", "commissions"),
    q(3, "Minority-community safeguards are mainly handled by which commission?", ["NCM", "NHRC", "NCW", "NCST"], "NCM", "commissions"),
    q(3, "Which commission is constitutionally linked with backward classes after 102nd Amendment?", ["NCBC", "NCSC", "NCST", "NCM"], "NCBC", "commissions"),
    q(3, "A denial of Scheduled Caste protections is closest to which forum?", ["NCSC", "NCST", "NCBC", "NHRC"], "NCSC", "commissions"),
    q(3, "A tribal-safeguards complaint is closest to which forum?", ["NCST", "NCSC", "NCBC", "NCM"], "NCST", "commissions"),
    q(3, "A complaint about women's legal safeguards best fits which body?", ["NCW", "NHRC", "NCM", "UPSC"], "NCW", "commissions"),
    q(3, "A minority-community safeguard complaint best fits which body?", ["NCM", "NCW", "NCST", "Finance Commission"], "NCM", "commissions"),
    q(3, "Which body would be the best fit for advice on tax sharing with states?", ["Finance Commission", "CAG", "Election Commission", "UPSC"], "Finance Commission", "commissions"),
    q(3, "Which body would be the best fit for audit findings on government spending?", ["CAG", "Finance Commission", "UPSC", "Election Commission"], "CAG", "commissions"),
    q(3, "Which body would be the best fit for allotment of election symbols?", ["Election Commission", "UPSC", "Finance Commission", "NCM"], "Election Commission", "commissions"),
    q(3, "Which body would be the best fit for Civil Services Examination rules?", ["UPSC", "Election Commission", "Finance Commission", "CAG"], "UPSC", "commissions"),
    q(3, "Which body would be the best fit for broad human-rights inquiry powers?", ["NHRC", "NCW", "NCSC", "NCM"], "NHRC", "commissions"),
    q(3, "Which body would be the best fit for examining OBC inclusion issues?", ["NCBC", "NCSC", "NCST", "NCM"], "NCBC", "commissions"),
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
    existing_ids = {item["id"] for item in existing}
    collisions = sorted(existing_ids.intersection(ids))
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
        already_present = [item for item in bank if item.get("question") in wanted_texts]
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
