# PHYRFLY Protocol Section: N=2 Epoch Coalescence

**Document Status:** DRAFT for review  
**Prepared for:** Steven Kirkland / mlehaptics Project  
**Date:** January 5, 2026

---

## 1. Foundational Principle: N=1 is Valid Life

A single device operating alone is not "waiting for consensus" — it is living its own timeline. The swarm does not require quorum to exist; it requires quorum only for contested decisions.

**Implications:**
- A device at N=1 maintains its own epoch origin
- Time progresses sequentially without interruption
- The device is authoritative over its own timeline until first contact
- There is no "incomplete" or "pending" state — N=1 is fully operational

---

## 2. Epoch State Structure

```c
typedef struct {
    uint32_t origin_time;      // Epoch origin timestamp (seconds since boot or absolute)
    uint8_t  depth;            // Inheritance depth (0 = originator, >0 = inherited)
    uint8_t  session_salt[2];  // Current session identifier (changes on reboot)
} epoch_state_t;               // 7 bytes, fixed size
```

### 2.1 Field Definitions

**origin_time**: The timestamp when this epoch lineage began. For an originator (depth=0), this is the device's boot time. For an inheritor (depth>0), this is the origin_time received from the epoch source.

**depth**: Count of inheritance events in this epoch's history.
- `depth = 0`: This device is the epoch originator; timeline has never been validated by another cell
- `depth > 0`: This device inherited the epoch; timeline has been validated by `depth` inheritance events
- Saturates at 255 (does not wrap)

**session_salt**: Random value generated at boot. Identifies the current session. A change in session_salt indicates the device has rebooted and lost volatile state.

---

## 3. First Contact Rules

When a device transitions from N=1 to N=2 (first detection of other life), the following rules apply:

### 3.1 The Implicit Trust Window

At first contact, devices cannot verify each other's claims. This creates a single, bounded window where false claims could be accepted. This is acknowledged and accepted because:

1. No information exists to contradict the claim
2. The window closes immediately upon relationship establishment
3. N=2 Byzantine agreement is provably impossible
4. Subsequent inconsistencies become detectable against established history

### 3.2 Resolution Algorithm

```
ON first_contact(peer):
    
    CASE 1: Both Originators (my.depth == 0 AND peer.depth == 0)
        // Two devices that have never met anyone
        // Oldest origin wins
        IF peer.origin_time < my.origin_time:
            adopt_epoch(peer)
        ELSE:
            // Peer adopts mine (handled by peer's logic)
            // My state unchanged
    
    CASE 2: I am Originator, Peer is Descendant (my.depth == 0 AND peer.depth > 0)
        // Peer has validated lineage, I have untested isolation
        // Validated lineage wins regardless of age
        adopt_epoch(peer)
    
    CASE 3: I am Descendant, Peer is Originator (my.depth > 0 AND peer.depth == 0)
        // I have validated lineage, peer has untested isolation
        // My lineage wins (peer adopts mine)
        // My state unchanged
    
    CASE 4: Both Descendants (my.depth > 0 AND peer.depth > 0)
        // Both have validated lineages
        // Oldest origin wins
        IF peer.origin_time < my.origin_time:
            adopt_epoch(peer)
        ELSE:
            // My state unchanged
```

### 3.3 Epoch Adoption Procedure

```
FUNCTION adopt_epoch(source):
    my.origin_time = source.origin_time
    my.depth = MIN(source.depth + 1, 255)  // Saturating increment
    // session_salt is NOT changed — I did not reboot
    
    RECORD epoch_adoption_event(
        timestamp: now(),
        source_mac: source.mac,
        source_salt: source.session_salt,
        adopted_origin: source.origin_time,
        adopted_depth: source.depth,
        new_depth: my.depth
    )
```

---

## 4. Rationale: Why Depth > 0 Beats Depth == 0

A device with `depth > 0` has had its epoch **validated by at least one other independent cell**. This represents social proof that the timeline has been examined and accepted.

A device with `depth == 0` has been operating in isolation. Its timeline may be correct, but it has never been tested against external reality. It could have drifted, corrupted, or been intentionally misconfigured with no opportunity for detection.

**Analogy:** A scientific result replicated by one other lab has more credibility than an unreplicated result, even if the unreplicated result is older.

---

## 5. N=2 to N=1 Transitions

When a device's only peer is lost (N=2 → N=1):

1. **Time continues sequentially** — No jumps, no resets
2. **Epoch state is preserved** — origin_time and depth unchanged
3. **Session continues** — session_salt unchanged (no reboot occurred)
4. **Device becomes sole carrier** of the lineage

The device is now responsible for continuity. If it later encounters new life, it presents its inherited epoch with its accumulated depth.

---

## 6. Session Salt and Reboot Detection

### 6.1 Purpose

Session salt identifies a continuous operational session. It changes only on reboot.

### 6.2 Reboot Detection Rule

```
IF known_peer.mac == received.mac AND known_peer.salt != received.salt:
    // Peer has rebooted
    // Their depth resets to 0 (they are now an originator of a new session)
    // Re-evaluate epoch relationship using first_contact rules
    handle_as_first_contact(received)
```

### 6.3 Identity Definition

A peer's identity for trust purposes is the tuple `(MAC, session_salt)`, not MAC alone.

- Same MAC, same salt = continuing relationship
- Same MAC, different salt = new relationship (peer rebooted)

---

## 7. Depth Counter Properties

### 7.1 Increment Behavior

- Increments on the **receiving** side only (the adopter increments, not the propagator)
- Saturates at 255 (never wraps to 0)
- Once `depth > 0`, device is permanently marked as "descendant" for this session

### 7.2 Reset Behavior

- Depth resets to 0 **only** on reboot (when session_salt changes)
- Depth is never decremented
- Depth is never reset without a reboot

### 7.3 Saturation Rationale

At depth=255, the epoch is "maximally validated." The distinction between 255 and 256 generations is not meaningful. The critical property is the binary distinction: `depth == 0` (untested) vs `depth > 0` (tested).

---

## 8. Data Transmission

### 8.1 What is Transmitted

During peer communication, epoch state is shared:
- `origin_time`
- `depth`
- `session_salt`

### 8.2 What is Local-Only

- Epoch adoption event history (logged locally, not transmitted)
- Peer relationship state (maintained locally)

---

## 9. Integration with N≥3 Consensus

When N≥3, standard consensus mechanisms apply. The N=2 rules defined here are specifically for:

1. Initial contact between two devices that have no shared history
2. Ongoing N=2 operation when no third device is available
3. Fallback behavior when network partitions to N=2

At N≥3, contested epoch claims can be resolved by majority. The depth counter contributes to credibility assessment but does not override consensus.

---

## 10. Summary Table

| Scenario | My Depth | Peer Depth | Resolution |
|----------|----------|------------|------------|
| Both new | 0 | 0 | Oldest origin_time wins |
| I'm isolated, peer validated | 0 | >0 | I adopt peer's epoch |
| I'm validated, peer isolated | >0 | 0 | Peer adopts my epoch |
| Both validated | >0 | >0 | Oldest origin_time wins |
| Peer rebooted (salt changed) | any | 0 (reset) | Re-evaluate as first contact |

---

*End of Protocol Section*
