# Chapter 06: Conclusions and Future Work

**Formatting note:** section numbering is placeholder for review. Citations reused from the
existing Chapter 2/3 reference list only; no new sources introduced. This chapter is
deliberately short — the interpretation, mechanisms, literature comparison, and detailed
limitations are covered in Chapter 5 and are not repeated here.

---

## 6.1 Introduction

This chapter closes the thesis: it summarizes whether the three objectives were met
(§6.2), answers the central research question in one paragraph (§6.3), states this thesis's
contribution to the literature (§6.4), and sets out recommended future work (§6.5).

## 6.2 Achievement of Research Objectives

All three objectives set out in §1.8 were met.

- **Objective 1** (total duty-cycle energy and per-byte efficiency, including hardware
  initialization overhead) — met. The hardware AES engine's initialization overhead was
  isolated and quantified as a 30.14 µJ fixed cost, against 15.03 µJ for ASCON-128 (§4.7.2).

- **Objective 2** (energy cost per byte across the full duty cycle) — met, with one
  qualification. Per-byte energy was measured across all 100 tested payload sizes for the
  complete duty cycle (§4.5.1); the sleep-phase contribution to that total was added
  analytically from a datasheet figure rather than measured directly (§5.4), though this
  does not affect the comparison between the two algorithms.

- **Objective 3** (break-even payload size and the conditions favoring ASCON-128) — met.
  A break-even point of approximately 347 bytes was identified and confirmed by an
  independent regime check (§4.5.2–§4.5.3).

## 6.3 Answer to the Research Question

Neither algorithm was unconditionally more energy-efficient. AES-128-GCM's hardware
acceleration carries a higher fixed per-operation cost but a lower cost per additional
byte, while ASCON-128's software implementation carries a lower fixed cost but a higher
cost per byte. These two cost structures cross at approximately 347 bytes of payload:
below this size, software ASCON-128 is the more energy-efficient choice for a full IoT
duty cycle on the ESP32; above it, hardware-accelerated AES-128-GCM is more efficient. The
ESP32's hardware accelerator therefore does not provide an unconditionally more
energy-efficient solution than software-based lightweight cryptography — only a
conditionally better one, depending on typical payload size.

## 6.4 Contribution to Knowledge

Prior literature had compared ASCON against *software* AES, and hardware-accelerated AES
against *software* AES, but not ASCON against hardware AES directly (§2.7). This thesis
closes that gap by comparing both algorithms on the same platform, under an identical
measurement pipeline, across a full duty cycle rather than an isolated encryption
operation. The 347-byte break-even point is the concrete output of that comparison: a new,
citable data point that explains why the prior literature appeared divided rather than
contradicting either side of it (§5.3).

## 6.5 Recommendations for Future Work

The limitations discussed in §5.4 point to the following concrete next steps:

1. **Multi-unit replication** — repeat the measurement pipeline across multiple ESP32
   boards to check whether the break-even point is a platform-level constant or varies
   between units.
2. **Empirically measure the sleep and wake-up phases** with the existing INA219 sensor,
   instead of substituting a datasheet current figure, to produce a fully measured
   (rather than partly analytical) total energy figure.
3. **Test multiple sleep durations** (e.g., 10 s, 300 s, 3,600 s) to empirically confirm
   that the break-even point is independent of the chosen sleep interval, as this thesis
   showed algebraically but did not test directly.
4. **Use a higher-resolution current sensor** to check whether the INA219's 12-bit ADC
   resolution floor affects the precision of the break-even estimate.
5. **Isolate transmission-phase noise**, for example by repeating the experiment over a
   wired connection, to separate Wi-Fi/MQTT variability from the cryptographic operations
   themselves.
6. **Extend the comparison to other algorithm pairs** (e.g., ChaCha20-Poly1305 against a
   hardware-accelerated cipher) to test whether a break-even relationship of this kind is a
   general feature of software-versus-hardware cryptography comparisons, or specific to
   ASCON-128 and AES-128-GCM.
7. **Run a real battery-drain field trial** to validate the per-byte energy proxy used in
   this thesis against actual measured device lifetime.

## 6.6 Closing Remarks

This thesis compared software-based ASCON-128 against hardware-accelerated AES-128-GCM on
the ESP32 across a complete IoT duty cycle, using 561 and 510 complete measurement
iterations respectively across 100 payload sizes. It found that neither algorithm was
unconditionally more energy-efficient: the two crossed over at approximately 347 bytes,
with ASCON-128 preferable below that point and AES-128-GCM preferable above it. This
finding, and the fixed-cost/marginal-cost mechanism shown to drive it (§5.2), is offered as
a more precise, evidence-based basis for choosing between software and hardware
cryptography in energy-constrained IoT deployments.
