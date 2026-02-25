# UTLP Technical Supplement S4: Partition Handling in Coprime Cyclic Systems

---

## Scope

This supplement extends UTLP Technical Supplement S3 (Vector Time) with techniques specific to handling network partitions in coprime cyclic time systems.

**Prerequisites:** UTLP Technical Report v2.0, Technical Supplements S1-S3

**What this document adds:**
- CRT aliasing horizon as partition detection mechanism
- Phase-lock coordination when CRT recovery is ambiguous
- Prior art claims 276-277

**Note on standard techniques:** This document also describes implementation patterns (dual counters, quality metrics, routing) that use established techniques. These are included for completeness but are not claimed as novel. See Section 5 for details.

---

## Section 1: The Partition Problem in Coprime Cyclic Systems

### 1.1 Unique Challenge

Scalar time systems detect partitions via sequence gaps or timestamp jumps. Coprime cyclic systems face a different challenge: the Chinese Remainder Theorem guarantees unique tick recovery only within the aliasing horizon (product of primes).

From S3:
- 8 primes (211-251): horizon = 8.24 × 10¹⁸ ticks = 261,000 years at 1μs
- In practice, nodes that drift beyond a few prime cycles become ambiguous

**Question:** How do you detect when two nodes have drifted so far apart that CRT recovery is unreliable?

### 1.2 HD Similarity as Horizon Indicator

The S3 HD vector representation provides a natural answer. Vector similarity degrades continuously with tick distance:

```python
# Adjacent ticks: ~99.5% similarity
# 100 ticks apart: ~95% similarity  
# 1000 ticks apart: ~50% similarity
# Beyond largest prime (~251 ticks): similarity becomes ambiguous
```

When similarity drops below a threshold, the nodes may have crossed into different "CRT cells" where the same phase tuple maps to different absolute ticks.

---

## Section 2: CRT Horizon as Partition Boundary (Claim 276)

### 2.1 The Mathematical Basis

The Chinese Remainder Theorem states that for coprime moduli {p₁, p₂, ..., pₙ}, any integer x in [0, P) where P = Πpᵢ can be uniquely recovered from its residues {x mod p₁, x mod p₂, ..., x mod pₙ}.

**The ambiguity:** If two nodes have tick counts x and x + P, they produce identical phase tuples. CRT cannot distinguish them.

**The practical issue:** Long before reaching P (261,000 years), nodes that have drifted apart become difficult to reconcile because:
1. The "direction" of drift (ahead vs behind) becomes ambiguous at half-prime distances
2. Multiple CRT solutions become plausible given measurement noise
3. Elastic sync may converge to wrong solution

### 2.2 Detection Mechanism

```c
typedef enum {
    PARTITION_NONE,      // High similarity, CRT unambiguous
    PARTITION_CAUTION,   // Medium similarity, CRT marginal
    PARTITION_DETECTED   // Low similarity, CRT ambiguous
} partition_status_t;

/**
 * Detect partition using HD similarity as proxy for CRT ambiguity
 * 
 * This is specific to coprime cyclic systems - scalar time systems
 * cannot use this technique because they lack the HD representation.
 */
partition_status_t detect_partition(const int8_t* my_vector,
                                     const int8_t* peer_vector,
                                     int dims) {
    int32_t similarity = hd_dot_product(my_vector, peer_vector, dims);
    float normalized = (float)similarity / dims;
    
    // Thresholds derived from coprime math:
    // >70% similar: within ~50 ticks, CRT unambiguous
    // 40-70% similar: within ~200 ticks, CRT marginal
    // <40% similar: beyond largest prime, CRT ambiguous
    
    if (normalized > 0.70f) return PARTITION_NONE;
    if (normalized > 0.40f) return PARTITION_CAUTION;
    return PARTITION_DETECTED;
}
```

### 2.3 Why This Is Architecture-Specific

This detection mechanism relies on properties unique to coprime cyclic time:

1. **HD vector exists** - Scalar systems have no equivalent
2. **Similarity correlates with tick distance** - Due to phase rotation in HD space
3. **Threshold maps to CRT boundary** - ~40% similarity ≈ largest prime distance

A scalar time system would need explicit sequence numbers or bounded counters to detect partitions. The coprime cyclic system gets partition detection as a byproduct of its HD representation.

---

## Section 3: Phase-Lock Coordination (Claim 277)

### 3.1 The Key Insight

When CRT recovery is ambiguous (partition detected), a remarkable property of coprime cyclic time remains useful: **each phase cycle is independently meaningful**.

SMSP patterns match on phase tuples:
```c
// SMSP region definition (from SMSP spec)
typedef struct {
    uint8_t phases[8];   // Target phases
    uint8_t mask[8];     // Which phases must match (255 = must match)
    uint8_t channels[8]; // Output values when matched
} smsp_region_t;
```

The pattern doesn't need to know the absolute tick count. It only needs the phases to match.

### 3.2 Partition-Tolerant Pattern Execution

```c
/**
 * Continue SMSP execution during partition via phase-lock
 * 
 * When CRT recovery is ambiguous, we can still:
 * 1. Lock phases to peer (relative sync)
 * 2. Execute SMSP patterns (which match on phases)
 * 3. Lose absolute time (no valid timestamps)
 * 
 * This is specific to coprime cyclic systems because:
 * - Phases are independently cyclic and lockable
 * - SMSP patterns are defined in phase space
 * - Scalar systems have no equivalent decomposition
 */
void phase_lock_sync(uint8_t* my_phases, 
                     const uint8_t* peer_phases,
                     const uint8_t* primes,
                     int num_primes,
                     float trust_weight) {
    for (int i = 0; i < num_primes; i++) {
        int diff = (int)peer_phases[i] - (int)my_phases[i];
        
        // Shortest path around the ring (cyclic property)
        if (abs(diff) > primes[i] / 2) {
            diff = diff > 0 ? diff - primes[i] : diff + primes[i];
        }
        
        // Nudge toward peer
        int nudge = (int)(diff * 0.1f * trust_weight);
        my_phases[i] = (my_phases[i] + nudge + primes[i]) % primes[i];
    }
}

/**
 * Application capability during partition
 */
typedef struct {
    bool smsp_patterns;      // YES - phases still valid
    bool bilateral_stim;     // YES - just needs phase sync
    bool lighting_sync;      // YES - just needs phase sync
    bool log_timestamps;     // NO - CRT ambiguous
    bool calendar_time;      // NO - CRT ambiguous
    bool cross_swarm_merge;  // NO - would need absolute time
} partition_capabilities_t;

partition_capabilities_t get_capabilities(partition_status_t status) {
    partition_capabilities_t cap = {0};
    
    if (status == PARTITION_NONE) {
        // Full capability
        cap.smsp_patterns = true;
        cap.bilateral_stim = true;
        cap.lighting_sync = true;
        cap.log_timestamps = true;
        cap.calendar_time = true;
        cap.cross_swarm_merge = true;
    } else if (status == PARTITION_DETECTED) {
        // Phase-lock only
        cap.smsp_patterns = true;
        cap.bilateral_stim = true;
        cap.lighting_sync = true;
        cap.log_timestamps = false;   // Can't timestamp
        cap.calendar_time = false;    // Can't convert to wall clock
        cap.cross_swarm_merge = false; // Can't reconcile with other partitions
    }
    
    return cap;
}
```

### 3.3 Graceful Degradation Hierarchy

| Capability | Requires | During Partition |
|------------|----------|------------------|
| SMSP pattern execution | Phase match | ✅ Available |
| Bilateral stimulation | Phase match | ✅ Available |
| Emergency lighting sync | Phase match | ✅ Available |
| Distributed sensing trigger | Phase match | ✅ Available |
| Log timestamps | CRT recovery | ❌ Unavailable |
| Calendar conversion | CRT + epoch | ❌ Unavailable |
| Cross-partition merge | Absolute time | ❌ Unavailable |

### 3.4 Why This Is Architecture-Specific

Scalar time systems cannot do this because:
1. A scalar counter is atomic - you can't "partially lock" it
2. There's no phase decomposition to exploit
3. Partition means total loss of time coordination

Coprime cyclic systems can partially degrade because:
1. Each phase cycle is independent
2. Applications can be designed to need only phases
3. CRT recovery is optional, not required

---

## Section 4: Prior Art Claims (276-277)

**See: claims_appendix.md (Single Source of Truth)**

This supplement establishes prior art for Claims 276-277 (2 claims):

**276. CRT Aliasing Horizon as Partition Boundary**

Using the mathematical property that Chinese Remainder Theorem recovery becomes ambiguous beyond the product of primes to detect network partitions in coprime cyclic time systems; HD vector similarity below threshold indicates potential horizon crossing; distinguishes "temporarily desynchronized" (recoverable via elastic sync) from "partitioned beyond CRT horizon" (requires phase-lock fallback); detection mechanism is specific to coprime cyclic architecture and does not apply to scalar time systems.

**277. Phase-Lock Coordination in Coprime Cyclic Systems**

Maintaining SMSP pattern coordination via direct phase matching across coprime cycles when CRT recovery is ambiguous; each phase cycle (mod pᵢ) is independently lockable; pattern execution continues because SMSP matches on phase tuples, not absolute ticks; enables graceful degradation where applications requiring only phase agreement (bilateral stimulation, lighting sync) continue while applications requiring absolute time (logging, scheduling) are unavailable; specific to coprime cyclic architecture where phases are independently meaningful.

---

## Section 5: Implementation Guidance (Standard Techniques)

The following implementation patterns use established techniques and are **not claimed as novel**. They are included for completeness.

### 5.1 Dual Counter Pattern

Maintaining separate `proper_ticks` (never adjusted) and `coordinate_ticks` (consensus-adjusted) is standard practice in disciplined oscillators (GPS receivers, PTP implementations).

```c
// Standard technique - not claimed
typedef struct {
    uint64_t proper_ticks;      // Local oscillator, never adjusted
    uint64_t coordinate_ticks;  // Disciplined to network
} dual_counter_t;
```

### 5.2 Quality Metrics

Computing sync quality from variance of neighbor observations is standard anomaly detection.

```c
// Standard technique - not claimed
float compute_quality_variance(float* similarities, int count);
```

### 5.3 Path Quality Routing

Accumulating cost along routing path is standard link-state routing (OSPF, IS-IS).

```c
// Standard technique - not claimed
typedef struct {
    int16_t path_cost;
    uint8_t hop_count;
} routing_metric_t;
```

### 5.4 Change Detection

Detecting partition rejoin via variance spike is standard change detection.

```c
// Standard technique - not claimed
bool detect_quality_spike(float current, float previous, float threshold);
```

### 5.5 Wire Format

The v0x04 beacon format adds fields for quality routing. Adding fields to protocols is standard engineering.

```c
// Standard technique - not claimed
typedef struct __attribute__((packed)) {
    // ... existing fields ...
    int16_t source_quality;
    int16_t path_quality;
    uint8_t hop_count;
} beacon_v4_t;
```

---

## Appendix A: Relationship to General Relativity

This architecture draws conceptual inspiration from GR's treatment of time (proper time vs coordinate time). However:

1. The analogy is **conceptual only** - our hardware cannot detect gravitational effects
2. ESP32 crystal noise (20 ppm) is 10⁸× larger than gravitational signals at terrestrial altitudes
3. Claims cover **implementation techniques**, not physics

The analogy aids design intuition but has no physical content.

---

**Document Version:** S4.2 (Post-Rigorous-Audit)  
**Author:** Steven Kirkland (mlehaptics Project)  
**AI Collaborators:** Claude (Anthropic)  
**Status:** Prior Art / Defensive Publication  
**License:** Public Domain

*End of Technical Supplement S4*
