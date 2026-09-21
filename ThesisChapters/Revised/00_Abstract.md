# Abstract (revised)

*Replaces the current Abstract (page iii). Keywords line unchanged except the last item. About 290 words.*

---

The Internet of Things increasingly relies on battery-powered devices that must balance data security against strict energy limits, yet no reviewed study compares software-based lightweight cryptography with hardware-accelerated legacy cryptography on the same platform under duty-cycle conditions. This dissertation evaluates ASCON-128, the NIST lightweight standard implemented in software, against AES-128-GCM using the dedicated AES hardware engine of the ESP32, in a Sleep → Wake → Sense → Encrypt → Transmit → Sleep duty cycle in which the encryption phase is measured on the device and the sleep phase is modelled from datasheet values.

Two measurement campaigns were carried out on an ESP32-WROOM-32E instrumented with an INA219 current monitor. A per-trial campaign (100 payload sizes, 16 to 1,600 bytes; 561 and 510 complete iterations) was found to be limited by instrumentation: the sensor cannot resolve a roughly 2 ms operation, and the timed region included task creation and sensor reads. A sustained-load campaign was therefore designed, in which each cipher call is repeated back-to-back while the sensor averages current, and the two algorithms are interleaved within one session. Its results are used for all energy conclusions.

Setting up the AES-GCM context cost 30.9 µs and 1.9 µJ per call. When that setup is paid on every message, as on a node that loses RAM in deep sleep, ASCON-128 is more energy-efficient below a break-even payload of approximately 100 bytes (95% bootstrap interval 96–107 bytes), and AES-128-GCM is more efficient above it; at 1,600 bytes AES-128-GCM used 28% less energy per call (104.7 µJ versus 145.2 µJ). If the AES context is kept between messages, AES-128-GCM was at least as efficient at every tested size. AES-128-GCM also used about 24% more memory. Against a modelled 60-second sleep interval, the choice of cipher changed total duty-cycle energy by less than 4%.

These findings reconcile a conflict in the literature and give designers a payload-size and setup-policy criterion for choosing between software and hardware cryptography.

**Keywords:** Internet of Things (IoT); Lightweight Cryptography; ASCON-128; AES-128-GCM; ESP32; Hardware Acceleration; Energy Efficiency; Duty Cycle; Break-Even Payload Size; Authenticated Encryption (AEAD)

---

### Numbers used and where they come from
| Claim | Source |
|---|---|
| 30.9 µs, 1.9 µJ setup | validation run 1 and 2 (`AES_SETKEY`), identical to 3 digits |
| ≈100 B (96–107 B) | validation run 2, 15 replicates, 5,000-resample bootstrap |
| 104.7 vs 145.2 µJ at 1,600 B | validation run 1, `AES_COLD` vs `ASCON` |
| 24% memory | original dataset, §4.6 (unchanged) |
| < 4% | (145.17 − 104.67) / (990 + 145.17) ≈ 3.6% at 1,600 B (5 µA case); smaller at all other sizes. **Depends on the sleep current, see [VERIFY 1] in `09_Open_Items.md`** |
