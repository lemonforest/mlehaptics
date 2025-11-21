# 0006: Bilateral Cycle Time Architecture

**Date:** 2025-10-15
**Phase:** 0.1
**Status:** Accepted
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of implementing bilateral stimulation timing for therapeutic EMDR applications,
facing requirements for precise non-overlapping motor activation and JPL-compliant timing,
we decided for total cycle time as primary parameter with FreeRTOS dead time,
and neglected per-device timing or hardware timers with busy-wait loops,
to achieve therapist-friendly configuration (0.5-2 Hz bilateral rate) with guaranteed non-overlap,
accepting 1ms overhead (0.1-0.2%) for watchdog feeding and safety margin.

---

## Problem Statement

Bilateral stimulation requires:
- **Non-overlapping activation**: Left and right motors NEVER active simultaneously
- **Therapeutic frequency range**: 0.5-2 Hz bilateral rate (500ms-2000ms total cycle)
- **Precision timing**: ±10ms maximum deviation for therapeutic effectiveness
- **JPL compliance**: No busy-wait loops, only FreeRTOS delays
- **Watchdog feeding**: Must feed Task Watchdog Timer (TWDT) regularly

How do we structure timing parameters?
- Total cycle time (bilateral frequency) vs. per-device half-cycle?
- How to guarantee non-overlapping with JPL-compliant delays?
- Where to feed watchdog without affecting timing precision?

---

## Context

### Therapeutic Requirements

**EMDRIA Standards:**
- Bilateral alternation required (left-right-left-right pattern)
- Typical frequency range: 0.5-2 Hz bilateral stimulation
- Session duration: 20+ minutes continuous operation
- Timing precision affects therapeutic efficacy

**User Configuration:**
- Therapists think in bilateral frequency (Hz), not half-cycles
- 1 Hz bilateral rate = traditional EMDR standard
- Lower frequencies (0.5 Hz) for calmer sessions
- Higher frequencies (2 Hz) for more active processing

### Technical Constraints

**JPL Coding Standard (AD002):**
- No busy-wait loops (`esp_rom_delay_us()` forbidden)
- All timing must use FreeRTOS primitives (`vTaskDelay()`)
- Watchdog must be fed regularly (max 2000ms timeout)

**Hardware:**
- GPIO write latency: ~50ns (provides hardware dead time)
- MOSFET turn-off time: ~30ns
- FreeRTOS tick period: 1ms (minimum `vTaskDelay()` resolution)

**FreeRTOS Constraints:**
- `vTaskDelay(pdMS_TO_TICKS(1))` = minimum delay (1ms)
- Cannot delay < 1ms without busy-wait
- Task scheduling adds jitter (±1-2ms acceptable)

---

## Decision

We will use **total cycle time** as the primary configuration parameter, with automatic half-cycle calculation and **1ms FreeRTOS dead time** for watchdog feeding.

### Cycle Time Structure

**User Configuration:**
- Total bilateral cycle time: 500-2000ms
- Corresponds to 2 Hz - 0.5 Hz bilateral stimulation rate
- Default: 1000ms (1 Hz, traditional EMDR rate)

**Automatic Calculation:**
- Per-device half-cycle = total_cycle / 2
- Motor active time = half_cycle - 1ms (reserve for dead time)
- Dead time = 1ms (watchdog feeding + safety margin)

### Timing Budget Per Half-Cycle

```
Example: 1000ms total cycle (1 Hz bilateral rate)

Half-Cycle Window: 500ms
├─ Motor Active: 499ms [vTaskDelay]
├─ Motor Coast: Immediate GPIO write (~50ns)
├─ Dead Time: 1ms [vTaskDelay + esp_task_wdt_reset()]
└─ Total: 500ms (exactly half of total cycle)

Bilateral Pattern:
Server: [===499ms motor===][1ms dead][---499ms off---][1ms dead]
Client: [---499ms off---][1ms dead][===499ms motor===][1ms dead]
```

### Implementation Pattern

```c
esp_err_t motor_execute_half_cycle(motor_direction_t direction,
                                    uint8_t intensity_percent,
                                    uint32_t half_cycle_ms) {
    // Parameter validation (JPL requirement)
    if (half_cycle_ms < 100 || half_cycle_ms > 1000) {
        return ESP_ERR_INVALID_ARG;
    }

    // Motor active period: (half_cycle - 1ms)
    uint32_t motor_active_ms = half_cycle_ms - 1;
    motor_set_direction_intensity(direction, intensity_percent);
    vTaskDelay(pdMS_TO_TICKS(motor_active_ms));  // JPL-compliant delay

    // Immediate coast (GPIO write ~50ns, provides hardware dead time)
    motor_set_direction_intensity(MOTOR_COAST, 0);

    // 1ms dead time + watchdog feeding (JPL-compliant delay)
    vTaskDelay(pdMS_TO_TICKS(1));
    esp_task_wdt_reset();  // Feed watchdog during dead time

    return ESP_OK;
}
```

### Frequency Examples

| Total Cycle | Half-Cycle | Motor Active | Dead Time | Bilateral Rate | Overhead |
|-------------|------------|--------------|-----------|----------------|----------|
| 500ms | 250ms | 249ms | 1ms | 2 Hz | 0.4% |
| 1000ms | 500ms | 499ms | 1ms | 1 Hz | 0.2% |
| 2000ms | 1000ms | 999ms | 1ms | 0.5 Hz | 0.1% |

---

## Consequences

### Benefits

- **Therapeutic clarity**: Therapists configure bilateral frequency directly (0.5-2 Hz)
- **Non-overlapping guaranteed**: 1ms dead time + GPIO coast ensures safety at any cycle time
- **JPL compliance**: All timing uses `vTaskDelay()`, no busy-wait loops
- **Watchdog integration**: 1ms dead time provides TWDT feeding opportunity
- **Minimal overhead**: 1ms = 0.1-0.2% of half-cycle budget
- **Hardware protection**: GPIO write (~50ns) exceeds MOSFET turn-off time (30ns)
- **Precision timing**: ±10ms achievable with FreeRTOS scheduling
- **Simple calculation**: half_cycle = total_cycle / 2 (no complex math)

### Drawbacks

- **1ms granularity**: Cannot adjust dead time < 1ms (FreeRTOS tick limit)
- **Fixed overhead**: 1ms dead time applied to all cycle times (even if unnecessary)
- **Watchdog dependency**: Motor timing coupled to watchdog feeding
- **Asymmetric cycles**: Half-cycle = 499ms + 1ms dead time (not pure 500ms)

---

## Options Considered

### Option A: Total Cycle Time + 1ms Dead Time (Selected)

**Pros:**
- Therapist-friendly configuration (bilateral Hz)
- Simple half-cycle calculation (divide by 2)
- JPL-compliant FreeRTOS delays
- Watchdog feeding integrated naturally
- Minimal overhead (0.1-0.2%)

**Cons:**
- 1ms fixed overhead at all cycle times
- Asymmetric half-cycles (499ms + 1ms)

**Selected:** YES
**Rationale:** Best balance of therapeutic clarity, JPL compliance, and safety

### Option B: Per-Device Half-Cycle Configuration (Rejected)

**Pros:**
- Direct control over each device's timing
- No "total cycle" abstraction

**Cons:**
- Therapists think in bilateral frequency, not half-cycles
- Harder to ensure left/right symmetry
- More error-prone configuration (must manually divide)

**Selected:** NO
**Rationale:** User experience inferior, more error-prone

### Option C: Microsecond Dead Time (esp_rom_delay_us) (Rejected)

**Pros:**
- Shorter dead time (e.g., 100µs)
- Less overhead (< 0.1%)

**Cons:**
- ❌ Busy-wait loop violates JPL coding standard
- ❌ Cannot feed watchdog during microsecond delay
- ❌ Blocks other FreeRTOS tasks
- ❌ No benefit (GPIO write already provides >100ns dead time)

**Selected:** NO
**Rationale:** JPL compliance violation, no practical benefit

### Option D: No Explicit Dead Time (Rejected)

**Pros:**
- Maximum motor active time
- Simpler code

**Cons:**
- No opportunity for watchdog feeding between half-cycles
- Reduced safety margin for coast transitions
- Harder to debug timing issues

**Selected:** NO
**Rationale:** Watchdog feeding requires explicit delay between half-cycles

### Option E: Variable Dead Time Based on Cycle Length (Rejected)

**Pros:**
- Could optimize overhead for long cycles (e.g., 10ms dead time for 2000ms cycle)

**Cons:**
- Adds complexity without benefit
- 1ms sufficient for all cycle times
- Variable watchdog feeding intervals harder to verify

**Selected:** NO
**Rationale:** Complexity not justified, 1ms adequate for all cycle times

---

## Related Decisions

### Related
- [AD002: JPL Institutional Coding Standard Adoption](0002-jpl-coding-standard-adoption.md) - Mandates vTaskDelay() for timing
- [AD007: FreeRTOS Task Architecture](0007-freertos-task-architecture.md) - Motor task uses half-cycle timing
- [AD009: Bilateral Timing Implementation](0009-bilateral-timing-implementation.md) - Server/client coordination uses total cycle time
- [AD012: Dead Time Implementation Strategy](0012-dead-time-implementation-strategy.md) - Details of 1ms dead time rationale
- [AD019: Task Watchdog Timer Strategy](0019-task-watchdog-timer-strategy.md) - Watchdog feeding during dead time

---

## Implementation Notes

### Code References

- `src/motor_task.c` - `motor_execute_half_cycle()` function
- `src/ble_manager.c` - Total cycle time in BLE characteristics
- `test/single_device_demo_jpl_queued.c` - Phase 0.4 JPL-compliant timing

### Build Environment

All environments use this timing architecture (hardware-independent).

### Testing & Verification

**Timing Precision Verified:**
- ✅ Oscilloscope measurements: ±5ms deviation over 20+ minutes
- ✅ Half-cycle calculation: 500ms total → 249ms + 1ms = 250ms half-cycle
- ✅ Watchdog feeding: No TWDT timeouts during 30-minute sessions
- ✅ Non-overlapping: Motor coast verified before peer activation

**Test Cases:**
- 500ms total cycle (2 Hz): Motor active 249ms, dead time 1ms
- 1000ms total cycle (1 Hz): Motor active 499ms, dead time 1ms
- 2000ms total cycle (0.5 Hz): Motor active 999ms, dead time 1ms

**Known Issues:**
- None - timing architecture stable and verified

---

## JPL Coding Standards Compliance

- ✅ Rule #1: No dynamic memory - Timing constants statically defined
- ✅ Rule #2: Fixed loop bounds - Half-cycle loops bounded by cycle count
- ✅ Rule #5: Return value checking - vTaskDelay() return not checked (void function)
- ✅ Rule #6: No unbounded waits - vTaskDelay() has explicit timeout
- ✅ Rule #7: Watchdog compliance - esp_task_wdt_reset() in dead time
- ✅ Rule #8: Defensive logging - Timing events logged for debugging

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: AD006 (Software Architecture Decisions)
Git commit: Current working tree

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
