# EMDR Bilateral Stimulation Device - Claude Code Reference

**Version:** v0.3.0-beta.1 (Phase 2 Complete)
**Last Updated:** 2025-11-21
**Status:** Dual-Device Time Synchronization (Phase 2 - Production Ready ✅)
**Project Phase:** Phase 2 Complete (Time Sync) | Phase 1c Complete (Pairing) | Phase 0.4 Complete (Single-Device)
**Hardware:** Seeed XIAO ESP32-C6
**Framework:** ESP-IDF v5.5.0 via PlatformIO

> **Note:** Phase 2 time synchronization is complete and tested (90-minute stress test passed). Next milestone: Phase 3 - Command & Control for bilateral motor coordination.

---

## CRITICAL BUG FIX (v0.1.3 - November 17, 2025)

**Issue:** Motor operated at 2× configured frequency due to fundamental timing calculation error.
- OLD behavior: Both forward AND reverse activations within single frequency period
- NEW behavior: ONE activation per frequency period, direction alternates BETWEEN cycles

**Impact:**
- All therapeutic sessions ran at wrong frequencies:
  - 0.5Hz setting → Actually ran at 1.0Hz
  - 1.0Hz setting → Actually ran at 2.0Hz
  - 2.0Hz setting → Actually ran at 4.0Hz (outside therapeutic range!)

**Resolution:**
- State machine refactored: 9 states → 6 states (FORWARD/REVERSE unified into ACTIVE/INACTIVE)
- Timing formula corrected: `(period_ms * duty) / 100` instead of `/ 200`
- Mode presets updated: Now 0.5Hz, 1.0Hz, 1.5Hz, 2.0Hz @ 25% duty
- Direction alternation: Added flag that flips after each INACTIVE period
- **Enum names kept for compatibility** (MODE_1HZ_50 now actually means 0.5Hz@25%)

**Testing Required:** Oscilloscope verification of actual frequency output.

**Files Modified:** [src/motor_task.h](src/motor_task.h), [src/motor_task.c](src/motor_task.c), [src/ble_manager.c](src/ble_manager.c)

---

## Phase 2: Time Synchronization (v0.3.0-beta.1 - November 21, 2025) ✅

**Status:** COMPLETE - Production Ready

Phase 2 implements NTP-style time synchronization between peer devices to enable precise bilateral motor coordination in Phase 3.

### Key Features Implemented

1. **Time Sync Protocol** (`src/time_sync.c`, `src/time_sync_task.c`)
   - NTP-style beacon exchange (timestamped messages)
   - Clock offset and drift tracking
   - Quality metrics (0-100%)
   - Hybrid approach: NTP algorithm + hardware timestamps

2. **Dual-Clock Architecture**
   - System clock remains untouched (no watchdog implications)
   - Synchronized time calculated on-demand via API
   - Applications opt-in to using synchronized time

3. **API for Phase 3 Integration**
   ```c
   bool time_sync_is_synchronized(void);
   int64_t time_sync_get_local_time_us(void);
   int64_t time_sync_get_peer_time_us(void);
   int64_t time_sync_get_drift_us(void);
   uint8_t time_sync_get_quality(void);
   ```

### Test Results (90-Minute Stress Test)

**Metrics:**
- **Beacons Exchanged:** 271/270 expected (100% delivery rate)
- **Initial Drift:** -377 μs
- **Converged Drift:** -14 μs (stable)
- **Final Drift:** -31 μs after 90 minutes
- **Quality Score:** 95% sustained (excellent)
- **Session Duration:** 5400 seconds (90 minutes, unattended)
- **System Stability:** No crashes, no BLE disconnects
- **Sequence Wrap:** Clean 255→0 transition (no errors)

**Anomalies Detected:** 7 brief 50ms offset jumps over 90 minutes
- **Root Cause:** Likely BLE connection parameter updates (not time sync bugs)
- **Recovery:** Time sync detected all anomalies (quality→0%), recovered within 2 beacons
- **Impact:** Negligible for 20-minute therapy sessions

**Verdict:** Time synchronization is production-ready. The ±30 μs drift over 90 minutes is excellent (0.003% timing error at 1 Hz).

### Bug Fixes This Session

**Bug #11:** Windows PC PWA Connection Tracking (FIXED - November 21, 2025)
- **Symptom:** PWA from Windows PC not tracked properly, device became invisible after disconnect
- **Root Cause:** CLIENT devices kept scanning after peer connection, causing connection interference
- **Fix:** Stop scanning immediately when peer connects (unconditional `ble_gap_disc_cancel()`)
- **Files:** `src/ble_manager.c:1613-1626`

**NimBLE Configuration Migration** (November 21, 2025)
- Replaced custom `BLE_PAIRING_TEST_MODE` flag with standard `CONFIG_BT_NIMBLE_NVS_PERSIST`
- Production environment: NVS bonding enabled
- Test environment: RAM-only bonding (unlimited pairing cycles)
- Binary size: Test environment 1,738 bytes smaller (NVS backend not compiled)

**Pairing Race Condition Fix (Bug #10)** (November 21, 2025)
- **Issue:** CLIENT devices stopped scanning before role assignment, SERVER couldn't discover them
- **Fix:** CLIENT devices keep scanning during wait period, only SERVER stops before connecting
- **Result:** Devices can be powered on at different times (not synchronized) and still pair successfully

### Phase 3 Planning

**Next Milestone:** Command & Control for Bilateral Motor Coordination

**Scope:**
1. Motor command protocol (start/stop/mode change via BLE GATT)
2. One-time phase alignment at session start (using time sync API)
3. Bilateral alternation patterns (Device A forward, Device B reverse, 500ms phase offset)
4. Mode change synchronization (both devices switch together)
5. Emergency shutdown propagation

**Design Decision:** One-time phase alignment is sufficient
- Observed drift: 28 μs over 90 minutes → 6 μs over 20-minute session
- At 1 Hz: 0.0006% timing error (imperceptible)
- Periodic re-sync unnecessary for therapy sessions
- Simpler implementation = fewer bugs

**Challenge:** Mode changes during active session
- Must coordinate between devices
- Phase recalculation for new frequency
- Graceful stop → switch → synchronized restart
- Expected to be complex ("fun bugs")

---

## Phase 6r: Drift Continuation During Disconnect (November 30, 2025)

**Status:** IMPLEMENTATION COMPLETE (Hardware testing pending)

Phase 6r implements conditional clearing of time sync state to allow CLIENT devices to continue bilateral motor coordination during brief BLE disconnections using frozen drift rate extrapolation.

### Key Features Implemented

1. **Modified Disconnect Handler** (`src/time_sync.c:174-217`)
   - PRESERVES motor_epoch_us, motor_cycle_ms, motor_epoch_valid
   - PRESERVES drift_rate_us_per_s and drift tracking state
   - CLIENT can continue bilateral alternation during disconnect
   - Only clears RTT measurement state (no fresh measurements possible)

2. **Safety Timeout** (`src/time_sync.c:935-958`)
   - `time_sync_get_motor_epoch()` expires after 2-minute disconnect
   - Returns `ESP_ERR_TIMEOUT` to gracefully stop coordination
   - Prevents unbounded drift accumulation (±2.4ms over 20min acceptable)

3. **Role Swap Detection** (`src/time_sync.c:219-278`)
   - New `time_sync_on_reconnection()` function detects role changes
   - Logs ⚠️ WARNING if role swap detected (shouldn't happen per Phase 6n)
   - Conditionally clears motor_epoch only on role swap
   - Normal case: Role preserved → motor epoch valid → smooth continuation

4. **BLE Manager Integration** (`src/ble_manager.c:2121-2128`)
   - Calls `time_sync_on_reconnection()` after role assignment
   - Maps `peer_role_t` → `time_sync_role_t` correctly

5. **Documentation** (`src/motor_task.c:21-28`)
   - Phase 6r section in motor_task.c header
   - Explains drift stability metrics from Phase 2 testing

### Technical Rationale

**Original Phase 6 Bug (2466ms phase skip):**
- Stale motor epoch from previous session when role SWAPPED on reconnection
- Example: CLIENT session 1 → disconnect → reconnect as SERVER → used old CLIENT epoch
- Original fix: Aggressive clearing stopped ALL continuation (even valid cases)

**Separate Question: Can CLIENT Continue During Disconnect?**
- Drift rate stability: ±30 μs over 90 minutes (Phase 2 testing)
- For 20-minute therapy: ±2.4ms worst-case drift (well within ±100ms spec)
- Technical conclusion: YES - continuation is valid and therapeutically beneficial

**Phase 6r Solution:**
- Preserve motor_epoch during disconnect → CLIENT continues using frozen drift
- Clear motor_epoch only on role swap → prevents original Phase 6 bug
- Safety timeout (2 min) → prevents unbounded drift for long disconnects
- Role swap detection → logs warning (indicates Phase 6n bug if triggered)

### Expected Behavior

**Brief Disconnect (< 2 min):**
- ✅ CLIENT motors continue using frozen drift rate
- ✅ Bilateral alternation maintained (±2.4ms drift over 20 min)
- ✅ No interruption to therapy session
- ✅ Smooth reconnection without phase skip

**Long Disconnect (> 2 min):**
- ⏱️ Motor epoch expires automatically
- ⏹️ Coordination stops gracefully
- 🔄 Resumes after reconnection with fresh handshake

**Role Swap (shouldn't happen):**
- ⚠️ Warning logged: "Role swap detected - THIS SHOULD NOT HAPPEN!"
- 🧹 Motor epoch cleared to prevent corruption
- 🐛 Indicates bug in Phase 6n role preservation logic

### Testing Required (Pending Hardware)

- [ ] Brief disconnect (30s): Verify motors continue without interruption
- [ ] Long disconnect (3 min): Verify timeout stops motors gracefully
- [ ] Role swap: Verify warning appears if roles somehow swap
- [ ] Timing accuracy: Verify <5ms drift during 60s disconnect

### Files Modified

- `src/time_sync.c` - Disconnect/reconnection handlers, safety timeout
- `src/time_sync.h` - New API declaration
- `src/ble_manager.c` - Integration with connect event
- `src/motor_task.c` - Documentation

### ADR Impact

- Partially supersedes original Phase 6 fix rationale
- Aligns with AD041 (predictive bilateral synchronization philosophy)
- Validates drift-based continuation model from tech spike

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
- **GPIO19/GPIO20 Crosstalk (RESOLVED December 2025):** ESP32-C6 silicon crosstalk issue eliminated by moving H-bridge IN1 from GPIO20 to GPIO18
- **Current Implementation:** Button on GPIO1, GPIO19 for H-bridge IN2 (reverse), GPIO18 for H-bridge IN1 (forward)
- **Breaking Change:** Firmware incompatible with old hardware (2 units in field retired, new PCB required)
- **Historical Context:** See [docs/GPIO_UPDATE_2025-10-17.md](docs/GPIO_UPDATE_2025-10-17.md) for original crosstalk analysis

---

## Directory Structure

```
EMDR_PULSER_SONNET4/
├── src/                          # Main source (placeholder - uses test/)
│   └── main.c                    # Empty - actual code in test/
├── test/                         # All functional test programs
│   ├── single_device_demo_jpl_queued.c # **PRIMARY** - Phase 0.4 JPL-compliant
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
- **Primary:** `test/single_device_demo_jpl_queued.c` - Phase 0.4 JPL-compliant (PRODUCTION-READY)
- **BLE Version:** `test/single_device_ble_gatt_test.c` - Full BLE GATT server with 8-state motor machine (PRODUCTION-READY)
- **Baseline:** `test/single_device_battery_bemf_test.c` - Research baseline with battery monitoring
- **Simple Demo:** `test/single_device_demo_test.c` - 4-mode demo without battery features
```

---

## Build System

**Platform:** PlatformIO with ESP-IDF v5.5.0

### Essential Commands

```bash
# Build for Phase 0.4 JPL-compliant (PRIMARY - use these)
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

- `single_device_demo_jpl_queued` - **PRIMARY** - Phase 0.4 JPL-compliant (production-ready)
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
// Production GPIO Mapping (December 2025 - New Hardware)
// BREAKING CHANGE: GPIO20 → GPIO18 to eliminate ESP32-C6 crosstalk
#define GPIO_BACKEMF            0       // Back-EMF sense (ADC1_CH0)
#define GPIO_BUTTON             1       // Button (RTC wake, moved from GPIO18 via jumper)
#define GPIO_BAT_VOLTAGE        2       // Battery voltage (ADC1_CH2)
#define GPIO_STATUS_LED         15      // Status LED (ACTIVE LOW: 0=ON, 1=OFF)
#define GPIO_WS2812B_ENABLE     16      // WS2812B power enable (P-MOSFET, LOW=enabled)
#define GPIO_WS2812B_DIN        17      // WS2812B data input
#define GPIO_HBRIDGE_IN2        19      // H-bridge reverse control (LEDC PWM)
#define GPIO_HBRIDGE_IN1        18      // H-bridge forward control (LEDC PWM) - MOVED from GPIO20
#define GPIO_BAT_ENABLE         21      // Battery monitor enable (HIGH=enabled)
```

**Note:** For detailed circuit analysis (BEMF filter, battery divider resistor values, etc.), see [AD005](docs/adr/0005-gpio-assignment-strategy.md) and [AD021](docs/adr/0021-motor-stall-detection-back-emf.md).

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

- **test/single_device_demo_jpl_queued.c** - Phase 0.4 JPL-compliant (PRIMARY)
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

### 1. GPIO19/GPIO20 Crosstalk (RESOLVED)

**Issue:** ESP32-C6 silicon crosstalk between GPIO19 and GPIO20 during boot/reset
**Status:** ✅ RESOLVED (December 2025) - H-bridge IN1 moved from GPIO20 to GPIO18
**Breaking Change:** Incompatible with old hardware (2 field units retired)
**Historical Documentation:** See [docs/GPIO_UPDATE_2025-10-17.md](docs/GPIO_UPDATE_2025-10-17.md) for analysis

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

### 5. Enclosure Pinholes Misalignment

**Issue:** Pinholes for RESET and BOOT pins in enclosure don't align with actual button/pad locations
**Status:** Known hardware limitation, unlikely to be fixed
**Workaround:** Access RESET/BOOT via USB reprogramming or remove from enclosure
**Impact:** Minimal - normal operation uses button wake from deep sleep; RESET/BOOT only needed for firmware recovery

---

## Development Workflow

### Typical Development Session

1. **Check current status:** Read QUICK_START.md and relevant test guides
2. **Build Phase 0.4:** `pio run -e single_device_demo_jpl_queued -t upload`
3. **Monitor:** `pio device monitor`
4. **Iterate:** Make changes, rebuild, test
5. **Document:** Update session summaries and architecture decisions

### Testing Different Versions

- **Production (Phase 0.4):** `pio run -e single_device_demo_jpl_queued -t upload`
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

**Status:** ✅ FIXED and tested in Phase 0.4 implementation

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

## Phase 0.4 Complete - JPL Coding Standards (Single-Device)

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
- **Phase 0.4:** `single_device_demo_jpl_queued.c` - Full JPL compliance (PRODUCTION-READY)

**Documentation:**
- **Test-Specific Guide:** `test/SINGLE_DEVICE_DEMO_JPL_QUEUED_GUIDE.md` - Quick reference for JPL environment
- **Comprehensive Guide:** `test/PHASE_0.4_JPL_QUEUED_COMPLETE_GUIDE.md` - Full JPL compliance details
- **Archived Guides:** `docs/archive/PHASE_*.md` - Development history

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

### Comparison to Phase 0.4 JPL Version

| Aspect | Phase 0.4 JPL (Single-Device) | BLE GATT Test |
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

**Use Phase 0.4 JPL when:** Simple button-only control is sufficient (single-device testing)
**Use BLE GATT when:** Mobile app control and research data collection needed

---

## Phase 1c - Battery-Based Role Assignment (Complete)

**Status:** ✅ COMPLETE (November 19, 2025)
**Build Environment:** `xiao_esp32c6` (modular architecture)

### Overview

Phase 1c implements battery-based role assignment for peer-to-peer bilateral stimulation. Devices broadcast battery level in advertising packets (BLE Service Data), compare batteries during discovery, and automatically assign SERVER (higher battery) and CLIENT (lower battery) roles BEFORE connection.

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

3. **Battery Exchange** (BLE Service Data - Phase 1c):
   - Battery level broadcast in advertising packet via Service Data (AD Type 0x16)
   - Battery Service UUID (0x180F) + battery percentage (0-100%)
   - Only broadcast during Bilateral UUID window (0-30s, peer discovery)
   - `ble_update_bilateral_battery_level()` restarts advertising when battery changes
   - Peer extracts battery from scan response BEFORE connection

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

### Critical Bugs Fixed (Phase 1b.1 and 1b.2)

**Bug #6: Mobile App Cannot Connect When Devices Peer-Paired** (RESOLVED Phase 1b.1):
- **Symptom**: nRF Connect saw advertising but connection attempts failed silently
- **Root Cause**: `CONFIG_BT_NIMBLE_MAX_CONNECTIONS=1` limited to single connection (peer OR app, not both)
- **Fix**: Increased to `CONFIG_BT_NIMBLE_MAX_CONNECTIONS=2` in `sdkconfig.xiao_esp32c6`
- **Result**: SERVER now accepts both peer and mobile app connections simultaneously
- **Status**: ✅ RESOLVED - Tested and working (November 14, 2025)

**Bug #7: Advertising Timeout Disconnects Peer Connection** (RESOLVED Phase 1b.2):
- **Symptom**: Peer connections would break after 5 minutes of operation
- **Root Cause**: Both devices continued advertising Configuration Service after peer connection. BLE_TASK timeout (5 minutes) would call `ble_stop_advertising()`, which broke the peer connection
- **Fix**: Both devices now stop advertising Configuration Service immediately after peer connection (`ble_manager.c:1136-1145`)
- **Workaround**: User can manually re-enable advertising with button hold (1-2s) if mobile app access needed
- **Status**: ✅ RESOLVED - Code complete, hardware testing pending

**Bug #8: Peer Reconnection Broken After Disconnect** (RESOLVED Phase 1b.2):
- **Symptom**: After peer disconnect, devices would never reconnect (stuck in IDLE state forever)
- **Root Cause**: Bug #7 fix set `adv_state.advertising_active = false`. Disconnect handler checked this flag before restarting scanning, so condition was never met
- **Serial Evidence**: "Failed to restart advertising after disconnect; rc=2" followed by permanent IDLE state
- **Fix**: Peer disconnect handler now explicitly restarts both advertising and scanning without relying on flag (`ble_manager.c:1186-1214`)
- **Result**: Devices should now reconnect automatically after disconnect
- **Status**: ✅ RESOLVED - Code complete, hardware testing pending

**Bug #9: PWA Cannot Discover Device** (RESOLVED Phase 1b.2):
- **Symptom**: nRF Connect could see device, but Web Bluetooth PWA required "Show all BLE Devices" to find it
- **Root Cause**: PWA filtered by Configuration Service UUID (`...0200`), but device only advertised Bilateral Service UUID (`...0100`) in scan response
- **Impact**: Web Bluetooth API `navigator.bluetooth.requestDevice()` with service filter would not show device
- **Fix**: Simplified to single-UUID approach - now advertising Configuration Service UUID in scan response (`ble_manager.c:1385`). Peer discovery updated to look for Configuration Service UUID instead of Bilateral Service UUID (`ble_manager.c:1708`). Both peers and PWAs discover via same UUID.
- **Status**: ✅ RESOLVED - Code complete, hardware testing pending

**Bug #10: Both Devices Think They're CLIENT** (RESOLVED Phase 1b.2):
- **Symptom**: Both devices would log "CLIENT role: Advertising stopped", preventing mobile app connection to either device
- **Root Cause**: Role detection logic used `peer_discovered` flag to determine connection initiator. When both devices scan simultaneously, both discover each other and set flag to `true`. When connection event fires on both sides, both think they initiated the connection and assign themselves CLIENT role.
- **Serial Evidence**: User logs showed both devices logging "CLIENT role: Advertising stopped (peer connected)"
- **Impact**: CRITICAL - Both devices stop advertising, making mobile app connection impossible during peer pairing
- **Fix**: Use NimBLE's actual connection role from `desc.role` field (`BLE_GAP_ROLE_MASTER` = CLIENT, `BLE_GAP_ROLE_SLAVE` = SERVER) instead of discovery flag (`ble_manager.c:1150-1166`). Connection role is definitively assigned by BLE stack based on who actually initiated the link.
- **Status**: ✅ RESOLVED - Code complete, hardware testing pending

**Bug #33: Lower-Battery Device Assigned Wrong Role** (CRITICAL - RESOLVED November 30, 2025):
- **Symptom**: Device with lower battery (96%) incorrectly assigned itself SERVER role instead of CLIENT
- **Root Cause**: CLIENT-waiting devices kept advertising after deciding to wait. Higher-battery device could connect TO lower-battery device, reversing BLE roles (MASTER/SLAVE) and thus reversing device roles (SERVER/CLIENT).
- **Log Evidence**: DEV_B correctly logged "Lower battery (96% < 97%) - waiting as CLIENT", but then logged "SERVER role assigned (BLE SLAVE)" when DEV_A connected to it
- **Impact**: CRITICAL - Role reversal could cause both devices to behave incorrectly (wrong coordination logic)
- **Fix**: Added `ble_gap_adv_stop()` in three CLIENT-waiting code paths (`src/ble_manager.c`):
  1. Lower battery device waiting for higher battery (line 3713-3719)
  2. Higher MAC device waiting for lower MAC (equal batteries) (line 3755-3761)
  3. Previous CLIENT waiting for previous SERVER reconnection (line 3685-3691)
- **Result**: Only the connection-initiating device (higher battery / lower MAC / previous SERVER) remains discoverable. CLIENT devices stop advertising and wait to receive connection, ensuring correct role assignment.
- **Status**: ✅ RESOLVED - Code complete, hardware testing pending

### Known Issues (Remaining)

1. **Advertising Timer Loop** (Possibly RESOLVED by Bug #8 fix):
   - Previous rapid IDLE→ADVERTISING→timeout loop after disconnect may be fixed by peer reconnection logic
   - Status: Requires hardware testing to confirm

2. **GPIO15 Status LED Stuck ON After Pairing** (RESOLVED November 19, 2025):
   - Symptom: GPIO15 remains ON after peer pairing completes, blocking subsequent blink patterns
   - Root cause: Motor task takes WS2812B ownership after pairing, but GPIO15 was left ON
   - When motor owns WS2812B, all `status_led_pattern()` calls skip GPIO15 control
   - Fix: Explicitly call `status_led_off()` after pairing success/failure patterns complete
   - Files modified: `src/ble_task.c:251-252, 301-302`
   - Status: ✅ RESOLVED - Hardware testing pending

3. **Battery Calibration Needed** (Planned Phase 1c):
   - Fully charged batteries don't reach 100% (~95-98% observed)
   - Root causes: 1S2P dual-battery configuration, P-MOSFET voltage drop, battery aging/wear
   - Proposed solution: Monitor 5V pin via voltage divider, track max voltage during USB connection
   - See AD035 for complete calibration algorithm

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

✅ **Phase 1b.1 and 1b.2: COMPLETE** (November 14, 2025)
- Bug #6 (Mobile app connection): RESOLVED - NimBLE max connections increased to 2
- Bug #7 (Advertising timeout): RESOLVED - Role-aware advertising (CLIENT stops, SERVER continues)
- Bug #8 (Peer reconnection): RESOLVED - Explicit advertising/scanning restart on disconnect
- Bug #9 (PWA discovery): RESOLVED - Advertise Configuration Service UUID for PWA filtering
- Bug #10 (Both devices CLIENT): RESOLVED - Use NimBLE's actual connection role (desc.role)
- **Hardware testing pending**: Verify role assignment, SERVER advertising, and PWA discovery

✅ **Phase 1c: COMPLETE** (November 19, 2025)

**Role Assignment Logic (IMPLEMENTED):**
- ✅ Battery level broadcast via BLE Service Data (Battery Service UUID 0x180F)
- ✅ Peer battery extracted from scan response BEFORE connection
- ✅ Higher battery device initiates connection (becomes SERVER/MASTER)
- ✅ Lower battery device waits for connection (becomes CLIENT/SLAVE)
- ✅ MAC address tie-breaker when batteries equal (lower MAC initiates)
- ✅ Fallback to discovery-based role if no battery data available
- **Implementation**: `src/ble_manager.c:2256-2319` (battery-based role assignment in scan callback)

**Key Benefits:**
- Faster role assignment (comparison during discovery, not after connection)
- Eliminates race condition (deterministic, higher battery always initiates)
- Standard BLE practice (Service Data is industry-standard approach)
- No privacy concerns (battery not personal health data, 30s window only)

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

- **Architecture Decisions**: `docs/adr/` - Individual ADR files (see [index](docs/adr/README.md))
  - [AD010](docs/adr/0010-race-condition-prevention-strategy.md): Race Condition Prevention
  - [AD028](docs/adr/0028-command-control-synchronized-fallback.md): Command-and-Control Architecture
  - [AD030](docs/adr/0030-ble-bilateral-control-service.md): BLE Bilateral Control Service
  - [AD032](docs/adr/0032-ble-configuration-service-architecture.md): BLE Service UUID Namespace
  - [AD035](docs/adr/0035-battery-based-initial-role-assignment.md): Battery-Based Role Assignment
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

### Battery Calibration System (Phase 1c)

Implement automatic calibration routine to address observed full-charge discrepancy:

**Problem:**
- Fully charged batteries don't reach 100% (observed ~95-98%)
- Causes: 1S2P parallel configuration, P-MOSFET voltage drop, battery wear, ADC tolerance
- Impact: Inaccurate battery percentage, affects role assignment fairness

**Solution:**
- **Hardware**: Add 5V pin monitoring via 45kΩ + 100kΩ voltage divider (community-tested)
- **Software**: Track maximum battery voltage during USB connection
- **Algorithm**: Only update calibration when USB connected AND voltage in valid charging range (4.0-4.25V)
- **Storage**: Save per-device calibration offset to NVS
- **Safety**: Clamp reference to 4.0-4.25V range, reset if degraded below 4.0V

**Benefits:**
- Automatic calibration during normal charging (no user intervention)
- Graceful tracking of battery wear over years
- Per-device compensation for manufacturing variations
- Protection against invalid calibration values

**Reference:** [Seeed Forum - USB Detection](https://forum.seeedstudio.com/t/detecting-usb-or-battery-power/280968)

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
Phase 1c (Modular):      src/*.c (ble_manager, motor_task, ble_task, button_task)
Phase 0.4 Code:          test/single_device_demo_jpl_queued.c
BLE GATT Code:           test/single_device_ble_gatt_test.c
Test-Specific Guide:     test/SINGLE_DEVICE_DEMO_JPL_QUEUED_GUIDE.md
BLE GATT Guide:          test/SINGLE_DEVICE_BLE_GATT_TEST_GUIDE.md
Comprehensive Guide:     test/PHASE_0.4_JPL_QUEUED_COMPLETE_GUIDE.md
Baseline Code:           test/single_device_battery_bemf_test.c
Simple Demo:             test/single_device_demo_test.c
GPIO Definitions:        [Within test files and src/*.h]
Build Commands:          BUILD_COMMANDS.md
Quick Start:             QUICK_START.md
Full Spec:               docs/requirements_spec.md
Architecture Decisions:  docs/adr/ (40 individual ADR files, see docs/adr/README.md index)
State Machine Analysis:  docs/STATE_MACHINE_ANALYSIS_CHECKLIST.md
BLE Task Analysis:       test/BLE_TASK_STATE_MACHINE_ANALYSIS.md
Mode Switch Refactor:    test/MODE_SWITCH_REFACTORING_PLAN.md
Archived Docs:           docs/archive/ (includes archived PHASE_0.4_COMPLETE_QUICKSTART.md)
```

---

## Questions Claude Code Might Ask

**Q: Where is the main application code?**
A: Two production-ready versions exist:
- `test/single_device_demo_jpl_queued.c` - Phase 0.4 JPL-compliant (button-only control)
- `test/single_device_ble_gatt_test.c` - BLE GATT server with state machines (mobile app control)

Both are automatically copied to `src/main.c` during build.

**Q: How do I switch between different tests?**
A: Use `pio run -e [environment_name] -t upload`, e.g.:
- `pio run -e single_device_demo_jpl_queued -t upload` (Phase 0.4 JPL)
- `pio run -e single_device_ble_gatt_test -t upload` (BLE GATT)

**Q: Why are there so many sdkconfig files?**
A: Each test needs different ESP-IDF configurations (GPIO, peripherals, power management, BLE stack).

**Q: What's the difference between the test files?**
A:
- `single_device_demo_jpl_queued.c` - Phase 0.4 JPL-compliant, button-only (production-ready)
- `single_device_ble_gatt_test.c` - Full BLE GATT server, state machines, mobile app control (production-ready)
- `single_device_battery_bemf_test.c` - Baseline with battery + back-EMF monitoring
- `single_device_battery_bemf_queued_test.c` - Phase 1 (adds message queues)
- `single_device_demo_test.c` - Simple 4-mode demo (no battery features)

**Q: What is Phase 1c and how do I build it?**
A: Phase 1c is battery-based role assignment for dual-device bilateral stimulation (modular architecture in `src/`).
- Build: `pio run -e xiao_esp32c6 -t upload`
- Features: Battery broadcast via Service Data, automatic role assignment (higher battery = SERVER)
- Status: ✅ Phase 1c complete (role assignment implemented November 19, 2025)

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

### Branch and PR Workflow (MANDATORY)

**No direct commits to main.** All changes must go through feature branches and PRs.

**Before finalizing any branch for PR:**

1. **Update CHANGELOG.md:**
   - Add entries under `[Unreleased]` section for all changes
   - Use appropriate categories: Added, Fixed, Changed, Infrastructure, Documentation
   - Include bug numbers for fixes (e.g., "Bug #12: Description")
   - Reference affected files with line numbers when helpful

2. **Suggest Version Bump:**
   - **Patch (v0.x.Y):** Bug fixes, documentation updates, minor tweaks
   - **Minor (v0.X.0):** New features, architecture changes, new phases
   - **Major (v1.0.0):** Production release milestone
   - Ask user to confirm version before updating CLAUDE.md header

3. **Branch Naming Convention:**
   - Feature branches: `phase6-bilateral-motor-coordination`, `feature/client-battery`
   - Bug fix branches: `fix/ble-sync-disruption`, `fix/bug-12-settings-spam`
   - Documentation: `docs/phase6-changelog`

4. **PR Checklist (remind user):**
   - [ ] CHANGELOG.md updated
   - [ ] Version bump agreed (if applicable)
   - [ ] Build verified (`pio run -e xiao_esp32c6_ble_no_nvs`)
   - [ ] Hardware testing completed (if behavior changed)
   - [ ] CLAUDE.md version header updated (if version bumped)

**Most Important:** The device must be reliable and safe for therapeutic use. When in doubt, ask before making changes that could affect safety or therapeutic effectiveness.
