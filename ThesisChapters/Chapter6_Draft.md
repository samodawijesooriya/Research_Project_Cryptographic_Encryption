# Chapter 06: Conclusions and Future Work

**Formatting note:** as with Chapters 4–5, section numbering is placeholder for review.
Citations reused from the existing Chapter 2/3 reference list only; no new sources
introduced.

---

## 6.1 Introduction

This chapter closed the thesis by stating, objective by objective, whether the research
described in Chapters 3–5 achieved what §1.8 set out to do (§6.2); synthesizing those
findings into a single answer to the central research question posed in §1.7 (§6.3);
offering an honest appraisal of the research as a piece of work, not only its results
(§6.4); restating the study's limitations in a form aimed forward, at what a following
student should address (§6.5); stating this thesis's specific contribution to the
literature gap identified in §2.7 (§6.6); and proposing concrete, actionable future work
(§6.7).

## 6.2 Achievement of Research Objectives

### 6.2.1 Objective 1 — Power Consumption, Total Duty-Cycle Energy, and Per-Byte Efficiency, Including Hardware Initialization Overhead

**Verdict: fully met.** Objective 1 required comparing power consumption and per-byte
energy efficiency between ASCON-128 and AES-128-GCM, explicitly including the
initialization overhead of the hardware engine. §4.4 reported power consumption across the
full 16–1,600 byte payload range for both algorithms; §4.7.2 isolated the hardware engine's
initialization overhead directly, as the 30.14 µJ AES-128-GCM energy-regression intercept
against ASCON-128's 15.03 µJ — a specific, quantified figure rather than a qualitative
statement that such overhead exists. §5.2.1 interpreted this figure against the literature's
general 50–80% hardware-efficiency claim [Faisal Abdullah Althobaiti, 2025] and found the
present results consistent with, and more granular than, that general claim. This objective
was met in full: the initialization overhead was not only measured but shown to be the
specific mechanism explaining why AES-128-GCM's relative efficiency depended on payload
size.

### 6.2.2 Objective 2 — Energy Cost Per Transmitted Byte Across the Full Duty Cycle

**Verdict: fully met, with one stated qualification.** Objective 2 required measuring
energy cost per transmitted byte across the complete Sleep → Wake → Sense → Encrypt →
Transmit → Sleep cycle. §4.5.1 reported this figure for both algorithms across all 100
tested payload sizes, and §5.2.2 showed that the relationship between the fixed sleep-phase
term and the payload-scaling active-phase term determined how much the algorithm choice
actually mattered at a given payload size — a finding that would not have been visible from
active-phase energy alone, and that directly fulfilled Objective 2's requirement to measure
across the *full* duty cycle rather than the encryption operation in isolation. The stated
qualification, carried forward from §5.5 and §5.6, is that the sleep-phase contribution to
this total was computed analytically from a cited datasheet figure rather than measured
empirically on the test unit; because this term was shown to be identical across both
algorithms at every payload size, it did not compromise the *comparative* validity of the
per-byte result, but it means the objective was met via a hybrid empirical/analytical
method rather than a fully empirical one.

### 6.2.3 Objective 3 — Break-Even Payload Size and Conditions Favoring ASCON-128

**Verdict: fully met.** Objective 3 required determining the conditions — including a
break-even payload size — under which software-based ASCON-128 remained preferable to
hardware-accelerated AES-128-GCM. §4.5.2 identified this break-even point at approximately
347 bytes, using linear interpolation between the two bracketing measured payload sizes;
§4.5.3 confirmed the result via independent regime segmentation into small
(<256 B, LPWAN-typical) and large (>800 B, bulk-telemetry-typical) payload categories, with
ASCON-128 preferable in the former and AES-128-GCM preferable in the latter. §5.2.3 showed
that this specific numeric result was not only an answer to Objective 3 in isolation, but
the reconciling data point for the broader literature conflict identified in §2.3.4 between
studies favoring ASCON and studies favoring hardware AES — an outcome that exceeded the
objective's literal requirement (a break-even point) by also explaining *why* the prior
literature appeared to disagree.

## 6.3 Answer to the Central Research Question

The research question posed in §1.7 asked how hardware-accelerated AES-128-GCM compared
with software-based ASCON-128 on the ESP32 in terms of power consumption, memory usage,
throughput, execution time, and per-byte energy efficiency, evaluated across a full IoT
duty cycle. The answer this thesis provided is that neither algorithm was unconditionally
superior: AES-128-GCM's hardware acceleration carried a larger fixed per-operation energy
and memory cost (§4.6, §4.7.2) but a lower marginal cost per additional byte once that fixed
cost was paid, while ASCON-128's software implementation carried a lower fixed cost but a
higher marginal cost per byte. The two curves crossed at approximately 347 bytes of
payload (§4.5.2): below this size, software-based ASCON-128 was the more energy-efficient
choice for a full IoT duty cycle on the ESP32; above it, hardware-accelerated AES-128-GCM
was more efficient. This means the ESP32's built-in cryptographic accelerator did provide a
more energy-efficient security solution than software-based lightweight cryptography, but
only conditionally — specifically, for payloads larger than the identified break-even
point — rather than universally, as a simple "hardware is always faster" framing would
suggest.

## 6.4 Critical Appraisal of the Research

Considered as a piece of research rather than only as a set of results, this study
established its central finding — the existence and approximate location of a break-even
payload size between software ASCON-128 and hardware-accelerated AES-128-GCM — with a
reasonably high degree of confidence. The break-even point was identified from a clean sign
change in the per-byte energy difference (§4.5.2), corroborated independently by the regime
segmentation (§4.5.3), and shown to be robust to the analytical sleep-energy substitution
(§5.5) on algebraic grounds rather than assumption. The statistical testing in §4.7.1
further showed that the power and energy differences underlying this result were
significant at the large majority of tested payload sizes, not merely at the two sizes
bracketing the crossover itself.

What this study establishes with less confidence is the *generalizability* of the specific
347-byte figure — to other physical ESP32 units, to other sleep-interval configurations, and
to other AEAD algorithm pairs — since, per §5.6, all measurements were taken on a single
test unit under a single fixed (analytically substituted) sleep duration. The study should
therefore be read as establishing, with confidence, that a break-even point of this kind
exists and lies in the low-hundreds-of-bytes range for this specific algorithm pair and
platform, while the future-work items in §6.7 are precisely those needed to test how far the
specific figure generalizes.

On the question of whether the experimental design was proportionate to the question asked:
the 100-payload-size, 500-plus-iteration, full-duty-cycle design (§3.3.1) was substantial
relative to a study whose central finding ultimately reduced to a single crossover point.
This was, on balance, an appropriate degree of rigor rather than over-engineering: the
break-even point could only be located precisely, and distinguished from measurement noise
(as the 528–560 byte "wobble" was distinguished from a genuine second crossover in §4.5.2),
because the payload range was sampled finely enough and each point was measured with enough
repetition to produce statistically stable per-size means. A coarser design — fewer payload
levels, fewer repeats — would likely have still suggested that a crossover existed
somewhere, but could not have located it to within roughly 16 bytes of resolution or
distinguished a genuine second regime change from noise with the same confidence.

## 6.5 Limitations of the Study

The five limitations identified diagnostically in §5.6 are restated here prospectively —
framed as constraints a following student could remove, each one paired with the specific
future-work item in §6.7 designed to address it.

- **Single physical test unit** (ESP32-WROOM-32E, one board). A following study could not,
  from this thesis alone, distinguish a genuine platform-level effect from unit-to-unit
  manufacturing variance. *Addressed by §6.7, item 1.*
- **INA219 measurement resolution** (12-bit ADC). The sensor used in this study could not
  resolve power deltas below its ADC's precision floor, which is a hard limit on how small
  a crossover-relevant difference this specific test-bed could ever have detected.
  *Addressed by §6.7, item 4.*
- **Fixed 60-second sleep window, applied only analytically.** The claim that the
  break-even point is sleep-duration-invariant was demonstrated algebraically (§4.5.1,
  §5.2.2) but never tested empirically against a second sleep duration. *Addressed by §6.7,
  item 3.*
- **Datasheet-derived, rather than measured, sleep current.** The absolute total
  duty-cycle energy figures depend on the accuracy of a manufacturer-published typical
  current figure for this study's exact test unit, rather than a direct measurement.
  *Addressed by §6.7, item 2.*
- **Wi-Fi/MQTT transmission-phase noise, and the unmeasured wake-up transient.** Both the
  variable latency of the transmission phase and the brief wake-up/reconnection power
  spike (reported elsewhere at approximately 22 µJ over 2.1 ms [Nkemeni et al., 2023]) were
  outside what this study's measurement design isolated. *Addressed by §6.7, item 5 and
  item 2 respectively.*

## 6.6 Contribution to Knowledge

§2.7 identified a specific, named gap in the literature: no reviewed study had performed a
direct, head-to-head comparison between software-based ASCON-128 and hardware-accelerated
AES-128-GCM under identical, realistic IoT duty-cycle conditions using a uniform
energy-per-byte metric [Ridho Rabbani, 2025]. This thesis is presented as closing that
specific gap. It did so by placing both algorithms on the same physical platform, under an
identical experimental pipeline (§4.2), evaluated across a full duty cycle rather than an
isolated encryption operation (§3.3.1), using a single uniform metric — per-byte energy
across 100 payload levels — that neither the ASCON-favoring nor the AES-favoring branch of
the prior literature had used against the other directly (§5.2.3, §5.3). The specific,
numeric break-even payload size (≈347 bytes) identified in §4.5.2 is the concrete output of
that closure: it is offered as a new, citable data point that reconciles why the prior
literature appeared divided, rather than as a refutation of either branch of it.

## 6.7 Recommendations for Future Work

Each item below corresponds directly to a limitation named in §6.5.

1. **Multi-unit replication.** Repeat the full measurement pipeline (§3.3, §4.2) across
   multiple (n > 1) physical ESP32-WROOM-32E boards to quantify unit-to-unit variance in
   the crossover point itself, establishing whether ≈347 bytes is a platform-level
   constant or subject to meaningful per-unit variation.
2. **Empirical measurement of the wake-up/reconnection transient and the sleep-phase
   current**, using the INA219 sensor already integrated into this test-bed, rather than
   substituting a datasheet steady-state figure (§4.2.4). This would convert the total
   duty-cycle energy figures in §4.5.1 from a hybrid empirical/analytical estimate into a
   fully empirical, end-to-end measurement, and would additionally allow the
   wake-up transient (unmeasured in this study, §5.6) to be captured directly.
3. **Repeat the duty cycle at multiple fixed sleep durations** (e.g., 10 s, 300 s, 3,600 s,
   in addition to the 60 s design value used here), to empirically test the prediction —
   demonstrated only algebraically in this thesis (§4.5.1, §5.2.2) — that the break-even
   payload size is invariant to the chosen sleep duration.
4. **Repeat the power measurements with a higher-resolution or multi-range current sensor**
   (e.g., a sensor offering finer ADC resolution at low currents, or a dual-range shunt
   configuration) to establish how close the current INA219-based measurements came to
   their resolution floor, and whether a finer-grained sensor would shift the identified
   break-even point.
5. **Isolate cryptographic energy cost from transmission-phase noise**, either by repeating
   the experiment over a wired Ethernet connection instead of Wi-Fi/MQTT, or by logging
   per-trial RF diagnostics (signal strength, retry counts) alongside the existing power and
   timing data, to quantify how much of the residual variance noted in §4.7.1 (particularly
   the comparatively low 21% significance rate for execution time) was attributable to
   network conditions rather than to the cryptographic operations themselves.
6. **Extend the comparison to other NIST lightweight cryptography finalists and other
   hardware-accelerated AEAD engines** (for example, ChaCha20-Poly1305, which some
   platforms accelerate in hardware) to test whether a break-even relationship of the kind
   identified in this thesis is a general feature of software-lightweight-versus-
   hardware-legacy cryptography comparisons, or specific to the ASCON-128/AES-128-GCM pair
   studied here.
7. **Conduct a real battery-drain field trial**, discharging a coin-cell or small Li-ion
   battery over multiple weeks under each algorithm's duty cycle, to validate the per-byte
   energy model developed in this thesis against actual measured device lifetime — directly
   addressing the construct-validity boundary noted in §5.5, where this thesis's per-byte
   energy metric was adopted as a proxy for practical battery-life impact rather than
   validated against it directly.

## 6.8 Closing Remarks

This thesis set out to resolve a specific, named gap in the IoT security literature: the
absence of a direct, same-platform comparison between software-based lightweight
cryptography and hardware-accelerated legacy cryptography, evaluated under a realistic,
full IoT duty cycle and a uniform energy-per-byte metric. Across 561 complete measurement
iterations for ASCON-128 and 510 for AES-128-GCM, spanning 100 payload sizes from 16 to
1,600 bytes, cleaned and calibrated through an identical, auditable pipeline (Chapter 4)
and interpreted against both the research objectives and the existing literature (Chapter
5), this thesis found that neither algorithm was unconditionally more energy-efficient: the
two approaches crossed over at approximately 347 bytes of payload, with software-based
ASCON-128 preferable below that point and hardware-accelerated AES-128-GCM preferable
above it. This finding, together with the specific mechanisms shown to drive it — the
hardware engine's fixed initialization overhead against its lower marginal per-byte cost —
is offered as this thesis's contribution toward a more precise, evidence-based basis for
choosing between software and hardware cryptography in energy-constrained IoT deployments.
