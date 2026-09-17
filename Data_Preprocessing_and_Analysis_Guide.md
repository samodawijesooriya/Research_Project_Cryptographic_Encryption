# Data Pre-Processing & Analysis Guide
## ASCON-128 (software) vs AES-128-GCM (hardware) on ESP32 — Energy-Centric Duty-Cycle Study

This guide turns the raw serial logs described in your methodology (Chapter 3) into the
tables, charts, and statistical tests needed for Chapter 4 (Results) and Chapter 5
(Conclusion). It is written against the **actual structure of `benchmark_raw_log_ASCON1.txt`**
so you can run it immediately on ASCON, then re-run the identical pipeline on AES the
moment that log is ready.

---

## 0. What you currently have

| File | Rows | Notes |
|---|---|---|
| `benchmark_raw_log_ASCON1.txt` | 65,506 | Newline-delimited JSON (NDJSON), one line per single ENCRYPT_AND_MEASURE trial |
| `benchmark_raw_log_stats_ASCON1.txt` | — | Referenced but not currently in this upload — re-check this if it's meant to hold pre-computed statistics; the steps below assume you are working **only from the raw log** |

Each line looks like:
```json
{"id":101,"algo":"ASCON-128","size":16,"time_us":1363,"heap_delta":4444,
 "heap_peak_used":2864,"stack_peak_used":0,"stack_used":80,
 "current_before":-17.3,"current_after":-17.1,
 "power_before":0,"power_after":78,"power_delta":78}
```

Field mapping to your methodology (Section 3.5):
| Field | Meaning | Metric it feeds |
|---|---|---|
| `size` | payload size in bytes (16 → 1600, step 16 ⇒ 100 levels, matches `Size = 16*j`) | x-axis for all scaling analysis |
| `time_us` | execution time of one ENCRYPT_AND_MEASURE call | 3.5.1 Execution Time, 3.5.2 Throughput |
| `heap_delta`, `heap_peak_used`, `stack_used`, `stack_peak_used` | memory footprint | 3.5.4 Memory Footprint |
| `current_before/after`, `power_before/after`, `power_delta` | INA219 readings around the encrypt call | 3.5.3 Power Consumption |
| `id` | trial identifier (not a clean 1–50,000 sequence — see §1.2) | used for de-duplication |

**Important — this log only covers the active `ENCRYPT_AND_MEASURE` phase.** Your
methodology's `SLEEP_AND_MEASURE` routine (60 s deep sleep + wake + reconnect) is a
*separate* measurement stage in Figure 1. If you have (or plan to log) a second file for
that stage, it needs to be merged in before you can report true **per-duty-cycle** energy
(Objective 1 asks for *total duty-cycle energy*, not just active-phase energy). Section 5
below shows exactly where that merge happens.

### 0.1 Two known data-quality issues found on inspection (handle both — see §2)

1. **Incomplete/duplicated iterations, not just duplicate IDs.** The raw `id` field
   repeats 1–15× per payload size, but a plain "dedup by id" is unreliable — some `id`
   values collide across genuinely different sweeps. The correct unit of cleaning is the
   **iteration** (one full 100-payload-size sweep). Segmenting the log this way finds
   **699 candidate iterations, of which 561 are fully complete** (all 100 sizes present
   with no gaps); the other 138 are partial sweeps from resets/reboots and should be
   discarded outright rather than repaired. After keeping only complete iterations and
   de-duplicating within each, every payload size ends up with exactly the same sample
   count (561, or subsample to 500 if you want to match the pre-registered design) —
   see Step 2.2.
2. **Negative / non-physical current readings.** ~21% of rows have a negative
   `current_before` or `current_after`. These aren't random noise — they cluster tightly
   around −5.5 to −6 mA, which is the signature of an INA219 **zero-offset calibration
   error**, not scattered ADC jitter. The fix is to estimate and subtract that constant
   offset (rather than simply flooring at zero, which would discard the signal and bias
   near-zero readings) — see Step 2.3.

---

## 1. Environment setup

```bash
pip install pandas numpy scipy matplotlib --break-system-packages
```

Recommended structure:
```
project/
├── raw/
│   ├── benchmark_raw_log_ASCON1.txt
│   └── benchmark_raw_log_AES1.txt        # when ready
├── processed/
│   ├── ascon_clean.csv
│   ├── aes_clean.csv
│   ├── ascon_summary_by_size.csv
│   └── aes_summary_by_size.csv
├── scripts/
│   ├── 01_parse_and_clean.py
│   ├── 02_summarize.py
│   ├── 03_compare_and_test.py
│   └── 04_plots.py
└── figures/
```

---

## 2. Step-by-step pre-processing (run once per algorithm)

### Step 2.1 — Parse the NDJSON log safely
```python
import json, pandas as pd

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
                bad += 1   # truncated/garbled serial line
    df = pd.DataFrame(rows)
    print(f"{algo_label}: parsed {len(df)} rows, skipped {bad} malformed lines")
    return df

ascon = load_raw("raw/benchmark_raw_log_ASCON1.txt", "ASCON-128")
```
Record the "skipped malformed lines" count in your thesis (Section 3.6 mentions a
"cleaning" step — this is the first entry in that log).

### Step 2.2 — Keep only complete iterations (the correct fix, not a plain id-dedup)

Testing this on your actual file confirms your instinct: `id` is **not** a reliable
dedup key on its own — some `id` collisions turn out to sit in different sweeps entirely
(the counter isn't perfectly monotonic across resets), so dropping by `id` alone either
under- or over-corrects. The reliable unit of cleaning is the **iteration** — one full
inner-loop sweep of `j = 1..100` (payload sizes 16 → 1600) — because your firmware's
outer loop (Figure 1) is defined at that granularity, not at the level of an individual id.

**Step 2.2a — reconstruct iteration boundaries from the payload-size sequence.**
Since `size` counts up 16 → 1600 within a sweep and then drops back to 16 when the next
outer-loop iteration starts, a drop in `size` marks a new iteration. This must be done on
the file in its **original recorded order** (do not sort by `id` or `size` first):
```python
def segment_iterations(df):
    df = df.reset_index(drop=True)
    iter_id, iter_ids, prev_size = 0, [], None
    for size in df["size"]:
        if prev_size is not None and size < prev_size:
            iter_id += 1          # payload size dropped -> new sweep began
        iter_ids.append(iter_id)
        prev_size = size
    df["iteration"] = iter_ids
    return df

ascon = segment_iterations(ascon)
print("iterations detected:", ascon["iteration"].nunique())
```
On your ASCON log this detects **699 candidate iterations** (more than the intended 500 —
expected, since some sweeps are only partial fragments from resets/reboots, not genuine
extra runs).

**Step 2.2b — remove true retransmission duplicates within each iteration**, keeping the
first reading for a given `(iteration, size)` pair:
```python
ascon_dedup = ascon.drop_duplicates(subset=["iteration", "size"], keep="first")
```

**Step 2.2c — discard incomplete iterations.** A genuinely completed iteration must
contain all 100 unique payload sizes (16, 32, …, 1600) exactly once. Keep only those:
```python
expected_sizes = set(range(16, 1601, 16))
sizes_per_iter = ascon_dedup.groupby("iteration")["size"].apply(set)
complete_iters = [it for it, s in sizes_per_iter.items() if s == expected_sizes]

ascon_complete = ascon_dedup[ascon_dedup["iteration"].isin(complete_iters)].copy()
print(f"{len(complete_iters)} complete iterations kept "
      f"out of {ascon_dedup['iteration'].nunique()} detected")
print(f"{len(ascon_complete)} rows retained")
```
**Validated result on your ASCON file:** this yields **561 complete iterations**, each
contributing **exactly one** row per payload size — i.e. **561 clean samples for every
one of the 100 payload sizes**, with zero variance in the per-size sample count. The
remaining 138 detected sweeps are genuinely incomplete (mostly missing only 1–4 of the
100 sizes) and are correctly discarded rather than padded or estimated.

Because 561 > 500, you have two defensible options — pick one and state it:
- **Use all 561** (more statistical power, simplest to justify: "every complete,
  uncorrupted sweep was retained").
- **Subsample to exactly 500** (first 500 complete iterations in chronological order) if
  you want the reported sample size to match the pre-registered design exactly:
  ```python
  first_500 = sorted(complete_iters)[:500]
  ascon_complete = ascon_dedup[ascon_dedup["iteration"].isin(first_500)].copy()
  ```
Report whichever you pick, and the exact complete-iteration count, in your methodology —
this replaces the "500 repeats" figure with the true, verified figure.

### Step 2.3 — Fix the negative current/power readings with a zero-offset calibration

Checking the negative values in your (now iteration-cleaned) data shows they are **not**
random symmetric noise — they cluster tightly: the middle 50% of negative
`current_before` readings sits between −6.5 mA and −5.2 mA (median ≈ −5.8 mA), and
`current_after` behaves almost identically (median ≈ −5.6 mA). A small number of much
larger negative spikes also exist (down to −76 mA / −99 mA) — those are separate,
genuine noise transients, not part of the offset.

That tight, repeatable cluster around −5.5 to −6 mA is exactly what a **sensor zero-offset
error** looks like: the INA219's true "zero current" reading is calibrated a few mA below
actual zero, so every reading — including the physically-valid positive ones — is shifted
down by a constant amount. Simply flooring/clipping at zero (as a first pass might suggest)
throws away that signal and biases every low-current reading upward by an inconsistent
amount depending on how close it is to zero. **Calibrating out the offset, then clipping
only the genuine outlier spikes, is the more defensible fix** — and it's directly
supported by your own literature (Section 2.4.2, INA219 zero-offset behaviour is a known
characteristic of the sensor).

**Step 2.3a — estimate the offset from the data itself.**
Use the median of the negative-reading cluster (robust to the rare large spikes) as the
offset estimate, separately for `current_before` and `current_after`, then average them
into one shared calibration constant:
```python
neg_before = ascon_complete.loc[ascon_complete["current_before"] < 0, "current_before"]
neg_after  = ascon_complete.loc[ascon_complete["current_after"]  < 0, "current_after"]

offset_mA = np.mean([abs(neg_before.median()), abs(neg_after.median())])
print(f"Estimated sensor zero-offset: {offset_mA:.2f} mA")   # ~5.7 mA on your ASCON data
```

**Step 2.3b — apply the correction to current, then clip the rare remaining outliers.**
```python
ascon_complete["current_before_corr"] = (ascon_complete["current_before"] + offset_mA).clip(lower=0)
ascon_complete["current_after_corr"]  = (ascon_complete["current_after"]  + offset_mA).clip(lower=0)

n_still_neg = ((ascon_complete["current_before"] + offset_mA < 0) |
               (ascon_complete["current_after"]  + offset_mA < 0)).sum()
print(f"{n_still_neg} rows still negative after offset correction — these are genuine "
      f"noise spikes, now clipped to 0")
```

**Step 2.3c — recompute power from the corrected current, using the *measured* bus
voltage rather than the nominal 5V rail.** Your device's `power_before`/`power_after`
fields were computed by the INA219 from the same miscalibrated current, so they carry the
identical offset — recomputing from `V × I` (Equation 2) with the corrected current is
more consistent than trying to offset-correct the power fields separately. The regulated
supply is nominally 5V, but the INA219 measures the actual bus voltage after the shunt
resistor's drop, so back it out from your own valid data instead of assuming 5.000V:
```python
mask_valid = ascon_complete["current_before"] > 20   # clearly-active, high-confidence rows
v_bus = (ascon_complete.loc[mask_valid, "power_before"]
         / ascon_complete.loc[mask_valid, "current_before"]).median()
print(f"Empirically measured bus voltage: {v_bus:.3f} V")   # ≈ 4.67 V on your ASCON data

ascon_complete["power_before_corr"] = ascon_complete["current_before_corr"] * v_bus
ascon_complete["power_after_corr"]  = ascon_complete["current_after_corr"]  * v_bus
ascon_complete["power_delta_corr"]  = (ascon_complete["power_after_corr"]
                                        - ascon_complete["power_before_corr"])
```
Report both the offset (mA) and the measured bus voltage (V) in your methodology as
calibration constants — they're a legitimate, auditable correction, not an arbitrary data
edit, and applying the *same two constants* to the AES log keeps both datasets on an
identical footing.

If you'd rather keep this simple for a first pass and accept some information loss,
**Option B (fallback): floor at zero without offset correction** — but note this discards
the systematic-offset signal identified above and slightly biases low-power readings:
```python
for col in ["current_before", "current_after", "power_before", "power_after"]:
    ascon_complete[col] = ascon_complete[col].clip(lower=0)
```

### Step 2.4 — Outlier removal per (algo, size) group
Per your Section 3.7.1, use spike removal before computing summary stats. IQR-based
trimming on `time_us` (and separately on the corrected power) is a defensible,
referee-friendly method, run only on the complete-iteration, offset-corrected data from
Steps 2.2–2.3:
```python
def remove_outliers_iqr(df, group_col, value_col, k=1.5):
    def trim(g):
        q1, q3 = g[value_col].quantile([0.25, 0.75])
        iqr = q3 - q1
        lo, hi = q1 - k*iqr, q3 + k*iqr
        return g[(g[value_col] >= lo) & (g[value_col] <= hi)]
    return df.groupby(group_col, group_keys=False).apply(trim)

ascon_trimmed = remove_outliers_iqr(ascon_complete, "size", "time_us")
```
Log how many rows were trimmed per payload size — small, uniform trimming (a few %) is
expected; if one payload size loses a disproportionate number of rows, flag it for manual
inspection (could indicate a genuine bimodal effect, e.g., a Wi-Fi retry event).

### Step 2.5 — Derive per-trial metrics
```python
ascon_trimmed["time_s"] = ascon_trimmed["time_us"] / 1e6

# Use the offset-corrected, recomputed power from Step 2.3c — not the device's raw field.
ascon_trimmed["power_mW"] = ascon_trimmed["power_delta_corr"]

# Total memory footprint proxy
ascon_trimmed["mem_total"] = ascon_trimmed["heap_peak_used"] + ascon_trimmed["stack_used"]
```

### Step 2.6 — Save the cleaned trial-level dataset
```python
ascon_trimmed.to_csv("processed/ascon_clean.csv", index=False)
```
This CSV is your Section 3.6 "structured file" — the auditable, cleaned dataset all
downstream stats/plots are built from. Keep a small log (even a plain text note) of the
row counts at each stage — raw → iteration-complete → offset-corrected → outlier-trimmed
— for both algorithms; that progression is worth an appendix table in the thesis.

---

## 3. Summary statistics per payload size

For **each** payload size (100 levels, 16–1600 bytes) and **each** metric
(`time_us`, `power_mW`, `mem_total`), compute:

```python
import numpy as np
from scipy import stats

def summarize(df, value_col):
    def agg(g):
        n = len(g)
        mean = g[value_col].mean()
        median = g[value_col].median()
        sd = g[value_col].std(ddof=1)
        se = sd / np.sqrt(n)
        ci95 = stats.t.ppf(0.975, df=n-1) * se
        return pd.Series({
            "n": n, "mean": mean, "median": median, "std": sd,
            "ci95_low": mean - ci95, "ci95_high": mean + ci95
        })
    return df.groupby("size").apply(agg).reset_index()

time_summary  = summarize(ascon_trimmed, "time_us")
power_summary = summarize(ascon_trimmed, "power_mW")
mem_summary   = summarize(ascon_trimmed, "mem_total")
```

### Throughput (Equation 1), computed from the grouped mean — not per-row
```python
time_summary["throughput_Bps"] = time_summary["size"] / (time_summary["mean"] / 1e6)
```

### Per-byte energy (Objective 1 & 2)
Energy per operation (µJ) = power (mW) × time (ms); per-byte = energy / payload size:
```python
merged = time_summary.merge(power_summary, on="size", suffixes=("_time", "_power"))
merged["energy_uJ"] = merged["mean_power"] * (merged["mean_time"] / 1000)   # mW * ms = µJ
merged["energy_per_byte_uJ"] = merged["energy_uJ"] / merged["size"]
merged.to_csv("processed/ascon_summary_by_size.csv", index=False)
```

### Regression / scaling analysis (Section 3.7.2)
```python
from scipy.stats import linregress

lr_time = linregress(merged["size"], merged["mean_time"])
print(f"time_us ~ size:   slope={lr_time.slope:.4f}, R²={lr_time.rvalue**2:.4f}")

lr_energy = linregress(merged["size"], merged["energy_uJ"])
print(f"energy ~ size:    slope={lr_energy.slope:.4f}, R²={lr_energy.rvalue**2:.4f}")
```
R² close to 1 confirms the "linear runtime scaling" behaviour your literature review
attributes to ASCON's sponge duplexing (Section 2.2.5) — this is a nice direct link back
to your lit review when you write the discussion.

---

## 4. Repeat identically for AES-128-GCM

Once `benchmark_raw_log_AES1.txt` is ready, run **Steps 2.1–2.6 and Section 3** unchanged
(just swap the input path and output filenames to `aes_clean.csv` /
`aes_summary_by_size.csv`). Using an identical pipeline for both algorithms is what makes
the comparison in Section 5 statistically valid — don't hand-tune cleaning thresholds
differently between the two datasets.

One AES-specific check to add during Step 2.1: your methodology fixes a 12-byte nonce for
AES vs 16-byte for ASCON (Section 3.3.3) — confirm the AES log's `id`/`size` structure
still spans the same 100 payload levels (16–1600 bytes) so the two datasets are directly
joinable on `size`.

---

## 5. Adding sleep-phase energy from the datasheet (no device measurement needed)

Since the sleep-phase current isn't something you're measuring on the device, use the
manufacturer's **ESP32-WROOM-32E datasheet** deep-sleep current figure rather than a
literature estimate — the two are usually close (your own lit review cites 5–10 µA in
Section 3.4.1 and 10–150 µA in Section 2.5.2, depending on which peripherals stay
powered), but the datasheet value is the one a reviewer will expect you to cite and is
specific to *your* exact module (WROOM-32E, not a generic ESP32-C3/S3 figure).

Look up (from the Espressif ESP32-WROOM-32E / ESP32 datasheet, "Current Consumption" or
"Power Modes" table):
- `I_sleep` — deep-sleep current draw (µA), for the specific wake source you use (RTC
  timer only vs. RTC + ULP coprocessor draw slightly different currents)
- The supply/domain voltage during deep sleep (typically 3.3V for the RTC domain, since
  the main 5V-side buck converter itself is not what's drawing current at that point)

Because sleep duration (60 s) and sleep current are **both fixed regardless of payload
size**, sleep energy is a single constant added to every row — it does not change the
*shape* of the per-byte energy curve, but it does change the **absolute totals** you
report for Objective 1 ("total duty-cycle energy"):

```python
I_SLEEP_uA = 10      # <- replace with the exact datasheet figure you cite
V_SLEEP    = 3.3      # <- RTC domain voltage per datasheet
T_SLEEP_S  = 60

sleep_energy_uJ = V_SLEEP * (I_SLEEP_uA) * T_SLEEP_S   # µW * s = µJ

merged["total_duty_cycle_energy_uJ"] = merged["energy_uJ"] + sleep_energy_uJ
merged["total_duty_cycle_energy_per_byte_uJ"] = (
    merged["total_duty_cycle_energy_uJ"] / merged["size"]
)
```
State the exact datasheet current/voltage figures you used, and the datasheet
revision/date, in your methodology text — that's the citation a reviewer will look for
next to Equation 2. If your two algorithms are tested with identical sleep configuration
(same wake source, same 60 s), this constant is identical for both ASCON and AES, so it
only shifts the absolute energy values, not the comparative conclusion — but Objective 1
explicitly asks for the total, so don't drop it from the final reported numbers.

If you later decide you *do* want a wake-up/reconnect transient captured empirically
(the brief spike as Wi-Fi/RTC come back up, which the datasheet won't give you a number
for), that one component would still need to come from the device rather than the
datasheet — the steady-state 60 s deep-sleep current is the only piece the datasheet
cleanly replaces.

---

## 6. Comparative statistics: ASCON vs AES

Do this only after both `ascon_clean.csv` and `aes_clean.csv` exist.

```python
ascon = pd.read_csv("processed/ascon_clean.csv")
aes   = pd.read_csv("processed/aes_clean.csv")
```

### 6.1 One-tailed independent t-tests per payload size (Section 3.7.2, α = 0.01)
```python
from scipy.stats import ttest_ind

results = []
for size, g_a in ascon.groupby("size"):
    g_h = aes[aes["size"] == size]
    if len(g_h) == 0:
        continue
    t_stat, p_two = ttest_ind(g_a["time_us"], g_h["time_us"], equal_var=False)
    p_one = p_two / 2 if t_stat > 0 else 1 - p_two / 2   # direction: ASCON slower on time?
    results.append({"size": size, "t_stat": t_stat, "p_one_tailed": p_one,
                     "significant_at_0.01": p_one < 0.01})
ttest_df = pd.DataFrame(results)
```
Repeat the same block for `power_mW` and `energy_per_byte_uJ`. Report the *proportion* of
payload sizes where the difference is significant, not just one aggregate p-value —
your 100-payload design is built for exactly this kind of scaling comparison.

### 6.2 Break-even / crossover payload size (Objective 3)
```python
compare = merged_ascon_summary.merge(merged_aes_summary, on="size",
                                      suffixes=("_ascon", "_aes"))
compare["ascon_minus_aes_energy"] = (
    compare["energy_per_byte_uJ_ascon"] - compare["energy_per_byte_uJ_aes"]
)
# Crossover = sign change in the difference column
sign_changes = compare[
    (compare["ascon_minus_aes_energy"].shift(1) * compare["ascon_minus_aes_energy"]) < 0
]
print("Approximate crossover payload size(s):", sign_changes["size"].tolist())
```
If ASCON's per-byte energy starts above AES's and drops below it (or vice versa) as
payload grows, the row(s) returned here bracket your reported break-even point —
interpolate linearly between the two bracketing sizes for a precise byte figure.

### 6.3 Memory footprint comparison
Same `summarize()` → merge → compare pattern as time/power, using `mem_total`. Since
AES-GCM has TLS/mbedTLS context overhead the ASCON software implementation may not,
this is often where the two algorithms diverge most clearly regardless of payload size —
worth a dedicated bar chart (constant-vs-size) rather than only a scaling line chart.

---

## 7. Visualizations to produce

| Chart | X | Y | Purpose |
|---|---|---|---|
| Line | payload size (16–1600B) | mean execution time (µs), ASCON vs AES, with 95% CI band | shows scaling behaviour |
| Line | payload size | throughput (B/s) | shows where hardware acceleration pulls ahead (or doesn't) |
| Line | payload size | energy per byte (µJ/byte) | **this is the chart that answers the core research question** — mark the crossover point from §6.2 |
| Bar | algorithm | mean memory footprint (bytes) | discrete comparison, Section 2.4.1 style |
| Scatter/line | payload size | R² regression fit overlay | supports the linear-scaling claim from Section 2.2.5 |

```python
import matplotlib.pyplot as plt

plt.figure()
plt.plot(ascon_summary["size"], ascon_summary["energy_per_byte_uJ"], label="ASCON-128 (SW)")
plt.plot(aes_summary["size"], aes_summary["energy_per_byte_uJ"], label="AES-128-GCM (HW)")
plt.xlabel("Payload size (bytes)")
plt.ylabel("Energy per byte (µJ/byte)")
plt.legend()
plt.title("Per-byte energy efficiency: software ASCON vs hardware AES")
plt.savefig("figures/energy_per_byte_comparison.png", dpi=200)
```

---

## 8. Mapping results back to your research questions

| Objective / RQ | Where the answer comes from |
|---|---|
| RQ1 — full comparison across power, memory, throughput, execution time, per-byte energy | Section 3 summary tables + Section 7 charts, both algorithms |
| Obj. 1 — total duty-cycle energy incl. HW init overhead | Section 5 merge (encrypt + sleep/wake energy); AES's hardware-engine init cost should show up as a near-constant offset independent of payload size — isolate it by comparing `energy_uJ` at `size→0` (intercept of the regression in §3) |
| Obj. 2 — energy cost per transmitted byte across full duty cycle | `energy_per_byte_uJ` column from Section 5/6 |
| Obj. 3 — conditions where ASCON remains preferable + break-even payload | Section 6.2 crossover analysis, plus segmenting by small (<256B) vs large (>800B) payloads typical of LPWAN vs bulk telemetry |

When you write the conclusion, structure it as: (1) state the crossover payload size and
which regime favors which algorithm, (2) report the t-test significance pattern from §6.1
as your statistical backing, (3) tie back to the literature gap from Section 2.3.4/2.7 —
this is the first study to place these two on the same platform under a uniform per-byte
metric, so your numeric crossover point is itself the novel contribution.

---

## 9. Checklist before running the AES pass

- [ ] AES raw log uses the same JSON schema (`id, algo, size, time_us, heap_delta,
      heap_peak_used, stack_peak_used, stack_used, current_before, current_after,
      power_before, power_after, power_delta`)
- [ ] Same 100 payload levels (16–1600 bytes, step 16)
- [ ] Same iteration-completeness filter, offset-correction, and outlier-trimming rules
      applied (Steps 2.2–2.4), so the two datasets are cleaned identically before comparison
- [ ] Same datasheet-derived sleep current/voltage constants (Section 5) applied to both
      algorithms' totals
- [ ] Record row counts at each cleaning step (raw → iteration-complete → offset-corrected
      → outlier-trimmed) for both algorithms — this table belongs in your methodology or
      appendix as evidence of data quality control
- [ ] Report the calibration constants themselves (offset in mA, measured bus voltage in
      V, datasheet sleep current/voltage) — these are auditable numbers a reviewer can
      check, not just a description of the method
