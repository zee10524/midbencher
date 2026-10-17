"""Read every file in the bill inbox: `python -m app.reader [--refresh]`.

Writes one JSON per file to app/reader/cache/ and one row per file to `parsed_bill` in a fresh working copy of the SAP stand-in (app/data/sap_working.sqlite).
Needs Tesseract unless every file is already cached.
"""
import sys

from .pipeline import WORKING_DB, run_all, summary

if __name__ == "__main__":
    results = run_all(refresh="--refresh" in sys.argv)
    for key, d in summary(results).items():
        print(f"{key:<12} files {d['files']:>3}  ok {d['ok']:>3}  review {d['review']:>3}  (human look {d['human_look']}, resend {d['resend']})")
    print(f"parsed_bill rows written to {WORKING_DB}")
