# EMDR Bilateral Stimulation Device - Requirements Specification

**Generated with assistance from Claude Sonnet 4 (Anthropic)**  
**Last Updated: 2025-10-21** *(CP005 updated based on hardware testing)*

## Project Overview

This document defines the complete functional and technical requirements for a dual-device EMDR (Eye Movement Desensitization and Reprocessing) bilateral stimulation system. The system consists of two identical ESP32-C6 devices that automatically pair and coordinate precise bilateral stimulation patterns for therapeutic applications.

## System Purpose

### Primary Objectives
- **Therapeutic Efficacy**: Provide precise bilateral stimulation timing for EMDR therapy
- **Safety-Critical Operation**: Ensure no overlapping stimulation between devices
- **Ease of Use**: Automatic pairing and minimal user intervention required
- **Professional Reliability**: Medical-grade device dependability and consistency

### Target Users
- **Primary**: Licensed EMDR therapists and mental health professionals
- **Secondary**: Researchers studying bilateral stimulation effects
- **Future**: Supervised self-administration under professional guidance

## Development Standards and Requirements

### ESP-IDF Framework Requirements

#### DS001: ESP-IDF Version Targeting
- **Mandatory Version**: ESP-IDF v5.5.0 (VERIFIED BUILD SUCCESS October 20, 2025)
- **Platform**: PlatformIO espressif32 v6.12.0 (official Seeed XIAO ESP32-C6 support)
- **Framework Package**: framework-espidf @ 3.50500.0
- **Rationale**: Latest stable version with enhanced ESP32-C6 ULP support, BR/EDR eSCO + Wi-Fi coexistence, MQTT 5.0
- **API Compliance**: All code must use ESP-IDF v5.5.x APIs and best practices
- **Deprecation Handling**: No use of deprecated functions from earlier ESP-IDF versions
- **Verification**: Build must succeed with platform v6.12.0
- **Migration Notes**: Requires fresh PlatformIO install + menuconfig minimal save

#### DS002: Build System Requirements and Version Enforcement
- **Platform**: PlatformIO with espressif32 platform
- **Framework**: ESP-IDF (not Arduino framework)
- **Toolchain**: Latest stable GCC toolchain for RISC-V (ESP32-C6)
- **Static Analysis**: Code must pass ESP-IDF component analysis tools

**CRITICAL: `platformio.ini` Configuration**

The ESP-IDF v5.5.0 configuration is managed via the `platformio.ini` file in the project root directory. This file MUST contain:

```ini
[env:xiao_esp32c6]
; VERIFIED BUILD SUCCESS with ESP-IDF v5.5.0 (October 20, 2025)
platform = espressif32 @ 6.12.0  ; Official Seeed XIAO ESP32-C6 support
; Platform automatically selects framework-espidf @ 3.50500.0 (ESP-IDF v5.5.0)
framework = espidf
```

**Key Requirements:**
- **Platform version lock**: `espressif32 @ 6.12.0` ensures latest ESP32-C6 support and ESP-IDF v5.5.0
- **Automatic framework selection**: Platform v6.12.0 automatically selects framework-espidf @ 3.50500.0
- **Seeed board support**: Official seeed_xiao_esp32c6 board definition (added in v6.11.0)
- **Enhanced ULP**: ESP32-C6 ULP RISC-V support for battery-efficient bilateral timing
- **Build validation**: VERIFIED successful build on October 20, 2025
- **Migration requirement**: Fresh PlatformIO install required if upgrading from v5.3.0

**Verification Steps:**
1. Build output must show "framework-espidf @ 3.50500.0 (5.5.0)"
2. First build after fresh install: ~10 minutes (downloads ~1GB)
3. Subsequent builds: ~1 minute incremental
4. Run `pio run -t menuconfig` → Save minimal configuration for sdkconfig
5. Static analysis must validate no deprecated API usage from earlier versions

**Safety Note**: Modifying the platform or framework versions requires:
- Complete requirements specification review and update
- Full regression testing of bilateral timing precision
- JPL coding standard re-validation
- Architecture decisions document update (see AD001)

### Safety-Critical Coding Standards

#### DS003: JPL Institutional Coding Standard Compliance
**Implementation of JPL Coding Standard for C Programming Language for safety-critical medical device:**

**Memory Management:**
- **No dynamic memory allocation** (malloc/free) during runtime
- **Static allocation only** for all data structures
- **Stack usage analysis** with defined limits per function
- **No memory leaks** - all resources statically allocated

**Control Flow:**
- **No recursion** - all algorithms must use iterative approaches
- **Limited function complexity** - maximum cyclomatic complexity of 10
- **Single entry/exit points** for all functions
- **No goto statements** except for error cleanup patterns

**Error Handling:**
- **Comprehensive error checking** for all function calls
- **Defensive programming** with parameter validation
- **Error propagation** using esp_err_t return codes
- **Fail-safe behavior** with graceful degradation

**Data Integrity:**
- **Type safety** with explicit casting where necessary
- **Boundary checking** for all array and buffer operations
- **Integer overflow protection** with range validation
- **Uninitialized variable prevention** with explicit initialization

#### DS004: Safety-Critical Implementation Rules
- **Bilateral timing precision**: ±10ms maximum deviation from configured total cycle time
- **Half-cycle guarantee**: Each device stimulates for exactly 50% of total cycle time
- **Dead time budget**: 1ms dead time included within half-cycle allocation (uses FreeRTOS delay)
- **Emergency shutdown**: Immediate motor coast within 50ms of button press
- **Connection loss handling**: Automatic safe mode within 2 seconds
- **Power failure recovery**: Graceful restart with no persistent unsafe states

#### DS005: Task Watchdog Timer Requirements
- **TWDT timeout**: 2000ms maximum for all monitored tasks (accommodates 1000ms half-cycles)
- **Adaptive feeding strategy**: 
  - Short half-cycles (≤500ms): Feed at end only (1ms dead time)
  - Long half-cycles (>500ms): Feed mid-cycle + end for additional safety
- **Monitored tasks**: Button ISR, BLE Manager, Motor Controller, Battery Monitor
- **Reset behavior**: Immediate system reset on timeout (fail-safe)
- **Timer-based architecture**: FreeRTOS delays for all timing operations
- **Safety margin**: Minimum 4x margin (feeds every 250-501ms vs 2000ms timeout)

#### DS006: Build Configuration and Compiler Flags
**Enforcement of safety-critical compilation standards while maintaining ESP-IDF framework compatibility.**

**Enabled Strict Checking (`-Werror` enforced):**
- **`-Wall -Wextra -Werror`**: All warnings treated as errors for application code
- **`-O2`**: Performance optimization (not `-Os`) for predictable timing
- **`-fstack-protector-strong`**: Stack overflow protection (JPL compliance)
- **`-Wformat=2 -Wformat-overflow=2`**: Format string security and buffer overflow detection
- **`-Wimplicit-fallthrough=3`**: Switch case fallthrough detection

**Disabled for ESP-IDF Framework Compatibility:**
- **`-Wstack-usage=2048`**: Removed - ESP-IDF ADC calibration code has unbounded stack usage
- **`-Wstrict-prototypes`**: Removed - C-only flag conflicts with C++ framework components
- **`-Wold-style-definition`**: Removed - conflicts with ESP-IDF framework limitations
- **`-Wno-format-truncation`**: ESP-IDF console component has unavoidable buffer sizing warnings
- **`-Wno-format-nonliteral`**: ESP-IDF argtable3 uses dynamic format strings

**Rationale:**
- ESP-IDF is a mature, battle-tested framework used in millions of production devices
- Framework code has its own QA validation independent of JPL standards
- Application code in `src/` directory follows full JPL compliance
- Pragmatic approach: strict checking on safety-critical application logic, trust framework QA
- Build must succeed to enable development; framework warnings don't compromise device safety

**Verification:**
- Application code warnings still treated as errors
- Framework compilation succeeds without masking real issues
- All safety-critical timing and logic uses FreeRTOS APIs with full checking enabled

## Functional Requirements

### Core System Behavior

#### FR001: Automatic Device Pairing
- **Power-on discovery**: Devices automatically find each other within 30 seconds
- **Role assignment**: First device becomes server, second becomes client
- **Race condition prevention**: Random 0-2000ms startup delay prevents simultaneous server attempts
- **Pairing persistence**: Device MAC addresses stored in NVS for reconnection

#### FR002: Bilateral Stimulation Control
- **Non-overlapping pattern**: Devices NEVER stimulate simultaneously (safety-critical requirement)
- **Precise timing**: Total cycle time configurable 500-2000ms with ±10ms accuracy
- **Half-cycle allocation**: Each device gets exactly 50% of total cycle time
- **Default cycle**: 1000ms total (500ms per device, 1 Hz bilateral rate)
- **Therapeutic range**: 0.5 Hz (2000ms cycle) to 2 Hz (500ms cycle) bilateral stimulation
- **Server control**: Server device maintains master timing and coordinates client
- **Intensity control**: Variable PWM intensity from 0-100% for both devices
- **Dead time inclusion**: 1ms dead time included within each half-cycle window

#### FR003: Session Management
- **Default duration**: 20 minutes with automatic shutdown
- **Manual control**: User-configurable session length via mobile app
- **Progress tracking**: Session time remaining indicated via status patterns
- **Coordinated shutdown**: Either device can trigger bilateral shutdown

#### FR004: Emergency Safety Features
- **Emergency stop**: 5-second button hold immediately disables all outputs
- **Connection monitoring**: Automatic safe mode if peer device disconnects
- **Power failure handling**: No persistent unsafe states across power cycles
- **Clear NVS (unpair and reset)**: 10-second button hold during first 30 seconds clears paired device and user settings from NVS

#### FR005: Single Device Operation
- **Standalone mode**: Device operates alone if pairing fails after 30 seconds
- **Fallback pattern**: Forward/reverse alternating motor pattern for single-device therapy
- **Cycle timing**: Configurable total cycle time (500-2000ms) with direction reversal at half-cycle
- **Connection retry**: Periodic attempts to discover and pair with second device
- **Status indication**: Heartbeat LED pattern indicates single-device mode

#### FR006: Error Recovery
- **Connection loss**: Automatic reconnection attempts with exponential backoff
- **Timeout handling**: Graceful fallback for all network operations
- **Error logging**: Persistent error tracking in NVS for diagnostics
- **Diagnostic modes**: Special LED patterns for different error conditions

#### FR007: H-Bridge Motor Control Architecture
- **Bidirectional control**: Full H-bridge with IN/IN configuration for forward/reverse motor operation
- **Dead time protection**: 1ms FreeRTOS delay at end of each half-cycle prevents shoot-through
- **JPL compliance**: Uses vTaskDelay() for all timing operations (no busy-wait loops)
- **Watchdog integration**: Dead time period used for TWDT feeding
- **PWM frequency**: 25kHz operation above human hearing range for smooth, silent motor control
- **Emergency coast**: Immediate motor coast mode (both inputs low) for emergency shutdown
- **Component design**: All-MOSFET design using AO3400A/AO3401A family

#### FR008: Single-Device Motor Fallback Enhancement
- **Forward/reverse alternating**: When no paired device found, single motor alternates direction to simulate bilateral effect
- **Cycle timing**: Configurable total cycle (500-2000ms) with direction reversal at half-cycle point
- **Dead time**: 1ms FreeRTOS delay at each half-cycle transition
- **Intensity consistency**: Same PWM intensity as bilateral mode for therapeutic equivalence
- **Status indication**: Heartbeat LED pattern confirms single-device motor operation

#### FR009: Motor Stall Detection and Recovery
- **Implementation**: Deferred to Phase 2 with dedicated H-bridge IC
- **Phase 1 safety**: Emergency coast (5-second button hold) and LED fallback
- **Phase 2 features**: Hardware-based stall detection, thermal protection, fault reporting
- **Current approach**: Focus on core bilateral timing and BLE reliability

#### FR010: Optional Therapy Light (Research Feature)
- **Purpose**: Experimental visual bilateral stimulation research
- **Implementation**: GPIO17 with dual footprint design supporting two assembly options:
  - **WS2812B option** (default): Addressable RGB LED using led_strip component
  - **Simple LED option** (community): 1206 LED connected to WS2812B DIN+GND pads, controlled via LEDC PWM
- **Current limiting**: 62Ω resistor inline from GPIO17 (always populated, works for both options)
- **Builder responsibility**: Simple LED builders must use LEDC/GPIO control (not led_strip component)
- **Case dependency**: Requires case material with light transmission capability (see CP005)
- **Priority**: Secondary to motor-based bilateral stimulation
- **Control**: Therapist-configurable via mobile app (enable/disable/intensity/color)
- **Research value**: Unknown therapeutic benefit - requires field testing with EMDR practitioners
- **Build variants**: Light-blocking cases (motor-only) vs light-transmitting cases (motor + light)
- **Original developer note**: All devices built by original developer use WS2812B hardware with purple dyed SLS nylon cases (light transmission verified)

#### FR011: Haptic Effects Within Bilateral Timing
- **Short pulse support**: Motor can activate for durations shorter than half-cycle
- **Timing budget**: pulse_duration_ms + dead_time_ms ≤ half_cycle_ms
- **Cycle maintenance**: Total cycle time always maintained regardless of pulse duration
- **Non-overlapping safety**: Devices remain on opposite half-cycles even with short pulses
- **Example**: 1000ms cycle → 500ms half-cycle → 200ms pulse + 300ms coast = 500ms window

## Technical Requirements

### Hardware Platform

#### TR001: ESP32-C6 Microcontroller
- **Processor**: RISC-V 160MHz with adequate real-time performance
- **Memory**: 512KB SRAM, 4MB Flash sufficient for application and future OTA
- **Connectivity**: BLE 5.0+ for reliable device-to-device communication

#### TR002: GPIO Configuration and Hardware Interfaces
- **Back-EMF Sensing**: GPIO0 (ADC1_CH0), OUTA from H-bridge, power-efficient motor stall detection
- **Button Input**: GPIO1 (via jumper from GPIO18), hardware debounced with 10k pull-up, ISR support for emergency response
- **Button Physical Location**: GPIO18 on PCB, jumpered to GPIO1, configured as high-impedance input to follow GPIO1 signal
- **Battery Monitor**: GPIO2 (ADC1_CH2, resistor divider input), GPIO21 (P-MOSFET enable control)
- **Status LED**: GPIO15, on/off control for system status indication
- **Therapy Light Enable**: GPIO16, P-MOSFET driver (**ACTIVE LOW** - LOW=enabled, HIGH=disabled) for therapy LED power control
- **Therapy Light Output**: GPIO17, dual footprint design supporting two assembly options:
  - **WS2812B option** (default for original developer): Addressable RGB LED via led_strip component
  - **Simple LED option** (community builders): 1206 LED connected to WS2812B DIN+GND pads, controlled via LEDC PWM
  - **Current limiting**: 62Ω resistor inline from GPIO17 (always populated)
  - **Build flags**: `THERAPY_LIGHT_WS2812B` or `THERAPY_LIGHT_SIMPLE_LED` (see build configuration)
  - **Case dependency**: Visual therapy light only functional with light-transmitting case materials (see CP005)
  - **Light-blocking cases**: GPIO17 unused (light hardware may be assembled but not visible)
- **Motor Control**: GPIO19 (H-bridge IN1 forward), GPIO20 (H-bridge IN2 reverse) for bidirectional motor control

#### TR007: Therapy Light Build Configuration

**Purpose:** Allow builders to configure firmware for their LED hardware choice and case type.

**Build Flag Options:**

```c
// WS2812B RGB LED (default for original developer)
#define THERAPY_LIGHT_WS2812B
// - Uses ESP-IDF led_strip component
// - RGB color control via led_strip_set_pixel()
// - Requires idf_component.yml with espressif/led_strip dependency
// - All light-transmitting case builds by original developer use this

// Simple 1206 LED (community builder option)  
#define THERAPY_LIGHT_SIMPLE_LED
// - Uses LEDC PWM for intensity control only (no color)
// - GPIO17 direct control via LEDC functions (no led_strip)
// - Builder responsibility: do not call led_strip functions
// - Lower cost, simpler firmware

// No therapy light (light-blocking case or disabled)
// - Neither flag defined
// - GPIO17 code disabled/unused
// - Saves flash space if therapy light not needed
```

**PlatformIO Configuration Examples:**

```ini
# Original developer (light-transmitting + WS2812B)
[env:xiao_esp32c6]
build_flags = 
    ${env:base.build_flags}
    -DTHERAPY_LIGHT_WS2812B

# Community builder (light-transmitting + simple LED)
[env:xiao_esp32c6_simple_led]
build_flags = 
    ${env:base.build_flags}
    -DTHERAPY_LIGHT_SIMPLE_LED

# Any builder (light-blocking case, motor only)
[env:xiao_esp32c6_opaque]
build_flags = 
    ${env:base.build_flags}
    # No therapy light flags - code disabled
```

**Hardware-Firmware Compatibility Matrix:**

| LED Hardware | Case Light Transmission | Build Flag | Result |
|--------------|------------------------|------------|--------|
| WS2812B | Good transmission | `THERAPY_LIGHT_WS2812B` | ✅ Full RGB therapy light |
| WS2812B | Blocks light | None | ✅ LED inactive (light blocked, code disabled) |
| Simple LED | Good transmission | `THERAPY_LIGHT_SIMPLE_LED` | ✅ Single-color therapy light |
| Simple LED | Blocks light | None | ✅ LED inactive (light blocked, code disabled) |
| WS2812B | Good transmission | `THERAPY_LIGHT_SIMPLE_LED` | ⚠️ Compiles but wrong driver (works but no color) |
| Simple LED | Good transmission | `THERAPY_LIGHT_WS2812B` | ❌ Will not work (led_strip expects WS2812B protocol) |

**Validation:**
- Builder must select correct flag for their assembled hardware AND case material
- Incorrect flag may cause non-functional therapy light or compilation errors
- Case material light transmission testing is MANDATORY (see CP005)

#### TR003: Power Requirements
- **Session Duration**: Minimum 20 minutes active operation
- **Standby**: Extended deep sleep with button wake capability  
- **Efficiency**: Automatic power management with session timers

### Software Architecture

#### TR004: Real-Time Operating System
- **RTOS**: FreeRTOS with proper task prioritization
- **Thread Safety**: Mutex protection for shared resources
- **Message Queues**: Inter-task communication for coordinated operations
- **Timing**: All delays use vTaskDelay() for JPL compliance (no busy-wait loops)

#### TR005: Wireless Communication
- **Protocol**: Bluetooth Low Energy (BLE) 5.0+
- **Services**: Dual GATT services for device-to-device and mobile app
- **Security**: Device authentication and encrypted communication

#### TR006: Data Persistence
- **Storage**: NVS (Non-Volatile Storage) for configuration and pairing data
- **Reliability**: Error handling and corruption recovery
- **Testing**: Conditional compilation flags for development phases

## Performance Requirements

### Timing Specifications

#### PF001: Response Times and Bilateral Timing
- **Button Response**: < 50ms from press to acknowledgment
- **BLE Connection**: < 10 seconds for device discovery and pairing
- **Total Cycle Timing**: ±10ms precision for configured total cycle time (500-2000ms)
- **Half-cycle precision**: Each device maintains exact 50% of total cycle time
- **Dead time overhead**: 1ms per half-cycle (0.1-0.2% of half-cycle budget)
- **Therapeutic rates**: 
  - Fast: 500ms cycle (250ms per device, 2 Hz rate)
  - Standard: 1000ms cycle (500ms per device, 1 Hz rate)  
  - Slow: 2000ms cycle (1000ms per device, 0.5 Hz rate)

#### PF002: Battery Life  
- **Active Session**: Minimum 20 minutes of bilateral stimulation
- **Deep Sleep**: < 1mA current consumption
- **Wake Time**: < 2 seconds from button press to full operation

#### PF003: Reliability
- **Connection Stability**: 99% uptime during 20-minute sessions
- **Error Recovery**: Automatic reconnection within 5 seconds
- **Memory Management**: No memory leaks or stack overflows
- **Motor Protection**: H-bridge shoot-through prevention with 1ms FreeRTOS dead time

#### PF004: Motor Control Performance
- **H-bridge switching**: 25kHz PWM frequency for silent motor operation above human hearing
- **Dead time implementation**: 1ms FreeRTOS delay (vTaskDelay) at end of each half-cycle
- **GPIO write speed**: ~50ns natural dead time during direction changes
- **Watchdog feeding**: TWDT reset during 1ms dead time period
- **Timing budget**: Motor active for (half_cycle_ms - 1) with 1ms reserved for dead time
- **Power efficiency**: <1mW power loss per MOSFET with AO3400A/AO3401A components
- **Current consumption**: 90mA typical motor operation, 120mA maximum stall current

#### PF005: Battery Management Performance  
- **Voltage monitoring**: 12-bit ADC resolution for precise battery level measurement
- **Monitor enable**: <1ms response time for battery voltage divider enable/disable
- **Power consumption**: <1mA battery monitor circuit when enabled, <1μA when disabled
- **Voltage range**: 4.2V (full) to 3.0V (cutoff) with accurate percentage calculation

## User Interface Requirements

### Physical Interface

#### UI001: Button Operation
- **Wake Up**: 2-second hold to wake from deep sleep
- **Emergency Shutdown**: 5-second hold for immediate stop (both devices)
- **Clear NVS**: 10-second hold during first 30 seconds after boot (unpairs device and clears user settings)

#### UI002: Visual Feedback
- **Boot Sequence**: 3-flash confirmation of successful startup
- **Scanning**: Fast blink (200ms) when searching for server
- **Listening**: Slow blink (1000ms) when waiting for client
- **Connected**: Solid on during bilateral stimulation
- **Errors**: Specific patterns for different error conditions

### Mobile App Interface

#### UI003: Configuration Screen
- Total cycle time adjustment (500-2000ms, displayed as Hz: 0.5-2 Hz)
- Session duration adjustment (5-60 minutes)
- Stimulation intensity control (0-100%)
- Device pairing management
- Clear NVS (unpair and reset settings) control

#### UI004: Session Monitoring
- Real-time stimulation status display with current cycle time
- Battery level indication for both devices
- Connection quality and error reporting
- Emergency stop capability

## Security Requirements

### Data Protection

#### SC001: Device Authentication
- Encrypted BLE communication between devices
- MAC address verification for trusted device pairing
- Protection against unauthorized device connections

#### SC002: Mobile App Security
- Secure GATT service access controls
- Input validation for all configuration parameters
- Session isolation between different mobile devices

#### SC003: BLE Configuration Parameter Validation
- **Range checking**: All BLE-configurable parameters validated before acceptance
- **Session duration**: 5-60 minutes (300,000-3,600,000ms)
- **Motor intensity**: 0-100% with overflow protection
- **Total cycle timing**: 500-2000ms (validated before calculating half-cycles)
- **Haptic pulse duration**: Must be ≤ (total_cycle_ms / 2) to fit in half-cycle window
- **Rejection protocol**: Invalid parameters rejected with BLE error codes
- **Logging**: All validation failures logged for diagnostics

## Compliance Requirements

### Hardware Manufacturing and Open Source Strategy

#### CP004: Open Source Hardware Commitment
- **Complete hardware release**: Schematics, PCB design files, and case models under open source license
- **Multiple case design options**: Case models for various materials and light transmission capabilities
- **User choice**: Builders select case material based on desired features, cost constraints, and manufacturing capabilities
- **Documentation**: Complete assembly instructions and bill of materials for multiple variants

#### CP005: Case Material Light Transmission and Therapy Light Compatibility

**Critical Discovery: Light Transmission is a Spectrum, Not Binary**

Hardware testing has revealed that **light transmission varies significantly** by material type, color, wall thickness, and printing method. The therapy light (GPIO17) functionality depends on **actual light transmission capability** of the assembled case, which builders must test for their specific material and color combination.

---

**Hardware Assembly Options (Open Source Builder's Choice)**

**LED Hardware Options at Assembly Time:**

**WS2812B RGB LED** (default for original developer):
- Uses ESP-IDF led_strip component
- Full RGB color therapy options (warm white, cool white, blue, green, amber)
- Build flag: `THERAPY_LIGHT_WS2812B`
- Connected to GPIO17 via 62Ω resistor
- All devices built by original developer use this option

**Simple 1206 LED** (community alternative):
- Connected to WS2812B footprint DIN+GND pads
- Uses LEDC PWM for intensity control (no color control)
- Build flag: `THERAPY_LIGHT_SIMPLE_LED`
- Builder must use LEDC/GPIO functions (not led_strip component)
- Lower cost alternative for basic visual stimulation

**Current Limiting:**
- 62Ω resistor inline from GPIO17 (always populated, standard part)
- Works for both LED hardware options

---

**Light Transmission Reality by Material and Color**

**Materials with GOOD Light Transmission** (Therapy light functional):
- **Clear resin** (SLA/DLP): Excellent transparency, minimal light scatter
- **Translucent PETG**: Good light diffusion, easier to print than resin
- **Purple/natural/light-colored SLS nylon**: Partial light transmission (**hardware verified** - purple dyed nylon transmits light)
- **Translucent TPU**: Flexible with interesting light diffusion properties
- **White/light-colored FDM filaments** (thin walls): May transmit enough light depending on wall thickness
- **Natural/undyed polymers**: Generally transmit more light than dyed versions

**Materials with LIMITED Light Transmission** (Test before committing):
- **Standard colored FDM filaments** (PLA, ABS, PETG): Depends heavily on pigment density
- **SLS nylon with medium pigment density**: Test sample required to verify
- **Thick-walled prints**: Even translucent materials block light with excessive thickness
- **High infill percentage prints**: Less light transmission with denser internal structure

**Materials that BLOCK Light** (Motor-only builds):
- **Black or dark-colored materials**: Dense pigments block most/all visible light
- **Carbon fiber reinforced materials**: Excellent light blocking, high strength
- **Opaque PLA/ABS with 100% infill**: Solid walls prevent light transmission
- **Metal cases** (future injection molding): Complete light blocking

---

**Builder Testing Procedure** (MANDATORY before committing to case material):

Before finalizing case material selection, builders MUST test light transmission:

1. **Print test piece**: 10mm × 10mm × actual_case_wall_thickness
2. **Assemble LED**: Install WS2812B or simple LED with 62Ω current limiting resistor
3. **Dark room test**: Hold LED directly behind test piece, verify visibility
4. **Decision criteria**:
   - **Light clearly visible**: Therapy light will function → Use `THERAPY_LIGHT_WS2812B` or `THERAPY_LIGHT_SIMPLE_LED`
   - **Light partially visible**: Decide if diffusion/intensity is acceptable
   - **No light visible**: Light blocked → Build motor-only (no therapy light flags)

**Note**: Wall thickness and infill percentage significantly affect transmission. A material that transmits light at 1mm may block it at 3mm.

---

**Case Build Strategies by Application**

**Motor-Only Builds** (Light-blocking materials):
- **Materials**: Black nylon SLS, dark PLA/ABS, carbon fiber, metal enclosures
- **Features**: Motor-based bilateral stimulation only
- **GPIO17 status**: Unused (light hardware optional, not visible if installed)
- **Build configuration**: Define neither `THERAPY_LIGHT_WS2812B` nor `THERAPY_LIGHT_SIMPLE_LED`
- **Advantages**: Widest material selection, lowest cost, highest durability options
- **Use case**: Core EMDR therapy with proven motor-based bilateral stimulation

**Therapy Light Builds** (Light-transmitting materials):
- **Materials**: Clear resin, translucent PETG, light-colored SLS nylon, natural polymers
- **Features**: Motor + visual bilateral stimulation via GPIO17
- **LED options**: 
  - WS2812B: Full RGB color therapy with 5 therapeutic presets
  - Simple LED: Single-color intensity control (lower cost)
- **Build configuration**: Use appropriate flag for assembled LED hardware
- **Material testing**: MANDATORY light transmission test before production run
- **Use case**: Visual bilateral stimulation research, multi-modal therapy options

**Hybrid Builds** (Advanced):
- **Multi-material printing**: Opaque base structure + translucent window inserts
- **Dual-material SLS**: Light-blocking nylon body + translucent nylon windows
- **Example**: Black case body with clear resin therapy light window
- **Advantages**: Structural durability with targeted light transmission
- **Complexity**: Requires multi-material printing capability or post-assembly

---

**Material Selection Guidance**

**For Maximum Therapy Light Visibility:**
1. **First choice**: Clear resin (SLA/DLP) - best transparency
2. **Second choice**: Translucent PETG - good balance of printability and transmission
3. **Third choice**: Natural/light-colored SLS nylon - proven to transmit light (purple dyed nylon verified in hardware testing)

**For Maximum Case Durability:**
1. **First choice**: Carbon fiber reinforced polymer - blocks light completely
2. **Second choice**: Black/dark SLS nylon - professional finish, light blocking
3. **Third choice**: Thick-walled opaque PLA/ABS - adequate durability, motor-only

**For Lowest Cost:**
1. **Standard FDM filament** (any dark color) - motor-only builds
2. **Test before committing**: Light colors MAY transmit depending on wall thickness

---

**Hardware-Firmware Compatibility Decision Tree**

```
START: Choose case material
  │
  ├─ Test piece shows GOOD light transmission?
  │   ├─ YES → Choose LED hardware
  │   │   ├─ Budget allows WS2812B? 
  │   │   │   ├─ YES → Use THERAPY_LIGHT_WS2812B flag
  │   │   │   └─ NO → Use THERAPY_LIGHT_SIMPLE_LED flag
  │   │   └─ END: Therapy light functional
  │   │
  │   └─ NO → Motor-only build
  │       ├─ No therapy light build flags
  │       ├─ GPIO17 unused (LED optional but not visible)
  │       └─ END: Core EMDR functionality with motor only
  │
END
```

---

**Critical Notes for Open Source Community**

**Original Developer Experience:**
- All devices use WS2812B RGB LED hardware
- Purple dyed SLS nylon cases transmit light (**hardware verified October 21, 2025**)
- This discovery prompted documentation update to reflect reality

**Community Builder Considerations:**
- **Do not assume** material descriptions (opaque/translucent) are accurate
- **Always test** your specific material + color + wall thickness combination
- **Injection molding** may behave differently than 3D printed materials
- **Pigment density** varies by manufacturer and batch

**Future Manufacturing Options:**
- Professional injection molded cases may use different materials with different light transmission characteristics
- Medical device certification may require specific case materials
- Material selection should consider both therapeutic effectiveness and regulatory compliance

---

**Documentation Updates:**
- **CP005 updated** October 21, 2025 based on purple dyed SLS nylon hardware testing
- Light transmission is a **spectrum**, not binary opaque/translucent
- Builder testing procedure now **MANDATORY** before production case manufacturing

### Medical Device Considerations

#### CP001: Safety Standards
- Electrical safety for body-contact devices
- EMC compliance for medical environments  
- Material safety for extended skin contact (motor housing, case materials)
- JPL coding standard compliance for safety-critical software

#### CP002: Therapeutic Effectiveness
- Precise timing for therapeutic bilateral stimulation (0.5-2 Hz range)
- Consistent stimulation intensity and patterns
- Minimal latency for real-time therapy sessions
- Research validation for visual bilateral stimulation (therapy light)

#### CP003: Development Standards Compliance
- **ESP-IDF v5.5.0**: Latest stable framework (VERIFIED October 20, 2025)
- **JPL Coding Standard**: Safety-critical software development practices including no busy-wait loops
- **Static Analysis**: Automated code quality verification
- **Medical Device Quality**: IEC 62304 software lifecycle considerations
- **Open Source Compliance**: Full hardware and software design transparency

## Quality Assurance

### Testing Requirements

#### QA001: Unit Testing
- Individual module functionality verification
- API contract compliance testing
- Error condition and edge case handling
- JPL coding standard compliance verification (including FreeRTOS delay usage)

#### QA002: Integration Testing  
- Device-to-device pairing and communication
- Mobile app integration and control
- Power management and sleep/wake cycles
- Safety-critical timing validation at multiple cycle times (500ms, 1000ms, 2000ms)
- Haptic effect timing within half-cycle windows

#### QA003: User Acceptance Testing
- Therapist workflow validation
- Patient comfort and usability assessment
- Real-world session reliability testing
- Cycle time adjustment usability (0.5-2 Hz range)

#### QA004: Safety-Critical System Testing
- **TWDT verification**: Intentional task hang testing with oscilloscope timing
- **Dead time validation**: Verify 1ms FreeRTOS delays at end of each half-cycle
- **Packet loss testing**: BLE interference testing with spectrum analyzer
- **Recovery validation**: Automatic recovery from all identified failure modes
- **Timing precision**: Hardware verification of ±10ms bilateral timing under all cycle times
- **Shoot-through testing**: Verify no simultaneous high signals on GPIO19/GPIO20

#### QA005: Case Material Light Transmission Testing
- **Test sample verification**: All case materials tested with LED hardware before production
- **Transmission documentation**: Light transmission characteristics recorded for each material/color combination
- **Builder guidance**: Material test results included in open-source build documentation
- **Quality control**: Case material batches verified for consistent light transmission behavior

---

## Future Enhancements: Phase 2 Haptic Driver Evolution

### Phase Transition Strategy

#### FE001: Phase 1 Completion Criteria

**Hardware Readiness Requirements:**
- **Final PCB revision**: Complete Phase 1 hardware fixes before Phase 2 transition
  - Hardware button moved from GPIO18 (with jumper) to GPIO1 (direct connection)
  - GPIO20 relocated to GPIO18 to resolve GPIO19/GPIO20 hardware crosstalk issue
  - ESP32-C6 documented GPIO19↔GPIO20 coupling during boot requires hardware remapping
  - All Phase 1 discrete MOSFET H-bridge circuits validated and production-ready
- **Software validation**: Core bilateral timing and BLE communication proven reliable
  - ±10ms bilateral timing precision verified across all cycle times (500-2000ms)
  - BLE packet loss detection and recovery validated with real-world testing
  - Emergency shutdown and safety-critical features tested by end users
  - Task watchdog timer adaptive feeding proven stable over extended sessions

**Production Readiness Checklist:**
- [ ] Phase 1 hardware revision assembled and tested (button on GPIO1, H-bridge on GPIO19/GPIO18)
- [ ] Bilateral timing validated by therapists in real EMDR sessions
- [ ] BLE connection stability meets 99% uptime requirement over 20+ devices
- [ ] Battery life validated for 20+ minute therapeutic sessions
- [ ] Documentation complete for Phase 1 assembly and operation

**Branch Strategy:**
- **Phase 2 as main development branch**: Phase 2 haptic driver research becomes the primary development path
- **Phase 1 maintenance branch**: Phase 1 discrete MOSFET hardware supported via build flags
- **Firmware compatibility**: Single codebase supports both Phase 1 and Phase 2 hardware

#### FE002: Phase 2 Research Goals and Priorities

**Primary Research Goal: Therapeutic Effectiveness**
- **End-user validation**: Make production-ready devices for real therapists to evaluate
- **Comparative evaluation**: Therapists assess ERM vs LRA haptic feel during actual EMDR sessions
- **Not laboratory research**: Project scope is device preparation, not therapeutic outcome studies
- **Field testing deliverable**: Complete working kits ready for professional therapeutic use

**Priority Hierarchy:**
1. **Therapeutic effectiveness** (PRIMARY): Which haptic technology feels best to patients and therapists?
2. **Battery life** (VERY CLOSE SECOND): Power consumption directly impacts session length and device usability
3. **Cost-effectiveness**: Component cost vs therapeutic benefit trade-off analysis
4. **Reliability**: MTBF, failure modes, and long-term durability assessment
5. **Frequency response**: Which actuator types work optimally at 0.5-2 Hz bilateral rates?

**Established Technology Baseline:**
- **ERM dominance in EMDR devices**: Existing commercial EMDR devices use ERM motors
- **Maintain ERM option**: Phase 2 must preserve ERM capability while exploring newer technologies
- **Technology diversification**: Explore LRA and piezo without abandoning proven ERM baseline

**Patent Risk Mitigation Strategy:**
- **No novel inventions**: All Phase 2 technology combinations use established, off-the-shelf components
- **Defensive publication**: Open-source release creates prior art protection
- **Technology mix assessment**: Rapid identification if specific combinations attract patent concerns
- **Alternative paths ready**: Multiple haptic driver IC options preserve project flexibility

### Hardware Architecture: Phase 2 Evolution

#### FE003: Haptic Driver IC Selection and Rationale

**Texas Instruments DRV260x Family Evaluation:**

**Primary Candidates:**

**DRV2605L** (I2C control, waveform library included):
- **I2C interface**: Saves GPIO if dual haptic drivers needed on single PCB
- **128-effect waveform library**: Preloaded haptic patterns (not needed for EMDR, but included)
- **ERM and LRA support**: Single IC handles both actuator types
- **Click compensation**: LRA braking reduces residual vibration
- **Supply voltage**: 2.5-5.2V (compatible with 3.3V system)
- **Current capability**: 250mA peak (adequate for small ERM/LRA)
- **Cost consideration**: More expensive due to included waveform library

**DRV2605** (I2C control, no waveform library):
- **I2C interface**: GPIO conservation for potential dual-driver designs
- **No waveform library**: Lower cost, simpler IC
- **ERM and LRA support**: Full actuator type flexibility
- **Direct PWM control**: Open-loop drive suitable for bilateral timing
- **Supply voltage**: 2.5-5.2V system compatibility
- **Cost advantage**: Library removal reduces component cost

**DRV2625** (I2C control, improved LRA performance):
- **Enhanced LRA drive**: Optimized for modern LRA actuators
- **I2C interface**: Consistent with DRV2605 family
- **Auto-resonance tracking**: LRA efficiency optimization (may not be critical for 0.5-2 Hz)
- **ERM support**: Maintains backward compatibility
- **Newer generation**: Potential performance improvements over DRV2605L

**DRV2604/DRV2624** (No I2C, direct PWM control):
- **No I2C interface**: GPIO direct control (IN/IN style similar to Phase 1)
- **No waveform library**: Lowest cost option
- **Simple integration**: Minimal firmware complexity
- **GPIO availability**: May limit dual-driver PCB designs
- **Cost-optimized**: Best price-per-channel for single-driver boards

**Decision Criteria:**
- **I2C preference for GPIO conservation**: If dual drivers on PCB, I2C saves GPIOs
- **Waveform library not critical**: EMDR bilateral timing doesn't need preloaded haptic patterns
- **Cost vs features**: Evaluate if I2C justifies additional cost over direct PWM control
- **Thermal management**: DRV260x family provides better heat dissipation than discrete MOSFETs

**IC Selection Not Finalized**: Hardware exploration phase will determine optimal DRV260x variant

#### FE004: Haptic Actuator Technology Research Matrix

**Eccentric Rotating Mass (ERM) Motors:**

**Advantages:**
- **Established in EMDR field**: Commercial EMDR devices use ERM technology
- **Therapist familiarity**: Practitioners know ERM haptic characteristics
- **Phase 1 baseline**: Direct comparison possible with discrete MOSFET implementation
- **Frequency range**: Works at 0.5-2 Hz bilateral stimulation rates
- **Cost-effective**: Readily available, low-cost components

**Disadvantages:**
- **Power consumption**: 90mA typical, 120mA stall (battery life limitation)
- **Intensity control only**: Cannot modulate frequency characteristics
- **Mechanical wear**: Moving parts reduce MTBF vs solid-state alternatives
- **Spin-up latency**: 50-100ms ramp time affects haptic precision

**Phase 2 ERM Implementation:**
- DRV260x family direct ERM drive mode
- Preserve Phase 1 intensity control (0-100% PWM equivalent)
- Hardware comparison: DRV260x efficiency vs Phase 1 discrete MOSFETs

**Linear Resonant Actuators (LRA):**

**Advantages:**
- **Power efficiency**: 40-60% lower current consumption vs ERM (potential 60mA typical vs 90mA ERM)
- **Frequency + intensity control**: Both parameters adjustable for therapeutic feel exploration
- **Faster response**: <20ms ramp time vs 50-100ms ERM (improved bilateral timing precision)
- **Longer lifespan**: No rotating bearings, reduced mechanical wear
- **Crisp haptic feel**: Sharp attack/decay characteristics (may improve therapeutic perception)

**Disadvantages:**
- **Resonant frequency dependency**: LRA optimized for specific frequency (~150-250Hz carrier)
- **0.5-2 Hz bilateral timing**: Must modulate LRA carrier for slow bilateral rates
- **Unknown therapeutic feel**: EMDR therapists unfamiliar with LRA haptics
- **Cost premium**: LRA actuators 2-3× more expensive than equivalent ERM

**Phase 2 LRA Research Questions:**
- Does 40-60% power savings justify cost premium for 20+ minute sessions?
- Can DRV260x LRA auto-resonance tracking improve bilateral timing precision?
- Do therapists/patients prefer LRA "crisp" feel vs ERM "smooth" feel?
- Does faster LRA response improve therapeutic bilateral alternation perception?

**Piezoelectric Actuators:**

**Advantages:**
- **Frequency + intensity control**: Full parameter space for therapeutic haptic exploration
- **Solid-state reliability**: No moving parts, longest MTBF potential
- **Immediate response**: <1ms actuation time (far exceeds bilateral timing requirements)
- **High precision**: Exact amplitude control for research-grade therapeutic tuning

**Disadvantages:**
- **High-voltage drive**: 50-200V DC-DC boost required (circuit complexity)
- **4-layer PCB requirement**: High-voltage separation rules (pollution level 2)
  - Phase 2 targets 2-layer PCB for cost/manufacturing accessibility
  - 4-layer PCB increases manufacturing cost and complexity
- **Driver IC availability**: Must support internal boost converter for single-chip solution
- **EMI/Grounding complexity**: High-voltage switching requires careful PCB layout
- **Cost premium**: Piezo actuators + boost circuitry most expensive option

**Phase 2 Piezo Consideration:**
- **Conditional evaluation**: Only if driver IC with integrated boost converter identified
- **Must support overdrive**: Therapeutic feel exploration requires variable drive voltage
- **PCB layer count**: 4-layer requirement may defer piezo to future phase
- **Alternative research path**: If DRV260x family has piezo-compatible variant with integrated boost

**Internal Boost Converter Requirement:**
- Simplifies PCB design (no external boost converter)
- Maintains 2-layer PCB feasibility
- Single-IC solution preserves open-source accessibility

**Overdrive Capability:**
- Variable drive voltage enables different haptic intensity characteristics
- Therapeutic feel research requires amplitude tunability
- Standard piezo drive may not explore full haptic parameter space

#### FE005: GPIO Architecture and Firmware Compatibility

**Phase 1 → Phase 2 GPIO Migration:**

**Phase 1 Final GPIO Assignment** (discrete MOSFET H-bridge):
```
GPIO0:  Back-EMF sensing (ADC1_CH0, OUTA from H-bridge)
GPIO1:  Button input (direct connection, no jumper, RTC wake)
GPIO2:  Battery voltage monitor (ADC1_CH2, resistor divider)
GPIO15: Status LED (on-board, active LOW)
GPIO16: Therapy light enable (P-MOSFET, active LOW)
GPIO17: Therapy light output (WS2812B DIN or simple LED)
GPIO18: H-bridge IN2 (moved from GPIO20 due to crosstalk)
GPIO19: H-bridge IN1 (forward control)
GPIO21: Battery monitor enable (P-MOSFET gate control)
```

**Phase 2 GPIO Options** (DRV260x haptic driver):

**Option A: Preserve IN/IN Direct Control** (DRV2604/DRV2624 style)
```
GPIO18: Haptic driver IN1 (forward/ERM or LRA drive)
GPIO19: Haptic driver IN2 (reverse/brake control)
- Maintains Phase 1 GPIO allocation familiarity
- No I2C overhead for simple single-driver designs
- Direct hardware compatibility with Phase 1 firmware patterns
```

**Option B: I2C Control** (DRV2605L/DRV2605/DRV2625)
```
GPIO6:  I2C SDA (standard ESP32-C6 I2C pins)
GPIO7:  I2C SCL
GPIO18: Haptic driver 1 enable (if dual drivers)
GPIO19: Haptic driver 2 enable (if dual drivers)
- Saves GPIOs for potential dual-driver PCB
- Enables advanced DRV260x features (waveform library, auto-resonance)
- Requires firmware I2C driver implementation
```

**Option C: Hybrid Approach**
- Primary haptic driver: I2C control (full feature access)
- Secondary/backup: Direct GPIO control (Phase 1 compatibility fallback)
- Maximum flexibility for comparative research

**GPIO Allocation Decision:**
- **Not finalized**: Hardware exploration will determine optimal control method
- **Firmware hooks**: Phase 1 code structured to support both direct GPIO and I2C control
- **Build flags**: Compile-time selection preserves single codebase for both phases

**Dual Haptic Driver Consideration:**
- **PCB size constraint**: Must fit Phase 1 case (or close variant)
- **dual 350mAh batteries (700mAh)**: Power budget for two haptic drivers requires careful analysis
- **Bilateral independence**: Could each device have ERM + LRA for A/B comparison?
- **GPIO availability**: I2C control frees GPIOs for dual-driver PCB designs
- **Research value**: Side-by-side ERM/LRA comparison within single device

#### FE006: Firmware Architecture for Phase 1/Phase 2 Compatibility

**Build Flag Strategy:**

```c
// Phase selection at compile time
#ifdef HARDWARE_PHASE_1
    // Discrete MOSFET H-bridge control
    // GPIO direct control: GPIO18 (IN2), GPIO19 (IN1)
    // All Phase 1 safety features and bilateral timing logic
#endif

#ifdef HARDWARE_PHASE_2
    // DRV260x haptic driver control
    // I2C or direct GPIO (TBD based on IC selection)
    // Enhanced haptic features (ERM/LRA/piezo support)
#endif

// Common bilateral timing and BLE coordination code
// Phase-agnostic safety-critical functions
// Shared NVS, button, and power management logic
```

**Abstraction Layer Design:**

**Motor Control HAL** (Hardware Abstraction Layer):
```c
esp_err_t motor_set_intensity(uint8_t intensity_percent);
esp_err_t motor_set_direction(motor_direction_t direction);
esp_err_t motor_execute_half_cycle(motor_direction_t dir, 
                                    uint8_t intensity, 
                                    uint32_t half_cycle_ms);

// Phase 1 implementation: Direct GPIO control + PWM
// Phase 2 implementation: DRV260x I2C commands or GPIO control
// Application code remains unchanged
```

**Haptic Driver Backend Selection:**
- Compile-time selection via build flags
- Runtime detection not required (hardware version known)
- Single API surface for bilateral timing coordination
- Phase-specific features exposed through common interface

**Firmware Compatibility Benefits:**
- **Bilateral timing logic**: Unchanged between phases (safety-critical code stability)
- **BLE coordination**: Phase-agnostic (device-to-device communication preserved)
- **Button/power management**: Common implementation (user experience consistency)
- **Testing efficiency**: Core logic validated once, applies to both hardware variants

**PlatformIO Build Environments:**
```ini
[env:xiao_esp32c6_phase1]
build_flags = 
    ${env:base.build_flags}
    -DHARDWARE_PHASE_1
    -DMOTOR_DISCRETE_MOSFET

[env:xiao_esp32c6_phase2_erm]
build_flags = 
    ${env:base.build_flags}
    -DHARDWARE_PHASE_2
    -DMOTOR_DRV260X
    -DACTUATOR_TYPE_ERM

[env:xiao_esp32c6_phase2_lra]
build_flags = 
    ${env:base.build_flags}
    -DHARDWARE_PHASE_2
    -DMOTOR_DRV260X
    -DACTUATOR_TYPE_LRA
```

### Power and Physical Constraints: Phase 2

#### FE007: Battery and Power Budget Analysis

**Fixed Power Constraints:**
- **Battery capacity**: Pair of (2) 350mAh per device (case form factor constraint)
- **Target session duration**: 20+ minutes bilateral stimulation (unchanged from Phase 1)
- **USB-C charging**: 100mA @ 5V via Seeed XIAO ESP32-C6 battery management IC (hardware limitation)

**Phase 1 Power Baseline:**
- **ERM motor**: 90mA typical, 120mA stall current
- **ESP32-C6 active**: ~50mA with BLE + bilateral timing tasks
- **Total consumption**: ~140-170mA during active bilateral stimulation
- **20-minute session**: ~47-57mAh consumed (13-16% of battery capacity)

**Phase 2 Power Targets:**

**ERM with DRV260x Driver:**
- **Motor current**: 90mA typical (same as Phase 1)
- **DRV260x efficiency**: 95%+ driver efficiency (vs ~85% discrete MOSFET)
- **Expected savings**: 5-10mA reduction from improved driver efficiency
- **Thermal improvement**: Better heat dissipation vs discrete components

**LRA with DRV260x Driver:**
- **Motor current**: 40-60mA typical (40-60% reduction vs ERM)
- **Battery life improvement**: 25-35mAh savings per 20-minute session
- **Session extension**: Potential 30+ minute sessions with same battery
- **Standby efficiency**: LRA lower idle current vs ERM cogging torque

**Dual Driver Power Consideration:**
- **Worst case**: Both haptic drivers active (research/comparison mode)
- **ERM + LRA**: 90mA + 60mA = 150mA haptic power
- **ESP32-C6**: 50mA system overhead
- **Total**: 200mA peak (57% higher than Phase 1 single driver)
- **Battery impact**: Reduced session duration or requires power management strategy

**Power Management Strategy:**
- **Single driver default**: Normal operation uses one haptic driver
- **Comparison mode**: Brief A/B testing with both drivers (therapist-initiated)
- **Sequential activation**: Never both drivers simultaneously unless research mode enabled
- **Battery monitoring**: Low battery warning if dual-driver mode risks session completion

#### FE008: PCB Form Factor and Case Compatibility

**Phase 1 Case as Reference Design:**
- **Current case dimensions**: Designed for discrete MOSFET Phase 1 PCB
- **dual 350mAh batteries (700mAh) fitment**: Case sized for specific battery form factor
- **Seeed XIAO ESP32-C6**: Form factor assumes specific module dimensions

**Phase 2 PCB Design Goals:**
- **Maintain Phase 1 case compatibility**: Preferred but not mandatory
- **Component height**: DRV260x IC height vs discrete MOSFET component height comparison needed
- **Thermal management**: DRV260x may require different heat sinking vs Phase 1
- **PCB area**: I2C control may enable more compact layout (fewer GPIO traces)

**Case Compatibility Trade-offs:**

**Priority 1: Maintain battery compatibility**
- dual 350mAh batteries (700mAh) form factor non-negotiable (power budget established)
- Case must accommodate same battery regardless of PCB changes

**Priority 2: Preserve therapy light window** (if case has light transmission)
- GPIO17 therapy light feature maintained in Phase 2
- Case light transmission characteristics apply to both phases

**Priority 3: PCB mounting compatibility**
- Attempt to preserve Phase 1 PCB mounting hole pattern
- May require minor case modification if DRV260x necessitates different layout

**Acceptable Case Modifications:**
- **Component clearance**: Small case revisions for DRV260x IC height differences
- **Thermal venting**: Additional airflow if DRV260x requires better heat dissipation
- **PCB size adjustment**: Slight dimension changes if dual-driver research board larger

**Open-Source Case Variants:**
- Phase 1 case design (discrete MOSFET hardware)
- Phase 2 case design (DRV260x haptic driver, if modifications needed)
- Community can choose hardware phase based on case manufacturing capability

### Phase 2 Research Methodology

#### FE009: Comparative Haptic Technology Study Design

**Study Objective:**
Enable EMDR therapists to evaluate ERM vs LRA haptic technologies in real therapeutic sessions and provide subjective feedback on patient comfort, therapeutic effectiveness, and device usability.

**Study Scope:**
- **Not laboratory research**: This project prepares devices for field testing, not therapeutic outcome studies
- **Therapist evaluation**: Professional practitioners assess haptic feel during actual EMDR sessions
- **Patient comfort**: Subjective feedback on haptic intensity, frequency, and overall comfort
- **Device usability**: Therapist workflow integration and device reliability assessment

**Research Variables:**

**Independent Variables (Controlled):**
1. **Actuator type**: ERM vs LRA (within-device or between-device comparison)
2. **Intensity levels**: 25%, 50%, 75%, 100% haptic drive
3. **Bilateral timing**: 500ms, 1000ms, 2000ms total cycles (0.5-2 Hz)
4. **Session duration**: Standard 20-minute EMDR sessions

**Dependent Variables (Measured):**
1. **Battery consumption**: mAh per 20-minute session (hardware measured)
2. **Therapist preference**: Subjective rating of haptic feel quality
3. **Patient comfort**: Post-session survey on haptic intensity and feel
4. **Device reliability**: Connection stability, timing precision, error rates
5. **Thermal performance**: PCB and actuator temperature during extended sessions

**Comparison Matrix:**

**Single Device Study** (2×2 within-subjects design):
- **Factor A**: Bilateral frequency (0.5 Hz vs 1 Hz)
- **Factor B**: Haptic intensity (25% vs 50%)
- **Measure**: Battery mAh consumption, therapist preference, patient comfort
- **Devices**: Phase 2 hardware with selectable ERM/LRA mode

**Dual Technology Comparison** (between-device design):
- **Device Set 1**: Phase 2 ERM actuators (both devices)
- **Device Set 2**: Phase 2 LRA actuators (both devices)
- **Measure**: Side-by-side therapist evaluation of haptic feel quality
- **Counterbalancing**: Randomize ERM/LRA order across therapy sessions

**Data Collection Methods:**
- **Automated logging**: ESP32-C6 records battery consumption, BLE stability, timing precision
- **Therapist surveys**: Post-session subjective ratings (5-point Likert scale)
- **Patient comfort**: Brief post-session survey on haptic feel acceptability
- **Device telemetry**: NVS stores session statistics for download/analysis

**Study Deliverables:**
- **Complete device kits**: Phase 2 hardware ready for therapist field testing
- **Data collection firmware**: Automated logging of power, timing, reliability metrics
- **Survey instruments**: Standardized therapist and patient feedback forms
- **Assembly documentation**: Open-source build guides for Phase 2 hardware

**Ethical Considerations:**
- **Therapist discretion**: Professional practitioners decide device appropriateness for specific patients
- **Informed consent**: Patients aware devices are research prototypes
- **No therapeutic claims**: Devices provided for professional evaluation, not patient treatment claims
- **Data privacy**: Patient identifiers not collected, only aggregate haptic preference data

#### FE010: Phase 2 Success Criteria and Timeline

**Hardware Validation Milestones:**

**Milestone 1: DRV260x IC Selection and Testing** (2-4 weeks)
- [ ] Evaluate DRV2605L, DRV2605, DRV2625, DRV2604/2624 datasheets
- [ ] Breadboard testing with ERM and LRA actuators
- [ ] Power consumption measurements vs Phase 1 baseline
- [ ] I2C vs direct GPIO control trade-off analysis
- [ ] Thermal performance characterization

**Milestone 2: Phase 2 PCB Design** (4-6 weeks)
- [ ] Schematic capture with selected DRV260x IC
- [ ] PCB layout targeting Phase 1 case compatibility
- [ ] Thermal simulation for DRV260x heat dissipation
- [ ] Dual-driver PCB variant design (if research warrants)
- [ ] Gerber file generation and PCB manufacturer selection

**Milestone 3: Phase 2 Prototype Assembly and Testing** (2-3 weeks)
- [ ] PCB assembly with DRV260x IC and ERM actuators
- [ ] PCB assembly with DRV260x IC and LRA actuators
- [ ] Firmware HAL implementation for Phase 2 hardware
- [ ] Bilateral timing precision validation (±10ms requirement)
- [ ] 20-minute battery life testing with dual 350mAh batteries (700mAh)

**Milestone 4: Comparative Testing** (4-6 weeks)
- [ ] Side-by-side ERM vs LRA haptic feel evaluation
- [ ] Battery consumption comparison across intensity levels
- [ ] Thermal performance during extended sessions
- [ ] BLE connection stability with Phase 2 hardware
- [ ] Therapist feedback on haptic quality (if accessible)

**Software Validation Milestones:**

**Milestone 5: Firmware Compatibility Implementation** (2-3 weeks)
- [ ] Motor control HAL with Phase 1/Phase 2 backends
- [ ] Build flag strategy for hardware variant selection
- [ ] I2C driver implementation (if DRV260x I2C variant selected)
- [ ] Preserve all Phase 1 safety-critical timing logic
- [ ] NVS schema extension for haptic technology type

**Milestone 6: Regression Testing** (1-2 weeks)
- [ ] Phase 1 hardware testing with unified firmware
- [ ] Phase 2 hardware testing with unified firmware
- [ ] Bilateral timing precision validation for both phases
- [ ] Emergency shutdown and safety features across hardware variants
- [ ] JPL coding standard compliance verification

**Documentation and Open-Source Release:**

**Milestone 7: Phase 2 Documentation** (2-3 weeks)
- [ ] Phase 2 hardware assembly guide (ERM and LRA variants)
- [ ] DRV260x IC selection rationale document
- [ ] Power consumption comparison report
- [ ] Thermal management guidelines
- [ ] Firmware build configuration guide

**Milestone 8: Research Study Preparation** (1-2 weeks)
- [ ] Therapist evaluation protocol documentation
- [ ] Data collection firmware features
- [ ] Survey instruments for haptic preference
- [ ] Device kit assembly and testing procedures

**Total Estimated Timeline: 16-25 weeks** (4-6 months)

**Phase 2 Success Criteria:**

**Technical Success:**
- ✅ DRV260x haptic driver demonstrates equal or better bilateral timing precision vs Phase 1
- ✅ LRA actuators show 40-60% power consumption reduction vs ERM baseline
- ✅ 20+ minute session duration maintained with dual 350mAh batteries (700mAh) (both ERM and LRA)
- ✅ Thermal performance within acceptable limits (no overheating during extended sessions)
- ✅ Single firmware codebase supports Phase 1 and Phase 2 hardware variants

**Research Success:**
- ✅ Therapist-ready device kits assembled and tested
- ✅ Automated data collection firmware operational
- ✅ Power consumption data collected for ERM vs LRA comparison
- ✅ Subjective haptic preference feedback mechanism validated
- ✅ Open-source documentation enables community replication

**Patent Risk Assessment:**
- ✅ No obvious novel inventions identified in Phase 2 technology combinations
- ✅ All components are off-the-shelf, commercially available ICs and actuators
- ✅ Open-source release provides prior art protection
- ✅ Alternative haptic driver IC options identified if concerns arise

### Phase 2 Risk Mitigation

#### FE011: Technical Risks and Mitigation Strategies

**Risk 1: DRV260x IC incompatibility with bilateral timing requirements**
- **Likelihood**: Low (DRV260x designed for haptic applications)
- **Impact**: High (would require alternative haptic driver IC)
- **Mitigation**: Early breadboard testing validates bilateral timing precision before PCB design
- **Fallback**: Revert to Phase 1 discrete MOSFET design if DRV260x unsuitable

**Risk 2: LRA actuators unsuitable for 0.5-2 Hz bilateral rates**
- **Likelihood**: Medium (LRA optimized for high-frequency resonance ~150-250Hz)
- **Impact**: Medium (ERM remains viable, LRA research path abandoned)
- **Mitigation**: Breadboard testing at bilateral frequencies before committing to LRA PCB variant
- **Fallback**: Phase 2 proceeds with ERM-only focus if LRA incompatible

**Risk 3: Phase 2 PCB incompatible with Phase 1 case dimensions**
- **Likelihood**: Medium (DRV260x IC size and layout may differ from discrete MOSFETs)
- **Impact**: Low (case redesign acceptable, part of open-source hardware evolution)
- **Mitigation**: Prioritize component height and battery clearance in PCB layout
- **Fallback**: Publish Phase 2 case variant as separate open-source design

**Risk 4: Insufficient battery capacity for dual-driver research mode**
- **Likelihood**: High (dual drivers exceed dual 350mAh batteries (700mAh) budget)
- **Impact**: Low (dual-driver mode remains research-only, not production requirement)
- **Mitigation**: Power management limits dual-driver operation to brief comparison testing
- **Fallback**: Dual-driver PCB variant abandoned, focus on single-driver comparison

**Risk 5: Piezo actuators require 4-layer PCB (Phase 2 targets 2-layer)**
- **Likelihood**: High (50-200V boost converter requires careful PCB layout)
- **Impact**: Medium (piezo research deferred to future phase)
- **Mitigation**: Conditional piezo evaluation only if driver IC with integrated boost identified
- **Fallback**: Phase 2 proceeds with ERM/LRA comparison, piezo deferred

#### FE012: Open-Source Community Engagement Strategy

**Phase 2 Hardware Variants for Community:**

**Variant 1: Phase 2 ERM** (direct Phase 1 upgrade path)
- **Target audience**: Existing Phase 1 builders seeking improved efficiency
- **Hardware**: DRV260x with ERM actuators
- **Benefits**: 5-10mA power savings, better thermal management
- **Build complexity**: Similar to Phase 1 (2-layer PCB, through-hole components where possible)

**Variant 2: Phase 2 LRA** (advanced builder, battery life priority)
- **Target audience**: Builders prioritizing battery life and session duration
- **Hardware**: DRV260x with LRA actuators
- **Benefits**: 40-60% power reduction, 30+ minute sessions
- **Build complexity**: Slightly higher (LRA sourcing, tuning may be required)

**Variant 3: Phase 2 Dual-Driver** (research/comparison, advanced builder)
- **Target audience**: Researchers wanting side-by-side ERM/LRA comparison
- **Hardware**: Two DRV260x ICs, both ERM and LRA actuators
- **Benefits**: Within-device A/B testing, maximum research flexibility
- **Build complexity**: Highest (dual I2C addressing, power management, larger PCB)

**Community Documentation Deliverables:**
- **Hardware selection guide**: Decision tree for ERM vs LRA vs dual-driver variants
- **BOM cost comparison**: Component costs for each Phase 2 variant
- **Assembly difficulty ratings**: Beginner/intermediate/advanced builder classifications
- **Firmware build guide**: PlatformIO environment selection for each hardware variant
- **Troubleshooting guides**: Common Phase 2 hardware issues and solutions

**Open-Source Hardware Release:**
- **KiCad project files**: Schematics, PCB layouts for all Phase 2 variants
- **Gerber files**: Ready-to-manufacture PCB files
- **BOM with supplier links**: DigiKey, Mouser, LCSC part numbers
- **3D case models**: STL/STEP files for Phase 2 case (if modified from Phase 1)
- **Assembly photos**: High-resolution build documentation

---

**This Phase 2 Future Enhancements section outlines the research-driven evolution toward dedicated haptic driver ICs with ERM/LRA comparative evaluation, maintaining open-source accessibility while exploring power-efficient alternatives for extended therapeutic sessions. Phase 2 preserves all Phase 1 safety-critical bilateral timing and BLE coordination logic while enabling therapist-driven haptic technology assessment.**

---

**This requirements specification provides the complete functional and technical foundation for the EMDR bilateral stimulation device project, ensuring all stakeholder needs are addressed while maintaining the highest standards for safety-critical medical device development.**

**October 21, 2025 Update**: CP005 revised to reflect hardware testing reality that light transmission is a spectrum dependent on material, color, and print parameters rather than binary opaque/translucent categorization.

**October 31, 2025 Update**: Phase 2 Future Enhancements section added, documenting transition to DRV260x haptic driver family with ERM/LRA comparative research strategy and firmware compatibility architecture.
