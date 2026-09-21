# Chapter 3: revised sections

Sections not listed here (3.1, 3.2 and its subsections, 3.3.2, 3.3.3) stay as they are, apart from the small fixes at the end of this file. Section numbers are kept so that existing cross-references still work.

---

## 3.2.3 Common Evaluation Basis: replace the table and following paragraph

To strengthen the methodological rigour of the comparison, a controlled-variable design was used. Payload content, key, timing method, CPU frequency and build configuration were held constant across the two algorithms, and in the validation campaign (3.3.1) the algorithms were additionally interleaved within a single session.

| Metric | Description | Measurement method / tool |
|---|---|---|
| Execution time | Time for one encryption call | `esp_timer_get_time()` (1 µs resolution). In the validation campaign, total time for a long run of back-to-back calls divided by the number of calls |
| Throughput | Bytes processed per second | Payload size / time per call |
| Power draw | Extra electrical power drawn while the cipher runs, above the idle level | INA219 mean current over a load window minus mean current over neighbouring idle windows, multiplied by the mean bus voltage |
| Energy per operation | Extra energy for one call | Power draw × time per call (µJ) |
| Memory footprint | Peak heap plus stack used by one call | ESP-IDF heap and FreeRTOS stack watermark counters before and after the call |

*Table 2 – Summary of evaluation metrics and methods.*

The evaluation was implemented in the ESP-IDF framework (v5.3.1), the official development framework for the ESP32 [Al-Mashhadani & Shujaa, 2022].

---

## 3.3 Experimental Design

The experimental design has two parts, and the reason for having two is part of the methodology.

### 3.3.1 Overview of the Measurement Programs

**Campaign A: per-trial (instrumented) benchmark.** The first firmware follows the benchmarking structure of Jin and Becker (2022): an outer loop of repeated sweeps and an inner loop of 100 payload sizes (16 × j bytes, j = 1…100). Each trial, run once per boot, generates a nonce and payload, calls `start_monitor()`, encrypts in a dedicated task, calls `stop_monitor()`, reports the metrics over MQTT, and then enters deep sleep before the next trial. Power was estimated from one INA219 reading taken before and one after the encryption call. Figure 1 gives the flowchart.

Analysis of Campaign A (Chapter 4) showed that this design cannot resolve energy for a call lasting about 2 ms. Reasons: the INA219 needs about 532 µs per conversion, so the two readings do not bracket the call; the timed region also contained task creation and two sensor reads; and the two algorithms were collected in separate sessions. Campaign A is therefore retained for memory footprint and as a documented instrumentation limit, not as the source of energy results.

**Campaign B: sustained-load validation.** A second, separate firmware was written to measure energy without these limits. For each *configuration* (a cipher variant and a payload size), the program measures three consecutive windows on core 0 while a worker task on core 1 does the encryption:

1. an **idle window** (400 ms) with the worker blocked;
2. a **load window** (700 ms) in which the worker calls the cipher back-to-back, counting calls and elapsed time;
3. a second **idle window** (400 ms).

The first 150 ms of each idle window and the first 200 ms of the load window are discarded so that the INA219's averaging window has settled. Energy per call is then

E_op = V_bus × (I_load − Ī_idle) × t_op,  (Equation 3)

where Ī_idle is the mean of the two idle windows, V_bus is the mean measured bus voltage and t_op is the elapsed time divided by the number of calls. Because the constant zero-offset of the sensor appears in both I_load and Ī_idle, it cancels in the difference, so no offset correction or outlier removal is applied to Campaign B.

Four cipher variants were measured:

| Variant | What one call does |
|---|---|
| ASCON | `ascon128_encrypt` (software; the same source file as Campaign A) |
| AES_COLD | initialise context, load key, encrypt and authenticate, free context (the sequence used in Campaign A, and the situation of a node that loses RAM in deep sleep) |
| AES_WARM | encrypt and authenticate only; the context was prepared once before the window |
| AES_SETKEY | initialise context, load key, free context only (setup cost in isolation) |

Within each *replicate* all configurations were run once in a shuffled order (fixed pseudo-random seed), so ASCON and AES share the same session, temperature and supply conditions. Two runs were made: **Run 1** covered 18 payload sizes (16, 64, 128, 256 to 448 in steps of 16, 800 and 1,600 bytes) with 10 replicates; **Run 2** was a fine sweep of 64 to 128 bytes in steps of 8 with 15 replicates, designed after Run 1 located the crossover between 64 and 128 bytes. In Campaign B no Wi-Fi, MQTT or deep sleep is used.

Both campaigns use a fresh nonce per message for AES-128-GCM (12 bytes) and ASCON-128 (16 bytes). In Campaign B a counter is incremented per call, which does not change the cost of either cipher.

### 3.3.4 Duty-Cycle and Sleep Design

The duty cycle follows the environmental-monitoring design of Syahmi Md Dzahir and Seng Chia (2023): Sleep → Wake → Sense → Encrypt → Transmit → Sleep. Only the deep-sleep dimension of their design is adopted, in a bare-metal (non-FreeRTOS-optimised) configuration.

The reporting interval modelled in this dissertation is **60 seconds**. The sleep phase and the wake-up phase were **not measured**: the sleep-phase energy is added analytically (4.2.4). During Campaign A the firmware used a short wake timer between trials, to keep about 127,000 trials feasible, and reported each trial over Wi-Fi and MQTT. **[CONFIRM 2 in `09_Open_Items.md`: state here the timer value that the collected data really used.]** The transmit step of Campaign A carries the record to the logging dashboard; its energy is not separated from the encryption energy and is not used in the results.

This means the term "duty cycle" in this dissertation describes a *modelled* cycle whose encryption phase is measured and whose sleep phase is estimated. This limitation is repeated in 5.5.

---

## 3.4.1 Hardware Components: corrections

1. **Board and chip.** The test-bed uses an **ESP32-WROOM-32E** module on a development board (ESP32 chip revision v3.1 according to the boot log). Replace **Figure 2** with the functional block diagram of the **ESP32** (Xtensa LX6). The current figure shows the ESP32-C3 (a RISC-V chip) and must not be used.
2. **CPU frequency.** The firmware ran at **160 MHz** (ESP-IDF default for this project's `sdkconfig`), not 240 MHz. Replace any statement of 240 MHz in the description of the test-bed (3.4.1) **and in 2.1.2**, where the 240 MHz figure describes the ESP32 in general and may stay if worded as "up to 240 MHz".
3. **Power path and sensor position.** The INA219 sits in the 5 V supply line ahead of the development board, so the measured current includes the board's regulator, USB-UART bridge and indicator LED as well as the ESP32 (measured idle level: about 35–37 mA at a bus voltage of about 4.72 V with Wi-Fi off). This is why the validation campaign measures the *difference* between load and idle: everything that does not change with the cipher cancels.
4. **Bus voltage.** Use the measured mean bus voltage (4.72 V in Campaign B) in Equation 2 and Equation 3, not the nominal 5 V or 3.3 V. Remove statements that mix the two (the buck converter sentence in "Supporting infrastructure" and the "regulated 5 V" sentence in 3.5.3 must describe the same rail).
5. **INA219 configuration.**
   - Campaign A: 12-bit conversions, no averaging (register value 0x399F, 532 µs per conversion).
   - Campaign B: shunt ADC set to 128-sample averaging (about 68 ms per result), bus ADC 12-bit, continuous mode (0x39FF).
   - Shunt resistor 0.1 Ω, calibration register 4096, current LSB 0.1 mA.
6. **Remove** the phrases "microsecond-level precision" (3.4.1, 3.4.3 and the paragraph after Figure 6). The sensor does not provide that; the timing precision (1 µs) belongs to `esp_timer`, not to the INA219.

## 3.4.2 Software Environment and Libraries: corrections

- ESP-IDF **v5.3.1**, GCC toolchain for Xtensa, default (`-Og`) optimisation, FreeRTOS tick 100 Hz.
- The `mbedtls` version is the one bundled with ESP-IDF v5.3.1 (**[VERIFY 3]** the exact version number from the build log; the previous draft says 2.16.2, which does not match IDF 5.3.1).
- `CONFIG_MBEDTLS_HARDWARE_AES=y`: AES block operations are executed by the ESP32's AES peripheral. To make the "hardware" claim checkable, add the build-configuration excerpt to Appendix A.

## 3.4.3 and 3.4.4: corrections
- In the 3.4.3 text, refer to the figures as Figure 5 (schematic) and Figure 6 (test-bed) instead of "Fig 7".
- The wiring in Figure 6 shows a 10 kΩ resistor. State its purpose (I2C pull-ups or otherwise) or remove it from the figure.

---

## 3.5 Measurement Methodology (replace 3.5.1 to 3.5.4)

### 3.5.1 Execution Time
Time is measured with `esp_timer_get_time()`, a 64-bit microsecond counter (not the Arduino `micros()` function, which is not part of ESP-IDF). In Campaign A the timestamp pair brackets `start_monitor()`, task creation, the cipher call and `stop_monitor()`; this therefore measures *trial latency including instrumentation* (4.3.3), not the cipher alone. In Campaign B the timer brackets a loop of thousands of back-to-back calls, and the time per call is the elapsed time divided by the call count; per-call instrumentation cost is thereby spread to a negligible level.

To quantify the instrumentation cost inherent to Campaign A, the validation firmware also times one INA219 current-plus-power register read pair, which took about 398 µs on this test-bed. **[Re-run the task-creation overhead measurement, see 09_Open_Items.md: the first version of that measurement returned an invalid value and is not used.]**

### 3.5.2 Throughput
Throughput (B/s) = payload size (bytes) / time per call (s), from Campaign B (Equation 1, unchanged).

### 3.5.3 Power and Energy
Electrical power is P = V × I (Equation 2, unchanged). In Campaign B, the extra power drawn by the cipher is ΔP = V_bus × (I_load − Ī_idle), and the energy per call follows from Equation 3. Per-byte energy is E_op divided by payload size.

The validity of this method rests on three properties, tested in Chapter 4 and discussed in 5.4: (1) the load window contains several complete INA219 results, so the reading represents sustained draw; (2) constant offsets cancel; (3) the idle level does not drift between the windows (measured: +0.01 mA on average, standard deviation about 0.1 mA).

### 3.5.4 Memory Footprint
The memory-footprint measurement in Campaign A follows the *idea* of Pipiras (2024), snapshotting free memory before and after the operation, but is implemented with ESP-IDF, not MicroPython. Heap use is taken from `heap_caps_get_free_size()` and from the change in `heap_caps_get_minimum_free_size()` (peak use), and stack use from `uxTaskGetStackHighWaterMark()` in a dedicated task created for the cipher call, so that stack use of other work does not contaminate the reading. Footprint = peak heap + stack. This measures run-time memory only, not flash (code) size. Remove the statements about `gc.collect()`, `gc.mem_free()`, ucrypto and "each configuration repeated five times".

---

## 3.6 Data Collection and Extraction

Campaign A: each trial reports a JSON record (execution time, heap and stack counters, two current and power readings) over MQTT to a Node-RED dashboard, and the records were logged to a file. Campaign B: the firmware prints comma-separated records to the serial console (variant, size, calls, time per call, three mean currents, mean bus voltage, sample counts), and a capture script writes them to a log file. All logs and scripts are archived (Appendix F). Replace "As specified in your experimental setup" (which addresses the reader in the second person) with "In this study".

## 3.7 Data Analysis and Statistical Evaluation

### 3.7.1 Statistical Methods and Tools
- Per-configuration mean, standard deviation and 95% confidence interval (Student's t) over replicates, computed with pandas and SciPy.
- Campaign A additionally uses the cleaning pipeline described in 4.2 and Appendix C.

### 3.7.2 Significance and Comparison Methods (replaces the current text)
- **Paired tests.** In Campaign B, each replicate contains both algorithms measured within the same pass, so the per-size comparison is a *paired* t-test on the per-replicate energy differences.
- **Two-sided tests.** The direction of the difference reverses across the break-even, so no single one-sided hypothesis is appropriate; all tests are two-sided.
- **Multiple comparisons.** One test is run for each payload size; p-values are therefore adjusted for the family of tests using the Holm procedure (family-wise α = 0.01). The number of significant sizes is reported before and after correction.
- **Effect size.** Because with several hundred trials almost any difference is statistically significant, significance is always reported together with the size of the difference (µJ, %).
- **Break-even and its uncertainty.** The break-even is the payload size at which the per-size mean difference (ASCON − AES) changes sign, by linear interpolation between the two bracketing sizes. Its 95% confidence interval is obtained by a bootstrap (5,000 resamples of replicates, keeping replicates paired across sizes).
- **Regression.** Linear regression of mean time or energy on payload size; slope, intercept, standard error and R² are reported. The intercept is described as a *fitted fixed cost*, and is compared with the directly measured setup cost (AES_SETKEY) instead of being called initialisation energy on its own.
- **Sensitivity analysis for Campaign A.** The Campaign A break-even and test counts are recomputed without outlier trimming and with two trimming factors (Appendix C).

---

## Small fixes in the rest of Chapter 3
- 3.1: "positive paradigm" → "positivist paradigm"; "The approach of [Jin & Becker, 2022 facilitates" → missing closing bracket.
- 3.3.1 old text ("Outer Loop (): …", "Inner Loop (): …") has lost its symbols (i and j) in the PDF conversion. Restore *i* and *j* wherever they were lost, also in 3.3.2 and 3.5.
- Figure 1: redraw as described in `07_Figures_and_Appendices.md`. In the text, refer to it as "Figure 1" without "Main Setup and Nested Loop Control flowchart".
- 3.3.2: "Each data point is executed and measured 500 times" should say that the outer loop was configured for 500 repetitions and that 561 and 510 *complete* sweeps were obtained (4.2.1).
