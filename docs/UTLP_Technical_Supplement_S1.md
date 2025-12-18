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

### 3.2 Time-Division Multiplexing

BLE and ESP-NOW share ESP32-C6's single 2.4GHz radio. Coordinate access around BLE connection events:

```
BLE Connection Interval = 100ms

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
    if (!ble_connected) return true;
    
    int64_t now = esp_timer_get_time();
    int64_t margin = 3000;  // 3ms safety
    int64_t to_next = next_ble_event() - now;
    int64_t from_prev = ble_interval_us - to_next;
    
    return (to_next > margin) && (from_prev > margin);
}
```

### 3.3 Recommended Transport Allocation

| Function | Transport | Rationale |
|----------|-----------|-----------|
| Discovery | BLE Advertising | Phone compatible |
| PWA connection | BLE GATT | Web Bluetooth API |
| Bonding | BLE SMP | Established crypto |
| **Time sync** | **ESP-NOW** | Deterministic latency |
| Pattern transfer | BLE GATT | Reliable, larger MTU |
| FTM ranging | WiFi 802.11mc | Hardware timestamps |

---

# Part III: Security Architecture

## 4. Authenticated ESP-NOW Transport

The Technical Report v2.0 specifies unencrypted UTLP beacons with "Common Mode Rejection" security. This section extends that model for ESP-NOW transport where authentication (not encryption) is desirable.

### 4.1 Key Derivation from BLE Bond

After BLE pairing, derive ESP-NOW authentication keys from the Long Term Key (LTK):

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

esp_err_t derive_espnow_keys(
    const uint8_t ltk[16],           // From BLE bond - THE secret
    const device_identity_t* local,
    const device_identity_t* peer,
    uint8_t totp_key[16],
    uint8_t nonce_base[8]
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
    uint8_t okm[24];
    mbedtls_hkdf(mbedtls_md_info_from_type(MBEDTLS_MD_SHA256),
                 (uint8_t*)"UTLP-v1", 7,  // Salt
                 ltk, 16,                   // IKM (secret)
                 info, 24,                  // Info (binding)
                 okm, 24);
    
    memcpy(totp_key, okm, 16);
    memcpy(nonce_base, okm + 16, 8);
    return ESP_OK;
}
```

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

1. **Minimum Delay Packet Selection** for wireless time sync filtering
2. **Two-state Kalman filter** (offset + drift) for embedded sync
3. **802.11mc FTM as Stratum 1a** time source in UTLP hierarchy
4. **FTM-Kalman fusion** with transport-specific noise weighting
5. **BLE/ESP-NOW time-division multiplexing** for single-radio coexistence
6. **Dual-MAC key derivation** with explicit entropy analysis (MACs bind, LTK secures)
7. **Time-synchronized TOTP** with 100ms windows (300× tighter than standard)
8. **Authenticated broadcast beacons** (authentication without confidentiality)

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
