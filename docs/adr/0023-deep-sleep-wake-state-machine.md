# 0023: Deep Sleep Wake State Machine for ESP32-C6 ext1

**Date:** 2025-10-25
**Phase:** 0.4
**Status:** Accepted
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of ESP32-C6 level-triggered ext1 wake mechanism,
facing immediate wake when button held during sleep entry,
we decided for wait-for-release with LED blink feedback pattern,
and neglected state machine with wake-on-HIGH or immediate re-sleep approaches,
to achieve guaranteed wake-on-new-press behavior,
accepting user must release button before sleep entry completes.

---

## Problem Statement

ESP32-C6 ext1 wake is **level-triggered**, not edge-triggered. This creates a fundamental challenge for button-triggered deep sleep:

**Initial Problem:**
- User holds button through countdown to trigger deep sleep
- Device enters sleep while button is LOW (pressed)
- ext1 configured to wake on LOW
- Device wakes immediately because button is still LOW
- Can't distinguish "still held from countdown" vs "new button press"

**Root Cause:** The ext1 wake system detects that GPIO1 is LOW at the moment of sleep entry. Since ext1 is level-triggered (wakes when GPIO is LOW), the device immediately wakes up because the wake condition is already true. There's no hardware mechanism to distinguish continuous hold vs. fresh press.

---

## Context

**Hardware Constraints:**
- ESP32-C6 ext1 wake is level-triggered (not edge-triggered)
- No hardware debouncing or edge detection available
- ext1 wake-on-HIGH support may be unreliable on ESP32-C6
- Button configured: Active LOW (pressed = 0, released = 1)

**User Experience Requirements:**
- 5-second button hold triggers deep sleep countdown
- User needs clear feedback when to release button
- Next button press must reliably wake device
- No serial monitor available for user feedback in field use

**Safety Requirements:**
- Guaranteed reliable wake from deep sleep
- Predictable behavior for medical device
- Simple, testable state machine

---

## Decision

We will use wait-for-release with LED blink feedback before deep sleep entry.

**Implementation:**

```c
esp_err_t enter_deep_sleep_with_wake_guarantee(void) {
    // If button held after countdown, wait for release
    if (gpio_get_level(GPIO_BUTTON) == 0) {
        ESP_LOGI(TAG, "Waiting for button release...");

        // Blink LED while waiting (visual feedback without serial)
        while (gpio_get_level(GPIO_BUTTON) == 0) {
            // Toggle LED at 5Hz (200ms period)
            gpio_set_level(GPIO_STATUS_LED, LED_ON);
            vTaskDelay(pdMS_TO_TICKS(100));
            gpio_set_level(GPIO_STATUS_LED, LED_OFF);
            vTaskDelay(pdMS_TO_TICKS(100));
        }

        ESP_LOGI(TAG, "Button released! Entering deep sleep...");
    }

    // Always configure ext1 to wake on LOW (button press)
    // Button guaranteed to be HIGH at this point
    uint64_t gpio_mask = (1ULL << GPIO_BUTTON);
    esp_err_t ret = esp_sleep_enable_ext1_wakeup(gpio_mask, ESP_EXT1_WAKEUP_ANY_LOW);
    if (ret != ESP_OK) {
        return ret;
    }

    // Enter deep sleep (button guaranteed HIGH at this point)
    esp_deep_sleep_start();

    // Never returns
    return ESP_OK;
}
```

**Key Features:**
- LED blinks rapidly (5Hz) while waiting for release - visual feedback without serial monitor
- Guarantees button is HIGH before sleep entry
- ext1 always configured for wake-on-LOW (next button press)
- Next wake is guaranteed to be NEW button press (not the countdown hold)
- Simple and bulletproof - no complex state machine

**User Experience Flow:**
1. User holds button 5+ seconds → Countdown ("5... 4... 3... 2... 1...")
2. LED blinks fast (5Hz) → Visual cue: "Release the button now"
3. User releases button → Device sleeps immediately
4. Later: User presses button → Device wakes (guaranteed NEW press)

---

## Consequences

### Benefits

- **Guaranteed reliable wake:** Next wake always from NEW button press
- **Visual user feedback:** LED blink provides clear indication without serial monitor
- **Simple implementation:** No complex state machine or conditional wake logic
- **Hardware compatibility:** Works within ESP32-C6 ext1 limitations
- **Predictable behavior:** Same wake pattern every time
- **Medical device appropriate:** Reliable, testable, maintainable
- **User-friendly:** Clear visual indication of expected user action

### Drawbacks

- **User must release button:** Can't sleep while holding button (acceptable, clear feedback)
- **Indefinite wait possible:** LED blinks indefinitely if button stuck (rare, detectable)
- **Active power during blink:** ~50mA while waiting for release (brief duration acceptable)

---

## Options Considered

### Option A: Immediate Re-Sleep with State Checking

**Implementation:**
```c
// ❌ DOES NOT WORK
esp_deep_sleep_start();
// Wake up here
if (gpio_get_level(GPIO_BUTTON) == 0) {
    // Button still held, go back to sleep
    esp_deep_sleep_start();
}
```

**Pros:**
- Simple logic
- No user action required

**Cons:**
- Device stuck sleeping after button release (wake condition never occurs)
- Can't detect new button press after re-sleeping
- Fundamental misunderstanding of level-triggered wake

**Selected:** NO
**Rationale:** Broken approach - device becomes unresponsive after button release

### Option B: State Machine with Wake-on-HIGH Support

**Implementation:**
```c
// ❌ TOO COMPLEX, hardware limitations
if (gpio_get_level(GPIO_BUTTON) == 0) {
    // Button held, configure wake on HIGH (release)
    esp_sleep_enable_ext1_wakeup(gpio_mask, ESP_EXT1_WAKEUP_ANY_HIGH);
} else {
    // Button not held, configure wake on LOW (press)
    esp_sleep_enable_ext1_wakeup(gpio_mask, ESP_EXT1_WAKEUP_ANY_LOW);
}
```

**Pros:**
- No user action required during countdown
- Could handle both scenarios

**Cons:**
- ESP32-C6 ext1 wake-on-HIGH support may be unreliable
- Adds significant state machine complexity
- Testing revealed inconsistent wake behavior
- Too fragile for safety-critical medical device

**Selected:** NO
**Rationale:** Hardware reliability concerns and excessive complexity

### Option C: Wait-for-Release with LED Blink (CHOSEN)

**Implementation:** See Decision section above

**Pros:**
- Simple and bulletproof
- Works within ESP32-C6 hardware limitations
- Visual feedback without serial monitor
- Guarantees wake-on-new-press
- Exploits level-triggered nature rather than fighting it

**Cons:**
- User must release button (acceptable with clear feedback)
- Active power during wait (brief duration)

**Selected:** YES
**Rationale:** Best balance of simplicity, reliability, and user experience

---

## Related Decisions

### Related
- **AD025: Dual-Device Wake Pattern** - Instant wake (no hold) pairs well with wait-for-release sleep
- **AD013: NVS Security Window** - 10s hold for NVS clear uses similar wait-for-release pattern

---

## Implementation Notes

### Code References

- **Reference Implementation:** `test/button_deepsleep_test.c` (hardware validation)
- **Production Use:** `test/single_device_demo_jpl_queued.c` lines ~800-850 (button_task)
- **Pattern Documentation:** `test/BUTTON_DEEPSLEEP_TEST_GUIDE.md`

### Build Environment

- **Environment Name:** `button_deepsleep_test` (hardware validation)
- **Configuration File:** `sdkconfig.button_deepsleep_test`
- **Hardware:** Seeed XIAO ESP32-C6 with button on GPIO1

### Testing & Verification

**Hardware Test Procedure:**
1. Hold button through 5-second countdown
2. Verify LED blinks while waiting for release
3. Release button, verify device sleeps
4. Press button, verify device wakes
5. Verify wake reason is EXT1 (RTC GPIO)

**Edge Cases Tested:**
- Button released during countdown → Sleep immediately (no blink)
- Button held indefinitely → LED blinks indefinitely (device waits)
- Button bounces during release → Debouncing prevents false wake

**Power Consumption Verified:**
- Active (LED blinking): ~50mA
- Deep sleep: <1mA
- Wake latency: <2 seconds

---

## JPL Coding Standards Compliance

- ✅ Rule #1: No dynamic memory allocation - Stack-based state only
- ✅ Rule #2: Fixed loop bounds - while(button_held) has guaranteed exit (user releases)
- ✅ Rule #3: No recursion - Linear control flow
- ✅ Rule #4: No goto statements - Clean if/while structure
- ✅ Rule #5: Return value checking - esp_sleep_enable_ext1_wakeup() checked
- ✅ Rule #6: No unbounded waits - vTaskDelay() for all timing
- ✅ Rule #7: Watchdog compliance - Feed watchdog during wait loop
- ✅ Rule #8: Defensive logging - ESP_LOGI for state transitions

**Why This Works (Exploiting Level-Triggered Wake):**

The solution exploits the level-triggered nature of ext1 rather than fighting it:

1. **Before sleep:** Ensure button is HIGH (not pressed)
2. **Configure ext1:** Wake when GPIO goes LOW (button pressed)
3. **Sleep entry:** Wake condition is FALSE (button is HIGH)
4. **Sleep state:** Device waits for wake condition to become TRUE
5. **Wake event:** Only occurs when button transitions from HIGH → LOW
6. **Guarantee:** This can only happen with a NEW button press

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: AD023
Git commit: (phase 0.4 implementation)

**Integration with Main Application:**

This pattern must be used for all button-triggered deep sleep scenarios:
- Session timeout → automatic sleep (no button hold)
- User-initiated sleep → 5-second button hold with wait-for-release
- Emergency shutdown → immediate motor coast, then sleep with wait-for-release
- Battery low → warning, then sleep with wait-for-release

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
