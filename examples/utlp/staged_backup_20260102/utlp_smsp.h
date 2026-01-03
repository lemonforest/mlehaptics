/**
 * @file utlp_smsp.h
 * @brief SMSP - Synchronized Multimodal Score Protocol for UTLP
 *
 * @section overview Overview
 *
 * SMSP is the "what" layer of the Protocol Trinity (UTLP=when, RFIP=where, SMSP=what).
 * It implements score-driven actuator control using atomic time from UTLP.
 *
 * This is a simplified implementation for the UTLP example, demonstrating the
 * clean separation between protocol layer (time sync) and application layer
 * (pattern playback). For the full production SMSP implementation with bilateral
 * L/R zones and sheet composition, see src/pattern_playback.h.
 *
 * @section architecture Architecture
 *
 * The Protocol Trinity (Prior Art Section 4):
 * @code
 *   ┌─────────────────────────────────────────────────────────────────┐
 *   │  UTLP PROTOCOL LAYER (utlp.c)                                  │
 *   │  - Beacons, trust, stratum                                      │
 *   │  - Calls smsp_notify_sync_ready() once synced                   │
 *   └──────────────────────────┬──────────────────────────────────────┘
 *                              │ sync semaphore
 *                              ↓
 *   ┌─────────────────────────────────────────────────────────────────┐
 *   │  SMSP APPLICATION LAYER (utlp_smsp.c)                          │
 *   │  - FreeRTOS task: smsp_task()                                   │
 *   │  - Pattern execution engine                                      │
 *   │  - Interpolation between score lines                            │
 *   │  - Calls utlp_hal_get_atomic_time_us() each tick               │
 *   │  - Calls utlp_hal_set_actuator_phase() for LED                 │
 *   └─────────────────────────────────────────────────────────────────┘
 * @endcode
 *
 * @section score_format Score Format
 *
 * Each score line specifies an actuator state at a point in time:
 * - time_offset_us: When to execute (relative to pattern start)
 * - duty_pct: Duty cycle 0-100%
 * - transition_ms_x4: Fade duration (×4 scaling = 0-1020ms resolution)
 * - flags: Interpolation type and sync markers
 *
 * @section patterns Built-in Patterns
 *
 * | Pattern | Description |
 * |---------|-------------|
 * | BLINK_1HZ | Simple 1Hz square wave (matches legacy run_physics) |
 * | BREATHE | Smooth 2-second fade in/out (demonstrates interpolation) |
 * | EMERGENCY | SAE J845 emergency vehicle flash pattern |
 *
 * @section reference Reference Implementation
 *
 * This is adapted from the production SMSP in src/pattern_playback.h/c.
 * Key differences:
 * - Single actuator (vs bilateral L/R zones)
 * - Simplified interpolation
 * - No sheet composition (patterns are self-contained)
 *
 * @see src/pattern_playback.h - Production SMSP implementation
 * @see docs/Connectionless_Distributed_Timing_Prior_Art.md §4.5 - SMSP specification
 * @see examples/utlp/utlp_hal.h - HAL interface for time/actuators
 *
 * @version 1.0.0
 * @date 2025-12-31
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/*============================================================================
 * CONSTANTS
 *==========================================================================*/

/** @brief Maximum score lines per pattern (static allocation) */
#define SMSP_MAX_SCORE_LINES    16

/** @brief Task stack size in bytes */
#define SMSP_TASK_STACK_SIZE    4096

/** @brief Task priority (same as UTLP main loop) */
#define SMSP_TASK_PRIORITY      5

/** @brief Tick interval for pattern execution (10ms = 100Hz) */
#define SMSP_TICK_INTERVAL_MS   10

/*============================================================================
 * SCORE LINE FLAGS
 *==========================================================================*/

/** @brief Interpolation type flags (bits 0-1) */
#define SMSP_FLAG_INTERP_STEP   0x00  /**< Step change (no interpolation) */
#define SMSP_FLAG_INTERP_LINEAR 0x01  /**< Linear interpolation */
#define SMSP_FLAG_INTERP_EASE   0x02  /**< Ease-in-out (cosine) */
#define SMSP_FLAG_INTERP_MASK   0x03  /**< Interpolation bits mask */

/** @brief Sync marker flag (bit 7) */
#define SMSP_FLAG_SYNC_POINT    0x80  /**< Mark as synchronization point */

/*============================================================================
 * PATTERN FLAGS
 *==========================================================================*/

/** @brief Pattern loops continuously */
#define SMSP_PATTERN_FLAG_LOOP  0x01

/*============================================================================
 * TYPES
 *==========================================================================*/

/**
 * @brief Score line - single actuator state at a point in time
 *
 * This is a simplified version of bilateral_segment_t from production SMSP.
 * Packed struct for consistent memory layout (10 bytes).
 *
 * @note time_offset_us is relative to pattern start, not absolute time.
 * The SMSP task adds the pattern's born_at_us to get absolute time.
 */
typedef struct __attribute__((packed)) {
    uint32_t time_offset_us;      /**< When to execute (relative to pattern start) */
    uint16_t transition_ms_x4;    /**< Fade duration (×4 scaling = 0-1020ms) */
    uint8_t  actuator_id;         /**< UTLP_ACTUATOR_MAIN (0) */
    uint8_t  duty_pct;            /**< Duty cycle 0-100 */
    uint8_t  frequency_hz_div10;  /**< Frequency / 10 (0 = DC, 100 = 1kHz) */
    uint8_t  flags;               /**< Interpolation + sync flags */
} smsp_score_line_t;              /* 10 bytes */

/**
 * @brief Pattern header - metadata for score playback
 *
 * Simplified from sheet_header_t (no CRC, no mode_id).
 * Packed struct for consistent memory layout (14 bytes).
 */
typedef struct __attribute__((packed)) {
    uint64_t born_at_us;          /**< LWW-CRDT timestamp (pattern start time) */
    uint32_t duration_us;         /**< Total pattern duration in microseconds */
    uint8_t  line_count;          /**< Number of score lines (1-SMSP_MAX_SCORE_LINES) */
    uint8_t  flags;               /**< SMSP_PATTERN_FLAG_* */
} smsp_pattern_header_t;          /* 14 bytes */

/**
 * @brief Built-in pattern identifiers
 *
 * These patterns are compiled into the firmware and always available.
 */
typedef enum {
    SMSP_PATTERN_BLINK_1HZ = 0,   /**< Default: matches current run_physics() */
    SMSP_PATTERN_BREATHE,         /**< Smooth fade in/out (2s cycle) */
    SMSP_PATTERN_EMERGENCY,       /**< SAE J845 emergency vehicle pattern */
    SMSP_PATTERN_COUNT            /**< Number of built-in patterns */
} smsp_builtin_pattern_t;

/**
 * @brief Playback state (internal use)
 */
typedef struct {
    smsp_pattern_header_t header;                  /**< Current pattern metadata */
    smsp_score_line_t lines[SMSP_MAX_SCORE_LINES]; /**< Score lines buffer */
    uint8_t current_line;                          /**< Index of current line */
    bool playing;                                  /**< Playback active flag */
    bool sync_ready;                               /**< UTLP sync complete flag */
} smsp_playback_state_t;

/*============================================================================
 * PUBLIC API
 *==========================================================================*/

/**
 * @brief Initialize SMSP subsystem
 *
 * Creates sync semaphore and initializes playback state.
 * Must be called before smsp_task is started.
 */
void smsp_init(void);

/**
 * @brief Notify SMSP that UTLP synchronization is complete
 *
 * Called by utlp.c when first beacon is adopted.
 * Releases the sync semaphore, allowing SMSP task to start playback.
 */
void smsp_notify_sync_ready(void);

/**
 * @brief Load a built-in pattern
 *
 * @param id Pattern identifier from smsp_builtin_pattern_t
 * @return 0 on success, -1 on invalid pattern
 */
int smsp_load_builtin(smsp_builtin_pattern_t id);

/**
 * @brief Start pattern playback
 *
 * Begins playback at the specified atomic time. If start_time_us is 0,
 * playback starts immediately at the current atomic time.
 *
 * @param start_time_us Absolute atomic time to start, or 0 for "now"
 * @return 0 on success, -1 if no pattern loaded
 */
int smsp_start(uint64_t start_time_us);

/**
 * @brief Stop pattern playback
 *
 * Stops playback and turns off the actuator.
 *
 * @return 0 on success
 */
int smsp_stop(void);

/**
 * @brief Check if playback is active
 *
 * @return true if currently playing
 */
bool smsp_is_playing(void);

/**
 * @brief SMSP FreeRTOS task entry point
 *
 * Main task that:
 * 1. Waits for UTLP sync (via semaphore)
 * 2. Loads default pattern (BLINK_1HZ)
 * 3. Executes pattern tick at SMSP_TICK_INTERVAL_MS
 *
 * @param pvParameters Unused (for FreeRTOS compatibility)
 */
void smsp_task(void *pvParameters);

/**
 * @brief Get current pattern name (for logging)
 *
 * @return Human-readable pattern name string
 */
const char* smsp_get_pattern_name(void);

#ifdef HOST_BUILD
/**
 * @brief Reset SMSP state for testing
 *
 * Forcibly resets all SMSP state including the initialized flag.
 * Only available in host builds for unit testing.
 */
void smsp_reset_for_testing(void);
#endif

#ifdef __cplusplus
}
#endif
