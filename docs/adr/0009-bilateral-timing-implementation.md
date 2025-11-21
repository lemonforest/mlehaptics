# 0009: Bilateral Timing Implementation with Configurable Cycles

**Date:** 2025-10-15
**Phase:** 0.1
**Status:** Accepted
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of coordinating bilateral motor activation across two wireless devices,
facing requirements for non-overlapping stimulation and configurable frequency (0.5-2 Hz),
we decided for server-controlled master timing with total cycle time configuration,
and neglected client-controlled or synchronized-clock approaches,
to achieve guaranteed non-overlap with therapist-configurable bilateral frequency,
accepting server as single point of failure for bilateral coordination.

---

## Problem Statement

Bilateral stimulation requires:
- **Non-overlapping**: Left and right motors NEVER active simultaneously
- **Configurable frequency**: 0.5-2 Hz bilateral rate (500ms-2000ms total cycle)
- **Precision timing**: ±10ms maximum deviation
- **Fail-safe behavior**: If communication lost, maintain safe operation
- **Server authority**: One device must coordinate timing

Who controls timing?
- Server dictates when each device activates?
- Both devices run synchronized clocks?
- Client requests activation windows?

How to ensure non-overlapping with wireless latency?

---

## Context

### Therapeutic Requirements

**EMDRIA Standards:**
- Bilateral alternation required (not simultaneous)
- Non-overlapping stimulation critical for therapeutic effect
- Frequency range: 0.5-2 Hz typical

**Safety Requirements:**
- Devices NEVER stimulate simultaneously
- Immediate emergency stop (<50ms response)
- Fail-safe behavior if BLE communication lost

### Technical Constraints

**BLE Communication:**
- Latency: ~10-50ms typical (ESP32-C6 to ESP32-C6)
- Packet loss: Occasional (interference, distance)
- Connection loss: Device power-off, out of range

**FreeRTOS Timing:**
- vTaskDelay() provides ±1-2ms precision
- 1ms dead time for watchdog feeding
- Half-cycle range: 250ms-1000ms

---

## Decision

We will use **server-controlled master timing** with **configurable total cycle time**.

### Timing Architecture

**Server Role:**
- Maintains master clock
- Commands client when to activate
- Configures total cycle time via BLE
- Activates during first half-cycle
- Waits during second half-cycle

**Client Role:**
- Receives timing commands from server
- Activates during second half-cycle
- Waits during first half-cycle
- Mirrors server's total cycle time

### Example Timing Patterns

**1000ms Total Cycle (1 Hz bilateral rate):**
```
Server: [===499ms motor===][1ms dead][---499ms off---][1ms dead]
Client: [---499ms off---][1ms dead][===499ms motor===][1ms dead]
```

**2000ms Total Cycle (0.5 Hz bilateral rate):**
```
Server: [===999ms motor===][1ms dead][---999ms off---][1ms dead]
Client: [---999ms off---][1ms dead][===999ms motor===][1ms dead]
```

**500ms Total Cycle (2 Hz bilateral rate):**
```
Server: [===249ms motor===][1ms dead][---249ms off---][1ms dead]
Client: [---249ms off---][1ms dead][===249ms motor===][1ms dead]
```

### Critical Safety Requirements

1. **Non-overlapping stimulation**: Devices NEVER stimulate simultaneously
2. **Precision timing**: ±10ms maximum deviation from configured cycle
3. **Half-cycle guarantee**: Each device gets exactly 50% of total cycle
4. **Dead time inclusion**: 1ms dead time included within each half-cycle window
5. **Server authority**: Server maintains master clock and commands client
6. **Immediate emergency stop**: 50ms maximum response time to shutdown

### Implementation Strategy

**BLE Command Messages:**
```c
typedef enum {
    CMD_START_SESSION,      // Begin bilateral stimulation
    CMD_STOP_SESSION,       // Stop stimulation
    CMD_SET_CYCLE_TIME,     // Configure total cycle time (ms)
    CMD_SET_INTENSITY,      // Configure motor PWM intensity (%)
    CMD_EMERGENCY_STOP      // Immediate shutdown
} bilateral_command_t;
```

**Timing Execution:**
- Server: Execute half-cycle, send CLIENT_ACTIVATE command, wait half-cycle
- Client: Wait for CLIENT_ACTIVATE, execute half-cycle, send CLIENT_DONE
- FreeRTOS vTaskDelay() for all timing (JPL compliant)
- 1ms dead time at end of each half-cycle for watchdog feeding

**Fail-Safe Behavior:**
- If communication lost, maintain last known cycle time
- Single-device mode: Forward/reverse alternating pattern
- Non-overlapping maintained at all times
- LED heartbeat pattern during fallback

### Haptic Effects Support

```c
// Short haptic pulse within half-cycle window
// Example: 200ms pulse in 500ms half-cycle
motor_active_time = 200ms;
coast_time = 500ms - 200ms - 1ms = 299ms;
dead_time = 1ms;
// Total = 500ms half-cycle maintained
```

---

## Consequences

### Benefits

- **Guaranteed non-overlap**: Server controls when each device activates
- **Configurable frequency**: Therapist adjusts bilateral rate (0.5-2 Hz)
- **Precision timing**: ±10ms achievable with FreeRTOS
- **Simple coordination**: Server dictates, client follows
- **Fail-safe**: Each device falls back to safe single-device mode
- **Emergency stop**: Server sends immediate shutdown command
- **Haptic flexibility**: Can vary motor duration within half-cycle

### Drawbacks

- **Server dependency**: Bilateral coordination requires server operation
- **BLE latency**: ~10-50ms command latency adds to timing jitter
- **Single point of failure**: Server malfunction stops bilateral coordination
- **No clock sync**: Client trusts server timing (no independent verification)

---

## Options Considered

### Option A: Server-Controlled Master Timing (Selected)

**Pros:**
- Simple coordination (server dictates)
- Guaranteed non-overlap (sequential activation)
- Configurable cycle time via BLE commands
- Fail-safe fallback to single-device mode

**Cons:**
- Server is single point of failure
- BLE latency affects timing precision

**Selected:** YES
**Rationale:** Simplest approach guaranteeing non-overlapping stimulation

### Option B: Synchronized Clocks (NTP-Style) - REJECTED

**Pros:**
- Both devices independent after sync
- No ongoing BLE coordination required
- More robust to communication loss

**Cons:**
- Complex clock synchronization protocol
- Clock drift over 20+ minute sessions
- Harder to guarantee non-overlap (clock skew)
- Overkill for 2-device system

**Selected:** NO
**Rationale:** Unnecessary complexity for simple 2-device coordination

### Option C: Client-Controlled Timing (Handshake) - REJECTED

**Pros:**
- Client confirms completion before server starts
- Explicit handshake protocol

**Cons:**
- Double BLE latency (server→client, client→server)
- More complex protocol
- No benefit over server-controlled

**Selected:** NO
**Rationale:** Extra latency and complexity without benefits

### Option D: Simultaneous Activation (Phase-Shifted PWM) - REJECTED

**Pros:**
- Both devices active simultaneously (lower latency)

**Cons:**
- ❌ Violates EMDRIA requirement (bilateral alternation, not simultaneous)
- ❌ Not true bilateral stimulation
- ❌ Therapeutic efficacy unproven

**Selected:** NO
**Rationale:** Does not meet EMDRIA bilateral alternation requirement

---

## Related Decisions

### Related
- [AD006: Bilateral Cycle Time Architecture](0006-bilateral-cycle-time-architecture.md) - Total cycle time as primary parameter
- [AD008: BLE Protocol Architecture](0008-ble-protocol-architecture.md) - BLE command messaging
- [AD010: Race Condition Prevention Strategy](0010-race-condition-prevention-strategy.md) - Server/client role assignment
- [AD011: Emergency Shutdown Protocol](0011-emergency-shutdown-protocol.md) - Immediate stop command

---

## Implementation Notes

### Code References

- `src/motor_task.c` - Half-cycle execution (server and client)
- `src/ble_manager.c` - Bilateral command messaging
- `src/ble_task.c` - BLE event handling and coordination

### Build Environment

All Phase 1+ environments implement bilateral timing.

### BLE Command Flow

**Session Start:**
```
Server → Client: CMD_START_SESSION(total_cycle_ms=1000, intensity=80%)
Server: Execute first half-cycle (499ms motor + 1ms dead)
Server → Client: CLIENT_ACTIVATE
Client: Execute half-cycle (499ms motor + 1ms dead)
Client → Server: CLIENT_DONE
[Repeat until CMD_STOP_SESSION]
```

**Emergency Stop:**
```
Server/Client: Button hold (5s)
Server → Client: CMD_EMERGENCY_STOP (fire-and-forget)
Server: Immediate motor coast + shutdown
Client: Immediate motor coast + shutdown
```

### Testing & Verification

**Bilateral Timing Verified:**
- ✅ Non-overlapping: Oscilloscope shows no simultaneous motor activation
- ✅ Precision: ±5ms deviation over 20+ minute sessions
- ✅ Configurable: 500ms, 1000ms, 2000ms total cycles tested
- ✅ Fail-safe: Communication loss triggers single-device fallback

**Test Cases:**
- 500ms total cycle (2 Hz): Server/client 249ms each + 1ms dead time
- 1000ms total cycle (1 Hz): Server/client 499ms each + 1ms dead time
- 2000ms total cycle (0.5 Hz): Server/client 999ms each + 1ms dead time
- Packet loss: 3 consecutive misses → single-device fallback
- Emergency stop: <50ms response time (server → client)

**Known Issues:**
- BLE latency adds ±10ms jitter (acceptable for therapeutic use)
- Server power-off requires manual client reset (no auto-reconnect yet)

---

## JPL Coding Standards Compliance

- ✅ Rule #1: No dynamic memory - Timing constants statically defined
- ✅ Rule #2: Fixed loop bounds - Bilateral loop bounded by session duration
- ✅ Rule #5: Return value checking - BLE send results checked
- ✅ Rule #6: No unbounded waits - vTaskDelay() has explicit timeouts
- ✅ Rule #7: Watchdog compliance - Dead time feeds TWDT
- ✅ Rule #8: Defensive logging - Bilateral commands logged

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: AD009 (Software Architecture Decisions)
Git commit: Current working tree

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
