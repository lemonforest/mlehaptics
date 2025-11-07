# Back-EMF Sampling Update - November 2025

## Problem Identified

The original implementation was sampling back-EMF **ONLY during coast**, which resulted in baseline readings (1653-1658mV) with no useful signal. This could be due to:
1. Motor stopping very quickly during coast
2. Circuit issue preventing proper sensing
3. Insufficient signal to measure during coast

## Solution Implemented

Added a **third reading point** to sample back-EMF **DURING motor operation** (while PWM is actively driving), in addition to the two coast readings. This helps:

1. **Verify circuit functionality** - Should see something other than baseline
2. **Understand motor behavior** - Compare drive vs coast readings
3. **Debug the issue** - Determine if it's fast motor stop or circuit problem

## Changes Made

### File: `test/single_device_battery_bemf_test.c`

**Modified both FORWARD and REVERSE half-cycles to include 3 readings:**

#### Previous Sequence (2 readings):
```c
1. Drive motor
2. Wait for motor_on_ms
3. Coast
4. Sample immediately
5. Wait 10ms
6. Sample after settling
```

#### New Sequence (3 readings):
```c
1. Drive motor
2. Wait (motor_on_ms - 10ms)
3. ⭐ SAMPLE DURING DRIVE ⭐  [NEW]
4. Finish drive period (10ms)
5. Coast
6. Sample immediately
7. Wait 10ms
8. Sample after settling
```

### Updated Output Format

**Old:**
```
FWD: Immediate: GPIO0=1653mV → BEMF=+6mV | Settled: GPIO0=1655mV → BEMF=+10mV
```

**New:**
```
FWD: Drive: GPIO0=XXXXmV → YYYYmV | Coast-Immed: GPIO0=XXXXmV → YYYYmV | Coast-Settled: GPIO0=XXXXmV → YYYYmV
REV: Drive: GPIO0=XXXXmV → YYYYmV | Coast-Immed: GPIO0=XXXXmV → YYYYmV | Coast-Settled: GPIO0=XXXXmV → YYYYmV
```

## Expected Behavior

### During Drive Reading (NEW):
- **Should NOT be baseline (~1650mV)**
- Should show the summed value of drive voltage + any motor characteristics
- Forward and reverse should show different values
- This reading proves the circuit works!

### Immediate Coast Reading:
- Captures back-EMF right when coast begins
- Shows motor's "flywheel" effect
- May or may not be near baseline depending on motor deceleration

### Settled Coast Reading:
- Shows filtered/decayed value after 10ms
- Likely will be near baseline if motor stops quickly
- Helps characterize filter performance

## What This Will Tell You

### If Drive Reading ≠ Baseline (~1650mV):
✅ **Circuit works!** 
- Proves ADC and summing network are functional
- If coast readings ARE baseline → Motor stops VERY quickly
- Motor may need different sensing strategy (during drive only)

### If Drive Reading = Baseline (~1650mV):
❌ **Circuit problem suspected**
- Check summing network connections
- Verify R_load is NOT populated
- Verify 10kΩ resistors on 3.3V and OUTA
- Check 15nF capacitor placement

### If Forward/Reverse Drive Readings Are Different:
✅ **Expected and good!**
- Shows H-bridge is working correctly
- Proves directional control
- Validates summing network operation

## Testing Procedure

1. **Build and flash:**
   ```bash
   pio run -e single_device_battery_bemf_test -t upload && pio device monitor
   ```

2. **Observe first 10 seconds** - Look for drive readings that differ from baseline

3. **Press button** to cycle through modes and restart sampling

4. **Document all three readings** for each direction

5. **Compare patterns:**
   - Drive vs Coast values
   - Forward vs Reverse symmetry
   - Changes across different modes

## Diagnostic Flowchart

```
Start Test
    ↓
Drive Reading = ~1650mV?
    ├─ NO → Circuit works! ✅
    │        ↓
    │   Coast readings = ~1650mV?
    │        ├─ YES → Motor stops very fast
    │        └─ NO → Motor coasts measurably
    │
    └─ YES → Circuit problem! ❌
             Check hardware connections
```

## Files Modified

- ✅ `test/single_device_battery_bemf_test.c` (motor_task - both half-cycles)
- ✅ File header comments updated (3 readings documented)
- ✅ Startup messages updated (app_main)

## Build Command

```bash
pio run -e single_device_battery_bemf_test -t upload && pio device monitor
```

## What To Report Back

Please share your serial output showing:
1. **Drive readings** - Are they different from 1650mV?
2. **Forward vs Reverse comparison** - Symmetric as expected?
3. **Coast readings** - Still baseline or showing signal?
4. **Mode comparison** - Any differences between 1Hz/0.5Hz or 50%/25%?

This will help us understand whether we have a circuit issue or a fast-stopping motor!

---

**Status:** ✅ Changes complete and ready to test
**Date:** November 2025
**Test Environment:** `single_device_battery_bemf_test`
