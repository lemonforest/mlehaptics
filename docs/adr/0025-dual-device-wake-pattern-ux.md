# 0025: Dual-Device Wake Pattern and UX Design

**Date:** 2025-11-01
**Phase:** 1
**Status:** Accepted
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of dual-device bilateral stimulation workflow,
facing user coordination difficulty with 2-second wake hold requirement,
we decided for instant button press wake with no hold required,
and neglected 2-second or 1-second wake hold approaches,
to achieve natural two-handed simultaneous wake for both devices,
accepting deep sleep itself provides sufficient accidental wake protection.

---

## Problem Statement

Original design specified 2-second button hold to wake from deep sleep. However, hardware testing with dual-device use case revealed this creates poor user experience:
- User must coordinate 2-second hold on BOTH devices simultaneously
- Difficult to synchronize without visual feedback
- Creates frustration and delays session start
- Hardware already supports instant wake via ESP32-C6 ext1 (per AD023)

---

## Context

**Hardware Capabilities:**
- ESP32-C6 ext1 wake already supports instant wake (level-triggered on GPIO LOW)
- AD023 wait-for-release pattern unchanged (applies to shutdown, not wake)
- No firmware changes needed beyond removing 2-second wake hold logic

**User Experience Testing:**
- Two-handed button press on dual devices is natural gesture
- Coordinating 2-second hold on both devices simultaneously is frustrating
- Users expect instant response when pressing power/wake button

**Safety Considerations:**
- Device is in deep sleep (intentional state)
- User must physically press button to wake (intentional action)
- Accidental wake requires device in pocket + external pressure (very rare)

---

## Decision

We will implement instant button press to wake from deep sleep (no hold required).

**Button Hold Sequence (Updated):**
```
Wake from sleep: Instant press (no hold)
0-5 seconds:     Normal hold, no action
5 seconds:       Emergency shutdown ready (purple LED blink via therapy light)
5-10 seconds:    Continue holding (purple blink continues, release triggers shutdown)
10 seconds:      NVS clear triggered (GPIO15 solid on, only first 30s of boot per AD013)
Release:         Execute action (shutdown at 5s+, NVS clear at 10s+)
```

**GPIO15 LED Indication for NVS Clear:**
- GPIO15 status LED turns solid on at 10-second hold mark
- Only active during first 30 seconds of boot (per AD013 security window)
- Clear visual indication distinct from purple therapy light blink
- Prevents accidental NVS clear during therapy sessions

**Dual-Device Simultaneous Wake Workflow:**
1. Both devices in deep sleep
2. User presses button on both devices (natural two-handed press)
3. Both devices wake instantly (< 100ms)
4. Devices discover each other via BLE (< 30s)
5. Session ready to begin

---

## Consequences

### Benefits

- **Instant response:** Professional, responsive UX feels natural
- **Dual-device friendly:** Natural two-handed simultaneous wake
- **Hardware lessons applied:** Spec updated based on real testing
- **Safety preserved:** Emergency shutdown still protected by 5s hold
- **Clear NVS indication:** GPIO15 solid on distinct from purple blink
- **Simple implementation:** Hardware already supports instant wake
- **No synchronization difficulty:** Users don't need to time holds

### Drawbacks

- **Potential accidental wake:** Device in pocket could wake from external pressure (very rare, acceptable)
- **No hold confirmation:** User doesn't "commit" to wake action (acceptable for instant response UX)

---

## Options Considered

### Option A: Keep 2-Second Wake Hold

**Pros:**
- Prevents accidental wake
- User "commits" to wake action

**Cons:**
- Poor UX for dual-device operation
- Difficult synchronization between devices
- Hardware already supports instant wake (wasted capability)

**Selected:** NO
**Rationale:** User experience testing revealed coordination difficulty outweighs accidental wake protection

### Option B: 1-Second Wake Hold (Compromise)

**Pros:**
- Shorter than 2s (easier to synchronize)
- Some accidental wake protection

**Cons:**
- Still requires synchronization between devices
- Adds complexity without significant benefit over instant wake

**Selected:** NO
**Rationale:** Doesn't solve coordination problem, adds unnecessary delay

### Option C: Instant Wake with Accidental Press Protection (CHOSEN)

**Pros:**
- Natural two-handed button press for dual devices
- Fast, intuitive user experience
- Deep sleep itself prevents most accidental wake scenarios
- Natural use case - user intends to wake device when pressing button

**Cons:**
- Possible accidental wake if device in pocket (very rare)

**Selected:** YES
**Rationale:** Best balance of user experience and functionality

---

## Related Decisions

### Related
- **AD023: Deep Sleep Wake State Machine** - Wait-for-release pattern applies to sleep entry, not wake
- **AD013: NVS Security Window** - 10s hold for NVS clear only works in first 30s of boot
- **AD026: BLE Automatic Role Recovery** - Fast wake enables quick dual-device pairing

### Supersedes
- Original 2-second wake hold specification in early requirements

---

## Implementation Notes

### Code References

- **Button Task:** `test/single_device_demo_jpl_queued.c` button_task (instant wake logic)
- **Sleep Entry:** AD023 wait-for-release pattern (unchanged)

### Build Environment

- **Environment Name:** All production environments
- **Hardware:** Seeed XIAO ESP32-C6 with button on GPIO1

### Testing & Verification

**Hardware Test Procedure:**
- Press both device buttons simultaneously
- Measure wake latency: < 100ms from button press to CPU active
- BLE discovery: < 30s from wake to paired
- NVS clear test: GPIO15 solid on during 10s hold (first 30s only)

**Accidental Wake Testing:**
- Device in pocket test: Minimal risk (requires sustained GPIO1 LOW)
- Device on table: No accidental wake (button requires deliberate press)

**Power Consumption Verified:**
- Deep sleep: <1mA
- Wake latency: <100ms
- First BLE advertisement: <2s after wake

---

## JPL Coding Standards Compliance

- ✅ Rule #1: No dynamic memory allocation - Uses hardware ext1 wake
- ✅ Rule #2: Fixed loop bounds - Deterministic wake behavior
- ✅ Rule #3: No recursion - Linear wake flow
- ✅ Rule #6: No unbounded waits - Hardware wake (no software polling)
- ✅ Deterministic wake behavior - Level-triggered ext1
- ✅ Predictable timing - <100ms wake latency

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: AD025
Git commit: (phase 1 implementation)

**Documentation Updates:**
- UI001 in requirements_spec.md: Updated to reflect instant wake
- FR001: Added automatic role recovery after 30s timeout
- FR003: Added automatic session start, background pairing
- FR004: Clarified fire-and-forget emergency shutdown
- PF002: Removed obsolete wake time specification

**Security Considerations:**

**NVS Clear Protection (Unchanged):**
- 10-second hold required (prevents accidental clear)
- Only works in first 30 seconds after boot (AD013)
- GPIO15 solid on provides clear warning
- After 30s boot window, 10s hold does nothing (safe for therapy sessions)

**Emergency Shutdown (Unchanged):**
- 5-second hold required (prevents accidental shutdown during therapy)
- Purple LED blink provides visual countdown
- Wait-for-release pattern ensures clean deep sleep entry (AD023)

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
