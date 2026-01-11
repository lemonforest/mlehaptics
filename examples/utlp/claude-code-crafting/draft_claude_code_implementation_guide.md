# Claude Code Implementation Guide: N=2 Epoch Coalescence

**Document Status:** DRAFT for review  
**Prepared for:** Steven Kirkland / mlehaptics Project  
**Date:** January 5, 2026  
**Target:** ESP32-C6 / mlehaptics embedded BLE EMDR device

---

## Purpose

This document provides complete implementation guidance for the N=2 epoch coalescence protocol. It is designed to be consumed by Claude Code or any implementer building the PHYRFLY timing layer.

---

## 1. Core Data Structures

### 1.1 Epoch State (7 bytes)

```c
typedef struct __attribute__((packed)) {
    uint32_t origin_time;      // Epoch lineage origin (seconds since device epoch or Unix time)
    uint8_t  depth;            // Inheritance depth (0=originator, >0=inherited, saturates at 255)
    uint8_t  session_salt[2];  // Random session identifier (regenerated on each boot)
} epoch_state_t;

// Compile-time assertion
_Static_assert(sizeof(epoch_state_t) == 7, "epoch_state_t must be 7 bytes");
```

### 1.2 Peer Record

```c
typedef struct {
    uint8_t  mac[6];               // Peer MAC address
    uint8_t  session_salt[2];      // Last known session salt from peer
    uint32_t last_seen;            // Timestamp of last communication
    uint8_t  peer_depth;           // Last known depth from peer
    uint32_t peer_origin;          // Last known origin_time from peer
    bool     is_known;             // Have we completed first contact?
} peer_record_t;

#define MAX_PEERS 8  // Adjust based on memory constraints
peer_record_t known_peers[MAX_PEERS];
```

### 1.3 Device State

```c
typedef struct {
    epoch_state_t epoch;           // Current epoch state
    uint32_t      boot_time;       // When this device booted (local monotonic)
    uint8_t       peer_count;      // Current N (1 = alone, 2+ = swarm)
    bool          has_ever_met;    // Has this device ever seen another?
} device_state_t;

device_state_t self;
```

---

## 2. Initialization

### 2.1 Boot Sequence

```c
void epoch_init(void) {
    // Generate random session salt
    esp_fill_random(self.epoch.session_salt, 2);
    
    // Set origin time to boot time
    self.epoch.origin_time = get_current_time();  // Implementation-specific
    
    // Depth 0 = we are originator (never inherited)
    self.epoch.depth = 0;
    
    // Record boot time
    self.boot_time = get_monotonic_time();
    
    // We start alone
    self.peer_count = 1;
    self.has_ever_met = false;
    
    // Clear peer table
    memset(known_peers, 0, sizeof(known_peers));
    
    log_event("BOOT", "origin=%u depth=0 salt=%02x%02x", 
              self.epoch.origin_time,
              self.epoch.session_salt[0], 
              self.epoch.session_salt[1]);
}
```

### 2.2 Critical: Do NOT Reset on Wake from Sleep

If device uses light sleep or deep sleep with RTC memory retention:

```c
void on_wake_from_sleep(void) {
    // DO NOT call epoch_init()
    // DO NOT regenerate session_salt
    // Epoch state persists through sleep
    
    // Only regenerate salt on true cold boot
    // (detected by RTC memory validation flag)
}
```

---

## 3. First Contact Detection

### 3.1 Is This First Contact?

```c
typedef enum {
    CONTACT_NEW_PEER,           // Never seen this MAC before
    CONTACT_KNOWN_PEER,         // Known MAC, same session
    CONTACT_REBOOTED_PEER       // Known MAC, different session salt
} contact_type_t;

contact_type_t classify_contact(uint8_t *mac, uint8_t *salt) {
    peer_record_t *peer = find_peer_by_mac(mac);
    
    if (peer == NULL) {
        return CONTACT_NEW_PEER;
    }
    
    if (memcmp(peer->session_salt, salt, 2) == 0) {
        return CONTACT_KNOWN_PEER;
    }
    
    return CONTACT_REBOOTED_PEER;
}
```

### 3.2 First Contact Triggers Re-Evaluation

Both `CONTACT_NEW_PEER` and `CONTACT_REBOOTED_PEER` trigger epoch resolution:

```c
void on_peer_message(uint8_t *mac, epoch_state_t *peer_epoch) {
    contact_type_t contact = classify_contact(mac, peer_epoch->session_salt);
    
    switch (contact) {
        case CONTACT_NEW_PEER:
            handle_first_contact(mac, peer_epoch);
            break;
            
        case CONTACT_REBOOTED_PEER:
            log_event("REBOOT_DETECTED", "mac=%s", mac_to_string(mac));
            invalidate_peer(mac);  // Clear old record
            handle_first_contact(mac, peer_epoch);
            break;
            
        case CONTACT_KNOWN_PEER:
            handle_ongoing_contact(mac, peer_epoch);
            break;
    }
}
```

---

## 4. Epoch Resolution Algorithm

### 4.1 First Contact Handler

```c
void handle_first_contact(uint8_t *mac, epoch_state_t *peer) {
    bool i_should_adopt = false;
    
    // Case 1: Both originators (depth == 0)
    if (self.epoch.depth == 0 && peer->depth == 0) {
        // Oldest origin wins
        i_should_adopt = (peer->origin_time < self.epoch.origin_time);
        log_event("RESOLUTION", "both_originators: peer_origin=%u my_origin=%u adopt=%d",
                  peer->origin_time, self.epoch.origin_time, i_should_adopt);
    }
    
    // Case 2: I'm originator, peer is descendant
    else if (self.epoch.depth == 0 && peer->depth > 0) {
        // Validated lineage beats untested isolation
        i_should_adopt = true;
        log_event("RESOLUTION", "i_originator_peer_descendant: adopting peer depth=%u",
                  peer->depth);
    }
    
    // Case 3: I'm descendant, peer is originator
    else if (self.epoch.depth > 0 && peer->depth == 0) {
        // I have validated lineage, peer is untested
        i_should_adopt = false;
        log_event("RESOLUTION", "i_descendant_peer_originator: keeping mine depth=%u",
                  self.epoch.depth);
    }
    
    // Case 4: Both descendants
    else {
        // Both validated, oldest origin wins
        i_should_adopt = (peer->origin_time < self.epoch.origin_time);
        log_event("RESOLUTION", "both_descendants: peer_origin=%u my_origin=%u adopt=%d",
                  peer->origin_time, self.epoch.origin_time, i_should_adopt);
    }
    
    // Execute adoption if needed
    if (i_should_adopt) {
        adopt_epoch(peer);
    }
    
    // Record this peer
    register_peer(mac, peer);
    
    // Update N count
    self.peer_count++;
    self.has_ever_met = true;
}
```

### 4.2 Epoch Adoption

```c
void adopt_epoch(epoch_state_t *source) {
    uint32_t old_origin = self.epoch.origin_time;
    uint8_t  old_depth  = self.epoch.depth;
    
    // Adopt origin time
    self.epoch.origin_time = source->origin_time;
    
    // Increment depth with saturation
    if (source->depth < 255) {
        self.epoch.depth = source->depth + 1;
    } else {
        self.epoch.depth = 255;  // Saturate, don't wrap
    }
    
    // DO NOT change session_salt - we did not reboot
    
    log_event("ADOPT", "old_origin=%u new_origin=%u old_depth=%u new_depth=%u",
              old_origin, self.epoch.origin_time, old_depth, self.epoch.depth);
}
```

### 4.3 Tiebreaker for Identical Origin Times

```c
// Add to first contact handler when origins are equal:
if (peer->origin_time == self.epoch.origin_time) {
    // True tie - use MAC as arbitrary tiebreaker
    // Lower MAC adopts from higher MAC
    if (memcmp(get_own_mac(), mac, 6) < 0) {
        i_should_adopt = true;
    } else {
        i_should_adopt = false;
    }
    log_event("TIEBREAKER", "identical_origin: using MAC comparison");
}
```

---

## 5. N Transitions

### 5.1 N=1 → N=2 Transition

Handled by first contact logic above. Key points:
- First contact triggers resolution
- Winner determined by depth + origin rules
- Both devices converge to same epoch

### 5.2 N=2 → N=1 Transition (Peer Loss)

```c
void on_peer_timeout(uint8_t *mac) {
    peer_record_t *peer = find_peer_by_mac(mac);
    if (peer == NULL) return;
    
    // Mark peer as gone
    peer->is_known = false;
    self.peer_count--;
    
    log_event("PEER_LOST", "mac=%s remaining_peers=%u", 
              mac_to_string(mac), self.peer_count);
    
    // CRITICAL: Do NOT modify epoch state
    // Time continues. We are now sole carrier of this lineage.
    // origin_time: unchanged
    // depth: unchanged
    // session_salt: unchanged
}
```

### 5.3 N=2 → N≥3 Transition

```c
void on_new_peer_while_paired(uint8_t *mac, epoch_state_t *peer) {
    // We already have a peer, this is a third
    contact_type_t contact = classify_contact(mac, peer->session_salt);
    
    if (contact == CONTACT_NEW_PEER || contact == CONTACT_REBOOTED_PEER) {
        // New device joining existing pair
        // Same resolution rules apply
        handle_first_contact(mac, peer);
    }
    
    // At N≥3, consensus mechanisms can now operate
    // (Implementation of N≥3 consensus is separate from this document)
}
```

---

## 6. Message Format

### 6.1 Epoch Advertisement

Include in periodic broadcasts:

```c
typedef struct __attribute__((packed)) {
    uint8_t       msg_type;        // MESSAGE_TYPE_EPOCH_ADV
    epoch_state_t epoch;           // 7 bytes
    uint8_t       peer_count;      // Current N (for informational purposes)
} epoch_advertisement_t;

#define MESSAGE_TYPE_EPOCH_ADV 0x01
```

### 6.2 Broadcast Interval

```c
#define EPOCH_BROADCAST_INTERVAL_MS 1000  // 1 second typical
#define EPOCH_BROADCAST_JITTER_MS   100   // Random jitter to avoid collision
```

---

## 7. Timing Continuity Guarantees

### 7.1 Monotonic Progression

```c
uint32_t get_epoch_time(void) {
    // Returns time relative to epoch origin
    uint32_t local_now = get_monotonic_time();
    uint32_t elapsed_since_boot = local_now - self.boot_time;
    
    // If we're originator, epoch time = local time
    // If we adopted, we calculate offset
    return self.epoch.origin_time + elapsed_since_boot;
}
```

### 7.2 No Backwards Jumps

After epoch adoption, time may *appear* to jump forward (we adopt an older origin). It should NEVER jump backward. Validation:

```c
static uint32_t last_reported_time = 0;

uint32_t get_epoch_time_safe(void) {
    uint32_t t = get_epoch_time();
    
    if (t < last_reported_time) {
        // This should never happen
        log_error("TIME_REGRESSION", "attempted %u but last was %u", 
                  t, last_reported_time);
        t = last_reported_time + 1;  // Force forward progress
    }
    
    last_reported_time = t;
    return t;
}
```

---

## 8. Persistence

### 8.1 What to Persist (RTC Memory or NVS)

If using deep sleep with state retention:

```c
typedef struct {
    uint32_t magic;            // Validation marker
    epoch_state_t epoch;       // Full epoch state
    uint8_t peer_count;        // For continuity
    uint32_t checksum;         // Integrity check
} persisted_state_t;

#define PERSIST_MAGIC 0x45504F43  // "EPOC"
```

### 8.2 What NOT to Persist

- Peer table (reconstruct from live discovery)
- Timing offsets (recalculate from monotonic clock)

### 8.3 Cold Boot Detection

```c
bool is_cold_boot(void) {
    persisted_state_t *state = get_rtc_memory();
    
    if (state->magic != PERSIST_MAGIC) return true;
    if (calculate_checksum(state) != state->checksum) return true;
    
    return false;
}

void on_boot(void) {
    if (is_cold_boot()) {
        epoch_init();  // Fresh start
    } else {
        restore_epoch_from_rtc();  // Continue session
    }
}
```

---

## 9. Testing Scenarios

### 9.1 Unit Tests Required

```c
// Test: Two originators, different ages
void test_two_originators_different_age(void);

// Test: Two originators, same age (tiebreaker)
void test_two_originators_same_age(void);

// Test: Originator meets descendant (descendant wins)
void test_originator_meets_descendant(void);

// Test: Descendant meets originator (descendant wins)
void test_descendant_meets_originator(void);

// Test: Two descendants, different origins
void test_two_descendants_different_origin(void);

// Test: Peer reboot detection
void test_peer_reboot_detection(void);

// Test: Depth saturation at 255
void test_depth_saturation(void);

// Test: N=2 to N=1 preserves state
void test_peer_loss_preserves_epoch(void);

// Test: Time never goes backward
void test_time_monotonicity(void);
```

### 9.2 Integration Tests Required

```
Scenario A: Fresh boot → N=1 → N=2 → N=1 → N=2 (same peer)
Scenario B: Fresh boot → N=1 → N=2 → N=1 → N=2 (different peer)
Scenario C: Two devices boot simultaneously
Scenario D: Old isolate meets young descendant
Scenario E: Young isolate meets old descendant
Scenario F: Rapid reboot cycles from peer
```

---

## 10. Debug Output Format

Standardized logging for debugging:

```
[EPOCH] BOOT origin=1704067200 depth=0 salt=a3f2
[EPOCH] PEER_DISCOVERED mac=AA:BB:CC:DD:EE:FF origin=1704067100 depth=2 salt=b1c3
[EPOCH] RESOLUTION both_originators: peer_origin=1704067100 my_origin=1704067200 adopt=1
[EPOCH] ADOPT old_origin=1704067200 new_origin=1704067100 old_depth=0 new_depth=3
[EPOCH] PEER_REGISTERED mac=AA:BB:CC:DD:EE:FF peer_count=2
[EPOCH] PEER_LOST mac=AA:BB:CC:DD:EE:FF remaining_peers=1
[EPOCH] REBOOT_DETECTED mac=AA:BB:CC:DD:EE:FF
```

---

## 11. Implementation Checklist

```
[ ] epoch_state_t is exactly 7 bytes (packed)
[ ] session_salt generated from hardware RNG at boot
[ ] session_salt NOT regenerated on sleep/wake
[ ] depth increments with saturation (max 255)
[ ] depth only resets on cold boot
[ ] First contact triggers resolution for NEW and REBOOTED peers
[ ] KNOWN peers do not re-trigger resolution
[ ] Epoch adoption copies origin_time
[ ] Epoch adoption increments depth
[ ] Epoch adoption does NOT change session_salt
[ ] Peer loss does NOT modify epoch state
[ ] Time never jumps backward
[ ] Tiebreaker exists for identical origin_time
[ ] All state transitions are logged
[ ] Persistence handles cold vs warm boot
```

---

## 12. What This Document Does NOT Cover

- N≥3 consensus mechanisms (separate protocol layer)
- Stratum/health/tenure metrics (separate protocol layer)
- Application-layer synchronization (uses epoch as foundation)
- BLE transport specifics (ESP-NOW, GATT, etc.)
- Power management integration

These are layered on top of the epoch foundation defined here.

---

*End of Implementation Guide*
