# Chapter 04: Data Analysis and Results (revised, full replacement)

*Written in the past tense, as the existing chapter is. Figure and table numbers follow the list in `07_Figures_and_Appendices.md`. Items in [square brackets] are for you to confirm or fill; all are collected in `09_Open_Items.md`.*

---

## 4.1 Introduction

This chapter presents the results of the experimental evaluation described in Chapter 3, comparing software-based ASCON-128 with hardware-accelerated AES-128-GCM on the ESP32-WROOM-32E. Two datasets were produced, and the chapter explains why both are reported.

**Campaign A** (the per-trial benchmark) followed the design of Jin and Becker (2022) and produced 100 payload sizes with hundreds of complete sweeps per algorithm. During its analysis, the measurement method was found to be unable to resolve the energy of a call lasting about two milliseconds (4.2.3). **Campaign B** (the sustained-load validation) was therefore designed and run to measure energy directly. All energy, power and break-even conclusions in this chapter come from Campaign B. Campaign A is used for memory footprint (4.6) and is reported, with sensitivity checks, as a documented limitation (4.7.3 and Appendix C).

The chapter is organised around the three objectives of 1.8: energy per operation and the cost of initialising the AES-GCM context (Objective 1, 4.3 to 4.5); the contribution of encryption to a modelled duty cycle (Objective 2, 4.5.5); and the conditions under which ASCON-128 is preferable, including the break-even payload size (Objective 3, 4.5.2 to 4.5.4). Statistical tests are in 4.7 and a summary in 4.8.

---

## 4.2 Data Collection and Processing

### 4.2.1 Campaign A: per-trial benchmark
The Campaign A firmware produced one JSON record per encryption trial. The raw log for ASCON-128 contained 65,506 records and the log for AES-128-GCM 61,715; no malformed lines were found. Records were not de-duplicated by the trial `id`, because the counter is not guaranteed to increase independently across device resets. Sweeps were instead segmented by detecting a drop of the recorded payload size back to 16 bytes (Size = 16 × j, 3.3.1). This identified 699 candidate iterations for ASCON-128 and 646 for AES-128-GCM, more than the 500 configured repetitions because some were partial fragments left by device resets. Only iterations containing each of the 100 payload sizes exactly once were kept, giving 561 complete iterations for ASCON-128 and 510 for AES-128-GCM, with an identical sample count at every payload size within each algorithm.

| Algorithm | Raw rows | Malformed | Candidate iterations | Complete iterations | Rows after filter | Rows after IQR trim (k = 1.5) |
|---|---|---|---|---|---|---|
| ASCON-128 | 65,506 | 0 | 699 | 561 | 56,100 | 45,745 |
| AES-128-GCM | 61,715 | 0 | 646 | 510 | 51,000 | 42,870 |

*Table 3 – Campaign A row counts per cleaning stage.*

Campaign A also applied a zero-offset correction of 5.70 mA and a bus voltage of 4.674 V, estimated from the ASCON data and applied to both datasets, and IQR outlier trimming (k = 1.5) on execution time and power delta, per payload size. The procedure is detailed in Appendix C. Its effect on the conclusions was tested (4.7.3).

### 4.2.2 Campaign B: sustained-load validation
The design and procedure are described in 3.3.1. In summary:

| | Run 1 | Run 2 (fine sweep) |
|---|---|---|
| Payload sizes (bytes) | 16, 64, 128, 256 to 448 (step 16), 800, 1,600 (18 sizes) | 64 to 128 (step 8) (9 sizes) |
| Variants | ASCON, AES_COLD, AES_WARM at each size; AES_SETKEY once | same |
| Replicates | 10 | 15 |
| Configurations per replicate | 55 | 28 |
| Rows | 550 | 420 |
| CPU frequency | 160 MHz | 160 MHz |
| Load / idle window | 700 ms / 2 × 400 ms | same |

*Table 4 – Design of the validation campaign.*

No rows were removed from Campaign B: no outlier trimming, no offset correction and no filtering were applied, because the sensor offset cancels in the load-minus-idle difference and no reading fell outside the expected range (load minus idle current between 12.8 and 16.7 mA in all 970 rows). The idle level did not drift between the two idle windows of a replicate (mean +0.006 mA in Run 1 and +0.009 mA in Run 2; standard deviation 0.07 and 0.11 mA).

### 4.2.3 Why Campaign A could not be used for energy
Three properties of Campaign A, established by inspecting the firmware, prevent it from yielding a valid energy per operation.
1. **Sensor resolution.** Power was taken as the difference of two instantaneous INA219 readings. The INA219 is configured for 12-bit conversion (about 532 µs), and its registers hold the most recently completed conversion, so two readings a millisecond or two apart do not measure the current during the call.
2. **Timed region.** The timestamp pair enclosed the sensor reads, task creation and the cipher call. In Campaign B, encrypting 16 bytes with AES-128-GCM (context reused) took 57 µs, whereas Campaign A reported about 1,740 µs at 16 bytes; a current-plus-power read pair alone cost about 398 µs. Most of the Campaign A "execution time" is therefore instrumentation, not cryptography.
3. **Session confound.** ASCON-128 and AES-128-GCM were collected in separate sessions.

### 4.2.4 Sleep-phase energy (modelled)
The sleep phase was not measured. Following 3.3.4, it was modelled for a 60-second interval as

E_sleep = V_sleep × I_sleep × T_sleep  (Equation 4)

with V_sleep = 3.3 V and T_sleep = 60 s. For the deep-sleep current, the ESP32 datasheet figure for the RTC-timer-plus-RTC-memory configuration was used **[VERIFY 1: I_sleep = ? µA]**. Two cases are reported: 5 µA (E_sleep = 990 µJ; the figure used in the earlier draft) and 10 µA (1,980 µJ). The earlier draft took this current from the ESP32-C3 datasheet, which describes a different chip and was replaced. Because E_sleep is identical for both algorithms it cannot change which is more efficient or the break-even; it only sets the scale of the total (4.5.5). The transmission and wake-up phases were not measured and are not modelled.

---

## 4.3 Execution Time and Throughput (Campaign B)

### 4.3.1 Time per operation
Time per operation scaled linearly with payload size for all variants (R² > 0.9999). At 16 bytes, ASCON-128 took 57.9 µs, AES-128-GCM with setup on every call 102.8 µs, and AES-128-GCM with the context reused 57.4 µs. At 1,600 bytes the values were 1,926.6, 1,523.5 and 1,478.5 µs.

| Payload (B) | ASCON (µs) | AES_COLD (µs) | AES_WARM (µs) |
|---|---|---|---|
| 16 | 57.9 | 102.8 | 57.4 |
| 64 | 114.5 | 145.8 | 100.5 |
| 128 | 190.0 | 203.2 | 157.9 |
| 352 | 454.3 | 404.1 | 358.9 |
| 800 | 982.8 | 806.0 | 760.8 |
| 1,600 | 1,926.6 | 1,523.5 | 1,478.5 |

*Table 5 – Time per operation (mean of 10 replicates; the median coefficient of variation across replicates was below 0.001%).*

### 4.3.2 Linear scaling and throughput
Slopes and intercepts are in Table 8. ASCON-128 added 1.180 µs per byte and AES-128-GCM 0.897 µs per byte, giving a throughput at 1,600 bytes of 0.83 MB/s for ASCON-128, 1.05 MB/s for AES-128-GCM with setup each call and 1.08 MB/s with the context reused. Time crossover between ASCON-128 and AES_COLD, by interpolation between 128 and 256 bytes, was at about 175 bytes: below it ASCON-128 was faster, above it AES-128-GCM was.

### 4.3.3 Campaign A trial latency (for reference)
Campaign A reported a time of about 1.37 ms at 16 bytes for ASCON-128 and 1.74 ms for AES-128-GCM, rising to 3.27 ms and 3.17 ms at 1,600 bytes, with a time crossover near 1,250 bytes. As explained in 4.2.3, these figures include instrumentation and are called *trial latency*. They should not be read as cipher execution time.

---

## 4.4 Power Draw (Campaign B)

The extra power drawn while the cipher ran was similar for all variants, and its differences were small relative to the differences in time. Averaged over payload sizes of 256 bytes and above, ΔP was 75.3 mW for ASCON-128, 67.8 mW for AES-128-GCM (setup each call) and 68.5 mW for AES-128-GCM (context reused): ASCON-128 drew about 10% more power. The AES setup step alone drew 61.3 mW. Idle current with Wi-Fi off was about 35–37 mA at a mean bus voltage of 4.72 V.

This differs from the Campaign A power figures (20 to 52 mW, with ASCON-128 rising steeply with payload size), which are not used for the reason given in 4.2.3.

*Figure: mean ΔP by variant (bar chart, with 95% CI).*

---

## 4.5 Energy and Break-Even Analysis (Campaign B)

### 4.5.1 Energy per operation and per byte

| Payload (B) | ASCON (µJ) | AES_COLD (µJ) | AES_WARM (µJ) | ASCON (µJ/B) | AES_COLD (µJ/B) | AES_WARM (µJ/B) |
|---|---|---|---|---|---|---|
| 16 | 4.35 | 6.56 | 3.75 | 0.272 | 0.410 | 0.234 |
| 64 | 8.62 | 9.54 | 6.73 | 0.135 | 0.149 | 0.105 |
| 128 | 14.30 | 13.48 | 10.69 | 0.112 | 0.105 | 0.084 |
| 352 | 34.19 | 27.36 | 24.59 | 0.097 | 0.078 | 0.070 |
| 800 | 74.01 | 55.13 | 52.36 | 0.093 | 0.069 | 0.065 |
| 1,600 | 145.17 | 104.67 | 101.94 | 0.091 | 0.065 | 0.064 |

*Table 7 – Mean energy per operation and per byte (Run 1, 10 replicates; the median coefficient of variation across replicates was 0.3%).*

At 16 bytes ASCON-128 used 34% less energy per call than AES-128-GCM with setup on each call (4.35 versus 6.56 µJ). At 1,600 bytes it used 39% more (145.17 versus 104.67 µJ), i.e. AES-128-GCM used 28% less.

### 4.5.2 Linear fits and the fixed cost

| Variant | Time slope (µs/B) | Time intercept (µs) | Energy slope (µJ/B) | Energy intercept (µJ) | R² (time; energy) |
|---|---|---|---|---|---|
| ASCON | 1.180 | 39.0 | 0.0889 | 2.91 | > 0.9999; > 0.9999 |
| AES_COLD | 0.897 | 88.4 | 0.0619 | 5.57 | > 0.9999; > 0.9999 |
| AES_WARM | 0.897 | 43.1 | 0.0620 | 2.76 | > 0.9999; > 0.9999 |

*Table 8 – Linear fits of time and energy per call against payload size (Run 1, all 18 sizes).*

The directly measured setup cost (AES_SETKEY, context initialisation, key load and release without any encryption) was **30.9 µs and 1.90 µJ** (95% CI 1.89 to 1.90 µJ; identical in Run 1 and Run 2 to three digits). The difference between the fitted intercepts of AES_COLD and AES_WARM was 2.82 µJ and 45.4 µs; the measured setup step therefore accounts for about two thirds of the fitted intercept gap. The remainder was not isolated (5.2.2).

Solving the fitted lines for equal energy, (5.57 − 2.91) / (0.0889 − 0.0619), gives a break-even of about **99 bytes**, in agreement with the directly measured crossing below. (In Campaign A the corresponding calculation gave 206 bytes against a measured 347; that disagreement was a symptom of the instrumentation problem, 5.2.5.)

### 4.5.3 Break-even payload size
The sign of the per-size difference (ASCON minus AES_COLD, energy per operation) was tracked across sizes.

- **Run 1** (coarse): the difference was −0.93 µJ at 64 bytes and +0.81 µJ at 128 bytes, so the crossing lay between them (interpolated: 98 bytes).
- **Run 2** (fine sweep, 15 replicates):

| Payload (B) | ASCON − AES_COLD (µJ) | Result (paired t, Holm, α = 0.01) |
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

*Table 10 – Fine sweep around the break-even (Run 2).*

Interpolation gave a break-even of **106 bytes**, with a 95% bootstrap interval of **96 to 107 bytes** (5,000 resamples of replicates; a clean crossing occurred in every resample). At 96 bytes the algorithms could not be distinguished. Values for sizes that are not multiples of 16 (72, 88, 104, 120) fall slightly below their neighbours for AES, which is consistent with AES processing 16-byte blocks; this produces the small zig-zag and the asymmetry of the interval. The two runs agree where they overlap: at 64 and 128 bytes, mean ASCON energy differed between runs by 0.04 and 0.07 µJ (below 0.5%), and AES_COLD by 0.01 and 0.002 µJ.

We therefore report the break-even as **approximately 100 bytes (96 to 107 bytes)** for the case in which AES-128-GCM sets up its context on each message.

### 4.5.4 The effect of context reuse
With the AES context prepared once and reused (AES_WARM), AES-128-GCM used less energy than ASCON-128 at every size from 64 bytes upward (by 1.9 µJ at 64 bytes and 43.2 µJ at 1,600 bytes), and at 16 bytes the two were within 0.6 µJ (times 57.4 and 57.9 µs). No break-even exists in that case.

Regime segmentation: below about 96 bytes (typical of narrow-band LPWAN messages), ASCON-128 used less energy than AES-128-GCM with per-message setup, with a mean difference of −0.7 µJ per call across the fine sweep from 64 to 88 bytes and −2.2 µJ at 16 bytes; above about 112 bytes AES-128-GCM was more efficient, and by 1,600 bytes the per-byte cost was 28% lower.

*Figures: energy per byte against payload size on a log axis, with the bootstrap interval marked; fine-sweep difference plot with error bars.*

### 4.5.5 Encryption within the modelled duty cycle
Adding the modelled sleep energy of 4.2.4 to the measured active-phase energy gives the energy of one modelled cycle with one message per wake.

| Payload (B) | Active ASCON (µJ) | Active AES_COLD (µJ) | Total ASCON, 5 µA (µJ) | Difference as % of total (5 µA) | Difference as % of total (10 µA) |
|---|---|---|---|---|---|
| 16 | 4.35 | 6.56 | 994.35 | 0.22% (AES higher) | 0.11% |
| 352 | 34.19 | 27.36 | 1,024.19 | 0.67% (ASCON higher) | 0.34% |
| 1,600 | 145.17 | 104.67 | 1,135.17 | 3.57% (ASCON higher) | 1.9% |

*Table 11 – Effect of the cipher choice on modelled duty-cycle energy (sleep energy 990 µJ, or 1,980 µJ at 10 µA; transmission and wake-up not included).*

The encryption phase was 0.4% of the modelled cycle at 16 bytes and 13% at 1,600 bytes (ASCON-128, 5 µA case). With a 60-second sleep interval and a chip-level sleep current, the cipher choice therefore changed total energy by under 4% at all tested sizes.

---

## 4.6 Memory Footprint (Campaign A)

Memory footprint was computed per trial as peak heap plus stack use and averaged over payload sizes. ASCON-128 had a mean footprint of 2,772.8 bytes and AES-128-GCM 3,441.0 bytes, about 668 bytes or 24% higher. The difference was nearly constant across payload sizes (ASCON-128: 2,771.0 bytes at 16 bytes and 2,767.6 at 1,600 bytes; AES-128-GCM: 3,463.2 and 3,449.5 bytes), consistent with fixed-size context structures in the mbedTLS library. This measurement does not depend on the timing and power methods criticised in 4.2.3; it measures run-time heap and stack only, not code size in flash.

*Figure 11 (unchanged): memory footprint comparison.*

---

## 4.7 Statistical Analysis

### 4.7.1 Campaign B: paired tests
For each payload size, paired two-sided t-tests were run on the per-replicate energy difference (ASCON − AES_COLD) and corrected with the Holm procedure (family-wise α = 0.01). In Run 1, all 18 sizes were significant after correction; in Run 2, 8 of 9 sizes were (the exception was 96 bytes, p = 0.78, the estimated break-even). Because significance is nearly guaranteed with low-noise repeated measurements, the effect sizes in Tables 7 and 10, and the bootstrap interval of 4.5.3, carry the interpretation. Against AES_WARM, all sizes in both runs were significant and ASCON-128 used more energy at every size from 64 bytes upward (Run 1 difference +0.6 µJ at 16 bytes, +1.9 µJ at 64 bytes).

### 4.7.2 Regression
See Table 8 and 4.5.2. The regressions of Campaign B are tight (R² > 0.9999), unlike those of Campaign A (R² 0.91 for ASCON and 0.43 for AES energy), which is itself an indicator of the difference in measurement quality.

### 4.7.3 Campaign A: sensitivity to trimming and multiple testing
Two checks addressed concerns about the Campaign A analysis: whether outlier trimming changed its conclusions, and whether the per-size tests were appropriate.

| | No trimming | IQR k = 3.0 | IQR k = 1.5 (used) |
|---|---|---|---|
| Rows (ASCON / AES) | 56,100 / 51,000 | 53,264 / 47,301 | 45,735 / 42,868 |
| Energy break-even (B) | 345.0 | 347.4 | 346.8 |
| Time crossover (B) | 1,245 | 1,267 | 1,267 |
| Sign changes of energy difference | 8 | 4 | 3 |

*Table 14 – Campaign A sensitivity to outlier trimming (calibration constants held fixed; row counts differ from Table 3 by at most 10 rows because of that).*

The Campaign A break-even of about 347 bytes did not depend on the trimming (345 to 347 bytes in all three variants), so trimming did not create it. The number of sign changes did depend on trimming (8 without, 3 with), indicating a noisier curve when outliers were retained.

| Sizes significant of 100 (α = 0.01) | Time | Power | Energy per byte |
|---|---|---|---|
| One-tailed (H₁: ASCON > AES), as originally reported | 21 | 78 | 72 |
| Two-sided, uncorrected | 100 | 99 | 93 |
| Two-sided, Holm-corrected | 100 | 99 | 92 |

*Table 15 – Campaign A per-size tests (k = 1.5).*

The originally reported execution-time result (significant at only 21 sizes) was an effect of the one-tailed direction: the hypothesis "ASCON slower than AES" holds only above the time crossover near 1,250 bytes, which covers about 21 of the 100 sizes. Two-sided, the times differed significantly at every size. The earlier interpretation that execution times "converged" and that the energy gap was driven by power rather than speed is therefore withdrawn (5.2.4).

---

## 4.8 Summary of Chapter 4

1. **Objective 1.** Setting up the AES-128-GCM context cost 30.9 µs and 1.9 µJ per call; the fitted fixed energy costs were 2.9 µJ (ASCON-128) and 5.6 µJ (AES-128-GCM with setup each call). Energy scaled linearly, at 0.089 µJ/B for ASCON-128 and 0.062 µJ/B for AES-128-GCM.
2. **Objective 2.** Encryption was 0.4% to 13% of a modelled 60-second duty cycle; the cipher choice moved total energy by under 4%.
3. **Objective 3.** With per-message AES setup, the break-even was approximately 100 bytes (95% CI 96 to 107 bytes): ASCON-128 below, AES-128-GCM above. With a reused AES context, AES-128-GCM was equal or better at every size. AES-128-GCM used about 24% more memory.
4. **Method finding.** The per-trial method of Campaign A could not measure energy of a millisecond-scale call; its 347-byte break-even was reproducible under trimming but was not supported by the sustained-load measurement.

Chapter 5 interprets these findings.
