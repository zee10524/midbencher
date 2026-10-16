# Riklr FDE case study: vendor-payments
# Works with GNU make (Linux/macOS/Git Bash) and mingw32-make (Windows).

ifeq ($(OS),Windows_NT)
  BOOTSTRAP ?= py -3.11
  VENV_PY   := .venv/Scripts/python.exe
else
  BOOTSTRAP ?= python3.11
  VENV_PY   := .venv/bin/python
endif

.PHONY: setup analyse test run

# Create the Python 3.11 virtualenv and install the project with dev extras.
setup:
	$(BOOTSTRAP) -m venv .venv
	"$(VENV_PY)" -m pip install --upgrade pip
	"$(VENV_PY)" -m pip install -e ".[dev]"

# Run the numbered scripts in analysis/ in order (none yet).
analyse:
	"$(VENV_PY)" analysis/run_all.py

test:
	"$(VENV_PY)" -m pytest

# Start the app (not built yet).
run:
	"$(VENV_PY)" -m app
