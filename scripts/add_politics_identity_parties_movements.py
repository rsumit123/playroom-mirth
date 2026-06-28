#!/usr/bin/env python3
"""Add politics questions on identity, parties, electoral behavior, and movements."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "backend" / "app" / "data" / "gk_questions.json"
OUT_PATH = ROOT / "backend" / "app" / "data" / "politics_identity_parties_movements_generated_109.json"


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
    q(1, "Which commission is most linked with OBC reservation politics?", ["Mandal Commission", "Sarkaria Commission", "Finance Commission", "Kothari Commission"], "Mandal Commission", "identity_politics"),
    q(1, "Which party is closely associated with Bahujan politics?", ["Bahujan Samaj Party", "Telugu Desam Party", "Dravida Munnetra Kazhagam", "Biju Janata Dal"], "Bahujan Samaj Party", "identity_politics"),
    q(1, "Which term refers to politics organized around caste identity?", ["Caste politics", "Coalition politics", "Fiscal federalism", "Judicial review"], "Caste politics", "identity_politics"),
    q(1, "Which idea means the State should treat all religions with equal respect?", ["Secularism", "Socialism", "Federalism", "Regionalism"], "Secularism", "identity_politics"),
    q(1, "Which commission is the direct forum for minority-community safeguards?", ["National Commission for Minorities", "National Commission for Women", "National Commission for Scheduled Tribes", "National Commission for Backward Classes"], "National Commission for Minorities", "identity_politics"),
    q(1, "Which schedule gives special arrangements for tribal areas in parts of the North-East?", ["Sixth Schedule", "Seventh Schedule", "Tenth Schedule", "Twelfth Schedule"], "Sixth Schedule", "identity_politics"),
    q(1, "Which demand is associated with the Darjeeling hills?", ["Gorkhaland", "Bodoland", "Vidarbha", "Bundelkhand"], "Gorkhaland", "identity_politics"),
    q(1, "Which demand is associated with Bodo identity politics in Assam?", ["Bodoland", "Gorkhaland", "Telangana", "Uttarakhand"], "Bodoland", "identity_politics"),
    q(1, "Which party is strongly associated with Dravidian politics in Tamil Nadu?", ["DMK", "TDP", "BJD", "Akali Dal"], "DMK", "party_system"),
    q(1, "TDP is best known as a regional party from which political space?", ["Telugu regional politics", "Dravidian politics", "Odia regional politics", "Sikh regional politics"], "Telugu regional politics", "party_system"),
    q(1, "BJD is best known as a regional party from which state?", ["Odisha", "Andhra Pradesh", "Tamil Nadu", "Punjab"], "Odisha", "party_system"),
    q(1, "Which party is strongly associated with Sikh and Punjab politics?", ["Akali Dal", "DMK", "BJD", "TMC"], "Akali Dal", "party_system"),
    q(1, "Trinamool Congress is best known as a regional force from which state?", ["West Bengal", "Odisha", "Andhra Pradesh", "Jammu and Kashmir"], "West Bengal", "party_system"),
    q(1, "Which term describes several parties sharing power in government?", ["Coalition government", "One-party system", "Judicial review", "Public audit"], "Coalition government", "party_system"),
    q(1, "Which phrase means no party has a clear majority in the legislature?", ["Hung house", "Money Bill", "Model Code", "Gram Sabha"], "Hung house", "party_system"),
    q(1, "Which group is a pressure group in politics?", ["Trade union", "Election Commission", "High Court", "Finance Commission"], "Trade union", "pressure_groups"),
    q(1, "Which pressure group represents organized labour?", ["Trade union", "Business chamber", "Farmers' union", "Student union"], "Trade union", "pressure_groups"),
    q(1, "Which pressure group represents cultivators' interests?", ["Farmers' union", "Trade union", "Business chamber", "Bar association"], "Farmers' union", "pressure_groups"),
    q(1, "Which term means voters reject a sitting government?", ["Anti-incumbency", "Coalition", "Delimitation", "Devolution"], "Anti-incumbency", "electoral_behavior"),
    q(1, "Which term refers to the share of eligible voters who vote?", ["Turnout", "Vote bank", "Swing", "Quota"], "Turnout", "electoral_behavior"),
    q(1, "Which term means a group seen as voting predictably for a party?", ["Vote bank", "Hung house", "Whip", "Writ"], "Vote bank", "electoral_behavior"),
    q(1, "Which term refers to voters who may shift between parties?", ["Swing voters", "Postal voters", "Proxy voters", "Tendered voters"], "Swing voters", "electoral_behavior"),
    q(1, "Which organization is known for civil-liberties work in India?", ["PUCL", "UPSC", "CAG", "NCBC"], "PUCL", "social_movements"),
    q(1, "Which movement is associated with women's safety at workplaces through Vishaka?", ["Women's rights movement", "Environmental movement", "Farmer movement", "Language movement"], "Women's rights movement", "social_movements"),
    q(1, "Which movement is linked with protests against dowry deaths?", ["Women's movement", "Civil-liberties movement", "Environmental movement", "Language movement"], "Women's movement", "social_movements"),
    q(1, "Which movement is best linked with forest conservation by villagers?", ["Chipko Movement", "Anti-arrack movement", "Civil liberties movement", "JP movement"], "Chipko Movement", "social_movements"),
    q(1, "Which movement is best linked with dam-displacement issues?", ["Narmada Bachao Andolan", "Chipko Movement", "Anti-arrack movement", "Right to Food campaign"], "Narmada Bachao Andolan", "social_movements"),
    q(1, "Which movement is associated with women protesting liquor abuse in Andhra Pradesh?", ["Anti-arrack movement", "Chipko Movement", "Bhoodan Movement", "RTI movement"], "Anti-arrack movement", "social_movements"),
    q(1, "Which term describes politicians from the same family repeatedly holding office?", ["Dynastic politics", "Coalition politics", "Federal politics", "Pressure politics"], "Dynastic politics", "legislator_profile"),
    q(1, "Which term refers to criminal cases becoming an issue in candidate politics?", ["Criminalisation of politics", "Coalition politics", "Fiscal federalism", "Judicial review"], "Criminalisation of politics", "legislator_profile"),
    q(1, "Which term describes women's presence in elected bodies?", ["Women's representation", "Vote-bank politics", "Anti-incumbency", "Delimitation"], "Women's representation", "legislator_profile"),
    q(1, "Which term refers to wealth and class background of elected representatives?", ["Socio-economic profile", "Electoral roll", "Party whip", "Model Code"], "Socio-economic profile", "legislator_profile"),
    q(1, "Which party system term describes many parties competing seriously?", ["Multi-party system", "Two-party system", "One-party rule", "Non-party democracy"], "Multi-party system", "party_system"),
    q(1, "Which concept links caste groups with electoral mobilization?", ["Social coalition", "Judicial review", "Tax devolution", "Public audit"], "Social coalition", "identity_politics"),
    q(1, "Which issue links Shah Bano and personal-law politics?", ["Religion and gender justice", "River-water sharing", "Industrial licensing", "State reorganization"], "Religion and gender justice", "identity_politics"),
    q(1, "Which term means political appeal based on religious identity?", ["Communal politics", "Coalition politics", "Green politics", "Fiscal politics"], "Communal politics", "identity_politics"),

    q(2, "Which case is most associated with the Mandal reservation framework?", ["Indra Sawhney", "S.R. Bommai", "Puttaswamy", "Vishaka"], "Indra Sawhney", "identity_politics"),
    q(2, "Which social category did Mandal politics mainly bring into national focus?", ["OBCs", "Anglo-Indians", "Linguistic minorities", "Non-resident Indians"], "OBCs", "identity_politics"),
    q(2, "Which political slogan is closest to Bahujan politics?", ["Majority of marginalized groups", "Single national language", "Pure market economy", "Centralized planning"], "Majority of marginalized groups", "identity_politics"),
    q(2, "Which constitutional arrangement protects many tribal areas in the North-East?", ["Sixth Schedule councils", "GST Council", "Public Accounts Committee", "Finance Commission"], "Sixth Schedule councils", "identity_politics"),
    q(2, "Which regional aspiration is linked with the Bodo movement?", ["Bodoland", "Gorkhaland", "Vidarbha", "Harit Pradesh"], "Bodoland", "identity_politics"),
    q(2, "Which regional aspiration is linked with the Darjeeling hills?", ["Gorkhaland", "Bodoland", "Telangana", "Saurashtra"], "Gorkhaland", "identity_politics"),
    q(2, "Which issue best describes communal politics?", ["Religious identity in political mobilization", "River-water sharing", "Public-sector disinvestment", "Civil-service recruitment"], "Religious identity in political mobilization", "identity_politics"),
    q(2, "Which concept best describes Dravidian parties' social base?", ["Regional-linguistic identity", "River-basin identity", "Civil-service identity", "Judicial identity"], "Regional-linguistic identity", "party_system"),
    q(2, "Which party is most associated with Dravidian ideology?", ["DMK", "TDP", "BJD", "Akali Dal"], "DMK", "party_system"),
    q(2, "Which party is most associated with Telugu regional assertion?", ["TDP", "DMK", "TMC", "National Conference"], "TDP", "party_system"),
    q(2, "Which party's base is most clearly tied to Odia regional politics?", ["BJD", "TDP", "AIADMK", "Shiv Sena"], "BJD", "party_system"),
    q(2, "Shiv Sena is most closely linked with which regional-political base?", ["Marathi regional politics", "Odia regional politics", "Telugu regional politics", "Sikh regional politics"], "Marathi regional politics", "party_system"),
    q(2, "National Conference is best understood as which kind of party?", ["Kashmir regional party", "Telugu regional party", "Dravidian party", "Odia regional party"], "Kashmir regional party", "party_system"),
    q(2, "Which coalition idea means allies agree on a shared policy agenda?", ["Common minimum programme", "Vote bank", "Party whip", "Model Code"], "Common minimum programme", "party_system"),
    q(2, "Which phrase means a party supports government without joining the cabinet?", ["Outside support", "Inner-party election", "Postal vote", "Floor crossing"], "Outside support", "party_system"),
    q(2, "Which phrase best describes coalition politics?", ["Government by alliance partners", "Government by courts", "Government by audit reports", "Government by commissions"], "Government by alliance partners", "party_system"),
    q(2, "Which group is a pressure group rather than a political party?", ["Business chamber", "Regional party", "National party", "Ruling coalition"], "Business chamber", "pressure_groups"),
    q(2, "Which pressure group mainly represents workers?", ["Trade union", "Farmers' union", "Business chamber", "Resident welfare association"], "Trade union", "pressure_groups"),
    q(2, "Which pressure group mainly represents industry interests?", ["Business chamber", "Trade union", "Farmers' union", "Student union"], "Business chamber", "pressure_groups"),
    q(2, "Which pressure group mainly represents agrarian interests?", ["Farmers' union", "Business chamber", "Trade union", "Bar association"], "Farmers' union", "pressure_groups"),
    q(2, "Which electoral behavior idea means voters punish a sitting government?", ["Anti-incumbency", "Coalition formation", "Delimitation", "Party recognition"], "Anti-incumbency", "electoral_behavior"),
    q(2, "Which electoral behavior idea means social groups vote as blocs?", ["Vote-bank politics", "Postal voting", "Tendered voting", "Floor test"], "Vote-bank politics", "electoral_behavior"),
    q(2, "Which electoral trend tracks rising participation by women voters?", ["Rising women turnout", "Vote-bank politics", "Anti-incumbency", "Swing voting"], "Rising women turnout", "electoral_behavior"),
    q(2, "Which factor can change voting behavior across elections?", ["Anti-incumbency mood", "Court roster", "Audit paragraph", "Writ jurisdiction"], "Anti-incumbency mood", "electoral_behavior"),
    q(2, "Which term describes candidates with serious pending criminal cases entering politics?", ["Criminalisation of politics", "Coalition politics", "Cooperative federalism", "Constitutional morality"], "Criminalisation of politics", "legislator_profile"),
    q(2, "Which term describes family networks shaping candidate selection?", ["Dynastic politics", "Pressure-group politics", "Civil-liberties politics", "Fiscal politics"], "Dynastic politics", "legislator_profile"),
    q(2, "Which profile issue asks whether MLAs and MPs reflect ordinary social diversity?", ["Representative social profile", "Election-symbol allotment", "River-water sharing", "Public audit"], "Representative social profile", "legislator_profile"),
    q(2, "Which organization is associated with democratic-rights activism?", ["PUDR", "UPSC", "CAG", "Finance Commission"], "PUDR", "social_movements"),
    q(2, "Which organization is associated with civil liberties activism?", ["PUCL", "NITI Aayog", "NCBC", "CAG"], "PUCL", "social_movements"),
    q(2, "Which period made civil liberties a major issue in Indian politics?", ["Emergency", "Green Revolution", "Planning Commission era", "GST rollout"], "Emergency", "social_movements"),
    q(2, "Which movement is linked with workplace sexual-harassment guidelines?", ["Women's movement", "Environmental movement", "Farmer movement", "Language movement"], "Women's movement", "social_movements"),
    q(2, "Which law area is most connected to anti-dowry activism?", ["Women's rights", "Environmental law", "Electoral law", "Water disputes"], "Women's rights", "social_movements"),
    q(2, "Which movement is linked with liquor prohibition demands by women?", ["Anti-arrack movement", "Chipko Movement", "Bhoodan Movement", "Gorkhaland movement"], "Anti-arrack movement", "social_movements"),
    q(2, "Which environmental movement protected trees through local protest?", ["Chipko Movement", "Narmada Bachao Andolan", "Silent Valley movement", "India Against Corruption"], "Chipko Movement", "social_movements"),
    q(2, "Which environmental movement opposed ecological damage in Kerala?", ["Silent Valley movement", "Chipko Movement", "Appiko Movement", "Bhoodan Movement"], "Silent Valley movement", "social_movements"),
    q(2, "Which movement opposed displacement from large dam projects?", ["Narmada Bachao Andolan", "Chipko Movement", "Silent Valley movement", "Anti-arrack movement"], "Narmada Bachao Andolan", "social_movements"),
    q(2, "Which movement is a Karnataka forest-conservation counterpart to Chipko?", ["Appiko Movement", "Narmada Bachao Andolan", "Anti-arrack movement", "Bhoodan Movement"], "Appiko Movement", "social_movements"),

    q(3, "Which politics concept best explains Mandal-era mobilization?", ["Caste-based social justice", "River-water federalism", "Public-sector planning", "Civil-service neutrality"], "Caste-based social justice", "identity_politics"),
    q(3, "Which political current is best linked with Kanshi Ram and BSP?", ["Bahujan politics", "Dravidian politics", "Hindutva politics", "Gandhian economics"], "Bahujan politics", "identity_politics"),
    q(3, "Which identity issue is most linked with Article 350B-type protections?", ["Linguistic minorities", "OBC reservations", "Women's movements", "Environmental movements"], "Linguistic minorities", "identity_politics"),
    q(3, "Which institution type is central to Sixth Schedule autonomy?", ["Autonomous district councils", "GST Council", "Finance Commission", "Municipal corporations"], "Autonomous district councils", "identity_politics"),
    q(3, "Which political demand is an ethnic-regional autonomy demand in Assam?", ["Bodoland", "Gorkhaland", "Vidarbha", "Bundelkhand"], "Bodoland", "identity_politics"),
    q(3, "Which political demand is an ethnic-regional autonomy demand in West Bengal hills?", ["Gorkhaland", "Bodoland", "Harit Pradesh", "Saurashtra"], "Gorkhaland", "identity_politics"),
    q(3, "Which concept best captures religion as a basis of electoral mobilization?", ["Communal politics", "Coalition bargaining", "Economic planning", "Public audit"], "Communal politics", "identity_politics"),
    q(3, "Which debate combines religion, gender, and personal law?", ["Uniform Civil Code debate", "River tribunal debate", "Delimitation debate", "Disinvestment debate"], "Uniform Civil Code debate", "identity_politics"),
    q(3, "Which party family is closest to Dravidian social-justice politics?", ["DMK-AIADMK", "TDP-BJD", "BSP-SP", "Akali-NC"], "DMK-AIADMK", "party_system"),
    q(3, "Which party is closest to a Telugu regional-party example?", ["TDP", "DMK", "Akali Dal", "National Conference"], "TDP", "party_system"),
    q(3, "For Odisha-centred regional politics, which party is the clearest example?", ["BJD", "TMC", "DMK", "AIADMK"], "BJD", "party_system"),
    q(3, "Which party is closest to a Punjab Sikh-regional party example?", ["Akali Dal", "BJD", "TDP", "DMK"], "Akali Dal", "party_system"),
    q(3, "National Conference is primarily rooted in which regional politics?", ["Kashmir", "Andhra Pradesh", "Tamil Nadu", "Odisha"], "Kashmir", "party_system"),
    q(3, "Which term best describes party support based on caste, class, region, and religion together?", ["Social base", "Judicial base", "Fiscal base", "Audit base"], "Social base", "party_system"),
    q(3, "Which coalition condition often produces bargaining among allies?", ["Hung Parliament", "Single-party majority", "Judicial review", "Finance Commission award"], "Hung Parliament", "party_system"),
    q(3, "Which coalition tool states shared policies among alliance partners?", ["Common minimum programme", "Election symbol order", "Audit report", "Writ petition"], "Common minimum programme", "party_system"),
    q(3, "Which phrase describes backing a government without ministerial posts?", ["Outside support", "Cabinet berth", "Party recognition", "Whip violation"], "Outside support", "party_system"),
    q(3, "Which kind of pressure group best fits CII or FICCI?", ["Business association", "Trade union", "Farmers' union", "Student union"], "Business association", "pressure_groups"),
    q(3, "Which kind of pressure group best fits a national farmers' union?", ["Agrarian interest group", "Business association", "Bar association", "Student union"], "Agrarian interest group", "pressure_groups"),
    q(3, "Which kind of pressure group best fits a workers' federation?", ["Trade union", "Business chamber", "Farmers' union", "Resident group"], "Trade union", "pressure_groups"),
    q(3, "Which electoral behavior term best describes voting against the ruling party due to dissatisfaction?", ["Anti-incumbency", "Vote transfer", "Party recognition", "Floor test"], "Anti-incumbency", "electoral_behavior"),
    q(3, "Which electoral behavior term describes a reliable caste or community support base?", ["Vote bank", "Postal ballot", "Tendered vote", "Counting agent"], "Vote bank", "electoral_behavior"),
    q(3, "Which electoral trend is about more women participating as voters?", ["Rising women turnout", "Floor crossing", "Delimitation freeze", "Judicial review"], "Rising women turnout", "electoral_behavior"),
    q(3, "Which legislator-profile issue concerns candidates' declared assets?", ["Wealth profile", "Vote-bank profile", "River-profile", "Writ profile"], "Wealth profile", "legislator_profile"),
    q(3, "Which legislator-profile issue concerns family dominance in tickets?", ["Dynastic politics", "Pressure-group lobbying", "Civil-liberties activism", "Federal bargaining"], "Dynastic politics", "legislator_profile"),
    q(3, "Which legislator-profile issue concerns pending serious cases among candidates?", ["Criminalisation of politics", "Coalition management", "Caste census", "Environmental clearance"], "Criminalisation of politics", "legislator_profile"),
    q(3, "Which civil-liberties organization is often abbreviated PUCL?", ["People's Union for Civil Liberties", "Planning Union for Cooperative Labour", "Public Utilities Commission League", "Panchayat Union for Civic Law"], "People's Union for Civil Liberties", "social_movements"),
    q(3, "Which rights organization is often abbreviated PUDR?", ["People's Union for Democratic Rights", "Public Union for District Reform", "Planning Unit for Development Review", "Panchayat Union for Democratic Roads"], "People's Union for Democratic Rights", "social_movements"),
    q(3, "Which movement area responds to unlawful detention and custodial abuse?", ["Civil liberties movement", "Environmental movement", "Regional party movement", "Coalition movement"], "Civil liberties movement", "social_movements"),
    q(3, "Which women's movement issue is linked with the Vishaka case?", ["Workplace sexual harassment", "River-water sharing", "Civil-service recruitment", "Land ceiling"], "Workplace sexual harassment", "social_movements"),
    q(3, "Which women's movement issue is linked with anti-dowry campaigns?", ["Dowry violence", "Forest conservation", "State reorganization", "Industrial licensing"], "Dowry violence", "social_movements"),
    q(3, "Which women's movement is linked with liquor prohibition in Andhra Pradesh?", ["Anti-arrack movement", "Chipko Movement", "Bhoodan Movement", "JP movement"], "Anti-arrack movement", "social_movements"),
    q(3, "Which environmental movement is most closely linked with the Western Ghats in Karnataka?", ["Appiko Movement", "Chipko Movement", "Narmada Bachao Andolan", "Silent Valley movement"], "Appiko Movement", "social_movements"),
    q(3, "Which environmental movement is most closely linked with Kerala rainforest protection?", ["Silent Valley movement", "Appiko Movement", "Chipko Movement", "Bhoodan Movement"], "Silent Valley movement", "social_movements"),
    q(3, "Which movement linked development, displacement, and environmental concerns?", ["Narmada Bachao Andolan", "Anti-arrack movement", "Bhoodan Movement", "JP movement"], "Narmada Bachao Andolan", "social_movements"),
    q(3, "Which movement linked forest conservation with local community protest in Uttarakhand?", ["Chipko Movement", "Appiko Movement", "Silent Valley movement", "India Against Corruption"], "Chipko Movement", "social_movements"),
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
        if item["category"] != "politics":
            raise ValueError(f"Bad category in {item['id']}")
        if item["difficulty"] not in {1, 2, 3}:
            raise ValueError(f"Bad difficulty in {item['id']}")
        if len(item["options"]) != 4 or len(set(item["options"])) != 4:
            raise ValueError(f"Bad options in {item['id']}")
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
