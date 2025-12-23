/**
 * @file pattern_playback.c
 * @brief Bilateral Pattern Playback Implementation
 *
 * @see pattern_playback.h for API documentation
 * @date December 2025
 * @author Claude Code (Anthropic)
 */

#include "pattern_playback.h"
#include "zone_config.h"
#include "led_control.h"
#include "motor_control.h"
#include "time_sync.h"
#include "esp_log.h"
#include "esp_crc.h"
#include <string.h>

static const char *TAG = "PATTERN";

// ============================================================================
// MODULE STATE
// ============================================================================

static pattern_buffer_t active_pattern = {0};
static playback_state_t playback_state = {0};
static bool module_initialized = false;

// ============================================================================
// HARDCODED PATTERNS
// ============================================================================

/**
 * @brief Emergency lightbar pattern - Red/Blue alternating at 2Hz
 *
 * Classic emergency vehicle light simulation.
 * Total duration: 4000ms (4 seconds), loops.
 *
 * Timeline:
 *   0ms:    LEFT=RED,  RIGHT=OFF
 *   250ms:  LEFT=OFF,  RIGHT=BLUE
 *   500ms:  LEFT=RED,  RIGHT=OFF
 *   750ms:  LEFT=OFF,  RIGHT=BLUE
 *   ... (repeats 4x)
 *   2000ms: Rapid flash phase
 *   4000ms: Loop back to start
 */
static const bilateral_segment_t emergency_pattern_segments[] = {
    // Phase 1: Slow alternation (500ms each side)
    // time_offset, transition, flags, waveform, L_color, L_bright, L_motor, R_color, R_bright, R_motor
    {    0,  10, 0, 0,   0, 100, 0,   2,   0, 0 },  // LEFT=RED on, RIGHT=BLUE off
    {  500,  10, 0, 0,   0,   0, 0,   2, 100, 0 },  // LEFT=RED off, RIGHT=BLUE on
    { 1000,  10, 0, 0,   0, 100, 0,   2,   0, 0 },  // LEFT=RED on, RIGHT=BLUE off
    { 1500,  10, 0, 0,   0,   0, 0,   2, 100, 0 },  // LEFT=RED off, RIGHT=BLUE on

    // Phase 2: Rapid alternation (250ms each side)
    { 2000,   5, 0, 0,   0, 100, 0,   2,   0, 0 },  // LEFT=RED on, RIGHT=BLUE off
    { 2250,   5, 0, 0,   0,   0, 0,   2, 100, 0 },  // LEFT=RED off, RIGHT=BLUE on
    { 2500,   5, 0, 0,   0, 100, 0,   2,   0, 0 },  // LEFT=RED on, RIGHT=BLUE off
    { 2750,   5, 0, 0,   0,   0, 0,   2, 100, 0 },  // LEFT=RED off, RIGHT=BLUE on
    { 3000,   5, 0, 0,   0, 100, 0,   2,   0, 0 },  // LEFT=RED on, RIGHT=BLUE off
    { 3250,   5, 0, 0,   0,   0, 0,   2, 100, 0 },  // LEFT=RED off, RIGHT=BLUE on
    { 3500,   5, 0, 0,   0, 100, 0,   2,   0, 0 },  // LEFT=RED on, RIGHT=BLUE off
    { 3750,   5, 0, 0,   0,   0, 0,   2, 100, 0 },  // LEFT=RED off, RIGHT=BLUE on

    // End marker (returns to start of loop)
    { 4000,   0, 0, 0,   0,   0, 0,   0,   0, 0 },  // Both off (loop point)
};
#define EMERGENCY_PATTERN_COUNT (sizeof(emergency_pattern_segments) / sizeof(bilateral_segment_t))

/**
 * @brief Simple alternating pattern - Left/Right at 1Hz
 *
 * Basic bilateral alternation for therapy mode demonstration.
 * Total duration: 2000ms (2 seconds), loops.
 */
static const bilateral_segment_t alternating_pattern_segments[] = {
    // time_offset, transition, flags, waveform, L_color, L_bright, L_motor, R_color, R_bright, R_motor
    {    0,  25, 0, 0,   1, 100, 60,   1,   0,  0 },  // LEFT=GREEN on with motor, RIGHT off
    { 1000,  25, 0, 0,   1,   0,  0,   1, 100, 60 },  // LEFT off, RIGHT=GREEN on with motor
    { 2000,   0, 0, 0,   0,   0,  0,   0,   0,  0 },  // Loop point
};
#define ALTERNATING_PATTERN_COUNT (sizeof(alternating_pattern_segments) / sizeof(bilateral_segment_t))

/**
 * @brief Breathing pattern - Slow synchronized pulse
 *
 * Calming breathing rhythm, both sides synchronized.
 * Total duration: 4000ms (4 seconds), loops.
 */
static const bilateral_segment_t breathe_pattern_segments[] = {
    // time_offset, transition, flags, waveform, L_color, L_bright, L_motor, R_color, R_bright, R_motor
    {    0, 250, SEG_FLAG_EASE_IN,  0,   4, 100, 30,   4, 100, 30 },  // Breathe in (cyan, 1s fade)
    { 2000, 250, SEG_FLAG_EASE_OUT, 0,   4,  10,  0,   4,  10,  0 },  // Breathe out (1s fade)
    { 4000,   0, 0, 0,   0,   0,  0,   0,   0,  0 },  // Loop point
};
#define BREATHE_PATTERN_COUNT (sizeof(breathe_pattern_segments) / sizeof(bilateral_segment_t))

/**
 * @brief Emergency Quad Flash - SAE J845-style Red/Blue/White
 *
 * Advanced emergency vehicle light simulation with quad flash bursts.
 * Inspired by SAE J845 Class 1 optical warning devices.
 * Total duration: 2000ms (2 seconds), loops at ~1.5 Hz effective rate.
 *
 * Flash Pattern (per SAE guidelines, 1-2 Hz safe range):
 *   Phase 1: LEFT quad flash (RED) - 4 rapid bursts
 *   Phase 2: RIGHT quad flash (BLUE) - 4 rapid bursts
 *   Phase 3: BOTH double flash (WHITE) - takedown/alley lights
 *
 * Timing: 50ms ON, 50ms OFF per flash (10 Hz burst within pattern)
 * Color Palette: 0=Red, 2=Blue, 10=White
 *
 * Reference: SAE J845 Class 1, safe flash rate 60-240 FPM (1-4 Hz)
 */
static const bilateral_segment_t emergency_quad_pattern_segments[] = {
    // Phase 1: LEFT (RED) quad flash - 4 bursts, 50ms each
    // time_offset, transition, flags, waveform, L_color, L_bright, L_motor, R_color, R_bright, R_motor
    {    0,   0, 0, 0,   0, 100, 0,   2,   0, 0 },  // RED on LEFT
    {   50,   0, 0, 0,   0,   0, 0,   2,   0, 0 },  // OFF
    {  100,   0, 0, 0,   0, 100, 0,   2,   0, 0 },  // RED on LEFT
    {  150,   0, 0, 0,   0,   0, 0,   2,   0, 0 },  // OFF
    {  200,   0, 0, 0,   0, 100, 0,   2,   0, 0 },  // RED on LEFT
    {  250,   0, 0, 0,   0,   0, 0,   2,   0, 0 },  // OFF
    {  300,   0, 0, 0,   0, 100, 0,   2,   0, 0 },  // RED on LEFT
    {  350,   0, 0, 0,   0,   0, 0,   2,   0, 0 },  // OFF - end quad

    // Gap before Phase 2
    {  500,   0, 0, 0,   0,   0, 0,   2,   0, 0 },  // Brief pause

    // Phase 2: RIGHT (BLUE) quad flash - 4 bursts, 50ms each
    {  550,   0, 0, 0,   0,   0, 0,   2, 100, 0 },  // BLUE on RIGHT
    {  600,   0, 0, 0,   0,   0, 0,   2,   0, 0 },  // OFF
    {  650,   0, 0, 0,   0,   0, 0,   2, 100, 0 },  // BLUE on RIGHT
    {  700,   0, 0, 0,   0,   0, 0,   2,   0, 0 },  // OFF
    {  750,   0, 0, 0,   0,   0, 0,   2, 100, 0 },  // BLUE on RIGHT
    {  800,   0, 0, 0,   0,   0, 0,   2,   0, 0 },  // OFF
    {  850,   0, 0, 0,   0,   0, 0,   2, 100, 0 },  // BLUE on RIGHT
    {  900,   0, 0, 0,   0,   0, 0,   2,   0, 0 },  // OFF - end quad

    // Gap before Phase 3
    { 1050,   0, 0, 0,   0,   0, 0,   0,   0, 0 },  // Brief pause

    // Phase 3: BOTH (WHITE) double flash - takedown lights
    { 1100,   0, 0, 0,  10, 100, 0,  10, 100, 0 },  // WHITE on BOTH
    { 1200,   0, 0, 0,  10,   0, 0,  10,   0, 0 },  // OFF
    { 1300,   0, 0, 0,  10, 100, 0,  10, 100, 0 },  // WHITE on BOTH
    { 1400,   0, 0, 0,  10,   0, 0,  10,   0, 0 },  // OFF

    // End marker (loop point)
    { 2000,   0, 0, 0,   0,   0, 0,   0,   0, 0 },  // Loop
};
#define EMERGENCY_QUAD_PATTERN_COUNT (sizeof(emergency_quad_pattern_segments) / sizeof(bilateral_segment_t))

// ============================================================================
// INTERNAL HELPERS
// ============================================================================

/**
 * @brief Find segment for given time offset
 * @param time_ms Current time in pattern (0 to pattern duration)
 * @return Segment index, or -1 if not found
 */
static int find_segment_for_time(uint32_t time_ms) {
    if (!active_pattern.valid || active_pattern.header.segment_count == 0) {
        return -1;
    }

    // Linear search (patterns are small)
    for (int i = active_pattern.header.segment_count - 1; i >= 0; i--) {
        if (active_pattern.segments[i].time_offset_ms <= time_ms) {
            return i;
        }
    }
    return 0;  // Default to first segment
}

/**
 * @brief Get pattern duration in milliseconds
 */
static uint32_t get_pattern_duration_ms(void) {
    if (!active_pattern.valid || active_pattern.header.segment_count == 0) {
        return 0;
    }
    // Last segment's time_offset is the pattern duration
    return active_pattern.segments[active_pattern.header.segment_count - 1].time_offset_ms;
}

/**
 * @brief Interpolate between two values based on progress
 * @param from Start value
 * @param to End value
 * @param progress Progress 0-255 (0=from, 255=to)
 * @return Interpolated value
 */
static uint8_t interpolate(uint8_t from, uint8_t to, uint8_t progress) {
    int16_t diff = (int16_t)to - (int16_t)from;
    return from + (int8_t)((diff * progress) / 255);
}

// ============================================================================
// PUBLIC API IMPLEMENTATION
// ============================================================================

esp_err_t pattern_playback_init(void) {
    ESP_LOGI(TAG, "Initializing pattern playback module");

    memset(&active_pattern, 0, sizeof(active_pattern));
    memset(&playback_state, 0, sizeof(playback_state));
    module_initialized = true;

    ESP_LOGI(TAG, "Pattern playback initialized (max %d segments, %d bytes)",
             PATTERN_MAX_SEGMENTS, (int)sizeof(pattern_buffer_t));
    return ESP_OK;
}

esp_err_t pattern_load_builtin(builtin_pattern_id_t pattern_id) {
    if (!module_initialized) {
        return ESP_ERR_INVALID_STATE;
    }

    const bilateral_segment_t *src_segments = NULL;
    uint16_t segment_count = 0;
    const char *pattern_name = "unknown";

    switch (pattern_id) {
        case BUILTIN_PATTERN_EMERGENCY:
            src_segments = emergency_pattern_segments;
            segment_count = EMERGENCY_PATTERN_COUNT;
            pattern_name = "emergency";
            break;

        case BUILTIN_PATTERN_ALTERNATING:
            src_segments = alternating_pattern_segments;
            segment_count = ALTERNATING_PATTERN_COUNT;
            pattern_name = "alternating";
            break;

        case BUILTIN_PATTERN_BREATHE:
            src_segments = breathe_pattern_segments;
            segment_count = BREATHE_PATTERN_COUNT;
            pattern_name = "breathe";
            break;

        case BUILTIN_PATTERN_EMERGENCY_QUAD:
            src_segments = emergency_quad_pattern_segments;
            segment_count = EMERGENCY_QUAD_PATTERN_COUNT;
            pattern_name = "emergency_quad";
            break;

        default:
            ESP_LOGE(TAG, "Unknown builtin pattern: %d", pattern_id);
            return ESP_ERR_INVALID_ARG;
    }

    // Stop any playing pattern
    pattern_stop();

    // Copy segments to buffer
    memcpy(active_pattern.segments, src_segments, segment_count * sizeof(bilateral_segment_t));

    // Set up header
    uint64_t current_time = 0;
    time_sync_get_time(&current_time);  // Get synchronized time (or 0 if not synced)
    active_pattern.header.born_at_us = current_time;
    active_pattern.header.segment_count = segment_count;
    active_pattern.header.mode_id = 5;  // Lightbar mode
    active_pattern.header.flags = SHEET_FLAG_LOOPING | SHEET_FLAG_LED;
    active_pattern.header.content_crc = pattern_calculate_crc(active_pattern.segments, segment_count);

    active_pattern.valid = true;

    ESP_LOGI(TAG, "Loaded builtin pattern '%s' (%d segments, %lums duration)",
             pattern_name, segment_count, (unsigned long)get_pattern_duration_ms());
    return ESP_OK;
}

esp_err_t pattern_load_external(const sheet_header_t *header,
                                 const bilateral_segment_t *segments,
                                 uint16_t segment_count) {
    if (!module_initialized) {
        return ESP_ERR_INVALID_STATE;
    }

    if (segment_count > PATTERN_MAX_SEGMENTS) {
        ESP_LOGE(TAG, "Too many segments: %d (max %d)", segment_count, PATTERN_MAX_SEGMENTS);
        return ESP_ERR_INVALID_SIZE;
    }

    // Validate CRC
    uint32_t calculated_crc = pattern_calculate_crc(segments, segment_count);
    if (calculated_crc != header->content_crc) {
        ESP_LOGE(TAG, "CRC mismatch: calculated=0x%08lx, header=0x%08lx",
                 (unsigned long)calculated_crc, (unsigned long)header->content_crc);
        return ESP_ERR_INVALID_CRC;
    }

    // Stop any playing pattern
    pattern_stop();

    // Copy data
    memcpy(&active_pattern.header, header, sizeof(sheet_header_t));
    memcpy(active_pattern.segments, segments, segment_count * sizeof(bilateral_segment_t));
    active_pattern.valid = true;

    ESP_LOGI(TAG, "Loaded external pattern (%d segments, mode %d)",
             segment_count, header->mode_id);
    return ESP_OK;
}

esp_err_t pattern_start(uint64_t start_time_us) {
    if (!module_initialized || !active_pattern.valid) {
        ESP_LOGE(TAG, "Cannot start: %s",
                 !module_initialized ? "not initialized" : "no pattern loaded");
        return ESP_ERR_INVALID_STATE;
    }

    // If start_time is 0, start now
    if (start_time_us == 0) {
        time_sync_get_time(&start_time_us);
    }

    playback_state.start_time_us = start_time_us;
    playback_state.current_segment = 0;
    playback_state.loop_count = 0;
    playback_state.playing = true;
    playback_state.paused = false;

    // Lock the pattern while playing
    active_pattern.header.flags |= SHEET_FLAG_LOCKED;

    ESP_LOGI(TAG, "Pattern playback started (start_time=%llu us)",
             (unsigned long long)start_time_us);
    return ESP_OK;
}

esp_err_t pattern_stop(void) {
    if (playback_state.playing) {
        playback_state.playing = false;
        playback_state.paused = false;

        // Unlock pattern
        active_pattern.header.flags &= ~SHEET_FLAG_LOCKED;

        // Clear outputs
        motor_coast(false);
        led_clear();

        ESP_LOGI(TAG, "Pattern playback stopped (%d loops completed)",
                 playback_state.loop_count);
    }
    return ESP_OK;
}

esp_err_t pattern_pause(void) {
    if (!playback_state.playing) {
        return ESP_ERR_INVALID_STATE;
    }
    playback_state.paused = true;
    ESP_LOGI(TAG, "Pattern playback paused");
    return ESP_OK;
}

esp_err_t pattern_resume(void) {
    if (!playback_state.playing || !playback_state.paused) {
        return ESP_ERR_INVALID_STATE;
    }
    playback_state.paused = false;
    ESP_LOGI(TAG, "Pattern playback resumed");
    return ESP_OK;
}

esp_err_t pattern_execute_tick(uint64_t current_time_us) {
    if (!playback_state.playing || playback_state.paused) {
        return ESP_ERR_INVALID_STATE;
    }

    // Calculate elapsed time in pattern
    int64_t elapsed_us = current_time_us - playback_state.start_time_us;
    if (elapsed_us < 0) {
        // Pattern hasn't started yet
        return ESP_OK;
    }

    uint32_t elapsed_ms = (uint32_t)(elapsed_us / 1000);
    uint32_t pattern_duration_ms = get_pattern_duration_ms();

    if (pattern_duration_ms == 0) {
        return ESP_ERR_INVALID_STATE;
    }

    // Handle looping
    if (elapsed_ms >= pattern_duration_ms) {
        if (active_pattern.header.flags & SHEET_FLAG_LOOPING) {
            // Loop back to start
            uint32_t loops = elapsed_ms / pattern_duration_ms;
            if (loops > playback_state.loop_count) {
                playback_state.loop_count = loops;
                ESP_LOGD(TAG, "Pattern loop %d", playback_state.loop_count);
            }
            elapsed_ms = elapsed_ms % pattern_duration_ms;
        } else {
            // Non-looping pattern complete
            pattern_stop();
            return ESP_ERR_NOT_FOUND;
        }
    }

    // Find current segment
    int seg_idx = find_segment_for_time(elapsed_ms);
    if (seg_idx < 0) {
        return ESP_ERR_INVALID_STATE;
    }

    playback_state.current_segment = seg_idx;

    // Get outputs and apply them
    uint8_t color, brightness, motor_intensity;
    esp_err_t ret = pattern_get_current_outputs(&color, &brightness, &motor_intensity);
    if (ret != ESP_OK) {
        return ret;
    }

    // Apply LED
    if (active_pattern.header.flags & SHEET_FLAG_LED) {
        led_enable();
        led_set_palette_perceptual(color, brightness);
    }

    // Apply motor
    if ((active_pattern.header.flags & SHEET_FLAG_MOTOR) && motor_intensity > 0) {
        // Determine direction based on zone
        device_zone_t zone = zone_config_get();
        if (zone == ZONE_LEFT) {
            motor_set_forward(motor_intensity, false);
        } else {
            motor_set_reverse(motor_intensity, false);
        }
    } else if (motor_intensity == 0) {
        motor_coast(false);
    }

    return ESP_OK;
}

esp_err_t pattern_get_current_outputs(uint8_t *color, uint8_t *brightness, uint8_t *motor) {
    if (!playback_state.playing) {
        return ESP_ERR_INVALID_STATE;
    }

    uint16_t seg_idx = playback_state.current_segment;
    if (seg_idx >= active_pattern.header.segment_count) {
        return ESP_ERR_INVALID_STATE;
    }

    const bilateral_segment_t *seg = &active_pattern.segments[seg_idx];
    device_zone_t zone = zone_config_get();

    // Select outputs based on zone
    if (zone == ZONE_LEFT) {
        *color = seg->L_color;
        *brightness = seg->L_brightness;
        *motor = seg->L_motor;
    } else {
        *color = seg->R_color;
        *brightness = seg->R_brightness;
        *motor = seg->R_motor;
    }

    // TODO: Add interpolation between segments for smooth transitions
    // For now, just return segment values directly

    return ESP_OK;
}

bool pattern_is_playing(void) {
    return playback_state.playing && !playback_state.paused;
}

const playback_state_t* pattern_get_state(void) {
    return &playback_state;
}

const pattern_buffer_t* pattern_get_buffer(void) {
    return &active_pattern;
}

bool pattern_validate_crc(const pattern_buffer_t *buffer) {
    if (!buffer->valid) {
        return false;
    }
    uint32_t calculated = pattern_calculate_crc(buffer->segments, buffer->header.segment_count);
    return calculated == buffer->header.content_crc;
}

uint32_t pattern_calculate_crc(const bilateral_segment_t *segments, uint16_t count) {
    if (segments == NULL || count == 0) {
        return 0;
    }
    return esp_crc32_le(0, (const uint8_t *)segments, count * sizeof(bilateral_segment_t));
}

esp_err_t pattern_playback_deinit(void) {
    ESP_LOGI(TAG, "Deinitializing pattern playback");

    pattern_stop();
    memset(&active_pattern, 0, sizeof(active_pattern));
    memset(&playback_state, 0, sizeof(playback_state));
    module_initialized = false;

    return ESP_OK;
}
