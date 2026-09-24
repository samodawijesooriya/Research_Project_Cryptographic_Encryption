"""Campaign A: raw INA219 current readings before and after the zero-offset correction.

Run from the project root:  python scripts/07_plot_offset_histogram.py
Writes fig_campaignA_offset_histogram (PNG 300 dpi + PDF) to ThesisChapters/Revised/figures/.

Uses the complete sweeps only (Step 2 of the pipeline) and the shared calibration
of the thesis (offset 5.70 mA from the ASCON data, applied to both algorithms).
Each trial contributes two readings (before and after the cipher call).
"""
import contextlib
import io
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import pipeline_common as pc

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ThesisChapters" / "Revised" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
RAW = {"ASCON": ROOT / "raw" / "benchmark_raw_log_ASCON1.txt",
       "AES": ROOT / "raw" / "benchmark_raw_log_AES1.txt"}
OFFSET_MA = 5.70

mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9.5,
    "legend.fontsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5,
    "figure.dpi": 120, "savefig.dpi": 300, "savefig.bbox": "tight",
})
C = {"ASCON": "#0072B2", "AES": "#D55E00"}
LBL = {"ASCON": "ASCON-128 session", "AES": "AES-128-GCM session"}

readings = {}
for algo, path in RAW.items():
    with contextlib.redirect_stdout(io.StringIO()):
        raw, _ = pc.load_raw(path, algo)
        comp, _ = pc.keep_complete_iterations(raw, algo)
    readings[algo] = pd.concat([comp["current_before"], comp["current_after"]]).to_numpy()

bins = np.arange(-20, 141, 1.0)
fig, axes = plt.subplots(2, 1, figsize=(6.3, 4.4), sharex=True)

for ax, corrected in zip(axes, [False, True]):
    for algo in ["ASCON", "AES"]:
        v = readings[algo]
        if corrected:
            v = np.clip(v + OFFSET_MA, 0, None)   # as in pipeline_common.calibrate_current_power
        ax.hist(v, bins=bins, histtype="step", linewidth=1.1, color=C[algo],
                linestyle="-" if algo == "ASCON" else "--",
                label=f"{LBL[algo]} ({(readings[algo] < 0).mean():.1%} below 0 mA raw)")
    ax.axvspan(-20, 0, color="#999999", alpha=0.18, linewidth=0)
    ax.axvline(0, color="black", linewidth=0.7)
    ax.set_ylabel("Readings per 1 mA bin")
    ax.yaxis.set_major_locator(mpl.ticker.MultipleLocator(5000))
    ax.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda x, _: f"{x / 1000:g}k" if x else "0"))

a_neg = readings["ASCON"][readings["ASCON"] < 0]
axes[0].set_title(f"(a) Raw readings: a separate cluster below zero (median {np.median(a_neg):.1f} mA)",
                  loc="left")
axes[0].text(-10, axes[0].get_ylim()[1] * 0.93, "negative\ncurrent", ha="center", va="top",
             fontsize=7.5, color="#555555")
axes[0].legend(loc="upper left", bbox_to_anchor=(0.12, 1.0), frameon=False)
axes[1].set_title(f"(b) After adding the {OFFSET_MA:.2f} mA offset (negatives clipped to 0)", loc="left")
axes[1].set_xlabel("INA219 current reading (mA)")
axes[1].set_xlim(-20, 140)

for algo, v in readings.items():
    print(f"{algo}: {len(v)} readings, {(v < 0).mean():.2%} negative, "
          f"median of negatives {np.median(v[v < 0]):.2f} mA, "
          f"{((v < -20) | (v > 140)).mean():.2%} outside the plotted range")

fig.tight_layout()
fig.savefig(OUT / "fig_campaignA_offset_histogram.png")
fig.savefig(OUT / "fig_campaignA_offset_histogram.pdf")
print("wrote fig_campaignA_offset_histogram")
