"""Score the reader against the 10 hand-labelled bills (analysis/gold_labels.csv), field by field. The labels file is only read, never written.

Two scores come from the same frozen reader output. The FIRST-RUN score uses the labels as first given. The user then corrected one label (bill-28 amount, which the page
image shows was a digit swap) by hand, and the SECOND score uses the labels as they are now. The first-given set is the current file with that one cell put back to what it
was (AS_FIRST_GIVEN), so the first-run numbers stay exactly as first recorded. The file is re-saved by Excel in places with day-first dates and amounts without trailing
zeros; that is formatting only and is normalised in memory here, as the evaluation rules say.

FIRST-RUN score: scored from analysis/reader_first_run.json, a frozen copy of the reader's output taken before any reader code or tuning saw the labels. It is never
overwritten, so the first-run score cannot move. If the live reader cache later differs in any value or confidence, a separate POST-FIX section is added and
labelled as tuned on these 10 bills.

Only formatting is normalised: spaces trimmed, names compared ignoring case, amounts compared as numbers, dates as YYYY-MM-DD. The label `amount` is compared with the
reader's grand total (taxable plus tax). Anything else counts as a miss: a field the reader did not read (None) is a miss, and so is a different value.

Writes analysis/out/figures_reader_eval.csv and notes/reader-evaluation.md.   Run: python analysis/15_reader_evaluation.py
"""
import csv
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "analysis" / "out"
LABELS = ROOT / "analysis" / "gold_labels.csv"
FIELDS = {"vendor_name": "vendor_name", "invoice_number": "invoice_no", "invoice_date": "invoice_date", "amount": "total", "gstin": "vendor_gstin", "po_or_wo_number": "wo_id"}
KEY = ["invoice_number", "invoice_date", "amount", "gstin"]
TYPES = ["pdf_single", "pdf_packet", "phone_photo"]
BAND = [("0.90 or more", 0.90, 2.0), ("0.70 to 0.90", 0.70, 0.90), ("below 0.70 (or not read)", -1.0, 0.70)]

# Analyst judgement, written after reading the OCR text and, for the starred cases, looking at the page image. Keyed by (file, label column).
CAUSE = {
    ("bill-14.pdf", "gstin"): "OCR inserted a spurious character after the leading 0 (`0O3GSNPI5677B1ZK`, 16 characters). The reader rejects a GSTIN that is not 15 characters rather than drop one, so nothing was read.",
    ("packet-10-credit-note.pdf", "gstin"): "Same artefact: `0O9LGQFQ3122D1ZY`, 16 characters, rejected. The reader keeps no value when the shape is wrong.",
    ("bill-16.jpg", "invoice_number"): "A stray apostrophe before the number (`Invoice No: '751/25-26/346`) on a noisy photo (line confidence 0.69). The label pattern does not allow punctuation after `No:`, so the number and the date on that line were both missed.",
    ("bill-16.jpg", "invoice_date"): "Same line as the invoice number: the date follows it and was lost with it.",
    ("bill-23.jpg", "amount"): "The first digit of the total was unreadable on the photo (`Total �,35,967.80`). The reader reads no value rather than guess. (Taxable value plus IGST would give the right total, but the reader does not derive values.)",
    ("bill-23.jpg", "gstin"): "Photo blur: the printed `06IXXFO6273K1ZU` was read `06D00F06273K1ZU`, and the position repair turned the zeros into letters (`06DOOFO6273K1ZU`). Shape and state both look valid, so the wrong GSTIN got 0.80. A miscalibration, not an abstention.",
    ("bill-28.jpg", "amount"): "*Label error, since corrected by the user.* The reader read 4,14,616.60. The page image shows taxable value 3,51,370.00, IGST @ 18% 63,246.60 and Total 4,14,616.60, and 3,51,370.00 + 63,246.60 is 4,14,616.60. The label as first given, 4,41,616.60, had two digits swapped. In the first-run score it counts as a miss because the labels file was the reference then; the second score uses the corrected label.",
    ("bill-28.jpg", "gstin"): "Photo blur: `06DUMCV9219I1ZB` was read with the D as an O (`06OUMCV9219I1ZB`). Shape and state both look valid, so it got 0.80. A miscalibration.",
}
SUSPECT_LABEL = {("bill-28.jpg", "amount")}
AS_FIRST_GIVEN = {("bill-28.jpg", "amount"): "441616.60"}   # the label before the user corrected it


def norm(label, v):
    if v is None:
        return None
    if label == "amount":
        return round(float(v), 2)
    if label == "vendor_name":
        return " ".join(str(v).split()).upper()
    return str(v).strip()


def score(results: dict, gold: list[dict]) -> pd.DataFrame:
    rows = []
    for g in gold:
        r = results[g["file"]]
        for lab, fld in FIELDS.items():
            x = (r.get("fields") or {}).get(fld) or {}
            read, conf = norm(lab, x.get("value")), float(x.get("conf", 0.0) or 0.0)
            want = norm(lab, float(g[lab]) if lab == "amount" and g[lab].strip() else g[lab].strip())
            rows.append(dict(file=g["file"], bill_type=g["bill_type"], field=lab, label=want, read=read, conf=conf, correct=read is not None and read == want,
                             not_read=read is None, status=r["status"], route=r["route_hint"]))
    return pd.DataFrame(rows)


def tables(df: pd.DataFrame) -> dict:
    per = {t: df[df.bill_type == t].groupby("field").correct.agg(["sum", "count"]) for t in [*TYPES]}
    allf = df.groupby("field").correct.agg(["sum", "count"])
    full = {}
    for t in [*TYPES, "all"]:
        sub = df if t == "all" else df[df.bill_type == t]
        k = sub[sub.field.isin(KEY)].groupby("file").correct.all()
        full[t] = (int(k.sum()), len(k))
    cal = []
    for name, lo, hi in BAND:
        sub = df[(df.conf >= lo) & (df.conf < hi)] if lo >= 0 else df[df.conf < hi]
        cal.append((name, len(sub), int(sub.correct.sum())))
    return dict(per=per, all=allf, full=full, cal=cal)


def section(title, df, gold):
    T = tables(df)
    L = [f"## {title}", "", "### 1. Per-field accuracy by bill type (correct of read)", "", "| Field | pdf_single (3) | pdf_packet (3) | phone_photo (4) | All (10) |", "|---|---|---|---|---|"]
    for lab in FIELDS:
        cells = [f"{int(T['per'][t].loc[lab, 'sum'])} of {int(T['per'][t].loc[lab, 'count'])}" for t in TYPES]
        L.append(f"| {lab} | " + " | ".join(cells) + f" | {int(T['all'].loc[lab, 'sum'])} of {int(T['all'].loc[lab, 'count'])} |")
    tot = {t: (int(df[df.bill_type == t].correct.sum()), len(df[df.bill_type == t])) for t in TYPES}
    L.append("| **All six fields** | " + " | ".join(f"{a} of {b}" for a, b in tot.values()) + f" | **{int(df.correct.sum())} of {len(df)}** |")
    L += ["", "### 2. Bills fully correct on the four key fields (invoice_number, invoice_date, amount, gstin)", "", "| | pdf_single | pdf_packet | phone_photo | All |", "|---|---|---|---|---|",
          "| Bills correct on all four | " + " | ".join(f"{T['full'][t][0]} of {T['full'][t][1]}" for t in [*TYPES, "all"]) + " |", ""]
    ok = df[df.field.isin(KEY)].groupby("file").correct.all()
    L.append("Fully correct: " + ", ".join(f"`{f}`" for f in ok[ok].index) + ". Not: " + ", ".join(f"`{f}`" for f in ok[~ok].index) + ".")
    return L, T


def build(results, gold, title):
    df = score(results, gold)
    L, T = section(title, df, gold)
    L += ["", "### 3. Is confidence calibrated?", "", "Every reading (10 bills x 6 fields = 60) is placed in a confidence band and checked against the label.", "",
          "| Confidence band | Readings | Correct | Share correct |", "|---|---|---|---|"]
    for name, n, c in T["cal"]:
        L.append(f"| {name} | {n} | {c} | {100 * c / n:.0f}% |" if n else f"| {name} | 0 | 0 | |")
    bystatus = df[df.field.isin(KEY)].groupby(["file", "status", "route"]).correct.all().reset_index()
    L += ["", "By the reader's verdict on each bill (all four key fields right or not):", "", "| Verdict | Bills | All four key fields right |", "|---|---|---|"]
    for route, g in bystatus.groupby("route"):
        L.append(f"| {route} | {len(g)} | {int(g.correct.sum())} |")
    wrong = df[(~df.correct)]
    conf_wrong = wrong[wrong.conf >= 0.70]
    L += ["", f"**Reading.** {len(wrong)} of {len(df)} readings are wrong or missing. {len(wrong) - len(conf_wrong)} of them carry a confidence below 0.70 (including the fields the reader declined to read), so the reader itself flagged them. "
          f"{len(conf_wrong)} are wrong at a confidence of 0.70 or more: " + "; ".join(f"`{r.file}` {r.field} (read `{r.read}`, confidence {r.conf:.2f})" for r in conf_wrong.itertuples()) + ". "
          "Those are the dangerous cases: a wrong value that is not flagged as unreliable. Both are GSTINs read from phone photos, at the 0.80 level that the reader gives when the shape is valid and the state agrees.", "",
          "**Ten bills are far too few to say whether the confidence is calibrated.** Each band holds only a handful of readings, one reading moves a percentage by several points, and the fields, the vendors and the photos are not a random sample. "
          "What can be said is narrow: on these ten, the 0.97 amounts were right every time, the 0.95 and above GSTINs were right every time, and the 0.80 GSTINs were right only some of the time, so 0.80 looks too high for a GSTIN read from a photo. "
          "Calibration needs the 40 labelled bills at the least, and a different set from the one used to tune."]
    L += ["", "### 4. Failures: the label, what the reader read, and the likely cause", "", "| Bill | Field | Label | Reader read | Confidence | Likely cause |", "|---|---|---|---|---|---|"]
    for r in wrong.itertuples():
        L.append(f"| `{r.file}` ({r.bill_type}) | {r.field} | `{r.label}` | {'`' + str(r.read) + '`' if r.read is not None else 'nothing (not read)'} | {r.conf:.2f} | {CAUSE.get((r.file, r.field), '(no analysis yet)')} |")
    return L, df, T


def load_labels() -> list[dict]:
    """The labels with formatting normalised in memory: dates as YYYY-MM-DD (day-first dates are converted), amounts as plain numbers, spaces trimmed."""
    out = []
    for r in csv.DictReader(open(LABELS, encoding="utf-8", newline="")):
        r = {k: (v or "").strip() for k, v in r.items()}
        m = re.fullmatch(r"(\d{2})-(\d{2})-(\d{4})", r["invoice_date"])
        if m:
            r["invoice_date"] = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
        r["amount"] = f"{float(r['amount'].replace(',', '')):.2f}"
        out.append(r)
    return out


gold = load_labels()
gold_first = [dict(g, **{lab: val for (f, lab), val in AS_FIRST_GIVEN.items() if f == g["file"]}) for g in gold]
assert any(float(a["amount"]) != float(g["amount"]) for g, a in zip(gold, gold_first) if g["file"] == "bill-28.jpg"), "the bill-28 amount label has not been corrected, or was changed back"
snap = json.loads((ROOT / "analysis" / "reader_first_run.json").read_text(encoding="utf-8"))
L1, df1, T1 = build(snap["results"], gold_first, f"FIRST-RUN score (reader {snap['reader_version']}, frozen before any tuning; labels as first given)")
L_second, df2, T2 = build(snap["results"], gold, "SECOND score")
live = {g["file"]: json.loads((ROOT / "app" / "reader" / "cache" / f"{g['file']}.json").read_text(encoding="utf-8")) for g in gold}
df_live = score(live, gold)
changed = not df1[["file", "field", "read", "conf"]].reset_index(drop=True).equals(df_live[["file", "field", "read", "conf"]].reset_index(drop=True))
POST_TITLE = "post-fix, tuned after seeing the first-run failures on these 10 bills"
if changed:
    L_post, df_post, T_post = build(live, gold, "POST-FIX: " + POST_TITLE)


def effect() -> dict:
    """The effect of the post-fix reader on all 40 bills, before (the cache saved just before the fixes) and after (the live cache), using the same checks and the same register."""
    sys.path.insert(0, str(ROOT))
    from app.intake import check_bill
    from app.rules import Context
    from app.sap.adapter import SapAdapter
    from app.tracker import seed
    req = ["vendor_gstin", "vendor_name", "invoice_no", "invoice_date", "wo_id", "taxable", "total"]
    out = {}
    with SapAdapter(ROOT / "pack" / "data" / "sap_extract.sqlite") as sap:
        ctx = Context(sap, seed(ROOT / "pack" / "data" / "bill_register.csv", ROOT / "pack" / "data" / "queries.csv", sap), bill_counted_in_billed=True)
        for tag, folder in (("before", ROOT / "analysis" / "reader_cache_before_part1c"), ("after", ROOT / "app" / "reader" / "cache")):
            rs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(folder.glob("*.json"))]
            low = ok = full = some = complete = 0
            for r in rs:
                before_low = low
                for k in req:
                    x = (r["fields"].get(k) or {})
                    if k == "wo_id" and x.get("value") is None and "printed blank" in x.get("note", ""):
                        continue
                    low += x.get("value") is None or float(x.get("conf", 0) or 0) < 0.70
                complete += low == before_low
                ok += r["status"] == "ok"
                o = check_bill(r, ctx)
                full += not o["not_run"]
                some += bool(o["results"])
            out[tag] = dict(files=len(rs), low=int(low), reader_ok=int(ok), full_verdict=int(full), some_verdict=int(some), complete_read=int(complete))
    return out


EFF = effect() if changed else None

figs = []
for t in [*TYPES, "all"]:
    sub = df1 if t == "all" else df1[df1.bill_type == t]
    figs.append((f"re.first.{t}.fields_correct", int(sub.correct.sum()), f"first run, {t}: field readings correct"))
    figs.append((f"re.first.{t}.fields_total", len(sub), f"first run, {t}: field readings scored"))
    figs.append((f"re.first.{t}.key_bills_correct", T1["full"][t][0], f"first run, {t}: bills correct on all four key fields"))
    figs.append((f"re.first.{t}.bills", T1["full"][t][1], f"first run, {t}: bills"))
    for lab in FIELDS:
        s = sub[sub.field == lab]
        figs.append((f"re.first.{t}.{lab}.correct", int(s.correct.sum()), f"first run, {t}: {lab} correct (of {len(s)})"))
for name, n, c in T1["cal"]:
    k = {"0.90 or more": "hi", "0.70 to 0.90": "mid"}.get(name, "lo")
    figs += [(f"re.first.cal.{k}.n", n, f"first run: readings with confidence {name}"), (f"re.first.cal.{k}.correct", c, f"first run: of those, correct")]
figs.append(("re.first.wrong_conf_070_plus", int(((~df1.correct) & (df1.conf >= 0.70)).sum()), "first run: wrong readings with confidence 0.70 or more"))
for t in [*TYPES, "all"]:
    sub = df2 if t == "all" else df2[df2.bill_type == t]
    figs.append((f"re.second.{t}.fields_correct", int(sub.correct.sum()), f"second score (label corrected), {t}: field readings correct"))
    figs.append((f"re.second.{t}.key_bills_correct", T2["full"][t][0], f"second score, {t}: bills correct on all four key fields"))
    for lab in FIELDS:
        figs.append((f"re.second.{t}.{lab}.correct", int(sub[sub.field == lab].correct.sum()), f"second score, {t}: {lab} correct"))
for name, n, c in T2["cal"]:
    k = {"0.90 or more": "hi", "0.70 to 0.90": "mid"}.get(name, "lo")
    figs += [(f"re.second.cal.{k}.n", n, f"second score: readings with confidence {name}"), (f"re.second.cal.{k}.correct", c, "second score: of those, correct")]
figs.append(("re.second.wrong_conf_070_plus", int(((~df2.correct) & (df2.conf >= 0.70)).sum()), "second score: wrong readings with confidence 0.70 or more"))
figs.append(("re.first.suspect_label_errors", len(SUSPECT_LABEL), "first run: misses where the label, not the reader, was wrong (bill-28 amount; the user has since corrected it)"))
if changed:
    figs.append(("re.post.changed", 1, "the live reader output differs from the first-run snapshot"))
    for t in [*TYPES, "all"]:
        sub = df_post if t == "all" else df_post[df_post.bill_type == t]
        figs.append((f"re.post.{t}.fields_correct", int(sub.correct.sum()), f"post-fix (tuned on these 10 bills), {t}: field readings correct"))
        figs.append((f"re.post.{t}.key_bills_correct", T_post["full"][t][0], f"post-fix (tuned on these 10 bills), {t}: bills correct on all four key fields"))
        for lab in FIELDS:
            figs.append((f"re.post.{t}.{lab}.correct", int(sub[sub.field == lab].correct.sum()), f"post-fix (tuned on these 10 bills), {t}: {lab} correct"))
    for name, n, c in T_post["cal"]:
        k = {"0.90 or more": "hi", "0.70 to 0.90": "mid"}.get(name, "lo")
        figs += [(f"re.post.cal.{k}.n", n, f"post-fix: readings with confidence {name}"), (f"re.post.cal.{k}.correct", c, "post-fix: of those, correct")]
    figs.append(("re.post.wrong_conf_070_plus", int(((~df_post.correct) & (df_post.conf >= 0.70)).sum()), "post-fix: wrong readings with confidence 0.70 or more"))
    for tag in ("before", "after"):
        for k, d in (("low", "required fields (7 per bill) not found or below 0.70 confidence"), ("reader_ok", "bills the reader passes (status ok)"),
                     ("full_verdict", "bills on which all six checks could run"), ("some_verdict", "bills on which at least one check could run"),
                     ("complete_read", "bills with every required field read at 0.70 or more (the bills that got a verdict under the old all-or-nothing rule)")):
            figs.append((f"re.part1c.{tag}.{k}", EFF[tag][k], f"all 40 bills, {tag} the post-fix reader: {d}"))
pd.DataFrame(figs, columns=["id", "value", "description"]).to_csv(OUT / "figures_reader_eval.csv", index=False)

F = {k: v for k, v, _ in figs}
header = ["# Reader evaluation against the hand-labelled bills", "",
          "Generated by `analysis/15_reader_evaluation.py`; every count is registered in `notes/numbers.md` under `re.*`. The labels file `analysis/gold_labels.csv` was read, not edited. "
          "Only formatting is normalised (spaces, name case, amounts as numbers, dates as YYYY-MM-DD). The label `amount` is compared with the reader's grand total.", "",
          "**Two scores, one reader output.** The **FIRST-RUN score** was taken from a frozen copy of the reader's output (`analysis/reader_first_run.json`) made before the labels were used for anything, "
          "with the labels as first given; the reader was not changed to chase it. After it, the `bill-28.jpg` amount label (4,41,616.60) was found to have two digits swapped (the page prints 4,14,616.60, taxable 3,51,370.00 + IGST 63,246.60) "
          "and the user corrected it by hand. The **SECOND score** uses the corrected label on the same frozen reader output. It is not tuned: no reader change has touched a scored field "
          "(`analysis/15_reader_evaluation.py` checks the live reader against the snapshot; when a scored value or confidence differs, a separate post-fix section follows the first-run tables, labelled as tuned after seeing the first-run failures).", "",
          "| Score | Labels | Field readings correct | Bills fully correct on the four key fields |", "|---|---|---|---|",
          f"| FIRST-RUN | as first given | {F['re.first.all.fields_correct']} of {F['re.first.all.fields_total']} | {F['re.first.all.key_bills_correct']} of {F['re.first.all.bills']} |",
          f"| SECOND | bill-28 amount corrected | {F['re.second.all.fields_correct']} of {F['re.first.all.fields_total']} | {F['re.second.all.key_bills_correct']} of {F['re.first.all.bills']} |", "",
          f"By type (first run): fully correct bills pdf_single {F['re.first.pdf_single.key_bills_correct']} of {F['re.first.pdf_single.bills']}, pdf_packet {F['re.first.pdf_packet.key_bills_correct']} of {F['re.first.pdf_packet.bills']}, phone_photo {F['re.first.phone_photo.key_bills_correct']} of {F['re.first.phone_photo.bills']}. "
          f"The correction adds one correct amount reading (photos {F['re.second.phone_photo.amount.correct']} of 4) and changes no key-field bill count, because the GSTIN on `bill-28.jpg` is also wrong. "
          f"Calibration under the second score: confidence 0.90 or more {F['re.second.cal.hi.correct']} of {F['re.second.cal.hi.n']} right, 0.70 to 0.90 {F['re.second.cal.mid.correct']} of {F['re.second.cal.mid.n']}, below 0.70 or not read {F['re.second.cal.lo.correct']} of {F['re.second.cal.lo.n']} "
          "(the corrected amount was read at 0.50, so it moves from a wrong to a right reading in the lowest band). Ten bills are still far too few to call the confidence calibrated. "
          "The tables below are the first run; the second score differs from them only in that one amount.", ""]
body = L1
if changed:
    E = EFF
    body += ["", "---", "", "## Effect of the post-fix reader on all 40 bills", "",
             "The post-fix reader renders pages at the same 300 dpi (400 dpi was tried and made amounts worse, so it was reverted), reads the header again on its own, and, where the GSTIN is unclear, "
             "repairs one confusable character or looks the vendor up by name in the vendor master, marking the result `repaired` or `vendor_master`, never `read`. "
             "The GSTIN check digit was not used: none of the 900 GSTINs in the vendor master passes it, so it would reject every true GSTIN. Same checks, same register, before and after.", "",
             "| Measure, all 40 bills | Before | After |", "|---|---|---|",
             f"| Required fields (7 per bill) not found or below 0.70 confidence | {F['re.part1c.before.low']} | {F['re.part1c.after.low']} |",
             f"| Bills the reader passes with every field at 0.90 or more | {F['re.part1c.before.reader_ok']} | {F['re.part1c.after.reader_ok']} |",
             f"| Bills with every required field read at 0.70 or more (a verdict under the old all-or-nothing rule) | {F['re.part1c.before.complete_read']} | {F['re.part1c.after.complete_read']} |",
             f"| Bills on which all six checks could run | {F['re.part1c.before.full_verdict']} | {F['re.part1c.after.full_verdict']} |",
             f"| Bills on which at least one check could run (a verdict) | {F['re.part1c.before.some_verdict']} | {F['re.part1c.after.some_verdict']} |", "",
             "---", "", "## POST-FIX score: " + POST_TITLE, "",
             "**This is not a fair measure.** The fixes were chosen after the first-run failures on these 10 bills were seen, so these bills are no longer unseen. The first-run and second scores above are untouched. "
             "Do not quote this section as accuracy; it shows only whether the fixes did what they were aimed at.", ""]
    body += L_post[1:]
(ROOT / "notes" / "reader-evaluation.md").write_text("\n".join(header + body) + "\n", encoding="utf-8", newline="\n")
print("first run:", F["re.first.all.fields_correct"], "of", F["re.first.all.fields_total"], "| key bills", F["re.first.all.key_bills_correct"], "of 10 | second:", F["re.second.all.fields_correct"], "of 60 | key bills", F["re.second.all.key_bills_correct"], "| live differs:", changed)
