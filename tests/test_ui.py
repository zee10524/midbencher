"""Tests for app/ui: the three screens' data, the server, and the rule that no number on screen is typed by hand."""
import csv
import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from app.reader import pipeline
from app.ui import data
from app.ui.server import make_handler

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "app" / "ui" / "static"


@pytest.fixture(scope="module")
def server():
    S = data.State()
    S.load()
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(S))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}", S
    httpd.shutdown()


def get(url, **kw):
    with urllib.request.urlopen(url, **kw) as r:
        return json.loads(r.read())


def post(url, body=b"", headers=None):
    req = urllib.request.Request(url, data=body, method="POST", headers=headers or {})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


# ------------------------------------------------------------------ intake
def test_samples_are_the_forty_inbox_files(server):
    url, _ = server
    s = get(url + "/api/samples")
    assert len(s) == len(list(pipeline.INBOX.glob("bill-*"))) + len(list(pipeline.INBOX.glob("packet-*")))
    assert {x["bill_type"] for x in s} == {"pdf_single", "pdf_packet", "phone_photo"}


def test_a_card_has_a_verdict_at_most_three_issues_who_fixes_each_and_a_simulated_outbox(server):
    url, S = server
    t = time.time()
    code, c = post(url + "/api/intake?sample=packet-08-repeat-invoice.pdf")
    assert code == 200 and time.time() - t < 5
    assert c["route"] == "human-look" and c["headline"] and 1 <= len(c["issues"]) <= 3
    assert all(i["who"] and i["title"] and i["detail"] for i in c["issues"])
    assert c["outbox_note"] == "Simulated outbox. Nothing is sent." and c["messages"]
    assert {m["channel"].split(" ")[0] for m in c["messages"]} <= {"WhatsApp", "In-app"}
    checks = [i["check"] for i in c["issues"]]
    assert "H3" in checks                       # the work order is over its approved value: the issue that matters most after the unreadable invoice number


def test_the_simulated_reading_label_takes_its_numbers_from_the_figure_register(server):
    url, S = server
    _, c = post(url + "/api/intake?sample=bill-13.pdf")
    N = data.Numbers()
    want = (f"Simulated reading: stored extraction from the reader. On the {N('re.first.all.bills'):.0f} hand-labelled bills it read {N('re.second.all.key_bills_correct'):.0f} fully right on the four key fields "
            f"(first run, before any tuning; the stored readings come from a later version tuned on those bills; weaker on phone photos, {N('re.first.phone_photo.key_bills_correct'):.0f} of {N('re.first.phone_photo.bills'):.0f}). "
            f"A person fills in any field it could not read. Its confident readings (0.90 and above) were {N('re.second.cal.hi.correct'):.0f} of {N('re.second.cal.hi.n'):.0f} right on those bills; "
            f"{N('re.first.all.bills'):.0f} bills is a small sample, so read that as a hint, not a guarantee.")
    assert c["reading_label"] == want
    assert "A person fills in any field it could not read" in c["reading_label"] and "small sample" in c["reading_label"] and "44 of 44" in c["reading_label"]


def test_low_confidence_fields_are_marked_and_never_shown_as_known(server):
    url, S = server
    _, c = post(url + "/api/intake?sample=bill-16.jpg")                   # a phone photo whose invoice number and date the reader did not read
    unread = [f for f in c["fields"] if f["state"] == "unread"]
    assert unread and all(f["value"] == "not read" for f in unread)
    assert c["review_note"].startswith("Fields marked needs human review are never guessed.")
    assert c["route"] == "human-look" and c["partial"] and c["issues"][-1]["check"] == "read" and "taxable" in c["inputs"]


def test_a_clean_bill_can_clear_and_needs_no_message_to_the_vendor(server):
    url, _ = server
    _, c = post(url + "/api/intake?sample=bill-17.pdf")
    assert c["route"] == "auto-clear" and not c["issues"]
    assert all("vendor" not in m["channel"].lower() for m in c["messages"])


def test_a_dropped_file_is_matched_by_its_content_and_an_unknown_file_has_no_stored_reading(server):
    url, S = server
    body = (pipeline.INBOX / "bill-13.pdf").read_bytes()
    code, c = post(url + "/api/intake", body, {"X-Filename": "renamed.pdf"})
    assert code == 200 and c["file"] == "bill-13.pdf"
    code, c = post(url + "/api/intake", b"not a bill", {"X-Filename": "mystery.pdf"})
    assert code == 200 and c["no_stored"] is True and "no stored reading" in c["message"].lower()


def test_live_reader_is_refused_without_tesseract_and_works_with_it(server, monkeypatch):
    url, S = server
    meta = get(url + "/api/meta")
    assert meta["tesseract"] == data.tesseract_found()
    monkeypatch.setattr(data, "tesseract_found", lambda: False)
    code, j = post(url + "/api/intake/live?sample=bill-13.pdf")
    assert code == 400 and "Tesseract is not installed" in j["error"]
    monkeypatch.undo()
    if data.tesseract_found():
        code, j = post(url + "/api/intake/live?sample=bill-13.pdf")
        assert code == 200 and j["source"] == "live" and j["reading_label"].startswith("Live reading")


# ------------------------------------------------------------------ control tower
def test_control_tower_has_the_four_parts(server):
    url, S = server
    d = get(url + "/api/control")
    assert len(d["oldest"]) == 20 and len(d["clerks"]) == 5 and d["msme"] and d["dry"]
    assert d["oldest"][0]["days"] >= d["oldest"][-1]["days"]
    assert all(c["after"] == c["in_hand"] + c["new"] for c in d["clerks"])
    assert all(r["days_left"] >= 0 for r in d["msme"])
    assert d["spread_pct"] <= 20 and d["live_waiting"] == int(S.numbers("l.live.waiting"))
    burns = [float(x["burn"].replace("Rs ", "").replace(",", "")) for x in d["dry"]]
    assert burns == sorted(burns, reverse=True)                              # the biggest billing first


def test_red_is_only_for_bills_that_miss_a_deadline(server):
    url, S = server
    from app.tracker import countdown
    d = get(url + "/api/control")
    missing = {r["bill_id"] for r in countdown(S.bills, 1) if r["state"] in ("late", "will be late: no run left")}
    assert all(b["bill_id"] in missing for b in d["oldest"] if b["miss"])
    assert all(r["runs_left"] == 0 for r in d["msme"] if r["miss"]) and all(r["miss"] for r in d["msme"] if r["runs_left"] == 0)
    css = (STATIC / "style.css").read_text(encoding="utf-8")
    uses = re.findall(r"([^{}]+)\{[^}]*var\(--red\)", css)
    assert all("miss" in u for u in uses)                                  # the red variable is used only on `.miss` rules


def test_cutoff_setting_changes_the_runs_left(server):
    url, _ = server
    a, b = get(url + "/api/control?cutoff=0"), get(url + "/api/control?cutoff=2")
    assert a["cutoff"] == 0 and b["cutoff"] == 2
    assert sum(r["runs_left"] for r in a["msme"]) >= sum(r["runs_left"] for r in b["msme"])


# ------------------------------------------------------------------ impact
def test_impact_ranges_come_from_the_backtest_files(server):
    url, S = server
    d = get(url + "/api/impact")
    rows = {(r["group"], r["metric"]): r for r in csv.DictReader(open(ROOT / "backtest" / "out" / "impact.csv", encoding="utf-8"))}
    ms = next(h for h in d["headline"] if h["name"].startswith("Micro and Small"))
    lo, hi = rows[("combined", "msme_over_45_days_count")]["high"], rows[("combined", "msme_over_45_days_count")]["low"]
    assert ms["after"] == f"{int(float(lo)):,} to {int(float(hi)):,}" and ms["before"] == f"{S.numbers('l.base.ms_late'):,.0f}"
    mean = d["headline"][0]
    assert mean["after"] == f"{S.numbers('l.base.desk_mean') - S.numbers('l.lever.high.save'):.1f} to {S.numbers('l.base.desk_mean') - S.numbers('l.lever.low.save'):.1f}"
    assert all(h["condition"] for h in d["headline"]) and len(d["levers"]) == 3 and all(l["condition"] for l in d["levers"])
    assert "unconfirmed" in d["headline"][0]["condition"] and "Treasury" in d["headline"][0]["condition"]
    assert "barely move the mean" in d["intake_line"] and "protect the tail" in d["intake_line"]
    assert "counterfactual" in d["label"]


# ------------------------------------------------------------------ no number is typed by hand
def _visible_html_text(html: str) -> str:
    html = re.sub(r"<(script|style)\b.*?</\1>", "", html, flags=re.S)
    return re.sub(r"<[^>]+>", " ", html)


def test_the_page_and_script_contain_no_numbers_of_their_own():
    html = _visible_html_text((STATIC / "index.html").read_text(encoding="utf-8"))
    assert not re.search(r"\d", html), "a number is typed into the page"
    js = (STATIC / "app.js").read_text(encoding="utf-8")
    literals = re.findall(r"\"((?:[^\"\\\n]|\\.)*)\"", js)
    typed = [s for s in literals if re.search(r"\d", s) and not re.fullmatch(r"h[1-6]", s)]   # `h2` is an HTML tag name, not a number
    assert not typed, f"numbers typed into the script: {typed}"


# ------------------------------------------------------------------ make run
def test_the_app_starts_with_python_m_app_and_serves_the_page():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    env = dict(os.environ, RIKLR_PORT=str(port), PYTHONIOENCODING="utf-8")
    p = subprocess.Popen([sys.executable, "-m", "app"], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        for _ in range(60):
            try:
                html = urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1).read().decode()
                break
            except Exception:  # noqa: BLE001 - not up yet
                time.sleep(0.5)
        else:
            pytest.fail("the app did not start")
        assert "Intake" in html and "Control tower" in html and "Impact" in html
        assert len(get(f"http://127.0.0.1:{port}/api/samples")) == 40
    finally:
        p.terminate()
        p.wait(timeout=10)


def test_work_orders_running_dry_are_estimated_from_the_last_90_days_of_billing(server):
    url, S = server
    d = get(url + "/api/control")
    N = S.numbers
    assert d["headline"]["dry"] == int(N("rw.dry")) and d["headline"]["dry_vendor_waiting"] == int(N("rw.dry.vendor_waiting"))
    assert d["labels"]["dry"] == f"work orders likely to run dry within {N('rw.horizon_days'):.0f} days, estimated from the last {N('rw.window_days'):.0f} days of billing"
    assert d["labels"]["dry_extra"].startswith(f"{N('rw.dry.vendor_waiting'):,.0f} of them have a vendor with a bill already waiting. It is an estimate")
    assert f"{N('rw.sens.window_60d.dry'):,.0f} orders with the last {N('rw.sens.window_lo_days'):.0f} days" in d["labels"]["dry_extra"] and f"{N('rw.sens.window_120d.dry'):,.0f} with the last {N('rw.sens.window_hi_days'):.0f} days" in d["labels"]["dry_extra"]
    rows = list(csv.DictReader(open(ROOT / "backtest" / "out" / "runway_90d.csv", encoding="utf-8")))
    assert len(rows) == int(N("rw.dry")) and [r["wo_id"] for r in rows[:6]] == [x["wo_id"] for x in d["dry"]]
    monthly = [int(r["monthly_billing_inr"]) for r in rows]
    assert monthly == sorted(monthly, reverse=True)                                       # ranked by monthly billing
    assert all(float(r["runway_days"]) <= N("rw.horizon_days") and int(r["balance_inr"]) > 0 for r in rows)
    assert sum(r["vendor_has_bill_waiting"] == "True" for r in rows) == int(N("rw.dry.vendor_waiting"))


def test_the_cutoff_control_wraps_instead_of_clipping_in_a_narrow_window():
    css = (STATIC / "style.css").read_text(encoding="utf-8")
    head = re.search(r"\.head-row\s*\{([^}]*)\}", css).group(1)
    assert "flex-wrap: wrap" in head
    assert "flex: 0 0 auto" in re.search(r"\.seg\s*\{([^}]*)\}", css).group(1)


def test_impact_msme_line_is_plain_and_from_the_files(server):
    url, S = server
    d = get(url + "/api/impact")
    ms = next(h for h in d["headline"] if h["name"].startswith("Micro and Small"))
    assert ms["sentence"] == "from 10.4 per cent of Micro and Small bills (530 of 5,106) to 3.9 to 5.9 per cent (200 to 303)"
    assert ms["sentence"].startswith(f"from {S.numbers('l.base.ms_late_pct'):.1f} per cent")
    text = d["low_middle_high"] + " ".join(l["condition"] for l in d["levers"])
    assert "best case" in text and "worst case" in text and "residual" not in text and "optimistic" not in text and "cut-off 2 /" not in text


# ------------------------------------------------------------------ review findings: only this machine's own page, and a traceable review
def test_requests_for_another_host_or_from_another_page_are_refused(server):
    url, _ = server
    for hdrs in ({"Host": "evil.example"}, {"Origin": "http://evil.example"}):
        req = urllib.request.Request(url + "/api/meta", headers=hdrs)
        try:
            urllib.request.urlopen(req)
            raise AssertionError("request was not refused")
        except urllib.error.HTTPError as e:
            assert e.code == 403
        code, body = post(url + "/api/intake/review", b"{}", hdrs)
        assert code == 403 and "refused" in body["error"]
    assert get(url + "/api/meta")["tesseract"] in (True, False)


def test_a_review_needs_a_name_and_is_written_to_a_chained_audit_log(server, tmp_path, monkeypatch):
    from app.ui import audit
    url, S = server
    monkeypatch.setattr(audit, "LOG", tmp_path / "log.jsonl")
    key = next(k for k, r in S.cache.items() if r["file"] == "packet-10-credit-note.pdf")
    code, body = post(url + "/api/intake/review", json.dumps({"key": key, "values": {"hsn_sac": "3304"}}).encode())
    assert code == 400 and "your name" in body["error"] and not (tmp_path / "log.jsonl").exists()
    code, body = post(url + "/api/intake/review", json.dumps({"key": key, "values": {"hsn_sac": "3304"}, "reviewer": "Asha Rao"}).encode())
    assert code == 200
    code, body = post(url + "/api/intake/review", json.dumps({"key": key, "values": {"hsn_sac": "3305"}, "reviewer": "Asha Rao"}).encode())
    lines = [json.loads(x) for x in (tmp_path / "log.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(lines) == 2 and lines[0]["reviewer"] == "Asha Rao" and lines[0]["typed"]["hsn_sac"]["typed"] == "3304" and "reader_original" in lines[0]["typed"]["hsn_sac"]
    assert audit.verify(tmp_path / "log.jsonl")[0] is True
    text = (tmp_path / "log.jsonl").read_text(encoding="utf-8").splitlines()
    (tmp_path / "log.jsonl").write_text(text[1] + "\n", encoding="utf-8")          # the first line removed
    ok, n, msg = audit.verify(tmp_path / "log.jsonl")
    assert ok is False and "edited or a line was removed" in msg
