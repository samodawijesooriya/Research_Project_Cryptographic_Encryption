# Analysis Design — ASCON-128 vs AES-128-GCM Energy/Performance Study

This document specifies the **design of the data analysis** used to turn the raw serial
benchmark logs produced by the firmware (`main/`) into the results reported in the
dissertation. It is the analysis-side companion to the methodology (data collection) and
should be read together with `Data_Preprocessing_and_Analysis_Guide.md`, which contains the
runnable implementation of every step described here.

---

## 1. Purpose and Scope

The analysis pipeline exists to answer, with statistical support, the three research
objectives:

1. **Obj. 1** — Total duty-cycle energy consumption (active encryption phase + sleep phase)
   for ASCON-128 (software) vs AES-128-GCM (hardware-accelerated).
2. **Obj. 2** — Energy cost per transmitted byte across the full duty cycle, as payload
   size scales from 16 to 1600 bytes.
3. **Obj. 3** — The conditions (payload-size regime) under which each algorithm is
   preferable, including the break-even/crossover payload size.

The analysis is deliberately split into two stages — **pre-processing / validity
assurance** and **statistical comparison** — so that every number reported in Chapter 4 can
be traced back to an auditable cleaning and calibration step.

---

## 2. Data Provenance

| Source | Produced by | Format |
|---|---|---|
| `benchmark_raw_log_<ALGO>.txt` | `output_metrics()` in `main/power_monitor.c`, one line per `ENCRYPT_AND_MEASURE` trial (Fig. 1 of the methodology) | NDJSON, one JSON object per line |
| Datasheet constants | Espressif ESP32-WROOM-32E datasheet | Manually transcribed constants (`I_SLEEP_uA`, `V_SLEEP`) |

Each record captures, for a single trial: trial `id`, `algo`, payload `size`, `time_us`,
heap/stack usage, and INA219 current/power readings before and after the encryption call.
The firmware measures **only the active encryption phase**; the sleep phase is deliberately
*not* instrumented on-device (see §5).

---

## 3. Design Principle: Validity Before Comparison

No cross-algorithm comparison is performed until each raw log has independently passed
three validity gates. Applying the *identical* pipeline to both datasets is itself part of
the design — it ensures any difference observed later is attributable to the algorithms,
not to inconsistent cleaning.

### Gate 1 — Structural completeness (iteration-level, not row-level)
A trial log is only usable if it can be reconstructed into complete **sweeps** (one full
100-payload-size run per outer-loop iteration, `j = 1..100`, sizes 16 → 1600 bytes).
- Iteration boundaries are detected from the payload-size sequence in original recorded
  order (a drop in `size` marks a new sweep).
- Duplicate readings within an iteration are removed, keeping the first occurrence.
- Only iterations containing **all 100 distinct payload sizes exactly once** are retained;
  partial sweeps (caused by resets/reboots mid-run) are discarded outright rather than
  padded or interpolated.
- **Why not deduplicate by trial `id` alone:** the `id` counter is not guaranteed to be
  monotonic across resets, so `id` collisions can span genuinely different sweeps. The
  sweep/iteration is the correct statistical unit because it matches the firmware's
  outer-loop granularity (Fig. 1), not an artifact of the logging counter.

### Gate 2 — Sensor calibration (offset correction, not blind clipping)
INA219 current readings exhibit a systematic negative offset (a known zero-offset
characteristic of the sensor). The design treats this as a **correctable measurement bias**,
not noise to be discarded:
- The offset is estimated directly from the data (median of the negative-reading cluster,
  computed separately for `current_before`/`current_after` then averaged), rather than
  assumed from a specification sheet.
- The offset is added back to every current reading (not only the negative ones), and only
  the small number of remaining large-magnitude outliers are clipped.
- Power is **recomputed** from the offset-corrected current and an empirically measured bus
  voltage (derived from high-confidence, clearly-active rows), rather than trusting the
  device's own `power_before`/`power_after` fields, which inherit the same sensor bias.
- Both calibration constants (offset in mA, measured bus voltage in V) are treated as
  reportable, auditable figures — not silent internal adjustments.

### Gate 3 — Outlier trimming (per payload-size group, post-calibration)
IQR-based trimming (`k = 1.5`) is applied to `time_us` and the corrected power, grouped by
payload size, only *after* Gates 1–2. Trimming before iteration-completeness or offset
correction would incorrectly treat structural artifacts (partial sweeps, sensor bias) as
statistical noise.

**Row-count accounting.** The number of rows retained at each stage (raw → iteration-
complete → offset-corrected → outlier-trimmed) is logged for both algorithms and reported
as a data-quality appendix table — this is the auditable evidence that the two datasets
were cleaned identically.

---

## 4. Derived Metrics (computed only on validated data)

| Metric | Derivation | Feeds |
|---|---|---|
| `time_s` | `time_us / 1e6` | Execution time, throughput |
| `throughput_Bps` | `size / mean(time_s)`, computed on the **grouped mean**, not per-row | Throughput scaling |
| `power_mW` | `power_delta_corr` (post-calibration) | Power consumption |
| `energy_uJ` | `mean_power_mW × mean_time_ms` | Objectives 1 & 2 |
| `energy_per_byte_uJ` | `energy_uJ / size` | Objective 2, crossover analysis |
| `mem_total` | `heap_peak_used + stack_used` | Memory footprint (Objective 1 context) |

Summary statistics (n, mean, median, SD, 95% CI) are computed **per payload size, per
algorithm** — 100 payload levels × 2 algorithms — not pooled, since the research questions
are explicitly about *scaling behaviour*, not a single aggregate figure.

---

## 5. Sleep-Phase Energy: Design Decision and Justification

The methodology's full duty cycle (Fig. 1) includes a deep-sleep phase between encryption
trials. Two points are relevant to the validity of the reported totals:

1. **Sleep energy is not measured empirically on-device.** It is calculated analytically as
   `E_sleep = V_sleep × I_sleep × T_sleep`, using the manufacturer's ESP32-WROOM-32E
   datasheet deep-sleep current figure and the RTC-domain voltage (3.3 V), at the
   **design-specified sleep duration (60 s)** — not the duration the firmware happened to
   use during any particular data-collection run.
2. **The firmware's `DEEP_SLEEP_SECONDS` constant was temporarily reduced from 2 s to 1 s
   during data collection**, purely to shorten total run time under practical time
   constraints for capturing the required number of iterations. This change affects only
   how long the physical board pauses between trials — it does **not** affect any value in
   the raw log (the log contains only active-phase measurements), and it does not feed into
   `E_sleep`, which is computed from the datasheet constant and the fixed 60 s design value
   regardless of what the board's actual sleep timer was set to during testing.

**Consequence for the analysis design:** because sleep energy is analytically substituted
rather than measured, the shortened on-device sleep interval used during data collection
has **no effect on data validity or on any reported metric**. It only shortened wall-clock
collection time. This is stated explicitly here so it is documented as a deliberate,
justified deviation between the *test rig's* sleep timer and the *reported* duty-cycle
energy calculation, rather than an undisclosed inconsistency.

---

## 6. Comparative Statistics Design

| Question | Method | Design notes |
|---|---|---|
| Is the per-size difference significant? | Welch's independent t-test, one-tailed, α = 0.01, run **per payload size** (100 tests per metric) | Report the *proportion* of sizes significant, not one pooled p-value — matches the 100-level scaling design |
| Where do the algorithms cross over in efficiency? | Sign-change detection on `(ASCON − AES) energy_per_byte_uJ` across ascending payload size, linear interpolation between bracketing sizes | Directly answers Objective 3 |
| Does execution time/energy scale linearly with payload size? | `scipy.stats.linregress` per algorithm, report slope and R² | Supports/refutes the sponge-duplexing linear-scaling claim from the literature review |
| Memory footprint | Same summarize→merge pattern on `mem_total`, but treated as a largely size-independent bar comparison | AES-GCM's mbedTLS context overhead is expected to dominate over payload-size effects |

---

## 7. Traceability Map: Objectives → Analysis Section

| Objective | Analysis section | Output |
|---|---|---|
| Obj. 1 — total duty-cycle energy | §4 (`energy_uJ`) + §5 (sleep-phase addition) | `total_duty_cycle_energy_uJ` per size, per algorithm |
| Obj. 2 — energy per transmitted byte | §4 (`energy_per_byte_uJ`) merged with §5 sleep contribution | Line chart, per-byte energy vs payload size |
| Obj. 3 — break-even payload size / regime preference | §6 crossover analysis, segmented into small (<256 B) vs large (>800 B) payload regimes | Crossover payload size (bytes), with statistical backing from the t-test proportion |

---

## 8. Threats to Validity Addressed by This Design

- **Sensor bias** → corrected analytically (§3, Gate 2), not ignored or crudely clipped.
- **Incomplete/corrupted sweeps from resets** → excluded at the iteration level (§3, Gate 1),
  preventing partial data from silently lowering per-size sample counts unevenly.
- **Inconsistent cleaning between algorithms** → identical pipeline and identical
  calibration constants applied to both datasets (§3, §6.3 checklist).
- **Sleep-timer deviation during collection** → shown to be immaterial to reported values
  because sleep energy is computed analytically, not measured (§5).
- **Outlier contamination of summary statistics** → outlier trimming deferred until after
  structural and calibration corrections, so it targets genuine noise rather than
  structural artifacts (§3, Gate 3).

---

*See `Data_Preprocessing_and_Analysis_Guide.md` for the executable Python implementation of
every step referenced above.*
