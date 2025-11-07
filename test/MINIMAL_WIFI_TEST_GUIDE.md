# Minimal WiFi Test Guide

**File:** `test/minimal_wifi_test.c`
**Environment:** `minimal_wifi_test`
**Purpose:** Diagnostic test for 2.4GHz radio hardware validation

## Overview

This test validates the ESP32-C6's 2.4GHz radio hardware by scanning for WiFi networks. Since BLE and WiFi share the same radio hardware, this test proves the radio is functional - making it a critical diagnostic tool when BLE issues occur.

### What It Does

1. **Initializes** WiFi in station mode
2. **Scans** for nearby 2.4GHz and 5GHz WiFi networks
3. **Displays** SSID, RSSI (signal strength), channel, and authentication type
4. **Repeats** scan every 10 seconds
5. **Validates** 2.4GHz radio hardware is operational

### Why This Test Exists

During BLE integration, we encountered a critical bug where BLE-enabled firmware produced zero serial output. Before assuming hardware damage, we needed to verify the 2.4GHz radio was functional. This test was created to:

- **Isolate radio hardware** from BLE software stack
- **Prove radio works** using a different protocol (WiFi vs BLE)
- **Quick validation** that radio wasn't damaged during assembly
- **Eliminate hardware** as a variable when debugging BLE issues

## Build and Upload

```bash
# Build and upload
pio run -e minimal_wifi_test -t upload && pio device monitor

# Or using shell alias (if configured)
pio-wifitest
```

## Expected Output

```
=== MINIMAL WIFI TEST FOR ESP32-C6 ===
Validates 2.4GHz radio hardware (same radio used for BLE)

WIFI_TEST: Step 1: Initializing NVS...
WIFI_TEST: ✓ NVS initialized

WIFI_TEST: Step 2: Initializing WiFi...
WIFI_TEST: ✓ WiFi initialized

WIFI_TEST: Step 3: Starting WiFi...
WIFI_TEST: ✓ WiFi started in station mode

=== WIFI INITIALIZATION COMPLETE ===
Device will scan for WiFi networks every 10 seconds
This test validates the 2.4GHz radio hardware is functional

WIFI_TEST: Starting WiFi scan...

WIFI_TEST: Found 8 WiFi networks:
WIFI_TEST:   1. SSID: HomeNetwork         | RSSI: -35 dBm | Ch: 6  | Auth: WPA2-PSK
WIFI_TEST:   2. SSID: Neighbor_5G         | RSSI: -58 dBm | Ch: 149 | Auth: WPA2-PSK
WIFI_TEST:   3. SSID: OfficeWiFi          | RSSI: -67 dBm | Ch: 11 | Auth: WPA2-PSK
WIFI_TEST:   4. SSID: Guest_Network       | RSSI: -72 dBm | Ch: 1  | Auth: Open
WIFI_TEST:   5. SSID: Apartment_201       | RSSI: -78 dBm | Ch: 6  | Auth: WPA2-PSK
WIFI_TEST:   6. SSID: Starbucks           | RSSI: -81 dBm | Ch: 11 | Auth: Open
WIFI_TEST:   7. SSID: Hidden_Network      | RSSI: -84 dBm | Ch: 3  | Auth: WPA3-PSK
WIFI_TEST:   8. SSID:                     | RSSI: -89 dBm | Ch: 9  | Auth: WPA2-PSK
WIFI_TEST: ✓ Scan complete

WIFI_TEST: ✓ WiFi test running, next scan in 10 seconds...
```

### RSSI Values

**Signal Strength Guide:**
- **-30 to -50 dBm:** Excellent (very close, strong signal)
- **-50 to -60 dBm:** Good (typical home network)
- **-60 to -70 dBm:** Fair (usable but not ideal)
- **-70 to -80 dBm:** Weak (may have connection issues)
- **-80 to -90 dBm:** Very weak (barely detectable)
- **Below -90 dBm:** Too weak to connect

### Channel Information

**2.4GHz Channels:** 1-14 (US typically uses 1-11)
**5GHz Channels:** Various (36, 40, 44, 48, 149, 153, 157, 161, 165, etc.)

Note: ESP32-C6 can scan both 2.4GHz and 5GHz networks, but only connects to 2.4GHz

## What This Test Proves

✅ **2.4GHz Radio Hardware:** If you see WiFi scan results, the radio is working
✅ **RF Frontend:** Antenna, matching network, and RF path are functional
✅ **Power Supply:** Radio is receiving sufficient power
✅ **Clock/Crystal:** 40MHz crystal is oscillating correctly
✅ **Firmware Upload:** Code is running (if you see serial output)

### Critical Finding

**If this test works:**
- Radio hardware is NOT damaged
- Any BLE issues are SOFTWARE-related, not hardware
- Focus debugging on BLE stack initialization
- Check for configuration errors in sdkconfig

**If this test fails:**
- Check antenna connection (SMD or PCB trace)
- Verify 3.3V power supply is stable
- Test with a spare board to confirm hardware issue
- Check for damage during assembly

## Troubleshooting

### No WiFi Networks Found

**Possible causes:**
1. No 2.4GHz networks in range (all networks are 5GHz only)
2. RF shielding (metal case with no window)
3. Antenna issue (disconnected or damaged)
4. Radio hardware damage

**What to try:**
- Move closer to a known 2.4GHz WiFi router
- Remove any metal shielding/enclosure
- Test with a spare board
- Check for visible antenna damage

### "WiFi init failed" Error

**Possible causes:**
1. NVS flash corruption
2. Insufficient free heap memory
3. Wrong sdkconfig settings

**Solution:**
```bash
# Erase flash and retry
pio run -e minimal_wifi_test -t erase
pio run -e minimal_wifi_test -t upload && pio device monitor
```

### Only Seeing 5GHz Networks

**This is expected!** ESP32-C6 can **scan** both 2.4GHz and 5GHz but only **connects** to 2.4GHz.

Seeing 5GHz networks in scan results actually **proves** the test is working correctly - it shows WiFi scan is functioning.

**Look for:**
- Channel 1-11: These are 2.4GHz networks
- Channel 36+: These are 5GHz networks

### No Serial Output at All

**Possible causes:**
1. Wrong COM port selected
2. Driver issue (CH340 driver not installed)
3. USB cable is power-only (no data)
4. Bootloader issue

**What to try:**
```bash
# List available ports
pio device list

# Try different baud rate
pio device monitor -b 115200

# Check if device is in bootloader mode
# (Should see "waiting for download" if stuck in bootloader)
```

## Code Structure

### Key Functions

**`app_main()`**
- Initializes NVS flash
- Initializes WiFi stack
- Starts WiFi in station mode
- Main loop triggers scans every 10 seconds

**`wifi_scan_task()`**
- Calls `esp_wifi_scan_start()`
- Waits for scan completion
- Retrieves scan results
- Logs network information (SSID, RSSI, channel, auth)

**`wifi_event_handler()`**
- Handles WiFi events (though not used in this minimal test)
- Required by ESP-IDF WiFi initialization

### WiFi Configuration

```c
wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
wifi_config_t wifi_config = {
    .sta = {
        .scan_method = WIFI_ALL_CHANNEL_SCAN,
        .sort_method = WIFI_CONNECT_AP_BY_SIGNAL,
    },
};
```

**Scan parameters:**
- **Scan type:** Active (faster, more reliable)
- **Channels:** All (both 2.4GHz and 5GHz)
- **Duration:** Default (per-channel dwell time)
- **Show hidden:** Yes (SSIDs with broadcast disabled)

## Diagnostic Use Cases

### BLE Debugging

**Scenario:** BLE firmware produces no serial output

**Steps:**
1. Run this WiFi test first
2. **If WiFi works:** Radio hardware is fine, BLE issue is software
3. **If WiFi fails:** Suspect hardware damage, test spare board

**Result:** We discovered BLE worked perfectly after fixing double-initialization bug, proving hardware was never the issue

### PCB Assembly Verification

**Use after:** Soldering, reflow, or any assembly work

**Check for:**
- ≥3 networks with RSSI > -70 dBm (assumes typical office/home environment)
- Network count similar to known-good board
- RSSI values within 10 dB of known-good board

**If fewer/weaker networks:**
- Check antenna solder joints
- Verify RF matching components
- Test without metal case

### Antenna Performance Testing

**Baseline:** Run test with good external antenna
**Compare:** Run test with PCB antenna or different external antenna
**Measure:** Difference in RSSI for the same network

**Typical results:**
- Good external antenna: -30 to -50 dBm
- PCB trace antenna: -40 to -60 dBm (typically 5-10 dB worse)
- Damaged/poor antenna: -60 to -80 dBm or fewer networks

## Configuration

### sdkconfig Settings

```ini
# WiFi enabled, BLE disabled
CONFIG_ESP32_WIFI_ENABLED=y
CONFIG_BT_ENABLED=n

# Flash size (critical!)
CONFIG_ESPTOOLPY_FLASHSIZE="4MB"

# WiFi scan parameters
CONFIG_ESP32_WIFI_STATIC_RX_BUFFER_NUM=10
CONFIG_ESP32_WIFI_DYNAMIC_RX_BUFFER_NUM=32
```

### Why BLE is Disabled

BLE shares the same radio hardware with WiFi. They cannot operate simultaneously without coordination. For this diagnostic test, BLE is disabled to:

1. **Isolate WiFi:** Simpler, proven code path
2. **Avoid conflicts:** No radio arbitration needed
3. **Faster compilation:** Fewer components to build
4. **Clear results:** Only testing WiFi functionality

## What Happens After This Test Passes

Once WiFi test confirms radio hardware is functional:

1. **Move to BLE testing:** Run `minimal_ble_test`
2. **If BLE fails:** Focus on NimBLE initialization code
3. **Compare code:** Look for differences vs working examples
4. **Check sdkconfig:** Verify BLE settings are correct

**In our case:**
- WiFi test: ✅ Passed (radio hardware confirmed functional)
- BLE test (with bug): ❌ Failed (zero output)
- BLE test (fixed): ✅ Passed (removed double-init)

**Conclusion:** Hardware was always fine - it was a software bug

## Related Tests

- **minimal_ble_test** - Tests BLE on the same 2.4GHz radio
- **single_device_ble_gatt_test** - Full BLE GATT server application

## References

- **ESP-IDF WiFi Documentation:** https://docs.espressif.com/projects/esp-idf/en/latest/esp32c6/api-reference/network/esp_wifi.html
- **ESP32-C6 Technical Reference Manual:** Radio specifications
- **BLE_DIAGNOSTIC_STRATEGY.md:** Complete diagnostic timeline
- **CLAUDE.md:** Recent Analysis & Fixes section

## Version History

- **November 5, 2025:** Created for BLE diagnostic investigation
- **November 5, 2025:** Confirmed radio hardware functional, isolated BLE issue to software
