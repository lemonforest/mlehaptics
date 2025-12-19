/**
 * @file pattern_playback.h
 * @brief Bilateral Pattern Playback - "Sheet Music" Architecture (AD047)
 *
 * Implements deterministic pattern playback for bilateral stimulation:
 * - Sheet header with timestamp-based versioning (LWW-CRDT)
 * - Bilateral segments with LEFT/RIGHT outputs per time offset
 * - Zone-aware execution (each device reads its zone's column)
 * - Hardcoded patterns for Mode 5/6 (lightbar showcase)
 *
 * Key Design Principles:
 * - "Sheet Music" paradigm: Both devices load identical pattern, execute locally
 * - Timestamp as version: born_at_us serves as implicit LWW-CRDT version
 * - Zone independence: L/R columns allow bilateral coordination
 * - Static allocation: All memory pre-allocated (JPL compliance)
 *
 * @see docs/bilateral_pattern_playback_architecture.md
 * @see docs/adr/0047-scheduled-pattern-playback.md
 * @date December 2025
 * @author Claude Code (Anthropic)
 */

#ifndef PATTERN_PLAYBACK_H
#define PATTERN_PLAYBACK_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"
#include "zone_config.h"

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// PATTERN LIMITS
// ============================================================================

/**
 * @brief Maximum number of segments per pattern
 *
 * 64 segments * 11 bytes = 704 bytes pattern data
 * Fits comfortably in RAM while allowing complex patterns
 */
#define PATTERN_MAX_SEGMENTS    64

/**
 * @brief Maximum pattern duration in milliseconds
 *
 * 65535ms = 65.5 seconds per pattern iteration
 * Longer patterns can loop
 */
#define PATTERN_MAX_DURATION_MS 65535

// ============================================================================
// SHEET HEADER STRUCTURE
// ============================================================================

/**
 * @brief Sheet header flags
 */
typedef enum {
    SHEET_FLAG_LOOPING  = (1 << 0),  /**< Pattern loops to start after last segment */
    SHEET_FLAG_LOCKED   = (1 << 1),  /**< Pattern cannot be modified (playing) */
    SHEET_FLAG_MOTOR    = (1 << 2),  /**< Pattern includes motor outputs */
    SHEET_FLAG_LED      = (1 << 3),  /**< Pattern includes LED outputs */
} sheet_flags_t;

/**
 * @brief Sheet header - pattern metadata and versioning
 *
 * The sheet header provides:
 * - Timestamp-based versioning (born_at_us as LWW-CRDT version)
 * - Content integrity (CRC32 of segment data)
 * - Pattern metadata (segment count, mode, flags)
 *
 * Size: 16 bytes (packed)
 */
typedef struct __attribute__((packed)) {
    uint64_t born_at_us;      /**< Synchronized time when sheet was created (VERSION) */
    uint32_t content_crc;     /**< CRC32 of pattern segment data */
    uint16_t segment_count;   /**< Number of segments in pattern (max 64) */
    uint8_t  mode_id;         /**< Human-readable mode reference (5=lightbar, 6=custom) */
    uint8_t  flags;           /**< Sheet flags (looping, locked, etc.) */
} sheet_header_t;

// ============================================================================
// BILATERAL SEGMENT STRUCTURE
// ============================================================================

/**
 * @brief Segment flags
 */
typedef enum {
    SEG_FLAG_SYNC_POINT = (1 << 0),  /**< Synchronization checkpoint */
    SEG_FLAG_EASE_IN    = (1 << 1),  /**< Ease-in transition */
    SEG_FLAG_EASE_OUT   = (1 << 2),  /**< Ease-out transition */
    SEG_FLAG_EASE_BOTH  = (1 << 3),  /**< Ease in and out */
} segment_flags_t;

/**
 * @brief Bilateral segment - single point in pattern timeline
 *
 * Each segment defines outputs for BOTH zones at a specific time offset.
 * Devices execute their zone's column (L_ or R_ fields).
 *
 * Timing:
 * - time_offset_ms: When to execute (0-65535ms from pattern start)
 * - transition_ms_x4: Fade duration (×4 scaling = 0-1020ms)
 *
 * Outputs per zone:
 * - color: 16-color palette index (0-15)
 * - brightness: Perceptual brightness (0-100%, CIE 1931 applied)
 * - motor: Motor intensity (0-100%, 0=LED-only)
 *
 * Size: 11 bytes (packed)
 */
typedef struct __attribute__((packed)) {
    uint16_t time_offset_ms;    /**< When to execute (0-65535ms from pattern start) */
    uint8_t  transition_ms_x4;  /**< Fade duration (×4 scaling = 0-1020ms) */
    uint8_t  flags;             /**< Segment flags (sync_point, easing) */
    uint8_t  waveform_id;       /**< Index into fade curve LUT (future use) */

    // Zone LEFT (port) outputs
    uint8_t  L_color;           /**< LEFT zone: Palette index 0-15 */
    uint8_t  L_brightness;      /**< LEFT zone: Brightness 0-100% */
    uint8_t  L_motor;           /**< LEFT zone: Motor intensity 0-100% */

    // Zone RIGHT (starboard) outputs
    uint8_t  R_color;           /**< RIGHT zone: Palette index 0-15 */
    uint8_t  R_brightness;      /**< RIGHT zone: Brightness 0-100% */
    uint8_t  R_motor;           /**< RIGHT zone: Motor intensity 0-100% */
} bilateral_segment_t;

// ============================================================================
// PATTERN BUFFER STRUCTURE
// ============================================================================

/**
 * @brief Pattern buffer - holds active pattern in RAM
 *
 * Static allocation for JPL compliance.
 * PWA uploads patterns via BLE; devices store in RAM (session-local).
 */
typedef struct {
    sheet_header_t header;                          /**< Pattern metadata */
    bilateral_segment_t segments[PATTERN_MAX_SEGMENTS]; /**< Segment data */
    bool valid;                                     /**< Buffer contains valid pattern */
} pattern_buffer_t;

/**
 * @brief Pattern playback state
 */
typedef struct {
    uint64_t start_time_us;     /**< When pattern playback started (synchronized time) */
    uint16_t current_segment;   /**< Currently executing segment index */
    uint16_t loop_count;        /**< Number of pattern loops completed */
    bool playing;               /**< Pattern is actively playing */
    bool paused;                /**< Pattern is paused */
} playback_state_t;

// ============================================================================
// BUILT-IN PATTERN IDENTIFIERS
// ============================================================================

/**
 * @brief Built-in pattern IDs (hardcoded patterns)
 *
 * Order matches BLE Pattern Control API (AD047):
 * - control_cmd 2 = ALTERNATING (green bilateral, therapy)
 * - control_cmd 3 = EMERGENCY (red/blue wig-wag, lightbar demo)
 * - control_cmd 4 = BREATHE (cyan pulse, calming)
 *
 * Formula: pattern_id = control_cmd - 1
 */
typedef enum {
    BUILTIN_PATTERN_NONE = 0,           /**< No pattern loaded */
    BUILTIN_PATTERN_ALTERNATING,        /**< Simple left/right alternation (BLE: 2) */
    BUILTIN_PATTERN_EMERGENCY,          /**< Red/blue emergency lights (BLE: 3) */
    BUILTIN_PATTERN_BREATHE,            /**< Slow breathing pulse (BLE: 4) */
    BUILTIN_PATTERN_COUNT               /**< Number of built-in patterns */
} builtin_pattern_id_t;

// ============================================================================
// PUBLIC API
// ============================================================================

/**
 * @brief Initialize pattern playback module
 * @return ESP_OK on success
 *
 * Initializes pattern buffer and playback state.
 * Must be called before any pattern operations.
 */
esp_err_t pattern_playback_init(void);

/**
 * @brief Load a built-in pattern
 * @param pattern_id Built-in pattern identifier
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG for unknown pattern
 *
 * Loads a hardcoded pattern into the pattern buffer.
 * Use for Mode 5/6 lightbar demonstration.
 */
esp_err_t pattern_load_builtin(builtin_pattern_id_t pattern_id);

/**
 * @brief Load pattern from external data
 * @param header Pattern header (will be copied)
 * @param segments Segment array (will be copied)
 * @param segment_count Number of segments
 * @return ESP_OK on success, ESP_ERR_INVALID_SIZE if too many segments
 *
 * Loads pattern from BLE transfer into pattern buffer.
 * Validates CRC before accepting.
 */
esp_err_t pattern_load_external(const sheet_header_t *header,
                                 const bilateral_segment_t *segments,
                                 uint16_t segment_count);

/**
 * @brief Start pattern playback
 * @param start_time_us Synchronized time to start playback (or 0 for now)
 * @return ESP_OK on success, ESP_ERR_INVALID_STATE if no pattern loaded
 *
 * Begins executing the loaded pattern.
 * If start_time_us is 0, starts immediately using current synchronized time.
 */
esp_err_t pattern_start(uint64_t start_time_us);

/**
 * @brief Stop pattern playback
 * @return ESP_OK on success
 *
 * Stops pattern playback and clears outputs (motor coast, LED off).
 */
esp_err_t pattern_stop(void);

/**
 * @brief Pause pattern playback
 * @return ESP_OK on success
 *
 * Pauses playback at current position. Call pattern_resume() to continue.
 */
esp_err_t pattern_pause(void);

/**
 * @brief Resume paused pattern
 * @return ESP_OK on success, ESP_ERR_INVALID_STATE if not paused
 */
esp_err_t pattern_resume(void);

/**
 * @brief Execute one tick of pattern playback
 * @param current_time_us Current synchronized time in microseconds
 * @return ESP_OK on success, ESP_ERR_NOT_FOUND if pattern complete (non-looping)
 *
 * Called from motor_task at regular intervals (~10ms).
 * Calculates current position in pattern and executes appropriate segment.
 * Uses device's zone from zone_config_get() to select L/R outputs.
 *
 * Thread-safe: Can be called from motor_task.
 */
esp_err_t pattern_execute_tick(uint64_t current_time_us);

/**
 * @brief Get current segment outputs for this device's zone
 * @param color Output: Palette index for LED
 * @param brightness Output: Brightness percentage (CIE-corrected internally)
 * @param motor Output: Motor intensity percentage
 * @return ESP_OK on success, ESP_ERR_INVALID_STATE if not playing
 *
 * Returns the current outputs based on:
 * - Current position in pattern timeline
 * - Device's zone (from zone_config_get())
 * - Interpolation between segments (if transition_ms > 0)
 */
esp_err_t pattern_get_current_outputs(uint8_t *color, uint8_t *brightness, uint8_t *motor);

/**
 * @brief Check if pattern is currently playing
 * @return true if pattern is playing, false otherwise
 */
bool pattern_is_playing(void);

/**
 * @brief Get current playback state
 * @return Pointer to playback state (read-only)
 */
const playback_state_t* pattern_get_state(void);

/**
 * @brief Get pattern buffer
 * @return Pointer to pattern buffer (read-only)
 */
const pattern_buffer_t* pattern_get_buffer(void);

/**
 * @brief Validate pattern data integrity
 * @param buffer Pattern buffer to validate
 * @return true if CRC matches, false otherwise
 */
bool pattern_validate_crc(const pattern_buffer_t *buffer);

/**
 * @brief Calculate CRC32 for pattern segments
 * @param segments Segment array
 * @param count Number of segments
 * @return CRC32 value
 */
uint32_t pattern_calculate_crc(const bilateral_segment_t *segments, uint16_t count);

/**
 * @brief Deinitialize pattern playback module
 * @return ESP_OK on success
 */
esp_err_t pattern_playback_deinit(void);

#ifdef __cplusplus
}
#endif

#endif // PATTERN_PLAYBACK_H
