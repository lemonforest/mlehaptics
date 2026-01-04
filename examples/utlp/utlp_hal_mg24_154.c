/**
 * @file utlp_hal_mg24_154.c
 * @brief UTLP HAL for Silicon Labs MG24 IEEE 802.15.4 via RAIL
 *
 * @section overview Overview
 *
 * Production implementation for Seeed XIAO MG24 (EFR32MG24).
 * Uses Silicon Labs' RAIL (Radio Abstraction Interface Layer) for
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
 * - **Claim 239+**: SFD-relative timestamp capture
 * - **Claim 240+**: RAIL_StartScheduledTx() hardware scheduling
 *
 * @version 2.0.0
 * @date 2026-01-03
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

/* Silicon Labs RAIL includes */
#include "rail.h"
#include "rail_ieee802154.h"
#include "rail_types.h"
#include "em_device.h"
#include "em_system.h"

/* Zephyr RTOS primitives */
#include <zephyr/kernel.h>
#include <zephyr/sys/ring_buffer.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(utlp_mg24_154, LOG_LEVEL_INF);

#else
#define UTLP_HAL_MG24_AVAILABLE 0
#endif

#if UTLP_HAL_MG24_AVAILABLE

/*============================================================================
 * CONFIGURATION CONSTANTS
 *==========================================================================*/

/** @brief TX buffer size (MAC frame) */
#define TX_BUFFER_SIZE          128

/** @brief RX FIFO buffer size */
#define RX_FIFO_SIZE            256

/** @brief RX packet queue depth */
#define RX_QUEUE_DEPTH          8

/** @brief TX power in deci-dBm (10 = 1 dBm, 200 = 20 dBm) */
#define DEFAULT_TX_POWER_DECIDBM  100  /* 10 dBm */

/*============================================================================
 * ATOMICITY SCAFFOLDING (Purple Team Pitfall 2: Torn Read Hazard)
 *
 * MG24 is 32-bit ARM Cortex-M33. 64-bit reads/writes require spinlock
 * protection to prevent reading mixed old/new halves.
 *
 * Zephyr RTOS uses k_spinlock instead of FreeRTOS portMUX_TYPE.
 *==========================================================================*/

/** @brief Spinlock for 64-bit SFD timestamp protection */
static struct k_spinlock s_sfd_spinlock;

/*============================================================================
 * RAIL CONFIGURATION
 *==========================================================================*/

/** @brief RAIL config for 802.15.4 2.4 GHz */
static const RAIL_IEEE802154_Config_t s_ieee802154_config = {
    .addresses = NULL,
    .ackConfig = {
        .enable = false,  /* UTLP doesn't use ACKs */
        .ackTimeout = 0,
        .rxTransitions = {
            .success = RAIL_RF_STATE_RX,
            .error = RAIL_RF_STATE_RX,
        },
        .txTransitions = {
            .success = RAIL_RF_STATE_RX,
            .error = RAIL_RF_STATE_RX,
        },
    },
    .timings = {
        .idleToRx = 100,
        .idleToTx = 100,
        .rxToTx = 192,    /* 12 symbol periods = 192 µs */
        .txToRx = 192,
        .rxSearchTimeout = 0,
        .txToRxSearchTimeout = 0,
    },
    .framesMask = RAIL_IEEE802154_ACCEPT_STANDARD_FRAMES |
                  RAIL_IEEE802154_ACCEPT_BEACON_FRAMES |
                  RAIL_IEEE802154_ACCEPT_DATA_FRAMES,
    .promiscuousMode = true,  /* Accept all frames on our PAN */
    .isPanCoordinator = false,
    .defaultFramePendingInOutgoingAcks = false,
};

/*============================================================================
 * RAIL STATE
 *==========================================================================*/

/** @brief RAIL handle */
static RAIL_Handle_t s_rail_handle = NULL;

/** @brief Current channel */
static uint8_t s_current_channel = UTLP_154_CHANNEL_DEFAULT;

/** @brief Current TX power in deci-dBm */
static int16_t s_tx_power_decidbm = DEFAULT_TX_POWER_DECIDBM;

/** @brief EUI-64 address (cached from DEVINFO) */
static uint8_t s_eui64[8];

/** @brief Initialization flag */
static bool s_initialized = false;

/** @brief Radio enabled flag */
static bool s_radio_enabled = false;

/** @brief Last SFD timestamp (Purple Team: requires spinlock for atomic read) */
static volatile uint64_t s_last_sfd_time = 0;

/** @brief Sequence number for MAC frames */
static uint8_t s_seq_num = 0;

/** @brief TX buffer */
static uint8_t s_tx_buffer[TX_BUFFER_SIZE];

/** @brief RX FIFO buffer for RAIL */
static uint8_t s_rx_fifo[RX_FIFO_SIZE];

/*============================================================================
 * RX PACKET QUEUE (Zephyr message queue)
 *==========================================================================*/

K_MSGQ_DEFINE(s_rx_queue, sizeof(utlp_packet_t), RX_QUEUE_DEPTH, 4);

/** @brief Semaphore for blocking RX wait */
K_SEM_DEFINE(s_rx_sem, 0, 1);

/*============================================================================
 * RAIL EVENT CALLBACK
 *==========================================================================*/

/**
 * @brief RAIL event callback handler
 *
 * Called from ISR context by RAIL for TX/RX events.
 *
 * @param rail_handle RAIL handle
 * @param events Event bitmask
 */
static void rail_event_callback(RAIL_Handle_t rail_handle, RAIL_Events_t events)
{
    (void)rail_handle;

    /* RX packet available */
    if (events & RAIL_EVENT_RX_PACKET_RECEIVED) {
        RAIL_RxPacketInfo_t packet_info;
        RAIL_RxPacketDetails_t packet_details;
        RAIL_RxPacketHandle_t packet_handle;

        /* Get packet from RAIL */
        packet_handle = RAIL_GetRxPacketInfo(s_rail_handle,
                                              RAIL_RX_PACKET_HANDLE_OLDEST,
                                              &packet_info);
        if (packet_handle == RAIL_RX_PACKET_HANDLE_INVALID) {
            return;
        }

        /* Get packet details including timestamp */
        RAIL_Status_t status = RAIL_GetRxPacketDetailsAlt(s_rail_handle,
                                                           packet_handle,
                                                           &packet_details);
        if (status != RAIL_STATUS_NO_ERROR) {
            RAIL_ReleaseRxPacket(s_rail_handle, packet_handle);
            return;
        }

        /* Capture SFD timestamp with spinlock protection (Purple Team Pitfall 2) */
        k_spinlock_key_t key = k_spin_lock(&s_sfd_spinlock);
        s_last_sfd_time = packet_details.timeReceived.packetTime;
        k_spin_unlock(&s_sfd_spinlock, key);

        /* Build UTLP packet */
        utlp_packet_t pkt = {0};
        pkt.rx_timestamp_us = s_last_sfd_time;
        pkt.rssi = packet_details.rssi;

        /* Copy packet data */
        if (packet_info.packetBytes <= sizeof(pkt.data)) {
            RAIL_CopyRxPacket(pkt.data, &packet_info);
            pkt.len = packet_info.packetBytes;

            /* Parse MAC header to extract source address
             * Frame format: FCF(2) + Seq(1) + PAN(2) + Dest(2) + Src(8) + Payload
             */
            if (pkt.len >= 15) {  /* Minimum frame with extended src */
                /* Source address starts at offset 7 (after FCF, Seq, PAN, Dest) */
                memcpy(pkt.src_addr, &pkt.data[7], 8);
            }

            /* Queue packet for application */
            if (k_msgq_put(&s_rx_queue, &pkt, K_NO_WAIT) == 0) {
                k_sem_give(&s_rx_sem);  /* Signal waiting thread */
            }
        }

        RAIL_ReleaseRxPacket(s_rail_handle, packet_handle);
    }

    /* TX completed */
    if (events & RAIL_EVENTS_TX_COMPLETION) {
        if (events & RAIL_EVENT_TX_PACKET_SENT) {
            LOG_DBG("TX complete");
        } else {
            LOG_WRN("TX failed: events=0x%08llx", events);
        }
    }

    /* Calibration needed */
    if (events & RAIL_EVENT_CAL_NEEDED) {
        RAIL_Calibrate(s_rail_handle, NULL, RAIL_CAL_ALL_PENDING);
    }
}

/*============================================================================
 * FRAME BUILDING
 *==========================================================================*/

/**
 * @brief Build 802.15.4 MAC Data frame
 *
 * Frame format per utlp_hal_802154.h:
 * - FCF: 0x8841 (Data, no ACK, PAN compression, short dest, extended src)
 * - Seq: auto-increment
 * - Dest PAN: 0xCAFE (UTLP reserved)
 * - Dest Addr: 0xFFFF (broadcast)
 * - Src Addr: EUI-64
 * - Payload: UTLP beacon data
 *
 * @param payload UTLP payload data
 * @param payload_len Payload length
 * @param frame Output frame buffer
 * @return Total frame length (excluding FCS - hardware adds it)
 */
static size_t build_mac_frame(const uint8_t *payload, size_t payload_len,
                               uint8_t *frame)
{
    size_t idx = 0;

    /* Frame Control Field: 0x8841
     * - Bits 0-2: 001 = Data frame
     * - Bit 3: 0 = Security disabled
     * - Bit 4: 0 = No frame pending
     * - Bit 5: 0 = No ACK request
     * - Bit 6: 1 = PAN ID compression
     * - Bits 10-11: 10 = Short dest addr
     * - Bits 14-15: 11 = Extended src addr
     */
    frame[idx++] = 0x41;  /* FCF low byte */
    frame[idx++] = 0x88;  /* FCF high byte */

    /* Sequence number */
    frame[idx++] = s_seq_num++;

    /* Destination PAN ID: 0xCAFE (UTLP reserved) */
    frame[idx++] = (UTLP_154_PAN_ID >> 0) & 0xFF;
    frame[idx++] = (UTLP_154_PAN_ID >> 8) & 0xFF;

    /* Destination address: 0xFFFF (broadcast) */
    frame[idx++] = 0xFF;
    frame[idx++] = 0xFF;

    /* Source address: EUI-64 */
    memcpy(&frame[idx], s_eui64, 8);
    idx += 8;

    /* Payload */
    if (payload && payload_len > 0) {
        memcpy(&frame[idx], payload, payload_len);
        idx += payload_len;
    }

    return idx;  /* FCS added by hardware */
}

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

    /* Read EUI-64 from DEVINFO (factory-programmed) */
    uint32_t eui64_lo = DEVINFO->EUI64L;
    uint32_t eui64_hi = DEVINFO->EUI64H;
    s_eui64[0] = (eui64_lo >> 0) & 0xFF;
    s_eui64[1] = (eui64_lo >> 8) & 0xFF;
    s_eui64[2] = (eui64_lo >> 16) & 0xFF;
    s_eui64[3] = (eui64_lo >> 24) & 0xFF;
    s_eui64[4] = (eui64_hi >> 0) & 0xFF;
    s_eui64[5] = (eui64_hi >> 8) & 0xFF;
    s_eui64[6] = (eui64_hi >> 16) & 0xFF;
    s_eui64[7] = (eui64_hi >> 24) & 0xFF;

    LOG_INF("EUI-64: %02X:%02X:%02X:%02X:%02X:%02X:%02X:%02X",
            s_eui64[0], s_eui64[1], s_eui64[2], s_eui64[3],
            s_eui64[4], s_eui64[5], s_eui64[6], s_eui64[7]);

    /* Get RAIL handle from Zephyr (configured in device tree) */
    s_rail_handle = sl_rail_util_get_handle(SL_RAIL_UTIL_HANDLE_INST0);
    if (s_rail_handle == NULL) {
        LOG_ERR("Failed to get RAIL handle");
        return false;
    }

    /* Configure RAIL for 802.15.4 */
    RAIL_Status_t status = RAIL_IEEE802154_Config2p4GHzRadio(s_rail_handle);
    if (status != RAIL_STATUS_NO_ERROR) {
        LOG_ERR("RAIL 802.15.4 config failed: %d", status);
        return false;
    }

    /* Initialize 802.15.4 protocol */
    status = RAIL_IEEE802154_Init(s_rail_handle, &s_ieee802154_config);
    if (status != RAIL_STATUS_NO_ERROR) {
        LOG_ERR("RAIL IEEE802154 init failed: %d", status);
        return false;
    }

    /* Set PAN ID */
    status = RAIL_IEEE802154_SetPanId(s_rail_handle, UTLP_154_PAN_ID, 0);
    if (status != RAIL_STATUS_NO_ERROR) {
        LOG_ERR("Failed to set PAN ID: %d", status);
        return false;
    }

    /* Set extended address */
    status = RAIL_IEEE802154_SetLongAddress(s_rail_handle, s_eui64, 0);
    if (status != RAIL_STATUS_NO_ERROR) {
        LOG_ERR("Failed to set long address: %d", status);
        return false;
    }

    /* Set RX FIFO */
    RAIL_SetRxFifo(s_rail_handle, s_rx_fifo, &(uint16_t){RX_FIFO_SIZE});

    /* Configure events */
    RAIL_ConfigEvents(s_rail_handle,
                      RAIL_EVENTS_ALL,
                      RAIL_EVENT_RX_PACKET_RECEIVED |
                      RAIL_EVENTS_TX_COMPLETION |
                      RAIL_EVENT_CAL_NEEDED);

    /* Set channel */
    s_current_channel = channel;

    /* Set TX power */
    RAIL_SetTxPowerDbm(s_rail_handle, s_tx_power_decidbm);

    /* Start receiving */
    status = RAIL_StartRx(s_rail_handle, channel, NULL);
    if (status != RAIL_STATUS_NO_ERROR) {
        LOG_ERR("Failed to start RX: %d", status);
        return false;
    }

    s_radio_enabled = true;
    s_initialized = true;

    LOG_INF("MG24 802.15.4 HAL initialized on channel %d", channel);
    return true;
}

void utlp_hal_154_get_eui64(uint8_t *eui64)
{
    if (eui64) {
        memcpy(eui64, s_eui64, 8);
    }
}

bool utlp_hal_154_tx_frame(const uint8_t *data, size_t len)
{
    if (!s_initialized || !data || len > UTLP_154_MAX_PAYLOAD) {
        return false;
    }

    /* Build MAC frame */
    size_t frame_len = build_mac_frame(data, len, s_tx_buffer);

    /* Load TX buffer */
    RAIL_WriteTxFifo(s_rail_handle, s_tx_buffer, frame_len, true);

    /* Transmit immediately */
    RAIL_Status_t status = RAIL_StartTx(s_rail_handle,
                                         s_current_channel,
                                         RAIL_TX_OPTIONS_DEFAULT,
                                         NULL);

    return (status == RAIL_STATUS_NO_ERROR);
}

bool utlp_hal_154_tx_scheduled(uint64_t tx_time_us, const uint8_t *data, size_t len)
{
    if (!s_initialized || !data || len > UTLP_154_MAX_PAYLOAD) {
        return false;
    }

    /* Build MAC frame */
    size_t frame_len = build_mac_frame(data, len, s_tx_buffer);

    /* Load TX buffer */
    RAIL_WriteTxFifo(s_rail_handle, s_tx_buffer, frame_len, true);

    /* Configure scheduled TX
     * RAIL uses absolute time in microseconds from RAIL_GetTime()
     */
    RAIL_ScheduleTxConfig_t tx_config = {
        .when = (RAIL_Time_t)tx_time_us,
        .mode = RAIL_TIME_ABSOLUTE,
    };

    /* Start hardware-scheduled TX (sub-microsecond precision!) */
    RAIL_Status_t status = RAIL_StartScheduledTx(s_rail_handle,
                                                  s_current_channel,
                                                  RAIL_TX_OPTIONS_DEFAULT,
                                                  &tx_config,
                                                  NULL);

    if (status != RAIL_STATUS_NO_ERROR) {
        LOG_WRN("Scheduled TX failed: %d (time=%llu)", status, tx_time_us);
    }

    return (status == RAIL_STATUS_NO_ERROR);
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

    /* Non-blocking receive from queue */
    return (k_msgq_get(&s_rx_queue, out_packet, K_NO_WAIT) == 0);
}

bool utlp_hal_154_rx_wait(utlp_packet_t *out_packet, uint32_t timeout_ms)
{
    if (!s_initialized || !out_packet) {
        return false;
    }

    /* Try to get from queue first */
    if (k_msgq_get(&s_rx_queue, out_packet, K_NO_WAIT) == 0) {
        return true;
    }

    /* Wait for semaphore signal */
    if (k_sem_take(&s_rx_sem, K_MSEC(timeout_ms)) == 0) {
        return (k_msgq_get(&s_rx_queue, out_packet, K_NO_WAIT) == 0);
    }

    return false;
}

uint64_t utlp_hal_154_get_last_sfd_time(void)
{
    /* Purple Team Pitfall 2: Torn Read Hazard
     * 64-bit read on 32-bit MCU requires critical section to prevent
     * reading mixed old/new halves if ISR fires mid-read.
     */
    k_spinlock_key_t key = k_spin_lock(&s_sfd_spinlock);
    uint64_t timestamp = s_last_sfd_time;
    k_spin_unlock(&s_sfd_spinlock, key);
    return timestamp;
}

bool utlp_hal_154_set_tx_power(int8_t power_dbm)
{
    if (!s_initialized) {
        return false;
    }

    /* Clamp to valid range */
    if (power_dbm > 20) power_dbm = 20;
    if (power_dbm < -30) power_dbm = -30;

    /* RAIL uses deci-dBm (10x) */
    s_tx_power_decidbm = power_dbm * 10;

    RAIL_Status_t status = RAIL_SetTxPowerDbm(s_rail_handle, s_tx_power_decidbm);
    return (status == RAIL_STATUS_NO_ERROR);
}

int8_t utlp_hal_154_get_tx_power(void)
{
    if (!s_initialized) {
        return 0;
    }

    /* Convert deci-dBm back to dBm */
    return (int8_t)(RAIL_GetTxPowerDbm(s_rail_handle) / 10);
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

    /* Restart RX on new channel */
    if (s_radio_enabled) {
        RAIL_Idle(s_rail_handle, RAIL_IDLE_ABORT, false);
        RAIL_Status_t status = RAIL_StartRx(s_rail_handle, channel, NULL);
        return (status == RAIL_STATUS_NO_ERROR);
    }

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

    if (enable && !s_radio_enabled) {
        RAIL_StartRx(s_rail_handle, s_current_channel, NULL);
        s_radio_enabled = true;
        LOG_INF("802.15.4 radio enabled");
    } else if (!enable && s_radio_enabled) {
        RAIL_Idle(s_rail_handle, RAIL_IDLE_FORCE_SHUTDOWN, false);
        s_radio_enabled = false;
        LOG_INF("802.15.4 radio disabled");
    }
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

    /* MG24 has hardware SFD timestamp via RAIL */
    caps->has_hardware_sfd_timestamp = true;

    /* MG24 has TRUE hardware-scheduled TX via RAIL */
    caps->has_hardware_scheduled_tx = true;

    /* No hardened ISR needed - RAIL hardware does scheduling */
    caps->has_hardened_isr = false;

    /* TX power range (MG24: -30 to +20 dBm) */
    caps->max_tx_power_dbm = 20;
    caps->min_tx_power_dbm = -30;

    /* All channels 11-26 supported (bits 11-26 set)
     * Byte 0: bits 0-7   → 0x00 (channels 0-7 not used)
     * Byte 1: bits 8-15  → 0xF8 (channels 11-15: bits 11-15)
     * Byte 2: bits 16-23 → 0xFF (channels 16-23)
     * Byte 3: bits 24-31 → 0x07 (channels 24-26: bits 24-26)
     */
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
