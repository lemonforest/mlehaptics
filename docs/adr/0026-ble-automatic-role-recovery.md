# 0026: BLE Automatic Role Recovery

**Date:** 2025-11-05
**Phase:** 1
**Status:** Superseded
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of BLE connection loss during bilateral therapy sessions,
facing manual power cycle requirement to restore bilateral mode,
we decided for "survivor becomes server" automatic role switching after 30s timeout,
and neglected immediate role switch or manual role selection,
to achieve session continuity despite device failure,
accepting 30-second timeout before role switch occurs.

**Note (November 11, 2025):** Single-device fallback behavior superseded by AD028 (Command-and-Control with Synchronized Fallback). Role recovery mechanism remains valid.

---

## Problem Statement

Original design had manual role assignment (first device = server, second = client) but no automatic recovery if BLE connection lost:
- If server device fails, client device stuck waiting
- If client device fails, server has no reconnection target
- User must manually power cycle both devices to reset roles
- Interrupts therapy session unnecessarily

---

## Context

**Dual-Device Operation Requirements:**
- Bilateral stimulation requires coordinated operation between two devices
- BLE connection can be lost due to: battery failure, interference, distance
- Therapy sessions are 20-90 minutes (long enough for connection issues)
- User intervention during therapy session should be minimized

**Technical Constraints:**
- BLE connection loss detection is immediate
- Role assignment determines which device advertises (server only)
- NVS pairing data enables reconnection (exception to AD011)

**User Experience Goals:**
- Session continuity despite device failure
- Automatic recovery when failed device returns
- No manual intervention required

---

## Decision

We will implement "survivor becomes server" automatic role switching after 30-second BLE disconnection timeout.

**Automatic Role Recovery Protocol:**

**Server Failure Scenario:**
1. Server device fails or is powered off
2. Client detects BLE disconnection
3. Client continues in single-device mode (forward/reverse alternating)
4. After 30-second timeout, client switches to server role
5. Client (now server) begins advertising
6. When original server returns, it discovers new server and becomes client
7. Session continues in bilateral mode

**Client Failure Scenario:**
1. Client device fails or is powered off
2. Server detects BLE disconnection
3. Server continues in single-device mode (forward/reverse alternating)
4. Server continues advertising for new client
5. When original client returns, it discovers server and reconnects as client
6. Session continues in bilateral mode

**"Survivor Becomes Server" Logic:**
```c
// Client device monitoring BLE connection
if (ble_connection_lost) {
    // Continue therapy in single-device mode
    motor_mode = SINGLE_DEVICE_ALTERNATING;

    // Start 30s timeout for role switch
    uint32_t timeout_start = xTaskGetTickCount();

    while (ble_connection_lost && !session_timeout) {
        // Continue single-device therapy
        motor_task_single_device();

        // Check if 30s elapsed
        if ((xTaskGetTickCount() - timeout_start) > pdMS_TO_TICKS(30000)) {
            // Switch to server role
            ble_role = BLE_ROLE_SERVER;
            ble_start_advertising();
            ESP_LOGI(TAG, "Role switch: Client → Server (survivor)");
            break;
        }

        vTaskDelay(pdMS_TO_TICKS(1000));  // Check every 1s
    }
}
```

**Background Pairing in Single-Device Mode:**

While operating in single-device mode after disconnection:
- Motor task continues forward/reverse alternating pattern
- BLE task scans for peer device in background (low priority)
- If peer reappears, automatic reconnection and bilateral mode resume
- User experience: seamless transition from single to bilateral

---

## Consequences

### Benefits

- **Session continuity:** Therapy not interrupted by device failure
- **Automatic recovery:** No user intervention required
- **Role flexibility:** Survivor takes charge to enable reconnection
- **Balanced timeout:** 30s allows transient vs permanent failure distinction
- **NVS exception justified:** Pairing data enables reconnection (settings, not state)
- **Symmetric design:** Works for server or client failure

### Drawbacks

- **30-second delay:** Brief period in single-device mode before role switch
- **NVS dependency:** Requires pairing data storage (acceptable exception to AD011)
- **Complexity:** Additional state machine logic for role switching

---

## Options Considered

### Option A: No Automatic Role Recovery

**Pros:**
- Simpler implementation
- No role switching logic needed

**Cons:**
- User must manually reset both devices
- Interrupts therapy session unnecessarily
- Poor user experience

**Selected:** NO
**Rationale:** Unacceptable user experience for medical device

### Option B: Immediate Role Switch on Disconnection

**Pros:**
- Fastest recovery to bilateral mode
- No timeout delay

**Cons:**
- Too aggressive (BLE packet loss shouldn't trigger role switch)
- Transient interference would cause unnecessary role changes
- Could create connection instability

**Selected:** NO
**Rationale:** 30s timeout balances transient interference vs permanent failure

### Option C: Manual Role Selection via Button

**Pros:**
- User has explicit control
- No automatic behavior surprises

**Cons:**
- Adds UI complexity
- Requires user intervention during session
- Interrupts therapy workflow

**Selected:** NO
**Rationale:** Automatic recovery provides better user experience

### Option D: 30-Second Timeout with Automatic Switch (CHOSEN)

**Pros:**
- Balances transient interference vs permanent failure
- Survivor takes server role automatically
- Allows time for transient issues to resolve
- Provides seamless user experience

**Cons:**
- 30-second delay before role switch
- Added complexity

**Selected:** YES
**Rationale:** Best balance of reliability and user experience

---

## Related Decisions

### Superseded By
- **AD028: Command-and-Control with Synchronized Fallback** - Replaced single-device fallback with synchronized fallback phases

### Related
- **AD011: No Session State in NVS** - Clarified pairing data storage exception
- **FR001: Automatic Pairing** - Coordination with random delay prevents simultaneous server attempts
- **FR003: Background Pairing** - Added background pairing in single-device mode

---

## Implementation Notes

### Code References

- **BLE Task:** `src/ble_task.c` (role recovery state machine)
- **Motor Task:** `src/motor_task.c` (single-device fallback mode)
- **NVS Manager:** `src/nvs_manager.c` (pairing data storage)

### Build Environment

- **Environment Name:** `xiao_esp32c6`
- **Configuration File:** `sdkconfig.xiao_esp32c6`
- **Phase:** Phase 1 dual-device implementation

### Testing & Verification

**Test Scenarios:**
- Server failure: Client switches to server after 30s
- Client failure: Server continues advertising
- Reconnection: Failed device becomes client when returning
- Transient interference: <30s packet loss doesn't trigger role switch

**Pairing Data in NVS (Exception to AD011):**

AD011 states "no NVS state saving" but clarifies this means session state, not settings:
- ✅ Pairing data (peer MAC address) stored in NVS
- ✅ Mode 5 settings (frequency, duty cycle, LED color) stored in NVS
- ❌ Session state (mid-session at 15 minutes) NOT stored in NVS
- Rationale: Settings enable reconnection, state would resume mid-session (unsafe)

---

## JPL Coding Standards Compliance

- ✅ Rule #1: No dynamic memory allocation - Static role state
- ✅ Rule #2: Fixed loop bounds - Bounded by session_timeout
- ✅ Rule #3: No recursion - Linear state transitions
- ✅ Rule #5: Return value checking - BLE function returns checked
- ✅ Rule #6: No unbounded waits - vTaskDelay() for timeout checking
- ✅ Rule #7: Watchdog compliance - Feed during timeout loop
- ✅ Rule #8: Defensive logging - ESP_LOGI for role transitions

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: AD026
Git commit: (phase 1 implementation)

**Status Update (November 11, 2025):**

Single-device fallback behavior superseded by AD028 (Command-and-Control with Synchronized Fallback Architecture). The new architecture provides:

- **Phase 1 (0-2 min):** Continue synchronized bilateral rhythm using last timing reference
- **Phase 2 (2+ min):** Fallback to fixed role assignment (no alternation within device)
- **Reconnection:** Periodic non-blocking attempts every 5 minutes

Role recovery mechanism (survivor becomes server) remains valid and integrated with AD028.

**Coordination with FR001 (Automatic Pairing):**
- Power-on: Random 0-2000ms delay prevents simultaneous server attempts
- Disconnection: 30s timeout gives failed device time to return
- Reconnection: Failed device discovers new server and becomes client
- Symmetric: Works for both server and client failure scenarios

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
