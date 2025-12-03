/**
 * @file motor_control.c
 * @brief Motor Control Implementation - H-bridge PWM control via LEDC
 *
 * Implements low-level motor control using ESP32-C6 LEDC peripheral.
 * Provides forward/reverse PWM control with safety limits.
 * Extracted from single_device_ble_gatt_test.c reference implementation.
 *
 * @date November 11, 2025
 * @author Claude Code (Anthropic)
 */

#include "motor_control.h"
#include "esp_log.h"
#include "driver/ledc.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

static const char *TAG = "MOTOR_CTRL";

// ============================================================================
// JPL COMPLIANCE
// ============================================================================

/**
 * @brief Mutex timeout for motor control operations
 *
 * JPL Rule #6: No unbounded waits - all mutex operations must have timeouts
 * 100ms timeout provides safety margin for motor control operations
 * If mutex timeout occurs, indicates potential deadlock or system failure
 */
#define MUTEX_TIMEOUT_MS 100

/**
 * @brief Dead-time delay for shoot-through protection (milliseconds)
 *
 * With discrete MOSFETs (no H-bridge IC with built-in protection), we must
 * ensure the opposite channel is fully OFF before turning on the desired channel.
 * 1ms provides sufficient margin for MOSFET turn-off time (~100ns typical)
 * while adding negligible timing error at therapeutic frequencies (0.5-2Hz).
 *
 * Sequence: Turn OFF opposite channel → wait DEAD_TIME_MS → turn ON desired channel
 */
#define DEAD_TIME_MS 1

// ============================================================================
// MOTOR STATE
// ============================================================================

static uint8_t current_intensity = MOTOR_PWM_DEFAULT;
static bool motor_initialized = false;
static bool motor_coasting = true;
static SemaphoreHandle_t motor_mutex = NULL;

// ============================================================================
// INTERNAL HELPERS
// ============================================================================

/**
 * @brief Clamp PWM intensity to safety limits
 * @param intensity_percent Input intensity percentage
 * @return Clamped intensity (0-80%, 0% = LED-only mode)
 */
static uint8_t clamp_intensity(uint8_t intensity_percent) {
    // Note: MOTOR_PWM_MIN is 0 (LED-only mode), so no minimum check needed
    // uint8_t is unsigned, so it can't be < 0
    if (intensity_percent > MOTOR_PWM_MAX) {
        ESP_LOGW(TAG, "Intensity %u%% above maximum, clamping to %u%%",
                 intensity_percent, MOTOR_PWM_MAX);
        return MOTOR_PWM_MAX;
    }
    return intensity_percent;
}

/**
 * @brief Convert percentage to 10-bit duty cycle value
 * @param percent Percentage 0-100
 * @return Duty cycle value 0-1023
 */
static uint32_t percent_to_duty(uint8_t percent) {
    // 10-bit resolution = 1024 levels (0-1023)
    // duty = (percent / 100) × 1023
    return (uint32_t)((percent * 1023) / 100);
}

// ============================================================================
// PUBLIC API IMPLEMENTATION
// ============================================================================

esp_err_t motor_init(void) {
    ESP_LOGI(TAG, "Initializing motor control");

    // Create mutex for thread-safe motor operations
    motor_mutex = xSemaphoreCreateMutex();
    if (motor_mutex == NULL) {
        ESP_LOGE(TAG, "Failed to create motor mutex");
        return ESP_ERR_NO_MEM;
    }

    // Configure LEDC timer
    ledc_timer_config_t timer_cfg = {
        .speed_mode = MOTOR_PWM_MODE,
        .duty_resolution = MOTOR_PWM_RESOLUTION,
        .timer_num = MOTOR_PWM_TIMER,
        .freq_hz = MOTOR_PWM_FREQUENCY,
        .clk_cfg = LEDC_AUTO_CLK
    };

    esp_err_t ret = ledc_timer_config(&timer_cfg);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "LEDC timer config failed: %s", esp_err_to_name(ret));
        return ret;
    }

    // Configure LEDC channel for IN2 (reverse/backward) - GPIO19
    ledc_channel_config_t in2_cfg = {
        .gpio_num = GPIO_HBRIDGE_IN2,
        .speed_mode = MOTOR_PWM_MODE,
        .channel = MOTOR_LEDC_CHANNEL_IN2,
        .intr_type = LEDC_INTR_DISABLE,
        .timer_sel = MOTOR_PWM_TIMER,
        .duty = 0,  // Start at 0% duty (coast)
        .hpoint = 0
    };

    ret = ledc_channel_config(&in2_cfg);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "LEDC IN2 channel config failed: %s", esp_err_to_name(ret));
        return ret;
    }

    // Configure LEDC channel for IN1 (forward) - GPIO20
    ledc_channel_config_t in1_cfg = {
        .gpio_num = GPIO_HBRIDGE_IN1,
        .speed_mode = MOTOR_PWM_MODE,
        .channel = MOTOR_LEDC_CHANNEL_IN1,
        .intr_type = LEDC_INTR_DISABLE,
        .timer_sel = MOTOR_PWM_TIMER,
        .duty = 0,  // Start at 0% duty (coast)
        .hpoint = 0
    };

    ret = ledc_channel_config(&in1_cfg);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "LEDC IN1 channel config failed: %s", esp_err_to_name(ret));
        return ret;
    }

    motor_initialized = true;
    motor_coasting = true;
    current_intensity = MOTOR_PWM_DEFAULT;

    ESP_LOGI(TAG, "Motor control initialized successfully");
    ESP_LOGI(TAG, "PWM: %u Hz, 10-bit resolution (1024 levels)", MOTOR_PWM_FREQUENCY);
    ESP_LOGI(TAG, "Safety limits: %u-%u%% PWM intensity", MOTOR_PWM_MIN, MOTOR_PWM_MAX);

    return ESP_OK;
}

esp_err_t motor_set_forward(uint8_t intensity_percent, bool verbose_logging) {
    if (!motor_initialized) {
        ESP_LOGE(TAG, "Motor not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(motor_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in motor_set_forward - possible deadlock");
        return ESP_ERR_TIMEOUT;
    }

    // Clamp intensity to safety limits
    intensity_percent = clamp_intensity(intensity_percent);
    current_intensity = intensity_percent;

    // Convert to duty cycle value
    uint32_t duty = percent_to_duty(intensity_percent);

    // SHOOT-THROUGH PROTECTION: Turn OFF opposite channel FIRST
    // With discrete MOSFETs, both channels HIGH simultaneously = short circuit
    esp_err_t ret = ledc_set_duty(MOTOR_PWM_MODE, MOTOR_LEDC_CHANNEL_IN2, 0);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to set IN2 duty: %s", esp_err_to_name(ret));
        xSemaphoreGive(motor_mutex);
        return ret;
    }

    ret = ledc_update_duty(MOTOR_PWM_MODE, MOTOR_LEDC_CHANNEL_IN2);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to update IN2 duty: %s", esp_err_to_name(ret));
        xSemaphoreGive(motor_mutex);
        return ret;
    }

    // Dead-time: Wait for MOSFET to fully turn off before turning on opposite side
    vTaskDelay(pdMS_TO_TICKS(DEAD_TIME_MS));

    // NOW safe to turn on forward channel (IN1)
    ret = ledc_set_duty(MOTOR_PWM_MODE, MOTOR_LEDC_CHANNEL_IN1, duty);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to set IN1 duty: %s", esp_err_to_name(ret));
        xSemaphoreGive(motor_mutex);
        return ret;
    }

    ret = ledc_update_duty(MOTOR_PWM_MODE, MOTOR_LEDC_CHANNEL_IN1);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to update IN1 duty: %s", esp_err_to_name(ret));
        xSemaphoreGive(motor_mutex);
        return ret;
    }

    motor_coasting = false;

    xSemaphoreGive(motor_mutex);

    if (verbose_logging) {
        ESP_LOGI(TAG, "Motor forward: %u%% (duty=%u/1023)", intensity_percent, duty);
    }
    return ESP_OK;
}

esp_err_t motor_set_reverse(uint8_t intensity_percent, bool verbose_logging) {
    if (!motor_initialized) {
        ESP_LOGE(TAG, "Motor not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(motor_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in motor_set_reverse - possible deadlock");
        return ESP_ERR_TIMEOUT;
    }

    // Clamp intensity to safety limits
    intensity_percent = clamp_intensity(intensity_percent);
    current_intensity = intensity_percent;

    // Convert to duty cycle value
    uint32_t duty = percent_to_duty(intensity_percent);

    // SHOOT-THROUGH PROTECTION: Turn OFF opposite channel FIRST
    // With discrete MOSFETs, both channels HIGH simultaneously = short circuit
    esp_err_t ret = ledc_set_duty(MOTOR_PWM_MODE, MOTOR_LEDC_CHANNEL_IN1, 0);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to set IN1 duty: %s", esp_err_to_name(ret));
        xSemaphoreGive(motor_mutex);
        return ret;
    }

    ret = ledc_update_duty(MOTOR_PWM_MODE, MOTOR_LEDC_CHANNEL_IN1);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to update IN1 duty: %s", esp_err_to_name(ret));
        xSemaphoreGive(motor_mutex);
        return ret;
    }

    // Dead-time: Wait for MOSFET to fully turn off before turning on opposite side
    vTaskDelay(pdMS_TO_TICKS(DEAD_TIME_MS));

    // NOW safe to turn on reverse channel (IN2)
    ret = ledc_set_duty(MOTOR_PWM_MODE, MOTOR_LEDC_CHANNEL_IN2, duty);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to set IN2 duty: %s", esp_err_to_name(ret));
        xSemaphoreGive(motor_mutex);
        return ret;
    }

    ret = ledc_update_duty(MOTOR_PWM_MODE, MOTOR_LEDC_CHANNEL_IN2);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to update IN2 duty: %s", esp_err_to_name(ret));
        xSemaphoreGive(motor_mutex);
        return ret;
    }

    motor_coasting = false;

    xSemaphoreGive(motor_mutex);

    if (verbose_logging) {
        ESP_LOGI(TAG, "Motor reverse: %u%% (duty=%u/1023)", intensity_percent, duty);
    }
    return ESP_OK;
}

void motor_coast(bool verbose_logging) {
    if (!motor_initialized) {
        ESP_LOGW(TAG, "Motor not initialized, cannot coast");
        return;
    }

    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(motor_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in motor_coast - possible deadlock");
        return;  // Cannot coast motor safely
    }

    // Set both IN1 and IN2 to LOW (0% duty)
    ledc_set_duty(MOTOR_PWM_MODE, MOTOR_LEDC_CHANNEL_IN1, 0);
    ledc_update_duty(MOTOR_PWM_MODE, MOTOR_LEDC_CHANNEL_IN1);

    ledc_set_duty(MOTOR_PWM_MODE, MOTOR_LEDC_CHANNEL_IN2, 0);
    ledc_update_duty(MOTOR_PWM_MODE, MOTOR_LEDC_CHANNEL_IN2);

    motor_coasting = true;

    xSemaphoreGive(motor_mutex);

    if (verbose_logging) {
        ESP_LOGI(TAG, "Motor coasting (both channels 0%%)");
    }
}

uint8_t motor_get_intensity(void) {
    uint8_t intensity;
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(motor_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in motor_get_intensity - possible deadlock");
        return MOTOR_PWM_DEFAULT;  // Return safe default value
    }
    intensity = current_intensity;
    xSemaphoreGive(motor_mutex);
    return intensity;
}

bool motor_is_coasting(void) {
    bool coasting;
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(motor_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in motor_is_coasting - possible deadlock");
        return true;  // Return safe default (assume coasting if uncertain)
    }
    coasting = motor_coasting;
    xSemaphoreGive(motor_mutex);
    return coasting;
}

esp_err_t motor_deinit(void) {
    ESP_LOGI(TAG, "Deinitializing motor control");

    // Coast motor before deinit
    motor_coast(false);  // Shutdown - no logging needed

    // Stop LEDC channels
    if (motor_initialized) {
        esp_err_t ret = ledc_stop(MOTOR_PWM_MODE, MOTOR_LEDC_CHANNEL_IN1, 0);
        if (ret != ESP_OK) {
            ESP_LOGW(TAG, "Failed to stop IN1 channel: %s", esp_err_to_name(ret));
        }

        ret = ledc_stop(MOTOR_PWM_MODE, MOTOR_LEDC_CHANNEL_IN2, 0);
        if (ret != ESP_OK) {
            ESP_LOGW(TAG, "Failed to stop IN2 channel: %s", esp_err_to_name(ret));
        }

        // Note: LEDC timer deinit not available in ESP-IDF API
        // Timer will be automatically reconfigured on next init

        motor_initialized = false;
    }

    // Delete mutex
    if (motor_mutex != NULL) {
        vSemaphoreDelete(motor_mutex);
        motor_mutex = NULL;
    }

    ESP_LOGI(TAG, "Motor control deinitialized");
    return ESP_OK;
}
