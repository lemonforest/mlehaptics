# AD047: Scheduled Pattern Playback Architecture

**Date:** 2025-12-13
**Phase:** 7 (Future - Lightbar Mode)
**Status:** Proposed
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of bilateral motor/LED synchronization with dynamic frequency changes,
facing mid-cycle timing disruptions when parameters change reactively,
we decided for a scheduled pattern playback architecture with half-cycle boundary execution,
and neglected immediate parameter application,
to achieve seamless frequency transitions and enable complex lightbar-style patterns,
accepting that changes have up to half-cycle latency (250-1000ms depending on mode).

---

## Problem Statement

The current reactive architecture applies parameter changes immediately, causing:

1. **Mid-cycle glitches**: Changes arrive while motor is active, disrupting timing
2. **Phase drift**: CLIENT recalculates antiphase after changes, often adding extra cycle delay
3. **Bug cascade**: Bugs #81, #82, #83, #84 are all symptoms of reactive timing decisions
4. **Pattern limitations**: Complex lightbar patterns with scheduled frequency changes are impossible

A scheduled playback architecture decouples "decision time" from "execution time", eliminating this class of bugs.

---

## Context

### Current Architecture (Reactive)
```
Change arrives → Calculate timing → Execute immediately → Compensate for disruption
```

### Problems with Reactive Approach
- BLE latency (~50-100ms) causes CLIENT to receive changes late
- Motor may be mid-pulse when change arrives
- INACTIVE state recalculation can add extra cycle delay
- No clean execution boundary for frequency changes

### Lightbar Mode Requirements
The planned "Lightbar Mode" (BLE PWA-accessible) requires:
- Pre-scheduled frequency changes (like emergency vehicle lights)
- Perfect bilateral sync during pattern transitions
- Zero-glitch operation during RF disruption
- GPS-quality timing without GPS hardware

### Half-Cycle Boundary Insight
At half-cycle boundaries:
- SERVER: Transitioning from ACTIVE to INACTIVE (motor pulse complete)
- CLIENT: Transitioning from INACTIVE to ACTIVE (motor pulse about to start)
- **Neither device is mid-pulse** - safe to apply new parameters

This enables half-cycle latency instead of full-cycle.

---

## Decision

We will implement a **Scheduled Pattern Playback** architecture:

### Core Concepts

1. **Pattern Buffer**: Pre-computed schedule of future motor events
2. **Boundary Execution**: All changes take effect at half-cycle boundaries
3. **Lookahead Window**: Changes arriving within window affect next boundary

### Pattern Definition Structure

```c
typedef struct {
    uint32_t boundary_time_ms;    // Relative to pattern epoch
    uint16_t frequency_mhz;       // Frequency in millihertz (500 = 0.5Hz)
    uint8_t  duty_percent;        // Motor ON as % of ACTIVE period
    uint8_t  pwm_intensity;       // Motor power (0-100, 0 = LED-only)
    uint8_t  led_color_index;     // LED color palette index
    uint8_t  flags;               // Phase flip, pattern end, etc.
} pattern_segment_t;
```

### Execution Model

```c
// Producer: Queue future segments (runs 1+ half-cycle ahead)
if (segment_buffer_space()) {
    queue_next_segment(current_params);  // Uses latest params
}

// Consumer: Execute from buffer (immune to parameter changes)
execute_segment_from_buffer();  // Pre-computed, deterministic
```

### RF Disruption Resilience

Both devices maintain synchronized pattern buffers:
- If connection lost, continue executing from local buffer
- Pattern epoch is absolute time reference (not relative)
- Reconnection resumes at current position, not restart

---

## Consequences

### Benefits

- **Zero-glitch transitions**: Changes apply at clean boundaries
- **Eliminates bug class**: Bugs #81-84 become impossible
- **Lightbar mode enabled**: Complex scheduled patterns work
- **RF resilient**: Continues during brief disconnections
- **Simpler CLIENT logic**: Just follow the schedule
- **Half-cycle latency**: 250-1000ms vs full cycle

### Drawbacks

- **Latency**: User sees 250-1000ms delay on changes
- **Memory**: Pattern buffer requires ~100-500 bytes
- **Complexity**: Scheduling logic more complex than reactive
- **Synchronization**: Both devices must agree on pattern epoch

---

## Options Considered

### Option A: Reactive with Skip Flags (Current + Bug Fixes)

**Pros:**
- Already implemented
- Zero latency for changes
- Simple mental model

**Cons:**
- Endless bug whack-a-mole (#81, #82, #83, #84...)
- Can't do complex patterns
- RF disruption breaks sync

**Selected:** NO (for new features)
**Rationale:** Fundamental architecture limits prevent clean solution

### Option B: Full-Cycle Buffering

**Pros:**
- Guarantees symmetric pattern completion
- Maximum safety margin

**Cons:**
- 500-2000ms latency (too slow)
- Wastes half the possible boundaries

**Selected:** NO
**Rationale:** Half-cycle boundaries are equally safe with half the latency

### Option C: Half-Cycle Boundary Scheduling (Selected)

**Pros:**
- Clean execution boundaries
- 250-1000ms latency (acceptable)
- Enables all future patterns
- RF resilient design

**Cons:**
- Requires architectural change
- Some implementation complexity

**Selected:** YES
**Rationale:** Best balance of safety, responsiveness, and future capability

---

## Related Decisions

### Related
- [AD041: Predictive Bilateral Synchronization](0041-predictive-bilateral-synchronization.md) - Foundation timing model
- [AD044: Non-blocking Motor Timing](0044-non-blocking-motor-timing.md) - Hardware timer infrastructure
- [AD045: Synchronized Independent Bilateral Operation](0045-synchronized-independent-bilateral-operation.md) - Current two-phase commit
- [AD046: PTP Observation Mode Integration](0046-ptp-observation-mode-integration.md) - Activation reports

---

## Implementation Notes

### Phase 1: Half-Cycle Boundary Execution (Near-term)

Modify existing two-phase commit to:
1. Calculate boundary time as `server_epoch + N * half_cycle`
2. Both devices execute at boundary, not arbitrary epoch
3. CLIENT skips INACTIVE after boundary (already Bug #83 pattern)

### Phase 2: Pattern Buffer (Lightbar Mode)

1. Define pattern segment structure
2. Implement circular buffer for segments
3. PWA sends pattern definition via BLE
4. Both devices execute from synchronized buffer

### Phase 3: RF Resilience

1. Pattern continues during disconnect (frozen drift extrapolation)
2. Reconnection compares pattern position
3. Resync if position diverges beyond threshold

### Known Issues to Address

- **Offline device**: Unspecified behavior when one device is off during mode change
- **Pattern sync**: How to ensure both devices have same pattern loaded
- **Buffer underrun**: What happens if changes arrive faster than half-cycle

---

## Lightbar Mode Concept

### Use Case
Demonstrate GPS-quality bilateral sync with complex visual patterns:
- Emergency vehicle light simulation
- Alternating flash patterns with frequency changes
- Showcases sub-millisecond timing precision

### Pattern Example
```c
// Emergency lightbar pattern (simplified)
pattern_segment_t emergency_pattern[] = {
    { 0,     2000, 50, 0, RED,   0 },  // 2Hz red flash
    { 2000,  2000, 50, 0, BLUE,  0 },  // 2Hz blue flash
    { 4000,  4000, 25, 0, RED,   0 },  // 4Hz rapid red
    { 5000,  4000, 25, 0, BLUE,  0 },  // 4Hz rapid blue
    { 6000,  1000, 50, 0, WHITE, 0 },  // 1Hz slow white
    { 8000,  0,    0,  0, 0,     PATTERN_LOOP },  // Loop to start
};
```

### PWA Integration
- Mode 6 (or special Mode 4 submode): Lightbar mode
- PWA uploads pattern via BLE GATT
- Devices store pattern in RAM (not NVS - patterns are session-local)
- Start command includes pattern epoch for sync

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-12-13
