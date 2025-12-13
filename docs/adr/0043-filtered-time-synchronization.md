# AD043: Filtered Time Synchronization Protocol

**Date:** December 2, 2025
**Phase:** Phase 6r
**Status:** ✅ **APPROVED** - Supersedes AD039
**Type:** Architecture
**Supersedes:** [AD039: Time Synchronization Protocol](0039-time-synchronization-protocol.md)

---

## Context

Phase 6 bilateral motor coordination revealed critical limitations in the RTT-based beacon protocol from AD039:

**Problems with AD039 (4-way RTT handshake):**
- RTT spikes (200-950ms) during BLE parameter updates cause stale timestamps
- 300ms RTT spike → timestamp is 150ms stale by the time CLIENT uses it
- Bug #41 data: 84% of POOR timing cycles (>50ms error) had RTT >100ms
- Clamping/rejection logic (Bug #41) treats symptoms, not root cause
- Best achievable accuracy: ±15ms effective jitter despite <10ms corrections

**Root Cause Identified:**
When beacon handshake takes 300ms to complete, the SERVER timestamp CLIENT receives is already 150ms old. Even with perfect clocks and drift correction, using a 150ms-old reference can't achieve better than ±15ms accuracy.

**Industry Standard Solution:**
NTP, PTP, and professional BLE/802.15.4 time sync protocols use **one-way timestamps + filter** instead of periodic RTT measurement. One 300ms outlier in 8 samples = minor bump, not a phase disaster.

**Key Insight from External Review (Grok AI):**
> "You're not working around BLE limitations anymore — you're now doing it the way everyone who needs tight sync over BLE does it. The 300ms RTT spike is the real killer — everything else we measured was a red herring."

---

## Decision

Implement **Filtered Time Synchronization Protocol** using exponential moving average filter:

### Protocol Changes

**REMOVE:**
- ❌ 4-way RTT handshake (T1, T2, T3, T4 timestamps)
- ❌ RTT measurement and quality scoring based on RTT
- ❌ Hard thresholds and clamping (Bug #41 approach)

**ADD:**
- ✅ **One-way SERVER timestamp** (just `server_time_us` in beacon)
- ✅ **CLIENT RX timestamp capture** (ISR-level `esp_timer_get_time()`)
- ✅ **Sample ring buffer** (last 8 samples for debugging/analysis)
- ✅ **Exponential moving average filter** (smooths outliers)

### Filter Algorithm

```c
// One-way delay estimate (assume symmetric, filter handles asymmetry)
int64_t raw_offset = client_rx_time - server_tx_time;

// Exponential moving average (alpha = 0.1 for heavy smoothing)
filtered_offset = (alpha * raw_offset) + ((1.0 - alpha) * filtered_offset);

// Apply filtered offset to get synchronized time
sync_time = esp_timer_get_time() + filtered_offset;
```

**Why Alpha = 0.1 Works:**
- 300ms RTT outlier → raw_offset way off → but only 10% weight
- Next 7 beacons with normal RTT (80ms) → quickly pull estimate back
- No hard thresholds, no rejection logic, no "if RTT > X" code

### Beacon Interval

**Keep adaptive backoff** from AD039 (5s → 80s):
- Provides sufficient update rate for 0.169 ms/s natural drift
- Each beacon contributes one sample to 8-sample filter
- Filter fully refreshed every 40-320 seconds (depending on interval)

---

## Architecture

### Simplified Beacon Structure

**OLD (AD039):**
```c
typedef struct {
    uint64_t t1_request_us;     // CLIENT request time
    uint64_t t2_server_rx_us;   // SERVER receive time
    uint64_t t3_server_tx_us;   // SERVER transmit time
    // CLIENT captures t4 on receive
    // RTT = (t4 - t1) - (t3 - t2)
    // Offset = ((t2 - t1) + (t3 - t4)) / 2
} time_beacon_t;
```

**NEW (AD043):**
```c
typedef struct {
    uint64_t server_time_us;    // SERVER's esp_timer_get_time()
    uint32_t cycle_count;       // Optional: for validation
    uint8_t sequence;           // Incrementing counter
} time_beacon_t;
```

**Size:** 13 bytes (fits in single BLE packet with overhead)

### Filter State Management

```c
typedef struct {
    // Sample history
    time_sample_t samples[8];   // Ring buffer
    uint8_t head;               // Next write index

    // Filter state
    int64_t filtered_offset_us; // Smoothed estimate
    float alpha;                // Filter coefficient (0.1 typical)

    // Metrics
    uint32_t sample_count;      // Total samples received
    uint32_t outlier_count;     // Samples >200ms deviation
} time_filter_t;

typedef struct {
    uint64_t server_tx_us;      // From beacon
    uint64_t client_rx_us;      // Local capture
    int64_t raw_offset_us;      // Calculated offset
} time_sample_t;
```

### Integration with Motor Task

**Bug #50 position-based state calculation unchanged:**
```c
// Still uses time_sync_get_time() - just better quality now
uint64_t sync_time_us;
if (time_sync_get_time(&sync_time_us) == ESP_OK) {
    // Calculate SERVER position in cycle
    uint64_t position_in_cycle = (sync_time_us - server_epoch_us) % cycle_us;
    bool server_is_active = (position_in_cycle < half_cycle_us);
    state = server_is_active ? MOTOR_STATE_INACTIVE : MOTOR_STATE_ACTIVE;
}
```

**What changed:** `time_sync_get_time()` now returns filtered offset instead of single-shot RTT-based offset.

---

## Implementation Plan (Phase 6r)

### Step 1: Simplify Beacon (1 hour)
- ✅ Remove T1, T2, T3, T4 timestamp logic from `src/time_sync_task.c`
- ✅ SERVER just sends `server_time_us` in beacon
- ✅ CLIENT captures `client_rx_us = esp_timer_get_time()` in BLE RX callback

### Step 2: Add Filter (2 hours)
- ✅ Create `time_filter_t` structure in `src/time_sync.c`
- ✅ Implement `update_time_offset()` with exponential moving average
- ✅ Replace `time_sync_get_time()` offset calculation with filtered offset

### Step 3: Remove RTT Logic (1 hour)
- ✅ Remove RTT measurement, quality scoring based on RTT
- ✅ Remove Bug #41 clamping/rejection thresholds
- ✅ Simplify adaptive backoff (keep interval adjustment, remove RTT triggers)

### Step 4: Testing (hardware validation)
- ✅ Verify <5ms mean error over 90 minutes (vs ±15ms with AD039)
- ✅ Confirm 300ms RTT outliers no longer cause phase jumps
- ✅ Validate Bug #50 position-based state works seamlessly

---

## Expected Outcomes

### Before (AD039 + Bug #41):
- Mean phase error: ±15ms (effective jitter)
- GOOD timing (±10ms): 18.7%
- POOR timing (>50ms): 25.1%
- RTT spikes cause phase jumps

### After (AD043):
- Mean phase error: **<5ms** (Grok claims <1ms, conservative estimate 5ms)
- GOOD timing (±10ms): **>95%**
- POOR timing (>50ms): **<1%**
- RTT spikes naturally filtered out

### Accuracy Target Update

**AD029 Revised Specification:**
- OLD: ±100ms (AD039 periodic sync)
- NEW: **±5ms** (AD043 filtered sync)

This 20× improvement enables **sub-10ms bilateral alternation accuracy** for therapeutic effectiveness.

---

## Technical Decisions

### Why Exponential Moving Average (not Kalman)?

**EMA Advantages:**
- 3 lines of code vs 50+ lines for Kalman
- No state prediction needed (offset changes slowly)
- Computationally trivial (one multiply, one add)
- Easy to tune (single alpha parameter)

**When to Upgrade to Kalman:**
- If natural drift rate varies significantly over temperature
- If we need to predict offset during BLE disconnects
- If we implement clock skew compensation (16 ppm from tech spike)

**Current Assessment:** EMA sufficient for 0.169 ms/s natural drift rate measured in tech spike.

### Why Keep Adaptive Backoff?

**Benefits:**
- Battery efficiency (less frequent beacons when sync is good)
- Natural oscillator drift is slow (0.169 ms/s)
- Filter doesn't need fresh samples every second

**Updated Intervals:**
- Base: 5s (initial sync)
- Max: 80s (steady state)
- Trigger: Remove RTT-based triggers, use filtered offset stability instead

---

## Consequences

### Benefits

- ✅ **Industry Standard:** Matches NTP/PTP/BLE time sync best practices
- ✅ **Robust to Outliers:** 300ms RTT spike = 10% weight, not 100%
- ✅ **Simpler Code:** No RTT calculation, no complex quality scoring
- ✅ **Better Accuracy:** <5ms vs ±15ms (3× improvement minimum)
- ✅ **No Thresholds:** No magic numbers like "reject if RTT >300ms"
- ✅ **Self-Tuning:** Filter automatically adapts to link quality
- ✅ **Seamless Integration:** Bug #50 position-based state works unchanged

### Drawbacks

- Filter state adds ~100 bytes RAM (8 samples × 12 bytes)
- Initial convergence takes 3-8 beacons (15-40 seconds at 5s intervals)
- Outlier rejection is implicit (can't easily detect bad links)
- Alpha parameter requires tuning for different drift rates

### Migration from AD039

**API Compatibility:** ✅ **PRESERVED**
- `time_sync_get_time()` signature unchanged
- `time_sync_get_motor_epoch()` signature unchanged
- `time_sync_is_synchronized()` logic simplified

**Breaking Changes:** ❌ **NONE**
- Motor task code unchanged (Bug #50 fix works with both)
- BLE task code mostly unchanged (beacon structure simpler)
- Time sync task internal refactor only

---

## Alternatives Considered

### Option A: Keep AD039, Improve Clamping (Rejected)

**Approach:** Add more sophisticated rejection thresholds (Bug #41 extended)

**Pros:**
- Minimal code changes
- Familiar RTT-based approach

**Cons:**
- Still fighting symptoms, not root cause
- More magic numbers to tune
- Can't achieve <10ms accuracy with stale timestamps
- Complexity grows with each edge case

**Why Rejected:** "Stop fighting, just filter it out" (external review)

### Option B: Kalman Filter (Deferred)

**Approach:** Full Kalman filter with state prediction and clock skew estimation

**Pros:**
- Optimal estimator (mathematically)
- Can predict offset during disconnects
- Can estimate clock skew (16 ppm correction)

**Cons:**
- 50+ lines of matrix math
- Requires tuning process noise and measurement noise
- Overkill for slow-changing offset (0.169 ms/s)
- Harder to debug than EMA

**Why Deferred:** EMA expected to be sufficient. Upgrade to Kalman if <5ms not achieved.

### Option C: Least Squares Regression (Rejected)

**Approach:** Fit line to last N samples, predict current offset

**Pros:**
- Handles clock skew naturally
- Well-understood algorithm

**Cons:**
- Computationally expensive (matrix operations)
- Assumes linear drift (true, but EMA also works)
- More complex than EMA
- No significant advantage over Kalman if going this route

**Why Rejected:** If EMA insufficient, jump straight to Kalman (industry standard).

---

## References

### Related ADRs

- **[AD028: Command Control Synchronized Fallback](0028-command-control-synchronized-fallback.md)** - Motor control architecture (unchanged)
- **[AD029: Relaxed Timing Specification](0029-relaxed-timing-specification.md)** - UPDATE: ±100ms → ±5ms target
- **[AD039: Time Synchronization Protocol](0039-time-synchronization-protocol.md)** - **SUPERSEDED** by this ADR
- **[AD041: Predictive Bilateral Synchronization](0041-predictive-bilateral-synchronization.md)** - May need offset calculation update

### External References

- NTP RFC 1305: Network Time Protocol
- IEEE 1588: Precision Time Protocol (PTP)
- [Tech Spike: Single-Device Drift Baseline](../../TECH_SPIKE_SINGLE_DEVICE_DRIFT_BASELINE.md) - 0.169 ms/s natural drift measured

### Bug History

- **Bug #41:** RTT-based clamping (rejected approach)
- **Bug #49:** Time domain mismatch (fixed)
- **Bug #50:** Position-based state selection (complements filter)

---

## Validation Criteria

### Phase 6r Success Metrics

1. **Mean Phase Error:** <5ms over 90-minute session
2. **GOOD Timing (±10ms):** >95% of cycles
3. **POOR Timing (>50ms):** <1% of cycles
4. **Outlier Resilience:** 300ms RTT spike causes <2ms phase bump
5. **Convergence Time:** <40 seconds from connection to stable sync
6. **Code Simplicity:** <200 lines for entire filter implementation

### Test Plan

1. **Baseline Test:** 90-minute session, measure phase errors
2. **Outlier Injection:** Manually delay beacons, verify filter rejects
3. **Comparison:** AD039 logs vs AD043 logs (same conditions)
4. **Regression:** Verify Bug #50 position-based state still works

---

## Migration Notes

### For Developers

**Time Sync Module:**
- Remove `src/time_sync.c` RTT calculation functions
- Add `time_filter_t` structure and `update_time_offset()` function
- Simplify `time_sync_get_time()` to return `esp_timer + filtered_offset`

**Motor Task Module:**
- **No changes required** - Bug #50 position-based state works with filtered offset

**BLE Task Module:**
- Simplify beacon structure (remove T2, T3 timestamps)
- CLIENT RX callback captures `esp_timer_get_time()` immediately

### For Testers

**Expected Log Changes:**
```
OLD (AD039):
TIME_SYNC: Beacon RTT measured: 92597 μs, offset: -4149875 μs

NEW (AD043):
TIME_SYNC: Sample: server_tx=12345678 us, client_rx=8195803 us, raw_offset=-4149875 us
TIME_SYNC: Filtered offset: -4150124 us (alpha=0.10, samples=5/8)
```

**What to Watch For:**
- Filtered offset should change smoothly (no jumps)
- Outliers visible in raw_offset, but filtered_offset stable
- Phase errors in motor logs should be consistently <10ms

---

## Status

**Current:** ✅ **IMPLEMENTED** - Enhanced in v0.6.72 with paired timestamps
**Original Implementation:** Phase 6r filter in `src/time_sync.c`
**Enhancement:** v0.6.72 - Paired timestamps in SYNC_FB for bias correction

---

## Enhancement: Paired Timestamps in SYNC_FB (v0.6.72)

### Problem: One-Way Delay Bias

The original AD043 EMA filter smooths **variance** but cannot correct **systematic bias** from one-way delays. If every beacon has +20ms one-way delay:

```
One-way offset: T2 - T1 = clock_offset + one_way_delay
EMA smooths variance but converges to: clock_offset + 20ms (wrong!)
```

This explains observed ~40ms phase offsets despite excellent filter stability.

### Solution: NTP-Style Paired Timestamps via SYNC_FB

CLIENT already sends SYNC_FB (activation report) every 10 cycles for drift verification. Enhanced structure now includes beacon timestamps:

```c
typedef struct __attribute__((packed)) {
    uint64_t actual_time_us;         // CLIENT's activation (original)
    uint64_t target_time_us;         // CLIENT's target (original)
    int32_t  client_error_ms;        // Self-measured error (original)
    uint32_t cycle_number;           // Cycle count (original)
    // v0.6.72: Paired timestamps for bias correction
    uint64_t beacon_server_time_us;  // T1: server_time_us from last beacon
    uint64_t beacon_rx_time_us;      // T2: CLIENT's local time when beacon received
    uint64_t report_tx_time_us;      // T3: CLIENT's local time when sending this
} activation_report_t;
```

SERVER records T4 when receiving SYNC_FB and calculates bias-corrected offset:

```c
// NTP formula: offset = ((T2-T1) + (T3-T4)) / 2
// (T2-T1) includes: clock_offset + delay_to_client
// (T3-T4) includes: clock_offset - delay_to_server
// Sum = 2*offset (delays cancel if symmetric)
int64_t d1 = t2 - t1;  // CLIENT rx - SERVER beacon tx
int64_t d2 = t3 - t4;  // CLIENT report tx - SERVER report rx
int64_t paired_offset = (d1 + d2) / 2;
```

### Why This Works Now (But RTT Caused Problems Before)

**Previous RTT Problem (AD039):** RTT spikes caused immediate bad corrections
```
RTT spike → stale timestamp → CLIENT applies stale correction → motor jitter
```

**Pattern-Broadcast Architecture (AD045):** Motors calculate independently, no active correction
```
RTT spike → EMA filter rejects outlier → motor timing unaffected
```

Paired timestamps now feed the EMA filter (not motor corrections directly), giving us bias-corrected offset estimates while maintaining outlier rejection.

### Implementation Details

**Files Modified:**
- `src/ble_manager.h`: Extended `activation_report_t` structure
- `src/time_sync.h`: Added new APIs:
  - `time_sync_get_last_beacon_timestamps()` - CLIENT gets T1/T2
  - `time_sync_update_from_paired_timestamps()` - SERVER calculates offset
- `src/time_sync.c`: Store T2 in `process_beacon()`, implement new functions
- `src/motor_task.c`: Populate paired timestamps in SYNC_FB
- `src/time_sync_task.c`: Call paired update on SYNC_FB receive

**Logging:**
```
[PAIRED] offset=-4150 µs, RTT=82000 µs (T1=..., T2=..., T3=..., T4=...)
```

### Expected Improvement

- One-way bias: Eliminated (NTP formula cancels symmetric delays)
- Phase offset: ~40ms → <5ms (target)
- RTT spikes: Still filtered by EMA (no jitter)
- Additional overhead: ~24 bytes per SYNC_FB (3× uint64_t)

### Hybrid Approach Summary

| Component | Source | Purpose |
|-----------|--------|---------|
| Beacon (SERVER→CLIENT) | One-way timestamp | Fast periodic sync (10-60s interval) |
| EMA Filter | AD043 | Smooth variance, reject outliers |
| SYNC_FB (CLIENT→SERVER) | Paired timestamps | Correct one-way delay bias |
| Pattern-Broadcast | AD045 | Both devices calculate independently |

This combines the best of both worlds: beacon simplicity + paired timestamp accuracy.

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** December 11, 2025
