# ESP-IDF v5.5.0 Build - Quick Start Guide

**Date**: 2025-10-20  
**Status**: ✅ **BUILD VERIFIED SUCCESSFUL**  
**Platform**: PlatformIO espressif32 v6.12.0  
**Framework**: ESP-IDF v5.5.0 (framework-espidf @ 3.50500.0)

---

## 🎯 Quick Answer

**Your configuration is ready to build with ESP-IDF v5.5.0!**

Run this command to build:
```bash
pio run
```

**First build:** ~10 minutes (downloads ESP-IDF v5.5.0 framework)  
**Subsequent builds:** ~1 minute (incremental compilation)

---

## 📋 What's Working

### Successful Build Results (October 20, 2025)
```
PLATFORM: Espressif 32 (6.12.0) > Seeed Studio XIAO ESP32C6
HARDWARE: ESP32C6 160MHz, 320KB RAM, 4MB Flash

PACKAGES:
 - framework-espidf @ 3.50500.0 (5.5.0)
 - tool-cmake @ 3.30.2
 - toolchain-riscv32-esp @ 14.2.0+20241119

RAM:   [          ]   3.1% (used 10,148 bytes from 327,680 bytes)
Flash: [          ]   4.1% (used 168,667 bytes from 4,128,768 bytes)

============================================ [SUCCESS] Took 610.28 seconds
```

---

## 🔧 Current Configuration

### platformio.ini (Working)
```ini
[env:xiao_esp32c6]
platform = espressif32 @ 6.12.0      ; Official Seeed XIAO ESP32-C6 support
framework = espidf                   ; Platform auto-selects ESP-IDF v5.5.0
board = seeed_xiao_esp32c6           ; Official board (added in platform v6.11.0)
board_build.partitions = default.csv
```

**Key Points:**
- ✅ Platform v6.12.0 automatically selects ESP-IDF v5.5.0
- ✅ No `platform_packages` configuration needed
- ✅ Official Seeed XIAO ESP32-C6 board support
- ✅ Board name uses underscore (not hyphen)

---

## 🚀 Build Steps

### Standard Build
```bash
cd "G:\My Drive\AI_PROJECTS\EMDR_PULSER_SONNET4"
pio run
```

### With Hardware Upload
```bash
# Upload to connected ESP32-C6
pio run -t upload

# Monitor serial output
pio device monitor

# Combined: Upload and monitor
pio run -t upload && pio device monitor
```

### Hardware Test Environments
```bash
# LED blink test (verify LEDC peripheral)
pio run -e ledc_blink_test -t upload && pio device monitor

# H-bridge PWM test (motor control)
pio run -e hbridge_pwm_test -t upload && pio device monitor
```

### Clean Build (After Version Changes)
```bash
pio run -t fullclean && pio run
```

---

## 🔍 Verification

### Check Build Output For:
```
✓ PLATFORM: Espressif 32 (6.12.0)
✓ framework-espidf @ 3.50500.0 (5.5.0)
✓ Board: Seeed Studio XIAO ESP32C6
✓ RAM Usage: 3.1%
✓ Flash Usage: 4.1%
✓ [SUCCESS]
```

### Verify ESP-IDF Version at Runtime
Add to your code:
```c
#include "esp_system.h"
#include "esp_log.h"

ESP_LOGI("VERSION", "ESP-IDF: %s", esp_get_idf_version());
```

Should output: `ESP-IDF Version: v5.5.0`

---

## ⚠️ Migration from v5.3.0

If upgrading from ESP-IDF v5.3.0, follow these steps:

### 1. Fresh PlatformIO Install (Required)
```bash
# Uninstall PlatformIO
pip uninstall platformio

# Reinstall PlatformIO
pip install platformio

# Verify new installation
pio --version
```

### 2. Update platformio.ini
```ini
[env:xiao_esp32c6]
platform = espressif32 @ 6.12.0  ; Change from 6.8.1
framework = espidf
board = seeed_xiao_esp32c6
# Remove platform_packages line (no longer needed)
```

### 3. Clean Everything
```bash
# Remove project build artifacts
rmdir /s /q .pio

# Clear platform cache (Windows)
rmdir /s /q "%USERPROFILE%\.platformio\platforms\espressif32"
rmdir /s /q "%USERPROFILE%\.platformio\packages\framework-espidf"
```

### 4. Menuconfig Minimal Save (Required)
```bash
# First build attempt
pio run

# Run menuconfig
pio run -t menuconfig

# In menuconfig:
# - Navigate to bottom: "Save minimal configuration"
# - Press 'S' to save
# - Press 'Q' to quit
```

### 5. Final Build
```bash
pio run -t fullclean
pio run
```

**Expected:** First build takes ~10 minutes, downloads ~1GB  
**Subsequent:** ~1 minute builds

---

## ❌ Common Issues and Solutions

### "Interface version 4 not supported"
**Error:**
```
CMake Error: argument --interface_version: invalid choice: '4'
```

**Solution:**
1. Fresh PlatformIO install (completely uninstall/reinstall)
2. Run `pio run -t menuconfig` and save minimal configuration
3. Clean rebuild: `pio run -t fullclean && pio run`

### "Unknown board ID 'seeed_xiao_esp32c6'"
**Cause:** Platform version too old (< v6.11.0)

**Solution:**
- Update platformio.ini: `platform = espressif32 @ 6.12.0`
- Clean and rebuild: `pio run -t fullclean && pio run`

### Build Takes Very Long
**First build:** 10-15 minutes is NORMAL (downloads framework)  
**Subsequent builds:** Should be 30-60 seconds

**If always slow:**
- Check antivirus (may be scanning .pio directory)
- Ensure .pio folder excluded from cloud sync

### "Package not found: framework-espidf"
**Solution:**
```bash
pio upgrade
pio pkg update
pio run -t fullclean
pio run
```

---

## 📊 Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| Platform | espressif32 @ 6.12.0 | Latest stable |
| Framework | ESP-IDF v5.5.0 | Auto-selected |
| Board | seeed_xiao_esp32c6 | Official support |
| First Build | 610 seconds (~10 min) | Downloads ~1GB |
| Incremental | 30-60 seconds | Cached |
| RAM Usage | 3.1% (10KB) | Very low |
| Flash Usage | 4.1% (169KB) | Plenty left |

---

## 📚 Documentation References

- **Migration Guide**: `docs/ESP_IDF_V5.5.0_MIGRATION.md` - Complete details
- **Build Configuration**: `BUILD_CONFIGURATION.md` - Flag explanations
- **Verification**: `docs/platformio_verification.md` - Testing procedures
- **Requirements**: `docs/requirements_spec.md` - DS001, DS002

---

## ✅ Success Criteria

Build is verified when:

- [x] Platform: espressif32 @ 6.12.0
- [x] Framework: ESP-IDF v5.5.0
- [x] Board: seeed_xiao_esp32c6
- [x] Build: SUCCESS
- [x] RAM: < 50% usage
- [x] Flash: < 50% usage
- [x] No warnings in application code

---

## 🎓 What Changed from v5.3.0

### Version Updates
- Platform: espressif32@6.8.1 → espressif32@6.12.0
- Framework: ESP-IDF v5.3.0 → v5.5.0
- Board: Now officially supported (added in platform v6.11.0)

### Configuration Simplifications
- ❌ Removed: `platform_packages` line (no longer needed)
- ✅ Simpler: Platform auto-selects correct ESP-IDF version
- ✅ Official: Board definition now in platform

### New ESP-IDF v5.5.0 Features
- Enhanced ESP32-C6 ULP RISC-V support
- BR/EDR (e)SCO + Wi-Fi coexistence
- Full MQTT 5.0 protocol support
- Hundreds of bug fixes from v5.3.0

---

## 📞 Need Help?

**Check these resources:**
1. `docs/ESP_IDF_V5.5.0_MIGRATION.md` - Detailed migration guide
2. `BUILD_CONFIGURATION.md` - Build flag explanations
3. PlatformIO ESP32 releases: https://github.com/platformio/platform-espressif32/releases
4. ESP-IDF v5.5.0 docs: https://docs.espressif.com/projects/esp-idf/en/v5.5.0/

**Common commands:**
```bash
# Check PlatformIO version
pio --version

# Update PlatformIO
pio upgrade

# Check installed packages
pio pkg list

# System info
pio system info
```

---

## 🔒 Safety-Critical Reminder

This is a **medical device** project with **JPL coding standards**.

Before production:
- ✅ Verify actual ESP-IDF v5.5.0 is being used
- ✅ All documentation reflects v5.5.0
- ✅ Re-test bilateral timing at all cycle times
- ✅ Complete safety validation

---

## ✨ You're Ready!

**Status**: ✅ Configuration verified (October 20, 2025)  
**Action**: Run `pio run` to build  
**Expected**: SUCCESS in ~1 minute (or ~10 min first build)  
**Next**: Hardware testing and development

---

**Configuration Version**: v3 (ESP-IDF v5.5.0)  
**Last Verified**: October 20, 2025  
**Build Status**: SUCCESS ✅
