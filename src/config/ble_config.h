/**
 * @file ble_config.h
 * @brief BLE Configuration Constants (Single Source of Truth)
 *
 * This header provides centralized BLE configuration constants.
 * All BLE-related magic numbers should be extracted here.
 *
 * SSOT Rule: Never hardcode BLE values. Always import and use named constants.
 *
 * @see CLAUDE.md "NO MAGIC NUMBERS" section
 * @date December 2025
 * @author Claude Code (Anthropic)
 */

#ifndef BLE_CONFIG_H
#define BLE_CONFIG_H

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// BLE ADVERTISING PARAMETERS
// ============================================================================

/**
 * @brief Peer discovery window duration (ms)
 *
 * Duration for broadcasting Bilateral Service UUID before switching
 * to Configuration Service UUID only. Allows peer devices to find each other.
 */
#define BLE_PEER_DISCOVERY_WINDOW_MS    30000

/**
 * @brief Advertising timeout duration (ms)
 *
 * Maximum time to advertise before timing out.
 * 5 minutes = 300000ms
 */
#define BLE_ADV_TIMEOUT_MS              300000

/**
 * @brief Minimum advertising interval (BLE units)
 *
 * BLE units = 0.625ms each
 * 160 units = 100ms
 */
#define BLE_ADV_INTERVAL_MIN_UNITS      160

/**
 * @brief Maximum advertising interval (BLE units)
 *
 * BLE units = 0.625ms each
 * 320 units = 200ms
 */
#define BLE_ADV_INTERVAL_MAX_UNITS      320

// ============================================================================
// BLE CONNECTION PARAMETERS
// ============================================================================

/**
 * @brief Maximum number of simultaneous BLE connections
 *
 * 2 = one peer device + one mobile app (PWA)
 * Per Bug #6 fix in Phase 1b.1
 */
#define BLE_MAX_CONNECTIONS             2

/**
 * @brief MTU (Maximum Transmission Unit) size
 *
 * 256 bytes provides room for pattern data transfer.
 */
#define BLE_MTU_SIZE                    256

// ============================================================================
// BLE GATT CHARACTERISTICS
// ============================================================================

/**
 * @brief Number of GATT characteristics in Configuration Service
 *
 * 9 characteristics per AD032 specification.
 */
#define BLE_GATT_CHAR_COUNT             9

// ============================================================================
// BLE SCAN PARAMETERS
// ============================================================================

/**
 * @brief Scan window duration (BLE units)
 *
 * BLE units = 0.625ms each
 * 100 units = 62.5ms
 */
#define BLE_SCAN_WINDOW_UNITS           100

/**
 * @brief Scan interval duration (BLE units)
 *
 * BLE units = 0.625ms each
 * 200 units = 125ms
 */
#define BLE_SCAN_INTERVAL_UNITS         200

// ============================================================================
// BLE TIMING (for status logging)
// ============================================================================

/**
 * @brief Advertising status log interval (ms)
 *
 * Log advertising status every 60 seconds.
 */
#define BLE_ADV_LOG_INTERVAL_MS         60000

/**
 * @brief Connected status log interval (ms)
 *
 * Log connection status every 5 seconds.
 */
#define BLE_CONN_LOG_INTERVAL_MS        5000

/**
 * @brief Minute boundary tolerance (ms)
 *
 * Window for minute-aligned logging (within 200ms of minute boundary).
 */
#define BLE_MINUTE_BOUNDARY_TOLERANCE_MS    200

/**
 * @brief 5-second boundary tolerance (ms)
 *
 * Window for 5-second aligned logging (within 600ms of boundary).
 */
#define BLE_5SEC_BOUNDARY_TOLERANCE_MS  600

// ============================================================================
// SERVICE DATA ADVERTISING
// ============================================================================

/**
 * @brief Battery Service UUID (16-bit)
 *
 * Standard Bluetooth Battery Service UUID for advertising battery level.
 * 0x180F
 */
#define BLE_BATTERY_SERVICE_UUID_16     0x180F

#ifdef __cplusplus
}
#endif

#endif // BLE_CONFIG_H
