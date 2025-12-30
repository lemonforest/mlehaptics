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

#include <string.h>
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
#define DEFAULT_WIFI_CHANNEL    1
#define RX_QUEUE_DEPTH          10

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

    utlp_packet_t pkt = {
        .rx_timestamp_us = rx_time,
        .len = len,
        .rssi = info->rx_ctrl->rssi
    };
    memcpy(pkt.mac, info->src_addr, UTLP_MAC_SIZE);
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
