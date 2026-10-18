"""Compare the two readers on the 10 hand-labelled bills: Tesseract alone, the stored vision reading alone, and the combination (agreement trusted, disagreement goes to a person).

This is a SECOND evaluation script and, like analysis/15_reader_evaluation.py, it reads analysis/gold_labels.csv (read only). No app code reads that file.

Inputs (all stored, no network): the frozen first-run Tesseract output analysis/reader_first_run.json, the live Tesseract cache app/reader/cache, and the stored vision readings
data/cache/vision/*.json (made by `python -m app.reader.vision --all`, which needs a GEMINI_API_KEY). The labels are used as they are now (the bill-28 amount corrected).

If the vision readings of the 10 labelled bills are not all stored, nothing about the vision reader is scored and the note says so. Nothing is estimated or filled in.

FIRST RUN means the vision prompt was not changed after seeing this score: the stored readings carry their prompt version, and PROMPT_VERSION in app/reader/vision.py is the first one. A reading made
with a later prompt is reported on a separate 'tuned' line.

Writes analysis/out/figures_comparison.csv and notes/reader-comparison.md.   Run: python -I analysis/18_reader_comparison.py
"""
import csv
import json
import os
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.reader import crosscheck, vision   # noqa: E402

OUT = Path(os.environ["RIKLR_COMPARISON_OUT"]) if os.environ.get("RIKLR_COMPARISON_OUT") else ROOT / "analysis" / "out"   # the override is for the tests
NOTES = Path(os.environ["RIKLR_COMPARISON_OUT"]) if os.environ.get("RIKLR_COMPARISON_OUT") else ROOT / "notes"
LABELS = ROOT / "analysis" / "gold_labels.csv"
FIELDS = {"vendor_name": "vendor_name", "invoice_number": "invoice_no", "invoice_date": "invoice_date", "amount": "total", "gstin": "vendor_gstin", "po_or_wo_number": "wo_id"}
KEY = ["invoice_number", "invoice_date", "amount", "gstin"]
FIRST_PROMPT = "vision-prompt-1"
FREE_REQUESTS = 20   # requests per day per model on the free tier, as stated in Google's own 429 message (limit: 20), seen on 2026-10-18


def load_labels() -> list[dict]:
    out = []
    for r in csv.DictReader(open(LABELS, encoding="utf-8", newline="")):
        r = {k: (v or "").strip() for k, v in r.items()}
        m = re.fullmatch(r"(\d{2})-(\d{2})-(\d{4})", r["invoice_date"])
        if m:
            r["invoice_date"] = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
        r["amount"] = f"{float(r['amount'].replace(',', '')):.2f}"
        out.append(r)
    return out


def same(key: str, a, b) -> bool:
    return a is not None and b is not None and crosscheck.norm(key, a) == crosscheck.norm(key, b)


gold = load_labels()
tess_first = json.loads((ROOT / "analysis" / "reader_first_run.json").read_text(encoding="utf-8"))["results"]
tess_live = {g["file"]: json.loads((ROOT / "app" / "reader" / "cache" / f"{g['file']}.json").read_text(encoding="utf-8")) for g in gold}
vis = {g["file"]: vision.stored(g["file"]) for g in gold}
have = [f for f, v in vis.items() if v]
complete = len(have) == len(gold)
versions = sorted({(v.get("reader") or {}).get("prompt_version") for v in vis.values() if v})
tuned = complete and versions != [FIRST_PROMPT]


def score(readings: dict, label: str) -> pd.DataFrame:
    """Alone: a field is right when the reader's value equals the label (formatting aside), whatever its confidence. A missing reading is a miss."""
    rows = []
    for g in gold:
        r = readings.get(g["file"])
        for lab, k in FIELDS.items():
            x = ((r or {}).get("fields") or {}).get(k) or {}
            rows.append(dict(file=g["file"], bill_type=g["bill_type"], field=lab, key=k, label=g[lab], read=x.get("value"), conf=float(x.get("conf", 0) or 0), correct=same(k, x.get("value"), g[lab])))
    return pd.DataFrame(rows)


def key_bills(df: pd.DataFrame) -> int:
    return int(df[df.field.isin(KEY)].groupby("file").correct.all().sum())


def combine(tess: dict, vis_: dict) -> pd.DataFrame:
    """Per field: the cross-check state of the two readers, and whether each value and the agreed value is right."""
    rows = []
    for g in gold:
        cmp_ = crosscheck.compare(tess[g["file"]], vis_[g["file"]])
        for lab, k in FIELDS.items():
            c = cmp_.get(k)
            t = ((tess[g["file"]].get("fields") or {}).get(k) or {})
            state = c["state"] if c else "none"
            rows.append(dict(file=g["file"], field=lab, key=k, label=g[lab], state=state, tess=t.get("value"), tess_conf=float(t.get("conf", 0) or 0),
                             vis=(c or {}).get("vision"), tess_right=same(k, t.get("value"), g[lab]),
                             trusted_right=state == "agree" and same(k, c["tesseract"], g[lab])))
    return pd.DataFrame(rows)


T1 = score(tess_first, "first")
TL = score(tess_live, "live")
_reads = sorted(p for p in vision.VISION_DIR.glob("*/*.json"))
disclosure = [("rc.vision.successful_reads", len(_reads), "stored vision responses over all models: bill files sent to Google's Gemini API that came back with a reading"),
              ("rc.vision.distinct_files_read", len({p.name for p in _reads}), "of those, distinct bill files (the same file was read by two models)")]
figs = [*disclosure, ("rc.free_tier.requests_per_day_per_model", FREE_REQUESTS, "free-tier limit per model per day, as stated in Google's 429 message (not computed here)"),
        ("rc.labelled_bills", len(gold), "hand-labelled bills"),
        ("rc.vision_stored_of_labelled", len(have), "of those, bills with a stored vision reading"),
        ("rc.tess_first.fields_correct", int(T1.correct.sum()), "Tesseract alone, first run: fields right (of 60)"),
        ("rc.tess_first.key_bills", key_bills(T1), "Tesseract alone, first run: bills right on the four key fields"),
        ("rc.tess_live.fields_correct", int(TL.correct.sum()), "Tesseract alone, stored reading now (tuned on these bills): fields right (of 60)"),
        ("rc.tess_live.key_bills", key_bills(TL), "Tesseract alone, stored reading now (tuned on these bills): bills right on the four key fields")]

L = ["# Reader comparison: Tesseract, a vision model, and the two together", "",
     "Generated by `analysis/18_reader_comparison.py`; every count is registered in `notes/numbers.md` under `rc.*`. The labels file `analysis/gold_labels.csv` was read, not edited. "
     "Labels are as they are now (the bill-28 amount corrected). The same 10 hand-labelled bills as `notes/reader-evaluation.md`; ten bills is a small sample, so read every number here as a hint, not a result.", ""]

if not complete:
    L += ["## Status: the vision reader has NOT been scored", "",
          f"The stored vision readings of the labelled bills are not all present ({len(have)} of {len(gold)}), so the vision reader is not scored: a score on part of the set, or on readings from different models, would not be a first run. "
          + ("None has been made yet (the reader needs a Gemini API key), and no vision response has been invented." if not have else "Missing: " + ", ".join(f"`{f}`" for f in vis if not vis[f]) + ". Run `python -m app.reader.vision --all` again (it skips what is cached; the free tier of a model has a daily request limit) with the same model, then re-run this script.")
          + " Everything below that depends on it is blank on purpose.", "",
          "To fill the cache (sends each bill image to Google; the pack is synthetic), put the key in a `.env` file (copy `.env.example`), then run:", "",
          "```", "python -m app.reader.vision --all", "python -I analysis/18_reader_comparison.py", "```", "",
          "That writes `data/cache/vision/<file>.json` for the 40 inbox bills (commit them, and the app and the tests then run with no key), and re-writes this file with the scores. "
          "The first scores after that are the FIRST RUN, as long as the prompt (`PROMPT` in `app/reader/vision.py`) is not edited after seeing them; if it is, the new scores are reported on a separate 'tuned' line.", ""]
    L += ["## 1. Tesseract alone (known now)", "", "| | Fields right (of 60) | Bills right on the four key fields (of 10) |", "|---|---|---|",
          f"| Tesseract, first run (frozen, before any tuning) | {int(T1.correct.sum())} | {key_bills(T1)} |",
          f"| Tesseract, the stored readings now (tuned on these 10 bills) | {int(TL.correct.sum())} | {key_bills(TL)} |", "",
          "| | Vision alone | Combination |", "|---|---|---|", "| Fields right, bills right | not scored (no stored vision readings) | not scored |", ""]
else:
    V = score(vis, "vision")
    C = combine(tess_first, vis)
    CL = combine(tess_live, vis)
    pct = lambda a, b: f"{a} of {b}"
    n_tr, n_trw = int((C.state == "agree").sum()), int(((C.state == "agree") & ~C.trusted_right).sum())
    n_diff, n_vo, n_to, n_none = (int((C.state == s).sum()) for s in ("differ", "vision_only", "tesseract_only", "none"))
    wrong_read = C[C.tess.notna() & ~C.tess_right]                  # Tesseract gave a value and it was wrong
    caught = int((wrong_read.state == "differ").sum())
    flagged_low = int(((wrong_read.state != "differ") & (wrong_read.tess_conf < 0.70)).sum())
    trusted_wrong_t = int(((wrong_read.state == "agree")).sum())
    wrong_total = len(wrong_read)
    kb = C[C.field.isin(KEY)].groupby("file")
    key_trusted_right = int(kb.apply(lambda d: bool((d.state == "agree").all() and d.trusted_right.all())).sum())
    key_trusted_wrong = int(kb.apply(lambda d: bool(((d.state == "agree") & ~d.trusted_right).any())).sum())
    key_to_person = int(kb.apply(lambda d: bool((d.state != "agree").any())).sum())
    title = "TUNED (prompt changed after seeing the first score)" if tuned else "FIRST RUN (vision prompt not changed after seeing the score)"
    figs += [("rc.vision.fields_correct", int(V.correct.sum()), "vision alone: fields right (of 60)"), ("rc.vision.key_bills", key_bills(V), "vision alone: bills right on the four key fields"),
             ("rc.comb.trusted", n_tr, "combination: fields where the readers agree (trusted)"), ("rc.comb.trusted_wrong", n_trw, "combination: trusted fields that are wrong"),
             ("rc.comb.differ", n_diff, "combination: fields where the readers differ (go to a person)"), ("rc.comb.vision_only", n_vo, "combination: fields only the vision reader read (go to a person)"),
             ("rc.comb.tesseract_only", n_to, "combination: fields only Tesseract read (no second opinion)"), ("rc.comb.neither", n_none, "combination: fields neither reader read"),
             ("rc.comb.tess_wrong_readings", wrong_total, "Tesseract readings that were wrong (a value, not the right one)"), ("rc.comb.wrong_caught", caught, "of those, caught because the readers disagreed"),
             ("rc.comb.wrong_already_low", flagged_low, "of those, not caught by disagreement but already below 0.70 confidence"), ("rc.comb.wrong_trusted", trusted_wrong_t, "of those, trusted because the vision reader made the same error"),
             ("rc.comb.key_bills_trusted_right", key_trusted_right, "combination: bills with all four key fields agreed and right"), ("rc.comb.key_bills_trusted_wrong", key_trusted_wrong, "combination: bills with a key field agreed but wrong"),
             ("rc.comb.key_bills_to_person", key_to_person, "combination: bills with at least one key field that goes to a person")]
    if n_trw == 0 and n_tr:
        figs.append(("rc.comb.trusted_wrong_upper95_pct", round(100 * 3 / n_tr, 1), "rule of three: with no trusted-and-wrong field in the trusted fields, the 95% upper bound on the true rate of trusted-and-wrong fields, per cent"))
    secs = [float((v.get("reader") or {}).get("seconds")) for v in vis.values() if v and (v.get("reader") or {}).get("seconds") is not None]
    if secs:
        figs.append(("rc.vision.seconds_mean", round(sum(secs) / len(secs), 1), "vision: mean seconds per bill (one call, rate-limit pause excluded)"))
    L += [f"## {title}", "", f"Vision model: {', '.join(sorted({(v.get('reader') or {}).get('model', '?') for v in vis.values()}))}; prompt version(s): {', '.join(versions)}.", "",
          f"**Why this model.** Google's free tier allows {FREE_REQUESTS} requests a day for each model (its own 429 message says so: `limit: {FREE_REQUESTS}`). `gemini-3.8-flash` ran out of quota after {FREE_REQUESTS} bills, and `gemini-2.5-flash` is closed to new users, "
          f"so the 10 labelled bills were read with one model that had quota, `{', '.join(sorted({(v.get('reader') or {}).get('model', '?') for v in vis.values()}))}`, and nothing else is mixed in: each model's readings are stored in their own folder (`data/cache/vision/<model>/`), and only this model's folder is scored. "
          "Readings by `gemini-3.8-flash` for other bills exist in their own folder and are not used here.", "",
          "## 1. Fields and bills right", "", "| Reader | Fields right (of 60) | Bills right on the four key fields (of 10) |", "|---|---|---|",
          f"| (1) Tesseract alone, first run | {int(T1.correct.sum())} | {key_bills(T1)} |", f"| (2) Vision alone | {int(V.correct.sum())} | {key_bills(V)} |",
          f"| (3) Combination: agreement trusted, disagreement to a person | {n_tr - n_trw} trusted and right; {n_trw} trusted and wrong; {n_diff + n_vo + n_to + n_none} not trusted | {key_trusted_right} bills fully trusted and right; {key_to_person} with a field for a person |", "",
          f"For reference, the Tesseract stored readings as they are now (tuned on these 10 bills, so not a fair measure): {int(TL.correct.sum())} fields, {key_bills(TL)} bills.", "",
          "## 2. The combination, field by field", "", "| | Fields |", "|---|---|", f"| Readers agree (trusted) | {n_tr} |", f"|   of those, wrong | {n_trw} |", f"| Readers differ (a person decides) | {n_diff} |",
          f"| Only the vision reader read it (a person decides) | {n_vo} |", f"| Only Tesseract read it (no second opinion) | {n_to} |", f"| Neither read it | {n_none} |", "",
          f"Of the {wrong_total} Tesseract readings that were wrong, {caught} were caught because the readers disagreed, {flagged_low} more were not caught by disagreement but already carried a confidence below 0.70, "
          f"and {trusted_wrong_t} were trusted because both readers made the same error." + (f" Zero trusted-and-wrong fields among {n_tr} does not mean the true rate is zero: by the rule of three the 95% upper bound is about {100 * 3 / n_tr:.1f} per cent of trusted fields, and both readers saw the same image, so their mistakes are not independent." if n_trw == 0 and n_tr else ""), ""]
    dd = C[C.state == "differ"]
    if len(dd):
        L += ["## 3. Where the readers differed", "", "| Bill | Field | Label | Tesseract | Vision |", "|---|---|---|---|---|"]
        L += [f"| `{r.file}` | {r.field} | `{r.label}` | `{r.tess}` | `{r.vis}` |" for r in dd.itertuples()]
        L.append("")

L += ["## Cost, speed and privacy, per reader", "",
      "These are notes, not measurements, unless a figure is registered in `notes/numbers.md`. Provider terms, prices and free-tier limits change and were not checked from here: confirm them before relying on them.", "",
      "| | Tesseract (local) | Vision model (Gemini, hosted) |", "|---|---|---|",
      "| Cost | Free software; runs on the machine that holds the bills | Pay per call on a paid tier; a free tier exists with request limits that make 40 bills take a few minutes (the fill script pauses between calls). Not priced here |",
      "| Speed | A few seconds a page on a laptop (the intake card shows the time of a live read) | One network call per bill; " + (f"mean {[v for i, v, d in figs if i == 'rc.vision.seconds_mean'][0]} seconds on the 10 labelled bills" if any(i == 'rc.vision.seconds_mean' for i, v, d in figs) else "not measured (no key)") + " |",
      "| Privacy | The bill never leaves the machine | The bill image is sent to the provider. **A free tier may use inputs to improve the provider's products.** The case-pack bills are synthetic, so that is acceptable here; real vendor bills (GSTINs, bank and contract details) would need a paid, no-training tier, a data-processing agreement, or an in-house model |",
      "| Failure | Misreads blurry photos; says so with a low confidence on most, but not all | May read confidently and wrongly, and its own confidence is only its estimate. Also fails to respond (limits, outages): the app does not wait for it, it uses the stored reading |",
      "| In this build | Always on | Off by default; used only from the stored cache, no key and no network at run time |", "",
      "## How it is used here", "",
      "The vision model only extracts the same fields as JSON with a confidence for each; it never decides pass or fail. The cross-check is `app/reader/crosscheck.py`: where both readers agree the field is marked *two readers agree*; "
      "where they differ both values are shown side by side and the field is treated as not read until a person types it; neither reading is picked automatically. The app shows the stored vision reading and says so.", ""]
if not complete:
    L += ["## Tuned line", "", "None. The vision prompt has not been changed, and it has not been run.", ""]
elif not tuned:
    L += ["## Tuned line", "", "None. The prompt was not changed after seeing this score.", ""]

(NOTES / "reader-comparison.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
pd.DataFrame(figs, columns=["id", "value", "description"]).to_csv(OUT / "figures_comparison.csv", index=False, lineterminator="\n")
print(f"vision readings stored for {len(have)} of {len(gold)} labelled bills; wrote notes/reader-comparison.md")
