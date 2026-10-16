"""Run every numbered analysis script (NN_*.py) in this folder, in order."""
import subprocess
import sys
from pathlib import Path

here = Path(__file__).parent
scripts = sorted(here.glob("[0-9][0-9]_*.py"))
if not scripts:
    print("No analysis scripts yet.")
for script in scripts:
    print(f"== {script.name}")
    subprocess.run([sys.executable, str(script)], check=True)
