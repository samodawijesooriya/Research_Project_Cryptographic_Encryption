// main/run_trial.c
#include "run_trial.h"
#include "encrypt_measure.h"
#include "power_monitor.h"
#include "esp_random.h"
#include "esp_log.h"
#include <string.h>
#include <stdlib.h>

#define MAX_PAYLOAD_BYTES (16 * 100)   // j ranges 1..100 -> up to 1600 bytes

static const char *TAG = "run_trial";

extern void report_to_nodered(const monitor_ctx_t *ctx, const char *label);
extern void report_trial_start(int i, int j, size_t payload_len, const char *label);

// GENERATE_NONCE(algo) — Fig. 4. AES-128-GCM -> 12-byte nonce (GCM standard).
// ASCON-128 -> 16-byte nonce. Random bytes sourced from the ESP32 hardware RNG.
size_t generate_nonce(algo_t algo, uint8_t *out_nonce) {
    size_t nonce_len = (algo == ALGO_AES_128_GCM) ? 12 : 16;
    for (size_t i = 0; i < nonce_len; i++) {
        out_nonce[i] = (uint8_t)(esp_random() & 0xFF);   // true HW RNG: must never repeat
    }
    return nonce_len;
}

// GENERATE_PAYLOAD(j) — Fig. 3. Size = 16 * j, filled by PRNG_bytes(size, seed=128).
size_t generate_payload(int j, uint8_t *out_payload) {
    size_t size = 16 * (size_t)j;
    srand(128);   // fixed seed: reproducible payload, not a secret one
    for (size_t i = 0; i < size; i++) {
        out_payload[i] = (uint8_t)(rand() & 0xFF);
    }
    return size;
}

// RUN_TRIAL(algo, key, i, j) — Fig. 1/2.
void run_trial(algo_t algo, const uint8_t *key, int i, int j) {
    uint8_t nonce[16];
    uint8_t payload[MAX_PAYLOAD_BYTES];
    monitor_ctx_t mctx;
    const char *label = (algo == ALGO_AES_128_GCM) ? "AES-128-GCM" : "ASCON-128";

    size_t nonce_len   = generate_nonce(algo, nonce);
    size_t payload_len = generate_payload(j, payload);

    ESP_LOGI(TAG, "trial i=%d j=%d algo=%s payload_len=%u bytes",
             i, j, label, (unsigned)payload_len);
    report_trial_start(i, j, payload_len, label);

    encrypt_and_measure(algo, key, nonce, nonce_len, payload, payload_len, &mctx);

    // Transmit now, while Wi-Fi is already up — before the next deep sleep,
    // matching Sleep -> Wake -> Sense -> Encrypt -> Transmit -> Sleep.
    report_to_nodered(&mctx, label);
}