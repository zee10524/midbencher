"""What the three screens show, as plain data. The browser code (static/) contains no numbers: every number on screen arrives from here, and here it is read from
`notes/numbers.md`, `backtest/out/impact.csv`, or computed by the tracker, the rules and the reader from the register, the SAP extract and the reader's stored results.

Screens: intake (a bill becomes one card: verdict, the three issues that matter, who fixes each, and a message in a simulated outbox), control tower (oldest bills, MSME
bills close to breach, the pick order across the five AP clerks, work orders about to run dry) and impact (the backtest's before and after, as ranges with their conditions).

Real connection: the same functions would sit behind the product's own API. Messages here are only composed and shown; nothing is sent (the WhatsApp Business API, an approved
template and the vendor's opt-in would be needed, `notes/solution-design.md` section 7).
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import threading
from datetime import date
from pathlib import Path

from app import intake
from app.reader import crosscheck, ocr, pipeline, vision
from app.ui import audit, chat
from app.rules import Context
from app.rules.model import AUTO_CLEAR, LOOK
from app.sap.adapter import AS_OF, SapAdapter
from app.tracker import countdown, oldest, pick_order, seed
from app.tracker.msme import LIMIT_DAYS
from app.tracker.payruns import DEFAULT_CUTOFF_DAYS, label as date_label
from app.tracker.pickorder import control_tower, spread

ROOT = Path(__file__).resolve().parent.parent.parent
NUMBERS = ROOT / "notes" / "numbers.md"
IMPACT = ROOT / "backtest" / "out" / "impact.csv"
RUNWAY = ROOT / "backtest" / "out" / "runway_90d.csv"
UPLOADS = ROOT / "app" / "data" / "uploads"


# ------------------------------------------------------------------------------------------------ numbers.md
class Numbers:
    """The figure register: `notes/numbers.md` rows `| id | value | description |`."""

    def __init__(self, path: Path = NUMBERS):
        self.v: dict[str, float] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\|\s*([A-Za-z0-9_.\-/ ]+?)\s*\|\s*(-?[0-9.]+(?:e[+-]?\d+)?)\s*\|", line)
            if m:
                try:
                    self.v[m.group(1)] = float(m.group(2))
                except ValueError:
                    pass

    def __call__(self, key: str) -> float:
        return self.v[key]


def n0(x: float) -> str:
    return f"{x:,.0f}"


def n1(x: float) -> str:
    return f"{x:,.1f}"


def between(lo: float, hi: float, f=n1) -> str:
    a, b = sorted((lo, hi))
    return f(a) if f(a) == f(b) else f"between {f(a)} and {f(b)}"


def rng(lo: float, hi: float, f=n1) -> str:
    """`24.9 to 27.3`, or one number when the two are the same."""
    a, b = sorted((lo, hi))
    return f(a) if f(a) == f(b) else f"{f(a)} to {f(b)}"


# ------------------------------------------------------------------------------------------------ state shared by requests
class State:
    """Loaded once: the figure register, the impact file, and the register as tracker bills (seeding takes a few seconds, so it runs in the background at start)."""

    def __init__(self):
        self.numbers = Numbers()
        self.impact = list(csv.DictReader(open(IMPACT, encoding="utf-8", newline="")))
        self.bills = []
        self.ready = threading.Event()
        self.error: str | None = None
        self.cache = {}
        self.session = {}       # readings made live in this session, by file hash, so a clerk's entries can be applied to them
        for p in sorted(pipeline.CACHE_DIR.glob("*.json")):
            r = json.loads(p.read_text(encoding="utf-8"))
            self.cache[r["sha256"]] = r
        self.by_name = {r["file"]: r for r in self.cache.values()}

    def load(self) -> None:
        try:
            with SapAdapter(pipeline.PACK_DB) as sap:
                self.bills = seed(ROOT / "pack" / "data" / "bill_register.csv", ROOT / "pack" / "data" / "queries.csv", sap)
        except Exception as e:  # noqa: BLE001 - shown on screen instead of a blank page
            self.error = f"{type(e).__name__}: {e}"
        finally:
            self.ready.set()

    def start(self) -> "State":
        threading.Thread(target=self.load, daemon=True).start()
        return self


# ------------------------------------------------------------------------------------------------ intake
PREVIEW_ROWS = 5      # how many rows of each long list the control tower shows before "show all" (layout only)
LABEL = {"auto-clear": ("Clear at intake", "No finding at intake. Every later check still runs."),
         "fix-before-sending": ("Send back to the vendor before filing", "The vendor can fix this the same day."),
         "fix-internal": ("Fix inside the company", "The bill is not blocked; the owner below starts the fix now."),
         "human-look": ("A person should look", "The evidence is side by side below."),
         "resend": ("Ask the vendor for a clearer image", "Some of what the checks need could not be read, so no verdict is safer than a wrong one.")}
TITLE = {"P1/H1": "Vendor GSTIN does not match our record", "P3": "Work order number missing or unknown", "H3": "Work order cannot cover this bill",
         "H13": "Invoice number already used by this vendor", "H11": "HSN or SAC code or GST rate looks wrong", "H10": "Tax type against place of supply"}
WHO = {"vendor": "Vendor", "procurement": "Procurement", "property": "Property", "AP": "AP verifier", None: "Executive"}
FIELDS = [("vendor_name", "Vendor"), ("vendor_gstin", "Vendor GSTIN"), ("invoice_no", "Invoice number"), ("invoice_date", "Invoice date"), ("wo_id", "Work order"), ("taxable", "Taxable value"), ("total", "Total")]
REQUIRED = [f for f, _ in FIELDS]


def reading_label(S: State, source: str) -> str:
    if source == "live":
        return "Live reading: Tesseract on this machine, just now. Fields marked needs human review are never guessed."
    N = S.numbers
    return (f"Simulated reading: stored extraction from the reader. On the {n0(N('re.first.all.bills'))} hand-labelled bills it read {n0(N('re.second.all.key_bills_correct'))} fully right on the four key fields "
            f"(first run, before any tuning; the stored readings come from a later version tuned on those bills; weaker on phone photos, {n0(N('re.first.phone_photo.key_bills_correct'))} of {n0(N('re.first.phone_photo.bills'))}). "
            f"A person fills in any field it could not read. Its confident readings ({AUTO_CLEAR:.2f} and above) were {n0(N('re.second.cal.hi.correct'))} of {n0(N('re.second.cal.hi.n'))} right on those bills; "
            f"{n0(N('re.first.all.bills'))} bills is a small sample, so read that as a hint, not a guarantee.")


# Shown beside the seven core fields only when the reader did not read them, so that a person can supply what a check that could not run needs.
EXTRA_FIELDS = [("hsn_sac", "HSN or SAC code"), ("recipient_gstin", "Buyer GSTIN"), ("place_of_supply", "Place of supply")]
TYPED = {"vendor_name": "text", "vendor_gstin": "gstin", "invoice_no": "text", "invoice_date": "date", "wo_id": "wo", "taxable": "amount", "total": "amount",
         "hsn_sac": "hsn", "recipient_gstin": "gstin", "place_of_supply": "text"}


def normalise_typed(key: str, text: str):
    """A value a person typed, checked and put in the form the checks use. Raises ValueError with a plain message."""
    t = (text or "").strip()
    kind = TYPED[key]
    if not t:
        raise ValueError("empty")
    if kind == "gstin":
        g = re.sub(r"\s+", "", t).upper()
        if not re.fullmatch(r"[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]", g):
            raise ValueError("a GSTIN has 15 letters and digits, for example two digits, five letters, four digits, a letter, then three characters")
        return g
    if kind == "date":
        m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", t) or re.fullmatch(r"(\d{2})[-/.](\d{2})[-/.](\d{4})", t)
        if not m:
            raise ValueError("write the date as day-month-year or year-month-day")
        a, b, c = m.groups()
        y, mo, d = (a, b, c) if len(a) == 4 else (c, b, a)
        try:
            return date(int(y), int(mo), int(d)).isoformat()
        except ValueError:
            raise ValueError("that is not a real date") from None
    if kind == "hsn":
        h = re.sub(r"\s+", "", t)
        if not re.fullmatch(r"\d{4}(\d{2}(\d{2})?)?", h):
            raise ValueError("an HSN or SAC code has 4, 6 or 8 digits")
        return h
    if kind == "wo":
        w = re.sub(r"\s+", "", t)
        if not re.fullmatch(r"\d{7,10}", w):
            raise ValueError("a work order number is 7 to 10 digits")
        return w
    if kind == "amount":
        try:
            return float(t.replace(",", "").replace("Rs", "").replace("\u20b9", "").strip())
        except ValueError:
            raise ValueError("write the amount as a number") from None
    return " ".join(t.split())


def _show(v) -> str:
    return "not read" if v is None else (f"{v:,.2f}" if isinstance(v, (int, float)) and not isinstance(v, bool) else str(v))


def field_rows(res: dict) -> list[dict]:
    """The read fields for the card. Below 0.70, or not found, the value is withheld: it is never shown as if it were known."""
    rows = []
    for key, name in FIELDS + EXTRA_FIELDS:
        x = (res.get("fields") or {}).get(key) or {}
        v, c = x.get("value"), float(x.get("conf", 0) or 0)
        if (key, name) in EXTRA_FIELDS and x.get("source") != "human_review" and v is not None and c >= LOOK:
            continue                 # an extra field is shown only when it was not read, or a person typed it
        cr = x.get("cross")
        side = dict(state=cr["state"], tesseract=_show(cr["tesseract"]), vision=_show(cr["vision"])) if cr else None
        if cr and cr["state"] == "differ":
            rows.append(dict(key=key, name=name, value="the two readers differ", state="differ", note="needs human review", cross=side))
            continue
        if x.get("source") == "human_review":
            rows.append(dict(key=key, name=name, value=f"{v:,.2f}" if isinstance(v, float) else str(v), state="typed", note="typed by a person"))
        elif x.get("source") == "vendor_master":
            rows.append(dict(key=key, name=name, value=str(v), state="review", note="resolved from vendor master, not read from the bill"))
        elif x.get("source") == "repaired":
            rows.append(dict(key=key, name=name, value=str(v), state="review", note="read with one confusable character; matched to the vendor master"))
        elif key == "wo_id" and v is None and "printed blank" in x.get("note", ""):
            rows.append(dict(key=key, name=name, value="printed blank on the bill", state="review", note="printed blank"))
        elif v is None or c < LOOK:
            rows.append(dict(key=key, name=name, value="not read", state="unread", note="", **({"cross": side} if side else {})))
        else:
            shown = f"{v:,.2f}" if isinstance(v, float) else str(v)
            rows.append(dict(key=key, name=name, value=shown, state="ok" if c >= AUTO_CLEAR else "review", note="", **({"cross": side} if side and cr["state"] in ("agree", "vision_confirms") else {})))
    return rows


def issue_for(r) -> dict:
    ev, owner = r.evidence, r.owner
    detail = r.fix
    if r.check_id == "H3":
        bits = []
        if ev.get("validity") in ("expired", "not_yet_valid"):
            bits.append(f"The work order is {ev['validity'].replace('_', ' ')}: valid to {ev.get('valid_to')}, bill dated {ev.get('bill_date')}.")
        if (ev.get("headroom_after_inr") or 0) < 0:
            bits.append(f"It is over its approved value by Rs {-ev['headroom_after_inr']:,.0f}.")
        detail = " ".join(bits) or r.fix
    elif r.check_id == "H13" and ev.get("matches"):
        m = ev["matches"][0]
        detail = (f"Possible repeat, confirm the invoice number: {m['bill_id']} (dated {m['invoice_date']}, Rs {float(m['amount_inr']):,.0f}) matches on {m.get('basis', 'the invoice number')}. Read the number from the bill and compare."
                  if ev.get("partial") else
                  f"The same number is on {m['bill_id']} dated {m['invoice_date']} for Rs {float(m['amount_inr']):,.0f}. A person decides whether it is a reused number or a duplicate.")
    elif r.check_id == "H10":
        detail = (f"Supplier in {ev.get('supplier_state')}, buyer in {ev.get('recipient_state')}, printed place of supply {ev.get('place_of_supply')}, tax charged {ev.get('tax_charged')}. "
                  + ("The two readings of the place of supply give different tax types, so a person decides." if r.certainty < 1 else r.fix))
    who = "Executive" if r.status == "warn" else WHO.get(owner, "Executive")
    title = "Vendor GSTIN read with a confusable character" if r.check_id == "P1/H1" and "gstin_as_repaired" in ev else TITLE.get(r.check_id, r.name)
    if r.check_id == "H13" and ev.get("partial"):
        title = "Possible repeat: confirm the invoice number"
    return dict(check=r.check_id, title=title, who=who, detail=detail, kind=r.status)


def top_issues(res: dict, out: dict) -> tuple[list[dict], int]:
    """The issues that matter, at most three: confident failures first, then what a person must decide (a possible repeat, a tax type), then what could not be read.
    If nothing else is wrong, what could not be read comes first. A field the reader could not read no longer hides the findings of the checks that did run."""
    rest = []
    for r in out["results"]:
        if r.status == "pass":
            continue
        rank = 0 if (r.status == "fail" and r.confidence >= AUTO_CLEAR) else 1 if r.status == "fail" else 2 if r.status == "warn" else 3
        rest.append((rank, ["P1/H1", "P3", "H3", "H13", "H11", "H10"].index(r.check_id), r))
    rest.sort(key=lambda t: t[:2])
    issues = [issue_for(r) for _, _, r in rest]
    if out["unread"]:
        nr = "; ".join(f"{n['title'].lower()} needs {', '.join(n['needs']).lower()}" for n in out["not_run"])
        issues.append(dict(check="read", title="Parts of the bill could not be read", who="Vendor, or a person types them", kind="resend",
                           detail="Not read: " + ", ".join(out["unread"]) + ". " + ("The checks that need them are listed below. " if nr else "") + "Nothing is guessed: ask for a clearer photo or scan, or type the values below."))
    return issues[:3], max(0, len(issues) - 3)


def messages(res: dict, out: dict) -> list[dict]:
    """Messages and tasks the verdict would send: composed in plain words, shown in the simulated outbox, never sent."""
    f = res.get("fields") or {}
    name = (f.get("vendor_name") or {})
    vendor = name.get("value") if name.get("value") and name.get("conf", 0) >= LOOK else "Vendor"
    noun = "credit note" if res.get("doc_type") == "credit_note" else "bill"
    inv = (f.get("invoice_no") or {})
    ok_inv = bool(inv.get("value") and inv.get("conf", 0) >= LOOK)
    ref = f"your {noun} {inv['value']}" if ok_inv else f"your {noun}"
    msgs = []
    for a in out["routing"].actions:
        if a.kind == "resend":
            body = (f"Hello {vendor}, we could not read these parts of {ref} clearly: {', '.join(out['unread'])}. Please send a clearer photo or scan of the whole {noun}. Thank you."
                    if out["unread"] else f"Hello {vendor}, we could not read {ref} clearly. Please send a clearer photo or scan of the whole {noun}. Thank you.")
            ask, ask_hi = chat.ask_resend(noun, out["unread"])
            msgs.append(dict(to=vendor, channel="WhatsApp to the vendor", text=body, kind="resend", ask=ask, ask_hi=ask_hi,
                             hi=chat.hindi_resend(vendor, noun, inv.get("value") if ok_inv else None, out["unread"])))
        elif a.kind == "tell-vendor":
            ask, ask_hi = chat.ask_fix(noun, a.text, a.checks)
            msgs.append(dict(to=vendor, channel="WhatsApp to the vendor", text=f"Hello {vendor}, we checked {ref} on arrival. To pay it without delay please fix: {a.text} Please send the corrected {noun} today. Thank you.",
                             kind="tell-vendor", ask=ask, ask_hi=ask_hi, hi=chat.hindi_tell_vendor(vendor, noun, inv.get("value") if ok_inv else None, a.checks)))
        elif a.kind == "task":
            msgs.append(dict(to=WHO.get(a.to, a.to), channel=f"In-app task for {WHO.get(a.to, a.to)}", text=a.text))
        elif a.kind == "human-look":
            msgs.append(dict(to="Commercial executive", channel="In-app task for the executive", text="Please look at this bill before it moves on. " + a.text))
    return msgs


def vision_label(res: dict) -> str | None:
    v = res.get("vision")
    if not v:
        return "Not read by the vision model yet."
    return (f"Stored vision reading ({v.get('model') or 'vision model'}, read {v.get('read_at') or 'earlier'}), not a live call. It is a second opinion only: where it agrees with Tesseract the field is marked "
            "two readers agree; where they differ both values are shown and a person decides. Neither is picked automatically. Both readers saw the same image, so agreement is not proof: the checks against SAP still decide the verdict.")


def card(S: State, res: dict, source: str, replay: bool, ms: float = 0.0) -> dict:
    return _card(S, res, source, replay, ms)[0]


def _card(S: State, res: dict, source: str, replay: bool, ms: float = 0.0) -> tuple[dict, dict, dict]:
    """The card, the reader result it was made from (with the cross-check applied) and the intake outcome."""
    res = crosscheck.apply(res, vision.stored(res["file"], res.get("sha256")))
    with SapAdapter(pipeline.PACK_DB) as sap:
        ctx = Context(sap, S.bills, bill_counted_in_billed=replay)
        out = intake.check_bill(res, ctx)
    label, sub = LABEL[out["routing"].route]
    ran = len(out["results"])
    total = len(intake.CHECK_IDS)
    if out["partial"]:
        sub = f"Partial verdict: {ran} of {total} checks ran. " + sub
    issues, more = top_issues(res, out)
    rows = field_rows(res)
    if res.get("sha256") and res["sha256"] not in S.cache:
        S.session[res["sha256"]] = res
    return dict(file=res["file"], key=res.get("sha256"), bill_type=res.get("bill_type"), doc_type=res.get("doc_type", "invoice"), source=source, reading_label=reading_label(S, source),
                route=out["routing"].route, headline=label, sub=sub, partial=out["partial"], checks_ran=ran, checks_total=total,
                not_run=[dict(check=n["check"], title=n["title"], needs=n["needs"]) for n in out["not_run"]], issues=issues, more_issues=more, fields=rows,
                inputs=[r["key"] for r in rows if r["state"] in ("unread", "differ")], vision_label=vision_label(res), messages=messages(res, out), outbox_note="Simulated outbox. Nothing is sent.",
                review_note="Fields marked needs human review are never guessed. A person can type the ones that were not read.", seconds=round(ms / 1000, 2),
                chat_note="Simulated: nothing is sent", hindi_note="The Hindi is a draft and needs a Hindi speaker's review before real use."), res, out


def reply_card(S: State, res: dict, source: str, replay: bool, ms: float = 0.0) -> dict:
    """A vendor's reply photo, read and checked: the full card for it, and the company's answer for the thread (English and Hindi). The status sentence comes from the tracker when the
    bill is in the register, and is the register's own truth as of the as-of date; for a bill that is not in the register the answer says only that the vendor will be told of the next step."""
    c, res2, out = _card(S, res, source, replay, ms)
    own = out.get("own_bill_id")
    bill = next((b for b in S.bills if b.bill_id == own), None) if own else None
    vendor_msgs = [m for m in c["messages"] if m["channel"].startswith("WhatsApp")]
    return dict(card=c, reply=chat.reply(res2, out, bill, vendor_msgs), status_from="tracker" if bill is not None else "none", file=c["file"])


def apply_review(S: State, key: str, values: dict, reviewer: str = "") -> dict:
    """A clerk has typed values for fields the reader did not read: put them in, run the checks again, and save the result to `parsed_bill` with source `human_review`,
    keeping the reader's own value and confidence for each typed field in the `reader_original` column. Returns the new card and what was saved."""
    import copy

    reviewer = " ".join(str(reviewer or "").split())
    if not reviewer:
        raise ValueError("Type your name first, so the entry can be traced to a person.")
    base = S.cache.get(key) or S.session.get(key)
    if base is None:
        raise ValueError("That bill is no longer held: drop or pick it again.")
    res = copy.deepcopy(base)
    errors = {}
    for k, text in (values or {}).items():
        if k not in TYPED or not str(text).strip():
            continue
        try:
            v = normalise_typed(k, str(text))
        except ValueError as e:
            errors[k] = str(e)
            continue
        old = (res.get("fields") or {}).get(k) or {}
        res.setdefault("fields", {})[k] = dict(value=v, conf=1.0, note="typed by a person", source="human_review", raw=None,
                                                original=dict(value=old.get("value"), conf=float(old.get("conf", 0) or 0)))
    if errors:
        raise ValueError("; ".join(f"{dict(FIELDS + EXTRA_FIELDS)[k]}: {m}" for k, m in errors.items()))
    if not any((x or {}).get("source") == "human_review" for x in res["fields"].values()):
        raise ValueError("Nothing was typed.")
    res["arithmetic_ok"] = None if ("taxable" in values or "total" in values) else res.get("arithmetic_ok")
    c = card(S, res, "human_review", replay=True)
    with SapAdapter(pipeline.PACK_DB) as sap:
        out = intake.check_bill(res, Context(sap, S.bills, bill_counted_in_billed=True))
    if not pipeline.WORKING_DB.exists():
        pipeline.make_working_copy()
    args = pipeline.parsed_bill_args(res)
    args["check_status"], args["check_notes"] = out["routing"].route, intake.verdict_notes(res, out) + f" Typed by {reviewer} (human_review)."
    with SapAdapter(pipeline.WORKING_DB) as w:
        rid = w.write_parsed_bill(**args)
    typed_fields = {k: dict(typed=x["value"], reader_original=x.get("original"), vision_value=(((vision.stored(res["file"], res.get("sha256")) or {}).get("fields") or {}).get(k) or {}).get("value")) for k, x in res["fields"].items() if x.get("source") == "human_review"}
    audit.append(dict(kind="human_review", reviewer=reviewer, file=res["file"], sha256=res.get("sha256"), typed=typed_fields, route_after=out["routing"].route, parsed_bill_row=rid,
                      reader_version=(res.get("reader") or {}).get("version")))
    c["saved"] = dict(table="parsed_bill", row=rid, source="human_review", typed=sorted(json.loads(args["reader_original"])), message=f"Saved to parsed_bill as human_review (row {rid}). The reader's own readings are kept in the reader_original column.")
    return c


def samples(S: State) -> list[dict]:
    return [dict(file=r["file"], bill_type=r["bill_type"]) for r in sorted(S.by_name.values(), key=lambda r: r["file"])]


def stored_for(S: State, name: str | None, body: bytes | None) -> dict | None:
    """The stored extraction for a dropped file: matched by the file's SHA-256, or by name for a sample picked from the list."""
    if body:
        return S.cache.get(hashlib.sha256(body).hexdigest())
    return S.by_name.get(name or "")


def live_read(S: State, name: str, body: bytes) -> dict:
    """Run the reader on an uploaded file now (Tesseract needed). The result is kept under app/data/uploads, not in the committed cache."""
    UPLOADS.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", name) or "upload"
    path = UPLOADS / safe
    path.write_bytes(body)
    with SapAdapter(pipeline.PACK_DB) as sap:
        return pipeline.read_file(path, sap=sap, refresh=True, cache_dir=UPLOADS / "cache")


def tesseract_found() -> bool:
    return ocr.tesseract_available()


# ------------------------------------------------------------------------------------------------ control tower
# the three cut-off cases, worst first, named as on the Impact page (the cut-off is how many days before a run the list closes)
SCENARIOS = [dict(cutoff=2, label="Two days before the run", case="worst case"), dict(cutoff=1, label="One day before", case="middle case"), dict(cutoff=0, label="Same day", case="best case")]


def _will_miss(bills, cutoff: int) -> int:
    """Known Micro and Small bills that will miss the limit because no payment run is left, for one cut-off: the same count as the headline."""
    return sum(1 for r in countdown(bills, cutoff) if r["msme_status"] in ("Micro", "Small") and r["state"] == "will be late: no run left")


def control(S: State, cutoff: int = DEFAULT_CUTOFF_DAYS) -> dict:
    N = S.numbers
    bills = S.bills
    cd = countdown(bills, cutoff)
    miss = {r["bill_id"] for r in cd if r["state"] in ("late", "will be late: no run left")}
    known = [r for r in cd if r["msme_status"] in ("Micro", "Small")]
    oldest20 = []
    for b in oldest(bills, 20):
        stuck = b.stage_name + (f", query open {b.days_in_query} days" if b.open_query else "")
        oldest20.append(dict(bill_id=b.bill_id, vendor=b.vendor_name, amount=f"Rs {b.amount:,.0f}", days=b.days_since_desk, stuck=stuck, in_stage=b.days_in_stage, owner=b.owner,
                             reason=(b.open_query.reason if b.open_query else None), miss=b.bill_id in miss))
    close = [r for r in cd if r["days_remaining"] >= 0][:8]
    msme = [dict(bill_id=r["bill_id"], vendor=r["vendor"], amount=f"Rs {r['amount_inr']:,.0f}", days_left=r["days_remaining"], runs_left=r["runs_left"], last_run=date_label(r["last_run"]) if r["last_run"] else None,
                 group=r["group"], unknown=r["msme_status"] == "Unknown", stage=r["stage"], owner=r["owner"], miss=r["state"] == "will be late: no run left") for r in close]
    po = pick_order(bills)
    tower = control_tower(bills)
    after = {r["verifier"]: r["in_hand_after"] for r in tower}
    clerks = []
    for r in tower:
        mine = [p for p in po if p["verifier"] == r["verifier"]]
        clerks.append(dict(clerk=r["verifier"], in_hand=r["in_hand"], new=r["new_from_pick_order"], after=r["in_hand_after"], queries=r["open_queries"],
                           first=(f"{mine[0]['bill_id']} ({mine[0]['msme_status']}, {mine[0]['days_since_desk']} days)" if mine else None)))
    # work orders likely to run dry: from backtest/out/runway_90d.csv (analysis/17_runway_90d.py), burn estimated from the last 90 days of billing, ranked by monthly billing
    wo = list(csv.DictReader(open(RUNWAY, encoding="utf-8", newline="")))
    dry = [dict(wo_id=r["wo_id"], property=r["property_code"], vendor=r["vendor_name"], balance=f"Rs {int(r['balance_inr']):,}", burn=f"Rs {int(r['monthly_billing_inr']):,}",
                days=int(float(r["runway_days"])), expires=int(r["days_to_expiry"]), vendor_waiting=r["vendor_has_bill_waiting"] == "True") for r in wo[:6]]
    miss_now = sum(1 for r in known if r["state"] == "will be late: no run left")
    miss_mid = miss_now if cutoff == DEFAULT_CUTOFF_DAYS else _will_miss(bills, DEFAULT_CUTOFF_DAYS)
    case = next(s for s in SCENARIOS if s["cutoff"] == cutoff)
    if cutoff == DEFAULT_CUTOFF_DAYS:
        effect = f"This is the middle case: {miss_now:,} more Micro and Small {'bill' if miss_now == 1 else 'bills'} will miss the {LIMIT_DAYS}-day limit because no payment run is left."
    else:
        d = miss_now - miss_mid
        effect = (f"In the {case['case']}, {miss_now:,} more Micro and Small {'bill' if miss_now == 1 else 'bills'} will miss the {LIMIT_DAYS}-day limit, "
                  + (f"{abs(d):,} {'more' if d > 0 else 'fewer'} than the {miss_mid:,} in the middle case." if d else f"the same as in the middle case."))
    return dict(as_of=date_label(AS_OF), cutoff=cutoff, cutoffs=[0, 1, 2], scenarios=SCENARIOS, effect=effect, cutoff_note=f"Payment runs are modelled with the run list closing {cutoff} {'day' if cutoff == 1 else 'days'} before the run. Treasury's real rule is unconfirmed.",
                headline=dict(late=sum(1 for r in known if r["state"] == "late"), miss=sum(1 for r in known if r["state"] == "will be late: no run left"), close=len(close),
                              waiting=len(po), dry=int(N("rw.dry")), dry_vendor_waiting=int(N("rw.dry.vendor_waiting"))),
                labels=dict(late=f"Micro and Small bills already past {LIMIT_DAYS} days", miss="more will miss it: no payment run left", waiting="bills waiting at head office for a clerk",
                            dry=f"work orders likely to run dry within {N('rw.horizon_days'):.0f} days, estimated from the last {N('rw.window_days'):.0f} days of billing",
                            dry_extra=f"{N('rw.dry.vendor_waiting'):,.0f} of them have a vendor with a bill already waiting",
                            dry_note=(f"An estimate, not a forecast: it depends on how many days of billing set the burn "
                                      f"({N('rw.sens.window_60d.dry'):,.0f} orders with the last {N('rw.sens.window_lo_days'):.0f} days, {N('rw.sens.window_120d.dry'):,.0f} with the last {N('rw.sens.window_hi_days'):.0f} days).")),
                preview=PREVIEW_ROWS, oldest=oldest20, msme=msme, clerks=clerks, spread_pct=(None if spread(after) == float("inf") else round(100 * spread(after), 1)), dry=dry, live_waiting=int(N("l.live.waiting")))


# ------------------------------------------------------------------------------------------------ impact
LEVER_SOURCE = {"pay": "backtest/out/impact.csv, group pay, days_off_mean (worst to best case); the figures l.lever.pay2.save to l.lever.pay0.save in notes/numbers.md.",
                "queue": "backtest/out/impact.csv, group queue, days_off_mean; the figure l.lever.queue.save in notes/numbers.md.",
                "intake": "backtest/out/impact.csv, group intake, days_off_mean (worst to best case); the figures l.lever.in3.save, l.lever.in1.save and l.lever.inopt.save in notes/numbers.md."}
METRIC_SOURCE = ["Before: l.base.desk_mean. After: that minus the saving, from backtest/out/impact.csv (group combined, days_off_mean) and l.lever.low.save to l.lever.high.save. All registered in notes/numbers.md.",
                 "Before: l.base.ms_late, l.base.ms_late_pct and l.n_msme_known. After: backtest/out/impact.csv (group combined, msme_over_45_days_count and msme_over_45_days_pct). Registered in notes/numbers.md.",
                 "Before: l.base.p90. After: backtest/out/impact.csv (group combined, p90_days_desk_to_paid). Registered in notes/numbers.md."]


def impact(S: State) -> dict:
    N = S.numbers
    rows = {(r["group"], r["metric"]): r for r in S.impact}
    f = lambda g, m: tuple(float(rows[(g, m)][k]) for k in ("low", "middle", "high"))
    base = dict(mean=N("l.base.desk_mean"), ms=N("l.base.ms_late"), ms_pct=N("l.base.ms_late_pct"), over=N("l.base.over45"), p90=N("l.base.p90"), n_ms=N("l.n_msme_known"))
    cmb = {m: f("combined", m) for m in ("days_off_mean", "mean_days_desk_to_paid_after", "msme_over_45_days_count", "msme_over_45_days_pct", "all_over_45_days_count", "p90_days_desk_to_paid")}
    intake_days, intake_over, intake_ms = f("intake", "days_off_mean"), f("intake", "all_over_45_days_count"), f("intake", "msme_over_45_days_count")
    # the backtest notes say "cut-off 2 / 1 / 0" and "residual 3 days / 1 day / optimistic"; the numbers are read from them, the words are plain
    cut = re.search(r"cut-off (\d+) / (\d+) / (\d+)", rows[("pay", "days_off_mean")]["note"]).groups()
    resid = re.search(r"residual (\d+) days? / (\d+) days?", rows[("intake", "days_off_mean")]["note"]).groups()
    days = lambda k: f"{k} day" if k == "1" else f"{k} days"
    pay_words = f"the run list closes {days(cut[0])} before the run in the worst case, {days(cut[1])} in the middle case and {days(cut[2])} in the best case"
    intake_words = f"a caught query still costs {days(resid[0])} in the worst case and {days(resid[1])} in the middle case, and the best case counts every query from the two early layers with {days(resid[1])} left"
    clerks = len(control_tower(S.bills))
    levers = []
    for g, title, sentence, cond in [
        ("pay", "Pay on the first run after posting", "A bill goes out on the first Tuesday or Friday run after it is posted, instead of waiting for the next one.",
         f"Depends on when Treasury closes the run list: {pay_words}. Why bills miss the first run is still unconfirmed."),
        ("queue", "Balance the AP pick order", "Bills at head office are picked up in turn across the clerks, so none waits behind a long queue.",
         f"Replays last year's waits across the {clerks} clerks; the live queue holds only {n0(N('l.live.waiting'))} waiting bills."),
        ("intake", "Check bills at intake", "A problem is caught the day the bill arrives and sent back to the vendor, so it does not sit in a query.",
         f"Depends on how long a bill still takes after a problem is caught: {intake_words}. Fewer queries, not a faster payment run.")]:
        d = f(g, "days_off_mean")
        levers.append(dict(title=title, sentence=sentence, days=rng(d[0], d[2], lambda x: f"{x:.2f}"), condition=cond, source=LEVER_SOURCE[g]))
    tail_pct = 100 * intake_days[2] / base["mean"]
    return dict(
        label="Replay on last year's register: a counterfactual, not a result.",
        headline=[
            dict(source=METRIC_SOURCE[0], name="Average days from desk to paid", before=n1(base["mean"]), after=rng(base["mean"] - N("l.lever.high.save"), base["mean"] - N("l.lever.low.save")),
                 unit="days", saved=rng(cmb["days_off_mean"][0], cmb["days_off_mean"][2], lambda x: f"{x:.1f}"),
                 sentence=f"from {n1(base['mean'])} days today, which is {rng(cmb['days_off_mean'][0], cmb['days_off_mean'][2], lambda x: f'{x:.1f}')} days faster",
                 condition="Needs Treasury and AP to act on all three changes. Payment-run cause unconfirmed.",
                 scale=dict(before=base["mean"], lo=base["mean"] - N("l.lever.high.save"), hi=base["mean"] - N("l.lever.low.save"), min=0, max=base["mean"])),
            dict(source=METRIC_SOURCE[1], name=f"Micro and Small bills paid after more than {LIMIT_DAYS} days", before=n0(base["ms"]), after=rng(cmb["msme_over_45_days_count"][2], cmb["msme_over_45_days_count"][0], n0), unit="bills",
                 sentence=(f"from {n1(base['ms_pct'])} per cent of Micro and Small bills ({n0(base['ms'])} of {n0(base['n_ms'])}) to "
                           f"{rng(cmb['msme_over_45_days_pct'][2], cmb['msme_over_45_days_pct'][0])} per cent ({rng(cmb['msme_over_45_days_count'][2], cmb['msme_over_45_days_count'][0], n0)})"),
                 saved=f"{rng(cmb['msme_over_45_days_pct'][2], cmb['msme_over_45_days_pct'][0])} per cent of {n0(base['n_ms'])}, from {n1(base['ms_pct'])}",
                 condition="Counted from the date the desk logged the bill. The statutory clock starts earlier, so these are minimums.",
                 scale=dict(before=base["ms"], lo=cmb["msme_over_45_days_count"][2], hi=cmb["msme_over_45_days_count"][0], min=0, max=base["ms"])),
            dict(source=METRIC_SOURCE[2], name="The slowest tenth of bills: days from desk to paid", before=n0(base["p90"]), after=rng(cmb["p90_days_desk_to_paid"][2], cmb["p90_days_desk_to_paid"][0], n0), unit="days",
                 saved=f"{n0(base['p90'] - cmb['p90_days_desk_to_paid'][0])} to {n0(base['p90'] - cmb['p90_days_desk_to_paid'][2])} days",
                 sentence=f"from {n0(base['p90'])} days today, which is {n0(base['p90'] - cmb['p90_days_desk_to_paid'][0])} to {n0(base['p90'] - cmb['p90_days_desk_to_paid'][2])} days faster",
                 condition="Same conditions as the average. This is the ninetieth percentile.", scale=dict(before=base["p90"], lo=cmb["p90_days_desk_to_paid"][2], hi=cmb["p90_days_desk_to_paid"][0], min=0, max=base["p90"]))],
        levers=levers,
        intake_line=(f"The intake rules barely move the mean ({rng(intake_days[0], intake_days[2], lambda x: f'{x:.2f}')} days, at most {n1(tail_pct)} per cent of it) but protect the tail: "
                     f"bills over {LIMIT_DAYS} days fall from {n0(base['over'])} to {between(intake_over[2], intake_over[0], n0)}, and {n0(N('l.chk.over45_queried'))} of those {n0(base['over'])} bills had a query."),
        low_middle_high=f"Best, middle and worst case: {pay_words}. For the intake rules, {intake_words}.",
        reading_note="Each range runs from the worst case to the best case, with the middle case between.",
        source="Backtest on last year's register (backtest/out/impact.csv). Figures are in notes/numbers.md.")
