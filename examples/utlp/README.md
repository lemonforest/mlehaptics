# UTLP v2 - Biological Governance for Distributed Time

**Universal Time Lord Protocol** - ESP32-focused implementation demonstrating
connectionless distributed time synchronization using **biological governance**
instead of political consensus.

> *"Time is born of one."* — UTLP Specification, Section 7
>
> *"Trust is not declared. It is accumulated."* — Technical Supplement S2

## The Radical Idea

Traditional distributed systems borrow from human politics:
- **Raft/Paxos**: Nodes vote to elect leaders
- **BFT**: Majority quorum decides truth
- **NTP**: Hierarchical strata assign authority

UTLP asks: **What if we governed like cells, not congresses?**

Your body coordinates 37 trillion cells without elections. It uses:
- **Hebbian Learning**: Neurons that fire together, wire together
- **Immune Checkpoints**: T-cell exhaustion prevents autoimmune attacks
- **Quorum Sensing**: Bacteria wait for critical mass before acting
- **Median Consensus**: Single liars cannot corrupt population health

This implementation translates those principles into working embedded C.

## Learning Path

If you're new to this codebase, read in this order:

| Order | File | What You'll Learn |
|-------|------|-------------------|
| 1 | `utlp.c` (header comments) | The manifesto - why biology beats politics |
| 2 | `utlp_trust.h` | Hebbian learning, median consensus, Dunbar's Number |
| 3 | `utlp_immune.h` | T-cell exhaustion, quorum sensing, cytokine storms |
| 4 | `utlp_hal.h` | Time-indexed execution, dual clock architecture |
| 5 | `sim/SIMULATION_RESULTS.md` | What happens when Byzantine actors attack |

Each file includes academic references and biological analogies.

## Overview

This is the production ESP32 implementation of UTLP v2, featuring the full
Frontier Algorithm for topology-aware Genesis election and Biological Governance
for Byzantine-resistant trust. Forked from `utlp_skeleton` for focused ESP32
development without cross-platform constraints.

**For cross-platform/educational use:** See `examples/utlp_skeleton/` which
maintains C64/8-bit compatibility.

## Key Features (Frontier Algorithm)

- **Score-based election:** Higher genesis_score wins (not lower MAC)
- **Layered Provider Model:** Genesis → Providers → Consumers
- **Smart Interval:** Promotion Pulse + Echo Rule for relays
- **Multi-hop support:** Providers extend range to edge nodes
- **Native 64-bit:** Full uint64_t support, no workarounds

## Quick Start

```bash
# Build and flash for XIAO ESP32-C6 (default)
pio run -e utlp_xiao_esp32c6 -t upload

# Build and flash for ESP32 DevKit v1
pio run -e utlp_esp32_devkit -t upload

# Monitor serial output
pio device monitor
```

**Important:** Reset both devices simultaneously for best results.
See [Known Limitations](#known-limitations) below.

## Board Configuration

The HAL supports multiple ESP32 boards via build flags:

| Board | Environment | GPIO | Polarity | Build Flags |
|-------|-------------|------|----------|-------------|
| XIAO ESP32-C6 | `utlp_xiao_esp32c6` | 15 | Active LOW | *(defaults)* |
| ESP32 DevKit v1 | `utlp_esp32_devkit` | 2 | Active HIGH | `-DACTUATOR_GPIO=2 -DACTUATOR_ACTIVE_LOW=0` |

For custom boards, add to `platformio.ini`:
```ini
[env:my_board]
platform = espressif32
board = my_board_id
framework = espidf
build_flags =
    -DACTUATOR_GPIO=13           ; Your LED GPIO
    -DACTUATOR_ACTIVE_LOW=0      ; 1=active LOW, 0=active HIGH
```

## The Genesis Principle

Every node boots as a **Genesis Node** — it declares itself the source of time
(stratum 1) and starts operating immediately. No waiting for peers. No election.
No handshake.

```
Boot → I AM the Atomic Clock (stratum 1) → LED blinks immediately
         ↓
    Beacon received from better stratum?
         ↓
    YES → Adopt their time, become Follower (stratum 2)
         ↓
    Same stratum? → Higher genesis_score wins (topology-aware)
         ↓
    Same score? → Lower MAC wins (tie-breaker)
```

**Why this matters:**
- Single device works standalone (no peer required)
- Late-joining nodes adopt from existing swarm
- Simple, robust, zero negotiation
- Better-positioned nodes win (not just oldest)

## Frontier Algorithm (Score-Based Election)

The original UTLP used MAC address as the tie-breaker. This is **topology-blind**:
an old device with a low MAC might be poorly positioned (behind walls, at the edge).

**Frontier Algorithm v2** uses a **genesis_score** (0-255) based on:

| Component | Points | What It Measures |
|-----------|--------|------------------|
| Neighbor count | 0-100 | Central position (more peers = better relay) |
| Average RSSI | 0-100 | Signal strength (louder = better coverage) |
| Drift stability | 0-55 | Clock quality (lower drift = better source) |

**Election Logic:**
1. Lower stratum always wins
2. Same stratum: **higher score** wins (topology-aware)
3. Same score: lower MAC wins (deterministic tie-breaker)

## Layered Provider Model

Not all nodes relay time. This saves bandwidth and prevents drift amplification.

```
Genesis (S1) ─────── Always chirps (source of truth) ──────────────────
                              │
                              ▼
         ┌─────────────────────────────────────────────┐
         │  HIGH-SCORE S2 = "Providers"                │
         │  - At network edge (weak master signal)     │ → ALSO chirp
         │  - Above RELAY_THRESHOLD (score > 128)      │   (extend range)
         └─────────────────────────────────────────────┘
                              │
                              ▼
         ┌─────────────────────────────────────────────┐
         │  LOW-SCORE S2 = "Consumers"                 │
         │  - Strong master signal (interior node)     │ → SILENT
         │  - Below RELAY_THRESHOLD (score ≤ 128)      │   (just sync)
         └─────────────────────────────────────────────┘
```

**Frontier Detection:** A node at the edge (weak master RSSI < -70 dBm) with
high score becomes a Provider to extend coverage to devices that can't hear Genesis.

## Smart Interval (Echo Rule)

**Problem:** A relay cannot chirp faster than it gets corrected. If Genesis
chirps every 60s, a Provider chirping every 10s would amplify drift errors.

**Solution:** Providers use smart interval logic:

| Role | Interval | Logic |
|------|----------|-------|
| Genesis | Genesis Pulse | 100ms→500ms→1s→10s→60s over time |
| New Provider | Promotion Pulse | 1s for 10 seconds (announce presence) |
| Steady Provider | Echo Rule | 60s + MAC-based jitter (match master) |

**Jitter:** Each Provider offsets by `MAC[5] × 100ms` (0-25.5s) to prevent
collision when multiple Providers transmit near the same 60s boundary.

## Genesis Pulse (Dynamic Beacon Interval)

Like a star beginning fusion, time broadcasts are rapid at genesis
then settle to steady-state:

| Time Since Boot | Beacon Interval | Purpose |
|-----------------|-----------------|---------|
| 0-1s | 100ms | Genesis burst (10/sec) |
| 1-5s | 500ms | Fast convergence |
| 5-10s | 1s | Settling |
| 10-60s | 10s | Stabilizing |
| 60s+ | 60s | Steady state |

**Benefits:**
1. New swarm converges quickly
2. Hospitable environment for late-joining nodes
3. Low steady-state overhead

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Application Layer (utlp.c)                 │
│                                                              │
│    Boot as Genesis (stratum 1) → Blink LED immediately      │
│    Listen for beacons → Adopt better stratum if found       │
│    Time-indexed physics: LED state = f(atomic_time)         │
│                                                              │
│    get_atomic_time() = local_time + offset                  │
├─────────────────────────────────────────────────────────────┤
│             Hardware Abstraction Layer (utlp_hal.h)         │
│                                                              │
│    Time:     get_micros(), set_time_offset()                │
│    Radio:    tx_packet(), rx_wait(), rx_poll()              │
│    Actuator: set_actuator_phase() [GPIO LED]                │
├─────────────────────────────────────────────────────────────┤
│           ESP32 Implementation (utlp_hal_esp32.c)           │
│                                                              │
│   ┌─────────┬─────────┬─────────┬─────────┐                 │
│   │ ESP-NOW │  MCPWM  │ Timer   │Semaphore│                 │
│   │ (radio) │  (LED)  │ (time)  │  (RX)   │                 │
│   └─────────┴─────────┴─────────┴─────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

## Seismic Chirp (3-Burst Beacon Pattern)

Every beacon transmission is a **seismic chirp**: 3 packets spaced 2ms apart,
all carrying the **same timestamp** (the "chirp epoch"). The 2ms spacing is
the **known reference signal** — like a seismic sweep with known frequency.

**The Principle:**
- Sender captures timestamp once, transmits it in all 3 bursts
- Bursts arrive at receiver 0ms, 2ms, 4ms after first (expected)
- Any deviation from 2ms spacing = receiver clock drift

**The Derivative Stack:**

| Burst | RX Time | Measures | Mathematical Role |
|-------|---------|----------|-------------------|
| Burst 0 | rx₀ | Offset | 0th derivative (where) |
| Burst 1 | rx₁ = rx₀ + 2ms ± drift | Drift | 1st derivative (rate) |
| Burst 2 | rx₂ = rx₀ + 4ms ± drift | Stability | 2nd derivative (acceleration) |

**Why same timestamp?** The chirp is a known signal (2ms spacing). Fresh
timestamps would mix sender and receiver drift — same timestamp isolates
receiver drift against the known reference.

See: `UTLP_Technical_Supplement_S1.md` Section 1.4

## Beacon Protocol (v2)

11-byte seismic chirp burst (one-way, no reply needed):

```
┌───────────┬─────────────────────────────────────────────┐
│ Byte 0    │ Stratum (1 = Genesis, 2 = Follower, etc.)   │
├───────────┼─────────────────────────────────────────────┤
│ Byte 1    │ Burst index (0, 1, or 2)                    │
├───────────┼─────────────────────────────────────────────┤
│ Byte 2    │ Genesis score (0-255, higher = better)      │
├───────────┼─────────────────────────────────────────────┤
│ Bytes 3-10│ Chirp epoch (SAME timestamp in all 3 bursts)│
└───────────┴─────────────────────────────────────────────┘
```

**Critical:** All 3 bursts carry the **same** timestamp (captured once at chirp start).
The 2ms burst spacing is the **known reference**. Receiver compares expected vs.
observed spacing to detect clock drift.

## Time-Indexed LED Control

The LED state is **calculated** from atomic time, not **toggled** by delays:

```c
uint64_t cycle_pos = atomic_time % BLINK_PERIOD_US;  // 1 second
bool led_on = (cycle_pos < BLINK_PERIOD_US / 2);     // 50% duty
```

**Why this is drift-proof:** Every node with the same atomic_time
will calculate the same LED state. No drift accumulation.

## Expected Serial Output

```
I (552) UTLP: ========================================
I (562) UTLP: UTLP GENESIS NODE v2 - Frontier Algorithm
I (562) UTLP: "Time is born of one."
I (572) UTLP: ========================================
I (572) UTLP: MAC: 10:51:DB:1C:B3:08
I (582) UTLP: Stratum: 1 (GENESIS)
I (582) UTLP: Beacon: 11-byte Seismic Chirp (3-burst @ 2ms)
I (592) UTLP: Election: Score-based (higher score wins)
I (592) UTLP: Relay: Frontier detection (edge nodes = Providers)
I (602) UTLP: Interval: Genesis Pulse / Promotion Pulse / Echo Rule
I (602) UTLP: Blink period: 1000 ms
I (612) UTLP: Drift Analysis: Enabled (polynomial fit)
I (612) UTLP: ========================================
I (XXX) UTLP: Beacon interval: 100 ms (uptime 0s, role=Genesis)
I (XXX) UTLP: [LED] ON  @ phase=500000 us (stratum 1)
I (XXX) UTLP: [LED] OFF @ phase=0 us (stratum 1)
I (XXX) UTLP: Beacon interval: 500 ms (uptime 1s, role=Genesis)
...
I (XXX) UTLP: Same stratum, higher score wins (180 > 120)
I (XXX) UTLP: SYNCED: stratum=2, offset=+1234 us
I (XXX) UTLP: Stratum changed: 1 -> 2 (provider=YES)
I (XXX) UTLP: Beacon interval: 1000 ms (uptime 5s, role=Provider)
...
I (XXX) UTLP: Beacon interval: 60000 ms (uptime 15s, role=Provider)
```

## Known Limitations

### No Automatic Failover (Matrix-Style Takeover)

This implementation does **not** implement automatic leader re-election when the
Genesis node goes offline. If you reset the Genesis node while a Follower
is still running:

- Follower continues using stale offset
- LEDs will drift out of sync
- **Solution:** Reset both devices together

Future work may add timeout-based re-election where Followers detect
Genesis absence and promote themselves.

## Biological Governance Modules

### The Metabolic Ledger (`utlp_trust.h/c`)

The trust module implements **Hebbian learning** for distributed systems:

```
Peers agreeing with consensus → health increases (+2)
Peers drifting (2-100ms off) → health decreases (-10)
Peers lying (>100ms off)     → health decreases (-50)
```

**Key Algorithms:**
- **Median Consensus**: Byzantine-resistant - single liar can't corrupt result
- **Asymmetric Cost**: 25:1 penalty ratio (one predator > 25 peaceful encounters)
- **Silicon Dunbar's Number**: Only 12 peer slots (forces prioritization)
- **Health-Weighted Eviction**: "Don't kill a healthy friend for a stranger"

### Immune Checkpoint System (`utlp_immune.h/c`)

The immune module prevents **cytokine storms** (RF pollution):

```
Token Bucket: 5 entrainment pulses max before exhaustion
Anergy State: Forced silence when depleted (T-cell exhaustion)
Hysteresis:   Need 3 tokens to exit anergy (prevents oscillation)
```

**Dual Constraint System:**
1. **Internal Check**: Do I have tokens? (prevents RF spam)
2. **External Check**: Do 2+ peers agree with me? (prevents "Crazy Old Man")

Both must pass before firing entrainment. This mimics real immune checkpoints
(PD-1, CTLA-4) that prevent autoimmune attacks.

### The Loom: Generalized Homeostatic Mechanism (S2.31)

The Loom is the emergent state machine that weaves entity structure from entropy
signals. It is not programmed with specific responses—it observes threats and
weaves homeostatic states across **any dimension of entity health**.

```
+-------------------+------------------------+-------------------+
|  Threat Domain    |    Entropy Signal      |  Emergent State   |
+-------------------+------------------------+-------------------+
|  Temporal         | Clock drift/instability| Time Lord (Anchor)|
|  Spectral         | RF congestion/jamming  | Channel divergence|
|  Spatial          | Position uncertainty   | RFIP coordinates  |
|  Thermal          | Power budget stress    | Sleep states      |
|  Social           | Trust distribution     | Affinity groups   |
+-------------------+------------------------+-------------------+
```

**The Pattern:**
1. **Detect** threat (entropy signal exceeds threshold)
2. **Weave** response (transition to emergent state)
3. **Maintain** organism (homeostasis restored)

Clock entropy produces Time Lords. Spectral congestion produces channel chirality.
The Loom is the unifying mechanism—what changes is the threat domain and the
emergent state, not the pattern of detection and response.

> *"The Loom weaves authority from entropy. It does not assign roles—
> it observes stability and lets structure emerge."*

**Implementation Status:** Temporal Loom complete (trust module); Spectral Loom
stubbed (chirality functions); Spatial/Thermal/Social Looms are future work.

### Simulation (`sim/genesis_reset_antiphase.py`)

Python simulation for testing Byzantine scenarios:
- Rogue Genesis attacks (ancient epoch claims)
- Web of Time merge (two swarms meeting)
- Derivative-based detection (jitter variance analysis)

## Files

| File | Description |
|------|-------------|
| `utlp.c` | Main protocol with Biological Governance |
| `utlp_trust.h/c` | Metabolic Ledger (Hebbian trust, median consensus) |
| `utlp_immune.h/c` | Immune Checkpoint (token bucket, anergy) |
| `utlp_hal.h` | HAL interface contract (time, radio, actuator) |
| `utlp_hal_esp32.c` | ESP32 HAL implementation (ESP-NOW, MCPWM) |
| `utlp_rfip.h` | Reference Frame Independent Positioning (stub) |
| `utlp_main_esp32.c` | Platform entry point (`app_main()`) |
| `sim/genesis_reset_antiphase.py` | Python simulation for Byzantine testing |
| `sim/SIMULATION_RESULTS.md` | Detailed simulation analysis |

### Architecture Note

`utlp.c` contains **0% platform-specific code**. All ESP-IDF dependencies
are isolated in the HAL files. The application code uses native 64-bit types
and C99 features without cross-platform constraints.

## HAL API Reference

### Time Functions

```c
uint64_t utlp_hal_get_micros(void);           // Raw local time
uint64_t utlp_hal_get_atomic_time_us(void);   // Synchronized time
void utlp_hal_set_time_offset(int64_t offset_us);
```

### Radio Functions

```c
void utlp_hal_get_mac(uint8_t *mac);
bool utlp_hal_tx_packet(const uint8_t *peer_mac, const uint8_t *data, size_t len);
bool utlp_hal_rx_wait(utlp_packet_t *out, uint32_t timeout_ms);  // Blocking
bool utlp_hal_rx_poll(utlp_packet_t *out);                       // Non-blocking
```

### Actuator Functions

```c
// LED actuator (polarity handled by HAL - just specify duty%)
void utlp_hal_set_actuator_phase(int channel, uint32_t freq_hz,
                                  float phase_deg, float duty_pct);
void utlp_hal_actuator_stop(int channel);
```

**Note:** The HAL abstracts LED polarity. Application code just uses duty percentage
(100% = ON, 0% = OFF) regardless of whether the LED is active HIGH or LOW.

### Logging Functions

```c
// Platform-agnostic logging (maps to ESP_LOGI)
void utlp_hal_log_info(const char *tag, const char *format, ...);
void utlp_hal_log_error(const char *tag, const char *format, ...);
void utlp_hal_log_warn(const char *tag, const char *format, ...);
```

### Application Entry

```c
// Called from platform-specific main (app_main)
void utlp_app_run(void);
```

## Related Documentation

- `docs/UTLP_Specification.md` - Full protocol specification
- `docs/Connectionless_Distributed_Timing_Prior_Art.md` - Research foundation
- `examples/utlp_skeleton/` - Cross-platform reference implementation

## Future Work

- **Automatic failover:** Timeout-based re-election when Genesis goes offline
- **GPS stratum-0:** External time reference integration
- **Drift compensation:** Use tracked drift rate for active clock correction
- **Panic Response:** Stratum 255 "Help!" signal for rescue chirps
- **Channel chirality:** Dynamic channel divergence under congestion pressure

## Channel Chirality (S2.31)

**The Spectral Loom — Why Channel 6 is the Golden Path**

Channel chirality is the **Spectral Loom's** response to RF congestion. Just as
the Temporal Loom weaves Time Lords from clock entropy, the Spectral Loom weaves
channel divergence from congestion signals.

UTLP uses WiFi channel 6 as the deterministic rendezvous point for all swarms.
This is not configuration but **mathematical necessity**: channel 6 is the only
non-overlapping channel equidistant from both divergence options.

```
WiFi Non-Overlapping Channels:
     [1]-------[6]-------[11]
      ↑         ↑         ↑
   Sinistral  Golden   Sinistral
   (left)     Path     (right)
```

### The Biological Analogy: Snail Chirality

In snail populations, most individuals are **dextral** (right-coiling). However,
a minority are **sinistral** (left-coiling). This matters for survival:

- Predatory snakes evolved jaws optimized for the dextral majority
- Sinistral snails are "incompatible" with snake jaw mechanics
- The "wrong" spiral becomes the survival advantage under predation

UTLP applies this principle to WiFi channels:

| Biological | WiFi | Role |
|-----------|------|------|
| Dextral majority | Channel 6 | Where strangers meet, swarms coalesce |
| Sinistral left | Channel 1 | Divergence under congestion pressure |
| Sinistral right | Channel 11 | Divergence under congestion pressure |
| Predation pressure | WiFi congestion | Forces divergence to survive |

### Why Not Channel 1 or 11?

- **Channel 1**: Not equidistant — can only diverge right (to 6, then 11)
- **Channel 11**: Not equidistant — can only diverge left (to 6, then 1)
- **Channel 6**: Equidistant — can diverge left OR right symmetrically

This symmetry is crucial for deterministic behavior. If a node on channel 6
needs to escape congestion, it can choose left or right based on a simple
deterministic function (e.g., `MAC % 2`). A node starting on channel 1 would
be biased toward right-only divergence.

### Bridge Nodes: Hybrid Zones

Nodes that maintain presence on channel 6 serve as **bridge nodes**:
- They hear both channel-1 and channel-11 populations
- They propagate timing coherence ("gene flow") between populations
- Divergent populations sync **through the golden path**, not directly

This prevents complete speciation while allowing channel-local optimization.
The bridge role emerges naturally from topology — nodes that happen to hear
multiple populations become bridges without explicit assignment.

### Implementation Status: Stub

Channel chirality is currently stubbed. The HAL defines the channel constants:

```c
#define WIFI_CHANNEL_SINISTRAL_LEFT   1   // Left-coiling divergence
#define WIFI_CHANNEL_GOLDEN_PATH      6   // Dextral majority (default)
#define WIFI_CHANNEL_SINISTRAL_RIGHT  11  // Right-coiling divergence
```

Future work will add:
- `utlp_chirality_detect_congestion()` — Measure channel saturation
- `utlp_chirality_select_divergent_channel()` — Deterministic left/right choice
- `utlp_chirality_is_bridge_node()` — Detect multi-population hearing

**Prior Art:** Claims 78-80 in Technical Supplement S2.31

## Academic Cross-References

The biological governance model draws from multiple domains:

### Neuroscience
- **Hebbian Learning** (Hebb, 1949): "The Organization of Behavior"
  - Trust accumulation mimics Long-Term Potentiation (LTP)
  - Temporal correlation drives synaptic strength

### Immunology
- **T-Cell Exhaustion** (Wherry, 2011): Nature Immunology 12(6):492-499
  - Token depletion → anergy (PD-1 pathway analog)
  - Hysteresis recovery mimics CD28 re-engagement
- **Quorum Sensing** (Waters & Bassler, 2005): Annual Review of Cell Biology
  - Autoinducer threshold → collective action

### Decision Theory
- **Prospect Theory** (Kahneman & Tversky, 1979): Econometrica
  - Asymmetric loss functions (25:1 penalty ratio)
  - Losses loom larger than gains

### Distributed Systems
- **Byzantine Generals** (Lamport et al., 1982): ACM TOPLAS
  - Median consensus for fault tolerance
- **Token Bucket** (Turner, 1986): IEEE Communications
  - Rate limiting for traffic shaping

### Anthropology
- **Dunbar's Number** (Dunbar, 1992): Journal of Human Evolution
  - Cognitive limit on social group size
  - Our "Silicon Dunbar" = 12 peer slots

### Evolutionary Biology
- **Snail Chirality** (Hoso et al., 2010): Nature Communications
  - Frequency-dependent selection in sinistral vs dextral populations
  - "Wrong" chirality survives specialized predators (snake jaw asymmetry)
  - Applied to WiFi channel divergence under congestion pressure

## License

This example is part of the EMDR Bilateral Stimulation Device project.
- Software: GPL v3
- Hardware: CERN-OHL-S v2

---

*"What if coordination emerged from physics, not negotiation?"*
