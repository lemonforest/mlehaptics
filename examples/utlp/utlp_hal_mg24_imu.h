/**
 * @file utlp_hal_mg24_imu.h
 * @brief UTLP IMU HAL Header for Silicon Labs MG24 with LSM6DS3
 *
 * @section overview Overview
 *
 * Header for MG24's onboard LSM6DS3 6-axis IMU. Implements the yield-pattern
 * interface (Claim 114) for RFIP positioning.
 *
 * @section usage Usage
 *
 * ```c
 * // Initialize IMU
 * if (!utlp_imu_init()) {
 *     LOG_ERR("IMU init failed");
 * }
 *
 * // Register callback with RFIP (Claim 114: Yield Pattern)
 * rfip_imu_register_callback(utlp_imu_get_state_callback);
 *
 * // In main loop (104 Hz):
 * while (1) {
 *     utlp_imu_update();  // Run Madgwick filter
 *     k_msleep(10);       // ~100 Hz
 * }
 * ```
 *
 * @see docs/UTLP_Technical_Supplement_S2.md - Section 8.28 (Claims 114-120)
 *
 * @version 1.0.0
 * @date 2026-01-03
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#pragma once

#include "rfip_hal.h"
#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/*============================================================================
 * PUBLIC API
 *==========================================================================*/

/**
 * @brief Initialize LSM6DS3 IMU
 *
 * Configures the IMU for 104 Hz sampling with ±4g accelerometer
 * and ±500 dps gyroscope ranges.
 *
 * @return true if successful, false on error
 */
bool utlp_imu_init(void);

/**
 * @brief Sample IMU and update fusion filter
 *
 * Call this at the configured ODR (104 Hz) from the main loop or
 * a dedicated IMU task. Updates the Madgwick AHRS filter and
 * motion confidence calculation.
 *
 * @code
 * // Example: IMU task running at 100 Hz
 * void imu_task(void *arg) {
 *     while (1) {
 *         utlp_imu_update();
 *         k_msleep(10);
 *     }
 * }
 * @endcode
 */
void utlp_imu_update(void);

/**
 * @brief IMU state callback for RFIP (Claim 114: Yield Pattern)
 *
 * This callback is registered with rfip_imu_register_callback().
 * RFIP calls it when it needs current IMU state for positioning.
 *
 * The yield pattern inverts traditional sensor fusion: the application
 * owns the IMU hardware and runs its own fusion filter. The protocol
 * layer (RFIP) only requests derived state when needed.
 *
 * @param[out] state IMU state structure to fill
 * @return true if state is valid, false if IMU unavailable
 *
 * @code
 * // Register with RFIP
 * rfip_imu_register_callback(utlp_imu_get_state_callback);
 * @endcode
 */
bool utlp_imu_get_state_callback(rfip_imu_state_t *state);

/**
 * @brief Check if IMU is initialized
 *
 * @return true if IMU is initialized and operational
 */
bool utlp_imu_is_initialized(void);

/**
 * @brief Get current motion confidence
 *
 * Returns 0-255 motion confidence based on recent acceleration variance.
 * 0 = stationary, 255 = high motion.
 *
 * This value is also available via utlp_imu_get_state_callback() in
 * the motion_confidence field.
 *
 * @return Motion confidence 0-255
 */
uint8_t utlp_imu_get_motion_confidence(void);

#ifdef __cplusplus
}
#endif
