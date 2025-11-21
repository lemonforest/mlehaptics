# 0011: Emergency Shutdown Protocol

**Date:** 2025-11-08
**Phase:** 0.4
**Status:** Accepted
**Type:** Architecture | Security

---

## Summary (Y-Statement)

In the context of safety-critical bilateral stimulation device operation,
facing the need for immediate motor shutdown and coordinated dual-device response,
we decided for fire-and-forget coordinated shutdown with immediate local motor coast,
and neglected waiting for peer acknowledgment,
to achieve sub-100ms emergency shutdown response time,
accepting that peer device may not receive shutdown command if powered off or disconnected.

---

## Problem Statement

A therapeutic bilateral stimulation device requires immediate emergency shutdown capability when a user holds the button for 5 seconds. The shutdown must:
- Stop motors immediately (within 50ms)
- Coordinate shutdown with paired device when possible
- Never block waiting for peer response
- Preserve pairing data for reconnection
- Maintain safety-first approach

---

## Context

**Safety Requirements:**
- 5-second button hold triggers emergency stop
- Immediate motor coast (GPIO write, no delay)
- Dual-device coordination (both devices should stop)
- No dependency on BLE connection state

**Technical Constraints:**
- ESP32-C6 GPIO write latency: ~50ns
- BLE message transmission: Variable (50-500ms)
- Peer device may be powered off or out of range
- ISR-based button monitoring for fastest response

**User Experience:**
- Clear indication of emergency shutdown (purple LED blink)
- Consistent behavior regardless of peer connection state
- Preserved pairing data enables reconnection after emergency

---

## Decision

We implement immediate motor coast with fire-and-forget coordinated shutdown:

1. **Local Shutdown (Immediate):**
   - ISR-based button monitoring detects 5-second hold
   - Immediate GPIO write for motor coast (~50ns)
   - No delays or waiting for acknowledgments

2. **Peer Coordination (Best Effort):**
   - BLE shutdown command sent without waiting for acknowledgment
   - Fallback to local shutdown if BLE disconnected (always safe)
   - Each device executes shutdown independently

3. **NVS Storage Clarification:**
   - ❌ Session state NOT saved: Don't resume mid-session (unsafe)
   - ✅ Pairing data saved: Peer device MAC address for reconnection (AD026)
   - ✅ Settings saved: Mode 5 custom parameters (frequency, duty cycle, LED)

---

## Consequences

### Benefits

- **Safety-first**: Device executes local shutdown immediately
- **Sub-100ms response**: GPIO write provides near-instantaneous motor coast
- **No blocking**: Don't wait for peer acknowledgment (may be powered off)
- **Always safe**: Each device shuts down independently
- **Reconnection preserved**: Pairing data enables automatic reconnection
- **ISR-based**: Fastest possible detection and response

### Drawbacks

- **Best effort coordination**: Peer may not receive shutdown command
- **Asymmetric shutdown**: One device may continue if BLE disconnected
- **User intervention**: May need to manually shut down peer device
- **No acknowledgment**: Cannot confirm peer received shutdown command

---

## Options Considered

### Option A: Fire-and-Forget Shutdown (Selected)

**Pros:**
- Immediate local shutdown (safety-first)
- No blocking on BLE operations
- Simple implementation (single GPIO write)
- Always safe (independent operation)

**Cons:**
- Peer may not receive shutdown command
- Asymmetric shutdown possible

**Selected:** YES
**Rationale:** Safety-first approach prioritizes immediate local shutdown over coordinated shutdown. Each device must be independently safe.

### Option B: Acknowledge-Before-Shutdown

**Pros:**
- Guaranteed peer coordination
- Symmetric shutdown behavior

**Cons:**
- Blocks waiting for peer response (may be infinite)
- Delayed local shutdown (safety risk)
- Fails if peer powered off or out of range
- Complex timeout logic required

**Selected:** NO
**Rationale:** Blocking on peer acknowledgment violates safety-first principle. Device must shut down immediately regardless of peer state.

### Option C: Timeout-Based Coordination

**Pros:**
- Bounded wait time (e.g., 500ms)
- Some coordination attempt

**Cons:**
- Still delays local shutdown
- Timeout adds complexity
- Partial solution (doesn't handle peer power-off)

**Selected:** NO
**Rationale:** Any delay in local shutdown is unacceptable for safety-critical device. Fire-and-forget provides same coordination benefit without delay.

---

## Related Decisions

### Related
- [AD013: Factory Reset Security Window] - Also uses 5-second button hold with different timing
- [AD026: BLE Pairing Data Persistence] - Pairing data preserved during emergency shutdown
- [AD011 NVS Clarification] - Session state vs. settings vs. pairing data storage

---

## Implementation Notes

### Code References

- `src/button_task.c` lines XXX-YYY (ISR-based button monitoring)
- `src/motor_task.c` lines XXX-YYY (motor_coast() function)
- `src/ble_manager.c` lines XXX-YYY (fire-and-forget shutdown message)

### Build Environment

- **Environment Name:** `xiao_esp32c6`
- **Configuration File:** `sdkconfig.xiao_esp32c6`
- **Build Flags:** None specific to emergency shutdown

### Implementation Pattern

```c
// ISR-based button monitoring
void button_isr_handler(void* arg) {
    // Detect 5-second hold
    if (button_hold_duration_ms >= 5000) {
        // Immediate motor coast (GPIO write, no delay)
        motor_set_direction_intensity(MOTOR_COAST, 0);

        // Fire-and-forget shutdown message to peer
        if (ble_is_peer_connected()) {
            ble_send_shutdown_command();  // No ACK wait
        }

        // Local shutdown continues regardless of BLE state
        shutdown_requested = true;
    }
}
```

### Testing & Verification

**Hardware testing performed:**
- Emergency shutdown during active session (motors stop within 50ms)
- Emergency shutdown with peer disconnected (local shutdown works)
- Emergency shutdown with peer powered off (local shutdown works)
- Reconnection after emergency shutdown (pairing data preserved)

**Known limitations:**
- Peer device may not receive shutdown command if powered off
- User may need to manually shut down peer device
- No confirmation of peer shutdown (by design)

---

## JPL Coding Standards Compliance

- ✅ Rule #1: No dynamic memory allocation - Uses static buffers for BLE messages
- ✅ Rule #2: Fixed loop bounds - ISR uses fixed-time polling
- ✅ Rule #3: No recursion - Linear shutdown sequence
- ✅ Rule #4: No goto statements - Structured control flow
- ✅ Rule #5: Return value checking - BLE send checked but not blocking
- ✅ Rule #6: No unbounded waits - Fire-and-forget (no wait)
- ✅ Rule #7: Watchdog compliance - Shutdown clears watchdog subscription
- ✅ Rule #8: Defensive logging - Emergency shutdown logged

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: ### AD011: Emergency Shutdown Protocol
Git commit: [to be filled after migration]

**NVS Storage Clarification Added:** November 2025
- Clarified difference between session state (not saved), pairing data (saved), and settings (saved)
- Rationale: Settings enable reconnection and user preferences, state would create unsafe resume

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
