# Battery Voltage Test with LVO Protection - Quick Reference

## Overview
Hardware test for Seeed Xiao ESP32C6 battery voltage monitoring with Low Voltage Cutout (LVO) protection.

## Test Purpose
Verify battery protection and monitoring before implementing main program power management:
- ✅ Low Voltage Cutout (LVO) at 3.2V threshold
- ✅ Visual warning (3 blinks) for 3.0V ≤ voltage < 3.2V
- ✅ No visual warning for voltage < 3.0V (battery protection)
- ✅ Battery voltage monitoring every 1000ms
- ✅ 20-minute session runtime limit
- ✅ Elapsed time tracking (MM:SS format)
- ✅ Graceful shutdown and deep sleep entry
- ✅ Button hold (5s) for manual sleep entry

## Build & Upload

### Quick Start
```bash
# Windows Command Prompt or PowerShell
pio run -e battery_voltage_test -t upload && pio device monitor
```

### Build System Details
This test uses the ESP-IDF v5.3.0 CMake build system with automatic source file selection:
- Python script (`scripts/select_source.py`) runs before each build
- Script detects environment name: `battery_voltage_test`
- Automatically configures `src/CMakeLists.txt` to build `test/battery_voltage_test.c`
- No manual CMakeLists.txt editing required

## Test Behavior

### Scenario 1: Normal Operation (Voltage ≥ 3.2V)

#### Initial Power-On
```
=== Battery Voltage Monitor Hardware Test ===
Board: Seeed Xiao ESP32C6
Framework: ESP-IDF v5.5.0

GPIO Configuration:
  Battery voltage: GPIO2 (ADC1_CH2)
  Battery enable: GPIO21 (HIGH=enabled)
  Button: GPIO1 (wake source)
  Status LED: GPIO15 (active LOW)

Checking battery voltage for LVO...
LVO check: Battery voltage = 3.85V [85%]
LVO check: PASSED - voltage OK for operation

Battery monitoring task started
Session duration: 20 minutes
Reading battery voltage every 1000ms...

Battery: 3.85V (Raw: 2.89V at GPIO2) [85%] - 0:01 elapsed
Battery: 3.84V (Raw: 2.88V at GPIO2) [84%] - 0:02 elapsed
Battery: 3.84V (Raw: 2.88V at GPIO2) [84%] - 0:03 elapsed
...
```

#### 20-Minute Auto Shutdown
```
Battery: 3.68V (Raw: 2.76V at GPIO2) [68%] - 19:57 elapsed
Battery: 3.68V (Raw: 2.76V at GPIO2) [68%] - 19:58 elapsed
Battery: 3.67V (Raw: 2.76V at GPIO2) [67%] - 19:59 elapsed

============================================
   20-MINUTE SESSION COMPLETE
============================================
Session duration: 20 minutes
Total readings: 1200
Final battery: 3.67V [67%]

Gracefully entering deep sleep...
Press button to wake and start new session
============================================

[Serial output stops - device is asleep]
```

### Scenario 2: LVO Warning (3.0V ≤ voltage < 3.2V)

#### Wake from Deep Sleep - Low Battery
```
ESP-ROM:esp32c6-20220919
...
=== Battery Voltage Monitor Hardware Test ===
...

Checking battery voltage for LVO...
LVO check: Battery voltage = 3.15V [15%]

============================================
   LOW VOLTAGE CUTOUT (LVO) TRIGGERED
============================================
Battery voltage: 3.15V (threshold: 3.20V)
Entering deep sleep to protect battery
Providing visual warning (3 blinks)...
[LED blinks 3 times: ON 200ms, OFF 200ms]
Charge battery to at least 3.20V to resume operation
============================================

[Serial output stops - device is asleep]
```

### Scenario 3: Critical Low Voltage (voltage < 3.0V)

#### Wake from Deep Sleep - Critical Battery
```
ESP-ROM:esp32c6-20220919
...
=== Battery Voltage Monitor Hardware Test ===
...

Checking battery voltage for LVO...
LVO check: Battery voltage = 2.85V [0%]

============================================
   LOW VOLTAGE CUTOUT (LVO) TRIGGERED
============================================
Battery voltage: 2.85V (threshold: 3.20V)
Entering deep sleep to protect battery
Battery critically low (2.85V) - no visual warning
Charge battery to at least 3.20V to resume operation
============================================

[Serial output stops - device is asleep]
[NO LED blinks - protecting battery]
```

### Scenario 4: Manual Button Sleep (Anytime)

#### Button Hold During Session
```
Battery: 3.75V (Raw: 2.81V at GPIO2) [75%] - 5:23 elapsed
Battery: 3.75V (Raw: 2.81V at GPIO2) [75%] - 5:24 elapsed

Hold button for deep sleep...
5... 4... 3... 2... 1...

Waiting for button release...
(LED will blink - release button when ready)
[LED blinks until button released]
Button released!

===========================================
Entering ultra-low power deep sleep mode...
===========================================
Press button (GPIO1) to wake device

[Serial output stops - device is asleep]
```

## GPIO Configuration

| GPIO | Function | Mode | Details |
|------|----------|------|---------|
| GPIO1 | Button | Input | RTC GPIO, hardware pull-up, 50ms debounce, wake source |
| GPIO2 | Battery ADC | Input | ADC1_CH2, resistor divider (3.3kΩ / 10kΩ) |
| GPIO15 | Status LED | Output | Active LOW (0=ON, 1=OFF), used for LVO warning |
| GPIO21 | Battery Enable | Output | P-MOSFET gate, HIGH=enabled, 1% duty cycle |

## LVO Thresholds

| Voltage Range | Behavior | Visual Feedback |
|---------------|----------|-----------------|
| ≥ 3.2V | Normal operation | LED stays OFF during monitoring |
| 3.0V - 3.2V | LVO triggered, enter sleep | 3 blinks on GPIO15 (200ms ON/OFF) |
| < 3.0V | LVO triggered, enter sleep | NO blinks (protect battery) |

## Battery Voltage Calculation

### Resistor Divider Network
```
VBAT → 3.3kΩ → GPIO2 → 10kΩ → GND
       (R1)            (R2)
```

### Calculations
- **Divider ratio**: R2 / (R1 + R2) = 10kΩ / 13.3kΩ = 0.7519
- **Voltage at GPIO2**: V_GPIO2 = V_BAT × 0.7519
- **Battery voltage**: V_BAT = V_GPIO2 / 0.7519 = V_GPIO2 × 1.3301

### Battery Percentage
- **100%**: 4.2V (fully charged LiPo)
- **0%**: 3.0V (cutoff voltage)
- **Calculation**: `((V_BAT - 3.0V) / (4.2V - 3.0V)) × 100%`

### Example Readings
| V_BAT | V_GPIO2 | Percentage | Status |
|-------|---------|------------|--------|
| 4.20V | 3.16V | 100% | Full charge |
| 3.85V | 2.89V | 71% | Normal |
| 3.60V | 2.71V | 50% | Mid-range |
| 3.20V | 2.41V | 17% | LVO threshold |
| 3.00V | 2.26V | 0% | Warning threshold |
| 2.85V | 2.14V | 0% | Critical (no blink) |

## Power Efficiency

### Battery Monitoring Strategy
- **GPIO21 enable pulse**: 10ms per reading
- **Reading interval**: 1000ms
- **Duty cycle**: 10ms / 1000ms = 1%
- **Power savings**: 99% of time, voltage divider is disabled

### Deep Sleep Current Draw
- **Active mode**: ~50mA (CPU + peripherals + LED monitoring)
- **Deep sleep mode**: <1mA (RTC domain only)
- **Battery life improvement**: 50× during sleep periods

## 20-Minute Session Details

### Runtime Tracking
- **Start time**: Captured at task initialization via `esp_timer_get_time()`
- **Elapsed time**: Calculated and displayed with each reading (MM:SS format)
- **Session limit**: 1,200,000 milliseconds (20 minutes)
- **Total readings**: ~1200 readings (one per second)

### Auto-Shutdown Sequence
1. Session duration reaches 20 minutes
2. Log session summary with statistics
3. Display final battery voltage and percentage
4. Configure button as wake source
5. Enter deep sleep gracefully
6. Wake only via button press to start new session

### Session Logging Example
```
============================================
   20-MINUTE SESSION COMPLETE
============================================
Session duration: 20 minutes
Total readings: 1200
Final battery: 3.67V [67%]

Gracefully entering deep sleep...
Press button to wake and start new session
============================================
```

## Key Features

### Low Voltage Cutout (LVO)
- **When**: Checked immediately on every wake/power-on
- **Threshold**: 3.2V (protects battery from over-discharge)
- **Warning threshold**: 3.0V (visual feedback if above)
- **Fail-safe**: If ADC read fails, continue operation (avoid false lockout)
- **Battery protection**: No LED activity if voltage < 3.0V

### Visual Warning Pattern
For 3.0V ≤ voltage < 3.2V:
- **Pattern**: 3 blinks on GPIO15 (active LOW)
- **Timing**: 200ms ON, 200ms OFF per blink
- **Total duration**: ~1200ms (1.2 seconds)
- **Purpose**: Alert user to charge battery before next use

### Runtime Limit
- **Duration**: 20 minutes (1,200,000ms)
- **Purpose**: Demonstrate session management for research studies
- **Tracking**: Elapsed time shown in MM:SS format with each reading
- **Shutdown**: Graceful with comprehensive logging

### Button Control
- **Short press**: No action (monitoring only, no toggle in this test)
- **5-second hold**: Manual deep sleep entry with countdown
- **Debouncing**: 50ms debounce prevents false triggers
- **Sampling**: 10ms polling for responsive detection

### Deep Sleep Management
- **Power consumption**: <1mA in sleep
- **Wake source**: GPIO1 button press (RTC GPIO ext1 wake)
- **Wake latency**: ~2 seconds to full operation
- **Wake detection**: Logs wake reason on startup

## Troubleshooting

### LVO Issues
- **LVO triggers incorrectly**: Check resistor divider accuracy (measure with multimeter)
- **No LVO when expected**: Verify GPIO21 enable/disable sequence and ADC calibration
- **LED doesn't blink**: Check GPIO15 connection (active LOW: 0=ON)

### Battery Reading Issues
- **Readings too high**: Check resistor divider ratio (should be 0.7519)
- **Readings too low**: Verify ADC attenuation (should be DB_12 for 0-3.3V)
- **Erratic readings**: Increase settling time from 10ms or check capacitor on divider
- **No readings**: Verify GPIO21 enable control and GPIO2 ADC channel

### Session Issues
- **Session ends early**: Check for button press (5s hold triggers sleep)
- **Session runs beyond 20 min**: Verify `SESSION_DURATION_MS` constant
- **Time display wrong**: Check `esp_timer_get_time()` availability

### Sleep/Wake Issues
- **Device doesn't sleep after 20 min**: Check for infinite loops or missing sleep call
- **Device doesn't wake**: Verify GPIO1 RTC capability and ext1 wake config
- **Wrong wake reason**: Check `esp_sleep_get_wakeup_cause()` logic

### Build Issues
- **Source file not found**: Check `scripts/select_source.py` mapping
- **CMakeLists.txt error**: Verify Python script ran successfully
- **ADC deprecated warnings**: Using ESP-IDF v5.5.0 (DB_12 attenuation)

## Technical Implementation

### JPL Compliance
- ✅ All timing uses `vTaskDelay()` (no busy-wait loops)
- ✅ Bounded complexity (all functions < 10 cyclomatic complexity)
- ✅ Comprehensive error checking with fail-safe defaults
- ✅ All variables explicitly initialized
- ✅ Single entry/exit points per function
- ✅ No magic numbers (all constants #defined)

### ESP-IDF v5.5.0 Features Used
- `adc_oneshot_*()`: ADC configuration and reading
- `adc_cali_*()`: ADC calibration (Curve Fitting or Line Fitting)
- `gpio_config()`: GPIO initialization
- `gpio_set_level()` / `gpio_get_level()`: GPIO control
- `rtc_gpio_*()`: RTC GPIO for deep sleep wake
- `esp_sleep_enable_ext1_wakeup()`: Wake source configuration
- `esp_deep_sleep_start()`: Enter deep sleep
- `esp_timer_get_time()`: High-resolution timing (microseconds)

### Power Management Strategy
1. **LVO at startup**: Prevent operation on depleted battery
2. **1% duty cycle monitoring**: Battery enable only during measurement
3. **20-minute limit**: Automatic shutdown for research study simulation
4. **Deep sleep between sessions**: <1mA current draw
5. **Button wake**: User-initiated next session

## Integration with Main Program

This test validates hardware and patterns for main program features:

### Battery Protection
- LVO threshold prevents battery over-discharge
- Visual feedback (3 blinks) alerts user to low battery
- Critical voltage (<3.0V) avoids LED activity to save power
- Automatic sleep entry protects battery health

### Session Management
- 20-minute runtime demonstrates research study session length
- Elapsed time tracking shows user progress through session
- Graceful shutdown with logging shows clean state transitions
- Auto-sleep after session preserves battery between uses

### User Interaction
- Button hold (5s) provides emergency shutdown
- Wake-on-button enables next session start
- Status LED provides visual feedback during LVO
- Comprehensive logging helps debug any issues

### Power Efficiency
- 1% duty cycle on battery monitoring maximizes battery life
- Deep sleep between sessions reduces idle power draw
- GPIO21 enable/disable strategy is production-ready

## Suggested Test Procedure

### Test 1: Normal Operation (Healthy Battery)
1. Ensure battery voltage is ≥ 3.2V (check with multimeter)
2. Build and upload: `pio run -e battery_voltage_test -t upload && pio device monitor`
3. Verify LVO check passes
4. Observe battery readings with elapsed time
5. Verify readings are accurate (compare to multimeter)
6. Let session run for 2-3 minutes
7. Press and hold button for 5 seconds
8. Verify countdown and clean deep sleep entry
9. Press button to wake
10. Verify LVO check and new session starts

### Test 2: 20-Minute Auto Shutdown
1. Start test with healthy battery
2. Let session run for full 20 minutes (monitor output)
3. Verify session complete message
4. Verify total readings count (~1200)
5. Verify device enters deep sleep automatically
6. Press button to wake and start new session

### Test 3: LVO Warning (3.0V - 3.2V)
1. Use power supply to set voltage to 3.15V
2. Build and upload test
3. Device should show LVO triggered message
4. Verify 3 blinks on GPIO15 LED
5. Device should enter deep sleep immediately
6. No session should start

### Test 4: Critical Low Voltage (<3.0V)
1. Use power supply to set voltage to 2.85V
2. Build and upload test
3. Device should show LVO triggered message
4. Verify NO blinks on GPIO15 (battery protection)
5. Device should enter deep sleep immediately
6. No session should start

### Test 5: ADC Accuracy Validation
1. Use calibrated power supply with known voltage
2. Set to 3.6V (mid-range)
3. Run test and compare reading to known voltage
4. Error should be <50mV (within ADC accuracy)
5. Verify percentage calculation is correct

### Test 6: Multiple Wake/Sleep Cycles
1. Start with healthy battery
2. Hold button 5s → sleep
3. Press button → wake, verify LVO pass
4. Hold button 5s → sleep
5. Repeat 5 times
6. Verify consistent LVO checks and clean transitions

## Success Criteria

✅ LVO check runs immediately on every wake/power-on  
✅ LVO correctly enters sleep if voltage < 3.2V  
✅ 3 blinks shown for 3.0V ≤ voltage < 3.2V  
✅ No blinks shown for voltage < 3.0V  
✅ Battery readings accurate within 50mV  
✅ Elapsed time tracks correctly (MM:SS format)  
✅ 20-minute session completes with auto-shutdown  
✅ Session statistics logged correctly  
✅ Button hold (5s) triggers manual sleep  
✅ Button press wakes device reliably  
✅ Device resumes with fresh LVO check after wake  
✅ Multiple wake/sleep cycles work consistently  

## Expected Battery Life

### Active Session (20 minutes)
- **Current draw**: ~50mA average
- **Capacity used**: 50mA × (20/60)h = 16.67 mAh
- **dual 350mAh batteries (700mAh)**: ~21 sessions per charge

### Deep Sleep (Between Sessions)
- **Current draw**: <1mA
- **Time between sessions**: Variable (user dependent)
- **Negligible capacity loss**: Deep sleep is very efficient

### Real-World Usage
- **Daily single session**: Battery lasts weeks between charges
- **Multiple sessions per day**: Charge every few days
- **LVO protection**: Prevents battery damage from over-discharge

## File Locations

```
project_root/
├── test/
│   ├── battery_voltage_test.c           # Test source code (UPDATED)
│   └── BATTERY_VOLTAGE_TEST_GUIDE.md    # This guide (NEW)
├── scripts/
│   └── select_source.py                 # Build system (already configured)
├── platformio.ini                       # Build config (already configured)
└── BUILD_COMMANDS.md                    # Build reference (already documented)
```

## Recent Updates

### LVO Protection System (Latest)
- Added `check_low_voltage_cutout()` function
- Runs at startup before task creation
- Implements 3.2V threshold with 3-blink warning
- No blink for critical voltage (<3.0V)
- Graceful deep sleep entry on LVO trigger

### 20-Minute Session Limit (Latest)
- Added `SESSION_DURATION_MS` constant (20 minutes)
- Elapsed time tracking in MM:SS format
- Auto-shutdown with comprehensive logging
- Session statistics: duration, total readings, final battery state

### Enhanced Battery Task (Latest)
- Displays elapsed time with each reading
- Monitors session duration continuously
- Graceful shutdown sequence when limit reached
- Calculates and logs session statistics

## Next Steps

1. **Build and upload test**:
   ```bash
   pio run -e battery_voltage_test -t upload && pio device monitor
   ```

2. **Verify LVO check** passes with healthy battery (≥3.2V)

3. **Monitor voltage readings** for accuracy (compare to multimeter)

4. **Test button hold** for manual deep sleep (5 seconds)

5. **Test 20-minute auto-shutdown** (full session)

6. **Test LVO warning** with 3.0V-3.2V range (3 blinks)

7. **Test critical LVO** with <3.0V (no blinks)

8. **Measure power consumption** (optional but recommended):
   - Active monitoring: ~50mA
   - Deep sleep: <1mA
   - Use ammeter in series with battery

9. **Once verified**, integrate patterns into main program:
   - LVO check on every wake
   - Session time limits for research studies
   - Graceful shutdown procedures
   - Power-efficient battery monitoring

## Additional Notes

### Why 3.2V Threshold?
- **Battery chemistry**: LiPo batteries should not discharge below 3.0V
- **Safety margin**: 3.2V provides 0.2V buffer above critical 3.0V
- **Voltage sag**: Under load, battery voltage drops; 3.2V ensures safe cutoff
- **Battery longevity**: Avoiding deep discharge extends battery cycle life

### Why 3-Blink Warning?
- **User feedback**: Alerts user to charge battery before next session
- **Battery protection**: Only shown if voltage ≥ 3.0V (safe to use LED)
- **Simplicity**: 3 blinks is clear, distinct signal
- **Duration**: ~1.2 seconds total (not annoying, easily noticed)

### Why No Blink Below 3.0V?
- **Battery protection**: Every milliamp counts when critically low
- **Safety**: Avoid further discharge that could damage battery
- **Fail-safe**: If user repeatedly tries to power on, LED won't drain battery

### Why 20-Minute Limit?
- **Research study alignment**: Typical EMDR session duration
- **Battery testing**: Long enough to observe voltage drop trends
- **User experience**: Forces periodic rest/break between sessions
- **Practical validation**: Proves system can handle timed sessions

---

**Board**: Seeed Xiao ESP32C6  
**Framework**: ESP-IDF v5.5.0  
**Test Created**: 2025-11-02  
**Test Updated**: 2025-11-02 (Added LVO and 20-minute session limit)  
**Build System**: ESP-IDF CMake with Python source selection  
**Generated with assistance from**: Claude Sonnet 4 (Anthropic)
