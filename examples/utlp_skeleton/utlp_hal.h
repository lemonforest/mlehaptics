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
 * @version 2.0.0 - Simplified Genesis Node
 * @date 2025-12-28
 */

#pragma once

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

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
 * @brief Get raw local monotonic time in microseconds
 *
 * This is the uncorrected hardware timer value.
 *
 * @return Local time in microseconds since boot
 */
uint64_t utlp_hal_get_micros(void);

/**
 * @brief Get synchronized atomic time in microseconds
 *
 * Returns: local_time + time_offset
 *
 * This is the "truth" that all physics calculations use.
 * Genesis node starts with offset=0 (local time IS atomic time).
 *
 * @return Synchronized time in microseconds
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
 *   utlp_hal_set_actuator_phase(UTLP_ACTUATOR_MAIN, 1, 0.0, 50.0);
 *
 * Two synchronized nodes with 180° phase offset = perfect alternation:
 *   Node A: phase=0°   → LED ON during first half of cycle
 *   Node B: phase=180° → LED ON during second half of cycle
 *
 * @param channel UTLP_ACTUATOR_MAIN (GPIO15)
 * @param frequency_hz Cycle frequency (e.g., 1Hz for blinking)
 * @param phase_deg Phase offset (0-360) relative to atomic time
 * @param duty_pct Duty cycle / brightness (0-100)
 */
void utlp_hal_set_actuator_phase(int channel, uint32_t frequency_hz,
                                  float phase_deg, float duty_pct);

/**
 * @brief Stop actuator output
 *
 * @param channel Channel to stop
 */
void utlp_hal_actuator_stop(int channel);

#ifdef __cplusplus
}
#endif
