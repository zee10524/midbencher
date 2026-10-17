"""The reader: turns the files in the bill inbox into `parsed_bill` fields, each with a confidence, and caches the result so the app runs without Tesseract.

    from app.reader import read_file, run_all, summary
"""
from .pipeline import CACHE_DIR, READER_VERSION, VISION_FALLBACK, parsed_bill_args, read_file, run_all, summary

__all__ = ["CACHE_DIR", "READER_VERSION", "VISION_FALLBACK", "parsed_bill_args", "read_file", "run_all", "summary"]
