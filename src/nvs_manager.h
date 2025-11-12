/**
 * @file nvs_manager.h
 * @brief NVS Manager Module - Non-Volatile Storage management
 *
 * This module provides centralized NVS (Non-Volatile Storage) management:
 * - NVS flash initialization
 * - Factory reset (clear all NVS data)
 * - NVS namespace management
 *
 * Individual modules (ble_manager, etc.) handle their own specific
 * key/value storage, but use this module for initialization and reset.
 *
 * @date November 11, 2025
 * @author Claude Code (Anthropic)
 */

#ifndef NVS_MANAGER_H
#define NVS_MANAGER_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// NVS CONFIGURATION
// ============================================================================

/**
 * @brief Default NVS partition name
 */
#define NVS_DEFAULT_PARTITION   "nvs"

/**
 * @brief BLE settings namespace
 */
#define NVS_NAMESPACE_BLE       "ble_settings"

// ============================================================================
// PUBLIC API
// ============================================================================

/**
 * @brief Initialize NVS flash
 * @return ESP_OK on success, error code on failure
 *
 * Initializes the default NVS partition.
 * If initialization fails due to no free pages or new version,
 * erases the NVS partition and retries.
 *
 * Must be called once at boot before any NVS operations.
 * Called by main.c during system initialization.
 *
 * Thread-safe: Can be called multiple times (subsequent calls are no-ops)
 */
esp_err_t nvs_manager_init(void);

/**
 * @brief Clear all NVS data (factory reset)
 * @return ESP_OK on success, error code on failure
 *
 * Erases all NVS data across all namespaces.
 * Used for factory reset (10s button hold within first 30s after boot).
 *
 * WARNING: This operation is irreversible and will delete:
 * - All BLE configuration settings
 * - WiFi credentials (if stored)
 * - Any other application data in NVS
 *
 * After clearing, NVS is reinitialized automatically.
 */
esp_err_t nvs_clear_all(void);

/**
 * @brief Check if NVS has been initialized
 * @return true if initialized, false otherwise
 *
 * Used for diagnostics and testing.
 */
bool nvs_is_initialized(void);

#ifdef __cplusplus
}
#endif

#endif // NVS_MANAGER_H
