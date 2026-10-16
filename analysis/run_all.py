"""Run the analysis in order: clean.py (makes bills_clean.parquet), the numbered scripts (NN_*.py), then the numbers register."""
import subprocess
import sys
from pathlib import Path

here = Path(__file__).parent
scripts = [here / "clean.py", *sorted(here.glob("[0-9][0-9]_*.py")), here / "register_numbers.py"]
for script in scripts:
    print(f"== {script.name}")
    subprocess.run([sys.executable, "-I", str(script)], check=True)
