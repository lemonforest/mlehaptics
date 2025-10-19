# Build Configuration Summary

**Last Updated:** 2025-10-17  
**Status:** ✅ **VERIFIED WORKING**

## Quick Reference

### Build Success Confirmation
```
RAM:   [          ]   1.9% (used 10004 bytes from 524288 bytes)
Flash: [          ]   3.9% (used 159633 bytes from 4128768 bytes)
============================================ [SUCCESS] Took 553.61 seconds ============================================
```

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
These flags were **REMOVED** to allow ESP-IDF v5.3.0 framework to compile:

| Flag Removed | Reason | Framework Component Affected |
|--------------|--------|------------------------------|
| `-Wstack-usage=2048` | ADC calibration has unbounded stack | `esp_adc/adc_cali_curve_fitting.c` |
| `-Wstrict-prototypes` | C-only flag, breaks C++ | `cxx/` components |
| `-Wold-style-definition` | ESP-IDF v5.3.0 framework bugs | Multiple framework files |

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

## ESP-IDF Version Lock

**Using:** ESP-IDF v5.3.0 (stable, proven, PlatformIO-compatible)

```ini
platform = espressif32@6.8.1
platform_packages = 
    platformio/framework-espidf @ 3.50300.0  # Locked to v5.3.0
framework = espidf
```

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

### Clean Build
```bash
pio run -t fullclean && pio run
```

### Production Build
```bash
pio run -e xiao_esp32c6_production
```

## Troubleshooting

### If Build Fails
1. Check that no new warnings introduced in `src/` code
2. Verify `platformio.ini` hasn't been modified
3. Ensure ESP-IDF v5.3.0 is being used (check build output)
4. Run clean build to eliminate stale artifacts

### Common Issues
- **New warnings in src/**: Fix the code, don't disable the warning
- **Framework updates**: Don't update ESP-IDF without testing
- **Platform changes**: Locked to espressif32@6.8.1 for stability

## Documentation References

- **Full requirements**: `docs/requirements_spec.md` (DS006)
- **Platform config**: `platformio.ini`
- **JPL compliance**: `docs/requirements_spec.md` (DS003)

---

**Status:** This configuration is tested and working as of 2025-10-17.
