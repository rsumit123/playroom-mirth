#!/usr/bin/env python3
"""Label each OCR'd newspaper page by section, so generation reads only high-yield pages.

Page numbers for Explained/Editorial/World shift between editions, so they must be
detected from section headers rather than hard-coded.

Usage:
  classify_pages.py --from 2026-06-15 --to 2026-09-13            # summary
  classify_pages.py --from ... --to ... --sections explained,editorial --paths
"""
import argparse, os, re, datetime, collections

# Ordered: first match wins, so the specific beats the generic.
SECTIONS = [
    ("explained",  r"#?ExpressExplained|\bExplained\b\s*$|Express\s*Explained|\bEXPLAINED\b"),
    ("editorial",  r"The Editorial Page|WORDLY WISE|BECAUSE THE TRUTH\s+INVOLVES US ALL"),
    ("ideas",      r"The Ideas Page|WHAT THE OTHERS SAY|READ\.\s*THINK\.\s*SHARE"),
    ("world",      r"\bThe World\b|\bWORLD\b\s*$|International News"),
    ("economy",    r"\bThe Economy\b|\bECONOMY\b\s*$|Business As Usual|\bMARKETS?\b\s*$"),
    ("govt",       r"Governance & Policy|\bThe Nation\b|\bNATION\b\s*$"),
    ("front",      r"LATE CITY|WWW\.INDIANEXPRESS\.COM"),
    ("sport",      r"\bThe Sports? Page\b|\bSPORT\b\s*$"),
]

# High-yield for durable-concept questions, in priority order.
PREFERRED = ["explained", "editorial", "ideas", "world", "economy", "govt", "front"]


def classify(text: str) -> str:
    head = "\n".join(text.splitlines()[:60])
    for name, pat in SECTIONS:
        if re.search(pat, head, re.I | re.M):
            return name
    return "other"


def walk(cache, frm, to):
    for d in sorted(os.listdir(cache)):
        if not re.match(r"\d{4}-\d{2}-\d{2}$", d):
            continue
        day = datetime.date.fromisoformat(d)
        if not (frm <= day <= to):
            continue
        path = os.path.join(cache, d)
        if not os.path.isfile(os.path.join(path, ".done")):
            continue
        for f in sorted(os.listdir(path)):
            if f.endswith(".txt"):
                fp = os.path.join(path, f)
                with open(fp, errors="ignore") as fh:
                    yield d, f, fp, classify(fh.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=os.path.expanduser("~/.cache/playroom-ocr"))
    ap.add_argument("--from", dest="frm", required=True)
    ap.add_argument("--to", dest="to", required=True)
    ap.add_argument("--sections", default=None,
                    help="comma list; default = the high-yield set")
    ap.add_argument("--paths", action="store_true", help="print file paths only")
    args = ap.parse_args()

    frm = datetime.date.fromisoformat(args.frm)
    to = datetime.date.fromisoformat(args.to)
    want = (args.sections.split(",") if args.sections else PREFERRED)

    rows = list(walk(args.cache, frm, to))
    if args.paths:
        for date, page, fp, sec in rows:
            if sec in want:
                print(fp)
        return

    counts = collections.Counter(sec for _, _, _, sec in rows)
    eds = len({d for d, _, _, _ in rows})
    print(f"{len(rows)} pages across {eds} complete editions\n")
    for sec, n in counts.most_common():
        mark = "*" if sec in want else " "
        print(f" {mark} {sec:10s} {n:5d}")
    sel = sum(n for s, n in counts.items() if s in want)
    print(f"\nselected ({','.join(want)}): {sel} pages "
          f"~{sel * 20000 // 4000}k tokens if read in full")


if __name__ == "__main__":
    main()
