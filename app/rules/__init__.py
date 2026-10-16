"""Intake rules: the checks in the Saturday slice, each a pure function, and the routing of a bill from their results.

    from app.rules import read, Context, run_all, route
    results = run_all(read(vendor_gstin=..., invoice_no=..., ...), Context(sap, known_bills))
    routing = route(results)
"""
from .checks import CHECKS, run_all
from .model import AUTO_CLEAR, LOOK, RULES_VERSION, BillRead, CheckResult, Context, Field, read
from .routing import Action, Routing, route

__all__ = ["CHECKS", "run_all", "AUTO_CLEAR", "LOOK", "RULES_VERSION", "BillRead", "CheckResult", "Context", "Field", "read", "Action", "Routing", "route"]
