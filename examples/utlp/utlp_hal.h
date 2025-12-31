/**
 * @file utlp_hal.h
 * @brief Hardware Abstraction Layer - Universal Time Lord Protocol
 *
 * @section overview Overview
 *
 * This HAL abstracts hardware-specific operations for UTLP, enabling the
 * protocol to run on different platforms (ESP32, C64, future targets).
 * The ESP32 implementation uses ESP-NOW for radio and MCPWM for actuators.
 *
 * @section philosophy Design Philosophy
 *
 * @subsection philosophy_genesis 1. Genesis First
 * A UTLP device works alone. Peers are optional enhancements, not requirements.
 * The first device in a zone IS the atomic clock - it doesn't need permission.
 *
 * @subsection philosophy_physics 2. Time-Indexed Execution
 * Physical outputs (LEDs, motors) are calculated from atomic time, not toggled
 * by delays. Instead of:
 * @code
 * led_on();
 * delay(500);
 * led_off();
 * @endcode
 * We use:
 * @code
 * bool should_be_on = (atomic_time % 1000000) < 500000;
 * set_led(should_be_on);
 * @endcode
 * This is **drift-proof** because we recalculate state every tick.
 *
 * @subsection philosophy_malloc 3. No Dynamic Allocation
 * All memory is statically allocated. No malloc, no free, no fragmentation.
 * This enables:
 * - Predictable memory usage (important for embedded systems)
 * - No memory leaks (can't leak what you don't allocate)
 * - Easier security analysis (no heap corruption vulnerabilities)
 *
 * @subsection philosophy_hal 4. Platform Abstraction
 * The HAL hides platform differences behind a clean API:
 * - ESP32: Uses esp_timer_get_time(), ESP-NOW, MCPWM
 * - C64: Uses CIA timer, custom radio, PWM via VIC-II tricks
 * - Future: STM32, nRF52, etc.
 *
 * @section timing Timing Architecture
 *
 * UTLP distinguishes between two time domains:
 *
 * @subsection timing_local Local Time (utlp_hal_get_micros)
 * The raw hardware timer value. Monotonically increasing, never modified.
 * This is the "ground truth" for the local oscillator.
 *
 * @subsection timing_atomic Atomic Time (utlp_hal_get_atomic_time_us)
 * Local time + time_offset. This is the "swarm truth" - what all nodes
 * agree is the current time. Genesis node has offset=0; followers have
 * offset calculated from beacon exchange.
 *
 * @par Formula:
 * @code
 * atomic_time = local_time + time_offset
 * @endcode
 *
 * @par Why Dual Clocks?
 * We never modify the system clock. This avoids:
 * - Watchdog timer confusion
 * - Timestamp discontinuities
 * - Scheduler timing issues
 *
 * @section radio Radio Architecture
 *
 * UTLP uses connectionless broadcast for all communication:
 * - No pairing, no handshaking, no connection state
 * - Every beacon is a broadcast (NULL destination MAC)
 * - Hardware timestamps captured at RX for precision
 *
 * @par Why Connectionless?
 * Connections require state. State requires memory. Memory runs out.
 * A device with 1000 peers would need 1000 connection structures.
 * With connectionless broadcast, a device can hear from unlimited peers
 * using fixed memory (the Metabolic Ledger's 12 slots).
 *
 * @section implementations Platform Implementations
 *
 * | Platform | Timer Source      | Radio      | Actuator    |
 * |----------|-------------------|------------|-------------|
 * | ESP32    | esp_timer (64-bit)| ESP-NOW    | MCPWM/LEDC  |
 * | C64      | CIA + extension   | Custom RF  | VIC-II      |
 * | Skeleton | Abstract (union)  | Abstract   | Abstract    |
 *
 * @see examples/utlp_skeleton/ for the platform-agnostic reference
 *
 * @version 2.2.0 - ESP32-focused (forked from skeleton)
 * @date 2025-12-29
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#pragma once

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/*============================================================================
 * TYPE DEFINITIONS - Native 64-bit
 *==========================================================================*/

/** @brief Native floating point type */
typedef float utlp_float_t;

/** @brief Convert degrees to internal representation (identity on ESP32) */
#define UTLP_PHASE(deg)  (deg)

/** @brief Convert percentage to internal representation (identity on ESP32) */
#define UTLP_DUTY(pct)   (pct)

/*============================================================================
 * TIME OPERATIONS - Native 64-bit
 *
 * ESP32 has hardware 64-bit math - use it directly.
 *==========================================================================*/

/** @brief Standard blink period in microseconds */
#define UTLP_BLINK_PERIOD_US    1000000UL

/** @brief Get phase position using native modulo */
#define UTLP_GET_PHASE(t, p)    ((uint32_t)((t) % (p)))

/** @brief Get time difference using native subtraction */
#define UTLP_DIFF_US(now, last) ((int64_t)((now) - (last)))

/** @brief Alias for compatibility */
#define UTLP_TIME_DIFF(a, b)    UTLP_DIFF_US(a, b)

/** @brief Add microseconds using native addition */
#define UTLP_ADD_US(t, us)      ((t) += (us))

/** @brief Get low 32 bits */
#define UTLP_TIME_LOW32(t)      ((uint32_t)(t))

/** @brief Compare times for less-than */
#define UTLP_TIME_LT(a, b)      ((a) < (b))

/** @brief Compare times for greater-or-equal */
#define UTLP_TIME_GE(a, b)      ((a) >= (b))

/** @brief Compare times for equality */
#define UTLP_TIME_EQ(a, b)      ((a) == (b))

/** @brief Size of serialized time in bytes */
#define UTLP_TIME_SERIAL_SIZE   8

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
 */
typedef struct {
    uint64_t rx_timestamp_us;           /**< HW timestamp of arrival */
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
 *
 * @return Local time in microseconds
 */
uint64_t utlp_hal_get_micros(void);

/**
 * @brief Get synchronized atomic time
 *
 * Returns: local_time + time_offset
 *
 * This is the "truth" that all physics calculations use.
 * Genesis node starts with offset=0 (local time IS atomic time).
 *
 * @return Synchronized atomic time in microseconds
 */
uint64_t utlp_hal_get_atomic_time_us(void);

/**
 * @brief Set the global time offset for synchronization
 *
 * Called when adopting time from a better stratum source.
 * Genesis node never calls this (offset stays 0).
 *
 * @param offset_us Offset to add to local time
 */
void utlp_hal_set_time_offset(int64_t offset_us);

/**
 * @brief Yield to RTOS scheduler
 *
 * Feeds watchdog, allows other tasks to run.
 */
void utlp_hal_yield(void);

/*============================================================================
 * SYNCHRONIZATION API
 *
 * Semaphore primitives for thread-safe communication.
 * Abstracts FreeRTOS (or other RTOS) semaphore implementation.
 *==========================================================================*/

/**
 * @brief Opaque semaphore handle
 *
 * Platform-specific implementation hidden behind void pointer.
 * ESP32: Maps to SemaphoreHandle_t
 */
typedef void* utlp_hal_semaphore_t;

/**
 * @brief Create a counting semaphore
 *
 * @param max_count   Maximum count value (1 for binary semaphore)
 * @param initial     Initial count value
 * @return Semaphore handle, or NULL on failure
 */
utlp_hal_semaphore_t utlp_hal_semaphore_create(uint32_t max_count, uint32_t initial);

/**
 * @brief Take (acquire) a semaphore
 *
 * Blocks until semaphore is available or timeout expires.
 *
 * @param sem        Semaphore handle
 * @param timeout_ms Maximum time to wait (0 = no wait, UINT32_MAX = forever)
 * @return true if semaphore acquired, false on timeout
 */
bool utlp_hal_semaphore_take(utlp_hal_semaphore_t sem, uint32_t timeout_ms);

/**
 * @brief Give (release) a semaphore
 *
 * Increments the semaphore count, potentially unblocking waiting tasks.
 *
 * @param sem Semaphore handle
 */
void utlp_hal_semaphore_give(utlp_hal_semaphore_t sem);

/**
 * @brief Delete a semaphore
 *
 * Frees resources associated with the semaphore.
 * Behavior is undefined if tasks are waiting on the semaphore.
 *
 * @param sem Semaphore handle
 */
void utlp_hal_semaphore_delete(utlp_hal_semaphore_t sem);

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
 * @param phase_deg Phase offset in degrees (0-360)
 * @param duty_pct Duty cycle percentage (0-100)
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
 * LOGGING API - ESP-IDF Integration
 *
 * Maps to ESP-IDF logging system (esp_log.h).
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
 * Call from platform-specific main (app_main for ESP-IDF).
 *==========================================================================*/

/**
 * @brief UTLP application entry point
 *
 * Call this from your platform's main function:
 *   - ESP-IDF: void app_main(void) { utlp_app_run(); }
 */
void utlp_app_run(void);

#ifdef __cplusplus
}
#endif
