"""Tests for app/reader. They use text of the kind the OCR returns (copied from files outside the hand-labelled ten), synthetic images, and, where Tesseract is
installed, one real development file. The hand-labelled file is never opened, read or referred to by any reader code or test."""
import json
import shutil
from pathlib import Path

import pymupdf
import pytest
from PIL import Image, ImageDraw, ImageFont

from app.reader import fields as F
from app.reader import images, ocr, pipeline
from app.reader.classify import classify_page, supporting_documents
from app.sap.adapter import SapAdapter

ROOT = Path(__file__).resolve().parent.parent
INBOX = ROOT / "pack" / "context" / "documents" / "bill-inbox"
HAS_TESS = ocr.tesseract_available()

BILL = """HEMKUNT GARUD HYGIENE SOLUTIONS
Delhi | GSTIN O7FFWFT1642T1ZA
TAX INVOICE
Invoice No: 866/25-26/737 Date: 05-11-2025
Bill to:
Property Management Division
Residential Society, Sector 94, Sonipat
GSTIN O6AAACX4421K1ZQ | Place of supply: Haryana
Work order / PO: 4100272
Description HSN/SAC Qty Rate Amount
Housekeeping services 998533 1 5,75,510.00 5,75,510.00
Taxable value 5,75,510.00
IGST @ 18% 1,03,591.80
Total 6,79,101.80
Bank: State bank branch, current account ending 4471
This is a computer generated invoice.
For Hemkunt Garud Hygiene Solutions
Authorised"""


def page(text):
    return ocr.text_page(text)


# ------------------------------------------------------------------ images
def _text_image(w=1400, h=1800, angle=0.0, dark_border=False):
    img = Image.new("L", (w, h), 255)
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 34)
    except OSError:
        font = ImageFont.load_default()
    for i in range(28):
        d.text((100, 120 + i * 55), f"Line {i} Description of services rendered 998533 1 5,75,510.00", fill=0, font=font)
    if angle:
        img = img.rotate(angle, resample=Image.BICUBIC, expand=True, fillcolor=255)
    if dark_border:
        bg = Image.new("L", (img.width + 400, img.height + 400), 25)
        bg.paste(img, (200, 200))
        img = bg
    return img


def test_deskew_estimates_a_known_tilt():
    for tilt in (3.0, -2.0):
        tilted = _text_image(angle=tilt)
        est = images.estimate_skew(tilted)
        assert abs(est - tilt) < 0.6, (tilt, est)                          # the estimate has the sign of the tilt applied (counter-clockwise is positive)
        straight, _, _ = images.clean(tilted.convert("RGB"))
        assert abs(images.estimate_skew(straight)) < 0.6, tilt             # and cleaning removes it


def test_clean_straightens_and_enlarges_small_images():
    out, angle, cropped = images.clean(_text_image(w=700, h=900, angle=2.0).convert("RGB"))
    assert out.height >= images.MIN_HEIGHT and abs(angle) > 1 and cropped is False


def test_crop_removes_a_dark_background_but_not_a_white_margin():
    _, cropped = images.crop_to_page(_text_image(dark_border=True))
    assert cropped is True
    _, cropped = images.crop_to_page(_text_image())
    assert cropped is False


def test_pdf_pages_are_rendered_at_300_dpi_and_have_no_text_layer(tmp_path):
    src = tmp_path / "img.png"
    _text_image().save(src)
    doc = pymupdf.open()
    pg = doc.new_page(width=595, height=842)               # A4 in points
    pg.insert_image(pg.rect, filename=str(src))
    pdf = tmp_path / "scan.pdf"
    doc.save(pdf)
    doc.close()
    assert images.pdf_text_layer(pdf) is None              # an image-only PDF has no text layer: the OCR path is used
    (img,) = images.render_pdf(pdf)
    assert abs(img.width - round(595 / 72 * 300)) <= 2 and abs(img.height - round(842 / 72 * 300)) <= 2


def test_text_layer_fast_path_when_a_pdf_has_text(tmp_path):
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 100), "TAX INVOICE Invoice No: 866/25-26/737 Date: 05-11-2025 Total 6,79,101.80 " * 2)
    pdf = tmp_path / "text.pdf"
    doc.save(pdf)
    doc.close()
    pages = images.pdf_text_layer(pdf)
    assert pages and "866/25-26/737" in pages[0]


# ------------------------------------------------------------------ classification
@pytest.mark.parametrize("text, expected", [
    ("PANCHJANYA FACILITY SERVICES\nHaryana | GSTIN 06QIAPL1108N1Z5\nTAX INVOICE\nInvoice No: 354/25-26/289", "bill"),
    ("CREDIT NOTE\nCredit note No: CN/528/25-26/207", "bill"),
    ("ATTENDANCE SUMMARY\nStaff Days\nHK-201 26", "attendance"),
    ("a i\nDELIVERY CHALLAN\nFloor cleaner 5 L 40", "challan"),
    ("DELIVERY CHALIAN\nChalian No: DC-5858", "challan"),
    ("SERVICE REPORT\nVisit date Lift Work done Status", "service_report"),
    ("PF AND ESIC CHALLAN\nMonth: March 2026", "pf_esic"),
    ("GOODS RECEIPT NOTE (SAP printout)\nPO Material Qty received Unit", "other:goods_receipt_note"),
    ("WORK ORDER EXTRACT\nWork order 4101352", "other:work_order_extract"),
    ("something unrelated\nnothing here", "other"),
])
def test_page_classes(text, expected):
    assert classify_page(page(text)) == expected


def test_supporting_documents_of_a_packet():
    sup = supporting_documents(["bill", "attendance", "other:goods_receipt_note"])
    assert sup == {"attendance": True, "challan": False, "service_report": False, "pf_esic": False}
    assert not any(supporting_documents(["bill"]).values())


# ------------------------------------------------------------------ fields
def test_gstin_repair_by_position():
    assert F.repair_gstin("O7FFWFT1642T1ZA") == ("07FFWFT1642T1ZA", 1)
    assert F.repair_gstin("06PPTPUOO50N1ZY") == ("06PPTPU0050N1ZY", 2)
    assert F.repair_gstin("07FFWFT1642T1ZA") == ("07FFWFT1642T1ZA", 0)


def test_amounts_and_dates_parse():
    assert F.parse_amount("5,75,510.00") == 575510.0 and F.parse_amount("616,720.00") == 616720.0
    assert F.parse_amount("-1,028.96") == -1028.96 and F.parse_amount("(1,028.96)") == -1028.96 and F.parse_amount("−1,028.96") == -1028.96
    assert str(F.parse_date("05-11-2025")) == "2025-11-05" and F.parse_date("31-02-2025") is None and F.parse_date("26.09.2996").year == 2996


def test_a_clean_bill_is_read_in_full_and_the_amounts_check_out():
    b = F.extract_bill(page(BILL))
    assert b.vendor_name.value == "HEMKUNT GARUD HYGIENE SOLUTIONS"
    assert b.vendor_gstin.value == "07FFWFT1642T1ZA"            # the vendor's, not the buyer's 06AAACX4421K1ZQ
    assert b.recipient_gstin.value == "06AAACX4421K1ZQ"
    assert (b.invoice_no.value, b.invoice_date.value, b.wo_id.value) == ("866/25-26/737", "2025-11-05", "4100272")
    assert (b.taxable.value, b.igst.value, b.total.value) == (575510.0, 103591.8, 679101.8) and b.cgst.value is None
    assert b.arithmetic_ok is True and b.taxable.conf >= 0.97 and b.total.conf >= 0.97
    assert b.hsn_sac.value == "998533" and b.place_of_supply.value == "Haryana" and b.doc_type == "invoice"
    assert b.property_name.value == "Residential Society, Sector 94, Sonipat"


def test_amounts_that_do_not_add_up_are_not_trusted():
    b = F.extract_bill(page(BILL.replace("Total 6,79,101.80", "Total 6,79,191.80")))
    assert b.arithmetic_ok is False and b.total.conf <= 0.5 and b.taxable.conf <= 0.5
    assert any("does not equal total" in r for r in b.reasons)
    st, hint, overall, reasons = pipeline.judge(b)
    assert st == "review" and hint == "resend" and overall <= 0.5


def test_tax_line_against_its_printed_rate():
    b = F.extract_bill(page(BILL.replace("IGST @ 18% 1,03,591.80", "IGST @ 12% 1,03,591.80").replace("Total 6,79,101.80", "Total 6,79,101.80")))
    assert b.arithmetic_ok is False and any("printed rate" in r for r in b.reasons)


def test_split_tax_lines_and_no_gst_bills():
    cs = BILL.replace("IGST @ 18% 1,03,591.80", "CGST @ 9% 51,795.90\nSGST @ 9% 51,795.90")
    b = F.extract_bill(page(cs))
    assert (b.cgst.value, b.sgst.value, b.igst.value) == (51795.9, 51795.9, None) and b.arithmetic_ok is True
    diesel = BILL.replace("IGST @ 18% 1,03,591.80", "GST Not applicable (outside GST)").replace("Total 6,79,101.80", "Total 5,75,510.00")
    d = F.extract_bill(page(diesel))
    assert d.no_gst_printed is True and d.arithmetic_ok is True and d.total.value == 575510.0


def test_a_missing_field_is_not_guessed():
    b = F.extract_bill(page(BILL.replace("Work order / PO: 4100272", "Work order / PO:")))
    assert b.wo_id.value is None and b.wo_id.conf == 0.0
    st, hint, overall, reasons = pipeline.judge(b)
    assert st == "review" and any(r.startswith("wo_id: not found") for r in reasons) and hint == "resend"
    b2 = F.extract_bill(page(BILL.replace("Invoice No: 866/25-26/737 Date: 05-11-2025", "")))
    assert b2.invoice_no.value is None and b2.invoice_date.value is None


def test_a_bad_gstin_shape_is_not_accepted():
    b = F.extract_bill(page(BILL.replace("O7FFWFT1642T1ZA", "O7FFWFT1642T1ZAA")))
    assert b.vendor_gstin.value is None and "not a valid GSTIN shape" in b.vendor_gstin.note


def test_state_code_must_agree_with_the_state_printed_beside_it():
    wrong = F.extract_bill(page(BILL.replace("Delhi | GSTIN O7FFWFT1642T1ZA", "Haryana | GSTIN O7FFWFT1642T1ZA")))
    assert wrong.vendor_gstin.conf <= 0.3
    ok = F.extract_bill(page(BILL))
    assert ok.vendor_gstin.conf >= 0.9 or ok.vendor_gstin.conf == 0.8      # without a second read of the image the repaired GSTIN stays at 0.80
    assert "state name agrees" in ok.vendor_gstin.note


def test_state_code_taken_from_the_name_when_the_printed_characters_are_confusable():
    b = F.extract_bill(page(BILL.replace("Delhi | GSTIN O7FFWFT1642T1ZA", "Uttar Pradesh | GSTIN OGFFWFT1642T1ZA")))
    assert b.vendor_gstin.value == "09FFWFT1642T1ZA" and "state code taken from the state name" in b.vendor_gstin.note


def test_date_outside_the_invoice_numbers_financial_year_is_flagged():
    b = F.extract_bill(page(BILL.replace("05-11-2025", "05-11-2026")))
    assert b.invoice_date.conf < 0.6 and any("financial year" in r for r in b.reasons)


def test_vendor_name_must_match_the_for_line():
    b = F.extract_bill(page(BILL.replace("For Hemkunt Garud Hygiene Solutions", "For Somebody Else Entirely")))
    assert b.vendor_name.conf < F.AUTO
    assert F.extract_bill(page(BILL)).vendor_name.conf >= 0.9


def test_credit_note_amounts_keep_their_sign():
    cn = """GARUD PRATAP TRADERS
Uttar Pradesh | GSTIN 09LGQFQ3122D1ZY
CREDIT NOTE
Credit Note No: CN/528/25-26/207 Date: 31-01-2026
Bill to:
Property Management Division
Residential Society, Sector 94, Sonipat
GSTIN 06AAACX4421K1ZQ | Place of supply: Haryana
Work order / PO: 4101182
Description HSN/SAC Qty Rate Amount
Return of goods 3304 1 -871.99 -871.99
Taxable value -871.99
IGST @ 18% -156.96
Total -1,028.95
For Garud Pratap Traders"""
    b = F.extract_bill(page(cn))
    assert b.doc_type == "credit_note" and b.invoice_no.value == "CN/528/25-26/207"
    assert (b.taxable.value, b.igst.value, b.total.value) == (-871.99, -156.96, -1028.95) and b.arithmetic_ok is True


def test_property_is_identified_only_when_one_sap_property_has_that_name(tmp_path):
    shutil.copy(ROOT / "pack" / "data" / "sap_extract.sqlite", tmp_path / "c.sqlite")
    with SapAdapter(tmp_path / "c.sqlite") as sap:
        assert F.extract_bill(page(BILL), sap).property_name.value == "SNP-R09"
        none = F.extract_bill(page(BILL.replace("Sector 94, Sonipat", "Sector 1, Nowhere")), sap)
        assert none.property_name.value is None and none.property_name.conf == 0.0


# ------------------------------------------------------------------ pipeline
def test_bill_types_come_from_the_file_name_and_extension():
    assert pipeline.bill_type_of(Path("bill-11.pdf")) == "pdf_single" and pipeline.bill_type_of(Path("packet-01-x.pdf")) == "pdf_packet"
    assert pipeline.bill_type_of(Path("bill-16.jpg")) == "phone_photo"


def test_low_confidence_values_are_withheld_from_parsed_bill():
    res = dict(file="x.pdf", status="review", route_hint="resend", overall_confidence=0.3, bill_type="pdf_single", doc_type="invoice", reasons=["vendor_gstin: confidence 0.30"],
               supporting={"attendance": True, "challan": False, "service_report": False, "pf_esic": False}, reader={"simulated": False},
               fields={"vendor_gstin": dict(value="07FFWFT1642T1ZA", conf=0.30, note=""), "invoice_no": dict(value="866/25-26/737", conf=0.92, note=""),
                       "taxable": dict(value=100.0, conf=0.97, note=""), "total": dict(value=118.0, conf=0.97, note=""), "igst": dict(value=18.0, conf=0.97, note=""),
                       "property_name": dict(value="SNP-R09", conf=0.99, note="")})
    a = pipeline.parsed_bill_args(res)
    assert a["vendor_gstin"] is None and a["invoice_no"] == "866/25-26/737" and a["total_inr"] == 118.0 and a["property_code"] == "SNP-R09"
    assert "withheld, low-confidence reading '07FFWFT1642T1ZA'" in a["check_notes"] and "supporting documents present: attendance" in a["check_notes"]
    assert a["check_status"] == "review" and a["confidence"] == 0.3


def test_vision_fallback_is_off_by_default_and_makes_no_call(monkeypatch):
    assert pipeline.VISION_FALLBACK is False and pipeline.vision_fallback(None, ["x"]) is None
    monkeypatch.setattr(pipeline, "VISION_FALLBACK", True)
    with pytest.raises(RuntimeError, match="no API key and makes no network call"):
        pipeline.vision_fallback(None, ["x"])


def test_without_tesseract_and_without_a_cache_the_reader_says_so_and_guesses_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(ocr, "tesseract_available", lambda: False)
    f = INBOX / "bill-13.pdf"
    res = pipeline.read_file(f, cache_dir=tmp_path)
    assert res["status"] == "review" and res["fields"] == {} and res["reader"]["simulated"] is True and "Tesseract is not installed" in res["reasons"][0]


def test_cached_result_is_used_without_tesseract_and_marked_simulated(tmp_path, monkeypatch):
    f = tmp_path / "bill-99.pdf"
    f.write_bytes(b"%PDF-1.4 fake")
    cached = dict(file=f.name, sha256=pipeline.sha256(f), status="ok", route_hint="auto-clear", reader=dict(simulated=False), fields={})
    (tmp_path / "bill-99.pdf.json").write_text(json.dumps(cached), encoding="utf-8")
    monkeypatch.setattr(ocr, "tesseract_available", lambda: False)
    res = pipeline.read_file(f, cache_dir=tmp_path)
    assert res["status"] == "ok" and res["reader"]["simulated"] is True
    f.write_bytes(b"%PDF-1.4 changed")                                   # a changed file does not match the cache
    assert pipeline.read_file(f, cache_dir=tmp_path)["status"] == "review"


@pytest.mark.skipif(not HAS_TESS, reason="Tesseract not installed")
def test_end_to_end_on_one_development_file(tmp_path):
    shutil.copyfile(ROOT / "pack" / "data" / "sap_extract.sqlite", tmp_path / "work.sqlite")
    with SapAdapter(tmp_path / "work.sqlite") as sap:
        res = pipeline.read_file(INBOX / "bill-13.pdf", sap=sap, cache_dir=tmp_path / "cache")
        assert res["status"] == "ok" and res["fields"]["invoice_no"]["value"] == "866/25-26/737" and res["fields"]["vendor_gstin"]["value"] == "07FFWFT1642T1ZA"
        assert res["bill_type"] == "pdf_single" and res["pages"][0]["class"] == "bill" and res["pages"][0]["source"] == "tesseract"
        rid = sap.write_parsed_bill(**pipeline.parsed_bill_args(res))
        row = sap._ro.execute("select source_file, invoice_no, total_inr, check_status from parsed_bill where rowid = ?", (rid,)).fetchone()
        assert tuple(row) == ("bill-13.pdf", "866/25-26/737", 679101.8, "ok")
        monkey_called = []
        orig = ocr.ocr_page
        ocr.ocr_page = lambda *a, **k: monkey_called.append(1) or orig(*a, **k)
        try:
            again = pipeline.read_file(INBOX / "bill-13.pdf", sap=sap, cache_dir=tmp_path / "cache")
        finally:
            ocr.ocr_page = orig
        assert again["fields"] == res["fields"] and monkey_called == []         # second call came from the cache


@pytest.mark.skipif(not HAS_TESS, reason="Tesseract not installed")
def test_packet_pages_are_classified_and_supporting_documents_recorded(tmp_path):
    res = pipeline.read_file(INBOX / "packet-02-housekeeping-manpower.pdf", cache_dir=tmp_path)
    assert [p["class"] for p in res["pages"]] == ["bill", "attendance"] and res["supporting"]["attendance"] is True and res["supporting"]["challan"] is False
    assert res["bill_type"] == "pdf_packet" and res["fields"]["taxable"]["value"] == 380016.0


# ------------------------------------------------------------------ the rule about the labelled file
def test_reader_code_and_tests_never_refer_to_the_hand_labelled_file():
    needle = "gold" + "_labels"
    for p in [*(ROOT / "app" / "reader").glob("*.py"), Path(__file__)]:
        text = p.read_text(encoding="utf-8")
        assert needle not in text.replace('needle = "gold" + "_labels"', ""), p


# ------------------------------------------------------------------ fixes made after the first-run score (fields the labels do not score)
def test_a_work_order_line_printed_blank_is_recorded_as_such():
    b = F.extract_bill(page(BILL.replace("Work order / PO: 4100272", "Work order / PO:")))
    assert b.wo_id.value is None and "printed blank" in b.wo_id.note


def test_hsn_is_found_whatever_the_table_header_says_and_never_in_a_bank_line():
    item = BILL.replace("Description HSN/SAC Qty Rate Amount", "Item HSN Qty Rate Amount")
    assert F.extract_bill(page(item)).hsn_sac.value == "998533"
    headless = BILL.replace("Description HSN/SAC Qty Rate Amount\n", "Billing period: 01-02-2026 to 28-02-2026\n")
    assert F.extract_bill(page(headless)).hsn_sac.value == "998533"
    nohsn = BILL.replace("Housekeeping services 998533 1 5,75,510.00 5,75,510.00", "Housekeeping services 1 5,75,510.00 5,75,510.00")
    assert F.extract_bill(page(nohsn)).hsn_sac.value is None            # 4471 in the bank line must not be taken


def test_buyers_gstin_is_read_with_its_own_confidence():
    b = F.extract_bill(page(BILL))
    assert b.recipient_gstin.value == "06AAACX4421K1ZQ" and 0 < b.recipient_gstin.conf <= 1
