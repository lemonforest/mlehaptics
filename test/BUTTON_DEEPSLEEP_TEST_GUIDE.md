# Button & Deep Sleep Hardware Test - Quick Reference

## Overview
Hardware test for Seeed Xiao ESP32C6 button, LED, and deep sleep functionality.

## Test Purpose
Verify hardware operation before implementing main program sleep/wake logic:
- ✅ Button input on GPIO1 (hardware debounced)
- ✅ LED output on GPIO15 (active LOW)
- ✅ 5-second button hold detection
- ✅ Ultra-low power deep sleep (<1mA)
- ✅ Wake from deep sleep via button press

## Build & Upload

### Quick Start
```bash
# Build, upload, and monitor in one command
pio run -e button_deepsleep_test -t upload && pio device monitor

# Or step by step:
pio run -e button_deepsleep_test        # Build only
pio run -e button_deepsleep_test -t upload   # Upload to device
pio device monitor                      # Monitor serial output
```

### Build System Details
This test uses the ESP-IDF v5.5.0 CMake build system with automatic source file selection:
- Python script (`scripts/select_source.py`) runs before each build
- Script detects environment name: `button_deepsleep_test`
- Automatically configures `src/CMakeLists.txt` to build `test/button_deepsleep_test.c`
- No manual CMakeLists.txt editing required

## Test Behavior

### Initial Power-On
```
=== Button & Deep Sleep Hardware Test ===
Wake up! Reason: Power-on or reset (not from deep sleep)
LED: ON (press button to toggle)
```

### Short Button Press (Toggle LED)
```
Button pressed! LED: OFF
[Press again]
Button pressed! LED: ON
```

### Button Hold (5 Seconds → Deep Sleep)
```
Button HOLD detected (5.0s) - entering deep sleep in...
5... 4... 3... 2... 1...
Entering ultra-low power deep sleep mode...
Power consumption: <1mA
Press button (GPIO1) to wake device
[Serial output stops - device is asleep]
```

### Wake from Deep Sleep
```
[Press button]
ESP-ROM:esp32c6-20220919
...
Wake up! Reason: GPIO (button press on GPIO1)
LED: ON (press button to toggle)
[Test restarts]
```

## GPIO Configuration

| GPIO | Function | Mode | Details |
|------|----------|------|---------|
| GPIO1 | Button | Input | RTC GPIO, hardware pull-up, 50ms debounce |
| GPIO15 | LED | Output | Active LOW (0=ON, 1=OFF) |

## Key Features

### Button Detection
- **Short press**: Toggle LED (press duration < 5 seconds)
- **Long press**: 5-second hold triggers deep sleep with countdown
- **Debouncing**: 50ms debounce time prevents false triggers
- **Sampling rate**: 10ms polling for responsive button detection

### Deep Sleep Mode
- **Power consumption**: <1mA (vs ~50mA active)
- **Wake source**: GPIO1 button press (RTC GPIO ext1 wake)
- **Wake behavior**: LED turns ON immediately after wake
- **Wake latency**: <2 seconds to full operation

### LED Behavior
- **Power-on**: LED starts ON (GPIO15 = 0)
- **Active**: Toggles with button press
- **Pre-sleep**: Turns OFF before entering sleep (power saving)
- **Post-wake**: Turns ON after wake-up

## Troubleshooting

### LED Issues
- **LED doesn't turn on**: Verify GPIO15 is active LOW (0=ON)
- **LED stuck on/off**: Check GPIO configuration and wiring

### Button Issues  
- **Button not detected**: Check GPIO1 connection and pull-up resistor
- **Multiple toggles**: Increase debounce time from 50ms
- **Hold not working**: Button must be held continuously for 5 seconds

### Sleep/Wake Issues
- **Device doesn't sleep**: Verify 5-second hold completes countdown
- **Device doesn't wake**: Check GPIO1 RTC capability and ext1 configuration
- **Wrong wake reason**: Verify rtc_gpio configuration

### Build Issues
- **Source file not found**: Check `scripts/select_source.py` mapping
- **CMakeLists.txt error**: Verify Python script ran successfully
- **Build fails**: Check ESP-IDF v5.5.0 installation

## Technical Implementation

### JPL Compliance
- ✅ All timing uses `vTaskDelay()` (no busy-wait loops)
- ✅ Bounded complexity (cyclomatic complexity < 10)
- ✅ Comprehensive error checking
- ✅ All variables explicitly initialized
- ✅ Single entry/exit points

### ESP-IDF v5.5.0 Features Used
- `gpio_config()`: GPIO initialization
- `rtc_gpio_*()`: RTC GPIO configuration for deep sleep
- `esp_sleep_enable_ext1_wakeup()`: Wake source configuration
- `esp_deep_sleep_start()`: Enter deep sleep
- `esp_sleep_get_wakeup_cause()`: Determine wake reason
- `esp_timer_get_time()`: High-resolution timing

### Power Management
- **Active mode**: ~50mA (CPU + peripherals)
- **Deep sleep**: <1mA (RTC domain only)
- **Wake latency**: <2 seconds (bootloader + app init)
- **Battery life impact**: 50x improvement during sleep

## Integration with Main Program

This test validates hardware for main program features:
- Emergency shutdown via 5-second button hold
- Deep sleep power management for battery life
- Wake-from-sleep for user interaction
- LED status indication during operation
- Button timing accuracy and debouncing

Once this test passes, main program can confidently implement:
- Session timeout → automatic deep sleep
- User-initiated sleep via button hold
- Wake-on-button for next session
- Visual feedback via status LED

## File Locations

```
project_root/
├── test/
│   └── button_deepsleep_test.c      # Test source code
├── scripts/
│   └── select_source.py             # Build system (updated)
├── platformio.ini                   # Build config (updated)
└── test/
    └── README.md                    # Test documentation (updated)
```

## Modified Files

1. **test/button_deepsleep_test.c** (NEW)
   - Complete hardware test implementation
   - ~400 lines with comprehensive documentation
   - JPL compliant with error handling

2. **scripts/select_source.py** (UPDATED)
   - Added: `"button_deepsleep_test": "../test/button_deepsleep_test.c"`
   - Enables automatic source selection

3. **platformio.ini** (UPDATED)
   - Added: `[env:button_deepsleep_test]` section
   - Configures build flags and extends base config

4. **test/README.md** (UPDATED)
   - Added comprehensive test documentation
   - Expected behavior and troubleshooting guide

## Next Steps

1. **Build and upload test**:
   ```bash
   pio run -e button_deepsleep_test -t upload && pio device monitor
   ```

2. **Verify LED starts ON** after power-up

3. **Test button toggle** (short press)

4. **Test deep sleep** (5-second hold)

5. **Test wake-up** (button press during sleep)

6. **Measure power consumption** (optional):
   - Active: ~50mA
   - Sleep: <1mA
   - Use ammeter in series with power supply

7. **Once verified**, integrate similar logic into main program:
   - Use same GPIO configuration
   - Adopt button timing patterns
   - Implement deep sleep for battery life
   - Use wake-on-button mechanism

## Success Criteria

✅ LED illuminates on power-up  
✅ Button press toggles LED reliably  
✅ No button bounce (false triggers)  
✅ 5-second hold shows countdown  
✅ Device enters deep sleep  
✅ Serial output stops during sleep  
✅ Button press wakes device  
✅ Wake reason correctly identified  
✅ LED illuminates after wake  
✅ Cycle repeats indefinitely  

---

**Board**: Seeed Xiao ESP32C6  
**Framework**: ESP-IDF v5.5.0  
**Test Created**: 2025-10-20  
**Build System**: AD022 (ESP-IDF CMake with Python source selection)
