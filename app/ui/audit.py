"""An append-only audit log of every human review: who typed what over what, and what the verdict became.

One JSON line per review in `app/data/audit_log.jsonl` (git-ignored, like the working copy of `parsed_bill`). Each line carries the SHA-256 of the previous line, so deleting or editing
an earlier line breaks the chain and `verify()` says where. This is evidence of order and of accidental change, not protection against someone who can rewrite the whole file: a
production system would write to a store the reviewer cannot edit (database with insert-only rights, or an append-only log service) and would take the reviewer from the login, not from a typed name.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

LOG = Path(__file__).resolve().parent.parent / "data" / "audit_log.jsonl"
GENESIS = "0" * 64


def _line_hash(line: str) -> str:
    return hashlib.sha256(line.encode("utf-8")).hexdigest()


def append(entry: dict, path: Path | None = None) -> dict:
    """Add one entry (a dict of plain values). Returns it with `at` (UTC), `prev` and `hash` filled in."""
    path = Path(path or LOG)
    path.parent.mkdir(parents=True, exist_ok=True)
    prev = GENESIS
    if path.exists():
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if lines:
            prev = _line_hash(lines[-1])
    rec = dict(entry, at=datetime.now(timezone.utc).isoformat(timespec="seconds"), prev=prev)
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
    return rec


def verify(path: Path | None = None) -> tuple[bool, int, str]:
    """(intact, entries, message). Checks that each line names the hash of the line before it."""
    path = Path(path or LOG)
    if not path.exists():
        return True, 0, "no log yet"
    prev, n = GENESIS, 0
    for i, ln in enumerate([x for x in path.read_text(encoding="utf-8").splitlines() if x.strip()], 1):
        if json.loads(ln).get("prev") != prev:
            return False, n, f"line {i} does not follow the line before it: the log was edited or a line was removed"
        prev, n = _line_hash(ln), i
    return True, n, "intact"
