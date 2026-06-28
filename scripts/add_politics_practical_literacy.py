#!/usr/bin/env python3
"""Add practical civics questions to the politics question bank."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "backend" / "app" / "data" / "gk_questions.json"
OUT_PATH = ROOT / "backend" / "app" / "data" / "politics_practical_literacy_generated_121.json"


DUPLICATE_REPLACEMENTS = {
    "pol_easy_181": {
        "question": "Which list must contain your name for you to vote at a polling booth?",
        "options": ["Electoral roll", "Income-tax return", "Passport register", "Driving-test list"],
        "correct_index": 0,
        "source_note": "politics_duplicate_rewrite",
    },
    "pol_easy_185": {
        "question": "Which tool lets a citizen ask a public authority for official records?",
        "options": ["RTI application", "Election manifesto", "Party whip", "Confidence motion"],
        "correct_index": 0,
        "source_note": "politics_duplicate_rewrite",
    },
    "pol_easy_187": {
        "question": "Which local body meeting lets village voters directly question Panchayat work?",
        "options": ["Gram Sabha", "Rajya Sabha", "Cabinet meeting", "Lok Sabha"],
        "correct_index": 0,
        "source_note": "politics_duplicate_rewrite",
    },
}


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
    q(1, "Which body conducts Lok Sabha and Assembly elections in India?", ["Election Commission of India", "Finance Commission", "NITI Aayog", "Central Vigilance Commission"], "Election Commission of India", "elections"),
    q(1, "What does NOTA allow a voter to record?", ["None of the above", "New transfer application", "Nomination to Assembly", "Notice of tax appeal"], "None of the above", "elections"),
    q(1, "Which machine records votes in most Indian polling booths?", ["EVM", "ATM", "GPS", "MRI"], "EVM", "elections"),
    q(1, "Which paper trail system helps voters verify the symbol they chose?", ["VVPAT", "EPFO", "CAG", "NCRB"], "VVPAT", "elections"),
    q(1, "Which document is commonly called the voter ID card?", ["EPIC", "PAN", "Aadhaar only", "Passport"], "EPIC", "elections"),
    q(1, "Which election rulebook starts after polls are announced?", ["Model Code of Conduct", "Civil Procedure Code", "Finance Bill", "Official Secrets Act"], "Model Code of Conduct", "elections"),
    q(1, "Who is the officer in charge of conducting an election in a constituency?", ["Returning Officer", "Comptroller", "Lokpal member", "Cabinet Secretary"], "Returning Officer", "elections"),
    q(1, "Which official list decides whether a person can vote in an election?", ["Electoral roll", "Census table", "Ration-card list", "Passport file"], "Electoral roll", "elections"),
    q(1, "Which body conducts Panchayat and municipal elections in a state?", ["State Election Commission", "Election Commission of India", "Union Public Service Commission", "Finance Ministry"], "State Election Commission", "elections"),
    q(1, "Which mark helps prevent a voter from voting twice?", ["Indelible ink", "Court stamp", "Revenue seal", "Police badge"], "Indelible ink", "elections"),
    q(1, "Which house is directly elected by Indian voters?", ["Lok Sabha", "Rajya Sabha", "Supreme Court", "NITI Aayog"], "Lok Sabha", "parliament"),
    q(1, "Which house represents the states in Parliament?", ["Rajya Sabha", "Lok Sabha", "Gram Sabha", "Municipal Council"], "Rajya Sabha", "parliament"),
    q(1, "Which officer presides over the Lok Sabha?", ["Speaker", "Governor", "Chief Election Commissioner", "CAG"], "Speaker", "parliament"),
    q(1, "Which parliamentary device lets MPs ask ministers about government work?", ["Question Hour", "Polling day", "Gram Sabha", "Cabinet oath"], "Question Hour", "parliament"),
    q(1, "Which vote tests whether the government still has majority support?", ["No-confidence motion", "Private member bill", "Adjournment list", "Starred question"], "No-confidence motion", "parliament"),
    q(1, "Which instruction tells party legislators how to vote in the House?", ["Whip", "Writ", "Ordinance", "Gazette"], "Whip", "parliament"),
    q(1, "Which bill deals mainly with taxation or government spending?", ["Money Bill", "Private Bill", "Local Bill", "Ordinary notice"], "Money Bill", "parliament"),
    q(1, "Which head of government leads a state council of ministers?", ["Chief Minister", "Governor", "Mayor", "Speaker"], "Chief Minister", "executive"),
    q(1, "Which constitutional head formally appoints a state Chief Minister?", ["Governor", "Mayor", "CAG", "Lokpal"], "Governor", "executive"),
    q(1, "Which temporary law can the President issue when Parliament is not in session?", ["Ordinance", "Manifesto", "White paper", "Election symbol"], "Ordinance", "executive"),
    q(1, "Which village forum includes all registered voters of that village?", ["Gram Sabha", "Rajya Sabha", "Cabinet", "High Court"], "Gram Sabha", "local_government"),
    q(1, "Who is usually the elected head of a Gram Panchayat?", ["Sarpanch", "Speaker", "Governor", "CAG"], "Sarpanch", "local_government"),
    q(1, "Who represents a city ward in a municipal body?", ["Councillor", "MP only", "Governor", "Comptroller"], "Councillor", "local_government"),
    q(1, "Who is the political head of many municipal corporations?", ["Mayor", "Sarpanch", "President of India", "Chief Justice"], "Mayor", "local_government"),
    q(1, "Which body is closest to ordinary village-level local government?", ["Gram Panchayat", "Rajya Sabha", "Finance Commission", "Supreme Court"], "Gram Panchayat", "local_government"),
    q(1, "Which law is used to request information from a public authority?", ["RTI Act", "Companies Act", "Arms Act", "Forest Act"], "RTI Act", "citizen_rights"),
    q(1, "Who is the first officer a citizen usually approaches under RTI?", ["Public Information Officer", "Returning Officer", "Police Commissioner", "Speaker"], "Public Information Officer", "citizen_rights"),
    q(1, "Which body hears second appeals under central RTI matters?", ["Central Information Commission", "Finance Commission", "Election Commission", "Planning Commission"], "Central Information Commission", "citizen_rights"),
    q(1, "Which court order is used to produce a detained person before court?", ["Habeas corpus", "Mandamus", "Certiorari", "Quo warranto"], "Habeas corpus", "citizen_rights"),
    q(1, "Which legal action can raise a public-interest issue in court?", ["PIL", "MCC", "EPIC", "VVPAT"], "PIL", "citizen_rights"),
    q(1, "Which body audits Union and state government accounts?", ["CAG", "UPSC", "NHRC", "CVC"], "CAG", "institutions"),
    q(1, "Which body investigates human-rights complaints in India?", ["NHRC", "CAG", "UPSC", "GST Council"], "NHRC", "institutions"),
    q(1, "Which body recruits civil servants through national competitive exams?", ["UPSC", "CAG", "Lokpal", "Finance Commission"], "UPSC", "institutions"),
    q(1, "Which anti-corruption ombudsman handles complaints against many central public officials?", ["Lokpal", "Governor", "Speaker", "Mayor"], "Lokpal", "institutions"),
    q(1, "Which body deals with vigilance and corruption-prevention in central government organizations?", ["CVC", "CAG", "NHRC", "SEC"], "CVC", "institutions"),
    q(1, "Which council brings the Union and states together for GST decisions?", ["GST Council", "NITI Aayog", "Lokpal", "National Security Council"], "GST Council", "federalism"),
    q(1, "Which schedule divides subjects into Union, State, and Concurrent lists?", ["Seventh Schedule", "Tenth Schedule", "Eighth Schedule", "First Schedule"], "Seventh Schedule", "federalism"),
    q(1, "Which list contains subjects mainly handled by state governments?", ["State List", "Union List", "Concurrent List", "Residuary List"], "State List", "federalism"),
    q(1, "Which list contains subjects on which both Union and states can legislate?", ["Concurrent List", "Union List only", "State List only", "Eighth Schedule"], "Concurrent List", "federalism"),
    q(1, "Which principle means India has both Union and state governments?", ["Federalism", "Monarchy", "Apartheid", "Colonial rule"], "Federalism", "federalism"),

    q(2, "What should a voter check before polling day to avoid being turned away?", ["Name in electoral roll", "Income-tax bracket", "Passport expiry", "Vehicle insurance"], "Name in electoral roll", "elections"),
    q(2, "What is the main purpose of VVPAT in elections?", ["Let voters verify the recorded choice", "Count income tax", "Issue voter ID cards", "Register political parties"], "Let voters verify the recorded choice", "elections"),
    q(2, "What does the Model Code of Conduct mainly try to ensure?", ["Fair election campaigning", "Faster tax refunds", "Court vacation schedule", "Bank interest rates"], "Fair election campaigning", "elections"),
    q(2, "Which officer usually accepts candidate nomination papers in a constituency?", ["Returning Officer", "Presiding Judge", "Gram Sachiv", "Cabinet Secretary"], "Returning Officer", "elections"),
    q(2, "Which poll official manages the actual polling station on voting day?", ["Presiding Officer", "Lokpal Chairperson", "Attorney General", "Mayor"], "Presiding Officer", "elections"),
    q(2, "Which election record is revised to add, delete, or correct voter names?", ["Electoral roll", "Budget speech", "Court diary", "Census slogan"], "Electoral roll", "elections"),
    q(2, "Which body recognizes national and state political parties?", ["Election Commission of India", "Supreme Court registry", "Finance Commission", "CAG"], "Election Commission of India", "elections"),
    q(2, "Which symbol-related job belongs to the Election Commission?", ["Allotting election symbols", "Approving police uniforms", "Printing currency notes", "Naming highways"], "Allotting election symbols", "elections"),
    q(2, "Which option is meant for voters who reject all listed candidates?", ["NOTA", "Postal ballot", "Tendered vote", "Proxy vote"], "NOTA", "elections"),
    q(2, "Which system is meant for some voters who cannot vote at their polling station?", ["Postal ballot", "Question Hour", "Money Bill", "Gram Sabha"], "Postal ballot", "elections"),
    q(2, "What is the main purpose of Question Hour?", ["Holding ministers accountable", "Electing the Speaker", "Passing only budgets", "Selecting judges"], "Holding ministers accountable", "parliament"),
    q(2, "What is Zero Hour used for in Parliament?", ["Raising urgent public matters", "Counting votes", "Administering oaths only", "Approving voter IDs"], "Raising urgent public matters", "parliament"),
    q(2, "Which committee examines CAG audit reports?", ["Public Accounts Committee", "Business Advisory Committee", "Rules Committee", "Ethics Committee only"], "Public Accounts Committee", "parliament"),
    q(2, "What does a party whip mainly enforce?", ["Party voting discipline", "Election counting", "Judicial review", "Census collection"], "Party voting discipline", "parliament"),
    q(2, "Who certifies whether a bill is a Money Bill in Lok Sabha?", ["Speaker", "President", "CAG", "Chief Election Commissioner"], "Speaker", "parliament"),
    q(2, "Which bill is introduced by an MP who is not a minister?", ["Private member bill", "Money Bill", "Appropriation Bill", "Finance Bill only"], "Private member bill", "parliament"),
    q(2, "Which motion can force a government to prove its majority?", ["No-confidence motion", "Calling attention notice", "Zero Hour mention", "Adjournment for lunch"], "No-confidence motion", "parliament"),
    q(2, "Which parliamentary question expects an oral answer and follow-up questions?", ["Starred question", "Unstarred question", "Short title", "White paper"], "Starred question", "parliament"),
    q(2, "Which parliamentary question usually receives a written answer?", ["Unstarred question", "Starred question", "Confidence motion", "Appropriation demand"], "Unstarred question", "parliament"),
    q(2, "What is the main role of parliamentary committees?", ["Detailed scrutiny of work and bills", "Running polling booths", "Appointing governors", "Issuing voter IDs"], "Detailed scrutiny of work and bills", "parliament"),
    q(2, "Which local body should a villager attend to question Panchayat spending?", ["Gram Sabha", "Rajya Sabha", "GST Council", "Public Accounts Committee"], "Gram Sabha", "local_government"),
    q(2, "Which representative is the closest elected contact for a city ward issue?", ["Ward councillor", "Rajya Sabha MP", "Governor", "CAG"], "Ward councillor", "local_government"),
    q(2, "Which local body handles urban services such as streetlights and local roads?", ["Municipality", "Rajya Sabha", "Election Commission", "Supreme Court"], "Municipality", "local_government"),
    q(2, "Which village-level plan is most directly discussed by local voters?", ["Gram Panchayat work plan", "Union Budget", "Supreme Court roster", "Foreign treaty"], "Gram Panchayat work plan", "local_government"),
    q(2, "Which level is most directly linked with a district collector's administration?", ["District", "Ward only", "Parliament only", "Supreme Court bench"], "District", "local_government"),
    q(2, "What is the first appeal under RTI used for?", ["Challenging a poor or missing PIO reply", "Changing a vote after polling", "Appealing a cricket score", "Approving a Budget"], "Challenging a poor or missing PIO reply", "citizen_rights"),
    q(2, "Which RTI officer is responsible for giving information held by a public authority?", ["PIO", "Returning Officer", "CAG", "Mayor"], "PIO", "citizen_rights"),
    q(2, "What is the normal RTI response deadline for most requests?", ["30 days", "24 hours", "6 months", "5 years"], "30 days", "citizen_rights"),
    q(2, "Which RTI deadline applies when life or liberty is involved?", ["48 hours", "30 days", "90 days", "One year"], "48 hours", "citizen_rights"),
    q(2, "Which court tool can order a public official to perform a legal duty?", ["Mandamus", "Habeas corpus", "Bail bond", "Manifesto"], "Mandamus", "citizen_rights"),
    q(2, "Which court tool questions a person's legal authority to hold public office?", ["Quo warranto", "Certiorari", "Habeas corpus", "Postal ballot"], "Quo warranto", "citizen_rights"),
    q(2, "Which writ is most directly linked to unlawful detention?", ["Habeas corpus", "Mandamus", "Prohibition", "Quo warranto"], "Habeas corpus", "citizen_rights"),
    q(2, "Which case is best known for recognizing privacy as a fundamental right?", ["Puttaswamy case", "Shah Bano case", "Bommai case", "Kesavananda case"], "Puttaswamy case", "citizen_rights"),
    q(2, "Which legal route is used when a larger public wrong needs court attention?", ["Public Interest Litigation", "Private election symbol", "Cabinet note", "Party whip"], "Public Interest Litigation", "citizen_rights"),
    q(2, "Which institution audits government receipts and spending?", ["CAG", "CVC", "UPSC", "NHRC"], "CAG", "institutions"),
    q(2, "Which institution is linked to anti-corruption vigilance in Union government bodies?", ["CVC", "CAG", "UPSC", "Finance Commission"], "CVC", "institutions"),
    q(2, "Which institution examines complaints of human-rights violations?", ["NHRC", "UPSC", "GST Council", "CAG"], "NHRC", "institutions"),
    q(2, "Which institution selects candidates for civil services exams?", ["UPSC", "Lokpal", "CVC", "Election Commission"], "UPSC", "institutions"),
    q(2, "Which institution recommends sharing Union taxes with states?", ["Finance Commission", "CVC", "UPSC", "NHRC"], "Finance Commission", "institutions"),
    q(2, "Which institution is India's central anti-corruption ombudsman?", ["Lokpal", "CAG", "UPSC", "GST Council"], "Lokpal", "institutions"),
    q(2, "Which state-level ombudsman is the counterpart of Lokpal?", ["Lokayukta", "Mayor", "Speaker", "Returning Officer"], "Lokayukta", "institutions"),
    q(2, "Which body is chaired by the Union Finance Minister for GST decisions?", ["GST Council", "Election Commission", "NHRC", "CVC"], "GST Council", "federalism"),
    q(2, "Which list gives Parliament exclusive lawmaking power over defence?", ["Union List", "State List", "Concurrent List", "Municipal List"], "Union List", "federalism"),
    q(2, "Which list includes subjects where both Parliament and states can make laws?", ["Concurrent List", "Union List only", "State List only", "Eighth Schedule"], "Concurrent List", "federalism"),
    q(2, "Which schedule is central to understanding Centre-state subject division?", ["Seventh Schedule", "Tenth Schedule", "Twelfth Schedule", "Eighth Schedule"], "Seventh Schedule", "federalism"),
    q(2, "Which reform reserved one-third seats for women in Panchayats and municipalities?", ["73rd and 74th Amendments", "42nd Amendment", "52nd Amendment", "101st Amendment"], "73rd and 74th Amendments", "local_government"),

    q(3, "Which election role is responsible for counting and declaring the result in a constituency?", ["Returning Officer", "Presiding Officer", "Polling Agent", "Booth Level Officer"], "Returning Officer", "elections"),
    q(3, "Which official is the best local contact for voter-list correction at booth level?", ["Booth Level Officer", "CAG auditor", "Lokpal registrar", "Cabinet Secretary"], "Booth Level Officer", "elections"),
    q(3, "Which vote type is used if someone's vote has already been wrongly cast by another person?", ["Tendered vote", "Postal ballot", "Proxy vote", "NOTA"], "Tendered vote", "elections"),
    q(3, "Which election document records the order and symbols of contesting candidates?", ["Ballot paper", "Union Budget", "CAG report", "Court decree"], "Ballot paper", "elections"),
    q(3, "Which polling-station role verifies voters before they cast votes?", ["Polling Officer", "Lokpal member", "Mayor", "CAG"], "Polling Officer", "elections"),
    q(3, "Which election complaint is most directly linked to misuse of official machinery?", ["MCC violation", "RTI first appeal", "Money Bill dispute", "CAG audit para"], "MCC violation", "elections"),
    q(3, "Which official appoints polling personnel at district level during elections?", ["District Election Officer", "Speaker", "Chief Justice", "Finance Secretary"], "District Election Officer", "elections"),
    q(3, "Which parliamentary device lets MPs seek urgent ministerial attention to a public issue?", ["Calling attention", "Postal ballot", "VVPAT slip", "Tendered vote"], "Calling attention", "parliament"),
    q(3, "Which committee is most associated with examining government spending after CAG audit?", ["Public Accounts Committee", "Estimates Committee", "Rules Committee", "Privileges Committee"], "Public Accounts Committee", "parliament"),
    q(3, "Which committee examines whether government funds were spent as Parliament approved?", ["Public Accounts Committee", "Ethics Committee", "House Committee", "Library Committee"], "Public Accounts Committee", "parliament"),
    q(3, "Which device can punish a legislator for defying a party line in key votes?", ["Anti-defection law", "RTI Act", "Model Code only", "Finance Commission order"], "Anti-defection law", "parliament"),
    q(3, "Which schedule contains India's anti-defection provisions?", ["Tenth Schedule", "Seventh Schedule", "Eighth Schedule", "Twelfth Schedule"], "Tenth Schedule", "parliament"),
    q(3, "Which situation most clearly tests collective responsibility of the cabinet?", ["No-confidence motion", "Starred question", "Zero Hour mention", "Private member resolution"], "No-confidence motion", "parliament"),
    q(3, "Which type of question allows supplementary questions in Parliament?", ["Starred question", "Unstarred question", "Short title", "Gazette question"], "Starred question", "parliament"),
    q(3, "Which House has limited power over a certified Money Bill?", ["Rajya Sabha", "Lok Sabha", "Gram Sabha", "GST Council"], "Rajya Sabha", "parliament"),
    q(3, "Which urban representative should a resident approach first for a broken streetlight in a ward?", ["Ward councillor", "Rajya Sabha MP", "Governor", "Lokpal"], "Ward councillor", "local_government"),
    q(3, "Which local meeting is meant to approve and review Panchayat-level work?", ["Gram Sabha", "Cabinet meeting", "Rajya Sabha session", "Finance Commission hearing"], "Gram Sabha", "local_government"),
    q(3, "Which urban body is usually responsible for local sanitation and municipal roads?", ["Municipal corporation", "Supreme Court", "Election Commission", "Rajya Sabha"], "Municipal corporation", "local_government"),
    q(3, "Which amendment is most directly linked with Panchayati Raj institutions?", ["73rd Amendment", "42nd Amendment", "52nd Amendment", "101st Amendment"], "73rd Amendment", "local_government"),
    q(3, "Which amendment is most directly linked with urban local bodies?", ["74th Amendment", "44th Amendment", "61st Amendment", "86th Amendment"], "74th Amendment", "local_government"),
    q(3, "Which RTI appeal goes to the Information Commission after the first appeal fails?", ["Second appeal", "Curative petition", "Postal ballot", "Confidence motion"], "Second appeal", "citizen_rights"),
    q(3, "Which public authority officer can face penalty for wrongly denying RTI information?", ["PIO", "Returning Officer only", "Mayor only", "Party whip"], "PIO", "citizen_rights"),
    q(3, "Which writ stops a lower court or tribunal from exceeding its jurisdiction?", ["Prohibition", "Habeas corpus", "Mandamus", "Quo warranto"], "Prohibition", "citizen_rights"),
    q(3, "Which writ can quash an order of a lower court or tribunal?", ["Certiorari", "Habeas corpus", "Mandamus", "Quo warranto"], "Certiorari", "citizen_rights"),
    q(3, "Which writ tells a public authority to do what the law requires?", ["Mandamus", "Habeas corpus", "Certiorari", "Prohibition"], "Mandamus", "citizen_rights"),
    q(3, "Which case is most linked with basic structure doctrine?", ["Kesavananda Bharati", "Vishaka", "Shah Bano", "Navtej Johar"], "Kesavananda Bharati", "citizen_rights"),
    q(3, "Which case is most linked with Centre-state misuse of President's Rule?", ["S.R. Bommai", "Puttaswamy", "Maneka Gandhi", "Vishaka"], "S.R. Bommai", "federalism"),
    q(3, "Which institution's reports are examined by the Public Accounts Committee?", ["CAG", "NHRC", "UPSC", "Election Commission"], "CAG", "institutions"),
    q(3, "Which body is often called the integrity institution for central vigilance?", ["CVC", "Finance Commission", "UPSC", "State Election Commission"], "CVC", "institutions"),
    q(3, "Which body can inquire into human-rights violations by public servants?", ["NHRC", "CAG", "UPSC", "GST Council"], "NHRC", "institutions"),
    q(3, "Which body conducts exams such as Civil Services and Engineering Services?", ["UPSC", "CAG", "CVC", "Lokayukta"], "UPSC", "institutions"),
    q(3, "Which constitutional body recommends tax devolution between Union and states?", ["Finance Commission", "GST Council", "Election Commission", "Planning Commission"], "Finance Commission", "institutions"),
    q(3, "Which body is the best fit for complaints against central public servants for corruption?", ["Lokpal", "Finance Commission", "NHRC", "Rajya Sabha Secretariat"], "Lokpal", "institutions"),
    q(3, "Which council embodies cooperative federalism in indirect-tax decisions?", ["GST Council", "CVC", "UPSC", "CAG"], "GST Council", "federalism"),
    q(3, "Which subject-list conflict is settled by giving Union law priority in many Concurrent List cases?", ["Concurrent List conflict", "Eighth Schedule listing", "Party-symbol dispute", "Voter-ID correction"], "Concurrent List conflict", "federalism"),
]


OPTION_REVISIONS = {
    "What does NOTA allow a voter to record?": ["None of the above", "Postal ballot", "Tendered vote", "Rejected nomination"],
    "Which machine records votes in most Indian polling booths?": ["EVM", "VVPAT", "Ballot unit only", "Postal ballot"],
    "Which paper trail system helps voters verify the symbol they chose?": ["VVPAT", "EVM control unit", "Postal ballot", "Electoral roll"],
    "Which election rulebook starts after polls are announced?": ["Model Code of Conduct", "Representation petition", "Election manifesto", "Voter-list revision"],
    "Who is the officer in charge of conducting an election in a constituency?": ["Returning Officer", "Presiding Officer", "Booth Level Officer", "Polling Agent"],
    "Which official list decides whether a person can vote in an election?": ["Electoral roll", "Voter slip", "EPIC database", "Candidate list"],
    "Which mark helps prevent a voter from voting twice?": ["Indelible ink", "VVPAT slip", "Polling stamp", "Voter slip"],
    "Which house is directly elected by Indian voters?": ["Lok Sabha", "Rajya Sabha", "State Legislative Council", "Gram Sabha"],
    "Which officer presides over the Lok Sabha?": ["Speaker", "Deputy Chairman", "President", "Leader of the House"],
    "Which parliamentary device lets MPs ask ministers about government work?": ["Question Hour", "Zero Hour", "Calling attention", "Private member business"],
    "Which vote tests whether the government still has majority support?": ["No-confidence motion", "Confidence motion", "Censure motion", "Adjournment motion"],
    "Which instruction tells party legislators how to vote in the House?": ["Whip", "Writ", "Notice", "Motion"],
    "Which temporary law can the President issue when Parliament is not in session?": ["Ordinance", "Rule", "Resolution", "Notification"],
    "Which village forum includes all registered voters of that village?": ["Gram Sabha", "Gram Panchayat", "Ward Committee", "Block Samiti"],
    "Who is usually the elected head of a Gram Panchayat?": ["Sarpanch", "Ward councillor", "Mayor", "Block officer"],
    "Who represents a city ward in a municipal body?": ["Councillor", "Mayor", "Sarpanch", "MLA"],
    "Who is the political head of many municipal corporations?": ["Mayor", "Municipal Commissioner", "Ward councillor", "District Collector"],
    "Which body is closest to ordinary village-level local government?": ["Gram Panchayat", "Block Samiti", "Zila Parishad", "Municipal Council"],
    "Which legal action can raise a public-interest issue in court?": ["PIL", "Writ petition", "RTI appeal", "Election petition"],
    "What should a voter check before polling day to avoid being turned away?": ["Name in electoral roll", "EPIC number only", "Polling-agent list", "Candidate affidavit"],
    "What is the main purpose of VVPAT in elections?": ["Let voters verify the recorded choice", "Replace the EVM entirely", "Register new voters", "Allot election symbols"],
    "What does the Model Code of Conduct mainly try to ensure?": ["Fair election campaigning", "Final voter-list revision", "Counting of postal ballots", "Candidate nomination scrutiny"],
    "Which officer usually accepts candidate nomination papers in a constituency?": ["Returning Officer", "Presiding Officer", "Booth Level Officer", "Counting Supervisor"],
    "Which poll official manages the actual polling station on voting day?": ["Presiding Officer", "Returning Officer", "Booth Level Officer", "Counting Observer"],
    "Which election record is revised to add, delete, or correct voter names?": ["Electoral roll", "Candidate affidavit", "Result sheet", "Polling diary"],
    "Which symbol-related job belongs to the Election Commission?": ["Allotting election symbols", "Approving party manifestos", "Printing voter slips only", "Counting VVPAT slips"],
    "Which system is meant for some voters who cannot vote at their polling station?": ["Postal ballot", "Tendered vote", "NOTA", "Proxy vote"],
    "What is Zero Hour used for in Parliament?": ["Raising urgent public matters", "Asking listed oral questions", "Voting on Money Bills only", "Electing the Speaker"],
    "What does a party whip mainly enforce?": ["Party voting discipline", "Question Hour order", "Committee witness summons", "Budget speech timing"],
    "Which local body handles urban services such as streetlights and local roads?": ["Municipality", "Gram Panchayat", "Zila Parishad", "State Election Commission"],
    "Which level is most directly linked with a district collector's administration?": ["District", "Ward", "Block only", "Parliamentary session"],
    "What is the first appeal under RTI used for?": ["Challenging a poor or missing PIO reply", "Appealing election results", "Seeking bail from a court", "Changing a party whip"],
    "Which RTI officer is responsible for giving information held by a public authority?": ["PIO", "First Appellate Authority", "Information Commissioner", "Public Prosecutor"],
    "Which legal route is used when a larger public wrong needs court attention?": ["Public Interest Litigation", "RTI first appeal", "Election petition", "Privilege motion"],
    "Which state-level ombudsman is the counterpart of Lokpal?": ["Lokayukta", "CVC", "CAG", "State Election Commissioner"],
    "Which official is the best local contact for voter-list correction at booth level?": ["Booth Level Officer", "Presiding Officer", "Polling Agent", "Counting Observer"],
    "Which election document records the order and symbols of contesting candidates?": ["Ballot paper", "Electoral roll", "Voter slip", "Candidate affidavit"],
    "Which polling-station role verifies voters before they cast votes?": ["Polling Officer", "Presiding Officer", "Polling Agent", "Counting Supervisor"],
    "Which election complaint is most directly linked to misuse of official machinery?": ["MCC violation", "Election petition", "RTI first appeal", "Candidate affidavit defect"],
    "Which official appoints polling personnel at district level during elections?": ["District Election Officer", "Returning Officer", "Presiding Officer", "Booth Level Officer"],
    "Which parliamentary device lets MPs seek urgent ministerial attention to a public issue?": ["Calling attention", "Zero Hour", "Starred question", "Privilege motion"],
    "Which urban representative should a resident approach first for a broken streetlight in a ward?": ["Ward councillor", "Mayor", "Municipal Commissioner", "MLA"],
    "Which local meeting is meant to approve and review Panchayat-level work?": ["Gram Sabha", "Gram Panchayat", "Block Samiti", "Zila Parishad"],
}


def apply_replacements(bank: list[dict]) -> None:
    for item in bank:
        patch = DUPLICATE_REPLACEMENTS.get(item.get("id"))
        if patch:
            item.update(patch)
        revised_options = OPTION_REVISIONS.get(item.get("question"))
        if revised_options:
            correct = item["options"][item["correct_index"]]
            item["options"] = revised_options
            item["correct_index"] = revised_options.index(correct)


def apply_option_revisions(questions: list[dict]) -> None:
    for item in questions:
        revised_options = OPTION_REVISIONS.get(item.get("question"))
        if revised_options:
            correct = item["options"][item["correct_index"]]
            item["options"] = revised_options
            item["correct_index"] = revised_options.index(correct)


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
    apply_replacements(bank)

    wanted_texts = {item["question"] for item in QUESTIONS}
    existing_texts = {item.get("question") for item in bank}
    pending = [item for item in QUESTIONS if item["question"] not in existing_texts]

    if not pending:
        already_present = [item for item in bank if item.get("question") in wanted_texts]
        apply_option_revisions(already_present)
        OUT_PATH.write_text(json.dumps(already_present, indent=2) + "\n")
        BANK_PATH.write_text(json.dumps(bank, indent=2) + "\n")
        print(f"generated=0 already_present={len(already_present)} total={len(bank)} out={OUT_PATH}")
        return

    generated = assign_ids(pending, bank)
    apply_option_revisions(generated)
    validate(generated, bank)
    OUT_PATH.write_text(json.dumps(generated, indent=2) + "\n")
    bank.extend(generated)
    BANK_PATH.write_text(json.dumps(bank, indent=2) + "\n")
    print(f"generated={len(generated)} total={len(bank)} out={OUT_PATH}")


if __name__ == "__main__":
    main()
