"""Tests for the simulated two-way WhatsApp thread: Hindi coverage, the reply to a vendor's photo and the tracker's status sentence. Nothing is sent anywhere."""
import json
import re
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from app.tracker import status as tstatus
from app.tracker import vendor_sentence
from app.ui import chat, data
from app.ui.server import make_handler

ROOT = Path(__file__).resolve().parent.parent
DEVANAGARI = re.compile(r"[ऀ-ॿ]")


@pytest.fixture(scope="module")
def server():
    S = data.State()
    S.load()
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(S))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}", S
    httpd.shutdown()


def post(url, body=b"", headers=None):
    req = urllib.request.Request(url, data=body, method="POST", headers=headers or {})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_every_query_reason_has_a_hindi_version():
    reasons = {r for _, _, r, _ in tstatus.RULES} | {"we are checking a detail on the bill"}
    assert reasons <= set(chat.QUERY_HI)
    assert all(DEVANAGARI.search(h) and DEVANAGARI.search(a) for h, a in chat.QUERY_HI.values())
    assert set(chat.OWNER_HI) == set(tstatus.OWNER_WORDS)


def test_hindi_status_covers_every_stage_and_never_prints_a_blank(server):
    _, S = server
    seen = set()
    for b in S.bills:
        s = chat.hindi_status(b)
        assert DEVANAGARI.search(s) and "None" not in s and b.invoice_no in s
        seen.add("query" if b.open_query else b.stage)
    assert {"paid", "query"} <= seen and len(seen) >= 4


def test_the_hindi_date_names_a_day_and_a_month():
    from datetime import date
    assert chat.hi_date(date(2026, 5, 5)) == "मंगलवार 5 मई 2026"


def test_the_first_message_has_a_hindi_version_and_the_checks_have_a_hindi_line(server):
    _, S = server
    res = json.loads((data.pipeline.CACHE_DIR / "bill-16.jpg.json").read_text(encoding="utf-8"))
    c = data.card(S, res, "stored", replay=True)
    vm = [m for m in c["messages"] if m["channel"].startswith("WhatsApp")]
    assert vm and all(DEVANAGARI.search(m["hi"]) and m["ask"] and m["ask_hi"] for m in vm) and c["chat_note"] == "Simulated: nothing is sent"
    assert "Hindi" in c["hindi_note"] and "review" in c["hindi_note"]
    assert set(chat.FIX_HI) == {"P1/H1", "P3", "H3", "H13", "H11", "H10"}


def test_a_reply_photo_posts_the_result_and_the_trackers_own_sentence(server):
    url, S = server
    code, r = post(url + "/api/intake/reply?sample=bill-11.pdf")
    assert code == 200 and r["file"] == "bill-11.pdf"
    own = r["card"]
    bill = next(b for b in S.bills if b.invoice_no == "085/25-26/730")
    assert vendor_sentence(bill) in r["reply"]["en"] and r["status_from"] == "tracker"
    assert chat.hindi_status(bill) in r["reply"]["hi"] and DEVANAGARI.search(r["reply"]["hi"])
    assert r["reply"]["en"].startswith("Thank you, we received your bill 085/25-26/730.")
    assert own["file"] == "bill-11.pdf" and own["checks_total"]


def test_a_reply_that_still_cannot_be_read_asks_again_in_both_languages(server):
    url, S = server
    code, r = post(url + "/api/intake/reply?sample=bill-16.jpg")
    assert code == 200
    asks = [m for m in r["card"]["messages"] if m["channel"].startswith("WhatsApp")]
    for m in asks:
        assert m["ask"] in r["reply"]["en"] and m["ask_hi"] in r["reply"]["hi"]


def test_a_credit_note_reply_says_credit_note(server):
    url, _ = server
    code, r = post(url + "/api/intake/reply?sample=packet-10-credit-note.pdf")
    assert code == 200 and r["card"]["doc_type"] == "credit_note"
    assert "credit note" in r["reply"]["en"] and "क्रेडिट नोट" in r["reply"]["hi"]


def test_an_unknown_photo_without_tesseract_is_refused_not_guessed(server, monkeypatch):
    url, _ = server
    monkeypatch.setattr(data, "tesseract_found", lambda: False)
    code, r = post(url + "/api/intake/reply", b"not a bill", {"X-Filename": "photo.jpg"})
    assert code == 400 and "cannot be read here" in r["error"]
