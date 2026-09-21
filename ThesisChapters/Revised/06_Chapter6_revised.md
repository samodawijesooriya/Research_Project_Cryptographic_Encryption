# Chapter 06: Conclusions and Future Work (revised, full replacement)

---

## 6.1 Introduction

This chapter states whether the three objectives were met (6.2), answers the research question (6.3), states the contribution (6.4), and recommends further work (6.5). Closing remarks follow in 6.6.

## 6.2 Achievement of Research Objectives

All three objectives set out in 1.8 were met, with the qualifications stated.

- **Objective 1: energy per operation and per byte, and the initialisation cost of AES-128-GCM.** Met. Energy per operation and per byte were measured for both ciphers at 18 payload sizes from 16 to 1,600 bytes and, near the crossover, at nine sizes from 64 to 128 bytes (4.5). The initialisation of the AES-GCM context was isolated and measured directly: 30.9 µs and 1.9 µJ per call (4.5.2). The fixed and variable costs are given in Table 8. *Qualification:* the fixed cost of ASCON-128 is a fitted intercept, not a separately measured step.
- **Objective 2: encryption as a share of a modelled duty cycle.** Met, with a qualification. The active phase was measured, and the sleep phase was modelled (60-second interval, datasheet current). Encryption was 0.4% to 13% of the modelled cycle, and the choice between ciphers changed total energy by under 4% (4.5.5). *Qualification:* transmission and wake-up were not measured, so the study does not establish the energy of a complete, empirically measured duty cycle.
- **Objective 3: conditions favouring ASCON-128, including the break-even.** Met. With AES-128-GCM setting up its context on every message, the break-even was approximately 100 bytes (95% bootstrap interval 96 to 107 bytes): ASCON-128 is more efficient below it and AES-128-GCM above it. If the AES context is retained, AES-128-GCM was at least as efficient at every tested size (4.5.3 and 4.5.4).

## 6.3 Answer to the Research Question

Neither algorithm was unconditionally more energy-efficient on the ESP32, and the deciding factors were payload size and how the AES context is managed. AES-128-GCM has a small but real per-message cost of preparing its context (30.9 µs and 1.9 µJ) and a lower cost per additional byte (0.062 versus 0.089 µJ per byte) than software ASCON-128. For a node that rebuilds the AES context on every message, as one that loses RAM in deep sleep does, software ASCON-128 was the more energy-efficient choice below about 100 bytes and hardware-assisted AES-128-GCM above it, and at 1,600 bytes AES-128-GCM used 28% less energy per call. For a node that keeps or reuses the context, AES-128-GCM was the more efficient choice at every size from 64 bytes and equal within measurement error at 16 bytes. AES-128-GCM used about 24% more run-time memory. Against a modelled 60-second sleep interval, the difference in total energy per cycle was below 4%, so the choice matters most for nodes that send frequently or in large batches.

## 6.4 Contribution to Knowledge

1. **A direct comparison.** The literature compared ASCON with software AES, and hardware AES with software AES, but not ASCON with hardware-assisted AES-128-GCM on the same platform (2.7). This dissertation provides that comparison, on one board, under one measurement pipeline, interleaved in a single session.
2. **A design criterion with its condition.** The break-even of about 100 bytes, and the finding that it disappears when the AES context is reused, give a payload-size and setup-policy criterion rather than a single number.
3. **A measured setup cost.** The initialisation cost of the AES-GCM context on the ESP32 was measured directly (1.9 µJ).
4. **A methodological finding.** A per-trial method, using two instantaneous sensor readings around a call of about 2 ms with instrumentation inside the timed region, can produce a reproducible but unsupported result (a 347-byte break-even that survives trimming). A sustained-load method resolves this, and the documented comparison of the two may help others using low-cost current monitors.
5. **A new memory comparison.** AES-128-GCM used about 24% more run-time memory than ASCON-128 on the same platform (4.6).

## 6.5 Recommendations for Future Work

1. **Cold-start measurement.** Measure the time of the first cipher call after a wake from deep sleep, for both ciphers, to test whether first-execution effects add a fixed cost (5.2.5). This addresses the main open question left by the comparison of the two campaigns.
2. **Fully measured duty cycle.** Measure the sleep, wake-up and transmission phases with the INA219 (or a sensor with a lower range) in place of the datasheet-based sleep model, and include the transmission of the tag and nonce overhead.
3. **Replication.** Repeat the pipeline on several boards, and, if possible, add an independent reference instrument to check the absolute scale.
4. **Other sleep intervals and message policies.** Vary the reporting interval and the number of messages per wake to test the practical-significance result of 4.5.5 directly. The break-even itself does not depend on the sleep interval, since the sleep term is identical for both ciphers, but this was shown by argument and not by experiment.
5. **Software AES on the same board.** Add software-only AES-128-GCM to place the two literature groups on one scale.
6. **Which parts of GCM run in hardware.** Establish the split of work between the AES peripheral and the CPU in mbedTLS on the ESP32, to explain the per-byte costs.
7. **Field trial.** A battery-drain trial would test the energy proxy against real device lifetime.

## 6.6 Closing Remarks

This dissertation compared software ASCON-128 with hardware-assisted AES-128-GCM on the ESP32 in a modelled IoT duty cycle. An early per-trial measurement produced a break-even of 347 bytes; a follow-up sustained-load measurement showed that this method could not resolve the energy of the operation, and the conclusions were rebuilt on the second. The finding is that ASCON-128 is more energy-efficient for messages below roughly 100 bytes when the AES context is set up per message, and that AES-128-GCM is at least as efficient otherwise, with a small effect on total energy at long sleep intervals. It is offered as an evidence-based design rule for the active phase of energy-constrained IoT nodes, together with a documented method for measuring it.
