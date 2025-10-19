# LEDC Resolution Fix - Project History

**Date:** October 19, 2025  
**Issue:** Device unresponsive when using LEDC PWM for H-bridge control  
**Resolution:** Changed LEDC resolution from 13-bit to 10-bit  
**Status:** ✅ RESOLVED - `hbridge_pwm_test` now working successfully

---

## Problem Summary

The ESP32-C6 device became completely unresponsive (no serial output, no LED) when attempting to use LEDC PWM for H-bridge motor control. This occurred even though basic GPIO control worked perfectly.

## Root Cause

**LEDC resolution was set too high for the PWM frequency:**

```c
// ORIGINAL (BROKEN)
#define PWM_FREQUENCY_HZ        25000
#define PWM_RESOLUTION          LEDC_TIMER_13_BIT  // ❌ WRONG!
```

**The Math Problem:**
- 13-bit @ 25kHz requires: 25,000 Hz × 2^13 = 25,000 × 8,192 = **204.8 MHz clock**
- ESP32-C6 APB clock: Only 80 MHz or 160 MHz available
- **Result:** `ledc_timer_config()` fails, causing system crash before any serial output

## Solution

**Changed to 10-bit resolution:**

```c
// FIXED (WORKING)
#define PWM_FREQUENCY_HZ        25000
#define PWM_RESOLUTION          LEDC_TIMER_10_BIT  // ✅ CORRECT!
```

**Why This Works:**
- 10-bit @ 25kHz requires: 25,000 Hz × 2^10 = 25,000 × 1,024 = **25.6 MHz clock**
- ESP32-C6 80 MHz APB can easily provide this
- **Result:** LEDC configures successfully, motor control works perfectly!

## Clock Requirement Formula

**Always verify before choosing resolution:**

```
Required Clock (Hz) = PWM Frequency (Hz) × 2^Resolution_Bits

Examples for 25kHz PWM:
- 8-bit:  25,000 × 256   = 6.4 MHz    ✅ (overkill, low precision)
- 10-bit: 25,000 × 1,024 = 25.6 MHz   ✅ (perfect balance)
- 13-bit: 25,000 × 8,192 = 204.8 MHz  ❌ (impossible!)
```

**ESP32-C6 Available Clocks:**
- APB Clock: 80 MHz or 160 MHz
- XTAL Clock: 40 MHz
- Maximum practical LEDC frequency depends on resolution chosen

## Impact on Motor Control

**10-bit resolution is MORE than sufficient:**

```
60% Duty Cycle Comparison:
- 13-bit: 60% = 4,915 / 8,192 (0.073% precision)
- 10-bit: 60% = 614 / 1,023   (0.098% precision)

Motor Perceptibility:
- Humans cannot feel 0.098% vs 0.073% precision difference
- 1,024 steps is already far more precise than needed
- Motor inertia and bearing friction mask tiny variations
```

**Conclusion:** 10-bit gives plenty of control precision while working within hardware limits.

## Diagnostic Process

### Tests Created

1. **`ledc_blink_test.c`** (SUCCESSFUL)
   - Simple LED blink using LEDC
   - 8-bit @ 1kHz (very easy clock requirement)
   - **Result:** Proved LEDC peripheral works correctly
   - **Purpose:** Isolated LEDC from H-bridge complexity

2. **`hbridge_pwm_incremental.c`** (DIAGNOSTIC - NOW DELETED)
   - Initialized LEDC but used GPIO control
   - **Purpose:** Determine if LEDC init OR LEDC usage caused crash
   - **Result:** Still had 13-bit resolution bug, so didn't help much
   - **Status:** Deleted - `ledc_blink_test` captures the same diagnostic value

3. **`hbridge_pwm_test.c`** (NOW WORKING! ✅)
   - Full H-bridge PWM control at 60% duty
   - Originally 13-bit (broken), now 10-bit (working)
   - **Result:** Device responsive, motor control works perfectly!

## Files Modified

### Updated Files
- ✅ `test/hbridge_pwm_test.c` - Changed resolution to 10-bit
- ✅ `test/README.md` - Documented the fix and added lessons learned
- ✅ `platformio.ini` - Removed obsolete `hbridge_pwm_incremental` environment
- ✅ `scripts/select_source.py` - Removed obsolete test mapping

### Deleted Files
- ❌ `test/hbridge_pwm_incremental.c` - Redundant diagnostic test
- ❌ `sdkconfig.hbridge_pwm_incremental` - Build configuration (obsolete)

### Working Test Suite
1. ✅ `test/ledc_blink_test.c` - Verify LEDC peripheral
2. ✅ `test/hbridge_test.c` - Verify H-bridge with GPIO
3. ✅ `test/hbridge_pwm_test.c` - Verify H-bridge with PWM (60% duty)

## Lessons Learned

### CRITICAL: Always Check Clock Requirements

**Before choosing LEDC parameters, calculate:**
```
Required_Clock = Frequency × 2^Resolution
```

**Then verify against ESP32-C6 capabilities:**
- APB Clock: 80 MHz or 160 MHz (configurable)
- XTAL Clock: 40 MHz (if using LEDC_USE_XTAL_CLK)

### Resolution Selection Guidelines

**For motor control (25kHz PWM):**
- ✅ **8-bit:** Good for simple on/off (0-255 range)
- ✅ **10-bit:** Perfect for variable speed (0-1023 range) - **RECOMMENDED**
- ⚠️ **12-bit:** Possible but tight (requires 102.4 MHz) - use only if needed
- ❌ **13-bit:** Impossible at 25kHz (requires 204.8 MHz)

**Trade-off:** Higher resolution = more clock frequency required

### Debugging Embedded Systems

**Lesson:** When a device becomes completely unresponsive (no serial output), the crash is happening during initialization, before any logging can occur.

**Better diagnostic approach:**
1. Create minimal test (like `ledc_blink_test`) to isolate peripheral
2. Use oscilloscope to verify PWM output even without serial
3. Calculate clock requirements BEFORE configuring hardware
4. Start with conservative parameters, then optimize

## Future Considerations

### If Higher Resolution Needed

**Option 1: Lower PWM Frequency**
```c
#define PWM_FREQUENCY_HZ        12500   // Half frequency
#define PWM_RESOLUTION          LEDC_TIMER_13_BIT  // Now possible!
// Required: 12,500 × 8,192 = 102.4 MHz (works with 160 MHz APB)
```

**Option 2: Use Lower Frequency for Fine Control**
```c
// Keep 25kHz for base PWM, add software "super-resolution"
// Use 10-bit hardware + dithering for 12-bit effective resolution
```

### Audible PWM Frequency

**Why 25kHz?**
- Above human hearing range (~20 Hz to 20 kHz)
- Motor won't produce audible PWM whine
- High enough to be smooth, low enough to be efficient

**Lower frequencies create audible noise:**
- 1 kHz: Loud PWM whine (VERY annoying)
- 5 kHz: Audible buzz (unpleasant)
- 10 kHz: Faint whine (borderline)
- 25 kHz: Silent (outside hearing range)

## Related Documentation

- **Test Documentation:** `test/README.md` - Complete test suite guide
- **Chat History:** "H-bridge PWM control test" - Detailed troubleshooting conversation
- **ESP-IDF LEDC Driver:** [ESP-IDF LEDC Documentation](https://docs.espressif.com/projects/esp-idf/en/v5.3.0/esp32c6/api-reference/peripherals/ledc.html)

---

## Conclusion

✅ **Problem Solved!** The `hbridge_pwm_test` is now working perfectly with 10-bit resolution.

**Key Takeaway:** Always calculate required clock frequencies before configuring LEDC parameters. The ESP32-C6 is powerful, but not infinite - respect the hardware limits!

**Next Steps:** Continue with bilateral timing implementation using working PWM motor control.

---

*Document created by Claude Sonnet 4.5 (Anthropic) - October 19, 2025*
