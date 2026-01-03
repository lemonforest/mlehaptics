/**
 * @file utlp_arbor.c
 * @brief Per-Transport Selective Dormancy Implementation
 *
 * @section overview Overview
 *
 * This module implements the Arbor/Soma architecture for multi-transport
 * UTLP nodes. Each transport (WiFi/ESP-NOW, 802.15.4, BLE) is a sensory
 * "arbor" (branch) feeding the central phase ("soma").
 *
 * @section prior_art Prior Art Claims
 *
 * This implementation supports the following prior art claims:
 * - **Claim 38**: Hibernation pattern for opportunistic participation
 * - **Claim 231**: Arbor Specific Immunity
 * - **Claim 232**: Identity Separation
 * - **Claim 237+**: Per-transport selective dormancy API
 *
 * @version 1.0.0
 * @date 2026-01-02
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "utlp_arbor.h"
#include "utlp_hal.h"
#include "esp_log.h"
#include "esp_timer.h"
#include <string.h>

#ifdef CONFIG_IEEE802154_ENABLED
#include "esp_ieee802154.h"
#endif

#ifdef CONFIG_ESP_WIFI_ENABLED
#include "esp_wifi.h"
#endif

#ifdef CONFIG_BT_NIMBLE_ENABLED
#include "nimble/nimble_port.h"
#endif

static const char *TAG = "UTLP_ARBOR";

/*============================================================================
 * ARBOR STATE TRACKING
 *==========================================================================*/

/**
 * @brief Internal arbor state structure
 */
typedef struct {
    utlp_arbor_state_t state;           /**< Current operational state */
    bool               registered;       /**< True if arbor has been registered */
    uint8_t            last_stratum;    /**< Stratum before dormancy */
    uint8_t            reentry_stratum; /**< Elevated stratum during WAKING */
    uint32_t           dormant_since;   /**< Timestamp when entered dormancy */
    uint32_t           wakeup_beacons;  /**< Beacons verified since WAKING */
    bool               ledger_preserved; /**< True if reputation snapshot exists */
} arbor_internal_t;

/** @brief Array of arbor states, one per transport type */
static arbor_internal_t s_arbors[UTLP_ARBOR_COUNT] = {0};

/** @brief Flag to track initialization */
static bool s_arbor_initialized = false;

/*============================================================================
 * HELPER FUNCTIONS
 *==========================================================================*/

/**
 * @brief Get current time in milliseconds
 */
static inline uint32_t get_time_ms(void) {
    return (uint32_t)(esp_timer_get_time() / 1000);
}

/**
 * @brief Validate arbor ID
 */
static inline bool is_valid_arbor(utlp_arbor_id_t id) {
    return id < UTLP_ARBOR_COUNT;
}

/**
 * @brief Perform physical layer shutdown for an arbor
 *
 * @param id Arbor to shutdown
 * @return ESP_OK on success
 */
static esp_err_t arbor_phy_shutdown(utlp_arbor_id_t id) {
    esp_err_t ret = ESP_OK;

    switch (id) {
#ifdef CONFIG_ESP_WIFI_ENABLED
        case UTLP_ARBOR_WIFI:
            ret = esp_wifi_stop();
            if (ret == ESP_OK) {
                ESP_LOGI(TAG, "WiFi arbor: Physical layer stopped");
            }
            break;
#endif

#ifdef CONFIG_IEEE802154_ENABLED
        case UTLP_ARBOR_154:
            esp_ieee802154_disable();
            ESP_LOGI(TAG, "802.15.4 arbor: Physical layer disabled");
            break;
#endif

#ifdef CONFIG_BT_NIMBLE_ENABLED
        case UTLP_ARBOR_BLE:
            /* Note: Full NimBLE shutdown is complex; this is simplified */
            ESP_LOGI(TAG, "BLE arbor: Physical layer stop requested");
            /* nimble_port_stop() would go here if full shutdown needed */
            break;
#endif

        default:
            ESP_LOGW(TAG, "Arbor %d: No physical layer handler", id);
            ret = ESP_ERR_NOT_SUPPORTED;
            break;
    }

    return ret;
}

/**
 * @brief Perform physical layer startup for an arbor
 *
 * @param id Arbor to start
 * @return ESP_OK on success
 */
static esp_err_t arbor_phy_startup(utlp_arbor_id_t id) {
    esp_err_t ret = ESP_OK;

    switch (id) {
#ifdef CONFIG_ESP_WIFI_ENABLED
        case UTLP_ARBOR_WIFI:
            ret = esp_wifi_start();
            if (ret == ESP_OK) {
                ESP_LOGI(TAG, "WiFi arbor: Physical layer started");
            }
            break;
#endif

#ifdef CONFIG_IEEE802154_ENABLED
        case UTLP_ARBOR_154:
            ret = esp_ieee802154_enable();
            if (ret == ESP_OK) {
                ESP_LOGI(TAG, "802.15.4 arbor: Physical layer enabled");
            }
            break;
#endif

#ifdef CONFIG_BT_NIMBLE_ENABLED
        case UTLP_ARBOR_BLE:
            ESP_LOGI(TAG, "BLE arbor: Physical layer start requested");
            /* nimble_port_init() would go here if full startup needed */
            break;
#endif

        default:
            ESP_LOGW(TAG, "Arbor %d: No physical layer handler", id);
            ret = ESP_ERR_NOT_SUPPORTED;
            break;
    }

    return ret;
}

/**
 * @brief Broadcast dormancy beacon to peers
 *
 * @param id Arbor entering dormancy
 * @param expected_duration_ms Expected dormancy duration
 */
static void broadcast_dormancy_beacon(utlp_arbor_id_t id, uint32_t expected_duration_ms) {
    /* TODO: Implement dormancy beacon format
     *
     * Beacon format (proposed):
     * - Byte 0: UTLP_BEACON_TYPE_DORMANCY (0xFE)
     * - Byte 1: Arbor ID
     * - Bytes 2-5: Expected duration (ms, little-endian)
     * - Bytes 6-9: Current atomic time (truncated)
     *
     * This allows peers to:
     * 1. Know not to expect beacons from this arbor
     * 2. Distinguish "sleeping" from "dead" (Claim 39)
     * 3. Estimate wake time for coordination
     */
    ESP_LOGI(TAG, "Arbor %s: Broadcasting dormancy beacon (expected: %lu ms)",
             utlp_arbor_name(id), (unsigned long)expected_duration_ms);
}

/**
 * @brief Snapshot arbor's reputation ledger
 *
 * @param id Arbor to snapshot
 */
static void snapshot_ledger(utlp_arbor_id_t id) {
    /* TODO: Integrate with utlp_trust.c
     *
     * This should:
     * 1. Copy arbor-specific peer observations to preserved storage
     * 2. Mark snapshot timestamp
     * 3. Set ledger_preserved flag
     *
     * On wake, the arbor can use this snapshot to:
     * - Quickly identify known peers
     * - Avoid cold-start trust bootstrapping
     * - Maintain continuity of reputation
     */
    s_arbors[id].ledger_preserved = true;
    ESP_LOGD(TAG, "Arbor %s: Ledger snapshot preserved", utlp_arbor_name(id));
}

/**
 * @brief Check if preserved ledger has expired
 *
 * @param id Arbor to check
 * @return true if ledger is stale (exceeded UTLP_MAX_DORMANCY_MS)
 */
static bool is_ledger_expired(utlp_arbor_id_t id) {
    if (!s_arbors[id].ledger_preserved) {
        return true;
    }

    uint32_t dormancy_duration = get_time_ms() - s_arbors[id].dormant_since;
    return dormancy_duration > UTLP_MAX_DORMANCY_MS;
}

/*============================================================================
 * PUBLIC API IMPLEMENTATION
 *==========================================================================*/

void utlp_arbor_init(void) {
    if (s_arbor_initialized) {
        ESP_LOGW(TAG, "Arbor subsystem already initialized");
        return;
    }

    /* Initialize all arbors to ERROR state (unregistered) */
    for (int i = 0; i < UTLP_ARBOR_COUNT; i++) {
        s_arbors[i].state = UTLP_ARBOR_STATE_ERROR;
        s_arbors[i].registered = false;
        s_arbors[i].last_stratum = 0xFF;
        s_arbors[i].reentry_stratum = 0xFF;
        s_arbors[i].dormant_since = 0;
        s_arbors[i].wakeup_beacons = 0;
        s_arbors[i].ledger_preserved = false;
    }

    s_arbor_initialized = true;
    ESP_LOGI(TAG, "Arbor subsystem initialized");
}

esp_err_t utlp_arbor_register(utlp_arbor_id_t id) {
    if (!is_valid_arbor(id)) {
        return ESP_ERR_INVALID_ARG;
    }

    if (s_arbors[id].registered) {
        ESP_LOGW(TAG, "Arbor %s already registered", utlp_arbor_name(id));
        return ESP_ERR_INVALID_STATE;
    }

    s_arbors[id].registered = true;
    s_arbors[id].state = UTLP_ARBOR_STATE_ACTIVE;
    s_arbors[id].last_stratum = 0xFF;  /* Will be set when first beacon received */
    s_arbors[id].reentry_stratum = 0xFF;

    ESP_LOGI(TAG, "Arbor %s registered (ACTIVE)", utlp_arbor_name(id));
    return ESP_OK;
}

esp_err_t utlp_arbor_yield(utlp_arbor_id_t id, const utlp_dormancy_params_t *params) {
    if (!is_valid_arbor(id)) {
        return ESP_ERR_INVALID_ARG;
    }

    if (!s_arbors[id].registered) {
        ESP_LOGE(TAG, "Arbor %s not registered", utlp_arbor_name(id));
        return ESP_ERR_INVALID_STATE;
    }

    if (s_arbors[id].state == UTLP_ARBOR_STATE_DORMANT) {
        ESP_LOGW(TAG, "Arbor %s already dormant", utlp_arbor_name(id));
        return ESP_ERR_INVALID_STATE;
    }

    /* Apply defaults if params not provided */
    utlp_dormancy_params_t default_params = {
        .expected_duration_ms = 0,      /* Indefinite */
        .broadcast_beacon = true,
        .preserve_ledger = true
    };
    const utlp_dormancy_params_t *p = params ? params : &default_params;

    /* 1. Snapshot reputation ledger */
    if (p->preserve_ledger) {
        snapshot_ledger(id);
    }

    /* 2. Broadcast dormancy beacon to peers */
    if (p->broadcast_beacon) {
        broadcast_dormancy_beacon(id, p->expected_duration_ms);
    }

    /* 3. Physical layer shutdown */
    esp_err_t ret = arbor_phy_shutdown(id);
    if (ret != ESP_OK && ret != ESP_ERR_NOT_SUPPORTED) {
        ESP_LOGE(TAG, "Arbor %s: Physical shutdown failed: %s",
                 utlp_arbor_name(id), esp_err_to_name(ret));
        return ret;
    }

    /* 4. Update state */
    s_arbors[id].dormant_since = get_time_ms();
    s_arbors[id].state = UTLP_ARBOR_STATE_DORMANT;

    ESP_LOGI(TAG, "Arbor %s YIELDED (dormant)", utlp_arbor_name(id));
    return ESP_OK;
}

esp_err_t utlp_arbor_wake(utlp_arbor_id_t id) {
    if (!is_valid_arbor(id)) {
        return ESP_ERR_INVALID_ARG;
    }

    if (!s_arbors[id].registered) {
        return ESP_ERR_INVALID_STATE;
    }

    if (s_arbors[id].state != UTLP_ARBOR_STATE_DORMANT) {
        ESP_LOGW(TAG, "Arbor %s not dormant (state=%d)",
                 utlp_arbor_name(id), s_arbors[id].state);
        return ESP_ERR_INVALID_STATE;
    }

    /* Check if ledger has expired */
    if (is_ledger_expired(id)) {
        ESP_LOGW(TAG, "Arbor %s: Ledger expired (dormant too long), clearing",
                 utlp_arbor_name(id));
        s_arbors[id].ledger_preserved = false;
        /* TODO: Clear actual ledger data in utlp_trust.c */
    }

    /* Physical layer startup */
    esp_err_t ret = arbor_phy_startup(id);
    if (ret != ESP_OK && ret != ESP_ERR_NOT_SUPPORTED) {
        ESP_LOGE(TAG, "Arbor %s: Physical startup failed: %s",
                 utlp_arbor_name(id), esp_err_to_name(ret));
        s_arbors[id].state = UTLP_ARBOR_STATE_ERROR;
        return ret;
    }

    /* DEGRADED RE-ENTRY: Enter at elevated stratum (lower authority) */
    s_arbors[id].reentry_stratum = s_arbors[id].last_stratum + UTLP_DEGRADED_REENTRY_PENALTY;

    /* Clamp to maximum stratum */
    if (s_arbors[id].reentry_stratum > 15) {
        s_arbors[id].reentry_stratum = 15;
    }

    s_arbors[id].wakeup_beacons = 0;
    s_arbors[id].state = UTLP_ARBOR_STATE_WAKING;

    ESP_LOGI(TAG, "Arbor %s WAKING (degraded re-entry, stratum %d->%d, need %d beacons)",
             utlp_arbor_name(id),
             s_arbors[id].last_stratum,
             s_arbors[id].reentry_stratum,
             UTLP_REENTRY_VERIFY_BEACONS);

    return ESP_OK;
}

esp_err_t utlp_arbor_force_wake(utlp_arbor_id_t id) {
    if (!is_valid_arbor(id)) {
        return ESP_ERR_INVALID_ARG;
    }

    if (!s_arbors[id].registered) {
        return ESP_ERR_INVALID_STATE;
    }

    ESP_LOGW(TAG, "Arbor %s: FORCE WAKE (skipping degraded re-entry)", utlp_arbor_name(id));

    /* Physical layer startup */
    esp_err_t ret = arbor_phy_startup(id);
    if (ret != ESP_OK && ret != ESP_ERR_NOT_SUPPORTED) {
        s_arbors[id].state = UTLP_ARBOR_STATE_ERROR;
        return ret;
    }

    /* Skip degraded re-entry - go directly to ACTIVE */
    s_arbors[id].state = UTLP_ARBOR_STATE_ACTIVE;
    s_arbors[id].reentry_stratum = s_arbors[id].last_stratum;
    s_arbors[id].wakeup_beacons = 0;

    return ESP_OK;
}

utlp_arbor_state_t utlp_arbor_get_state(utlp_arbor_id_t id) {
    if (!is_valid_arbor(id)) {
        return UTLP_ARBOR_STATE_ERROR;
    }
    return s_arbors[id].state;
}

esp_err_t utlp_arbor_get_status(utlp_arbor_id_t id, utlp_arbor_status_t *status) {
    if (!is_valid_arbor(id) || status == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    if (!s_arbors[id].registered) {
        return ESP_ERR_INVALID_STATE;
    }

    status->id = id;
    status->state = s_arbors[id].state;
    status->last_stratum = s_arbors[id].last_stratum;
    status->reentry_stratum = s_arbors[id].reentry_stratum;
    status->dormant_since = s_arbors[id].dormant_since;
    status->wakeup_beacons = s_arbors[id].wakeup_beacons;

    return ESP_OK;
}

bool utlp_arbor_can_tx(utlp_arbor_id_t id) {
    if (!is_valid_arbor(id)) {
        return false;
    }
    return s_arbors[id].registered &&
           s_arbors[id].state == UTLP_ARBOR_STATE_ACTIVE;
}

bool utlp_arbor_can_rx(utlp_arbor_id_t id) {
    if (!is_valid_arbor(id)) {
        return false;
    }
    return s_arbors[id].registered &&
           (s_arbors[id].state == UTLP_ARBOR_STATE_ACTIVE ||
            s_arbors[id].state == UTLP_ARBOR_STATE_WAKING);
}

esp_err_t utlp_arbor_beacon_verified(utlp_arbor_id_t id) {
    if (!is_valid_arbor(id)) {
        return ESP_ERR_INVALID_ARG;
    }

    if (s_arbors[id].state != UTLP_ARBOR_STATE_WAKING) {
        return ESP_ERR_INVALID_STATE;
    }

    s_arbors[id].wakeup_beacons++;

    ESP_LOGD(TAG, "Arbor %s: Beacon verified (%lu/%d)",
             utlp_arbor_name(id),
             (unsigned long)s_arbors[id].wakeup_beacons,
             UTLP_REENTRY_VERIFY_BEACONS);

    /* Check if verification threshold reached */
    if (s_arbors[id].wakeup_beacons >= UTLP_REENTRY_VERIFY_BEACONS) {
        /* Transition to ACTIVE with restored stratum */
        s_arbors[id].state = UTLP_ARBOR_STATE_ACTIVE;
        s_arbors[id].reentry_stratum = s_arbors[id].last_stratum;

        ESP_LOGI(TAG, "Arbor %s: Re-entry complete, stratum restored to %d",
                 utlp_arbor_name(id), s_arbors[id].last_stratum);
    }

    return ESP_OK;
}

const char* utlp_arbor_name(utlp_arbor_id_t id) {
    switch (id) {
        case UTLP_ARBOR_WIFI:  return "WiFi";
        case UTLP_ARBOR_154:   return "15.4";
        case UTLP_ARBOR_BLE:   return "BLE";
        default:               return "Unknown";
    }
}

uint8_t utlp_arbor_active_count(void) {
    uint8_t count = 0;
    for (int i = 0; i < UTLP_ARBOR_COUNT; i++) {
        if (s_arbors[i].registered &&
            s_arbors[i].state == UTLP_ARBOR_STATE_ACTIVE) {
            count++;
        }
    }
    return count;
}

uint8_t utlp_arbor_registered_count(void) {
    uint8_t count = 0;
    for (int i = 0; i < UTLP_ARBOR_COUNT; i++) {
        if (s_arbors[i].registered) {
            count++;
        }
    }
    return count;
}

/*============================================================================
 * STRATUM MANAGEMENT (for protocol layer integration)
 *==========================================================================*/

/**
 * @brief Update arbor's last known stratum
 *
 * Called by protocol layer when stratum changes. This is used for:
 * 1. Determining re-entry stratum after dormancy
 * 2. Tracking arbor authority level
 *
 * @param id Arbor to update
 * @param stratum New stratum value
 */
void utlp_arbor_set_stratum(utlp_arbor_id_t id, uint8_t stratum) {
    if (!is_valid_arbor(id) || !s_arbors[id].registered) {
        return;
    }

    s_arbors[id].last_stratum = stratum;

    /* If currently WAKING, update re-entry stratum too */
    if (s_arbors[id].state == UTLP_ARBOR_STATE_WAKING) {
        s_arbors[id].reentry_stratum = stratum + UTLP_DEGRADED_REENTRY_PENALTY;
        if (s_arbors[id].reentry_stratum > 15) {
            s_arbors[id].reentry_stratum = 15;
        }
    }
}

/**
 * @brief Get arbor's effective stratum
 *
 * Returns the stratum that should be used for beacon transmission:
 * - ACTIVE: Returns last_stratum
 * - WAKING: Returns reentry_stratum (elevated, lower authority)
 * - DORMANT/ERROR: Returns 0xFF (should not transmit)
 *
 * @param id Arbor to query
 * @return Effective stratum, or 0xFF if arbor cannot transmit
 */
uint8_t utlp_arbor_get_effective_stratum(utlp_arbor_id_t id) {
    if (!is_valid_arbor(id) || !s_arbors[id].registered) {
        return 0xFF;
    }

    switch (s_arbors[id].state) {
        case UTLP_ARBOR_STATE_ACTIVE:
            return s_arbors[id].last_stratum;

        case UTLP_ARBOR_STATE_WAKING:
            return s_arbors[id].reentry_stratum;

        case UTLP_ARBOR_STATE_DORMANT:
        case UTLP_ARBOR_STATE_ERROR:
        default:
            return 0xFF;
    }
}
