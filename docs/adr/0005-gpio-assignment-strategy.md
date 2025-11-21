# 0005: GPIO Assignment Strategy

**Date:** 2025-10-15
**Phase:** 0.1
**Status:** Accepted
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of assigning GPIO pins for motor control, battery monitoring, and user interface,
facing ESP32-C6 pin limitations and hardware constraints (GPIO19/20 crosstalk, ADC channels),
we decided for dedicated GPIO assignments optimized for power efficiency and ISR capability,
and neglected multiplexed GPIO or alternative ADC configurations,
to achieve reliable motor control with power-efficient back-EMF sensing and fast button response,
accepting GPIO19/20 crosstalk risk mitigated by external pull-downs.

---

## Problem Statement

The Seeed XIAO ESP32-C6 has limited GPIO pins (21x17.5mm package), requiring careful allocation for:
- **Motor control**: H-bridge PWM (2 pins) + coast capability
- **Battery monitoring**: Voltage sense with minimal power consumption
- **Motor diagnostics**: Back-EMF sensing for stall detection
- **User interface**: Button with ISR + RTC wake, status LED, therapy LED
- **Safety**: Emergency shutdown requires fastest button response

Hardware constraints:
- **GPIO19/20 crosstalk**: Known silicon issue during boot
- **ADC channels**: Limited to specific GPIO pins
- **ISR capability**: Button needs interrupt-capable GPIO
- **RTC wake**: Deep sleep wake requires RTC GPIO

---

## Context

### Hardware Requirements

**Motor Control (H-bridge TB6612FNG):**
- 2 PWM channels for bidirectional control (forward/reverse)
- Coast mode via setting both low
- 25kHz PWM frequency (above human hearing)

**Power Monitoring:**
- Battery voltage sensing (resistor divider to 3.3V max)
- Back-EMF sensing for stall detection (±3.3V motor signal)
- Minimize power consumption (continuous monitoring)

**User Interface:**
- Button with hardware debouncing (10kΩ pull-up)
- ISR capability for emergency shutdown
- RTC wake from deep sleep
- Status LED (on-board, active LOW)
- Therapy LED (WS2812B RGB) with enable control

### ESP32-C6 Constraints

**ADC Channels:**
- ADC1_CH0 (GPIO0), ADC1_CH2 (GPIO2), ADC1_CH3 (GPIO3), ADC1_CH4 (GPIO4)
- ADC shares channels with WiFi (avoid ADC2 for reliability)

**RTC GPIO (deep sleep wake):**
- GPIO0-5 support RTC wake functionality

**Known Issues:**
- **GPIO19/GPIO20 crosstalk**: Silicon issue causes unintended activation during boot
- Mitigation: External pull-downs prevent shoot-through

---

## Decision

We will use dedicated GPIO assignments optimized for functionality and power efficiency.

### GPIO Allocation

| GPIO | Function | Direction | Notes |
|------|----------|-----------|-------|
| GPIO0 | Back-EMF sense | Input (ADC1_CH0) | Power-efficient motor monitoring (µA vs mA) |
| GPIO1 | User button | Input (ISR) | Via jumper from GPIO18, RTC wake capable |
| GPIO2 | Battery voltage | Input (ADC1_CH2) | Resistor divider: VBAT→3.3kΩ→GPIO2→10kΩ→GND |
| GPIO15 | Status LED | Output | On-board LED, **ACTIVE LOW** (0=ON, 1=OFF) |
| GPIO16 | WS2812B Enable | Output | P-MOSFET driver, **ACTIVE LOW** (LOW=enabled) |
| GPIO17 | WS2812B DIN | Output | RGB LED data (RMT peripheral) |
| GPIO18 | Button (physical) | High-Z Input | Physical PCB location, jumpered to GPIO1 |
| GPIO19 | H-bridge IN2 | Output (LEDC PWM) | Motor reverse control |
| GPIO20 | H-bridge IN1 | Output (LEDC PWM) | Motor forward control |
| GPIO21 | Battery Enable | Output | P-MOSFET gate driver (HIGH=enabled) |

### Key Design Decisions

**1. GPIO0 for Back-EMF Sensing (Power Efficiency)**
- **Rationale**: Continuous stall detection with minimal power (µA ADC input impedance)
- **Alternative rejected**: Frequent battery voltage checks would require mA resistor divider current
- **Benefit**: Always-on motor monitoring without battery drain

**2. GPIO1 for Button (via jumper from GPIO18)**
- **Rationale**: ISR-capable GPIO enables fastest emergency response
- **Hardware**: Physical button on GPIO18, jumper wire to GPIO1
- **Software**: GPIO18 configured as high-impedance input (unused)
- **Benefit**: No PCB rework required, enables ISR support

**3. GPIO2 for Battery Voltage**
- **Rationale**: Periodic monitoring only (not continuous like back-EMF)
- **Power gating**: GPIO21 enables P-MOSFET only during measurements
- **Resistor values**: 3.3kΩ + 10kΩ divider (see calculations below)

**4. GPIO19/GPIO20 for H-bridge (despite crosstalk risk)**
- **Rationale**: High-current capable pins suitable for PWM
- **Mitigation**: External pull-downs prevent shoot-through during boot
- **Future**: May move GPIO20 to GPIO18 in next PCB revision

### Circuit Details

**Battery Voltage Divider:**
```
VBAT (max 4.2V) → 3.3kΩ → GPIO2 (ADC) → 10kΩ → GND
V_adc = VBAT × (10kΩ / (3.3kΩ + 10kΩ))
V_adc = VBAT × 0.7519

For VBAT = 4.2V: V_adc = 3.16V (within 3.3V ADC range)
For VBAT = 3.0V: V_adc = 2.26V (measurable)
```

**Back-EMF Voltage Summing:**
```
Motor H-bridge: -3.3V to +3.3V (bidirectional)
ADC input: 0V to 3.3V (unipolar)

Solution: Voltage divider with 1.65V offset
V_adc = (V_motor + 3.3V) / 2

For V_motor = +3.3V: V_adc = 3.3V (max ADC range)
For V_motor = 0V: V_adc = 1.65V (midpoint)
For V_motor = -3.3V: V_adc = 0V (min ADC range)
```

**Status LED (GPIO15):**
- On-board LED on XIAO ESP32-C6
- **ACTIVE LOW**: GPIO15 = 0 turns LED ON, GPIO15 = 1 turns LED OFF

**WS2812B Enable (GPIO16):**
- P-MOSFET gate driver
- **ACTIVE LOW**: LOW = MOSFET ON (WS2812B powered), HIGH = MOSFET OFF

### LEDC PWM Configuration

**Timer Settings:**
```c
.freq_hz = 25000,              // 25kHz (above human hearing)
.duty_resolution = LEDC_TIMER_10_BIT,  // 1024 levels (0-1023)
.clk_cfg = LEDC_AUTO_CLK,      // Automatic clock selection
```

**Why 10-bit, not 13-bit:**
- Constraint: `frequency × 2^resolution ≤ APB_CLK_FREQ`
- 25kHz × 2^13 = 204.8 MHz > APB_CLK_FREQ (80 MHz typical)
- 25kHz × 2^10 = 25.6 MHz < APB_CLK_FREQ ✓
- 1024 levels sufficient for smooth motor intensity control

---

## Consequences

### Benefits

- **Power efficiency**: Back-EMF monitoring (GPIO0) uses µA vs mA for continuous sensing
- **Fast emergency response**: GPIO1 ISR capability enables immediate motor coast
- **RTC wake support**: GPIO1 can wake from deep sleep for button press
- **No PCB rework**: Jumper from GPIO18 to GPIO1 preserves hardware investment
- **Clean on-board LED**: GPIO15 status LED always available (no case dependency)
- **WS2812B power control**: GPIO16 P-MOSFET enables therapy LED power gating
- **Motor control**: GPIO19/20 high-current pins suitable for H-bridge PWM

### Drawbacks

- **GPIO19/20 crosstalk risk**: Silicon issue during boot (mitigated by pull-downs)
- **Jumper wire required**: GPIO18→GPIO1 connection for ISR support
- **Limited GPIO expansion**: Most pins assigned, little room for future features
- **ADC1 only**: Avoids ADC2/WiFi conflict but limits analog inputs

---

## Options Considered

### Option A: GPIO0 for Back-EMF (Selected)

**Pros:**
- Continuous motor monitoring with minimal power (µA ADC input impedance)
- No resistor divider power drain
- ADC1_CH0 avoids WiFi conflicts

**Cons:**
- GPIO0 also used for boot mode (requires careful reset handling)

**Selected:** YES
**Rationale:** Power efficiency critical for 20+ minute sessions

### Option B: GPIO2 for Back-EMF (Rejected)

**Pros:**
- ADC1_CH2 available
- Not involved in boot mode

**Cons:**
- Would require moving battery voltage to different pin
- No significant advantage over GPIO0

**Selected:** NO
**Rationale:** GPIO2 better suited for battery voltage (less frequent sampling)

### Option C: Frequent Battery Voltage Checks for Stall Detection (Rejected)

**Pros:**
- Single ADC channel for both battery and motor monitoring
- Simpler software

**Cons:**
- Resistor divider draws mA continuously (significant battery drain)
- Battery voltage doesn't directly indicate motor stall
- Would need very frequent sampling (>10Hz) for stall detection

**Selected:** NO
**Rationale:** Power consumption unacceptable, indirect stall indication

### Option D: Move H-bridge to GPIO16/17 (Rejected for now)

**Pros:**
- Avoids GPIO19/20 crosstalk issue entirely
- High-current capable pins

**Cons:**
- Would conflict with WS2812B (GPIO16 enable, GPIO17 data)
- Therapy LED valuable for user feedback
- External pull-downs adequately mitigate crosstalk

**Selected:** NO (deferred to future PCB revision)
**Rationale:** WS2812B therapy LED more valuable than eliminating already-mitigated crosstalk

---

## Related Decisions

### Related
- [AD004: Seeed XIAO ESP32-C6 Platform Selection](0004-seeed-xiao-esp32c6-platform-selection.md) - Hardware platform with GPIO constraints
- [AD006: Bilateral Cycle Time Architecture](0006-bilateral-cycle-time-architecture.md) - Motor timing uses these GPIO assignments
- [AD012: Dead Time Implementation Strategy](0012-dead-time-implementation-strategy.md) - GPIO write latency provides hardware dead time

---

## Implementation Notes

### Code References

GPIO definitions appear in multiple files:
- `src/motor_task.h` - Motor GPIO definitions (GPIO19/20)
- `src/ble_manager.h` - Status LED GPIO (GPIO15)
- `test/single_device_demo_jpl_queued.c` - Complete GPIO mapping
- `test/single_device_battery_bemf_test.c` - Battery + back-EMF GPIO

### Build Environment

All environments use the same GPIO assignments (hardware-specific).

### Testing & Verification

**GPIO Functionality Verified:**
- ✅ GPIO0: Back-EMF ADC readings (OUTA from H-bridge)
- ✅ GPIO1: Button ISR + RTC wake from deep sleep
- ✅ GPIO2: Battery voltage ADC (12-bit resolution)
- ✅ GPIO15: Status LED blink patterns (active LOW verified)
- ✅ GPIO16: WS2812B power enable (P-MOSFET control)
- ✅ GPIO17: WS2812B data (RMT peripheral, 800kHz protocol)
- ✅ GPIO19/20: H-bridge PWM (25kHz, 10-bit resolution)
- ✅ GPIO21: Battery monitor enable (P-MOSFET control)

**Known Issues:**
- GPIO19/20 crosstalk during boot: External pull-downs prevent shoot-through
- Potential future move to GPIO18 for H-bridge if therapy LED removed

**Power Consumption Measurements:**
- Back-EMF monitoring (GPIO0): <10µA (ADC input impedance)
- Battery voltage divider (GPIO2): ~300µA when enabled via GPIO21
- WS2812B (GPIO17): ~15mA per LED at 50% brightness

---

## JPL Coding Standards Compliance

- ✅ Rule #1: No dynamic memory - GPIO configuration structs statically allocated
- ✅ Rule #2: Fixed bounds - GPIO initialization loops bounded by pin count
- ✅ Rule #5: Return value checking - All `gpio_set_direction()` calls checked
- ✅ Rule #8: Defensive logging - GPIO state changes logged via ESP_LOGI

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: AD005 (Hardware Architecture Decisions)
Git commit: Current working tree

Additional documentation:
- `docs/GPIO_UPDATE_2025-10-17.md` - GPIO19/20 crosstalk analysis
- Hardware schematics (if available in separate repo)

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
