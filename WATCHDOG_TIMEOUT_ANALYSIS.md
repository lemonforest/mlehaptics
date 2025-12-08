# Watchdog Timeout Analysis - Motor Task State Machine

**Date:** 2025-12-07
**Issue:** Watchdog timeout at 42636ms during normal motor operation
**Last Operation:** Back-EMF logging in ACTIVE state

---

## Error Log Analysis

```
I (41896) MOTOR_TASK: REV: 2336mV→+1372mV | 3202mV→+3104mV | 3219mV→+3138mV
E (42636) task_wdt:  - IDLE (CPU 0)
E (42636) task_wdt: CPU 0: motor_task
```

**Timeline:**
- Last successful log: 41896ms (back-EMF logging)
- Watchdog timeout: 42636ms
- **Gap: 740ms**

**Interpretation:**
- IDLE task is starved (can't feed watchdog)
- motor_task is hogging CPU without yielding
- **NOT** related to GPIO remapping (no code logic changes)

---

## Critical Findings

### ✅ CONFIRMED: GPIO Remapping NOT the Cause

My recent GPIO20→GPIO18 remapping changed:
- Only `#define` values in headers/test files
- Comments in motor_control.c
- Documentation

**Zero code logic changes.** The watchdog timeout is **pre-existing** or **scenario-specific**.

### ⚠️ PROBLEM #1: PAIRING_WAIT State - Missing Watchdog Feeds

**Location:** [src/motor_task.c:592-596](src/motor_task.c#L592-L596)

```c
// SERVER: Wait for time_sync initialization (1000ms max)
int init_wait = 20;  // 20 × 50ms = 1000ms max
while (init_wait > 0 && !TIME_SYNC_IS_INITIALIZED()) {
    vTaskDelay(pdMS_TO_TICKS(50));  // Yields but NO watchdog feed
    init_wait--;
}
```

**Issue:** 1 second loop without feeding watchdog
**Risk:** Low (1s < 2s timeout) but violates defensive programming
**Fix:** Add `esp_task_wdt_reset()` inside loop

---

**Location:** [src/motor_task.c:693-696](src/motor_task.c#L693-L696)

```c
// CLIENT: Wait for handshake to complete (5s max)
int handshake_wait = 100;  // 100 × 50ms = 5s max
while (handshake_wait > 0 && !TIME_SYNC_IS_INITIALIZED()) {
    vTaskDelay(pdMS_TO_TICKS(50));  // Yields but NO watchdog feed
    handshake_wait--;
}
```

**Issue:** **5 second loop** without feeding watchdog
**Risk:** HIGH - Exceeds 2s watchdog timeout
**Impact:** CLIENT devices will timeout during pairing initialization
**Fix:** Add `esp_task_wdt_reset()` inside loop (like other long waits)

---

### ⚠️ PROBLEM #2: INACTIVE State - No Watchdog Feeding

**Location:** [src/motor_task.c:1582-1873](src/motor_task.c#L1582-L1873)

**Observation:** Entire INACTIVE state has **zero watchdog feeds**

**Why This Matters:**
- INACTIVE periods can be LONG (especially at low frequencies)
- Example: 0.5Hz with 1500ms coast = 1.5 seconds in INACTIVE
- If `delay_until_target_ms()` takes >2s, watchdog times out

**Current Protection:**
- `delay_until_target_ms()` checks queue every 50ms (yields)
- CHECK_MESSAGES feeds watchdog every cycle

**Gap:** If INACTIVE→CHECK_MESSAGES transition is delayed, timeout can occur

---

### 🔍 PROBLEM #3: Potential BLE Blocking After Back-EMF

**User's Error Context:**
- Last log: "REV: 2336mV→..." (back-EMF in ACTIVE state)
- 740ms gap before watchdog timeout

**Question:** What happens immediately after back-EMF logging?

**Code Path After Back-EMF ([src/motor_task.c:1544-1577](src/motor_task.c#L1544-L1577)):**

1. Back-EMF logging completes
2. `delay_until_target_ms(active_end_target_ms)` - waits for ACTIVE period to end
3. State transition logic (SERVER vs CLIENT paths)
4. Transition to next state

**Potential Blocking Points:**
- BLE operations (battery updates, coordination messages)
- Time sync API calls (if blocking internally)
- Queue operations (if queues full)
- LED updates

---

## Watchdog Timeout Scenarios

### Scenario A: Pairing Initialization (CLIENT)

**State:** PAIRING_WAIT
**Trigger:** `handshake_wait` loop at line 693
**Duration:** Up to 5000ms
**Watchdog Timeout:** 2000ms
**Result:** ❌ GUARANTEED TIMEOUT

**Evidence:** User mentioned "new unit build" and "back to client timing debugging" - likely hit this during pairing!

---

### Scenario B: Long INACTIVE Period

**State:** INACTIVE
**Trigger:** Low frequency mode (0.5Hz) with long coast times
**Duration:** Up to 1500ms
**Watchdog Timeout:** 2000ms
**Result:** ⚠️ POSSIBLE if transition delayed

**Mitigation:** `delay_until_target_ms()` yields every 50ms (IDLE can run)
**Caveat:** If something blocks AFTER delay completes...

---

### Scenario C: BLE Operation Blocking

**State:** CHECK_MESSAGES or ACTIVE
**Trigger:** BLE send operation hangs
**Examples:**
- `ble_send_coordination_message()` blocks
- `ble_update_battery_level()` waits for ATT confirmation
- `ble_send_time_sync_beacon()` hangs on connection issues

**Duration:** Variable (could be >2s if BLE stack blocks)
**Result:** ⚠️ POSSIBLE especially with poor RF conditions

---

## Recommended Fixes

### Priority 1: Fix CLIENT Handshake Loop (CRITICAL)

```c
// src/motor_task.c:693-696
int handshake_wait = 100;  // 100 × 50ms = 5s max
while (handshake_wait > 0 && !TIME_SYNC_IS_INITIALIZED()) {
    vTaskDelay(pdMS_TO_TICKS(50));
    esp_task_wdt_reset();  // FIX: Feed watchdog during long wait
    handshake_wait--;
}
```

**Justification:** 5s loop WILL timeout without this fix.

---

### Priority 2: Fix SERVER Init Loop

```c
// src/motor_task.c:592-596
int init_wait = 20;  // 20 × 50ms = 1000ms max
while (init_wait > 0 && !TIME_SYNC_IS_INITIALIZED()) {
    vTaskDelay(pdMS_TO_TICKS(50));
    esp_task_wdt_reset();  // FIX: Feed watchdog for defensive programming
    init_wait--;
}
```

**Justification:** Defensive programming - prevent future issues if timeout reduced.

---

### Priority 3: Add Watchdog Feed to INACTIVE State

**Option A:** Feed in `delay_until_target_ms()` (already done)
**Option B:** Feed at INACTIVE state entry and exit

```c
// src/motor_task.c:1582 (INACTIVE state entry)
case MOTOR_STATE_INACTIVE: {
    // Feed watchdog at state entry
    esp_task_wdt_reset();

    // ... existing code ...
}
```

**Justification:** Defense in depth - ensure watchdog fed even if delays are long.

---

### Priority 4: Audit All BLE Calls

**Search for blocking BLE operations:**
- `ble_send_coordination_message()`
- `ble_update_battery_level()`
- `ble_send_time_sync_beacon()`
- `time_sync_get_*()` API calls

**Verify:** None of these block for >2 seconds

---

## Testing Strategy

### Test 1: Pairing Initialization Timeout

**Setup:**
1. Flash firmware to new device (CLIENT role)
2. Boot without SERVER present (or with BLE off)
3. Observe logs during pairing wait

**Expected:**
- ✅ WITHOUT FIX: Watchdog timeout at ~5 seconds during handshake wait
- ✅ WITH FIX: No timeout, graceful timeout message after 5 seconds

---

### Test 2: Low Frequency Operation

**Setup:**
1. Flash firmware to paired devices
2. Set mode to 0.5Hz (longest INACTIVE periods)
3. Run for 5+ minutes

**Expected:**
- ✅ No watchdog timeouts during normal operation

---

### Test 3: BLE Stress Test

**Setup:**
1. Flash firmware to paired devices
2. Move devices to RF-hostile environment (metal enclosure, WiFi interference)
3. Run for 5+ minutes

**Expected:**
- ✅ Graceful handling of BLE failures
- ❌ If timeout occurs: Audit BLE API for blocking calls

---

## Conclusion

The watchdog timeout is **NOT caused by GPIO remapping**. My changes only affected GPIO pin numbers, not code logic.

**Root Cause:** AD044 changed `MODE_CHECK_INTERVAL_MS` from **50ms → 1ms**, starving the IDLE task.

When `delay_until_target_ms()` calls `vTaskDelay(1ms)` 2000 times during a 2-second INACTIVE period, motor_task only yields for 1ms at a time. The IDLE task (priority 0, lowest) doesn't get enough CPU time to feed its own watchdog, causing timeout.

**User Context Match:** "new unit build" + "client timing debugging" = Watchdog timeout during normal motor operation, button lag from blocking delays.

**Fixes Applied:**

✅ **Priority 1: CLIENT handshake loop** (line 697) - Added `esp_task_wdt_reset()` in 5-second wait loop
✅ **Priority 2: SERVER init loop** (line 595) - Added `esp_task_wdt_reset()` in 1-second wait loop
✅ **Priority 3: delay_until_target_ms() function** (line 345) - Added `esp_task_wdt_reset()` in main delay loop (NOT SUFFICIENT)
✅ **INTERIM FIX: MODE_CHECK_INTERVAL_MS** (line 60) - Changed from 1ms to 10ms (fixed IDLE starvation but still unnecessary optimization)
✅ **FINAL FIX: MODE_CHECK_INTERVAL_MS** (line 60) - Reverted to 50ms (main branch baseline)

**Impact:**
- Eliminates IDLE task starvation - motor_task yields for 50ms (proven stable baseline)
- Button response remains excellent - 50ms latency is imperceptible (<100ms threshold)
- All tasks get fair CPU time - FreeRTOS scheduler can run IDLE task
- Removes unnecessary CPU overhead from 1ms polling (980 additional wake-ups/second eliminated)

---

**Testing Required:**
1. ✅ Build verification
2. Hardware test: Run 0.5Hz mode (longest INACTIVE periods) for 5+ minutes - NO watchdog timeout
3. Hardware test: Verify quick button presses change mode instantly (50ms latency)
4. Hardware test: Verify no watchdog timeouts during CLIENT pairing

---

## AD044 Design Conflation Analysis

### Why Did AD044 Include Button Polling Optimization?

**AD044 Primary Goal (lines 10-17):**
- CLIENT hardware timer synchronization for bilateral antiphase precision
- Achieve ±50μs precision (20× improvement over ±1ms jitter)
- Problem: CLIENT needs to synchronize to SERVER motor_epoch

**Design Conflation Identified:**

AD044 conflated **two independent optimizations**:

1. **Non-Blocking Motor Timing** (NECESSARY FOR GOAL)
   - Check time with `esp_timer_get_time()` instead of blocking with `vTaskDelay()`
   - Allows motor task to remain responsive during long coast periods
   - Enables CLIENT hardware timer callbacks to trigger transitions with ±50μs precision
   - **This is the core goal of AD044**

2. **Fast Button Response** (UNNECESSARY SIDE EFFECT)
   - Poll queue every 1ms instead of 50ms
   - Reduces message latency from 50ms to 1ms
   - **But 50ms was already instant** (<100ms human perception threshold)
   - Caused IDLE task starvation (watchdog timeout)

### Evidence of Conflation

**AD044 Decision Section (lines 103-108) lists these together:**
1. "Polls control queue every 1ms" instead of blocking
2. "Tracks state transitions using `esp_timer_get_time()`" for precise timing
3. "Processes messages immediately" (target <1ms latency)

**Key Insight:**

CLIENT synchronization precision comes from `esp_timer_get_time()` hardware accuracy (±10-50μs), NOT from queue polling rate. You could poll the queue every 50ms and still achieve ±50μs CLIENT synchronization if you check `esp_timer_get_time()` on each poll to see if a transition is needed.

**Conflation Indicators in AD044:**

- Line 188: "~1ms message response time (50× improvement from 50ms baseline)" - Treating button response as part of bilateral timing goal
- Lines 205-214: Performance analysis focuses on 980 additional wake-ups/second from 1ms polling - This overhead was unnecessary for the stated goal
- Lines 186-191: Benefits list mixes bilateral timing ("Simplifies bilateral synchronization") with user input ("Enables responsive features")

### Correct Implementation

**What AD044 Should Have Specified:**

```c
// NON-BLOCKING state machine with 50ms polling (CORRECT)
while (1) {
    // Poll queue every 50ms (instant button response)
    if (xQueueReceive(motor_queue, &msg, pdMS_TO_TICKS(50)) == pdTRUE) {
        handle_message(&msg);
    }

    // Check if it's time to transition (±50μs precision)
    int64_t now_us = esp_timer_get_time();
    if (now_us >= next_transition_us) {
        // Transition to next state
    }
}
```

This achieves both goals:
- ✅ Non-blocking motor timing (check time on each loop)
- ✅ ±50μs CLIENT synchronization (from `esp_timer_get_time()` precision)
- ✅ Instant button response (50ms < 100ms perception threshold)
- ✅ Fair task scheduling (IDLE task gets CPU time)

### Lessons Learned

1. **Separate concerns in architecture decisions** - Motor timing precision and user input responsiveness are independent
2. **Question performance optimizations** - 1ms vs 50ms button response is imperceptible to humans
3. **Understand where precision comes from** - CLIENT precision comes from hardware timer accuracy, not polling rate
4. **Consider task starvation** - Very short vTaskDelay() intervals can prevent lower-priority tasks from running

**Resolution:** Reverted MODE_CHECK_INTERVAL_MS to 50ms (main branch baseline). This preserves all AD044 benefits (non-blocking motor timing, ±50μs CLIENT precision) without the unnecessary CPU overhead and task starvation issues.
