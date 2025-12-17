# Universal Time Layer Protocol

**Transport-Agnostic Time Synchronization for Distributed Embedded Systems**

*mlehaptics Project — Technical Report v2.0 — December 2025*

> *"Time is a Public Utility."*

**Contributors:** Steve (mlehaptics), Gemini (Google), Claude (Anthropic)

---

## Abstract

This document specifies the Universal Time Layer Protocol (UTLP), a transport-agnostic time synchronization architecture enabling distributed determinism on resource-constrained wireless embedded systems. The protocol achieves ±30μs synchronization precision over 90-minute sessions using commodity ESP32-C6 microcontrollers, enabling coordinated behavior across independent nodes without consensus algorithms, persistent storage, or continuous communication.

UTLP treats synchronized time as a *broadcast environmental variable*—a public utility that any device can consume without pairing, encryption, or application-specific logic. This "Glass Wall" architecture strictly separates the time stack (public, unencrypted) from the application stack (private, encrypted), enabling disparate devices to share high-precision timing while maintaining data privacy.

The architecture extends synchronized time beyond clock agreement to provide: stratum-based source selection with opportunistic GPS upgrade, timestamp-based state versioning (implicit LWW-CRDT), holdover mode for graceful degradation during network partitions, power-aware leader election for battery-constrained swarms, and deterministic pattern execution. These primitives form a Distributed Determinism Platform applicable to synchronized wearables, sensor networks, swarm robotics, and coordinated installations.

This work is published as open-source prior art under permissive license, ensuring these techniques remain freely available for public use.

---

## 1. Introduction

### 1.1 The Distributed Coordination Problem

Distributed systems face a fundamental challenge: how do independent nodes agree on shared state without continuous coordination? Traditional solutions—consensus algorithms (Raft, Paxos), vector clocks, persistent sequence numbers—assume reliable networks, persistent storage, and significant computational resources. These assumptions fail in resource-constrained embedded systems operating over lossy wireless links with limited memory and power budgets.

The FLP impossibility result (Fischer, Lynch, Paterson, 1985) demonstrates that deterministic consensus is impossible in asynchronous systems with even a single faulty process. Yet practical applications—from synchronized wearables to industrial sensor networks—require coordinated behavior across distributed nodes.

### 1.2 Time as a Public Utility

UTLP sidesteps the consensus problem entirely by establishing *time agreement first*, then deriving ordering, versioning, and coordination as consequences. The core insight: synchronized time itself serves as a universal reference for any ordering problem. When two devices agree on time to ±30μs precision—three orders of magnitude better than human perception thresholds—wall-clock timestamps provide sufficient ordering granularity for any human-scale interaction.

Unlike traditional synchronization methods that couple timing with application data (requiring pairing, encryption, and specific app logic), UTLP treats time as a *broadcast environmental variable*. Any device can listen for UTLP beacons and synchronize—no handshake, no secrets, no application awareness required. A cheap consumer wearable automatically "latches" onto a high-precision source (GPS-equipped phone, emergency vehicle, municipal infrastructure) passing nearby, temporarily achieving sub-microsecond precision.

### 1.3 The Glass Wall Architecture

UTLP mandates strict separation of concerns within firmware:

**Time Stack (Public/Low-Level):** Listens for any UTLP beacon. Prioritizes sources based on stratum and quality. Maintains monotonic system clock with microsecond precision. *No encryption, no pairing, no application awareness.*

**Application Stack (Private/High-Level):** Contains user data, encryption keys, and business logic. Has *read-only access* to time via `UTLP_GetEpoch()`. Does not need to know how synchronization was achieved.

This "glass wall" enables a medical wearable to synchronize timing with municipal infrastructure while keeping patient data completely isolated. The time stack sees only timestamps; the application stack sees only its encrypted data channel.

### 1.4 Design Principles

- **Transport agnostic:** Core protocol independent of physical layer (BLE, ESP-NOW, WiFi, acoustic)
- **Stratum-based hierarchy:** Automatic source selection with opportunistic precision upgrade
- **Graceful degradation:** Holdover mode maintains timing during source loss
- **Power awareness:** Battery-constrained leader election for swarm scenarios
- **Stateless recovery:** Position reconstructable from synchronized time alone
- **Minimal resources:** Implementable on single-core 160MHz MCU with BLE stack overhead

---

## 2. Related Work

### 2.1 Precision Time Protocol (IEEE 1588)

IEEE 1588 PTP achieves sub-microsecond synchronization in wired networks using hardware timestamping at the MAC layer. The protocol defines Grandmaster/Ordinary/Boundary/Transparent clock roles, Best Master Clock (BMC) algorithm for hierarchy establishment, and Sync/Follow_Up/Delay_Req/Delay_Resp message exchange for offset calculation.

UTLP adapts PTP's stratum concept and two-way delay measurement to connectionless wireless transports, sacrificing sub-microsecond precision for transport flexibility and zero-configuration operation.

### 2.2 Network Time Protocol (NTP)

NTP's stratum hierarchy (0-15) directly inspires UTLP's source selection model. NTP achieves millisecond-scale synchronization over the internet through statistical filtering of multiple server responses. UTLP extends this hierarchy to embedded wireless contexts with finer granularity (stratum 0-255) and explicit holdover/flywheel semantics.

### 2.3 Wireless Sensor Network Synchronization

Reference Broadcast Synchronization (RBS), Timing-sync Protocol for Sensor Networks (TPSN), and Flooding Time Synchronization Protocol (FTSP) address WSN timing. FTSP achieves ±1μs per-hop accuracy using MAC-layer timestamping and clock skew estimation. Swarm-Sync (2018) demonstrates hundreds-of-microseconds accuracy for swarm robotics with minute-scale resynchronization intervals.

UTLP draws from FTSP's flood-based approach but extends beyond clock synchronization to provide versioning and coordination primitives.

### 2.4 CRDTs and Distributed State

Conflict-free Replicated Data Types (Shapiro et al., 2011) achieve eventual consistency without coordination through mathematically convergent merge operations. The Last-Writer-Wins Register uses timestamps for conflict resolution: max(timestamp) wins. UTLP's timestamp-based versioning implements an implicit LWW-Register CRDT where the standard clock skew caveat is invalidated by ±30μs sync precision.

---

## 3. Protocol Architecture

### 3.1 Layered Design

UTLP consists of four layers, each building on the previous:

| Layer | Purpose | Provides |
|-------|---------|----------|
| **Transport** | Physical delivery | `send_beacon()`, `receive_beacon()`, `get_tx/rx_timestamp()` |
| **Time Sync** | Clock agreement | `UTLP_GetEpoch()` → ±30μs synchronized time |
| **State Versioning** | Ordering agreement | `born_at_us` timestamp as atomic version number |
| **Coordination** | Behavior agreement | Pattern playback, zone extraction, epoch derivation |

### 3.2 Transport Abstraction

The transport layer provides a minimal interface for beacon exchange with timing information:

```c
typedef struct {
    esp_err_t (*send_beacon)(const sync_beacon_t* beacon);
    esp_err_t (*receive_beacon)(sync_beacon_t* beacon, uint32_t timeout_ms);
    int64_t (*get_tx_timestamp)(void);
    int64_t (*get_rx_timestamp)(void);
} sync_transport_t;
```

| Transport | RTT Jitter | Sync Precision | Range |
|-----------|------------|----------------|-------|
| BLE 5.0 | ~15ms | ±30μs | ~10m indoor |
| ESP-NOW | ~1-5ms | ±10-50μs | ~200m LOS |
| 802.11 LR | ~5-10ms | ±20μs | ~1km LOS |
| Acoustic (40kHz) | ~0.3ms/10cm | ±100μs + ranging | ~5m indoor |

### 3.3 Stratum-Based Source Selection

UTLP uses a "baton passing" model (inspired by NTP) to determine timing authority. Lower stratum values indicate higher trust and precision:

| Stratum | Class | Description |
|---------|-------|-------------|
| **0** | Primary Reference | Active external lock (GPS, Atomic, Cellular PTP). The "Gold Standard." |
| **1** | Direct Link | Device directly receiving RF packets from Stratum 0. |
| **2-15** | Mesh Hop | Device synced to Stratum (N-1). Each hop adds ~50μs jitter. |
| **255** | Free Running | No external reference. Internal crystal with drift compensation. |

#### 3.3.1 Opportunistic Synchronization

Devices default to **Listener Mode**, continuously scanning for UTLP beacons:

1. Device scans for beacons with UTLP service UUID (0xFEFE).
2. If `Packet.Stratum < Current_Stratum` → Switch immediately.
3. If `Packet.Stratum == Current_Stratum` AND `Packet.Quality > Current_Quality` → Switch.
4. Result: Cheap consumer device automatically "latches" onto high-precision source passing nearby.

This enables a bilateral EMDR device pair (normally Stratum 255, peer-synced) to opportunistically upgrade to Stratum 1 precision when a GPS-equipped smartphone or emergency vehicle broadcasts UTLP beacons nearby.

---

## 4. Time Synchronization Layer

### 4.1 PTP-Inspired Offset Calculation

The synchronization protocol adapts IEEE 1588's two-way delay measurement to connectionless transports. Four timestamps capture a beacon round-trip:

- **T1:** Server transmit timestamp (local clock when beacon sent)
- **T2:** Client receive timestamp (local clock when beacon received)
- **T3:** Client transmit timestamp (response beacon)
- **T4:** Server receive timestamp (response received)

Clock offset and one-way delay derive from:

```
offset = ((T2 - T1) - (T4 - T3)) / 2
delay  = ((T2 - T1) + (T4 - T3)) / 2
```

### 4.2 Drift Rate Estimation

Crystal oscillator drift (typically ±20-50ppm for ESP32) accumulates over time. UTLP beacons include a `drift_rate` field (parts per billion) enabling receivers to predict clock behavior between sync events. Linear regression over recent offset samples estimates drift, allowing interpolation during beacon gaps.

### 4.3 Holdover Mode (The Flywheel Effect)

When a device loses connection to its time source (e.g., GPS-equipped phone moves out of range), it enters **Holdover Mode** rather than resetting:

1. Clock continues incrementing using internal crystal.
2. Last known `drift_rate` correction is applied.
3. Advertised stratum degrades (e.g., Stratum 2 → Stratum 3, or → Stratum 255).
4. Device continues broadcasting degraded-stratum beacons for downstream nodes.

This "flywheel" behavior ensures graceful degradation rather than abrupt timing discontinuities. A bilateral device pair losing external sync smoothly transitions to peer-only synchronization while maintaining relative timing accuracy.

---

## 5. Timestamp-Based State Versioning

### 5.1 The Core Innovation

Traditional distributed systems use persistent sequence numbers or vector clocks for version ordering. UTLP eliminates persistence requirements by using the synchronized timestamp at state creation as the version identifier. Since both devices agree on time (±30μs), a timestamp uniquely and globally orders all state changes.

When any device initiates a state change, it captures the current synchronized time. This timestamp *becomes* the version number. Conflict resolution is trivial: higher timestamp wins. No NVS writes, no coordination protocol, no central authority for version assignment.

### 5.2 Beacon Payload Structure

```c
struct UTLP_Payload {
    uint8_t  magic[2];       // 0xFE, 0xFE (Protocol Identifier)
    uint8_t  stratum;        // 0 = GPS, 255 = Free Run
    uint8_t  quality;        // 0-100 (Battery/Oscillator confidence)
    uint8_t  hops;           // Distance from Master (loop prevention)
    uint64_t epoch_us;       // Microseconds since epoch
    int32_t  drift_rate;     // Estimated drift in ppb
};
```

### 5.3 CRDT Equivalence

This versioning scheme implements a State-based CRDT with Last-Writer-Wins semantics:

- **Replica:** Each UTLP-enabled device
- **State:** Beacon payload (epoch_us, stratum, quality)
- **Timestamp:** epoch_us (from synchronized clock)
- **Merge function:** Lower stratum wins; if equal, higher quality wins; if equal, max(epoch_us) wins
- **Tiebreaker:** SERVER role wins if timestamps within ±100μs

---

## 6. Power-Aware Leader Election

### 6.1 The Swarm Rule

In battery-constrained scenarios without external time sources (e.g., bilateral EMDR devices indoors), UTLP implements power-aware leader election using the `quality` field:

1. Nodes encode battery level (0-100) in the quality field.
2. Current time master broadcasts `quality = battery_level`.
3. If master's battery drops below threshold (e.g., 20%), it sets `quality = 0`.
4. Swarm automatically re-elects neighbor with highest quality as new time anchor.

This ensures the device with most remaining power serves as time master, extending overall swarm operating time. Handoffs are seamless—followers simply begin tracking the new highest-quality source.

### 6.2 Zone and Role Separation

Drawing from Texas Instruments' software-defined vehicle architecture, UTLP separates two orthogonal concepts:

- **Zone (physical):** Which outputs to drive. Values: LEFT, RIGHT. Immutable, hardware-determined.
- **Role (logical):** Who provides timing reference. Values: SERVER, CLIENT. Mutable, runtime-negotiated via quality field.

This separation enables identical firmware on both devices. A LEFT-zone device can be either SERVER or CLIENT depending on battery state and network topology.

---

## 7. Coordination Layer

### 7.1 The Sheet Music Paradigm

The coordination model draws from emergency vehicle lighting systems (Feniex, Whelen): synchronized modules don't negotiate timing per-output. Instead, all modules receive the same pattern definition and execute independently from their local copy. Each module knows its position (zone) and extracts its portion from the shared "sheet music."

This eliminates reactive timing calculation—the source of cascading bugs in earlier architectures. Both devices load identical pattern definitions; each reads only its assigned zone and executes locally. No per-cycle coordination needed during playback.

### 7.2 Epoch Derivation

Pattern playback epoch (when cycle 0 begins) derives mathematically from the state's birth timestamp:

```c
epoch_us = ((born_at_us / cycle_us) + 1) * cycle_us
```

Both devices independently calculate the same epoch from the shared `born_at_us` timestamp—no additional coordination required.

---

## 8. Security Considerations

### 8.1 The Shared Hallucination Model

UTLP is intentionally unencrypted, creating what might be called a "shared hallucination." Security analysis:

- **Spoofing:** A bad actor CAN broadcast fake time (e.g., "The year is 2050").
- **Impact:** All listening devices will agree it is 2050.
- **Safety:** Since patterns rely on RELATIVE timing (intervals), absolute time error is irrelevant to physical safety.

### 8.2 Common Mode Rejection

The key security insight: if time is spoofed, it is spoofed *identically for all local nodes*, preserving relative synchronization. A bilateral EMDR device pair maintains perfect antiphase regardless of whether the absolute epoch is correct. The "Left" and "Right" units remain synchronized to each other—which is what matters for therapeutic efficacy.

This is fundamentally different from attacks on application data, where spoofing one device while not another creates inconsistency. UTLP's broadcast nature ensures consistent spoofing—a property that, counterintuitively, provides safety through uniformity.

### 8.3 Application-Layer Isolation

The Glass Wall architecture ensures that time spoofing cannot compromise application data:

- Time stack has no access to encryption keys, user data, or business logic.
- Application stack cannot be reached through time beacons.
- Worst case: device has wrong absolute time, but all data remains confidential and correctly encrypted.

---

## 9. Implementation Notes

### 9.1 ESP32-C6 Reference Implementation

The reference implementation targets ESP32-C6—a single-core RISC-V processor at 160MHz. The NimBLE stack creates high-priority tasks (19-23) sharing the single core with application code. Timing-critical operations use GPTimer ISR callbacks rather than FreeRTOS software timers.

**Critical Kconfig:** `CONFIG_GPTIMER_ISR_HANDLER_IN_IRAM=y`, `CONFIG_GPTIMER_ISR_CACHE_SAFE=y` (prevents 10-100μs latency spikes during flash operations).

### 9.2 BLE Service UUID

**Proposed Service UUID:** 0xFEFE (pending formal registration). Manufacturing data payload uses this UUID for beacon identification across vendors.

---

## 10. Applications

### 10.1 Reference Application: Bilateral EMDR

The protocol was developed for synchronized bilateral haptic stimulation in EMDR therapy—two handheld devices producing alternating vibration/LED patterns. Requirements: antiphase maintained within ±10ms over 20-minute sessions, autonomous operation during brief disconnections, perceptually smooth output.

### 10.2 Extended Applications

- **Municipal infrastructure:** Traffic signals, emergency vehicle preemption, coordinated lighting
- **Medical wearables:** Multi-sensor body networks requiring coordinated sampling
- **Industrial IoT:** Timestamped sensor fusion from distributed arrays
- **Swarm robotics:** Coordination timing layer for multi-agent systems
- **Art installations:** Synchronized lighting/sound across distributed nodes

---

## 11. Intellectual Property Statement

This work is published as **open-source prior art** under permissive license. The authors explicitly disclaim any patent rights and publish these techniques to establish prior art, ensuring they remain available for public use.

**Key techniques documented as prior art:**

1. Time as public utility / broadcast environmental variable architecture
2. Glass Wall separation of time stack (public) from application stack (private)
3. Stratum-based opportunistic synchronization with GPS upgrade path
4. Holdover/flywheel mode for graceful degradation during source loss
5. Power-aware leader election via quality field (Swarm Rule)
6. Timestamp-based distributed state versioning (implicit LWW-CRDT)
7. Common Mode Rejection security model for broadcast time
8. Transport-agnostic sync abstraction (BLE, ESP-NOW, 802.11 LR, acoustic)
9. Sheet music pattern execution with zone extraction
10. Zone/Role architectural separation for identical firmware deployment

**First published:** December 2025

**Repository:** github.com/mlehaptics (MIT License)

---

## 12. Conclusion

The Universal Time Layer Protocol demonstrates that distributed determinism is achievable on resource-constrained embedded systems without consensus algorithms, persistent storage, or continuous coordination. The key insight: when time synchronization is precise enough (±30μs), it collapses the distributed systems problem—ordering, versioning, and coordination derive as consequences of time agreement.

By treating time as a public utility—a broadcast environmental variable available to any device without pairing or authentication—UTLP enables a new class of applications where timing precision is shared freely while application data remains private. The Glass Wall architecture ensures this openness does not compromise security.

The resulting Distributed Determinism Platform provides reusable primitives for any application requiring coordinated behavior across independent wireless nodes. By publishing this work as open-source prior art, we ensure these techniques remain freely available for innovation—technology that assumes cooperation rather than extraction.

---

## References

[1] IEEE 1588-2019. "Precision Clock Synchronization Protocol for Networked Measurement and Control Systems." IEEE Standards Association.

[2] D. Mills et al. RFC 5905. "Network Time Protocol Version 4: Protocol and Algorithms Specification." IETF, 2010.

[3] M. Shapiro, N. Preguiça, C. Baquero, M. Zawirski. "Conflict-free Replicated Data Types." SSS 2011.

[4] M. Maróti, B. Kusy, G. Simon, Á. Lédeczi. "The Flooding Time Synchronization Protocol." SenSys 2004.

[5] M. Fischer, N. Lynch, M. Paterson. "Impossibility of Distributed Consensus with One Faulty Process." JACM 1985.

[6] M.V. Shenoy. "Swarm-Sync: A distributed global time synchronization framework for swarm robotic systems." Pervasive and Mobile Computing 2018.

[7] C. Medina, J.C. Segura, A. de la Torre. "Accurate time synchronization of ultrasonic TOF measurements in IEEE 802.15.4 based wireless sensor networks." Ad Hoc Networks 2013.

[8] Espressif Systems. "ESP-IDF Programming Guide: Wi-Fi Driver." docs.espressif.com, 2025.

[9] J. Li et al. "Application-Layer Time Synchronization and Data Alignment Method for Multichannel Biosignal Sensors Using BLE Protocol." Sensors 2023.

---

## Acknowledgments

This specification emerged from collaborative development across multiple AI systems and human expertise:

- **Steve (mlehaptics):** Architecture design, EMDR domain expertise, hardware implementation, "Time as Public Utility" philosophy, Glass Wall architecture, Stratum hierarchy, Flywheel/Holdover mode, Swarm Rule battery-aware election, Common Mode Rejection security model, UTLP packet structure.

- **Gemini (Google):** CRDT analysis and LWW-Register mapping, recognition of timestamp-as-version pattern, distributed systems theoretical framing, platform abstraction insights.

- **Claude (Anthropic):** Technical report compilation, academic literature survey (PTP, FTSP, BLE sync, swarm robotics), transport comparison analysis, prior art documentation, defensive publication framing.

---

*— End of Document —*
