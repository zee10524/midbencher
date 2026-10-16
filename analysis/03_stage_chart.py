"""One chart: where the days go between invoice date and paid date (mean calendar days, stage by stage).

Reads analysis/out/stage_times.csv, analysis/out/policy_compliance.csv and figures_stage_times.csv.
Writes analysis/out/stage_times_chart.png. The data behind it is the 'overall' rows of stage_times.csv (table view).
Colours: dataviz reference palette slots 1 and 2 (blue = waiting, orange = worked), checked with validate_palette.py.

Run: python analysis/03_stage_chart.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "analysis" / "out"
SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
WAIT, WORK, TOTAL = "#2a78d6", "#eb6834", "#898781"
plt.rcParams["font.family"] = ["Segoe UI", "DejaVu Sans"]

t = pd.read_csv(OUT / "stage_times.csv")
ov = t[t.dimension == "overall"].set_index("stage_order")
fg = pd.read_csv(OUT / "figures_stage_times.csv").set_index("id").value
stages = ov.loc[1:8]
total = ov.loc[99]
worked, waiting = ov.loc[98], ov.loc[97]
n = int(total.n)

fig, ax = plt.subplots(figsize=(11.5, 6.4), dpi=200)
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)

# reference band and limits (behind the bars)
ax.axvspan(45, 50, color="#e8e7e1", lw=0, zorder=0)
for x, label in [(45, "45 days: MSME limit"), (60, "60 days: other vendors")]:
    ax.axvline(x, color=MUTED, lw=1, zorder=1)
    ax.text(x - 0.6 if x == 45 else x + 0.6, -0.9, label, ha="right" if x == 45 else "left", va="bottom", fontsize=9, color=INK2)

start = 0.0
rows = []
for i, (o, r) in enumerate(stages.iterrows()):
    colour = WORK if r.kind == "worked" else WAIT
    ax.barh(i, r.cal_mean, left=start, height=0.58, color=colour, zorder=3)
    share = r.share_of_total_cal_mean
    label = f"{r.cal_mean:.1f} d  ({share:.0%})"
    ax.text(start + r.cal_mean + 0.6, i, label, va="center", ha="left", fontsize=9.5, color=INK, zorder=4)
    if o == 7:
        ax.text(start - 0.6, i, f"mean over all bills;\n{fg['query.mean_days_among_queried']:.0f} d on the "
                f"{fg['query.share_of_bills']:.1%} of paid invoices with a query", va="center", ha="right", fontsize=8.5, color=INK2, zorder=4)
    rows.append(r.stage)
    start += r.cal_mean

i = len(stages)
ax.barh(i + 0.5, total.cal_mean, left=0, height=0.58, color=TOTAL, zorder=3)
ax.text(total.cal_mean + 0.6, i + 0.5, f"{total.cal_mean:.1f} d mean   (median {total.cal_median:.0f}, p90 {total.cal_p90:.0f})",
        va="center", ha="left", fontsize=9.5, color=INK, fontweight="bold", zorder=4)
rows_pos = list(range(len(stages))) + [i + 0.5]
ax.set_yticks(rows_pos)
ax.set_yticklabels(rows + ["Invoice date to paid date"], fontsize=10, color=INK)
ax.invert_yaxis()
ax.set_xlim(0, 70)
ax.set_ylim(i + 1.1, -1.2)
ax.set_xlabel("Days since invoice date (mean, calendar days)", fontsize=9.5, color=INK2)
ax.tick_params(axis="x", colors=INK2, labelsize=9, length=0)
ax.tick_params(axis="y", length=0, pad=6)
ax.xaxis.grid(True, color=GRID, lw=0.8, zorder=0)
ax.set_axisbelow(True)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color("#c3c2b7")

# legend (two series, always present)
from matplotlib.patches import Patch

ax.legend(handles=[Patch(color=WAIT, label=f"Waiting: {waiting.cal_mean:.1f} d ({waiting.share_of_total_cal_mean:.0%})"),
                   Patch(color=WORK, label=f"Worked on: {worked.cal_mean:.1f} d ({worked.share_of_total_cal_mean:.0%})"),
                   Patch(color="#e8e7e1", label="CFO's claim: 45 to 50 days")],
          loc="upper left", bbox_to_anchor=(0.37, 0.93), frameon=False, fontsize=9.5, labelcolor=INK)

fig.text(0.02, 0.965, f"{waiting.share_of_total_cal_mean:.0%} of the {total.cal_mean:.0f} days from invoice to payment is waiting, not work",
         fontsize=15, fontweight="bold", color=INK, ha="left", va="top")
fig.text(0.02, 0.915, f"Mean calendar days per stage, {n:,} paid invoices dated Apr 2025 to Mar 2026. Largest single wait: the queue at central AP.",
         fontsize=10, color=INK2, ha="left", va="top")
fig.text(0.02, 0.012, "Worked = a named person is acting on the bill (elapsed time, not effort). Excludes credit notes, unpaid bills and "
         f"{int(fg['pop.invoices_bad_paid_date_excluded'])} invoices with an impossible payment date.\nSource: pack/data bill_register.csv and queries.csv via analysis/out/bills_clean.parquet. Table: analysis/out/stage_times.csv.",
         fontsize=8, color=MUTED, ha="left", va="bottom")
fig.subplots_adjust(left=0.27, right=0.97, top=0.84, bottom=0.14)
fig.savefig(OUT / "stage_times_chart.png", facecolor=SURFACE)
print("wrote", OUT / "stage_times_chart.png")
