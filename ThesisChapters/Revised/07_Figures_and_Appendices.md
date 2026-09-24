# Figures to add or change, and what the appendices should contain

*Updated against **Final Thesis V04.pdf** page/section numbers (the version circulating now). The previous draft of this file, and `10_Cross_Check_Report.md`, were written against V02 — treat section numbers below as current, and re-check that report's page numbers if you rely on them.*

---

## A. Figures

### A.0 The most urgent fix: the image currently under "Figure 10" is wrong

On p.43 (§4.5.1), the caption reads **"Figure 10-Total duty cycle energy per byte"**, but the chart actually placed there is titled *"Fine sweep around the break-even (Run 2, 15 replicates, 95% CI of the paired difference)"* — that is Campaign B's fine-sweep chart, not a Campaign A duty-cycle chart. This is not a captioning preference, it is a wrong image inserted under the wrong number.

**Fix (do this first, before anything else in this file):**
1. Remove that fine-sweep image from p.43. It belongs later, in Chapter 5 (see A.3, Figure 19 below).
2. In its place, insert `figures/total_duty_cycle_energy_per_byte.png` (already sitting unused in your root `figures/` folder — it was generated for exactly this slot and never inserted). Keep the existing caption, "Figure 10 – Total duty cycle energy per byte."
3. This means Figures 1–11 keep their current numbers. Nothing before Chapter 5 needs renumbering.

(If you'd rather follow the earlier recommendation to drop old Figure 10 outright, because the two sleep-dominated curves are visually indistinguishable — see the note at the end of A.3 — that is a valid alternative, but it forces Figure 11 to become Figure 10 and a matching edit to the List of Figures. Replacing the image, above, is the lower-disruption fix and is what's assumed for the rest of this file.)

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

Specific defects to correct in the current figure (p.24):
1. `Stop main()`, `Stop RUN_TRIAL()` and `Return …` are all used for the same thing. Use *End* for main and *Return* for functions.
2. "EUN_TRIAL" is a typo for `RUN_TRIAL`.
3. The inner loop bound "j ≤ X" should read "j ≤ 100".
4. The nonce decision has no Yes/No labels and the AES-GCM branch appears to lead to `random_bytes(16)`; AES-GCM → 12 bytes, ASCON → 16 bytes.
5. Add the missing duty-cycle steps (Sense and Transmit) or state that Sense is a placeholder and Transmit is the MQTT publish.
6. Split into panels: (a) main loop, (b) `RUN_TRIAL`, (c) `GENERATE_NONCE`, (d) `ENCRYPT_AND_MEASURE`, (e) `SLEEP_AND_MEASURE`.
7. Update the sleep block to match the firmware (see `09_Open_Items.md`, [CONFIRM 2]).

**Figure 1b (new) – Validation firmware flowchart**, same style: shuffle configurations → idle window → start worker → load window → stop worker → idle window → print record → next configuration → next replicate.

**Figure 2 (p.26) – Replace** the ESP32-C3 block diagram with the ESP32 (Xtensa LX6) block diagram — the board used is an ESP32-WROOM-32E, not a C3.

**Figure 6 (p.31) caption / wiring** – label the 10 kΩ resistor or remove it.

### A.2 Figures 1–11 (Chapters 3–4): no renumbering needed

Figures 1–9 and 11 are correctly captioned and correctly placed; leave their numbers alone. Only Figure 10 needs the A.0 fix above. The Campaign A time/energy plots (Figures 7, 8) may optionally be duplicated into Appendix C labelled "trial latency including instrumentation," but that is additive — it does not change their numbers in Chapter 4.

### A.3 New figures for Chapter 5 — exact numbers and insertion points

Chapter 5, as currently written, **cites nine figure numbers (12, 13, 14, 15, 16, 18, 19, 20, 22) with no images actually inserted anywhere**, and never mentions Figures 17 or 21 at all. Your eleven files in `ThesisChapters/Revised/figures/` fill exactly these eleven slots once the two silent gaps (17, 21) are given one sentence of prose each. Insert in this order, top to bottom of Chapter 5:

| Fig. # | File | Insert at | Status of the citation | Suggested caption |
|---|---|---|---|---|
| **12** | `fig_method_windows` | §5.3.1, right after "The extra current, multiplied by the bus voltage and the time per call, gives the energy per call." (the paragraph ending "...offset cancels in the load-minus-idle difference.") — this is where the text already says **"Figure 12 and 13"** | Already cited, just insert the image | Schematic of one configuration: idle, load and idle windows, discarded portions, and the INA219 averaged register lagging the true current. |
| **13** | `fig_sensor_timing_scale` | §5.3.1, same paragraph, second of the pair | Already cited | Durations on a log scale: 532 µs INA219 conversion vs a ~2 ms cipher call vs ~1.3–1.6 ms of Campaign A instrumentation (est.). |
| **14** | `fig07_time_per_operation` | §5.4.2, at the end of the paragraph "...ASCON-128 was faster below about 175 bytes... and AES-128-GCM above it **(Figure 14)**" | Already cited | Time per operation against payload size (three variants, means of 10 replicates); inset 16–448 B; ~175 B time crossover marked. |
| **15** | `fig_aes_setup_cost` | §5.4.3, end of paragraph "...the measured setup step accounts for about two thirds of it; the remainder was not isolated **(Figure 15)**" | Already cited | Composition of the 16-byte cost: AES_COLD = setup (1.90 µJ) + encrypt, next to AES_WARM and ASCON. |
| **16** | `fig_power_by_variant` | §5.4.4, end of paragraph "...as the setup was amortized **(Figure 16)**" | Already cited | Extra power drawn above idle, by variant, with 95% CI. |
| **17** | `fig08_energy_fits` | §5.4.5, immediately after Table 12 | **Not cited — add one sentence**, e.g. "The three fitted lines are shown in Figure 17." | Energy per operation with linear fits (Run 1); slope and intercept per variant in the legend. |
| **18** | `fig09_energy_per_byte` | §5.4.6, in "...a clean crossing occurred in every resample **(Figure 18** and Figure 19)" | Already cited (first of the pair) | Energy per byte against payload size (log axis); shaded band = 95% bootstrap interval of the break-even (96–107 B). |
| **19** | `fig10_fine_sweep` | §5.4.6, same sentence, second of the pair — **this is the image currently mis-inserted as old "Figure 10" on p.43; move it here** | Already cited (second of the pair) | Fine sweep, Run 2: ASCON − AES_COLD difference with 95% CI per size, zero line, crossing marked; note the 16-byte-block zig-zag. |
| **20** | `fig_modelled_duty_cycle` | §5.4.8, immediately after Table 14 | **Not cited — add one sentence**, e.g. "Figure 20 shows the encryption share of the modelled cycle at each payload size." | Encryption energy stacked on a modelled 60 s sleep, two assumed deep-sleep currents; labels give the encryption share of the cycle. |
| **21** | `fig_campaignA_vs_B` | §5.5.1, in "...and from 21.9 to 47.8 mW between 1,520 and 1,536 bytes **(Figure 20)**" | **Already cited, but as "Figure 20" — change that in-text number to "Figure 21"** once Figure 20 above is inserted at §5.4.8 | Side-by-side: Campaign A's stepped power/energy vs Campaign B's flat, validated values, at the eight shared payload sizes. |
| **22** | `fig_campaignA_trimming_sensitivity` | §5.5.5, end of paragraph "...the step of 5.5.2 is a systematic effect present in the untrimmed data as well **(Figure 22)**" | Already cited, correct number | Break-even under three trimming choices (none, k=3, k=1.5) against the Campaign B result as a horizontal reference. |

**The one required text edit**: in §5.5.1, change "(Figure 20)" to "(Figure 21)". Every other citation in Chapter 5 already has the right number — you only need to insert the images and add the two missing sentences (Figures 17 and 20).

Also add all eleven to the **List of Figures** (p.x), which currently stops at Figure 11.

### A.4 File locations

All eleven files are in `ThesisChapters/Revised/figures/` as 300-dpi PNG (for Word) and vector PDF, generated by `python scripts/06_plots_validation.py`. The one file needed for the A.0 fix, `total_duty_cycle_energy_per_byte.png`, is in the root `figures/` folder alongside the other four original Campaign A charts (`execution_time_scaling.png` → Fig. 7, `regression_scaling_overlay.png` → Fig. 8, `energy_per_byte_comparison.png` → Fig. 9, `memory_footprint_comparison.png` → Fig. 11). That folder also has `throughput_scaling.png`, which is not currently cited anywhere in the thesis — either add one sentence and a figure number for it in §4.3.2 (Throughput), or leave it out of the final document and drop it from the repo note.

Colours are colour-blind safe, and line styles/markers also differ so the figures survive black-and-white printing.

Notes:
- The "sensor timing scale" bar for Campaign A instrumentation is an estimate (about 1.3 to 1.6 ms — the difference between Campaign A latency and Campaign B call time). Keep the "(est.)" in the label.
- `fig_method_windows` is a schematic built from the real conversion time and window lengths, not measured data; the caption should say so.

Still to be drawn by hand (not generated plots): the **Figure 1 flowcharts** (A.1), **Figure 1b**, and the **ESP32 block diagram** for Figure 2.

---

## B. Tables: the actual numbering conflict, and how to resolve it

The List of Tables (p.x) stops at "Table 8 – Resource cost before encryption ... 62", matching the pre-Chapter-5 thesis. After Chapter 5 was inserted, two things happened:

1. Chapter 5 introduced its own **Table 8** ("Audit of the Campaign A measurement method," p.48–49) — colliding with the front matter's Table 8.
2. Chapter 5 continues Table 9 through Table 18 (Cipher variants, Time per operation, Energy per operation and per byte, Linear fits, Fine sweep, Modelled cycle effect, side-by-side Campaign A/B time, side-by-side power/energy, trimming sensitivity, corrected per-size tests). The table that the front matter still calls "Table 8" is, in the body, actually captioned **Table 19** (Chapter 6, "Resource cost before encryption," p.62).

**Fix:** renumber the front matter's List of Tables to match the body exactly: Tables 1–7 unchanged, then Table 8 = "Audit of the Campaign A measurement method" (p.48), Tables 9–18 as they appear in Chapter 5 (already correctly numbered in the body, just missing from the list), Table 19 = "Resource cost before encryption" (p.62, currently mislabelled "Table 8" only in the front matter, not in the body). Also fix the title mismatch at Table 7: the front matter says "ttest significance summary," the body (p.46) says "Campaign A per-size tests (IQR k=1.5)" — pick one and use it in both places.

## B.1 Equations: same root cause

- List of Equations (p.x) stops at Equation 4, "Energy per operation," p.63.
- The body has an *earlier* Equation 4 at §5.3.2 ("Energy per call equation," p.50) — a genuine duplicate number.
- §5.4.8 cites "(Equation 4)" for the sleep-phase formula, but that formula was already defined as **Equation 3** in §4.2.4. This cross-reference is simply wrong and should point to Equation 3.
- The formula the front matter's page-63 row describes is captioned **Equation 5** in the body (§6.2.2, "Energy per operation," the fixed-cost + variable-cost split).

**Fix:** renumber the front matter to Equation 1 Throughput (p.32), Equation 2 Total Power (p.33), Equation 3 Sleep-phase energy constant (p.39), Equation 4 Energy per call (p.50, §5.3.2), Equation 5 Energy per operation / fixed+variable split (p.63, §6.2.2). Correct the in-text cross-reference in §5.4.8 from "(Equation 4)" to "(Equation 3)".

## B.2 Section numbers to fix while you're in there

- Chapter 5 jumps **§5.6 → §5.8** ("Reliability and Validity of the Validation" straight to "Summary of Chapter 5"). Either there is a missing §5.7, or §5.8 should be renumbered to §5.7.
- Chapter 6's final section is headed **"6.5 Summary of Chapter 5"** — it is in Chapter 6 and closes Chapter 6; it should read "6.5 Summary of Chapter 6."

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
- C.3 Trimming sensitivity (Table 17) and corrected tests (Table 18).
- C.4 The Campaign A time and energy plots (Figures 7 and 8), optionally duplicated here labelled "trial latency including instrumentation."
- C.5 Explanation of the discrepancy between the regression-based (206 B) and measured (347 B) break-even.

**Appendix D: Statistical methods**
- Paired t-test, Welch t-test, Holm procedure (with a worked example), bootstrap interval, linear regression formulas, definitions of all symbols.

**Appendix E: Hardware details**
- Bill of materials, pin assignments (SDA 21, SCL 22, address 0x40), schematic and photograph, INA219 configuration bits for both campaigns and their conversion times, supply and bus-voltage measurements.

**Appendix F: Reproducibility**
- Repository layout, exact commands to build, flash and capture (PowerShell and Python), commands to reproduce every table and figure (`scripts/04_validation_analysis.py`, `scripts/05_original_sensitivity.py`, plotting script), software versions (ESP-IDF v5.3.1, Python 3.11, pandas 2.3.3, NumPy 2.2.3, SciPy 1.15.1), and where the raw logs are stored.

**Appendix G (optional): Changes made after supervisor review**
- A short table listing each review comment and where in the dissertation it was addressed. Useful for the supervisor; delete before final submission if the department does not want it in the document.
