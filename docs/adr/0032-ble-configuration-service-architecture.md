# 0032: BLE Configuration Service Architecture

**Date:** 2025-11-11 (Updated 2025-12-17: Added Time Beacon + Hardware Info characteristics for UTLP/AD048)
**Phase:** Phase 1b
**Status:** Approved
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of mobile app control for motor parameters, LED settings, and status monitoring,
facing the need for a dedicated GATT service separate from bilateral control,
we decided to implement a comprehensive BLE Configuration Service using production UUIDs with 13 logically grouped characteristics,
and neglected using temporary test UUIDs that would require future migration,
to achieve single point of control for BOTH single-device and dual-device operation,
accepting additional BLE stack complexity and NVS persistence requirements.

---

## Problem Statement

Mobile app control requires a dedicated GATT service for configuring motor parameters, LED settings, and monitoring device status. The service must work for both single-device testing and dual-device bilateral stimulation without code changes. Current implementation used temporary test UUIDs causing confusion and requiring future migration.

---

## Context

**Background:**
- Mobile app control requires dedicated GATT service separate from Bilateral Control Service (AD030)
- Current implementation uses temporary test UUIDs (`a1b2c3d4-e5f6-7890-a1b2-c3d4e5f6xxxx`)
- Nordic UART Service collision issue (`6E400002-B5A3-F393-E0A9-E50E24DCCA9E`) from AD008
- Configuration Service must work identically for single-device and dual-device modes
- Need production UUIDs from day one to avoid migration complexity

**Requirements:**
- Dedicated service for mobile app control
- Avoid Nordic UART Service UUID collision
- Single point of control for motor, LED, and status monitoring
- Work for both single-device and dual-device configurations
- User preference persistence across power cycles

---

## Decision

Implement comprehensive BLE Configuration Service using production UUIDs with logical characteristic grouping.

### Service Architecture

**Configuration Service** (Mobile App Control):
- **UUID**: `4BCAE9BE-9829-4F0A-9E88-267DE5E70200` (Project-specific, no Nordic collision)
- **Purpose**: Mobile app control for motor, LED, and status monitoring
- **Scope**: Used by both single-device and dual-device configurations

### UUID Scheme

**Base:** `4BCAE9BE-9829-4F0A-9E88-267DE5E7XXYY`
- **Project UUID Base:** `4BCAE9BE-9829-4F0A-9E88-267DE5E7____`
- **XX byte** (service type): `01` = Bilateral Control (AD030), `02` = Configuration Service (AD032)
- **YY byte** (characteristic ID): `00` = service UUID, `01-11` = characteristics

### Characteristics (22 Total)

**MOTOR CONTROL GROUP (8 characteristics):**

| UUID | Name | Type | Access | Range/Values | Purpose |
|------|------|------|--------|--------------|---------|
| `...0201` | Mode | uint8 | R/W/Notify | 0-4 | MODE_05HZ_25, MODE_1HZ_25, MODE_15HZ_25, MODE_2HZ_25, MODE_CUSTOM |
| `...0202` | Custom Frequency | uint16 | R/W | 25-200 | Hz × 100 (0.25-2.0 Hz research range) |
| `...0203` | Custom Duty Cycle | uint8 | R/W | 10-100% | Half-cycle duty (100% = entire half-cycle) |
| `...0204` | Mode 4 PWM Intensity | uint8 | R/W | 0, 30-80% | Mode 4 (Custom) motor strength (0% = LED-only) |
| `...020E` | Mode 0 PWM Intensity | uint8 | R/W | 50-80% | Mode 0 (0.5Hz) motor strength |
| `...020F` | Mode 1 PWM Intensity | uint8 | R/W | 50-80% | Mode 1 (1.0Hz) motor strength |
| `...0210` | Mode 2 PWM Intensity | uint8 | R/W | 70-90% | Mode 2 (1.5Hz) motor strength |
| `...0211` | Mode 3 PWM Intensity | uint8 | R/W | 70-90% | Mode 3 (2.0Hz) motor strength |

**LED CONTROL GROUP (5 characteristics):**

| UUID | Name | Type | Access | Range/Values | Purpose |
|------|------|------|--------|--------------|---------|
| `...0205` | LED Enable | uint8 | R/W | 0-1 | 0=off, 1=on |
| `...0206` | LED Color Mode | uint8 | R/W | 0-1 | 0=palette, 1=custom RGB |
| `...0207` | LED Palette Index | uint8 | R/W | 0-15 | 16-color preset palette |
| `...0208` | LED Custom RGB | uint8[3] | R/W | RGB 0-255 | Custom color wheel RGB values |
| `...0209` | LED Brightness | uint8 | R/W | 10-30% | User comfort range (eye strain prevention) |

**STATUS/MONITORING GROUP (4 characteristics):**

| UUID | Name | Type | Access | Range/Values | Purpose |
|------|------|------|--------|--------------|---------|
| `...020A` | Session Duration | uint32 | R/W | 1200-5400 sec | Target session length (20-90 min) |
| `...020B` | Session Time | uint32 | R/Notify | 0-5400 sec | Elapsed session seconds (0-90 min) |
| `...020C` | Battery Level | uint8 | R/Notify | 0-100% | SERVER battery state of charge |
| `...020D` | Client Battery | uint8 | R/Notify | 0-100% | CLIENT battery (dual-device mode) |

**FIRMWARE VERSION GROUP (2 characteristics):**

| UUID | Name | Type | Access | Range/Values | Purpose |
|------|------|------|--------|--------------|---------|
| `...0212` | Local Firmware Version | string(32) | R | "v0.6.47 (Dec 2 2025 15:30:45)" | Local device firmware version with build timestamp |
| `...0213` | Peer Firmware Version | string(32) | R | "v0.6.47 (Dec 2 2025 15:30:45)" | Peer device firmware version (dual-device mode, empty if no peer) |

**TIME SYNCHRONIZATION GROUP (1 characteristic) - AD047/UTLP:**

| UUID | Name | Type | Access | Range/Values | Purpose |
|------|------|------|--------|--------------|---------|
| `...0214` | Time Beacon | struct(14) | W | See below | UTLP time beacon for opportunistic adoption |

**Time Beacon Structure (14 bytes, packed):**
```c
typedef struct __attribute__((packed)) {
    uint8_t  stratum;         // 0=GPS, 1=network/cellular, 2+=peer-derived, 255=no external source
    uint8_t  quality;         // Signal quality 0-100 (GPS accuracy or battery for peers)
    uint64_t utc_time_us;     // Microseconds since Unix epoch (1970-01-01)
    int32_t  uncertainty_us;  // Estimated uncertainty (± microseconds)
} time_beacon_t;              // 14 bytes
```

### Time Beacon UTLP Semantics

**Philosophy: Passive Opportunistic Adoption**

The Time Beacon characteristic implements UTLP (Universal Time Layer Protocol) semantics within our BLE channel:

1. **Devices passively listen** - The characteristic is write-only; devices don't request time, they simply accept beacons when sources send them.

2. **Sources broadcast opportunistically** - PWAs, phones, or any connected source with GPS/cellular time can write beacons periodically. From the source's perspective, it's "broadcasting" time into our closed BLE channel.

3. **Stratum-based adoption** - Devices adopt time from lower stratum sources:
   - Stratum 0: GPS time (atomic clock accuracy)
   - Stratum 1: Phone/cellular network time
   - Stratum 2+: Peer-derived time (each hop increments)
   - Stratum 255: No external source (internal clock only)

4. **Quality as tiebreaker** - When stratums are equal, higher quality wins (battery level for peers, signal strength for GPS).

**Why "Beacon" not "Inject":**
- "Inject" implies device-initiated request/response
- "Beacon" emphasizes source-initiated broadcast semantics
- Devices are passive listeners that opportunistically benefit from any time source

**PWA Beacon Behavior:**
```javascript
// PWA broadcasts time beacons periodically while connected
setInterval(async () => {
    const gpsTime = await navigator.geolocation.getCurrentPosition();
    const beacon = {
        stratum: 0,  // GPS source
        quality: 100,
        utc_time_us: BigInt(gpsTime.timestamp) * 1000n,
        uncertainty_us: 1000  // ±1ms typical GPS
    };
    await characteristic.writeValue(encodeBeacon(beacon));
}, 1000);  // Every second
```

**Device Reception:**
- Always adopts received time (no stratum comparison needed for single-source)
- Updates internal stratum to match source
- SERVER propagates to CLIENT via time sync beacon
- Both devices now share GPS-quality synchronized time

**Rationale: "Closed Channel Broadcast"**
- BLE provides authenticated, encrypted channel (not open RF broadcast)
- But semantics remain broadcast-style: sources send, devices listen
- UTLP's opportunistic adoption works identically - just over BLE instead of WiFi/ESP-NOW

**HARDWARE INFO GROUP (2 characteristics) - AD048:**

| UUID | Name | Type | Access | Range/Values | Purpose |
|------|------|------|--------|--------------|---------|
| `...0215` | Local Hardware Info | string(48) | R | "ESP32-C6 v0.2 FTM:full" | Local device silicon revision and 802.11mc FTM capability |
| `...0216` | Peer Hardware Info | string(48) | R | "ESP32-C6 v0.2 FTM:full" | Peer device hardware info (dual-device mode, empty if no peer) |

**Hardware Info String Format:**
```
<model> v<major>.<minor> [FTM:full|FTM:resp]
```

**Examples:**
- `"ESP32-C6 v0.2 FTM:full"` - Silicon revision v0.2+, 802.11mc FTM Initiator + Responder supported
- `"ESP32-C6 v0.1 FTM:resp"` - Silicon revision v0.1, only FTM Responder (errata WIFI-9686)
- `"ESP32-C3 v0.4"` - Non-C6 chip, no FTM capability

**Purpose:**
- PWA can discover 802.11mc FTM capability without terminal output
- Enables adaptive transport layer decisions (ESP-NOW fallback threshold adjustment)
- Silicon revision affects range/timing capabilities
- Peer hardware info useful for diagnosing bilateral sync issues

**Data Flow:**
```
LOCAL Device                                     PWA
     |                                            |
     |<-- GATT read (local_hardware_info) --------|
     |                                            |
     |-- "ESP32-C6 v0.2 FTM:full" --------------->|
     |                                            |
     |<-- GATT read (peer_hardware_info) ---------|
     |                                            |
     |-- "ESP32-C6 v0.2 FTM:full" --------------->|
     |   (or "" if no peer connected)             |
```

### Per-Mode PWM Intensity Rationale

**Problem:** Preset modes (0.5Hz, 1.0Hz, 1.5Hz, 2.0Hz) have shorter active duty cycles by design (25% of half-cycle). When global PWM intensity is reduced, these modes feel weak compared to custom mode.

**Solution:** Each mode has its own PWM intensity setting with frequency-appropriate ranges:

**Low-Frequency Modes (0.5Hz, 1.0Hz):**
- Range: 50-80%
- Rationale: Longer activation periods (250-1000ms) allow lower PWM without feeling weak
- Default: 65%

**High-Frequency Modes (1.5Hz, 2.0Hz):**
- Range: 70-90%
- Rationale: Shorter activation periods (83-167ms) need higher PWM to feel perceptible
- Default: 80%
- Note: 2Hz especially needs "punch" due to brief 125ms activation at 25% duty

**Custom Mode (Mode 4):**
- Range: 30-80%
- Rationale: User controls both frequency AND duty, so wider intensity range needed
- Includes 0% for LED-only mode (no motor vibration)
- Default: 75%

**Benefits:**
- Users no longer need to adjust intensity when switching between preset modes
- Higher frequencies maintain therapeutic effectiveness at shorter duty cycles
- Each mode feels "right" out of the box
- PWM tuning per-mode enables frequency-dependent perceptual compensation

### LED Color Control Architecture

**Two-Mode System:**

1. **Palette Mode** (Color Mode = 0):
   - Uses 16-color preset palette (Red, Green, Blue, Yellow, etc.)
   - Mobile app selects via Palette Index (0-15)
   - Simple for users who want quick color selection
   - Palette defined in firmware (see `color_palette[]` in ble_manager.c)

2. **Custom RGB Mode** (Color Mode = 1):
   - Mobile app sends RGB values from color wheel/picker
   - Enables full-spectrum color selection
   - Allows precise color matching for therapeutic preferences
   - RGB values applied directly to WS2812B LED

**Brightness Application:**
```c
// Brightness is 10-30% for user comfort (eye strain prevention)
// Applied uniformly to all RGB channels regardless of color mode
uint8_t r_final = (source_r * led_brightness) / 100;
uint8_t g_final = (source_g * led_brightness) / 100;
uint8_t b_final = (source_b * led_brightness) / 100;
```

**Example:** Pure red RGB(255, 0, 0) at 20% brightness → RGB(51, 0, 0)

### Client Battery (Dual-Device Mode)

**Data Flow:**
```
CLIENT Device                    SERVER Device                   PWA
     |                                |                           |
     |-- SYNC_MSG_CLIENT_BATTERY ---->|                           |
     |   (coordination message)       |                           |
     |                                |-- GATT notify ----------->|
     |                                |   (client_battery char)   |
```

**Update Triggers:**
1. **Immediate:** When peer coordination starts (CLIENT sends battery to SERVER)
2. **Periodic:** Every 60 seconds (aligned with existing battery measurement cycle)

**Characteristic Behavior:**
- **Single-device mode:** Returns 0% (no CLIENT device)
- **Dual-device mode:** Returns CLIENT's last reported battery level
- **Read-only:** PWA cannot write this characteristic (data comes from CLIENT)
- **Notifications:** Optional subscribe for real-time updates

**Rationale for Always-Update (vs On-Demand):**
- Motor (ERM) dominates power consumption (4000-20000× more than BLE packet)
- Conditional updates add complexity with negligible power savings
- Data always available when PWA connects (no 60s wait)

### Firmware Version Characteristics

**Purpose:**
- Verify both devices run identical firmware builds before therapy sessions
- Detect firmware mismatch that could cause timing issues or protocol incompatibility
- Enable PWA to display version info for troubleshooting

**Local Firmware Version (Read-Only):**
- **Format**: `"vMAJOR.MINOR.PATCH (MMM DD YYYY HH:MM:SS)"`
- **Example**: `"v0.6.47 (Dec  2 2025 15:30:45)"`
- **Source**: Compile-time macros from `src/firmware_version.h`
- **Update**: Static, set at build time

**Peer Firmware Version (Read-Only):**
- **Single-device mode**: Returns empty string `""` (no peer connected)
- **Dual-device mode**: Returns peer's firmware version string after handshake
- **Exchange Protocol**: Sent via `SYNC_MSG_FIRMWARE_VERSION` coordination message during time sync handshake
- **Update Trigger**: Immediately after peer time sync handshake completes
- **Mismatch Handling**:
  - If `FIRMWARE_VERSION_CHECK_ENABLED=1` (default): Reject pairing, log warning, enter single-device mode
  - If `FIRMWARE_VERSION_CHECK_ENABLED=0` (dev mode): Allow pairing, log warning only

**Data Flow:**
```
CLIENT Device                    SERVER Device                   PWA
     |                                |                           |
     |<-- Time Sync Handshake ------->|                           |
     |                                |                           |
     |-- SYNC_MSG_FIRMWARE_VERSION -->|                           |
     |   (coordination message)       |                           |
     |                                |-- Store peer version      |
     |                                |                           |
     |<-- SYNC_MSG_FIRMWARE_VERSION --|                           |
     |                                |                           |
     |-- Store peer version           |                           |
     |                                |                           |
     |                                |<-- GATT read -------------|
     |                                |   (local_fw_version)      |
     |                                |                           |
     |                                |-- "v0.6.47..." ---------->|
     |                                |                           |
     |                                |<-- GATT read -------------|
     |                                |   (peer_fw_version)       |
     |                                |                           |
     |                                |-- "v0.6.47..." ---------->|
     |                                |   (or "" if no peer)      |
```

**Rationale:**
- **Build Timestamp Ensures Exact Match**: Version number (v0.6.47) alone insufficient - two developers compiling same version could have different bugs. Build timestamp guarantees binary-identical firmware.
- **Coordination Message (Not Beacon)**: Firmware version sent via coordination message (guaranteed delivery, requires ACK) instead of beacon (periodic, best-effort). Ensures both devices receive peer version before motors start.
- **Read-Only Characteristics**: PWA cannot modify firmware version (obviously). Only used for display and pre-session verification.
- **Empty String for No Peer**: Simplifies PWA logic - empty string clearly indicates single-device mode.

### Default Settings (First Boot)

- Mode: MODE_05HZ_25 (0.5 Hz @ 25% duty bilateral)
- Custom Frequency: 100 (1.00 Hz)
- Custom Duty: 50%
- PWM Intensity: 75%
- LED Enable: true
- LED Color Mode: 1 (Custom RGB)
- LED Custom RGB: (255, 0, 0) Red
- LED Brightness: 20%
- Session Duration: 1200 seconds (20 minutes)

### Duty Cycle Calculation (Half-Cycle Basis)

For bilateral alternating stimulation, each motor operates during HALF the total period:

```
Full Period (1.0 Hz example): 1000ms
├─ Half-Cycle A: 500ms (Motor A active, then coast)
│  ├─ Active: duty% × 500ms
│  └─ Coast: (100% - duty%) × 500ms
└─ Half-Cycle B: 500ms (Motor B active, then coast)
   ├─ Active: duty% × 500ms
   └─ Coast: (100% - duty%) × 500ms
```

**Calculation Formula:**
```c
uint32_t half_cycle_ms = period_ms / 2;           // 500ms for 1Hz
uint32_t motor_on_ms = (half_cycle_ms * duty) / 100;  // Max 500ms at 100% duty
uint32_t coast_ms = half_cycle_ms - motor_on_ms;      // Remaining coast time
```

**Why 10-100% is Safe:**
- **10% minimum:** Ensures motor activation above perceptual threshold (~30ms at 1Hz)
- **100% maximum:** Motor active for entire half-cycle, then coasts during peer's half-cycle
- **Overlap prevention:** Half-cycle calculation mathematically prevents motor overlap between directions
- **Research flexibility:** Full range allows studying intensity, battery, thermal tradeoffs
- **Hardware capability:** ERM motors and H-bridge support continuous 100% duty operation

**Example Values:**

| Frequency | Period | Half-Cycle | 10% Duty | 50% Duty | 100% Duty |
|-----------|--------|------------|----------|----------|-----------|
| 0.25 Hz | 4000ms | 2000ms | 200ms ON, 1800ms coast | 1000ms ON, 1000ms coast | 2000ms ON, 0ms coast |
| 1.0 Hz | 1000ms | 500ms | 50ms ON, 450ms coast | 250ms ON, 250ms coast | 500ms ON, 0ms coast |
| 2.0 Hz | 500ms | 250ms | 25ms ON, 225ms coast | 125ms ON, 125ms coast | 250ms ON, 0ms coast |

**Research Tradeoffs:**
- **Battery Life:** Higher duty = shorter runtime (100% duty at 0.25Hz = 2000ms continuous activation)
- **Thermal:** Extended high-duty operation may cause motor warming
- **Intensity:** Higher duty does NOT equal higher vibration amplitude (controlled by PWM intensity 0-80%)
- **Perception:** Therapeutic effectiveness vs. energy efficiency (researcher/therapist decision)

### NVS Persistence

**Saved Parameters (User Preferences):**
- Mode (uint8: 0-4) - Last used mode
- Custom Frequency (uint16: 25-200) - For Mode 4 (Custom)
- Custom Duty Cycle (uint8: 10-100%) - For Mode 4 (half-cycle duty)
- Mode 0 PWM Intensity (uint8: 50-80%) - 0.5Hz mode motor strength
- Mode 1 PWM Intensity (uint8: 50-80%) - 1.0Hz mode motor strength
- Mode 2 PWM Intensity (uint8: 70-90%) - 1.5Hz mode motor strength
- Mode 3 PWM Intensity (uint8: 70-90%) - 2.0Hz mode motor strength
- Mode 4 PWM Intensity (uint8: 30-80%, 0% = LED-only mode) - Custom mode motor strength
- LED Enable (uint8: 0 or 1)
- LED Color Mode (uint8: 0 or 1)
- LED Palette Index (uint8: 0-15)
- LED Custom RGB (uint8[3]: R, G, B)
- LED Brightness (uint8: 10-30%)
- Session Duration (uint32: 1200-5400 sec)

**NVS Signature:** CRC32 of characteristic UUID endings and data types (detects structure changes)

**Migration Strategy:** Clear NVS on signature mismatch (simple, clean slate for structural changes)

### BLE Advertising Configuration

**Advertising Parameters:**
- **Connection Mode**: Undirected connectable (`BLE_GAP_CONN_MODE_UND`)
- **Discovery Mode**: General discoverable (`BLE_GAP_DISC_MODE_GEN`)
- **Interval Range**: 20-40ms (0x20-0x40)
- **Duration**: Forever (`BLE_HS_FOREVER`) until disconnect

**Advertising Packet Fields (31-byte limit):**

| Field | Value | Purpose | Location |
|-------|-------|---------|----------|
| **Device Name** | `EMDR_Pulser_XXXXXX` | Human-readable ID (last 3 MAC bytes) | Advertising |
| **Flags** | `0x06` | General discoverable + BR/EDR not supported | Advertising |
| **TX Power** | Auto | Signal strength indication | Advertising |
| **Service UUID** | `...0200` | Configuration Service UUID for app filtering | **Scan Response** |

**Phase 1b Update:** Scan response now advertises **Bilateral Control Service** UUID (`...0100`) for peer discovery. Configuration Service UUID discovered via GATT after connection.

### Service UUID in Scan Response

The Configuration Service UUID **MUST** be included in scan response data to:
- Avoid exceeding 31-byte advertising packet limit
- Enable mobile app filtering for EMDR devices only
- Allow automatic device discovery without manual scanning
- Support service-based connection validation before GATT discovery
- Comply with BLE best practices for service advertisement

**Implementation:**
```c
// In ble_on_sync() - Advertising packet (device name, flags, TX power)
rc = ble_gap_adv_set_fields(&fields);

// Scan response packet (Configuration Service UUID)
struct ble_hs_adv_fields rsp_fields;
memset(&rsp_fields, 0, sizeof(rsp_fields));
rsp_fields.uuids128 = &uuid_config_service;
rsp_fields.num_uuids128 = 1;
rsp_fields.uuids128_is_complete = 1;
rc = ble_gap_adv_rsp_set_fields(&rsp_fields);
```

### Re-advertising Strategy

- **Trigger**: Automatic on client disconnect
- **Delay**: 100ms after disconnect (Android compatibility)
- **Error Handling**: BLE task retry on failure (30-second heartbeat)
- **Recovery**: Automatic restart ensures discoverability

**Rationale:**
- PWAs and mobile apps can filter `navigator.bluetooth.requestDevice()` by service UUID
- Prevents users from seeing non-EMDR devices in scan results
- Reduces connection attempts to wrong devices (battery savings)
- Standard practice for service-oriented BLE applications

---

## Consequences

### Benefits

- ✅ **Production UUIDs:** No test UUID migration complexity
- ✅ **Clear Separation:** Configuration (AD032) vs Bilateral Control (AD030)
- ✅ **Logical Grouping:** Motor (8), LED (5), Status (4), Firmware (2), Time (1), Hardware (2) = 22 characteristics
- ✅ **RGB Flexibility:** Palette presets AND custom color wheel support
- ✅ **Session Control:** Configurable duration (20-90 min) + real-time elapsed monitoring
- ✅ **Research Platform:** Full 0.25-2 Hz, 10-100% duty, 0-80% PWM (0%=LED-only)
- ✅ **User Comfort:** 10-30% LED brightness prevents eye strain
- ✅ **Persistent Preferences:** NVS saves user settings across power cycles
- ✅ **Firmware Version Verification:** PWA can verify both devices run matching firmware builds
- ✅ **Hardware Discovery:** PWA can discover silicon revision and 802.11mc FTM capability (AD048)
- ✅ **Future-Proof:** Architecture supports bilateral implementation without changes

### Drawbacks

- 22 characteristics increase BLE stack memory usage
- NVS persistence adds flash wear (mitigated by write-on-change only)
- Two LED color modes add configuration complexity
- Mobile app must implement both palette and custom RGB UIs
- UUID scheme requires documentation for app developers
- Firmware version exchange adds coordination message overhead (one-time at pairing)

---

## Options Considered

### Option A: Nordic UART Service (Rejected)

**Pros:**
- Standard service, well-documented
- Many example apps available

**Cons:**
- UUID collision with existing implementations
- Not designed for structured configuration
- No native characteristic grouping

**Selected:** NO
**Rationale:** UUID collision unacceptable, poor fit for use case

### Option B: Test UUIDs with Future Migration

**Pros:**
- Quick to implement
- Standard UUID format

**Cons:**
- Requires future migration effort
- Mobile apps need updates
- NVS data migration complexity

**Selected:** NO
**Rationale:** Migration overhead not worth temporary convenience

### Option C: Project-Specific Production UUIDs (Selected)

**Pros:**
- No collision risk
- Production-ready from day one
- Clear namespace organization
- No future migration needed

**Cons:**
- Requires custom UUID generation
- No existing example apps

**Selected:** YES
**Rationale:** Best long-term solution, avoids migration complexity

---

## Related Decisions

### Supersedes
- Test UUID scheme (`a1b2c3d4-e5f6-7890-a1b2-c3d4e5f6xxxx`)
- Nordic UART Service collision UUIDs from AD008

### Related
- AD030: Bilateral Control Service - Separate service for device-to-device communication
- AD031: Research Platform Extensions - Defines extended parameter ranges
- AD033: LED Color Palette Standard - Defines 16-color palette for palette mode
- AD047: Scheduled Pattern Playback - Time Beacon characteristic for UTLP integration
- AD048: ESP-NOW Adaptive Transport and Hardware Acceleration - Hardware Info characteristics for 802.11mc FTM discovery

---

## Implementation Notes

### Code References

- `src/ble_manager.c` - GATT service and characteristic definitions
- `src/ble_manager.c` - `color_palette[]` array (16-color master definition)
- `src/ble_manager.c` - NVS persistence implementation
- `src/ble_manager.h` - Public API for characteristic access

### Build Environment

- **Environment Name:** `xiao_esp32c6`
- **Configuration File:** `sdkconfig.xiao_esp32c6`
- **NimBLE Configuration:**
  - `CONFIG_BT_NIMBLE_MAX_CONNECTIONS=2` (peer + app simultaneous)
  - NVS namespace: `"ble_config"` for user preferences

### Testing & Verification

**Testing Required:**
- Mobile app connection and characteristic discovery
- Read/write operations for all 12 characteristics
- NVS persistence across power cycles
- Simultaneous peer + app connections (Phase 1b)
- LED color accuracy (palette vs custom RGB)
- Characteristic notifications (battery, session time)

**Known Limitations:**
- Configuration Service works identically for single-device and dual-device modes
- Dual-device coordination handled separately via Bilateral Control Service (AD030)
- Mobile app connects to ONE device's Configuration Service to control session

---

## JPL Coding Standards Compliance

- ✅ Rule #1: No dynamic memory allocation - All GATT data statically allocated
- ✅ Rule #5: Return value checking - All NimBLE API calls validated
- ✅ Rule #8: Defensive logging - All characteristic operations logged

---

## Integration Notes

- Configuration Service works identically for single-device and dual-device modes
- Dual-device coordination handled separately via Bilateral Control Service (AD030)
- Mobile app connects to ONE device's Configuration Service to control session
- LED Custom RGB mode is default (most users want color wheel control)
- Palette mode provides convenience for users who prefer presets

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: AD032 (lines 2968-3221)
Git commit: TBD (migration commit)

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-12-17
