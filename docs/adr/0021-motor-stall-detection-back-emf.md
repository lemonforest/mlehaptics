# 0021: Motor Stall Detection via Back-EMF Sensing

**Date:** 2025-10-15
**Phase:** 0.4
**Status:** Accepted
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of motor stall protection for safety-critical EMDR therapy,
facing the need for current sensing without dedicated hardware,
we decided for back-EMF sensing with resistive voltage summing,
and neglected battery voltage drop monitoring as primary method,
to achieve power-efficient continuous motor health monitoring,
accepting 165µA continuous bias current and 10ms measurement delay.

---

## Problem Statement

ERM motor stall condition (120mA vs 90mA normal) could damage H-bridge MOSFETs and accelerate battery drain. No dedicated current sensing hardware exists in discrete MOSFET design. Battery voltage monitoring for stall detection is power-inefficient (resistor divider draws ~248µA continuously). Back-EMF can swing from -3.3V to +3.3V, but ESP32-C6 ADC only accepts 0V to 3.3V.

---

## Context

**Technical Constraints:**
- Discrete MOSFET H-bridge design (no integrated current sensing)
- ESP32-C6 ADC: 0V to 3.3V input range
- Motor back-EMF: -3.3V to +3.3V range (bidirectional)
- Battery divider: 248µA continuous draw when enabled
- Power budget: Target <1mA standby current

**Safety Requirements:**
- Detect stalled motor to prevent MOSFET damage
- Continuous monitoring capability during therapy sessions
- Graceful degradation to LED stimulation if motor fails

**Hardware Resources:**
- GPIO0 (ADC1_CH0) available for back-EMF sensing
- GPIO2 (ADC1_CH2) reserved for battery voltage monitoring

---

## Decision

We will implement software-based motor stall detection using power-efficient back-EMF sensing as the primary method.

**Implementation:**

1. **Back-EMF Sensing (Primary Method):**
   - GPIO0 (ADC1_CH0) reads OUTA from H-bridge during coast periods
   - Resistive summing network biases and scales ±3.3V to 0-3.3V ADC range
   - Low-pass filter (5kΩ + 22nF, fc ≈ 1.45 kHz) removes 25kHz PWM noise
   - 10ms coast delay allows back-EMF and filter to stabilize
   - Stall threshold: back-EMF magnitude < 1000mV

2. **Battery Voltage Drop Analysis (Backup Method):**
   - GPIO2 (ADC1_CH2) monitors battery voltage
   - Compare voltage drop: no-load vs. motor-active
   - Stall threshold: voltage drop > 300mV suggests excessive current

3. **Signal Conditioning Circuit:**
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
   ```

4. **Voltage Mapping:**
   - V_GPIO1 = (3.3V + V_OUTA) / 2
   - V_OUTA = -3.3V → V_GPIO1 = 0V (ADC minimum)
   - V_OUTA = 0V → V_GPIO1 = 1.65V (ADC center)
   - V_OUTA = +3.3V → V_GPIO1 = 3.3V (ADC maximum)

5. **Stall Response Protocol:**
   - Immediate coast: Set both H-bridge inputs low
   - Mechanical settling: 100ms vTaskDelay()
   - Reduced intensity restart: Retry at 50% intensity
   - LED fallback: Switch to LED stimulation if stall persists
   - Error logging: Record stall event in NVS for diagnostics

---

## Consequences

### Benefits

- **Power efficiency:** 165µA continuous vs. 248µA for battery monitoring (33% more efficient)
- **Continuous monitoring:** Can check motor health frequently without battery drain
- **Direct indication:** Stalled motor has no back-EMF (direct mechanical failure indicator)
- **Perfect ADC range utilization:** 100% of 0-3.3V range maps ±3.3V back-EMF
- **Therapeutic continuity:** Graceful degradation to LED stimulation preserves therapy session

### Drawbacks

- **165µA continuous bias current** (acceptable for 640mAh battery capacity)
- **10ms measurement delay** required for filter settling (negligible for 500ms cycles)
- **Requires coast period** to develop back-EMF (already part of motor control timing)
- **Component count:** Adds 2 resistors + 1 capacitor per motor to BOM

---

## Options Considered

### Option A: Battery Voltage Drop Monitoring (Rejected)

**Pros:**
- Simple implementation (single ADC read)
- No additional analog conditioning hardware

**Cons:**
- 248µA continuous power draw from resistor divider
- Less direct indication of motor stall
- Requires baseline vs. active comparison (two measurements)

**Selected:** NO
**Rationale:** 50% higher power consumption and indirect measurement make it inferior to back-EMF sensing

### Option B: Back-EMF Sensing with Voltage Summing (CHOSEN)

**Pros:**
- 33% more power efficient than battery method (165µA vs. 248µA)
- Direct mechanical failure indication
- Continuous monitoring capability
- Perfect ADC range utilization (100% of 0-3.3V)

**Cons:**
- Requires analog conditioning circuit
- 10ms settling delay needed

**Selected:** YES
**Rationale:** Superior power efficiency, direct indication, and continuous monitoring capability

### Option C: Integrated H-Bridge IC with Current Sensing (Future)

**Pros:**
- Hardware current sensing with dedicated sense resistor
- Thermal protection integrated
- Shoot-through protection via hardware interlocks
- Detailed fault reporting via SPI/I2C

**Cons:**
- Requires PCB redesign
- Higher component cost
- Not available for current discrete MOSFET design

**Selected:** NO (future enhancement)
**Rationale:** Excellent long-term solution, but back-EMF sensing is adequate for current hardware

---

## Related Decisions

### Related
- **AD005: Motor H-Bridge Control** - Defines H-bridge GPIO mappings and control signals
- **AD007: Battery Voltage Monitoring** - Defines battery ADC channel (GPIO2) as backup stall detection method
- **AD027: Modular Source File Architecture** - Battery monitor module calls stall detection

---

## Implementation Notes

### Code References

- Circuit analysis: `docs/architecture_decisions.md` AD021 (voltage summing equations)
- Future integration: `src/battery_monitor.c` (stall detection support functions)
- Test validation: `test/single_device_battery_bemf_test.c` lines 1-1500 (hardware validation)

### Circuit Analysis

**Voltage Summing Principle:**
```
By Kirchhoff's Current Law (ADC draws negligible current):
I_bias = I_signal
(3.3V - V_GPIO1) / R_bias = (V_GPIO1 - V_OUTA) / R_signal

With R_bias = R_signal = 10kΩ:
3.3V - V_GPIO1 = V_GPIO1 - V_OUTA
3.3V + V_OUTA = 2 × V_GPIO1

V_GPIO1 = (3.3V + V_OUTA) / 2
V_GPIO1 = 1.65V + 0.5 × V_OUTA
```

**Low-Pass Filter Characteristics:**
```
R_parallel = R_bias || R_signal = 10kΩ || 10kΩ = 5kΩ
f_c = 1 / (2π × R_parallel × C_filter)
f_c = 1 / (2π × 5kΩ × 22nF) ≈ 1.45 kHz

- Filters 25kHz PWM switching noise (17× attenuation, >94% reduction)
- Preserves ~100-200Hz motor back-EMF fundamental frequency
- Settles in ~0.55ms (5τ = 550µs, sufficient for 1ms+ coast measurement window)
```

### Build Environment

- **Environment Name:** `single_device_battery_bemf_test` (hardware validation)
- **Configuration File:** `sdkconfig.single_device_battery_bemf_test`
- **Hardware:** Seeed XIAO ESP32-C6 + TB6612FNG H-bridge

### Testing & Verification

**Hardware Testing Performed:**
- Validated voltage summing circuit: -3.3V maps to 0V, 0V maps to 1.65V, +3.3V maps to 3.3V
- Confirmed 22nF capacitor provides adequate PWM noise filtering
- Verified stall detection: Motor with blocked shaft shows <1000mV back-EMF
- Normal operation: Back-EMF magnitude 1000-2000mV during coast periods

**Known Limitations:**
- Requires 10ms coast period for accurate measurement
- R_load intentionally not populated (would reduce ADC range to 67%)
- Production uses 22nF capacitor (prototypes used 12nF, original design 15nF)

---

## JPL Coding Standards Compliance

- ✅ Rule #1: No dynamic memory allocation - Static circuit, no malloc
- ✅ Rule #2: Fixed loop bounds - Stall check during fixed coast periods
- ✅ Rule #3: No recursion - Linear stall detection algorithm
- ✅ Rule #5: Return value checking - ESP_ERROR_CHECK on ADC reads
- ✅ Rule #6: No unbounded waits - vTaskDelay() for 10ms settling time
- ✅ Rule #7: Watchdog compliance - Fast ADC reads don't block task
- ✅ Rule #8: Defensive logging - ESP_LOGI on stall detection events

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: AD021
Git commit: (phase 0.4 implementation)

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
