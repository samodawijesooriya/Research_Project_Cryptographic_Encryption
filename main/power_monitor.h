// main/power_monitor.h
#ifndef POWER_MONITOR_H
#define POWER_MONITOR_H

#include <stdint.h>
#include "esp_heap_caps.h"
#include "esp_timer.h"

typedef struct {
    int64_t  start_time_us;
    int64_t  end_time_us;
    uint32_t heap_before;
    uint32_t heap_after;
    float    current_before_mA;
    float    current_after_mA;
    float    power_before_mW;
    float    power_after_mW;
} monitor_ctx_t;

void start_monitor(monitor_ctx_t *ctx);
void stop_monitor(monitor_ctx_t *ctx);
void output_metrics(const monitor_ctx_t *ctx, const char *label);

#endif // POWER_MONITOR_H