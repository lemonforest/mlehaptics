# Future Phases: BLE GATT Server Integration
## Power Management Compatibility Notes

**Date:** November 4, 2025  
**Status:** Planning for Post-Phase 4  
**Context:** BLE GATT server role for remote control/monitoring

---

## Overview

After completing Phase 4 (Full JPL Compliance), the next major feature will be **BLE GATT server** functionality. This document outlines power management considerations for BLE integration.

---

## BLE + Light Sleep Compatibility ✅

**Good news:** ESP32-C6 supports BLE connections during light sleep!

### How It Works:

```c
// Phase 2/3 light sleep (current)
vTaskDelay(pdMS_TO_TICKS(375));  // Auto light sleep
// → CPU sleeps, BLE would disconnect ❌

// BLE-compatible light sleep (future)
CONFIG_PM_ENABLE=y                          // Power management
CONFIG_BT_ENABLED=y                         // BLE stack
CONFIG_BTDM_CTRL_MODE_BLE_ONLY=y           // BLE only (no classic)
CONFIG_PM_POWER_DOWN_CPU_IN_LIGHT_SLEEP=y  // CPU can sleep
CONFIG_BT_SLEEP_ENABLE=y                   // BLE light sleep mode
CONFIG_BTDM_MODEM_SLEEP_MODE_ORIG=y        // Modem sleep during idle

// Then in code:
vTaskDelay(pdMS_TO_TICKS(375));
// → CPU enters light sleep
// → BLE modem stays active (low power mode)
// → BLE connections maintained ✅
// → Wakes on BLE events OR timer
```

### Power Consumption with BLE:

| State | Current (No BLE) | Current (with BLE) | Notes |
|-------|------------------|-------------------|-------|
| Motor active | 80mA | 85mA | +5mA for BLE radio |
| Coast (light sleep) | 2-5mA | 8-12mA | BLE modem active |
| Advertising only | N/A | 10-15mA | No connections |
| Connected idle | N/A | 8-12mA | Connection maintained |
| Deep sleep | <1mA | N/A | ❌ BLE disconnects |

**Key Point:** Light sleep is perfect for BLE. Deep sleep disconnects!

---

## Architecture Changes Needed

### Phase 2/3 (Current): Device-Only Operation

```
┌─────────────────────────────────────┐
│         EMDR Pulser Device          │
├─────────────────────────────────────┤
│ Button Control (GPIO1)              │
│  → Mode changes                     │
│  → Emergency shutdown               │
│                                     │
│ Motor Task                          │
│  → 4 modes (bilateral stimulation) │
│  → Light sleep during coast         │
│                                     │
│ Battery Task                        │
│  → Voltage monitoring               │
│  → LVO protection                   │
└─────────────────────────────────────┘
```

### Future: BLE GATT Server Integration

```
┌─────────────────────────────────────┐    ┌──────────────────┐
│         EMDR Pulser Device          │◄──►│  Phone/Tablet    │
│           (GATT Server)             │    │  (GATT Client)   │
├─────────────────────────────────────┤    ├──────────────────┤
│ BLE Task (NEW)                      │    │ Custom App       │
│  → GATT server                      │    │  → Mode select   │
│  → Characteristics:                 │    │  → Session start │
│    • Mode (R/W)                     │    │  → Battery level │
│    • Session control (W)            │    │  → Statistics    │
│    • Battery level (R/Notify)       │    └──────────────────┘
│    • Motor status (R/Notify)        │
│                                     │
│ Button Control (GPIO1)              │
│  → Fallback if BLE disconnected     │
│  → Emergency shutdown (always)      │
│                                     │
│ Motor Task                          │
│  → Receives commands from:          │
│    • BLE task queue (remote)        │
│    • Button task queue (local)      │
│  → Light sleep during coast ✅      │
│                                     │
│ Battery Task                        │
│  → Sends notifications to BLE       │
│  → LVO protection                   │
└─────────────────────────────────────┘
```

---

## Configuration Changes for BLE

### Additional sdkconfig Settings:

```ini
#
# Bluetooth
#
CONFIG_BT_ENABLED=y
CONFIG_BT_BLE_ENABLED=y
CONFIG_BTDM_CTRL_MODE_BLE_ONLY=y       # BLE only (no BR/EDR)
CONFIG_BT_NIMBLE_ENABLED=y              # Use NimBLE stack

#
# NimBLE Options
#
CONFIG_BT_NIMBLE_ROLE_PERIPHERAL=y      # GATT server role
CONFIG_BT_NIMBLE_ROLE_BROADCASTER=y     # Advertising
CONFIG_BT_NIMBLE_MAX_CONNECTIONS=1      # Single connection

#
# BLE Power Management
#
CONFIG_BT_SLEEP_ENABLE=y                # Enable BLE sleep
CONFIG_BTDM_MODEM_SLEEP_MODE_ORIG=y    # Modem sleep during idle
CONFIG_PM_ENABLE=y                      # Required for BLE sleep
CONFIG_FREERTOS_USE_TICKLESS_IDLE=y    # Light sleep

#
# BLE Security (Optional)
#
CONFIG_BT_NIMBLE_SM_LEGACY=y            # Pairing support
CONFIG_BT_NIMBLE_SM_SC=y                # Secure connections
```

### platformio.ini Changes:

```ini
[env:single_device_ble_gatt]
extends = env:single_device_battery_bemf_queued_test

build_flags = 
    ${env:single_device_battery_bemf_queued_test.build_flags}
    -DBLE_GATT_SERVER=1                # Enable BLE features
    -DBLE_DEVICE_NAME="EMDR_Pulser"   # BLE advertising name
```

---

## GATT Service Design (Draft)

### EMDR Therapy Service (Primary)

**UUID:** `0000FE00-0000-1000-8000-00805F9B34FB` (custom service)

#### Characteristics:

1. **Mode Control** (Read/Write)
   - UUID: `0000FE01-...-34FB`
   - Type: uint8
   - Values: 0=Mode1, 1=Mode2, 2=Mode3, 3=Mode4
   - Permissions: Read, Write
   - Action: Sends message to motor task queue

2. **Session Control** (Write)
   - UUID: `0000FE02-...-34FB`
   - Type: uint8
   - Values: 0=Stop, 1=Start, 2=Pause
   - Permissions: Write
   - Action: Controls session state

3. **Battery Level** (Read/Notify)
   - UUID: `0000FE03-...-34FB`
   - Type: uint8
   - Values: 0-100 (percentage)
   - Permissions: Read, Notify
   - Update: Every 10 seconds (from battery task)

4. **Motor Status** (Read/Notify)
   - UUID: `0000FE04-...-34FB`
   - Type: uint8
   - Values: 0=Stopped, 1=Forward, 2=Reverse, 3=Coast
   - Permissions: Read, Notify
   - Update: On state change

5. **Session Time Remaining** (Read/Notify)
   - UUID: `0000FE05-...-34FB`
   - Type: uint16
   - Values: Seconds remaining
   - Permissions: Read, Notify
   - Update: Every second

### Battery Service (Standard)

**UUID:** `0x180F` (org.bluetooth.service.battery_service)

#### Characteristics:

1. **Battery Level** (Read/Notify)
   - UUID: `0x2A19` (org.bluetooth.characteristic.battery_level)
   - Type: uint8
   - Values: 0-100 (percentage)
   - Standard battery service

---

## Message Queue Architecture (BLE Integration)

### New Queue: BLE → Motor

```c
// Add new queue
static QueueHandle_t ble_to_motor_queue = NULL;

// In ble_task:
void handle_mode_write(uint8_t new_mode) {
    task_message_t msg = {
        .type = MSG_MODE_CHANGE,
        .data.new_mode = new_mode
    };
    xQueueSend(ble_to_motor_queue, &msg, pdMS_TO_TICKS(100));
}

// In motor_task (modified):
while (session_active) {
    // Check ALL queues (priority order)
    task_message_t msg;
    
    // 1. Button (highest priority - local control)
    if (xQueueReceive(button_to_motor_queue, &msg, 0) == pdPASS) {
        handle_motor_command(&msg);
    }
    
    // 2. BLE (medium priority - remote control)
    else if (xQueueReceive(ble_to_motor_queue, &msg, 0) == pdPASS) {
        handle_motor_command(&msg);
    }
    
    // 3. Battery (lowest priority - warnings)
    else if (xQueueReceive(battery_to_motor_queue, &msg, 0) == pdPASS) {
        handle_battery_warning(&msg);
    }
    
    // Run motor cycle...
}
```

### New Queue: Motor → BLE (Status Updates)

```c
// Add new queue
static QueueHandle_t motor_to_ble_queue = NULL;

// In motor_task:
void update_motor_state(motor_state_t state) {
    ble_notification_t notif = {
        .type = NOTIF_MOTOR_STATUS,
        .data.motor_state = state
    };
    xQueueSend(motor_to_ble_queue, &notif, 0);  // Non-blocking
}

// In ble_task:
void ble_task(void *pvParameters) {
    while (1) {
        ble_notification_t notif;
        if (xQueueReceive(motor_to_ble_queue, &notif, pdMS_TO_TICKS(100)) == pdPASS) {
            // Send BLE notification to connected client
            ble_gatts_notify(notif.characteristic, notif.data);
        }
    }
}
```

---

## Power Budget with BLE

### Current (Phase 2 - No BLE):

| Component | Active | Light Sleep | Notes |
|-----------|--------|-------------|-------|
| ESP32-C6 CPU | 60mA | 2mA | Tickless idle |
| Motor (avg) | 10mA | 0mA | 25% duty cycle |
| Peripherals | 3mA | 0.5mA | ADC, LEDC, etc. |
| **Total** | **73mA** | **2.5mA** | |
| **Average (Mode 2)** | **25mA** | | 75% idle time |

### Future (with BLE):

| Component | Active | Light Sleep | Notes |
|-----------|--------|-------------|-------|
| ESP32-C6 CPU | 60mA | 2mA | Tickless idle |
| BLE Radio | 5mA | 6mA | Always on for connections |
| Motor (avg) | 10mA | 0mA | 25% duty cycle |
| Peripherals | 3mA | 0.5mA | ADC, LEDC, etc. |
| **Total** | **78mA** | **8.5mA** | |
| **Average (Mode 2)** | **32mA** | | +7mA vs no BLE |

### Battery Life Impact:

| Configuration | Mode 2 Current | Battery Life (dual 350mAh - 700mAh total) | vs Phase 2 |
|---------------|----------------|----------------------|------------|
| Phase 2 (No BLE) | 25mA | ~50 minutes | Baseline |
| Future (with BLE) | 32mA | ~40 minutes | -20% |

**Tradeoff:** Remote control costs ~10 minutes of battery life, but adds significant UX value.

---

## Implementation Phases

### Phase 5: Basic BLE (After Phase 4)

**Effort:** 1-2 weeks  
**Goal:** Minimal BLE GATT server

Features:
- ✅ BLE advertising
- ✅ Single connection
- ✅ Mode control characteristic (R/W)
- ✅ Battery level characteristic (R/Notify)
- ✅ Light sleep with BLE maintained
- ✅ Button control still works (fallback)

### Phase 6: Advanced BLE (Optional)

**Effort:** 2-3 weeks  
**Goal:** Full remote control and monitoring

Features:
- ✅ Session control (start/stop/pause)
- ✅ Motor status notifications
- ✅ Session timer
- ✅ Statistics (total sessions, battery cycles)
- ✅ BLE security (pairing, encryption)
- ✅ Firmware update over BLE (OTA)

---

## Testing Strategy

### BLE + Light Sleep Verification:

1. **Connection Stability:**
   - Connect phone to EMDR pulser via BLE
   - Start motor (enters light sleep during coast)
   - Verify BLE connection maintained for 20 minutes
   - Expected: No disconnections

2. **Command Responsiveness:**
   - Connect via BLE
   - Send mode change command during coast (device in light sleep)
   - Measure response latency
   - Expected: <100ms wake + command processing

3. **Power Consumption:**
   - Measure current with BLE connected vs disconnected
   - Verify BLE sleep mode active during coast
   - Expected: ~6-8mA additional (BLE modem)

4. **Notification Throughput:**
   - Subscribe to battery + motor status notifications
   - Run 20-minute session
   - Verify all notifications received
   - Expected: 100% delivery rate

---

## Compatibility Matrix

| Feature | Deep Sleep | Light Sleep (No BLE) | Light Sleep (BLE) |
|---------|-----------|---------------------|-------------------|
| Motor control | ✅ | ✅ | ✅ |
| Button wake | ✅ | ✅ | ✅ |
| Battery monitoring | ✅ | ✅ | ✅ |
| Power savings | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| BLE connections | ❌ | ❌ | ✅ |
| Remote control | ❌ | ❌ | ✅ |
| Use case | Standalone only | Standalone only | Remote + Standalone |

---

## Security Considerations

### BLE Security Features:

1. **Pairing (Optional):**
   - Numeric comparison (most secure)
   - Prevents unauthorized control
   - Configurable: Open vs Paired

2. **Encryption:**
   - Link-layer encryption
   - Protects command/data transmission
   - Standard BLE security

3. **Access Control:**
   - Emergency shutdown always via button
   - Critical safety functions not BLE-controlled
   - BLE for convenience only

### Recommended Security Policy:

```c
// Default: Open (no pairing required)
// User can enable pairing via button sequence
// Critical functions (emergency stop) always via button
```

---

## Conclusion

**BLE + Light Sleep = Perfect Match ✅**

Key Points:
- Light sleep maintains BLE connections (deep sleep doesn't)
- Power cost: ~7mA additional for BLE
- Battery life: ~40 minutes (vs 50 without BLE)
- User experience: Significantly improved with remote control
- Architecture: Message queues already support BLE integration
- Implementation: Straightforward after Phase 4 complete

**Phase 2/3 light sleep architecture is BLE-ready!**

---

## References

- **ESP32-C6 BLE Power Management:** https://docs.espressif.com/projects/esp-idf/en/v5.5/esp32c6/api-guides/low-power-mode.html
- **NimBLE Stack:** https://docs.espressif.com/projects/esp-idf/en/v5.5/esp32c6/api-reference/bluetooth/nimble/index.html
- **GATT Services:** https://www.bluetooth.com/specifications/gatt/
- **ESP32 BLE Examples:** https://github.com/espressif/esp-idf/tree/v5.5/examples/bluetooth/nimble

---

**Next Steps:** Complete Phase 2-4, then implement BLE in Phase 5! 🚀
