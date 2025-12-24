# AD047 Supplemental: Bilateral Pattern Playback Architecture
## For External AI Review (Gemini Feedback Request)

**Date:** 2025-12-16
**Purpose:** Provide comprehensive context for external AI feedback on proposed architectural shift
**Status:** Design phase - seeking validation before implementation

---

## 1. Project Overview

**EMDR Bilateral Stimulation Device** - An open-source therapeutic device for Eye Movement Desensitization and Reprocessing (EMDR) therapy.

### Hardware
- 2x Seeed XIAO ESP32-C6 microcontrollers (RISC-V @ 160MHz)
- 2x ERM vibration motors (one per device, left/right hands)
- 2x WS2812B RGB LEDs (visual feedback)
- BLE communication between paired devices
- Battery powered (320mAh LiPo per device)

### Current Functionality
- Bilateral alternation: Left motor ON while right motor OFF, then swap
- Frequency range: 0.5-2.0 Hz (therapeutic EMDR range)
- Time synchronization: PTP-inspired protocol achieving ±30 microseconds accuracy
- Roles: SERVER (higher battery, sends timing reference) and CLIENT (receives, calculates antiphase)

### Codebase
- Framework: ESP-IDF v5.5.0 (FreeRTOS-based)
- Coding standard: JPL embedded systems (no malloc, bounded loops, explicit error handling)
- Language: C (embedded, ~15K lines)

---

## 2. Current Architecture: Reactive Motor Timing

### How It Works Today

The current system uses a **reactive** approach where:
1. SERVER sets a `motor_epoch` (start timestamp) and broadcasts it via BLE beacon
2. CLIENT receives beacon, calculates antiphase offset (half-cycle delay)
3. Both devices execute motor pulses based on their calculated next activation time
4. Mode/frequency changes trigger recalculation of timing parameters

### Current Data Structures

```c
// From time_sync.h - Current beacon structure (25 bytes)
typedef struct __attribute__((packed)) {
    uint64_t server_time_us;    // SERVER's current time
    uint64_t motor_epoch_us;    // Pattern start time
    uint32_t motor_cycle_ms;    // Cycle period (e.g., 2000ms for 0.5Hz)
    uint8_t  duty_percent;      // Motor ON time as % of half-cycle
    uint8_t  mode_id;           // Mode identifier (0-4)
    uint8_t  sequence;          // Sequence number
    uint16_t checksum;          // CRC-16
} time_sync_beacon_t;
```

```c
// From motor_task.c - Mode configurations
const mode_config_t modes[MODE_COUNT] = {
    // {name, motor_on_ms, active_coast_ms, inactive_ms}
    {"0.5Hz@25%",  250,  750, 1000},  // Mode 0
    {"1.0Hz@25%",  125,  375,  500},  // Mode 1
    {"1.5Hz@25%",   84,  250,  333},  // Mode 2
    {"2.0Hz@25%",   63,  187,  250},  // Mode 3
    {"Custom",     250,  250,  500}   // Mode 4
};
```

### Current Antiphase Calculation (CLIENT)

```c
// Simplified from actual implementation
uint64_t server_epoch_us, cycle_ms;
time_sync_get_motor_epoch(&server_epoch_us, &cycle_ms);

// CLIENT activates at half-cycle offset from SERVER
uint64_t half_cycle_us = (cycle_ms * 1000) / 2;
uint64_t client_epoch_us = server_epoch_us + half_cycle_us;

// Calculate next activation from epoch
uint64_t now_us = esp_timer_get_time();
uint64_t cycles_elapsed = (now_us - client_epoch_us) / (cycle_ms * 1000);
uint64_t next_activation = client_epoch_us + (cycles_elapsed + 1) * (cycle_ms * 1000);
```

### Problems with Reactive Architecture

1. **Bug cascade**: Bugs #81-96 are all variations of "reactive timing calculation went wrong"
   - Mode change during active pulse
   - CLIENT recalculating antiphase when it shouldn't
   - Phase drift from calculation errors
   - Extra cycle delays after frequency changes

2. **Mid-cycle glitches**: Changes arrive while motor is active, causing timing disruption

3. **Complex state management**: CLIENT must track:
   - Whether to skip INACTIVE wait
   - Armed mode changes
   - Server epoch vs local epoch
   - Cycle counts for correlation

4. **Cannot support complex patterns**: Only single-frequency bilateral alternation

---

## 3. Proposed Architecture: Bilateral Pattern Playback

### Core Insight

Inspired by emergency vehicle light bars (Feniex, Whelen):
- Police lights don't negotiate timing per-flash
- All modules receive the SAME pattern definition
- Each module knows its zone (left bar, right bar, center)
- They execute independently from shared "sheet music"

### Key Conceptual Shift

**Current (Reactive):**
```
SERVER calculates → Broadcasts epoch → CLIENT calculates antiphase → Both execute independently
                                       ↑ This calculation is source of bugs
```

**Proposed (Pattern Playback):**
```
Pattern defines BOTH zones → SERVER reads zone_left → CLIENT reads zone_right → Both execute
                             No calculation needed - pattern is explicit
```

### Proposed Data Structures

```c
// Zone assignment (determined at BLE pairing)
typedef enum {
    ZONE_UNASSIGNED = 0,
    ZONE_LEFT,      // Phase 1 (SERVER) - typically left hand
    ZONE_RIGHT,     // Phase 2 (CLIENT) - typically right hand
} zone_id_t;

// Single segment of a bilateral pattern
// Contains BOTH zone definitions in same structure
typedef struct __attribute__((packed)) {
    uint32_t time_offset_ms;      // Relative to pattern epoch (0, 250, 500, 750...)

    // Zone definitions - BOTH in same structure
    struct {
        uint8_t led_color;        // Color palette index (0-15)
        uint8_t led_brightness;   // 0-100%
        uint8_t motor_intensity;  // 0-100% (0 = LED-only mode)
    } zone_left;                  // Phase 1 / SERVER

    struct {
        uint8_t led_color;        // Color palette index
        uint8_t led_brightness;   // 0-100%
        uint8_t motor_intensity;  // 0-100%
    } zone_right;                 // Phase 2 / CLIENT

} bilateral_segment_t;           // 10 bytes per segment

// Complete pattern (the "sheet music")
typedef struct {
    uint64_t epoch_us;            // Synchronized pattern start time
    uint32_t loop_point_ms;       // Where to restart (0 = no loop)
    uint8_t  segment_count;       // Number of segments (max ~50?)
    bilateral_segment_t segments[]; // Flexible array member
} bilateral_pattern_t;
```

### Example: Emergency Light Pattern

```c
// Classic police alternating pattern - RED/BLUE at 2Hz
// This single pattern is loaded on BOTH devices
bilateral_pattern_t emergency_pattern = {
    .epoch_us = 0,          // Set at runtime (synchronized start)
    .loop_point_ms = 1000,  // Loop every 1 second
    .segment_count = 4,
    .segments = {
        // T=0ms: LEFT=RED, RIGHT=OFF
        { .time_offset_ms = 0,
          .zone_left  = { .led_color = RED, .led_brightness = 100, .motor_intensity = 0 },
          .zone_right = { .led_color = OFF, .led_brightness = 0,   .motor_intensity = 0 }},

        // T=250ms: LEFT=OFF, RIGHT=BLUE
        { .time_offset_ms = 250,
          .zone_left  = { .led_color = OFF,  .led_brightness = 0,   .motor_intensity = 0 },
          .zone_right = { .led_color = BLUE, .led_brightness = 100, .motor_intensity = 0 }},

        // T=500ms: LEFT=RED, RIGHT=OFF
        { .time_offset_ms = 500,
          .zone_left  = { .led_color = RED, .led_brightness = 100, .motor_intensity = 0 },
          .zone_right = { .led_color = OFF, .led_brightness = 0,   .motor_intensity = 0 }},

        // T=750ms: LEFT=OFF, RIGHT=BLUE
        { .time_offset_ms = 750,
          .zone_left  = { .led_color = OFF,  .led_brightness = 0,   .motor_intensity = 0 },
          .zone_right = { .led_color = BLUE, .led_brightness = 100, .motor_intensity = 0 }},
    }
};
```

### Example: Standard EMDR Therapy Pattern

```c
// 1.0Hz bilateral motor alternation with LED indication
bilateral_pattern_t emdr_1hz_pattern = {
    .epoch_us = 0,
    .loop_point_ms = 1000,  // 1Hz = 1000ms period
    .segment_count = 2,
    .segments = {
        // T=0ms: LEFT active, RIGHT inactive
        { .time_offset_ms = 0,
          .zone_left  = { .led_color = GREEN, .led_brightness = 30, .motor_intensity = 60 },
          .zone_right = { .led_color = OFF,   .led_brightness = 0,  .motor_intensity = 0  }},

        // T=500ms: LEFT inactive, RIGHT active (antiphase)
        { .time_offset_ms = 500,
          .zone_left  = { .led_color = OFF,   .led_brightness = 0,  .motor_intensity = 0  },
          .zone_right = { .led_color = GREEN, .led_brightness = 30, .motor_intensity = 60 }},
    }
};
```

---

## 4. The "Conductor" Model

### Current: motor_task Drives Everything

In the current architecture, `motor_task` is actually doing multiple jobs:
1. Timing calculations (epoch, antiphase, next activation)
2. Motor control (PWM commands)
3. LED control (color changes synchronized with motor)
4. State machine transitions
5. Message handling (mode changes, shutdown)

### Proposed: Conductor Task

Rename/refactor `motor_task` to be a "conductor" that:
1. Advances through pattern segments based on synchronized time
2. Dispatches outputs to appropriate hardware (motors, LEDs)
3. Handles pattern loading and loop points
4. Maintains timing even when motors are silent (PWM 0%)

**Key insight: When `motor_intensity = 0%`, the conductor still runs and advances through segments.** This enables:
- LED-only modes (visual bilateral stimulation)
- Seamless transitions between LED-only and motor patterns
- Consistent timing reference regardless of output type

```c
// Conductor execution loop (conceptual)
void conductor_task(void *arg) {
    bilateral_pattern_t *pattern = get_active_pattern();
    zone_id_t my_zone = role_manager_get_zone();  // ZONE_LEFT or ZONE_RIGHT

    while (session_active) {
        uint64_t now_us;
        time_sync_get_time(&now_us);

        // Calculate position in pattern
        uint32_t pattern_time_ms = (now_us - pattern->epoch_us) / 1000;
        if (pattern->loop_point_ms > 0) {
            pattern_time_ms = pattern_time_ms % pattern->loop_point_ms;
        }

        // Find current segment
        bilateral_segment_t *seg = find_segment_for_time(pattern, pattern_time_ms);

        // Extract MY zone's outputs
        zone_output_t output = (my_zone == ZONE_LEFT)
            ? seg->zone_left
            : seg->zone_right;

        // Apply outputs
        led_set_color(output.led_color, output.led_brightness);
        if (output.motor_intensity > 0) {
            motor_set_forward(output.motor_intensity, false);
        } else {
            motor_coast(false);  // Motors silent but conductor keeps running
        }

        // Wait until next segment boundary
        uint32_t next_segment_ms = find_next_segment_time(pattern, pattern_time_ms);
        delay_until_absolute_time(pattern->epoch_us + next_segment_ms * 1000);
    }
}
```

---

## 5. Pattern Distribution Protocol

### How Patterns Get to Devices

**Option A: SERVER Broadcasts Complete Pattern**
```
1. PWA sends pattern to SERVER via BLE GATT
2. SERVER stores pattern, sets epoch
3. SERVER broadcasts pattern to CLIENT via BLE notification
4. Both devices execute from identical local copies
```

**Option B: PWA Sends to Both Devices**
```
1. PWA connects to both devices (already supported)
2. PWA sends identical pattern to both
3. PWA sends synchronized START command with epoch
4. Both devices execute from identical local copies
```

**Current Preference:** Option A (simpler, matches existing beacon architecture)

### Pattern Epoch Synchronization

The pattern's `epoch_us` must be synchronized:
1. SERVER decides epoch (current time + coordination delay)
2. SERVER broadcasts epoch in time sync beacon (already implemented)
3. CLIENT receives and aligns to same epoch
4. Both execute pattern segments at identical absolute times

This is **identical to current approach** - just with richer segment data.

---

## 6. Industry Comparison

### Emergency Vehicle Lighting (Feniex, Whelen)

- Light bars receive **pattern definitions**, not per-flash commands
- Controller broadcasts: "Run pattern #7 starting NOW"
- Each module knows its position and extracts its portion
- Sub-millisecond sync across 20+ LED modules

**Similarity to our approach:** Bilateral pattern = emergency light pattern with 2 zones

### DMX-512 Lighting Protocol

- Controller sends frame with 512 channel values at 44Hz
- Each fixture has a "start address" and reads N consecutive channels
- Fixtures don't calculate - they just read their assigned channels

**Similarity to our approach:** Zone = DMX start address, segment = DMX frame

### MIDI Sequencing

- Sequencer sends timestamped events: "Note ON, channel 1, velocity 80, at tick 480"
- Instruments don't calculate - they play notes at specified times

**Similarity to our approach:** Pattern segments = MIDI events, conductor = sequencer

### Professional Assessment

This pattern-based architecture is **not over-engineering**. It's the standard approach used by:
- Emergency vehicle lighting (safety-critical, must never desync)
- Stage lighting (hundreds of fixtures, perfect sync)
- Musical instruments (timing precision critical)
- Industrial automation (coordinated motion)

Our requirements (2 devices, ±100ms tolerance) are actually simpler than these applications.

---

## 7. Migration Strategy

### Dual Architecture Approach

1. **Keep existing reactive architecture** for Modes 0-4 (therapy modes)
   - Well-tested, handles basic bilateral alternation
   - Continues to work for current therapeutic use case

2. **Add pattern-based architecture** for Mode 5/6 (lightbar mode)
   - New "showcase" mode demonstrating sync precision
   - LED-only initially (no motor safety concerns)
   - Prove the architecture before migrating therapy modes

3. **Future: Migrate therapy modes** once pattern architecture proven
   - Define therapy patterns using same structure
   - Eliminate entire class of antiphase calculation bugs
   - Enable future features (dynamic frequency sweeps, etc.)

### Implementation Phases

**Phase 1: Data Structures**
- Define `bilateral_segment_t` and `bilateral_pattern_t`
- Add zone assignment to role manager
- Create predefined patterns (emergency, emdr_1hz, etc.)

**Phase 2: Conductor Refactor**
- Refactor motor_task to pattern-based execution
- Add pattern loading from NVS/BLE
- Implement segment advancement with loop points

**Phase 3: BLE Integration**
- Add pattern characteristic to GATT service
- Implement pattern broadcast from SERVER
- Add PWA pattern editor (future)

**Phase 4: Therapy Mode Migration**
- Convert Modes 0-4 to pattern definitions
- Deprecate antiphase calculation code
- Full regression testing

---

## 8. Project Philosophy & Questions for Feedback

### About This Project

**Important context for providing feedback:**

This is a solo passion project by someone who cares deeply about doing things *right*, not just "good enough to ship." The distinction matters:

| "Good Enough" Mindset | This Project's Mindset |
|-----------------------|------------------------|
| Ship MVP, iterate later | Build it correctly the first time |
| Simplify to reduce scope | Embrace complexity that serves the goal |
| "Nobody will notice" | "I will know it's wrong" |
| Cost/time optimization | Correctness/elegance optimization |
| 80/20 rule | 100% of intended behavior |

The emergency lightbar showcase isn't just a demo - it's proof that the synchronization system works *exactly* as designed, visible to the naked eye. Sub-millisecond precision between two battery-powered devices over BLE, with no wires, demonstrating mastery of the hardware and protocol.

**What I'm looking for:**
- Help refining this architecture to be *excellent*, not simpler
- Industry insights that make it more robust
- Edge cases I haven't considered
- Alternative approaches that are *equally sophisticated*

**What I'm NOT looking for:**
- "Just use your reactive approach, it's simpler"
- "This is overkill for 2 devices"
- MVP/pragmatic shortcuts

---

### Architecture Refinement Questions

1. **Bilateral segment structure optimization:**
   - 10 bytes per segment allows ~50 segments in 500-byte budget
   - Is per-segment PWM intensity granularity (8-bit, 0-100%) sufficient?
   - Should we add per-segment flags (e.g., "smooth transition", "hard cut")?
   - Any fields missing that professional lighting protocols include?

2. **Zone model coexistence with roles:**
   - Current: SERVER/CLIENT roles (for time sync authority)
   - Proposed: Zone LEFT/RIGHT (for pattern consumption)
   - These seem orthogonal - SERVER can be LEFT or RIGHT depending on physical placement
   - Is this the right mental model, or should we unify them?

3. **Pattern distribution efficiency:**
   - BLE notification MTU is ~240 bytes (negotiated)
   - Complex patterns may need fragmentation
   - How do professional systems handle pattern updates mid-playback?
   - Should patterns be immutable once started, requiring full stop/reload?

### Implementation Refinement Questions

4. **Variable-length pattern storage:**
   - Flexible array member requires knowing size at allocation
   - Fixed max (e.g., 64 segments) wastes memory for simple patterns
   - NVS has 4KB page size - what's the sweet spot?
   - Any compression techniques used in DMX/lighting for pattern storage?

5. **Timing precision tradeoffs:**
   - `uint32_t time_offset_ms` supports patterns up to ~50 days
   - `uint16_t` would cap at 65 seconds but save 2 bytes/segment
   - For looping patterns, 65 seconds seems sufficient
   - Is there value in sub-millisecond timing (`uint32_t time_offset_us`)?

6. **Loop boundary edge cases:**
   - What if motor pulse spans loop point? (e.g., pulse at 990ms, loop at 1000ms)
   - Should we require segments to align cleanly to loop point?
   - How does DMX handle this? (I assume they just don't care since it's 44Hz refresh)

### Edge Cases & Failure Modes

7. **Pattern mismatch between devices:**
   - What if SERVER and CLIENT somehow have different patterns loaded?
   - Should patterns include a hash/version for validation?
   - Is there a "safe mode" pattern that both can fall back to?

8. **Mid-pattern updates:**
   - User changes mode via PWA while pattern is running
   - Immediate switch (may cause jarring transition) vs. wait for loop point?
   - Professional lighting uses "cue stacks" - relevant here?

9. **Timing drift during long patterns:**
   - Our time sync achieves ±30μs over 90 minutes
   - For a 60-second looping pattern over 20-minute session, drift is negligible
   - But for non-looping patterns (one-shot sequences), should we re-anchor periodically?

### Industry Wisdom Questions

10. **What are we missing from professional lighting?**
    - DMX has concepts like "fade time", "hold time", "chase direction"
    - Are any of these relevant to bilateral stimulation?
    - Emergency lighting has "phase groups" - is our zone model sufficient?

11. **Failure recovery patterns:**
    - Professional systems have "home position" / "blackout" fallbacks
    - What should happen if pattern execution encounters an error?
    - Should there be a watchdog that reverts to simple alternation if pattern stalls?

---

## 9. Relevant Code References

For deeper investigation, these files contain the current implementation:

| File | Lines | Description |
|------|-------|-------------|
| `src/motor_task.c` | 1-200 | Current 9-state motor machine, mode configs |
| `src/motor_task.h` | All | Motor API, state definitions |
| `src/time_sync.h` | All | Time sync protocol, beacon structure |
| `src/time_sync.c` | All | PTP-style sync implementation |
| `src/role_manager.c` | All | SERVER/CLIENT role assignment |
| `src/led_control.c` | All | WS2812B control via RMT peripheral |
| `docs/adr/0045-synchronized-independent-bilateral-operation.md` | All | Current timing architecture |
| `docs/adr/0047-scheduled-pattern-playback.md` | All | Original pattern playback proposal |

---

## 10. Success Criteria

The pattern-based architecture will be considered successful if:

1. **Zero antiphase calculation bugs** - Pattern explicitly defines both zones
2. **Seamless mode transitions** - No glitches when switching patterns
3. **RF resilience** - Continue executing during brief BLE dropouts
4. **PWA pattern editing** - Users can create custom patterns
5. **Sub-millisecond sync** - Emergency light demo visually impressive
6. **Maintainability** - Simpler code than current reactive approach

---

**Document prepared for external AI review.**
**Project: EMDR Bilateral Stimulation Device**
**Architecture Decision: AD047 - Scheduled Pattern Playback**
