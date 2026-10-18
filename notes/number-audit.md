# Number audit (4.3)

What was checked, how, and what it found. Nothing here is a new analysis result.

## 1. Does every registered figure reproduce?

Every analysis script was re-run from a clean state with `python tasks.py analyse` (all numbered scripts, then `analysis/register_numbers.py`). **The re-run changed no file**: every figures file in `analysis/out/`, every output in `backtest/out/`, every generated note and `notes/numbers.md` came out byte for byte as committed. So each registered figure **matches** the script and command recorded beside it. (Six figures were added afterwards, see section 3; the total is now 2,250.)

## 2. Does every figure written in the text have a source?

`python -I analysis/audit_numbers.py` reads each number in `README.md` and `notes/*.md` and looks it up in `notes/numbers.md` (as written, as a percentage, or in lakh or crore). Dates, ids and small whole numbers are skipped. The UI is not scanned this way: its figures are produced by `app/ui/data.py` from `notes/numbers.md`, `backtest/out/*` or the register, and `tests/test_ui.py` fails if a digit is typed into the page or script. **No deck outline exists** (`deck/` is empty), so none was checked.

Of the figures in the text, 145 had no entry in `notes/numbers.md`. Read one by one:

| What they are | Count | Source | Verdict |
|---|---|---|---|
| Rows of a table copied from an output file: the loose-duplicate pairs, the open Micro and Small bills, the per-bill intake verdicts, the query-day tables by category and month, the payment-lag factor table | 43 + 25 + 18 + 24 + 4 = 114 | `analysis/out/*.csv` and the script named in each note (`13_duplicate_false_alarms.py`, `06_msme_exposure.py`, `16_intake_run.py`, query forensics, `09_levers.py`) | **Match**: the files were regenerated unchanged. Not in `numbers.md` because they are rows, not headline figures |
| Rupee amounts and work-order ids quoted from four inbox bills | 12 + 10 = 22 | the bill image and `analysis/10_solution_design.py` (the four bills read by eye) | **Matches the page**; hand-read, as the note says |
| Numbers inside references: a section of a law, a case id | 6 | external sources in `notes/research.md` | Not data |
| Test counts in the progress log | 3 | what the test run said on that day | A log, not a figure |

**Figures that had no source and were fixed.** Two sums printed in `notes/problem.md` (10.59 and 12.89 days, the ceilings for the central AP lead and for the property heads) and four derived values in `notes/solution-design.md` (the after-means 24.9 to 27.3 and 31.3 to 33.7) were computed in the script but had no id. They are now registered: `p.owner.ap_lead.ceiling`, `p.owner.property.ceiling`, `d.after.desk_mean_low`, `d.after.desk_mean_high`, `d.after.inv_mean_low`, `d.after.inv_mean_high`. The values did not change.

**Stale numbers fixed.** The README's expected output (`registered … figures`, `… passed`) was out of date and now matches a clean run.

## 3. Two numbers that look like one

The Tesseract first-run score is **52 of 60 fields** on the labels as first given (`re.first.all.fields_correct`) and **53 of 60** on the labels after the bill-28 amount was corrected (`rc.tess_first.fields_correct`). Both are first-run readings; only the label changed. Bills right on the four key fields are 5 of 10 either way. The comparison note uses the corrected labels and says so.

## 4. Claims rewritten to what the data supports

- `notes/reader-comparison.md` now says the vision reader's 60 of 60 on ten bills is not evidence that it is always right (95% upper bound on its error rate about `rc.vision.error_upper95_pct` per cent, one reading, labels typed by one person, same image seen by both readers). The tuned Tesseract result is named as not a fair comparison and not a headline; it never appears in the app, the README or a summary line. Nothing in the text says the vision reader is 100% accurate.
- `notes/query-forensics.md` said "What the data proves" and "Proven total"; it now says "shows" and "confirmed in the extract", with a sentence that it is a count of matches, not a promise for new bills.
- The app's reading label already says ten bills is a small sample and a hint, not a guarantee. The control-tower "likely to run dry" headline now shows how far it moves with the burn window.
- Cross-check wording: agreement of two readers that saw the same image is not proof.

## 5. Is any bill counted twice? Are the dates consistent?

`tests/test_numbers.py` checks, from the cleaned register alone:

- 11,000 bills, each `bill_id` once, and no invoice (same vendor, number, date and amount) under two ids.
- The headline figures are **re-derived a second way** and match: mean days from the desk to paid, paid invoices over 45 days, the known Micro and Small paid invoices, and how many of them are over 45 (`l.base.desk_mean`, `l.base.over45`, `l.n_msme_known`, `l.base.ms_late`).
- The after-means are exactly the registered before minus the registered saving.
- The 40 inbox bills: the intake verdicts add up to 40, and no register bill is claimed by two inbox bills.
- One definition of **late**: more than 45 days from the **desk-received date** (46 or more), in the tracker (`days_remaining` below zero), in every analysis script and in the replay; no script counts day 45 as late. Elsewhere the note `notes/assumptions.md` explains the two other clocks (the property-verified date as a floor, the invoice date as an upper bracket) and why the desk date is primary. "Days from the invoice date" is always labelled as such (`l.base.inv_mean`).
- The credit notes are in the register (261 of the 11,000) and are excluded from the paid-invoice populations (doc type invoice) in the days figures; the tracker handles them separately.

## 6. What this audit cannot say

It shows that every number can be traced to a script and reproduces, and that headline figures agree with an independent recount. It does not show that the data are right (the register is the client's export, with known issues in `notes/data-audit.md`), or that the scenario assumptions behind the days saved hold (`notes/assumptions.md`, Known limits).
