# EMDR Bilateral Stimulation Device - Complete Project DNA

**Generated with Claude Sonnet 4 (Anthropic) - Master Reference Version**
**Last Updated: 2025-10-02**

> **Usage Instructions for AI Assistants:**
> This file contains complete project specifications and API contracts. Use this as the authoritative source for generating any project component. All generated code must maintain API compatibility with the contracts defined here.

## 🎯 Project Mission

Create a dual-device EMDR bilateral stimulation system using ESP32-C6 microcontrollers with automatic pairing, coordinated timing, and safety-critical non-overlapping stimulation patterns with configurable bilateral frequencies (0.5-2 Hz).

## 🚀 Quick Start for New Chat Sessions

### Essential Context for AI Assistants:
1. **This is a safety-critical medical device** - bilateral stimulation must NEVER overlap
2. **Dual identical devices** - same code, automatic role switching (server/client)
3. **ESP32-C6 + NimBLE** - C language (not C++), FreeRTOS, heavy documentation required
4. **Current phase:** ERM motor control with H-bridge → LED testing capability
5. **Power-on race condition solution:** Random 0-2000ms delay before BLE operations
6. **JPL Compliance**: No busy-wait loops - all timing uses vTaskDelay() or hardware timers

### Critical Safety Requirements:
- **Non-overlapping stimulation:** Server and client alternate in precise half-cycles
- **Configurable cycle time:** 500-2000ms total cycle (0.5-2 Hz bilateral rate)
- **Half-cycle guarantee:** Each device gets exactly 50% of total cycle time
- **Dead time inclusion:** 1ms FreeRTOS dead time included within each half-cycle
- **Emergency shutdown:** 5-second button hold stops everything immediately
- **H-bridge protection:** 1ms dead time prevents shoot-through, feeds watchdog
- **No state persistence:** Every startup begins new session (no NVS recovery)
- **Factory reset window:** Only first 30 seconds after boot (prevents accidental resets)

## 🔧 Hardware Platform

**Target Device:** Seeed Xiao ESP32-C6
- **Microcontroller:** ESP32-C6 (RISC-V, 160MHz)
- **Memory:** 512KB SRAM, 4MB Flash  
- **Connectivity:** WiFi 6, BLE 5.0, Zigbee 3.0
- **Form Factor:** Ultra-compact (21x17.5mm)

### Complete GPIO Assignments
- **GPIO0**: Back-EMF sense (OUTA from H-bridge, power-efficient motor stall detection via ADC)
- **GPIO1**: User button (via jumper from GPIO18, hardware debounced with 10k pull-up, ISR support for emergency response)
- **GPIO2**: Battery voltage monitor (resistor divider, periodic battery level reporting)
- **GPIO15**: Status LED (system state indication, **ACTIVE LOW** on Xiao ESP32C6)
- **GPIO16**: Therapy LED Enable (P-MOSFET driver)
- **GPIO17**: Therapy LED / WS2812B DIN (dual footprint, translucent case only)
- **GPIO18**: User button (physical PCB location, jumpered to GPIO1, configured as high-impedance input)
- **GPIO19**: H-bridge IN1 (motor forward control)
- **GPIO20**: H-bridge IN2 (motor reverse control)
- **GPIO21**: Battery monitor enable (P-MOSFET gate driver control)

### H-Bridge Motor Control Configuration
```c
// H-bridge control modes (IN/IN configuration)
#define MOTOR_FORWARD_MODE      // GPIO19=H, GPIO20=L
#define MOTOR_REVERSE_MODE      // GPIO19=L, GPIO20=H  
#define MOTOR_COAST_MODE        // GPIO19=L, GPIO20=L
// NEVER: GPIO19=H, GPIO20=H (shoot-through condition)

#define MOTOR_PWM_FREQ          25000   // 25kHz frequency (above hearing)
#define MOTOR_PWM_RESOLUTION    LEDC_TIMER_10_BIT  // 10-bit (0-1023 range)

// CRITICAL PWM Resolution Selection:
// 10-bit @ 25kHz requires: 25,000 Hz × 1024 = 25.6 MHz clock ✓ (within 80/160MHz APB)
// 13-bit @ 25kHz would need: 25,000 Hz × 8192 = 204.8 MHz clock ✗ (exceeds ESP32-C6 max!)
// Resolution trade-off: 1024 steps provides imperceptible smoothness for motor control

// Dead time configuration (JPL compliant - uses FreeRTOS delays)
#define MOTOR_DEAD_TIME_MS      1       // 1ms FreeRTOS delay at end of half-cycle
#define GPIO_WRITE_LATENCY_NS   50      // Natural hardware dead time from GPIO writes
```

### MOSFET Component Architecture
- **High-side**: 2x AO3401A (P-channel, -30V, -4.2A, SOT-23, ~30ns turn-off)
- **Low-side**: 2x AO3400A (N-channel, 30V, 5.7A, SOT-23, ~30ns turn-off)
- **Gate drivers**: AO3400A (replaces MMBT2222A BJTs)
- **Battery monitor**: AO3401A P-MOSFET switch

### ERM Motor Specifications
- **Part**: Zard zoop flat coin vibration motor
- **Voltage**: 2.7-3.3V (operates at 3.3V from regulator)
- **Current**: 90mA running, ~120mA stall
- **Dimensions**: φ10mm × 3mm thickness
- **Speed**: ~12,000 RPM at 3V

## API Contracts & Function Prototypes

### Motor Control API

```c
/**
 * @brief Initialize motor H-bridge controller
 * @return ESP_OK on success
 * 
 * Configures GPIO19/20 for H-bridge control with 1ms FreeRTOS dead time
 * Sets up 25kHz PWM with 10-bit resolution for smooth motor control
 * Resolution: 10-bit (0-1023) chosen for ESP32-C6 clock constraints
 * JPL Compliant: No busy-wait loops, all timing uses vTaskDelay()
 */
esp_err_t motor_controller_init(void);

/**
 * @brief Set motor direction and intensity
 * @param direction Motor direction (MOTOR_FORWARD, MOTOR_REVERSE, MOTOR_COAST)
 * @param intensity_percent PWM intensity 0-100%
 * @return ESP_OK on success
 * 
 * Immediate GPIO control (no delays):
 * - Sets both channels to coast first (GPIO writes ~50ns each)
 * - Applies new direction with PWM
 * - GPIO write latency provides natural dead time (>100ns)
 * - No explicit microsecond delays needed
 * 
 * CRITICAL: Never set both IN1 and IN2 high simultaneously
 */
esp_err_t motor_set_direction_intensity(motor_direction_t direction, uint8_t intensity_percent);

/**
 * @brief Execute one half-cycle of bilateral stimulation with adaptive watchdog feeding
 * @param direction Motor direction for this half-cycle
 * @param intensity_percent Motor intensity (0-100%)
 * @param half_cycle_ms Half-cycle duration (total_cycle / 2)
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG if half_cycle out of range
 * 
 * JPL-compliant implementation with adaptive watchdog feeding:
 * - Short half-cycles (≤500ms): Feed at end only
 * - Long half-cycles (>500ms): Feed mid-cycle + end for safety
 * - Motor active uses vTaskDelay() (no busy-wait)
 * - Immediate coast via GPIO write (~50ns)
 * - 1ms dead time using vTaskDelay() for final watchdog feed
 * - Total time = exactly half_cycle_ms
 * 
 * Timing examples:
 * 
 * 500ms half-cycle (1000ms total):
 * [===499ms motor===][1ms dead+feed]
 * Watchdog fed every 500ms
 * 
 * 1000ms half-cycle (2000ms total):
 * [===500ms motor===][feed][===499ms motor===][1ms dead+feed]
 * Watchdog fed every 500ms and at 1000ms (end of half-cycle)
 */
esp_err_t motor_execute_half_cycle(motor_direction_t direction, 
                                    uint8_t intensity_percent,
                                    uint32_t half_cycle_ms);

/**
 * @brief Start bilateral motor stimulation with configurable cycle time
 * @param intensity_percent Motor intensity (0-100%)
 * @param total_cycle_ms Total bilateral cycle time (500-2000ms)
 * @param session_duration_ms Total session length in milliseconds
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG if cycle time out of range
 * 
 * Implements safety-critical non-overlapping bilateral pattern:
 * - Each device stimulates for exactly half of total_cycle_ms
 * - 1ms dead time included within each half-cycle window
 * - Non-overlapping guaranteed at all cycle times
 * 
 * Example with 1000ms total cycle:
 * Server: [===499ms motor===][1ms dead][---499ms off---][1ms dead]
 * Client: [---499ms off---][1ms dead][===499ms motor===][1ms dead]
 * 
 * Example with 2000ms total cycle:
 * Server: [===999ms motor===][1ms dead][---999ms off---][1ms dead]
 * Client: [---999ms off---][1ms dead][===999ms motor===][1ms dead]
 */
esp_err_t bilateral_start_motor_session(uint8_t intensity_percent,
                                        uint32_t total_cycle_ms,
                                        uint32_t session_duration_ms);

/**
 * @brief Single-device fallback with configurable cycle time
 * @param intensity_percent Motor intensity (0-100%)
 * @param total_cycle_ms Total cycle time (500-2000ms)
 * @return ESP_OK on success
 * 
 * Simulates bilateral effect using single motor:
 * - Forward for (total_cycle_ms / 2 - 1)ms
 * - 1ms dead time
 * - Reverse for (total_cycle_ms / 2 - 1)ms
 * - 1ms dead time
 * - Repeat
 */
esp_err_t motor_start_single_device_fallback(uint8_t intensity_percent, 
                                             uint32_t total_cycle_ms);

/**
 * @brief Start haptic effect within half-cycle window
 * @param pulse_duration_ms Active haptic pulse duration
 * @param total_cycle_ms Total bilateral cycle time (500-2000ms)
 * @param intensity_percent Motor intensity (0-100%)
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG if pulse exceeds half-cycle
 * 
 * Creates short haptic pulses within half-cycle budget:
 * - pulse_duration_ms must be ≤ (total_cycle_ms / 2 - 1)
 * - Remaining time in half-cycle is coast
 * - 1ms dead time always reserved at end of half-cycle
 * - Total cycle timing maintained for bilateral coordination
 * 
 * Example with 1000ms total cycle, 200ms haptic pulse:
 * Active: 200ms motor on [vTaskDelay]
 * Coast: 299ms off [vTaskDelay]
 * Dead: 1ms [vTaskDelay + watchdog]
 * Total: 500ms half-cycle window maintained
 */
esp_err_t bilateral_start_haptic_effect(uint8_t intensity_percent,
                                        uint16_t pulse_duration_ms,
                                        uint32_t total_cycle_ms);

/**
 * @brief Emergency motor stop - immediate coast mode
 * @return ESP_OK on success
 * 
 * Safety-first implementation:
 * - Immediately set both IN pins low (coast mode, immediate GPIO write)
 * - Send emergency stop command to paired device
 * - No NVS saving (every restart begins new session)
 */
esp_err_t motor_emergency_stop(void);

/**
 * @brief Detect motor stall condition via back-EMF sensing (primary method)
 * @return ESP_OK if motor running normally, ESP_ERR_MOTOR_STALL if stalled
 * 
 * Power-efficient stall detection using back-EMF monitoring:
 * - Reads back-EMF voltage on GPIO0 (OUTA from H-bridge) during coast periods
 * - Signal conditioning circuit: V_GPIO0 = 1.65V + 0.5 × V_OUTA
 *   - Maps -3.3V to +3.3V back-EMF → 0V to 3.3V ADC range (100% utilization)
 *   - R_bias = R_signal = 10kΩ, R_load unpopulated, C_filter = 15nF
 *   - 2.1kHz low-pass filter removes 25kHz PWM noise
 * - Stalled motor: back-EMF magnitude < 100mV (essentially no back-EMF)
 * - Normal operation: back-EMF magnitude > 1000mV (~1-2V depending on speed)
 * - Power consumption: 165µA continuous (bias network)
 * - 33% more efficient than battery voltage monitoring (248µA)
 * - Uses vTaskDelay() for all timing (JPL compliant)
 * 
 * ADC to Back-EMF conversion:
 *   V_backemf = 2 × (V_ADC - 1650mV)
 *   Example: ADC reads 0mV → back-EMF = -3.3V
 *            ADC reads 1650mV → back-EMF = 0V
 *            ADC reads 3300mV → back-EMF = +3.3V
 */
esp_err_t motor_detect_stall_via_backemf(void);

/**
 * @brief Detect motor stall condition via battery voltage drop (backup method)
 * @return ESP_OK if motor running normally, ESP_ERR_MOTOR_STALL if stalled
 * 
 * Backup stall detection using battery voltage monitoring:
 * - Measures voltage drop during motor operation
 * - >300mV drop indicates stall condition (120mA vs 90mA normal)
 * - Less power-efficient: enables resistor divider (~248µA when active)
 * - Uses vTaskDelay() for all timing (JPL compliant)
 * - Use back-EMF sensing as primary method when available
 */
esp_err_t motor_detect_stall_via_voltage_drop(void);

/**
 * @brief Handle motor stall recovery protocol
 * @return ESP_OK on successful recovery, ESP_ERR_MOTOR_STALL if recovery failed
 *
 * Stall recovery sequence:
 * 1. Immediate coast (GPIO write)
 * 2. 100ms settling time (vTaskDelay)
 * 3. Restart at 50% intensity
 * 4. If stall persists, switch to LED fallback mode
 */
esp_err_t motor_handle_stall_recovery(void);
```

### Power Manager API

```c
/**
 * @brief Initialize power management system
 * @return ESP_OK on success
 *
 * Phase 1: Basic initialization and current estimation
 * Phase 2: Full light sleep configuration and monitoring
 *
 * Safety: Power management must not impact bilateral timing precision
 */
esp_err_t power_manager_init(void);

/**
 * @brief Configure power optimization for bilateral stimulation patterns
 * @param total_cycle_ms Current bilateral cycle time (affects optimization strategy)
 * @return ESP_OK on success
 *
 * Optimizes light sleep behavior based on cycle timing:
 * - Short cycles (500ms): Minimal light sleep to maintain responsiveness
 * - Long cycles (2000ms): Maximum light sleep for power savings
 * - Maintains BLE responsiveness and emergency shutdown capability
 */
esp_err_t power_manager_optimize_for_bilateral_session(uint32_t total_cycle_ms);

/**
 * @brief Get current power consumption estimate
 * @param current_ma Pointer to store current consumption in mA
 * @return ESP_OK on success
 *
 * Provides real-time power monitoring for session optimization
 */
esp_err_t power_manager_get_current_consumption(uint16_t* current_ma);

/**
 * @brief Configure automatic light sleep during vTaskDelay
 * @param enable_light_sleep Enable/disable automatic light sleep in delays
 * @return ESP_OK on success
 *
 * When enabled:
 * - CPU enters light sleep during vTaskDelay() periods
 * - Power consumption drops from ~50mA to ~2-5mA during delays
 * - BLE and PWM peripherals remain active and functional
 * - Wake-up latency: <50μs (no impact on bilateral timing precision)
 *
 * Safety considerations:
 * - BLE stack must remain active (uses separate RTOS tasks)
 * - PWM/LEDC peripheral must not enter sleep
 * - Wake-up must be transparent to bilateral timing
 */
esp_err_t power_manager_configure_light_sleep(bool enable_light_sleep);

/**
 * @brief Configure BLE-compatible light sleep mode for bilateral stimulation
 * @param config BLE-safe power management configuration
 * @return ESP_OK on success
 *
 * BLE-Compatible Implementation:
 * - CPU enters light sleep (80MHz) during vTaskDelay periods
 * - BLE stack locked at 160MHz for reliable communication
 * - PWM/LEDC locked at 160MHz for motor control precision
 * - Wake-up latency: <50μs (maintains ±10ms bilateral timing)
 *
 * Realistic power savings: 40-50% (constrained by BLE requirements)
 * Safety: BLE responsiveness and emergency shutdown preserved
 */
esp_err_t power_manager_configure_ble_safe_light_sleep(
    const ble_compatible_light_sleep_config_t* config);

/**
 * @brief Monitor power consumption with BLE performance metrics
 * @param stats Real-time power consumption and BLE reliability data
 * @return ESP_OK on success
 */
esp_err_t power_manager_get_ble_aware_session_stats(
    ble_aware_session_stats_t* stats);
```

### Battery Monitor API

```c
/**
 * @brief Initialize battery monitoring system
 * @return ESP_OK on success
 * 
 * Configures GPIO22 for P-MOSFET control and GPIO1 for ADC reading
 * Sets up voltage divider monitoring with AO3400A gate driver
 */
esp_err_t battery_monitor_init(void);

/**
 * @brief Read battery voltage level
 * @param voltage_mv Pointer to store battery voltage in millivolts
 * @return ESP_OK on success, ESP_ERR_INVALID_STATE for ADC calibration failure
 * 
 * Enhanced with error detection:
 * - ADC calibration failure detection
 * - Voltage divider fault detection (open circuit, MOSFET failure)
 * - Diagnostic LED patterns for hardware faults
 * - Enables voltage divider, reads ADC, calculates actual battery voltage
 * - Automatically disables divider after reading to save power
 */
esp_err_t battery_read_voltage(uint16_t* voltage_mv);

/**
 * @brief Get battery percentage estimate
 * @return Battery percentage (0-100), 255 if error
 */
uint8_t battery_get_percentage(void);
```

### BLE Manager API

```c
/**
 * @brief Initialize BLE manager with race condition prevention
 * @param device_role Initial role preference (can change based on discovery)
 * @return ESP_OK on success
 * 
 * Implements random 0-2000ms delay before BLE operations
 */
esp_err_t ble_manager_init(device_role_t device_role);

/**
 * @brief Send bilateral stimulation command to paired device
 * @param command Command type (START/STOP/SYNC/INTENSITY/CYCLE_TIME)
 * @param sequence_number Rolling sequence number for packet loss detection
 * @param data Command-specific data (total_cycle_ms for CYCLE_TIME command)
 * @return ESP_OK on success
 * 
 * Enhanced with packet loss detection:
 * - Sequence numbers track missed packets
 * - 3 consecutive missed packets trigger single-device fallback
 * - Automatic recovery when communication resumes
 * - Cycle time configuration synchronized between devices
 */
esp_err_t ble_send_bilateral_command(bilateral_command_t command, 
                                     uint16_t sequence_number, 
                                     uint32_t data);

/**
 * @brief Process received bilateral message and detect packet loss
 * @param message Received bilateral message structure
 * @return ESP_OK on success, ESP_ERR_TIMEOUT for packet loss detection
 * 
 * Implements packet loss detection algorithm:
 * - Checks sequence number gaps
 * - Monitors communication timeouts (>2 seconds)
 * - Triggers fallback mode on consecutive losses
 */
esp_err_t ble_process_bilateral_message(bilateral_message_t* message);

/**
 * @brief Validate BLE configuration parameters
 * @param total_cycle_ms Total bilateral cycle time
 * @param intensity_percent Motor intensity
 * @param session_duration_ms Session duration
 * @return ESP_OK if valid, ESP_ERR_INVALID_ARG if any parameter out of range
 * 
 * Validates all user-configurable parameters:
 * - Total cycle time: 500-2000ms
 * - Intensity: 0-100%
 * - Session duration: 5-60 minutes
 */
esp_err_t ble_validate_config_parameters(uint32_t total_cycle_ms,
                                         uint8_t intensity_percent,
                                         uint32_t session_duration_ms);
```

### Button Handler API

```c
/**
 * @brief Handle button press with timing-based actions
 * @param press_duration_ms How long button was held
 * @return ESP_OK on success
 * 
 * Timing-based functionality:
 * - First 30 seconds after boot: 10-second hold = factory reset (if enabled)
 * - After 30 seconds: 10-second hold ignored (safety)
 * - Any time: 5-second hold = emergency shutdown
 */
esp_err_t button_handle_press(uint32_t press_duration_ms);

/**
 * @brief Factory reset - clear all NVS data (conditional compilation)
 * @return ESP_OK on success
 * 
 * Only compiled when ENABLE_FACTORY_RESET is defined
 */
#ifdef ENABLE_FACTORY_RESET
esp_err_t button_factory_reset(void);
#endif
```

### Therapy Light API (Research Feature)

```c
/**
 * @brief Initialize therapy light system (case-dependent)
 * @return ESP_OK on success, ESP_ERR_NOT_SUPPORTED if opaque case
 * 
 * Configures GPIO23 based on case type and build configuration:
 * - Translucent case + simple LED: LEDC PWM control (same as motor control)
 * - Translucent case + WS2812B: RMT peripheral for precise timing
 * - Opaque case: GPIO23 disabled, function returns not supported
 * 
 * Simple LED Implementation:
 * - Uses LEDC peripheral (same as motor PWM)
 * - 25kHz frequency for silent operation
 * - 10-bit resolution (0-1023 range) - matches motor PWM constraints
 * - Independent PWM channel from motor control
 * 
 * WS2812B Implementation:
 * - Uses RMT (Remote Control) peripheral for precise bit-level timing
 * - 800kHz data rate (1.25μs per bit)
 * - GRB color order (WS2812B standard)
 * - Single LED control via ESP-IDF led_strip component
 * - RMT channel independent from motor/LED PWM channels
 */
esp_err_t therapy_light_init(void);

/**
 * @brief Set therapy light intensity
 * @param intensity_percent Light intensity (0-100%)
 * @return ESP_OK on success, ESP_ERR_NOT_SUPPORTED if no therapy light
 * 
 * Simple LED: Maps 0-100% to LEDC duty cycle (0-1023)
 * WS2812B: Scales RGB values by intensity percentage
 */
esp_err_t therapy_light_set_intensity(uint8_t intensity_percent);

#ifdef THERAPY_LIGHT_WS2812B
/**
 * @brief Set therapy light color (WS2812B only)
 * @param red Red component (0-255)
 * @param green Green component (0-255)
 * @param blue Blue component (0-255)
 * @return ESP_OK on success, ESP_ERR_NOT_SUPPORTED if simple LED
 * 
 * Uses ESP-IDF led_strip component with RMT backend:
 * - led_strip_rmt_config_t for RMT configuration
 * - led_strip_config_t for LED strip parameters
 * - led_strip_set_pixel() for single LED control
 * - led_strip_refresh() to update LED output
 * - GRB color order (WS2812B standard)
 */
esp_err_t therapy_light_set_color(uint8_t red, uint8_t green, uint8_t blue);

/**
 * @brief Set therapy light to preset therapeutic colors
 * @param preset Therapeutic color preset (WARM_WHITE, COOL_WHITE, BLUE, etc.)
 * @return ESP_OK on success
 * 
 * Predefined therapeutic color presets:
 * - WARM_WHITE: Calming, relaxing effect (2700K equivalent)
 * - COOL_WHITE: Alertness, focus (5000K equivalent) 
 * - BLUE: Calming, stress reduction
 * - GREEN: Balance, grounding
 * - AMBER: Comfort, warmth
 */
esp_err_t therapy_light_set_preset(therapy_light_preset_t preset);
#endif

/**
 * @brief Start bilateral light therapy session
 * @param total_cycle_ms Total bilateral cycle time (matches motor timing)
 * @param intensity_percent Light intensity (0-100%)
 * @return ESP_OK on success
 * 
 * Synchronizes light with bilateral motor pattern:
 * - Server: Light on during motor active half-cycle
 * - Client: Light on during motor active half-cycle
 * - Provides visual cue synchronized with haptic stimulation
 * - Uses same timing as motor_execute_half_cycle()
 */
esp_err_t therapy_light_start_bilateral_session(uint32_t total_cycle_ms,
                                                  uint8_t intensity_percent);

/**
 * @brief Emergency therapy light shutdown
 * @return ESP_OK on success
 * 
 * Simple LED: Set LEDC duty to 0
 * WS2812B: Set pixel to (0,0,0) and refresh
 */
esp_err_t therapy_light_emergency_stop(void);
```

## Safety Implementation Requirements

### Bilateral Timing with Configurable Cycles

**Total Cycle Time Configuration:**
- **User parameter**: Total bilateral cycle time (500-2000ms)
- **Automatic calculation**: Half-cycle = total_cycle / 2
- **Therapeutic range**: 0.5 Hz (2000ms) to 2 Hz (500ms)
- **Default**: 1000ms total cycle (1 Hz, traditional EMDR rate)

**Timing Examples:**
```
500ms Total Cycle (2 Hz bilateral rate):
Server: [===249ms motor===][1ms dead][---249ms off---][1ms dead]
Client: [---249ms off---][1ms dead][===249ms motor===][1ms dead]

1000ms Total Cycle (1 Hz bilateral rate):
Server: [===499ms motor===][1ms dead][---499ms off---][1ms dead]
Client: [---499ms off---][1ms dead][===499ms motor===][1ms dead]

2000ms Total Cycle (0.5 Hz bilateral rate):
Server: [===999ms motor===][1ms dead][---999ms off---][1ms dead]
Client: [---999ms off---][1ms dead][===999ms motor===][1ms dead]
```

### H-Bridge Safety Protocol

**Dead Time Implementation:**
- **Method**: 1ms FreeRTOS delay (vTaskDelay) at end of each half-cycle
- **JPL Compliance**: No busy-wait loops, only vTaskDelay() used
- **Hardware protection**: GPIO write latency (~50ns) exceeds MOSFET turn-off (30ns)
- **Watchdog feeding**: esp_task_wdt_reset() called during 1ms dead time
- **Timing budget**: 1ms = 0.1-0.4% overhead depending on cycle time

**Emergency coast**: Both IN pins low for immediate motor stop (immediate GPIO write)
**Shoot-through prevention**: Software interlocks prevent both pins high

### Power Management
- **Battery monitoring**: AO3401A switch enables/disables voltage divider
- **Deep sleep**: <1mA standby current
- **Emergency shutdown**: No NVS saving, immediate safe state

## Enhanced Data Structures

```c
// Bilateral cycle time configuration (PRIMARY PARAMETER)
#define BILATERAL_CYCLE_TOTAL_MIN_MS    500     // Minimum total cycle (2 Hz)
#define BILATERAL_CYCLE_TOTAL_MAX_MS    2000    // Maximum total cycle (0.5 Hz)
#define BILATERAL_CYCLE_TOTAL_DEFAULT   1000    // Default 1 Hz bilateral rate

// Derived per-device timing (ALWAYS half of total cycle)
#define HALFCYCLE_FROM_TOTAL(total_ms)  ((total_ms) / 2)

// Dead time budget (INCLUDED within half-cycle window)
#define MOTOR_DEAD_TIME_MS              1       // FreeRTOS delay at end of half-cycle
#define GPIO_WRITE_LATENCY_NS           50      // Natural hardware dead time

// Enhanced bilateral message structure with packet loss detection
typedef struct {
    bilateral_command_t command;    // START/STOP/SYNC/INTENSITY/CYCLE_TIME
    uint16_t sequence_number;       // Rolling sequence number
    uint32_t timestamp_ms;          // System timestamp
    uint32_t data;                  // Total cycle time or intensity
    uint16_t checksum;              // Simple integrity check
} bilateral_message_t;

// Packet loss detection state
typedef struct {
    uint16_t last_received_seq;     // Last sequence number received
    uint16_t expected_seq;          // Next expected sequence
    uint8_t missed_count;           // Consecutive missed packets
    uint32_t last_received_time;    // Timestamp of last received message
} packet_loss_detector_t;

// Motor stall detection state
typedef struct {
    uint32_t start_time_ms;         // When motor started
    uint8_t current_duty_percent;   // Current PWM duty cycle
    uint32_t stall_detection_time;  // How long to wait before checking
    bool is_stalled;                // Current stall state
    uint16_t baseline_voltage_mv;   // No-load battery voltage reference
} motor_stall_detector_t;

// Task priority and stack size definitions
#define TASK_PRIORITY_BUTTON_ISR        25  // Highest - emergency response
#define TASK_PRIORITY_MOTOR_CONTROL     15  // High - bilateral timing critical
#define TASK_PRIORITY_BLE_MANAGER       10  // Medium - communication
#define TASK_PRIORITY_BATTERY_MONITOR    5  // Low - background monitoring  
#define TASK_PRIORITY_NVS_MANAGER        1  // Lowest - data persistence

#define STACK_SIZE_BUTTON_ISR       1024    // Simple ISR handling
#define STACK_SIZE_MOTOR_CONTROL    2048    // PWM + timing calculations
#define STACK_SIZE_BLE_MANAGER      4096    // NimBLE stack requirements
#define STACK_SIZE_BATTERY_MONITOR  1024    // ADC reading + calculations
#define STACK_SIZE_NVS_MANAGER      1024    // NVS operations

// Validation limits for BLE input parameters (UPDATED)
#define SESSION_DURATION_MIN_MS         (5 * 60 * 1000)     // 5 minutes
#define SESSION_DURATION_MAX_MS         (60 * 60 * 1000)    // 60 minutes
#define INTENSITY_MIN_PERCENT           0
#define INTENSITY_MAX_PERCENT           100
#define TOTAL_CYCLE_MIN_MS              500                 // 2 Hz max rate
#define TOTAL_CYCLE_MAX_MS              2000                // 0.5 Hz min rate

// Motor stall detection thresholds (back-EMF sensing)
#define BACKEMF_STALL_THRESHOLD_MV          1000    // <1000mV magnitude indicates stall
#define BACKEMF_NORMAL_MIN_MV               1000    // Normal operation: ~1-2V back-EMF magnitude
#define BACKEMF_ADC_CENTER_MV               1650    // ADC center point (maps to 0V back-EMF)
#define MOTOR_COAST_SETTLE_TIME_MS          10      // Wait for back-EMF and filter to stabilize
#define MOTOR_STARTUP_TIME_MS               200     // Wait before stall detection
#define MOTOR_STALL_CHECK_INTERVAL_MS       500     // Check every 500ms

// Back-EMF signal conditioning circuit (see AD021)
#define BACKEMF_R_BIAS                      10000   // 10kΩ from 3.3V to GPIO0
#define BACKEMF_R_SIGNAL                    10000   // 10kΩ from OUTA to GPIO0
// Note: R_load intentionally NOT POPULATED for maximum ADC range (100%)
#define BACKEMF_C_FILTER_NF                 15      // 15nF low-pass filter (2.1kHz cutoff)
#define BACKEMF_FILTER_CUTOFF_HZ            2100    // Removes 25kHz PWM, preserves motor back-EMF
#define BACKEMF_BIAS_CURRENT_UA             165     // Continuous bias current

// Motor stall detection thresholds (battery voltage sensing - backup method)
#define STALL_VOLTAGE_DROP_THRESHOLD_MV     300     // >300mV battery drop indicates stall (backup method)

// Packet loss detection parameters
#define PACKET_LOSS_CONSECUTIVE_THRESHOLD   3       // 3 missed packets = fallback
#define PACKET_LOSS_TIMEOUT_MS              2000    // 2 seconds = communication timeout

// Task Watchdog Timer configuration
#define TWDT_TIMEOUT_MS                     2000    // 2 second timeout (accommodates 1000ms half-cycles)
#define TWDT_FEED_INTERVAL_MAX_MS           501     // Maximum time between feeds (short half-cycles)
#define TWDT_FEED_INTERVAL_MIN_MS           250     // Minimum time between feeds (long half-cycles with mid-cycle feeding)

// Therapy light configuration (case-dependent)
#ifdef TRANSLUCENT_CASE_BUILD
    #ifdef THERAPY_LIGHT_WS2812B
        #define THERAPY_OUTPUT_TYPE         WS2812B_STRIP
        #define THERAPY_COLOR_OPTIONS       true
        #define THERAPY_MAX_BRIGHTNESS      255     // WS2812B max brightness
        #define THERAPY_GPIO                23      // WS2812B DIN pin
        #define THERAPY_RMT_CHANNEL         RMT_CHANNEL_0
        #define THERAPY_LED_COUNT           1       // Single LED
    #else
        #define THERAPY_OUTPUT_TYPE         SIMPLE_LED
        #define THERAPY_COLOR_OPTIONS       false
        #define THERAPY_MAX_BRIGHTNESS      100     // PWM percentage
        #define THERAPY_GPIO                23      // LED pin
        #define THERAPY_LEDC_CHANNEL        LEDC_CHANNEL_2  // Independent from motor
        #define THERAPY_PWM_FREQ            25000   // 25kHz (same as motor)
        #define THERAPY_PWM_RESOLUTION      LEDC_TIMER_10_BIT  // 10-bit (0-1023)
    #endif
#else
    // Opaque case: GPIO23 unused (motor-only stimulation)
    #define THERAPY_OUTPUT_TYPE             NONE
    #define THERAPY_COLOR_OPTIONS           false
#endif

// Therapy light color presets (WS2812B only)
#ifdef THERAPY_LIGHT_WS2812B
typedef enum {
    THERAPY_PRESET_WARM_WHITE,      // 255, 147, 41 (2700K equivalent)
    THERAPY_PRESET_COOL_WHITE,      // 255, 255, 255 (5000K equivalent)
    THERAPY_PRESET_BLUE,            // 0, 0, 255 (calming)
    THERAPY_PRESET_GREEN,           // 0, 255, 0 (balance)
    THERAPY_PRESET_AMBER,           // 255, 191, 0 (comfort)
    THERAPY_PRESET_OFF              // 0, 0, 0 (off)
} therapy_light_preset_t;

// WS2812B timing configuration (ESP-IDF led_strip component)
typedef struct {
    uint8_t led_count;              // Number of LEDs (1 for this project)
    uint8_t gpio_num;               // GPIO23
    rmt_channel_t rmt_channel;      // RMT_CHANNEL_0
    uint32_t resolution_hz;         // 10MHz (ESP-IDF default for led_strip)
} ws2812b_config_t;
#endif

// Therapy light state structure
typedef struct {
    bool is_initialized;                // Initialization state
    bool is_active;                     // Currently outputting light
    uint8_t current_intensity;          // Current intensity (0-100%)
#ifdef THERAPY_LIGHT_WS2812B
    uint8_t current_red;                // Current RGB values
    uint8_t current_green;
    uint8_t current_blue;
    therapy_light_preset_t current_preset;  // Current color preset
    led_strip_handle_t led_strip;       // ESP-IDF led_strip handle
#else
    uint32_t ledc_duty;                 // Current LEDC duty cycle (0-1023)
#endif
} therapy_light_state_t;

// Power management configuration structures
typedef struct {
    bool enable_cpu_light_sleep;            // CPU light sleep during delays (80MHz)
    bool lock_ble_at_full_speed;            // BLE stack stays at 160MHz
    bool lock_pwm_at_full_speed;            // Motor control stays at 160MHz
    uint32_t light_sleep_wake_latency_us;   // <50μs for bilateral timing
    uint16_t expected_power_savings_percent; // 40-50% (BLE-constrained)
} ble_compatible_light_sleep_config_t;

typedef struct {
    uint32_t session_duration_ms;           // Total session time
    uint16_t average_current_ma;            // Overall average consumption
    uint16_t cpu_sleep_current_ma;          // During CPU light sleep periods
    uint16_t ble_active_current_ma;         // During BLE operations
    uint32_t cpu_light_sleep_time_ms;       // Time CPU spent in light sleep
    uint32_t ble_full_speed_time_ms;        // Time BLE locked at 160MHz
    uint8_t ble_packet_success_rate;        // BLE reliability metric
    uint8_t power_efficiency_percent;       // Actual vs theoretical efficiency
} ble_aware_session_stats_t;
```

## Therapy Light Implementation Notes

### WS2812B LED Strip Control (ESP-IDF v5.5.1)

**Required ESP-IDF Component:** `led_strip` (built-in component)

**Correct Implementation Pattern:**
```c
#include "led_strip.h"

static led_strip_handle_t led_strip = NULL;

esp_err_t therapy_light_init_ws2812b(void) {
    // RMT configuration for WS2812B timing
    led_strip_rmt_config_t rmt_config = {
        .clk_src = RMT_CLK_SRC_DEFAULT,        // Use default clock source
        .resolution_hz = 10 * 1000 * 1000,     // 10MHz resolution (ESP-IDF default)
        .flags.with_dma = false,                // Single LED doesn't need DMA
    };
    
    // LED strip configuration
    led_strip_config_t strip_config = {
        .strip_gpio_num = 23,                   // GPIO23
        .max_leds = 1,                          // Single LED
        .led_model = LED_MODEL_WS2812,          // WS2812B model
        .color_component_format = {
            .format = LED_STRIP_COLOR_COMPONENT_FMT_GRB  // GRB order
        },
        .flags.invert_out = false,
    };
    
    // Create LED strip object with RMT backend
    esp_err_t ret = led_strip_new_rmt_device(&strip_config, &rmt_config, &led_strip);
    if (ret != ESP_OK) {
        return ret;
    }
    
    // Initialize to off state
    led_strip_set_pixel(led_strip, 0, 0, 0, 0);  // Index 0, RGB = (0,0,0)
    led_strip_refresh(led_strip);
    
    return ESP_OK;
}

esp_err_t therapy_light_set_color(uint8_t red, uint8_t green, uint8_t blue) {
    if (led_strip == NULL) {
        return ESP_ERR_INVALID_STATE;
    }
    
    // Set pixel color (RMT handles GRB conversion automatically)
    esp_err_t ret = led_strip_set_pixel(led_strip, 0, red, green, blue);
    if (ret != ESP_OK) return ret;
    
    // Refresh to actually output the color
    return led_strip_refresh(led_strip);
}
```

**Key Points:**
- **Use `led_strip_new_rmt_device()`** not `led_strip_new()` for ESP-IDF v5.5.1
- **RMT handles timing automatically** - no manual bit-banging needed
- **GRB order handled by component** - pass RGB, component converts
- **Resolution must be 10MHz** for standard WS2812B timing (1.25μs per bit)
- **Call `led_strip_refresh()`** after `led_strip_set_pixel()` to update LED

### Simple LED (LEDC) Control

**For non-WS2812B builds, use standard LEDC:**
```c
esp_err_t therapy_light_init_simple(void) {
    ledc_timer_config_t ledc_timer = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .timer_num = LEDC_TIMER_1,              // Different from motor timer
        .duty_resolution = LEDC_TIMER_10_BIT,   // 10-bit (0-1023)
        .freq_hz = 25000,                       // 25kHz
        .clk_cfg = LEDC_AUTO_CLK
    };
    esp_err_t ret = ledc_timer_config(&ledc_timer);
    if (ret != ESP_OK) return ret;
    
    ledc_channel_config_t ledc_channel = {
        .gpio_num = 23,
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel = LEDC_CHANNEL_2,              // Independent from motor channels
        .timer_sel = LEDC_TIMER_1,
        .duty = 0,
        .hpoint = 0
    };
    return ledc_channel_config(&ledc_channel);
}

esp_err_t therapy_light_set_intensity(uint8_t intensity_percent) {
    // Map 0-100% to 0-1023 (10-bit)
    uint32_t duty = (1023 * intensity_percent) / 100;
    return ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_2, duty)
           && ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_2);
}
```

**Key Points:**
- **Use separate LEDC timer and channel** from motor control
- **Same 25kHz frequency** for consistency
- **Independent duty cycle control** doesn't affect motor

## Critical Implementation Notes

### Dead Time Implementation (JPL Compliant)

**CRITICAL: Use vTaskDelay() for all timing operations**

```c
// CORRECT - JPL compliant implementation
esp_err_t motor_execute_half_cycle(motor_direction_t direction,
                                    uint8_t intensity_percent,
                                    uint32_t half_cycle_ms) {
    // Motor active period (FreeRTOS delay)
    uint32_t motor_active_ms = half_cycle_ms - 1;
    motor_set_direction_intensity(direction, intensity_percent);
    vTaskDelay(pdMS_TO_TICKS(motor_active_ms));
    
    // Immediate coast (GPIO write provides hardware dead time)
    motor_set_direction_intensity(MOTOR_COAST, 0);
    
    // 1ms dead time + watchdog feeding (FreeRTOS delay)
    vTaskDelay(pdMS_TO_TICKS(1));
    esp_task_wdt_reset();
    
    return ESP_OK;
}

// INCORRECT - Violates JPL standard
// ❌ DO NOT USE esp_rom_delay_us() - busy-wait loop
// ❌ DO NOT USE ets_delay_us() - busy-wait loop
// ❌ DO NOT USE while loops for timing
```

**Why FreeRTOS delays are required:**
1. **JPL Compliance**: No busy-wait loops allowed in safety-critical code
2. **Watchdog feeding**: 1ms delay provides opportunity to feed TWDT
3. **Task scheduling**: Other tasks can run during delays
4. **Minimal overhead**: 1ms = 0.1-0.4% of half-cycle time
5. **Hardware protection**: GPIO writes (~50ns) provide actual MOSFET dead time

## Testing and Development Flags

```c
#ifdef TESTING_MODE
    // Use LED instead of motor for safe testing
    // Skip NVS writes during development
    // Enable debug logging
#endif

#ifdef PRODUCTION_BUILD
    // Motor control only (no LED fallback)
    // Zero logging overhead
    // Full power management
#endif

#ifdef MOTOR_TESTING_MODE
    // Enable both LED and motor control for comparison
    // Extended diagnostics for H-bridge operation
#endif
```

## Build System Architecture (CRITICAL FOR AI ASSISTANTS)

### ESP-IDF CMake Build System

**CRITICAL: ESP-IDF uses CMake, NOT PlatformIO's build_src_filter**

ESP-IDF requires source files to be specified in `src/CMakeLists.txt`. PlatformIO's `build_src_filter` has no effect. We use a Python pre-build script to solve this.

### Hardware Test Build System

**How It Works:**
1. Python script `scripts/select_source.py` runs before every build
2. Script detects build environment (e.g., `hbridge_test`, `xiao_esp32c6`)
3. Script modifies `src/CMakeLists.txt` to use correct source file
4. ESP-IDF CMake builds the selected file

**Source File Mapping:**
```python
# scripts/select_source.py
source_map = {
    "xiao_esp32c6": "main.c",                    # Main application
    "xiao_esp32c6_production": "main.c",
    "xiao_esp32c6_testing": "main.c",
    "hbridge_test": "../test/hbridge_test.c",    # H-bridge hardware test
    # Add future tests here
}
```

**Build Commands:**
```bash
# Main application
pio run -e xiao_esp32c6 -t upload && pio device monitor

# H-bridge hardware test
pio run -e hbridge_test -t upload && pio device monitor

# Production build
pio run -e xiao_esp32c6_production -t upload
```

**Adding New Hardware Tests:**
1. Create `test/my_test.c`
2. Add to `scripts/select_source.py` source_map: `"my_test": "../test/my_test.c"`
3. Add environment to `platformio.ini` (copy `hbridge_test` pattern)
4. Build: `pio run -e my_test -t upload`

**Why This Architecture:**
- ✅ ESP-IDF native (works with CMake)
- ✅ Clean separation (tests in `test/`, main in `src/`)
- ✅ Automatic (no manual CMakeLists.txt editing)
- ✅ Scalable (easy to add new tests)
- ✅ Fast (<100ms script overhead)

**See Also:**
- `docs/architecture_decisions.md` - AD022: ESP-IDF Build System
- `docs/ESP_IDF_SOURCE_SELECTION.md` - Technical details
- `test/README.md` - Hardware test procedures
- `BUILD_COMMANDS.md` - Quick reference

## Implementation Checklist for AI Code Generation

When generating code for this project, always ensure:

✅ **All timing uses vTaskDelay()** - no esp_rom_delay_us() or ets_delay_us()
✅ **Total cycle time is primary parameter** - half-cycles calculated automatically
✅ **1ms dead time reserved** at end of each half-cycle
✅ **Watchdog feeding** during 1ms dead time periods
✅ **Motor active time** = (half_cycle_ms - 1)
✅ **Immediate GPIO writes** for direction changes (no explicit delays)
✅ **Parameter validation** for total cycle time (500-2000ms)
✅ **Non-overlapping guarantee** maintained at all cycle times
✅ **Comprehensive Doxygen documentation** for all functions
✅ **JPL compliance** - no dynamic allocation, no recursion, error checking

---

**This document serves as the complete specification for building the EMDR bilateral stimulation device with configurable cycle times and JPL-compliant dead time implementation.**
