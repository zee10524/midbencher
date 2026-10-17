# Riklr AI FDE case study: vendor-payments

Vendor bills arrive on paper, as scans and as phone photos, and take a mean of about 31 days from the desk to payment. This project reads a bill when it arrives, checks it against SAP data, tells the right person the one fix that matters, and tracks every bill to payment. It has three screens: **Intake** (drop a bill, get a verdict and a message ready to send), **Control tower** (the oldest bills, Micro and Small bills close to the 45-day limit, the pick order across the AP clerks, work orders about to run dry) and **Impact** (a backtest on last year's register, as ranges, with the condition beside each).

The thinking behind it is in `notes/`: `notes/understanding.md`, `notes/problem.md`, `notes/options.md`, `notes/solution-design.md`, and the reader's scores in `notes/reader-evaluation.md`. Every figure used anywhere is listed in `notes/numbers.md` with the script and command that produced it.

## What you need

| Need | Windows | Linux |
|---|---|---|
| Python **3.11** (exactly; the dependencies are pinned for it) | python.org installer, or `py -3.11` | `python3.11` (`apt install python3.11 python3.11-venv`) |
| Git | git-scm.com | `apt install git` |
| **Tesseract OCR** (only to read *new* bills; without it the app runs on the stored readings, marked "reader simulated") | UB Mannheim installer: https://github.com/UB-Mannheim/tesseract/wiki, tick "add to PATH" (or add `C:\Program Files\Tesseract-OCR` to PATH yourself), then open a new terminal | `sudo apt install tesseract-ocr` |
| PyMuPDF | nothing to install: `pip` installs it in step 1 | same |
| `make` (optional) | not installed by default: use `python tasks.py ...` below (`mingw32-make` also works) | usually present |

Check Tesseract with `tesseract --version`. Nothing else is needed from outside the repository: the case pack (`pack/`, including the SAP extract and the bill inbox), the stored readings (`app/reader/cache/`) and the figure register are all in the repository. There is no API key and the app makes no network call.

## Run it, in order

Every step works two ways: `python tasks.py <step>` (plain Python, same on both systems, nothing to install first) or `make <step>`. Run from the project root. Times are from a clean clone on a Windows laptop; Linux is similar.

### 1. Set up: about N (needs the internet once)

```
git clone <the repository URL> riklr-ai
cd riklr-ai
py -3.11 tasks.py setup          # Windows
python3.11 tasks.py setup        # Linux       (or: make setup)
```

Creates `.venv` and installs the pinned versions in `constraints.txt`. Expected last lines: `Tesseract found: the live reader will be available.` (or the note that it is not found, which is fine) and `Setup done.`

### 2. Analyse: about N

```
python tasks.py analyse          # or: make analyse
```

Runs the numbered scripts in `analysis/`, then refreshes `notes/numbers.md`. Expected: one line per script (`== clean.py`, `== 01_profile.py` and so on up to `== 17_runway_90d.py`) and, last, `registered N figures in .../notes/numbers.md`. It also rewrites the files in `analysis/out/`, `backtest/out/` and `notes/` that the app and the tests read; they are already in the repository, so the result should match what you cloned.

### 3. Test: about N

```
python tasks.py test             # or: make test
```

Expected last line: `N passed`. Tests that need Tesseract are skipped if it is not installed.

### 4. Run

```
python tasks.py run              # or: make run
```

Expected: `Riklr intake is running at http://127.0.0.1:8765/  (Ctrl+C to stop)` and a line saying whether Tesseract was found. Open that address. The register loads in about N when the server starts, so the first screen may take that long. Stop with Ctrl+C. Change the port with the `RIKLR_PORT` environment variable. `python tasks.py run --open` also opens the browser.


## What is simulated

| Part | What it is here | What a real connection needs |
|---|---|---|
| **SAP** | A local SQLite file, `pack/data/sap_extract.sqlite`, opened read-only. `parsed_bill` is written only in a working copy under `app/data/` (git-ignored); the case pack is never edited | RFC read access (approved); writing invoices into SAP is a separate project with the SAP partner and audit sign-off, and the product never posts |
| **WhatsApp** | An on-screen outbox on the intake card. Messages are composed and shown; nothing is sent | A WhatsApp Business API account on a company number, approved templates, the vendor's recorded opt-in, files stored on the company side |
| **Treasury payment runs** | Modelled from history: payments go out on Tuesdays and Fridays in the register, and the cut-off is a setting (0, 1 or 2 days) because the real rule is unconfirmed (`notes/payment-lag.md`) | Treasury's run lists, approval times and written cut-off |
| **The reader** | Tesseract on page images (PDFs rendered at 300 dpi), with every field carrying a confidence. A stored reading is used unless you press "Run live reader" | A scanner or phone app feeding the same pipeline; accuracy measured on the client's own bills |
| **The backtest** | Last year's register replayed with each lever; a counterfactual, not a result | A pilot on a few properties, compared with the others from the event log |

## Layout

| Path | Purpose |
|---|---|
| `pack/` | Untouched copy of `vendor-payments/` from the case pack. Never edited. |
| `analysis/` | Analysis scripts (numbered, run in order by `analyse`). `analysis/gold_labels.csv` is the hand-labelled sheet: only the evaluation script reads it; no app code does. |
| `notes/` | Working notes. `notes/numbers.md` is the register of every figure. `notes/progress.md` is a one-line log of the latest work. |
| `app/{reader,rules,sap,tracker,ui}` and `app/intake.py` | The application: reader, intake checks, SAP adapter, ledger and lists, the three screens. |
| `backtest/` | The lever replay (`replay.py`) and its outputs (`backtest/out/`). |
| `tests/` | The test suite (`python tasks.py test`). |
| `tasks.py`, `Makefile`, `constraints.txt` | Setup, analysis, test and run; the pinned dependency versions. |
| `deck/`, `video/`, `chat-history/` | Presentation, walkthrough video, exported AI chat history. |
