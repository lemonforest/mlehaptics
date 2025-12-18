# ESP-NOW vs BLE Power Analysis for UTLP

**ESP32-C6 Transport Selection**

*mlehaptics Project — December 2025*

---

## 1. The Question

Should UTLP use BLE or ESP-NOW for time synchronization beacons?

**Hybrid proposal:** BLE for bonding/pairing (security), ESP-NOW for data (speed).

---

## 2. ESP32-C6 Power Specifications

### 2.1 Radio Power Draw

| Mode | Current | Notes |
|------|---------|-------|
| **WiFi TX** (802.11n HT20 MCS7) | ~130-150 mA | ESP-NOW uses this |
| **WiFi TX** (802.11b 1Mbps) | ~170-180 mA | Long-range mode |
| **WiFi RX** | ~95-100 mA | Listening |
| **BLE TX** (0 dBm) | ~17-20 mA | Standard power |
| **BLE RX** | ~17-20 mA | Scanning/connected |
| **Light Sleep** (WiFi connected) | ~800 μA | WiFi modem sleep |
| **Light Sleep** (BLE connected) | ~30 μA | BLE maintains conn |
| **Deep Sleep** | ~7 μA | RTC only |

### 2.2 Timing Characteristics

| Operation | Duration | Notes |
|-----------|----------|-------|
| **ESP-NOW packet** | ~250-400 μs | Fixed, deterministic |
| **BLE connection event** | ~2-3 ms | Minimum practical |
| **BLE connection interval** | 7.5-4000 ms | Negotiated |
| **WiFi wake from light sleep** | ~1-3 ms | To active TX |
| **BLE wake from light sleep** | ~2-5 ms | To connection event |

---

## 3. Energy Per Beacon Analysis

### 3.1 ESP-NOW Beacon

```
Scenario: 27-byte UTLP beacon via ESP-NOW

Transmission:
- Packet overhead: ~50 bytes (MAC header, FCS)
- Total frame: ~77 bytes at 24 Mbps (HT20 MCS0)
- Airtime: ~300 μs (including preamble, SIFS)
- TX current: 145 mA

Energy per TX:
  E = I × t = 145 mA × 0.3 ms = 43.5 μJ

Wake overhead (from light sleep):
- Wake time: ~2 ms at ~50 mA average = 100 μJ

Total per beacon (with wake): ~144 μJ
Total per beacon (already awake): ~44 μJ
```

### 3.2 BLE GATT Notification

```
Scenario: 27-byte UTLP beacon via BLE notification

Connection event:
- Data packet + ACK
- Minimum event duration: ~2 ms (625μs × 3-4 slots)
- TX/RX current: 18 mA average

Energy per notification:
  E = I × t = 18 mA × 2 ms = 36 μJ

Connection maintenance:
- Empty events to maintain connection
- At 100ms interval: 10 events/sec
- Overhead: 36 μJ × 9 = 324 μJ/sec (no-data events)

Total per second (100ms interval): ~360 μJ
Total per second (1000ms interval): ~72 μJ
```

### 3.3 BLE Advertising (Connectionless)

```
Scenario: 27-byte beacon in BLE advertising PDU

Advertising:
- 3 channels (37, 38, 39)
- ~1 ms per channel = 3 ms total
- TX current: 18 mA

Energy per advertisement:
  E = I × t = 18 mA × 3 ms = 54 μJ

At 1 Hz beacon rate: 54 μJ/sec
At 10 Hz beacon rate: 540 μJ/sec
```

---

## 4. Comparison Summary

### 4.1 Energy Budget (1 beacon/second, from sleep)

| Transport | Energy/sec | Battery Life (500mAh) |
|-----------|------------|----------------------|
| ESP-NOW (sleep between) | ~144 μJ | ~3,470 hours |
| BLE Notification (100ms CI) | ~360 μJ | ~1,390 hours |
| BLE Notification (1000ms CI) | ~72 μJ | ~6,940 hours |
| BLE Advertising | ~54 μJ | ~9,260 hours |

*Assumes ideal conditions, no other system power*

### 4.2 Energy Budget (10 beacons/second)

| Transport | Energy/sec | Battery Life (500mAh) |
|-----------|------------|----------------------|
| ESP-NOW (stay awake) | ~440 μJ | ~1,136 hours |
| ESP-NOW (sleep between) | ~1,440 μJ | ~347 hours |
| BLE Notification (15ms CI) | ~2,400 μJ | ~208 hours |
| BLE Advertising | ~540 μJ | ~926 hours |

**Key insight:** At higher beacon rates, ESP-NOW becomes competitive because BLE connection interval overhead dominates.

---

## 5. Latency Analysis (Critical for UTLP)

### 5.1 Worst-Case Latency

| Transport | Worst Case | Jitter |
|-----------|------------|--------|
| **ESP-NOW** | <1 ms | ~100 μs |
| **BLE Connected** (100ms CI) | 100 ms | ±50 ms |
| **BLE Connected** (15ms CI) | 15 ms | ±7.5 ms |
| **BLE Advertising** | Adv interval | ±10 ms |

### 5.2 Impact on Time Sync

```
UTLP offset calculation:
  offset = ((T2 - T1) + (T3 - T4)) / 2

Jitter in T1/T2/T3/T4 directly impacts offset accuracy.

ESP-NOW: ±100 μs jitter → ±100 μs offset uncertainty
BLE (100ms CI): ±50 ms jitter → ±50 ms offset uncertainty (!!!)

For ±30 μs sync target:
- ESP-NOW: Achievable
- BLE (long CI): Not achievable without tricks
```

**This is why your current BLE implementation probably uses short connection intervals or careful slot alignment.**

---

## 6. The Hybrid Architecture

### 6.1 Proposal

```
┌─────────────────────────────────────────────────────────────────┐
│                   Hybrid Transport Stack                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phase 1: Discovery & Bonding (BLE)                            │
│  ┌──────────┐         ┌──────────┐                             │
│  │ Device A │◄─BLE───►│ Device B │                             │
│  └──────────┘  Adv/   └──────────┘                             │
│               Scan/                                             │
│               Bond                                              │
│                                                                 │
│  Result: Shared encryption key (LTK from BLE bonding)          │
│                                                                 │
│  Phase 2: Data Exchange (ESP-NOW)                              │
│  ┌──────────┐         ┌──────────┐                             │
│  │ Device A │◄─ESP────►│ Device B │                             │
│  └──────────┘  NOW    └──────────┘                             │
│               (encrypted with BLE-derived key)                  │
│                                                                 │
│  - Sub-ms latency                                              │
│  - Deterministic timing                                         │
│  - Broadcast capable                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Security Model

ESP-NOW doesn't have built-in encryption, but you can use the BLE bond:

```c
// During BLE bonding, extract the Long Term Key (LTK)
// This is the key BLE uses for encrypted reconnections

typedef struct {
    uint8_t ltk[16];       // From BLE bonding
    uint8_t peer_mac[6];   // ESP-NOW peer address
    bool    trusted;       // Bond complete
} peer_credential_t;

// Derive ESP-NOW encryption key from BLE LTK
void derive_espnow_key(const peer_credential_t* cred, uint8_t* espnow_key) {
    // HKDF or simple derivation
    // espnow_key = HMAC-SHA256(LTK, "ESPNOW" || peer_mac)
    
    mbedtls_md_context_t ctx;
    mbedtls_md_init(&ctx);
    mbedtls_md_setup(&ctx, mbedtls_md_info_from_type(MBEDTLS_MD_SHA256), 1);
    mbedtls_md_hmac_starts(&ctx, cred->ltk, 16);
    mbedtls_md_hmac_update(&ctx, (uint8_t*)"ESPNOW", 6);
    mbedtls_md_hmac_update(&ctx, cred->peer_mac, 6);
    mbedtls_md_hmac_finish(&ctx, espnow_key);  // 32 bytes, use first 16
    mbedtls_md_free(&ctx);
}

// ESP-NOW has built-in CCMP encryption if you set a PMK
esp_now_set_pmk(espnow_key);  // Primary Master Key
esp_now_peer_info_t peer = {
    .encrypt = true,
    .lmk = {derived_local_key},  // Per-peer key
};
esp_now_add_peer(&peer);
```

### 6.3 Transport Switching Logic

```c
typedef enum {
    TRANSPORT_BLE_ONLY,
    TRANSPORT_ESPNOW_ONLY,
    TRANSPORT_HYBRID,
} transport_mode_t;

typedef struct {
    transport_mode_t mode;
    bool ble_bonded;
    bool espnow_ready;
    
    // BLE handles
    uint16_t ble_conn_handle;
    
    // ESP-NOW handles  
    uint8_t espnow_peer_mac[6];
    uint8_t espnow_key[16];
} transport_state_t;

esp_err_t transport_send_beacon(const utlp_beacon_t* beacon) {
    switch (transport.mode) {
        case TRANSPORT_BLE_ONLY:
            return ble_send_notification(beacon);
            
        case TRANSPORT_ESPNOW_ONLY:
        case TRANSPORT_HYBRID:
            if (transport.espnow_ready) {
                return espnow_send_encrypted(beacon);
            }
            // Fallback to BLE if ESP-NOW not ready
            return ble_send_notification(beacon);
    }
}

// State machine for hybrid mode
void transport_update(void) {
    if (transport.mode == TRANSPORT_HYBRID) {
        if (transport.ble_bonded && !transport.espnow_ready) {
            // Bonding complete, set up ESP-NOW
            derive_espnow_key(&credentials, transport.espnow_key);
            espnow_init_peer(transport.espnow_peer_mac, transport.espnow_key);
            transport.espnow_ready = true;
            
            // Optionally disconnect BLE to save power
            // Or keep it for PWA communication
        }
    }
}
```

---

## 7. ESP-NOW Implementation Details

### 7.1 Basic Setup

```c
#include "esp_now.h"
#include "esp_wifi.h"

// ESP-NOW requires WiFi to be initialized (but not connected)
esp_err_t espnow_transport_init(void) {
    // Initialize WiFi in station mode (required for ESP-NOW)
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_start());
    
    // Set channel to match BLE advertising channels' WiFi overlap
    // Channel 1 (2412 MHz) is near BLE ch 37 (2402 MHz)
    ESP_ERROR_CHECK(esp_wifi_set_channel(1, WIFI_SECOND_CHAN_NONE));
    
    // Initialize ESP-NOW
    ESP_ERROR_CHECK(esp_now_init());
    ESP_ERROR_CHECK(esp_now_register_recv_cb(espnow_recv_callback));
    ESP_ERROR_CHECK(esp_now_register_send_cb(espnow_send_callback));
    
    return ESP_OK;
}

// Receive callback - runs in WiFi task context
static void espnow_recv_callback(const esp_now_recv_info_t* info,
                                  const uint8_t* data, int len) {
    int64_t rx_time = esp_timer_get_time();  // Timestamp immediately
    
    // Validate sender is bonded peer
    if (memcmp(info->src_addr, trusted_peer_mac, 6) != 0) {
        return;  // Ignore unknown senders
    }
    
    // Process UTLP beacon
    if (len >= sizeof(utlp_beacon_t)) {
        utlp_beacon_t* beacon = (utlp_beacon_t*)data;
        time_sync_process_beacon(beacon, rx_time);
    }
}
```

### 7.2 Timestamping for UTLP

```c
// ESP-NOW provides TX callback after transmission completes
// We can bracket the TX to get approximate timestamp

static volatile int64_t last_tx_time = 0;
static volatile bool tx_pending = false;

static void espnow_send_callback(const uint8_t* mac, esp_now_send_status_t status) {
    last_tx_time = esp_timer_get_time();
    tx_pending = false;
}

esp_err_t espnow_send_beacon_timed(const utlp_beacon_t* beacon, int64_t* tx_time) {
    tx_pending = true;
    
    // Capture time just before send
    int64_t t_before = esp_timer_get_time();
    
    esp_err_t ret = esp_now_send(peer_mac, (uint8_t*)beacon, sizeof(*beacon));
    if (ret != ESP_OK) {
        tx_pending = false;
        return ret;
    }
    
    // Wait for TX complete callback (should be <1ms)
    int timeout = 10;  // 10ms max
    while (tx_pending && timeout-- > 0) {
        vTaskDelay(pdMS_TO_TICKS(1));
    }
    
    // TX time is approximately midpoint
    *tx_time = (t_before + last_tx_time) / 2;
    
    return ESP_OK;
}
```

### 7.3 Power Management

```c
// ESP-NOW with aggressive power saving

void espnow_enter_power_save(void) {
    // Enable WiFi modem sleep between transmissions
    esp_wifi_set_ps(WIFI_PS_MAX_MODEM);
}

void espnow_prepare_tx(void) {
    // Wake modem before transmission
    esp_wifi_set_ps(WIFI_PS_NONE);
    vTaskDelay(pdMS_TO_TICKS(2));  // Allow modem wake
}

// For maximum power saving, can stop WiFi entirely between bursts
void espnow_deep_sleep_between_sync(void) {
    esp_wifi_stop();  // Radio off completely
    
    // ... sleep ...
    
    esp_wifi_start();  // Radio back on
    // Note: ESP-NOW peer info is retained
}
```

---

## 8. Coexistence: BLE + ESP-NOW

### 8.1 Radio Sharing

ESP32-C6 has a single 2.4 GHz radio. BLE and WiFi share it via coexistence arbitration.

```c
// Enable coexistence
esp_coex_preference_set(ESP_COEX_PREFER_BALANCE);

// Options:
// ESP_COEX_PREFER_WIFI    - WiFi gets priority (better for ESP-NOW)
// ESP_COEX_PREFER_BT      - BLE gets priority
// ESP_COEX_PREFER_BALANCE - Time-division sharing
```

### 8.2 Practical Coexistence Strategy

```
Scenario: PWA connected via BLE, devices syncing via ESP-NOW

┌─────────────────────────────────────────────────────────────────┐
│                    Time Division Strategy                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  BLE Connection Interval: 100ms                                 │
│                                                                 │
│  ──┬────────────────────────────────────────────────────┬──    │
│    │                   100ms                            │       │
│  ──┴────────────────────────────────────────────────────┴──    │
│    ▲                                                    ▲       │
│    │                                                    │       │
│  BLE event                                          BLE event  │
│  (~3ms)                                              (~3ms)    │
│                                                                 │
│           ESP-NOW sync beacons fire between BLE events         │
│                                                                 │
│      ┌─┐       ┌─┐       ┌─┐       ┌─┐       ┌─┐              │
│      │ │       │ │       │ │       │ │       │ │              │
│  ────┴─┴───────┴─┴───────┴─┴───────┴─┴───────┴─┴────          │
│       ▲         ▲         ▲         ▲         ▲                │
│    ESP-NOW   ESP-NOW   ESP-NOW   ESP-NOW   ESP-NOW            │
│    (~0.3ms)  (~0.3ms)  (~0.3ms)  (~0.3ms)  (~0.3ms)           │
│                                                                 │
│  97ms available for ESP-NOW between 3ms BLE events             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.3 Conflict Avoidance

```c
// Check if BLE event is imminent before ESP-NOW TX
bool is_ble_event_soon(void) {
    // If we know the connection interval and anchor point,
    // we can predict when the next BLE event will occur
    int64_t now = esp_timer_get_time();
    int64_t next_ble_event = ble_anchor_point + 
        ((now - ble_anchor_point) / ble_conn_interval + 1) * ble_conn_interval;
    
    int64_t time_to_event = next_ble_event - now;
    
    // Don't TX if BLE event is within 5ms
    return (time_to_event < 5000);
}

esp_err_t espnow_send_if_clear(const utlp_beacon_t* beacon) {
    if (ble_connected && is_ble_event_soon()) {
        // Defer transmission
        return ESP_ERR_TIMEOUT;
    }
    return espnow_send_beacon_timed(beacon, &tx_time);
}
```

---

## 9. Recommendation

### 9.1 For UTLP Bilateral Sync

**Use hybrid approach:**

| Function | Transport | Rationale |
|----------|-----------|-----------|
| Device discovery | BLE Advertising | Standard, phone-compatible |
| PWA connection | BLE GATT | Required for web interface |
| Bonding/security | BLE SMP | Established security model |
| Time sync beacons | **ESP-NOW** | Deterministic latency |
| Pattern transfer | BLE GATT | Larger MTU, reliable |
| FTM ranging | WiFi 802.11mc | Hardware timestamping |

### 9.2 Expected Improvements

| Metric | BLE Only | Hybrid | Improvement |
|--------|----------|--------|-------------|
| Sync latency jitter | ±10-50 ms | ±100 μs | 100-500x |
| Achievable offset | ±30 μs (best case) | ±10 μs | 3x |
| Beacon rate limit | ~30 Hz | ~100+ Hz | 3x+ |
| Multi-device broadcast | Not native | Native | Architecture win |

### 9.3 Implementation Priority

1. **Phase 1:** Add ESP-NOW transport alongside BLE (A/B testing)
2. **Phase 2:** Implement BLE→ESP-NOW key derivation
3. **Phase 3:** Add coexistence timing coordination
4. **Phase 4:** Default to ESP-NOW for sync, BLE for control

---

## 10. Gotchas

### 10.1 Channel Selection

ESP-NOW requires both devices on same WiFi channel. BLE doesn't care.

```c
// Both devices must agree on channel
#define ESPNOW_CHANNEL 1  // Configure in both devices

// Or: exchange channel via BLE during bonding
```

### 10.2 MAC Address

ESP-NOW uses WiFi MAC, BLE uses BLE MAC. They're different!

```c
uint8_t wifi_mac[6], ble_mac[6];
esp_read_mac(wifi_mac, ESP_MAC_WIFI_STA);
esp_read_mac(ble_mac, ESP_MAC_BT);

// During BLE bonding, exchange WiFi MACs for ESP-NOW peer setup
```

### 10.3 Wake Latency

WiFi modem takes ~2ms to wake from power save. Budget this into timing.

```c
// If sync beacon needed immediately, keep modem awake
// If beacon can wait 2ms, use modem sleep for power saving
```

---

## References

- ESP-IDF ESP-NOW Guide: https://docs.espressif.com/projects/esp-idf/en/latest/esp32c6/api-reference/network/esp_now.html
- ESP32-C6 Datasheet (power specifications): https://www.espressif.com/sites/default/files/documentation/esp32-c6_datasheet_en.pdf
- BLE/WiFi Coexistence: https://docs.espressif.com/projects/esp-idf/en/latest/esp32c6/api-guides/coexist.html

---

*Analysis prepared for mlehaptics UTLP transport selection.*
