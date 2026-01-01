# UTLP Executive Summary: The Unkillable Watchdog

**For Hardware Engineers — How to Build It**

---

## What It Is

A distributed timing protocol that maintains phase lock across nodes without:
- A master node (any node can be Genesis)
- Connection state (pure broadcast)
- Central coordination (consensus emerges locally)

**Target Hardware:** ESP32-C6 with ESP-NOW (tested), portable to any MCU with broadcast RF.

---

## The 30-Second Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         UTLP NODE                                   │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 7: APPLICATION                                               │
│    Your app (EMDR therapy, drone swarm, etc.)                       │
│    Reads: atomic_time = local_time + time_offset                    │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 4: TIMING ENGINE (utlp.c)                                    │
│    - Beacon TX/RX (11-byte chirps)                                  │
│    - Genesis election (stratum + atomic time)                       │
│    - Phase alignment (drift correction)                             │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 3: TRUST (utlp_trust.c)                                      │
│    - Metabolic Ledger (12 peer slots)                               │
│    - Health scores (0-255)                                          │
│    - Median consensus                                               │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 2: IMMUNITY (utlp_immune.c)                                  │
│    - Token bucket (5 tokens)                                        │
│    - Anergy state (exhaustion)                                      │
│    - Rate limiting                                                  │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 1: HAL (utlp_hal_esp32.c)                                    │
│    - ESP-NOW broadcast                                              │
│    - 64-bit timer (esp_timer_get_time)                              │
│    - GPIO/PWM actuators                                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Critical Numbers

| Parameter | Value | Why |
|-----------|-------|-----|
| **Beacon size** | 11 bytes | Fits in single ESP-NOW frame |
| **Peer slots** | 12 | Silicon Dunbar's Number |
| **Sync threshold** | 100 health | Minimum to be trusted |
| **Agreement window** | 2 ms | Phase tolerance |
| **Lying threshold** | 100 ms | Beyond = punished hard |
| **Token bucket** | 5 tokens | Entrainment rate limit |
| **Token refill** | 12 seconds | 1 token per 12s |
| **Anergy recovery** | 3 tokens | Exit exhaustion at 3 |

---

## Beacon Format (11 bytes)

```
Byte 0:     Stratum (0=GPS, 1=Genesis, 2=Follower, ...)
Byte 1:     Burst index (0, 1, 2 for seismic chirp)
Byte 2:     Genesis score (0-255, topology metric)
Bytes 3-10: TX timestamp (64-bit, little-endian, microseconds)
```

**Seismic Chirp:** 3 bursts × 2ms spacing = 6ms per beacon. Enables drift extraction via polynomial fit.

---

## Genesis Election (Who Is The Clock?)

```c
// Priority order:
1. Lower stratum wins (GPS < Genesis < Follower)
2. Same stratum: Higher atomic time wins ("First Born")
3. Tie-breaker: Lower MAC address wins (dominance hierarchy)

// Bootstrap behavior:
- Boot as stratum 1 (Genesis)
- If hear better stratum → demote and adopt
- If hear same stratum with elder atomic time → demote
```

---

## Trust Dynamics (The Immune System)

```c
// On receiving a beacon:
deviation = peer_offset - consensus_offset;

if (deviation < 2000us)     health += 2;    // TRUTH
else if (deviation < 100ms) health -= 10;   // DRIFTING  
else                        health -= 50;   // LYING

// Selection: health dominates stratum
score = (health * 10) + (16 - stratum);
// A healthy stratum-2 beats a sick stratum-1
```

---

## Rate Limiting (Cytokine Storm Prevention)

```c
// Before firing entrainment pulse:
if (!utlp_immune_can_defend()) return;  // Budget exhausted
if (!utlp_trust_has_quorum())  return;  // No crowd support

// Both constraints must pass
send_chirp();  // Fire entrainment pulse
```

---

## Time-Indexed Execution (The Magic)

**Wrong way:**
```c
led_on();
delay(500);
led_off();  // Drifts over time
```

**UTLP way:**
```c
uint64_t now = utlp_hal_get_atomic_time_us();
bool should_be_on = (now % 1000000) < 500000;
set_led(should_be_on);  // Recalculated every tick
```

This is **drift-proof** because output state is computed from shared atomic time, not accumulated delays.

---

## Genesis Pulse (Beacon Intervals)

| Uptime | Interval | Phase |
|--------|----------|-------|
| 0-1s | 100ms | Genesis burst |
| 1-5s | 500ms | Fast convergence |
| 5-10s | 1000ms | Settling |
| 10-60s | 10s | Stabilizing |
| 60s+ | 60s | Steady state |

New nodes announce loudly, then quiet down. Late joiners inherit established timing.

---

## Hardware Requirements

| Component | ESP32-C6 Example | Notes |
|-----------|------------------|-------|
| Timer | esp_timer (64-bit) | Microsecond resolution |
| Radio | ESP-NOW | Connectionless broadcast |
| Actuator | GPIO/PWM | Phase-aligned output |
| Memory | ~400 bytes | Static allocation only |

**No malloc. No fragmentation. No surprises.**

---

## Build Checklist

1. ☐ Implement HAL for your platform (see `utlp_hal.h`)
2. ☐ Copy `utlp.c`, `utlp_trust.c`, `utlp_immune.c`
3. ☐ Call `utlp_app_run()` from your main
4. ☐ Use `utlp_hal_get_atomic_time_us()` for all timing
5. ☐ Test two nodes: verify LED blink sync < 2ms

---

## Test Vectors

| Test | Expected Result |
|------|-----------------|
| Single node boot | Stratum 1, beacon @ 100ms initially |
| Two nodes, same boot | Lower MAC stays Genesis |
| Node reset with offset | Elder atomic time wins |
| Byzantine attacker | Drops to health=0, ignored |
| Ledger full | Lowest-health peer evicted |

---

## Quick Reference: Key Functions

```c
// Initialization
utlp_trust_init();
utlp_immune_init();
utlp_hal_init();

// Get synchronized time
uint64_t now = utlp_hal_get_atomic_time_us();

// Record peer observation (called on beacon RX)
utlp_trust_record_observation(mac, offset_us, stratum);

// Select best peer for sync
utlp_peer_ledger_t *best = utlp_trust_select_best_peer();

// Check entrainment budget
bool can_fire = utlp_immune_can_defend();

// Check crowd support
bool have_support = utlp_trust_has_quorum(my_offset, 2000);
```

---

## Files

| File | Lines | Purpose |
|------|-------|---------|
| `utlp.c` | ~1300 | Core protocol engine |
| `utlp_trust.c` | ~800 | Metabolic Ledger |
| `utlp_trust.h` | ~550 | Trust API + constants |
| `utlp_immune.c` | ~120 | Token bucket + anergy |
| `utlp_immune.h` | ~200 | Immune API + constants |
| `utlp_hal.h` | ~250 | Platform abstraction |
| `utlp_hal_esp32.c` | ~400 | ESP32 HAL implementation |

**Total: ~3,620 lines of C**

---

## The Philosophy

> "Time cannot wait for pairwise agreement or quorum. A distributed timeline must be born of one — a single genesis node declares the epoch and propagates the reference."

The first device IS the atomic clock. Peers are optional enhancements, not requirements. When a second device arrives, it defers to the established timeline. No voting. No elections. Just physics.

---

*Document version: 1.0*
*Parent: UTLP Technical Supplement S2.32*
*Implementation: ESP32-C6 / ESP-NOW*
*Repository: https://github.com/lemonforest/mlehaptics/tree/main/examples/utlp*
