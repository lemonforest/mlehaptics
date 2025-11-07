# Button Debug Testing Guide

## 🐛 Added Debug Logging to Button Task

### What Was Added:
1. **Initial heartbeat** - confirms task started and GPIO state
2. **State change logging** - every time GPIO changes (1→0 or 0→1)
3. **Press detection** - logs when button pressed
4. **Hold duration** - logs every 1 second while holding
5. **Release logging** - logs duration when button released
6. **Periodic heartbeat** - logs every 10 seconds to prove task is alive
7. **Mode switch confirmation** - explicitly says verbose logging restarted

---

## 🧪 Testing Procedure

### Step 1: Reset Device and Capture Full Startup
```bash
# Option A: Hardware reset
Press RESET button on ESP32C6 while monitor is running

# Option B: Software reset
In PlatformIO monitor, press: Ctrl+T then R

# Option C: Replug USB
Unplug and replug USB cable
```

**Expected startup logs (what you missed before):**
```
================================================
=== EMDR Single Device Demo Test ===
...
Button task started
[BUTTON] Task alive, GPIO1=1
LED task started (Direct Notification mode)
Motor task started (with Direct Notification to LED)
...
[MOTOR] Cycle 0 start: time=0
[LED] Notification #1: motor=ON at time=5
```

---

### Step 2: Test Button Press (Short Press)

**Action:** Press and release button quickly (<5 seconds)

**Expected logs:**
```
[BUTTON] State change: 1 -> 0
[BUTTON] Press detected at 5432 ms
[BUTTON] State change: 0 -> 1
[BUTTON] Released after 123 ms
Mode switched to: 1Hz@25%
[BUTTON] Verbose logging restarted for 3 seconds
[LED] Notification #X: motor=ON at time=...
[MOTOR] Cycle X start: time=...
```

**If nothing appears:**
- Task may have crashed
- GPIO not connected
- Button hardware issue

---

### Step 3: Test Button Hold (5 Second Hold)

**Action:** Press and HOLD button for 5+ seconds

**Expected logs:**
```
[BUTTON] State change: 1 -> 0
[BUTTON] Press detected at 8765 ms
[BUTTON] Holding for 1000 ms...
[BUTTON] Holding for 2000 ms...
[BUTTON] Holding for 3000 ms...
[BUTTON] Holding for 4000 ms...
[BUTTON] Holding for 5000 ms...
Button held for 5000ms - entering sleep

Entering deep sleep sequence...
Waiting for button release...
```

---

### Step 4: Check Heartbeat (Wait 10 Seconds)

**Action:** Do nothing, just wait

**Expected logs (every 10 seconds):**
```
[BUTTON] Task heartbeat - still monitoring GPIO1
```

**If missing:**
- Button task crashed (watchdog should have caught this)
- Task was deleted somehow

---

## 🔍 Diagnostic Scenarios

### Scenario 1: No Button Logs at All
```
# Only motor/LED logs, no [BUTTON] logs
[LED] Notification #5: motor=ON at time=123
[MOTOR] Cycle 1 start: time=456
```

**Diagnosis:** Button task never started or crashed immediately

**Fix:**
- Check task creation order in `app_main()`
- Check stack overflow (increase button_task stack from 3072)
- Check if GPIO1 is valid on your board

---

### Scenario 2: Task Alive, But No State Changes
```
[BUTTON] Task alive, GPIO1=1
[BUTTON] Task heartbeat - still monitoring GPIO1
[BUTTON] Task heartbeat - still monitoring GPIO1
# <you press button, nothing happens>
```

**Diagnosis:** GPIO not responding to physical button

**Possible causes:**
- Button not wired to GPIO1
- Button stuck HIGH (no pullup, or wiring issue)
- GPIO1 used by something else (USB? JTAG?)

**Test:** Manually short GPIO1 to GND with a wire

---

### Scenario 3: State Changes, But Wrong Polarity
```
[BUTTON] Task alive, GPIO1=0  # <-- Should be 1!
[BUTTON] State change: 0 -> 1  # <-- Backwards!
```

**Diagnosis:** Button is active-HIGH instead of active-LOW

**Fix:** Button is wired backwards or no pullup resistor

---

### Scenario 4: Constant Toggling
```
[BUTTON] State change: 1 -> 0
[BUTTON] State change: 0 -> 1
[BUTTON] State change: 1 -> 0
[BUTTON] State change: 0 -> 1
```

**Diagnosis:** Floating GPIO (no pullup) or button bouncing

**Fix:**
- Check pullup resistor (10kΩ)
- GPIO config has `pull_up_en = GPIO_PULLUP_ENABLE` ✓
- May need larger debounce time

---

### Scenario 5: Press Detected, But No Mode Switch
```
[BUTTON] State change: 1 -> 0
[BUTTON] Press detected at 5432 ms
[BUTTON] State change: 0 -> 1
[BUTTON] Released after 45 ms
# <-- No "Mode switched to" message
```

**Diagnosis:** Duration < 50ms (BUTTON_DEBOUNCE_MS)

**Fix:** Press longer, or reduce debounce time

---

## 🎯 What to Report Back

Please paste your full serial output showing:
1. ✅ Startup banner (after reset)
2. ✅ First 3 seconds of motor/LED logs
3. ✅ Button task startup
4. ✅ What happens when you press button

**Format:**
```
=== FULL SERIAL LOG ===
[paste everything from reset to button press]

=== BUTTON PRESS TEST ===
Action: Short press
Result: [paste logs or "nothing happened"]

Action: 5-second hold
Result: [paste logs or "nothing happened"]

=== PHYSICAL OBSERVATIONS ===
- LED blinking: YES/NO - [describe pattern]
- Motor vibrating: YES/NO - [describe pattern]
- Button feels: [normal/sticky/no click/etc]
- LED/motor sync: [perfect/early/late/random]
```

This will help diagnose:
- Is button task running?
- Is GPIO responding?
- Is button wired correctly?
- Are notifications working?
- Is LED/motor synced?

---

## ⚡ Quick GPIO1 Hardware Check

**If button completely unresponsive:**

1. **Verify GPIO1 is available:**
   - ESP32C6 datasheet: GPIO1 should be general purpose
   - Not used by USB-JTAG on Xiao ESP32C6

2. **Test with multimeter:**
   - Measure GPIO1 voltage: should be ~3.3V (pulled HIGH)
   - Press button: should drop to ~0V (GND)

3. **Test with scope/logic analyzer:**
   - Look for clean transitions (no bouncing)
   - Verify rise/fall times

4. **Bypass code temporarily:**
   Add to `app_main()` before tasks:
   ```c
   while(1) {
       int level = gpio_get_level(GPIO_BUTTON);
       ESP_LOGI(TAG, "GPIO1 = %d", level);
       vTaskDelay(pdMS_TO_TICKS(100));
   }
   ```
   This proves GPIO reads work independently of FreeRTOS tasks.
