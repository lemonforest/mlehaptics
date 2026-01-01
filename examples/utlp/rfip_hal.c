/**
 * @file rfip_hal.c
 * @brief RFIP Hardware Abstraction Layer - ESP32 Implementation
 *
 * @section overview Overview
 *
 * This file implements the RFIP HAL for ESP32 platforms. It performs runtime
 * capability detection based on:
 * - Chip model (ESP32, ESP32-S2, ESP32-C3, ESP32-S3, ESP32-C6)
 * - Silicon revision (critical for ESP32-C6 FTM errata)
 * - IDF configuration (CSI enabled, FTM enabled)
 * - External module probing (UWB via SPI)
 *
 * @section chaos The Chaos Monkey Principle
 *
 * ESP32 DevKit V1 serves as the "Chaos Monkey" - it has NO FTM support.
 * If RFIP works on DevKit V1 using only RSSI/CSI/TDoA, the core algorithm
 * is sound. FTM then becomes calibration, not foundation.
 *
 * @section silicon Silicon Revision Detection
 *
 * ESP32-C6 has known errata for FTM:
 * - ECO0 (v0.0): FTM initiator broken (WIFI-9686 - T3 timestamp wrong)
 * - ECO1 (v0.1): FTM initiator broken (same errata)
 * - ECO2 (v0.2): FTM initiator FIXED
 *
 * The XIAO ESP32-C6 ships with ECO2 silicon (verified), so FTM initiator
 * is available. DevKit V1 has no FTM at all.
 *
 * @see docs/RFIP_Technical_Specification.md - Section 2: Platform Capabilities
 * @see docs/802.11mc_FTM_Reconnaissance_Report.md - FTM errata details
 *
 * @version 0.1.0
 * @date 2025-12-31
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "rfip_hal.h"
#include <stdio.h>
#include <string.h>

/* ESP-IDF includes (only for ESP32 platforms) */
#ifdef ESP_PLATFORM
#include "esp_chip_info.h"
#include "esp_log.h"
#include "esp_wifi.h"
#include "esp_timer.h"
#endif

static const char *TAG = "RFIP_HAL";

/*============================================================================
 * OBSERVATION CACHE
 *
 * Stores recent observations from each peer for position estimation.
 * Updated by rfip_record_observation() called from ESP-NOW RX callback.
 *==========================================================================*/

#define RFIP_MAX_CACHED_PEERS  16  /**< Matches DUNBAR_PEERS */

/**
 * @brief Cached observation for one peer
 *
 * Packed heavy-first: 64-bit → 32-bit → arrays → single bytes
 */
typedef struct {
    int64_t  last_rx_timestamp_us;  /**< Hardware RX timestamp */
    uint32_t last_seen_ms;          /**< System time of observation */
    uint8_t  mac[6];                /**< Peer MAC address */
    int8_t   rssi_dbm;              /**< Last RSSI observation */
    uint8_t  valid;                 /**< Entry is valid */
} rfip_peer_cache_entry_t;

static rfip_peer_cache_entry_t s_peer_cache[RFIP_MAX_CACHED_PEERS];
static int64_t s_last_rx_timestamp_us = 0;

/*============================================================================
 * FORWARD DECLARATIONS
 *==========================================================================*/

static int32_t rfip_impl_get_rssi(const uint8_t *mac);
static int32_t rfip_impl_get_csi(const uint8_t *mac, rfip_csi_data_t *csi);
static int32_t rfip_impl_get_ftm_range(const uint8_t *mac);
static int32_t rfip_impl_get_uwb_range(const uint8_t *mac);
static int64_t rfip_impl_get_rx_timestamp(void);

/*============================================================================
 * SILICON DETECTION
 *==========================================================================*/

bool rfip_has_ftm_initiator(void) {
#ifdef ESP_PLATFORM
    esp_chip_info_t chip_info;
    esp_chip_info(&chip_info);

    /*
     * ESP32-C6 ECO0/ECO1 have errata WIFI-9686 (broken T3 timestamp).
     * Only ECO2+ (revision >= 2) has working FTM initiator.
     *
     * From RFIP Tech Spec Section 2.1:
     * "ECO2 (revision 0.2) and later have FTM initiator fix"
     */
    if (chip_info.model == CHIP_ESP32C6) {
        return (chip_info.revision >= 2);
    }

    /* Other chips with FTM support - all revisions work */
    if (chip_info.model == CHIP_ESP32S2 ||
        chip_info.model == CHIP_ESP32C3 ||
        chip_info.model == CHIP_ESP32S3) {
        return true;
    }

    /* Original ESP32 has no FTM support */
    return false;
#else
    /* Non-ESP platforms - no FTM */
    return false;
#endif
}

bool rfip_probe_uwb(void) {
    /*
     * STUB: UWB probe not implemented
     *
     * When implemented, will:
     * - Initialize SPI bus with DW3000 pins
     * - Send DEV_ID register read command
     * - Verify response matches DW3000 signature
     *
     * See: Makerfabs ESP32-UWB-DW3000 pinout
     * - SPI_SCK:  18
     * - SPI_MISO: 19
     * - SPI_MOSI: 23
     * - DW_CS:    4
     * - DW_RST:   27
     * - DW_IRQ:   34
     */
    return false;
}

/*============================================================================
 * HAL INITIALIZATION
 *==========================================================================*/

void rfip_hal_init(rfip_hal_t *hal) {
    if (hal == NULL) {
        return;
    }

    /* Initialize to known state */
    memset(hal, 0, sizeof(rfip_hal_t));

    /*
     * Layer 0: RSSI is ALWAYS available on all platforms
     * This is our foundation - if nothing else works, we have RSSI
     */
    hal->capabilities = RFIP_CAP_RSSI;
    hal->get_rssi = rfip_impl_get_rssi;
    hal->get_rx_timestamp = rfip_impl_get_rx_timestamp;

    /*
     * Assign all function pointers. Capability flags indicate which
     * are actually functional vs returning "not available".
     */
    hal->get_csi = rfip_impl_get_csi;
    hal->get_ftm_range = rfip_impl_get_ftm_range;
    hal->get_uwb_range = rfip_impl_get_uwb_range;

#ifdef ESP_PLATFORM
    esp_chip_info_t chip_info;
    esp_chip_info(&chip_info);

    /*
     * Layer 3: CSI available on ESP32 family
     * Quality ranking: ESP32-C5 > ESP32-C6 > ESP32-C3 ≈ ESP32-S3 > ESP32
     */
#if CONFIG_IDF_TARGET_ESP32C6 || CONFIG_IDF_TARGET_ESP32S2 || \
    CONFIG_IDF_TARGET_ESP32C3 || CONFIG_IDF_TARGET_ESP32S3 || \
    CONFIG_IDF_TARGET_ESP32
    #if CONFIG_ESP_WIFI_CSI_ENABLED
        hal->capabilities |= RFIP_CAP_CSI;
    #endif
#endif

    /*
     * Layer 2: TDoA from UTLP beacons
     * Requires UTLP sync to be active - always potentially available
     */
    hal->capabilities |= RFIP_CAP_UTLP_TDOA;

    /*
     * Layer 5: FTM capabilities
     * - Responder: Available on all FTM-capable chips
     * - Initiator: Requires silicon check (ESP32-C6 ECO2+)
     */
#if CONFIG_IDF_TARGET_ESP32C6 || CONFIG_IDF_TARGET_ESP32S2 || \
    CONFIG_IDF_TARGET_ESP32C3 || CONFIG_IDF_TARGET_ESP32S3
    #if CONFIG_ESP_WIFI_FTM_ENABLE
        hal->capabilities |= RFIP_CAP_FTM_RESPONDER;

        if (rfip_has_ftm_initiator()) {
            hal->capabilities |= RFIP_CAP_FTM_INITIATOR;
        }
    #endif
#endif

    /*
     * Layer 6: UWB via external DW3000 module
     * Detected via SPI probe at runtime
     */
    if (rfip_probe_uwb()) {
        hal->capabilities |= RFIP_CAP_UWB;
    }

    /* Log detected capabilities */
    char cap_str[64];
    rfip_hal_get_capability_str(hal, cap_str, sizeof(cap_str));

#ifdef ESP_PLATFORM
    ESP_LOGI(TAG, "Silicon: %s rev %d.%d",
             chip_info.model == CHIP_ESP32C6 ? "ESP32-C6" :
             chip_info.model == CHIP_ESP32S3 ? "ESP32-S3" :
             chip_info.model == CHIP_ESP32C3 ? "ESP32-C3" :
             chip_info.model == CHIP_ESP32S2 ? "ESP32-S2" :
             chip_info.model == CHIP_ESP32   ? "ESP32" : "Unknown",
             chip_info.revision / 100,
             chip_info.revision % 100);
    ESP_LOGI(TAG, "RFIP capabilities: %s", cap_str);
#endif

#else
    /* Non-ESP platform - only RSSI available */
    hal->get_rx_timestamp = rfip_stub_get_rx_timestamp;
#endif
}

/*============================================================================
 * CAPABILITY STRING FORMATTING
 *==========================================================================*/

void rfip_hal_get_capability_str(const rfip_hal_t *hal, char *buf, size_t len) {
    if (hal == NULL || buf == NULL || len == 0) {
        if (buf && len > 0) {
            buf[0] = '\0';
        }
        return;
    }

    buf[0] = '\0';
    size_t pos = 0;

    /* Build capability string with | separator */
    struct {
        rfip_capability_t cap;
        const char *name;
    } caps[] = {
        { RFIP_CAP_RSSI,          "RSSI" },
        { RFIP_CAP_CSI,           "CSI" },
        { RFIP_CAP_UTLP_TDOA,     "TDOA" },
        { RFIP_CAP_FTM_INITIATOR, "FTM_INIT" },
        { RFIP_CAP_FTM_RESPONDER, "FTM_RESP" },
        { RFIP_CAP_UWB,           "UWB" },
        { RFIP_CAP_BLE_AOA,       "BLE_AOA" },
    };

    for (size_t i = 0; i < sizeof(caps) / sizeof(caps[0]); i++) {
        if (hal->capabilities & caps[i].cap) {
            size_t name_len = strlen(caps[i].name);
            if (pos + name_len + 2 < len) {  /* +2 for "|" and null */
                if (pos > 0) {
                    buf[pos++] = '|';
                }
                memcpy(buf + pos, caps[i].name, name_len);
                pos += name_len;
                buf[pos] = '\0';
            }
        }
    }

    if (pos == 0) {
        snprintf(buf, len, "NONE");
    }
}

/*============================================================================
 * FTM TIME SYNC EXTRACTION
 *
 * DEVIATION FROM SPEC: This feature is NOT in RFIP_Technical_Specification.md
 * The spec focuses on ranging; we add time sync extraction for UTLP enhancement.
 *==========================================================================*/

int64_t rfip_ftm_calculate_offset(const rfip_ftm_session_result_t *result) {
    if (result == NULL || result->measurement_count == 0) {
        return 0;
    }

    /*
     * NTP-style offset calculation from FTM timestamps:
     *
     *     offset = ((T2 - T1) + (T3 - T4)) / 2
     *
     * Where:
     * - T1: Initiator TX time (our clock)
     * - T2: Responder RX time (peer clock)
     * - T3: Responder TX time (peer clock)
     * - T4: Initiator RX time (our clock)
     *
     * This extracts the clock offset with symmetric delay assumption.
     * The result is in nanoseconds (timestamps are picoseconds / 1000).
     *
     * For multiple measurements, we average to reduce noise.
     */
    int64_t total_offset_ps = 0;
    int valid_count = 0;

    for (int i = 0; i < result->measurement_count && i < 16; i++) {
        const rfip_ftm_measurement_t *m = &result->measurements[i];
        if (!m->valid) {
            continue;
        }

        /* Calculate offset for this measurement */
        int64_t t2_minus_t1 = (int64_t)m->t2_ps - (int64_t)m->t1_ps;
        int64_t t3_minus_t4 = (int64_t)m->t3_ps - (int64_t)m->t4_ps;
        int64_t offset_ps = (t2_minus_t1 + t3_minus_t4) / 2;

        total_offset_ps += offset_ps;
        valid_count++;
    }

    if (valid_count == 0) {
        return 0;
    }

    /* Convert from picoseconds to nanoseconds */
    int64_t avg_offset_ps = total_offset_ps / valid_count;
    return avg_offset_ps / 1000;
}

/*============================================================================
 * OBSERVATION RECORDING API
 *
 * Called from ESP-NOW receive callback to cache observations.
 *==========================================================================*/

/**
 * @brief Find cache entry for a MAC address
 *
 * @param mac 6-byte MAC address
 * @return Pointer to cache entry, or NULL if not found
 */
static rfip_peer_cache_entry_t *rfip_find_peer(const uint8_t *mac) {
    for (int i = 0; i < RFIP_MAX_CACHED_PEERS; i++) {
        if (s_peer_cache[i].valid &&
            memcmp(s_peer_cache[i].mac, mac, 6) == 0) {
            return &s_peer_cache[i];
        }
    }
    return NULL;
}

/**
 * @brief Find or allocate cache entry for a MAC address
 *
 * Uses LRU eviction when cache is full.
 *
 * @param mac 6-byte MAC address
 * @return Pointer to cache entry (always succeeds)
 */
static rfip_peer_cache_entry_t *rfip_get_or_create_peer(const uint8_t *mac) {
    /* First, check if already exists */
    rfip_peer_cache_entry_t *entry = rfip_find_peer(mac);
    if (entry != NULL) {
        return entry;
    }

    /* Find empty slot */
    for (int i = 0; i < RFIP_MAX_CACHED_PEERS; i++) {
        if (!s_peer_cache[i].valid) {
            s_peer_cache[i].valid = 1;
            memcpy(s_peer_cache[i].mac, mac, 6);
            return &s_peer_cache[i];
        }
    }

    /* Cache full - evict oldest (LRU) */
    uint32_t oldest_time = UINT32_MAX;
    int oldest_idx = 0;
    for (int i = 0; i < RFIP_MAX_CACHED_PEERS; i++) {
        if (s_peer_cache[i].last_seen_ms < oldest_time) {
            oldest_time = s_peer_cache[i].last_seen_ms;
            oldest_idx = i;
        }
    }

    memcpy(s_peer_cache[oldest_idx].mac, mac, 6);
    return &s_peer_cache[oldest_idx];
}

void rfip_record_observation(const uint8_t *mac, int8_t rssi_dbm,
                             int64_t rx_timestamp_us) {
    if (mac == NULL) {
        return;
    }

    rfip_peer_cache_entry_t *entry = rfip_get_or_create_peer(mac);

    entry->rssi_dbm = rssi_dbm;
    entry->last_rx_timestamp_us = rx_timestamp_us;

#ifdef ESP_PLATFORM
    entry->last_seen_ms = (uint32_t)(esp_timer_get_time() / 1000);
#else
    entry->last_seen_ms = 0;
#endif

    /* Update global last RX timestamp for TDoA */
    s_last_rx_timestamp_us = rx_timestamp_us;
}

/*============================================================================
 * FUNCTIONAL IMPLEMENTATIONS
 *==========================================================================*/

/**
 * @brief Get last RSSI observation for a peer
 *
 * @param mac 6-byte MAC address
 * @return RSSI in dBm, or -128 if peer unknown
 */
static int32_t rfip_impl_get_rssi(const uint8_t *mac) {
    if (mac == NULL) {
        return -128;
    }

    rfip_peer_cache_entry_t *entry = rfip_find_peer(mac);
    if (entry == NULL) {
        return -128;  /* Peer not in cache */
    }

    return (int32_t)entry->rssi_dbm;
}

/**
 * @brief Get last RX timestamp (for TDoA calculations)
 *
 * Returns the hardware timestamp of the most recent packet reception.
 * On ESP32, this comes from esp_timer_get_time() captured at RX.
 *
 * @return Timestamp in microseconds
 */
static int64_t rfip_impl_get_rx_timestamp(void) {
    return s_last_rx_timestamp_us;
}

/**
 * @brief Get CSI data for a peer
 *
 * Phase 2 implementation - currently returns "not available".
 * Will be implemented when CSI callback is integrated.
 *
 * @param mac 6-byte MAC address
 * @param csi Output buffer for CSI data
 * @return 0 on success, -1 if not available
 */
static int32_t rfip_impl_get_csi(const uint8_t *mac, rfip_csi_data_t *csi) {
    (void)mac;
    (void)csi;
    /* Phase 2: CSI integration pending */
    return -1;
}

/**
 * @brief Get FTM range to a peer
 *
 * Phase 4 implementation - currently returns "not available".
 * Will be implemented when FTM session management is added.
 *
 * @param mac 6-byte MAC address
 * @return Range in millimeters, or -1 if not available
 */
static int32_t rfip_impl_get_ftm_range(const uint8_t *mac) {
    (void)mac;
    /* Phase 4: FTM integration pending */
    return -1;
}

/**
 * @brief Get UWB range to a peer
 *
 * Phase 5 implementation - currently returns "not available".
 * Will be implemented when DW3000 SPI driver is added.
 *
 * @param mac 6-byte MAC address
 * @return Range in millimeters, or -1 if not available
 */
static int32_t rfip_impl_get_uwb_range(const uint8_t *mac) {
    (void)mac;
    /* Phase 5: UWB integration pending */
    return -1;
}

/*============================================================================
 * CACHE MANAGEMENT API
 *==========================================================================*/

uint8_t rfip_get_cached_peer_count(void) {
    uint8_t count = 0;
    for (int i = 0; i < RFIP_MAX_CACHED_PEERS; i++) {
        if (s_peer_cache[i].valid) {
            count++;
        }
    }
    return count;
}

void rfip_clear_cache(void) {
    memset(s_peer_cache, 0, sizeof(s_peer_cache));
    s_last_rx_timestamp_us = 0;
}
