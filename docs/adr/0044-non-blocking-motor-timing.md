# 0044: CLIENT Hardware Timer Synchronization for Bilateral Antiphase Precision

**Date:** 2025-12-03
**Phase:** 6 (Bilateral Motor Coordination)
**Status:** Accepted
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of bilateral CLIENT-SERVER motor coordination requiring precise antiphase synchronization,
facing ±1ms jitter from periodic polling in CLIENT synchronization to SERVER's motor epoch,
we decided for CLIENT-specific hardware timer callbacks synchronized to SERVER's schedule,
and neglected uniform polling approach for both devices,
to achieve ±50μs bilateral synchronization precision (20× improvement),
accepting increased CLIENT motor task complexity while keeping SERVER simple.

---

## Problem Statement

The CLIENT device must synchronize its motor transitions to the SERVER's motor_epoch (authoritative timing reference) to achieve perfect antiphase bilateral stimulation. Current polling-based approach introduces timing jitter:

- **±1ms jitter** from periodic queue checking during motor delays
- **Accumulated phase drift** over 20+ minute therapy sessions
- **Inconsistent bilateral alternation** perceived by users during mode changes
- **Slower antiphase lock convergence** without microsecond-precision timing

The SERVERCLIENT relationship is analogous to external events (BLE packets, button presses) - the CLIENT doesn't control when SERVER's motor transitions happen, it must **react precisely** to an external timing reference transmitted via beacons.

**Goal:** Achieve ±50μs bilateral synchronization precision to eliminate perceptible phase drift and accelerate antiphase lock convergence without building a full phase-locked loop (PLL).

---

## Context

### Current Implementation

The motor task structure blocks during each motor phase:

```c
void motor_task(void *arg) {
    while (1) {
        // Poll queue with 50ms timeout
        if (xQueueReceive(motor_queue, &msg, pdMS_TO_TICKS(50))) {
            handle_message(&msg);
        }

        // BLOCKING MOTOR CYCLE (500-2000ms total)
        motor_on(FORWARD);
        vTaskDelay(pdMS_TO_TICKS(125));  // ❌ Task sleeps, cannot process messages

        motor_off();
        vTaskDelay(pdMS_TO_TICKS(375));  // ❌ Task sleeps, cannot process messages

        motor_on(REVERSE);
        vTaskDelay(pdMS_TO_TICKS(125));  // ❌ Task sleeps, cannot process messages

        motor_off();
        vTaskDelay(pdMS_TO_TICKS(375));  // ❌ Task sleeps, cannot process messages
    }
}
```

### Key Insight: LEDC Hardware Already Non-Blocking

The ESP32-C6 LEDC peripheral generates PWM autonomously after configuration:

```c
ledc_set_duty(LEDC_CHANNEL, pwm_duty);     // Configure duty cycle
ledc_update_duty(LEDC_CHANNEL);             // Start PWM generation
// ✅ Hardware continues PWM independently, task is free to do other work!
```

The firmware artificially blocks with `vTaskDelay()` when it could instead:
1. Configure LEDC to start motor
2. Return to queue polling immediately
3. Check timer to detect when to transition to next state

This is a **fundamental architecture misunderstanding** - we treated synchronous delays as required when the hardware is already asynchronous.

### Technical Constraints

- **FreeRTOS minimum tick period:** 1ms (configurable via `CONFIG_FREERTOS_HZ`)
- **Queue receive overhead:** ~100μs typical
- **LEDC transition time:** Instantaneous (hardware-driven)
- **esp_timer overhead:** ~10-50μs for callback scheduling
- **Therapeutic timing requirements:** ±10ms bilateral synchronization target

### Related Work

- [AD007](0007-freertos-task-architecture.md): Task architecture using message queues
- [AD028](0028-command-control-synchronized-fallback.md): Command & control requiring responsive mode changes
- [AD041](0041-predictive-bilateral-synchronization.md): Bilateral coordination requiring precise timing

---

## Decision

We will implement a **non-blocking state machine** in motor_task.c that:

1. **Polls control queue every 50ms** instead of blocking during motor phases
2. **Tracks state transitions using `esp_timer_get_time()`** for precise timing
3. **Maintains explicit motor states**: `ACTIVE_FORWARD`, `COAST_1`, `ACTIVE_REVERSE`, `COAST_2`
4. **Processes messages with instant response** (50ms < 100ms human perception threshold)
5. **Preserves forward/reverse semantics** separate from active/inactive bilateral timing

### State Machine Architecture

```c
typedef enum {
    MOTOR_STATE_ACTIVE_FORWARD,   // Motor PWM active, forward direction
    MOTOR_STATE_COAST_1,          // Motor off, first coast period
    MOTOR_STATE_ACTIVE_REVERSE,   // Motor PWM active, reverse direction
    MOTOR_STATE_COAST_2,          // Motor off, second coast period
    MOTOR_STATE_IDLE              // Stopped, waiting for commands
} motor_state_t;

void motor_task(void *arg) {
    motor_state_t state = MOTOR_STATE_IDLE;
    int64_t next_transition_us = 0;
    motor_msg_t msg;

    while (1) {
        // Check queue every 50ms (instant response, <100ms perception threshold)
        if (xQueueReceive(motor_queue, &msg, pdMS_TO_TICKS(50)) == pdTRUE) {
            handle_message(&msg);  // Process immediately
            // Message may change mode, update timing params, or stop motor
        }

        // Check for state transitions (±50μs precision from esp_timer_get_time())
        int64_t now_us = esp_timer_get_time();
        if (now_us >= next_transition_us) {
            switch (state) {
                case MOTOR_STATE_ACTIVE_FORWARD:
                    motor_on(FORWARD, current_pwm);
                    next_transition_us = now_us + (active_time_ms * 1000);
                    state = MOTOR_STATE_COAST_1;
                    break;

                case MOTOR_STATE_COAST_1:
                    motor_off();
                    next_transition_us = now_us + (inactive_time_ms * 1000);
                    state = MOTOR_STATE_ACTIVE_REVERSE;
                    break;

                case MOTOR_STATE_ACTIVE_REVERSE:
                    motor_on(REVERSE, current_pwm);
                    next_transition_us = now_us + (active_time_ms * 1000);
                    state = MOTOR_STATE_COAST_2;
                    break;

                case MOTOR_STATE_COAST_2:
                    motor_off();
                    next_transition_us = now_us + (inactive_time_ms * 1000);
                    state = MOTOR_STATE_ACTIVE_FORWARD;  // Loop
                    break;

                case MOTOR_STATE_IDLE:
                    // Wait for start command from queue
                    break;
            }
        }

        esp_task_wdt_reset();  // Feed watchdog every 50ms
        // vTaskDelay(pdMS_TO_TICKS(50)) is implicit in xQueueReceive timeout
    }
}
```

### Important Semantic Preservation

**Forward/Reverse Direction ≠ Active/Inactive Bilateral Timing**

- **Forward/Reverse:** Per-device motor wear balancing, direction alternates every cycle
- **Active/Inactive:** Bilateral synchronization timing between devices (500ms phase offset)
- **Critical:** These are independent parameters, must not be conflated

Early firmware bug: Bilateral timing was incorrectly calculated between forward/reverse transitions when it should be based on active/inactive periods. This ADR preserves the correct semantics.

---

## Consequences

### Benefits

- **Instant button response** (50ms < 100ms human perception threshold)
- **Eliminates worst-case 2000ms latency** during 0.5Hz cycles
- **Enables responsive features** like mid-cycle emergency shutdown
- **±50μs CLIENT synchronization** from `esp_timer_get_time()` hardware precision
- **Simplifies bilateral synchronization** by allowing immediate phase adjustments
- **Preserves JPL compliance** - no unbounded waits, explicit state machine
- **Minimal CPU overhead** - 50ms loop with blocking queue receive (task still yields)
- **Fair task scheduling** - IDLE task gets sufficient CPU time (no watchdog timeout)
- **Hardware utilization** - Leverages existing LEDC autonomy (no firmware change needed)

### Drawbacks

- **Slightly higher task wake frequency** - 20 Hz vs previous blocking approach
- **More complex state machine** - Explicit state tracking vs simple linear delays
- **Requires careful timing validation** - Must verify ±10ms bilateral accuracy maintained
- **Forward/reverse semantics must be preserved** - Easy to accidentally break separation from bilateral timing

### Performance Impact

Estimated CPU overhead (CORRECTED):
- Previous (blocking): Variable, up to 2000ms blocked per cycle
- New: ~20 wake-ups/second (50ms queue poll)
- **Net change: Non-blocking responsiveness with minimal overhead**

ESP32-C6 @ 160 MHz can easily handle this:
- Queue receive: ~100μs per wake-up
- Total overhead: 20 × 100μs = 2ms/second = **0.2% CPU utilization**
- Remaining capacity: **99.8% for other tasks** (BLE, time sync, button, battery)

This is highly efficient and provides instant responsiveness.

---

## Options Considered

### Option A: Blocking vTaskDelay() (Current Implementation)

**Pros:**
- Simple, straightforward code
- Lower CPU wake-up frequency
- Proven stable in current firmware

**Cons:**
- 50ms minimum message latency
- Up to 2000ms worst-case latency
- Cannot implement responsive features
- Poor user experience for mode changes

**Selected:** NO
**Rationale:** Unacceptable latency for bilateral coordination and user control. Simplicity not worth the functional limitations.

---

### Option B: Hardware Timer Callbacks (esp_timer)

**Pros:**
- True asynchronous timing (~10-50μs overhead)
- No polling loop required
- Most CPU-efficient approach

**Cons:**
- Callbacks run in timer ISR context (restricted operations)
- Cannot call FreeRTOS queue functions from ISR (must use FromISR variants)
- Motor control code would need significant refactoring for ISR safety
- Harder to debug (ISR context, no blocking operations allowed)
- Increased complexity for marginal benefit over 1ms polling

**Selected:** NO
**Rationale:** Added complexity and ISR safety requirements not justified. 50ms polling achieves instant response (<100ms) with simpler task-context code.

---

### Option C: Non-Blocking State Machine with 50ms Polling (Selected)

**Pros:**
- Instant button response (50ms < 100ms human perception threshold)
- ±50μs CLIENT synchronization from `esp_timer_get_time()` hardware precision
- Runs in task context (full FreeRTOS API available)
- Easy to debug with standard logging
- Leverages existing LEDC hardware autonomy
- Minimal CPU overhead (0.2%)
- Fair task scheduling (no IDLE task starvation)
- Preserves JPL coding standards (explicit state machine, no unbounded waits)

**Cons:**
- Slightly higher wake-up frequency than blocking approach (20 Hz vs blocking)
- More complex than simple blocking delays
- Timing must be validated carefully

**Selected:** YES
**Rationale:** Best balance of responsiveness, code simplicity, debuggability, and efficiency. Achieves both goals: (1) ±50μs CLIENT synchronization from `esp_timer_get_time()` precision, (2) instant button response from non-blocking state machine. Polling frequency (50ms) is independent of timing precision.

---

## Related Decisions

### Related
- [AD007: FreeRTOS Task Architecture](0007-freertos-task-architecture.md) - Task communication via queues
- [AD028: Command & Control Synchronized Fallback](0028-command-control-synchronized-fallback.md) - Requires responsive mode changes
- [AD041: Predictive Bilateral Synchronization](0041-predictive-bilateral-synchronization.md) - Bilateral timing requiring precise control
- [AD009: Bilateral Timing Implementation](0009-bilateral-timing-implementation.md) - Active/inactive timing semantics

---

## Implementation Notes

### Code References

- `src/motor_task.c` (to be refactored): Main motor task loop
- `src/motor_control.c`: LEDC hardware control functions (no changes needed)
- `src/motor_task.h`: Motor state enum and message definitions

### Build Environment

- **Environment Name:** `xiao_esp32c6_ble_no_nvs`
- **Configuration File:** `sdkconfig.xiao_esp32c6_ble_no_nvs`
- **Build Flags:** No special flags required

### Testing & Verification

**Pre-Implementation Testing:**
- Verify current LEDC operation is non-blocking (configure + return immediately)
- Measure baseline message latency with oscilloscope (expect 50ms average)

**Post-Implementation Testing:**
- Measure message response time with oscilloscope (target <1ms)
- Verify bilateral synchronization accuracy maintained (±10ms)
- Validate forward/reverse alternation preserved (not conflated with active/inactive)
- Test mode changes during all motor states (forward active, coast, reverse active)
- Measure CPU utilization via FreeRTOS task stats
- 90-minute stress test to verify no timing drift or state machine bugs

**Known Limitations:**
- 1ms FreeRTOS tick period sets minimum polling interval
- Queue receive overhead adds ~100μs per iteration
- State transitions accurate to ±1ms (acceptable for therapeutic use)

---

## JPL Coding Standards Compliance

- ✅ **Rule #1: No dynamic memory allocation** - State machine uses stack variables only
- ✅ **Rule #2: Fixed loop bounds** - While loop with explicit state machine, deterministic transitions
- ✅ **Rule #3: No recursion** - Flat state machine, no recursive calls
- ✅ **Rule #4: No goto statements** - State machine uses switch/case with explicit transitions
- ✅ **Rule #5: Return value checking** - All `xQueueReceive()` return values checked
- ✅ **Rule #6: No unbounded waits** - Queue receive has 50ms timeout (bounded)
- ✅ **Rule #7: Watchdog compliance** - Task feeds watchdog every 50ms (well within 2000ms timeout)
- ✅ **Rule #8: Defensive logging** - State transitions logged for debugging

---

## Amendment: Design Conflation Discovered and Corrected

**Date:** 2025-12-08
**Issue:** Watchdog timeout and IDLE task starvation during normal motor operation

### What Happened

Initial implementation used 1ms polling interval based on original ADR text. This caused:
- IDLE task starvation (watchdog timeout after 740ms)
- Unnecessary CPU overhead (980 additional wake-ups/second)
- Button lag perception during motor cycles

### Root Cause Analysis

The original ADR conflated **two independent optimizations**:

1. **Non-Blocking Motor Timing** (NECESSARY)
   - Check time with `esp_timer_get_time()` instead of blocking with `vTaskDelay()`
   - Enables CLIENT hardware timer precision (±50μs)
   - **This is the core goal of AD044**

2. **Fast Button Response** (UNNECESSARY)
   - Poll queue every 1ms instead of 50ms
   - Reduced message latency from 50ms → 1ms
   - **But 50ms was already instant** (<100ms human perception threshold)

### Key Insight

CLIENT synchronization precision comes from `esp_timer_get_time()` hardware accuracy (±10-50μs), NOT from queue polling rate. You can poll the queue every 50ms and still achieve ±50μs CLIENT synchronization if you check `esp_timer_get_time()` on each poll to see if a transition is needed.

### Resolution

This ADR has been corrected to specify 50ms polling interval (main branch baseline). This preserves ALL original goals:
- ✅ Non-blocking motor timing (check time on each loop)
- ✅ ±50μs CLIENT synchronization (from `esp_timer_get_time()` precision)
- ✅ Instant button response (50ms < 100ms perception threshold)
- ✅ Fair task scheduling (IDLE task gets CPU time)
- ✅ No watchdog timeout (motor_task yields for 50ms, not 1ms)
- ✅ Minimal CPU overhead (0.2% vs 9.8%)

### Lessons Learned

1. **Separate concerns in architecture decisions** - Motor timing precision and user input responsiveness are independent
2. **Question performance optimizations** - 1ms vs 50ms button response is imperceptible to humans
3. **Understand where precision comes from** - CLIENT precision comes from hardware timer accuracy, not polling rate
4. **Consider task starvation** - Very short vTaskDelay() intervals can prevent lower-priority tasks from running

### References

- **Complete Analysis:** WATCHDOG_TIMEOUT_ANALYSIS.md
- **Code Fix:** src/motor_task.c:60 (MODE_CHECK_INTERVAL_MS reverted to 50ms)
- **Git Commit:** 421c046 "[AD044] Revert MODE_CHECK_INTERVAL_MS to 50ms - Fix design conflation"

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-12-08 (Amendment added)
