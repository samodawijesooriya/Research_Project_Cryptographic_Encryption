# Chapter 05: Discussion and Critical Evaluation

**Formatting note:** as with Chapter 4, figure/table numbering below is placeholder
(§5.x-style) for review purposes — align with Word's automatic numbering when pasting in.
All citations below are reused directly from Chapter 2/3's existing reference list (the
`[Author, Year]` bracket form, Mendeley Cite/APA 6th) — none are new. Where I make a claim
that isn't directly supported by an existing citation, I've marked it **[NEW CLAIM — no
citation, this study's own finding]** so you can see exactly which sentences are original
synthesis versus literature-backed. The [Jin & Becker, 2022] and [Amirkhanova et al.,
2026] comparisons in §5.3 were checked directly against the two source PDFs in
`Findings/` (not inferred from Chapter 2/3's summary of them), so the specific
methodological contrasts drawn there — e.g., that Jin & Becker's own analysis had no
power measurement, regression, or hypothesis testing, and that Amirkhanova et al. named
energy/CPU quantification and payload-size variation as their own unaddressed
limitations — are traceable to those papers' Methods/Results and Discussion/Limitations
sections respectively.

---

## 5.1 Introduction

This chapter interpreted the results presented in Chapter 4 against the research question
and three objectives stated in §1.7–1.8, and situated them within the body of literature
reviewed in Chapter 2. The chapter was organized in four parts: an objective-by-objective
interpretation of the findings (§5.2); a comparison of these findings with the existing
literature, including a direct reconciliation of the literature conflict identified in
§2.3.4 (§5.3); an explicit assessment of the reliability of the data and data collection
process (§5.4) and the validity of the evaluation approach (§5.5), both required to
establish that the numbers reported in Chapter 4 could bear the interpretive weight placed
on them; and a critical self-evaluation of the study's limitations (§5.6), stating plainly
what each limitation did and did not bound about the conclusions drawn.

## 5.2 Interpretation of Findings Against the Research Objectives

### 5.2.1 Objective 1 — Total Duty-Cycle Energy and Hardware Initialization Overhead

Objective 1 required comparing the total duty-cycle energy and per-byte energy efficiency
of ASCON-128 against AES-128-GCM, including the initialization overhead of the hardware
engine. The regression analysis in §4.7.2 provided direct evidence for this overhead: the
energy-versus-payload-size regression intercept was 30.14 µJ for AES-128-GCM against 15.03
µJ for ASCON-128 — that is, before a single byte of payload was accounted for,
AES-128-GCM's hardware-accelerated path carried a fixed energy cost roughly double that of
ASCON-128's software path. This is consistent with the literature's general observation
that dedicated hardware cryptographic engines, while efficient once running, introduce a
comparatively rigid, front-loaded cost structure rather than a purely linear one
[Faisal Abdullah Althobaiti, 2025]. Hardware accelerators of this kind have been reported
to reduce cryptographic energy consumption per operation by 50% to 80% relative to
software-only implementations once amortized across sufficient payload [Faisal Abdullah
Althobaiti, 2025], and the results in §4.3.3 and §4.5.1 are consistent with that pattern:
AES-128-GCM's higher fixed cost was progressively offset as payload size increased, to the
point of becoming the more energy-efficient algorithm beyond the break-even point
identified in §4.5.2.

This finding partially answered Objective 1: the hardware engine's initialization overhead
was successfully isolated and quantified (as the regression intercept gap), but whether
that overhead was "worth paying" depended entirely on payload size — a nuance that a single
aggregate energy figure would have obscured, and which is precisely why Objective 1's
requirement to look at power consumption *and* per-byte efficiency together, rather than
execution time alone, proved necessary.

### 5.2.2 Objective 2 — Energy Cost Per Transmitted Byte Across the Full Duty Cycle

Objective 2 required measuring the energy cost per transmitted byte across the complete
Sleep → Wake → Sense → Encrypt → Transmit → Sleep cycle, not the active encryption phase in
isolation. The total duty-cycle energy-per-byte figures reported in §4.5.1 satisfied this
requirement directly: at the smallest tested payload (16 bytes), the complete duty cycle
cost 63.62 µJ/byte for ASCON-128 versus 64.51 µJ/byte for AES-128-GCM; at the largest
tested payload (1,600 bytes), this had fallen to 0.727 µJ/byte and 0.714 µJ/byte
respectively. The steep decline in per-byte cost as payload size increased — for both
algorithms — reflected the fact that the fixed sleep-phase energy term (990 µJ, §4.2.4) was
amortized over progressively more transmitted bytes, dominating the per-byte figure at
small payloads and becoming comparatively negligible at large ones.

This has a direct practical implication for Objective 2 that would not have been visible
from active-phase energy alone: at small, LPWAN-typical payload sizes, the *sleep-phase*
energy term dominated the total duty-cycle cost for both algorithms almost equally,
meaning the *choice of algorithm* mattered comparatively little to total energy at very
small payloads — it was only once payload size grew large enough for the active-phase
energy to become a meaningful share of the total that the algorithm choice identified in
§4.5.2 began to matter in absolute terms. **[NEW CLAIM — no citation, this study's own
finding]** This observation refines Objective 2's practical interpretation: the per-byte
energy advantage of one algorithm over the other is conditional not just on payload size in
isolation, but on how large the active-phase cost is relative to the fixed sleep-phase
cost for the deployment's chosen sleep interval — a relationship made visible only by
measuring the full duty cycle, which is exactly what §2.5's literature identified as
missing from most prior cryptographic energy benchmarks [Nkemeni et al., 2023].

### 5.2.3 Objective 3 — Break-Even Payload Size and Conditions Favoring ASCON-128

Objective 3 asked under what conditions software-based ASCON-128 remained preferable to
hardware-accelerated AES-128-GCM, including identifying a break-even payload size. §4.5.2
identified this break-even point at approximately 347 bytes, confirmed by the regime
segmentation in §4.5.3: ASCON-128 was the more energy-efficient choice for payloads below
this size (mean advantage of 0.225 µJ/byte in the <256-byte LPWAN-typical regime), and
AES-128-GCM became the more energy-efficient choice above it (mean advantage of 0.065
µJ/byte in the >800-byte bulk-telemetry-typical regime).

This result is best understood as this thesis's central empirical contribution, and it
directly addresses the specific gap identified in Chapter 2. §2.3.4 established that the
existing literature was not actually in disagreement about whether ASCON or hardware AES
was "better" — rather, the two bodies of literature had been answering different questions.
Studies reporting ASCON's superiority, such as the 74% execution-latency advantage over
*software-emulated* AES-128 on identical ESP32 silicon reported by [Ridho Rabbani, 2025],
and the throughput and energy-efficiency advantages over software AES reported across
Arduino-based 32-bit platforms by [Tripathi et al., 2024], benchmarked ASCON exclusively
against software AES. Studies reporting hardware-accelerated AES's superiority, such as the
sub-3-millisecond encryption latency and stable 35–45% CPU utilization reported on the
ESP32 by [Rafat et al., 2025], and the reduced power consumption from hardware-stored AES
matrices reported on ARM Cortex-M3 platforms by [Hung & Hsu, 2018], benchmarked hardware
AES against the same software AES baseline being offloaded to silicon — never against
ASCON. As §2.7 stated explicitly, "the intersection of these two domains — comparing the
new software standard against the legacy hardware standard on the same platform — remains
empirically untested" [Ridho Rabbani, 2025].

The ≈347-byte break-even point identified in this study is the reconciling data point for
that gap. **[NEW CLAIM — no citation, this study's own finding]** It shows that both
literatures were, in effect, correct within the scope of what they measured: ASCON-128
genuinely was the more energy-efficient choice at the small payload sizes typical of the
narrow-band LPWAN traffic these lightweight-cryptography studies most often targeted, while
hardware-accelerated AES-128-GCM genuinely was the more efficient choice once payload size
grew past the point where its fixed hardware-engine overhead was amortized — a regime the
hardware-acceleration literature's benchmarks (which did not test ASCON directly) could not
have distinguished from ASCON's perspective. Objective 3 is therefore answered not with a
single "ASCON is/is not preferable" verdict, but with the specific, numeric condition — the
≈347-byte break-even point — under which the preference reverses.

## 5.3 Comparison with Existing Literature

Two further points of agreement and one further point of refinement, beyond the crossover
reconciliation in §5.2.3, were evident when the Chapter 4 results were checked against
Chapter 2's specific claims.

**Agreement — ASCON's linear scaling behaviour.** §4.3.3 found that ASCON-128's execution
time scaled essentially perfectly linearly with payload size (R² = 0.9999997). This
matched the literature's characterization of ASCON's sponge-duplexing construction as
introducing linear runtime scaling as payload size increases, particularly in the absence
of hardware acceleration [Ridho Rabbani, 2025]. The present results provided direct
empirical confirmation of that claim on the specific hardware platform (ESP32-WROOM-32E)
and specific implementation used in this study, across a wider payload range (16–1,600
bytes, 100 levels) than is typically reported.

**Agreement — hardware AES's advantage at larger payloads.** The reversal in both
execution time (§4.3.1) and power draw (§4.4) favoring AES-128-GCM at larger payload sizes
was consistent with the literature's account of the ESP32's dedicated AES hardware engine
offloading computation from the CPU into specialized silicon, maintaining stable CPU
utilization and low latency regardless of load [Rafat et al., 2025], and with the broader
finding that AES's energy and latency penalties are substantially neutralized once
offloaded to dedicated hardware accelerators [Hung & Hsu, 2018].

**Extension — statistical and energy analysis absent from the source benchmarking
design.** The iteration structure underlying §4.2.1 (500-repeat outer loop, 100-payload
inner loop, PRNG-seeded payload generation) was adopted directly from the ESP32
benchmarking methodology of [Jin & Becker, 2022]. However, that study's own analysis
was limited to descriptive statistics — mean, minimum, and maximum execution time and
throughput, presented as line graphs and bar charts — and did not measure power or
energy at all, nor did it apply any hypothesis test or regression analysis to establish
whether observed differences between configurations were statistically meaningful. This
thesis extended that design in three respects that materially changed what could be
concluded from it: the INA219-based power instrumentation (§4.2.2) added the energy
dimension entirely absent from the source study; the per-size Welch's t-tests (§4.7.1)
replaced descriptive-only min/max reporting with a formal significance criterion; and the
linear regression analysis (§4.3.3, §4.7.2) quantified the scaling behaviour rather than
only plotting it. None of these three additions exist in the benchmarking approach this
study's experimental design was otherwise built on.

**Extension — directly answering a named limitation in prior end-to-end pipeline
literature.** [Amirkhanova et al., 2026], whose AES-GCM/ESP32/MQTT pipeline this
study's algorithm selection and duty-cycle framing also drew on (§3.1.1, §3.2), explicitly
identified in their own study's limitations that "future work should... incorporate energy
or CPU utilization measurements to strengthen cross-paper comparability" and that their
benchmark was constrained to "a single sustained message rate" without testing
"different payload sizes." This thesis's per-byte energy analysis across 100 payload sizes
(§4.5) is a direct, targeted response to both gaps as that source study itself named them —
not merely a generic extension of unrelated prior work, but an explicit answer to a
limitation its own authors flagged as unaddressed.

**Contrast — a cycle-per-byte comparison that does not specify hardware-acceleration
status.** [Al-Shmailawi et al., 2026], already cited in §2.4.1 for the metrics-fragmentation
problem in LWC benchmarking, reported ASCON-128 requiring 234 CPU cycles per byte
against AES-128's 959 cycles per byte on an ESP32-S2, with a correspondingly large gap
in initialization time (65 µs vs. 486 µs) — an unconditional efficiency advantage for
ASCON, not a payload-size-dependent one. The paper's Implementation section (§III) does
not state whether the ESP32-S2's hardware AES engine was explicitly invoked for the
AES-GCM baseline or whether mbedTLS defaulted to software emulation; per the
literature's own documented risk that hardware peripherals are not always invoked
automatically [Ridho Rabbani, 2025] (§2.3.3), this is left as an open question about that
study's baseline configuration rather than a claim this thesis can verify. **[NEW CLAIM —
no citation, this study's own finding]** What can be said is that this thesis's own AES-GCM
figures (§4.7.2, regression intercept of 30.14 µJ) are explicitly reported alongside the exact
hardware/software configuration and library version used (§3.4.2, ESP-IDF mbedTLS
hardware AES acceleration explicitly enabled), so that the ambiguity present in
cross-paper cycle-count comparisons like [Al-Shmailawi et al., 2026]'s does not apply to
the comparison drawn in this chapter.

**Refinement — memory footprint as a genuinely new comparison.** §4.6 found AES-128-GCM's
mean memory footprint to be approximately 24% higher than ASCON-128's, attributed to the
mbedTLS library's cryptographic context structures carrying a fixed overhead independent of
payload size. **[NEW CLAIM — no citation, this study's own finding]** While the general
principle that software cryptographic libraries carry RAM overhead is established in the
literature reviewed in §2.3.1, no source reviewed in Chapter 2 specifically compared the
memory footprint of a hardware-accelerated AES-GCM implementation against a purely
software-based lightweight AEAD cipher such as ASCON-128 on the same platform; this
specific comparison, like the crossover result in §5.2.3, is a new data point this study
contributes rather than a confirmation of a prior specific claim.

## 5.4 Reliability of the Data and Data Collection Process

The reliability of the results reported in Chapter 4 rested on the cleaning and calibration
pipeline described in §4.2, and this section synthesizes why that pipeline constitutes a
defensible, auditable basis for the comparison rather than restating its mechanics.

Three design decisions, taken together, formed the reliability chain. First,
iteration-level structural cleaning (§4.2.1) rather than deduplication by trial `id` alone
recognized that the logging counter was not a reliable proxy for the firmware's actual
outer-loop structure — using the payload-size sequence itself to detect sweep boundaries
matched the unit of cleaning to the unit the experiment was actually designed around
(§3.3.1). Second, the INA219 zero-offset calibration (§4.2.2) treated the systematic
negative-current cluster as a correctable, quantifiable sensor bias rather than either
ignoring it or discarding it through blind clipping — a distinction the literature has
identified as a live methodological concern, since many existing measurement tools are
reported to suffer from limited current ranges or low accuracy when capturing the rapid
power spikes characteristic of cryptographic and wireless-transmission bursts [Dezfouli et
al., 2018]. Third, outlier trimming (§4.2.3) was deliberately sequenced *after* the
structural and calibration corrections, so that it targeted genuine per-trial measurement
noise rather than misclassifying partial-sweep artifacts or systematic sensor bias as
statistical outliers.

This pipeline extended, rather than simply followed, the measurement lineage established by
[Mitchel et al., 2025], whose micros()-based timing methodology (§3.5.1) and use of SciPy
for statistical evaluation and raw-log cleaning (§3.7.1) this study adopted directly. Where
this study went further was in adding an explicit, quantified sensor-calibration procedure
(§4.2.2) — a step not present in the methodology this thesis otherwise built on — which was
necessary because the INA219 current readings exhibited a systematic offset that a
purely statistical cleaning pass (removing outliers, computing means) would not have
corrected, since the offset was assured a consistent bias rather than random noise.

Critically, because the same three-stage pipeline and the same two calibration constants
(5.70 mA offset, 4.674 V measured bus voltage) were applied identically to both the
ASCON-128 and AES-128-GCM datasets (§4.2.2), any residual noise that the pipeline did not
fully eliminate — for example, variance introduced by the Wi-Fi/MQTT transmission phase
during the duty cycle's reporting step (§3.3.4) — was present in both datasets under the
same conditions. This does not eliminate that noise from either individual dataset, but it
substantially contains its effect on the *comparison* between the two algorithms, which is
the quantity the research question in §1.7 actually asked about.

## 5.5 Validity of the Evaluation Approach

This section addressed directly whether the experimental design described in Chapter 3 —
100 payload sizes from 16 to 1,600 bytes, 561 (ASCON-128) and 510 (AES-128-GCM) complete
duty-cycle iterations, and a full Sleep → Wake → Sense → Encrypt → Transmit → Sleep cycle —
actually measured what the research question in §1.7 asked, rather than merely producing
numbers that resembled an answer.

Three features of the design supported its validity for this purpose. First, per-byte
normalization (§4.5.1) removed payload size as a confounding variable from the
energy-efficiency comparison, which was necessary because the two algorithms' relative
efficiency was shown in §4.5.2 to reverse across the tested payload range — a single
aggregate energy figure, of the kind Chapter 2 identified as common in fragmented existing
benchmarking practice [Ibrahim et al., 2025; Beaulieu et al., 2013], would have concealed
exactly the break-even behaviour that answers Objective 3. Second, the controlled-variable
design (§3.2.3) held every experimental factor constant between the two algorithms except
the cryptographic algorithm itself — the same payload generation strategy, the same timing
method, the same duty-cycle structure, and (per §4.2.2) the same calibration constants —
so that differences observed in Chapter 4 could be attributed to the algorithms under test
rather than to inconsistencies in the experimental apparatus. Third, the explicit inclusion
of the hardware engine's initialization overhead in the energy accounting (isolated via the
regression intercept in §4.7.2) meant the design answered Objective 1's requirement
literally, rather than only approximately: the "total duty-cycle energy including hardware
initialization overhead" that Objective 1 asked for was not assumed away or averaged out,
but explicitly measured and reported as a distinct, quantified figure.

This design also directly addressed a gap Chapter 2 identified in prior duty-cycle-aware
energy research: that duty-cycle models frequently omit the transient "start-up energy
cost" of a wake-up event, and that lab-bench benchmarks focused on isolated, continuous
encryption operations therefore fail to capture the true energy landscape of a deployed IoT
node [Nkemeni et al., 2023; Junchao Ma, 2009]. By measuring the complete duty cycle rather
than the encryption operation in isolation — and by extending the methodology of [Jin &
Becker, 2022], which established execution-time and throughput benchmarking on the ESP32
but did not include power consumption or a full duty cycle, and by directly responding to
the limitation identified by [Amirkhanova et al., 2026] that prior end-to-end AES-GCM
pipelines on the ESP32 failed to quantify energy or CPU utilization beyond basic latency —
this study's design was constructed specifically to close that gap for the ASCON-vs-AES
comparison.

This claim of validity is, however, bounded in one specific respect that must be stated
plainly here rather than deferred entirely to §5.6: the sleep phase of the duty cycle was
not itself empirically measured, but substituted analytically from a datasheet figure
(§4.2.4). This means the design measured the complete duty cycle's *active* phases with
high fidelity, but represented the *sleep* phase's contribution with a constant rather than
a measurement. Because that constant was shown algebraically (§4.5.1) to be identical for
both algorithms at every payload size, it cannot have introduced a difference between the
two algorithms — meaning the crossover result in §5.2.3, which is a *comparative* finding,
is not threatened by this substitution. It does mean, however, that this study's construct
validity for the term "total duty-cycle energy" specifically should be read as "active-phase
energy plus an analytically-derived, literature-cited sleep-phase estimate," rather than as
a fully empirical, device-measured total — a distinction developed further as an explicit
limitation in §5.6.

More broadly, "energy per byte over one duty cycle" was adopted in this study as the
operational proxy for "practical usefulness for a battery-powered IoT node," which is what
the research question in §1.7 was ultimately concerned with. This proxy deliberately did
not capture several factors that would affect a real deployment's actual battery life:
battery chemistry and non-linear discharge curves, cumulative thermal effects across
thousands of duty cycles, and drift in RF-environment conditions over the deployment's
lifetime. These were reasonable exclusions for a controlled, comparative laboratory study —
capturing them would have required a different kind of study entirely (a field trial, as
proposed in Chapter 6's future work) — but they mark the boundary of what this thesis's
specific evaluation approach was designed to establish.

## 5.6 Critical Self-Evaluation

This section stated, for each limitation of the study, what it specifically bounded about
the conclusions drawn in this chapter, and — equally importantly — what it did not bound.

**Single physical test unit.** All measurements were taken on a single ESP32-WROOM-32E
development board. This bounds the extent to which the absolute figures reported in Chapter
4 can be generalized across manufacturing variance between individual ESP32 units (e.g.,
silicon process variation affecting the hardware AES engine's power draw). It does not
bound the internal ASCON-vs-AES comparison within this study, since both algorithms were
measured on the same physical unit under the same conditions — the break-even result in
§5.2.3 is a within-unit comparison, not a between-unit one.

**INA219 measurement resolution.** The INA219's internal 12-bit ADC (§3.4.1) set a floor on
the smallest power delta the sensor could resolve. This bounds confidence in the precision
of the very smallest measured power and energy values (particularly at the smallest payload
sizes, where per-operation energy was lowest). It does not bound the much larger power and
energy differences that drove the break-even result at ≈347 bytes, which were well above
this resolution floor, nor does it explain the pattern in §4.7.1 where power and energy
differences were statistically significant at 72–78% of tested sizes — a pattern too
widespread to be an artifact of sensor resolution alone.

**Fixed 60-second sleep window, applied only analytically.** The sleep-phase energy term
(§4.2.4) was computed for a single, fixed 60-second interval and was not empirically varied
across different sleep durations. This bounds any claim this study makes about *other*
duty-cycle frequencies (e.g., a 5-minute or 1-hour sleep interval, as might be used by a
real deployment optimizing for multi-year battery life). It does not bound the ≈347-byte
break-even point itself, because §4.5.1 showed algebraically that the sleep-phase term was
a constant added identically to both algorithms' curves at every payload size — the
crossover point is mathematically independent of the specific sleep duration chosen, a
claim this study asserts but, per the point below, did not empirically confirm across
multiple sleep durations.

**Datasheet-derived, rather than measured, sleep current.** The 5 µA deep-sleep current
figure was taken from the Espressif ESP32-C3 Series Datasheet (§4.2.4) rather than measured
directly on the test unit during a genuine 60-second sleep interval. This bounds confidence
in the *absolute* total duty-cycle energy figures reported in §4.5.1 to the precision and
representativeness of that datasheet figure for the specific unit and configuration used.
It does not bound the comparative or crossover conclusion, for the same algebraic reason
given above — an error in the sleep-current constant would shift both algorithms' total
energy curves by the same amount and would not move the crossover point.

**Wi-Fi/MQTT transmission-phase noise.** The duty cycle's transmission phase (§3.3.4)
involved reconnecting to Wi-Fi and publishing over MQTT after each sleep interval, a source
of variable-latency, variable-power network activity outside the cryptographic operation
itself. This is a plausible contributor to the residual variance reflected in the
statistical results of §4.7.1, specifically the finding that execution-time differences
between the two algorithms reached significance at only 21% of tested payload sizes, well
below the 72–78% seen for power and energy — since execution time, as measured, isolated
only the `ENCRYPT_AND_MEASURE` call (§3.5.1) and should not itself have been affected by
transmission-phase noise, the comparatively low significance rate for time is more likely
explained by the two algorithms' execution times genuinely converging across much of the
payload range (§4.3.3) than by transmission noise contaminating the time measurement
directly; transmission-phase noise is a more plausible contributor to the *power*
measurement's variance, since power monitoring (§3.5.3) was active across a wider window of
the duty cycle than the isolated timing measurement. This distinction is noted here because
conflating the two would overstate transmission noise as an explanation for the
execution-time result specifically.

**A further limitation, not previously named in the structure of this chapter but relevant
here:** the wake-up and reconnection transient — the brief power spike as Wi-Fi and the
oscillator re-initialize after deep sleep, reported elsewhere in the literature to cost
approximately 22 µJ over 2.1 ms [Nkemeni et al., 2023] — was not separately measured or
isolated in this study's duty-cycle energy accounting. Because this transient, like the
sleep-phase current, would be expected to occur identically regardless of which
cryptographic algorithm was in use, its omission is not expected to bias the comparative
crossover result, but it is a further respect in which the total duty-cycle energy figures
reported in §4.5.1 represent an analytically-supplemented estimate rather than a fully
empirical, end-to-end measured total.

## 5.7 Summary of Chapter 5

This chapter interpreted the Chapter 4 results against each of the three research
objectives, finding that the hardware engine's initialization overhead was successfully
isolated and quantified (Objective 1), that the full duty-cycle per-byte energy cost was
measured and shown to depend on the relationship between active-phase and sleep-phase
energy at a given payload size (Objective 2), and that a specific, numeric break-even
payload size of approximately 347 bytes was identified and shown to reconcile a previously
unresolved conflict in the literature between studies favoring software ASCON and studies
favoring hardware-accelerated AES (Objective 3). The chapter then argued that the
reliability of these findings rested on a deliberately sequenced, identically-applied
cleaning and calibration pipeline (§5.4), and that the validity of the evaluation approach
was supported by per-byte normalization, controlled-variable design, and explicit
accounting for hardware initialization overhead — while being honestly bounded, in
particular, by the analytical (rather than measured) treatment of the sleep phase (§5.5).
Finally, §5.6 set out, limitation by limitation, exactly what this study's findings did and
did not establish. Chapter 6 now draws these findings together into a final assessment of
whether the three objectives were met, what this study contributes to the literature, and
what a following student should investigate next.
