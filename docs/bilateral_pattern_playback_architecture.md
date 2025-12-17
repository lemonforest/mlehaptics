# Bilateral Pattern Playback Architecture

**Comprehensive Technical Specification for ESP32-C6 EMDR Devices**

*Version 1.0 — December 2025*

---

## Executive Summary

This document specifies a pattern-based bilateral playback architecture for EMDR therapeutic devices built on ESP32-C6 microcontrollers. The architecture replaces reactive timing calculations with deterministic "sheet music" execution, where both devices independently play from identical pre-loaded patterns using synchronized clocks.

The design leverages proven PTP-inspired time synchronization (±30μs precision over 90 minutes) as its foundation, extending this synchronized time reference to provide atomic pattern versioning without persistent storage. Key innovations include timestamp-based sheet identification, zone/role architectural separation, and CIE 1931 perceptual dimming for therapeutic LED output.

---

## 1. Architectural Foundation

### 1.1 The Sheet Music Paradigm

The fundamental insight driving this architecture comes from emergency vehicle lighting systems (Feniex, Whelen): synchronized modules don't negotiate timing per-flash. Instead, all modules receive the same pattern definition and execute independently from their local copy. Each module knows its position (left bar, right bar) and extracts its portion from the shared "sheet music."

Applied to bilateral EMDR stimulation, this means both handheld devices load identical pattern definitions containing timing and output values for **both** zones. Each device reads only its assigned zone (LEFT or RIGHT) and executes locally. No cycle-by-cycle coordination is needed during playback.

### 1.2 Why Reactive Timing Failed

The previous architecture used reactive antiphase calculation, where the CLIENT computed its timing offset from SERVER broadcasts. This approach produced a cascade of bugs:

- **Death spiral:** Correction algorithms oscillated and diverged instead of converging
- **Phase inversion:** CLIENT ended at 36ms position instead of 1000ms (in-phase rather than antiphase)
- **Stale data:** Beacon latency caused corrections based on outdated information
- **Complexity explosion:** ~500 lines of correction logic that fought itself (Bugs #16, #20, #26, #40-43)

### 1.3 Time Sync as Universal Foundation

The project's PTP-inspired time synchronization achieves ±30μs precision over 90-minute sessions—three orders of magnitude better than the ±10ms tolerance required for perceptible bilateral alternation. This excess precision enables a critical insight: *synchronized time itself can serve as a universal reference for any ordering problem*, not just playback timing.

---

## 2. Timestamp-Based Sheet Versioning

### 2.1 The Core Innovation

Traditional distributed systems use persistent sequence numbers or vector clocks for version ordering. This architecture eliminates persistence requirements by using the synchronized timestamp at pattern creation as the version identifier. Since both devices agree on time (±30μs), a timestamp uniquely and globally orders all pattern changes.

When any device initiates a mode change (button press, BLE command), it captures the current synchronized time. This timestamp *becomes* the sheet's version number. Higher timestamp = newer sheet. No NVS writes, no coordination protocol, no central authority for version assignment.

### 2.2 Sheet Header Structure

```c
typedef struct __attribute__((packed)) {
    uint64_t born_at_us;      // Synchronized time when sheet was created
    uint32_t content_crc;     // CRC32 of pattern segment data
    uint16_t segment_count;   // Number of segments in pattern
    uint8_t  mode_id;         // Human-readable mode reference
    uint8_t  flags;           // LOOPING, LOCKED, etc.
} sheet_header_t;             // 16 bytes — fits single BLE packet
```

### 2.3 Symmetric Mode Change Protocol

Either device can initiate mode changes. The protocol is identical regardless of which device originates the change:

```c
void on_mode_change(uint8_t new_mode_id) {
    uint64_t now_us;
    time_sync_get_time(&now_us);  // Same value on both devices
    
    active_sheet.born_at_us = now_us;
    active_sheet.mode_id = new_mode_id;
    active_sheet.content_crc = calculate_crc(patterns[new_mode_id]);
    
    broadcast_sheet_announcement(&active_sheet);
}
```

### 2.4 Reconnection Handshake

After a disconnection, devices exchange sheet headers before resuming playback:

| Scenario | Resolution |
|----------|------------|
| Same born_at_us, same CRC | Sheets match — verify phase alignment and resume |
| Same born_at_us, different CRC | **Error:** Corruption detected, re-transfer required |
| Different born_at_us | Higher timestamp is truth — lower device adopts newer sheet |
| Timestamps within ±100μs | Simultaneous change — SERVER role wins tiebreaker |

### 2.5 Epoch Derivation from Birth Time

The pattern's playback epoch (when cycle 0 begins) derives mathematically from the sheet's birth timestamp, eliminating the need to transmit or store it separately:

```c
uint64_t calculate_epoch(const sheet_header_t* sheet, uint32_t cycle_ms) {
    uint64_t cycle_us = cycle_ms * 1000;
    // Align to next cycle boundary after birth
    return ((sheet->born_at_us / cycle_us) + 1) * cycle_us;
}
```

---

## 3. Bilateral Pattern Structure

### 3.1 Segment Definition

Each pattern consists of timestamped segments containing output values for both zones. The structure is optimized for 32-bit alignment on RISC-V while minimizing memory footprint:

```c
typedef struct __attribute__((packed)) {
    uint16_t time_offset_ms;    // When to execute (0-65535ms from pattern start)
    uint8_t  transition_ms_x4;  // Fade duration (×4 scaling = 0-1020ms)
    uint8_t  flags;             // Bit 0: sync_point, Bits 1-2: easing type
    uint8_t  waveform_id;       // Index into fade curve LUT
    // Zone LEFT outputs
    uint8_t  L_color;           // Color palette index
    uint8_t  L_brightness;      // 0-255 (pre-gamma)
    uint8_t  L_motor;           // 0-255 intensity
    // Zone RIGHT outputs
    uint8_t  R_color;
    uint8_t  R_brightness;
    uint8_t  R_motor;
} bilateral_segment_t;          // 11 bytes per segment
```

### 3.2 Zone Extraction at Runtime

Each device extracts only its assigned zone from the bilateral pattern:

```c
void conductor_apply_segment(bilateral_segment_t* seg) {
    device_zone_t my_zone = get_hardware_zone();  // GPIO strap: LEFT or RIGHT
    
    uint8_t color, brightness, motor;
    if (my_zone == ZONE_LEFT) {
        color = seg->L_color;
        brightness = seg->L_brightness;
        motor = seg->L_motor;
    } else {
        color = seg->R_color;
        brightness = seg->R_brightness;
        motor = seg->R_motor;
    }
    
    led_set_color(color, CIE_LUT[brightness]);  // Apply gamma correction
    motor_set_intensity(motor);
}
```

### 3.3 Example: Standard EMDR 1Hz Pattern

```c
bilateral_segment_t emdr_1hz[] = {
    // T=0ms: LEFT active, RIGHT inactive
    { .time_offset_ms = 0,
      .L_color = GREEN, .L_brightness = 80, .L_motor = 180,
      .R_color = OFF,   .R_brightness = 0,  .R_motor = 0 },
    
    // T=500ms: LEFT inactive, RIGHT active (antiphase)
    { .time_offset_ms = 500,
      .L_color = OFF,   .L_brightness = 0,  .L_motor = 0,
      .R_color = GREEN, .R_brightness = 80, .R_motor = 180 },
}; // Loop point at 1000ms
```

---

## 4. Zone and Role Separation

### 4.1 Architectural Distinction

Drawing from Texas Instruments' software-defined vehicle architecture, the system separates two orthogonal concepts:

| Concept | Zone (Physical) | Role (Logical) |
|---------|-----------------|----------------|
| **Purpose** | Which outputs to drive | Who generates timing reference |
| **Values** | LEFT, RIGHT | SERVER, CLIENT |
| **Determined** | Hardware (GPIO strap at boot) | Runtime (battery level, device ID) |
| **Mutability** | Immutable | Can change (failover) |

This separation enables identical firmware on both devices. A LEFT-zone device can be either SERVER or CLIENT. Manufacturing doesn't need to track which unit goes in which hand—a single GPIO strap (or NVS flag) configures physical identity.

### 4.2 Implementation

```c
typedef enum { ZONE_LEFT = 0, ZONE_RIGHT = 1 } device_zone_t;
typedef enum { ROLE_NONE = 0, ROLE_SERVER = 1, ROLE_CLIENT = 2 } device_role_t;

typedef struct {
    device_zone_t zone;    // From GPIO/NVS, never changes
    device_role_t role;    // Runtime state, can change
    uint64_t device_id;    // MAC or serial
} device_identity_t;

// Zone from hardware strap at boot
device_zone_t determine_zone(void) {
    return gpio_get_level(ZONE_SELECT_PIN) ? ZONE_RIGHT : ZONE_LEFT;
}

// Role negotiation at runtime (e.g., higher battery becomes SERVER)
device_role_t negotiate_role(device_identity_t* self, device_identity_t* peer) {
    if (self->battery_mv > peer->battery_mv + 100) return ROLE_SERVER;
    if (peer->battery_mv > self->battery_mv + 100) return ROLE_CLIENT;
    return (self->device_id < peer->device_id) ? ROLE_SERVER : ROLE_CLIENT;
}
```

---

## 5. Perceptual LED Dimming (CIE 1931)

### 5.1 Why Linear PWM Fails

Human brightness perception follows a logarithmic curve (Weber-Fechner law). Linear PWM changes produce non-linear perceived brightness: the difference between 10% and 20% duty cycle is highly visible, while 80% to 90% appears nearly identical. For therapeutic applications where "organic" visual pulses reduce anxiety, this matters significantly.

### 5.2 The CIE 1931 Formula

The CIE 1931 lightness function (L*) models human perception. The inverse formula converts perceived brightness to actual luminance:

```
Y = L* / 903.3           for L* ≤ 8
Y = ((L* + 16) / 116)³   for L* > 8
```

At 50% perceived brightness, CIE 1931 outputs only 18.4% actual duty cycle—compared to 21.8% for gamma 2.2—providing noticeably smoother low-end dimming where human perception is most sensitive.

### 5.3 Pre-computed Lookup Table

For ISR-safe integer-only implementation, use a 256-entry lookup table (10-bit output for ESP32 LEDC):

```c
const uint16_t CIE_LUT_10BIT[256] = {
      0,    0,    1,    1,    2,    2,    3,    3,    4,    4,    4,    5,    5,    6,    6,    7,
      7,    8,    8,    8,    9,    9,   10,   10,   11,   11,   12,   12,   13,   13,   14,   15,
     15,   16,   17,   17,   18,   19,   19,   20,   21,   22,   22,   23,   24,   25,   26,   27,
     28,   29,   30,   31,   32,   33,   34,   35,   36,   37,   38,   39,   40,   42,   43,   44,
     45,   47,   48,   50,   51,   52,   54,   55,   57,   58,   60,   61,   63,   65,   66,   68,
     70,   71,   73,   75,   77,   79,   81,   83,   84,   86,   88,   90,   93,   95,   97,   99,
    101,  103,  106,  108,  110,  113,  115,  118,  120,  123,  125,  128,  130,  133,  136,  138,
    141,  144,  147,  149,  152,  155,  158,  161,  164,  167,  171,  174,  177,  180,  183,  187,
    190,  194,  197,  200,  204,  208,  211,  215,  218,  222,  226,  230,  234,  237,  241,  245,
    249,  254,  258,  262,  266,  270,  275,  279,  283,  288,  292,  297,  301,  306,  311,  315,
    320,  325,  330,  335,  340,  345,  350,  355,  360,  365,  370,  376,  381,  386,  392,  397,
    403,  408,  414,  420,  425,  431,  437,  443,  449,  455,  461,  467,  473,  480,  486,  492,
    499,  505,  512,  518,  525,  532,  538,  545,  552,  559,  566,  573,  580,  587,  594,  601,
    609,  616,  624,  631,  639,  646,  654,  662,  669,  677,  685,  693,  701,  709,  717,  726,
    734,  742,  751,  759,  768,  776,  785,  794,  802,  811,  820,  829,  838,  847,  857,  866,
    875,  885,  894,  903,  913,  923,  932,  942,  952,  962,  972,  982,  992, 1002, 1013, 1023,
};

// ISR-safe: pure integer lookup, no FPU
void IRAM_ATTR set_led_brightness(uint8_t brightness) {
    ledc_set_duty(LEDC_HIGH_SPEED_MODE, LEDC_CHANNEL_0, CIE_LUT_10BIT[brightness]);
    ledc_update_duty(LEDC_HIGH_SPEED_MODE, LEDC_CHANNEL_0);
}
```

---

## 6. ESP32-C6 Real-Time Constraints

### 6.1 Single-Core Architecture

The ESP32-C6 is a **single-core** RISC-V processor at 160MHz. Unlike ESP32-S3 (dual-core Xtensa), there is no option to dedicate one core to BLE and another to real-time control. The NimBLE stack creates four high-priority tasks (priorities 19-23) that share the single core with application code.

### 6.2 Task Priority Allocation

| Priority | Task | Notes |
|----------|------|-------|
| 23 | BT Controller | Highest — radio timing critical |
| 22 | esp_timer, NimBLE HCI | High-resolution callbacks |
| 21 | NimBLE Host | Bluetooth operations |
| **17-19** | **Conductor task** | Safe ceiling with BLE active |
| 5-10 | General application | Background processing |
| 1 | Main task (app_main) | Initialization only |

**Critical rule:** Never set application task priorities above 19 when BLE is running—starving the BLE stack causes instability and disconnections.

### 6.3 GPTimer for Microsecond Precision

For ±30μs timing, use GPTimer ISR callbacks rather than FreeRTOS software timers (which are limited to tick resolution, typically 1-10ms):

```c
#include "driver/gptimer.h"

static bool IRAM_ATTR timer_alarm_cb(gptimer_handle_t timer,
                                      const gptimer_alarm_event_data_t *edata,
                                      void *user_ctx) {
    BaseType_t high_task_woken = pdFALSE;
    xSemaphoreGiveFromISR(g_conductor_sem, &high_task_woken);
    
    // Schedule next alarm (dynamic timing)
    gptimer_alarm_config_t alarm_config = {
        .alarm_count = edata->alarm_value + next_segment_delay_us,
    };
    gptimer_set_alarm_action(timer, &alarm_config);
    
    return high_task_woken == pdTRUE;
}

void setup_gptimer(void) {
    gptimer_handle_t gptimer = NULL;
    gptimer_config_t config = {
        .clk_src = GPTIMER_CLK_SRC_DEFAULT,
        .direction = GPTIMER_COUNT_UP,
        .resolution_hz = 1000000,  // 1MHz = 1μs per tick
        .intr_priority = 2,
    };
    ESP_ERROR_CHECK(gptimer_new_timer(&config, &gptimer));
    
    gptimer_event_callbacks_t cbs = { .on_alarm = timer_alarm_cb };
    ESP_ERROR_CHECK(gptimer_register_event_callbacks(gptimer, &cbs, NULL));
    ESP_ERROR_CHECK(gptimer_enable(gptimer));
    ESP_ERROR_CHECK(gptimer_start(gptimer));
}
```

### 6.4 Essential Kconfig Settings

```kconfig
CONFIG_FREERTOS_HZ=1000
CONFIG_GPTIMER_ISR_HANDLER_IN_IRAM=y
CONFIG_GPTIMER_CTRL_FUNC_IN_IRAM=y
CONFIG_GPTIMER_ISR_CACHE_SAFE=y
CONFIG_ESP_TIMER_SUPPORTS_ISR_DISPATCH_METHOD=y
```

The `ISR_CACHE_SAFE` option is critical—without it, flash cache misses during OTA or NVS writes can add 10-100μs latency to ISR handlers.

### 6.5 Timer Wraparound

The `esp_timer_get_time()` function returns a **64-bit signed integer** (int64_t) representing microseconds since boot. Wraparound occurs after approximately 292,000 years—effectively infinite for any practical application. Your existing PTP-inspired synchronization can safely use it as the time base.

---

## 7. Pattern Validation and Integrity

### 7.1 CRC32 with Hardware Acceleration

ESP-IDF provides hardware-accelerated CRC functions in ROM:

```c
#include <esp_rom_crc.h>

uint32_t calculate_crc32(const uint8_t *data, size_t length) {
    return (~esp_rom_crc32_le(~0xFFFFFFFF, data, length)) ^ 0xFFFFFFFF;
}
```

### 7.2 Peer Verification Protocol

After reconnection, exchange sheet headers (16 bytes) and compare:

1. Exchange sheet headers over BLE (born_at_us, content_crc, segment_count)
2. Compare born_at_us to determine which sheet is newer
3. Verify content_crc matches if sheets claim to be identical
4. Calculate expected phase positions before resuming playback
5. If CRC mismatch on same-version sheets: trigger full re-transfer

### 7.3 Phase Alignment Verification

```c
bool verify_phase_alignment(uint64_t my_epoch, uint64_t peer_epoch, 
                            uint32_t cycle_ms, uint64_t now_us,
                            uint32_t peer_reported_position_ms) {
    // Both should have same epoch
    if (my_epoch != peer_epoch) return false;
    
    // Calculate expected positions
    uint32_t my_position_ms = (now_us - my_epoch) / 1000 % cycle_ms;
    uint32_t expected_peer_ms = (my_position_ms + cycle_ms/2) % cycle_ms;
    
    // Allow ±10ms tolerance for verification round-trip
    int32_t drift = (int32_t)peer_reported_position_ms - (int32_t)expected_peer_ms;
    return (abs(drift) < 10);
}
```

---

## 8. Loop Boundary Handling

### 8.1 The "Hanging Note" Problem

In MIDI sequencing, a critical edge case occurs when a "Note-On" event happens near the end of a loop and the corresponding "Note-Off" falls in the next iteration. If the sequencer resets its counter at the loop point, the "Off" command is lost and the motor vibrates indefinitely.

### 8.2 Recommended Solution: Clean Alignment

For therapeutic bilateral stimulation, require clean loop alignment rather than implementing complex carry-over logic:

- All motor/LED activations must complete before the loop point
- Final segment must return system to neutral/off state
- Validate at pattern load time: reject patterns where effects span boundaries
- No segment's (time_offset_ms + transition_ms) may exceed total duration

```c
bool validate_loop_alignment(const pattern_t *pattern) {
    if (!(pattern->flags & PATTERN_FLAG_LOOP)) return true;
    
    bilateral_segment_t *last = &pattern->segments[pattern->segment_count - 1];
    uint32_t last_end = last->time_offset_ms + (last->transition_ms_x4 * 4);
    
    // Must complete before loop point AND return to safe state
    return (last_end <= pattern->total_duration_ms) &&
           (last->L_motor == 0 && last->R_motor == 0);
}
```

This simplification eliminates an entire class of edge-case bugs while only slightly constraining pattern design—a worthwhile tradeoff for safety-adjacent therapeutic applications.

---

## 9. BLE Pattern Transfer Optimization

### 9.1 Write Without Response

Standard BLE Write Requests require round-trip acknowledgment for every packet, killing throughput. Use Write Without Response (WWR) for streaming, with application-layer block acknowledgments:

| Parameter | Recommended Value | Rationale |
|-----------|-------------------|-----------|
| MTU | 512 (request max) | Handle iOS 185 gracefully |
| Connection Interval | 7.5-15ms | Balance throughput/power |
| Write Type | Write Without Response | ~10x throughput |
| Block ACK Interval | Every 8 packets | ~1.5KB before ACK |
| Packet header | 5 bytes | Seq, length, checksum |

### 9.2 Realistic Throughput Expectations

- **iOS (185 MTU):** ~12 KB/s
- **Android (247-512 MTU):** ~30-60 KB/s
- **ESP32-to-ESP32 with DLE:** ~90 KB/s

### 9.3 Application-Layer Framing

```c
typedef struct __attribute__((packed)) {
    uint8_t  sequence;        // Packet sequence number
    uint16_t total_length;    // Total transfer size (first packet only)
    uint16_t checksum;        // CRC16 of this packet's payload
    uint8_t  payload[];       // Pattern data
} ble_transfer_packet_t;

// Block ACK every 8 packets
if (packet.sequence % 8 == 7) {
    send_block_ack(calculate_block_crc(last_8_packets));
}
```

---

## 10. Storage Strategy

### 10.1 RAM for Active Playback

Patterns are session-local: loaded into RAM from PWA, lost on power cycle. The PWA serves as the library and source of truth. This eliminates flash wear during playback and simplifies firmware updates (no pattern database migration).

### 10.2 NVS for Persistent Configuration

Reserve NVS for minimal system state that must survive power cycles:

- last_mode_id (uint8_t)
- global_intensity (uint8_t)
- led_brightness (uint8_t)
- paired_device_mac (uint8_t[6])
- device_zone (uint8_t) — if not using GPIO strap

### 10.3 NVS Limits and Best Practices

Maximum NVS blob size in ESP-IDF 5.x is **508,000 bytes**—far exceeding typical ~4KB pattern requirements. However, NVS writes during active playback should be avoided to prevent flash wear. Use "save-on-shutdown" protocol: hold changes in RAM, persist only on explicit save or graceful shutdown.

```c
void save_on_shutdown(void) {
    nvs_handle_t handle;
    nvs_open("config", NVS_READWRITE, &handle);
    nvs_set_u8(handle, "mode", current_mode);
    nvs_set_u8(handle, "intensity", current_intensity);
    nvs_commit(handle);
    nvs_close(handle);
}
```

---

## 11. Safety and Watchdog Architecture

### 11.1 Multi-Tier Watchdog Strategy

Professional lighting systems implement 50ms failover to safe state upon fault detection. For EMDR devices:

- **Tier 1 — Task health:** Conductor task checks in every 500ms
- **Tier 2 — Hardware WDT:** 5-second timeout triggers system reset
- **Tier 3 — Safe state:** Motors off, LEDs off, fault LED indication

### 11.2 Safe State Definition

```c
typedef struct {
    uint8_t led_brightness;    // 0 — LEDs off
    uint8_t motor_intensity;   // 0 — motors stopped
} safe_state_t;

void enter_safe_state(void) {
    motor_stop_all();
    led_set_all(0);
    log_fault_to_nvs();       // For post-mortem
    indicate_fault_via_led(); // User notification (e.g., red blink)
}
```

### 11.3 Task Health Monitoring

```c
static uint8_t task_checkin_flags = 0;
#define CONDUCTOR_BIT  (1 << 0)
#define BLE_BIT        (1 << 1)
#define SYNC_BIT       (1 << 2)
#define ALL_TASKS_MASK (CONDUCTOR_BIT | BLE_BIT | SYNC_BIT)

void watchdog_supervisor_task(void *arg) {
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(500));
        if (task_checkin_flags != ALL_TASKS_MASK) {
            ESP_LOGW(TAG, "Task health check failed: 0x%02X", task_checkin_flags);
            enter_safe_state();
        }
        task_checkin_flags = 0;  // Reset for next period
    }
}
```

---

## 12. Implementation Summary

### 12.1 Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| Pattern-based playback | Eliminates reactive calculation bugs; both devices execute from identical "sheet music" |
| Timestamp versioning | No NVS persistence needed; leverages existing ±30μs time sync as universal ordering |
| Zone/Role separation | Identical firmware on both devices; physical identity vs logical function decoupled |
| CIE 1931 dimming | Perceptually linear brightness for therapeutic "organic" pulses |
| GPTimer ISR | Hardware-based ±30μs timing on single-core ESP32-C6 with BLE stack |
| Clean loop alignment | Eliminates "hanging note" edge cases; patterns must complete before loop point |
| RAM-based patterns | PWA is source of truth; no flash wear during playback; session-local storage |

### 12.2 Migration Path

1. **Phase 1:** Implement sheet header structure and timestamp-based versioning
2. **Phase 2:** Add bilateral segment structure with zone extraction
3. **Phase 3:** Implement CIE 1931 gamma correction LUT
4. **Phase 4:** Refactor motor_task to conductor model
5. **Phase 5:** Add reconnection handshake with sheet comparison
6. **Phase 6:** Implement lightbar showcase mode (LED-only patterns)

---

## Appendix A: Protocol Comparison Matrix

| Feature | PTP Time Sync | Sheet Versioning |
|---------|---------------|------------------|
| **Purpose** | Establish shared clock reference | Establish shared "newness" reference |
| **Agreement** | "What time is it now?" | "Which sheet is current?" |
| **Persistence** | No persistent clock needed | No persistent version counter needed |
| **Reference source** | Atomic from beacon exchange | Atomic from timestamp at creation |
| **Precision** | ±30μs | Same (uses time sync) |

The sheet versioning system *parasitizes* the time sync foundation—it's a second-order application of the same principle: two devices can independently arrive at the same reference value through exchange rather than persistence.

---

## Appendix B: Reconnection State Machine

```
┌─────────────────┐
│   CONNECTED     │◄──────────────────────────────────┐
│                 │                                    │
│ Normal playback │                                    │
└────────┬────────┘                                    │
         │ BLE disconnect                              │
         ▼                                             │
┌─────────────────┐                                    │
│   AUTONOMOUS    │                                    │
│                 │                                    │
│ Continue from   │                                    │
│ local pattern   │                                    │
└────────┬────────┘                                    │
         │ BLE reconnect                               │
         ▼                                             │
┌─────────────────┐                                    │
│  HANDSHAKE      │                                    │
│                 │                                    │
│ Exchange sheet  │──── Sheets match ─────────────────►│
│ headers         │                                    │
└────────┬────────┘                                    │
         │ Sheets differ                               │
         ▼                                             │
┌─────────────────┐                                    │
│  RESYNC         │                                    │
│                 │                                    │
│ Newer sheet     │──── Sync complete ────────────────►│
│ wins, transfer  │
└─────────────────┘
```

---

## Appendix C: Emergency Lightbar Example Pattern

```c
// Classic police alternating pattern - RED/BLUE at 2Hz
// This single pattern is loaded on BOTH devices
bilateral_segment_t emergency_pattern[] = {
    // T=0ms: LEFT=RED, RIGHT=OFF
    { .time_offset_ms = 0,   .transition_ms_x4 = 0,
      .L_color = RED,  .L_brightness = 255, .L_motor = 0,
      .R_color = OFF,  .R_brightness = 0,   .R_motor = 0 },

    // T=250ms: LEFT=OFF, RIGHT=BLUE
    { .time_offset_ms = 250, .transition_ms_x4 = 0,
      .L_color = OFF,  .L_brightness = 0,   .L_motor = 0,
      .R_color = BLUE, .R_brightness = 255, .R_motor = 0 },

    // T=500ms: LEFT=RED, RIGHT=OFF
    { .time_offset_ms = 500, .transition_ms_x4 = 0,
      .L_color = RED,  .L_brightness = 255, .L_motor = 0,
      .R_color = OFF,  .R_brightness = 0,   .R_motor = 0 },

    // T=750ms: LEFT=OFF, RIGHT=BLUE
    { .time_offset_ms = 750, .transition_ms_x4 = 0,
      .L_color = OFF,  .L_brightness = 0,   .L_motor = 0,
      .R_color = BLUE, .R_brightness = 255, .R_motor = 0 },
}; // Loop point at 1000ms
```

This pattern demonstrates sub-millisecond synchronization between two battery-powered wireless devices—visible proof that the timing architecture works exactly as designed.

---

*— End of Document —*
