"""
Runs Steps 1-6 of DATA_ANALYSIS_README.md for both algorithms.

Per Step 3 of the guide, the two calibration constants (offset_mA, v_bus) must
be estimated once and applied identically to both datasets. We estimate them
from the ASCON log's iteration-complete data (Gate 1 output), then reuse the
same constants for AES.
"""
import json
import pandas as pd
from pipeline_common import (
    load_raw, keep_complete_iterations, calibrate_current_power,
    apply_full_outlier_trim, derive_metrics, summarize, run_pipeline
)

SUBSAMPLE_N = None  # use all complete iterations (see stage log for the count)

# --- Step 1-2: get iteration-complete ASCON data to estimate shared calibration constants ---
ascon_raw, ascon_bad = load_raw("raw/benchmark_raw_log_ASCON1.txt", "ASCON-128")
ascon_complete, ascon_gate1 = keep_complete_iterations(ascon_raw, "ASCON-128", subsample_n=SUBSAMPLE_N)

_, gate2_log = calibrate_current_power(ascon_complete, "ASCON-128 (constant estimation)")
SHARED_OFFSET_MA = gate2_log["offset_mA"]
SHARED_V_BUS = gate2_log["v_bus_V"]

print(f"\n=== Shared calibration constants (Step 3, applied to BOTH algorithms) ===")
print(f"offset_mA = {SHARED_OFFSET_MA:.4f}")
print(f"v_bus_V   = {SHARED_V_BUS:.4f}\n")

# --- Full pipeline, both algorithms, identical constants ---
ascon_clean, ascon_summary, ascon_log = run_pipeline(
    "raw/benchmark_raw_log_ASCON1.txt", "ASCON-128", "ascon",
    subsample_n=SUBSAMPLE_N, offset_mA=SHARED_OFFSET_MA, v_bus=SHARED_V_BUS
)

aes_clean, aes_summary, aes_log = run_pipeline(
    "raw/benchmark_raw_log_AES1.txt", "AES-128-GCM", "aes",
    subsample_n=SUBSAMPLE_N, offset_mA=SHARED_OFFSET_MA, v_bus=SHARED_V_BUS
)

# --- Data-quality appendix table (row counts per stage) ---
stage_table = pd.DataFrame([ascon_log, aes_log])
stage_table.to_csv("processed/data_quality_stage_log.csv", index=False)

calibration_constants = {
    "offset_mA": SHARED_OFFSET_MA,
    "v_bus_V": SHARED_V_BUS,
}
with open("processed/calibration_constants.json", "w") as f:
    json.dump(calibration_constants, f, indent=2)

print("\n=== Row-count-per-stage appendix table ===")
print(stage_table.to_string(index=False))
print(f"\nSaved: processed/data_quality_stage_log.csv")
print(f"Saved: processed/calibration_constants.json")
print(f"Saved: processed/ascon_clean.csv, processed/aes_clean.csv")
print(f"Saved: processed/ascon_summary_by_size.csv, processed/aes_summary_by_size.csv")
