#!/usr/bin/env python3
"""Add politics questions for constitution/state/grassroots gaps."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "backend" / "app" / "data" / "gk_questions.json"
OUT_PATH = ROOT / "backend" / "app" / "data" / "politics_constitution_grassroots_generated_95.json"


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
    q(1, "Which word in the Preamble means India is not ruled by a monarch?", ["Republic", "Secular", "Socialist", "Federal"], "Republic", "constitutional_values"),
    q(1, "Which Preamble value means all religions get equal respect from the State?", ["Secular", "Sovereign", "Socialist", "Republic"], "Secular", "constitutional_values"),
    q(1, "Which Preamble value means people choose their government?", ["Democratic", "Socialist", "Sovereign", "Federal"], "Democratic", "constitutional_values"),
    q(1, "Which Preamble value means India makes its own decisions as an independent country?", ["Sovereign", "Secular", "Fraternity", "Republic"], "Sovereign", "constitutional_values"),
    q(1, "Which constitutional idea promotes brotherhood among citizens?", ["Fraternity", "Judicial review", "Money Bill", "Ordinance"], "Fraternity", "constitutional_values"),
    q(1, "Which part of the Constitution contains Fundamental Duties?", ["Part IVA", "Part III", "Part IV", "Part V"], "Part IVA", "constitutional_values"),
    q(1, "Which constitutional duties apply mainly to citizens?", ["Fundamental Duties", "Directive Principles", "Money Bills", "Writs"], "Fundamental Duties", "constitutional_values"),
    q(1, "Which constitutional principles guide the State in making social-welfare laws?", ["Directive Principles", "Fundamental Duties", "Election symbols", "Court rosters"], "Directive Principles", "constitutional_values"),
    q(1, "Are Directive Principles directly enforceable by courts?", ["No", "Yes, always", "Only during elections", "Only in villages"], "No", "constitutional_values"),
    q(1, "Which duty asks citizens to protect public property?", ["Fundamental Duty", "Cabinet duty", "Election duty", "Judicial review"], "Fundamental Duty", "constitutional_values"),
    q(1, "Which constitutional idea lets courts check whether a law violates the Constitution?", ["Judicial review", "Question Hour", "Zero Hour", "Postal ballot"], "Judicial review", "judiciary"),
    q(1, "Which doctrine says Parliament cannot destroy the Constitution's core identity?", ["Basic structure doctrine", "Collective responsibility", "Model Code", "Postal ballot rule"], "Basic structure doctrine", "judiciary"),
    q(1, "Which court is the highest court within a state?", ["High Court", "District Court", "Gram Nyayalaya", "Lok Adalat"], "High Court", "state_government"),
    q(1, "Which court hears many appeals from district courts in a state?", ["High Court", "Supreme Court only", "Gram Sabha", "Election Commission"], "High Court", "state_government"),
    q(1, "Which state-level body makes laws for a state?", ["State Legislature", "Municipal Corporation", "Finance Commission", "Gram Sabha"], "State Legislature", "state_government"),
    q(1, "Which house is the directly elected house in most state legislatures?", ["Vidhan Sabha", "Vidhan Parishad", "Rajya Sabha", "Gram Sabha"], "Vidhan Sabha", "state_government"),
    q(1, "Which official is the constitutional head of a state?", ["Governor", "Chief Minister", "Speaker", "Mayor"], "Governor", "state_government"),
    q(1, "Who leads the elected government in an Indian state?", ["Chief Minister", "Governor", "High Court Chief Justice", "State Election Commissioner"], "Chief Minister", "state_government"),
    q(1, "Which body advises the Governor through the Chief Minister?", ["State Council of Ministers", "High Court collegium", "Municipal Council", "Finance Commission"], "State Council of Ministers", "state_government"),
    q(1, "Which state officer gives legal advice to the state government?", ["Advocate General", "Attorney General", "CAG", "Lokpal"], "Advocate General", "state_government"),
    q(1, "Which constitutional amendment is linked with Panchayati Raj?", ["73rd Amendment", "42nd Amendment", "52nd Amendment", "101st Amendment"], "73rd Amendment", "grassroots"),
    q(1, "Which constitutional amendment is linked with municipalities?", ["74th Amendment", "44th Amendment", "61st Amendment", "86th Amendment"], "74th Amendment", "grassroots"),
    q(1, "Which local forum lets village voters directly review Panchayat work?", ["Gram Sabha", "Rajya Sabha", "Cabinet", "High Court"], "Gram Sabha", "grassroots"),
    q(1, "Which local body handles village-level development work?", ["Gram Panchayat", "Rajya Sabha", "GST Council", "High Court"], "Gram Panchayat", "grassroots"),
    q(1, "Which elected representative handles many ward-level city issues?", ["Ward councillor", "Governor", "Rajya Sabha MP", "CAG"], "Ward councillor", "grassroots"),
    q(1, "Which movement is famous for villagers hugging trees to prevent felling?", ["Chipko Movement", "Quit India Movement", "Green Revolution", "White Revolution"], "Chipko Movement", "grassroots_movements"),
    q(1, "Which movement is associated with displacement and rehabilitation around Narmada dams?", ["Narmada Bachao Andolan", "Chipko Movement", "Bhoodan Movement", "Non-Cooperation Movement"], "Narmada Bachao Andolan", "grassroots_movements"),
    q(1, "Which movement helped make transparency in government a public demand?", ["Right to Information movement", "Swadeshi movement", "Khilafat movement", "Blue Revolution"], "Right to Information movement", "grassroots_movements"),
    q(1, "Which anti-corruption campaign is closely linked with demand for a Jan Lokpal?", ["India Against Corruption", "Chipko Movement", "Narmada Bachao Andolan", "Appiko Movement"], "India Against Corruption", "grassroots_movements"),
    q(1, "Which local groups often help rural women save and borrow small amounts together?", ["Self-help groups", "Election committees", "High Court benches", "Cabinet committees"], "Self-help groups", "grassroots"),
    q(1, "Which local system gives citizens a direct voice in village development?", ["Gram Sabha participation", "Only governor approval", "Only Rajya Sabha debate", "Only court review"], "Gram Sabha participation", "grassroots"),
    q(1, "Which constitutional schedule lists Panchayat subjects?", ["Eleventh Schedule", "Seventh Schedule", "Eighth Schedule", "Tenth Schedule"], "Eleventh Schedule", "grassroots"),

    q(2, "Which Preamble value means the State should not privilege one religion over another?", ["Secular", "Republic", "Socialist", "Sovereign"], "Secular", "constitutional_values"),
    q(2, "Which Preamble value is most connected with reducing social and economic inequality?", ["Socialist", "Republic", "Secular", "Sovereign"], "Socialist", "constitutional_values"),
    q(2, "Which Preamble value is closest to equal legal and political status for citizens?", ["Equality", "Emergency", "Ordinance", "Federalism"], "Equality", "constitutional_values"),
    q(2, "Which Preamble value supports freedom of thought, expression, belief, faith, and worship?", ["Liberty", "Fraternity", "Sovereignty", "Cabinet rule"], "Liberty", "constitutional_values"),
    q(2, "What is the main purpose of Fundamental Duties?", ["Set citizen responsibilities", "Create election symbols", "Run courts directly", "Decide tax rates"], "Set citizen responsibilities", "constitutional_values"),
    q(2, "Which duty asks citizens to develop scientific temper?", ["Fundamental Duty", "Directive Principle", "Money Bill rule", "Election petition"], "Fundamental Duty", "constitutional_values"),
    q(2, "Which duty asks citizens to protect the natural environment?", ["Fundamental Duty", "Speaker's power", "Governor's discretion", "Money Bill rule"], "Fundamental Duty", "constitutional_values"),
    q(2, "Which constitutional principles are non-justiciable but important for governance?", ["Directive Principles", "Fundamental Rights", "Writs", "Election petitions"], "Directive Principles", "constitutional_values"),
    q(2, "Which idea best describes Directive Principles?", ["Policy goals for the State", "Criminal punishments", "Election symbols", "Court vacation rules"], "Policy goals for the State", "constitutional_values"),
    q(2, "Which constitutional idea balances individual rights with social-welfare goals?", ["Rights and Directive Principles", "Ballot and symbols", "Speaker and whip", "Mayor and councillor"], "Rights and Directive Principles", "constitutional_values"),
    q(2, "Which doctrine came from the Kesavananda Bharati case?", ["Basic structure doctrine", "Collective responsibility", "No-confidence motion", "Model Code"], "Basic structure doctrine", "judiciary"),
    q(2, "Which power lets courts strike down unconstitutional laws?", ["Judicial review", "Question Hour", "Postal ballot", "Party whip"], "Judicial review", "judiciary"),
    q(2, "Which court can issue writs under Article 226?", ["High Court", "District Court", "Gram Panchayat", "Election Commission"], "High Court", "judiciary"),
    q(2, "Which court can issue writs for more than only Fundamental Rights?", ["High Court", "Supreme Court only", "Lok Sabha", "State Election Commission"], "High Court", "judiciary"),
    q(2, "Which court supervises subordinate courts within a state?", ["High Court", "Supreme Court only", "Lokpal", "CAG"], "High Court", "judiciary"),
    q(2, "Which court is the final interpreter of the Constitution in India?", ["Supreme Court", "High Court only", "District Court", "Gram Nyayalaya"], "Supreme Court", "judiciary"),
    q(2, "Which state house can remove a state government through a confidence vote?", ["Vidhan Sabha", "Vidhan Parishad", "Rajya Sabha", "Gram Sabha"], "Vidhan Sabha", "state_government"),
    q(2, "Which state house is also called the Legislative Assembly?", ["Vidhan Sabha", "Vidhan Parishad", "Lok Sabha", "Municipal Council"], "Vidhan Sabha", "state_government"),
    q(2, "What is the usual name for a state's upper house?", ["Vidhan Parishad", "Vidhan Sabha", "Rajya Sabha", "Zila Parishad"], "Vidhan Parishad", "state_government"),
    q(2, "Which state office is similar to the President's constitutional role at Union level?", ["Governor", "Chief Minister", "Speaker", "Mayor"], "Governor", "state_government"),
    q(2, "Who is collectively responsible to the State Legislative Assembly?", ["State Council of Ministers", "High Court judges", "State Election Commission", "Municipal councillors"], "State Council of Ministers", "state_government"),
    q(2, "Which state official is the leader of the majority government in the Assembly?", ["Chief Minister", "Governor", "Advocate General", "Speaker only"], "Chief Minister", "state_government"),
    q(2, "Which state law officer is similar to the Attorney General at Union level?", ["Advocate General", "Solicitor General", "CAG", "Lokayukta"], "Advocate General", "state_government"),
    q(2, "Which body conducts elections to municipalities and Panchayats?", ["State Election Commission", "Election Commission of India", "UPSC", "Finance Commission"], "State Election Commission", "grassroots"),
    q(2, "Which schedule lists functions of municipalities?", ["Twelfth Schedule", "Eleventh Schedule", "Seventh Schedule", "Tenth Schedule"], "Twelfth Schedule", "grassroots"),
    q(2, "Which schedule lists functions of Panchayats?", ["Eleventh Schedule", "Twelfth Schedule", "Eighth Schedule", "First Schedule"], "Eleventh Schedule", "grassroots"),
    q(2, "Which amendment gave constitutional status to Panchayati Raj institutions?", ["73rd Amendment", "74th Amendment", "42nd Amendment", "52nd Amendment"], "73rd Amendment", "grassroots"),
    q(2, "Which amendment gave constitutional status to urban local bodies?", ["74th Amendment", "73rd Amendment", "61st Amendment", "86th Amendment"], "74th Amendment", "grassroots"),
    q(2, "Which local institution directly includes every registered voter in a village?", ["Gram Sabha", "Gram Panchayat", "Zila Parishad", "Block Samiti"], "Gram Sabha", "grassroots"),
    q(2, "Which urban body is usually responsible for local sanitation and roads?", ["Municipality", "Gram Sabha", "State Legislature", "High Court"], "Municipality", "grassroots"),
    q(2, "Which movement linked forest protection with local community rights?", ["Chipko Movement", "India Against Corruption", "Narmada Bachao Andolan", "Bhoodan Movement"], "Chipko Movement", "grassroots_movements"),
    q(2, "Which movement raised rehabilitation concerns around large dam projects?", ["Narmada Bachao Andolan", "Chipko Movement", "RTI movement", "Appiko Movement"], "Narmada Bachao Andolan", "grassroots_movements"),
    q(2, "Which grassroots campaign helped push the demand for an information law?", ["RTI movement", "Green Revolution", "White Revolution", "Quit India Movement"], "RTI movement", "grassroots_movements"),
    q(2, "Which movement is associated with non-violent anti-corruption protests for Lokpal?", ["India Against Corruption", "Chipko Movement", "Narmada Bachao Andolan", "Appiko Movement"], "India Against Corruption", "grassroots_movements"),

    q(3, "Which Preamble value is most directly tied to the absence of hereditary rule?", ["Republic", "Secular", "Socialist", "Fraternity"], "Republic", "constitutional_values"),
    q(3, "Which Preamble value is most directly tied to national independence in external affairs?", ["Sovereign", "Democratic", "Socialist", "Fraternity"], "Sovereign", "constitutional_values"),
    q(3, "Which constitutional value connects dignity of the individual with unity of the nation?", ["Fraternity", "Judicial review", "Collective responsibility", "Separation of powers"], "Fraternity", "constitutional_values"),
    q(3, "Which Fundamental Duty is most directly linked with rational public thinking?", ["Develop scientific temper", "Pay income tax only", "Vote in every election", "Join a political party"], "Develop scientific temper", "constitutional_values"),
    q(3, "Which Fundamental Duty is most directly linked with forests, lakes, rivers, and wildlife?", ["Protect the natural environment", "Obey a party whip", "File election expenses", "Attend Question Hour"], "Protect the natural environment", "constitutional_values"),
    q(3, "Which constitutional principle is a guide for lawmaking but not directly enforceable in court?", ["Directive Principle", "Fundamental Right", "Writ", "Election petition"], "Directive Principle", "constitutional_values"),
    q(3, "Which doctrine prevents even a constitutional amendment from destroying core constitutional features?", ["Basic structure doctrine", "Colourable legislation", "Collective responsibility", "Pleasure doctrine"], "Basic structure doctrine", "judiciary"),
    q(3, "Which case is the standard reference for the basic structure doctrine?", ["Kesavananda Bharati", "Shah Bano", "Vishaka", "Navtej Johar"], "Kesavananda Bharati", "judiciary"),
    q(3, "Which case reinforced the balance between Fundamental Rights and Directive Principles?", ["Minerva Mills", "S.R. Bommai", "Kihoto Hollohan", "Indra Sawhney"], "Minerva Mills", "judiciary"),
    q(3, "Which power lets High Courts protect legal rights beyond only Fundamental Rights?", ["Article 226 writ jurisdiction", "Article 32 only", "Money Bill certification", "Model Code enforcement"], "Article 226 writ jurisdiction", "judiciary"),
    q(3, "Which High Court power is most useful for challenging illegal state action?", ["Writ jurisdiction", "Budget approval", "Voter-list preparation", "Party recognition"], "Writ jurisdiction", "judiciary"),
    q(3, "Which court is usually approached first for many state-government service and local-authority disputes?", ["High Court", "Supreme Court only", "Lok Sabha", "GST Council"], "High Court", "judiciary"),
    q(3, "Which state office may invite a party leader to form government after an election?", ["Governor", "Speaker", "Advocate General", "State Election Commissioner"], "Governor", "state_government"),
    q(3, "Which state institution checks whether the ministry still enjoys Assembly confidence?", ["Vidhan Sabha", "Vidhan Parishad", "High Court", "State Election Commission"], "Vidhan Sabha", "state_government"),
    q(3, "Which house is permanent in some states and not directly elected in full?", ["Vidhan Parishad", "Vidhan Sabha", "Lok Sabha", "Gram Sabha"], "Vidhan Parishad", "state_government"),
    q(3, "Which law officer represents and advises the state government in legal matters?", ["Advocate General", "Attorney General", "Solicitor General", "CAG"], "Advocate General", "state_government"),
    q(3, "Which local institution is the strongest example of direct democracy in village governance?", ["Gram Sabha", "Rajya Sabha", "Vidhan Parishad", "Finance Commission"], "Gram Sabha", "grassroots"),
    q(3, "Which amendment is most tied to women's reservation in local bodies?", ["73rd and 74th Amendments", "42nd Amendment", "52nd Amendment", "101st Amendment"], "73rd and 74th Amendments", "grassroots"),
    q(3, "Which schedule is linked with subjects such as urban planning and public health in municipalities?", ["Twelfth Schedule", "Eleventh Schedule", "Seventh Schedule", "Ninth Schedule"], "Twelfth Schedule", "grassroots"),
    q(3, "Which schedule is linked with subjects such as agriculture and rural development for Panchayats?", ["Eleventh Schedule", "Twelfth Schedule", "Eighth Schedule", "Tenth Schedule"], "Eleventh Schedule", "grassroots"),
    q(3, "Which movement made environmental protection a grassroots democratic issue in the Himalayas?", ["Chipko Movement", "India Against Corruption", "Narmada Bachao Andolan", "Total Revolution"], "Chipko Movement", "grassroots_movements"),
    q(3, "Which movement connected dam development with rehabilitation and consent concerns?", ["Narmada Bachao Andolan", "Chipko Movement", "Appiko Movement", "White Revolution"], "Narmada Bachao Andolan", "grassroots_movements"),
    q(3, "Which grassroots demand turned government records into a citizen-access issue?", ["Right to Information", "Basic structure", "Money Bill", "Postal ballot"], "Right to Information", "grassroots_movements"),
    q(3, "Which anti-corruption movement helped popularize the demand for a Jan Lokpal?", ["India Against Corruption", "Chipko Movement", "Bhoodan Movement", "Narmada Bachao Andolan"], "India Against Corruption", "grassroots_movements"),
    q(3, "Which form of local participation lets citizens review works rather than only vote once in five years?", ["Gram Sabha oversight", "Rajya Sabha debate", "Cabinet secrecy", "Governor assent"], "Gram Sabha oversight", "grassroots"),
    q(3, "Which local unit is closest to urban residents for ward-level civic complaints?", ["Ward councillor", "Rajya Sabha MP", "Governor", "High Court registrar"], "Ward councillor", "grassroots"),
    q(3, "Which local-government idea means decisions should be made as close to citizens as possible?", ["Decentralisation", "Centralisation", "Ordinance rule", "Judicial appointment"], "Decentralisation", "grassroots"),
    q(3, "Which grassroots institution is meant to improve accountability of Panchayat spending?", ["Gram Sabha", "Vidhan Parishad", "Lok Sabha Secretariat", "Finance Commission"], "Gram Sabha", "grassroots"),
    q(3, "Which movement is a better example of environmental grassroots politics than electoral party politics?", ["Chipko Movement", "Question Hour", "Money Bill", "No-confidence motion"], "Chipko Movement", "grassroots_movements"),
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
        missing = {"id", "category", "difficulty", "question", "options", "correct_index"} - item.keys()
        if missing:
            raise ValueError(f"Missing {missing} in {item}")
        if item["category"] != "politics":
            raise ValueError(f"Wrong category in {item['id']}")
        if item["difficulty"] not in {1, 2, 3}:
            raise ValueError(f"Wrong difficulty in {item['id']}")
        if len(item["options"]) != 4:
            raise ValueError(f"Wrong option count in {item['id']}")
        if len(set(item["options"])) != 4:
            raise ValueError(f"Duplicate option in {item['id']}")
        if not 0 <= item["correct_index"] < 4:
            raise ValueError(f"Wrong correct_index in {item['id']}")


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
