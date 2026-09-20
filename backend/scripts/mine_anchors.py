#!/usr/bin/env python3
"""Mine durable topic anchors from an OCR'd newspaper corpus.

Reading ~1400 OCR pages directly is not viable. This surfaces the entities that
recur ACROSS editions -- the institutions, laws, treaties, schemes and missions
that a period was actually about -- so question generation can target them.

Usage:
  mine_anchors.py --cache ~/.cache/playroom-ocr --from 2026-06-15 --to 2026-09-13
  mine_anchors.py ... --grep "Strait of Hormuz" --context 300
"""
import argparse, os, re, sys, datetime
from collections import Counter, defaultdict

# Durable-concept vocabulary: things that stay true. Deliberately excludes
# people, tolls, scores and prices -- those fail the 1-year durability test.
PATTERNS = {
    "institution": r"\b(?:Supreme Court|High Court|Election Commission|Reserve Bank|RBI|SEBI|NITI Aayog|CAG|UPSC|TRAI|CCI|NGT|Lokpal|Finance Commission|CBI|ED|NIA|ISRO|DRDO|CSIR|ICMR|NHRC|CIC|GST Council|Niti Aayog)\b",
    "law": r"\b(?:Article\s+\d+[A-Z]?|Section\s+\d+[A-Z]*|(?:[A-Z][a-z]+\s+){1,4}(?:Act|Bill|Code|Amendment)(?:,\s*\d{4})?)\b",
    "scheme": r"\b(?:Pradhan Mantri[\w\s]{0,30}|Ayushman Bharat|Jan Aushadhi|Ujjwala|PM-KISAN|Jal Jeevan|MGNREGA|Skill India|Digital India|Make in India|Atmanirbhar|Smart Cities|Swachh Bharat|Ayushman|PLI scheme)\b",
    "intl_body": r"\b(?:United Nations|UNSC|UNESCO|UNICEF|WHO|WTO|IMF|World Bank|BRICS|G7|G20|Quad|ASEAN|SAARC|OPEC|NATO|SCO|IAEA|ICJ|ICC|Interpol|FATF|OECD)\b",
    # "Reserve" must be qualified (Tiger/Biosphere/Wildlife) or "Federal Reserve"
    # and "Reserve Bank" get mined as geography.
    "geography": r"\b(?:Strait of [A-Z]\w{3,}|Gulf of [A-Z]\w{2,}|Bay of [A-Z]\w{2,}|Sea of [A-Z]\w{2,}|(?:[A-Z][a-z]+)\s+(?:River|Glacier|Plateau|Delta|Canal|Sanctuary)|(?:[A-Z][a-z]+)\s+(?:Tiger|Biosphere|Wildlife)\s+Reserve|(?:[A-Z][a-z]+)\s+National Park)\b",
    "treaty": r"\b(?:[A-Z][a-z]+\s+(?:Convention|Protocol|Treaty|Accord|Agreement|Declaration))\b",
    "sci_tech": r"\b(?:Chandrayaan|Gaganyaan|Aditya-L1|Artemis|ISS|PSLV|GSLV|SSLV|Agni-\w+|BrahMos|Tejas|semiconductor|quantum comput\w+|CRISPR|mRNA|thorium|fast breeder|PHWR|green hydrogen|carbon capture)\b",
}

NOISE = re.compile(
    r"^(?:The|This|That|These|Those|There|Their|What|When|Where|Which|While|After|Before|"
    r"Indian Express|Express Group|New Delhi|Late City|Page)\b", re.I)


def editions(cache, frm, to):
    for d in sorted(os.listdir(cache)):
        if not re.match(r"\d{4}-\d{2}-\d{2}$", d):
            continue
        day = datetime.date.fromisoformat(d)
        if frm <= day <= to:
            yield d, os.path.join(cache, d)


def read_edition(path):
    parts = []
    for f in sorted(os.listdir(path)):
        if f.endswith(".txt"):
            with open(os.path.join(path, f), errors="ignore") as fh:
                parts.append(fh.read())
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=os.path.expanduser("~/.cache/playroom-ocr"))
    ap.add_argument("--from", dest="frm", required=True)
    ap.add_argument("--to", dest="to", required=True)
    ap.add_argument("--min-editions", type=int, default=3,
                    help="only report anchors appearing in >= N distinct editions")
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--grep", help="instead of mining, show context around this term")
    ap.add_argument("--context", type=int, default=250)
    args = ap.parse_args()

    frm = datetime.date.fromisoformat(args.frm)
    to = datetime.date.fromisoformat(args.to)
    eds = list(editions(args.cache, frm, to))
    if not eds:
        sys.exit(f"no cached editions in {args.frm}..{args.to} under {args.cache}")

    if args.grep:
        rx = re.compile(re.escape(args.grep), re.I)
        hits = 0
        for date, path in eds:
            text = read_edition(path)
            for m in rx.finditer(text):
                a = max(0, m.start() - args.context)
                snippet = " ".join(text[a:m.end() + args.context].split())
                print(f"--- {date}\n{snippet}\n")
                hits += 1
                if hits >= 40:
                    print(f"[truncated at 40 hits]"); return
        print(f"{hits} hits across {len(eds)} editions")
        return

    # edition-frequency, not raw count: a term repeated 50x in one paper is a
    # one-day story; a term in 20 separate editions is a durable theme.
    per_kind = {k: defaultdict(set) for k in PATTERNS}
    for date, path in eds:
        text = read_edition(path)
        for kind, pat in PATTERNS.items():
            for m in re.finditer(pat, text):
                term = " ".join(m.group(0).split())
                if len(term) < 4 or NOISE.match(term):
                    continue
                per_kind[kind][term].add(date)

    print(f"# Anchors across {len(eds)} editions ({args.frm} .. {args.to})\n")
    for kind in PATTERNS:
        items = per_kind[kind]
        # OCR clips words ("Strait of Hor" alongside "Strait of Hormuz"). Fold a
        # term into a longer one that starts with it and is at least as common.
        drop = set()
        for short in items:
            for long in items:
                if short != long and long.startswith(short) and len(items[long]) >= len(items[short]):
                    drop.add(short); break
        rows = [(len(v), k) for k, v in items.items()
                if len(v) >= args.min_editions and k not in drop]
        rows.sort(reverse=True)
        if not rows:
            continue
        print(f"\n## {kind}  ({len(rows)} anchors in >={args.min_editions} editions)")
        for n, term in rows[:args.top]:
            print(f"{n:4d}  {term}")


if __name__ == "__main__":
    main()
