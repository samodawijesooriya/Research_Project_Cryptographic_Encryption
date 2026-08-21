// main/power_monitor.c
#include "power_monitor.h"
#include "ina219.h"
#include <stdio.h>

// ESP32 is I2C master, INA219 is slave on GPIO21 (SDA) / GPIO22 (SCL), per
// thesis Section 3.5 ("Fig 5 schematic"). Address pins A0/A1 tied to GND -> 0x40.
#define INA219_SDA_GPIO   GPIO_NUM_21
#define INA219_SCL_GPIO   GPIO_NUM_22
#define INA219_I2C_ADDR   0x40

static bool s_ina219_ready = false;

static void ensure_ina219_ready(void) {
    if (!s_ina219_ready) {
        ina219_init(I2C_NUM_0, INA219_SDA_GPIO, INA219_SCL_GPIO, INA219_I2C_ADDR);
        s_ina219_ready = true;
    }
}

void start_monitor(monitor_ctx_t *ctx) {
    ensure_ina219_ready();
    ctx->start_time_us      = esp_timer_get_time();
    ctx->heap_before         = heap_caps_get_free_size(MALLOC_CAP_8BIT);
    ctx->current_before_mA   = ina219_read_current_mA();
    ctx->power_before_mW     = ina219_read_power_mW();
}

void stop_monitor(monitor_ctx_t *ctx) {
    ctx->end_time_us        = esp_timer_get_time();
    ctx->heap_after          = heap_caps_get_free_size(MALLOC_CAP_8BIT);
    ctx->current_after_mA    = ina219_read_current_mA();
    ctx->power_after_mW      = ina219_read_power_mW();
}

void output_metrics(const monitor_ctx_t *ctx, const char *label) {
    int64_t elapsed_us     = ctx->end_time_us - ctx->start_time_us;
    int32_t heap_delta_b   = (int32_t)ctx->heap_before - (int32_t)ctx->heap_after;
    float   power_delta_mW = ctx->power_after_mW - ctx->power_before_mW;

    // This record feeds directly into the offline clean/CSV/analyze pipeline
    // (thesis Section 3.6/3.7) — no cross-device timestamp correlation needed,
    // since everything was measured on this one board.
    printf("[%s] time_us=%lld  heap_delta_bytes=%ld  "
           "current_mA(before,after)=%.3f,%.3f  power_mW(before,after)=%.3f,%.3f  "
           "power_delta_mW=%.3f\n",
           label, elapsed_us, heap_delta_b,
           ctx->current_before_mA, ctx->current_after_mA,
           ctx->power_before_mW, ctx->power_after_mW,
           power_delta_mW);
}