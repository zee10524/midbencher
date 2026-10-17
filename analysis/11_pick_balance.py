"""Balance check of the AP pick order under two definitions of a verifier's load, as of 30 April 2026.

Definition 1 (the pick order's own): bills in hand = picked and not posted, excluding bills blocked by an open query.
Definition 2: bills in hand including the bills blocked by an open query.
The pick order balances definition 1 only. The check reports the spread (highest above lowest, as a fraction of the lowest) after the pick order has
assigned the waiting bills, against a tolerance of 20%. The counting is not changed to make either check pass.

Reads pack/data only. Writes analysis/out/figures_pickbalance.csv and pick_balance.csv.   Run: python analysis/11_pick_balance.py
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.sap.adapter import SapAdapter  # noqa: E402
from app.tracker import balance_check, control_tower, seed  # noqa: E402
from app.tracker.pickorder import TOLERANCE  # noqa: E402

OUT = ROOT / "analysis" / "out"
with SapAdapter(ROOT / "pack" / "data" / "sap_extract.sqlite") as sap:
    bills = seed(ROOT / "pack" / "data" / "bill_register.csv", ROOT / "pack" / "data" / "queries.csv", sap)
res = balance_check(bills)
tower = control_tower(bills)
figs = [("pb.tolerance_pct", 100 * TOLERANCE, "tolerance: highest verifier load at most this % above the lowest"),
        ("pb.waiting", sum(r["new_from_pick_order"] for r in tower), "bills waiting at head office that the pick order assigns")]
rows = []
for r in tower:
    v = r["verifier"]
    for k, d in [("in_hand", "bills in hand excluding open queries (definition 1), before"), ("open_queries", "bills blocked by an open query"),
                 ("new_from_pick_order", "new bills given by the pick order"), ("in_hand_after", "bills in hand excluding open queries, after")]:
        figs.append((f"pb.{v}.{k}", r[k], f"{v}: {d}"))
    figs.append((f"pb.{v}.def2_after", res["def2"]["after"][v], f"{v}: bills in hand including open queries (definition 2), after"))
    rows.append({**r, "def2_before": res["def2"]["before"][v], "def2_after": res["def2"]["after"][v]})
for k in ("def1", "def2"):
    sp = res[k]["spread"]
    figs.append((f"pb.{k}.spread_pct", 100 * sp if sp != float("inf") else -1, f"after the pick order, highest load above lowest as % of lowest, {k} (-1 = lowest is zero)"))
    figs.append((f"pb.{k}.within", int(res[k]["within_tolerance"]), f"1 if {k} is within the tolerance after the pick order, else 0"))
pd.DataFrame(figs, columns=["id", "value", "description"]).round(3).to_csv(OUT / "figures_pickbalance.csv", index=False, lineterminator="\n")
pd.DataFrame(rows).to_csv(OUT / "pick_balance.csv", index=False, lineterminator="\n")
print(pd.DataFrame(rows).to_string(index=False))
print({k: (round(v["spread"], 3), v["within_tolerance"]) for k, v in res.items()})
