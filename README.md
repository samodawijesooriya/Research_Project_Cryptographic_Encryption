ESP32 Lightweight Cryptography Benchmark
=========================================

ESP-IDF firmware for a research project comparing **AES-128-GCM** against the
NIST lightweight-crypto finalist **ASCON-128** on an ESP32, measured for
execution time, heap usage, and power draw across a sweep of payload sizes.

## What it does

On each boot the device runs exactly **one trial**, then deep-sleeps for a
fixed interval and resets to run the next one. State (loop indices, chosen
algorithm, encryption key) survives across sleep cycles in RTC memory.

For a trial `(i, j)`:

1. Generate a random nonce (12 bytes for AES-GCM, 16 for ASCON-128) from the
   ESP32 hardware RNG.
2. Generate a deterministic pseudo-random payload of `16 * j` bytes
   (fixed seed, so payloads are reproducible across runs).
3. Encrypt the payload, measuring elapsed time, heap delta, and current/power
   draw (via an INA219 sensor) before and after.
4. Publish the trial-start event and the resulting metrics to an MQTT broker
   (consumed by a Node-RED flow for logging/analysis).
5. Persist progress (`i`, `j`) to RTC memory, then deep-sleep until the next
   trial.

The sweep runs `OUTER_LOOP_COUNT` (500) payload-size steps x
`INNER_LOOP_COUNT` (100) repetitions each; both are defined in
[main/main.c](main/main.c). Once the sweep completes, the device halts in
deep sleep permanently.

## Source layout

| File | Purpose |
|---|---|
| [main/main.c](main/main.c) | Boot/resume state machine, deep-sleep scheduling |
| [main/run_trial.c](main/run_trial.c) | Per-trial nonce/payload generation and orchestration |
| [main/encrypt_measure.c](main/encrypt_measure.c) | Runs the AES-GCM / ASCON-128 encryption under measurement |
| [main/ascon128.c](main/ascon128.c) | ASCON-128 AEAD implementation |
| [main/power_monitor.c](main/power_monitor.c) | Timing + INA219 current/power sampling |
| [main/ina219.c](main/ina219.c) | INA219 I2C current/power sensor driver |
| [main/wifi_stubs.c](main/wifi_stubs.c) | Wi-Fi station bring-up and MQTT reporting to Node-RED |

## Hardware

- ESP32 development board
- INA219 current/power sensor wired over I2C, in-line with the ESP32's supply

## Building and flashing

Requires [ESP-IDF](https://docs.espressif.com/projects/esp-idf/en/latest/get-started/index.html).

```
idf.py set-target esp32
idf.py menuconfig   # under "Benchmark Configuration": set Wi-Fi + MQTT broker
idf.py build flash monitor
```

### Configuration

Set these under `Benchmark Configuration` in `menuconfig` (or in
`sdkconfig`) before flashing:

- `ESP_WIFI_SSID` / `ESP_WIFI_PASSWORD` — network the device joins on boot
- `ESP_MQTT_BROKER_URI` — Node-RED's MQTT broker (use your PC's LAN IP, not
  `localhost`, since the ESP32 is a separate device on the network)
- `ESP_MQTT_TOPIC` — topic trial results are published to
- `ESP_MQTT_TOPIC_STATS` — topic trial-start events are published to

`sdkconfig` is not committed to version control since it holds these
network credentials; each collaborator generates their own via
`idf.py menuconfig`.

## License

Public Domain / CC0 — see [LICENSE](LICENSE).
