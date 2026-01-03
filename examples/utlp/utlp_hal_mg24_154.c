/**
 * @file utlp_hal_mg24_154.c
 * @brief UTLP HAL Stub for Silicon Labs MG24 IEEE 802.15.4 via RAIL
 *
 * @section overview Overview
 *
 * This is a **STUB IMPLEMENTATION** for the Seeed XIAO MG24 (EFR32MG24).
 * The MG24 uses Silicon Labs' RAIL (Radio Abstraction Interface Layer) for
 * hardware-scheduled TX with sub-microsecond precision.
 *
 * @section hardware Target Hardware
 *
 * - **MCU:** EFR32MG24B220F1536IM48
 * - **Radio:** IEEE 802.15.4 @ 2.4 GHz
 * - **API:** RAIL (Radio Abstraction Interface Layer)
 * - **SDK:** Gecko SDK or Zephyr RTOS
 *
 * @section scheduling Hardware-Scheduled TX
 *
 * The MG24's RAIL provides `RAIL_StartScheduledTx()` for hardware-precise timing:
 *
 * ```c
 * RAIL_ScheduleTxConfig_t config = {
 *     .when = target_time_us,
 *     .mode = RAIL_TIME_ABSOLUTE,
 * };
 * RAIL_StartScheduledTx(rail_handle, channel, RAIL_TX_OPTIONS_DEFAULT, &config, NULL);
 * ```
 *
 * @section timing Timing Precision
 *
 * | Capability | MG24 RAIL |
 * |------------|-----------|
 * | TX Jitter | ~0.1µs (sub-microsecond) |
 * | RX Timestamp | SFD-relative (hardware) |
 * | Timer Resolution | µs |
 *
 * @section prior_art Prior Art Claims
 *
 * - **Claim 238+**: Cross-manufacturer 802.15.4 timing mesh
 * - **Claim 240+**: RAIL_StartScheduledTx() hardware scheduling
 *
 * @note This is a STUB. Implementation requires MG24 hardware and Gecko/Zephyr SDK.
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
#if defined(EFR32MG24) || defined(CONFIG_SOC_SERIES_EFR32MG24)
#define UTLP_HAL_MG24_AVAILABLE 1
#include "rail.h"
#include "sl_rail_util_init.h"
#else
#define UTLP_HAL_MG24_AVAILABLE 0
#endif

#if UTLP_HAL_MG24_AVAILABLE

/*============================================================================
 * RAIL HANDLES (to be set during initialization)
 *==========================================================================*/

static RAIL_Handle_t s_rail_handle = NULL;
static uint8_t s_current_channel = UTLP_154_CHANNEL_DEFAULT;
static uint8_t s_eui64[8];
static bool s_initialized = false;

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

    /* TODO: Initialize RAIL
     *
     * 1. Call RAIL_Init() with appropriate config
     * 2. Configure for 802.15.4 operation
     * 3. Set PAN ID to UTLP_154_PAN_ID (0xCAFE)
     * 4. Read EUI-64 from DEVINFO
     * 5. Set channel and TX power
     */

    s_current_channel = channel;
    s_initialized = true;

    return true;
}

void utlp_hal_154_get_eui64(uint8_t *eui64)
{
    if (eui64) {
        /* TODO: Read from DEVINFO->EUI64 */
        memcpy(eui64, s_eui64, 8);
    }
}

bool utlp_hal_154_tx_frame(const uint8_t *data, size_t len)
{
    if (!s_initialized || !data || len > UTLP_154_MAX_PAYLOAD) {
        return false;
    }

    /* TODO: Build frame and transmit via RAIL_StartTx() */

    return false;  /* STUB */
}

bool utlp_hal_154_tx_scheduled(uint64_t tx_time_us, const uint8_t *data, size_t len)
{
    if (!s_initialized || !data || len > UTLP_154_MAX_PAYLOAD) {
        return false;
    }

    /* TODO: Implement using RAIL_StartScheduledTx()
     *
     * RAIL_ScheduleTxConfig_t config = {
     *     .when = (RAIL_Time_t)(tx_time_us),
     *     .mode = RAIL_TIME_ABSOLUTE,
     * };
     *
     * RAIL_Status_t status = RAIL_StartScheduledTx(
     *     s_rail_handle,
     *     s_current_channel,
     *     RAIL_TX_OPTIONS_DEFAULT,
     *     &config,
     *     NULL
     * );
     *
     * return (status == RAIL_STATUS_NO_ERROR);
     */

    return false;  /* STUB */
}

bool utlp_hal_154_has_scheduled_tx(void)
{
    /* MG24 RAIL has TRUE hardware-scheduled TX */
    return true;
}

bool utlp_hal_154_rx_poll(utlp_packet_t *out_packet)
{
    if (!s_initialized || !out_packet) {
        return false;
    }

    /* TODO: Check RAIL RX FIFO for packets */

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
    /* TODO: Return RAIL_GetRxTimeSyncWordEnd() value */
    return 0;  /* STUB */
}

bool utlp_hal_154_set_tx_power(int8_t power_dbm)
{
    if (!s_initialized) {
        return false;
    }

    /* TODO: RAIL_SetTxPower() */

    return false;  /* STUB */
}

int8_t utlp_hal_154_get_tx_power(void)
{
    /* TODO: RAIL_GetTxPower() */
    return 10;  /* Default */
}

bool utlp_hal_154_set_channel(uint8_t channel)
{
    if (!s_initialized) {
        return false;
    }

    if (channel < UTLP_154_CHANNEL_MIN || channel > UTLP_154_CHANNEL_MAX) {
        return false;
    }

    s_current_channel = channel;
    return true;
}

uint8_t utlp_hal_154_get_channel(void)
{
    return s_current_channel;
}

void utlp_hal_154_enable(bool enable)
{
    /* TODO: RAIL_StartRx() / RAIL_Idle() */
}

bool utlp_hal_154_is_enabled(void)
{
    return s_initialized;
}

void utlp_hal_154_get_caps(utlp_154_caps_t *caps)
{
    if (!caps) {
        return;
    }

    memset(caps, 0, sizeof(*caps));

    /* MG24 has hardware SFD timestamp via RAIL */
    caps->has_hardware_sfd_timestamp = true;

    /* MG24 has TRUE hardware-scheduled TX via RAIL */
    caps->has_hardware_scheduled_tx = true;

    /* No hardened ISR needed - hardware does it */
    caps->has_hardened_isr = false;

    /* TX power range (MG24) */
    caps->max_tx_power_dbm = 20;
    caps->min_tx_power_dbm = -30;

    /* All channels 11-26 supported */
    caps->supported_channels_mask[0] = 0x00;
    caps->supported_channels_mask[1] = 0xF8;
    caps->supported_channels_mask[2] = 0xFF;
    caps->supported_channels_mask[3] = 0x07;
}

#else /* !UTLP_HAL_MG24_AVAILABLE */

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

#endif /* UTLP_HAL_MG24_AVAILABLE */
