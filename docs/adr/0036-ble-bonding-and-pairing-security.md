# 0036: BLE Bonding and Pairing Security (Phase 1b.3)

**Date:** 2025-11-15
**Phase:** Phase 1b.3
**Status:** Approved
**Type:** Security

---

## Summary (Y-Statement)

In the context of peer-to-peer device discovery lacking authentication,
facing real security concerns (malicious battery values, command injection, peer impersonation),
we decided to implement BLE bonding/pairing with LE Secure Connections + Just Works + button confirmation,
and neglected passkey display, out-of-band pairing, or no pairing approaches,
to achieve secure authentication preventing unauthorized connections before Phase 1c and Phase 2,
accepting additional complexity (pairing state machine, timeout handling, NVS storage, test environment).

---

## Problem Statement

Phase 1b.2 implements peer-to-peer discovery and connection, but lacks authentication. Any nearby BLE device advertising the Bilateral Control Service UUID can connect as a "peer", potentially:
- Sending malicious battery values to influence role assignment (Phase 1c)
- Injecting malicious commands during bilateral control (Phase 2)
- Impersonating legitimate peer device
- Causing denial of service by connecting and disconnecting repeatedly

This is a **real security concern** for BLE devices in public spaces (therapy offices, clinics) vulnerable to malicious connections from nearby attackers.

---

## Context

**Background:**
- Phase 1b.2 implements peer discovery but no authentication
- Phase 1c (battery-based role assignment) requires trusted battery values
- Phase 2 (command-and-control) requires authenticated command channel
- Devices lack displays for passkey entry (button-only input)
- NimBLE supports multiple pairing methods

**Security Threats:**
- **Peer Impersonation:** Attacker advertises as peer device, connects
- **Battery Manipulation:** Attacker sends false battery level to become SERVER
- **Command Injection:** Attacker sends malicious commands (Phase 2)
- **Denial of Service:** Repeated connect/disconnect prevents legitimate pairing

**Requirements:**
- Secure authentication before Phase 1c and Phase 2
- No display required (button-only confirmation)
- User-friendly pairing workflow
- Bonding data persistence (no re-pairing after reboot)
- Test mode (no NVS wear during development)
- Bounded timeouts (JPL compliance)

---

## Decision

Implement BLE bonding/pairing with **LE Secure Connections + Just Works + button confirmation** for peer connections BEFORE implementing Phase 1c (battery-based role assignment) and Phase 2 (command-and-control).

### Security Architecture

**1. BLE Pairing Method: LE Secure Connections with Just Works + Button Confirmation**

NimBLE supports multiple pairing methods. We chose **Just Works with button confirmation** because:
- ✅ **No Display Required:** Devices lack screens for passkey display
- ✅ **MITM Protection via Button:** User confirms pairing by pressing button (prevents passive attackers)
- ✅ **LE Secure Connections:** Uses ECDH (Elliptic Curve Diffie-Hellman) for key exchange
- ✅ **Bonding:** Long-term keys stored in NVS, no re-pairing after reboot
- ✅ **User Experience:** Simple "press button to pair" workflow

**NimBLE Security Configuration:**
```c
static const struct ble_gap_security_params security_params = {
    .bonding = 1,                           // Enable bonding (store keys in NVS)
    .mitm = 1,                              // Require MITM protection (button confirmation)
    .sc = 1,                                // Use LE Secure Connections (ECDH key exchange)
    .keypress = 0,                          // No keypress notifications
    .io_cap = BLE_HS_IO_KEYBOARD_DISPLAY,   // Support passkey input/display
    .oob = 0,                               // No out-of-band pairing
    .min_key_size = 16,                     // Require maximum key strength
    .max_key_size = 16,
    .our_key_dist = BLE_SM_PAIR_KEY_DIST_ENC | BLE_SM_PAIR_KEY_DIST_ID,
    .their_key_dist = BLE_SM_PAIR_KEY_DIST_ENC | BLE_SM_PAIR_KEY_DIST_ID,
};
```

### 2. Pairing Flow

```
Device A Boot                Device B Boot
     ↓                            ↓
[PAIRING_WAIT]              [PAIRING_WAIT]
  Purple LED                  Purple LED
  GPIO15 ON                   GPIO15 ON
     ↓                            ↓
  Advertising +              Advertising +
  Scanning                   Scanning
     ↓                            ↓
     └──── Peer Discovery ────────┘
              ↓
        BLE Connection
              ↓
     ┌─── Pairing Request ───┐
     │  (NimBLE automatic)    │
     └────────────────────────┘
              ↓
     Purple Pulsing LED       Purple Pulsing LED
     "Press button to pair"   "Press button to pair"
              ↓
     User presses button      User presses button
     (short press < 1s)       (short press < 1s)
              ↓
     ┌──── Confirmation ─────┐
     │  (numeric comparison)  │
     └────────────────────────┘
              ↓
        Bonding Success
              ↓
     Green 3× blink           Green 3× blink
     GPIO15 OFF               GPIO15 OFF
              ↓
     [MOTOR_ACTIVE]          [MOTOR_ACTIVE]
     Session timer starts    Session timer starts
```

### 3. Bonding Data Storage

**Production Mode** (`xiao_esp32c6` environment):
- Bonding keys stored in NVS partition
- Persistent across reboots (no re-pairing needed)
- NVS namespace: `"ble_sec"` (NimBLE default)

**Test Mode** (`xiao_esp32c6_ble_no_nvs` environment):
- Build flag: `-DBLE_PAIRING_TEST_MODE=1`
- Bonding data NOT written to NVS (prevents flash wear during testing)
- Forces fresh pairing every boot
- Allows unlimited pairing testing without NVS degradation

### 4. Timeout Handling

```c
// BLE Task State Machine
case BLE_STATE_PAIRING: {
    uint32_t pairing_elapsed = esp_timer_get_time()/1000 - pairing_start_time;

    if (pairing_elapsed >= 30000) {  // 30-second timeout (JPL bounded wait)
        ESP_LOGW(TAG, "Pairing timeout (30 seconds), disconnecting peer");
        ble_gap_terminate(peer_conn_handle, BLE_ERR_REM_USER_CONN_TERM);

        // Send failure message to motor task
        task_message_t msg = { .type = MSG_PAIRING_FAILED };
        xQueueSend(ble_to_motor_queue, &msg, 0);

        // LED feedback: Red 3× blink
        status_led_pattern(STATUS_PATTERN_PAIRING_FAILED);

        ESP_LOGI(TAG, "State: PAIRING → IDLE");
        state = BLE_STATE_IDLE;
    }

    // Feed watchdog during wait (JPL Rule #7)
    esp_task_wdt_reset();
    vTaskDelay(pdMS_TO_TICKS(100));
}
```

### 5. Status LED Feedback (GPIO15 + WS2812B Synchronized)

| State | GPIO15 (Discrete LED) | WS2812B (RGB LED) | Duration |
|-------|----------------------|-------------------|----------|
| **Waiting for Peer** | ON (solid) | Purple solid | Until peer discovered |
| **Pairing in Progress** | Pulsing (1 Hz) | Purple pulsing | Until user confirms or timeout |
| **Pairing Success** | OFF | Green 3× blink | 1.5 seconds |
| **Pairing Failed** | OFF | Red 3× blink | 1.5 seconds |

**Implementation:**
```c
// status_led.c - Synchronize GPIO15 with WS2812B patterns
void status_led_pattern(status_pattern_t pattern) {
    switch (pattern) {
        case STATUS_PATTERN_PAIRING_WAIT:
            gpio_set_level(GPIO_STATUS_LED, 0);  // ON (active low)
            set_ws2812b_color(PURPLE);
            break;

        case STATUS_PATTERN_PAIRING_PROGRESS:
            // Pulse GPIO15 and WS2812B together (1 Hz)
            start_led_pulse(PURPLE, 1000);  // Handles both LEDs
            break;

        case STATUS_PATTERN_PAIRING_SUCCESS:
            gpio_set_level(GPIO_STATUS_LED, 1);  // OFF
            blink_led(GREEN, 3, 250);  // 3× blink, 250ms each
            break;

        case STATUS_PATTERN_PAIRING_FAILED:
            gpio_set_level(GPIO_STATUS_LED, 1);  // OFF
            blink_led(RED, 3, 250);
            break;
    }
}
```

### 6. Motor Task Delayed Start

Motor task and session timer do NOT start until pairing completes:

```c
// motor_task.c
void motor_task(void *pvParameters) {
    motor_state_t state = MOTOR_STATE_PAIRING_WAIT;

    while (state != MOTOR_STATE_SHUTDOWN) {
        switch (state) {
            case MOTOR_STATE_PAIRING_WAIT: {
                // Wait for pairing completion message
                task_message_t msg;
                if (xQueueReceive(ble_to_motor_queue, &msg, pdMS_TO_TICKS(100)) == pdTRUE) {
                    if (msg.type == MSG_PAIRING_COMPLETE) {
                        ESP_LOGI(TAG, "Pairing complete, starting session");

                        // Initialize session timer NOW (not in main.c)
                        session_start_time_ms = esp_timer_get_time() / 1000;

                        ESP_LOGI(TAG, "State: PAIRING_WAIT → CHECK_MESSAGES");
                        state = MOTOR_STATE_CHECK_MESSAGES;
                    } else if (msg.type == MSG_PAIRING_FAILED) {
                        ESP_LOGW(TAG, "Pairing failed, retrying...");
                        // Stay in PAIRING_WAIT, user can trigger re-pair via button
                    } else if (msg.type == MSG_EMERGENCY_SHUTDOWN) {
                        ESP_LOGI(TAG, "State: PAIRING_WAIT → SHUTDOWN");
                        state = MOTOR_STATE_SHUTDOWN;
                    }
                }

                // Feed watchdog during wait
                esp_task_wdt_reset();
                break;
            }
            // ... rest of motor states ...
        }
    }
}
```

### 7. Button Task Pairing Confirmation

Short button press (< 1 second) during pairing confirms pairing:

```c
// button_task.c
case BTN_STATE_PRESSED: {
    uint32_t press_duration = esp_timer_get_time()/1000 - press_start_time;

    if (gpio_get_level(GPIO_BUTTON) == 1) {  // Button released
        ESP_LOGI(TAG, "Button released after %u ms", press_duration);

        // Check if we're in pairing mode
        if (ble_is_pairing()) {
            // ANY short press during pairing = confirmation
            ESP_LOGI(TAG, "Pairing confirmation (button press)");
            ble_sm_inject_io(peer_conn_handle, BLE_SM_IOACT_NUMCMP, 1);  // Confirm
            ESP_LOGI(TAG, "State: PRESSED → IDLE");
            state = BTN_STATE_IDLE;
        }
        else if (press_duration < 1000) {
            // Normal mode change (existing code)
            // ...
        }
        // ... rest of button logic ...
    }
}
```

---

## Consequences

### Benefits

- ✅ **Security:** Prevents unauthorized peer connections and command injection
- ✅ **User Experience:** Simple "press button to pair" workflow, no configuration needed
- ✅ **Testing:** Separate test environment prevents NVS wear during development
- ✅ **JPL Compliance:** Bounded timeouts, watchdog feeding, defensive logging
- ✅ **Foundation:** Establishes authentication for Phase 1c and Phase 2
- ✅ **MITM Protection:** Button confirmation prevents passive eavesdropping attacks
- ✅ **Encryption:** LE Secure Connections uses ECDH for secure key exchange
- ✅ **Persistence:** Bonding data stored in NVS (no re-pairing after reboot)

### Drawbacks

- Additional pairing step adds session start latency (30 seconds max)
- User must press button on both devices (two-handed operation during pairing)
- NVS storage required for bonding data (flash wear over device lifetime)
- Test mode requires separate build environment
- Pairing timeout may be too short for users with motor impairments (consider extending)

---

## Options Considered

### Option A: Passkey Display

**Pros:**
- Strongest MITM protection
- Standard BLE pairing method

**Cons:**
- Requires display (not available on device)
- Poor accessibility (vision impairment)

**Selected:** NO
**Rationale:** Hardware constraint (no display)

### Option B: Out-of-Band (NFC)

**Pros:**
- Very secure pairing
- Good user experience (tap to pair)

**Cons:**
- Requires NFC hardware (not available)
- Additional cost and PCB complexity

**Selected:** NO
**Rationale:** Hardware constraint (no NFC)

### Option C: Just Works (no button confirmation)

**Pros:**
- Simple UX (automatic pairing)
- No user action required

**Cons:**
- No MITM protection (vulnerable to active attacks)
- Passive eavesdropping possible

**Selected:** NO
**Rationale:** Insufficient security for therapeutic device

### Option D: Just Works + Button Confirmation (Selected)

**Pros:**
- Good security (MITM protection via button)
- Simple UX (press button to pair)
- No display required
- Standard BLE practice for button-only devices

**Cons:**
- Requires user action (acceptable tradeoff)
- Two-handed operation during pairing

**Selected:** YES
**Rationale:** Best balance of security and UX for button-only device

### Option E: No Pairing

**Pros:**
- Simplest implementation
- Fastest session start

**Cons:**
- Completely insecure (unacceptable for Phase 2)
- No protection against impersonation or command injection

**Selected:** NO
**Rationale:** Unacceptable security risk for therapeutic device

---

## Related Decisions

### Related
- AD028: Command-and-Control Architecture - Requires authenticated command channel (Phase 2)
- AD035: Battery-Based Initial Role Assignment - Requires trusted battery values (Phase 1c)
- AD030: Bilateral Control Service - Defines peer communication GATT service

---

## Implementation Notes

### Code References

**Modified Files:**
1. `src/motor_task.h` - Add `MSG_PAIRING_COMPLETE`, `MSG_PAIRING_FAILED`, `MOTOR_STATE_PAIRING_WAIT`
2. `src/motor_task.c` - Implement pairing wait state, delay session timer
3. `src/ble_task.h` - Add `BLE_STATE_PAIRING`
4. `src/ble_task.c` - Add pairing timeout handling
5. `src/ble_manager.c` - Add NimBLE security callbacks, bonding config
6. `src/button_task.c` - Add pairing confirmation handler
7. `src/status_led.c/h` - Add pairing LED patterns with GPIO15 sync
8. `src/main.c` - Remove session timer init (moved to motor task)
9. `platformio.ini` - Add `xiao_esp32c6_ble_no_nvs` environment

### Build Environment

**Production Mode:**
- **Environment Name:** `xiao_esp32c6`
- **Configuration File:** `sdkconfig.xiao_esp32c6`
- **NVS Partition:** Bonding data stored persistently

**Test Mode:**
- **Environment Name:** `xiao_esp32c6_ble_no_nvs`
- **Configuration File:** `sdkconfig.xiao_esp32c6_ble_no_nvs`
- **Build Flag:** `-DBLE_PAIRING_TEST_MODE=1`
- **NVS:** Bonding data NOT written (prevents flash wear)

### Testing & Verification

**1. Production Mode Testing:**
- Pair two devices
- Verify bonding persists after reboot
- Verify automatic reconnection without re-pairing
- Test timeout handling (wait 30 seconds without button press)

**2. Test Mode Testing:**
- Flash both devices with test environment
- Verify fresh pairing required every boot
- Test rapid pairing cycles (20+ iterations)
- Verify no NVS errors from repeated pairing

**3. Security Testing:**
- Attempt connection from unpaired third device (should fail)
- Verify bonding data cleared on factory reset
- Test pairing rejection (don't press button within 30s)

---

## Attack Mitigation

| Attack Vector | Mitigation |
|---------------|------------|
| **Peer Impersonation** | Bonding required - only previously paired devices can reconnect |
| **Malicious Battery Values** | Authenticated connection required before battery exchange |
| **Command Injection (Phase 2)** | All commands authenticated via bonded connection |
| **Denial of Service** | Pairing timeout (30s) prevents indefinite blocking |
| **Passive Eavesdropping** | LE Secure Connections uses ECDH encryption |
| **Man-in-the-Middle** | Button confirmation required (MITM protection enabled) |

---

## JPL Power of Ten Compliance

- ✅ **Rule #2 (Fixed loop bounds):** Pairing timeout enforced (30 seconds max)
- ✅ **Rule #6 (No unbounded waits):** All pairing waits bounded by timeout
- ✅ **Rule #7 (Watchdog compliance):** Watchdog fed during pairing wait states
- ✅ **Rule #8 (Defensive logging):** All pairing events logged (success/failure/timeout)

---

## Phase Dependencies

```
Phase 1b.1: Peer Discovery ✅ COMPLETE
Phase 1b.2: Bug Fixes (#7-#17) ✅ COMPLETE
Phase 1b.3: BLE Bonding/Pairing ⏳ IN PROGRESS ← We are here
Phase 1c: Battery-Based Role Assignment (depends on 1b.3 for security)
Phase 2: Command-and-Control (depends on 1b.3 for authentication)
```

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: AD036 (lines 3666-3981)
Git commit: TBD (migration commit)

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
