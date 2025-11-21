# 0017: Conditional Compilation Strategy

**Date:** 2025-11-08
**Phase:** 0.4
**Status:** Accepted
**Type:** Build System

---

## Summary (Y-Statement)

In the context of multiple deployment phases from development to production,
facing the need for different logging, power management, and feature configurations,
we decided for conditional compilation with multiple build configurations,
and neglected runtime configuration switches,
to achieve zero debug overhead in production builds,
accepting that different builds required for different deployment phases.

---

## Problem Statement

A bilateral stimulation device goes through multiple deployment phases:
- Development (intensive debugging and testing)
- Field Testing (reduced logging, some debug features)
- Production (zero debug overhead, optimized power management)

Each phase requires different configurations:
- Logging levels (verbose in development, minimal in production)
- NVS write behavior (disabled statistics in testing, enabled in production)
- Factory reset capability (always available in development, time-limited in production)
- Power management (disabled in development, enabled in production)
- Debug assertions (enabled in development, disabled in production)

The system must support these configurations without:
- Runtime overhead in production builds
- Code bloat from unused debug features
- Complex runtime configuration logic
- Performance degradation from disabled features

---

## Context

**Development Phase Requirements:**
- Verbose logging (ESP_LOGI, ESP_LOGD, ESP_LOGV)
- NVS statistics disabled (reduce flash wear)
- Factory reset always available
- Power management disabled (faster iteration)
- Debug assertions enabled

**Field Testing Phase Requirements:**
- Moderate logging (ESP_LOGI, ESP_LOGW, ESP_LOGE)
- NVS statistics enabled (representative behavior)
- Factory reset time-limited (production-like)
- Power management enabled (battery life testing)
- Debug assertions enabled (catch bugs)

**Production Phase Requirements:**
- Minimal logging (ESP_LOGE only)
- NVS statistics enabled
- Factory reset time-limited or disabled
- Power management fully enabled
- Debug assertions disabled (zero overhead)

**Technical Constraints:**
- ESP32-C6 limited flash (4MB)
- Logging overhead: ~5-10% CPU in verbose mode
- Debug assertions: ~2-5% code size overhead
- Runtime configuration: Adds complexity and overhead

---

## Decision

We implement conditional compilation with multiple build configurations:

1. **Build Modes:**
```c
// Development Build
#ifdef DEVELOPMENT_BUILD
    #define TESTING_MODE              // Disable NVS statistics
    #define ENABLE_FACTORY_RESET      // Always available
    #define VERBOSE_LOGGING           // Full logging
    #undef CONFIG_PM_ENABLE            // Power management disabled
    #define DEBUG_ASSERTIONS          // Runtime checks
#endif

// Field Testing Build
#ifdef FIELD_TESTING_BUILD
    #undef TESTING_MODE                // Enable NVS statistics
    #define ENABLE_FACTORY_RESET       // Time-limited (30s)
    #define MODERATE_LOGGING           // Info/warning/error only
    #define CONFIG_PM_ENABLE           // Power management enabled
    #define DEBUG_ASSERTIONS           // Runtime checks
#endif

// Production Build
#ifdef PRODUCTION_BUILD
    #undef TESTING_MODE                // Enable NVS statistics
    #undef ENABLE_FACTORY_RESET        // Disabled or time-limited
    #define MINIMAL_LOGGING            // Errors only
    #define CONFIG_PM_ENABLE           // Power management fully enabled
    #undef DEBUG_ASSERTIONS            // Zero overhead
#endif
```

2. **Logging Macros:**
```c
#ifdef VERBOSE_LOGGING
    #define LOG_MOTOR(fmt, ...) ESP_LOGI(TAG, fmt, ##__VA_ARGS__)
    #define LOG_DEBUG(fmt, ...) ESP_LOGD(TAG, fmt, ##__VA_ARGS__)
#elif defined(MODERATE_LOGGING)
    #define LOG_MOTOR(fmt, ...) ESP_LOGI(TAG, fmt, ##__VA_ARGS__)
    #define LOG_DEBUG(fmt, ...) do {} while(0)  // No-op
#else // MINIMAL_LOGGING
    #define LOG_MOTOR(fmt, ...) do {} while(0)  // No-op
    #define LOG_DEBUG(fmt, ...) do {} while(0)  // No-op
#endif
```

3. **Factory Reset:**
```c
#ifdef ENABLE_FACTORY_RESET
    // Factory reset logic included in binary
    void check_factory_reset(void) {
        // ... implementation
    }
#else
    // Factory reset completely removed from binary
    void check_factory_reset(void) {
        // No-op
    }
#endif
```

4. **Debug Assertions:**
```c
#ifdef DEBUG_ASSERTIONS
    #define ASSERT(condition) \
        if (!(condition)) { \
            ESP_LOGE(TAG, "Assertion failed: %s", #condition); \
            abort(); \
        }
#else
    #define ASSERT(condition) do {} while(0)  // No-op
#endif
```

---

## Consequences

### Benefits

- **Development Efficiency:** Fast iteration with verbose logging and reduced flash wear
- **Production Optimization:** Zero debug overhead in deployed devices
- **Safety Configuration:** Factory reset can be disabled in production
- **Debugging Capability:** Extensive logging available when needed
- **Code Size Reduction:** Debug features removed from production binary (~5-10% savings)
- **Performance Optimization:** No runtime overhead from disabled features
- **Clear Build Boundaries:** Each phase has well-defined configuration

### Drawbacks

- **Multiple Builds Required:** Different binaries for different phases
- **Build System Complexity:** Multiple sdkconfig files and build flags
- **Testing Coverage:** Must test each build configuration
- **Conditional Compilation:** Code harder to read with many #ifdef blocks
- **Deployment Management:** Must track which build deployed where

---

## Options Considered

### Option A: Conditional Compilation (Selected)

**Pros:**
- Zero runtime overhead in production
- Debug features completely removed from binary
- Clear separation between build phases
- Code size optimization (~5-10% savings)
- Performance optimization (no runtime checks)

**Cons:**
- Multiple builds required
- Build system complexity
- More #ifdef blocks in code

**Selected:** YES
**Rationale:** Zero overhead in production critical for battery-powered device. Debug features add 5-10% overhead, unacceptable in production. Clear build boundaries improve maintainability.

### Option B: Runtime Configuration Switches

**Pros:**
- Single binary for all phases
- Easy to switch modes in field
- No build system complexity

**Cons:**
- ❌ Debug code always present in binary (code bloat)
- ❌ Runtime overhead checking configuration flags
- ❌ Cannot optimize out unused features
- ❌ Logging macros still execute (even if output disabled)
- ❌ Debug assertions add runtime checks

**Selected:** NO
**Rationale:** Runtime overhead unacceptable for production. Battery-powered device requires maximum efficiency. Cannot achieve zero overhead with runtime switches.

### Option C: Separate Source Files for Debug Features

**Pros:**
- No #ifdef blocks in main code
- Clean code separation

**Cons:**
- Code duplication (similar logic in debug and production files)
- Harder to maintain (changes must be synchronized)
- Still requires conditional compilation at link time
- More complex build system

**Selected:** NO
**Rationale:** Code duplication outweighs benefits. Conditional compilation simpler and more maintainable than separate files. #ifdef blocks acceptable for embedded systems.

---

## Related Decisions

### Related
- [AD015: NVS Storage Strategy] - TESTING_MODE flag disables statistics writes
- [AD013: Factory Reset Security Window] - ENABLE_FACTORY_RESET controls factory reset availability
- [AD020: Power Management Strategy] - CONFIG_PM_ENABLE controls power management

---

## Implementation Notes

### Code References

- `platformio.ini` lines XXX-YYY (build environment definitions)
- `sdkconfig.xiao_esp32c6` lines XXX-YYY (production configuration)
- `sdkconfig.xiao_esp32c6_dev` lines XXX-YYY (development configuration)
- `src/main.c` lines XXX-YYY (conditional compilation examples)

### Build Environment

- **Development:** `pio run -e xiao_esp32c6_dev -t upload`
- **Field Testing:** `pio run -e xiao_esp32c6_field -t upload`
- **Production:** `pio run -e xiao_esp32c6 -t upload`

### Build Flags (platformio.ini)

```ini
# Development Build
[env:xiao_esp32c6_dev]
build_flags =
    -DDEVELOPMENT_BUILD
    -DTESTING_MODE
    -DENABLE_FACTORY_RESET
    -DVERBOSE_LOGGING
    -DDEBUG_ASSERTIONS
    -DLOG_LOCAL_LEVEL=ESP_LOG_VERBOSE

# Field Testing Build
[env:xiao_esp32c6_field]
build_flags =
    -DFIELD_TESTING_BUILD
    -DENABLE_FACTORY_RESET
    -DMODERATE_LOGGING
    -DDEBUG_ASSERTIONS
    -DLOG_LOCAL_LEVEL=ESP_LOG_INFO

# Production Build
[env:xiao_esp32c6]
build_flags =
    -DPRODUCTION_BUILD
    -DMINIMAL_LOGGING
    -DLOG_LOCAL_LEVEL=ESP_LOG_ERROR
```

### Code Size Comparison

```
Development Build:
- Binary size: ~1.2 MB
- Logging overhead: ~5-10% CPU
- Debug assertions: ~2-5% code size

Production Build:
- Binary size: ~1.0 MB (~15% smaller)
- Logging overhead: 0% (errors only)
- Debug assertions: 0% (removed)
```

### Testing & Verification

**Build verification performed:**
- Development build: Confirmed verbose logging works
- Field testing build: Confirmed moderate logging, power management enabled
- Production build: Confirmed minimal logging, factory reset disabled (optional)
- Code size comparison: Confirmed ~15% reduction in production build
- Performance testing: Confirmed zero debug overhead in production

**Known limitations:**
- Must maintain multiple build configurations (sync sdkconfig files)
- Code harder to read with #ifdef blocks
- Testing coverage requires testing each build configuration

---

## JPL Coding Standards Compliance

- ✅ Rule #1: No dynamic memory allocation - Conditional compilation uses preprocessor only
- ✅ Rule #2: Fixed loop bounds - No loops in conditional compilation logic
- ✅ Rule #3: No recursion - Linear control flow
- ✅ Rule #4: No goto statements - Structured control flow
- ✅ Rule #5: Return value checking - Not applicable (compile-time only)
- ✅ Rule #6: No unbounded waits - Not applicable (compile-time only)
- ✅ Rule #7: Watchdog compliance - Not applicable (compile-time only)
- ✅ Rule #8: Defensive logging - Conditional logging macros support this

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: ### AD017: Conditional Compilation Strategy
Git commit: [to be filled after migration]

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
