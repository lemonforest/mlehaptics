/**
 * @file utlp_transport.c
 * @brief Multi-Transport Management Layer - Phase 0 Stub
 *
 * PHASE 0 STUB: All functions return success/defaults.
 * Full implementation will be added in Phase 2 (First Contact).
 *
 * @version 0.0.1 (Phase 0 Stub)
 * @date 2026-01-08
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "utlp_transport.h"
#include "utlp_hal.h"

static const char *TAG = "UTLP_TRANSPORT";

/*============================================================================
 * STUB STATE
 *==========================================================================*/

static struct {
    uint8_t available;
    uint8_t enabled;
    bool    initialized;
} s_transport_state = {0};

/*============================================================================
 * PUBLIC API STUBS
 *==========================================================================*/

uint8_t utlp_transport_probe(void)
{
    /* Phase 0: Report 802.15.4 available (our target transport) */
    return UTLP_TRANSPORT_154;
}

bool utlp_transport_init(const utlp_transport_config_t *config)
{
    (void)config;

    utlp_hal_log_info(TAG, "Phase 0 stub: transport_init()");

    s_transport_state.available = UTLP_TRANSPORT_154;
    s_transport_state.enabled = UTLP_TRANSPORT_154;
    s_transport_state.initialized = true;

    return true;
}

void utlp_transport_get_status(utlp_transport_status_t *status)
{
    if (status == NULL) {
        return;
    }

    status->available = s_transport_state.available;
    status->enabled = s_transport_state.enabled;
    status->active = s_transport_state.enabled;
    status->has_scheduled_tx = false;
    status->primary = UTLP_TRANSPORT_154;
}

bool utlp_transport_enable(utlp_transport_t transport)
{
    (void)transport;
    return true;
}

bool utlp_transport_is_espnow_pending(void)
{
    return false;
}

bool utlp_transport_tx(const uint8_t *data, size_t len)
{
    /* Phase 0: Broadcast to all (NULL peer_mac = broadcast) */
    uint8_t broadcast[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    return utlp_hal_tx_packet(broadcast, data, len);
}

bool utlp_transport_tx_scheduled(const utlp_scheduled_tx_t *packets, size_t count)
{
    (void)packets;
    (void)count;
    return true;
}

bool utlp_transport_has_scheduled_tx(void)
{
    return false;
}

bool utlp_transport_rx_poll(utlp_packet_t *out_packet)
{
    return utlp_hal_rx_poll(out_packet);
}

bool utlp_transport_rx_wait(utlp_packet_t *out_packet, uint32_t timeout_ms)
{
    return utlp_hal_rx_wait(out_packet, timeout_ms);
}

void utlp_transport_get_addr(utlp_addr_t *addr)
{
    if (addr == NULL) {
        return;
    }

    utlp_hal_get_addr(addr);
}

void utlp_transport_get_mac(uint8_t *mac)
{
    if (mac == NULL) {
        return;
    }

    utlp_hal_get_mac(mac);
}

bool utlp_transport_yield(utlp_transport_t transport)
{
    (void)transport;
    return true;
}

bool utlp_transport_wake(utlp_transport_t transport)
{
    (void)transport;
    return true;
}

const char* utlp_transport_name(utlp_transport_t transport)
{
    switch (transport) {
        case UTLP_TRANSPORT_ESPNOW: return "ESP-NOW";
        case UTLP_TRANSPORT_154:    return "802.15.4";
        case UTLP_TRANSPORT_BLE:    return "BLE";
        default:                    return "Unknown";
    }
}

void utlp_transport_log_status(void)
{
    utlp_hal_log_info(TAG, "Phase 0 stub: available=0x%02X enabled=0x%02X",
                      s_transport_state.available,
                      s_transport_state.enabled);
}
