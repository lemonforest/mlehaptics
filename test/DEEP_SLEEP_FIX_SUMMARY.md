# Single Device Demo Test - Deep Sleep Fix Summary
**Date:** November 1, 2025
**Issue:** Heap corruption crash after 20-minute session completion
**Resolution:** Fixed by properly handling WS2812B LED strip shutdown and task cleanup

## Root Cause Analysis

The crash was caused by improper cleanup of the WS2812B LED strip (RMT driver) during the transition to deep sleep:

1. **Heap Corruption**: The led_strip handle wasn't properly deleted before sleep, leaving RMT resources allocated
2. **Task Race Condition**: Tasks weren't given enough time to cleanly exit before memory operations
3. **GPIO Conflicts**: Using WS2812B for the "purple blink" during button wait caused RMT/heap operations during critical shutdown phase

## Key Fixes Applied

### 1. Proper WS2812B Shutdown
```c
// NEW: Clean shutdown function
static void shutdown_ws2812b(void) {
    if (led_strip != NULL) {
        led_strip_clear(led_strip);
        led_strip_del(led_strip);  // CRITICAL: Free RMT resources
        led_strip = NULL;
        gpio_set_level(GPIO_WS2812B_ENABLE, 1);  // Cut power
    }
}
```

### 2. Use GPIO15 for Sleep Blink
- Replaced WS2812B "purple blink" with onboard LED (GPIO15)
- No heap operations during wait-for-button-release
- Simple GPIO toggle instead of RMT driver calls

### 3. Extended Task Exit Time
- Increased wait time from 500ms to 1000ms for tasks to exit
- Tasks check `session_active` flag and self-delete cleanly
- Motor task unsubscribes from watchdog before deletion

### 4. Watchdog Management
- Button task only subscribes to watchdog when entering sleep
- Session coordinator subscribes when triggering timeout sleep
- Proper `esp_task_wdt_reset()` during button wait loop

## Testing Recommendations

1. **20-Minute Session Test**
   - Let device run full 20-minute session
   - Should enter deep sleep without crash
   - Verify wake on button press

2. **Button Hold Sleep Test**
   - Hold button for 5 seconds during session
   - Verify countdown and clean sleep entry
   - Check for proper LED blink during wait

3. **Memory Leak Test**
   - Run multiple wake/sleep cycles
   - Monitor heap usage after each wake
   - Verify no memory leaks

## Comparison with button_deepsleep_test

The fixed version now follows the proven pattern from `button_deepsleep_test.c`:
- Simple GPIO blink during wait (no complex drivers)
- Proper task cleanup before memory operations
- RTC GPIO configuration at the right time
- Clear separation of concerns between tasks

## Files Changed

- **single_device_demo_test.c** - Fixed version (active)
- **single_device_demo_test_original.c** - Backup of problematic version

## Build Command

```bash
pio run -e single_device_demo_test -t upload && pio device monitor
```

## Verification

The fix should eliminate the heap corruption assert failure:
```
assert failed: block_merge_prev heap_tlsf.c:379 (block_is_free(prev) && "prev block is not free though marked as such")
```

Instead, you should see clean deep sleep entry:
```
Session complete! (20 minutes)
Waiting for tasks to exit...
WS2812B shutdown complete
Entering ultra-low power deep sleep mode...
```
