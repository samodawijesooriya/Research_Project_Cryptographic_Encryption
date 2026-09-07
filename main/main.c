// main/main.c
#include <stdio.h>
#include "run_trial.h"
#include "esp_sleep.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "nvs_flash.h"

#define OUTER_LOOP_COUNT   500   // was: for (i = 0; i < 500; i++)
#define INNER_LOOP_COUNT   100   // was: for (j = 1; j <= 100; j++)
#define DEEP_SLEEP_SECONDS 60

extern void wifi_connect(void);
extern void wifi_reconnect(void);

// Survive deep sleep (RTC memory domain). Lost only on a full power-cycle.
RTC_DATA_ATTR static int      rtc_i           = 0;
RTC_DATA_ATTR static int      rtc_j           = 1;
RTC_DATA_ATTR static algo_t   rtc_algo        = ALGO_AES_128_GCM;
RTC_DATA_ATTR static uint8_t  rtc_key[16];
RTC_DATA_ATTR static bool     rtc_initialized = false;

static algo_t select_algorithm(void) {
    // Swap for menuconfig / UART prompt if you need to pick per test run.
    return ALGO_ASCON_128;
}

static void define_key(uint8_t *key_out) {
    for (int b = 0; b < 16; b++) key_out[b] = 0xA0 + b;   // fixed test key
}

// SAVE_PROGRESS(): advances (i, j) to the next payload size / repetition and
// persists it to RTC memory (Fig. 6).
static void save_progress(void) {
    rtc_j++;
    if (rtc_j > INNER_LOOP_COUNT) {
        rtc_j = 1;
        rtc_i++;
    }
    // RTC_DATA_ATTR variables are written back automatically — no explicit
    // flush call is needed, unlike NVS. They just need to still be in scope
    // when esp_deep_sleep_start() is called below.
}

// SLEEP_AND_RESET(): fixed 60-second timer wakeup, then deep sleep (Fig. 7).
static void sleep_until_next_trial(void) {
    esp_sleep_enable_timer_wakeup((uint64_t)DEEP_SLEEP_SECONDS * 1000000ULL);
    esp_deep_sleep_start();       // does not return — chip resets here
}

void app_main(void) {
    esp_sleep_wakeup_cause_t cause = esp_sleep_get_wakeup_cause();
    bool resuming = (cause == ESP_SLEEP_WAKEUP_TIMER) && rtc_initialized;

    esp_err_t nvs_ret = nvs_flash_init();
    if (nvs_ret == ESP_ERR_NVS_NO_FREE_PAGES || nvs_ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        nvs_ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(nvs_ret);
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    if (!resuming) {
        // Cold boot (power-on, or an unexpected reset). Runs exactly once
        // per physical power-cycle. Corresponds to COLD_BOOT_INIT() in Fig. 1.
        rtc_algo = select_algorithm();
        define_key(rtc_key);
        rtc_i = 1;    // fresh ASCON-128 run
        rtc_j = 1;
        rtc_initialized = true;
        wifi_connect();

        if (cause != ESP_SLEEP_WAKEUP_UNDEFINED) {
            printf("WARNING: unexpected reset (cause=%d) — resuming at i=%d j=%d\n",
                   cause, rtc_i, rtc_j);
        }
    } else {
        // Woke from our own deep sleep — resume exactly where we left off.
        // Corresponds to RESUME_BOOT() in Fig. 1.
        wifi_reconnect();
    }

    if (rtc_i < OUTER_LOOP_COUNT) {
        run_trial(rtc_algo, rtc_key, rtc_i, rtc_j);   // exactly one trial this boot
        save_progress();
        sleep_until_next_trial();              // never returns
    } else {
        printf("Measurement sweep complete: %d x %d trials.\n",
               OUTER_LOOP_COUNT, INNER_LOOP_COUNT);
        esp_deep_sleep_start();   // no wake timer configured — HALT_PERMANENTLY()
    }
}