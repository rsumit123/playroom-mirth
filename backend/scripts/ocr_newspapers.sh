#!/usr/bin/env bash
# OCR Indian Express newspaper PDFs into a stable text cache.
#
# Usage: ocr_newspapers.sh <pdf_dir> <from:YYYY-MM-DD> <to:YYYY-MM-DD> [parallelism]
#
# Output: $OCR_CACHE/<YYYY-MM-DD>/pNN.txt  (default cache: ~/.cache/playroom-ocr)
# Re-runnable: editions with a .done marker are skipped.

set -uo pipefail

PDF_DIR="${1:?usage: ocr_newspapers.sh <pdf_dir> <from> <to> [parallelism]}"
FROM="${2:?missing from date}"
TO="${3:?missing to date}"
JOBS="${4:-6}"
CACHE="${OCR_CACHE:-$HOME/.cache/playroom-ocr}"

command -v pdftoppm >/dev/null || { echo "need poppler: brew install poppler" >&2; exit 1; }
command -v tesseract >/dev/null || { echo "need tesseract: brew install tesseract" >&2; exit 1; }

mkdir -p "$CACHE"

# Resolve PDFs in range -> "YYYY-MM-DD<TAB>/abs/path.pdf"
python3 - "$PDF_DIR" "$FROM" "$TO" <<'PY' > "$CACHE/_worklist.tsv"
import os, re, sys, datetime
pdf_dir, frm, to = sys.argv[1], sys.argv[2], sys.argv[3]
frm = datetime.date.fromisoformat(frm); to = datetime.date.fromisoformat(to)
seen = {}
for f in sorted(os.listdir(pdf_dir)):
    if not f.lower().endswith(".pdf"):
        continue
    m = re.match(r"Kolkata-+([A-Za-z]+)-+(\d+)-+(\d+)", f)
    if not m:
        print(f"SKIP unparsed: {f}", file=sys.stderr); continue
    mon, day, yr = m.groups()
    try:
        d = datetime.datetime.strptime(f"{mon} {day} {yr}", "%B %d %Y").date()
    except ValueError:
        print(f"SKIP bad date: {f}", file=sys.stderr); continue
    if not (frm <= d <= to):
        continue
    # Prefer the plain filename over a " (1)" duplicate of the same date
    if d in seen and "(" not in seen[d]:
        continue
    seen[d] = f
for d in sorted(seen):
    print(f"{d}\t{os.path.join(pdf_dir, seen[d])}")
PY

TOTAL=$(wc -l < "$CACHE/_worklist.tsv" | tr -d ' ')
echo "[ocr] $TOTAL editions in range $FROM..$TO -> $CACHE (parallelism=$JOBS)"

ocr_edition() {
    local date="$1" pdf="$2" cache="$3"
    local out="$cache/$date"
    if [ -f "$out/.done" ]; then
        echo "[ocr] $date already cached, skipping"; return 0
    fi
    mkdir -p "$out"
    local tmp; tmp=$(mktemp -d)

    # Materialise the file if iCloud is holding it as a dataless placeholder,
    # otherwise every read stalls on a network fetch.
    cat "$pdf" > /dev/null 2>&1

    # Render the WHOLE pdf in ONE pdftoppm call. Calling it per-page re-parses
    # (and, for iCloud placeholders, re-fetches) the entire PDF each time --
    # that made this ~10x slower than the per-page CPU cost predicts.
    if ! pdftoppm -png -r 200 "$pdf" "$tmp/pg" 2>/dev/null; then
        echo "[ocr] $date FAILED: pdftoppm could not render" >&2
        rm -rf "$tmp"; return 1
    fi

    local png pp n=0
    for png in "$tmp"/pg*.png; do
        [ -e "$png" ] || continue
        pp=$(basename "$png" .png); pp=${pp##pg-}
        if [ ! -s "$out/p$pp.txt" ]; then
            tesseract "$png" "$out/p$pp" --psm 3 >/dev/null 2>&1
        fi
        rm -f "$png"
        n=$((n + 1))
    done
    rm -rf "$tmp"

    if [ "$n" -ge 1 ]; then
        date > "$out/.done"
        echo "[ocr] $date done ($n pages, $(cat "$out"/p*.txt 2>/dev/null | wc -c | tr -d ' ') chars)"
    else
        echo "[ocr] $date FAILED: no pages produced" >&2
    fi
}
export -f ocr_edition

# Bounded-parallelism loop (xargs -I word-splits paths containing spaces).
while IFS=$'\t' read -r d pdf; do
    [ -z "$d" ] && continue
    while [ "$(jobs -rp | wc -l)" -ge "$JOBS" ]; do wait -n 2>/dev/null || sleep 1; done
    ocr_edition "$d" "$pdf" "$CACHE" &
done < "$CACHE/_worklist.tsv"
wait

echo "[ocr] complete. cached editions: $(ls -d "$CACHE"/2* 2>/dev/null | wc -l | tr -d ' ')"
