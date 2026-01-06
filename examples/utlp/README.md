# UTLP v3 - Biological Governance for Distributed Time

**Universal Time Lord Protocol** (UTLP) - Multi-transport implementation demonstrating
connectionless distributed time synchronization using **biological governance**
instead of political consensus. Part of the **PHYRFLY Protocol Stack** (Protocol Trinity:
UTLP/RFIP/SMSP - "when/where/what").

> **v3 Features:** Multi-Arbor Transport Architecture (ESP-NOW + 802.15.4),
> Servo-Locked Phase Correction (S2 Claim 55), Genesis Reset Detection,
> SMSP Application Layer, Centralized Configuration (SSOT),
> **Phase 9: The Loom** (Emergent Time Lord, Per-Arbor Genesis Pulse),
> **Phase 10: Proprioception** (Hardware-assisted latency learning for TX scheduling),
> **Phase 11: Spectral Retina** (Multi-transport RSSI telemetry for Radio Color),
> **Phase 12: Session Continuity** (PT-6: Seniority Bankruptcy on reboot detection),
> **HPLAC: Hardware Phase Locked Atomic Coherency** (MCPWM-based phase engine),
> **Claim 253: Polychromatic Stratum Asymmetry** (per-transport stratum levels),
> **Claim 255: Rolling Splice-Site Security** (Bio-TOTP encryption).

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
| 1 | `utlp_config.h` | All tunable parameters (SSOT - authoritative constant definitions) |
| 2 | `utlp.c` (header comments) | The manifesto - why biology beats politics |
| 3 | `utlp_trust.h` | Hebbian learning, median consensus, Dunbar's Number |
| 4 | `utlp_immune.h` | T-cell exhaustion, quorum sensing, cytokine storms |
| 5 | `utlp_loom.h` | Emergent Time Lord + Polychromatic Stratum (Claim 253) |
| 6 | `utlp_phase.h` | Hardware Phase Engine (MCPWM atomic coherency) |
| 7 | `utlp_transport.h` | Multi-arbor architecture (ESP-NOW + 802.15.4) |
| 8 | `utlp_smsp.h` | Score-driven actuation (Protocol Trinity: when/where/what) |
| 9 | `utlp_hal.h` | Time-indexed execution, imports SSOT from utlp_config.h |
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

## Protocol Evolution Timeline

PHYRFLY protocol stack development phases (all ✅ IMPLEMENTED):

| Phase | Name | Description | Key Files |
|-------|------|-------------|-----------|
| **1-3** | Basic Sync | NTP-style beacon exchange, clock offset tracking | `utlp.c` |
| **4-5** | Trust Layer | Metabolic Ledger (Hebbian learning), median consensus | `utlp_trust.c` |
| **6** | Immune System | Token bucket rate limiting, T-cell exhaustion (anergy) | `utlp_immune.c` |
| **7** | Security | Bio-TOTP (Claim 255), Purple Team hardening (PT-1 through PT-5) | `utlp_security.c`, `utlp_hal_security.c` |
| **8** | Multi-Arbor | ESP-NOW + 802.15.4, staggered startup, transport manager | `utlp_transport.c`, `utlp_arbor.c` |
| **9** | The Loom | Emergent Time Lord, Polychromatic Stratum (Claim 253) | `utlp_loom.c` |
| **10** | Proprioception | Hardware-assisted TX latency learning (802.15.4 HAL) | `utlp_hal_esp32c6_154.c` |
| **11** | Spectral Retina | Multi-transport RSSI telemetry ("radio color") | `utlp_trust.c` |
| **12** | Session Continuity | PT-6: Seniority Bankruptcy on reboot detection | `utlp_trust.c` |
| **13** | HPLAC | Hardware Phase Locked Atomic Coherency (MCPWM engine) | `utlp_phase.c` |
| **14** | ILC | Interrupt Latency Compensation (ISR proprioception) | `utlp_phase.c` |

### Purple Team Hardening (Security Audit)

All Purple Team directives implemented:

| PT# | Directive | Status | Impact |
|-----|-----------|--------|--------|
| PT-1 | Stateless AES-CTR | ✅ | Reset `nc_off=0` before every packet |
| PT-2 | RISC-V Torn Reads | ✅ | `portENTER_CRITICAL()` for all 64-bit ops |
| PT-3 | Infinite Slew | N/A | Architecture uses continuous P-servo |
| PT-4 | Herd Immunity | ✅ | Public/Private identical crypto paths |
| PT-5 | Strict Plausibility | ✅ | TX_Power, Drift, Heartbeat validation |
| PT-6 | Session Continuity | ✅ | Salt change = Seniority Bankruptcy |
| PT-7 | ILC Integration | ✅ | Spinlock protection for ISR learning |
| PT-8 | Servo State Race | ✅ | Spinlock for all g_servo 64-bit fields |
| PT-9 | Bankruptcy Stratum | ✅ | Bankrupted peers reset to stratum=255 |
| PT-10 | INNATE Genesis Guard | ✅ | Genesis pulse check in INNATE immunity |
| PT-11 | Coalescence Fix | ✅ | Use peer atomic time, not tenure |
| PT-12 | Token Waste Fix | ✅ | Separate budget check from consume |

### Prior Art Claims Implemented

| Claim | Name | Description | File |
|-------|------|-------------|------|
| **253** | Polychromatic Stratum | Per-transport Genesis election | `utlp_loom.c` |
| **255** | Rolling Splice-Site Security | Bio-TOTP key rotation per second | `utlp_security.c` |

### Critical Architectural Fixes (v3.4 - January 2026)

**Genesis Pulse Swarm Disruption Fix (PT-10):**

When two devices are synchronized and a third device boots, the newborn's rapid genesis pulse
(100ms beacon interval) was disrupting the established sync. Root cause: the INNATE IMMUNITY
path had no genesis pulse detection.

**Failure Chain (Before Fix):**
1. Device C boots with rapid 100ms genesis pulses
2. Devices A & B fire entrainment at C (5 tokens in 400ms)
3. A & B enter ANERGY state (36s deaf period)
4. A & B lose their mutual "best" peer reference
5. Device C reaches A & B via INNATE IMMUNITY (`!best && remote_stratum < local_stratum`)
6. A & B adopt C's stale epoch WITHOUT genesis pulse check
7. **SYNC BROKEN** between A & B

**FIX-1 (CRITICAL): INNATE IMMUNITY Genesis Protection**

Added genesis pulse check to both INNATE IMMUNITY paths (`utlp.c:2015-2040` and `utlp.c:2041-2087`):
- "Better Stratum" path now checks `utlp_trust_is_genesis_pulsing(sender)`
- "Same Stratum / First Born Wins" path also protected
- Genesis-pulsing peers blocked from INNATE adoption until they exit genesis phase
- Log: `"INNATE: Blocking genesis-pulsing peer XX:YY (stratum=N, interval=Nms)"`

**FIX-2 (HIGH): Entrainment Token Conservation**

Added genesis pulse check before entrainment fire (`utlp.c:2318-2335`):
- Genesis-pulsing peers skipped for entrainment (they'll self-correct in 5s)
- Preserves immune budget for real threats (non-genesis drifting peers)
- Prevents ANERGY cascade that breaks established sync
- Log: `"Entrainment: Skipping genesis-pulsing peer XX:YY (interval=Nms) - will self-correct"`

**Expected Behavior (After Fix):**
1. Device C boots with genesis pulse
2. A & B observe C but skip entrainment (token conservation)
3. A & B maintain their mutual sync (no ANERGY)
4. C exits genesis phase (5s) and naturally syncs via ADAPTIVE IMMUNITY
5. **SWARM STABLE** - established devices protected from newborn disruption

### Critical Architectural Fixes (v3.6 - January 2026)

**Coalescence Bug Fix (PT-11): Tenure Check Prevented Device Sync**

After adding frequency slewing (v3.5), two devices could no longer entrain. Root cause:
the genesis pulse detection used `first_seen_ms` (when WE first saw the peer) instead of
the peer's intrinsic age. This blocked ALL newly-discovered peers for 5 seconds, even
established ones that a newcomer just met.

**Biological Principle:**
> *"The nature of the cell is to come together."*

A newcomer encountering an established peer should coalesce, not fight. The peer's atomic
time (TX timestamp) tells us how long they've been running - this is intrinsic to them,
not dependent on when we first noticed them.

**Failure Scenario (Before Fix):**
1. Device A running for 60 seconds (atomic time = 60s)
2. Device B boots and discovers A
3. B checks `utlp_trust_is_genesis_pulsing(A)` using tenure:
   - `tenure_ms = now - first_seen_ms = 0ms` (just discovered!)
   - Tenure < 5000ms → **INCORRECTLY** returns `true` (genesis pulsing)
4. B blocks adoption of A's time despite A being established
5. **COALESCENCE BROKEN** - devices cannot sync

**Root Cause:**
The v3.5 tenure check conflated two distinct concepts:
- "Peer I've never seen before" (tenure low)
- "Peer that just rebooted" (atomic time low)

An established peer (atomic time = 60s) discovered by a newcomer still had tenure_ms ≈ 0
because the NEWCOMER just discovered that peer.

**Fix (v3.6):** Use peer's atomic time (TX timestamp) as age indicator:
```c
if (peer_tx_time >= genesis_threshold_us) {
    /* Peer running >= 5 seconds - clearly established */
    return false;  /* NOT genesis-pulsing */
}
```

This is unforgeable: a newborn cannot claim to be old (their atomic time starts at 0).
A cell's age is intrinsic, not based on when a neighbor first noticed it.

**API Change:** `utlp_trust_is_genesis_pulsing()` now requires peer's TX time:
```c
// Before (v3.5)
bool utlp_trust_is_genesis_pulsing(const utlp_peer_ledger_t *peer);

// After (v3.6)
bool utlp_trust_is_genesis_pulsing(const utlp_peer_ledger_t *peer,
                                    int64_t peer_tx_time);
```

**Files Modified:**
- `utlp_trust.h`: Updated function signature with biological analogy documentation
- `utlp_trust.c`: Rewrote `utlp_trust_is_genesis_pulsing()` (lines 995-1049)
- `utlp.c`: Updated 4 call sites to pass `remote_tx_time` parameter

**Expected Behavior (After Fix):**
1. Device A running (atomic time = 60s)
2. Device B boots and discovers A
3. B checks `utlp_trust_is_genesis_pulsing(A, A.tx_time)`:
   - `peer_tx_time = 60,000,000 µs` (A's atomic time from beacon)
   - 60s >= 5s → Returns `false` (A is NOT genesis-pulsing)
4. B adopts A's time via INNATE IMMUNITY
5. **COALESCENCE WORKS** - newcomer syncs with established peer

### Critical Architectural Fixes (v3.7 - January 2026)

**Token Waste Bug Fix (PT-12): Immune Budget Exhausted on First Contact**

When a single device first detected a peer powering up, anergy exhausted immediately (~170ms).
Root cause: `utlp_immune_can_defend()` consumed a token just by being **called**, even if
subsequent checks (quorum sensing) failed and no entrainment pulse was fired.

**Failure Scenario (Before Fix):**
```
14:53:13.009 > New Peer B3:08 discovered
14:53:13.010 > Entrainment: No quorum - I may be the outlier   ← Token #1 wasted
14:53:13.013 > Entrainment: No quorum - I may be the outlier   ← Token #2 wasted
14:53:13.018 > Entrainment: No quorum - I may be the outlier   ← Token #3 wasted
14:53:13.107 > Entrainment: No quorum - I may be the outlier   ← Token #4 wasted
14:53:13.112 > Entrainment budget exhausted. Entering anergy.  ← Token #5 wasted
14:53:13.115 > Entrainment: Budget exhausted - B3:08 escapes
```

With genesis chirps (3 bursts × 100ms), 5 tokens exhausted in ~170ms without firing a single
entrainment pulse. The device entered anergy (36-second deaf period) immediately on first contact.

**Root Cause:**
The `utlp_immune_can_defend()` function was designed as "check and consume" combined:
```c
bool utlp_immune_can_defend(void) {
    if (g_immune.tokens > 0) {
        g_immune.tokens--;  // BUG: Consumes token just by CHECKING!
        return true;
    }
    return false;
}
```

The caller checked budget BEFORE checking quorum, so tokens were consumed for checks that failed.

**Fix (v3.7):** Separate "check" from "consume":
```c
// New API
bool utlp_immune_has_budget(void);     // Check only - no side effects
bool utlp_immune_consume_token(void);  // Consume only - call when firing

// Updated call site in evaluate_entrainment_response()
if (!utlp_immune_has_budget()) return;  // Check only
if (!utlp_trust_has_quorum(...)) return; // Check only - NO TOKEN CONSUMED
utlp_immune_consume_token();             // Consume ONLY when actually firing
send_chirp_immediate();
```

**Biological Analogy:**
You don't send T-cells to investigate whether you should deploy T-cells. The immune system
checks for threats (quorum sensing, antigen recognition) BEFORE committing metabolic resources
(T-cell activation). Token consumption = T-cell deployment = only after all checks pass.

**Purple Team Audit (PT-12):**
- ✅ No race conditions (single-threaded execution model)
- ✅ No token leak paths (consume only immediately before fire)
- ✅ Biological model faithful (check before commit)
- ⚠️ Design limitation: 2-node quorum impossible (requires 2+ agreeing peers)

**Files Modified:**
- `utlp_immune.h`: Added `utlp_immune_has_budget()` and `utlp_immune_consume_token()` APIs
- `utlp_immune.c`: Implemented separate check/consume functions
- `utlp.c`: Updated `evaluate_entrainment_response()` to use new pattern (lines 2337-2381)

**Expected Behavior (After Fix):**
1. Device A discovers peer B3:08 sending genesis chirps
2. A calls `has_budget()` → true (5 tokens, no consumption)
3. A calls `has_quorum()` → false (only 1 peer, need 2+)
4. A returns WITHOUT consuming token
5. Token budget preserved for actual entrainment needs
6. **IMMUNE BUDGET INTACT** - no premature anergy

### Critical Architectural Fixes (v3.2 - January 2026)

**Servo State Race Condition Fix (PT-8):**

The servo PLL runs from two contexts that can race:
1. **Main task**: `servo_apply_offset()` called from beacon handler
2. **Timer callback**: `servo_tick()` called from 10Hz engine timer (high priority)

Without protection, torn reads/writes of 64-bit fields could occur. All `g_servo`
accesses are now protected by `g_servo_spinlock`.

**Dual-Offset Architecture (Intentional Design):**

The system maintains **two separate offsets** that serve different purposes:

| Offset | Location | Update Frequency | Purpose |
|--------|----------|------------------|---------|
| HAL offset | `g_time_offset_us` | Every 10Hz tick during slewing | Smooth interpolation |
| Phase engine offset | `s_state.epoch_offset_us` | Epoch events only | Stable atomic time for SMSP |

This is NOT an SSOT violation - it's intentional:
- **HAL offset**: Updated every 100ms during slewing for smooth clock correction
- **Phase engine offset**: Only updated at discrete events (epoch jumps, genesis, convergence)
- **SMSP reads from phase engine**: Sees stable values, not jittery interpolation

**BUG FIX (January 2026):** Previously, phase engine offset was updated every 10Hz tick
during slewing, causing "firefly" LED chaos (offset values oscillating wildly in logs).
Fix: Phase engine only receives updates at:
1. Epoch jumps (whole-cycle corrections)
2. Genesis jumps (bootstrap)
3. Slew convergence (final stable value)

During active slewing, HAL offset is updated but phase engine stays stable.

### Critical Architectural Fixes (v3.3 - January 2026)

**Seniority Bankruptcy Stratum Reset (PT-9):**

Per S2 Claim 137 (Session Bankruptcy), when a peer reboots (detected via session salt change),
ALL trust metrics must be wiped including stratum. Previously, stratum was correctly reset to
255 but then immediately overwritten by the beacon's claimed stratum value.

**Bug Evidence:**
```
*** SENIORITY BANKRUPTCY *** Peer F5:C8 salt 0xBFF0->0x9248 (REBOOT DETECTED)
Peer F5:C8 reborn (arbor=0, health=0, rssi=-75, salt=0x9248)
[F5:C8] Health:[W  0/P  0/B  0] Agg:  0 | Strat: 1 | Int:6
                                                 ↑
                                    Should be 255, not 1!
```

**Fix:** Removed errant `p->stratum_claim = stratum;` line in bankruptcy handler.
Bankrupted peers now correctly show `Strat: 255` until they re-earn trust.

**Two-Octet Peer Naming:**

Changed all peer MAC logging from single-octet (`%02X`) to two-octet (`%02X:%02X`) format
for clarity when debugging 3+ device swarms. Before: `[08]`, After: `[04:08]`.

Updated 16 log locations across `utlp.c` and `utlp_trust.c`.

### Critical Architectural Fixes (v3.1)

Fixes that address fundamental timing architecture bugs:

| Fix | Problem | Solution | Impact |
|-----|---------|----------|--------|
| **Epoch vs Phase Separation** | Servo tried to slew 7+ second boot offsets | Split error into epoch (jump) + phase (slew) | Instant epoch alignment, gentle phase slew |
| **Derivative Noise Explosion** | 2nd derivative amplified jitter to +169M ppb | Disabled acceleration calculation | Stable drift tracking, no garbage values |
| **Physical Drift Clamp** | Measurement errors produced impossible drift | Clamp to ±500 ppm (UTLP_MAX_PHYSICAL_DRIFT_PPB) | Genesis scoring ignores bad measurements |

**Epoch vs Phase Separation:**
When devices boot at different times, the total clock offset can be millions of microseconds
(e.g., 7 seconds = 7,000,000 µs). The servo cannot slew such massive offsets - it would take
hours. The fix splits the error:
- **Epoch error** (whole cycles, multiples of 1,000,000 µs) → HARD JUMP immediately
- **Phase error** (within one cycle, ±500,000 µs max) → GENTLE SLEW for spectral purity

**Derivative Noise Explosion:**
The seismic chirp's 2nd derivative was intended to detect jitter acceleration.
In practice, the Coexistence Arbiter jitter (40-60µs on Dual Stack) dominated the signal,
producing garbage values like +169,500,000 ppb (169x faster than real time). This was
misinterpreted as massive clock acceleration, causing oscillation loops. Solution: Set
`accel_ppb_s = 0.0` and use only the 1st derivative (jitter rate). Note: Crystal drift
is measured via inter-exchange analysis over seconds, not within-chirp analysis.

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

## Purple Team Security (Claim 255)

UTLP implements **Rolling Splice-Site Security** (Bio-TOTP), where the encryption
key changes every second based on the packet's own timestamp. This section documents
the Purple Team audit findings and architectural decisions.

### Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Claim 255: Bio-TOTP Security                │
├─────────────────────────────────────────────────────────────┤
│  CLEARTEXT EXON (24 bytes)                                  │
│    - SequenceID, Timestamp, Session_Salt, Stratum, Version  │
│    - Provides nonce components for encryption               │
├─────────────────────────────────────────────────────────────┤
│  ENCRYPTED INTRON (8 bytes) - AES-128-CTR                   │
│    - TX_Power, Battery, Drift, Opcode, Payload              │
│    - Key = SHA256(Swarm_DNA || Quantize_1s(Timestamp))[0:16]│
│    - Plausibility validation replaces auth tag              │
└─────────────────────────────────────────────────────────────┘
```

### Purple Team Directives (Implemented)

| Directive | Title | Status | Description |
|-----------|-------|--------|-------------|
| **PT-1** | Stateless AES-CTR | ✅ | Reset nc_off=0, fresh nonce/stream each packet |
| **PT-2** | RISC-V Torn Reads | ✅ | portENTER_CRITICAL() for all 64-bit operations |
| **PT-3** | Infinite Slew | N/A | Architecture uses continuous P-servo, not time-boxed |
| **PT-4** | Herd Immunity | ✅ | Public/Private nodes execute identical code paths |
| **PT-5** | Strict Plausibility | ✅ | TX_Power ±40dBm, Drift ±2000ppm, Heartbeat validation |
| **PT-6** | Session Continuity | ✅ | Session_Salt change triggers Seniority Bankruptcy (reboot detection) |
| **PT-7** | ILC Integration | ✅ | Phase timer ISR latency learning with spinlock protection |

### Herd Immunity (PT-4)

**Critical Design Decision:** Public Mode (Zero Key) executes the exact same
crypto code path as Private Mode. We do NOT optimize by skipping SHA256 or AES.

**Why This Matters:**
- CPU power profile identical (no side-channel leakage)
- Timing signature identical (no timing attacks)
- Traffic analysis cannot distinguish encrypted from "cleartext"
- Public nodes provide "cover" for private nodes in mixed swarms

```c
// BAD - Creates timing side-channel!
if (is_zero_key(dna)) {
    memcpy(output, input, 8);  // Skip crypto
    return;
}

// GOOD - Run SHA256 + AES even for Zero Key
key = sha256(dna || time);  // Even if dna is all zeros
aes_ctr(key, nonce, input, output);
```

### Semantic Plausibility Validation (PT-5)

Without an authentication tag (AES-CTR mode), we use semantic validation to
detect wrong-key decryptions. Random garbage is unlikely to pass all checks:

| Check | Range | Probability |
|-------|-------|-------------|
| TX Power | -40 to +21 dBm | 62/256 ≈ 24% |
| Opcode | 0x00-0x04 or 0x80+ | 133/256 ≈ 52% |
| Drift PPM | ±2000 | 4000/65536 ≈ 6% |
| CPU Load (Heartbeat) | 0-100% | 101/256 ≈ 39% |
| Role (Heartbeat) | 0-3 | 4/256 ≈ 1.5% |

**Combined false positive rate:** ~0.00004% per packet (acceptable for swarm sync).

### Files Implementing Security

| File | Purpose |
|------|---------|
| `utlp_security.h` | Packet structures (Exon/Intron), plausibility constants |
| `utlp_security.c` | Key derivation, sliding window decryption, validation |
| `utlp_hal_security.h` | HAL crypto abstraction, Herd Immunity documentation |
| `utlp_hal_security.c` | mbedtls implementation, stateless AES-CTR |

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

## Proprioception (Hardware-Assisted Latency Learning)

**"The Body Learns Its Own Timing"**

Hardware-scheduled TX via `esp_ieee802154_transmit_at()` requires the application
to provide a future timestamp. The optimal lead time depends on platform-specific
factors (radio warmup, ISR latency, SPI buffer time, RTOS jitter). Rather than
hardcode these values, we **learn** them by observing actual vs. target timing.

### Learning Loop

```
┌─────────────────────────────────────────────────────────────┐
│              Proprioception Feedback Loop                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. SCHEDULE  ─────┐                                         │
│                    │  adjusted_time = tx_time + latency      │
│                    ▼                                         │
│  2. EMBED     target = adjusted_time                         │
│                    │                                         │
│                    ▼                                         │
│  3. TRANSMIT  esp_ieee802154_transmit_at(adjusted_time)      │
│                    │                                         │
│                    ▼                                         │
│  4. FEEDBACK  tx_done_callback() reads actual timestamp      │
│                    │                                         │
│                    ▼                                         │
│  5. LEARN     error = actual - target                        │
│               ├─ LATE (error > 0):  latency += error/16      │
│               ├─ ON-TIME:           no change                │
│               └─ EARLY (error < -10): latency -= 10µs        │
│                    │                                         │
│                    └─────────────► (loop)                    │
└─────────────────────────────────────────────────────────────┘
```

### Convergence Behavior

| Phase | Latency | Duration | Description |
|-------|---------|----------|-------------|
| **Startup** | 50ms | 0 TX | Conservative initial value |
| **Fast Learning** | 50ms → 1ms | ~100 TX | Large errors corrected quickly |
| **Fine Tuning** | 1ms → 200µs | ~500 TX | Slow decay finds minimum |
| **Steady State** | ~100-500µs | ∞ | Platform-optimal buffer |

### Safety Patches

**Death Spiral Prevention:** If `esp_ieee802154_transmit_at()` fails (returns
ESP_ERR_INVALID_STATE), we're already past the target time. Without intervention,
the learning loop never runs (no callback), latency stays too small, next TX also
fails → death spiral. The fix: bump latency by 5ms immediately.

**Callback Math Safety:** The hardware timestamp is 32-bit, our target is 64-bit.
To handle rollover correctly, we cast both to 32-bit before subtraction:
```c
// WRONG: int64_t error = actual - target;
// RIGHT:
int32_t error = (int32_t)(frame_info->timestamp - (uint32_t)target);
```

### Configuration (utlp_config.h)

| Constant | Default | Description |
|----------|---------|-------------|
| `UTLP_LATENCY_INITIAL_US` | 50000 | Conservative startup (50ms) |
| `UTLP_LATENCY_MIN_US` | 100 | Floor to prevent instability |
| `UTLP_LATENCY_MAX_US` | 100000 | Ceiling sanity check (100ms) |
| `UTLP_LATENCY_LEARN_DIVISOR` | 16 | Late error learning rate (6%/cycle) |
| `UTLP_LATENCY_DECAY_US` | 10 | Early decay rate (10µs/cycle) |
| `UTLP_LATENCY_DEADZONE_US` | 10 | On-time threshold (±10µs) |
| `UTLP_LATENCY_DEATH_SPIRAL_BUMP_US` | 5000 | Emergency bump (5ms) |

### Files

| File | Purpose |
|------|---------|
| `utlp_config.h` | Proprioception tuning constants |
| `utlp_hal_esp32c6_154.c` | Learning loop implementation (tx_done_callback) |

## Interrupt Latency Compensation (ILC) ✅ IMPLEMENTED

**"The Body Learns Its Own ISR Timing"**

While Proprioception learns radio TX latency, ILC learns interrupt latency for the
phase timer ISR. Dual Stack devices (WiFi+BLE coexistence) experience 40-60µs
interrupt delay compared to ~5µs on Single Stack devices. Without ILC, these
devices would show visible phase offset despite running identical firmware.

### The Problem: The "Software Gap"

**Ideal Physics:** Timer hits `0` → LED toggles.

**Reality (ESP32):** Timer hits `0` → Interrupt Controller → Arbiter → Context
Switch → ISR Entry → GPIO Instruction → LED toggles.

| Stack Type | Interrupt Latency | Root Cause |
|------------|-------------------|------------|
| **Single Stack** | ~5µs | Minimal ISR path |
| **Dual Stack** | ~40-60µs | WiFi/BLE Coexistence Arbiter |

This 35-55µs difference creates a visible phase offset between Single Stack and
Dual Stack devices running the same firmware.

### The Solution: Pre-Fire Proprioception

Just like TX Latency Learning, we **learn** the ISR latency and **pre-fire** the
timer to compensate:

```
BEFORE (naive):     Timer fires at T → ISR runs at T+40µs → LED toggles LATE
AFTER (ILC):        Timer fires at T-40µs → ISR runs at T → LED toggles ON-TIME
```

### Learning Loop

```
┌─────────────────────────────────────────────────────────────┐
│              ILC Feedback Loop (Phase Timer ISR)            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. MEASURE  ─────┐                                          │
│                   │  actual_time = MCPWM event timestamp     │
│                   │  expected_time = g_isr_target_time_us    │
│                   ▼                                          │
│  2. CALCULATE error_us = actual - expected                   │
│                   │                                          │
│                   ▼                                          │
│  3. LEARN    ├─ LATE (error > +5µs):  latency += error/16   │
│              ├─ ON-TIME (±5µs):       no change             │
│              └─ EARLY (error < -5µs): latency -= 2µs        │
│                   │                                          │
│                   ▼                                          │
│  4. COMPENSATE   next_alarm = target - learned_latency       │
│                   │                                          │
│                   └─────────────► (loop)                     │
└─────────────────────────────────────────────────────────────┘
```

### Expected Convergence

| Stack Type | Initial | Converged | Cycles |
|------------|---------|-----------|--------|
| Single Stack | 1ms | ~10µs | ~100 |
| Dual Stack | 1ms | ~50µs | ~100 |

### Configuration (utlp_config.h)

| Constant | Default | Description |
|----------|---------|-------------|
| `UTLP_ILC_INITIAL_US` | 1000 | Conservative startup (1ms) |
| `UTLP_ILC_MIN_US` | 5 | Floor to prevent instability |
| `UTLP_ILC_MAX_US` | 100000 | Ceiling sanity check (100ms) |
| `UTLP_ILC_LEARN_DIVISOR` | 16 | ~6% error correction per cycle |
| `UTLP_ILC_DEADZONE_US` | 5 | ±5µs is "on-time" |
| `UTLP_ILC_DECAY_US` | 2 | Early decay rate (2µs/cycle) |

### Files

| File | Purpose |
|------|---------|
| `utlp_config.h` | ILC tuning constants |
| `utlp_phase.c` | Learning loop in `phase_timer_empty_isr()` |
| `utlp_phase.h` | `utlp_phase_get_isr_latency_us()` diagnostic API |

### Why This Is Better Than Hardware Output Compare

While mapping LED directly to MCPWM comparator output pin is "perfect" (±50ns),
it requires specific GPIO assignment. ILC works on **any GPIO** and solves the
problem mathematically, effectively learning the weight of the OS stack.

## Spectral Retina (Multi-Transport RSSI Telemetry)

**"The Swarm Sees in Radio Color"**

When a peer is visible on both WiFi (ESP-NOW) and 802.15.4, comparing RSSI values
reveals environmental RF characteristics — the "radio color" of the propagation
path. This enables future confidence weighting based on environmental clutter.

### Why RSSI Delta Matters

WiFi (2.4GHz, 20MHz bandwidth) and 802.15.4 (2.4GHz, 2MHz bandwidth) experience
different multipath fading profiles despite sharing the same band:

| Environment | WiFi RSSI | 802.15.4 RSSI | Delta | Classification |
|-------------|-----------|---------------|-------|----------------|
| Open area   | -45 dBm   | -48 dBm       | 3 dB  | **CLEAR** |
| Office      | -52 dBm   | -56 dBm       | 4 dB  | **CLEAR** |
| Warehouse   | -58 dBm   | -72 dBm       | 14 dB | **CLUTTERED** |
| Dense metal | -65 dBm   | -88 dBm       | 23 dB | **CLUTTERED** |

### Implementation

The Metabolic Ledger now stores per-arbor RSSI with timestamps:

```c
typedef struct {
    /* ... existing fields ... */

    /* Spectral Retina: Per-arbor RSSI tracking */
    int8_t   last_rssi[UTLP_MAX_ARBORS];       /* Per-arbor RSSI (dBm) */
    uint32_t rssi_timestamp_ms[UTLP_MAX_ARBORS]; /* When RSSI was recorded */
} utlp_peer_ledger_t;
```

When a beacon arrives with RSSI, the observation recorder logs spectral coherence:

```
I (12345) RETINA: Peer 5c | WiFi:-45 15.4:-52 | Delta: 7 dB | CLEAR
I (12456) RETINA: Peer 5c | WiFi:-45 15.4:-68 | Delta: 23 dB | CLUTTERED
```

### Configuration (utlp_config.h)

| Constant | Default | Description |
|----------|---------|-------------|
| `UTLP_RSSI_STALE_MS` | 5000 | RSSI readings older than this are ignored |
| `UTLP_RSSI_DELTA_CLEAR` | 10 | Delta ≤ this = CLEAR environment |
| `UTLP_RSSI_INVALID` | -128 | Sentinel for unavailable RSSI |

### Future Applications

- **Polychromatic Confidence Weighting:** Timing from cluttered environments gets
  lower weight in consensus calculation
- **Dynamic Arbor Selection:** Prefer transport with lower multipath distortion
- **Environmental Mapping:** Swarm collectively maps RF characteristics of space

### Files

| File | Purpose |
|------|---------|
| `utlp_trust.h` | Per-arbor RSSI fields in peer ledger |
| `utlp_trust.c` | `utlp_trust_log_spectral_coherence()` implementation |
| `utlp_config.h` | Spectral Retina tuning constants |

### Related Prior Art

- **Claim 253:** Polychromatic Stratum Asymmetry (per-transport trust)
- **Phase 9:** Blood-Brain Barrier (per-arbor health scores)
- **Phase 11:** Spectral Retina (multi-transport RSSI comparison)

## Session Continuity Enforcement (Purple Team PT-6)

**"The Ghost has died. Long live the Ghost."**

Session Continuity Enforcement provides instant reboot detection using the `Session_Salt`
field (beacon bytes 11-12). When a peer's salt changes but MAC remains the same, the peer
has rebooted — triggering **Seniority Bankruptcy**: complete wipe of all accumulated trust.

### The Problem: Fresh Boot Genesis Attack

A rebooted peer retains its MAC address but starts fresh with no timing history. Without
salt tracking, existing detection methods have vulnerabilities:

| Detection Method | Trigger | Speed | Limitation |
|------------------|---------|-------|------------|
| **Genesis Pulse** | Interval < 2000ms | 2+ beacons | Needs timing history |
| **Time Regression** | Atomic time backwards > 10s | Slow | Large threshold |
| **Session Salt** (PT-6) | Salt ≠ last_salt | **FIRST beacon** | **Definitive** |

Attack scenario without PT-6:
1. High-trust peer (health=150, seniority=1000) crashes and reboots
2. Sends first beacon claiming Genesis authority (stratum 1)
3. Old way: Swarm briefly accepts claim before detecting interval anomaly
4. New way: Salt change detected immediately → Trust wiped → Genesis rejected

### Implementation

**Beacon Format Extended (11 → 13 bytes):**
```
[Stratum(1), Burst(1), Score(1), Timestamp(8), Session_Salt(2)]
                                                     ↑
                                            PT-6: Boot Instance ID
```

**Seniority Bankruptcy Wipe:**
```c
if (peer->last_session_salt != 0 && peer->last_session_salt != session_salt) {
    /* WIPE: Reset ALL trust metrics */
    peer->first_seen_ms = now_ms;        /* Tenure starts over */
    peer->health_score[*] = 0;           /* Zero trust, not STARTUP */
    peer->stratum_claim = 255;           /* Worst possible stratum */
    peer->interactions = 1;              /* First observation in new life */
    peer->consecutive_hits = 0;
    peer->last_tx_time_us = 0;
}
peer->last_session_salt = session_salt;
```

**Why Zero Health, Not STARTUP:**
- STARTUP (50) is "probationary" — benefit of the doubt for new peers
- A rebooted peer could have been compromised or attacked
- Zero trust forces complete re-validation before ANY influence
- Genesis Guard rejects peers with health < 100

### Expected Log Output

```
W (12345) TRUST: *** SENIORITY BANKRUPTCY *** Peer 5C salt 0x1234->0xABCD (REBOOT DETECTED)
I (12346) TRUST: Peer 5C reborn (arbor=1, health=0, rssi=-52, salt=0xABCD)
```

### Packet Structure

**Legacy 13-byte format has been replaced with 32-byte wire packet.**

| Constant | Value | Description |
|----------|-------|-------------|
| `UTLP_PACKET_SIZE` | 32 | Fixed wire packet size |
| `UTLP_EXON_SIZE` | 24 | Cleartext header |
| `UTLP_INTRON_SIZE` | 8 | AES-128-CTR encrypted |

Session salt is now in the Exon at offset 20 (`exon.session_salt`).

See `utlp_security.h` for complete `utlp_wire_packet_t` structure.

### Defense in Depth

Session Continuity provides the fastest and most definitive reboot detection:

1. **Fastest:** Detectable on FIRST beacon after reboot (no history needed)
2. **Definitive:** Salt change is absolute proof of reboot (random 16-bit value)
3. **Complementary:** Works alongside Genesis Pulse and Time Regression
4. **No false positives:** Salt only changes on actual device reboot

### Files

| File | Purpose |
|------|---------|
| `utlp.c` | Beacon TX/RX with session_salt |
| `utlp_trust.h` | `last_session_salt` field in peer ledger |
| `utlp_trust.c` | Seniority Bankruptcy wipe logic |
| `utlp_security.c` | `utlp_security_get_session_salt()` API |

### Related Prior Art

- **Purple Team PT-1 through PT-5:** Other security hardening fixes
- **Claim 255:** Rolling Splice-Site Security (Bio-TOTP uses session_salt for nonce)
- **Phase 9:** Blood-Brain Barrier (per-arbor trust separation)

## Seismic Chirp (3-Burst Beacon Pattern)

Every beacon transmission is a **seismic chirp**: 3 packets spaced 2ms apart,
all carrying the **same timestamp** (the "chirp epoch"). The 2ms spacing is
the **known reference signal** — like a seismic sweep with known frequency.

**CRITICAL INSIGHT: This Measures JITTER, Not Crystal Drift**

Timescale analysis proves why:
- Crystal drift at 40ppm over 6ms chirp span = **0.24µs** (negligible)
- Stack jitter (ISR latency, WiFi arbitration) = **10-100µs** (dominates!)
- The crystal IS the stable reference ("D" in control theory)
- Drift characterization requires **SECONDS** of observation, not milliseconds

The 3-burst chirp filters software/hardware jitter to extract a cleaner offset.
Crystal drift is measured separately via inter-exchange analysis (offsets
compared over 10+ seconds).

**The Principle:**
- Sender captures timestamp once, transmits it in all 3 bursts
- Bursts arrive at receiver 0ms, 2ms, 4ms after first (expected)
- Any deviation from 2ms spacing = **receiver jitter** (not drift!)

**The Derivative Stack:**

| Burst | RX Time | Measures | Use |
|-------|---------|----------|-----|
| Burst 0 | rx₀ | Offset | Control (servo) |
| Burst 1 | rx₁ = rx₀ + 2ms ± jitter | Jitter rate | Control (servo) |
| Burst 2 | rx₂ = rx₀ + 4ms ± jitter | Jitter accel | **Logged only** |

**Observation vs. Control (Burst 2):**
The 2nd derivative ("jitter acceleration") amplifies measurement noise into
values like +169M ppb ("Derivative Noise Explosion"). It is **NOT used for
servo control**. However, we still CALCULATE and LOG it for:
- Environmental fingerprinting (WiFi congestion, thermal cycles)
- Hardware characterization (different devices = different jitter profiles)
- Research data for future algorithm improvements
- Anomaly detection (sudden change in jitter pattern = something changed)

**Why same timestamp?** The chirp is a known signal (2ms spacing). Fresh
timestamps would mix sender and receiver jitter — same timestamp isolates
receiver jitter against the known reference.

See: `UTLP_Technical_Supplement_S1.md` Section 1.4

## Packet Structure (32 Bytes Fixed)

PHYRFLY uses a fixed 32-byte wire packet geometry for all beacons (Claim 255):

```
┌─────────────────────────────────────────────────────────────┐
│  CLEARTEXT EXON (24 bytes) - Wire-visible                   │
├─────────────────────────────────────────────────────────────┤
│  [0-3]   SequenceID          (uint32_t) Anti-replay counter │
│  [4-11]  UTLP_Timestamp_US   (uint64_t) Chirp epoch         │
│  [12-19] NTP_Timestamp_UTC   (uint64_t) Wall-clock (stealth)│
│  [20-21] Session_Salt        (uint16_t) PT-6 boot instance  │
│  [22]    Stratum             (uint8_t)  1=Genesis, 2+=Relay │
│  [23]    Protocol_Version    (uint8_t)  0x01 = PHYRFLY v1   │
├─────────────────────────────────────────────────────────────┤
│  ENCRYPTED INTRON (8 bytes) - AES-128-CTR via Bio-TOTP      │
├─────────────────────────────────────────────────────────────┤
│  [24]    TX_Power_dBm        (int8_t)   Physics telemetry   │
│  [25]    Battery_Level       (uint8_t)  0-255 scaled        │
│  [26-27] Drift_PPM           (int16_t)  Clock drift         │
│  [28]    Opcode              (uint8_t)  0x00=Heartbeat      │
│  [29-31] Payload[3]          (uint8_t)  Multiplexed data    │
└─────────────────────────────────────────────────────────────┘
```

### Intron Multiplexing (Opcode 0x00 Heartbeat)

When opcode is `UTLP_CMD_NONE` (0x00), the 3-byte payload carries:
- `payload[0]` = CPU_Load (0-100%)
- `payload[1]` = Role (0=GENESIS, 1=SERVER, 2=CLIENT, 3=OBSERVER)
- `payload[2]` = Burst index (0, 1, or 2 for seismic chirp)

### Why Fixed Geometry?

1. **Deterministic Timing** - Same TX duration, same airtime budget
2. **Traffic Analysis Resistance** - All packets look identical (Herd Immunity)
3. **Hardware Optimization** - DMA can use fixed buffer sizes
4. **Forward Compatibility** - Version field enables future evolution

### Encryption Details

**Key Derivation (Bio-TOTP):**
```
quantized_sec = UTLP_Timestamp_US / 1,000,000  (floor to second)
hash_input = Swarm_DNA || quantized_sec        (24 bytes)
Key = SHA256(hash_input)[0:16]                 (first 128 bits)
```

**Sliding Window Decryption:** Receivers try keys for T-1, T, T+1 seconds
to handle clock jitter. Semantic plausibility validation replaces auth tag.

**Critical:** All 3 bursts in a seismic chirp carry the **same** timestamp
(captured once at chirp start). The 2ms burst spacing is the **known reference**.
Receiver compares expected vs. observed spacing to detect clock drift.

See `utlp_security.h` for complete `utlp_wire_packet_t` structure definition.

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
| `utlp_trust.h/c` | Metabolic Ledger (Hebbian trust, per-arbor stratum helpers, Spectral Retina) |
| `utlp_immune.h/c` | Immune Checkpoint (token bucket, anergy) |
| `utlp_transport.h/c` | **Multi-Arbor Transport Manager** (ESP-NOW + 802.15.4) |
| `utlp_arbor.h/c` | Per-transport selective dormancy API |
| `utlp_loom.h/c` | **The Loom** - Emergent Time Lord + Polychromatic Stratum (Claim 253) |
| `utlp_phase.h/c` | **HPLAC** - Hardware Phase Locked Atomic Coherency (MCPWM + ILC) |
| `utlp_security.h/c` | **Claim 255** - 32-byte packet geometry, Bio-TOTP key derivation, plausibility validation |
| `utlp_hal_security.h/c` | **Security HAL** - mbedtls AES-CTR, SHA-256, stateless crypto (PT-1) |
| `utlp_hal.h` | HAL interface contract (imports SSOT from utlp_config.h) |
| `utlp_hal_esp32.c` | ESP32 HAL implementation (ESP-NOW, MCPWM) |
| `utlp_hal_esp32c6_154.c` | **802.15.4 HAL** - Hardware-scheduled TX, Proprioception learning |
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
- `docs/UTLP_Technical_Supplement_S2.md` - Biological Governance (250+ claims including Claim 253)
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

### Claim 253: Polychromatic Stratum Asymmetry

Multi-transport devices (e.g., ESP32-C6 with WiFi + 802.15.4) can maintain
**independent stratum levels per interface**. A bridge node following a Time Lord
on WiFi (Stratum 2) can simultaneously act as Genesis Authority (Stratum 1) on
802.15.4 if that spectrum is silent.

**Key Insight:** Propagates "Genesis Truth" into silent spectral bands without
manual "Bridge Mode" flags.

```
┌─────────────────────────────────────────────────────────────┐
│  Device with WiFi + 802.15.4                                │
│                                                              │
│  ┌───────────────┐         ┌───────────────┐                │
│  │    WiFi       │         │   802.15.4    │                │
│  │  Stratum: 2   │         │  Stratum: 1   │                │
│  │  (following)  │         │   (genesis)   │                │
│  └───────────────┘         └───────────────┘                │
│         │                         │                          │
│         ▼                         ▼                          │
│  ┌──────────────────────────────────────────────┐           │
│  │        Primary Time Source (WiFi)            │           │
│  │  Split-Horizon: Only primary updates clock   │           │
│  └──────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

**Architecture:**

| Component | Description |
|-----------|-------------|
| **Per-Arbor Stratum** | `stratum[UTLP_ARBOR_COUNT]` array replaces single stratum |
| **Primary Time Source** | Explicit field tracks which arbor drives the clock |
| **Split-Horizon Protection** | Beacons from secondary arbors update Loom, not offset |
| **Auto-Promotion** | Silent secondary promoted to Genesis after 30s |
| **Auto-Demotion** | Secondary demotes if authority appears on that band |

**API:**

```c
void utlp_loom_polychromatic_update(void);       // Called from loom_tick()
uint8_t utlp_get_stratum_for_arbor(arbor_id);    // Per-arbor stratum query
void utlp_set_stratum_for_arbor(arbor_id, s);    // Per-arbor stratum set
utlp_arbor_id_t utlp_get_primary_time_source(void); // Which arbor is primary
```

**Helper Functions (utlp_trust.c):**

```c
// Count neighbors with stratum <= threshold on specific arbor
uint8_t utlp_trust_count_neighbors_by_stratum_arbor(arbor_id, max_stratum);

// Get lowest (best) stratum seen on specific arbor
uint8_t utlp_trust_get_best_stratum_arbor(arbor_id);
```

**Prior Art:** Claim 253 in Technical Supplement S2

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
