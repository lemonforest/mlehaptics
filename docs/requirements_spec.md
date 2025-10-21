# EMDR Bilateral Stimulation Device - Requirements Specification

**Generated with assistance from Claude Sonnet 4 (Anthropic)**  
**Last Updated: 2025-10-20**

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
- **Factory reset**: 10-second button hold during first 30 seconds clears all data

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
- **Implementation**: GPIO23 with dual LED footprint (simple LED or WS2812B)
- **Case dependency**: Only functional with translucent case materials
- **Priority**: Secondary to motor-based bilateral stimulation
- **Control**: Therapist-configurable via mobile app (enable/disable/intensity)
- **Research value**: Unknown therapeutic benefit - requires field testing with EMDR practitioners
- **Build variants**: Opaque cases (motor-only) vs translucent cases (motor + light)

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
- **Therapy Light Enable**: GPIO16, P-MOSFET driver for therapy LED power control
- **Therapy Light Output**: GPIO17/GPIO23 dual-use LED/WS2812B with overlapping footprint design
- **Motor Control**: GPIO19 (H-bridge IN1 forward), GPIO20 (H-bridge IN2 reverse) for bidirectional motor control
  - **Case dependency**: Only functional with translucent case materials
  - **Standard translucent**: Simple LED for basic therapy light research
  - **Premium translucent**: WS2812B LED for color therapy research
  - **Opaque cases**: GPIO17/GPIO23 unused (motor-only bilateral stimulation)

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
- **Factory Reset**: 10-second hold during first 30 seconds after boot

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
- Factory reset and system controls

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
- **Dual case manufacturing options**: Both opaque and translucent case models available as open STL files
- **User choice**: Builders select case style based on desired features and material cost constraints
- **Documentation**: Complete assembly instructions and bill of materials for both variants

#### CP005: Case Material Options and Research

**Opaque Case Builds** (Cost-effective option):
- **Materials**: Standard 3D printing materials (PLA, ABS, standard nylon)
- **Features**: Motor-only bilateral stimulation, GPIO23 unused
- **Cost**: Low-cost materials, widely available
- **Use case**: Core EMDR therapy functionality

**Translucent Case Builds** (Research/premium option):
- **Primary materials**: 
  - **Clear resin**: SLA/DLP printing, excellent light transmission
  - **Translucent PETG**: FDM-compatible, good light diffusion, easier printing than clear resin
- **Alternative materials for research**:
  - **Translucent TPU**: Flexible option, interesting light diffusion properties
  - **Translucent PLA/PETG variants**: Various manufacturers offer translucent filaments
- **Advanced options**:
  - **Multi-material printing**: Opaque base structure with translucent window inserts
  - **Dual-material SLS**: Investigate translucent nylon windows in opaque nylon housing
- **Features**: Motor + therapy light bilateral stimulation
- **Cost**: Higher material costs, specialized printing requirements
- **Use case**: Visual bilateral stimulation research, premium therapeutic options

**Material Research Recommendations**:
- **PETG investigation**: Test various translucent PETG brands for optimal light transmission and diffusion
- **Multi-material feasibility**: Research dual-material printing techniques for cost-effective translucent windows
- **Light diffusion optimization**: Test different translucent materials for therapeutic light quality
- **Durability testing**: Validate translucent material durability for medical device handling

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

---

**This requirements specification provides the complete functional and technical foundation for the EMDR bilateral stimulation device project, ensuring all stakeholder needs are addressed while maintaining the highest standards for safety-critical medical device development.**
