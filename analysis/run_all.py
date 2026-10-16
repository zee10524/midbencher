"""Run the analysis in dependency order, then the numbers register.

clean.py makes bills_clean.parquet; 02 makes stage_times.csv, which 04 reads; 04 makes the query forensics, which 05 reads;
06_msme_exposure.py reads only bills_clean.parquet but 05 reads its figures, so it runs before 05.
Any numbered script not listed here runs after the listed ones, in name order.
"""
import subprocess
import sys
from pathlib import Path

here = Path(__file__).parent
ORDER = ["clean.py", "01_profile.py", "02_stage_times.py", "03_stage_chart.py", "04_query_forensics.py", "06_msme_exposure.py", "05_claims_tested.py"]
listed = [here / n for n in ORDER]
extra = [p for p in sorted(here.glob("[0-9][0-9]_*.py")) if p not in listed]
for script in [*listed, *extra, here / "register_numbers.py"]:
    print(f"== {script.name}")
    subprocess.run([sys.executable, "-I", str(script)], check=True)
