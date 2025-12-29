/**
 * @file utlp_main_esp32c6.c
 * @brief ESP32-C6 Platform Entry Point
 *
 * This file contains the ONLY platform-specific entry point (app_main).
 * To port UTLP to another platform, replace this file:
 *
 *   - ESP-IDF:  void app_main(void) { utlp_app_run(); }
 *   - Arduino:  void setup() { utlp_app_run(); } void loop() {}
 *   - Linux:    int main() { utlp_app_run(); return 0; }
 *
 * The entire UTLP protocol logic lives in utlp_skeleton.c,
 * which is platform-agnostic pure C.
 *
 * @version 1.0.0
 * @date 2025-12-28
 */

#include "utlp_hal.h"

/**
 * @brief ESP-IDF FreeRTOS entry point
 *
 * This is the standard ESP-IDF entry function.
 * It simply delegates to the platform-agnostic UTLP application.
 */
void app_main(void)
{
    utlp_app_run();
}
