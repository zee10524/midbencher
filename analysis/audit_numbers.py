"""Find figures in the text that have no source in notes/numbers.md.

Reads the registered values from notes/numbers.md (the Value column) and every number written in README.md and notes/*.md (outside notes/numbers.md itself), and lists the numbers that
match no registered value. A number matches when it equals a registered value at the precision it is written in, or that value as a percentage, in lakh or crore, or in thousands.
Skipped as not being figures: dates, years, ids (bill-28, V10444, H13), version strings, line and section references, and bare whole numbers under 100 that are not followed by a unit.

This finds candidates, not errors: a person reads each one (see notes/number-audit.md). It does not read analysis/gold_labels.csv.

Run: python -I analysis/audit_numbers.py            (prints the list; writes nothing)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NUM = ROOT / "notes" / "numbers.md"
NUM_RX = re.compile(r"(?<![\w./#-])(?:₹|Rs\s?)?(\d{1,3}(?:,\d{2,3})+(?:\.\d+)?|\d+(?:\.\d+)?)(\s?(?:%|per cent|crore|lakh|days?|bills?|bill|invoices?|work orders?|orders?|vendors?|hours?))?", re.I)
DATE_RX = re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}(?:st|nd|rd|th)? (?:January|February|March|April|May|June|July|August|September|October|November|December)(?: \d{4})?\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{4}\b|\bFY ?\d{2,4}[-/]\d{2,4}\b|\b\d{2}/\d{2}-\d{2}\b")


def registered() -> list[float]:
    vals = []
    for ln in NUM.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*([\w.\-/<>]+)\s*\|\s*(-?[\d.,]+(?:e[+-]?\d+)?)\s*\|", ln)
        if m and m.group(1) not in ("Figure", "---"):
            try:
                vals.append(float(m.group(2).replace(",", "")))
            except ValueError:
                pass
    return vals


def matches(x: float, decimals: int, vals: list[float]) -> bool:
    for v in vals:
        for k in (1, 100, 1e-2, 1e5, 1e7, 1e3, 1e-3):
            if round(v * k if k in (1, 100, 1e-2) else v / k, decimals) == round(x, decimals):
                return True
    return False


def scan(path: Path, vals: list[float]) -> list[tuple[int, str, str]]:
    out = []
    in_code = False
    for i, ln in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if ln.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code or ln.lstrip().startswith("|---"):
            continue
        clean = DATE_RX.sub(" ", re.sub(r"`[^`]*`", " ", ln))            # ids and commands in backticks are not figures
        for m in NUM_RX.finditer(clean):
            raw, unit = m.group(1), (m.group(2) or "").strip()
            x = float(raw.replace(",", ""))
            dec = len(raw.split(".")[1]) if "." in raw else 0
            if re.fullmatch(r"(19|20)\d\d", raw) or (dec == 0 and x < 100 and not unit) or raw.startswith("0") and dec == 0 and len(raw) > 1:
                continue
            if not matches(x, dec, vals):
                out.append((i, raw + (" " + unit if unit else ""), ln.strip()[:150]))
    return out


if __name__ == "__main__":
    vals = registered()
    print(f"{len(vals)} registered values")
    files = [ROOT / "README.md", *sorted((ROOT / "notes").glob("*.md"))]
    total = 0
    for f in files:
        if f.name == "numbers.md":
            continue
        hits = scan(f, vals)
        total += len(hits)
        print(f"\n== {f.relative_to(ROOT)}: {len(hits)} with no registered source")
        for i, tok, ctx in hits:
            print(f"  {i}: [{tok}] {ctx}")
    print(f"\n{total} figures with no registered source")
    sys.exit(0)
