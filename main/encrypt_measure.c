// main/encrypt_measure.c
#include "encrypt_measure.h"
#include "ascon128.h"
#include "mbedtls/gcm.h"
#include "freertos/semphr.h"
#include <string.h>

#define TAG_LEN 16

// Stack the dedicated encrypt task runs on. Sized well above what AES-GCM
// (mbedtls context + round-key tables) or ASCON (a handful of local u64s)
// actually need -- see CONFIG_ESP_MAIN_TASK_STACK_SIZE=3584 in sdkconfig for
// a comparable reference point on this project's main task.
#define ENCRYPT_TASK_STACK_BYTES 4096
#define ENCRYPT_TASK_PRIORITY    (tskIDLE_PRIORITY + 1)

typedef struct {
    algo_t         algo;
    const uint8_t *key;
    const uint8_t *nonce;
    size_t         nonce_len;
    const uint8_t *payload;
    size_t         payload_len;
    uint8_t       *ciphertext_out;
    size_t         ct_len;
    uint32_t       stack_used_bytes;
    SemaphoreHandle_t done_sem;
} encrypt_task_args_t;

static size_t aes128_gcm_encrypt(const uint8_t *key,
                                  const uint8_t *nonce, size_t nonce_len,
                                  const uint8_t *plaintext, size_t pt_len,
                                  uint8_t *ciphertext_out) {
    mbedtls_gcm_context ctx;
    mbedtls_gcm_init(&ctx);
    mbedtls_gcm_setkey(&ctx, MBEDTLS_CIPHER_ID_AES, key, 128);

    uint8_t tag[TAG_LEN];
    mbedtls_gcm_crypt_and_tag(&ctx, MBEDTLS_GCM_ENCRYPT, pt_len,
                               nonce, nonce_len,
                               NULL, 0,
                               plaintext, ciphertext_out,
                               TAG_LEN, tag);

    memcpy(ciphertext_out + pt_len, tag, TAG_LEN);
    mbedtls_gcm_free(&ctx);
    return pt_len + TAG_LEN;
}

// Runs on its own freshly-created task so uxTaskGetStackHighWaterMark()
// reflects ONLY this call's stack depth. Measuring on the caller's task
// (run_trial's task) would be contaminated: report_trial_start()'s MQTT
// publish runs first and drives that task's watermark far deeper than either
// AES-GCM or ASCON ever reach, so a before/after diff there is always ~0
// regardless of the crypto call's real footprint.
static void encrypt_task_fn(void *pv) {
    encrypt_task_args_t *args = (encrypt_task_args_t *)pv;

    UBaseType_t hwm_words_before = uxTaskGetStackHighWaterMark(NULL);

    if (args->algo == ALGO_AES_128_GCM) {
        args->ct_len = aes128_gcm_encrypt(args->key, args->nonce, args->nonce_len,
                                           args->payload, args->payload_len,
                                           args->ciphertext_out);
    } else {
        args->ct_len = ascon128_encrypt(args->key, args->nonce,
                                         args->payload, args->payload_len,
                                         args->ciphertext_out);
    }

    UBaseType_t hwm_words_after = uxTaskGetStackHighWaterMark(NULL);
    args->stack_used_bytes = (hwm_words_before > hwm_words_after)
        ? (uint32_t)(hwm_words_before - hwm_words_after) * sizeof(StackType_t)
        : 0;

    xSemaphoreGive(args->done_sem);
    vTaskDelete(NULL);
}

size_t encrypt_and_measure(algo_t algo,
                            const uint8_t *key,
                            const uint8_t *nonce, size_t nonce_len,
                            const uint8_t *payload, size_t payload_len,
                            monitor_ctx_t *out_ctx,
                            int trial_id) {
    static uint8_t ciphertext[16 * 100 + TAG_LEN];

    start_monitor(out_ctx);   // baseline heap snapshot + INA219 reading (Fig. 5)

    encrypt_task_args_t args = {
        .algo = algo, .key = key,
        .nonce = nonce, .nonce_len = nonce_len,
        .payload = payload, .payload_len = payload_len,
        .ciphertext_out = ciphertext,
        .done_sem = xSemaphoreCreateBinary(),
    };
    xTaskCreate(encrypt_task_fn, "encrypt_task", ENCRYPT_TASK_STACK_BYTES,
                &args, ENCRYPT_TASK_PRIORITY, NULL);
    xSemaphoreTake(args.done_sem, portMAX_DELAY);
    vSemaphoreDelete(args.done_sem);

    out_ctx->stack_used_bytes = args.stack_used_bytes;

    stop_monitor(out_ctx);    // post-op heap + second INA219 reading, deltas derived
    output_metrics(out_ctx, (algo == ALGO_AES_128_GCM) ? "AES-128-GCM" : "ASCON-128",
                    trial_id, payload_len);

    return args.ct_len;
}