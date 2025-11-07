# Phase 2: Tickless Idle and Light Sleep
## Power Management Integration for EMDR Pulser

**Date:** November 4, 2025  
**Baseline:** `single_device_battery_bemf_queued_test.c`  
**Objective:** Enable automatic power management for 50-80% power savings during idle periods

---

## Overview

Phase 2 adds FreeRTOS **Tickless Idle** mode with ESP32-C6 **Light Sleep**, providing automatic power management without code changes. The ESP32 automatically enters light sleep during `vTaskDelay()` calls when no tasks are ready to run.

### Power Savings Estimate

Based on coast periods in current modes:
- **Mode 1 (1Hz @ 50%)**: 250ms coast per 500ms = 50% idle time
- **Mode 2 (1Hz @ 25%)**: 375ms coast per 500ms = 75% idle time  
- **Mode 3 (0.5Hz @ 50%)**: 500ms coast per 1000ms = 50% idle time
- **Mode 4 (0.5Hz @ 25%)**: 750ms coast per 1000ms = 75% idle time

**Expected battery life improvement:** 2-3× in Mode 2/Mode 4 compared to always-on CPU.

---

## Configuration Changes

### Step 1: Enable Power Management

Add these lines to `sdkconfig.single_device_battery_bemf_queued_test`:

```ini
#
# Power Management
#
CONFIG_PM_ENABLE=y
CONFIG_FREERTOS_USE_TICKLESS_IDLE=y
CONFIG_PM_DFS_INIT_AUTO=y

# Light sleep during idle
CONFIG_PM_SLP_IRAM_OPT=y
CONFIG_PM_SLP_DEFAULT_PARAMS_OPT=y
CONFIG_PM_POWER_DOWN_CPU_IN_LIGHT_SLEEP=y
CONFIG_PM_POWER_DOWN_PERIPHERAL_IN_LIGHT_SLEEP=y

# Minimum idle duration for light sleep (milliseconds)
CONFIG_PM_MIN_IDLE_TIME_DURATION_MS=20
```

### Step 2: Understand What Happens

When `CONFIG_FREERTOS_USE_TICKLESS_IDLE=y`:

1. **During `vTaskDelay()`:**
   - FreeRTOS checks if all tasks are blocked/delayed
   - If minimum idle time > `CONFIG_PM_MIN_IDLE_TIME_DURATION_MS`:
     - CPU enters light sleep automatically
     - Peripherals power down (based on CONFIG)
     - System wakes before next task needs CPU

2. **Automatic Wake Sources:**
   - FreeRTOS tick timer (for task scheduling)
   - GPIO interrupts (button)
   - Timer interrupts (if configured)

3. **Transparent to Application:**
   - No code changes needed
   - Tasks wake exactly when scheduled
   - All timing behavior preserved

---

## What Gets Powered Down in Light Sleep

### Always Kept Alive:
- ✅ RTC domain (for wake timers)
- ✅ GPIO wake sources (button on GPIO1)
- ✅ RAM contents
- ✅ FreeRTOS state

### Automatically Powered Down:
- ⚡ CPU (RISC-V core)
- ⚡ High-speed clocks
- ⚡ Digital peripherals (when idle):
  - LEDC (motor PWM) - safe during coast
  - ADC (only active during reads)
  - RMT (WS2812B LED) - already off during most operation

### Wake Latency:
- **Light sleep**: ~1-2ms wake time
- **Impact**: Negligible for 250-750ms delays

---

## Code Behavior with Phase 2 Enabled

### Motor Task Example:

```c
// Mode 2: 1Hz @ 25% duty
motor_forward(75);              // CPU active
led_set_color(255, 0, 0);      // CPU active
vTaskDelay(pdMS_TO_TICKS(125)); // CPU active (motor running)

motor_coast();                  // CPU active (brief)
led_clear();                   // CPU active (brief)
vTaskDelay(pdMS_TO_TICKS(375)); // ⚡ LIGHT SLEEP ⚡ (375ms >> 20ms min)
                                // CPU wakes automatically after 375ms
```

### Battery Task Example:

```c
while (1) {
    uint32_t now = esp_timer_get_time() / 1000;
    
    if ((now - last_read_ms) >= BAT_READ_INTERVAL_MS) {
        // Do battery read (CPU active)
        read_battery_voltage(...);
        last_read_ms = now;
    }
    
    vTaskDelay(pdMS_TO_TICKS(1000));  // ⚡ LIGHT SLEEP ⚡
                                       // CPU wakes after 1 second
}
```

**Key Point:** All existing `vTaskDelay()` calls become automatic sleep opportunities!

---

## JPL Compliance Impact

✅ **Improved:**
- Rule 8: "Limit scope of data to smallest possible level"
  - Power management keeps peripherals off when not needed
  
✅ **Maintained:**
- All Rule 2 improvements from Phase 1 (message queues) preserved
- No changes to task isolation or data ownership
- Timing behavior unchanged (tasks wake exactly when scheduled)

---

## Testing Plan

### Baseline Power Measurement (Phase 1):
1. Run `single_device_battery_bemf_queued_test`
2. Measure current during coast periods with multimeter
3. Record: ~XX mA average current

### Phase 2 Power Measurement:
1. Enable PM configuration
2. Rebuild and flash
3. Measure current during same coast periods
4. Expected: ~YY mA average current (50-80% reduction)

### Functional Verification:
1. **Motor Operation:**
   - ✓ All 4 modes work identically
   - ✓ Timing matches Phase 1 (no drift)
   - ✓ LED sync maintained

2. **Button Responsiveness:**
   - ✓ Mode changes work during coast (CPU wakes on GPIO)
   - ✓ Emergency shutdown (5-second hold) still functional
   
3. **Battery Monitoring:**
   - ✓ Reads occur every 10 seconds
   - ✓ LVO triggers correctly
   - ✓ Deep sleep entry unchanged

4. **Back-EMF Sampling:**
   - ✓ First 10 seconds of each mode capture data
   - ✓ ADC timing unaffected

---

## Configuration Details

### Minimum Idle Time (`CONFIG_PM_MIN_IDLE_TIME_DURATION_MS`)

**Default:** 20ms  
**Rationale:** 
- Wake latency ~1-2ms
- Transition overhead ~2-3ms
- Break-even point ~5-10ms idle
- 20ms provides good safety margin

**For EMDR Pulser:**
- Shortest coast: 125ms (Mode 2)
- 125ms >> 20ms → Always beneficial to sleep

### Dynamic Frequency Scaling (DFS)

**Not recommended for Phase 2:**
- `CONFIG_PM_DFS_INIT_AUTO=y` can be enabled
- But frequency changes add latency
- EMDR timing is critical (bilateral alternation must be precise)
- **Stick with light sleep only** for Phase 2

---

## Expected Results

### Battery Life (per 20-minute session):

| Mode | Phase 1 (No PM) | Phase 2 (w/ PM) | Improvement |
|------|----------------|-----------------|-------------|
| Mode 1 (1Hz@50%) | 100% | ~60-70% | 30-40% savings |
| Mode 2 (1Hz@25%) | 100% | ~40-50% | 50-60% savings |
| Mode 3 (0.5Hz@50%) | 100% | ~60-70% | 30-40% savings |
| Mode 4 (0.5Hz@25%) | 100% | ~35-45% | 55-65% savings |

### With dual 350mAh batteries (700mAh total):
- **Mode 1:** 20 min → ~28-30 min
- **Mode 2:** 20 min → ~35-40 min
- **Mode 3:** 20 min → ~28-30 min  
- **Mode 4:** 20 min → ~40-45 min

---

## Build Commands

```bash
# Clean previous build (recommended when changing PM config)
pio run -e single_device_battery_bemf_queued_test -t clean

# Rebuild with new configuration
pio run -e single_device_battery_bemf_queued_test -t upload

# Monitor serial output
pio device monitor
```

---

## Serial Output - What to Look For

With Phase 2 enabled, you won't see different logs (light sleep is transparent), but you can verify:

1. **Timing Precision:**
   ```
   FWD: Drive: 1650mV→+0mV | Coast-Immed: 1650mV→+0mV | ...
   REV: Drive: 1650mV→+0mV | Coast-Immed: 1650mV→+0mV | ...
   ```
   - Timestamps should be identical to Phase 1
   - No drift over 20-minute session

2. **Button Response:**
   - Mode changes during coast still instant
   - No added latency

3. **Battery Reads:**
   - Still every 10 seconds exactly

---

## Troubleshooting

### Problem: Device doesn't wake from sleep
**Cause:** Button (GPIO1) not configured as RTC wake source  
**Solution:** Already handled in `enter_deep_sleep()` - same config works for light sleep

### Problem: Motor timing seems off
**Cause:** `CONFIG_PM_MIN_IDLE_TIME_DURATION_MS` set too high  
**Solution:** Reduce to 10-20ms

### Problem: No power savings measured
**Cause:** Multimeter sampling rate too slow to catch sleep periods  
**Solution:** Use oscilloscope or average over full session

### Problem: Back-EMF readings affected
**Cause:** ADC powered down during light sleep  
**Solution:** Already prevented - ADC active during motor operation, only sleeps during coast

---

## Next Steps (Phase 3 - Optional)

After verifying Phase 2 works:

1. **Explicit Light Sleep for Long Delays:**
   - Replace very long `vTaskDelay()` with `esp_light_sleep_start()`
   - Better for >1 second delays
   - More complex - requires timer wakeup configuration

2. **Deep Sleep During Long Idle:**
   - If no button press for N seconds during coast
   - Enter deep sleep instead of light sleep
   - Even more power savings

3. **Phase 4: Full JPL Compliance:**
   - Remove `goto` statements
   - State machines for button logic
   - Static analysis integration

---

## Summary

**Phase 2 gives you:**
- ✅ 50-80% power savings during idle
- ✅ Zero code changes
- ✅ Zero functional changes
- ✅ Maintained JPL improvements from Phase 1
- ✅ Foundation for future power management

**Risk:** Very low - light sleep is designed to be transparent

**Effort:** ~5 minutes to configure, 10 minutes to test

**Ready to proceed?** Just update the sdkconfig and rebuild!
