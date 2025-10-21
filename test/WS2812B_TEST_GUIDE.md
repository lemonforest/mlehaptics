# WS2812B LED Hardware Verification Test Guide

**Purpose:** Verify WS2812B LED functionality, power control, color display, and deep sleep integration before implementing therapy light features.

**Board:** Seeed Xiao ESP32C6  
**Framework:** ESP-IDF v5.5.0  
**Date Created:** October 20, 2025

---

## Test Overview

This hardware test verifies the complete WS2812B LED subsystem:
- GPIO16 power enable (P-MOSFET control)
- GPIO17 data control (WS2812B DIN)
- Color accuracy and transitions
- Button-triggered color cycling
- Deep sleep wake guarantee (AD023)
- GPIO15 status LED feedback

---

## Hardware Configuration

### GPIO Pin Assignment
| GPIO | Function | Description |
|------|----------|-------------|
| **GPIO1** | Button Input | Hardware pull-up, RTC wake source |
| **GPIO15** | Status LED | Active LOW (0=ON, 1=OFF), state indicator |
| **GPIO16** | WS2812B Power Enable | P-MOSFET gate control (HIGH=enabled) |
| **GPIO17** | WS2812B DIN | WS2812B data input pin |

### WS2812B Configuration
- **LED Type:** WS2812B (RGB addressable LED)
- **Number of LEDs:** 1 (single LED test)
- **Data Protocol:** GRB format (Green-Red-Blue byte order)
- **Control Method:** ESP-IDF `led_strip` component with RMT peripheral
- **RMT Resolution:** 10MHz
- **Power Control:** P-MOSFET switch on GPIO16

---

## Test Sequence

### Power-On Behavior
1. ESP32-C6 boots and initializes GPIO
2. GPIO16 goes HIGH → WS2812B powered
3. 50ms stabilization delay
4. LED strip initialized (RMT peripheral)
5. WS2812B displays **RED** (initial state)
6. GPIO15 begins **slow blink** (500ms period, 2Hz)

### Color Cycling (Button Press)
Each button press cycles through colors:

| State | WS2812B Color | RGB Values | GPIO15 Pattern | Frequency |
|-------|---------------|------------|----------------|-----------|
| **RED** | Pure red | (255, 0, 0) | Slow blink | 2Hz (500ms) |
| **GREEN** | Pure green | (0, 255, 0) | Medium blink | 4Hz (250ms) |
| **BLUE** | Pure blue | (0, 0, 255) | Fast blink | 8Hz (125ms) |
| **RAINBOW** | Color cycle | HSV sweep | Very fast blink | 10Hz (100ms) |
| **Repeat** | Back to RED | (255, 0, 0) | Slow blink | 2Hz (500ms) |

**Rainbow Effect Details:**
- Smooth HSV color wheel rotation (0-360 degrees)
- Hue increments by 1 degree per update
- Update rate: 50Hz (20ms per step)
- Full rainbow cycle: ~7.2 seconds (360 steps × 20ms)
- Saturation: 100%, Value: 100% (full brightness)

### Deep Sleep Shutdown (5-Second Hold)
1. User holds button for 1 second → Countdown starts
2. Console displays: "5... 4... 3... 2... 1..."
3. After countdown → **PURPLE blink effect** begins
4. WS2812B alternates: Purple ON (200ms) → OFF (200ms)
5. Waiting for button release (visual feedback without serial)
6. User releases button → Sleep immediately
7. WS2812B cleared (all off)
8. GPIO15 set LOW (off)
9. GPIO16 set LOW (WS2812B unpowered)
10. Device enters deep sleep (<1mA consumption)

### Wake-Up Behavior (Button Press)
1. User presses button → ESP32-C6 wakes (EXT1 RTC wake)
2. GPIO16 goes HIGH → WS2812B powered
3. 50ms stabilization delay
4. WS2812B displays **RED** (fresh session)
5. GPIO15 begins **slow blink** (2Hz)
6. Cycle repeats from beginning

---

## Expected Console Output

### Power-On
```
================================================
=== WS2812B LED Hardware Verification Test ===
================================================
Board: Seeed Xiao ESP32C6
Framework: ESP-IDF v5.5.0
Button: GPIO1 (hardware pull-up)
Status LED: GPIO15 (active LOW - 0=ON, 1=OFF)
WS2812B Enable: GPIO16 (HIGH=powered)
WS2812B DIN: GPIO17 (data control)

Wake up! Reason: Power-on or reset (not from deep sleep)

Initializing GPIO...
Button GPIO1 configured
Status LED GPIO15 configured (active LOW)
WS2812B power enable GPIO16 configured (HIGH=enabled)
GPIO initialized successfully

Initializing WS2812B LED strip...
WS2812B LED strip initialized successfully
WS2812B powered ON

Configuring deep sleep wake source...
Configuring GPIO1 for RTC wake...
RTC wake configured: GPIO1 (wake on LOW)
Wake source configured successfully

=== Test Instructions ===
1. WS2812B should show RED
2. GPIO15 blinks slowly (2Hz) for RED state
3. Press button: Cycle through colors
   - RED → GREEN (GPIO15 blinks 4Hz)
   - GREEN → BLUE (GPIO15 blinks 8Hz)
   - BLUE → RAINBOW (GPIO15 blinks 10Hz)
   - RAINBOW → RED (cycle repeats)
4. Hold button 5s: Countdown + purple blink
5. Release button: Deep sleep (<1mA)
6. Press button to wake: Returns to RED

Starting tasks...
Button monitoring task started
Rainbow effect task started
Status LED blink task started
Hardware test running!
State: RED (press button to cycle colors)
================================================
```

### Color Cycling
```
Button pressed! State: GREEN
Button pressed! State: BLUE
Button pressed! State: RAINBOW
Button pressed! State: RED
```

### Deep Sleep Entry
```
Hold button for deep sleep...
5...
4...
3...
2...
1...

Waiting for button release...
(Purple blink effect - release button when ready)
Button released!

===========================================
Entering ultra-low power deep sleep mode...
===========================================
Power consumption: <1mA
WS2812B powered OFF
Press button (GPIO1) to wake device
Upon wake, WS2812B will show RED
```

### Wake-Up
```
ESP-ROM:esp32c6-20220919
rst:0x5 (DSLEEP),boot:0xc (SPI_FAST_FLASH_BOOT)
SPIWP:0xee
mode:DIO, clock div:2
...

Wake up! Reason: EXT1 (RTC GPIO - button press)

[Initialization sequence repeats]

State: RED (press button to cycle colors)
```

---

## Verification Checklist

### Power-On Verification
- [ ] WS2812B lights up RED immediately after boot
- [ ] GPIO15 status LED blinks slowly (500ms period)
- [ ] No visible flicker or instability in LED color

### Color Accuracy Verification
- [ ] **RED state:** Pure red, no green/blue contamination
- [ ] **GREEN state:** Pure green, no red/blue contamination
- [ ] **BLUE state:** Pure blue, no red/green contamination
- [ ] **RAINBOW state:** Smooth color transitions (no jumps)
- [ ] GPIO15 blink pattern changes correctly for each state

### Rainbow Effect Verification
- [ ] Smooth color progression (no sudden color jumps)
- [ ] Complete spectrum visible (red → yellow → green → cyan → blue → magenta → red)
- [ ] Consistent brightness throughout color cycle
- [ ] GPIO15 blinks very fast (10Hz) during rainbow

### Button Functionality Verification
- [ ] Short button press cycles colors reliably
- [ ] No missed button presses (hardware debounce working)
- [ ] Color state advances in correct sequence
- [ ] Long button hold triggers countdown (no accidental color cycling)

### Deep Sleep Entry Verification
- [ ] 5-second countdown displays correctly
- [ ] PURPLE blink effect visible while waiting for release
- [ ] Device enters sleep immediately after button release
- [ ] WS2812B turns completely off before sleep
- [ ] GPIO15 status LED turns off before sleep

### Deep Sleep Wake Verification
- [ ] Button press wakes device reliably
- [ ] Wake-up reason: "EXT1 (RTC GPIO)"
- [ ] WS2812B returns to RED state after wake
- [ ] GPIO15 status LED resumes slow blink (2Hz)
- [ ] Button press during sleep never fails to wake device

### Power Consumption Verification
**Active State (Color Display):**
- WS2812B LED: ~50-60mA (full brightness)
- ESP32-C6 active: ~50mA
- GPIO15 status LED: ~5mA
- **Total:** ~105-115mA

**Deep Sleep:**
- ESP32-C6: <1mA
- WS2812B unpowered: 0mA
- GPIO15 off: 0mA
- **Total:** <1mA

---

## Troubleshooting

### WS2812B Not Lighting Up
**Symptom:** LED stays dark after power-on  
**Possible Causes:**
1. GPIO16 not going HIGH (power enable not working)
   - Check P-MOSFET gate connection
   - Verify GPIO16 output level with multimeter
2. WS2812B power connection issue
   - Verify 5V supply to LED
   - Check P-MOSFET drain connection to LED VDD
3. GPIO17 DIN signal issue
   - Verify RMT peripheral initialization
   - Check data line connection to WS2812B DIN

**Debugging Steps:**
```bash
# Check GPIO states at boot
pio device monitor

# Look for these messages:
WS2812B power enable GPIO16 configured (HIGH=enabled)
WS2812B LED strip initialized successfully
WS2812B powered ON
```

### Wrong Colors Displayed
**Symptom:** LED shows incorrect colors (e.g., red when should be green)  
**Possible Causes:**
1. GRB vs RGB byte order confusion
   - ESP-IDF `led_strip` configured for GRB format (correct for WS2812B)
   - Some WS2812B variants use RGB format
2. Data signal timing issues
   - RMT resolution incorrect
   - Signal integrity problems on GPIO17

**Debugging Steps:**
1. Verify LED strip configuration in code:
   ```c
   led_pixel_format = LED_PIXEL_FORMAT_GRB,  // WS2812B standard
   ```
2. Try different byte orders if colors are consistently wrong
3. Check for signal reflection on long wires (add 100-470Ω resistor on DIN)

### Rainbow Effect Not Smooth
**Symptom:** Rainbow colors jump or flicker  
**Possible Causes:**
1. HSV to RGB conversion errors
2. Task priority issues (rainbow task starved)
3. RMT peripheral busy errors

**Debugging Steps:**
1. Check task priorities in code (rainbow task should be priority 4)
2. Monitor for RMT errors in console
3. Reduce rainbow update rate (increase `RAINBOW_UPDATE_MS`)

### Button Not Responding
**Symptom:** Button presses don't cycle colors  
**Possible Causes:**
1. Hardware debounce circuit issue
2. GPIO1 pull-up not working
3. Button polling rate too slow

**Debugging Steps:**
1. Verify button hardware pull-up (10kΩ to 3.3V)
2. Check GPIO1 voltage with multimeter:
   - Released: ~3.3V
   - Pressed: ~0V
3. Add debug logging to button task to see press detection

### Deep Sleep Wake Fails
**Symptom:** Button press doesn't wake device from sleep  
**Possible Causes:**
1. GPIO1 not properly configured as RTC GPIO
2. ext1 wake source misconfigured
3. Button still held when entering sleep (AD023 violation)

**Debugging Steps:**
1. Verify console message before sleep:
   ```
   RTC wake configured: GPIO1 (wake on LOW)
   ```
2. Ensure button released before sleep (purple blink should complete)
3. Check that device actually entered deep sleep (USB activity LED off)
4. Try holding BOOT button while pressing wake button

### Purple Blink Too Fast/Slow
**Symptom:** Shutdown blink effect not visible or too rapid  
**Possible Causes:**
1. `PURPLE_BLINK_PERIOD_MS` constant incorrect
2. Task scheduling issues during shutdown

**Adjustment:**
```c
// In ws2812b_test.c, adjust:
#define PURPLE_BLINK_PERIOD_MS  200     // Change this value (100-500ms)
```

### Status LED Not Blinking
**Symptom:** GPIO15 status LED stays on or off continuously  
**Possible Causes:**
1. Status LED task not created
2. Task priority too low (starved)
3. GPIO15 connection issue

**Debugging Steps:**
1. Verify task creation message:
   ```
   Status LED blink task started
   ```
2. Check GPIO15 with multimeter (should alternate 0V/3.3V)
3. Increase status LED task priority if needed

---

## Advanced Testing

### Color Accuracy Measurement
For precise color verification, use a spectrometer or calibrated camera:

1. **RED state:** Peak wavelength ~620-630nm
2. **GREEN state:** Peak wavelength ~520-530nm
3. **BLUE state:** Peak wavelength ~465-475nm

### Power Consumption Measurement
Use a USB power meter to verify:

1. **Active:** 105-115mA @ 5V
2. **Deep Sleep:** <1mA @ 5V
3. **Wake Transition:** Brief spike to ~200mA (normal)

### Timing Verification
Use an oscilloscope to verify:

1. **GPIO15 blink periods:**
   - RED: 500ms period (2Hz)
   - GREEN: 250ms period (4Hz)
   - BLUE: 125ms period (8Hz)
   - RAINBOW: 100ms period (10Hz)

2. **WS2812B DIN signal:**
   - 0-bit: ~400ns HIGH, ~850ns LOW
   - 1-bit: ~800ns HIGH, ~450ns LOW
   - Reset: >50µs LOW

---

## Integration Notes

This test validates hardware before implementing therapy light features in the main application.

**Validated Components:**
- ✅ GPIO16 WS2812B power enable control
- ✅ GPIO17 WS2812B DIN data control
- ✅ ESP-IDF `led_strip` RMT peripheral
- ✅ Color accuracy (R, G, B, HSV)
- ✅ Deep sleep power management
- ✅ AD023 wake guarantee (wait-for-release pattern)

**Ready for Main Application Integration:**
Once this test passes all verification checks, the following can be integrated into the main bilateral stimulation application:

1. **Therapy light enable/disable** via mobile app
2. **Synchronized bilateral light patterns** with motor stimulation
3. **Color therapy research** (specific colors for different therapy types)
4. **Intensity control** via PWM or color brightness modulation
5. **Session-based light patterns** (breathing effects, gradual color changes)

**Known Limitations:**
- Single WS2812B LED only (expandable to strips if needed)
- No case light diffusion testing (requires translucent case)
- No long-term thermal testing (WS2812B heat dissipation)

---

## Build and Run

```bash
# Build and upload test
pio run -e ws2812b_test -t upload && pio device monitor

# Quick alias (add to shell profile)
alias pio-ws2812b='pio run -e ws2812b_test -t upload && pio device monitor'

# Then just run:
pio-ws2812b
```

---

## Related Documentation

- **Architecture Decisions:** `docs/architecture_decisions.md` (AD023: Deep Sleep Wake Pattern)
- **GPIO Mapping:** `docs/GPIO_UPDATE_2025-10-17.md` (Pin assignments and back-EMF circuit)
- **Build Commands:** `BUILD_COMMANDS.md` (All hardware test environments)
- **Button/Deep Sleep Test:** `test/BUTTON_DEEPSLEEP_TEST_GUIDE.md` (AD023 reference implementation)

---

**Test Status:** ✅ Ready for hardware verification  
**Next Steps:** Run test, complete verification checklist, integrate into main application

---

*Generated with assistance from Claude Sonnet 4 (Anthropic)*
