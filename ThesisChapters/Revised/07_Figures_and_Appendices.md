# Figures to add or change, and what the appendices should contain

---

## A. Figures

### A.1 Redraw (supervisor's Comment 1)

**Figure 1 – Firmware flowcharts (redraw to ISO 5807).** Use one symbol set consistently:

| Meaning | Symbol |
|---|---|
| Start / End of the program | Rounded terminator, labelled **Start** or **End** |
| Function entry / exit | Terminator labelled **Function name()** and **Return** (every function ends in *Return*; only `main` ends in *End*) |
| Processing step | Rectangle |
| Call to another routine | Rectangle with double side bars |
| Decision | Diamond with labelled **Yes / No** exits |
| Input / output (MQTT publish, serial print) | Parallelogram |
| Flow | Arrows only, no unlabelled branches |

Specific defects to correct in the current figure:
1. `Stop main()`, `Stop RUN_TRIAL()` and `Return …` are all used for the same thing. Use *End* for main and *Return* for functions.
2. "EUN_TRIAL" is a typo for `RUN_TRIAL`.
3. The inner loop bound "j ≤ X" should read "j ≤ 100".
4. The nonce decision has no Yes/No labels and the AES-GCM branch appears to lead to `random_bytes(16)`; AES-GCM → 12 bytes, ASCON → 16 bytes.
5. Add the missing duty-cycle steps (Sense and Transmit) or state that Sense is a placeholder and Transmit is the MQTT publish.
6. Split into panels: (a) main loop, (b) `RUN_TRIAL`, (c) `GENERATE_NONCE`, (d) `ENCRYPT_AND_MEASURE`, (e) `SLEEP_AND_MEASURE`.
7. Update the sleep block to match the firmware (see [CONFIRM 2]).

**Figure 1b (new) – Validation firmware flowchart** in the same style: shuffle configurations → idle window → start worker → load window → stop worker → idle window → print record → next configuration → next replicate.

**Figure 2 – Replace** the ESP32-C3 block diagram with the ESP32 (Xtensa LX6) block diagram.

**Figure 6 caption / wiring** – label the 10 kΩ resistor or remove it.

### A.2 New figures for Chapter 3

| # | Figure | Purpose |
|---|---|---|
| New | **Timing diagram of one configuration**: idle → load → idle windows on a time axis, with the INA219 conversion cycles (about 68 ms) drawn beneath and the discarded portions shaded | Shows why the method works and what is discarded |
| New | **Sensor timing versus call length** (to scale): a 532 µs INA219 conversion beside a ~2 ms call and a ~1.7 ms instrumentation overhead | Explains Campaign A's limitation visually |

### A.3 Figures for Chapter 4 (replace old Figures 7 to 10)

| Old | New | Content |
|---|---|---|
| Fig 7 | **Figure 7 – Time per operation vs payload size** (Campaign B) | 3 lines (ASCON, AES_COLD, AES_WARM), 95% CI band; inset for 16 to 448 B; mark the ~175 B time crossover |
| Fig 8 | **Figure 8 – Energy per operation vs payload with linear fits** | Points with error bars and fitted lines for the three variants; annotate slopes and intercepts (Table 8) |
| Fig 9 | **Figure 9 – Energy per byte vs payload, log x-axis** | ASCON vs AES_COLD vs AES_WARM; vertical line at 106 B with a shaded 96 to 107 B bootstrap band |
| Fig 10 | **Figure 10 – Fine sweep 64 to 128 B** | ASCON − AES_COLD difference (µJ) with 95% CI per size, zero line, crossing marked; note the 16-byte-block zig-zag |
| New | **Figure – AES setup cost** | Stacked bar: AES_COLD = setup (1.9 µJ) + encrypt, next to AES_WARM and ASCON at 16 B; or bar of setup time and energy |
| New | **Figure – Extra power by variant** | Bar chart of ΔP (mW) with 95% CI |
| New | **Figure – Modelled duty cycle** | Stacked bars (sleep vs encryption energy) at 16, 352, 1,600 B for each cipher, with the sleep current stated |
| New | **Figure – Sensitivity of the Campaign A break-even to trimming** | Three bars (none, k = 3, k = 1.5) with the Campaign B break-even as a horizontal reference |
| Fig 11 | **Figure 11 – Memory footprint** | Keep as is |
| Old 7, 8 | Move the Campaign A time and energy plots to **Appendix C**, labelled "trial latency including instrumentation" | Keep the evidence, drop the interpretation |

Old **Figure 10 (total duty-cycle energy per byte)** should be dropped: the two curves are visually indistinguishable because the sleep term dominates, which the stacked-bar figure shows better.

### A.4 Generated figures (ready to insert)

Files are in `ThesisChapters/Revised/figures/` as 300-dpi PNG (for Word) and vector PDF. Regenerate any time with `python scripts/06_plots_validation.py`. Colours are colour-blind safe, and line styles and markers also differ so they survive black-and-white printing.

| File | Use as | Suggested caption |
|---|---|---|
| `fig07_time_per_operation` | Figure 7 (4.3) | Time per operation against payload size for the three variants (means of 10 replicates; the 95% confidence bands are narrower than the line width). Inset: 16 to 448 B. |
| `fig08_energy_fits` | Figure 8 (4.5.2) | Energy per operation with linear fits (Run 1). Slope and intercept for each variant are in the legend. |
| `fig09_energy_per_byte` | Figure 9 (4.5) | Energy per byte against payload size (log axis). The shaded band is the 95% bootstrap interval of the break-even (96 to 107 B). |
| `fig10_fine_sweep` | Figure 10 (4.5.3) | Fine sweep, Run 2: difference in energy per operation (ASCON − AES with setup on each call) with 95% confidence intervals of the paired difference. |
| `fig_aes_setup_cost` | new (4.5.2) | Composition of the 16-byte cost. The measured setup step accounts for about two thirds of the difference between the two AES variants; the rest was not isolated. |
| `fig_power_by_variant` | new (4.4) | Extra power drawn above idle. |
| `fig_modelled_duty_cycle` | new (4.5.5) | Encryption energy stacked on a modelled 60 s sleep, for two assumed deep-sleep currents. Labels give the encryption share of the cycle. Transmission and wake-up are not included. |
| `fig_campaignA_trimming_sensitivity` | new (4.7.3 or Appendix C) | Break-even from Campaign A under three trimming choices, against the validation result. |
| `fig_method_windows` | new (3.3.1) | Schematic of one configuration: idle, load and idle windows, discarded portions, and the INA219 averaged register lagging the true current. |
| `fig_sensor_timing_scale` | new (4.2.3) | Durations on a log scale. The 1,500 µs bar is an estimate of the instrumentation in Campaign A's timed region. |

Still to be drawn by you (not plots): **Figure 1 flowcharts** (draw.io or Visio, following A.1), **Figure 1b**, the **ESP32 block diagram** for Figure 2, and the memory figure (Figure 11 stays as it is).

Notes for the figures:
- The "sensor timing scale" bar for Campaign A instrumentation is an estimate (about 1.3 to 1.6 ms: the difference between Campaign A latency and Campaign B call time, which also holds the 398 µs sensor read pair). Keep the "(est.)" in the label.
- `fig_method_windows` is a schematic built from the real conversion time and window lengths, not measured data; the caption says so.

---

## B. Tables to renumber (Chapters 3 to 5)

Table 1 (encryption methods) and Table 2 (metrics) stay. Then: Table 3 (Campaign A row counts), Table 4 (validation design), Table 5 (time per operation), Table 6 (extra power by variant, add if you want it as a table in place of the bar chart), Table 7 (energy per op and per byte), Table 8 (fits), Table 9 (break-even summary, optional), Table 10 (fine sweep), Table 11 (modelled duty cycle), Table 12 (memory), Table 13 (paired tests summary, optional), Table 14 (Campaign A trimming sensitivity), Table 15 (Campaign A corrected tests), Table 16 (fixed and variable costs, Chapter 5). The chapter text uses these numbers; adjust in the list of tables. Equations: 1 throughput, 2 power, 3 energy per operation (sustained-load), 4 sleep-phase energy, 5 fixed plus variable cost.

---

## C. Appendices

**Appendix A: Firmware and build configuration**
- A.1 Key parts of the Campaign A firmware (`run_trial`, `encrypt_and_measure`, `power_monitor`), with the INA219 settings (register 0x399F, calibration 4096, 0.1 Ω).
- A.2 The Campaign B firmware `validation_fw/main/main.c` (full listing or the core loop and configuration list).
- A.3 Build configuration excerpt: ESP-IDF v5.3.1, target `esp32`, CPU 160 MHz, `CONFIG_MBEDTLS_HARDWARE_AES=y`, optimisation level, FreeRTOS tick, watchdog setting on core 1's idle task.
- A.4 The `git` commit hash of the code used for each campaign.

**Appendix B: Campaign B protocol and results tables**
- B.1 Step-by-step protocol (windows, discards, shuffling seed, replicate counts).
- B.2 Full per-size tables: mean, standard deviation and 95% CI of time per operation, extra power and energy for every variant and size, for Run 1 and Run 2 (from `processed/validation/*/validation_summary.csv`).
- B.3 Paired-test results per size, raw and Holm-adjusted p-values (from `validation_paired_tests_*.csv`).
- B.4 Bootstrap procedure and the distribution of resampled break-even values.
- B.5 Raw log excerpt (first and last 20 lines of each run), and the location of the full logs.

**Appendix C: Campaign A processing and sensitivity**
- C.1 Cleaning stages and row counts (Table 3 in detail).
- C.2 Zero-offset calibration: histogram of negative current readings, the 5.70 mA constant, the 4.674 V bus-voltage estimate, and a sensitivity check of the constant (for example 5.2 to 6.5 mA) **[not yet run; see 09_Open_Items.md]**.
- C.3 Trimming sensitivity (Table 14) and corrected tests (Table 15).
- C.4 The Campaign A time and energy plots (old Figures 7 and 8), labelled as instrumentation-inclusive.
- C.5 Explanation of the discrepancy between the regression-based (206 B) and measured (347 B) break-even.

**Appendix D: Statistical methods**
- Paired t-test, Welch t-test, Holm procedure (with a worked example), bootstrap interval, linear regression formulas, definitions of all symbols.

**Appendix E: Hardware details**
- Bill of materials, pin assignments (SDA 21, SCL 22, address 0x40), schematic and photograph, INA219 configuration bits for both campaigns and their conversion times, supply and bus-voltage measurements.

**Appendix F: Reproducibility**
- Repository layout, exact commands to build, flash and capture (PowerShell and Python), commands to reproduce every table and figure (`scripts/04_validation_analysis.py`, `scripts/05_original_sensitivity.py`, plotting script), software versions (ESP-IDF v5.3.1, Python 3.11, pandas 2.3.3, NumPy 2.2.3, SciPy 1.15.1), and where the raw logs are stored.

**Appendix G (optional): Changes made after supervisor review**
- A short table listing each review comment and where in the dissertation it was addressed. Useful for the supervisor; delete before final submission if the department does not want it in the document.
