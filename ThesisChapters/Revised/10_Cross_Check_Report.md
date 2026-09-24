# Cross-check report: what the thesis said, what the validation found, what changed and why

*Written for: the author and the supervisor. Page numbers refer to "Final Thesis V02.pdf". Evidence files are listed in section 8.*

---

## 1. What was compared

| | **Campaign A** (the original thesis data) | **Campaign B** (the validation) |
|---|---|---|
| Firmware | `main/` (one trial per boot, Wi-Fi/MQTT reporting) | `validation_fw/` (sustained load, no Wi-Fi) |
| Power method | Two instantaneous INA219 readings around one call | INA219 averaged (about 68 ms), extra current over an idle baseline, 700 ms of back-to-back calls |
| Timed region | Sensor reads + task creation + cipher call | Cipher call only, in a long loop |
| Sessions | ASCON-128 and AES-128-GCM collected separately | Interleaved, shuffled order, one session |
| Data removed | 18.5% (ASCON) and 15.9% (AES) as outliers | None |
| Size of dataset | 65,506 and 61,715 raw rows; 561 and 510 complete sweeps | 970 rows (Run 1: 550, Run 2: 420) |
| Sizes | 100 (16 to 1,600 B, step 16) | 18 (Run 1) and 9 (Run 2, 64 to 128 B, step 8) |
| What it can support | Increments of time per byte, memory footprint | Time, power, energy per call, setup cost, break-even |

The two datasets are not competing measurements of the same quantity. Campaign A measured *trial latency including instrumentation* and a power estimate that turned out to be unreliable; Campaign B measured the cost of the cipher call itself. The cross-check therefore asks, for every claim in the thesis: is it supported by Campaign B, changed by it, or contradicted by it?

---

## 2. The main finding of the cross-check

**Campaign A time is Campaign B time plus a constant, and Campaign A power is not power.**

- *Time.* At the eight sizes that both campaigns share, Campaign A exceeded Campaign B by 1,313 to 1,340 µs for ASCON-128 and by 1,638 to 1,644 µs for AES-128-GCM, almost independent of payload size. The slopes agree to within 1.4% (ASCON 1.197 vs 1.180 µs/B; AES 0.901 vs 0.897 µs/B). So the *increments* in Campaign A are correct; the level is dominated by instrumentation (task creation, sensor reads, cold start).
- *Power.* Campaign A reported 20 to 25 mW at small sizes, where Campaign B measures 64 to 75 mW, and it changed in steps (ASCON 19.8 → 52.6 mW between 560 and 576 B; AES 24.9 → 14.8 mW between 336 and 352 B and 21.9 → 47.8 mW between 1,520 and 1,536 B) that do not exist in Campaign B, where ASCON power is constant at 75.1 to 75.4 mW.
- *The 347-byte break-even.* It sits exactly on the AES power step between 336 and 352 B: AES energy per byte fell from 0.150 to 0.086 µJ/B (−43%) while AES time rose smoothly (2,029 → 2,044 µs). If the AES power is held at its pre-step level, the crossing moves to about 564 B; if the ASCON step is also removed, there is no crossing. So the 347 B was produced by a discontinuity in the power measurement.

---

## 3. Claim-by-claim comparison

"Where" gives the page of the thesis PDF.

### 3.1 Headline and mechanism

| # | Thesis claim (page) | Campaign B result | Verdict | Why it changed |
|---|---|---|---|---|
| 1 | Break-even ≈ 347 bytes; ASCON below, AES above (p. iii, 43, 47, 55) | ≈ 100 bytes (96 to 107) if AES sets up its context on every message; **no break-even** if the context is reused | **Replaced** | 347 B coincides with an artefact step in measured AES power (Sect. 2) |
| 2 | AES has a fixed initialisation cost of 30.14 µJ, twice ASCON's 15.03 µJ (p. iii, 41, 46, 47, 55) | Setup step measured at 30.9 µs and 1.90 µJ. Fitted fixed costs: 5.57 µJ (AES, setup each call), 2.91 µJ (ASCON); ratio 1.9 | **Replaced** in magnitude; ratio survives | An intercept extrapolated from a poor fit (R² 0.43) that also contained instrumentation cost |
| 3 | AES adds energy more slowly per byte (0.0335 vs 0.1068 µJ/B) (p. 41, 47) | 0.062 vs 0.089 µJ/B | **Direction confirmed, magnitude changed** | AES power steps distorted the Campaign A slope; slope of AES was 1.8 times too low |
| 4 | The break-even is a mathematical consequence of a fixed cost and a per-byte cost (p. 49–50) | Confirmed: (5.57 − 2.91)/(0.0889 − 0.0619) = 99 B, matching the measured 96 to 107 B | **Confirmed, with new numbers** | — |
| 5 | Regression gives 206 B; the gap to 347 B is "expected" because of noise (p. 50) | Regression 99 B vs measured 96 to 107 B | **Explanation replaced** | The fitted line crossed stepped data; in Campaign B the model fits (R² > 0.9999) and both estimates agree |
| 6 | Hardware setup consists of clock enabling, key loading and GHASH subkey (Table 8, p. 48) | Not tested | **Soften** | Mechanism claimed without verification; the measurement supports "setup costs 1.9 µJ", not the description of its parts |

### 3.2 Time, power, energy

| # | Thesis claim (page) | Campaign B result | Verdict | Why |
|---|---|---|---|---|
| 7 | Time linear in size; slopes 1.197 and 0.901 µs/B (p. 40) | 1.180 and 0.897 µs/B (R² > 0.9999) | **Confirmed** | Increments were sound |
| 8 | Time at 16 B: 1,740.8 µs (AES); at 1,600 B ASCON 3,266.5 µs (p. 40) | 102.8 µs (AES, setup each call) and 1,926.6 µs (ASCON) | **Replaced** | Offsets of 1.3 to 1.6 ms of instrumentation |
| 9 | Execution-time crossover near 1,250 B (p. 40, Fig. 7) | ≈ 175 B | **Replaced** | The 325 µs larger offset of AES in Campaign A |
| 10 | Power: ASCON 20.3 mW, AES 24.2 mW at 16 B; ASCON 52.2 vs AES 22.2 mW at 800 B (p. 41) | ASCON 75.1 mW, AES 63.8 mW at 16 B; ASCON 75.3 vs AES 68.4 mW at 800 B | **Withdrawn** | Two-reading method; power steps |
| 11 | "ASCON-128's power draw scaled upward more steeply with payload size" (p. 41) | ASCON power constant (75.1 to 75.4 mW) | **Withdrawn** | The rise in Campaign A was the step at 576 B |
| 12 | Energy per byte 1.742 (ASCON) vs 2.633 µJ/B (AES) at 16 B (p. 42) | 0.272 vs 0.410 µJ/B | **Replaced** in scale (6.4 times too high), ordering confirmed (ASCON lower at 16 B) | Same causes |
| 13 | At 1,600 B ASCON 0.108 vs AES 0.095 µJ/B (p. 42) | 0.091 vs 0.065 µJ/B | **Ordering confirmed** | AES 28% cheaper (validated) vs 12% (Campaign A) |
| 14 | Table 5 shows ASCON 0.017 µJ/B at 336 B (p. 44) | 0.107 (Campaign A value); typing error | **Correct the typo** | — |
| 15 | Energy regressions R² 0.91 (ASCON) and 0.43 (AES) (p. 41) | R² > 0.9999 | **Replaced** | The Campaign A fit was poor because the data had steps |
| 16 | Regime segmentation: small < 256 B ASCON better; large > 800 B AES better (Table 6, p. 44) | ASCON better below ≈ 100 B (setup each call); AES better above; none if reused | **Replaced** | Break-even moved |

### 3.3 Statistics

| # | Thesis claim (page) | Re-analysis | Verdict | Why |
|---|---|---|---|---|
| 17 | Time significant at 21 of 100 sizes, power 78, energy 72 (Table 7, p. 46) | Two-sided: 100, 99, 93 (uncorrected); 100, 99, 92 (Holm) | **Replaced** | One-tailed test fixed in the direction "ASCON > AES" |
| 18 | Time "converged" and the gap was "driven by power rather than speed" (p. iii, 45, 51) | Time differs at every size; in Campaign B ASCON draws 10% more power but takes up to 26% more time at 1,600 B | **Withdrawn** | Same cause |
| 19 | Outlier trimming did not concentrate at particular sizes (p. 39) | Break-even 345.0 / 347.4 / 346.8 B with no trimming / k = 3 / k = 1.5 | **Checked; trimming did not create the 347 B** | But the result is still an artefact (Sect. 2) |
| 20 | One-tailed independent t-tests at α = 0.01 (p. 35, 45) | Two-sided, paired (Campaign B), Holm-corrected | **Method replaced** | Direction reverses across the break-even; 300 tests were uncorrected |

### 3.4 Duty cycle and scope

| # | Thesis claim (page) | Re-examination | Verdict |
|---|---|---|---|
| 21 | Total duty-cycle energy per byte 63.62 vs 64.51 µJ/B at 16 B (p. 42, 49) | The sleep term is a constant of 990 µJ (or 1,980 µJ at 10 µA) and identical for both; the cipher choice changes cycle energy by 0.1 to 3.6% | **Reframed** as modelled shares |
| 22 | Sleep phase 60 s, 5 µA from the ESP32-C3 datasheet (p. 39) | The board is an ESP32, not a C3; firmware wake timer was 1 s in the committed code; 127,000 trials at 60 s would take about 88 days | **Correct the source; state the modelled interval; [CONFIRM 2]** |
| 23 | "Complete Sleep → Wake → Sense → Encrypt → Transmit → Sleep" cycle measured (abstract, p. 1, 4, 22, 36) | Only the encryption phase was measured; sleep modelled; wake-up and transmission not measured | **Scope narrowed** |
| 24 | Measurements at 240 MHz (p. 27) | Firmware built for 160 MHz | **Correct** |
| 25 | Memory footprint: AES 3,441.0 B vs ASCON 2,772.8 B (24%) (p. 44) | Not re-measured; independent of the timing and power method | **Retained** |
| 26 | The literature conflict is "reconciled" (p. iii, 51) | Qualitatively supported, but the crossover point and the AES setup policy matter | **Retained in conditional form** |

---

## 4. The supervisor's five comments

| # | Comment | Answer | Where |
|---|---|---|---|
| 1 | Flowchart symbols not standard; stops vs returns inconsistent | Correct. Figure 1 uses `Stop main()`, `Stop RUN_TRIAL()` and `Return …` for the same thing, `EUN_TRIAL` for `RUN_TRIAL`, `j ≤ X` for `j ≤ 100`, unlabelled decision exits, and an AES-GCM branch that appears to lead to `random_bytes(16)`. Redraw to ISO 5807 (terminators for Start/End, *Return* for every function), with labelled Yes/No | `07_Figures_and_Appendices.md` (A.1) |
| 2 | 347 B vs 206 B: why? | The regression fitted a straight line to data with steps (R² 0.43 and 0.91); the 347 B sits on a step in measured AES power; in the validated data the two estimates agree (99 vs 96 to 107 B) | Chapter 5, 5.5.2 and 5.5.3 |
| 3 | Intercept is not initialisation energy | Correct. Setup measured directly at 1.90 µJ; the 30.14 µJ was an extrapolation of a poor fit that included instrumentation | 5.4.3 and 5.5.4 |
| 4 | Why remove outliers? Tested without trimming? | Tested: 345.0 / 347.4 / 346.8 B. Trimming did not create the result. Campaign B removes nothing | 5.5.5 |
| 5 | Are separate t-tests appropriate? Multiple comparisons? | No. One-tailed in a fixed direction, uncorrected, 300 tests. Redone two-sided, and paired with Holm correction for Campaign B; effect sizes and a bootstrap interval added | 5.3.5 and 5.5.6 |

---

## 5. Factual errors found in the thesis while cross-checking

Beyond the findings above, these errors are independent of the new data and need correcting.

| Where | Error | Correction |
|---|---|---|
| p. 27 (Fig. 2) | The block diagram is of the ESP32-**C3** (RISC-V) | Use the ESP32 (Xtensa LX6) block diagram |
| p. 27 | 240 MHz | The build used 160 MHz |
| p. 39, 62 | Deep-sleep current from the ESP32-C3 datasheet | Use the ESP32 datasheet [VERIFY 1] |
| p. 29 | mbedTLS 2.16.2 | ESP-IDF 5.3.1 bundles its own version [VERIFY 3] |
| p. 33 | Memory method described as MicroPython (`gc.mem_free`, `ucrypto`), and "repeated five times, median" | The firmware is ESP-IDF C using heap and stack counters over hundreds of sweeps |
| p. 21 | Memory captured with `ESP.getFreeHeap()` (Arduino) | `heap_caps_get_free_size()` and stack watermark |
| p. 32 | `micros()` (Arduino) | `esp_timer_get_time()` |
| p. 28–29, 31–32 | "Microsecond-level precision" of the INA219 | The INA219 does not have it; the timer does |
| p. 29, 33 | Supply described as both 5 V and 3.3 V | INA219 on the 5 V rail upstream of the board's regulator; measured bus voltage 4.72 V |
| p. 37 | Paragraphs repeated three times with garbled sentences in 4.2.1 ("left by device distinct payload sizes exactly once were kept …") | Delete the duplicates |
| p. 40 | "ASCON-128-GCM required 1,740.8 µs" (should be AES-128-GCM); "ASCON-128's mean … marginally lower than ASCON-128's"; "85% confidence interval" | AES-128-GCM; AES-128-GCM; 95% |
| p. 40–46, 47–50 | Cross-references to "4.3.3" (does not exist), "5.2.1" for the initialisation discussion | 4.3.2; 5.2.1 (after revision) |
| p. 44 | Table 5: ASCON 0.017 µJ/B at 336 B | 0.107 |
| p. 47–53 | Two sections numbered 5.2.2; no 5.5 | Renumber |
| p. iii, 1, 4 | "This thesis", "paper" | "This dissertation" |
| p. 22, 32, 35 | Symbols (i, j) missing in "Outer Loop ()" etc. | Restore |
| p. 9, 62 | Duplicate reference keys ("Mahdi & Abdullah, 2025") for two different works | Fix |
| Title | "in a Realistic IoT Duty Cycle" | Optionally "with a Modelled Sleep Phase", or state the scope in the abstract (done) |

---

## 6. What did not change

- ASCON-128 is more efficient than AES-128-GCM at very small payloads *when the AES context is prepared on every message*.
- AES-128-GCM has a lower cost per additional byte and is more efficient at larger payloads (28% lower energy at 1,600 B).
- Neither cipher is unconditionally better, and the trade-off is a fixed cost against a per-byte cost.
- Time per byte scales linearly and the slopes are as reported.
- AES-128-GCM uses about 24% more run-time memory.
- The literature comparison (ASCON vs *software* AES, hardware AES vs *software* AES) and the research gap of Chapter 2.

---

## 7. Confidence and limits

**High confidence:** the setup cost (1.90 µJ, identical in two runs); the ordering of the ciphers below 64 B and above 128 B; the linearity of time and energy; the finding that Campaign A cannot support energy conclusions.

**Moderate confidence:** the break-even value, about 100 B with 96 to 107 B. It is tight statistically, but from one board, one sensor, steady-state, Wi-Fi off, one core, with an unverified absolute scale.

**Untested, stated as such:** whether a cold first call after wake adds an AES-specific fixed cost (the 325 µs difference in Campaign A offsets); which parts of GCM run in hardware; the sleep, wake-up and transmission phases; other boards.

**Depends on an unconfirmed input:** the "under 4%" duty-cycle statement depends on the sleep current [VERIFY 1] and the interval [CONFIRM 2]; it does not affect the break-even.

---

## 8. Evidence and how to reproduce it

| Item | File |
|---|---|
| Campaign A firmware | `main/*.c` (unchanged) |
| Campaign B firmware | `validation_fw/main/main.c` |
| Campaign B logs | `validation_fw/validation_run1.log`, `validation_run2.log` |
| Campaign B analysis | `scripts/04_validation_analysis.py` → `processed/validation/validation_run{1,2}/` |
| Campaign A sensitivity and tests | `scripts/05_original_sensitivity.py` → `processed/original_sensitivity.csv` |
| Figures | `scripts/06_plots_validation.py` → `ThesisChapters/Revised/figures/` |
| Campaign A processed data (unchanged) | `processed/ascon_clean.csv`, `aes_clean.csv`, `*_summary_by_size.csv` |
