"""Write every figure in the analysis/out/figures*.csv files into notes/numbers.md, with the script and the exact command that produced it.

Each source gets its own block between marker lines; the rule and any hand-added rows are kept.
Run after the analysis scripts:  python -I analysis/register_numbers.py   (python tasks.py analyse does all of it)
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
NUM = ROOT / "notes" / "numbers.md"
PY = "python -I"

# (script, figures file, scripts it needs first, where the figures are used)
SOURCES = [
    ("clean.py", "figures.csv", [], "notes/data-audit.md"),
    ("02_stage_times.py", "figures_stage_times.csv", ["clean.py"],
     "stage_times.csv, policy_compliance.csv, stage_times_chart.png. Every row of stage_times.csv and "
     "policy_compliance.csv is also a figure: same script, same command"),
    ("04_query_forensics.py", "figures_query_forensics.csv", ["clean.py", "02_stage_times.py"],
     "notes/query-forensics.md, query_forensics.csv. Every row of query_forensics.csv, query_forensics_summary.csv and "
     "query_rules.csv is also a figure: same script, same command"),
    ("06_msme_exposure.py", "figures_msme.csv", ["clean.py"],
     "notes/msme-exposure.md, notes/research.md, notes/assumptions.md. Every row of msme_exposure.csv and msme_open_bills.csv is also a figure: same script, same command"),
    ("05_claims_tested.py", "figures_claims_tested.csv", ["clean.py", "02_stage_times.py", "04_query_forensics.py", "06_msme_exposure.py"],
     "notes/claims-tested.md, claims_tested.csv. The other numbers in claims-tested.md are read from the figure ids "
     "named in claims_tested.csv (clean.py, 02_stage_times.py, 04_query_forensics.py and 06_msme_exposure.py)"),
    ("07_workflow_map.py", "figures_workflows.csv", ["clean.py", "02_stage_times.py", "04_query_forensics.py", "06_msme_exposure.py", "05_claims_tested.py"],
     "notes/workflows.md and notes/workflows/swimlane.mmd. The other numbers in workflows.md are read by figure id from the other scripts' figures files"),
    ("08_problem_ranking.py", "figures_problem.csv", ["clean.py", "02_stage_times.py", "04_query_forensics.py", "06_msme_exposure.py", "05_claims_tested.py"],
     "notes/problem.md. The other numbers in problem.md are read by figure id from the other scripts' figures files"),
    ("09_levers.py", "figures_levers.csv", ["clean.py", "02_stage_times.py", "04_query_forensics.py", "06_msme_exposure.py", "05_claims_tested.py", "08_problem_ranking.py"],
     "notes/payment-lag.md and notes/solution-design.md (part f). The replay is backtest/replay.py, called by this script; every value in backtest/out/impact.csv and confusion.csv is one of these figures (l.lever.*, l.base.*, l.cf.*, l.impact.*, l.assume.*, l.live.*): same script, same command. Every row of levers.csv, lag_factors.csv, lag_first_run.csv and backtest_rules.csv is also a figure: same script, same command"),
    ("09_options.py", "figures_options.csv", ["clean.py", "02_stage_times.py", "04_query_forensics.py", "06_msme_exposure.py", "05_claims_tested.py", "08_problem_ranking.py"],
     "notes/options.md. Build hours are my estimates and the time budget is an assumption, both stated in the note; the other numbers are read by figure id from the other scripts' figures files"),
    ("10_solution_design.py", "figures_design.csv", ["clean.py", "02_stage_times.py", "04_query_forensics.py", "06_msme_exposure.py", "05_claims_tested.py", "08_problem_ranking.py", "09_levers.py", "09_options.py"],
     "notes/solution-design.md. The check classes and build hours are my judgement and estimates, stated in the note; four inbox bills were read by eye"),
    ("11_pick_balance.py", "figures_pickbalance.csv", [],
     "notes/assumptions.md ('Tracker: judgement calls', verifier load). Reads pack/data and runs app/tracker; every row of pick_balance.csv is also a figure: same script, same command"),
    ("12_loose_duplicates.py", "figures_loose.csv", ["clean.py", "02_stage_times.py", "04_query_forensics.py"],
     "notes/assumptions.md and the docstring of check H13 in app/rules/checks.py. What loose duplicate matching adds on the register; the backtest and impact figures use exact matching only"),
    ("13_duplicate_false_alarms.py", "figures_dupalarm.csv", ["clean.py", "02_stage_times.py", "04_query_forensics.py"],
     "notes/duplicate-false-alarms.md. Loose near-duplicate matching run on every posted invoice in the SAP extract"),
    ("14_reader_results.py", "figures_reader.csv", [],
     "app/reader/ (reader summary). What the reader did with the 40 inbox files; reads app/reader/cache/*.json (written by `python -m app.reader`); no label file is read"),
    ("15_reader_evaluation.py", "figures_reader_eval.csv", [],
     "notes/reader-evaluation.md. FIRST-RUN score of the reader against the 10 hand-labelled bills (analysis/gold_labels.csv, read only), from the frozen analysis/reader_first_run.json"),
    ("16_intake_run.py", "figures_intake.csv", ["clean.py", "02_stage_times.py", "04_query_forensics.py"],
     "notes/intake-run.md. All 40 inbox bills through the reader results, the checks, the routing and parsed_bill"),
    ("17_runway_90d.py", "figures_runway.csv", ["clean.py"],
     "app/ui (control tower headline and list of work orders likely to run dry), backtest/out/runway_90d.csv. Burn from the last 90 days of billing; the lifetime-average figure is kept for comparison"),
    ("18_reader_comparison.py", "figures_comparison.csv", [],
     "notes/reader-comparison.md. Tesseract alone, the stored vision reading alone and the two together on the 10 hand-labelled bills (analysis/gold_labels.csv, read only by this script and by 15_reader_evaluation.py); the vision figures exist only once data/cache/vision holds the readings"),
]

# the evaluation script is frozen and writes the platform line ending; keep the repository on LF
for _p in (ROOT / "analysis" / "out").glob("figures_reader_eval.csv"):
    _p.write_bytes(_p.read_bytes().replace(b"\r\n", b"\n"))

text = NUM.read_text(encoding="utf-8")
total = 0
for script, fname, needs, used in SOURCES:
    begin, end = f"<!-- BEGIN {script} -->", f"<!-- END {script} -->"
    f = pd.read_csv(ROOT / "analysis" / "out" / fname, keep_default_na=False)
    rows = [f"| {r.id} | {r.value} | {r.description} |" for r in f.itertuples()]
    total += len(rows)
    chain = [f"{PY} analysis/{n}" for n in [*needs, script]]
    block = "\n".join([
        begin, "",
        f"### Figures from `analysis/{script}` (used in {used})", "",
        f"Script: `analysis/{script}`. Output: `analysis/out/{fname}`, one row per figure id below. "
        "Run from the project root. Exact commands to reproduce, in order:", "",
        "```", *chain, "```", "",
        "Run from the project root with the project's virtual environment active (`.venv`). `python tasks.py analyse` (or `make analyse`) runs the whole chain and refreshes this register (`python tasks.py setup` first on a new machine).", "",
        "| Figure id | Value | What it counts |", "|---|---|---|", *rows, "", end,
    ])
    if begin in text:
        head, rest = text.split(begin, 1)
        text = head + block + rest.split(end, 1)[1]
    else:
        text = text.rstrip("\n") + "\n\n" + block + "\n"
NUM.write_text(text, encoding="utf-8", newline="\n")
print(f"registered {total} figures in {NUM}")
