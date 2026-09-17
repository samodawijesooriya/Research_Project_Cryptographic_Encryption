"""
Step 7: sleep-phase energy (analytical, from datasheet).
Step 9: comparative statistics (t-tests, crossover, regression, memory, regimes).
"""
import json
import numpy as np
import pandas as pd
from scipy.stats import ttest_ind, linregress


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

# --- Step 7: datasheet constants ---
# Source: Espressif ESP32-C3 Series Datasheet, Version 2.3.
# Table 5-9 "Current Consumption in Low-Power Modes": Deep-sleep (RTC timer + RTC
# memory) = 5 uA (Typ). Per Section 5.6.1, current consumption measurements in this
# section are taken with a 3.3V supply at 25 degC ambient temperature.
I_SLEEP_uA = 5.0
V_SLEEP = 3.3
T_SLEEP_S = 60.0
DATASHEET_REVISION = ("Espressif ESP32-C3 Series Datasheet, Version 2.3, Table 5-9 "
                       "'Current Consumption in Low-Power Modes' (Deep-sleep: RTC "
                       "timer + RTC memory), measured at 3.3V/25degC per Section 5.6.1")

sleep_energy_uJ = V_SLEEP * I_SLEEP_uA * T_SLEEP_S
print(f"Step 7: E_sleep = {V_SLEEP} V * {I_SLEEP_uA} uA * {T_SLEEP_S} s = {sleep_energy_uJ:.2f} uJ")
print(f"        (datasheet: {DATASHEET_REVISION})")

ascon_summary = pd.read_csv("processed/ascon_summary_by_size.csv")
aes_summary = pd.read_csv("processed/aes_summary_by_size.csv")

for name, df in [("ascon", ascon_summary), ("aes", aes_summary)]:
    df["total_duty_cycle_energy_uJ"] = df["energy_uJ"] + sleep_energy_uJ
    df["total_duty_cycle_energy_per_byte_uJ"] = df["total_duty_cycle_energy_uJ"] / df["size"]
    df.to_csv(f"processed/{name}_summary_by_size.csv", index=False)

with open("processed/sleep_energy_constants.json", "w") as f:
    json.dump({
        "I_sleep_uA": I_SLEEP_uA, "V_sleep_V": V_SLEEP, "T_sleep_s": T_SLEEP_S,
        "sleep_energy_uJ": sleep_energy_uJ, "datasheet_citation": DATASHEET_REVISION
    }, f, indent=2, default=_json_default)

# --- Step 9: comparative statistics ---
ascon_clean = pd.read_csv("processed/ascon_clean.csv")
aes_clean = pd.read_csv("processed/aes_clean.csv")


def per_size_ttests(clean_a, clean_h, value_col, label_a="ascon", label_h="aes"):
    results = []
    for size, g_a in clean_a.groupby("size"):
        g_h = clean_h[clean_h["size"] == size]
        if len(g_h) == 0:
            continue
        t_stat, p_two = ttest_ind(g_a[value_col], g_h[value_col], equal_var=False)
        # one-tailed: is ascon greater than aes (t_stat > 0 -> ascon mean higher)
        p_one = p_two / 2 if t_stat > 0 else 1 - p_two / 2
        results.append({"size": size, "t_stat": t_stat, "p_one_tailed": p_one,
                         "significant_at_0.01": p_one < 0.01})
    return pd.DataFrame(results)


ttest_summary = {}
for metric, ascon_col, aes_col in [
    ("time_us", "time_us", "time_us"),
    ("power_mW", "power_mW", "power_mW"),
]:
    tdf = per_size_ttests(ascon_clean, aes_clean, metric)
    tdf.to_csv(f"processed/ttest_{metric}.csv", index=False)
    prop_sig = tdf["significant_at_0.01"].mean()
    ttest_summary[metric] = prop_sig
    print(f"Step 9 t-test ({metric}): {tdf['significant_at_0.01'].sum()}/{len(tdf)} "
          f"sizes significant at alpha=0.01 ({prop_sig:.1%})")

# energy_per_byte_uJ is only available at the summary (per-size aggregate) level via
# energy_uJ/size, not per-row in the clean data (energy = power*time derived per group).
# To t-test it per-row we approximate per-row energy = power_mW * time_ms.
for df in (ascon_clean, aes_clean):
    df["energy_per_byte_uJ_row"] = (df["power_mW"] * (df["time_us"] / 1000)) / df["size"]

tdf_energy = per_size_ttests(ascon_clean, aes_clean, "energy_per_byte_uJ_row")
tdf_energy.to_csv("processed/ttest_energy_per_byte_uJ.csv", index=False)
prop_sig_energy = tdf_energy["significant_at_0.01"].mean()
ttest_summary["energy_per_byte_uJ"] = prop_sig_energy
print(f"Step 9 t-test (energy_per_byte_uJ): "
      f"{tdf_energy['significant_at_0.01'].sum()}/{len(tdf_energy)} sizes significant "
      f"at alpha=0.01 ({prop_sig_energy:.1%})")

with open("processed/ttest_significance_summary.json", "w") as f:
    json.dump(ttest_summary, f, indent=2, default=_json_default)

# --- Crossover / break-even analysis (Objective 3) ---
compare = ascon_summary.merge(aes_summary, on="size", suffixes=("_ascon", "_aes"))
compare["ascon_minus_aes_energy"] = (
    compare["energy_per_byte_uJ_ascon"] - compare["energy_per_byte_uJ_aes"]
)
compare["ascon_minus_aes_total_energy"] = (
    compare["total_duty_cycle_energy_per_byte_uJ_ascon"]
    - compare["total_duty_cycle_energy_per_byte_uJ_aes"]
)
compare.to_csv("processed/comparison_by_size.csv", index=False)

sign_changes = compare[
    (compare["ascon_minus_aes_energy"].shift(1) * compare["ascon_minus_aes_energy"]) < 0
]
crossovers = []
for idx in sign_changes.index:
    if idx == 0:
        continue
    s0, s1 = compare.loc[idx - 1, "size"], compare.loc[idx, "size"]
    d0, d1 = compare.loc[idx - 1, "ascon_minus_aes_energy"], compare.loc[idx, "ascon_minus_aes_energy"]
    # linear interpolation for the zero-crossing
    frac = -d0 / (d1 - d0)
    crossover_size = s0 + frac * (s1 - s0)
    crossovers.append({"bracket_low": s0, "bracket_high": s1,
                        "interpolated_crossover_bytes": crossover_size})

print(f"Step 9 crossover (active-phase energy_per_byte): {crossovers}")

sign_changes_total = compare[
    (compare["ascon_minus_aes_total_energy"].shift(1) * compare["ascon_minus_aes_total_energy"]) < 0
]
crossovers_total = []
for idx in sign_changes_total.index:
    if idx == 0:
        continue
    s0, s1 = compare.loc[idx - 1, "size"], compare.loc[idx, "size"]
    d0, d1 = compare.loc[idx - 1, "ascon_minus_aes_total_energy"], compare.loc[idx, "ascon_minus_aes_total_energy"]
    frac = -d0 / (d1 - d0)
    crossover_size = s0 + frac * (s1 - s0)
    crossovers_total.append({"bracket_low": s0, "bracket_high": s1,
                              "interpolated_crossover_bytes": crossover_size})

print(f"Step 9 crossover (total duty-cycle energy_per_byte): {crossovers_total}")

with open("processed/crossover_results.json", "w") as f:
    json.dump({
        "active_phase_energy_per_byte": crossovers,
        "total_duty_cycle_energy_per_byte": crossovers_total
    }, f, indent=2, default=_json_default)

# --- Regression / scaling analysis ---
regression_results = {}
for label, df in [("ascon", ascon_summary), ("aes", aes_summary)]:
    lr_time = linregress(df["size"], df["mean_time"])
    lr_energy = linregress(df["size"], df["energy_uJ"])
    regression_results[label] = {
        "time_slope": lr_time.slope, "time_intercept": lr_time.intercept,
        "time_r2": lr_time.rvalue ** 2,
        "energy_slope": lr_energy.slope, "energy_intercept": lr_energy.intercept,
        "energy_r2": lr_energy.rvalue ** 2,
    }
    print(f"Step 9 regression ({label}): time slope={lr_time.slope:.4f} R2={lr_time.rvalue**2:.4f}; "
          f"energy slope={lr_energy.slope:.4f} intercept={lr_energy.intercept:.2f} "
          f"R2={lr_energy.rvalue**2:.4f}")

with open("processed/regression_results.json", "w") as f:
    json.dump(regression_results, f, indent=2, default=_json_default)

# --- Memory footprint comparison ---
mem_compare = compare[["size", "mean_mem_ascon", "mean_mem_aes"]].copy()
mem_compare["mem_diff_aes_minus_ascon"] = mem_compare["mean_mem_aes"] - mem_compare["mean_mem_ascon"]
mem_compare.to_csv("processed/memory_comparison.csv", index=False)
print(f"Step 9 memory: mean ASCON mem_total={ascon_clean['mem_total'].mean():.1f} bytes, "
      f"mean AES mem_total={aes_clean['mem_total'].mean():.1f} bytes")

# --- Regime segmentation (Objective 3) ---
small = compare[compare["size"] < 256]
large = compare[compare["size"] > 800]


def regime_verdict(sub, label):
    mean_diff = sub["ascon_minus_aes_energy"].mean()
    preferable = "ASCON" if mean_diff < 0 else "AES"
    print(f"Step 9 regime [{label}]: mean(ascon-aes energy/byte)={mean_diff:.4f} uJ/byte "
          f"-> {preferable} more efficient on average")
    return {"regime": label, "mean_ascon_minus_aes_energy_per_byte": mean_diff,
            "more_efficient": preferable}


regime_results = [
    regime_verdict(small, "small (<256B, LPWAN-typical)"),
    regime_verdict(large, "large (>800B, bulk-telemetry-typical)"),
]
with open("processed/regime_segmentation.json", "w") as f:
    json.dump(regime_results, f, indent=2, default=_json_default)

print("\nAll Step 7 & Step 9 outputs saved to processed/.")
