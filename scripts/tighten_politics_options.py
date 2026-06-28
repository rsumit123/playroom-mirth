#!/usr/bin/env python3
"""Tighten distractors in recently generated politics batches."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / "backend" / "app" / "data" / "gk_questions.json",
    ROOT / "backend" / "app" / "data" / "politics_practical_literacy_generated_121.json",
    ROOT / "backend" / "app" / "data" / "politics_constitution_grassroots_generated_95.json",
]


REVISIONS = {
    "Which constitutional head formally appoints a state Chief Minister?": ["Governor", "President", "Speaker", "Chief Justice of High Court"],
    "Which anti-corruption ombudsman handles complaints against many central public officials?": ["Lokpal", "Lokayukta", "CVC", "CBI"],
    "Which council brings the Union and states together for GST decisions?": ["GST Council", "Finance Commission", "Inter-State Council", "NITI Aayog Governing Council"],
    "Which body recognizes national and state political parties?": ["Election Commission of India", "State Election Commission", "Registrar of Societies", "Ministry of Law and Justice"],
    "What is the main role of parliamentary committees?": ["Detailed scrutiny of work and bills", "Questioning ministers in Question Hour", "Certifying Money Bills", "Issuing party whips"],
    "Which local body should a villager attend to question Panchayat spending?": ["Gram Sabha", "Gram Panchayat", "Block Samiti", "Zila Parishad"],
    "Which representative is the closest elected contact for a city ward issue?": ["Ward councillor", "Mayor", "Municipal Commissioner", "MLA"],
    "Which institution is India's central anti-corruption ombudsman?": ["Lokpal", "Lokayukta", "CVC", "CBI"],
    "Which House has limited power over a certified Money Bill?": ["Rajya Sabha", "Lok Sabha", "State Legislative Council", "Joint sitting"],
    "Which constitutional idea promotes brotherhood among citizens?": ["Fraternity", "Liberty", "Equality", "Secularism"],
    "Which constitutional duties apply mainly to citizens?": ["Fundamental Duties", "Fundamental Rights", "Directive Principles", "Constitutional remedies"],
    "Which constitutional principles guide the State in making social-welfare laws?": ["Directive Principles", "Fundamental Rights", "Fundamental Duties", "Basic structure"],
    "Which constitutional idea lets courts check whether a law violates the Constitution?": ["Judicial review", "Basic structure", "Writ jurisdiction", "Separation of powers"],
    "Which doctrine says Parliament cannot destroy the Constitution's core identity?": ["Basic structure doctrine", "Judicial review", "Separation of powers", "Collective responsibility"],
    "Which court hears many appeals from district courts in a state?": ["High Court", "District Court", "Sessions Court", "Supreme Court"],
    "Which body advises the Governor through the Chief Minister?": ["State Council of Ministers", "State Cabinet Secretariat", "Legislative Assembly", "Advocate General's office"],
    "Which local forum lets village voters directly review Panchayat work?": ["Gram Sabha", "Gram Panchayat", "Block Samiti", "Zila Parishad"],
    "Which local body handles village-level development work?": ["Gram Panchayat", "Gram Sabha", "Block Samiti", "Zila Parishad"],
    "Which elected representative handles many ward-level city issues?": ["Ward councillor", "Mayor", "Municipal Commissioner", "MLA"],
    "Which movement is famous for villagers hugging trees to prevent felling?": ["Chipko Movement", "Appiko Movement", "Narmada Bachao Andolan", "Silent Valley movement"],
    "Which local groups often help rural women save and borrow small amounts together?": ["Self-help groups", "Cooperative societies", "Gram Sabhas", "Ward committees"],
    "Which local system gives citizens a direct voice in village development?": ["Gram Sabha participation", "Social audit meeting", "Panchayat standing committee", "Ward committee"],
    "Which duty asks citizens to develop scientific temper?": ["Fundamental Duty", "Directive Principle", "Fundamental Right", "Constitutional convention"],
    "Which duty asks citizens to protect the natural environment?": ["Fundamental Duty", "Directive Principle", "Fundamental Right", "State List subject"],
    "Which power lets courts strike down unconstitutional laws?": ["Judicial review", "Writ jurisdiction", "Basic structure doctrine", "Curative jurisdiction"],
    "Which court can issue writs under Article 226?": ["High Court", "Supreme Court", "District Court", "Tribunal"],
    "Which court can issue writs for more than only Fundamental Rights?": ["High Court", "Supreme Court", "District Court", "Lok Adalat"],
    "Which court supervises subordinate courts within a state?": ["High Court", "Supreme Court", "District Court", "State Law Department"],
    "Which court is the final interpreter of the Constitution in India?": ["Supreme Court", "High Court", "Constitution Bench only", "President"],
    "Which state office is similar to the President's constitutional role at Union level?": ["Governor", "Chief Minister", "Speaker", "Advocate General"],
    "Who is collectively responsible to the State Legislative Assembly?": ["State Council of Ministers", "Chief Minister alone", "Governor's Secretariat", "Advocate General's office"],
    "Which state official is the leader of the majority government in the Assembly?": ["Chief Minister", "Governor", "Speaker", "Leader of Opposition"],
    "Which state law officer is similar to the Attorney General at Union level?": ["Advocate General", "Solicitor General", "Law Secretary", "Public Prosecutor"],
    "Which urban body is usually responsible for local sanitation and roads?": ["Municipality", "Municipal corporation", "Ward committee", "Development authority"],
    "Which grassroots campaign helped push the demand for an information law?": ["RTI movement", "Mazdoor Kisan Shakti Sangathan campaign", "Jan Lokpal movement", "Social audit movement"],
    "Which Fundamental Duty is most directly linked with forests, lakes, rivers, and wildlife?": ["Protect the natural environment", "Develop scientific temper", "Safeguard public property", "Promote harmony"],
    "Which power lets High Courts protect legal rights beyond only Fundamental Rights?": ["Article 226 writ jurisdiction", "Article 32 writ jurisdiction", "Supervisory jurisdiction", "Appellate jurisdiction"],
    "Which court is usually approached first for many state-government service and local-authority disputes?": ["High Court", "Administrative tribunal", "District Court", "Supreme Court"],
    "Which state office may invite a party leader to form government after an election?": ["Governor", "Speaker", "Chief Minister", "Election Commissioner"],
    "Which state institution checks whether the ministry still enjoys Assembly confidence?": ["Vidhan Sabha", "Vidhan Parishad", "Governor", "Speaker"],
    "Which law officer represents and advises the state government in legal matters?": ["Advocate General", "Attorney General", "Solicitor General", "Public Prosecutor"],
    "Which movement connected dam development with rehabilitation and consent concerns?": ["Narmada Bachao Andolan", "Chipko Movement", "Appiko Movement", "Silent Valley movement"],
    "Which grassroots demand turned government records into a citizen-access issue?": ["Right to Information", "Social audit", "Public hearing", "Citizen charter"],
    "Which form of local participation lets citizens review works rather than only vote once in five years?": ["Gram Sabha oversight", "Social audit", "Ward committee review", "Panchayat committee review"],
    "Which local unit is closest to urban residents for ward-level civic complaints?": ["Ward councillor", "Mayor", "Municipal Commissioner", "Ward committee"],
    "Which local-government idea means decisions should be made as close to citizens as possible?": ["Decentralisation", "Devolution", "Subsidiarity", "Local self-government"],
    "Which movement is a better example of environmental grassroots politics than electoral party politics?": ["Chipko Movement", "Appiko Movement", "Narmada Bachao Andolan", "Silent Valley movement"],
}


def tighten_file(path: Path) -> int:
    if not path.exists():
        return 0
    data = json.loads(path.read_text())
    changed = 0
    for item in data:
        revised = REVISIONS.get(item.get("question"))
        if not revised:
            continue
        correct = item["options"][item["correct_index"]]
        if correct not in revised:
            raise ValueError(f"Correct answer missing for {item['id']}: {correct}")
        if item["options"] != revised:
            item["options"] = revised
            item["correct_index"] = revised.index(correct)
            changed += 1
    if changed:
        path.write_text(json.dumps(data, indent=2) + "\n")
    return changed


def main() -> None:
    for path in FILES:
        print(path.relative_to(ROOT), tighten_file(path))


if __name__ == "__main__":
    main()
