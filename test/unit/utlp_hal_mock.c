/**
 * @file utlp_hal_mock.c
 * @brief HAL Mock for Native Unit Testing
 *
 * Provides mock implementations of all utlp_hal_* functions for running
 * UTLP unit tests on the host PC without ESP32 hardware.
 *
 * @note This file is ONLY compiled for the native test environment.
 *       ESP32 builds use utlp_hal_esp32.c instead.
 */

#include "utlp_hal.h"
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <stdlib.h>

#ifdef _WIN32
#include <windows.h>
#else
#include <time.h>
#include <unistd.h>
#endif

/*============================================================================
 * MOCK STATE
 *==========================================================================*/

static uint64_t g_mock_time_us = 0;
static int64_t g_mock_time_offset = 0;
static uint8_t g_mock_mac[6] = {0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0x01};

/* Packet queue for testing TX/RX */
#define MOCK_PACKET_QUEUE_SIZE 32
static utlp_packet_t g_rx_queue[MOCK_PACKET_QUEUE_SIZE];
static int g_rx_queue_head = 0;
static int g_rx_queue_tail = 0;

/* Actuator state for verification */
static struct {
    uint32_t frequency_hz;
    float phase_degrees;
    float duty_percent;
    bool active;
} g_mock_actuator[4] = {0};

/* Logging capture for test verification */
#define MOCK_LOG_BUFFER_SIZE 4096
static char g_last_log[MOCK_LOG_BUFFER_SIZE];
static int g_log_count = 0;

/*============================================================================
 * TEST CONTROL API
 *==========================================================================*/

/**
 * @brief Advance mock time by given microseconds
 */
void mock_advance_time_us(uint64_t delta_us) {
    g_mock_time_us += delta_us;
}

/**
 * @brief Set mock time to specific value
 */
void mock_set_time_us(uint64_t time_us) {
    g_mock_time_us = time_us;
}

/**
 * @brief Set mock MAC address
 */
void mock_set_mac(const uint8_t *mac) {
    memcpy(g_mock_mac, mac, 6);
}

/**
 * @brief Inject a packet into the RX queue (simulates receiving)
 */
bool mock_inject_rx_packet(const utlp_packet_t *packet) {
    int next_tail = (g_rx_queue_tail + 1) % MOCK_PACKET_QUEUE_SIZE;
    if (next_tail == g_rx_queue_head) {
        return false;  /* Queue full */
    }
    memcpy(&g_rx_queue[g_rx_queue_tail], packet, sizeof(utlp_packet_t));
    g_rx_queue_tail = next_tail;
    return true;
}

/**
 * @brief Get actuator state for test verification
 */
void mock_get_actuator_state(int channel, uint32_t *freq, float *phase, float *duty, bool *active) {
    if (channel >= 0 && channel < 4) {
        if (freq) *freq = g_mock_actuator[channel].frequency_hz;
        if (phase) *phase = g_mock_actuator[channel].phase_degrees;
        if (duty) *duty = g_mock_actuator[channel].duty_percent;
        if (active) *active = g_mock_actuator[channel].active;
    }
}

/**
 * @brief Get last log message
 */
const char* mock_get_last_log(void) {
    return g_last_log;
}

/**
 * @brief Get total log count
 */
int mock_get_log_count(void) {
    return g_log_count;
}

/**
 * @brief Reset all mock state
 */
/* Forward declaration for test reset */
extern void smsp_reset_for_testing(void);

void mock_reset(void) {
    g_mock_time_us = 0;
    g_mock_time_offset = 0;
    g_rx_queue_head = 0;
    g_rx_queue_tail = 0;
    memset(g_mock_actuator, 0, sizeof(g_mock_actuator));
    g_last_log[0] = '\0';
    g_log_count = 0;

    /* Also reset SMSP state for test isolation */
    smsp_reset_for_testing();
}

/*============================================================================
 * HAL IMPLEMENTATION (Mock)
 *==========================================================================*/

void utlp_hal_init(void) {
    mock_reset();
}

uint64_t utlp_hal_get_micros(void) {
    return g_mock_time_us;
}

uint64_t utlp_hal_get_atomic_time_us(void) {
    return (uint64_t)((int64_t)g_mock_time_us + g_mock_time_offset);
}

void utlp_hal_set_time_offset(int64_t offset_us) {
    g_mock_time_offset = offset_us;
}

void utlp_hal_yield(void) {
    /* No-op in mock */
}

/*============================================================================
 * SEMAPHORE MOCK
 *==========================================================================*/

typedef struct {
    int count;
    int max_count;
} mock_semaphore_t;

utlp_hal_semaphore_t utlp_hal_semaphore_create(uint32_t max_count, uint32_t initial) {
    mock_semaphore_t *sem = (mock_semaphore_t*)malloc(sizeof(mock_semaphore_t));
    if (sem) {
        sem->count = (int)initial;
        sem->max_count = (int)max_count;
    }
    return (utlp_hal_semaphore_t)sem;
}

bool utlp_hal_semaphore_take(utlp_hal_semaphore_t sem, uint32_t timeout_ms) {
    (void)timeout_ms;
    mock_semaphore_t *s = (mock_semaphore_t*)sem;
    if (s && s->count > 0) {
        s->count--;
        return true;
    }
    return false;
}

void utlp_hal_semaphore_give(utlp_hal_semaphore_t sem) {
    mock_semaphore_t *s = (mock_semaphore_t*)sem;
    if (s && s->count < s->max_count) {
        s->count++;
    }
}

void utlp_hal_semaphore_delete(utlp_hal_semaphore_t sem) {
    free(sem);
}

/*============================================================================
 * NETWORK MOCK
 *==========================================================================*/

void utlp_hal_get_mac(uint8_t *mac) {
    memcpy(mac, g_mock_mac, 6);
}

bool utlp_hal_tx_packet(const uint8_t *peer_mac, const uint8_t *data, size_t len) {
    (void)peer_mac;
    (void)data;
    (void)len;
    /* In mock, TX always succeeds - tests can verify via callbacks if needed */
    return true;
}

bool utlp_hal_rx_poll(utlp_packet_t *out_packet) {
    if (g_rx_queue_head == g_rx_queue_tail) {
        return false;  /* Queue empty */
    }
    memcpy(out_packet, &g_rx_queue[g_rx_queue_head], sizeof(utlp_packet_t));
    g_rx_queue_head = (g_rx_queue_head + 1) % MOCK_PACKET_QUEUE_SIZE;
    return true;
}

bool utlp_hal_rx_wait(utlp_packet_t *out_packet, uint32_t timeout_ms) {
    (void)timeout_ms;
    return utlp_hal_rx_poll(out_packet);
}

/*============================================================================
 * ACTUATOR MOCK
 *==========================================================================*/

void utlp_hal_set_actuator_phase(int channel, uint32_t frequency_hz,
                                  float phase_degrees, float duty_percent) {
    if (channel >= 0 && channel < 4) {
        g_mock_actuator[channel].frequency_hz = frequency_hz;
        g_mock_actuator[channel].phase_degrees = phase_degrees;
        g_mock_actuator[channel].duty_percent = duty_percent;
        g_mock_actuator[channel].active = (duty_percent > 0.0f);
    }
}

void utlp_hal_actuator_stop(int channel) {
    if (channel >= 0 && channel < 4) {
        g_mock_actuator[channel].active = false;
        g_mock_actuator[channel].duty_percent = 0.0f;
    }
}

/*============================================================================
 * LOGGING MOCK
 *==========================================================================*/

void utlp_hal_log_info(const char *tag, const char *format, ...) {
    va_list args;
    va_start(args, format);
    snprintf(g_last_log, MOCK_LOG_BUFFER_SIZE, "[%s] ", tag);
    size_t offset = strlen(g_last_log);
    vsnprintf(g_last_log + offset, MOCK_LOG_BUFFER_SIZE - offset, format, args);
    va_end(args);
    g_log_count++;

    /* Also print to stdout for debugging */
    printf("I %s\n", g_last_log);
}

void utlp_hal_log_error(const char *tag, const char *format, ...) {
    va_list args;
    va_start(args, format);
    snprintf(g_last_log, MOCK_LOG_BUFFER_SIZE, "[%s] ERROR: ", tag);
    size_t offset = strlen(g_last_log);
    vsnprintf(g_last_log + offset, MOCK_LOG_BUFFER_SIZE - offset, format, args);
    va_end(args);
    g_log_count++;

    printf("E %s\n", g_last_log);
}

void utlp_hal_log_warn(const char *tag, const char *format, ...) {
    va_list args;
    va_start(args, format);
    snprintf(g_last_log, MOCK_LOG_BUFFER_SIZE, "[%s] WARN: ", tag);
    size_t offset = strlen(g_last_log);
    vsnprintf(g_last_log + offset, MOCK_LOG_BUFFER_SIZE - offset, format, args);
    va_end(args);
    g_log_count++;

    printf("W %s\n", g_last_log);
}
