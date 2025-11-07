# BLE Diagnostic Strategy for ESP32-C6

## Problem Statement

When BLE is enabled (NimBLE stack), the ESP32-C6 shows **ZERO serial output** after firmware upload:
- No bootloader messages
- No app_main() logs
- Complete device silence

Device works perfectly **without BLE** (motor control, battery monitoring, LEDs all functional).

## Hypothesis

Either:
1. **Software Bug** - NimBLE in ESP-IDF v5.5.0 has an initialization bug causing crash before app_main()
2. **Hardware Damage** - BLE radio damaged during board assembly

## Diagnostic Tests

### Test 1: WiFi Radio Test (PRIORITY)
**File:** `test/minimal_wifi_test.c`
**Environment:** `minimal_wifi_test`
**Purpose:** Verify 2.4GHz radio hardware is functional
**Rationale:** WiFi and BLE use the same 2.4GHz radio hardware on ESP32-C6

**Expected Outcomes:**
- ✅ **WiFi works** → Radio hardware is fine, BLE issue is software-related
- ❌ **WiFi fails** → Possible radio hardware damage

**Command:**
```bash
pio run -e minimal_wifi_test -t upload --upload-port COM3 && pio device monitor --port COM3
```

### Test 2: BLE with Official ESP-IDF Example
**File:** `test/minimal_ble_test.c`
**Environment:** `minimal_ble_test`
**Purpose:** Test BLE using official ESP-IDF bleprph example code
**Rationale:** Use proven working code from ESP-IDF to isolate custom code issues

**Command:**
```bash
pio run -e minimal_ble_test -t upload && pio device monitor
```

### Test 3: Spare Board Test (If Needed)
**Hardware:** Unused XIAO ESP32-C6 board (still in package)
**Purpose:** Eliminate board-specific issues
**When:** Only if Tests 1 & 2 suggest hardware damage

## Technical Details

### Created Files

**test/minimal_wifi_test.c** - Absolute minimum WiFi test
- Initialize WiFi
- Scan for networks
- Print results every 10 seconds
- No other peripherals (no GPIO, motors, sensors)

**test/minimal_ble_test.c** - Absolute minimum BLE test
- Initialize NimBLE
- Start advertising as "ESP32C6_TEST"
- Log every 10 seconds
- No other peripherals

**platformio.ini** - Added environments:
```ini
[env:minimal_wifi_test]
extends = env:xiao_esp32c6
# WiFi-only test with ESP-IDF v5.5.0

[env:minimal_ble_test]
extends = env:xiao_esp32c6
# BLE test using official ESP-IDF bleprph example
```

**sdkconfig files:**
- `sdkconfig.minimal_wifi_test` - BLE disabled, WiFi enabled
- `sdkconfig.minimal_ble_test` - BLE enabled (NimBLE)

### Key Insights

1. **Both tests use minimal code** - No GPIO, motors, sensors, battery monitoring
2. **Isolates the variable** - WiFi test proves radio works, BLE test proves software stack
3. **Official example code** - Using proven ESP-IDF bleprph example to eliminate custom code issues
4. **Hardware verification** - Spare board available for comparison if needed

## Next Steps Based on Results

### Scenario A: WiFi works + BLE works with official example
**Conclusion:** Custom BLE initialization code has a bug
**Action:** Compare custom code with working example to identify the issue

### Scenario B: WiFi works + BLE fails with official example
**Conclusion:** Configuration or hardware issue
**Action:** Test on spare board, verify sdkconfig settings

### Scenario C: WiFi fails
**Conclusion:** Possible 2.4GHz radio hardware damage
**Action:** Test on spare board to confirm hardware issue

### Scenario D: Everything works
**Conclusion:** Original issue was configuration-related
**Action:** Integrate working BLE pattern into main application

## Timeline

- **November 5, 2025 13:00** - Created diagnostic tests
- **November 5, 2025 14:30** - ✅ **WiFi test SUCCESS on both boards!**
  - Tested on spare XIAO ESP32-C6 (bare board) - WiFi works perfectly
  - Tested on assembled project PCB - WiFi works perfectly
  - **Conclusion:** 2.4GHz radio hardware is fully functional
- **November 5, 2025 15:00** - Fixed led_strip dependency issue for ESP-IDF v5.3 test
- **November 5, 2025 15:30** - Building minimal BLE test with ESP-IDF v5.3...
- **November 5, 2025 15:45** - 🎯 **FOUND ROOT CAUSE: Flash Size Mismatch!**
  - Device crash error: `Detected size(4096k) smaller than the size in the binary image header(8192k)`
  - **Problem:** sdkconfig files configured for 2MB flash, hardware has 4MB
  - **Fix:** Updated all BLE/WiFi sdkconfig files: `CONFIG_ESPTOOLPY_FLASHSIZE="4MB"`
  - **Impact:** This was causing crash BEFORE any code ran - not a BLE issue at all!
  - Rebuilding with correct flash size...
- **November 5, 2025 17:40** - ⚠️ **Build System Issue: Wrong Source File**
  - Build system compiled minimal_wifi_test.c instead of minimal_ble_test.c for BLE test
  - CMake cache issue - stale configuration from previous builds
  - **Root Cause:** select_source.py updates src/CMakeLists.txt, but CMake caches build configuration
  - **Solution:** Need to clean build directory before switching between test environments
- **November 5, 2025 18:00** - 🎯 **BREAKTHROUGH: Found the ACTUAL Root Cause!**
  - Used official ESP-IDF bleprph example code
  - Still got ZERO serial output with our custom initialization
  - **ROOT CAUSE IDENTIFIED:** Manual `esp_bt_controller_init()` + `esp_bt_controller_enable()` conflicted with NimBLE
  - `nimble_port_init()` ALREADY initializes the BT controller internally!
  - Double initialization caused complete system freeze before any output
- **November 5, 2025 18:15** - ✅ **BLE NOW WORKING!**
  - Removed manual BT controller init from minimal_ble_test.c
  - Device boots, serial output works perfectly
  - Advertising successfully, scannable by BLE scanner apps
  - **CONCLUSION:** Never manually initialize BT controller when using NimBLE

## Resolution and Working Solution

### Root Cause
The BLE initialization bug was caused by **double-initialization of the BT controller**:

**WRONG (causes zero serial output):**
```c
// Manual BT controller initialization
esp_bt_controller_config_t bt_cfg = BT_CONTROLLER_INIT_CONFIG_DEFAULT();
esp_bt_controller_init(&bt_cfg);          // ❌ Conflicts with NimBLE
esp_bt_controller_enable(ESP_BT_MODE_BLE); // ❌ Conflicts with NimBLE

// NimBLE initialization
nimble_port_init();  // This ALSO initializes the BT controller!
```

**CORRECT (works perfectly):**
```c
// NimBLE handles BT controller internally
nimble_port_init();  // ✅ Does everything needed
```

### Why This Happened
- Custom code followed older ESP32 BLE examples that manually initialized the controller
- NimBLE integration was updated in newer ESP-IDF versions to handle this automatically
- Double initialization caused complete system lockup before serial output could start
- This explains why there was NO output at all - the freeze happened during boot

### Key Lessons Learned
1. **Always use official examples** - ESP-IDF bleprph example worked immediately once controller init was removed
2. **NimBLE is self-contained** - Let `nimble_port_init()` handle all initialization
3. **WiFi test was crucial** - Proved radio hardware was fine, isolated issue to software
4. **Systematic debugging works** - Methodical testing led to the answer

### Verified Working Configuration
- **ESP-IDF:** v5.5.0 (latest)
- **Board:** Seeed XIAO ESP32-C6
- **Flash Size:** 4MB (correctly configured in sdkconfig)
- **BLE Stack:** NimBLE (built into ESP-IDF)
- **Initialization:** Let `nimble_port_init()` handle everything

### Files Fixed
1. `test/minimal_ble_test.c` - Diagnostic test (now working with scanning)
2. `test/single_device_ble_gatt_test.c` - Main GATT server application

## References

- ESP32-C6 Technical Reference Manual
- ESP-IDF v5.5.0 NimBLE integration documentation
- ESP-IDF bleprph example (examples/bluetooth/nimble/bleprph)
- NimBLE documentation for ESP32-C6
- XIAO ESP32-C6 hardware specifications
