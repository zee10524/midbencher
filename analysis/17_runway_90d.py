"""Which work orders are about to run dry, with the burn rate taken from the last 90 days of billing instead of the order's whole life.

The earlier runway view divided an order's balance by its lifetime-average monthly billing (`app/tracker/runway.py`), which flags many orders with a few rupees left. Here the burn is
what the order was actually billed in the 90 days before 30 April 2026 (invoices and credit notes by desk-received date), as a daily rate, and an order is likely to run dry when its
balance (approved less billed in the SAP extract) is above zero, it has not expired, and the balance covers 45 days or fewer of that billing. Ranked by monthly billing, biggest first.

Also counted: how many of those orders have a vendor with a bill already waiting (an open bill in the register: not yet paid), and how many have a bill waiting on that order itself.

Writes backtest/out/runway_90d.csv and analysis/out/figures_runway.csv.   Run: python analysis/17_runway_90d.py
"""
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.sap.adapter import AS_OF, DAYS_PER_MONTH, SapAdapter  # noqa: E402
from app.tracker.runway import runway  # noqa: E402
from app.tracker import seed  # noqa: E402

OUT = ROOT / "analysis" / "out"
WINDOW, HORIZON = 90, 45
b = pd.read_parquet(OUT / "bills_clean.parquet")
since = pd.Timestamp(AS_OF - timedelta(days=WINDOW))
win = b[(b.desk_received_date > since) & (b.desk_received_date <= pd.Timestamp(AS_OF))]
billing = win.groupby("wo_id").amount_inr.sum()
open_b = b[b.status != "Paid"]
open_v, open_w = set(open_b.vendor_id), set(open_b.wo_id)
con = sqlite3.connect(f"file:{(ROOT / 'pack' / 'data' / 'sap_extract.sqlite').as_posix()}?mode=ro", uri=True)
wo = pd.read_sql("select * from work_orders", con).set_index("wo_id")
vn = pd.read_sql("select vendor_id, vendor_name from vendor_master", con).set_index("vendor_id").vendor_name
rows = []
for wid, bill in billing.items():
    r = wo.loc[wid]
    approved, billed = float(r.approved_value_inr), float(r.billed_value_inr)
    remaining = approved - billed
    vt = pd.Timestamp(r.valid_to)
    vf = pd.Timestamp(r.valid_from)
    to_end = (vt - pd.Timestamp(AS_OF)).days
    if remaining <= 0 or vt < vf or to_end < 0 or bill <= 0:
        continue
    per_day = bill / WINDOW
    days = remaining / per_day
    if days <= HORIZON:
        rows.append(dict(wo_id=wid, vendor_id=r.vendor_id, vendor_name=vn.get(r.vendor_id, ""), property_code=r.property_code, balance_inr=round(remaining), billing_90d_inr=round(bill),
                         monthly_billing_inr=round(per_day * DAYS_PER_MONTH), runway_days=round(days, 1), days_to_expiry=to_end, vendor_has_bill_waiting=r.vendor_id in open_v, wo_has_bill_waiting=wid in open_w))
D = pd.DataFrame(rows).sort_values(["monthly_billing_inr", "wo_id"], ascending=[False, True])
(ROOT / "backtest" / "out").mkdir(parents=True, exist_ok=True)
D.to_csv(ROOT / "backtest" / "out" / "runway_90d.csv", index=False)

with SapAdapter(ROOT / "pack" / "data" / "sap_extract.sqlite") as sap:
    old = [x for x in runway(seed(ROOT / "pack" / "data" / "bill_register.csv", ROOT / "pack" / "data" / "queries.csv", sap), sap)
           if x["kind"] == "ahead" and any("balance runs out" in f for f in x["flags"])]
figs = [("rw.window_days", WINDOW, "days of billing before 30 April 2026 that the burn rate is taken from"),
        ("rw.horizon_days", HORIZON, "an order is likely to run dry when its balance covers this many days or fewer of its recent billing"),
        ("rw.orders_billed_90d", len(billing), "work orders with any billing in the last 90 days"),
        ("rw.dry", len(D), "work orders likely to run dry within 45 days, burn estimated from the last 90 days of billing"),
        ("rw.dry.vendor_waiting", int(D.vendor_has_bill_waiting.sum()), "of those, orders whose vendor has a bill already waiting (an open bill in the register)"),
        ("rw.dry.wo_waiting", int(D.wo_has_bill_waiting.sum()), "of those, orders with a bill already waiting on that order itself"),
        ("rw.dry.monthly_billing_inr", int(D.monthly_billing_inr.sum()), "monthly billing, rupees, on those orders (last 90 days, per 30.4375 days)"),
        ("rw.dry_lifetime", len(old), "for comparison: the same view using each order's lifetime-average burn (the earlier headline)")]
pd.DataFrame(figs, columns=["id", "value", "description"]).to_csv(OUT / "figures_runway.csv", index=False)
for k, v, _ in figs:
    print(f"{k:<28} {v}")
print(D.head(6).to_string(index=False))
