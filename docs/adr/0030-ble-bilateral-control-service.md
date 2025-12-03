# 0030: BLE Bilateral Control Service Architecture

**Date:** 2025-11-11 (Updated 2025-11-25 with Phase 6 Implementation)
**Phase:** Phase 6 (Bilateral Motor Coordination)
**Status:** Implemented
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of device-to-device bilateral coordination and research platform capabilities,
facing Nordic UART Service UUID collision from AD008,
we decided for project-specific UUID base (`4BCAE9BE-9829-4F0A-9E88-267DE5E7XXYY`) with coordination messages via time_sync_task,
and neglected per-cycle BLE commands (too much latency) or GATT characteristics for device-to-device (too complex),
to achieve collision-free namespace, instant mode switching, and precise bilateral motor coordination,
accepting motor epoch complexity and CLIENT phase reset requirements.

---

## Problem Statement

Current implementation (`single_device_ble_gatt_test.c`) provides Configuration Service for mobile app control but lacks device-to-device Bilateral Control Service. Research platform requirements expand beyond standard EMDR parameters (0.5-2 Hz) to explore wider frequency ranges and stimulation patterns. Nordic UART Service UUID collision (AD008) requires project-specific UUID base.

---

## Context

**Current Limitations:**
- Configuration Service: Mobile app control only (not device-to-device)
- Standard EMDR range: 0.5-2 Hz (limited for research)
- Nordic UUID collision: Prevents proper peer discovery

**Research Platform Goals:**
- Extended frequency range: 0.25-2 Hz (wider therapeutic exploration)
- Multiple stimulation patterns: BILATERAL_FIXED, BILATERAL_ALTERNATING, UNILATERAL
- Device-to-device coordination: Real-time bilateral control
- Data collection: Sequence numbers enable packet analysis

**Technical Requirements:**
- Collision-free UUID namespace
- Real-time command transmission (SERVER → CLIENT)
- Battery level exchange for role assignment
- Research parameter flexibility

---

## Decision

We implement BLE Bilateral Control Service using **coordination messages** sent via NimBLE GATT writes, processed by time_sync_task to avoid motor timing disruption.

**Service Architecture:**

**Bilateral Control Service** (Device-to-Device):
- **UUID:** `4BCAE9BE-9829-4F0A-9E88-267DE5E70100` (Project-specific, no Nordic collision)
- **Purpose:** Peer discovery during pairing and coordination message exchange

**UUID Scheme:**
```
Project UUID Base: 4BCAE9BE-9829-4F0A-9E88-267DE5E7XXYY
                                                ↑↑ ↑↑
                                            Service Char

Bilateral Control Service: 4BCAE9BE-9829-4F0A-9E88-267DE5E70100
                                                            01 00

Configuration Service:     4BCAE9BE-9829-4F0A-9E88-267DE5E70200
                                                            02 00
```

### Phase 6 Implementation: Coordination Messages

Instead of individual GATT characteristics, Phase 6 uses **coordination messages** sent via a single GATT characteristic. Messages are processed by `time_sync_task` (not motor_task) to prevent motor timing disruption.

**Coordination Message Types (`sync_message_type_t`):**

| Type | Value | Payload | Direction | Purpose |
|------|-------|---------|-----------|---------|
| `SYNC_MSG_MODE_CHANGE` | 0 | `mode_t new_mode` | SERVER→CLIENT | Button press mode change |
| `SYNC_MSG_SETTINGS` | 1 | `coordination_settings_t` | SERVER→CLIENT | BLE GATT parameter changes |
| `SYNC_MSG_SHUTDOWN` | 2 | None | Bidirectional | Emergency shutdown propagation |
| `SYNC_MSG_START_ADVERTISING` | 3 | None | SERVER→CLIENT | Re-enable BLE advertising |
| `SYNC_MSG_CLIENT_BATTERY` | 4 | `uint8_t battery_level` | CLIENT→SERVER | Client battery for PWA display |

**Settings Payload (`coordination_settings_t`):**
```c
typedef struct {
    uint16_t frequency_cHz;     // Hz × 100 (25-200 = 0.25-2.0 Hz)
    uint8_t duty_pct;           // 10-100% duty cycle
    uint8_t intensity_pct;      // 0-80% PWM (0% = LED-only)
    uint8_t led_enable;         // 0=off, 1=on
    uint8_t led_color_mode;     // 0=palette, 1=custom RGB
    uint8_t led_color_idx;      // 0-15 palette index
    uint8_t led_brightness_pct; // 10-30%
    uint8_t led_custom_r;       // Custom RGB red
    uint8_t led_custom_g;       // Custom RGB green
    uint8_t led_custom_b;       // Custom RGB blue
    uint32_t session_duration_sec; // 1200-5400 seconds
} coordination_settings_t;
```

### Motor Epoch Mechanism

Phase 6 uses **motor epoch** for bilateral timing synchronization instead of per-cycle BLE commands:

```
SERVER                              CLIENT
   |                                   |
   |-- Publishes motor epoch --------->|
   |   (time_sync_set_motor_epoch)     |
   |                                   |
   |-- Sends time sync beacon -------->|
   |   (ble_send_time_sync_beacon)     |
   |                                   |
   |   ACTIVE state                    |   INACTIVE state (drift correction)
   |   [motor_on_ms ON]               |   [calculated from epoch]
   |   [active_coast_ms coast]        |
   |                                   |
   |   INACTIVE state                  |   ACTIVE state
   |   [inactive_ms coast]            |   [motor_on_ms ON]
   |                                   |   [active_coast_ms coast]
```

**Motor Epoch Republish Triggers:**
1. **Mode change:** Button press changes mode 0-4
2. **Parameter change:** BLE GATT writes frequency/duty in Mode 4 (Custom)

**CLIENT Phase Reset:**
When CLIENT receives new timing parameters, it resets to INACTIVE state to resync with SERVER's new epoch. This prevents overlap when switching from slow→fast frequency.

### Implementation Files

| File | Function |
|------|----------|
| `src/ble_manager.h` | `sync_message_type_t`, `coordination_message_t` definitions |
| `src/ble_manager.c` | `ble_send_coordination_message()`, GATT handlers |
| `src/time_sync_task.c` | `handle_coordination_message()` - processes all message types |
| `src/time_sync.c` | `time_sync_set_motor_epoch()`, beacon generation |
| `src/motor_task.c` | Motor epoch publish, CLIENT phase reset on param change |

**Research Platform Stimulation Patterns:**

**1. BILATERAL_FIXED (Standard EMDR):**
```
Server: Always FORWARD stimulation
Client: Always REVERSE stimulation
Time     Server    Client
0-250    ON        OFF
250-500  OFF       ON
500-750  ON        OFF
750-1000 OFF       ON
```

**2. BILATERAL_ALTERNATING (Research Mode):**
```
Both devices alternate direction each cycle
Time     Server         Client
0-250    FORWARD ON     OFF
250-500  OFF           REVERSE ON
500-750  REVERSE ON    OFF
750-1000 OFF          FORWARD ON
```

**3. UNILATERAL (Control Studies):**
```
Only one device active (for research controls)
Server: Normal operation
Client: Remains OFF
```

**Extended Research Parameters:**

**Frequency Range (0.25-2 Hz):**
- Ultra-slow: 0.25 Hz (4000ms cycle) - research into slow processing
- Slow: 0.5 Hz (2000ms cycle) - standard EMDR minimum
- Standard: 1 Hz (1000ms cycle) - typical therapeutic rate
- Fast: 1.5 Hz (667ms cycle) - enhanced processing
- Ultra-fast: 2 Hz (500ms cycle) - standard EMDR maximum

**Safety Constraints:**
- Motor PWM: 0-80% (0% = LED-only mode, 80% max prevents overheating)
- Duty Cycle: 10-50% (timing pattern, 50% max prevents overlap)
- Non-overlapping: Time-window separation prevents overlap

**UUID Assignment Rationale:**

Using YY bytes (last 2 bytes) for characteristic differentiation:
```c
// Base service UUID: 4BCAE9BE-9829-4F0A-9E88-267DE5E70100
// Characteristic:    4BCAE9BE-9829-4F0A-9E88-267DE5E701YY where YY increments (01-0A)
static const ble_uuid128_t bilateral_cmd_uuid = BLE_UUID128_INIT(
    0x01, 0x01, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);
//    ↑     ↑
//   YY=01 XX=01 (Bilateral Command characteristic of Bilateral Control Service)
```

---

## Consequences

### Benefits

- **Research flexibility:** Extended frequency range (0.25-2 Hz) for studies
- **Pattern variety:** Three distinct stimulation patterns
- **Safety first:** Hard limits on PWM (30-80%) and duty cycle
- **Clear UUID scheme:** Incremental byte 14 for characteristics
- **Backward compatible:** Maintains standard EMDR capabilities
- **Data collection ready:** Sequence numbers enable packet analysis
- **Collision-free:** Project-specific UUID prevents Nordic UART conflict

### Drawbacks

- **Increased complexity:** 10 characteristics to manage vs. simpler service
- **UUID management:** Custom UUID base requires careful documentation
- **Testing burden:** Extended parameter ranges require validation
- **Memory overhead:** Multiple characteristics consume RAM/NVS

---

## Options Considered

### Option A: Continue with Nordic UART Service UUID

**Pros:**
- Well-known UUID
- Existing tooling support

**Cons:**
- Collision with Nordic UART Service (AD008)
- Prevents proper peer device discovery
- Not project-specific

**Selected:** NO
**Rationale:** UUID collision breaks peer discovery

### Option B: Standard EMDR Parameters Only (0.5-2 Hz)

**Pros:**
- Simpler service definition
- Fewer characteristics
- Matches clinical standards

**Cons:**
- Limits research capabilities
- Can't explore therapeutic boundaries
- Missed opportunity for platform extensibility

**Selected:** NO
**Rationale:** Research platform goals require extended parameters

### Option C: Project-Specific UUID with Extended Research Parameters (CHOSEN)

**Pros:**
- Collision-free namespace
- Extended research frequency range (0.25-2 Hz)
- Three stimulation patterns
- Future-proof for additional characteristics

**Cons:**
- Custom UUID management complexity
- More characteristics to implement and test

**Selected:** YES
**Rationale:** Best balance of collision-free operation and research flexibility

---

## Related Decisions

### Supersedes
- **AD008: Nordic UART Service UUID** - Replaced with project-specific UUID base

### Related
- **AD028: Command-and-Control Architecture** - Bilateral Command characteristic implements this
- **AD032: BLE Service UUID Namespace** - Documents project-specific UUID base design
- **AD035: Battery-Based Role Assignment** - Uses Bilateral Battery characteristic

---

## Implementation Notes

### Code References

- **BLE Manager:** `src/ble_manager.c` lines 2650-2730 (Bilateral Battery characteristic)
- **Motor Task:** `src/motor_task.c` line 269 (battery update calls)
- **UUID Definitions:** `src/ble_manager.c` (128-bit UUID constants)

### Build Environment

- **Environment Name:** `xiao_esp32c6`
- **Configuration File:** `sdkconfig.xiao_esp32c6`
- **Phase:** Phase 1b (Bilateral Battery implemented), Phase 2 (full service)

### Testing & Verification

**Phase 1b Implementation Status (November 14, 2025):**

✅ **Implemented Characteristics:**

| Characteristic | UUID | Type | Status | Phase |
|----------------|------|------|--------|-------|
| **Bilateral Battery** | `...E7010A` | uint8 R/Notify | ✅ Implemented | Phase 1b |
| Bilateral Command | `...E70101` | uint8 Write | ⏳ Pending | Phase 2 |
| Total Cycle Time | `...E70102` | uint16 R/W | ⏳ Pending | Phase 2 |
| Motor Intensity | `...E70103` | uint8 R/W | ⏳ Pending | Phase 2 |
| Stimulation Pattern | `...E70104` | uint8 R/W | ⏳ Pending | Phase 2 |
| Device Role | `...E70105` | uint8 Read | ⏳ Pending | Phase 1c |
| Session Duration | `...E70106` | uint32 R/W | ⏳ Pending | Phase 2 |
| Sequence Number | `...E70107` | uint16 Read | ⏳ Pending | Phase 2 |
| Emergency Shutdown | `...E70108` | uint8 Write | ⏳ Pending | Phase 2 |
| Duty Cycle | `...E70109` | uint8 R/W | ⏳ Pending | Phase 2 |

**Bilateral Battery Characteristic Implementation:**

```c
// src/ble_manager.c lines 2650-2730
// Bilateral Control Service Battery Characteristic
// Updated by motor_task every 60 seconds via ble_update_bilateral_battery_level()
// Allows peer devices to read battery level for role assignment (AD035)
static uint16_t bilateral_battery_handle;
static uint8_t bilateral_battery_level = 100;  // Default 100%
static SemaphoreHandle_t bilateral_data_mutex;  // Thread-safe access
```

Called by motor_task:
```c
// src/motor_task.c:269
if (battery_read_voltage(&raw_mv, &battery_v, &battery_pct) == ESP_OK) {
    ble_update_battery_level((uint8_t)battery_pct);           // Configuration Service
    ble_update_bilateral_battery_level((uint8_t)battery_pct); // Bilateral Control Service
    ESP_LOGI(TAG, "Battery: %.2fV [%d%%] | BLE: %s", battery_v, battery_pct,
             ble_get_connection_type_str());
}
```

**Integration with AD028 Synchronized Fallback:**

During BLE disconnection, devices use last known pattern setting:
- Phase 1 (0-2 min): Continue pattern with last timing reference
- Phase 2 (2+ min): Fallback based on pattern type:
  - BILATERAL_FIXED: Server=forward only, Client=reverse only
  - BILATERAL_ALTERNATING: Continue local alternation
  - UNILATERAL: Active device continues, inactive remains off

**Integration with AD035 (Battery-Based Role Assignment):**

Phase 1b provides battery exchange mechanism via Bilateral Battery characteristic. Phase 1c will implement role assignment logic that reads peer battery level and compares with local battery to determine SERVER vs CLIENT role.

---

## JPL Coding Standards Compliance

- ✅ Rule #1: No dynamic memory allocation - Static characteristic storage
- ✅ Rule #2: Fixed loop bounds - Deterministic characteristic updates
- ✅ Rule #3: No recursion - Linear GATT operations
- ✅ Rule #5: Return value checking - BLE function returns validated
- ✅ Rule #6: No unbounded waits - Non-blocking GATT operations
- ✅ Rule #7: Watchdog compliance - GATT operations don't block
- ✅ Rule #8: Defensive logging - ESP_LOGI for characteristic updates

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: AD030
Git commit: (phase 1b UUID update, bilateral battery implementation)

**UUID Clarification (AD032 Update):**

Phase 1b changed Bilateral Control Service UUID from `6E400001-...` (Nordic UART) to `4BCAE9BE-9829-4F0A-9E88-267DE5E70100` (project-specific). Characteristics within this service now use byte 13 for service type and bytes 14-15 for characteristic ID.

This prevents UUID collision with Nordic UART Service and provides clear namespace for project characteristics.

**Documentation Updates:**
- AD032: BLE Service UUID Namespace (project-specific UUID design)
- AD028: Command-and-Control (Bilateral Command characteristic usage)
- AD035: Battery-Based Role Assignment (Bilateral Battery characteristic usage)

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
