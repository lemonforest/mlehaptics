# 0035: Battery-Based Initial Role Assignment (Phase 1c)

**Date:** 2025-11-14 (Implemented 2025-11-19)
**Phase:** Phase 1c
**Status:** Implemented
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of peer-to-peer device discovery for bilateral stimulation,
facing the need to assign SERVER and CLIENT roles without user configuration,
we decided to implement battery-based role assignment where higher battery device becomes SERVER,
and neglected RSSI-based, MAC-based, manual configuration, or random selection approaches,
to achieve automatic, fair, deterministic role assignment with zero user intervention,
accepting the requirement for battery monitoring (already implemented) and calibration needs.

---

## Problem Statement

When two EMDR devices connect for bilateral stimulation, they must assign SERVER (controller) and CLIENT (follower) roles to coordinate alternating stimulation patterns. Without role assignment, both devices may behave identically (causing simultaneous stimulation instead of therapeutic alternation).

The role assignment mechanism must:
- Work automatically without user configuration (accessibility requirement)
- Produce deterministic outcomes (no RSSI fluctuation issues)
- Distribute roles fairly over multiple sessions
- Handle tie-breaking when devices have identical batteries

---

## Context

**Background:**
- Phase 1b implements peer-to-peer device discovery
- Bilateral stimulation requires coordinated alternation (one motor active while other coasts)
- Users should not need to configure which device is "left" or "right"
- Battery monitoring already runs every 60 seconds for low-voltage protection
- RSSI values fluctuate wildly (±10 dBm), unsuitable for stable role assignment

**Requirements:**
- Zero user configuration (critical for accessibility)
- Deterministic outcome (same conditions = same result)
- Fair distribution over time (users shouldn't always be same role)
- Clear tie-breaker when batteries equal
- Integration with existing battery monitoring

---

## Decision

Implement battery-based initial role assignment where the device with **HIGHER battery level becomes SERVER** (controller) and the device with **LOWER battery level becomes CLIENT** (follower).

### Implementation Phases

**Phase 1b (Connection Type Identification):**
1. Peer discovery via Bilateral Control Service UUID (`...0100`)
2. Both devices advertise and scan simultaneously
3. First to discover peer initiates connection
4. Connection type identified (peer vs mobile app)

**Phase 1c (Battery-Based Role Assignment - IMPLEMENTED):**

**Battery Exchange via BLE Service Data:**
- Battery level broadcast in advertising packet via Service Data (AD Type 0x16)
- Battery Service UUID (0x180F) + battery percentage (0-100%)
- Only broadcast during Bilateral UUID window (0-30s, peer discovery phase)
- `ble_update_bilateral_battery_level()` restarts advertising when battery changes
- Peer extracts battery from scan response BEFORE connection

**Role Assignment Logic:**
```c
// Actual implementation in ble_manager.c:2271-2319
if (peer_state.peer_battery_known) {
    if (local_battery > peer_battery) {
        // Higher battery - initiate connection (SERVER/MASTER)
        ble_connect_to_peer();
    } else if (local_battery < peer_battery) {
        // Lower battery - wait for peer (CLIENT/SLAVE)
        // Don't call ble_connect_to_peer()
    } else {
        // Equal batteries - MAC address tie-breaker
        // Lower MAC address initiates connection
    }
}
```

**Connection Status Display:**
Motor task shows connection type in battery logs (src/motor_task.c:269):
```c
ESP_LOGI(TAG, "Battery: %.2fV [%d%%] | BLE: %s", battery_v, battery_pct,
         ble_get_connection_type_str());
```

Output examples:
- `Battery: 4.16V [96%] | BLE: Peer` ← Peer device connected
- `Battery: 4.10V [89%] | BLE: App` ← Mobile app connected
- `Battery: 3.95V [72%] | BLE: Disconnected` ← No connection

### Phase 1c Implementation Benefits

1. **Faster Role Assignment:** Battery comparison during discovery (no GATT connection needed first)
2. **Eliminates Race Condition:** Higher battery always initiates, deterministic outcome
3. **Standard BLE Practice:** Service Data (0x16) is industry-standard approach
4. **Privacy Acceptable:** Battery level not personal health data, only broadcast during 30s pairing window
5. **Efficient Packet Size:** Only 3 bytes (Battery UUID + percentage), 23 total bytes in scan response

### Race Condition Handling (per AD010)

When both devices simultaneously attempt connection:
- Error `BLE_ERR_ACL_CONN_EXISTS` (523) indicates peer is already connecting to us
- Don't reset `peer_discovered` flag - connection event will arrive momentarily
- Passive device accepts incoming connection, active device's attempt fails gracefully
- Result: One device becomes SERVER (initiator), other becomes CLIENT (acceptor)

---

## Consequences

### Benefits

- ✅ **Zero Configuration:** No user setup required, works out of the box
- ✅ **Fair Role Distribution:** Over time, users naturally alternate roles as battery levels vary
- ✅ **Deterministic:** Clear winner in all cases (battery comparison + MAC tie-breaker)
- ✅ **Accessible:** No UI barriers, works for all users regardless of technical ability
- ✅ **Efficient:** Leverages existing battery monitoring (no additional overhead)
- ✅ **Graceful Degradation:** Tie-breaker ensures role assignment even with identical batteries
- ✅ **Faster Assignment:** Comparison during discovery (no post-connection GATT reads)
- ✅ **Standard Practice:** Service Data is industry-standard BLE approach

### Drawbacks

- Requires accurate battery monitoring (calibration needed for fairness)
- Battery levels may drift during session (role doesn't change mid-session)
- MAC address tie-breaker may favor same device when batteries always equal
- 30-second pairing window constraint for battery broadcast
- Fully charged batteries may show similar percentages (95-98% due to calibration issues)

---

## Options Considered

### Option A: RSSI-Based Selection

**Pros:**
- Uses existing BLE radio data
- No additional measurements needed

**Cons:**
- RSSI fluctuates wildly (±10 dBm)
- Unstable role assignment (changes every connection)
- Environmental factors (walls, interference) affect RSSI

**Selected:** NO
**Rationale:** Instability unacceptable, non-deterministic

### Option B: MAC Address Comparison

**Pros:**
- Deterministic, no fluctuation
- Simple implementation
- No measurement needed

**Cons:**
- Always assigns same device as SERVER (unfair distribution)
- Users would always have same role
- Poor user experience over time

**Selected:** NO
**Rationale:** Unfair role distribution over multiple sessions

### Option C: Manual Configuration

**Pros:**
- User has full control
- Explicit role selection

**Cons:**
- Requires UI (poor user experience)
- Accessibility barrier (vision impairment, cognitive load)
- Users may not understand "SERVER" vs "CLIENT" concepts
- Configuration step every session

**Selected:** NO
**Rationale:** Accessibility barrier, poor UX

### Option D: Random Selection

**Pros:**
- Simple implementation
- Fair over time (statistically)

**Cons:**
- No fairness guarantee for individual users
- Non-deterministic (different result each connection)
- Unpredictable behavior

**Selected:** NO
**Rationale:** Non-deterministic, no per-user fairness guarantee

### Option E: Battery-Based Selection (Selected)

**Pros:**
- Fair over time (battery levels vary naturally)
- Deterministic (same batteries = same result)
- No user configuration needed
- Leverages existing battery monitoring
- Accessible to all users
- MAC address tie-breaker for edge cases

**Cons:**
- Requires battery monitoring (already implemented)
- Needs calibration for accuracy

**Selected:** YES
**Rationale:** Best balance of fairness, determinism, and accessibility

---

## Related Decisions

### Related
- AD010: Race Condition Prevention Strategy - Defines how simultaneous connections are handled
- AD028: Command-and-Control Architecture - Defines SERVER→CLIENT command protocol (Phase 2)
- AD030: Bilateral Control Service - Defines peer communication GATT service
- AD032: BLE Configuration Service Architecture - Defines battery level characteristic

---

## Implementation Notes

### Code References

**Battery Exchange (Phase 1c):**
- `src/ble_manager.c:2256-2319` - Battery-based role assignment in scan callback
- `src/ble_manager.c` - `ble_update_bilateral_battery_level()` - Restart advertising on battery change
- `src/ble_manager.c` - Service Data (0x16) with Battery Service UUID (0x180F)

**Connection Type Display:**
- `src/motor_task.c:269` - Battery logs show connection type
- `src/ble_manager.c` - `ble_get_connection_type_str()` - Returns "Peer", "App", or "Disconnected"
- `src/ble_manager.c` - `ble_is_peer_connected()` - Check peer connection status

**Role Assignment (Phase 1c COMPLETE):**
- `src/ble_manager.c:2271-2319` - Battery comparison logic in scan callback
- Higher battery → initiate connection (SERVER/MASTER)
- Lower battery → wait for connection (CLIENT/SLAVE)
- Equal batteries → MAC address tie-breaker (lower MAC initiates)

### Build Environment

- **Environment Name:** `xiao_esp32c6`
- **Configuration File:** `sdkconfig.xiao_esp32c6`
- **Battery Monitoring:** ADC1_CH2 (GPIO2) via voltage divider (2× 100kΩ resistors)
- **Battery Update Rate:** Every 60 seconds (motor task)

### Testing & Verification

**Phase 1b Testing (November 14, 2025):**
```
11:09:01.749 > Peer discovered: b4:3a:45:89:5c:76
11:09:01.949 > BLE connection established
11:09:01.963 > Peer identified by address match
11:09:01.969 > Peer device connected
11:09:27.452 > Battery: 4.18V [98%] | BLE: Peer  ← Correct identification
```

**Phase 1c Testing Required:**
- Two devices with different battery levels (e.g., 98% vs 85%)
- Verify higher battery device becomes SERVER (initiates connection)
- Verify lower battery device becomes CLIENT (waits for connection)
- Test tie-breaker with identical batteries (MAC address comparison)
- Test role assignment persistence across disconnect/reconnect
- Verify battery-based advertising restart on battery changes

**Known Limitations:**
- Role assignment is ONE-TIME at connection establishment
- Roles do NOT change mid-session (prevents mobile app disconnection from SERVER)
- Only reassign roles on next peer connection/reconnection

---

## Known Issues

### Issue 1: Battery Calibration Needed (Planned Phase 1c)

**Symptom:** Fully charged batteries don't reach 100% (observed ~95-98%)

**Root Causes:**
- **1S2P dual-battery configuration:** Parallel cells may charge unevenly
- **P-MOSFET voltage drop:** High-side switch introduces ~50-100mV drop
- **Battery aging/wear:** Maximum cell voltage decreases over time (4.2V → 4.1V → 4.0V)
- **ADC calibration tolerance:** ESP32-C6 ADC ±2% accuracy

**Impact:**
- Battery percentage inaccurate (user experience issue)
- Affects role assignment fairness (both show 95%, wrong device may become SERVER)

**Proposed Solution (Phase 1c):**

**Hardware:**
- Add 5V pin monitoring via 45kΩ + 100kΩ voltage divider (community-tested design)
- Detect USB connection (5V present = charging)

**Software:**
- Track maximum battery voltage seen during USB connection
- Use tracked maximum as 100% reference (with safety clamps)

**Algorithm:**
```c
// Only update calibration when USB connected AND voltage in valid charging range
if (usb_connected && (voltage >= 4.0V && voltage <= 4.25V)) {
    if (voltage > max_voltage_seen) {
        max_voltage_seen = voltage;  // Save to NVS
    }
}

// Use tracked maximum as 100% reference (with safety clamps)
float v_100 = max_voltage_seen;
if (v_100 < 4.0f) v_100 = 4.2f;    // Reset if severely degraded
if (v_100 > 4.25f) v_100 = 4.25f;  // Prevent overcharge reference

percentage = ((voltage - 3.2V) / (v_100 - 3.2V)) * 100.0f;
```

**Benefits:**
- ✅ Automatic calibration during normal charging (no user intervention)
- ✅ Graceful tracking of battery wear over years
- ✅ Per-device calibration stored in NVS (accounts for manufacturing variations)
- ✅ Protection against invalid calibration (won't allow 3.8V as 100% reference)

**Reference:** [Seeed XIAO Forum - USB Detection via 5V pin](https://forum.seeedstudio.com/t/detecting-usb-or-battery-power/280968)

**Implementation Complexity:** Moderate (requires board rework: 1 wire + 2 resistors per device)

---

## Integration with Other Decisions

### Integration with AD028 (Command-and-Control Architecture)

Battery-based role assignment provides foundation for Phase 2 synchronized bilateral control:
- SERVER device sends timing commands via Bilateral Control Service
- CLIENT device receives and executes commands
- Role can be reassigned if battery levels flip (only on reconnection, not mid-session)

### Integration with AD030 (Bilateral Control Service)

Phase 1b implements peer discovery and connection type identification. Future phases will use:
- `Device Role` characteristic (UUID `4BCAE9BE-9829-4F0A-9E88-267DE5E70105`) to store assigned role
- `Bilateral Command` characteristic (UUID `4BCAE9BE-9829-4F0A-9E88-267DE5E70101`) for SERVER→CLIENT commands
- `Bilateral Battery` characteristic for ongoing battery level comparison

---

## Phase Completion Status

**Phase 1b (COMPLETE - November 14, 2025):**
- ✅ Peer discovery working (both devices discover each other)
- ✅ Connection type identification (`ble_get_connection_type_str()` returns "Peer" vs "App")
- ✅ Bilateral Battery characteristic implemented and updating every 60 seconds
- ✅ Motor task logs show correct connection status
- ✅ Devices successfully reconnect after disconnect

**Phase 1c (COMPLETE - November 19, 2025):**
- ✅ Battery broadcast via Service Data (AD Type 0x16)
- ✅ Battery extraction from scan response BEFORE connection
- ✅ Role assignment logic (higher battery initiates connection)
- ✅ MAC address tie-breaker for equal batteries
- ✅ Connection role-based identification (MASTER/SLAVE)

**Phase 2 (Pending):**
- ⏳ Role-based bilateral control (SERVER sends commands, CLIENT executes)
- ⏳ Synchronized bilateral alternation pattern

---

## Next Steps

**ONE-TIME Role Assignment (Phase 1c COMPLETE):**
1. ✅ Exchange battery levels during discovery (Service Data broadcast)
2. ✅ Compare: local battery vs peer battery
3. ✅ Higher battery → initiate connection (SERVER/MASTER)
4. ✅ Lower battery → wait for connection (CLIENT/SLAVE)
5. ✅ If batteries equal → MAC address tie-breaker
6. ✅ Log role assignment: "Role assigned: SERVER (battery 4.18V > peer 4.16V)"

**DO NOT Implement Ongoing Role Monitoring:**
- Once roles assigned, they are FIXED for this session
- Role changes during active session would disconnect mobile app from SERVER device
- Only reassign roles on next peer connection/reconnection

**Battery Calibration (Phase 1c - Planned):**
- Implement 5V pin monitoring via voltage divider
- Track maximum voltage during USB connection
- Store per-device calibration offset in NVS
- Graceful battery wear tracking over device lifetime

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: AD035 (lines 3428-3664)
Git commit: TBD (migration commit)

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
