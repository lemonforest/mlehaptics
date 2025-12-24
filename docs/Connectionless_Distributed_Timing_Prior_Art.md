# Connectionless Distributed Timing: A Prior Art Publication

**Changing the Conditions of the FLP Impossibility Test**

*mlehaptics Project — Defensive Publication — December 2025*

**Authors:** Steve (mlehaptics), with assistance from Claude (Anthropic)

**Status:** Prior Art / Defensive Publication / Open Source

---

## Abstract

This document establishes prior art for a class of distributed embedded systems that achieve synchronized actuation across independent wireless nodes *without* real-time coordination traffic during operation. The core insight: when devices share a time reference and a script describing future actions, they can execute in perfect synchronization without exchanging messages during the timing-critical phase.

Development began with single-device pattern playback—deterministic, timer-driven actuation. Adding wireless pairing revealed that networked devices needed only to agree on time offset; the pattern architecture already supported connectionless operation. BLE worked. ESP-NOW worked better. By separating *configuration* (which requires bidirectional communication) from *execution* (which does not), we achieve sub-millisecond synchronization using commodity microcontrollers and standard RF protocols.

This architecture was validated using SAE J845-compliant emergency lighting patterns (Quad Flash) captured at 240fps, demonstrating zero perceptible overlap between alternating signals—precision sufficient for therapeutic bilateral stimulation, emergency vehicle warning systems, and distributed swarm coordination. Reference implementation runs on commodity ESP32-C6 hardware with a bill of materials under $15 per node.

This work is published as open-source prior art to ensure these techniques remain freely available for public use and cannot be enclosed by patents.

---

## 1. Introduction: The Solution Was Already There

### 1.1 The Development Path

The mlehaptics project began with a single device: one ESP32-C6 running a bilateral stimulation pattern—alternating haptic and visual pulses at configurable rates. The pattern playback was deterministic from the start, driven by a local timer.

When we added networking to create a wireless pair, the implementation was straightforward: the client runs the same pattern as the server, but in antiphase. Both devices execute the same script; they just need to agree on timing offset. BLE provided the communication channel, and it worked.

But we had questions. The ESP32-C6 has both BLE and WiFi radios. Could we do better with ESP-NOW? How tight could the synchronization actually get? What were the limits?

### 1.2 The Stack Jitter Investigation

Investigating BLE timing led us deep into the ESP32's radio stack:

```
┌─────────────────────────────────────────────────────────────┐
│  RF Event (hardware interrupt) ← Precise timing exists here │
├─────────────────────────────────────────────────────────────┤
│  BLE Controller ISR (closed-source binary blob)             │
├─────────────────────────────────────────────────────────────┤
│  VHCI Transport (RAM buffer exchange)                       │
├─────────────────────────────────────────────────────────────┤
│  NimBLE Host Task (FreeRTOS context switch)                 │
├─────────────────────────────────────────────────────────────┤
│  L2CAP → ATT → GATT parsing                                 │
├─────────────────────────────────────────────────────────────┤
│  Application callback ← Where we can timestamp              │
└─────────────────────────────────────────────────────────────┘
```

The latency from RF event to application callback varies by 1-50ms depending on system state: FreeRTOS scheduling, other BLE operations in progress, WiFi coexistence, flash operations. This jitter is not RF propagation (nanoseconds across a room) but *software processing time*.

### 1.3 The Realization

The investigation revealed something we hadn't fully appreciated: **we already had a connectionless architecture**. Both devices possessed the same pattern. They just needed to agree on time. The pattern playback we'd built for a single device was already the solution—we just hadn't recognized it as such.

BLE worked. We implemented PTP-style synchronization using NTP timestamps over BLE GATT, calculating clock asymmetry from round-trip measurements. Validation against wall-clock serial logs confirmed the algorithm reached coherence—but it took approximately 2 minutes to converge to stable sub-millisecond sync due to BLE's jitter distribution.

ESP-NOW could work better:
- **Faster convergence**: Seconds instead of minutes (lower jitter means fewer samples needed)
- **Lower steady-state jitter**: ±100μs vs ±10-50ms for time synchronization
- **Power efficiency**: Truly connectionless operation means radio silence when nothing changes
- **No connection to drop**: Pattern continues even if sync beacon is missed

The therapeutic requirement (sub-40ms precision) was easily met by BLE after convergence. But since the hardware supported ESP-NOW at no additional cost, why not use the better tool?

### 1.4 The Generalization

Once we recognized that "pattern playback with time agreement" was the core primitive, applications beyond bilateral stimulation became obvious. Any scenario where multiple devices need to act in coordination—emergency lighting, swarm robotics, sensor arrays—fits the same pattern:

**Devices don't need to talk to each other during operation. They need to agree on time and script.**

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
2. Knows what script to play (preloaded in firmware or uploaded during configuration)
3. Knows its zone/role (assigned during configuration)
4. Executes locally with no network dependency

### 2.2 Script-Based Execution

A "script" is a deterministic sequence of timed events that both devices possess. The simplest script for bilateral stimulation (illustrative pseudocode—the reference implementation uses richer structures for pattern playback):

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

Key derivation concept (illustrative—reference implementation wraps this in a transport API):

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

SAE J845 defines flash patterns for emergency vehicle warning lights, with strict timing requirements for visibility and seizure safety. This validation used a tri-color variant: red and blue channels alternating in antiphase (like opposing lightbar sections), plus a shared white channel flashing in-phase on both devices. If alternating signals overlap or synchronized signals desynchronize, the pattern fails.

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

Validation method: 240fps slow-motion video capture (4.17ms per frame). At this frame rate, any timing error would be visible as white desynchronization or glitches during frequency transitions.

### 3.3 The Result

**Zero frames showed white desynchronization. Zero visible glitches during frequency transitions.**

Note: Red/blue "overlap" isn't a meaningful metric here—they're on separate devices and physically cannot overlap. Bilateral synchronization quality is validated separately using a 100% duty cycle alternating pattern where each device is illuminated for its entire phase; any timing error appears as simultaneous illumination or gaps.

The quad flash validation reveals something more subtle: **smooth step-boundary transitions**. When the pattern changes frequency mid-execution, both devices transition cleanly at step boundaries with no visible discontinuity. At 240fps (4.17ms per frame), frequency changes appear instantaneous.

This validates:
1. **Step-boundary architecture works**: Pattern changes execute at deterministic boundaries, not arbitrary moments
2. **Frequency transitions appear instant**: Mode changes in therapeutic applications (EMDR bilateral stimulation) can switch speeds without perceptible glitches
3. **In-phase coordination is precise**: White channel lock across devices confirms sub-frame synchronization
4. **Zone assignment works correctly**: Identical firmware, different runtime behavior based on role

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

**Distributed IMU from ranging geometry**: With 3+ nodes ranging to each other, the swarm gains 6-DOF orientation sensing without per-node IMUs:
- **Translation**: Swarm centroid moves
- **Rotation**: Inter-node angles change  
- **Scale**: All distances shift proportionally

A per-node 6-axis IMU (e.g., Seeed XIAO MG24 Sense) adds ~$5-8 per device. Ranging geometry provides equivalent swarm-level orientation for the cost of the ranging capability you already need. For budget-constrained projects—high school robotics teams, community safety initiatives—this tradeoff matters. The $5 saved per node is another node in the swarm.

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

### 4.4 IMU-Augmented Positioning (Hardware Option)

RFIP using 802.11mc ranging provides position but not orientation. Adding a 6-axis IMU (accelerometer + gyroscope) enables:

- **Reflection ambiguity resolution**: RFIP's distance-only geometry has a mirror ambiguity—the swarm could be "flipped." Gravity vector from accelerometer defines "down," resolving which solution is correct.
- **Dead reckoning between ranging updates**: FTM exchanges take time. IMU provides continuous position estimates during gaps via inertial navigation.
- **Orientation awareness**: Ranging tells you *where* you are relative to peers. IMU tells you *which way you're facing*. Search patterns require both.
- **Motion state detection**: Ranging accuracy differs when stationary vs. moving. IMU provides immediate motion classification.

**Hardware example**: Adding a 6-axis IMU (e.g., MPU6050, ~$2) to ESP32-C6 provides inertial sensing. Alternatively, integrated boards like Seeed XIAO MG24 Sense (~$15, Silicon Labs platform) include IMU on-board—though this requires porting UTLP from ESP-IDF. The architecture is platform-agnostic; the primitives work on any microcontroller with suitable RF capabilities.

**Design tradeoff**: For bilateral EMDR devices (stationary during use, only 2 nodes, known left/right assignment), IMU is unnecessary cost. For mobile swarms doing search patterns, IMU becomes valuable. The architecture supports both—IMU data feeds into the same RFIP coordinate system when available.

### 4.5 SMSP (Synchronized Multimodal Score Protocol)

While UTLP provides *when* and RFIP provides *where*, SMSP defines *what*: the format for describing synchronized actuator behavior across any number of channels and modalities.

#### 4.5.1 The Three-Layer Architecture

SMSP separates human intent from machine execution:

```
┌─────────────────────────────────────────────────────────────┐
│  DECLARATIVE LAYER (Human Intent)                           │
│  "Alternate left/right at 1Hz with 50% duty cycle"          │
│  "SAE J845 Quad Flash pattern"                              │
│  "Binary star wobble with golden ratio orbit"               │
├─────────────────────────────────────────────────────────────┤
│  COMPILER LAYER (PWA / Configuration Tool)                  │
│  Transforms intent into timeline of discrete events         │
│  Validates parameters, calculates phase offsets             │
├─────────────────────────────────────────────────────────────┤
│  IMPERATIVE LAYER (Score + Playback Engine)                 │
│  Sequence of: "At time T, set channel C to state S"         │
│  Engine only knows: current time, current segment, outputs  │
└─────────────────────────────────────────────────────────────┘
```

This separation means:
- **Firmware stays simple**: The playback engine is "dumb"—it reads the timeline, interpolates between keyframes, sets outputs. No waveform math, no frequency calculation.
- **Complexity lives in the compiler**: The PWA or configuration tool can be updated without touching firmware.
- **Advanced users can bypass**: Raw timelines can be authored directly for patterns the compiler doesn't anticipate.

#### 4.5.2 The Score Line Primitive

The fundamental unit is a **score line**: a specification of actuator state at a point in time.

```c
typedef struct {
    uint32_t time_offset_ms;    // When (relative to score start or previous segment)
    uint16_t transition_ms;     // Interpolation duration to reach this state
    uint8_t  flags;             // EASE_IN, EASE_OUT, SYNC_POINT, etc.
    uint8_t  waveform;          // CONSTANT, SINE, RAMP, PULSE (for audio/haptic)
    
    // Per-channel state (example: bilateral device)
    uint8_t  L_r, L_g, L_b;     // Left LED RGB (0-255)
    uint8_t  L_brightness;      // Left LED master brightness
    uint8_t  L_motor;           // Left haptic intensity
    uint8_t  R_r, R_g, R_b;     // Right LED RGB
    uint8_t  R_brightness;      // Right LED master brightness
    uint8_t  R_motor;           // Right haptic intensity
    
    // Audio channels (if present)
    uint16_t L_audio_freq_hz;   // Left audio frequency (synthesized, not sampled)
    uint8_t  L_audio_amplitude; // Left audio amplitude
    uint16_t R_audio_freq_hz;   // Right audio frequency
    uint8_t  R_audio_amplitude; // Right audio amplitude
} score_line_t;

typedef struct {
    uint8_t       line_count;
    uint8_t       loop_point;     // Which line to jump to on completion (0xFF = stop)
    uint8_t       pattern_class;  // BILATERAL, EMERGENCY, SWARM, CUSTOM
    score_line_t  lines[];
} score_t;
```

The structure above is illustrative; implementations may optimize for their specific channel configuration. The key properties are:

1. **Time-indexed**: Each line specifies *when*, not *what frequency*—frequency is implicit in line spacing
2. **Transition-aware**: Interpolation duration is explicit, enabling smooth crossfades
3. **Modality-agnostic**: LED, haptic, audio are parallel channels in the same timeline
4. **Zone-agnostic**: Score describes one node's behavior; zone assignment determines which score (or score variant) each node plays

#### 4.5.3 Pattern Classification

Scores carry metadata indicating their pattern class:

```c
typedef enum {
    PATTERN_BILATERAL,      // Antiphase pair, therapeutic applications
    PATTERN_EMERGENCY,      // SAE J845 compliant, warning applications
    PATTERN_SWARM_SYNC,     // In-phase coherence, mutual visibility
    PATTERN_PURSUIT,        // Sequential activation around geometry
    PATTERN_BINARY_ORBIT,   // Wobble + rotation composite
    PATTERN_CUSTOM          // Raw timeline, no assumptions
} pattern_class_t;
```

Classification enables:
- UI hints ("this is a bilateral pattern, show left/right preview")
- Validation ("emergency patterns must meet SAE J845 timing")
- Optimization ("bilateral patterns can use simpler zone logic")

#### 4.5.4 Scale Invariance

The same score format applies regardless of physical scale:

| Scale | Zones Are | Transport | Example |
|-------|-----------|-----------|---------|
| **PCB** | GPIO pins | Direct register write | RGB LEDs on one board |
| **Device** | Peer MAC addresses | ESP-NOW | Bilateral handhelds |
| **Room** | Node positions | ESP-NOW / WiFi | Warning light array |
| **Field** | Drone IDs | ESP-NOW / custom RF | Search and rescue swarm |

A score written for three LEDs on a PCB plays identically on three drones 100 meters apart. The playback engine doesn't know or care about physical spacing—it only knows time and channels.

#### 4.5.5 Transport Agnosticism

SMSP defines the score format, not the delivery mechanism:

- **ESP-NOW**: Peer-to-peer wireless, used during configuration phase
- **BLE**: Alternative transport for PWA-to-device score upload
- **Wired bus**: UART/I2C/SPI for conductor-to-node in fixed installations
- **Flash at build time**: Score baked into firmware for dedicated-function devices

The protocol is complete when a node possesses:
1. A score (however delivered)
2. A time reference (however synchronized via UTLP)
3. Knowledge of its zone (however assigned, potentially via RFIP ranging)

#### 4.5.6 Minimal Engine Requirements

The playback engine requires only:

```c
while (running) {
    uint32_t now = get_synchronized_time_ms();
    
    if (now >= current_segment->time_offset_ms + transition_end) {
        advance_to_next_segment();
    }
    
    float progress = calculate_eased_progress(now, current_segment);
    
    for (each channel) {
        output[channel] = interpolate(
            previous_state[channel],
            current_segment->state[channel],
            progress
        );
    }
    
    apply_outputs();
}
```

This runs on an 8-bit microcontroller. An ATtiny85 ($0.50) can execute SMSP scores; the ESP32-C6 ($5) is only required for wireless bootstrap and UTLP time synchronization. For wired or pre-configured deployments, a "smart" conductor node handles sync while "dumb" nodes only play scores.

#### 4.5.7 Relationship to Existing Standards

| Standard | What It Does | SMSP Difference |
|----------|--------------|-----------------|
| **DMX512** | 512 channels, wired, master broadcasts continuously | SMSP: score uploaded once, nodes execute independently |
| **MIDI** | Note events, primarily musical timing | SMSP: continuous interpolated states, sub-millisecond sync |
| **SMPTE** | Timecode for film sync, devices chase master | SMSP: devices agree on time then execute autonomously |
| **OSC** | Real-time control messages over network | SMSP: score is complete before execution, no runtime traffic |
| **Art-Net** | DMX over Ethernet, still continuous broadcast | SMSP: connectionless during execution |

SMSP combines:
- DMX's channel abstraction
- MIDI's event timing
- SMPTE's frame accuracy
- OSC's flexibility

...while eliminating:
- Continuous network traffic during execution
- Central controller as single point of failure
- Wired infrastructure requirements
- Per-node cost barriers (runs on $0.50 MCU)

#### 4.5.8 The Protocol Family

UTLP, RFIP, and SMSP together form a complete primitive for distributed synchronized actuation:

| Protocol | Question | Answer |
|----------|----------|--------|
| **UTLP** | When is it? | Synchronized time across all nodes |
| **RFIP** | Where am I? | Relative position from peer ranging |
| **SMSP** | What do I do? | Score-based multimodal actuation |

Any node with answers to these three questions can participate in coordinated behavior without ongoing communication during execution.

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

**Swarm Form Factors**: Coordinated node networks are not limited to mobile robots. The architecture covers three instantiation categories:

| Form Factor | Locomotion | Platform | Example |
|-------------|------------|----------|---------|
| **Wearable swarm** | Person provides | Body-mounted | Bilateral EMDR pulsers, rescue worker trackers |
| **Fixed swarm** | None | Stationary | Warning lights on poles, building evacuation beacons |
| **Mobile swarm** | Self-propelled | Autonomous | Aerial drones, ground robots, autonomous vehicles |

All three share the same timing and coordination architecture—UTLP synchronization, pattern scripts, peer ranging. Locomotion is simply another actuator channel: some nodes have it, some don't.

**Terminology note**: The distinction is *agency*, not form factor. A *drone* is an independent agent acting on your behalf. A *wearable* extends the person wearing it—the person remains the agent. Both participate identically in swarm coordination.

The architecture requires only: radio and time sync participation. Nodes may be stationary, worn, or mobile.

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

### 5.8 Distributed Wave Beamforming

**The Physics**: Beamforming is not about creating more energy—it redistributes energy spatially. By altering the timing (phase) of multiple emitters, waves arrive at a target point in sync (constructive interference) while arriving out of sync elsewhere (destructive interference). The "beam" is a region of reinforcement.

**The Timing Relationship**: Beamforming requires phase coherence—emitters synchronized to a fraction of the wave period. The fraction determines beam quality; typically <10% of period for useful steering.

| Domain | Wavelength | Period | Required Sync | ESP32 Capable? |
|--------|-----------|--------|---------------|----------------|
| Acoustic 1kHz | 34 cm | 1 ms | ~100 μs | ✓ |
| Ultrasonic 40kHz | 8.5 mm | 25 μs | ~2.5 μs | Marginal |
| RF 2.4GHz | 12.5 cm | 0.4 ns | ~40 ps | ✗ |
| Optical 600THz | 500 nm | 1.7 fs | ~170 as | ✗ |

**The Architecture Is Domain-Invariant**: UTLP's ±30μs synchronization is 3% of a 1ms acoustic period—sufficient for beam steering. The same architecture with picosecond-capable hardware (FPGA, SDR) addresses RF. **The protocol doesn't change; only the clock determines the applicable domain.**

**RFIP Feeds the Math**: Beam steering requires knowing inter-node distances. For a linear array steering to angle θ with node spacing d:

```
delay_n = (n × d × sin(θ)) / v

Where:
  n = node index (0, 1, 2...)
  d = inter-node spacing (from RFIP ranging)
  θ = target steering angle
  v = wave velocity (343 m/s for sound, 3×10⁸ m/s for RF)
```

RFIP's peer ranging provides d directly. No pre-surveyed array geometry required—the swarm measures itself.

**SMSP Carries the Phase Offsets**: Beam steering compiles to per-node time delays in the score:

```c
// PWA/Compiler calculates offsets for 45° steering, 10cm spacing
// delay_n = (n × 0.10m × sin(45°)) / 343 m/s
// Node 0: 0 μs, Node 1: 206 μs, Node 2: 412 μs, Node 3: 618 μs

score_line_t beam_45deg[] = {
    { .zone = 0, .time_offset_ms = 0,   .L_audio_freq_hz = 1000 },
    { .zone = 1, .time_offset_ms = 0,   .start_delay_us = 206, .L_audio_freq_hz = 1000 },
    { .zone = 2, .time_offset_ms = 0,   .start_delay_us = 412, .L_audio_freq_hz = 1000 },
    { .zone = 3, .time_offset_ms = 0,   .start_delay_us = 618, .L_audio_freq_hz = 1000 },
};
```

The nodes execute independently. The beam emerges from synchronized phase relationships.

**Dynamic Steering**: Changing beam direction requires only a new score. The execution model is unchanged—nodes receive updated phase offsets, execute locally, new beam direction emerges. No architectural changes for scanning, tracking, or multi-beam patterns.

**Enclosure Effects as Radome Simulation**: In the reference implementation, speakers are mounted inside plastic enclosures (EMDR handles). The enclosure modifies acoustic response—internal reflections, phase distortion, directivity changes. This is not a limitation; it's a **high-fidelity simulation of radome interaction** in real RF systems. Putting radar inside an aircraft nose cone creates identical phenomena: antenna detuning, boresight error, sidelobe distortion. The acoustic prototype exercises the same compensation algorithms needed for aerospace deployment.

**Application Domains** (architecture identical, timing hardware varies):

| Application | Domain | Hardware | Status |
|-------------|--------|----------|--------|
| Directional alerts | Acoustic | ESP32 + speaker | Achievable now |
| Parametric audio | Ultrasonic | ESP32 + transducer array | Marginal now |
| Sonar/echolocation | Ultrasonic | ESP32 + transducer | Marginal now |
| Directed comms | RF | FPGA/SDR | Architecture ready |
| Synthetic aperture | RF | FPGA/SDR | Architecture ready |
| Jamming/nulling | RF | FPGA/SDR | Architecture ready |

**The Validation Path**: Acoustic beamforming with ESP32 proves the distributed control logic at human-observable timescales. The architecture is identical for RF—only the timing hardware changes. Successfully steering a 1kHz acoustic beam validates that the UTLP/RFIP/SMSP stack can steer a 2.4GHz RF beam when instantiated on appropriate silicon.

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
4. **Power efficiency**: When everyone has the same script, radio silence until something changes
5. **Phone compatibility preserved**: BLE handles the user-facing interface; ESP-NOW handles peer coordination

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

**Hardware requirements (minimum):**
- ESP32-C6 (recommended) or ESP32-S3/C3: ~$5-8
- Standard BLE and WiFi capabilities
- No specialized timing hardware required
- **Total BOM for bilateral device: under $15/node**

**Hardware options (enhanced capabilities):**
- Seeed XIAO MG24 Sense (~$15): Adds 6-axis IMU for orientation/dead reckoning
- ESP32-C6 v0.2+ silicon: Enables FTM initiator role (earlier revisions: responder only)
- External GPS module: Stratum 0 time source for outdoor applications

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

30. **Distributed IMU from ranging geometry**: 3+ nodes with peer ranging provide 6-DOF swarm orientation (translation, rotation, scale) without per-node inertial sensors—the swarm's geometry is itself an inertial reference

31. **IMU-augmented peer ranging**: Combining 802.11mc FTM with per-node inertial measurement for reflection ambiguity resolution, dead reckoning between ranging updates, and orientation awareness in mobile swarms

32. **Connection-oriented sync bootstrapping connectionless execution**: Using PTP/NTP-style timestamp exchange over connection-oriented transports (BLE, WiFi, etc.) to establish a persistent time reference that outlives the connection—the sync method is scaffolding, removed after use, while the time agreement enables indefinite connectionless coordination

### 9.6 Score Protocol Techniques (SMSP)

33. **Three-layer score architecture**: Separating declarative intent (human-readable parameters), compiler layer (PWA/tool transforming intent to timeline), and imperative execution (dumb engine playing time-indexed events)

34. **Time-indexed score format**: Defining actuator state at absolute/relative timestamps rather than frequencies—frequency becomes implicit in timeline spacing, eliminating runtime waveform calculation

35. **Transition-aware keyframes**: Score lines include interpolation duration and easing specification, enabling smooth crossfades as first-class operations rather than engine complexity

36. **Multimodal channel abstraction**: LED RGB, brightness, haptic intensity, audio frequency/amplitude as parallel channels in unified timeline—modality is a channel property, not a protocol distinction

37. **Pattern classification metadata**: Score-level enum (BILATERAL, EMERGENCY, SWARM_SYNC, PURSUIT, CUSTOM) enabling UI hints, validation rules, and zone logic optimization without parsing the timeline

38. **Scale-invariant score execution**: Identical score format from PCB-mounted LEDs (zones = GPIO pins) to field-deployed swarms (zones = node IDs)—playback engine unaware of physical scale

39. **Transport-agnostic score delivery**: Score format independent of delivery mechanism (ESP-NOW, BLE, wired bus, flash-at-build-time)—protocol complete when node has score + time + zone

40. **8-bit capable score engine**: Playback loop (time check → segment advance → interpolate → output) simple enough for ATtiny-class MCUs; wireless sync capability determines cost, not execution capability

41. **Conductor/performer topology**: Single "smart" node handles UTLP sync and score distribution; multiple "dumb" nodes execute scores with minimal hardware—enables $0.50 per additional node in wired deployments

42. **Synthesized audio as score channel**: Audio frequency and amplitude as score parameters for real-time synthesis (no sample storage), enabling binaural/bilateral audio patterns with same connectionless execution model

### 9.7 Wave Domain Techniques (Beamforming)

43. **Distributed beamforming via connectionless phase coordination**: Nodes with synchronized time and known geometry execute scores containing per-node phase offsets, enabling steered wave emission without real-time coordination during transmission

44. **Domain-invariant phased array architecture**: Same UTLP/RFIP/SMSP stack applies from acoustic (ms periods, MCU-achievable) to RF (ns periods, FPGA-required)—architecture unchanged, timing precision determines applicable domain

45. **Swarm geometry feeding beam steering calculations**: RFIP-derived inter-node distances as direct input to phase offset computation (delay = n×d×sin(θ)/v), eliminating pre-surveyed array geometry requirements

46. **Phase offset as SMSP score parameter**: Beam steering angles compiled to per-node microsecond delays, distributed as standard score timing, executed via normal connectionless playback

47. **Dynamic beam steering via score update**: Changing target bearing requires only new score distribution, not architectural modification—same connectionless execution model for fixed, scanning, or tracking beams

48. **Acoustic validation of RF-applicable architecture**: Proving distributed phase coordination at human-observable timescales (kHz acoustic) to validate control logic for RF timescales (GHz)—architecture identical, only clock hardware differs

49. **Enclosure acoustic effects as radome simulation**: Structural acoustic non-idealities (phase distortion, directivity modification, internal reflections) modeling RF antenna detuning, body shadowing, and boresight error in aerospace deployments

### 9.8 Implementation Philosophy

50. **Score generation method independence**: Score authoring by any means—manual, algorithmic, AI/LLM-assisted, or real-time sensor-driven compilation—is implementation detail; the protocol and execution model are the contribution, not the generation method

---

## 10. Conclusion

The connectionless distributed timing architecture demonstrates that many coordination problems have simpler solutions than traditionally assumed. By separating configuration from execution, and by treating synchronized time as foundational rather than incidental, we eliminate entire categories of complexity.

The techniques documented here are not limited by technology—the hardware has existed for years. They were limited by recognition: that pattern playback is already connectionless, that BLE and ESP-NOW can coexist with each handling what it does best, that the "$5 saved per node is another node in the swarm."

By publishing this work as prior art, we ensure these techniques remain freely available. Technology that assumes cooperation rather than extraction.

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-23 | Initial defensive publication |
| 1.1 | 2025-12-23 | Added defense-in-depth security architecture, HKDF selection rationale, multi-layer replay protection, threat-proportional design philosophy; clarified BLE Bootstrap Model with peer release |
| 1.2 | 2025-12-23 | Added GPS-denied search and rescue with self-mapping patterns |
| 1.3 | 2025-12-23 | Added distributed IMU from ranging geometry—swarm orientation without per-node inertial sensors |
| 1.4 | 2025-12-23 | Rewrote Section 1 to reflect actual development history: pattern playback existed from day one, BLE worked, ESP-NOW chosen because hardware was available and it's better; added power efficiency rationale |
| 1.5 | 2025-12-23 | Added BLE sync implementation details: PTP-style with NTP timestamps, ~2 minute convergence validated via serial logs; reframed prior art claim to capture the actual contribution (connection as scaffolding for persistent time reference) |
| 1.6 | 2025-12-23 | Added IMU-augmented positioning option, hardware cost breakdown |
| 1.7 | 2025-12-24 | Added SMSP (Synchronized Multimodal Score Protocol) as Section 4.5—defines score format, three-layer architecture (declarative/compiler/imperative), scale and transport invariance; added 10 SMSP-specific prior art claims (33-42) |
| 1.8 | 2025-12-24 | Added distributed wave beamforming (Section 5.8)—acoustic demo proving domain-invariant phased array architecture; RFIP geometry feeding phase offset math; enclosure effects as radome simulation; 8 new prior art claims (43-50) covering beamforming and generation method independence |

---

## References

### Project Documentation
1. UTLP Technical Report v2.0, mlehaptics Project, December 2025
2. UTLP Addendum A: Reference-Frame Independent Positioning, December 2025
3. UTLP Technical Supplement S1: Precision, Transport, and Security Extensions, December 2025
4. Advanced Architectural Analysis: Bilateral Pattern Playback Systems, mlehaptics Project, December 2025
5. Emergency Vehicle Light Sync: Proven Architectures for ESP32 Adaptation, mlehaptics Project, December 2025
6. 802.11mc FTM Reconnaissance Report, mlehaptics Project, December 2025
7. Technical Note: Distributed Acoustic Beamforming ("The Slow-Motion Death Star"), mlehaptics Project, December 2025

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
16. N. Meyer (dir.), "Star Trek II: The Wrath of Khan," Paramount Pictures, 1982. (Kobayashi Maru scenario: the insight that "unwinnable" tests can be beaten by changing their preconditions—see [14])

---

## Acknowledgments

This work emerged from collaborative development combining human domain expertise with AI assistance:

- **Steve (mlehaptics)**: Architecture design, hardware implementation, "Time as Public Utility" philosophy, Glass Wall architecture, validation methodology, therapeutic domain expertise

- **Claude (Anthropic)**: Literature survey, protocol analysis, documentation compilation, prior art framing, SMSP formalization, application brainstorming

- **Gemini (Google)**: Acoustic beamforming connection—recognizing that UTLP's timing precision enables phased array demonstrations at acoustic wavelengths

---

## Intellectual Property Statement

This document is published as **open-source prior art** under Creative Commons CC0 (public domain dedication) for the architectural concepts, and MIT license for reference implementations.

The authors explicitly disclaim any patent rights to the techniques described herein and publish this document to establish prior art, ensuring these methods remain freely available for public use without licensing requirements or restrictions.

**First Published**: December 23, 2025

**Repository**: github.com/mlehaptics

---

*— End of Document —*
