# UTLP Statistical Simulation: Genesis Reset + Antiphase Lock

## Summary

This simulation explores what happens when a Genesis node resets and returns with a phase offset, potentially causing "antiphase lock" where bilateral stimulation motors fire simultaneously instead of alternating.

**Key Finding:** The protocol is **resilient** to this attack vector, but only if a replacement Genesis is promoted during the outage.

---

## Scenario 1: Simple Genesis Reset (No Promotion)

**Setup:**
- 3 nodes: A (Genesis), B (Follower), C (Follower)
- A goes offline for 30 seconds
- B and C remain as stratum-2 (no promotion)
- A returns with 500ms offset

**Result:**
```
T=91:  AA:01(s1,a1500ms) AA:02(s2,a96000ms) AA:03(s2,a96000ms)
T=101: AA:01(s1,a11500ms) AA:02(s2,a11500ms) AA:03(s2,a11500ms)
```

**What Happened:**
1. A returns as stratum-1 with fresh atomic time (500ms offset)
2. B and C are still stratum-2 (followers)
3. **Innate Immunity triggers**: stratum-1 < stratum-2, so B and C adopt A's time
4. The entire swarm synchronizes to A's **corrupted time**

**Conclusion:** The swarm converges, but to the WRONG reference. The 500ms offset is now the new truth.

---

## Scenario 2: Promoted Genesis (Realistic)

**Setup:**
- 3 nodes: A (Genesis), B (Follower), C (Follower)
- A goes offline for 30 seconds
- **B promotes to Genesis** after holdover expires
- A returns with 500ms offset

**Result:**
```
T=101: stratums={'AA:01': 2, 'AA:02': 1, 'AA:03': 2}
       AA:02 atomic_time=105000000us (running for 100s)
       AA:01 atomic_time=500000us (just rebooted)
```

**What Happened:**
1. A returns as stratum-1, B is already stratum-1
2. **Same-stratum: "First Born Wins"** triggers
3. B's atomic time (105M μs) > A's atomic time (500K μs)
4. B is "elder" → A defers and demotes to stratum-2
5. Swarm preserves correct timing

**Conclusion:** The "First Born Wins" tie-breaker correctly rejects freshly-rebooted nodes.

---

## Critical Design Insight

### The Holdover Promotion Problem

If no node promotes to Genesis during an outage, the returning (corrupted) Genesis wins by default:

| Scenario | Who Promotes? | Outcome |
|----------|---------------|---------|
| Short outage (< holdover) | Nobody | Returning Genesis wins, may corrupt swarm |
| Long outage (> holdover) | Healthiest follower | "First Born Wins" rejects new Genesis |

**Recommendation:** Holdover timer must be short enough that a replacement Genesis is always promoted before the original could return.

Typical values:
- **Holdover timeout:** 60 seconds (current S2 default)
- **Reset recovery time:** 5-10 seconds (ESP32 reboot)

With these values, a returning Genesis will always encounter a promoted replacement, triggering "First Born Wins" protection.

---

## The Antiphase Lock Vector

**Attack Pattern:**
1. Attacker controls Genesis node
2. Attacker resets Genesis with crafted offset (e.g., 500ms for 1Hz → antiphase)
3. If no replacement Genesis exists, swarm adopts corrupted time
4. Bilateral stimulation fires both sides simultaneously

**Mitigation (already implemented):**
- "First Born Wins" rejects nodes with younger atomic times
- A reset node has atomic_time ≈ 0, which is always younger than established nodes

**Remaining Risk:**
- Very short outages (< 60s) before holdover expires
- Attacker could theoretically time the reset to return before promotion

---

## Parameter Sweep Results

All initial offsets converge to <10μs final offset:

| Initial Offset | Final Offset | Notes |
|----------------|--------------|-------|
| 0ms | 8μs | Best case |
| 50ms | 8μs | Small drift |
| 250ms | 8μs | Quarter phase |
| 500ms | 8μs | Antiphase |
| 750ms | 8μs | 3/4 phase |
| 1000ms | 8μs | Full cycle |

**Interpretation:** Innate Immunity path dominates. The swarm will ALWAYS converge, but the question is: to whose time?

---

## Protocol Recommendations

### 1. Mandatory Holdover Promotion
Followers MUST promote to Genesis after holdover expires (e.g., 60s without Genesis beacons).

### 2. "First Born Wins" is Correct
Comparing atomic times (not MACs) correctly favors established nodes over rebooted ones.

### 3. Atomic Time Starts at Boot
After reset, atomic_time = local_clock + offset. If offset starts at 0, a fresh node has small atomic time.

### 4. Consider: Atomic Time Epoch
For extra protection, could embed boot count or NVS counter in atomic time to make rebooted nodes definitively "younger" even if clocks drift.

---

## Test Vectors for Hardware Validation

1. **Basic convergence:** Two nodes, different boot times, verify they sync
2. **Genesis reset:** 3 nodes, reset Genesis, verify promoted Genesis wins
3. **Antiphase injection:** Reset Genesis with known offset, verify rejection
4. **Holdover promotion:** Remove Genesis, verify follower promotes after timeout

---

## Implementation Gap Identified

### Missing: Holdover Promotion Logic

**Current State (utlp.c):**
- Nodes boot as Genesis (stratum 1) or adopt higher authority
- No mechanism for followers to detect Genesis absence and promote

**S2 Specification:**
- Stratum 254 = "Degraded / Lost Sync" (exists in spec)
- Stratum 15 = "Holdover / Warming Up" (exists in spec)
- Automatic promotion on Genesis absence = **NOT IMPLEMENTED**

**Risk:**
Without holdover promotion, a returning Genesis with corrupted time
will always win against stratum-2 followers, potentially corrupting
the entire swarm.

**Proposed Solution (for S2.23):**
```c
// In beacon processing loop, track Genesis silence
if (g_aatr.stratum > 1) {  // I'm a follower
    if (time_since_genesis_beacon() > HOLDOVER_TIMEOUT_MS) {
        // My Genesis is gone - time to step up
        if (am_i_most_stable_remaining_peer()) {
            utlp_hal_log_warn(TAG, "Genesis absent for %lu ms, promoting to stratum 1",
                              time_since_genesis_beacon());
            g_aatr.stratum = 1;
        }
    }
}
```

**Constants to add:**
```c
#define UTLP_HOLDOVER_TIMEOUT_MS   60000   // 60 seconds without Genesis
#define UTLP_STABILITY_WINDOW_MS   10000   // Stability observation window
```

---

*Simulation: December 2025*
*Protocol: UTLP v2 with Biological Governance (S2.22)*
