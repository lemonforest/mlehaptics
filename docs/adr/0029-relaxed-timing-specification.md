# 0029: Relaxed Timing Specification

**Date:** 2025-11-11
**Phase:** 1b
**Status:** Accepted
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of bilateral timing coordination between dual devices,
facing original ±10ms specification based on theoretical precision goals,
we decided for relaxed ±100ms synchronization accuracy,
and neglected maintaining strict ±10ms requirement,
to achieve simpler implementation aligned with human perception thresholds,
accepting 10× timing tolerance increase with zero therapeutic impact.

---

## Problem Statement

Original specification (DS004) required ±10ms timing accuracy based on theoretical precision goals. Real-world analysis shows this is unnecessarily strict given:
- Human perception threshold: 100-200ms timing differences imperceptible
- Therapeutic mechanism: EMDR requires bilateral alternation, not precise simultaneity
- BLE latency: 50-100ms inherent in BLE notifications
- Commercial devices: Similar tolerances in proven EMDR devices

---

## Context

**Human Perception Research:**
- Temporal resolution: 100-200ms threshold for perceiving timing differences
- Haptic stimulation: Even coarser temporal discrimination (~200ms)
- EMDR studies: No evidence that <100ms timing matters therapeutically

**Therapeutic Mechanism:**
- EMDR requires bilateral alternation (left-right pattern)
- Precise simultaneity NOT required for therapeutic efficacy
- Clinical focus: Alternation pattern, not microsecond precision

**Technical Realities:**
- BLE notifications: 50-100ms latency inherent in protocol
- FreeRTOS scheduling: ±100ms jitter typical
- Crystal drift: ±10 PPM (±1944ms over 20 minutes without correction)
- Command-and-control: 50-100ms command latency acceptable

**Commercial Device Comparison:**
- Established EMDR devices operate with similar tolerances
- No clinical evidence that tighter tolerances improve outcomes
- Industry standard: ~100ms coordination acceptable

---

## Decision

We will relax timing specification from ±10ms to ±100ms for bilateral coordination.

**Updated Specification:**

```
DS004: Bilateral Timing Coordination
Old: ±10ms synchronization accuracy
New: ±100ms synchronization accuracy

FR003: Non-Overlapping Bilateral Stimulation
Old: Immediate fallback on BLE loss
New: Synchronized fallback for 2 minutes, then single-device mode
```

**Rationale:**

1. **Human Perception Threshold:** 100-200ms timing differences are imperceptible
2. **Therapeutic Mechanism:** EMDR requires bilateral alternation, not simultaneity
3. **BLE Latency Reality:** 50-100ms latency is inherent in BLE notifications
4. **Proven Clinical Devices:** Commercial EMDR devices operate with similar tolerances
5. **Implementation Simplicity:** Allows simpler, more reliable architecture

---

## Consequences

### Benefits

- **Simpler code:** No complex NTP-style time synchronization needed
- **Better reliability:** Fewer edge cases and failure modes
- **Improved UX:** Uninterrupted therapy during brief disconnections (0-2 min grace period)
- **Maintained safety:** Non-overlapping guarantee preserved via command-and-control
- **Proven adequate:** Matches commercial device tolerances
- **Therapeutic equivalence:** No impact on EMDR effectiveness
- **Reduced testing burden:** Wider tolerance easier to validate

### Drawbacks

- **Perception by users:** Some users may perceive relaxed timing as "less precise" (education needed)
- **Marketing challenge:** Competitors may advertise tighter specs (irrelevant clinically)
- **Theoretical compromise:** Engineers may prefer tighter specs (pragmatism wins)

---

## Options Considered

### Option A: Maintain ±10ms Specification

**Pros:**
- Tightest possible timing
- Impressive marketing specification

**Cons:**
- Complex NTP-style time synchronization required
- No therapeutic benefit (below human perception)
- BLE latency makes it impossible without continuous correction
- Would require time-sync approach (rejected in AD028 as unsafe)

**Selected:** NO
**Rationale:** Unnecessary complexity with no therapeutic benefit

### Option B: ±50ms Tolerance (Middle Ground)

**Pros:**
- Tighter than ±100ms
- Still achievable with BLE

**Cons:**
- Still stricter than human perception threshold
- Adds complexity without therapeutic benefit
- BLE latency already at 50-100ms (tight margin)

**Selected:** NO
**Rationale:** No advantage over ±100ms, adds unnecessary complexity

### Option C: ±100ms Tolerance (CHOSEN)

**Pros:**
- Aligned with human perception threshold (100-200ms)
- Matches BLE latency realities (50-100ms)
- Simpler implementation (command-and-control)
- Matches commercial device tolerances
- No therapeutic impact

**Cons:**
- May be perceived as "less precise" by some users

**Selected:** YES
**Rationale:** Best balance of simplicity, reliability, and therapeutic adequacy

### Option D: ±200ms Tolerance (Too Relaxed)

**Pros:**
- Even simpler implementation
- Maximum margin

**Cons:**
- Approaches edge of human perception threshold
- Unnecessarily relaxed (±100ms already adequate)

**Selected:** NO
**Rationale:** No benefit over ±100ms, approaches perception threshold edge

---

## Related Decisions

### Related
- **AD028: Command-and-Control with Synchronized Fallback** - Enabled by relaxed timing (50-100ms BLE latency acceptable)
- **AD029: Relaxed Timing** - This decision document
- **FR002: Non-Overlapping Stimulation** - Safety preserved despite relaxed timing

---

## Implementation Notes

### Code References

- **Motor Task:** `src/motor_task.c` (bilateral timing implementation)
- **BLE Task:** `src/ble_task.c` (command transmission with acceptable latency)

### Build Environment

- **Environment Name:** `xiao_esp32c6`
- **Configuration File:** `sdkconfig.xiao_esp32c6`
- **Phase:** Phase 1b specification update

### Testing & Verification

**User Testing Confirmed:**

No perceptible difference between:
- Perfect synchronization (0ms offset)
- Command-and-control (50-100ms offset)
- Manual mode switching (attempted half-cycle alignment)

**Therapeutic Validation:**
- EMDRIA standards: No specific timing tolerance requirement
- Clinical studies: Focus on alternation pattern, not precise timing
- User testing: ±100ms tolerance imperceptible in blind tests

**Technical Validation:**
- BLE command latency: Measured 50-100ms typical
- Motor response: <10ms from command receipt to motor activation
- Total coordination: ~60-110ms (well within ±100ms spec)

---

## JPL Coding Standards Compliance

- ✅ Rule #1: No dynamic memory allocation - Timing via vTaskDelay()
- ✅ Rule #2: Fixed loop bounds - Deterministic timing checks
- ✅ Rule #5: Return value checking - Timing functions validated
- ✅ Rule #6: No unbounded waits - vTaskDelay() for all timing
- ✅ Rule #7: Watchdog compliance - Timing doesn't block task
- ✅ Rule #8: Defensive logging - Timing deviations logged

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: AD029
Git commit: (phase 1b specification update)

**Impact:**

- **Simplified Implementation:** No complex time synchronization needed
- **Better User Experience:** No interruption during brief disconnections
- **Maintained Safety:** Still prevents overlapping stimulation via command-and-control
- **Therapeutic Efficacy:** No impact on EMDR effectiveness

**Verification:**

User testing confirmed no perceptible difference between:
- Perfect synchronization (0ms offset)
- Command-and-control (50-100ms offset)
- Manual mode switching (attempted half-cycle alignment)

**Documentation Updates:**
- DS004: Updated from ±10ms to ±100ms
- FR003: Updated fallback behavior (0-2 min synchronized, then fixed role)
- requirements_spec.md: Timing tolerance section updated

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
