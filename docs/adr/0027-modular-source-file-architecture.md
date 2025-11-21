# 0027: Modular Source File Architecture

**Date:** 2025-11-08
**Phase:** 1
**Status:** Accepted
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of scaling from monolithic single-file tests to production dual-device implementation,
facing code reuse challenges and maintenance complexity,
we decided for hybrid task-based + functional modular architecture,
and neglected pure functional or pure task-based approaches,
to achieve clear separation of concerns with single-device/dual-device as state not separate code,
accepting increased initial setup complexity for long-term maintainability.

---

## Problem Statement

Current code organization uses monolithic single-file test programs:
- `test/single_device_demo_jpl_queued.c` - Phase 0.4 JPL-compliant (all code in one file)
- `test/single_device_ble_gatt_test.c` - BLE GATT server (all code in one file)
- Difficult to maintain as features grow
- Code reuse between single-device and dual-device modes challenging
- Clear separation of concerns needed for safety-critical development

---

## Context

**Current Architecture:**
- Single-file test programs proven effective for hardware validation
- BLE GATT test demonstrated task-based state machines work well
- Need to scale to production dual-device bilateral stimulation
- JPL coding standards must be maintained

**Requirements:**
- Clear module boundaries for safety-critical development
- Code reuse between single-device and dual-device modes
- Single-device vs dual-device should be STATE, not separate code paths
- Maintain FreeRTOS task structure (proven in BLE GATT test)
- Support both task modules (own FreeRTOS tasks) and functional modules (reusable components)

---

## Decision

We will implement a hybrid task-based + functional modular architecture for production dual-device implementation.

**File Structure:**

```
src/
├── main.c                      # app_main(), initialization, task creation
├── motor_task.c/h              # Motor control task (FreeRTOS task)
├── ble_task.c/h                # BLE advertising/connection task
├── button_task.c/h             # Button monitoring task
├── battery_monitor.c/h         # Battery voltage/percentage (support)
├── nvs_manager.c/h             # NVS read/write/clear (support)
├── power_manager.c/h           # Light sleep/deep sleep config (support)
└── led_control.c/h             # WS2812B + GPIO15 LED control (support)

include/
├── motor_task.h                # Public motor task interface
├── ble_task.h                  # Public BLE task interface
├── button_task.h               # Public button task interface
├── battery_monitor.h           # Public battery monitor interface
├── nvs_manager.h               # Public NVS manager interface
├── power_manager.h             # Public power manager interface
└── led_control.h               # Public LED control interface
```

**Module Responsibilities:**

**Task Modules (FreeRTOS Tasks):**

**motor_task.c/h:**
- Owns motor control FreeRTOS task
- Implements bilateral stimulation timing (server/client coordination)
- Single-device mode (forward/reverse alternating)
- Role-based behavior: SERVER, CLIENT, STANDALONE (state variable)
- Message queue for mode changes, BLE commands, shutdown
- Calls: battery_monitor (LVO check), led_control (therapy light), power_manager (sleep)

**ble_task.c/h:**
- Owns BLE FreeRTOS task
- NimBLE stack initialization and management
- Advertising lifecycle (IDLE → ADVERTISING → CONNECTED → SHUTDOWN)
- Role assignment and automatic recovery ("survivor becomes server")
- GATT server (optional, for mobile app configuration)
- Calls: nvs_manager (pairing data), motor_task (via message queue)

**button_task.c/h:**
- Owns button monitoring FreeRTOS task
- Button hold duration tracking (5s shutdown, 10s NVS clear)
- Emergency shutdown coordination (fire-and-forget)
- Deep sleep entry with wait-for-release pattern (AD023)
- Calls: motor_task (shutdown message), ble_task (shutdown message), nvs_manager (clear), led_control (purple blink), power_manager (deep sleep)

**Support Modules (Functional Components):**

**battery_monitor.c/h:**
- Battery voltage reading via ADC
- Percentage calculation (4.2V → 3.0V range)
- LVO detection (< 3.0V cutoff)
- Called by: motor_task (startup LVO check, periodic monitoring)

**nvs_manager.c/h:**
- NVS namespace management
- Pairing data storage (peer MAC address)
- Settings storage (Mode 5 custom parameters)
- Factory reset (clear all NVS data)
- Called by: ble_task (pairing), motor_task (settings), button_task (clear)

**power_manager.c/h:**
- Light sleep configuration (esp_pm_configure)
- Deep sleep entry (esp_deep_sleep_start)
- Wake source configuration (ext1 button wake)
- Called by: main.c (init), button_task (deep sleep)

**led_control.c/h:**
- WS2812B RGB LED control (if translucent case)
- GPIO15 status LED control (always available)
- Therapy light patterns (purple blink, mode indication)
- Called by: motor_task (therapy patterns), button_task (purple blink), main.c (boot sequence)

**Key Design Principle: Single-Device vs Dual-Device as State:**

```c
// motor_task.c
typedef enum {
    MOTOR_ROLE_SERVER,      // Dual-device: server role (first half-cycle)
    MOTOR_ROLE_CLIENT,      // Dual-device: client role (second half-cycle)
    MOTOR_ROLE_STANDALONE   // Single-device: forward/reverse alternating
} motor_role_t;

static motor_role_t current_role = MOTOR_ROLE_STANDALONE;  // Start standalone

// Same motor_task code handles all three roles
void motor_task(void *arg) {
    while (session_active) {
        switch (current_role) {
            case MOTOR_ROLE_SERVER:
                // Execute server half-cycle, wait client half-cycle
                break;
            case MOTOR_ROLE_CLIENT:
                // Wait server half-cycle, execute client half-cycle
                break;
            case MOTOR_ROLE_STANDALONE:
                // Forward half-cycle, reverse half-cycle
                break;
        }
    }
}
```

**Module Dependencies:**
```
main.c
  ├─> motor_task ──> battery_monitor
  │                ├─> led_control
  │                └─> power_manager
  ├─> ble_task ────> nvs_manager
  │                └─> motor_task (message queue)
  └─> button_task ─> motor_task (message queue)
                    ├─> ble_task (message queue)
                    ├─> nvs_manager
                    ├─> led_control
                    └─> power_manager
```

**Message Queue Communication:**
```c
// motor_task.h
typedef enum {
    MOTOR_MSG_MODE_CHANGE,
    MOTOR_MSG_EMERGENCY_SHUTDOWN,
    MOTOR_MSG_BLE_CONNECTED,
    MOTOR_MSG_BLE_DISCONNECTED,
    MOTOR_MSG_ROLE_CHANGE
} motor_msg_type_t;

extern QueueHandle_t motor_msg_queue;
```

---

## Consequences

### Benefits

- **Maintainability:** Clear module boundaries, easier code navigation
- **Reusability:** Support modules shared across tasks
- **Testability:** Modules testable independently
- **Proven structure:** Mirrors successful BLE GATT test implementation
- **Unified behavior:** Single-device vs dual-device as state, not separate code
- **API alignment:** Module names match API contracts (clear documentation)
- **Migration path:** Incremental refactoring from monolithic test files
- **JPL compliant:** All standards maintained throughout modular architecture

### Drawbacks

- **Initial complexity:** More files to manage than monolithic approach
- **Build system changes:** CMakeLists.txt must list all source files
- **Testing overhead:** Need integration tests across modules
- **Learning curve:** Developers must understand module boundaries

---

## Options Considered

### Option A: Pure Functional (No Task Modules)

**Pros:**
- All modules are reusable functions
- Simple dependency management

**Cons:**
- Doesn't mirror FreeRTOS task structure
- Harder to map to existing BLE GATT test code
- Task ownership unclear (who owns motor_task function?)

**Selected:** NO
**Rationale:** FreeRTOS task structure proven effective in BLE GATT test

### Option B: Pure Task-Based (All Modules Are Tasks)

**Pros:**
- Every module has dedicated task
- Clear ownership

**Cons:**
- Battery monitor doesn't need dedicated task
- NVS manager doesn't need dedicated task
- Wastes FreeRTOS resources (stack per task)

**Selected:** NO
**Rationale:** Unnecessary resource consumption for support modules

### Option C: Monolithic with #ifdef SINGLE_DEVICE / DUAL_DEVICE

**Pros:**
- Single file per functionality
- No module boundaries to manage

**Cons:**
- Maintenance nightmare (two code paths)
- Violates "single-device shouldn't deviate from dual-device" requirement
- Harder testing (need to test both #ifdef paths)

**Selected:** NO
**Rationale:** Poor maintainability and testing complexity

### Option D: Hybrid Task + Functional (CHOSEN)

**Pros:**
- Best of both worlds
- Task modules map 1:1 to FreeRTOS tasks
- Support modules reusable across tasks
- Matches proven BLE GATT test structure
- Single-device vs dual-device as state (not separate code)

**Cons:**
- Initial setup complexity
- More files to manage

**Selected:** YES
**Rationale:** Best balance of maintainability, reusability, and proven effectiveness

---

## Related Decisions

### Related
- **AD022: ESP-IDF Build System** - CMakeLists.txt naturally supports multiple source files
- **AD027: Modular Architecture** - This decision implements the modular structure
- BLE GATT test (`test/single_device_ble_gatt_test.c`) provided proof-of-concept for task-based structure

---

## Implementation Notes

### Code References

- **Production Source:** `src/main.c`, `src/motor_task.c`, `src/ble_task.c`, `src/button_task.c`
- **Support Modules:** `src/battery_monitor.c`, `src/nvs_manager.c`, `src/power_manager.c`, `src/led_control.c`
- **Test Baseline:** `test/single_device_demo_jpl_queued.c` (monolithic reference)

### Build Environment

- **Environment Name:** `xiao_esp32c6`
- **Configuration File:** `sdkconfig.xiao_esp32c6`
- **CMake Integration:**

```cmake
# src/CMakeLists.txt
idf_component_register(
    SRCS
        "main.c"
        "motor_task.c"
        "ble_task.c"
        "button_task.c"
        "battery_monitor.c"
        "nvs_manager.c"
        "power_manager.c"
        "led_control.c"
    INCLUDE_DIRS
        "."
        "include"
    REQUIRES
        nvs_flash
        esp_adc
        driver
        led_strip
)
```

### Testing & Verification

**Migration Path from Monolithic Test Files:**

**Phase 1: Extract Support Modules**
1. Create battery_monitor.c/h from BLE GATT test battery code
2. Create nvs_manager.c/h from NVS storage code
3. Create power_manager.c/h from sleep management code
4. Create led_control.c/h from WS2812B + GPIO15 code
5. Test: Verify support modules work independently

**Phase 2: Extract Task Modules**
1. Create motor_task.c/h from motor_task function + state machine
2. Create ble_task.c/h from ble_task function + NimBLE init
3. Create button_task.c/h from button_task function + state machine
4. Test: Verify tasks communicate via message queues

**Phase 3: Create Main**
1. Create main.c with app_main()
2. Initialize all modules
3. Create FreeRTOS tasks
4. Test: Full system integration

**Test Strategy Preserved:**

Test files remain monolithic for hardware validation:
- `test/single_device_demo_jpl_queued.c` - Baseline JPL compliance test
- `test/single_device_ble_gatt_test.c` - BLE GATT hardware validation
- `test/battery_voltage_test.c` - Battery monitoring validation

Production code uses modular architecture:
- `src/main.c` + task/support modules

**Verification Strategy:**
- Extract battery_monitor module first (simplest, most isolated)
- Verify API compatibility with existing test code
- Incrementally migrate other modules
- Maintain test files as monolithic validation baseline
- Compare production modular build vs test monolithic build (behavior identical)

---

## JPL Coding Standards Compliance

- ✅ Rule #1: No dynamic memory allocation - All static/stack allocation
- ✅ Rule #2: Fixed loop bounds - All while loops have exit conditions
- ✅ Rule #3: No recursion - Linear module interactions
- ✅ Rule #5: Return value checking - ESP_ERROR_CHECK wrapper throughout
- ✅ Rule #6: No unbounded waits - vTaskDelay() for all timing
- ✅ Rule #7: Watchdog compliance - Task-level subscription
- ✅ Rule #8: Defensive logging - ESP_LOGI throughout

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: AD027
Git commit: (phase 1 implementation)

**API Contract Alignment:**

Module filenames mirror API contracts in `docs/ai_context.md`:
- Motor Control API → `motor_task.c/h`
- BLE Manager API → `ble_task.c/h`
- Button Handler API → `button_task.c/h`
- Battery Monitor API → `battery_monitor.c/h`
- Power Manager API → `power_manager.c/h`
- Therapy Light API → `led_control.c/h` (renamed from "therapy_light" for brevity)

**Header File Strategy:**

Single public header per module:
- motor_task.h - Public functions, message queue handles, enums
- motor_task.c - Private static functions, task implementation
- No `_private.h` headers needed (use `static` for private functions)

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
