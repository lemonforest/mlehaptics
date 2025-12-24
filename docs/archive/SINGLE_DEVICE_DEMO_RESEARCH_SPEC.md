# EMDR Single Device Demo Test - Research Specification

**Project**: EMDR Bilateral Stimulation Device  
**Test Type**: Hardware Validation & Research Study  
**Board**: Seeed Xiao ESP32-C6  
**Framework**: ESP-IDF v5.5.0  
**Created**: 2025-01-21  
**Purpose**: Research motor duty cycle effects on therapeutic efficacy and battery life

---

## Executive Summary

This test creates a standalone single-device EMDR stimulation system that operates for 20 minutes without BLE pairing. The primary purpose is to research the relationship between motor duty cycle, frequency, and therapeutic effectiveness while optimizing battery consumption.

**Key Innovation**: Most commercial EMDR devices run motors at 100% duty cycle. This research explores whether reduced duty cycles (50%, 25%) maintain therapeutic effectiveness while extending battery life.

---

## Research Design - 2×2 Matrix Study

### Independent Variables

1. **Cycle Frequency**: 0.5Hz (2000ms) vs 1Hz (1000ms)
2. **Motor Duty Cycle**: 50% vs 25% of half-cycle time

### Four Research Modes

| Mode | Frequency | Duty Cycle | Half-Cycle | Motor ON | Coast | Motor Duty |
|------|-----------|------------|------------|----------|-------|------------|
| **Mode 1** | 1Hz | 50% | 500ms | 250ms | 250ms | 49.8% |
| **Mode 2** | 1Hz | 25% | 500ms | 125ms | 375ms | 24.9% |
| **Mode 3** | 0.5Hz | 50% | 1000ms | 500ms | 500ms | 49.8% |
| **Mode 4** | 0.5Hz | 25% | 1000ms | 250ms | 750ms | 24.9% |

### Research Questions

1. **Efficacy vs. Duty**: Does 25% duty cycle maintain therapeutic effect vs 50%?
2. **Frequency Effect**: Does slower 0.5Hz feel different from traditional 1Hz?
3. **Battery Optimization**: How much battery life gained at 25% duty?
4. **User Preference**: Which mode feels most effective/comfortable?
5. **Motor Longevity**: Does reduced duty extend motor lifespan?

### Expected Power Consumption

```
Mode 1 (1Hz@50%):   ~45mA average → 15mAh per 20min session
Mode 2 (1Hz@25%):   ~27mA average → 9mAh per 20min session (40% savings)
Mode 3 (0.5Hz@50%): ~45mA average → 15mAh per 20min session
Mode 4 (0.5Hz@25%): ~27mA average → 9mAh per 20min session (40% savings)
```

---

## Hardware Configuration

### GPIO Assignments (from ai_context.md)

```c
#define GPIO_BUTTON              1    // User button (via jumper from GPIO18)
#define GPIO_STATUS_LED         15    // Status LED (ACTIVE LOW - not used in this test)
#define GPIO_WS2812B_ENABLE     16    // WS2812B power (P-MOSFET, ACTIVE LOW)
#define GPIO_WS2812B_DIN        17    // WS2812B data line
#define GPIO_HBRIDGE_IN1        20    // H-bridge forward control (LEDC PWM)
#define GPIO_HBRIDGE_IN2        19    // H-bridge reverse control (LEDC PWM)
```

### Motor Control (from hbridge_pwm_test.c)

```c
// PWM Configuration
#define PWM_FREQUENCY_HZ        25000                    // 25kHz (above hearing)
#define PWM_RESOLUTION          LEDC_TIMER_10_BIT        // 10-bit (0-1023 range)
#define PWM_INTENSITY_PERCENT   60                       // 60% PWM intensity

// H-Bridge Control
// Forward: IN1=PWM, IN2=LOW
// Reverse: IN1=LOW, IN2=PWM
// Coast:   IN1=LOW, IN2=LOW
```

### WS2812B LED Control (from ws2812b_test.c)

```c
// LED Configuration
#define WS2812B_MAX_BRIGHTNESS  20    // 20% maximum (battery + transmittance test)
#define LED_COLOR_RED           {51, 0, 0}      // Red @ 20% (255 * 0.2 = 51)
#define LED_COLOR_PURPLE        {26, 0, 26}     // Purple @ 20% for shutdown

// Power Control (ACTIVE LOW P-MOSFET)
gpio_set_level(GPIO_WS2812B_ENABLE, 0);  // LOW = LED powered ON
gpio_set_level(GPIO_WS2812B_ENABLE, 1);  // HIGH = LED powered OFF
```

---

## Operational Behavior

### Session Timeline (20 minutes)

```
[0:00 - 0:10]   LED ON: Visual mode indicator (blinks match motor duty)
[0:10 - 19:00]  LED OFF: Battery conservation, motor only
[19:00 - 20:00] LED BLINK: 1Hz slow blink warning (session ending soon)
[20:00]         AUTO SLEEP: Enter deep sleep automatically
```

### LED Visual Feedback Strategy

**Purpose**: User must be able to see which mode is active without serial monitor

**10-Second Mode Indication Window**:
- LED blinks RED @ 20% brightness in sync with motor pattern
- Blink pattern visually matches the motor duty cycle
- Pattern repeats continuously for 10 seconds
- **Critical**: This 10-second window RESETS every time button is pressed

**Example Mode 1 (1Hz @ 50% duty)**:
```
Motor:  [===250ms ON===][250ms OFF][===250ms ON===][250ms OFF]
LED:    [===250ms RED===][250ms OFF][===250ms RED===][250ms OFF]
Visual: User sees LED matches motor rhythm - 50% on, 50% off
```

**Example Mode 2 (1Hz @ 25% duty)**:
```
Motor:  [===125ms ON===][375ms OFF][===125ms ON===][375ms OFF]
LED:    [===125ms RED===][375ms OFF][===125ms RED===][375ms OFF]
Visual: User sees short blinks - 25% on, 75% off
```

**Last Minute Warning (19:00 - 20:00)**:
```
LED: [1000ms RED ON @ 20%][1000ms OFF][1000ms RED ON][1000ms OFF]
Pattern: Slow 1Hz blink regardless of mode (universal "ending" signal)
```

### Button Behavior

**Single Press (during session)**:
- Cycle to next mode: Mode 1 → Mode 2 → Mode 3 → Mode 4 → Mode 1
- Motor transitions smoothly to new pattern
- LED indication window resets to 10 seconds (shows new mode)
- Session timer continues (does NOT reset)

**5-Second Hold**:
- Emergency shutdown: Motor coast immediately
- Purple blink wait-for-release pattern (from AD023)
- Enter deep sleep with button wake capability
- Session ends prematurely

### Motor Pattern (Single Device Bilateral Simulation)

**All modes follow this structure**:
```c
// Forward half-cycle
[===motor_on_ms Forward @ 60% PWM===][coast_ms][1ms dead time + watchdog feed]

// Reverse half-cycle  
[===motor_on_ms Reverse @ 60% PWM===][coast_ms][1ms dead time + watchdog feed]

// Repeat for 20 minutes
```

**Mode-Specific Timing**:

**Mode 1: 1Hz @ 50% duty**
```
Half-cycle: 500ms total
├─ Forward: 250ms @ 60% PWM
├─ Coast: 249ms
└─ Dead time: 1ms [watchdog feed]
├─ Reverse: 250ms @ 60% PWM
├─ Coast: 249ms
└─ Dead time: 1ms [watchdog feed]
Total cycle: 1000ms (1Hz)
```

**Mode 2: 1Hz @ 25% duty**
```
Half-cycle: 500ms total
├─ Forward: 125ms @ 60% PWM
├─ Coast: 374ms
└─ Dead time: 1ms [watchdog feed]
├─ Reverse: 125ms @ 60% PWM
├─ Coast: 374ms
└─ Dead time: 1ms [watchdog feed]
Total cycle: 1000ms (1Hz)
```

**Mode 3: 0.5Hz @ 50% duty**
```
Half-cycle: 1000ms total
├─ Forward: 500ms @ 60% PWM
│   ├─ First 250ms
│   ├─ [Watchdog feed at 250ms]
│   └─ Next 250ms
├─ Coast: 499ms
└─ Dead time: 1ms [watchdog feed]
├─ Reverse: 500ms @ 60% PWM
│   ├─ First 250ms
│   ├─ [Watchdog feed at 250ms]
│   └─ Next 250ms
├─ Coast: 499ms
└─ Dead time: 1ms [watchdog feed]
Total cycle: 2000ms (0.5Hz)
```

**Mode 4: 0.5Hz @ 25% duty**
```
Half-cycle: 1000ms total
├─ Forward: 250ms @ 60% PWM
├─ Coast: 749ms
└─ Dead time: 1ms [watchdog feed]
├─ Reverse: 250ms @ 60% PWM
├─ Coast: 749ms
└─ Dead time: 1ms [watchdog feed]
Total cycle: 2000ms (0.5Hz)
```

### Deep Sleep Entry (AD023 Pattern)

**Automatic after 20 minutes**:
1. Motor coast (immediate GPIO write)
2. Turn off WS2812B power: `gpio_set_level(GPIO_WS2812B_ENABLE, 1);`
3. Check button state
4. If button held: Purple blink @ 20% (5Hz) until released
5. Once released: Enter deep sleep immediately
6. Wake source: GPIO1 button press only

**Manual via 5-second hold**:
- Same sequence as automatic sleep
- Motor coast happens immediately on hold detection
- Session ends early

---

## JPL Compliance Requirements

All timing must use `vTaskDelay()` - **NO busy-wait loops**

### Watchdog Feeding Strategy (AD019)

**Task Watchdog Timeout**: 2000ms

**Feeding Schedule**:
- **Short motor periods (<250ms)**: Feed at end of half-cycle (during 1ms dead time)
- **Long motor periods (≥250ms)**: Feed mid-cycle + end of half-cycle

**Mode 3/4 Example** (500ms and 250ms motor periods):
```c
// Mode 3: 500ms motor period
motor_set_direction(MOTOR_FORWARD, 60);
vTaskDelay(pdMS_TO_TICKS(250));        // First half
esp_task_wdt_reset();                   // Mid-cycle feed
vTaskDelay(pdMS_TO_TICKS(250));        // Second half
motor_coast();
vTaskDelay(pdMS_TO_TICKS(coast_ms));
vTaskDelay(pdMS_TO_TICKS(1));          // Dead time
esp_task_wdt_reset();                   // End-of-half-cycle feed

// Mode 4: 250ms motor period  
motor_set_direction(MOTOR_FORWARD, 60);
vTaskDelay(pdMS_TO_TICKS(250));        // Full period
motor_coast();
vTaskDelay(pdMS_TO_TICKS(749));
vTaskDelay(pdMS_TO_TICKS(1));          // Dead time
esp_task_wdt_reset();                   // End-of-half-cycle feed only
```

### Safety Requirements

1. **1ms dead time**: Reserved at end of each half-cycle
2. **Motor coast first**: Always coast before direction change
3. **Emergency response**: Button hold triggers immediate coast
4. **Power-off sequence**: Disable WS2812B before deep sleep
5. **Parameter validation**: All timing parameters checked at startup

---

## Implementation Files Required

### 1. test/single_device_demo_test.c

**Main test file** implementing:
- Four mode state machine
- Motor control patterns
- LED indication with mode-matched blink patterns
- 10-second LED window with button-press reset
- Button press mode cycling
- Button hold deep sleep (AD023 pattern)
- 20-minute session timer
- Automatic deep sleep on timeout
- JPL-compliant timing (all vTaskDelay)

### 2. scripts/select_source.py

**Update source map**:
```python
source_map = {
    "xiao_esp32c6": "main.c",
    "xiao_esp32c6_production": "main.c",
    "xiao_esp32c6_testing": "main.c",
    "hbridge_test": "../test/hbridge_test.c",
    "hbridge_pwm_test": "../test/hbridge_pwm_test.c",
    "ledc_blink_test": "../test/ledc_blink_test.c",
    "button_deepsleep_test": "../test/button_deepsleep_test.c",
    "ws2812b_test": "../test/ws2812b_test.c",
    "single_device_demo_test": "../test/single_device_demo_test.c",  # ADD THIS
}
```

### 3. platformio.ini

**Add new environment**:
```ini
[env:single_device_demo_test]
extends = env:xiao_esp32c6

build_flags = 
    ${env:xiao_esp32c6.build_flags}
    -DHARDWARE_TEST=1
    -DDEBUG_LEVEL=3

; Source selection handled by extra_scripts in base environment
```

### 4. test/README.md

**Add new section**:
```markdown
### 6. Single Device Demo Test (`single_device_demo_test.c`)

**Purpose:** Research study of motor duty cycle effects on therapeutic efficacy and battery life

**Test Sequence:**
- 4 modes: 2×2 matrix of frequency (0.5Hz, 1Hz) × duty cycle (50%, 25%)
- 20-minute session with button mode cycling
- LED @ 20% brightness for mode indication and case transmittance testing
- Automatic deep sleep after session

**Build & Run:**
```bash
pio run -e single_device_demo_test -t upload && pio device monitor
```
```

### 5. BUILD_COMMANDS.md

**Update hardware test table**:
```markdown
| `single_device_demo_test` | 20min research: 4 modes (freq×duty), LED@20% | `pio run -e single_device_demo_test -t upload && pio device monitor` |
```

### 6. test/SINGLE_DEVICE_DEMO_TEST_GUIDE.md

**Quick reference guide** with:
- Mode descriptions
- Button operation
- LED patterns
- Expected behavior
- Research data collection procedures
- Troubleshooting

---

## Code Structure Template

```c
// State machine
typedef enum {
    MODE_1HZ_50_DUTY,     // Mode 1: Traditional 1Hz @ 50%
    MODE_1HZ_25_DUTY,     // Mode 2: Power saver 1Hz @ 25%
    MODE_05HZ_50_DUTY,    // Mode 3: Slow 0.5Hz @ 50%
    MODE_05HZ_25_DUTY,    // Mode 4: Maximum efficiency 0.5Hz @ 25%
    MODE_COUNT
} device_mode_t;

// Mode configuration
typedef struct {
    uint32_t total_cycle_ms;      // 1000 or 2000
    uint32_t motor_on_ms;         // Motor active duration per half-cycle
    uint32_t coast_ms;            // Coast duration per half-cycle
    uint8_t pwm_intensity;        // 60% for all modes
    const char* name;             // Human-readable name
} mode_config_t;

// Mode configurations
static const mode_config_t mode_configs[MODE_COUNT] = {
    {1000, 250, 249, 60, "1Hz@50%"},    // Mode 1
    {1000, 125, 374, 60, "1Hz@25%"},    // Mode 2
    {2000, 500, 499, 60, "0.5Hz@50%"},  // Mode 3
    {2000, 250, 749, 60, "0.5Hz@25%"}   // Mode 4
};

// LED indication function
void led_indicate_mode(device_mode_t mode, uint32_t duration_ms) {
    // Turn on WS2812B power
    // Display mode-matched blink pattern for duration_ms
    // Blinks sync with motor duty cycle
    // Turn off WS2812B power when done
}

// Motor half-cycle execution
esp_err_t execute_motor_half_cycle(motor_direction_t direction, 
                                    const mode_config_t* config) {
    // Set motor direction and intensity
    // Delay for motor_on_ms (with mid-cycle watchdog if needed)
    // Motor coast
    // Delay for coast_ms
    // 1ms dead time with watchdog feed
    // Return ESP_OK
}

// Main session loop
void session_task(void *pvParameters) {
    device_mode_t current_mode = MODE_1HZ_50_DUTY;
    uint32_t session_start = xTaskGetTickCount();
    uint32_t mode_switch_time = session_start;
    bool led_indication_active = true;
    
    // 10-second LED mode indication
    led_indicate_mode(current_mode, 10000);
    
    while (elapsed_time < 20_MINUTES) {
        // Check button press for mode change
        if (button_pressed) {
            current_mode = (current_mode + 1) % MODE_COUNT;
            mode_switch_time = xTaskGetTickCount();
            led_indication_active = true;
            led_indicate_mode(current_mode, 10000);  // Reset 10s window
        }
        
        // LED indication window management
        if (led_indication_active) {
            if ((xTaskGetTickCount() - mode_switch_time) > 10_SECONDS) {
                led_indication_active = false;
                // Turn off LED power
            }
        }
        
        // Last minute warning (19:00-20:00)
        if (19_MINUTES < elapsed_time < 20_MINUTES) {
            // Slow 1Hz blink RED @ 20%
        }
        
        // Execute motor pattern
        execute_motor_half_cycle(MOTOR_FORWARD, &mode_configs[current_mode]);
        execute_motor_half_cycle(MOTOR_REVERSE, &mode_configs[current_mode]);
    }
    
    // Session complete - enter deep sleep
    enter_deep_sleep_with_wake_guarantee();
}
```

---

## Research Data Collection

### Quantitative Measurements

**For each mode, record**:
1. Session battery consumption (mAh)
2. Average current draw (mA)
3. Motor temperature (infrared thermometer)
4. LED visibility through purple case (subjective 1-10 scale)

### Qualitative Assessments

**User experience ratings (1-10 scale)**:
1. Stimulation intensity perception
2. Comfort over 20 minutes
3. Therapeutic "effectiveness" feeling
4. Preference ranking

### Comparative Analysis

**Key comparisons**:
- Mode 1 vs Mode 2: Does 25% duty feel as effective as 50% at 1Hz?
- Mode 3 vs Mode 4: Does 25% duty feel as effective as 50% at 0.5Hz?
- Mode 1 vs Mode 3: Does frequency matter at same duty?
- Mode 2 vs Mode 4: Does frequency matter at reduced duty?

### Success Criteria

**This test is successful if**:
1. All 4 modes run for full 20 minutes without issues
2. Mode transitions work smoothly via button press
3. LED indication clearly shows which mode is active
4. Device enters deep sleep correctly after session
5. User can collect meaningful comparison data between modes

---

## Technical Specifications Summary

### Timing Parameters

```c
#define SESSION_DURATION_MS     (20 * 60 * 1000)  // 20 minutes
#define LED_INDICATION_WINDOW   10000             // 10 seconds
#define LED_WARNING_START       (19 * 60 * 1000)  // Last minute
#define LED_BRIGHTNESS_PERCENT  20                // 20% max
#define MOTOR_INTENSITY_PERCENT 60                // 60% PWM
#define BUTTON_HOLD_SLEEP_MS    5000              // 5 second hold
#define BUTTON_DEBOUNCE_MS      50                // 50ms debounce
```

### Power Budget

```
Active operation (worst case - Mode 1):
- ESP32-C6: ~20mA
- Motor: ~90mA × 50% duty = ~45mA average
- LED (during 10s window): ~10mA
- Total: ~75mA peak, ~65mA average

Active operation (best case - Mode 4):
- ESP32-C6: ~20mA
- Motor: ~90mA × 25% duty = ~23mA average  
- LED (during 10s window): ~10mA
- Total: ~53mA peak, ~43mA average

Deep sleep:
- <1mA total
```

### Build Commands

```bash
# Build and upload
pio run -e single_device_demo_test -t upload

# Build, upload, and monitor
pio run -e single_device_demo_test -t upload && pio device monitor

# Clean build
pio run -e single_device_demo_test -t clean
pio run -e single_device_demo_test -t upload
```

---

## Expected Console Output

```
================================================
=== EMDR Single Device Demo Test ===
=== Research Study: Motor Duty Cycle Effects ===
================================================
Board: Seeed Xiao ESP32C6
Framework: ESP-IDF v5.5.0
Session Duration: 20 minutes
Modes: 4 (frequency × duty cycle matrix)

=== Mode Configuration ===
Mode 1: 1Hz @ 50% duty (250ms motor, 249ms coast per half-cycle)
Mode 2: 1Hz @ 25% duty (125ms motor, 374ms coast per half-cycle)
Mode 3: 0.5Hz @ 50% duty (500ms motor, 499ms coast per half-cycle)
Mode 4: 0.5Hz @ 25% duty (250ms motor, 749ms coast per half-cycle)

Starting Mode: Mode 1 (1Hz @ 50% duty)
LED Indication: 10 seconds (resets on button press)
LED Brightness: 20% RED for mode indication
Motor Intensity: 60% PWM

Press button: Cycle through modes
Hold button 5s: Emergency sleep

=== Session Start ===
[00:00] Mode 1 Active - LED indicating mode (10s)
[00:10] LED OFF - Battery conservation mode
[01:30] Button pressed! Switching to Mode 2...
[01:30] Mode 2 Active - LED indicating mode (10s)
[01:40] LED OFF - Battery conservation mode
[19:00] LED WARNING: Session ending in 1 minute (slow blink)
[20:00] Session complete!
[20:00] Entering deep sleep...
[20:00] Waiting for button release... (purple blink)
[20:01] Button released! Deep sleep activated.

Press button to wake and start new session.
```

---

## Safety and Compliance

### JPL Coding Standard Compliance

✅ All timing uses vTaskDelay() (no busy-wait loops)  
✅ Watchdog fed appropriately for all motor periods  
✅ Bounded execution time (20-minute maximum)  
✅ Single entry/exit points  
✅ Comprehensive parameter validation  
✅ Static memory allocation only  

### AD023 Deep Sleep Pattern

✅ Wait-for-release with LED blink feedback  
✅ Guaranteed wake-on-new-press  
✅ WS2812B power disabled before sleep  
✅ GPIO1 button wake configured correctly  

### Motor Safety

✅ 1ms dead time between direction changes  
✅ Always coast before direction change  
✅ Emergency stop via 5-second button hold  
✅ Immediate motor coast on emergency  

---

## Future Research Directions

### Phase 2 Studies

1. **Intensity Variation**: Test 40%, 60%, 80% PWM intensity at optimal duty/frequency
2. **Asymmetric Patterns**: Different duty for forward vs reverse
3. **Haptic Pulses**: Short burst patterns within half-cycles
4. **Adaptive Duty**: Start high, reduce over session as user habituates

### Hardware Improvements

1. **Current Sensing**: Measure actual motor current for each mode
2. **Temperature Monitoring**: Track motor temperature over 20-minute session
3. **Battery Telemetry**: Real-time voltage and current monitoring
4. **Accelerometer**: Measure actual vibration intensity

### Therapeutic Validation

1. **Clinical Trials**: Compare modes in actual therapeutic sessions
2. **User Studies**: Larger sample size preference data
3. **Efficacy Metrics**: Measure therapeutic outcomes by mode
4. **Comfort Analysis**: Long-term (multi-session) comfort ratings

---

## Version History

- **v1.0** (2025-01-21): Initial research specification
  - 4-mode duty cycle study design
  - LED indication with mode-matched blink patterns
  - 20-minute session with automatic deep sleep
  - Button mode cycling with LED window reset
  - Purple case transmittance testing at 20% RED brightness

---

## References

- **Architecture Decisions**: `docs/architecture_decisions.md`
  - AD006: Bilateral Cycle Time Architecture
  - AD012: Dead Time Implementation Strategy
  - AD019: Task Watchdog Timer with Adaptive Feeding
  - AD022: ESP-IDF Build System and Hardware Test Architecture
  - AD023: Deep Sleep Wake State Machine for ESP32-C6 ext1

- **Project Context**: `docs/ai_context.md`
  - GPIO assignments and hardware specifications
  - Motor control API contracts
  - WS2812B LED control implementation
  - JPL compliance requirements

- **Existing Tests**: `test/README.md`
  - `hbridge_pwm_test.c`: Motor PWM control reference
  - `button_deepsleep_test.c`: Deep sleep pattern reference
  - `ws2812b_test.c`: LED control reference

---

## Contact & Collaboration

**Research Questions?**
- Open GitHub issue with tag `research:duty-cycle`
- Include mode, battery data, and user experience notes

**Implementation Issues?**
- See `test/SINGLE_DEVICE_DEMO_TEST_GUIDE.md` for troubleshooting
- Check serial output for timing validation
- Use oscilloscope to verify motor PWM and LED patterns

**Contributing Results?**
- Document quantitative measurements (battery, timing)
- Share qualitative assessments (user experience)
- Report any unexpected behavior or insights

---

**End of Specification**

This document contains everything needed to:
1. Implement the single device demo test
2. Conduct the research study
3. Document and compare results
4. Continue development in a new chat session

The test represents a genuine research opportunity to optimize EMDR device battery life while maintaining therapeutic effectiveness - a contribution that could benefit the entire field.
