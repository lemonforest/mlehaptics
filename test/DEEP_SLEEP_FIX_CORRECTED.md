# Single Device Demo Test - Deep Sleep Fix (Corrected)
**Date:** November 1, 2025  
**Issue:** Device not properly entering deep sleep with button wait-for-release  
**Resolution:** Fixed by restoring proper WS2812B purple blink and correct cleanup sequence

## Problem Analysis

The original implementation had been incorrectly modified to use GPIO15 instead of the intended WS2812B purple blink. Additionally, the WS2812B LED strip wasn't being properly cleaned up, causing potential heap corruption.

## Key Issues Found

1. **Incorrect LED Usage**: Code was using GPIO15 instead of WS2812B for the purple blink
2. **Missing Cleanup**: `led_strip_del()` was never called to free RMT resources
3. **Timing Issue**: Tasks weren't given enough time to exit cleanly (only 500ms)
4. **Wrong Documentation**: Analysis documents incorrectly stated GPIO15 was the fix

## Correct Fix Applied

### 1. Restored WS2812B Purple Blink
```c
// Purple LED blink (128, 0, 128) with brightness scaling
while (gpio_get_level(GPIO_BUTTON) == 0) {
    uint8_t r = 128, g = 0, b = 128;
    if (led_on) {
        apply_brightness(&r, &g, &b, WS2812B_BRIGHTNESS);
        led_strip_set_pixel(led_strip, 0, r, g, b);
    } else {
        led_strip_set_pixel(led_strip, 0, 0, 0, 0);
    }
    led_strip_refresh(led_strip);
    led_on = !led_on;
    
    // Feed watchdog
    esp_task_wdt_reset();
    vTaskDelay(pdMS_TO_TICKS(200));
}
```

### 2. Proper WS2812B Cleanup AFTER Blink
```c
// Clean up WS2812B LED strip AFTER blink loop completes
ESP_LOGI(TAG, "Shutting down WS2812B...");
led_strip_clear(led_strip);
led_strip_del(led_strip);  // CRITICAL: Free RMT resources
led_strip = NULL;
gpio_set_level(GPIO_WS2812B_ENABLE, 1);  // Disable power
```

### 3. Extended Task Exit Time
- Changed from 500ms to 1000ms wait after setting `session_active = false`
- Ensures all tasks have time to exit cleanly before memory operations

### 4. Proper Sleep Entry Flow

The correct sequence is now:
1. Countdown completes with button held
2. Set `session_active = false` to signal tasks
3. Wait 1000ms for tasks to exit cleanly
4. Subscribe to watchdog
5. Enter deep sleep function
6. Purple blink while waiting for button release
7. After release, cleanup WS2812B
8. Configure RTC wake
9. Enter deep sleep

## Why This Works

- **WS2812B is safe to use**: The RMT driver is fine as long as we properly clean it up AFTER the blink loop
- **Proper cleanup order**: Blink first, then delete led_strip handle, then sleep
- **Task synchronization**: 1000ms gives all tasks time to exit before any memory operations
- **Watchdog management**: Button task subscribes and feeds watchdog during wait loop

## Testing

```bash
pio run -e single_device_demo_test -t upload && pio device monitor
```

### Test 1: Button Hold Sleep
1. Hold button for 5 seconds
2. See countdown (4...3...2...1...)
3. See purple LED blink while holding
4. Release button
5. Device enters deep sleep cleanly

### Test 2: 20-Minute Timeout
1. Let device run full 20 minutes
2. At "Session complete!" device should:
   - Wait for tasks to exit
   - Enter deep sleep without crash
   - No heap corruption errors

### Test 3: Cancel During Countdown
1. Hold button for 1 second
2. During countdown, release button
3. Countdown cancels
4. Device continues normal operation

## Verification Points

✅ Purple LED blinks (not GPIO15)  
✅ Device waits for button release before sleeping  
✅ No heap corruption assert failures  
✅ Clean wake on next button press  
✅ Watchdog doesn't trigger during wait  

## Important Notes

- The `button_deepsleep_test.c` doesn't use WS2812B at all - it only uses GPIO15
- The WS2812B purple blink works fine as long as proper cleanup is done
- GPIO15 is NOT needed to avoid RMT issues - proper cleanup is what's needed
- The original purple blink logic was correct, just missing the cleanup
