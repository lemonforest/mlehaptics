/**
 * @file utlp_main_esp32.c
 * @brief ESP32 Platform Entry Point - UTLP v2 Frontier Algorithm
 *
 * This file contains the ONLY platform-specific entry point (app_main).
 * The entire UTLP protocol logic lives in utlp.c, which is platform-agnostic.
 *
 * @version 2.2.0 - ESP32-focused (forked from skeleton)
 * @date 2025-12-29
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
