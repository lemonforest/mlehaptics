# Bilateral Phase Error Analysis - Final Summary

**Date:** 2025-12-01
**Issue:** CLIENT motor activation consistently 660ms late relative to ideal antiphase target
**Status:** ✅ FIXED (Bug #40) - 98.6% improvement | 🔬 ENHANCEMENT (Bug #41) - RTT-based outlier rejection implemented

---

## Executive Summary

**The CLIENT is NOT double-activating motors.** The original "double activation" finding was an analysis script artifact from counting both ACTIVE and INACTIVE state transitions.

**The REAL bug:** CLIENT motors activate consistently **660ms too late** relative to ideal antiphase timing. Over a 90-minute Mode 0 baseline session (2,699 cycles), CLIENT showed:
- **Mean phase error:** +662ms
- **Phase error range:** +185ms to +4735ms (all positive = all too late)
- **Zero acceptable cycles:** 0% within ±50ms of target

This is a **systematic offset**, not random jitter, indicating a fundamental flaw in the INACTIVE state drift correction algorithm.

---

## Corrected Measurement Methodology

### Analysis Script Fix

The corrected script ([scripts/analyze_bilateral_phase.py](scripts/analyze_bilateral_phase.py)) now:
1. Counts only "Cycle starts ACTIVE" for both SERVER and CLIENT
2. Ignores CLIENT "Cycle starts INACTIVE" (motor coasting, not activation)
3. Calculates phase error from ideal antiphase target (SERVER_time + period/2)
4. Produces 1:1 measurement ratio (2,699 measurements for 2,699 cycles)

### CLIENT Timing Pattern (Verified from Logs)

```
T=11031ms: INACTIVE starts (drift correction calculates wait time)
T=12041ms: ACTIVE starts (+1010ms) ← Motor activates
T=12291ms: Motor coasting (+250ms motor ON)
T=13041ms: INACTIVE starts (+1000ms from ACTIVE start)
T=14001ms: ACTIVE starts (+960ms) ← Motor activates
T=14251ms: Motor coasting (+250ms motor ON)
T=15001ms: INACTIVE starts (+1000ms from ACTIVE start)
T=16001ms: ACTIVE starts (+1000ms) ← Motor activates
...
```

**Pattern:** CLIENT correctly alternates INACTIVE → ACTIVE every ~1000ms (total ~2000ms cycle for 1Hz).

---

## Phase Error Details

### Mode 0 Baseline (2000ms cycle, 25% duty)

**Ideal Bilateral Timing:**
```
SERVER cycle structure:
  T=0ms:    ACTIVE starts (motor ON 250ms, coast 750ms = 1000ms total ACTIVE)
  T=1000ms: INACTIVE starts (coast 1000ms)
  T=2000ms: Next cycle ACTIVE starts

CLIENT should do:
  T=1000ms: ACTIVE starts (antiphase target = SERVER_start + period/2)
  T=1500ms: INACTIVE starts
  T=3000ms: Next cycle ACTIVE starts
```

**Actual CLIENT Timing (from analysis):**
```
SERVER ACTIVE at T=10320ms
  → CLIENT should start ACTIVE at T=10320 + 1000 = T=11320ms
  → CLIENT actually starts ACTIVE at T=12041ms
  → Phase error: +721ms

SERVER ACTIVE at T=12320ms
  → CLIENT should start ACTIVE at T=12320 + 1000 = T=13320ms
  → CLIENT actually starts ACTIVE at T=14005ms
  → Phase error: +685ms

SERVER ACTIVE at T=14320ms
  → CLIENT should start ACTIVE at T=14320 + 1000 = T=15320ms
  → CLIENT actually starts ACTIVE at T=16001ms
  → Phase error: +681ms
```

**Pattern:** CLIENT consistently 660-720ms late, with slight variation (±60ms).

### Convergence Behavior

Initial pairing shows rapid convergence:
```
Cycle 1:  +4735ms (extremely late, likely initial sync artifact)
Cycle 2:  +2725ms (converging)
Cycle 3:  +725ms  (approaching steady-state)
Cycle 4+: +660ms  (stable systematic offset)
```

After ~3 cycles, phase error stabilizes around +660ms and does NOT further converge.

---

## Root Cause Hypothesis

### Where the 660ms Comes From

**CLIENT INACTIVE State Drift Correction** ([src/motor_task.c:1387-1508](src/motor_task.c))

CLIENT calculates:
```c
// Where is SERVER in its cycle right now?
uint64_t elapsed_us = sync_time_us - server_epoch_us;
uint64_t server_position_us = elapsed_us % cycle_us;  // e.g., 96ms into 2000ms cycle

// CLIENT should end INACTIVE (start ACTIVE) when SERVER reaches half_period (1000ms)
uint64_t target_wait_us;
if (server_position_us < half_period_us) {
    target_wait_us = half_period_us - server_position_us;  // e.g., 1000 - 96 = 904ms
}
```

**Example from CLIENT log:**
```
T=11031ms: CLIENT enters INACTIVE
           sync_time = 6023ms (CLIENT's synchronized clock)
           server_epoch = 5927ms (last SERVER ACTIVE start)
           elapsed = 96ms
           server_position = 96ms (SERVER is 96ms into its cycle)
           half_period = 1000ms
           target_wait = 1000 - 96 = 904ms

T=11031 + 904 = T=11935ms: CLIENT should start ACTIVE
T=12041ms: CLIENT actually starts ACTIVE ← 106ms late

NEXT CYCLE:
T=13041ms: CLIENT enters INACTIVE
           Drift correction: -105ms detected, apply -50ms correction
           target_wait = 950ms (nominal 1000ms - 50ms catch-up)

T=13041 + 950 = T=13991ms: CLIENT should start ACTIVE
T=14001ms: CLIENT actually starts ACTIVE ← 10ms late (rounding error)
```

**Observation:** Cycle-to-cycle corrections work correctly (~10ms error after correction), but overall phase remains 660ms late!

### Possible Root Causes

#### 1. Stale Epoch Data (Most Likely)

**Problem:** CLIENT may be using outdated `server_epoch_us` when calculating `server_position_us`.

**Evidence:**
- SERVER updates epoch at start of each ACTIVE cycle (every 2000ms)
- Epoch is broadcast in beacons (5-80 second intervals per Bug #36 fix)
- If CLIENT doesn't receive fresh epoch for multiple cycles, calculation uses stale reference

**Example:**
```
T=10320ms: SERVER ACTIVE starts, sets epoch = 10320000
           Beacon sent, CLIENT receives epoch update
T=12320ms: SERVER ACTIVE starts, sets epoch = 12320000
           NO beacon sent (beacon interval is 20s)
T=12041ms: CLIENT calculates using STALE epoch = 10320000
           elapsed = 12041 - 10320 = 1721ms
           server_position = 1721 % 2000 = 1721ms (WRONG!)
           Should be: (12041 - 12320) % 2000 = -279ms = 1721ms (wraps)
```

Actually that calculation shows the same result due to modulo wrap, so this isn't the issue.

#### 2. CLIENT Clock Runs Slow Relative to SERVER

**Problem:** If CLIENT's crystal is slower than SERVER's by ~33%, when CLIENT waits "1000ms" on its clock, 1660ms passes in SERVER time.

**Calculation:**
```
CLIENT wait: 1000ms (on CLIENT's clock)
SERVER time elapsed: 1660ms
Clock rate error: 66% drift (1660/1000 = 1.66)
```

**Likelihood:** EXTREMELY UNLIKELY - ESP32-C6 crystals are ±20ppm (0.002%), not 66%!

#### 3. CLIENT ACTIVE Duration Not Accounted For

**Problem:** CLIENT ACTIVE state runs for fixed 500ms (motor_on_ms + active_coast_ms). If CLIENT enters INACTIVE at T=12500ms after ending ACTIVE at T=12500ms, it calculates wait time from that point, not from when ACTIVE started.

**Analysis:**
```
T=12041ms: CLIENT ACTIVE starts
T=12541ms: CLIENT ACTIVE ends (500ms later)
T=13041ms: CLIENT INACTIVE starts (CHECK_MESSAGES overhead)

CLIENT calculates: "SERVER is now at position X, wait until position 1000ms"

But CLIENT should account for the fact that it JUST spent 500ms in ACTIVE!
```

**THIS IS LIKELY THE BUG!**

CLIENT INACTIVE state calculation assumes "I'm calculating from the moment I enter INACTIVE", but doesn't account for the fact that it's ALREADY 500ms behind where it should be due to ACTIVE duration!

#### 4. Predictive Timing Not Used

**Current approach:** CLIENT calculates "where is SERVER now, when will it reach 1000ms?"

**Better approach:** CLIENT should calculate "when did SERVER last start ACTIVE (epoch), add 1000ms, that's my absolute target time".

```c
// Current (relative calculation)
target_wait_us = half_period_us - server_position_us;  // Depends on current position

// Proposed (absolute calculation)
uint64_t server_last_active_us = server_epoch_us;
uint64_t client_target_active_us = server_last_active_us + half_period_us;
target_wait_us = client_target_active_us - sync_time_us;  // Absolute target
```

This eliminates accumulated errors from CLIENT ACTIVE duration and CHECK_MESSAGES overhead.

---

## Proposed Fix

### Option 1: Absolute Target Time Calculation

**Change:** [src/motor_task.c:1410-1443](src/motor_task.c) - Replace relative position calculation with absolute target

```c
// OLD (relative to current position)
uint64_t elapsed_us = sync_time_us - server_epoch_us;
uint64_t server_position_us = elapsed_us % cycle_us;
uint64_t target_wait_us;
if (server_position_us < half_period_us) {
    target_wait_us = half_period_us - server_position_us;
} else {
    target_wait_us = cycle_us + half_period_us - server_position_us;
}

// NEW (absolute target time)
// Calculate when SERVER last started ACTIVE (within current epoch window)
uint64_t cycles_since_epoch = (sync_time_us - server_epoch_us) / cycle_us;
uint64_t server_current_cycle_start_us = server_epoch_us + (cycles_since_epoch * cycle_us);

// CLIENT should start ACTIVE at SERVER's cycle start + half_period
uint64_t client_target_active_us = server_current_cycle_start_us + half_period_us;

// If target is in the past, advance to next cycle
if (client_target_active_us <= sync_time_us) {
    client_target_active_us += cycle_us;
}

// Calculate wait time
target_wait_us = client_target_active_us - sync_time_us;
```

**Benefits:**
- Eliminates accumulated error from ACTIVE duration and CHECK_MESSAGES overhead
- Directly targets absolute antiphase timing
- Simpler logic (no modulo position calculation)

### Option 2: Compensate for CLIENT ACTIVE Duration

**Change:** Subtract CLIENT's ACTIVE duration from calculated wait time

```c
// After calculating target_wait_us from server_position...
// Compensate for CLIENT ACTIVE duration that already occurred
uint32_t active_duration_ms = motor_on_ms + active_coast_ms;  // e.g., 500ms
if (target_wait_us > (active_duration_ms * 1000ULL)) {
    target_wait_us -= (active_duration_ms * 1000ULL);
}
```

**Benefits:**
- Minimal code change
- Accounts for time already spent in ACTIVE state

**Drawbacks:**
- Doesn't fix CHECK_MESSAGES overhead accumulation
- More complex logic (stacking corrections)

### Option 3: Measure and Log Epoch Staleness

**Before making changes, add diagnostic logging:**

```c
// In INACTIVE state, before phase calculation
uint64_t epoch_age_ms = (sync_time_us - server_epoch_us) / 1000;
if (epoch_age_ms > cycle_ms * 2) {
    ESP_LOGW(TAG, "CLIENT: Stale epoch detected (%lu ms old, >2 cycles)",
             (uint32_t)epoch_age_ms);
}
ESP_LOGI(TAG, "CLIENT: Epoch age=%lu ms, cycles=%lu",
         (uint32_t)epoch_age_ms, (uint32_t)(epoch_age_ms / cycle_ms));
```

This will reveal if epoch staleness is contributing to phase error.

---

## Test Plan

### 1. Add Diagnostic Logging

**Goal:** Confirm hypothesis before making fixes

**Changes:**
- Log epoch age in INACTIVE state
- Log calculated target_wait vs actual wait duration
- Log CLIENT ACTIVE duration for each cycle
- Compare logged values to phase error

**Expected Results:**
- If Option 1 hypothesis correct: target_wait consistently ~100ms short
- If Option 2 hypothesis correct: CLIENT ACTIVE duration not subtracted from wait
- If Option 3 hypothesis correct: epoch_age > 2 cycles (4000ms) frequently

### 2. Implement Fix (Based on Diagnostic Results)

Choose Option 1, 2, or 3 based on diagnostic evidence.

### 3. Verify Phase Error Reduction

**Test:** Run Mode 0 baseline for 90 minutes with fix applied

**Success Criteria:**
- Mean phase error < 50ms (currently 662ms)
- 95% of cycles within ±50ms (currently 0%)
- 50% of cycles within ±10ms (currently 0%)

---

## Implementation Results

### Bug #40: Absolute Target Time Calculation (IMPLEMENTED)

**Fix Applied:** Option 1 - Replace relative position calculation with absolute target time

**Implementation:** [src/motor_task.c:1410-1443](src/motor_task.c)

```c
// Calculate when SERVER last started ACTIVE (within current epoch window)
uint64_t cycles_since_epoch = (sync_time_us - server_epoch_us) / cycle_us;
uint64_t server_current_cycle_start_us = server_epoch_us + (cycles_since_epoch * cycle_us);

// CLIENT should start ACTIVE at SERVER's cycle start + half_period
uint64_t client_target_active_us = server_current_cycle_start_us + half_period_us;

// If target is in the past, advance to next cycle
if (client_target_active_us <= sync_time_us) {
    client_target_active_us += cycle_us;
}

// Calculate wait time
target_wait_us = client_target_active_us - sync_time_us;
```

**Test Results (90-minute Mode 0 baseline):**
- Mean phase error: **+662ms → +9.1ms** (98.6% improvement)
- Acceptable timing (±50ms): **0% → 74.9%**
- Excellent timing (±10ms): **0% → 18.7%**
- Standard deviation: 156.6ms (room for improvement)

**Remaining Issues:**
- Initial convergence artifacts (first 3-5 cycles show large errors)
- Periodic drift patterns around T=700-750s
- Only 18.7% achieve ±10ms target (goal: 95%)

### Bug #41: RTT-Based Outlier Rejection (IMPLEMENTED)

**Root Cause:** Analysis revealed **84% of POOR cycles (569/676) have RTT >100ms**
- Mean RTT for POOR timing: 246.5ms vs 137.8ms for GOOD timing (79% higher)
- RTT can spike to 950ms during BLE connection parameter updates
- Beacon adaptive backoff (5s→80s) means some corrections use stale data

**Implementation:** [src/motor_task.c:1543-1599](src/motor_task.c)

**Approach 1 (ACTIVE CORRECTION):** RTT-based hard thresholds
- RTT >300ms: No correction (use nominal timing)
- RTT 150-300ms: Limit correction to ±25ms
- RTT <150ms: Full correction allowed

**Approach 2 (DATA COLLECTION):** Adaptive EWMA gain
- Base alpha = 0.5 for normal RTT
- High RTT reduces alpha: `alpha = 0.5 * (200ms / RTT)`
- Floor at alpha = 0.1 (10% trust minimum)
- Logged side-by-side with clamping for comparison

**Design Rationale:**
- Start with simple proven approach (hard thresholds, 84% correlation)
- Collect evidence for whether adaptive gain would improve results
- Both use same max_correction ceiling for fair comparison

**Test Status:** Hardware testing pending

**Expected Outcome:**
- Reject corrections when beacon data is stale (RTT >300ms)
- Target: **95% of cycles within ±10ms** (currently 18.7%)

### Enhanced Analysis Tools

**[scripts/analyze_bilateral_phase_detailed.py](scripts/analyze_bilateral_phase_detailed.py):**
- Extracts RSSI, RTT, Quality from beacon processing logs
- Carries forward last known metrics to all motor activations
- Correlates phase errors with BLE link quality
- Identifies outlier patterns

**Key Discovery:**
```
GOOD timing (±10ms): RTT mean=137.8ms, min=90.9ms, max=950.0ms
POOR timing (>50ms): RTT mean=246.5ms, min=71.5ms, max=950.0ms

High RTT (>100ms) cycles: 569/676 (84%) of POOR cycles
```

---

## Files for Investigation

1. **[src/motor_task.c:1387-1508](src/motor_task.c)** - CLIENT INACTIVE drift correction logic
2. **[src/time_sync.c](src/time_sync.c)** - Epoch management and clock synchronization
3. **[scripts/analyze_bilateral_phase.py](scripts/analyze_bilateral_phase.py)** - Corrected analysis tool

---

## Key Learnings

1. **Don't trust first analysis** - The "double activation" finding was a measurement artifact
2. **Log everything during development** - Diagnostic logging revealed the true timing pattern
3. **Verify assumptions** - "CLIENT is double-activating" vs "CLIENT is consistently late"
4. **Use absolute timing** - Relative calculations accumulate errors, absolute targets don't
5. **Test in isolation first** - Mode 0 baseline (no mode changes) isolated the core algorithm bug

---

## Next Actions

1. ✅ Create corrected analysis script (DONE)
2. ✅ Identify systematic phase offset (DONE - +662ms mean error)
3. ✅ Develop root cause hypotheses (DONE - 3 options)
4. ✅ Add diagnostic logging to confirm hypothesis (DONE)
5. ✅ Implement Bug #40 fix - Absolute target time calculation (DONE - 98.6% improvement)
6. ✅ Test Bug #40 fix with 90-minute Mode 0 baseline (DONE - mean error +662ms → +9.1ms)
7. ✅ Enhanced analysis: RTT/RSSI/Quality correlation (DONE - 84% of POOR cycles have RTT >100ms)
8. ✅ Implement Bug #41 - RTT-based outlier rejection + adaptive EWMA comparison (DONE)
9. 🔲 Test Bug #41 with 90-minute Mode 0 baseline (hardware testing pending)
10. 🔲 Compare RTT clamping vs adaptive EWMA logs
11. 🔲 Evaluate if 95% ±10ms target achieved
12. 🔲 Test fix with multi-mode session (mode changes)

---

**Generated:** 2025-12-01
**Analysis Duration:** ~3 hours
**Status:** Bug #40 fixed (98.6% improvement), Bug #41 implemented (RTT-based outlier rejection), hardware testing pending
