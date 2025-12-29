/**
 * @file utlp_main_c64.c
 * @brief Commodore 64 Platform Entry Point
 *
 * This file contains the ONLY platform-specific entry point for C64.
 * To port UTLP to another platform, replace this file:
 *
 *   - ESP-IDF:  void app_main(void) { utlp_app_run(); }
 *   - Arduino:  void setup() { utlp_app_run(); } void loop() {}
 *   - Linux:    int main() { utlp_app_run(); return 0; }
 *   - C64:      int main(void) { utlp_app_run(); return 0; }  <-- THIS FILE
 *
 * The entire UTLP protocol logic lives in utlp_skeleton.c,
 * which is platform-agnostic pure C.
 *
 * @version 1.0.0
 * @date 2025-12-28
 */

/* Include the LOCAL transformed header (C89-compatible) */
#include "utlp_hal.h"

/**
 * @brief C64 standard C entry point
 *
 * cc65 uses standard main() as the entry function.
 * It simply delegates to the platform-agnostic UTLP application.
 *
 * @return 0 (never returns - UTLP runs forever)
 */
int main(void)
{
    utlp_app_run();
    return 0;  /* Never reached */
}
