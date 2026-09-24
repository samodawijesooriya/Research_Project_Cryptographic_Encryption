# Chapter 05: Validation of the Measurements and Reassessment of the Results

*New chapter, to be inserted after Chapter 4. The current Chapter 5 (Discussion) becomes Chapter 6 and the current Chapter 6 (Conclusions) becomes Chapter 7. If headings use Word's heading styles, the renumbering is automatic; cross-references in the existing text are listed in `12_Targeted_Edits_Existing_Thesis.md`.*

*Tables continue the thesis numbering (Table 9 onward) and figures continue from Figure 12. Figure files are in `ThesisChapters/Revised/figures/`. Items in [square brackets] must be confirmed by the author (see `09_Open_Items.md`).*

---

## 5.1 Introduction

The results reported in Chapter 4 came from a per-trial benchmark that is called Campaign A in this chapter. During the review of that work, five questions were raised about the analysis: the inconsistent flowchart symbols, the disagreement between the regression-based break-even (206 bytes) and the measured one (347 bytes), the interpretation of a regression intercept as hardware initialisation energy, the removal of outliers, and the use of separate one-tailed t-tests without correction for multiple comparisons. Answering the second and third questions required examining how Campaign A actually measured time and power. That examination showed that the measurement method could not support energy conclusions for an operation lasting a few milliseconds, and a second campaign was therefore designed and carried out.

This chapter has four aims. It documents the audit of Campaign A (5.2). It describes and reports the second campaign, Campaign B, a sustained-load measurement designed to avoid the identified limitations (5.3 and 5.4). It re-examines the Campaign A results in the light of Campaign B and answers the five review questions (5.5). It then states how far the validation can be trusted (5.6) and which findings of Chapter 4 stand, change or are withdrawn (5.7). The interpretation of the corrected findings follows in Chapter 6.

---

## 5.2 Why Validation Was Needed: Audit of Campaign A

### 5.2.1 Method
The Campaign A firmware (`main.c`, `run_trial.c`, `encrypt_measure.c`, `power_monitor.c` and `ina219.c`) and its build configuration were inspected line by line, and the raw data were compared with what the code implies. Campaign B was then run and compared with Campaign A at the payload sizes that both campaigns share.

### 5.2.2 Findings

| # | Property of Campaign A | Consequence |
|---|---|---|
| 1 | Power was estimated as the difference of two instantaneous INA219 readings, one taken just before and one just after the cipher call. | The INA219 was configured for 12-bit conversions (register value 0x399F), which take about 532 µs, and its registers hold the result of the most recently completed conversion. A call lasting about 2 ms is therefore not bracketed by the two readings in any defined way. |
| 2 | The "before" reading followed an MQTT publish that waited for a broker acknowledgement, so the radio was active. | The baseline used for the difference was not an idle baseline. |
| 3 | The timestamp pair enclosed the heap counters, two INA219 register reads, the creation of a FreeRTOS task for the cipher, a semaphore wait, and the cipher call itself. | The recorded time is trial latency including instrumentation, not the cipher time (5.5.1). |
| 4 | The AES-128-GCM path initialised the context and loaded the key inside every timed call. ASCON-128 has no equivalent step. | The measured time and energy of AES include a per-call setup that is not present for ASCON, which is realistic for a node that loses RAM in deep sleep, but the two are only comparable if this is stated. |
| 5 | Each trial ran once after a fresh boot, followed by a Wi-Fi reconnect. | Cold-start effects (empty instruction cache, first use of peripherals) are included in the trial, and are larger for the AES path than for ASCON (5.5.1). |
| 6 | ASCON-128 and AES-128-GCM were collected in separate sessions. | Session conditions (temperature, supply, Wi-Fi environment) can differ between the two datasets. |
| 7 | The firmware ran at 160 MHz. | Chapter 3 states 240 MHz; this is corrected. |
| 8 | The wake timer in the committed firmware is 1 s; earlier commits used 60 s. About 127,000 logged trials at 60 s each would take about 88 days. [CONFIRM 2] | The sleep phase was never measured, and the collection did not use a 60-second sleep for all trials. The 60 s interval is treated in this dissertation as a modelled parameter (4.2.4, 5.4.8). |

*Table 9 – Audit of the Campaign A measurement method.*

Items 1 to 3 are the reason why Campaign A cannot be used for energy conclusions. Items 4 and 5 explain why parts of it remain informative and are used in the comparison of 5.5.

---

## 5.3 Validation Design (Campaign B)

### 5.3.1 Principle
Campaign B measures the energy of the cipher call without the problems of Table 9. Instead of bracketing one call, it repeats the call back-to-back for 700 ms while the INA219 averages current, and compares that with the idle level measured immediately before and after. The extra current, multiplied by the bus voltage and the time per call, gives the energy per call. The INA219 was configured for 128-sample averaging on the shunt channel (about 68 ms per result, register value 0x39FF), so a 700 ms window contains several complete, clean results. Because every reading contains the same constant sensor offset, the offset cancels in the load-minus-idle difference.

Figure 12 shows the durations involved, and Figure 13 the structure of one measurement.

### 5.3.2 Procedure
The firmware is a separate program (`validation_fw`) that reuses the ASCON-128 source file of Campaign A and the same key, payload generator and build settings. It does not use Wi-Fi, MQTT or deep sleep. For each configuration (a cipher variant and a payload size):

1. **Idle window**, 400 ms, with the worker task blocked. The first 150 ms are discarded so that the INA219 averaging window has settled. Mean current I_idle,pre is taken from the remainder.
2. **Load window**, 700 ms. A worker task pinned to core 1 calls the cipher back-to-back and counts the calls and the elapsed time (`esp_timer_get_time()`). Core 0 polls the INA219 about every 10 ms. The first 200 ms (about three INA219 result periods) are discarded. Mean current I_load is taken from the remainder.
3. **Idle window**, as in step 1, giving I_idle,post.

The energy per call is

E_op = V_bus × (I_load − Ī_idle) × t_op,  (Equation 6)

where Ī_idle is the mean of the two idle values, V_bus the mean measured bus voltage (about 4.72 V) and t_op the elapsed time divided by the number of calls. Per-byte energy is E_op divided by the payload size.

### 5.3.3 Variants
| Variant | What one call does | Purpose |
|---|---|---|
| ASCON | `ascon128_encrypt` (software) | Lightweight cipher |
| AES_COLD | initialise GCM context, load key, encrypt and authenticate, release | The sequence used in Campaign A; the situation of a node that loses RAM in deep sleep |
| AES_WARM | encrypt and authenticate only; the context is prepared once before the window | AES with the setup amortised |
| AES_SETKEY | initialise context, load key, release, with no encryption | The setup cost in isolation |

*Table 10 – Cipher variants in Campaign B.*

All configurations are run within each replicate in a shuffled order (fixed seed), so that the two ciphers share the same session, temperature and supply conditions.

### 5.3.4 Runs
**Run 1** covered 18 payload sizes (16, 64, 128, 256 to 448 in steps of 16, 800 and 1,600 bytes) with 10 replicates (550 rows). **Run 2** was a fine sweep of 64 to 128 bytes in steps of 8, with 15 replicates (420 rows), designed after Run 1 located the crossing between 64 and 128 bytes. The setup-only variant was included in both runs.

### 5.3.5 Statistics
Per-configuration means, standard deviations and 95% confidence intervals (Student's t) were computed over replicates. Differences between ciphers were tested per payload size with a two-sided paired t-test on the per-replicate differences (each replicate contains both ciphers), with Holm correction across the sizes of a run (family-wise α = 0.01). The break-even was found by linear interpolation of the sign change in the mean difference, and its 95% interval by a bootstrap of replicates (5,000 resamples, replicates kept paired across sizes). No outlier removal, filtering or offset correction was applied.

---

## 5.4 Validation Results

### 5.4.1 Data quality
All 970 rows (550 in Run 1, 420 in Run 2) were retained. The extra current under load was between 12.8 and 16.7 mA in every row. The two idle windows of a replicate differed by +0.006 mA on average in Run 1 and +0.009 mA in Run 2 (standard deviations 0.07 and 0.11 mA). Across replicates the median coefficient of variation was 0.3% for energy per call and below 0.001% for time per call.

### 5.4.2 Time per operation and throughput

| Payload (B) | ASCON (µs) | AES_COLD (µs) | AES_WARM (µs) |
|---|---|---|---|
| 16 | 57.9 | 102.8 | 57.4 |
| 64 | 114.5 | 145.8 | 100.5 |
| 128 | 190.0 | 203.2 | 157.9 |
| 352 | 454.3 | 404.1 | 358.9 |
| 800 | 982.8 | 806.0 | 760.8 |
| 1,600 | 1,926.6 | 1,523.5 | 1,478.5 |

*Table 11 – Time per operation (Run 1 means).*

Time was linear in payload size for all variants (R² > 0.9999): ASCON-128 added 1.180 µs per byte (intercept 39.0 µs), AES-128-GCM 0.897 µs per byte (intercepts 88.4 µs with setup on each call, 43.1 µs with the context reused). Throughput at 1,600 bytes was 0.83 MB/s for ASCON-128 and 1.05 MB/s (setup each call) or 1.08 MB/s (context reused) for AES-128-GCM. ASCON-128 was faster below about 175 bytes (interpolated between 128 and 256 bytes) and AES-128-GCM above it (Figure 14).

### 5.4.3 Setup cost of the AES-GCM context
The setup step alone took **30.9 µs and 1.90 µJ** per call (95% confidence interval for energy 1.89 to 1.90 µJ), and the value was the same in Run 1 and Run 2 to three digits. The difference between the AES_COLD and AES_WARM fitted intercepts was 45.4 µs and 2.82 µJ, so the measured setup step accounts for about two thirds of it; the remainder was not isolated (Figure 15).

### 5.4.4 Extra power
Averaged over payload sizes of 256 bytes and above, the extra power above idle was 75.3 mW for ASCON-128, 67.8 mW for AES-128-GCM (setup each call) and 68.5 mW for AES-128-GCM (context reused). The setup step drew 61.3 mW. ASCON-128 power was constant over payload size (75.1 to 75.4 mW), and AES power rose slightly with size (63.8 mW at 16 bytes to 68.7 mW at 1,600 bytes) as the setup was amortised (Figure 16). Idle current with Wi-Fi off was about 35 to 37 mA at 4.72 V.

### 5.4.5 Energy per operation and per byte

| Payload (B) | ASCON (µJ) | AES_COLD (µJ) | AES_WARM (µJ) | ASCON (µJ/B) | AES_COLD (µJ/B) | AES_WARM (µJ/B) |
|---|---|---|---|---|---|---|
| 16 | 4.35 | 6.56 | 3.75 | 0.272 | 0.410 | 0.234 |
| 64 | 8.62 | 9.54 | 6.73 | 0.135 | 0.149 | 0.105 |
| 128 | 14.30 | 13.48 | 10.69 | 0.112 | 0.105 | 0.084 |
| 352 | 34.19 | 27.36 | 24.59 | 0.097 | 0.078 | 0.070 |
| 800 | 74.01 | 55.13 | 52.36 | 0.093 | 0.069 | 0.065 |
| 1,600 | 145.17 | 104.67 | 101.94 | 0.091 | 0.065 | 0.064 |

*Table 12 – Energy per operation and per byte (Run 1 means).*

| Variant | Energy slope (µJ/B) | Energy intercept (µJ) | R² |
|---|---|---|---|
| ASCON | 0.0889 | 2.91 | > 0.9999 |
| AES_COLD | 0.0619 | 5.57 | > 0.9999 |
| AES_WARM | 0.0620 | 2.76 | > 0.9999 |

*Table 13 – Linear fits of energy per call against payload size (Run 1, 18 sizes; Figure 17).*

At 16 bytes ASCON-128 used 34% less energy than AES-128-GCM with setup on each call; at 1,600 bytes AES-128-GCM used 28% less.

### 5.4.6 Break-even payload size
The difference ASCON − AES_COLD was −0.93 µJ at 64 bytes and +0.81 µJ at 128 bytes in Run 1. The fine sweep of Run 2 located the crossing:

| Payload (B) | ASCON − AES_COLD (µJ) | Result (Holm-corrected, α = 0.01) |
|---|---|---|
| 64 | −0.871 | ASCON lower |
| 72 | −1.044 | ASCON lower |
| 80 | −0.465 | ASCON lower |
| 88 | −0.617 | ASCON lower |
| 96 | −0.007 | not significant (p = 0.78) |
| 104 | −0.196 | ASCON lower |
| 112 | +0.467 | AES lower |
| 120 | +0.234 | AES lower |
| 128 | +0.877 | AES lower |

*Table 14 – Fine sweep around the break-even (Run 2).*

Interpolation gave a break-even of **106 bytes**, with a 95% bootstrap interval of **96 to 107 bytes**; a clean crossing occurred in every resample (Figure 18 and Figure 19). At 96 bytes the ciphers could not be distinguished. Sizes that are not multiples of 16 (72, 88, 104, 120) fall slightly below their neighbours for AES, consistent with 16-byte blocks; this explains the small zig-zag and the asymmetry of the interval. Where the two runs overlapped (64 and 128 bytes), mean ASCON energy differed by 0.04 and 0.07 µJ (below 0.5%) and AES_COLD by 0.01 and 0.002 µJ.

The fitted lines of Table 13 give an independent estimate: (5.57 − 2.91) / (0.0889 − 0.0619) ≈ 99 bytes, in agreement with the direct measurement. The break-even is therefore approximately **100 bytes (96 to 107 bytes)** when AES-128-GCM sets up its context on each message.

### 5.4.7 Effect of reusing the AES context
With the context reused (AES_WARM), AES-128-GCM used less energy than ASCON-128 at every size from 64 bytes upward (by 1.9 µJ at 64 bytes and 43.2 µJ at 1,600 bytes). At 16 bytes the two were within 0.6 µJ, with times of 57.4 and 57.9 µs. No break-even exists in that case.

### 5.4.8 Encryption within a modelled duty cycle
The sleep phase was modelled as E_sleep = 3.3 V × I_sleep × 60 s (Equation 4), with I_sleep = 5 µA (990 µJ) and 10 µA (1,980 µJ) shown as two cases **[VERIFY 1: use the ESP32 datasheet figure]**.

| Payload (B) | ASCON active (µJ) | AES_COLD active (µJ) | Difference, % of cycle (5 µA) | Difference, % of cycle (10 µA) |
|---|---|---|---|---|
| 16 | 4.35 | 6.56 | 0.22% (AES higher) | 0.11% |
| 352 | 34.19 | 27.36 | 0.67% (ASCON higher) | 0.34% |
| 1,600 | 145.17 | 104.67 | 3.57% (ASCON higher) | 1.9% |

*Table 15 – Effect of the cipher choice on modelled cycle energy (transmission and wake-up not included; Figure 21).*

Encryption was 0.4% of the modelled cycle at 16 bytes and 13% at 1,600 bytes (ASCON-128, 5 µA case), and the cipher choice changed total cycle energy by under 4% at all tested sizes.

---

## 5.5 Re-examination of the Campaign A Results

### 5.5.1 Side-by-side comparison
Campaign A and Campaign B share eight payload sizes. Time in Campaign A exceeded Campaign B by a nearly constant amount for each cipher:

| Payload (B) | ASCON A (µs) | ASCON B (µs) | Difference | AES A (µs) | AES_COLD B (µs) | Difference |
|---|---|---|---|---|---|---|
| 16 | 1,370.9 | 57.9 | 1,313 | 1,740.8 | 102.8 | 1,638 |
| 64 | 1,428.3 | 114.5 | 1,314 | 1,784.5 | 145.8 | 1,639 |
| 128 | 1,504.6 | 190.0 | 1,315 | 1,841.6 | 203.2 | 1,638 |
| 256 | 1,658.0 | 341.0 | 1,317 | 1,957.5 | 318.0 | 1,639 |
| 352 | 1,772.7 | 454.3 | 1,318 | 2,043.9 | 404.1 | 1,640 |
| 448 | 1,887.7 | 567.6 | 1,320 | 2,130.4 | 490.2 | 1,640 |
| 800 | 2,309.0 | 982.8 | 1,326 | 2,447.4 | 806.0 | 1,641 |
| 1,600 | 3,266.5 | 1,926.6 | 1,340 | 3,167.6 | 1,523.5 | 1,644 |

*Table 16 – Time per operation in Campaign A and Campaign B.*

Three observations follow. First, the slopes agree: 1.197 against 1.180 µs/B for ASCON-128 and 0.901 against 0.897 µs/B for AES-128-GCM (differences of 1.4% and 0.4%). The time measurements of Campaign A are therefore sound as *increments*. Second, the offset is about 1.31 ms for ASCON-128 and 1.64 ms for AES-128-GCM, which is the instrumentation and cold-start cost of Table 9. Third, the offset is about 325 µs larger for AES-128-GCM, which is far more than the measured setup step (30.9 µs). The most plausible contributor is a first-execution effect after boot, which was **not tested** and is proposed as future work (7.5). The time crossover of Campaign A near 1,250 bytes is largely produced by this 325 µs difference in offsets (it would lie near 1,150 bytes from the offset difference and the slope difference alone), and the crossover of the cipher calls themselves is near 175 bytes (5.4.2).

Power and energy did not agree:

| Payload (B) | ASCON A power (mW) | ASCON B power (mW) | AES A power (mW) | AES_COLD B power (mW) | ASCON A energy (µJ) | ASCON B energy (µJ) | AES A energy (µJ) | AES_COLD B energy (µJ) |
|---|---|---|---|---|---|---|---|---|
| 16 | 20.3 | 75.1 | 24.2 | 63.8 | 27.9 | 4.35 | 42.1 | 6.56 |
| 64 | 19.8 | 75.2 | 26.0 | 65.4 | 28.3 | 8.62 | 46.3 | 9.54 |
| 128 | 19.7 | 75.2 | 25.1 | 66.4 | 29.7 | 14.30 | 46.3 | 13.48 |
| 256 | 19.8 | 75.3 | 25.7 | 67.4 | 32.8 | 25.66 | 50.4 | 21.42 |
| 352 | 21.1 | 75.3 | 14.8 | 67.7 | 37.3 | 34.19 | 30.2 | 27.36 |
| 448 | 20.4 | 75.2 | 16.8 | 68.0 | 38.6 | 42.70 | 35.9 | 33.32 |
| 800 | 52.2 | 75.3 | 22.2 | 68.4 | 120.5 | 74.01 | 54.3 | 55.13 |
| 1,600 | 52.8 | 75.4 | 48.1 | 68.7 | 172.6 | 145.17 | 152.4 | 104.67 |

*Table 17 – Extra power and energy per operation in Campaign A and Campaign B.*

Campaign A power was 20 to 25 mW for both ciphers at small sizes against 64 to 75 mW in Campaign B, and it changed in **steps** that Campaign B does not show: ASCON-128 from 19.8 to 52.6 mW between 560 and 576 bytes, AES-128-GCM from 24.9 to 14.8 mW between 336 and 352 bytes, and from 21.9 to 47.8 mW between 1,520 and 1,536 bytes (Figure 20). A constant per-call power such as the one measured in Campaign B does not change in steps with payload size. Consequently Campaign A energy at 16 bytes was 6.4 times the validated value for both ciphers, and at 1,600 bytes 19% (ASCON) and 46% (AES) too high.

### 5.5.2 The origin of the 347-byte break-even (review question 2)
The Campaign A energy per byte of AES-128-GCM fell abruptly from 0.150 µJ/B at 336 bytes to 0.086 µJ/B at 352 bytes (a 43% drop), whereas AES time rose smoothly from 2,029 to 2,044 µs over the same step. The whole drop is caused by the measured AES power falling from 24.85 to 14.75 mW (−10.1 mW, −41%). ASCON-128 energy per byte was 0.107 µJ/B at 336 bytes (the value of 0.017 in Table 5 is a typing error) and 0.106 µJ/B at 352 bytes. The sign change of the ASCON − AES difference, and hence the 347-byte break-even, therefore coincides exactly with this discontinuity.

A counterfactual check supports this. If the AES power is held at its mean below the step (25.5 mW) and all else is left as measured, the Campaign A crossing moves from 347 to about 564 bytes, and if the ASCON power is also held at its pre-step level (20.2 mW), so that neither step is present, no crossing occurs at all. These calculations are illustrative, since the measured power values are themselves unreliable, but they show that the crossing depends on a step in the power measurement and not on a smooth trade-off between fixed and per-byte costs.

### 5.5.3 Regression versus measured break-even (review question 2, continued)
The Campaign A regression lines (Table 4) give a break-even of (30.14 − 15.03) / (0.1068 − 0.0335) ≈ 206 bytes. A straight line was fitted to data that contained steps (AES at 340 bytes, ASCON at 570 bytes), which is why the energy fits had R² of only 0.43 for AES and 0.91 for ASCON. A line fitted through a stepped curve does not reproduce the crossing of the curve. The earlier statement that the difference was "expected" because of noise was therefore incomplete; the disagreement was a symptom of the measurement problem. In Campaign B the regressions have R² > 0.9999 and the fitted (99 bytes) and directly measured (96 to 107 bytes) break-evens agree.

### 5.5.4 The meaning of the regression intercept (review question 3)
A regression intercept is the value the fitted line takes at a payload of zero bytes, below the smallest size measured (16 bytes). It absorbs every fixed cost that does not depend on payload size, including measurement overhead, and it inherits the poor fit of the line (R² = 0.43 for AES in Campaign A). The Campaign A intercept of 30.14 µJ could not be attributed to hardware initialisation. Campaign B measured the initialisation step directly at 1.90 µJ (5.4.3), about one sixteenth of that figure. What survives from Campaign A is the ratio of the fitted fixed costs (30.14 to 15.03, about 2.0), which in Campaign B is 5.57 to 2.91 µJ (1.9). In this dissertation an intercept is therefore called a *fitted fixed cost*, and only the measured setup step is called the initialisation cost.

### 5.5.5 Outlier trimming (review question 4)
Campaign A trimmed 18.5% of the ASCON-128 rows and 15.9% of the AES-128-GCM rows (IQR rule with k = 1.5, per payload size, on time and power). The analysis was repeated without trimming and with k = 3 (calibration constants held fixed):

| | No trimming | IQR k = 3.0 | IQR k = 1.5 (used) |
|---|---|---|---|
| Rows (ASCON / AES) | 56,100 / 51,000 | 53,264 / 47,301 | 45,735 / 42,868 |
| Energy break-even (B) | 345.0 | 347.4 | 346.8 |
| Time crossover (B) | 1,245 | 1,267 | 1,267 |
| Sign changes of energy difference | 8 | 4 | 3 |

*Table 18 – Sensitivity of Campaign A to outlier trimming (row counts differ from Table 3 by at most 10 rows).*

The break-even was 345 to 347 bytes in all three cases. Trimming therefore did not create the result, and it is not the explanation for the difference with Campaign B: the step of 5.5.2 is a systematic effect present in the untrimmed data as well (Figure 22). Trimming did affect the noisiness of the curve (8 sign changes without trimming, 3 with). Campaign B involved no trimming, because it involves no calibration constant and no data-cleaning step that needed one.

### 5.5.6 Statistical testing (review question 5)
Campaign A applied 300 separate one-tailed Welch t-tests (100 sizes, three metrics) at α = 0.01 without adjustment for multiple comparisons, with the alternative hypothesis fixed as "ASCON greater than AES" at every size. Both choices were inappropriate: with 300 tests about three false positives are expected by chance alone, and the direction of the difference reverses across the break-even, so a single one-sided hypothesis holds only on one side of it. The tests were repeated two-sided and Holm-corrected:

| Sizes significant of 100 (α = 0.01) | Time | Power | Energy per byte |
|---|---|---|---|
| One-tailed, as originally reported | 21 | 78 | 72 |
| Two-sided, uncorrected | 100 | 99 | 93 |
| Two-sided, Holm-corrected | 100 | 99 | 92 |

*Table 19 – Campaign A per-size tests (IQR k = 1.5).*

The originally reported "execution time significant at only 21 sizes" reflected the fixed direction: ASCON-128 is slower than AES-128-GCM only above the time crossover near 1,250 bytes, which covers about 21 of the 100 sizes. Two-sided, the times differed at every size. The inference in Chapter 4 that the two execution times "converged" and that the energy difference was driven by power and not speed is therefore withdrawn. In Campaign B, the tests were two-sided, paired and Holm-corrected, and effect sizes are reported next to them.

---

## 5.6 Reliability and Validity of the Validation

**Signal and noise.** The extra current under load (12.8 to 16.7 mA) exceeded the drift of the idle baseline (about 0.01 mA on average, standard deviation about 0.1 mA) by two orders of magnitude.

**Repeatability.** The median coefficient of variation of energy across replicates was 0.3%. Two separate runs with different sizes and replicate counts agreed to within 0.5% at the overlapping sizes, and the AES setup cost was 1.896 and 1.895 µJ.

**Internal consistency.** Time and energy were linear in payload size (R² > 0.9999), and the break-even predicted by the fitted lines (99 bytes) agreed with the measured one (96 to 107 bytes). Campaign A failed this test (206 against 347 bytes).

**Independent paths.** Time comes from the CPU timer and current from the INA219. Energy ordering followed time ordering with a nearly constant power difference, and the increments of time agreed with Campaign A to within 1.4%.

**Design instead of clean-up.** The sensor offset cancels in the difference, the timed region contains only the cipher loop, the ciphers share one session in shuffled order, and no data were removed.

**What the validation does not show.** No independent reference instrument was used, so the absolute energy scale depends on the INA219 calibration, although the comparison between ciphers does not (same sensor, same offset). One board was used. The measurement is steady-state with Wi-Fi off, on one core, and does not include cold-start effects such as those suggested by the 325 µs difference of 5.5.1. Only the encryption of a payload with a 16-byte tag and no associated data was measured. Which parts of GCM run in the AES peripheral and which on the CPU was not established. Sleep, wake-up and transmission were not measured.

---

## 5.7 Summary of Changes to the Findings

| Finding in Chapter 4 | Status | Reason |
|---|---|---|
| Break-even of about 347 bytes | **Replaced** by about 100 bytes (96 to 107) for AES with per-message setup; none if the context is reused | 347 bytes coincided with a step in the measured AES power (5.5.2) |
| AES initialisation energy 30.14 µJ, fixed cost twice ASCON's (15.03 µJ) | **Replaced**: setup measured at 1.90 µJ; fitted fixed costs 5.57 and 2.91 µJ (ratio 1.9 survives) | Intercept extrapolated from a poor fit and including instrumentation (5.5.4) |
| AES energy slope lower than ASCON's | **Confirmed**, with corrected values 0.062 and 0.089 µJ/B (Campaign A: 0.0335 and 0.1068) | Campaign A slope for AES was distorted by the power steps |
| Time linear in payload size, slopes 1.197 and 0.901 µs/B | **Confirmed** (1.180 and 0.897 µs/B) | Increments in Campaign A were sound |
| Time crossover near 1,250 bytes | **Replaced** by about 175 bytes | Campaign A included a fixed offset larger for AES by about 325 µs |
| Power figures (20 to 52 mW) | **Withdrawn**; replaced by 75.3 mW (ASCON) and 67.8 mW (AES) | Two-reading method could not resolve the call (5.2.2) |
| Energy differences driven by power, not speed | **Withdrawn**; energy differences follow time, with a 10% power difference | One-tailed test artefact (5.5.6) |
| Significance at 21, 78 and 72 sizes | **Replaced** by 100, 99 and 92 (two-sided, Holm) for Campaign A; paired and Holm-corrected for Campaign B | Test direction and multiple comparisons |
| Break-even independent of trimming | **Confirmed** for Campaign A (345 to 347 bytes), but not evidence of validity | Systematic step in the data |
| AES-128-GCM uses about 24% more memory | **Retained**, not re-measured | Not affected by the timing and power method |
| Duty-cycle energy per byte of 63.62 and 64.51 µJ/B at 16 bytes | **Replaced** by the modelled shares of Table 15 | Sleep phase modelled; algorithms differ by under 4% |
| Literature conflict reconciled | **Retained in conditional form** | The literature comparison is now conditional on payload size and setup policy (Chapter 6) |
| Wake timer of 60 s, CPU of 240 MHz, ESP32-C3 datasheet and diagram | **Corrected** | Firmware and datasheet audit (Table 9) |

*Table 20 – Status of the Chapter 4 findings after validation.*

---

## 5.8 Summary of Chapter 5

Campaign A, the per-trial benchmark of Chapter 4, was audited and found unable to resolve the energy of a call lasting a few milliseconds: it used two instantaneous sensor readings, a timed region containing instrumentation, and separate sessions for the two ciphers. Campaign B, a sustained-load measurement with interleaved ciphers and no data removal, measured the AES-128-GCM setup step directly (30.9 µs, 1.90 µJ), found a break-even of about 100 bytes (96 to 107 bytes) when the setup is paid on every message, and found no break-even when the context is reused. Comparison with Campaign A showed that its time increments were sound, that its time offsets and power values were not, and that its 347-byte break-even coincides with a step in the measured AES power. The five review questions were answered: the regression disagreement was a symptom of that step, the intercept was not an initialisation energy, trimming did not create the result but the result was nonetheless not valid, and the statistical tests were redone two-sided and with correction for multiple comparisons. Chapter 6 interprets the corrected findings.
