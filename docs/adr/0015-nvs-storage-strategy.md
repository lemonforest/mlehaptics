# 0015: NVS Storage Strategy

**Date:** 2025-11-08
**Phase:** 1c
**Status:** Accepted
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of persistent device configuration and pairing data,
facing the need for selective data persistence with testing mode flexibility,
we decided for selective NVS persistence with conditional compilation overrides,
and neglected storing all state data,
to achieve persistent pairing and settings without flash wear during testing,
accepting that session state is never persisted (see AD016).

---

## Problem Statement

A dual-device bilateral stimulation system requires persistent storage for:
- Device pairing information (peer MAC addresses)
- User configuration settings (Mode 5 custom parameters)
- Session statistics and usage tracking
- Future calibration data for motors

However, storage must:
- Support testing without flash wear
- Enable conditional compilation for different build modes
- Distinguish between settings (persistent) and session state (non-persistent)
- Survive power cycles and deep sleep

---

## Context

**Stored Data Categories:**

1. **Pairing Data (Critical):**
   - Peer device MAC address
   - BLE connection parameters
   - Role assignment history (optional)

2. **User Settings (Important):**
   - Mode 5 custom frequency (0.5-2.0 Hz)
   - Mode 5 custom duty cycle (10-50%)
   - Mode 5 LED color and brightness
   - Last used mode (optional)

3. **Session Statistics (Optional):**
   - Total session count
   - Total session duration
   - Usage patterns

4. **Calibration Data (Future):**
   - Motor calibration offsets
   - Battery calibration (see AD035)

**Session State (NEVER Stored - see AD016):**
- Current session elapsed time
- Current motor state
- Current mode

**Testing Considerations:**
- Flash wear during intensive testing (100k write cycles limit)
- Need to disable NVS writes during development
- Functional testing without storage side effects

**ESP32-C6 NVS:**
- Flash-based storage (100k write cycle limit per sector)
- Wear leveling built-in
- Namespaced key-value storage

---

## Decision

We implement selective persistence with testing mode overrides:

1. **Always Stored (Production and Testing):**
   - Device pairing information (MAC addresses)
   - User configuration settings (Mode 5 custom parameters)

2. **Conditionally Stored (Production Only):**
   - Session statistics (disabled in testing mode)
   - Usage tracking (disabled in testing mode)

3. **Never Stored:**
   - Session state (see AD016: No Session State Persistence)
   - Temporary runtime state

4. **Testing Mode Flag:**
```c
#ifdef TESTING_MODE
    // Disable session statistics NVS writes
    // Disable usage tracking NVS writes
    // Pairing and settings still persist (for functional testing)
#endif

#ifdef PRODUCTION_BUILD
    // Full NVS persistence enabled
    // Statistics and usage tracking enabled
#endif
```

5. **NVS Namespace Organization:**
   - `pairing`: Peer MAC address, connection parameters
   - `settings`: Mode 5 parameters, last mode
   - `stats`: Session count, duration (disabled in testing mode)
   - `calibration`: Motor/battery calibration (future)

---

## Consequences

### Benefits

- **Pairing Persistence:** Automatic reconnection after power cycle
- **User Settings:** Mode 5 custom parameters preserved
- **Testing Flexibility:** Statistics disabled during development (reduces flash wear)
- **Functional Testing:** Pairing and settings still work in testing mode
- **Flash Wear Reduction:** 100× fewer writes during testing (statistics disabled)
- **Clear Boundaries:** Session state never persisted (see AD016)

### Drawbacks

- **Conditional Compilation:** Different behavior in testing vs. production
- **Testing Mode Differences:** Statistics not tested until production build
- **Flash Wear Limit:** 100k write cycles per sector (managed by wear leveling)
- **No Session Recovery:** Power loss = new session (intentional, see AD016)

---

## Options Considered

### Option A: Selective Persistence with Testing Overrides (Selected)

**Pros:**
- Pairing and settings always persist (critical functionality)
- Statistics disabled in testing (reduces flash wear 100×)
- Functional testing works (pairing/settings available)
- Clear conditional compilation boundaries

**Cons:**
- Different behavior in testing vs. production
- Statistics not tested until production build

**Selected:** YES
**Rationale:** Balances functional testing (pairing/settings) with flash wear protection (statistics disabled). 100× reduction in write cycles during development critical for flash lifetime.

### Option B: Always Persist Everything

**Pros:**
- Consistent behavior across builds
- All features tested

**Cons:**
- ❌ Flash wear during testing (100× more writes)
- ❌ Statistics updates every session (unnecessary during development)
- ❌ Flash lifetime reduced significantly

**Selected:** NO
**Rationale:** Flash wear during development unacceptable. Testing typically runs hundreds of sessions per day, would quickly exceed 100k write cycle limit.

### Option C: Never Persist Anything (RAM Only)

**Pros:**
- No flash wear
- Fast testing iterations

**Cons:**
- ❌ Pairing lost after power cycle (critical functionality broken)
- ❌ User settings lost (poor user experience)
- ❌ Not representative of production behavior

**Selected:** NO
**Rationale:** Pairing persistence critical for dual-device system. Users expect settings to survive power cycles.

### Option D: External EEPROM for Settings

**Pros:**
- Unlimited write cycles (compared to flash)
- Separate storage from firmware

**Cons:**
- Additional hardware cost (~$0.50-1.00)
- I2C bus complexity
- Over-engineered for infrequent writes
- ESP32-C6 NVS sufficient

**Selected:** NO
**Rationale:** NVS with wear leveling sufficient for infrequent settings updates. External EEPROM adds cost and complexity without significant benefit.

---

## Related Decisions

### Related
- [AD016: No Session State Persistence] - Session state never persisted
- [AD011: Emergency Shutdown Protocol] - Pairing data preserved during emergency shutdown
- [AD026: BLE Pairing Data Persistence] - Details of pairing data storage
- [AD035: Battery-Based Initial Role Assignment] - Future battery calibration storage

---

## Implementation Notes

### Code References

- `src/nvs_manager.c` lines XXX-YYY (NVS initialization and namespace management)
- `src/nvs_manager.h` lines XXX-YYY (NVS API definitions)
- `src/ble_manager.c` lines XXX-YYY (pairing data save/load)

### Build Environment

- **Environment Name:** `xiao_esp32c6`
- **Configuration File:** `sdkconfig.xiao_esp32c6`
- **Build Flags:**
  - `-DTESTING_MODE` (disables statistics NVS writes)
  - `-DPRODUCTION_BUILD` (enables all NVS writes)

### NVS Namespace Structure

```c
// Pairing namespace (always persisted)
namespace "pairing" {
    "peer_mac": [6 bytes]           // Peer device MAC address
    "conn_params": [struct]         // BLE connection parameters
}

// Settings namespace (always persisted)
namespace "settings" {
    "mode5_freq": uint16_t          // Hz × 100 (0.5-2.0 Hz)
    "mode5_duty": uint8_t           // Percentage (10-50%)
    "mode5_led_color": uint8_t      // Color index (0-15)
    "mode5_led_brightness": uint8_t // Percentage (10-30%)
    "last_mode": uint8_t            // Last used mode (0-4)
}

// Statistics namespace (disabled in testing mode)
#ifndef TESTING_MODE
namespace "stats" {
    "session_count": uint32_t       // Total sessions
    "session_duration": uint32_t    // Total seconds
}
#endif

// Calibration namespace (future)
namespace "calibration" {
    "battery_max_mv": uint16_t      // Max battery voltage (mV)
    "motor_cal_offset": int8_t      // Motor calibration offset
}
```

### Testing & Verification

**Hardware testing performed:**
- Pairing data persistence: Confirmed MAC address survives power cycle
- Settings persistence: Mode 5 parameters survive deep sleep and power cycle
- Testing mode: Confirmed statistics NVS writes disabled (flash wear reduced)
- Production mode: Confirmed statistics NVS writes enabled
- Factory reset: Confirmed all NVS data cleared (see AD013)

**Flash Wear Analysis:**
```
Testing Mode (statistics disabled):
- Pairing data: 1 write per pairing (~1-10 total)
- Settings: 1 write per change (~10-100 per day)
- Total: ~100-1000 writes per week
- Flash lifetime: 100k cycles / 100 writes = 1000 weeks = 20 years

Production Mode (statistics enabled):
- Pairing data: 1 write per pairing (~1-10 total)
- Settings: 1 write per change (~1-10 per day)
- Statistics: 1 write per session (~3-10 per day)
- Total: ~10-30 writes per day
- Flash lifetime: 100k cycles / 30 writes = 3333 days = 9 years
```

**Known limitations:**
- Statistics not tested in testing mode (different build behavior)
- Flash lifetime limited by write cycles (managed by wear leveling)
- No session state recovery after power loss (intentional, see AD016)

---

## JPL Coding Standards Compliance

- ✅ Rule #1: No dynamic memory allocation - NVS uses static buffers
- ✅ Rule #2: Fixed loop bounds - NVS read/write loops bounded
- ✅ Rule #3: No recursion - Linear control flow
- ✅ Rule #4: No goto statements - Structured control flow
- ✅ Rule #5: Return value checking - All nvs_* calls wrapped in ESP_ERROR_CHECK()
- ✅ Rule #6: No unbounded waits - NVS operations have fixed timeout
- ✅ Rule #7: Watchdog compliance - NVS operations complete within watchdog timeout
- ✅ Rule #8: Defensive logging - NVS errors logged with context

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: ### AD015: NVS Storage Strategy
Git commit: [to be filled after migration]

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
