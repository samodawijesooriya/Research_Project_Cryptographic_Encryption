"""Supervisor comments 4 and 5 applied to the ORIGINAL dataset.

(4) Does the conclusion survive without / with different outlier trimming?
(5) What do the per-size t-tests look like two-sided and Holm-corrected?

Run from the project root:  python scripts/05_original_sensitivity.py
Writes processed/original_sensitivity.csv and prints a summary.
"""
import contextlib
import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ttest_ind

sys.path.insert(0, str(Path(__file__).parent))
import pipeline_common as pc

RAW = {"ASCON": "raw/benchmark_raw_log_ASCON1.txt", "AES": "raw/benchmark_raw_log_AES1.txt"}


def build(algo, k):
    """Steps 1-3 as in the thesis pipeline, then trimming with factor k (None = no trimming)."""
    with contextlib.redirect_stdout(io.StringIO()):
        raw, _ = pc.load_raw(RAW[algo], algo)
        comp, _ = pc.keep_complete_iterations(raw, algo)
        # the thesis used one shared calibration (ASCON offset, ASCON v_bus); reproduce that
        cal, info = pc.calibrate_current_power(comp, algo, offset_mA=5.70, v_bus=4.674)
        if k is not None:
            cal, _, _ = pc.apply_full_outlier_trim(cal, algo, k=k)
    cal = cal.copy()
    cal["power_mW"] = cal["power_delta_corr"]
    cal["e_per_byte"] = cal["power_mW"] * (cal["time_us"] / 1000) / cal["size"]
    return cal


def crossing(sizes, diff):
    for i in range(len(sizes) - 1):
        if diff[i] < 0 <= diff[i + 1]:
            return sizes[i] + (0 - diff[i]) * (sizes[i + 1] - sizes[i]) / (diff[i + 1] - diff[i])
    return None


def holm(p):
    p = np.asarray(p)
    o = np.argsort(p)
    m = len(p)
    out = np.empty(m)
    run = 0.0
    for r, i in enumerate(o):
        run = max(run, (m - r) * p[i])
        out[i] = min(1.0, run)
    return out


def tests(a, h, col):
    sizes, one, two = [], [], []
    for s, ga in a.groupby("size"):
        gh = h[h["size"] == s]
        t, p2 = ttest_ind(ga[col], gh[col], equal_var=False)
        sizes.append(s)
        two.append(p2)
        one.append(p2 / 2 if t > 0 else 1 - p2 / 2)   # thesis: H1 = ASCON > AES
    two, one = np.array(two), np.array(one)
    return dict(one_tailed_0p01=int((one < 0.01).sum()),
                two_sided_raw_0p01=int((two < 0.01).sum()),
                two_sided_holm_0p01=int((holm(two) < 0.01).sum()))


rows = []
for label, k in [("no trimming", None), ("IQR k=3.0", 3.0), ("IQR k=1.5 (thesis)", 1.5)]:
    a, h = build("ASCON", k), build("AES", k)
    ga = a.groupby("size").agg(t=("time_us", "mean"), p=("power_mW", "mean"))
    gh = h.groupby("size").agg(t=("time_us", "mean"), p=("power_mW", "mean"))
    ea = ga.p * ga.t / 1000 / ga.index
    eh = gh.p * gh.t / 1000 / gh.index
    sizes = list(ga.index)
    diff = (ea - eh).values
    tdiff = (ga.t - gh.t).values
    a["e"], h["e"] = a["e_per_byte"], h["e_per_byte"]
    r = dict(variant=label, rows_ascon=len(a), rows_aes=len(h),
             energy_crossing_B=crossing(sizes, diff),
             time_crossing_B=(next((sizes[i] + (0 - tdiff[i]) * 16 / (tdiff[i + 1] - tdiff[i])
                                    for i in range(len(sizes) - 1) if tdiff[i] < 0 <= tdiff[i + 1]), None)),
             n_sign_changes_energy=int(((np.sign(diff[:-1]) * np.sign(diff[1:])) < 0).sum()))
    for m in ["time_us", "power_mW", "e"]:
        for k2, v in tests(a, h, m).items():
            r[f"{m}:{k2}"] = v
    rows.append(r)

out = pd.DataFrame(rows)
out.to_csv("processed/original_sensitivity.csv", index=False)
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 50)
print(out.T.to_string())
