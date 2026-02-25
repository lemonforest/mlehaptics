# SMSP Technical Specification

## Synchronized Multimodal Score Protocol

**Version:** 2.0 (Vector Time Integration)  
**Status:** Draft / Experimental  
**Parent Document:** Connectionless Distributed Timing Prior Art (DOI: 10.5281/zenodo.18078264)  
**Repository:** https://github.com/lemonforest/mlehaptics

---

## Abstract

SMSP (Synchronized Multimodal Score Protocol) defines *what* synchronized nodes do, completing the protocol triad with UTLP (*when*) and RFIP (*where*). Version 2.0 integrates with UTLP Vector Time, enabling phase-indexed scores that execute identically across all phase-locked nodes without runtime coordination or start synchronization.

The key insight: **patterns are deterministic functions of phase**. Given the same phase, every node computes the same output. Phases converge automatically via UTLP. Therefore, outputs converge automatically—no "start now" signal required.

---

## 1. Introduction

### 1.1 The Protocol Triad

| Protocol | Question | Direction |
|----------|----------|-----------|
| **UTLP** | When is it? | Broadcast (time source → all) |
| **RFIP** | Where am I? | Peer-to-peer (mutual ranging) |
| **SMSP** | What do I do? / What did I see? | Bidirectional (instructions ↔ observations) |

Any node with synchronized time (UTLP), known position (RFIP), and a score (SMSP) can participate in coordinated behavior.

### 1.2 Design Philosophy

SMSP separates concerns:

```
┌─────────────────────────────────────────────────────────────┐
│  DECLARATIVE LAYER (Human Intent)                           │
│  "Alternate left/right at 1Hz with 50% duty cycle"          │
│  "SAE J845 Quad Flash pattern"                              │
│  "Bilateral EMDR standard protocol"                         │
├─────────────────────────────────────────────────────────────┤
│  COMPILER LAYER (Design Tool / PWA)                         │
│  Transforms intent into phase-indexed events                │
│  Validates parameters, encodes tick → phases                │
├─────────────────────────────────────────────────────────────┤
│  EXECUTION LAYER (Score + Playback Engine)                  │
│  "When my phases match event phases, execute action"        │
│  Engine only knows: current phases, score, outputs          │
└─────────────────────────────────────────────────────────────┘
```

This separation means:
- **Firmware stays simple**: The playback engine is "dumb"—it matches phases, sets outputs
- **Complexity lives in the compiler**: Updated without touching firmware
- **Advanced users can bypass**: Raw phase-indexed scores can be authored directly

### 1.3 Version History

| Version | Model | Time Representation | Sync Requirement |
|---------|-------|---------------------|------------------|
| 1.0 | Imperative | Scalar ticks | Explicit start signal |
| **2.0** | **Declarative** | **Phase vector** | **None (auto-converge)** |

---

## 2. Core Concepts

### 2.1 The Paradigm Shift: Scalar vs Vector Time

**Scalar Time (v1.0):**
```c
// "At tick 1000, turn LED on"
if (current_tick == 1000) {
    led_on();
}
```

Problem: Requires all nodes to agree on absolute tick count. Needs start synchronization.

**Vector Time (v2.0):**
```c
// "When phases are [35, 246, 44, 68, 84, 92, 108, 156], turn LED on"
if (phases_match(my_phases, event_phases)) {
    led_on();
}
```

Advantage: Phases converge automatically. No start signal needed.

### 2.2 Why This Works

```
Device A: powered on at arbitrary time, counts ticks, broadcasts phases
Device B: powered on later, counts ticks, hears A's beacon, nudges toward A
Device C: powered on even later, hears both, nudges toward consensus

After a few beacon cycles: all devices have same phases
                          WITHOUT agreeing on "what tick is it"

Same phases → same score position → same output
```

The pattern becomes a **pure function of phase**. Sync the phases (UTLP does this automatically), and the outputs sync automatically.

### 2.3 Encoding: Tick Space → Phase Space

Patterns are designed in tick-space (human-intuitive), compiled to phase-space (machine-executable):

```python
# Human writes this:
pattern = [
    { "tick": 0,   "led": ON  },
    { "tick": 100, "led": OFF },
    { "tick": 200, "led": ON  },
    { "tick": 300, "led": OFF },
]

# Compiler generates this:
PRIMES = [241, 251, 239, 233, 229, 227, 223, 211]

compiled = [
    { "phases": [0 % p for p in PRIMES],   "led": ON  },   # [0,0,0,0,0,0,0,0]
    { "phases": [100 % p for p in PRIMES], "led": OFF },   # [100,100,100,100,100,100,100,100]
    { "phases": [200 % p for p in PRIMES], "led": ON  },   # [200,200,200,200,200,200,200,200]
    { "phases": [300 % p for p in PRIMES], "led": OFF },   # [59,49,61,67,71,73,77,89]
]
```

**Encoding is trivial**: `phase[i] = tick % prime[i]`

**No CRT at runtime**: Just compare 8 bytes per event.

---

## 3. Score Format

### 3.1 Phase-Indexed Event (v2.0)

```c
typedef struct {
    // Phase coordinates (when to execute)
    uint8_t phases[8];          // Target phase for each prime
    uint8_t phase_mask;         // Which phases must match (0xFF = all)
    
    // Transition
    uint8_t transition_ticks;   // Interpolation duration (in pattern ticks)
    uint8_t easing;             // EASE_LINEAR, EASE_IN, EASE_OUT, EASE_INOUT
    
    // Output state
    uint8_t channels[];         // Variable-length channel state array
} smsp_event_v2_t;
```

### 3.2 Single-Phase Optimization

For patterns fitting within one prime cycle (≤241 ticks at smallest prime):

```c
typedef struct {
    uint8_t phase;              // Single phase value (prime index 0)
    uint8_t transition_ticks;
    uint8_t channels[];
} smsp_event_simple_t;
```

Runtime check becomes **one byte comparison**.

### 3.3 Region-Based Scores (Declarative)

Instead of discrete events, define continuous regions:

```c
typedef struct {
    uint8_t phase_index;        // Which prime dimension (0-7)
    uint8_t region_start;       // Inclusive start
    uint8_t region_end;         // Exclusive end
    uint8_t channels[];         // State while in this region
} smsp_region_t;

typedef struct {
    uint8_t num_regions;
    smsp_region_t regions[];
} smsp_region_score_t;
```

**Example: Bilateral EMDR with RGB LEDs**
```c
// Channel layout: L_R, L_G, L_B, L_haptic, R_R, R_G, R_B, R_haptic
// Using prime[0] = 241, pattern period = 241 ticks (~241ms at 1ms ticks)

#define LED_OFF     0
#define LED_FULL    255
#define HAPTIC_MED  180

smsp_region_t bilateral_score[] = {
    // Left active: Cyan LED (R=0, G=255, B=255) + haptic
    { .phase_index = 0, .region_start = 0,   .region_end = 120, 
      .channels = { LED_OFF, LED_FULL, LED_FULL, HAPTIC_MED,   // Left: Cyan + haptic
                    LED_OFF, LED_OFF,  LED_OFF,  0 } },         // Right: Off
    
    // Right active: Cyan LED + haptic  
    { .phase_index = 0, .region_start = 120, .region_end = 241,
      .channels = { LED_OFF, LED_OFF,  LED_OFF,  0,             // Left: Off
                    LED_OFF, LED_FULL, LED_FULL, HAPTIC_MED } } // Right: Cyan + haptic
};
```

Every node with phase[0] ∈ [0,120) outputs LEFT active. Every node with phase[0] ∈ [120,241) outputs RIGHT active. **No coordination message needed.**

### 3.4 Score Container

```c
typedef struct {
    // Header
    uint8_t  version;           // SMSP_VERSION_2
    uint8_t  format;            // FORMAT_EVENTS | FORMAT_REGIONS | FORMAT_SIMPLE
    uint8_t  pattern_class;     // BILATERAL, EMERGENCY, SWARM, CUSTOM
    uint8_t  prime_config;      // Which prime set (standard, fine, custom)
    
    // Timing
    uint8_t  tick_period_log2;  // Tick period = 2^N microseconds (0=1μs, 10=1ms)
    uint8_t  pattern_prime_idx; // Which prime defines pattern period (0-7)
    
    // Loop control
    uint8_t  loop_count;        // 0 = infinite, N = play N times
    uint8_t  loop_point;        // Event/region index to loop back to
    
    // Channel configuration
    uint8_t  num_channels;
    uint8_t  channel_types[];   // LED_RGB, LED_MONO, HAPTIC, AUDIO_FREQ, etc.
    
    // Score data
    uint16_t data_length;
    uint8_t  data[];            // Events or regions, format-dependent
} smsp_score_t;
```

---

## 4. Playback Engine

### 4.1 Minimal Implementation (Region-Based)

```c
void smsp_tick(smsp_engine_t* engine) {
    uint8_t phase = engine->current_phases[engine->score->pattern_prime_idx];
    
    for (int i = 0; i < engine->score->num_regions; i++) {
        smsp_region_t* r = &engine->score->regions[i];
        
        if (phase >= r->region_start && phase < r->region_end) {
            apply_channels(r->channels, engine->score->num_channels);
            return;
        }
    }
}
```

**This runs on an ATtiny85.** The ESP32-C6 is only needed for wireless bootstrap and UTLP phase synchronization.

### 4.2 Event-Based Implementation

```c
void smsp_tick(smsp_engine_t* engine) {
    // Check if current phases match any event
    for (int i = 0; i < engine->score->num_events; i++) {
        smsp_event_v2_t* e = &engine->score->events[i];
        
        if (phases_match(engine->current_phases, e->phases, e->phase_mask)) {
            // Start transition to this event's state
            engine->target_state = e->channels;
            engine->transition_remaining = e->transition_ticks;
            engine->easing = e->easing;
            return;
        }
    }
    
    // Continue any active transition
    if (engine->transition_remaining > 0) {
        interpolate_outputs(engine);
        engine->transition_remaining--;
    }
}

bool phases_match(uint8_t* current, uint8_t* target, uint8_t mask) {
    for (int i = 0; i < 8; i++) {
        if ((mask & (1 << i)) && current[i] != target[i]) {
            return false;
        }
    }
    return true;
}
```

### 4.3 Integration with UTLP Vector Time

```c
// UTLP callback - called every tick
void utlp_on_tick(uint8_t* phases) {
    // Update engine's phase view
    memcpy(smsp_engine.current_phases, phases, 8);
    
    // Execute score
    smsp_tick(&smsp_engine);
}

// UTLP callback - called when beacon received
void utlp_on_beacon(uint8_t* peer_phases) {
    // UTLP handles phase nudging internally
    // SMSP doesn't need to know about sync mechanics
}
```

**Key insight**: SMSP doesn't manage time. It receives phases from UTLP and reacts. The sync is invisible to the score engine.

---

## 5. Pattern Compiler

### 5.1 Compilation Pipeline

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Human Intent   │────▶│    Compiler     │────▶│  Binary Score   │
│  (JSON/YAML)    │     │  (PWA/CLI)      │     │  (Flash/OTA)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
  "1Hz bilateral"      tick→phase encode        smsp_score_t
  "SAE J845 quad"      validation               ready for MCU
  "custom timeline"    optimization
```

### 5.2 Intent Format (Input)

```yaml
# bilateral_1hz.smsp.yaml
name: "Bilateral 1Hz"
class: bilateral
tick_period_us: 1000    # 1ms ticks
pattern_period_ms: 1000 # 1 second cycle

channels:
  - name: left_led
    type: led_mono
  - name: right_led  
    type: led_mono
  - name: left_haptic
    type: haptic
  - name: right_haptic
    type: haptic

regions:
  - name: left_active
    start_ms: 0
    end_ms: 500
    state:
      left_led: 255
      right_led: 0
      left_haptic: 200
      right_haptic: 0
      
  - name: right_active
    start_ms: 500
    end_ms: 1000
    state:
      left_led: 0
      right_led: 255
      left_haptic: 0
      right_haptic: 200
```

### 5.3 Compilation Process

```python
def compile_score(intent):
    # 1. Select prime configuration
    primes = select_primes(intent.pattern_period_ms, intent.tick_period_us)
    
    # 2. Calculate pattern period in ticks
    period_ticks = intent.pattern_period_ms * 1000 // intent.tick_period_us
    
    # 3. Find best-fit prime for pattern period
    pattern_prime_idx = find_closest_prime(period_ticks, primes)
    pattern_prime = primes[pattern_prime_idx]
    
    # 4. Scale regions to fit prime
    scale = pattern_prime / period_ticks
    
    # 5. Convert regions
    compiled_regions = []
    for region in intent.regions:
        start_tick = region.start_ms * 1000 // intent.tick_period_us
        end_tick = region.end_ms * 1000 // intent.tick_period_us
        
        compiled_regions.append({
            'phase_index': pattern_prime_idx,
            'region_start': int(start_tick * scale) % pattern_prime,
            'region_end': int(end_tick * scale) % pattern_prime,
            'channels': encode_channels(region.state, intent.channels)
        })
    
    # 6. Package into score container
    return smsp_score_t(
        version=2,
        format=FORMAT_REGIONS,
        pattern_class=intent.class,
        prime_config=PRIMES_STANDARD,
        pattern_prime_idx=pattern_prime_idx,
        regions=compiled_regions
    )
```

### 5.4 Prime Selection Strategy

> **Design Note:** Prime selection is a **compiler responsibility**, not an engine responsibility. The playback engine on the MCU is intentionally "dumb"—it only matches phases and sets outputs. All the intelligence about selecting optimal primes, scaling patterns, and handling edge cases lives in the PWA/CLI compiler that runs on a more capable device (phone, laptop). This keeps the embedded firmware simple, deterministic, and portable across MCU architectures.

| Pattern Period | Recommended Prime | Fit Error |
|----------------|-------------------|-----------|
| ~211 ticks | 211 | Exact |
| ~223 ticks | 223 | Exact |
| ~227 ticks | 227 | Exact |
| ~229 ticks | 229 | Exact |
| ~233 ticks | 233 | Exact |
| ~239 ticks | 239 | Exact |
| ~241 ticks | 241 | Exact |
| ~251 ticks | 251 | Exact |
| ~500 ticks | 251 × 2 | Use dual-phase |
| ~1000 ticks | 251 × 4 | Use dual-phase |
| Arbitrary | Use mask | Match subset of phases |

**Compiler Algorithm:**
1. Calculate desired pattern period in ticks
2. Find the prime closest to that period
3. Scale pattern timing to fit the selected prime
4. Encode scaled timing into phase values
5. Store selected prime index in score header

For patterns that don't fit a single prime, use **phase masking** to match only relevant phases, or use **CRT tick recovery** at the cost of more computation.

---

## 6. Pattern Classes

### 6.1 Classification Enum

```c
typedef enum {
    PATTERN_BILATERAL,      // Antiphase pair (EMDR, tDCS)
    PATTERN_EMERGENCY,      // SAE J845 compliant (lightbars)
    PATTERN_SWARM_SYNC,     // In-phase coherence (mutual visibility)
    PATTERN_PURSUIT,        // Sequential chase (around geometry)
    PATTERN_BINARY_ORBIT,   // Wobble + rotation composite
    PATTERN_SENSING,        // Coordinated sampling schedule
    PATTERN_CUSTOM          // Raw score, no assumptions
} pattern_class_t;
```

### 6.2 Bilateral Patterns

**Characteristics:**
- Two zones (LEFT, RIGHT)
- Antiphase operation (when LEFT is active, RIGHT is inactive)
- Typically therapeutic (EMDR, bilateral stimulation)

**Constraints:**
- Duty cycle should sum to ≤100%
- Frequency range: 0.5-2 Hz typical for EMDR

**Example with RGB LEDs:**
```c
// 1Hz bilateral, 50% duty cycle each side
// Pattern period fits prime[0] = 241 ticks (~241ms at 1ms ticks)
// Channel layout: L_R, L_G, L_B, L_haptic, R_R, R_G, R_B, R_haptic

smsp_region_t bilateral[] = {
    // Left active: Soft blue LED + haptic buzz
    { 0, 0, 120,   { 0, 100, 255, 180,    // Left: Blue-ish, haptic on
                    0, 0,   0,   0   } }, // Right: Off
    // Right active: Soft blue LED + haptic buzz                
    { 0, 120, 241, { 0, 0,   0,   0,      // Left: Off
                    0, 100, 255, 180 } }  // Right: Blue-ish, haptic on
};
```

### 6.3 Emergency Patterns (SAE J845)

**Characteristics:**
- Flash rate: 1.0 - 4.0 Hz
- Dark interval: ≥160 ms between flash bursts
- Pulse train: pulses within burst start ≤100 ms apart
- SAE J845 Class 1 for high-visibility roadway applications

**Police Lightbar Example (Red/Blue/White):**

Typical police lightbar configuration: Red on driver's side, Blue on passenger side, White for takedowns/pursuit. Pattern alternates colors for maximum visibility—each color flash ensures optimal wavelength is visible regardless of ambient lighting conditions.

```c
// SAE J845 Quad Flash with Red/Blue alternating + White accent
// At 1ms ticks: 250 ticks per cycle (4Hz), use prime[7] = 251
// Channel layout: L_R, L_G, L_B, R_R, R_G, R_B (Left RGB, Right RGB)

#define RED_FULL    {255, 0,   0  }   // Red: high daytime visibility
#define BLUE_FULL   {0,   0,   255}   // Blue: high nighttime visibility  
#define WHITE_FULL  {255, 255, 255}   // White: pursuit/takedown flash
#define LED_OFF     {0,   0,   0  }

smsp_region_t police_lightbar[] = {
    // Phase 1: Left RED quad flash
    { 7, 0,   10,  { 255,0,0, 0,0,0 } },     // L=RED, R=OFF
    { 7, 10,  20,  { 0,0,0,   0,0,0 } },     // Gap
    { 7, 20,  30,  { 255,0,0, 0,0,0 } },     // L=RED
    { 7, 30,  40,  { 0,0,0,   0,0,0 } },     // Gap
    { 7, 40,  50,  { 255,0,0, 0,0,0 } },     // L=RED
    { 7, 50,  60,  { 0,0,0,   0,0,0 } },     // Gap
    { 7, 60,  70,  { 255,0,0, 0,0,0 } },     // L=RED (4th flash)
    
    // Phase 2: Right BLUE quad flash  
    { 7, 70,  80,  { 0,0,0, 0,0,255 } },     // L=OFF, R=BLUE
    { 7, 80,  90,  { 0,0,0,   0,0,0 } },     // Gap
    { 7, 90,  100, { 0,0,0, 0,0,255 } },     // R=BLUE
    { 7, 100, 110, { 0,0,0,   0,0,0 } },     // Gap
    { 7, 110, 120, { 0,0,0, 0,0,255 } },     // R=BLUE
    { 7, 120, 130, { 0,0,0,   0,0,0 } },     // Gap
    { 7, 130, 140, { 0,0,0, 0,0,255 } },     // R=BLUE (4th flash)
    
    // Phase 3: WHITE pursuit burst (both sides)
    { 7, 140, 150, { 255,255,255, 255,255,255 } },  // Both WHITE
    { 7, 150, 160, { 0,0,0, 0,0,0 } },              // Gap
    { 7, 160, 170, { 255,255,255, 255,255,255 } },  // Both WHITE
    
    // Dark interval (81 ticks = 81ms, satisfies ≥80ms for readability)
    { 7, 170, 251, { 0,0,0, 0,0,0 } },       // Dark period before repeat
};
```

**Pattern Analysis:**
- Total cycle: 251ms (~4Hz flash rate) ✓
- Each quad flash burst: 70ms (4 flashes × 10ms + 3 gaps × 10ms) ✓
- Inter-phase gaps: adequate for color differentiation ✓
- White accent: high-intensity burst attracts attention during pursuit
- Dark interval: 81ms at end provides visual reset

**Color Selection Rationale:**
- **Red** (255,0,0): Superior daytime visibility, traditional "stop" association
- **Blue** (0,0,255): Superior nighttime visibility, reduced eye fatigue
- **White** (255,255,255): Maximum intensity burst, pursuit mode indicator

### 6.4 Sensing Patterns

**Characteristics:**
- Coordinated sampling across distributed nodes
- Timestamps in phase space
- Observations flow back to coordinator

**Example: Acoustic Sampling**
```c
// Sample every 100μs (10 kHz rate)
// At 1μs ticks: period = 100, use prime[0] mod 100
smsp_event_simple_t sample_schedule[] = {
    { .phase = 0,  .action = ACTION_SAMPLE },
    { .phase = 50, .action = ACTION_SAMPLE },  // Two samples per prime cycle
};
```

---

## 7. Bidirectional Operation

### 7.1 The Orchestra Model

```
┌─────────────┐     score (baton)      ┌─────────────┐
│             │ ─────────────────────▶ │             │
│  Conductor  │                        │   Nodes     │
│             │ ◀───────────────────── │             │
└─────────────┘    observations        └─────────────┘
```

SMSP supports bidirectional flow:
- **Instructions** (conductor → nodes): "Sample at phase P", "Set output to X"
- **Observations** (nodes → conductor): "At phase P, I measured V"

### 7.2 Observation Format

```c
typedef struct {
    uint8_t  phases[8];         // When it happened
    uint16_t source_node;       // Who observed it
    uint8_t  observation_type;  // What kind
    uint8_t  payload[];         // Data
} smsp_observation_t;

typedef enum {
    OBS_HEARTBEAT,          // "I'm alive, sync quality = X"
    OBS_SAMPLE,             // "At phase P, sensor read V"
    OBS_EVENT,              // "At phase P, threshold crossed"
    OBS_ACK,                // "I executed instruction N"
    OBS_ERROR,              // "Instruction N failed"
} observation_type_t;
```

### 7.3 Closed-Loop Operation

```
         ┌──────────────────────────────────────────┐
         │           Coordinator/Gateway            │
         │  - Distributes sampling schedule         │
         │  - Receives observations                 │
         │  - Correlates data (beamforming, etc.)   │
         └────────────────┬───────────────────────┬─┘
                          │                       │
              SMSP instructions           SMSP observations
              (sample at phase P)         (at P, saw V)
                          │                       │
                          ▼                       ▲
         ┌────────────────┴───────────────────────┴─┐
         │              Sensor Nodes                 │
         │  - Execute at synchronized phases        │
         │  - Report observations with phase stamps │
         └───────────────────────────────────────────┘
```

---

## 8. Transport Agnosticism

SMSP defines format and semantics, not delivery:

| Transport | Score Delivery | Observation Return |
|-----------|----------------|-------------------|
| **ESP-NOW** | Broadcast/unicast | Unicast to coordinator |
| **BLE** | GATT write | GATT notify |
| **LoRa** | Broadcast | Unicast to gateway |
| **WiFi** | UDP multicast | UDP to server |
| **Serial** | Point-to-point | Collected by host |
| **Flash** | Baked at build | Not applicable |

The protocol is complete when a node possesses:
1. A score (however delivered)
2. Phase lock with peers (however achieved via UTLP)
3. Zone assignment (however determined, potentially via RFIP)

---

## 9. Scale Invariance

The same score format works regardless of physical scale:

| Scale | "Zones" Are | Example |
|-------|-------------|---------|
| **PCB** | GPIO pins | RGB LEDs on one board |
| **Device** | Peer MAC addresses | Bilateral handhelds |
| **Room** | Node positions | Warning light array |
| **Field** | Drone IDs | Search and rescue swarm |
| **Building** | Sensor clusters | Structural monitoring |
| **Region** | Base stations | Seismic array |

A score written for three LEDs on a PCB plays identically on three drones 100 meters apart. The playback engine doesn't know physical spacing—it only knows phases and channels.

---

## 10. Relationship to Existing Standards

| Standard | What It Does | SMSP Difference |
|----------|--------------|-----------------|
| **DMX512** | 512 channels, continuous broadcast | Score uploaded once, nodes execute independently |
| **MIDI** | Note events, musical timing | Continuous interpolated states, sub-ms sync |
| **SMPTE** | Timecode, devices chase master | Devices agree on phase then execute autonomously |
| **OSC** | Real-time control messages | Score complete before execution, no runtime traffic |
| **Art-Net** | DMX over Ethernet | Connectionless during execution |

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

---

## 11. Implementation Requirements

### 11.1 Minimum Engine (Region-Based)

| Resource | Requirement |
|----------|-------------|
| Flash | ~500 bytes code + score size |
| RAM | ~50 bytes state |
| CPU | One comparison per region per tick |
| Timer | UTLP tick interrupt |

Runs on: ATtiny85, ATmega328, any Cortex-M0+

### 11.2 Full Engine (Event-Based with Interpolation)

| Resource | Requirement |
|----------|-------------|
| Flash | ~2 KB code + score size |
| RAM | ~200 bytes state |
| CPU | Phase matching + interpolation |
| Timer | UTLP tick interrupt |

Runs on: ESP32, STM32, any Cortex-M3+

### 11.3 Coordinator (Bidirectional)

| Resource | Requirement |
|----------|-------------|
| Flash | ~10 KB code |
| RAM | ~1 KB + observations buffer |
| Network | ESP-NOW/BLE/WiFi |
| Storage | Optional logging |

Runs on: ESP32-C6, ESP32-S3, Linux gateway

---

## 12. Wire Format

### 12.1 Score Upload Packet

```
┌──────────────────────────────────────────────────────────┐
│ Byte 0: SMSP_MAGIC (0x53)                                │
│ Byte 1: Command (SCORE_UPLOAD = 0x01)                    │
│ Byte 2-3: Total length (little-endian)                   │
│ Byte 4: Fragment index                                   │
│ Byte 5: Total fragments                                  │
│ Byte 6-N: Score data (smsp_score_t fragment)             │
└──────────────────────────────────────────────────────────┘
```

### 12.2 Observation Packet

```
┌──────────────────────────────────────────────────────────┐
│ Byte 0: SMSP_MAGIC (0x53)                                │
│ Byte 1: Command (OBSERVATION = 0x02)                     │
│ Byte 2-9: Phases[8] (when observed)                      │
│ Byte 10-11: Source node ID                               │
│ Byte 12: Observation type                                │
│ Byte 13-N: Payload (type-dependent)                      │
└──────────────────────────────────────────────────────────┘
```

---

## 13. Security Considerations

### 13.1 Score Integrity

Scores should be signed when delivered over untrusted channels:

```c
typedef struct {
    smsp_score_t score;
    uint8_t      signature[32];  // Ed25519 or HMAC-SHA256
} smsp_signed_score_t;
```

### 13.2 Observation Authentication

Observations should include node authentication:

```c
typedef struct {
    smsp_observation_t obs;
    uint8_t            mac[8];  // Truncated HMAC
} smsp_authenticated_obs_t;
```

### 13.3 Phase Lock Attacks

An attacker broadcasting false UTLP beacons could desynchronize nodes. Mitigations:
- Stratum hierarchy (prefer higher-authority sources)
- Byzantine detection (reject outliers via vector similarity)
- Cryptographic beacons (signed by trusted time source)

See UTLP Technical Supplement S2 (Biological Governance) for security architecture.

---

## 14. Reference Implementation

### 14.1 Score Compiler (Python)

```python
#!/usr/bin/env python3
"""
SMSP Score Compiler
Converts human-readable pattern definitions to binary scores.
"""

import struct
from dataclasses import dataclass
from typing import List

PRIMES = [241, 251, 239, 233, 229, 227, 223, 211]

@dataclass
class Region:
    phase_index: int
    start: int
    end: int
    channels: bytes

@dataclass
class Score:
    version: int = 2
    format: int = 1  # FORMAT_REGIONS
    pattern_class: int = 0
    prime_config: int = 0
    pattern_prime_idx: int = 0
    regions: List[Region] = None
    
    def to_bytes(self) -> bytes:
        header = struct.pack('<BBBBBB',
            self.version,
            self.format,
            self.pattern_class,
            self.prime_config,
            self.pattern_prime_idx,
            len(self.regions)
        )
        
        region_data = b''
        for r in self.regions:
            region_data += struct.pack('<BBB',
                r.phase_index,
                r.start,
                r.end
            ) + r.channels
        
        return header + region_data


def compile_bilateral(frequency_hz: float, num_channels: int = 4) -> Score:
    """Compile a bilateral (EMDR-style) pattern."""
    
    # Select prime closest to desired period
    # At 1ms ticks, 1Hz = 1000 ticks
    tick_period_ms = 1
    period_ticks = int(1000 / frequency_hz / tick_period_ms)
    
    # Find best prime
    best_prime_idx = min(range(len(PRIMES)), 
                         key=lambda i: abs(PRIMES[i] - period_ticks))
    prime = PRIMES[best_prime_idx]
    
    # Create antiphase regions
    midpoint = prime // 2
    
    # Channel layout: L_R, L_G, L_B, L_haptic, R_R, R_G, R_B, R_haptic
    # Soft blue color (R=0, G=100, B=255) for therapeutic calming effect
    left_channels = bytes([0, 100, 255, 180,   0, 0, 0, 0])    # Left: blue+haptic
    right_channels = bytes([0, 0, 0, 0,   0, 100, 255, 180])   # Right: blue+haptic
    
    return Score(
        pattern_class=0,  # BILATERAL
        pattern_prime_idx=best_prime_idx,
        regions=[
            Region(best_prime_idx, 0, midpoint, left_channels),
            Region(best_prime_idx, midpoint, prime, right_channels),
        ]
    )


def compile_police_lightbar() -> Score:
    """Compile SAE J845 police lightbar pattern with Red/Blue/White."""
    
    # 4Hz = 250ms period, use prime[7] = 251
    prime_idx = 7  # 251
    
    # Channel layout: L_R, L_G, L_B, R_R, R_G, R_B (6 bytes per region)
    RED =   bytes([255, 0, 0])
    BLUE =  bytes([0, 0, 255])
    WHITE = bytes([255, 255, 255])
    OFF =   bytes([0, 0, 0])
    
    return Score(
        pattern_class=1,  # EMERGENCY
        pattern_prime_idx=prime_idx,
        regions=[
            # Left RED quad flash
            Region(prime_idx, 0,   10,  RED + OFF),      # L=RED
            Region(prime_idx, 10,  20,  OFF + OFF),     # Gap
            Region(prime_idx, 20,  30,  RED + OFF),      # L=RED
            Region(prime_idx, 30,  40,  OFF + OFF),     # Gap
            Region(prime_idx, 40,  50,  RED + OFF),      # L=RED
            Region(prime_idx, 50,  60,  OFF + OFF),     # Gap
            Region(prime_idx, 60,  70,  RED + OFF),      # L=RED (4th)
            # Right BLUE quad flash
            Region(prime_idx, 70,  80,  OFF + BLUE),    # R=BLUE
            Region(prime_idx, 80,  90,  OFF + OFF),     # Gap
            Region(prime_idx, 90,  100, OFF + BLUE),    # R=BLUE
            Region(prime_idx, 100, 110, OFF + OFF),     # Gap
            Region(prime_idx, 110, 120, OFF + BLUE),    # R=BLUE
            Region(prime_idx, 120, 130, OFF + OFF),     # Gap
            Region(prime_idx, 130, 140, OFF + BLUE),    # R=BLUE (4th)
            # WHITE pursuit burst
            Region(prime_idx, 140, 150, WHITE + WHITE), # Both WHITE
            Region(prime_idx, 150, 160, OFF + OFF),     # Gap
            Region(prime_idx, 160, 170, WHITE + WHITE), # Both WHITE
            # Dark interval
            Region(prime_idx, 170, 251, OFF + OFF),     # Dark period
        ]
    )


if __name__ == '__main__':
    # Example: compile 1Hz bilateral
    score = compile_bilateral(1.0)
    binary = score.to_bytes()
    print(f"Bilateral 1Hz: {len(binary)} bytes")
    print(f"  Prime index: {score.pattern_prime_idx}")
    print(f"  Prime value: {PRIMES[score.pattern_prime_idx]}")
    print(f"  Regions: {len(score.regions)}")
    
    # Example: compile police lightbar
    score = compile_police_lightbar()
    binary = score.to_bytes()
    print(f"\nPolice Lightbar: {len(binary)} bytes")
    print(f"  Prime index: {score.pattern_prime_idx}")
    print(f"  Prime value: {PRIMES[score.pattern_prime_idx]}")
    print(f"  Regions: {len(score.regions)}")
```

### 14.2 Playback Engine (C)

```c
/**
 * SMSP Playback Engine
 * Minimal region-based implementation
 */

#include <stdint.h>
#include <string.h>

#define SMSP_MAX_CHANNELS 8
#define SMSP_MAX_REGIONS 16

typedef struct {
    uint8_t phase_index;
    uint8_t region_start;
    uint8_t region_end;
    uint8_t channels[SMSP_MAX_CHANNELS];
} smsp_region_t;

typedef struct {
    uint8_t version;
    uint8_t format;
    uint8_t pattern_class;
    uint8_t prime_config;
    uint8_t pattern_prime_idx;
    uint8_t num_regions;
    uint8_t num_channels;
    smsp_region_t regions[SMSP_MAX_REGIONS];
} smsp_score_t;

typedef struct {
    smsp_score_t* score;
    uint8_t current_phases[8];
    uint8_t output_channels[SMSP_MAX_CHANNELS];
} smsp_engine_t;

/**
 * Initialize engine with a score
 */
void smsp_init(smsp_engine_t* engine, smsp_score_t* score) {
    engine->score = score;
    memset(engine->current_phases, 0, 8);
    memset(engine->output_channels, 0, SMSP_MAX_CHANNELS);
}

/**
 * Update phases from UTLP
 */
void smsp_update_phases(smsp_engine_t* engine, uint8_t* phases) {
    memcpy(engine->current_phases, phases, 8);
}

/**
 * Execute one tick - find matching region and set outputs
 */
void smsp_tick(smsp_engine_t* engine) {
    if (!engine->score) return;
    
    uint8_t phase = engine->current_phases[engine->score->pattern_prime_idx];
    
    for (int i = 0; i < engine->score->num_regions; i++) {
        smsp_region_t* r = &engine->score->regions[i];
        
        // Check if phase is in this region
        if (r->region_start <= r->region_end) {
            // Normal range
            if (phase >= r->region_start && phase < r->region_end) {
                memcpy(engine->output_channels, r->channels, 
                       engine->score->num_channels);
                return;
            }
        } else {
            // Wrapped range (e.g., 200-50 means 200-255 and 0-50)
            if (phase >= r->region_start || phase < r->region_end) {
                memcpy(engine->output_channels, r->channels,
                       engine->score->num_channels);
                return;
            }
        }
    }
}

/**
 * Get current output for a channel
 */
uint8_t smsp_get_output(smsp_engine_t* engine, uint8_t channel) {
    if (channel < SMSP_MAX_CHANNELS) {
        return engine->output_channels[channel];
    }
    return 0;
}
```

---

## 15. Migration from v1.0

### 15.1 Score Conversion

v1.0 scores (tick-indexed) can be converted to v2.0 (phase-indexed):

```python
def convert_v1_to_v2(v1_score):
    """Convert tick-indexed score to phase-indexed."""
    
    # Find pattern period from v1 score
    max_tick = max(event.time_offset for event in v1_score.events)
    period_ticks = v1_score.loop_period or (max_tick + 1)
    
    # Select best prime
    prime_idx = find_closest_prime(period_ticks, PRIMES)
    prime = PRIMES[prime_idx]
    
    # Scale factor
    scale = prime / period_ticks
    
    # Convert events to phase-indexed
    v2_events = []
    for event in v1_score.events:
        tick = event.time_offset
        phase = int(tick * scale) % prime
        
        v2_events.append(smsp_event_v2(
            phases=[phase if i == prime_idx else 0 for i in range(8)],
            phase_mask=(1 << prime_idx),
            channels=event.channels
        ))
    
    return smsp_score_v2(events=v2_events)
```

### 15.2 Engine Compatibility

v2.0 engines can execute v1.0 scores by:
1. Converting at load time (recommended)
2. Using CRT recovery to get tick, then index (slower)

---

## 16. Future Extensions

### 16.1 Multi-Prime Patterns

For patterns requiring more precision than a single prime:

```c
typedef struct {
    uint8_t phases[8];      // All 8 phases must match
    uint8_t phase_mask;     // 0xFF = all must match
    // ...
} smsp_event_multiprime_t;
```

### 16.2 Conditional Execution

```c
typedef struct {
    uint8_t condition_type;  // IF_ZONE, IF_ROLE, IF_INPUT
    uint8_t condition_value;
    smsp_region_t region;
} smsp_conditional_region_t;
```

### 16.3 Dynamic Scores

Scores generated at runtime based on sensor input or network state.

---

## 17. Prior Art Claims

SMSP-related claims are documented in the Claims Appendix:

| Claim Range | Topic |
|-------------|-------|
| 33-42 | Core SMSP structure and execution |
| 50 | Scale invariance |
| 82-86 | Bidirectional operation |
| 87-100 | Sensing and metasurface applications |

---

## Appendix A: Quick Reference

### A.1 Pattern Classes

| Class | Value | Use Case |
|-------|-------|----------|
| BILATERAL | 0 | EMDR, therapeutic |
| EMERGENCY | 1 | SAE J845 lightbars |
| SWARM_SYNC | 2 | In-phase coordination |
| PURSUIT | 3 | Sequential chase |
| SENSING | 4 | Distributed sampling |
| CUSTOM | 255 | Raw scores |

### A.2 Channel Types

| Type | Value | Bytes |
|------|-------|-------|
| LED_MONO | 0 | 1 (brightness) |
| LED_RGB | 1 | 3 (R, G, B) |
| LED_RGBW | 2 | 4 (R, G, B, W) |
| HAPTIC | 3 | 1 (intensity) |
| AUDIO_FREQ | 4 | 3 (freq_hz LE16, amplitude) |
| GPIO | 5 | 1 (on/off) |

### A.3 Standard Primes

| Index | Prime | Typical Use |
|-------|-------|-------------|
| 0 | 241 | ~4.1 Hz patterns |
| 1 | 251 | ~4.0 Hz patterns |
| 2 | 239 | ~4.2 Hz patterns |
| 3 | 233 | ~4.3 Hz patterns |
| 4 | 229 | ~4.4 Hz patterns |
| 5 | 227 | ~4.4 Hz patterns |
| 6 | 223 | ~4.5 Hz patterns |
| 7 | 211 | ~4.7 Hz patterns |

(Frequencies assume 1ms tick period)

---

*This document is published as prior art for the Synchronized Multimodal Score Protocol.*

---

*PHYRFLY Protocol Family: UTLP | RFIP | SMSP*
