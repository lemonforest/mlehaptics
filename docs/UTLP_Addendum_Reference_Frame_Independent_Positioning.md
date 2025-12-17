# UTLP Technical Report — Addendum A

## Reference-Frame Independent Positioning (RFIP)

**Universal Time Layer Protocol Extension**

*mlehaptics Project — December 17, 2025*

*Authors: Steve [mlehaptics], with assistance from Claude (Anthropic)*

---

## Abstract

This addendum documents an emergent architectural capability of the Universal Time Layer Protocol (UTLP) when combined with 802.11mc Fine Time Measurement (FTM) or equivalent ranging technologies: **Reference-Frame Independent Positioning (RFIP)**. Unlike traditional positioning systems that locate devices relative to a fixed Earth-centered reference frame, RFIP establishes spatial relationships between swarm members without requiring any external reference. The coordinate system emerges from the swarm itself, making it operational in environments where GPS is unavailable, impractical, or physically meaningless—including moving vehicles, underground facilities, underwater, and extraterrestrial environments.

---

## 1. Introduction

### 1.1 The Limitation of Earth-Centric Positioning

All widely-deployed positioning systems share a fundamental assumption: positions are defined relative to Earth's surface or center of mass.

| System | Reference Frame | Limitation |
|--------|-----------------|------------|
| GPS/GNSS | WGS84 (Earth-centered) | Requires satellite visibility |
| Cell tower trilateration | Fixed tower locations | Requires cellular infrastructure |
| WiFi fingerprinting | Pre-mapped AP locations | Requires static infrastructure |
| UWB anchors | Surveyed anchor positions | Requires fixed installation |

This assumption fails when:
- The operational environment moves relative to Earth (vehicles, vessels, aircraft, spacecraft)
- No Earth-referenced infrastructure exists (wilderness, ocean, space)
- Infrastructure access is denied (military jamming, underground, underwater)
- Earth-referenced coordinates are meaningless (planetary surfaces, orbital stations)

### 1.2 A Different Question

Traditional positioning asks: *"Where am I on Earth?"*

RFIP asks: *"Where are we relative to each other?"*

This reframing eliminates the dependency on external reference frames while preserving the spatial information actually needed for most applications.

---

## 2. Theoretical Foundation

### 2.1 Intrinsic vs. Extrinsic Geometry

**Extrinsic positioning** defines location using coordinates in an external reference frame (latitude, longitude, altitude). The reference frame must exist independently and be accessible to the system.

**Intrinsic positioning** defines spatial relationships using only measurements between objects in the system. The geometry is self-contained—distances and angles between nodes define shape without reference to anything external.

RFIP implements intrinsic positioning. The mathematical foundation is straightforward:

- **2 nodes**: One distance measurement. Defines separation but not orientation.
- **3 nodes**: Three distances. Defines a triangle (2D shape, unique up to reflection).
- **4 nodes**: Six distances. Defines a tetrahedron (3D shape, unique up to reflection).
- **N nodes**: N(N-1)/2 distances. Overconstrained system enabling error correction.

### 2.2 Dimensional Requirements

The number of nodes determines the dimensionality of recoverable geometry:

| Nodes | Pairwise Distances | Geometry | Dimensionality | Use Case |
|-------|-------------------|----------|----------------|----------|
| 2 | 1 | Line segment | 1D (separation only) | Bilateral sync |
| 3 | 3 | Triangle | 2D (planar) | Ground vehicles |
| **4** | **6** | **Tetrahedron** | **3D (volumetric)** | **Flying swarms, rescue** |
| 5+ | 10+ | Polytope | 3D + redundancy | Fault tolerance |

**Critical insight for 3D applications:** Three nodes are *always* coplanar — they define a triangle in some plane, but you cannot determine that plane's orientation in 3D space without a fourth node. For any application involving:
- Flying drones
- Multi-floor buildings
- Underwater operations
- Spacecraft
- Rescue in collapsed structures

**You need minimum 4 nodes for true 3D spatial awareness.**

The 4th node's distances to the existing three determine its height above/below their plane, breaking the 2D constraint and establishing full volumetric positioning.

**Redundancy scaling:**
- 4 nodes: Exactly determined (no error correction possible)
- 5 nodes: 10 distances, 3×5=15 coordinates → 4 redundant measurements
- N nodes: N(N-1)/2 distances, 3N coordinates → increasing overdetermination

For mission-critical applications (rescue, medical, aerospace), **5+ nodes** provide measurement redundancy enabling detection and correction of individual ranging failures.

### 2.3 Coordinate System Emergence

Given pairwise distances between nodes, a local coordinate system can be constructed algorithmically:

```
Algorithm: Swarm Coordinate Synthesis

1. SELECT anchor node A → origin (0, 0, 0)
2. SELECT node B → positive X-axis at (d_AB, 0, 0)
3. SELECT node C → XY-plane via trilateration
   - x_C = (d_AC² - d_BC² + d_AB²) / (2 · d_AB)
   - y_C = √(d_AC² - x_C²)
   - C located at (x_C, y_C, 0)
4. SELECT node D → 3D position via trilateration
   - Solve system of three equations for (x_D, y_D, z_D)
5. FOR remaining nodes:
   - Trilaterate using any 3+ known positions
   - Apply least-squares fitting if overdetermined

Result: All nodes have (x, y, z) coordinates in swarm-local frame
```

The choice of anchor node A is arbitrary—different choices yield coordinate systems related by rigid transformation (rotation + translation). The **shape** of the swarm is invariant.

### 2.3 Reference Frame Properties

The emergent RFIP coordinate system has the following properties:

| Property | Description |
|----------|-------------|
| **Origin** | Defined by convention (e.g., first node, centroid, master node) |
| **Orientation** | Defined by convention (e.g., A→B defines +X axis) |
| **Handedness** | Requires convention or external reference to resolve reflection ambiguity |
| **Scale** | Metric (meters), derived from speed of light in ranging |
| **Validity** | Instantaneous—valid at measurement time only |
| **Persistence** | Requires continuous or periodic re-measurement |

### 2.4 Resolving Reflection Ambiguity

With distance measurements alone, the coordinate system has a reflection ambiguity (the swarm could be "flipped"). This can be resolved by:

1. **Convention**: Define which side is "up" or "left" by node role (e.g., SERVER = RIGHT)
2. **Gravity vector**: If available, accelerometer defines "down"
3. **Magnetic north**: If available, magnetometer defines heading
4. **Initial calibration**: Human operator specifies orientation once
5. **Continuity**: Track which reflection was chosen and maintain it

For the mlehaptics bilateral device use case, option 1 suffices: the SERVER is defined as the RIGHT device, CLIENT as LEFT. No ambiguity exists because the roles are assigned at pairing time.

---

## 3. Implementation in UTLP

### 3.1 Architectural Fit

UTLP already provides:
- Peer discovery and pairing
- Microsecond-precision time synchronization
- Quality/stratum-based hierarchy
- Beacon-based state distribution

RFIP extends UTLP by adding **spatial awareness** alongside temporal awareness. The same beacon infrastructure that distributes time can distribute position.

### 3.2 Extended Beacon Structure

```c
typedef struct __attribute__((packed)) {
    // Standard UTLP fields
    uint8_t  magic[2];           // 0xFE, 0xFE
    uint8_t  version;            // Protocol version
    uint8_t  flags;              // Capability flags
    uint8_t  stratum;            // Time stratum
    uint8_t  quality;            // Source quality
    uint64_t epoch_us;           // Synchronized timestamp
    
    // RFIP extension fields
    uint8_t  spatial_flags;      // RFIP capability/state flags
    uint8_t  node_count;         // Nodes in coordinate system
    int16_t  pos_x_cm;           // Position X in centimeters
    int16_t  pos_y_cm;           // Position Y in centimeters  
    int16_t  pos_z_cm;           // Position Z in centimeters
    uint8_t  pos_uncertainty_cm; // Position uncertainty radius
    
    // Ranging data (for receivers to verify/refine)
    uint16_t range_to_origin_cm; // Distance to origin node
    
    uint16_t checksum;
} utlp_rfip_beacon_t;

// Spatial flags
#define RFIP_FLAG_CAPABLE        (1 << 0)  // Node supports ranging
#define RFIP_FLAG_ORIGIN         (1 << 1)  // Node is coordinate origin
#define RFIP_FLAG_CALIBRATED     (1 << 2)  // Position is known
#define RFIP_FLAG_3D             (1 << 3)  // 3D coordinates valid (vs 2D)
#define RFIP_FLAG_MOVING         (1 << 4)  // Swarm is in motion
```

### 3.3 Ranging Integration

RFIP is transport-agnostic for ranging. Supported methods include:

| Method | Precision | Range | Hardware |
|--------|-----------|-------|----------|
| 802.11mc FTM | ±1-2m | 50m+ | ESP32-C6, phones |
| UWB (802.15.4z) | ±10cm | 30m | DW1000, DW3000 |
| BLE RSSI | ±2-5m | 10m | Any BLE device |
| BLE AoA/AoD | ±1m | 10m | BLE 5.1+ arrays |
| Acoustic | ±1cm | 5m | Ultrasonic transducer |

The UTLP transport abstraction layer (Phase D of implementation plan) accommodates all methods through a common interface:

```c
typedef struct {
    esp_err_t (*measure_range)(const uint8_t* peer_id, range_result_t* result);
    uint16_t  typical_precision_cm;
    uint16_t  maximum_range_cm;
    bool      requires_los;  // Line of sight required?
} rfip_ranging_transport_t;
```

### 3.4 Coordinate System Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                    RFIP State Machine                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    Peer         ┌──────────┐    3+ nodes         │
│  │          │   discovered    │          │   ranged            │
│  │ DISABLED ├────────────────►│ RANGING  ├──────────────┐      │
│  │          │                 │          │              │      │
│  └──────────┘                 └────┬─────┘              ▼      │
│                                    │            ┌──────────┐   │
│                                    │ <3 nodes   │          │   │
│                                    └────────────┤CALIBRATED│   │
│                                                 │          │   │
│       ┌────────────────────────────────────────►└────┬─────┘   │
│       │ Peer lost, recalibrating                     │         │
│       │                                              │         │
│  ┌────┴─────┐◄───────────────────────────────────────┘         │
│  │          │        Position drift detected                   │
│  │ TRACKING │                                                  │
│  │          │◄─────── Continuous ranging updates               │
│  └──────────┘                                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Reference Frame Independence

### 4.1 Invariance Under Motion

The critical property of RFIP is that the swarm's internal geometry is invariant under rigid motion of the entire swarm. Mathematically:

If the swarm undergoes transformation T (rotation R + translation t):
- Each node position p_i → R·p_i + t
- Each pairwise distance d_ij → d_ij (unchanged)
- The coordinate synthesis algorithm produces the same shape

This means RFIP **works identically** whether the swarm is:
- Stationary on Earth's surface
- Moving in a vehicle at any speed
- Rotating (e.g., on a turntable or in a spinning spacecraft)
- In freefall (zero-g environment)
- On another planetary body

### 4.2 No Infrastructure Dependency

RFIP requires only:
1. Ranging capability between nodes (RF, acoustic, or optical)
2. Time synchronization between nodes (UTLP core function)
3. Computation to solve trilateration (embedded MCU sufficient)

It does **not** require:
- GPS satellites or signals
- Pre-surveyed anchor points
- Fixed infrastructure of any kind
- Connection to Earth-based networks
- Knowledge of absolute location

### 4.3 Operational Environments

| Environment | GPS | Cellular | RFIP |
|-------------|-----|----------|------|
| Urban outdoor | ✓ | ✓ | ✓ |
| Urban indoor | ✗ | Limited | ✓ |
| Underground | ✗ | ✗ | ✓ |
| Underwater | ✗ | ✗ | ✓* |
| Aircraft cabin | ✓** | ✗ | ✓ |
| Spacecraft | ✓** | ✗ | ✓ |
| Lunar surface | ✗ | ✗ | ✓ |
| Mars surface | ✗ | ✗ | ✓ |
| Deep space | ✗ | ✗ | ✓ |
| Jamming environment | ✗ | ✗ | ✓ |

\* Acoustic ranging required; RF does not propagate underwater  
\** GPS works but provides Earth-relative coordinates, not cabin-relative

---

## 5. Use Cases

### 5.1 Mobile Medical Applications (Primary Use Case)

**Scenario**: EMDR therapy in ambulance, medevac helicopter, or patient transport.

**Problem**: Patient needs bilateral stimulation therapy during transport. Earth-referenced positioning is irrelevant—what matters is the position of therapy devices relative to the patient's body.

**RFIP Solution**: 
- Two haptic devices establish bilateral coordinate system
- "Left" and "Right" defined by device roles, not compass heading
- Therapy works identically whether vehicle is stationary or moving
- No GPS or cellular required

### 5.2 Confined Space Operations

**Scenario**: Search and rescue in collapsed structure, cave system, or mine.

**Problem**: GPS unavailable. Pre-surveyed infrastructure doesn't exist.

**RFIP Solution**:
- Rescue team carries UTLP-enabled devices
- Swarm establishes relative positions as team spreads out
- Coordinator sees team member positions on display
- "Map" is relative to team, not to Earth surface

### 5.3 Underwater Operations

**Scenario**: Dive team coordination, underwater construction, ROV swarm.

**Problem**: RF doesn't propagate underwater. GPS completely unavailable.

**RFIP Solution**:
- Acoustic ranging between nodes (existing technology)
- UTLP time sync via acoustic modem
- Relative positioning works identically to surface operation

### 5.4 Spacecraft and Habitat Applications

**Scenario**: Astronaut tracking in ISS, lunar habitat, or Mars base.

**Problem**: GPS provides orbital position, not position within habitat. No cellular infrastructure on Moon/Mars.

**RFIP Solution**:
- UTLP nodes installed in habitat
- Crew-worn devices range to habitat nodes
- Position defined relative to habitat, not planetary body
- Works identically on ISS, Moon, Mars, or transit vehicle

### 5.5 Swarm Robotics

**Scenario**: Autonomous robot swarm for exploration, construction, or agriculture.

**Problem**: GPS precision insufficient for close coordination. Infrastructure-based positioning limits operational area.

**RFIP Solution**:
- Each robot is a UTLP node
- Robots maintain awareness of neighbors' positions
- Formation control uses swarm-relative coordinates
- Operational area unlimited by infrastructure

### 5.6 GPS-Denied Military/Security

**Scenario**: Operations in GPS-jammed environment.

**Problem**: Adversary denies GPS access. Cannot rely on any external reference.

**RFIP Solution**:
- Squad members carry UTLP devices
- Relative positioning maintained via FTM or UWB
- Works regardless of jamming
- No signals to external infrastructure that could be detected

### 5.7 Emergency Vehicle Lightbar Synchronization (A Return Offering)

**Scenario**: Multiple emergency vehicles requiring synchronized warning lights.

**Problem**: Current lightbar systems either flash independently (chaotic appearance, reduced visibility) or require each unit to have its own GPS module for synchronization. GPS adds cost, complexity, and fails in tunnels, parking structures, and urban canyons.

**UTLP Solution**:
- **Single time source**: One vehicle with GPS (or cellular time) acts as stratum 0/1 source
- **Peer propagation**: Nearby vehicles passively adopt time via UTLP beacon
- **Synchronized patterns**: All lightbars execute identical "sheet music" patterns in lockstep
- **No per-unit GPS**: Only the time source needs external reference; all others sync opportunistically

**The Symmetry**: This project borrowed the "lightbar paradigm" for bilateral pattern playback—the concept that synchronized flashing patterns can be pre-programmed and executed independently by each unit once they share a common time reference. UTLP is our return offering: a protocol that enables the very systems that inspired us to achieve coordination without requiring GPS in every unit.

**Technical Implementation**:
- Emergency vehicle #1 (with GPS): Broadcasts UTLP beacons at stratum 0
- Vehicles #2-N: Receive beacons, adopt time, increment stratum
- All vehicles: Execute `emergency_pattern[]` segments at identical offsets
- Result: Fleet-wide synchronized flashing, tunnel-proof, no per-unit GPS cost

This exemplifies UTLP's philosophy: **time as a public utility**. One accurate source benefits the entire swarm.

---

## 6. Geometric Self-Diagnostics

### 6.1 The Feedback Loop

RFIP creates a unique capability: **the swarm can use its spatial model to validate the measurements that produced it.** Once node positions are established, anomalous ranging measurements can be analyzed against the known geometry to diagnose failure modes.

This is self-aware swarm diagnostics — the geometry informs measurement validity.

### 6.2 RF Path Occlusion Detection

**Problem:** Ranging measurement between nodes A and C returns unexpected value.

**Diagnostic query:** Is there a node B positioned on or near the line segment A→C?

```c
// Geometric occlusion check
typedef struct {
    vec3_t position;
    float  body_radius_cm;  // RF-opaque radius of device
} node_geometry_t;

// Check if node B occludes the path from A to C
bool check_path_occlusion(const node_geometry_t* A,
                          const node_geometry_t* B, 
                          const node_geometry_t* C) {
    // Vector from A to C
    vec3_t AC = vec3_sub(C->position, A->position);
    float AC_len = vec3_length(AC);
    vec3_t AC_norm = vec3_scale(AC, 1.0f / AC_len);
    
    // Vector from A to B
    vec3_t AB = vec3_sub(B->position, A->position);
    
    // Project B onto line AC
    float projection = vec3_dot(AB, AC_norm);
    
    // B is not between A and C
    if (projection < 0 || projection > AC_len) {
        return false;
    }
    
    // Closest point on AC to B
    vec3_t closest = vec3_add(A->position, vec3_scale(AC_norm, projection));
    
    // Distance from B to line AC
    float distance_to_line = vec3_length(vec3_sub(B->position, closest));
    
    // Check if B's body intersects the path
    // Include Fresnel zone approximation for RF
    float fresnel_radius_cm = sqrt(WAVELENGTH_CM * projection * (AC_len - projection) / AC_len);
    float occlusion_radius = B->body_radius_cm + fresnel_radius_cm;
    
    return (distance_to_line < occlusion_radius);
}
```

**Diagnostic outcomes:**

| Scenario | Geometry Check | Interpretation | Action |
|----------|---------------|----------------|--------|
| Bad A→C range | B on path | Node occlusion | Use A→D→C path |
| Bad A→C range | No node on path | Environmental obstruction | Flag, use multipath |
| All ranges good | N/A | Nominal operation | Continue |
| Multiple bad ranges | Colinear nodes | Degenerate geometry | Alert operator |

### 6.3 Degenerate Geometry Detection

Certain node arrangements produce unreliable position estimates:

**Near-colinear (obtuse triangle):**
```
A ●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━● C
              ● B (slightly off-line)
```

When angle ABC approaches 180°, small ranging errors in A→B and B→C produce large position errors in B's computed location. The system should detect this:

```c
typedef struct {
    float condition_number;      // Matrix condition (high = bad)
    float min_angle_degrees;     // Smallest angle in geometry
    float colinearity_score;     // 0 = perfect tetrahedron, 1 = all colinear
    bool  is_degenerate;
} geometry_quality_t;

geometry_quality_t assess_geometry_quality(const node_geometry_t* nodes, int count) {
    geometry_quality_t quality = {0};
    
    if (count < 3) {
        quality.is_degenerate = true;
        return quality;
    }
    
    // Find minimum angle in all triangles
    quality.min_angle_degrees = 180.0f;
    for (int i = 0; i < count; i++) {
        for (int j = i+1; j < count; j++) {
            for (int k = j+1; k < count; k++) {
                float angle = min_triangle_angle(nodes[i], nodes[j], nodes[k]);
                if (angle < quality.min_angle_degrees) {
                    quality.min_angle_degrees = angle;
                }
            }
        }
    }
    
    // Degenerate if any angle < 10° (configurable threshold)
    quality.is_degenerate = (quality.min_angle_degrees < 10.0f);
    
    // For 4+ nodes, compute tetrahedron quality
    if (count >= 4) {
        quality.colinearity_score = compute_colinearity(nodes, count);
    }
    
    return quality;
}
```

### 6.4 Self-Healing Measurement Strategy

When geometry analysis detects potential issues, the swarm can adapt:

```
┌─────────────────────────────────────────────────────────────────┐
│              Measurement Validation Pipeline                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐     ┌──────────────┐     ┌─────────────────┐    │
│  │  Raw     │     │   Geometry   │     │   Validated     │    │
│  │ Ranging  │────►│   Quality    │────►│   Position      │    │
│  │ Measure  │     │   Check      │     │   Update        │    │
│  └──────────┘     └──────┬───────┘     └─────────────────┘    │
│                          │                                      │
│                          │ Quality poor?                        │
│                          ▼                                      │
│                   ┌──────────────┐                              │
│                   │  Diagnostic  │                              │
│                   │   Analysis   │                              │
│                   └──────┬───────┘                              │
│                          │                                      │
│            ┌─────────────┼─────────────┐                       │
│            ▼             ▼             ▼                        │
│     ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│     │ Occlusion│  │Degenerate│  │  Multi-  │                  │
│     │ by Node  │  │ Geometry │  │   path   │                  │
│     └────┬─────┘  └────┬─────┘  └────┬─────┘                  │
│          │             │             │                         │
│          ▼             ▼             ▼                         │
│     Use alternate  Request node   Apply                        │
│     ranging path   repositioning  multipath                    │
│                                   correction                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.5 Operational Implications

**For rescue scenarios:** If a 5-node team enters a collapsed structure and geometry quality degrades (nodes forced into near-colinear arrangement by confined space), the system can:
1. Alert coordinator that position accuracy is degraded
2. Identify which node movements would improve geometry
3. Continue operating with wider uncertainty bounds
4. Flag specific pairwise measurements as unreliable

**For flying swarms:** If formation becomes too flat (all drones at same altitude), 3D positioning accuracy in the vertical axis degrades. The system can:
1. Request altitude separation from formation controller
2. Weight horizontal measurements more heavily
3. Report anisotropic uncertainty (good XY, poor Z)

**For bilateral therapy (2 nodes):** Geometry is inherently degenerate (1D only). The system acknowledges this limitation — it knows separation distance, not 3D position. This is *sufficient* for bilateral sync, which only requires both devices to agree on timing, not on spatial coordinates.

---

## 7. Temporal-Spatial Coupling

### 7.1 Unified Time-Space Awareness

UTLP's core contribution is treating **time as a public utility**—synchronized time available to all swarm members. RFIP extends this to **space as a public utility**—consistent coordinate system available to all swarm members.

The coupling is deep:
- Ranging requires synchronized timing (ToF measurement)
- Position updates are timestamped (when was this position valid?)
- Moving swarms need temporal interpolation (where was node X at time T?)

### 7.2 Spacetime Events

With UTLP+RFIP, events can be tagged with full spacetime coordinates:

```c
typedef struct {
    uint64_t time_us;     // UTLP synchronized time
    int16_t  x_cm;        // RFIP X coordinate
    int16_t  y_cm;        // RFIP Y coordinate
    int16_t  z_cm;        // RFIP Z coordinate
    uint8_t  event_type;  // Application-specific
    uint8_t  source_node; // Which node observed this
} spacetime_event_t;
```

Multiple observers can correlate events even if the swarm is moving, because:
- Time is synchronized across observers
- Position is known in common reference frame
- Both are valid at event timestamp

### 7.3 Relativistic Considerations (Future)

For terrestrial and near-Earth applications, Newtonian mechanics suffices. However, the architecture is extensible to relativistic scenarios:

- High-velocity swarms (spacecraft)
- High-precision timing (where light-travel-time matters)
- Strong gravitational fields (orbital mechanics)

UTLP's stratum model already accommodates varying clock rates—relativistic time dilation is just an extreme case of clock drift.

---

## 8. Comparison with Prior Art

### 8.1 Relation to Existing Technologies

| Technology | Earth Reference | Infrastructure | Self-Organizing | UTLP/RFIP |
|------------|-----------------|----------------|-----------------|-----------|
| GPS | Required | Satellites | No | No |
| UWB RTLS | Required | Anchors | No | Optional |
| WiFi RTT | Required | APs | No | Optional |
| SLAM | Built incrementally | None | Yes | Yes |
| RFIP | Optional | None | Yes | **Yes** |

RFIP is most similar to SLAM (Simultaneous Localization and Mapping) but differs in:
- SLAM builds a persistent map; RFIP maintains ephemeral positions
- SLAM is typically single-agent; RFIP is inherently multi-agent
- SLAM requires feature detection; RFIP uses explicit ranging

### 8.2 Novel Contributions

This document establishes prior art for:

1. **Combining PTP-inspired time sync with cooperative ranging** for joint time-space awareness in embedded swarms.

2. **Reference-frame independent positioning** as an explicit design goal, not an incidental capability.

3. **Transport-agnostic ranging integration** within a time synchronization protocol.

4. **Application to mobile medical devices** where patient-relative positioning matters, not Earth-relative positioning.

5. **Geometric self-diagnostics** using swarm spatial model to validate ranging measurements — detecting node occlusion, degenerate geometry, and enabling self-healing measurement strategies.

6. **Explicit dimensional requirements** (4+ nodes for 3D) for aerospace and rescue applications where vertical positioning is critical.

---

## 9. Implementation Status

### 9.1 Current State (December 2025)

| Component | Status | Notes |
|-----------|--------|-------|
| UTLP time sync | Implemented | ±30μs over BLE |
| 802.11mc research | Complete | See FTM Reconnaissance Report |
| FTM integration | Planned | Q1 2026 |
| RFIP coordinate synthesis | Specified | This document |
| Multi-node ranging | Not started | Requires 3+ devices |

### 9.2 Minimum Viable RFIP

For the bilateral EMDR use case, full RFIP is not required. The minimal implementation is:

1. Two nodes with defined roles (SERVER=RIGHT, CLIENT=LEFT)
2. Optional: FTM ranging to measure/verify separation distance
3. Coordinate system is implicit: origin at midpoint, X-axis along LEFT→RIGHT

This provides the therapeutic benefit (bilateral synchronization) without requiring full N-node coordinate synthesis.

### 9.3 Roadmap to Full RFIP

| Phase | Capability | Nodes | Application |
|-------|------------|-------|-------------|
| Current | Bilateral sync | 2 | EMDR therapy |
| Phase 1 | FTM ranging | 2 | Verified separation |
| Phase 2 | Triangulation | 3 | 2D relative positioning |
| Phase 3 | Tetrahedralization | 4+ | 3D relative positioning |
| Phase 4 | Dynamic tracking | N | Moving swarm coordination |

### 9.4 Lightbar Testbed: 4-Device UTLP/RFIP Demonstration

**Hardware:** Four EMDR bilateral devices, LED-only mode (motors disabled)

**Dual Purpose:**
1. **Lightbar Demo**: Prove synchronized pattern playback across 4 nodes using "sheet music" paradigm - visible proof that UTLP time synchronization enables fleet-wide coordination
2. **Mesh Protocol Testbed**: First physical implementation of multi-node UTLP + RFIP, validating the architecture before scaling to larger swarms

**Why 4 Devices:**
- **Tetrahedron geometry**: 4 nodes is the minimum for full 3D RFIP (volumetric positioning)
- **Mesh topology**: Tests multi-hop stratum propagation (PWA → Device 1 → Devices 2-4)
- **Proof of concept**: If 4 WS2812B LEDs flash in perfect sync without per-device GPS, the protocol works

**Development Philosophy: Lightbar Drives EMDR Improvements**

The lightbar showcase is not a separate product—it's a proving ground. Every improvement made to achieve smooth, synchronized LED patterns across 4 devices flows directly back to the EMDR therapy firmware:

| Lightbar Requirement | EMDR Therapy Benefit |
|---------------------|----------------------|
| Seamless pattern transitions | Smooth frequency changes mid-session |
| Multi-device mesh sync | Future multi-zone therapy configurations |
| Atomic-grade timing | Tighter bilateral alternation precision |
| RF disruption resilience | Therapy continuity during BLE glitches |

**The test**: If 4 LEDs can flash in perfect sync through arbitrary pattern changes, 2 motors can alternate smoothly through frequency changes.

**Using Existing Hardware:** The EMDR devices already have WS2812B LEDs and BLE. No new hardware required—just firmware expansion to support 4+ device mesh topology.

---

## 10. Protocol Hardening Extensions

As UTLP scales beyond trusted bilateral pairs to multi-node meshes and potentially adversarial environments, the protocol requires hardening. These extensions leverage the atomic-grade time that UTLP already provides.

### 10.1 TOTP Beacon Integrity (Replay Attack Prevention)

**Problem:** Current sync beacons use plaintext rolling counters, vulnerable to replay attacks.

**Solution:** Time-Based One-Time Password (TOTP) tokens ensure packet freshness.

```c
// UTLP TOTP parameters
#define TOTP_WINDOW_US      100000  // 100ms validity window
#define TOTP_SECRET_SIZE    16      // 128-bit shared secret (pre-provisioned at pairing)

typedef struct __attribute__((packed)) {
    // Existing beacon fields...
    uint64_t atomic_time_us;   // UTLP synchronized time
    uint32_t totp_token;       // HMAC-SHA256(secret, time_slot) truncated to 32 bits
} utlp_hardened_beacon_t;

// Token generation
uint32_t utlp_generate_totp(uint64_t atomic_time_us, const uint8_t* secret) {
    uint64_t time_slot = atomic_time_us / TOTP_WINDOW_US;
    uint8_t hash[32];
    hmac_sha256(secret, TOTP_SECRET_SIZE, &time_slot, sizeof(time_slot), hash);
    return *(uint32_t*)hash;  // Truncate to 32 bits
}
```

**Validation:** Receiver generates expected token locally. Mismatch → drop packet.

**Benefit:** Immunity to replay attacks; ensures "freshness" of all UTLP messages.

### 10.2 Pseudo-802.11az Security Layer (Ranging Integrity)

Since 802.11az hardware encryption is unavailable at the application layer, we implement "Defense in Depth" to validate FTM ranging data.

#### 10.2.1 Identity Verification (Signed Nonce)

**Problem:** Rogue device could initiate ranging to inject false distance data.

**Solution:** Cryptographically signed nonce in FTM setup proves swarm membership.

```c
typedef struct __attribute__((packed)) {
    uint8_t  nonce[16];           // Random challenge
    uint8_t  signature[64];       // Ed25519 signature of nonce
    uint8_t  public_key[32];      // Signer's public key (for verification)
} ftm_identity_proof_t;
```

**Requirement:** Device must possess private key provisioned at swarm enrollment.

#### 10.2.2 Newtonian Gating (Physics-Based Spoofing Detection)

**Problem:** Attacker could inject false ranging measurements implying impossible motion.

**Solution:** Reject measurements violating physical velocity limits.

```c
#define MAX_HUMAN_VELOCITY_CM_S     1000   // 10 m/s (running speed)
#define MAX_VEHICLE_VELOCITY_CM_S   5000   // 50 m/s (highway speed)

bool is_physically_plausible(int16_t old_dist_cm, int16_t new_dist_cm,
                             uint32_t time_delta_us, uint16_t max_velocity) {
    // Implied velocity = Δd / Δt
    int32_t delta_cm = abs(new_dist_cm - old_dist_cm);
    uint32_t implied_velocity_cm_s = (delta_cm * 1000000UL) / time_delta_us;

    if (implied_velocity_cm_s > max_velocity) {
        ESP_LOGW(TAG, "Newtonian gate: rejected (%.1f m/s > %.1f m/s limit)",
                 implied_velocity_cm_s / 100.0f, max_velocity / 100.0f);
        return false;
    }
    return true;
}
```

**Integration:** Add as filter before Kalman update step.

#### 10.2.3 Geometric Consensus (Swarm Witness)

**Problem:** "Teleportation/Wormhole" attacks where a node claims impossible positions.

**Solution:** Verify spatial claims against neighbor observations using triangle inequality.

```c
// Triangle inequality: For any three nodes A, B, C:
// dist(A,C) ≤ dist(A,B) + dist(B,C)
// dist(A,C) ≥ |dist(A,B) - dist(B,C)|

bool validate_triangle_inequality(int16_t ab_cm, int16_t bc_cm, int16_t ac_cm,
                                  int16_t tolerance_cm) {
    // Upper bound: AC ≤ AB + BC
    if (ac_cm > ab_cm + bc_cm + tolerance_cm) {
        ESP_LOGW(TAG, "Triangle inequality violated: AC=%d > AB+BC=%d",
                 ac_cm, ab_cm + bc_cm);
        return false;
    }
    // Lower bound: AC ≥ |AB - BC|
    int16_t lower_bound = abs(ab_cm - bc_cm);
    if (ac_cm < lower_bound - tolerance_cm) {
        ESP_LOGW(TAG, "Triangle inequality violated: AC=%d < |AB-BC|=%d",
                 ac_cm, lower_bound);
        return false;
    }
    return true;
}
```

**Requirement:** 3+ nodes for basic validation, 4+ for full 3D verification.

### 10.3 Deterministic TDMA (Collision-Free Transmission)

**Problem:** As swarm size increases, RF collisions degrade sync quality.

**Solution:** Use atomic time to procedurally assign speaking slots—no central scheduler needed.

```c
#define TDMA_SLOT_DURATION_US  10000  // 10ms per slot

// Each node gets a deterministic speaking window
bool utlp_can_transmit(uint64_t atomic_time_us, uint8_t node_id, uint8_t total_nodes) {
    uint64_t current_slot = (atomic_time_us / TDMA_SLOT_DURATION_US) % total_nodes;
    return (current_slot == node_id);
}

// Usage in beacon transmission
void utlp_beacon_task(void* arg) {
    while (running) {
        uint64_t now = time_sync_get_atomic_time();

        if (utlp_can_transmit(now, my_node_id, swarm_size)) {
            send_beacon();
        }

        vTaskDelay(pdMS_TO_TICKS(1));  // Check frequently, transmit only in slot
    }
}
```

**Benefit:** Virtual wired bus over RF—continuous swarm communication without handshakes or collisions.

**Topology Discovery:** Requires knowing `total_nodes`. Options:
- Fixed at compile time (4-device testbed)
- Discovered via beacon counting
- Configured via PWA

### 10.4 Unified Security Model

All three hardening features leverage the same foundation:

| Feature | Uses Atomic Time For |
|---------|---------------------|
| TOTP | Token freshness (100ms micro-window) |
| Newtonian Gating | Velocity calculation (Δd / Δt) |
| Geometric Consensus | Timestamped position claims |
| Deterministic TDMA | Speaking slot assignment |

**Key Insight:** Atomic-grade synchronized time is the security primitive. Once you have trusted time, you can build trusted identity, trusted physics, and trusted coordination.

---

## 11. Conclusion

Reference-Frame Independent Positioning emerges naturally from UTLP's architecture when combined with peer-to-peer ranging. By asking "where are we relative to each other?" instead of "where are we on Earth?", RFIP eliminates dependencies on external infrastructure and fixed reference frames.

This enables operation in environments where traditional positioning fails: moving vehicles, underground, underwater, and beyond Earth. For the mlehaptics project, it means bilateral therapy devices work identically whether the patient is in a clinic, an ambulance, an aircraft, or a spacecraft.

RFIP represents a philosophical shift: **the swarm defines its own space**, just as UTLP allows **the swarm to distribute its own time**. Together, they provide complete spatiotemporal awareness without external dependencies.

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-17 | Steve / Claude | Initial specification |
| 1.1 | 2025-12-17 | Steve / Claude | Added Section 5.7 (Lightbar return offering), Section 9.4 (4-device testbed) |
| 1.2 | 2025-12-17 | Steve / Claude | Added Section 10 (Protocol Hardening: TOTP, Pseudo-802.11az, TDMA) |

---

## References

1. UTLP Technical Report v2.0, mlehaptics Project, December 2025
2. 802.11mc FTM Reconnaissance Report, mlehaptics Project, December 2025
3. ESPARGOS Physics Integration Report, mlehaptics Project, December 2025
4. IEEE 802.11-2016, Section 11.24 (Fine Timing Measurement)
5. IEEE 802.15.4z-2020 (Ultra-Wideband Ranging)
6. Precision Time Protocol (IEEE 1588-2019)

---

*This document is published as prior art for Reference-Frame Independent Positioning using peer-to-peer ranging in time-synchronized embedded device swarms.*
