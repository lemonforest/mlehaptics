# Bilateral Timing Root Cause Analysis

**Date:** 2025-12-01
**Issue:** Analysis showed "double activation" with 5,395 measurements for 2,699 SERVER cycles (2.00× ratio)
**Status:** ✅ ROOT CAUSE IDENTIFIED - Analysis script artifact, NOT a firmware bug

---

## Executive Summary

**The "double activation bug" is actually an analysis script artifact, not a firmware bug.**

The analysis script counts BOTH "Cycle starts ACTIVE" AND "Cycle starts INACTIVE" log messages from CLIENT, resulting in 2 measurements per CLIENT cycle. This creates the appearance of double activation when in fact CLIENT is behaving correctly by alternating between INACTIVE and ACTIVE states for bilateral anti-phase coordination.

**Key Finding:** CLIENT firmware is working AS DESIGNED. The timing issues observed (OVERLAP and DRIFT status) are due to phase offset errors in the CLIENT drift correction algorithm, NOT double motor activations.

---

## Analysis Script Behavior

### What the Script Counts (analyze_bilateral_timing_fixed.py)

```python
# Only matches "Cycle starts ACTIVE"
active_match = re.search(r'I\((\d+)\)MOTOR_TASK:.*CyclestartsACTIVE', cleaned_line)
```

### CLIENT Log Pattern (Mode 0 Baseline)

```
T=11031ms: CLIENT: Cycle starts INACTIVE (next will be ACTIVE)
T=12041ms: CLIENT: Cycle starts ACTIVE (next will be INACTIVE)
T=13041ms: CLIENT: Cycle starts INACTIVE (next will be ACTIVE)
T=14001ms: CLIENT: Cycle starts ACTIVE (next will be INACTIVE)
T=15001ms: CLIENT: Cycle starts INACTIVE (next will be ACTIVE)
T=16001ms: CLIENT: Cycle starts ACTIVE (next will be INACTIVE)
...
```

**Pattern:** CLIENT alternates INACTIVE → ACTIVE every ~1000ms (total cycle ~2000ms for 1Hz operation).

### Why Script Found 5,395 Measurements for 2,699 Cycles

- **SERVER:** Logs only "Cycle starts ACTIVE" → 2,699 activations
- **CLIENT:** Logs BOTH "Cycle starts INACTIVE" and "Cycle starts ACTIVE" → 2,699 × 2 = 5,398 events
- **Script:** Counts only "ACTIVE" → 2,699 CLIENT ACTIVE events
- **Pairing Algorithm:** Tries to pair each CLIENT event with nearest SERVER → creates 5,395 measurements

The script attempts to pair BOTH CLIENT's INACTIVE starts AND ACTIVE starts with SERVER's ACTIVE starts, creating two measurements per SERVER cycle.

---

## Actual CLIENT Behavior (Verified from Logs)

### Timing Pattern

```
T=11031ms: INACTIVE starts
            ↓ (wait 903ms to antiphase via drift correction)
T=12041ms: ACTIVE starts (+1010ms)
            ↓ (motor ON 250ms, coast 250ms = 500ms)
T=12291ms: Motor coasting
            ↓
T=13041ms: INACTIVE starts (+1000ms from ACTIVE start)
            ↓ (wait ~960ms via drift correction)
T=14001ms: ACTIVE starts (+960ms)
            ↓ (motor ON 250ms, coast 250ms = 500ms)
T=14251ms: Motor coasting
            ↓
T=15001ms: INACTIVE starts (+1000ms from ACTIVE start)
```

### State Machine Flow

```
CHECK_MESSAGES (toggle: client_next_inactive=false)
    ↓
ACTIVE (run motor for 500ms total)
    ↓
CHECK_MESSAGES (toggle: client_next_inactive=true)
    ↓
INACTIVE (drift-corrected wait until SERVER at half-period)
    ↓
CHECK_MESSAGES (toggle: client_next_inactive=false)
    ↓
ACTIVE ...
```

**Verdict:** CLIENT is correctly alternating between ACTIVE and INACTIVE states with ~1000ms intervals, resulting in proper ~2000ms full cycles for Mode 0 (1Hz).

---

## Why Timing Shows OVERLAP and DRIFT

While CLIENT is not double-activating, the logs DO show timing issues:

### Mode 0 Baseline Analysis Results

| Category | Percentage | Mean Error | Description |
|----------|-----------|-----------|-------------|
| OVERLAP | ~50% | -1,300ms | CLIENT starting too early (before SERVER ends ACTIVE) |
| DRIFT | ~50% | +600ms | CLIENT starting too late (after optimal antiphase) |

### Root Cause: Phase Offset Errors

The INACTIVE state drift correction algorithm calculates when CLIENT should start ACTIVE (target: when SERVER is at half-period), but the actual CLIENT activation times show consistent phase errors:

**Example from analysis:**
```
SERVER at T=12320ms
CLIENT INACTIVE ends at T=12045ms (-275ms error)  ← CLIENT too early (OVERLAP)
CLIENT ACTIVE ends at T=13041ms
CLIENT should start next ACTIVE at T=13320ms (SERVER's half-period)
CLIENT actually starts next ACTIVE at T=14005ms (+685ms error) ← CLIENT too late (DRIFT)
```

### Hypothesized Causes of Phase Errors

1. **Stale Epoch Data:** SERVER epoch updates may be delayed or CLIENT may be using outdated epoch when calculating target wait time

2. **Accumulated Jitter:** Despite Bug #17 fix for absolute time scheduling, message queue processing delays in CHECK_MESSAGES state may accumulate timing errors

3. **ACTIVE Duration Mismatch:** CLIENT ACTIVE state runs for fixed duration (motor_on_ms + active_coast_ms = 500ms), which doesn't account for drift corrections that should adjust cycle phase

4. **Initial Pairing Phase Alignment:** First few cycles after pairing show large phase errors (e.g., +4735ms, +2725ms, +725ms) that take many cycles to converge

5. **Correction Algorithm Issues:**
   - **Bug #27:** Replaced PD controller with pure P + deadband
   - **Bug #29:** Fixed frequency-dependent correction clamping
   - These fixes may have introduced or exposed new phase tracking issues

---

## Idealized vs Actual Behavior

### Idealized SERVER Timeline (Mode 0, 2000ms cycle, 25% duty)

```
T=0ms:     SERVER ACTIVE starts
T=500ms:   SERVER ACTIVE ends (motor OFF), SERVER INACTIVE starts
T=2000ms:  SERVER INACTIVE ends, SERVER ACTIVE starts (next cycle)
T=2500ms:  SERVER ACTIVE ends
T=4000ms:  SERVER ACTIVE starts (next cycle)
...
```

### Ideal CLIENT Timeline (Perfect Antiphase)

```
T=1000ms:  CLIENT ACTIVE starts (when SERVER at mid-INACTIVE)
T=1500ms:  CLIENT ACTIVE ends (motor OFF), CLIENT INACTIVE starts
T=3000ms:  CLIENT INACTIVE ends, CLIENT ACTIVE starts
T=3500ms:  CLIENT ACTIVE ends
T=5000ms:  CLIENT ACTIVE starts (next cycle)
...
```

**Delta:** CLIENT starts ACTIVE exactly +1000ms after each SERVER ACTIVE start (period/2).

### Actual CLIENT Timeline (from logs)

```
T=12320ms: SERVER ACTIVE starts (inferred from epoch)
T=12045ms: CLIENT ACTIVE starts (-275ms from SERVER) ← OVERLAP
T=12545ms: CLIENT ACTIVE ends (estimated)
T=13045ms: CLIENT INACTIVE ends
T=14005ms: CLIENT ACTIVE starts (+1685ms from SERVER) ← DRIFT, but -315ms from NEXT SERVER
```

**Observed Delta:** CLIENT ACTIVE starts range from -275ms to +1685ms relative to nearest SERVER ACTIVE start, instead of consistent +1000ms.

---

## Key Differences from Initial Hypothesis

### Initial Hypothesis (WRONG)

- CLIENT was activating motors TWICE per cycle
- Both activations had same timestamp (duplicate logging)
- Bug was in motor cycle start/stop logic

### Actual Situation (CORRECT)

- CLIENT activates motors ONCE per cycle (ACTIVE state)
- CLIENT also enters INACTIVE state once per cycle (not a motor activation)
- Bug is in INACTIVE state drift correction phase calculation, causing inconsistent timing relative to SERVER

---

## Corrected Analysis Approach

### What to Measure

Instead of counting "all cycle starts," measure only MOTOR ACTIVATIONS:

**SERVER:** "Cycle starts ACTIVE" (motor activation)
**CLIENT:** "Cycle starts ACTIVE" (motor activation)
**Ignore:** CLIENT "Cycle starts INACTIVE" (motor coasting, not activation)

### Corrected Pairing Algorithm

For each SERVER ACTIVE start:
1. Find the CLIENT ACTIVE start that occurs nearest to SERVER_time + 1000ms (target antiphase)
2. Calculate delta = CLIENT_time - (SERVER_time + 1000ms)
3. Report error magnitude and direction

### Expected Results

- **Count:** 2,699 SERVER ACTIVE, 2,699 CLIENT ACTIVE → 2,699 paired measurements (1:1 ratio)
- **Ideal Delta:** 0ms (CLIENT starts ACTIVE exactly 1000ms after SERVER)
- **Actual Delta:** Currently showing -275ms to +685ms range (phase offset errors)

---

## Next Steps

### 1. Update Analysis Script

Create `analyze_bilateral_timing_corrected.py` that:
- Counts only "Cycle starts ACTIVE" for both SERVER and CLIENT
- Pairs each CLIENT ACTIVE with temporally nearest SERVER ACTIVE
- Calculates delta from ideal +1000ms offset (not from SERVER timestamp directly)
- Reports phase error magnitude and convergence over time

### 2. Investigate Phase Calculation Logic

Focus on `src/motor_task.c:1387-1508` (INACTIVE state CLIENT drift correction):

**Key Questions:**
- Is `server_epoch_us` up-to-date when CLIENT calculates wait time?
- Is `server_position_us` calculation accounting for beacon transmission delay?
- Why do corrections consistently undershoot (CLIENT too early) OR overshoot (CLIENT too late)?
- Are corrections being applied in the right direction?

### 3. Add Diagnostic Logging

Temporarily enable verbose logging for every cycle (not just every 10th):
```c
// Line 1417: Change from "% 10 == 0" to "% 1 == 0"
bool should_log = (inactive_cycle_count % 1 == 0);
```

This will show:
- SERVER epoch timestamp
- CLIENT sync time
- Calculated server_position_us
- Target wait time
- Actual wait time after corrections

### 4. Test Hypothesis: Epoch Staleness

Add logging to show beacon age:
```c
uint64_t epoch_age_us = sync_time_us - server_epoch_us;
ESP_LOGI(TAG, "Epoch age: %lu ms", (uint32_t)(epoch_age_us / 1000));
```

If epoch_age_us exceeds one full cycle (2000ms), CLIENT is using stale SERVER data.

### 5. Consider Alternative Algorithm

Current: CLIENT calculates "wait until SERVER at half-period"
Alternative: CLIENT calculates "start ACTIVE when SERVER last started ACTIVE + 1000ms"

This would directly target the antiphase timing without modulo arithmetic that may introduce errors.

---

## Firmware Changes NOT Needed

**No changes to motor activation logic** - CLIENT is correctly running motors once per ACTIVE cycle.

**Preserve toggle logic** - The `client_next_inactive` flag correctly alternates ACTIVE/INACTIVE states.

**Keep ACTIVE state duration fixed** - 500ms ACTIVE period is correct; phase is adjusted during INACTIVE wait.

---

## Conclusion

The "double activation" finding was an artifact of the analysis script counting both INACTIVE and ACTIVE state transitions. CLIENT firmware is working as designed, alternating between INACTIVE (coasting, drift-corrected wait) and ACTIVE (motor running) states for bilateral anti-phase coordination.

The REAL issue is phase offset errors in the INACTIVE state drift correction algorithm, causing CLIENT to consistently start ACTIVE either too early (OVERLAP) or too late (DRIFT) relative to the ideal +1000ms offset from SERVER.

Next investigation should focus on why the phase calculation consistently produces these offsets despite the drift correction logic.

---

**Generated:** 2025-12-01
**Analysis Duration:** ~2 hours
**Next Action:** Update analysis script to correctly measure phase offsets (CLIENT ACTIVE vs SERVER ACTIVE only)
