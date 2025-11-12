/**
 * @file main.c
 * @brief EMDR Bilateral Stimulation Device - Main Application Entry Point
 *
 * This is the main application file for the EMDR bilateral stimulation device.
 * It initializes all hardware modules, creates FreeRTOS tasks and message queues,
 * and starts the main control loops.
 *
 * System Architecture:
 * - motor_task: 8-state motor control with bilateral alternation
 * - ble_task: 4-state BLE advertising lifecycle management
 * - button_task: 8-state button handler with hold detection
 *
 * Hardware Modules:
 * - NVS Manager: Non-volatile storage for user settings
 * - Battery Monitor: ADC-based voltage and back-EMF sensing
 * - Motor Control: LEDC PWM for H-bridge control
 * - LED Control: RMT-based WS2812B RGB control
 * - BLE Manager: NimBLE GATT Configuration Service (AD032)
 *
 * Power Management:
 * - Deep sleep on 5s button hold
 * - Battery low voltage protection (LVO)
 * - Settings persistence to NVS
 *
 * @date November 11, 2025
 * @author Claude Code (Anthropic)
 */

#include <stdio.h>
#include "esp_log.h"
#include "esp_system.h"
#include "esp_task_wdt.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"

// Module headers
#include "nvs_manager.h"
#include "battery_monitor.h"
#include "motor_control.h"
#include "led_control.h"
#include "ble_manager.h"
#include "motor_task.h"
#include "ble_task.h"
#include "button_task.h"
#include "power_manager.h"

static const char *TAG = "MAIN";

// ============================================================================
// GLOBAL MESSAGE QUEUES
// ============================================================================

/**
 * @brief Message queue from button_task to motor_task
 *
 * Queue size: 5 messages (mode changes can queue up)
 * Message types: MSG_MODE_CHANGE, MSG_EMERGENCY_SHUTDOWN
 */
QueueHandle_t button_to_motor_queue = NULL;

/**
 * @brief Message queue from button_task to BLE task
 *
 * Queue size: 3 messages (small, low traffic)
 * Message types: MSG_BLE_REENABLE, MSG_EMERGENCY_SHUTDOWN
 */
QueueHandle_t button_to_ble_queue = NULL;

// ============================================================================
// WATCHDOG CONFIGURATION
// ============================================================================

/**
 * @brief Watchdog timeout configuration
 *
 * Set to 2 seconds to provide safety margin for:
 * - Motor duty cycles (up to 500ms)
 * - Task scheduling overhead
 * - Purple LED countdown loop (200ms intervals)
 */
#define WATCHDOG_TIMEOUT_SEC    2

// ============================================================================
// TASK CONFIGURATION
// ============================================================================

/**
 * @brief FreeRTOS task stack sizes (bytes)
 */
#define MOTOR_TASK_STACK_SIZE   4096    /**< Motor task stack (increased for stability) */
#define BLE_TASK_STACK_SIZE     3072    /**< BLE task stack */
#define BUTTON_TASK_STACK_SIZE  3072    /**< Button task stack */

/**
 * @brief FreeRTOS task priorities
 *
 * Higher number = higher priority
 * Button task has highest priority for responsiveness
 * Motor task second for timing accuracy
 * BLE task lowest (non-critical background)
 */
#define MOTOR_TASK_PRIORITY     5
#define BUTTON_TASK_PRIORITY    4
#define BLE_TASK_PRIORITY       3

// ============================================================================
// INITIALIZATION FUNCTIONS
// ============================================================================

/**
 * @brief Initialize watchdog timer
 * @return ESP_OK on success, error code on failure
 *
 * Configures Task Watchdog Timer (TWDT) for safety monitoring:
 * - Timeout: 2 seconds
 * - Panic on timeout (trigger reset)
 * - Tasks subscribe individually via esp_task_wdt_add()
 */
static esp_err_t init_watchdog(void) {
    ESP_LOGI(TAG, "Initializing watchdog (%d sec timeout)", WATCHDOG_TIMEOUT_SEC);

    esp_task_wdt_config_t wdt_cfg = {
        .timeout_ms = WATCHDOG_TIMEOUT_SEC * 1000,
        .idle_core_mask = 0,  // Don't monitor idle task
        .trigger_panic = true  // Panic on timeout
    };

    esp_err_t ret = esp_task_wdt_init(&wdt_cfg);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Watchdog init failed: %s", esp_err_to_name(ret));
        return ret;
    }

    ESP_LOGI(TAG, "Watchdog initialized successfully");
    return ESP_OK;
}

/**
 * @brief Initialize all hardware modules in correct order
 * @return ESP_OK on success, error code on failure
 *
 * Initialization sequence:
 * 1. NVS Manager (required for BLE and settings)
 * 2. Battery Monitor (ADC, check LVO)
 * 3. Motor Control (LEDC PWM)
 * 4. LED Control (RMT + WS2812B)
 * 5. BLE Manager (NimBLE GATT server)
 */
static esp_err_t init_hardware(void) {
    esp_err_t ret;

    // 1. Initialize NVS Manager
    ESP_LOGI(TAG, "Initializing NVS Manager...");
    ret = nvs_manager_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "NVS Manager init failed: %s", esp_err_to_name(ret));
        return ret;
    }

    // 2. Initialize Battery Monitor
    ESP_LOGI(TAG, "Initializing Battery Monitor...");
    ret = battery_monitor_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Battery Monitor init failed: %s", esp_err_to_name(ret));
        return ret;
    }

    // Check battery level (LVO protection)
    ESP_LOGI(TAG, "Checking battery level (LVO)...");
    bool battery_ok = power_check_battery();
    if (!battery_ok) {
        // power_check_battery() enters deep sleep if battery critical
        // This line should never be reached
        ESP_LOGE(TAG, "Battery check failed (should have entered deep sleep)");
        return ESP_FAIL;
    }

    // 3. Initialize Motor Control
    ESP_LOGI(TAG, "Initializing Motor Control...");
    ret = motor_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Motor Control init failed: %s", esp_err_to_name(ret));
        return ret;
    }

    // 4. Initialize LED Control
    ESP_LOGI(TAG, "Initializing LED Control...");
    ret = led_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "LED Control init failed: %s", esp_err_to_name(ret));
        return ret;
    }

    // Enable LED power (P-MOSFET gate control)
    led_enable();
    ESP_LOGI(TAG, "LED power enabled");

    // 5. Initialize BLE Manager (load settings from NVS)
    ESP_LOGI(TAG, "Initializing BLE Manager...");
    ret = ble_manager_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "BLE Manager init failed: %s", esp_err_to_name(ret));
        return ret;
    }

    ESP_LOGI(TAG, "All hardware modules initialized successfully");
    return ESP_OK;
}

/**
 * @brief Create FreeRTOS message queues
 * @return ESP_OK on success, ESP_FAIL on failure
 *
 * Creates message queues for inter-task communication:
 * - button_to_motor_queue: Button → Motor (mode changes, shutdown)
 * - button_to_ble_queue: Button → BLE (re-enable, shutdown)
 */
static esp_err_t create_message_queues(void) {
    ESP_LOGI(TAG, "Creating message queues...");

    // Button → Motor queue (5 messages, mode changes can queue up)
    button_to_motor_queue = xQueueCreate(5, sizeof(task_message_t));
    if (button_to_motor_queue == NULL) {
        ESP_LOGE(TAG, "Failed to create button_to_motor_queue");
        return ESP_FAIL;
    }

    // Button → BLE queue (3 messages, low traffic)
    button_to_ble_queue = xQueueCreate(3, sizeof(task_message_t));
    if (button_to_ble_queue == NULL) {
        ESP_LOGE(TAG, "Failed to create button_to_ble_queue");
        vQueueDelete(button_to_motor_queue);
        return ESP_FAIL;
    }

    ESP_LOGI(TAG, "Message queues created successfully");
    return ESP_OK;
}

/**
 * @brief Create and start FreeRTOS tasks
 * @return ESP_OK on success, ESP_FAIL on failure
 *
 * Creates tasks in order:
 * 1. Motor task (priority 5, 4096 bytes stack)
 * 2. BLE task (priority 3, 3072 bytes stack)
 * 3. Button task (priority 4, 3072 bytes stack)
 *
 * All tasks are unpinned (auto-assigned to core)
 */
static esp_err_t create_tasks(void) {
    ESP_LOGI(TAG, "Creating FreeRTOS tasks...");

    BaseType_t ret;

    // Create Motor Task
    ret = xTaskCreate(
        motor_task,
        "motor_task",
        MOTOR_TASK_STACK_SIZE,
        NULL,
        MOTOR_TASK_PRIORITY,
        NULL
    );
    if (ret != pdPASS) {
        ESP_LOGE(TAG, "Failed to create motor_task");
        return ESP_FAIL;
    }

    // Create BLE Task
    ret = xTaskCreate(
        ble_task,
        "ble_task",
        BLE_TASK_STACK_SIZE,
        NULL,
        BLE_TASK_PRIORITY,
        NULL
    );
    if (ret != pdPASS) {
        ESP_LOGE(TAG, "Failed to create ble_task");
        return ESP_FAIL;
    }

    // Create Button Task
    ret = xTaskCreate(
        button_task,
        "button_task",
        BUTTON_TASK_STACK_SIZE,
        NULL,
        BUTTON_TASK_PRIORITY,
        NULL
    );
    if (ret != pdPASS) {
        ESP_LOGE(TAG, "Failed to create button_task");
        return ESP_FAIL;
    }

    ESP_LOGI(TAG, "All FreeRTOS tasks created successfully");
    return ESP_OK;
}

// ============================================================================
// APPLICATION ENTRY POINT
// ============================================================================

void app_main(void) {
    ESP_LOGI(TAG, "========================================");
    ESP_LOGI(TAG, "EMDR Bilateral Stimulation Device");
    ESP_LOGI(TAG, "Hardware: Seeed XIAO ESP32-C6");
    ESP_LOGI(TAG, "Firmware: Modular BLE GATT v1.0");
    ESP_LOGI(TAG, "Build Date: %s %s", __DATE__, __TIME__);
    ESP_LOGI(TAG, "========================================");

    esp_err_t ret;

    // Initialize watchdog
    ret = init_watchdog();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Watchdog init failed, continuing anyway");
    }

    // Initialize hardware modules
    ret = init_hardware();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Hardware init failed: %s", esp_err_to_name(ret));
        ESP_LOGE(TAG, "System halted");
        while (1) {
            vTaskDelay(pdMS_TO_TICKS(1000));
        }
    }

    // Create message queues
    ret = create_message_queues();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Message queue creation failed");
        ESP_LOGE(TAG, "System halted");
        while (1) {
            vTaskDelay(pdMS_TO_TICKS(1000));
        }
    }

    // Create and start tasks
    ret = create_tasks();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Task creation failed");
        ESP_LOGE(TAG, "System halted");
        while (1) {
            vTaskDelay(pdMS_TO_TICKS(1000));
        }
    }

    ESP_LOGI(TAG, "========================================");
    ESP_LOGI(TAG, "System initialization complete");
    ESP_LOGI(TAG, "Motor task: Priority %d, Stack %d bytes", MOTOR_TASK_PRIORITY, MOTOR_TASK_STACK_SIZE);
    ESP_LOGI(TAG, "BLE task: Priority %d, Stack %d bytes", BLE_TASK_PRIORITY, BLE_TASK_STACK_SIZE);
    ESP_LOGI(TAG, "Button task: Priority %d, Stack %d bytes", BUTTON_TASK_PRIORITY, BUTTON_TASK_STACK_SIZE);
    ESP_LOGI(TAG, "========================================");
    ESP_LOGI(TAG, "System running...");

    // Main task complete, tasks are now running independently
    // This task can be deleted as it's no longer needed
    vTaskDelete(NULL);
}
