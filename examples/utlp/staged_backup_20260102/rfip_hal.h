/**
 * @file rfip_hal.h
 * @brief RFIP Hardware Abstraction Layer
 *
 * @section purpose Purpose
 *
 * This HAL enables the same RFIP positioning code to run across devices with
 * vastly different hardware capabilities. A DevKit V1 (no FTM) and an
 * ESP32-C6 (full FTM, CSI) can participate in the same swarm, with each
 * contributing what it can.
 *
 * @section philosophy Design Philosophy
 *
 * **Build from always-available, let fancy stuff enhance:**
 *
 * | Layer | Source | Precision | Always Available |
 * |-------|--------|-----------|------------------|
 * | 0 | RSSI | ~3-5m | Yes (all platforms) |
 * | 1 | RSSI differential | ~1-3m | Yes |
 * | 2 | TDoA from UTLP beacons | ~30cm | Yes (requires UTLP sync) |
 * | 3 | CSI | ~50cm-1m | Yes (ESP32 family) |
 * | 4 | Multipath signatures | Fingerprint | Yes (learned) |
 * | 5 | 802.11mc FTM | ~10-50cm | Platform-dependent |
 * | 6 | UWB (DW3000) | ~10cm | Add-on only |
 *
 * The HAL queries capabilities at runtime and exposes them as flags.
 * Application code checks flags before using features.
 *
 * @section silicon Silicon Revision Detection
 *
 * ESP32-C6 ECO0/ECO1 have errata WIFI-9686 (broken T3 timestamp for FTM).
 * Only ECO2+ (silicon v0.2+) has working FTM initiator. The HAL detects
 * this at runtime so nodes can advertise accurate capabilities.
 *
 * @section chaos The "Chaos Monkey" Principle
 *
 * ESP32 DevKit V1 has NO FTM support. It serves as our "Chaos Monkey":
 * if RFIP works on DevKit V1 using only RSSI/CSI/TDoA, it works anywhere.
 * FTM then becomes calibration, not foundation.
 *
 * @see docs/RFIP_Technical_Specification.md - Section 2: Platform Capabilities
 * @see docs/802.11mc_FTM_Reconnaissance_Report.md - FTM research notes
 *
 * @version 0.1.0
 * @date 2025-12-31
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
 * STRUCT PACKING CONVENTION (Memory Alignment Optimization)
 *
 * Always order struct fields from largest to smallest alignment:
 *   1. 8-byte fields first (int64_t, uint64_t, double, pointers on 64-bit)
 *   2. 4-byte fields (int32_t, uint32_t, float)
 *   3. 2-byte fields (int16_t, uint16_t)
 *   4. 1-byte fields and arrays (uint8_t, bool, char[])
 *
 * This minimizes padding bytes inserted by the compiler for alignment.
 * See utlp_trust.h for detailed example with BAD/GOOD comparison.
 *==========================================================================*/

/*============================================================================
 * CAPABILITY FLAGS
 *
 * Runtime-detected capabilities. Query silicon version, probe for external
 * modules, check IDF config. Each bit represents one observation source.
 *==========================================================================*/

/**
 * @brief RFIP capability flags (bitmask)
 *
 * Detected at runtime via rfip_hal_init(). Application code checks flags
 * before attempting to use specific observation sources.
 *
 * @see docs/RFIP_Technical_Specification.md - Section 2.3
 */
typedef enum {
    RFIP_CAP_RSSI          = (1 << 0),  /**< RSSI from packets (all platforms) */
    RFIP_CAP_CSI           = (1 << 1),  /**< Channel State Information (ESP32 family) */
    RFIP_CAP_UTLP_TDOA     = (1 << 2),  /**< TDoA from UTLP beacons (requires sync) */
    RFIP_CAP_FTM_INITIATOR = (1 << 3),  /**< 802.11mc FTM initiator (ESP32-S2/C3/S3, C6 ECO2+) */
    RFIP_CAP_FTM_RESPONDER = (1 << 4),  /**< 802.11mc FTM responder (all FTM-capable chips) */
    RFIP_CAP_UWB           = (1 << 5),  /**< UWB ranging (external DW1000/DW3000 module) */
    RFIP_CAP_BLE_AOA       = (1 << 6),  /**< BLE 5.1 Angle of Arrival (future, requires antenna array) */
} rfip_capability_t;

/*============================================================================
 * OBSERVATION TYPES
 *
 * Each observation source produces different data. The fusion layer combines
 * these into a unified position estimate.
 *==========================================================================*/

/**
 * @brief Type of observation source
 *
 * Used to tag rfip_observation_t so fusion layer knows how to interpret data.
 */
typedef enum {
    RFIP_OBS_RSSI,   /**< RSSI-based (single value, noisy) */
    RFIP_OBS_CSI,    /**< CSI-based (subcarrier amplitude/phase) */
    RFIP_OBS_TDOA,   /**< Time Difference of Arrival from UTLP beacons */
    RFIP_OBS_FTM,    /**< 802.11mc Fine Time Measurement */
    RFIP_OBS_UWB,    /**< Ultra-wideband ranging */
    RFIP_OBS_AOA,    /**< Angle of Arrival (BLE 5.1) */
} rfip_obs_type_t;

/**
 * @brief CSI data buffer (opaque to application)
 *
 * Contains raw [Imag, Real] pairs for each OFDM subcarrier.
 * Interpretation handled by CSI-specific processing functions.
 */
typedef struct {
    int8_t  *data;   /**< Buffer of [Imag, Real] pairs per subcarrier */
    size_t   len;    /**< Buffer length in bytes */
} rfip_csi_data_t;

/**
 * @brief Generic observation from any source
 *
 * Packed heavy-first: 64-bit → union → 8-bit arrays → single bytes
 *
 * @see docs/RFIP_Technical_Specification.md - Section 5.1
 */
typedef struct {
    /* 8-byte fields first */
    int64_t         timestamp_us;    /**< UTLP atomic time of observation */

    /* Union - size determined by largest member */
    union {
        struct {
            int8_t *data;
            size_t  len;
        } csi;                        /**< CSI data (pointer + length) */
        struct {
            int64_t tdoa_us;          /**< Time difference in microseconds */
            uint8_t anchor_mac[6];    /**< MAC of reference anchor */
        } tdoa;                       /**< TDoA observation */
        struct {
            uint32_t range_mm;        /**< Range in millimeters */
        } ftm;                        /**< FTM observation */
        struct {
            uint32_t range_mm;        /**< Range in millimeters */
        } uwb;                        /**< UWB observation */
        struct {
            float azimuth;            /**< Horizontal angle in degrees */
            float elevation;          /**< Vertical angle in degrees */
        } aoa;                        /**< AoA observation */
        struct {
            int8_t rssi_dbm;          /**< RSSI in dBm */
        } rssi;                       /**< RSSI observation */
    };

    /* 1-byte arrays */
    uint8_t         peer_mac[6];     /**< MAC address of observed peer */

    /* Single bytes */
    rfip_obs_type_t type;            /**< Observation type (enum, 1 byte) */
    uint8_t         confidence;      /**< Confidence 0-255 (maps to 0.0-1.0) */
} rfip_observation_t;

/*============================================================================
 * HAL STRUCTURE
 *
 * Function pointers for platform-specific implementations. Initialized by
 * rfip_hal_init() based on runtime capability detection.
 *==========================================================================*/

/**
 * @brief RFIP Hardware Abstraction Layer
 *
 * Contains capability flags and function pointers for observation sources.
 * Application code calls rfip_hal_init() once at boot, then uses function
 * pointers for platform-agnostic observation collection.
 *
 * Packed heavy-first: pointers (4/8 bytes) → enum (4 bytes)
 */
typedef struct {
    /* Function pointers (4 or 8 bytes depending on platform) */
    int32_t (*get_rssi)(const uint8_t *mac);
    int32_t (*get_csi)(const uint8_t *mac, rfip_csi_data_t *csi);
    int32_t (*get_ftm_range)(const uint8_t *mac);
    int32_t (*get_uwb_range)(const uint8_t *mac);
    int64_t (*get_rx_timestamp)(void);

    /* 4-byte fields */
    rfip_capability_t capabilities;  /**< Bitmask of available capabilities */
} rfip_hal_t;

/*============================================================================
 * FTM SESSION STRUCTURES
 *
 * DEVIATION FROM SPEC: These structures are NOT in RFIP_Technical_Specification.md
 * They add FTM session management with raw T1-T4 timestamps for:
 * - Time sync extraction (NTP-style offset from FTM)
 * - Per-measurement analysis
 * - Data logging for research
 *
 * @note Consider adding to spec after validation.
 *==========================================================================*/

/**
 * @brief Single FTM measurement with raw timestamps
 *
 * Contains the four timestamps from 802.11mc RTT exchange, enabling:
 * - Distance calculation: RTT = (t4-t1) - (t3-t2); distance = RTT * c / 2
 * - Time sync extraction: offset = ((t2-t1) + (t3-t4)) / 2
 *
 * Timestamps are in picoseconds for maximum precision (WiFi timing).
 *
 * Packed heavy-first: 64-bit → 32-bit → 8-bit
 */
typedef struct {
    /* 8-byte fields first */
    uint64_t t1_ps;        /**< Initiator TX timestamp (picoseconds) */
    uint64_t t2_ps;        /**< Responder RX timestamp (picoseconds) */
    uint64_t t3_ps;        /**< Responder TX timestamp (picoseconds) */
    uint64_t t4_ps;        /**< Initiator RX timestamp (picoseconds) */

    /* 4-byte fields */
    uint32_t rtt_ns;       /**< Calculated RTT (nanoseconds) */
    int32_t  distance_cm;  /**< Calculated distance (centimeters) */

    /* 1-byte fields */
    int8_t   rssi;         /**< RSSI of measurement exchange */
    bool     valid;        /**< Measurement completed successfully */
} rfip_ftm_measurement_t;

/**
 * @brief Complete FTM session result
 *
 * Contains multiple measurements from one FTM session, plus aggregated
 * metrics. The clock_offset_ns field enables UTLP precision enhancement
 * from ±30μs to ±100ns when FTM is available.
 *
 * Packed heavy-first: 64-bit → 32-bit → array → 8-bit
 */
typedef struct {
    /* 8-byte fields first */
    int64_t  clock_offset_ns;  /**< Extracted clock offset for UTLP time sync */

    /* 4-byte fields */
    uint32_t avg_rtt_ns;       /**< Average RTT across measurements */
    int32_t  avg_distance_cm;  /**< Average distance (centimeters) */

    /* Arrays (large allocation) */
    rfip_ftm_measurement_t measurements[16];  /**< Individual measurements */

    /* 1-byte fields and arrays */
    uint8_t  peer_mac[6];      /**< MAC of FTM peer */
    uint8_t  measurement_count; /**< Number of valid measurements */
    bool     success;          /**< Session completed successfully */
} rfip_ftm_session_result_t;

/*============================================================================
 * METRICS STRUCTURE
 *
 * DEVIATION FROM SPEC: Research observability for RFIP performance analysis.
 *
 * @note Consider adding to spec after validation.
 *==========================================================================*/

/**
 * @brief RFIP metrics for data logging and analysis
 *
 * Tracks observation counts, FTM session statistics, and fusion quality.
 * Designed for research data collection - "we love data and it's mostly free!"
 *
 * Packed heavy-first: 64-bit → 32-bit → 16-bit → 8-bit
 */
typedef struct {
    /* 8-byte fields first */
    int64_t  ftm_offset_ns;           /**< Most recent FTM-derived clock offset */
    int64_t  espnow_offset_us;        /**< Most recent ESP-NOW-derived offset */

    /* 4-byte fields */
    uint32_t sessions_initiated;      /**< FTM sessions started */
    uint32_t sessions_successful;     /**< FTM sessions completed */
    uint32_t sessions_failed;         /**< FTM sessions failed */
    uint32_t avg_rtt_ns;              /**< Running average RTT */
    int32_t  distance_cm;             /**< Most recent distance estimate */
    int32_t  distance_variance_cm;    /**< Distance variance */
    uint32_t ftm_session_duration_ms; /**< Typical session duration */

    /* 2-byte fields */
    uint16_t csi_observations;        /**< CSI observations collected */
    uint16_t rssi_observations;       /**< RSSI observations collected */

    /* 1-byte fields */
    uint8_t  fusion_quality;          /**< Overall position quality 0-255 */
} rfip_metrics_t;

/*============================================================================
 * PUBLIC API
 *==========================================================================*/

/**
 * @brief Initialize the RFIP HAL with runtime capability detection
 *
 * Probes silicon version, checks IDF configuration, and sets capability
 * flags. Also initializes function pointers for available observation
 * sources.
 *
 * Call once at boot before any RFIP operations.
 *
 * @param[out] hal  HAL structure to initialize
 */
void rfip_hal_init(rfip_hal_t *hal);

/**
 * @brief Check if FTM initiator is available on this silicon
 *
 * ESP32-C6 ECO0/ECO1 have errata WIFI-9686 (broken T3 timestamp).
 * ECO2+ (revision >= 2) has the fix.
 *
 * This function queries the chip revision at runtime to determine
 * if FTM initiator functionality is available.
 *
 * @return true if FTM initiator is functional
 *
 * @see docs/RFIP_Technical_Specification.md - Section 2.1
 */
bool rfip_has_ftm_initiator(void);

/**
 * @brief Probe for external UWB module (DW1000/DW3000)
 *
 * Attempts SPI communication with DW3000 at configured pins.
 * Returns true if valid device ID response received.
 *
 * @return true if UWB module detected and responding
 */
bool rfip_probe_uwb(void);

/**
 * @brief Check if capability is available
 *
 * Convenience function to test a single capability flag.
 *
 * @param[in] hal  Initialized HAL structure
 * @param[in] cap  Capability flag to check
 * @return true if capability is available
 */
static inline bool rfip_has_capability(const rfip_hal_t *hal, rfip_capability_t cap) {
    return (hal->capabilities & cap) != 0;
}

/**
 * @brief Get human-readable capability string
 *
 * Returns a string describing available capabilities for logging.
 * Example: "RSSI|CSI|FTM_INIT|FTM_RESP"
 *
 * @param[in] hal  Initialized HAL structure
 * @param[out] buf Output buffer (minimum 64 bytes recommended)
 * @param[in] len  Buffer length
 */
void rfip_hal_get_capability_str(const rfip_hal_t *hal, char *buf, size_t len);

/**
 * @brief Calculate clock offset from FTM measurement
 *
 * Uses NTP-style formula: offset = ((T2-T1) + (T3-T4)) / 2
 *
 * This enables upgrading UTLP precision from ±30μs to ±100ns
 * when FTM is available.
 *
 * DEVIATION FROM SPEC: Time sync extraction not in RFIP_Technical_Specification.md
 * Spec focuses on ranging; this adds time sync capability.
 *
 * @param[in] result  FTM session result with T1-T4 timestamps
 * @return Clock offset in nanoseconds
 */
int64_t rfip_ftm_calculate_offset(const rfip_ftm_session_result_t *result);

/*============================================================================
 * OBSERVATION RECORDING API
 *
 * Called from ESP-NOW receive callback to feed observations into RFIP.
 *==========================================================================*/

/**
 * @brief Record an RSSI observation for a peer
 *
 * Call this from the ESP-NOW receive callback to cache RSSI and timestamp
 * data for position estimation. The observation is stored in an internal
 * cache indexed by MAC address.
 *
 * @param[in] mac            6-byte MAC address of the sender
 * @param[in] rssi_dbm       RSSI of received packet in dBm
 * @param[in] rx_timestamp_us Hardware RX timestamp in microseconds
 *
 * @code
 * // Example: In ESP-NOW receive callback
 * void espnow_recv_cb(const uint8_t *mac, const uint8_t *data, int len) {
 *     int64_t rx_time = esp_timer_get_time();
 *     int8_t rssi = wifi_pkt->rx_ctrl.rssi;  // From promiscuous header
 *     rfip_record_observation(mac, rssi, rx_time);
 * }
 * @endcode
 */
void rfip_record_observation(const uint8_t *mac, int8_t rssi_dbm,
                             int64_t rx_timestamp_us);

/**
 * @brief Get the number of peers in the observation cache
 *
 * @return Number of peers with recent observations
 */
uint8_t rfip_get_cached_peer_count(void);

/**
 * @brief Clear all cached observations
 *
 * Use when resetting RFIP state or for testing.
 */
void rfip_clear_cache(void);

#ifdef __cplusplus
}
#endif
