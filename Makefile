# Convenience wrappers over tasks.py, which does the work in plain Python and is the same on Windows and Linux.
# On Windows without GNU make you can run the same steps as `python tasks.py setup`, `analyse`, `test`, `run`.
# (mingw32-make also works with this file.)

ifeq ($(OS),Windows_NT)
  PYTHON ?= py -3.11
else
  PYTHON ?= python3.11
endif

.PHONY: setup analyse test run all

# Create .venv and install the pinned dependencies (constraints.txt).
setup:
	$(PYTHON) tasks.py setup

# Run the numbered scripts in analysis/ in order and refresh notes/numbers.md.
analyse:
	$(PYTHON) tasks.py analyse

test:
	$(PYTHON) tasks.py test

# Start the app at http://127.0.0.1:8765/
run:
	$(PYTHON) tasks.py run

all: setup analyse test
