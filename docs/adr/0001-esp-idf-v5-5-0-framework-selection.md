# 0001: ESP-IDF v5.5.0 Framework Selection

**Date:** 2025-10-20
**Phase:** 0.1
**Status:** Accepted
**Type:** Build System

---

## Summary (Y-Statement)

In the context of selecting a firmware framework for the ESP32-C6 microcontroller,
facing requirements for real-time performance, stable BLE stack, and safety-critical timing,
we decided for ESP-IDF v5.5.0 via PlatformIO,
and neglected Arduino framework and custom bare-metal implementations,
to achieve proven stability and mature FreeRTOS integration for therapeutic applications,
accepting the steeper learning curve and longer build times compared to Arduino.

---

## Problem Statement

The EMDR bilateral stimulation device requires a firmware framework that supports:
- Real-time bilateral timing with ±10ms precision
- Stable BLE 5.0+ for device-to-device communication
- Safety-critical code patterns (JPL coding standards)
- ESP32-C6 RISC-V architecture support
- Predictable memory management and task scheduling

---

## Context

### Technical Constraints
- **Hardware**: Seeed XIAO ESP32-C6 (RISC-V @ 160MHz, 512KB SRAM, 4MB Flash)
- **Timing Critical**: Bilateral stimulation requires non-overlapping motor activation (0.5-2 Hz)
- **Medical Device**: Safety-critical application requires deterministic behavior
- **Power Efficiency**: Battery-powered operation requires efficient sleep modes

### Framework Requirements
- Mature FreeRTOS implementation for multi-task real-time scheduling
- Stable NimBLE stack for BLE 5.0+ peer-to-peer communication
- Comprehensive peripheral drivers (LEDC, ADC, GPIO)
- Active development and long-term support
- PlatformIO integration for reproducible builds

---

## Decision

We will use **ESP-IDF v5.5.0** as the firmware framework, deployed via **PlatformIO espressif32 platform v6.12.0**.

### Implementation Details

**PlatformIO Configuration:**
```ini
[env:base_esp32c6]
platform = espressif32 @ 6.12.0  ; Auto-selects ESP-IDF v5.5.0
framework = espidf
board = seeed_xiao_esp32c6
```

**Key ESP-IDF v5.5.0 Features Used:**
- Enhanced ESP32-C6 support with improved ULP RISC-V coprocessor
- BR/EDR improvements for enhanced (e)SCO + Wi-Fi coexistence
- Mature NimBLE stack for BLE 5.0+ communication
- FreeRTOS v10.5.1 with tickless idle for power management
- Stable heap and stack analysis tools for JPL compliance

---

## Consequences

### Benefits

- **Real-time guarantees**: Mature FreeRTOS integration provides predictable task scheduling
- **Proven stability**: ESP-IDF v5.5.0 includes hundreds of bug fixes from v5.3.0
- **ESP32-C6 optimization**: Enhanced support for RISC-V architecture and peripherals
- **Memory management**: Stable heap/stack analysis tools enable JPL compliance verification
- **Long-term support**: Official Espressif framework with active development
- **PlatformIO integration**: Reproducible builds with version-locked dependencies
- **Migration success**: Build verified at 3.1% RAM (10,148 bytes), 4.1% Flash (168,667 bytes)

### Drawbacks

- **Steep learning curve**: ESP-IDF requires deeper embedded systems knowledge than Arduino
- **Build times**: 610 seconds first build, ~60 seconds incremental (vs. Arduino's faster builds)
- **Framework size**: Larger Flash footprint than minimal bare-metal implementations
- **Migration complexity**: Fresh PlatformIO install required to resolve v5.3.0 → v5.5.0 conflicts

---

## Options Considered

### Option A: ESP-IDF v5.5.0 (via PlatformIO)

**Pros:**
- Latest stable release with enhanced ESP32-C6 support
- Proven NimBLE stack stability
- Mature FreeRTOS real-time capabilities
- PlatformIO integration for reproducible builds
- Official board support for Seeed XIAO ESP32-C6

**Cons:**
- Steeper learning curve than Arduino
- Longer build times (610s first build)
- Requires fresh PlatformIO install for clean migration

**Selected:** YES
**Rationale:** Only option that meets all safety-critical, real-time, and BLE stability requirements

### Option B: Arduino Framework

**Pros:**
- Easier learning curve
- Faster build times
- Large community and library ecosystem

**Cons:**
- Limited real-time capabilities (Arduino loop() model)
- Abstraction overhead hides critical timing behavior
- Less control over FreeRTOS task scheduling
- Insufficient for safety-critical medical device software

**Selected:** NO
**Rationale:** Cannot guarantee ±10ms bilateral timing precision required for therapeutic effectiveness

### Option C: ESP-IDF v5.3.0

**Pros:**
- Previous stable release (known working state)
- Already configured in initial project setup

**Cons:**
- Superseded by v5.5.0 with significant improvements
- Missing enhanced ESP32-C6 support
- Fewer bug fixes than v5.5.0

**Selected:** NO
**Rationale:** Superseded by v5.5.0 with better ESP32-C6 support and stability

### Option D: Native ESP-IDF Build (without PlatformIO)

**Pros:**
- Direct access to ESP-IDF build system
- No PlatformIO abstraction layer

**Cons:**
- Loses PlatformIO's dependency management
- Harder to maintain reproducible builds
- Manual SDK installation and updates
- Less portable across development environments

**Selected:** NO
**Rationale:** PlatformIO provides reproducible builds and dependency management without sacrificing ESP-IDF features

---

## Related Decisions

### Related
- [AD002: JPL Institutional Coding Standard Adoption](0002-jpl-coding-standard-adoption.md) - ESP-IDF APIs used in JPL-compliant patterns
- [AD003: C Language Selection](0003-c-language-selection.md) - ESP-IDF is C-based, aligns with C-only decision
- [AD007: FreeRTOS Task Architecture](0007-freertos-task-architecture.md) - Leverages ESP-IDF's FreeRTOS integration

---

## Implementation Notes

### Code References

- `platformio.ini` - Platform and framework configuration
- All `sdkconfig.*` files - ESP-IDF menuconfig outputs
- `src/CMakeLists.txt` - ESP-IDF CMake integration

### Build Environment

- **Environment Name:** All environments extend `env:base_esp32c6`
- **Configuration Files:** Per-environment `sdkconfig.*` files
- **Build Flags:**
  - `-mno-relax` (RISC-V linker relaxation workaround)
  - `-DBOARD_HAS_PSRAM` (future expansion)

### Testing & Verification

**Migration Verification (October 20, 2025):**
- Fresh PlatformIO install resolved interface version conflicts
- Platform v6.12.0 automatically selected ESP-IDF v5.5.0 (framework-espidf @ 3.50500.0)
- Build successful: 610s first build, ~60s incremental
- RAM usage: 3.1% (10,148 bytes)
- Flash usage: 4.1% (168,667 bytes)
- Menuconfig minimal save resolved v5.3.0 → v5.5.0 config conflicts

**Hardware Testing:**
- All peripherals functional (LEDC PWM, ADC, GPIO, WS2812B)
- BLE stack stable (NimBLE via ESP-IDF)
- FreeRTOS task scheduling verified with oscilloscope
- Deep sleep/wake cycles tested successfully

---

## JPL Coding Standards Compliance

- ✅ Rule #1: No dynamic memory allocation - ESP-IDF allows static allocation strategies
- ✅ Rule #2: Fixed loop bounds - FreeRTOS task loops use bounded queues
- ✅ Rule #3: No recursion - ESP-IDF APIs are non-recursive
- ✅ Rule #5: Return value checking - ESP-IDF uses `esp_err_t` return codes
- ✅ Rule #6: No unbounded waits - FreeRTOS provides timeout parameters
- ✅ Rule #7: Watchdog compliance - ESP-IDF provides Task Watchdog Timer (TWDT)
- ✅ Rule #8: Defensive logging - ESP-IDF provides `ESP_LOGI/ESP_LOGE` macros

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: AD001 (Development Platform and Framework Decisions)
Git commit: Current working tree

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
