// main/encrypt_measure.h
#ifndef ENCRYPT_MEASURE_H
#define ENCRYPT_MEASURE_H

#include "run_trial.h"
#include "power_monitor.h"

size_t encrypt_and_measure(algo_t algo,
                            const uint8_t *key,
                            const uint8_t *nonce, size_t nonce_len,
                            const uint8_t *payload, size_t payload_len,
                            monitor_ctx_t *out_ctx,
                            int trial_id);

#endif // ENCRYPT_MEASURE_H