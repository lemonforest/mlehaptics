# Phase 3: Explicit Light Sleep Implementation
## Manual Sleep Control for Optimal Power Management

**Date:** November 4, 2025  
**Status:** Ready for Implementation  
**Baseline:** Phase 2 (Tickless Idle) - Complete and Working  
**Effort:** 2-4 hours (code changes + testing)

---

## Overview

Phase 3 replaces automatic tickless idle with **explicit light sleep** calls for maximum power efficiency. While Phase 2's automatic sleep is good, explicit sleep gives you:

- ✅ **Lower power consumption** (~2-5mA vs ~5-10mA in Phase 2)
- ✅ **Better control** over wake sources
- ✅ **Predictable behavior** (no FreeRTOS scheduler overhead)
- ✅ **Optimal for >1 second delays**

---

## Phase 2 vs Phase 3: Power Comparison

### Phase 2 (Automatic Tickless Idle):

```c
// Battery task - Phase 2
vTaskDelay(pdMS_TO_TICKS(1000));  // FreeRTOS automatically:
                                   // 1. Checks all tasks blocked
                                   // 2. Enters light sleep (~8-10mA)
                                   // 3. Wakes for button every 10ms
                                   // 4. FreeRTOS scheduler overhead
```

**Power during 1-second delay:**
- CPU sleep: 2mA
- FreeRTOS overhead: 1-2mA (periodic wake for scheduler)
- Button task wakes: 5mA × 100 wake events = 5mA average
- **Total: ~8-10mA**

### Phase 3 (Explicit Light Sleep):

```c
// Battery task - Phase 3
esp_sleep_enable_timer_wakeup(1000 * 1000);  // 1 second in µs
esp_sleep_enable_gpio_wakeup(
    (1ULL << GPIO_BUTTON),
    ESP_GPIO_WAKEUP_GPIO_LOW
);
esp_light_sleep_start();  // Explicit sleep:
                          // 1. CPU sleeps immediately
                          // 2. No FreeRTOS scheduler
                          // 3. Only wakes on timer OR button
                          // 4. Direct wake (no overhead)
```

**Power during 1-second delay:**
- CPU sleep: 2mA
- No scheduler overhead: 0mA
- GPIO wake circuit: <1mA
- **Total: ~2-3mA**

**Savings: 5-7mA (60-70% reduction for this specific delay)**

---

## Where Explicit Sleep Helps

### Good Candidates (Use Explicit Sleep):

1. **Battery monitoring delays (≥1 second)**
   - Current: `vTaskDelay(1000ms)` in battery task
   - Better: Explicit sleep with timer + GPIO wake
   - Savings: ~5-7mA

2. **Long idle periods (≥5 seconds)**
   - Example: User inactivity timeout
   - Explicit sleep much better than automatic
   - Savings: ~10-15mA

3. **Dedicated sleep tasks**
   - Task whose only job is to sleep and wake periodically
   - Explicit sleep is perfect
   - Savings: Maximum efficiency

### Poor Candidates (Keep Automatic):

1. **Motor timing delays (<1 second)**
   - Current: `vTaskDelay(125-750ms)` in motor task
   - Keep automatic: Too complex to manage wake sources
   - Reason: Motor needs precise timing, button must interrupt

2. **Button sampling (10ms)**
   - Current: `vTaskDelay(10ms)` in button task
   - Keep automatic: Too short to benefit
   - Reason: Wake overhead > power savings

3. **Multiple wake sources needed**
   - Tasks waiting on queues + timers
   - Automatic tickless idle handles this better
   - Reason: Explicit sleep requires manual coordination

---

## Implementation Strategy

### File Structure:

```
single_device_battery_bemf_queued_test.c     ← Phase 2 (baseline)
single_device_battery_bemf_explicit_test.c   ← Phase 3 (new file)
```

**Preserve Phase 2 baseline, create new Phase 3 implementation.**

### Changes Summary:

1. **Battery Task:** Replace `vTaskDelay()` with explicit sleep
2. **Motor Task:** Keep automatic (too complex for explicit)
3. **Button Task:** Keep automatic (too short for explicit)
4. **Wake Sources:** Configure timer + GPIO for battery task

---

## Code Changes

### Battery Task - Phase 2 (Current):

```c
static void battery_task(void *pvParameters) {
    uint32_t last_read_ms = (uint32_t)(esp_timer_get_time() / 1000);
    
    ESP_LOGI(TAG, "Battery task started");
    
    while (1) {
        uint32_t now = (uint32_t)(esp_timer_get_time() / 1000);
        
        if ((now - last_read_ms) >= BAT_READ_INTERVAL_MS) {
            int raw_mv = 0;
            float battery_v = 0.0f;
            int percentage = 0;
            
            if (read_battery_voltage(&raw_mv, &battery_v, &percentage) == ESP_OK) {
                ESP_LOGI(TAG, "Battery: %.2fV [%d%%]", battery_v, percentage);
                
                if (battery_v < LVO_WARNING_VOLTAGE) {
                    task_message_t msg = {
                        .type = MSG_BATTERY_CRITICAL,
                        .data.battery = {.voltage = battery_v, .percentage = percentage}
                    };
                    xQueueSend(battery_to_motor_queue, &msg, pdMS_TO_TICKS(100));
                } else if (battery_v < LVO_CUTOFF_VOLTAGE) {
                    low_battery_warning();
                    task_message_t msg = {
                        .type = MSG_BATTERY_WARNING,
                        .data.battery = {.voltage = battery_v, .percentage = percentage}
                    };
                    xQueueSend(battery_to_motor_queue, &msg, pdMS_TO_TICKS(100));
                }
            }
            last_read_ms = now;
        }
        
        vTaskDelay(pdMS_TO_TICKS(1000));  // ← Automatic tickless idle (~8-10mA)
    }
}
```

### Battery Task - Phase 3 (Explicit Sleep):

```c
// New helper function for explicit light sleep
static void battery_light_sleep(uint32_t duration_ms) {
    // Configure timer wakeup
    esp_sleep_enable_timer_wakeup(duration_ms * 1000);  // Convert ms to µs
    
    // Configure GPIO wakeup (button can still wake us)
    gpio_wakeup_enable(GPIO_BUTTON, GPIO_INTR_LOW_LEVEL);
    esp_sleep_enable_gpio_wakeup();
    
    // Enter light sleep
    esp_light_sleep_start();
    
    // Disable GPIO wakeup (clean up)
    esp_sleep_disable_wakeup_source(ESP_SLEEP_WAKEUP_GPIO);
    gpio_wakeup_disable(GPIO_BUTTON);
}

static void battery_task(void *pvParameters) {
    uint32_t last_read_ms = (uint32_t)(esp_timer_get_time() / 1000);
    
    ESP_LOGI(TAG, "Battery task started (Phase 3: Explicit light sleep)");
    
    while (1) {
        uint32_t now = (uint32_t)(esp_timer_get_time() / 1000);
        
        if ((now - last_read_ms) >= BAT_READ_INTERVAL_MS) {
            int raw_mv = 0;
            float battery_v = 0.0f;
            int percentage = 0;
            
            if (read_battery_voltage(&raw_mv, &battery_v, &percentage) == ESP_OK) {
                ESP_LOGI(TAG, "Battery: %.2fV [%d%%]", battery_v, percentage);
                
                if (battery_v < LVO_WARNING_VOLTAGE) {
                    task_message_t msg = {
                        .type = MSG_BATTERY_CRITICAL,
                        .data.battery = {.voltage = battery_v, .percentage = percentage}
                    };
                    xQueueSend(battery_to_motor_queue, &msg, pdMS_TO_TICKS(100));
                } else if (battery_v < LVO_CUTOFF_VOLTAGE) {
                    low_battery_warning();
                    task_message_t msg = {
                        .type = MSG_BATTERY_WARNING,
                        .data.battery = {.voltage = battery_v, .percentage = percentage}
                    };
                    xQueueSend(battery_to_motor_queue, &msg, pdMS_TO_TICKS(100));
                }
            }
            last_read_ms = now;
        }
        
        // Phase 3: Explicit light sleep (~2-3mA)
        battery_light_sleep(1000);
        
        // Check why we woke up
        esp_sleep_wakeup_cause_t cause = esp_sleep_get_wakeup_cause();
        if (cause == ESP_SLEEP_WAKEUP_GPIO) {
            ESP_LOGI(TAG, "Battery task: Woke on button press");
            // Button was pressed during sleep - continue normally
        }
        // If timer wakeup, just continue to next iteration
    }
}
```

---

## Configuration Changes

### sdkconfig Modifications:

```ini
# Phase 3: Explicit light sleep configuration
# Keep Phase 2 PM enabled (still needed for motor/button tasks)
CONFIG_PM_ENABLE=y
CONFIG_FREERTOS_USE_TICKLESS_IDLE=y

# Additional Phase 3 settings
CONFIG_ESP_SLEEP_GPIO_RESET_WORKAROUND=y      # ESP32-C6 GPIO wake fix
CONFIG_ESP_SLEEP_FLASH_LEAKAGE_WORKAROUND=y   # Reduce flash leakage
CONFIG_ESP_SLEEP_DEEP_SLEEP_WAKEUP_DELAY=2000 # Wake delay (µs)

# Light sleep optimizations
CONFIG_PM_LIGHT_SLEEP_CALLBACKS=y             # Sleep entry/exit callbacks
CONFIG_PM_POWER_DOWN_PERIPHERAL_IN_LIGHT_SLEEP=y
```

---

## Power Budget Comparison

### Phase 2 (Automatic) - Mode 2:

| Period | Duration | Current | Avg Power |
|--------|----------|---------|-----------|
| Motor forward | 125ms | 80mA | 10mA |
| Motor coast | 375ms | 8-10mA | 3-4mA |
| Battery sleep (automatic) | 1000ms every 10s | 8-10mA | 0.8-1mA |
| **Total Average** | | | **~25mA** |

### Phase 3 (Explicit) - Mode 2:

| Period | Duration | Current | Avg Power |
|--------|----------|---------|-----------|
| Motor forward | 125ms | 80mA | 10mA |
| Motor coast | 375ms | 8-10mA | 3-4mA |
| Battery sleep (explicit) | 1000ms every 10s | 2-3mA | 0.2-0.3mA |
| **Total Average** | | | **~23-24mA** |

**Phase 3 savings: ~1-2mA (4-8% improvement over Phase 2)**

### Battery Life Projection (dual 350mAh - 700mAh total):

| Configuration | Mode 2 Current | Battery Life | vs Phase 2 |
|---------------|----------------|--------------|------------|
| Phase 2 (Automatic) | 25mA | ~50 minutes | Baseline |
| Phase 3 (Explicit) | 23-24mA | ~52-55 minutes | +4-10% |

**Diminishing returns, but free improvement if you're implementing anyway.**

---

## Implementation Checklist

### Step 1: Create New File ✅

```bash
# Copy Phase 2 baseline
cp test/single_device_battery_bemf_queued_test.c \
   test/single_device_battery_bemf_explicit_test.c
```

### Step 2: Modify Battery Task ✅

- [ ] Add `battery_light_sleep()` helper function
- [ ] Replace `vTaskDelay()` with explicit sleep
- [ ] Add wake cause checking
- [ ] Test button wake during battery sleep

### Step 3: Update Configuration ✅

- [ ] Create `sdkconfig.single_device_battery_bemf_explicit_test`
- [ ] Copy from Phase 2 sdkconfig
- [ ] Add Phase 3 GPIO/sleep settings
- [ ] Verify PM still enabled

### Step 4: Update platformio.ini ✅

```ini
[env:single_device_battery_bemf_explicit_test]
extends = env:single_device_battery_bemf_queued_test

build_flags = 
    ${env:single_device_battery_bemf_queued_test.build_flags}
    -DPHASE_3_EXPLICIT_SLEEP=1
```

### Step 5: Test Thoroughly ✅

- [ ] Battery reads still every 10 seconds
- [ ] Button press during battery sleep wakes task
- [ ] Motor operation unchanged
- [ ] All 4 modes work correctly
- [ ] Measure power consumption improvement

---

## Testing Plan

### Functional Tests (Same as Phase 2):

- [ ] Motor operates identically to Phase 2
- [ ] All 4 modes cycle correctly
- [ ] Button responsive (even during battery sleep)
- [ ] Battery monitoring works (10-second interval)
- [ ] LVO warnings/shutdown work
- [ ] Emergency shutdown (5-sec hold) works

### Phase 3-Specific Tests:

- [ ] **Battery sleep duration accurate:**
  - Time 10 battery reads
  - Should be exactly 10 seconds apart
  - ±50ms tolerance

- [ ] **Button wake during battery sleep:**
  - Press button during 1-second battery sleep
  - Should wake task immediately
  - Should continue normal operation

- [ ] **Wake cause logging:**
  - Check serial output for wake causes
  - Should see timer wake (normal)
  - Should see GPIO wake (button press)

### Power Measurement:

- [ ] Measure current during battery sleep
  - Phase 2: Expected ~8-10mA
  - Phase 3: Expected ~2-3mA
  - Improvement: ~5-7mA (60-70%)

- [ ] Measure overall average (20-minute session)
  - Phase 2: ~25mA (Mode 2)
  - Phase 3: ~23-24mA (Mode 2)
  - Improvement: ~1-2mA (4-8%)

---

## Common Pitfalls

### ❌ Pitfall 1: Forgetting GPIO Wakeup

```c
// WRONG - No button wake configured
esp_sleep_enable_timer_wakeup(1000 * 1000);
esp_light_sleep_start();
// Button press during sleep does nothing!
```

```c
// CORRECT - Button can wake us
esp_sleep_enable_timer_wakeup(1000 * 1000);
gpio_wakeup_enable(GPIO_BUTTON, GPIO_INTR_LOW_LEVEL);
esp_sleep_enable_gpio_wakeup();
esp_light_sleep_start();
```

### ❌ Pitfall 2: Not Cleaning Up Wake Sources

```c
// WRONG - Wake sources accumulate
while (1) {
    esp_sleep_enable_timer_wakeup(1000 * 1000);
    gpio_wakeup_enable(GPIO_BUTTON, GPIO_INTR_LOW_LEVEL);
    esp_sleep_enable_gpio_wakeup();
    esp_light_sleep_start();
    // GPIO wake still enabled!
}
```

```c
// CORRECT - Clean up after wake
while (1) {
    esp_sleep_enable_timer_wakeup(1000 * 1000);
    gpio_wakeup_enable(GPIO_BUTTON, GPIO_INTR_LOW_LEVEL);
    esp_sleep_enable_gpio_wakeup();
    esp_light_sleep_start();
    
    // Clean up
    esp_sleep_disable_wakeup_source(ESP_SLEEP_WAKEUP_GPIO);
    gpio_wakeup_disable(GPIO_BUTTON);
}
```

### ❌ Pitfall 3: Incorrect Time Units

```c
// WRONG - Time in milliseconds
esp_sleep_enable_timer_wakeup(1000);  // Only 1ms!
```

```c
// CORRECT - Time in microseconds
esp_sleep_enable_timer_wakeup(1000 * 1000);  // 1 second
```

---

## When to Use Phase 3

### Use Phase 3 if:

✅ You need absolute minimum power (every mA counts)  
✅ You have tasks with ≥1 second delays  
✅ You want explicit control over wake sources  
✅ You're willing to manage wake source configuration  
✅ You're measuring power consumption and need to optimize  

### Stick with Phase 2 if:

✅ Automatic tickless idle is "good enough"  
✅ Code simplicity is more important than 1-2mA  
✅ All your delays are <1 second  
✅ You don't want to manage wake sources manually  
✅ You value "set and forget" power management  

**For EMDR Pulser: Phase 3 provides ~5% improvement. Nice but not essential.**

---

## BLE Compatibility Note

**Phase 3 explicit sleep is also BLE-compatible!** ✅

```c
// Phase 3 with BLE (future)
CONFIG_PM_ENABLE=y
CONFIG_BT_SLEEP_ENABLE=y
CONFIG_BTDM_MODEM_SLEEP_MODE_ORIG=y

// In battery task:
esp_sleep_enable_timer_wakeup(1000 * 1000);
esp_sleep_enable_gpio_wakeup();       // Button
esp_sleep_enable_bt_wakeup();          // BLE events (NEW!)
esp_light_sleep_start();

// Wakes on: Timer OR Button OR BLE event
```

**Phase 3 architecture supports future BLE integration!**

---

## Next Steps

### 1. Decide: Phase 3 Worth It?

**Question:** Is 5% power improvement worth 2-4 hours of work?

- For research/prototyping: **Probably not** (Phase 2 is good enough)
- For production/optimization: **Maybe** (depends on requirements)
- For learning/completeness: **Yes** (good to understand explicit sleep)

### 2. If Yes: Implement Phase 3

- Create `single_device_battery_bemf_explicit_test.c`
- Modify battery task as shown above
- Update configuration
- Test thoroughly
- Measure power improvement

### 3. If No: Skip to Phase 4

Phase 4 (Full JPL Compliance) provides:
- Code quality improvements
- Static analysis integration
- Production readiness

**Phase 4 is arguably more valuable than Phase 3 for most users.**

---

## Summary

**Phase 3 provides:**
- ~5% additional power savings over Phase 2
- Explicit control over sleep behavior
- Better understanding of ESP32 power management
- Foundation for advanced power optimization

**Phase 3 requires:**
- 2-4 hours implementation + testing
- Manual wake source management
- More complex code
- Careful testing of wake scenarios

**Recommendation:**
- **Skip Phase 3** if Phase 2 battery life meets requirements
- **Implement Phase 3** if you need maximum battery life
- **Consider Phase 4** (JPL compliance) before Phase 3

---

## Ready to Implement?

If yes:
1. Read this guide thoroughly
2. Create new file from Phase 2 baseline
3. Implement battery task changes
4. Test extensively
5. Measure power improvement

If no:
- Phase 2 is production-ready
- Consider Phase 4 (JPL compliance) next
- Or Phase 5 (BLE GATT server) for remote control

**Your Phase 2 implementation is already excellent. Phase 3 is optional optimization.**

---

**Next:** Would you like me to:
1. Create the full Phase 3 implementation?
2. Skip to Phase 4 (JPL Compliance)?
3. Or discuss Phase 5 (BLE) timeline?
