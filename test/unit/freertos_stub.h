/**
 * @file freertos_stub.h
 * @brief FreeRTOS Stubs for Host Testing
 *
 * Provides minimal FreeRTOS API stubs so UTLP code compiles on host.
 * These stubs are NOT functional - they just prevent linker errors.
 */

#pragma once

#include <stdint.h>
#include <stdlib.h>

/*============================================================================
 * FREERTOS TYPE STUBS
 *==========================================================================*/

typedef void* TaskHandle_t;
typedef uint32_t TickType_t;
typedef long BaseType_t;
typedef unsigned long UBaseType_t;

#define pdMS_TO_TICKS(ms) ((TickType_t)((ms) * 1))
#define pdTRUE  1
#define pdFALSE 0
#define pdPASS  pdTRUE

/*============================================================================
 * FREERTOS FUNCTION STUBS
 *==========================================================================*/

static inline void vTaskDelay(TickType_t ticks) {
    (void)ticks;
    /* No-op in host tests */
}

static inline void vTaskDelete(TaskHandle_t task) {
    (void)task;
    /* No-op - in real code this would delete the calling task */
}

static inline BaseType_t xTaskCreate(
    void (*taskCode)(void*),
    const char *name,
    uint32_t stackDepth,
    void *params,
    UBaseType_t priority,
    TaskHandle_t *taskHandle
) {
    (void)taskCode;
    (void)name;
    (void)stackDepth;
    (void)params;
    (void)priority;
    (void)taskHandle;
    /* In host tests, we don't actually create tasks */
    return pdPASS;
}

/*============================================================================
 * FREERTOS PATH REDIRECT
 *
 * The actual code includes "freertos/FreeRTOS.h" and "freertos/task.h".
 * We create stub headers at those paths.
 *==========================================================================*/
