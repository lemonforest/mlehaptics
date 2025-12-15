# 0028: Command-and-Control with Synchronized Fallback Architecture

**Date:** 2025-11-11
**Phase:** 1b
**Status:** Accepted (Motor Control) | Superseded by AD041 (Bilateral Alternation)
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of dual-device bilateral stimulation with BLE coordination,
facing time-sync drift causing safety violations vs. immediate fallback poor UX,
we decided for command-and-control with synchronized fallback (2-minute grace period),
and neglected time-synchronized independent operation or immediate fallback,
to achieve guaranteed non-overlapping stimulation with seamless brief disconnection handling,
accepting Phase 1 (0-2 min) synchronized fallback then Phase 2 (2+ min) fixed role fallback.

---

## Problem Statement

Initial dual-device architecture (AD026) specified immediate fallback to single-device mode on BLE disconnection. User requested analysis of time-synchronized independent operation as an alternative. Mathematical analysis revealed time-sync would cause safety violations (overlapping stimulation) after 15-20 minutes due to crystal drift and FreeRTOS jitter.

**Crystal Drift Analysis:**
- ESP32-C6 crystal: ±10 PPM typical tolerance
- FreeRTOS jitter: ±100ms typical per task cycle
- Over 20 minutes: ±1944ms accumulated drift
- Result: Overlapping stimulation violates FR002 safety requirement

---

## Context

**Safety Requirements:**
- FR002: Non-overlapping bilateral stimulation (devices must not stimulate simultaneously)
- Therapeutic efficacy: Bilateral alternation required for EMDR
- Session duration: 20-90 minutes (long enough for drift to matter)

**User Experience Requirements:**
- Brief BLE disconnections (< 2 min) shouldn't interrupt therapy
- Permanent failures (battery death, 2.4GHz interference) need graceful degradation
- No manual intervention during session

**Technical Constraints:**
- BLE latency: 50-100ms (therapeutically insignificant)
- Crystal drift: ±10 PPM (±1944ms over 20 minutes)
- FreeRTOS jitter: ±100ms per task cycle
- Human perception threshold: 100-200ms timing differences imperceptible

---

## Decision

We will adopt Command-and-Control with Synchronized Fallback architecture for dual-device bilateral stimulation.

**Architecture:**

```
Normal Operation (BLE Connected):
Server Device                Client Device
Check messages →             Receive BLE command
Send BLE "FORWARD" →         Process command
Forward active (125ms)       Wait for next command
Send BLE "COAST" →          Process command
Coast (375ms)               Coast (375ms)
Send BLE "REVERSE" →        Process command
Coast continues             Reverse active (125ms)
                           Coast (375ms)

Synchronized Fallback Phase 1 (0-2 minutes after disconnect):
Server Device                Client Device
Detect BLE loss →           Detect BLE loss
Continue rhythm (SERVER)    Continue rhythm (CLIENT)
Forward → Coast →           Coast → Reverse →
Use last timing ref         Use last timing ref
                           ↓
Fallback Phase 2 (2+ minutes, remainder of session):
Server Device                Client Device
Forward only (125ms on)     Reverse only (125ms on)
Coast (375ms)               Coast (375ms)
Repeat assigned role        Repeat assigned role
No alternation              No alternation
Reconnect attempt/5min      Reconnect attempt/5min
                           ↓
Session Complete (60-90 minutes):
Both devices → Deep Sleep
```

**Key Features:**

1. **Command-and-Control During Normal Operation:**
   - Server controls all timing decisions
   - Client executes commands immediately upon receipt
   - Guarantees non-overlapping stimulation (FR002 safety requirement)
   - 50-100ms BLE latency is therapeutically insignificant

2. **Synchronized Fallback Phase 1 (0-2 minutes):**
   - Continue established bilateral rhythm using last timing reference
   - Maximum drift over 2 minutes: ±1.2ms (negligible)
   - Provides seamless therapy during brief disconnections
   - Both devices maintain alternating pattern

3. **Fallback Phase 2 (2+ minutes to session end):**
   - Server continues forward-only stimulation (assigned role)
   - Client continues reverse-only stimulation (assigned role)
   - No alternation within each device - just repeat assigned role
   - Handles both battery death and 2.4GHz interference scenarios
   - Non-blocking reconnection attempt every 5 minutes
   - If reconnection succeeds, resume command-and-control seamlessly

4. **Session Completion:**
   - Both devices enter deep sleep after 60-90 minute session
   - Ensures predictable battery management
   - Clear session boundaries for therapeutic practice

**Implementation:**

```c
// Fallback state management
typedef struct {
    uint32_t disconnect_time;        // When BLE disconnected
    uint32_t last_command_time;      // Timestamp of last server command
    uint32_t last_reconnect_attempt; // Last reconnection attempt
    uint16_t established_cycle_ms;   // Current cycle period (e.g., 500ms)
    uint16_t established_duty_ms;    // Current duty cycle (e.g., 125ms)
    motor_role_t fallback_role;      // MOTOR_ROLE_SERVER or MOTOR_ROLE_CLIENT
    bool phase1_sync;                 // True during 2-minute sync phase
} fallback_state_t;

// Fallback phase management
uint32_t now = xTaskGetTickCount();
uint32_t disconnect_duration = now - fallback_state.disconnect_time;

if (disconnect_duration < pdMS_TO_TICKS(120000)) {
    // Phase 1: Maintain synchronized bilateral pattern
    continue_bilateral_rhythm();
} else {
    // Phase 2: Continue in assigned role only
    fallback_state.phase1_sync = false;
    if (fallback_state.fallback_role == MOTOR_ROLE_SERVER) {
        motor_forward_only();  // No reverse
    } else {
        motor_reverse_only();  // No forward
    }

    // Periodic reconnection attempts (non-blocking)
    if ((now - fallback_state.last_reconnect_attempt) > pdMS_TO_TICKS(300000)) {
        ble_attempt_reconnect_nonblocking();
        fallback_state.last_reconnect_attempt = now;
    }
}
```

---

## Consequences

### Benefits

- **No overlap risk:** Command-and-control guarantees sequential operation
- **Minimal drift during fallback:** ±1.2ms over 2 minutes is imperceptible
- **Automatic recovery:** Falls back to safe single-device mode after 2 minutes
- **Seamless brief disconnections:** 0-2 minute window handles transient issues
- **User notification:** LED/haptic feedback indicates mode changes
- **Therapeutic continuity:** Session continues despite connection issues
- **Safety guaranteed:** FR002 non-overlapping requirement preserved

### Drawbacks

- **Complex state machine:** Three operational modes (normal, phase 1, phase 2)
- **2-minute grace period:** Accumulates small drift during Phase 1
- **Reduced bilateral alternation:** Phase 2 loses alternation (acceptable for emergency fallback)
- **Periodic reconnection overhead:** 5-minute attempts consume power

---

## Options Considered

### Option A: Time-Synchronized Independent Operation

**Pros:**
- No command-and-control complexity
- Devices operate independently

**Cons:**
- Crystal drift (±10 PPM) + FreeRTOS jitter = ±1944ms over 20 minutes
- Would cause overlapping stimulation (safety violation)
- Complex NTP-style time sync adds unnecessary complexity
- Drift correction requires continuous BLE communication

**Selected:** NO
**Rationale:** Mathematical analysis proves unsafe after 15-20 minutes (violates FR002)

### Option B: Immediate Fallback (AD026)

**Pros:**
- Simple state machine
- No drift accumulation

**Cons:**
- Interrupts therapy on any BLE glitch
- Poor user experience during brief disconnections
- No grace period for transient issues

**Selected:** NO
**Rationale:** User experience testing revealed brief disconnections common, immediate fallback too aggressive

### Option C: Command-and-Control with Synchronized Fallback (CHOSEN)

**Pros:**
- Guaranteed non-overlapping (command-driven)
- 2-minute grace period handles transient disconnections
- Minimal drift during Phase 1 (±1.2ms)
- Automatic recovery to safe fallback mode
- Periodic reconnection attempts

**Cons:**
- More complex state machine
- Phase 2 loses bilateral alternation (acceptable emergency fallback)

**Selected:** YES
**Rationale:** Best balance of safety, user experience, and therapeutic continuity

---

## Related Decisions

### Supersedes
- **AD026: BLE Automatic Role Recovery** - Immediate fallback behavior replaced with synchronized fallback phases

### Superseded By
- **[AD045: Synchronized Independent Operation](0045-synchronized-independent-bilateral-operation.md)** - Motor control uses epoch-based calculation without corrections. Both devices calculate transitions independently from synchronized motor_epoch (like Bluetooth audio). Command-and-control retained for mode changes (two-phase commit protocol) and emergency features only.

### Related
- **AD029: Relaxed Timing Specification** - ±100ms tolerance enables command-and-control architecture
- **AD030: BLE Bilateral Control Service** - Bilateral Command characteristic implements command-and-control
- **AD035: Battery-Based Role Assignment** - Determines SERVER vs CLIENT role for fallback behavior

---

## Implementation Notes

### Code References

- **Motor Task:** `src/motor_task.c` (fallback state machine)
- **BLE Task:** `src/ble_task.c` (command transmission/reception)
- **BLE Manager:** `src/ble_manager.c` (Bilateral Command characteristic)

### Build Environment

- **Environment Name:** `xiao_esp32c6`
- **Configuration File:** `sdkconfig.xiao_esp32c6`
- **Phase:** Phase 1b foundation, Phase 2 full implementation

### Testing & Verification

**Phase 1b Implementation Status (November 14, 2025):**

✅ **Peer Discovery** (Implemented):
- Both devices advertise Bilateral Control Service UUID
- Both devices scan for peer advertising same service
- First device to discover peer initiates connection
- Race condition handled per AD010 (ACL error 523 gracefully handled)
- Connection type identification (`ble_get_connection_type_str()` returns "Peer" vs "App")

✅ **Battery Exchange** (Implemented):
- Bilateral Battery characteristic updating every 60 seconds
- `ble_update_bilateral_battery_level()` called by motor_task
- Motor task battery logs show connection status: `Battery: 4.18V [98%] | BLE: Peer`

⏳ **Role Assignment** (Phase 1c - Pending):
- Battery-based role assignment logic (see AD035)
- Higher battery device becomes SERVER (controller)
- Lower battery device becomes CLIENT (follower)
- Tie-breaker: Connection initiator becomes SERVER if batteries equal

⏳ **Command-and-Control** (Phase 2 - Pending):
- Bilateral Command characteristic for SERVER→CLIENT commands
- Device Role characteristic to store assigned role
- Command types: START/STOP/SYNC/MODE_CHANGE/EMERGENCY/PATTERN
- Normal operation with BLE commands as described above

⏳ **Synchronized Fallback** (Phase 2 - Pending):
- Fallback Phase 1 (0-2 minutes): Continue bilateral rhythm
- Fallback Phase 2 (2+ minutes): Fixed role assignment (no alternation)
- Periodic reconnection attempts every 5 minutes
- Seamless resume of command-and-control on reconnection

**Testing Evidence (November 14, 2025):**

Peer discovery working reliably with ~1-2 second connection time:
```
11:09:01.749 > Peer discovered: b4:3a:45:89:5c:76
11:09:01.949 > BLE connection established
11:09:01.963 > Peer identified by address match
11:09:27.452 > Battery: 4.18V [98%] | BLE: Peer  ← Correct identification
```

Devices successfully reconnect after disconnect.

---

## JPL Coding Standards Compliance

- ✅ Rule #1: No dynamic memory allocation - Static fallback state structure
- ✅ Rule #2: Fixed loop bounds - Phase transitions have deterministic timing
- ✅ Rule #3: No recursion - Linear state machine transitions
- ✅ Rule #5: Return value checking - BLE command transmission checked
- ✅ Rule #6: No unbounded waits - vTaskDelay() for all timing
- ✅ Rule #7: Watchdog compliance - Feed during all phases
- ✅ Rule #8: Defensive logging - ESP_LOGI for phase transitions

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: AD028
Git commit: (phase 1b implementation)

**Safety Analysis:**

- **No Overlap Risk:** Command-and-control guarantees sequential operation
- **Minimal Drift During Fallback:** ±1.2ms over 2 minutes is imperceptible
- **Automatic Recovery:** Falls back to safe single-device mode after 2 minutes
- **User Notification:** LED/haptic feedback indicates mode changes

**Integration with AD035 (Battery-Based Role Assignment):**

Phase 1b provides connection establishment and peer identification. Phase 1c will add role assignment based on battery comparison. Phase 2 will implement the full command-and-control architecture with synchronized fallback as described above.

---

---

## Phase 6k Update (November 28, 2025)

**Status Change:** Motor control architecture superseded by AD041 (Predictive Bilateral Synchronization).

**What Changed:**
- **Motor Control:** Now uses AD041 (predictive sync with drift-rate compensation) instead of command-and-control
- **Emergency Features:** Still uses command-and-control (shutdown, mode sync)
- **Rationale:** AD041 validates Option A by solving the drift problem that caused rejection

**Coexistence:**
```
Motor Control:         AD041 (Predictive Sync) ← Changed from AD028
Emergency Shutdown:    AD028 (Command-and-Control) ← Retained
Mode Sync:             AD028 (Command-and-Control) ← Retained
Session Management:    AD041 (Predictive Sync) ← Changed from AD028
```

**Result:** AD028 Option A (rejected due to drift) is now validated and implemented via AD041's drift-rate prediction. Command-and-control architecture retained for critical safety features only.

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-28
