# Phase 6s Testing - Critical Bug Report

**Test Date:** 2025-12-03 07:50 AM
**Version Tested:** v0.6.56 (Phase 6s - Two-Stage Antiphase Lock)
**Test Duration:** ~8 minutes
**Test Mode:** Mode 4 (Custom) - 0.5Hz, 79% duty, PWM 58%

**Deployment Status:** Phase 6s (v0.6.56) deployed to therapist for live testing
**Hardware Status:** Development paused for new unit assembly

---

## Summary

Phase 6s testing revealed **three critical bugs** that must be fixed before production deployment:

1. **Bug #48: Role Assignment Ignores Battery Level** (CRITICAL - affects fairness)
2. **Bug #49: Convergence Issues - Lock Timeout and Loss** (HIGH - affects reliability)
3. **Bug #50: Mode 4 Duty Cycle UX Confusion** (MEDIUM - affects user understanding)

---

## Bug #48: Role Assignment Ignores Battery Level (CRITICAL)

### Symptom
SERVER role is determined by **power-on order**, not battery level, despite battery-based role assignment being implemented in Phase 1c.

### Evidence from Serial Logs

**Dev A (powered on first) - serial_log_dev_a_0750-20251203.txt:**
```
Line 16: W (4982) BLE_MANAGER: No peer battery data - falling back to discovery-based role
Line 24: I (5252) BLE_MANAGER: SERVER role assigned (BLE MASTER)
```

**Dev B (powered on second) - serial_log_dev_b_0750-20251203.txt:**
```
Line 16: W (4612) BLE_MANAGER: No peer battery data - falling back to discovery-based role
Line 24: I (4882) BLE_MANAGER: CLIENT role assigned (BLE SLAVE)
```

### Root Cause
Battery data is not being exchanged during discovery phase, causing both devices to fall back to discovery-based role assignment (BLE MASTER/SLAVE), which is determined by **which device initiates the connection** (powered on first).

### Impact
- **Fairness issue:** Device with higher battery should be SERVER to balance load
- **User confusion:** Role assignment appears random (actually based on power-on order)
- **Therapeutic impact:** Higher-battery device may run out first if used as CLIENT

### Expected Behavior
Per AD035 (Battery-Based Initial Role Assignment):
- Both devices broadcast battery level via BLE Service Data (Battery Service UUID 0x180F)
- Peer extracts battery from scan response BEFORE connection
- Higher battery device initiates connection (becomes SERVER/MASTER)
- Lower battery device waits (becomes CLIENT/SLAVE)

### Files to Investigate
- `src/ble_manager.c` - Battery data broadcasting in advertising packets
- `src/ble_manager.c` - Battery extraction from scan response
- `src/ble_manager.c:2256-2319` - Battery-based role assignment logic

### Proposed Fix
1. Verify battery level is being broadcast in advertising Service Data
2. Verify peer battery extraction from scan response
3. Add logging to show battery comparison during role assignment
4. Ensure fallback only occurs if battery data genuinely unavailable

---

## Bug #49: Convergence Issues - Lock Timeout and Loss (HIGH)

### Symptom
CLIENT device experiences:
- **5-second antiphase lock timeout** during startup
- **Lock loss during session** requiring re-establishment via beacons

### Evidence from Serial Logs

**Dev B (CLIENT) - serial_log_dev_b_0750-20251203.txt:**
```
Line 78:  W (11437) MOTOR_TASK: CLIENT: Antiphase lock TIMEOUT after 5s
Line 116: W (22437) MOTOR_TASK: CLIENT: Antiphase lock LOST (will re-establish via beacons)
```

**Offset Drift Analysis:**
```
Initial offset: -3958835 µs
Stable offset:  -3970000 µs (approximately)
Drift range:    ~12 ms over session
```

### Root Cause
Phase 6s two-stage antiphase lock is too conservative:
- Waits for **steady-state filter mode** (10+ samples) before lock detection
- Beacons arrive at **1-2 second intervals** → 10-20 second wait time
- 5-second timeout triggers before lock can be established

### Impact
- **UX degradation:** CLIENT appears "frozen" while waiting for lock
- **Therapeutic disruption:** Lock loss during session interrupts bilateral stimulation
- **User confusion:** Asymmetric startup behavior (SERVER starts immediately, CLIENT waits)

### Expected Behavior
Per Phase 6t implementation:
- Fast lock beacon burst (5 beacons @ 200ms = 1 second)
- Early variance-based lock detection (±2ms threshold over 5 samples)
- Lock achieved in ~1 second (vs 5+ seconds in Phase 6s)

### Phase 6t Fixes (Already Implemented in PR #4)
- `src/time_sync_task.c:674-686` - Forced beacon burst after handshake
- `src/time_sync.c:827-835` - 200ms beacon intervals (vs 500ms)
- `src/time_sync.c:1505-1548` - Early variance-based lock detection
- `src/motor_task.c:564-573` - Coordinated 1.5s start delay

### Status
**RESOLVED in Phase 6t (v0.6.57)** - Awaiting hardware testing

---

## Bug #50: Mode 4 Duty Cycle UX Confusion (MEDIUM)

### Symptom
Mode 4 (Custom) displays **"79% duty"** but actual motor duty cycle is **39.5%**, causing user confusion about haptic intensity.

### Evidence from Serial Logs

**Dev A (SERVER) - serial_log_dev_a_0750-20251203.txt:**
```
Line 690: I (167272) MOTOR_TASK: Mode 4 (Custom): 0.50Hz, 79% duty → ACTIVE[790ms motor + 210ms coast] | INACTIVE[1000ms], PWM=58%
```

**Duty Cycle Calculation:**
```
User Setting:        79% duty
Cycle Period:        2000ms (0.5Hz)
ACTIVE Period:       1000ms (50% of cycle)
Motor ON Time:       790ms (79% of ACTIVE period)
Actual Duty Cycle:   790ms / 2000ms = 39.5% (NOT 79%!)
```

### Root Cause
Semantic ambiguity in "duty cycle" definition:
- **User expectation:** Duty cycle = % of total cycle with motor ON
- **Firmware implementation:** Duty cycle = % of ACTIVE period with motor ON (correct for bilateral)
- **Display:** Shows "79% duty" without clarifying it's relative to ACTIVE period

### Why Current Behavior is Correct
For **bilateral alternation**, ACTIVE and INACTIVE periods MUST be equal (50/50 split):
- ACTIVE period = cycle / 2 (e.g., 1000ms @ 0.5Hz)
- INACTIVE period = cycle / 2 (e.g., 1000ms @ 0.5Hz)

If "79% duty" meant "79% of total cycle":
- ACTIVE period = 1580ms
- INACTIVE period = 420ms
- **This BREAKS bilateral alternation** (not 50/50)

Therefore, duty cycle MUST be relative to ACTIVE period to maintain bilateral symmetry.

### Impact
- **User confusion:** Expects 79% haptic feedback, gets 39.5%
- **UX issue:** Display is misleading ("79% duty" sounds like total cycle duty)
- **Therapeutic concern:** User may set excessively high duty trying to reach desired intensity

### Proposed Fixes (Choose One)

**Option 1: Change Display to Show Actual Duty Cycle** (Recommended)
```c
// Before:
ESP_LOGI(TAG, "Mode 4 (Custom): %.2fHz, %u%% duty → ...", freq_x100 / 100.0f, duty, ...);

// After:
uint8_t actual_duty = (motor_on_ms * 100) / cycle_ms;  // 790/2000 = 39.5%
ESP_LOGI(TAG, "Mode 4 (Custom): %.2fHz, %u%% total duty (%u%% active) → ...",
         freq_x100 / 100.0f, actual_duty, duty, ...);
```

**Option 2: Relabel to "Active Period Duty"**
```c
ESP_LOGI(TAG, "Mode 4 (Custom): %.2fHz, %u%% active duty → ...", freq_x100 / 100.0f, duty, ...);
```

**Option 3: Add BLE Characteristic Description**
Update mobile app UI to clarify:
- Label: "Motor Duty (% of active period)"
- Help text: "Percentage of the active half-cycle with motor ON. 100% = continuous during active period."

### Files to Modify
- `src/motor_task.c:354-357` - Logging display
- `src/ble_manager.c` - BLE characteristic descriptions (if Option 3)

---

## Additional Issue: Time Sync Initialization Race Condition

### Symptom
`time_sync_on_reconnection()` called before time_sync module initialization completes.

### Evidence from Serial Logs

**Dev A (SERVER) - serial_log_dev_a_0750-20251203.txt:**
```
Line 44: E (5732) TIME_SYNC: Not initialized
Line 51: W (5732) BLE_MANAGER: time_sync_on_reconnection failed; rc=259
```

### Root Cause
CCCD write callback triggers `time_sync_on_reconnection()` before `time_sync_init()` completes.

### Impact
- **Initialization failure:** Time sync may not start properly after reconnection
- **Error logging:** Confusing error messages during normal startup
- **Potential instability:** Undefined behavior if time sync functions called before init

### Proposed Fix
Add initialization check in `time_sync_on_reconnection()`:
```c
esp_err_t time_sync_on_reconnection(void) {
    if (!g_time_sync_state.initialized) {
        ESP_LOGW(TAG, "Time sync not yet initialized, deferring reconnection setup");
        return ESP_ERR_INVALID_STATE;
    }
    // ... existing code
}
```

---

## Test Configuration

**Hardware:**
- Device A (SERVER): COM3, powered on first
- Device B (CLIENT): COM7, powered on second

**Firmware:**
- Version: v0.6.56 (Phase 6s)
- Build: xiao_esp32c6_ble_no_nvs

**Mode Settings:**
- Mode: 4 (Custom)
- Frequency: 0.50Hz (50 × 100)
- Duty Cycle: 79% (of active period)
- PWM Intensity: 58%

**Test Environment:**
- Date: 2025-12-03
- Session duration: ~8 minutes
- No user intervention during test

---

## Recommendations

### Immediate Fixes (Phase 6u or Hotfix)

1. **Bug #48 (Battery Role Assignment)** - CRITICAL
   - Priority: P0 - Must fix before production deployment
   - Effort: Medium (1-2 hours debugging + testing)
   - Risk: High if not fixed (fairness and battery life)

2. **Bug #49 (Convergence)** - HIGH
   - Priority: P1 - Already fixed in Phase 6t
   - Effort: Zero (just deploy Phase 6t)
   - Risk: Medium (UX degradation, not a safety issue)

3. **Bug #50 (Duty Cycle UX)** - MEDIUM
   - Priority: P2 - Can be fixed incrementally
   - Effort: Low (15-30 minutes for display change)
   - Risk: Low (UX confusion, not a functional issue)

4. **Time Sync Race Condition** - LOW
   - Priority: P3 - Minor initialization issue
   - Effort: Low (15 minutes for guard check)
   - Risk: Very low (self-corrects after init)

### Testing Plan

1. **Fix Bug #48 first** - Battery-based role assignment
2. **Merge Phase 6t** - Fast lock (already fixes Bug #49)
3. **Fix Bug #50** - Duty cycle display clarity
4. **Hardware test all fixes** - 90-minute stress test with two devices
5. **Deploy to therapist** - Only after all critical bugs fixed

### Phase 6t Deployment Decision

Phase 6t (v0.6.57) in PR #4 already addresses Bug #49 (convergence issues).
Recommend:
- **Merge Phase 6t to main** after fixing Bug #48
- **Test Phase 6t on hardware** before therapist deployment
- **Update CHANGELOG** with all bug fixes

---

## Appendix: Serial Log Analysis

### Battery Voltage Tracking

**Dev A (SERVER):**
```
Initial:  4.16V [96%]
Midpoint: 4.16V [96%]
Final:    4.16V [96%] (stable, no drain observed)
```

**Dev B (CLIENT):**
```
Initial:  4.13V [93%]
Midpoint: 4.13V [93%]
Final:    4.13V [93%] (stable, no drain observed)
```

Short test duration (~8 min) shows no significant battery drain.

### Time Sync Offset Tracking (Dev B CLIENT)

```
Initial offset:     -3958835 µs
Converged offset:   -3970000 µs (approx)
Offset range:       ±12 ms variation
Beacon count:       10+ beacons observed
Lock quality:       Unstable (timeout + loss events)
```

Phase 6s lock detection too slow, Phase 6t should resolve this.

---

**End of Bug Report**
