# 0008: BLE Protocol Architecture

**Date:** 2025-10-15
**Phase:** 0.1
**Status:** Superseded (Phase 1b - November 14, 2025)
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of BLE service design for device-to-device and mobile app communication,
facing requirements for bilateral motor coordination and therapist configuration,
we decided for dual GATT service architecture with 128-bit custom UUIDs,
and neglected single service or Bluetooth SIG reserved UUIDs (0x1800/0x1801),
to achieve service isolation and collision-free UUID space,
accepting more complex UUID management and potential mobile app filtering issues.

**NOTE:** This decision was **SUPERSEDED** in Phase 1b (November 14, 2025) by project-specific UUID base `4BCAE9BE-9829-...`. See AD030 and AD032 for current UUIDs.

---

## Problem Statement

BLE communication requires two distinct service types:
1. **Bilateral Control Service**: Real-time motor coordination between paired devices
2. **Configuration Service**: Therapist control and session monitoring via mobile app

Initial UUID selection attempted to use:
- 0x1800 for Bilateral Control (WRONG - reserved by Bluetooth SIG for GAP)
- 0x1801 for Configuration (WRONG - reserved by Bluetooth SIG for GATT)

**Critical Issue:** Using reserved UUIDs causes device pairing failures and BLE stack conflicts.

How do we:
- Avoid UUID collisions with Bluetooth SIG standards?
- Separate bilateral motor timing from mobile app configuration?
- Enable concurrent connections (peer device + mobile app)?

---

## Context

### Bluetooth SIG UUID Reservations

**Reserved UUIDs:**
- 0x1800 = Generic Access Service (GAP) - mandatory on all BLE devices
- 0x1801 = Generic Attribute Service (GATT) - standard BLE service
- 0x180F = Battery Service (standard)
- **All 16-bit UUIDs (0x0000-0xFFFF)** are reserved or require Bluetooth SIG assignment

**Safe UUID Space:**
- 128-bit custom UUIDs (no SIG reservation required)
- Generated randomly or with project-specific pattern
- Guaranteed collision-free if properly generated

### Service Requirements

**1. Bilateral Control Service (Device-to-Device):**
- Real-time start/stop commands
- Cycle time configuration
- Motor intensity control
- Emergency shutdown coordination

**2. Configuration Service (Mobile App):**
- Session parameter configuration
- Battery status monitoring
- Error reporting
- Therapist override controls

### NimBLE Stack

**ESP-IDF v5.5.0 NimBLE:**
- Supports 128-bit UUIDs via `BLE_UUID128_INIT()` macro
- Little-endian byte ordering (reverse of standard UUID format)
- Multiple GATT services per device
- Concurrent connections supported

---

## Decision (HISTORICAL - Superseded by AD032)

We will use **128-bit custom UUIDs** with dual GATT service architecture.

**IMPORTANT:** This design used Nordic UART Service UUID pattern (`6E400001-...`), which was **REPLACED** in Phase 1b due to collision concerns. See AD032 for current project-specific UUIDs.

### UUID Design (HISTORICAL)

**Bilateral Control Service:**
```
UUID: 6E400001-B5A3-F393-E0A9-E50E24DCCA9E
Purpose: Real-time motor coordination
Connection: Peer device only
```

**Configuration Service:**
```
UUID: 6E400002-B5A3-F393-E0A9-E50E24DCCA9E
Purpose: Therapist configuration and monitoring
Connection: Mobile app or peer device
```

**UUID Pattern:**
- Base: `6E4000XX-B5A3-F393-E0A9-E50E24DCCA9E`
- 13th byte (position 12): Service ID (0x01, 0x02)
- 14th byte (position 13): Characteristic ID (0x01-0xFF)

### Characteristic UUID Assignment (HISTORICAL)

**Service UUID:**
```
6E4000XX-B5A3-F393-E0A9-E50E24DCCA9E
      ↑ (13th byte: service ID)
```

**Characteristic:**
```
6E40XXYY-B5A3-F393-E0A9-E50E24DCCA9E
      ↑  ↑
  13th  14th (characteristic ID)
```

**Example - Bilateral Control Service:**
```
6E400101 = Bilateral Command (service 01, char 01)
6E400201 = Total Cycle Time (service 01, char 02)
6E400301 = Motor Intensity (service 01, char 03)
```

**Example - Configuration Service:**
```
6E400201 = Mode Selection (service 02, char 01)
6E400202 = Battery Level (service 02, char 02)
6E400203 = Session Time (service 02, char 03)
```

### NimBLE Implementation (HISTORICAL)

```c
// SUPERSEDED: Do not use these UUIDs
// See AD032 for current project-specific UUIDs

// Bilateral Control Service: 6E400001-B5A3-F393-E0A9-E50E24DCCA9E
static const ble_uuid128_t bilateral_service_uuid =
    BLE_UUID128_INIT(0x9e, 0xca, 0xdc, 0x24, 0x0e, 0xe5,
                     0xa9, 0xe0, 0x93, 0xf3, 0xa3, 0xb5,
                     0x01, 0x00, 0x40, 0x6e);

// Configuration Service: 6E400002-B5A3-F393-E0A9-E50E24DCCA9E
static const ble_uuid128_t config_service_uuid =
    BLE_UUID128_INIT(0x9e, 0xca, 0xdc, 0x24, 0x0e, 0xe5,
                     0xa9, 0xe0, 0x93, 0xf3, 0xa3, 0xb5,
                     0x02, 0x00, 0x40, 0x6e);

// Note: BLE_UUID128_INIT uses reverse byte order (little-endian)
```

### Packet Loss Detection

**Enhanced Message Structure:**
```c
typedef struct {
    bilateral_command_t command;    // START/STOP/SYNC/INTENSITY
    uint16_t sequence_number;       // Rolling sequence number
    uint32_t timestamp_ms;          // System timestamp
    uint32_t data;                  // Cycle time or intensity
    uint16_t checksum;              // Integrity check
} bilateral_message_t;
```

**Detection Logic:**
- Sequence gap detection (missing sequence numbers)
- Timeout detection (no packets for >2 seconds)
- Consecutive miss threshold (3 missed = fallback)
- Automatic recovery when communication resumes

**Fallback Strategy:**
- Single-device mode (forward/reverse alternating)
- Non-overlapping maintained at all times
- LED heartbeat pattern during fallback
- Periodic scanning for lost peer

---

## Consequences (HISTORICAL)

### Benefits

- **Collision avoidance**: 128-bit UUIDs guaranteed not to conflict with Bluetooth SIG
- **Service isolation**: Bilateral timing not affected by mobile app configuration
- **Concurrent connections**: Both peer device and mobile app can connect
- **Security separation**: Different access controls for different functions
- **Related UUIDs**: Single byte difference makes services recognizable
- **Future expansion**: Easy to add services (0x03, 0x04) without affecting core functionality

### Drawbacks

- **UUID management**: 128-bit UUIDs harder to remember than 16-bit
- **Mobile app filtering**: Some BLE libraries filter by service UUID, causing discovery issues
- **Nordic UART collision**: `6E400001-...` collides with Nordic UART Service (discovered Phase 1b)
- **Documentation overhead**: Must document UUIDs clearly for mobile app developers

---

## Options Considered (HISTORICAL)

### Option A: 128-bit Custom UUIDs (6E400001 pattern) - SUPERSEDED

**Pros:**
- Collision-free UUID space
- Service isolation
- Concurrent connections
- Future expansion

**Cons:**
- Collided with Nordic UART Service
- Mobile app filtering issues

**Selected:** YES (initially)
**Rationale:** Avoided Bluetooth SIG collisions, but created Nordic UART collision

**SUPERSEDED BY:** Project-specific UUID base `4BCAE9BE-9829-...` (AD032, Phase 1b)

### Option B: Bluetooth SIG Reserved UUIDs (0x1800/0x1801) - REJECTED

**Pros:**
- Shorter 16-bit UUIDs
- Easier to document

**Cons:**
- ❌ 0x1800 reserved for Generic Access Service (GAP)
- ❌ 0x1801 reserved for Generic Attribute Service (GATT)
- ❌ Causes pairing failures and BLE stack conflicts

**Selected:** NO
**Rationale:** Reserved UUIDs cause critical failures

### Option C: Single GATT Service for Both - REJECTED

**Pros:**
- Simpler UUID management
- Single service to advertise

**Cons:**
- No service isolation (bilateral timing affected by app)
- Harder to control access (peer vs. mobile app)
- Concurrent connections more complex

**Selected:** NO
**Rationale:** Service isolation critical for safety

---

## Related Decisions

### Superseded By
- [AD032: BLE Service UUID Namespace](0032-ble-service-uuid-namespace.md) - Phase 1b replaced with project-specific UUIDs

### Related
- [AD030: Bilateral Control Service Design](0030-bilateral-control-service-design.md) - Current bilateral service implementation
- [AD001: ESP-IDF v5.5.0 Framework Selection](0001-esp-idf-v5-5-0-framework-selection.md) - Provides NimBLE stack
- [AD007: FreeRTOS Task Architecture](0007-freertos-task-architecture.md) - BLE Manager task

---

## Implementation Notes

### HISTORICAL Code References (SUPERSEDED)

**DO NOT USE** these UUIDs in new code:
- `6E400001-B5A3-F393-E0A9-E50E24DCCA9E` (Bilateral Control - collides with Nordic UART)
- `6E400002-B5A3-F393-E0A9-E50E24DCCA9E` (Configuration)

**USE INSTEAD** (see AD032):
- `4BCAE9BE-9829-4F0A-9E88-267DE5E70100` (Bilateral Control)
- `4BCAE9BE-9829-4F0A-9E88-267DE5E70200` (Configuration)

### Current Code References (Phase 1b+)

- `src/ble_manager.c` - Project-specific UUIDs (AD032)
- `test/single_device_ble_gatt_test.c` - Historical single-device BLE test

### Testing & Verification (HISTORICAL)

**Phase 0.4-1a Testing:**
- ✅ Bilateral Control Service discovered by peer devices
- ✅ Configuration Service discovered by nRF Connect
- ⚠️ Web Bluetooth PWA filtering issues (fixed in Phase 1b.2)

**Phase 1b Issues:**
- ❌ Nordic UART Service collision discovered
- ❌ PWA "Show all BLE Devices" required for discovery
- ✅ Resolved by migrating to project-specific UUID base (AD032)

---

## JPL Coding Standards Compliance

- ✅ Rule #1: No dynamic memory - UUID structs statically allocated
- ✅ Rule #8: Defensive logging - BLE connection events logged

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: AD008 (Software Architecture Decisions)
Git commit: Current working tree

**IMPORTANT:** This AD is maintained for historical reference only. For current BLE UUID architecture, see:
- AD030: Bilateral Control Service Design
- AD032: BLE Service UUID Namespace (project-specific UUIDs)

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
