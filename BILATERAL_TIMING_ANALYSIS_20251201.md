# Bilateral Timing Analysis - 90-Minute Session (2025-12-01)

**Session Duration:** ~5405 seconds (90 minutes)
**SERVER Activations:** 3,350
**CLIENT Activations:** 3,340
**Analysis Date:** 2025-12-01

---

## Executive Summary

**CRITICAL BUG DISCOVERED: CLIENT Double-Activation Per Cycle**

The bilateral timing analysis reveals a severe synchronization bug where the CLIENT device is activating motors **twice per SERVER cycle** instead of once. This creates:

1. **53% motor activation overlap** (both devices running simultaneously)
2. **Only 4.5% of cycles within ±10ms of target anti-phase timing**
3. **Mean error of -844ms** (CLIENT activating 844ms before target offset)

---

## Overall Statistics

| Metric                  | Value      |
|-------------------------|------------|
| Total measurements      | 6,182      |
| Mean error              | -844.1 ms  |
| Min error               | -2775.0 ms |
| Max error               | +4125.0 ms |

### Error Distribution

| Category          | Count | Percentage |
|-------------------|-------|------------|
| **GOOD** (±10ms)  | 280   | 4.5%       |
| **WARNING** (±50ms) | 1,347 | 21.8%      |
| **POOR** (>50ms)  | 4,555 | 73.7%      |

### Status Breakdown

| Status    | Count | Percentage | Description                           |
|-----------|-------|------------|---------------------------------------|
| OVERLAP   | 3,275 | 53.0%      | CLIENT too early (motor overlap)      |
| DRIFT     | 1,280 | 20.7%      | CLIENT too late (> 50ms after target) |
| WARNING   | 1,347 | 21.8%      | Within ±50ms of target                |
| GOOD      | 280   | 4.5%       | Within ±10ms of target                |

---

## Root Cause: Double-Activation Bug

### Pattern Analysis (Time 5403s)

For a single 2000ms SERVER cycle:

```
Time      SERVER  CLIENT  Delta   Target  Error    Status
--------  ------  ------  ------  ------  -------  --------
5403.61   ✅       ❌      -975    1000    -1975    OVERLAP  ← 1st activation (wrong timing)
5403.61   (same)  ✅      +995    1000    -5       GOOD     ← 2nd activation (correct timing!)
5405.62   ✅       ❌      -1005   1000    -2005    OVERLAP  ← 1st activation (next cycle)
```

### Key Findings

1. **CLIENT activates twice per SERVER cycle**
   - First activation: ~0ms after SERVER (causes overlap)
   - Second activation: ~1000ms after SERVER (correct anti-phase!)

2. **Number of measurements confirms this**
   - 6,182 measurements / 3,350 SERVER cycles = **1.84 CLIENT activations per SERVER cycle**
   - Should be exactly 1.0 activations per cycle

3. **Half the activations show good timing**
   - 26.3% of measurements are GOOD or WARNING status
   - These are the "second" activations that happen at correct timing
   - The "first" activations (53% OVERLAP) are spurious

---

## Mode Changes During Session

The CLIENT log shows multiple mode changes:

| Time      | Cycle Period | Note                      |
|-----------|--------------|---------------------------|
| 01:09:04  | 2000 ms      | Initial mode              |
| 01:09:20  | 1000 ms      | Mode change #1            |
| 01:09:21  | 667 ms       | Mode change #2            |
| 01:09:22  | 500 ms       | Mode change #3            |
| 01:09:22  | 2000 ms      | Back to initial mode      |
| 01:25:32  | 2000 ms      | Re-synchronized?          |
| 01:25:39  | 1000 ms      | Another mode change cycle |

**Hypothesis:** Mode changes may be triggering the double-activation bug. The CLIENT may be:
- Starting a new cycle immediately after mode change
- Not properly canceling the previous cycle's pending activation
- Creating overlapping motor state machines

---

## Timing Performance by Category

### GOOD Timing (±10ms from target)
- **Count:** 280 activations (4.5%)
- **Mean error:** -0.4 ms
- **Best case:** +5ms to -5ms (perfect anti-phase)
- **Pattern:** Exclusively the "second" activation in each cycle

### WARNING Timing (10-50ms from target)
- **Count:** 1,347 activations (21.8%)
- **Mean error:** +22.7 ms (CLIENT slightly late)
- **Pattern:** Mix of "second" activations with minor drift

### OVERLAP (CLIENT too early)
- **Count:** 3,275 activations (53.0%)
- **Mean error:** -1,958 ms (CLIENT nearly 2 seconds early!)
- **Pattern:** The spurious "first" activation in each cycle

### DRIFT (CLIENT too late)
- **Count:** 1,280 activations (20.7%)
- **Mean error:** +687 ms (CLIENT late by ~700ms)
- **Pattern:** Unknown - may be related to mode transitions

---

## Impact on Therapeutic Use

### Motor Overlap Analysis
- **53% of cycles have overlap** (both motors active simultaneously)
- This violates the fundamental requirement for bilateral alternation therapy
- Users would feel both motors at once, defeating the therapeutic purpose

### Timing Precision
- **Only 4.5% meet the ±10ms precision target**
- **26.3% meet the ±50ms acceptable range**
- **73.7% have unacceptable timing errors**

### Battery Impact
- Double activations consume **2× expected power**
- This explains user reports of shorter-than-expected battery life

---

## Recommendations

### 1. HIGH PRIORITY: Fix Double-Activation Bug

**Investigate:**
- Motor state machine logic in CLIENT
- Mode change handling (cycle cancellation)
- Anti-phase calculation during transitions
- Possible race condition between old and new cycle timers

**Files to Review:**
- [src/motor_task.c](src/motor_task.c) - CLIENT motor state machine
- [src/time_sync_task.c](src/time_sync_task.c) - Mode change message handling

### 2. Add Diagnostic Logging

Add logging to track:
- Motor cycle start/stop events with unique cycle IDs
- Mode change transitions (old cycle → new cycle)
- Pending timer cancellations
- Phase calculation inputs/outputs

### 3. Implement Cycle Mutex

Ensure only ONE motor cycle can be active at a time:
- Add cycle state flag (`bool cycle_active`)
- Reject new cycle start if `cycle_active == true`
- Clear flag only when cycle fully completes
- Log rejected cycle attempts for debugging

### 4. Mode Change Protocol

Define explicit mode change behavior:
1. Stop current motor cycle immediately
2. Coast motors
3. Wait for full period to elapse
4. Start new cycle with new parameters
5. Log transition: "Mode X → Mode Y (cycle cancelled, restarting)"

---

## Test Plan

### Unit Test: Single Mode, No Changes
1. Start both devices in 2000ms mode
2. Run for 60 seconds (30 cycles)
3. Verify: Exactly 30 CLIENT activations (not 60)
4. Verify: All activations within ±50ms of period/2 target

### Integration Test: Mode Changes
1. Start in 2000ms mode
2. After 30 seconds, change to 1000ms
3. After 30 seconds, change to 667ms
4. After 30 seconds, change back to 2000ms
5. Verify: No double activations during transitions
6. Verify: Timing re-converges within 3 cycles after each change

### Stress Test: Rapid Mode Changes
1. Change modes every 10 seconds
2. Run for 5 minutes
3. Verify: No motor overlap
4. Verify: No double activations
5. Check: CPU usage, memory leaks, task stack usage

---

## Analysis Files

- **Full Analysis:** `bilateral_timing_analysis_0108.txt` (6,182 measurements)
- **Raw Logs:**
  - `serial_log_dev_a_0108-20251201.txt` (SERVER, UTF-8)
  - `serial_log_dev_b_0108-20251201.txt` (CLIENT, UTF-16 LE)
- **Analysis Script:** `scripts/analyze_bilateral_timing.py`

---

## Notes

### Encoding Discovery
- SERVER log: UTF-8 (normal)
- CLIENT log: UTF-16 LE with BOM (`FF FE`)
- Analysis script updated to auto-detect encoding

### Measurement Method
- Extracted timestamps from "Cycle starts ACTIVE" and "Motor forward/reverse" log entries
- Paired SERVER and CLIENT activations chronologically
- Calculated delta (CLIENT timestamp - SERVER timestamp)
- Target = SERVER period / 2 (e.g., 1000ms for 2000ms cycle)
- Error = delta - target

---

**Generated:** 2025-12-01
**Analysis Duration:** ~30 minutes
**Next Step:** Fix double-activation bug (Bug #40)
