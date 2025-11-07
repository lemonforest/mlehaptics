# Debug Serial Output Guide - Single Device Demo Test

## 🎯 What Serial Output to Expect

### At Power-On/Reset (One-Time Startup Banner)
```
================================================
=== EMDR Single Device Demo Test ===
=== Research Study: Motor Duty Cycle Effects ===
================================================
Board: Seeed Xiao ESP32C6
Framework: ESP-IDF v5.5.0
Session Duration: 20 minutes
Modes: 4 (frequency × duty cycle matrix)

Wake up! Reason: Power-on or reset

=== Mode Configuration ===
Mode 1: 1Hz@50% (250ms motor, 249ms coast per half-cycle)
Mode 2: 1Hz@25% (125ms motor, 374ms coast per half-cycle)
Mode 3: 0.5Hz@50% (500ms motor, 499ms coast per half-cycle)
Mode 4: 0.5Hz@25% (250ms motor, 749ms coast per half-cycle)

Starting Mode: Mode 1 (1Hz@50%)
LED Indication: 10 seconds (resets on button press)
LED Brightness: 20% RED for mode indication
Motor Intensity: 60% PWM

Press button: Cycle through modes
Hold button 5s: Emergency sleep

Initializing remaining hardware...
GPIO initialized
WS2812B initialized
PWM initialized: 25kHz, 60% intensity
RTC wake configured: GPIO1 (wake on LOW)
Hardware initialized successfully

=== Session Start ===

Session coordinator task started
Button task started
LED task started
Motor task started
All tasks created - motor and LED running independently

=== 20-Minute Session Started ===
Starting Mode: 1Hz@50%
```

---

## 📊 NEW: Debug Timing Logs (First 3 Seconds Only)

### What You'll See Now:
```
[MOTOR] Cycle 0 start: time=0
[LED] time=520, cycle_pos=520, phase=FWD, in_phase=520, motor=OFF
[MOTOR] Cycle 1 start: time=1000
[LED] time=1020, cycle_pos=20, phase=FWD, in_phase=20, motor=ON
[MOTOR] Cycle 2 start: time=2000
[LED] time=2020, cycle_pos=20, phase=FWD, in_phase=20, motor=ON
```

**This lets you see:**
- ✅ When motor starts each full cycle (FORWARD → REVERSE)
- ✅ What LED *thinks* motor is doing (calculated timing)
- ✅ Any timing drift between tasks

---

## 🔇 During Normal Operation (10s - 19min)

**COMPLETE SILENCE!** No logs = device running normally.

This is intentional for:
- Battery conservation
- Clean serial output
- Performance

---

## 🔔 Event-Triggered Logs

### Button Press (Mode Switch)
```
Mode switched to: 1Hz@25%
```
*Debug logs restart for 3 seconds after mode switch*

### Button Hold (5 seconds)
```
Button held for 5000ms - entering sleep

Entering deep sleep sequence...
Waiting for button release...
Button released!
Entering deep sleep...
Press button to wake and start new session
```

### Session Complete (20 minutes)
```
Session complete! (20 minutes)

Entering deep sleep sequence...
Entering deep sleep...
Press button to wake and start new session
```

---

## 🔍 How to Use Debug Logs to Fix LED Sync

### ✅ Expected Pattern (Mode 1: 1Hz@50%)

**Full cycle = 1000ms (500ms FWD + 500ms REV)**

| Time (ms) | Motor Cycle | Motor Phase | LED Should Show |
|-----------|-------------|-------------|-----------------|
| 0-250     | Cycle 0     | FWD ON      | ON (FWD, 0-250ms) |
| 250-499   | Cycle 0     | FWD COAST   | OFF (FWD, 250-499ms) |
| 500-750   | Cycle 0     | REV ON      | ON (REV, 0-250ms) |
| 750-1000  | Cycle 0     | REV COAST   | OFF (REV, 250-499ms) |
| 1000-1250 | Cycle 1     | FWD ON      | ON (FWD, 0-250ms) |

### 🐛 If LED is Out of Sync:

**Look for these clues in debug output:**

1. **LED shows "motor=ON" when cycle_pos shows coast range**
   - Problem: LED calculation wrong
   - Fix: Adjust `motor_on` calculation

2. **Motor cycles don't align with 1000ms intervals**
   - Problem: Task delays not matching config
   - Fix: Check motor_on_ms + coast_ms + dead_time math

3. **LED phase shows "FWD" when motor just started REV**
   - Problem: LED half-cycle calculation wrong
   - Fix: Check `is_forward` logic

---

## 🎬 Testing Procedure

### Step 1: Flash and Monitor
```bash
pio run -t upload -t monitor
```

### Step 2: Immediately Observe First 3 Seconds
- Should see startup banner
- Should see ~6 `[MOTOR]` logs (one per cycle start)
- Should see ~6 `[LED]` logs (every 500ms)

### Step 3: Compare Timestamps
- Are motor cycles 1000ms apart? (Mode 1)
- Does LED cycle_pos match expected range?
- Does LED motor=ON/OFF match actual vibration?

### Step 4: Test Mode Switch
- Press button
- Should see "Mode switched to: [name]"
- Debug logs restart for 3 more seconds
- Verify new timing (Mode 2 = 1000ms, Mode 3/4 = 2000ms cycles)

### Step 5: Physical Verification
- **Hold device while looking at LED**
- Does LED blink match vibration pulse?
- If not, note the timing offset

---

## 📝 Report Format for Debug Session

When posting results, please include:

```
Device: [ESP32C6]
Mode Tested: [Mode 1/2/3/4]
Issue: [LED blinks too early/late/wrong pattern]

Debug Logs (first 3 seconds):
[paste logs here]

Physical Observation:
- LED blinks: [describe pattern]
- Motor vibrates: [describe pattern]
- Sync: [YES / NO - LED is X ms early/late]
```

This format helps identify:
- Calculation errors in LED task
- Timing drift from FreeRTOS delays
- Off-by-one errors in phase detection

---

## ⚠️ Known Timing Caveats

1. **FreeRTOS tick precision**: 
   - `portTICK_PERIOD_MS` may round
   - Expect ±1-10ms jitter

2. **Task scheduling**:
   - Motor task priority: 4
   - LED task priority: 3
   - Motor may occasionally preempt LED calculation

3. **Watchdog resets**:
   - Motor task splits long delays
   - May introduce tiny delays

**These are normal and expected!** Look for consistent offsets, not jitter.

---

## 🎯 Success Criteria

✅ **LED synced if:**
- LED ON matches start of motor pulse (±50ms tolerance)
- LED OFF matches end of motor pulse
- Pattern consistent across all 4 modes
- No visible drift after 10 seconds

---

## 🔧 After Fixing (Disable Debug Logs)

Once synced, remove debug logs by commenting out:
```c
// if (elapsed_since_mode_switch < 3000 && (current_time - last_log_time) >= 500) {
//     ESP_LOGI(TAG, "[LED] ...");
// }
```

This reduces power consumption and keeps serial clean.
