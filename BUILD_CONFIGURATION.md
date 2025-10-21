# Build Configuration Summary

**Last Updated:** 2025-10-20  
**Status:** ✅ **VERIFIED WORKING - ESP-IDF v5.5.0**

## Quick Reference

### Build Success Confirmation (ESP-IDF v5.5.0)
```
Platform: espressif32 @ 6.12.0
Framework: framework-espidf @ 3.50500.0 (5.5.0)
Board: seeed_xiao_esp32c6 (officially supported)

RAM:   [          ]   3.1% (used 10,148 bytes from 327,680 bytes)
Flash: [          ]   4.1% (used 168,667 bytes from 4,128,768 bytes)
============================================ [SUCCESS] Took 610.28 seconds ============================================
```

**First Build:** ~10 minutes (downloads ESP-IDF v5.5.0 framework)  
**Subsequent Builds:** ~1 minute (incremental compilation)

## Active Build Flags

### Strict Checking (Enabled with `-Werror`)
These flags are **ACTIVE** and treat warnings as errors in your application code:

```ini
-O2                          # Performance optimization for predictable timing
-Wall                        # All standard warnings
-Wextra                      # Extra warnings
-Werror                      # Warnings = Errors (strict enforcement)
-fstack-protector-strong     # Stack overflow protection (JPL)
-Wformat=2                   # Format string security
-Wformat-overflow=2          # Buffer overflow detection
-Wimplicit-fallthrough=3     # Switch case fallthrough detection
```

### Framework Compatibility Exclusions
These flags were **REMOVED** to allow ESP-IDF v5.5.0 framework to compile:

| Flag Removed | Reason | Framework Component Affected |
|--------------|--------|------------------------------|
| `-Wstack-usage=2048` | ADC calibration has unbounded stack | `esp_adc/adc_cali_curve_fitting.c` |
| `-Wstrict-prototypes` | C-only flag, breaks C++ | `cxx/` components |
| `-Wold-style-definition` | ESP-IDF framework limitations | Multiple framework files |

These flags are **DISABLED** for framework components:

```ini
-Wno-format-truncation       # ESP-IDF console component buffer sizing
-Wno-format-nonliteral       # ESP-IDF argtable3 dynamic format strings
```

## Philosophy

### Pragmatic Safety-Critical Development

**✅ What We Do:**
- Apply **full JPL compliance** to application code in `src/`
- Use `-Werror` globally to catch issues in our code
- Trust ESP-IDF's own QA process (used in millions of devices)
- Disable only specific framework warnings that would block builds

**❌ What We Don't Do:**
- Try to force JPL compliance on third-party framework
- Remove `-Werror` completely
- Compromise safety of our application logic
- Mask real issues in our own code

### Result
- **Your code**: Maximum safety checking with warnings as errors
- **Framework code**: Allows compilation while maintaining framework QA
- **Build**: Succeeds reliably
- **Safety**: Not compromised - critical logic fully checked

## ESP-IDF Version Configuration

**Using:** ESP-IDF v5.5.0 (latest stable, enhanced ESP32-C6 support)

```ini
platform = espressif32 @ 6.12.0
# Platform v6.12.0 automatically selects framework-espidf @ 3.50500.0 (ESP-IDF v5.5.0)
framework = espidf
board = seeed_xiao_esp32c6  # Official board support added in platform v6.11.0
```

**Key Features in ESP-IDF v5.5.0:**
- Enhanced ESP32-C6 ULP RISC-V support (better power efficiency)
- BR/EDR (e)SCO + Wi-Fi coexistence improvements
- Full MQTT 5.0 protocol support
- Hundreds of bug fixes from v5.3.0
- Official Seeed XIAO ESP32-C6 board support

**Migration from v5.3.0:**
- ✅ Requires fresh PlatformIO install (uninstall/reinstall if upgrading)
- ✅ Run `pio run -t menuconfig` → Save minimal configuration
- ✅ Platform v6.12.0 auto-selects correct ESP-IDF v5.5.0 framework
- ✅ No explicit `platform_packages` configuration needed
- ✅ First build downloads ~1GB and takes ~10 minutes
- ✅ Build verified successful October 20, 2025

See `docs/ESP_IDF_V5.5.0_MIGRATION.md` for complete migration details.

## Testing Requirements

All application code must:
1. Compile with zero warnings (enforced by `-Werror`)
2. Pass static analysis
3. Follow JPL principles (documented in requirements_spec.md DS003)
4. Use FreeRTOS delays (no busy-wait loops)
5. Validate all input parameters

## Build Commands

### Standard Build
```bash
pio run
```

### Clean Build (After ESP-IDF Version Changes)
```bash
pio run -t fullclean && pio run
```

### Production Build
```bash
pio run -e xiao_esp32c6_production
```

### Hardware Test Builds
```bash
# LED blink test (verify LEDC peripheral)
pio run -e ledc_blink_test -t upload && pio device monitor

# H-bridge PWM test (motor control)
pio run -e hbridge_pwm_test -t upload && pio device monitor
```

## Troubleshooting

### If Build Fails
1. Check that no new warnings introduced in `src/` code
2. Verify `platformio.ini` hasn't been modified
3. Ensure ESP-IDF v5.5.0 is being used (check build output for "framework-espidf @ 3.50500.0")
4. Run clean build to eliminate stale artifacts: `pio run -t fullclean && pio run`

### Common Issues

**"Interface version 4 not supported"**
- **Cause**: Corrupted PlatformIO cache or old platform version
- **Solution**: Fresh PlatformIO install (uninstall/reinstall completely)
- **Then run**: `pio run -t menuconfig` → Save minimal configuration

**"Package not found: framework-espidf @ 3.50500.0"**
- **Cause**: PlatformIO not updated or cache corruption
- **Solution**: `pio upgrade` then `pio pkg update`
- **Or**: Fresh PlatformIO install

**New warnings in src/**
- **Action**: Fix the code, don't disable the warning
- **Reason**: `-Werror` enforces code quality for safety-critical application

**Framework updates**
- **Warning**: Don't update ESP-IDF without testing
- **Reason**: Platform v6.12.0 is locked for reproducibility
- **Process**: Test in separate branch before merging version changes

**Platform changes**
- **Current**: Locked to espressif32@6.12.0 for stability
- **Migration**: Requires full regression testing of bilateral timing

## Performance Metrics (ESP-IDF v5.5.0)

| Metric | Value | Notes |
|--------|-------|-------|
| Platform | espressif32 @ 6.12.0 | Official Seeed board support |
| Framework | ESP-IDF v5.5.0 | Latest stable release |
| Board | seeed_xiao_esp32c6 | Underscore in name (official) |
| First Build | 610 seconds (~10 min) | Downloads framework |
| Incremental Build | 30-60 seconds | Cached dependencies |
| RAM Usage | 3.1% (10,148 bytes) | Very conservative |
| Flash Usage | 4.1% (168,667 bytes) | Plenty of room for growth |
| RAM Available | 327,680 bytes | ESP32-C6 specification |
| Flash Available | 4,128,768 bytes | 4MB flash |

## Documentation References

- **Full requirements**: `docs/requirements_spec.md` (DS001, DS002, DS006)
- **Platform config**: `platformio.ini` (working configuration)
- **JPL compliance**: `docs/requirements_spec.md` (DS003)
- **Migration guide**: `docs/ESP_IDF_V5.5.0_MIGRATION.md` (complete migration details)
- **Build system**: `docs/ESP_IDF_SOURCE_SELECTION.md` (CMake architecture)

---

**Status:** ESP-IDF v5.5.0 configuration verified and working as of October 20, 2025.  
**Migration:** Successfully migrated from v5.3.0 → v5.5.0 with fresh PlatformIO install.  
**Platform:** Official PlatformIO espressif32 v6.12.0 with native Seeed XIAO ESP32-C6 support.
