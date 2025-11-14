# Quick Build & Test Reference

**Version:** v0.1.2
**Last Updated:** 2025-11-14
**Status:** Production-Ready

---

## Available Build Environments

### Main Application Environments

| Environment | Purpose | Command |
|-------------|---------|---------|
| `xiao_esp32c6` | Development build (default) | `pio run -t upload && pio device monitor` |
| `xiao_esp32c6_production` | Production release | `pio run -e xiao_esp32c6_production -t upload` |
| `xiao_esp32c6_testing` | Unit testing | `pio test -e xiao_esp32c6_testing` |

### Hardware Test Environments

| Test | Purpose | Command |
|------|---------|---------|
| `ledc_blink_test` | Minimal LEDC test (blink LED at 1Hz) | `pio run -e ledc_blink_test -t upload && pio device monitor` |
| `hbridge_test` | H-bridge GPIO control test (100% power) | `pio run -e hbridge_test -t upload && pio device monitor` |
| `hbridge_pwm_test` | H-bridge PWM control @ 60% duty ✅ WORKING | `pio run -e hbridge_pwm_test -t upload && pio device monitor` |
| `button_deepsleep_test` | Button toggle, 5s hold → deep sleep, wake test | `pio run -e button_deepsleep_test -t upload && pio device monitor` |
| `ws2812b_test` | WS2812B color cycling (Red→Green→Blue→Rainbow) + deep sleep | `pio run -e ws2812b_test -t upload && pio device monitor` |
| `single_device_demo_test` | 20-min research study: 4 modes testing duty cycle effects (0.5-1Hz @ 25-50%) | `pio run -e single_device_demo_test -t upload && pio device monitor` |
| `battery_voltage_test` | Battery monitoring with LVO protection (3.2V threshold), 20-min session limit | `pio run -e battery_voltage_test -t upload && pio device monitor` |
| `single_device_battery_bemf_test` | Integrated test: 4-mode motor + battery + back-EMF characterization | `pio run -e single_device_battery_bemf_test -t upload && pio device monitor` |
| `single_device_demo_jpl_queued` | **JPL-compliant** FreeRTOS architecture: Task isolation, message queues, proper watchdog feeding, 4-mode motor control | `pio run -e single_device_demo_jpl_queued -t upload && pio device monitor` |
| `single_device_ble_gatt_test` | **NEW!** Phase A BLE GATT server: Mobile app config, 5-mode operation, NVS persistence | `pio run -e single_device_ble_gatt_test -t upload && pio device monitor` |

### Diagnostic Test Environments

| Test | Purpose | Command |
|------|---------|---------|
| `minimal_ble_test` | **BLE Diagnostic** - NimBLE advertising + scanning with RSSI for RF testing | `pio run -e minimal_ble_test -t upload && pio device monitor` |
| `minimal_wifi_test` | **WiFi Diagnostic** - 2.4GHz radio hardware validation (same radio as BLE) | `pio run -e minimal_wifi_test -t upload && pio device monitor` |

---

## Common Commands

### Building
```bash
# Build default environment (xiao_esp32c6)
pio run

# Build specific environment
pio run -e hbridge_test

# Clean build (force rebuild)
pio run -t clean
pio run
```

### Uploading & Monitoring
```bash
# Upload and start serial monitor (default env)
pio run -t upload && pio device monitor

# Upload specific test
pio run -e hbridge_test -t upload

# Just monitor (no upload)
pio device monitor

# Monitor with custom baud rate
pio device monitor -b 115200
```

### Serial Monitor Controls
- `Ctrl+C` - Exit monitor
- `Ctrl+T` followed by `Ctrl+D` - Toggle DTR
- `Ctrl+T` followed by `Ctrl+R` - Toggle RTS

### Cleaning
```bash
# Clean build artifacts
pio run -t clean

# Full clean (including downloaded packages)
pio run -t fullclean

# Clean specific environment
pio run -e hbridge_test -t clean
```

**Windows PowerShell:**
```powershell
# Remove specific build folder
Remove-Item -Recurse -Force .pio\build\hbridge_test

# Remove all build artifacts
Remove-Item -Recurse -Force .pio\build
```

**Windows Command Prompt:**
```cmd
# Remove specific build folder
rmdir /s /q .pio\build\hbridge_test

# Remove all build artifacts
rmdir /s /q .pio\build
```

### Project Information
```bash
# List all environments
pio project config

# Show device information
pio device list

# Check PlatformIO version
pio --version
```

---

## Quick Start - Hardware Testing

### First Time Setup
```bash
# 1. Let PlatformIO download ESP-IDF (first build only, takes 5-10 minutes)
pio run

# 2. Connect your board via USB

# 3. Run H-bridge test
pio run -e hbridge_test -t upload && pio device monitor
```

### After Making Changes
```bash
# Quick rebuild and test
pio run -e hbridge_test -t upload && pio device monitor

# Or if you prefer separate steps
pio run -e hbridge_test -t upload
pio device monitor
```

### Test Button and Deep Sleep
```bash
# Button toggle, 5-second hold deep sleep test
pio run -e button_deepsleep_test -t upload && pio device monitor

# WS2812B LED color cycling test
pio run -e ws2812b_test -t upload && pio device monitor

# Test sequence:
# 1. LED should be ON after power-up
# 2. Press button: Toggle LED
# 3. Hold button 5 seconds: Countdown + deep sleep
# 4. Press button while sleeping: Wake up, LED ON
```

### Research and Demo Tests
```bash
# Single device demo test (20-minute research study)
pio run -e single_device_demo_test -t upload && pio device monitor

# Battery voltage monitoring test
pio run -e battery_voltage_test -t upload && pio device monitor
```

### Switch Back to Main Application
```bash
pio run -t upload && pio device monitor
```

---

## Troubleshooting

### Port Issues (Windows)
```bash
# List available COM ports
pio device list

# Manually specify port in platformio.ini:
# upload_port = COM3
# monitor_port = COM3
```

### Port Issues (Linux/Mac)
```bash
# List available ports
ls /dev/tty*

# Give permissions (Linux)
sudo usermod -a -G dialout $USER
# Then log out and back in

# Manually specify port in platformio.ini:
# upload_port = /dev/ttyACM0
# monitor_port = /dev/ttyACM0
```

### Build Errors
```bash
# Clean and rebuild
pio run -t clean
pio run
```

**If ESP-IDF download failed, delete and retry:**

*Linux/Mac:*
```bash
rm -rf ~/.platformio/packages/framework-espidf
pio run
```

*Windows PowerShell:*
```powershell
Remove-Item -Recurse -Force $env:USERPROFILE\.platformio\packages\framework-espidf
pio run
```

*Windows Command Prompt:*
```cmd
rmdir /s /q %USERPROFILE%\.platformio\packages\framework-espidf
pio run
```

### Upload Fails
```bash
# Try holding BOOT button during upload
# Or reset board and immediately run:
pio run -t upload

# Reduce upload speed (in platformio.ini):
# upload_speed = 460800
```

---

## Build Flags Reference

### Development Flags (enabled by default)
- `TESTING_MODE=1` - Enable test features
- `ENABLE_FACTORY_RESET=1` - Allow factory reset
- `DEBUG_LEVEL=3` - Verbose logging

### Hardware Test Flags
- `HARDWARE_TEST=1` - Indicates hardware test mode
- `DEBUG_LEVEL=3` - Verbose test logging

### Production Flags
- `TESTING_MODE=0` - Disable test features
- `ENABLE_FACTORY_RESET=0` - Disable factory reset
- `DEBUG_LEVEL=0` - Minimal logging

---

## Windows-Specific Notes

### Finding Your COM Port
1. Open Device Manager
2. Expand "Ports (COM & LPT)"
3. Look for "USB Serial Device" or "USB-SERIAL CH340"
4. Note the COM number (e.g., COM3)

### Common Issues
- **Driver not found:** Install CH340 USB driver
- **Access denied:** Close Arduino IDE or other serial monitors
- **Port disappeared:** Try different USB cable or port

---

## Tips & Best Practices

### Efficient Development Workflow
```bash
# Keep monitor running in one terminal
pio device monitor

# Build and upload in another terminal
pio run -e hbridge_test -t upload
```

### Quick Test Cycle

**Linux/Mac (bash/zsh):**
```bash
# Create aliases for quick testing (add to .bashrc or .zshrc)
alias pio-htest='pio run -e hbridge_test -t upload && pio device monitor'
alias pio-btntest='pio run -e button_deepsleep_test -t upload && pio device monitor'
alias pio-ledtest='pio run -e ledc_blink_test -t upload && pio device monitor'
alias pio-ws2812b='pio run -e ws2812b_test -t upload && pio device monitor'
alias pio-demo='pio run -e single_device_demo_test -t upload && pio device monitor'
alias pio-battery='pio run -e battery_voltage_test -t upload && pio device monitor'
alias pio-bemf='pio run -e single_device_battery_bemf_test -t upload && pio device monitor'
alias pio-jplqueue='pio run -e single_device_demo_jpl_queued -t upload && pio device monitor'
alias pio-ble='pio run -e single_device_ble_gatt_test -t upload && pio device monitor'
alias pio-bletest='pio run -e minimal_ble_test -t upload && pio device monitor'
alias pio-wifitest='pio run -e minimal_wifi_test -t upload && pio device monitor'

# Then just run:
pio-htest      # H-bridge test
pio-btntest    # Button and deep sleep test
pio-ledtest    # LED blink test
pio-ws2812b    # WS2812B color cycling test
pio-demo       # Single device demo (research modes)
pio-battery    # Battery voltage monitoring test
pio-bemf       # Integrated battery + back-EMF + motor test
pio-jplqueue   # JPL-compliant FreeRTOS architecture test
pio-ble        # BLE GATT server test (Phase A)
pio-bletest    # BLE diagnostic with RSSI scanning
pio-wifitest   # WiFi diagnostic test
```

**Windows PowerShell:**
```powershell
# Create functions in your PowerShell profile
# Edit profile: notepad $PROFILE
function pio-htest {
    pio run -e hbridge_test -t upload
    if ($LASTEXITCODE -eq 0) { pio device monitor }
}

function pio-btntest {
    pio run -e button_deepsleep_test -t upload
    if ($LASTEXITCODE -eq 0) { pio device monitor }
}

function pio-ledtest {
    pio run -e ledc_blink_test -t upload
    if ($LASTEXITCODE -eq 0) { pio device monitor }
}

function pio-ws2812b {
    pio run -e ws2812b_test -t upload
    if ($LASTEXITCODE -eq 0) { pio device monitor }
}

function pio-demo {
    pio run -e single_device_demo_test -t upload
    if ($LASTEXITCODE -eq 0) { pio device monitor }
}

function pio-battery {
    pio run -e battery_voltage_test -t upload
    if ($LASTEXITCODE -eq 0) { pio device monitor }
}

function pio-bemf {
    pio run -e single_device_battery_bemf_test -t upload
    if ($LASTEXITCODE -eq 0) { pio device monitor }
}

function pio-jplqueue {
    pio run -e single_device_demo_jpl_queued -t upload
    if ($LASTEXITCODE -eq 0) { pio device monitor }
}

function pio-ble {
    pio run -e single_device_ble_gatt_test -t upload
    if ($LASTEXITCODE -eq 0) { pio device monitor }
}

function pio-bletest {
    pio run -e minimal_ble_test -t upload
    if ($LASTEXITCODE -eq 0) { pio device monitor }
}

function pio-wifitest {
    pio run -e minimal_wifi_test -t upload
    if ($LASTEXITCODE -eq 0) { pio device monitor }
}

# Then just run:
pio-htest      # H-bridge test
pio-btntest    # Button and deep sleep test
pio-ledtest    # LED blink test
pio-ws2812b    # WS2812B color cycling test
pio-demo       # Single device demo (research modes)
pio-battery    # Battery voltage monitoring test
pio-bemf       # Integrated battery + back-EMF + motor test
pio-jplqueue   # JPL-compliant FreeRTOS architecture test
pio-ble        # BLE GATT server test (Phase A)
pio-bletest    # BLE diagnostic with RSSI scanning
pio-wifitest   # WiFi diagnostic test
```

**Windows Command Prompt:**
```cmd
# Create batch files in a directory in your PATH:

# pio-htest.bat
@echo off
pio run -e hbridge_test -t upload
if %errorlevel% equ 0 pio device monitor

# pio-btntest.bat
@echo off
pio run -e button_deepsleep_test -t upload
if %errorlevel% equ 0 pio device monitor

# pio-ledtest.bat
@echo off
pio run -e ledc_blink_test -t upload
if %errorlevel% equ 0 pio device monitor

# pio-ws2812b.bat
@echo off
pio run -e ws2812b_test -t upload
if %errorlevel% equ 0 pio device monitor

# pio-demo.bat
@echo off
pio run -e single_device_demo_test -t upload
if %errorlevel% equ 0 pio device monitor

# pio-battery.bat
@echo off
pio run -e battery_voltage_test -t upload
if %errorlevel% equ 0 pio device monitor

# pio-bemf.bat
@echo off
pio run -e single_device_battery_bemf_test -t upload
if %errorlevel% equ 0 pio device monitor

# pio-jplqueue.bat
@echo off
pio run -e single_device_demo_jpl_queued -t upload
if %errorlevel% equ 0 pio device monitor

# pio-ble.bat
@echo off
pio run -e single_device_ble_gatt_test -t upload
if %errorlevel% equ 0 pio device monitor

# pio-bletest.bat
@echo off
pio run -e minimal_ble_test -t upload
if %errorlevel% equ 0 pio device monitor

# pio-wifitest.bat
@echo off
pio run -e minimal_wifi_test -t upload
if %errorlevel% equ 0 pio device monitor

# Then just run:
pio-htest      REM H-bridge test
pio-btntest    REM Button and deep sleep test
pio-ledtest    REM LED blink test
pio-ws2812b    REM WS2812B color cycling test
pio-demo       REM Single device demo (research modes)
pio-battery    REM Battery voltage monitoring test
pio-bemf       REM Integrated battery + back-EMF + motor test
pio-jplqueue   REM JPL-compliant FreeRTOS architecture test
pio-ble        REM BLE GATT server test (Phase A)
pio-bletest    REM BLE diagnostic with RSSI scanning
pio-wifitest   REM WiFi diagnostic test
```

### Save Build Output
```bash
# Log build output to file
pio run 2>&1 | tee build_output.log

# Log monitor output
pio device monitor | tee test_results.log
```

---

## Adding New Test Environments

**Checklist for adding new hardware tests:**

1. **Create test file:** `test/my_new_test.c`
2. **Add to source map:** Edit `scripts/select_source.py`
   ```python
   "my_new_test": "../test/my_new_test.c",
   ```
3. **Add environment:** Edit `platformio.ini`
   ```ini
   [env:my_new_test]
   extends = env:xiao_esp32c6
   build_flags = 
       ${env:xiao_esp32c6.build_flags}
       -DHARDWARE_TEST=1
       -DDEBUG_LEVEL=3
   ```
4. **Update this file:** Add to Hardware Test Environments table above
5. **Test build:** `pio run -e my_new_test -t upload && pio device monitor`

This ensures consistency across all project documentation!
