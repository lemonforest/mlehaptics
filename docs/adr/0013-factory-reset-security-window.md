# 0013: Factory Reset Security Window

**Date:** 2025-11-08
**Phase:** 0.4
**Status:** Accepted
**Type:** Security

---

## Summary (Y-Statement)

In the context of NVS factory reset capability for service technicians,
facing the risk of accidental reset during therapeutic sessions,
we decided for time-limited factory reset (first 30 seconds only) with GPIO15 solid on indication,
and neglected always-available factory reset,
to achieve protection against accidental data loss,
accepting that factory reset requires device reboot for access.

---

## Problem Statement

A therapeutic device requires factory reset capability for service technicians to clear pairing data and user settings. However, factory reset must:
- Be accessible for initial setup and service
- Prevent accidental triggering during therapy sessions
- Provide clear visual warning before NVS clear
- Be distinguishable from emergency shutdown (5-second hold)
- Support conditional compilation for production builds

---

## Context

**Security Requirements:**
- Prevent accidental factory reset during 20+ minute therapy sessions
- Protect user pairing data and custom settings
- Service technician access during initial setup

**User Experience:**
- Clear visual indication of factory reset (different from emergency shutdown)
- Purple therapy light blink for emergency shutdown (5-second hold)
- GPIO15 solid on for factory reset warning (10-second hold)

**Technical Constraints:**
- Button held for 5 seconds: Emergency shutdown
- Button held for 10 seconds: Factory reset (only in first 30s after boot)
- ESP32-C6 boot time tracking
- NVS clearing includes pairing data

**Hardware:**
- GPIO15 status LED (on-board, active LOW)
- Purple therapy light (WS2812B, case-dependent)
- GPIO0 button for all interactions

---

## Decision

We implement time-limited factory reset capability with clear visual warning:

1. **Security Window:**
   - Factory reset available only in first 30 seconds after boot
   - Boot time tracking via esp_timer_get_time()
   - After 30 seconds: 10-second hold only triggers emergency shutdown

2. **Button Hold Timing:**
   - **5-second hold:** Emergency shutdown (purple therapy light blink)
   - **10-second hold (first 30s only):** Factory reset + emergency shutdown
   - **10-second hold (after 30s):** Emergency shutdown only

3. **LED Indication Pattern:**
   - **5-second hold:** Purple therapy light blink (emergency shutdown)
   - **10-second hold (first 30s):** GPIO15 solid on + purple blink (NVS clear warning)
   - **10-second hold (after 30s):** Purple blink only (no NVS clear)

4. **GPIO15 Rationale:**
   - Distinct from purple therapy light (separate on-board LED)
   - Solid on vs blinking provides clear differentiation
   - Always available (no case material dependency)
   - Active LOW: GPIO15 = 0 turns LED on

5. **Conditional Compilation:**
   - Factory reset can be disabled with `#ifndef ENABLE_FACTORY_RESET`
   - Production builds may disable factory reset entirely
   - Development builds enable factory reset for testing

---

## Consequences

### Benefits

- **Accidental Reset Prevention:** No factory reset during therapy sessions (after 30s)
- **Service Technician Access:** Reset available during initial setup window
- **Clear User Feedback:** GPIO15 solid on distinct from purple therapy light blink
- **Security Window:** 10-second hold only works in first 30 seconds after boot
- **Conditional Compilation:** Factory reset can be disabled in production builds
- **Dual Indication:** Both GPIO15 and purple light provide redundant warning

### Drawbacks

- **Requires Reboot:** Factory reset not available during active session
- **30-Second Window:** Service technician must act quickly after power-on
- **10-Second Hold:** Long hold time (but prevents accidental trigger)
- **NVS Clear Comprehensive:** Clears all data including pairing (intentional)

---

## Options Considered

### Option A: Time-Limited Factory Reset (First 30s) (Selected)

**Pros:**
- Prevents accidental reset during therapy sessions
- Service technician access during setup
- Clear security boundary
- Simple implementation (boot time tracking)

**Cons:**
- Requires device reboot to access factory reset
- 30-second window may be short for some workflows

**Selected:** YES
**Rationale:** Balances service access with accidental reset protection. 30-second window sufficient for service technicians while protecting active therapy sessions.

### Option B: Always-Available Factory Reset

**Pros:**
- No reboot required for factory reset
- Service technician convenience

**Cons:**
- ❌ High risk of accidental trigger during therapy
- ❌ User may hold button for 10 seconds during panic/emergency
- ❌ Data loss risk during critical sessions

**Selected:** NO
**Rationale:** Risk of accidental data loss too high for therapeutic device. Users may hold button during distress, triggering unintended factory reset.

### Option C: Hidden Factory Reset Sequence

**Pros:**
- Very low accidental trigger risk (e.g., triple-tap + hold)
- Service technician-only access

**Cons:**
- Complex button sequence
- Difficult to communicate to service technicians
- May be forgotten or require documentation lookup

**Selected:** NO
**Rationale:** Time-limited approach simpler and equally secure. Service technicians already familiar with boot-time service windows.

### Option D: Factory Reset via BLE Only

**Pros:**
- No button sequence required
- Mobile app control

**Cons:**
- Requires BLE connection (may fail if pairing corrupted)
- No hardware-only fallback
- Complex BLE security implementation

**Selected:** NO
**Rationale:** Factory reset must work when BLE pairing corrupted (common reset scenario). Hardware-only fallback essential.

---

## Related Decisions

### Related
- [AD011: Emergency Shutdown Protocol] - 5-second button hold for emergency shutdown
- [AD015: NVS Storage Strategy] - Data cleared by factory reset
- [AD026: BLE Pairing Data Persistence] - Pairing data cleared by factory reset

---

## Implementation Notes

### Code References

- `src/button_task.c` lines XXX-YYY (button hold timing and factory reset logic)
- `src/nvs_manager.c` lines XXX-YYY (nvs_clear_all() function)

### Build Environment

- **Environment Name:** `xiao_esp32c6`
- **Configuration File:** `sdkconfig.xiao_esp32c6`
- **Build Flags:** `-DENABLE_FACTORY_RESET` (optional, enables factory reset in production)

### Implementation Details

```c
// Boot time tracking
static uint64_t boot_time_us = 0;

void app_main(void) {
    boot_time_us = esp_timer_get_time();
    // ... rest of initialization
}

// Button task factory reset logic
void button_task(void* arg) {
    while (true) {
        uint32_t hold_duration_ms = get_button_hold_duration();
        uint64_t current_time_us = esp_timer_get_time();
        uint64_t elapsed_since_boot_ms = (current_time_us - boot_time_us) / 1000;

        if (hold_duration_ms >= 10000) {
            // 10-second hold detected
            if (elapsed_since_boot_ms <= 30000) {
                // Within 30-second window: Factory reset enabled
                gpio_set_level(GPIO_STATUS_LED, 0);  // GPIO15 solid on (active LOW)
                status_led_set_color(PURPLE);         // Purple therapy light blink

                // Wait for button release
                while (gpio_get_level(GPIO_BUTTON) == 0) {
                    vTaskDelay(pdMS_TO_TICKS(100));
                }

                // Execute factory reset
                ESP_LOGI(TAG, "Factory reset: Clearing NVS");
                nvs_clear_all();

                // Reboot
                esp_restart();
            } else {
                // After 30 seconds: Only emergency shutdown (no factory reset)
                status_led_set_color(PURPLE);  // Purple blink only
                // ... emergency shutdown logic
            }
        } else if (hold_duration_ms >= 5000) {
            // 5-second hold: Emergency shutdown only
            status_led_set_color(PURPLE);
            // ... emergency shutdown logic
        }

        vTaskDelay(pdMS_TO_TICKS(100));
    }
}
```

### Testing & Verification

**Hardware testing performed:**
- Factory reset within 30-second window (GPIO15 solid on, NVS cleared)
- Factory reset attempt after 30 seconds (no NVS clear, emergency shutdown only)
- Accidental button hold during therapy (no factory reset after 30s)
- NVS data cleared: Pairing data and settings confirmed cleared
- Reboot after factory reset: Clean device state

**Known limitations:**
- 30-second window may be short for some service workflows
- Requires device reboot to access factory reset
- 10-second hold time may feel long for service technicians

---

## JPL Coding Standards Compliance

- ✅ Rule #1: No dynamic memory allocation - Uses static boot_time_us variable
- ✅ Rule #2: Fixed loop bounds - Button polling loop bounded by session_active flag
- ✅ Rule #3: No recursion - Linear control flow
- ✅ Rule #4: No goto statements - Structured control flow
- ✅ Rule #5: Return value checking - nvs_clear_all() return checked
- ✅ Rule #6: No unbounded waits - Button release polling uses vTaskDelay()
- ✅ Rule #7: Watchdog compliance - Watchdog fed during button polling
- ✅ Rule #8: Defensive logging - Factory reset logged before execution

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: ### AD013: Factory Reset Security Window
Git commit: [to be filled after migration]

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
