# platformio.ini Verification Checklist

**Project**: EMDR Bilateral Stimulation Device  
**Date**: 2025-10-20  
**Purpose**: Verify correct ESP-IDF v5.5.0 configuration

---

## ✅ ESP-IDF v5.5.0 Migration Complete

**Status:** Build verified successful on October 20, 2025

### Current Working Configuration
- **Platform**: espressif32 @ 6.12.0 (official Seeed XIAO ESP32-C6 support)
- **Framework**: ESP-IDF v5.5.0 (framework-espidf @ 3.50500.0)
- **Board**: seeed_xiao_esp32c6 (official support added in platform v6.11.0)
- **Build Time**: 610 seconds first build, ~60 seconds incremental
- **RAM Usage**: 3.1% (10,148 / 327,680 bytes)
- **Flash Usage**: 4.1% (168,667 / 4,128,768 bytes)

---

## 🧪 Verification Steps

Run these commands in your project directory to verify the configuration:

### Step 1: Verify PlatformIO Installation
```bash
cd "G:\My Drive\AI_PROJECTS\EMDR_PULSER_SONNET4"
pio --version
```

**Expected output:**
```
PlatformIO Core, version 6.1.x or later
```

**If PlatformIO needs update:**
```bash
pio upgrade
```

### Step 2: Check Package Installation
```bash
pio pkg list
```

**Look for**:
```
espressif32 @ 6.12.0
framework-espidf @ 3.50500.0
```

### Step 3: Build Project (Verbose)
```bash
pio run --verbose
```

**Critical lines to verify in output:**
```
Processing xiao_esp32c6 (platform: espressif32@6.12.0; framework: espidf)
...
PLATFORM: Espressif 32 (6.12.0) > Seeed Studio XIAO ESP32C6
HARDWARE: ESP32C6 160MHz, 320KB RAM, 4MB Flash
...
PACKAGES:
 - framework-espidf @ 3.50500.0 (5.5.0)
 - tool-cmake @ 3.30.2
 - toolchain-riscv32-esp @ 14.2.0+20241119
...
ESP-IDF v5.5.0
...
RAM:   [          ]   3.1% (used 10148 bytes from 327680 bytes)
Flash: [          ]   4.1% (used 168667 bytes from 4128768 bytes)
============================================ [SUCCESS] ============================================
```

### Step 4: Verify ESP-IDF Configuration (Optional)
```bash
pio run -t menuconfig
```

**In the menu:**
- Navigate through to verify NimBLE and other components are available
- **DO NOT SAVE** unless you need to make changes
- Press 'Q' to quit

---

## ⚠️ Migration Requirements from v5.3.0

If upgrading from ESP-IDF v5.3.0, follow these steps:

### Required: Fresh PlatformIO Install
```bash
# Uninstall PlatformIO (via IDE extension manager or pip)
pip uninstall platformio

# Reinstall PlatformIO
pip install platformio

# Verify new installation
pio --version
```

### Required: Menuconfig Minimal Save
```bash
# After fresh PlatformIO install and first build attempt
pio run -t menuconfig

# In menuconfig:
# Navigate to bottom of main menu
# Select: "Save minimal configuration"
# Confirm save
# Exit menuconfig (press 'Q')
```

### Required: Clean Build
```bash
# Remove all build artifacts
pio run -t fullclean

# First clean build (takes ~10 minutes, downloads ~1GB)
pio run
```

**First Build Expectations:**
- Downloads ESP-IDF v5.5.0 framework (~500MB)
- Downloads toolchains and packages (~500MB)
- Compiles entire framework (10-15 minutes)
- Creates sdkconfig files
- Subsequent builds: 30-60 seconds

---

## 🔍 Verifying ESP-IDF Version at Runtime

Add this code to your `main.c` to verify ESP-IDF version at runtime:

```c
#include "esp_system.h"
#include "esp_log.h"

static const char *TAG = "VERSION_CHECK";

void app_main(void)
{
    // Print ESP-IDF version
    ESP_LOGI(TAG, "ESP-IDF Version: %s", esp_get_idf_version());
    
    #if ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(5, 5, 0)
        ESP_LOGI(TAG, "✓ ESP-IDF v5.5.0 or later confirmed");
    #else
        ESP_LOGW(TAG, "⚠ ESP-IDF version is older than v5.5.0");
        ESP_LOGW(TAG, "⚠ This may cause compatibility issues");
    #endif
    
    // Your application code here...
}
```

**Expected console output:**
```
I (xxx) VERSION_CHECK: ESP-IDF Version: v5.5.0
I (xxx) VERSION_CHECK: ✓ ESP-IDF v5.5.0 or later confirmed
```

---

## 🔧 Configuration Details

### platformio.ini Configuration (Current Working)

```ini
[env:xiao_esp32c6]
; Official PlatformIO platform with ESP-IDF v5.5.0
platform = espressif32 @ 6.12.0

; ESP-IDF framework (v5.5.0 automatically selected by platform)
framework = espidf

; Official Seeed XIAO ESP32-C6 board (supported since platform v6.11.0)
board = seeed_xiao_esp32c6

; Board configuration
board_build.partitions = default.csv

; Build flags (JPL compliance)
build_flags = 
    -O2
    -Wall
    -Wextra
    -Werror
    -fstack-protector-strong
    -Wformat=2
    -Wformat-overflow=2
    -Wno-format-truncation
    -Wno-format-nonliteral
    -Wimplicit-fallthrough=3
    -DESP_IDF_VERSION_MAJOR=5
    -DESP_IDF_VERSION_MINOR=5
    -DESP_IDF_VERSION_PATCH=0
    -DJPL_COMPLIANT_BUILD=1
    -DSAFETY_CRITICAL=1
    -DTESTING_MODE=1
    -DENABLE_FACTORY_RESET=1
    -DDEBUG_LEVEL=3

; Source file selection (ESP-IDF uses CMake, not build_src_filter)
extra_scripts = 
    pre:scripts/select_source.py

; Monitoring
monitor_speed = 115200
monitor_filters = 
    esp32_exception_decoder
    colorize
    time

; Upload
upload_speed = 921600
upload_protocol = esptool
```

**Key Points:**
- ✅ No `platform_packages` line needed (platform auto-selects ESP-IDF v5.5.0)
- ✅ Board name uses underscore: `seeed_xiao_esp32c6` (not hyphen)
- ✅ Platform v6.12.0 includes official Seeed board support
- ✅ ESP-IDF v5.5.0 automatically selected by platform

---

## 📋 Configuration Validation Checklist

Before considering the configuration "verified", confirm:

- [ ] `pio --version` shows PlatformIO Core v6.1.x or later
- [ ] `pio pkg list` shows espressif32 @ 6.12.0
- [ ] `pio pkg list` shows framework-espidf @ 3.50500.0
- [ ] `pio run --verbose` shows "PLATFORM: Espressif 32 (6.12.0)"
- [ ] `pio run --verbose` shows "ESP-IDF v5.5.0"
- [ ] Build completes without errors
- [ ] Build output shows "framework-espidf @ 3.50500.0 (5.5.0)"
- [ ] RAM usage: 3.1% (10,148 bytes)
- [ ] Flash usage: 4.1% (168,667 bytes)
- [ ] All build flags compile without errors
- [ ] JPL compliance flags are present and active

---

## ❌ Common Issues and Solutions

### Issue 1: "Interface version 4 not supported"

**Error:**
```
CMake Error: argument --interface_version: invalid choice: '4'
(choose from 0, 1, 2, 3)
```

**Root Cause:** Corrupted PlatformIO cache or old CMake version

**Solution:**
1. Fresh PlatformIO install (completely uninstall/reinstall)
2. Clear all caches:
   ```bash
   # Windows
   rmdir /s /q "%USERPROFILE%\.platformio\platforms\espressif32"
   rmdir /s /q "%USERPROFILE%\.platformio\packages\framework-espidf"
   
   # Linux/Mac
   rm -rf ~/.platformio/platforms/espressif32
   rm -rf ~/.platformio/packages/framework-espidf
   ```
3. Run `pio run -t menuconfig` and save minimal configuration
4. Clean rebuild: `pio run -t fullclean && pio run`

### Issue 2: Board Not Found

**Error:**
```
Unknown board ID 'seeed_xiao_esp32c6'
```

**Root Cause:** Platform version too old (< v6.11.0)

**Solution:** 
- Verify platform v6.12.0 is installed: `pio pkg list`
- If wrong version, update platformio.ini to lock platform: `platform = espressif32 @ 6.12.0`
- Clean and rebuild: `pio run -t fullclean && pio run`

### Issue 3: Package Not Found

**Error:**
```
Package not found: framework-espidf @ 3.50500.0
```

**Solution:**
1. Update PlatformIO: `pio upgrade`
2. Update packages: `pio pkg update`
3. Clear cache and rebuild:
   ```bash
   pio run -t fullclean
   pio run
   ```

### Issue 4: Build Flags Errors

**Error:** Various warnings about `-Wstrict-prototypes` or stack usage

**Solution:**
- Verify `build_flags` in platformio.ini match working configuration above
- These flags are specifically tuned for ESP-IDF v5.5.0 framework compatibility
- See `BUILD_CONFIGURATION.md` for detailed flag rationale

### Issue 5: NimBLE Not Found

**Error:**
```
nimble.h: No such file or directory
```

**Solution:**
- NimBLE is included in ESP-IDF v5.5.0 as a native component
- No external libraries needed
- If error persists, run `pio run -t menuconfig`:
  - Component config → Bluetooth → Enable Bluetooth
  - Component config → Bluetooth → Bluedroid Enable → NimBLE
  - Save and exit

---

## 📞 Need Help?

If verification fails or you encounter errors:

1. **Check official PlatformIO ESP32 releases**:
   https://github.com/platformio/platform-espressif32/releases

2. **Check ESP-IDF v5.5.0 release notes**:
   https://github.com/espressif/esp-idf/releases/tag/v5.5.0

3. **Search PlatformIO registry**:
   ```bash
   pio pkg search framework-espidf
   pio pkg search espressif32
   ```

4. **Verify PlatformIO installation**:
   ```bash
   pio --version
   pio upgrade
   pio system info
   ```

5. **Review migration documentation**:
   - `docs/ESP_IDF_V5.5.0_MIGRATION.md` - Complete migration guide
   - `BUILD_CONFIGURATION.md` - Build flag details

---

## ✅ Verified Configuration Summary

**Verified Configuration (October 20, 2025):**
- **Platform**: espressif32 @ 6.12.0
- **Framework**: ESP-IDF v5.5.0 (framework-espidf @ 3.50500.0)
- **Board**: seeed_xiao_esp32c6 (official support)
- **Build Status**: SUCCESS
- **RAM Usage**: 3.1% (10,148 / 327,680 bytes)
- **Flash Usage**: 4.1% (168,667 / 4,128,768 bytes)
- **Build Time**: 610 seconds (first), ~60 seconds (incremental)

**Migration Requirements:**
- Fresh PlatformIO install
- Menuconfig minimal save
- Clean rebuild

**Update this information in:**
- ✅ `BUILD_CONFIGURATION.md` - Updated October 20, 2025
- ✅ `platformio_verification.md` - This document
- ✅ `docs/ESP_IDF_V5.5.0_MIGRATION.md` - Complete migration guide
- [ ] `README.md` - User-facing documentation (next update)
- [ ] `QUICK_START.md` - Setup instructions (next update)

---

**Remember**: The `platformio.ini` file is safety-critical. Any changes must be thoroughly tested and documented before use in medical device applications.
