#!/usr/bin/env python3
"""Regenerate Indian Law trivia without near-duplicate template variants.

This script intentionally uses one question per fact/concept. It replaces the
previous batch where many entries repeated the same answer with light rewording.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "backend/app/data/indian_law_generated_500.json"
BANK = ROOT / "backend/app/data/gk_questions.json"


def choose_options(answer: str, pool: list[str], salt: int) -> tuple[list[str], int]:
    distractors = [item for item in pool if item != answer]
    if len(distractors) < 3:
        raise ValueError(f"Not enough distractors for {answer}")
    start = salt % len(distractors)
    picked: list[str] = []
    i = start
    while len(picked) < 3:
        item = distractors[i % len(distractors)]
        if item not in picked:
            picked.append(item)
        i += 7
    insert_at = salt % 4
    options = picked[:]
    options.insert(insert_at, answer)
    return options, insert_at


ARTICLE_FACTS = [
    ("1", "name and territory of the Union", 1),
    ("3", "formation of new States and alteration of areas or names", 2),
    ("12", "definition of State for fundamental rights", 2),
    ("13", "laws inconsistent with fundamental rights", 2),
    ("14", "equality before law and equal protection of laws", 1),
    ("15", "prohibition of discrimination by the State", 1),
    ("16", "equality of opportunity in public employment", 1),
    ("17", "abolition of untouchability", 1),
    ("18", "abolition of titles", 1),
    ("19", "certain freedoms including speech, assembly and movement", 1),
    ("20", "protection in respect of conviction for offences", 2),
    ("21", "protection of life and personal liberty", 1),
    ("21A", "free and compulsory education for children aged 6 to 14", 1),
    ("22", "protection against arrest and detention in certain cases", 1),
    ("23", "prohibition of human trafficking and forced labour", 1),
    ("24", "prohibition of child employment in factories and hazardous work", 1),
    ("25", "freedom of conscience and free profession of religion", 1),
    ("26", "freedom to manage religious affairs", 2),
    ("27", "freedom from taxes for promotion of a particular religion", 2),
    ("28", "religious instruction in certain educational institutions", 2),
    ("29", "protection of interests of minorities", 2),
    ("30", "minorities' right to establish and administer educational institutions", 2),
    ("32", "Supreme Court remedies for fundamental rights", 1),
    ("39A", "equal justice and free legal aid", 1),
    ("44", "directive principle on a uniform civil code", 2),
    ("50", "separation of judiciary from executive", 2),
    ("51A", "fundamental duties of citizens", 1),
    ("72", "President's power to grant pardons and commute sentences", 2),
    ("76", "Attorney-General for India", 2),
    ("79", "constitution of Parliament", 1),
    ("80", "composition of the Council of States", 2),
    ("81", "composition of the House of the People", 2),
    ("85", "sessions, prorogation and dissolution of Parliament", 2),
    ("93", "Speaker and Deputy Speaker of the Lok Sabha", 1),
    ("100", "voting in Houses of Parliament and quorum", 2),
    ("105", "powers and privileges of Parliament and its members", 2),
    ("108", "joint sitting of both Houses", 2),
    ("110", "definition of Money Bills", 2),
    ("112", "annual financial statement", 1),
    ("123", "President's power to promulgate Ordinances", 2),
    ("124", "establishment and constitution of the Supreme Court", 1),
    ("129", "Supreme Court as a court of record", 2),
    ("136", "special leave to appeal by the Supreme Court", 3),
    ("141", "law declared by the Supreme Court binding on all courts", 2),
    ("142", "Supreme Court orders for complete justice", 3),
    ("143", "President's power to consult the Supreme Court", 3),
    ("148", "Comptroller and Auditor-General of India", 1),
    ("153", "Governors of States", 1),
    ("161", "Governor's power to grant pardons and commute sentences", 2),
    ("168", "constitution of State Legislatures", 1),
    ("178", "Speaker and Deputy Speaker of a Legislative Assembly", 2),
    ("200", "Governor's assent to Bills", 2),
    ("214", "High Courts for States", 1),
    ("215", "High Courts as courts of record", 2),
    ("226", "High Court power to issue writs", 1),
    ("227", "High Court superintendence over subordinate courts", 3),
    ("233", "appointment of district judges", 2),
    ("239", "administration of Union territories", 2),
    ("243B", "constitution of Panchayats", 1),
    ("243G", "powers and responsibilities of Panchayats", 2),
    ("243K", "State Election Commission for Panchayats", 2),
    ("243Q", "constitution of Municipalities", 1),
    ("243ZA", "elections to Municipalities", 2),
    ("245", "extent of laws made by Parliament and State Legislatures", 3),
    ("246", "subject matter of laws by Parliament and States", 3),
    ("249", "Parliament power to legislate on State List in national interest", 3),
    ("252", "Parliament legislation for two or more States by consent", 3),
    ("256", "obligation of States and the Union", 3),
    ("263", "Inter-State Council", 2),
    ("265", "taxes not to be imposed except by authority of law", 1),
    ("280", "Finance Commission", 1),
    ("300A", "property not to be deprived except by authority of law", 1),
    ("312", "All India Services", 2),
    ("315", "Public Service Commissions", 1),
    ("324", "superintendence and control of elections", 1),
    ("326", "adult suffrage for elections", 1),
    ("338", "National Commission for Scheduled Castes", 2),
    ("338A", "National Commission for Scheduled Tribes", 2),
    ("338B", "National Commission for Backward Classes", 2),
    ("343", "official language of the Union", 2),
    ("368", "power of Parliament to amend the Constitution", 2),
]


LAW_PURPOSE_FACTS = [
    ("The Bharatiya Nyaya Sanhita, 2023", "substantive criminal offences replacing the IPC", 1),
    ("The Bharatiya Nagarik Suraksha Sanhita, 2023", "criminal procedure replacing the CrPC", 1),
    ("The Bharatiya Sakshya Adhiniyam, 2023", "rules and principles of evidence replacing the Evidence Act", 1),
    ("The Consumer Protection Act, 2019", "consumer rights and dispute redressal", 1),
    ("The Right to Information Act, 2005", "access to information from public authorities", 1),
    ("The Protection of Children from Sexual Offences Act, 2012", "sexual offences against children", 1),
    ("The POSH Act, 2013", "workplace sexual harassment prevention and redressal", 1),
    ("The Protection of Women from Domestic Violence Act, 2005", "civil protection and reliefs for domestic violence", 1),
    ("The Dowry Prohibition Act, 1961", "prohibition of giving, taking or demanding dowry", 1),
    ("The Legal Services Authorities Act, 1987", "free legal services and Lok Adalats", 1),
    ("The Information Technology Act, 2000", "electronic records, digital signatures and cyber offences", 1),
    ("The Negotiable Instruments Act, 1881", "cheques, promissory notes and negotiable instruments", 2),
    ("The Indian Contract Act, 1872", "contracts, agreements and related obligations", 1),
    ("The Specific Relief Act, 1963", "specific performance and injunction-related civil remedies", 2),
    ("The Limitation Act, 1963", "time limits for filing legal proceedings", 2),
    ("The Code of Civil Procedure, 1908", "procedure for civil suits and decrees", 2),
    ("The Registration Act, 1908", "registration of documents affecting property and other rights", 2),
    ("The Transfer of Property Act, 1882", "transfer of property between living persons", 2),
    ("The Indian Easements Act, 1882", "easements such as rights of way and access", 3),
    ("The Indian Trusts Act, 1882", "private trusts and trustee obligations", 3),
    ("The Hindu Marriage Act, 1955", "marriage and divorce among Hindus and related communities", 1),
    ("The Special Marriage Act, 1954", "civil marriage outside religious personal law ceremony", 1),
    ("The Hindu Succession Act, 1956", "inheritance among Hindus and related communities", 2),
    ("The Indian Succession Act, 1925", "succession and wills in many non-Hindu contexts", 2),
    ("The Guardians and Wards Act, 1890", "appointment and duties of guardians", 2),
    ("The Juvenile Justice Act, 2015", "children in conflict with law and children needing care", 1),
    ("The Motor Vehicles Act, 1988", "road transport, driving licences and accident claims", 1),
    ("The Employees' Provident Funds Act, 1952", "provident fund and social security for covered employees", 2),
    ("The Payment of Gratuity Act, 1972", "gratuity payable to eligible employees", 2),
    ("The Minimum Wages Act, 1948", "minimum wage protection", 1),
    ("The Maternity Benefit Act, 1961", "maternity leave and related employment benefits", 1),
    ("The Equal Remuneration Act, 1976", "equal pay and non-discrimination in remuneration", 2),
    ("The Industrial Disputes Act, 1947", "industrial disputes, retrenchment and labour adjudication", 2),
    ("The Trade Unions Act, 1926", "registration and rights of trade unions", 2),
    ("The Companies Act, 2013", "incorporation, governance and regulation of companies", 1),
    ("The Partnership Act, 1932", "partnership firms and partner relations", 2),
    ("The Limited Liability Partnership Act, 2008", "limited liability partnerships", 2),
    ("The Insolvency and Bankruptcy Code, 2016", "time-bound insolvency resolution", 2),
    ("The Arbitration and Conciliation Act, 1996", "arbitration, conciliation and arbitral awards", 2),
    ("The Mediation Act, 2023", "institutional framework for mediation", 2),
    ("The Aadhaar Act, 2016", "targeted delivery of subsidies and Aadhaar authentication framework", 2),
    ("The Digital Personal Data Protection Act, 2023", "processing and protection of digital personal data", 2),
    ("The Environment Protection Act, 1986", "environment protection and central government powers", 1),
    ("The Water Act, 1974", "prevention and control of water pollution", 2),
    ("The Air Act, 1981", "prevention and control of air pollution", 2),
    ("The Wildlife Protection Act, 1972", "protection of wild animals, birds and plants", 1),
    ("The Forest Conservation Act, 1980", "restriction on dereservation and non-forest use of forest land", 2),
    ("The Biological Diversity Act, 2002", "conservation and sustainable use of biological diversity", 2),
    ("The Food Safety and Standards Act, 2006", "food safety regulation through FSSAI", 1),
    ("The Drugs and Cosmetics Act, 1940", "regulation of drugs and cosmetics", 2),
    ("The Mental Healthcare Act, 2017", "rights of persons with mental illness and mental healthcare", 1),
    ("The Rights of Persons with Disabilities Act, 2016", "rights and accessibility for persons with disabilities", 1),
    ("The Transgender Persons Act, 2019", "rights and welfare of transgender persons", 2),
    ("The SC/ST Prevention of Atrocities Act, 1989", "prevention of atrocities against Scheduled Castes and Scheduled Tribes", 1),
    ("The Representation of the People Act, 1951", "conduct of elections and election offences", 2),
    ("The Citizenship Act, 1955", "acquisition and termination of Indian citizenship", 2),
    ("The Passport Act, 1967", "issue and regulation of passports and travel documents", 1),
    ("The Foreigners Act, 1946", "powers concerning foreigners in India", 3),
    ("The Official Secrets Act, 1923", "official secrets and unauthorised disclosure", 3),
    ("The Prevention of Corruption Act, 1988", "bribery and corruption offences by public servants", 1),
    ("The Lokpal and Lokayuktas Act, 2013", "anti-corruption ombudsman institutions", 2),
    ("The Prevention of Money Laundering Act, 2002", "money laundering and attachment of proceeds of crime", 2),
    ("The Benami Transactions Act, 1988", "prohibition of benami property transactions", 3),
    ("The GST Acts", "goods and services tax framework", 1),
    ("The Income-tax Act, 1961", "income tax levy, assessment and administration", 1),
    ("The Customs Act, 1962", "customs duty, imports and exports regulation", 2),
    ("The Legal Metrology Act, 2009", "weights, measures and packaged commodity declarations", 1),
    ("The Bureau of Indian Standards Act, 2016", "standardisation, marking and quality certification", 2),
    ("The Real Estate Regulation and Development Act, 2016", "registration and regulation of real estate projects", 1),
    ("The Consumer Protection (E-Commerce) Rules, 2020", "consumer protection duties for e-commerce entities", 2),
    ("The Prohibition of Child Marriage Act, 2006", "prevention and restraint of child marriage", 1),
    ("The Medical Termination of Pregnancy Act, 1971", "legal framework for termination of pregnancy", 2),
    ("The Pre-Conception and Pre-Natal Diagnostic Techniques Act, 1994", "prohibition of sex selection", 2),
    ("The Epidemic Diseases Act, 1897", "special powers during dangerous epidemic disease", 3),
    ("The Disaster Management Act, 2005", "institutional framework for disaster management", 1),
    ("The National Food Security Act, 2013", "subsidised food grain entitlements", 1),
    ("The Street Vendors Act, 2014", "protection and regulation of street vending", 2),
]


LANDMARK_CASE_FACTS = [
    ("Navtej Singh Johar v. Union of India", "partially decriminalising consensual same-sex relations under Section 377", 2),
    ("Justice K.S. Puttaswamy v. Union of India", "recognising privacy as a fundamental right", 2),
    ("Vishaka v. State of Rajasthan", "workplace sexual harassment guidelines before the POSH Act", 2),
    ("D.K. Basu v. State of West Bengal", "arrest and custody safeguards", 2),
    ("Maneka Gandhi v. Union of India", "expanding Article 21 due process and personal liberty", 2),
    ("Kesavananda Bharati v. State of Kerala", "basic structure doctrine", 2),
    ("M.C. Mehta v. Union of India", "absolute liability principle in hazardous industry cases", 2),
    ("Hussainara Khatoon v. State of Bihar", "speedy trial and undertrial prisoners", 2),
    ("Lalita Kumari v. Government of Uttar Pradesh", "mandatory FIR registration for cognizable offences", 2),
    ("Nirbhaya case", "criminal law reforms after the 2012 Delhi gang rape case", 1),
    ("Shreya Singhal v. Union of India", "striking down Section 66A of the IT Act", 2),
    ("Mohd. Ahmed Khan v. Shah Bano Begum", "maintenance rights after divorce", 2),
    ("Joseph Shine v. Union of India", "decriminalising adultery", 2),
    ("Indian Young Lawyers Association v. State of Kerala", "Sabarimala temple entry issue", 3),
    ("Olga Tellis v. Bombay Municipal Corporation", "right to livelihood under Article 21", 3),
    ("Vineeta Sharma v. Rakesh Sharma", "equal coparcenary rights of daughters", 2),
    ("Aruna Shanbaug v. Union of India", "passive euthanasia discussion before later guidelines", 3),
    ("Common Cause v. Union of India", "recognition of advance directives for passive euthanasia", 3),
    ("NALSA v. Union of India", "recognising transgender persons' rights", 2),
    ("Indra Sawhney v. Union of India", "reservations and the 50 percent ceiling principle", 3),
    ("Minerva Mills v. Union of India", "balance between fundamental rights and directive principles", 3),
    ("S.R. Bommai v. Union of India", "limits on misuse of President's Rule", 3),
    ("I.C. Golaknath v. State of Punjab", "Parliament's power to amend fundamental rights debate", 3),
    ("A.K. Gopalan v. State of Madras", "early preventive detention and personal liberty interpretation", 3),
    ("ADM Jabalpur v. Shivkant Shukla", "Emergency-era habeas corpus controversy", 3),
    ("Anuradha Bhasin v. Union of India", "internet restrictions and free speech review", 2),
    ("Laxmi v. Union of India", "acid attack regulation and victim compensation directions", 2),
    ("Prakash Singh v. Union of India", "police reform directions", 2),
    ("Bachan Singh v. State of Punjab", "rarest of rare doctrine for death penalty", 3),
    ("Vishnu Dutt Sharma v. Manju Sharma", "irretrievable breakdown not standalone divorce ground under Hindu Marriage Act", 3),
    ("Lily Thomas v. Union of India", "disqualification of convicted legislators", 3),
    ("People's Union for Civil Liberties v. Union of India", "NOTA option in elections", 2),
    ("Association for Democratic Reforms case", "candidate disclosure of criminal, financial and educational details", 2),
    ("Subramanian Swamy v. Union of India", "upholding criminal defamation", 3),
    ("K.M. Nanavati v. State of Maharashtra", "famous jury trial leading to debate on jury system", 2),
    ("Rudul Sah v. State of Bihar", "compensation for illegal detention", 3),
    ("Bhim Singh v. State of Jammu and Kashmir", "compensation for unlawful detention of an MLA", 3),
    ("Sheela Barse v. State of Maharashtra", "custodial safeguards for women prisoners", 3),
    ("Mary Roy v. State of Kerala", "inheritance rights for Syrian Christian women", 3),
    ("Githa Hariharan v. Reserve Bank of India", "mother's role as natural guardian", 3),
]


LEGAL_HISTORY_FACTS = [
    ("Dr. B.R. Ambedkar", "first Law Minister of independent India", 1),
    ("M.C. Setalvad", "first Attorney General of India", 2),
    ("H.J. Kania", "first Chief Justice of India", 2),
    ("Fathima Beevi", "first woman judge of the Supreme Court of India", 1),
    ("Leila Seth", "first woman Chief Justice of a State High Court in India", 2),
    ("Anna Chandy", "first woman High Court judge in India", 3),
    ("Cornelia Sorabji", "first woman advocate associated with Indian legal history", 2),
    ("Justice Y.V. Chandrachud", "longest-serving Chief Justice of India", 3),
    ("Nani Palkhivala", "noted constitutional lawyer in the Kesavananda Bharati case", 2),
    ("K.K. Venugopal", "former Attorney General of India and senior constitutional lawyer", 3),
    ("Soli Sorabjee", "former Attorney General and noted free speech lawyer", 3),
    ("Harish Salve", "Indian lawyer who represented India in the Kulbhushan Jadhav case at the ICJ", 3),
    ("Constituent Assembly", "body that framed the Constitution of India", 1),
    ("26 January 1950", "date when the Constitution of India came into force", 1),
    ("26 November 1949", "date when the Constituent Assembly adopted the Constitution", 2),
    ("Government of India Act, 1935", "major colonial statute influencing India's constitutional structure", 3),
    ("Sir Benegal Narsing Rau", "constitutional adviser to the Constituent Assembly", 3),
    ("Drafting Committee", "committee chaired by Dr. B.R. Ambedkar to draft the Constitution", 1),
    ("Supreme Court of India", "court inaugurated on 28 January 1950", 2),
    ("Federal Court of India", "predecessor institution before the Supreme Court of India", 3),
]


TERM_FACTS = [
    ("FIR", "first information report for a cognizable offence", 1),
    ("Zero FIR", "FIR registered at any police station and transferred to the proper station", 1),
    ("Cognizable offence", "offence where police may investigate without prior magistrate permission", 1),
    ("Non-cognizable offence", "offence where police generally need magistrate permission to investigate", 1),
    ("Bailable offence", "offence where bail can be claimed as a matter of right subject to law", 1),
    ("Non-bailable offence", "offence where bail depends on discretion of court or authority", 1),
    ("Anticipatory bail", "pre-arrest bail direction from a court", 1),
    ("Regular bail", "bail sought after arrest or custody", 1),
    ("Default bail", "statutory bail when investigation is not completed within the prescribed period", 2),
    ("Personal bond", "promise to appear without necessarily depositing cash", 1),
    ("Surety", "person who undertakes responsibility for an accused person's appearance", 1),
    ("Summons", "court direction requiring a person to appear", 1),
    ("Warrant", "court order authorising arrest, search or another legal act", 1),
    ("Search warrant", "court authorisation to search a specified place or person", 1),
    ("Arrest memo", "written record of arrest details prepared during arrest", 1),
    ("Remand", "court-authorised custody during investigation or trial", 2),
    ("Judicial custody", "custody under court control, usually in jail", 2),
    ("Police custody", "custody with police for investigation as authorised by court", 2),
    ("Charge sheet", "police report filed after investigation", 1),
    ("Closure report", "police report suggesting no sufficient case after investigation", 2),
    ("Protest petition", "complainant objection to a closure report", 2),
    ("Plea bargaining", "negotiated disposal procedure available in eligible criminal cases", 2),
    ("Compoundable offence", "offence that law permits parties to compromise", 1),
    ("Cognizance", "court taking judicial notice of an offence or matter", 3),
    ("Framing of charge", "court formally states the accusation to be tried", 2),
    ("Acquittal", "finding that the accused is not guilty", 1),
    ("Conviction", "finding that the accused is guilty", 1),
    ("Appeal", "challenge to a decision before a higher forum", 1),
    ("Revision", "supervisory correction of jurisdictional or legal error", 3),
    ("Review", "same court reconsidering its decision in limited situations", 2),
    ("Public prosecutor", "law officer who conducts criminal prosecution for the State", 1),
    ("Legal aid counsel", "lawyer provided through legal services system for eligible persons", 1),
    ("Victim compensation", "monetary relief scheme or order for victims as per law", 1),
    ("Habeas corpus", "writ used to question unlawful detention", 1),
    ("Mandamus", "writ directing a public authority to perform a public duty", 1),
    ("Certiorari", "writ used by a higher court to quash an order of a lower court or tribunal", 2),
    ("Prohibition", "writ restraining a lower court or tribunal from exceeding jurisdiction", 2),
    ("Quo warranto", "writ questioning authority to hold a public office", 2),
    ("PIL", "public interest litigation for issues affecting the public", 1),
    ("Locus standi", "legal standing to bring a case", 2),
    ("Res judicata", "matter already finally decided cannot be re-litigated between same parties", 3),
    ("Natural justice", "fair hearing and absence of bias", 2),
    ("Audi alteram partem", "hear the other side", 3),
    ("Nemo judex in causa sua", "no one should be a judge in their own cause", 3),
    ("Interim order", "temporary order pending final decision", 1),
    ("Stay order", "temporary pause on a proceeding, order or action", 1),
    ("Injunction", "court order to do or stop doing an act", 1),
    ("Ex parte order", "order passed after hearing only one side in permitted circumstances", 2),
    ("Affidavit", "written statement confirmed on oath or affirmation", 1),
    ("Vakalatnama", "authorisation given to an advocate to represent a party", 1),
    ("Plaint", "document by which a civil suit is instituted", 2),
    ("Written statement", "defendant's reply in a civil suit", 2),
    ("Decree", "formal expression of adjudication in a civil suit", 2),
    ("Execution", "process of enforcing a decree or order", 2),
    ("Limitation period", "time limit within which a legal action must be started", 1),
    ("Cause of action", "bundle of facts giving a right to sue", 2),
    ("Jurisdiction", "legal authority of a court or body to decide a matter", 1),
    ("Territorial jurisdiction", "authority based on place or area", 2),
    ("Pecuniary jurisdiction", "authority based on monetary value of the case", 2),
    ("Subject-matter jurisdiction", "authority based on type of dispute", 2),
    ("Mens rea", "guilty mind or criminal intent where required", 2),
    ("Actus reus", "external act or omission forming part of an offence", 2),
    ("Strict liability", "liability without needing proof of fault in specified contexts", 3),
    ("Vicarious liability", "liability of one person for acts of another in recognised relationships", 3),
    ("Burden of proof", "responsibility to prove a fact in legal proceedings", 1),
    ("Beyond reasonable doubt", "standard generally required for criminal conviction", 1),
    ("Preponderance of probabilities", "standard commonly used in civil cases", 2),
    ("Presumption of innocence", "accused is treated as not guilty until proven guilty", 1),
    ("Hostile witness", "witness who departs from prior expected testimony", 2),
    ("Dying declaration", "statement about cause or circumstances of death by a person who dies", 3),
    ("Expert evidence", "opinion evidence from a person specially skilled in a relevant field", 2),
    ("Electronic evidence certificate", "certificate commonly linked to proving electronic records", 2),
    ("Chain of custody", "documented handling path of evidence", 2),
    ("Confession to police officer", "statement category treated with special restrictions in evidence law", 2),
    ("Admission", "statement suggesting a fact in issue or relevant fact", 3),
    ("Primary evidence", "document itself produced for inspection of the court", 2),
    ("Secondary evidence", "permitted substitute evidence when primary evidence is unavailable under law", 3),
    ("Cross-examination", "questioning of a witness by the opposite party", 1),
    ("Leading question", "question suggesting the answer", 2),
    ("Perjury", "false evidence given under oath or legal obligation", 2),
    ("Estoppel", "rule preventing a person from denying certain represented facts in specified situations", 3),
    ("Sub judice", "matter currently under judicial consideration", 3),
    ("Functus officio", "authority that has exhausted its function after completing the decision", 3),
    ("Ratio decidendi", "binding legal reason for a judicial decision", 3),
    ("Obiter dicta", "court observations not forming the binding reason for decision", 3),
    ("Per incuriam", "decision given in ignorance of binding law or relevant statutory provision", 3),
    ("Ultra vires", "act done beyond legal power or authority", 3),
    ("Delegated legislation", "rules or regulations made under authority given by a statute", 3),
    ("Promissory estoppel", "principle preventing unfair withdrawal from a clear promise in suitable cases", 3),
    ("Doctrine of proportionality", "principle that State action restricting rights should not be excessive", 3),
    ("Doctrine of legitimate expectation", "administrative law principle protecting reasonable procedural expectations", 3),
    ("Colourable legislation", "law-making that appears within power but indirectly exceeds constitutional limits", 3),
    ("Pith and substance", "doctrine used to identify the true nature of legislation", 3),
    ("Repugnancy", "conflict between Union and State laws on a concurrent subject", 3),
    ("Severability", "doctrine allowing valid parts of a law to survive when invalid parts are removed", 3),
    ("Basic structure doctrine", "principle limiting constitutional amendments that damage core constitutional features", 3),
    ("Consumer", "person who buys goods or hires services for consideration under consumer law", 1),
    ("Defective goods", "goods with fault, imperfection or shortcoming", 1),
    ("Deficiency in service", "fault or shortcoming in service promised to a consumer", 1),
    ("Unfair trade practice", "misleading or deceptive consumer-facing business practice", 1),
    ("Product liability", "liability for harm caused by defective products or services", 2),
    ("MRP", "maximum retail price printed for packaged goods", 1),
    ("Consumer mediation", "settlement mechanism for consumer disputes", 2),
    ("E-Daakhil", "online filing portal for consumer complaints", 1),
    ("CCPA", "regulator for consumer rights, unfair trade practices and misleading ads", 2),
    ("District Consumer Commission", "district-level forum for consumer disputes", 1),
    ("State Consumer Commission", "state-level forum for consumer disputes and appeals", 2),
    ("National Consumer Commission", "national-level consumer disputes commission", 2),
    ("Phishing", "fraudulent attempt to steal sensitive information online", 1),
    ("OTP fraud", "misuse of one-time password to access money or accounts", 1),
    ("Cybercrime portal", "online reporting of cybercrime complaints", 1),
    ("Cyber helpline 1930", "quick reporting of cyber financial fraud", 1),
    ("CERT-In", "national computer emergency response team for cyber security incidents", 2),
    ("Intermediary under IT law", "platform or service that receives, stores or transmits electronic records for others", 2),
    ("Electronic record", "digital information treated as a record under law", 1),
    ("Digital signature", "electronic method used to authenticate digital records", 2),
    ("Sensitive personal data", "personal data needing stronger protection in privacy compliance", 2),
    ("Data fiduciary", "entity deciding purpose and means of processing digital personal data", 2),
    ("Consent under data protection", "free, specific, informed and unambiguous indication for processing", 2),
    ("POCSO child", "person below 18 years of age", 1),
    ("Mandatory reporting under POCSO", "legal duty to report child sexual offences", 2),
    ("Child-friendly POCSO procedure", "recording and trial safeguards for child victims", 2),
    ("POCSO Special Court", "designated court for POCSO offences", 2),
    ("Identity protection for sexual offence victims", "restriction on publishing identifying details", 1),
    ("POSH Internal Committee", "workplace committee for sexual harassment complaints", 1),
    ("POSH Local Committee", "district-level forum where Internal Committee is unavailable or complaint is against employer", 2),
    ("POSH complaint period", "usual three-month complaint period, extendable in specified cases", 2),
    ("SHe-Box", "online channel for workplace sexual harassment complaints by women", 1),
    ("Protection Officer", "official who assists in domestic violence proceedings", 1),
    ("Residence order", "domestic violence relief concerning residence in shared household", 1),
    ("Monetary relief", "financial relief for losses, expenses or maintenance as ordered", 1),
    ("Protection order", "court direction restraining violence or contact as ordered", 1),
    ("Dowry demand", "illegal demand connected with marriage", 1),
    ("Maintenance", "financial support ordered for eligible dependants", 1),
    ("Marriage registration", "official recording of marriage", 1),
    ("Civil marriage", "marriage framework not based on religious ceremony", 1),
    ("Restitution of conjugal rights", "matrimonial remedy seeking resumption of cohabitation", 3),
    ("Mutual consent divorce", "divorce based on joint consent of spouses under applicable law", 2),
    ("Adoption", "legal process creating parent-child relationship", 1),
    ("Guardianship", "legal authority to care for a minor or property", 1),
    ("Will", "legal declaration of how property should pass after death", 1),
    ("Probate", "court certification of a will", 2),
    ("Legal heir certificate", "document identifying heirs for limited administrative purposes", 1),
    ("Succession certificate", "court certificate to collect debts and securities of deceased", 2),
    ("Sale deed", "document transferring ownership in a sale of immovable property", 1),
    ("Gift deed", "document transferring property voluntarily without consideration", 1),
    ("Lease deed", "document recording lease rights and obligations", 1),
    ("Mortgage", "transfer of interest in property as security for a debt", 2),
    ("Easement", "right enjoyed over another person's land for beneficial use", 2),
    ("Mutation", "revenue record change after transfer or inheritance", 1),
    ("Encumbrance certificate", "record showing registered property transactions or liabilities", 1),
    ("RERA registration", "registration requirement for covered real estate projects", 1),
    ("Cheque dishonour", "dishonour of cheque for insufficient funds or similar reasons", 1),
    ("Promissory note", "written promise to pay a certain sum", 2),
    ("Indemnity", "promise to save another from loss", 2),
    ("Guarantee", "promise to answer for debt or default of another", 2),
    ("Bailment", "delivery of goods for a purpose on contract to return or dispose", 2),
    ("Pledge", "bailment of goods as security for debt or performance", 2),
    ("Agency", "relationship where one person acts on behalf of another", 1),
    ("Offer", "proposal showing willingness to do or abstain from doing something", 1),
    ("Acceptance", "assent to a proposal", 1),
    ("Consideration", "something of value exchanged for a promise", 1),
    ("Void agreement", "agreement not enforceable by law", 1),
    ("Voidable contract", "contract enforceable at option of one party", 2),
    ("Specific performance", "court order requiring performance of contractual obligation", 2),
    ("Arbitration clause", "agreement to refer disputes to arbitration", 1),
    ("Arbitral award", "decision made by an arbitral tribunal", 1),
    ("Conciliation", "assisted settlement process with a conciliator", 2),
    ("Mediation", "neutral-assisted settlement process", 1),
    ("Lok Adalat award", "settlement-based award treated as final in the Lok Adalat framework", 2),
    ("DLSA", "District Legal Services Authority", 1),
    ("NALSA helpline 15100", "legal aid helpline information", 1),
    ("Amicus curiae", "friend of the court assisting with legal submissions", 2),
    ("Court of record", "court whose records have evidentiary value and contempt powers", 2),
    ("Tribunal", "special adjudicatory body for particular types of disputes", 1),
    ("Ombudsman", "authority receiving complaints against institutions or public bodies", 2),
]


INSTITUTION_FACTS = [
    ("Supreme Court of India", "highest constitutional court of India", 1),
    ("High Court", "highest court in a State or group of States and territories", 1),
    ("District Court", "local court system handling district-level civil and criminal matters", 1),
    ("Family Court", "court dealing with family and matrimonial disputes", 1),
    ("Consumer Commission", "forum for consumer disputes", 1),
    ("Lok Adalat", "forum for amicable settlement of disputes through legal services authorities", 1),
    ("Gram Nyayalaya", "village-level court framework for local access to justice", 2),
    ("Central Information Commission", "appeals and complaints under central RTI matters", 2),
    ("State Information Commission", "appeals and complaints under State RTI matters", 2),
    ("Election Commission of India", "superintendence, direction and control of elections", 1),
    ("Finance Commission", "recommendations on distribution of tax revenues", 2),
    ("CAG", "audit of Union and State government accounts", 1),
    ("UPSC", "Union public service recruitment and related functions", 1),
    ("State Public Service Commission", "State public service recruitment functions", 1),
    ("National Human Rights Commission", "human rights protection and inquiry body", 1),
    ("National Commission for Women", "women's rights and safeguards advisory body", 1),
    ("National Commission for Protection of Child Rights", "child rights monitoring body", 1),
    ("National Commission for Scheduled Castes", "constitutional body for safeguards of Scheduled Castes", 2),
    ("National Commission for Scheduled Tribes", "constitutional body for safeguards of Scheduled Tribes", 2),
    ("National Commission for Backward Classes", "constitutional body for safeguards of backward classes", 2),
    ("Lokpal", "anti-corruption ombudsman for specified public functionaries", 2),
    ("Competition Commission of India", "competition law regulator", 2),
    ("SEBI", "securities market regulator", 1),
    ("RBI", "central bank and banking regulator", 1),
    ("IRDAI", "insurance regulator", 1),
    ("PFRDA", "pension sector regulator", 2),
    ("TRAI", "telecom regulator", 1),
    ("FSSAI", "food safety regulator", 1),
    ("BIS", "standards and certification body", 1),
    ("RERA Authority", "real estate project and agent regulator under RERA", 1),
    ("Armed Forces Tribunal", "service disputes and appeals for members of the armed forces", 3),
    ("NCLT", "company law and insolvency adjudication forum", 2),
    ("NCLAT", "appellate forum for NCLT and specified regulatory matters", 2),
    ("DRT", "debt recovery tribunal for banks and financial institutions", 2),
    ("CAT", "Central Administrative Tribunal for service matters", 2),
    ("NGT", "specialised tribunal for environmental matters", 1),
    ("Income Tax Appellate Tribunal", "appellate tribunal for income tax disputes", 2),
    ("Motor Accident Claims Tribunal", "forum for motor accident compensation claims", 1),
    ("Juvenile Justice Board", "body handling children in conflict with law", 1),
    ("Child Welfare Committee", "body for children needing care and protection", 1),
    ("Internal Committee under POSH", "workplace forum for sexual harassment complaints", 1),
    ("Local Committee under POSH", "district-level forum for certain workplace harassment complaints", 2),
    ("Protection Officer", "domestic violence law support official", 1),
    ("Registrar of Companies", "company registration and compliance office", 1),
    ("Sub-Registrar", "registration office for documents such as sale deeds", 1),
    ("Public Information Officer", "officer who receives and responds to RTI requests", 1),
    ("First Appellate Authority", "first appeal forum under RTI inside the public authority", 2),
    ("Police Station", "local police unit for reporting offences and investigation", 1),
    ("Magistrate", "judicial officer handling remand and cognizance", 1),
    ("Sessions Court", "court trying serious criminal cases", 2),
    ("Special Court", "court designated for particular statute or offence category", 2),
    ("Legal Metrology Department", "authority checking weights, measures and packaged declarations", 1),
    ("Labour Commissioner", "labour law enforcement and dispute-related authority", 1),
    ("EPFO", "provident fund organisation", 1),
    ("UIDAI", "Aadhaar authority", 1),
    ("Data Protection Board of India", "adjudicatory body under digital personal data protection law", 2),
    ("Central Pollution Control Board", "central pollution control body", 1),
    ("State Pollution Control Board", "State-level pollution control body", 1),
    ("National Biodiversity Authority", "authority under biodiversity law", 2),
    ("SHe-Box portal", "online channel for workplace sexual harassment complaints by women", 1),
    ("National Consumer Helpline 1915", "consumer grievance guidance and registration", 1),
    ("National Cyber Crime Reporting Portal", "online cybercrime complaint portal", 1),
    ("RTI Online", "portal for filing RTI requests to central public authorities", 1),
    ("State Legal Services Authority", "State-level legal aid and Lok Adalat coordination", 1),
    ("Taluk Legal Services Committee", "legal services support at taluk or mandal level", 1),
    ("Gram Sabha", "village assembly under Panchayati Raj", 1),
    ("Municipal Corporation", "urban local body for larger cities", 1),
    ("District Magistrate", "district administration and executive magistracy head in many States", 1),
    ("Tehsil office", "local revenue administration office for land and related records", 1),
    ("Police control room 112", "emergency response number used across many Indian States", 1),
    ("eCourts portal", "online access to court case status and services", 1),
]


PRACTICAL_FACTS = [
    ("If a person is arrested, which safeguard requires informing them why they are arrested?", "being informed of grounds of arrest", 1),
    ("Which safeguard lets an arrested person consult and be defended by a lawyer?", "right to consult and be defended by a legal practitioner", 1),
    ("What is the usual constitutional safeguard on producing an arrested person before a magistrate?", "production within 24 hours excluding journey time", 1),
    ("Which record helps document time, place and details of arrest?", "arrest memo", 1),
    ("Which step helps family or a nominated person know about an arrest?", "informing a nominated person about the arrest", 1),
    ("Which service should an eligible person approach when they cannot afford a lawyer?", "legal aid through legal services authorities", 1),
    ("Which forum is suited for settlement of many compoundable or civil disputes by consent?", "Lok Adalat", 1),
    ("Which portal is meant for cybercrime complaints in India?", "cybercrime.gov.in", 1),
    ("Which helpline is commonly used for urgent cyber financial fraud reporting?", "1930", 1),
    ("Which helpline is used for National Consumer Helpline support?", "1915", 1),
    ("Which helpline is linked with NALSA legal aid?", "15100", 1),
    ("Which filing route helps submit consumer complaints online?", "E-Daakhil or e-Jagriti consumer filing", 1),
    ("For a defective product bought by a consumer, which law family is usually relevant?", "consumer protection law", 1),
    ("For a bounced cheque due to insufficient funds, which law is commonly involved?", "Negotiable Instruments law", 1),
    ("For workplace sexual harassment in an office, which committee is the first workplace forum?", "Internal Committee under POSH", 1),
    ("If the workplace has no Internal Committee where required, which district forum may matter?", "Local Committee under POSH", 2),
    ("For domestic violence residence-related relief, which order is commonly relevant?", "residence order", 1),
    ("For domestic violence financial support, which relief is commonly relevant?", "monetary relief", 1),
    ("For child sexual offences, which statute is the core special law?", "POCSO Act", 1),
    ("For a public authority refusing RTI information, what is generally the first challenge step?", "first appeal under RTI", 2),
    ("For a delayed or unsatisfactory RTI first appeal, what later forum may be approached?", "Information Commission", 2),
    ("For a sale of immovable property, which document is central to transfer?", "sale deed", 1),
    ("For checking registered liabilities on property, which document is commonly searched?", "encumbrance certificate", 1),
    ("For updating revenue records after property transfer, which process is commonly used?", "mutation", 1),
    ("For a rented property relationship, which document records lease terms?", "lease deed or rent agreement", 1),
    ("For a civil court order preventing demolition temporarily, which relief is likely?", "interim injunction or stay order", 2),
    ("For a person summoned by court, what does the document require?", "appearance before court", 1),
    ("For a witness questioned by the opposite side, what is the process called?", "cross-examination", 1),
    ("For proving a digital record in court, what evidence requirement is often relevant?", "electronic evidence certificate", 2),
    ("For a person seeking information from a government department, which officer receives RTI requests?", "Public Information Officer", 1),
    ("For an employee's provident fund issue, which organisation is usually relevant?", "EPFO", 1),
    ("For a food safety complaint about packaged food standards, which regulator is relevant?", "FSSAI", 1),
    ("For telecom service regulation complaints or rules, which regulator is relevant?", "TRAI", 1),
    ("For securities market misconduct, which regulator is relevant?", "SEBI", 1),
    ("For real estate project registration, which authority is relevant?", "RERA Authority", 1),
    ("For pollution control consent, which board is commonly relevant?", "State Pollution Control Board", 1),
    ("For company incorporation records, which office is commonly relevant?", "Registrar of Companies", 1),
    ("For registration of a sale deed, which office is commonly relevant?", "Sub-Registrar", 1),
    ("For a road accident compensation claim, which tribunal is commonly relevant?", "Motor Accident Claims Tribunal", 1),
    ("For a child in conflict with law, which body handles the matter?", "Juvenile Justice Board", 1),
    ("For a child needing care and protection, which body handles the matter?", "Child Welfare Committee", 1),
    ("For an environmental case needing a specialised forum, which tribunal is relevant?", "National Green Tribunal", 1),
    ("For company insolvency resolution, which tribunal is commonly relevant?", "NCLT", 2),
    ("For an appeal from many NCLT orders, which forum is commonly relevant?", "NCLAT", 2),
    ("For debt recovery by banks and financial institutions, which tribunal is relevant?", "DRT", 2),
    ("For central government service disputes, which tribunal is commonly relevant?", "CAT", 2),
    ("For a case already finally decided between same parties, which principle may block re-litigation?", "res judicata", 3),
    ("For a judge deciding a matter where they have personal interest, which natural justice rule is implicated?", "nemo judex in causa sua", 3),
    ("For not giving a person a chance to be heard, which natural justice rule is implicated?", "audi alteram partem", 3),
    ("For liability of an employer for employee acts in a recognised relationship, which concept is relevant?", "vicarious liability", 3),
    ("For liability without proof of fault in specified contexts, which concept is relevant?", "strict liability", 3),
    ("For a criminal trial, who generally carries the burden of proving guilt?", "prosecution", 2),
    ("For a civil case, which proof standard is commonly used?", "preponderance of probabilities", 2),
    ("For criminal conviction, which proof standard is generally required?", "beyond reasonable doubt", 1),
    ("For a deceased person's statement about cause of death, which evidence concept applies?", "dying declaration", 3),
    ("For a technical opinion from a specialised professional, which evidence concept applies?", "expert evidence", 2),
    ("For tracking evidence from seizure to court, which concept matters?", "chain of custody", 2),
    ("For asking the Supreme Court to enforce fundamental rights, which constitutional remedy is central?", "Article 32 petition", 2),
    ("For asking a High Court to issue writs, which constitutional provision is central?", "Article 226 petition", 2),
    ("For unlawful detention, which writ is commonly sought?", "habeas corpus", 1),
    ("For a public authority failing a public duty, which writ is commonly sought?", "mandamus", 2),
    ("For questioning someone's authority to hold public office, which writ is commonly sought?", "quo warranto", 2),
    ("For quashing an order of a lower court or tribunal, which writ is commonly used?", "certiorari", 3),
    ("For stopping a lower court from exceeding jurisdiction, which writ is commonly used?", "prohibition", 3),
    ("For settling disputes through a neutral third party without adjudication, which process fits?", "mediation", 1),
    ("For a binding private adjudication based on agreement, which process fits?", "arbitration", 1),
    ("For a court-appointed helper on legal submissions, which role fits?", "amicus curiae", 2),
    ("For a temporary court order before final judgment, which term fits?", "interim order", 1),
    ("For a court proceeding held privately in sensitive cases, which term fits?", "in camera proceeding", 2),
    ("Which written request asks police to record information about an offence?", "police complaint", 1),
    ("Which notice tells a person to appear before police or court?", "summons notice", 1),
    ("Which document proves a person's residential address?", "address proof", 1),
    ("Which document proves a person's identity in many official processes?", "identity proof", 1),
    ("Which written record is useful after paying rent in cash?", "rent receipt", 1),
    ("Which document records basic terms between landlord and tenant?", "rent agreement", 1),
    ("Which complaint can a consumer make for poor service?", "service deficiency complaint", 1),
    ("Which complaint can a consumer make for faulty goods?", "defective goods complaint", 1),
    ("Which record should be kept after buying an expensive product?", "purchase invoice", 1),
    ("Which basic document shows salary paid by an employer?", "salary slip", 1),
    ("Which document records employment terms between worker and employer?", "employment contract", 1),
]


def build_questions() -> list[dict]:
    questions: list[dict] = []
    article_pool = [f"Article {num}" for num, _, _ in ARTICLE_FACTS]
    law_pool = [law for law, _, _ in LAW_PURPOSE_FACTS]
    landmark_pool = [case for case, _, _ in LANDMARK_CASE_FACTS]
    history_pool = [item for item, _, _ in LEGAL_HISTORY_FACTS]
    term_pool = [term for term, _, _ in TERM_FACTS]
    inst_pool = [name for name, _, _ in INSTITUTION_FACTS]
    practical_pool = [answer for _, answer, _ in PRACTICAL_FACTS]

    salt = 0
    for num, meaning, diff in ARTICLE_FACTS:
        answer = f"Article {num}"
        options, correct = choose_options(answer, article_pool, salt)
        questions.append({
            "category": "indian_law",
            "difficulty": diff,
            "question": f"Which constitutional article is mainly associated with {meaning}?",
            "options": options,
            "correct_index": correct,
            "source_note": "Constitution of India",
        })
        salt += 1

    for law, purpose, diff in LAW_PURPOSE_FACTS:
        options, correct = choose_options(law, law_pool, salt)
        questions.append({
            "category": "indian_law",
            "difficulty": diff,
            "question": f"Which law is mainly associated with {purpose}?",
            "options": options,
            "correct_index": correct,
            "source_note": "Indian statutes",
        })
        salt += 1

    for term, definition, diff in TERM_FACTS:
        options, correct = choose_options(term, term_pool, salt)
        questions.append({
            "category": "indian_law",
            "difficulty": diff,
            "question": f"Which legal term means {definition}?",
            "options": options,
            "correct_index": correct,
            "source_note": "Legal literacy glossary",
        })
        salt += 1

    for name, role, diff in INSTITUTION_FACTS:
        options, correct = choose_options(name, inst_pool, salt)
        questions.append({
            "category": "indian_law",
            "difficulty": diff,
            "question": f"Which institution or forum is mainly associated with {role}?",
            "options": options,
            "correct_index": correct,
            "source_note": "Indian legal institutions",
        })
        salt += 1

    for question, answer, diff in PRACTICAL_FACTS:
        options, correct = choose_options(answer, practical_pool, salt)
        questions.append({
            "category": "indian_law",
            "difficulty": diff,
            "question": question,
            "options": options,
            "correct_index": correct,
            "source_note": "Practical legal literacy",
        })
        salt += 1

    for case, principle, diff in LANDMARK_CASE_FACTS:
        options, correct = choose_options(case, landmark_pool, salt)
        questions.append({
            "category": "indian_law",
            "difficulty": diff,
            "question": f"Which case is known for {principle}?",
            "options": options,
            "correct_index": correct,
            "source_note": "Landmark judgments",
        })
        salt += 1

    for item, fact, diff in LEGAL_HISTORY_FACTS:
        options, correct = choose_options(item, history_pool, salt)
        questions.append({
            "category": "indian_law",
            "difficulty": diff,
            "question": f"Who or what is associated with {fact}?",
            "options": options,
            "correct_index": correct,
            "source_note": "Indian legal history",
        })
        salt += 1

    # Add extra distinct section-specific facts to reach a balanced 500 without
    # repeating the same topic with different wording.
    section_facts = [
        ("BNS Section 85", "cruelty by husband or relatives of husband", 2),
        ("BNS Section 86", "definition of cruelty", 2),
        ("BNS Section 63", "rape", 3),
        ("BNS Section 69", "sexual intercourse by deceitful means etc.", 3),
        ("BNS Section 74", "assault or criminal force to woman with intent to outrage modesty", 2),
        ("BNS Section 75", "sexual harassment", 2),
        ("BNS Section 78", "stalking", 2),
        ("BNS Section 80", "dowry death", 2),
        ("BNS Section 103", "punishment for murder", 2),
        ("BNS Section 106", "causing death by negligence", 2),
        ("BNS Section 108", "abetment of suicide", 3),
        ("BNS Section 113", "terrorist act", 3),
        ("BNS Section 115", "voluntarily causing hurt", 2),
        ("BNS Section 126", "wrongful restraint", 2),
        ("BNS Section 127", "wrongful confinement", 2),
        ("BNS Section 137", "kidnapping", 2),
        ("BNS Section 152", "acts endangering sovereignty, unity and integrity of India", 3),
        ("BNS Section 189", "unlawful assembly", 3),
        ("BNS Section 178", "counterfeiting coin, government stamp, currency-notes or bank-notes", 3),
        ("BNS Section 303", "theft", 1),
        ("BNS Section 304", "snatching", 2),
        ("BNS Section 309", "robbery", 2),
        ("BNS Section 316", "criminal breach of trust", 2),
        ("BNS Section 318", "cheating", 1),
        ("BNS Section 329", "criminal trespass and house-trespass", 2),
        ("BNS Section 351", "criminal intimidation", 1),
        ("BNS Chapter III", "general exceptions and right of private defence", 3),
        ("BNS Chapter V", "offences against woman and child", 3),
        ("BNS Chapter XVII", "offences against property", 3),
        ("BSA Section 2", "definitions under evidence law", 3),
        ("BSA Section 24", "confession caused by inducement, threat, coercion or promise", 3),
        ("BSA Section 29", "confession to police officer not to be proved against accused", 3),
        ("BSA Section 32", "statements by persons who are dead or unavailable", 3),
        ("BSA Section 39", "opinions of experts", 3),
        ("BSA Section 57", "primary evidence", 3),
        ("BSA Section 58", "secondary evidence", 3),
        ("BSA Section 63", "special provisions as to evidence relating to electronic record", 3),
        ("BSA Section 104", "burden of proof", 3),
        ("BSA Section 122", "estoppel of tenant and licensee", 3),
        ("POCSO Section 2", "definition of child as person below 18", 2),
        ("POCSO Section 19", "reporting of offences", 2),
        ("POCSO Section 21", "punishment for failure to report or record a case", 3),
        ("POCSO Section 23", "procedure for media and identity protection", 2),
        ("POCSO Section 24", "recording statement of a child", 2),
        ("POCSO Section 28", "designation of Special Courts", 2),
        ("POCSO Section 33", "procedure and powers of Special Court", 3),
        ("POCSO Section 37", "trials to be conducted in camera", 2),
        ("POSH Section 4", "constitution of Internal Committee", 2),
        ("POSH Section 6", "constitution and jurisdiction of Local Committee", 2),
        ("POSH Section 9", "complaint of sexual harassment", 2),
        ("POSH Section 10", "conciliation", 3),
        ("POSH Section 11", "inquiry into complaint", 2),
        ("POSH Section 16", "confidentiality of complaint and inquiry contents", 2),
        ("POSH Section 19", "duties of employer", 2),
        ("POSH Section 26", "penalty for non-compliance", 3),
        ("RTI Section 3", "right to information for citizens", 1),
        ("RTI Section 4", "obligations of public authorities", 2),
        ("RTI Section 6", "request for obtaining information", 1),
        ("RTI Section 7", "disposal of RTI request", 2),
        ("RTI Section 8", "exemptions from disclosure", 3),
        ("RTI Section 19", "appeals", 2),
        ("RTI Section 20", "penalties", 3),
        ("DV Act Section 12", "application to Magistrate", 2),
        ("DV Act Section 17", "right to reside in shared household", 2),
        ("DV Act Section 18", "protection orders", 2),
        ("DV Act Section 19", "residence orders", 2),
        ("DV Act Section 20", "monetary reliefs", 2),
        ("DV Act Section 21", "custody orders", 3),
        ("DV Act Section 22", "compensation orders", 3),
        ("Consumer Protection Act Section 2", "definitions such as consumer and defect", 2),
        ("Consumer Protection Act Section 35", "manner of making complaint to District Commission", 3),
        ("Consumer Protection Act Section 74", "establishment of consumer mediation cell", 3),
        ("Consumer Protection Act Section 83", "product liability action", 3),
        ("IT Act Section 4", "legal recognition of electronic records", 2),
        ("IT Act Section 5", "legal recognition of electronic signatures", 2),
        ("IT Act Section 43", "penalty and compensation for damage to computer systems", 3),
        ("IT Act Section 66", "computer-related offences", 2),
        ("IT Act Section 66C", "identity theft", 2),
        ("IT Act Section 66D", "cheating by personation using computer resource", 2),
        ("IT Act Section 67", "publishing or transmitting obscene material in electronic form", 3),
        ("IT Act Section 69A", "blocking public access to information through computer resource", 3),
        ("IT Act Section 70B", "Indian Computer Emergency Response Team", 2),
        ("NI Act Section 138", "dishonour of cheque for insufficiency of funds", 1),
        ("Contract Act Section 10", "what agreements are contracts", 2),
        ("Contract Act Section 11", "who is competent to contract", 2),
        ("Contract Act Section 73", "compensation for loss caused by breach of contract", 3),
        ("Specific Relief Act Section 10", "specific performance of contracts", 3),
        ("Limitation Act Section 3", "bar of limitation", 3),
        ("CPC Section 9", "courts to try all civil suits unless barred", 2),
        ("CPC Section 11", "res judicata", 3),
        ("CPC Section 89", "settlement of disputes outside court", 2),
        ("CrPC legacy term replaced by BNSS", "criminal procedure framework now under BNSS", 1),
        ("IPC legacy term replaced by BNS", "substantive criminal offences now under BNS", 1),
        ("Evidence Act legacy term replaced by BSA", "evidence framework now under BSA", 1),
    ]
    section_pool = [item for item, _, _ in section_facts]
    for item, meaning, diff in section_facts:
        options, correct = choose_options(item, section_pool, salt)
        questions.append({
            "category": "indian_law",
            "difficulty": diff,
            "question": f"Which provision or legal label is mainly associated with {meaning}?",
            "options": options,
            "correct_index": correct,
            "source_note": "Statutory provisions",
        })
        salt += 1

    deduped: list[dict] = []
    seen_answers: set[str] = set()
    source_priority = {
        "Practical legal literacy": 0,
        "Legal literacy glossary": 1,
        "Landmark judgments": 2,
        "Indian statutes": 3,
        "Indian legal institutions": 4,
        "Indian legal history": 5,
        "Statutory provisions": 6,
        "Constitution of India": 7,
    }
    questions.sort(key=lambda q: source_priority.get(q.get("source_note", ""), 99))
    for q in questions:
        answer_key = q["options"][q["correct_index"]].strip().lower()
        if answer_key in seen_answers:
            continue
        seen_answers.add(answer_key)
        deduped.append(q)

    quotas = {1: 220, 2: 200, 3: 80}
    selected: list[dict] = []
    precision_answer_limit = 15
    precision_answers = 0

    def is_precision_answer(q: dict) -> bool:
        answer = q["options"][q["correct_index"]]
        return "Article " in answer

    for diff, quota in quotas.items():
        bucket = [q for q in deduped if q["difficulty"] == diff]
        chosen: list[dict] = []
        deferred_precision: list[dict] = []
        for q in bucket:
            if is_precision_answer(q):
                deferred_precision.append(q)
                continue
            chosen.append(q)
            if len(chosen) == quota:
                break
        if len(chosen) < quota:
            for q in deferred_precision:
                if precision_answers >= precision_answer_limit:
                    continue
                chosen.append(q)
                precision_answers += 1
                if len(chosen) == quota:
                    break
        if len(chosen) < quota:
            raise ValueError(f"Need {quota} difficulty {diff} questions, only have {len(chosen)}")
        selected.extend(chosen)

    counters = {1: 0, 2: 0, 3: 0}
    labels = {1: "easy", 2: "medium", 3: "hard"}
    for q in selected:
        diff = q["difficulty"]
        counters[diff] += 1
        q["id"] = f"law_{labels[diff]}_{counters[diff]:03d}"
    selected.sort(key=lambda q: (q["difficulty"], q["id"]))
    return selected


def validate(questions: list[dict]) -> None:
    ids = [q["id"] for q in questions]
    if len(questions) != 500:
        raise ValueError(f"Expected 500 questions, got {len(questions)}")
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate IDs")
    seen_questions = set()
    for q in questions:
        if q["question"] in seen_questions:
            raise ValueError(f"Duplicate question text: {q['question']}")
        seen_questions.add(q["question"])
        if q["category"] != "indian_law":
            raise ValueError(f"Wrong category in {q['id']}")
        if q["difficulty"] not in {1, 2, 3}:
            raise ValueError(f"Bad difficulty in {q['id']}")
        if len(q["options"]) != 4 or len(set(q["options"])) != 4:
            raise ValueError(f"Bad options in {q['id']}")
        if q["correct_index"] not in {0, 1, 2, 3}:
            raise ValueError(f"Bad correct_index in {q['id']}")
        if not q["options"][q["correct_index"]].strip():
            raise ValueError(f"Blank answer in {q['id']}")


def main() -> None:
    questions = build_questions()
    validate(questions)
    GENERATED.write_text(json.dumps(questions, indent=2) + "\n")

    bank = json.loads(BANK.read_text())
    without_law = [q for q in bank if q.get("category") != "indian_law"]
    without_law.extend(questions)
    BANK.write_text(json.dumps(without_law, indent=2) + "\n")
    print(f"Wrote {len(questions)} Indian Law questions")
    print(f"Merged bank total: {len(without_law)}")


if __name__ == "__main__":
    main()
