# Single Device Battery + Back-EMF Test - Quick Guide

**Test:** `single_device_battery_bemf_test`  
**Purpose:** Characterize back-EMF behavior and validate integrated battery management

## Quick Start

```bash
pio run -e single_device_battery_bemf_test -t upload && pio device monitor
```

## What This Test Does

### Motor Control (4 Research Modes)
- Mode 1: 1Hz @ 50% duty (250ms motor, 250ms coast)
- Mode 2: 1Hz @ 25% duty (125ms motor, 375ms coast)
- Mode 3: 0.5Hz @ 50% duty (500ms motor, 500ms coast)
- Mode 4: 0.5Hz @ 25% duty (250ms motor, 750ms coast)

### Battery Monitoring
- **Startup**: LVO check - sleep if < 3.2V (with 3-blink warning if ≥ 3.0V)
- **Runtime**: Check every 10 seconds
- **Warning**: 3 blinks on GPIO15 (active LOW) if 3.0-3.2V
- **Critical**: Deep sleep if < 3.0V

### Back-EMF Sensing
- **GPIO0** (ADC1_CH0) with resistive summing network
- **THREE readings per pulse**: during drive + immediate coast + 10ms settled
- **Both directions**: Forward and reverse sampled
- **Timing**: Active only during first 10 seconds of each mode
- **Restart**: Button press cycles modes and restarts sampling

### LED Indication
- **First 10 seconds**: RED @ 20%, blinks with motor (sampling mode)
- **10s - 19min**: OFF (battery conservation)
- **Last minute**: RED @ 20%, blinks with motor (warning)

### Controls
- **Button press**: Cycle modes (1→2→3→4→1), restart 10s sampling
- **Button hold 5s**: Emergency shutdown (purple blink)
- **20 minutes**: Auto deep sleep

## Expected Serial Output

### Back-EMF (First 10 Seconds)
```
FWD: Drive: GPIO0=2400mV → +1500mV | Coast-Immed: GPIO0=800mV → -1700mV | Coast-Settled: GPIO0=1200mV → -900mV
REV: Drive: GPIO0=900mV → -1500mV | Coast-Immed: GPIO0=2700mV → +2100mV | Coast-Settled: GPIO0=2300mV → +1300mV
```

**Reading Meanings:**
- **Drive**: Sampled during active motor drive (verifies circuit works)
- **Coast-Immed**: Right when coast begins (peak back-EMF)
- **Coast-Settled**: After 10ms (filtered/decayed value)

### Battery (Every 10 Seconds)
```
Battery: 3.85V [85%]
```

### Mode Change
```
=== Mode Change ===
New mode: 1Hz@25%
Restarting 10-second sampling window
```

### Last Minute Warning
```
Last minute warning - LED synced with motor
```

## What to Look For

1. **Drive readings ≠ 1650mV**: Proves circuit is working
2. **Forward vs Reverse**: Should show opposite polarity
3. **Immediate > Settled**: Coast readings should decay
4. **Filter Performance**: PWM noise should be removed
5. **Battery Efficiency**: Compare voltage drop across modes

## Circuit Requirements

### ⚠️ CRITICAL: Back-EMF Connection Point

**INCORRECT** (old schematic - gives baseline readings only):
```
GPIO0 ← Connected to motor_ctrl_a (ESP32 PWM output)
```

**CORRECT** (required for proper back-EMF sensing):
```
GPIO0 ← Connected to motor_out_a (H-bridge output to motor)
```

### Back-EMF Summing Network (GPIO0)
```
3.3V ─[10kΩ]─┬─ GPIO0 (ADC1_CH0)
              │
OUTA ─[10kΩ]─┤  ← Must connect to H-bridge OUTPUT, not control input!
              │
           [15nF]
              │
             GND
```

**Requirements:**
- ✅ Connect to motor_out_a (H-bridge output)
- ✅ R_load must be NOT POPULATED
- ✅ 15nF capacitor for PWM filtering
- ❌ Do NOT connect to motor_ctrl_a (PWM control signal)

**Why This Matters:**
- motor_ctrl_a = ESP32 GPIO signal (0-3.3V, no back-EMF)
- motor_out_a = H-bridge output (±3.3V with back-EMF when coasting)

### Battery Divider (GPIO2)
```
VBAT ─[3.3kΩ]─┬─ GPIO2 (ADC1_CH2)
               │
           [10kΩ]
               │
              GND
```
GPIO21 Battery Enable:
- HIGH on GPIO21 → N-FET ON → Pulls P-FET gate LOW → P-FET ON → Measurement enabled
- Circuit uses N-FET + P-FET pair for level shifting/current handling

## Diagnostic Guide

### Symptom: All readings ~1650mV
**Cause**: Back-EMF sense connected to motor_ctrl_a instead of motor_out_a  
**Fix**: Rewire/redesign to connect GPIO0 summing network to H-bridge output

### Symptom: Only positive values, no directional info
**Cause**: Same as above - measuring control signal not motor output  
**Fix**: Connect to motor_out_a

### Symptom: Drive reading = 1650mV ± 50mV
**Likely**: Circuit issue - check summing network connections  
**Also check**: R_load populated (should be NOT populated)

### Symptom: Drive reading shows ±1000-2000mV range
**Good!**: Circuit is working properly  
**Next**: Compare coast readings to understand motor behavior

### Symptom: Battery warning persists
**Cause**: Battery genuinely low (< 3.2V)  
**Fix**: Charge battery to > 3.2V before testing

### Symptom: Motor not running
**Test**: Run hbridge_pwm_test.c first to verify H-bridge  
**Check**: PWM signals on GPIO19/GPIO20

### Symptom: LED not blinking
**Check**: GPIO16 enable (should be LOW)  
**Check**: WS2812B power and data connections

## Power Consumption Notes

**Summing Network Idle Current:**
- When coasting (OUTA floating): ~33nA (negligible)
- During drive: ~165-330µA (depending on direction)
- No enable circuitry needed - circuit naturally low-power when idle

## Files Modified

- ✅ `test/single_device_battery_bemf_test.c` - Main test (3 readings, synced LED)
- ✅ `platformio.ini` - Build environment
- ✅ `scripts/select_source.py` - Source mapping
- ✅ `BUILD_COMMANDS.md` - Build commands
- ✅ `BACK_EMF_DURING_DRIVE_UPDATE.md` - Change summary

---

**Status**: Ready to test after fixing motor_out_a connection  
**Next Step**: Verify back-EMF sense connects to H-bridge output, then build and test
