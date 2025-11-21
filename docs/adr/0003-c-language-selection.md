# 0003: C Language Selection (No C++)

**Date:** 2025-10-15
**Phase:** 0.1
**Status:** Accepted
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of implementing safety-critical medical device firmware,
facing requirements for predictable memory layout and deterministic execution,
we decided for pure C language (no C++ features),
and neglected C++ and mixed C/C++ approaches,
to achieve predictable behavior aligned with JPL coding standard and ESP-IDF native APIs,
accepting the loss of object-oriented abstraction and C++ standard library features.

---

## Problem Statement

The firmware requires:
- Predictable memory layout for safety analysis
- Deterministic execution timing for bilateral stimulation
- Alignment with JPL Institutional Coding Standard (C-specific)
- Simple code review for single-developer project
- Native compatibility with ESP-IDF APIs

C++ introduces hidden complexity:
- Constructor/destructor overhead affects timing
- Exception handling complicates control flow
- Virtual functions add indirection and memory overhead
- Template instantiation can bloat binary size

---

## Context

### Technical Constraints
- **ESP-IDF framework**: Native APIs are C-based (`esp_err_t`, FreeRTOS, NimBLE)
- **Real-time timing**: ±10ms bilateral precision requires predictable execution
- **Memory constraints**: 512KB SRAM with static allocation only
- **JPL compliance**: JPL coding standard is C-specific

### Project Characteristics
- Single-developer project (no large team requiring OOP structure)
- Embedded firmware (not application software)
- Safety-critical medical device
- Code review priority over abstraction

### C++ Considerations
- **Hidden overhead**: Constructors/destructors run at non-obvious times
- **Exception handling**: Adds code size and unpredictable control flow
- **Virtual functions**: Add vtable indirection and memory overhead
- **Templates**: Can bloat binary size with multiple instantiations

---

## Decision

We will use **pure C language** exclusively, with **no C++ features**.

### Implementation Guidelines

1. **File Extensions:**
   - All source files use `.c` extension
   - All headers use `.h` extension with C guards

2. **Header Guards:**
```c
#ifndef COMPONENT_NAME_H
#define COMPONENT_NAME_H

#ifdef __cplusplus
extern "C" {
#endif

/* C declarations */

#ifdef __cplusplus
}
#endif

#endif /* COMPONENT_NAME_H */
```

3. **Function Prototypes:**
   - Explicit function prototypes for all APIs
   - No function overloading (C doesn't support it)
   - Use descriptive names with namespacing prefixes

4. **Data Structures:**
   - Static allocation for all structures
   - Explicit initialization functions instead of constructors
   - No classes or inheritance

5. **ESP-IDF Integration:**
   - Direct use of C APIs (no C++ wrappers)
   - FreeRTOS C API (not C++ task wrapper)
   - NimBLE C API (not ESP-IDF C++ BLE wrapper)

---

## Consequences

### Benefits

- **JPL alignment**: JPL coding standard is C-specific, full compliance achievable
- **Predictable behavior**: No hidden constructors/destructors affecting timing
- **ESP-IDF compatibility**: Native C API usage, no wrapper overhead
- **Code review simplicity**: Easier verification for safety-critical code
- **Real-time guarantees**: No hidden overhead affecting bilateral timing
- **Deterministic memory**: No virtual function tables, exception handling structures
- **Binary size**: Smaller Flash footprint without C++ runtime
- **Learning curve**: Standard C is widely understood

### Drawbacks

- **No OOP abstraction**: Cannot use classes, inheritance, polymorphism
- **Manual memory management patterns**: No RAII (Resource Acquisition Is Initialization)
- **No templates**: Type-generic code requires manual duplication or macros
- **No STL**: Cannot use standard containers (vector, map, etc.)
- **Verbose error handling**: Manual error checking vs. exception handling
- **Code organization**: Namespacing via prefixes instead of namespaces/classes

---

## Options Considered

### Option A: Pure C Language

**Pros:**
- JPL coding standard alignment (C-specific)
- Predictable memory layout and execution
- Native ESP-IDF API compatibility
- Simpler code review for safety-critical code
- No hidden overhead (constructors, vtables, exceptions)

**Cons:**
- No object-oriented abstraction
- Manual resource management patterns
- Type-generic code requires duplication

**Selected:** YES
**Rationale:** Best fit for safety-critical embedded firmware with JPL compliance requirements

### Option B: Pure C++

**Pros:**
- Object-oriented abstraction
- RAII for resource management
- Templates for type-generic code
- STL containers

**Cons:**
- Hidden overhead (constructors, destructors, vtables)
- Exception handling complicates control flow
- JPL standard is C-specific (no formal C++ compliance)
- ESP-IDF C APIs would need C++ wrappers
- Larger binary size with C++ runtime

**Selected:** NO
**Rationale:** Hidden complexity unacceptable for safety-critical timing and JPL compliance

### Option C: Mixed C/C++ (C++ with extern "C")

**Pros:**
- Can use C++ for non-critical components
- ESP-IDF C APIs accessible via extern "C"
- Some object-oriented abstraction

**Cons:**
- Complexity of mixing paradigms
- Unclear boundary between C and C++ code
- Still requires C++ runtime overhead
- Harder to maintain consistent coding standard
- Complicates JPL compliance verification

**Selected:** NO
**Rationale:** Mixed paradigms add complexity without sufficient benefits for this project

### Option D: Arduino C++ Framework

**Pros:**
- High-level C++ abstractions
- Large library ecosystem
- Easier learning curve for beginners

**Cons:**
- Insufficient real-time guarantees
- Hidden timing overhead
- Not suitable for safety-critical medical device
- See AD001 for full Arduino rejection rationale

**Selected:** NO
**Rationale:** See AD001 - Arduino framework rejected for safety-critical requirements

---

## Related Decisions

### Related
- [AD001: ESP-IDF v5.5.0 Framework Selection](0001-esp-idf-v5-5-0-framework-selection.md) - ESP-IDF is C-based framework
- [AD002: JPL Institutional Coding Standard Adoption](0002-jpl-coding-standard-adoption.md) - JPL standard is C-specific
- [AD007: FreeRTOS Task Architecture](0007-freertos-task-architecture.md) - Uses FreeRTOS C API

---

## Implementation Notes

### Code References

All source files demonstrate pure C implementation:
- `src/motor_task.c` - C task with explicit initialization
- `src/ble_manager.c` - C API for NimBLE stack
- `src/button_task.c` - C state machine
- `test/single_device_demo_jpl_queued.c` - Pure C reference implementation

### Build Environment

- **Compiler:** `riscv32-esp-elf-gcc` (C compiler)
- **File Extensions:** All source files `.c`, headers `.h`
- **Build Flags:** No C++ specific flags
- **Linker:** No C++ runtime libraries

### Code Patterns

**Initialization instead of constructors:**
```c
// C pattern (no constructors)
typedef struct {
    uint32_t frequency_hz;
    uint8_t duty_cycle_percent;
} motor_config_t;

esp_err_t motor_init(motor_config_t *config) {
    if (config == NULL) return ESP_ERR_INVALID_ARG;
    // Explicit initialization
    config->frequency_hz = 1000;
    config->duty_cycle_percent = 25;
    return ESP_OK;
}
```

**Manual resource management:**
```c
// Explicit cleanup function (instead of RAII destructor)
void motor_cleanup(void) {
    motor_coast();
    ledc_stop(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, 0);
    ledc_stop(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_1, 0);
}
```

**Namespacing via prefixes:**
```c
// motor_* prefix for motor module functions
esp_err_t motor_init(void);
esp_err_t motor_set_direction_intensity(motor_direction_t dir, uint8_t intensity);
void motor_coast(void);

// ble_* prefix for BLE module functions
esp_err_t ble_init(void);
bool ble_is_peer_connected(void);
```

### Testing & Verification

**C Compliance Verified:**
- ✅ All source files compile with C compiler (no C++ required)
- ✅ No C++ keywords used (class, namespace, template, etc.)
- ✅ No C++ standard library includes
- ✅ All ESP-IDF C APIs used directly

**Known Issues:**
- None - pure C implementation successful

---

## JPL Coding Standards Compliance

- ✅ Rule #1: No dynamic memory allocation - C allows static allocation patterns
- ✅ Rule #2: Fixed loop bounds - C for-loops with compile-time bounds
- ✅ Rule #3: No recursion - C functions are non-recursive
- ✅ Rule #4: No goto statements - C state machines replace goto
- ✅ Rule #5: Return value checking - C return codes explicitly checked
- ✅ Rule #8: Defensive logging - C printf-style logging via ESP_LOGI

Pure C enables straightforward JPL compliance without C++ complications.

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: AD003 (Development Platform and Framework Decisions)
Git commit: Current working tree

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
