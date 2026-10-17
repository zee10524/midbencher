"""Tesseract OCR on a cleaned page image, with a confidence for every word.

`tesseract_available()` says whether the program can be run. If it cannot, the reader does not guess: it uses the cached results (see pipeline.py) and marks them
`reader simulated`.

Real connection: this module is the only place that calls Tesseract. No network call is made here, and the vision-model fallback is separate and off.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field

import pytesseract
from PIL import Image

PSM = 6          # a single uniform block of text: bills are tables and labelled lines
OEM = 3
LANG = "eng"


@dataclass
class Word:
    text: str
    conf: float      # 0 to 1
    line: int        # line number on the page
    left: int
    top: int
    width: int
    height: int


@dataclass
class OcrPage:
    words: list[Word] = field(default_factory=list)
    image: Image.Image | None = field(default=None, repr=False)   # the cleaned page, kept so that a single word can be read a second time
    header: "OcrPage | None" = field(default=None, repr=False)    # the top of the page read again on its own, enlarged

    @property
    def lines(self) -> list[list[Word]]:
        out: dict[int, list[Word]] = {}
        for w in self.words:
            out.setdefault(w.line, []).append(w)
        return [sorted(ws, key=lambda w: w.left) for _, ws in sorted(out.items())]

    @property
    def text(self) -> str:
        return "\n".join(" ".join(w.text for w in ln) for ln in self.lines)


def tesseract_available() -> bool:
    if shutil.which("tesseract") is None:
        return False
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:  # noqa: BLE001
        return False


def ocr_page(img: Image.Image, psm: int = PSM) -> OcrPage:
    """Run Tesseract and return words with confidences. Words Tesseract could not score (conf -1) and blanks are dropped."""
    d = pytesseract.image_to_data(img, lang=LANG, config=f"--oem {OEM} --psm {psm}", output_type=pytesseract.Output.DICT)
    words, line_key, line_no = [], None, -1
    for i, t in enumerate(d["text"]):
        key = (d["block_num"][i], d["par_num"][i], d["line_num"][i])
        if key != line_key:
            line_key, line_no = key, line_no + 1
        t = (t or "").strip()
        conf = float(d["conf"][i])
        if not t or conf < 0:
            continue
        words.append(Word(t, conf / 100.0, line_no, d["left"][i], d["top"][i], d["width"][i], d["height"][i]))
    return OcrPage(words, img)


def ocr_header(page: OcrPage, zoom: float = 1.6) -> OcrPage | None:
    """Read the header of the page again on its own: from the top down to the line after `Bill to` (the supplier block, GSTIN, invoice number and date), enlarged. The header is
    the part of a bill that holds the vendor and the invoice number, so a second, closer read of it is worth the extra second. Returns None if the page image was not kept."""
    if page.image is None:
        return None
    bill = [i for i, ln in enumerate(page.lines) if ln and ln[0].text.lower().startswith(("bill", "bil", "b1l"))]
    if bill:
        lines = page.lines
        nxt = lines[min(bill[0] + 1, len(lines) - 1)]
        bottom = max(w.top + w.height for w in nxt) + 30
    else:
        bottom = int(page.image.height * 0.40)
    crop = page.image.crop((0, 0, page.image.width, min(page.image.height, bottom)))
    crop = crop.resize((int(crop.width * zoom), int(crop.height * zoom)), Image.LANCZOS)
    out = ocr_page(crop)
    return out


def text_page(text: str) -> OcrPage:
    """An OcrPage from plain text (the pdfplumber fast path): every word has confidence 1.0, because the text is exact."""
    words = [Word(w, 1.0, n, i * 10, n * 10, 10, 10) for n, ln in enumerate(text.splitlines()) for i, w in enumerate(ln.split())]
    return OcrPage(words)


def reread(page: OcrPage, word: Word, whitelist: str, pad: int = 14, zoom: int = 2) -> tuple[str, float] | None:
    """Read one word a second time: crop it from the page, enlarge it and let Tesseract choose only from `whitelist` (for example digits and capital letters).
    Two independent reads that agree are far stronger evidence than one. Returns (text, confidence), or None if the page image was not kept."""
    if page.image is None:
        return None
    box = (max(0, word.left - pad), max(0, word.top - pad), min(page.image.width, word.left + word.width + pad), min(page.image.height, word.top + word.height + pad))
    crop = page.image.crop(box)
    crop = crop.resize((crop.width * zoom, crop.height * zoom), Image.LANCZOS)
    framed = Image.new("L", (crop.width + 40, crop.height + 40), 255)
    framed.paste(crop, (20, 20))
    d = pytesseract.image_to_data(framed, lang=LANG, config=f"--oem {OEM} --psm 7 -c tessedit_char_whitelist={whitelist}", output_type=pytesseract.Output.DICT)
    parts = [(t.strip(), float(c) / 100.0) for t, c in zip(d["text"], d["conf"]) if t.strip() and float(c) >= 0]
    if not parts:
        return "", 0.0
    return "".join(t for t, _ in parts), min(c for _, c in parts)
