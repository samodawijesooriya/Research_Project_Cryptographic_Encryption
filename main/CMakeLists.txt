# See the build system documentation in IDF programming guide
# for more information about component CMakeLists.txt files.

idf_component_register(
    SRCS
        "main.c"
        "run_trial.c"
        "encrypt_measure.c"
        "power_monitor.c"
        "ina219.c"
        "wifi_stubs.c"
        "ascon128.c"
    INCLUDE_DIRS "."
    REQUIRES
        driver
        heap
        esp_timer
    PRIV_REQUIRES
        esp_wifi
        esp_event
        esp_netif
        nvs_flash
        esp_hw_support
        mbedtls
        freertos
        mqtt
        json
)