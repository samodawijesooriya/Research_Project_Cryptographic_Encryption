// main/wifi_stubs.c
#include <stdio.h>
#include <string.h>
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "mqtt_client.h"
#include "power_monitor.h"
#include "sdkconfig.h"

static const char *TAG = "wifi_stubs";

static EventGroupHandle_t s_wifi_event_group;
#define WIFI_CONNECTED_BIT BIT0

static esp_mqtt_client_handle_t s_mqtt_client = NULL;
static bool s_mqtt_connected = false;
static volatile bool s_mqtt_publish_acked = false;

static void wifi_event_handler(void *arg, esp_event_base_t event_base,
                                int32_t event_id, void *event_data) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        xEventGroupClearBits(s_wifi_event_group, WIFI_CONNECTED_BIT);
        ESP_LOGW(TAG, "Wi-Fi disconnected, retrying...");
        esp_wifi_connect();
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t *event = (ip_event_got_ip_t *)event_data;
        ESP_LOGI(TAG, "Got IP: " IPSTR, IP2STR(&event->ip_info.ip));
        xEventGroupSetBits(s_wifi_event_group, WIFI_CONNECTED_BIT);
    }
}

static void mqtt_event_handler(void *handler_args, esp_event_base_t base,
                                int32_t event_id, void *event_data) {
    switch (event_id) {
        case MQTT_EVENT_CONNECTED:
            s_mqtt_connected = true;
            ESP_LOGI(TAG, "MQTT connected to %s", CONFIG_ESP_MQTT_BROKER_URI);
            break;
        case MQTT_EVENT_DISCONNECTED:
            s_mqtt_connected = false;
            ESP_LOGW(TAG, "MQTT disconnected");
            break;
        case MQTT_EVENT_PUBLISHED:
            s_mqtt_publish_acked = true;
            break;
        default:
            break;
    }
}

// One-time station init: driver bring-up, event handlers, MQTT client create.
// Safe to call again on a resume boot (esp_wifi_start/connect just re-associate).
static void wifi_station_init_and_connect(void) {
    s_wifi_event_group = xEventGroupCreate();

    esp_netif_create_default_wifi_sta();

    wifi_init_config_t init_cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&init_cfg));

    ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, &wifi_event_handler, NULL));
    ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, &wifi_event_handler, NULL));

    wifi_config_t wifi_cfg = {
        .sta = {
            .ssid = CONFIG_ESP_WIFI_SSID,
            .password = CONFIG_ESP_WIFI_PASSWORD,
            .threshold.authmode = WIFI_AUTH_WPA2_PSK,
        },
    };
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_cfg));
    ESP_ERROR_CHECK(esp_wifi_start());

    // Blocks until WIFI_CONNECTED_BIT is set by the IP_EVENT_STA_GOT_IP handler above.
    xEventGroupWaitBits(s_wifi_event_group, WIFI_CONNECTED_BIT, pdFALSE, pdTRUE, portMAX_DELAY);

    esp_mqtt_client_config_t mqtt_cfg = {
        .broker.address.uri = CONFIG_ESP_MQTT_BROKER_URI,
    };
    s_mqtt_client = esp_mqtt_client_init(&mqtt_cfg);
    esp_mqtt_client_register_event(s_mqtt_client, ESP_EVENT_ANY_ID, mqtt_event_handler, NULL);
    esp_mqtt_client_start(s_mqtt_client);

    // Wait briefly for the MQTT_EVENT_CONNECTED callback so the very first
    // report_to_nodered() call after boot doesn't race the TCP handshake.
    for (int waited_ms = 0; !s_mqtt_connected && waited_ms < 5000; waited_ms += 100) {
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}

void wifi_connect(void) {
    wifi_station_init_and_connect();
}

void wifi_reconnect(void) {
    // esp_wifi_start()/connect already re-associate via WIFI_EVENT_STA_START;
    // driver + MQTT client persist across deep sleep only if this is the same
    // boot session, which it isn't (deep sleep resets the chip) -- so a resume
    // boot needs the exact same bring-up as a cold boot.
    wifi_station_init_and_connect();
}

// Blocks until the broker's QoS-1 PUBACK arrives (or times out). Deep sleep
// kills the MQTT task immediately after run_trial() returns, so callers must
// not return until the packet has actually gone out over the wire.
static void wait_for_publish_ack(const char *label) {
    for (int waited_ms = 0; !s_mqtt_publish_acked && waited_ms < 3000; waited_ms += 50) {
        vTaskDelay(pdMS_TO_TICKS(50));
    }
    if (!s_mqtt_publish_acked) {
        ESP_LOGW(TAG, "Timed out waiting for MQTT publish ack for %s", label);
    }
}

void report_trial_start(int i, int j, size_t payload_len, const char *label) {
    if (!s_mqtt_client || !s_mqtt_connected) {
        ESP_LOGW(TAG, "MQTT not connected, dropping trial-start report for %s", label);
        return;
    }

    char payload[160];
    int len = snprintf(payload, sizeof(payload),
        "{"
        "\"event\":\"trial_start\","
        "\"algo\":\"%s\","
        "\"i\":%d,"
        "\"j\":%d,"
        "\"payload_len_bytes\":%u"
        "}",
        label, i, j, (unsigned)payload_len);

    s_mqtt_publish_acked = false;
    esp_mqtt_client_publish(s_mqtt_client, CONFIG_ESP_MQTT_TOPIC_STATS, payload, len, 1, 0);
    wait_for_publish_ack(label);
}

void report_to_nodered(const monitor_ctx_t *ctx, const char *label, int trial_id, size_t payload_len) {
    if (!s_mqtt_client || !s_mqtt_connected) {
        ESP_LOGW(TAG, "MQTT not connected, dropping report for %s", label);
        return;
    }

    int64_t elapsed_us   = ctx->end_time_us - ctx->start_time_us;
    int32_t heap_delta_b = (int32_t)ctx->heap_before - (int32_t)ctx->heap_after;
    int32_t heap_peak_b  = (int32_t)ctx->heap_min_free_before - (int32_t)ctx->heap_min_free_after;
    if (heap_peak_b < 0) heap_peak_b = 0;
    int32_t stack_peak_b = (int32_t)ctx->stack_hwm_free_before - (int32_t)ctx->stack_hwm_free_after;
    if (stack_peak_b < 0) stack_peak_b = 0;
    float   power_delta  = ctx->power_after_mW - ctx->power_before_mW;

    char payload[384];
    int len = snprintf(payload, sizeof(payload),
        "{"
        "\"id\":%d,"
        "\"algo\":\"%s\","
        "\"size\":%u,"
        "\"time_us\":%lld,"
        "\"heap_delta_bytes\":%ld,"
        "\"heap_peak_used_bytes\":%ld,"
        "\"stack_peak_used_bytes\":%ld,"
        "\"stack_used_bytes\":%lu,"
        "\"current_before_mA\":%.3f,"
        "\"current_after_mA\":%.3f,"
        "\"power_before_mW\":%.3f,"
        "\"power_after_mW\":%.3f,"
        "\"power_delta_mW\":%.3f"
        "}",
        trial_id, label, (unsigned)payload_len, elapsed_us, heap_delta_b, heap_peak_b, stack_peak_b,
        (unsigned long)ctx->stack_used_bytes,
        ctx->current_before_mA, ctx->current_after_mA,
        ctx->power_before_mW, ctx->power_after_mW,
        power_delta);

    s_mqtt_publish_acked = false;
    esp_mqtt_client_publish(s_mqtt_client, CONFIG_ESP_MQTT_TOPIC, payload, len, 1, 0);
    wait_for_publish_ack(label);
}
