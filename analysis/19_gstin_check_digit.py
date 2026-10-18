"""Does the real GSTIN check digit pass on the vendor master's GSTINs?

A real GSTIN is 15 characters: 2 digits of state code, 10 of PAN, an entity number, the letter Z, and a last character that is a check digit computed from the first 14 (base-36 value of each
character, weights 1 and 2 alternating from the left, the digits of each product summed in base 36, check = (36 - sum mod 36) mod 36). If the pack's GSTINs were real the check would pass on all of
them. This script counts how many pass; it does not read analysis/gold_labels.csv or any bill.

Writes analysis/out/figures_gstin.csv.   Run: python -I analysis/19_gstin_check_digit.py
"""
import re
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "analysis" / "out"
CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
SHAPE = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")


def check_char(first14: str) -> str:
    total = 0
    for i, ch in enumerate(first14):
        p = CHARS.index(ch) * (1 if i % 2 == 0 else 2)
        total += p // 36 + p % 36
    return CHARS[(36 - total % 36) % 36]


assert check_char("27AAPFU0939F1Z") == "V"        # a published example GSTIN (27AAPFU0939F1ZV) passes, so the routine is right

con = sqlite3.connect(f"file:{(ROOT / 'pack' / 'data' / 'sap_extract.sqlite').as_posix()}?mode=ro", uri=True)
g = pd.read_sql("select vendor_id, gstin from vendor_master", con).gstin.astype(str).str.strip().str.upper()
shape = g.map(lambda x: bool(SHAPE.match(x)))
passes = g.map(lambda x: bool(SHAPE.match(x)) and check_char(x[:14]) == x[14])
figs = [("g.vendors", len(g), "vendors in the vendor master"),
        ("g.shape_valid", int(shape.sum()), "vendor GSTINs with the right shape (15 characters, state code, PAN, entity, Z, check character)"),
        ("g.check_digit_pass", int(passes.sum()), "vendor GSTINs whose last character is the correct check digit"),
        ("g.check_digit_fail", int((shape & ~passes).sum()), "vendor GSTINs with the right shape whose last character is not the correct check digit")]
pd.DataFrame(figs, columns=["id", "value", "description"]).to_csv(OUT / "figures_gstin.csv", index=False, lineterminator="\n")
for k, v, _ in figs:
    print(f"{k:<20} {v}")
