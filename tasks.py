"""Project tasks with plain Python, the same on Windows and Linux. `make` is only a convenience over these.

    python tasks.py setup      create .venv and install the pinned dependencies (needs the internet once)
    python tasks.py analyse    run the analysis scripts in order and refresh notes/numbers.md
    python tasks.py test       run the test suite
    python tasks.py run        start the app at http://127.0.0.1:8765/   (add --open to open a browser)
    python tasks.py all        setup, analyse and test in one go

It uses only the standard library, so it runs before anything is installed. Python 3.11 is required.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def sh(*args: str | Path) -> None:
    print("+", " ".join(str(a) for a in args), flush=True)
    subprocess.run([str(a) for a in args], cwd=ROOT, check=True)


def setup() -> None:
    if sys.version_info[:2] != (3, 11):
        sys.exit(f"Python 3.11 is required; this is {sys.version_info.major}.{sys.version_info.minor}. Install 3.11 and run it with that (for example `py -3.11 tasks.py setup` on Windows or `python3.11 tasks.py setup`).")
    if not venv_python().exists():
        print("Creating .venv", flush=True)
        venv.EnvBuilder(with_pip=True, clear=False).create(VENV)
    sh(venv_python(), "-m", "pip", "install", "--quiet", "--upgrade", "pip")
    sh(venv_python(), "-m", "pip", "install", "--quiet", "-c", "constraints.txt", "-e", ".[dev]")
    if shutil.which("tesseract"):
        print("Tesseract found: the live reader will be available.")
    else:
        print("Tesseract NOT found on PATH. The app still runs on the stored readings (marked 'reader simulated'); install Tesseract to read new bills. See README, System requirement.")
    print("Setup done.")


def need_venv() -> None:
    if not venv_python().exists():
        sys.exit("No .venv yet: run `python tasks.py setup` first.")


def analyse() -> None:
    need_venv()
    sh(venv_python(), "analysis/run_all.py")


def test() -> None:
    need_venv()
    sh(venv_python(), "-m", "pytest")


def run(extra: list[str]) -> None:
    need_venv()
    sh(venv_python(), "-m", "app", *extra)


def main(argv: list[str]) -> None:
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd == "setup":
        setup()
    elif cmd == "analyse":
        analyse()
    elif cmd == "test":
        test()
    elif cmd == "run":
        run(argv[2:])
    elif cmd == "all":
        setup(); analyse(); test()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
