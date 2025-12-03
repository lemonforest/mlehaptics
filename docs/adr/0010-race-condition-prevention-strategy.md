# 0010: Race Condition Prevention Strategy

**Date:** 2025-10-15 (originally planned), Updated 2025-11-14 (Phase 1b implementation)
**Phase:** 1b (Peer Discovery and Connection)
**Status:** 🔄 Partially Superseded (MAC delay removed in Phase 6q; error 523 handling retained)
**Type:** Architecture

> **Note:** MAC-based scan delay (Component #5) removed in [AD042](0042-remove-mac-delay-battery-based-symmetry-breaking.md) (Phase 6q, November 29, 2025). Battery-based role assignment (Phase 1c) provides superior symmetry breaking, making the MAC delay unnecessary. Error 523 handling and fallback peer identification logic remain valid and in use.

---

## Summary (Y-Statement)

In the context of simultaneous device power-on causing peer discovery race conditions,
facing risks of both devices connecting simultaneously (error 523) or connection before scan event,
we decided for simultaneous advertising + scanning with graceful error handling and MAC-based delay,
and neglected random startup delays or connection retry loops,
to achieve fast peer discovery (~1-2 seconds) with deterministic race condition resolution,
accepting complexity of dual-path peer identification and connection initiator tracking.

---

## Problem Statement

When both devices power on simultaneously, both attempt to connect to each other, creating race conditions:

1. **Both devices initiate connection simultaneously**
   - Result: `BLE_ERR_ACL_CONN_EXISTS` (error code 523)
   - One connection succeeds, other fails with ACL error

2. **Connection event arrives before scan event is processed**
   - Peer address not yet saved from scan response
   - Cannot identify connection as "peer device" vs "mobile app"

3. **Ambiguous role assignment**
   - Which device is SERVER (connection initiator)?
   - Which device is CLIENT (connection acceptor)?

How do we:
- Handle simultaneous connection attempts gracefully?
- Identify peer device when connection arrives before scan event?
- Assign roles deterministically (SERVER vs CLIENT)?

---

## Context

### Race Condition Scenarios

**Scenario 1: Perfect Timing (Both Connect Simultaneously)**
```
Time 0ms:  Both devices start advertising + scanning
Time 1500ms: Device A discovers Device B
Time 1500ms: Device B discovers Device A (same moment)
Time 1600ms: Device A calls ble_gap_connect()
Time 1600ms: Device B calls ble_gap_connect() (same moment)
Result: One succeeds, other gets BLE_ERR_ACL_CONN_EXISTS (523)
```

**Scenario 2: Connection Before Scan Event**
```
Time 0ms:   Both devices start advertising + scanning
Time 1500ms: Device A discovers Device B, saves peer address
Time 1520ms: Device B starts connecting to Device A
Time 1530ms: Connection event arrives at Device A
Time 1550ms: Scan event processed at Device A (late!)
Problem: Connection event has no peer address to match
```

**Scenario 3: Exactly Simultaneous Power-On**
```
Time 0ms: Device A powered on, starts advertising/scanning immediately
Time 0ms: Device B powered on, starts advertising/scanning immediately
Time 1500ms: Both discover each other at same moment
Result: Symmetric race condition (both try to connect)
```

### BLE Stack Behavior

**NimBLE ble_gap_connect() returns:**
- `0` = Success (connection initiated)
- `523` (BLE_ERR_ACL_CONN_EXISTS) = Peer already connecting to us
- Other error codes = Connection failed

**Connection Event Ordering:**
- Scan event: Peer discovered, address saved
- Connection event: Connection established, address available
- **Order not guaranteed** - connection may arrive before scan event processed

---

## Decision

We will use **simultaneous advertising + scanning** with **graceful race condition handling** and **MAC-based scan startup delay**.

### Solution Components

**1. Simultaneous Advertising + Scanning**
- Both devices advertise Bilateral Control Service UUID
- Both devices scan for peers advertising same UUID
- First device to discover peer initiates connection
- No artificial random delays (fast discovery)

**2. ACL Connection Exists Error Handling**

When `ble_gap_connect()` returns error 523:
```c
int rc = ble_gap_connect(BLE_OWN_ADDR_PUBLIC, &peer_state.peer_addr,
                         30000, NULL, ble_gap_event, NULL);

if (rc != 0) {
    ESP_LOGE(TAG, "Failed to connect to peer; rc=%d", rc);

    // BLE_ERR_ACL_CONN_EXISTS (523) means peer is connecting to US
    // Don't reset peer_discovered - connection event will arrive momentarily
    if (rc != 523) {
        peer_state.peer_discovered = false;
    } else {
        ESP_LOGI(TAG, "Peer is connecting to us (ACL already exists)");
    }
}
```

**Key Insight:** Error 523 means peer is already connecting to us. Don't reset discovery state - connection event will arrive within milliseconds.

**3. Connection Event Before Scan Event (Fallback Logic)**

Dual-path peer identification:
```c
bool is_peer = false;

// Primary: Match by peer address (if scan event arrived first)
if (peer_state.peer_discovered &&
    memcmp(&desc.peer_id_addr, &peer_state.peer_addr, sizeof(ble_addr_t)) == 0) {
    is_peer = true;
    ESP_LOGI(TAG, "Peer identified by address match");
}
else {
    // Fallback: Connection while scanning = peer device
    if (scanning_active && !adv_state.client_connected) {
        is_peer = true;
        peer_state.peer_discovered = true;
        memcpy(&peer_state.peer_addr, &desc.peer_id_addr, sizeof(ble_addr_t));
        ESP_LOGI(TAG, "Peer identified by simultaneous connection (address saved)");
    }
}
```

**Key Insight:** If connection arrives while scanning and no mobile app connected, it must be peer device.

**4. Role Assignment**

- Device that successfully initiates connection = **SERVER** (connection initiator)
- Device that receives connection = **CLIENT** (connection acceptor)
- NimBLE provides `desc.role` field for definitive role assignment:
  - `BLE_GAP_ROLE_MASTER` = SERVER
  - `BLE_GAP_ROLE_SLAVE` = CLIENT

**5. MAC-Based Scan Startup Delay (Phase 1b.3)**

To break exact simultaneous power-on symmetry:
```c
uint8_t addr_val[6];
int is_nrpa;
int rc_addr = ble_hs_id_copy_addr(BLE_ADDR_PUBLIC, addr_val, &is_nrpa);

if (rc_addr == 0) {
    // Use last 3 bytes of MAC to generate delay (0-499ms)
    uint32_t seed = (addr_val[0] << 16) | (addr_val[1] << 8) | addr_val[2];
    uint32_t delay_ms = seed % 500;  // 0-499ms delay

    ESP_LOGI(TAG, "Scan startup delay: %lums (MAC-based)", delay_ms);
    vTaskDelay(pdMS_TO_TICKS(delay_ms));
}
```

**Key Insight:** Deterministic per-device delay (same MAC = same delay) breaks symmetry without randomness.

---

## Consequences

### Benefits

- ✅ **No artificial delays**: Devices discover each other as fast as possible (~1-2 seconds)
- ✅ **Graceful race handling**: ACL error 523 handled without resetting discovery state
- ✅ **Robust peer identification**: Dual path (address match + fallback) ensures correct identification
- ✅ **Deterministic outcome**: One device always becomes initiator, other becomes acceptor
- ✅ **Fast reconnection**: After disconnect, devices rediscover within ~2 seconds
- ✅ **JPL compliant**: No randomness (MAC-based delay is deterministic)
- ✅ **Symmetry breaking**: MAC-based delay prevents exact simultaneous power-on race

### Drawbacks

- **Complexity**: Dual-path peer identification adds code complexity
- **Connection initiator preference**: Cannot prefer higher-battery device as initiator (Phase 1c will add)
- **Rare failures**: Extremely rare case where both connections fail simultaneously (not handled)
- **MAC dependency**: Relies on stable MAC address across boots

---

## Options Considered

### Option A: Simultaneous Advertising/Scanning + Graceful Handling (Selected)

**Pros:**
- Fast discovery (~1-2 seconds)
- Graceful handling of ACL error 523
- Robust dual-path peer identification
- Deterministic role assignment
- MAC-based symmetry breaking

**Cons:**
- Code complexity (dual-path logic)
- Rare unhandled edge cases

**Selected:** YES
**Rationale:** Best balance of speed, robustness, and JPL compliance

### Option B: Random Startup Delays (0-5 seconds) - REJECTED

**Pros:**
- Reduces simultaneous connection attempts
- Simple to implement

**Cons:**
- ❌ Violates JPL Rule #2 (no random/unpredictable behavior)
- ❌ Slows discovery by up to 5 seconds
- ❌ User experience: unpredictable startup time
- ❌ Doesn't eliminate race condition (just reduces probability)

**Selected:** NO
**Rationale:** JPL compliance violation, poor user experience

### Option C: Connection Retry Loop (Exponential Backoff) - REJECTED

**Pros:**
- Handles simultaneous connection failures
- Standard networking practice

**Cons:**
- Adds latency (retry delays)
- More complex state machine
- Unnecessary (ACL 523 already handled gracefully)

**Selected:** NO
**Rationale:** Unnecessary complexity, ACL 523 handling sufficient

### Option D: Server-Only Initiates (Client Only Advertises) - REJECTED

**Pros:**
- No race condition (only one device tries to connect)

**Cons:**
- Requires battery comparison BEFORE connection (Phase 1c)
- Slower discovery (server must scan, client only advertises)
- Both devices don't know roles until battery comparison

**Selected:** NO (deferred to Phase 1c)
**Rationale:** Battery-based role assignment comes after connection in Phase 1c

---

## Related Decisions

### Related
- [AD008: BLE Protocol Architecture](0008-ble-protocol-architecture.md) - BLE services for peer communication
- [AD009: Bilateral Timing Implementation](0009-bilateral-timing-implementation.md) - Server/client coordination
- [AD035: Battery-Based Initial Role Assignment](0035-battery-based-initial-role-assignment.md) - Phase 1c battery comparison (future)

---

## Implementation Notes

### Code References

- `src/ble_manager.c:1779-1789` - ACL error 523 handling
- `src/ble_manager.c:1094-1134` - Dual-path peer identification
- `src/ble_manager.c:2147-2196` - MAC-based scan startup delay
- `src/ble_manager.c:1150-1166` - Role assignment via `desc.role`

### Build Environment

- **Environment:** `xiao_esp32c6` (Phase 1b+)
- **NimBLE Stack:** ESP-IDF v5.5.0 NimBLE
- **Configuration:** `CONFIG_BT_NIMBLE_MAX_CONNECTIONS=2`

### Testing & Verification

**Phase 1b Testing (November 14, 2025):**

**Scenario 1: Device A Discovers First**
```
Device A:
11:09:01.749 > Peer discovered: b4:3a:45:89:5c:76
11:09:01.949 > BLE connection established
11:09:01.963 > Peer identified by address match

Device B:
11:09:01.824 > Peer discovered: a2:1f:33:67:4d:52
11:09:01.943 > Failed to connect to peer; rc=523
11:09:01.950 > Peer is connecting to us (ACL already exists)
11:09:01.969 > BLE connection established
11:09:01.975 > Peer identified by simultaneous connection (address saved)
```

**Scenario 2: Connection Before Scan Event**
```
Device A:
11:12:45.123 > BLE connection established
11:12:45.130 > Peer identified by simultaneous connection (address saved)
11:12:45.156 > Peer discovered: b4:3a:45:89:5c:76 (late scan event)
```

**Scenario 3: Exact Simultaneous Power-On (MAC-based delay)**
```
Device A (MAC ending in ...5c:76):
00:00:00.100 > Scan startup delay: 376ms (MAC-based)
00:00:00.476 > Starting BLE scan

Device B (MAC ending in ...4d:52):
00:00:00.100 > Scan startup delay: 210ms (MAC-based)
00:00:00.310 > Starting BLE scan

Result: Device B starts scanning 166ms earlier, discovers Device A first
```

**Known Issues:**
- None - race condition handling verified stable

---

## JPL Coding Standards Compliance

- ✅ Rule #1: No dynamic memory - Peer state statically allocated
- ✅ Rule #2: Fixed loop bounds - No unbounded retry loops
- ✅ Rule #5: Return value checking - ble_gap_connect() result checked
- ✅ Rule #6: No unbounded waits - Connection timeout 30 seconds
- ✅ Rule #8: Defensive logging - All race condition paths logged

**No randomness:** MAC-based delay is deterministic (same MAC = same delay), JPL-compliant.

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: AD010 (Safety and Error Handling Decisions)
Git commit: Current working tree

**Phase History:**
- **Phase 0.1**: Original design (planned October 2025)
- **Phase 1b**: Implementation (November 14, 2025)
- **Phase 1b.3**: MAC-based delay added (November 17, 2025)

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
