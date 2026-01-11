/**
 * @file utlp_smsp.c
 * @brief SMSP - Synchronized Multimodal Score Protocol - Phase 0 Stub
 *
 * PHASE 0 STUB: Minimal implementation for LED heartbeat.
 * Full pattern engine will be added in Phase 5.
 *
 * @version 0.0.1 (Phase 0 Stub)
 * @date 2026-01-08
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "utlp_smsp.h"
#include "utlp_hal.h"

#ifdef ESP_PLATFORM
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "freertos/task.h"
#else
/* Native test stubs */
typedef void* SemaphoreHandle_t;
#define xSemaphoreCreateBinary() NULL
#define xSemaphoreTake(s, t) 1
#define xSemaphoreGive(s)
#define portMAX_DELAY 0xFFFFFFFF
#define vTaskDelay(t)
#define pdMS_TO_TICKS(t) (t)
#endif

static const char *TAG = "SMSP_PHASE0";

/*============================================================================
 * STUB STATE
 *==========================================================================*/

static struct {
    bool initialized;
    bool sync_ready;
    bool playing;
    smsp_builtin_pattern_t current_pattern;
    SemaphoreHandle_t sync_sem;
} s_smsp_state = {0};

/*============================================================================
 * PUBLIC API STUBS
 *==========================================================================*/

void smsp_init(void)
{
    if (s_smsp_state.initialized) {
        return;
    }

#ifdef ESP_PLATFORM
    s_smsp_state.sync_sem = xSemaphoreCreateBinary();
#endif
    s_smsp_state.sync_ready = false;
    s_smsp_state.playing = false;
    s_smsp_state.current_pattern = SMSP_PATTERN_BLINK_1HZ;
    s_smsp_state.initialized = true;

    utlp_hal_log_info(TAG, "Phase 0 stub: smsp_init()");
}

void smsp_notify_sync_ready(void)
{
    s_smsp_state.sync_ready = true;

#ifdef ESP_PLATFORM
    if (s_smsp_state.sync_sem != NULL) {
        xSemaphoreGive(s_smsp_state.sync_sem);
    }
#endif

    utlp_hal_log_info(TAG, "Sync ready notification received");
}

int smsp_load_builtin(smsp_builtin_pattern_t id)
{
    if (id >= SMSP_PATTERN_COUNT) {
        return -1;
    }

    s_smsp_state.current_pattern = id;
    return 0;
}

int smsp_start(uint64_t start_time_us)
{
    (void)start_time_us;

    s_smsp_state.playing = true;
    utlp_hal_log_info(TAG, "Pattern playback started");
    return 0;
}

int smsp_stop(void)
{
    s_smsp_state.playing = false;

    /* Turn off actuator */
    utlp_hal_set_actuator_phase(UTLP_ACTUATOR_MAIN, 0, 0, 0);

    utlp_hal_log_info(TAG, "Pattern playback stopped");
    return 0;
}

bool smsp_is_playing(void)
{
    return s_smsp_state.playing;
}

void smsp_task(void *pvParameters)
{
    (void)pvParameters;

    utlp_hal_log_info(TAG, "Phase 0 stub: SMSP task started (waiting for sync)");

#ifdef ESP_PLATFORM
    /* Wait for sync notification */
    if (s_smsp_state.sync_sem != NULL) {
        xSemaphoreTake(s_smsp_state.sync_sem, portMAX_DELAY);
    }
#endif

    utlp_hal_log_info(TAG, "SMSP task: sync ready, starting pattern");

    /* Load and start default pattern */
    smsp_load_builtin(SMSP_PATTERN_BLINK_1HZ);
    smsp_start(0);

    /* Phase 0: Simple 1Hz blink using HAL time */
    while (s_smsp_state.playing) {
        uint64_t now_us = utlp_hal_get_micros();
        uint32_t phase_ms = (now_us / 1000) % 1000;

        /* 1Hz blink: ON for 500ms, OFF for 500ms */
        uint8_t duty = (phase_ms < 500) ? 100 : 0;

        utlp_hal_set_actuator_phase(UTLP_ACTUATOR_MAIN, 1000, 0, duty);

#ifdef ESP_PLATFORM
        vTaskDelay(pdMS_TO_TICKS(SMSP_TICK_INTERVAL_MS));
#else
        utlp_hal_yield();
#endif
    }

    utlp_hal_log_info(TAG, "SMSP task exiting");
}

const char* smsp_get_pattern_name(void)
{
    switch (s_smsp_state.current_pattern) {
        case SMSP_PATTERN_BLINK_1HZ: return "BLINK_1HZ";
        case SMSP_PATTERN_BREATHE:   return "BREATHE";
        case SMSP_PATTERN_EMERGENCY: return "EMERGENCY";
        default:                     return "Unknown";
    }
}

#ifdef HOST_BUILD
void smsp_reset_for_testing(void)
{
    s_smsp_state.initialized = false;
    s_smsp_state.sync_ready = false;
    s_smsp_state.playing = false;
}
#endif
