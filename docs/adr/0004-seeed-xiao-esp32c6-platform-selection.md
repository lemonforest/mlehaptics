# 0004: Seeed XIAO ESP32-C6 Platform Selection

**Date:** 2025-10-15
**Phase:** 0.1
**Status:** Accepted
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of selecting hardware for a dual-device bilateral stimulation system,
facing requirements for BLE 5.0+ communication, compact form factor, and power efficiency,
we decided for Seeed XIAO ESP32-C6 with RISC-V architecture,
and neglected ESP32 (Xtensa), ESP32-S3, and competing BLE microcontrollers,
to achieve modern open-source architecture with excellent BLE capabilities in ultra-compact package,
accepting the newer RISC-V toolchain and limited community examples compared to ESP32 classic.

---

## Problem Statement

The EMDR bilateral stimulation device requires hardware that supports:
- **Dual-device communication**: Reliable BLE 5.0+ for peer-to-peer coordination
- **Compact form factor**: Wearable/portable design for therapeutic use
- **Real-time processing**: RISC-V with sufficient speed for ±10ms timing precision
- **Power efficiency**: Battery operation for 20+ minute therapy sessions
- **Development support**: Stable toolchain and ESP-IDF compatibility

---

## Context

### Therapeutic Requirements
- **Bilateral stimulation**: Two independent devices (left/right)
- **Wireless coordination**: BLE peer-to-peer with <100ms latency
- **Portable design**: Small enough for wrist-mounted or handheld use
- **Session duration**: 20+ minutes on battery power

### Technical Constraints
- **Memory**: Sufficient for FreeRTOS + NimBLE + application code
- **Peripherals**: LEDC PWM (motor control), ADC (battery monitoring), GPIO (button/LED)
- **Connectivity**: BLE 5.0+ for reliable device-to-device communication
- **Power**: USB-C charging, battery connector, low-power sleep modes

### Market Analysis (October 2025)
- **ESP32-C6**: Newest Espressif chip with RISC-V, WiFi 6, BLE 5.0, Zigbee 3.0
- **Seeed XIAO**: Ultra-compact form factor (21x17.5mm), breadboard-friendly
- **Official support**: Seeed XIAO ESP32-C6 supported in PlatformIO v6.11.0+

---

## Decision

We will use the **Seeed XIAO ESP32-C6** as the hardware platform for both devices in the bilateral system.

### Technical Specifications

**Processor:**
- RISC-V single-core @ 160 MHz
- Modern open-source architecture
- Sufficient for real-time FreeRTOS tasks

**Memory:**
- 512 KB SRAM (adequate for application + NimBLE stack)
- 4 MB Flash (sufficient for firmware + OTA updates)

**Connectivity:**
- **BLE 5.0**: Primary for device-to-device bilateral coordination
- **WiFi 6** (802.11ax): Future expansion for cloud features
- **Zigbee 3.0**: Future expansion for smart home integration

**Physical:**
- **Size**: 21x17.5mm (ultra-compact)
- **Power**: USB-C charging, battery connector
- **Voltage**: 3.3V/5V operation
- **Form factor**: Castellated holes + pin headers for flexible mounting

**Peripherals:**
- LEDC PWM channels (motor control)
- ADC channels (battery voltage, back-EMF sensing)
- GPIO with ISR capability (button, status LED)
- I2C, SPI, UART (future sensor integration)

---

## Consequences

### Benefits

- **RISC-V architecture**: Modern, open-source processor with excellent toolchain support
- **BLE 5.0+ capability**: Essential for reliable device-to-device communication
- **Ultra-compact form factor**: 21x17.5mm enables truly portable therapeutic devices
- **Power efficiency**: Advanced sleep modes support extended battery operation
- **Cost-effective**: ~$7-10 per unit, affordable for dual-device therapy systems
- **USB-C charging**: Modern charging standard, no custom cables
- **WiFi 6 + Zigbee**: Future expansion options without hardware change
- **Official support**: PlatformIO espressif32 v6.11.0+ includes board definition
- **Community adoption**: Growing XIAO ESP32-C6 user base and examples

### Drawbacks

- **Newer platform**: Less community examples than ESP32 classic (Xtensa)
- **RISC-V toolchain**: Newer than Xtensa, fewer debugging tools
- **512KB SRAM**: Smaller than ESP32-S3 (512KB vs 512KB SRAM, same actually)
- **Single-core**: No parallel processing (vs ESP32-S3 dual-core)
- **Limited GPIO**: 21x17.5mm package limits pin count vs full-size ESP32

---

## Options Considered

### Option A: Seeed XIAO ESP32-C6 (RISC-V)

**Pros:**
- Modern RISC-V architecture (open-source ISA)
- BLE 5.0 with excellent performance
- Ultra-compact (21x17.5mm)
- WiFi 6 + Zigbee 3.0 for future features
- Official PlatformIO support
- USB-C charging

**Cons:**
- Newer platform with fewer examples
- RISC-V toolchain less mature than Xtensa
- Single-core (vs ESP32-S3 dual-core)

**Selected:** YES
**Rationale:** Best balance of modern features, BLE capability, and compact size

### Option B: ESP32 Classic (Xtensa, dual-core)

**Pros:**
- Mature platform with extensive examples
- Dual-core for parallel processing
- Large community and library support
- Well-documented

**Cons:**
- Xtensa architecture (proprietary ISA)
- BLE 4.2 (not BLE 5.0)
- Larger physical footprint
- Older technology (2016 design)
- Micro-USB charging (not USB-C)

**Selected:** NO
**Rationale:** BLE 4.2 insufficient for reliable peer-to-peer, larger size undesirable for portable device

### Option C: ESP32-S3 (Xtensa, dual-core)

**Pros:**
- Dual-core for parallel processing
- More SRAM than ESP32-C6 (512KB PSRAM option)
- BLE 5.0 support
- Mature toolchain (Xtensa)

**Cons:**
- Xtensa architecture (proprietary ISA)
- Larger physical footprint than XIAO form factor
- Higher power consumption (dual-core)
- More expensive than ESP32-C6

**Selected:** NO
**Rationale:** Single-core sufficient for this application, RISC-V preferred over Xtensa, larger size undesirable

### Option D: Nordic nRF52840 (ARM Cortex-M4)

**Pros:**
- Excellent BLE stack (SoftDevice)
- Low power consumption
- Mature ARM toolchain
- Strong BLE ecosystem

**Cons:**
- No WiFi (limits future expansion)
- More expensive than ESP32-C6
- Proprietary BLE stack (vs open NimBLE)
- Smaller Flash (1MB vs 4MB)
- Less GPIO/peripheral flexibility

**Selected:** NO
**Rationale:** Lack of WiFi limits future features, more expensive, ESP32-C6 provides better overall value

### Option E: STM32WB (ARM Cortex-M4 + Cortex-M0)

**Pros:**
- Dual-core (application + BLE)
- BLE 5.0 support
- ST ecosystem

**Cons:**
- More complex dual-core programming
- No WiFi
- Less community support than ESP32
- More expensive

**Selected:** NO
**Rationale:** Dual-core complexity not needed, no WiFi, less community support

---

## Related Decisions

### Related
- [AD001: ESP-IDF v5.5.0 Framework Selection](0001-esp-idf-v5-5-0-framework-selection.md) - ESP-IDF v5.5.0 has enhanced ESP32-C6 support
- [AD005: GPIO Assignment Strategy](0005-gpio-assignment-strategy.md) - GPIO mapping for XIAO ESP32-C6
- [AD008: BLE Protocol Architecture](0008-ble-protocol-architecture.md) - Leverages BLE 5.0 capabilities

---

## Implementation Notes

### Code References

- `platformio.ini` - Board definition: `seeed_xiao_esp32c6`
- All `sdkconfig.*` files - ESP32-C6 specific configurations
- `src/ble_manager.c` - NimBLE stack for ESP32-C6
- `src/motor_task.c` - LEDC PWM using ESP32-C6 peripherals

### Build Environment

- **Board Name:** `seeed_xiao_esp32c6` (PlatformIO)
- **Platform:** `espressif32 @ 6.12.0`
- **Framework:** `espidf` (ESP-IDF v5.5.0)
- **Toolchain:** `riscv32-esp-elf-gcc`

### Hardware Configuration

**Pin Assignments (see AD005 for details):**
- GPIO0: Back-EMF sense (ADC)
- GPIO1: User button (RTC wake)
- GPIO2: Battery voltage (ADC)
- GPIO15: Status LED (active LOW)
- GPIO16: WS2812B enable (P-MOSFET, active LOW)
- GPIO17: WS2812B data
- GPIO19: H-bridge IN2 (LEDC PWM)
- GPIO20: H-bridge IN1 (LEDC PWM)
- GPIO21: Battery monitor enable

### Testing & Verification

**Hardware Verified:**
- ✅ LEDC PWM motor control @ 25kHz
- ✅ ADC battery voltage monitoring (12-bit resolution)
- ✅ GPIO ISR for button with RTC wake from deep sleep
- ✅ WS2812B RGB LED via RMT peripheral
- ✅ NimBLE stack peer-to-peer communication
- ✅ Deep sleep < 1mA, wake time < 2 seconds
- ✅ USB-C charging with battery management

**Known Issues:**
- GPIO19/GPIO20 crosstalk during boot (silicon issue, see GPIO_UPDATE_2025-10-17.md)
- Workaround: External pull-downs prevent shoot-through
- Future PCB may move H-bridge control to different GPIOs

---

## JPL Coding Standards Compliance

Hardware selection enables JPL compliance:

- ✅ Rule #1: 512KB SRAM sufficient for static allocation
- ✅ Rule #2: 160MHz RISC-V provides deterministic loop timing
- ✅ Rule #6: Hardware watchdog timer available
- ✅ Rule #7: Task Watchdog Timer (TWDT) in ESP-IDF

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: AD004 (Hardware Architecture Decisions)
Git commit: Current working tree

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
