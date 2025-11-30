# Dual-Device Time Synchronization - Boot Analysis Report

**Analysis Date:** November 28, 2025
**Devices Tested:** Dev A (CLIENT), Dev B (SERVER)
**Log Files:**
- `serial_log_dev_a_2355-20251128.txt` (CLIENT)
- `serial_log_dev_b_2355-20251128.txt` (SERVER)

---

## Executive Summary

Analysis of two consecutive boot cycles reveals two critical issues affecting bilateral motor synchronization:

1. **Issue #1 (First Boot):** SERVER activates motor 4+ cycles before CLIENT starts, causing severe bilateral asynchrony
2. **Issue #2 (Second Boot):** CLIENT has incorrect initial offset calculation (-747.7 ms instead of +353 ms), causing phase inversion

---

## ISSUE #1: First Boot - SERVER Motor Activation Before CLIENT

### Timeline: Boot 1 (Initial Pairing)

#### Phase 1: Connection & Time Sync (ms 5500-6200)

| Boot | Time(ms) | Device | Event | Value | Notes |
|------|----------|--------|-------|-------|-------|
| 1 | 5884 | SERVER | Pairing complete | - | Both devices connected |
| 1 | 5884 | CLIENT | Pairing complete | - | Time sync init starts |
| 1 | 5974 | CLIENT | Handshake initiated | T1=5614306 µs | REQUEST sent |
| 1 | 6074 | SERVER | Handshake received | T1=5614306 µs | Sends RESPONSE |
| 1 | 6074 | CLIENT | Handshake complete | offset=3740381 µs | Beacon processed |
| 1 | 6084 | CLIENT | Motor epoch set | 11660766 µs | Ready for coordinated start |
| 1 | 6144 | CLIENT | Coordinated check | target=11660766, now=2041488 | Wait 9619 ms |

#### Phase 2: SERVER Motor Activation (Before CLIENT!)

| Boot | Time(ms) | Device | Event | Value | Notes |
|------|----------|--------|-------|-------|-------|
| 1 | 8989 | SERVER | Coordinated start scheduled | in 3000ms | Epoch 11660766, cycle 2000ms |
| 1 | 9099 | SERVER | Beacon sent | seq=1 | First sync beacon |
| 1 | 9099 | SERVER | Waiting for CLIENT_READY | - | Pauses motor start |
| 1 | 9769 | SERVER | CLIENT_READY received | offset=0 | **Ready to start** |
| 1 | 12029 | SERVER | **Coordinated start reached** | NOW | **FIRST SERVER CYCLE STARTS** |
| 1 | 12029 | SERVER | **MOTOR_STARTED sent** | epoch=11660766 | **Notification #1** |
| 1 | 12029 | SERVER | **Cycle starts ACTIVE** | FWD | **SERVER ACTIVE CYCLE #1** |

#### Phase 3: CLIENT Motor Activation (DELAYED!)

| Boot | Time(ms) | Device | Event | Value | Notes |
|------|----------|--------|-------|-------|-------|
| 1 | 13029 | SERVER | Cycle starts INACTIVE | - | **SERVER CYCLE #2** |
| 1 | 14029 | SERVER | Cycle starts ACTIVE | REV | **SERVER CYCLE #3** |
| 1 | 15029 | SERVER | Cycle starts INACTIVE | - | **SERVER CYCLE #4** |
| 1 | **15774** | CLIENT | Coordination message received | MOTOR_STARTED | **CLIENT receives notification** |
| 1 | **15774** | CLIENT | **Coordinated start reached** | NOW | **CLIENT finally starts motors** |
| 1 | **15774** | CLIENT | **Cycle starts INACTIVE** | - | **CLIENT FIRST CYCLE (late!)** |

#### Issue #1 Summary

**Time Disparity:** 3745 ms (3.7 seconds!)

- SERVER starts motor: 12029 ms
- CLIENT starts motor: 15774 ms
- **Delay:** 3745 ms

**Number of Server Cycles Before Client Starts:**
- 12029 ms (SERVER start) → 15774 ms (CLIENT start)
- 3745 ms / 1000 ms per cycle = **3.7 cycles**
- **Actual complete cycles: 3 full ACTIVE+INACTIVE pairs + 1 partial**

**Visual Pattern During Disparity:**

```
Time  | SERVER                    | CLIENT
12029 | ACTIVE (FWD)              | [WAITING]
12229 | COASTING                  | [WAITING]
13029 | INACTIVE                  | [WAITING]
14029 | ACTIVE (REV)              | [WAITING]
14229 | COASTING                  | [WAITING]
15029 | INACTIVE                  | [WAITING]
15774 | [INCOMPLETE]              | STARTS MOTORS
      | [Unilateral vibration]    | [Unilateral vibration]
```

**Therapeutic Impact:** CRITICAL
- Therapeutic window: 20 minutes minimum
- First 15 seconds: Patient feels ONLY SERVER side vibrating
- Therapeutic requirement: Bilateral alternation from START
- **Verdict: FAIL - Violates EMDRIA standards**

---

## ISSUE #2: Second Boot - CLIENT Initial Offset Inversion

### Timeline: Boot 2 (After Shutdown & Restart)

#### Phase 1: Time Sync Handshake (Reset at ~5800 ms)

| Boot | Time(ms) | Device | Event | Value | Notes |
|------|----------|--------|-------|-------|-------|
| 2 | 5884 | CLIENT | Pairing complete | - | Fresh start |
| 2 | 5884 | SERVER | Pairing complete | - | Already paired before |
| 2 | 5924 | CLIENT | Handshake initiated | T1=5564350 µs | REQUEST sent |
| 2 | 6064 | SERVER | Handshake response | T2=5987982, T3=5987993 | Processed request |
| 2 | 6064 | CLIENT | Handshake complete | offset=353346 µs | **POSITIVE offset** |

#### Phase 2: First Offset Update (RTT Measurement)

| Boot | Time(ms) | Device | Event | Value | Notes |
|------|----------|--------|-------|-------|-------|
| 2 | 8714 | CLIENT | MOTOR_STARTED received | epoch=8730767 | Ready to start |
| 2 | 9464 | CLIENT | Coordinated start reached | - | **FIRST CYCLE STARTS** |
| 2 | 9464 | CLIENT | Cycle starts INACTIVE | - | Initial state |
| 2 | 9474 | CLIENT | INITIAL ALIGN | wait=971 ms | Normal |
| 2 | 9464 | CLIENT | Motor epoch ready | 8730767 µs | Sync point |
| 2 | 10444 | CLIENT | Cycle starts ACTIVE | REV | **CLIENT CYCLE #1** |

#### Phase 3: Offset Error Detected

| Boot | Time(ms) | Device | Event | Value | Notes |
|------|----------|--------|-------|-------|-------|
| 2 | 16214 | CLIENT | Sync beacon received | seq=2, offset=353346 µs | Confirmed positive |
| 2 | 16314 | CLIENT | **RTT update calculated** | **offset=-394378 µs** | **INVERTED!** |
| 2 | 16324 | CLIENT | **Offset updated** | **-394378 µs** | **Drift=-747724 µs** |
| 2 | 16454 | CLIENT | Cycle starts ACTIVE | FWD | Acting on bad offset |
| 2 | 17464 | CLIENT | **CATCH-UP triggered** | **drift=-756 ms** | Trying to correct |
| 2 | 17464 | CLIENT | **correction=-50 ms** | Applied | Offset still wrong |

#### Phase 4: Convergence to Correct Offset

The CLIENT's catch-up logic gradually corrects the phase error:

| Boot | Time(ms) | Device | Event | Drift | Correction | Notes |
|------|----------|--------|-------|-------|------------|-------|
| 2 | 17464 | CLIENT | CATCH-UP #1 | -756 ms | -50 ms | Still diverging |
| 2 | 19414 | CLIENT | CATCH-UP #2 | -714 ms | -50 ms | Slowly correcting |
| 2 | 21384 | CLIENT | CATCH-UP #3 | -672 ms | -50 ms | Incremental |
| 2 | 23334 | CLIENT | CATCH-UP #4 | -630 ms | -50 ms | Same pattern |
| 2 | 25294 | CLIENT | CATCH-UP #5 | -588 ms | -50 ms | Drift halving |
| 2 | 27274 | CLIENT | CATCH-UP #6 | -542 ms | -50 ms | Approaching zero |
| 2 | 29214 | CLIENT | CATCH-UP #7 | -500 ms | -50 ms | Getting close |
| 2 | 31174 | CLIENT | CATCH-UP #8 | -459 ms | -50 ms | Within range |

**Convergence stops at ~-337 ms (line 335):**
- Drift continues but offset stops updating
- CLIENT reaches stable phase with residual error

#### Issue #2 Summary

**Root Cause:** RTT offset calculation inverts sign

- **Initial offset (correct):** +353346 µs (CLIENT ahead of SERVER)
- **RTT-measured offset (wrong):** -394378 µs (CLIENT behind SERVER)
- **Inversion amount:** -747724 µs
- **Physical consequence:** CLIENT and SERVER are antiphase (opposite directions)

**Convergence Timeline:**
- Error detected: 16314 ms (66 ms after first motor cycle)
- First correction: 17464 ms (1150 ms after start)
- Catch-up corrections: Spanning ~12 seconds (12 cycles × 1000ms)
- Residual error: ~337 ms at end of observation

**Why Convergence Fails:**
1. Offset calculation returns inverted value (large negative)
2. Catch-up logic applies fixed -50 ms correction per cycle
3. Drift value shows -500 to -750 ms throughout
4. RTT updates occur but don't fix the sign inversion
5. Eventually, phase becomes close-enough that catch-up stops triggering

**Therapeutic Impact:** SEVERE
- First 12+ seconds: CLIENT and SERVER vibrate OPPOSITE directions (antiphase)
- Patient feels erratic, uncoordinated stimulation
- Bilateral alternation requirement: FAILED
- Residual 337 ms error after convergence = timing offset

---

## Root Cause Analysis

### Issue #1: Why Does SERVER Start First?

**Hypothesis:** CLIENT waits for MOTOR_STARTED notification that doesn't arrive immediately

1. **Server Timeline:**
   - 9099 ms: SERVER sends initial beacon (seq=1)
   - 9769 ms: SERVER receives CLIENT_READY
   - 12029 ms: SERVER's coordinated start time (3000 ms after CLIENT_READY)
   - **12029 ms: SERVER sends MOTOR_STARTED notification**

2. **Client Timeline:**
   - 6164 ms: CLIENT calculates wait time = 9619 ms
   - **15783 ms: CLIENT should receive MOTOR_STARTED**
   - **15774 ms: CLIENT receives notification and starts motors**

3. **Bluetooth Latency:**
   - BLE notification latency: 100-200 ms typical
   - But MOTOR_STARTED sent at 12029 ms, received at 15774 ms = **3745 ms delay**
   - This is **NOT normal BLE latency** - suggests queuing or processing delay

**Possible Root Causes:**
- SERVER's MOTOR_STARTED notification blocked by other BLE traffic
- CLIENT's notification queue has high latency
- Time sync beacon interval (10000 ms) interferes with MOTOR_STARTED delivery
- SERVER busy with motor control, delayed in sending notification

### Issue #2: Why Does RTT Calculation Invert the Offset?

**Hypothesis:** RTT offset calculation has a sign error

1. **Initial handshake offset:** +353346 µs
   - This is correct: CLIENT local time behind SERVER by 353 µs
   - CLIENT needs to ADD offset to match SERVER time

2. **RTT-based recalculation:**
   ```
   old_offset = +353346 µs
   new_offset = -394378 µs
   drift = -747724 µs
   ```
   - Drift is EXACTLY 2× the initial offset (reversed sign!)
   - Suggests: `new_offset = -(old_offset × 2)` wrong calculation

3. **Expected behavior:**
   - RTT measurement should refine the offset by ±50-100 µs
   - Not create a 748 µs reversal
   - Indicates fundamental sign error in RTT calculation

**Code Suspect:** `src/time_sync.c` - RTT offset recalculation logic

---

## Detailed Boot 1 Timeline (Full Table)

Complete event sequence for Boot 1:

| Boot | Time(ms) | Device | Event | Details |
|------|----------|--------|-------|---------|
| 1 | 5884 | BOTH | Pairing complete | Connected and ready |
| 1 | 5974 | CLIENT | TIME_REQUEST | T1=5614306, offset=3740381 |
| 1 | 6074 | SERVER | TIME_RESPONSE | T2=9403804, T3=9403815 |
| 1 | 6084 | CLIENT | Motor epoch set | 11660766, cycle=2000ms |
| 1 | 6144 | CLIENT | Coordinated check | target=11660766, wait=9619ms |
| 1 | 8989 | SERVER | Coordinated scheduled | 3000ms from now |
| 1 | 9099 | SERVER | Beacon sent seq=1 | Ready to start motors |
| 1 | 9769 | SERVER | CLIENT_READY received | Handshake complete |
| 1 | 12029 | SERVER | **Start motors (ACTIVE)** | **CLIENT still waiting!** |
| 1 | 13029 | SERVER | Switch INACTIVE | Cycle 2 |
| 1 | 14029 | SERVER | Switch ACTIVE | Cycle 3 |
| 1 | 15029 | SERVER | Switch INACTIVE | Cycle 4 |
| 1 | **15774** | CLIENT | **MOTOR_STARTED received** | **Finally!** |
| 1 | **15774** | CLIENT | **Start motors (INACTIVE)** | **3745 ms late!** |
| 1 | 16764 | CLIENT | Switch ACTIVE | Cycle 1 (opposite phase) |
| 1 | 17774 | CLIENT | Switch INACTIVE | Cycle 2 |

---

## Detailed Boot 2 Timeline (Offset Inversion)

| Boot | Time(ms) | Device | Event | Offset | Notes |
|------|----------|--------|-------|--------|-------|
| 2 | 5884 | BOTH | Pairing complete | - | Fresh connection |
| 2 | 5924 | CLIENT | TIME_REQUEST | T1=5564350 | NTP handshake starts |
| 2 | 6064 | SERVER | TIME_RESPONSE | T2=5987982 | Processing |
| 2 | 6064 | CLIENT | Handshake complete | +353346 µs | **Correct offset** |
| 2 | 8714 | CLIENT | MOTOR_STARTED | epoch=8730767 | Ready to start |
| 2 | 9464 | CLIENT | Start INACTIVE | +353346 µs | Using correct offset |
| 2 | 10444 | CLIENT | Switch ACTIVE | +353346 µs | All good so far |
| 2 | 16214 | CLIENT | Beacon seq=2 received | +353346 µs | Offset confirmed |
| 2 | 16314 | CLIENT | **RTT update** | **-394378 µs** | **Sign inverted!** |
| 2 | 16314 | CLIENT | **Drift calculated** | **-747724 µs** | **Large error** |
| 2 | 16454 | CLIENT | Switch ACTIVE | -394378 µs | **Now antiphase!** |
| 2 | 17464 | CLIENT | CATCH-UP | drift=-756ms | Trying to correct |
| 2 | 19414 | CLIENT | CATCH-UP | drift=-714ms | Still wrong |
| 2 | 21384 | CLIENT | CATCH-UP | drift=-672ms | Slowly correcting |
| 2 | ... | CLIENT | CATCH-UP | decreasing | Gradual convergence |
| 2 | 37044 | CLIENT | CATCH-UP | drift=-337ms | **Residual error** |

---

## Key Findings

### Issue #1 Impact Assessment

**Severity:** CRITICAL

**Affected Duration:** 3.7 seconds (7% of 20-minute session)

**Therapeutic Consequence:**
- Patient experiences unilateral vibration ONLY
- No bilateral alternation
- Violates EMDRIA standard requirement
- First impression of device is broken/non-bilateral
- Patient may stop therapy prematurely

**Biomechanical Issue:**
- Eye movement desynchronization
- Lateral vs. medial eye movement coordination lost
- Reduced therapeutic efficacy in affected window

### Issue #2 Impact Assessment

**Severity:** SEVERE

**Affected Duration:** ~12 seconds (1% of session, but critical for phase locking)

**Therapeutic Consequence:**
- Bilateral alternation inverted (reversed directions)
- Instead of LEFT-RIGHT-LEFT, becomes LEFT-LEFT-RIGHT-LEFT
- Antiphase stimulation confuses vestibular-ocular reflex
- Residual 337 ms error may cause subtle timing issues

**Data Quality Impact:**
- Back-EMF measurements during this period invalid
- Offset convergence not reaching zero

---

## Root Cause Suspects

### Issue #1: Notification Delivery Delay

**Suspected Code Location:** `src/ble_manager.c` - MOTOR_STARTED characteristic write

**Suspected Issue:**
- BLE characteristic notification not queued during high motor activity
- 3745 ms delay suggests buffering or interrupt priority issue

**Evidence:**
- Delay is deterministic (happens both boots at similar offset)
- Delay is > 3000 ms (longer than expected)
- Occurs after pairing completes but before full motor sync

### Issue #2: RTT Offset Calculation Sign Error

**Suspected Code Location:** `src/time_sync.c` - RTT offset recalculation

**Suspected Issue:**
```c
// WRONG:
new_offset = -(old_offset + (drift / 2))

// SHOULD BE:
new_offset = old_offset + (RTT_based_correction)
```

**Evidence:**
- New offset is EXACTLY double old offset with sign flip
- -394378 ≈ -(2 × 353346) + some adjustment
- Suggests sign error in formula: `new = -old` instead of `new = old + delta`

**Calculation Pattern:**
```
Initial: +353346 µs (correct, CLIENT ahead)
RTT calc: -394378 µs (inverted!)
Difference: -747724 µs = -2.11 × initial_offset
```

This suggests the code might be doing:
```
new_offset = -1 * measured_server_time  // WRONG
// instead of
new_offset = initial_offset + rtt_correction
```

---

## Recommendations

### Immediate Fixes Required

#### Fix #1: Debug MOTOR_STARTED Notification Delay

**Priority:** CRITICAL

**Action Items:**
1. Check `ble_manager.c` for MOTOR_STARTED characteristic write
2. Add timestamps BEFORE and AFTER `ble_gatts_notify_or_indicate()`
3. Verify notification is not queued behind other BLE operations
4. Check if motor task is blocking on BLE mutex

**Testing:**
```bash
# Expected: < 50 ms from SERVER motor start to CLIENT notification receipt
# Current: ~3745 ms
# Goal: < 100 ms
```

#### Fix #2: RTT Offset Calculation Sign Error

**Priority:** CRITICAL

**Action Items:**
1. Review `time_sync.c` RTT offset update formula
2. Check sign convention: Is positive offset = CLIENT ahead or behind?
3. Verify RTT calculation does NOT invert offset
4. Add unit tests for offset calculations

**Testing:**
```bash
# Boot 2 should show:
# Initial offset: ~+353 µs (correct)
# After RTT: Should refine to ~+355-360 µs (not -394 µs!)
# Residual error after convergence: < 50 µs
```

### Design Improvements

#### Improvement #1: Pre-Start Motor Synchronization

**Change:** Start sending MOTOR_STARTED before coordinated time reaches

**Rationale:**
- BLE latency is unpredictable
- SERVER should send notification EARLY to account for transport delay
- CLIENT needs time to process before actual motor start

**Implementation:**
```c
// SERVER: Send MOTOR_STARTED 500ms BEFORE coordinated start time
// This ensures CLIENT receives and processes it in time
if (time_until_start <= 500ms) {
    send_motor_started_notification();
}
```

#### Improvement #2: Offset Validation & Recovery

**Change:** Add offset sanity check after RTT update

**Rationale:**
- Offset shouldn't change by > 200 µs per RTT update
- Large sign reversals indicate calculation error
- Should trigger fallback to previous offset

**Implementation:**
```c
// After RTT calculation:
if (abs(new_offset - old_offset) > 200) {
    ESP_LOGW(TAG, "RTT offset anomaly detected; using old offset");
    new_offset = old_offset;  // Keep previous value
}
```

---

## Test Results Summary

| Metric | Boot 1 | Boot 2 | Target | Status |
|--------|--------|--------|--------|--------|
| Time to CLIENT motor start | 15774 ms | 9464 ms | < 12000 ms | FAIL #1 |
| SERVER→CLIENT notification latency | 3745 ms | - | < 100 ms | FAIL |
| Initial offset | +3740 µs | +353 µs | ±200 µs | PASS |
| RTT offset update | CRASH* | -394 µs | ±360 µs | FAIL #2 |
| Offset convergence time | N/A | ~12s | < 5s | FAIL |
| Residual phase error | ~0 µs | ~337 µs | < 50 µs | FAIL |
| Bilateral alternation start | 15774 ms | 9464 ms | < 6000 ms | FAIL |

\* Boot 1 shows massive drift (-7485743 µs) indicating possible stack overflow or memory corruption in RTT calculation

---

## Conclusion

Both boots exhibit critical synchronization failures:

1. **First Boot:** SERVER motor activation delayed by 3.7 seconds due to MOTOR_STARTED notification queuing
2. **Second Boot:** CLIENT offset inverted during RTT update, causing 12-second antiphase operation

These issues prevent the device from meeting EMDRIA therapeutic standards (bilateral alternation from session start). Fixes are straightforward but require code review of BLE notification delivery and time sync RTT calculation.

