# Phase 6: ACTIVE Coast Adjustment Plan

**Status:** IMPLEMENTED (Phase 6j - November 26, 2025)
**Date:** 2025-11-26
**Problem:** Current INACTIVE-based corrections have limited headroom at high motor duty
**Solution:** Asymmetric correction - catch-up in ACTIVE coast, slow-down in INACTIVE

> **Implementation Complete:** Phase 6j implemented on November 26, 2025.
> - Catch-up (negative drift): Shortens ACTIVE coast period
> - Slow-down (positive drift): Extends INACTIVE period (unchanged)
> - PD damping applied to both correction types
> - Headroom at high duty cycles vastly improved

---

## Current Approach (INACTIVE Adjustment)

```
Timeline at 1Hz (1000ms period, 500ms half-period):

SERVER: |===== ACTIVE =====|----- INACTIVE -----|===== ACTIVE =====|
        0                 500                  1000               1500

CLIENT: |----- INACTIVE ----|===== ACTIVE =====|----- INACTIVE ----|
        0                  500                 1000               1500
                            ↑
                    Correction applied here
                    (adjust INACTIVE duration)
```

**The Problem:**
- To catch up: CLIENT shortens INACTIVE (starts ACTIVE earlier)
- Floor constraint: Can't start ACTIVE while SERVER is still in ACTIVE
- Floor = motor_on + coast ≈ 250-450ms at high duty
- At high duty: floor ≈ INACTIVE → **near-zero headroom**

---

## Proposed Approach (ACTIVE Coast Adjustment)

**Key Insight:** Corrections should happen at END of ACTIVE, not START of ACTIVE.

```
Catch-up scenario (CLIENT is behind):

Current (risky):
  CLIENT shortens INACTIVE → starts ACTIVE earlier → might overlap SERVER's ACTIVE

Proposed (safe):
  CLIENT shortens ACTIVE coast → ends ACTIVE earlier → enters INACTIVE sooner
  → next cycle starts sooner → caught up!

  No risk of overlap: we're ending our turn early, not starting early.
```

### Asymmetric Correction Strategy

| Scenario | Correction | Where Applied | Risk | Headroom |
|----------|------------|---------------|------|----------|
| CLIENT behind (catch up) | Negative | Shorten ACTIVE coast | None (ending early) | ~400ms |
| CLIENT ahead (slow down) | Positive | Lengthen INACTIVE | None (waiting longer) | Unlimited |

**Why asymmetric?**
- Shortening ACTIVE = ending our motor early = safe
- Lengthening ACTIVE = running motor longer = risks overlap with SERVER's next ACTIVE
- Shortening INACTIVE = starting motor early = risks overlap with SERVER's ACTIVE (current floor problem)
- Lengthening INACTIVE = waiting longer before motor = safe

---

## Timing Structure (Clarified Terminology)

```
One full period (e.g., 1000ms at 1Hz):
├── ACTIVE (this device's half-period, ~500ms)
│   ├── MOTOR_DRIVE: PWM driving motor (motor_on_ms)
│   ├── COAST: Motor freewheeling (coast_ms) ← CATCH-UP ADJUSTMENT HERE
│   └── BEMF_SAMPLE: Optional back-EMF reading
│
└── INACTIVE (other device's half-period, ~500ms) ← SLOW-DOWN ADJUSTMENT HERE
    └── Motor completely off (sacred promise)
```

### Motor Duty Percentage

| Motor Duty | MOTOR_DRIVE | COAST | Total ACTIVE | INACTIVE |
|------------|-------------|-------|--------------|----------|
| 50% | 250ms | 0ms | 250ms | 500ms + 250ms gap |
| 75% | 375ms | 0ms | 375ms | 500ms + 125ms gap |
| 90% | 450ms | 0ms | 450ms | 500ms + 50ms gap |
| 100% | 500ms | 0ms | 500ms | 500ms (seamless) |

Wait, this doesn't match our current structure. Let me reconsider...

**Current structure (I think):**
- ACTIVE phase = motor_on + coast + BEMF, duration determined by duty%
- INACTIVE phase = remaining time in half-period
- At 100% duty: ACTIVE fills entire half-period, INACTIVE = other device's half-period

**Clarified structure:**
```
At 1Hz, 100% motor duty:
  Half-period = 500ms

  ACTIVE = 500ms (motor driving, possibly with small coast for BEMF)
  INACTIVE = 500ms (motor off, other device's turn)

  Total cycle = 1000ms
```

---

## State Machine Changes

### Current States
```
CHECK_MESSAGES → FORWARD_ACTIVE → BEMF → COAST_SETTLE → INACTIVE → back to CHECK
                       ↓                                    ↓
                  (motor on)                        (correction here)
```

### Proposed States
```
CHECK_MESSAGES → MOTOR_DRIVE → COAST_ADJUST → INACTIVE → back to CHECK
                      ↓              ↓             ↓
                 (motor on)   (catch-up adj)  (slow-down adj)
```

**Changes:**
1. `COAST_ADJUST` state: Variable duration based on catch-up correction
2. `INACTIVE` state: Variable duration based on slow-down correction (or fixed at half-period)
3. Correction logic split between two states based on sign

### Pseudocode

```c
// In MOTOR_DRIVE state (end of motor_on period):
// Calculate where we should be vs where we are
int32_t drift_ms = calculate_drift_from_server_epoch();

if (drift_ms < 0) {
    // CLIENT is behind, need to catch up
    // Shorten ACTIVE coast to end cycle sooner
    int32_t catch_up_ms = -drift_ms;  // positive value

    // Clamp to available coast time
    int32_t max_coast_reduction = coast_ms - MIN_COAST_MS;  // e.g., 50ms minimum
    if (catch_up_ms > max_coast_reduction) {
        // Need more than coast allows - borrow from motor_on next cycle?
        // Or request duty reduction from SERVER?
        catch_up_ms = max_coast_reduction;
        // Flag: correction_limited = true
    }

    actual_coast_ms = coast_ms - catch_up_ms;
    inactive_ms = HALF_PERIOD_MS;  // Fixed, keep the promise

} else if (drift_ms > 0) {
    // CLIENT is ahead, need to slow down
    // Lengthen INACTIVE to delay next cycle
    actual_coast_ms = coast_ms;  // Nominal
    inactive_ms = HALF_PERIOD_MS + drift_ms;  // Extended wait

} else {
    // Perfectly aligned
    actual_coast_ms = coast_ms;
    inactive_ms = HALF_PERIOD_MS;
}

// Transition to COAST_ADJUST state, wait actual_coast_ms
// Then transition to INACTIVE state, wait inactive_ms
```

---

## Headroom Analysis

### Current Approach (INACTIVE Adjustment)

At 2Hz (250ms half-period), 90% motor duty:
- ACTIVE = 225ms (motor_on=200ms, coast=25ms)
- INACTIVE = 250ms
- Floor = motor_on + coast = 225ms
- **Catch-up headroom = 250ms - 225ms = 25ms** ← Very limited!

### Proposed Approach (ACTIVE Coast Adjustment)

Same scenario:
- ACTIVE = 225ms (motor_on=200ms, coast=25ms)
- MIN_COAST = 10ms (for BEMF if needed)
- **Catch-up headroom from coast = 25ms - 10ms = 15ms**

That's still limited! But we can also borrow from motor_on:
- MIN_MOTOR_ON = 50ms (motor startup minimum)
- **Additional headroom from motor_on = 200ms - 50ms = 150ms**
- **Total catch-up headroom = 15ms + 150ms = 165ms** ← Much better!

### The 100% Motor Duty Case

At 100% duty, coast_ms = 0. All headroom comes from motor_on:
- motor_on = 250ms (entire half-period at 2Hz)
- MIN_MOTOR_ON = 50ms
- **Catch-up headroom = 250ms - 50ms = 200ms**

This is 8× better than current approach at high duty!

---

## Do We Need CLIENT → SERVER Feedback?

### When Would CLIENT Be Unable to Keep Up?

With ACTIVE adjustment headroom of ~200ms at 2Hz:
- Normal drift: ~30μs per 90 minutes (measured)
- Maximum correction per cycle: 200ms
- CLIENT would need drift > 200ms per cycle to be unable to keep up
- That's 80% phase error per cycle = catastrophic clock failure

**Conclusion:** Under normal operation, CLIENT should ALWAYS be able to keep up.

### Edge Cases Where Feedback Might Help

1. **Repeated motor_on borrowing**: If CLIENT consistently borrows from motor_on (reducing therapeutic intensity), it could notify SERVER.

2. **Hardware degradation**: If Bluetooth interference or clock issues cause sustained drift, feedback could trigger investigation.

3. **User preference**: Some users might prefer "perfect sync" over "consistent motor intensity" - feedback enables this choice.

### Proposed Feedback (Optional Enhancement)

```c
// If CLIENT borrows from motor_on more than 3 consecutive cycles:
coordination_message_t feedback = {
    .type = SYNC_MSG_DUTY_REDUCTION_REQUEST,
    .payload.duty_reduction_pct = 5  // Request 5% reduction
};
ble_send_coordination_message(&feedback);

// SERVER receives and both devices reduce duty
// Creates more coast headroom for corrections
// Can be restored after sync stabilizes
```

**Recommendation:** Implement feedback as Phase 6b enhancement, not required for initial refactor.

---

## Implementation Plan

### Phase 6a: ACTIVE Coast Adjustment (Core Refactor)

1. **Modify motor_task.c state machine:**
   - Add `COAST_ADJUST` state (or rename existing `COAST_SETTLE`)
   - Move catch-up correction from INACTIVE to COAST_ADJUST
   - Keep slow-down correction in INACTIVE

2. **Update drift calculation:**
   - Calculate at end of MOTOR_DRIVE (before coast)
   - Determine correction sign and magnitude
   - Route to appropriate adjustment (coast vs inactive)

3. **Add motor_on borrowing:**
   - If coast headroom insufficient, borrow from motor_on
   - Track borrowed amount for logging/diagnostics
   - Clamp to MIN_MOTOR_ON (50ms suggested)

4. **Update logging:**
   - Log correction type (coast vs inactive vs motor_on borrow)
   - Track headroom usage for tuning

### Phase 6b: CLIENT Feedback (Optional Enhancement)

1. **Add SYNC_MSG_DUTY_REDUCTION_REQUEST message type**
2. **CLIENT tracks consecutive motor_on borrows**
3. **SERVER handles duty reduction request**
4. **Both devices coordinate duty change**
5. **Auto-restore duty after sync stabilizes**

---

## Testing Strategy

### Unit Tests (If Applicable)
- Drift calculation with known inputs
- Correction routing (coast vs inactive)
- Motor_on borrowing threshold

### Hardware Tests

1. **Basic antiphase at various duty cycles:**
   - 50%, 75%, 90%, 100% motor duty
   - 0.5Hz, 1Hz, 2Hz frequencies
   - Verify no perceptible gap/overlap

2. **Correction responsiveness:**
   - Introduce artificial drift (delay one device's boot)
   - Measure cycles to achieve antiphase
   - Target: < 3 cycles (was 10+ cycles)

3. **Motor_on borrowing perception:**
   - At 100% duty, cause correction requiring motor_on borrow
   - User perception test: is 450ms vs 500ms motor_on noticeable?

4. **Long-duration stability:**
   - 20-minute session at high duty
   - Monitor for accumulated drift
   - Verify no sync degradation

---

## Open Questions

1. **MIN_MOTOR_ON value:** 50ms suggested. Too conservative? Motor startup time is ~10-20ms.

2. **MIN_COAST value:** 10ms suggested for BEMF. Can we go to 0ms if BEMF not needed?

3. **INACTIVE adjustment limit:** Should we cap slow-down correction to prevent one device waiting too long?

4. **PD controller integration:** Does the damped correction approach still apply, or does asymmetric adjustment change things?

5. **SERVER behavior:** Should SERVER ever adjust, or always be the reference? (Current: SERVER is reference.)

---

## Summary

| Aspect | Current | Proposed |
|--------|---------|----------|
| Catch-up correction | Shorten INACTIVE | Shorten ACTIVE coast |
| Slow-down correction | Lengthen INACTIVE | Lengthen INACTIVE (same) |
| Floor constraint | motor_on + coast (~250ms) | MIN_MOTOR_ON (~50ms) |
| Headroom at 90% duty, 2Hz | ~25ms | ~165ms |
| Headroom at 100% duty | ~0ms (broken) | ~200ms (works!) |
| CLIENT feedback needed | N/A | Optional enhancement |
| Complexity | Medium | Medium (different, not harder) |

**Bottom Line:** This refactor should eliminate the sync problems at high duty cycles while maintaining clinical compatibility with existing EMDR devices that expect seamless L↔R alternation.
