"""
Shared pre-processing pipeline for ASCON-128 vs AES-128-GCM benchmark logs.
Implements Steps 1-6 of DATA_ANALYSIS_README.md identically for both algorithms.
"""
import json
import numpy as np
import pandas as pd
from scipy import stats

EXPECTED_SIZES = set(range(16, 1601, 16))


def load_raw(path, algo_label):
    rows, bad = [], 0
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                bad += 1
    df = pd.DataFrame(rows)
    print(f"[{algo_label}] Step 1: parsed {len(df)} rows, skipped {bad} malformed lines")
    return df, bad


def segment_iterations(df):
    df = df.reset_index(drop=True)
    iter_id, iter_ids, prev_size = 0, [], None
    for size in df["size"]:
        if prev_size is not None and size < prev_size:
            iter_id += 1
        iter_ids.append(iter_id)
        prev_size = size
    df = df.copy()
    df["iteration"] = iter_ids
    return df


def keep_complete_iterations(df, algo_label, subsample_n=None):
    df = segment_iterations(df)
    n_candidate = df["iteration"].nunique()

    df_dedup = df.drop_duplicates(subset=["iteration", "size"], keep="first")

    sizes_per_iter = df_dedup.groupby("iteration")["size"].apply(set)
    complete_iters = [it for it, s in sizes_per_iter.items() if s == EXPECTED_SIZES]

    if subsample_n is not None:
        complete_iters = sorted(complete_iters)[:subsample_n]

    df_complete = df_dedup[df_dedup["iteration"].isin(complete_iters)].copy()

    print(f"[{algo_label}] Step 2: {n_candidate} candidate iterations detected, "
          f"{len(complete_iters)} complete iterations kept, "
          f"{len(df_complete)} rows retained")

    per_size_counts = df_complete.groupby("size").size()
    assert per_size_counts.nunique() == 1, (
        f"[{algo_label}] Per-size sample counts are not uniform after cleaning: "
        f"{per_size_counts.unique()}"
    )

    return df_complete, {
        "candidate_iterations": n_candidate,
        "complete_iterations": len(complete_iters),
        "rows_retained": len(df_complete),
        "n_per_size": int(per_size_counts.iloc[0]),
    }


def calibrate_current_power(df, algo_label, offset_mA=None, v_bus=None):
    neg_before = df.loc[df["current_before"] < 0, "current_before"]
    neg_after = df.loc[df["current_after"] < 0, "current_after"]
    n_neg = len(neg_before) + len(neg_after)

    if offset_mA is None:
        offset_mA = float(np.mean([abs(neg_before.median()), abs(neg_after.median())]))

    df = df.copy()
    df["current_before_corr"] = (df["current_before"] + offset_mA).clip(lower=0)
    df["current_after_corr"] = (df["current_after"] + offset_mA).clip(lower=0)

    n_still_neg = int(((df["current_before"] + offset_mA < 0) |
                        (df["current_after"] + offset_mA < 0)).sum())

    if v_bus is None:
        mask_valid = df["current_before"] > 20
        v_bus = float((df.loc[mask_valid, "power_before"]
                        / df.loc[mask_valid, "current_before"]).median())

    df["power_before_corr"] = df["current_before_corr"] * v_bus
    df["power_after_corr"] = df["current_after_corr"] * v_bus
    df["power_delta_corr"] = df["power_after_corr"] - df["power_before_corr"]

    print(f"[{algo_label}] Step 3: {n_neg} negative current readings found "
          f"(before+after combined); offset={offset_mA:.3f} mA; "
          f"v_bus={v_bus:.3f} V; {n_still_neg} rows still negative after "
          f"correction (clipped to 0)")

    return df, {"offset_mA": offset_mA, "v_bus_V": v_bus,
                 "n_negative_raw": n_neg, "n_still_negative_after_offset": n_still_neg}


def remove_outliers_iqr(df, algo_label, value_col, group_col="size", k=1.5):
    def trim(g):
        q1, q3 = g[value_col].quantile([0.25, 0.75])
        iqr = q3 - q1
        lo, hi = q1 - k * iqr, q3 + k * iqr
        return g[(g[value_col] >= lo) & (g[value_col] <= hi)]

    before_counts = df.groupby(group_col).size()
    trimmed = df.groupby(group_col, group_keys=False).apply(trim, include_groups=False)
    trimmed = df.loc[trimmed.index] if not trimmed.empty else trimmed
    after_counts = trimmed.groupby(group_col).size()

    removed_per_size = (before_counts - after_counts).fillna(before_counts)
    print(f"[{algo_label}] Step 4 ({value_col}): trimmed "
          f"{int(removed_per_size.sum())} rows total "
          f"(min/max per-size removed: {int(removed_per_size.min())}/"
          f"{int(removed_per_size.max())})")

    return trimmed, removed_per_size


def apply_full_outlier_trim(df, algo_label, k=1.5):
    trimmed, removed_time = remove_outliers_iqr(df, algo_label, "time_us", k=k)
    trimmed, removed_power = remove_outliers_iqr(trimmed, algo_label, "power_delta_corr", k=k)
    return trimmed, removed_time, removed_power


def derive_metrics(df):
    df = df.copy()
    df["time_s"] = df["time_us"] / 1e6
    df["power_mW"] = df["power_delta_corr"]
    df["mem_total"] = df["heap_peak_used"] + df["stack_used"]
    return df


def summarize(df, value_col, group_col="size"):
    def agg(g):
        n = len(g)
        mean = g[value_col].mean()
        median = g[value_col].median()
        sd = g[value_col].std(ddof=1)
        se = sd / np.sqrt(n) if n > 1 else np.nan
        ci95 = stats.t.ppf(0.975, df=n - 1) * se if n > 1 else np.nan
        return pd.Series({
            "n": n, "mean": mean, "median": median, "std": sd,
            "ci95_low": mean - ci95, "ci95_high": mean + ci95
        })
    return df.groupby(group_col).apply(agg, include_groups=False).reset_index()


def run_pipeline(raw_path, algo_label, out_prefix, subsample_n=None,
                  offset_mA=None, v_bus=None, k=1.5):
    """Runs Steps 1-6 end to end. Returns (clean_df, summary_df, stage_log_dict)."""
    stage_log = {"algo": algo_label}

    df_raw, n_bad = load_raw(raw_path, algo_label)
    stage_log["raw_rows"] = len(df_raw)
    stage_log["malformed_lines"] = n_bad

    df_complete, gate1_log = keep_complete_iterations(df_raw, algo_label, subsample_n=subsample_n)
    stage_log.update({f"gate1_{k_}": v_ for k_, v_ in gate1_log.items()})

    df_calib, gate2_log = calibrate_current_power(df_complete, algo_label,
                                                    offset_mA=offset_mA, v_bus=v_bus)
    stage_log.update({f"gate2_{k_}": v_ for k_, v_ in gate2_log.items()})

    df_trimmed, removed_time, removed_power = apply_full_outlier_trim(df_calib, algo_label, k=k)
    stage_log["gate3_rows_after_trim"] = len(df_trimmed)
    stage_log["gate3_rows_removed_total"] = stage_log["gate1_rows_retained"] - len(df_trimmed)

    df_final = derive_metrics(df_trimmed)
    df_final.to_csv(f"processed/{out_prefix}_clean.csv", index=False)
    print(f"[{algo_label}] Step 5: saved processed/{out_prefix}_clean.csv "
          f"({len(df_final)} rows)")

    time_summary = summarize(df_final, "time_us")
    power_summary = summarize(df_final, "power_mW")
    mem_summary = summarize(df_final, "mem_total")

    time_summary["throughput_Bps"] = time_summary["size"] / (time_summary["mean"] / 1e6)

    merged = time_summary.merge(power_summary, on="size", suffixes=("_time", "_power"))
    merged = merged.merge(mem_summary.rename(
        columns={c: f"{c}_mem" for c in mem_summary.columns if c != "size"}), on="size")
    merged["energy_uJ"] = merged["mean_power"] * (merged["mean_time"] / 1000)
    merged["energy_per_byte_uJ"] = merged["energy_uJ"] / merged["size"]

    merged.to_csv(f"processed/{out_prefix}_summary_by_size.csv", index=False)
    print(f"[{algo_label}] Step 6: saved processed/{out_prefix}_summary_by_size.csv")

    return df_final, merged, stage_log
