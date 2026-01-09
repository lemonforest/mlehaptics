/***************************************************************************//**
 * @file
 * @brief
 *******************************************************************************
 * # License
 * <b>Copyright 2024 Silicon Laboratories Inc. www.silabs.com</b>
 *******************************************************************************
 *
 * SPDX-License-Identifier: Zlib
 *
 * The licensor of this software is Silicon Laboratories Inc.
 *
 * This software is provided 'as-is', without any express or implied
 * warranty. In no event will the authors be held liable for any damages
 * arising from the use of this software.
 *
 * Permission is granted to anyone to use this software for any purpose,
 * including commercial applications, and to alter it and redistribute it
 * freely, subject to the following restrictions:
 *
 * 1. The origin of this software must not be misrepresented; you must not
 *    claim that you wrote the original software. If you use this software
 *    in a product, an acknowledgment in the product documentation would be
 *    appreciated but is not required.
 * 2. Altered source versions must be plainly marked as such, and must not be
 *    misrepresented as being the original software.
 * 3. This notice may not be removed or altered from any source distribution.
 *
 ******************************************************************************/
#include <inttypes.h>
#include "sl_rail.h"
#include "sl_rail_ble.h" // for sl_rail_ble_state_t
#include "sli_rail_util_callbacks.h" // for internal-only callback signatures
#include "sl_rail_util_init.h"
#include "sl_rail_util_protocol.h"
#if defined(SL_COMPONENT_CATALOG_PRESENT)
#include "sl_component_catalog.h"
#endif

#if defined(SL_CATALOG_TIMING_TEST_PRESENT) && !SL_RAIL_LIB_MULTIPROTOCOL_SUPPORT
// Needed for measuring sl_rail_init() time as a part of
// detailed timing characterization.
#include "em_device.h"
#if defined(_SILICON_LABS_32B_SERIES_2)
#include "em_timer.h"
#else
#include "sl_hal_timer.h"
#endif // defined(_SILICON_LABS_32B_SERIES_2)

#if defined(SL_CATALOG_CLOCK_MANAGER_PRESENT)
#include "sl_clock_manager.h"
#else
#include "em_cmu.h"
#endif //defined(SL_CATALOG_CLOCK_MANAGER_PRESENT)
#endif //defined(SL_CATALOG_TIMING_TEST_PRESENT) && !SL_RAIL_LIB_MULTIPROTOCOL_SUPPORT

#ifdef SL_CATALOG_APP_ASSERT_PRESENT
#include "app_assert.h"
#define APP_ASSERT(expr, ...) app_assert(expr,__VA_ARGS__)
#else
#define APP_ASSERT(expr, ...) \
  do {                        \
    if (!(expr)) {            \
      while (1) ;             \
    }                         \
  } while (0)
#endif

#if 0U \
  || SL_RAIL_UTIL_INIT_RADIO_CONFIG_SUPPORT_INST0_ENABLE \
  || 0U
  #include "rail_config.h"
#endif

// Instance: inst0
static sl_rail_handle_t sli_rail_handle_inst0 = SL_RAIL_EFR32_HANDLE;

#if SL_RAIL_UTIL_INIT_INST0_ENABLE
#if     (SL_RAIL_UTIL_INIT_RX_PACKET_QUEUE_INST0_ENTRIES > 0)
static sl_rail_packet_queue_entry_t sli_rail_rx_packet_queue_inst0[SL_RAIL_UTIL_INIT_RX_PACKET_QUEUE_INST0_ENTRIES];
#endif
#if     (SL_RAIL_UTIL_INIT_RX_FIFO_INST0_BYTES > 0)
static SL_RAIL_DECLARE_FIFO_BUFFER(sli_rx_fifo_buffer_inst0, SL_RAIL_UTIL_INIT_RX_FIFO_INST0_BYTES);
#endif
#if     (SL_RAIL_UTIL_INIT_TX_FIFO_INST0_BYTES > 0)
static SL_RAIL_DECLARE_FIFO_BUFFER(sli_tx_fifo_buffer_inst0, SL_RAIL_UTIL_INIT_TX_FIFO_INST0_BYTES);
#endif
#endif // SL_RAIL_UTIL_INIT_INST0_ENABLE

#if defined(SL_CATALOG_TIMING_TEST_PRESENT) && !SL_RAIL_LIB_MULTIPROTOCOL_SUPPORT
uint32_t sli_timing_start_tick = 0U;
uint32_t sli_timing_end_tick = 0U;
static TIMER_TypeDef *timer = TIMER0;
static void setupTimingTestTimer(void)
{
// Clock TIMER0 using the HF clock
#ifndef SL_CATALOG_CLOCK_MANAGER_PRESENT
  CMU_CLOCK_SELECT_SET(TIMER0, HFXO);
  CMU_ClockEnable(cmuClock_TIMER0, true);
  // Use default configuration, prescaled by 8.
  TIMER_Init_TypeDef timerCfg = TIMER_INIT_DEFAULT;
  timerCfg.prescale = timerPrescale8;
  // Enable TIMER0 to upcount
  TIMER_Init(timer, &timerCfg);
#else
  sl_clock_manager_enable_bus_clock(SL_BUS_CLOCK_TIMER0);
  sl_hal_timer_config_t timerCfg = SL_HAL_TIMER_CONFIG_DEFAULT;
  // Use default configuration, prescaled by 8.
  timerCfg.prescaler = TIMER_CFG_PRESC_DIV8;
   // Enable TIMER0 to upcount
  sl_hal_timer_init(timer, &timerCfg);
#endif //SL_CATALOG_CLOCK_MANAGER_PRESENT
}
#endif

static void sl_rail_util_init_inst0(void)
{
#if SL_RAIL_UTIL_INIT_INST0_ENABLE
  sl_rail_status_t status;
  sl_rail_config_t rail_init_config = {
    .events_callback = &sli_rail_util_on_event,
#if     (SL_RAIL_UTIL_INIT_RX_PACKET_QUEUE_INST0_ENTRIES < 0)
    .rx_packet_queue_entries = sl_rail_builtin_rx_packet_queue_entries,
    .p_rx_packet_queue = sl_rail_builtin_rx_packet_queue_ptr,
#elif (SL_RAIL_UTIL_INIT_RX_PACKET_QUEUE_INST0_ENTRIES > 0)
    .rx_packet_queue_entries = SL_RAIL_UTIL_INIT_RX_PACKET_QUEUE_INST0_ENTRIES,
    .p_rx_packet_queue = sli_rail_rx_packet_queue_inst0,
#else
    // .rx_packet_queue_entries = 0U,
    // .p_rx_packet_queue = NULL,
#endif
#if     (SL_RAIL_UTIL_INIT_RX_FIFO_INST0_BYTES < 0)
    .rx_fifo_bytes = sl_rail_builtin_rx_fifo_bytes,
    .p_rx_fifo_buffer = sl_rail_builtin_rx_fifo_ptr,
#elif (SL_RAIL_UTIL_INIT_RX_FIFO_INST0_BYTES > 0)
    .rx_fifo_bytes = SL_RAIL_UTIL_INIT_RX_FIFO_INST0_BYTES,
    .p_rx_fifo_buffer = sli_rx_fifo_buffer_inst0,
#else
    // .rx_fifo_bytes = 0U,
    // .p_rx_fifo_buffer = NULL,
#endif
    .tx_fifo_bytes = SL_RAIL_UTIL_INIT_TX_FIFO_INST0_BYTES,
    .tx_fifo_init_bytes = 0U,
#if     (SL_RAIL_UTIL_INIT_TX_FIFO_INST0_BYTES > 0)
    .p_tx_fifo_buffer = sli_tx_fifo_buffer_inst0,
#else
    // .p_tx_fifo_buffer = NULL,
#endif
  };

  (void) status; // Suppress compiler warning if status ends up unused
#ifdef SL_CATALOG_TIMING_TEST_PRESENT
  setupTimingTestTimer();
  sli_timing_start_tick = timer->CNT;
#endif // SL_CATALOG_TIMING_TEST_PRESENT

  status = sl_rail_init(&sli_rail_handle_inst0,
                        &rail_init_config,
#if SL_RAIL_UTIL_INIT_INIT_COMPLETE_CALLBACK_INST0_ENABLE
                        &sli_rail_util_on_rf_ready
#else
                        NULL
#endif // SL_RAIL_UTIL_INIT_INIT_COMPLETE_CALLBACK_INST0_ENABLE
                        );
  APP_ASSERT((SL_RAIL_STATUS_NO_ERROR == status),
             "sl_rail_init failed, return value: 0x%04" PRIX32, status);
#ifdef SL_CATALOG_TIMING_TEST_PRESENT
  sli_timing_end_tick = timer->CNT;
#endif // SL_CATALOG_TIMING_TEST_PRESENT

#if SL_RAIL_UTIL_INIT_TX_DATA_FORMAT_INST0_ENABLE
  sl_rail_tx_data_config_t tx_data_config = {
    .tx_source = SL_RAIL_UTIL_INIT_TX_DATA_FORMAT_INST0_SOURCE,
    .tx_method = SL_RAIL_UTIL_INIT_TX_DATA_FORMAT_INST0_MODE,
  };
  status = sl_rail_config_tx_data(sli_rail_handle_inst0,
                                  &tx_data_config);
  APP_ASSERT((SL_RAIL_STATUS_NO_ERROR == status),
             "sl_rail_config_tx_data failed, return value: 0x%04" PRIX32,
             status);
#endif // SL_RAIL_UTIL_INIT_TX_DATA_FORMAT_INST0_ENABLE
#if SL_RAIL_UTIL_INIT_RX_DATA_FORMAT_INST0_ENABLE
  sl_rail_rx_data_config_t rx_data_config = {
    .rx_source = SL_RAIL_UTIL_INIT_RX_DATA_FORMAT_INST0_SOURCE,
    .rx_method = SL_RAIL_UTIL_INIT_RX_DATA_FORMAT_INST0_MODE,
  };
  status = sl_rail_config_rx_data(sli_rail_handle_inst0,
                                  &rx_data_config);
  APP_ASSERT((SL_RAIL_STATUS_NO_ERROR == status),
             "sl_rail_config_rx_data failed, return value: 0x%04" PRIX32,
             status);
#endif // SL_RAIL_UTIL_INIT_RX_DATA_FORMAT_INST0_ENABLE

#if SL_RAIL_UTIL_INIT_PROTOCOLS_INST0_ENABLE
  const sl_rail_channel_config_t *channel_config = NULL;
  if (SL_RAIL_UTIL_INIT_PROTOCOL_INST0_DEFAULT
      == SL_RAIL_UTIL_PROTOCOL_PROPRIETARY) {
#if SL_RAIL_UTIL_INIT_RADIO_CONFIG_SUPPORT_INST0_ENABLE
    channel_config = (const sl_rail_channel_config_t *)channelConfigs[SL_RAIL_UTIL_INIT_PROTOCOL_PROPRIETARY_INST0_INDEX];
#else // !SL_RAIL_UTIL_INIT_RADIO_CONFIG_SUPPORT_INST0_ENABLE
    APP_ASSERT(false,
               "SL_RAIL_UTIL_INIT_RADIO_CONFIG_SUPPORT_INST0_ENABLE must be true when (SL_RAIL_UTIL_INIT_PROTOCOL_INST0_DEFAULT == SL_RAIL_UTIL_PROTOCOL_PROPRIETARY)");
#endif // SL_RAIL_UTIL_INIT_RADIO_CONFIG_SUPPORT_INST0_ENABLE
  }
  status = sl_rail_config_channels(sli_rail_handle_inst0,
                                   channel_config,
                                   &sli_rail_util_on_channel_config_change);
  APP_ASSERT((SL_RAIL_STATUS_NO_ERROR == status),
             "sl_rail_config_channels failed, return value: 0x%04" PRIX32,
             status);
  if (channel_config != NULL) {
    // Establish first channel by default
    // Perhaps someday this will be parameterized in the init config
    uint16_t channel = sl_rail_get_first_channel(sli_rail_handle_inst0,
                                                 channel_config);
    if (channel != SL_RAIL_CHANNEL_INVALID) {
      status = sl_rail_prepare_channel(sli_rail_handle_inst0, channel);
      APP_ASSERT((SL_RAIL_STATUS_NO_ERROR == status),
                 "sl_rail_prepare_channel failed, return value: 0x%04" PRIX32,
                 status);
    }
  }
  status = sl_rail_util_protocol_config(sli_rail_handle_inst0,
                                        SL_RAIL_UTIL_INIT_PROTOCOL_INST0_DEFAULT);
  APP_ASSERT((SL_RAIL_STATUS_NO_ERROR == status),
             "sl_rail_util_protocol_config failed, return value: 0x%04" PRIX32,
             status);
#endif // SL_RAIL_UTIL_INIT_PROTOCOLS_INST0_ENABLE

#if SL_RAIL_UTIL_INIT_CALIBRATIONS_INST0_ENABLE
  status = sl_rail_config_cal(sli_rail_handle_inst0,
                              0U
                              | (SL_RAIL_UTIL_INIT_CALIBRATION_TEMPERATURE_NOTIFY_INST0_ENABLE
                                 ? SL_RAIL_CAL_TEMP : 0U)
                              | (SL_RAIL_UTIL_INIT_CALIBRATION_ONETIME_NOTIFY_INST0_ENABLE
                                 ? SL_RAIL_CAL_ONETIME : 0U));
  APP_ASSERT((SL_RAIL_STATUS_NO_ERROR == status),
             "sl_rail_config_cal failed, return value: 0x%04" PRIX32,
             status);
#endif // SL_RAIL_UTIL_INIT_CALIBRATIONS_INST0_ENABLE

#if SL_RAIL_UTIL_INIT_EVENTS_INST0_ENABLE
  status = sl_rail_config_events(sli_rail_handle_inst0,
                                 SL_RAIL_EVENTS_ALL,
                                 SL_RAIL_UTIL_INIT_EVENT_INST0_MASK);
  APP_ASSERT((SL_RAIL_STATUS_NO_ERROR == status),
             "sl_rail_config_events failed, return value: 0x%04" PRIX32,
             status);
#endif // SL_RAIL_UTIL_INIT_EVENTS_INST0_ENABLE

#if SL_RAIL_UTIL_INIT_TRANSITIONS_INST0_ENABLE
  sl_rail_state_transitions_t tx_transitions = {
    .success = SL_RAIL_UTIL_INIT_TRANSITION_INST0_TX_SUCCESS,
    .error = SL_RAIL_UTIL_INIT_TRANSITION_INST0_TX_ERROR
  };
  sl_rail_state_transitions_t rx_transitions = {
    .success = SL_RAIL_UTIL_INIT_TRANSITION_INST0_RX_SUCCESS,
    .error = SL_RAIL_UTIL_INIT_TRANSITION_INST0_RX_ERROR
  };
  status = sl_rail_set_tx_transitions(sli_rail_handle_inst0,
                                      &tx_transitions);
  APP_ASSERT((SL_RAIL_STATUS_NO_ERROR == status),
             "sl_rail_set_tx_transitions failed, return value: 0x%04" PRIX32,
             status);
  status = sl_rail_set_rx_transitions(sli_rail_handle_inst0,
                                      &rx_transitions);
  APP_ASSERT((SL_RAIL_STATUS_NO_ERROR == status),
             "sl_rail_set_rx_transitions failed, return value: 0x%04" PRIX32,
             status);
#endif // SL_RAIL_UTIL_INIT_TRANSITIONS_INST0_ENABLE
#else // !SL_RAIL_UTIL_INIT_INST0_ENABLE
  // Eliminate compiler warnings.
  (void) sli_rail_handle_inst0;
#endif // SL_RAIL_UTIL_INIT_INST0_ENABLE
}

sl_rail_handle_t sl_rail_util_get_handle(sl_rail_util_handle_type_t handle)
{
  sl_rail_handle_t *sli_rail_handle_array[] = {
    &sli_rail_handle_inst0,
  };
  return *sli_rail_handle_array[handle];
}

#define INIT_INSTANCES (0 + 1)

#if (INIT_INSTANCES > 1) && !SL_RAIL_LIB_MULTIPROTOCOL_SUPPORT
  #error "sl_rail_util_init.c: If you are going to use more than one sl_rail_util_init instance, you must use the Multiprotocol RAIL library."
#elif (INIT_INSTANCES > 4)
  static uint64_t sli_extra_state_buffers[INIT_INSTANCES - 4][SL_RAIL_STATE_BUFFER_BYTES / sizeof(uint64_t)];
  static sl_rail_state_buffer_entry_t sli_extra_protos[INIT_INSTANCES - 4];
#else
  // RAIL provides enough built-in state buffers for all the instances
#endif

void sl_rail_util_init(void)
{
#if   (INIT_INSTANCES > 2)
  sl_rail_status_t status;
  status = sl_rail_add_state_buffer_3(SL_RAIL_EFR32_HANDLE);
  APP_ASSERT((SL_RAIL_STATUS_NO_ERROR == status),
             "sl_rail_add_state_buffer_3 failed, return value: 0x%04" PRIX32,
             status);
#if   (INIT_INSTANCES > 3)
  status = sl_rail_add_state_buffer_4(SL_RAIL_EFR32_HANDLE);
  APP_ASSERT((SL_RAIL_STATUS_NO_ERROR == status),
             "sl_rail_add_state_buffer_4 failed, return value: 0x%04" PRIX32,
             status);
#endif
#if   (INIT_INSTANCES > 4)
  for (int i = 0; i < (INIT_INSTANCES - 4); i++) {
    sli_extra_protos[i].buffer_bytes = sizeof(sli_extra_state_buffers[0]);
    sli_extra_protos[i].p_buffer = sli_extra_state_buffers[i];
    status = sl_rail_add_state_buffer(SL_RAIL_EFR32_HANDLE, &sli_extra_protos[i]);
    APP_ASSERT((SL_RAIL_STATUS_NO_ERROR == status),
               "sl_rail_add_state_buffer(%d) failed, return value: 0x%04" PRIX32,
               (INIT_INSTANCES + i), status);
  }
#endif
#endif
  sl_rail_util_init_inst0();
}
