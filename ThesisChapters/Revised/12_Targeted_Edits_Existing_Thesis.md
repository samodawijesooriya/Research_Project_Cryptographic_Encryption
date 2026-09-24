# Targeted edits to the existing thesis (no full rewrite)

Approach: keep the thesis as it is, insert the new **Chapter 5 (Validation)** from `11_Validation_Chapter.md`, and patch only what must change. Chapter 4 stays as the record of Campaign A and is relabelled honestly; the Discussion and Conclusions get replacement text for the sections whose claims depended on the 347-byte result.

Each item below says *where*, *what to do* and gives the text to paste. Edits are ordered by their position in the document.

> The earlier files `03_Chapter3_revised.md`, `04_Chapter4_revised.md`, `05_Chapter5_revised.md` and `06_Chapter6_revised.md` were written as full rewrites for a structure without a separate validation chapter. **They are now reference only**; use this file and `11_Validation_Chapter.md` instead. `00_Abstract.md`, `01_Chapter1_edits.md` and `02_Chapter2_edits.md` remain valid.

---

## 0. Structure

1. Insert **Chapter 05: Validation of the Measurements and Reassessment of the Results** after Chapter 4.
2. Renumber: Discussion → **Chapter 06**, Conclusions and Future Work → **Chapter 07**, References stays last. (The current Contents lists "11. References"; call it "References".)
3. Update the Contents, List of Figures (add Figures 12 to 22), List of Tables (add Tables 9 to 20 and, in Chapter 3, none), List of Equations (add Equation 5 = the fixed plus variable cost relation, which is the current Equation 4 in the Discussion, and Equation 6 = sustained-load energy). If captions use Word's caption feature, the numbers update automatically; otherwise renumber the Discussion's "Table 8 – Resource cost before encryption" to follow the new tables (Table 21).
4. Cross-references to renumbered sections:

| In the text | Change to |
|---|---|
| "Chapter 5" (Discussion) | "Chapter 6" |
| "Chapter 6" (Conclusions) | "Chapter 7" |
| "5.2.x", "5.3", "5.4" (Discussion sections) | "6.2.x", "6.3", "6.4" |
| "6.x" (Conclusion sections) | "7.x" |
| "4.3.3" | "4.3.2" |
| "the 347-byte break-even (4.5.2)" | "the Campaign A break-even (4.5.2), reassessed in 5.5.2" |

---

## 1. Abstract (page iii)
Replace the whole abstract and keep the keywords line with `00_Abstract.md`. Its structure (two campaigns, setup cost, break-even ≈ 100 B, context reuse, 24% memory, < 4% of modelled cycle) matches the new chapter.

## 2. Chapter 1 (pages 1 to 5)
Apply `01_Chapter1_edits.md`, with these changes to fit the validation chapter:

- **1.9 Organization of Thesis** (rename "of the Dissertation"): after the Chapter 3 paragraph add
  > **Chapter 4: Data Analysis and Results** – Reports the per-trial benchmark (Campaign A): cleaning, time, power, energy, break-even, memory and statistical tests.
  >
  > **Chapter 5: Validation** – Audits the measurement method of Campaign A, reports a second, sustained-load campaign (Campaign B), and reassesses the Campaign A results, including the responses to the review comments.
  >
  > **Chapter 6: Discussion** – Interprets the corrected findings, compares them with the literature and states the limitations.
  >
  > **Chapter 7: Conclusions and Future Work** – Answers the research question, states the contribution and lists recommendations.
- **1.7 and 1.8**: use the text of `01_Chapter1_edits.md`.

## 3. Chapter 2
Apply `02_Chapter2_edits.md` (sensor timing paragraph in 2.4.2; ESP32 datasheet in 2.5.2; sentence in 2.3.3; sentence in 2.7; typo list).

## 4. Chapter 3: corrections only (no restructuring)

The measurement design of Campaign B is described in Chapter 5 (5.3). Chapter 3 needs the following corrections and pointers.

| Where | Edit |
|---|---|
| 3.1 | "positive paradigm" → "positivist paradigm"; "[Jin & Becker, 2022 facilitates" → "[Jin & Becker, 2022] facilitates"; "This thesis" → "This dissertation" |
| 3.2.3, Table 2 | Execution time: `micros()` → `esp_timer_get_time()`; memory: `ESP.getFreeHeap()` → `heap_caps_get_free_size()` and the stack high-water mark |
| 3.3.1 | Restore the symbols *i* and *j* lost in "Outer Loop ()" and "Inner Loop ()". Add at the end: *"This program is referred to as Campaign A. A second, sustained-load program (Campaign B) was developed to validate its energy measurements and is described in 5.3."* |
| Figure 1 | Redraw to ISO 5807 (`07_Figures_and_Appendices.md`, A.1) |
| 3.3.4 | Replace the second sentence of the first paragraph ("In accordance with Syahmi's methodology, the device enters a deep sleep mode for 60 seconds…") with the text below |
| 3.4.1 | Replace Figure 2 with the ESP32 block diagram; "240 MHz" → "up to 240 MHz (160 MHz was used in this study)"; remove "microsecond-level precision" (also in 3.4.3 and the paragraph after Figure 6); state that the INA219 is on the 5 V supply ahead of the board's regulator; use 4.72 V as the measured bus voltage; label or remove the 10 kΩ resistor |
| 3.4.2 | mbedTLS version: [VERIFY 3]; add "ESP-IDF v5.3.1, default optimisation level, CPU frequency 160 MHz, `CONFIG_MBEDTLS_HARDWARE_AES=y`" |
| 3.4.3 | "Fig 7" → "Figure 5"; "Fig.7" in 3.4.4 → "Figure 6" |
| 3.5.1 | `micros()` → `esp_timer_get_time()`; add "In Campaign A the timed region also contained instrumentation (5.2.2)" |
| 3.5.3 | Replace the last sentence ("By maintaining a regulated 5V supply…") with the text below |
| 3.5.4 | Replace with the text below |
| 3.7.2 | Replace "Hypothesis Testing" with the text below |
| 3.6 | "As specified in your experimental setup" → "In this study" |

**Text for 3.3.4 (replace the sentence):**
> The reporting interval modelled in this dissertation is 60 seconds. The sleep phase was not measured: its energy is added analytically (4.2.4 and 5.4.8). During collection of the Campaign A data the firmware used a shorter wake timer between trials so that about 127,000 trials could be collected **[CONFIRM 2: state the value your data used]**; the transmission step reported each trial to a Node-RED dashboard and its energy was not separated from that of the encryption.

**Text for 3.5.3 (last sentence):**
> The bus voltage measured on the 5 V rail was about 4.72 V. In Campaign A, power was estimated from two instantaneous readings around each cipher call; the limits of that method are examined in 5.2. In Campaign B, the extra power drawn by the cipher was measured as the difference between a sustained-load window and idle windows (5.3.2).

**Text for 3.5.4 (memory footprint):**
> Memory footprint was measured in Campaign A. Heap use was taken from `heap_caps_get_free_size()` before and after the cipher call, and peak heap use from the change in `heap_caps_get_minimum_free_size()`. Stack use was taken from `uxTaskGetStackHighWaterMark()` in a dedicated task created for each cipher call, so that stack use by other work does not contaminate the reading. The footprint is the sum of peak heap and stack use, averaged over the hundreds of sweeps collected. The technique follows the idea of before-and-after memory snapshots used by Pipiras (2024), implemented in ESP-IDF and not in MicroPython. It measures run-time memory only, not code size in flash.

**Text for 3.7.2 (hypothesis testing):**
> Hypothesis testing: per-size differences between the ciphers were tested with two-sided t-tests (Welch's test for the independent Campaign A samples; a paired test on per-replicate differences for Campaign B), because the direction of the difference reverses across the break-even. Because one test is run for each payload size, the p-values were adjusted for the family of tests with the Holm procedure (family-wise α = 0.01), and effect sizes are reported next to significance. The break-even is the interpolated sign change of the mean difference, with a bootstrap 95% interval. An earlier analysis of Campaign A used one-tailed uncorrected tests; it is re-examined in 5.5.6.

## 5. Chapter 4: relabel, correct, and point to Chapter 5

| Where | Edit |
|---|---|
| Chapter title or 4.1 | Add as the second paragraph of 4.1 the text below |
| 4.1, last paragraph | Delete the sentence "…so that any difference reported between the two algorithms in this chapter could be attributed to the algorithms themselves…" and replace with: "Both datasets were processed through the same pipeline; the limits of the resulting measurements are assessed in Chapter 5." |
| 4.2.1 | **Delete the repeated paragraphs** (the two copies of "This process identified 699 candidate iterations…" and the fragment "Thisstudy extended that design…"); keep only the last version. Fix "praising" → "parsing" |
| 4.2.3 | Replace the last sentence ("No single payload size lost a share…") with: "Trimming was tested for its effect on the conclusions (5.5.5): the break-even was 345.0, 347.4 and 346.8 bytes without trimming, with k = 3 and with k = 1.5." Fix "51,00" → "51,000" |
| 4.2.4 | Replace "ESP32-C3 Series Datasheet … 5 µA" with "the ESP32 datasheet deep-sleep figure **[VERIFY 1]**", and add: "Two cases (5 µA and 10 µA) are reported in 5.4.8." |
| 4.3.1 | "ASCON-128-GCM required 1,740.8 µs" → "AES-128-GCM required 1,740.8 µs"; "ASCON-128's mean execution time has risen to 3,266.5 µs – marginally lower than ASCON-128's at this payload size" → "ASCON-128's mean execution time had risen to 3,266.5 µs, marginally higher than AES-128-GCM's 3,167.6 µs"; "85% confidence interval" → "95%"; rename the quantity "trial latency" |
| 4.3.2 | Add at the end: "These times include instrumentation (5.5.1); their increments per byte were confirmed in Campaign B (1.180 and 0.897 µs/B)." |
| 4.4 | Add a final paragraph: "The power figures of this section are not used for conclusions: comparison with Campaign B (Table 17) showed that they were 20 to 25 mW at small payload sizes against 64 to 75 mW measured with the sustained-load method, and that they contained steps that do not exist in the validated data (5.5.1)." |
| 4.5.1 | Add a final paragraph: "The per-byte energies and the sleep-inclusive figures of this section are superseded by the validated values in 5.4.5 and 5.4.8. The sleep term (990 µJ) is a modelled constant and identical for both ciphers." |
| 4.5.2 | Add: "This 347-byte figure was reassessed in 5.5.2: it coincides with a step in the measured AES power between 336 and 352 bytes and was not confirmed by the sustained-load measurement." |
| Table 5 | ASCON at 336 B: **0.017 → 0.107** |
| 4.6 (memory) | Keep unchanged. Add: "This measurement does not depend on the timing and power method examined in Chapter 5." Replace the reference "(2.3.1)" with "(2.3.3)" or remove it |
| 4.7.1 | Keep the text, add at the start: "The tests of this section were one-tailed and uncorrected. They are re-run two-sided and with Holm correction in 5.5.6 (Table 19), which replaces Table 7." Delete the last two sentences (the interpretation "driven by differences in power consumption rather than … raw execution speed") |
| Table 7 | Replace with Table 19 (or add "superseded by Table 19") |
| 4.7.2 | Replace with the text below |
| 4.8 | Replace the second paragraph with the text below |

**Text for 4.1 (new second paragraph):**
> The measurements reported in this chapter were made with the per-trial benchmark described in 3.3.1, referred to as Campaign A. After review, its measurement method was audited and a second, sustained-load campaign (Campaign B) was carried out; both are reported in Chapter 5. The time increments and the memory footprint of this chapter were confirmed. The power, energy, break-even and significance results were changed, and Chapter 5 states which findings stand, which are replaced and why (Table 20).

**Text for 4.7.2 (replace):**
> The linear regression of per-operation energy against payload size produced intercepts of 15.03 µJ for ASCON-128 and 30.14 µJ for AES-128-GCM (Table 4). An intercept is the value of the fitted line at a hypothetical zero-byte payload. It includes every fixed cost that does not depend on payload size, and with R² of 0.91 and 0.43 it is imprecise. It was therefore not taken as evidence of the AES hardware initialisation cost. That cost was measured directly in Campaign B (1.90 µJ; 5.4.3), and the intercept is called a *fitted fixed cost* (5.5.4).

**Text for 4.8 (replace the second paragraph):**
> The significance tests of 4.7.1 were one-tailed and uncorrected and have been re-run two-sided with correction for multiple comparisons (5.5.6). The interpretation given in an earlier version of this section, that the efficiency gap was driven primarily by power draw rather than speed, is withdrawn. Chapter 5 audits the measurement method used for these results, reports a validation measurement, and states which findings are retained, changed or withdrawn.

## 6. Chapter 6 (Discussion; currently Chapter 5)

Section by section. Replace the listed text; keep everything else.

| Section | Action |
|---|---|
| 6.1 Introduction | Replace with the text below |
| 6.2.1 Why a break-even point exists at all | Replace the two paragraphs and Table 8 as below |
| 6.2.2 (first, "Objective 2…") | Replace with the text below |
| 6.2.2 (second, "Why the algorithm choice matters less…") | **Delete** (its content is in the new 6.2.2) and renumber 6.2.3 to 6.2.3 |
| 6.2.3 "An unexpected result…" | Replace with the text below (new title) |
| new 6.2.4 | Add "Why the first analysis gave 347 bytes" (text below) |
| 6.3 Comparison with existing literature | Replace paragraph 3 ("The 347 bytes break-even point…") and the two-respects paragraph as below |
| 6.4 Limitations | Keep, add the items below, and change "None of them are expected to change the direction of the break-even result" to "The direction of the corrected break-even result is unaffected by them" |
| "5.6 Summary of Chapter 5" | Renumber to 6.5 and replace |

**6.1 Introduction (replace):**
> This study asked whether software-based ASCON-128 or hardware-accelerated AES-128-GCM is the more energy-efficient choice for a battery-powered IoT node on the ESP32, and under what conditions (1.7). The answer, after validation (Chapter 5), is conditional on two things: the payload size, and whether the AES-128-GCM context is set up on every message. When it is, as on a node that loses RAM in deep sleep and sends one message per wake, ASCON-128 used less energy below about 100 bytes and AES-128-GCM above it. When the context is kept, AES-128-GCM was at least as efficient at every tested size. This replaces the break-even of 347 bytes reported in Chapter 4. This chapter interprets the corrected result (6.2), explains why the first analysis differed (6.2.4), compares the result with the literature (6.3) and states the limitations (6.4).

**6.2.1 (replace):**
> The break-even exists because the two ciphers pay for their work in different proportions. Writing energy per byte as (fixed cost ÷ payload size) + variable cost per byte (Equation 5), the fixed term shrinks as the payload grows: small payloads are decided by the fixed cost and large payloads by the variable cost. Campaign B gave fixed costs (fitted intercepts) of 2.91 µJ for ASCON-128 and 5.57 µJ for AES-128-GCM with setup on each call, and variable costs of 0.0889 and 0.0619 µJ per byte (Table 13). Because each wins on a different term, a payload size exists at which they are equal; solving the lines gives 99 bytes, and the directly measured crossing was 106 bytes (95% interval 96 to 107 bytes), in agreement.
>
> The slopes have a plausible cause: ASCON-128 executes its permutation on the CPU, which stays busy longer (1.18 µs per byte against 0.90 for AES-128-GCM), whereas the AES block operation is performed by the AES peripheral. Which parts of GCM run in the peripheral and which on the CPU was not examined, so the AES slope is the measured cost of the complete library call.
>
> The directly measured setup step (context initialisation and key load, no encryption) cost 30.9 µs and 1.90 µJ. This is the measured initialisation cost of the AES-GCM context. It replaces the figure of 30.14 µJ of the earlier draft, which was extrapolated from a poor regression (5.5.4). The difference between the AES_COLD and AES_WARM intercepts (2.82 µJ) is larger than the setup step, and the remainder was not isolated. The fitted fixed cost of ASCON-128 is the intercept of a fit, not a separately measured step.
>
> Setting the context up on each message corresponds to a node that loses RAM in deep sleep and rebuilds its security state on every wake [Gerndt et al., 2025]; keeping it corresponds to a node that sends several messages per wake or stores the key schedule in RTC memory. The choice moves the break-even from about 100 bytes to no break-even, and is the practical form of the result.

*Replace Table 8 ("Resource cost before encryption") with these rows, and renumber:*

| Item | Content |
|---|---|
| AES-128-GCM fixed cost | Preparing the context: initialisation and loading of the key. **Measured: 30.9 µs, 1.90 µJ per call.** |
| AES-128-GCM per-byte cost | Block processing by the AES peripheral and the surrounding library calls. **Measured: 0.897 µs and 0.062 µJ per byte.** |
| ASCON-128 fixed cost | Initial permutation over key and nonce on the CPU. **Fitted intercept: 2.9 µJ** (not separately isolated). |
| ASCON-128 per-byte cost | Permutation rounds on the CPU. **Measured: 1.180 µs and 0.089 µJ per byte.** |

Delete the sentences "GSM also needed to authenticate the ciphertext, then separately compute the GHASH subkey by encrypting an all-zero block and load that into engine as well. Regardless of the payload size, this fixed cost rather than a per-byte one."

**6.2.2 Objective 2 (replace):**
> Objective 2 asked for the energy cost per byte across the duty cycle. Only the encryption phase was measured; the sleep phase was modelled as 3.3 V × I_sleep × 60 s (990 µJ for 5 µA, 1,980 µJ for 10 µA **[VERIFY 1]**), and wake-up and transmission were not measured. With this model, encryption was 0.4% of the cycle at 16 bytes and 13% at 1,600 bytes (ASCON-128, 5 µA case), and the choice of cipher changed total cycle energy by between 0.1% and 3.6% (Table 15). At small payloads the sleep term dominates both ciphers almost equally, so the choice matters little to total energy. It matters most for nodes that wake often, send large batches, or run close to their energy budget. Wi-Fi association and transmission, which were not measured, would enlarge the non-cipher part of the cycle further. The break-even is therefore a design rule for the active phase and not a large lever on battery life at low reporting rates.

**6.2.3 Power and time (replace the whole section, new title "Power versus time"):**
> The earlier draft concluded that the energy difference was driven primarily by power rather than speed, because execution time differed significantly at only 21 of 100 sizes. That conclusion is withdrawn. The tests were one-tailed with the hypothesis "ASCON slower than AES", which holds only above the time crossover near 1,250 bytes, about 21 of the 100 sizes; two-sided, execution time differed at every size (5.5.6). In Campaign B, time dominates: ASCON-128 drew about 10% more extra power than AES-128-GCM (75.3 versus 67.8 mW), and at 1,600 bytes took 26% more time (1,927 versus 1,524 µs), which together give the 28% energy difference. At small payloads, AES-128-GCM with per-message setup is slower (102.8 versus 57.9 µs at 16 bytes), which is why ASCON-128 wins there. On this platform, energy differences between the ciphers are mostly differences in how long the CPU is busy.

**6.2.4 Why the first analysis gave 347 bytes (new):**
> The Campaign A break-even of 347 bytes was reproducible (345.0, 347.4 and 346.8 bytes without trimming and with two trimming factors) but was not confirmed by Campaign B. The comparison of 5.5 explains why: the measured AES power fell by 10.1 mW between 336 and 352 bytes while AES time rose smoothly, and the break-even lies exactly on that step; the power figures were 20 to 25 mW where 64 to 75 mW was measured; the timed region contained about 1.3 to 1.6 ms of instrumentation against a call of 58 to 103 µs at 16 bytes; and the ciphers were collected in separate sessions. The disagreement between the regression (206 bytes) and the measured (347 bytes) break-even was a symptom of the same problem: a straight line fitted to data with steps. A further difference of about 325 µs between the two ciphers' time offsets in Campaign A is much larger than any difference in Campaign B; since each Campaign A trial ran after a fresh boot, a plausible contributor is a first-execution effect. This was not tested and is proposed in 7.5.

**6.3 (replace the paragraph starting "The 347 bytes break-even point…"):**
> The break-even measured in this study fills that gap: both groups of findings are correct within the scope of what they measured. ASCON-128 is the more efficient choice at small payloads when the AES context must be prepared per message, which is compatible with the lightweight-cryptography claim for short messages, and hardware-assisted AES-128-GCM is more efficient at larger payloads and, if its setup is amortised, at nearly all sizes, which is compatible with the accelerator studies. Software AES was not measured here, so the figures of those studies (for example the 74% latency reduction of ASCON over software AES) cannot be confirmed or refuted; only the qualitative relation is addressed.

*And in the paragraph "Beyond this finding…": replace "R² = 0.9999997, 4.3.3" with "R² > 0.9999, 5.4.2"; replace "the per-byte energy analysis across 100 payload sizes in 4.5 answers both gaps directly" with "the per-byte energy analysis in Chapter 5 addresses both gaps".*

**6.4 Limitations (add these items; keep the existing ones):**
> - The sleep phase was modelled, and wake-up and transmission were not measured; the term "duty cycle" refers to a modelled cycle whose encryption phase is measured. The wake timer used while collecting Campaign A was shorter than 60 s **[CONFIRM 2]**.
> - The validation measured steady-state cost with Wi-Fi off on one core; it does not capture first-execution effects after a boot, which may add a fixed cost (6.2.4).
> - All measurements used one board and one INA219 without an independent reference instrument. The relative comparison between the ciphers does not depend on the absolute calibration, but the absolute energy scale does.
> - The extra power is measured above the idle level of a development board (about 35 to 37 mA), which includes board components.
> - Only encryption with a 16-byte tag and no associated data was measured.
> - Which parts of GCM run in hardware was not established.

Also fix the limitation about the INA219: "This affects confidence in the very smallest measured values, but the differences that drove the break-even result were well above this floor" → "In Campaign B the averaged mode was used and the differences of interest (several µJ; 10% in power) were well above the resolution of the sensor."

**6.5 Summary (replace):**
> The validated results show a payload-size break-even of about 100 bytes for AES-128-GCM with per-message setup, and none if the context is reused. The mechanism is a lower fixed cost but a higher per-byte cost for ASCON-128. The AES setup cost was measured directly (30.9 µs, 1.90 µJ). The claim that power drives the difference is withdrawn. The 347-byte result of Campaign A is reproducible under trimming but is attributed to a step in the measured power, and was not confirmed. Against a modelled 60-second sleep interval, the cipher choice changed total energy by under 4%. The limitations of 6.4 bound these conclusions, and Chapter 7 states what should be done next.

## 7. Chapter 7 (Conclusions; currently Chapter 6)

**7.2 (replace the three bullets):**
> - **Objective 1: energy per operation and per byte, and the initialisation cost of AES-128-GCM.** Met. Energy per operation and per byte were measured for both ciphers (5.4.5), and the initialisation step of the AES-GCM context was isolated: 30.9 µs and 1.90 µJ per call (5.4.3). *Qualification:* the fixed cost of ASCON-128 is a fitted intercept, not a separately measured step.
> - **Objective 2: energy per byte across the duty cycle.** Met, with a qualification. The active phase was measured and the sleep phase modelled (60 s, datasheet current). Encryption was 0.4% to 13% of the modelled cycle, and the cipher choice changed total energy by under 4% (5.4.8). Transmission and wake-up were not measured, so the study does not establish the energy of a fully measured duty cycle.
> - **Objective 3: conditions favouring ASCON-128, including the break-even.** Met. With AES-128-GCM setting up its context on every message the break-even was about 100 bytes (95% interval 96 to 107 bytes); with the context reused AES-128-GCM was at least as efficient at every size (5.4.6 and 5.4.7).

**7.3 (replace):**
> Neither algorithm was unconditionally more energy-efficient on the ESP32; the deciding factors were payload size and how the AES context is managed. AES-128-GCM has a small per-message cost of preparing its context (30.9 µs, 1.90 µJ) and a lower cost per additional byte (0.062 versus 0.089 µJ) than software ASCON-128. For a node that rebuilds the AES context on every message, software ASCON-128 was more energy-efficient below about 100 bytes and hardware-assisted AES-128-GCM above it, and at 1,600 bytes AES-128-GCM used 28% less energy per call. For a node that reuses the context, AES-128-GCM was more efficient at every size from 64 bytes and equal within measurement error at 16 bytes. AES-128-GCM used about 24% more run-time memory. Against a modelled 60-second sleep interval the difference in total energy per cycle was under 4%, so the choice matters most for nodes that send frequently or in large batches.

**7.4 (replace):**
> Prior literature had compared ASCON with software AES, and hardware-accelerated AES with software AES, but not ASCON with hardware-assisted AES-128-GCM directly (2.7). This dissertation provides that comparison on one platform, and adds four things: a break-even of about 100 bytes together with the finding that it disappears when the AES context is reused; a direct measurement of the AES-GCM setup cost on the ESP32 (1.90 µJ); a documented comparison showing that a per-trial method with two sensor readings around a millisecond-scale call can give a reproducible but unsupported result, with a sustained-load method that resolves it; and a new comparison of run-time memory (AES-128-GCM about 24% larger).

**7.5 (keep the five bullets; replace the second and third, and add):**
> - **Empirically measure the sleep, wake-up and transmission phases** with the INA219 (or a sensor with a suitable range) instead of a datasheet model, including the transmission of the tag and nonce overhead.
> - **Test other sleep intervals and messages per wake** to check the practical-significance result of 5.4.8 directly.
> - **Cold-start measurement:** time the first cipher call after a wake from deep sleep for both ciphers, to test whether first-execution effects add a fixed cost (5.5.1).
> - **Software AES on the same board**, to place the two groups of literature on one scale.
> - **Which parts of GCM run in hardware** in mbedTLS on the ESP32.

**7.6 (replace):**
> This dissertation compared software ASCON-128 with hardware-assisted AES-128-GCM on the ESP32 in a modelled IoT duty cycle. An early per-trial measurement gave a break-even of 347 bytes; a validation with a sustained-load method showed that the early method could not resolve the energy of the operation, and the conclusions were rebuilt on the second measurement. ASCON-128 is more energy-efficient for messages below roughly 100 bytes when the AES context is set up per message, and AES-128-GCM is at least as efficient otherwise, with a small effect on total energy at long sleep intervals. The result is offered as an evidence-based design rule for the active phase of energy-constrained IoT nodes, together with a documented method for measuring it.

## 8. Appendices to add
See `07_Figures_and_Appendices.md` (section C). The minimum set: Appendix A (firmware and build configuration), Appendix B (Campaign B protocol and per-size tables), Appendix C (Campaign A processing, sensitivity and the old time and energy plots labelled "trial latency including instrumentation"), Appendix D (statistical methods), Appendix E (hardware and INA219 settings), Appendix F (reproducibility).

## 9. Do these last
1. Insert the figures listed in `07_Figures_and_Appendices.md` (A.4) and add `fig_campaignA_vs_B` as Figure 20 in 5.5.1.
2. Confirm [VERIFY 1], [CONFIRM 2] and [VERIFY 3] (`09_Open_Items.md`) and replace the markers.
3. Redraw Figure 1 and replace Figure 2.
4. Update the Contents, List of Figures, List of Tables and List of Equations.
5. Search the whole document for "347", "30.14", "15.03", "power rather than", "240", "C3", "thesis" and "5.2.1" and check each hit against the new text.