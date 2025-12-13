# 0029: Bilateral Timing Specification

**Date:** 2025-11-11
**Updated:** 2025-12-11
**Phase:** 1b → Phase 6 (tightened after time sync proven)
**Status:** Superseded (see AD043, AD045)
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of bilateral timing coordination between dual devices,
facing original ±10ms specification and later relaxed ±100ms target,
we decided for **±15ms synchronization accuracy** (with ±5ms stretch goal),
achieving tighter precision than human perception requires,
accepting modest implementation complexity for improved bilateral coordination,
**superseding the ±100ms relaxation** now that Phase 2 time sync is proven.

> **UPDATE December 2025:** Original ±100ms relaxation was based on pre-time-sync
> assumptions. Phase 2 testing proved ±30μs clock drift over 90 minutes. AD043
> targets <5ms mean error with EMA filter. This ADR is tightened accordingly.

---

## Problem Statement

**Original History:**
- DS004 originally required ±10ms timing accuracy (theoretical precision goal)
- AD029 (November 2025) relaxed this to ±100ms citing BLE latency and human perception
- Phase 2 time sync (November 2025) proved ±30μs clock drift is achievable
- This revision tightens to ±15ms based on proven capabilities

**Current Problem:**
While ±100ms was therapeutically adequate, we now have the capability to do much better.
The ±40ms phase offsets observed in testing are technically within spec, but we can achieve
tighter coordination. AD043 targets <5ms mean error with EMA filtering.

---

## Context

**Human Perception Research (Unchanged):**
- Temporal resolution: 100-200ms threshold for perceiving timing differences
- Haptic stimulation: Even coarser temporal discrimination (~200ms)
- EMDR studies: No evidence that <100ms timing matters therapeutically

**Therapeutic Mechanism (Unchanged):**
- EMDR requires bilateral alternation (left-right pattern)
- Precise simultaneity NOT required for therapeutic efficacy
- Clinical focus: Alternation pattern, not microsecond precision

**Technical Capabilities (Updated December 2025):**
- Phase 2 time sync: ±30μs clock drift proven over 90 minutes
- EMA filter (AD043): <5ms mean error target with paired timestamps
- Pattern-broadcast (AD045): Independent execution eliminates per-cycle corrections
- BLE beacon latency: 10-50ms jitter, smoothed by EMA filter
- Crystal drift: ±10 PPM, corrected by continuous beacon exchange

**Why Tighten Beyond Therapeutic Requirement:**
- We have the capability to do better, so we should
- Tighter spec validates the investment in Phase 2/3 time sync
- Provides headroom for future applications (research, accessibility)
- Demonstrates technical excellence in open-source project

---

## Decision

**December 2025 Revision:** Tighten timing specification from ±100ms to **±15ms** for bilateral coordination.

**Updated Specification:**

```
DS004: Bilateral Timing Coordination
Original (2025-11):     ±10ms (theoretical)
Relaxed (AD029 v1):     ±100ms (pre-time-sync)
Tightened (AD029 v2):   ±15ms REQUIRED, ±5ms GOAL

Specification Tiers:
  ±15ms - MUST ACHIEVE (hard requirement)
  ±10ms - SHOULD ACHIEVE (expected typical)
  ±5ms  - STRETCH GOAL (AD043 target)

FR003: Non-Overlapping Bilateral Stimulation
Old: Immediate fallback on BLE loss
Current: Synchronized fallback for 2 minutes, then single-device mode (unchanged)
```

**Rationale for Tightening:**

1. **Proven Capability:** Phase 2 time sync achieves ±30μs clock drift over 90 minutes
2. **AD043 Implementation:** EMA filter with paired timestamps targets <5ms mean error
3. **Engineering Pride:** We can do better than ±40ms, so let's do it
4. **Future-Proofing:** Tighter spec enables research and accessibility applications
5. **Therapeutic Safety Margin:** Well within human perception threshold (~200ms)

---

## Consequences

### Benefits of Tightened Spec (±15ms)

- **Technical excellence:** Validates Phase 2/3 time sync investment
- **Engineering satisfaction:** ±40ms offsets no longer acceptable, too easily achieved
- **Future applications:** Enables research requiring precise bilateral timing
- **Open-source credibility:** Demonstrates capability, not just "good enough"
- **Safety margin:** Still 10× inside human perception threshold
- **Therapeutic equivalence:** No change to EMDR effectiveness

### Costs of Tightened Spec

- **Implementation complexity:** Requires EMA filter, paired timestamps (already implemented)
- **Testing rigor:** Must validate ±15ms across all modes and conditions
- **Debugging effort:** Phase offsets >15ms now require investigation

### Unchanged from Original

- **Uninterrupted therapy:** Brief disconnections (0-2 min) still handled gracefully
- **Non-overlapping safety:** Guaranteed via pattern-broadcast architecture
- **FreeRTOS compatibility:** vTaskDelay() timing unchanged

---

## Options Considered (December 2025 Revision)

### Option A: Keep ±100ms (No Change)

**Pros:**
- No code changes needed
- Already therapeutically adequate

**Cons:**
- We can do better than ±40ms offsets
- Doesn't leverage Phase 2/3 time sync investment
- Leaves performance on the table

**Selected:** NO
**Rationale:** We can do better, and we should

### Option B: ±50ms Tolerance

**Pros:**
- Tighter than ±100ms
- Achievable with current implementation

**Cons:**
- Still allows ~40ms offsets that prompted this revision
- Doesn't push toward AD043's <5ms goal

**Selected:** NO
**Rationale:** Half-measure that doesn't address the core complaint

### Option C: ±15ms Tolerance (CHOSEN)

**Pros:**
- Achievable with EMA filter (AD043)
- Improves on 40ms offsets we observed in testing
- Clear stretch goal (±5ms) provides direction
- 10× inside human perception threshold

**Cons:**
- Requires validation testing
- Phase offsets >15ms now bugs instead of features

**Selected:** YES
**Rationale:** Balances achievability with engineering pride

### Option D: ±5ms Tolerance (Stretch Goal Only)

**Pros:**
- Maximum precision
- AD043's stated target

**Cons:**
- May not be consistently achievable during BLE jitter spikes
- Too aggressive as hard requirement

**Selected:** AS STRETCH GOAL
**Rationale:** Aspirational target, not hard requirement

---

## Related Decisions

### Superseding Documents
- **AD043: Filtered Time Synchronization** - EMA filter with paired timestamps, <5ms target
- **AD045: Synchronized Independent Bilateral Operation** - Pattern-broadcast architecture

### Related
- **AD028: Command-and-Control with Synchronized Fallback** - Original architecture (pre-time-sync)
- **AD041: Predictive Bilateral Synchronization** - Drift-rate extrapolation during disconnect
- **FR002: Non-Overlapping Stimulation** - Safety preserved via pattern-broadcast

---

## Implementation Notes

### Code References

- **Time Sync:** `src/time_sync.c`, `src/time_sync_task.c` (EMA filter, paired timestamps)
- **Motor Task:** `src/motor_task.c` (bilateral timing, epoch-based activation)
- **BLE Manager:** `src/ble_manager.c` (beacon exchange, motor epoch broadcast)

### Build Environment

- **Environment Name:** `xiao_esp32c6_ble_no_nvs`
- **Configuration File:** `sdkconfig.xiao_esp32c6_ble_no_nvs`
- **Phase:** Phase 6 (tightened specification)

### Testing & Verification

**Phase 2 Time Sync Validation (November 2025):**
- 90-minute stress test: ±30μs clock drift (excellent)
- 271/270 beacons exchanged (100% delivery)
- Quality score: 95% sustained
- 7 brief jitter spikes detected and recovered

**Tightened Spec Validation (December 2025 - PENDING):**
- [ ] Measure actual phase offset in all 5 modes
- [ ] Verify ±15ms achieved during mode changes
- [ ] Stress test: 20-minute session with mode changes
- [ ] Edge case: Verify recovery after BLE jitter spike

**Pass/Fail Criteria:**
- **PASS:** 95th percentile phase offset ≤ 15ms
- **GOAL:** Mean phase offset ≤ 5ms
- **FAIL:** Any phase offset > 15ms during stable operation

---

## JPL Coding Standards Compliance

- ✅ Rule #1: No dynamic memory allocation - Timing via vTaskDelay()
- ✅ Rule #2: Fixed loop bounds - Deterministic timing checks
- ✅ Rule #5: Return value checking - Timing functions validated
- ✅ Rule #6: No unbounded waits - vTaskDelay() for all timing
- ✅ Rule #7: Watchdog compliance - Timing doesn't block task
- ✅ Rule #8: Defensive logging - Timing deviations logged

---

## Revision History

### v2 (December 2025) - Tightened Specification
- Spec changed: ±100ms → ±15ms (±5ms goal)
- Status changed: Accepted → Superseded
- Rationale: Phase 2 time sync proven, AD043/AD045 implemented
- Trigger: We can do better than ±40ms, so let's raise the bar

### v1 (November 2025) - Original Relaxation
- Spec changed: ±10ms → ±100ms
- Rationale: Pre-time-sync, aligned with human perception
- Context: Command-and-control architecture (AD028)

## Migration Notes

**Original Migration (2025-11-21):**
Migrated from `docs/architecture_decisions.md`
Original location: AD029

**December 2025 Update:**
- DS004: Updated from ±100ms to ±15ms (±5ms goal)
- AD043, AD045: Referenced as superseding implementations
- requirements_spec.md: Timing tolerance section to be updated

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-12-11
