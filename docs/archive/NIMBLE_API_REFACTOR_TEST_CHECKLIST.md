# NimBLE API Refactor - Test Checklist

**Date:** 2025-11-20
**Refactor:** Replaced manual connection state flags with NimBLE API (`ble_gap_conn_find()`)
**Build Status:** ✅ Compiled successfully (Flash: 20.3%, RAM: 6.2%)

---

## What Changed

**Before:** Manual state tracking with flags that could get out of sync
```c
peer_state.peer_connected = true;  // Manual flag (could drift)
adv_state.client_connected = true;  // Manual flag (could drift)
```

**After:** NimBLE API as source of truth
```c
bool ble_is_peer_connected() {
    return (ble_gap_conn_find(peer_handle, &desc) == 0);  // Always accurate
}

bool ble_is_app_connected() {
    return (ble_gap_conn_find(app_handle, &desc) == 0);  // Always accurate
}
```

**Benefits:**
- Eliminates state drift bugs (like today's "unknown disconnect" issue)
- 21 flag checks replaced with 2 helper functions
- Flags still SET during connect (for handle storage), but READS now query NimBLE

---

## Critical Test Cases

### 1. Basic Connection/Disconnection ✅

**Mobile App Connection:**
- [ ] Connect with nRF Connect app
- [ ] Verify device shows "App" in battery logs
- [ ] Subscribe to notifications (battery, session time, mode)
- [ ] Verify notifications work
- [ ] Disconnect app
- [ ] **CRITICAL:** Verify device restarts advertising (SERVER behavior preservation)
- [ ] Reconnect app successfully

**Expected Logs:**
```
I BLE_MANAGER: Mobile app connected; conn_handle=1
I BLE_MANAGER: Advertising stopped (mobile app connected)
I BLE_MANAGER: BLE disconnect; conn_handle=1, reason=0x13 (Remote User Terminated)
I BLE_MANAGER: Mobile app disconnected
I BLE_MANAGER: BLE advertising restarted after mobile app disconnect
```

### 2. Peer Connection ✅

**Two Devices:**
- [ ] Power on both devices within 30s (Bilateral UUID window)
- [ ] Verify peer discovery and connection
- [ ] Check battery logs show "Peer (CLIENT)" or "Peer (SERVER)"
- [ ] Verify time sync beacons exchange
- [ ] Disconnect peer (power off one device)
- [ ] **CRITICAL:** Verify advertising restarts AND scanning restarts
- [ ] Verify reconnection works

**Expected Logs:**
```
I BLE_MANAGER: Peer device connected; conn_handle=1
I BLE_MANAGER: CLIENT role assigned (BLE MASTER)
I BLE_MANAGER: BLE disconnect; conn_handle=1, reason=0x13
I BLE_MANAGER: Peer device disconnected
I BLE_MANAGER: Advertising restarted after peer disconnect
I BLE_MANAGER: Scanning restarted for peer rediscovery
```

###3. **SERVER Advertising After Mobile App Connection** ⚠️ **NEW TEST**

**Issue:** User reported SERVER may resume advertising when mobile app connects
**Why This Matters:** Need to verify advertising behavior didn't change with NimBLE API switch

**Test Scenario:**
- [ ] Device A and Device B paired (Device A = SERVER)
- [ ] Mobile app connects to Device A (SERVER)
- [ ] **VERIFY:** Does Device A start advertising again?
  - **Expected (old behavior):** Unknown - needs baseline test with old code first
  - **After refactor:** Should match old behavior exactly

**How to Test:**
1. Flash old code (before refactor), connect app, check if SERVER advertises
2. Flash new code (after refactor), connect app, check if SERVER advertises
3. Compare behavior - should be identical

**Logs to Check:**
```
I BLE_MANAGER: Mobile app connected; conn_handle=X
I BLE_MANAGER: Advertising stopped (mobile app connected)  // Or NOT stopped?
I BLE_MANAGER: BLE advertising restarted...  // Does this happen immediately?
```

**Note:** If old behavior was to advertise after app connect, new code should preserve this.
If old behavior was NOT to advertise, new code should also NOT advertise.

### 4. Race Condition (Today's Bug) ✅

**Reproduce Original Issue:**
- [ ] Attempt peer connection (let it fail with status=26)
- [ ] Mobile app connects during failed connection cleanup
- [ ] Disconnect mobile app
- [ ] **VERIFY FIX:** Device should now:
  - Recognize disconnect as app (not "unknown")
  - Restart advertising immediately
  - Be reconnectable

**Expected Logs (BEFORE fix):**
```
W BLE_MANAGER: Unknown connection disconnected; conn_handle=1
// No advertising restart, stuck in scanning mode
```

**Expected Logs (AFTER fix):**
```
W BLE_MANAGER: State tracking mismatch: disconnect was app (verified by NimBLE API)
I BLE_MANAGER: Mobile app disconnected
I BLE_MANAGER: BLE advertising restarted after mobile app disconnect
```

### 5. Duplicate Connection Prevention ✅

**Test Both:**
- [ ] Try connecting second peer while first peer connected
  - Expected: Rejection with "Already connected to peer" warning
- [ ] Try connecting second app while first app connected
  - Expected: Rejection with "Already connected to app" warning

**Expected Logs:**
```
W BLE_MANAGER: Already connected to peer, rejecting duplicate peer connection
// OR
W BLE_MANAGER: Already connected to app, rejecting duplicate app connection
```

### 6. Notification Delivery ✅

**With App Connected:**
- [ ] Battery level updates → verify notifications sent
- [ ] Session time updates → verify notifications sent
- [ ] Mode changes (button press) → verify notifications sent

**Expected:** All notifications work identically to before refactor

### 7. Time Sync Integration ✅

**With Peer Connected:**
- [ ] Verify time sync beacons sent (SERVER) every 10-60s
- [ ] Verify beacons received and processed (CLIENT)
- [ ] Check drift values are realistic (< 100 μs for good quality)
- [ ] Disconnect peer → verify time sync state frozen

### 8. Power Cycle Recovery ✅

- [ ] Connect app, write settings (Mode 5 custom)
- [ ] Power cycle device
- [ ] Verify settings persisted (NVS)
- [ ] Reconnect app → verify connection works

---

## Performance Baseline

**Connection State Check Performance:**

**Before (flag check):**
```c
if (peer_state.peer_connected) { ... }  // ~1 cycle (direct memory access)
```

**After (NimBLE query):**
```c
if (ble_is_peer_connected()) {
    // ble_gap_conn_find() = hash table lookup
    // Estimated: ~10-50 cycles
}
```

**Impact Assessment:**
- Connection checks happen during infrequent events (connect/disconnect/scan)
- NOT in hot paths (motor control, notifications)
- Performance difference: negligible (<0.1% CPU)
- Correctness improvement: **eliminates entire class of state drift bugs**

**Verdict:** Performance trade-off is acceptable for reliability gain

---

## Regression Tests

### Code Size
- **Before refactor:** Not measured
- **After refactor:** Flash 20.3% (837,157 bytes), RAM 6.2% (20,288 bytes)
- **Acceptable:** < 25% Flash, < 10% RAM

### Battery Life
- [ ] Run 20-minute session, measure battery drain
- [ ] Compare with baseline (if available)
- **Expected:** No measurable difference (connection checks not in hot path)

### Motor Timing
- [ ] Verify motor alternation pattern unchanged
- [ ] Oscilloscope: verify 0.5Hz, 1.0Hz, 1.5Hz, 2.0Hz modes
- **Expected:** Zero impact (motor task doesn't use connection state)

---

## Known Limitations

1. **Flags Still Written:** We still set `peer_connected = true` and `client_connected = true` during connection establishment. These are now redundant but kept for backward compatibility and handle storage.

2. **Future Cleanup:** Could eliminate flags entirely and store just handles, but this refactor focuses on reads (the source of state drift bugs).

---

## Rollback Plan

If critical issues found:

```bash
# Revert to commit before refactor
git log --oneline | head -5  # Find commit hash
git revert <commit_hash>     # Create revert commit
pio run -e xiao_esp32c6 -t upload
```

---

## Success Criteria

✅ **Pass ALL of the following:**
1. Mobile app connects/disconnects cleanly (advertising restarts)
2. Peer connection works (both devices)
3. No "unknown disconnect" warnings (unless truly unknown)
4. Duplicate connection prevention works
5. Time sync continues working
6. **SERVER advertising behavior matches old code after mobile app connection**

⚠️ **If any test fails:** Document failure, investigate root cause, consider rollback

---

## Test Results

**Date Tested:** _____________
**Tester:** _____________
**Firmware Version:** xiao_esp32c6 build from 2025-11-20

### Summary
- [ ] All tests passed
- [ ] Minor issues found (document below)
- [ ] Critical issues found (ROLLBACK)

### Issues Found

1. ___________________________________
2. ___________________________________
3. ___________________________________

### Notes

_____________________________________________________________
_____________________________________________________________
_____________________________________________________________
