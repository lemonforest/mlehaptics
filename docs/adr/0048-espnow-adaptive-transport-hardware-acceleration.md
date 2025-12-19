# ADR 0048: ESP-NOW Adaptive Transport and Hardware Acceleration

**Status:** Accepted
**Date:** 2025-12-17 (updated 2025-12-19)
**Authors:** Claude Code (Opus 4.5)
**Supersedes:** Portions of AD041 (BLE-only time sync)

## Context

Phase 2 time synchronization over BLE achieved ±30μs drift over 90 minutes through mathematical convergence (EMA filtering, drift rate estimation). However, this required extended convergence time and the raw BLE jitter (~50-70ms) created perceptible phase errors during pattern playback (wig-wag effects) before the filter converged.

**Human testing revealed that >50ms phase variance is perceptually detectable.** BLE's connection-event-based scheduling cannot guarantee sub-50ms jitter for individual messages, even though the statistical average converges well.

ESP-NOW offers:
- Sub-millisecond latency (~100-500μs typical)
- ±100μs jitter (vs BLE's ±50ms)
- Connectionless broadcast capability
- WiFi/BLE coexistence on ESP32-C6
- 200+ meter range (vs ~100m for BLE)
- Future FTM support path (sub-nanosecond)

## Decision

### Dual-Transport Architecture

Implement a **dual-transport architecture** where each transport serves its optimal purpose:

| Transport | Purpose | Latency Target | Power |
|-----------|---------|----------------|-------|
| **ESP-NOW** | Time sync beacons, coordination messages | <1ms | Higher (WiFi) |
| **BLE** | PWA connectivity, human-initiated commands | ~50ms OK | Lower |

### Message Classification

Three distinct message types with different behaviors:

#### 1. Time Sync Beacons (ESP-NOW Broadcast)
- **Trigger:** Adaptive schedule (1 min → 20 min based on quality)
- **Pattern:** 3 broadcasts at 100ms intervals (burst)
- **Purpose:** Clock maintenance, drift correction
- **Latency:** Best-effort (scheduled)

#### 2. Coordination Messages (ESP-NOW Unicast)
- **Trigger:** User action (mode change, settings update, shutdown)
- **Pattern:** Single message, immediate
- **Purpose:** State synchronization
- **Latency:** <100ms required
- **Key insight:** Mode changes do NOT wait for scheduled beacons

#### 3. PWA Commands (BLE GATT)
- **Trigger:** Web app interaction
- **Pattern:** GATT characteristic writes
- **Purpose:** Human interface, configuration
- **Latency:** ~50-100ms acceptable (human perception)

### Adaptive Beacon Interval Algorithm

```c
// Time sync beacon intervals
#define BEACON_INTERVAL_MIN_MS      (60 * 1000)     // 1 minute
#define BEACON_INTERVAL_MAX_MS      (20 * 60 * 1000) // 20 minutes
#define QUALITY_THRESHOLD_HIGH      95   // %
#define QUALITY_THRESHOLD_LOW       80   // %
#define BURST_VARIANCE_THRESHOLD_US 1000 // 1ms

// Adaptive logic
if (quality >= QUALITY_THRESHOLD_HIGH for 3 consecutive beacons) {
    interval = min(interval * 2, BEACON_INTERVAL_MAX_MS);
}

if (quality < QUALITY_THRESHOLD_LOW) {
    interval = BEACON_INTERVAL_MIN_MS;  // Reset
}

if (burst_variance > BURST_VARIANCE_THRESHOLD_US) {
    interval = max(interval / 2, BEACON_INTERVAL_MIN_MS);
}
```

### Beacon Burst Pattern

Each scheduled sync is actually 3 broadcasts at 100ms intervals:

```
t=0ms:    Beacon (seq=N, burst_idx=0)
t=100ms:  Beacon (seq=N, burst_idx=1)
t=200ms:  Beacon (seq=N, burst_idx=2)
```

Benefits:
- Statistical confidence (3 samples vs 1)
- Measure inter-beacon timing variance
- Redundancy for packet loss
- Phase coherence confirms receipt ("dinner bell" model - we know it was heard by who shows up)

### BLE Bootstrap Model (Trust Establishment Only)

BLE peer connection is used ONLY for initial trust establishment, then released:

1. **Discovery Phase:** Both devices advertise, discover peer via Bilateral Service UUID
2. **Connection Phase:** One device connects to peer (battery-based role assignment)
3. **Key Exchange Phase:**
   - SERVER generates key exchange message (nonce + MAC)
   - SERVER sends `SYNC_MSG_ESPNOW_KEY_EXCHANGE` via BLE
   - Both devices derive shared LMK via HKDF-SHA256
   - Both devices configure ESP-NOW peer with derived key
4. **Release Phase:** Peer BLE connection terminated
5. **Operation Phase:** ALL peer communication via encrypted ESP-NOW

```
┌─────────────────────────────────────────────────────────────────┐
│                    BLE Bootstrap Sequence                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐         ┌─────────────┐         ┌────────────┐ │
│  │ BLE Discover│  ──→    │ Key Exchange│  ──→    │ BLE Release│ │
│  │ + Connect   │         │ via GATT    │         │ ESP-NOW Go │ │
│  └─────────────┘         └─────────────┘         └────────────┘ │
│        ~2s                    ~200ms                  ~50ms     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Post-Bootstrap Operation                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐                      ┌──────────────┐        │
│   │   ESP-NOW    │                      │     BLE      │        │
│   │  (Peer Ops)  │                      │  (PWA Only)  │        │
│   └──────┬───────┘                      └──────┬───────┘        │
│          │                                     │                │
│   Time Sync Beacons                     PWA Web Interface       │
│   Coordination Messages                 Human Commands          │
│   Mode Changes                          Mobile App Control      │
│   Shutdown Propagation                                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Key Insight:** BLE peer connection is NOT maintained between devices.
- Eliminates BLE connection overhead during operation
- ESP-NOW handles all timing-critical peer communication
- BLE only used for PWA (phone) interface
- Simpler architecture, fewer failure modes

**Coexistence:**
- BLE uses 2.4 GHz with frequency hopping (advertising channels 37, 38, 39)
- ESP-NOW uses WiFi channel (configurable, channel 1 default)
- ESP32-C6 handles coexistence automatically (`CONFIG_ESP_COEX_SW_COEXIST_ENABLE=y`)

### UTLP Transport HAL

Platform-agnostic transport abstraction for portability:

```c
// utlp_transport.h - Universal interface
typedef struct {
    utlp_err_t (*init)(void);
    utlp_err_t (*send)(const utlp_frame_t *frame);
    utlp_err_t (*set_peer_encrypted)(const uint8_t mac[6], const uint8_t key[16]);
    // ... other operations
} utlp_transport_ops_t;

// Usage: UTLP logic never touches vendor APIs
utlp_transport->send(&beacon_frame);
```

**Implementations:**
- `utlp_transport_espnow.c` - Current (ESP32 ESP-NOW)
- `utlp_transport_shockburst.c` - Future (Nordic Enhanced ShockBurst)
- `utlp_transport_802154.c` - Future (IEEE 802.15.4 / Thread)

### Part 2: Hardware Accelerator Opportunities

**Current Software Implementations:**

| Location | Algorithm | Implementation | Accelerator Available |
|----------|-----------|----------------|----------------------|
| `time_sync.c:830` | CRC-16 CCITT | Custom software | No direct HW |
| `pattern_playback.c:438` | CRC-32 | `esp_crc32_le()` | ROM table lookup |
| `ble_manager.c:553` | CRC-32 | `esp_crc32_le()` | ROM table lookup |
| RFIP Protocol Hardening | TOTP (SHA-based) | Not implemented | **SHA accelerator** |
| BLE | AES-CCM | NimBLE internal | **AES accelerator** |

**ESP32-C6 Hardware Accelerators:**

| Accelerator | Use Cases | ESP-IDF API |
|-------------|-----------|-------------|
| **AES** | TOTP, message encryption, pattern data encryption | `esp_aes.h` |
| **SHA-256** | Message authentication, HMAC-based TOTP | `esp_sha.h`, `mbedtls/sha256.h` |
| **ECC/RSA** | Device attestation, signed firmware | `esp_ds.h` (Digital Signature) |
| **HMAC** | Secure key derivation, TOTP | `esp_hmac.h` |
| **RNG** | Nonce generation, entropy | `esp_random.h` (already used) |

**Recommended Upgrades:**

1. **CRC-16 → HMAC-SHA256 truncated (for beacons)**
   - Current: 16-bit CRC provides error detection only
   - Proposed: 32-bit HMAC-SHA256 provides authentication + integrity
   - Hardware: ESP32-C6 SHA accelerator
   - Benefit: Prevents beacon spoofing (RFIP Protocol Hardening requirement)

2. **TOTP Beacon Integrity (from UTLP RFIP Section 10.1)**
   ```c
   // Hardware-accelerated TOTP generation
   #include "mbedtls/sha256.h"

   uint32_t generate_totp_hmac(uint64_t epoch_us, const uint8_t *secret, size_t secret_len) {
       // Uses hardware SHA-256 accelerator automatically via mbedTLS
       uint8_t hmac[32];
       mbedtls_md_context_t ctx;
       mbedtls_md_init(&ctx);
       mbedtls_md_setup(&ctx, mbedtls_md_info_from_type(MBEDTLS_MD_SHA256), 1);
       mbedtls_md_hmac_starts(&ctx, secret, secret_len);
       mbedtls_md_hmac_update(&ctx, (uint8_t *)&epoch_us, sizeof(epoch_us));
       mbedtls_md_hmac_finish(&ctx, hmac);
       mbedtls_md_free(&ctx);

       // Truncate to 32-bit TOTP
       return (hmac[0] << 24) | (hmac[1] << 16) | (hmac[2] << 8) | hmac[3];
   }
   ```

3. **Pattern Data Encryption (future PWA pattern transfer)**
   - Use AES-128-GCM for authenticated encryption
   - Hardware: ESP32-C6 AES accelerator
   - Benefit: Protect custom pattern data from interception

**Performance Comparison:**

| Operation | Software (cycles) | Hardware (cycles) | Speedup |
|-----------|-------------------|-------------------|---------|
| SHA-256 (64B) | ~4000 | ~100 | 40x |
| AES-128-GCM (256B) | ~3000 | ~150 | 20x |
| CRC-32 (64B) | ~200 | ~200 | 1x (ROM table) |

Note: CRC-32 is already fast via ROM lookup table; hardware acceleration most beneficial for SHA/AES operations.

## Implementation Status

### ✅ Phase 1: ESP-NOW Transport (COMPLETE)

| File | Status | Description |
|------|--------|-------------|
| `src/espnow_transport.h` | ✅ Done | API definitions, types, jitter metrics |
| `src/espnow_transport.c` | ✅ Done | WiFi init, peer management, callbacks |
| `src/time_sync_task.h` | ✅ Done | Transport field in beacon message |
| `src/time_sync_task.c` | ✅ Done | Deduplication logic, disconnect reset |
| `src/ble_manager.c` | ✅ Done | Transport parameter for beacon calls |
| `src/CMakeLists.txt` | ✅ Done | ESP-NOW source and WiFi deps |
| `sdkconfig.xiao_esp32c6*` | ✅ Done | WiFi + coexistence enabled |

### 🚧 Phase 2: Adaptive Intervals & Burst Pattern (TODO)

1. [ ] Implement beacon burst (3x at 100ms)
2. [ ] Add adaptive interval algorithm (1-20 min)
3. [ ] Quality-based interval scaling
4. [ ] Burst variance measurement

### 🚧 Phase 3: Coordination Messages (TODO)

1. [ ] Create `transport_coordinator.c/.h`
2. [ ] Immediate ESP-NOW for mode changes
3. [ ] Settings sync on ESP-NOW
4. [ ] Shutdown propagation

### 🚧 Phase 4: BLE Fallback & Recovery (TODO)

1. [ ] BLE reconnect backoff (30s, 30s, 30s, 60s)
2. [ ] RSSI-triggered reconnection
3. [ ] Seamless handoff between transports

### 📋 Phase 5: Hardware Crypto Integration (Future)

1. Replace CRC-16 with HMAC-SHA256-32 in beacons
2. Implement TOTP beacon integrity (RFIP requirement)
3. Add pattern encryption for BLE transfer

### 📋 Phase 6: 802.11mc FTM Integration (Future)

1. Check silicon revision (v0.2+ required for initiator)
2. Implement FTM ranging alongside ESP-NOW
3. Extract raw T1-T4 timestamps for sub-microsecond sync

## Silicon Revision Check

Added to `main.c` startup logging:

```c
// 802.11mc FTM capability check (ESP32-C6 specific)
if (chip_info.model == CHIP_ESP32C6) {
    bool ftm_initiator_ok = (rev_major > 0) || (rev_major == 0 && rev_minor >= 2);
    if (ftm_initiator_ok) {
        ESP_LOGI(TAG, "802.11mc FTM: Initiator + Responder (full support)");
    } else {
        ESP_LOGW(TAG, "802.11mc FTM: Responder ONLY (v0.2+ needed for Initiator)");
    }
}
```

## Consequences

### Positive

- **Immediate phase coherence** (<1ms) without convergence delay
- **Pattern playback** within 50ms perceptual threshold (wig-wag works)
- **Mode changes propagate immediately** (not waiting for scheduled beacons)
- **Graceful BLE disconnect** - devices continue coordinating via ESP-NOW
- **Better range** (200m+ vs ~100m for BLE)
- **Future FTM path** for sub-nanosecond precision
- **Maintains PWA compatibility** - BLE always available for phone

### Negative

- **Higher power** during active WiFi (addressed by adaptive intervals)
- **More complex** transport layer
- **Two radios** to coordinate

### Neutral

- ESP-NOW and BLE coexist automatically (`CONFIG_ESP_COEX_SW_COEXIST_ENABLE=y`)
- BLE math (EMA filtering, drift estimation) still valid as fallback
- Phase 2 work preserved (provides graceful degradation)

### Power Budget Analysis

| Mode | WiFi Radio | BLE Radio | Duty Cycle | Notes |
|------|------------|-----------|------------|-------|
| Synced Idle | Sleep | Connected | 0% WiFi | Minimal power |
| Beacon Burst | Active 300ms | Connected | ~0.025% @ 20min | 3 broadcasts |
| Mode Change | Active ~50ms | Connected | On-demand | User action |
| BLE Fallback | Active | Off | Variable | Temporary |

At 20-minute beacon intervals: WiFi active 300ms per 1200s = 0.025% duty cycle.
Estimated impact: +2-5% battery consumption vs BLE-only.

## References

- [ESP-NOW Programming Guide](https://docs.espressif.com/projects/esp-idf/en/latest/esp32c6/api-reference/network/esp_now.html)
- [802.11mc FTM Reconnaissance Report](../802.11mc_FTM_Reconnaissance_Report.md)
- [ESP32-C6 Technical Reference Manual - Crypto Accelerators](https://www.espressif.com/sites/default/files/documentation/esp32-c6_technical_reference_manual_en.pdf)
- [UTLP Specification](../UTLP_Specification.md)
- [AD039: Time Synchronization Protocol](0039-time-synchronization-protocol.md)
- [AD041: Predictive Bilateral Synchronization](0041-predictive-bilateral-synchronization.md)

## Resolved Questions

1. ✅ **ESP-NOW channel:** Fixed at channel 1 (ESPNOW_CHANNEL constant)
2. ✅ **BLE fallback model:** ESP-NOW primary for timing, BLE for PWA only
3. ✅ **Broadcast vs unicast:** Broadcast for time sync (fire-and-forget), unicast for coordination
4. ✅ **Mode change latency:** Immediate ESP-NOW, NOT piggybacked on scheduled beacons

## Open Questions

1. Should beacon burst use same sequence number for all 3, or increment?
2. What variance threshold (in the burst) indicates poor link quality?
3. Should RSSI improvements trigger immediate BLE reconnection or wait for pattern?
