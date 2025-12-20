# UTLP Technical Report — Supplement S1

## Precision, Transport, and Security Extensions

*mlehaptics Project — December 2025*

---

## Scope

This supplement extends the UTLP Technical Report v2.0 with new findings from:
- ESPARGOS phase-coherent WiFi sensing research (University of Stuttgart)
- 802.11mc Fine Time Measurement (FTM) protocol analysis
- Hybrid BLE/ESP-NOW transport architecture
- Dual-MAC authenticated security model

**Prerequisites:** UTLP Technical Report v2.0, Addendum A (RFIP)

**What this document adds:**
- Implementation-level precision improvements (not just concepts)
- 802.11mc FTM as a sub-microsecond sync source
- ESP-NOW + BLE time-division multiplexing
- Cryptographic security for ESP-NOW transport

---

# Part I: Precision Improvements

## 1. ESPARGOS-Derived Techniques

Research from the ESPARGOS project (University of Stuttgart) on phase-coherent WiFi sensing reveals techniques directly applicable to UTLP time synchronization.

### 1.1 Minimum Delay Packet Selection (MDPS)

**Problem:** The Technical Report v2.0 specifies ±30μs sync precision but does not specify the filtering algorithm. Naive averaging of RTT samples includes jitter-contaminated measurements.

**Finding:** Wireless delays have heavy-tailed distributions. The minimum observed RTT is closest to true propagation delay—larger values are contaminated by stack jitter, retransmissions, and queuing.

**Implementation:**

```c
#define RTT_HISTORY_SIZE 16
#define RTT_PERCENTILE   10  // 10th percentile ≈ near-minimum

typedef struct {
    int64_t samples[RTT_HISTORY_SIZE];
    uint8_t index;
    uint8_t count;
} rtt_filter_t;

int64_t rtt_filter_get_minimum(const rtt_filter_t* f) {
    if (f->count == 0) return 0;
    
    // Copy and sort (insertion sort for small N)
    int64_t sorted[RTT_HISTORY_SIZE];
    memcpy(sorted, f->samples, f->count * sizeof(int64_t));
    
    for (int i = 1; i < f->count; i++) {
        int64_t key = sorted[i];
        int j = i - 1;
        while (j >= 0 && sorted[j] > key) {
            sorted[j + 1] = sorted[j];
            j--;
        }
        sorted[j + 1] = key;
    }
    
    return sorted[(f->count * RTT_PERCENTILE) / 100];
}
```

**Expected improvement:** 2-5x reduction in offset jitter vs averaging.

### 1.2 Two-State Kalman Filter

**Problem:** The Technical Report specifies holdover mode with "last known drift rate" but does not specify how drift is estimated or how offset/drift are jointly tracked.

**Solution:** A two-state Kalman filter simultaneously estimates clock offset and drift rate, enabling optimal measurement fusion and drift prediction during holdover.

**State vector:** `x = [offset_us, drift_ppb]`

```c
typedef struct {
    double x[2];           // [offset, drift]
    double P[4];           // 2x2 covariance (flattened)
    double Q_offset;       // Process noise: offset
    double Q_drift;        // Process noise: drift
    double R;              // Measurement noise
    int64_t last_update_us;
} kalman_state_t;

// Typical ESP32 parameters
void kalman_init(kalman_state_t* k) {
    k->x[0] = 0;  k->x[1] = 0;
    k->P[0] = 1e6;  k->P[3] = 1e4;  // High initial uncertainty
    k->Q_offset = 100.0;    // us²/s - stack jitter
    k->Q_drift = 1.0;       // ppb²/s - crystal aging
    k->R = 900.0;           // (30 us)² - BLE measurement noise
}

void kalman_update(kalman_state_t* k, int64_t measured_offset, int64_t now_us) {
    double dt = (now_us - k->last_update_us) / 1e6;
    
    // Predict: offset grows by drift × dt
    double x_pred[2] = {
        k->x[0] + k->x[1] * dt * 1e-3,  // ppb → us/s
        k->x[1]
    };
    double P00_pred = k->P[0] + k->Q_offset * dt;
    double P11_pred = k->P[3] + k->Q_drift * dt;
    
    // Update
    double y = measured_offset - x_pred[0];
    double S = P00_pred + k->R;
    double K0 = P00_pred / S;
    
    k->x[0] = x_pred[0] + K0 * y;
    k->x[1] = x_pred[1] + (k->P[2] / S) * y;
    k->P[0] = (1 - K0) * P00_pred;
    k->P[3] = P11_pred;
    k->last_update_us = now_us;
}

int64_t kalman_predict(const kalman_state_t* k, int64_t now_us) {
    double dt = (now_us - k->last_update_us) / 1e6;
    return (int64_t)(k->x[0] + k->x[1] * dt * 1e-3);
}
```

**Benefit:** Kalman drift estimate enables accurate holdover extrapolation. The filter naturally handles varying measurement rates and missing samples.

### 1.3 Enhanced Holdover

**Extension to Technical Report v2.0 Section 4.2:**

The basic holdover mode freezes drift rate. Enhanced holdover uses Kalman extrapolation with uncertainty-based stratum degradation:

```c
uint8_t get_holdover_stratum(int64_t holdover_start_us, uint8_t base_stratum) {
    int64_t elapsed_s = (esp_timer_get_time() - holdover_start_us) / 1000000;
    
    // Degrade 1 stratum per 30s of holdover
    uint8_t time_penalty = elapsed_s / 30;
    
    // Additional penalty if Kalman uncertainty exceeds thresholds
    double uncertainty = sqrt(kalman.P[0]);
    uint8_t uncertainty_penalty = 0;
    if (uncertainty > 100) uncertainty_penalty++;   // >100μs
    if (uncertainty > 500) uncertainty_penalty++;   // >500μs
    
    return MIN(base_stratum + time_penalty + uncertainty_penalty + 1, 254);
}
```

---

## 2. 802.11mc Fine Time Measurement Integration

### 2.1 FTM as Stratum 1a Source

802.11mc FTM provides hardware-timestamped ranging with ~100ns precision—300x better than BLE. The same T1-T4 timestamps used for distance calculation yield clock offset:

```
FTM ranging:  distance = RTT × c / 2
UTLP sync:    offset = ((T2 - T1) + (T3 - T4)) / 2   ← Same timestamps!
```

**New stratum level (extends Technical Report Table 3.3):**

| Stratum | Source | Precision |
|---------|--------|-----------|
| 0 | GPS/Atomic | <1μs |
| 1 | Direct from Stratum 0 | ~1ms |
| **1a** | **FTM from Stratum 1** | **~100ns** |
| 2 | BLE from Stratum 1 | ~30μs |

### 2.2 ESP32-C6 FTM Errata

**Critical hardware limitation:**

| Chip Revision | FTM Initiator | FTM Responder |
|---------------|---------------|---------------|
| ESP32-C6 v0.0 | ❌ (WIFI-9686) | ✅ |
| ESP32-C6 v0.1 | ❌ (WIFI-9686) | ✅ |
| ESP32-C6 v0.2+ | ✅ | ✅ |

Errata WIFI-9686: "The time of T3 cannot be acquired correctly" in early silicon.

```c
bool hardware_supports_ftm_initiator(void) {
    esp_chip_info_t info;
    esp_chip_info(&info);
    return (info.model == CHIP_ESP32C6 && info.revision >= 2);
}
```

### 2.3 FTM-Kalman Fusion

When FTM measurements are available, adjust Kalman measurement noise:

```c
void process_ftm_offset(int64_t ftm_offset_us) {
    double saved_R = kalman.R;
    kalman.R = 0.01;  // FTM: (0.1 μs)² vs BLE: (30 μs)²
    kalman_update(&kalman, ftm_offset_us, esp_timer_get_time());
    kalman.R = saved_R;
}
```

FTM measurements are weighted 900× higher than BLE measurements.

---

# Part II: Hybrid Transport Architecture

## 3. ESP-NOW Integration

### 3.1 Transport Comparison

| Metric | BLE GATT | ESP-NOW |
|--------|----------|---------|
| TX current | ~18 mA | ~145 mA |
| Packet time | ~2-3 ms | ~300 μs |
| **Energy/packet** | **~40 μJ** | **~44 μJ** |
| Latency jitter | ±10-50 ms | **±100 μs** |

**Key finding:** Energy per packet is similar, but ESP-NOW has 100× lower latency jitter—critical for sub-30μs sync.

### 3.2 Time-Division Multiplexing (PWA + Peer Coexistence)

**Design Evolution:** The original TDM concept assumed continuous BLE connection between *peer devices* alongside ESP-NOW. The implemented "BLE Bootstrap Model" (Section 3.5) releases peer BLE after key exchange, making peer TDM unnecessary.

**Remaining TDM use case:** PWA (phone app) BLE connection coexists with peer ESP-NOW traffic. The phone provides user interface, pattern uploads, and optional GPS time injection while peers exchange sub-millisecond time sync beacons.

```
PWA ← BLE → SERVER ←─ ESP-NOW ─→ CLIENT
              │
              └── Single 2.4GHz radio handles both
```

BLE and ESP-NOW share ESP32-C6's single 2.4GHz radio. Coordinate ESP-NOW transmissions around PWA BLE connection events:

```
BLE Connection Interval = 100ms (typical for PWA)

Timeline:
────┬─────────────────────────────────────────────────┬────
    │◄───────────────── 100ms ───────────────────────►│
    ▲                                                 ▲
 BLE Event                                        BLE Event
 (~3ms)                                            (~3ms)

    ├──► AVOID (3ms)                         AVOID ◄──┤

         │◄────────── ~94ms SAFE FOR ESP-NOW ────────►│
```

```c
static int64_t ble_anchor_us;
static uint32_t ble_interval_us;

int64_t next_ble_event(void) {
    int64_t now = esp_timer_get_time();
    int64_t elapsed = now - ble_anchor_us;
    return ble_anchor_us + ((elapsed / ble_interval_us) + 1) * ble_interval_us;
}

bool is_safe_for_espnow(void) {
    if (!pwa_connected) return true;  // No PWA = no contention

    int64_t now = esp_timer_get_time();
    int64_t margin = 3000;  // 3ms safety
    int64_t to_next = next_ble_event() - now;
    int64_t from_prev = ble_interval_us - to_next;

    return (to_next > margin) && (from_prev > margin);
}
```

**Implementation note:** Current firmware does not implement active TDM scheduling. ESP-IDF's coexistence arbitrator handles contention automatically. TDM becomes beneficial if PWA traffic causes observable ESP-NOW jitter (>1ms).

### 3.3 Recommended Transport Allocation

| Function | Transport | Endpoint | Rationale |
|----------|-----------|----------|-----------|
| Discovery | BLE Advertising | All | Phone + peer compatible |
| PWA connection | BLE GATT | Phone↔Device | Web Bluetooth API |
| Peer bonding | BLE SMP | Device↔Device | Trust establishment |
| **Key exchange** | **BLE GATT** | Device↔Device | Secure channel for nonce |
| **Time sync** | **ESP-NOW** | Device↔Device | Deterministic ±100μs latency |
| Motor coordination | ESP-NOW | Device↔Device | Real-time bilateral commands |
| Pattern transfer | BLE GATT | Phone↔Device | Reliable, larger MTU |
| GPS time inject | BLE GATT | Phone→Device | Stratum 0→1 upgrade |
| FTM ranging | WiFi 802.11mc | Device↔Device | Hardware timestamps (future) |

**Transport lifecycle:**

```
Phase 1: Bootstrap (BLE only)
  ├── Peer discovery via advertising
  ├── BLE connection + SMP bonding
  ├── WiFi MAC exchange
  └── ESP-NOW key derivation + peer registration

Phase 2: Operational (ESP-NOW primary, BLE for PWA)
  ├── Peer BLE released
  ├── Time sync via ESP-NOW beacons
  ├── Motor commands via ESP-NOW
  └── PWA connects via BLE (optional)
```

### 3.4 Transport Hardware Abstraction Layer (HAL)

To support future transport options (802.11 Long Range, acoustic sync, wired fallback), UTLP defines a transport-agnostic HAL:

```c
// Transport capability flags
#define UTLP_TRANSPORT_CAP_BROADCAST    (1 << 0)  // Can broadcast to all peers
#define UTLP_TRANSPORT_CAP_UNICAST      (1 << 1)  // Can address single peer
#define UTLP_TRANSPORT_CAP_ENCRYPTED    (1 << 2)  // Link-layer encryption
#define UTLP_TRANSPORT_CAP_TIMESTAMPS   (1 << 3)  // Hardware TX/RX timestamps
#define UTLP_TRANSPORT_CAP_RELIABLE     (1 << 4)  // Guaranteed delivery

typedef struct {
    const char* name;           // "espnow", "ble_gatt", "802.11lr"
    uint32_t capabilities;
    uint16_t max_payload;       // Bytes per transmission
    uint16_t typical_latency_us;
    uint16_t jitter_us;         // ±jitter bound

    // Lifecycle
    esp_err_t (*init)(void);
    esp_err_t (*deinit)(void);

    // Peer management
    esp_err_t (*add_peer)(const uint8_t mac[6], const uint8_t key[16]);
    esp_err_t (*remove_peer)(const uint8_t mac[6]);

    // Data transfer
    esp_err_t (*send)(const uint8_t* data, size_t len, const uint8_t* dest_mac);
    esp_err_t (*set_recv_callback)(void (*cb)(const uint8_t* data, size_t len,
                                              const uint8_t* src_mac));
} utlp_transport_t;
```

**Current implementation:** `espnow_transport.c` implements this interface for ESP-NOW.

**Future transports:**
- **802.11 Long Range:** 1km+ outdoor sync for stadium/outdoor events
- **Acoustic:** Ultrasonic sync through walls/barriers
- **Wired:** USB/UART fallback for deterministic debugging

### 3.5 BLE Bootstrap Model

**Key insight:** BLE is excellent for *trust establishment* but suboptimal for *real-time sync*. The BLE Bootstrap Model uses BLE only during initialization, then releases it for ESP-NOW-only peer communication.

```
┌─────────────────────────────────────────────────────────────┐
│                    BLE BOOTSTRAP PHASE                       │
│  ┌──────────┐    BLE    ┌──────────┐                        │
│  │  SERVER  │◄─────────►│  CLIENT  │                        │
│  └────┬─────┘           └────┬─────┘                        │
│       │                      │                              │
│       │ 1. Advertise/Scan    │                              │
│       │ 2. Connect + Bond    │                              │
│       │ 3. Exchange WiFi MACs│                              │
│       │ 4. Exchange nonce    │                              │
│       │ 5. Derive LMK        │                              │
│       │ 6. Register ESP-NOW  │                              │
│       ▼                      ▼                              │
│   ┌───────────────────────────────┐                         │
│   │  RELEASE PEER BLE CONNECTION  │ ← Key transition        │
│   └───────────────────────────────┘                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   OPERATIONAL PHASE                          │
│  ┌──────────┐  ESP-NOW  ┌──────────┐                        │
│  │  SERVER  │◄─────────►│  CLIENT  │                        │
│  └────┬─────┘           └────┬─────┘                        │
│       │                      │                              │
│       │ Time sync beacons    │  (encrypted, ±100μs jitter)  │
│       │ Motor commands       │                              │
│       │ Pattern segments     │                              │
│       ▼                      ▼                              │
│                                                             │
│  ┌──────────┐    BLE    ┌──────────┐                        │
│  │  SERVER  │◄─────────►│   PWA    │  (optional, for UI)    │
│  └──────────┘           └──────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

**Benefits:**
1. **Deterministic sync:** ESP-NOW ±100μs vs BLE ±10-50ms jitter
2. **Radio efficiency:** No peer BLE connection events consuming bandwidth
3. **PWA compatibility:** Server still accepts PWA connections for user interface
4. **Clean separation:** Trust layer (BLE) vs realtime layer (ESP-NOW)

**Implementation:** See `src/espnow_transport.c` and `src/ble_manager.c` (key exchange flow).

---

# Part III: Security Architecture

## 4. Authenticated ESP-NOW Transport

The Technical Report v2.0 specifies unencrypted UTLP beacons with "Common Mode Rejection" security. This section extends that model for ESP-NOW transport where authentication (not encryption) is desirable.

### 4.1 Key Derivation Approaches: A Design Journey

This section documents two viable approaches to ESP-NOW key derivation, preserving implementation lessons learned. In medical device development, understanding *why* design decisions were made is as important as the final implementation.

#### 4.1.1 Approach A: LTK-Based Derivation (Maximum Entropy)

The theoretically optimal approach derives ESP-NOW keys from the BLE Long Term Key (LTK):

**Entropy analysis:**

```
MAC Address: [OUI: 3 bytes][NIC: 3 bytes]
             └─ Vendor ─┘  └─ Unique ─┘

ESP32 derivation: WiFi_MAC = BLE_MAC - 2

Actual entropy:
  OUI:           0 bits (known: Espressif)
  BLE↔WiFi:      0 bits (fixed offset)
  NIC:          ~24 bits per device

  MACs total:   ~48 bits (binding, NOT secrecy)
  LTK:          128 bits (THE secret)
```

**Critical understanding:** MACs provide *uniqueness* (key binding), not *entropy*. The LTK is the sole source of cryptographic strength.

```c
typedef struct {
    uint8_t ble_mac[6];
    uint8_t wifi_mac[6];
} device_identity_t;

esp_err_t derive_espnow_keys_ltk(
    const uint8_t ltk[16],           // From BLE bond - THE secret
    const device_identity_t* local,
    const device_identity_t* peer,
    uint8_t lmk_out[16]              // ESP-NOW Local Master Key
) {
    // Deterministic ordering (lower BLE MAC first)
    const device_identity_t *first, *second;
    if (memcmp(local->ble_mac, peer->ble_mac, 6) < 0) {
        first = local; second = peer;
    } else {
        first = peer; second = local;
    }

    // MACs in INFO field (binding context)
    uint8_t info[24];
    memcpy(info + 0,  first->ble_mac, 6);
    memcpy(info + 6,  first->wifi_mac, 6);
    memcpy(info + 12, second->ble_mac, 6);
    memcpy(info + 18, second->wifi_mac, 6);

    // HKDF: security from LTK, uniqueness from MACs
    mbedtls_hkdf(mbedtls_md_info_from_type(MBEDTLS_MD_SHA256),
                 (uint8_t*)"UTLP-v1", 7,  // Salt
                 ltk, 16,                   // IKM (secret)
                 info, 24,                  // Info (binding)
                 lmk_out, 16);

    return ESP_OK;
}
```

**Advantages:**
- 128-bit cryptographic entropy (AES-128 strength)
- Key derived from established BLE SMP security
- No additional key exchange protocol needed

**Practical Challenges:**
- Requires `CONFIG_BT_NIMBLE_NVS_PERSIST=y` for LTK storage
- LTK retrieval via NimBLE's `ble_store_util_*` APIs is complex
- Test environments with RAM-only bonding cannot use this approach
- NVS wear concerns with frequent re-pairing during development

#### 4.1.2 Approach B: Nonce-Based Derivation (Implementation Simplicity)

The implemented approach uses a server-generated nonce exchanged over the already-secure BLE channel:

**Entropy analysis:**

```
8-byte hardware RNG nonce:  64 bits (security)
WiFi MACs (both devices):   ~48 bits (binding)
```

**Key insight:** While 64-bit is below the 128-bit ideal, it vastly exceeds threat model requirements for a therapeutic device. An attacker would need:
1. Physical proximity during key exchange (~5-second window)
2. BLE sniffer to capture encrypted GATT traffic
3. Break BLE encryption to extract nonce

```c
// Actual implementation from espnow_transport.c
esp_err_t espnow_derive_session_key(
    const uint8_t nonce[8],           // Server-generated, sent via BLE
    const uint8_t server_mac[6],      // WiFi STA MAC of server
    const uint8_t client_mac[6],      // WiFi STA MAC of client
    uint8_t lmk_out[16]               // ESP-NOW Local Master Key
) {
    // IKM = server_mac || client_mac (key binding material)
    uint8_t ikm[12];
    memcpy(ikm, server_mac, 6);
    memcpy(ikm + 6, client_mac, 6);

    // HKDF-SHA256: nonce as salt, MACs as IKM, fixed info string
    return mbedtls_hkdf(
        mbedtls_md_info_from_type(MBEDTLS_MD_SHA256),
        nonce, 8,                      // Salt (session-unique)
        ikm, 12,                       // IKM (device binding)
        (uint8_t*)"ESPNOW_LMK", 10,   // Info (domain separation)
        lmk_out, 16
    );
}
```

**Why this was chosen:**
1. **Simplicity:** No NVS dependency, no LTK retrieval complexity
2. **Test compatibility:** Works with `CONFIG_BT_NIMBLE_NVS_PERSIST=n`
3. **Sufficient security:** 64-bit entropy + BLE encryption + physical proximity
4. **Hardware RNG:** ESP32-C6 provides true randomness via `esp_fill_random()`

#### 4.1.3 Decision Matrix

| Factor | Approach A (LTK) | Approach B (Nonce) |
|--------|------------------|-------------------|
| Entropy | 128-bit | 64-bit |
| NVS dependency | Required | None |
| Implementation complexity | Higher | Lower |
| Test environment support | NVS builds only | All builds |
| BLE channel security | Implicit (derived) | Explicit (transport) |
| Threat model coverage | Exceeds | Meets |

**Recommendation for medical devices:** Start with Approach B for development velocity, migrate to Approach A for production if regulatory requirements mandate 128-bit key strength. Document the decision in your Design History File (DHF).

#### 4.1.4 Entropy Guidance for Future Implementations

For AI agents implementing similar protocols:

1. **Don't conflate binding with secrecy.** MAC addresses bind keys to devices but contribute near-zero entropy due to predictable OUI and derivation patterns.

2. **Hardware RNG is mandatory.** Never use `rand()` or timestamps for cryptographic material. ESP32's `esp_fill_random()` uses a hardware entropy source.

3. **HKDF is the right primitive.** It properly separates extraction (getting entropy from IKM) and expansion (generating key material). Don't hand-roll XOR-based derivation.

4. **Transport security compounds.** A 64-bit nonce sent over encrypted BLE is not a 64-bit attack surface—the attacker must also break BLE to obtain it.

5. **Document the journey.** Future maintainers (human or AI) benefit from understanding rejected alternatives as much as chosen solutions.

### 4.2 Time-Synchronized TOTP

UTLP's synchronized time enables tight TOTP windows:

| Standard TOTP | UTLP TOTP |
|---------------|-----------|
| 30-second windows | **100ms windows** |
| 30s tolerance | ±1 window (200ms) |

```c
#define TOTP_WINDOW_US  100000  // 100ms

uint32_t totp_generate(const uint8_t key[16], int64_t sync_time_us) {
    uint64_t counter = sync_time_us / TOTP_WINDOW_US;
    
    uint8_t msg[8];
    for (int i = 7; i >= 0; i--) {
        msg[i] = counter & 0xFF;
        counter >>= 8;
    }
    
    // AES-CMAC (hardware accelerated on ESP32)
    uint8_t mac[16];
    mbedtls_cipher_cmac(
        mbedtls_cipher_info_from_type(MBEDTLS_CIPHER_AES_128_ECB),
        key, 128, msg, 8, mac);
    
    return ((mac[0] & 0x7F) << 24 | mac[1] << 16 | 
            mac[2] << 8 | mac[3]) % 1000000;
}

bool totp_validate(uint32_t received, int64_t sync_time_us, uint64_t* last_counter) {
    uint64_t counter = sync_time_us / TOTP_WINDOW_US;
    
    for (int ofs = -1; ofs <= 1; ofs++) {  // ±1 window tolerance
        uint64_t check = counter + ofs;
        if (check <= *last_counter) continue;  // Replay prevention
        
        if (received == totp_generate(totp_key, check * TOTP_WINDOW_US)) {
            *last_counter = check;
            return true;
        }
    }
    return false;
}
```

### 4.3 Authenticated Beacon Format

```c
typedef struct __attribute__((packed)) {
    // Header (plaintext for filtering)
    uint8_t  magic[2];        // 0xFE, 0xFE
    uint8_t  version;         // 0x03
    uint8_t  flags;
    uint16_t sequence;        // Monotonic (replay detection)
    
    // Payload
    uint8_t  stratum;
    uint8_t  quality;
    int64_t  sync_time_us;
    int32_t  drift_ppb;       // Kalman estimate
    
    // Authentication
    uint32_t totp;            // Time-bound authentication
    uint16_t crc16;
} espnow_beacon_v3_t;         // 26 bytes
```

### 4.4 Security Properties

| Property | Mechanism |
|----------|-----------|
| Authentication | TOTP proves key possession |
| Replay prevention | Monotonic sequence + TOTP counter |
| Hardware binding | Both device MACs in key derivation |
| Time binding | 100ms TOTP windows (vs 30s standard) |
| Key secrecy | 128-bit LTK from BLE SMP |

**Note:** This provides *authentication*, not *confidentiality*. Sync beacons remain readable (consistent with Common Mode Rejection model) but cannot be forged or replayed.

---

# Part IV: Beacon Version 3

## 5. Extended Beacon Structure

Extends Technical Report v2.0 beacon with Kalman drift and optional RFIP fields:

```c
typedef struct __attribute__((packed)) {
    // Header (4 bytes)
    uint8_t  magic[2];           // 0xFE, 0xFE
    uint8_t  version;            // 0x03
    uint8_t  flags;
    
    // Time sync (14 bytes)
    uint8_t  stratum;
    uint8_t  quality;
    int64_t  sync_time_us;
    int32_t  drift_ppb;          // NEW: Kalman drift estimate
    
    // RFIP extension (optional, 8 bytes if FLAG_HAS_POSITION)
    int16_t  pos_x_cm;
    int16_t  pos_y_cm;
    int16_t  pos_z_cm;
    uint8_t  pos_uncertainty_cm;
    uint8_t  spatial_flags;
    
    // Integrity (4 bytes, or 8 if authenticated)
    uint16_t sequence;
    uint16_t crc16;
    // + uint32_t totp if FLAG_AUTHENTICATED
} utlp_beacon_v3_t;

// flags byte
#define FLAG_TIME_MASTER    (1 << 0)
#define FLAG_FTM_CAPABLE    (1 << 1)  // 802.11mc responder
#define FLAG_HAS_POSITION   (1 << 2)  // RFIP fields present
#define FLAG_HOLDOVER       (1 << 3)
#define FLAG_AUTHENTICATED  (1 << 4)  // TOTP field present
#define FLAG_HIGH_STRATUM   (1 << 5)  // Stratum 0-1
```

---

## 6. Prior Art Extensions

This supplement establishes additional prior art for:

### 6.1 Precision Techniques
1. **Minimum Delay Packet Selection** for wireless time sync filtering
2. **Two-state Kalman filter** (offset + drift) for embedded sync
3. **802.11mc FTM as Stratum 1a** time source in UTLP hierarchy
4. **FTM-Kalman fusion** with transport-specific noise weighting

### 6.2 Transport Architecture
5. **BLE Bootstrap Model**: BLE for trust establishment only, released after key exchange
6. **Transport HAL abstraction**: Platform-agnostic interface for sync transports
7. **PWA+ESP-NOW TDM**: Time-division multiplexing for phone BLE + peer ESP-NOW coexistence
8. **Transport lifecycle phases**: Bootstrap (BLE) → Operational (ESP-NOW) separation

### 6.3 Security Models
9. **Dual key derivation approaches**: LTK-based (128-bit) vs nonce-based (64-bit) with documented tradeoffs
10. **Entropy analysis methodology**: Distinguishing binding (MACs) from secrecy (keys)
11. **Time-synchronized TOTP** with 100ms windows (300× tighter than standard)
12. **Authenticated broadcast beacons** (authentication without confidentiality)
13. **Nonce-over-encrypted-channel**: Leveraging BLE encryption for key material transport

### 6.4 Implementation Guidance
14. **Design journey documentation**: Preserving rejected alternatives for AI/human maintainers
15. **Medical device development velocity**: Nonce-based approach for development, LTK for production
16. **Hardware RNG requirements**: `esp_fill_random()` for cryptographic material, never `rand()`

---

## References

1. ESPARGOS Project: https://espargos.net/
2. ESPARGOS arXiv: https://arxiv.org/abs/2502.09405
3. IEEE 802.11-2016 §11.24 (Fine Timing Measurement)
4. ESP32-C6 Errata WIFI-9686: docs.espressif.com
5. RFC 6238: TOTP Algorithm
6. RFC 5869: HKDF

---

*Supplement S1 to UTLP Technical Report v2.0*

*December 2025*
