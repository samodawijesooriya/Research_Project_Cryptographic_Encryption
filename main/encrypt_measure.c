// main/encrypt_measure.c
#include "encrypt_measure.h"
#include "ascon128.h"
#include "mbedtls/gcm.h"
#include <string.h>

#define TAG_LEN 16

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

size_t encrypt_and_measure(algo_t algo,
                            const uint8_t *key,
                            const uint8_t *nonce, size_t nonce_len,
                            const uint8_t *payload, size_t payload_len,
                            monitor_ctx_t *out_ctx) {
    static uint8_t ciphertext[16 * 100 + TAG_LEN];
    size_t ct_len = 0;

    start_monitor(out_ctx);   // baseline heap snapshot + INA219 reading (Fig. 5)

    if (algo == ALGO_AES_128_GCM) {
        ct_len = aes128_gcm_encrypt(key, nonce, nonce_len,
                                     payload, payload_len, ciphertext);
    } else {
        ct_len = ascon128_encrypt(key, nonce, payload, payload_len, ciphertext);
    }

    stop_monitor(out_ctx);    // post-op heap + second INA219 reading, deltas derived
    output_metrics(out_ctx, (algo == ALGO_AES_128_GCM) ? "AES-128-GCM" : "ASCON-128");

    return ct_len;
}