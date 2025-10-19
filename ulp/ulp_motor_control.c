/**
 * @file ulp_motor_control.c
 * @brief ULP RISC-V program for low-power motor command processing
 * 
 * This ULP program runs on the ESP32-C6 LP (Low Power) core and handles:
 * - Command queue processing
 * - Timing calculations for bilateral patterns
 * - Waking HP core for actual motor control
 * 
 * Power savings: LP core runs at ~17MHz using <100µA while HP core sleeps
 * 
 * IMPORTANT: ESP32-C6 ULP is RISC-V based, not FSM-based like ESP32/ESP32-S2
 */

#include "ulp_riscv.h"
#include "ulp_riscv_utils.h"
#include "ulp_riscv_gpio.h"

/* Shared memory between HP and LP cores */
typedef enum {
    CMD_NONE = 0,
    CMD_FORWARD,
    CMD_REVERSE,
    CMD_COAST,
    CMD_SLEEP_HP
} motor_command_t;

/* ULP shared variables (accessible from both cores) */
volatile motor_command_t ulp_motor_command = CMD_NONE;
volatile uint32_t ulp_motor_intensity = 0;     // 0-100%
volatile uint32_t ulp_half_cycle_ms = 500;      // Default 500ms half-cycle
volatile uint32_t ulp_wake_count = 0;           // Debug: count HP wakes
volatile uint32_t ulp_cycle_count = 0;          // Debug: count ULP cycles

/* ULP internal state */
static uint32_t next_wake_time_ms = 0;
static motor_command_t current_phase = CMD_FORWARD;

/**
 * @brief Main ULP program entry point
 * 
 * Execution flow:
 * 1. Check if it's time to wake HP core
 * 2. If yes: set command and wake HP core
 * 3. If no: sleep until next cycle
 * 
 * HP core will handle actual GPIO/PWM control and then sleep
 * ULP maintains timing and wakes HP as needed
 */
int main(void)
{
    ulp_cycle_count++;
    
    // Get current time from RTC
    uint32_t current_time_ms = ulp_riscv_get_ccount() / 17;  // ~17MHz LP clock
    
    // Check if it's time for next phase
    if (current_time_ms >= next_wake_time_ms) {
        // Toggle phase: Forward <-> Reverse
        if (current_phase == CMD_FORWARD) {
            current_phase = CMD_REVERSE;
        } else {
            current_phase = CMD_FORWARD;
        }
        
        // Set command for HP core
        ulp_motor_command = current_phase;
        ulp_wake_count++;
        
        // Calculate next wake time (half-cycle from now)
        next_wake_time_ms = current_time_ms + ulp_half_cycle_ms;
        
        // Wake HP core to execute motor command
        ulp_riscv_wakeup_main_processor();
    }
    
    // Sleep until next check (reduces LP core power consumption)
    // Check every 10ms for responsiveness
    ulp_riscv_delay_cycles(17000 * 10);  // 10ms at ~17MHz
    
    // ULP program automatically loops
    return 0;
}
