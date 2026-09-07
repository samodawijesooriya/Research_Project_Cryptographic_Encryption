// main/run_trial.c
#include "run_trial.h"
#include "encrypt_measure.h"
#include "power_monitor.h"
#include "esp_random.h"
#include "esp_log.h"
#include <string.h>
#include <stdlib.h>

#ifdef DEBUG_HEAP_TRACE
#include "esp_heap_trace.h"
#define HEAP_TRACE_NUM_RECORDS 100
static heap_trace_record_t s_heap_trace_records[HEAP_TRACE_NUM_RECORDS];
#endif

#define MAX_PAYLOAD_BYTES (16 * 100)   // j ranges 1..100 -> up to 1600 bytes

static const char *TAG = "run_trial";

extern void report_to_nodered(const monitor_ctx_t *ctx, const char *label, int trial_id, size_t payload_len);
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

    // Single ID computed once from the restored (i, j) counters and reused
    // verbatim in both the console line and the JSON telemetry line below,
    // so the two logs can be joined on `id` afterward.
    int trial_id = i * 100 + j;

    ESP_LOGI(TAG, "Running trial %d/%d - %s (%u bytes) [id=%d]",
             i, j, label, (unsigned)payload_len, trial_id);
    report_trial_start(i, j, payload_len, label);

#ifdef DEBUG_HEAP_TRACE
    // One-off diagnostic: enable CONFIG_HEAP_TRACING_STANDALONE in menuconfig
    // and build with -DDEBUG_HEAP_TRACE to trace allocations made by this
    // single ENCRYPT_AND_MEASURE call (each boot only ever runs one trial,
    // so this naturally captures exactly one call).
    static bool s_heap_trace_initialized = false;
    if (!s_heap_trace_initialized) {
        ESP_ERROR_CHECK(heap_trace_init_standalone(s_heap_trace_records, HEAP_TRACE_NUM_RECORDS));
        s_heap_trace_initialized = true;
    }
    heap_trace_start(HEAP_TRACE_ALL);
#endif

    encrypt_and_measure(algo, key, nonce, nonce_len, payload, payload_len, &mctx);

#ifdef DEBUG_HEAP_TRACE
    heap_trace_stop();
    heap_trace_dump();
#endif

    // Transmit now, while Wi-Fi is already up — before the next deep sleep,
    // matching Sleep -> Wake -> Sense -> Encrypt -> Transmit -> Sleep.
    report_to_nodered(&mctx, label, trial_id, payload_len);
}