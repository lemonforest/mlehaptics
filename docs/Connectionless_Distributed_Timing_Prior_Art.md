# Connectionless Distributed Timing: A Prior Art Publication

**Synchronized Actuation Without Real-Time Coordination**

*mlehaptics Project — Defensive Publication — December 2025*

**Authors:** Steve (mlehaptics), with assistance from Claude (Anthropic)

**Status:** Prior Art / Defensive Publication / Open Source

---

## Abstract

This document establishes prior art for a class of distributed embedded systems that achieve synchronized actuation across independent wireless nodes *without* real-time coordination traffic during operation. The core insight: when devices share a time reference and a script describing future actions, they can execute in perfect synchronization without exchanging messages during the timing-critical phase.

We document the journey from attempting to solve BLE (Bluetooth Low Energy) stack timing jitter to recognizing that the constraint itself was artificial. By separating *configuration* (which requires bidirectional communication) from *execution* (which does not), we achieve sub-millisecond synchronization using commodity microcontrollers and standard RF protocols.

This architecture was validated using SAE J845-compliant emergency lighting patterns (Quad Flash) captured at 240fps, demonstrating zero perceptible overlap between alternating signals—precision sufficient for therapeutic bilateral stimulation, emergency vehicle warning systems, and distributed swarm coordination.

This work is published as open-source prior art to ensure these techniques remain freely available for public use and cannot be enclosed by patents.

---

## 1. Introduction: The Constraint That Wasn't

### 1.1 The Original Problem

The mlehaptics project began with a straightforward goal: create a wireless bilateral EMDR (Eye Movement Desensitization and Reprocessing) therapy device using two handheld units that produce alternating haptic/visual stimulation. The therapeutic requirement: maintain antiphase timing such that when the left device is active, the right is inactive, and vice versa—with sufficient precision that a patient never perceives simultaneous activation.

The initial assumption was that this required BLE communication between the devices during operation. One device would signal "I'm activating now" and the other would respond. This assumption led to months of engineering effort attempting to compensate for BLE stack latency and jitter.

### 1.2 The Stack Jitter Problem

BLE on ESP32-class microcontrollers presents a fundamental timing challenge. When a packet arrives at the RF frontend, the following processing chain executes before application code learns of the event:

```
┌─────────────────────────────────────────────────────────────┐
│  RF Event (hardware interrupt) ← Precise timing exists here │
├─────────────────────────────────────────────────────────────┤
│  BLE Controller ISR (closed-source binary blob)             │
├─────────────────────────────────────────────────────────────┤
│  VHCI Transport (RAM buffer exchange)                       │
├─────────────────────────────────────────────────────────────┤
│  NimBLE/Bluedroid Host Task (FreeRTOS context switch)       │
├─────────────────────────────────────────────────────────────┤
│  L2CAP → ATT → GATT parsing                                 │
├─────────────────────────────────────────────────────────────┤
│  Application callback ← Where we can timestamp              │
└─────────────────────────────────────────────────────────────┘
```

The latency from RF event to application callback varies by 1-50ms depending on system state: FreeRTOS scheduling, other BLE operations in progress, WiFi coexistence, flash operations. This jitter is not RF propagation (nanoseconds across a room) but *software processing time*—and it's largely invisible to the application layer.

### 1.3 The Irony

The BLE radio *has* precise timing. It must—frequency hopping requires sub-microsecond coordination or packets land on wrong channels. Both devices in a BLE connection are already synchronized to a shared anchor point. The peripheral knows *exactly* when the central will transmit.

This synchronization exists inside the controller. It's simply not exposed to the application.

We spent considerable effort trying to measure and compensate for jitter we couldn't directly observe, because the abstraction hid the precision we needed.

### 1.4 The Reframe

The breakthrough came from questioning the original assumption. The user requirement was:

> "I want Bluetooth"

What this actually meant:

> "I want to configure these devices from my phone"

These are not the same thing. The phone needs bidirectional BLE communication during *setup*. The devices themselves, during *operation*, need only to execute a shared plan.

**The devices don't need to talk to each other. They need to agree on what time it is and what they're going to do.**

---

## 2. The Connectionless Architecture

### 2.1 Separation of Concerns

The architecture cleanly separates three phases:

| Phase | Transport | Purpose | Timing Criticality |
|-------|-----------|---------|-------------------|
| **Bootstrap** | BLE | Pairing, key exchange, WiFi MAC exchange | None |
| **Configuration** | BLE (then released) | Script upload, zone assignment, ESP-NOW key derivation | None |
| **Execution** | ESP-NOW only | Pattern playback, time sync beacons | **Sub-millisecond** |

**BLE Bootstrap Model**: Peer BLE connection is released after key exchange completes. The operational phase uses ESP-NOW exclusively for peer-to-peer traffic. This provides deterministic timing (ESP-NOW ±100μs vs BLE ±10-50ms jitter) while preserving radio bandwidth. A PWA (phone app) can still connect via BLE for user interface—only the peer-to-peer link transitions to ESP-NOW.

During execution, devices do not coordinate. Each device:
1. Knows what time it is (via prior UTLP synchronization)
2. Knows what script to play (uploaded during configuration)
3. Knows its zone/role (assigned during configuration)
4. Executes locally with no network dependency

### 2.2 Script-Based Execution

A "script" is a deterministic sequence of timed events that both devices possess. The simplest script for bilateral stimulation:

```c
typedef struct {
    uint64_t start_time_us;      // When pattern begins (synchronized time)
    uint32_t period_us;          // Alternation period (e.g., 1,000,000 = 1Hz)
    uint8_t  duty_cycle_percent; // Active portion of each half-cycle
    uint8_t  zone_active_first;  // Which zone starts active (0 or 1)
} bilateral_script_t;
```

Given synchronized time and this script, each device independently calculates:

```c
bool should_be_active(uint64_t now_us, bilateral_script_t* script, uint8_t my_zone) {
    uint64_t elapsed = now_us - script->start_time_us;
    uint64_t cycle_position = elapsed % script->period_us;
    uint8_t current_phase = (cycle_position < script->period_us / 2) ? 0 : 1;
    
    // XOR determines if this zone is active in this phase
    return (current_phase ^ my_zone) == script->zone_active_first;
}
```

No communication. No coordination. Just math on shared data.

### 2.3 Time is Defined, Not Measured

Once devices share a time reference, the question shifts from "when did you send this?" to "what should we both be doing right now?"

Early designs explored TDM (Time Division Multiplexing) scheduling, but this introduced artificial delays—devices waiting for their assigned slot even when the channel was clear. The final architecture abandons TDM in favor of event-driven execution against synchronized time.

WiFi (ESP-NOW) is prioritized over BLE for all peer-to-peer traffic, even on the server/master device. BLE's connection-oriented overhead and scheduling constraints create unnecessary latency. Once trust is established via BLE pairing, all operational communication moves to ESP-NOW's connectionless model.

**The synchronization problem becomes a shared-clock problem, not a message-passing problem.**

### 2.4 BLE for Bootstrap, ESP-NOW for Operations

The ESP-NOW protocol (Espressif's proprietary connectionless WiFi protocol) offers 10-100x lower latency jitter than BLE because it bypasses the connection-oriented stack entirely. A typical ESP-NOW packet arrives in ~300μs with ~100μs jitter, versus BLE's ~3ms with ~10-50ms jitter.

The architecture uses both:

1. **BLE** establishes trust (pairing, bonding, key exchange)
2. **ESP-NOW** carries operational traffic (sync beacons, monitoring)
3. **Shared key material** derived from BLE pairing secures ESP-NOW

```c
// Key derivation: BLE provides the secret, MACs provide binding
esp_err_t derive_espnow_key(
    const uint8_t nonce[8],           // Random, sent via encrypted BLE
    const uint8_t server_mac[6],      // WiFi MAC of server
    const uint8_t client_mac[6],      // WiFi MAC of client
    uint8_t lmk_out[16]               // ESP-NOW encryption key
) {
    uint8_t ikm[12];
    memcpy(ikm, server_mac, 6);
    memcpy(ikm + 6, client_mac, 6);
    
    return mbedtls_hkdf(
        mbedtls_md_info_from_type(MBEDTLS_MD_SHA256),
        nonce, 8,                      // Salt
        ikm, 12,                       // Key binding material
        (uint8_t*)"ESPNOW_LMK", 10,   // Domain separation
        lmk_out, 16
    );
}
```

**Why HKDF, not PBKDF2/Argon2**: The input is already high-entropy (64-bit hardware RNG nonce or 128-bit BLE LTK). Password-stretching algorithms solve the wrong problem—they're designed to slow brute-force attacks on weak human-memorable passwords. With 64+ bit entropy, brute force is already computationally infeasible. HKDF correctly extracts and expands high-entropy key material without unnecessary iterations or memory overhead.

**Defense-in-depth architecture**: Security is layered across physical (proximity requirement), transport (BLE SMP bonding, ESP-NOW CCMP), key derivation (HKDF with dual-MAC binding), and application layers (sequence numbers, optional TOTP). This provides threat-proportional security—appropriate cryptographic strength without over-engineering that would increase complexity and attack surface.

This gives the security properties of BLE pairing (encrypted key exchange, MITM protection) with the timing properties of ESP-NOW (low-jitter delivery). Peer BLE connection is released after key exchange—the operational phase uses ESP-NOW exclusively for peer traffic.

---

## 3. Validation: SAE J845 Quad Flash

### 3.1 The Standard

SAE J845 defines flash patterns for emergency vehicle warning lights. The Quad Flash pattern (four rapid flashes followed by a pause) has strict timing requirements for visibility and seizure safety. If two devices executing alternating Quad Flash patterns show any overlap, the pattern is broken.

### 3.2 The Test

Two ESP32-C6 devices running the connectionless architecture were configured for a dual-pattern validation:

**Zone-assigned alternation (antiphase):**
- Device A: RED channel
- Device B: BLUE channel
- Alternation: When A's red flashes, B's blue is dark; when B's blue flashes, A's red is dark

**Shared synchronization (in-phase):**
- Both devices: WHITE channel
- Both white LEDs flash together at a different frequency than the red/blue pattern

This dual-pattern test validates both capabilities simultaneously:
1. **Antiphase coordination**: Red and blue never overlap (bilateral stimulation requirement)
2. **In-phase coordination**: White LEDs fire together (swarm coherence requirement)

Validation method: 240fps slow-motion video capture (4.17ms per frame). At this frame rate, any timing error would be visible as either red/blue overlap or white desynchronization.

### 3.3 The Result

**Zero frames showed red/blue overlap. Zero frames showed white desynchronization.** 

The devices maintained clean alternation on zone-assigned channels while simultaneously maintaining lock on the shared white channel—across the entire test duration, with timing precision well within one frame (4.17ms).

This is approximately 10x better than the therapeutic requirement for EMDR bilateral stimulation (~40ms perceptual threshold), and validates that:
1. Connectionless execution achieves sufficient precision for demanding timing applications
2. Commodity ESP32 hardware with standard protocols can meet professional emergency lighting standards
3. The architecture supports both antiphase (bilateral) and in-phase (swarm) coordination simultaneously
4. Zone assignment works correctly—identical firmware, different runtime behavior

---

## 4. Foundational Protocols

The connectionless architecture builds on two protocol specifications documented separately:

### 4.1 UTLP (Universal Time Layer Protocol)

UTLP provides synchronized time as a "broadcast environmental variable"—a public utility that any device can consume without pairing or authentication. Key features:

- **Stratum-based hierarchy**: Automatic source selection (GPS → FTM → ESP-NOW peer → free-running)
- **Holdover mode**: Graceful degradation during source loss using Kalman-filtered drift compensation
- **Transport agnostic**: Designed to work over BLE, ESP-NOW, 802.11, or acoustic channels
- **Glass Wall architecture**: Time stack (public) strictly separated from application stack (private)

**Implementation note**: In the reference implementation, UTLP runs over ESP-NOW after BLE bootstrap completes. BLE establishes trust and exchanges the Long-Term Key (LTK); all subsequent peer traffic—including UTLP sync beacons—uses ESP-NOW encrypted with keys derived from the LTK. This provides BLE-grade security with ESP-NOW's timing characteristics.

The core insight: when devices agree on time to ±30μs precision, timestamps provide sufficient ordering granularity for any human-scale coordination.

### 4.2 RFIP (Reference-Frame Independent Positioning)

When UTLP is combined with 802.11mc FTM (Fine Time Measurement) ranging, devices can establish spatial relationships without external reference:

- **Intrinsic geometry**: "Where are we relative to each other?" not "Where are we on Earth?"
- **No infrastructure dependency**: Works in moving vehicles, underground, underwater, or in space
- **Swarm-emergent coordinates**: The coordinate system arises from the swarm itself

This enables applications where GPS is unavailable or meaningless: drone swarms in GPS-denied environments, rescue operations in collapsed structures, coordination on mobile platforms. Critically, the swarm can *build a map of where it has been* using only peer-derived coordinates—enabling systematic search patterns without any external positioning infrastructure.

### 4.3 Autonomous Zone Assignment via Ranging

802.11mc ranging enables a capability beyond simple positioning: **autonomous zone assignment**. When devices can measure distances to each other, the swarm can self-organize without explicit configuration.

**The problem with manual zone assignment:**
- Pre-configured device zones require knowing which physical device is which
- Ordered assignment ("first to connect = zone 0") depends on connection timing, not spatial position
- Neither method produces spatially-meaningful zone topology

**Ranging-based autonomous assignment:**
1. Devices range to each other and/or to reference points
2. Relative positions computed via trilateration (RFIP)
3. Zone assignment derived from spatial position (e.g., leftmost = zone 0, rightmost = zone 1)
4. Topology emerges from geometry, not configuration

**Example: Pile of drones → Flying swarm**

A responder dumps a bag of identical drones at an incident scene. Without ranging:
- Drones must be pre-labeled with zone assignments, OR
- Zones assigned by activation order (spatially meaningless)

With 802.11mc ranging:
- Drones take off and establish relative positions
- Spatial topology computed (who's north, south, highest, lowest)
- Zone assignment follows spatial role (e.g., "northernmost drone = zone 0")
- Coherent warning pattern emerges from spatial reality

The swarm becomes spatially self-aware. Zone assignment becomes a property of where you *are*, not what you were *labeled*.

---

## 5. Applications: The Primitive Enables Many Things

The connectionless timing architecture is not a product—it's a **distributed real-time primitive**. The EMDR device was simply the forcing function that demanded solving the hard parts. Once solved, the primitive instantiates across domains.

### 5.1 Medical and Therapeutic

**Bilateral Stimulation Devices (EMDR, tDCS)**
- Handheld haptic/visual alternating stimulation
- Multi-electrode transcranial stimulation with precise phase relationships
- Binaural audio generation across separate speakers

**Coordinated Wearable Sensing**
- Multi-point biosignal acquisition (ECG leads, EEG arrays) with synchronized sampling
- Distributed pulse oximetry for perfusion mapping
- Synchronized accelerometry for gait analysis across body segments

**Rehabilitation Systems**
- Bilateral motor training devices with precisely timed feedback
- Synchronized haptic cues for Parkinson's gait freezing intervention
- Multi-limb coordination training with phase-locked stimulation

### 5.2 Emergency and Safety

**Vehicle Warning Light Synchronization**
- Fleet-coherent flash patterns without GPS dependency
- Incident-scene "light walls" from multiple vehicles
- Motorcycle/bicycle conspicuity systems synced to nearby emergency vehicles

**Aerial Warning Swarms**
- Drone-carried warning lights above traffic incidents
- Elevated pattern visibility over terrain/vehicle obstructions
- Self-organizing formation with RFIP-derived zone assignment

**Search and Rescue in GPS-Denied Environments**
- Collapsed structures, underground, underwater, or remote wilderness
- Swarm builds its own spatial map using RFIP peer ranging
- Searched areas tracked via swarm-local coordinates—no external reference needed
- Pattern coverage emerges from spatial awareness: "I'm north of you, I'll search north"
- Works where GPS fails: rubble attenuation, canyon walls, dense canopy, caves

**Building Evacuation Systems**
- Synchronized directional lighting across floors
- Wave patterns indicating egress direction
- No wired infrastructure required—battery-powered nodes

**Maritime and Aviation**
- Distributed navigation markers without shore infrastructure
- Runway/taxiway lighting for austere airfields
- Search pattern coordination for distributed assets

### 5.3 Entertainment and Art

**Distributed Light Shows**
- Audience-carried LED devices synchronized to stage performance
- Architectural lighting across multiple buildings
- No DMX wiring—wireless with frame-accurate timing

**Silent Disco Evolution**
- Multiple music streams with synchronized lighting across all receivers
- Crowd-wide visual effects responding to the mix
- Zone-based experiences within single venue

**Kinetic Sculptures**
- Synchronized mechanical elements across physical space
- No control wiring between sculpture segments
- Battery-operated with seasonal deployment

**Theatrical Effects**
- Wireless pyrotechnic timing (with appropriate safety systems)
- Coordinated fog/haze release across stage
- Actor-carried props with synchronized effects

### 5.4 Industrial and Agricultural

**Distributed Sensor Arrays**
- Synchronized sampling for sensor fusion
- Seismic/acoustic arrays without wired timing bus
- Air quality monitoring with coordinated measurement windows

**Agricultural Automation**
- Coordinated spraying across multiple drones/vehicles
- Synchronized irrigation pulse patterns
- Pollination timing coordination for indoor farms

**Construction and Surveying**
- Synchronized laser scanning from multiple stations
- Coordinated vibration monitoring during blasting
- Multi-point settlement monitoring with time-aligned measurements

**Mining and Underground**
- GPS-denied environment timing for equipment coordination
- Ventilation control with synchronized damper operation
- Refuge chamber status synchronization

### 5.5 Research and Scientific

**Distributed Physics Experiments**
- Multi-point detector timing without dedicated timing infrastructure
- Balloon-borne instrument arrays with synchronized acquisition
- Underwater acoustic arrays for marine research

**Environmental Monitoring**
- Wildlife tracking with synchronized beacon detection
- Distributed weather sensing with coordinated measurements
- Volcanic/seismic monitoring in remote locations

**Astronomy and Space**
- Ground-based interferometry timing layer
- CubeSat swarm coordination
- Lunar/planetary surface operations (RFIP particularly relevant)

### 5.6 Consumer and Lifestyle

**Gaming and Social**
- Multiplayer physical game props with synchronized effects
- Escape room puzzle coordination without wired systems
- Social dancing apps with group-synchronized haptic cues

**Fitness and Sports**
- Team training systems with synchronized timing cues
- Interval training coordination across group classes
- Race timing systems for informal events

**Home Automation**
- Circadian lighting synchronized across rooms
- Multi-speaker audio with sub-millisecond alignment
- Holiday lighting coordination across properties

### 5.7 The Meta-Pattern

All these applications share the same structure:

```
┌─────────────────────────────────────────────────────────────┐
│  CONFIGURATION PHASE                                         │
│  - Establish trust (pairing, authentication)                │
│  - Synchronize time reference                               │
│  - Distribute script/pattern                                │
│  - Assign zones/roles                                       │
├─────────────────────────────────────────────────────────────┤
│  EXECUTION PHASE                                            │
│  - No coordination traffic                                  │
│  - Local calculation: script[zone][t]                       │
│  - Independent actuation                                    │
│  - Coherent group behavior emerges                          │
└─────────────────────────────────────────────────────────────┘
```

The primitive doesn't care whether it's vibrating a therapy device, flashing a warning light, triggering a pyrotechnic, or sampling a sensor. It only cares that distributed nodes agree on time and plan.

---

## 6. Industry Context: How Professionals Solved This (And Its Limitations)

### 6.1 The GPS Convergence

Investigation of professional emergency lighting manufacturers—Whelen, Federal Signal, SoundOff Signal, and Feniex—revealed a surprising convergence: **none use direct RF communication for inter-vehicle timing synchronization**. All four independently adopted GPS time as a universal reference clock.

| Manufacturer | Product | Sync Method | Characteristics |
|-------------|---------|-------------|-----------------|
| Whelen | V2V Module | GPS atomic reference | 8+ hour holdover with TCXO |
| SoundOff | bluePRINT Sync | GPS (passive, no position) | ~8-hour GPS refresh |
| Federal Signal | PFSYNC-1 | GPS + RS485 | 45s acquisition time |
| Feniex | Fusion/T3 | Pattern-boundary resync | Per-cycle realignment |

SoundOff's documentation explicitly states their sync module is "passive"—it does not broadcast, transmit, or know its position. It only consumes GPS timing signals. This validates the core insight: **synchronization requires shared time, not bidirectional communication**.

### 6.2 Existing Patent Landscape

**US7116294B2** (Whelen, filed 2003): Documents a self-organizing master/slave architecture for LED synchronization using a shared SYNC line. Key elements:
- First device to assert the line becomes master
- Other devices detect the assertion and become slaves
- 8-bit PIC microcontroller manages phase clock (Ø1/Ø2 phases)
- 400ms signal phases with matching 400ms resting phases

This patent covers *wired* synchronization with physical sync lines—not applicable to wireless connectionless operation.

**EP3535629A1** (Whelen): Describes Receiver-Receiver Synchronization (RRS) where a reference node broadcasts a message that multiple receivers witness simultaneously. Receivers exchange timestamps of the commonly-witnessed event to calculate mutual offsets. This requires "fully meshed" devices and continuous coordination traffic.

### 6.3 The GPS Dependency Problem

GPS-based synchronization works but creates hard dependencies:
- **Acquisition time**: 45 seconds to several minutes for initial lock
- **Sky visibility**: Fails indoors, underground, in urban canyons
- **Hardware cost**: GPS receivers add $5-20 per node
- **Power consumption**: GPS draws 20-50mA continuous
- **Jamming vulnerability**: Civilian GPS is trivially disrupted

The connectionless architecture documented here provides an alternative: peer-derived time synchronization that works without external infrastructure, indoors, and at lower power.

### 6.4 Pattern-Boundary Resynchronization (Feniex Contribution)

Feniex's approach accepts clock drift between sync exchanges by **resynchronizing automatically at the end of each pattern cycle**. This is pragmatic: if patterns repeat every 500ms, and crystal drift accumulates at 50 PPM (typical ESP32), maximum drift per cycle is 25μs—imperceptible.

This insight influenced the UTLP design: for many applications, perfect continuous synchronization is unnecessary. Agreement at pattern boundaries suffices.

### 6.5 What This Work Adds Beyond Industry Practice

| Existing Practice | This Work's Contribution |
|------------------|-------------------------|
| GPS as time source | Peer-derived time (UTLP stratum hierarchy) |
| Wired sync lines | Connectionless RF execution |
| Continuous coordination traffic | Script-based independent execution |
| Fixed infrastructure | Mobile, infrastructure-free operation |
| Single-purpose devices | Zone/Role abstraction for flexible deployment |
| Earth-referenced positioning | Intrinsic swarm geometry (RFIP) |

---

## 7. Why This Wasn't Done Before

### 7.1 The BLE Stack Abstraction (And Why We Left Anyway)

BLE was designed for reliable data transfer with minimal power, not precision timing. The stack abstracts away the RF-level timing that would enable tight synchronization. The controller knows the connection event anchor with microsecond precision; the application learns "a packet arrived" with millisecond uncertainty.

**Important clarification**: Tight timing *can* be achieved over BLE. With careful stack configuration, statistical filtering, and jitter compensation, sub-millisecond synchronization is possible. Research implementations have demonstrated this.

We chose the connectionless RF path deliberately, not because BLE timing was impossible, but because:
1. **Connectionless eliminates a failure mode**: No connection to drop during therapy
2. **Lower latency jitter**: ESP-NOW's ~100μs jitter vs BLE's ~10-50ms simplifies the timing stack
3. **Independence during execution**: Devices don't need to maintain a link while operating
4. **Phone compatibility preserved**: BLE handles the user-facing interface; ESP-NOW handles peer coordination

The architecture uses BLE for what it's good at (phone pairing, trust establishment) and ESP-NOW for what it's good at (low-jitter peer communication).

### 7.2 The Coordination Assumption

Distributed systems literature focuses heavily on consensus and coordination: how do nodes agree? BFT, Raft, Paxos—all assume ongoing communication is necessary for agreement.

For many applications, this assumption is unnecessary. If nodes can agree *once* on time and plan, they don't need to agree *continuously* during execution. The FLP impossibility result (consensus is impossible in asynchronous systems) doesn't apply when you've already established synchronous time.

### 7.3 GPS as Crutch

Professional systems (emergency vehicle lighting, broadcast synchronization) solved this problem with GPS. Every node gets atomic time from satellites; coordination is implicit.

This works but creates dependencies: satellite visibility, antenna placement, acquisition time. The connectionless architecture provides an alternative path that works indoors, underground, and in RF-challenged environments.

---

## 8. Implementation Availability

Reference implementations are available under MIT license:

- **UTLP specification and ESP32 implementation**: github.com/mlehaptics
- **RFIP addendum with 802.11mc FTM integration**: Included in UTLP repository
- **Bilateral stimulation firmware**: ESP32-C6 reference design with BLE+ESP-NOW

Hardware requirements:
- ESP32-C6 (recommended) or ESP32-S3/C3
- Standard BLE and WiFi capabilities
- No specialized timing hardware required

---

## 9. Prior Art Claims

This document establishes prior art for the following techniques, ensuring they remain available for public use:

### 9.1 Architectural Patterns

1. **Connectionless synchronized actuation**: Devices sharing time reference and script execute in coordination without runtime communication

2. **Bootstrap/Configuration/Execution phase separation**: BLE for trust and setup, connectionless for timing-critical operation

3. **Script-based distributed execution**: Deterministic event sequences calculated locally from shared parameters

4. **Shared-clock execution model**: Devices calculate state from synchronized time rather than exchanging coordination messages

5. **Local jitter characterization**: Treating synchronization error as a property of local software stack, not network

### 9.2 Protocol Techniques

6. **BLE bootstrap for ESP-NOW security**: Deriving ESP-NOW encryption keys from BLE pairing material, then releasing peer BLE connection

7. **UTLP time as public utility**: Unencrypted broadcast time with Glass Wall isolation from application data

8. **Common Mode Rejection security**: Spoofed time affects all nodes equally, preserving relative synchronization

9. **Stratum-based opportunistic upgrade**: Automatic precision improvement when better sources become available

10. **Kalman-filtered holdover**: Joint offset/drift estimation for graceful degradation during source loss

11. **HKDF for high-entropy key derivation**: Using HKDF-SHA256 (not PBKDF2/Argon2) for secrets that are already high-entropy—password stretching is inappropriate when input has 64+ bits of entropy

12. **Multi-layer replay protection**: Session nonce (session uniqueness) + sequence numbers (intra-session ordering) + TOTP (time-binding) + CCMP (transport integrity)—four independent layers

13. **Defense-in-depth security architecture**: Physical, transport, key derivation, and application layer security with each layer providing independent protection

14. **Threat-proportional security design**: Cryptographic strength appropriate to actual threat model, avoiding over-engineering that increases complexity and attack surface

### 9.3 Application Patterns

15. **Swarm-emergent warning systems**: Distributed nodes forming coherent visual signals without central coordination

16. **Aerial extension of ground-level warnings**: Drone swarms providing elevated visibility for traffic incidents

17. **Zone/Role architectural separation**: Identical firmware, runtime-assigned function based on position or configuration

18. **RFIP intrinsic positioning**: Spatial awareness without Earth-referenced infrastructure

### 9.4 Validation Methods

19. **High-speed video validation of distributed timing**: Using frame-accurate capture to verify synchronization precision

20. **SAE J845 compliance testing for swarm systems**: Applying emergency vehicle lighting standards to distributed architectures

### 9.5 Techniques Extending Beyond Existing Patents

21. **Wireless connectionless sync vs. wired sync lines**: US7116294B2 requires physical SYNC wire; this work achieves equivalent coordination over RF without wired connection

22. **Script-based execution vs. continuous mesh coordination**: EP3535629A1 requires ongoing timestamp exchange between "fully meshed" devices; this work distributes script once, then executes independently

23. **Peer-derived time vs. GPS dependency**: Emergency vehicle systems require GPS receivers; UTLP stratum hierarchy achieves equivalent precision from peer sources

24. **Pattern-boundary resync generalization**: Extending Feniex's per-cycle resync concept to arbitrary script boundaries and multi-modal actuation

25. **Infrastructure-free spatial awareness**: RFIP provides relative positioning without surveyed anchor points, fixed infrastructure, or Earth-referenced coordinates

26. **Ranging-based autonomous zone assignment**: Using 802.11mc FTM or equivalent ranging to derive zone assignments from spatial position rather than pre-configuration or connection order

27. **Pile-to-swarm self-organization**: Undifferentiated identical devices establishing spatially-coherent role topology through peer ranging without central assignment authority

28. **Spatial-semantic zone mapping**: Zone assignments that reflect physical relationships (leftmost, northernmost, highest) rather than arbitrary identifiers

29. **Self-mapping search patterns in GPS-denied environments**: Swarm builds and tracks searched areas using only peer-derived RFIP coordinates, enabling coordinated coverage without external positioning infrastructure

---

## 10. Conclusion

The connectionless distributed timing architecture demonstrates that many coordination problems have simpler solutions than traditionally assumed. By separating configuration from execution, and by treating synchronized time as foundational rather than incidental, we eliminate entire categories of complexity.

The techniques documented here are not limited by technology—the hardware has existed for years. They were limited by assumptions: that coordination requires communication, that BLE timing is "good enough" (or "hopeless"), that GPS is the only path to precision.

By publishing this work as prior art, we ensure these techniques remain freely available. Technology that assumes cooperation rather than extraction.

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-23 | Initial defensive publication |
| 1.1 | 2025-12-23 | Added defense-in-depth security architecture, HKDF selection rationale, multi-layer replay protection, threat-proportional design philosophy; clarified BLE Bootstrap Model with peer release |
| 1.2 | 2025-12-23 | Added GPS-denied search and rescue with self-mapping patterns |

---

## References

### Project Documentation
1. UTLP Technical Report v2.0, mlehaptics Project, December 2025
2. UTLP Addendum A: Reference-Frame Independent Positioning, December 2025
3. UTLP Technical Supplement S1: Precision, Transport, and Security Extensions, December 2025
4. Advanced Architectural Analysis: Bilateral Pattern Playback Systems, mlehaptics Project, December 2025
5. Emergency Vehicle Light Sync: Proven Architectures for ESP32 Adaptation, mlehaptics Project, December 2025
6. 802.11mc FTM Reconnaissance Report, mlehaptics Project, December 2025

### Standards
7. SAE J845: Optical Warning Devices for Authorized Emergency, Maintenance, and Service Vehicles
8. IEEE 802.11-2016 §11.24: Fine Timing Measurement
9. IEEE 1588-2019: Precision Time Protocol (PTP)

### Related Patents (Prior Art Context)
10. US7116294B2: "LED synchronization" (Whelen, 2003) — Wired sync line master/slave architecture
11. EP3535629A1: "Receiver-Receiver Synchronization" (Whelen) — Mesh network timestamp exchange

### Technical References
12. ESP-IDF Programming Guide: ESP-NOW Protocol, Espressif Systems
13. ESP-IDF Programming Guide: Wi-Fi Driver, Espressif Systems
14. M. Fischer, N. Lynch, M. Paterson. "Impossibility of Distributed Consensus with One Faulty Process." JACM 1985
15. M. Shapiro et al. "Conflict-free Replicated Data Types." SSS 2011

---

## Acknowledgments

This work emerged from collaborative development combining human domain expertise with AI assistance:

- **Steve (mlehaptics)**: Architecture design, hardware implementation, "Time as Public Utility" philosophy, Glass Wall architecture, validation methodology, therapeutic domain expertise

- **Claude (Anthropic)**: Literature survey, protocol analysis, documentation compilation, prior art framing, application brainstorming

---

## Intellectual Property Statement

This document is published as **open-source prior art** under Creative Commons CC0 (public domain dedication) for the architectural concepts, and MIT license for reference implementations.

The authors explicitly disclaim any patent rights to the techniques described herein and publish this document to establish prior art, ensuring these methods remain freely available for public use without licensing requirements or restrictions.

**First Published**: December 23, 2025

**Repository**: github.com/mlehaptics

---

*— End of Document —*
