# ADR 046: Hardened PTP with Bidirectional Feedback

**Status:** Proposed
**Date:** December 12, 2025
**Context:** IEEE 1588-style time sync hardening with CLIENT→SERVER activation feedback

## Executive Summary

This document outlines a hardened PTP implementation with **bidirectional feedback** between CLIENT and SERVER. The key innovation is that CLIENT reports its actual activation times back to SERVER, enabling closed-loop validation and eventual correction.

**Phased Rollout:**
1. **Phase 1 (Observation):** Log corrections that *would* be applied, validate the algorithm
2. **Phase 2 (Active):** Apply corrections based on validated feedback loop

## The Feedback Loop

### Current Architecture (One-Way)
```
SERVER → beacon(epoch, cycle_period) → CLIENT
CLIENT calculates target time, activates, hopes it's right
```

### Hardened Architecture (Bidirectional)
```
SERVER → beacon(epoch, cycle_period) → CLIENT
CLIENT activates, records actual_time_us
CLIENT → activation_report(actual_time, cycle_number) → SERVER
SERVER compares: expected vs actual, calculates drift correction
SERVER → next beacon includes drift adjustment (Phase 2)
```

## What We Already Have

| Component | Status | Location |
|-----------|--------|----------|
| Four-timestamp exchange (T1-T4) | ✅ | `SYNC_MSG_TIME_REQUEST/RESPONSE` |
| IEEE 1588 offset formula | ✅ | `time_sync_process_handshake_response()` |
| EWMA filter (α=10%) | ✅ | `TIME_FILTER_ALPHA_PCT` |
| Drift rate tracking | ✅ | `drift_rate_us_per_s` |
| Motor epoch in beacon | ✅ | AD045 pattern-broadcast |
| Activation report message | ✅ | `SYNC_MSG_ACTIVATION_REPORT` |

## What We Need to Add

### 1. Enhanced Activation Report Payload

```c
// CLIENT sends this after each activation
typedef struct __attribute__((packed)) {
    uint64_t actual_time_us;    // When CLIENT actually activated (sync time)
    uint32_t cycle_number;      // Which cycle this was
    int16_t  local_drift_us;    // CLIENT's observed drift from expected
    uint8_t  direction;         // FWD=0, REV=1
    uint8_t  reserved;          // Alignment
} activation_report_t;  // 16 bytes
```

### 2. SERVER-Side Validation Logic

```c
// SERVER receives activation report, compares to expected
void process_activation_report(activation_report_t *report) {
    // Calculate expected CLIENT activation time
    uint64_t expected_us = motor_epoch_us +
                          (report->cycle_number * cycle_period_us) +
                          (cycle_period_us / 2);  // Antiphase offset

    // Compare actual vs expected
    int32_t phase_error_us = (int32_t)(report->actual_time_us - expected_us);

    #if PTP_APPLY_CORRECTIONS
        // Phase 2: Apply correction to next beacon
        accumulated_correction_us += phase_error_us * CORRECTION_GAIN;
    #else
        // Phase 1: Log only, validate algorithm
        ESP_LOGI(TAG, "PTP_HARDENED: cycle=%u expected=%llu actual=%llu error=%+dμs",
                 report->cycle_number, expected_us, report->actual_time_us, phase_error_us);
    #endif
}
```

### 3. Phased Correction Application

**Phase 1 (Observation):**
```c
// In platformio.ini:
-DPTP_APPLY_CORRECTIONS=0  // Log corrections, don't apply

// SERVER logs:
// PTP_HARDENED: cycle=5 expected=12345678 actual=12345712 error=+34μs
// PTP_HARDENED: cycle=6 expected=14345678 actual=14345690 error=+12μs
// PTP_HARDENED: correction_would_be=+23μs (not applied)
```

**Phase 2 (Active):**
```c
// After validation, enable:
-DPTP_APPLY_CORRECTIONS=1  // Apply corrections to beacon

// SERVER applies accumulated correction to next motor_epoch
// CLIENT receives corrected epoch, phase error converges to zero
```

## Implementation Plan

### Phase 1: Observation Infrastructure (Low Risk)

**Goal:** Collect data, validate algorithm, don't change behavior

1. **Enhance `activation_report_t`** with expected vs actual comparison
2. **Add SERVER-side logging** of phase errors
3. **Track correction values** that *would* be applied
4. **Collect 10+ sessions** of observation data

**Files:**
- `src/ble_manager.h` - Enhanced report structure
- `src/motor_task.c` - CLIENT sends enhanced reports
- `src/time_sync_task.c` - SERVER processes and logs reports

### Phase 2: Active Corrections (Medium Risk)

**Goal:** Apply validated corrections, achieve sub-10ms phase lock

1. **Add `PTP_APPLY_CORRECTIONS` build flag** (default=0 initially)
2. **Implement correction accumulator** in SERVER
3. **Apply corrections to motor_epoch** in beacon
4. **Validate convergence** in hardware tests

**Validation Criteria Before Enabling:**
- Phase error consistently <±50ms in observation logs
- Correction algorithm converges (doesn't oscillate)
- No systematic bias detected
- 10+ sessions without anomalies

## Correction Algorithm Design

### Option A: Immediate Correction (Aggressive)
```c
// Apply 100% of error immediately
motor_epoch_us += phase_error_us;
```
**Risk:** Overcorrection, oscillation

### Option B: Damped Correction (Conservative)
```c
// Apply 25% of error per cycle
#define CORRECTION_GAIN 0.25f
correction_us = (int32_t)(phase_error_us * CORRECTION_GAIN);
motor_epoch_us += correction_us;
```
**Benefit:** Smooth convergence, no oscillation

### Option C: EMA-Filtered Correction (Recommended)
```c
// Track average error over N cycles, apply smoothed correction
static int32_t ema_error_us = 0;
ema_error_us = (ema_error_us * 9 + phase_error_us) / 10;  // α=0.1

// Only correct if error is consistent (not noise)
if (abs(ema_error_us) > CORRECTION_THRESHOLD_US) {
    motor_epoch_us += ema_error_us / 2;  // Apply half of smoothed error
}
```
**Benefit:** Filters noise, only corrects systematic drift

## Key Principle

> "Hardening means closed-loop validation, not just one-way hope."

The current system broadcasts epoch and trusts CLIENT to activate correctly. The hardened system adds CLIENT feedback, enabling SERVER to:
1. **Verify** CLIENT actually activated when expected
2. **Detect** systematic drift before it becomes perceptible
3. **Correct** drift in real-time (Phase 2)

## Success Criteria

### Phase 1 (Observation)
- [ ] Activation reports received and logged on SERVER
- [ ] Phase error calculated and logged for each cycle
- [ ] Proposed corrections logged (not applied)
- [ ] 10+ sessions collected with <5% data loss

### Phase 2 (Active)
- [ ] Phase error converges to <±10ms within 30 seconds
- [ ] No oscillation or overcorrection
- [ ] 90-minute stress test passes
- [ ] Mode changes don't break correction loop

## Relationship to Existing ADRs

- **AD039** (Phase 2 Time Sync): Foundation - we build on this
- **AD043** (Filtered Time Sync): EMA filter reused for corrections
- **AD045** (Pattern-Broadcast): Motor epoch mechanism enhanced, not replaced
- **AD041** (Predictive Bilateral): Drift prediction feeds correction algorithm

## Risk Assessment

| Phase | Risk | Mitigation |
|-------|------|------------|
| Observation | Very Low | Logging only, no behavioral change |
| Active (initial) | Medium | Start with conservative gain, validate |
| Active (tuned) | Low | Proven algorithm, extensive testing |

## Recommendation

**Start with Phase 1 (Observation)** immediately. Add enhanced activation reports and SERVER-side logging. Collect data from real sessions. This validates the feedback loop without any risk.

Only enable Phase 2 (Active Corrections) after:
1. Observation data confirms algorithm correctness
2. Correction values are consistent and converge
3. No anomalies detected in 10+ sessions

---

*ADR 046: Hardened PTP with Bidirectional Feedback*
*mlehaptics Project | December 2025*
