# platformio.ini Verification Checklist

**Project**: EMDR Bilateral Stimulation Device  
**Date**: 2025-10-15  
**Purpose**: Verify correct ESP-IDF v5.5.1 configuration

---

## ✅ Changes Made to Fix Configuration

### 1. **Fixed Platform Version**
- **Changed from**: `espressif32@6.9.0` (doesn't exist)
- **Changed to**: `espressif32@6.8.1` (latest stable)
- **Reason**: Version 6.9.0 was incorrectly specified

### 2. **Fixed ESP-IDF Package Reference**
- **Changed from**: `framework-espidf @ ~3.50501.0`
- **Changed to**: `platformio/framework-espidf @ ~3.50501.240916`
- **Reason**: Added proper package namespace and build date for ESP-IDF v5.5.1

### 3. **Removed Wrong Dependency** ❌
- **Removed**: `h2zero/NimBLE-Arduino@^1.4.1`
- **Reason**: This is an Arduino library. ESP-IDF v5.5.1 includes NimBLE as a native component
- **No external library needed**: NimBLE is built into ESP-IDF

### 4. **Fixed Build Flags**
- **Removed**: `-fcomplexity-limit=10` (not a real GCC flag)
- **Removed**: `-Wno-dynamic-exception-spec` (C++ only, not needed for C)
- **Added**: Proper JPL-compliant warnings:
  - `-Wstrict-prototypes`
  - `-Wmissing-prototypes`
  - `-Wold-style-definition`
  - `-Wimplicit-fallthrough=3`

---

## 🧪 Verification Steps

Run these commands in your project directory to verify the configuration:

### Step 1: Update Package Cache
```bash
cd "G:\My Drive\AI_PROJECTS\EMDR_PULSER_SONNET4"
pio pkg update
```

**Expected output:**
```
Updating espressif32 @ 6.8.1
Updating framework-espidf @ 3.50501.240916
...
```

### Step 2: Check Available Packages
```bash
pio pkg list
```

**Look for**:
```
espressif32 @ 6.8.1
framework-espidf @ 3.50501.240916
```

### Step 3: Build Project (Verbose)
```bash
pio run --verbose
```

**Critical lines to verify in output:**
```
Processing xiao_esp32c6 (platform: espressif32@6.8.1; framework: espidf)
...
ESP-IDF v5.5.1
...
Compiling .pio/build/xiao_esp32c6/...
```

### Step 4: Open ESP-IDF Configuration Menu (Optional)
```bash
pio run --target menuconfig
```

**Verify in menu:**
- Check "Component config" → "Bluetooth" → Verify NimBLE is available
- Check "Component config" → "FreeRTOS" → Verify watchdog settings

---

## ⚠️ Potential Issues and Solutions

### Issue 1: "Package not found: framework-espidf @ 3.50501.240916"

**Reason**: ESP-IDF v5.5.1 might not be available in PlatformIO registry yet

**Solution Options**:

#### Option A: Use Latest Available ESP-IDF
1. Check available versions:
   ```bash
   pio pkg search "framework-espidf"
   ```

2. Find the latest v5.x version (e.g., `3.50402.0` for v5.4.2)

3. Update `platformio.ini`:
   ```ini
   platform_packages = 
       platformio/framework-espidf @ ~3.50402.0  ; Use latest available
   ```

4. Update ALL documentation to reflect actual version used

#### Option B: Use ESP-IDF v5.3.1 (Known Stable)
```ini
platform = espressif32@6.8.1
platform_packages = 
    platformio/framework-espidf @ ~3.50301.0  ; ESP-IDF v5.3.1
```

**⚠️ WARNING**: If changing from v5.5.1, you MUST:
- Update `requirements_spec.md` DS001
- Update `README.md` 
- Update `architecture_decisions.md` AD001
- Re-test all bilateral timing
- Re-validate JPL compliance

### Issue 2: Build Errors with NimBLE

**If you see**: `nimble.h: No such file or directory`

**Solution**: NimBLE must be enabled in ESP-IDF config

1. Open menuconfig:
   ```bash
   pio run --target menuconfig
   ```

2. Navigate to:
   ```
   Component config → Bluetooth → Bluedroid Bluetooth stack enabled [*]
   Component config → Bluetooth → NimBLE Stack [*]
   ```

3. Save and exit (press 'S', then 'Q')

### Issue 3: Board Not Found

**If you see**: `Unknown board ID 'seeed_xiao_esp32c6'`

**Solution**: Board definition might be missing

Add custom board definition:
```ini
board = esp32-c6-devkitc-1  ; Use generic ESP32-C6 board
board_build.mcu = esp32c6
board_build.f_cpu = 160000000L
```

---

## 📋 Configuration Validation Checklist

Before considering the configuration "verified", confirm:

- [ ] `pio pkg update` completes without errors
- [ ] `pio pkg list` shows correct espressif32 platform version
- [ ] `pio pkg list` shows correct framework-espidf version
- [ ] `pio run --verbose` shows "ESP-IDF v5.5.1" (or documented alternative)
- [ ] Build completes without errors
- [ ] No Arduino libraries are referenced (NimBLE is native ESP-IDF)
- [ ] All build flags compile without errors
- [ ] JPL compliance flags are present and active

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
    
    #if ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(5, 5, 1)
        ESP_LOGI(TAG, "✓ ESP-IDF v5.5.1 or later confirmed");
    #else
        ESP_LOGW(TAG, "⚠ ESP-IDF version is older than v5.5.1");
        ESP_LOGW(TAG, "⚠ This may cause compatibility issues");
    #endif
    
    // Your application code here...
}
```

**Expected console output:**
```
I (xxx) VERSION_CHECK: ESP-IDF Version: v5.5.1
I (xxx) VERSION_CHECK: ✓ ESP-IDF v5.5.1 or later confirmed
```

---

## 📞 Need Help?

If verification fails or you encounter errors:

1. **Check PlatformIO ESP32 platform releases**:
   https://github.com/platformio/platform-espressif32/releases

2. **Check ESP-IDF release dates**:
   https://github.com/espressif/esp-idf/releases

3. **Search PlatformIO registry**:
   ```bash
   pio pkg search framework-espidf
   ```

4. **Verify your PlatformIO installation**:
   ```bash
   pio --version
   pio upgrade
   ```

---

## ✅ Configuration Verified

Once all checks pass, document the results:

**Verified Configuration:**
- Platform: espressif32 @ _______
- Framework: ESP-IDF v_______
- Date: _______
- Verified by: _______

**Update this information in**:
- `requirements_spec.md` (DS001)
- `README.md` (Quick Start section)
- `architecture_decisions.md` (AD001)

---

**Remember**: The `platformio.ini` file is safety-critical. Any changes must be thoroughly tested and documented before use in medical device applications.
