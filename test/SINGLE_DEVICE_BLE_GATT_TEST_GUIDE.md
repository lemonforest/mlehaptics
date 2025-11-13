# BLE GATT Server Test Guide

**Test File:** `test/single_device_ble_gatt_test.c`
**Build Environment:** `single_device_ble_gatt_test`
**Date:** November 6, 2025

## Overview

This test implements a complete NimBLE GATT service for the EMDR bilateral stimulation device, allowing BLE configuration via mobile app (nRF Connect).

## Features Implemented

### 1. Custom 128-bit UUID Base
- **Base UUID:** `a1b2c3d4-e5f6-7890-a1b2-c3d4e5f67890`
- **Format:** Last 2 bytes are 16-bit little-endian offsets
- **Service UUID:** `...0000` (offset 0x0000)

### 2. GATT Characteristics

| Characteristic | UUID Offset | Type | Properties | Description |
|----------------|-------------|------|------------|-------------|
| Mode | 0x0001 | uint8 | Read/Write | Current mode (0-4) |
| Custom Frequency | 0x0002 | uint16 | Read/Write | Hz × 100 (50-200 = 0.5-2.0Hz) |
| Custom Duty Cycle | 0x0003 | uint8 | Read/Write | Percentage (0-50%, 0%=LED-only) |
| Battery Level | 0x0004 | uint8 | Read/Notify | Battery % (0-100) |
| Session Time | 0x0005 | uint32 | Read/Notify | Elapsed seconds |
| LED Enable | 0x0006 | uint8 | Read/Write | LED on/off for Mode 5 (0=off, 1=on) |
| LED Color | 0x0007 | uint8 | Read/Write | Color index (0-15, see palette) |
| LED Brightness | 0x0008 | uint8 | Read/Write | Brightness % (10-30%) |
| PWM Intensity | 0x0009 | uint8 | Read/Write | Motor PWM % for Mode 5 (30-90%, default 75%) |

### 3. Mode 5 LED Color Palette
Mode 5 supports 16 predefined RGB colors for WS2812B LED feedback:

| Index | Color Name | RGB Values | Hex |
|-------|------------|------------|-----|
| 0 | Red | (255, 0, 0) | #FF0000 |
| 1 | Orange | (255, 127, 0) | #FF7F00 |
| 2 | Yellow | (255, 255, 0) | #FFFF00 |
| 3 | Green | (0, 255, 0) | #00FF00 |
| 4 | Spring Green | (0, 255, 127) | #00FF7F |
| 5 | Cyan | (0, 255, 255) | #00FFFF |
| 6 | Sky Blue | (0, 127, 255) | #007FFF |
| 7 | Blue | (0, 0, 255) | #0000FF |
| 8 | Violet | (127, 0, 255) | #7F00FF |
| 9 | Magenta | (255, 0, 255) | #FF00FF |
| 10 | Pink | (255, 0, 127) | #FF007F |
| 11 | White | (255, 255, 255) | #FFFFFF |
| 12 | Gray | (127, 127, 127) | #7F7F7F |
| 13 | Dark Gray | (64, 64, 64) | #404040 |
| 14 | Light Gray | (192, 192, 192) | #C0C0C0 |
| 15 | Brown | (128, 64, 0) | #804000 |

**Notes:**
- Brightness is applied on top of base color (configurable 10-30%)
- Default: Red (index 0) at 20% brightness
- LED control only applies in Mode 5

### 4. Mode 5 (MODE_CUSTOM) Integration
- **Default:** 1Hz @ 50% duty cycle
- **Frequency range:** 0.5Hz - 2.0Hz (therapeutic EMDRIA range)
- **Duty cycle range:** 10% - 90% (prevents motor stall/overheat)
- **LED defaults:** Enabled, Red color (index 0), 20% brightness
- **Dynamic updates:** Changes apply immediately if in Mode 5

### 5. Motor Timing Calculation
```c
// Formula
period_ms = 100000 / custom_frequency_hz
on_time_ms = (period_ms * custom_duty_percent) / 100
coast_ms = period_ms - on_time_ms

// Example: 1Hz @ 50%
custom_frequency_hz = 100  // 1.00 Hz
custom_duty_percent = 50   // 50%
→ period_ms = 1000ms
→ on_time_ms = 500ms
→ coast_ms = 500ms
```

### 6. JPL Coding Standards Compliance
- ✅ No dynamic memory allocation (static UUIDs)
- ✅ All ESP-IDF calls wrapped in ESP_ERROR_CHECK()
- ✅ Comprehensive ESP_LOGI() logging
- ✅ Input validation on all write operations
- ✅ Queue-based task communication

### 7. NVS Persistence for Mode 5 Settings

**Status:** ✅ Implemented (November 6, 2025)

Mode 5 settings are automatically saved to Non-Volatile Storage (NVS) and restored across power cycles and deep sleep wake cycles.

#### Persisted Settings

The following 6 Mode 5 characteristics are persisted to NVS:

| Characteristic | UUID | Type | Storage Key | Default Value |
|----------------|------|------|-------------|---------------|
| Custom Frequency | 0x0002 | uint16 | `freq` | 100 (1.0 Hz) |
| Custom Duty Cycle | 0x0003 | uint8 | `duty` | 50% |
| LED Enable | 0x0006 | uint8 | `led_en` | 1 (enabled) |
| LED Color | 0x0007 | uint8 | `led_col` | 0 (red) |
| LED Brightness | 0x0008 | uint8 | `led_bri` | 20% |
| PWM Intensity | 0x0009 | uint8 | `pwm_int` | 75% |

**Note:** Mode (0x0001) is NOT persisted - device always boots to Mode 1.

#### How It Works

**Lazy Write Strategy:**
- Settings are **only saved when entering deep sleep** (5-second button hold)
- Uses dirty flag to skip NVS write if no BLE changes occurred
- Optimizes flash wear by avoiding unnecessary writes

**CRC32 Signature Validation:**
- Each boot, firmware calculates expected signature from GATT structure
- Signature data: `{uuid_ending, byte_length}` pairs for all 6 characteristics
- Example: `{0x02,2, 0x03,1, 0x06,1, 0x07,1, 0x08,1, 0x09,1}` → CRC32 hash
- Protects against loading corrupted data if GATT structure changes

**Boot Behavior:**
```
First Boot:
  → NVS empty → Use defaults → Log: "Unable to open namespace (first boot?)"

Subsequent Boots (Signature Match):
  → Load all 6 settings from NVS → Log: "Signature valid (0xXXXXXXXX), loading..."
  → Recalculate motor timings from loaded frequency/duty

Structure Changed (Signature Mismatch):
  → Ignore stored values → Use defaults → Log: "Signature mismatch - using defaults"
  → Prevents loading undefined values after code changes
```

#### Testing NVS Persistence

**Test Procedure:**

1. **Upload firmware and verify first boot:**
   ```bash
   pio run -e single_device_ble_gatt_test -t upload && pio device monitor
   ```
   Expected log: `NVS: Unable to open namespace (first boot?) - using defaults`

2. **Connect via nRF Connect and modify Mode 5 settings:**
   - Change Custom Frequency to 150 (1.5 Hz)
   - Change Custom Duty to 60%
   - Change LED Color to Blue (index 7)
   - Change LED Brightness to 25%
   - Change PWM Intensity to 80%

3. **Switch to Mode 5 and verify changes applied:**
   - Write `0x04` to Mode characteristic (0x0001)
   - Motor should run at 1.5 Hz, 60% duty, 80% PWM intensity
   - LED should be blue at 25% brightness

4. **Trigger deep sleep:**
   - Hold button for 5 seconds until purple LED starts blinking
   - Release button when purple blink appears
   - Device enters deep sleep
   - Expected log before sleep:
     ```
     NVS: Saving Mode 5 settings...
     NVS: Mode 5 settings saved (freq=150 duty=60% led_en=1 led_col=7 led_bri=25% pwm=80%)
     Entering deep sleep
     ```

5. **Wake device and verify persistence:**
   - Press button to wake from deep sleep
   - Check serial log for:
     ```
     NVS: Signature valid (0xXXXXXXXX), loading Mode 5 settings...
     NVS: Loaded frequency = 150
     NVS: Loaded duty = 60%
     NVS: Loaded LED enable = 1
     NVS: Loaded LED color index = 7
     NVS: Loaded LED brightness = 25%
     NVS: Loaded PWM intensity = 80%
     NVS: Mode 5 settings loaded successfully
     ```

6. **Switch to Mode 5 and confirm settings persisted:**
   - Write `0x04` to Mode characteristic via BLE
   - Motor should immediately run with saved parameters (1.5 Hz, 60%, 80%)
   - LED should be blue at 25% brightness

**Expected Results:**
- ✅ Settings persist across deep sleep cycles
- ✅ Settings persist across power cycles (unplug/replug USB)
- ✅ Dirty flag optimization prevents unnecessary writes if no BLE changes
- ✅ Device boots to Mode 1 every time (mode not persisted)

#### NVS Storage Details

**NVS Namespace:** `mode5_cfg`

**Storage Keys:**
- `sig` (uint32) - CRC32 signature for structure validation
- `freq` (uint16) - Custom frequency in centahertz (50-200)
- `duty` (uint8) - Duty cycle percentage (0-50, 0=LED-only)
- `led_en` (uint8) - LED enable flag (0 or 1)
- `led_col` (uint8) - LED color index (0-15)
- `led_bri` (uint8) - LED brightness percentage (10-30)
- `pwm_int` (uint8) - PWM intensity percentage (30-90)

**Total Storage:** 11 bytes (1×uint32 + 1×uint16 + 5×uint8)

**Flash Wear Considerations:**
- ESP32-C6 NVS flash: ~100,000 write cycles
- Lazy write strategy: 1 write per session (when entering sleep)
- Expected lifespan: >10 years at 10 sessions/day

#### Serial Log Examples

**First Boot (No NVS Data):**
```
DEBUG: About to load Mode 5 settings from NVS
NVS: Unable to open namespace (first boot?) - using defaults
DEBUG: Mode 5 settings load complete
```

**Normal Boot (Settings Restored):**
```
DEBUG: About to load Mode 5 settings from NVS
NVS: Signature valid (0x8A3B2C1D), loading Mode 5 settings...
NVS: Loaded frequency = 150
NVS: Loaded duty = 60%
NVS: Loaded LED enable = 1
NVS: Loaded LED color index = 7
NVS: Loaded LED brightness = 25%
NVS: Loaded PWM intensity = 80%
NVS: Mode 5 settings loaded successfully
DEBUG: Mode 5 settings load complete
```

**Deep Sleep Entry (Save):**
```
NVS: Saving Mode 5 settings...
NVS: Mode 5 settings saved (freq=150 duty=60% led_en=1 led_col=7 led_bri=25% pwm=80%)
Entering deep sleep
```

**Deep Sleep Entry (No Changes):**
```
NVS: Mode 5 settings unchanged, skipping save
Entering deep sleep
```

**Structure Changed (Signature Mismatch):**
```
NVS: Signature mismatch (0x12345678 != 0x8A3B2C1D) - using defaults
DEBUG: Mode 5 settings load complete
```

#### Implementation Details

**Code Locations:**
- **NVS Infrastructure:** `test/single_device_ble_gatt_test.c` lines 36-37, 198-206, 311-313
- **Helper Functions:** Lines 487-632
  - `calculate_mode5_signature()` - CRC32 calculation
  - `load_mode5_settings_from_nvs()` - Boot-time load with validation
  - `save_mode5_settings_to_nvs()` - Pre-sleep save with dirty check
- **Dirty Flag Updates:** All 6 GATT write handlers (lines 702-960)
- **Initialization:** `app_main()` lines 1940-1953
- **Save Trigger:** `enter_deep_sleep()` line 1482-1483

**Thread Safety:**
- FreeRTOS mutex protects dirty flag access
- All GATT write handlers use mutex-protected pattern
- Graceful degradation if mutex creation fails (early boot)

**Error Handling:**
- NVS write failure logged but doesn't block deep sleep (battery safety)
- Signature mismatch automatically falls back to defaults
- Missing NVS data treated as first boot (uses defaults)

---

## State Machine Architecture

**Implemented:** November 8, 2025
**Motivation:** Instant mode switching (< 100ms latency) with safe cleanup
**Analysis Status:** ✅ Production-ready (no critical bugs found)

This implementation uses explicit state machines for all three FreeRTOS tasks, following JPL coding standards for embedded systems.

### Motor Task State Machine (8 States)

**Purpose:** Control bilateral alternation pattern with instant response to mode changes

**States:**

```
                                    ┌──────────────────┐
                                    │ CHECK_MESSAGES   │ ← Loop entry point
                                    └────────┬─────────┘
                                             ↓
                                    ┌──────────────────┐
                                    │ FORWARD_ACTIVE   │ ← PWM forward, LED on
                                    └────────┬─────────┘
                                             ↓
┌─────────────────────────────┬─────────────┴─────────────┬────────────────────────────┐
│ Back-EMF Sampling Path      │                           │ Normal Operation Path      │
│ (first 10s after mode change)                           │ (after 10s)                │
├─────────────────────────────┤                           ├────────────────────────────┤
│  ┌──────────────────┐       │                           │  ┌──────────────────────┐  │
│  │ BEMF_IMMEDIATE   │       │                           │  │ FORWARD_COAST_       │  │
│  │ (coast + sample) │       │                           │  │ REMAINING            │  │
│  └────────┬─────────┘       │                           │  │ (coast full period)  │  │
│           ↓                 │                           │  └──────────┬───────────┘  │
│  ┌──────────────────┐       │                           │             ↓               │
│  │ COAST_SETTLE     │       │                           │  (skip BEMF states)        │
│  │ (wait + sample)  │       │                           │                             │
│  └────────┬─────────┘       │                           │                             │
│           ↓                 │                           │                             │
│  ┌──────────────────┐       │                           │                             │
│  │ FORWARD_COAST_   │←──────┴───────────────────────────┴─────────────────────────────┘
│  │ REMAINING        │
│  └────────┬─────────┘
│           ↓
│  ┌──────────────────┐
│  │ REVERSE_ACTIVE   │ ← PWM reverse, LED on
│  └────────┬─────────┘
│           ↓
│  (Same BEMF sampling or direct coast path)
│           ↓
│  ┌──────────────────┐
│  │ REVERSE_COAST_   │
│  │ REMAINING        │
│  └────────┬─────────┘
│           ↓
└───────────┴──→ Return to CHECK_MESSAGES (loop)

Any State + MSG_EMERGENCY_SHUTDOWN → SHUTDOWN → enter_deep_sleep() → (never returns)
```

**Key Design Decisions:**

1. **Shared Back-EMF States** - `BEMF_IMMEDIATE` and `COAST_SETTLE` are used by both FORWARD and REVERSE phases
   - Back-EMF measurement hardware (voltage summing circuit) produces same output regardless of motor direction
   - Reduces state count from 10 to 8 while maintaining JPL compliance
   - `in_forward_phase` boolean tracks direction for logging purposes only

2. **Instant Mode Switching** - `delay_with_mode_check()` helper function
   - Checks message queue every 50ms during delays (20 Hz polling)
   - Worst-case latency: < 100ms (feels instant to user)
   - Allows interruption during any delay: motor active, coast settle, coast remaining

3. **Safe Cleanup Everywhere** - Critical pattern: coast motor + clear LED before ALL state transitions
   ```c
   if (delay_with_mode_check(motor_on_ms)) {
       motor_coast();        // ALWAYS coast before transition
       led_clear();          // ALWAYS clear LED before transition
       state = MOTOR_STATE_CHECK_MESSAGES;  // Return to message check
       break;
   }
   ```

4. **Queue Purging** - Multiple rapid mode changes → only last one takes effect
   - Prevents queue overflow from button mashing
   - Prevents "queued mode changes" behavior (user expects immediate response)

**State Transition Table:**

| From State | Trigger | To State | Cleanup? | Notes |
|-----------|---------|----------|----------|-------|
| CHECK_MESSAGES | Mode change | FORWARD_ACTIVE | N/A | Fresh cycle start |
| CHECK_MESSAGES | Shutdown/Battery critical | SHUTDOWN | N/A | Emergency exit |
| FORWARD_ACTIVE | Delay complete (sampling) | BEMF_IMMEDIATE | No | Continue cycle |
| FORWARD_ACTIVE | Delay complete (no sampling) | FORWARD_COAST_REMAINING | ✅ Coast + clear | Skip BEMF |
| FORWARD_ACTIVE | Mode change during delay | CHECK_MESSAGES | ✅ Coast + clear | Instant response |
| BEMF_IMMEDIATE | Always | COAST_SETTLE | No | Already coasted |
| COAST_SETTLE | Delay complete | FORWARD_COAST_REMAINING | No | Continue cycle |
| COAST_SETTLE | Mode change during delay | CHECK_MESSAGES | No | Already coasted |
| FORWARD_COAST_REMAINING | Delay complete | REVERSE_ACTIVE | No | Half cycle done |
| FORWARD_COAST_REMAINING | Mode change during delay | CHECK_MESSAGES | No | Already coasted |
| REVERSE_ACTIVE | (same patterns as FORWARD) | ... | ... | ... |
| SHUTDOWN | Loop exits | `enter_deep_sleep()` | ✅ Coast + clear | Never returns |

### BLE Task State Machine (4 States)

**Purpose:** Manage advertising lifecycle and client connections

**States:**

```
┌─────┐     MSG_BLE_REENABLE      ┌─────────────┐
│IDLE │────────────────────────→│ ADVERTISING │
└──┬──┘                          └──────┬──────┘
   ↑                                    │
   │ Timeout (5 min)                    │ Client connected
   │ or advertising stopped             │ (GAP event)
   │                                    ↓
   │                          ┌────────────────┐
   └──────────────────────────┤   CONNECTED    │
                              └────────┬───────┘
                                       │
                                       │ Client disconnected
                                       │ (GAP event)
                                       ↓
                              (Auto-restart advertising
                               or return to IDLE)

Any State + MSG_EMERGENCY_SHUTDOWN → SHUTDOWN → ble_stop_advertising() → vTaskDelete()
```

**Analysis Result:** Grade A - No critical bugs found

**Why BLE Task Avoided Bugs (compared to Motor Task):**

1. **Simpler message handling** - Uses `if (xQueueReceive(...))` instead of `while (xQueueReceive(...))`
   - No nested loops around shutdown handling
   - Break statements always exit the correct scope

2. **Conditional-only state transitions** - No unconditional state assignments
   - Motor task HAD: `state = MOTOR_STATE_FORWARD_ACTIVE;` after message loop (bug!)
   - BLE task: All transitions inside `if` blocks, shutdown cannot be overwritten

3. **Fewer states** - 4 states vs motor's 8 states
   - Simpler control flow = less error-prone

4. **Cleanup only when needed** - `ble_stop_advertising()` called only when advertising is active
   - Idempotent design (calling stop when already stopped is safe)

**State Transition Table:**

| From State | Trigger | To State | Cleanup? | Notes |
|-----------|---------|----------|----------|-------|
| IDLE | MSG_BLE_REENABLE + success | ADVERTISING | N/A | Start advertising |
| IDLE | MSG_EMERGENCY_SHUTDOWN | SHUTDOWN | N/A | Clean exit |
| ADVERTISING | MSG_EMERGENCY_SHUTDOWN | SHUTDOWN | ✅ Stop advertising | Clean exit |
| ADVERTISING | Client connected (GAP event) | CONNECTED | N/A | GAP stops advertising |
| ADVERTISING | Timeout (5 min) | IDLE | ✅ Stop advertising | Battery conservation |
| CONNECTED | MSG_EMERGENCY_SHUTDOWN | SHUTDOWN | N/A | GAP handles disconnect |
| CONNECTED | Client disconnected | ADVERTISING or IDLE | N/A | Auto-restart or idle |
| SHUTDOWN | Task exits | `vTaskDelete()` | ✅ Stop if active | Clean task cleanup |

### Button Task State Machine (5 States)

**Purpose:** Detect button patterns for mode changes, shutdown, and BLE re-enable

**States:**

1. `BTN_STATE_IDLE` - Waiting for button press
2. `BTN_STATE_DEBOUNCE` - 50ms debounce period after press
3. `BTN_STATE_PRESSED` - Waiting for release (mode change) or hold (shutdown)
4. `BTN_STATE_SHUTDOWN` - Hold detected (5s), send shutdown message, wait for purple blink
5. `BTN_STATE_SHUTDOWN_SENT` - Terminal state after sending shutdown (prevents message spam)

**Critical Fix Applied:**
- **Bug:** Continuous "Emergency shutdown" message spam
- **Root Cause:** No terminal state after sending shutdown message
- **Fix:** Added `BTN_STATE_SHUTDOWN_SENT` terminal state that does nothing (waits for deep sleep)

### Critical Bugs Fixed During Development

The state machine refactoring uncovered **6 critical bugs** that were fixed before production:

#### Bug #1: State Overwrite After Shutdown (CRITICAL)
**Location:** Motor task, CHECK_MESSAGES state (lines 1815-1890)

**Symptom:** Emergency shutdown never stopped motor, no purple blink LED, device unresponsive

**Root Cause:** Nested loop break scope error
```c
// Inside CHECK_MESSAGES case:
while (xQueueReceive(button_to_motor_queue, &msg, 0) == pdPASS) {
    if (msg.type == MSG_EMERGENCY_SHUTDOWN) {
        state = MOTOR_STATE_SHUTDOWN;
        break;  // ❌ Only breaks inner while loop, NOT switch case!
    }
}
// Execution continues in CHECK_MESSAGES case...
state = MOTOR_STATE_FORWARD_ACTIVE;  // ❌ OVERWRITES shutdown state!
```

**Fix:** Added state guard before forward transition
```c
if (state == MOTOR_STATE_SHUTDOWN) {
    break;  // Exit CHECK_MESSAGES case
}
state = MOTOR_STATE_FORWARD_ACTIVE;  // Only if not shutting down
```

#### Bug #2-#3: Missing Cleanup (CRITICAL)
**Symptom:** LED always on, motor stuck running during mode changes

**Root Cause:** Forgot to call `motor_coast()` and `led_clear()` in non-sampling code path

**Fix:** Added explicit cleanup in ALL transition paths:
```c
// Non-sampling path (after 10 seconds)
if (delay_with_mode_check(motor_on_ms)) {
    motor_coast();   // ✅ Added
    led_clear();     // ✅ Added
    state = MOTOR_STATE_CHECK_MESSAGES;
    break;
}
// CRITICAL: Always coast and clear before next state!
motor_coast();   // ✅ Added
led_clear();     // ✅ Added
state = MOTOR_STATE_FORWARD_COAST_REMAINING;
```

#### Bug #4: Button Task Message Spam
**Symptom:** "Emergency shutdown" logged continuously after shutdown button held

**Fix:** Added terminal state `BTN_STATE_SHUTDOWN_SENT` to prevent re-sending

#### Bug #5: Watchdog Timeout
**Symptom:** Watchdog timeout during normal operation

**Root Cause:** Motor task subscribed to watchdog but only fed it in purple blink loop

**Fix:** Feed watchdog in CHECK_MESSAGES every cycle:
```c
case MOTOR_STATE_CHECK_MESSAGES: {
    esp_task_wdt_reset();  // ✅ Feed every cycle
    // ... message handling ...
}
```

#### Bug #6: BLE Parameter Update Latency
**Symptom:** BLE writes (LED color, frequency, etc.) delayed up to 1 second

**Root Cause:** Motor task only reloaded Mode 5 parameters in CHECK_MESSAGES (once per cycle)

**Fix:** Added `ble_params_updated` flag checked in `delay_with_mode_check()`:
```c
// In delay_with_mode_check():
if (ble_params_updated) {
    return true;  // Interrupt delay, return to CHECK_MESSAGES
}

// In CHECK_MESSAGES after parameter reload:
ble_params_updated = false;  // Clear flag
```

### Mode Switch Latency

**Measurement:** < 100ms worst-case (typically 50ms)

**How it works:**
- `delay_with_mode_check()` polls queue every 50ms
- Queue check is non-blocking (`xQueuePeek(..., 0)`)
- If message found, delay returns early with `true`
- Caller coasts motor, clears LED, returns to CHECK_MESSAGES

**User experience:** Instant (indistinguishable from hardware button press)

### Analysis Methodology

All three state machines were systematically analyzed using:
- **Checklist:** `docs/STATE_MACHINE_ANALYSIS_CHECKLIST.md` (10-step verification process)
- **BLE Task Report:** `test/BLE_TASK_STATE_MACHINE_ANALYSIS.md` (400+ line audit)
- **Refactoring Log:** `test/MODE_SWITCH_REFACTORING_PLAN.md` (implementation details)

**Key checks performed:**
1. ✅ Verify loop exit conditions (shutdown cannot be ignored)
2. ✅ Trace all state transitions (no orphaned states)
3. ✅ Analyze queue message handling (shutdown prioritized)
4. ✅ Check break/continue scope (correct loop exit)
5. ✅ Verify cleanup paths (motor/LED in all exit paths)
6. ✅ Look for race conditions (shared state protected)
7. ✅ Check timing and delays (watchdog fed, delays interruptible)
8. ✅ Verify state machine completeness (all enum cases handled)
9. ✅ Test edge cases (rapid messages, timeouts, battery critical)
10. ✅ Document findings and fixes

**Result:** Motor task had 6 critical bugs (all fixed), BLE task had 0 bugs (simpler design)

---

## Build & Flash

```bash
# Build
pio run -e single_device_ble_gatt_test -t upload

# Monitor
pio device monitor
```

## Testing with nRF Connect Mobile App

### Step 1: Install App
- **Android:** [nRF Connect for Mobile (Google Play)](https://play.google.com/store/apps/details?id=no.nordicsemi.android.mcp)
- **iOS:** [nRF Connect for Mobile (App Store)](https://apps.apple.com/us/app/nrf-connect-for-mobile/id1054362403)

### Step 2: Device Discovery
1. Open nRF Connect app
2. Tap "Scan" at the top
3. Look for device named: `EMDR_Pulser_XXXXXX` (last 6 hex digits of MAC address)
4. **Note:** Advertising times out after 5 minutes
   - Re-enable by holding button for 1-2 seconds (status LED on, then 3× blink)
   - Device will advertise for another 5 minutes

### Step 3: Connect
1. Tap "CONNECT" next to EMDR_Pulser device
2. Wait for connection to establish
3. Status LED will blink 5× rapidly to confirm connection
4. Services will auto-discover

### Step 4: Locate Custom Service
1. Scroll to find service UUID: `a1b2c3d4-e5f6-7890-a1b2-c3d4e5f60000`
2. Expand service to see 5 characteristics
3. Each characteristic has a UUID ending in `...00XX` where XX is offset

### Step 5: Read Characteristics

#### Battery Level (0x0004)
1. Tap "↓" (Read) button
2. Value shown in hex (e.g., `0x46` = 70%)
3. Convert hex to decimal for percentage

#### Session Time (0x0005)
1. Tap "↓" (Read) button
2. Value is 4 bytes, little-endian (e.g., `0x0000003C` = 60 seconds)

#### Current Mode (0x0001)
1. Tap "↓" (Read) button
2. Value: `0x00` to `0x04` (Mode 1 to Mode 5)

#### Custom Frequency (0x0002)
1. Tap "↓" (Read) button
2. Value is 2 bytes, little-endian
3. Default: `0x0064` = 100 = 1.00 Hz

#### Custom Duty Cycle (0x0003)
1. Tap "↓" (Read) button
2. Value: `0x32` = 50%

#### LED Enable (0x0006)
1. Tap "↓" (Read) button
2. Value: `0x01` = Enabled (default)

#### LED Color (0x0007)
1. Tap "↓" (Read) button
2. Value: `0x00` = Red (default)

#### LED Brightness (0x0008)
1. Tap "↓" (Read) button
2. Value: `0x14` = 20% (default)

#### PWM Intensity (0x0009)
1. Tap "↓" (Read) button
2. Value: `0x4B` = 75% (default)

### Step 6: Write Characteristics

#### Change Mode
1. Tap "↑" (Write) button on Mode characteristic (0x0001)
2. Select "UINT8" format
3. Enter value: `0` to `4`
   - `0` = Mode 1 (1Hz @ 50%)
   - `1` = Mode 2 (1Hz @ 25%)
   - `2` = Mode 3 (0.5Hz @ 50%)
   - `3` = Mode 4 (0.5Hz @ 25%)
   - `4` = Mode 5 (Custom - uses freq/duty settings)
4. Tap "SEND"
5. Device will switch modes immediately
6. WS2812B LED will light red for 10 seconds to indicate mode change

#### Configure Custom Frequency (Mode 5)
1. Tap "↑" (Write) button on Custom Frequency (0x0002)
2. Select "UINT16" format, little-endian
3. Enter value (Hz × 100):
   - `0x0032` (50) = 0.5 Hz
   - `0x0064` (100) = 1.0 Hz
   - `0x0096` (150) = 1.5 Hz
   - `0x00C8` (200) = 2.0 Hz
4. Tap "SEND"
5. Check serial monitor for confirmation:
   ```
   GATT Write: Custom frequency = 150 (1.50 Hz)
   Mode 5 updated: freq=150Hz duty=50% -> on=333ms coast=333ms
   ```
6. If currently in Mode 5, motor pattern updates immediately

#### Configure Custom Duty Cycle (Mode 5)
1. Tap "↑" (Write) button on Custom Duty Cycle (0x0003)
2. Select "UINT8" format
3. Enter value: `10` to `90` (percentage)
   - `0x0A` (10) = 10%
   - `0x19` (25) = 25%
   - `0x32` (50) = 50%
   - `0x4B` (75) = 75%
4. Tap "SEND"
5. Check serial monitor for confirmation
6. If currently in Mode 5, motor pattern updates immediately

#### Configure LED Enable (Mode 5)
1. Tap "↑" (Write) button on LED Enable (0x0006)
2. Select "UINT8" format
3. Enter value:
   - `0x00` (0) = Disable LED
   - `0x01` (1) = Enable LED
4. Tap "SEND"
5. Check serial monitor for confirmation:
   ```
   GATT Write: Mode 5 LED enable = 1
   ```
6. **Note:** LED control only applies when in Mode 5

#### Configure LED Color (Mode 5)
1. Tap "↑" (Write) button on LED Color (0x0007)
2. Select "UINT8" format
3. Enter value: `0` to `15` (see color palette in Section 3)
   - `0x00` (0) = Red
   - `0x03` (3) = Green
   - `0x07` (7) = Blue
   - `0x09` (9) = Magenta
4. Tap "SEND"
5. Check serial monitor for confirmation:
   ```
   GATT Write: Mode 5 LED color = 7 (R:0 G:0 B:255)
   ```
6. If currently in Mode 5 with LED enabled, color updates immediately

#### Configure LED Brightness (Mode 5)
1. Tap "↑" (Write) button on LED Brightness (0x0008)
2. Select "UINT8" format
3. Enter value: `10` to `30` (percentage)
   - `0x0A` (10) = 10% (dim)
   - `0x14` (20) = 20% (default)
   - `0x1E` (30) = 30% (bright)
4. Tap "SEND"
5. Check serial monitor for confirmation:
   ```
   GATT Write: Mode 5 LED brightness = 25%
   ```
6. If currently in Mode 5 with LED enabled, brightness updates immediately

#### Configure PWM Intensity (Mode 5)
1. Tap "↑" (Write) button on PWM Intensity (0x0009)
2. Select "UINT8" format
3. Enter value: `30` to `90` (percentage)
   - `0x1E` (30) = 30% (gentle)
   - `0x4B` (75) = 75% (default)
   - `0x5A` (90) = 90% (strong)
4. Tap "SEND"
5. Check serial monitor for confirmation:
   ```
   GATT Write: Mode 5 PWM intensity = 75%
   ```
6. If currently in Mode 5, motor intensity updates immediately

### Step 7: Test Custom Mode (Mode 5)
1. Write frequency: `0x0064` (1.0 Hz)
2. Write duty cycle: `0x32` (50%)
3. Write mode: `0x04` (Mode 5)
4. **Expected behavior:**
   - Motor alternates forward/reverse every 500ms
   - 50% on, 50% coast
   - Red LED blinks in sync for 10 seconds
5. Try different settings:
   - **0.5Hz @ 25%:** freq=50, duty=25 → long slow pulses
   - **2.0Hz @ 75%:** freq=200, duty=75 → fast strong pulses

### Step 8: Validation Checks

#### Invalid Frequency (should reject)
1. Try writing frequency `0x0030` (48 = 0.48 Hz, below 0.5 Hz min)
2. **Expected:** Write fails, no change
3. Serial log: `GATT Write: Invalid frequency 48 (range 50-200 = 0.5-2.0Hz)`

#### Invalid Duty Cycle (should reject)
1. Try writing duty cycle `0x33` (51%, above 50% max)
2. **Expected:** Write fails, no change
3. Serial log: `GATT Write: Invalid duty cycle 51% (range 0-50%)`

#### Invalid Mode (should reject)
1. Try writing mode `0x05` (Mode 6, doesn't exist)
2. **Expected:** Write fails, no change
3. Serial log: `GATT Write: Invalid mode 5 (max 4)`

#### Invalid LED Color (should reject)
1. Try writing LED color `0x10` (16, out of range 0-15)
2. **Expected:** Write fails, no change
3. Serial log: `GATT Write: LED color index 16 out of range (0-15)`

#### Invalid LED Brightness (should reject)
1. Try writing LED brightness `0x05` (5%, below 10% min)
2. **Expected:** Write fails, no change
3. Serial log: `GATT Write: LED brightness 5% out of range (10-30%)`

#### Invalid LED Brightness (high range)
1. Try writing LED brightness `0x32` (50%, above 30% max)
2. **Expected:** Write fails, no change
3. Serial log: `GATT Write: LED brightness 50% out of range (10-30%)`

#### Invalid PWM Intensity (low range)
1. Try writing PWM intensity `0x1E` (20%, below 30% min)
2. **Expected:** Write fails, no change
3. Serial log: `GATT Write: PWM intensity 20% out of range (30-90%)`

#### Invalid PWM Intensity (high range)
1. Try writing PWM intensity `0x64` (100%, above 90% max)
2. **Expected:** Write fails, no change
3. Serial log: `GATT Write: PWM intensity 100% out of range (30-90%)`

## Key Code Locations

### UUID Definitions (Lines 211-245)
```c
static const ble_uuid128_t uuid_emdr_service = BLE_UUID128_INIT(...);
static const ble_uuid128_t uuid_char_mode = BLE_UUID128_INIT(...);
// ... existing 5 characteristics
static const ble_uuid128_t uuid_char_led_enable = BLE_UUID128_INIT(...);
static const ble_uuid128_t uuid_char_led_color = BLE_UUID128_INIT(...);
static const ble_uuid128_t uuid_char_led_brightness = BLE_UUID128_INIT(...);
```

### LED Color Palette (Lines 250-274)
```c
typedef struct {
    uint8_t r;
    uint8_t g;
    uint8_t b;
} rgb_color_t;

static const rgb_color_t color_palette[16] = {
    {255, 0, 0},      // 0: Red
    // ... 16 colors total
};
```

### Custom Settings (Lines 276-285)
```c
static uint16_t custom_frequency_hz = 100;   // Default 1Hz
static uint8_t custom_duty_percent = 50;     // Default 50%
static mode_t current_mode_ble = MODE_1HZ_50;
static uint32_t session_start_time_ms = 0;

// Mode 5 LED settings
static bool mode5_led_enable = true;
static uint8_t mode5_led_color_index = 0;
static uint8_t mode5_led_brightness = 20;
```

### GATT Access Callbacks (Lines 436-752)
- `gatt_char_mode_read()` / `gatt_char_mode_write()` - Mode selection
- `gatt_char_custom_freq_read()` / `gatt_char_custom_freq_write()` - Frequency
- `gatt_char_custom_duty_read()` / `gatt_char_custom_duty_write()` - Duty cycle
- `gatt_char_battery_read()` - Battery level
- `gatt_char_session_time_read()` - Session time
- `gatt_char_led_enable_read()` / `gatt_char_led_enable_write()` - LED enable
- `gatt_char_led_color_read()` / `gatt_char_led_color_write()` - LED color
- `gatt_char_led_brightness_read()` / `gatt_char_led_brightness_write()` - LED brightness
- `gatt_svr_chr_access()` - Dispatcher

### GATT Service Definition (Lines 754-817)
```c
static const struct ble_gatt_svc_def gatt_svr_svcs[] = {
    {
        .type = BLE_GATT_SVC_TYPE_PRIMARY,
        .uuid = &uuid_emdr_service.u,
        .characteristics = (struct ble_gatt_chr_def[]) {
            // ... 5 existing characteristics
            // ... 3 new LED characteristics
        }
    }
};
```

### GATT Service Registration (Line ~975)
```c
ble_hs_cfg.gatts_register_cb = gatt_svr_register_cb;
```

### GATT Service Initialization (Lines ~740-760, called at ~980)
```c
static esp_err_t gatt_svr_init(void) {
    ble_svc_gatt_init();
    ble_gatts_count_cfg(gatt_svr_svcs);
    ble_gatts_add_svcs(gatt_svr_svcs);
}
```

## Serial Monitor Output Examples

### Successful Mode Change via BLE
```
I (12345) BLE_GATT_TEST: GATT Write: Mode changed to 4 (Custom)
I (12346) BLE_GATT_TEST: Mode: Custom
```

### Successful Frequency Update
```
I (23456) BLE_GATT_TEST: GATT Write: Custom frequency = 150 (1.50 Hz)
I (23457) BLE_GATT_TEST: Mode 5 updated: freq=150Hz duty=50% -> on=333ms coast=333ms
```

### Successful Duty Cycle Update
```
I (34567) BLE_GATT_TEST: GATT Write: Custom duty cycle = 75%
I (34568) BLE_GATT_TEST: Mode 5 updated: freq=100Hz duty=75% -> on=750ms coast=250ms
```

### Battery Read
```
I (45678) BLE_GATT_TEST: GATT Read: Battery = 82% (3.95V)
```

### Session Time Read
```
I (56789) BLE_GATT_TEST: GATT Read: Session time = 127 seconds
```

## Troubleshooting

### Device Not Advertising
**Symptom:** Can't find EMDR_Pulser in nRF Connect scan
**Causes:**
1. Advertising timeout (5 minutes elapsed)
2. BLE initialization failed
3. Device in deep sleep

**Solutions:**
1. Re-enable advertising: Hold button 1-2 seconds (LED on → 3× blink)
2. Check serial monitor for BLE init errors
3. Press button briefly to wake from sleep

### Can't Connect
**Symptom:** Connection fails or disconnects immediately
**Causes:**
1. Another device already connected
2. BLE stack busy
3. Signal strength too low

**Solutions:**
1. Disconnect other BLE devices from EMDR_Pulser
2. Power cycle device (deep sleep → wake)
3. Move closer to device (< 1 meter)

### Service Not Visible
**Symptom:** Device connects but custom service missing
**Causes:**
1. GATT services not initialized
2. UUID mismatch

**Solutions:**
1. Check serial monitor for "GATT: Services initialized successfully"
2. Verify UUID: `a1b2c3d4-e5f6-7890-a1b2-c3d4e5f60000`
3. Try disconnect → reconnect

### Write Fails
**Symptom:** Write operation returns error in nRF Connect
**Causes:**
1. Value out of range
2. Wrong data type
3. Read-only characteristic

**Solutions:**
1. Verify value ranges (see Step 8)
2. Check data type (UINT8/UINT16/UINT32)
3. Ensure characteristic is writable (Mode, Freq, Duty only)

### Mode 5 Doesn't Change
**Symptom:** Motor pattern doesn't update after writing freq/duty
**Causes:**
1. Not in Mode 5
2. Value didn't update

**Solutions:**
1. Write mode `0x04` to switch to Mode 5
2. Read back freq/duty characteristics to verify
3. Check serial monitor for confirmation logs

## Known Limitations

1. **No NVS Persistence:** Custom settings reset on deep sleep/reboot
   - Future enhancement: Save to NVS
2. **No Notifications:** Battery/session time don't auto-notify
   - Current: Manual read only
   - Future enhancement: Periodic notifications
3. **Single Connection:** Only 1 BLE client at a time
   - NimBLE limitation for single-connection config
4. **Advertising Timeout:** 5 minutes, then manual re-enable required
   - Design choice for power conservation
5. **No Security:** Open BLE connection (no pairing/bonding)
   - Future enhancement: BLE security features

## Future Enhancements

### Phase 1: NVS Persistence
- Save custom_frequency_hz and custom_duty_percent to NVS
- Restore on boot
- Survive deep sleep cycles

### Phase 2: Notifications
- Periodic battery level notifications (every 10 seconds)
- Session time notifications (every 5 seconds)
- Low battery warning notification

### Phase 3: Write Response
- Return actual applied value after write
- Useful for debugging range limiting

### Phase 4: BLE Security
- Pairing/bonding support
- PIN code protection
- Encrypted characteristics

### Phase 5: Additional Characteristics
- Motor intensity (PWM duty cycle, currently fixed 60%)
- Session duration preset
- Vibration pattern presets (e.g., ramp up/down)

## Reference: nRF Connect UUID Display Format

nRF Connect shows UUIDs in standard format:
```
Service:
a1b2c3d4-e5f6-7890-a1b2-c3d4e5f60000

Characteristics:
a1b2c3d4-e5f6-7890-a1b2-c3d4e5f60001  (Mode)
a1b2c3d4-e5f6-7890-a1b2-c3d4e5f60002  (Custom Frequency)
a1b2c3d4-e5f6-7890-a1b2-c3d4e5f60003  (Custom Duty Cycle)
a1b2c3d4-e5f6-7890-a1b2-c3d4e5f60004  (Battery Level)
a1b2c3d4-e5f6-7890-a1b2-c3d4e5f60005  (Session Time)
a1b2c3d4-e5f6-7890-a1b2-c3d4e5f60006  (LED Enable)
a1b2c3d4-e5f6-7890-a1b2-c3d4e5f60007  (LED Color)
a1b2c3d4-e5f6-7890-a1b2-c3d4e5f60008  (LED Brightness)
a1b2c3d4-e5f6-7890-a1b2-c3d4e5f60009  (PWM Intensity)
```

## Testing Checklist

### Basic BLE Functionality
- [ ] Device advertises as "EMDR_Pulser_XXXXXX"
- [ ] nRF Connect can connect
- [ ] Custom service visible (UUID ...0000)
- [ ] All 9 characteristics present

### Read Operations
- [ ] Battery read returns valid percentage
- [ ] Session time read returns elapsed seconds
- [ ] Current mode read returns 0-4
- [ ] Custom frequency read returns value
- [ ] Custom duty cycle read returns value
- [ ] LED enable read returns 0 or 1
- [ ] LED color read returns 0-15
- [ ] LED brightness read returns 10-30
- [ ] PWM intensity read returns 30-90

### Write Operations - Motor Control
- [ ] Mode write changes motor pattern (test all 5 modes)
- [ ] Custom frequency write accepted (50-200)
- [ ] Custom frequency write rejected (< 50 or > 200)
- [ ] Custom duty cycle write accepted (0-50)
- [ ] Custom duty cycle write rejected (> 50)
- [ ] Mode 5 applies custom freq/duty settings
- [ ] Motor pattern updates immediately when changing freq/duty in Mode 5

### Write Operations - LED Control
- [ ] LED enable write toggles LED on/off in Mode 5
- [ ] LED color write accepted (0-15)
- [ ] LED color write rejected (> 15)
- [ ] LED brightness write accepted (10-30)
- [ ] LED brightness write rejected (< 10)
- [ ] LED brightness write rejected (> 30)
- [ ] LED color changes immediately in Mode 5 when enabled
- [ ] LED brightness changes immediately in Mode 5 when enabled
- [ ] LED controls only affect Mode 5 (not other modes)

### Write Operations - PWM Intensity
- [ ] PWM intensity write accepted (30-90)
- [ ] PWM intensity write rejected (< 30)
- [ ] PWM intensity write rejected (> 90)
- [ ] PWM intensity changes motor strength immediately in Mode 5

### System Behavior
- [ ] Status LED blinks on mode change
- [ ] Advertising timeout after 5 minutes
- [ ] Button hold (1-2s) re-enables advertising
- [ ] Device survives deep sleep/wake cycle

## Conclusion

This implementation provides a complete BLE GATT service for configuring the EMDR device's Mode 5 (Custom) motor timing and LED feedback via mobile app. The service includes 9 characteristics across 3 categories:
- **Motor Control:** Mode selection, custom frequency/duty cycle, PWM intensity (30-90%)
- **LED Control:** Enable/disable, 16-color palette, configurable brightness (10-30%)
- **Status Monitoring:** Battery level, session time

All JPL coding standards are followed, with comprehensive error checking, input validation, and logging. The system is production-ready for research applications studying motor duty cycle effects and LED feedback on therapeutic efficacy.

**Key Features:**
- 16-color LED palette optimized for WS2812B
- Brightness range (10-30%) prevents excessive power consumption
- LED controls only apply to Mode 5 (preserves existing mode behavior)
- All settings have TODO markers for future motor task integration

**Next Steps:**
1. Integrate LED control with motor task (apply color/brightness in Mode 5)
2. Add NVS persistence for custom settings (motor + LED)
3. Implement BLE notifications for battery/session time
4. Consider adding motor intensity characteristic
5. Evaluate BLE security requirements for clinical use
