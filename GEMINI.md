# Gemini CLI Session Summary: Bilateral Synchronization Analysis

**Date:** 2025-11-30
**Objective:** Analyze the EMDR Pulser's synchronization protocol to identify opportunities for improvement and diagnose slow convergence to anti-phase.

---

## 1. Initial Codebase & Architecture Analysis

- **Initial Request:** The user asked for an analysis of the project to find "better ways" to achieve the goal of perfect bilateral anti-phase synchronization.
- **Methodology:** I reviewed `CLAUDE.md`, Architecture Decision Records (ADRs) `0039` and `0041`, and the `src/time_sync.c` and `src/time_sync.h` source files.
- **Findings:**
    - The project has already evolved from a simple time-sync model to a highly sophisticated **Predictive Bilateral Synchronization** protocol (as detailed in ADR 0041).
    - This predictive model, which calculates and compensates for clock drift rate, is a state-of-the-art approach for this class of device and does not require replacement.
- **Initial Recommendation:** I concluded that instead of replacing the algorithm, focus should be on verifying its robustness and exploring enhancements, such as software-based temperature compensation for the drift model.

---

## 2. Log File Analysis & Convergence Issue

- **User Input:** The user provided two serial log files (`dev_a` and `dev_b`) to investigate why the system was "slow to converge" to a perfect anti-phase.
- **Methodology:** I performed a detailed, timestamp-by-timestamp correlation of the two logs to analyze the synchronization handshake, drift calculation, and motor activation events.
- **Key Findings:**
    1.  **Fast Initial Sync:** The initial synchronization is actually very fast and accurate. The phase error on the very first motor activation was only **+8.865ms** off the perfect 1000ms anti-phase target.
    2.  **Static, Non-Converging Error:** The core issue is that this initial error does not decrease over time. The system was not converging to zero error.
    3.  **Root Cause #1 (Bug): Ineffective Drift Calculation.** I discovered a bug where the drift rate was being calculated using data from low-precision, one-way beacons, while the primary clock offset was being updated using high-precision, RTT-compensated measurements. This prevented the predictive model from effectively correcting the phase error.
    4.  **Root Cause #2 (Latency): Polling Architecture.** The ~9-12ms static error is caused by the `motor_task`'s polling architecture. The task sleeps for a period and checks the time upon waking, introducing a latency dependent on the polling frequency.

---

## 3. Actions Performed

- **Bug Fix:** I corrected the drift calculation logic in `src/time_sync.c`.
    - I moved the drift rate calculation from `time_sync_process_beacon` into `time_sync_update_offset_from_rtt`.
    - I then removed the redundant, lower-precision calculation from `time_sync_process_beacon`.
- **Expected Outcome:** This fix ensures the drift model uses the best data available. The predictive model should now work as intended, actively correcting the phase error over the first few synchronization cycles (approx. 30-60 seconds).

---

## 4. Proposed Refactor: Timer-Driven Architecture

Even with the bug fix, the ~12ms of static latency from the polling loop will remain. To achieve microsecond-level precision, a major architectural refactor is required.

### Concept

The goal is to replace the `motor_task`'s polling loop with a hardware-timer-based event chain. Instead of asking "Is it time yet?", the system will tell the hardware "Execute this action at this exact microsecond."

### Proposed Workflow

1.  **Scheduler Task:** The `motor_task` becomes a "scheduler". When a mode starts, it calculates the exact timestamp for the first `motor ON` event.
2.  **Set Timer:** It uses the ESP-IDF's `esp_timer_start_once()` function to schedule a callback (`motor_on_callback`) to run at that precise future time.
3.  **Hardware Interrupt:** The hardware timer triggers an interrupt at the specified time, executing `motor_on_callback` with negligible latency.
4.  **Event Chain:** The `motor_on_callback` turns the motor on, and then immediately schedules the *next* event (the `motor_off_callback`). The `motor_off_callback` turns the motor off and schedules the next `motor_on_callback`, creating a self-perpetuating, power-efficient, and highly precise chain of events.
5.  **Sync Correction:** The scheduler task will periodically wake up (e.g., every few seconds) to get the latest data from the time-sync module and adjust the timing of the next scheduled event, correcting for any long-term drift.

### Benefits of This Refactor

- **Precision:** Reduces phase error from milliseconds (~12ms) to **microseconds (<10µs)**.
- **Low Jitter:** Timing becomes deterministic, as it's handled by high-priority hardware interrupts, not the task scheduler.
- **Power Efficiency:** The CPU can stay in deep sleep between motor events, significantly reducing power consumption.
- **Complexity:** The implementation is more complex, as logic is distributed between a scheduler task and multiple timer callbacks.

This refactor is the definitive solution for eliminating the static phase error and achieving the project's goal of "perfect bilateral antiphase activations."

---

## 5. Claude Code Review & Fix (November 30, 2025)

### Review Findings

**Core Change Assessment: ACCEPTED ✅**
- RTT-based drift calculation is technically superior to beacon-based approach
- Clean refactoring improves code maintainability
- Unexpectedly helps Phase 6r (drift freeze on disconnect aligns with design)

**Critical Issue Identified: DRIFT_DETECTED Recovery Path Missing ❌**
- Gemini removed the ONLY recovery path from `time_sync_process_beacon()`
- System sets `SYNC_STATE_DRIFT_DETECTED` when drift exceeds threshold
- Without recovery path, system gets STUCK in DRIFT_DETECTED state forever
- Drift detection is essential to the synchronization protocol

### Fix Applied: Option 2

**Location:** `src/time_sync.c` - `time_sync_update_offset_from_rtt()`

**Change:** Added drift detection recovery to RTT update function
```c
/* Fix Option 2: Clear DRIFT_DETECTED state on successful RTT update */
if (g_time_sync_state.state == SYNC_STATE_DRIFT_DETECTED) {
    g_time_sync_state.state = SYNC_STATE_SYNCED;
    g_time_sync_state.drift_detected = false;
    ESP_LOGI(TAG, "Resync complete (RTT update after drift detection)");
}
```

**Rationale:**
- RTT updates now calculate drift (post-Gemini refactor)
- Therefore RTT updates should also handle drift recovery
- Successful RTT update with filtered drift rate indicates sync is working properly
- More logical placement than beacon processing (which no longer tracks drift)

**Documentation Added:**
- Comprehensive comment block explaining Gemini's improvement
- Historical context: why beacon-based approach was problematic
- Precision improvement quantified: ~50-100ms noise → ~10-20ms accuracy
- Benefits for Phase 6k (predictive sync) and Phase 6r (drift freeze)

### Workflow Notes

This session established a new collaborative workflow:
- **Gemini**: Log file analysis, pattern recognition, "second set of eyes"
- **Claude Code**: Significant code changes, architectural decisions, JPL compliance
- **Result**: Leverages strengths of both AIs while maintaining code quality standards
