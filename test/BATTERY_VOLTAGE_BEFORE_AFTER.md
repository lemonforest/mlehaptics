# Battery Voltage Test - Quick Before/After Reference

## What Changed?

### ⚡ New Features Added
1. **Low Voltage Cutout (LVO)** - 3.2V threshold with visual warning
2. **20-Minute Session Limit** - Auto-shutdown after session complete
3. **Elapsed Time Display** - Shows MM:SS with each reading

---

## Before (Original)

### Behavior
```
=== Battery Voltage Monitor Hardware Test ===
Battery monitor enabled (GPIO21)
Reading battery every 1000ms...

Battery: 3.85V (Raw: 2.89V at GPIO2) [85%]
Battery: 3.84V (Raw: 2.88V at GPIO2) [84%]
Battery: 3.84V (Raw: 2.88V at GPIO2) [84%]
...
[Runs forever until manual button hold]

[Hold button 5 seconds]
Hold button for deep sleep...
5... 4... 3... 2... 1...
Entering deep sleep...
```

### Features
- ✅ Battery voltage reading every 1 second
- ✅ Percentage calculation
- ✅ Manual sleep via button (5s hold)
- ❌ No LVO protection
- ❌ No runtime limit
- ❌ No elapsed time display

---

## After (Enhanced)

### Behavior - Normal Operation

```
=== Battery Voltage Monitor Hardware Test ===
Checking battery voltage for LVO...
LVO check: Battery voltage = 3.85V [85%]
LVO check: PASSED - voltage OK for operation

Battery monitoring task started
Session duration: 20 minutes
Reading battery voltage every 1000ms...

Battery: 3.85V (Raw: 2.89V at GPIO2) [85%] - 0:01 elapsed
Battery: 3.84V (Raw: 2.88V at GPIO2) [84%] - 0:02 elapsed
Battery: 3.84V (Raw: 2.88V at GPIO2) [84%] - 0:03 elapsed
...
Battery: 3.67V (Raw: 2.76V at GPIO2) [67%] - 19:59 elapsed

============================================
   20-MINUTE SESSION COMPLETE
============================================
Session duration: 20 minutes
Total readings: 1200
Final battery: 3.67V [67%]

Gracefully entering deep sleep...
Press button to wake and start new session
============================================
```

### Behavior - LVO Triggered (3.0V-3.2V)

```
=== Battery Voltage Monitor Hardware Test ===
Checking battery voltage for LVO...
LVO check: Battery voltage = 3.15V [15%]

============================================
   LOW VOLTAGE CUTOUT (LVO) TRIGGERED
============================================
Battery voltage: 3.15V (threshold: 3.20V)
Providing visual warning (3 blinks)...
[LED BLINKS 3 TIMES on GPIO15]
Charge battery to at least 3.20V to resume operation
============================================

[Enters deep sleep immediately - no session starts]
```

### Behavior - Critical Battery (<3.0V)

```
=== Battery Voltage Monitor Hardware Test ===
Checking battery voltage for LVO...
LVO check: Battery voltage = 2.85V [0%]

============================================
   LOW VOLTAGE CUTOUT (LVO) TRIGGERED
============================================
Battery voltage: 2.85V (threshold: 3.20V)
Battery critically low (2.85V) - no visual warning
Charge battery to at least 3.20V to resume operation
============================================

[Enters deep sleep immediately - NO LED blinks - battery protection]
```

### Features
- ✅ Battery voltage reading every 1 second
- ✅ Percentage calculation
- ✅ Manual sleep via button (5s hold)
- ✅ **NEW: LVO protection at 3.2V**
- ✅ **NEW: 3-blink warning (3.0V-3.2V)**
- ✅ **NEW: No blink protection (<3.0V)**
- ✅ **NEW: 20-minute auto-shutdown**
- ✅ **NEW: Elapsed time (MM:SS)**
- ✅ **NEW: Session statistics**

---

## Key Differences Summary

| Feature | Before | After |
|---------|--------|-------|
| **LVO Check** | None | ✅ 3.2V threshold |
| **Visual Warning** | None | ✅ 3 blinks (3.0V-3.2V) |
| **Battery Protection** | None | ✅ No blink (<3.0V) |
| **Runtime Limit** | Infinite | ✅ 20 minutes |
| **Elapsed Time** | None | ✅ MM:SS format |
| **Auto-Shutdown** | Manual only | ✅ After 20 min |
| **Session Stats** | None | ✅ Duration, readings, final voltage |
| **Wake Behavior** | Normal start | ✅ LVO re-check |

---

## Build Command (Same)

```cmd
pio run -e battery_voltage_test -t upload && pio device monitor
```

---

## Quick Test Scenarios

### ✅ Test 1: Normal Operation (Battery ≥3.2V)
**Expected:** LVO passes → 20-minute session → auto-shutdown → wake for new session

### ✅ Test 2: Low Battery Warning (3.0V-3.2V)
**Expected:** LVO triggers → 3 blinks → immediate sleep → no session

### ✅ Test 3: Critical Battery (<3.0V)
**Expected:** LVO triggers → NO blinks → immediate sleep → no session

### ✅ Test 4: Manual Sleep (Anytime)
**Expected:** Hold button 5s → countdown → sleep → wake for new session

---

## Files Changed

### Modified
- ✏️ `test/battery_voltage_test.c` - LVO + session limit
- ✏️ `BUILD_COMMANDS.md` - Updated description

### Created
- 📄 `test/BATTERY_VOLTAGE_TEST_GUIDE.md` - Comprehensive guide
- 📄 `test/BATTERY_VOLTAGE_LVO_IMPLEMENTATION_SUMMARY.md` - Detailed summary
- 📄 `test/BATTERY_VOLTAGE_BEFORE_AFTER.md` - This document

---

## Ready to Test! 🚀

```cmd
pio run -e battery_voltage_test -t upload && pio device monitor
```

**What to look for:**
1. "Checking battery voltage for LVO..." on startup
2. "LVO check: PASSED" if battery ≥3.2V
3. Elapsed time in format "0:01", "0:02", etc.
4. Auto-shutdown after 20 minutes
5. Session statistics at end

---

**Quick Reference Created:** November 2, 2025  
**Project:** MLE Haptics EMDR Pulser
