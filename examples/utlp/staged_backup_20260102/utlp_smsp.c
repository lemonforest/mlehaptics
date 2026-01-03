/**
 * @file utlp_smsp.c
 * @brief SMSP - Synchronized Multimodal Score Protocol Implementation
 *
 * This is the "what" layer of the Protocol Trinity, implementing score-driven
 * actuator control using atomic time from UTLP.
 *
 * @see utlp_smsp.h for API documentation
 * @see src/pattern_playback.c for production SMSP reference
 * @date 2025-12-31
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "utlp_smsp.h"
#include "utlp_hal.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <string.h>

/*============================================================================
 * LOGGING TAG
 *==========================================================================*/

static const char *TAG = "SMSP";

/*============================================================================
 * MODULE STATE (Static Allocation - JPL Compliant)
 *==========================================================================*/

/** @brief Playback state (single instance) */
static smsp_playback_state_t s_state = {0};

/** @brief Sync semaphore - released when UTLP sync complete */
static utlp_hal_semaphore_t s_sync_semaphore = NULL;

/** @brief Module initialized flag */
static bool s_initialized = false;

/** @brief Current pattern name (for logging) */
static const char* s_pattern_name = "none";

/*============================================================================
 * BUILT-IN PATTERN CATALOG (Static Segment Data)
 *==========================================================================*/

/**
 * @brief BLINK_1HZ - Simple 1Hz square wave
 *
 * Matches the legacy run_physics() behavior exactly:
 * - 1 second period
 * - 50% duty cycle (500ms ON, 500ms OFF)
 * - No interpolation
 */
static const smsp_score_line_t s_blink_1hz_lines[] = {
    /* time_offset_us,  transition,  actuator, duty, freq, flags */
    {       0,             0,          0,      100,   0,    SMSP_FLAG_INTERP_STEP },  /* LED ON */
    {  500000,             0,          0,        0,   0,    SMSP_FLAG_INTERP_STEP },  /* LED OFF */
};
#define BLINK_1HZ_LINE_COUNT (sizeof(s_blink_1hz_lines) / sizeof(smsp_score_line_t))
#define BLINK_1HZ_DURATION_US 1000000  /* 1 second */

/**
 * @brief BREATHE - Smooth 2-second fade cycle
 *
 * Demonstrates SMSP interpolation capability:
 * - 2 second period
 * - Linear fade from 0% to 100% over 1 second
 * - Linear fade from 100% to 0% over 1 second
 */
static const smsp_score_line_t s_breathe_lines[] = {
    /* time_offset_us,  transition,  actuator, duty, freq, flags */
    {       0,           250,          0,        0,   0,    SMSP_FLAG_INTERP_LINEAR },  /* Start at 0% */
    { 1000000,           250,          0,      100,   0,    SMSP_FLAG_INTERP_LINEAR },  /* Fade to 100% */
    { 2000000,           250,          0,        0,   0,    SMSP_FLAG_INTERP_LINEAR },  /* Fade to 0% */
};
#define BREATHE_LINE_COUNT (sizeof(s_breathe_lines) / sizeof(smsp_score_line_t))
#define BREATHE_DURATION_US 2000000  /* 2 seconds */

/**
 * @brief EMERGENCY - SAE J845-style flash pattern
 *
 * Three-phase emergency vehicle simulation:
 * - Phase 1: Double flash
 * - Phase 2: Pause
 * - Phase 3: Double flash
 * - 1 second total cycle
 */
static const smsp_score_line_t s_emergency_lines[] = {
    /* time_offset_us,  transition,  actuator, duty, freq, flags */
    {       0,             0,          0,      100,   0,    SMSP_FLAG_INTERP_STEP },  /* Flash 1 ON */
    {   50000,             0,          0,        0,   0,    SMSP_FLAG_INTERP_STEP },  /* OFF */
    {  100000,             0,          0,      100,   0,    SMSP_FLAG_INTERP_STEP },  /* Flash 2 ON */
    {  150000,             0,          0,        0,   0,    SMSP_FLAG_INTERP_STEP },  /* OFF */
    {  500000,             0,          0,      100,   0,    SMSP_FLAG_INTERP_STEP },  /* Flash 3 ON */
    {  550000,             0,          0,        0,   0,    SMSP_FLAG_INTERP_STEP },  /* OFF */
    {  600000,             0,          0,      100,   0,    SMSP_FLAG_INTERP_STEP },  /* Flash 4 ON */
    {  650000,             0,          0,        0,   0,    SMSP_FLAG_INTERP_STEP },  /* OFF */
};
#define EMERGENCY_LINE_COUNT (sizeof(s_emergency_lines) / sizeof(smsp_score_line_t))
#define EMERGENCY_DURATION_US 1000000  /* 1 second */

/*============================================================================
 * INTERNAL HELPERS
 *==========================================================================*/

/**
 * @brief Find score line for given time offset
 *
 * @param time_us Current time in pattern (0 to pattern duration)
 * @return Line index, or -1 if not found
 */
static int find_line_for_time(uint32_t time_us)
{
    if (s_state.header.line_count == 0) {
        return -1;
    }

    /* Linear search (patterns are small, typically < 16 lines) */
    for (int i = s_state.header.line_count - 1; i >= 0; i--) {
        if (s_state.lines[i].time_offset_us <= time_us) {
            return i;
        }
    }
    return 0;  /* Default to first line */
}

/**
 * @brief Interpolate between two duty cycle values
 *
 * @param from Start duty (0-100)
 * @param to End duty (0-100)
 * @param progress Progress 0-255 (0=from, 255=to)
 * @return Interpolated duty (0-100)
 */
static uint8_t interpolate_duty(uint8_t from, uint8_t to, uint8_t progress)
{
    int16_t diff = (int16_t)to - (int16_t)from;
    return (uint8_t)(from + (diff * progress) / 255);
}

/**
 * @brief Calculate current duty cycle with interpolation
 *
 * @param elapsed_us Time since pattern start (already looped if applicable)
 * @return Duty cycle 0-100
 */
static uint8_t calculate_duty(uint32_t elapsed_us)
{
    int line_idx = find_line_for_time(elapsed_us);
    if (line_idx < 0) {
        return 0;
    }

    const smsp_score_line_t *line = &s_state.lines[line_idx];
    uint8_t interp_type = line->flags & SMSP_FLAG_INTERP_MASK;

    /* Step interpolation (or no transition time) - just return target */
    if (interp_type == SMSP_FLAG_INTERP_STEP || line->transition_ms_x4 == 0) {
        return line->duty_pct;
    }

    /* Calculate transition duration (×4 scaling) */
    uint32_t transition_us = (uint32_t)line->transition_ms_x4 * 4 * 1000;  /* ms to us */
    uint32_t time_in_line = elapsed_us - line->time_offset_us;

    /* If past transition, use target value */
    if (time_in_line >= transition_us) {
        return line->duty_pct;
    }

    /* Get previous line's duty (or 0 if first line) */
    uint8_t prev_duty = 0;
    if (line_idx > 0) {
        prev_duty = s_state.lines[line_idx - 1].duty_pct;
    }

    /* Calculate progress (0-255) */
    uint8_t progress = (uint8_t)((time_in_line * 255) / transition_us);

    /* Linear interpolation */
    return interpolate_duty(prev_duty, line->duty_pct, progress);
}

/**
 * @brief Execute one pattern tick
 *
 * Called at SMSP_TICK_INTERVAL_MS rate. Calculates current duty
 * from atomic time and applies to actuator.
 */
static void execute_tick(void)
{
    if (!s_state.playing) {
        return;
    }

    /* Get current atomic time */
    uint64_t atomic_now = utlp_hal_get_atomic_time_us();

    /* Calculate elapsed time in pattern */
    int64_t elapsed_signed = (int64_t)(atomic_now - s_state.header.born_at_us);
    if (elapsed_signed < 0) {
        /* Pattern hasn't started yet (future start time) */
        return;
    }

    uint64_t elapsed_us = (uint64_t)elapsed_signed;
    uint32_t pattern_duration = s_state.header.duration_us;

    if (pattern_duration == 0) {
        return;
    }

    /* Handle looping */
    uint32_t position_us;
    if (s_state.header.flags & SMSP_PATTERN_FLAG_LOOP) {
        position_us = (uint32_t)(elapsed_us % pattern_duration);
    } else {
        if (elapsed_us >= pattern_duration) {
            /* Non-looping pattern complete */
            s_state.playing = false;
            utlp_hal_set_actuator_phase(UTLP_ACTUATOR_MAIN, 1000, 0.0f, 0.0f);
            utlp_hal_log_info(TAG, "Pattern '%s' complete", s_pattern_name);
            return;
        }
        position_us = (uint32_t)elapsed_us;
    }

    /* Calculate duty and apply */
    uint8_t duty = calculate_duty(position_us);

    /* Apply to actuator (frequency=1000Hz for smooth PWM, phase=0) */
    utlp_hal_set_actuator_phase(UTLP_ACTUATOR_MAIN, 1000, 0.0f, (float)duty);
}

/*============================================================================
 * PUBLIC API
 *==========================================================================*/

void smsp_init(void)
{
    if (s_initialized) {
        return;
    }

    /* Clear state */
    memset(&s_state, 0, sizeof(s_state));

    /* Create sync semaphore (binary, starts empty) */
    s_sync_semaphore = utlp_hal_semaphore_create(1, 0);
    if (s_sync_semaphore == NULL) {
        utlp_hal_log_error(TAG, "Failed to create sync semaphore");
        return;
    }

    s_initialized = true;
    s_pattern_name = "none";

    utlp_hal_log_info(TAG, "SMSP initialized (tick=%dms, max_lines=%d)",
                      SMSP_TICK_INTERVAL_MS, SMSP_MAX_SCORE_LINES);
}

void smsp_notify_sync_ready(void)
{
    if (s_sync_semaphore != NULL && !s_state.sync_ready) {
        s_state.sync_ready = true;
        utlp_hal_semaphore_give(s_sync_semaphore);
        utlp_hal_log_info(TAG, "UTLP sync ready - SMSP unlocked");
    }
}

int smsp_load_builtin(smsp_builtin_pattern_t id)
{
    if (!s_initialized) {
        return -1;
    }

    /* Stop any current playback */
    smsp_stop();

    const smsp_score_line_t *src_lines = NULL;
    uint8_t line_count = 0;
    uint32_t duration_us = 0;

    switch (id) {
        case SMSP_PATTERN_BLINK_1HZ:
            src_lines = s_blink_1hz_lines;
            line_count = BLINK_1HZ_LINE_COUNT;
            duration_us = BLINK_1HZ_DURATION_US;
            s_pattern_name = "BLINK_1HZ";
            break;

        case SMSP_PATTERN_BREATHE:
            src_lines = s_breathe_lines;
            line_count = BREATHE_LINE_COUNT;
            duration_us = BREATHE_DURATION_US;
            s_pattern_name = "BREATHE";
            break;

        case SMSP_PATTERN_EMERGENCY:
            src_lines = s_emergency_lines;
            line_count = EMERGENCY_LINE_COUNT;
            duration_us = EMERGENCY_DURATION_US;
            s_pattern_name = "EMERGENCY";
            break;

        default:
            utlp_hal_log_error(TAG, "Unknown pattern ID: %d", id);
            return -1;
    }

    /* Validate line count */
    if (line_count > SMSP_MAX_SCORE_LINES) {
        utlp_hal_log_error(TAG, "Pattern too large: %d lines (max %d)",
                          line_count, SMSP_MAX_SCORE_LINES);
        return -1;
    }

    /* Copy lines to state buffer */
    memcpy(s_state.lines, src_lines, line_count * sizeof(smsp_score_line_t));

    /* Set up header */
    s_state.header.born_at_us = 0;  /* Will be set on start */
    s_state.header.duration_us = duration_us;
    s_state.header.line_count = line_count;
    s_state.header.flags = SMSP_PATTERN_FLAG_LOOP;

    s_state.current_line = 0;
    s_state.playing = false;

    utlp_hal_log_info(TAG, "Loaded pattern '%s' (%d lines, %lu ms)",
                      s_pattern_name, line_count, (unsigned long)(duration_us / 1000));

    return 0;
}

int smsp_start(uint64_t start_time_us)
{
    if (!s_initialized || s_state.header.line_count == 0) {
        utlp_hal_log_error(TAG, "Cannot start: %s",
                          !s_initialized ? "not initialized" : "no pattern loaded");
        return -1;
    }

    /* If start_time is 0, start now */
    if (start_time_us == 0) {
        start_time_us = utlp_hal_get_atomic_time_us();
    }

    s_state.header.born_at_us = start_time_us;
    s_state.current_line = 0;
    s_state.playing = true;

    utlp_hal_log_info(TAG, "Pattern '%s' started (born_at=%llu us)",
                      s_pattern_name, (unsigned long long)start_time_us);

    return 0;
}

int smsp_stop(void)
{
    if (s_state.playing) {
        s_state.playing = false;

        /* Turn off actuator */
        utlp_hal_set_actuator_phase(UTLP_ACTUATOR_MAIN, 1000, 0.0f, 0.0f);

        utlp_hal_log_info(TAG, "Pattern '%s' stopped", s_pattern_name);
    }
    return 0;
}

bool smsp_is_playing(void)
{
    return s_state.playing;
}

const char* smsp_get_pattern_name(void)
{
    return s_pattern_name;
}

void smsp_task(void *pvParameters)
{
    (void)pvParameters;

    utlp_hal_log_info(TAG, "SMSP task started - waiting for UTLP sync...");

    /* Wait for UTLP synchronization */
    if (s_sync_semaphore != NULL) {
        /* Block indefinitely until sync ready */
        if (!utlp_hal_semaphore_take(s_sync_semaphore, UINT32_MAX)) {
            utlp_hal_log_error(TAG, "Failed to wait for sync semaphore");
            vTaskDelete(NULL);
            return;
        }
    }

    utlp_hal_log_info(TAG, "SMSP sync received - loading default pattern");

    /* Load default pattern */
    if (smsp_load_builtin(SMSP_PATTERN_BLINK_1HZ) != 0) {
        utlp_hal_log_error(TAG, "Failed to load default pattern");
        vTaskDelete(NULL);
        return;
    }

    /* Start playback */
    if (smsp_start(0) != 0) {
        utlp_hal_log_error(TAG, "Failed to start pattern playback");
        vTaskDelete(NULL);
        return;
    }

    utlp_hal_log_info(TAG, "SMSP playback loop started (tick=%dms)", SMSP_TICK_INTERVAL_MS);

    /* Main pattern execution loop */
    while (1) {
        execute_tick();
        vTaskDelay(pdMS_TO_TICKS(SMSP_TICK_INTERVAL_MS));
    }
}

/*============================================================================
 * TEST SUPPORT (HOST_BUILD only)
 *==========================================================================*/

#ifdef HOST_BUILD
void smsp_reset_for_testing(void)
{
    /* Stop any active playback */
    smsp_stop();

    /* Clear all state */
    memset(&s_state, 0, sizeof(s_state));

    /* Reset initialization flag */
    s_initialized = false;

    /* Reset pattern name */
    s_pattern_name = "none";

    /* Note: Semaphore is not destroyed/recreated - tests should handle this */
}
#endif
