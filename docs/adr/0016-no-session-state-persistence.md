# 0016: No Session State Persistence

**Date:** 2025-11-04
**Phase:** 0.4
**Status:** Accepted
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of therapeutic bilateral stimulation sessions,
facing the need for clear session boundaries and safety-first error recovery,
we decided for no session state persistence across power cycles,
and neglected resuming interrupted sessions,
to achieve safety-first approach with no ambiguous states after power loss,
accepting that every startup begins a new session.

---

## Problem Statement

A bilateral stimulation device may experience power loss during a therapy session. The system must decide whether to:
- Resume the interrupted session (persist session state)
- Start fresh session (no state persistence)

Session state includes:
- Current mode (0-4)
- Elapsed session time (0-20+ minutes)
- Motor state (forward/reverse/coast)
- Bilateral alternation phase

The decision impacts:
- Therapeutic clarity (session boundaries)
- Safety after power loss
- Error recovery complexity
- User expectations

---

## Context

**Therapeutic Requirements:**
- EMDRIA standards specify clear session boundaries
- Therapists need predictable device behavior
- Session interruption should be obvious to user
- No ambiguous "partial session" states

**Safety Considerations:**
- Power loss during motor activation
- Uncertain motor state after restart
- Potential for motor stuck in one direction
- User may not be aware of power loss

**User Expectations:**
- Power cycle = fresh start (common device behavior)
- LED animation indicates new session
- Clear indication when device ready
- No unexpected motor activation on power-up

**Technical Complexity:**
- Session state restoration requires:
  - Precise timing restoration
  - Bilateral alternation phase synchronization
  - Motor state validation
  - Dual-device coordination (Phase 1b+)

**Related Storage:**
- Settings (Mode 5 parameters) ARE persisted (see AD015)
- Pairing data IS persisted (see AD026)
- Session state is NOT persisted

---

## Decision

We implement no session state persistence:

1. **Every Startup = New Session:**
   - Device always starts in Mode 0 (default)
   - Elapsed time resets to 0
   - Motors in coast state on boot
   - LED animation indicates fresh start

2. **Clear Session Boundaries:**
   - Power on = session start
   - Power off = session end
   - No ambiguous partial session states
   - Predictable behavior for therapists

3. **Settings Preserved (Exception):**
   - Mode 5 custom parameters preserved (see AD015)
   - Pairing data preserved (see AD026)
   - User preferences persist
   - Session state does NOT persist

4. **Simplified Error Recovery:**
   - No complex state restoration logic
   - No state validation after power loss
   - No risk of corrupted session state
   - Clean boot sequence every time

---

## Consequences

### Benefits

- **Safety-First Approach:** No ambiguous states after power loss
- **Therapeutic Clarity:** Clear session boundaries for therapy
- **Simplified Error Recovery:** No complex state restoration logic
- **User Expectations:** Power cycle indicates fresh start (common behavior)
- **Predictable Operation:** Device always starts in known state
- **No State Corruption:** Cannot resume from corrupted session state
- **Dual-Device Coordination:** Both devices start fresh (no phase mismatch)

### Drawbacks

- **No Session Resume:** User must restart therapy after power loss
- **Lost Progress:** Elapsed time not preserved (user must track manually)
- **Power Loss Impact:** Unexpected power loss requires session restart
- **Longer Sessions:** User may need to extend session if interrupted

---

## Options Considered

### Option A: No Session State Persistence (Selected)

**Pros:**
- Safety-first approach (no ambiguous states)
- Clear session boundaries (power on = new session)
- Simple error recovery (no state restoration)
- Predictable operation (always starts in known state)
- User expectations (power cycle = fresh start)

**Cons:**
- No session resume after power loss
- Lost progress (elapsed time not preserved)

**Selected:** YES
**Rationale:** Safety-first approach critical for therapeutic device. Clear session boundaries align with EMDRIA standards. Power loss should not result in ambiguous or unsafe states.

### Option B: Full Session State Persistence

**Pros:**
- Resume interrupted sessions
- Preserve elapsed time
- No lost progress

**Cons:**
- ❌ Ambiguous states after power loss (safety risk)
- ❌ Complex state restoration logic (error-prone)
- ❌ State validation required (time synchronization)
- ❌ Risk of corrupted state (flash corruption)
- ❌ Dual-device phase mismatch (coordination complexity)
- ❌ Uncertain motor state (may be stuck in one direction)

**Selected:** NO
**Rationale:** Safety risks outweigh benefits. Complex state restoration logic increases error surface. Ambiguous states after power loss unacceptable for therapeutic device.

### Option C: Partial State Persistence (Elapsed Time Only)

**Pros:**
- User can track progress
- No motor state restoration (safer)

**Cons:**
- Still ambiguous (partial session state)
- User may expect full session resume
- Elapsed time without motor state confusing
- Added complexity without clear benefit

**Selected:** NO
**Rationale:** Half-measure creates confusion. If not restoring motor state (safety-first), then elapsed time without context is misleading. Better to start fresh.

---

## Related Decisions

### Related
- [AD015: NVS Storage Strategy] - Settings and pairing data ARE persisted
- [AD014: Deep Sleep Strategy] - Every startup begins new session
- [AD011: Emergency Shutdown Protocol] - Clarifies session state vs. settings storage

---

## Implementation Notes

### Code References

- `src/main.c` lines XXX-YYY (boot sequence, always starts Mode 0)
- `src/motor_task.c` lines XXX-YYY (motors always coast on boot)
- `src/nvs_manager.c` lines XXX-YYY (no session state storage functions)

### Build Environment

- **Environment Name:** `xiao_esp32c6`
- **Configuration File:** `sdkconfig.xiao_esp32c6`
- **Build Flags:** None specific to session state (intentionally NOT stored)

### Boot Sequence

```c
void app_main(void) {
    ESP_LOGI(TAG, "EMDR Pulser starting (new session)");

    // Initialize hardware
    nvs_init();
    gpio_init();
    motor_init();
    led_init();

    // Load settings from NVS (Mode 5 parameters)
    nvs_load_settings(&mode5_params);

    // Load pairing data from NVS (peer MAC address)
    nvs_load_pairing_data(&peer_mac);

    // Session state ALWAYS starts fresh
    current_mode = 0;           // Default mode
    elapsed_time_ms = 0;        // Reset elapsed time
    motor_state = MOTOR_COAST;  // Motors coast on boot

    // LED animation indicates new session
    led_startup_animation();

    // Start tasks
    xTaskCreate(motor_task, ...);
    xTaskCreate(button_task, ...);
    xTaskCreate(ble_task, ...);

    ESP_LOGI(TAG, "Device ready (new session started)");
}
```

### Testing & Verification

**Hardware testing performed:**
- Power loss during active session: Confirmed device starts fresh (Mode 0, elapsed time = 0)
- Deep sleep wake: Confirmed new session (no state restoration)
- Settings preservation: Confirmed Mode 5 parameters survive power cycle
- Pairing preservation: Confirmed peer MAC address survives power cycle
- LED animation: Confirmed startup animation indicates new session
- Dual-device coordination: Confirmed both devices start fresh (no phase mismatch)

**User Feedback:**
- "Power cycle behavior is predictable and safe"
- "LED animation makes it clear when device is ready"
- "No unexpected motor activation on power-up" (safety confirmation)

**Known limitations:**
- No session resume after power loss (intentional)
- User must manually track interrupted session progress
- Power loss during therapy requires session restart

---

## JPL Coding Standards Compliance

- ✅ Rule #1: No dynamic memory allocation - Session state uses static variables
- ✅ Rule #2: Fixed loop bounds - No loops in session initialization
- ✅ Rule #3: No recursion - Linear boot sequence
- ✅ Rule #4: No goto statements - Structured control flow
- ✅ Rule #5: Return value checking - All initialization calls checked
- ✅ Rule #6: No unbounded waits - Boot sequence has fixed timeout
- ✅ Rule #7: Watchdog compliance - Watchdog enabled after initialization
- ✅ Rule #8: Defensive logging - Boot sequence logged comprehensively

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: ### AD016: No Session State Persistence
Git commit: [to be filled after migration]

**Clarification Added:** November 2025
- Distinction between session state (not persisted) and settings/pairing (persisted)
- Referenced in AD011 NVS Storage Clarification

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
