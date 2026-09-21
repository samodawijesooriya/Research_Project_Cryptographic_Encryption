# The validation experiment: what was found, and why it can be trusted

*For you and your supervisor. Plain language first, details after.*

---

## 1. In plain terms

Your supervisor asked five questions. Checking them led to a bigger finding than any of the five: the way the original benchmark measured energy could not work for an operation this short.

- The original firmware estimated power from **two instant sensor readings** around one encryption. The sensor takes about half a millisecond to produce one reading, and the encryption lasted about two milliseconds, so those two readings did not describe the encryption.
- The original "execution time" also included **creating a task and two sensor reads**, about 1.3 to 1.6 ms, while the encryption itself takes 58 to 103 µs for a small payload.
- The two algorithms were measured on **separate days**.

So a new test program was written (`validation_fw/`). It runs one encryption **over and over for 0.7 seconds** while the sensor averages the current, compares against idle just before and after, and mixes the two algorithms in random order in one session. That gives a clean measurement of energy per encryption.

## 2. What it found

| Question                                  | Answer from the new measurement |
|---|---|
| Setup cost of the AES context             | **30.9 µs and 1.9 µJ** per call (not 30 µJ) |
| ASCON vs AES, setup every message | ASCON better **below ≈ 100 B (96 to 107 B)**, AES better above |
| AES with the setup done once | AES equal or better at **every** size |
| Cost per byte | ASCON 0.089 µJ/B, AES 0.062 µJ/B |
| At 1,600 B | AES uses **28% less** energy (104.7 vs 145.2 µJ) |
| Power while running | ASCON ≈ 75 mW, AES ≈ 68 mW (about 10% apart) |
| Time crossover | ≈ 175 B (not ≈ 1,250 B) |
| In a 60 s duty cycle | The choice changes total energy by **under 4%** |

Also checked on the original data (supervisor Comments 4 and 5):
- The original 347 B did **not** come from outlier trimming (345, 347, 347 B with none, k = 3, k = 1.5).
- The "execution time significant at only 21 sizes" came from testing **one direction only**. Two-sided, time differed at all 100 sizes, so the claim "power, not speed, drives the gap" is withdrawn.

## 3. How to answer "why should we trust this?"

Use these points in the dissertation (5.4) and in the viva.

1. **The signal is large and the noise is tiny.** Extra current under load was 12.8 to 16.7 mA. The idle level moved by 0.01 mA on average between the windows before and after.
2. **It repeats.** The spread of energy across replicates was 0.3%. A second run, with different sizes and more replicates, agreed with the first to within 0.5% where they overlapped, and the AES setup cost came out as 1.896 and 1.895 µJ.
3. **The numbers agree with each other.** Time and energy are straight lines in payload size (R² above 0.9999). The break-even worked out from the fitted lines (99 B) matches the one found directly (96 to 107 B). The old data failed this test (206 B against 347 B).
4. **Known problems were removed by design, not by clean-up.** The sensor's constant offset cancels because it is in both load and idle readings; the timed region holds only the cipher loop; the algorithms share one session in random order; no data points were deleted.
5. **Two independent measurement paths.** Time comes from the CPU timer, current from the sensor. Energy ordering follows the time ordering with a roughly constant power difference, so the paths do not contradict each other.
6. **The tests are reproducible.** All firmware, logs and scripts are in the repository and are listed in Appendix F.

## 4. Limits you must state (an examiner will ask)

- **One board, one sensor, no reference meter.** The *relative* comparison is safe (same sensor, same offset); the *absolute* µJ scale rests on the INA219.
- **Steady state, Wi-Fi off, one core.** It does not include the cost of the first run after waking from deep sleep. The old data hint that such a cost exists (about 370 µs extra for AES at 16 B, against 45 µs in the clean measurement). **This is a guess, not a result**, and is listed as future work.
- **Sleep, wake-up and transmit are not measured.** The 60 s sleep is modelled from a datasheet number.
- **We do not know which parts of GCM run in hardware.** Do not claim more than "the ESP32 AES peripheral is enabled in the build".
- **Encryption only**, 16-byte tag, no associated data.

## 5. Mapping to your supervisor's five comments

| # | Comment | Where and how it is handled |
|---|---|---|
| 1 | Flowchart symbols | Figure 1 redrawn in one ISO 5807 convention; typos fixed (`07_Figures_and_Appendices.md`) |
| 2 | 347 B vs 206 B | 4.5.2 and 5.2.5. With the validated data the two agree (99 vs 106 B). The old mismatch is explained as a symptom of the instrumentation problem |
| 3 | Intercept is not initialisation energy | 4.5.2, 5.2.2. Setup measured directly (1.9 µJ); intercept described as a "fitted fixed cost"; old 30.14 µJ claim withdrawn |
| 4 | Outlier trimming | 4.2.2 (no trimming in Campaign B), 4.7.3 and Table 14 (sensitivity: 345 / 347 / 347 B) |
| 5 | Separate t-tests, multiple comparisons | 3.7.2, 4.7.1, 4.7.3. Paired, two-sided, Holm-corrected; effect sizes and a bootstrap interval added; the one-tailed 21% result corrected |

## 6. Things I noticed that your supervisor may also raise

- The **wake timer**: the firmware in the repository says 1 s; git history shows earlier commits with 60 s and the 1 s value first appearing in the post-collection commit; and about 127,000 logged trials at 60 s each would take about 88 days, which does not fit the period between your first commit (21 Aug) and the analysis commit (17 Sep). The dissertation now says the 60 s is a *modelled* interval. See [CONFIRM 2].
- **160 MHz** (not 240), **ESP32** (not the C3 datasheet or block diagram), **INA219 upstream of the board regulator** (so the idle level includes board parts).
- **Memory method** described as MicroPython in Chapter 3 while the firmware is ESP-IDF C.
- The title says "in a Realistic IoT Duty Cycle". The encryption phase is measured and the rest modelled; consider adding "with a Modelled Sleep Phase" or stating the scope in the first paragraph of the abstract (done in the revised abstract).
