# RFIP Technical Specification

## Reference Frame Independent Positioning

**A Connectionless Spatial Coordination Protocol**

---

*Document version: Draft 0.1*
*Last updated: December 2025*
*Status: Initial specification draft*
*Parent document: Connectionless Distributed Timing Prior Art (DOI: 10.5281/zenodo.18078265)*
*Related: UTLP Technical Supplement S2*
*Repository: https://github.com/lemonforest/mlehaptics*

---

## 1. Introduction

### 1.1 The UTLP Foundation

UTLP solves for time. Once nodes share synchronized time, **position becomes extractable**.

GPS solves for 4 unknowns: X, Y, Z, **and receiver clock error**.

RFIP with UTLP solves for 3 unknowns: X, Y, Z. **Clock error is already solved.**

This is the key insight: every UTLP beacon arrives at a known transmit time (±microseconds). A receiver hearing 3+ beacons can compute position from arrival time differences alone.

### 1.2 Design Philosophy

RFIP follows the same principles as UTLP:

| Principle | UTLP (Time) | RFIP (Space) |
|-----------|-------------|--------------|
| **Connectionless** | No pairing required for sync | No infrastructure required for positioning |
| **Emergent** | Authority emerges from stability | Anchors emerge from capability |
| **Layered** | Better sources enhance, don't replace | 802.11mc enhances, doesn't replace |
| **Biological** | Immune system governance | Proprioception / spatial awareness |

### 1.3 The Data Hierarchy

Position data sources, from always-available to enhancement:

| Layer | Source | Precision | Requires | Always Available |
|-------|--------|-----------|----------|------------------|
| 0 | **RSSI** | ~3-5m (noisy) | Nothing | ✓ |
| 1 | **RSSI differential** | ~1-3m | Multiple known anchors | ✓ |
| 2 | **TDoA from UTLP beacons** | ~30cm | UTLP sync | ✓ |
| 3 | **CSI (Channel State Information)** | ~50cm-1m | ESP-IDF support | ✓ |
| 4 | **Multipath signatures** | Fingerprint-level | Training/learning | ✓ |
| 5 | **802.11mc FTM** | ~10-50cm | Hardware support | Platform-dependent |
| 6 | **UWB (DW3000)** | ~10cm | External module | ✗ (add-on) |

**Strategy:** Build positioning from always-available sources (Layers 0-4). Let 802.11mc/UWB be calibration and enhancement, not foundation.

---

## 2. Platform Capabilities Assessment

### 2.1 ESP32-C6 (Primary Target)

| Technology | Status | Notes |
|------------|--------|-------|
| **RSSI** | ✓ Full support | Available on all WiFi packets |
| **CSI** | ✓ Full support | ESP32-C6 ranked 2nd best (after C5) for CSI quality |
| **802.11mc FTM Initiator** | ✓ Full support (ECO2+) | Silicon v0.2+ has working T3 timestamp |
| **802.11mc FTM Responder** | ✓ Full support | Can respond to FTM requests |
| **ESP-NOW timestamps** | ✓ Available | TX/RX timestamps from radio |
| **BLE 5.3** | ✓ Supported | RSSI available, no AoA/AoD (requires 5.1+ antenna array) |
| **IEEE 802.15.4** | ✓ Supported | Thread/Zigbee, potential ranging via ToF |

**Silicon Version Note:** 
- ECO0/ECO1 (v0.0, v0.1): FTM Initiator broken (T3 timestamp errata)
- **ECO2+ (v0.2+): Full FTM support** — XIAO ESP32-C6 boards ship with v0.2

**Runtime Detection Strategy:**
```c
#include "esp_chip_info.h"

bool rfip_has_ftm_initiator(void) {
    esp_chip_info_t chip_info;
    esp_chip_info(&chip_info);
    
    if (chip_info.model == CHIP_ESP32C6) {
        // ECO2 (revision 0.2) and later have FTM initiator fix
        return (chip_info.revision >= 2);
    }
    
    // Other chips with FTM support
    if (chip_info.model == CHIP_ESP32S2 ||
        chip_info.model == CHIP_ESP32C3 ||
        chip_info.model == CHIP_ESP32S3) {
        return true;
    }
    
    return false;
}
```

This enables graceful degradation: query silicon at boot, advertise capabilities in UTLP beacon, fall back to CSI/TDoA on older silicon.

### 2.2 ESP32 DevKit V1 (Chaos Monkey)

| Technology | Status | Notes |
|------------|--------|-------|
| **RSSI** | ✓ Full support | Available on all WiFi packets |
| **CSI** | ✓ Full support | Lowest quality of ESP32 family, but functional |
| **802.11mc FTM** | ✗ Not supported | No hardware capability |
| **ESP-NOW timestamps** | ✓ Available | TX/RX timestamps from radio |
| **BLE 4.2** | ✓ Classic + LE | RSSI only, no direction finding |

**Role:** Testing that core RFIP works WITHOUT fancy ranging. If it works on DevKit V1, it works anywhere.

### 2.3 HAL Abstraction Strategy

```c
typedef enum {
    RFIP_CAP_RSSI          = (1 << 0),  // All platforms
    RFIP_CAP_CSI           = (1 << 1),  // ESP32 family
    RFIP_CAP_UTLP_TDOA     = (1 << 2),  // Requires UTLP sync
    RFIP_CAP_FTM_INITIATOR = (1 << 3),  // ESP32-S2/C3/S3, ESP32-C6 ECO2+
    RFIP_CAP_FTM_RESPONDER = (1 << 4),  // All FTM-capable chips
    RFIP_CAP_UWB           = (1 << 5),  // External DW1000/DW3000 module
    RFIP_CAP_BLE_AOA       = (1 << 6),  // Future: BLE 5.1+ with antenna array
} rfip_capability_t;

typedef struct {
    rfip_capability_t capabilities;
    
    // Function pointers for HAL
    int32_t (*get_rssi)(uint8_t *mac);
    int32_t (*get_csi)(uint8_t *mac, csi_data_t *csi);
    int32_t (*get_ftm_range)(uint8_t *mac);
    int32_t (*get_uwb_range)(uint8_t *mac);
    int64_t (*get_rx_timestamp)(void);
} rfip_hal_t;

// Initialize HAL with runtime-detected capabilities
void rfip_hal_init(rfip_hal_t *hal) {
    hal->capabilities = RFIP_CAP_RSSI;  // Always available
    
    #if CONFIG_IDF_TARGET_ESP32C6 || CONFIG_IDF_TARGET_ESP32S2 || \
        CONFIG_IDF_TARGET_ESP32C3 || CONFIG_IDF_TARGET_ESP32S3
        hal->capabilities |= RFIP_CAP_CSI;
    #endif
    
    if (rfip_has_ftm_initiator()) {
        hal->capabilities |= RFIP_CAP_FTM_INITIATOR;
    }
    
    // FTM responder available on all FTM-capable silicon
    #if CONFIG_IDF_TARGET_ESP32C6 || CONFIG_IDF_TARGET_ESP32S2 || \
        CONFIG_IDF_TARGET_ESP32C3 || CONFIG_IDF_TARGET_ESP32S3
        hal->capabilities |= RFIP_CAP_FTM_RESPONDER;
    #endif
    
    // UWB detected via SPI probe at runtime
    if (rfip_probe_uwb()) {
        hal->capabilities |= RFIP_CAP_UWB;
    }
}
```

---

## 3. Ranging Technologies Deep Dive

### 3.1 RSSI-Based Ranging

**Principle:** Signal strength decreases with distance (inverse square law in free space).

**Reality:** Multipath, obstacles, antenna orientation make RSSI unreliable for absolute distance but useful for:
- Proximity detection (near/far)
- Relative distance changes
- Coarse positioning with fingerprinting

**ESP32 Implementation:**
```c
// RSSI available in wifi_promiscuous_pkt_t
typedef struct {
    wifi_pkt_rx_ctrl_t rx_ctrl;  // Contains rssi field
    uint8_t payload[0];
} wifi_promiscuous_pkt_t;

// Also available in ESP-NOW receive callback
void espnow_recv_cb(const uint8_t *mac, const uint8_t *data, int len) {
    wifi_promiscuous_pkt_t *pkt = ...;
    int8_t rssi = pkt->rx_ctrl.rssi;
}
```

### 3.2 CSI-Based Ranging (Channel State Information)

**Principle:** CSI provides amplitude and phase for each OFDM subcarrier (~52-64 subcarriers). This is FAR richer than RSSI's single value.

**Capabilities:**
- Subcarrier-level signal analysis
- Phase information (enables ToF estimation)
- Multipath characterization
- Human presence/motion detection
- Fingerprint-based positioning

**ESP32 CSI Quality Ranking:**
```
ESP32-C5 > ESP32-C6 > ESP32-C3 ≈ ESP32-S3 > ESP32
```

**ESP32 Implementation:**
```c
// Enable CSI collection
wifi_csi_config_t csi_config = {
    .lltf_en = true,
    .htltf_en = true,
    .stbc_htltf2_en = true,
    .ltf_merge_en = true,
    .channel_filter_en = false,
    .manu_scale = false,
};
esp_wifi_set_csi_config(&csi_config);
esp_wifi_set_csi_rx_cb(csi_callback, NULL);
esp_wifi_set_csi(true);

// CSI data structure
void csi_callback(void *ctx, wifi_csi_info_t *info) {
    // info->buf contains [Imag, Real] pairs for each subcarrier
    // info->len is buffer length
    // info->rx_ctrl contains rssi, noise_floor, etc.
}
```

**Resources:**
- Espressif ESP-CSI: https://github.com/espressif/esp-csi
- ESP32-CSI-Tool: https://github.com/StevenMHernandez/ESP32-CSI-Tool

### 3.3 TDoA from UTLP Beacons

**Principle:** If multiple anchors transmit at known times (UTLP provides this), receiver can compute position from Time Difference of Arrival.

**The UTLP Advantage:**
- Standard TDoA requires synchronized anchors (hard problem)
- UTLP already solves anchor synchronization
- Every beacon is a ranging opportunity

**Math:**
```
For anchors A, B, C at known positions:
  TDoA_AB = (t_arrival_A - t_arrival_B)
  Distance_diff_AB = TDoA_AB × speed_of_light
  
With 3+ anchors → hyperbolic intersection → position
```

**Precision estimate:**
- UTLP sync precision: ~10-100 μs
- Speed of light: ~300 m/μs
- Position error: ~3-30 meters from timing alone
- **With CSI phase refinement:** ~30cm possible

### 3.4 802.11mc FTM (Fine Time Measurement)

**Principle:** Two-way ranging with nanosecond timestamps.

```
Initiator                    Responder
    |-------- t1 -------->|
    |                     |  (t2 = arrival time)
    |                     |  (t3 = departure time)
    |<------- t4 ---------|
    
RTT = (t4 - t1) - (t3 - t2)
Distance = RTT × c / 2
```

**ESP32 Support Matrix:**

| Chip | Initiator | Responder | Notes |
|------|-----------|-----------|-------|
| ESP32 | ✗ | ✗ | No FTM support |
| ESP32-S2 | ✓ | ✓ | Full support |
| ESP32-C3 | ✓ | ✓ | Full support |
| ESP32-S3 | ✓ | ✓ | Full support |
| ESP32-C6 (ECO0/1) | ✗ | ✓ | T3 timestamp errata |
| ESP32-C6 (ECO2+) | ✓ | ✓ | **Full support** (silicon v0.2+) |

**Runtime Capability Advertisement:**

RFIP nodes should query silicon version at boot and advertise FTM capability in their beacons. This enables:
- Heterogeneous swarms (mixed silicon revisions)
- Automatic role assignment (FTM-capable nodes become ranging anchors)
- Graceful degradation (fall back to CSI/TDoA when FTM unavailable)

**Precision:**
- 80 MHz bandwidth: ~2 meter (90% CDF)
- 40 MHz bandwidth: ~4 meters
- 20 MHz bandwidth: ~8 meters

**ESP-IDF Example:** `examples/wifi/ftm/`

### 3.5 UWB (Ultra-Wideband) via DW3000

**Principle:** Very short pulses (~2ns) across wide bandwidth (500MHz+) enable centimeter-level ToF measurement.

**Hardware Options:**
- **Makerfabs ESP32-UWB-DW3000**: ESP32 + DW3000 integrated module
- **MaUWB**: ESP32 + STM32 + DW3000 with AT command interface (8 anchors, 32 tags)
- **DWM3000 module**: SPI interface to any MCU

**Capabilities:**
- ~10cm ranging accuracy
- 500m range (with proper antenna)
- Resistant to multipath (key advantage over WiFi)
- IEEE 802.15.4z compliant
- Interoperable with Apple U1 chip

**Integration with UTLP:**
- UWB provides high-precision range
- UTLP provides time synchronization for TDoA
- Combined: centimeter-level 3D positioning

**SPI Pinout (ESP32 + DW3000):**
```c
#define SPI_SCK   18
#define SPI_MISO  19
#define SPI_MOSI  23
#define DW_CS     4
#define DW_RST    27
#define DW_IRQ    34
```

### 3.6 BLE Direction Finding (Future)

**Principle:** Bluetooth 5.1 AoA (Angle of Arrival) uses antenna arrays to determine signal direction.

**Current ESP32 Status:**
- ESP32 family: BLE 5.0 only (no AoA/AoD)
- No current Espressif chip supports BLE 5.1 direction finding
- Requires external module (Nordic nRF52833, STM32WB09) with antenna array

**Future HAL Placeholder:**
```c
typedef struct {
    float azimuth_deg;    // Horizontal angle
    float elevation_deg;  // Vertical angle
    float confidence;     // Quality metric
} rfip_aoa_result_t;
```

---

## 4. RFIP Architecture

### 4.1 Layered Fusion Model

```
┌─────────────────────────────────────────────────┐
│              Application Layer                   │
│         (Position coordinates, geofencing)       │
├─────────────────────────────────────────────────┤
│              Fusion Layer                        │
│    (Kalman filter, particle filter, ML)          │
├─────────────────────────────────────────────────┤
│           Observation Layer                      │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐       │
│  │RSSI │ │ CSI │ │TDoA │ │ FTM │ │ UWB │       │
│  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘       │
├─────────────────────────────────────────────────┤
│              HAL Layer                           │
│     (Platform-specific implementations)          │
├─────────────────────────────────────────────────┤
│              UTLP Layer                          │
│        (Time synchronization foundation)         │
└─────────────────────────────────────────────────┘
```

### 4.2 The 802.11mc Enhancement Model

**Philosophy:** 802.11mc doesn't replace—it calibrates.

```
Without 802.11mc:
  - RSSI + CSI + TDoA → position estimate (±1-3m)
  - Useful for most applications

With 802.11mc available:
  - FTM provides ground truth ranges
  - Calibrates RSSI path-loss model
  - Calibrates CSI-to-distance mapping
  - Validates TDoA hyperbolic intersections
  - Result: sub-meter accuracy even when FTM unavailable
```

### 4.3 RF Tomography (Advanced)

**Insight:** The mesh becomes a distributed radar.

If Node A and Node B have ranging data, and something (Node C, a person, a wall) is between them:
- Direct path changes
- Multipath signatures change
- This is **information**, not noise

**Applications:**
- Detecting humans/objects between nodes
- Mapping room geometry
- Intrusion detection without cameras
- Occupancy sensing

---

## 5. Data Structures

> **🚚 Struct Packing Rule: Heavy Stuff First**
> 
> Pack structs like loading a moving truck — big stuff goes in first, small stuff fills the gaps.
> 
> ```c
> // BAD: Small stuff first = padding nightmare
> typedef struct {
>     uint8_t  flags;        // 1 byte + 7 bytes padding
>     uint64_t timestamp;    // 8 bytes
>     uint8_t  mac[6];       // 6 bytes + 2 bytes padding
>     uint32_t range_mm;     // 4 bytes
> } bad_t;  // 28 bytes with hidden padding
> 
> // GOOD: Heavy first, light fills gaps
> typedef struct {
>     uint64_t timestamp;    // 8 bytes (aligned)
>     uint32_t range_mm;     // 4 bytes (aligned)
>     uint8_t  mac[6];       // 6 bytes
>     uint8_t  flags;        // 1 byte
>     uint8_t  _pad;         // 1 byte (explicit, intentional)
> } good_t;  // 20 bytes, no surprise padding
> ```
> 
> **Rule of thumb:** `uint64_t` → `uint32_t` → `uint16_t` → `uint8_t` → bitfields
> 
> *If you put all the small boxes in the truck first, good luck with that couch.*

### 5.1 Observation Types

```c
typedef enum {
    RFIP_OBS_RSSI,
    RFIP_OBS_CSI,
    RFIP_OBS_TDOA,
    RFIP_OBS_FTM,
    RFIP_OBS_UWB,
    RFIP_OBS_AOA,
} rfip_obs_type_t;

// Packed heavy-first: 64-bit → pointers → 32-bit → 8-bit
typedef struct {
    int64_t         timestamp_us;    // 8 bytes - UTLP atomic time
    
    union {                          // Union size = largest member
        struct { int8_t *data; size_t len; } csi;  // pointer + size_t
        struct { int64_t tdoa_us; uint8_t anchor_mac[6]; } tdoa;
        struct { uint32_t range_mm; } ftm;
        struct { uint32_t range_mm; } uwb;
        struct { float azimuth; float elevation; } aoa;  // 8 bytes
        struct { int8_t rssi_dbm; } rssi;
    };
    
    uint8_t         peer_mac[6];     // 6 bytes
    rfip_obs_type_t type;            // 1 byte (enum)
    uint8_t         confidence;      // 1 byte (0-255 maps to 0.0-1.0)
} rfip_observation_t;
```

### 5.2 Anchor Registry

```c
// Packed heavy-first: floats (4 bytes) → arrays → single bytes
typedef struct {
    float    x, y, z;           // 12 bytes - Known position (meters)
    uint32_t last_seen_ms;      // 4 bytes
    uint8_t  mac[6];            // 6 bytes
    uint8_t  capabilities;      // 1 byte - What observations it can provide
    uint8_t  health_score;      // 1 byte - UTLP trust metric
} rfip_anchor_t;  // 24 bytes, naturally aligned

#define RFIP_MAX_ANCHORS 16

typedef struct {
    rfip_anchor_t anchors[RFIP_MAX_ANCHORS];
    uint8_t       count;
    uint8_t       _pad[3];      // Explicit padding for 4-byte alignment
} rfip_anchor_registry_t;
```

### 5.3 Position Estimate

```c
// Packed heavy-first: 64-bit → floats → single bytes
typedef struct {
    int64_t  timestamp_us;      // 8 bytes - UTLP atomic time
    float    x, y, z;           // 12 bytes - Position estimate (meters)
    float    error_x, error_y, error_z;  // 12 bytes - Uncertainty (1σ)
    uint8_t  num_observations;  // 1 byte - How many data points used
    uint8_t  quality;           // 1 byte - Overall quality metric 0-255
    uint8_t  _pad[2];           // 2 bytes - Explicit padding
} rfip_position_t;  // 36 bytes
```

---

## 6. Integration Strategy

### 6.1 Phase 1: RSSI Baseline
- [ ] Collect RSSI from ESP-NOW beacons
- [ ] Path-loss model calibration
- [ ] Proximity detection (near/far)
- [ ] Basic trilateration with known anchors

### 6.2 Phase 2: CSI Integration
- [ ] Enable CSI collection on ESP32-C6
- [ ] CSI-to-distance mapping
- [ ] Fingerprint database for known locations
- [ ] Motion/presence detection

### 6.3 Phase 3: TDoA from UTLP
- [ ] Extract TX timestamps from UTLP beacons
- [ ] Hyperbolic intersection solver
- [ ] Fusion with RSSI/CSI observations

### 6.4 Phase 4: 802.11mc Enhancement
- [ ] FTM responder mode on ESP32-C6
- [ ] FTM initiator on ESP32-S2/C3/S3 (if available)
- [ ] Calibration loop for other observations
- [ ] Ground truth validation

### 6.5 Phase 5: UWB Integration (Optional)
- [ ] DW3000 SPI driver
- [ ] Two-way ranging protocol
- [ ] Integration with UTLP time base
- [ ] Centimeter-level positioning

### 6.6 Phase 6: Fusion & ML
- [ ] Kalman filter for observation fusion
- [ ] Particle filter for non-Gaussian scenarios
- [ ] TinyML for on-device inference
- [ ] Adaptive model selection

---

## 7. Prior Art Extension Claims

*Claims to be added after implementation validates concepts.*

### 7.1 Preliminary Claims

1. **UTLP-enabled TDoA without infrastructure**: Using UTLP time synchronization to enable Time Difference of Arrival positioning without dedicated timing infrastructure; every synchronized node is a potential ranging anchor
2. **Layered observation fusion with graceful degradation**: Position estimation that uses all available observations (RSSI, CSI, TDoA, FTM, UWB) with automatic fallback when higher-precision sources unavailable
3. **802.11mc as calibration, not foundation**: Using FTM ranging to calibrate other observation models rather than as primary positioning source; enables precision even when FTM unavailable
4. **RF tomography from timing mesh**: Using changes in ranging/CSI between node pairs to detect objects/humans in the RF path; mesh as distributed radar
5. **HAL abstraction for heterogeneous ranging**: Platform capability flags enabling same positioning code across devices with different hardware (ESP32 variants, UWB modules, future BLE AoA)
6. **Runtime silicon capability detection**: Query chip revision at boot to determine available ranging features (e.g., FTM initiator on ESP32-C6 ECO2+ vs ECO0/1); advertise capabilities in beacon; enables heterogeneous swarms with automatic role assignment and graceful degradation on older silicon

---

## 8. References

### 8.1 Espressif Documentation
- ESP-IDF WiFi Driver: https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/api-guides/wifi.html
- ESP-CSI Guide: https://github.com/espressif/esp-csi
- ESP32-C6 FTM Errata: https://docs.espressif.com/projects/esp-chip-errata/en/latest/esp32c6/

### 8.2 Academic References
- "Fine Time Measurement for IoT: A Practical Approach Using ESP32" (IEEE, 2022)
- "WiFi Sensing on the Edge" - ESP32 CSI Toolkit paper

### 8.3 Hardware
- Makerfabs ESP32-UWB-DW3000: https://github.com/Makerfabs/Makerfabs-ESP32-UWB-DW3000
- Qorvo DWM3000 Datasheet

### 8.4 Related Documents
- Connectionless Distributed Timing Prior Art (DOI: 10.5281/zenodo.18078265)
- UTLP Technical Supplement S2

---

**Author:** Steve (mlehaptics Project)

---

*Document version: Draft 0.1*
*Status: Initial specification for review*
*Repository: https://github.com/lemonforest/mlehaptics*
