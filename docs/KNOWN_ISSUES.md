# Known Issues

This document tracks known bugs and limitations that are documented for future resolution.

---

## Bug #105: NVS Peer Exclusivity Not Enforced

**Status:** Open
**Severity:** Medium
**Environment:** `xiao_esp32c6` (NVS bonding enabled)
**Discovered:** 2025-12-18

### Description

When using the production environment with NVS bonding enabled, a device that already has a paired peer saved in NVS will still connect to a **different** unpaired device if both are powered on during the pairing window.

### Expected Behavior

Once a peer MAC address is saved to NVS:
1. Device should ONLY scan for and connect to that specific peer
2. Connections from/to other devices should be rejected during peer discovery
3. NVS peer MAC should be the **source of truth** for finding a "friend"
4. Only clearing NVS (or explicit unpair action) should allow pairing with a different device

### Actual Behavior

- Device accepts connection from any peer during the discovery window
- Previously bonded peer is ignored if a new device connects first
- Results in unpredictable pairing behavior in multi-device environments

### Root Cause (Suspected)

The peer discovery logic doesn't check NVS for an existing bonded peer MAC before accepting new connections. The scan callback accepts any device advertising the bilateral service UUID.

### Proposed Fix

1. On startup, check NVS for saved peer MAC address
2. If peer MAC exists in NVS:
   - Only scan for that specific MAC address
   - Reject advertising/connections from other peers
   - After timeout (e.g., 30s), optionally fall back to open discovery
3. If no peer MAC in NVS:
   - Proceed with normal battery-based discovery and bonding
   - Save new peer MAC to NVS after successful pairing

### Files Likely Affected

- `src/ble_manager.c` - Scan callback, connection handling
- `src/nvs_manager.c` - Peer MAC storage/retrieval

### Workaround

Use `xiao_esp32c6_ble_no_nvs` environment during development/testing to avoid stale bond confusion.

---

## Bug #106: Firmware Version Timestamp Not Enforced

**Status:** Open (Deferred)
**Severity:** Low
**Discovered:** 2025-12-18

### Description

The firmware version checking system (AD040) was designed to compare both semantic version AND build timestamp, but:

1. The version mismatch was never actually preventing pairing
2. No orange LED blink pattern was shown on version mismatch
3. The `firmware_versions_match()` function was called but its return value may not have been used to reject connections

### Current State (v0.6.129)

The timestamp matching has been intentionally relaxed - only `major.minor.patch` is now enforced, with timestamp differences logged as warnings. This is the correct behavior for practical use since PlatformIO rebuilds make identical timestamps impractical.

### Remaining Issue

The original design called for visual feedback (orange blink) when firmware versions don't match. This was never implemented or tested.

### Proposed Resolution

1. Verify `firmware_versions_match()` is called during peer connection
2. Add orange LED blink pattern for version mismatch (warning, not rejection)
3. Log version mismatch clearly in serial output
4. Consider adding version info to PWA status display

### Priority

Low - Current behavior (semantic version matching) is sufficient for production use. Visual feedback is nice-to-have for debugging.

---

## Bug #107: LED Pattern Override - Yellow Overwritten by Green

**Status:** Open
**Severity:** Low (UX/Visual)
**Environment:** All environments with peer pairing
**Discovered:** 2025-12-18

### Description

When firmware version mismatch is detected between peers, the yellow warning LED pattern (`STATUS_PATTERN_VERSION_MISMATCH`) is briefly shown, but then immediately overwritten by the green success pattern (`STATUS_PATTERN_PAIRING_SUCCESS`), making the version warning invisible to the user.

### Expected Behavior

1. On firmware version mismatch: Show yellow blink pattern for full duration
2. User should clearly see the warning before any success indication
3. Patterns should not override each other in rapid succession

### Actual Behavior

- Yellow pattern starts but is quickly replaced by green
- User sees: brief yellow flash → green pattern
- Version mismatch warning is effectively invisible

### Root Cause (Suspected)

Multiple LED pattern triggers fire in sequence during the pairing/version exchange flow. The success pattern (`STATUS_PATTERN_PAIRING_SUCCESS`) is called after the mismatch pattern without waiting for the warning to complete.

Likely locations:
- `src/time_sync_task.c` - Version exchange handler calls patterns in sequence
- `src/ble_task.c` - Pairing success may trigger its own pattern

### Proposed Fix

1. Option A: **Queue-based patterns** - LED patterns queue up instead of replacing
2. Option B: **Priority system** - Warning patterns take priority over success
3. Option C: **Delay between patterns** - Add delay after warning before success
4. Option D: **Combined pattern** - Single "success with warning" pattern (yellow-green alternating)

### Files Likely Affected

- `src/status_led.c` - Pattern execution logic
- `src/time_sync_task.c` - Version exchange LED triggers
- `src/ble_task.c` - Pairing success LED triggers

### Workaround

Check serial logs for "Build timestamps differ" warning message to confirm version mismatch. LED indication is unreliable.

### Note

This is an **indicator/UX issue**, not a firmware version matching issue. The version matching logic itself works correctly (logs show timestamps differ). The problem is purely visual feedback.

---

## Bug #108: Pattern Start Time Mismatch (33ms Gap)

**Status:** Open
**Severity:** High (UTLP/Pattern Mode)
**Environment:** All environments with pattern playback (Mode 5)
**Discovered:** 2025-12-18

### Description

When entering pattern playback mode (Mode 5), SERVER and CLIENT start their pattern execution at different epoch times, resulting in ~33ms desynchronization. This violates the "sheet music" paradigm where both devices should read from the same synchronized timeline.

### Expected Behavior

Both devices should start pattern playback at the **same epoch time**:
- SERVER and CLIENT agree on a start_time during mode change proposal
- Both devices begin executing pattern segments from that identical timestamp
- Pattern segments should fire within ±1ms of each other

### Actual Behavior

From logs (2025-12-18):
```
SERVER: Pattern playback started (start_time=245750765 us)
CLIENT: Pattern playback started (start_time=245783658 us)
```

**Gap: 32,893 µs (33ms)** - unacceptable for synchronized bilateral playback.

Additional observations:
- Mode change proposal had `server_epoch=245743790`, `client_epoch=245748790`
- Neither device used the proposed epochs
- CLIENT logged: "Proposal not epoch-aligned (remainder=752790us)"

### Root Cause (Suspected)

1. **Proposed epochs not honored:** Both devices calculate new start times instead of using agreed epochs
2. **Alignment logic failure:** The "epoch-aligned" check is failing, causing fallback behavior
3. **Timing race:** CLIENT receives proposal, but by the time it acts, the epoch has passed

### Proposed Fix

1. Ensure mode change proposal epochs are used exactly (no recalculation)
2. If proposed epoch has passed, wait for next aligned epoch
3. Add tolerance for "almost aligned" epochs (within one tick)
4. Consider using absolute future time instead of relative offsets

### Files Likely Affected

- `src/time_sync_task.c` - Mode change proposal/ACK handling
- `src/motor_task.c` - Pattern start timing
- `src/pattern_playback.c` - Pattern initialization

### Impact on UTLP

This bug is **critical for UTLP implementation**. The "sheet music" paradigm requires:
- Identical start epoch on both devices
- Shared timeline reference (same "measure number")
- Sub-millisecond precision for visual lightbar effects

### Workaround

None - pattern mode (Mode 5) is experimental and should not be used for synchronized playback until this is fixed.

---

## Bug #109: SYNC_FB Causes Motor Cycle Timing Jitter

**Status:** Open
**Severity:** Medium (Timing)
**Environment:** All environments (CLIENT device)
**Discovered:** 2025-12-18

### Description

When the CLIENT sends a SYNC_FB (synchronization feedback) message, the following motor cycle start is delayed by 3-6ms. This jitter is systematic and occurs every time SYNC_FB is sent.

### Expected Behavior

Motor cycle starts should occur at consistent intervals (e.g., `.233` or `.234` milliseconds) regardless of BLE message activity.

### Actual Behavior

From logs:
```
Normal cycles:     10:05:02.234, 10:05:04.234, 10:05:06.234
After SYNC_FB:     10:05:12.238 (+4ms jitter)
Normal cycles:     10:05:14.233, 10:05:16.233, ...
After SYNC_FB:     10:05:32.237 (+4ms jitter)
Normal cycles:     10:05:34.233, ...
After SYNC_FB:     10:05:52.239 (+5ms jitter)
```

Pattern: **Every SYNC_FB send delays the next cycle by 3-6ms.**

### Root Cause (Suspected)

1. SYNC_FB involves a BLE write operation that blocks the motor task briefly
2. The BLE stack doesn't yield immediately, causing the delay
3. Contrast: REV_PROBE doesn't cause the same delay (different BLE operation type?)

### Impact

- **Immediate:** Single-cycle timing jitter (corrected next cycle)
- **Potential:** Could affect RTT measurements if they coincide with SYNC_FB timing
- **UTLP:** Jitter during time-critical operations could degrade sync quality

### Proposed Fix

1. **Option A:** Move SYNC_FB sending to a separate low-priority task (decouple from motor timing)
2. **Option B:** Use Write Without Response for SYNC_FB (faster BLE operation)
3. **Option C:** Send SYNC_FB asynchronously via queue to BLE task
4. **Option D:** Schedule SYNC_FB during motor inactive period (not at cycle boundary)

### Files Likely Affected

- `src/motor_task.c` - SYNC_FB sending logic
- `src/ble_manager.c` - BLE write implementation

### Related Observations

Other events that might cause similar jitter (needs investigation):
- Battery logging (~x.242)
- BLE_TASK state logging (~x.732)
- FW version logging (~x.102, ~x.201)
- Sync beacon received (TIME_SYNC_TASK, not motor task)

REV_PROBE does NOT cause the same delay, suggesting the issue is specific to SYNC_FB's BLE operation.

### Workaround

The jitter is self-correcting (next cycle returns to normal timing). For time-critical RTT measurements, avoid scheduling them during SYNC_FB cycles (every 10 cycles = 20 seconds at 0.5Hz).

---

## Bug #110: Shutdown During Pairing Leaves Peer Stranded

**Status:** Open
**Severity:** Medium
**Environment:** All environments
**Discovered:** 2025-12-18

### Description

If a device shuts down (button hold or low battery) at the moment pairing completes, the shutdown coordination message never gets sent to the newly-paired peer. The peer is left in an undefined state:
- **If CLIENT:** Does nothing, stuck waiting
- **If SERVER:** Enters link failure state

### Expected Behavior

1. Shutdown should be delayed until peer coordination is complete, OR
2. Shutdown coordination message should be sent before entering sleep, OR
3. Peer should detect "pairing completed but no activity" and timeout gracefully

### Actual Behavior

- Device A initiates shutdown during pairing window
- Pairing completes just as Device A enters deep sleep
- Device A doesn't know peer exists (or can't send message)
- Device B receives connection success but then immediately loses link
- Device B stuck in unexpected state

### Root Cause (Suspected)

Race condition between:
1. BLE pairing completion callback
2. Shutdown sequence (deep sleep entry)

The shutdown sequence doesn't check if pairing just completed, and the pairing completion doesn't check if shutdown is in progress.

### Proposed Fix

1. **Option A:** Add "pairing in progress" flag that delays shutdown by 2-3 seconds
2. **Option B:** Send shutdown coordination message in pairing success callback if shutdown pending
3. **Option C:** Add peer detection timeout (if connected but no beacons for 5s, assume peer gone)
4. **Option D:** Check `ble_is_peer_connected()` before entering deep sleep, send shutdown if true

### Files Likely Affected

- `src/button_task.c` - Shutdown sequence
- `src/ble_manager.c` - Pairing completion handler
- `src/ble_task.c` - Connection state management

### Workaround

Avoid pressing the shutdown button during the pairing window (first 30 seconds after power-on). Wait for pairing to complete (green LED flash) before initiating shutdown.

---

## Bug #111: role_manager_init() Never Called or Mutex Destroyed

**Status:** RESOLVED (v0.6.130)
**Severity:** High
**Environment:** All environments
**Discovered:** 2025-12-18

### Description

The `role_manager` module's mutex (`g_state_mutex`) is NULL during normal operation, causing every call to `role_get_current()` to log an error. This is particularly visible in Pattern Mode (Mode 5) where `zone_config_get()` calls `role_get_current()` every 10ms tick, resulting in a flood of error messages.

### Expected Behavior

1. `role_manager_init()` is called during startup
2. `g_state_mutex` is created and valid
3. All `role_get_current()` calls succeed without error

### Actual Behavior

From logs:
```
11:07:31.393 > E (65881) ROLE_MGR: role_get_current: mutex is NULL - role_manager_init() not called?
11:07:31.402 > E (65901) ROLE_MGR: role_get_current: mutex is NULL - role_manager_init() not called?
... (repeats every 10ms during pattern mode)
```

The error spams continuously during Pattern Mode because:
1. `pattern_execute_tick()` → `zone_config_get()` → `role_get_current()`
2. Each tick (10ms) triggers another NULL mutex check

### Root Cause (Suspected)

One of the following:
1. **Missing init call:** `role_manager_init()` is not called in `app_main()` or initialization sequence
2. **Init order issue:** Module is called before initialization completes
3. **Mutex destroyed:** Something is destroying the mutex after init
4. **Conditional compilation:** Init might be wrapped in a `#ifdef` that's not set

### Call Stack

```
pattern_execute_tick()
  └─> zone_config_get()           // src/zone_config.c
        └─> role_get_current()    // src/role_manager.c
              └─> [ERROR: mutex NULL]
```

### Impact

- **Error log spam:** ~100 errors/second during Pattern Mode
- **Potential crashes:** Before Bug #104 fix, this would have crashed
- **Role detection broken:** `zone_config_get()` can't determine device zone correctly
- **Pattern playback:** Zone assignment falls back to default (LEFT) instead of proper SERVER=RIGHT, CLIENT=LEFT

### Related Bugs

- **Bug #104:** Added NULL guards to role_manager.c (v0.6.128) - this bug is why those guards were needed

### Proposed Fix

1. **Check main.c:** Verify `role_manager_init()` is called in initialization sequence
2. **Add init check:** Log when `role_manager_init()` is called and succeeds
3. **Guard pattern mode:** Don't start pattern playback until role_manager is initialized
4. **Trace destruction:** Add logging if mutex is ever destroyed/freed

### Files Likely Affected

- `src/main.c` - Initialization sequence
- `src/role_manager.c` - Module initialization
- `src/pattern_playback.c` - Should check init status before using zone_config

### Workaround

The NULL guards (Bug #104) prevent crashes, but pattern mode zone assignment is broken. Avoid Pattern Mode until this is fixed, or accept that zone assignment will use fallback behavior.

### Resolution (v0.6.130)

Added `role_manager_init()` call to `init_hardware()` in [main.c](../src/main.c) after NVS init but before other modules:

```c
// 1b. Initialize Role Manager (Bug #111 Fix)
// Must be initialized early - zone_config depends on role_get_current()
ret = role_manager_init();
```

This ensures the mutex is created before any code calls `role_get_current()` or `zone_config_get()`.

---

## Issue Tracking Format

```markdown
## Bug #NNN: Brief Title

**Status:** Open | In Progress | Resolved | Deferred
**Severity:** Critical | High | Medium | Low
**Environment:** Affected build environment(s)
**Discovered:** YYYY-MM-DD

### Description
What the bug is.

### Expected Behavior
What should happen.

### Actual Behavior
What actually happens.

### Root Cause
Why it happens (if known).

### Proposed Fix
How to fix it.

### Files Affected
Which files need changes.

### Workaround
Temporary solution if available.
```

---

**Last Updated:** 2025-12-18 (Bug #111 added)
