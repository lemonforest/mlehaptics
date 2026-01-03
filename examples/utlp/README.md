# UTLP v3 - Biological Governance for Distributed Time

**Universal Time Lord Protocol** - Multi-transport implementation demonstrating
connectionless distributed time synchronization using **biological governance**
instead of political consensus.

> **v3 Features:** Multi-Arbor Transport Architecture (ESP-NOW + 802.15.4),
> Servo-Locked Phase Correction (S2 Claim 55), Genesis Reset Detection,
> SMSP Application Layer, Centralized Configuration (SSOT),
> **Phase 9: The Loom** (Emergent Time Lord, Per-Arbor Genesis Pulse),
> **HPLAC: Hardware Phase Locked Atomic Coherency** (MCPWM-based phase engine).

> **Transport Support:** ESP-NOW (WiFi broadcast) + IEEE 802.15.4 (raw MAC frames).
> Staggered startup enables testing pure 802.15.4 sync before WiFi joins.

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
| 1 | `utlp_config.h` | All tunable parameters (SSOT - Single Source of Truth) |
| 2 | `utlp.c` (header comments) | The manifesto - why biology beats politics |
| 3 | `utlp_trust.h` | Hebbian learning, median consensus, Dunbar's Number |
| 4 | `utlp_immune.h` | T-cell exhaustion, quorum sensing, cytokine storms |
| 5 | `utlp_loom.h` | Emergent Time Lord authority (Phase 9) |
| 6 | `utlp_phase.h` | **NEW:** Hardware Phase Engine (MCPWM atomic coherency) |
| 7 | `utlp_transport.h` | Multi-arbor architecture (ESP-NOW + 802.15.4) |
| 8 | `utlp_smsp.h` | Score-driven actuation (Protocol Trinity: when/where/what) |
| 9 | `utlp_hal.h` | Time-indexed execution, dual clock architecture |
| 10 | `sim/SIMULATION_RESULTS.md` | What happens when Byzantine actors attack |

Each file includes academic references and biological analogies.

## Overview

This is the production ESP32 implementation of UTLP v3, featuring the full
Frontier Algorithm for topology-aware Genesis election, Biological Governance
for Byzantine-resistant trust, and the Protocol Trinity (UTLP/RFIP/SMSP).
Forked from `utlp_skeleton` for focused ESP32 development without cross-platform
constraints.

**For cross-platform/educational use:** See `examples/utlp_skeleton/` which
maintains C64/8-bit compatibility.

## Key Features

### Frontier Algorithm (v2)
- **Score-based election:** Higher genesis_score wins (not lower MAC)
- **Layered Provider Model:** Genesis → Providers → Consumers
- **Smart Interval:** Promotion Pulse + Echo Rule for relays
- **Multi-hop support:** Providers extend range to edge nodes
- **Native 64-bit:** Full uint64_t support, no workarounds

### Biological Governance (v3)
- **Servo-Locked Phase Correction:** Frequency slewing, not instant jumps (S2 Claim 55)
- **Genesis Reset Detection:** Blocks adoption of reset peer's stale epoch
- **SMSP Application Layer:** Score-driven actuation (Protocol Trinity)
- **Centralized Config:** All constants in `utlp_config.h` (SSOT)

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

The HAL supports multiple boards via build flags:

### ESP32 Boards

| Board | Environment | GPIO | Polarity | Build Flags |
|-------|-------------|------|----------|-------------|
| XIAO ESP32-C6 | `utlp_xiao_esp32c6` | 15 | Active LOW | *(defaults)* |
| ESP32 DevKit v1 | `utlp_esp32_devkit` | 2 | Active HIGH | `-DACTUATOR_GPIO=2 -DACTUATOR_ACTIVE_LOW=0` |

For custom ESP32 boards, add to `platformio.ini`:
```ini
[env:my_board]
platform = espressif32
board = my_board_id
framework = espidf
build_flags =
    -DACTUATOR_GPIO=13           ; Your LED GPIO
    -DACTUATOR_ACTIVE_LOW=0      ; 1=active LOW, 0=active HIGH
```

### Seeed XIAO MG24 (802.15.4 - Planned)

The XIAO MG24 (EFR32MG24B220F1536IM48-B) provides hardware-scheduled TX
for ±1µs seismic chirp precision via Silicon Labs RAIL API. This is a
planned platform with HAL work in progress.

#### Hardware Specifications

| Specification | Value |
|---------------|-------|
| MCU | ARM Cortex-M33 @ 78 MHz |
| Flash | 1536 KB |
| RAM | 256 KB |
| Radio | 802.15.4 + BLE 5.3 |
| RX Sensitivity | -106.4 dBm |
| TX Power | +19.5 dBm max |
| Address | 8-byte EUI-64 (factory-programmed) |

#### Development Options

**Option 1: Simplicity Studio 6 (Gecko SDK) - Recommended for RAIL**

For hardware-precise scheduled TX, use Silicon Labs' native toolchain:

1. **Install Simplicity Studio 6**
   - Download from [Silicon Labs](https://www.silabs.com/developers/simplicity-studio)
   - Install Gecko SDK 4.x during setup

2. **Create RAIL Project**
   ```
   File → New → Silicon Labs Project Wizard
   → Select "EFR32MG24B220F1536IM48" as target
   → Choose "RAIL - RAILtest" or "Empty C Project"
   → Add RAIL component
   ```

3. **Configure Radio (Radio Configurator)**
   - Open `.radioconf` file in project
   - Select "IEEE 802.15.4 OQPSK 250 kbps"
   - Set channel to 15 (~2.425 GHz, golden path for interop with WiFi Ch 6)
   - Configure TX power (+10 dBm default, up to +19.5 dBm)

4. **Key RAIL APIs for UTLP**
   ```c
   // Immediate transmission (spin-wait equivalent)
   RAIL_StartTx(rail_handle, channel, RAIL_TX_OPTIONS_DEFAULT, NULL);

   // Scheduled transmission (hardware-precise timing)
   RAIL_ScheduleTxConfig_t config = {
       .when = absolute_time_us,
       .mode = RAIL_TIME_ABSOLUTE,
       .txDuringRx = RAIL_SCHEDULED_TX_DURING_RX_POSTPONE_TX
   };
   RAIL_StartScheduledTx(rail_handle, channel, RAIL_TX_OPTIONS_DEFAULT, &config, NULL);
   ```

5. **Documentation**
   - [RAIL API Reference](https://docs.silabs.com/rail/latest/)
   - [AN1253: Radio Configurator Guide](https://www.silabs.com/documents/public/application-notes/an1253-efr32-radio-configurator-guide-for-ssv5.pdf)
   - [XIAO MG24 Wiki](https://wiki.seeedstudio.com/xiao_mg24_getting_started/)

**Option 2: Zephyr RTOS**

For RTOS features and portability, use Zephyr's IEEE 802.15.4 driver:

1. **Set up Zephyr environment**
   ```bash
   west init ~/zephyrproject
   cd ~/zephyrproject
   west update
   ```

2. **Build for XIAO MG24**
   ```bash
   west build -b xiao_mg24 samples/net/sockets/echo_server -- \
       -DCONFIG_IEEE802154=y \
       -DCONFIG_IEEE802154_DRIVER=y
   ```

3. **Key Zephyr APIs for UTLP**
   ```c
   #include <zephyr/net/ieee802154_radio.h>

   // Immediate transmission
   ieee802154_radio_api->tx(dev, IEEE802154_TX_MODE_DIRECT, pkt, ...);

   // Scheduled transmission (if driver supports)
   ieee802154_radio_api->tx(dev, IEEE802154_TX_MODE_TXTIME, pkt, ...);
   ```

4. **Note:** Zephyr's IEEE 802.15.4 TX_MODE_TXTIME support varies by driver.
   Check driver capabilities before relying on scheduled TX.

#### 802.15.4 Channel Mapping

| 802.15.4 Channel | Center Freq | WiFi Overlap | Notes |
|------------------|-------------|--------------|-------|
| 11 | 2.405 GHz | Ch 1 | |
| **15** | **2.425 GHz** | **Ch 6** | **Golden Path** |
| 20 | 2.450 GHz | Ch 6-7 | |
| 26 | 2.480 GHz | Ch 11 | |

**Recommended:** Channel 15 (near WiFi Ch 6 "golden path" for UTLP chirality)

#### Interoperability Note

MG24 (802.15.4) and ESP32 (ESP-NOW/WiFi) use different physical layers:
- **MG24 swarm:** 802.15.4 devices sync with each other
- **ESP32 swarm:** ESP-NOW devices sync with each other
- **Bridge:** ESP32-C6 has both WiFi and Thread, enabling future bridging

The HAL's transport-agnostic address abstraction (`utlp_addr_t`) enables
the protocol layer to work identically across both transports.

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

## Servo-Locked Phase Correction (S2 Claim 55)

Standard firefly synchronization applies phase corrections **instantly**:
```c
// Standard firefly: phase step (discontinuity)
local_time += offset;
```

This creates **spectral splatter** — the sudden jump corrupts coherent aperture
integration. For coherent beamforming applications, transient behavior matters.

UTLP v3 uses **frequency slewing** instead:
```c
// UTLP servo-lock: frequency slew (smooth)
drift_correction_ppb = offset * 1e9 / T_convergence;
// Clock speeds up/slows down rather than jumping
```

| Aspect | Standard Firefly | UTLP Servo-Lock |
|--------|-----------------|-----------------|
| Phase adjustment | Instantaneous Δφ | Frequency slewing Δf |
| Convergence window | N/A (instant) | 500ms (configurable) |
| Output type | Discrete flash | Continuous wave |
| Transient behavior | Phase jump | Spectral purity maintained |

**10-Second Exception:** During the genesis pulse (first 10 seconds), instant
jumps ARE allowed. This enables fast initial synchronization. After 10 seconds,
all corrections use frequency slewing.

**Configuration:** See `UTLP_SERVO_*` constants in `utlp_config.h`.

## Genesis Reset Detection

When a Genesis node resets during testing, it may broadcast a newer epoch that
would corrupt followers' timing. UTLP v3 detects this by checking for
**suspiciously large forward jumps**:

```c
// Reject beacons that jump forward more than MAX_FORWARD_JUMP (1 second)
if (peer_atomic_time > local_atomic_time + UTLP_MAX_FORWARD_JUMP_US) {
    // This looks like a reset Genesis with stale epoch
    // Block adoption, log warning
}
```

This prevents a single reset node from disrupting an established swarm.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Protocol Trinity                          │
│                                                              │
│    UTLP = "when" (time sync, beacons, trust)                │
│    RFIP = "where" (positioning, ranging, anchors)           │
│    SMSP = "what" (score-driven actuation, patterns)         │
├─────────────────────────────────────────────────────────────┤
│              Protocol Layer (utlp.c + utlp_trust.c)         │
│                                                              │
│    Boot as Genesis (stratum 1) → Notify SMSP when synced    │
│    Listen for beacons → Servo-lock to better stratum        │
│    Biological Governance: Metabolic Ledger, Immune Checks   │
│                                                              │
│    get_atomic_time() = local_time + offset + drift_corr     │
├─────────────────────────────────────────────────────────────┤
│              Application Layer (utlp_smsp.c)                │
│                                                              │
│    Wait for sync_ready semaphore from protocol layer        │
│    Load pattern (BLINK_1HZ, BREATHE, EMERGENCY)             │
│    Execute score lines at atomic time with interpolation    │
│    Calls: utlp_hal_get_atomic_time_us(), set_actuator()     │
├─────────────────────────────────────────────────────────────┤
│          Transport Manager (utlp_transport.c)               │
│                                                              │
│    Multi-Arbor Architecture: ESP-NOW + 802.15.4 + BLE       │
│    Staggered Startup: 802.15.4 first, ESP-NOW after 15s     │
│    TX Mode: ALL, PRIMARY, or BEST (prefers 802.15.4)        │
│    Per-Transport Dormancy: Selective arbor sleep/wake       │
│                                                              │
│    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│    │   ESP-NOW    │  │  802.15.4    │  │     BLE      │     │
│    │    Arbor     │  │    Arbor     │  │    Arbor     │     │
│    └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│           │                 │                 │              │
│    ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐     │
│    │utlp_hal_esp32│  │utlp_hal_154  │  │ (future)     │     │
│    └──────────────┘  └──────────────┘  └──────────────┘     │
├─────────────────────────────────────────────────────────────┤
│             Hardware Abstraction Layer (utlp_hal.h)         │
│                                                              │
│    Time:     get_micros(), get_atomic_time_us()             │
│    Radio:    tx_packet(), rx_wait(), rx_poll()              │
│    Actuator: set_actuator_phase() [GPIO LED]                │
├─────────────────────────────────────────────────────────────┤
│           ESP32 Implementation (utlp_hal_esp32.c)           │
│                                                              │
│   ┌─────────┬─────────────┬─────────┬─────────┐             │
│   │ ESP-NOW │ MCPWM Phase │ Timer   │Semaphore│             │
│   │ (radio) │  (HPLAC)    │ (time)  │  (RX)   │             │
│   └─────────┴─────────────┴─────────┴─────────┘             │
└─────────────────────────────────────────────────────────────┘
```

## Multi-Arbor Transport Architecture

UTLP v3 supports multiple radio transports simultaneously. Each transport is an
**arbor** (sensory branch) feeding the central **soma** (unified atomic time).

### Supported Transports

| Transport | Status | Timing | Use Case |
|-----------|--------|--------|----------|
| **ESP-NOW** | ✅ Production | ~100µs jitter | WiFi-based, longer range |
| **802.15.4** | ✅ Production | ~10µs jitter | Better timing, cross-vendor |
| **BLE** | 🔄 Planned | TBD | Low power, beacons |

### Staggered Startup (Testing Feature)

When both 802.15.4 and ESP-NOW are available, the transport manager can delay
WiFi startup to enable isolated testing:

```c
// Default: 802.15.4 starts immediately, ESP-NOW delayed 15 seconds
utlp_transport_config_t cfg = UTLP_TRANSPORT_CONFIG_DEFAULT();
utlp_transport_init(&cfg);

// Immediate: Both start together (production mode)
utlp_transport_config_t cfg = UTLP_TRANSPORT_CONFIG_IMMEDIATE();
utlp_transport_init(&cfg);
```

**Test Scenarios Enabled:**
1. **t=0 to t=15s:** Pure 802.15.4 sync (observe genesis election, measure jitter)
2. **t=15s:** WiFi arbor joins (observe arbor merge behavior)
3. **t>15s:** Steady state (both transports active, verify TX routing)

### TX Mode Options

| Mode | Behavior | Use Case |
|------|----------|----------|
| `UTLP_TX_MODE_ALL` | Broadcast on ALL enabled transports | Maximum redundancy |
| `UTLP_TX_MODE_PRIMARY` | TX on first available only | Minimum RF |
| `UTLP_TX_MODE_BEST` | TX on best transport (802.15.4 > ESP-NOW) | Optimal timing |

### Per-Transport Dormancy

The arbor system enables selective sleep of individual transports:

```c
// Silence WiFi to prove 802.15.4 can maintain Hard-PLL
utlp_transport_yield(UTLP_TRANSPORT_ESPNOW);

// Wake WiFi after testing
utlp_transport_wake(UTLP_TRANSPORT_ESPNOW);
```

**Degraded Re-Entry:** Waking arbors enter at elevated stratum until they
re-verify phase against the soma's internal clock. This prevents "phantom arbor"
attacks where stale timing data could corrupt the swarm.

### Files

| File | Description |
|------|-------------|
| `utlp_transport.h` | Transport management API |
| `utlp_transport.c` | Multi-arbor implementation (~700 lines) |
| `utlp_arbor.h` | Per-transport dormancy API |
| `utlp_hal_802154.h` | 802.15.4 HAL interface |

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

## Time-Indexed LED Control (Legacy)

> **Note:** In v3, LED control moved to SMSP application layer.
> This section describes the underlying principle.

The LED state is **calculated** from atomic time, not **toggled** by delays:

```c
uint64_t cycle_pos = atomic_time % BLINK_PERIOD_US;  // 1 second
bool led_on = (cycle_pos < BLINK_PERIOD_US / 2);     // 50% duty
```

**Why this is drift-proof:** Every node with the same atomic_time
will calculate the same LED state. No drift accumulation.

## SMSP - Synchronized Multimodal Score Protocol

SMSP is the "what" layer of the Protocol Trinity. It implements score-driven
actuator control using atomic time from UTLP.

### Pattern Playback Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  UTLP PROTOCOL LAYER (utlp.c)                               │
│  - Beacons, trust, stratum                                  │
│  - Calls smsp_notify_sync_ready() once synced               │
└──────────────────────────┬──────────────────────────────────┘
                           │ sync semaphore
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  SMSP APPLICATION LAYER (utlp_smsp.c)                       │
│  - FreeRTOS task: smsp_task()                               │
│  - Pattern execution engine                                  │
│  - Interpolation between score lines                        │
│  - Calls utlp_hal_get_atomic_time_us() each tick            │
│  - Calls utlp_hal_set_actuator_phase() for LED              │
└─────────────────────────────────────────────────────────────┘
```

### Built-in Patterns

| Pattern | Description | Duration |
|---------|-------------|----------|
| `BLINK_1HZ` | Simple 1Hz square wave (matches legacy `run_physics`) | 1s loop |
| `BREATHE` | Smooth 2-second fade in/out (demonstrates interpolation) | 2s loop |
| `EMERGENCY` | SAE J845 emergency vehicle flash pattern | 1s loop |

### Score Line Format

Each score line specifies an actuator state at a point in time:

```c
typedef struct __attribute__((packed)) {
    uint32_t time_offset_us;      // When to execute (relative to pattern start)
    uint16_t transition_ms_x4;    // Fade duration (×4 scaling = 0-1020ms)
    uint8_t  actuator_id;         // UTLP_ACTUATOR_MAIN (0)
    uint8_t  duty_pct;            // Duty cycle 0-100
    uint8_t  frequency_hz_div10;  // Frequency / 10 (0 = DC)
    uint8_t  flags;               // Interpolation + sync flags
} smsp_score_line_t;              // 10 bytes
```

### API

```c
void smsp_init(void);                          // Initialize subsystem
void smsp_notify_sync_ready(void);             // Called by utlp.c after sync
int  smsp_load_builtin(smsp_builtin_pattern_t id);
int  smsp_start(uint64_t start_time_us);       // 0 = "now"
int  smsp_stop(void);
bool smsp_is_playing(void);
void smsp_task(void *pvParameters);            // FreeRTOS task entry
```

**Reference:** `src/pattern_playback.h` (production SMSP with bilateral zones)

## Expected Serial Output

```
I (552) UTLP: ========================================
I (562) UTLP: UTLP GENESIS NODE v3 - Biological Governance
I (562) UTLP: "Time is born of one."
I (572) UTLP: ========================================
I (572) UTLP: MAC: 10:51:DB:1C:B3:08
I (582) UTLP: Stratum: 1 (GENESIS)
I (582) UTLP: Beacon: 11-byte Seismic Chirp (3-burst @ 2ms)
I (592) UTLP: Election: Score-based (higher score wins)
I (592) UTLP: Relay: Frontier detection (edge nodes = Providers)
I (602) UTLP: Interval: Genesis Pulse / Promotion Pulse / Echo Rule
I (602) UTLP: Servo-Lock: 500ms convergence, ±100ppm max
I (612) UTLP: Blink period: 1000 ms
I (612) UTLP: Drift Analysis: Enabled (polynomial fit)
I (612) UTLP: ========================================
I (XXX) UTLP: Beacon interval: 100 ms (uptime 0s, role=Genesis)
I (XXX) SMSP: Waiting for sync...
I (XXX) UTLP: [LED] ON  @ phase=500000 us (stratum 1)
I (XXX) UTLP: [LED] OFF @ phase=0 us (stratum 1)
I (XXX) UTLP: Beacon interval: 500 ms (uptime 1s, role=Genesis)
...
I (XXX) UTLP: Same stratum, higher score wins (180 > 120)
I (XXX) UTLP: Servo: genesis phase (instant jump allowed)
I (XXX) UTLP: SYNCED: stratum=2, offset=+1234 us
I (XXX) UTLP: Stratum changed: 1 -> 2 (provider=YES)
I (XXX) SMSP: Sync ready, loading BLINK_1HZ pattern
I (XXX) SMSP: Playing BLINK_1HZ (looping)
I (XXX) UTLP: Beacon interval: 1000 ms (uptime 5s, role=Provider)
...
I (XXX) UTLP: Servo: slewing offset +42us at 84000 ppb
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
stubbed (chirality functions); **Spatial Loom in progress** (RFIP HAL layer);
Thermal/Social Looms are future work.

### The Spatial Loom (RFIP)

The **Spatial Loom** weaves position from observation entropy. Just as the
Temporal Loom produces Time Lords from clock stability, the Spatial Loom
produces position estimates from ranging observations.

**RFIP (Reference Frame Independent Positioning)** is the spatial threat domain:

```
+-------------------+------------------------+-------------------+
|  Threat Domain    |    Entropy Signal      |  Emergent State   |
+-------------------+------------------------+-------------------+
|  Temporal         | Clock drift/instability| Time Lord (Anchor)|
|  Spectral         | RF congestion/jamming  | Channel divergence|
|  **Spatial**      | Position uncertainty   | RFIP coordinates  |
+-------------------+------------------------+-------------------+
```

#### Data Hierarchy (Build from Always-Available)

| Layer | Source | Precision | Always Available | Status |
|-------|--------|-----------|------------------|--------|
| 0 | **RSSI** | ~3-5m | ✓ | Phase 1 |
| 1 | **RSSI differential** | ~1-3m | ✓ | Phase 1 |
| 2 | **TDoA from UTLP beacons** | ~30cm | ✓ | Phase 3 |
| 3 | **CSI** | ~50cm-1m | ✓ (ESP32) | Phase 2 |
| 4 | **Multipath signatures** | Fingerprint | ✓ (learned) | Phase 6 |
| 5 | **802.11mc FTM** | ~10-50cm | Platform-dependent | Phase 4 |
| 6 | **UWB (DW3000)** | ~10cm | Add-on | Phase 5 |

**Philosophy:** Build from always-available sources (RSSI, CSI, TDoA). Let
802.11mc/UWB calibrate and enhance, not replace.

#### The "Chaos Monkey" Principle

ESP32 DevKit V1 has **NO FTM support**. It serves as the "Chaos Monkey":
if RFIP works on DevKit V1 using only RSSI/CSI/TDoA, the core algorithm
is sound. FTM then becomes calibration, not foundation.

#### Silicon Revision Detection

ESP32-C6 has known errata for FTM:
- **ECO0/ECO1 (v0.0-0.1):** FTM initiator broken (T3 timestamp errata)
- **ECO2+ (v0.2+):** FTM initiator FIXED

The HAL queries silicon revision at boot and advertises accurate capabilities.
XIAO ESP32-C6 ships with ECO2 silicon (verified).

#### Deviations from RFIP Tech Spec

Items implemented but not yet in `docs/RFIP_Technical_Specification.md`:

| Deviation | Description | Priority |
|-----------|-------------|----------|
| **Time Sync Extraction** | NTP-style offset from FTM T1-T4 timestamps | HIGH |
| **FTM Session Structures** | Detailed `rfip_ftm_measurement_t` with T1-T4 ps | MEDIUM |
| **Metrics Structure** | `rfip_metrics_t` for data logging | MEDIUM |

**See:** `rfip_hal.h` for structures, `docs/RFIP_Technical_Specification.md`
for master spec.

### Simulation (`sim/genesis_reset_coherence.py`)

Python simulation for testing phase coherence and Byzantine scenarios:
- Genesis reset and phase coherence recovery
- Rogue Genesis attacks (ancient epoch claims)
- Web of Time merge (two swarms meeting)
- Derivative-based detection (jitter variance analysis)

## Files

| File | Description |
|------|-------------|
| `utlp_config.h` | **Centralized configuration (SSOT)** - all tunable constants |
| `utlp.c` | Protocol layer with servo-lock and genesis reset detection |
| `utlp_smsp.h/c` | **SMSP** - score-driven pattern playback (Protocol Trinity "what") |
| `utlp_trust.h/c` | Metabolic Ledger (Hebbian trust, median consensus) |
| `utlp_immune.h/c` | Immune Checkpoint (token bucket, anergy) |
| `utlp_transport.h/c` | **Multi-Arbor Transport Manager** (ESP-NOW + 802.15.4) |
| `utlp_arbor.h/c` | Per-transport selective dormancy API |
| `utlp_loom.h/c` | **The Loom** - Emergent Time Lord state machine (Phase 9) |
| `utlp_phase.h/c` | **HPLAC** - Hardware Phase Locked Atomic Coherency (MCPWM) |
| `utlp_hal.h` | HAL interface contract (time, radio, actuator) |
| `utlp_hal_esp32.c` | ESP32 HAL implementation (ESP-NOW, MCPWM) |
| `utlp_hal_802154.h` | 802.15.4 HAL interface (raw MAC, FCF 0x8841) |
| `utlp_rfip.h` | RFIP types and stub API (ranges, anchors, positions) |
| `rfip_hal.h` | **RFIP HAL** (capability detection, observation types) |
| `rfip_hal.c` | RFIP HAL implementation (runtime silicon detection) |
| `utlp_main_esp32.c` | Platform entry point (`app_main()`) |
| `sim/genesis_reset_coherence.py` | Python simulation for coherence + Byzantine + multi-arbor testing |
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
- `docs/Connectionless_Distributed_Timing_Prior_Art.md` - Research foundation (122 claims)
- `docs/UTLP_Technical_Supplement_S2.md` - Biological Governance (100+ claims)
- `src/pattern_playback.h` - Production SMSP with bilateral zones
- `examples/utlp_skeleton/` - Cross-platform reference implementation

## Future Work

### Temporal Loom
- **Automatic failover:** Timeout-based re-election when Genesis goes offline
- **GPS stratum-0:** External time reference integration
- ~~**Drift compensation:** Use tracked drift rate for active clock correction~~ ✅ **v3: Servo-lock implemented**
- **Panic Response:** Stratum 255 "Help!" signal for rescue chirps

### Spectral Loom
- **Channel chirality:** Dynamic channel divergence under congestion pressure

### Spatial Loom (RFIP)
- **CSI integration:** Subcarrier-level ranging and motion detection (Phase 2)
- **TDoA from UTLP beacons:** Position from arrival time differences (Phase 3)
- **802.11mc FTM:** High-precision ranging as calibration layer (Phase 4)
- **UWB integration:** DW3000 for centimeter-level ranging (Phase 5)
- **RF Tomography:** Mesh as distributed radar for presence detection (Phase 6)
- **Multipath fingerprinting:** Location recognition from RF signatures (Phase 6)

### Multi-Arbor Architecture (Phase 8) ✅ IMPLEMENTED

Cross-manufacturer 802.15.4 timing mesh using raw IEEE MAC Data Frames.

**Key Discovery:** All three target platforms have TRUE hardware-scheduled TX:

| Platform | API | Jitter | Method |
|----------|-----|--------|--------|
| **ESP32-C6** | `esp_ieee802154_transmit_at()` | ~1µs | Radio timer |
| **MG24 (RAIL)** | `RAIL_StartScheduledTx()` | ~0.1µs | Radio timer |
| **nRF52840** | `nrf_802154_transmit_raw_at()` | ~0.1µs | TIMER + PPI |

**Files:**
- `utlp_hal_802154.h` - 802.15.4 HAL interface (FCF 0x8841, PAN ID 0xCAFE)
- `utlp_hal_esp32c6_154.c` - ESP32-C6 implementation with hardware TX
- `utlp_hal_mg24_154.c` - MG24 RAIL stub
- `utlp_hal_nrf52840_154.c` - nRF52840 stub
- `utlp_arbor.h/c` - Per-transport selective dormancy

**Build:**
```bash
pio run -e utlp_esp32c6_154 -t upload && pio device monitor
```

**Prior Art:** Claims 237-247 (see `PRIOR_ART_DRAFT.md`)

### Phase 9: Biological Architecture Upgrade ✅ IMPLEMENTED

Phase 9 completes the biological governance architecture with independent engine
timing, per-arbor health tracking, and the Loom state machine for emergent
Time Lord authority.

#### The Loom: Emergent Time Lord Authority (`utlp_loom.h/c`)

When no beacons are received for 2 minutes (timeline "frays"), the Loom begins
"weaving" a new temporal thread, promoting the node to Time Lord (ANCHOR state).

**State Machine:**
```
                    ┌──────────────────┐
                    │                  │
         (silence)  ▼                  │ (better beacon)
    ┌─────────> DORMANT ◄──────────────┤
    │              │                   │
    │   (2 min silence on arbor)       │
    │              ▼                   │
    │          WEAVING ────────────────┘
    │              │    (10s warmup complete)
    │              ▼
    └────────── ANCHOR ──────────────┐
                   │                  │
                   │ (better beacon)  │
                   ▼                  │
               DISSOLVING ────────────┘
```

**Per-Arbor Independence:** Each arbor (WiFi, 802.15.4, BLE) has its own Loom
state. A device can be Time Lord on one transport while following on another.

**Genesis Pulse Integration:** When the Loom promotes an arbor to ANCHOR, or
when an arbor wakes from dormancy, it requests a Genesis Pulse. The main loop
consumes these requests and broadcasts the 3-burst seismic chirp.

#### Engine Timer (10Hz Independent Tick)

The UTLP engine now runs on an independent 10Hz timer (`esp_timer`), not just
when packets arrive. This ensures:

- **Drift model updates** even when transport is yielded
- **Loom tick** runs continuously for silence detection
- **Genesis Pulse scheduling** independent of RX events

```c
static void engine_tick_callback(void* arg) {
    utlp_clock_update_model();  // Always runs
    if (!utlp_is_fully_dormant()) {
        utlp_loom_tick();       // Detect timeline fray
    }
}
```

#### Variable Gain PLL (Claim 55 Compliance)

Three-state phase correction replaces hard jumps after cold start:

| State | Condition | Behavior | Rationale |
|-------|-----------|----------|-----------|
| **Cold Start** | Uptime < 5s | Hard jump | "Snap to grid" quickly |
| **Locked** | Error < 10ms | Slow slew (200 ppm) | Spectral purity |
| **Recovery** | Error > 10ms | Fast slew (5000 ppm) | Catch up smoothly |

This implements S2 Claim 55 (Servo-Locked Phase Correction) - frequency slewing
instead of phase discontinuities for coherent beamforming compatibility.

#### Per-Arbor Health Tracking (Blood-Brain Barrier)

The trust system now tracks peer health **per-arbor**, not globally:

```c
typedef struct __attribute__((packed)) {
    uint32_t last_seen_ms[UTLP_MAX_ARBORS];      // Per-arbor timestamps
    int32_t  last_offset_us[UTLP_MAX_ARBORS];    // Per-arbor timing
    uint8_t  health_score[UTLP_MAX_ARBORS];      // Per-arbor reputation
    // ...
} utlp_peer_ledger_t;
```

**Benefit:** A peer that's jittery on WiFi doesn't pollute their 802.15.4
reputation. Each arbor is an isolated "sensory branch."

#### Airlock Integration (Yield/Wake)

The arbor yield/wake API now integrates with the Loom:

- `utlp_arbor_yield()` pauses the Loom for that arbor (no false silence detection)
- `utlp_arbor_wake()` resumes the Loom AND requests Genesis Pulse (mandatory)

**Mandatory Genesis Pulse on Wake:** App-layer yield is invisible to the UTLP
engine. When an arbor resumes, it MUST announce "I'm back" to the swarm via
Genesis Pulse. This prevents "phantom arbor" reintegration bugs.

**Files:**
- `utlp_loom.h/c` - Loom state machine + Genesis Pulse API
- `utlp.c` - Engine timer, Genesis Pulse consumption in main loop
- `utlp_arbor.c` - Loom pause/resume integration
- `utlp_trust.c` - Per-arbor health arrays

**Prior Art:** Claims 35-41 (Emergent Role Differentiation, Dormancy Control)

### HPLAC: Hardware Phase Locked Atomic Coherency (`utlp_phase.h/c`)

**"Physics First: Hardware defines time, not software."**

HPLAC replaces software-based time offset tracking with a hardware-driven MCPWM
timer that IS the source of phase truth. The ESP32 MCPWM peripheral runs at 50kHz,
providing 20µs granularity (0.0072°) over a full 1-second phase cycle.

```
Timer Count:  0 ─────────────────────────────────────► 49,999 (1s)
              │                                           │
              │  ← Single hardware SYNC resets here →     │
              │                                           │
Full Phase:   0° ────────────────────────────────────► 360°
              │                                           │
              │         ONE REGISTER = ONE CYCLE          │
              │    (True atomic coherency - no sub-cycles) │
              └───────────────────────────────────────────┘
```

**Key Features:**

| Feature | Description |
|---------|-------------|
| **Single-Register Phase** | 50kHz × 50000 ticks = 1 second in one hardware register |
| **Hard Sync (Cold Start)** | MCPWM soft sync instantly jams phase during first 5s |
| **Soft Slew (Locked)** | Period bending for spectral purity after lock |
| **Variable Gain PLL** | COLD → LOCKED → RECOVERY state machine |
| **Critical Sections** | Prevents execution jitter, torn reads, sticky slew |

**Phase Engine State Machine:**

```
            ┌───────────────────────────────────┐
            │                                   │
   Boot     ▼                                   │ (error > threshold)
  ───────► COLD ─────────────────────────────►  │
            │                                   │
            │ (uptime > 5s)                     │
            ▼                                   │
         LOCKED ◄───────────────────────────────┤
            │                                   │
            │ (error > threshold)               │
            ▼                                   │
        RECOVERY ───────────────────────────────┘
            │      (error < threshold/2)
            │
            └──► LOCKED (hysteresis)
```

**Atomicity Guarantees (Purple Team Fixes):**

1. **Execution Jitter Prevention**: Hard sync wrapped in `portENTER_CRITICAL()`
2. **Torn Read Prevention**: 64-bit `cycle_count` getters use critical sections
3. **Sticky Slew Prevention**: Hard sync resets period to nominal

**API:**

```c
esp_err_t utlp_phase_init(void);              // Initialize MCPWM timer
uint32_t  utlp_phase_get_ticks(void);         // Current phase (0-49999)
uint64_t  utlp_phase_get_cycle_count(void);   // Full cycles since init
esp_err_t utlp_phase_hard_sync(uint32_t t);   // Instant phase jam (cold)
esp_err_t utlp_phase_slew(int32_t error);     // Frequency bend (locked)
esp_err_t utlp_phase_on_beacon(uint32_t p, uint64_t rx); // High-level entry
uint64_t  utlp_phase_get_atomic_time_us(void); // Replaces HAL version
```

**Prior Art:** Claim 55 (Servo-Locked Phase Correction) in Technical Supplement S2

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
