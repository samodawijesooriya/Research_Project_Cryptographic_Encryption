# Chapter 2: targeted edits

Chapter 2 needs additions, not a rewrite. The research gap in 2.7 remains valid.

---

## 2.4.2 Measurement Techniques and Instrumentation: add as a new paragraph before "These inconsistencies become especially consequential…"

> A further practical constraint concerns temporal resolution. Low-cost current monitors such as the INA219 convert the shunt voltage at a fixed rate: at 12-bit resolution one conversion takes about 532 µs, and the device offers hardware averaging over up to 128 samples (about 68 ms per result) [Texas Instruments, 2008]. A cryptographic call that lasts a few milliseconds, or less, therefore cannot be resolved by two instantaneous register reads taken before and after it, because each register holds the result of the most recently completed conversion rather than the instantaneous current. The usual remedy is to repeat the operation continuously for long enough that several full conversions fall inside the measurement window, and to derive energy per operation from mean power and time per operation. Studies that report per-operation energy for millisecond-scale operations should therefore state how the sensor's conversion time was accommodated.

## 2.5.2 Sleep Implementation Mechanisms: correct the source and value
Current text cites the ESP32-C3 datasheet ("Mac et al., n.d.") for deep-sleep current. The board in this study is an **ESP32** (ESP32-WROOM-32E), not an ESP32-C3.
- Replace the citation with the **ESP32 Series Datasheet** and cite the deep-sleep figure for the "RTC timer + RTC memory" configuration from its low-power current table. **[VERIFY 1]** the exact value (I expect 10 µA; the C3 figure of 5 µA was used in the previous draft).
- The range "10 µA–150 µA" in the existing sentence can stay if it is attributed to a source you can point to.

## 2.3.3 The ESP32 Hardware Accelerator: add one sentence at the end of the second paragraph
> The accelerator covers the AES block operation; it does not remove the per-call cost of preparing the cipher context (key expansion and loading), which is examined in Chapters 4 and 5.

(Do not go further than this in Chapter 2. Whether the GHASH part of GCM runs in hardware or software on this platform is **not verified**; see `09_Open_Items.md`.)

## 2.7 Research Gap and Justification: add one sentence to the first paragraph, after "remains empirically untested"
> In addition, none of the reviewed studies reports the fixed cost of preparing the hardware cipher context separately from the cost that scales with payload size, although that split determines at which message size a hardware accelerator becomes worthwhile.

## Also fix
- 2.1.2 "Bideh et al., 2020]" → missing opening bracket.
- 2.2.4 "researches acknowledge" → "researchers acknowledge".
- 2.3.4: the claim "ASCON-128 can cut execution latency by 74%" is attributed to Ridho Rabbani (2025); keep, but make sure the wording says *software-emulated AES*, as it already does.
- "The extend which of these…" (2.2.5) → "The extent to which these…".
- Table 1 caption sits below the table; keep captions consistent (tables: caption above; figures: caption below) across the whole document.
- References list: "[Mahdi & Abdullah, 2025]" appears twice with different entries (one is Ibrahim et al.). Fix the key of the Ibrahim et al. entry.
