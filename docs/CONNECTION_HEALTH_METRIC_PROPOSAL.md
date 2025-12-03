# Connection Health Metric - Design Proposal

**Status:** Proposed (Not Yet Implemented)
**Date:** 2025-12-01
**Context:** Discussion about exposing link quality metrics to PWA app

---

## Problem Statement

Users and developers would benefit from visibility into BLE connection quality between:
1. **Peer-to-peer link** (Device A ↔ Device B) - Critical for bilateral synchronization
2. **Device-to-app link** (Device ↔ PWA) - Used for monitoring and control

However, raw RSSI values can be alarming to non-technical users, especially since:
- Devices are in plastic enclosures
- Devices are held in hands (body blocking signal)
- Typical handheld BLE devices show -70 to -85 dBm (looks "weak" but works fine)

---

## Design Goals

1. **Transparency**: Give users diagnostic information without creating anxiety
2. **Actionable**: Help users troubleshoot real connection problems
3. **Non-alarming**: Present metrics in user-friendly format
4. **Diagnostic value**: Enable remote support via screenshots/stats
5. **Minimal overhead**: Reuse existing beacon infrastructure

---

## Proposed Solution: Composite "Connection Health" Metric

Instead of showing raw RSSI, combine multiple signals into a holistic health indicator:

```
Connection Health: Good (87%)
  ├─ Time Sync Quality: 95%       ← Already implemented!
  ├─ Peer Link Quality: 82%       ← Normalized RSSI
  ├─ Packet Delivery: 99.8%       ← Beacon success rate
  └─ Phase Accuracy: ±12ms        ← Bilateral timing error
```

### **Components**

#### 1. Time Sync Quality (Already Exists)
- **Source:** `time_sync_get_quality()` (0-100%)
- **Meaning:** How well devices' clocks are synchronized
- **Already exposed:** Internal to firmware, could add to BLE characteristic

#### 2. Peer Link Quality (New - Normalized RSSI)

**Formula:**
```c
// Map RSSI to 0-100% with calibration for handheld device
uint8_t rssi_to_quality_percent(int8_t rssi_dbm) {
    const int8_t RSSI_MIN = -95;  // Below this = 0% (near dropout)
    const int8_t RSSI_MAX = -50;  // Above this = 100% (perfect)

    if (rssi_dbm >= RSSI_MAX) return 100;
    if (rssi_dbm <= RSSI_MIN) return 0;

    return (uint8_t)(((rssi_dbm - RSSI_MIN) * 100) / (RSSI_MAX - RSSI_MIN));
}

// Quality bands (for qualitative display)
const char* quality_to_string(uint8_t quality_percent) {
    if (quality_percent >= 80) return "Excellent";
    if (quality_percent >= 60) return "Good";
    if (quality_percent >= 40) return "Fair";
    if (quality_percent >= 20) return "Poor";
    return "Very Poor";
}
```

**Calibration for Handheld Device:**
| RSSI (dBm) | Quality % | Band | Expected Scenario |
|------------|-----------|------|-------------------|
| ≥ -50 | 100% | Excellent | Devices very close, no obstruction |
| -60 | 78% | Good | Normal handheld, 0.5-1m apart |
| -70 | 56% | Good | **Typical in-hand usage** ← Most common |
| -80 | 33% | Fair | Hands farther apart, body blocking |
| -90 | 11% | Poor | Near edge of reliable range |
| ≤ -95 | 0% | Very Poor | Connection likely to drop |

**Key Insight:** -70 to -85 dBm is **normal and acceptable** for handheld BLE devices in enclosures. Normalize this to 40-60% to avoid alarming users.

#### 3. Packet Delivery Rate (New)

**Track beacon success:**
```c
// In time_sync.c or ble_manager.c
typedef struct {
    uint32_t beacons_sent;
    uint32_t beacons_acked;  // Responses received
    uint8_t delivery_rate_percent;  // Rolling average
} beacon_stats_t;

uint8_t calculate_delivery_rate(beacon_stats_t* stats) {
    if (stats->beacons_sent == 0) return 100;
    return (uint8_t)((stats->beacons_acked * 100) / stats->beacons_sent);
}
```

**Interpretation:**
- 100%: Perfect (no lost beacons)
- 95-99%: Excellent (occasional loss, normal for BLE)
- 90-94%: Good (minor interference)
- <90%: Poor (investigate connection issues)

#### 4. Phase Accuracy (Future - After Bug #40 Fix)

**Measure bilateral timing error:**
```c
// In motor_task.c CLIENT INACTIVE state
static int32_t last_phase_error_ms = 0;

// After calculating target_wait_us, track actual vs ideal
uint64_t ideal_target = server_current_cycle_start_us + half_period_us;
int32_t phase_error_ms = (int32_t)((client_actual_start_us - ideal_target) / 1000);
last_phase_error_ms = phase_error_ms;  // Expose via getter
```

**Interpretation:**
- ±10ms: Excellent (imperceptible to user)
- ±50ms: Good (acceptable for therapy)
- ±100ms: Fair (noticeable, but functional)
- >100ms: Poor (bilateral alternation compromised)

---

## UX Presentation Options

### **Option A: Composite Score (Recommended)**

**PWA Display:**
```
Connection Health: Good (87%)

Details:
  Time Sync:        95% (Excellent)
  Peer Signal:      82% (Good - normal for handheld)
  Packet Delivery:  99% (Excellent)
  Phase Accuracy:   ±12ms (Excellent)
```

**Benefits:**
- Single number users can glance at
- Details available for troubleshooting
- Reassuring text ("normal for handheld")

### **Option B: Signal Bars**

**Visual Representation:**
```
Peer Connection: ▂▃▄▅  (Good)
App Connection:  ▂▃▄▅▆ (Excellent)
```

**Benefits:**
- Familiar to users (like WiFi/cellular signal)
- Non-technical
- Quick visual assessment

### **Option C: Developer Mode Only**

**Default View:**
```
Status: Connected
Sync Quality: 95%
```

**Developer Mode (long-press to enable):**
```
Connection Diagnostics:
  Peer RSSI:        -72 dBm
  App RSSI:         -58 dBm
  Sync Quality:     95%
  Beacons Sent:     127
  Beacons Acked:    126 (99.2%)
  Phase Error:      +12ms
  Last Beacon:      3s ago
```

**Benefits:**
- Doesn't overwhelm casual users
- Power users get full data
- Support can say "enable developer mode and send screenshot"

---

## BLE Characteristic Specification

### **New Characteristic: Connection Health (Read + Notify)**

**UUID:** `4BCAE9BE-9829-4F0A-9E88-267DE5E70104` (next available in Configuration Service)

**Payload (8 bytes):**
```c
typedef struct __attribute__((packed)) {
    uint8_t composite_health_percent;    // 0-100% overall health
    uint8_t time_sync_quality_percent;   // 0-100% sync quality (already tracked)
    uint8_t peer_link_quality_percent;   // 0-100% normalized RSSI
    uint8_t packet_delivery_percent;     // 0-100% beacon success rate
    int16_t phase_error_ms;              // Signed ms error (±32767 range)
    uint8_t peer_rssi_dbm;               // Raw RSSI for developer mode (127 offset)
    uint8_t reserved;                     // Future use
} connection_health_t;
```

**Update Frequency:**
- Notify on significant change (>10% in any metric)
- Maximum rate: Once per 10 seconds (avoid spam)
- Piggyback on sync beacon processing (no extra BLE traffic)

**Composite Health Calculation:**
```c
uint8_t calculate_composite_health(connection_health_t* health) {
    // Weighted average (sync quality most important)
    uint16_t weighted_sum =
        (health->time_sync_quality_percent * 40) +    // 40% weight
        (health->peer_link_quality_percent * 30) +    // 30% weight
        (health->packet_delivery_percent * 20) +      // 20% weight
        (phase_error_quality(health->phase_error_ms) * 10);  // 10% weight

    return (uint8_t)(weighted_sum / 100);
}

uint8_t phase_error_quality(int16_t error_ms) {
    int16_t abs_error = (error_ms < 0) ? -error_ms : error_ms;
    if (abs_error <= 10) return 100;
    if (abs_error <= 50) return 75;
    if (abs_error <= 100) return 50;
    return 25;
}
```

---

## Implementation Priority

**Phase 1 (Immediate - After Bug #40 Testing):**
- ✅ Time Sync Quality (already exists, just expose it)
- ⏳ Phase Error Tracking (add to INACTIVE state)

**Phase 2 (Short-term Enhancement):**
- ⏳ Peer RSSI normalization
- ⏳ Packet delivery rate tracking
- ⏳ Composite health calculation
- ⏳ BLE characteristic implementation

**Phase 3 (Long-term Polish):**
- ⏳ PWA UI for connection health
- ⏳ Developer mode toggle
- ⏳ Historical graphing (connection quality over session)
- ⏳ Alert thresholds (notify if health drops below 40%)

---

## Pros and Cons

### **Pros**
✅ **Transparency**: Users can see connection status
✅ **Troubleshooting**: Identify real problems vs. placebo issues
✅ **Remote support**: Users send screenshots for diagnosis
✅ **Correlation**: Link poor bilateral sync to connection issues
✅ **Confidence**: "95% sync quality" is reassuring

### **Cons**
⚠️ **User anxiety**: Low RSSI might alarm non-technical users
⚠️ **Support burden**: Explaining -80 dBm is normal
⚠️ **False correlation**: Users blame RSSI when issue is elsewhere
⚠️ **Complexity**: More code to maintain
⚠️ **Minimal value**: BLE works fine down to -90 dBm anyway

### **Mitigation Strategies**
- Use normalized percentages, not raw RSSI
- Add reassuring text ("Good - normal for handheld device")
- Emphasize Time Sync Quality as primary indicator
- Hide raw metrics in developer mode
- Show composite health score (single glanceable number)

---

## Alternative Approaches Considered

### **1. Don't Expose RSSI at All**
**Rationale:** BLE is robust, RSSI doesn't correlate well with actual performance
**Verdict:** Still useful for extreme cases (moving out of range, metal shielding)

### **2. Only Show Warning When Bad**
**Approach:** Don't show connection health unless it drops below threshold
**Example:** "Warning: Weak connection detected. Move devices closer."
**Verdict:** Good for minimalist UI, but users can't proactively check

### **3. Show Only Time Sync Quality**
**Approach:** Reuse existing 0-100% metric, skip RSSI entirely
**Verdict:** Simpler, but doesn't help diagnose BLE vs. firmware issues

---

## Recommended Path Forward

1. **Test Bug #40 fix first** (absolute target time calculation)
2. **Add phase error tracking** to motor_task.c INACTIVE state
3. **Expose Time Sync Quality** to PWA (minimal effort, high value)
4. **Observe user feedback** - do users ask for more connection details?
5. **If needed, add composite health metric** with normalized RSSI

**Key Decision Point:**
If Time Sync Quality (95%) is sufficient to reassure users and diagnose issues, **don't add RSSI at all**. Only add it if users specifically report connection concerns that Time Sync Quality doesn't address.

---

## Future Enhancements

- **Historical trends:** Graph sync quality over 20-minute session
- **Predictive alerts:** "Connection degrading, may drop in 30 seconds"
- **Multi-device support:** Show health for all paired devices (future 3+ device setup)
- **Bluetooth 5 features:** Use Coded PHY for extended range mode

---

## References

- **Time Sync Quality Implementation:** `src/time_sync.c:time_sync_get_quality()`
- **Beacon Infrastructure:** `src/time_sync_task.c` (5-80 second adaptive interval)
- **Current RSSI Usage:** Beacon exchange in time sync protocol
- **BLE Characteristic Spec:** Configuration Service UUID base `...0200`

---

**Document Status:** Proposal for future implementation
**Next Action:** Wait for Bug #40 test results, then decide if connection health monitoring is needed based on user feedback.
