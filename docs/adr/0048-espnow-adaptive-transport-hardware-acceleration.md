# ADR 0048: ESP-NOW Adaptive Transport and Hardware Acceleration

**Status:** Research
**Date:** 2025-12-17
**Authors:** Claude Code (Opus 4.5)

## Context

Currently, EMDR Pulser devices communicate peer-to-peer exclusively via BLE. While BLE is excellent for:
- Phone compatibility ("When someone asks bluetooth or BLE, they usually want to know if they can use their phone")
- Low power consumption
- Established pairing/bonding security

There are scenarios where BLE range or reliability is insufficient. ESP-NOW offers:
- 200+ meter range (vs ~100m for BLE)
- Lower latency (~1ms vs ~7-15ms for BLE)
- No connection overhead (broadcast-based)
- Coexistence with 802.11mc FTM for ranging

Additionally, the ESP32-C6 has hardware cryptographic accelerators (AES, SHA, ECC) that are currently underutilized for CRC and message authentication.

## Decision

### Part 1: ESP-NOW as Adaptive BLE Fallback

**Goal:** Use ESP-NOW when BLE quality degrades (RSSI < threshold, packet loss > threshold), while maintaining BLE for phone connectivity.

**Proposed Architecture:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    Transport Abstraction Layer                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────┐      ┌──────────┐      ┌──────────┐              │
│   │   BLE    │      │ ESP-NOW  │      │ 802.11mc │              │
│   │ (Primary)│      │(Fallback)│      │  (FTM)   │              │
│   └────┬─────┘      └────┬─────┘      └────┬─────┘              │
│        │                 │                 │                     │
│        ▼                 ▼                 ▼                     │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              sync_transport_t Interface                  │   │
│   │  - send_beacon(beacon)                                   │   │
│   │  - receive_beacon(beacon, timeout)                       │   │
│   │  - get_tx_timestamp()                                    │   │
│   │  - get_rx_timestamp()                                    │   │
│   │  - get_link_quality() → RSSI, packet_loss, latency       │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Adaptive Switching Logic:**

```c
// Proposed thresholds
#define BLE_RSSI_FALLBACK_THRESHOLD    -85  // dBm - switch to ESP-NOW
#define BLE_RSSI_RECOVER_THRESHOLD     -75  // dBm - switch back to BLE
#define BLE_PACKET_LOSS_THRESHOLD      10   // % - switch to ESP-NOW
#define ESPNOW_CHANNEL_SCAN_INTERVAL   5000 // ms - find peer channel

typedef enum {
    TRANSPORT_BLE_PRIMARY,      // Normal operation
    TRANSPORT_ESPNOW_FALLBACK,  // BLE degraded, using ESP-NOW
    TRANSPORT_HYBRID,           // Both active (future: multipath)
} transport_mode_t;
```

**Phone Compatibility Preservation:**

| Mode | BLE Advertising | ESP-NOW | Phone Can Connect |
|------|-----------------|---------|-------------------|
| `BLE_PRIMARY` | Yes | No | Yes |
| `ESPNOW_FALLBACK` | Yes (reduced rate) | Yes | Yes (but may be slower) |
| `HYBRID` | Yes | Yes | Yes |

Key insight: ESP-NOW and BLE advertising can coexist because:
- BLE uses 2.4 GHz with frequency hopping (37, 38, 39 advertising channels)
- ESP-NOW uses WiFi channel (1-14)
- ESP32-C6 can switch between them rapidly

**ESP-NOW + 802.11mc Coexistence:**

Both use the WiFi radio but for different purposes:
- ESP-NOW: Data transfer (connectionless, broadcast/unicast)
- 802.11mc FTM: Ranging (Action Frame exchange)

Interleaving strategy:
1. ESP-NOW for time sync beacons (low latency)
2. 802.11mc FTM on-demand for position updates (higher accuracy time but more overhead)

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

## Implementation Plan

### Phase 1: Transport Abstraction (This Sprint)

1. Create `sync_transport.h` interface
2. Implement BLE transport (refactor from current `time_sync.c`)
3. Add link quality monitoring to BLE transport

### Phase 2: ESP-NOW Transport

1. Implement `espnow_transport.c`
2. Add peer discovery via MAC address exchange (from BLE pairing)
3. Implement adaptive switching logic
4. Test ESP-NOW + BLE advertising coexistence

### Phase 3: Hardware Crypto Integration

1. Replace CRC-16 with HMAC-SHA256-32 in beacons
2. Implement TOTP beacon integrity (RFIP requirement)
3. Add pattern encryption for BLE transfer

### Phase 4: 802.11mc FTM Integration

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

- Better range for peer communication in challenging RF environments
- Faster failover when BLE quality degrades
- Hardware acceleration improves security without CPU overhead
- Future-proofs for 802.11mc ranging integration
- Maintains phone compatibility (BLE advertising always available)

### Negative

- Increased code complexity (transport abstraction layer)
- WiFi radio power consumption higher than BLE
- Need to manage ESP-NOW channel selection
- SHA-256 beacons larger than CRC-16 (but still fits in BLE advertisement)

### Neutral

- ESP-NOW and BLE can coexist on ESP32-C6 (validated by Espressif)
- Hardware crypto is transparent via mbedTLS (no code changes for SHA)
- Silicon revision check is informational only (graceful degradation)

## References

- [ESP-NOW Programming Guide](https://docs.espressif.com/projects/esp-idf/en/latest/esp32c6/api-reference/network/esp_now.html)
- [802.11mc FTM Reconnaissance Report](../802.11mc_FTM_Reconnaissance_Report.md)
- [ESP32-C6 Technical Reference Manual - Crypto Accelerators](https://www.espressif.com/sites/default/files/documentation/esp32-c6_technical_reference_manual_en.pdf)
- [UTLP RFIP Addendum - Protocol Hardening](../UTLP_Addendum_Reference_Frame_Independent_Positioning.md)
- [AD039: Time Synchronization Protocol](0039-time-synchronization-protocol.md)

## Open Questions

1. Should ESP-NOW use the same channel as PWA's WiFi connection (if any)?
2. What's the optimal RSSI threshold for BLE → ESP-NOW fallback?
3. Should we implement bidirectional ESP-NOW or keep it broadcast-only like BLE beacons?
4. Is HMAC-SHA256 overkill for beacon integrity vs. simpler CMAC-AES?
