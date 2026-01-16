# UTLP v4 - Hyperdimensional Vector Time

**Universal Time Lord Protocol** (UTLP) v4 - Connectionless distributed time
synchronization using **vector time** (phase chords) instead of scalar timestamps.
Part of the **PHYRFLY Protocol Stack** (Protocol Trinity: UTLP/RFIP/SMSP).

> **v4 Foundation:** "Time is a chord, not a number."
>
> Vector time via 8-byte phase chords (residues modulo coprime primes).
> Integer-only HDC similarity. Stem cell depth model. Partition-resilient.

> **Historical Note:** For scalar time implementation (v3), see `README_scalar.md`.

## The Radical Idea

Traditional time synchronization uses scalar values:
- **NTP:** 64-bit timestamp (seconds + fraction)
- **PTP:** 80-bit timestamp with nanosecond precision
- **GPS:** Week number + time of week

UTLP v4 asks: **What if time were a vector, not a number?**

Instead of a single large number that wraps unpredictably, we represent time as
8 small residues, each cycling independently on coprime primes:

```
Scalar time:     1,234,567,890,123 microseconds
Vector time:     [142, 217, 84, 156, 203, 31, 178, 92]
                  ↑    ↑    ↑    ↑    ↑    ↑    ↑    ↑
                 %241 %251 %239 %233 %229 %227 %223 %211
```

**Why this matters:**
- **Partition detection:** HD similarity tells us if two nodes are close in time
- **Byzantine resilience:** Harder to forge plausible chords than scalar timestamps
- **Graceful degradation:** SMSP patterns work on phases, not absolute time
- **No aliasing for 261,000 years:** CRT reconstruction is unambiguous

## Current Status

| Phase | Name | Status | Description |
|-------|------|--------|-------------|
| **0** | HAL Preservation | ✅ COMPLETE | Timer HAL, stubs for N≥3 features |
| **1** | Genesis (N=1) | ✅ COMPLETE | Single device life, vector time native |
| **2** | First Contact (N=2) | 🔄 IN PROGRESS | Peer discovery, epoch resolution, texture tracking |
| **3** | Time Agreement | ⏳ Planned | Beacon exchange, offset convergence |
| **4** | HD Similarity | ⏳ Planned | Integer HDC, partition detection |
| **5** | SMSP Sync | ⏳ Planned | Synchronized LED blink |

### Phase 2 Progress

- ✅ Seismic chirp (3-burst beacon) with offset/jitter extraction
- ✅ Median-filtered offset for stable sync
- ✅ Offset-first epoch resolution (oldest device wins)
- ✅ Genesis pulse protection (established devices reject newborns)
- ✅ **Beacon interval texture tracking** (swarm state awareness)
- ✅ **Genesis pattern script** (SMSP-style playback definition)
- ✅ **Biological role taxonomy** (NAIVE/TIME_LORD/SOMATIC/OBSERVER)
- ✅ **N=2 hardware test:** Two C6s sync ✓, C6+DevKit sync ✓
- ✅ **Burst interval bug fix:** Now measures chirp intervals, not burst intervals
- ✅ **TIME UPDATE guard:** Prevent genesis peers from polluting established sync
- ⏳ **N=3 hardware test:** Pending re-test

## Quick Start

```bash
# Build for Seeed XIAO ESP32-C6
pio run -e utlp_xiao_esp32c6 -t upload

# Or for ESP32 DevKit
pio run -e utlp_esp32_devkit -t upload

# Monitor output
pio device monitor
```

**Transport Strategy:** ESP-NOW (802.11bgn action frames) first, then 802.15.4 later.
Arbors are controlled via API, not separate build environments.

Expected output (Phase 1 Genesis):
```
UTLP: Phase 1 initialization complete
UTLP: Starting 1Hz LED heartbeat - N=1 life begins!
UTLP: Heartbeat #1 | depth=128 | salt=0xA3F2 | ILC=47 us
UTLP:   chord=[142,217,84,156,203,31,178,92]
```

## Architecture

### Vector Time Foundation

Time is represented as an 8-byte **phase chord**:

```c
typedef uint8_t utlp_phase_chord_t[8];  // 8 residues, 8 bytes

// The 8 coprime primes (from utlp_config.h)
static const uint8_t PRIMES[8] = {241, 251, 239, 233, 229, 227, 223, 211};

// Computing chord from scalar (for initialization/logging)
void scalar_to_chord(uint64_t scalar_us, utlp_phase_chord_t chord) {
    for (int i = 0; i < 8; i++) {
        chord[i] = (uint8_t)(scalar_us % PRIMES[i]);
    }
}
```

**Properties:**
- Wire size: 8 bytes (same as scalar timestamp)
- Aliasing horizon: 261,000 years at 1 microsecond resolution
- Adjacent ticks: 7-8/8 similarity (detectable as "close")
- Partition threshold: <4/8 similarity indicates CRT ambiguity

### Stem Cell Depth Model

Lineage vitality uses biological stem cell / telomere dynamics:

```c
#define DEPTH_FRESH     128   // Somatic cell (fresh boot)
#define DEPTH_TIME_LORD 255   // Stem cell with telomerase
#define DEPTH_EXHAUSTED 0     // Cannot propagate further
```

**Resolution rules:**
1. Higher depth (more vitality) wins
2. Equal depth → oldest origin_time wins
3. True tie → lower MAC adopts from higher MAC

**Why this design:**
- Fresh boots start at 128, not 255 (prevents reboot attacks)
- Time Lords earn 255 through service (telomerase activation)
- Non-Time-Lords exhaust naturally over propagation hops

### Beacon Interval Texture (Swarm State Awareness)

"Time has texture" - beacon intervals reveal device state:

```c
// Genesis Pattern Script (SMSP-style playback definition)
static const genesis_step_t GENESIS_SCRIPT[5] = {
    { .start_ms = 0,     .end_ms = 1000,   .interval_ms = 100,   .tolerance_ms = 50 },   // Phase 1: Rapid
    { .start_ms = 1000,  .end_ms = 5000,   .interval_ms = 500,   .tolerance_ms = 200 },  // Phase 2: Fast
    { .start_ms = 5000,  .end_ms = 10000,  .interval_ms = 1000,  .tolerance_ms = 300 },  // Phase 3: Settling
    { .start_ms = 10000, .end_ms = 60000,  .interval_ms = 10000, .tolerance_ms = 2000 }, // Phase 4: Stabilizing
    { .start_ms = 60000, .end_ms = MAX,    .interval_ms = 60000, .tolerance_ms = 5000 }, // Phase 5: Steady
};

// Pattern matching: "Where in genesis is this peer?"
uint8_t phase = genesis_pattern_match(peer->interval_history.median_ms);
```

**Why this matters:**
- Genesis texture: rapid ramp (100ms → 500ms → 1s → 10s → 60s)
- Established texture: steady 60s intervals with low variance
- Pattern matching detects genesis without trusting claimed timestamps
- Self-observation: device tracks its own beacon texture for symmetry

**Texture-based adoption:**
- Devices with similar textures can sync
- Mismatched textures → established wins (genesis protection)
- Cannot be faked: observed behavior, not claimed values

### Integer HDC Similarity

Float-free similarity metric for embedded efficiency:

```c
uint8_t chord_similarity_int(const uint8_t *a, const uint8_t *b) {
    uint8_t matches = 0;
    const uint8_t PRIMES[8] = {241, 251, 239, 233, 229, 227, 223, 211};

    for (int i = 0; i < 8; i++) {
        // Circular distance on each prime's ring
        uint8_t diff = (a[i] > b[i]) ? (a[i] - b[i]) : (b[i] - a[i]);
        uint8_t wrap = PRIMES[i] - diff;
        uint8_t min_dist = (diff < wrap) ? diff : wrap;

        // Threshold: ~10% of prime value
        uint8_t threshold = PRIMES[i] / 10;
        if (min_dist <= threshold) {
            matches++;
        }
    }
    return matches;  // 0-8, higher = more similar
}
```

**Threshold semantics:**
- 8/8: Nearly identical time (within ~20 ticks)
- 6-7/8: Recent divergence (within ~100 ticks)
- 5/8: Acceptable for adoption (minimum threshold)
- <4/8: Partition detected or spoofed chord

## File Structure

### Core Implementation

| File | Purpose |
|------|---------|
| `utlp_config.h` | SSOT - All constants, primes, thresholds |
| `utlp.c` | Main protocol logic, Phase 1 Genesis |
| `utlp_phase.c/h` | HPLC phase engine, vector time |
| `utlp_transport.c/h` | Multi-arbor transport (ESP-NOW + 802.15.4) |
| `utlp_arbor.c/h` | Per-transport channel management |
| `utlp_smsp.c/h` | Synchronized Multimodal Score Protocol |
| `utlp_security.c/h` | Session salt, Bio-TOTP |

### HAL Layer (Preserved)

| File | Purpose |
|------|---------|
| `utlp_hal.h` | Platform abstraction API |
| `utlp_hal_esp32.c` | ESP32 base implementation |
| `utlp_hal_esp32c6_154.c` | ESP32-C6 with 802.15.4 |
| `utlp_hal_timer.h` | Timer abstraction (MCPWM) |
| `utlp_hal_timer_esp32.c` | ESP32 MCPWM implementation |
| `utlp_hal_security.c/h` | Hardware RNG, crypto |
| `rfip_hal.c/h` | Radio capability detection |

### Stubs (N≥3 Features - Not Implemented)

| File | Purpose | Why Stub |
|------|---------|----------|
| `utlp_trust.c/h` | Metabolic Ledger | Requires N≥3 for consensus |
| `utlp_immune.c/h` | Token bucket, anergy | Requires quorum sensing |
| `utlp_loom.c/h` | Time Lord elections | Requires Byzantine tolerance |

### Documentation

| File | Purpose |
|------|---------|
| `README.md` | This file (HD Vector Time) |
| `README_scalar.md` | Historical scalar time (v3) reference |
| `claude-code-crafting/` | Implementation guides, known issues |

## Design Principles

### N=2 First Contact Rule

At N=2, consensus is impossible (Byzantine requires 2f+1 nodes to tolerate f faults).
We use deterministic resolution:

1. **Chord-Origin Verification:** Verify peer's chord matches claimed origin_time
2. **Depth Comparison:** Higher depth wins (stem cell model)
3. **Origin Tiebreaker:** Older lineage wins
4. **MAC Tiebreaker:** Lower MAC adopts from higher MAC

### Defense Layers

| Layer | Attack Prevented | Mechanism |
|-------|------------------|-----------|
| Chord-Origin Verification | Chord fabrication | Must maintain plausible time history |
| Stem Cell Depth | Reboot spam | Fresh boots capped at 128, not 255 |
| Session Salt | Stale epoch adoption | Detects rebooted peers |

### Known Limitations (Accepted at N=2)

| Attack | Why Accepted |
|--------|--------------|
| Telomere count lying | No third party to verify (deferred to N≥3) |
| First contact fabrication | Byzantine impossible at N=2 |
| Sybil attacks | Requires hardware attestation at N≥3 |

## Validation

### Phase 1 Validation Gates (All Passing)

- [x] Single device boots, generates unique session_salt
- [x] LED blinks at 1Hz using HPLC phase engine
- [x] origin_time = boot moment, depth = 128 (somatic cell)
- [x] Epoch regenerates fresh on every power cycle (no RTC)
- [x] Phase chord computed each cycle and logged in heartbeat

### Phase 2 Validation Gates (Upcoming)

- [ ] Two devices discover each other
- [ ] Higher depth (more vital) wins resolution
- [ ] Depth DECREMENTS on adoption (telomere shortening)
- [ ] Session_salt unchanged after adoption
- [ ] Reboot detection works (same MAC, new salt)
- [ ] Exhausted lineage (depth=0) cannot propagate
- [ ] Chord-origin verification rejects implausible peers
- [ ] Fresh boots (128) don't immediately dominate Time Lords (255)

## References

### Technical Documents

- `docs/misc/UTLP_Technical_Supplement_S3.md` - Vector Time (Claims 262-275)
- `docs/misc/UTLP_Technical_Supplement_S4.md` - Partition Handling (Claims 276-277)
- `scripts/utlp_vector_time.py` - Python reference implementation

### Biological Model

- `docs/misc/UTLP_Technical_Supplement_S2.md` - Biological Governance

### Plan Document

- `C:\Users\sckir\.claude\plans\tender-squishing-simon.md` - Implementation meta-plan

## License

SPDX-License-Identifier: GPL-3.0-or-later
