"""Turn an inbox file into clean page images for OCR.

Every PDF is treated as an image: the inbox PDFs carry no text layer (checked), so each page is rendered with PyMuPDF at about 300 dpi. A phone photo is
opened as it is. Each image is then cleaned: converted to grey, cropped to the page when the photo has a dark background, deskewed, contrast-stretched
and, if small, enlarged so that text is tall enough for Tesseract.

`pdf_text_layer(path)` is the fast path: pdfplumber returns text if a PDF does have a text layer, and the reader then skips OCR for that page. It is
expected to return nothing for the files in the pack.

Real connection: a desk scanner or the WhatsApp Business API media download would hand over the same files; the originals are kept untouched and these cleaned
images are working copies.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image, ImageFilter, ImageOps

RENDER_DPI = 300
MIN_HEIGHT = 2400          # enlarge photos smaller than this so that body text is about 20 px tall or more
MAX_SKEW_DEGREES = 8.0
PHOTO_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


@dataclass
class PageImage:
    page: int                 # 1-based
    image: Image.Image        # cleaned, ready for OCR
    skew_degrees: float       # rotation applied to straighten it
    cropped: bool             # a dark background was cut away


def pdf_text_layer(path: Path) -> list[str] | None:
    """Text of each page if the PDF has a text layer (fast path), else None. Needs more than a few characters on some page to count as a layer."""
    import pdfplumber

    try:
        with pdfplumber.open(path) as pdf:
            pages = [(p.extract_text() or "").strip() for p in pdf.pages]
    except Exception:  # noqa: BLE001 - a broken PDF has no usable layer; the image path still works
        return None
    return pages if any(len(t) > 20 for t in pages) else None


def render_pdf(path: Path, dpi: int = RENDER_DPI) -> list[Image.Image]:
    """Render every page of a PDF to an RGB image at `dpi`."""
    out = []
    with pymupdf.open(path) as doc:
        for page in doc:
            pix = page.get_pixmap(dpi=dpi, alpha=False)
            out.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
    return out


def load_raw(path: Path) -> list[Image.Image]:
    """The raw page images of a file: rendered pages for a PDF, the single image for a photo (rotated upright if the camera recorded an orientation)."""
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        return render_pdf(path)
    if path.suffix.lower() in PHOTO_SUFFIXES:
        return [ImageOps.exif_transpose(Image.open(path)).convert("RGB")]
    raise ValueError(f"unsupported file type: {path.suffix}")


def _otsu(grey: np.ndarray) -> int:
    hist = np.bincount(grey.ravel(), minlength=256).astype(float)
    total, sum_all = hist.sum(), (np.arange(256) * hist).sum()
    w0 = s0 = best = 0.0
    thr = 127
    for t in range(256):
        w0 += hist[t]
        if w0 == 0 or w0 == total:
            continue
        s0 += t * hist[t]
        m0, m1 = s0 / w0, (sum_all - s0) / (total - w0)
        var = w0 * (total - w0) * (m0 - m1) ** 2
        if var > best:
            best, thr = var, t
    return thr


def crop_to_page(grey: Image.Image) -> tuple[Image.Image, bool]:
    """If the picture is a page on a dark background, cut it to the bright page. A scan with a white margin is left alone."""
    a = np.asarray(grey)
    edge = np.concatenate([a[:8].ravel(), a[-8:].ravel(), a[:, :8].ravel(), a[:, -8:].ravel()])
    if edge.mean() > 150:
        return grey, False
    small = grey.resize((max(1, grey.width // 4), max(1, grey.height // 4)))
    s = np.asarray(small)
    mask = s > _otsu(s)
    rows, cols = mask.mean(axis=1) > 0.25, mask.mean(axis=0) > 0.25
    if rows.sum() < 10 or cols.sum() < 10:
        return grey, False
    y0, y1 = np.where(rows)[0][[0, -1]]
    x0, x1 = np.where(cols)[0][[0, -1]]
    box = (int(x0 * 4), int(y0 * 4), int((x1 + 1) * 4), int((y1 + 1) * 4))
    if (box[2] - box[0]) < grey.width * 0.4 or (box[3] - box[1]) < grey.height * 0.4:
        return grey, False
    return grey.crop(box), True


def estimate_skew(grey: Image.Image) -> float:
    """Skew angle in degrees (positive = the page is turned counter-clockwise, so text runs uphill to the right), by maximising the variance of the row profile of dark pixels."""
    w = 900
    small = grey.resize((w, max(1, int(grey.height * w / grey.width))))
    a = np.asarray(small)
    dark = Image.fromarray(((a < _otsu(a)) * 255).astype(np.uint8))

    def score(angle: float) -> float:
        rot = dark.rotate(angle, resample=Image.BILINEAR, fillcolor=0)
        return float(np.var(np.asarray(rot).mean(axis=1)))

    coarse = max(np.arange(-MAX_SKEW_DEGREES, MAX_SKEW_DEGREES + 0.01, 0.5), key=score)
    fine = max(np.arange(coarse - 0.5, coarse + 0.51, 0.1), key=score)
    return float(round(-fine, 2))


def clean(img: Image.Image) -> tuple[Image.Image, float, bool]:
    """Grey, crop to the page, deskew, stretch contrast, enlarge if small. Returns the image, the skew corrected and whether a background was cropped."""
    grey = ImageOps.grayscale(img)
    grey, cropped = crop_to_page(grey)
    angle = estimate_skew(grey)
    if abs(angle) >= 0.2:
        grey = grey.rotate(-angle, resample=Image.BICUBIC, expand=True, fillcolor=255)
    grey = ImageOps.autocontrast(grey, cutoff=1)
    if grey.height < MIN_HEIGHT:
        k = MIN_HEIGHT / grey.height
        grey = grey.resize((int(grey.width * k), MIN_HEIGHT), Image.LANCZOS)
    grey = grey.filter(ImageFilter.UnsharpMask(radius=2, percent=80, threshold=3))
    return grey, angle, cropped


def page_images(path: Path) -> list[PageImage]:
    """Cleaned page images of an inbox file, in page order."""
    out = []
    for i, raw in enumerate(load_raw(Path(path)), 1):
        img, angle, cropped = clean(raw)
        out.append(PageImage(i, img, angle, cropped))
    return out
