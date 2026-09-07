// main/power_monitor.h
#ifndef POWER_MONITOR_H
#define POWER_MONITOR_H

#include <stdint.h>
#include "esp_heap_caps.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

typedef struct {
    int64_t  start_time_us;
    int64_t  end_time_us;
    uint32_t heap_before;
    uint32_t heap_after;
    // Watermarks, not simple before/after snapshots: heap_min_free_* is the
    // lowest free-heap level ever seen since boot (heap_caps_get_minimum_free_size),
    // and stack_hwm_free_* is the least free stack ever seen on this task
    // (uxTaskGetStackHighWaterMark, in BYTES on ESP-IDF/Xtensa -- unlike vanilla
    // FreeRTOS this port's StackType_t is 1 byte, not a 4-byte word). Since each
    // trial runs in its own boot session (deep sleep resets the chip -- see
    // main.c), these watermarks reset every trial, so before/after deltas give
    // the true peak heap/stack consumed by *this* encrypt call, including any
    // transient allocations that were freed before stop_monitor() ran.
    uint32_t heap_min_free_before;
    uint32_t heap_min_free_after;
    uint32_t stack_hwm_free_before;
    uint32_t stack_hwm_free_after;
    // Stack actually consumed by just the ENCRYPT(...) call, measured with
    // uxTaskGetStackHighWaterMark(NULL) taken immediately before/after that
    // call (not the whole start_monitor..stop_monitor window above, which
    // also covers INA219 I/O and tends to read back 0 since the task's
    // watermark was already driven lower by earlier calls this boot).
    uint32_t stack_used_bytes;
    float    current_before_mA;
    float    current_after_mA;
    float    power_before_mW;
    float    power_after_mW;
} monitor_ctx_t;

void start_monitor(monitor_ctx_t *ctx);
void stop_monitor(monitor_ctx_t *ctx);
void output_metrics(const monitor_ctx_t *ctx, const char *label);

#endif // POWER_MONITOR_H