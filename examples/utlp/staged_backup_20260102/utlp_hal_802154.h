/**
 * @file utlp_hal_802154.h
 * @brief HAL Interface for IEEE 802.15.4 Raw MAC Frame Transport
 *
 * @section overview Overview
 *
 * This header defines the HAL interface for 802.15.4-based UTLP transport.
 * It enables cross-manufacturer timing swarms using **raw MAC Data Frames**
 * (NOT ZigBee/Thread/Matter stacks).
 *
 * @section why_raw Why Raw MAC Frames?
 *
 * | Factor | Raw MAC | ZigBee/Thread |
 * |--------|---------|---------------|
 * | Stack size | ~2 KB | ~200 KB |
 * | Certification | None (radio only) | $5000+/year |
 * | Latency | Deterministic | Variable (mesh) |
 * | Complexity | Minimal | Commissioning, clusters |
 * | Cross-vendor | IEEE standard | Stack compatibility issues |
 *
 * UTLP needs only broadcast timing frames - no mesh routing, no security
 * negotiation. Raw MAC is sufficient and optimal.
 *
 * @section frame_format Frame Format
 *
 * @subsection fcf Frame Control Field (FCF): 0x8841
 *
 * ```
 * Bits 0-2:   001  = Frame Type: Data
 * Bit 3:      0    = Security Disabled
 * Bit 4:      0    = Frame Pending: No
 * Bit 5:      0    = ACK Request: No
 * Bit 6:      1    = PAN ID Compression: Yes
 * Bits 7-9:   000  = Reserved
 * Bits 10-11: 10   = Dest Addr Mode: Short (16-bit)
 * Bits 12-13: 00   = Frame Version: 802.15.4-2003
 * Bits 14-15: 11   = Src Addr Mode: Extended (64-bit)
 * ```
 *
 * @subsection complete_frame Complete Frame Structure (28 bytes)
 *
 * ```
 * ┌───────────────┬───────┬────────────────┬─────────────────────┐
 * │ Field         │ Bytes │ Value          │ Description         │
 * ├───────────────┼───────┼────────────────┼─────────────────────┤
 * │ Frame Control │   2   │ 0x8841         │ Data, no ACK        │
 * │ Seq Number    │   1   │ 0-255          │ Auto-increment      │
 * │ Dest PAN ID   │   2   │ 0xCAFE         │ UTLP reserved       │
 * │ Dest Address  │   2   │ 0xFFFF         │ Broadcast           │
 * │ Source Address│   8   │ EUI-64         │ Factory-programmed  │
 * ├───────────────┼───────┼────────────────┼─────────────────────┤
 * │ UTLP Payload  │  11   │ (beacon)       │ Timing beacon       │
 * ├───────────────┼───────┼────────────────┼─────────────────────┤
 * │ FCS (CRC-16)  │   2   │ Auto-calc      │ Hardware CRC        │
 * └───────────────┴───────┴────────────────┴─────────────────────┘
 * ```
 *
 * @section sfd_timestamp SFD-Relative Timestamp Capture
 *
 * CRITICAL: All implementations MUST capture RX timestamps at **SFD
 * (Start Frame Delimiter)** detection, not after MAC processing:
 *
 * ```
 * ┌──────────────────────────────────────────────────────────┐
 * │                 802.15.4 PHY Packet                      │
 * ├──────────┬───────────┬───────────┬───────────────────────┤
 * │ Preamble │    SFD    │    PHR    │      PSDU (MAC)       │
 * │ (32 bits)│  (8 bits) │ (8 bits)  │   (Frame + FCS)       │
 * └──────────┴─────┬─────┴───────────┴───────────────────────┘
 *                  │
 *                  └── T1/T2 capture point (before MAC latency)
 * ```
 *
 * Platform-specific APIs for SFD timestamp:
 * - **MG24 RAIL**: `RAIL_GetRxTimeSyncWordEnd()`
 * - **nRF52840**: `NRF_RADIO->EVENTS_ADDRESS` + Timer capture
 * - **ESP32-C6**: Best-effort software timestamp (hardened ISR)
 *
 * @section cross_vendor Cross-Manufacturer Compatibility
 *
 * | Vendor | Chip | Radio API | Scheduled TX | RX Timestamp | EUI-64 Location |
 * |--------|------|-----------|--------------|--------------|-----------------|
 * | Espressif | ESP32-C6 | ieee802154 | Hardened ISR (±10µs) | SW | efuse |
 * | Silicon Labs | EFR32MG24 | RAIL | Hardware (±1µs) | SFD | DEVINFO |
 * | Nordic | nRF52840 | Radio Driver | PPI (±10µs) | Timer | FICR |
 *
 * @section prior_art Prior Art Claims
 *
 * This interface supports the following prior art claims:
 * - **Claim 237+**: Raw MAC Data Frame for connectionless timing (FCF 0x8841)
 * - **Claim 238+**: Cross-manufacturer 802.15.4 timing mesh
 * - **Claim 239+**: SFD-relative timestamp capture
 * - **Claim 240+**: Reserved PAN ID 0xCAFE for timing namespace
 *
 * @version 1.0.0
 * @date 2026-01-02
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#pragma once

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include "utlp_hal.h"

#ifdef __cplusplus
extern "C" {
#endif

/*============================================================================
 * 802.15.4 CONSTANTS
 *==========================================================================*/

/**
 * @defgroup utlp_154_constants 802.15.4 Protocol Constants
 * @{
 */

/** @brief Reserved PAN ID for UTLP timing traffic */
#define UTLP_154_PAN_ID             0xCAFE

/** @brief Broadcast short address */
#define UTLP_154_BROADCAST          0xFFFF

/** @brief Frame Control Field: Data, no ACK, PAN ID compression, short dest, extended src */
#define UTLP_154_FCF                0x8841

/** @brief Default channel (golden path, near WiFi Ch 6) */
#define UTLP_154_CHANNEL_DEFAULT    15

/** @brief 2.4 GHz band channel range */
#define UTLP_154_CHANNEL_MIN        11
#define UTLP_154_CHANNEL_MAX        26

/** @brief Maximum MAC frame payload (127 - MHR - FCS) */
#define UTLP_154_MAX_PAYLOAD        125

/** @brief EUI-64 address size */
#define UTLP_154_ADDR_SIZE          8

/** @} */ /* utlp_154_constants */

/*============================================================================
 * 802.15.4 CHANNEL MAPPING
 *
 * Reference: IEEE 802.15.4-2020 Table 10-39
 *==========================================================================*/

/**
 * @defgroup utlp_154_channels 802.15.4 Channel Definitions
 * @{
 */

/**
 * @brief Channel to center frequency mapping (2.4 GHz band)
 *
 * Formula: f_c = 2405 + 5 * (channel - 11) MHz
 *
 * | Channel | Center Freq | WiFi Overlap |
 * |---------|-------------|--------------|
 * | 11 | 2.405 GHz | Ch 1 |
 * | 15 | 2.425 GHz | Ch 6 (golden path) |
 * | 20 | 2.450 GHz | Ch 6-7 |
 * | 25 | 2.475 GHz | Ch 11 |
 * | 26 | 2.480 GHz | Ch 11 |
 */
#define UTLP_154_CHANNEL_TO_FREQ_MHZ(ch)    (2405 + 5 * ((ch) - 11))

/** @} */ /* utlp_154_channels */

/*============================================================================
 * 802.15.4 HAL FUNCTIONS
 *==========================================================================*/

/**
 * @defgroup utlp_154_api 802.15.4 HAL API
 * @{
 */

/**
 * @brief Initialize 802.15.4 radio
 *
 * Configures the radio for raw MAC frame transmission/reception:
 * - Sets PAN ID to UTLP_154_PAN_ID (0xCAFE)
 * - Configures promiscuous/coordinator mode for broadcast reception
 * - Sets channel (11-26, default 15)
 *
 * @param channel IEEE 802.15.4 channel number (11-26)
 * @return true on success, false on failure
 */
bool utlp_hal_154_init(uint8_t channel);

/**
 * @brief Get device's factory-programmed EUI-64
 *
 * @param[out] eui64 8-byte buffer to store EUI-64
 */
void utlp_hal_154_get_eui64(uint8_t *eui64);

/**
 * @brief Transmit raw MAC frame immediately
 *
 * Constructs and transmits a raw MAC Data frame:
 * - FCF: 0x8841 (Data, no ACK, PAN compression)
 * - Dest: 0xFFFF (broadcast), PAN: 0xCAFE
 * - Src: Device EUI-64
 * - Payload: UTLP beacon data
 *
 * @param data UTLP payload data (11 bytes for beacon)
 * @param len Payload length
 * @return true if transmission started, false on error
 */
bool utlp_hal_154_tx_frame(const uint8_t *data, size_t len);

/**
 * @brief Schedule frame transmission at absolute time
 *
 * Uses hardware scheduling (MG24 RAIL, nRF52840 PPI) or hardened ISR
 * (ESP32-C6) to achieve deterministic timing for seismic chirp.
 *
 * @section timing_precision Timing Precision
 *
 * | Platform | Method | Precision |
 * |----------|--------|-----------|
 * | ESP32-C6 | Hardened ISR (Level-5 + IRAM) | ±10µs |
 * | MG24 | RAIL_StartScheduledTx() | ±1µs |
 * | nRF52840 | PPI + Radio Timer | ±10µs |
 *
 * @param tx_time_us Absolute time to transmit (microseconds, from atomic clock)
 * @param data UTLP payload data
 * @param len Payload length
 * @return true if scheduled successfully, false on error
 */
bool utlp_hal_154_tx_scheduled(uint64_t tx_time_us, const uint8_t *data, size_t len);

/**
 * @brief Check if platform supports hardware-scheduled TX
 *
 * @return true if utlp_hal_154_tx_scheduled() uses hardware timing,
 *         false if using hardened ISR (ESP32-C6) or spin-wait fallback
 */
bool utlp_hal_154_has_scheduled_tx(void);

/**
 * @brief Poll for received packet (non-blocking)
 *
 * @param[out] out_packet Received packet structure
 * @return true if packet available, false if queue empty
 */
bool utlp_hal_154_rx_poll(utlp_packet_t *out_packet);

/**
 * @brief Wait for packet with timeout (blocking)
 *
 * @param[out] out_packet Received packet structure
 * @param timeout_ms Maximum time to wait (0 = no wait)
 * @return true if packet received, false on timeout
 */
bool utlp_hal_154_rx_wait(utlp_packet_t *out_packet, uint32_t timeout_ms);

/**
 * @brief Get timestamp of last SFD detection
 *
 * Returns the capture time of the most recent Start Frame Delimiter.
 * This is the precise arrival time for time-of-arrival calculations.
 *
 * @return SFD timestamp in microseconds (platform clock)
 */
uint64_t utlp_hal_154_get_last_sfd_time(void);

/**
 * @brief Set TX power
 *
 * @param power_dbm TX power in dBm (platform-specific limits apply)
 * @return true if power set successfully
 */
bool utlp_hal_154_set_tx_power(int8_t power_dbm);

/**
 * @brief Get current TX power
 *
 * @return Current TX power in dBm
 */
int8_t utlp_hal_154_get_tx_power(void);

/**
 * @brief Set channel
 *
 * @param channel IEEE 802.15.4 channel (11-26)
 * @return true if channel set successfully
 */
bool utlp_hal_154_set_channel(uint8_t channel);

/**
 * @brief Get current channel
 *
 * @return Current channel number (11-26)
 */
uint8_t utlp_hal_154_get_channel(void);

/**
 * @brief Enable/disable 802.15.4 radio
 *
 * Used for arbor-specific dormancy (per-transport sleep).
 *
 * @param enable true to enable radio, false to disable
 */
void utlp_hal_154_enable(bool enable);

/**
 * @brief Check if radio is enabled
 *
 * @return true if radio is enabled and operational
 */
bool utlp_hal_154_is_enabled(void);

/** @} */ /* utlp_154_api */

/*============================================================================
 * 802.15.4 CAPABILITY QUERY
 *==========================================================================*/

/**
 * @brief 802.15.4-specific capabilities structure
 *
 * Extends utlp_hal_caps_t with 802.15.4-specific features.
 */
typedef struct {
    bool     has_hardware_sfd_timestamp;    /**< SFD time captured in hardware */
    bool     has_hardware_scheduled_tx;     /**< Hardware TX scheduling (RAIL/PPI) */
    bool     has_hardened_isr;              /**< Level-5 ISR scheduling (ESP32-C6) */
    int8_t   max_tx_power_dbm;              /**< Maximum TX power */
    int8_t   min_tx_power_dbm;              /**< Minimum TX power */
    uint8_t  supported_channels_mask[4];    /**< Bitmask of supported channels */
} utlp_154_caps_t;

/**
 * @brief Query 802.15.4-specific capabilities
 *
 * @param[out] caps Capabilities structure to fill
 */
void utlp_hal_154_get_caps(utlp_154_caps_t *caps);

#ifdef __cplusplus
}
#endif
