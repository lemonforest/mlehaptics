# Hardware Test Suite

This directory contains standalone hardware validation tests for the EMDR Pulser project.

## Purpose

These tests are designed to verify individual hardware subsystems **before** integrating them into the full bilateral stimulation system. Each test is a complete, minimal program that exercises specific hardware components.

## Available Tests

### 1. LEDC Blink Test (`ledc_blink_test.c`)

**Purpose:** Verify LEDC PWM peripheral before H-bridge integration

**Test Sequence:**
- Blink GPIO15 LED at 1Hz (500ms on, 500ms off) using LEDC PWM

**PWM Configuration:**
- Frequency: 1kHz (carrier frequency for PWM)
- Resolution: 8-bit (0-255 range)
- LED Control: duty=0 = LED ON, duty=255 = LED OFF (active LOW)

**Visual Feedback:**
- GPIO15 LED: Blinks at 1Hz (visible confirmation of LEDC working)
- **IMPORTANT:** Xiao ESP32C6 user LED is ACTIVE LOW
  - `ledc_set_duty(0)` = LED **ON** (100% low)
  - `ledc_set_duty(255)` = LED **OFF** (100% high)

**Hardware Requirements:**
- Only the onboard GPIO15 LED (no external hardware needed)

**Build & Run:**
```bash
pio run -e ledc_blink_test -t upload && pio device monitor
```

**Expected Behavior:**
- ✅ LED blinks at exactly 1Hz (use stopwatch to verify)
- ✅ LED fully on for 500ms, fully off for 500ms
- ✅ Serial output shows "LED ON" and "LED OFF" messages
- ✅ Blink count increments each cycle
- ✅ No flickering or instability

**What to Check:**
- [ ] LED blinks at steady 1Hz rate
- [ ] LED brightness is consistent (fully on, not dimmed)
- [ ] No visible PWM flicker (1kHz should be smooth)
- [ ] Serial timestamps match 500ms intervals
- [ ] System runs stably for extended period

**Troubleshooting:**
- **LED doesn't blink:** Check GPIO15 connection, verify LEDC init
- **Wrong blink rate:** Check timing constants, vTaskDelay implementation
- **Visible PWM flicker:** 1kHz might be too slow, increase frequency
- **Dim LED:** Check duty cycle settings (should be 0 or 255, not intermediate)

**Why This Test?**
This minimal test verifies that:
1. LEDC peripheral initializes correctly
2. LEDC timer and channel configuration works
3. PWM output can be dynamically changed (duty cycle updates)
4. FreeRTOS task timing is accurate
5. System is ready for more complex LEDC usage (H-bridge control)

---

### 2. H-Bridge GPIO Test (`hbridge_test.c`)

**Purpose:** Verify H-bridge motor control circuitry using basic GPIO (no PWM)

**Test Sequence:**
- Forward @ 100% (2 seconds) → Coast (1 second) → Reverse @ 100% (2 seconds) → Coast (1 second) → Repeat

**Control Method:**
- Simple GPIO HIGH/LOW (not PWM)
- Direct MOSFET control for verification
- Full power forward/reverse for clear motor response

**Visual Feedback:**
- GPIO15 LED: ON during Forward/Reverse, OFF during Coast
- **IMPORTANT:** Xiao ESP32C6 user LED is ACTIVE LOW
  - `gpio_set_level(15, 0)` = LED **ON**
  - `gpio_set_level(15, 1)` = LED **OFF**
- Motor: Should spin in both directions with 60% power

**Hardware Requirements:**
- Assembled H-bridge circuit (GPIO19, GPIO20)
- ERM motor connected to H-bridge outputs
- GPIO15 LED connected

**Build & Run:**
```bash
pio run -e hbridge_test -t upload && pio device monitor
```

**Expected Behavior:**
- ✅ Motor spins forward for 2 seconds
- ✅ Motor coasts (freewheels) for 1 second
- ✅ Motor spins reverse for 2 seconds
- ✅ Motor coasts for 1 second
- ✅ LED matches motor active/coast periods
- ✅ Cycle repeats continuously

**What to Check:**
- [ ] Forward and reverse directions are clearly different
- [ ] Coast period shows motor freewheeling (not braking)
- [ ] No unusual heating of MOSFETs (should be barely warm)
- [ ] Current draw ~90mA during active, minimal during coast
- [ ] LED timing perfectly matches motor behavior
- [ ] No erratic behavior during direction changes

**Troubleshooting:**
- **Motor doesn't spin:** Check H-bridge power connections, MOSFET gates
- **Motor only spins one direction:** Check GPIO19/20 connections, MOSFET orientation
- **MOSFETs getting hot:** Possible shoot-through, check gate driver circuit
- **LED doesn't match motor:** Check GPIO15 connection
- **Erratic behavior:** Check power supply stability, add decoupling caps

---

### 3. H-Bridge PWM Test (`hbridge_pwm_test.c`) ✅ WORKING

**Purpose:** Verify H-bridge motor control with LEDC PWM for variable speed

**Status:** ✅ **Successfully tested and working!**

**Test Sequence:**
- Forward @ 60% PWM (2 seconds) → Coast (1 second) → Reverse @ 60% PWM (2 seconds) → Coast (1 second) → Repeat

**PWM Configuration:**
- Frequency: 25kHz (above human hearing range)
- Resolution: **10-bit** (0-1023 range) - **CRITICAL: 13-bit was too high and caused device freeze!**
- Duty Cycle: 60% = 614/1023 (smoother operation than full power)

**Visual Feedback:**
- GPIO15 LED: ON during Forward/Reverse, OFF during Coast
- **IMPORTANT:** Xiao ESP32C6 user LED is ACTIVE LOW
  - `gpio_set_level(15, 0)` = LED **ON**
  - `gpio_set_level(15, 1)` = LED **OFF**
- Motor: Should spin smoothly at 60% power in both directions

**Hardware Requirements:**
- Assembled H-bridge circuit (GPIO19, GPIO20)
- ERM motor connected to H-bridge outputs
- GPIO15 LED connected

**Build & Run:**
```bash
pio run -e hbridge_pwm_test -t upload && pio device monitor
```

**Expected Behavior:**
- ✅ Motor spins forward smoothly at 60% power for 2 seconds
- ✅ Motor coasts (freewheels) for 1 second
- ✅ Motor spins reverse smoothly at 60% power for 2 seconds
- ✅ Motor coasts for 1 second
- ✅ LED matches motor active/coast periods
- ✅ Cycle repeats continuously
- ✅ Smooth PWM operation (no audible 25kHz whine)
- ✅ Device responsive with serial output

**What to Check:**
- [ ] Motor speed is visibly reduced compared to 100% GPIO test
- [ ] Forward and reverse directions are smooth (not jerky)
- [ ] No audible PWM whine (25kHz should be inaudible)
- [ ] Coast period shows motor freewheeling naturally
- [ ] Current draw ~54mA during active (60% of full power)
- [ ] Serial output shows correct duty cycle calculations
- [ ] No device freezing or unresponsiveness

**Troubleshooting:**
- **Device freezes/unresponsive:** Check LEDC resolution - must be 10-bit or lower for 25kHz
- **Motor doesn't spin:** Check H-bridge power, verify PWM duty cycle > 0
- **Motor spins at full power:** Check PWM duty calculation (should be 614/1023, not 1023/1023)
- **Audible PWM whine:** Normal at low frequencies, should be inaudible at 25kHz
- **Erratic behavior:** Check power supply stability under PWM load

**Important Lesson Learned:**
🔴 **LEDC Resolution vs Frequency Trade-off**
- 13-bit @ 25kHz requires 204.8 MHz clock (IMPOSSIBLE on ESP32-C6!)
- 10-bit @ 25kHz requires 25.6 MHz clock (works perfectly)
- Formula: Required clock = frequency × 2^resolution
- ESP32-C6 APB clock: 80MHz or 160MHz
- Always verify clock requirements before choosing resolution!

---

## Adding New Hardware Tests

When creating new hardware tests:

1. **Create test file** in `test/` directory (e.g., `test/battery_monitor_test.c`)

2. **Add to source map** in `scripts/select_source.py`:
```python
source_map = {
    "xiao_esp32c6": "main.c",
    "hbridge_test": "../test/hbridge_test.c",
    "ledc_blink_test": "../test/ledc_blink_test.c",
    "battery_monitor_test": "../test/battery_monitor_test.c",  # Add this
}
```

3. **Add environment to platformio.ini:**
```ini
[env:battery_monitor_test]
extends = env:xiao_esp32c6

build_flags = 
    ${env:xiao_esp32c6.build_flags}
    -DHARDWARE_TEST=1
    -DDEBUG_LEVEL=3

; Note: Source file selection handled by extra_scripts in base environment
```

4. **Document in this README** with test purpose, sequence, and expected behavior

5. **Keep tests simple** - single subsystem per test, minimal dependencies

**Why the extra step?** ESP-IDF uses CMake (not PlatformIO's build filters), so we use a Python script to select the correct source file. See `docs/ESP_IDF_SOURCE_SELECTION.md` for details.

---

## Test Philosophy

**Hardware tests should be:**
- ✅ **Standalone** - No dependencies on main application code
- ✅ **Observable** - Clear visual/audio feedback of test state
- ✅ **Repeatable** - Continuous loops for extended observation
- ✅ **Minimal** - Test only one subsystem at a time
- ✅ **Safe** - Include safety features (dead time, current limits, etc.)

**Hardware tests should NOT:**
- ❌ Include BLE communication
- ❌ Include bilateral timing logic
- ❌ Use NVS storage
- ❌ Test multiple subsystems simultaneously (unless integration testing)

---

## Integration Testing vs Hardware Testing

**Use Hardware Tests for:**
- Initial board bring-up
- Component-level verification
- Troubleshooting specific subsystems
- Validating repairs or modifications

**Use Main Application for:**
- System integration testing
- Bilateral timing verification
- BLE communication testing
- End-to-end functionality validation

---

## Notes

- All hardware tests use the same ESP-IDF version and safety flags as the main application
- Tests are compiled with `-DHARDWARE_TEST=1` flag for conditional compilation if needed
- Serial monitor logging is verbose (`-DDEBUG_LEVEL=3`) for clear observation
- Each test is completely independent and can be run without building the main application
