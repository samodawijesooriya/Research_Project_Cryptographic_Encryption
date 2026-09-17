"""
Step 10: visualizations.
"""
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ascon = pd.read_csv("processed/ascon_summary_by_size.csv")
aes = pd.read_csv("processed/aes_summary_by_size.csv")

with open("processed/crossover_results.json") as f:
    crossover = json.load(f)

primary_crossover = crossover["active_phase_energy_per_byte"][0]["interpolated_crossover_bytes"]

COLOR_ASCON = "#2b6cb0"  # blue
COLOR_AES = "#c05621"    # orange

# --- Chart 1: execution time vs payload size, with 95% CI band ---
plt.figure(figsize=(8, 5))
plt.plot(ascon["size"], ascon["mean_time"], label="ASCON-128 (SW)", color=COLOR_ASCON)
plt.fill_between(ascon["size"], ascon["ci95_low_time"], ascon["ci95_high_time"],
                  color=COLOR_ASCON, alpha=0.2)
plt.plot(aes["size"], aes["mean_time"], label="AES-128-GCM (HW)", color=COLOR_AES)
plt.fill_between(aes["size"], aes["ci95_low_time"], aes["ci95_high_time"],
                  color=COLOR_AES, alpha=0.2)
plt.xlabel("Payload size (bytes)")
plt.ylabel("Mean execution time (µs)")
plt.title("Execution time scaling: ASCON-128 vs AES-128-GCM")
plt.legend()
plt.tight_layout()
plt.savefig("figures/execution_time_scaling.png", dpi=200)
plt.close()

# --- Chart 2: throughput vs payload size ---
plt.figure(figsize=(8, 5))
plt.plot(ascon["size"], ascon["throughput_Bps"], label="ASCON-128 (SW)", color=COLOR_ASCON)
plt.plot(aes["size"], aes["throughput_Bps"], label="AES-128-GCM (HW)", color=COLOR_AES)
plt.xlabel("Payload size (bytes)")
plt.ylabel("Throughput (bytes/s)")
plt.title("Throughput scaling: ASCON-128 vs AES-128-GCM")
plt.legend()
plt.tight_layout()
plt.savefig("figures/throughput_scaling.png", dpi=200)
plt.close()

# --- Chart 3: energy per byte vs payload size, with crossover marker (CORE RQ CHART) ---
plt.figure(figsize=(8, 5))
plt.plot(ascon["size"], ascon["energy_per_byte_uJ"], label="ASCON-128 (SW)", color=COLOR_ASCON)
plt.plot(aes["size"], aes["energy_per_byte_uJ"], label="AES-128-GCM (HW)", color=COLOR_AES)
plt.axvline(primary_crossover, color="gray", linestyle="--", linewidth=1)
plt.text(primary_crossover, plt.ylim()[1] * 0.9, f"  crossover ≈ {primary_crossover:.0f} B",
         rotation=90, va="top", fontsize=9, color="gray")
plt.xlabel("Payload size (bytes)")
plt.ylabel("Energy per byte (µJ/byte)")
plt.title("Per-byte energy efficiency: ASCON-128 (SW) vs AES-128-GCM (HW)")
plt.legend()
plt.tight_layout()
plt.savefig("figures/energy_per_byte_comparison.png", dpi=200)
plt.close()

# --- Chart 3b: total duty-cycle energy per byte (incl. sleep) ---
plt.figure(figsize=(8, 5))
plt.plot(ascon["size"], ascon["total_duty_cycle_energy_per_byte_uJ"],
         label="ASCON-128 (SW)", color=COLOR_ASCON)
plt.plot(aes["size"], aes["total_duty_cycle_energy_per_byte_uJ"],
         label="AES-128-GCM (HW)", color=COLOR_AES)
plt.xlabel("Payload size (bytes)")
plt.ylabel("Total duty-cycle energy per byte (µJ/byte)")
plt.title("Total duty-cycle (incl. sleep) per-byte energy: ASCON vs AES")
plt.legend()
plt.tight_layout()
plt.savefig("figures/total_duty_cycle_energy_per_byte.png", dpi=200)
plt.close()

# --- Chart 4: mean memory footprint bar chart ---
plt.figure(figsize=(5, 5))
algos = ["ASCON-128\n(SW)", "AES-128-GCM\n(HW)"]
mem_means = [ascon["mean_mem"].mean(), aes["mean_mem"].mean()]
bars = plt.bar(algos, mem_means, color=[COLOR_ASCON, COLOR_AES])
plt.ylabel("Mean memory footprint (bytes)")
plt.title("Memory footprint comparison")
for b, v in zip(bars, mem_means):
    plt.text(b.get_x() + b.get_width() / 2, v, f"{v:.0f}", ha="center", va="bottom")
plt.tight_layout()
plt.savefig("figures/memory_footprint_comparison.png", dpi=200)
plt.close()

# --- Chart 5: regression fit overlay (time and energy) ---
from scipy.stats import linregress

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
for label, df, color in [("ASCON-128", ascon, COLOR_ASCON), ("AES-128-GCM", aes, COLOR_AES)]:
    lr = linregress(df["size"], df["mean_time"])
    axes[0].scatter(df["size"], df["mean_time"], s=8, color=color, alpha=0.5)
    axes[0].plot(df["size"], lr.intercept + lr.slope * df["size"],
                 color=color, label=f"{label} (R²={lr.rvalue**2:.3f})")

    lr_e = linregress(df["size"], df["energy_uJ"])
    axes[1].scatter(df["size"], df["energy_uJ"], s=8, color=color, alpha=0.5)
    axes[1].plot(df["size"], lr_e.intercept + lr_e.slope * df["size"],
                 color=color, label=f"{label} (R²={lr_e.rvalue**2:.3f})")

axes[0].set_xlabel("Payload size (bytes)")
axes[0].set_ylabel("Mean execution time (µs)")
axes[0].set_title("Linear scaling: time vs size")
axes[0].legend()

axes[1].set_xlabel("Payload size (bytes)")
axes[1].set_ylabel("Energy per operation (µJ)")
axes[1].set_title("Linear scaling: energy vs size")
axes[1].legend()

plt.tight_layout()
plt.savefig("figures/regression_scaling_overlay.png", dpi=200)
plt.close()

print("Step 10: saved 6 figures to figures/")
print(" - execution_time_scaling.png")
print(" - throughput_scaling.png")
print(" - energy_per_byte_comparison.png")
print(" - total_duty_cycle_energy_per_byte.png")
print(" - memory_footprint_comparison.png")
print(" - regression_scaling_overlay.png")
