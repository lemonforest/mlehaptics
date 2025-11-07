# Minimal BLE Test Guide

**File:** `test/minimal_ble_test.c`
**Environment:** `minimal_ble_test`
**Purpose:** Diagnostic test for BLE functionality with RSSI scanning

## Overview

This test validates BLE radio functionality using the official ESP-IDF bleprph example code. It serves as both a diagnostic tool and a reference implementation for correct NimBLE initialization.

### What It Does

1. **Advertises** as "ESP32C6_BLE_TEST" (discoverable by BLE scanner apps)
2. **Scans** for nearby BLE devices every 15 seconds
3. **Displays** device addresses, RSSI (signal strength), and names
4. **Validates** 2.4GHz radio hardware is functional

### Why This Test Exists

During BLE integration, we discovered a critical bug where BLE-enabled firmware produced ZERO serial output - the device appeared completely bricked. This test was created to:

- Isolate BLE initialization from other project code
- Use proven official ESP-IDF example code
- Provide RF performance testing via RSSI scanning
- Serve as a reference for correct NimBLE initialization

## Build and Upload

```bash
# Build and upload
pio run -e minimal_ble_test -t upload && pio device monitor

# Or using shell alias (if configured)
pio-bletest
```

## Expected Output

```
=== MINIMAL BLE TEST FOR ESP32-C6 ===
Based on official ESP-IDF bleprph example
Key difference: NO manual BT controller init

BLE_TEST: Step 1: Initializing NVS...
BLE_TEST: ✓ NVS initialized
BLE_TEST: Step 2: Initializing NimBLE port...
BLE_TEST: ✓ NimBLE port initialized
BLE_TEST: Step 3: Configuring NimBLE host...
BLE_TEST: ✓ NimBLE host configured
BLE_TEST: Step 4: Setting device name...
BLE_TEST: ✓ Device name set to 'ESP32C6_BLE_TEST'
BLE_TEST: Step 5: Starting NimBLE host task...
BLE_TEST: ✓ NimBLE host task started

=== BLE INITIALIZATION COMPLETE ===
Device should now be advertising as 'ESP32C6_BLE_TEST'
Scan for this device with a BLE scanner app

This device will scan for nearby BLE devices every 15 seconds
RSSI values indicate signal strength (higher = stronger signal)

BLE_TEST: Device Address: XX:XX:XX:XX:XX:XX
BLE_TEST: ✓ Advertising started successfully!

BLE_TEST: Starting BLE scan...
BLE_TEST: Device found: AA:BB:CC:DD:EE:FF  RSSI: -45 dBm
BLE_TEST:   Name: iPhone
BLE_TEST: Device found: 11:22:33:44:55:66  RSSI: -67 dBm
BLE_TEST:   Name: Bluetooth Speaker
BLE_TEST: Scan complete

BLE_TEST: ✓ BLE test still running...
```

### Scan Cycle

- **Scan duration:** 5 seconds
- **Scan interval:** 15 seconds (5s scan + 10s delay)
- **Filter duplicates:** Enabled (same device only shown once per scan)
- **Scan type:** Active (requests scan response for names)

## Testing BLE Scanner Apps

Use these apps to verify your device is advertising:

**iOS:**
- LightBlue® (Punch Through)
- nRF Connect (Nordic Semiconductor)

**Android:**
- nRF Connect (Nordic Semiconductor)
- BLE Scanner (Bluepixel Technologies)

**What to look for:**
- Device name: "ESP32C6_BLE_TEST"
- Service UUID: 0x180F (Battery Service)
- Connectable: Yes
- RSSI: Signal strength (typically -30 to -70 dBm at 1-5 meters)

## RSSI Testing for PCB Case

This test is useful for measuring RF attenuation through enclosures:

1. **Baseline:** Run test with bare PCB, note RSSI values
2. **With case:** Install PCB in enclosure, run test again
3. **Compare:** Calculate attenuation (baseline RSSI - case RSSI)

**Typical results:**
- Plastic case: 3-8 dB loss
- Metal case (with window): 5-15 dB loss
- Metal case (no window): 20-40 dB loss (may not work)

**Acceptable loss:** < 10 dB is good, < 15 dB is acceptable

## The Critical Fix

### Root Cause of Zero Serial Output Bug

The original BLE integration produced NO output because of double-initialization:

**WRONG (causes system freeze):**
```c
// Manual BT controller initialization
esp_bt_controller_config_t bt_cfg = BT_CONTROLLER_INIT_CONFIG_DEFAULT();
esp_bt_controller_init(&bt_cfg);          // ❌ Conflicts!
esp_bt_controller_enable(ESP_BT_MODE_BLE); // ❌ Conflicts!

// NimBLE initialization
nimble_port_init();  // This ALSO initializes the BT controller!
```

**CORRECT (this test uses):**
```c
// NimBLE handles everything
nimble_port_init();  // ✅ Does all BT controller setup internally
```

### Why This Happened

- Older ESP32 examples (pre-ESP-IDF v5.x) required manual controller init
- ESP-IDF v5.5.0 NimBLE integration handles this automatically
- Double initialization caused complete lockup before any output
- The freeze happened so early even bootloader messages didn't appear

### Key Lesson

**Never manually initialize the BT controller when using NimBLE in ESP-IDF v5.5.0+**

Let `nimble_port_init()` handle everything.

## Troubleshooting

### No Serial Output at All

**Possible causes:**
1. ❌ **Manual BT controller init present** - Check your code doesn't call `esp_bt_controller_init()`
2. ❌ **Wrong flash size in sdkconfig** - Must be 4MB for XIAO ESP32-C6
3. ❌ **Build cache issue** - Try `pio run -t clean` then rebuild

**Solution:**
```bash
# Clean and rebuild
pio run -e minimal_ble_test -t clean
pio run -e minimal_ble_test -t upload && pio device monitor
```

### BLE Advertising Works But No Scan Results

**Possible causes:**
1. No BLE devices nearby
2. Devices are not advertising (e.g., phones in non-discoverable mode)
3. Scan in progress when you're watching (wait 10-15 seconds for next cycle)

**What to try:**
- Put phone in pairing mode (Settings → Bluetooth → make discoverable)
- Turn on a Bluetooth speaker or headphones
- Wait for multiple scan cycles

### Can't Find Device with Scanner App

**Possible causes:**
1. Advertising not started (check serial output for "✓ Advertising started successfully!")
2. Too far away (BLE range is typically 10-30 meters indoors)
3. RF interference or shielding
4. BLE radio hardware issue

**What to try:**
```bash
# Verify WiFi test works (same radio hardware)
pio run -e minimal_wifi_test -t upload && pio device monitor
```

If WiFi works but BLE doesn't, suspect NimBLE configuration issue.

### Build Errors

**Error:** `undefined reference to esp_bt_controller_init`

**Cause:** Missing `bt` component in CMakeLists.txt REQUIRES

**Solution:** Should not happen with this test - check you're building the correct environment

**Error:** `Failed to init nimble`

**Cause:** Usually NVS flash issue

**Solution:**
```bash
# Erase flash and retry
pio run -e minimal_ble_test -t erase
pio run -e minimal_ble_test -t upload && pio device monitor
```

## Code Structure

### Key Functions

**`app_main()`**
- Initializes NVS flash
- Calls `nimble_port_init()` (no manual BT controller init!)
- Configures NimBLE callbacks
- Starts NimBLE host task
- Main loop triggers periodic scans

**`bleprph_advertise()`**
- Sets up advertisement data (name, flags, TX power)
- Starts connectable, discoverable advertising
- Called automatically when host syncs

**`ble_scan_start()`**
- Configures scan parameters (5-second active scan)
- Starts scan with `ble_gap_disc()`
- Results reported to `ble_scan_event()`

**`ble_scan_event()`**
- Handles BLE_GAP_EVENT_DISC (device discovered)
- Parses advertisement data for device names
- Logs device address, RSSI, and name

### NimBLE Callbacks

**`bleprph_on_sync()`**
- Called when NimBLE stack is ready
- Gets device address
- Starts advertising
- Triggers first scan after 2-second delay

**`bleprph_on_reset()`**
- Called on stack reset (errors)
- Logs reset reason for debugging

## What This Test Proves

✅ **2.4GHz Radio Hardware:** If WiFi test passed, radio is functional
✅ **NimBLE Stack:** Correct initialization and operation
✅ **BLE Advertising:** Device is discoverable by scanners
✅ **BLE Scanning:** Can discover other devices
✅ **RF Performance:** RSSI values indicate signal quality
✅ **Configuration:** sdkconfig is correct for BLE operation

## Related Tests

- **minimal_wifi_test** - Tests same 2.4GHz radio hardware
- **single_device_ble_gatt_test** - Full GATT server with motor control

## References

- **ESP-IDF bleprph example:** `esp-idf/examples/bluetooth/nimble/bleprph/`
- **NimBLE documentation:** https://mynewt.apache.org/latest/network/
- **BLE_DIAGNOSTIC_STRATEGY.md:** Full diagnostic investigation timeline
- **CLAUDE.md:** Recent Analysis & Fixes section for BLE fix details

## Version History

- **November 5, 2025:** Created for BLE diagnostic investigation
- **November 5, 2025:** Fixed double-initialization bug
- **November 5, 2025:** Added RSSI scanning for RF performance testing
