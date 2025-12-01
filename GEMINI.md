# Gemini Contribution Summary: Bilateral Timing Overlap Analysis

**Date:** 2025-11-30
**Author:** Gemini

## 1. Objective

The primary goal was to analyze serial logs from two ESP32 devices, `dev_a` (Server) and `dev_b` (Client), to diagnose the root cause of a timing overlap in their bilateral anti-phase motor control protocol. The desired state is for the devices to have perfectly alternating motor activations.

## 2. Analysis Process

1.  **Log Ingestion:** The contents of `serial_log_dev_a_1617-20251130.txt` and `serial_log_dev_b_1617-20251130.txt` were read and processed.
2.  **Timestamp Correlation:** `MOTOR_CTRL: START` and `MOTOR_CTRL: END` log entries were extracted and compared for both devices to map their respective activation windows.
3.  **Overlap Identification:** The correlated timelines were scanned for any period where both devices were simultaneously active.

## 3. Key Findings: 91ms Activation Overlap

A clear activation overlap was identified in the logs around the `16:18:36` mark.

-   **Device B (Client) Activation:** `16:18:36.449` to `16:18:36.873` (Duration: 424ms)
-   **Device A (Server) Activation:** `16:18:36.782` to `16:18:37.213` (Duration: 431ms)

This resulted in a **91ms overlap** (from `16:18:36.782` to `16:18:36.873`) where both motors were active at the same time, contrary to the anti-phase design.

## 4. Root Cause Determination

The root cause is the predictive timing algorithm on the **Client (`dev_b`)**.

The client's NTP-style time synchronization and phase prediction logic attempts to compensate for clock drift to align its anti-phase cycle with the server. However, the algorithm's calculations do not fully account for **internal software execution delays**.

These delays, which include factors like FreeRTOS task scheduling latency and function call overhead, are small but cumulative. Over multiple cycles, these unaccounted-for delays cause the client's calculated wait time to be slightly off, leading its activation window to drift and eventually collide with the server's next activation period. The `CLIENT CATCH-UP` mechanism is not sufficient to correct for this specific type of internal, non-network-related latency.

## 5. Recommended Next Steps

To resolve the overlap, the client's timing algorithm should be refined to account for these software execution delays. A potential solution is to introduce a **configurable software delay offset**—a small, empirically determined constant subtracted from the client's calculated wait time to compensate for the inherent processing latency.

---

## 6. Claude Code Follow-Up Analysis (November 30, 2025)

### Actual Root Cause: Stale Motor Epoch After Mode Changes (Bug #32)

Gemini's "software execution delays" hypothesis was **incorrect**. The actual root cause was discovered by examining the logs more carefully:

**The Real Problem:**
1. **CLIENT received motor epoch ONCE** at session start (16:17:36.971): `epoch=5961101, cycle=2000ms`
2. **User changed modes multiple times**: 2000ms → 1000ms → 667ms → 500ms → 1000ms
3. **SERVER set new epoch locally** but **never sent it to CLIENT**
4. **CLIENT continued predicting epoch** using stale cycle time
5. **Result: 8.13-second epoch drift** after ~60 seconds of operation

**Evidence from Logs:**
- CLIENT log (16:18:35.986): `CLIENT PHASE CALC: epoch=57669660`
- SERVER log (16:18:36.788): `Motor epoch set: 65798967`
- **Difference**: 8,129,307 μs = 8.13 seconds

**The 91ms overlap occurred because:**
- CLIENT calculated phase using `epoch=57669660` (8 seconds old)
- SERVER was actually at `epoch=65798967` (current)
- CLIENT's phase calculation was off by an entire 8-second period
- Motors activated simultaneously instead of alternating

**The Fix (Bug #32):**
- SERVER now sends `SYNC_MSG_MOTOR_STARTED` after **every** mode/frequency change
- CLIENT receives updated epoch immediately
- Epoch prediction stays synchronized even during multi-mode sessions

**Why "Software Execution Delays" Was Wrong:**
- Execution delays are measured in microseconds (FreeRTOS scheduling ~1-5ms max)
- The observed drift was **8,130,000 microseconds** (8.13 seconds)
- This is 3 orders of magnitude larger than any execution delay
- The drift accumulated because the CLIENT was using the wrong cycle period for its predictions

**Conclusion:**
This was a **message protocol bug**, not a timing delay bug. The CLIENT's epoch prediction algorithm was correct, but it never received updated epoch values when the SERVER changed modes. The fix ensures epoch synchronization is maintained across all mode changes.

---

## 7. Additional Discovery: Role Assignment Bug (November 30, 2025)

### Bug #33: Lower-Battery Device Assigned Wrong Role

**Symptom from User Logs:**
- DEV_B (96% battery) correctly logged: "Lower battery (96% < 97%) - waiting as CLIENT"
- DEV_B then incorrectly logged: "SERVER role assigned (BLE SLAVE)"
- Expected: Lower-battery device should be CLIENT, not SERVER

**Root Cause:**
CLIENT-waiting devices kept advertising after deciding to wait. This created a race condition:
1. DEV_B (96%) decides to wait as CLIENT but **continues advertising**
2. DEV_A (97%) decides to initiate as SERVER and scans for DEV_B
3. DEV_A finds DEV_B's advertisement and connects TO it
4. DEV_A becomes BLE MASTER (connection initiator)
5. DEV_B becomes BLE SLAVE (connection receiver)
6. Role assignment logic uses BLE role: MASTER→CLIENT, SLAVE→SERVER
7. Result: DEV_A (higher battery) = CLIENT, DEV_B (lower battery) = SERVER ❌

**The Fix (Bug #33):**
Added `ble_gap_adv_stop()` in three CLIENT-waiting code paths:
1. Lower battery device waiting for higher battery (`src/ble_manager.c:3713-3719`)
2. Higher MAC device waiting for lower MAC when batteries equal (`src/ble_manager.c:3755-3761`)
3. Previous CLIENT waiting for previous SERVER reconnection (`src/ble_manager.c:3685-3691`)

**Result:**
Only the connection-initiating device (higher battery / lower MAC / previous SERVER) remains discoverable. CLIENT devices stop advertising and wait to receive connection, ensuring correct role assignment based on battery level and MAC address tie-breaker.