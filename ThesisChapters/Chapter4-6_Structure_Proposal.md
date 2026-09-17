# Proposed Structure — Chapters 4–6 (v2, expanded)

**Status: proposal only, approved split (4/5/6), now expanded to sub-subtopic level per
your feedback. Still no thesis content drafted — this is the outline + reasoning for each
piece, so you can sanity-check the plan before I write actual prose.**

Confirmed since v1:
- All 6 figures in `figures/` are final and now mapped to a specific subsection each
  (`regression_scaling_overlay.png` was unmapped in v1 — fixed below, in 4.3.3).
- Citing existing Chapter 2 sources by claim is approved; I will still flag anything that
  looks like it needs a source Chapter 2 doesn't already have, before using it.
- Split (Ch.4 Results / Ch.5 Discussion / Ch.6 Conclusions) confirmed.
- Added: a dedicated **Limitations of the Study** subsection inside Chapter 6 (6.5,
  between the appraisal and the future-work list), distinct in *purpose* from Chapter 5's
  Critical Self-Evaluation (5.6) — see the note under Chapter 6 explaining the difference
  so the two don't just duplicate each other.

---

## Chapter 4: Data Analysis and Results

Past tense throughout. Every subsection opens by naming which Objective(s) it feeds, then
presents the numbers, then one short paragraph of "what this shows" (interpretation proper
is Chapter 5's job — 4.x stays close to the data).

### 4.1 Introduction
- Restates the RQ and the three Objectives (cross-referenced to §1.7–1.8, not rewritten).
- States the chapter's organizing logic: data quality first (4.2), then one subsection per
  metric family (4.3–4.6), then the cross-cutting statistical tests (4.7), then a
  per-objective summary (4.8).
- States plainly that ASCON and AES were pushed through an *identical* processing
  pipeline (Steps 1–9 of `DATA_ANALYSIS_README.md`) — the single sentence that licenses
  every "ASCON vs AES" comparison later in the chapter to be read as attributable to the
  algorithms, not to inconsistent handling.

### 4.2 Data Collection Outcome and Cleaning Summary
*(Reliability-of-data focus — how the raw logs became the numbers in 4.3–4.7)*

- **4.2.1 Raw Log Volumes and Structural Completeness**
  How it worked: the raw NDJSON logs (65,506 ASCON rows / 61,715 AES rows) were segmented
  into iterations by detecting drops in payload size (a new sweep starts when `size` resets
  from ~1600 back to 16), rather than deduplicating on the trial `id` field. Explains
  *why* `id` was rejected as a cleaning key (non-monotonic across device resets, so `id`
  collisions can span genuinely different sweeps) — this is a methodological decision worth
  defending on its own, not just a technical footnote. Reports: 699/646 candidate
  iterations detected, 561/510 kept as fully complete (all 100 payload sizes present
  exactly once), the rest discarded outright as partial resets. States the resulting
  uniform per-size sample count (561 for ASCON, 510 for AES) and the decision to use all
  complete iterations rather than subsample to a fixed N. Table: row-count-per-stage
  appendix (from `processed/data_quality_stage_log.csv`).
- **4.2.2 INA219 Zero-Offset Calibration**
  How it worked: ~21% of current readings were negative, but clustered tightly (a narrow
  band, not scattered noise) — identified as a sensor zero-offset characteristic rather
  than random error. The offset (5.70 mA) was estimated from the negative-reading cluster's
  median and added back to *every* reading (not just the negative ones); power was then
  recomputed from the corrected current and an empirically measured bus voltage (4.674 V,
  derived from high-confidence active rows) rather than trusting the device's own
  raw power fields, which inherited the same bias. Framed explicitly as evidence of
  methodological rigor: the offset is a reported, auditable constant, not a silent data
  edit — and it is the *same* constant applied to both algorithms' logs, which is what
  keeps the later comparison valid.
- **4.2.3 Outlier Trimming**
  How it worked: IQR-based trimming (k=1.5) on execution time and corrected power, applied
  per payload size, only *after* 4.2.1–4.2.2. Explains why that ordering matters: trimming
  before structural/calibration correction would misclassify partial-sweep artifacts or
  sensor bias as statistical noise. Reports total rows trimmed per algorithm and confirms
  no single payload size lost a disproportionate share.
- **4.2.4 Sleep-Phase Energy Constant**
  How it worked: the firmware measures only the active `ENCRYPT_AND_MEASURE` phase; sleep
  energy is added analytically as `E_sleep = V_sleep × I_sleep × T_sleep`, using the
  Espressif ESP32-C3 Series Datasheet v2.3, Table 5-9 figure (Deep-sleep, RTC timer + RTC
  memory = 5 µA, measured at 3.3 V) and the design's fixed 60 s duration — **not** the 1 s
  the firmware's `DEEP_SLEEP_SECONDS` was actually set to during collection. States this as
  a deliberate substitution and gives the one-sentence reason it's valid (sleep current and
  duration are both payload-size-independent, so the term only shifts absolute totals, not
  the comparison) — full defence of *why* this doesn't threaten validity is Chapter 5's
  job (5.5), this subsection just reports the constant and its citation.

### 4.3 Execution Time and Throughput Results *(feeds Objective 1; contextual for Obj. 3)*
- **4.3.1 Execution Time Scaling** — mean/median/SD/95% CI per payload size, both
  algorithms. Figure: `execution_time_scaling.png` (mean time with 95% CI band, both
  algorithms overlaid).
- **4.3.2 Throughput** — computed per Equation 1 (Chapter 3) on the grouped mean, not
  per-row. Figure: `throughput_scaling.png`.
- **4.3.3 Linear Scaling / Regression Fit** — reports slope and R² for time-vs-size, both
  algorithms (R² ≈ 1.0 for both — near-perfect linear scaling). Figure:
  `regression_scaling_overlay.png` (scatter + fitted line, time and energy side-by-side).
  Ties the time-scaling result directly back to the ASCON sponge-duplexing linear-scaling
  claim from Chapter 2 §2.2.5 — this is a literature-linking sentence, kept brief here,
  expanded properly in Chapter 5 §5.3.

### 4.4 Power Consumption Results *(feeds Objective 1)*
How it worked / what's reported: corrected power (`power_mW`, from 4.2.2) per payload
size, both algorithms, with the same summary statistics as 4.3. One paragraph on what the
power curve's shape indicates about the fixed vs. scaling components of each algorithm's
draw — sets up 4.5's energy-per-byte section, which is where this becomes the chapter's
main result.

### 4.5 Per-Byte Energy Efficiency and Break-Even Analysis
*(feeds Objective 2 directly; Objective 3 is answered almost entirely in this section)*
- **4.5.1 Per-Byte Energy Curves** — active-phase (`energy_per_byte_uJ`) and total
  duty-cycle (incl. the 990 µJ sleep term) energy per byte, both algorithms. Figures:
  `energy_per_byte_comparison.png` (the core RQ chart, crossover marked),
  `total_duty_cycle_energy_per_byte.png`.
- **4.5.2 Break-Even / Crossover Payload Size** — reports the ≈347-byte crossover with the
  linear-interpolation method stated explicitly (bracketing sizes 336B/352B). Explicitly
  names the small 528–560B sign-wobble as measurement noise (curves converge to within
  ±0.003 µJ/byte there) rather than a genuine second regime, and gives the magnitude
  evidence for calling it that.
- **4.5.3 Regime Segmentation** — small (<256B, LPWAN-typical) vs large (>800B,
  bulk-telemetry-typical) payload table, stating which algorithm is preferable in each —
  the direct, literal answer to Objective 3's "conditions under which ASCON remains
  preferable."

### 4.6 Memory Footprint Results *(feeds Objective 1, contextual)*
Mean `mem_total` (heap peak + stack used) per algorithm, bar comparison. Figure:
`memory_footprint_comparison.png`. One paragraph connecting the ~24% AES overhead to
Chapter 2's mbedTLS-context-overhead discussion (§2.3.1) — again, brief here, expanded in
5.3.

### 4.7 Statistical Significance Testing
*(supports the reliability of every claim in 4.3–4.6)*
- **4.7.1 Per-Size Hypothesis Testing** — one-tailed Welch's t-tests (α=0.01) run per
  payload size (100 tests per metric) for time, power, and energy/byte. Reports the
  *proportion* of significant sizes (21% / 78% / 72%) rather than one pooled p-value, per
  the pre-registered design in Chapter 3 §3.7.2. States plainly what the pattern means:
  execution time rarely differs significantly, but power and energy almost always do — the
  energy story in this thesis is carried by power draw, not raw speed.
- **4.7.2 Regression Summary** — consolidated slope/intercept/R² table for time and energy,
  both algorithms. The AES energy-regression intercept (30.14 µJ) vs. ASCON's (15.03 µJ) is
  presented here as the direct numerical evidence for the "hardware engine initialization
  overhead" clause of Objective 1.

### 4.8 Summary of Chapter 4
One short paragraph per Objective, stating in past tense *what was found* (not yet what it
*means* — that's Chapter 5). Explicitly closes the loop back to §4.1's preview.

*(All of 4.2–4.7 has real, final numbers already available in `processed/RESULTS_SUMMARY.md`
and the underlying CSVs/JSONs — no `[PENDING AES DATA]` markers needed anywhere in this
chapter.)*

---

## Chapter 5: Discussion and Critical Evaluation

Past tense throughout. This is where interpretation, literature comparison, and the two
explicitly-required subsections (Reliability; Validity) live in full, plus Critical
Self-Evaluation.

### 5.1 Introduction
States the chapter's organizing logic: objective-by-objective interpretation first (5.2),
then literature comparison (5.3), then the two required methodological subsections
(5.4–5.5), then self-evaluation (5.6).

### 5.2 Interpretation of Findings Against the Research Objectives
- **5.2.1 Objective 1** — total duty-cycle energy incl. HW init overhead. Interprets the
  regression-intercept gap (4.7.2) and the total-energy figures (4.5.1, incl. sleep term)
  together: does the hardware engine's speed/power advantage actually offset its fixed
  initialization cost across the measured payload range, and at what point.
- **5.2.2 Objective 2** — energy cost per transmitted byte. Interprets the per-byte curves
  (4.5.1) specifically at realistic LPWAN-scale (<256B) vs. bulk-telemetry-scale (>800B)
  payloads, connecting to the regime table (4.5.3).
- **5.2.3 Objective 3** — break-even/crossover, conditions favoring ASCON. The ≈347B
  crossover (4.5.2) is presented as this thesis's central empirical contribution, explicitly
  connected to the gap identified in Chapter 2 §2.3.4/§2.7 (no prior study places software
  ASCON-128 head-to-head against hardware AES-128-GCM on one platform under a uniform
  per-byte, full-duty-cycle metric).

### 5.3 Comparison with Existing Literature
How it works: takes specific claims already cited in Chapter 2 and checks each one against
this study's numbers — agreement, disagreement, or (most interestingly) reframing. Two
concrete threads already visible from the data:
- **Where results agree**: ASCON's near-perfect linear runtime scaling (4.3.3, R²≈1.0)
  matches the sponge-duplexing claim in §2.2.5; hardware AES's throughput advantage at
  larger payloads matches the ESP32-hardware-accelerator literature in §2.3.3.
- **Where results reconcile a literature conflict**: §2.3.4 noted that studies showing
  ASCON "winning" benchmarked it against *software* AES, while studies showing hardware AES
  "winning" benchmarked it against the *same* software AES baseline being offloaded — never
  against ASCON directly. This study's crossover result (≈347B) is presented as the
  reconciling data point: both literatures were correct for their respective comparisons,
  and the crossover shows where the frontier actually sits when the two are measured
  against each other directly.

### 5.4 Reliability of the Data and Data Collection Process *(required subsection)*
Synthesises 4.2 into an argument rather than a restatement: why iteration-level cleaning
(not `id` dedup), offset-calibration (not blind clipping), and post-hoc IQR trimming
together form a defensible, auditable reliability chain — and why applying that *identical*
chain to both algorithms is what makes the Chapter 4 comparison trustworthy rather than an
artifact of differential cleaning. Names the residual noise sources that remain despite
this (Wi-Fi/MQTT transmission-phase variance, INA219 measurement resolution) and explains
how the shared-pipeline design contains their effect on the *comparison* even though it
doesn't eliminate them from either dataset individually.

### 5.5 Validity of the Evaluation Approach *(required subsection)*
Addresses head-on whether the experimental design (100 payload sizes, 561/510 complete
iterations, full Sleep→Wake→Sense→Encrypt→Transmit→Sleep cycle) actually measures what the
RQ asks. Argues yes via: per-byte normalization (removes the payload-size confound),
controlled-variable design (§3.2.3 — identical everything except the algorithm under test),
and explicit inclusion of HW-engine init/setup cost in the energy accounting (this is what
makes the design answer Objective 1 literally, not approximately). Also addresses
*construct* validity directly: does "energy per byte over one duty cycle" really capture
"practical usefulness for a battery-powered IoT node," and what it deliberately does not
capture (battery chemistry and discharge curves, multi-day thermal drift, RF-environment
variability) — this paragraph is the bridge into 5.6.

### 5.6 Critical Self-Evaluation
*(required subsection — an argued position on what the work does and doesn't establish,
not a checklist)*
For each limitation: what it is, what specifically it bounds, and what it does *not* bound
(this asymmetry is what makes it a critical evaluation rather than a disclaimer list):
- Single physical ESP32-WROOM-32E unit — bounds generalization across manufacturing
  variance; does not bound the internal ASCON-vs-AES comparison, which is within-unit.
- INA219 measurement resolution (12-bit ADC) — bounds precision at the smallest measured
  power deltas; does not bound the much larger deltas driving the crossover result.
- Fixed 60 s sleep window, used only analytically — bounds claims about *other* duty-cycle
  frequencies; does not bound the crossover point itself, since sleep energy is a
  payload-size-independent constant (proven algebraically in 4.5.1/5.2.2).
- Datasheet-derived (not measured) sleep current — bounds confidence in *absolute*
  duty-cycle totals; does not bound the comparative/crossover conclusion (cross-references
  the regression-intercept argument from 4.7.2).
- Wi-Fi/MQTT transmission-phase noise — contributes to the residual variance visible in the
  t-test proportions (4.7.1), specifically why execution time was significant at only 21%
  of sizes versus 72–78% for power/energy.

### 5.7 Summary of Chapter 5
Short paragraph bridging into Chapter 6: what's now established (per-objective findings)
vs. what's now explicitly bounded (5.6) — sets up 6.2's verdicts directly.

---

## Chapter 6: Conclusions and Future Work

**Relationship between 5.6 and the new 6.5 (so they don't just repeat each other):**
Chapter 5's Critical Self-Evaluation (5.6) is *diagnostic* — it happens alongside the
Discussion, bounding each interpretive claim as it's made. Chapter 6's Limitations of the
Study (6.5) is *prospective* — it's written after the objective-achievement verdicts (6.2)
and the appraisal (6.4), and its only job is to hand each limitation forward into a
concrete future-work item (6.6). Same five limitations, different function: 5.6 says "here
is what you should not conclude from this thesis"; 6.5 says "here is what a next student
should go and fix." Some repetition of content is intentional (per your Step 4 note) but
the framing and the forward-pointing structure differ.

### 6.1 Introduction
States the chapter answers three things in order: were the objectives met (6.2), what's
the one-paragraph answer to the RQ (6.3), and what should happen next (6.4–6.6).

### 6.2 Achievement of Research Objectives
One subsection per objective, each with an explicit verdict (fully met / partially met /
not met) and the one-sentence reason, referencing back to the Chapter 4 numbers and
Chapter 5 interpretation directly (intentional repetition, per your Step 4 note):
- 6.2.1 Objective 1 — power consumption / per-byte energy incl. HW init overhead
- 6.2.2 Objective 2 — energy cost per transmitted byte across the full duty cycle
- 6.2.3 Objective 3 — break-even payload size / conditions favoring ASCON

### 6.3 Answer to the Central Research Question
A direct, single-paragraph synthesis of all three objectives into one answer, with the
≈347B crossover point as the headline finding.

### 6.4 Critical Appraisal of the Research
Not a limitations rehash (that's 6.5) — an honest assessment of the work *as research*:
what it establishes with confidence vs. what it only suggests, and whether the experimental
design was proportionate to the question asked (100 payload sizes × 500+ iterations × full
duty cycle, for a question that ultimately turned on a single crossover point — was that
the right amount of rigor, over- or under-engineered, and why).

### 6.5 Limitations of the Study
*(new — added per your request)*
Restates the five limitations from 5.6, each now written prospectively — framed as "a
constraint on this study that a following student could remove" rather than "a bound on
this study's claims" — directly setting up 6.6's matching future-work items one-to-one:
single-unit hardware, INA219 resolution, fixed 60 s sleep window, datasheet-derived sleep
current, and Wi-Fi/MQTT transmission noise.

### 6.6 Contribution to Knowledge
Ties back to the Chapter 2 §2.7 gap statement: this is presented as the first study placing
software ASCON-128 and hardware AES-128-GCM on the same platform under a uniform per-byte,
full-duty-cycle metric.

### 6.7 Recommendations for Future Work
Concrete, one item per 6.5 limitation plus two broader extensions — each stated as an
actionable next step, not a generic "more research is needed":
1. **Multi-unit replication** (n>1 physical ESP32 boards) — directly answers the
   single-unit limitation; quantifies unit-to-unit variance in the crossover point itself.
2. **Empirical wake-up/reconnect transient measurement** instead of the datasheet
   steady-state figure — directly answers the datasheet-derived-sleep-current limitation.
3. **Repeat the duty cycle at alternate fixed sleep durations** (e.g., 10 s, 300 s, 3600 s)
   to empirically confirm the crossover point is sleep-duration-invariant (predicted
   algebraically in 4.5.1/5.2.2, but never empirically tested here) — directly answers the
   fixed-60s-window limitation.
4. **Higher-resolution or multi-range current sensing** (e.g., a sensor with finer ADC
   resolution at low currents, or a dual-range shunt) — directly answers the INA219
   resolution limitation.
5. **Repeat with Ethernet or a quieter RF environment**, or log per-trial RF diagnostics, to
   isolate cryptographic energy cost from Wi-Fi/MQTT transmission noise — directly answers
   the transmission-noise limitation.
6. **Extend to other NIST LWC finalists / other hardware AEAD engines** (e.g. ChaCha20-
   Poly1305) to test whether the ASCON-vs-AES crossover pattern generalizes beyond this
   specific pair.
7. **Real battery-drain field trial** (coin-cell discharge over weeks) to validate the
   per-byte energy model against actual device lifetime — directly answers the
   construct-validity point raised in 5.5.

### 6.8 Closing Remarks

---

## Figure-to-section map (all 6 figures now placed)

| Figure | Section |
|---|---|
| `execution_time_scaling.png` | 4.3.1 |
| `throughput_scaling.png` | 4.3.2 |
| `regression_scaling_overlay.png` | 4.3.3 |
| `energy_per_byte_comparison.png` | 4.5.1 |
| `total_duty_cycle_energy_per_byte.png` | 4.5.1 |
| `memory_footprint_comparison.png` | 4.6 |

---

## Next step

If this expanded outline looks right, I'll draft **Chapter 4 in full**, section by section
(starting with 4.1–4.2), for your review before moving to 4.3 onward.
