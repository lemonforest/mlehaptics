/**
 * @file utlp_hal.h
 * @brief Hardware Abstraction Layer - Universal Time Lord Protocol
 *
 * Minimal HAL for UTLP Genesis Node demonstration.
 * Single actuator (GPIO15 LED) driven by MCPWM for phase-aligned output.
 *
 * DESIGN PHILOSOPHY:
 * 1. Genesis First: Device works alone, peers are optional
 * 2. Single Actuator: GPIO15 LED shows sync visually
 * 3. Time-Indexed: LED state derived from atomic time, not delays
 * 4. No Malloc: All memory statically allocated
 *
 * PLATFORM SUPPORT:
 * - ESP32-C6: Full floating-point support
 * - C64 (cc65): Integer-only (no FPU, no float emulation)
 *
 * @version 2.1.0 - Added cc65/C64 platform support
 * @date 2025-12-28
 */

#pragma once

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

/*============================================================================
 * PLATFORM DETECTION - Floating Point Support
 *
 * cc65 (C64, Apple II, NES, etc.) has NO floating point support.
 * We use integer types for phase/duty on these platforms:
 *   - phase: 0-36000 (degrees × 100, so 180.00° = 18000)
 *   - duty:  0-10000 (percent × 100, so 50.00% = 5000)
 *==========================================================================*/

/*============================================================================
 * THE CHAMELEON TIME STRUCTURE
 *
 * This is the "Grand Unified Theory" of the UTLP architecture.
 * The fundamental nature of time changes based on the hardware:
 *
 *   ESP32: Native uint64_t - fast hardware math
 *   C64:   Segmented struct - manual control for 8-bit ALU
 *
 * The skeleton code uses abstract macros (UTLP_GET_PHASE, UTLP_DIFF_US)
 * that adapt to the hardware automatically. The code runs on BOTH chips
 * without changing the logic.
 *==========================================================================*/

#ifdef __CC65__
    /*=========================================================================
     * COMMODORE 64 MODE - No 64-bit Support
     *
     * CRITICAL: cc65 does NOT support 'long long' (64-bit integers).
     * The largest integer type is 'long' (32-bit).
     *
     * We work around this by:
     *   1. Using a union { words[4], dwords[2] } for time storage
     *   2. Never doing 64-bit math - only 32-bit with ripple carry
     *   3. HAL functions return utlp_time_t instead of uint64_t
     *========================================================================*/

    /** @brief C64 has NO 64-bit types - must use utlp_time_t everywhere */
    #define UTLP_NO_64BIT 1

    /* cc65: No floating point - use fixed-point integers */
    typedef uint16_t utlp_float_t;
    #define UTLP_NO_FLOAT 1
    #define UTLP_PHASE(deg)  ((uint16_t)((deg) * 100))   /* 180.0 -> 18000 */
    #define UTLP_DUTY(pct)   ((uint16_t)((pct) * 100))   /* 50.0 -> 5000 */

    /*=========================================================================
     * THE UNION-CASCADE TIME STRUCTURE
     *
     * 64-bits of time, viewed two ways:
     *   1. 'words': 4× 16-bit chunks for fast ripple-carry incrementing
     *   2. 'dwords': 2× 32-bit chunks for the "Magic Remainder" phase math
     *
     * This is the NATIVE LANGUAGE of the 6502:
     *   - 16-bit is the natural address width (zero-page indirect)
     *   - Ripple carry: 8-bit ALU chains naturally through 16-bit pairs
     *   - Zero-cost view switching (compiler just reads memory differently)
     *========================================================================*/

    typedef union {
        /* View as 16-bit Cascades (Fastest for counting) */
        struct {
            uint16_t w0;  /**< 0..65ms */
            uint16_t w1;  /**< 65ms..71min */
            uint16_t w2;  /**< 71min..8yrs */
            uint16_t w3;  /**< 8yrs..584kyrs */
        } words;

        /* View as 32-bit Chunks (Fastest for Phase Math) */
        struct {
            uint32_t lo;  /**< The "Standard" 32-bit clock */
            uint32_t hi;  /**< The "Epoch" */
        } dwords;
    } utlp_time_t;

    /** @brief Zero-initialize a time value */
    #define UTLP_TIME_ZERO  { { 0, 0, 0, 0 } }

    /** @brief Standard blink period in microseconds */
    #define UTLP_BLINK_PERIOD_US    1000000UL

    /** @brief Magic constant: 2^32 mod 1,000,000 = 296 */
    #define MAGIC_EPOCH_REM         296UL

    /*=========================================================================
     * THE PHYSICS MACROS - The "Ripple Magic"
     *
     * These macros use the union's multiple views for optimal 6502 code:
     *   - dwords.lo: Low 32 bits for phase math
     *   - dwords.hi: High 32 bits (epoch)
     *   - words.w0..w3: For ripple carry and lazy comparison
     *========================================================================*/

    /**
     * @brief Get phase position (modulo) using Magic Remainder trick
     *
     * THE MATH:
     *   Time = (Hi * 2^32) + Lo
     *   2^32 mod 1,000,000 = 296
     *   Phase = ((dwords.hi * 296) + (dwords.lo % 1M)) % 1M
     *
     * This gives ~200 cycle phase calc instead of ~3000 cycles!
     */
    #define UTLP_GET_PHASE(t, period_us) \
        ( ((period_us) == UTLP_BLINK_PERIOD_US) ? \
          ((((uint32_t)(t).dwords.hi * MAGIC_EPOCH_REM) + ((t).dwords.lo % UTLP_BLINK_PERIOD_US)) % UTLP_BLINK_PERIOD_US) : \
          ((t).dwords.lo % (period_us)) )

    /**
     * @brief Get time difference (fast 32-bit path)
     * Uses dwords.lo for fast 32-bit subtraction.
     * Valid for differences < 71 minutes.
     */
    #define UTLP_DIFF_US(now, last)     ((int32_t)((now).dwords.lo - (last).dwords.lo))

    /**
     * @brief Add microseconds to time (Manual Ripple Carry)
     *
     * This is where the 4× uint16_t shines.
     * We add to w0. If it wraps, we tick w1, etc.
     * This avoids loading 64-bits into registers for a simple add.
     */
    #define UTLP_ADD_US(t, us) do { \
        uint16_t _prev = (t).words.w0; \
        (t).words.w0 += (uint16_t)(us); \
        if ((t).words.w0 < _prev) { \
            if (++(t).words.w1 == 0) { \
                if (++(t).words.w2 == 0) { \
                    (t).words.w3++; \
                } \
            } \
        } \
    } while(0)

    /** @brief Get low 32 bits (for compatibility) */
    #define UTLP_TIME_LOW32(t)          ((t).dwords.lo)

    /** @brief Alias for compatibility with skeleton code */
    #define UTLP_TIME_DIFF(a, b)        UTLP_DIFF_US(a, b)

    /**
     * @brief Compare times for less-than (LAZY COMPARISON)
     *
     * The 6502 Pro Move: Compare from MSB (w3) first.
     * If unequal, we're done! No need to check lower words.
     * This is MUCH faster than comparing all 64 bits.
     */
    #define UTLP_TIME_LT(a, b) \
        ( ((a).words.w3 != (b).words.w3) ? ((a).words.w3 < (b).words.w3) : \
          ((a).words.w2 != (b).words.w2) ? ((a).words.w2 < (b).words.w2) : \
          ((a).words.w1 != (b).words.w1) ? ((a).words.w1 < (b).words.w1) : \
          ((a).words.w0 < (b).words.w0) )

    /** @brief Compare times for greater-or-equal */
    #define UTLP_TIME_GE(a, b)          (!UTLP_TIME_LT(a, b))

    /** @brief Compare times for equality */
    #define UTLP_TIME_EQ(a, b) \
        ((a).words.w3 == (b).words.w3 && \
         (a).words.w2 == (b).words.w2 && \
         (a).words.w1 == (b).words.w1 && \
         (a).words.w0 == (b).words.w0)

    /**
     * @brief Create time from bytes (for receiving beacons)
     *
     * Beacons are sent as 8 bytes (little-endian).
     * We copy directly into our union's dwords view.
     */
    static utlp_time_t utlp_time_from_bytes(const uint8_t *bytes)
    {
        utlp_time_t t;
        /* Little-endian: bytes 0-3 = lo, bytes 4-7 = hi */
        t.dwords.lo = (uint32_t)bytes[0] |
                      ((uint32_t)bytes[1] << 8) |
                      ((uint32_t)bytes[2] << 16) |
                      ((uint32_t)bytes[3] << 24);
        t.dwords.hi = (uint32_t)bytes[4] |
                      ((uint32_t)bytes[5] << 8) |
                      ((uint32_t)bytes[6] << 16) |
                      ((uint32_t)bytes[7] << 24);
        return t;
    }
    #define UTLP_TIME_FROM_BYTES(ptr)   utlp_time_from_bytes(ptr)

    /**
     * @brief Write time to bytes (for sending beacons)
     *
     * Writes 8 bytes in little-endian format.
     */
    static void utlp_time_to_bytes(utlp_time_t t, uint8_t *bytes)
    {
        bytes[0] = (uint8_t)(t.dwords.lo);
        bytes[1] = (uint8_t)(t.dwords.lo >> 8);
        bytes[2] = (uint8_t)(t.dwords.lo >> 16);
        bytes[3] = (uint8_t)(t.dwords.lo >> 24);
        bytes[4] = (uint8_t)(t.dwords.hi);
        bytes[5] = (uint8_t)(t.dwords.hi >> 8);
        bytes[6] = (uint8_t)(t.dwords.hi >> 16);
        bytes[7] = (uint8_t)(t.dwords.hi >> 24);
    }
    #define UTLP_TIME_TO_BYTES(t, ptr)  utlp_time_to_bytes(t, ptr)

    /** @brief Size of serialized time in bytes */
    #define UTLP_TIME_SERIAL_SIZE       8

    /** @brief Use cascaded time on C64 */
    #define UTLP_CASCADED_TIME 1

#else
    /*=========================================================================
     * ESP32 MODE - The "Atomic" Time
     *
     * Modern CPUs have native 64-bit math. We use it directly.
     * No tricks needed - the hardware is fast enough.
     *========================================================================*/

    /* Normal platforms: Use native float */
    typedef float utlp_float_t;
    #define UTLP_NO_FLOAT 0
    #define UTLP_PHASE(deg)  (deg)
    #define UTLP_DUTY(pct)   (pct)

    /** @brief Native 64-bit time type */
    typedef uint64_t utlp_time_t;

    /** @brief Zero-initialize a time value */
    #define UTLP_TIME_ZERO          ((utlp_time_t)0)

    /** @brief Standard blink period in microseconds */
    #define UTLP_BLINK_PERIOD_US    1000000UL

    /** @brief Get phase position (native modulo) */
    #define UTLP_GET_PHASE(t, p)    ((uint32_t)((t) % (p)))

    /** @brief Get time difference (native subtraction) */
    #define UTLP_DIFF_US(now, last) ((int64_t)((now) - (last)))

    /** @brief Alias for compatibility */
    #define UTLP_TIME_DIFF(a, b)    UTLP_DIFF_US(a, b)

    /** @brief Add microseconds (native addition) */
    #define UTLP_ADD_US(t, us)      ((t) += (us))

    /** @brief Get low 32 bits (for compatibility) */
    #define UTLP_TIME_LOW32(t)      ((uint32_t)(t))

    /** @brief Compare times for less-than */
    #define UTLP_TIME_LT(a, b)      ((a) < (b))

    /** @brief Compare times for greater-or-equal */
    #define UTLP_TIME_GE(a, b)      ((a) >= (b))

    /** @brief Compare times for equality */
    #define UTLP_TIME_EQ(a, b)      ((a) == (b))

    /** @brief Create time from uint64_t (no-op on native) */
    #define UTLP_TIME_FROM_U64(raw) (raw)

    /** @brief Convert time to uint64_t (no-op on native) */
    #define UTLP_TIME_TO_U64(t)     (t)

    /** @brief Create time from bytes (for API compatibility with C64) */
    static inline utlp_time_t utlp_time_from_bytes_esp32(const uint8_t *bytes)
    {
        return (utlp_time_t)bytes[0] |
               ((utlp_time_t)bytes[1] << 8) |
               ((utlp_time_t)bytes[2] << 16) |
               ((utlp_time_t)bytes[3] << 24) |
               ((utlp_time_t)bytes[4] << 32) |
               ((utlp_time_t)bytes[5] << 40) |
               ((utlp_time_t)bytes[6] << 48) |
               ((utlp_time_t)bytes[7] << 56);
    }
    #define UTLP_TIME_FROM_BYTES(ptr)   utlp_time_from_bytes_esp32(ptr)

    /** @brief Write time to bytes (for API compatibility with C64) */
    static inline void utlp_time_to_bytes_esp32(utlp_time_t t, uint8_t *bytes)
    {
        bytes[0] = (uint8_t)(t);
        bytes[1] = (uint8_t)(t >> 8);
        bytes[2] = (uint8_t)(t >> 16);
        bytes[3] = (uint8_t)(t >> 24);
        bytes[4] = (uint8_t)(t >> 32);
        bytes[5] = (uint8_t)(t >> 40);
        bytes[6] = (uint8_t)(t >> 48);
        bytes[7] = (uint8_t)(t >> 56);
    }
    #define UTLP_TIME_TO_BYTES(t, ptr)  utlp_time_to_bytes_esp32(t, ptr)

    /** @brief Size of serialized time in bytes */
    #define UTLP_TIME_SERIAL_SIZE       8

    /** @brief ESP32 supports 64-bit types */
    #define UTLP_NO_64BIT 0

    /** @brief Use native 64-bit time on ESP32 */
    #define UTLP_SEGMENTED_TIME 0

#endif

#ifdef __cplusplus
extern "C" {
#endif

/*============================================================================
 * CONSTANTS
 *==========================================================================*/

#define UTLP_MAC_SIZE           6       /**< MAC address size in bytes */
#define UTLP_MAX_PAYLOAD        200     /**< Maximum packet payload bytes */
#define UTLP_TICK_INTERVAL_US   10000   /**< Physics tick: 100 Hz = 10ms */

/** @brief Actuator Channels (Generic) */
#define UTLP_ACTUATOR_MAIN      0       /**< GPIO15 LED (led_builtin) */
#define UTLP_ACTUATOR_AUX       1       /**< Future expansion */

/*============================================================================
 * TYPES
 *==========================================================================*/

/**
 * @brief Received packet structure
 *
 * Contains hardware-timestamped arrival time for precise offset computation.
 * On C64: rx_timestamp stored as utlp_time_t (union)
 * On ESP32: rx_timestamp stored as uint64_t (native)
 */
typedef struct {
#if UTLP_NO_64BIT
    utlp_time_t rx_timestamp;           /**< HW timestamp of arrival (union) */
#else
    uint64_t rx_timestamp_us;           /**< HW timestamp of arrival (uint64) */
#endif
    uint8_t  payload[UTLP_MAX_PAYLOAD]; /**< Packet payload data */
    size_t   len;                       /**< Payload length in bytes */
    int8_t   rssi;                      /**< Received signal strength */
    uint8_t  mac[UTLP_MAC_SIZE];        /**< Sender's MAC address */
} utlp_packet_t;

/*============================================================================
 * SYSTEM API
 *==========================================================================*/

/**
 * @brief Initialize the HAL layer
 *
 * Sets up WiFi, ESP-NOW, MCPWM (GPIO15), and high-resolution timer.
 * Must be called before any other HAL functions.
 */
void utlp_hal_init(void);

/**
 * @brief Get raw local monotonic time
 *
 * This is the uncorrected hardware timer value.
 * On C64: Returns utlp_time_t (union)
 * On ESP32: Returns uint64_t (native)
 *
 * @return Local time since boot
 */
#if UTLP_NO_64BIT
utlp_time_t utlp_hal_get_time(void);
#else
uint64_t utlp_hal_get_micros(void);
#endif

/**
 * @brief Get synchronized atomic time
 *
 * Returns: local_time + time_offset
 *
 * This is the "truth" that all physics calculations use.
 * Genesis node starts with offset=0 (local time IS atomic time).
 *
 * @return Synchronized time
 */
#if UTLP_NO_64BIT
utlp_time_t utlp_hal_get_atomic_time(void);
#else
uint64_t utlp_hal_get_atomic_time_us(void);
#endif

/**
 * @brief Set the global time offset for synchronization
 *
 * Called when adopting time from a better stratum source.
 * Genesis node never calls this (offset stays 0).
 *
 * @param offset_us Offset to add to local time (32-bit on C64)
 */
#if UTLP_NO_64BIT
void utlp_hal_set_time_offset(int32_t offset_us);
#else
void utlp_hal_set_time_offset(int64_t offset_us);
#endif

/**
 * @brief Yield to RTOS scheduler
 *
 * Feeds watchdog, allows other tasks to run.
 */
void utlp_hal_yield(void);

/*============================================================================
 * RADIO API
 *==========================================================================*/

/**
 * @brief Get this device's MAC address
 *
 * @param[out] mac Buffer to store 6-byte MAC address
 */
void utlp_hal_get_mac(uint8_t *mac);

/**
 * @brief Transmit a packet (broadcast)
 *
 * @param peer_mac Destination MAC (NULL for broadcast)
 * @param data Payload data
 * @param len Payload length
 * @return true if queued successfully
 */
bool utlp_hal_tx_packet(const uint8_t *peer_mac, const uint8_t *data, size_t len);

/**
 * @brief Poll for received packet (non-blocking)
 *
 * @param[out] out_packet Buffer to store received packet
 * @return true if packet available
 */
bool utlp_hal_rx_poll(utlp_packet_t *out_packet);

/**
 * @brief Wait for packet with timeout (blocking)
 *
 * Uses semaphore signaled from receive callback for precision timing.
 * Eliminates polling delay (~4ms → <100us latency).
 *
 * @param[out] out_packet Buffer to store received packet
 * @param timeout_ms Maximum time to wait
 * @return true if packet available, false on timeout
 */
bool utlp_hal_rx_wait(utlp_packet_t *out_packet, uint32_t timeout_ms);

/*============================================================================
 * ACTUATOR API - The Physics Interface
 *
 * Single actuator (GPIO15 LED) driven by MCPWM for phase alignment.
 * This is the visual feedback of time synchronization.
 *==========================================================================*/

/**
 * @brief Set actuator phase-aligned output
 *
 * THE MAGIC FUNCTION: Sets PWM with phase relative to atomic time.
 *
 * For LED blinking at 1Hz:
 *   utlp_hal_set_actuator_phase(UTLP_ACTUATOR_MAIN, 1, UTLP_PHASE(0), UTLP_DUTY(50));
 *
 * Two synchronized nodes with 180° phase offset = perfect alternation:
 *   Node A: phase=0°   → LED ON during first half of cycle
 *   Node B: phase=180° → LED ON during second half of cycle
 *
 * @param channel UTLP_ACTUATOR_MAIN (GPIO15)
 * @param frequency_hz Cycle frequency (e.g., 1Hz for blinking)
 * @param phase_deg Phase offset: float on ESP32, fixed-point on C64 (0-36000 = 0-360°)
 * @param duty_pct Duty cycle: float on ESP32, fixed-point on C64 (0-10000 = 0-100%)
 */
void utlp_hal_set_actuator_phase(int channel, uint32_t frequency_hz,
                                  utlp_float_t phase_deg, utlp_float_t duty_pct);

/**
 * @brief Stop actuator output
 *
 * @param channel Channel to stop
 */
void utlp_hal_actuator_stop(int channel);

/*============================================================================
 * LOGGING API - Platform-Agnostic
 *
 * Abstraction layer for logging. Maps to:
 *   - ESP-IDF: esp_log_writev()
 *   - Arduino: Serial.printf()
 *   - Linux: printf()
 *==========================================================================*/

/**
 * @brief Log informational message
 *
 * @param tag Module identifier for filtering
 * @param format printf-style format string
 */
void utlp_hal_log_info(const char *tag, const char *format, ...);

/**
 * @brief Log error message
 *
 * @param tag Module identifier for filtering
 * @param format printf-style format string
 */
void utlp_hal_log_error(const char *tag, const char *format, ...);

/**
 * @brief Log warning message
 *
 * @param tag Module identifier for filtering
 * @param format printf-style format string
 */
void utlp_hal_log_warn(const char *tag, const char *format, ...);

/*============================================================================
 * APPLICATION ENTRY POINT
 *
 * Call from platform-specific main (app_main, main, setup/loop).
 * This keeps utlp_skeleton.c platform-agnostic.
 *==========================================================================*/

/**
 * @brief UTLP application entry point
 *
 * Call this from your platform's main function:
 *   - ESP-IDF: void app_main(void) { utlp_app_run(); }
 *   - Arduino: void setup() { utlp_app_run(); }
 *   - Linux:   int main() { utlp_app_run(); return 0; }
 */
void utlp_app_run(void);

#ifdef __cplusplus
}
#endif
