# Riklr AI FDE case study: vendor-payments

Stub. To be written once the analysis is done.

## Layout

| Path | Purpose |
|---|---|
| `pack/` | Untouched copy of `vendor-payments/` from the case pack. Never edited. |
| `analysis/` | Analysis scripts (numbered, run in order by `make analyse`). |
| `notes/` | Working notes. `notes/numbers.md` is the register of every figure. |
| `app/{reader,rules,sap,tracker,ui}` | The application. |
| `backtest/` | Backtest of the rules against the pack data. |
| `deck/` | Presentation. |
| `video/` | Walkthrough video. |
| `chat-history/` | Exported AI chat history. |

## System requirement

The reader needs the **Tesseract OCR program** installed and on your `PATH` (the Python package `pytesseract` only calls it). On Windows use the installer from UB Mannheim (https://github.com/UB-Mannheim/tesseract/wiki); on Linux run `apt install tesseract-ocr`. Check with `tesseract --version`. If Tesseract is not there, the app falls back to saved results for the labelled bills and marks the screen `reader simulated`.

## Commands

Requires Python 3.11. On Windows without `make`, use `mingw32-make`.

```
make setup     # create .venv, install deps
make analyse   # run analysis scripts
make test      # run tests
make run       # start the app
```
