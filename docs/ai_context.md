# EMDR Bilateral Stimulation Device - AI Context Reference

**Version:** v0.1.2
**Last Updated:** 2025-11-14
**Status:** Historical Reference (use CLAUDE.md for current info)

**Generated with Claude Sonnet 4 (Anthropic) - Master Reference Version**

> **Usage Instructions for AI Assistants:**
> This file contains historical project specifications and API contracts. For current project information, refer to CLAUDE.md as the primary authoritative source. This document is maintained for historical reference and may contain outdated information.

## 🎯 Project Mission

Create a dual-device EMDR bilateral stimulation system using ESP32-C6 microcontrollers with automatic pairing, coordinated timing, and safety-critical non-overlapping stimulation patterns with configurable bilateral frequencies (0.5-2 Hz).

## 🚀 Quick Start for New Chat Sessions

### Essential Context for AI Assistants:
1. **This is a safety-critical medical device** - bilateral stimulation must NEVER overlap
2. **Dual identical devices** - same code, automatic role switching (server/client)
3. **ESP32-C6 + NimBLE** - C language (not C++), FreeRTOS, heavy documentation required
4. **Current phase:** ERM motor control with H-bridge → LED testing capability → Dual-device pairing implementation
5. **Power-on race condition solution:** Random 0-2000ms delay before BLE operations
6. **Automatic role recovery:** Client becomes server after 30s disconnection timeout ("survivor becomes server")
7. **Instant wake:** Button press immediately wakes from deep sleep (no hold required for dual-device coordination)
8. **Fire-and-forget shutdown:** Emergency shutdown sends BLE command without waiting for ACK
9. **JPL Compliance**: No busy-wait loops - all timing uses vTaskDelay() or hardware timers
10. **Synchronized fallback (AD028):** 0-2min maintain bilateral rhythm, 2+ min continue assigned role only, reconnect every 5min
11. **Research Platform (AD030/AD031):** Extended 0.25-2 Hz range, 3 patterns (FIXED/ALTERNATING/UNILATERAL), 30-80% PWM safety limits

### Critical Safety Requirements:
- **Non-overlapping stimulation:** Server and client alternate in precise half-cycles
- **Configurable cycle time:** 500-4000ms total cycle (0.25-2 Hz research range, 0.5-2 Hz standard)
- **Half-cycle guarantee:** Each device gets exactly 50% of total cycle time
- **Dead time inclusion:** 1ms FreeRTOS dead time included within each half-cycle
- **Emergency shutdown:** 5-second button hold stops everything immediately
- **H-bridge protection:** 1ms dead time prevents shoot-through, feeds watchdog
- **Motor intensity limits:** 30-80% PWM for research safety (prevents damage/overheating)
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
- **GPIO16**: Therapy LED Enable (P-MOSFET driver, **ACTIVE LOW** - LOW=enabled, HIGH=disabled)
- **GPIO17**: Therapy light output (dual footprint: WS2812B or simple 1206 LED)
  - WS2812B option: Addressable RGB via led_strip component (default)
  - Simple LED option: 1206 LED via LEDC PWM (community alternative)
  - 62Ω current-limiting resistor inline (always populated)
  - Only functional with translucent case materials
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

## Hardware Assembly Options

### Therapy Light Dual Footprint Design

The PCB includes a dual footprint design on GPIO17 allowing builders to choose their LED hardware at assembly time:

#### Option 1: WS2812B RGB LED (Default)
- **Who uses**: Original developer (all builds)
- **Hardware**: WS2812B addressable RGB LED
- **Connection**: Standard WS2812B footprint on GPIO17
- **Current limiting**: 62Ω resistor (always populated)
- **Control**: ESP-IDF led_strip component via RMT peripheral
- **Build flag**: `THERAPY_LIGHT_WS2812B`
- **Features**: Full RGB color control, 5 therapeutic presets
- **Firmware requirement**: `src/idf_component.yml` with espressif/led_strip

#### Option 2: Simple 1206 LED (Community Alternative)
- **Who uses**: Community builders preferring simpler/cheaper option
- **Hardware**: Standard 1206 single-color LED
- **Connection**: DIN and GND pads of WS2812B footprint
- **Current limiting**: Same 62Ω resistor (always populated)
- **Control**: LEDC PWM (standard GPIO control)
- **Build flag**: `THERAPY_LIGHT_SIMPLE_LED`
- **Features**: Intensity control only (no color)
- **Firmware requirement**: Standard LEDC driver (no external dependencies)

#### Hardware Notes
- **Current limiting resistor**: 62Ω is always populated regardless of LED choice
  - Works for WS2812B (data line protection)
  - Works for simple LED (current limiting)
  - Standard part (reduces BOM complexity)
- **Assembly time decision**: Builder chooses which LED to populate
- **Firmware responsibility**: Builder must use correct build flag for their hardware
- **Testing**: `ws2812b_test.c` validates WS2812B option
- **Testing**: `dual_footprint_simple_led_test.c` validates simple LED option (untested by original dev)

#### Case Compatibility Matrix

| LED Hardware | Opaque Case | Translucent Case |
|--------------|-------------|------------------|
| WS2812B | Light blocked (GPIO17 disabled) | ✅ Full RGB therapy |
| Simple LED | Light blocked (GPIO17 disabled) | ✅ Single-color therapy |
| None | Motor-only device | Motor-only device |

**Build Flag Strategy:**
- Opaque case (any LED): No flags defined → therapy light code disabled
- Translucent + WS2812B: `THERAPY_LIGHT_WS2812B` defined
- Translucent + Simple LED: `THERAPY_LIGHT_SIMPLE_LED` defined

## API Contracts & Function Prototypes

**Implementation Mapping (see AD027):** These API contracts map to production source modules in the hybrid task-based + functional modular architecture:
- Motor Control API → `motor_task.c/h` (FreeRTOS task module)
- BLE Manager API → `ble_task.c/h` (FreeRTOS task module)
- Button Handler API → `button_task.c/h` (FreeRTOS task module)
- Battery Monitor API → `battery_monitor.c/h` (support module)
- Power Manager API → `power_manager.c/h` (support module)
- Therapy Light API → `led_control.c/h` (support module)

For complete modular architecture details, including file structure, module dependencies, and migration strategy, see `docs/architecture_decisions.md` AD027.

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
 *   - R_bias = R_signal = 10kΩ, R_load unpopulated, C_filter = 22nF
 *   - 1.45kHz low-pass filter removes 25kHz PWM noise (>94% attenuation)
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

### BLE GATT Server API (Single-Device Configuration)

**Note:** This is separate from the bilateral coordination BLE system. This API provides mobile app configuration of single-device Mode 5 (Custom) parameters via NimBLE GATT services.

```c
/**
 * @brief Initialize NimBLE GATT server for mobile app configuration
 * @return ESP_OK on success
 *
 * Implements complete NimBLE GATT service with 9 characteristics:
 * - Custom 128-bit UUID base: a1b2c3d4-e5f6-7890-a1b2-c3d4e5f6xxxx
 * - Service UUID ends in ...0000
 * - Characteristic UUIDs end in ...0001 through ...0009
 *
 * CRITICAL: Uses NimBLE stack, NOT Bluedroid
 * - nimble_port_init() handles all BT controller setup
 * - Never manually call esp_bt_controller_init()
 * - Double initialization causes complete system lockup
 */
esp_err_t ble_gatt_server_init(void);

/**
 * @brief GATT Characteristic 0x0001: Mode Selection
 * @param mode Device mode (0-4)
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG if mode > 4
 *
 * Mode mapping:
 * - 0 = Mode 1 (1Hz @ 50%)
 * - 1 = Mode 2 (1Hz @ 25%)
 * - 2 = Mode 3 (0.5Hz @ 50%)
 * - 3 = Mode 4 (0.5Hz @ 25%)
 * - 4 = Mode 5 (Custom - uses BLE-configured parameters)
 *
 * Properties: Read/Write
 * Type: uint8
 */
esp_err_t ble_gatt_set_mode(uint8_t mode);

/**
 * @brief GATT Characteristic 0x0002: Custom Frequency (Mode 5 only)
 * @param frequency_hz_x100 Frequency in Hz × 100 (50-200 = 0.5-2.0Hz)
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG if out of range
 *
 * Example values:
 * - 50 = 0.5 Hz (2000ms cycle)
 * - 100 = 1.0 Hz (1000ms cycle)
 * - 150 = 1.5 Hz (667ms cycle)
 * - 200 = 2.0 Hz (500ms cycle)
 *
 * Properties: Read/Write
 * Type: uint16 (little-endian)
 * Therapeutic range: 0.5-2.0 Hz (EMDRIA standards)
 */
esp_err_t ble_gatt_set_custom_frequency(uint16_t frequency_hz_x100);

/**
 * @brief GATT Characteristic 0x0003: Custom Duty Cycle (Mode 5 only)
 * @param duty_percent Duty cycle percentage (10-50%)
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG if out of range
 *
 * Range: 10-50%
 * - 10% minimum ensures perceptible timing pattern
 * - Maximum 50% prevents motor overlap in single-device bilateral alternation
 * - For LED-only mode (no motor), use PWM intensity = 0% instead
 *
 * Properties: Read/Write
 * Type: uint8
 */
esp_err_t ble_gatt_set_custom_duty_cycle(uint8_t duty_percent);

/**
 * @brief GATT Characteristic 0x0004: Battery Level (Read-only)
 * @param battery_percent Pointer to store battery percentage
 * @return ESP_OK on success
 *
 * Returns current battery level as percentage (0-100%)
 *
 * Properties: Read/Notify
 * Type: uint8
 */
esp_err_t ble_gatt_read_battery_level(uint8_t* battery_percent);

/**
 * @brief GATT Characteristic 0x0005: Session Time (Read-only)
 * @param session_time_s Pointer to store elapsed session time in seconds
 * @return ESP_OK on success
 *
 * Returns elapsed time since session start
 *
 * Properties: Read/Notify
 * Type: uint32 (little-endian)
 */
esp_err_t ble_gatt_read_session_time(uint32_t* session_time_s);

/**
 * @brief GATT Characteristic 0x0006: LED Enable (Mode 5 only)
 * @param enable LED enable state (0=off, 1=on)
 * @return ESP_OK on success
 *
 * Controls WS2812B LED behavior in Mode 5:
 * - 0x00 (false): LED off entire session (battery conservation)
 * - 0x01 (true): LED blinks in sync with motor patterns entire session
 *
 * Note: Other modes (1-4) use fixed 10-second LED timeout
 * Mode 5 LED behavior respects this setting (no timeout when enabled)
 *
 * Properties: Read/Write
 * Type: uint8
 * Default: 0x01 (enabled)
 */
esp_err_t ble_gatt_set_led_enable(uint8_t enable);

/**
 * @brief GATT Characteristic 0x0007: LED Color (Mode 5 only)
 * @param color_index Color palette index (0-15)
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG if > 15
 *
 * 16-color therapeutic palette for WS2812B:
 * - 0: Red, 1: Orange, 2: Yellow, 3: Green
 * - 4: Spring Green, 5: Cyan, 6: Sky Blue, 7: Blue
 * - 8: Violet, 9: Magenta, 10: Pink, 11: White
 * - 12: Gray, 13: Dark Gray, 14: Light Gray, 15: Brown
 *
 * Properties: Read/Write
 * Type: uint8
 * Default: 0x00 (Red)
 */
esp_err_t ble_gatt_set_led_color(uint8_t color_index);

/**
 * @brief GATT Characteristic 0x0008: LED Brightness (Mode 5 only)
 * @param brightness_percent Brightness percentage (10-30%)
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG if out of range
 *
 * Range: 10-30%
 * - Minimum 10% ensures visibility
 * - Maximum 30% prevents excessive power consumption
 * - Applied on top of base color from palette
 *
 * Properties: Read/Write
 * Type: uint8
 * Default: 20%
 */
esp_err_t ble_gatt_set_led_brightness(uint8_t brightness_percent);

/**
 * @brief GATT Characteristic 0x0009: PWM Intensity (Mode 5 only)
 * @param intensity_percent Motor PWM intensity percentage (0-80%)
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG if out of range
 *
 * Range: 0-80%
 * - 0% enables LED-only mode (visual therapy without motor vibration)
 * - Maximum 80% prevents motor overheating and excessive power draw
 * - Adjusts motor strength independently of duty cycle timing
 *
 * Properties: Read/Write
 * Type: uint8
 * Default: 75%
 */
esp_err_t ble_gatt_set_pwm_intensity(uint8_t intensity_percent);

/**
 * @brief Start advertising as "EMDR_Pulser_XXXXXX" (XXXXXX = last 6 MAC digits)
 * @return ESP_OK on success
 *
 * Advertising includes:
 * - Device name: EMDR_Pulser_XXXXXX
 * - Service UUID: a1b2c3d4-e5f6-7890-a1b2-c3d4e5f60000
 * - Flags: BLE-only, general discoverable
 *
 * Use nRF Connect (iOS/Android) to connect and configure
 */
esp_err_t ble_gatt_start_advertising(void);

/**
 * @brief Stop BLE advertising
 * @return ESP_OK on success
 *
 * Call during deep sleep or when BLE configuration not needed
 */
esp_err_t ble_gatt_stop_advertising(void);
```

**BLE GATT Implementation Notes:**

**UUID Structure:**
- Base: `a1b2c3d4-e5f6-7890-a1b2-c3d4e5f6xxxx`
- Service: `...0000`
- Characteristics: `...0001` through `...0009`
- Format: Complete little-endian byte order (all 16 bytes reversed)

**Critical NimBLE Initialization:**
```c
// CORRECT - NimBLE handles BT controller automatically
esp_err_t ble_gatt_server_init(void) {
    ESP_ERROR_CHECK(nvs_flash_init());
    ESP_ERROR_CHECK(nimble_port_init());  // This does everything
    // Configure NimBLE stack...
    nimble_port_freertos_init(nimble_host_task);
    return ESP_OK;
}

// WRONG - Double initialization causes system lockup
esp_err_t ble_gatt_server_init(void) {
    esp_bt_controller_config_t bt_cfg = BT_CONTROLLER_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_bt_controller_init(&bt_cfg));       // ❌ Conflict!
    ESP_ERROR_CHECK(esp_bt_controller_enable(ESP_BT_MODE_BLE)); // ❌ Conflict!
    ESP_ERROR_CHECK(nimble_port_init());  // Already initializes controller!
    // System freezes before any output!
}
```

**Mode 5 LED Behavior Fix:**
```c
// Critical fix: Mode 5 LED should NOT timeout after 10 seconds
// Motor task checks mode before applying LED timeout:

if (current_mode != MODE_CUSTOM && led_indication_active &&
    ((now - led_indication_start_ms) >= LED_INDICATION_TIME_MS)) {
    led_indication_active = false;
    led_clear();
    ESP_LOGI(TAG, "LED off (battery conservation)");
}

// Mode 5 LED behavior:
// - If mode5_led_enable = true: LED blinks entire session (no timeout)
// - If mode5_led_enable = false: LED off entire session
// Other modes: LED blinks 10 seconds after mode change (battery conservation)
```

**Testing with nRF Connect:**
- **Android:** [Google Play](https://play.google.com/store/apps/details?id=no.nordicsemi.android.mcp)
- **iOS:** [App Store](https://apps.apple.com/us/app/nrf-connect-for-mobile/id1054362403)

**Test Guide:** `test/SINGLE_DEVICE_BLE_GATT_TEST_GUIDE.md`

**Build Command:**
```bash
pio run -e single_device_ble_gatt_test -t upload && pio device monitor
```

### Button Handler API

```c
/**
 * @brief Handle button press with timing-based actions
 * @param press_duration_ms How long button was held
 * @return ESP_OK on success
 *
 * Button hold sequence (updated for dual-device operation):
 * - Instant press: Wake from deep sleep (no hold required)
 * - 0-5 seconds: Normal hold, no action
 * - 5 seconds: Emergency shutdown ready (purple LED blink via therapy light)
 * - 5-10 seconds: Continue holding (purple blink continues, release triggers shutdown)
 * - 10 seconds: NVS clear triggered (GPIO15 solid on, only first 30s of boot per AD013)
 * - Release: Execute action (shutdown at 5s+, NVS clear at 10s+)
 *
 * GPIO15 LED indication:
 * - 5s hold: Purple therapy light blink (if available)
 * - 10s hold (first 30s only): GPIO15 solid on (distinct from purple blink)
 */
esp_err_t button_handle_press(uint32_t press_duration_ms);

/**
 * @brief Enter deep sleep with guaranteed wake-on-new-press
 * @return Does not return (device sleeps)
 * 
 * ESP32-C6 ext1 wake pattern (see AD023):
 * 1. Check button state
 * 2. If LOW (held): Blink LED at 5Hz while waiting for release
 * 3. Once HIGH: Configure ext1 wake on LOW
 * 4. Enter deep sleep (button guaranteed released)
 * 5. Next wake guaranteed to be NEW button press
 * 
 * Visual feedback: LED blinks at 5Hz (100ms on, 100ms off) while waiting
 * No serial monitor required for user to know when to release
 * 
 * Power consumption:
 * - While waiting (LED blinking): ~50mA
 * - Deep sleep: <1mA
 * - Wake latency: <2 seconds to full operation
 * 
 * JPL Compliant: Uses vTaskDelay() for all timing
 * 
 * Reference implementation: test/button_deepsleep_test.c
 */
esp_err_t enter_deep_sleep_with_wake_guarantee(void);

/**
 * @brief Clear all NVS data (conditional compilation)
 * @return ESP_OK on success
 * 
 * Clears from NVS:
 * - Paired device MAC address
 * - User preference defaults (cycle time, intensity)
 * - Session statistics (if stored)
 * 
 * Does NOT affect:
 * - Firmware or bootloader
 * - Hardware calibration data
 * - Device serial number
 * 
 * User-facing description: "Unpair device and reset settings"
 * After clearing, device restarts and enters pairing mode.
 * 
 * Only compiled when ENABLE_CLEAR_NVS is defined.
 */
#ifdef ENABLE_CLEAR_NVS
esp_err_t button_clear_nvs(void);
#endif
```

### Therapy Light API (Research Feature)

```c
/**
 * @brief Initialize therapy light system (hardware and case dependent)
 * @return ESP_OK on success, ESP_ERR_NOT_SUPPORTED if disabled or opaque case
 * 
 * Hardware-dependent initialization based on build flags:
 * 
 * THERAPY_LIGHT_WS2812B defined:
 * - Configures GPIO17 for WS2812B via RMT peripheral
 * - Uses ESP-IDF led_strip component
 * - Requires idf_component.yml with espressif/led_strip dependency
 * - Returns ESP_ERR_NOT_SUPPORTED if opaque case (light blocked)
 * 
 * THERAPY_LIGHT_SIMPLE_LED defined:
 * - Configures GPIO17 for LEDC PWM control
 * - Uses standard LEDC peripheral (like motor control)
 * - Independent LEDC timer and channel from motor
 * - Returns ESP_ERR_NOT_SUPPORTED if opaque case (light blocked)
 * 
 * Neither flag defined:
 * - Returns ESP_ERR_NOT_SUPPORTED immediately
 * - No GPIO17 configuration (disabled/unused)
 * - Saves flash space when therapy light not needed
 * 
 * GPIO16 (Power Enable):
 * - Configured as output, ACTIVE LOW (LOW=enabled, HIGH=disabled)
 * - P-MOSFET gate control for LED power
 * - Set LOW during initialization to enable LED power
 */
esp_err_t therapy_light_init(void);

#if defined(THERAPY_LIGHT_WS2812B)
/**
 * @brief Set therapy light color (WS2812B only)
 * @param red Red component (0-255)
 * @param green Green component (0-255)
 * @param blue Blue component (0-255)
 * @return ESP_OK on success, ESP_ERR_INVALID_STATE if not initialized
 * 
 * Uses ESP-IDF led_strip component with RMT backend:
 * - led_strip_set_pixel() for single LED control
 * - led_strip_refresh() to update LED output
 * - GRB color order handled automatically by component
 * 
 * Only available when THERAPY_LIGHT_WS2812B is defined.
 */
esp_err_t therapy_light_set_color(uint8_t red, uint8_t green, uint8_t blue);

/**
 * @brief Set therapy light to preset therapeutic colors (WS2812B only)
 * @param preset Therapeutic color preset
 * @return ESP_OK on success
 * 
 * Predefined therapeutic color presets:
 * - THERAPY_PRESET_WARM_WHITE: Calming, relaxing (2700K)
 * - THERAPY_PRESET_COOL_WHITE: Alertness, focus (5000K)
 * - THERAPY_PRESET_BLUE: Calming, stress reduction
 * - THERAPY_PRESET_GREEN: Balance, grounding
 * - THERAPY_PRESET_AMBER: Comfort, warmth
 * 
 * Only available when THERAPY_LIGHT_WS2812B is defined.
 */
esp_err_t therapy_light_set_preset(therapy_light_preset_t preset);

#elif defined(THERAPY_LIGHT_SIMPLE_LED)
/**
 * @brief Set therapy light intensity (Simple LED only)
 * @param intensity_percent Light intensity (0-100%)
 * @return ESP_OK on success
 * 
 * Uses LEDC PWM for intensity control:
 * - Maps 0-100% to LEDC duty cycle
 * - Same 25kHz frequency as motor control
 * - Independent LEDC timer and channel
 * - No color control (single-color LED)
 * 
 * Only available when THERAPY_LIGHT_SIMPLE_LED is defined.
 */
esp_err_t therapy_light_set_intensity(uint8_t intensity_percent);

#else
// No therapy light functions available when neither flag defined
// therapy_light_init() will return ESP_ERR_NOT_SUPPORTED
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
#define BACKEMF_C_FILTER_NF                 22      // 22nF low-pass filter (1.45kHz cutoff, >94% PWM attenuation)
#define BACKEMF_FILTER_CUTOFF_HZ            1450    // Removes 25kHz PWM, preserves motor back-EMF
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

### WS2812B Component Installation via idf_component.yml

**PlatformIO with ESP-IDF requires component registry setup:**

Create `src/idf_component.yml` to automatically fetch ESP-IDF components:

```yaml
## IDF Component Manager Manifest File
## This file tells ESP-IDF's component manager which external components to download

dependencies:
  espressif/led_strip: "^2.5.0"
```

**What happens on first build:**
1. ESP-IDF component manager sees `src/idf_component.yml`
2. Downloads `espressif/led_strip` from component registry
3. Caches in `.pio/build/.../managed_components/`
4. Includes automatically in build

**Expected build output:**
```
-- Component espressif__led_strip downloading...
-- Component espressif__led_strip downloaded (v2.5.0)
```

**No CMakeLists.txt changes needed** - component manager handles everything!

### WS2812B Hardware Test

**Test File:** `test/ws2812b_test.c`

**Build & Run:**
```bash
pio run -e ws2812b_test -t upload && pio device monitor
```

**Test Features:**
- Color cycling: RED → GREEN → BLUE → RAINBOW → repeat
- Button press: Cycle through colors
- Button hold 5s: Deep sleep with purple blink wait-for-release
- GPIO15 status LED: Blink pattern indicates current color
- 50% brightness default (battery-friendly)
- Deep sleep: <1mA with button wake

**Test Sequence:**
1. Power on → WS2812B shows RED (50% brightness)
2. GPIO15 blinks slowly (2Hz) for RED state
3. Press button → GREEN, GPIO15 blinks 4Hz
4. Press button → BLUE, GPIO15 blinks 8Hz
5. Press button → RAINBOW cycle, GPIO15 blinks 10Hz
6. Hold button 5s → Countdown, purple blink on WS2812B
7. Release button → Deep sleep (<1mA)
8. Press button → Wake to RED state

**Brightness Control:**
```c
#define WS2812B_BRIGHTNESS 50  // 0-100%, default 50%

// In code:
apply_brightness(&r, &g, &b, WS2812B_BRIGHTNESS);
led_strip_set_pixel(led_strip, 0, r, g, b);
led_strip_refresh(led_strip);
```

**Power Consumption:**
- 50% brightness: ~30mA LED + ~20mA ESP32 = 50mA active
- 100% brightness: ~60mA LED + ~20mA ESP32 = 80mA active
- Deep sleep: <1mA total

**GPIO16 Power Control (ACTIVE LOW):**
```c
// Enable WS2812B power (P-MOSFET conducts)
gpio_set_level(GPIO_WS2812B_ENABLE, 0);  // LOW = ON

// Disable WS2812B power for deep sleep
gpio_set_level(GPIO_WS2812B_ENABLE, 1);  // HIGH = OFF
```

**Reference:** See `test/ws2812b_test.c` for complete implementation pattern

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

## Deep Sleep and Wake Patterns

### ESP32-C6 ext1 Wake Limitation

ext1 wake is **level-triggered**, not edge-triggered:
- Wake condition: GPIO is LOW (button pressed)
- Not an edge detection (no press "event")
- If GPIO is LOW when sleeping → wakes immediately

**The Problem:**
When a user holds a button to trigger deep sleep (e.g., 5-second countdown), the button is still LOW (pressed) when the device enters sleep. Since ext1 wakes when GPIO is LOW, the device wakes immediately. There's no way to distinguish "still held from countdown" vs "new button press."

### Guaranteed Wake-on-New-Press Pattern

**Always use this pattern for button-triggered deep sleep (see AD023):**

```c
esp_err_t enter_deep_sleep_with_wake_guarantee(void) {
    // Step 1: Wait for button release if currently pressed
    if (gpio_get_level(GPIO_BUTTON) == 0) {
        // Step 2: Blink LED at 5Hz while waiting (visual feedback)
        while (gpio_get_level(GPIO_BUTTON) == 0) {
            gpio_set_level(GPIO_STATUS_LED, LED_ON);
            vTaskDelay(pdMS_TO_TICKS(100));
            gpio_set_level(GPIO_STATUS_LED, LED_OFF);
            vTaskDelay(pdMS_TO_TICKS(100));
        }
    }
    
    // Step 3: Configure ext1 to wake on LOW (button press)
    //         Button is guaranteed HIGH at this point
    uint64_t gpio_mask = (1ULL << GPIO_BUTTON);
    esp_sleep_enable_ext1_wakeup(gpio_mask, ESP_EXT1_WAKEUP_ANY_LOW);
    
    // Step 4: Enter deep sleep
    //         Next wake will be from NEW button press only
    esp_deep_sleep_start();
    return ESP_OK;  // Never reached
}
```

**Why This Works:**

1. **Before sleep**: Ensure button is HIGH (not pressed)
2. **Configure ext1**: Wake when GPIO goes LOW (button pressed)
3. **Sleep entry**: Wake condition is FALSE (button is HIGH)
4. **Sleep state**: Device waits for wake condition to become TRUE
5. **Wake event**: Only occurs when button transitions HIGH → LOW
6. **Guarantee**: This can only happen with a NEW button press

**User Experience:**
1. Hold button for countdown (e.g., 5 seconds)
2. LED blinks fast (5Hz) → Visual cue: "Release the button now"
3. Release button → Device sleeps immediately
4. Later: Press button → Device wakes (guaranteed NEW press)

**Key Features:**
- ✅ LED blink provides visual feedback (no serial monitor needed)
- ✅ Guarantees button is HIGH before sleep
- ✅ ext1 always configured for wake-on-LOW
- ✅ Next wake guaranteed to be NEW press
- ✅ Simple - no complex state machine
- ✅ JPL compliant - uses vTaskDelay() for all timing

**Reference Implementation:** `test/button_deepsleep_test.c`

**Build & Test:**
```bash
pio run -e button_deepsleep_test -t upload && pio device monitor
```

**Failed Approaches (DO NOT USE):**

❌ **Immediate re-sleep pattern** (DOES NOT WORK):
```c
// Device wakes immediately while button held
esp_deep_sleep_start();
// Check if button still held
if (gpio_get_level(GPIO_BUTTON) == 0) {
    esp_deep_sleep_start();  // Try to sleep again
}
// Problem: After release, ext1 still waiting for LOW
// Device stuck sleeping, can't detect new press!
```

❌ **Wake-on-HIGH state machine** (TOO COMPLEX/UNRELIABLE):
```c
// Try to configure wake-on-HIGH for button release
if (gpio_get_level(GPIO_BUTTON) == 0) {
    esp_sleep_enable_ext1_wakeup(mask, ESP_EXT1_WAKEUP_ANY_HIGH);
}
// Problem: ESP32-C6 ext1 wake-on-HIGH is unreliable
// Adds unnecessary complexity
```

### Integration with Main Application

**Use this pattern for:**
- Session timeout → automatic sleep (no button hold scenario)
- User-initiated sleep → button hold countdown with wait-for-release
- Emergency shutdown → immediate coast, then sleep with wait-for-release
- Battery low → warning, then sleep with wait-for-release

**Power Consumption:**
- Active (LED blinking): ~50mA
- Deep sleep: <1mA
- Wake latency: <2 seconds
- Battery life: 50x improvement during sleep

---

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
✅ **Deep sleep pattern** - always use wait-for-release with LED blink (AD023)

---

**This document serves as the complete specification for building the EMDR bilateral stimulation device with configurable cycle times, JPL-compliant dead time implementation, and guaranteed wake-on-new-press deep sleep patterns.**
