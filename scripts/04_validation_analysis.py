"""Analysis of the sustained-load validation run (validation_fw/validation_run1.log).

E_op = V_bus * (I_load - mean(I_idle_pre, I_idle_post)) * time_per_op
The INA219 zero-offset cancels in the (load - idle) difference.

Outputs to processed/validation/.
"""
import io
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import sys

ROOT = Path(__file__).resolve().parents[1]
RUN = sys.argv[1] if len(sys.argv) > 1 else "validation_run1"
LOG = ROOT / "validation_fw" / f"{RUN}.log"
OUT = ROOT / "processed" / "validation" / RUN
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(128)
N_BOOT = 5000

lines = LOG.read_text(encoding="utf-8", errors="replace").splitlines()
hdr = next(l for l in lines if l.startswith("HEADER,")).split(",")[1:]
rows = [l.split(",")[1:] for l in lines if l.startswith("DATA,")]
df = pd.DataFrame(rows, columns=hdr)
for c in df.columns:
    if c != "variant":
        df[c] = pd.to_numeric(df[c])

df["idle_mA"] = (df.idle_pre_mA + df.idle_post_mA) / 2
df["dI_mA"] = df.load_mA - df.idle_mA
df["dP_mW"] = df.vbus_V * df.dI_mA
df["E_uJ"] = df.dP_mW * df.time_per_op_us / 1000.0          # mW * us = nJ -> /1000 = uJ
df["idle_drift_mA"] = df.idle_post_mA - df.idle_pre_mA
df.to_csv(OUT / "validation_rows.csv", index=False)

print(f"rows={len(df)}  reps={df.rep.nunique()}  configs={df.groupby(['variant','size']).ngroups}")
print(f"idle drift pre->post: mean {df.idle_drift_mA.mean():+.3f} mA, sd {df.idle_drift_mA.std():.3f} mA")
print(f"dI range: {df.dI_mA.min():.2f}..{df.dI_mA.max():.2f} mA, median {df.dI_mA.median():.2f} mA\n")


def ci95(x):
    x = np.asarray(x, float)
    h = stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))
    return x.mean() - h, x.mean() + h


# ---- per-config summary ------------------------------------------------------
summ = (df.groupby(["variant", "size"])
          .agg(time_us=("time_per_op_us", "mean"), time_sd=("time_per_op_us", "std"),
               dP_mW=("dP_mW", "mean"), dP_sd=("dP_mW", "std"),
               E_uJ=("E_uJ", "mean"), E_sd=("E_uJ", "std"), n=("E_uJ", "size"))
          .reset_index())
summ["E_ci_lo"] = summ.E_uJ - 2.262 * summ.E_sd / np.sqrt(summ.n)
summ["E_ci_hi"] = summ.E_uJ + 2.262 * summ.E_sd / np.sqrt(summ.n)
summ.to_csv(OUT / "validation_summary.csv", index=False)

print("=== AES setup cost in isolation (AES_SETKEY, size ignored) ===")
sk = df[df.variant == "AES_SETKEY"]
print(f"time per setkey: {sk.time_per_op_us.mean():.2f} us (CI {ci95(sk.time_per_op_us)[0]:.2f}..{ci95(sk.time_per_op_us)[1]:.2f})")
print(f"power delta:     {sk.dP_mW.mean():.1f} mW")
print(f"energy per setkey: {sk.E_uJ.mean():.3f} uJ (CI {ci95(sk.E_uJ)[0]:.3f}..{ci95(sk.E_uJ)[1]:.3f})\n")

# ---- regressions -------------------------------------------------------------
print("=== Linear fits over ALL sizes (mean per size vs size) ===")
fits = []
for v in ["ASCON", "AES_COLD", "AES_WARM"]:
    s = summ[summ.variant == v]
    for y in ["time_us", "E_uJ"]:
        r = stats.linregress(s["size"], s[y])
        fits.append(dict(variant=v, y=y, slope=r.slope, intercept=r.intercept,
                         intercept_se=r.intercept_stderr, r2=r.rvalue ** 2))
fits = pd.DataFrame(fits)
print(fits.round(5).to_string(index=False), "\n")
fits.to_csv(OUT / "validation_fits.csv", index=False)

# ---- paired difference and break-even ---------------------------------------
sizes = sorted(df["size"].unique())
sizes = [s for s in sizes if s > 0]


def rep_table(variant, value):
    return (df[(df.variant == variant) & (df["size"] > 0)]
            .pivot(index="rep", columns="size", values=value))


def crossing(diff_by_size):
    """Interpolated size where diff (ASCON - AES) goes from negative to positive
    scanning ascending sizes; None if no clean sign change."""
    s = np.array(sizes, float)
    d = np.asarray(diff_by_size, float)
    for i in range(len(s) - 1):
        if d[i] < 0 <= d[i + 1]:
            return s[i] + (0 - d[i]) * (s[i + 1] - s[i]) / (d[i + 1] - d[i])
    return None


for aes_var in ["AES_COLD", "AES_WARM"]:
    A = rep_table("ASCON", "E_uJ")
    B = rep_table(aes_var, "E_uJ")
    per_byte = (A - B)  # total-energy difference; sign change identical to per-byte
    point = crossing(per_byte.mean().values)
    boots = []
    reps = A.index.values
    for _ in range(N_BOOT):
        pick = rng.choice(reps, size=len(reps), replace=True)
        c = crossing(per_byte.loc[pick].mean().values)
        boots.append(c)
    valid = np.array([b for b in boots if b is not None])
    frac = len(valid) / N_BOOT
    print(f"=== Break-even ASCON vs {aes_var} (total energy per op) ===")
    print("mean(ASCON-AES) by size, uJ:")
    print(per_byte.mean().round(3).to_string())
    if point is None:
        print("no clean negative->positive crossing in the mean curve")
    else:
        lo, hi = np.percentile(valid, [2.5, 97.5])
        print(f"crossing (point est.) = {point:.0f} B; bootstrap 95% CI {lo:.0f}..{hi:.0f} B "
              f"({frac*100:.0f}% of resamples had a clean crossing)")
    print()

    # per-size paired tests, two-sided, Holm-corrected
    pv = []
    for s in sizes:
        d = (A[s] - B[s]).values
        pv.append(stats.ttest_1samp(d, 0.0).pvalue)
    pv = np.array(pv)
    order = np.argsort(pv)
    m = len(pv)
    holm = np.empty(m)
    run = 0.0
    for rank, idx in enumerate(order):
        run = max(run, (m - rank) * pv[idx])
        holm[idx] = min(1.0, run)
    out = pd.DataFrame(dict(size=sizes,
                            diff_uJ=[(A[s] - B[s]).mean() for s in sizes],
                            p_raw=pv, p_holm=holm))
    out["sig_holm_0.01"] = out.p_holm < 0.01
    out.to_csv(OUT / f"validation_paired_tests_{aes_var}.csv", index=False)
    print(out.round(4).to_string(index=False), "\n")

# ---- time-only comparison (pure crypto, no measurement overhead) --------------
print("=== time per op (us): ASCON vs AES_WARM vs AES_COLD ===")
t = summ.pivot(index="size", columns="variant", values="time_us").drop(index=0, errors="ignore")
print(t[["ASCON", "AES_COLD", "AES_WARM"]].round(1).to_string())
