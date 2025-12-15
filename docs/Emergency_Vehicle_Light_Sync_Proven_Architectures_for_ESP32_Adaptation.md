# Emergency Vehicle Light Sync: Proven Architectures for ESP32 Adaptation

Professional emergency lighting manufacturers have converged on a surprisingly elegant solution for wireless synchronization: **GPS atomic clock as a shared time reference rather than direct RF communication between nodes**. This eliminates the complexity of real-time wireless coordination entirely. For your ESP32 bilateral stimulation device, a simplified adaptation of their wired sync protocols combined with BLE timestamp exchange can achieve **sub-5ms accuracy**—well within your 10ms requirement.

## The GPS breakthrough eliminates wireless timing complexity

The most significant discovery across Whelen, Federal Signal, SoundOff Signal, and Feniex is that **none use direct RF communication for inter-vehicle timing synchronization**. Instead, all four manufacturers independently adopted GPS time as a universal reference clock. Each vehicle's sync module contains a GPS receiver that captures only the timing signal—not position data—eliminating cumulative drift by periodically anchoring to atomic clock precision.

SoundOff's bluePRINT Sync documentation explicitly states the module is "passive"—it does not broadcast, transmit, or know its position. Federal Signal's On Scene Sync (PFSYNC-1) works identically, requiring **45 seconds** for initial lock and maintaining sync accuracy with GPS refresh approximately every **8 hours**. This 8-hour holdover window reveals that the internal oscillator maintains sub-pattern-cycle accuracy (typically <100ms drift) over extended operation, implying crystal stability around **10-20 PPM**.

For intra-vehicle synchronization, these systems use deterministic wired buses: Whelen's WeCanX (proprietary CAN, 99 device capacity), Federal Signal's Convergence Network (RS485 with open SAE protocol), and simpler sync wires for standalone lightheads.

## Patent US7116294B2 reveals the sync line master election

Whelen's foundational patent for LED synchronization (US7116294B2, filed 2003) documents a self-organizing master/slave architecture that's directly adaptable to peer-to-peer BLE systems:

**The SYNC line protocol works as follows:**
- All driver circuits connect to a common SYNC line via two transistors (Q1 senses, Q2 asserts)
- The first device to initiate its flash pattern pulls the SYNC line low and becomes master
- Other devices detect this low signal through Q1, recognizing another unit has taken control
- Slave devices follow the timing pulses on the SYNC line rather than running independent clocks
- An 8-bit PIC microcontroller (PIC12C519) manages the internal phase clock with Ø1/Ø2 phases

This eliminates any configuration requirement—plug multiple lights together, power them on, and one automatically becomes timing master. The phase selection input (GP5) allows each unit to sync to either Ø1 or Ø2 phase edges, enabling alternating "wig-wag" operation. Pattern timing uses **400ms signal phases** with matching **400ms resting phases**, controlled by the switching regulator at **150 kHz**.

A more sophisticated approach appears in Whelen's mesh networking patent (EP3535629A1), which describes **Receiver-Receiver Synchronization (RRS)**: a reference node broadcasts a message that multiple receivers witness simultaneously. Receivers then exchange timestamps of this commonly-witnessed event to calculate their mutual offsets. This requires at least three "fully meshed" devices to avoid multi-hop delay errors.

## Feniex uses pattern-boundary resync to mask drift

Feniex takes a pragmatic approach that accepts clock drift between sync exchanges by **resynchronizing automatically at the end of each pattern cycle**. Their Fusion and T3 series use a simple master/slave election:

1. Hold the blue sync wire to ground for 3 seconds
2. All LEDs illuminating indicates **master mode**; partial/no illumination means **slave mode**
3. Products must share identical firmware versions to sync (indicated by label color matching)

Their newer Q-Link serial system abandons master/slave entirely for a **zone-based architecture** supporting up to 48 lightheads per controller via 2-wire twisted pair serial connections (recommended: 7 turns per foot for noise immunity). The SynQ controller scales this to **96 Q Serial lightheads or 16 Quantum 2.0 devices**, with all products communicating as one intelligent system.

The critical insight for adaptation: by resynchronizing at pattern boundaries (typically every few hundred milliseconds to a few seconds), Feniex masks crystal drift without requiring continuous correction. For bilateral stimulation with typical 500ms-2s alternation periods, this approach means drift within a single cycle would be negligible even with poor oscillators.

## Timing tolerances and data structures for patterns

Emergency lighting patterns are stored as firmware lookup tables with timing specified in terms of:
- **Flash duration** (on-time per burst)
- **Inter-flash interval** (off-time between bursts within a signal phase)
- **Signal/resting phase duration** (Whelen uses 400ms each)
- **Phase assignment** (Ø1 or Ø2 for alternating sync)

SoundOff's PWM control specification reveals timing precision: remote mode control signals must be **100 ±2Hz** (1% frequency tolerance), with duty cycle controlling light output intensity. Their documented patterns include flash durations down to **50ms** (over-voltage warning: 50ms ON / 950ms OFF).

| Manufacturer | Sync Method | Typical Accuracy | Drift Handling |
|-------------|-------------|------------------|----------------|
| Whelen V2V | GPS time reference | Sub-μs (GPS atomic) | 8+ hour holdover with TCXO |
| SoundOff | GPS time (passive) | Sub-ms | ~8-hour GPS refresh required |
| Federal Signal | GPS clock + RS485 | 45s acquisition | Continuous GPS lock |
| Feniex | Pattern-boundary resync | Per-cycle (~100-400ms) | Resync each pattern cycle |

## BLE implementation strategy for ESP32-C6 bilateral stimulation

The ESP32-C6 supports **BLE 5.0** (not 5.2), meaning isochronous channels used by LE Audio for TWS sync are unavailable. However, research confirms **sub-5ms synchronization is readily achievable** using connection-based approaches with two-way timestamp exchange.

**Recommended architecture adapts the emergency lighting patterns:**

Instead of GPS, use the BLE master device's clock as the shared reference. The master periodically sends timestamp packets; the slave calculates offset using a simplified Cristian's algorithm:

```
offset = ((t2 - t1) + (t3 - t4)) / 2
```

Where t1 is slave's send time, t2 is master's receive time, t3 is master's reply time, and t4 is slave's receive time. Apply moving-average smoothing over 5-10 samples to reduce jitter.

**Critical ESP32 configuration for minimum latency:**
- Connection interval: **7.5-15ms** (parameter min_int = 0x0006 to 0x000C)
- Slave latency: **0** (no skipped connection events)
- Use **esp_timer** with ISR dispatch for microsecond-resolution scheduling
- Sync frequency: every **30-60 seconds** after initial convergence (adequate for 20-100 PPM crystal drift)

At typical ESP32 crystal accuracy of 50 PPM, drift accumulates at approximately **180ms per hour**. Syncing every 60 seconds limits worst-case error to **3ms** between exchanges—well under your 10ms threshold. For 8+ hour operation, the system simply continues periodic sync; there's no "holdover" concern since the BLE connection remains active.

## Pattern protocol for bilateral stimulation

Adapt Feniex's pattern-boundary approach combined with Whelen's phase-based alternation:

```c
typedef struct {
    uint64_t start_time_master;    // Pattern start in master's clock
    uint16_t period_ms;            // Alternation period (e.g., 500ms)
    uint8_t  master_phase;         // Which device starts (0 or 1)
    uint16_t duty_cycle_percent;   // Pulse width as percentage of period
} bilateral_pattern_t;
```

Master broadcasts this structure once. Both devices calculate their local trigger times by applying their synchronized offset. The slave inverts `master_phase` to ensure alternation. Each device independently schedules its stimulation pulses using `esp_timer_start_once()`, eliminating round-trip latency from the timing-critical path.

For therapeutic EMDR application, pattern changes (speed adjustment, pause, resume) are non-time-critical and can use standard BLE write operations with acknowledgment.

## Resilience and quality monitoring

Emergency lighting systems include several robustness features worth adopting:

**Automatic master election** (from Whelen patent): If your design allows role flexibility, implement first-to-advertise-becomes-master logic. For a fixed two-device system, this may be unnecessary—simply designate one device as permanent master.

**Sync quality monitoring**: Track offset variance across recent sync exchanges. If variance exceeds **2-3ms**, trigger more frequent syncing or alert the user. SoundOff's 8-hour GPS refresh requirement suggests acceptable drift tolerance is quite generous for perceptible synchronization.

**Pattern-boundary safety**: Following Feniex's approach, ensure stimulation patterns naturally resync at their boundaries. If a 500ms alternation cycle drifts by 3ms, users won't perceive it—but implementing a brief resync confirmation at each pattern restart provides an additional safety margin.

**Connection loss handling**: Stop all stimulation immediately on disconnect, enter safe mode, and require full resync (5-10 timestamp exchanges) before resuming operation after reconnection.

## Conclusion: Proven patterns for reliable bilateral sync

Emergency vehicle manufacturers solved wireless multi-node synchronization by avoiding real-time RF coordination entirely—using GPS as a shared reference eliminates the fundamental problem. For ESP32 BLE, the equivalent is using the connection itself as the timing anchor: the master's clock becomes the reference, timestamp exchanges measure offset, and both devices execute patterns from their synchronized local clocks.

The Feniex pattern-boundary resync approach is particularly well-suited to bilateral stimulation, where alternation periods of hundreds of milliseconds make sub-10ms accuracy more than sufficient. By syncing every 30-60 seconds and resynchronizing at pattern transitions, you achieve the reliability of professional systems with minimal implementation complexity.

Key specifications to target: **15ms connection interval**, **30-second sync period** (after initial 5-exchange convergence), **esp_timer ISR dispatch** for pulse triggering, and **pattern-broadcast architecture** where timing commands contain future timestamps rather than immediate triggers. This architecture directly mirrors how Whelen's V2V module works: both ends know what time it is, both know the pattern, so both execute independently in perfect sync.