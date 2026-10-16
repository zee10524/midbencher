"""Generic profile of every file in pack/data and every table in sap_extract.sqlite.

Reads the pack read-only. Writes analysis/out/profile.md.
Run: python analysis/01_profile.py
"""
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "pack" / "data"
OUT = ROOT / "analysis" / "out"
OUT.mkdir(parents=True, exist_ok=True)

lines: list[str] = []


def p(s: str = "") -> None:
    lines.append(s)


def profile(name: str, df: pd.DataFrame) -> None:
    p(f"## {name}")
    p(f"rows={len(df)} cols={len(df.columns)}")
    p("")
    p("| column | non-null | null | blank | unique | min | max | sample |")
    p("|---|---|---|---|---|---|---|---|")
    for c in df.columns:
        s = df[c]
        null = int(s.isna().sum())
        blank = int((s.astype(str).str.strip() == "").sum()) if s.dtype == object else 0
        nn = s.dropna()
        try:
            mn, mx = nn.min(), nn.max()
        except Exception:
            mn = mx = ""
        sample = " / ".join(map(str, nn.astype(str).unique()[:3]))[:60]
        p(f"| {c} | {len(nn)} | {null} | {blank} | {nn.nunique()} | {str(mn)[:25]} | {str(mx)[:25]} | {sample} |")
    p("")


for f in sorted(DATA.rglob("*.csv")):
    df = pd.read_csv(f, dtype=str, keep_default_na=False, na_values=[])
    # treat empty string as blank, not NA, so blank counts are visible
    profile(str(f.relative_to(DATA)), df)

con = sqlite3.connect(f"file:{(DATA / 'sap_extract.sqlite').as_posix()}?mode=ro", uri=True)
tables = [r[0] for r in con.execute("select name from sqlite_master where type='table' order by 1")]
p("# sap_extract.sqlite")
for t in tables:
    ddl = con.execute("select sql from sqlite_master where name=?", (t,)).fetchone()[0]
    p(f"```sql\n{ddl}\n```")
    df = pd.read_sql_query(f'select * from "{t}"', con)
    profile(f"sqlite:{t}", df)
con.close()

(OUT / "profile.md").write_text("\n".join(lines), encoding="utf-8")
print("wrote", OUT / "profile.md")
