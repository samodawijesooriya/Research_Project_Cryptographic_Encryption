# Final Dissertation Presentation — Slide Content (extended)

Source: *Final Thesis V05* (chapters in this folder: `03`, `04`, `11` validation, `05` discussion, `06` conclusions) + the earlier *Research 3 Chapter Presentation* (22 slides).

How to use each slide:
- **On screen**: the only text on the slide. Tables marked "on screen" are meant to be shown; keep everything else short.
- **Visual**: the image that carries the slide. Files in `figures/` are ready to use; "Thesis Fig N" means take a screenshot from the V05 PDF.
- **Say**: what you say out loud. It covers what the slide shows and why it matters.

The story has three acts, and the panel will want all three:
1. **What I did first**: Campaign A, how the data was collected and what it said.
2. **How I checked it**: the audit, the validation experiment (Campaign B) and the side-by-side comparison.
3. **What I can now conclude**: the validated results, and how each conclusion follows from the evidence.

---

## Time plan

| Part | Slides | Full version | 25-min version |
|---|---|---|---|
| 1. Recap (problem, question, test bed) | 1–8 | 4 min | 3 min |
| 2. Campaign A: data collection and first results | 9–17 | 6 min | 4 min |
| 3. Validation: audit, Campaign B, A vs B | 18–35 | 12 min | 8 min |
| 4. Validated results | 36–43 | 6 min | 5 min |
| 5. From evidence to conclusions | 44–52 | 6 min | 5 min |
| **Total** | 52 + Q&A | **~34 min** | **~25 min** |

For the 25-minute version, move every slide marked **[optional]** to the backup section. The story still holds without them.

---

## Fix these before reusing old slides

The old deck has details that the final thesis corrected. If you copy old slides, change these:

| Old slide | Old text | Correct it to |
|---|---|---|
| 15 (Test-bed) | "up to 240 MHz" | Firmware ran at **160 MHz** (thesis Table 9, item 7) |
| 11 (Metrics) | `micros()`, `ESP.getFreeHeap()` | ESP-IDF: `esp_timer_get_time()`, `heap_caps_get_free_size()`, `uxTaskGetStackHighWaterMark()` |
| 17 (Formulas) | "gc.collect() → snapshot" | Remove. That is MicroPython. Use the heap_caps before/after method |
| 19 (Statistics) | t-tests (one-tailed implied) | **Two-sided** tests with **Holm correction**, plus a **bootstrap 95% interval** for the break-even |
| 20 (Expected outcomes) | "expected" | Replace with the actual results (slides 36–43 below) |
| 12–14 (Design) | One campaign | Call it **Campaign A** and add Campaign B (slides 24–29 below) |

## Do not say these until they are confirmed

Two items in `09_Open_Items.md` are still open. The slides below are worded to avoid them. Keep it that way unless you resolve them first.

- **Sleep current (VERIFY 1).** Always say "5 or 10 µA, modelled from the datasheet". Never quote one sleep figure as measured.
- **Wake timer during collection (CONFIRM 2).** Say "a short wake timer between trials". Do not say "60-second sleep between every trial". 60 s is the **modelled** interval only.

---

# PART 1 — Recap (Chapters 1–3, compressed)

### Slide 1 — Title
**On screen:**
An Energy-Centric Comparative Evaluation of Software-Based vs. Hardware-Accelerated Cryptography on ESP32 in a Realistic IoT Duty Cycle
Samoda Wijesooriya · Supervisor: Dr. Keerthi Wijayasiriwardhane
Final Dissertation Presentation · 2026

**Visual:** Keep the old title design.

---

### Slide 2 — The Journey
**On screen:**
Problem → Method → **Campaign A** → **Validation (Campaign B)** → Final Answer

**Visual:** A horizontal arrow with 5 stops. Make "Validation" a different colour. Reuse this arrow as a small progress bar at the top of later slides.

**Say:** "Last time I presented the plan. Today I'll show three things: the first data collection and what it said, how I tested whether that result could be trusted, and the conclusions I could draw after that. The validation step changed the final answer, so it takes up the middle of this talk."

---

### Slide 3 — The Problem
**On screen:**
Battery-powered IoT devices
Encryption is a must
But encryption costs energy

**Visual:** An ESP32 or sensor node icon, a battery icon, and a padlock.

**Say:** "IoT nodes run on batteries for months or years. They must encrypt data, but every encryption uses battery. So the question is which encryption uses the least energy."

---

### Slide 4 — Two Contenders
**On screen:**
**AES-128-GCM**: hardware AES engine, the classic standard
**ASCON-128**: software on the CPU, NIST lightweight standard (2023)

**Visual:** Split screen. Left: chip with a highlighted "AES engine" block (Thesis Fig 2, ESP32 block diagram). Right: CPU icon with "ASCON".

**Say:** "The ESP32 has a built-in hardware AES engine. ASCON is newer and designed to be light, but on the ESP32 it has to run in software. Hardware should be faster and ASCON should be lighter. Which one really uses less energy?"

---

### Slide 5 — Research Question and Objectives
**On screen:**
*Hardware AES or software ASCON: which uses less energy per byte in a real IoT duty cycle?*
① Energy per operation and per byte + AES setup cost
② Share of encryption in the duty cycle
③ Conditions favouring ASCON, including the break-even payload size

**Visual:** Three numbered icons (lightning bolt, cycle arrow, crossing lines). Reuse these icons on slide 45.

**Say:** "Three objectives: measure the energy, see how much it matters in a full cycle, and find the payload size where the winner changes. At the end I'll come back to each one and show the evidence behind it."

---

### Slide 6 — The Gap
**On screen:**
Nobody compared **software ASCON** vs **hardware AES** on the **same chip**

**Visual:** Reuse old slide 8 (the gap table with Covered / Partial / Not covered). Highlight the "This study" row.

**Say:** "Some studies say ASCON is better and others say hardware AES is better. But each of them compared against *software* AES. Nobody put these two against each other on the same board. That is the gap."

---

### Slide 7 — The IoT Duty Cycle
**On screen:**
Sleep → Wake → Sense → **Encrypt** → Transmit → Sleep
60 s reporting interval (modelled)

**Visual:** Circular diagram with "Encrypt" highlighted.

**Say:** "Real devices don't encrypt non-stop. They sleep, wake up, encrypt one message, send it and sleep again. I measured the encryption step and placed it in a 60-second cycle. The sleep part is modelled from the datasheet, and I'll be clear about that when we reach the results."

---

### Slide 8 — Test Bed
**On screen:**
ESP32-WROOM-32E, **160 MHz**, ESP-IDF v5.3.1
INA219 current sensor in the 5 V line (0.1 Ω shunt)
mbedTLS with hardware AES enabled
Soldered board, not a breadboard

**Visual:** Test bed photo (Thesis Fig 6) + schematic (Thesis Fig 5) side by side.

**Say:** "The INA219 sits between the power supply and the ESP32 board, so every milliamp the board uses passes through it. AES uses the chip's hardware engine through mbedTLS, and ASCON is the reference C code running on the CPU. Both ran on the same board, with the same key, the same payloads and the same build settings."

---

# PART 2 — Campaign A: data collection and first results (Chapter 4)

### Slide 9 — Campaign A: The Design
**On screen:**
Based on Jin & Becker (2022)
Outer loop: **500 repetitions**
Inner loop: **100 payload sizes**, 16 × j bytes (16 → 1,600 B)
One trial per boot, one algorithm per session

**Visual:** Nested-loop diagram: a big loop "repeat 500×" containing a small loop "size = 16, 32 … 1,600".

**Say:** "My first experiment, which I now call Campaign A, followed the benchmarking structure of Jin and Becker. For every repetition I stepped through 100 payload sizes, from 16 to 1,600 bytes in steps of 16. Each size was one trial, and I collected ASCON and AES in separate sessions."

---

### Slide 10 — One Trial, Step by Step
**On screen:**
Boot → Wi-Fi + MQTT connect
→ Generate nonce + payload
→ `start_monitor()`: heap snapshot + INA219 reading
→ Encrypt in a dedicated FreeRTOS task
→ `stop_monitor()`: INA219 reading + heap + stack watermark
→ Publish JSON over MQTT → deep sleep

**Visual:** Main algorithm flowchart (Thesis Fig 1), redrawn as a vertical flow. Highlight the two INA219 readings in orange (they come back on slide 21).

**Say:** "This is what one trial did. The board woke up, connected, created a fresh nonce and payload, took a memory snapshot and one current reading, then ran the encryption in its own task so I could measure its stack. After that it took a second reading, sent the results as JSON over MQTT and went back to sleep. Remember the two orange readings, because they turn out to be the weak point."

---

### Slide 11 — What Each Record Contained
**On screen:**

| Field | Tool |
|---|---|
| Time | `esp_timer_get_time()` (1 µs) |
| Current and power, before and after | INA219, 12-bit, 532 µs per conversion |
| Heap (peak) | `heap_caps_get_minimum_free_size()` |
| Stack | `uxTaskGetStackHighWaterMark()` |

Power = after − before · Energy = power × time

**Visual:** A sample JSON record (one line, from the raw log) next to the table.

**Say:** "Each trial produced one record with time, two current and power readings, and memory counters. Power was the difference between the after and before readings, and energy was that power multiplied by the time. The records went to a Node-RED dashboard and were saved to a log file."

---

### Slide 12 — From Raw Logs to Clean Data
**On screen:**

| | ASCON-128 | AES-128-GCM |
|---|---|---|
| Raw records | 65,506 | 61,715 |
| Malformed | 0 | 0 |
| Candidate sweeps | 699 | 646 |
| **Complete sweeps** | **561** | **510** |
| Rows kept | 56,100 | 51,000 |
| After IQR trim (k = 1.5) | 45,745 | 42,870 |

**Visual:** A funnel graphic next to the table: 127,221 raw → 107,100 complete → 88,615 trimmed.

**Say:** "In total I logged 127,221 records. Device resets left some sweeps unfinished, so I split the log wherever the payload size dropped back to 16 bytes, and kept only the sweeps that contained all 100 sizes exactly once. That left 561 complete sweeps for ASCON and 510 for AES, with the same number of samples at every size. Then I trimmed outliers per payload size."

---

### Slide 13 — Calibration and Cleaning  **[optional]**
**On screen:**
**21%** of ASCON current readings were **negative** (AES: 0.2%)
Read as a sensor zero offset → correction **+5.70 mA**, applied to both
Bus voltage: **4.674 V** (measured, not nominal 5 V)
Outliers: IQR rule, k = 1.5, per size, on time and power

**Visual:** `figures/fig_campaignA_offset_histogram.png` (raw readings on top, corrected below). Generated by `scripts/07_plot_offset_histogram.py` from the complete sweeps.

**Say:** "Current can't be negative, yet 21% of the ASCON readings were, clustered around minus 5.7 milliamps. In the AES session it was only 0.2%. I treated this as a zero offset in the sensor, estimated it as 5.70 mA from the ASCON data, and added it to every reading in both datasets. The negative cluster moves to zero, and the rest of the distribution shifts slightly. Keep this correction in mind: it was a patch applied after the fact, and in the validation experiment I designed the need for it away completely."

---

### Slide 14 — First Results: Time
**On screen:**
Time grows **linearly** with size (slopes 1.197 and 0.901 µs/B)
16 B: ASCON **1.37 ms**, AES **1.74 ms**
1,600 B: ASCON **3.27 ms**, AES **3.17 ms**
Time crossover ≈ **1,250 B**

**Visual:** Thesis Fig 7 (execution time scaling).

**Say:** "Time grew in a straight line with payload size for both ciphers. ASCON added about 1.2 microseconds per byte and AES about 0.9. At the time, it looked as if AES was slower for small messages and only overtook ASCON around 1,250 bytes. Note the scale here: over a millisecond even for 16 bytes. That number will matter later."

---

### Slide 15 — First Results: Power and Energy
**On screen:**
Extra power: **20–52 mW**, jumps with size
Regression: AES fixed cost **30.14 µJ**, ASCON **15.03 µJ**
Per-byte slope: AES **0.034**, ASCON **0.107 µJ/B**
Fit quality: R² = **0.43** (AES), **0.91** (ASCON)

**Visual:** Thesis Fig 8/9 (Campaign A energy per byte).

**Say:** "Fitting a line to energy gave AES a fixed cost of about 30 microjoules, which I interpreted as the energy of starting the hardware engine, twice ASCON's. AES was much cheaper per byte. The fits were weak, though. An R² of 0.43 means the line explains less than half of the AES data. At the time I blamed noise."

---

### Slide 16 — First Results: Memory
**On screen:**
ASCON-128: **2,773 B** · AES-128-GCM: **3,441 B**
AES uses **+668 B (24%)** more RAM
Constant across all payload sizes

**Visual:** Thesis Fig 11 (memory bar chart).

**Say:** "AES used about 24% more run-time memory, and the difference was the same at every payload size. That points to fixed-size structures in the AES library, such as the key schedule and the authentication tables. This result doesn't depend on the timing or the current sensor, so it still stands after validation."

---

### Slide 17 — What Campaign A Concluded
**On screen:**
Break-even ≈ **347 B** (ASCON below, AES above)
AES "hardware initialisation" ≈ **30 µJ**
"Energy gap driven by **power**, not speed"
Significant at 21 (time), 78 (power), 72 (energy) of 100 sizes

**Visual:** Thesis Fig 9 with the 347 B crossing circled. Stamp "FIRST DRAFT" in the corner.

**Say:** "These were the conclusions of my first draft. The break-even was 347 bytes. AES seemed to pay 30 microjoules to start its engine. Time was significantly different at only 21 sizes, so I concluded that the energy gap came from power, not speed. It looked like a complete answer. The next part shows why I couldn't keep it."

---

# PART 3 — Validation (Chapter 5): the key part

### Slide 18 — What Triggered the Validation
**On screen:**
Five review questions:
1. Flowchart symbols inconsistent
2. Regression says **206 B**, data says **347 B**. Why?
3. Is the 30 µJ intercept really "initialisation"?
4. Did outlier removal create the result?
5. 300 one-tailed tests with no correction?

**Visual:** Five numbered cards. Grey out Q1 (a drawing fix) and highlight Q2 and Q3.

**Say:** "The review of Chapter 4 raised five questions. The first was a drawing fix. Questions 2 and 3 could not be answered from the analysis alone. To explain why two methods on the same data gave 206 and 347 bytes, I had to go back and check how the firmware actually measured time and power."

---

### Slide 19 — Red Flags in the Data
**On screen:**
Two methods, same data: **206 B vs 347 B**
Power jumps in **steps** between neighbouring sizes
R² = 0.43 for a supposedly linear process
Over 1 ms for 16 bytes of encryption

**Visual:** Crop of the stepped Campaign A power curve from `figures/fig_campaignA_vs_B.png`, with the steps circled.

**Say:** "Four things didn't fit together. A straight-line fit and the raw data gave different break-evens. Power jumped suddenly between neighbouring sizes, which a cipher has no reason to do. Encryption is a fixed sequence of operations, so its energy should be almost perfectly linear, yet the fit was poor. And over a millisecond to encrypt 16 bytes is slow for a 160 MHz chip."

---

### Slide 20 — The Validation Process
**On screen:**
① **Audit** the Campaign A firmware line by line
② **Design** a new measurement that avoids each problem (Campaign B)
③ **Run** it: Run 1 (coarse) → Run 2 (fine sweep)
④ **Check** Campaign B can be trusted
⑤ **Compare** A and B at shared sizes
⑥ **Reassess** every Chapter 4 finding: stands, changed or withdrawn

**Visual:** A six-step horizontal flow. Use it as a mini-map at the top of slides 21–35.

**Say:** "This is how I validated the results, in six steps. First I audited the code. Then I built a second experiment that removes each problem I found. I ran it twice, checked that it was reliable, compared it with Campaign A size by size, and finally went through every earlier finding and labelled it as standing, changed or withdrawn."

---

### Slide 21 — Audit ①: The Sensor Was Too Slow
**On screen:**
One INA219 conversion: **532 µs**
Encryption at 16 B: **58–103 µs**
Two readings ≠ current *during* the call

**Visual:** `figures/fig_sensor_timing_scale.png`

**Say:** "This is the root cause. One INA219 conversion takes 532 microseconds, and the sensor register holds whatever conversion finished last. A small encryption takes only 60 to 100 microseconds. So my before and after readings didn't bracket the encryption in any defined way. It's like photographing a hummingbird with a slow shutter: you get a blur, not the bird."

---

### Slide 22 — Audit ②: What the Timer Really Measured
**On screen:**
Inside the timed region:
heap counters + 2 sensor reads (**~398 µs**) + task creation + semaphore + **cipher**
Campaign A at 16 B: **1,740 µs**
Real AES call (measured later): **57–103 µs**

**Visual:** A horizontal bar for the 1,740 µs, split into coloured segments with the cipher as a thin sliver at the end.

**Say:** "The timer didn't measure only the cipher. It also included the sensor reads, which alone cost about 400 microseconds, plus creating a task and waiting on a semaphore. So most of the 'execution time' in Campaign A was measurement overhead. It was trial latency, not cipher time."

---

### Slide 23 — Audit ③: Other Confounds
**On screen:**

| Found | Why it matters |
|---|---|
| "Before" reading right after an MQTT publish | Baseline not idle, radio active |
| Fresh reboot every trial | Cold-start effects included |
| ASCON and AES on different days | Session conditions differ |
| AES setup inside every call | Not present for ASCON; realistic, but must be stated |
| Firmware at 160 MHz | Thesis said 240 MHz, now corrected |

**Visual:** The table (summary of Thesis Table 9).

**Say:** "The audit found more. The baseline reading was taken while the radio was still active. Each trial started cold after a reboot. The two ciphers were measured in different sessions. AES rebuilt its setup on every call, which is realistic for a node that loses RAM in deep sleep, but it has to be stated. The first three problems explain why Campaign A can't be used for energy. The last two explain which parts of it are still useful."

---

### Slide 24 — Designing Campaign B: The Principle
**On screen:**
Don't measure one call.
Run it **back-to-back for 700 ms**, and compare with **idle** before and after.
Energy per call = V × (I_load − I_idle) × t_per_call

**Visual:** `figures/fig_method_windows.png` (idle → load → idle windows)

**Say:** "Instead of trying to catch one tiny encryption, I made it repeat thousands of times for 700 milliseconds while the sensor averaged. Then I compared that with the idle level just before and just after. It's like weighing a whole ream of paper to find the weight of one sheet. Because the sensor offset appears in both the load and the idle reading, it cancels out, so no correction is needed."

---

### Slide 25 — Campaign B: One Measurement in Detail  **[optional]**
**On screen:**
Idle 400 ms (drop first 150 ms) → **Load 700 ms** (drop first 200 ms) → Idle 400 ms
INA219: **128-sample averaging** (~68 ms per result)
Core 1: cipher loop, counts calls · Core 0: reads sensor every ~10 ms
No Wi-Fi, no MQTT, no deep sleep

**Visual:** Timeline with the three windows, discarded parts hatched, and a two-lane diagram for core 0 and core 1.

**Say:** "Each configuration was measured in three windows. I discarded the start of each window so the sensor's averaging had settled. The sensor was switched to 128-sample averaging, so a 700-millisecond window contains several complete, clean results. The cipher ran on one core and the sensor was read from the other, so measuring didn't interrupt the encryption. Wi-Fi was off, so nothing else was drawing current."

---

### Slide 26 — Four Things Measured
**On screen:**
**ASCON**: software cipher
**AES_COLD**: setup + encrypt, every call
**AES_WARM**: setup once, then encrypt only
**AES_SETKEY**: setup only, no encryption

**Visual:** 4 cards with icons (❄️ cold, 🔥 warm, 🔑 setup).

**Say:** "I split AES into cases. Cold rebuilds the AES context for every message, like a node that loses RAM in deep sleep. This is exactly what Campaign A did. Warm prepares it once and reuses it. SETKEY measures the setup step alone, so I can measure the setup cost directly instead of guessing it from a regression line."

---

### Slide 27 — Runs and Randomisation
**On screen:**

| | Run 1 (coarse) | Run 2 (fine sweep) |
|---|---|---|
| Sizes | 18 (16 → 1,600 B) | 9 (64 → 128 B, step 8) |
| Replicates | 10 | 15 |
| Rows | 550 | 420 |

Every replicate: all configurations in **shuffled order**, same session

**Visual:** The table, plus a small arrow "Run 1 found the crossing between 64 and 128 B → Run 2 zoomed in".

**Say:** "Run 1 covered the whole range. It showed the crossing lay between 64 and 128 bytes, which is far from 347. So I designed Run 2 as a fine sweep in 8-byte steps around that region. Within each replicate every configuration ran once in a shuffled order, so ASCON and AES shared the same session, temperature and supply. This removes the session problem from the audit."

---

### Slide 28 — Statistics, Redesigned  **[optional]**
**On screen:**
**Paired** t-tests: both ciphers in every replicate
**Two-sided**: the winner flips at the break-even
**Holm correction** across sizes (α = 0.01)
**Bootstrap** 95% interval for the break-even (5,000 resamples)
Effect sizes (µJ, %) reported with every p-value
**No** trimming, filtering or offset correction

**Visual:** Six check marks, each next to the Campaign A flaw it fixes (one-tailed, uncorrected, unpaired, trimmed).

**Say:** "I also fixed the statistics. Because both ciphers ran in every replicate, I could use paired tests. The tests are two-sided, because the winner changes at the break-even, and Holm-corrected, because I run one test per size. The break-even gets a bootstrap confidence interval instead of a single number. No data was removed."

---

### Slide 29 — Can We Trust Campaign B?
**On screen:**

| Check | Result |
|---|---|
| Rows removed | **0 of 970** |
| Signal vs idle drift | 12.8–16.7 mA vs ~0.01 mA |
| Repeat-to-repeat variation | **0.3%** |
| Run 1 vs Run 2 (shared sizes) | within **0.5%** |
| AES setup cost, Run 1 / Run 2 | 1.896 / 1.895 µJ |
| Linear fit | R² > **0.9999** |
| Fit vs measured break-even | **99 B vs 96–107 B** ✅ (A: 206 vs 347 ❌) |

**Visual:** The table. Colour the last row green, with Campaign A in red next to it.

**Say:** "Before using Campaign B, I checked that it could be trusted. Nothing had to be removed. The signal was about a hundred times larger than the idle drift. Repeats varied by only 0.3%, and the two runs agreed within half a percent. The key test is the last row: the line fit and the direct measurement now give the same break-even. That is exactly the consistency check Campaign A failed."

---

### Slide 30 — Comparing A and B ①: Time
**On screen:**
Slopes **agree**: ASCON 1.197 vs 1.180 µs/B · AES 0.901 vs 0.897 µs/B
A = B + constant offset: **1.31 ms** (ASCON), **1.64 ms** (AES)
→ Campaign A time **increments** were sound, **absolute** times were not

**Visual:** `figures/fig_campaignA_vs_B.png` (time panel): two parallel lines per cipher, with the gap labelled "instrumentation + cold start".

**Say:** "With both datasets in hand I compared them at the eight payload sizes they share. For time, the slopes agree within 1.4%, so Campaign A measured the *extra* time per byte correctly. But every value carries a constant offset of 1.3 to 1.6 milliseconds, which is the instrumentation. The offset is about 325 microseconds bigger for AES, which is why Campaign A put the time crossover at 1,250 bytes. The real crossover is about 175 bytes."

---

### Slide 31 — Comparing A and B ②: Power and Energy
**On screen:**

| At 16 B | Campaign A | Campaign B |
|---|---|---|
| ASCON power | 20.3 mW | 75.1 mW |
| AES power | 24.2 mW | 63.8 mW |
| ASCON energy | 27.9 µJ | 4.35 µJ |
| AES energy | 42.1 µJ | 6.56 µJ |

A's energy was **6.4× too high** at 16 B

**Visual:** `figures/fig_campaignA_vs_B.png` (power panel): stepped A lines against flat B lines.

**Say:** "Power did not agree. In Campaign B, power is flat across payload sizes, which is what you'd expect from a CPU doing the same kind of work. Campaign A power was much lower and changed in steps. Because Campaign A time was also inflated, its energy at 16 bytes was 6.4 times the validated value for both ciphers."

---

### Slide 32 — Where 347 Bytes Came From
**On screen:**
AES power between 336 and 352 B: **24.9 → 14.8 mW (−41%)**
AES time over the same step: smooth (2,029 → 2,044 µs)
The 347 B crossing sits **exactly on this step**
Remove the step → crossing moves to **~564 B**. Remove both steps → **no crossing**

**Visual:** Zoom of the Campaign A energy-per-byte curves around 336–352 B, with the AES drop arrowed and the 347 B crossing marked.

**Say:** "This answers review question 2. Between 336 and 352 bytes, the measured AES power suddenly dropped by 41%, while its time rose smoothly. The whole drop came from the power reading. The 347-byte break-even sits exactly on that step. As a check, if I hold AES power at its level before the step, the crossing moves to about 564 bytes, and if I remove both steps there is no crossing at all. So 347 came from a jump in the power readings, not from anything the ciphers did. It also explains the 206: a straight line fitted through a stepped curve can't reproduce where the curve crosses."

---

### Slide 33 — Was Trimming the Cause?
**On screen:**

| | No trimming | IQR k = 3 | IQR k = 1.5 (used) |
|---|---|---|---|
| Break-even | **345.0 B** | **347.4 B** | **346.8 B** |
| Sign changes | 8 | 4 | 3 |

Repeatable ≠ valid

**Visual:** `figures/fig_campaignA_trimming_sensitivity.png`

**Say:** "Review question 4 asked whether removing outliers created the 347. I re-ran the analysis with no trimming and with a looser rule. The break-even stayed between 345 and 347 bytes. So trimming did not cause it. The step is systematic, and it is there in the raw data too. That is the lesson: a result can be perfectly repeatable and still be wrong, if the error is built into the method."

---

### Slide 34 — Statistics, Redone on Campaign A  **[optional]**
**On screen:**

| Sizes significant (of 100) | Time | Power | Energy/B |
|---|---|---|---|
| One-tailed (original) | **21** | 78 | 72 |
| Two-sided, Holm | **100** | 99 | 92 |

"Times converged" → **withdrawn**

**Visual:** The table, with an arrow from 21 to 100.

**Say:** "Review question 5. I originally ran 300 one-tailed tests with the hypothesis 'ASCON is greater' at every size, with no correction. ASCON is only slower than AES above about 1,250 bytes, which is about 21 of the 100 sizes. That's where the 21 came from. Two-sided, the times differ at every size. So my claim that the times converged, and that power rather than speed drove the energy gap, is withdrawn."

---

### Slide 35 — The Five Review Questions, Answered
**On screen:**

| Question | Answer |
|---|---|
| 1. Flowchart symbols | Redrawn (Figure 1) |
| 2. 206 vs 347 B | Both artefacts of a power step. Validated: **~100 B**, fit and data agree |
| 3. Intercept = initialisation? | No. Setup measured directly: **1.90 µJ**, not 30 µJ |
| 4. Trimming? | Did not create 347 (345–347 B without it), but 347 is still not valid |
| 5. One-tailed tests | Redone two-sided + Holm; "power drives energy" withdrawn |

**Visual:** The table with a green tick per row.

**Say:** "So every review question now has an answer backed by data. Two of the answers changed my conclusions, and the next part shows the validated results."

---

# PART 4 — Validated Results (Campaign B)

### Slide 36 — Speed
**On screen:**
16 B: ASCON **57.9 µs** · AES_COLD **102.8 µs** · AES_WARM **57.4 µs**
1,600 B: ASCON **1,927 µs** · AES_COLD **1,524 µs**
ASCON faster below **~175 B**, AES faster above
Throughput at 1,600 B: AES 1.05 MB/s vs ASCON 0.83 MB/s

**Visual:** `figures/fig07_time_per_operation.png`

**Say:** "ASCON starts faster because it has no setup step. AES costs less for each extra byte, 0.90 against 1.18 microseconds, so it overtakes ASCON at around 175 bytes. When the AES context is reused, AES matches ASCON even at 16 bytes."

---

### Slide 37 — The Cost of Getting AES Ready
**On screen:**
AES setup = **30.9 µs · 1.90 µJ** per message
(95% CI 1.89–1.90 µJ, identical in both runs)
First draft: 30.14 µJ → **16× too high**

**Visual:** `figures/fig_aes_setup_cost.png`

**Say:** "For the first time, I measured the AES setup cost directly: 1.9 microjoules. My first draft estimated 30 microjoules by extending a poor fit down to zero bytes. The real value is 16 times smaller. The earlier number wasn't the hardware starting up. It was mostly measurement overhead."

---

### Slide 38 — Power Is Almost the Same, So Time Decides
**On screen:**
Extra power: ASCON **75.3 mW** · AES **67.8 mW** (+11%)
Time at 1,600 B: ASCON takes **+26%**
1.11 × 1.26 ≈ **1.40** → AES uses **28% less** energy
**Energy ≈ how long the CPU is busy**

**Visual:** `figures/fig_power_by_variant.png`

**Say:** "Both ciphers draw roughly the same power. ASCON draws about 11% more and takes 26% longer at 1,600 bytes, and multiplying those gives the 28% energy gap. So on this chip, energy is mostly decided by how long the CPU stays busy. This reverses the claim in my first draft, which I have withdrawn."

---

### Slide 39 — Energy per Call
**On screen:**

| Payload | ASCON | AES_COLD | AES_WARM |
|---|---|---|---|
| 16 B | **4.35 µJ** | 6.56 µJ | 3.75 µJ |
| 128 B | 14.30 µJ | **13.48 µJ** | 10.69 µJ |
| 1,600 B | 145.17 µJ | **104.67 µJ** | 101.94 µJ |

16 B: ASCON uses **34% less** · 1,600 B: AES uses **28% less**

**Visual:** `figures/fig09_energy_per_byte.png`

**Say:** "Small messages favour ASCON and large messages favour AES. The curves cross, so there has to be a break-even point somewhere between 16 and 128 bytes."

---

### Slide 40 — The Break-Even
**On screen:**
# ≈ 100 bytes
95% bootstrap interval: **96–107 B**
Line-fit prediction: **99 B** ✅

| Size | 64 | 80 | 96 | 104 | 112 | 128 |
|---|---|---|---|---|---|---|
| ASCON − AES (µJ) | −0.87 | −0.47 | **−0.01** | −0.20 | +0.47 | +0.88 |
| Winner | ASCON | ASCON | tie (p = 0.78) | ASCON | AES | AES |

**Visual:** `figures/fig10_fine_sweep.png`

**Say:** "The fine sweep puts the crossing at about 100 bytes, with a 95% interval of 96 to 107. At 96 bytes the two ciphers can't be told apart statistically. The crossing appeared in every one of the 5,000 bootstrap resamples. The line-fit method, calculated independently, gives 99 bytes, so both methods agree."

---

### Slide 41 — Why a Break-Even Exists
**On screen:**
Energy per byte = fixed cost ÷ size + cost per byte

| | Fixed (µJ) | Per byte (µJ/B) |
|---|---|---|
| ASCON | **2.91** | 0.089 |
| AES, setup every call | 5.57 | **0.062** |
| AES, context kept | **2.76** | **0.062** |

🚕 AES = starting fee + cheap per km · 🚶 ASCON = no fee, costs more per km

**Visual:** Simple two-line chart (cost vs distance), with the crossing labelled "100 B".

**Say:** "The break-even follows from how the costs are structured. AES with setup has a higher fixed cost but a lower cost per byte. Think of a taxi: AES has a starting fee but a cheap rate per kilometre. ASCON has no fee but costs more per kilometre. For short trips ASCON wins, and for long trips AES wins. Solving the two lines gives 99 bytes."

---

### Slide 42 — Keep AES Warm and It Always Wins
**On screen:**
Setup **every message** → break-even at ~100 B
Setup **kept** → AES wins at every size from 64 B, ties at 16 B
→ The real question: *can your firmware keep the AES context?*

**Visual:** Two mini charts side by side: COLD with a crossing, WARM with no crossing (from `fig08_energy_fits.png`).

**Say:** "Look at the last row of the previous table. If the context is kept, AES loses its starting fee but keeps its cheaper per-byte cost, so there's no crossing. This applies to a node that sends several messages per wake-up, or keeps the context in RTC memory. So the real design question is whether you can keep the AES context."

---

### Slide 43 — The Big Picture: Sleep Dominates
**On screen:**

| Payload | Cipher choice changes total cycle energy by |
|---|---|
| 16 B | 0.22% |
| 352 B | 0.67% |
| 1,600 B | 3.57% |

Encryption = **0.4%–13%** of a modelled 60 s cycle (sleep 5–10 µA, datasheet)

**Visual:** `figures/fig_modelled_duty_cycle.png` (or a pie chart where the encryption slice is tiny)

**Say:** "With a 60-second sleep, sleep uses most of the energy. So the cipher choice changes total energy by less than 4%. The sleep phase is modelled, not measured, but it's identical for both ciphers, so it can't move the break-even. It only scales the total. The choice matters most for nodes that send often or send large batches."

---

# PART 5 — From Evidence to Conclusions (Chapters 6–7)

### Slide 44 — What Stood, What Changed, What Was Withdrawn
**On screen:**

| Chapter 4 finding | Status |
|---|---|
| Time linear with size | ✅ **Confirmed** (1.180 / 0.897 µs/B) |
| AES cheaper per byte | ✅ **Confirmed** (0.062 vs 0.089 µJ/B) |
| AES +24% memory | ✅ **Retained** |
| Break-even 347 B | 🔄 **Replaced** → ~100 B (96–107), none if context kept |
| AES initialisation 30 µJ | 🔄 **Replaced** → 1.90 µJ, measured |
| Time crossover 1,250 B | 🔄 **Replaced** → ~175 B |
| Power 20–52 mW | ❌ **Withdrawn** → 75 / 68 mW |
| "Energy driven by power" | ❌ **Withdrawn** → driven by time |

**Visual:** The table with green, amber and red rows (summary of Thesis Table 20).

**Say:** "This slide is where the validation leads. I went through every finding from Chapter 4. Things that depended only on time increments or memory survived. Anything that depended on the two-reading power method was replaced by a Campaign B value or withdrawn. My conclusions are built only on the green rows and the Campaign B values."

---

### Slide 45 — How Each Conclusion Was Reached
**On screen:**

| Objective | Evidence | Conclusion |
|---|---|---|
| ① Energy + setup | 18 sizes × 10 reps, AES_SETKEY, R² > 0.9999 | Setup 1.90 µJ; 0.089 vs 0.062 µJ/B |
| ② Duty cycle | Measured active phase + modelled sleep | Encryption 0.4–13%; choice < 4% |
| ③ Break-even | Fine sweep, paired + Holm, bootstrap, fit cross-check | ~100 B (96–107); none if context kept |

**Visual:** Three rows, each with the objective icon from slide 5 → evidence → conclusion arrows.

**Say:** "Here is the chain from evidence to conclusion for each objective. Every number in the conclusion column comes from Campaign B and passed the reliability checks on slide 29. For the break-even I used two independent methods, the direct fine sweep and the line fit, and I only accepted it because they agree."

---

### Slide 46 — Answer to the Research Question
**On screen:**
**Neither cipher is always more energy-efficient.**
Setup every message → **ASCON below ~100 B**, **AES above**
Context kept → **AES at every size**
AES needs **24% more RAM**
At a 60 s interval the difference is **< 4%** of total energy

**Visual:** Text slide. Bold the two conditions.

**Say:** "So my answer to the research question is conditional. It depends on two things: the payload size, and whether the AES context is rebuilt for every message. Those two conditions decide the winner. And at long sleep intervals, the choice has only a small effect on battery life."

---

### Slide 47 — Resolving the Literature Conflict
**On screen:**
"ASCON wins" studies → compared vs **software** AES
"Hardware AES wins" studies → never tested ASCON
**Both are right, in their own range**

**Visual:** Two groups of paper icons, with this study's break-even bridging them.

**Say:** "The literature wasn't really contradicting itself. The two groups answered different questions. My break-even shows both are right: ASCON for small messages, hardware AES for large ones or when the setup is reused. I didn't test software AES, so I can't confirm their exact percentages, only the overall pattern."

---

### Slide 48 — Design Rule for Engineers
**On screen:**
Can you keep the AES context?
Yes → **AES**
No → payload < 100 B → **ASCON**, else **AES**
Tight RAM? → ASCON (−24%)

**Visual:** A simple decision-tree flowchart.

**Say:** "This is the practical takeaway. It's one question about your firmware, then one about your message size. Many LPWAN sensor messages are under 100 bytes, so for a node that sends one message per wake, ASCON is the better choice."

---

### Slide 49 — Contributions
**On screen:**
1. First same-chip ASCON vs hardware AES comparison
2. Break-even ≈ 100 B, and when it disappears
3. AES setup cost on ESP32 measured directly (1.90 µJ)
4. Method lesson: per-trial fails, sustained-load works
5. First memory comparison on the same platform (+24%)

**Visual:** 5 icons.

**Say:** "The fourth point matters for other researchers. Taking two sensor readings around a millisecond-scale operation can give a result that is repeatable but wrong. My 347 bytes is the example. The sustained-load method fixes this, and anyone with a low-cost current sensor can use it."

---

### Slide 50 — Limitations
**On screen:**
One board, one sensor, no reference instrument
Sleep **modelled**; wake-up and Wi-Fi not measured
Steady state (warm), Wi-Fi off, one core
Encryption only (no decryption or associated data)
Hardware/software split inside GCM not examined

**Visual:** 5 small grey icons.

**Say:** "These limit how far the results generalise. The absolute energy scale depends on the INA219's calibration. But both ciphers were measured on the same board, with the same sensor, in the same session, so the comparison between them still holds."

---

### Slide 51 — Future Work
**On screen:**
Cold-start: first call after wake from deep sleep
Measure sleep, wake-up and transmission
Multiple boards + reference meter
Software AES on the same board
Real battery-drain trial

**Visual:** A roadmap arrow with 5 steps.

**Say:** "The top item comes directly from the validation. Campaign A had an extra 325 microseconds for AES that I couldn't explain, and the most likely cause is a first-run effect after reboot. That needs its own experiment. After that, measuring the full cycle and running a battery test would complete the picture."

---

### Slide 52 — Closing
**On screen:**
**Neither wins always.**
It depends on **payload size** and **AES setup reuse**.
And a measurement you can repeat is not always a measurement you can trust.

**Visual:** The taxi chart from slide 41, small.

**Say:** "Hardware isn't automatically better, and lightweight isn't automatically lighter. It depends on message size and whether you keep the AES context. The second lesson from this project is about method: my first answer was repeatable but wrong, and checking my own work is what led to the right one. Thank you."

### Slide 53 — Thank You / Q&A

---

# BACKUP SLIDES (show only if asked)

### B1 — Full Audit Table
Thesis Table 9, all 8 items. Use it if the panel asks "what exactly was wrong with Campaign A?"

### B2 — Full A vs B Time Table
Thesis Table 16 (8 shared sizes). The offset column (1,313 → 1,340 µs for ASCON, 1,638 → 1,644 µs for AES) is the key evidence that the slopes are right and the offsets are not.

### B3 — Full A vs B Power and Energy Table
Thesis Table 17. Point to the steps: ASCON 19.8 → 52.6 mW at 560–576 B, AES 24.9 → 14.8 mW at 336–352 B, AES 21.9 → 47.8 mW at 1,520–1,536 B.

### B4 — Full Fine-Sweep Table
Thesis Table 14 (all 9 sizes, with Holm results). Mention the 16-byte block zig-zag: 72, 88, 104 and 120 B sit slightly below their neighbours for AES.

### B5 — Campaign B Energy Fits
`figures/fig08_energy_fits.png` + Thesis Table 13.

### B6 — Memory Measurement Method
`heap_caps_get_minimum_free_size()` (peak heap) + `uxTaskGetStackHighWaterMark()` in a dedicated task. Run-time RAM only, not flash.

### B7 — Moved-out optional slides
Put slides 13, 25, 28 and 34 here if you are running the 25-minute version.

---

## Likely panel questions

| Question | Short answer |
|---|---|
| Why trust Campaign B over A? | The offset cancels by design, nothing was removed, repeats vary by 0.3%, two runs agree within 0.5%, and the fit (99 B) matches the direct measurement (96–107 B). Campaign A failed that check (206 vs 347). |
| Why not just fix Campaign A's analysis instead of a new experiment? | The problem was in how the data was captured. Two 532 µs sensor readings around a 60–100 µs call contain no information about the call's current, and no analysis can recover it. |
| Is anything from Campaign A still used? | Yes. Memory (+24%), and the time slopes, which agree with Campaign B within 1.4%. Its energy, power and break-even are not used. |
| Is the INA219 accurate enough? | The absolute scale depends on its calibration, but both ciphers use the same sensor, so the comparison holds. The extra current (12.8–16.7 mA) is about 100× the idle drift. |
| Isn't Campaign B unrealistic, since real nodes don't encrypt in a loop? | It measures the steady-state cost of one call. AES_COLD reproduces the per-message setup of a node that wakes from deep sleep. What it leaves out is cold-start after boot, which is listed as the first future-work item. |
| Why is the AES offset in A 325 µs larger? | Most likely a first-run effect after each reboot (cold cache, first use of the AES peripheral). It wasn't tested, so it is future work. |
| The setup step is 1.90 µJ but the COLD–WARM intercept gap is 2.82 µJ. Why? | The setup step accounts for about two thirds of it. The rest was not isolated. A likely candidate is the first block after a fresh context, but this wasn't tested. |
| Why is ASCON's power higher than AES's? | ASCON keeps the CPU fully busy computing the permutation, while part of AES's work runs in the peripheral. Exactly which GCM steps run in hardware was not examined. |
| Was trimming the cause of 347? | No. Without trimming it was 345, with k = 3 it was 347.4. The cause was the power step. |
| Why 160 MHz, not 240? | That was the firmware setting. Chapter 3 originally said 240 and was corrected. |
| Why not measure sleep? | The INA219 can't resolve 5–10 µA well. The sleep term is identical for both ciphers, so it can't move the break-even. |
| Did you test software AES? | No. That's why the 74% figure from Rabbani (2025) can't be confirmed or refuted, only the qualitative relation. |
| Does the break-even depend on the sleep interval? | No. Sleep energy is the same for both ciphers, so it cancels in the difference. The interval only changes how much the choice matters for total energy. |
