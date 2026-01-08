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
 * The "swarm truth" - what all nodes agree is the current time.
 *
 * **Implementation Options:**
 *
 * 1. **Software-based (Legacy):** `atomic_time = local_time + time_offset`
 *    - Genesis node has offset=0; followers calculate from beacon exchange
 *    - Simple, works on any platform
 *
 * 2. **HPLAC (Hardware Phase Locked Atomic Coherency):**
 *    - Atomic time derived from MCPWM hardware timer
 *    - `atomic_time = (cycle_count × 1000000) + (ticks × 20) + epoch_offset`
 *    - Single-register atomic phase: 50kHz × 50000 = 1 second cycle
 *    - See utlp_phase.h for full API
 *
 * @par Philosophy:
 * "Physics First: Hardware defines time, not software."
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
 * @version 3.0.0 - Transport-agnostic addressing + scheduled TX
 * @date 2026-01-02
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#pragma once

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include "utlp_config.h"  /* SSOT for all UTLP constants */

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

/* UTLP_BLINK_PERIOD_US defined in utlp_config.h (SSOT) */

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

#define UTLP_MAX_PAYLOAD        200     /**< Maximum packet payload bytes */
#define UTLP_TICK_INTERVAL_US   10000   /**< Physics tick: 100 Hz = 10ms */

/** @brief Actuator Channels (Generic) */
#define UTLP_ACTUATOR_MAIN      0       /**< GPIO15 LED (led_builtin) */
#define UTLP_ACTUATOR_AUX       1       /**< Future expansion */

/*============================================================================
 * TRANSPORT-AGNOSTIC ADDRESS ABSTRACTION
 *
 * @section addr_overview Overview
 *
 * Supports variable-length addresses across different radio transports:
 * - ESP32 ESP-NOW: 6-byte MAC (IEEE 802.11)
 * - 802.15.4:      8-byte EUI-64 (MG24, nRF52, etc.)
 * - Future:        IPv6 (16 bytes), custom protocols
 *
 * @section addr_design Design Rationale
 *
 * The HAL abstracts address handling so protocol code doesn't need to know
 * whether it's running over ESP-NOW (6-byte MAC) or 802.15.4 (8-byte EUI-64).
 * This enables:
 * - Single protocol codebase across platforms
 * - Future transport additions without protocol changes
 * - Proper address comparison (different lengths are never equal)
 *
 * @section addr_interop Interoperability Note
 *
 * Addresses from different transports exist in separate namespaces:
 * - A 6-byte ESP32 MAC cannot directly address an 8-byte 802.15.4 EUI-64
 * - Bridge devices (e.g., ESP32-C6 with both WiFi and Thread) can translate
 * - Protocol layer treats addresses opaquely via utlp_hal_addr_*() functions
 *
 * @section addr_refs References
 *
 * - IEEE 802.11-2020: MAC addresses (OUI + NIC-specific)
 * - IEEE 802.15.4-2020: EUI-64 extended addresses
 * - RFC 4291: IPv6 Addressing Architecture (future)
 *==========================================================================*/

/** @brief Maximum address size in bytes (EUI-64) */
#define UTLP_ADDR_MAX_SIZE      8

/** @brief Legacy MAC size for backward compatibility */
#define UTLP_MAC_SIZE           6

/**
 * @brief Transport-agnostic address structure
 *
 * Contains variable-length address with explicit length field.
 * Addresses from different transports are NOT comparable unless
 * explicitly mapped (e.g., via bridge device).
 *
 * @par Memory Layout
 * @code
 * +--------+--------+--------+--------+--------+--------+--------+--------+-----+
 * | addr[0]| addr[1]| addr[2]| addr[3]| addr[4]| addr[5]| addr[6]| addr[7]| len |
 * +--------+--------+--------+--------+--------+--------+--------+--------+-----+
 *   MSB                                                              LSB    1-8
 * @endcode
 *
 * @par Usage Examples
 * @code
 * // Get this device's address
 * utlp_addr_t my_addr;
 * utlp_hal_get_addr(&my_addr);
 *
 * // Compare addresses
 * if (utlp_hal_addr_equal(&peer_addr, &my_addr)) { ... }
 *
 * // Format for logging
 * char buf[24];  // "AA:BB:CC:DD:EE:FF:GG:HH" + null
 * utlp_hal_addr_to_string(&addr, buf, sizeof(buf));
 * @endcode
 */
typedef struct {
    uint8_t  addr[UTLP_ADDR_MAX_SIZE];  /**< Address bytes (MSB first) */
    uint8_t  len;                        /**< Actual length (6 or 8) */
} utlp_addr_t;

/*============================================================================
 * TYPES
 *==========================================================================*/

/**
 * @brief Received packet structure
 *
 * Contains hardware-timestamped arrival time for precise offset computation.
 *
 * @note Anonymous union provides backward compatibility:
 *       - pkt->mac[i] works for legacy code (first 6 bytes)
 *       - pkt->src_addr is preferred for new code (transport-agnostic)
 *
 * @section arbor_id Arbor ID (Phase 9 - Blood-Brain Barrier)
 *
 * The arbor_id field identifies which transport received this packet:
 *   - 0 = UTLP_ARBOR_WIFI (ESP-NOW)
 *   - 1 = UTLP_ARBOR_154 (IEEE 802.15.4)
 *   - 2 = UTLP_ARBOR_BLE (Bluetooth LE)
 *
 * This enables per-arbor trust tracking in the Metabolic Ledger (Blood-Brain
 * Barrier). A peer that is healthy on 802.15.4 but jittery on WiFi should
 * have independent health scores for each transport.
 *
 * @see utlp_arbor.h for utlp_arbor_id_t enum definition
 */
typedef struct {
    uint64_t rx_timestamp_us;           /**< HW timestamp of arrival */
    uint8_t  payload[UTLP_MAX_PAYLOAD]; /**< Packet payload data */
    size_t   len;                       /**< Payload length in bytes */
    int8_t   rssi;                      /**< Received signal strength */
    uint8_t  arbor_id;                  /**< Transport that received this (0=WiFi, 1=154, 2=BLE) */
    union {
        uint8_t     mac[UTLP_MAC_SIZE]; /**< @deprecated Use src_addr */
        utlp_addr_t src_addr;           /**< Sender's address (preferred) */
    };
} utlp_packet_t;

/**
 * @brief Scheduled transmission request
 *
 * For platforms with hardware TX scheduling (e.g., MG24 RAIL).
 * Allows deterministic timing of seismic chirp bursts.
 *
 * @section sched_tx_overview Overview
 *
 * Scheduled TX enables hardware-precise timing for the seismic chirp pattern.
 * Instead of spin-waiting between bursts (±100µs jitter), all 3 bursts are
 * queued upfront with absolute timestamps. The radio hardware handles the
 * timing, achieving ±1µs precision.
 *
 * @section sched_tx_platforms Platform Support
 *
 * | Platform | Scheduling API | Precision | Notes |
 * |----------|----------------|-----------|-------|
 * | ESP32 ESP-NOW | None (spin-wait fallback) | ±100µs | Software timing |
 * | MG24 RAIL | RAIL_StartScheduledTx() | ±1µs | Hardware scheduling |
 * | nRF52 (future) | IEEE 802.15.4 TX time | ±10µs | Radio timer |
 * | Zephyr 802.15.4 | IEEE802154_TX_MODE_TXTIME | varies | Driver-dependent |
 *
 * @section sched_tx_pattern API Pattern
 *
 * Follows Silicon Labs RAIL API precedent:
 * - RAIL_StartTx(): Immediate transmission
 * - RAIL_StartScheduledTx(): Hardware-scheduled transmission
 *
 * UTLP exposes this via:
 * - utlp_hal_tx_packet(): Immediate transmission
 * - utlp_hal_tx_schedule(): Hardware-scheduled transmission
 * - utlp_hal_has_scheduled_tx(): Capability check
 *
 * @section sched_tx_refs References
 *
 * - Silicon Labs RAIL API: https://docs.silabs.com/rail/latest/
 * - Zephyr IEEE 802.15.4: IEEE802154_TX_MODE_TXTIME
 * - SAE 2024-01-2989: Time-controlled hardware access patterns
 *
 * @par Usage Example
 * @code
 * // Schedule 3 bursts for seismic chirp
 * utlp_scheduled_tx_t bursts[3];
 * uint64_t now = utlp_hal_get_micros();
 *
 * for (int i = 0; i < 3; i++) {
 *     bursts[i].tx_time_us = now + (i * 2000);  // 0, 2ms, 4ms
 *     build_payload(bursts[i].payload, &bursts[i].len);
 * }
 *
 * if (utlp_hal_has_scheduled_tx()) {
 *     utlp_hal_tx_schedule(bursts, 3);
 * } else {
 *     // Fall back to spin-wait
 * }
 * @endcode
 */
typedef struct {
    uint64_t tx_time_us;                /**< Absolute atomic time to transmit */
    uint8_t  payload[UTLP_MAX_PAYLOAD]; /**< Payload data */
    size_t   len;                       /**< Payload length in bytes */
} utlp_scheduled_tx_t;

/**
 * @brief Platform capabilities structure
 *
 * Allows protocol layer to adapt to available platform features.
 * Queried once at startup to determine optimal algorithms.
 *
 * @section caps_philosophy Philosophy
 *
 * Rather than #ifdef per platform, UTLP uses runtime capability discovery.
 * This enables:
 * - Single protocol binary across platforms (future)
 * - Graceful degradation on constrained platforms
 * - Clear documentation of what features are available
 *
 * @section caps_fields Field Descriptions
 *
 * | Field | Description | ESP32 | MG24 |
 * |-------|-------------|-------|------|
 * | has_scheduled_tx | Hardware TX scheduling | false | true |
 * | has_hw_timestamp | Hardware RX timestamps | true | true |
 * | addr_size | Native address length | 6 | 8 |
 * | max_payload | Max payload bytes | 200 | 125 |
 * | tx_power_dbm | Current TX power | ~20 | ~19 |
 * | channel | Current channel | 6 | 15 |
 *
 * @par Usage Example
 * @code
 * utlp_hal_caps_t caps;
 * utlp_hal_get_caps(&caps);
 *
 * if (caps.has_scheduled_tx) {
 *     // Use hardware scheduling for precise timing
 * } else {
 *     // Fall back to spin-wait
 * }
 * @endcode
 */
typedef struct {
    bool     has_scheduled_tx;          /**< Hardware TX scheduling available */
    bool     has_hw_timestamp;          /**< Hardware RX timestamps available */
    uint8_t  addr_size;                 /**< Native address size (6 or 8) */
    uint8_t  max_payload;               /**< Max payload bytes */
    int8_t   tx_power_dbm;              /**< Current TX power */
    uint16_t channel;                   /**< Current channel number */
} utlp_hal_caps_t;

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

/*----------------------------------------------------------------------------
 * Address Operations (Transport-Agnostic)
 *--------------------------------------------------------------------------*/

/**
 * @brief Get this device's transport address
 *
 * Returns the native address for this transport:
 * - ESP32 ESP-NOW: 6-byte MAC
 * - 802.15.4:      8-byte EUI-64
 *
 * @param[out] addr Address structure to fill
 */
void utlp_hal_get_addr(utlp_addr_t *addr);

/**
 * @brief Compare two addresses for equality
 *
 * @note Addresses of different lengths are never equal.
 *
 * @param a First address
 * @param b Second address
 * @return true if addresses are identical
 */
bool utlp_hal_addr_equal(const utlp_addr_t *a, const utlp_addr_t *b);

/**
 * @brief Format address as human-readable string
 *
 * Produces colon-separated hex: "AA:BB:CC:DD:EE:FF" (6-byte)
 * or "AA:BB:CC:DD:EE:FF:GG:HH" (8-byte)
 *
 * @param addr Address to format
 * @param[out] buf Output buffer (minimum 24 bytes for EUI-64)
 * @param buf_len Buffer size
 */
void utlp_hal_addr_to_string(const utlp_addr_t *addr, char *buf, size_t buf_len);

/**
 * @brief Compute hash of address for peer table lookup
 *
 * @param addr Address to hash
 * @return 32-bit hash value
 */
uint32_t utlp_hal_addr_hash(const utlp_addr_t *addr);

/**
 * @brief Get this device's MAC address (DEPRECATED)
 *
 * @deprecated Use utlp_hal_get_addr() for transport-agnostic code.
 *             This function only returns the first 6 bytes.
 *
 * @param[out] mac Buffer to store 6-byte MAC address
 */
void utlp_hal_get_mac(uint8_t *mac);

/*----------------------------------------------------------------------------
 * Packet Transmission
 *--------------------------------------------------------------------------*/

/**
 * @brief Transmit a packet immediately (broadcast)
 *
 * @param peer_mac Destination MAC (NULL for broadcast)
 * @param data Payload data
 * @param len Payload length
 * @return true if queued successfully
 */
bool utlp_hal_tx_packet(const uint8_t *peer_mac, const uint8_t *data, size_t len);

/**
 * @brief Check if platform supports hardware-scheduled TX
 *
 * Scheduled TX allows hardware-precise timing for seismic chirp.
 * The protocol layer uses this to select between scheduling paths:
 *
 * @code
 * if (utlp_hal_has_scheduled_tx()) {
 *     // Use utlp_hal_tx_schedule() for ±1µs precision
 * } else {
 *     // Use spin-wait for ±100µs precision
 * }
 * @endcode
 *
 * @section has_sched_platforms Platform Support
 *
 * | Platform | Returns | Reason |
 * |----------|---------|--------|
 * | ESP32 ESP-NOW | false | No hardware scheduling API |
 * | MG24 RAIL | true | RAIL_StartScheduledTx() available |
 * | Zephyr 802.15.4 | varies | Depends on driver |
 *
 * @note Analogous to checking RAIL capabilities in Silicon Labs SDK
 *
 * @return true if utlp_hal_tx_schedule() uses hardware scheduling,
 *         false if it falls back to spin-wait
 */
bool utlp_hal_has_scheduled_tx(void);

/**
 * @brief Schedule multiple packets for future transmission
 *
 * Queues packets with absolute timestamps for hardware-precise timing.
 * On platforms with scheduling support (MG24 RAIL), achieves ±1µs precision.
 * On other platforms (ESP32), falls back to spin-wait with ±100µs precision.
 *
 * @section tx_sched_atomicity Atomicity
 *
 * All packets are queued atomically - either all succeed or none.
 * If any packet fails to queue, the function returns false and
 * no packets are transmitted.
 *
 * @section tx_sched_timing Timing Diagram
 *
 * @code
 * Traditional (ESP32 spin-wait):
 * ┌────┐     ┌────┐     ┌────┐
 * │TX 0│wait │TX 1│wait │TX 2│   ← Jitter from RTOS scheduler
 * └────┘2ms  └────┘2ms  └────┘
 *        ±100µs    ±100µs
 *
 * Scheduled TX (MG24 RAIL):
 * t=now: Schedule(TX0@t, TX1@t+2ms, TX2@t+4ms)
 *        │
 *        ▼
 * ┌────┐     ┌────┐     ┌────┐
 * │TX 0│     │TX 1│     │TX 2│   ← Hardware-precise timing
 * └────┘     └────┘     └────┘
 *      2.000ms    2.000ms         ← ±1µs precision
 * @endcode
 *
 * @section tx_sched_impl Implementation Notes
 *
 * **ESP32 (fallback):** Spin-waits until each tx_time_us, then transmits.
 * This ties up the CPU but avoids RTOS scheduler jitter.
 *
 * **MG24 RAIL:** Uses RAIL_StartScheduledTx() with RAIL_TIME_ABSOLUTE mode.
 * Packets are queued to the radio FIFO and hardware handles timing.
 *
 * @note Analogous to RAIL_StartScheduledTx() in Silicon Labs RAIL API
 * @see utlp_hal_has_scheduled_tx() to check if hardware scheduling available
 * @see utlp_hal_tx_packet() for immediate (non-scheduled) transmission
 *
 * @param packets Array of scheduled transmissions (tx_time_us must be absolute)
 * @param count   Number of packets to schedule (typically 3 for seismic chirp)
 * @return true if all packets scheduled successfully, false on any failure
 */
bool utlp_hal_tx_schedule(const utlp_scheduled_tx_t *packets, size_t count);

/*----------------------------------------------------------------------------
 * Packet Reception
 *--------------------------------------------------------------------------*/

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

/*----------------------------------------------------------------------------
 * Platform Capabilities
 *--------------------------------------------------------------------------*/

/**
 * @brief Query platform capabilities
 *
 * Allows protocol layer to adapt to available features.
 *
 * @param[out] caps Capabilities structure to fill
 */
void utlp_hal_get_caps(utlp_hal_caps_t *caps);

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
 * TELEMETRY API - Physics and Status Data for Intron
 *
 * These functions provide data for the encrypted Intron payload.
 * Default implementations return safe placeholder values.
 *==========================================================================*/

/**
 * @brief Get NTP wall-clock time (or random if stealth mode)
 *
 * For normal operation: Returns UTC timestamp from NTP sync.
 * For stealth mode: Returns random value to prevent correlation attacks.
 *
 * @return NTP timestamp (microseconds since epoch) or random value
 */
uint64_t utlp_hal_get_ntp_time_utc(void);

/**
 * @brief Get current TX power setting
 *
 * @return TX power in dBm (-40 to +21 typical range)
 */
int8_t utlp_hal_get_tx_power_dbm(void);

/**
 * @brief Get battery level scaled to 0-255
 *
 * @return Battery level (0=empty, 255=full) or 127 if not available
 */
uint8_t utlp_hal_get_battery_scaled(void);

/**
 * @brief Get CPU load percentage
 *
 * @return CPU load (0-100%) or 0 if not available
 */
uint8_t utlp_hal_get_cpu_load(void);

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

/**
 * @brief Log debug message
 *
 * Debug messages are typically filtered out in production builds.
 * Use for verbose diagnostics that would spam the console.
 *
 * @param tag Module identifier for filtering
 * @param format printf-style format string
 */
void utlp_hal_log_debug(const char *tag, const char *format, ...);

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
