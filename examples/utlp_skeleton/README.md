# UTLP Genesis Node Skeleton

**Universal Time Lord Protocol** - A minimal implementation demonstrating
connectionless distributed time synchronization.

> *"Time is born of one."* — UTLP Specification, Section 7

## Quick Start

```bash
# Build and flash (both devices)
pio run -e utlp_skeleton -t upload

# Monitor serial output
pio device monitor
```

**Important:** Reset both devices simultaneously for best results.
See [Known Limitations](#known-limitations) below.

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
    NO  → Continue as Genesis (stratum 1)
```

**Why this matters:**
- Single device works standalone (no peer required)
- Late-joining nodes adopt from existing swarm
- Simple, robust, zero negotiation

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
│              Application Layer (utlp_skeleton.c)            │
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
│    Actuator: set_actuator_phase() [GPIO15 LED]              │
├─────────────────────────────────────────────────────────────┤
│        ESP32-C6 Implementation (utlp_hal_esp32c6.c)         │
│                                                              │
│   ┌─────────┬─────────┬─────────┬─────────┐                 │
│   │ ESP-NOW │  MCPWM  │ Timer   │Semaphore│                 │
│   │ (radio) │(GPIO15) │ (time)  │  (RX)   │                 │
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

**Why 2ms spacing?** Tight grouping (6ms total chirp) represents a single
"moment" in time, minimizing drift smearing within the measurement window.

See: `UTLP_Technical_Supplement_S1.md` Section 1.4

## Beacon Protocol

10-byte seismic chirp burst (one-way, no reply needed):

```
┌──────────┬─────────────────────────────────────────────┐
│ Byte 0   │ Stratum (1 = Genesis)                       │
├──────────┼─────────────────────────────────────────────┤
│ Byte 1   │ Burst index (0, 1, or 2)                    │
├──────────┼─────────────────────────────────────────────┤
│ Bytes 2-9│ Chirp epoch (SAME timestamp in all 3 bursts)│
└──────────┴─────────────────────────────────────────────┘
```

**Critical:** All 3 bursts carry the **same** timestamp (captured once at chirp start).
The 2ms burst spacing is the **known reference**. Receiver compares expected vs.
observed spacing to detect clock drift.

**Receiver behavior:** Only burst 0 is used for synchronization (offset).
Bursts 1 and 2 enable future drift/stability extraction via polynomial fitting.

**Sync Math (one-way timing):**
```
offset = remote_tx_time - local_rx_time
atomic_time = local_time + offset
```

For short-range ESP-NOW (same room), flight time ≈ 0.

## Time-Indexed LED Control

The LED state is **calculated** from atomic time, not **toggled** by delays:

```c
uint64_t cycle_pos = atomic_time % BLINK_PERIOD_US;  // 1 second
bool led_on = (cycle_pos < BLINK_PERIOD_US / 2);     // 50% duty
```

**Why this is drift-proof:** Every node with the same atomic_time
will calculate the same LED state. No drift accumulation.

## Drift Analysis (Polynomial Fitting)

When a Follower receives all 3 bursts of a seismic chirp, it performs
polynomial fitting to extract drift metrics:

```
offset(t) = a + b*t + c*t²

Where:
  a = instantaneous offset (microseconds)
  b = drift rate (parts-per-billion, PPB)
  c = drift acceleration (PPB/second, thermal instability)
```

**How drift is calculated:**

The 3 bursts should arrive exactly 2ms apart. Any deviation from 2ms
spacing indicates local clock drift:

```
Expected:  rx[0], rx[0]+2000us, rx[0]+4000us
Actual:    rx[0], rx[1], rx[2]
Delta:     0, (rx[1]-rx[0])-2000, (rx[2]-rx[1])-2000

Drift (PPB) = delta_01 / 0.002s * 1000
Accel (PPB/s) = (delta_12 - delta_01) / 0.002s * 1000
```

**Genesis-Pulse Logging:**

| Uptime | Log Interval | Purpose |
|--------|--------------|---------|
| 0-10s | 1 second | Fast feedback during convergence |
| 10s+ | 30 seconds | Steady-state monitoring |

**Example drift stats output:**

```
I (XXX) UTLP: ════════════════════════════════════════════════════════
I (XXX) UTLP: [DRIFT STATS] Chirps analyzed: 5 (uptime: 3s)
I (XXX) UTLP:   LAST: offset=+1234us | drift=+500ppb | accel=+10.5ppb/s
I (XXX) UTLP:   AVG:  offset=+1200us | drift=+480ppb | accel=+8.2ppb/s
I (XXX) UTLP:   RANGE: drift=[+450..+520]ppb
I (XXX) UTLP: ════════════════════════════════════════════════════════
```

**Interpretation:**
- **offset**: How far local clock is from master (applies to all bursts)
- **drift**: Local clock speed error (+500 PPB = running 0.0005% fast)
- **accel**: Drift rate changing (thermal instability indicator)
- **Typical crystal**: ±20 ppm = ±20,000 ppb

## Expected Serial Output

```
I (552) UTLP: ========================================
I (562) UTLP: UTLP GENESIS NODE
I (562) UTLP: "Time is born of one."
I (572) UTLP: ========================================
I (572) UTLP: MAC: 10:51:DB:1C:B3:08
I (582) UTLP: Stratum: 1 (GENESIS)
I (582) UTLP: Beacon: Seismic Chirp (3-burst @ 2ms spacing)
I (592) UTLP: Interval: Genesis Pulse (100ms→500ms→1s→10s→60s)
I (602) UTLP: Blink period: 1000 ms
I (602) UTLP: Drift Analysis: Enabled (polynomial fit)
I (612) UTLP: Stats Log: 1s (first 10s) → 30s (steady state)
I (612) UTLP: ========================================
I (XXX) UTLP: Beacon interval: 100 ms (uptime 0s)
I (XXX) UTLP: [LED] ON  @ atomic=500000 us (stratum 1)
I (XXX) UTLP: [LED] OFF @ atomic=1000000 us (stratum 1)
I (XXX) UTLP: Beacon interval: 500 ms (uptime 1s)
...
I (XXX) UTLP: SYNCED: stratum=2, offset=+1234 us  ← Adopted from peer
I (XXX) UTLP: ════════════════════════════════════════════════════════
I (XXX) UTLP: [DRIFT STATS] Chirps analyzed: 5 (uptime: 1s)
I (XXX) UTLP:   LAST: offset=+1234us | drift=+500ppb | accel=+10.5ppb/s
I (XXX) UTLP:   AVG:  offset=+1234us | drift=+500ppb | accel=+10.5ppb/s
I (XXX) UTLP:   RANGE: drift=[+500..+500]ppb
I (XXX) UTLP: ════════════════════════════════════════════════════════
```

## Known Limitations

### No Automatic Failover (Matrix-Style Takeover)

This skeleton does **not** implement automatic leader re-election when the
Genesis node goes offline. If you reset the Genesis node (lowest MAC) while
the Follower is still running:

- Follower continues using stale offset
- LEDs will drift out of sync
- **Solution:** Reset both devices together

Future work may add timeout-based re-election where Followers detect
Genesis absence and promote themselves.

### No Stratum Relay

Currently only supports stratum 0 (GPS), 1 (Genesis), and 2 (Follower).
Multi-hop relay (stratum 3+) is not implemented.

## Files

| File | Description |
|------|-------------|
| `utlp_skeleton.c` | Genesis Node application (~290 lines) |
| `utlp_hal.h` | HAL interface contract (~185 lines) |
| `utlp_hal_esp32c6.c` | ESP32-C6 implementation (~400 lines) |
| `README.md` | This documentation |

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
// GPIO15 LED (active LOW on XIAO ESP32-C6)
void utlp_hal_set_actuator_phase(int channel, uint32_t freq_hz,
                                  float phase_deg, float duty_pct);
void utlp_hal_actuator_stop(int channel);
```

## Porting to Other Platforms

1. Create `utlp_hal_<platform>.c` implementing all functions in `utlp_hal.h`
2. Replace ESP-NOW with platform-specific radio (LoRa, BLE, etc.)
3. Replace MCPWM with platform-specific PWM/GPIO
4. Application code (`utlp_skeleton.c`) remains **unchanged**

## Related Documentation

- `docs/UTLP_Specification.md` - Full protocol specification
- `docs/Connectionless_Distributed_Timing_Prior_Art.md` - Research foundation

## Future Work

- **Automatic failover:** Timeout-based re-election when Genesis goes offline
- **Stratum relay:** Multi-hop mesh (stratum 3+)
- **GPS stratum-0:** External time reference integration
- **Drift compensation:** Use tracked drift rate for active clock correction

## License

This example is part of the EMDR Bilateral Stimulation Device project.
- Software: GPL v3
- Hardware: CERN-OHL-S v2
