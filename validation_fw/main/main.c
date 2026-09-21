// validation_fw/main/main.c
//
// Supplementary validation experiment for the dissertation (supervisor review).
//
// Why this exists: the original benchmark estimated per-operation energy from
// two instantaneous INA219 reads bracketing a single ~2 ms encrypt call. The
// INA219 (12-bit, 532 us/conversion) cannot resolve that, so this firmware uses
// a SUSTAINED-LOAD method instead:
//
//   for each (variant, payload size), in shuffled order, per replicate:
//     idle window  (core 1 idle)          -> mean current  I_idle_pre
//     load window  (core 1 runs the op back-to-back for ~700 ms)
//                                          -> mean current  I_load, and time/op
//     idle window                          -> mean current  I_idle_post
//   E_op = V_bus * (I_load - mean(I_idle_pre, I_idle_post)) * time_per_op
//
// The INA219 is configured to average 128 samples per shunt conversion (68 ms),
// so a >=700 ms window contains several full, clean conversions. The constant
// INA219 zero-offset cancels in (I_load - I_idle).
//
// Variants:
//   ASCON        ascon128_encrypt()                                   (software)
//   AES_COLD     gcm init + setkey + crypt_and_tag + free per op      (same as original benchmark)
//   AES_WARM     crypt_and_tag only, context set up once              (no per-op setup)
//   AES_SETKEY   gcm init + setkey + free only                        (setup cost in isolation)
//
// Everything is interleaved within one session (fixes the "AES and ASCON were
// run on different days" confound). No Wi-Fi, no MQTT, no deep sleep.

#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "esp_timer.h"
#include "esp_random.h"
#include "driver/i2c.h"
#include "mbedtls/gcm.h"
#include "ascon128.h"

// ---------------------------------------------------------------- config ----
#define REPLICATES        15        // full passes over all configs
#define LOAD_MS           700
#define LOAD_DISCARD_MS   200       // > 2 INA conversion cycles (68.6 ms each)
#define IDLE_MS           400
#define IDLE_DISCARD_MS   150
#define POLL_TICKS        1         // FREERTOS_HZ=100 -> ~10 ms between polls
#define MAX_PAYLOAD       1600

#define INA_SDA   GPIO_NUM_21
#define INA_SCL   GPIO_NUM_22
#define INA_ADDR  0x40
#define INA_PORT  I2C_NUM_0

// Same sizes as the dense region of interest around the reported crossover,
// plus a few anchor points across the full 16..1600 range.
// RUN 2: fine sweep around the crossover found in run 1 (between 64 and 128 B).
static const int SIZES[] = {64, 72, 80, 88, 96, 104, 112, 120, 128};
#define N_SIZES (sizeof(SIZES) / sizeof(SIZES[0]))

typedef enum { V_ASCON = 0, V_AES_COLD, V_AES_WARM, V_AES_SETKEY } variant_t;
static const char *VNAME[] = {"ASCON", "AES_COLD", "AES_WARM", "AES_SETKEY"};

typedef struct { variant_t v; int size; } config_t;
#define MAX_CONFIGS (N_SIZES * 3 + 1)
static config_t s_cfgs[MAX_CONFIGS];
static int      s_ncfg = 0;

// ---------------------------------------------------------------- INA219 ----
#define REG_CONFIG 0x00
#define REG_BUS_V  0x02
#define REG_CURRENT 0x04
#define REG_CAL    0x05

static void ina_write(uint8_t reg, uint16_t val) {
    uint8_t b[3] = {reg, (uint8_t)(val >> 8), (uint8_t)val};
    i2c_master_write_to_device(INA_PORT, INA_ADDR, b, 3, pdMS_TO_TICKS(100));
}
static int16_t ina_read(uint8_t reg) {
    uint8_t rx[2] = {0};
    i2c_master_write_read_device(INA_PORT, INA_ADDR, &reg, 1, rx, 2, pdMS_TO_TICKS(100));
    return (int16_t)((rx[0] << 8) | rx[1]);
}
static void ina_init(void) {
    i2c_config_t c = {
        .mode = I2C_MODE_MASTER, .sda_io_num = INA_SDA, .scl_io_num = INA_SCL,
        .sda_pullup_en = GPIO_PULLUP_ENABLE, .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = 400000,
    };
    i2c_param_config(INA_PORT, &c);
    i2c_driver_install(INA_PORT, c.mode, 0, 0, 0);
    ina_write(REG_CAL, 4096);                       // Rshunt 0.1 ohm, Current_LSB 0.1 mA (as original)
    // BRNG=32V, PGA /8, BADC=12-bit (532 us), SADC=128-sample average (68.1 ms), continuous.
    ina_write(REG_CONFIG, 0x39FF);
}
static float ina_current_mA(void) { return (float)ina_read(REG_CURRENT) * 0.1f; }
static float ina_bus_V(void)      { return (float)(ina_read(REG_BUS_V) >> 3) * 0.004f; }

// -------------------------------------------------------------- workloads ----
static const uint8_t KEY[16] = {0xA0,0xA1,0xA2,0xA3,0xA4,0xA5,0xA6,0xA7,0xA8,0xA9,0xAA,0xAB,0xAC,0xAD,0xAE,0xAF};
static uint8_t s_payload[MAX_PAYLOAD];
static uint8_t s_ct[MAX_PAYLOAD + 16];
static uint8_t s_nonce[16];
static mbedtls_gcm_context s_warm_ctx;

static inline void bump_nonce(void) { s_nonce[0]++; if (!s_nonce[0]) s_nonce[1]++; }

static void aes_encrypt_with(mbedtls_gcm_context *ctx, int size) {
    uint8_t tag[16];
    bump_nonce();
    mbedtls_gcm_crypt_and_tag(ctx, MBEDTLS_GCM_ENCRYPT, size, s_nonce, 12, NULL, 0,
                              s_payload, s_ct, 16, tag);
    s_ct[0] ^= tag[0];   // keep tag live
}

static inline void do_op(variant_t v, int size) {
    switch (v) {
    case V_ASCON:
        bump_nonce();
        ascon128_encrypt(KEY, s_nonce, s_payload, size, s_ct);
        break;
    case V_AES_COLD: {
        mbedtls_gcm_context ctx;
        mbedtls_gcm_init(&ctx);
        mbedtls_gcm_setkey(&ctx, MBEDTLS_CIPHER_ID_AES, KEY, 128);
        aes_encrypt_with(&ctx, size);
        mbedtls_gcm_free(&ctx);
        break;
    }
    case V_AES_WARM:
        aes_encrypt_with(&s_warm_ctx, size);
        break;
    case V_AES_SETKEY: {
        mbedtls_gcm_context ctx;
        mbedtls_gcm_init(&ctx);
        mbedtls_gcm_setkey(&ctx, MBEDTLS_CIPHER_ID_AES, KEY, 128);
        mbedtls_gcm_free(&ctx);
        break;
    }
    }
}

// Workload task, pinned to core 1 (sampling runs on core 0).
static TaskHandle_t      s_work_task;
static SemaphoreHandle_t s_done;
static volatile bool     s_run;
static volatile uint32_t s_ops;
static volatile int64_t  s_elapsed_us;
static variant_t         s_cur_v;
static int               s_cur_size;

static void work_task(void *arg) {
    for (;;) {
        ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
        uint32_t ops = 0;
        int64_t t0 = esp_timer_get_time();
        while (s_run) { do_op(s_cur_v, s_cur_size); ops++; }
        s_elapsed_us = esp_timer_get_time() - t0;
        s_ops = ops;
        xSemaphoreGive(s_done);
    }
}

// ---------------------------------------------------------------- sampling ---
typedef struct { double sum_mA, sum_V; int n; } acc_t;

static void sample_for(int total_ms, int discard_ms, acc_t *a) {
    int64_t t0 = esp_timer_get_time();
    for (;;) {
        int64_t el = (esp_timer_get_time() - t0) / 1000;
        if (el >= total_ms) break;
        if (el >= discard_ms) {
            a->sum_mA += ina_current_mA();
            a->sum_V  += ina_bus_V();
            a->n++;
        }
        vTaskDelay(POLL_TICKS);
    }
}

static void run_config(int rep, config_t cfg) {
    s_cur_v = cfg.v;
    s_cur_size = cfg.size;
    if (cfg.v == V_AES_WARM) {
        mbedtls_gcm_init(&s_warm_ctx);
        mbedtls_gcm_setkey(&s_warm_ctx, MBEDTLS_CIPHER_ID_AES, KEY, 128);
    }

    acc_t pre = {0}, load = {0}, post = {0};
    sample_for(IDLE_MS, IDLE_DISCARD_MS, &pre);

    s_run = true;
    xTaskNotifyGive(s_work_task);
    sample_for(LOAD_MS, LOAD_DISCARD_MS, &load);
    s_run = false;
    xSemaphoreTake(s_done, portMAX_DELAY);

    sample_for(IDLE_MS, IDLE_DISCARD_MS, &post);

    if (cfg.v == V_AES_WARM) mbedtls_gcm_free(&s_warm_ctx);

    double t_op_us = (double)s_elapsed_us / (double)s_ops;
    printf("DATA,%d,%s,%d,%lu,%.4f,%.4f,%.4f,%.4f,%.4f,%d,%d,%d\n",
           rep, VNAME[cfg.v], cfg.size, (unsigned long)s_ops, t_op_us,
           pre.sum_mA / pre.n, load.sum_mA / load.n, post.sum_mA / post.n,
           load.sum_V / load.n, pre.n, load.n, post.n);
}

// ------------------------------------------------- overhead of original method
// The original benchmark's "time_us" also included xTaskCreate + semaphore +
// two INA219 register reads (start_monitor) inside the timed region. Quantify
// those so the original intercepts can be interpreted.
static void task_noop(void *arg) { xSemaphoreGive((SemaphoreHandle_t)arg); vTaskDelete(NULL); }

static void measure_original_method_overhead(void) {
    const int N = 500;
    SemaphoreHandle_t sem = xSemaphoreCreateBinary();
    int64_t t0 = esp_timer_get_time();
    for (int i = 0; i < N; i++) {
        xTaskCreate(task_noop, "n", 2048, sem, tskIDLE_PRIORITY + 1, NULL);
        xSemaphoreTake(sem, portMAX_DELAY);
        vTaskDelay(1);                       // let the deleted task be reaped
    }
    double task_us = (double)(esp_timer_get_time() - t0) / N - 10000.0;   // minus the 10 ms tick delay
    vSemaphoreDelete(sem);

    int64_t t1 = esp_timer_get_time();
    for (int i = 0; i < N; i++) { (void)ina_current_mA(); (void)ina_read(0x03); }
    double i2c_us = (double)(esp_timer_get_time() - t1) / N;   // one current + one power read
    printf("OVERHEAD,task_create_and_sem_us,%.2f,ina219_current_plus_power_read_us,%.2f\n", task_us, i2c_us);
}

// ------------------------------------------------------------------- main ---
static uint32_t s_rng = 0xC0FFEE;
static uint32_t lcg(void) { s_rng = s_rng * 1664525u + 1013904223u; return s_rng >> 8; }

void app_main(void) {
    vTaskDelay(pdMS_TO_TICKS(3000));    // let the serial capture attach
    ina_init();

    // Fixed pseudo-random payload (same generator/seed as the original benchmark).
    srand(128);
    for (int i = 0; i < MAX_PAYLOAD; i++) s_payload[i] = (uint8_t)(rand() & 0xFF);
    for (int i = 0; i < 16; i++) s_nonce[i] = (uint8_t)esp_random();

    for (size_t i = 0; i < N_SIZES; i++) {
        s_cfgs[s_ncfg++] = (config_t){V_ASCON,    SIZES[i]};
        s_cfgs[s_ncfg++] = (config_t){V_AES_COLD, SIZES[i]};
        s_cfgs[s_ncfg++] = (config_t){V_AES_WARM, SIZES[i]};
    }
    s_cfgs[s_ncfg++] = (config_t){V_AES_SETKEY, 0};

    s_done = xSemaphoreCreateBinary();
    xTaskCreatePinnedToCore(work_task, "work", 8192, NULL, 5, &s_work_task, 1);

    printf("META,cpu_mhz,%d,ina_config,0x39FF,load_ms,%d,idle_ms,%d,replicates,%d,configs,%d\n",
           CONFIG_ESP_DEFAULT_CPU_FREQ_MHZ, LOAD_MS, IDLE_MS, REPLICATES, s_ncfg);
    printf("HEADER,rep,variant,size,ops,time_per_op_us,idle_pre_mA,load_mA,idle_post_mA,vbus_V,n_pre,n_load,n_post\n");

    measure_original_method_overhead();

    for (int rep = 0; rep < REPLICATES; rep++) {
        int order[MAX_CONFIGS];
        for (int i = 0; i < s_ncfg; i++) order[i] = i;
        for (int i = s_ncfg - 1; i > 0; i--) {          // Fisher-Yates, deterministic seed
            int j = lcg() % (i + 1);
            int t = order[i]; order[i] = order[j]; order[j] = t;
        }
        for (int k = 0; k < s_ncfg; k++) run_config(rep, s_cfgs[order[k]]);
        printf("REP_DONE,%d\n", rep);
    }
    printf("DONE\n");
    for (;;) vTaskDelay(pdMS_TO_TICKS(1000));
}
