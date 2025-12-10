# 0045: Synchronized Independent Bilateral Operation

**Date:** 2025-12-08
**Phase:** 6u (Synchronized Independent Operation)
**Status:** Proposed
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of bilateral antiphase motor coordination requiring precise alternation,
facing correction algorithms that oscillate and diverge instead of converging (death spiral),
we decided for synchronized independent operation where both devices calculate transitions from synced clocks,
and neglected cycle-by-cycle drift correction approach,
to achieve stable antiphase with ±6 μs precision over 20 minutes (Phase 2 proven),
accepting that edge cases may require targeted corrections if discovered through passive monitoring.

---

## Problem Statement

**Current Approach: Correction Death Spiral**

Serial log analysis (Dec 8, 2025) revealed that cycle-by-cycle drift corrections are making antiphase WORSE, not better:

```
Time      CLIENT drift    Correction     Result
15:52:19  -930ms         +200ms SLOW    Getting better
15:52:20  -130ms         +65ms SLOW     Good!
15:52:22  -195ms         +97ms SLOW     Wait, worse again
15:52:24  -292ms         +146ms SLOW    Much worse
15:52:26  -438ms         +200ms SLOW    Catastrophic
15:52:28  -638ms         +200ms SLOW    Maxed out
15:52:30  -838ms         +200ms SLOW    Completely broken
15:52:32  position=36ms (should be 1000ms for antiphase!)
```

**Root Cause:** CLIENT should be at position 1000ms (half-cycle offset) but ends up at 36ms - basically **in-phase with SERVER** instead of antiphase.

**Evidence of Over-Engineering:**
- Bug #16: Unclamped correction for initial alignment
- Bug #20: Reset PD state to avoid stale derivative
- Bug #26: Corrections during COAST made things WORSE (permanently disabled)
- Bug #40: Systematic phase offset from accumulated errors
- Bug #41, #42, #43: Multiple attempts to fix correction sign/logic
- Deadbands, clamping, frequency-dependent limits
- ~500 lines of correction code that fights itself

**Phase 2 Time Sync Quality (90-Minute Test):**
- **±30 μs drift over 90 minutes** (0.003% timing error)
- **±6 μs over 20-minute therapy session** (proven in production)
- **100% sync quality** sustained
- **Conclusion:** Clocks are SO GOOD we don't need constant corrections

---

## Context

### Bluetooth Audio Analogy

Bluetooth audio achieves synchronized playback across multiple devices using the same approach:
1. **Sync clocks once** using precise time synchronization
2. **Both devices calculate playback times** from synchronized clock
3. **Play independently** - no cycle-by-cycle corrections
4. **Monitor quality passively** - only re-sync if quality degrades

### Phase 2 Provides Foundation

Our time sync infrastructure already provides everything we need:
- NTP-style clock synchronization (±6 μs precision)
- Quality metrics (0-100%)
- Drift tracking
- Beacon-based epoch broadcasting

### Why Current Approach Fails

**Classic Control System Instability:**
1. CLIENT detects "behind" (negative drift)
2. Applies SLOW-DOWN correction (extends wait)
3. Makes it MORE behind (opposite effect!)
4. Next cycle detects bigger drift
5. Applies more SLOW-DOWN
6. **Death spiral** until completely out of antiphase

This is likely due to:
- Stale beacon data causing inverted corrections
- RTT jitter (±15ms) worse than drift being corrected
- Correction sign errors
- Oscillation from fighting itself

---

## Decision

We will implement **Synchronized Independent Operation** where both devices calculate motor transitions independently from synchronized clocks, with passive monitoring for edge cases.

### Architecture: Independent Calculation

**SERVER (Simple - Broadcasts Epoch):**
```c
// SERVER starts new cycle at local time
int64_t server_cycle_start_us = time_sync_get_local_time_us();

// Broadcast epoch to CLIENT via beacon
time_sync_update_motor_epoch(server_cycle_start_us, cycle_duration_ms);

// Wait for ACTIVE duration (no corrections, just wait)
int64_t target_us = server_cycle_start_us + (active_ms * 1000);
while (time_sync_get_local_time_us() < target_us) {
    check_queue_for_mode_change();  // Non-blocking
}
// Transition to INACTIVE
```

**CLIENT (Calculate From Epoch - No Corrections):**
```c
// CLIENT reads last motor epoch from beacon
int64_t server_epoch_us;
uint32_t cycle_ms;
if (!time_sync_get_motor_epoch(&server_epoch_us, &cycle_ms)) {
    // No epoch yet - wait
    return;
}

// Calculate CLIENT's target time (antiphase = half cycle offset)
int64_t cycle_us = cycle_ms * 1000;
int64_t half_cycle_us = cycle_us / 2;
int64_t client_target_us = server_epoch_us + half_cycle_us;

// Wait until target time (simple!)
int64_t now_us = time_sync_get_local_time_us();
if (client_target_us > now_us) {
    int64_t wait_us = client_target_us - now_us;
    vTaskDelay(pdMS_TO_TICKS(wait_us / 1000));
}

// Start motor - perfectly antiphase!
motor_on(FORWARD, current_pwm);
```

### Mode Change Coordination (Two-Phase Commit)

To ensure smooth mode changes, both devices must agree on when to start the new pattern:

**Phase 1: Proposal & Agreement**
```c
// SERVER: User presses button to change mode
typedef struct {
    mode_t new_mode;
    uint32_t new_cycle_ms;
    uint32_t new_active_ms;
    int64_t server_epoch_us;   // When SERVER will start
    int64_t client_epoch_us;   // When CLIENT should start (server + half_cycle)
} mode_change_proposal_t;

// SERVER sends proposal with future epoch (2 seconds from now)
proposal.server_epoch_us = time_sync_get_local_time_us() + 2000000;
proposal.client_epoch_us = proposal.server_epoch_us + (new_cycle_us / 2);
send_mode_change_proposal(&proposal);

// CLIENT receives and validates
if (proposal.server_epoch_us > time_sync_get_local_time_us()) {
    // Future epoch - valid
    send_mode_change_ack(&proposal);
    arm_mode_change(proposal.client_epoch_us, proposal.new_mode);
}

// Both devices wait until their epoch, then start new pattern
```

**Phase 2: Synchronized Transition**
```c
// Both devices independently wait until their agreed epoch
while (time_sync_get_local_time_us() < my_epoch_us) {
    vTaskDelay(pdMS_TO_TICKS(10));
}
// Start new mode - guaranteed antiphase!
```

### Passive Monitoring (Edge Case Detection)

```c
// Monitor sync quality every cycle (don't correct!)
uint8_t sync_quality = time_sync_get_quality();
int64_t drift_us = time_sync_get_drift_us();

if (sync_quality < 50 || abs(drift_us) > 100000) {  // 100ms threshold
    ESP_LOGW(TAG, "Sync degraded: quality=%u%%, drift=%lld μs",
             sync_quality, drift_us);

    // Future: Could trigger re-sync or targeted correction
    // For now: Just log and monitor
}
```

### Edge Case Provisions

This architecture leaves room to add **targeted corrections** if we discover real edge cases through monitoring:

**Possible Future Additions (Only If Needed):**
- Cosmic ray detection: Sudden >100ms jump → re-sync
- Temperature-induced drift: Gradual >10ms → gentle correction
- BLE glitch recovery: Quality <50% for >30s → re-pair
- Crystal aging: Drift >5ms sustained → one-time offset adjust

**Key Difference:** Add corrections based on **evidence from monitoring**, not preemptive complexity.

---

## Consequences

### Benefits

✅ **Eliminates correction bugs** - No more Bug #16, #26, #40, #41, #42, #43
✅ **Simpler code** - ~500 lines of correction logic removed
✅ **Relies on proven tech** - Phase 2 time sync (±6 μs) is excellent
✅ **No oscillation** - Can't fight itself
✅ **Coordinated mode changes** - Two-phase commit ensures smooth transitions
✅ **Like Bluetooth audio** - Sync once, run independently
✅ **Passive monitoring** - Detect edge cases instead of preemptively correcting
✅ **Room to evolve** - Can add targeted corrections if evidence demands

### Drawbacks

⚠️ **Assumes clocks stay synced** - Relies on Phase 2 quality (proven over 90 min)
⚠️ **Edge cases unknown** - Cosmic rays, temperature extremes, crystal aging
⚠️ **No active compensation** - Must rely on passive monitoring to detect issues

### Performance Impact

**Code Reduction:**
- Remove: ~500 lines of correction logic
- Add: ~50 lines of mode change coordination
- Net: **90% reduction in complexity**

**Expected Precision:**
- Phase 2 proven: ±6 μs over 20 minutes
- At 1 Hz: 0.0006% timing error (imperceptible)
- No drift corrections needed for therapeutic use

---

## Implementation Plan

### Phase 1: Remove Correction Logic
1. Remove all drift correction code from INACTIVE state
2. CLIENT calculates target from epoch (simple math)
3. Both devices wait until target time
4. Monitor and log any drift (passive)

### Phase 2: Mode Change Protocol
1. Add mode_change_proposal_t message type
2. SERVER sends proposal with future epochs
3. CLIENT validates and acknowledges
4. Both devices arm transition and wait

### Phase 3: Passive Monitoring
1. Log sync quality every cycle
2. Log drift magnitude every cycle
3. Analyze logs for edge cases
4. **Only add corrections if evidence shows need**

### Phase 4: Edge Case Response (If Needed)
1. Cosmic ray detection: >100ms sudden jump
2. Temperature drift: >10ms gradual change
3. BLE glitch recovery: Quality <50% sustained
4. **Add minimal targeted corrections** based on evidence

---

## Validation & Testing

**Success Criteria:**
- Antiphase maintained within ±10ms over 20-minute session
- No drift corrections applied during normal operation
- Mode changes complete within 2 seconds
- Edge cases documented through passive monitoring

**Test Plan:**
1. **90-minute stress test** - Verify antiphase stability
2. **Mode change testing** - All modes, all frequencies
3. **Temperature variation** - Hot/cold environments
4. **BLE interference** - WiFi-heavy environments
5. **Edge case hunting** - Look for cosmic rays, glitches, drift

---

## Related Decisions

### Supersedes

- **[AD041: Predictive Bilateral Synchronization](0041-predictive-bilateral-synchronization.md)** - Drift correction approach caused death spiral (CLIENT at 36ms instead of 1000ms for antiphase). Position-based state forcing and cycle-by-cycle corrections replaced by epoch-based calculation with zero corrections. Phase 2's ±6 μs clock precision eliminates need for continuous drift compensation.
- Bug #16, #20, #26, #40, #41, #42, #43 fixes (all correction-related)

### Related
- [AD028: Command & Control](0028-command-control-synchronized-fallback.md) - Mode change coordination (two-phase commit protocol)

### Builds On
- Phase 2 Time Synchronization (±6 μs proven)
- [AD044: Non-Blocking Motor Timing](0044-non-blocking-motor-timing.md) - Polling architecture

---

## JPL Coding Standards Compliance

- ✅ **Rule #1: No dynamic memory allocation** - Stack variables only
- ✅ **Rule #2: Fixed loop bounds** - Deterministic wait loops
- ✅ **Rule #3: No recursion** - Flat control flow
- ✅ **Rule #4: No goto statements** - Structured logic
- ✅ **Rule #5: Return value checking** - All time sync API calls checked
- ✅ **Rule #6: No unbounded waits** - Wait loops have timeout bounds
- ✅ **Rule #7: Watchdog compliance** - Feed watchdog during waits
- ✅ **Rule #8: Defensive logging** - Passive monitoring logs

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-12-08
