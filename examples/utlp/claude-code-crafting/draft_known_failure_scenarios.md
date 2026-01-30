# PHYRFLY Protocol: Known Failure-to-Coalesce Scenarios

**Document Status:** DRAFT for review  
**Prepared for:** Steven Kirkland / mlehaptics Project  
**Date:** January 5, 2026

---

## Purpose

This document defines scenarios where epoch coalescence may fail or produce suboptimal results. These are **accepted limitations** of N=2 operation, not bugs to be fixed. We document them to:

1. Set correct expectations for protocol behavior
2. Prevent future attempts to "solve" provably unsolvable problems
3. Guide implementation toward graceful degradation rather than impossible guarantees

---

## Foundational Constraint

**N=2 Byzantine agreement is impossible.**

With only two parties and no prior shared history, there is no way to distinguish a legitimate peer from a malicious one claiming false state. This is not a PHYRFLY limitation — it is a mathematical reality.

Our approach: **Accept bounded uncertainty at first contact, then build verifiable history.**

---

## Scenario 1: First Contact Epoch Fabrication

### Description
A malicious device claims a false `origin_time` (older than actual) at first contact.

### What Happens
The false epoch is accepted. The attacker's fabricated timeline becomes the lineage.

### Why This is Accepted
- No information exists to contradict the claim
- Both parties are in symmetric positions of uncertainty
- The attack window is bounded: one shot, at first contact, frozen forever
- Subsequent inconsistencies (reboot, conflicting claims to a third party) become detectable

### Detection After the Fact
If the attacker later:
- Reboots (salt changes, depth resets to 0)
- Meets a third device with conflicting knowledge
- Claims inconsistent origin_time

...the fabrication may be exposed. The lie is permanent and must be maintained consistently.

### Mitigation
None at N=2. At N≥3, consensus can detect inconsistencies.

---

## Scenario 2: First Contact Depth Fabrication

### Description
A malicious device claims a false `depth` (higher than actual) at first contact.

### What Happens
The inflated depth is accepted. The attacker appears to have "more validated" lineage than reality.

### Why This is Accepted
Same reasoning as Scenario 1. Additionally:
- Depth saturates at 255, limiting the magnitude of the lie
- Absurdly high depth with young origin_time is implausible but not automatically rejected
- The functional distinction (tested vs untested) is binary; depth=5 vs depth=50 doesn't change behavior

### Mitigation
Sanity heuristics may flag suspiciously high depth relative to origin_time age, but no automatic rejection. At N≥3, consensus can assess credibility.

---

## Scenario 3: Lineage Fragmentation

### Description
```
Cell1 → Cell2 → Cell3 (Cell1 and Cell2 die)
Cell1 → Cell4 → Cell5 (Cell1 and Cell4 die)

Cell3 and Cell5 meet. Both have depth > 0. Both claim origin from Cell1.
But Cell3's last shared ancestor is Cell1, and Cell5's last shared ancestor is Cell1.
They have diverged histories since Cell1.
```

### What Happens
Both have `depth > 0` and same `origin_time`. Fall back to... tie?

### Resolution
This is effectively "both validated, same origin" — a true tie. Options:
1. **Arbitrary tiebreaker**: Lower MAC address wins
2. **Merge**: Both continue with same origin, higher of the two depths + 1
3. **Wait for N≥3**: Operate in parallel until third party breaks tie

### Recommended Behavior
**Merge with arbitrary tiebreaker for depth source**: 
- Both keep same `origin_time` (already identical)
- Lower MAC device keeps its depth
- Higher MAC device adopts `peer.depth + 1`

This maintains lineage continuity without stalling.

---

## Scenario 4: Simultaneous Boot

### Description
Two devices boot at exactly the same moment, operate at N=1 for different durations, then meet.

### What Happens
Both have `depth = 0` and identical `origin_time`. True tie.

### Resolution
Arbitrary tiebreaker: Lower MAC address becomes epoch source.

### Notes
Genuinely simultaneous boot times are rare. If origin_time granularity is seconds, this requires boot within same second. If milliseconds, even rarer.

---

## Scenario 5: Time Source Corruption

### Description
A device's hardware clock is corrupted (battery failure, RTC malfunction, cosmic ray bit flip) and reports wildly incorrect time.

### What Happens
If corrupted device claims very old time: It wins epoch authority incorrectly.
If corrupted device claims future time: It loses correctly, but may cause confusion.

### Why This is Accepted
Hardware failure is outside protocol scope. The protocol cannot distinguish "legitimately old device" from "corrupted clock claiming old time."

### Mitigation
- Sanity bounds on acceptable origin_time (e.g., not before 2024, not after 2100)
- Plausibility checks: origin_time shouldn't predate device manufacture date
- These are heuristics, not guarantees

---

## Scenario 6: Long-Isolated Descendant Meets Ancient Originator

### Description
```
Cell1 (origin T0) → Cell2 (T1) → Cell3 (T2)
Cell1 and Cell2 die.
Cell3 operates alone for years.

Cell4 booted at T0.5 (after Cell1, before Cell2), has been isolated for 10 years.

Cell3: depth=2, origin=T0
Cell4: depth=0, origin=T0.5

Cell3 wins because depth > 0 beats depth == 0.
```

### What Happens
Cell4's 10 years of isolated operation are discarded. Cell4 adopts Cell3's younger-bodied but older-lineage epoch.

### Why This is Accepted
Cell4's timeline was never validated. It *could* have been wrong for 10 years with no way to know. Cell3's lineage has been tested by multiple independent cells. Social proof outweighs isolation duration.

### Philosophical Note
This is analogous to: "A peer-reviewed paper from last year outweighs an unpublished manuscript from a decade ago, even if the manuscript author is more senior."

---

## Scenario 7: Rapid Reboot Cycles

### Description
A device rapidly reboots multiple times while in contact with a peer.

### What Happens
Each reboot:
- Generates new session_salt
- Resets depth to 0
- Triggers re-evaluation as first contact

If rebooting device had the authoritative epoch, peer must handle repeated "new originator" appearances.

### Potential Problem
Peer may repeatedly increment its depth as it "inherits" from what it thinks are new devices.

### Resolution
Rate limiting: If same MAC presents with new salt more than N times in T seconds, flag as unstable and deprioritize as epoch source.

---

## Scenario 8: Malicious Depth Pumping

### Description
Attacker colludes with accomplice. They repeatedly "meet" each other, incrementing depth artificially.

```
A → B (B.depth = 1)
B → A (A.depth = 2)
A → B (B.depth = 3)
... repeat to depth = 255
```

### What Happens
Attacker presents artificially high depth to victim, gaining unearned credibility.

### Why This is Accepted
- Requires two colluding devices
- Depth saturates at 255 anyway
- At N≥3, colluding pair doesn't automatically win — consensus evaluates multiple inputs
- The attack requires sustained coordination to exploit and provides limited benefit

### Mitigation
None at protocol level. Operational security (physical control of devices) is the defense.

---

## Scenario 9: Network Partition and Rejoin

### Description
```
Initial: Cell1, Cell2, Cell3 share epoch
Partition: Cell1 alone | Cell2+Cell3 together
Both sides continue operating, time advancing
Rejoin: All three reconnect
```

### What Happens
During partition:
- Cell1 continues its timeline (N=1)
- Cell2+Cell3 continue their timeline (N=2, potentially with health/tenure evolution)

On rejoin:
- Same origin_time (inherited from same source)
- Potentially different depth (Cell2 or Cell3 may have incremented)
- N≥3 consensus should converge

### Resolution
This is normal operation. N≥3 consensus handles partition recovery. No special case needed.

---

## Scenario 10: Permanent N=2 with Contested State

### Description
Two devices meet, both believe they should be authoritative, and the resolution rules produce a "wrong" result (from human perspective).

### What Happens
Protocol follows rules. "Wrong" device becomes epoch source.

### Why This is Accepted
"Wrong" is subjective. The protocol cannot know human intent. It follows deterministic rules that both parties can compute independently.

### User Recourse
If a human operator knows the correct epoch:
1. Factory reset the "wrong" device (clears state)
2. Let it rejoin with depth=0
3. "Correct" device (as originator or descendant) will win

This is manual intervention, not protocol-level correction.

---

## Summary: What We Accept

| Scenario | Accepted Outcome | Rationale |
|----------|------------------|-----------|
| First contact fabrication | Lie accepted | Provably unsolvable at N=2 |
| Depth fabrication | Inflated depth accepted | Bounded impact, single window |
| Lineage fragmentation | Arbitrary tiebreaker | Deterministic resolution |
| Simultaneous boot | Arbitrary tiebreaker | Rare edge case |
| Clock corruption | Corrupted time may win | Hardware failure out of scope |
| Isolated elder loses to young descendant | Descendant wins | Social proof > isolation duration |
| Rapid reboots | Rate limit heuristic | Operational, not protocol |
| Depth pumping | Collusion possible | Requires coordination, limited payoff |
| Partition/rejoin | Normal N≥3 consensus | Designed behavior |
| Contested N=2 | Rules apply, may feel "wrong" | Deterministic beats subjective |

---

## Design Philosophy

These scenarios are **known limitations**, not **defects**. A protocol that attempted to solve all of them would either:

1. Require trusted third parties (violates connectionless principle)
2. Require cryptographic infrastructure (violates resource constraints)
3. Be provably impossible (N=2 Byzantine agreement)

We choose: **Simple rules, deterministic outcomes, bounded uncertainty, graceful degradation.**

---

## Implementation Status Tracking

This section tracks which commits achieve stable sync and which do not.

| Commit | Description | Sync Status | Notes |
|--------|-------------|-------------|-------|
| `36ea892` | Fix chord cross-profile incompatibility | ✅ Working | Baseline before HDC changes |
| `033022d` | HDC primitives + lamprey model (CRT offset) | ❌ Unstable | Sometimes in-phase, sometimes antiphase |
| `5de5420` | Vector-native firefly sync (no CRT) | ❌ Unstable | Same antiphase bug as 033022d |

### Known Bug: Antiphase Sync

**Symptom:** After reboot, devices sometimes sync in-phase, sometimes antiphase (~180° out of phase).

**Suspected Causes:**
1. Firefly vote margin requirement (+1) may cause too many "tied" results
2. MAC tiebreaker doesn't correlate with actual age - wrong device may adopt
3. Offset chord application may have sign/direction bug

**Required Investigation:**
- Add verbose logging to firefly vote showing all dimension votes
- Log which device adopts and what offset chord is stored
- Compare swarm_chord values between devices at same wall-clock moment

---

*End of Known Failure Scenarios*
