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
from app.reader import ocr, pipeline
from app.rules import Context
from app.rules.model import AUTO_CLEAR, LOOK
from app.sap.adapter import AS_OF, SapAdapter
from app.tracker import countdown, oldest, pick_order, runway, seed
from app.tracker.msme import LIMIT_DAYS
from app.tracker.runway import HORIZON_DAYS
from app.tracker.payruns import DEFAULT_CUTOFF_DAYS, label as date_label
from app.tracker.pickorder import control_tower, spread

ROOT = Path(__file__).resolve().parent.parent.parent
NUMBERS = ROOT / "notes" / "numbers.md"
IMPACT = ROOT / "backtest" / "out" / "impact.csv"
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
    return (f"Simulated reading: stored extraction from the reader ({n0(N('re.second.all.key_bills_correct'))} of {n0(N('re.first.all.bills'))} hand-labelled bills fully correct on the four key fields; "
            f"weaker on phone photos, {n0(N('re.first.phone_photo.key_bills_correct'))} of {n0(N('re.first.phone_photo.bills'))})")


def field_rows(res: dict) -> list[dict]:
    """The read fields for the card. Below 0.70, or not found, the value is withheld: it is never shown as if it were known."""
    rows = []
    for key, name in FIELDS:
        x = (res.get("fields") or {}).get(key) or {}
        v, c = x.get("value"), float(x.get("conf", 0) or 0)
        if key == "wo_id" and v is None and "printed blank" in x.get("note", ""):
            rows.append(dict(name=name, value="printed blank on the bill", state="review"))
        elif v is None or c < LOOK:
            rows.append(dict(name=name, value="not read", state="unread"))
        else:
            shown = f"{v:,.2f}" if isinstance(v, float) else str(v)
            rows.append(dict(name=name, value=shown, state="ok" if c >= AUTO_CLEAR else "review"))
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
        detail = f"The same number is on {m['bill_id']} dated {m['invoice_date']} for Rs {float(m['amount_inr']):,.0f}. A person decides whether it is a reused number or a duplicate."
    elif r.check_id == "H10":
        detail = (f"Supplier in {ev.get('supplier_state')}, buyer in {ev.get('recipient_state')}, printed place of supply {ev.get('place_of_supply')}, tax charged {ev.get('tax_charged')}. "
                  + ("The two readings of the place of supply give different tax types, so a person decides." if r.certainty < 1 else r.fix))
    who = "Executive" if r.status == "warn" else WHO.get(owner, "Executive")
    return dict(check=r.check_id, title=TITLE.get(r.check_id, r.name), who=who, detail=detail, kind=r.status)


def top_issues(res: dict, out: dict) -> tuple[list[dict], int]:
    """The issues that matter, at most three: what could not be read first (nothing else can be trusted), then confident failures, then what a person must decide."""
    issues = []
    unread = [lab for (key, lab), row in zip(FIELDS, field_rows(res)) if row["state"] == "unread" and not (key == "wo_id" and "printed blank" in ((res.get("fields") or {}).get("wo_id") or {}).get("note", ""))]
    if unread:
        issues.append(dict(check="read", title="Parts of the bill could not be read", who="Vendor", detail="Not read: " + ", ".join(unread) + ". Ask for a clearer photo or scan; nothing is guessed.", kind="resend"))
    rest = []
    for r in out["results"]:
        if r.status == "pass" or r.field_confidence < LOOK:
            continue
        rank = 0 if (r.status == "fail" and r.confidence >= AUTO_CLEAR) else 1 if r.status == "fail" else 2 if r.status == "warn" else 3
        rest.append((rank, ["P1/H1", "P3", "H3", "H13", "H11", "H10"].index(r.check_id), r))
    rest.sort(key=lambda t: t[:2])
    issues += [issue_for(r) for _, _, r in rest]
    return issues[:3], max(0, len(issues) - 3)


def messages(res: dict, out: dict) -> list[dict]:
    """Messages and tasks the verdict would send: composed in plain words, shown in the simulated outbox, never sent."""
    f = res.get("fields") or {}
    name = (f.get("vendor_name") or {})
    vendor = name.get("value") if name.get("value") and name.get("conf", 0) >= LOOK else "Vendor"
    inv = (f.get("invoice_no") or {})
    ref = f"your bill {inv['value']}" if inv.get("value") and inv.get("conf", 0) >= LOOK else "your bill"
    msgs = []
    for a in out["routing"].actions:
        if a.kind == "resend":
            fields = [lab for (key, lab), row in zip(FIELDS, field_rows(res)) if row["state"] == "unread"]
            body = f"Hello {vendor}, we could not read these parts of {ref} clearly: {', '.join(fields)}. Please send a clearer photo or scan of the whole bill. Thank you."
            msgs.append(dict(to=vendor, channel="WhatsApp to the vendor", text=body))
        elif a.kind == "tell-vendor":
            msgs.append(dict(to=vendor, channel="WhatsApp to the vendor", text=f"Hello {vendor}, we checked {ref} on arrival. To pay it without delay please fix: {a.text} Please send the corrected bill today. Thank you."))
        elif a.kind == "task":
            msgs.append(dict(to=WHO.get(a.to, a.to), channel=f"In-app task for {WHO.get(a.to, a.to)}", text=a.text))
        elif a.kind == "human-look":
            msgs.append(dict(to="Commercial executive", channel="In-app task for the executive", text="Please look at this bill before it moves on. " + a.text))
    return msgs


def card(S: State, res: dict, source: str, replay: bool, ms: float = 0.0) -> dict:
    with SapAdapter(pipeline.PACK_DB) as sap:
        ctx = Context(sap, S.bills, bill_counted_in_billed=replay)
        out = intake.check_bill(res, ctx)
    label, sub = LABEL[out["routing"].route]
    issues, more = top_issues(res, out)
    return dict(file=res["file"], bill_type=res.get("bill_type"), source=source, reading_label=reading_label(S, source), route=out["routing"].route, headline=label, sub=sub,
                issues=issues, more_issues=more, fields=field_rows(res), messages=messages(res, out), outbox_note="Simulated outbox. Nothing is sent.",
                review_note="Fields marked needs human review are never guessed.", seconds=round(ms / 1000, 2))


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
    with SapAdapter(pipeline.PACK_DB) as sap:
        wo_rows = runway(bills, sap)
    ahead = [r for r in wo_rows if r["kind"] == "ahead" and any("balance runs out" in f for f in r["flags"])]
    ahead.sort(key=lambda r: -(r["monthly_burn_inr"] or 0))          # the orders that will block the most billing first, not the ones with a few rupees left
    dry = [dict(wo_id=r["wo_id"], property=r["property_code"], balance=f"Rs {r['balance_inr']:,.0f}", burn=f"Rs {r['monthly_burn_inr']:,.0f}", days=int(r["runway_days"]), expires=r["days_to_expiry"]) for r in ahead[:6]]
    return dict(as_of=date_label(AS_OF), cutoff=cutoff, cutoffs=[0, 1, 2], cutoff_note=f"Payment-run cut-off setting: {cutoff} day(s) before the run (Treasury's real rule is unconfirmed).",
                headline=dict(late=sum(1 for r in known if r["state"] == "late"), miss=sum(1 for r in known if r["state"] == "will be late: no run left"), close=len(close),
                              waiting=len(po), dry=len(ahead)),
                labels=dict(late=f"Micro and Small bills already past {LIMIT_DAYS} days", miss="more will miss it: no payment run left", waiting="bills waiting at head office for a clerk",
                            dry=f"work orders whose balance runs out within {HORIZON_DAYS} days"),
                oldest=oldest20, msme=msme, clerks=clerks, spread_pct=(None if spread(after) == float("inf") else round(100 * spread(after), 1)), dry=dry, live_waiting=int(N("l.live.waiting")))


# ------------------------------------------------------------------------------------------------ impact
def impact(S: State) -> dict:
    N = S.numbers
    rows = {(r["group"], r["metric"]): r for r in S.impact}
    f = lambda g, m: tuple(float(rows[(g, m)][k]) for k in ("low", "middle", "high"))
    base = dict(mean=N("l.base.desk_mean"), ms=N("l.base.ms_late"), ms_pct=N("l.base.ms_late_pct"), over=N("l.base.over45"), p90=N("l.base.p90"), n_ms=N("l.n_msme_known"))
    cmb = {m: f("combined", m) for m in ("days_off_mean", "mean_days_desk_to_paid_after", "msme_over_45_days_count", "msme_over_45_days_pct", "all_over_45_days_count", "p90_days_desk_to_paid")}
    intake_days, intake_over, intake_ms = f("intake", "days_off_mean"), f("intake", "all_over_45_days_count"), f("intake", "msme_over_45_days_count")
    note = lambda g: re.search(r"\((.*)\)", rows[(g, "days_off_mean")]["note"]).group(1) if re.search(r"\((.*)\)", rows[(g, "days_off_mean")]["note"]) else rows[(g, "days_off_mean")]["note"]
    clerks = len(control_tower(S.bills))
    levers = []
    for g, title, cond in [
        ("pay", "Pay on the first run after posting", f"Treasury sets the run-list cut-off ({note('pay')}). Why bills miss the first run is unconfirmed: Treasury's run lists are still a question for the client."),
        ("queue", "Balance the AP pick order", f"The AP lead works the order across the {clerks} clerks. This is a replay of last year's waits; the live queue holds only {n0(N('l.live.waiting'))} waiting bills."),
        ("intake", "Check bills at intake", f"The desk and the executives fix problems at the source. The replay assumes a delay left over after a catch of {note('intake')}. Fewer queries, not a faster payment run.")]:
        d = f(g, "days_off_mean")
        levers.append(dict(title=title, days=rng(d[0], d[2], lambda x: f"{x:.2f}"), condition=cond))
    tail_pct = 100 * intake_days[2] / base["mean"]
    return dict(
        label="Replay on last year's register: a counterfactual, not a result.",
        headline=[
            dict(name="Average days from desk to paid", before=n1(base["mean"]), after=rng(base["mean"] - N("l.lever.high.save"), base["mean"] - N("l.lever.low.save")),
                 unit="days", saved=rng(cmb["days_off_mean"][0], cmb["days_off_mean"][2], lambda x: f"{x:.1f}"),
                 condition="Needs Treasury and AP to act on all three levers. Payment-run cause unconfirmed.",
                 scale=dict(before=base["mean"], lo=base["mean"] - N("l.lever.high.save"), hi=base["mean"] - N("l.lever.low.save"), min=0, max=base["mean"])),
            dict(name=f"Micro and Small bills over {LIMIT_DAYS} days", before=n0(base["ms"]), after=rng(cmb["msme_over_45_days_count"][2], cmb["msme_over_45_days_count"][0], n0), unit="bills",
                 saved=f"{rng(cmb['msme_over_45_days_pct'][2], cmb['msme_over_45_days_pct'][0])} per cent of {n0(base['n_ms'])}, from {n1(base['ms_pct'])}",
                 condition="Counted from the date the desk logged the bill. The statutory clock starts earlier, so these are minimums.",
                 scale=dict(before=base["ms"], lo=cmb["msme_over_45_days_count"][2], hi=cmb["msme_over_45_days_count"][0], min=0, max=base["ms"])),
            dict(name="The slowest tenth of bills: days from desk to paid", before=n0(base["p90"]), after=rng(cmb["p90_days_desk_to_paid"][2], cmb["p90_days_desk_to_paid"][0], n0), unit="days",
                 saved=f"{n0(base['p90'] - cmb['p90_days_desk_to_paid'][0])} to {n0(base['p90'] - cmb['p90_days_desk_to_paid'][2])} days",
                 condition="Same conditions as the average. This is the ninetieth percentile.", scale=dict(before=base["p90"], lo=cmb["p90_days_desk_to_paid"][2], hi=cmb["p90_days_desk_to_paid"][0], min=0, max=base["p90"]))],
        levers=levers,
        intake_line=(f"The intake rules barely move the mean ({rng(intake_days[0], intake_days[2], lambda x: f'{x:.2f}')} days, at most {n1(tail_pct)} per cent of it) but protect the tail: "
                     f"bills over {LIMIT_DAYS} days fall from {n0(base['over'])} to {between(intake_over[2], intake_over[0], n0)}, and {n0(N('l.chk.over45_queried'))} of those {n0(base['over'])} bills had a query."),
        low_middle_high=f"Low, middle and high pair {note('pay')} with {note('intake')}.",
        source="Backtest on last year's register (backtest/out/impact.csv). Figures are in notes/numbers.md.")
