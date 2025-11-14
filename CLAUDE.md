# EMDR Bilateral Stimulation Device - Claude Code Reference

**Version:** v0.1.2
**Last Updated:** 2025-11-14
**Status:** Production-Ready
**Project Phase:** Phase 1b Complete (Peer Discovery) | Phase 4 Complete (JPL-Compliant)
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
- **Power:** dual 320mAh LiPo batteries (640mAh) with integrated charging
- **Button:** Single hardware button for mode switching and sleep

**Critical GPIO Constraints:**
- **GPIO19/GPIO20 Crosstalk:** ESP32-C6 silicon issue - crosstalk during boot can cause unintended GPIO20 activation (see [docs/GPIO_UPDATE_2025-10-17.md](docs/GPIO_UPDATE_2025-10-17.md) for details)
- **Current Implementation:** Button on GPIO1 (moved from GPIO18 via hardware jumper), GPIO19/20 used for H-bridge IN2/IN1
- **Mitigation:** External pull-downs prevent shoot-through; crosstalk risk remains during boot/reset
- **Future PCB:** May move IN1 from GPIO20 to GPIO18 to eliminate crosstalk entirely

---

## Directory Structure

```
EMDR_PULSER_SONNET4/
├── src/                          # Main source (placeholder - uses test/)
│   └── main.c                    # Empty - actual code in test/
├── test/                         # All functional test programs
│   ├── single_device_demo_jpl_queued.c # **PRIMARY** - Phase 4 JPL-compliant
│   ├── single_device_ble_gatt_test.c # **BLE** - Full NimBLE GATT server with state machines
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

**Active Development Files (as of Nov 8, 2025):**
- **Primary:** `test/single_device_demo_jpl_queued.c` - Phase 4 JPL-compliant (PRODUCTION-READY)
- **BLE Version:** `test/single_device_ble_gatt_test.c` - Full BLE GATT server with 8-state motor machine (PRODUCTION-READY)
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

# Build BLE GATT version with mobile app control
pio run -e single_device_ble_gatt_test -t upload
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
- `single_device_ble_gatt_test` - **BLE** - Full NimBLE GATT server with state machines (production-ready)
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
- Advanced power profiling with dual 320mAh batteries (640mAh)

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
// Production GPIO Mapping (Single Motor Device)
#define GPIO_BACKEMF            0       // Back-EMF sense (ADC1_CH0)
#define GPIO_BUTTON             1       // Button (RTC wake, moved from GPIO18 via jumper)
#define GPIO_BAT_VOLTAGE        2       // Battery voltage (ADC1_CH2)
#define GPIO_STATUS_LED         15      // Status LED (ACTIVE LOW: 0=ON, 1=OFF)
#define GPIO_WS2812B_ENABLE     16      // WS2812B power enable (P-MOSFET, LOW=enabled)
#define GPIO_WS2812B_DIN        17      // WS2812B data input
#define GPIO_HBRIDGE_IN2        19      // H-bridge reverse control (LEDC PWM)
#define GPIO_HBRIDGE_IN1        20      // H-bridge forward control (LEDC PWM)
#define GPIO_BAT_ENABLE         21      // Battery monitor enable (HIGH=enabled)
```

**Note:** For detailed circuit analysis (BEMF filter, battery divider resistor values, etc.), see [docs/architecture_decisions.md](docs/architecture_decisions.md) AD005 and AD021.

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

## BLE GATT Test - State Machine Architecture

**Status:** ✅ PRODUCTION-READY (November 8, 2025)
**File:** `test/single_device_ble_gatt_test.c`
**Build Environment:** `single_device_ble_gatt_test`

### Overview

This is a complete BLE-enabled version with NimBLE GATT server for mobile app control (via nRF Connect or similar apps). It implements explicit state machines for motor control, button handling, and BLE advertising lifecycle.

### Key Features

1. **Full NimBLE GATT Server** - Custom 128-bit UUID service with 9 characteristics
2. **8-State Motor Task** - Instant mode switching with safe cleanup
3. **4-State BLE Task** - Advertising lifecycle management with shutdown handling
4. **4-State Button Task** - Mode changes, emergency shutdown, BLE re-enable
5. **NVS Persistence** - Mode 5 settings saved across power cycles
6. **Back-EMF Integration** - Research measurements during first 10 seconds of mode changes

### Motor State Machine (8 States)

**Design Goal:** Instant mode switching (< 100ms latency) with safe motor coast

```
CHECK_MESSAGES → FORWARD_ACTIVE → BEMF_IMMEDIATE → COAST_SETTLE → FORWARD_COAST_REMAINING
                                                                     ↓
                                                      REVERSE_COAST_REMAINING ← COAST_SETTLE ← BEMF_IMMEDIATE ← REVERSE_ACTIVE
                                                                     ↓
                                                                  SHUTDOWN
```

**Key States:**
- `CHECK_MESSAGES` - Process mode changes, shutdown, battery messages
- `FORWARD_ACTIVE` / `REVERSE_ACTIVE` - Motor PWM active
- `BEMF_IMMEDIATE` / `COAST_SETTLE` - Back-EMF sampling (shared between directions)
- `FORWARD_COAST_REMAINING` / `REVERSE_COAST_REMAINING` - Complete coast period
- `SHUTDOWN` - Final cleanup before task exit

**Critical Features:**
- **Instant mode switching:** `delay_with_mode_check()` checks queue every 50ms during delays
- **Safe cleanup:** `motor_coast()` and `led_clear()` called in ALL state transition paths
- **Queue purging:** Multiple rapid mode changes → only last one takes effect
- **Shared back-EMF states:** Reduces complexity from 10 to 8 states

### BLE State Machine (4 States)

**Design:** Simple lifecycle management for advertising and client connections

```
IDLE → ADVERTISING → CONNECTED
  ↑        ↓            ↓
  └────────┴────────────┘
           ↓
       SHUTDOWN
```

**Analysis Result:** Grade A - No critical bugs found
**Why it's safer:** Simpler message handling (if vs while), conditional-only state transitions

### Mobile App Control (GATT Characteristics)

**Service UUID:** `a1b2c3d4-e5f6-7890-a1b2-c3d4e5f67890` (custom 128-bit)

| Characteristic | Read | Write | Notify | Description |
|----------------|------|-------|--------|-------------|
| Mode | ✅ | ✅ | | Current mode (0-4) |
| Custom Frequency | ✅ | ✅ | | Hz × 100 (0.5-2.0 Hz) |
| Custom Duty Cycle | ✅ | ✅ | | Percentage (10-50%) |
| Battery Level | ✅ | | ✅ | Battery % (0-100) |
| Session Time | ✅ | | ✅ | Elapsed seconds |
| LED Enable | ✅ | ✅ | | LED on/off for Mode 5 |
| LED Color | ✅ | ✅ | | 16-color palette index |
| LED Brightness | ✅ | ✅ | | Brightness % (10-30%) |
| PWM Intensity | ✅ | ✅ | | Motor PWM % (0-80%, 0%=LED-only) |

### Critical Bugs Fixed During Development

**Bug #1: State Overwrite After Shutdown** (CRITICAL)
- **Symptom:** Emergency shutdown never stopped motor, no purple blink
- **Root Cause:** `break` inside queue receive loop only exited inner loop, not switch case
- **Result:** Shutdown state overwritten by unconditional transition to FORWARD
- **Fix:** Added state guard before all forward transitions

**Bug #2-#3: Missing Cleanup** (CRITICAL)
- **Symptom:** LED always on, motor stuck running
- **Root Cause:** Missing `motor_coast()` / `led_clear()` in non-sampling code paths
- **Fix:** Added explicit cleanup in ALL state transition paths

**Bug #4: Button Task Message Spam**
- **Symptom:** Continuous "Emergency shutdown" logging after shutdown message sent
- **Root Cause:** No terminal state after sending shutdown message
- **Fix:** Added `BTN_STATE_SHUTDOWN_SENT` terminal state

**Bug #5: Watchdog Timeout**
- **Symptom:** Watchdog timeout during normal operation
- **Root Cause:** Motor task subscribed to watchdog but only fed it in purple blink loop
- **Fix:** Feed watchdog in CHECK_MESSAGES state every cycle

**Bug #6: BLE Parameter Update Latency**
- **Symptom:** BLE parameter changes delayed up to 1 second
- **Root Cause:** Motor task only reloaded parameters in CHECK_MESSAGES (once per cycle)
- **Fix:** Added `ble_params_updated` flag checked in `delay_with_mode_check()`

### State Machine Analysis

**Methodology:** Systematic checklist-based analysis (see `docs/STATE_MACHINE_ANALYSIS_CHECKLIST.md`)

**Motor Task:** 8 states, multiple critical bugs found and fixed
**BLE Task:** 4 states, NO critical bugs found (simpler design inherently safer)
**Button Task:** 5 states, one bug fixed (message spam)

**Key Learning:** Simpler state machines with fewer states and less complex control flow are less error-prone.

### Build & Test

```bash
# Build and upload
pio run -e single_device_ble_gatt_test -t upload

# Monitor output
pio device monitor

# Connect via nRF Connect app
# Device name: "EMDR_Pulser"
# Service UUID: a1b2c3d4-e5f6-7890-a1b2-c3d4e5f67890
```

### Documentation

- **Test Guide:** `test/SINGLE_DEVICE_BLE_GATT_TEST_GUIDE.md` - Complete GATT reference
- **Refactoring Plan:** `test/MODE_SWITCH_REFACTORING_PLAN.md` - State machine implementation details
- **BLE Task Analysis:** `test/BLE_TASK_STATE_MACHINE_ANALYSIS.md` - Comprehensive audit (400+ lines)
- **Analysis Checklist:** `docs/STATE_MACHINE_ANALYSIS_CHECKLIST.md` - Reusable audit template

### Comparison to Phase 4 JPL Version

| Aspect | Phase 4 JPL | BLE GATT Test |
|--------|-------------|---------------|
| **BLE Support** | No | ✅ Full NimBLE GATT |
| **Mobile App Control** | No | ✅ 9 GATT characteristics |
| **Mode Switching** | Button only | Button + BLE writes |
| **State Machine** | Message queues | ✅ Explicit state machines |
| **Mode Switch Latency** | Variable | < 100ms (instant) |
| **Back-EMF Sampling** | No | ✅ First 10 seconds after mode change |
| **NVS Persistence** | No | ✅ Mode 5 settings saved |
| **Code Complexity** | Lower | Higher (state machines) |
| **Production Status** | ✅ Ready | ✅ Ready |

**Use Phase 4 JPL when:** Simple button-only control is sufficient
**Use BLE GATT when:** Mobile app control and research data collection needed

---

## Phase 1b - Peer Discovery and Initial Role Assignment

**Status:** ✅ COMPLETE (November 14, 2025)
**Build Environment:** `xiao_esp32c6` (modular architecture)

### Overview

Phase 1b implements peer-to-peer device discovery for dual-device bilateral stimulation. Two EMDR devices can now discover each other, connect, and exchange battery information for future role assignment.

### Key Features Implemented

1. **Peer Discovery** (`src/ble_manager.c`):
   - Both devices advertise Bilateral Control Service UUID (`4BCAE9BE-9829-4F0A-9E88-267DE5E70100`)
   - Both devices scan for peer advertising same service
   - First device to discover peer initiates connection
   - Connection time: ~1-2 seconds

2. **Connection Type Identification**:
   - `ble_is_peer_connected()` - Check if connected to peer device
   - `ble_get_connection_type_str()` - Returns "Peer", "App", or "Disconnected"
   - Motor task battery logs show connection status every 60 seconds

3. **Battery Exchange** (GATT Characteristic):
   - Bilateral Battery characteristic (`6E400A01-B5A3-...`)
   - `ble_update_bilateral_battery_level()` called every 60 seconds by motor_task
   - Allows peer devices to read battery level for role assignment (Phase 1c)

4. **Race Condition Handling** (per AD010):
   - Error `BLE_ERR_ACL_CONN_EXISTS` (523) gracefully handled
   - Fallback logic for connection-before-scan-event scenarios
   - Devices successfully reconnect after disconnect

### Battery Status Logging

Motor task now shows connection type in battery logs (`src/motor_task.c:269`):
```
Battery: 4.16V [96%] | BLE: Peer          ← Peer device connected
Battery: 4.10V [89%] | BLE: App           ← Mobile app connected
Battery: 3.95V [72%] | BLE: Disconnected  ← No connection
```

### UUID Architecture (AD032)

Phase 1b changed from Nordic UART Service UUID to project-specific UUID base to prevent collision:

```
Project UUID Base: 4BCAE9BE-9829-4F0A-9E88-267DE5E7XXYY
                                                ↑↑ ↑↑
                                            Service Char

Bilateral Control Service: 4BCAE9BE-9829-4F0A-9E88-267DE5E70100
Configuration Service:     4BCAE9BE-9829-4F0A-9E88-267DE5E70200
```

### Known Issues (Documented in AD035)

1. **Advertising Timer Loop** (Cosmetic, Does Not Block Functionality):
   - After peer disconnect, rapid IDLE→ADVERTISING→timeout loop occurs (~100ms cycles)
   - Root cause: `ble_get_advertising_elapsed_ms()` returns time since boot, not since restart
   - Impact: Noisy logging only - devices successfully reconnect despite loop
   - Fix: Deferred to Phase 1c

2. **Status LED 5× Blink Not Visible**:
   - `status_led_pattern()` called on peer connection (logs confirm)
   - User observes NO LED blinks on GPIO15 (hardware confirmed functional via button hold test)
   - Root cause: Unknown (timing issue or state conflict suspected)
   - Impact: Minor - connection still works, only visual feedback missing
   - Fix: Deferred to Phase 1c investigation

3. **Mobile App Cannot Connect When Devices Peer-Paired** (BLOCKING):
   - nRF Connect sees advertising but cannot connect when devices are peer-paired
   - Connection attempts fail silently (no logs, no connection event)
   - **Impact: Cannot configure devices via mobile app while peer-paired**
   - Workaround: Restart device to break peer connection, connect mobile app before re-pairing
   - Proposed solutions: SERVER-only Configuration Service advertising, or peer disconnect via button
   - Fix: Phase 1c/2 architecture decision needed (see AD035 for full analysis)

### Testing Evidence

```
11:09:01.749 > Peer discovered: b4:3a:45:89:5c:76
11:09:01.949 > BLE connection established
11:09:01.963 > Peer identified by address match
11:09:01.969 > Peer device connected
11:09:27.452 > Battery: 4.18V [98%] | BLE: Peer  ← Correct!
```

### Architecture Decisions

- **AD010**: Race Condition Prevention Strategy (updated with Phase 1b implementation)
- **AD032**: BLE Service UUID Namespace (project-specific UUID base)
- **AD035**: Battery-Based Initial Role Assignment (Phase 1b foundation)

### Next Steps

🚨 **Phase 1b.1 (REQUIRED before Phase 1c):**
- **Fix BLOCKING Issue #3**: Enable mobile app connection when devices are peer-paired
- **Proposed solution**: Only SERVER advertises Configuration Service when peer-paired
- **Implementation**: CLIENT stops advertising Configuration Service after peer connection established
- **Alternative**: Enable NimBLE simultaneous connections (SERVER accepts peer + mobile app)
- **Priority**: MUST be resolved - this is a project requirement for mobile app control

⏳ **Phase 1c (After 1b.1 complete):**

**Role Assignment Logic:**
- Implement `role_manager.c` with battery comparison
- Add `ble_get_peer_battery_level()` to read peer's battery characteristic
- Assign SERVER role to device with higher battery, CLIENT to lower
- Tie-breaker: Connection initiator becomes SERVER if batteries equal
- Update motor task logs to show role: `BLE: Peer (SERVER)` vs `BLE: Peer (CLIENT)`

⏳ **Device Role Characteristic:**
- Add Device Role GATT characteristic to Bilateral Control Service
- Store assigned role (SERVER=0, CLIENT=1, STANDALONE=2)
- Allow role reassignment if battery levels flip

### Build & Test

```bash
# Build Phase 1b (modular architecture)
pio run -e xiao_esp32c6 -t upload

# Monitor output
pio device monitor

# Test with two devices
# - Power on both devices within ~10 seconds
# - Watch for "Peer discovered" and "BLE connection established" in logs
# - Verify battery logs show "BLE: Peer" after connection
# - Test disconnect/reconnect by power cycling one device
```

### Documentation

- **Architecture Decisions**: `docs/architecture_decisions.md` (AD010, AD032, AD035)
- **Command-and-Control**: `docs/architecture_decisions.md` (AD028 - Phase 1b status added)
- **Bilateral Control Service**: `docs/architecture_decisions.md` (AD030 - Phase 1b status added)
- **Session Summary**: `SESSION_SUMMARY_PHASE_1B.md` (to be created)

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
- Validate 20+ minute session target with dual 320mAh batteries (640mAh)

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
Phase 1b (Modular):      src/*.c (ble_manager, motor_task, ble_task, button_task)
Primary Code (Phase 4):  test/single_device_demo_jpl_queued.c
BLE GATT Code:           test/single_device_ble_gatt_test.c
Test-Specific Guide:     test/SINGLE_DEVICE_DEMO_JPL_QUEUED_GUIDE.md
BLE GATT Guide:          test/SINGLE_DEVICE_BLE_GATT_TEST_GUIDE.md
Comprehensive Guide:     test/PHASE_4_JPL_QUEUED_COMPLETE_GUIDE.md
Baseline Code:           test/single_device_battery_bemf_test.c
Simple Demo:             test/single_device_demo_test.c
GPIO Definitions:        [Within test files and src/*.h]
Build Commands:          BUILD_COMMANDS.md
Quick Start:             PHASE_4_COMPLETE_QUICKSTART.md
Full Spec:               docs/requirements_spec.md
Architecture Decisions:  docs/architecture_decisions.md (AD010, AD028, AD030, AD032, AD035)
State Machine Analysis:  docs/STATE_MACHINE_ANALYSIS_CHECKLIST.md
BLE Task Analysis:       test/BLE_TASK_STATE_MACHINE_ANALYSIS.md
Mode Switch Refactor:    test/MODE_SWITCH_REFACTORING_PLAN.md
Archived Docs:           docs/archive/PHASE_*.md
```

---

## Questions Claude Code Might Ask

**Q: Where is the main application code?**
A: Two production-ready versions exist:
- `test/single_device_demo_jpl_queued.c` - Phase 4 JPL-compliant (button-only control)
- `test/single_device_ble_gatt_test.c` - BLE GATT server with state machines (mobile app control)

Both are automatically copied to `src/main.c` during build.

**Q: How do I switch between different tests?**
A: Use `pio run -e [environment_name] -t upload`, e.g.:
- `pio run -e single_device_demo_jpl_queued -t upload` (Phase 4 JPL)
- `pio run -e single_device_ble_gatt_test -t upload` (BLE GATT)

**Q: Why are there so many sdkconfig files?**
A: Each test needs different ESP-IDF configurations (GPIO, peripherals, power management, BLE stack).

**Q: What's the difference between the test files?**
A:
- `single_device_demo_jpl_queued.c` - Phase 4 JPL-compliant, button-only (production-ready)
- `single_device_ble_gatt_test.c` - Full BLE GATT server, state machines, mobile app control (production-ready)
- `single_device_battery_bemf_test.c` - Baseline with battery + back-EMF monitoring
- `single_device_battery_bemf_queued_test.c` - Phase 1 (adds message queues)
- `single_device_demo_test.c` - Simple 4-mode demo (no battery features)

**Q: What is Phase 1b and how do I build it?**
A: Phase 1b is peer-to-peer device discovery for dual-device bilateral stimulation (modular architecture in `src/`).
- Build: `pio run -e xiao_esp32c6 -t upload`
- Features: Peer discovery, connection type identification, battery exchange for role assignment
- Status: Phase 1b complete (peer discovery), Phase 1c pending (role assignment logic)

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
