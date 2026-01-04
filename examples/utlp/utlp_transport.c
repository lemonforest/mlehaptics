/**
 * @file utlp_transport.c
 * @brief Multi-Transport Management Layer Implementation
 *
 * @section overview Overview
 *
 * This module implements the transport management layer that enables UTLP
 * to operate over multiple transports simultaneously. On ESP32-C6, this
 * includes ESP-NOW (WiFi) and IEEE 802.15.4.
 *
 * @section coexistence Hardware Coexistence
 *
 * ESP32-C6 has a **hardware coexistence arbiter** that time-divisions the
 * 2.4GHz radio between WiFi, BLE, and 802.15.4. We don't do software
 * multiplexing - we just initialize each transport and let the hardware
 * sort out the timing.
 *
 * This is critical: There's ONE 2.4GHz radio, but THREE PHY layers can
 * share it because the hardware arbiter handles slot allocation.
 *
 * @section usage Usage
 *
 * **Option A: Application specifies transports**
 * @code
 * utlp_transport_config_t cfg = UTLP_TRANSPORT_CONFIG_DEFAULT();
 * cfg.transports = UTLP_TRANSPORT_ESPNOW;  // WiFi only
 * utlp_transport_init(&cfg);
 * @endcode
 *
 * **Option B: Auto-detect all available transports (for testing)**
 * @code
 * utlp_transport_init(NULL);  // Probe and enable all
 * @endcode
 *
 * @section prior_art Prior Art Claims
 *
 * - **Claim 243**: Arbor/Soma Multi-Transport Architecture
 * - **Claim 244**: Selective Arbor Yield (per-transport dormancy)
 * - **Claim 245**: Degraded Re-Entry with Stratum Penalty
 *
 * @version 1.0.0
 * @date 2026-01-02
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "utlp_transport.h"
#include "utlp_hal.h"
#include "utlp_arbor.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"
#include "sdkconfig.h"

#include <string.h>

/* Platform-specific includes */
#if defined(CONFIG_SOC_IEEE802154_SUPPORTED) && CONFIG_SOC_IEEE802154_SUPPORTED
#include "utlp_hal_802154.h"
#define HAVE_802154 1
#else
#define HAVE_802154 0
#endif

#if defined(CONFIG_ESP_WIFI_ENABLED) || defined(CONFIG_WIFI_ENABLED)
#define HAVE_ESPNOW 1
#else
#define HAVE_ESPNOW 0
#endif

static const char *TAG = "UTLP_TRANSPORT";

/*============================================================================
 * STATE VARIABLES
 *==========================================================================*/

/** @brief Initialization state */
static bool s_initialized = false;

/** @brief Per-transport initialization state (idempotency guards) */
static bool s_espnow_initialized = false;
static bool s_154_initialized = false;
static bool s_ble_initialized = false;

/** @brief Current configuration */
static utlp_transport_config_t s_config;

/** @brief Current status */
static utlp_transport_status_t s_status = {0};

/** @brief Unified RX queue (aggregates from all transports) */
static QueueHandle_t s_rx_queue = NULL;

/** @brief RX semaphore for blocking wait */
static SemaphoreHandle_t s_rx_sem = NULL;

/** @brief Queue depth for unified RX queue */
#define UNIFIED_RX_QUEUE_DEPTH  16

/** @brief Timer handle for delayed ESP-NOW startup */
static esp_timer_handle_t s_delayed_espnow_timer = NULL;

/** @brief Flag to track pending delayed startup */
static bool s_espnow_pending = false;

/*============================================================================
 * FORWARD DECLARATIONS
 *==========================================================================*/

static bool init_espnow_transport(void);
static bool init_154_transport(uint8_t channel);
static void route_rx_to_unified_queue(const utlp_packet_t *pkt);
static void delayed_espnow_timer_callback(void *arg);
static bool enable_transport_internal(utlp_transport_t transport);

/*============================================================================
 * TRANSPORT PROBING
 *==========================================================================*/

uint8_t utlp_transport_probe(void)
{
    uint8_t available = UTLP_TRANSPORT_NONE;

#if HAVE_ESPNOW
    /*
     * ESP-NOW is available on all ESP32 variants with WiFi
     * Check at compile time via CONFIG_ESP_WIFI_ENABLED
     */
    available |= UTLP_TRANSPORT_ESPNOW;
    ESP_LOGI(TAG, "Probe: ESP-NOW available (WiFi enabled)");
#endif

#if HAVE_802154
    /*
     * 802.15.4 is only available on ESP32-C6 and ESP32-H2
     * Check at compile time via CONFIG_SOC_IEEE802154_SUPPORTED
     */
    available |= UTLP_TRANSPORT_154;
    ESP_LOGI(TAG, "Probe: 802.15.4 available (C6/H2 radio)");
#endif

    /* BLE probing would go here (future) */

    if (available == UTLP_TRANSPORT_NONE) {
        ESP_LOGW(TAG, "Probe: No transports available!");
    }

    return available;
}

/*============================================================================
 * TRANSPORT INITIALIZATION
 *==========================================================================*/

bool utlp_transport_init(const utlp_transport_config_t *config)
{
    if (s_initialized) {
        ESP_LOGW(TAG, "Transport layer already initialized");
        return true;
    }

    ESP_LOGI(TAG, "Initializing transport layer");

    /* Use defaults if no config provided */
    if (config) {
        s_config = *config;
    } else {
        /* Option B: Auto-detect all available with staggered startup */
        s_config.transports = UTLP_TRANSPORT_ALL;
        s_config.channel_154 = 15;  /* Golden path */
        s_config.tx_mode = UTLP_TX_MODE_BEST;
        s_config.stagger_espnow_ms = 15000;  /* 15 second delay for testing */
    }

    /* Probe available transports */
    s_status.available = utlp_transport_probe();

    /* If TRANSPORT_ALL requested, use all available */
    if (s_config.transports == UTLP_TRANSPORT_ALL) {
        s_config.transports = s_status.available;
    }

    /* Check if any requested transports are unavailable */
    uint8_t unavailable = s_config.transports & ~s_status.available;
    if (unavailable) {
        ESP_LOGW(TAG, "Requested transports 0x%02X not available", unavailable);
        s_config.transports &= s_status.available;
    }

    if (s_config.transports == UTLP_TRANSPORT_NONE) {
        ESP_LOGE(TAG, "No transports to initialize!");
        return false;
    }

    /* Create unified RX queue (only once) */
    if (!s_rx_queue) {
        s_rx_queue = xQueueCreate(UNIFIED_RX_QUEUE_DEPTH, sizeof(utlp_packet_t));
    }
    if (!s_rx_sem) {
        s_rx_sem = xSemaphoreCreateCounting(UNIFIED_RX_QUEUE_DEPTH, 0);
    }

    if (!s_rx_queue || !s_rx_sem) {
        ESP_LOGE(TAG, "Failed to create unified RX queue/semaphore");
        return false;
    }

    /* Initialize arbor subsystem (idempotent) */
    utlp_arbor_init();

    bool any_success = false;

    /*
     * STAGGERED STARTUP LOGIC
     *
     * When both 802.15.4 and ESP-NOW are available:
     * 1. Start 802.15.4 immediately (better timing, deterministic)
     * 2. Delay ESP-NOW by stagger_espnow_ms (default 15s)
     *
     * This enables testing scenarios:
     * - Pure 802.15.4 synchronization (first 15 seconds)
     * - What happens when 15.4 genesis meets WiFi genesis
     * - Arbor isolation and coexistence behavior
     */

    /*
     * Initialize 802.15.4 transport FIRST (15.4 arbor)
     * This gets priority because it has better timing characteristics.
     */
    if (s_config.transports & UTLP_TRANSPORT_154) {
        if (enable_transport_internal(UTLP_TRANSPORT_154)) {
            any_success = true;
        }
    }

    /*
     * Initialize ESP-NOW transport (WiFi arbor)
     * If 802.15.4 actually initialized and stagger is set, delay this.
     *
     * IMPORTANT: Check s_status.enabled (actual init success), not just
     * what was requested. If 802.15.4 init failed (e.g., stub on ESP32-C6),
     * there's no point delaying ESP-NOW.
     */
    if (s_config.transports & UTLP_TRANSPORT_ESPNOW) {
        bool has_154_working = (s_status.enabled & UTLP_TRANSPORT_154);
        if (has_154_working && s_config.stagger_espnow_ms > 0) {
            /* Schedule delayed ESP-NOW startup */
            esp_timer_create_args_t timer_args = {
                .callback = delayed_espnow_timer_callback,
                .arg = NULL,
                .dispatch_method = ESP_TIMER_TASK,
                .name = "espnow_delay"
            };

            if (esp_timer_create(&timer_args, &s_delayed_espnow_timer) == ESP_OK) {
                uint64_t delay_us = (uint64_t)s_config.stagger_espnow_ms * 1000;
                esp_timer_start_once(s_delayed_espnow_timer, delay_us);
                s_espnow_pending = true;

                ESP_LOGI(TAG, "=== STAGGERED STARTUP: 802.15.4 FIRST ===");
                ESP_LOGI(TAG, "ESP-NOW delayed by %lu ms (pure 802.15.4 sync window)",
                         (unsigned long)s_config.stagger_espnow_ms);

                /* Still count as success - ESP-NOW is pending */
                any_success = true;
            } else {
                ESP_LOGW(TAG, "Failed to create delay timer, starting ESP-NOW now");
                if (enable_transport_internal(UTLP_TRANSPORT_ESPNOW)) {
                    any_success = true;
                }
            }
        } else {
            /* No stagger - start immediately */
            if (enable_transport_internal(UTLP_TRANSPORT_ESPNOW)) {
                any_success = true;
            }
        }
    }

    /* BLE initialization would go here (future) */

    if (!any_success) {
        ESP_LOGE(TAG, "All transport initializations failed");
        return false;
    }

    /* Determine primary transport for TX mode decisions */
    if (s_status.enabled & UTLP_TRANSPORT_154) {
        s_status.primary = UTLP_TRANSPORT_154;  /* 802.15.4 preferred (better timing) */
    } else if (s_status.enabled & UTLP_TRANSPORT_ESPNOW) {
        s_status.primary = UTLP_TRANSPORT_ESPNOW;
    }

    /* Check for hardware-scheduled TX capability */
#if HAVE_802154
    s_status.has_scheduled_tx = (s_status.enabled & UTLP_TRANSPORT_154) &&
                                utlp_hal_154_has_scheduled_tx();
#else
    s_status.has_scheduled_tx = false;
#endif

    s_initialized = true;

    ESP_LOGI(TAG, "Transport layer initialized");
    ESP_LOGI(TAG, "  Enabled: 0x%02X (ESP-NOW=%s, 15.4=%s)",
             s_status.enabled,
             (s_status.enabled & UTLP_TRANSPORT_ESPNOW) ? "yes" :
             (s_espnow_pending ? "pending" : "no"),
             (s_status.enabled & UTLP_TRANSPORT_154) ? "yes" : "no");
    ESP_LOGI(TAG, "  Primary: %s",
             (s_status.primary == UTLP_TRANSPORT_154) ? "802.15.4" :
             (s_status.primary == UTLP_TRANSPORT_ESPNOW) ? "ESP-NOW" : "none");
    ESP_LOGI(TAG, "  TX mode: %s",
             (s_config.tx_mode == UTLP_TX_MODE_ALL) ? "ALL" :
             (s_config.tx_mode == UTLP_TX_MODE_PRIMARY) ? "PRIMARY" : "BEST");
    ESP_LOGI(TAG, "  Scheduled TX: %s", s_status.has_scheduled_tx ? "available" : "no");

    return true;
}

/*============================================================================
 * DELAYED STARTUP CALLBACK
 *==========================================================================*/

/**
 * @brief Timer callback for delayed ESP-NOW startup
 *
 * Called after stagger_espnow_ms to bring ESP-NOW online.
 * This allows pure 802.15.4 sync testing before WiFi joins.
 */
static void delayed_espnow_timer_callback(void *arg)
{
    (void)arg;

    ESP_LOGI(TAG, "=== STAGGER COMPLETE: Enabling ESP-NOW ===");
    ESP_LOGI(TAG, "WiFi arbor joining 802.15.4 swarm...");

    s_espnow_pending = false;

    if (enable_transport_internal(UTLP_TRANSPORT_ESPNOW)) {
        ESP_LOGI(TAG, "ESP-NOW transport now active");

        /* Update primary if 802.15.4 not available (shouldn't happen) */
        if (!(s_status.enabled & UTLP_TRANSPORT_154)) {
            s_status.primary = UTLP_TRANSPORT_ESPNOW;
        }

        utlp_transport_log_status();
    } else {
        ESP_LOGE(TAG, "ESP-NOW delayed startup failed!");
    }

    /* Clean up timer */
    if (s_delayed_espnow_timer) {
        esp_timer_delete(s_delayed_espnow_timer);
        s_delayed_espnow_timer = NULL;
    }
}

/*============================================================================
 * RUNTIME TRANSPORT ENABLE
 *==========================================================================*/

/**
 * @brief Enable a specific transport at runtime
 *
 * Safe to call multiple times (idempotent).
 *
 * @param transport Single transport bit to enable
 * @return true if transport enabled successfully
 */
bool utlp_transport_enable(utlp_transport_t transport)
{
    if (!s_initialized) {
        ESP_LOGW(TAG, "Transport layer not initialized");
        return false;
    }

    return enable_transport_internal(transport);
}

/**
 * @brief Internal transport enable with idempotency
 */
static bool enable_transport_internal(utlp_transport_t transport)
{
    switch (transport) {
        case UTLP_TRANSPORT_ESPNOW:
            if (s_espnow_initialized) {
                ESP_LOGD(TAG, "ESP-NOW already initialized");
                return true;  /* Idempotent success */
            }
            if (init_espnow_transport()) {
                s_espnow_initialized = true;
                s_status.enabled |= UTLP_TRANSPORT_ESPNOW;
                s_status.active |= UTLP_TRANSPORT_ESPNOW;
                utlp_arbor_register(UTLP_ARBOR_WIFI);
                ESP_LOGI(TAG, "ESP-NOW transport enabled");
                return true;
            }
            ESP_LOGE(TAG, "ESP-NOW transport init failed");
            return false;

        case UTLP_TRANSPORT_154:
            if (s_154_initialized) {
                ESP_LOGD(TAG, "802.15.4 already initialized");
                return true;  /* Idempotent success */
            }
            if (init_154_transport(s_config.channel_154)) {
                s_154_initialized = true;
                s_status.enabled |= UTLP_TRANSPORT_154;
                s_status.active |= UTLP_TRANSPORT_154;
                utlp_arbor_register(UTLP_ARBOR_154);
                ESP_LOGI(TAG, "802.15.4 transport enabled (channel %d)",
                         s_config.channel_154);
                return true;
            }
            ESP_LOGE(TAG, "802.15.4 transport init failed");
            return false;

        case UTLP_TRANSPORT_BLE:
            if (s_ble_initialized) {
                ESP_LOGD(TAG, "BLE already initialized");
                return true;
            }
            ESP_LOGW(TAG, "BLE transport not yet implemented");
            return false;

        default:
            ESP_LOGW(TAG, "Unknown transport: 0x%02X", transport);
            return false;
    }
}

/*============================================================================
 * TRANSPORT-SPECIFIC INITIALIZATION
 *==========================================================================*/

/**
 * @brief Initialize ESP-NOW transport
 *
 * This calls the existing utlp_hal_init() which sets up WiFi + ESP-NOW.
 * The existing HAL was already working for ESP-NOW only.
 */
static bool init_espnow_transport(void)
{
#if HAVE_ESPNOW
    ESP_LOGI(TAG, "Initializing ESP-NOW transport");

    /*
     * The existing utlp_hal_init() in utlp_hal_esp32.c handles:
     * - WiFi initialization (station mode)
     * - ESP-NOW initialization and registration
     * - RX callback setup
     *
     * We reuse this existing code rather than duplicating it.
     * Note: utlp_hal_init() returns void, assume success if no crash.
     */
    utlp_hal_init();
    return true;  /* No return value from HAL init, assume success */
#else
    ESP_LOGW(TAG, "ESP-NOW not available on this platform");
    return false;
#endif
}

/**
 * @brief Initialize 802.15.4 transport
 *
 * This calls the new utlp_hal_154_init() which sets up raw MAC frames.
 */
static bool init_154_transport(uint8_t channel)
{
#if HAVE_802154
    ESP_LOGI(TAG, "Initializing 802.15.4 transport on channel %d", channel);

    return utlp_hal_154_init(channel);
#else
    (void)channel;
    ESP_LOGW(TAG, "802.15.4 not available on this platform");
    return false;
#endif
}

/*============================================================================
 * STATUS QUERY
 *==========================================================================*/

void utlp_transport_get_status(utlp_transport_status_t *status)
{
    if (status) {
        /* Update active status from arbor states */
        s_status.active = 0;

        if ((s_status.enabled & UTLP_TRANSPORT_ESPNOW) &&
            utlp_arbor_get_state(UTLP_ARBOR_WIFI) == UTLP_ARBOR_STATE_ACTIVE) {
            s_status.active |= UTLP_TRANSPORT_ESPNOW;
        }

        if ((s_status.enabled & UTLP_TRANSPORT_154) &&
            utlp_arbor_get_state(UTLP_ARBOR_154) == UTLP_ARBOR_STATE_ACTIVE) {
            s_status.active |= UTLP_TRANSPORT_154;
        }

        *status = s_status;
    }
}

/*============================================================================
 * TRANSMIT FUNCTIONS
 *==========================================================================*/

bool utlp_transport_tx(const uint8_t *data, size_t len)
{
    if (!s_initialized || !data || len == 0) {
        return false;
    }

    bool any_success = false;
    uint8_t targets = 0;

    /* Determine which transports to use based on tx_mode */
    switch (s_config.tx_mode) {
        case UTLP_TX_MODE_ALL:
            targets = s_status.active;
            break;

        case UTLP_TX_MODE_PRIMARY:
            targets = s_status.primary;
            break;

        case UTLP_TX_MODE_BEST:
            /* Prefer 802.15.4 for better timing, fall back to ESP-NOW */
            if (s_status.active & UTLP_TRANSPORT_154) {
                targets = UTLP_TRANSPORT_154;
            } else if (s_status.active & UTLP_TRANSPORT_ESPNOW) {
                targets = UTLP_TRANSPORT_ESPNOW;
            }
            break;

        default:
            targets = s_status.primary;
    }

    /* Transmit on ESP-NOW */
    if (targets & UTLP_TRANSPORT_ESPNOW) {
        if (utlp_arbor_can_tx(UTLP_ARBOR_WIFI)) {
            if (utlp_hal_tx_packet(NULL, data, len)) {
                any_success = true;
            }
        }
    }

    /* Transmit on 802.15.4 */
#if HAVE_802154
    if (targets & UTLP_TRANSPORT_154) {
        if (utlp_arbor_can_tx(UTLP_ARBOR_154)) {
            if (utlp_hal_154_tx_frame(data, len)) {
                any_success = true;
            }
        }
    }
#endif

    return any_success;
}

bool utlp_transport_tx_scheduled(const utlp_scheduled_tx_t *packets, size_t count)
{
    if (!s_initialized || !packets || count == 0) {
        return false;
    }

    /*
     * Scheduled TX only makes sense on transports with hardware timing.
     * Currently, only 802.15.4 on ESP32-C6 has this capability.
     */
#if HAVE_802154
    if (!(s_status.active & UTLP_TRANSPORT_154)) {
        ESP_LOGW(TAG, "Scheduled TX requested but 802.15.4 not active");
        return false;
    }

    if (!utlp_arbor_can_tx(UTLP_ARBOR_154)) {
        ESP_LOGW(TAG, "802.15.4 arbor cannot TX (dormant or waking)");
        return false;
    }

    bool all_success = true;
    for (size_t i = 0; i < count; i++) {
        if (!utlp_hal_154_tx_scheduled(packets[i].tx_time_us,
                                        packets[i].payload,
                                        packets[i].len)) {
            all_success = false;
        }
    }

    return all_success;
#else
    /*
     * No hardware-scheduled TX available. Fall back to spin-wait.
     * This is the existing behavior for ESP-NOW on original ESP32.
     */
    ESP_LOGW(TAG, "Scheduled TX: Using spin-wait fallback (no 802.15.4)");

    bool all_success = true;
    for (size_t i = 0; i < count; i++) {
        /* Wait until scheduled time */
        while (esp_timer_get_time() < packets[i].tx_time_us) {
            /* Spin */
        }

        if (!utlp_transport_tx(packets[i].payload, packets[i].len)) {
            all_success = false;
        }
    }

    return all_success;
#endif
}

bool utlp_transport_has_scheduled_tx(void)
{
    return s_status.has_scheduled_tx;
}

/*============================================================================
 * RECEIVE FUNCTIONS
 *==========================================================================*/

bool utlp_transport_rx_poll(utlp_packet_t *out_packet)
{
    if (!s_initialized || !out_packet || !s_rx_queue) {
        return false;
    }

    /*
     * First, drain any packets from transport-specific queues into unified queue.
     * This aggregates RX from all active transports.
     */

    /* Poll ESP-NOW RX (Blood-Brain Barrier: tag with arbor_id for per-arbor trust) */
#if HAVE_ESPNOW
    if (s_status.active & UTLP_TRANSPORT_ESPNOW) {
        utlp_packet_t pkt;
        if (utlp_hal_rx_poll(&pkt)) {
            pkt.arbor_id = UTLP_ARBOR_WIFI;  /* Tag packet with transport source */
            route_rx_to_unified_queue(&pkt);
        }
    }
#endif

    /* Poll 802.15.4 RX (Blood-Brain Barrier: tag with arbor_id for per-arbor trust) */
#if HAVE_802154
    if (s_status.active & UTLP_TRANSPORT_154) {
        utlp_packet_t pkt;
        if (utlp_hal_154_rx_poll(&pkt)) {
            pkt.arbor_id = UTLP_ARBOR_154;  /* Tag packet with transport source */
            route_rx_to_unified_queue(&pkt);
        }
    }
#endif

    /* Now return from unified queue */
    return (xQueueReceive(s_rx_queue, out_packet, 0) == pdTRUE);
}

bool utlp_transport_rx_wait(utlp_packet_t *out_packet, uint32_t timeout_ms)
{
    if (!s_initialized || !out_packet) {
        return false;
    }

    /*
     * For blocking wait, we use a polling approach that checks all transports.
     * This is simpler than setting up interrupt-driven aggregation.
     *
     * TODO: Optimize with actual semaphore signaling from transport ISRs
     */

    uint32_t poll_interval_ms = 10;
    uint32_t elapsed_ms = 0;

    while (elapsed_ms < timeout_ms || timeout_ms == 0) {
        if (utlp_transport_rx_poll(out_packet)) {
            return true;
        }

        vTaskDelay(pdMS_TO_TICKS(poll_interval_ms));
        elapsed_ms += poll_interval_ms;

        if (timeout_ms == 0) {
            break;  /* No-wait mode */
        }
    }

    return false;
}

/**
 * @brief Route received packet to unified queue
 *
 * Called when a packet is received from any transport.
 * Adds transport metadata and queues for protocol layer.
 */
static void route_rx_to_unified_queue(const utlp_packet_t *pkt)
{
    if (!pkt || !s_rx_queue) {
        return;
    }

    /* Queue packet (drop if full) */
    if (xQueueSend(s_rx_queue, pkt, 0) != pdTRUE) {
        ESP_LOGW(TAG, "Unified RX queue full, dropping packet");
    }
}

/*============================================================================
 * ADDRESS FUNCTIONS
 *==========================================================================*/

void utlp_transport_get_addr(utlp_addr_t *addr)
{
    if (!addr) {
        return;
    }

    /*
     * Return address from primary transport.
     * ESP-NOW uses 6-byte MAC, 802.15.4 uses 8-byte EUI-64.
     */
    if (s_status.primary == UTLP_TRANSPORT_154) {
#if HAVE_802154
        uint8_t eui64[8];
        utlp_hal_154_get_eui64(eui64);
        memcpy(addr->addr, eui64, 8);
        addr->len = 8;
#endif
    } else {
        /* ESP-NOW (6-byte MAC) */
        utlp_hal_get_addr(addr);
    }
}

void utlp_transport_get_mac(uint8_t *mac)
{
    if (!mac) {
        return;
    }

    /* Legacy 6-byte MAC (from WiFi) */
    utlp_addr_t addr;
    utlp_hal_get_addr(&addr);
    memcpy(mac, addr.addr, 6);
}

/*============================================================================
 * DORMANCY FUNCTIONS (Arbor Wrappers)
 *==========================================================================*/

bool utlp_transport_yield(utlp_transport_t transport)
{
    if (!s_initialized) {
        return false;
    }

    utlp_arbor_id_t arbor_id;

    switch (transport) {
        case UTLP_TRANSPORT_ESPNOW:
            arbor_id = UTLP_ARBOR_WIFI;
            break;
        case UTLP_TRANSPORT_154:
            arbor_id = UTLP_ARBOR_154;
            break;
        case UTLP_TRANSPORT_BLE:
            arbor_id = UTLP_ARBOR_BLE;
            break;
        default:
            ESP_LOGW(TAG, "Invalid transport for yield: 0x%02X", transport);
            return false;
    }

    utlp_dormancy_params_t params = {
        .expected_duration_ms = 0,      /* Indefinite */
        .broadcast_beacon = true,
        .preserve_ledger = true
    };

    esp_err_t ret = utlp_arbor_yield(arbor_id, &params);
    if (ret == ESP_OK) {
        ESP_LOGI(TAG, "Transport 0x%02X yielded (dormant)", transport);
        return true;
    }

    return false;
}

bool utlp_transport_wake(utlp_transport_t transport)
{
    if (!s_initialized) {
        return false;
    }

    utlp_arbor_id_t arbor_id;

    switch (transport) {
        case UTLP_TRANSPORT_ESPNOW:
            arbor_id = UTLP_ARBOR_WIFI;
            break;
        case UTLP_TRANSPORT_154:
            arbor_id = UTLP_ARBOR_154;
            break;
        case UTLP_TRANSPORT_BLE:
            arbor_id = UTLP_ARBOR_BLE;
            break;
        default:
            ESP_LOGW(TAG, "Invalid transport for wake: 0x%02X", transport);
            return false;
    }

    esp_err_t ret = utlp_arbor_wake(arbor_id);
    if (ret == ESP_OK) {
        ESP_LOGI(TAG, "Transport 0x%02X waking (degraded re-entry)", transport);
        return true;
    }

    return false;
}

/*============================================================================
 * UTILITY FUNCTIONS
 *==========================================================================*/

/**
 * @brief Get human-readable transport name
 */
const char* utlp_transport_name(utlp_transport_t transport)
{
    switch (transport) {
        case UTLP_TRANSPORT_ESPNOW: return "ESP-NOW";
        case UTLP_TRANSPORT_154:    return "802.15.4";
        case UTLP_TRANSPORT_BLE:    return "BLE";
        case UTLP_TRANSPORT_ALL:    return "ALL";
        default:                    return "Unknown";
    }
}

/**
 * @brief Log current transport status
 */
void utlp_transport_log_status(void)
{
    if (!s_initialized) {
        ESP_LOGI(TAG, "Transport layer not initialized");
        return;
    }

    utlp_transport_status_t status;
    utlp_transport_get_status(&status);

    ESP_LOGI(TAG, "Transport Status:");
    ESP_LOGI(TAG, "  Available: 0x%02X", status.available);
    ESP_LOGI(TAG, "  Enabled:   0x%02X", status.enabled);
    ESP_LOGI(TAG, "  Active:    0x%02X", status.active);
    ESP_LOGI(TAG, "  Primary:   %s", utlp_transport_name(status.primary));
    ESP_LOGI(TAG, "  Scheduled: %s", status.has_scheduled_tx ? "yes" : "no");

    if (s_espnow_pending) {
        ESP_LOGI(TAG, "  ESP-NOW:   PENDING (staggered startup)");
    }
}

/**
 * @brief Check if ESP-NOW startup is pending
 */
bool utlp_transport_is_espnow_pending(void)
{
    return s_espnow_pending;
}
