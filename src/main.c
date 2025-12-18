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
#include "esp_chip_info.h"
#include "esp_task_wdt.h"
#include "esp_sleep.h"
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
#include "time_sync_task.h"
#include "firmware_version.h"
#include "role_manager.h"

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

/**
 * @brief Message queue from motor_task to button_task
 *
 * Queue size: 1 message (only session timeout notification)
 * Message types: MSG_SESSION_TIMEOUT
 */
QueueHandle_t motor_to_button_queue = NULL;

/**
 * @brief Message queue from BLE task to motor_task (Phase 1b.3)
 *
 * Queue size: 2 messages (pairing result notifications)
 * Message types: MSG_PAIRING_COMPLETE, MSG_PAIRING_FAILED
 */
QueueHandle_t ble_to_motor_queue = NULL;

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
#define MOTOR_TASK_PRIORITY     6
#define BUTTON_TASK_PRIORITY    4
#define BLE_TASK_PRIORITY       3

// ============================================================================
// INITIALIZATION FUNCTIONS
// ============================================================================

/**
 * @brief Log ESP32-C6 silicon revision and capabilities
 *
 * Reports chip model, revision, and feature availability for debugging.
 * Critical for 802.11mc FTM: Initiator mode requires silicon v0.2+
 * (Errata WIFI-9686 affects v0.0 and v0.1)
 *
 * @see docs/802.11mc_FTM_Reconnaissance_Report.md Section 4.3
 */
static void log_silicon_info(void) {
    esp_chip_info_t chip_info;
    esp_chip_info(&chip_info);

    const char *model_name = "Unknown";
    switch (chip_info.model) {
        case CHIP_ESP32:   model_name = "ESP32"; break;
        case CHIP_ESP32S2: model_name = "ESP32-S2"; break;
        case CHIP_ESP32S3: model_name = "ESP32-S3"; break;
        case CHIP_ESP32C3: model_name = "ESP32-C3"; break;
        case CHIP_ESP32C6: model_name = "ESP32-C6"; break;
        case CHIP_ESP32H2: model_name = "ESP32-H2"; break;
        default: break;
    }

    // Extract major and minor revision
    // ESP-IDF v5.x: revision = (major << 8) | minor
    uint8_t rev_major = (chip_info.revision >> 8) & 0xFF;
    uint8_t rev_minor = chip_info.revision & 0xFF;

    ESP_LOGI(TAG, "Silicon: %s v%d.%d (%d cores @ %d MHz)",
             model_name, rev_major, rev_minor,
             chip_info.cores, CONFIG_ESP_DEFAULT_CPU_FREQ_MHZ);

    // Feature flags
    ESP_LOGI(TAG, "Features: WiFi%s%s%s%s",
             (chip_info.features & CHIP_FEATURE_BT) ? " BT" : "",
             (chip_info.features & CHIP_FEATURE_BLE) ? " BLE" : "",
             (chip_info.features & CHIP_FEATURE_IEEE802154) ? " 802.15.4" : "",
             (chip_info.features & CHIP_FEATURE_EMB_FLASH) ? " EmbFlash" : "");

    // 802.11mc FTM capability check (ESP32-C6 specific)
    if (chip_info.model == CHIP_ESP32C6) {
        // Errata WIFI-9686: v0.0 and v0.1 have broken FTM initiator
        bool ftm_initiator_ok = (rev_major > 0) || (rev_major == 0 && rev_minor >= 2);
        if (ftm_initiator_ok) {
            ESP_LOGI(TAG, "802.11mc FTM: Initiator + Responder (full support)");
        } else {
            ESP_LOGW(TAG, "802.11mc FTM: Responder ONLY (v0.2+ needed for Initiator)");
        }
    }

    // Note about ESP-NOW/802.11mc coexistence
    ESP_LOGI(TAG, "ESP-NOW: Available (can coexist with 802.11mc)");
}

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

    // Check if watchdog already initialized (e.g., wake from deep sleep)
    // esp_task_wdt_status() returns ESP_ERR_INVALID_STATE if not initialized
    esp_err_t ret = esp_task_wdt_status(NULL);

    if (ret == ESP_ERR_INVALID_STATE) {
        // Watchdog not initialized, initialize it now
        esp_task_wdt_config_t wdt_cfg = {
            .timeout_ms = WATCHDOG_TIMEOUT_SEC * 1000,
            .idle_core_mask = 0,  // Don't monitor idle task
            .trigger_panic = true  // Panic on timeout
        };

        ret = esp_task_wdt_init(&wdt_cfg);
        if (ret != ESP_OK) {
            ESP_LOGE(TAG, "Watchdog init failed: %s", esp_err_to_name(ret));
            return ret;
        }
        ESP_LOGI(TAG, "Watchdog initialized successfully");
    } else {
        // Already initialized (likely wake from deep sleep)
        ESP_LOGI(TAG, "Watchdog already initialized (wake from deep sleep)");
    }

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

    // 1b. Initialize Role Manager (Bug #111 Fix)
    // Must be initialized early - zone_config depends on role_get_current()
    ESP_LOGI(TAG, "Initializing Role Manager...");
    ret = role_manager_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Role Manager init failed: %s", esp_err_to_name(ret));
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

    // NOTE: Session timer initialization moved to motor_task (Phase 1b.3)
    // Session timer now starts AFTER pairing completes to ensure accurate session duration

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

    // 5. Read initial battery level BEFORE BLE init (Bug #48 Fix)
    // Battery must be known before ble_on_sync() callback fires for role assignment
    ESP_LOGI(TAG, "Reading initial battery level (Bug #48)...");
    int raw_mv = 0;
    float battery_v = 0.0f;
    int battery_pct = 0;
    if (battery_read_voltage(&raw_mv, &battery_v, &battery_pct) != ESP_OK) {
        ESP_LOGW(TAG, "Failed to read initial battery level, using 0%%");
        battery_pct = 0;
    } else {
        ESP_LOGI(TAG, "Initial battery: %.2fV [%d%%]", battery_v, battery_pct);
    }

    // 6. Initialize BLE Manager (load settings from NVS)
    // Pass initial battery for role assignment (Bug #48 Fix)
    ESP_LOGI(TAG, "Initializing BLE Manager...");
    ret = ble_manager_init((uint8_t)battery_pct);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "BLE Manager init failed: %s", esp_err_to_name(ret));
        return ret;
    }

    // 7. Update BLE characteristics with battery level
    // This updates the Configuration Service battery characteristic for mobile apps
    // (bilateral_data.battery_level already initialized in ble_on_sync())
    ESP_LOGI(TAG, "Updating BLE Configuration Service battery...");
    ble_update_battery_level((uint8_t)battery_pct);  // Configuration Service (mobile app)

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

    // Motor → Button queue (1 message, session timeout only)
    motor_to_button_queue = xQueueCreate(1, sizeof(task_message_t));
    if (motor_to_button_queue == NULL) {
        ESP_LOGE(TAG, "Failed to create motor_to_button_queue");
        vQueueDelete(button_to_motor_queue);
        vQueueDelete(button_to_ble_queue);
        return ESP_FAIL;
    }

    // BLE → Motor queue (2 messages, pairing result notifications) - Phase 1b.3
    ble_to_motor_queue = xQueueCreate(2, sizeof(task_message_t));
    if (ble_to_motor_queue == NULL) {
        ESP_LOGE(TAG, "Failed to create ble_to_motor_queue");
        vQueueDelete(button_to_motor_queue);
        vQueueDelete(button_to_ble_queue);
        vQueueDelete(motor_to_button_queue);
        return ESP_FAIL;
    }

    ESP_LOGI(TAG, "Message queues created successfully (4 queues total)");
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

    // Create Time Sync Task (Phase 2: AD039)
    esp_err_t err = time_sync_task_init();
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to create time_sync_task: %s", esp_err_to_name(err));
        return ESP_FAIL;
    }

    ESP_LOGI(TAG, "All FreeRTOS tasks created successfully");
    return ESP_OK;
}

// ============================================================================
// APPLICATION ENTRY POINT
// ============================================================================

void app_main(void) {
    // Get firmware version information
    firmware_version_t fw_version = firmware_get_version();

    ESP_LOGI(TAG, "========================================");
    ESP_LOGI(TAG, "EMDR Bilateral Stimulation Device");
    ESP_LOGI(TAG, "Hardware: Seeed XIAO ESP32-C6");
    firmware_log_version(TAG, "Firmware", fw_version);
    ESP_LOGI(TAG, "----------------------------------------");
    log_silicon_info();
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
        ESP_LOGE(TAG, "Entering deep sleep for recovery - press button to restart");
        // JPL compliance: Enter deep sleep instead of infinite loop
        // Allows button-wake recovery instead of permanent hang
        vTaskDelay(pdMS_TO_TICKS(1000));  // Allow log message to flush
        esp_deep_sleep_start();
    }

    // Create message queues
    ret = create_message_queues();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Message queue creation failed");
        ESP_LOGE(TAG, "Entering deep sleep for recovery - press button to restart");
        // JPL compliance: Enter deep sleep instead of infinite loop
        vTaskDelay(pdMS_TO_TICKS(1000));  // Allow log message to flush
        esp_deep_sleep_start();
    }

    // Create and start tasks
    ret = create_tasks();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Task creation failed");
        ESP_LOGE(TAG, "Entering deep sleep for recovery - press button to restart");
        // JPL compliance: Enter deep sleep instead of infinite loop
        vTaskDelay(pdMS_TO_TICKS(1000));  // Allow log message to flush
        esp_deep_sleep_start();
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
