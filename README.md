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

### 1. Set up: about 5 minutes (downloads the packages; needs the internet once)

```
git clone <the repository URL> riklr-ai
cd riklr-ai
py -3.11 tasks.py setup          # Windows
python3.11 tasks.py setup        # Linux       (or: make setup)
```

Creates `.venv` and installs the pinned versions in `constraints.txt`. Expected last lines: `Tesseract found: the live reader will be available.` (or the note that it is not found, which is fine) and `Setup done.`

### 2. Analyse: about 2.5 minutes

```
python tasks.py analyse          # or: make analyse
```

Runs the numbered scripts in `analysis/`, then refreshes `notes/numbers.md`. Expected: one line per script (`== clean.py`, `== 01_profile.py` and so on up to `== 18_reader_comparison.py`) and, last, `registered 2250 figures in .../notes/numbers.md` (the figure count grows as figures are added). It also rewrites the files in `analysis/out/`, `backtest/out/` and `notes/` that the app and the tests read; they are already in the repository, so the result should match what you cloned.

### 3. Test: about 1.5 minutes

```
python tasks.py test             # or: make test
```

Expected last line: `218 passed` (the number grows as tests are added; there must be no failures). Tests that need Tesseract are skipped if it is not installed.

### 4. Run

```
python tasks.py run              # or: make run
```

Expected: `Riklr intake is running at http://127.0.0.1:8765/  (Ctrl+C to stop)` and a line saying whether Tesseract was found. Open that address. On the intake card pick a sample bill; the vendor message appears in a phone-style panel (English or Hindi), and **Vendor replies with a photo** answers it. The server answers within a second or two; the register (11,000 bills) loads in the background for about two seconds, so the first Control tower or Impact request may wait that long. Stop with Ctrl+C. Change the port with the `RIKLR_PORT` environment variable. `python tasks.py run --open` also opens the browser.


### Optional: fill the second reader's cache (needs a Gemini key and the internet; the app and the tests do not need it)

The app can show a second, vision-model reading next to Tesseract's and mark each field *two readers agree* or *needs human review*. It runs from stored responses in `data/cache/vision/`, so it needs no key and no network. That folder is empty until someone with a key fills it:

```
copy .env.example .env           # Windows   (cp .env.example .env on Linux)
# put your key after GEMINI_API_KEY= in .env  (.env is git-ignored, and the key is never printed or logged)
.venv\Scripts\python -m app.reader.vision --all     # Linux: .venv/bin/python -m app.reader.vision --all
.venv\Scripts\python -I analysis/18_reader_comparison.py   # scores both readers on the 10 labelled bills, writes notes/reader-comparison.md
```

This sends each bill image to Google (about 40 calls, paused between calls for free-tier limits). The pack is synthetic; real vendor bills would need a paid no-training tier or an in-house model (see `notes/reader-comparison.md`). Until it is run, `notes/reader-comparison.md` says the vision reader has not been scored.

## What is simulated

| Part | What it is here | What a real connection needs |
|---|---|---|
| **SAP** | A local SQLite file, `pack/data/sap_extract.sqlite`, opened read-only. `parsed_bill` is written only in a working copy under `app/data/` (git-ignored); the case pack is never edited | RFC read access (approved); writing invoices into SAP is a separate project with the SAP partner and audit sign-off, and the product never posts |
| **WhatsApp** | A phone-style chat on the intake card, labelled "Simulated: nothing is sent". The drafted message shows in English or Hindi (the Hindi is a draft for a Hindi speaker to review). "Vendor replies with a photo" reads a chosen photo (the stored reading, or Tesseract if installed), re-runs the checks, and posts the result and the bill status sentence from the tracker back to the thread. Other tasks stay in an on-screen outbox | A WhatsApp Business API account on a company number, approved templates in each language, the vendor's recorded opt-in, incoming photos by webhook, files stored on the company side |
| **Treasury payment runs** | Modelled from history: payments go out on Tuesdays and Fridays in the register, and the cut-off is a setting (0, 1 or 2 days) because the real rule is unconfirmed (`notes/payment-lag.md`) | Treasury's run lists, approval times and written cut-off |
| **The reader** | Tesseract on page images (PDFs rendered at 300 dpi), with every field carrying a confidence. A stored reading is used unless you press "Run live reader" | A scanner or phone app feeding the same pipeline; accuracy measured on the client's own bills |
| **The second reader** | A Gemini vision model, off by default, used only from stored responses in `data/cache/vision/` (empty until filled with a key). It extracts the same fields and never decides pass or fail; where it differs from Tesseract a person decides | A paid no-training tier or an in-house model for real bills; a larger labelled set to measure whether it helps |
| **The backtest** | Last year's register replayed with each lever; a counterfactual, not a result | A pilot on a few properties, compared with the others from the event log |

## Layout

| Path | Purpose |
|---|---|
| `pack/` | Untouched copy of `vendor-payments/` from the case pack. Never edited. |
| `analysis/` | Analysis scripts (numbered, run in order by `analyse`). `analysis/gold_labels.csv` is the hand-labelled sheet: only the two evaluation scripts (`15_reader_evaluation.py`, `18_reader_comparison.py`) read it; no app code does. |
| `notes/` | Working notes. `notes/numbers.md` is the register of every figure. `notes/progress.md` is a one-line log of the latest work. |
| `app/{reader,rules,sap,tracker,ui}` and `app/intake.py` | The application: reader (Tesseract, the optional vision reader and the cross-check), intake checks, SAP adapter, ledger and lists, the three screens and the simulated WhatsApp thread (`app/ui/chat.py`). |
| `data/cache/vision/`, `.env.example` | Stored vision readings (empty until filled) and the blank key template. `.env` is git-ignored. |
| `backtest/` | The lever replay (`replay.py`) and its outputs (`backtest/out/`). |
| `tests/` | The test suite (`python tasks.py test`). |
| `tasks.py`, `Makefile`, `constraints.txt` | Setup, analysis, test and run; the pinned dependency versions. |
| `deck/`, `video/`, `chat-history/` | Presentation, walkthrough video, exported AI chat history. |
