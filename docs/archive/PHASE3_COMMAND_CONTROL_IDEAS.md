# Phase 3: Command and Control - Design Ideas

**Date:** 2025-11-19
**Status:** Planning Phase
**Related AD:** AD028 (Command-and-Control Protocol)

---

## Overview

Phase 3 will implement synchronized mode changes between peer devices. When one device changes mode (via button press or BLE), the peer device should automatically switch to the same mode to maintain synchronized bilateral stimulation.

**Current Status (Phase 2):**
- Time synchronization works ✅
- Bilateral alternation works (frequency/2 offset) ✅
- Devices maintain independent modes ❌
- Button press only affects local device ❌

**Phase 3 Goal:**
- Mode changes propagate to peer device automatically
- Both devices always run the same mode
- Prevent recursive mode change loops
- Handle edge cases (disconnect, conflicting changes, etc.)

---

## User's Initial Ideas

From Phase 2 development session (November 19, 2025):

> "What we'd need to do is, when the mode is changed on one by a button press, we need to command the other device to switch to the same mode. It's possible that we can do this with subscribe/notify. We might need a way to keep this from recursively triggering by checking current mode vs requested mode."

**Key Concepts:**
1. **BLE Subscribe/Notify** - Use existing BLE infrastructure for mode propagation
2. **Recursion Prevention** - Check `current_mode != requested_mode` before propagating
3. **Bilateral Synchronization** - Both devices must run identical modes for therapeutic effectiveness

---

## Architecture Options

### Option 1: Master/Slave (Role-Based)

**Concept:** Only SERVER can initiate mode changes, CLIENT always follows

**Pros:**
- Simple, no conflict resolution needed
- Clear authority hierarchy
- Easy to implement

**Cons:**
- CLIENT users cannot change mode (poor UX)
- Asymmetric experience between devices
- Doesn't leverage bilateral alternation symmetry

**Verdict:** ❌ Poor user experience

---

### Option 2: Peer Notification (Symmetric)

**Concept:** Either device can initiate mode change, notifies peer via BLE characteristic

**Implementation:**
```c
// Bilateral Control Service (AD030)
// Add new characteristic: MODE_SYNC (UUID: ...01XX)

typedef struct {
    uint8_t requested_mode;  // 0-4 (MODE_SLEEP to MODE_CUSTOM)
    uint32_t timestamp_ms;   // Local timestamp of mode change
} mode_sync_message_t;

// In button_task.c or motor_task.c:
void propagate_mode_change(mode_t new_mode) {
    // 1. Check if mode actually changed
    if (new_mode == current_mode) {
        return;  // Prevent recursion
    }

    // 2. Apply mode locally
    current_mode = new_mode;
    calculate_mode_timing();

    // 3. Notify peer if connected
    if (ble_is_peer_connected()) {
        mode_sync_message_t msg = {
            .requested_mode = new_mode,
            .timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000)
        };
        ble_notify_mode_sync(&msg);
    }
}

// In ble_manager.c (MODE_SYNC write callback):
int handle_mode_sync_write(struct os_mbuf *om) {
    mode_sync_message_t msg;
    os_mbuf_copydata(om, 0, sizeof(msg), &msg);

    // Forward to motor_task via message queue
    task_message_t task_msg = {
        .type = MSG_MODE_SYNC,
        .data.mode = msg.requested_mode
    };
    xQueueSend(ble_to_motor_queue, &task_msg, 0);

    return 0;
}
```

**Recursion Prevention:**
- Local mode change: `if (new_mode == current_mode) return;`
- BLE write triggers same check in motor_task
- No infinite loop possible

**Pros:**
- ✅ Symmetric user experience
- ✅ Simple recursion prevention
- ✅ Uses existing BLE infrastructure
- ✅ Low latency (BLE notify is fast)

**Cons:**
- Race condition if both users press button simultaneously
- Need conflict resolution strategy

**Verdict:** ⭐ **RECOMMENDED** (with conflict resolution)

---

### Option 3: Timestamp-Based Conflict Resolution

**Enhancement to Option 2:** Use synchronized time (Phase 2) to resolve conflicts

**Conflict Scenario:**
1. Device A changes to Mode 1 at T=1000ms
2. Device B changes to Mode 2 at T=1005ms
3. Both devices receive peer notification

**Resolution Strategy:**
```c
void handle_mode_sync_message(mode_sync_message_t *msg) {
    // Get synchronized time
    uint64_t current_time_us = time_sync_get_time();
    uint32_t current_time_ms = (uint32_t)(current_time_us / 1000);

    // Check if mode actually changed
    if (msg->requested_mode == current_mode) {
        return;  // Already in this mode
    }

    // Conflict detection: Did we recently change mode too?
    const uint32_t CONFLICT_WINDOW_MS = 500;  // 500ms window
    uint32_t time_since_local_change = current_time_ms - last_local_mode_change_ms;

    if (time_since_local_change < CONFLICT_WINDOW_MS) {
        // Conflict detected! Use timestamp to decide winner
        if (msg->timestamp_ms > last_local_mode_change_ms) {
            // Peer timestamp is newer, accept their mode
            ESP_LOGI(TAG, "Mode conflict: accepting peer mode %d (newer)", msg->requested_mode);
            current_mode = msg->requested_mode;
            calculate_mode_timing();
        } else {
            // Our timestamp is newer or equal, ignore peer
            ESP_LOGI(TAG, "Mode conflict: keeping local mode %d (newer)", current_mode);
            return;
        }
    } else {
        // No conflict, normal mode sync
        ESP_LOGI(TAG, "Mode sync: switching to mode %d", msg->requested_mode);
        current_mode = msg->requested_mode;
        calculate_mode_timing();
    }
}
```

**Benefits:**
- ✅ Deterministic conflict resolution
- ✅ Uses Phase 2 time sync infrastructure
- ✅ Both devices converge to same mode
- ✅ Newest mode change always wins

**Drawbacks:**
- Requires accurate time sync (depends on Phase 2 quality)
- 500ms conflict window might be too large (adjust based on testing)

**Verdict:** ⭐⭐ **BEST OPTION** (combines Option 2 + conflict resolution)

---

## Implementation Checklist

### 1. BLE Characteristics (ble_manager.c)

- [ ] Add MODE_SYNC characteristic to Bilateral Control Service (UUID: ...01XX)
- [ ] Implement write callback: `bilateral_mode_sync_write_cb()`
- [ ] Implement notify function: `ble_notify_mode_sync()`
- [ ] Add mode sync message struct to `ble_manager.h`

### 2. Message Queue Integration (motor_task.c)

- [ ] Add `MSG_MODE_SYNC` message type to `task_message_t` enum
- [ ] Handle `MSG_MODE_SYNC` in motor_task CHECK_MESSAGES state
- [ ] Implement conflict detection logic with timestamp comparison
- [ ] Track `last_local_mode_change_ms` variable

### 3. Button Task Integration (button_task.c)

- [ ] Call `ble_notify_mode_sync()` after local mode change
- [ ] Include synchronized timestamp in notification
- [ ] Ensure recursion prevention (`if (new_mode == current_mode)`)

### 4. Testing

- [ ] Test simultaneous button presses on both devices
- [ ] Verify conflict resolution (newest mode wins)
- [ ] Test mode sync with peer disconnect/reconnect
- [ ] Verify no infinite notification loops
- [ ] Test all 5 modes (MODE_1 through MODE_CUSTOM)

---

## Edge Cases to Consider

### 1. Peer Disconnect During Mode Change

**Scenario:** Device A changes mode, sends notification, peer disconnects before receiving

**Solution:**
- Store last known peer mode in NVS
- On reconnect, check if modes match
- If mismatch, use timestamp or SERVER role to decide

### 2. Mode Change During Deep Sleep Wake

**Scenario:** Device wakes from sleep, peer is already running different mode

**Solution:**
- Query peer mode on connection (read MODE_SYNC characteristic)
- Sync to peer mode if different
- Log discrepancy for debugging

### 3. Custom Mode with Different Parameters

**Scenario:** Both devices in MODE_CUSTOM but with different frequency/duty cycle

**Solution:**
- MODE_SYNC message must include custom parameters:
```c
typedef struct {
    uint8_t requested_mode;
    uint32_t timestamp_ms;
    uint16_t custom_frequency_cHz;  // Only valid if mode == MODE_CUSTOM
    uint8_t custom_duty_pct;        // Only valid if mode == MODE_CUSTOM
} mode_sync_message_t;
```

### 4. Mobile App Mode Change

**Scenario:** User changes mode via nRF Connect app on one device

**Solution:**
- Configuration Service mode write should also trigger `ble_notify_mode_sync()`
- Peer device receives notification and syncs
- Works identically to button press

---

## Phase 3 Architecture Diagram

```
Device A (SERVER)                          Device B (CLIENT)
┌─────────────────┐                        ┌─────────────────┐
│  Button Press   │                        │                 │
│      Mode 1     │                        │                 │
└────────┬────────┘                        └─────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  button_task.c              │
│  - Set local mode           │
│  - Calculate timing         │
│  - Send MSG_MODE_CHANGE     │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐            ┌─────────────────────────────┐
│  motor_task.c               │            │  motor_task.c               │
│  - Apply new mode           │            │  - Receive MSG_MODE_SYNC    │
│  - Notify peer via BLE  ────┼───────────►│  - Check timestamp          │
│    (mode_sync_message_t)    │   BLE      │  - Apply new mode           │
└─────────────────────────────┘  Notify    │  - Calculate timing         │
                                            └─────────────────────────────┘
                                                     │
                                                     ▼
                                            ┌─────────────────┐
                                            │  Motor Running  │
                                            │     Mode 1      │
                                            └─────────────────┘

Result: Both devices synchronized to Mode 1
```

---

## Open Questions

1. **Conflict window duration:** Is 500ms appropriate or should it be shorter (e.g., 200ms)?
2. **Mobile app integration:** Should mobile app show "mode sync in progress" indicator?
3. **NVS persistence:** Should last synced mode be saved to NVS for post-reboot recovery?
4. **LED feedback:** Should devices flash different colors during conflict resolution?
5. **Graceful degradation:** If time sync quality is poor (<70%), disable timestamp-based conflict resolution?

---

## References

- **AD028:** Command-and-Control Protocol (Phase 3 overview)
- **AD030:** Bilateral Control Service UUID (BLE service for peer communication)
- **AD039:** Time Synchronization Protocol (Phase 2, required for conflict resolution)
- **motor_task.c:** Current mode switching implementation
- **ble_manager.c:** Bilateral Control Service implementation

---

## Implementation Timeline (Suggested)

**Phase 3a - Basic Mode Sync (1-2 days):**
- Implement MODE_SYNC characteristic
- Simple recursion prevention (`current_mode != requested_mode`)
- Test with sequential button presses (no conflicts)

**Phase 3b - Conflict Resolution (1-2 days):**
- Add timestamp-based conflict resolution
- Test simultaneous button presses
- Verify convergence to consistent state

**Phase 3c - Edge Cases (1-2 days):**
- Handle disconnect/reconnect scenarios
- Custom mode parameter sync
- Mobile app integration testing
- NVS persistence for mode recovery

**Phase 3d - Polish (1 day):**
- LED feedback for sync status
- Comprehensive logging
- Documentation updates
- Hardware validation

**Total Estimated Time:** 5-7 days

---

## Notes

- This document captures initial design ideas from Phase 2 development session
- Implementation details may change based on testing and user feedback
- Conflict resolution strategy is critical for good UX (avoid "mode wars")
- Time sync quality (Phase 2) directly impacts conflict resolution reliability
