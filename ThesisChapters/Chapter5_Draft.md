# Chapter 05: Discussion

**Formatting note:** figure/table references below point to Chapter 4 (§4.x). Citations
reuse the existing reference list from Chapters 2–3 (`[Author, Year]`, APA 6th via
Mendeley Cite) — no new sources are introduced. Sentences that report this study's own
interpretation rather than a literature-backed claim are written in plain measured language
(e.g., "this suggests") rather than tagged individually, in line with normal discussion
writing.

---

## 5.1 Restating the Research Question and the Core Finding

This study asked whether software-based ASCON-128 or hardware-accelerated AES-128-GCM was
the more energy-efficient choice for a battery-powered IoT node running a complete
Sleep → Wake → Sense → Encrypt → Transmit → Sleep duty cycle on the ESP32, and under what
conditions that preference held (§1.7).

The results in Chapter 4 show that neither algorithm was more efficient overall — the
answer depended on payload size. ASCON-128 was the more energy-efficient algorithm for
payloads below approximately **347 bytes**, and AES-128-GCM became more efficient above
that point (§4.5.2). This break-even point is the central finding of this thesis, and the
rest of this chapter interprets what produced it, checks it against the existing
literature, and states plainly what it does and does not establish.

## 5.2 Interpreting the Findings

### 5.2.1 Why a break-even point exists at all

The break-even point exists because the two algorithms pay for their computation in
different ways. The regression analysis in §4.7.2 showed that AES-128-GCM carried a fixed
energy cost of 30.14 µJ per operation, roughly double ASCON-128's 15.03 µJ, before a single
byte of payload was processed. This fixed cost is the price of preparing the ESP32's
hardware AES engine — enabling its clock and loading the key and authentication subkey
into dedicated registers — a step ASCON-128 does not need, since its "setup" is simply the
CPU running the same sponge permutation it uses for the rest of the algorithm.

Once running, however, AES-128-GCM added energy more slowly per additional byte than
ASCON-128 did (0.0335 µJ/byte versus 0.1068 µJ/byte, §4.3.3), because its hardware engine
processes each subsequent block in dedicated silicon rather than executing it on the
general-purpose CPU. So AES-128-GCM starts more expensive but grows cheaper, while
ASCON-128 starts cheaper but grows more expensive — and the two lines cross at
approximately 347 bytes. This structure is consistent with the general pattern reported for
hardware cryptographic accelerators, which typically introduce a fixed set-up cost in
exchange for a lower marginal cost once running [Faisal Abdullah Althobaiti, 2025].

**The physical origin of the two cost structures.** The reason the two algorithms differ in
this way traces back to what each one has to do before it can encrypt a single byte, and
how it processes each byte after that.

- *AES-128-GCM's fixed cost* comes from preparing a hardware peripheral. Before the ESP32's
  AES engine can be used, the driver must switch on the peripheral's clock, expand the
  128-bit key into the full set of round keys and write them into the engine's dedicated key
  registers, and — because GCM also needs to authenticate the ciphertext, not just encrypt
  it — separately compute the GHASH subkey `H` by encrypting an all-zero block and load that
  into the engine as well. All of this happens once per operation, regardless of whether the
  payload is 16 bytes or 1,600 bytes, which is exactly why it shows up as a fixed cost rather
  than a per-byte one.

- *AES-128-GCM's low marginal cost*, once that setup is done, comes from the fact that each
  subsequent 16-byte block is processed by dedicated silicon: the substitution, permutation,
  and mixing steps of each AES round happen in purpose-built hardware logic in parallel,
  rather than as a sequence of general-purpose CPU instructions. This is inherently cheaper
  per byte than doing the equivalent work in software.

- *ASCON-128's low fixed cost* comes from having no separate hardware hand-off to perform at
  all. Its "setup" is the sponge construction's initial permutation over the key and nonce —
  a software operation that runs on the same general-purpose CPU path as the rest of the
  algorithm, with no clock-enabling or register-loading step of its own.

- *ASCON-128's higher marginal cost* comes from the same reason its setup was cheap: every
  block, not just the first, is processed by the CPU executing bitwise rotations, XORs, and
  additions on a 320-bit state held in software, rather than by dedicated encryption
  circuitry. Each additional byte therefore costs more energy than the equivalent byte does
  under AES-128-GCM's hardware path.

In short, AES-128-GCM trades a larger one-time hardware "boot-up" cost for a cheaper
per-byte hardware execution cost, while ASCON-128 avoids that boot-up cost entirely but pays
for every byte using slower, more energy-hungry general-purpose CPU cycles. The break-even
point is simply the payload size at which the energy saved by AES-128-GCM's cheaper
per-byte hardware processing has caught up with, and overtaken, the energy it spent getting
that hardware ready in the first place.

**Why a fixed cost and a marginal cost produce a crossing point at all.** Energy per
operation splits into a one-time *fixed* cost plus a *variable* cost paid per byte:

```
Energy per byte = (Fixed cost ÷ payload size) + Variable cost per byte
```

As payload size grows, the fixed-cost term is divided across more bytes and shrinks toward
zero ("amortized"). So at small payloads the fixed-cost term dominates, favoring whichever
algorithm has the smaller fixed cost (ASCON-128: 15.03 µJ vs. AES-128-GCM: 30.14 µJ,
§4.7.2). At large payloads the fixed-cost term becomes negligible for both, so the result is
decided by the variable cost instead, favoring whichever is smaller there (AES-128-GCM:
0.0335 µJ/byte vs. ASCON-128: 0.1068 µJ/byte). Since each algorithm wins on a different
term, there must be some payload size in between where the two are exactly equal — the
break-even point is a mathematical consequence of this trade-off, not a coincidence of this
dataset.

This is visible directly in the measured data (Table 4.3): at 16 bytes ASCON-128 used 1.742
µJ/byte against AES-128-GCM's 2.633 (ASCON cheaper, fixed cost still dominant); by 1,600
bytes ASCON-128 used 0.108 µJ/byte against AES-128-GCM's 0.095 (AES cheaper, variable cost
now dominant). The gap narrows steadily and flips sign between 336 and 352 bytes,
interpolated in §4.5.2 to ≈347 bytes.

Solving the equation algebraically from Table 4.2's regression constants gives ≈206 bytes —
noticeably lower than the measured 347. This gap is expected, not a contradiction: the
energy regressions were far noisier than the time regression (R² of 0.91 and 0.43, versus
>0.9999 for time), so the straight-line fit tracks the true curve less tightly. §4.5.2's
347-byte figure, taken from the actual measured values rather than the noisier regression
line, is the more reliable of the two.

### 5.2.2 Why the algorithm choice matters less at very small payloads

A less obvious result is that the sleep phase, not the encryption itself, dominated total
energy at small payload sizes. The fixed sleep-phase term (990 µJ per cycle, §4.2.4) was
the same for both algorithms, and at the smallest tested payload (16 bytes) it made up the
overwhelming majority of the 63–65 µJ/byte total duty-cycle cost (§4.5.1). In other words,
at small, LPWAN-typical payload sizes, which algorithm was used mattered comparatively
little to total energy — the active-phase energy only became a meaningful share of the
total, and therefore only became worth optimizing, once payload size grew large enough.
This is a practical qualification on Objective 2 that would not have been visible from
active-phase energy alone, and it reinforces the value of measuring the complete duty
cycle rather than the encryption step in isolation, consistent with the gap identified in
§2.5's review of duty-cycle-aware energy studies [Nkemeni et al., 2023].

### 5.2.3 An unexpected result: execution time told a different story than energy

One result did not follow the same pattern as the rest and is worth addressing directly.
The per-size significance testing in §4.7.1 found that power and energy differed
significantly between the two algorithms at 78% and 72% of tested payload sizes
respectively, but execution time differed significantly at only 21% of sizes. If
AES-128-GCM's hardware engine were simply "faster," a similarly high proportion would be
expected for execution time as well.

The most plausible explanation is that the two algorithms' execution times genuinely
converge across much of the payload range — their regression slopes were close enough
(1.197 µs/byte for ASCON-128, 0.901 µs/byte for AES-128-GCM, §4.3.3) that the hardware
engine's advantage shows up mainly in *how much energy* each cycle takes, not in *how long*
it takes. This matters for interpretation: the energy-efficiency differences reported in
this thesis are best understood as a difference in power draw between a CPU-bound software
path and a hardware-offloaded path, rather than a difference in raw computational speed.

## 5.3 Comparison with Existing Literature

Chapter 2 (§2.3.4, §2.7) identified an apparent conflict in the literature: some studies
reported ASCON as more efficient than AES, while others reported hardware-accelerated AES
as more efficient, with no study directly comparing the two on the same platform. Closer
reading showed this was not really a conflict — the two groups of studies had answered
different questions. Studies favoring ASCON, such as [Ridho Rabbani, 2025] and
[Tripathi et al., 2024], compared it against *software-emulated* AES. Studies favoring
hardware AES, such as [Rafat et al., 2025] and [Hung & Hsu, 2018], compared hardware AES
against that same software AES baseline — never against ASCON.

The 347-byte break-even point identified in this study reconciles that gap directly: both
groups of findings were correct within the scope of what they measured. ASCON-128 is the
more efficient choice at the small payload sizes typical of the LPWAN traffic the
ASCON-favoring studies focused on, and hardware-accelerated AES-128-GCM is the more
efficient choice once payload size grows past the point where its fixed setup cost is
recovered — a distinction the hardware-AES studies could not have made, since they never
tested ASCON.

Beyond this reconciliation, the results agreed with the literature in two further respects.
ASCON-128's execution time scaled almost perfectly linearly with payload size
(R² = 0.9999997, §4.3.3), matching its documented sponge-based structure, in which every
block costs the same fixed number of CPU cycles [Ridho Rabbani, 2025]. And AES-128-GCM's
growing advantage at larger payloads matched the documented behaviour of dedicated hardware
engines maintaining stable, low-latency performance under load [Rafat et al., 2025].

The study also extended two specific gaps named in prior work. [Jin & Becker, 2022], whose
benchmarking structure this study's experimental design was built on, measured only
execution time and throughput, with no power measurement, energy analysis, or significance
testing. This thesis added all three. Separately, [Amirkhanova et al., 2026] explicitly
named the absence of energy/CPU measurement and payload-size variation as limitations of
their own AES-GCM/ESP32 pipeline; the per-byte energy analysis across 100 payload sizes in
§4.5 answers both gaps directly.

One further comparison could not be fully verified. [Al-Shmailawi et al., 2026] reported an
unconditional ASCON advantage in cycles-per-byte on an ESP32-S2, but did not state whether
the ESP32-S2's hardware AES engine was actually invoked for their AES baseline — a
configuration detail the literature has flagged as easy to get wrong [Ridho Rabbani, 2025].
This study's own AES-128-GCM figures are reported alongside an explicitly confirmed
hardware-acceleration configuration (§3.4.2), so this ambiguity does not affect the
comparison drawn in this chapter, but it means the two studies' AES baselines cannot be
directly equated.

Finally, the memory footprint result (AES-128-GCM using approximately 24% more RAM than
ASCON-128, §4.6) is a new comparison rather than a confirmation of an existing one — no
study reviewed in Chapter 2 compared the memory footprint of hardware-accelerated AES
against a software AEAD cipher on the same platform. The direction of the gap is consistent
with what each library must keep in memory: mbedTLS's AES-GCM context holds both the
expanded AES key schedule and a precomputed GHASH table, while ASCON-128 only needs to keep
its sponge state resident.

## 5.4 Limitations

The findings above should be read with the following constraints in mind. None of them are
expected to change the direction of the break-even result, for the reasons given below, but
they do bound how far the results can be generalized.

- **Single test board.** All measurements were taken on one ESP32-WROOM-32E unit. This
  limits how confidently the *absolute* figures generalize across other units (e.g., due to
  silicon variation in the hardware AES engine), but does not affect the ASCON-vs-AES
  comparison itself, since both algorithms were measured on the same board under the same
  conditions.

- **Sensor resolution.** The INA219 power sensor's 12-bit ADC sets a floor on the smallest
  power difference it can resolve. This affects confidence in the very smallest measured
  values, but the differences that drove the break-even result were well above this floor.

- **Sleep-phase energy was estimated, not measured.** The firmware only instrumented the
  active encryption phase; the 990 µJ sleep-phase term was calculated analytically from a
  datasheet current figure and a fixed 60-second interval (§4.2.4), rather than measured on
  the device. Because this term is identical for both algorithms at every payload size, it
  could not have shifted the break-even point — but it does mean the total duty-cycle
  energy figures should be read as "measured active-phase energy plus a datasheet-derived
  sleep estimate," not as a fully empirical end-to-end measurement. For the same reason,
  this study cannot speak to duty cycles using a sleep interval other than 60 seconds.

- **Transmission-phase noise.** The duty cycle's Wi-Fi/MQTT transmission step introduces
  variable-latency network activity outside the encryption operation itself. This is a
  plausible contributor to residual variance in the power measurements, though it should
  not have affected the execution-time measurement, which isolated only the encryption
  call.

- **Wake-up transient not isolated.** The brief power spike as Wi-Fi and the oscillator
  re-initialize after deep sleep — reported elsewhere as roughly 22 µJ over 2.1 ms
  [Nkemeni et al., 2023] — was not separately measured here. As with the sleep-phase
  estimate, this cost would apply equally to both algorithms and is not expected to bias the
  comparison, but it is a further respect in which the total energy figures are a
  supplemented estimate rather than a fully measured total.

- **Scope of the efficiency metric.** "Energy per byte over one duty cycle" was used as the
  practical proxy for battery-life impact. It does not capture battery chemistry and
  discharge-curve effects, cumulative thermal effects, or RF-environment drift over a real
  deployment's lifetime. These were reasonable exclusions for a controlled laboratory
  comparison, but a field deployment (proposed in Chapter 6) would be needed to confirm the
  break-even point holds under those additional factors.

## 5.5 Implications and Future Work

For IoT system designers, the practical implication is straightforward: the choice between
software ASCON and hardware-accelerated AES-GCM on the ESP32 should be based on the typical
payload size the device will send, not on a general assumption that one algorithm is always
better. Devices sending small, infrequent payloads — narrow-band sensor readings, for
example — are better served by ASCON-128, while devices sending larger payloads, such as
batched telemetry or firmware updates, are better served by hardware-accelerated
AES-128-GCM.

Academically, this result reconciles a gap the literature had not previously closed: prior
studies had compared ASCON against software AES, or hardware AES against software AES, but
not ASCON against hardware AES directly. This thesis provides that missing data point,
together with a specific numeric condition — the 347-byte break-even payload — rather than
a general claim that one algorithm is superior.

Future work should address the limitations above directly: measuring the sleep and wake-up
phases empirically rather than analytically, repeating the comparison across multiple
physical boards to test whether the break-even point is stable across manufacturing
variance, and validating the result in a field deployment across a range of real sleep
intervals and RF conditions. It would also be useful to test whether the same break-even
pattern holds for other hardware-accelerated ciphers and other lightweight AEAD candidates
beyond ASCON-128.

## 5.6 Summary of Chapter 5

This chapter interpreted the Chapter 4 results as answering the research question with a
break-even payload size of approximately 347 bytes, below which software ASCON-128 is more
energy-efficient and above which hardware-accelerated AES-128-GCM is more energy-efficient.
This result was explained by the two algorithms' different cost structures — a high
fixed/low marginal cost for hardware AES versus a low fixed/high marginal cost for software
ASCON — and was shown to reconcile an apparent conflict in the existing literature rather
than contradict it. The chapter also addressed an unexpected result (execution time
differing far less often than power or energy) and set out the limitations that bound, but
do not overturn, the central finding. Chapter 6 draws these findings together into a final
assessment of the study's contribution and its directions for future research.
