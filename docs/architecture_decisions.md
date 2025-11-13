# Architecture Decisions (AD Format)

**Version:** v0.1.0
**Last Updated:** 2025-11-13
**Status:** Living Document
**Total Decisions:** AD001-AD034

**Preliminary Design Review Document**
**Generated with assistance from Claude Sonnet 4 (Anthropic)**

## Executive Summary

This document captures the technical architecture decisions and engineering rationale for the EMDR bilateral stimulation device project. The system implements safety-critical medical device software following JPL Institutional Coding Standards using ESP-IDF v5.5.0 for enhanced reliability and therapeutic effectiveness.

**⚠️ CRITICAL BUILD SYSTEM CONSTRAINT ⚠️**

**ESP-IDF uses CMake - PlatformIO's `build_src_filter` DOES NOT WORK!**

ESP-IDF framework delegates all compilation to CMake, which reads `src/CMakeLists.txt` directly. PlatformIO's `build_src_filter` option has **NO EFFECT** with ESP-IDF. Source file selection MUST be done via:
- Python pre-build scripts that modify `src/CMakeLists.txt` (see AD022)
- Direct CMakeLists.txt editing is NOT recommended (breaks automation)

See **AD022: ESP-IDF Build System and Hardware Test Architecture** for full details.

---

## Development Platform and Framework Decisions

### AD001: ESP-IDF v5.5.0 Framework Selection

**Decision**: Use ESP-IDF v5.5.0 (latest stable, enhanced ESP32-C6 support)

**Rationale:**
- **Enhanced ESP32-C6 support**: Improved ULP RISC-V coprocessor support for battery-efficient bilateral timing
- **BR/EDR improvements**: Enhanced (e)SCO + Wi-Fi coexistence for future Bluetooth Classic features
- **MQTT 5.0 support**: Full protocol support for future IoT features
- **Platform compatibility**: Official PlatformIO espressif32 v6.12.0 support with auto-selection
- **Proven stability**: Hundreds of bug fixes from v5.3.0, extensive field deployment
- **Official board support**: Seeed XIAO ESP32-C6 officially supported since platform v6.11.0
- **Real-time guarantees**: Mature FreeRTOS integration for safety-critical timing
- **Memory management**: Stable heap and stack analysis tools for JPL compliance

**Successful Migration (October 20, 2025):**
- Fresh PlatformIO install resolved interface version conflicts
- Platform v6.12.0 automatically selects ESP-IDF v5.5.0 (no platform_packages needed)
- Build verified successful: 610 seconds first build, ~60 seconds incremental
- RAM usage: 3.1% (10,148 bytes), Flash usage: 4.1% (168,667 bytes)
- Menuconfig minimal save resolved v5.3.0 → v5.5.0 config conflicts

**Alternatives Considered:**
- **Arduino framework**: Rejected due to limited real-time capabilities and abstraction overhead
- **ESP-IDF v5.3.0**: Superseded by v5.5.0 with significant improvements
- **ESP-IDF v5.4.x**: Skipped - v5.5.0 available with better ESP32-C6 support
- **Native ESP-IDF build**: Rejected to maintain PlatformIO toolchain compatibility
- **Seeed custom platform**: Rejected in favor of official PlatformIO platform

**Implementation Requirements:**
- All code must use ESP-IDF v5.5.0 APIs exclusively
- No deprecated function calls from earlier versions
- Platform: `espressif32 @ 6.12.0` (auto-selects framework-espidf @ 3.50500.0)
- Board: `seeed_xiao_esp32c6` (official support, underscore in name)
- Static analysis tools must validate ESP-IDF v5.5.0 compatibility
- Fresh PlatformIO install required if migrating from v5.3.0

### AD002: JPL Institutional Coding Standard Adoption

**Decision**: Implement JPL Coding Standard for C Programming Language for all safety-critical code

**Rationale:**
- **Medical device safety**: Bilateral stimulation timing errors could affect therapeutic outcomes
- **Zero dynamic allocation**: Prevents memory leaks and heap fragmentation in long-running sessions
- **Predictable execution**: No recursion ensures deterministic stack usage
- **Error resilience**: Comprehensive error checking prevents silent failures
- **Regulatory compliance**: Demonstrates commitment to safety-critical software practices

**Key JPL Rules Applied:**
1. **No dynamic memory allocation** (malloc/calloc/realloc/free)
2. **No recursion** in any function
3. **Limited function complexity** (cyclomatic complexity ≤ 10)
4. **All functions return error codes** (esp_err_t)
5. **Single entry/exit points** for all functions
6. **Comprehensive parameter validation**
7. **No goto statements** except error cleanup
8. **All variables explicitly initialized**

**Verification Strategy:**
- Static analysis tools configured for JPL compliance
- Automated complexity analysis for all functions
- Stack usage analysis with defined limits
- Peer review checklist including JPL rule verification

### AD003: C Language Selection (No C++)

**Decision**: Use C language exclusively, no C++ features

**Rationale:**
- **JPL standard alignment**: JPL coding standard is C-specific
- **Predictable behavior**: C provides deterministic memory layout and execution
- **ESP-IDF compatibility**: Native ESP-IDF APIs are C-based
- **Code review simplicity**: Easier verification of safety-critical code
- **Real-time guarantees**: No hidden constructor/destructor overhead

**Implementation Guidelines:**
- All source files use `.c` extension
- Headers use `.h` extension with C guards
- No C++ keywords or features
- Explicit function prototypes for all APIs
- Static allocation for all data structures

## Hardware Architecture Decisions

### AD004: Seeed Xiao ESP32-C6 Platform Selection

**Decision**: Target Seeed Xiao ESP32-C6 as the hardware platform

**Rationale:**
- **RISC-V architecture**: Modern, open-source processor with excellent toolchain support
- **BLE 5.0+ capability**: Essential for reliable device-to-device communication
- **Ultra-compact form factor**: 21x17.5mm enables portable therapeutic devices
- **Power efficiency**: Advanced sleep modes for extended battery operation
- **Cost-effective**: Competitive pricing for dual-device therapy systems

**Technical Specifications:**
- **Processor**: RISC-V 160MHz with real-time performance
- **Memory**: 512KB SRAM, 4MB Flash (adequate for application + OTA)
- **Connectivity**: WiFi 6, BLE 5.0, Zigbee 3.0 (future expansion)
- **Power**: USB-C charging, battery connector, 3.3V/5V operation

### AD005: GPIO Assignment Strategy

**Decision**: Dedicated GPIO assignments for specific functions

**GPIO Allocation:**
- **GPIO0**: Back-EMF sense (OUTA from H-bridge, power-efficient motor stall detection via ADC)
- **GPIO1**: User button (via jumper from GPIO18, hardware debounced with 10k pull-up, RTC wake for deep sleep)
- **GPIO2**: Battery voltage monitor (resistor divider: VBAT→3.3kΩ→GPIO2→10kΩ→GND)
- **GPIO15**: Status LED (system state indication)
- **GPIO16**: Therapy LED Enable (P-MOSFET driver, **ACTIVE LOW** - LOW=enabled, HIGH=disabled)
- **GPIO17**: Therapy LED / WS2812B DIN (dual footprint, requires case with light transmission - see CP005 for material testing)
- **GPIO18**: User button (physical PCB location, jumpered to GPIO0, configured as high-impedance input)
- **GPIO19**: H-bridge IN2 (motor reverse control)
- **GPIO20**: H-bridge IN1 (motor forward control)
- **GPIO21**: Battery monitor enable (P-MOSFET gate driver control)

**Rationale:**
- **GPIO0**: Back-EMF monitoring provides power-efficient continuous stall detection (µA ADC input impedance vs mA resistor divider current)
- **GPIO1**: ISR-capable GPIO enables fastest emergency response; receives button signal via jumper from GPIO18
- **GPIO2**: Battery voltage for periodic battery level reporting only (not for continuous stall monitoring to minimize power consumption)
- **GPIO15**: On-board LED available for status indication (**ACTIVE LOW** - LED on when GPIO = 0)
- **GPIO18**: Original button location on PCB; jumper wire to GPIO1 enables ISR support without PCB rework; software configures as high-Z input
- **GPIO19/20**: High-current capable pins suitable for H-bridge PWM control
- **Power efficiency**: Back-EMF sensing allows continuous motor monitoring without the resistor divider power drain that would occur with frequent battery voltage measurements

**PWM Configuration Decision:**
- **Frequency**: 25kHz (above human hearing range, good for both LED and motor)
- **Resolution**: 13-bit LEDC (0-8191 range for smooth intensity control)
- **Fade capability**: Hardware fade support for smooth transitions

## Software Architecture Decisions

### AD006: Bilateral Cycle Time Architecture

**Decision**: Total cycle time as primary configuration parameter with FreeRTOS dead time

**Cycle Time Structure:**
- **User Configuration**: Total bilateral cycle time (500-2000ms)
- **Automatic Calculation**: Per-device half-cycle = total_cycle / 2
- **Therapeutic Range**: 0.5 Hz (2000ms) to 2 Hz (500ms) bilateral stimulation rate
- **Default**: 1000ms total cycle (1 Hz, the traditional EMDR bilateral rate)

**Timing Budget per Half-Cycle:**
```
Half-Cycle Window (example: 500ms for 1000ms total cycle):
├─ Motor Active: (half_cycle_ms - 1) = 499ms  [vTaskDelay]
├─ Motor Coast: Immediate GPIO write (~50ns)
├─ Dead Time: 1ms [vTaskDelay for watchdog feeding]
└─ Total: Exactly half_cycle_ms = 500ms
```

**Dead Time Implementation:**
```c
esp_err_t motor_execute_half_cycle(motor_direction_t direction,
                                    uint8_t intensity_percent, 
                                    uint32_t half_cycle_ms) {
    // Motor active period (JPL-compliant FreeRTOS delay)
    uint32_t motor_active_ms = half_cycle_ms - 1;  // Reserve 1ms for dead time
    motor_set_direction_intensity(direction, intensity_percent);
    vTaskDelay(pdMS_TO_TICKS(motor_active_ms));
    
    // Immediate coast (GPIO write ~50ns, provides hardware dead time)
    motor_set_direction_intensity(MOTOR_COAST, 0);
    
    // 1ms dead time + watchdog feeding (JPL-compliant FreeRTOS delay)
    vTaskDelay(pdMS_TO_TICKS(1));
    esp_task_wdt_reset();  // Feed watchdog during dead time
    
    return ESP_OK;
}
```

**Rationale:**
- **Therapeutic clarity**: Therapists configure bilateral frequency (0.5-2 Hz)
- **Safety consistency**: Non-overlapping guaranteed at any cycle time
- **JPL compliance**: All timing uses vTaskDelay(), no busy-wait loops
- **Watchdog integration**: 1ms dead time provides TWDT feeding opportunity
- **Minimal overhead**: 1ms = 0.1-0.2% of half-cycle budget
- **Hardware protection**: GPIO write latency (~50ns) exceeds MOSFET turn-off time (30ns)

**Dead Time Overhead Analysis:**
- 250ms half-cycle (500ms total): 1ms = 0.4% overhead
- 500ms half-cycle (1000ms total): 1ms = 0.2% overhead
- 1000ms half-cycle (2000ms total): 1ms = 0.1% overhead

**Examples:**
- Fast stimulation: 500ms total → 250ms per device (2 Hz)
  - Motor active: 249ms, Dead time: 1ms
- Standard EMDR: 1000ms total → 500ms per device (1 Hz)
  - Motor active: 499ms, Dead time: 1ms
- Slow stimulation: 2000ms total → 1000ms per device (0.5 Hz)
  - Motor active: 999ms, Dead time: 1ms

**Alternatives Considered:**
- **Microsecond dead time (esp_rom_delay_us(1))**: 
  - ❌ Rejected: Busy-wait loop violates JPL coding standard
  - ❌ Rejected: Cannot feed watchdog during delay
  - ❌ Rejected: Blocks other FreeRTOS tasks
- **No explicit dead time**: 
  - ❌ Rejected: No opportunity for watchdog feeding
  - ❌ Rejected: Reduces safety margin
- **Variable dead time based on cycle length**:
  - ❌ Rejected: Adds complexity without benefit
  - ❌ Rejected: 1ms sufficient for all cycle times

### AD007: FreeRTOS Task Architecture

**Decision**: Multi-task architecture with priority-based scheduling

**Task Priorities and Stack Allocation:**
```c
// Task priority definitions (higher number = higher priority)
#define TASK_PRIORITY_BUTTON_ISR        25  // Highest - emergency response
#define TASK_PRIORITY_MOTOR_CONTROL     15  // High - bilateral timing critical
#define TASK_PRIORITY_BLE_MANAGER       10  // Medium - communication
#define TASK_PRIORITY_BATTERY_MONITOR    5  // Low - background monitoring  
#define TASK_PRIORITY_NVS_MANAGER        1  // Lowest - data persistence

// Stack sizes (optimized for ESP32-C6's 512KB SRAM)
#define STACK_SIZE_BUTTON_ISR       1024    // Simple ISR handling
#define STACK_SIZE_MOTOR_CONTROL    2048    // PWM + timing calculations
#define STACK_SIZE_BLE_MANAGER      4096    // NimBLE stack requirements
#define STACK_SIZE_BATTERY_MONITOR  1024    // ADC reading + calculations
#define STACK_SIZE_NVS_MANAGER      1024    // NVS operations

// Total stack usage: ~9KB of 512KB SRAM (very conservative)
```

**Task Creation Requirements:**
- **Stack analysis**: All tasks must undergo worst-case stack usage analysis
- **Priority validation**: Real-time performance testing to verify priority assignments
- **TWDT registration**: All critical tasks must register with Task Watchdog Timer
- **Mutex protection**: All shared resources protected by FreeRTOS mutexes
- **Timing compliance**: All delays use vTaskDelay() (no busy-wait loops)

**Rationale:**
- **Emergency response**: Button ISR has highest priority for immediate motor coast
- **Real-time communication**: BLE tasks prioritized for timing-critical bilateral coordination
- **Motor safety**: H-bridge control prioritized for precise timing and safety
- **Watchdog feeding**: 1ms dead time periods provide TWDT reset opportunities
- **Power efficiency**: Background monitoring tasks run at lower priority
- **Thread safety**: All shared resources protected by FreeRTOS mutexes

### AD008: BLE Protocol Architecture

**Decision**: Dual GATT service architecture for different connection types with proper 128-bit UUIDs

**UUID Collision Issue - CRITICAL:**
- **0x1800 and 0x1801 are RESERVED by Bluetooth SIG**
- 0x1800 = Generic Access Service (GAP) - mandatory on all BLE devices
- 0x1801 = Generic Attribute Service (GATT) - standard BLE service
- Using these UUIDs will cause device pairing failures and BLE stack conflicts

**Service Design with Proper UUIDs:**

1. **EMDR Bilateral Control Service** - Device-to-device motor coordination
   - **UUID**: `6E400001-B5A3-F393-E0A9-E50E24DCCA9E`
   - **Purpose**: Real-time bilateral stimulation commands between paired devices
   - **Characteristics**: Start/stop, cycle time configuration, intensity control

2. **EMDR Configuration Service** - Mobile app control and monitoring  
   - **UUID**: `6E400002-B5A3-F393-E0A9-E50E24DCCA9E`
   - **Purpose**: Therapist configuration and session monitoring
   - **Characteristics**: Session parameters, battery status, error reporting

**UUID Generation Strategy:**
- **128-bit custom UUIDs** to avoid all collisions
- **Related pattern**: Both services share base UUID with single byte difference (0x01 vs 0x02)
- **Collision-free guarantee**: Random generation ensures uniqueness
- **NimBLE format**: Uses `BLE_UUID128_INIT()` macro for proper byte ordering

**Characteristic UUID Assignment (Added November 11, 2025):**

Services use the 13th byte (position 12 in array) for service differentiation (0x01, 0x02).
Characteristics within each service use the 14th byte (position 13 in array) for incremental IDs:

```
Service UUID:     6E4000XX-B5A3-F393-E0A9-E50E24DCCA9E
                        ↑ (13th byte: service ID)

Characteristic:   6E40XXYY-B5A3-F393-E0A9-E50E24DCCA9E
                        ↑  ↑
                    13th  14th (characteristic ID)

Example - Bilateral Control Service Characteristics:
6E400101-... = Bilateral Command (service 01, char 01)
6E400201-... = Total Cycle Time (service 01, char 02)
6E400301-... = Motor Intensity (service 01, char 03)

Example - Configuration Service Characteristics:
6E400201-... = Mode Selection (service 02, char 01)
6E400202-... = Battery Level (service 02, char 02)
6E400203-... = Session Time (service 02, char 03)
```

This scheme allows:
- 255 services (byte 13: 0x01-0xFF)
- 255 characteristics per service (byte 14: 0x01-0xFF)
- Clear relationship between services and their characteristics
- Future expansion without UUID collisions

**NimBLE Implementation:**
```c
// EMDR Bilateral Control Service UUID: 6E400001-B5A3-F393-E0A9-E50E24DCCA9E
static const ble_uuid128_t bilateral_service_uuid = 
    BLE_UUID128_INIT(0x9e, 0xca, 0xdc, 0x24, 0x0e, 0xe5,
                     0xa9, 0xe0, 0x93, 0xf3, 0xa3, 0xb5,
                     0x01, 0x00, 0x40, 0x6e);

// EMDR Configuration Service UUID: 6E400002-B5A3-F393-E0A9-E50E24DCCA9E
static const ble_uuid128_t config_service_uuid = 
    BLE_UUID128_INIT(0x9e, 0xca, 0xdc, 0x24, 0x0e, 0xe5,
                     0xa9, 0xe0, 0x93, 0xf3, 0xa3, 0xb5,
                     0x02, 0x00, 0x40, 0x6e);

// Note: BLE_UUID128_INIT uses reverse byte order (little-endian)
// The 13th byte differs: 0x01 for Bilateral, 0x02 for Configuration
```

**Rationale:**
- **Collision avoidance**: 128-bit UUIDs guaranteed not to conflict with Bluetooth SIG standards
- **Service isolation**: Bilateral motor timing not affected by mobile app configuration
- **Concurrent connections**: Both bilateral device and mobile app can connect
- **Security separation**: Different access controls for different functions
- **Related UUIDs**: Single byte difference makes services recognizable as related
- **Future expansion**: Easy to add new services (0x03, 0x04, etc.) without affecting core motor functionality

**Connection Priority:**
- Bilateral device connections take precedence over mobile app
- Mobile app configuration only allowed during non-stimulation periods
- Emergency shutdown available from all connected devices

**Packet Loss Detection and Recovery:**

**Enhanced Message Structure:**
```c
typedef struct {
    bilateral_command_t command;    // START/STOP/SYNC/INTENSITY
    uint16_t sequence_number;       // Rolling sequence number
    uint32_t timestamp_ms;          // System timestamp
    uint32_t data;                  // Total cycle time or intensity
    uint16_t checksum;              // Simple integrity check
} bilateral_message_t;
```

**Detection Logic:**
- **Sequence gap detection**: Missing sequence numbers indicate packet loss
- **Timeout detection**: No packets received for >2 seconds triggers fallback
- **Consecutive miss threshold**: 3 consecutive missed packets = single-device mode
- **Automatic recovery**: Return to bilateral mode when communication resumes

**Fallback Strategy:**
- **Immediate safety**: Non-overlapping stimulation maintained at all times
- **Single-device mode**: Forward/reverse alternating motor pattern with same cycle time
- **Status indication**: LED heartbeat pattern during fallback
- **Reconnection attempts**: Periodic scanning for lost peer device

**Benefits:**
- **No ACK overhead**: Lightweight detection without additional BLE traffic
- **Fast detection**: <1.5 seconds maximum detection time
- **Graceful degradation**: Therapeutic session continues uninterrupted
- **JPL compliant**: Bounded complexity, predictable behavior

### AD009: Bilateral Timing Implementation with Configurable Cycles

**Decision**: Server-controlled master timing with configurable total cycle time

**Timing Architecture Examples:**
```
1000ms Total Cycle (1 Hz bilateral rate):
Server: [===499ms motor===][1ms dead][---499ms off---][1ms dead]
Client: [---499ms off---][1ms dead][===499ms motor===][1ms dead]

2000ms Total Cycle (0.5 Hz bilateral rate):
Server: [===999ms motor===][1ms dead][---999ms off---][1ms dead]
Client: [---999ms off---][1ms dead][===999ms motor===][1ms dead]
```

**Critical Safety Requirements:**
- **Non-overlapping stimulation**: Devices NEVER stimulate simultaneously
- **Precision timing**: ±10ms maximum deviation from configured total cycle time
- **Half-cycle guarantee**: Each device gets exactly 50% of total cycle
- **Dead time inclusion**: 1ms dead time included within each half-cycle window
- **Server authority**: Server maintains master clock and commands client
- **Immediate emergency stop**: 50ms maximum response time to shutdown

**Implementation Strategy:**
- FreeRTOS vTaskDelay() for all timing operations (JPL compliant)
- BLE command messages include total cycle time configuration
- Fail-safe behavior if communication lost (maintains last known cycle time)
- 1ms dead time at end of each half-cycle for watchdog feeding

**Haptic Effects Support:**
```c
// Short haptic pulse within half-cycle window
// Example: 200ms pulse in 500ms half-cycle
motor_active_time = 200ms;
coast_time = 500ms - 200ms - 1ms = 299ms;
dead_time = 1ms;
// Total = 500ms half-cycle maintained
```

## Safety and Error Handling Decisions

### AD010: Race Condition Prevention Strategy

**Decision**: Random startup delay to prevent simultaneous server attempts

**Problem**: If both devices power on simultaneously, both might attempt server role

**Solution**: 
- Random delay 0-2000ms before starting BLE operations
- First device to advertise becomes server
- Second device discovers server and becomes client
- Hardware RNG used for true randomness

**Verification**: Stress testing with simultaneous power-on scenarios

### AD011: Emergency Shutdown Protocol

**Decision**: Immediate motor coast with fire-and-forget coordinated shutdown

**Safety Requirements:**
- 5-second button hold triggers emergency stop
- Immediate motor coast (GPIO write, no delay)
- Fire-and-forget shutdown message to paired device (no ACK wait)
- No NVS session state saving during emergency (new session on restart)
- Pairing data and settings preserved in NVS (exception for reconnection)

**Implementation:**
- ISR-based button monitoring for fastest response
- Immediate GPIO write for motor coast (~50ns)
- BLE shutdown command sent without waiting for acknowledgment
- Fallback to local shutdown if BLE disconnected (always safe)

**Fire-and-Forget Rationale:**
- **Safety-first**: Device executes local shutdown immediately
- **No blocking**: Don't wait for peer acknowledgment (may be powered off)
- **Best effort**: Send BLE command but don't depend on it
- **Always safe**: Each device shuts down independently

**NVS Storage Clarification:**

AD011 "no NVS state saving" means session state, not settings:
- ❌ Session state NOT saved: Don't resume mid-session at 15 minutes (unsafe)
- ✅ Pairing data saved: Peer device MAC address for reconnection (AD026)
- ✅ Settings saved: Mode 5 custom parameters (frequency, duty cycle, LED)
- Rationale: Settings enable reconnection and user preferences, state would create unsafe resume

### AD012: Dead Time Implementation Strategy

**Decision**: 1ms FreeRTOS delay at end of each half-cycle

**Rationale:**
- **JPL Compliance**: No busy-wait loops, uses FreeRTOS primitives exclusively
- **Watchdog friendly**: 1ms dead time allows TWDT feeding between half-cycles
- **Hardware protection**: GPIO write latency (~50ns) provides actual MOSFET dead time (>30ns requirement)
- **Timing budget**: 1ms represents only 0.1-0.2% of typical half-cycle
- **Safety margin**: 1000x hardware requirement (1ms vs 100ns needed)

**GPIO Write Reality:**
- ESP32-C6 GPIO write: ~10-50ns latency
- MOSFET turn-off time: ~30ns
- Sequential GPIO writes create >100ns natural dead time
- No explicit microsecond delays needed between direction changes

**Implementation Pattern:**
```c
// Step 1: Motor active for (half_cycle - 1ms)
motor_set_direction_intensity(MOTOR_FORWARD, intensity);
vTaskDelay(pdMS_TO_TICKS(half_cycle_ms - 1));

// Step 2: Immediate coast (GPIO write provides hardware dead time)
motor_set_direction_intensity(MOTOR_COAST, 0);

// Step 3: 1ms FreeRTOS delay for watchdog feeding
vTaskDelay(pdMS_TO_TICKS(1));
esp_task_wdt_reset();
```

### AD013: Factory Reset Security Window

**Decision**: Time-limited factory reset capability (first 30 seconds only) with GPIO15 solid on indication

**Rationale:**
- **Accidental reset prevention**: No factory reset during therapy sessions
- **Service technician access**: Reset available during initial setup
- **Clear user feedback**: GPIO15 solid on distinct from purple therapy light blink
- **Security window**: 10-second hold only works in first 30 seconds after boot
- **Conditional compilation**: Factory reset can be disabled in production builds

**Implementation:**
- Boot time tracking with 30-second window
- 10-second button hold triggers NVS clear (only in first 30s)
- GPIO15 status LED solid on at 10-second mark (clear visual warning)
- Purple therapy light blink for 5s emergency shutdown (different indication)
- Comprehensive NVS clearing including pairing data

**LED Indication Pattern:**
- **5-second hold**: Purple therapy light blink (emergency shutdown)
- **10-second hold (first 30s only)**: GPIO15 solid on + purple blink (NVS clear)
- **10-second hold (after 30s)**: No NVS clear, only emergency shutdown

**GPIO15 Rationale:**
- Distinct from purple therapy light (separate LED)
- Solid on vs blinking provides clear differentiation
- On-board LED always available (no case material dependency)
- Active LOW: GPIO15 = 0 turns LED on

## Power Management Architecture

### AD014: Deep Sleep Strategy

**Decision**: Aggressive power management with button wake

**Sleep Implementation:**
- **Deep sleep mode**: < 1mA current consumption
- **Wake sources**: GPIO0 button press only
- **Wake time**: < 2 seconds to full operation
- **Session timers**: Automatic shutdown after configured duration

**Rationale:**
- **Battery life**: Essential for portable therapeutic devices
- **User experience**: Fast wake times for immediate use
- **Predictable operation**: Clear session boundaries

## Data Persistence Decisions

### AD015: NVS Storage Strategy

**Decision**: Selective persistence with testing mode overrides

**Stored Data:**
- Device pairing information (MAC addresses)
- User configuration settings (last used cycle time, intensity)
- Session statistics and usage tracking
- Calibration data for motors (future)

**Testing Mode Considerations:**
- Conditional compilation flag to disable NVS writes during development
- Prevents flash wear during intensive testing
- Maintains functional testing without storage side effects

### AD016: No Session State Persistence

**Decision**: Every startup begins a new session (no recovery)

**Rationale:**
- **Safety-first approach**: No ambiguous states after power loss
- **Therapeutic clarity**: Clear session boundaries for therapy
- **Simplified error recovery**: No complex state restoration logic
- **User expectations**: Power cycle indicates fresh start

## Testing and Validation Architecture

### AD017: Conditional Compilation Strategy

**Decision**: Multiple build configurations for different deployment phases

**Build Modes:**
```c
#ifdef TESTING_MODE
    // Disable NVS writes, enable debug logging
#endif

#ifdef PRODUCTION_BUILD
    // Zero logging overhead, full power management
#endif

#ifdef ENABLE_FACTORY_RESET
    // Include factory reset functionality
#endif
```

**Rationale:**
- **Development efficiency**: Fast iteration without flash wear
- **Production optimization**: Zero debug overhead in deployed devices
- **Safety configuration**: Factory reset disabled in some deployments
- **Debugging capability**: Extensive logging available when needed

## Risk Assessment and Mitigation

### AD018: Technical Risk Mitigation

**Identified Risks:**
1. **BLE connection instability** → Mitigation: ESP-IDF v5.5.0 with proven, stable BLE stack
2. **Timing precision degradation** → Mitigation: FreeRTOS delays with ±10ms specification
3. **Power management complexity** → Mitigation: Proven deep sleep patterns from ESP-IDF
4. **Code complexity growth** → Mitigation: JPL coding standard with complexity limits
5. **Watchdog timeout** → Mitigation: 1ms dead time provides TWDT feeding opportunity

**Monitoring Strategy:**
- Real-time performance metrics collection
- Automated testing for timing precision at multiple cycle times
- Battery life monitoring and optimization
- Code complexity analysis in CI/CD pipeline

### AD019: Task Watchdog Timer with Adaptive Feeding Strategy

**Decision**: Adaptive watchdog feeding based on half-cycle duration

**Problem Analysis:**
- **Maximum half-cycle**: 1000ms (for 2000ms total cycle at 0.5 Hz)
- **Original TWDT timeout**: 1000ms
- **Risk**: Half-cycle = timeout, no safety margin

**Solution**: Adaptive feeding with increased timeout

**Watchdog Feeding Strategy:**
```c
esp_err_t motor_execute_half_cycle(motor_direction_t direction,
                                    uint8_t intensity_percent,
                                    uint32_t half_cycle_ms) {
    // Validate parameter (JPL requirement)
    if (half_cycle_ms < 100 || half_cycle_ms > 1000) {
        return ESP_ERR_INVALID_ARG;
    }
    
    motor_set_direction_intensity(direction, intensity_percent);
    
    // For long half-cycles (>500ms), feed watchdog mid-cycle for extra safety
    if (half_cycle_ms > 500) {
        uint32_t mid_point = half_cycle_ms / 2;
        vTaskDelay(pdMS_TO_TICKS(mid_point));
        esp_task_wdt_reset();  // Mid-cycle feeding
        vTaskDelay(pdMS_TO_TICKS(half_cycle_ms - 1 - mid_point));
    } else {
        vTaskDelay(pdMS_TO_TICKS(half_cycle_ms - 1));
    }
    
    motor_set_direction_intensity(MOTOR_COAST, 0);
    
    // Always feed at end of half-cycle (dead time period)
    vTaskDelay(pdMS_TO_TICKS(1));
    esp_task_wdt_reset();
    
    return ESP_OK;
}
```

**TWDT Configuration:**
- **Timeout**: 2000ms (accommodates 1000ms half-cycles with 2x safety margin)
- **Monitored tasks**: Button ISR, BLE Manager, Motor Controller, Battery Monitor
- **Reset behavior**: Immediate system reset on timeout (fail-safe)
- **Feed frequency**: 
  - Short half-cycles (≤500ms): Every 501ms maximum
  - Long half-cycles (>500ms): Every 250-251ms (mid-cycle + end)

**Safety Margin Analysis:**
```
500ms Half-Cycle (1000ms total cycle):
[===499ms motor===][1ms dead+feed]
Watchdog fed every 500ms
Timeout: 2000ms
Safety margin: 4x ✓

1000ms Half-Cycle (2000ms total cycle):
[===500ms motor===][feed][===499ms motor===][1ms dead+feed]
Watchdog fed every 500ms and at 1000ms (end of half-cycle)
Timeout: 2000ms
Safety margin: 4x ✓
```

**JPL Compliance:**
- ✅ Cyclomatic complexity: 2 (one if statement, well under limit of 10)
- ✅ No busy-wait loops (all timing uses vTaskDelay)
- ✅ Bounded execution time (predictable for all cycle times)
- ✅ Comprehensive parameter validation

**Rationale:**
- **Safety-critical**: Prevents watchdog timeout even with worst-case timing jitter
- **Therapeutic range**: Maintains full 0.5-2 Hz bilateral stimulation capability
- **JPL compliant**: Simple conditional logic, predictable behavior
- **Integrated design**: Dead time serves dual purpose (motor safety + watchdog)
- **Therapeutic safety**: System automatically recovers from software hangs

**Verification Requirements:**
- Stress testing with intentional task hangs at all cycle times
- Timing precision validation with oscilloscope (500ms, 1000ms, 2000ms total cycles)
- TWDT timeout testing under various load conditions
- Verify mid-cycle feeding occurs for 1000ms half-cycles

### AD020: Power Management Strategy with Phased Implementation

**Decision**: BLE-compatible power management hooks in Phase 1 with full light sleep optimization in Phase 2

**Problem Statement:**
- **Battery-powered medical device** requires 20+ minute therapeutic sessions
- **ESP32-C6 BLE frequency requirements** constrain light sleep options (~80MHz minimum)
- **Safety-critical timing requirements** must not be compromised by power optimization
- **Development velocity** needed for core bilateral stimulation functionality

**Solution Strategy:**

**Phase 1 (Core Development): BLE-Safe Power Management Hooks**
```c
// Power management lock handles (initialized in Phase 1)
static esp_pm_lock_handle_t ble_pm_lock = NULL;
static esp_pm_lock_handle_t pwm_pm_lock = NULL;

esp_err_t power_manager_init(void) {
    esp_err_t ret;
    
    // Create locks (Phase 1: created but not actively managed yet)
    ret = esp_pm_lock_create(ESP_PM_NO_LIGHT_SLEEP, 0, "ble_stack", &ble_pm_lock);
    if (ret != ESP_OK) return ret;
    
    ret = esp_pm_lock_create(ESP_PM_APB_FREQ_MAX, 0, "pwm_motor", &pwm_pm_lock);
    if (ret != ESP_OK) return ret;
    
    // Phase 1: Don't configure power management yet, just initialize handles
    return ESP_OK;
}

esp_err_t power_manager_configure_ble_safe_light_sleep(
    const ble_compatible_light_sleep_config_t* config) {
    // Phase 1: Stub (power management not active)
    // Phase 2: Will call esp_pm_configure() and manage locks
    return ESP_OK;
}

esp_err_t power_manager_get_ble_aware_session_stats(
    ble_aware_session_stats_t* stats) {
    // Phase 1: Return estimated values
    stats->average_current_ma = 50;
    stats->cpu_sleep_current_ma = 25;
    stats->ble_active_current_ma = 50;
    stats->power_efficiency_percent = 0;  // No optimization active yet
    return ESP_OK;
}
```

**Phase 2 (Post-Verification): Full BLE-Compatible Light Sleep**
```c
// Advanced power optimization after bilateral timing verified
esp_err_t power_manager_configure_ble_safe_light_sleep(
    const ble_compatible_light_sleep_config_t* config) {
    esp_err_t ret;
    
    // Configure BLE-compatible power management
    esp_pm_config_esp32_t pm_config = {
        .max_freq_mhz = 160,
        .min_freq_mhz = 80,         // BLE-safe minimum
        .light_sleep_enable = true
    };
    
    ret = esp_pm_configure(&pm_config);
    if (ret != ESP_OK) return ret;
    
    // Locks already created in power_manager_init()
    // Acquire during BLE operations and motor active periods
    // Release during motor off periods to allow light sleep
    
    // 40-50% power savings with BLE-safe configuration
    // CPU at 80MHz during light sleep, BLE/PWM at 160MHz
    // Maintains BLE responsiveness and ±10ms timing precision
    
    return ESP_OK;
}
```

**BLE-Compatible Power Management Architecture:**

**ESP32-C6 Frequency Strategy:**
```c
// CORRECTED - BLE-safe frequency configuration
esp_pm_config_esp32_t pm_config = {
    .max_freq_mhz = 160,        // Full speed when CPU awake
    .min_freq_mhz = 80,         // ✅ BLE-compatible minimum frequency
    .light_sleep_enable = true  // Automatic light sleep during delays
};

// Power management lock handles (CORRECTED API)
static esp_pm_lock_handle_t ble_pm_lock = NULL;
static esp_pm_lock_handle_t pwm_pm_lock = NULL;

// Create locks with proper API (requires handle output parameter)
esp_pm_lock_create(ESP_PM_NO_LIGHT_SLEEP, 0, "ble_stack", &ble_pm_lock);
esp_pm_lock_create(ESP_PM_APB_FREQ_MAX, 0, "pwm_motor", &pwm_pm_lock);

// Acquire locks during critical operations
esp_pm_lock_acquire(ble_pm_lock);     // Prevent CPU light sleep during BLE
esp_pm_lock_acquire(pwm_pm_lock);     // Maintain APB frequency for PWM

// Release when safe to sleep
esp_pm_lock_release(ble_pm_lock);
esp_pm_lock_release(pwm_pm_lock);
```

**Realistic Power Savings with BLE Constraints:**

**Without Power Management:**
- Continuous 160MHz active: ~50-60mA
- 20-minute session: 60-72mAh

**With BLE-Compatible Light Sleep:**
```
Bilateral Pattern Analysis (1000ms total cycle):
Server: [===499ms motor===][1ms dead][---499ms off---][1ms dead]
Client: [---499ms off---][1ms dead][===499ms motor===][1ms dead]

Power States:
- Motor active periods: 50mA (CPU awake at 160MHz for GPIO control)
- Inactive periods: 25-30mA (CPU at 80MHz light sleep)
- BLE operations: 50mA (BLE stack locked at 160MHz)
- Average consumption: 30-35mA (40-50% power savings)
```

**Implementation Rationale:**

**Why BLE-Safe Configuration:**
1. **BLE Stack Requirements**: ~80MHz minimum for reliable BLE operation
2. **Safety-Critical Communication**: BLE must remain responsive for emergency shutdown
3. **Therapeutic Session Reliability**: Therapists depend on stable device communication
4. **ESP-IDF v5.5.1 Compatibility**: Uses proven BLE power management patterns

**Why Stubs in Phase 1:**
1. **Development Focus**: Core bilateral timing and BLE communication prioritized
2. **Risk Mitigation**: Power management complexity doesn't block core functionality
3. **API Architecture**: Power management interfaces established from project start
4. **Testing Isolation**: Bilateral timing verified before adding sleep complexity

**Why Full Implementation in Phase 2:**
1. **Verified Foundation**: Bilateral timing precision confirmed before optimization
2. **Power Data Available**: Real hardware testing provides accurate consumption baselines
3. **Safety Validation**: Emergency shutdown and timing precision validated first
4. **Incremental Enhancement**: Power optimization builds on proven core functionality

**Safety Considerations:**

**Light Sleep Compatibility Requirements:**
- **BLE Stack Responsiveness**: NimBLE must remain responsive during CPU light sleep
- **PWM/LEDC Continuity**: Motor control peripherals locked at 160MHz (no sleep)
- **Emergency Shutdown**: <50ms response time maintained during light sleep
- **Watchdog Feeding**: TWDT feeding continues during 1ms dead time periods
- **Timing Precision**: <50μs wake-up latency maintains ±10ms bilateral requirement

**LEDC PWM Frequency Dependency:**
```c
/**
 * LEDC PWM Frequency Requirements for Power Management:
 * - LEDC clock source: APB_CLK (80MHz when CPU in light sleep)
 * - PWM frequency: 25kHz
 * - Resolution: 13-bit (0-8191)
 * - Clock calculation: 80MHz / (25kHz * 8192) = 0.39 (works)
 * - ✅ LEDC continues running at 25kHz even when CPU at 80MHz
 * 
 * Power Lock Strategy:
 * - Use ESP_PM_APB_FREQ_MAX during motor active periods
 * - Release lock during motor off periods (allows deeper sleep)
 * - BLE stack keeps minimum 80MHz during all operations
 * 
 * Why ESP_PM_APB_FREQ_MAX for PWM:
 * - Maintains consistent LEDC clock frequency for motor control
 * - Prevents PWM frequency drift during power state transitions
 * - Ensures smooth motor operation without audible frequency changes
 */
```

**Power Monitoring Integration:**
```c
typedef struct {
    uint32_t session_duration_ms;
    uint16_t average_current_ma;        // Overall average consumption
    uint16_t cpu_sleep_current_ma;      // During CPU light sleep (80MHz)
    uint16_t ble_active_current_ma;     // During BLE operations (160MHz)
    uint32_t cpu_light_sleep_time_ms;   // Time CPU spent in light sleep
    uint32_t ble_full_speed_time_ms;    // Time BLE locked at 160MHz
    uint8_t ble_packet_success_rate;    // BLE reliability metric
    uint8_t power_efficiency_percent;   // Actual vs theoretical efficiency
} ble_aware_session_stats_t;
```

**Validation Strategy:**

**Phase 1 Validation:**
- Bilateral timing precision: ±10ms at all cycle times (500ms, 1000ms, 2000ms)
- BLE communication reliability: <3 consecutive packet loss threshold
- Emergency shutdown response: <50ms from button press to motor coast
- Motor control functionality: H-bridge operation and dead time implementation

**Phase 2 Validation:**
- Power consumption: 40-50% reduction during bilateral sessions
- Light sleep wake-up latency: <50μs (verified with oscilloscope)
- BLE responsiveness during light sleep: GATT operation timing maintained
- PWM continuity: Motor operation uninterrupted during CPU sleep
- Thermal performance: No overheating during extended light sleep sessions

**Risk Mitigation:**
- **Gradual roll-out**: Power management enhanced incrementally
- **Fallback modes**: System works without light sleep if issues discovered
- **Monitoring hooks**: Power consumption tracked from Phase 1
- **Safety preservation**: All emergency and timing requirements maintained

**Benefits of Phased Approach:**

**For Immediate Development:**
- Core functionality development not blocked by power complexity
- Power management interfaces established for future enhancement
- Basic power monitoring provides data for optimization decisions

**For Long-term Success:**
- Power efficiency architected from project start
- Medical device battery life requirements achievable (40-50% improvement)
- ESP-IDF v5.5.1 BLE-compatible power management features utilized
- Future enhancements build on solid power management foundation

**Development Timeline:**
- **Week 1-2**: Core bilateral stimulation implementation
- **Week 3**: Basic BLE-safe power management hooks functional
- **Week 4**: Advanced light sleep optimization (40-50% power savings)

### AD021: Motor Stall Detection via Back-EMF Sensing

**Decision**: Software-based motor stall detection using power-efficient back-EMF sensing

**Problem**:
- ERM motor stall condition (120mA vs 90mA normal) could damage H-bridge MOSFETs
- Battery drain acceleration during stall conditions
- No dedicated current sensing hardware in discrete MOSFET design
- Battery voltage monitoring for stall detection is power-inefficient (resistor divider draws ~248µA continuously)
- Back-EMF can swing from -3.3V to +3.3V, but ESP32-C6 ADC only accepts 0V to 3.3V

**Solution**:
- **Primary method**: Back-EMF sensing via GPIO0 (ADC1_CH0) during coast periods
- **Signal conditioning**: Resistive summing network biases and scales ±3.3V to 0-3.3V ADC range
- **Backup method**: Battery voltage drop monitoring if back-EMF unavailable
- **Future**: Integrated H-bridge IC with hardware current sensing and thermal protection
- All detection uses vTaskDelay() for JPL compliance

**Back-EMF Signal Conditioning Circuit:**

```
        R_bias (10kΩ)
3.3V ---/\/\/\---+
                 |
   R_signal (10kΩ)|
OUTA ---/\/\/\---+--- GPIO0 (ADC input) ---> [ESP32-C6 ADC, ~100kΩ-1MΩ input Z]
                 |
              C_filter
               (22nF)
                 |
                GND

Note: R_load intentionally NOT POPULATED for maximum ADC range
Production: 22nF capacitor (prototypes used 12nF, original design 15nF)
```

**Circuit Analysis:**

This is a **voltage summing circuit** that averages two voltage sources through equal resistors.

By Kirchhoff's Current Law (ADC draws negligible current):
```
I_bias = I_signal
(3.3V - V_GPIO1) / R_bias = (V_GPIO1 - V_OUTA) / R_signal
```

With R_bias = R_signal = 10kΩ:
```
3.3V - V_GPIO1 = V_GPIO1 - V_OUTA
3.3V + V_OUTA = 2 × V_GPIO1

V_GPIO1 = (3.3V + V_OUTA) / 2
V_GPIO1 = 1.65V + 0.5 × V_OUTA
```

**Voltage Mapping (Perfect Full Range):**
```
V_OUTA = -3.3V → V_GPIO1 = (3.3V - 3.3V) / 2 = 0V     ✓ (ADC minimum)
V_OUTA =   0V  → V_GPIO1 = (3.3V + 0V) / 2   = 1.65V  ✓ (ADC center)
V_OUTA = +3.3V → V_GPIO1 = (3.3V + 3.3V) / 2 = 3.3V   ✓ (ADC maximum)
```

**Key Insight - Why No R_load:**

The circuit works by making GPIO1 the **center tap of a voltage divider between 3.3V and V_OUTA**. When resistors are equal, GPIO1 sits at their average voltage. Adding a load resistor to ground pulls GPIO1 down, breaking the symmetry:

- **Without R_load**: V_GPIO1 = 1.65V + 0.5 × V_OUTA (100% ADC range, centered at 1.65V)
- **With R_load = 10kΩ**: V_GPIO1 = 1.1V + 0.333 × V_OUTA (only 67% ADC range, offset bias)

The negative back-EMF is handled by the voltage divider action between R_bias and R_signal, not by a ground reference resistor.

**Low-Pass Filter Characteristics:**
```
R_parallel = R_bias || R_signal = 10kΩ || 10kΩ = 5kΩ
f_c = 1 / (2π × R_parallel × C_filter)
f_c = 1 / (2π × 5kΩ × 22nF) ≈ 1.45 kHz

- Filters 25kHz PWM switching noise (17× attenuation, >94% reduction)
- Preserves ~100-200Hz motor back-EMF fundamental frequency
- Settles in ~0.55ms (5τ = 550µs, sufficient for 1ms+ coast measurement window)
```

**Power Consumption:**
```
Bias current (continuous):
I_bias = 3.3V / (R_bias + R_signal) = 3.3V / 20kΩ = 165µA

Comparison:
- Back-EMF bias network: 165µA continuous
- Battery voltage divider: 248µA when enabled
- Back-EMF is 33% more efficient even with continuous bias
```

**Implementation Methods:**

**Method 1: Back-EMF Sensing (Primary - Power Efficient)**
```c
esp_err_t detect_stall_via_backemf(void) {
    uint16_t backemf_voltage_mv;
    
    // Coast motor to allow back-EMF to develop
    motor_set_direction_intensity(MOTOR_COAST, 0);
    vTaskDelay(pdMS_TO_TICKS(10));  // Allow back-EMF and filter to stabilize
    
    // Read back-EMF on GPIO0 (OUTA from H-bridge)
    // ADC reading is already biased and scaled: 0-3.3V ADC → -3.3V to +3.3V back-EMF
    adc_read_voltage(ADC1_CHANNEL_0, &backemf_voltage_mv);
    
    // Convert ADC voltage back to actual back-EMF:
    // V_backemf = 2 × (V_ADC - 1650mV)
    int16_t actual_backemf_mv = 2 * ((int16_t)backemf_voltage_mv - 1650);
    
    // Stalled motor: very low or no back-EMF voltage
    // Normal operation: back-EMF magnitude > 1000mV (~1-2V depending on speed)
    int16_t backemf_magnitude = (actual_backemf_mv < 0) ? -actual_backemf_mv : actual_backemf_mv;
    
    if (backemf_magnitude < BACKEMF_STALL_THRESHOLD_MV) {
        return ESP_ERR_MOTOR_STALL;
    }
    
    return ESP_OK;
}
```

**Method 2: Battery Voltage Drop Analysis (Backup)**
```c
esp_err_t detect_stall_via_battery_drop(void) {
    uint16_t voltage_no_load, voltage_with_motor;
    
    // Baseline measurement
    motor_set_direction_intensity(MOTOR_COAST, 0);
    vTaskDelay(pdMS_TO_TICKS(10));
    battery_read_voltage(&voltage_no_load);
    
    // Load measurement
    motor_set_direction_intensity(MOTOR_FORWARD, 50);
    vTaskDelay(pdMS_TO_TICKS(100));
    battery_read_voltage(&voltage_with_motor);
    
    uint16_t voltage_drop_mv = voltage_no_load - voltage_with_motor;
    
    // Stalled motor: >300mV drop suggests excessive current
    if (voltage_drop_mv > STALL_VOLTAGE_DROP_THRESHOLD) {
        return ESP_ERR_MOTOR_STALL;
    }
    
    return ESP_OK;
}
```

**Stall Response Protocol:**
1. **Immediate coast**: Set both H-bridge inputs low (immediate GPIO write)
2. **Mechanical settling**: 100ms vTaskDelay() for motor to stop
3. **Reduced intensity restart**: Retry at 50% intensity
4. **LED fallback**: Switch to LED stimulation if stall persists
5. **Error logging**: Record stall event in NVS for diagnostics

**Rationale:**
- **Power efficiency**: Back-EMF sensing is ~250x more efficient than battery voltage monitoring
- **Continuous monitoring**: Can check motor health frequently without battery drain
- **Direct indication**: Stalled motor has no back-EMF (direct mechanical failure indicator)
- **Hardware compatibility**: Uses existing GPIO0 ADC capability
- **JPL compliant**: All delays use vTaskDelay(), no busy-wait loops
- **Battery monitoring preserved**: GPIO2 reserved for periodic battery level reporting
- **Therapeutic continuity**: Graceful degradation to LED stimulation

**Future Enhancement (Integrated H-Bridge IC):**
- **Hardware current sensing**: Dedicated sense resistor for precise stall detection
- **Thermal protection**: Integrated over-temperature shutdown
- **Shoot-through protection**: Hardware interlocks eliminate software dead time
- **Fault reporting**: Detailed diagnostic information via SPI/I2C
- **Simpler PCB**: Fewer discrete components, smaller board area
- **Software compatibility**: Back-EMF algorithms remain useful for validation

### AD022: ESP-IDF Build System and Hardware Test Architecture

**Decision**: Use Python pre-build scripts to manage source file selection for ESP-IDF's CMake build system

**CRITICAL CONSTRAINT: ESP-IDF uses CMake, NOT PlatformIO's build system!**

**Problem Statement:**
ESP-IDF uses CMake as its native build system, which requires source files to be explicitly listed in `src/CMakeLists.txt`. PlatformIO's `build_src_filter` option (used for other frameworks) has **NO EFFECT** with ESP-IDF, making it impossible to select different source files for hardware tests using standard PlatformIO mechanisms.

**Why build_src_filter Doesn't Work:**
- ESP-IDF framework uses CMake for all compilation
- PlatformIO's `build_src_filter` only works with PlatformIO's native build system
- When `framework = espidf`, PlatformIO delegates entirely to ESP-IDF's CMake
- CMake reads `src/CMakeLists.txt` directly - no PlatformIO filtering applied
- **Attempting to use build_src_filter with ESP-IDF will silently fail**

**Solution Architecture:**

**1. Python Pre-Build Script (`scripts/select_source.py`)**
- Runs before every build via PlatformIO's `extra_scripts` feature
- Detects current build environment name (e.g., `hbridge_test`, `xiao_esp32c6`)
- Modifies `src/CMakeLists.txt` to use the correct source file
- Maintains source file mapping dictionary for all environments

**2. Source File Organization:**
```
project_root/
├── src/
│   ├── main.c              # Main application
│   └── CMakeLists.txt      # Modified by script before each build
├── test/
│   ├── hbridge_test.c      # Hardware validation tests
│   ├── battery_test.c      # Future tests
│   └── README.md
└── scripts/
    └── select_source.py    # Build-time source selector
```

**3. Build Environment Configuration:**
```ini
; Main application (default)
[env:xiao_esp32c6]
extends = env:base_config
extra_scripts = pre:scripts/select_source.py

; Hardware test environment
[env:hbridge_test]
extends = env:xiao_esp32c6
build_flags = 
    ${env:xiao_esp32c6.build_flags}
    -DHARDWARE_TEST=1
    -DDEBUG_LEVEL=3
; Note: Source selection handled by extra_scripts inherited from base
```

**4. CMakeLists.txt Modification Pattern:**

**Before build (modified by script):**
```cmake
idf_component_register(
    SRCS "main.c"                    # For main application
    # SRCS "../test/hbridge_test.c"  # For hbridge_test environment
    INCLUDE_DIRS "."
    REQUIRES freertos esp_system driver nvs_flash bt
)
```

**How It Works:**
1. User runs: `pio run -e hbridge_test -t upload`
2. PlatformIO reads `platformio.ini`
3. Executes `pre:scripts/select_source.py` before CMake configuration
4. Script detects environment is `hbridge_test`
5. Script modifies `src/CMakeLists.txt` to use `"../test/hbridge_test.c"`
6. ESP-IDF CMake reads modified `CMakeLists.txt`
7. Builds correct source file

**Script Implementation:**
```python
# scripts/select_source.py
Import("env")
import os

# Source file mapping for each build environment
source_map = {
    "xiao_esp32c6": "main.c",
    "xiao_esp32c6_production": "main.c",
    "xiao_esp32c6_testing": "main.c",
    "hbridge_test": "../test/hbridge_test.c",
    # Add future tests here
}

build_env = env["PIOENV"]
source_file = source_map.get(build_env, "main.c")

# Modify src/CMakeLists.txt
cmake_path = os.path.join(env["PROJECT_DIR"], "src", "CMakeLists.txt")
with open(cmake_path, 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.strip().startswith('SRCS'):
        new_lines.append(f'    SRCS "{source_file}"\n')
    else:
        new_lines.append(line)

with open(cmake_path, 'w') as f:
    f.writelines(new_lines)
```

**Rationale:**

1. **ESP-IDF Native Compatibility:**
   - Works with ESP-IDF's CMake build system without fighting it
   - No workarounds or hacks required
   - Follows ESP-IDF best practices

2. **Clean Test Separation:**
   - Hardware tests live in `test/` directory
   - Main application code stays in `src/`
   - No conditional compilation in main.c

3. **Scalable Architecture:**
   - Easy to add new tests (one line in `source_map`)
   - No manual CMakeLists.txt editing needed
   - Future tests follow same pattern

4. **Developer Experience:**
   - Simple commands: `pio run -e hbridge_test -t upload`
   - Fast build switching (automatic source selection)
   - No manual file management

5. **Build System Transparency:**
   - Console output shows which source selected
   - Modified `CMakeLists.txt` can be inspected if needed
   - Deterministic build process

**Adding New Hardware Tests:**

1. Create test file: `test/my_new_test.c`
2. Update `scripts/select_source.py`:
   ```python
   source_map = {
       ...
       "my_new_test": "../test/my_new_test.c",
   }
   ```
3. Add environment to `platformio.ini`:
   ```ini
   [env:my_new_test]
   extends = env:xiao_esp32c6
   build_flags = 
       ${env:xiao_esp32c6.build_flags}
       -DHARDWARE_TEST=1
   ```
4. Build: `pio run -e my_new_test -t upload`

**Alternatives Considered:**

1. **Multiple CMakeLists.txt files:**
   - ❌ Rejected: ESP-IDF expects specific file locations
   - ❌ Rejected: Would require complex CMake include logic

2. **Conditional compilation in main.c:**
   - ❌ Rejected: Clutters main application code
   - ❌ Rejected: Hardware tests should be standalone

3. **Separate PlatformIO projects:**
   - ❌ Rejected: Duplicates configuration
   - ❌ Rejected: Harder to maintain consistency

4. **Manual CMakeLists.txt editing:**
   - ❌ Rejected: Error-prone
   - ❌ Rejected: Breaks automation

5. **Git branch per test:**
   - ❌ Rejected: Excessive branching overhead
   - ❌ Rejected: Difficult to maintain multiple tests

**Benefits:**

✅ **ESP-IDF native** - Works with CMake build system  
✅ **Automatic** - No manual file editing  
✅ **Clean** - Test code separate from main code  
✅ **Scalable** - Easy to add new tests  
✅ **Fast** - Script overhead <100ms  
✅ **Deterministic** - Same command always builds same source  
✅ **Documented** - Clear process for future developers  

**Verification:**
```bash
# Verify main application builds
pio run -e xiao_esp32c6
cat src/CMakeLists.txt  # Should show: SRCS "main.c"

# Verify test builds
pio run -e hbridge_test
cat src/CMakeLists.txt  # Should show: SRCS "../test/hbridge_test.c"
```

**Documentation:**
- Technical details: `docs/ESP_IDF_SOURCE_SELECTION.md`
- Test procedures: `test/README.md`
- Build commands: `BUILD_COMMANDS.md`

**JPL Compliance:**
- Script has bounded complexity (simple dictionary lookup and file modification)
- Deterministic behavior (same input always produces same output)
- Error handling for missing environments (defaults to main.c)
- No dynamic code execution or complex logic

**Future Enhancements:**
- Could extend to select different `sdkconfig` files per environment
- Could manage component dependencies per test
- Could auto-generate test environments from test directory

### AD023: Deep Sleep Wake State Machine for ESP32-C6 ext1

**Decision**: Use wait-for-release with LED blink feedback before deep sleep entry

**Problem Statement:**

ESP32-C6 ext1 wake is **level-triggered**, not edge-triggered. This creates a challenge for button-triggered deep sleep:

**Initial Problem:**
- User holds button through countdown to trigger deep sleep
- Device enters sleep while button is LOW (pressed)
- ext1 configured to wake on LOW
- Device wakes immediately because button is still LOW
- Can't distinguish "still held from countdown" vs "new button press"

**Root Cause:**
The ext1 wake system detects that GPIO1 is LOW (button pressed) at the moment of sleep entry. Since ext1 is level-triggered (wakes when GPIO is LOW), the device immediately wakes up because the wake condition is already true. There's no way for the hardware to know the button was held continuously vs. freshly pressed.

**Failed Approaches Tried:**

1. **Wake immediately, check state, re-sleep if held**
   ```c
   // ❌ DOES NOT WORK
   esp_deep_sleep_start();
   // Wake up here
   if (gpio_get_level(GPIO_BUTTON) == 0) {
       // Button still held, go back to sleep
       esp_deep_sleep_start();
   }
   ```
   - **Problem**: After button released (goes HIGH), ext1 is still configured to wake on LOW
   - Device stuck sleeping because wake condition (LOW) never occurs
   - Can't detect new button press because already sleeping
   - Fundamental misunderstanding of level-triggered wake

2. **State machine with wake-on-HIGH support**
   ```c
   // ❌ TOO COMPLEX, hardware limitations
   if (gpio_get_level(GPIO_BUTTON) == 0) {
       // Button held, configure wake on HIGH (release)
       esp_sleep_enable_ext1_wakeup(gpio_mask, ESP_EXT1_WAKEUP_ANY_HIGH);
   } else {
       // Button not held, configure wake on LOW (press)
       esp_sleep_enable_ext1_wakeup(gpio_mask, ESP_EXT1_WAKEUP_ANY_LOW);
   }
   ```
   - **Problem**: ESP32-C6 ext1 wake-on-HIGH support may be unreliable
   - Adds significant state machine complexity
   - Testing revealed inconsistent wake behavior
   - Too fragile for safety-critical medical device

**Solution Implemented: Wait-for-Release with LED Blink Feedback**

```c
esp_err_t enter_deep_sleep_with_wake_guarantee(void) {
    // If button held after countdown, wait for release
    if (gpio_get_level(GPIO_BUTTON) == 0) {
        ESP_LOGI(TAG, "Waiting for button release...");
        
        // Blink LED while waiting (visual feedback without serial)
        while (gpio_get_level(GPIO_BUTTON) == 0) {
            // Toggle LED at 5Hz (200ms period)
            gpio_set_level(GPIO_STATUS_LED, LED_ON);
            vTaskDelay(pdMS_TO_TICKS(100));
            gpio_set_level(GPIO_STATUS_LED, LED_OFF);
            vTaskDelay(pdMS_TO_TICKS(100));
        }
        
        ESP_LOGI(TAG, "Button released! Entering deep sleep...");
    }
    
    // Always configure ext1 to wake on LOW (button press)
    // Button guaranteed to be HIGH at this point
    uint64_t gpio_mask = (1ULL << GPIO_BUTTON);
    esp_err_t ret = esp_sleep_enable_ext1_wakeup(gpio_mask, ESP_EXT1_WAKEUP_ANY_LOW);
    if (ret != ESP_OK) {
        return ret;
    }
    
    // Enter deep sleep (button guaranteed HIGH at this point)
    esp_deep_sleep_start();
    
    // Never returns
    return ESP_OK;
}
```

**Key Features:**
- **LED blinks rapidly** (5Hz) while waiting for release - visual feedback without serial monitor
- **Guarantees button is HIGH** before sleep entry
- **ext1 always configured for wake-on-LOW** (next button press)
- **Next wake is guaranteed to be NEW button press** - not the countdown hold
- **Simple and bulletproof** - no complex state machine
- **User-friendly** - clear visual cue to release button

**User Experience Flow:**
1. User holds button 6 seconds → Countdown ("5... 4... 3... 2... 1...")
2. LED blinks fast (5Hz) → Visual cue: "Release the button now"
3. User releases button → Device sleeps immediately
4. Later: User presses button → Device wakes (guaranteed NEW press)

**Why This Works:**

The solution exploits the level-triggered nature of ext1 rather than fighting it:

1. **Before sleep**: Ensure button is HIGH (not pressed)
2. **Configure ext1**: Wake when GPIO goes LOW (button pressed)
3. **Sleep entry**: Wake condition is FALSE (button is HIGH)
4. **Sleep state**: Device waits for wake condition to become TRUE
5. **Wake event**: Only occurs when button transitions from HIGH → LOW
6. **Guarantee**: This can only happen with a NEW button press

**Alternatives Considered:**

1. **Immediate re-sleep with state checking**:
   - ❌ Rejected: Device stuck sleeping after button release
   - ❌ Rejected: Can't detect new press after re-sleeping
   - ❌ Rejected: Fundamental misunderstanding of level-triggered wake

2. **State machine with wake-on-HIGH**:
   - ❌ Rejected: ESP32-C6 ext1 limitations
   - ❌ Rejected: Unreliable wake-on-HIGH behavior
   - ❌ Rejected: Excessive complexity for medical device

3. **Wait-for-release with LED blink**:
   - ✅ Chosen: Simple and bulletproof
   - ✅ Chosen: Works within ESP32-C6 hardware limitations
   - ✅ Chosen: Visual feedback without serial monitor
   - ✅ Chosen: Guarantees wake-on-new-press

**Rationale:**

- **Hardware compatibility**: Works within ESP32-C6 ext1 limitations
- **Visual feedback**: LED blink provides user guidance without serial monitor
- **Guaranteed wake**: Next wake is always from NEW button press
- **Simple implementation**: No complex state machine or conditional wake logic
- **Predictable behavior**: Same wake pattern every time
- **Medical device safety**: Reliable, testable, maintainable
- **JPL compliant**: Uses vTaskDelay() for timing, no busy-wait loops
- **User-friendly**: Clear visual indication of expected user action

**Implementation Pattern for Future Use:**

```c
/**
 * @brief Enter deep sleep with guaranteed wake-on-new-press
 * @return Does not return (device sleeps)
 * 
 * ESP32-C6 ext1 wake pattern:
 * 1. Check button state
 * 2. If LOW (held): Blink LED while waiting for release
 * 3. Once HIGH: Configure ext1 wake on LOW
 * 4. Enter deep sleep (button guaranteed released)
 * 5. Next wake guaranteed to be NEW button press
 * 
 * Visual feedback: LED blinks at 5Hz while waiting for release
 * No serial monitor required for user to know when to release
 * 
 * JPL Compliant: Uses vTaskDelay() for all timing
 */
esp_err_t enter_deep_sleep_with_wake_guarantee(void) {
    // Wait for button release if currently pressed
    if (gpio_get_level(GPIO_BUTTON) == 0) {
        // Blink LED at 5Hz (100ms on, 100ms off)
        while (gpio_get_level(GPIO_BUTTON) == 0) {
            gpio_set_level(GPIO_STATUS_LED, LED_ON);
            vTaskDelay(pdMS_TO_TICKS(100));
            gpio_set_level(GPIO_STATUS_LED, LED_OFF);
            vTaskDelay(pdMS_TO_TICKS(100));
        }
    }
    
    // Configure wake source (button press = LOW)
    uint64_t gpio_mask = (1ULL << GPIO_BUTTON);
    esp_sleep_enable_ext1_wakeup(gpio_mask, ESP_EXT1_WAKEUP_ANY_LOW);
    
    // Enter deep sleep
    esp_deep_sleep_start();
    return ESP_OK;  // Never reached
}
```

**JPL Compliance:**
- ✅ All delays use vTaskDelay() (no busy-wait loops)
- ✅ Bounded loop (only runs while button held)
- ✅ Predictable behavior (same pattern every time)
- ✅ Single entry/exit point
- ✅ Comprehensive error checking (wake configuration)
- ✅ Low cyclomatic complexity (simple conditional logic)

**Verification Strategy:**

1. **Hardware Test** (`test/button_deepsleep_test.c`):
   - Hold button through 5-second countdown
   - Verify LED blinks while waiting for release
   - Release button, verify device sleeps
   - Press button, verify device wakes
   - Verify wake reason is EXT1 (RTC GPIO)

2. **Edge Cases**:
   - Button released during countdown → Sleep immediately (no blink)
   - Button held indefinitely → LED blinks indefinitely (device waits)
   - Button bounces during release → Debouncing prevents false wake

3. **Power Consumption**:
   - Active (LED blinking): ~50mA
   - Deep sleep: <1mA
   - Wake latency: <2 seconds

**Reference Implementation:**
- **File**: `test/button_deepsleep_test.c`
- **Build**: `pio run -e button_deepsleep_test -t upload`
- **Documentation**: `test/BUTTON_DEEPSLEEP_TEST_GUIDE.md`

**Integration with Main Application:**

This pattern must be used for all button-triggered deep sleep scenarios:
- Session timeout → automatic sleep (no button hold)
- User-initiated sleep → 5-second button hold with wait-for-release
- Emergency shutdown → immediate motor coast, then sleep with wait-for-release
- Battery low → warning, then sleep with wait-for-release

**Benefits:**

✅ **Solves hardware limitation** - works within ESP32-C6 ext1 constraints
✅ **Visual user feedback** - no serial monitor needed
✅ **Guaranteed reliable wake** - always from NEW button press
✅ **Simple and maintainable** - no complex state machine
✅ **Medical device appropriate** - predictable, testable behavior
✅ **JPL compliant** - no busy-wait loops
✅ **Power efficient** - minimal active time before sleep
✅ **User-friendly** - clear indication of expected action

### AD024: LED Strip Component Version Selection

**Decision**: Use led_strip version 2.5.x family (specifically ^2.5.0) for WS2812B control

**Current Version**: 2.5.5 (automatically updated from 2.5.0 via semver range)

**Rationale:**

**Stability and Maturity:**
- Version 2.5.x is the mature, production-tested branch (>1M downloads)
- Over 1 year of field deployment with extensive bug fixes
- No known critical issues with ESP32-C6 or WS2812B operation
- Latest 2.5.5 includes build time optimizations for ESP-IDF v5.5.0

**API Simplicity:**
- Clean, intuitive API using `LED_PIXEL_FORMAT_GRB` enum style
- Configuration structure straightforward and readable:
  ```c
  led_strip_config_t strip_config = {
      .strip_gpio_num = GPIO_WS2812B_DIN,
      .max_leds = WS2812B_NUM_LEDS,
      .led_pixel_format = LED_PIXEL_FORMAT_GRB,  // Simple, clear
      .led_model = LED_MODEL_WS2812,
      .flags.invert_out = false,
  };
  ```

**JPL Coding Standards Alignment:**
- Safety-critical medical device prioritizes stability over cutting-edge features
- "If it ain't broke, don't fix it" principle
- Proven code more valuable than latest version for therapeutic applications
- Reduces risk of introducing bugs during development

**Version 3.x Breaking Changes (Why Not to Upgrade):**
- Field name changed: `led_pixel_format` → `color_component_format`
- Enum renamed: `LED_PIXEL_FORMAT_GRB` → `LED_STRIP_COLOR_COMPONENT_FMT_GRB`
- These are cosmetic API changes with zero functional benefit
- Only new feature: custom color component ordering (irrelevant for standard WS2812B GRB format)
- Migration effort: 1-2 hours across all test files
- Testing overhead: Full regression testing required after migration
- **No therapeutic or functional improvements gained**

**Automatic Security Updates:**
- Dependency specification `^2.5.0` receives automatic patch updates
- Already received 2.5.0 → 2.5.5 updates automatically
- Stays within 2.5.x family (no breaking changes)
- Future 2.5.6, 2.5.7, etc. will auto-update if released

**ESP-IDF Compatibility:**
- Version 2.5.x supports ESP-IDF v4.4 through v5.5.0
- Version 3.x drops ESP-IDF v4.x support (not relevant for this project)
- Both versions fully compatible with ESP-IDF v5.5.0 (our target)

**Implementation Pattern:**
```yaml
# File: src/idf_component.yml
dependencies:
  espressif/led_strip: "^2.5.0"  # Allows 2.5.x patches, blocks 3.x
```

**Working Code Pattern:**
```c
// Current working pattern (2.5.x)
led_strip_config_t strip_config = {
    .strip_gpio_num = GPIO_WS2812B_DIN,
    .max_leds = WS2812B_NUM_LEDS,
    .led_pixel_format = LED_PIXEL_FORMAT_GRB,  // ✅ 2.5.x API
    .led_model = LED_MODEL_WS2812,
    .flags.invert_out = false,
};

led_strip_rmt_config_t rmt_config = {
    .clk_src = RMT_CLK_SRC_DEFAULT,
    .resolution_hz = 10 * 1000 * 1000,  // 10MHz
    .flags.with_dma = false,
};

ESP_ERROR_CHECK(led_strip_new_rmt_device(&strip_config, &rmt_config, &led_strip));
```

**Files Using LED Strip:**
- `test/ws2812b_test.c` - Hardware validation test
- `test/single_device_demo_test.c` - Research study test with integrated LED
- Future bilateral application files

**Alternatives Considered:**

1. **Version 3.0.1 (latest stable):**
   - ❌ Rejected: Breaking API changes require code modifications
   - ❌ Rejected: Only new feature is custom color ordering (not needed)
   - ❌ Rejected: Migration effort with zero functional benefit
   - ❌ Rejected: Increases risk during critical development phase

2. **Lock to specific version 2.5.5:**
   - ❌ Rejected: Loses automatic security patch updates
   - ❌ Rejected: `^2.5.0` range is safer (gets patches automatically)
   - ✅ Alternative acceptable if version stability critical

3. **Version 3.x range specification:**
   - ❌ Rejected: Would receive future breaking changes automatically
   - ❌ Rejected: Not appropriate for safety-critical medical device

**Migration Path (Future):**
If version 3.x becomes necessary (unlikely scenarios):
- ESP-IDF v6.x forces 3.x requirement
- Critical bug only fixed in 3.x
- Version 2.5.x reaches end-of-life

Migration checklist:
1. Update `src/idf_component.yml`: `espressif/led_strip: "^3.0.1"`
2. Update all `led_strip_config_t` initializations:
   - Replace: `led_pixel_format` → `color_component_format`
   - Replace: `LED_PIXEL_FORMAT_GRB` → `LED_STRIP_COLOR_COMPONENT_FMT_GRB`
3. Clean build: `rm -rf managed_components/espressif__led_strip && pio run -t clean`
4. Test on hardware: Full regression testing of WS2812B functionality

**Decision Timeline:**
- October 2025: Selected version 2.5.0 for initial implementation
- November 2025: Documented as AD024 after version 3.x investigation
- Auto-updated to 2.5.5 via semver range specification

**Benefits:**

✅ **Stable and proven** - Over 1 year of production use
✅ **JPL compliant** - Prioritizes stability over bleeding-edge features
✅ **Zero migration overhead** - Code works today, continues working
✅ **Automatic security updates** - Patch versions auto-update
✅ **Simple API** - Clean, readable configuration
✅ **Medical device appropriate** - Risk reduction for safety-critical system
✅ **Development velocity** - No time spent on unnecessary refactoring
✅ **Focus on therapeutics** - Engineering effort on bilateral stimulation, not library upgrades

**Verification:**
- Current build: ✅ Successful with 2.5.5
- Hardware testing: ✅ WS2812B control working correctly
- Test files: ✅ ws2812b_test.c and single_device_demo_test.c validated
- Deep sleep integration: ✅ LED power management verified

**Related Documentation:**
- Full version analysis: `docs/led_strip_version_analysis.md` (detailed comparison)
- Component manifest: `src/idf_component.yml` (dependency specification)
- Test implementation: `test/ws2812b_test.c` (reference code pattern)

### AD025: Dual-Device Wake Pattern and UX Design

**Decision**: Instant button press to wake from deep sleep (no hold required) with GPIO15 LED indication for NVS clear

**Problem Statement:**

Original design specified 2-second button hold to wake from deep sleep. However, hardware testing with dual-device use case revealed this creates poor user experience:
- User must coordinate 2-second hold on BOTH devices simultaneously
- Difficult to synchronize without visual feedback
- Creates frustration and delays session start
- Hardware already supports instant wake via ESP32-C6 ext1 (per AD023)

**Solution:**

**Instant Wake (No Hold):**
- Single button press immediately wakes device from deep sleep
- Both devices can be woken simultaneously with natural two-handed button press
- Fast, intuitive user experience for dual-device operation
- Leverages existing AD023 wait-for-release pattern (unchanged)

**Button Hold Sequence (Updated):**
```
0-5 seconds:   Normal hold, no action
5 seconds:     Emergency shutdown ready (purple LED blink via therapy light)
5-10 seconds:  Continue holding (purple blink continues, release triggers shutdown)
10 seconds:    NVS clear triggered (GPIO15 solid on, only first 30s of boot per AD013)
Release:       Execute action (shutdown at 5s+, NVS clear at 10s+)
```

**GPIO15 LED Indication for NVS Clear:**
- GPIO15 status LED turns solid on at 10-second hold mark
- Only active during first 30 seconds of boot (per AD013 security window)
- Clear visual indication distinct from purple therapy light blink
- Prevents accidental NVS clear during therapy sessions

**Dual-Device Simultaneous Wake Workflow:**
1. Both devices in deep sleep
2. User presses button on both devices (natural two-handed press)
3. Both devices wake instantly (< 100ms)
4. Devices discover each other via BLE (< 30s)
5. Session ready to begin

**Hardware Compatibility:**
- ESP32-C6 ext1 wake already supports instant wake (level-triggered on GPIO LOW)
- AD023 wait-for-release pattern unchanged (applies to shutdown, not wake)
- No firmware changes needed beyond removing 2-second wake hold logic

**Rationale:**
- **User experience**: Instant wake feels responsive, professional
- **Dual-device coordination**: Eliminates synchronization difficulty
- **Hardware lessons learned**: Original 2-second spec written before hardware testing
- **Safety preserved**: Emergency shutdown still requires 5-second hold (prevents accidents)
- **NVS clear indication**: GPIO15 solid on provides clear visual feedback (distinct from purple blink)
- **Security window**: 10s NVS clear only works in first 30s of boot (AD013)

**Alternatives Considered:**

1. **Keep 2-second wake hold:**
   - ❌ Rejected: Poor UX for dual-device operation
   - ❌ Rejected: Hardware already supports instant wake

2. **1-second wake hold (compromise):**
   - ❌ Rejected: Still requires synchronization
   - ❌ Rejected: Adds complexity without benefit

3. **Instant wake with accidental press protection:**
   - ✅ Chosen: Deep sleep itself prevents accidental wake (device must be sleeping)
   - ✅ Chosen: Natural use case - user intends to wake device when pressing button

**Security Considerations:**

**NVS Clear Protection (Unchanged):**
- 10-second hold required (prevents accidental clear)
- Only works in first 30 seconds after boot (AD013)
- GPIO15 solid on provides clear warning
- After 30s boot window, 10s hold does nothing (safe for therapy sessions)

**Emergency Shutdown (Unchanged):**
- 5-second hold required (prevents accidental shutdown during therapy)
- Purple LED blink provides visual countdown
- Wait-for-release pattern ensures clean deep sleep entry (AD023)

**JPL Compliance:**
- No busy-wait loops (instant wake uses hardware ext1)
- Deterministic wake behavior (level-triggered)
- Predictable timing (< 100ms wake latency)

**Documentation Updates:**
- UI001 in requirements_spec.md: Updated to reflect instant wake
- FR001: Added automatic role recovery after 30s timeout
- FR003: Added automatic session start, background pairing
- FR004: Clarified fire-and-forget emergency shutdown
- PF002: Removed obsolete wake time specification

**Verification Strategy:**
- Hardware test: Press both device buttons simultaneously
- Measure wake latency: < 100ms from button press to CPU active
- BLE discovery: < 30s from wake to paired
- NVS clear test: GPIO15 solid on during 10s hold (first 30s only)

**Benefits:**

✅ **Instant response** - Professional, responsive UX
✅ **Dual-device friendly** - Natural two-handed simultaneous wake
✅ **Hardware lessons applied** - Spec updated based on real testing
✅ **Safety preserved** - Emergency shutdown still protected by 5s hold
✅ **Clear NVS indication** - GPIO15 solid on distinct from purple blink
✅ **Simple implementation** - Hardware already supports instant wake

### AD026: BLE Automatic Role Recovery

**Decision**: "Survivor becomes server" - automatic role switching after 30-second BLE disconnection timeout

**Note (November 11, 2025):** Single-device fallback behavior superseded by AD028 (Command-and-Control with Synchronized Fallback). Role recovery mechanism remains valid.

**Problem Statement:**

Original design had manual role assignment (first device = server, second = client) but no automatic recovery if BLE connection lost:
- If server device fails, client device stuck waiting
- If client device fails, server has no reconnection target
- User must manually power cycle both devices to reset roles
- Interrupts therapy session unnecessarily

**Solution:**

**Automatic Role Recovery Protocol:**

**Server Failure Scenario:**
1. Server device fails or is powered off
2. Client detects BLE disconnection
3. Client continues in single-device mode (forward/reverse alternating)
4. After 30-second timeout, client switches to server role
5. Client (now server) begins advertising
6. When original server returns, it discovers new server and becomes client
7. Session continues in bilateral mode

**Client Failure Scenario:**
1. Client device fails or is powered off
2. Server detects BLE disconnection
3. Server continues in single-device mode (forward/reverse alternating)
4. Server continues advertising for new client
5. When original client returns, it discovers server and reconnects as client
6. Session continues in bilateral mode

**"Survivor Becomes Server" Logic:**
```c
// Client device monitoring BLE connection
if (ble_connection_lost) {
    // Continue therapy in single-device mode
    motor_mode = SINGLE_DEVICE_ALTERNATING;

    // Start 30s timeout for role switch
    uint32_t timeout_start = xTaskGetTickCount();

    while (ble_connection_lost && !session_timeout) {
        // Continue single-device therapy
        motor_task_single_device();

        // Check if 30s elapsed
        if ((xTaskGetTickCount() - timeout_start) > pdMS_TO_TICKS(30000)) {
            // Switch to server role
            ble_role = BLE_ROLE_SERVER;
            ble_start_advertising();
            ESP_LOGI(TAG, "Role switch: Client → Server (survivor)");
            break;
        }

        vTaskDelay(pdMS_TO_TICKS(1000));  // Check every 1s
    }
}
```

**Pairing Data in NVS (Exception to AD011):**

AD011 states "no NVS state saving" but clarifies this means session state, not settings:
- ✅ Pairing data (peer MAC address) stored in NVS
- ✅ Mode 5 settings (frequency, duty cycle, LED color) stored in NVS
- ❌ Session state (mid-session at 15 minutes) NOT stored in NVS
- Rationale: Settings enable reconnection, state would resume mid-session (unsafe)

**Background Pairing in Single-Device Mode:**

While operating in single-device mode after disconnection:
- Motor task continues forward/reverse alternating pattern
- BLE task scans for peer device in background (low priority)
- If peer reappears, automatic reconnection and bilateral mode resume
- User experience: seamless transition from single to bilateral

**Rationale:**
- **Session continuity**: Therapy continues despite device failure
- **User experience**: No manual intervention required
- **Role flexibility**: "Survivor" takes charge to enable reconnection
- **Automatic recovery**: When failed device returns, bilateral mode resumes
- **NVS exception justified**: Pairing data enables reconnection (AD011 allows settings)

**Alternatives Considered:**

1. **No automatic role recovery:**
   - ❌ Rejected: User must manually reset both devices
   - ❌ Rejected: Interrupts therapy session unnecessarily

2. **Immediate role switch on disconnection:**
   - ❌ Rejected: 30s timeout allows transient interference recovery
   - ❌ Rejected: Too aggressive (BLE packet loss shouldn't trigger role switch)

3. **Manual role selection via button:**
   - ❌ Rejected: Adds UI complexity
   - ❌ Rejected: Requires user intervention during session

4. **30-second timeout with automatic switch:**
   - ✅ Chosen: Balances transient interference vs permanent failure
   - ✅ Chosen: Survivor takes server role automatically

**Coordination with FR001 (Automatic Pairing):**
- Power-on: Random 0-2000ms delay prevents simultaneous server attempts
- Disconnection: 30s timeout gives failed device time to return
- Reconnection: Failed device discovers new server and becomes client
- Symmetric: Works for both server and client failure scenarios

**JPL Compliance:**
- Timeout using vTaskDelay() (no busy-wait)
- Bounded loop (session timeout or reconnection)
- Deterministic behavior (30s timeout always)
- Fail-safe: Single-device mode always safe

**Documentation Updates:**
- FR001: Added automatic role recovery bullet points
- FR003: Added background pairing in single-device mode
- AD011: Clarified NVS pairing storage exception

**Verification Strategy:**
- Test server failure: Client switches to server after 30s
- Test client failure: Server continues advertising
- Test reconnection: Failed device becomes client when returning
- Test transient interference: < 30s packet loss doesn't trigger role switch

**Benefits:**

✅ **Session continuity** - Therapy not interrupted by device failure
✅ **Automatic recovery** - No user intervention required
✅ **Role flexibility** - Survivor takes charge
✅ **Balanced timeout** - 30s allows transient vs permanent failure distinction
✅ **NVS exception justified** - Pairing data enables reconnection (settings, not state)
✅ **Symmetric design** - Works for server or client failure

### AD027: Modular Source File Architecture

**Decision**: Hybrid task-based + functional modular architecture for production dual-device implementation

**Problem Statement:**

Current code organization uses monolithic single-file test programs:
- `test/single_device_demo_jpl_queued.c` - Phase 4 JPL-compliant (all code in one file)
- `test/single_device_ble_gatt_test.c` - BLE GATT server (all code in one file)
- Difficult to maintain as features grow
- Code reuse between single-device and dual-device modes challenging
- Clear separation of concerns needed for safety-critical development

**Solution:**

**Hybrid Architecture:**
- **Task modules** - Mirror FreeRTOS task structure (proven in BLE GATT test)
- **Support modules** - Functional components reusable across tasks
- **Single header per module** - Clear interface (motor_task.c + motor_task.h)
- **State-based behavior** - Single-device vs dual-device is STATE, not separate code

**File Structure:**

```
src/
├── main.c                      # app_main(), initialization, task creation
├── motor_task.c/h              # Motor control task (FreeRTOS task)
├── ble_task.c/h                # BLE advertising/connection task
├── button_task.c/h             # Button monitoring task
├── battery_monitor.c/h         # Battery voltage/percentage (support)
├── nvs_manager.c/h             # NVS read/write/clear (support)
├── power_manager.c/h           # Light sleep/deep sleep config (support)
└── led_control.c/h             # WS2812B + GPIO15 LED control (support)

include/
├── motor_task.h                # Public motor task interface
├── ble_task.h                  # Public BLE task interface
├── button_task.h               # Public button task interface
├── battery_monitor.h           # Public battery monitor interface
├── nvs_manager.h               # Public NVS manager interface
├── power_manager.h             # Public power manager interface
└── led_control.h               # Public LED control interface
```

**Module Responsibilities:**

**Task Modules (FreeRTOS Tasks):**

**motor_task.c/h:**
- Owns motor control FreeRTOS task
- Implements bilateral stimulation timing (server/client coordination)
- Single-device mode (forward/reverse alternating)
- Role-based behavior: SERVER, CLIENT, STANDALONE (state variable)
- Message queue for mode changes, BLE commands, shutdown
- Calls: battery_monitor (LVO check), led_control (therapy light), power_manager (sleep)

**ble_task.c/h:**
- Owns BLE FreeRTOS task
- NimBLE stack initialization and management
- Advertising lifecycle (IDLE → ADVERTISING → CONNECTED → SHUTDOWN)
- Role assignment and automatic recovery ("survivor becomes server")
- GATT server (optional, for mobile app configuration)
- Calls: nvs_manager (pairing data), motor_task (via message queue)

**button_task.c/h:**
- Owns button monitoring FreeRTOS task
- Button hold duration tracking (5s shutdown, 10s NVS clear)
- Emergency shutdown coordination (fire-and-forget)
- Deep sleep entry with wait-for-release pattern (AD023)
- Calls: motor_task (shutdown message), ble_task (shutdown message), nvs_manager (clear), led_control (purple blink), power_manager (deep sleep)

**Support Modules (Functional Components):**

**battery_monitor.c/h:**
- Battery voltage reading via ADC
- Percentage calculation (4.2V → 3.0V range)
- LVO detection (< 3.0V cutoff)
- Called by: motor_task (startup LVO check, periodic monitoring)

**nvs_manager.c/h:**
- NVS namespace management
- Pairing data storage (peer MAC address)
- Settings storage (Mode 5 custom parameters)
- Factory reset (clear all NVS data)
- Called by: ble_task (pairing), motor_task (settings), button_task (clear)

**power_manager.c/h:**
- Light sleep configuration (esp_pm_configure)
- Deep sleep entry (esp_deep_sleep_start)
- Wake source configuration (ext1 button wake)
- Called by: main.c (init), button_task (deep sleep)

**led_control.c/h:**
- WS2812B RGB LED control (if translucent case)
- GPIO15 status LED control (always available)
- Therapy light patterns (purple blink, mode indication)
- Called by: motor_task (therapy patterns), button_task (purple blink), main.c (boot sequence)

**Key Design Principles:**

**1. Single-Device vs Dual-Device as State:**
```c
// motor_task.c
typedef enum {
    MOTOR_ROLE_SERVER,      // Dual-device: server role (first half-cycle)
    MOTOR_ROLE_CLIENT,      // Dual-device: client role (second half-cycle)
    MOTOR_ROLE_STANDALONE   // Single-device: forward/reverse alternating
} motor_role_t;

static motor_role_t current_role = MOTOR_ROLE_STANDALONE;  // Start standalone

// Same motor_task code handles all three roles
void motor_task(void *arg) {
    while (session_active) {
        switch (current_role) {
            case MOTOR_ROLE_SERVER:
                // Execute server half-cycle, wait client half-cycle
                break;
            case MOTOR_ROLE_CLIENT:
                // Wait server half-cycle, execute client half-cycle
                break;
            case MOTOR_ROLE_STANDALONE:
                // Forward half-cycle, reverse half-cycle
                break;
        }
    }
}
```

**2. API Contract Alignment:**
Module filenames mirror API contracts in `docs/ai_context.md`:
- Motor Control API → `motor_task.c/h`
- BLE Manager API → `ble_task.c/h`
- Button Handler API → `button_task.c/h`
- Battery Monitor API → `battery_monitor.c/h`
- Power Manager API → `power_manager.c/h`
- Therapy Light API → `led_control.c/h` (renamed from "therapy_light" for brevity)

**3. Header File Strategy:**
Single public header per module:
- motor_task.h - Public functions, message queue handles, enums
- motor_task.c - Private static functions, task implementation
- No `_private.h` headers needed (use `static` for private functions)

**4. Module Dependencies:**
```
main.c
  ├─> motor_task ──> battery_monitor
  │                ├─> led_control
  │                └─> power_manager
  ├─> ble_task ────> nvs_manager
  │                └─> motor_task (message queue)
  └─> button_task ─> motor_task (message queue)
                    ├─> ble_task (message queue)
                    ├─> nvs_manager
                    ├─> led_control
                    └─> power_manager
```

**5. Message Queue Communication:**
Tasks communicate via FreeRTOS message queues (established pattern from BLE GATT test):
```c
// motor_task.h
typedef enum {
    MOTOR_MSG_MODE_CHANGE,
    MOTOR_MSG_EMERGENCY_SHUTDOWN,
    MOTOR_MSG_BLE_CONNECTED,
    MOTOR_MSG_BLE_DISCONNECTED,
    MOTOR_MSG_ROLE_CHANGE
} motor_msg_type_t;

extern QueueHandle_t motor_msg_queue;
```

**Rationale:**

**Why Hybrid (Task + Functional)?**
- ✅ Task modules map 1:1 to FreeRTOS tasks (clear ownership, proven structure)
- ✅ Support modules reusable across tasks (battery_monitor used by motor + BLE)
- ✅ Matches existing BLE GATT test structure (de-risk migration)
- ✅ API contracts remain meaningful (battery_monitor API = battery_monitor.c/h)
- ✅ Single-device vs dual-device unified (state variable, not separate code paths)

**Why Single Header Per Module?**
- ✅ Consistent naming (motor_task.c + motor_task.h)
- ✅ Clear public interface (header = API contract)
- ✅ Private functions via `static` (no `_private.h` complexity)
- ✅ Standard C project organization

**Why State-Based Behavior?**
- ✅ Same code handles server/client/standalone (reduces bugs)
- ✅ Role changes at runtime (automatic recovery, AD026)
- ✅ No conditional compilation (#ifdef SINGLE_DEVICE / DUAL_DEVICE)
- ✅ Easier testing (single test suite covers all modes)

**Migration Path from Monolithic Test Files:**

**Phase 1: Extract Support Modules**
1. Create battery_monitor.c/h from BLE GATT test battery code
2. Create nvs_manager.c/h from NVS storage code
3. Create power_manager.c/h from sleep management code
4. Create led_control.c/h from WS2812B + GPIO15 code
5. Test: Verify support modules work independently

**Phase 2: Extract Task Modules**
1. Create motor_task.c/h from motor_task function + state machine
2. Create ble_task.c/h from ble_task function + NimBLE init
3. Create button_task.c/h from button_task function + state machine
4. Test: Verify tasks communicate via message queues

**Phase 3: Create Main**
1. Create main.c with app_main()
2. Initialize all modules
3. Create FreeRTOS tasks
4. Test: Full system integration

**Build System Integration:**

ESP-IDF CMake naturally supports this structure:
```cmake
# src/CMakeLists.txt
idf_component_register(
    SRCS
        "main.c"
        "motor_task.c"
        "ble_task.c"
        "button_task.c"
        "battery_monitor.c"
        "nvs_manager.c"
        "power_manager.c"
        "led_control.c"
    INCLUDE_DIRS
        "."
        "include"
    REQUIRES
        nvs_flash
        esp_adc
        driver
        led_strip
)
```

**JPL Compliance Maintained:**
- ✅ No dynamic memory allocation (all static/stack)
- ✅ Fixed loop bounds (all while loops have exit conditions)
- ✅ vTaskDelay() for all timing (no busy-wait)
- ✅ Watchdog feeding (task-level subscription)
- ✅ Explicit error checking (ESP_ERROR_CHECK wrapper)
- ✅ Comprehensive logging (ESP_LOGI throughout)

**Test Strategy Preserved:**

Test files remain monolithic for hardware validation:
- `test/single_device_demo_jpl_queued.c` - Baseline JPL compliance test
- `test/single_device_ble_gatt_test.c` - BLE GATT hardware validation
- `test/battery_voltage_test.c` - Battery monitoring validation

Production code uses modular architecture:
- `src/main.c` + task/support modules

**Alternatives Considered:**

**1. Pure Functional (No Task Modules):**
- ❌ Rejected: Doesn't mirror FreeRTOS task structure
- ❌ Rejected: Harder to map to existing BLE GATT test code
- ❌ Rejected: Task ownership unclear (who owns motor_task function?)

**2. Pure Task-Based (All Modules Are Tasks):**
- ❌ Rejected: Battery monitor doesn't need dedicated task
- ❌ Rejected: NVS manager doesn't need dedicated task
- ❌ Rejected: Wastes FreeRTOS resources (stack per task)

**3. Monolithic with #ifdef SINGLE_DEVICE / DUAL_DEVICE:**
- ❌ Rejected: Maintenance nightmare (two code paths)
- ❌ Rejected: Violates "single-device shouldn't deviate from dual-device" requirement
- ❌ Rejected: Harder testing (need to test both #ifdef paths)

**4. Hybrid Task + Functional (Chosen):**
- ✅ Chosen: Best of both worlds
- ✅ Chosen: Matches proven BLE GATT test structure
- ✅ Chosen: Single-device vs dual-device as state (not separate code)

**Documentation Updates:**
- ai_context.md: Added implementation mapping note to API Contracts section
- requirements_spec.md: No changes needed (functional requirements unchanged)
- This AD documents modular architecture for dual-device implementation

**Verification Strategy:**
- Extract battery_monitor module first (simplest, most isolated)
- Verify API compatibility with existing test code
- Incrementally migrate other modules
- Maintain test files as monolithic validation baseline
- Compare production modular build vs test monolithic build (behavior identical)

**Benefits:**

✅ **Maintainability** - Clear module boundaries, easier code navigation
✅ **Reusability** - Support modules shared across tasks
✅ **Testability** - Modules testable independently
✅ **Proven structure** - Mirrors successful BLE GATT test implementation
✅ **Unified behavior** - Single-device vs dual-device as state, not separate code
✅ **API alignment** - Module names match API contracts (clear documentation)
✅ **Migration path** - Incremental refactoring from monolithic test files
✅ **JPL compliant** - All standards maintained throughout modular architecture

### AD028: Command-and-Control with Synchronized Fallback Architecture

**Date:** November 11, 2025

**Status:** Approved

**Context:**

Initial dual-device architecture (AD026) specified immediate fallback to single-device mode on BLE disconnection. User requested analysis of time-synchronized independent operation as an alternative. Mathematical analysis revealed time-sync would cause safety violations (overlapping stimulation) after 15-20 minutes due to crystal drift and FreeRTOS jitter.

**Decision:**

Adopt Command-and-Control with Synchronized Fallback architecture for dual-device bilateral stimulation.

**Architecture:**

```
Normal Operation (BLE Connected):
Server Device                Client Device
Check messages →             Receive BLE command
Send BLE "FORWARD" →         Process command
Forward active (125ms)       Wait for next command
Send BLE "COAST" →          Process command
Coast (375ms)               Coast (375ms)
Send BLE "REVERSE" →        Process command
Coast continues             Reverse active (125ms)
                           Coast (375ms)

Synchronized Fallback Phase 1 (0-2 minutes after disconnect):
Server Device                Client Device
Detect BLE loss →           Detect BLE loss
Continue rhythm (SERVER)    Continue rhythm (CLIENT)
Forward → Coast →           Coast → Reverse →
Use last timing ref         Use last timing ref
                           ↓
Fallback Phase 2 (2+ minutes, remainder of session):
Server Device                Client Device
Forward only (125ms on)     Reverse only (125ms on)
Coast (375ms)               Coast (375ms)
Repeat assigned role        Repeat assigned role
No alternation              No alternation
Reconnect attempt/5min      Reconnect attempt/5min
                           ↓
Session Complete (60-90 minutes):
Both devices → Deep Sleep
```

**Key Features:**

1. **Command-and-Control During Normal Operation:**
   - Server controls all timing decisions
   - Client executes commands immediately upon receipt
   - Guarantees non-overlapping stimulation (FR002 safety requirement)
   - 50-100ms BLE latency is therapeutically insignificant

2. **Synchronized Fallback Phase 1 (0-2 minutes):**
   - Continue established bilateral rhythm using last timing reference
   - Maximum drift over 2 minutes: ±1.2ms (negligible)
   - Provides seamless therapy during brief disconnections
   - Both devices maintain alternating pattern

3. **Fallback Phase 2 (2+ minutes to session end):**
   - Server continues forward-only stimulation (assigned role)
   - Client continues reverse-only stimulation (assigned role)
   - No alternation within each device - just repeat assigned role
   - Handles both battery death and 2.4GHz interference scenarios
   - Non-blocking reconnection attempt every 5 minutes
   - If reconnection succeeds, resume command-and-control seamlessly

4. **Session Completion:**
   - Both devices enter deep sleep after 60-90 minute session
   - Ensures predictable battery management
   - Clear session boundaries for therapeutic practice

**Implementation:**

```c
// Fallback state management
typedef struct {
    uint32_t disconnect_time;        // When BLE disconnected
    uint32_t last_command_time;      // Timestamp of last server command
    uint32_t last_reconnect_attempt; // Last reconnection attempt
    uint16_t established_cycle_ms;   // Current cycle period (e.g., 500ms)
    uint16_t established_duty_ms;    // Current duty cycle (e.g., 125ms)
    motor_role_t fallback_role;      // MOTOR_ROLE_SERVER or MOTOR_ROLE_CLIENT
    bool phase1_sync;                 // True during 2-minute sync phase
} fallback_state_t;

// Fallback phase management
uint32_t now = xTaskGetTickCount();
uint32_t disconnect_duration = now - fallback_state.disconnect_time;

if (disconnect_duration < pdMS_TO_TICKS(120000)) {
    // Phase 1: Maintain synchronized bilateral pattern
    continue_bilateral_rhythm();
} else {
    // Phase 2: Continue in assigned role only
    fallback_state.phase1_sync = false;
    if (fallback_state.fallback_role == MOTOR_ROLE_SERVER) {
        motor_forward_only();  // No reverse
    } else {
        motor_reverse_only();  // No forward
    }

    // Periodic reconnection attempts (non-blocking)
    if ((now - fallback_state.last_reconnect_attempt) > pdMS_TO_TICKS(300000)) {
        ble_attempt_reconnect_nonblocking();
        fallback_state.last_reconnect_attempt = now;
    }
}
```

**Safety Analysis:**

- **No Overlap Risk:** Command-and-control guarantees sequential operation
- **Minimal Drift During Fallback:** ±1.2ms over 2 minutes is imperceptible
- **Automatic Recovery:** Falls back to safe single-device mode after 2 minutes
- **User Notification:** LED/haptic feedback indicates mode changes

**Alternatives Rejected:**

1. **Time-Synchronized Independent Operation:**
   - Crystal drift (±10 PPM) + FreeRTOS jitter = ±1944ms over 20 minutes
   - Would cause overlapping stimulation (safety violation)
   - Complex NTP-style time sync adds unnecessary complexity

2. **Immediate Fallback (AD026):**
   - Interrupts therapy on any BLE glitch
   - Poor user experience during brief disconnections
   - Superseded by this synchronized fallback approach

**Supersedes:** AD026 (immediate fallback behavior)

---

### AD029: Relaxed Timing Specification

**Date:** November 11, 2025

**Status:** Approved

**Context:**

Original specification (DS004) required ±10ms timing accuracy based on theoretical precision goals. Real-world analysis shows this is unnecessarily strict given human perception thresholds (100-200ms) and therapeutic mechanism (bilateral alternation, not precise simultaneity).

**Decision:**

Relax timing specification from ±10ms to ±100ms for bilateral coordination.

**Rationale:**

1. **Human Perception Threshold:** 100-200ms timing differences are imperceptible
2. **Therapeutic Mechanism:** EMDR requires bilateral alternation, not simultaneity
3. **BLE Latency Reality:** 50-100ms latency is inherent in BLE notifications
4. **Proven Clinical Devices:** Commercial EMDR devices operate with similar tolerances
5. **Implementation Simplicity:** Allows simpler, more reliable architecture

**Updated Specification:**

```
DS004: Bilateral Timing Coordination
Old: ±10ms synchronization accuracy
New: ±100ms synchronization accuracy

FR003: Non-Overlapping Bilateral Stimulation
Old: Immediate fallback on BLE loss
New: Synchronized fallback for 2 minutes, then single-device mode
```

**Impact:**

- **Simplified Implementation:** No complex time synchronization needed
- **Better User Experience:** No interruption during brief disconnections
- **Maintained Safety:** Still prevents overlapping stimulation
- **Therapeutic Efficacy:** No impact on EMDR effectiveness

**Verification:**

User testing confirmed no perceptible difference between:
- Perfect synchronization (0ms offset)
- Command-and-control (50-100ms offset)
- Manual mode switching (attempted half-cycle alignment)

**Benefits:**

✅ **Simpler Code:** No NTP-style time sync complexity
✅ **Better Reliability:** Fewer edge cases and failure modes
✅ **Improved UX:** Uninterrupted therapy during brief disconnections
✅ **Maintained Safety:** Non-overlapping guarantee preserved
✅ **Proven Adequate:** Matches commercial device tolerances

---

### AD030: BLE Bilateral Control Service Architecture

**Date:** November 11, 2025

**Status:** Approved

**Context:**

Current implementation (`single_device_ble_gatt_test.c`) provides Configuration Service for mobile app control but lacks device-to-device Bilateral Control Service. Research platform requirements expand beyond standard EMDR parameters (0.5-2 Hz) to explore wider frequency ranges and stimulation patterns.

**Decision:**

Implement comprehensive BLE Bilateral Control Service for device-to-device coordination with research platform extensions.

**Service Architecture:**

**Bilateral Control Service** (Device-to-Device):
- **UUID**: `6E400001-B5A3-F393-E0A9-E50E24DCCA9E`
- **Purpose**: Real-time bilateral coordination between paired devices

**Characteristics** (14th byte increments: 01, 02, 03, etc.):

| UUID | Name | Type | Access | Range/Values | Purpose |
|------|------|------|--------|--------------|---------|
| `6E400101-B5A3-...` | Bilateral Command | uint8 | Write | 0-6 | START/STOP/SYNC/MODE_CHANGE/EMERGENCY/PATTERN |
| `6E400201-B5A3-...` | Total Cycle Time | uint16 | R/W | 500-4000ms | 0.25-2 Hz research range |
| `6E400301-B5A3-...` | Motor Intensity | uint8 | R/W | 30-80% | Safe research PWM range |
| `6E400401-B5A3-...` | Stimulation Pattern | uint8 | R/W | 0-2 | BILATERAL_FIXED/ALTERNATING/UNILATERAL |
| `6E400501-B5A3-...` | Device Role | uint8 | Read | 0-2 | SERVER/CLIENT/STANDALONE |
| `6E400601-B5A3-...` | Session Duration | uint32 | R/W | 1200000-5400000ms | 20-90 minutes |
| `6E400701-B5A3-...` | Sequence Number | uint16 | Read | 0-65535 | Packet loss detection |
| `6E400801-B5A3-...` | Emergency Shutdown | uint8 | Write | 1 | Fire-and-forget safety |
| `6E400901-B5A3-...` | Duty Cycle | uint8 | R/W | 10-50% | Timing pattern (50% max prevents motor overlap) |

**Research Platform Stimulation Patterns:**

1. **BILATERAL_FIXED** (Standard EMDR):
```
Server: Always FORWARD stimulation
Client: Always REVERSE stimulation
Time     Server    Client
0-250    ON        OFF
250-500  OFF       ON
500-750  ON        OFF
750-1000 OFF       ON
```

2. **BILATERAL_ALTERNATING** (Research Mode):
```
Both devices alternate direction each cycle
Time     Server         Client
0-250    FORWARD ON     OFF
250-500  OFF           REVERSE ON
500-750  REVERSE ON    OFF
750-1000 OFF          FORWARD ON
```

3. **UNILATERAL** (Control Studies):
```
Only one device active (for research controls)
Server: Normal operation
Client: Remains OFF
```

**Extended Research Parameters:**

**Frequency Range** (0.25-2 Hz):
- Ultra-slow: 0.25 Hz (4000ms cycle) - research into slow processing
- Slow: 0.5 Hz (2000ms cycle) - standard EMDR minimum
- Standard: 1 Hz (1000ms cycle) - typical therapeutic rate
- Fast: 1.5 Hz (667ms cycle) - enhanced processing
- Ultra-fast: 2 Hz (500ms cycle) - standard EMDR maximum

**Safety Constraints:**
- Motor PWM: 0-80% (0% = LED-only mode, 80% max prevents overheating)
- Duty Cycle: 10-50% (timing pattern, 50% max prevents motor overlap in single-device bilateral alternation)
- Non-overlapping: Time-window separation prevents overlap (devices/directions have sequential windows)

**UUID Assignment Rationale:**

Using 14th byte (position 13 in array) for characteristic differentiation:
```c
// Base service UUID: 6E400001-B5A3-F393-E0A9-E50E24DCCA9E
// Characteristic: 6E400X01-B5A3-... where X increments
static const ble_uuid128_t bilateral_cmd_uuid = BLE_UUID128_INIT(
    0x9e, 0xca, 0xdc, 0x24, 0x0e, 0xe5, 0xa9, 0xe0,
    0x93, 0xf3, 0xa3, 0xb5, 0x01, 0x01, 0x40, 0x6e);
//                               ↑     ↑
//                           14th  13th (service)
```

**Integration with AD028 Synchronized Fallback:**

During BLE disconnection, devices use last known pattern setting:
- Phase 1 (0-2 min): Continue pattern with last timing reference
- Phase 2 (2+ min): Fallback based on pattern type:
  - BILATERAL_FIXED: Server=forward only, Client=reverse only
  - BILATERAL_ALTERNATING: Continue local alternation
  - UNILATERAL: Active device continues, inactive remains off

**Benefits:**

✅ **Research Flexibility:** Extended frequency range for studies
✅ **Pattern Variety:** Three distinct stimulation patterns
✅ **Safety First:** Hard limits on PWM (30-80%) and duty cycle
✅ **Clear UUID Scheme:** Incremental 14th byte for characteristics
✅ **Backward Compatible:** Maintains standard EMDR capabilities
✅ **Data Collection Ready:** Sequence numbers enable packet analysis

---

### AD031: Research Platform Extensions

**Date:** November 11, 2025

**Status:** Approved

**Context:**

Device serves dual purpose: clinical EMDR therapy tool AND research platform for studying bilateral stimulation parameters. Standard EMDR uses 0.5-2 Hz, but research requires extended ranges to explore therapeutic boundaries.

**Decision:**

Extend platform capabilities beyond standard EMDR while maintaining safety constraints.

**Research Extensions:**

**1. Extended Frequency Range (0.25-2 Hz vs Standard 0.5-2 Hz):**

**Rationale for 0.25 Hz (4000ms cycle):**
- Explore slow bilateral processing for trauma with dissociation
- Study attention and working memory at slower rates
- Investigate relationship between stimulation rate and processing speed
- Research applications for elderly or cognitively impaired populations

**Rationale for Full 2 Hz (500ms cycle):**
- Match fastest standard EMDR rate for complete compatibility
- Study rapid bilateral stimulation effects
- Research applications for ADHD and high-arousal states

**2. Bilateral Alternating Pattern:**

**Research Questions Enabled:**
- Does motor direction (forward vs reverse) affect therapeutic outcome?
- Is alternating direction more/less effective than fixed direction?
- How does direction change impact habituation?
- Can direction alternation reduce motor adaptation?

**Implementation:**
```c
// Each device alternates its own direction
typedef enum {
    RESEARCH_PATTERN_FIXED,        // Standard: Server=forward, Client=reverse
    RESEARCH_PATTERN_ALTERNATING,  // Both alternate direction each cycle
    RESEARCH_PATTERN_UNILATERAL    // Control: single device only
} research_pattern_t;
```

**3. Duty Cycle Research (10-50%):**

**Single-Device Bilateral Constraint:**
In single-device mode, one motor alternates forward/reverse in sequential half-cycles:
- **Cycle pattern:** [Forward active] → [Forward coast] → [Reverse active] → [Reverse coast]
- **Maximum 50% duty cycle** ensures adequate coast time between direction changes
- **Above 50% causes motor overlap:** Motor attempts to reverse before fully stopped, causing:
  - Mechanical stress from direction change while spinning
  - Potential current spikes and H-bridge stress
  - Poor haptic experience (no clear bilateral separation)

**Research Applications:**
- **10% = 50ms pulses:** Micro-stimulation studies, minimum perceptible timing pattern
- **25% = 125ms pulses:** Standard therapy baseline (4× battery life improvement vs continuous)
- **50% = 250ms pulses:** Maximum bilateral stimulation intensity without motor overlap

**Important Note:** Duty cycle controls TIMING pattern (when motor/LED are active), NOT motor strength. For LED-only mode (pure visual stimulation), set PWM intensity = 0% instead of duty = 0%.

**Safety Note:** 50% maximum is a **hard physical limit** for single-device bilateral alternation. Each half-cycle must allow both active time AND coast time. Dual-device mode (future) can support higher duty cycles since devices operate in separate time windows without direction reversals.

**4. Motor Intensity Research (0-80% PWM):**

**Safety Rationale:**
- **0% (LED-only mode):** Disables motor vibration while maintaining LED blink pattern (pure visual therapy)
- **10-30%:** Gentle stimulation for sensitive users
- **40-60%:** Standard therapeutic range
- **70-80%:** Strong stimulation (maximum prevents overheating and tissue irritation)
- **Research Range:** 80% variation allows comprehensive intensity studies

**5. Session Duration Flexibility (20-90 minutes):**

**Applications:**
- **20 minutes:** Minimum for research protocols
- **45 minutes:** Standard therapy session
- **60 minutes:** Extended therapy session
- **90 minutes:** Maximum research session

**6. Data Collection Capabilities:**

**Logged Parameters:**
- Timestamp of each stimulation cycle
- Actual vs commanded timing (drift analysis)
- BLE packet loss rate (sequence number gaps)
- Battery voltage during session
- Motor back-EMF readings (when implemented)
- Pattern changes mid-session

**Storage Format:**
```c
typedef struct {
    uint32_t timestamp_ms;
    uint16_t cycle_time_ms;
    uint8_t motor_intensity;
    uint8_t pattern_type;
    uint8_t device_role;
    uint16_t sequence_num;
    uint8_t battery_percent;
} research_data_point_t;
```

**7. Safety Constraints:**

**Hard Limits (Cannot Override):**
- PWM maximum: 80% (prevents motor damage)
- PWM minimum: 30% (ensures perception)
- Non-overlapping stimulation (safety-critical)
- Emergency shutdown always available

**Soft Limits (Configurable with Warning):**
- Session > 60 minutes: Requires confirmation
- Duty cycle > 40%: Warning about motor heating
- Frequency < 0.5 Hz: Outside standard EMDR range

**Research Protocol Support:**

**Example Protocol: Direction Preference Study**
```
1. Baseline: 5 min BILATERAL_FIXED at 1 Hz
2. Condition A: 5 min BILATERAL_ALTERNATING at 1 Hz
3. Rest: 2 min no stimulation
4. Condition B: 5 min BILATERAL_FIXED reversed roles
5. Data: Compare subjective ratings and physiological measures
```

**Example Protocol: Minimal Stimulation Study**
```
1. Standard: 10 min at 25% duty cycle, 1 Hz
2. Minimal: 10 min at 10% duty cycle, 1 Hz
3. Micro: 10 min at 10% duty cycle, 2 Hz
4. Data: Compare therapeutic efficacy
```

**Compliance Notes:**

- Research features require explicit opt-in via Configuration Service
- Standard EMDR mode uses only approved parameters (0.5-2 Hz, fixed pattern)
- Research mode displays clear indication via LED patterns
- All research data is anonymous (no patient identifiers)

**Future Research Directions:**

1. **Phase 2**: Integration with physiological sensors (HR, HRV, GSR)
2. **Phase 3**: Closed-loop stimulation based on physiological feedback
3. **Phase 4**: Machine learning optimization of parameters
4. **Phase 5**: Multi-site research protocol coordination

**Benefits:**

✅ **Scientific Rigor:** Controlled parameter manipulation
✅ **Safety Maintained:** Hard limits prevent harmful operation
✅ **Clinical + Research:** Dual-purpose platform
✅ **Open Source:** Enables collaborative research
✅ **Data-Driven:** Built-in logging for analysis
✅ **Expandable:** Architecture supports future sensors

---

### AD032: BLE Configuration Service Architecture

**Date:** November 11, 2025

**Status:** Approved

**Supersedes:** Test UUID scheme (`a1b2c3d4-e5f6-7890-a1b2-c3d4e5f6xxxx`)

**Context:**

Mobile app control requires a dedicated GATT service separate from Bilateral Control Service (AD030). Current implementation uses temporary test UUIDs which cause confusion and should be replaced with production UUIDs from day one. Configuration Service provides single point of control for motor parameters, LED control, and status monitoring for BOTH single-device and dual-device operation.

**Decision:**

Implement comprehensive BLE Configuration Service using production UUIDs with logical characteristic grouping.

**Service Architecture:**

**Configuration Service** (Mobile App Control):
- **UUID**: `6E400002-B5A3-F393-E0A9-E50E24DCCA9E` (13th byte = `02`)
- **Purpose**: Mobile app control for motor, LED, and status monitoring
- **Scope**: Used by both single-device and dual-device configurations

**Characteristics** (14th byte increments: 01, 02, 03... 0A, 0B):

| UUID | Name | Type | Access | Range/Values | Purpose |
|------|------|------|--------|--------------|---------|
| **MOTOR CONTROL GROUP** |
| `6E400102-B5A3-...` | Mode | uint8 | R/W/Notify | 0-4 | MODE_1HZ_50, MODE_1HZ_25, MODE_05HZ_50, MODE_05HZ_25, MODE_CUSTOM |
| `6E400202-B5A3-...` | Custom Frequency | uint16 | R/W | 25-200 | Hz × 100 (0.25-2.0 Hz research range) |
| `6E400302-B5A3-...` | Custom Duty Cycle | uint8 | R/W | 10-50% | Timing pattern (50% max, no overlap) |
| `6E400402-B5A3-...` | PWM Intensity | uint8 | R/W | 0-80% | Motor strength (0% = LED-only) |
| **LED CONTROL GROUP** |
| `6E400502-B5A3-...` | LED Enable | uint8 | R/W | 0-1 | 0=off, 1=on |
| `6E400602-B5A3-...` | LED Color Mode | uint8 | R/W | 0-1 | 0=palette, 1=custom RGB |
| `6E400702-B5A3-...` | LED Palette Index | uint8 | R/W | 0-15 | 16-color preset palette |
| `6E400802-B5A3-...` | LED Custom RGB | uint8[3] | R/W | RGB 0-255 | Custom color wheel RGB values |
| `6E400902-B5A3-...` | LED Brightness | uint8 | R/W | 10-30% | User comfort range (eye strain prevention) |
| **STATUS/MONITORING GROUP** |
| `6E400A02-B5A3-...` | Session Duration | uint32 | R/W | 1200-5400 sec | Target session length (20-90 min) |
| `6E400B02-B5A3-...` | Session Time | uint32 | R/Notify | 0-5400 sec | Elapsed session seconds (0-90 min) |
| `6E400C02-B5A3-...` | Battery Level | uint8 | R/Notify | 0-100% | Battery state of charge |

**LED Color Control Architecture:**

**Two-Mode System:**

1. **Palette Mode** (Color Mode = 0):
   - Uses 16-color preset palette (Red, Green, Blue, Yellow, etc.)
   - Mobile app selects via Palette Index (0-15)
   - Simple for users who want quick color selection
   - Palette defined in firmware (see `color_palette[]` in ble_manager.c)

2. **Custom RGB Mode** (Color Mode = 1):
   - Mobile app sends RGB values from color wheel/picker
   - Enables full-spectrum color selection
   - Allows precise color matching for therapeutic preferences
   - RGB values applied directly to WS2812B LED

**Brightness Application:**
```c
// Brightness is 10-30% for user comfort (eye strain prevention)
// Applied uniformly to all RGB channels regardless of color mode
uint8_t r_final = (source_r * led_brightness) / 100;
uint8_t g_final = (source_g * led_brightness) / 100;
uint8_t b_final = (source_b * led_brightness) / 100;
```

**Example:** Pure red RGB(255, 0, 0) at 20% brightness → RGB(51, 0, 0)

**Default Settings (First Boot):**
- Mode: MODE_1HZ_50 (standard 1 Hz bilateral)
- Custom Frequency: 100 (1.00 Hz)
- Custom Duty: 50%
- PWM Intensity: 75%
- LED Enable: false
- LED Color Mode: 1 (Custom RGB)
- LED Custom RGB: (255, 0, 0) Red
- LED Brightness: 20%
- Session Duration: 1200 seconds (20 minutes)

**NVS Persistence:**

**Saved Parameters (User Preferences):**
- Mode (uint8: 0-4) - Last used mode
- Custom Frequency (uint16: 25-200) - For Mode 5
- Custom Duty Cycle (uint8: 10-50%) - For Mode 5 (timing pattern)
- LED Enable (uint8: 0 or 1)
- LED Color Mode (uint8: 0 or 1) ← NEW
- LED Palette Index (uint8: 0-15)
- LED Custom RGB (uint8[3]: R, G, B) ← NEW
- LED Brightness (uint8: 10-30%)
- PWM Intensity (uint8: 0-80%, 0% = LED-only mode)
- Session Duration (uint32: 1200-5400 sec) ← NEW

**NVS Signature:** CRC32 of characteristic UUID endings and data types (detects structure changes)

**Migration Strategy:** Clear NVS on signature mismatch (simple, clean slate for structural changes)

**UUID Scheme Rationale:**

**Service Differentiation (13th byte):**
```
6E400001-... = Bilateral Control Service (device-to-device, AD030)
6E400002-... = Configuration Service (mobile app, AD032)
        ↑
   13th byte (service ID)
```

**Characteristic Differentiation (14th byte):**
```
6E400102-... = Characteristic 01 of service 02
6E400202-... = Characteristic 02 of service 02
        ↑  ↑
     14th 13th
```

**BLE Advertising Configuration:**

Mobile app discovery requires Configuration Service UUID in scan response data for efficient device filtering.

**Advertising Parameters:**
- **Connection Mode**: Undirected connectable (`BLE_GAP_CONN_MODE_UND`)
- **Discovery Mode**: General discoverable (`BLE_GAP_DISC_MODE_GEN`)
- **Interval Range**: 20-40ms (0x20-0x40)
- **Duration**: Forever (`BLE_HS_FOREVER`) until disconnect

**Advertising Packet Fields (31-byte limit):**

| Field | Value | Purpose | Location |
|-------|-------|---------|----------|
| **Device Name** | `EMDR_Pulser_XXXXXX` | Human-readable identification (last 3 MAC bytes) | Advertising |
| **Flags** | `0x06` | General discoverable + BR/EDR not supported | Advertising |
| **TX Power** | Auto | Signal strength indication | Advertising |
| **Service UUID** | `6E400002-B5A3-...` | Configuration Service UUID for app filtering | **Scan Response** |

**Service UUID in Scan Response:**

The Configuration Service UUID **MUST** be included in scan response data (not advertising packet) to:
- Avoid exceeding 31-byte advertising packet limit
- Enable mobile app filtering for EMDR devices only
- Allow automatic device discovery without manual scanning
- Support service-based connection validation before GATT discovery
- Comply with BLE best practices for service advertisement

**Implementation:**
```c
// In ble_on_sync() - Advertising packet (device name, flags, TX power)
rc = ble_gap_adv_set_fields(&fields);

// Scan response packet (Configuration Service UUID)
struct ble_hs_adv_fields rsp_fields;
memset(&rsp_fields, 0, sizeof(rsp_fields));
rsp_fields.uuids128 = &uuid_config_service;
rsp_fields.num_uuids128 = 1;
rsp_fields.uuids128_is_complete = 1;
rc = ble_gap_adv_rsp_set_fields(&rsp_fields);
```

**Re-advertising Strategy:**
- **Trigger**: Automatic on client disconnect
- **Delay**: 100ms after disconnect (Android compatibility)
- **Error Handling**: BLE task retry on failure (30-second heartbeat)
- **Recovery**: Automatic restart ensures discoverability

**Rationale:**
- PWAs and mobile apps can filter `navigator.bluetooth.requestDevice()` by service UUID
- Prevents users from seeing non-EMDR devices in scan results
- Reduces connection attempts to wrong devices (battery savings)
- Standard practice for service-oriented BLE applications

**Benefits:**

✅ **Production UUIDs:** No test UUID migration complexity
✅ **Clear Separation:** Configuration (AD032) vs Bilateral Control (AD030)
✅ **Logical Grouping:** Motor (4), LED (5), Status (3) = 12 characteristics
✅ **RGB Flexibility:** Palette presets AND custom color wheel support
✅ **Session Control:** Configurable duration (20-90 min) + real-time elapsed monitoring
✅ **Research Platform:** Full 0.25-2 Hz, 10-50% duty, 0-80% PWM (0%=LED-only)
✅ **User Comfort:** 10-30% LED brightness prevents eye strain
✅ **Persistent Preferences:** NVS saves user settings across power cycles
✅ **Future-Proof:** Architecture supports bilateral implementation without changes

**Integration Notes:**

- Configuration Service works identically for single-device and dual-device modes
- Dual-device coordination handled separately via Bilateral Control Service (AD030)
- Mobile app connects to ONE device's Configuration Service to control session
- LED Custom RGB mode is default (most users want color wheel control)
- Palette mode provides convenience for users who prefer presets

---

### AD033: LED Color Palette Standard

**Date:** November 13, 2025

**Status:** Approved

**Context:**

Mobile app control via BLE Configuration Service (AD032) includes a 16-color palette mode for WS2812B RGB LED control. During modular architecture implementation, a color palette mismatch was discovered between `ble_manager.c` (master palette) and `led_control.c` (hardware implementation) - colors 8-15 were completely different, which would cause incorrect LED colors when users selected palette indices via mobile app.

**Decision:**

Standardize on a single 16-color palette across all modules, with `ble_manager.c` as the authoritative source and `led_control.c` synchronized to match.

**16-Color Palette Standard:**

| Index | Color Name | RGB Values | Hex | Notes |
|-------|------------|------------|-----|-------|
| 0 | Red | (255, 0, 0) | #FF0000 | Primary colors |
| 1 | Green | (0, 255, 0) | #00FF00 | Primary colors |
| 2 | Blue | (0, 0, 255) | #0000FF | Primary colors |
| 3 | Yellow | (255, 255, 0) | #FFFF00 | Secondary colors |
| 4 | Cyan | (0, 255, 255) | #00FFFF | Secondary colors |
| 5 | Magenta | (255, 0, 255) | #FF00FF | Secondary colors |
| 6 | Orange | (255, 128, 0) | #FF8000 | Warm tones |
| 7 | Purple | (128, 0, 255) | #8000FF | Cool tones |
| 8 | Spring Green | (0, 255, 128) | #00FF80 | Nature colors |
| 9 | Pink | (255, 192, 203) | #FFC0CB | Soft colors |
| 10 | White | (255, 255, 255) | #FFFFFF | Neutral |
| 11 | Olive | (128, 128, 0) | #808000 | Earth tones |
| 12 | Teal | (0, 128, 128) | #008080 | Cool tones |
| 13 | Violet | (128, 0, 128) | #800080 | Cool tones |
| 14 | Turquoise | (64, 224, 208) | #40E0D0 | Cool tones |
| 15 | Dark Orange | (255, 140, 0) | #FF8C00 | Warm tones |

**Implementation:**

**Master Definition** (`ble_manager.c`):
```c
const rgb_color_t color_palette[16] = {
    {255, 0,   0,   "Red"},
    {0,   255, 0,   "Green"},
    {0,   0,   255, "Blue"},
    {255, 255, 0,   "Yellow"},
    {0,   255, 255, "Cyan"},
    {255, 0,   255, "Magenta"},
    {255, 128, 0,   "Orange"},
    {128, 0,   255, "Purple"},
    {0,   255, 128, "Spring Green"},
    {255, 192, 203, "Pink"},
    {255, 255, 255, "White"},
    {128, 128, 0,   "Olive"},
    {0,   128, 128, "Teal"},
    {128, 0,   128, "Violet"},
    {64,  224, 208, "Turquoise"},
    {255, 140, 0,   "Dark Orange"}
};
```

**Hardware Implementation** (`led_control.c`):
```c
const led_rgb_t led_color_palette[16] = {
    {255,   0,   0},  // 0: Red
    {0,   255,   0},  // 1: Green
    {0,     0, 255},  // 2: Blue
    {255, 255,   0},  // 3: Yellow
    {0,   255, 255},  // 4: Cyan
    {255,   0, 255},  // 5: Magenta
    {255, 128,   0},  // 6: Orange
    {128,   0, 255},  // 7: Purple
    {0,   255, 128},  // 8: Spring Green
    {255, 192, 203},  // 9: Pink
    {255, 255, 255},  // 10: White
    {128, 128,   0},  // 11: Olive
    {0,   128, 128},  // 12: Teal
    {128,   0, 128},  // 13: Violet
    {64,  224, 208},  // 14: Turquoise
    {255, 140,   0}   // 15: Dark Orange
};
```

**Usage Flow:**

1. **Mobile App**: User selects color from palette (sends index 0-15 via BLE)
2. **BLE Manager**: Stores `led_palette_index` in characteristic data
3. **LED Control**: Reads `ble_get_led_palette_index()` and looks up RGB from `led_color_palette[]`
4. **WS2812B**: Applies RGB with brightness scaling (10-30%) and sends to LED hardware

**Brightness Scaling:**

All RGB values are scaled by brightness percentage (10-30% range for user comfort):
```c
// Example: Red (255,0,0) at 20% brightness → (51,0,0)
uint8_t r_final = (color.r * brightness) / 100;
uint8_t g_final = (color.g * brightness) / 100;
uint8_t b_final = (color.b * brightness) / 100;
```

**Palette Design Rationale:**

- **0-2**: Primary colors (Red/Green/Blue) - Essential basics
- **3-5**: Secondary colors (Yellow/Cyan/Magenta) - RGB mixing completes
- **6-7**: Popular warm/cool tones (Orange/Purple) - User favorites
- **8-15**: Diverse extended palette - Nature colors, soft colors, earth tones, neutrals
- **Balanced distribution**: Warm tones (6,15), cool tones (7,12,13,14), nature (8,11), soft (9,10)

**Alternative Considered:**

**Custom RGB Mode** (Color Mode = 1) allows full-spectrum color selection via mobile app color wheel/picker, bypassing palette entirely. This provides unlimited color options but requires more complex UI. Palette mode is for users who prefer quick selection.

**Benefits:**

✅ **Consistency:** Mobile app → BLE → Hardware produces expected LED colors
✅ **User Experience:** What you select is what you get (WYSIWYG)
✅ **Maintenance:** Single source of truth for palette definition
✅ **Documentation:** Clear reference for mobile app developers
✅ **Flexibility:** 16 colors covers most therapeutic/preference needs
✅ **Fallback:** Users can always use Custom RGB mode for exact colors

**Integration Notes:**

- Palette is compile-time constant (no runtime modification needed)
- Mobile app should display palette preview using these exact RGB values
- BLE characteristic validates index 0-15, returns error for invalid indices
- Default palette index is 0 (Red) on first boot
- NVS saves last-used palette index across power cycles

---

### AD034: Documentation Versioning and Release Management (2025-11-13)

**Decision:** Implement unified semantic versioning for project documentation using v0.MAJOR.MINOR pre-release format.

**Rationale:**
- **Unified versioning**: All core docs share one version number, making out-of-sync documents immediately obvious
- **Pre-release format**: v0.x.x indicates active development; v1.0.0 for production-ready
- **Version bump triggers**: Minor (v0.x.Y) for doc updates/fixes; Major (v0.X.0) for features/architecture changes
- **Consistency**: Standardized header format across all core documentation
- **Traceability**: Git tags enable version checkout and GitHub releases

**Versioned Documents (Tier 1 - Core Project Docs):**
1. CLAUDE.md - AI reference guide
2. README.md - Main project documentation
3. QUICK_START.md - Consolidated quick start guide
4. BUILD_COMMANDS.md - Essential build commands reference
5. docs/architecture_decisions.md - Design decision record (this document)
6. docs/requirements_spec.md - Full project specification
7. docs/ai_context.md - API contracts and rebuild instructions

**Excluded from Versioning:**
- test/ directory documents (test-specific, evolve independently)
- Session summaries (already date-tracked)
- Archived documentation (frozen by nature)

**Standard Header Format:**
```markdown
# Document Title

**Version:** v0.1.0
**Last Updated:** 2025-11-13
**Status:** Production-Ready | In Development | Archived
**Project Phase:** Phase 4 Complete (JPL-Compliant)
```

**Version Bump Guidelines:**
- **v0.x.Y (Minor)**: Documentation updates, clarifications, typo fixes, content additions
- **v0.X.0 (Major)**: New features (BLE, dual-device), architecture changes, requirement updates
- **v1.0.0**: Production release (feature-complete, tested, documented)

**Git Tag Policy:**
- Create git tags for all minor and major version bumps
- Tag format: `v0.1.0`, `v0.2.0`, etc.
- Tag message includes brief description of changes

**CHANGELOG.md Tracking:**
- Track major project milestones only (not individual doc edits)
- Examples: BLE integration, Phase 4 completion, dual-device support
- Link to relevant session summaries and ADs

**Implementation Date:** 2025-11-13
**Initial Version:** v0.1.0 (Phase 4 Complete with BLE GATT production-ready)

**Benefits:**

✅ **Synchronization Detection**: Out-of-date docs are immediately visible (mismatched version numbers)
✅ **Release Management**: Git tags enable rollback to specific documentation versions
✅ **Change Tracking**: CHANGELOG.md provides high-level project milestone history
✅ **Collaboration**: Version numbers provide clear reference points for discussions
✅ **Maintenance**: Unified versioning reduces overhead compared to per-doc versioning

**Alternatives Considered:**

- **Per-document versioning**: Rejected due to complexity and synchronization challenges
- **Date-only tracking**: Rejected due to lack of semantic meaning (what changed?)
- **No versioning**: Rejected due to difficulty tracking when docs are out of sync

**Integration Notes:**

- When ANY core document is updated, bump version across ALL core docs (maintains unified version)
- Update CHANGELOG.md for major milestones only (not every doc edit)
- Create git tag after committing version bump
- Session summaries remain date-tracked (not versioned)

---

## Conclusion

This architecture provides a robust foundation for a safety-critical medical device while maintaining flexibility for future enhancements. The combination of ESP-IDF v5.5.0 and JPL coding standards (including no busy-wait loops) ensures both reliability and regulatory compliance for therapeutic applications.

The modular design with comprehensive API contracts enables distributed development while maintaining interface stability and code quality standards appropriate for medical device software. The 1ms FreeRTOS dead time implementation provides both hardware protection and watchdog feeding opportunities while maintaining strict JPL compliance.

AD023 documents the critical deep sleep wake pattern that ensures reliable button-triggered wake from deep sleep, solving the ESP32-C6 ext1 level-triggered wake limitation with a simple, user-friendly visual feedback pattern.

---

**This PDR document captures the complete technical rationale for all major architectural decisions, providing the foundation for safe, reliable, and maintainable EMDR bilateral stimulation device development.**
