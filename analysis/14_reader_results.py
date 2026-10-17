"""What the reader did with the 40 files in the bill inbox: how many are ok and how many go to review, by bill type, and why.

Reads only the reader's own cached results (app/reader/cache/*.json, written by `python -m app.reader`). It does not read any label file and does not compare the
reader with any answer: the counts are about the reader's own confidence, not its accuracy.

Writes analysis/out/figures_reader.csv.   Run: python analysis/14_reader_results.py
"""
import json
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "analysis" / "out"
res = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "app" / "reader" / "cache").glob("*.json"))]
REQUIRED = ["vendor_gstin", "vendor_name", "invoice_no", "invoice_date", "wo_id", "taxable", "total"]
figs = []
for key in ["all", "pdf_single", "pdf_packet", "phone_photo"]:
    rs = [r for r in res if key == "all" or r["bill_type"] == key]
    ok = sum(r["status"] == "ok" for r in rs)
    hl = sum(r["status"] != "ok" and r["route_hint"] == "human-look" for r in rs)
    rsd = sum(r["status"] != "ok" and r["route_hint"] == "resend" for r in rs)
    figs += [(f"rd.{key}.files", len(rs), f"files read ({key})"), (f"rd.{key}.ok", ok, f"files the reader passes with every required field at 0.90 or more and amounts that add up ({key})"),
             (f"rd.{key}.review", len(rs) - ok, f"files that go to review ({key})"), (f"rd.{key}.review.human_look", hl, f"of the review files, lowest required confidence 0.70 to 0.90 ({key})"),
             (f"rd.{key}.review.resend", rsd, f"of the review files, a required field missing or below 0.70 ({key})")]
    for fld in REQUIRED:
        missing = sum((r["fields"].get(fld) or {}).get("value") is None for r in rs)
        low = sum((r["fields"].get(fld) or {}).get("value") is not None and (r["fields"][fld]["conf"] < 0.9) for r in rs)
        figs += [(f"rd.{key}.{fld}.not_found", missing, f"files where {fld} was not found ({key})"), (f"rd.{key}.{fld}.below_090", low, f"files where {fld} was found with confidence below 0.90 ({key})")]
    figs.append((f"rd.{key}.arithmetic_fail", sum(r.get("arithmetic_ok") is False for r in rs), f"files where taxable value plus tax does not equal the total, or a tax line does not match its rate ({key})"))
pk = [r for r in res if r["bill_type"] == "pdf_packet"]
for d in ["attendance", "challan", "service_report", "pf_esic"]:
    figs.append((f"rd.packets.has_{d}", sum(bool(r["supporting"].get(d)) for r in pk), f"packets with a {d} page recognised"))
figs.append(("rd.packets.no_support", sum(not any(r["supporting"].values()) for r in pk), "packets with no supporting page recognised"))
figs.append(("rd.credit_notes", sum(r.get("doc_type") == "credit_note" for r in res), "files read as a credit note"))
figs.append(("rd.no_gst", sum(bool(r.get("no_gst_printed")) for r in res), "files that print 'GST not applicable'"))
figs.append(("rd.text_layer_fast_path", sum(bool(r["reader"].get("text_layer_fast_path")) for r in res), "files read through the pdfplumber text-layer fast path (expected 0)"))
figs.append(("rd.simulated", sum(bool(r["reader"].get("simulated")) for r in res), "cached results marked reader simulated"))
pd.DataFrame(figs, columns=["id", "value", "description"]).to_csv(OUT / "figures_reader.csv", index=False, lineterminator="\n")
print(f"{len(res)} cached results; {len(figs)} figures")
c = Counter(r["route_hint"] for r in res)
print(dict(c))
