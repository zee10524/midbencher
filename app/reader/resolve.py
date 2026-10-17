"""Use the vendor master to rescue a vendor GSTIN the page did not give cleanly, and say plainly where the value came from.

The check digit does not help here: none of the 900 GSTINs in this pack's vendor master passes the standard GSTIN check-digit rule (the pack's GSTINs are synthetic), so
a check-digit test would reject every true GSTIN. The vendor master is used as the validator instead:

1. repaired: the read text is one confusable character away (O and 0, I and 1, S and 5, B and 8), or has one extra character, from exactly one GSTIN in the master.
   The result is marked `repaired` and check P1/H1 turns it into a warning for a person to confirm. It is never marked `read`, because a vendor's own one-character
   mistake on the bill (the cause of the real `GSTIN does not match` queries) would look identical, so a repair must never hide it.
2. vendor_master: no GSTIN was read, but the vendor's name was read with confidence 0.90 or more and names exactly one vendor in the master. The GSTIN is looked up and
   marked `vendor_master`, never `read`; check P1/H1 does not run on it, because it says nothing about what the bill printed.

Real connection: the vendor master read over RFC, as in app/sap/adapter.py.
"""
from __future__ import annotations

import re

from .fields import AUTO, BillFields, F

PAIRS = {"O": "0", "0": "O", "I": "1", "1": "I", "S": "5", "5": "S", "B": "8", "8": "B"}
NAME_CONF = 0.90        # the vendor name must be read at least this well to look the vendor up by it
REPAIRED_CONF = 0.85    # a repaired GSTIN is a human-look item, not a clean read
LOOKED_UP_CONF = 0.90


def candidates(raw: str) -> set[str]:
    """Every 15-character string one confusable swap, or one deleted character, away from `raw` (and `raw` itself when it already has 15 characters)."""
    s = re.sub(r"[^A-Z0-9]", "", (raw or "").upper())
    out: set[str] = set()
    if len(s) == 15:
        out.add(s)
        for i, c in enumerate(s):
            if c in PAIRS:
                out.add(s[:i] + PAIRS[c] + s[i + 1:])
    elif len(s) == 16:
        for i in range(16):
            t = s[:i] + s[i + 1:]
            out.add(t)
            for j, c in enumerate(t):
                if c in PAIRS:
                    out.add(t[:j] + PAIRS[c] + t[j + 1:])
    return out


def repair_to_master(raw: str, index: dict[str, str]) -> str | None:
    """The one master GSTIN within a single swap or deletion of `raw`, or None if there is none or more than one."""
    hits = {c for c in candidates(raw) if c in index}
    return next(iter(hits)) if len(hits) == 1 else None


def resolve_vendor(b: BillFields, sap) -> None:
    """Fix up `b.vendor_gstin` in place when the page did not give a usable one. Does nothing when the GSTIN was read at 0.90 or more."""
    g = b.vendor_gstin
    if g.value is not None and g.conf >= AUTO:
        return
    index = sap.vendor_gstin_index()
    raw = g.value or g.raw
    if raw and (g.value is None or g.value not in index):
        fixed = repair_to_master(raw, index)
        if fixed:
            b.vendor_gstin = F(fixed, REPAIRED_CONF, f"read as '{raw}', one confusable or extra character away from exactly one GSTIN in the vendor master", source="repaired", raw=raw)
            return
    if (b.vendor_gstin.value is None or b.vendor_gstin.conf < 0.70) and b.vendor_name.value and b.vendor_name.conf >= NAME_CONF:
        hit = sap.get_vendor(name=b.vendor_name.value)
        if hit.status == "found":
            b.vendor_gstin = F(hit.vendor.gstin, min(LOOKED_UP_CONF, b.vendor_name.conf), "resolved from the vendor master by the vendor's name; not read from the bill", source="vendor_master", raw=raw)
