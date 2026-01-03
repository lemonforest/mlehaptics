/**
 * @file utlp_hal_esp32.c
 * @brief ESP32 HAL Implementation - UTLP v2 Frontier Algorithm
 *
 * Minimal implementation for UTLP time synchronization demonstration.
 * Single actuator (LED) driven by MCPWM for phase-aligned output.
 *
 * BOARD CONFIGURATION (via build flags):
 *   -DACTUATOR_GPIO=15        GPIO for LED (default: 15 for XIAO ESP32-C6)
 *   -DACTUATOR_ACTIVE_LOW=1   LED polarity (default: 1 = active LOW)
 *
 * Examples:
 *   XIAO ESP32-C6: GPIO15, active LOW  (defaults)
 *   ESP32 DevKit:  GPIO2,  active HIGH (-DACTUATOR_GPIO=2 -DACTUATOR_ACTIVE_LOW=0)
 *
 * @version 2.2.0 - ESP32-focused (forked from skeleton)
 * @date 2025-12-29
 */

#include "utlp_hal.h"
#include "rfip_hal.h"

#include <string.h>
#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_wifi.h"
#include "esp_now.h"
#include "esp_mac.h"
#include "nvs_flash.h"
#include "driver/mcpwm_prelude.h"

static const char *TAG = "UTLP_HAL";

/*============================================================================
 * CONFIGURATION
 *
 * Board-agnostic defaults - override via build flags:
 *   -DACTUATOR_GPIO=2 -DACTUATOR_ACTIVE_LOW=0   (ESP32 DevKit v1)
 *==========================================================================*/

#ifndef ACTUATOR_GPIO
#define ACTUATOR_GPIO           15      /* Default: XIAO ESP32-C6 led_builtin */
#endif

#ifndef ACTUATOR_ACTIVE_LOW
#define ACTUATOR_ACTIVE_LOW     1       /* Default: XIAO is active LOW */
#endif

#define MCPWM_RESOLUTION_HZ     1000000 /* 1MHz = 1us resolution */
#define RX_QUEUE_DEPTH          10

/*============================================================================
 * CHANNEL CHIRALITY (S2.31 - Frequency-Dependent Selection)
 *
 * WiFi non-overlapping channels [1, 6, 11] map to a chirality space analogous
 * to snail shell coiling direction (dextral vs sinistral). Channel 6 is the
 * geometric center—the "Golden Path" where all nodes bootstrap and strangers
 * meet. This is not configuration but mathematical necessity: channel 6 is
 * the only channel equidistant from both divergence options.
 *
 * Under congestion ("predation pressure"), nodes diverge to channels 1 or 11:
 * - Channel 1: "Left-coiling" sinistral population
 * - Channel 11: "Right-coiling" sinistral population
 * - Channel 6: Dextral majority / hybrid zone (bridge nodes)
 *
 * Bridge nodes on channel 6 maintain timing coherence ("gene flow") between
 * divergent populations. Channel 1 and channel 11 nodes sync through the
 * golden path, not directly—preventing complete speciation while allowing
 * channel-local optimization.
 *
 * Prior Art: Claims 78-80 in Technical Supplement S2.31
 *
 * @see UTLP_Technical_Supplement_S2.md Section 8.22
 *==========================================================================*/

/**
 * @brief Default WiFi channel (Golden Path)
 *
 * Channel 6 is the deterministic rendezvous point for all UTLP swarms.
 * Mathematical justification: only channel equidistant from divergence
 * options [1, 11]. All nodes bootstrap here; divergence occurs under
 * congestion pressure via utlp_chirality_select_divergent_channel().
 */
#define DEFAULT_WIFI_CHANNEL    6

/**
 * @brief Non-overlapping WiFi channels for chirality divergence
 *
 * In 2.4GHz WiFi, only channels 1, 6, and 11 are non-overlapping.
 * Channel 6 is the center (golden path), while 1 and 11 are the
 * sinistral divergence options.
 */
#define WIFI_CHANNEL_SINISTRAL_LEFT   1   /**< Left-coiling divergence */
#define WIFI_CHANNEL_GOLDEN_PATH      6   /**< Dextral majority (default) */
#define WIFI_CHANNEL_SINISTRAL_RIGHT  11  /**< Right-coiling divergence */

/*============================================================================
 * STATE (Static Allocation)
 *==========================================================================*/

/** @brief Time offset for synchronization */
static volatile int64_t g_time_offset_us = 0;

/** @brief Local MAC address */
static uint8_t g_local_mac[UTLP_MAC_SIZE];

/** @brief RX packet queue */
static utlp_packet_t g_rx_queue[RX_QUEUE_DEPTH];
static volatile int g_rx_head = 0;
static volatile int g_rx_tail = 0;

/** @brief RX semaphore for precision timing */
static SemaphoreHandle_t g_rx_sem = NULL;
static StaticSemaphore_t g_rx_sem_buffer;

/** @brief MCPWM handles */
static mcpwm_timer_handle_t g_mcpwm_timer = NULL;
static mcpwm_oper_handle_t g_mcpwm_operator = NULL;
static mcpwm_cmpr_handle_t g_mcpwm_comparator = NULL;
static mcpwm_gen_handle_t g_mcpwm_generator = NULL;

/** @brief Current MCPWM state */
static uint32_t g_current_period_ticks = 0;

/*============================================================================
 * RX QUEUE HELPERS
 *==========================================================================*/

static bool rx_queue_push(const utlp_packet_t *pkt)
{
    int next = (g_rx_head + 1) % RX_QUEUE_DEPTH;
    if (next == g_rx_tail) {
        return false;  /* Queue full */
    }
    memcpy(&g_rx_queue[g_rx_head], pkt, sizeof(utlp_packet_t));
    g_rx_head = next;
    return true;
}

static bool rx_queue_pop(utlp_packet_t *out)
{
    if (g_rx_head == g_rx_tail) {
        return false;  /* Queue empty */
    }
    memcpy(out, &g_rx_queue[g_rx_tail], sizeof(utlp_packet_t));
    g_rx_tail = (g_rx_tail + 1) % RX_QUEUE_DEPTH;
    return true;
}

/*============================================================================
 * ESP-NOW CALLBACKS
 *==========================================================================*/

static void espnow_recv_cb(const esp_now_recv_info_t *info,
                           const uint8_t *data, int len)
{
    /* Timestamp immediately */
    uint64_t rx_time = esp_timer_get_time();

    if (len > UTLP_MAX_PAYLOAD) {
        return;
    }

    /* Record RSSI observation for RFIP spatial awareness */
    rfip_record_observation(info->src_addr, info->rx_ctrl->rssi, (int64_t)rx_time);

    utlp_packet_t pkt = {
        .rx_timestamp_us = rx_time,
        .len = len,
        .rssi = info->rx_ctrl->rssi
    };
    /* Populate src_addr (union overlays with mac[]) */
    memcpy(pkt.src_addr.addr, info->src_addr, UTLP_MAC_SIZE);
    pkt.src_addr.len = UTLP_MAC_SIZE;
    memcpy(pkt.payload, data, len);

    if (rx_queue_push(&pkt)) {
        /* Wake main loop immediately */
        BaseType_t woken = pdFALSE;
        xSemaphoreGiveFromISR(g_rx_sem, &woken);
        portYIELD_FROM_ISR(woken);
    }
}

static void espnow_send_cb(const wifi_tx_info_t *tx_info,
                           esp_now_send_status_t status)
{
    /* Unused for now */
    (void)tx_info;
    (void)status;
}

/*============================================================================
 * MCPWM INITIALIZATION - LED Actuator
 *
 * Polarity is board-dependent:
 *   - XIAO ESP32-C6 (GPIO15): Active LOW  (0=ON, 1=OFF)
 *   - ESP32 DevKit  (GPIO2):  Active HIGH (1=ON, 0=OFF)
 *
 * The polarity is configured via ACTUATOR_ACTIVE_LOW define.
 *==========================================================================*/

static void init_mcpwm_led(void)
{
    ESP_LOGI(TAG, "Init MCPWM on GPIO %d (led_builtin)...", ACTUATOR_GPIO);

    /*
     * Timer: 1MHz resolution, default 1kHz period (1000 ticks)
     *
     * ESP32-C6 MCPWM has 16-bit counter (max 65535 ticks).
     * At 1MHz resolution:
     *   - 1Hz    = 1,000,000 ticks (EXCEEDS LIMIT - won't work!)
     *   - 100Hz  = 10,000 ticks (OK)
     *   - 1kHz   = 1,000 ticks (OK - our default)
     *
     * UTLP uses time-indexed LED control and calls
     * set_actuator_phase() with freq=1000Hz, so 1kHz default works.
     */
    uint32_t default_period = MCPWM_RESOLUTION_HZ / 1000;  /* 1kHz = 1000 ticks */

    mcpwm_timer_config_t timer_cfg = {
        .group_id = 0,
        .clk_src = MCPWM_TIMER_CLK_SRC_DEFAULT,
        .resolution_hz = MCPWM_RESOLUTION_HZ,
        .period_ticks = default_period,
        .count_mode = MCPWM_TIMER_COUNT_MODE_UP,
    };
    ESP_ERROR_CHECK(mcpwm_new_timer(&timer_cfg, &g_mcpwm_timer));
    g_current_period_ticks = default_period;

    /* Operator */
    mcpwm_operator_config_t oper_cfg = { .group_id = 0 };
    ESP_ERROR_CHECK(mcpwm_new_operator(&oper_cfg, &g_mcpwm_operator));
    ESP_ERROR_CHECK(mcpwm_operator_connect_timer(g_mcpwm_operator, g_mcpwm_timer));

    /* Comparator */
    mcpwm_comparator_config_t cmp_cfg = {
        .flags.update_cmp_on_tez = true,
    };
    ESP_ERROR_CHECK(mcpwm_new_comparator(g_mcpwm_operator, &cmp_cfg, &g_mcpwm_comparator));

    /* Generator on actuator GPIO */
    mcpwm_generator_config_t gen_cfg = {
        .gen_gpio_num = ACTUATOR_GPIO,
    };
    ESP_ERROR_CHECK(mcpwm_new_generator(g_mcpwm_operator, &gen_cfg, &g_mcpwm_generator));

    /*
     * POLARITY CONFIGURATION:
     *
     * For intuitive duty cycle (duty=100% means LED ON):
     *
     * Active LOW (XIAO ESP32-C6):  0=ON, 1=OFF
     *   - LOW at timer zero (LED ON at start)
     *   - HIGH at compare (LED OFF after duty%)
     *
     * Active HIGH (ESP32 DevKit): 1=ON, 0=OFF
     *   - HIGH at timer zero (LED ON at start)
     *   - LOW at compare (LED OFF after duty%)
     */
#if ACTUATOR_ACTIVE_LOW
    /* Active LOW: LOW=ON, HIGH=OFF */
    ESP_ERROR_CHECK(mcpwm_generator_set_action_on_timer_event(
        g_mcpwm_generator,
        MCPWM_GEN_TIMER_EVENT_ACTION(MCPWM_TIMER_DIRECTION_UP,
                                     MCPWM_TIMER_EVENT_EMPTY,
                                     MCPWM_GEN_ACTION_LOW)));  /* LED ON at start */

    ESP_ERROR_CHECK(mcpwm_generator_set_action_on_compare_event(
        g_mcpwm_generator,
        MCPWM_GEN_COMPARE_EVENT_ACTION(MCPWM_TIMER_DIRECTION_UP,
                                       g_mcpwm_comparator,
                                       MCPWM_GEN_ACTION_HIGH)));  /* LED OFF at compare */
#else
    /* Active HIGH: HIGH=ON, LOW=OFF */
    ESP_ERROR_CHECK(mcpwm_generator_set_action_on_timer_event(
        g_mcpwm_generator,
        MCPWM_GEN_TIMER_EVENT_ACTION(MCPWM_TIMER_DIRECTION_UP,
                                     MCPWM_TIMER_EVENT_EMPTY,
                                     MCPWM_GEN_ACTION_HIGH)));  /* LED ON at start */

    ESP_ERROR_CHECK(mcpwm_generator_set_action_on_compare_event(
        g_mcpwm_generator,
        MCPWM_GEN_COMPARE_EVENT_ACTION(MCPWM_TIMER_DIRECTION_UP,
                                       g_mcpwm_comparator,
                                       MCPWM_GEN_ACTION_LOW)));  /* LED OFF at compare */
#endif

    /* Enable and start */
    ESP_ERROR_CHECK(mcpwm_timer_enable(g_mcpwm_timer));
    ESP_ERROR_CHECK(mcpwm_timer_start_stop(g_mcpwm_timer, MCPWM_TIMER_START_NO_STOP));

    /* Start with LED OFF (compare=0 means immediate switch to HIGH) */
    mcpwm_comparator_set_compare_value(g_mcpwm_comparator, 0);

    ESP_LOGI(TAG, "MCPWM initialized: GPIO%d, %s, 1MHz resolution",
             ACTUATOR_GPIO, ACTUATOR_ACTIVE_LOW ? "active LOW" : "active HIGH");
}

/*============================================================================
 * WIFI/ESP-NOW INITIALIZATION
 *==========================================================================*/

static void init_wifi_espnow(void)
{
    ESP_LOGI(TAG, "Init WiFi/ESP-NOW...");

    ESP_ERROR_CHECK(esp_netif_init());
    esp_event_loop_create_default();  /* Ignore if already exists */

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    ESP_ERROR_CHECK(esp_wifi_set_storage(WIFI_STORAGE_RAM));
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_start());
    ESP_ERROR_CHECK(esp_wifi_set_channel(DEFAULT_WIFI_CHANNEL, WIFI_SECOND_CHAN_NONE));

    /* Read MAC */
    ESP_ERROR_CHECK(esp_read_mac(g_local_mac, ESP_MAC_WIFI_STA));

    /* ESP-NOW */
    ESP_ERROR_CHECK(esp_now_init());
    ESP_ERROR_CHECK(esp_now_register_recv_cb(espnow_recv_cb));
    ESP_ERROR_CHECK(esp_now_register_send_cb(espnow_send_cb));

    /* Add broadcast peer */
    esp_now_peer_info_t peer = {
        .channel = DEFAULT_WIFI_CHANNEL,
        .ifidx = WIFI_IF_STA,
        .encrypt = false,
    };
    memset(peer.peer_addr, 0xFF, 6);
    esp_now_add_peer(&peer);

    ESP_LOGI(TAG, "WiFi/ESP-NOW ready, MAC: %02X:%02X:%02X:%02X:%02X:%02X",
             g_local_mac[0], g_local_mac[1], g_local_mac[2],
             g_local_mac[3], g_local_mac[4], g_local_mac[5]);
}

/*============================================================================
 * HAL API IMPLEMENTATION
 *==========================================================================*/

void utlp_hal_init(void)
{
    ESP_LOGI(TAG, "========================================");
    ESP_LOGI(TAG, "UTLP HAL v2 - Frontier Algorithm");
    ESP_LOGI(TAG, "========================================");

    /* NVS (required for WiFi) */
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        nvs_flash_erase();
        nvs_flash_init();
    }

    /* RX semaphore (static allocation) */
    g_rx_sem = xSemaphoreCreateBinaryStatic(&g_rx_sem_buffer);
    ESP_LOGI(TAG, "RX semaphore created");

    /* WiFi/ESP-NOW */
    init_wifi_espnow();

    /* MCPWM for LED */
    init_mcpwm_led();

    ESP_LOGI(TAG, "HAL init complete");
}

uint64_t utlp_hal_get_micros(void)
{
    return esp_timer_get_time();
}

uint64_t utlp_hal_get_atomic_time_us(void)
{
    return esp_timer_get_time() + g_time_offset_us;
}

void utlp_hal_set_time_offset(int64_t offset_us)
{
    g_time_offset_us = offset_us;
}

void utlp_hal_yield(void)
{
    vTaskDelay(1);
}

void utlp_hal_get_mac(uint8_t *mac)
{
    memcpy(mac, g_local_mac, UTLP_MAC_SIZE);
}

/*============================================================================
 * ADDRESS OPERATIONS (Transport-Agnostic)
 *
 * ESP32 uses 6-byte MAC addresses. These functions wrap the MAC in the
 * transport-agnostic utlp_addr_t structure for protocol layer compatibility.
 *==========================================================================*/

void utlp_hal_get_addr(utlp_addr_t *addr)
{
    addr->len = UTLP_MAC_SIZE;
    memcpy(addr->addr, g_local_mac, UTLP_MAC_SIZE);
}

bool utlp_hal_addr_equal(const utlp_addr_t *a, const utlp_addr_t *b)
{
    if (a->len != b->len) {
        return false;  /* Different address types are never equal */
    }
    return memcmp(a->addr, b->addr, a->len) == 0;
}

void utlp_hal_addr_to_string(const utlp_addr_t *addr, char *buf, size_t buf_len)
{
    if (buf_len < 3 * addr->len) {
        /* Not enough space even for minimal output */
        if (buf_len > 0) {
            buf[0] = '\0';
        }
        return;
    }

    size_t pos = 0;
    for (uint8_t i = 0; i < addr->len && pos + 3 < buf_len; i++) {
        if (i > 0) {
            buf[pos++] = ':';
        }
        pos += snprintf(buf + pos, buf_len - pos, "%02X", addr->addr[i]);
    }
}

uint32_t utlp_hal_addr_hash(const utlp_addr_t *addr)
{
    /* DJB2 hash - simple and effective for small data */
    uint32_t hash = 5381;
    for (uint8_t i = 0; i < addr->len; i++) {
        hash = ((hash << 5) + hash) + addr->addr[i];  /* hash * 33 + byte */
    }
    return hash;
}

/*============================================================================
 * SCHEDULED TX (Fallback Implementation)
 *
 * ESP32 ESP-NOW does not support hardware-scheduled transmission.
 * This fallback uses spin-wait between packets, achieving ~±100µs precision.
 * MG24 RAIL will provide true hardware scheduling with ±1µs precision.
 *==========================================================================*/

bool utlp_hal_has_scheduled_tx(void)
{
    return false;  /* ESP32 uses spin-wait fallback */
}

bool utlp_hal_tx_schedule(const utlp_scheduled_tx_t *packets, size_t count)
{
    for (size_t i = 0; i < count; i++) {
        /* Wait until scheduled time (spin-wait) */
        while (utlp_hal_get_micros() < packets[i].tx_time_us) {
            /* Spin - yields would add jitter */
        }
        if (!utlp_hal_tx_packet(NULL, packets[i].payload, packets[i].len)) {
            return false;  /* TX failed */
        }
    }
    return true;
}

/*============================================================================
 * PLATFORM CAPABILITY DISCOVERY
 *==========================================================================*/

void utlp_hal_get_caps(utlp_hal_caps_t *caps)
{
    caps->has_scheduled_tx = false;       /* Spin-wait fallback */
    caps->has_hw_timestamp = true;        /* ESP-NOW provides RX timestamps */
    caps->addr_size = UTLP_MAC_SIZE;      /* 6-byte MAC */
    caps->max_payload = UTLP_MAX_PAYLOAD; /* 200 bytes */
    caps->tx_power_dbm = 20;              /* ESP32 default ~20 dBm */
    caps->channel = DEFAULT_WIFI_CHANNEL; /* Channel 6 (golden path) */
}

bool utlp_hal_tx_packet(const uint8_t *peer_mac, const uint8_t *data, size_t len)
{
    if (len > UTLP_MAX_PAYLOAD) {
        return false;
    }

    static const uint8_t broadcast[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    const uint8_t *dest = peer_mac ? peer_mac : broadcast;

    return (esp_now_send(dest, data, len) == ESP_OK);
}

bool utlp_hal_rx_poll(utlp_packet_t *out_packet)
{
    return rx_queue_pop(out_packet);
}

bool utlp_hal_rx_wait(utlp_packet_t *out_packet, uint32_t timeout_ms)
{
    if (xSemaphoreTake(g_rx_sem, pdMS_TO_TICKS(timeout_ms)) == pdTRUE) {
        return rx_queue_pop(out_packet);
    }
    return false;
}

void utlp_hal_set_actuator_phase(int channel, uint32_t frequency_hz,
                                  utlp_float_t phase_deg, utlp_float_t duty_pct)
{
    if (channel != UTLP_ACTUATOR_MAIN) {
        return;
    }

    /*
     * Frequency limits (ESP32-C6 MCPWM 16-bit counter):
     *   - Min: 16 Hz (1MHz / 65535 = 15.26 Hz, round up)
     *   - Max: Practical limit ~40kHz for LED, no need for higher
     *
     * Clamp to valid range to prevent mcpwm_timer_set_period() failure.
     */
    if (frequency_hz < 16) {
        frequency_hz = 16;
    }
    if (frequency_hz > 40000) {
        frequency_hz = 40000;
    }

    /* Clamp duty */
    if (duty_pct < 0) duty_pct = 0;
    if (duty_pct > 100) duty_pct = 100;

    /* Calculate period in ticks (1MHz = 1 tick per us) */
    uint32_t period_ticks = MCPWM_RESOLUTION_HZ / frequency_hz;

    /* Update timer period if frequency changed */
    if (period_ticks != g_current_period_ticks) {
        mcpwm_timer_set_period(g_mcpwm_timer, period_ticks);
        g_current_period_ticks = period_ticks;
    }

    /* Calculate duty ticks */
    uint32_t duty_ticks = (uint32_t)((duty_pct / 100.0f) * period_ticks);

    /*
     * PHASE ALIGNMENT:
     *
     * The 'phase_deg' parameter tells us where in the cycle we want our
     * output relative to atomic time.
     *
     * For perfect sync between nodes, we don't just set duty - we need
     * the PWM cycle to align with atomic time boundaries.
     *
     * Simple approach for now: Just set duty. The time-indexed logic
     * will call this function with appropriate duty
     * (100% or 0%) at the right times based on atomic time modulo.
     *
     * True hardware phase sync would require syncing the MCPWM counter
     * to the atomic time, which is more complex.
     */
    (void)phase_deg;  /* Not used in simple mode */

    mcpwm_comparator_set_compare_value(g_mcpwm_comparator, duty_ticks);
}

void utlp_hal_actuator_stop(int channel)
{
    if (channel == UTLP_ACTUATOR_MAIN) {
        mcpwm_comparator_set_compare_value(g_mcpwm_comparator, 0);
    }
}

/*============================================================================
 * LOGGING API IMPLEMENTATION
 *
 * Maps platform-agnostic logging to ESP-IDF esp_log.
 * These functions are called from utlp.c which has no ESP dependencies.
 *==========================================================================*/

#include <stdarg.h>

void utlp_hal_log_info(const char *tag, const char *format, ...)
{
    va_list args;
    va_start(args, format);
    esp_log_writev(ESP_LOG_INFO, tag, format, args);
    va_end(args);
}

void utlp_hal_log_error(const char *tag, const char *format, ...)
{
    va_list args;
    va_start(args, format);
    esp_log_writev(ESP_LOG_ERROR, tag, format, args);
    va_end(args);
}

void utlp_hal_log_warn(const char *tag, const char *format, ...)
{
    va_list args;
    va_start(args, format);
    esp_log_writev(ESP_LOG_WARN, tag, format, args);
    va_end(args);
}

/*============================================================================
 * SEMAPHORE API IMPLEMENTATION
 *
 * Abstracts FreeRTOS semaphore operations for platform independence.
 * Uses dynamic allocation for flexibility (counting semaphores).
 *==========================================================================*/

utlp_hal_semaphore_t utlp_hal_semaphore_create(uint32_t max_count, uint32_t initial)
{
    SemaphoreHandle_t sem;

    if (max_count == 1) {
        /* Binary semaphore */
        sem = xSemaphoreCreateBinary();
        if (sem && initial > 0) {
            xSemaphoreGive(sem);
        }
    } else {
        /* Counting semaphore */
        sem = xSemaphoreCreateCounting(max_count, initial);
    }

    return (utlp_hal_semaphore_t)sem;
}

bool utlp_hal_semaphore_take(utlp_hal_semaphore_t sem, uint32_t timeout_ms)
{
    if (!sem) {
        return false;
    }

    TickType_t ticks;
    if (timeout_ms == UINT32_MAX) {
        ticks = portMAX_DELAY;
    } else {
        ticks = pdMS_TO_TICKS(timeout_ms);
    }

    return (xSemaphoreTake((SemaphoreHandle_t)sem, ticks) == pdTRUE);
}

void utlp_hal_semaphore_give(utlp_hal_semaphore_t sem)
{
    if (sem) {
        xSemaphoreGive((SemaphoreHandle_t)sem);
    }
}

void utlp_hal_semaphore_delete(utlp_hal_semaphore_t sem)
{
    if (sem) {
        vSemaphoreDelete((SemaphoreHandle_t)sem);
    }
}

/*============================================================================
 * CHANNEL CHIRALITY API (STUB - S2.31)
 *
 * The Spectral Loom: Weaving channel divergence from congestion entropy.
 *
 * Just as the Temporal Loom (utlp_trust.c) weaves Time Lords from clock
 * entropy, this API implements the Spectral Loom—detecting RF congestion
 * ("predation pressure") and weaving emergent chirality (channel divergence).
 *
 * | Loom Type  | Entropy Signal     | Emergent State     | Implementation |
 * |------------|--------------------|--------------------|----------------|
 * | Temporal   | Clock instability  | Time Lord (Anchor) | utlp_trust.c   |
 * | Spectral   | RF congestion      | Channel divergence | THIS FILE      |
 *
 * Currently stubbed - always returns golden path (channel 6).
 *
 * Future implementation will:
 * - Measure channel congestion via beacon density / collision rate
 * - Select divergent channel via deterministic function (MAC % 2)
 * - Detect bridge node status via multi-population hearing
 *
 * @see Technical Supplement S2.31, Claims 78-81
 *==========================================================================*/

/**
 * @brief Detect channel congestion level
 *
 * STUB: Always returns 0 (no congestion detected).
 *
 * Future implementation will measure:
 * - Beacon density (beacons/second on current channel)
 * - Collision rate (failed transmissions / total attempts)
 * - RSSI noise floor changes
 *
 * @return Congestion level 0-100 (0 = no congestion, 100 = saturated)
 */
uint8_t utlp_chirality_detect_congestion(void)
{
    /* STUB: No congestion detection implemented */
    return 0;
}

/**
 * @brief Select divergent channel under congestion pressure
 *
 * STUB: Always returns current channel (no divergence).
 *
 * Future implementation will:
 * - Check congestion threshold
 * - Select left (1) or right (11) based on MAC % 2
 * - Return WIFI_CHANNEL_GOLDEN_PATH if not under pressure
 *
 * @return Selected channel (1, 6, or 11)
 */
uint8_t utlp_chirality_select_divergent_channel(void)
{
    /* STUB: Always stay on golden path */
    return WIFI_CHANNEL_GOLDEN_PATH;
}

/**
 * @brief Check if this node is a bridge node (hybrid zone)
 *
 * STUB: Always returns false.
 *
 * Future implementation will detect if we can hear nodes on:
 * - Channel 6 (golden path) AND channel 1, OR
 * - Channel 6 (golden path) AND channel 11, OR
 * - All three channels (super-bridge)
 *
 * Bridge nodes maintain timing coherence between divergent populations.
 *
 * @return true if this node bridges multiple channel populations
 */
bool utlp_chirality_is_bridge_node(void)
{
    /* STUB: Never a bridge (single-channel operation) */
    return false;
}

/**
 * @brief Get current operating channel
 *
 * @return Current WiFi channel (1, 6, or 11)
 */
uint8_t utlp_chirality_get_current_channel(void)
{
    return DEFAULT_WIFI_CHANNEL;
}
