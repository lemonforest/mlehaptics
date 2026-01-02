/**
 * @file test_native_runner.c
 * @brief Entry point for native unit tests
 *
 * This file exists at test/ root to help PlatformIO discover tests.
 * It includes and runs tests from test/unit/ subdirectory.
 *
 * NOTE: We directly include .c files to work around PlatformIO's
 * build system limitations for the native platform.
 */

/* Include source files directly (they're not compiled separately) */
#include "../test/unit/utlp_hal_mock.c"
#include "../examples/utlp/utlp_smsp.c"

/* Include the actual test implementation */
#include "unit/test_utlp_smsp.c"
