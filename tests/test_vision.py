"""Tests for the second reader and the cross-check. No key and no network are used: the vision reading is a synthetic fixture, and the call is faked.
The hand-labelled file is never opened here or anywhere in app code."""
import copy
import json
import shutil
import urllib.error
from pathlib import Path

import pytest

from app import intake
from app.reader import crosscheck, pipeline, vision
from app.rules import Context
from app.sap.adapter import SapAdapter
from app.tracker import seed
from app.ui import data

ROOT = Path(__file__).resolve().parent.parent
PACK = ROOT / "pack" / "data"
KEY = "TEST-KEY-do-not-leak-1234"


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    d = tmp_path_factory.mktemp("vis")
    shutil.copyfile(PACK / "sap_extract.sqlite", d / "c.sqlite")
    sap = SapAdapter(d / "c.sqlite")
    S = data.State()
    S.bills = seed(PACK / "bill_register.csv", PACK / "queries.csv", sap)
    yield sap, S
    sap.close()


def cached(name):
    return json.loads((pipeline.CACHE_DIR / f"{name}.json").read_text(encoding="utf-8"))


def vis_of(res, **over):
    """A synthetic vision reading that equals the Tesseract one on every field, with `over` {field: value or None} changed."""
    f = {}
    for k in vision.FIELDS:
        x = (res["fields"].get(k) or {})
        f[k] = dict(value=x.get("value"), conf=0.9 if x.get("value") is not None else 0.0)
    for k, v in over.items():
        f[k] = dict(value=v, conf=0.9 if v is not None else 0.0)
    return dict(file=res["file"], sha256=res["sha256"], reader=dict(name="vision", provider="Gemini", model=vision.MODEL, prompt_version="t", read_at="2026-10-17"), doc_type="invoice", fields=f)


# ------------------------------------------------------------------ the key and the cache
def test_the_example_env_is_blank_and_the_real_env_is_ignored():
    assert (ROOT / ".env.example").read_text(encoding="utf-8").count("GEMINI_API_KEY=\n") == 1
    ign = (ROOT / ".gitignore").read_text(encoding="utf-8").split()
    assert ".env" in ign and "!.env.example" in ign


def test_no_key_means_no_call(monkeypatch, tmp_path):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(vision, "_env_file_value", lambda name: None)
    monkeypatch.setattr(vision.urllib.request, "urlopen", lambda *a, **k: pytest.fail("a network call was made"))
    f = tmp_path / "bill.pdf"
    f.write_bytes(b"%PDF-1.4 test")
    with pytest.raises(RuntimeError, match="No GEMINI_API_KEY"):
        vision.read_file(f, folder=tmp_path / "cache")
    assert not vision.has_key()


def test_the_key_goes_in_a_header_and_never_into_the_cache_or_an_error(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("GEMINI_API_KEY", KEY)
    seen = {}

    class R:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return json.dumps({"candidates": [{"content": {"parts": [{"text": json.dumps({"doc_type": "credit_note", "fields": {"invoice_no": {"value": " CN-1 ", "confidence": 1.4}, "total": {"value": None, "confidence": 0.9}}})}]}}]}).encode()

    def fake(req, timeout=0):
        seen["url"], seen["headers"] = req.full_url, dict(req.header_items())
        return R()

    monkeypatch.setattr(vision.urllib.request, "urlopen", fake)
    f = tmp_path / "bill.pdf"
    f.write_bytes(b"%PDF-1.4 test")
    rec = vision.read_file(f, folder=tmp_path / "cache")
    assert KEY not in seen["url"] and seen["headers"]["X-goog-api-key"] == KEY
    assert KEY not in (tmp_path / "cache" / "bill.pdf.json").read_text(encoding="utf-8")
    assert rec["doc_type"] == "credit_note" and rec["fields"]["invoice_no"] == dict(value="CN-1", conf=1.0) and rec["fields"]["total"] == dict(value=None, conf=0.0)
    assert set(rec["fields"]) == set(vision.FIELDS)
    assert vision.read_file(f, folder=tmp_path / "cache") == rec            # the second time comes from the cache: urlopen is not needed
    monkeypatch.setattr(vision.urllib.request, "urlopen", lambda *a, **k: pytest.fail("cache not used"))
    assert vision.read_file(f, folder=tmp_path / "cache")["fields"]["invoice_no"]["value"] == "CN-1"

    def boom(req, timeout=0):
        raise urllib.error.HTTPError(req.full_url, 429, "x", {}, None)

    monkeypatch.setattr(vision.urllib.request, "urlopen", boom)
    with pytest.raises(RuntimeError) as e:
        vision.read_file(f, force=True, folder=tmp_path / "cache")
    assert KEY not in str(e.value) and "429" in str(e.value)
    assert KEY not in capsys.readouterr().out


def test_a_stored_reading_made_from_other_bytes_is_not_used(tmp_path):
    (tmp_path / "x.pdf.json").write_text(json.dumps(dict(file="x.pdf", sha256="aaa", fields={})), encoding="utf-8")
    assert vision.stored("x.pdf", "aaa", tmp_path) is not None and vision.stored("x.pdf", "bbb", tmp_path) is None and vision.stored("nothing.pdf", None, tmp_path) is None


# ------------------------------------------------------------------ the cross-check
def test_agree_differ_and_one_reader_only():
    res = cached("bill-11.pdf")
    vis = vis_of(res, total=float(res["fields"]["total"]["value"]) + 1, hsn_sac=None)
    vis["fields"]["invoice_no"]["value"] = " " + res["fields"]["invoice_no"]["value"].lower() + " "     # formatting only
    got = crosscheck.compare(res, vis)
    assert got["vendor_gstin"]["state"] == "agree" and got["invoice_no"]["state"] == "agree"
    assert got["total"]["state"] == "differ" and got["total"]["tesseract"] != got["total"]["vision"]
    unread = copy.deepcopy(res)
    unread["fields"]["invoice_date"] = dict(value=None, conf=0.0, note="", source="read", raw=None)
    got2 = crosscheck.compare(unread, vis_of(res))
    assert got2["invoice_date"]["state"] == "vision_only" and got2["invoice_date"]["tesseract"] is None
    low = copy.deepcopy(res)
    low["fields"]["vendor_name"]["conf"] = 0.5
    assert crosscheck.compare(low, vis_of(res))["vendor_name"]["state"] == "vision_only"        # below 0.70 is no reading
    assert crosscheck.compare(res, None) == {}


def test_a_disagreement_is_never_resolved_and_a_typed_field_is_left_alone():
    res = cached("bill-11.pdf")
    other = "99" + res["fields"]["vendor_gstin"]["value"][2:]
    applied = crosscheck.apply(res, vis_of(res, vendor_gstin=other))
    x = applied["fields"]["vendor_gstin"]
    assert x["value"] is None and x["conf"] == 0.0 and x["cross"]["state"] == "differ"
    assert x["tesseract"]["value"] == res["fields"]["vendor_gstin"]["value"] and x["cross"]["vision"] == other     # both kept, neither used
    assert crosscheck.apply(applied, vis_of(res)) == applied                                                      # applying twice changes nothing
    assert res["fields"]["vendor_gstin"]["value"] is not None                                                     # the input is not changed
    typed = copy.deepcopy(res)
    typed["fields"]["vendor_gstin"] = dict(value=other, conf=1.0, note="typed", source="human_review", raw=None)
    assert "cross" not in crosscheck.apply(typed, vis_of(res))["fields"]["vendor_gstin"]


def test_a_disputed_field_is_treated_as_not_read_by_the_checks(world):
    sap, S = world
    res = cached("bill-11.pdf")
    ctx = Context(sap, S.bills, bill_counted_in_billed=True)
    base = intake.check_bill(res, ctx)
    applied = crosscheck.apply(res, vis_of(res, vendor_gstin="99" + res["fields"]["vendor_gstin"]["value"][2:]))
    out = intake.check_bill(applied, ctx)
    assert len(out["disputed"]) == 1
    assert out["unread"] == [] and out["partial"] and len(out["not_run"]) > len(base["not_run"])
    assert not any("clearer" in a.text for a in out["routing"].actions if hasattr(a, "text"))        # a disagreement is not a request for a clearer image
    assert out["routing"].route != "auto-clear"


# ------------------------------------------------------------------ the card
def test_card_marks_agreement_and_shows_both_values_on_a_difference(world, monkeypatch, tmp_path):
    sap, S = world
    res = cached("bill-11.pdf")
    monkeypatch.setattr(vision, "VISION_DIR", tmp_path)          # an empty cache folder: the real one may hold readings by now
    plain = data.card(S, res, "stored", replay=True)
    assert plain["vision_label"] == "Not read by the vision model yet." and not any("cross" in r for r in plain["fields"])           # no stored vision reading: nothing changes
    total = float(res["fields"]["total"]["value"])
    (tmp_path / vision.MODEL).mkdir()
    (tmp_path / vision.MODEL / "bill-11.pdf.json").write_text(json.dumps(vis_of(res, total=total + 5)), encoding="utf-8")
    monkeypatch.setattr(vision, "VISION_DIR", tmp_path)
    c = data.card(S, res, "stored", replay=True)
    rows = {r["key"]: r for r in c["fields"]}
    assert "Stored vision reading" in c["vision_label"] and vision.MODEL in c["vision_label"] and "Neither is picked automatically" in c["vision_label"]
    assert rows["vendor_gstin"]["cross"]["state"] == "agree" and rows["vendor_gstin"]["state"] == "ok"
    t = rows["total"]
    assert t["state"] == "differ" and t["cross"]["tesseract"] == f"{total:,.2f}" and t["cross"]["vision"] == f"{total + 5:,.2f}" and "total" in c["inputs"]
    assert c["partial"] and c["route"] != "auto-clear"


def test_typing_a_value_on_a_difference_saves_it_as_human_review(world, monkeypatch, tmp_path):
    sap, S = world
    res = cached("bill-11.pdf")
    S.cache[res["sha256"]] = res
    total = float(res["fields"]["total"]["value"])
    (tmp_path / vision.MODEL).mkdir()
    (tmp_path / vision.MODEL / "bill-11.pdf.json").write_text(json.dumps(vis_of(res, total=total + 5)), encoding="utf-8")
    monkeypatch.setattr(vision, "VISION_DIR", tmp_path)
    monkeypatch.setattr(pipeline, "WORKING_DB", tmp_path / "w.sqlite")
    pipeline.make_working_copy(PACK / "sap_extract.sqlite", tmp_path / "w.sqlite")
    c = data.apply_review(S, res["sha256"], {"total": f"{total:.2f}"}, "A. Reviewer")
    assert c["saved"]["source"] == "human_review" and c["saved"]["typed"] == ["total"]
    assert {r["key"]: r for r in c["fields"]}["total"]["state"] == "typed"


# ------------------------------------------------------------------ the comparison script, on a synthetic cache (the real one needs a key)
def test_comparison_script_scores_a_synthetic_cache_and_says_nothing_without_one(tmp_path):
    import csv
    import subprocess
    import sys

    first = json.loads((ROOT / "analysis" / "reader_first_run.json").read_text(encoding="utf-8"))["results"]       # the names of the 10 labelled bills, not the labels
    env = {**__import__("os").environ, "RIKLR_COMPARISON_OUT": str(tmp_path / "out")}
    (tmp_path / "out").mkdir()
    run = lambda: subprocess.run([sys.executable, "-I", str(ROOT / "analysis" / "18_reader_comparison.py")], env=env, cwd=ROOT, capture_output=True, text=True, check=True)
    empty = tmp_path / "empty"
    empty.mkdir()
    env["RIKLR_VISION_DIR"] = str(empty)
    run()
    assert "NOT been scored" in (tmp_path / "out" / "reader-comparison.md").read_text(encoding="utf-8")
    full = tmp_path / "full" / vision.MODEL
    full.mkdir(parents=True)
    for name, r in first.items():
        live = cached(name)
        v = vis_of(live)
        v["reader"]["prompt_version"] = vision.PROMPT_VERSION
        if name == sorted(first)[0]:
            v["fields"]["vendor_gstin"]["value"] = "06ZZZZZ9999Z1Z9"            # one disagreement
        (full / f"{name}.json").write_text(json.dumps(v), encoding="utf-8")
    env["RIKLR_VISION_DIR"] = str(full.parent)
    run()
    md = (tmp_path / "out" / "reader-comparison.md").read_text(encoding="utf-8")
    figs = {r["id"]: float(r["value"]) for r in csv.DictReader(open(tmp_path / "out" / "figures_comparison.csv", encoding="utf-8"))}
    assert "FIRST RUN" in md and "TUNED" not in md and "Tesseract alone, first run" in md
    assert figs["rc.vision_stored_of_labelled"] == 10 and figs["rc.comb.differ"] >= 1
    assert figs["rc.comb.trusted"] + figs["rc.comb.differ"] + figs["rc.comb.vision_only"] + figs["rc.comb.tesseract_only"] + figs["rc.comb.neither"] == 60
    assert figs["rc.comb.wrong_caught"] + figs["rc.comb.wrong_already_low"] + figs["rc.comb.wrong_trusted"] <= figs["rc.comb.tess_wrong_readings"]
    # a later prompt version is reported as tuned
    for p in full.glob("*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        d["reader"]["prompt_version"] = "vision-prompt-2"
        p.write_text(json.dumps(d), encoding="utf-8")
    run()
    assert "TUNED" in (tmp_path / "out" / "reader-comparison.md").read_text(encoding="utf-8")


# ------------------------------------------------------------------ one folder per model, retries, and --files
def test_readings_of_different_models_are_never_mixed(tmp_path, monkeypatch):
    monkeypatch.setattr(vision, "VISION_DIR", tmp_path)
    (tmp_path / "other-model").mkdir()
    (tmp_path / "other-model" / "x.pdf.json").write_text(json.dumps(dict(file="x.pdf", sha256="a", reader=dict(model="other-model"), fields={})), encoding="utf-8")
    assert vision.stored("x.pdf", "a") is None and vision.stored("x.pdf", "a", model="other-model") is not None
    (tmp_path / vision.MODEL).mkdir()
    (tmp_path / vision.MODEL / "x.pdf.json").write_text(json.dumps(dict(file="x.pdf", sha256="a", reader=dict(model="other-model"), fields={})), encoding="utf-8")
    assert vision.stored("x.pdf", "a") is None          # a file in this model's folder that says it came from another model is not used


def _http_error(code):
    return urllib.error.HTTPError("https://x/v1beta/models/m:generateContent", code, "x", {}, __import__("io").BytesIO(json.dumps({"error": {"message": f"Google text {code} " + KEY}}).encode()))


def test_503_is_retried_three_times_and_429_stops_without_a_retry(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("GEMINI_API_KEY", KEY)
    monkeypatch.setenv("GEMINI_RETRY_SECONDS", "0")
    calls = []

    def always(code):
        def f(req, timeout=0):
            calls.append(code)
            raise _http_error(code)
        return f

    f = tmp_path / "bill.pdf"
    f.write_bytes(b"%PDF-1.4 test")
    monkeypatch.setattr(vision.urllib.request, "urlopen", always(503))
    with pytest.raises(RuntimeError) as e:
        vision.read_file(f, folder=tmp_path / "c")
    assert calls == [503, 503, 503] and "HTTP 503" in str(e.value) and vision.MODEL in str(e.value) and "Google text 503" in str(e.value) and KEY not in str(e.value)
    calls.clear()
    monkeypatch.setattr(vision.urllib.request, "urlopen", always(429))
    with pytest.raises(vision.QuotaExceeded) as e:
        vision.read_file(f, folder=tmp_path / "c")
    assert calls == [429] and KEY not in str(e.value)


def test_files_option_reads_only_those_files_and_stops_at_a_quota(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("GEMINI_API_KEY", KEY)
    monkeypatch.setattr(vision, "VISION_DIR", tmp_path)
    monkeypatch.setattr(vision.time, "sleep", lambda s: None)
    seen = []

    def fake_read(p, force=False, folder=None):
        seen.append(p.name)
        if len(seen) == 2:
            raise vision.QuotaExceeded("429 text")
        return {}

    monkeypatch.setattr(vision, "read_file", fake_read)
    rc = vision.main(["--files", "bill-11.pdf", "bill-12.pdf", "bill-14.pdf", "--confirm-send"])
    out = capsys.readouterr().out
    assert rc == 1 and seen == ["bill-11.pdf", "bill-12.pdf"] and "Stopped" in out and KEY not in out
    assert vision.main(["--files", "index.md-not-there.pdf"]) == 2
    seen.clear()
    monkeypatch.setattr(vision, "read_file", lambda p, force=False, folder=None: seen.append(p.name) or {})
    vision.main(["--all", "--confirm-send"])
    assert len(seen) == 40 and not any(n.endswith(".md") for n in seen)


# ------------------------------------------------------------------ review findings: consent, raw answer, vendor-master values
def test_nothing_is_sent_without_the_confirm_flag(monkeypatch, capsys):
    monkeypatch.setenv("GEMINI_API_KEY", KEY)
    monkeypatch.setattr(vision, "read_file", lambda *a, **k: pytest.fail("a bill was sent without --confirm-send"))
    assert vision.main(["--all"]) == 3
    out = capsys.readouterr().out
    assert "third party" in out and "--confirm-send" in out and KEY not in out


def test_the_models_own_answer_is_kept_in_the_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_API_KEY", KEY)
    text = json.dumps({"doc_type": "invoice", "fields": {"total": {"value": 5, "confidence": 0.9}}})

    class R:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return json.dumps({"candidates": [{"content": {"parts": [{"text": text}]}}]}).encode()

    monkeypatch.setattr(vision.urllib.request, "urlopen", lambda req, timeout=0: R())
    f = tmp_path / "b.pdf"
    f.write_bytes(b"%PDF")
    rec = vision.read_file(f, folder=tmp_path / "c")
    assert rec["model_answer"] == text and rec["fields"]["total"]["value"] == 5


def test_a_value_taken_from_the_vendor_master_is_not_two_readers_agreeing():
    res = cached("bill-11.pdf")
    looked_up = copy.deepcopy(res)
    looked_up["fields"]["vendor_gstin"]["source"] = "vendor_master"
    got = crosscheck.compare(looked_up, vis_of(res))
    assert got["vendor_gstin"]["state"] == "vision_confirms" and got["invoice_no"]["state"] == "agree"
