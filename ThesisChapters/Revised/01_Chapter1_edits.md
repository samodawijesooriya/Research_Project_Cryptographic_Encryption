# Chapter 1: targeted edits

Chapter 1 mostly stands. Change only the items below. Use "dissertation" instead of "thesis" and "paper" throughout the whole document.

---

## 1.4 (last paragraph): no change
The "3 s active / 297 s sleep" example is fine as a motivating illustration.

## 1.5: add one sentence at the end
> The evidence is also thin on measurement quality: energy is rarely measured on physical hardware at the resolution needed to separate a cryptographic call of a few milliseconds from its surrounding software, which is a problem this study encountered directly (Chapter 4).

## 1.7 Research Question: replace with
> How does hardware-accelerated AES-128-GCM on the ESP32 compare with software-based ASCON-128 in terms of energy per operation, power draw, execution time, memory usage and per-byte energy efficiency, and how do these differences translate into a Sleep → Wake → Sense → Encrypt → Transmit → Sleep duty cycle in which the encryption phase is measured and the sleep phase is modelled?

Reason: the original wording promised a fully measured duty cycle. Only the encryption phase is measured (Wi-Fi/MQTT transmission and wake-up are not); saying so up front avoids an overclaim.

## 1.8 Objectives: replace with
> - **Objective 1.** To measure the energy per operation and per byte of software ASCON-128 and hardware-accelerated AES-128-GCM on the ESP32, and to isolate the fixed cost of initialising the AES-GCM context (key setup) from the cost that scales with payload size.
> - **Objective 2.** To express the measured encryption cost as a share of a modelled duty cycle (measured active phase plus a datasheet-based sleep phase), so that the practical significance of the algorithm choice can be judged.
> - **Objective 3.** To determine the conditions (payload size and whether the AES context is set up on every message or kept) under which software ASCON-128 is preferable to hardware-accelerated AES-128-GCM, including any break-even payload size, with a confidence interval.

## 1.9 Organization of Thesis → "Organization of the Dissertation": append after the Chapter 3 paragraph
> **Chapter 4: Data Analysis and Results.** Presents two datasets: a per-trial dataset that exposed limits of the original instrumentation, and a sustained-load validation dataset used for all energy conclusions. It reports execution time, power, energy, break-even, memory and statistical tests.
>
> **Chapter 5: Discussion.** Interprets the results, explains the break-even mechanism, accounts for why the earlier per-trial measurements differed, compares the findings with the literature, and states the limitations and threats to validity.
>
> **Chapter 6: Conclusions and Future Work.** Answers the research question, states the contribution, and lists recommendations.
>
> **Appendices.** Firmware, protocol, raw summary tables, data-processing detail and reproducibility information.

## Also fix
- Reference formats: "[Kumar & Sethi Ericsson, 2019]" should be "[Kumar & Sethi, 2019]" (Ericsson is an affiliation).
- "Because of these devices are frequently deployed…" → "Because these devices are frequently deployed…".
- "This massive interconnected device necessitates…" → "This massive number of interconnected devices necessitates…".
- 1.6: "This research addresses this gap by evaluating…" is fine; keep.
