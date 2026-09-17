# Data Analysis — Step-by-Step Guide

**Project:** An Energy-Centric Comparative Evaluation of Software-Based vs.
Hardware-Accelerated Cryptography on ESP32 in a Realistic IoT Duty Cycle
**Algorithms compared:** ASCON-128 (software) vs AES-128-GCM (hardware-accelerated)

This README is the step-by-step procedure for turning the raw serial benchmark logs
produced by the firmware in `main/` into the results reported in Chapter 4 (Results) of
the dissertation. It is a condensed, action-oriented version of
[Analysis_Design.md](Analysis_Design.md) (which explains *why* each step exists) and the
executable pipeline in
[Data_Preprocessing_and_Analysis_Guide.md](Data_Preprocessing_and_Analysis_Guide.md)
(which has the runnable Python for every step below).

Every step below is tied back to the dissertation's **Research Question** and three
**Objectives** (Chapter 1, §1.7–1.8) so it is traceable, when writing Chapter 4, exactly
which analysis step answers which objective.

---

## 0. What this analysis needs to answer

**RQ:** How does hardware-accelerated AES-128-GCM compare with software-based
ASCON-128 in power consumption, memory usage, throughput, execution time, and
per-byte energy efficiency, across a full IoT duty cycle
(Sleep → Wake → Sense → Encrypt → Transmit → Sleep)?

- **Objective 1** — total duty-cycle energy (incl. hardware-engine init overhead) per algorithm
- **Objective 2** — energy cost per transmitted byte across the full duty cycle
- **Objective 3** — conditions/payload regime where ASCON remains preferable, incl. the break-even (crossover) payload size

Every step from here is done **twice, identically** — once for the ASCON-128 log, once
for the AES-128-GCM log — so the two datasets stay directly comparable.

---

## Step 1 — Collect and inventory the raw logs

Input: `benchmark_raw_log_<ALGO>.txt`, one NDJSON line per trial, produced by
`output_metrics()` in `main/power_monitor.c` (see the `Sample Benchmark Data` line in
[README.md](README.md) for the exact schema).

- [ ] Confirm both algorithm logs exist and use the identical JSON schema (`id, algo,
      size, time_us, heap_delta_bytes, heap_peak_used_bytes, stack_peak_used_bytes,
      stack_used_bytes, current_before_mA, current_after_mA, power_before_mW,
      power_after_mW, power_delta_mW`).
- [ ] Confirm both logs cover the same 100 payload levels (16–1600 bytes, step 16).
- [ ] Parse each log line as JSON; count and log how many lines fail to parse
      (truncated/garbled serial output) — this count is the first entry in the Chapter 3
      "data cleaning" log.

## Step 2 — Reconstruct and validate complete iterations

Do **not** deduplicate by the trial `id` field alone — the counter is not guaranteed
monotonic across device resets, so `id` collisions can span different sweeps.

- [ ] Segment the log into iterations: a drop in `size` (from ~1600 back to 16) marks the
      start of a new outer-loop sweep. Do this on the log in original recorded order.
- [ ] Within each iteration, drop duplicate `(iteration, size)` rows, keeping the first.
- [ ] Keep only iterations containing **all 100 distinct payload sizes exactly once**.
      Discard partial iterations (resets/reboots mid-sweep) outright — do not repair or
      interpolate them.
- [ ] Record: candidate iterations detected, complete iterations kept, rows retained.
      This becomes the row-count-per-stage appendix table required for both algorithms.
- [ ] Decide and document whether to use **all complete iterations** or **subsample to a
      fixed count** to match the pre-registered design — apply the same choice to both
      algorithms.

## Step 3 — Calibrate the INA219 current/power readings

- [ ] Check for negative `current_before`/`current_after` values. Confirm they cluster
      tightly (a narrow negative band), which is the signature of a sensor zero-offset
      rather than random noise.
- [ ] Estimate the offset as the mean of the median negative `current_before` and median
      negative `current_after` magnitudes.
- [ ] Add the offset back to every current reading (not only the negative ones), then
      clip the small number of remaining large-magnitude outliers at zero.
- [ ] Recompute power from the corrected current using an empirically measured bus
      voltage (median of `power / current` on clearly-active, high-current rows) — do
      not trust the device's raw `power_before`/`power_after` fields, since they were
      computed from the same miscalibrated current.
- [ ] Record the two calibration constants (offset in mA, measured bus voltage in V) —
      report them in the methodology as auditable figures. Apply the **same two
      constants** to both algorithms' logs.

## Step 4 — Remove residual outliers

- [ ] Only after Steps 2–3, apply IQR-based trimming (k = 1.5) to `time_us` and the
      corrected power, grouped by payload size.
- [ ] Log how many rows were trimmed per payload size. Small, uniform trimming (a few
      percent) is expected; flag any size that loses a disproportionate share of rows.

## Step 5 — Derive per-trial metrics and save the cleaned dataset

- [ ] `time_s = time_us / 1e6`
- [ ] `power_mW` = the offset-corrected, recomputed power delta from Step 3 (not the
      device's raw field)
- [ ] `mem_total = heap_peak_used_bytes + stack_used_bytes`
- [ ] Save to `processed/ascon_clean.csv` / `processed/aes_clean.csv` — this is the
      auditable, cleaned dataset every downstream statistic is built from.

## Step 6 — Compute per-payload-size summary statistics

For each of the 100 payload sizes, for each of `time_us`, `power_mW`, `mem_total`:

- [ ] n, mean, median, standard deviation, 95% CI (using the t-distribution).
- [ ] Throughput (Equation 1): `size / mean(time_s)`, computed on the **grouped mean**,
      not per-row.
- [ ] Per-operation energy (µJ): `mean_power_mW × mean_time_ms`.
- [ ] Per-byte energy (µJ/byte): `energy_uJ / size`.
- [ ] Save as `processed/ascon_summary_by_size.csv` / `aes_summary_by_size.csv`.

## Step 7 — Add sleep-phase energy (Objective 1 & 2)

The firmware measures only the active `ENCRYPT_AND_MEASURE` phase. Sleep-phase energy
is added analytically, not from an on-device measurement:

- [ ] Look up the ESP32-WROOM-32E datasheet deep-sleep current (`I_sleep`, µA) for the
      wake source used (RTC timer), and the RTC-domain supply voltage (`V_sleep`,
      typically 3.3 V). Record the datasheet revision/date cited.
- [ ] Compute `E_sleep = V_sleep × I_sleep × T_sleep`, using the **design-specified**
      sleep duration `T_sleep = 60 s` from Chapter 3 (§3.3.4) — regardless of what the
      firmware's `DEEP_SLEEP_SECONDS` constant was actually set to during a given
      collection run (see the note below).
- [ ] `total_duty_cycle_energy_uJ = energy_uJ (Step 6) + E_sleep`
- [ ] `total_duty_cycle_energy_per_byte_uJ = total_duty_cycle_energy_uJ / size`

> **Note on the on-device sleep interval used during data collection.** During actual
> data-collection runs, `DEEP_SLEEP_SECONDS` in `main/main.c` was temporarily reduced
> from the design value (2 s, later intended to represent the 60 s duty cycle) down to
> **1 s**, purely to shorten total collection time under the project's practical time
> constraints. This has **no effect on validity or on any reported number**: the raw log
> only contains active-phase measurements (Step 1), and `E_sleep` above is computed
> analytically from the datasheet current and the fixed 60 s design duration, independent
> of the board's actual sleep-timer setting during collection. Do not mention this in the thesis document.

## Step 8 — Repeat Steps 1–7 identically for the second algorithm

- [ ] Confirm the AES-128-GCM log's `id`/`size` structure spans the same 100 payload
      levels so the two datasets join cleanly on `size`.
- [ ] Do not hand-tune cleaning thresholds differently between the two datasets — this is
      what keeps the Step 9 comparison valid.

## Step 9 — Comparative statistics (answers the RQ directly)

- [ ] **Per-size significance (Objective 1/2 support):** one-tailed Welch's t-test per
      payload size (α = 0.01) for `time_us`, `power_mW`, and `energy_per_byte_uJ`.
      Report the *proportion* of the 100 sizes that are significant, not one pooled
      p-value.
- [ ] **Break-even / crossover payload size (Objective 3):** merge the two
      `..._summary_by_size.csv` files on `size`; compute
      `ascon_minus_aes_energy = energy_per_byte_uJ_ascon - energy_per_byte_uJ_aes`;
      find the sign change(s) across ascending payload size; linearly interpolate
      between the two bracketing sizes for a precise crossover value in bytes.
- [ ] **Scaling/regression (supports literature link, §2.2.5):** linear regression of
      `mean_time` and `energy_uJ` against `size` per algorithm; report slope and R².
- [ ] **Memory footprint (Objective 1 context):** same summarize→merge pattern on
      `mem_total`; treat primarily as a size-independent bar comparison, since AES-GCM's
      mbedTLS context overhead is expected to dominate regardless of payload size.
- [ ] **Regime segmentation (Objective 3):** split the crossover analysis into small
      (<256 B, LPWAN-typical) vs large (>800 B, bulk-telemetry-typical) payload regimes
      and state which algorithm is preferable in each.

## Step 10 — Visualizations

| Chart | X | Y | Purpose |
|---|---|---|---|
| Line | payload size (16–1600 B) | mean execution time (µs), both algorithms, 95% CI band | scaling behaviour |
| Line | payload size | throughput (B/s) | where hardware acceleration pulls ahead |
| Line | payload size | energy per byte (µJ/byte) | **core RQ answer** — mark the crossover point |
| Bar | algorithm | mean memory footprint (bytes) | discrete comparison |
| Scatter/line | payload size | regression fit overlay (R²) | supports linear-scaling claim |

## Step 11 — Map results back to the dissertation objectives

| Objective | Where the number comes from |
|---|---|
| Obj. 1 — total duty-cycle energy incl. HW init overhead | Step 7 (`total_duty_cycle_energy_uJ`); isolate the AES hardware-engine init cost as the near-constant offset at the regression intercept (`size → 0`) from Step 9's regression |
| Obj. 2 — energy cost per transmitted byte, full duty cycle | Step 7 (`total_duty_cycle_energy_per_byte_uJ`) |
| Obj. 3 — conditions/break-even where ASCON remains preferable | Step 9 crossover + regime segmentation |

When writing Chapter 4/5: (1) state the crossover payload size and which regime favours
which algorithm, (2) report the t-test significance pattern from Step 9 as statistical
backing, (3) tie back to the literature gap (Chapter 2, §2.3.4/2.7) — this study is the
first to place software ASCON-128 and hardware AES-128-GCM on the same platform under a
uniform per-byte, full-duty-cycle metric, so the numeric crossover point is itself the
novel contribution the thesis claims.

## Step 12 — Data-quality checklist before writing Chapter 4

- [ ] Row counts logged at every stage (raw → iteration-complete → offset-corrected →
      outlier-trimmed) for both algorithms — appendix table.
- [ ] Calibration constants reported (offset mA, measured bus voltage V, datasheet sleep
      current/voltage + datasheet revision/date).
- [ ] Same cleaning pipeline and same calibration constants confirmed applied to both
      datasets.
- [ ] Sleep-timer deviation (1 s used during collection vs 60 s design value) documented
      per the note in Step 7, with the justification that it does not affect any
      reported metric.
- [ ] Complete-iteration count and sampling decision (all complete vs subsampled to a
      fixed N) stated, replacing any earlier "500 repeats" figure with the verified count.

---

*Companion documents: [Analysis_Design.md](Analysis_Design.md) (design rationale) and
[Data_Preprocessing_and_Analysis_Guide.md](Data_Preprocessing_and_Analysis_Guide.md)
(runnable Python implementation of every step above).*
