idf_component_register(
    SRCS
        "main.c"
        "../../main/ascon128.c"      # reuse the exact ASCON implementation from the original benchmark
    INCLUDE_DIRS "." "../../main"
    REQUIRES driver esp_timer mbedtls freertos
)
