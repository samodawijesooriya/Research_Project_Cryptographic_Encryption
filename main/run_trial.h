// main/run_trial.h
#ifndef RUN_TRIAL_H
#define RUN_TRIAL_H

#include <stdint.h>
#include <stddef.h>

typedef enum {
    ALGO_AES_128_GCM,
    ALGO_ASCON_128
} algo_t;

size_t generate_nonce(algo_t algo, uint8_t *out_nonce);
size_t generate_payload(int j, uint8_t *out_payload);
void   run_trial(algo_t algo, const uint8_t *key, int i, int j);

#endif // RUN_TRIAL_H