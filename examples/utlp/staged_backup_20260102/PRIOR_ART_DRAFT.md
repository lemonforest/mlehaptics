# UTLP Phase 8: Prior Art Claims Draft (237+)

## Overview

This document drafts prior art claims for **Phase 8: Multi-Arbor Architecture** - enabling cross-manufacturer 802.15.4 timing swarms using raw IEEE MAC Data Frames.

**Key Discovery:** All three target platforms (ESP32-C6, MG24, nRF52840) have TRUE hardware-scheduled TX for 802.15.4, achieving ~1µs precision. The ESP32-C6's `esp_ieee802154_transmit_at()` API was previously underdocumented but fully functional.

---

## Section 1: Raw MAC Data Frame for Connectionless Timing

### Claim 237: Raw MAC Data Frame Format (FCF 0x8841)

**Title:** Connectionless timing synchronization using IEEE 802.15.4 raw MAC Data Frames

**Description:** A method for distributed time synchronization that uses IEEE 802.15.4 raw MAC Data Frames (NOT ZigBee/Thread/Matter stacks) with specific frame control field configuration:

| Field | Value | Purpose |
|-------|-------|---------|
| Frame Type | Data (001) | Timing payload carrier |
| Security | Disabled (0) | Minimal overhead |
| ACK Request | No (0) | Broadcast, connectionless |
| PAN ID Compression | Yes (1) | Efficient addressing |
| Dest Addr Mode | Short (10) | Broadcast 0xFFFF |
| Src Addr Mode | Extended (11) | 8-byte EUI-64 |

**FCF Value:** 0x8841 (little-endian: 0x41, 0x88)

**Benefits over protocol stacks:**
- Stack size: ~2 KB vs ~200 KB for ZigBee/Thread
- No certification costs (~$5000+/year for ZigBee)
- Deterministic latency (no mesh routing)
- Cross-vendor compatibility (IEEE standard only)

### Claim 238: Reserved PAN ID for Timing Namespace

**Title:** Dedicated PAN ID reservation for connectionless timing traffic

**Description:** Reservation of PAN ID `0xCAFE` as a well-known identifier for UTLP timing traffic, enabling:
- Coexistence with other 802.15.4 networks on same channel
- Simple frame filtering at MAC layer
- No commissioning or network formation required
- Immediate participation upon power-on

### Claim 239: SFD-Relative Timestamp Capture

**Title:** Start Frame Delimiter-relative timing for microsecond-precision synchronization

**Description:** Capture of received frame timestamps at the SFD (Start Frame Delimiter) detection point, BEFORE MAC layer processing, to minimize software-induced jitter:

```
┌──────────────────────────────────────────────────────────┐
│                 802.15.4 PHY Packet                      │
├──────────┬───────────┬───────────┬───────────────────────┤
│ Preamble │    SFD    │    PHR    │      PSDU (MAC)       │
│ (32 bits)│  (8 bits) │ (8 bits)  │   (Frame + FCS)       │
└──────────┴─────┬─────┴───────────┴───────────────────────┘
                 │
                 └── T1/T2 capture point (before MAC latency)
```

**Platform APIs:**
- ESP32-C6: Software timestamp at ISR (best-effort ~10µs)
- MG24 RAIL: `RAIL_GetRxTimeSyncWordEnd()` (hardware, ~0.1µs)
- nRF52840: `EVENTS_ADDRESS` + Timer capture (hardware, ~0.1µs)

---

## Section 2: Hardware-Scheduled TX Discovery

### Claim 240: ESP32-C6 Hardware-Scheduled TX

**Title:** Discovery and utilization of undocumented `esp_ieee802154_transmit_at()` for hardware-precise timing

**Description:** The ESP32-C6's 802.15.4 driver includes a hardware-scheduled transmission API that was previously underdocumented:

```c
esp_err_t esp_ieee802154_transmit_at(
    const uint8_t *frame,
    size_t frame_length,
    bool cca,
    uint32_t time  // Absolute hardware timer value
);
```

**Key Insight:** This API exists for CSL (Coordinated Sampled Listening) and TSCH (Time Slotted Channel Hopping) support but is fully functional for raw timing applications.

**Precision:** ~1µs (same as MG24 and nRF52840)

**Prior Misconception:** Documentation suggested ESP32-C6 required software scheduling, but hardware capability was always present.

### Claim 241: Cross-Manufacturer Hardware TX Parity

**Title:** Unified hardware-scheduled TX across three major 802.15.4 platforms

**Description:** All three target platforms have equivalent hardware-scheduled TX capabilities:

| Platform | API | Jitter Floor | Method |
|----------|-----|--------------|--------|
| ESP32-C6 | `esp_ieee802154_transmit_at()` | ~1µs | Radio timer |
| MG24 (RAIL) | `RAIL_StartScheduledTx()` | ~0.1µs | Radio timer |
| nRF52840 | `nrf_802154_transmit_raw_at()` | ~0.1µs | TIMER + PPI |

**Implication:** Cross-manufacturer timing meshes can achieve uniform precision without platform-specific workarounds.

### Claim 242: Hardened ISR as Fallback

**Title:** Level-5 interrupt scheduling as degraded fallback for hardware TX failures

**Description:** When hardware-scheduled TX fails (late scheduling, hardware busy), a fallback mechanism using high-priority interrupts provides graceful degradation:

1. GPTimer at 1MHz resolution
2. Level-5 interrupt (NMI-like priority on ESP32)
3. IRAM-resident TX code (no Flash cache misses)
4. Achieves ~10µs jitter (10× better than spin-wait)

**Use Case:** Transient hardware contention, multi-arbor environments with shared radio.

---

## Section 3: Per-Transport Selective Dormancy

### Claim 243: Arbor/Soma Multi-Transport Architecture

**Title:** Hierarchical transport management with central phase aggregation

**Description:** A node architecture where multiple radio transports ("arbors") feed a central timing phase ("soma"):

```
┌─────────────────────────────────────────────────────────────────┐
│                      SOMA (Central Phase)                       │
│   Aggregates observations from all arbors                       │
│   Maintains unified atomic time                                 │
│                                                                 │
│   ┌─────────┐     ┌─────────┐     ┌─────────┐                   │
│   │  ARBOR  │     │  ARBOR  │     │  ARBOR  │                   │
│   │  WiFi   │     │  15.4   │     │  BLE    │                   │
│   │ ESP-NOW │     │ 802.15.4│     │ NimBLE  │                   │
│   └────┬────┘     └────┬────┘     └────┬────┘                   │
│        │ ACTIVE        │ DORMANT       │ WAKING                 │
│        ▼               ▼               ▼                        │
│   [Beacons]       [Sleeping]      [Re-verifying]               │
└─────────────────────────────────────────────────────────────────┘
```

**Benefits:**
- Independent transport lifecycle management
- Isolated failure domains
- Energy-adaptive duty cycling

### Claim 244: Selective Arbor Yield (`utlp_arbor_yield()`)

**Title:** Per-transport hibernation with reputation ledger preservation

**Description:** API for selectively hibernating a single transport while maintaining others:

```c
typedef struct {
    uint32_t expected_duration_ms;  // Hint for peers
    bool     broadcast_beacon;      // Announce dormancy to swarm
    bool     preserve_ledger;       // Keep reputation snapshot
} utlp_dormancy_params_t;

esp_err_t utlp_arbor_yield(utlp_arbor_id_t id, const utlp_dormancy_params_t *params);
```

**Process:**
1. Snapshot arbor's reputation ledger
2. Broadcast "Dormant" beacon to transport-specific peers
3. Physical layer shutdown (WiFi, 802.15.4, or BLE)
4. State transition to DORMANT

**Use Cases:**
- Isolation testing (silence WiFi to prove 802.15.4 stability)
- Energy conservation (hibernate high-power transports)
- Security/immunity (shutdown contaminated arbor)

### Claim 245: Degraded Re-Entry with Stratum Penalty

**Title:** Trust-aware reactivation of dormant transports

**Description:** When a dormant arbor wakes, it enters at elevated stratum (lower authority) until re-verified:

```c
#define UTLP_DEGRADED_REENTRY_PENALTY   2  // +2 stratum levels
#define UTLP_REENTRY_VERIFY_BEACONS     5  // Beacons to verify

// WAKING state: Listen-only, no TX
// After N consistent beacons matching Soma phase → ACTIVE
```

**Rationale:** Prevents "Phantom Arbor" attack where a waking transport could corrupt the swarm with stale timing data.

### Claim 246: Dormancy Beacon for Swarm Awareness

**Title:** Broadcast distinction between "sleeping" and "dead" nodes

**Description:** Before entering dormancy, arbors optionally broadcast a beacon indicating:
- Expected dormancy duration
- Current atomic time
- Transport identifier

**Benefit:** Peers can distinguish "sleeping friend" from "dead node," enabling smarter peer table management and avoiding unnecessary trust decay.

---

## Section 4: Steel-Manned Experiment Protocol

### Claim 247: Arbor Isolation Testing Methodology

**Title:** Controlled experiment to prove transport-specific timing stability

**Description:** Experimental protocol using a homogeneous swarm (e.g., "Box of C6s") to definitively prove arbor isolation:

| Step | Action | Measurement |
|------|--------|-------------|
| 1 | Baseline: All arbors active (802.15.4 + WiFi) | Aggregate phase jitter |
| 2 | Half nodes: `utlp_arbor_yield(UTLP_ARBOR_WIFI)` | — |
| 3 | External auditor measures 15.4-only stability | Phase jitter (µs) |
| 4 | Compare 802.15.4-only vs dual-arbor stability | Statistical significance |

**Hypothesis:** 802.15.4-only nodes achieve lower jitter than dual-arbor nodes due to elimination of WiFi software scheduler interference.

---

## Implementation Files

| File | Claims Supported |
|------|------------------|
| `utlp_hal_802154.h` | 237, 238, 239 |
| `utlp_hal_esp32c6_154.c` | 240, 242 |
| `utlp_hal_mg24_154.c` | 241 (stub) |
| `utlp_hal_nrf52840_154.c` | 241 (stub) |
| `utlp_arbor.h` | 243, 244, 245, 246 |
| `utlp_arbor.c` | 244, 245, 246 |

---

## License

**CC0 1.0 Universal (Public Domain Dedication)**

This defensive publication is released to the public domain to prevent patent claims on these fundamental techniques.

---

*Draft prepared for integration into UTLP Technical Supplement S2/S3*
