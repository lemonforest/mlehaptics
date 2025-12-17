The prototype build succeeded. The plan has been updated with your feedback: Key changes made:
Time adoption: Removed stratum comparison - always adopt PWA time (any direction)
Zone assignment: SERVER=ZONE_RIGHT, CLIENT=ZONE_LEFT initially (simple, role-based)
Future expansion: Noted in A1 that zone will decouple from role for 4+ devices
Now exiting plan mode to begin implementation:
Claude’s Plan
Bilateral Pattern Playback + UTLP Integration Plan
Branch: scheduled-pattern-playback Reference Docs:
docs/bilateral_pattern_playback_architecture.md
docs/UTLP_Specification.md
docs/UTLP_Technical_Report_v2.md
Overview
Implement pattern-based bilateral playback ("sheet music" paradigm) with selective UTLP integration, including cellular/GPS time injection from PWA. Key Goals:
Preserve existing therapy modes (0-4) - production firmware must not break
Add lightbar showcase mode (Mode 5/6) with synchronized LED patterns
Integrate UTLP stratum/quality concepts for improved time sync
Enable PWA to inject GPS/cellular time (Stratum 0→1 upgrade)
Phase A: Core Pattern Playback Infrastructure
A1: Zone Configuration Module
NEW FILES: src/zone_config.h, src/zone_config.c
typedef enum { ZONE_LEFT = 0, ZONE_RIGHT = 1 } device_zone_t;

// Initial implementation: Role-based zone assignment (simple for testing)
// SERVER = ZONE_RIGHT (starboard), CLIENT = ZONE_LEFT (port)
device_zone_t zone_config_get(void);      // Returns zone based on current role
Initial Approach (Simple):
No NVS, no BLE configuration needed
zone_config_get() simply returns ZONE_RIGHT if SERVER, ZONE_LEFT if CLIENT
Pattern segments have L/R columns - each device reads its zone's column
Future Expansion (4+ Devices / Mesh):
Will need explicit zone assignment via NVS or BLE
Zone becomes independent of role when >2 devices
Keep API stable: zone_config_get() / zone_config_set()
A2: CIE 1931 Perceptual LED Dimming
MODIFY: src/led_control.c NEW FILE: src/cie_lut.h (256-entry 10-bit LUT)
esp_err_t led_set_brightness_perceptual(uint8_t linear_brightness);
At 50% perceived = 18.4% actual duty (vs 50% linear). Smooth "organic" pulses.
A3: Sheet Header & Bilateral Segment Structures
NEW FILES: src/pattern_playback.h, src/pattern_playback.c
typedef struct __attribute__((packed)) {
    uint64_t born_at_us;      // Synchronized time = VERSION (LWW-CRDT)
    uint32_t content_crc;     // CRC32 of segments
    uint16_t segment_count;   // Max ~64 for 704 bytes
    uint8_t  mode_id;         // 5 = lightbar
    uint8_t  flags;           // LOOPING, LOCKED
} sheet_header_t;             // 16 bytes

typedef struct __attribute__((packed)) {
    uint16_t time_offset_ms;  // 0-65535ms from pattern start
    uint8_t  transition_ms_x4;// x4 scaling = 0-1020ms fade
    uint8_t  flags;           // sync_point, easing type
    uint8_t  waveform_id;     // Fade curve LUT index
    uint8_t  L_color, L_brightness, L_motor;  // Zone LEFT
    uint8_t  R_color, R_brightness, R_motor;  // Zone RIGHT
} bilateral_segment_t;        // 11 bytes
A4: Hardcoded Lightbar Patterns (MVP)
IN: src/pattern_playback.c
// Emergency vehicle RED/BLUE at 2Hz - compile-time pattern
static const bilateral_segment_t emergency_pattern[] = { ... };
Avoids BLE transfer complexity for initial demo.
A5: Conductor Task Modification
MODIFY: src/motor_task.c Add pattern playback path for Mode 5/6 while preserving Modes 0-4:
if (current_mode >= MODE_LIGHTBAR_START) {
    conductor_execute_segment(&active_sheet, my_zone);  // Pattern mode
} else {
    state = MOTOR_STATE_ACTIVE;  // Existing reactive mode
}
A6: GPTimer for Microsecond Precision
NEW FILES: src/pattern_timer.h, src/pattern_timer.c MODIFY: sdkconfig.xiao_esp32c6
esp_err_t pattern_timer_schedule_us(uint64_t target_us, callback_t cb);
Kconfig:
CONFIG_GPTIMER_ISR_HANDLER_IN_IRAM=y
CONFIG_GPTIMER_ISR_CACHE_SAFE=y
Phase B: UTLP Stratum/Quality Integration
B1: Extended Beacon Structure
MODIFY: src/time_sync.h
typedef struct __attribute__((packed)) {
    uint8_t  magic[2];        // 0xFE, 0xFE (UTLP identifier)
    uint8_t  stratum;         // 0=GPS, 1=phone, 255=peer-only
    uint8_t  quality;         // Battery level 0-100 (Swarm Rule)
    uint64_t server_time_us;  // Current synchronized time
    uint64_t motor_epoch_us;  // Pattern start time
    uint32_t motor_cycle_ms;  // Pattern period
    uint8_t  mode_id;         // Current mode
    uint8_t  sequence;        // Beacon sequence
    uint16_t checksum;        // CRC-16
} time_sync_beacon_v2_t;      // ~27 bytes
Backward compat: detect v1 vs v2 by magic bytes.
B2: Holdover Mode
MODIFY: src/time_sync.c Add explicit SYNC_STATE_HOLDOVER state:
Continue using frozen drift rate during disconnect
Degrade stratum (255 → internal "degraded" marker)
2-minute safety timeout (existing Phase 6r)
B3: Quality = Battery Level
Map existing battery_get_percentage() to UTLP quality field for leader election.
Phase B2: PWA Cellular/GPS Time Injection (Stratum 0→1 Upgrade)
B2.1: PWA Time Source Characteristic
MODIFY: src/ble_manager.h, src/ble_manager.c New BLE characteristic for PWA to inject time:
// New message type
SYNC_MSG_PWA_TIME_INJECT = 0x20,

typedef struct __attribute__((packed)) {
    uint8_t  stratum;         // 0=GPS, 1=network time
    uint8_t  quality;         // Signal quality 0-100
    uint64_t utc_time_us;     // Microseconds since Unix epoch
    int32_t  uncertainty_us;  // Estimated uncertainty (±)
} pwa_time_inject_t;
B2.2: Time Adoption Logic
MODIFY: src/time_sync.c
esp_err_t time_sync_inject_pwa_time(const pwa_time_inject_t* inject) {
    // ALWAYS adopt PWA time - we don't care about absolute date,
    // only that both devices agree on when seconds change.
    // This allows correction in ANY direction (forward or backward).
    // Prevents "time spoofing lockout" where high spoofed time blocks recovery.

    time_sync_set_external_reference(inject->utc_time_us, inject->stratum);

    // Propagate to peer if we're SERVER
    if (role == ROLE_SERVER) {
        broadcast_beacon_with_new_stratum();
    }

    ESP_LOGI(TAG, "PWA time adopted: stratum=%d, time=%llu us",
             inject->stratum, inject->utc_time_us);
    return ESP_OK;
}
Rationale: The goal is bilateral synchronization, not wall-clock accuracy.
We need both devices to agree on "when seconds change"
Absolute UTC correctness is irrelevant for therapy timing
Allowing any-direction changes prevents lockout from spoofed high timestamps
B2.3: PWA Implementation Notes (for docs)
The PWA can obtain high-precision time via:
// GPS time (best - Stratum 0)
navigator.geolocation.getCurrentPosition((pos) => {
    const gpsTime = pos.timestamp;  // Unix ms from GPS
}, null, { enableHighAccuracy: true });

// Performance timing for offset calculation
const t1 = performance.now();
// ... BLE round-trip ...
const t4 = performance.now();

// Inject to device
await characteristic.writeValue(encode({
    stratum: 0,  // GPS source
    quality: 100,
    utc_time_us: gpsTime * 1000,
    uncertainty_us: 1000  // ±1ms typical GPS
}));
B2.4: Stratum Propagation
When a device receives Stratum 0/1 time from PWA:
Device adopts phone's time as reference
Device updates its own stratum (255 → 1)
SERVER broadcasts updated beacon to CLIENT
CLIENT upgrades to Stratum 2 (one hop from source)
Both devices now have GPS-quality time sync
This is UTLP's "opportunistic synchronization" in action.
Phase C: BLE Pattern Transfer
C1: Pattern Transfer Protocol
MODIFY: src/ble_manager.h, src/ble_manager.c Write Without Response for throughput:
typedef struct __attribute__((packed)) {
    uint8_t  sequence;        // Packet sequence
    uint8_t  flags;           // FIRST, LAST, ACK_REQ
    uint16_t checksum;        // CRC16
    uint8_t  payload[];       // Pattern data
} pattern_transfer_packet_t;
Block ACK every 8 packets.
C2: Pattern RAM Storage
#define MAX_PATTERN_SEGMENTS 64  // 64 * 11 = 704 bytes
static pattern_buffer_t active_pattern;  // Static allocation
No NVS - patterns are session-local. PWA is source of truth.
C3: Pattern Validation
CRC check
Loop alignment (no "hanging notes")
Safe state requirement for final segment
Phase D: Full UTLP Compliance (Future/Optional)
D1: Transport Abstraction Layer
typedef struct {
    esp_err_t (*send_beacon)(const sync_beacon_t*);
    esp_err_t (*receive_beacon)(sync_beacon_t*, uint32_t timeout_ms);
    int64_t (*get_tx_timestamp)(void);
    int64_t (*get_rx_timestamp)(void);
} sync_transport_t;
Enable ESP-NOW, 802.11 LR, acoustic transports in future.
D2: Multi-Source Aggregation
Blend multiple stratum sources for improved accuracy.
File Summary
New Files
File	Purpose
src/zone_config.h/c	Zone config (initially role-based: SERVER=RIGHT, CLIENT=LEFT)
src/pattern_playback.h/c	Sheet music structures & executor
src/pattern_timer.h/c	GPTimer microsecond scheduler
src/cie_lut.h	CIE 1931 10-bit lookup table
Modified Files
File	Changes
src/time_sync.h	Extended beacon with stratum/quality, PWA time inject
src/time_sync.c	Holdover state, stratum adoption, PWA time handling
src/motor_task.c	Pattern playback path for Mode 5/6
src/led_control.c	CIE perceptual dimming function
src/ble_manager.h/c	Pattern transfer, PWA time inject characteristic
sdkconfig.xiao_esp32c6	GPTimer IRAM/cache-safe options
Implementation Priority
MVP for Lightbar Demo (Phase A + B2.1-B2.4)
Zone configuration (A1)
CIE 1931 dimming (A2)
Sheet/segment structures (A3)
Hardcoded patterns (A4)
Conductor task mod (A5)
Extended beacon with stratum (B1)
PWA time injection infrastructure (B2) ← User requested
Full Feature Set
GPTimer precision (A6)
Holdover mode (B2)
BLE pattern transfer (C1-C3)
Transport abstraction (D1-D2)
Risk Mitigation
Backward compat: Pattern playback is Mode 5/6 only - Modes 0-4 unchanged
Beacon versioning: Magic bytes detect v1 vs v2 format
PWA time trust: Always adopt (bilateral sync matters, not wall-clock accuracy)
JPL compliance: Static allocation, bounded loops, no recursion
Questions Resolved
Zone vs Role: Initially coupled (SERVER=RIGHT, CLIENT=LEFT), decoupled later for 4+ devices
PWA time injection: Added as Phase B2 - always adopt, any direction allowed
Pattern storage: RAM only, PWA is source of truth
Time spoofing: Not a concern - we only need devices to agree, not be UTC-accurate
User approved the plan
Update Todos

Create zone_config.h/c (SERVER=RIGHT, CLIENT=LEFT)

Add CIE 1931 perceptual dimming LUT to led_control

Create pattern_playback.h with sheet_header_t and bilateral_segment_t

Add hardcoded lightbar patterns in pattern_playback.c

Modify motor_task.c for pattern playback path (Mode 5/6)

Extend time_sync beacon with stratum/quality (v2)

Add PWA time injection characteristic and handler