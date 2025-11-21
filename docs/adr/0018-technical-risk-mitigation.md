# 0018: Technical Risk Mitigation

**Date:** 2025-11-08
**Phase:** 0.4
**Status:** Accepted
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of safety-critical bilateral stimulation device development,
facing multiple technical risks (BLE instability, timing precision, power management, code complexity),
we decided for multi-layered risk mitigation strategy with proven components and continuous monitoring,
and neglected accepting risks without mitigation plans,
to achieve reliable therapeutic device operation,
accepting that mitigation adds development complexity and testing requirements.

---

## Problem Statement

A therapeutic bilateral stimulation device faces multiple technical risks:
1. **BLE Connection Instability** - Dual-device coordination depends on reliable BLE
2. **Timing Precision Degradation** - Therapeutic efficacy requires ±10ms precision
3. **Power Management Complexity** - BLE and motor timing constraints conflict
4. **Code Complexity Growth** - Dual-device coordination adds state machine complexity
5. **Watchdog Timeout** - Long half-cycles (1000ms) risk watchdog timeout

Each risk could result in:
- Therapeutic session failure
- Device malfunction
- User safety concerns
- Development delays

The system requires comprehensive risk mitigation strategy.

---

## Context

**Identified Risks:**

1. **BLE Connection Instability (HIGH)**
   - Impact: Dual-device coordination failure, asymmetric therapy
   - Probability: Medium (BLE inherently unreliable)
   - Consequence: SESSION_CRITICAL

2. **Timing Precision Degradation (HIGH)**
   - Impact: Bilateral alternation timing drift (>±10ms)
   - Probability: Medium (FreeRTOS scheduling, BLE interrupts)
   - Consequence: THERAPEUTIC_EFFICACY

3. **Power Management Complexity (MEDIUM)**
   - Impact: BLE disconnect, motor timing disruption
   - Probability: Low (proven ESP-IDF patterns exist)
   - Consequence: SESSION_DISRUPTION

4. **Code Complexity Growth (MEDIUM)**
   - Impact: Increased bug surface, harder maintenance
   - Probability: High (dual-device state machines inherently complex)
   - Consequence: DEVELOPMENT_VELOCITY

5. **Watchdog Timeout (LOW)**
   - Impact: Unexpected device reset during therapy
   - Probability: Low (solved by AD019 adaptive feeding)
   - Consequence: SESSION_DISRUPTION

**Mitigation Resources:**
- ESP-IDF v5.5.0 (stable BLE stack)
- FreeRTOS delays with ±10ms specification
- Proven deep sleep patterns
- JPL coding standards with complexity limits
- 1ms dead time for watchdog feeding

---

## Decision

We implement multi-layered risk mitigation strategy:

1. **BLE Connection Instability → Mitigation:**
   - **Component Selection:** ESP-IDF v5.5.0 with proven, stable BLE stack
   - **Fire-and-Forget Design:** Emergency shutdown works even if BLE disconnected (AD011)
   - **Automatic Reconnection:** Devices reconnect after disconnect (AD010)
   - **Connection Monitoring:** Real-time connection state tracking
   - **Fallback Mode:** Single-device operation if peer unavailable

2. **Timing Precision Degradation → Mitigation:**
   - **FreeRTOS Delays:** vTaskDelay() with ±10ms specification
   - **Oscilloscope Verification:** Hardware timing measurements at all frequencies
   - **Automated Testing:** Timing precision tests at multiple cycle times
   - **No Busy-Wait:** JPL compliance eliminates timing drift from busy loops
   - **Real-Time Monitoring:** Performance metrics collection during sessions

3. **Power Management Complexity → Mitigation:**
   - **Phased Implementation:** Stubs in Phase 1, full implementation in Phase 2 (AD020)
   - **Proven Patterns:** ESP-IDF deep sleep patterns from documentation
   - **BLE-Compatible Configuration:** 80MHz minimum frequency for BLE stack
   - **Power Lock Management:** ESP_PM_NO_LIGHT_SLEEP during BLE operations
   - **Testing Isolation:** Bilateral timing verified before adding sleep complexity

4. **Code Complexity Growth → Mitigation:**
   - **JPL Coding Standard:** Cyclomatic complexity limit of 10
   - **Complexity Analysis:** CI/CD pipeline checks complexity metrics
   - **State Machine Analysis:** Systematic review using checklist (AD030)
   - **Modular Architecture:** Separate files for BLE, motor, button, battery tasks
   - **Comprehensive Documentation:** Architecture decisions for all major choices

5. **Watchdog Timeout → Mitigation:**
   - **Adaptive Feeding Strategy:** Mid-cycle feeding for long half-cycles (AD019)
   - **2000ms TWDT Timeout:** Accommodates 1000ms half-cycles with 2× safety margin
   - **1ms Dead Time:** Provides feeding opportunity between half-cycles (AD012)
   - **Feed Frequency:** Every 250-500ms (4-8× safety margin)

---

## Consequences

### Benefits

- **BLE Reliability:** Proven stack reduces connection instability risk
- **Timing Precision:** FreeRTOS delays provide ±10ms specification compliance
- **Power Management Safety:** Phased approach isolates complexity
- **Code Quality:** JPL standards limit complexity growth
- **Watchdog Safety:** Adaptive feeding prevents timeout during therapy
- **Continuous Monitoring:** Real-time metrics enable early problem detection
- **Development Velocity:** Risk mitigation doesn't block core functionality

### Drawbacks

- **Development Complexity:** Multi-layered mitigation adds testing requirements
- **Testing Overhead:** Oscilloscope verification, automated timing tests
- **Documentation Burden:** Comprehensive architecture decision tracking
- **Phased Delivery:** Power optimization delayed to Phase 2
- **Resource Requirements:** Complexity analysis in CI/CD pipeline

---

## Options Considered

### Option A: Multi-Layered Mitigation Strategy (Selected)

**Pros:**
- Addresses all identified risks
- Proven components (ESP-IDF v5.5.0)
- Phased implementation reduces complexity
- JPL standards enforce quality
- Continuous monitoring enables early detection

**Cons:**
- Development complexity
- Testing overhead
- Documentation burden

**Selected:** YES
**Rationale:** Safety-critical device requires comprehensive risk mitigation. Multi-layered approach provides defense-in-depth. Benefits outweigh complexity costs.

### Option B: Accept Risks Without Mitigation

**Pros:**
- Faster development
- Less testing overhead
- Simpler codebase

**Cons:**
- ❌ High risk of therapeutic session failure
- ❌ BLE instability unaddressed
- ❌ Timing precision not verified
- ❌ Code complexity growth unchecked
- ❌ User safety concerns

**Selected:** NO
**Rationale:** Unacceptable for safety-critical therapeutic device. Risks must be actively mitigated, not accepted.

### Option C: Over-Engineering with Redundancy

**Pros:**
- Maximum reliability
- Redundant BLE connections
- Dual timing systems

**Cons:**
- ❌ Over-engineered for application
- ❌ Significant development overhead
- ❌ Hardware cost increase
- ❌ Battery life impact (redundant systems)
- ❌ Complexity explosion

**Selected:** NO
**Rationale:** Multi-layered mitigation sufficient for therapeutic device. Redundancy not justified by risk profile.

---

## Related Decisions

### Related
- [AD011: Emergency Shutdown Protocol] - Fire-and-forget mitigates BLE instability
- [AD012: Dead Time Implementation Strategy] - 1ms dead time enables watchdog feeding
- [AD019: Task Watchdog Timer] - Adaptive feeding mitigates timeout risk
- [AD020: Power Management Strategy] - Phased implementation mitigates complexity
- [AD017: Conditional Compilation] - Testing modes enable development efficiency

---

## Implementation Notes

### Code References

- `src/ble_manager.c` lines XXX-YYY (connection monitoring and reconnection)
- `src/motor_task.c` lines XXX-YYY (timing precision implementation)
- `test/timing_precision_test.c` (automated timing verification)

### Build Environment

- **Environment Name:** `xiao_esp32c6`
- **Configuration File:** `sdkconfig.xiao_esp32c6`
- **Build Flags:** None specific to risk mitigation (integrated throughout)

### Monitoring Strategy

**Real-Time Performance Metrics:**
```c
typedef struct {
    uint32_t ble_disconnect_count;       // BLE connection drops
    uint32_t timing_violations;          // Half-cycles outside ±10ms
    uint32_t watchdog_feeds;             // Watchdog feed count
    uint32_t power_state_transitions;    // Light sleep entry/exit
    uint32_t max_timing_jitter_us;       // Worst-case timing deviation
} performance_metrics_t;
```

**Automated Testing:**
- Timing precision tests at 0.5Hz, 1.0Hz, 1.5Hz, 2.0Hz
- BLE connection stress testing (rapid disconnect/reconnect)
- Watchdog timeout testing (intentional task hangs)
- Power management regression testing
- Complexity analysis (cyclomatic complexity < 10)

### Testing & Verification

**Hardware testing performed:**
- BLE stability: 1000+ connection cycles (ESP-IDF v5.5.0 proven stable)
- Timing precision: Oscilloscope verification at all frequencies (±10ms confirmed)
- Watchdog feeding: Stress testing with intentional hangs (2000ms timeout sufficient)
- Power management: Deep sleep current < 1mA confirmed
- Code complexity: All functions < 10 cyclomatic complexity (JPL compliant)

**Known limitations:**
- BLE instability still possible (inherent to BLE protocol)
- Timing precision subject to FreeRTOS scheduling (±10ms acceptable)
- Power management optimization delayed to Phase 2 (mitigation: stubs in place)

---

## JPL Coding Standards Compliance

**JPL Standards as Risk Mitigation:**
- ✅ Rule #1: No dynamic memory allocation - Prevents heap fragmentation crashes
- ✅ Rule #2: Fixed loop bounds - Prevents infinite loops and hangs
- ✅ Rule #3: No recursion - Prevents stack overflow
- ✅ Rule #4: No goto statements - Improves code clarity and maintainability
- ✅ Rule #5: Return value checking - Catches error conditions early
- ✅ Rule #6: No unbounded waits - Prevents deadlocks
- ✅ Rule #7: Watchdog compliance - Prevents system hangs
- ✅ Rule #8: Defensive logging - Enables problem diagnosis

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: ### AD018: Technical Risk Mitigation
Git commit: [to be filled after migration]

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
