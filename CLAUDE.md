# EMDR Bilateral Stimulation Device - Claude Code Reference

**Last Updated:** November 4, 2025
**Project Version:** Phase 4 Complete (JPL-Compliant)
**Hardware:** Seeed XIAO ESP32-C6
**Framework:** ESP-IDF v5.5.0 via PlatformIO

---

## Project Overview

This is an open-source EMDR (Eye Movement Desensitization and Reprocessing) bilateral stimulation device designed for therapeutic applications. The device uses dual wireless ESP32-C6 microcontrollers with ERM motors for bilateral tactile stimulation.

**Key Goals:**
- 20+ minute therapeutic sessions with precise bilateral alternation (0.5-2 Hz)
- Open-source research platform for studying motor duty cycle effects
- Reliable, affordable alternative to expensive commercial devices
- JPL coding standards compliance for production-quality embedded software

**Project License:**
- Hardware: CERN-OHL-S v2
- Software: GPL v3

---

## Hardware Platform

**MCU:** Seeed XIAO ESP32-C6
- RISC-V single-core @ 160 MHz
- 512 KB SRAM, 4 MB Flash
- Built-in USB-JTAG for debugging

**Key Peripherals:**
- **Motors:** 2× ERM vibration motors via H-bridge (TB6612FNG)
- **LEDs:** 2× WS2812B RGB LEDs for status feedback
- **Power:** 350mAh LiPo with integrated charging
- **Button:** Single hardware button for mode switching and sleep

**Critical GPIO Constraints:**
- **GPIO19/GPIO20 Crosstalk:** Known hardware issue - cannot use both simultaneously
- **Next PCB Revision:** Button will move to GPIO1 to resolve this

---

## Directory Structure

```
EMDR_PULSER_SONNET4/
├── src/                          # Main source (placeholder - uses test/)
│   └── main.c                    # Empty - actual code in test/
├── test/                         # All functional test programs
│   ├── single_device_demo_jpl_queued.c # **PRIMARY** - Phase 4 JPL-compliant
│   ├── single_device_battery_bemf_test.c # Baseline with battery monitoring
│   ├── single_device_battery_bemf_queued_test.c # Phase 1 (message queues)
│   ├── single_device_demo_test.c # Simple 4-mode demo (no battery)
│   ├── battery_voltage_test.c    # Battery monitoring tests
│   ├── hbridge_pwm_test.c        # Motor PWM control tests
│   ├── ws2812b_test.c            # LED tests
│   └── *.md                      # Test-specific guides
├── docs/                         # Technical documentation
│   ├── architecture_decisions.md # Key design choices (AD format)
│   ├── requirements_spec.md      # Full project specification
│   └── ESP_IDF_*.md             # ESP-IDF specific notes
├── scripts/
│   └── select_source.py          # CMake integration for test selection
├── sdkconfig.*                   # Per-test ESP-IDF configurations
├── platformio.ini                # Build system configuration
└── BUILD_COMMANDS.md             # Essential build commands reference

**Active Development Files (as of Nov 4, 2025):**
- **Primary:** `test/single_device_demo_jpl_queued.c` - Phase 4 JPL-compliant (PRODUCTION-READY)
- **Baseline:** `test/single_device_battery_bemf_test.c` - Research baseline with battery monitoring
- **Simple Demo:** `test/single_device_demo_test.c` - 4-mode demo without battery features
```

---

## Build System

**Platform:** PlatformIO with ESP-IDF v5.5.0

### Essential Commands

```bash
# Build for Phase 4 JPL-compliant (PRIMARY - use these)
pio run -e single_device_demo_jpl_queued -t upload
pio device monitor

# Alternative: Build baseline with battery monitoring
pio run -e single_device_battery_bemf_test -t upload
pio device monitor

# Clean build
pio run -e single_device_demo_jpl_queued -t clean
```

### Available Test Environments

Each test has its own PlatformIO environment and sdkconfig:

- `single_device_demo_jpl_queued` - **PRIMARY** - Phase 4 JPL-compliant (production-ready)
- `single_device_battery_bemf_test` - Baseline with battery + back-EMF monitoring
- `single_device_battery_bemf_queued_test` - Phase 1 (adds message queues)
- `single_device_demo_test` - Simple 4-mode demo (no battery features)
- `battery_voltage_test` - Battery monitoring hardware tests
- `hbridge_pwm_test` - Motor PWM control tests
- `ws2812b_test` - LED functionality tests
- `button_deepsleep_test` - Sleep/wake cycle tests

### Build System Architecture

**Important:** ESP-IDF requires all source files in `src/` at CMake time, but we use `test/` for modular development.

**Solution:** Python pre-build script (`scripts/select_source.py`) that:
1. Copies the active test file to `src/main.c` before CMake runs
2. Preserves test files in `test/` directory
3. Allows clean separation of different functional tests

**Never manually edit `src/main.c`** - it's auto-generated from test files.

---

## Coding Standards & Patterns

### JPL Coding Standards (Power of Ten)

This project follows JPL embedded systems standards:

1. **No dynamic memory allocation** - All memory statically allocated
2. **Fixed loop bounds** - All loops must have deterministic termination
3. **vTaskDelay() for all timing** - No busy-wait loops
4. **Watchdog feeding** - Critical tasks subscribe to watchdog
5. **Explicit error checking** - All ESP-IDF calls wrapped in ESP_ERROR_CHECK()
6. **Defensive logging** - Comprehensive ESP_LOGI() for debugging

### FreeRTOS Task Architecture

```c
// Standard task pattern
void example_task(void *arg) {
    ESP_ERROR_CHECK(esp_task_wdt_add(NULL));  // Subscribe to watchdog
    
    while (session_active) {  // Global flag for clean shutdown
        // Work
        esp_task_wdt_reset();  // Feed watchdog
        vTaskDelay(pdMS_TO_TICKS(50));  // Never busy-wait
    }
    
    ESP_LOGI(TAG, "Task stopping");
    esp_task_wdt_delete(NULL);  // Unsubscribe before exit
    vTaskDelete(NULL);  // Self-delete
}
```

### Motor Duty Cycle Optimization

**Critical Finding:** 125ms ON per 500ms cycle is optimal
- Provides 4× battery life vs. 499ms
- Still exceeds minimum perceptual threshold by 4×
- Therapeutic effectiveness confirmed by EMDRIA standards

### Power Management

**Current Implementation (Phase 1):**
- Tickless idle automatically enabled in ESP-IDF
- Deep sleep on button hold (5s countdown)
- Purple LED blink indicates "release button to sleep"

**Phase 2 Planning (Not Yet Implemented):**
- Explicit light sleep during inter-stimulus intervals
- Dedicated haptic driver ICs (DRV2605L family)
- Advanced power profiling with 350mAh battery constraints

---

## Key Technical Details

### LEDC Timer Configuration

**Critical Constraint:** `frequency × 2^resolution ≤ APB_CLK_FREQ`

```c
// WORKING: 10-bit @ 25 kHz
.freq_hz = 25000,
.duty_resolution = LEDC_TIMER_10_BIT,

// FAILS: 13-bit causes initialization failure
// .duty_resolution = LEDC_TIMER_13_BIT,  // DON'T USE
```

**Why:** APB clock frequency limits on ESP32-C6

### Back-EMF Sensing

Elegant voltage summing approach for ±3.3V motor signals:

```c
// Motor H-bridge produces -3.3V to +3.3V
// ADC accepts 0V to 3.3V
// Solution: Voltage divider with 1.65V offset
V_adc = (V_motor + 3.3V) / 2
```

### Bilateral Alternation Pattern

**Therapeutically Superior:** Alternating > Unilateral  
**EMDRIA Standards:** Bilateral alternation required

```c
// Alternating pattern (500ms cycle)
Motor A: [125ms ON] [375ms OFF]
Motor B: [375ms OFF] [125ms ON]
// Repeat
```

### GPIO Pin Mapping

```c
// Motors (H-bridge TB6612FNG)
#define GPIO_M1_IN1  2  // Motor 1 direction
#define GPIO_M1_IN2  3
#define GPIO_M1_PWM  4  // Motor 1 speed (LEDC)
#define GPIO_M2_IN1  6  // Motor 2 direction
#define GPIO_M2_IN2  7
#define GPIO_M2_PWM  21 // Motor 2 speed (LEDC)

// LEDs (WS2812B via RMT)
#define GPIO_WS2812B_DATA   5  // RMT data pin
#define GPIO_WS2812B_ENABLE 10 // Active-low power enable

// Button
#define GPIO_BUTTON 20  // **TEMPORARY** - moves to GPIO1 in next HW revision

// Back-EMF Sensing
#define GPIO_M1_BEMF 0  // ADC1 Channel 0
#define GPIO_M2_BEMF 1  // ADC1 Channel 1

// Battery Monitoring
#define GPIO_BATTERY_VOLTAGE 23 // ADC through voltage divider
```

---

## Common Development Tasks

### Switching Between Tests

```bash
# Build specific environment
pio run -e single_device_demo_jpl_queued -t upload
pio device monitor

# Or edit platformio.ini to change default_envs
[platformio]
default_envs = single_device_demo_jpl_queued  # Change this line

# Then build
pio run -t upload
pio device monitor
```

### Adding a New Test

1. Create `test/my_new_test.c`
2. Create `sdkconfig.my_new_test` (copy from similar test)
3. Add environment to `platformio.ini`:

```ini
[env:my_new_test]
extends = env:base_esp32c6
build_flags =
    ${env:base_esp32c6.build_flags}
    -DSOURCE_FILE=test/my_new_test.c
board_build.extra_flags =
    -DBOARD_HAS_PSRAM
    -mno-relax
```

4. Build: `pio run -e my_new_test`

### Debugging Serial Output

```bash
# Monitor with filters
pio device monitor --filter colorize --filter time

# Monitor specific baud rate
pio device monitor -b 115200

# Monitor with ESP-IDF filters
pio device monitor --filter esp32_exception_decoder
```

### Viewing GPIO States

Add to your test code:

```c
ESP_LOGI(TAG, "GPIO %d state: %d", GPIO_BUTTON, gpio_get_level(GPIO_BUTTON));
```

### Cleaning Build Artifacts

```bash
# PlatformIO clean
pio run -t clean

# Full clean (nuclear option)
rm -rf .pio/build
```

---

## Important Files & Their Purpose

### Configuration Files

- **platformio.ini** - Build system configuration, environment definitions
- **sdkconfig.\*** - Per-environment ESP-IDF configurations
- **CMakeLists.txt** - ESP-IDF CMake integration (don't edit directly)

### Source Files

- **test/single_device_demo_jpl_queued.c** - Phase 4 JPL-compliant (PRIMARY)
- **test/single_device_battery_bemf_test.c** - Baseline with battery monitoring
- **test/single_device_demo_test.c** - Simple demo (no battery features)
- **src/main.c** - Auto-generated, do not edit manually
- **scripts/select_source.py** - Build system integration script

### Documentation Hierarchy

1. **QUICK_START.md** - First-time setup
2. **BUILD_COMMANDS.md** - Essential build commands
3. **test/README.md** - Overview of all test programs
4. **docs/requirements_spec.md** - Full project specification
5. **docs/architecture_decisions.md** - Design choices (AD format)

### Session Summaries

- **SESSION_SUMMARY_\*.md** - Detailed records of major development milestones
- **UPDATES_2025-01-03.md** - Most recent changes

---

## Known Issues & Workarounds

### 1. GPIO19/GPIO20 Crosstalk

**Issue:** Hardware crosstalk between GPIO19 and GPIO20  
**Status:** Documented in hardware design notes  
**Workaround:** Don't use both simultaneously  
**Fix:** Next PCB revision moves button to GPIO1

### 2. ESP-IDF Build System Constraints

**Issue:** ESP-IDF requires source in `src/` at CMake configuration time  
**Solution:** Python pre-build script copies test files automatically  
**Impact:** Never edit `src/main.c` directly

### 3. LEDC Timer Resolution Limits

**Issue:** 13-bit LEDC resolution fails to initialize  
**Root Cause:** `25000 Hz × 2^13 > APB_CLK_FREQ`  
**Solution:** Use 10-bit resolution (1024 levels, plenty for motor control)

### 4. Watchdog Timeout During Purple Blink Loop

**Issue:** Watchdog timeout during wait-for-button-release in sleep sequence  
**Status:** FIXED in current code  
**Solution:** `button_task` subscribes to watchdog and feeds during purple blink loop  
**Details:** See `/mnt/project/purple_blink_logic_analysis.md` for complete analysis

---

## Development Workflow

### Typical Development Session

1. **Check current status:** Read PHASE_4_COMPLETE_QUICKSTART.md
2. **Build Phase 4:** `pio run -e single_device_demo_jpl_queued -t upload`
3. **Monitor:** `pio device monitor`
4. **Iterate:** Make changes, rebuild, test
5. **Document:** Update session summaries and architecture decisions

### Testing Different Versions

- **Production (Phase 4):** `pio run -e single_device_demo_jpl_queued -t upload`
- **Baseline (with battery):** `pio run -e single_device_battery_bemf_test -t upload`
- **Simple demo (no battery):** `pio run -e single_device_demo_test -t upload`

### Before Committing Changes

1. Ensure code compiles cleanly
2. Test on hardware if possible
3. Update relevant documentation:
   - Architecture decisions (if design changed)
   - Session summary (for major milestones)
   - Test-specific guides (if behavior changed)
4. Follow commit message format: `[Component] Brief description`

Example:
```
[Motor] Optimize duty cycle to 125ms for 4× battery life
```

---

## Recent Analysis & Fixes (November 2025)

### Purple Blink Watchdog Fix (November 4, 2025)

**Issue:** Watchdog timeout during purple LED wait-for-button-release in sleep sequence  
**Root Cause:** After motor_task stops, no task was feeding the watchdog  
**Solution:** button_task now subscribes to watchdog and feeds it during purple blink loop  

**Implementation Details:**
- button_task subscribes via `esp_task_wdt_add(NULL)` at task start
- Feeds watchdog every 200ms during purple blink (`esp_task_wdt_reset()`)
- 200ms feed interval vs 2000ms timeout = 10× safety margin
- Complete analysis: See `purple_blink_logic_analysis.md`

**Status:** ✅ FIXED and tested in Phase 4 implementation

### BLE Initialization Fix (November 5, 2025)

**Issue:** BLE enabled ESP32-C6 showed ZERO serial output after firmware upload - complete device silence
**Symptom:** No bootloader messages, no app_main() logs, nothing - device appeared bricked
**Hardware Status:** Confirmed functional via WiFi test (same 2.4GHz radio hardware)

**Root Cause:** Manual BT controller initialization conflicted with NimBLE's internal init:
```c
// WRONG (causes system freeze before any output):
esp_bt_controller_config_t bt_cfg = BT_CONTROLLER_INIT_CONFIG_DEFAULT();
esp_bt_controller_init(&bt_cfg);          // ❌ Conflicts with NimBLE
esp_bt_controller_enable(ESP_BT_MODE_BLE); // ❌ Conflicts with NimBLE
nimble_port_init();  // This ALSO initializes the BT controller!

// CORRECT (works perfectly):
nimble_port_init();  // ✅ Handles all BT controller setup internally
```

**Why This Happened:**
- Custom code followed older ESP32 examples that manually initialized the controller
- NimBLE in ESP-IDF v5.5.0 handles controller init automatically
- Double initialization caused complete lockup before any serial output could start

**Diagnostic Process:**
1. Created `minimal_wifi_test.c` - Confirmed 2.4GHz radio hardware functional
2. Created `minimal_ble_test.c` - Used official ESP-IDF bleprph example code
3. Systematic comparison identified the double-init bug

**Solution Applied:**
- Removed manual `esp_bt_controller_init()` and `esp_bt_controller_enable()` calls
- Let `nimble_port_init()` handle everything
- Added comprehensive inline comments documenting the fix

**Files Fixed:**
- `test/minimal_ble_test.c` - Diagnostic test (now includes RSSI scanning for RF testing)
- `test/single_device_ble_gatt_test.c` - Main GATT server application

**Status:** ✅ RESOLVED - BLE now works perfectly, full documentation in BLE_DIAGNOSTIC_STRATEGY.md

### Build System Fix (November 4, 2025)

**Issue:** JPL environment only showing "CONFIG_TEST: System running..." heartbeat
**Root Cause:** Missing mapping in `scripts/select_source.py` for `single_device_demo_jpl_queued`
**Symptom:** Build system was compiling old `src/main.c` stub instead of actual JPL source

**Solution:** Added mapping to `scripts/select_source.py`:
```python
"single_device_demo_jpl_queued": "../test/single_device_demo_jpl_queued.c"
```

**Additional Fixes:**
- Increased motor task stack from 3072 to 4096 bytes for stability
- Added stack watermark logging to all three tasks for diagnostics

**Status:** ✅ RESOLVED - JPL version now runs correctly with "JPL_PHASE4" tags

### Tickless Idle Enabled (November 4, 2025)

**Enhancement:** Enabled automatic power management for extended battery life

**Changes to `sdkconfig.single_device_demo_jpl_queued`:**
```ini
CONFIG_PM_ENABLE=y
CONFIG_FREERTOS_USE_TICKLESS_IDLE=y
CONFIG_FREERTOS_IDLE_TIME_BEFORE_SLEEP=3
```

**Benefits:**
- Automatic light sleep during idle periods (e.g., motor coast times)
- No code changes required - handled by FreeRTOS automatically
- Estimated 10-20% battery life improvement
- CPU sleeps when no tasks are active

**Status:** ✅ ENABLED - Now matches Phase 1 power efficiency

---

## Phase 4 Complete - JPL Coding Standards

**Status:** ✅ IMPLEMENTED in `test/single_device_demo_jpl_queued.c`

### Key Features

1. **Message Queues** - Task isolation, no shared state
2. **Button State Machine** - No `goto` statements
3. **All Return Values Checked** - FreeRTOS + ESP-IDF calls
4. **Battery LVO Protection** - Startup check + runtime monitoring
5. **Comprehensive Error Handling** - Graceful degradation

### Phase Evolution

- **Baseline:** `single_device_battery_bemf_test.c` - 4 modes + battery monitoring
- **Phase 1:** `single_device_battery_bemf_queued_test.c` - Adds message queues
- **Phase 4:** `single_device_demo_jpl_queued.c` - Full JPL compliance (PRODUCTION-READY)

**Documentation:**
- **Test-Specific Guide:** `test/SINGLE_DEVICE_DEMO_JPL_QUEUED_GUIDE.md` - Quick reference for JPL environment
- **Comprehensive Guide:** `test/PHASE_4_JPL_QUEUED_COMPLETE_GUIDE.md` - Full JPL compliance details
- **Archived Guides:** `docs/archive/PHASE_*.md` - Development history (Phases 1-3)

---

## Future Work Considerations

### Explicit Light Sleep

Replace tickless idle with manual light sleep calls:

```c
// During inter-stimulus intervals
esp_sleep_enable_timer_wakeup(375 * 1000);  // 375ms in µs
esp_light_sleep_start();
```

### Dedicated Haptic Drivers

Evaluate DRV2605L family:
- Supports both ERM and LRA actuators
- Built-in waveform library
- I2C control interface
- Superior power efficiency

### Advanced Power Profiling

- Measure current draw in all operational modes
- Characterize battery life under various duty cycles
- Validate 20+ minute session target with 350mAh battery

---

## Therapeutic Context

**EMDRIA Standards:**
- Bilateral alternation required (not unilateral)
- Frequency range: 0.5-2 Hz typical
- Session duration: 20+ minutes target

**Research Questions:**
- Effect of motor duty cycle on therapeutic efficacy
- Power consumption vs. perceptual threshold
- Optimal stimulation patterns for different applications

**Potential Applications Beyond EMDR:**
- LED-guided breathing exercises
- Sensory regulation for autism spectrum
- Accessibility applications for motor impairments
- General relaxation/mindfulness support

---

## Quick Reference: File Locations

```
Build Configuration:     platformio.ini
Primary Code (Phase 4):  test/single_device_demo_jpl_queued.c
Test-Specific Guide:     test/SINGLE_DEVICE_DEMO_JPL_QUEUED_GUIDE.md
Comprehensive Guide:     test/PHASE_4_JPL_QUEUED_COMPLETE_GUIDE.md
Baseline Code:           test/single_device_battery_bemf_test.c
Simple Demo:             test/single_device_demo_test.c
GPIO Definitions:        [Within test files]
Build Commands:          BUILD_COMMANDS.md
Quick Start:             PHASE_4_COMPLETE_QUICKSTART.md
Full Spec:               docs/requirements_spec.md
Architecture Decisions:  docs/architecture_decisions.md
Archived Docs:           docs/archive/PHASE_*.md
```

---

## Questions Claude Code Might Ask

**Q: Where is the main application code?**
A: `test/single_device_demo_jpl_queued.c` (Phase 4 production-ready). It's copied to `src/main.c` automatically during build.

**Q: How do I switch between different tests?**
A: Use `pio run -e [environment_name] -t upload`, e.g., `pio run -e single_device_demo_jpl_queued -t upload`.

**Q: Why are there so many sdkconfig files?**
A: Each test needs different ESP-IDF configurations (GPIO, peripherals, power management).

**Q: What's the difference between the test files?**
A:
- `single_device_demo_jpl_queued.c` - Phase 4 JPL-compliant (production-ready)
- `single_device_battery_bemf_test.c` - Baseline with battery + back-EMF monitoring
- `single_device_battery_bemf_queued_test.c` - Phase 1 (adds message queues)
- `single_device_demo_test.c` - Simple 4-mode demo (no battery features)

**Q: Can I add new motor control modes?**
A: Yes! See `mode_t` enum in single_device_demo_jpl_queued.c. Add your mode to the modes array, and the system will automatically cycle through it.

**Q: How do I measure battery life?**  
A: Use battery_voltage_test.c to monitor voltage over time. Current consumption measurements require external equipment.

**Q: Why is the watchdog timeout 2000ms?**  
A: Provides safety margin for motor duty cycles (500ms max) plus task scheduling overhead. Configured in sdkconfig files.

**Q: What happens if the device crashes?**  
A: Watchdog will trigger reset after 2000ms. Check serial logs for panic handler output and backtrace.

---

## Contact & Resources

**Project Documentation:** All documentation is in this repository  
**ESP-IDF Documentation:** https://docs.espressif.com/projects/esp-idf/  
**PlatformIO Documentation:** https://docs.platformio.org/  
**Seeed XIAO ESP32-C6:** https://wiki.seeedstudio.com/xiao_esp32c6_getting_started/

---

## Notes for Claude Code

- **Build before suggesting changes:** Run `pio run -e single_device_demo_jpl_queued` to verify compilation
- **Respect JPL standards:** No malloc, no unbounded loops, all delays via vTaskDelay()
- **Check existing patterns:** Similar functionality probably exists elsewhere in the codebase
- **Preserve test isolation:** Don't mix unrelated changes across test files
- **Document design choices:** Add to architecture_decisions.md if making significant changes
- **Hardware constraints matter:** Remember GPIO limitations, LEDC timing constraints, battery capacity
- **Test on hardware when possible:** Simulators don't catch timing issues or hardware quirks

**Most Important:** The device must be reliable and safe for therapeutic use. When in doubt, ask before making changes that could affect safety or therapeutic effectiveness.
