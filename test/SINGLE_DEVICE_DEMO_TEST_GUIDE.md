# Single Device Demo Test Guide
**Simple 4-Mode EMDR Research Study**

**Board:** Seeed Xiao ESP32-C6  
**Framework:** ESP-IDF v5.5.0  
**Date:** November 2, 2025  
**Version:** 2.0 (Simplified - No WDT Complexity)

---

## Overview

This test implements a standalone 20-minute EMDR session with 4 different motor patterns to research the effects of duty cycle and frequency on therapeutic effectiveness and battery life.

**Key Features:**
- ✅ 4 research modes (frequency × duty cycle matrix)
- ✅ LED visual feedback synced with motor pattern
- ✅ Button mode cycling with instant LED reset
- ✅ 20-minute automatic session
- ✅ Emergency shutdown (5 seconds total)
- ✅ Purple blink shutdown pattern
- ✅ Simple architecture (no WDT complexity)

---

## Research Design - Four Modes

### Mode Configuration

| Mode | Frequency | Duty Cycle | Motor ON | Coast | Cycle Time |
|------|-----------|------------|----------|-------|------------|
| **Mode 1** | 1Hz | 50% | 250ms | 250ms | 1000ms |
| **Mode 2** | 1Hz | 25% | 125ms | 375ms | 1000ms |
| **Mode 3** | 0.5Hz | 50% | 500ms | 500ms | 2000ms |
| **Mode 4** | 0.5Hz | 25% | 250ms | 750ms | 2000ms |

### Research Questions

1. **Duty Cycle Effect:** Does 25% duty maintain therapeutic effectiveness vs 50%?
2. **Frequency Effect:** Does 0.5Hz feel different from traditional 1Hz?
3. **Battery Optimization:** How much battery life gained at 25% duty?
4. **User Preference:** Which mode feels most effective/comfortable?
5. **Motor Longevity:** Does reduced duty extend motor lifespan?

### Expected Power Consumption

```
Mode 1 (1Hz @ 50%):  ~65mA average → ~22mAh per 20min session
Mode 2 (1Hz @ 25%):  ~43mA average → ~14mAh per 20min session (36% savings!)
Mode 3 (0.5Hz @ 50%): ~65mA average → ~22mAh per 20min session
Mode 4 (0.5Hz @ 25%): ~43mA average → ~14mAh per 20min session (36% savings!)

Deep Sleep: <1mA
```

---

## Hardware Configuration

### GPIO Assignments

| GPIO | Function | Description |
|------|----------|-------------|
| **GPIO1** | Button | Hardware pull-up, RTC wake source |
| **GPIO15** | Status LED | Reserved (not used in this test) |
| **GPIO16** | WS2812B Power | P-MOSFET gate (ACTIVE LOW) |
| **GPIO17** | WS2812B DIN | LED data line |
| **GPIO19** | H-Bridge IN2 | LEDC PWM reverse control |
| **GPIO20** | H-Bridge IN1 | LEDC PWM forward control |

### Motor Control

- **PWM Frequency:** 25kHz (above human hearing)
- **PWM Resolution:** 10-bit (0-1023 range)
- **PWM Intensity:** 60% duty cycle
- **Control Method:** LEDC peripheral (hardware PWM)

### LED Configuration

- **Type:** WS2812B RGB addressable LED
- **Brightness:** 20% (battery optimization + case transmittance)
- **Color:** RED @ 20% for mode indication
- **Pattern:** Blinks in sync with motor (ON during pulse, OFF during coast)

---

## Operation Guide

### Power-On Behavior

1. ESP32-C6 boots and initializes
2. GPIO16 LOW → WS2812B powered
3. PWM and LED initialized
4. **Mode 1** selected by default
5. LED blinks RED in sync with motor for 10 seconds
6. Session starts

### LED Visual Feedback (Critical Feature!)

**During First 10 Seconds:**
The LED blinks in perfect sync with the motor pattern, giving instant visual confirmation of the duty cycle.

**Mode 1 (1Hz @ 50%):**
```
LED:   [====250ms RED====][250ms OFF][====250ms RED====][250ms OFF]
Motor: [====250ms FWD=====][250ms OFF][====250ms REV=====][250ms OFF]
Visual: Balanced blink - 50% on, 50% off
```

**Mode 2 (1Hz @ 25%):**
```
LED:   [==125ms RED==][375ms OFF][==125ms RED==][375ms OFF]
Motor: [==125ms FWD==][375ms OFF][==125ms REV==][375ms OFF]
Visual: Short blinks - 25% on, 75% off
```

**Mode 3 (0.5Hz @ 50%):**
```
LED:   [======500ms RED======][500ms OFF][======500ms RED======][500ms OFF]
Motor: [======500ms FWD======][500ms OFF][======500ms REV======][500ms OFF]
Visual: Long slow pulses - half time on, slower rhythm
```

**Mode 4 (0.5Hz @ 25%):**
```
LED:   [==250ms RED==][750ms OFF][==250ms RED==][750ms OFF]
Motor: [==250ms FWD==][750ms OFF][==250ms REV==][750ms OFF]
Visual: Brief flashes with long gaps - most efficient
```

**After 10 Seconds:**
- LED turns OFF (battery conservation)
- Motor continues running in selected mode

**Last Minute (19:00-20:00):**
- LED blinks slowly at 1Hz (universal "session ending" warning)
- Independent of current mode

### Button Controls

**Short Press (< 1 second):**
- Cycles to next mode: Mode 1 → 2 → 3 → 4 → 1
- LED indication resets to 10 seconds
- Console shows: "Mode: [mode_name]"
- Session timer continues (does NOT reset)

**Hold 5 Seconds (Emergency Shutdown):**
1. Hold button for 1 second
2. "Hold detected! Emergency shutdown..." appears
3. Countdown: "4...3...2...1..."
4. Can release during countdown to cancel
5. After countdown: Motor stops, purple blink starts
6. Release button → Enter deep sleep

**During Countdown:**
- Can release button to cancel shutdown
- "Cancelled!" message appears
- Returns to normal operation

### Session Timeline (20 Minutes)

```
[0:00 - 0:10]   LED ON: Blinks with motor pattern (mode indicator)
[0:10 - 19:00]  LED OFF: Battery conservation, motor only
[19:00 - 20:00] LED BLINK: 1Hz slow blink warning (session ending)
[20:00]         AUTO SLEEP: Purple blink, wait for release, then sleep
```

### Deep Sleep Entry

**Automatic (20 minutes elapsed):**
1. Motor coasts immediately
2. Purple blink pattern starts
3. Wait for button release
4. LED off, WS2812B unpowered
5. Enter deep sleep (<1mA)

**Manual (5-second hold):**
- Same sequence as automatic
- Session ends prematurely

**Wake-Up:**
- Press button → Device wakes
- Returns to Mode 1
- New 20-minute session starts

---

## Build and Run

### Build Commands

```bash
# Clean build (recommended for first build)
pio run -e single_device_demo_test -t clean

# Build and upload
pio run -e single_device_demo_test -t upload && pio device monitor

# Quick rebuild
pio run -e single_device_demo_test -t upload && pio device monitor
```

### Expected Console Output

**Power-On:**
```
================================================
=== Single Device Demo Test ===
=== Simple 4-Mode Research (No WDT) ===
================================================
Board: Seeed Xiao ESP32C6
Session: 20 minutes

Modes:
  1. 1Hz@50%
  2. 1Hz@25%
  3. 0.5Hz@50%
  4. 0.5Hz@25%

Controls:
  - Press button: Cycle modes
  - Hold 5s: Emergency shutdown (1s + 4s countdown)

LED Indication:
  - First 10s: RED blinks with motor pattern
  - Button press: LED resets to 10s
  - After 10s: LED off (battery saving)
  - Last minute: Slow warning blink

Wake: Power on

Initializing hardware...
GPIO initialized
LED initialized
PWM initialized: 25kHz, 60%
Hardware ready!

=== Session Start ===

Button task started
Motor task started
Mode: 1Hz@50%
```

**Mode Change:**
```
Mode: 1Hz@25%
```

**10-Second Mark:**
```
LED off (battery conservation)
```

**Emergency Shutdown:**
```
Hold detected! Emergency shutdown...
4...
3...
2...
1...

Entering deep sleep sequence...
Waiting for button release...
(Purple blink - release when ready)
Button released!
Entering deep sleep...
Press button to wake
```

---

## Testing Procedures

### Functional Testing

**Test 1: Mode Cycling**
1. Power on device
2. Observe Mode 1 LED pattern (250ms on/off)
3. Press button
4. Verify Mode 2 LED pattern (125ms on, 375ms off)
5. Press button twice more
6. Verify returns to Mode 1

**Expected:** LED blink patterns should be visually distinct for each mode

**Test 2: LED Indication Window**
1. Power on device
2. Count 10 seconds
3. Verify LED turns off at 10 seconds
4. Press button to change mode
5. Verify LED comes back on for 10 seconds
6. Verify new mode pattern is shown

**Expected:** LED always resets to 10 seconds on mode change

**Test 3: Emergency Shutdown**
1. During session, hold button
2. After 1 second, see "Hold detected!" message
3. See countdown: 4...3...2...1...
4. Release button during purple blink
5. Device enters sleep

**Expected:** Total hold time = 5 seconds from start to shutdown

**Test 4: Shutdown Cancellation**
1. Hold button for 1 second
2. During countdown (e.g., at "2..."), release button
3. Verify "Cancelled!" message
4. Verify session continues normally

**Expected:** Can cancel at any time during countdown

**Test 5: 20-Minute Session**
1. Start session
2. Let run for 20 minutes (or use shorter time for testing)
3. At 19 minutes, verify LED warning blink starts
4. At 20 minutes, verify auto-shutdown

**Expected:** Session ends exactly at 20 minutes

**Test 6: Wake from Sleep**
1. Complete any shutdown sequence
2. Verify purple blink and sleep entry
3. Press button
4. Verify device wakes
5. Verify Mode 1 is active
6. Verify new session starts

**Expected:** Clean wake and restart in Mode 1

### Research Data Collection

**For Each Mode, Record:**

**Quantitative:**
- Battery consumption (mAh) via USB power meter
- Average current draw (mA)
- Motor temperature (infrared thermometer)
- LED visibility through case (1-10 scale)

**Qualitative (1-10 scale):**
- Intensity: How strong does the stimulation feel?
- Comfort: How comfortable over 20 minutes?
- Rhythm: Does the rhythm feel appropriate?
- Effectiveness: Does it "feel" therapeutic?

**Data Collection Form:**
```
Session Date: ___________
Mode Tested: ___________
Battery Start: _____ mAh
Battery End: _____ mAh
Battery Used: _____ mAh
Motor Temp: _____ °C

Intensity (1-10): _____
Comfort (1-10): _____
Rhythm (1-10): _____
Effectiveness (1-10): _____

Notes:
_________________________________
```

---

## Troubleshooting

### Motor Not Running

**Symptom:** No motor movement in any mode

**Possible Causes:**
1. LEDC PWM not initializing
2. H-bridge power supply issue
3. GPIO19/GPIO20 not outputting PWM

**Debug Steps:**
```bash
# Check console for initialization
PWM initialized: 25kHz, 60%

# Verify GPIO output with oscilloscope
# Should see 25kHz PWM at 60% duty on GPIO19/20
```

### LED Not Showing Pattern

**Symptom:** LED stays on/off or doesn't blink correctly

**Possible Causes:**
1. WS2812B power control issue (GPIO16)
2. LED indication timing logic error
3. LED strip not initializing

**Debug Steps:**
1. Verify GPIO16 is LOW during first 10 seconds
2. Add debug logging to motor_task LED control
3. Check console: "LED initialized"

### Button Not Cycling Modes

**Symptom:** Button press doesn't change modes

**Possible Causes:**
1. Button debounce too aggressive
2. Button hold time detection interfering
3. GPIO1 pull-up not working

**Debug Steps:**
1. Check console for "Mode: [name]" messages
2. Verify button press duration (should be < 1 second)
3. Test with multimeter: Button should go from 3.3V → 0V when pressed

### Shutdown Takes 10 Seconds

**Symptom:** Emergency shutdown requires 10 seconds instead of 5

**Status:** This was fixed in v2.0!
- Old version: 5s hold detection + 5s countdown = 10s total
- New version: 1s hold detection + 4s countdown = 5s total

**Verify Fix:**
Check constants in code:
```c
#define BUTTON_HOLD_MS          1000    // Should be 1000, not 5000
#define BUTTON_COUNTDOWN_SEC    4       // Should be 4, not 5
```

### Session Doesn't Last 20 Minutes

**Symptom:** Session ends early or runs too long

**Debug Steps:**
1. Add minute markers to console:
   ```c
   if (elapsed % 60000 == 0) {
       ESP_LOGI(TAG, "Minute: %d", elapsed / 60000);
   }
   ```
2. Verify SESSION_DURATION_MS = 1200000 (20 × 60 × 1000)
3. Use stopwatch to measure actual time

---

## Technical Specifications

### Timing Parameters

```c
// Session
#define SESSION_DURATION_MS     1200000  // 20 minutes
#define LED_INDICATION_TIME_MS  10000    // 10 seconds
#define WARNING_START_MS        1140000  // Start at 19 minutes

// Button
#define BUTTON_DEBOUNCE_MS      50       // 50ms debounce
#define BUTTON_HOLD_MS          1000     // 1s before countdown
#define BUTTON_COUNTDOWN_SEC    4        // 4s countdown (5s total)

// LED
#define WS2812B_BRIGHTNESS      20       // 20% brightness
#define PURPLE_BLINK_MS         200      // 5Hz purple blink
```

### Power Budget

```
Active Operation (Mode 1 - worst case):
- ESP32-C6: ~20mA
- Motor: ~90mA × 50% duty = ~45mA average
- LED (during 10s): ~10mA
- Total: ~75mA peak, ~65mA average

Active Operation (Mode 4 - best case):
- ESP32-C6: ~20mA
- Motor: ~90mA × 25% duty = ~23mA average
- LED (during 10s): ~10mA
- Total: ~53mA peak, ~43mA average

Deep Sleep:
- <1mA total (WS2812B unpowered)
```

### Battery Life Estimates (dual 320mAh batteries - 640mAh total)

```
Mode 1 (1Hz @ 50%):  22mAh/session → ~16 sessions per charge
Mode 2 (1Hz @ 25%):  14mAh/session → ~25 sessions per charge (56% more!)
Mode 3 (0.5Hz @ 50%): 22mAh/session → ~16 sessions per charge
Mode 4 (0.5Hz @ 25%): 14mAh/session → ~25 sessions per charge (56% more!)
```

---

## Comparison to Old Version

### What Changed from v1.0?

**Removed (Complexity Reduction):**
- ❌ Task Watchdog Timer (WDT) requirements
- ❌ FreeRTOS task synchronization with notifications
- ❌ Complex task coordination for shutdown
- ❌ JPL coding standard enforcement
- ❌ Adaptive watchdog feeding strategies

**Kept (Working Features):**
- ✅ 4-mode research design
- ✅ LED visual feedback (now synced better!)
- ✅ Button cycling and hold detection
- ✅ Purple blink shutdown pattern
- ✅ 20-minute session timer
- ✅ Deep sleep power management

**Improved:**
- ✅ Shutdown timing: Now truly 5 seconds (was 10 seconds)
- ✅ LED synchronization: Perfect sync via single task (no drift)
- ✅ Code simplicity: Much easier to understand and modify
- ✅ Reliability: Fewer moving parts = fewer failure modes

### Why the Simplified Approach Works

**No Drift Problem:**
- Old version: Separate motor task + LED task → needed sync
- New version: Single motor task controls both → perfect sync automatically

**No Watchdog Needed:**
- Longest delay: 500ms (Mode 3 motor pulse)
- FreeRTOS watchdog: 2000ms timeout (default)
- Margin: 1500ms (3× safety factor)
- Result: Never hits watchdog timeout naturally

**Architecture:**
```
Old (Complex):
├─ Motor Task (watchdog subscriber)
├─ LED Task (watchdog subscriber)
├─ Session Coordinator Task
├─ Button Task
└─ Task Notifications for sync

New (Simple):
├─ Motor Task (controls motor + LED together)
└─ Button Task (handles mode changes)
```

---

## Future Enhancements

### Phase 2 Research

1. **Intensity Variation:** Test 40%, 60%, 80% PWM at optimal mode
2. **Asymmetric Patterns:** Different duty for forward vs reverse
3. **Haptic Pulses:** Short burst patterns within cycles
4. **Adaptive Duty:** Start high, reduce as user habituates

### Hardware Improvements

1. **Current Sensing:** Measure actual motor current per mode
2. **Temperature Monitoring:** Track motor temperature over session
3. **Battery Telemetry:** Real-time voltage and SOC
4. **Accelerometer:** Measure actual vibration intensity

### Software Enhancements

1. **Session Statistics:** Track mode usage and preferences
2. **Pattern Library:** Save and load custom patterns
3. **Mobile App:** Remote control and data logging
4. **Bluetooth Pairing:** Sync two devices for true bilateral

---

## Success Criteria

This test is successful when:

1. ✅ All 4 modes run for full 20 minutes without crashes
2. ✅ Mode transitions work smoothly and instantly
3. ✅ LED indication clearly shows duty cycle visually
4. ✅ Emergency shutdown works in exactly 5 seconds
5. ✅ Deep sleep and wake function reliably
6. ✅ Measurable battery difference between modes
7. ✅ Users can collect meaningful research data

---

## Related Documentation

- **Research Specification:** `docs/SINGLE_DEVICE_DEMO_RESEARCH_SPEC.md`
- **Architecture Decisions:** `docs/architecture_decisions.md`
- **GPIO Mapping:** `docs/GPIO_UPDATE_2025-10-17.md`
- **Build Commands:** `BUILD_COMMANDS.md`
- **Reference Tests:**
  - `test/hbridge_pwm_test.c` - Motor PWM control
  - `test/ws2812b_test.c` - LED control and purple blink
  - `test/button_deepsleep_test.c` - Button and sleep patterns

---

## Version History

**v2.0 (November 2, 2025) - Simplified Architecture**
- Removed WDT complexity
- Fixed 5-second shutdown (was 10 seconds)
- Improved LED sync (single task approach)
- Simplified code structure

**v1.0 (October 21, 2025) - Initial Implementation**
- Complex WDT-compliant version
- Task synchronization with notifications
- 10-second shutdown issue
- JPL coding standard enforcement

---

**Test Status:** ✅ Working and Validated  
**Next Steps:** Collect research data, compare modes, analyze results

---

*Generated with assistance from Claude Sonnet 4 (Anthropic)*
