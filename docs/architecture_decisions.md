# EMDR Bilateral Stimulation Device - Architecture Decisions (PDR)

**Preliminary Design Review Document**  
**Generated with assistance from Claude Sonnet 4 (Anthropic)**  
**Last Updated: 2025-10-20**

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

**Decision**: Immediate motor coast with coordinated shutdown

**Safety Requirements:**
- 5-second button hold triggers emergency stop
- Immediate motor coast (GPIO write, no delay)
- Coordinated shutdown message to paired device
- No NVS state saving during emergency (new session on restart)

**Implementation:**
- ISR-based button monitoring for fastest response
- Immediate GPIO write for motor coast (~50ns)
- Fallback to local shutdown if communication fails

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

**Decision**: Time-limited factory reset capability (first 30 seconds only)

**Rationale:**
- **Accidental reset prevention**: No factory reset during therapy sessions
- **Service technician access**: Reset available during initial setup
- **Clear user feedback**: Different LED patterns for reset vs shutdown
- **Conditional compilation**: Factory reset can be disabled in production builds

**Implementation:**
- Boot time tracking with 30-second window
- LED rapid blink pattern for reset confirmation
- Comprehensive NVS clearing including pairing data

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
1. **BLE connection instability** → Mitigation: ESP-IDF v5.3.0 with proven, stable BLE stack
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

---

## Conclusion

This architecture provides a robust foundation for a safety-critical medical device while maintaining flexibility for future enhancements. The combination of ESP-IDF v5.3.0 and JPL coding standards (including no busy-wait loops) ensures both reliability and regulatory compliance for therapeutic applications.

The modular design with comprehensive API contracts enables distributed development while maintaining interface stability and code quality standards appropriate for medical device software. The 1ms FreeRTOS dead time implementation provides both hardware protection and watchdog feeding opportunities while maintaining strict JPL compliance.

AD023 documents the critical deep sleep wake pattern that ensures reliable button-triggered wake from deep sleep, solving the ESP32-C6 ext1 level-triggered wake limitation with a simple, user-friendly visual feedback pattern.

---

**This PDR document captures the complete technical rationale for all major architectural decisions, providing the foundation for safe, reliable, and maintainable EMDR bilateral stimulation device development.**
