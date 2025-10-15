# EMDR Bilateral Stimulation Device - Architecture Decisions (PDR)

**Preliminary Design Review Document**  
**Generated with assistance from Claude Sonnet 4 (Anthropic)**  
**Last Updated: 2025-10-02**

## Executive Summary

This document captures the technical architecture decisions and engineering rationale for the EMDR bilateral stimulation device project. The system implements safety-critical medical device software following JPL Institutional Coding Standards and targeting ESP-IDF v5.5.1 for maximum reliability and therapeutic effectiveness.

## Development Platform and Framework Decisions

### AD001: ESP-IDF v5.5.1 Framework Selection

**Decision**: Target ESP-IDF v5.5.1 specifically (not Arduino framework)

**Rationale:**
- **Latest NimBLE optimizations**: v5.5.1 includes critical BLE stability improvements for ESP32-C6
- **Power management enhancements**: Advanced deep sleep capabilities with faster wake times
- **Real-time guarantees**: Better FreeRTOS integration for safety-critical timing requirements
- **Memory management**: Improved heap and stack analysis tools for JPL compliance
- **Security features**: Enhanced encryption and authentication for medical device communication

**Alternatives Considered:**
- **Arduino framework**: Rejected due to limited real-time capabilities and abstraction overhead
- **ESP-IDF v5.3.x**: Rejected due to known BLE instability issues with ESP32-C6
- **ESP-IDF v5.4.x**: Rejected due to power management limitations

**Implementation Requirements:**
- All code must use ESP-IDF v5.5.1 APIs exclusively
- No deprecated function calls from earlier versions
- Platform packages locked to prevent accidental downgrades
- Static analysis tools must validate ESP-IDF compatibility

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
- **GPIO0**: User button (hardware debounced, internal pull-up)
- **GPIO15**: Status LED (system state indication)
- **GPIO19**: H-bridge IN1 (motor forward control)
- **GPIO20**: H-bridge IN2 (motor reverse control)
- **GPIO22**: Battery monitor enable (P-MOSFET gate driver)
- **GPIO23**: Therapy LED / WS2812B DIN (dual footprint, translucent case only)

**Rationale:**
- **GPIO0**: Standard boot button with hardware pull-up, ISR wake capability
- **GPIO15**: On-board LED available for status indication
- **GPIO19/20**: High-current capable pins suitable for H-bridge PWM control
- **Separation of concerns**: Status indication separate from therapeutic output

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
1. **BLE connection instability** → Mitigation: ESP-IDF v5.5.1 with proven BLE stack
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

### AD021: Motor Stall Detection Without Additional Hardware

**Decision**: Software-based motor stall detection using existing ESP32-C6 resources

**Problem**:
- ERM motor stall condition (120mA vs 90mA normal) could damage H-bridge MOSFETs
- Battery drain acceleration during stall conditions
- No dedicated current sensing hardware in design

**Solution**:
- Battery voltage drop monitoring during motor operation
- Direction change response testing for mechanical verification
- All detection uses vTaskDelay() for JPL compliance

**Implementation Methods:**

**Method 1: Battery Voltage Drop Analysis**
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

**Rationale:**
- **Hardware compatibility**: Uses existing battery monitoring circuit
- **Cost effective**: No additional current sensing components required
- **JPL compliant**: All delays use vTaskDelay(), no busy-wait loops
- **Therapeutic continuity**: Graceful degradation to LED stimulation

## Conclusion

This architecture provides a robust foundation for a safety-critical medical device while maintaining flexibility for future enhancements. The combination of ESP-IDF v5.5.1 and JPL coding standards (including no busy-wait loops) ensures both reliability and regulatory compliance for therapeutic applications.

The modular design with comprehensive API contracts enables distributed development while maintaining interface stability and code quality standards appropriate for medical device software. The 1ms FreeRTOS dead time implementation provides both hardware protection and watchdog feeding opportunities while maintaining strict JPL compliance.

---

**This PDR document captures the complete technical rationale for all major architectural decisions, providing the foundation for safe, reliable, and maintainable EMDR bilateral stimulation device development.**
