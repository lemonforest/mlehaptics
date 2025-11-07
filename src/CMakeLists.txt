# EMDR Bilateral Stimulation Device - Main Component
# Component-level CMakeLists.txt for ESP-IDF
#
# This tells ESP-IDF how to build the src/ directory

idf_component_register(
    SRCS "main.c"
    INCLUDE_DIRS "."
    REQUIRES
        freertos
        esp_system
        esp_common
        driver
        nvs_flash
        bt
)
