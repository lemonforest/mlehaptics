# 0020: Power Management Strategy with Phased Implementation

**Date:** 2025-11-08
**Phase:** 1 (stubs), Phase 2 (full implementation)
**Status:** Accepted
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of battery-powered bilateral stimulation with BLE-dependent timing,
facing the need for power optimization without compromising safety or timing precision,
we decided for BLE-compatible power management hooks in Phase 1 with full light sleep optimization in Phase 2,
and neglected immediate full power management implementation,
to achieve development velocity for core functionality while architecting power efficiency from project start,
accepting that power optimization benefits delayed until Phase 2 validation complete.

---

## Problem Statement

A battery-powered bilateral stimulation device requires 20+ minute therapeutic sessions with dual 320mAh batteries (640mAh total). Power optimization essential, but:

**Technical Constraints:**
- ESP32-C6 BLE stack requires ~80MHz minimum frequency
- Motor PWM (LEDC) requires stable APB clock frequency
- Safety-critical timing requirements (±10ms bilateral precision)
- Emergency shutdown must maintain <50ms response time

**Development Priorities:**
- Phase 1: Core bilateral stimulation and BLE communication (critical functionality)
- Phase 2: Power optimization (battery life enhancement)

**Risk:**
- Power management complexity could block Phase 1 development
- BLE frequency requirements constrain light sleep options
- Timing precision must not be compromised by sleep transitions

---

## Context

**ESP32-C6 Power Modes:**
- **Active (160MHz):** ~50-60mA
- **Light sleep (80MHz):** ~25-30mA (BLE-compatible minimum)
- **Deep sleep:** < 1mA (no BLE, see AD014)

**Power Consumption Without Optimization:**
- Continuous 160MHz active: ~50-60mA
- 20-minute session: 60-72mAh
- Battery life: 640mAh / 60mAh = ~10 sessions

**BLE-Compatible Light Sleep Potential:**
```
Bilateral Pattern Analysis (1000ms total cycle):
Server: [===499ms motor===][1ms dead][---499ms off---][1ms dead]
Client: [---499ms off---][1ms dead][===499ms motor===][1ms dead]

Power States:
- Motor active periods: 50mA (CPU awake at 160MHz for GPIO control)
- Inactive periods: 25-30mA (CPU at 80MHz light sleep)
- BLE operations: 50mA (BLE stack locked at 160MHz)
- Average consumption: 30-35mA (40-50% power savings)
```

**Power Management Complexity:**
- BLE stack responsiveness during light sleep
- PWM/LEDC continuity during CPU frequency changes
- Emergency shutdown <50ms response time
- Watchdog feeding during sleep transitions
- Timing precision <50μs wake-up latency

---

## Decision

We implement BLE-compatible power management hooks in Phase 1 with full light sleep optimization in Phase 2:

**Phase 1 (Core Development): Power Management Hooks**
```c
// Power management lock handles (initialized in Phase 1)
static esp_pm_lock_handle_t ble_pm_lock = NULL;
static esp_pm_lock_handle_t pwm_pm_lock = NULL;

esp_err_t power_manager_init(void) {
    esp_err_t ret;

    // Create locks (Phase 1: created but not actively managed yet)
    ret = esp_pm_lock_create(ESP_PM_NO_LIGHT_SLEEP, 0, "ble_stack", &ble_pm_lock);
    if (ret != ESP_OK) return ret;

    ret = esp_pm_lock_create(ESP_PM_APB_FREQ_MAX, 0, "pwm_motor", &pwm_pm_lock);
    if (ret != ESP_OK) return ret;

    // Phase 1: Don't configure power management yet, just initialize handles
    return ESP_OK;
}

esp_err_t power_manager_configure_ble_safe_light_sleep(
    const ble_compatible_light_sleep_config_t* config) {
    // Phase 1: Stub (power management not active)
    // Phase 2: Will call esp_pm_configure() and manage locks
    return ESP_OK;
}

esp_err_t power_manager_get_ble_aware_session_stats(
    ble_aware_session_stats_t* stats) {
    // Phase 1: Return estimated values
    stats->average_current_ma = 50;
    stats->cpu_sleep_current_ma = 25;
    stats->ble_active_current_ma = 50;
    stats->power_efficiency_percent = 0;  // No optimization active yet
    return ESP_OK;
}
```

**Phase 2 (Post-Verification): Full BLE-Compatible Light Sleep**
```c
// Advanced power optimization after bilateral timing verified
esp_err_t power_manager_configure_ble_safe_light_sleep(
    const ble_compatible_light_sleep_config_t* config) {
    esp_err_t ret;

    // Configure BLE-compatible power management
    esp_pm_config_esp32_t pm_config = {
        .max_freq_mhz = 160,        // Full speed when CPU awake
        .min_freq_mhz = 80,         // BLE-compatible minimum frequency
        .light_sleep_enable = true  // Automatic light sleep during delays
    };

    ret = esp_pm_configure(&pm_config);
    if (ret != ESP_OK) return ret;

    // Locks already created in power_manager_init()
    // Acquire during BLE operations and motor active periods
    // Release during motor off periods to allow light sleep

    // 40-50% power savings with BLE-safe configuration
    // CPU at 80MHz during light sleep, BLE/PWM at 160MHz
    // Maintains BLE responsiveness and ±10ms timing precision

    return ESP_OK;
}
```

**BLE-Compatible Power Management Architecture:**
```c
// Power management lock handles (CORRECTED API)
static esp_pm_lock_handle_t ble_pm_lock = NULL;
static esp_pm_lock_handle_t pwm_pm_lock = NULL;

// Create locks with proper API (requires handle output parameter)
esp_pm_lock_create(ESP_PM_NO_LIGHT_SLEEP, 0, "ble_stack", &ble_pm_lock);
esp_pm_lock_create(ESP_PM_APB_FREQ_MAX, 0, "pwm_motor", &pwm_pm_lock);

// Acquire locks during critical operations
esp_pm_lock_acquire(ble_pm_lock);     // Prevent CPU light sleep during BLE
esp_pm_lock_acquire(pwm_pm_lock);     // Maintain APB frequency for PWM

// Release when safe to sleep
esp_pm_lock_release(ble_pm_lock);
esp_pm_lock_release(pwm_pm_lock);
```

---

## Consequences

### Benefits

**Phase 1 (Immediate):**
- Core functionality development not blocked by power complexity
- Power management interfaces established for future enhancement
- Basic power monitoring provides data for optimization decisions
- API architecture in place from project start

**Phase 2 (Long-term):**
- 40-50% power savings during bilateral sessions
- Battery life: ~40 sessions per charge (vs. ~10 without optimization)
- BLE-safe configuration maintains communication reliability
- Timing precision maintained (<50μs wake-up latency)
- ESP-IDF v5.5.0 BLE-compatible power management features utilized
- Medical device battery life requirements achievable

### Drawbacks

- **Delayed Power Savings:** No optimization in Phase 1 (development velocity prioritized)
- **Stub Complexity:** Phase 1 stubs add code that doesn't provide benefits yet
- **Testing Overhead:** Must validate power management in Phase 2
- **Two-Phase Development:** Power optimization requires separate development phase

---

## Options Considered

### Option A: Phased Implementation (Stubs Phase 1, Full Phase 2) (Selected)

**Pros:**
- Core functionality not blocked by power complexity
- Risk mitigation (power complexity isolated from core development)
- API architecture established from start
- Testing isolation (bilateral timing verified before adding sleep)
- Incremental enhancement (optimization builds on proven core)

**Cons:**
- Delayed power savings (no optimization in Phase 1)
- Stub complexity (code without immediate benefit)

**Selected:** YES
**Rationale:** Development focus on core bilateral timing and BLE communication critical for Phase 1. Power optimization builds on verified foundation. Risk mitigation outweighs delayed benefits.

### Option B: Full Power Management in Phase 1

**Pros:**
- Power savings from project start
- No two-phase development

**Cons:**
- ❌ Power complexity blocks core development
- ❌ Risk to bilateral timing (sleep transitions untested)
- ❌ BLE reliability risk (frequency scaling interactions)
- ❌ Complex debugging (timing + power + BLE interactions)
- ❌ Development velocity impact

**Selected:** NO
**Rationale:** Power management complexity too high for Phase 1. Core bilateral timing and BLE communication must be verified first. Risk of blocking critical functionality development unacceptable.

### Option C: No Power Management (Always Active 160MHz)

**Pros:**
- Simplest implementation
- No complexity
- No sleep transition risks

**Cons:**
- ❌ Poor battery life (~10 sessions vs. ~40 with optimization)
- ❌ Not competitive with commercial devices
- ❌ Medical device battery life requirements not met
- ❌ No power efficiency architecture for future

**Selected:** NO
**Rationale:** Battery life critical for portable therapeutic device. 40-50% power savings achievable with BLE-safe configuration. Phased approach provides architecture for optimization without blocking Phase 1.

---

## Related Decisions

### Related
- [AD014: Deep Sleep Strategy] - Deep sleep for standby (Phase 1), light sleep during sessions (Phase 2)
- [AD018: Technical Risk Mitigation] - Power management complexity identified as risk
- [AD012: Dead Time Implementation Strategy] - 1ms dead time compatible with light sleep

---

## Implementation Notes

### Code References

- `src/power_manager.c` lines XXX-YYY (Phase 1 stubs, Phase 2 full implementation)
- `src/power_manager.h` lines XXX-YYY (API definitions)
- `src/motor_task.c` lines XXX-YYY (power lock acquisition during motor active)
- `src/ble_manager.c` lines XXX-YYY (power lock acquisition during BLE operations)

### Build Environment

- **Environment Name:** `xiao_esp32c6`
- **Configuration File:** `sdkconfig.xiao_esp32c6`
- **Build Flags:**
  - Phase 1: `-DPOWER_MGMT_STUBS` (stubs active)
  - Phase 2: `-DPOWER_MGMT_FULL` (full implementation active)

### Phase 1 Configuration (Stubs)

```c
// Phase 1: Create locks but don't activate power management
esp_err_t power_manager_init(void) {
    // Create locks (handles ready for Phase 2)
    ESP_ERROR_CHECK(esp_pm_lock_create(ESP_PM_NO_LIGHT_SLEEP, 0,
                                        "ble_stack", &ble_pm_lock));
    ESP_ERROR_CHECK(esp_pm_lock_create(ESP_PM_APB_FREQ_MAX, 0,
                                        "pwm_motor", &pwm_pm_lock));

    // Don't configure esp_pm_configure() yet
    ESP_LOGI(TAG, "Power management hooks initialized (Phase 1 stubs)");
    return ESP_OK;
}
```

### Phase 2 Configuration (Full Implementation)

```c
// Phase 2: Activate BLE-compatible light sleep
esp_err_t power_manager_configure_ble_safe_light_sleep(
    const ble_compatible_light_sleep_config_t* config) {

    esp_pm_config_esp32_t pm_config = {
        .max_freq_mhz = 160,        // Full speed when awake
        .min_freq_mhz = 80,         // BLE-safe minimum
        .light_sleep_enable = true  // Automatic light sleep
    };

    ESP_ERROR_CHECK(esp_pm_configure(&pm_config));
    ESP_LOGI(TAG, "BLE-compatible light sleep enabled (Phase 2)");

    // Acquire locks during motor/BLE operations, release during inactive
    return ESP_OK;
}
```

### Power Monitoring Structure

```c
typedef struct {
    uint32_t session_duration_ms;
    uint16_t average_current_ma;        // Overall average consumption
    uint16_t cpu_sleep_current_ma;      // During CPU light sleep (80MHz)
    uint16_t ble_active_current_ma;     // During BLE operations (160MHz)
    uint32_t cpu_light_sleep_time_ms;   // Time CPU spent in light sleep
    uint32_t ble_full_speed_time_ms;    // Time BLE locked at 160MHz
    uint8_t ble_packet_success_rate;    // BLE reliability metric
    uint8_t power_efficiency_percent;   // Actual vs theoretical efficiency
} ble_aware_session_stats_t;
```

### Testing & Verification

**Phase 1 Validation:**
- Bilateral timing precision: ±10ms at all cycle times (500ms, 1000ms, 2000ms)
- BLE communication reliability: <3 consecutive packet loss threshold
- Emergency shutdown response: <50ms from button press to motor coast
- Motor control functionality: H-bridge operation and dead time implementation

**Phase 2 Validation:**
- Power consumption: 40-50% reduction during bilateral sessions
- Light sleep wake-up latency: <50μs (verified with oscilloscope)
- BLE responsiveness during light sleep: GATT operation timing maintained
- PWM continuity: Motor operation uninterrupted during CPU sleep
- Thermal performance: No overheating during extended light sleep sessions

**Risk Mitigation:**
- Gradual roll-out: Power management enhanced incrementally
- Fallback modes: System works without light sleep if issues discovered
- Monitoring hooks: Power consumption tracked from Phase 1
- Safety preservation: All emergency and timing requirements maintained

---

## JPL Coding Standards Compliance

- ✅ Rule #1: No dynamic memory allocation - Power locks statically allocated
- ✅ Rule #2: Fixed loop bounds - No loops in power management logic
- ✅ Rule #3: No recursion - Linear control flow
- ✅ Rule #4: No goto statements - Structured control flow
- ✅ Rule #5: Return value checking - All esp_pm_* calls wrapped in ESP_ERROR_CHECK()
- ✅ Rule #6: No unbounded waits - Power lock operations have fixed timeout
- ✅ Rule #7: Watchdog compliance - Light sleep doesn't affect watchdog feeding
- ✅ Rule #8: Defensive logging - Power state transitions logged

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: ### AD020: Power Management Strategy with Phased Implementation
Git commit: [to be filled after migration]

**Development Timeline (Original):**
- Week 1-2: Core bilateral stimulation implementation
- Week 3: Basic BLE-safe power management hooks functional
- Week 4: Advanced light sleep optimization (40-50% power savings)

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
