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

## MQTT Connection using CMD
### For getting the bechamarks
To subscribe to that topic from the command line (useful for testing outside Node-RED), use mosquitto_sub:

mosquitto_sub -h 10.83.32.98 -p 1883 -t "esp32/benchmark" -v

Change the ip address by giveing `ipconfig` command in the cmd.

### For getting the benchmark stats
mosquitto_sub -h 10.83.32.98 -p 1883 -t "esp32/benchmark/stats" -v

## Sample Benchmark Code

### Sample Benchmark Stats
{"event":"trial_start","algo":"ASCON-128","i":21,"j":76,"payload_len_bytes":1216}
### Sample Benchmark Data
{"id":2176,"algo":"ASCON-128","size":1216,"time_us":2800,"heap_delta_bytes":4444,"heap_peak_used_bytes":2840,"stack_peak_used_bytes":0,"stack_used_bytes":79,"current_before_mA":-19.4,"current_after_mA":-14.9,"power_before_mW":88,"power_after_mW":68,"power_delta_mW":-20}

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


Design decisions
Which payload sizes to test. Don't repeat all 100 sizes — pick 5–6 representative ones spanning your existing j range (e.g. smallest, ~25%, ~50%, ~75%, largest). Your existing dataset already tells you how time/memory scale with size; you just need power to fill in the same trend at a few points.

Batch size N. Needs the whole loop to run comfortably longer than the INA219's ~1.06ms conversion cycle so the average is over many real conversions, not one stale register value. If ASCON is tens-of-µs and AES-GCM is low-hundreds-of-µs per call, N=2000–5000 gives a window of roughly 0.1–1s — plenty.

Sampling interval K. Don't poll the INA219 every iteration inside the timing-critical loop — an I2C read at 400kHz takes tens-to-~100µs, which is comparable to or larger than the crypto op itself, so interleaving it would both slow down the loop and inject extra current draw right into the number you're trying to measure. Poll every K=20–50 iterations instead.

Code additions (new, isolated — don't touch the existing functions)
In power_monitor.h, add accumulator fields and a sampling function without changing the existing struct fields other trials rely on:


// added for supplementary energy run — does not affect existing fields
double   current_sum_mA;
double   power_sum_mW;
uint32_t sample_count;

void sample_monitor(monitor_ctx_t *ctx) {
    ctx->current_sum_mA += ina219_read_current_mA();
    ctx->power_sum_mW   += ina219_read_power_mW();
    ctx->sample_count++;
}
In encrypt_measure.c, add a new function alongside the existing encrypt_and_measure (leave that one exactly as-is):


void energy_batch_measure(algo_t algo, const uint8_t *key,
                           const uint8_t *nonce, size_t nonce_len,
                           const uint8_t *payload, size_t payload_len,
                           int N, int sample_every,
                           monitor_ctx_t *out_ctx) {
    static uint8_t ciphertext[16 * 100 + TAG_LEN];
    start_monitor(out_ctx);
    for (int i = 0; i < N; i++) {
        if (algo == ALGO_AES_128_GCM)
            aes128_gcm_encrypt(key, nonce, nonce_len, payload, payload_len, ciphertext);
        else
            ascon128_encrypt(key, nonce, payload, payload_len, ciphertext);
        if (i % sample_every == 0) sample_monitor(out_ctx);
    }
    stop_monitor(out_ctx);

    float avg_power_mW = out_ctx->sample_count ?
        (float)(out_ctx->power_sum_mW / out_ctx->sample_count) : 0;
    printf("[ENERGY %s] N=%d samples=%lu avg_power_mW=%.3f\n",
           (algo == ALGO_AES_128_GCM) ? "AES-128-GCM" : "ASCON-128",
           N, (unsigned long)out_ctx->sample_count, avg_power_mW);
}
Note this deliberately doesn't report time from this loop — the periodic I2C polling inflates elapsed time, so don't use it. You already have clean, valid per-op timing for each payload size from your main dataset.

Trial matrix & how to run it without disturbing the main sweep
Rather than editing main.c's existing 500×100 loop, wire this behind a separate small driver so your archived dataset-producing firmware stays frozen and rebuildable:

Before changing anything, commit/tag the current state (git tag pre-energy-supplement or similar) so you can always rebuild the exact firmware that produced your existing dataset.
Add a second, small RTC-backed loop (copy the pattern already in main.c) iterating over just: 2 algorithms × ~6 payload sizes × ~10–15 repeats (independent boots, for variance across trials) = ~150–180 boots.
You can shorten DEEP_SLEEP_SECONDS for this run — the long 60s sleep in the original design exists to let things settle for clean heap watermarks; power averaging doesn't need that, a few seconds between boots is enough for I2C/WiFi to reinit cleanly.
Runtime estimate: ~150 boots × (~2–3s reconnect + ~0.2–1s batch + ~5s settle) ≈ 15–25 minutes of device time — well inside "a few hours," with margin for re-runs.
Turning the result into energy
For each (algorithm, payload size):


energy_per_op_mJ = avg_power_mW × time_per_op_us_from_existing_dataset / 1000
Average avg_power_mW across your ~10–15 repeat batches per condition, report mean ± CI, and pair it with the mean per-op time you already have for that same algorithm/size from the original 50,000-trial dataset.

Write-up note
In your methodology section, be explicit that energy is computed by combining two separately-validated measurements (batched average power × previously-measured per-operation time) rather than derived from a single continuous energy trace — that's a legitimate and common practical compromise, but naming it precisely heads off questions from examiners better than presenting it as if it were one seamless measurement.