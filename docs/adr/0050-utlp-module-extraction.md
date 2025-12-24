# AD050: UTLP Module Extraction

**Date:** 2025-12-24
**Phase:** Phase 8 (Architecture)
**Status:** Proposed
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of time synchronization protocol implementation,
facing the need for a clean, portable reference implementation,
we decided to extract UTLP (Universal Time-Lite Protocol) into a standalone module (`utlp.c/h`),
and neglected keeping time sync tightly coupled to application code,
to achieve portability across ESP-IDF projects and clear security boundaries,
accepting that minor refactoring is required to separate protocol from application concerns.

---

## Problem Statement

The current time synchronization implementation in `time_sync.c` mixes three concerns:

1. **Pure UTLP protocol** - Beacon format, stratum calculation, offset/drift computation
2. **EMDR application layer** - motor_epoch, pattern scheduling, bilateral coordination
3. **Transport layer** - ESP-NOW send/receive, BLE characteristics

This coupling makes the protocol:
- Difficult to reuse in other projects
- Hard to reason about security boundaries
- Less suitable as a reference implementation for academic/research use

---

## Context

### Current Architecture

```
time_sync.c (1200+ lines)
├── Beacon format and parsing
├── NTP-style offset calculation
├── Drift rate estimation (EMA filter)
├── Motor epoch management (EMDR-specific)
├── Pattern scheduling integration (EMDR-specific)
└── Transport handling (ESP-NOW callbacks)

espnow_transport.c
└── Raw send/receive + encryption
```

### Security Architecture Insight

During Bug #111 investigation, a key architectural principle emerged:

**Time beacons should be unencrypted** - Time is a public utility
- GPS satellites broadcast unencrypted time
- NTP uses UDP (no encryption at protocol level)
- PTP (IEEE 1588) works over raw Ethernet
- Time itself is not sensitive data

**Application data should always be encrypted** - Whether we think it's sensitive or not
- Coordination messages (pattern commands)
- Settings synchronization
- Any future application-layer extensions

### Prior Art

The project's `docs/Connectionless_Distributed_Timing_Prior_Art.md` provides extensive English documentation of the time synchronization approach, making UTLP extraction valuable for:
- Academic reference
- Open-source community contribution
- Future ESP-IDF projects requiring sub-millisecond sync

---

## Decision

We will extract the Universal Time-Lite Protocol (UTLP) into a standalone module pair:

### Layer Separation

```
utlp.c/h              ← Pure protocol: beacon format, stratum, offset/drift
                         Transport-agnostic, no application knowledge
                         Uses platform time API only

time_sync.c/h         ← EMDR wrapper: motor_epoch, application integration
                         Uses utlp_ API underneath
                         Handles application-specific timing needs

espnow_transport.c    ← Just transport: send/receive bytes
                         AES encryption for application data
                         Passes raw bytes to UTLP (unencrypted)
```

### UTLP Public API (Proposed)

```c
// utlp.h - Universal Time-Lite Protocol

// Beacon structure (transport-agnostic)
typedef struct __attribute__((packed)) {
    uint8_t  version;          // Protocol version (1)
    uint8_t  stratum;          // Time quality (1=crystal, 2=synced)
    uint16_t sequence;         // Monotonic counter (replay detection)
    int32_t  drift_rate_ppb;   // Drift rate in parts-per-billion
    uint64_t origin_time_us;   // Sender's local time when beacon created
} utlp_beacon_t;

// Initialize UTLP state
esp_err_t utlp_init(bool is_reference_clock);

// Create beacon for transmission (SERVER)
esp_err_t utlp_create_beacon(utlp_beacon_t *beacon);

// Process received beacon (CLIENT)
esp_err_t utlp_process_beacon(const utlp_beacon_t *beacon, uint64_t rx_time_us);

// Get synchronized time
uint64_t utlp_get_synced_time_us(void);

// Get offset from reference clock
int64_t utlp_get_offset_us(void);

// Get current drift rate estimate
int32_t utlp_get_drift_ppb(void);

// Get sync quality (0-100%)
uint8_t utlp_get_quality(void);

// Check if synchronized
bool utlp_is_synchronized(void);
```

### Security Boundary

```
                    UNENCRYPTED              ENCRYPTED
                    (Public Time)            (Private Data)
                         │                        │
                         ▼                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    espnow_transport.c                        │
├─────────────────────────────────────────────────────────────┤
│  utlp_beacon_t      │        coordination_msg_t             │
│  (raw bytes)        │        (AES-128 encrypted)            │
└──────────┬──────────┴──────────────────┬────────────────────┘
           │                              │
           ▼                              ▼
┌──────────────────┐          ┌───────────────────────────────┐
│    utlp.c/h      │          │      time_sync.c/h            │
│                  │          │                               │
│  - Offset calc   │          │  - motor_epoch                │
│  - Drift EMA     │          │  - Pattern scheduling         │
│  - Stratum       │          │  - Bilateral coordination     │
│  - Quality       │          │                               │
└──────────────────┘          └───────────────────────────────┘
```

---

## Consequences

### Benefits

- **Portability**: UTLP can be extracted and used in any ESP-IDF project
- **Clear security model**: Time = public, Everything else = encrypted
- **Academic value**: Clean reference implementation for prior art documentation
- **Testability**: Pure protocol logic can be unit tested without hardware
- **Maintainability**: Changes to time sync don't affect application logic

### Drawbacks

- **Refactoring effort**: Requires careful extraction from existing code
- **API boundary**: Slight overhead from function calls between layers
- **Two files to maintain**: Instead of one monolithic time_sync.c

---

## Options Considered

### Option A: Keep Current Architecture

**Pros:**
- No refactoring work required
- Single file for all time sync concerns

**Cons:**
- Not portable to other projects
- Security boundaries unclear
- Difficult to unit test protocol logic

**Selected:** NO
**Rationale:** Misses opportunity for clean, reusable implementation

### Option B: UTLP Module Extraction (Selected)

**Pros:**
- Clean separation of concerns
- Portable reference implementation
- Clear security boundaries
- Aligns with GPS/NTP/PTP philosophy

**Cons:**
- Requires refactoring work
- Slight API overhead

**Selected:** YES
**Rationale:** Long-term architectural benefits outweigh one-time refactoring cost

### Option C: Full Protocol Rewrite

**Pros:**
- Could incorporate additional features
- Start fresh with lessons learned

**Cons:**
- Significant development time
- Risk of introducing new bugs
- Current implementation is proven stable

**Selected:** NO
**Rationale:** Current implementation works well; extraction preserves proven code

---

## Related Decisions

### Related
- [AD039](0039-time-synchronization-protocol.md) - Original time sync protocol
- [AD043](0043-filtered-time-synchronization.md) - EMA filter design (will move to utlp.c)
- [AD041](0041-predictive-bilateral-synchronization.md) - Drift prediction (will remain in time_sync.c)
- [AD047](0047-scheduled-pattern-playback.md) - Pattern scheduling (uses time_sync API)
- [AD048](0048-espnow-adaptive-transport-hardware-acceleration.md) - Transport layer concerns

---

## Implementation Notes

### Migration Steps

1. **Create utlp.h** - Define beacon structure and pure protocol API
2. **Create utlp.c** - Extract offset/drift calculation from time_sync.c
3. **Refactor time_sync.c** - Use utlp_ API for time calculations
4. **Update espnow_transport.c** - Route beacons through UTLP (unencrypted)
5. **Update documentation** - Link UTLP to prior art publication

### Code References (Current)

Functions to extract into utlp.c:
- `time_sync.c:calculate_offset()` → `utlp_process_beacon()`
- `time_sync.c:update_drift_rate()` → internal to utlp.c
- `time_sync.c:perform_periodic_update()` (beacon creation part) → `utlp_create_beacon()`
- `time_sync.c:time_sync_get_synchronized_time_us()` → `utlp_get_synced_time_us()`

Functions to keep in time_sync.c:
- Motor epoch management
- Pattern scheduling integration
- Application-level coordination

### Testing & Verification

- Unit tests for utlp.c (host-based, no hardware needed)
- Integration tests with existing bilateral sync tests
- Verify unencrypted beacons work (sequence/nonce for replay detection)
- 90-minute stress test after refactor

---

## JPL Coding Standards Compliance

- Rule #1: No dynamic memory allocation - All UTLP structures statically allocated
- Rule #2: Fixed loop bounds - EMA filter has bounded iterations
- Rule #3: No recursion - Linear processing only
- Rule #5: Return value checking - All API calls return esp_err_t
- Rule #8: Defensive logging - Stratum changes, sync events logged

---

## Future Considerations

### Potential UTLP Enhancements (Post-Extraction)

1. **Multi-source sync** - Accept beacons from multiple servers
2. **Hardware timestamping** - Use ESP32 WiFi timestamp registers
3. **PTPv2 interoperability** - Map UTLP to IEEE 1588 concepts
4. **Documentation** - Standalone README for extraction

### Standalone Distribution

After extraction, UTLP could be:
- Published as ESP-IDF component
- Referenced in academic papers
- Used as teaching example for embedded time sync

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-12-24
