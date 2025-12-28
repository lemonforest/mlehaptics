# Secure SMP Pairing Example

High-security BLE SMP (Security Manager Protocol) pairing between ESP32-C6 devices using Numeric Comparison with MITM protection.

## Security Level

This example implements the **highest security level** available in BLE 4.2+:

| Feature | Setting | Why |
|---------|---------|-----|
| I/O Capability | `DISPLAY_YESNO` | Enables Numeric Comparison |
| MITM Protection | Enabled | Prevents relay attacks |
| LE Secure Connections | Required | ECDH P-256 key exchange |
| Bonding | Enabled | Stores LTK for reconnection |

## Why Not "Just Works"?

"Just Works" pairing (`BLE_HS_IO_NO_INPUT_OUTPUT`) provides **zero** protection against man-in-the-middle attacks. An attacker can intercept and modify all traffic between devices.

**Use Just Works only when:**
- Physical security is guaranteed (e.g., test bench)
- Data is not sensitive (e.g., debug logs only)
- Convenience outweighs security requirements

**Use Numeric Comparison (this example) when:**
- Data confidentiality matters
- Device authenticity must be verified
- The pairing channel could be observed/modified
- You're building a protocol (not just a demo)

## Pairing Flow

```
    Device A                              Device B
        |                                     |
        |-------- Advertise + Scan ---------> |
        | <------- Discover peer ------------ |
        |                                     |
        | (MAC tie-breaker: lower addr wins)  |
        |                                     |
        |-------- BLE Connection -----------> |
        | (Device A = MASTER, B = SLAVE)      |
        |                                     |
        |-------- MTU Exchange -------------> |
        | <-------- MTU Response ------------ |
        |                                     |
        |------ SMP Pairing Request --------> |
        | <---- SMP Pairing Response -------- |
        |                                     |
        | (ECDH P-256 Key Exchange)           |
        |                                     |
    +-------+                            +-------+
    |CODE:  |                            |CODE:  |
    |847291 |   User verifies match      |847291 |
    +-------+                            +-------+
        |                                     |
        |------ Numeric Confirm (Yes) ------> |
        | <----- Numeric Confirm (Yes) ------ |
        |                                     |
        | *** CONNECTION ENCRYPTED ***        |
        | *** LTK STORED FOR FUTURE ***       |
```

## Critical Implementation Details

### 1. Store Initialization (Bug #113 Root Cause)

```c
// MANDATORY - Without this, SMP returns BLE_HS_ENOTSUP (rc=8)
ble_store_config_init();
```

This single missing call was the root cause of Bug #113. The SMP subsystem needs store callbacks to persist security material.

### 2. MAC Address Tie-Breaker

When two identical devices discover each other, both may try to connect simultaneously:

```c
static bool address_is_lower(const uint8_t *peer) {
    for (int i = 5; i >= 0; i--) {
        if (own_addr_val[i] < peer[i]) return true;
        if (own_addr_val[i] > peer[i]) return false;
    }
    return false;
}

// In discovery handler:
if (address_is_lower(event->disc.addr.val)) {
    connect_to_peer();  // We initiate
} else {
    // Wait for peer to connect to us
}
```

### 3. Stabilization Delays

BLE operations need settling time:

```c
#define DELAY_DISC_TO_CONNECT_MS    100   // After scan cancel
#define DELAY_CONNECT_STABILIZE_MS  200   // Before MTU exchange
#define DELAY_PRE_SMP_MS            50    // Before SMP initiation
```

### 4. RAM-Only Storage

Set in `sdkconfig` to prevent "zombie bonds":

```ini
CONFIG_BT_NIMBLE_NVS_PERSIST=n
```

## Building

### ESP-IDF (PlatformIO)

```bash
# Build
pio run -e secure_smp_pairing

# Flash
pio run -e secure_smp_pairing -t upload

# Monitor
pio device monitor
```

### Arduino (PlatformIO)

```ini
; platformio.ini for Arduino framework
[env:esp32c6_arduino]
platform = espressif32
board = seeed_xiao_esp32c6
framework = arduino
lib_deps = h2zero/NimBLE-Arduino@^1.4.0
```

## Expected Output

### Success

```
PEER DISCOVERED!
  Addr: 10:51:db:1c:b3:0a
  TIE-BREAKER: We are LOWER -> Initiating connection

CONNECTION ESTABLISHED!
  Role: MASTER (we initiated)

NUMERIC COMPARISON REQUIRED
  CODE: 847291
  Verify this matches the code on peer device
  [TEST MODE] Auto-confirmed numeric comparison

BLE_GAP_EVENT_ENC_CHANGE
  *** SMP PAIRING SUCCESS! ***
  Connection is now ENCRYPTED
  MITM protection: ACTIVE
  LTK available for ESP-NOW encryption!
```

### Failure Modes

| Error | Cause | Fix |
|-------|-------|-----|
| `rc=8` (ENOTSUP) | Missing `ble_store_config_init()` | Add the call |
| `rc=6` (ACL_EXISTS) | Both devices connecting | MAC tie-breaker |
| `status=13` (timeout) | Procedures racing | Add stabilization delays |
| No PASSKEY_ACTION | Wrong `sm_io_cap` | Use `DISPLAY_YESNO` |

## Production Considerations

### Replace Auto-Confirm

The example auto-confirms numeric comparison for testing convenience:

```c
pkey.numcmp_accept = 1;  // Auto-accept for testing
```

In production, wait for user input:

```c
// Read button state or other input
if (user_confirmed_match()) {
    pkey.numcmp_accept = 1;
} else {
    pkey.numcmp_accept = 0;  // Reject pairing
}
```

### Display the Code

The 6-digit code should be displayed on a screen, LED matrix, or spoken via audio:

```c
case BLE_SM_IOACT_NUMCMP:
    uint32_t code = event->passkey.params.numcmp;
    display_pairing_code(code);  // Your display function
    break;
```

### Enable NVS Persistence

For production, enable NVS to persist bonds across reboots:

```ini
CONFIG_BT_NIMBLE_NVS_PERSIST=y
```

## Arduino Porting Guide

The ESP-IDF code can be adapted for Arduino using the **NimBLE-Arduino** library by h2zero.

### Key Differences

| Aspect | ESP-IDF | Arduino |
|--------|---------|---------|
| Library | Built-in NimBLE | `h2zero/NimBLE-Arduino` |
| Init | `nimble_port_init()` + `ble_store_config_init()` | `NimBLEDevice::init()` (handles both) |
| Security | `ble_hs_cfg.sm_*` flags | `NimBLEDevice::setSecurityAuth()` |
| Callbacks | C function pointers | C++ class inheritance |
| Main loop | `while(1) + vTaskDelay()` | Arduino `loop()` |

### Arduino Security Configuration

```cpp
#include <NimBLEDevice.h>

// High-security: Numeric Comparison + MITM + Bonding
NimBLEDevice::setSecurityIOCap(BLE_HS_IO_DISPLAY_YESNO);
NimBLEDevice::setSecurityAuth(
    BLE_SM_PAIR_AUTHREQ_BOND |    // Enable bonding
    BLE_SM_PAIR_AUTHREQ_MITM |    // Require MITM protection
    BLE_SM_PAIR_AUTHREQ_SC        // LE Secure Connections
);
```

### Arduino Security Callbacks

```cpp
class SecureCallbacks : public NimBLESecurityCallbacks {
    bool onConfirmPIN(uint32_t pin) override {
        Serial.printf("Confirm pairing code: %06d\n", pin);
        // In production: wait for user button press
        return true;  // Auto-confirm for testing
    }

    void onAuthenticationComplete(NimBLEConnInfo& connInfo) override {
        if (connInfo.isEncrypted()) {
            Serial.println("*** SMP PAIRING SUCCESS! ***");
            Serial.println("Connection encrypted with MITM protection");
        }
    }

    uint32_t onPassKeyRequest() override { return 0; }
    void onPassKeyNotify(uint32_t pin) override {}
    bool onSecurityRequest() override { return true; }
};

// In setup():
NimBLEDevice::setSecurityCallbacks(new SecureCallbacks());
```

### MAC Tie-Breaker in Arduino

```cpp
NimBLEAddress myAddr = NimBLEDevice::getAddress();
NimBLEAddress peerAddr = advertisedDevice->getAddress();

// Compare addresses - lower initiates connection
if (myAddr < peerAddr) {
    // We initiate connection
    NimBLEClient* client = NimBLEDevice::createClient();
    client->connect(peerAddr);
} else {
    // Wait for peer to connect to us
}
```

### Complete Arduino Example

See the doxygen `@section ARDUINO_PORTING` in `secure_smp_pairing.c` for a complete skeleton.

## Files

| File | Description |
|------|-------------|
| `secure_smp_pairing.c` | Complete ESP-IDF example with doxygen documentation |
| `README.md` | This file |

## References

- [Bluetooth Core Spec v5.3, Vol 3, Part H](https://www.bluetooth.com/specifications/specs/) - Security Manager Specification
- [ESP-IDF NimBLE Examples](https://github.com/espressif/esp-idf/tree/master/examples/bluetooth/nimble)
- Bug #113: SMP Pairing Timeout Investigation
- [Gemini's SMP Analysis](../../test/gemini_smp_test_corrections.md)

## License

SPDX-License-Identifier: GPL-3.0-or-later
