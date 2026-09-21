"""Figures for the revised Chapters 3-5, generated from the saved validation data.

Run from the project root:  python scripts/06_plots_validation.py
Writes PNG (300 dpi) and PDF (vector) to ThesisChapters/Revised/figures/.

Colours are the Okabe-Ito colour-blind-safe set; the figures also differ in line
style and marker so they survive black-and-white printing.
"""
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
VAL = ROOT / "processed" / "validation"
OUT = ROOT / "ThesisChapters" / "Revised" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9.5,
    "legend.fontsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5,
    "figure.dpi": 120, "savefig.dpi": 300, "savefig.bbox": "tight",
})

C = {"ASCON": "#0072B2", "AES_COLD": "#D55E00", "AES_WARM": "#009E73", "AES_SETKEY": "#7f7f7f"}
LS = {"ASCON": "-", "AES_COLD": "--", "AES_WARM": "-."}
MK = {"ASCON": "o", "AES_COLD": "s", "AES_WARM": "^"}
LBL = {"ASCON": "ASCON-128 (software)",
       "AES_COLD": "AES-128-GCM, setup every call",
       "AES_WARM": "AES-128-GCM, context reused"}
VARS = ["ASCON", "AES_COLD", "AES_WARM"]

r1 = pd.read_csv(VAL / "validation_run1" / "validation_rows.csv")
r2 = pd.read_csv(VAL / "validation_run2" / "validation_rows.csv")
r1["run"], r2["run"] = 1, 2
allr = pd.concat([r1, r2], ignore_index=True)


def save(fig, name):
    fig.savefig(OUT / f"{name}.png")
    fig.savefig(OUT / f"{name}.pdf")
    plt.close(fig)
    print("wrote", name)


def agg(df, col):
    g = df.groupby(["variant", "size"])[col]
    m, s, n = g.mean(), g.std(ddof=1), g.count()
    ci = stats.t.ppf(0.975, n - 1) * s / np.sqrt(n)
    return pd.DataFrame({"mean": m, "ci": ci}).reset_index()


def interp_cross(x, d):
    for i in range(len(x) - 1):
        if d[i] < 0 <= d[i + 1]:
            return x[i] + (0 - d[i]) * (x[i + 1] - x[i]) / (d[i + 1] - d[i])
    return None


# ------------------------------------------------------------ numbers reused
t1 = agg(r1, "time_per_op_us")
e1 = agg(r1, "E_uJ")
sizes1 = sorted(r1[r1["size"] > 0]["size"].unique())

# time crossover ASCON vs AES_COLD (Run 1, interpolated)
tp = t1.pivot(index="size", columns="variant", values="mean").loc[sizes1]
t_cross = interp_cross(np.array(sizes1, float), (tp["ASCON"] - tp["AES_COLD"]).values)

# energy break-even and bootstrap band from Run 2 (paired by replicate)
A = r2[r2.variant == "ASCON"].pivot(index="rep", columns="size", values="E_uJ")
B = r2[r2.variant == "AES_COLD"].pivot(index="rep", columns="size", values="E_uJ")
D = A - B
s2 = np.array(D.columns, float)
be_point = interp_cross(s2, D.mean().values)
rng = np.random.default_rng(128)
boots = []
for _ in range(5000):
    pick = rng.choice(D.index.values, size=len(D), replace=True)
    c = interp_cross(s2, D.loc[pick].mean().values)
    if c is not None:
        boots.append(c)
be_lo, be_hi = np.percentile(boots, [2.5, 97.5])
print(f"time crossover {t_cross:.0f} B; break-even {be_point:.0f} B, 95% CI {be_lo:.0f}-{be_hi:.0f} B")


# ============================================================ Figure 7: time
def fig_time():
    fig, ax = plt.subplots(figsize=(6.3, 3.9))
    for v in VARS:
        d = agg(allr[(allr.variant == v) & (allr["size"] > 0)], "time_per_op_us")
        ax.plot(d["size"], d["mean"], LS[v], color=C[v], marker=MK[v], ms=3.5, lw=1.2, label=LBL[v])
        ax.fill_between(d["size"], d["mean"] - d["ci"], d["mean"] + d["ci"], color=C[v], alpha=0.25, lw=0)
    ax.set_xlabel("Payload size (bytes)")
    ax.set_ylabel("Time per operation (µs)")
    ax.set_title("Time per operation against payload size")
    ax.axvline(t_cross, color="k", lw=0.8, ls=":")
    ax.annotate(f"time crossover ≈ {t_cross:.0f} B\n(ASCON vs setup every call)",
                xy=(t_cross, 600), xytext=(t_cross + 60, 1350), fontsize=7.5,
                arrowprops=dict(arrowstyle="-", lw=0.6))
    ax.legend(loc="upper left", frameon=False)
    ins = ax.inset_axes([0.58, 0.10, 0.38, 0.36])
    for v in VARS:
        d = agg(allr[(allr.variant == v) & (allr["size"].between(16, 448))], "time_per_op_us")
        ins.plot(d["size"], d["mean"], LS[v], color=C[v], marker=MK[v], ms=2.5, lw=0.9)
    ins.set_title("16–448 B", fontsize=7)
    ins.tick_params(labelsize=6.5)
    ins.grid(alpha=0.2)
    save(fig, "fig07_time_per_operation")


# ============================================================ Figure 8: energy + fits
def fig_energy_fits():
    fig, ax = plt.subplots(figsize=(6.3, 3.9))
    for v in VARS:
        d = e1[(e1.variant == v) & (e1["size"] > 0)]
        r = stats.linregress(d["size"], d["mean"])
        ax.errorbar(d["size"], d["mean"], yerr=d["ci"], fmt=MK[v], color=C[v], ms=3.5, capsize=1.5,
                    lw=0.7, label=f"{LBL[v]}: {r.slope:.4f} µJ/B, intercept {r.intercept:.2f} µJ")
        xs = np.array([0, 1600])
        ax.plot(xs, r.intercept + r.slope * xs, LS[v], color=C[v], lw=1.0)
    ax.set_xlim(0, 1620)
    ax.set_xlabel("Payload size (bytes)")
    ax.set_ylabel("Energy per operation (µJ)")
    ax.set_title("Energy per operation with linear fits (Run 1)")
    ax.legend(loc="upper left", frameon=False)
    save(fig, "fig08_energy_fits")


# ============================================================ Figure 9: energy per byte
def fig_per_byte():
    fig, ax = plt.subplots(figsize=(6.3, 3.9))
    for v in VARS:
        d = agg(allr[(allr.variant == v) & (allr["size"] > 0)], "E_uJ")
        ax.plot(d["size"], d["mean"] / d["size"], LS[v], color=C[v], marker=MK[v], ms=3.5, lw=1.2, label=LBL[v])
    ax.set_xscale("log")
    ax.set_xticks([16, 32, 64, 128, 256, 512, 1024, 1600])
    ax.get_xaxis().set_major_formatter(mpl.ticker.ScalarFormatter())
    ax.axvspan(be_lo, be_hi, color="gray", alpha=0.3, lw=0)
    ax.axvline(be_point, color="k", lw=0.8, ls=":")
    ax.annotate(f"break-even ≈ {be_point:.0f} B\n(95% CI {be_lo:.0f}–{be_hi:.0f} B)", xy=(be_point, 0.30),
                xytext=(be_point * 1.35, 0.34), fontsize=7.5, arrowprops=dict(arrowstyle="-", lw=0.6))
    ax.set_xlabel("Payload size (bytes, log scale)")
    ax.set_ylabel("Energy per byte (µJ/B)")
    ax.set_title("Energy per byte against payload size")
    ax.legend(loc="upper right", frameon=False)
    save(fig, "fig09_energy_per_byte")


# ============================================================ Figure 10: fine sweep
def fig_fine():
    fig, ax = plt.subplots(figsize=(6.3, 3.6))
    n = len(D)
    m = D.mean()
    ci = stats.t.ppf(0.975, n - 1) * D.std(ddof=1) / np.sqrt(n)
    ax.errorbar(s2, m.values, yerr=ci.values, fmt="o", color=C["ASCON"], capsize=3, ms=4, lw=1)
    ax.plot(s2, m.values, "-", color=C["ASCON"], lw=0.8, alpha=0.6)
    ax.axhline(0, color="k", lw=0.8)
    ax.axvspan(be_lo, be_hi, color="gray", alpha=0.25, lw=0)
    ax.text(be_hi + 1, 0.55, f"break-even ≈ {be_point:.0f} B\n95% CI {be_lo:.0f}–{be_hi:.0f} B", fontsize=7.5)
    # difference = ASCON - AES: positive means ASCON uses MORE energy, i.e. AES is more efficient
    ax.text(65, 0.80, "↑ positive: AES-128-GCM more efficient", fontsize=7.5, color=C["AES_COLD"])
    ax.text(127, -1.12, "↓ negative: ASCON-128 more efficient", fontsize=7.5, color=C["ASCON"], ha="right")
    ax.set_xticks(s2)
    ax.set_xlabel("Payload size (bytes)")
    ax.set_ylabel("ASCON − AES (setup every call), µJ per operation")
    ax.set_title("Fine sweep around the break-even (Run 2, 15 replicates, 95% CI of the paired difference)")
    save(fig, "fig10_fine_sweep")


# ============================================================ setup cost
def fig_setup():
    e = agg(r1, "E_uJ")
    t = agg(r1, "time_per_op_us")
    fig, axs = plt.subplots(1, 2, figsize=(6.3, 3.3))
    for ax, d, unit, name in [(axs[0], e, "µJ", "Energy per operation"), (axs[1], t, "µs", "Time per operation")]:
        g = lambda v, s: float(d[(d.variant == v) & (d["size"] == s)]["mean"].iloc[0])
        warm, cold, asc = g("AES_WARM", 16), g("AES_COLD", 16), g("ASCON", 16)
        setk = float(d[d.variant == "AES_SETKEY"]["mean"].iloc[0])
        rest = cold - warm - setk
        ax.bar(0, asc, color=C["ASCON"], width=0.6)
        ax.bar(1, warm, color=C["AES_WARM"], width=0.6)
        ax.bar(2, warm, color=C["AES_WARM"], width=0.6)
        ax.bar(2, setk, bottom=warm, color=C["AES_SETKEY"], width=0.6, label="measured setup step")
        ax.bar(2, rest, bottom=warm + setk, color="white", edgecolor=C["AES_SETKEY"], hatch="///",
               width=0.6, label="not isolated")
        for x, v in [(0, asc), (1, warm), (2, cold)]:
            ax.text(x, v * 1.02, f"{v:.2f}" if unit == "µJ" else f"{v:.1f}", ha="center", fontsize=7.5)
        ax.set_xticks([0, 1, 2])
        ax.set_xticklabels(["ASCON", "AES\ncontext reused", "AES\nsetup each call"], fontsize=7.5)
        ax.set_ylabel(unit)
        ax.set_title(f"{name}, 16 B", fontsize=9)
        ax.set_ylim(0, cold * 1.15)
    axs[1].legend(loc="upper left", fontsize=7, frameon=False)
    fig.suptitle("Where the AES-128-GCM setup cost appears (Run 1)", fontsize=9.5, y=1.02)
    save(fig, "fig_aes_setup_cost")


# ============================================================ power by variant
def fig_power():
    big = r1[(r1["size"] >= 256)]
    rows = []
    for v in VARS:
        x = big[big.variant == v].dP_mW
        rows.append((v, x.mean(), stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))))
    sk = r1[r1.variant == "AES_SETKEY"].dP_mW
    rows.append(("AES_SETKEY", sk.mean(), stats.t.ppf(0.975, len(sk) - 1) * sk.std(ddof=1) / np.sqrt(len(sk))))
    fig, ax = plt.subplots(figsize=(5.2, 3.3))
    labels = ["ASCON-128", "AES-128-GCM\nsetup each call", "AES-128-GCM\ncontext reused", "AES setup\nstep alone"]
    for i, (v, m, ci) in enumerate(rows):
        ax.bar(i, m, yerr=ci, color=C[v], width=0.6, capsize=3)
        ax.text(i, m + 2, f"{m:.1f}", ha="center", fontsize=8)
    ax.set_xticks(range(4))
    ax.set_xticklabels(labels, fontsize=7.5)
    ax.set_ylabel("Extra power above idle (mW)")
    ax.set_title("Extra power drawn while the cipher runs\n(payloads ≥ 256 B; setup step: no payload)")
    ax.set_ylim(0, max(r[1] for r in rows) * 1.2)
    save(fig, "fig_power_by_variant")


# ============================================================ modelled duty cycle
def fig_duty():
    e = agg(r1, "E_uJ")
    g = lambda v, s: float(e[(e.variant == v) & (e["size"] == s)]["mean"].iloc[0])
    sizes = [16, 352, 1600]
    fig, axs = plt.subplots(1, 2, figsize=(6.3, 3.5), sharey=True)
    for ax, sleep, lab in [(axs[0], 990, "5 µA deep-sleep current"), (axs[1], 1980, "10 µA deep-sleep current")]:
        x = 0
        ticks, tl = [], []
        for s in sizes:
            for v, off in [("ASCON", 0), ("AES_COLD", 1)]:
                act = g(v, s)
                ax.bar(x + off, sleep, color="#cccccc", width=0.8)
                ax.bar(x + off, act, bottom=sleep, color=C[v], width=0.8)
                ax.text(x + off, sleep + act + 25, f"{100 * act / (sleep + act):.1f}%", ha="center", fontsize=6.5)
            ticks.append(x + 0.5)
            tl.append(f"{s} B")
            x += 3
        ax.set_xticks(ticks)
        ax.set_xticklabels(tl)
        ax.set_title(lab, fontsize=8.5)
        ax.set_ylim(0, 2300)
    axs[0].set_ylabel("Energy of one modelled cycle (µJ)")
    handles = [mpl.patches.Patch(color="#cccccc", label="modelled sleep (60 s)"),
               mpl.patches.Patch(color=C["ASCON"], label="ASCON-128 encryption"),
               mpl.patches.Patch(color=C["AES_COLD"], label="AES-128-GCM encryption (setup each call)")]
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=7, frameon=False, bbox_to_anchor=(0.5, -0.06))
    fig.suptitle("Encryption within a modelled 60 s duty cycle (label: encryption share of the cycle;\n"
                 "transmission and wake-up not included)", fontsize=8.5, y=1.03)
    save(fig, "fig_modelled_duty_cycle")


# ============================================================ Campaign A sensitivity
def fig_sensitivity():
    s = pd.read_csv(ROOT / "processed" / "original_sensitivity.csv")
    fig, ax = plt.subplots(figsize=(5.4, 3.4))
    labels = ["no trimming", "IQR k = 3", "IQR k = 1.5\n(used)"]
    ax.bar(range(3), s["energy_crossing_B"], color="#999999", width=0.55)
    for i, v in enumerate(s["energy_crossing_B"]):
        ax.text(i, v + 6, f"{v:.0f} B", ha="center", fontsize=8)
    ax.axhspan(be_lo, be_hi, color="#ffffff", alpha=0.6, lw=0)
    ax.axhline(be_point, color=C["ASCON"], lw=2,
               label=f"validation break-even ≈ {be_point:.0f} B (95% CI {be_lo:.0f}–{be_hi:.0f} B)")
    ax.legend(loc="upper right", frameon=True, framealpha=0.95, fontsize=7.5)
    ax.set_xticks(range(3))
    ax.set_xticklabels(labels)
    ax.set_ylabel("Break-even payload (bytes)")
    ax.set_ylim(0, 420)
    ax.set_title("Campaign A break-even under three trimming choices\nagainst the validation measurement")
    save(fig, "fig_campaignA_trimming_sensitivity")


# ============================================================ method diagrams
def fig_windows():
    """Idle / load / idle windows with simulated INA219 128-sample-average output."""
    T = 68.6e-3
    t = np.linspace(0, 1.5, 6001)
    true_i = np.where((t >= 0.4) & (t < 1.1), 51.2, 36.7)
    # INA219 result = average over each 68.6 ms conversion window, held until the next completes
    edges = np.arange(0, 1.5 + T, T)
    ina = np.empty_like(t)
    for k in range(len(edges) - 1):
        m = (t >= edges[k]) & (t < edges[k + 1])
        prev = (t >= edges[k] - T) & (t < edges[k])
        # the register visible during window k is the average of window k-1
        ina[m] = true_i[prev].mean() if prev.any() else 36.7
    fig, ax = plt.subplots(figsize=(6.3, 3.4))
    ax.plot(t, true_i, color="#999999", lw=1, label="true current (schematic)")
    ax.step(t, ina, where="post", color=C["ASCON"], lw=1.2, label="INA219 register (68.6 ms averaged results)")
    for a, b, c, lab in [(0.0, 0.4, "#eeeeee", "idle window"), (0.4, 1.1, "#fde5d5", "load window (700 ms)"),
                         (1.1, 1.5, "#eeeeee", "idle window")]:
        ax.axvspan(a, b, color=c, alpha=0.7, lw=0)
        ax.text((a + b) / 2, 55.6, lab, ha="center", fontsize=7.5)
    for a, b in [(0.0, 0.15), (0.4, 0.6), (1.1, 1.25)]:
        ax.axvspan(a, b, facecolor="none", edgecolor="k", hatch="///", lw=0, alpha=0.35)
    ax.text(0.075, 33.2, "discarded", ha="center", fontsize=6.5)
    ax.text(0.5, 33.2, "discarded", ha="center", fontsize=6.5)
    ax.text(1.175, 33.2, "discarded", ha="center", fontsize=6.5)
    ax.set_ylim(32, 58)
    ax.set_xlim(0, 1.5)
    ax.set_xlabel("Time within one configuration (s)")
    ax.set_ylabel("Supply current (mA)")
    ax.set_title("Sustained-load measurement of one configuration (schematic)")
    ax.legend(loc="upper center", frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, -0.17), ncol=2)
    save(fig, "fig_method_windows")


def fig_sensor_scale():
    items = [
        ("AES-128-GCM call, 16 B (Campaign B)", 57.4, C["AES_WARM"]),
        ("ASCON-128 call, 16 B (Campaign B)", 57.9, C["ASCON"]),
        ("INA219 register read pair (current + power)", 398, "#999999"),
        ("INA219 conversion, 12-bit, no averaging", 532, "#999999"),
        ("ASCON-128 call, 1,600 B (Campaign B)", 1926.6, C["ASCON"]),
        ("Campaign A: instrumentation inside timed region (est.)", 1500, "#cc79a7"),
        ("INA219 result with 128-sample averaging (Campaign B)", 68100, "#999999"),
    ]
    items.sort(key=lambda z: z[1])
    fig, ax = plt.subplots(figsize=(6.3, 3.5))
    for i, (lab, v, col) in enumerate(items):
        ax.barh(i, v, color=col, height=0.6)
        ax.text(v * 1.15, i, f"{v:,.0f} µs" if v < 1e4 else f"{v / 1000:.1f} ms", va="center", fontsize=7.5)
    ax.set_yticks(range(len(items)))
    ax.set_yticklabels([i[0] for i in items], fontsize=7.5)
    ax.set_xscale("log")
    ax.set_xlim(20, 4e5)
    ax.set_xlabel("Duration (µs, log scale)")
    ax.set_title("Durations that matter for the energy measurement")
    ax.grid(axis="y", alpha=0)
    save(fig, "fig_sensor_timing_scale")


if __name__ == "__main__":
    fig_time()
    fig_energy_fits()
    fig_per_byte()
    fig_fine()
    fig_setup()
    fig_power()
    fig_duty()
    fig_sensitivity()
    fig_windows()
    fig_sensor_scale()
