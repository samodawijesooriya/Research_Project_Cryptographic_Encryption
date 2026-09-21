# Chapter 05: Discussion (revised, full replacement)

*Section numbers are corrected (the current draft has two 5.2.2 and no 5.5). Comparisons with earlier draft claims are deliberate: the chapter says plainly what changed and why.*

---

## 5.1 Introduction

This study asked whether software-based ASCON-128 or hardware-accelerated AES-128-GCM is the more energy-efficient choice for a battery-powered ESP32 node, and under what conditions (1.7). The answer, from the sustained-load measurements of Campaign B, is conditional on two things: the payload size and whether the AES-GCM context is prepared on every message. When it is (the situation of a node that loses RAM in deep sleep and sends one message per wake), ASCON-128 used less energy below about 100 bytes and AES-128-GCM above it. When the context is kept, AES-128-GCM was equal or better at every tested size.

This is a different result from the 347-byte break-even of the first analysis. The chapter explains the mechanism behind the new result (5.2.1 to 5.2.3), what it means for a real duty cycle (5.2.4), why the first analysis gave a different answer (5.2.5), how the result compares with the literature (5.3), and how far it can be trusted (5.4 and 5.5).

---

## 5.2 Interpretation of Findings

### 5.2.1 Why a break-even exists
The break-even exists because the two ciphers pay for their work in different proportions. Writing the energy per byte as

Energy per byte = (fixed cost ÷ payload size) + variable cost per byte  (Equation 5)

the fixed term shrinks as the payload grows, so small payloads are decided by the fixed cost and large payloads by the variable cost. The measurements gave:

| | Fixed cost (fitted intercept, µJ) | Variable cost (slope, µJ/B) |
|---|---|---|
| ASCON-128 | 2.91 | 0.0889 |
| AES-128-GCM, setup on each call | 5.57 | 0.0619 |
| AES-128-GCM, context reused | 2.76 | 0.0620 |

*Table 16 – Fixed and variable energy costs (Run 1, Table 8).*

AES-128-GCM with per-message setup starts higher and grows more slowly; ASCON-128 starts lower and grows faster. Because each wins on a different term, a payload size exists at which they are equal, and it is a mathematical consequence of this structure and not a coincidence of the data. Solving the fitted lines gives 99 bytes; the directly measured crossing in the fine sweep was 106 bytes (95% CI 96 to 107 bytes). The two agree because, unlike in Campaign A, the linear model here describes the data almost exactly (R² > 0.9999).

The slopes have a plausible cause. ASCON-128 executes its permutation on the CPU, so each byte costs CPU cycles and the CPU is active for longer (1.18 µs per byte against 0.90 for AES-128-GCM). For AES the block operation is performed by the AES peripheral. **Which parts of GCM run in the peripheral and which run on the CPU (for example the authentication step) was not examined in this study**, and the AES slope should be read as the measured cost of the complete mbedTLS call, not of the peripheral alone.

### 5.2.2 What the fixed cost is
The directly measured setup step (context initialisation and key load, no encryption) cost 30.9 µs and 1.9 µJ. This is the measured *initialisation cost of the AES-GCM context* and answers the part of Objective 1 that asked for the initialisation overhead. It is about fifteen times smaller than the 30.14 µJ that the first draft attributed to the "hardware engine" from a regression intercept, and the way that number was obtained (extrapolating a poor fit, R² = 0.43, to a payload of zero bytes) could not identify its cause. Two further observations:

- The gap between the fitted intercepts of AES_COLD and AES_WARM (2.82 µJ, 45.4 µs) is larger than the setup step alone (1.90 µJ, 30.9 µs). About one third of the gap was not isolated. Candidates are effects of first use of a freshly initialised context on the first block, but this was not tested.
- The fitted fixed cost of ASCON-128 (2.9 µJ) is not a separately measured "setup" step; it is the intercept of the fit, and includes the loop and call overhead common to all variants. The comparison of fixed costs is therefore between fitted intercepts, and only the AES setup cost has been isolated directly.

### 5.2.3 Setup on every message versus once
The two AES variants correspond to two policies. A node that enters deep sleep between messages loses RAM and must rebuild the context on each wake (Ciuffoletti, 2022; Gerndt et al., 2025, as reviewed in 2.5.2), which is the AES_COLD case. A node that sends several messages per wake, or that keeps the key schedule in RTC memory, can amortise the setup, which is the AES_WARM case. For the ESP32 the choice therefore moves the break-even from roughly 100 bytes to "no break-even". This is the most useful practical statement of the study: the payload-size criterion applies to nodes that send one message per wake, and nodes that send bursts should prefer AES-128-GCM.

### 5.2.4 Power versus time
The earlier draft concluded that the energy difference was "driven primarily by power rather than speed" because execution time differed significantly at only 21 sizes. That conclusion is withdrawn. Two-sided tests show that execution time differed significantly at all 100 sizes of Campaign A (Table 15); the 21 was a result of testing a single direction (H₁: ASCON slower) that holds only above the time crossover near 1,250 bytes.

In Campaign B, time and power both contribute, but time dominates. ASCON-128 drew about 10% more extra power than AES-128-GCM (75.3 versus 67.8 mW), while at 1,600 bytes it took 26% more time (1,927 versus 1,524 µs). The energy gap of 28% is roughly the product of the two. At small payloads AES-128-GCM with per-message setup is slower (102.8 versus 57.9 µs at 16 bytes), which is why ASCON-128 wins there. In this platform, energy differences between the two ciphers are mostly differences in how long the CPU is busy.

### 5.2.5 Why the first analysis gave a break-even of 347 bytes
Campaign A produced a break-even near 347 bytes, and that value was reproducible: recomputing it without outlier trimming and with two trimming factors gave 345.0, 347.4 and 346.8 bytes (Table 14). It is therefore not a product of trimming. It also did not appear in Campaign B, where the break-even is near 100 bytes. The properties of Campaign A listed in 4.2.3 are the reasons the two disagree:

- the INA219 could not resolve the current during a call of about 2 ms, and power was taken as a difference of two readings whose relation to the call is not defined;
- the timed region contained about 1.3 to 1.6 ms of task creation and sensor reads, against a cipher call of 58 to 103 µs at 16 bytes;
- the algorithms were measured in different sessions;
- a further difference between the two algorithms at 16 bytes in Campaign A (about 370 µs) is far larger than any difference in Campaign B (45 µs). Since in Campaign A each trial ran once after a fresh boot, a plausible contributor is the cost of first execution (cold instruction cache and first use of the AES peripheral), which the sustained-load method deliberately excludes. **This was not tested**; a boot-to-first-call measurement is proposed in 6.5.

The regression-versus-measurement disagreement in Campaign A (206 versus 347 bytes) is best read as evidence of the same problem: a straight-line model fitted to noisy energy values (R² of 0.91 and 0.43) is not expected to reproduce a crossing measured directly. The internal consistency of Campaign B (99 versus 106 bytes) is the contrast.

### 5.2.6 Practical significance within a duty cycle
Against a modelled 60-second sleep interval, the cipher choice changed total energy per cycle by 0.1% to 3.6% (Table 11). Even at 1,600 bytes the encryption phase was 13% of the cycle. The algorithm therefore matters most for nodes that (a) wake often or send large batches, so that active energy is a larger share; (b) are already very close to their energy budget; or (c) can put a number on the cost of transmitting the extra tag bytes and authentication data, which was outside this study. For a node with a chip-level sleep current and a long sleep interval, other factors (Wi-Fi association and transmission, sleep current, wake-up cost) are far larger than the encryption phase. The value of the break-even is as a design rule for the active phase, not a large lever on battery life at low reporting rates. The transmission and wake-up costs, which would enlarge the non-cipher part of the cycle still further, were not measured.

---

## 5.3 Comparison with Existing Literature

Chapter 2 found that studies favouring ASCON [Ridho Rabbani, 2025; Tripathi et al., 2024] compared it with *software* AES, while studies favouring hardware AES [Rafat et al., 2025; Hung & Hsu, 2018] compared it with a software AES baseline and not with ASCON. The present measurements compare ASCON-128 with hardware-assisted AES-128-GCM on one platform. They support a conditional reading rather than a contradiction between the two groups:

- ASCON-128 is more energy-efficient at small payloads when the AES context must be prepared per message, which is compatible with the lightweight-cryptography claim for short messages.
- Hardware-assisted AES-128-GCM is more efficient at larger payloads and, if its setup is amortised, at nearly all sizes, which is compatible with the accelerator studies.

This study did not measure software AES, so the specific figures of those studies (for example the 74% latency reduction of ASCON over software AES) cannot be confirmed or refuted here; only the qualitative relation is addressed.

The results agree with the literature in a second respect: execution time scaled linearly with payload (R² > 0.9999 for both), as expected for a block-based construction [Ridho Rabbani, 2025].

Two contributions extend prior work. First, this study adds power, energy and significance testing to the benchmarking structure of Jin and Becker (2022), who reported execution time and throughput only. Second, it reports energy per byte across payload sizes for the AES-GCM/ESP32 pipeline of Amirkhanova et al. (2026), which those authors listed as missing. A third point is methodological: it documents that a per-trial, two-reading power method does not resolve millisecond-scale operations, and gives a sustained-load alternative (3.3.1), which may be of use to others using low-cost current monitors [Dezfouli et al., 2018].

Finally, the memory result (AES-128-GCM about 24% larger footprint than ASCON-128, 4.6) is a new comparison: none of the studies reviewed in Chapter 2 compared these on the same platform. The direction is plausible given that the mbedTLS GCM context holds a key schedule and precomputed authentication tables, whereas ASCON-128 holds a 320-bit state; that explanation was not verified by inspecting the library.

---

## 5.4 Validity and Trustworthiness of the Sustained-Load Measurement

Because the energy conclusions depend on Campaign B, its credibility is examined explicitly.

**Signal against noise.** The extra current under load (12.8 to 16.7 mA) was two orders of magnitude above the drift of the idle baseline between windows (+0.01 mA, standard deviation about 0.1 mA).

**Repeatability.** The median coefficient of variation of energy across replicates was 0.3%. Two separate runs (with different payload sets and replicate counts) agreed where they overlapped: mean energy differed by less than 0.5% at 64 and 128 bytes, and the AES setup cost was 1.896 and 1.895 µJ.

**Internal consistency.** Time and energy were both linear in payload size (R² > 0.9999), and the break-even predicted from the fitted lines (99 bytes) matched the one measured directly (96 to 107 bytes). Campaign A failed this test (206 versus 347 bytes).

**Removal of known confounds.** The sensor offset cancels in the load-minus-idle difference; the timed region contains only the cipher call in a long loop; the algorithms share one session in shuffled order; no data were removed.

**Independence of timing and current.** Time per call comes from the CPU timer and current from the INA219; energy ordering followed time ordering with a roughly constant power difference, so the two measurement paths do not contradict each other.

**What the evidence does not show.** No independent reference instrument (a bench meter or a second sensor) was used, so the absolute energy scale rests on the INA219 calibration; the relative comparison between algorithms does not, because both use the same sensor and offset. A single board was used (5.5).

---

## 5.5 Limitations

1. **Modelled duty cycle.** Only the encryption phase was measured. The sleep phase was modelled from a datasheet current for a 60-second interval, and wake-up, Wi-Fi association and MQTT transmission were not measured. The term "duty cycle" is used in this sense throughout. The sleep energy is identical for both ciphers, so it cannot change the break-even, but the "under 4%" statement depends on it (Table 11, both currents shown). The wake timer used while collecting Campaign A was shorter than 60 s **[CONFIRM 2]** so that about 127,000 trials could be collected.
2. **Steady-state, not cold-start.** Campaign B repeats the cipher call in a warm loop with Wi-Fi off, on one core. It does not capture first-execution effects after a boot, which real duty-cycled nodes experience, and which may add a fixed cost (5.2.5). The break-even applies to the steady-state cost of the call.
3. **Single board, single sensor.** All measurements are from one ESP32-WROOM-32E and one INA219 with a 0.1 Ω shunt. Silicon and sensor variation across units was not assessed, but both algorithms were measured on the same unit in the same session.
4. **Extra current, not total.** ΔP is the extra power over the idle level of a development board. The idle level (about 35 to 37 mA) includes board components and is not representative of a bare module in a product.
5. **Scope of cipher use.** Only encryption with a 16-byte tag, no associated data and one CPU core was measured; decryption, associated data and multi-core use were not.
6. **Which parts of GCM are hardware-assisted** was not established (5.2.1).
7. **Campaign A** (memory measurement and the 561 and 510 iterations) is retained as documented but is not used for energy; its raw data are in Appendix C.
8. **Sensor resolution.** The INA219 has a 12-bit ADC. The differences of interest (several µJ, 10% in power) were well above its resolution in the averaged mode used, but per-call differences below about 0.1 µJ were not resolved.
9. **Battery effects** (chemistry, discharge curve, temperature) are outside the scope of a controlled comparison and would need a field trial.

---

## 5.6 Summary of Chapter 5

The results show a payload-size break-even of about 100 bytes for AES-128-GCM with per-message setup, and none if the context is kept. The mechanism is a lower fixed cost but a higher per-byte cost for ASCON-128 (5.2.1). The AES setup cost was measured directly as 30.9 µs and 1.9 µJ, and replaces the figure of 30.14 µJ in the first draft. The claim that power, rather than time, drives the difference is withdrawn (5.2.4). The 347-byte result of Campaign A is reproducible under trimming but is attributed to limits of the instrumentation and was not confirmed by the validation measurement (5.2.5). Against a modelled 60-second duty cycle the cipher choice changed total energy by under 4%. The limits listed in 5.5 bound these conclusions, and Chapter 6 states what should be done next.

---

### Table 8 of the current draft ("Resource cost before encryption")
Keep the table but replace its prose with measured wording:

| Item | Content |
|---|---|
| AES-128-GCM fixed cost | Preparing the context: initialisation and loading of the key, including derivation of the authentication key material. **Measured: 30.9 µs, 1.9 µJ per call.** |
| AES-128-GCM per-byte cost | Block processing by the AES peripheral plus the surrounding library calls. **Measured: 0.897 µs and 0.062 µJ per byte.** |
| ASCON-128 fixed cost | Initial permutation over key and nonce, executed on the CPU. **Fitted intercept: 2.9 µJ** (not separately isolated). |
| ASCON-128 per-byte cost | Permutation rounds executed on the CPU. **Measured: 1.180 µs and 0.089 µJ per byte.** |

Renumber it as Table 16, and remove the sentence "Regardless of the payload size, this fixed cost rather than a per-byte one" (it is unfinished in the current draft).
