/**
 * @file utlp_hal_mock.h
 * @brief HAL Mock API for Test Control
 *
 * Provides functions to control mock behavior during unit tests.
 */

#pragma once

#include "utlp_hal.h"
#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/*============================================================================
 * TIME CONTROL
 *==========================================================================*/

/**
 * @brief Advance mock time by given microseconds
 * @param delta_us Time to advance in microseconds
 */
void mock_advance_time_us(uint64_t delta_us);

/**
 * @brief Set mock time to specific value
 * @param time_us Absolute time in microseconds
 */
void mock_set_time_us(uint64_t time_us);

/*============================================================================
 * NETWORK CONTROL
 *==========================================================================*/

/**
 * @brief Set mock MAC address
 * @param mac 6-byte MAC address
 */
void mock_set_mac(const uint8_t *mac);

/**
 * @brief Inject a packet into the RX queue (simulates receiving)
 * @param packet Packet to inject
 * @return true if injected, false if queue full
 */
bool mock_inject_rx_packet(const utlp_packet_t *packet);

/*============================================================================
 * ACTUATOR VERIFICATION
 *==========================================================================*/

/**
 * @brief Get actuator state for test verification
 * @param channel Actuator channel (0-3)
 * @param freq Output: frequency in Hz (NULL to skip)
 * @param phase Output: phase in degrees (NULL to skip)
 * @param duty Output: duty cycle percent (NULL to skip)
 * @param active Output: whether actuator is active (NULL to skip)
 */
void mock_get_actuator_state(int channel, uint32_t *freq, float *phase,
                              float *duty, bool *active);

/*============================================================================
 * LOG VERIFICATION
 *==========================================================================*/

/**
 * @brief Get last log message
 * @return Pointer to last log message string
 */
const char* mock_get_last_log(void);

/**
 * @brief Get total log count since last reset
 * @return Number of log messages
 */
int mock_get_log_count(void);

/*============================================================================
 * STATE MANAGEMENT
 *==========================================================================*/

/**
 * @brief Reset all mock state to initial values
 */
void mock_reset(void);

#ifdef __cplusplus
}
#endif
