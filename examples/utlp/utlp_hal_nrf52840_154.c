/**
 * @file utlp_hal_nrf52840_154.c
 * @brief UTLP HAL Stub for Nordic nRF52840 IEEE 802.15.4
 *
 * @section overview Overview
 *
 * This is a **STUB IMPLEMENTATION** for the Nordic nRF52840.
 * The nRF52840 uses Nordic's 802.15.4 radio driver which provides
 * hardware-scheduled TX with sub-microsecond precision.
 *
 * @section hardware Target Hardware
 *
 * - **MCU:** nRF52840 (ARM Cortex-M4F @ 64 MHz)
 * - **Radio:** IEEE 802.15.4 @ 2.4 GHz + BLE multi-protocol
 * - **API:** nrf_802154 driver
 * - **SDK:** nRF Connect SDK or Zephyr RTOS
 *
 * @section scheduling Hardware-Scheduled TX
 *
 * The nRF52840's 802.15.4 driver provides `nrf_802154_transmit_raw_at()`:
 *
 * ```c
 * bool nrf_802154_transmit_raw_at(
 *     uint8_t *p_data,
 *     uint32_t tx_time,
 *     const nrf_802154_transmit_at_metadata_t *p_metadata
 * );
 * ```
 *
 * @section timing Timing Precision
 *
 * | Capability | nRF52840 |
 * |------------|----------|
 * | TX Jitter | ~0.1µs (sub-microsecond) |
 * | RX Timestamp | Timer capture at ADDRESS event |
 * | Timer Resolution | µs (TIMER peripheral) |
 *
 * @section prior_art Prior Art Claims
 *
 * - **Claim 238+**: Cross-manufacturer 802.15.4 timing mesh
 * - **Claim 241+**: nrf_802154_transmit_raw_at() hardware scheduling
 *
 * @note This is a STUB. Implementation requires nRF52840 hardware and nRF Connect SDK.
 *
 * @version 1.0.0
 * @date 2026-01-02
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "utlp_hal_802154.h"
#include "utlp_hal.h"

#include <string.h>

/* Platform detection */
#if defined(NRF52840_XXAA) || defined(CONFIG_SOC_NRF52840)
#define UTLP_HAL_NRF52840_AVAILABLE 1
#include "nrf_802154.h"
#include "nrf_802154_config.h"
#else
#define UTLP_HAL_NRF52840_AVAILABLE 0
#endif

#if UTLP_HAL_NRF52840_AVAILABLE

/*============================================================================
 * STATE VARIABLES
 *==========================================================================*/

static uint8_t s_current_channel = UTLP_154_CHANNEL_DEFAULT;
static uint8_t s_eui64[8];
static bool s_initialized = false;
static bool s_radio_enabled = false;

/*============================================================================
 * PUBLIC API IMPLEMENTATION
 *==========================================================================*/

bool utlp_hal_154_init(uint8_t channel)
{
    if (s_initialized) {
        return true;
    }

    if (channel < UTLP_154_CHANNEL_MIN || channel > UTLP_154_CHANNEL_MAX) {
        return false;
    }

    /* TODO: Initialize nRF 802.15.4 driver
     *
     * 1. Call nrf_802154_init()
     * 2. Set PAN ID via nrf_802154_pan_id_set()
     * 3. Read EUI-64 from FICR
     * 4. Set channel and TX power
     * 5. Enable RX via nrf_802154_receive()
     */

    s_current_channel = channel;
    s_initialized = true;
    s_radio_enabled = true;

    return true;
}

void utlp_hal_154_get_eui64(uint8_t *eui64)
{
    if (eui64) {
        /* TODO: Read from NRF_FICR->DEVICEADDR or DEVICEID */
        memcpy(eui64, s_eui64, 8);
    }
}

bool utlp_hal_154_tx_frame(const uint8_t *data, size_t len)
{
    if (!s_initialized || !data || len > UTLP_154_MAX_PAYLOAD) {
        return false;
    }

    /* TODO: Build frame and transmit via nrf_802154_transmit_raw() */

    return false;  /* STUB */
}

bool utlp_hal_154_tx_scheduled(uint64_t tx_time_us, const uint8_t *data, size_t len)
{
    if (!s_initialized || !data || len > UTLP_154_MAX_PAYLOAD) {
        return false;
    }

    /* TODO: Implement using nrf_802154_transmit_raw_at()
     *
     * nrf_802154_transmit_at_metadata_t metadata = {
     *     .frame_props = { ... },
     *     .cca = false,  // No CCA for scheduled TX
     *     .channel = s_current_channel,
     * };
     *
     * bool result = nrf_802154_transmit_raw_at(
     *     frame_buffer,
     *     (uint32_t)(tx_time_us & 0xFFFFFFFF),
     *     &metadata
     * );
     *
     * return result;
     */

    return false;  /* STUB */
}

bool utlp_hal_154_has_scheduled_tx(void)
{
    /* nRF52840 has TRUE hardware-scheduled TX */
    return true;
}

bool utlp_hal_154_rx_poll(utlp_packet_t *out_packet)
{
    if (!s_initialized || !out_packet) {
        return false;
    }

    /* TODO: Check for received frames */

    return false;  /* STUB */
}

bool utlp_hal_154_rx_wait(utlp_packet_t *out_packet, uint32_t timeout_ms)
{
    if (!s_initialized || !out_packet) {
        return false;
    }

    /* TODO: Wait for RX event with timeout */

    return false;  /* STUB */
}

uint64_t utlp_hal_154_get_last_sfd_time(void)
{
    /* TODO: Return timestamp from NRF_RADIO->EVENTS_ADDRESS + Timer capture
     *
     * The nRF52840 captures SFD time using PPI to connect:
     * RADIO->EVENTS_ADDRESS -> TIMER->TASKS_CAPTURE
     */
    return 0;  /* STUB */
}

bool utlp_hal_154_set_tx_power(int8_t power_dbm)
{
    if (!s_initialized) {
        return false;
    }

    /* TODO: nrf_802154_tx_power_set() */

    return false;  /* STUB */
}

int8_t utlp_hal_154_get_tx_power(void)
{
    /* TODO: nrf_802154_tx_power_get() */
    return 8;  /* Default */
}

bool utlp_hal_154_set_channel(uint8_t channel)
{
    if (!s_initialized) {
        return false;
    }

    if (channel < UTLP_154_CHANNEL_MIN || channel > UTLP_154_CHANNEL_MAX) {
        return false;
    }

    /* TODO: nrf_802154_channel_set() */
    s_current_channel = channel;
    return true;
}

uint8_t utlp_hal_154_get_channel(void)
{
    return s_current_channel;
}

void utlp_hal_154_enable(bool enable)
{
    if (!s_initialized) {
        return;
    }

    /* TODO: nrf_802154_receive() / nrf_802154_sleep() */
    s_radio_enabled = enable;
}

bool utlp_hal_154_is_enabled(void)
{
    return s_radio_enabled;
}

void utlp_hal_154_get_caps(utlp_154_caps_t *caps)
{
    if (!caps) {
        return;
    }

    memset(caps, 0, sizeof(*caps));

    /* nRF52840 has hardware SFD timestamp via TIMER capture */
    caps->has_hardware_sfd_timestamp = true;

    /* nRF52840 has TRUE hardware-scheduled TX */
    caps->has_hardware_scheduled_tx = true;

    /* No hardened ISR needed - hardware does it */
    caps->has_hardened_isr = false;

    /* TX power range (nRF52840) */
    caps->max_tx_power_dbm = 8;
    caps->min_tx_power_dbm = -40;

    /* All channels 11-26 supported */
    caps->supported_channels_mask[0] = 0x00;
    caps->supported_channels_mask[1] = 0xF8;
    caps->supported_channels_mask[2] = 0xFF;
    caps->supported_channels_mask[3] = 0x07;
}

#else /* !UTLP_HAL_NRF52840_AVAILABLE */

/*============================================================================
 * STUB IMPLEMENTATION (Platform Not Available)
 *==========================================================================*/

bool utlp_hal_154_init(uint8_t channel) { (void)channel; return false; }
void utlp_hal_154_get_eui64(uint8_t *eui64) { (void)eui64; }
bool utlp_hal_154_tx_frame(const uint8_t *data, size_t len) { (void)data; (void)len; return false; }
bool utlp_hal_154_tx_scheduled(uint64_t tx_time_us, const uint8_t *data, size_t len) { (void)tx_time_us; (void)data; (void)len; return false; }
bool utlp_hal_154_has_scheduled_tx(void) { return false; }
bool utlp_hal_154_rx_poll(utlp_packet_t *out_packet) { (void)out_packet; return false; }
bool utlp_hal_154_rx_wait(utlp_packet_t *out_packet, uint32_t timeout_ms) { (void)out_packet; (void)timeout_ms; return false; }
uint64_t utlp_hal_154_get_last_sfd_time(void) { return 0; }
bool utlp_hal_154_set_tx_power(int8_t power_dbm) { (void)power_dbm; return false; }
int8_t utlp_hal_154_get_tx_power(void) { return 0; }
bool utlp_hal_154_set_channel(uint8_t channel) { (void)channel; return false; }
uint8_t utlp_hal_154_get_channel(void) { return 0; }
void utlp_hal_154_enable(bool enable) { (void)enable; }
bool utlp_hal_154_is_enabled(void) { return false; }
void utlp_hal_154_get_caps(utlp_154_caps_t *caps) { if (caps) memset(caps, 0, sizeof(*caps)); }

#endif /* UTLP_HAL_NRF52840_AVAILABLE */
