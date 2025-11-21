# 0002: JPL Institutional Coding Standard Adoption

**Date:** 2025-10-15
**Phase:** 0.1
**Status:** Accepted
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of developing safety-critical medical device firmware,
facing risks of timing errors affecting therapeutic outcomes and potential memory corruption,
we decided for implementing JPL Institutional Coding Standard for C Programming Language,
and neglected general embedded coding practices without formal safety standards,
to achieve deterministic behavior and zero dynamic allocation for long-running therapy sessions,
accepting increased code complexity and stricter development constraints.

---

## Problem Statement

Medical device software requires extremely high reliability. Bilateral stimulation timing errors could:
- Affect therapeutic efficacy (overlapping motor activation)
- Cause unpredictable behavior during 20+ minute sessions
- Lead to memory leaks or heap fragmentation
- Result in silent failures without error detection

We need a formal coding standard that provides:
- Predictable memory behavior (no heap fragmentation)
- Deterministic execution (no unbounded recursion)
- Comprehensive error detection
- Verifiable safety properties

---

## Context

### Medical Device Requirements
- **Bilateral timing**: ±10ms precision over 20+ minute sessions
- **Safety-critical**: Motor activation errors affect therapy effectiveness
- **Long-running**: Sessions must maintain stability without memory degradation
- **Embedded constraints**: 512KB SRAM, no runtime memory allocation

### Regulatory Context
- Open-source medical device (not FDA-approved)
- Research platform for studying EMDR therapy
- Commitment to safety-critical software practices
- Need for auditable code quality

### Team Capabilities
- Single developer (Claude AI assistance)
- Embedded systems expertise
- Focus on verifiable safety properties

---

## Decision

We will implement the **JPL Institutional Coding Standard** for all safety-critical code in this project.

### Core JPL Rules Applied

1. **No dynamic memory allocation** (malloc/calloc/realloc/free)
   - All data structures statically allocated at compile time
   - Prevents heap fragmentation during long therapy sessions

2. **No recursion** in any function
   - Ensures predictable, bounded stack usage
   - Simplifies worst-case execution time analysis

3. **Limited function complexity** (cyclomatic complexity ≤ 10)
   - Improves code review effectiveness
   - Reduces hidden state and edge cases

4. **All functions return error codes** (`esp_err_t`)
   - Forces explicit error handling at every call site
   - Prevents silent failures

5. **Single entry/exit points** for all functions
   - Simplifies reasoning about function behavior
   - Enables easier formal verification

6. **Comprehensive parameter validation**
   - All function inputs validated before use
   - Fail fast with clear error codes

7. **No goto statements** (except error cleanup paths)
   - Reduces spaghetti code and hidden control flow
   - Exception for cleanup-only goto patterns

8. **All variables explicitly initialized**
   - Prevents undefined behavior
   - Makes code behavior deterministic

---

## Consequences

### Benefits

- **Medical device safety**: Formal standard demonstrates commitment to safety-critical practices
- **Zero memory leaks**: Static allocation prevents heap fragmentation in long sessions
- **Predictable execution**: No recursion ensures deterministic stack usage
- **Error resilience**: Comprehensive checking prevents silent failures
- **Code review efficiency**: Complexity limits make code easier to audit
- **Regulatory compliance**: Provides documented safety approach for research platform
- **Stack analysis**: Bounded stack usage enables worst-case analysis

### Drawbacks

- **Increased code complexity**: Error checking adds boilerplate to every function
- **Development overhead**: Static allocation requires upfront sizing decisions
- **Learning curve**: Developers must understand and follow JPL rules
- **Flexibility reduction**: Some algorithms harder to implement without dynamic allocation
- **Verbose code**: Explicit initialization and error checks increase line count

---

## Options Considered

### Option A: JPL Institutional Coding Standard

**Pros:**
- Proven in spacecraft and safety-critical systems
- Zero dynamic allocation prevents memory issues
- Comprehensive error handling requirements
- Verifiable safety properties
- Well-documented standard

**Cons:**
- Increased code verbosity
- Steeper learning curve
- Requires disciplined adherence

**Selected:** YES
**Rationale:** Only option providing formal safety guarantees suitable for medical device software

### Option B: MISRA C Standard

**Pros:**
- Industry standard for automotive/medical
- Comprehensive rule set (>140 rules)
- Tool support for automated checking

**Cons:**
- More complex than JPL (harder to verify compliance)
- Some rules not applicable to ESP-IDF
- Less focus on embedded real-time systems

**Selected:** NO
**Rationale:** JPL standard more appropriate for embedded real-time systems with FreeRTOS

### Option C: BARR-C Embedded C Coding Standard

**Pros:**
- Designed specifically for embedded systems
- Good practices for microcontroller development
- Less restrictive than JPL

**Cons:**
- No formal verification methodology
- Less stringent safety requirements
- Not as widely recognized as JPL/MISRA

**Selected:** NO
**Rationale:** Insufficient safety guarantees for medical device application

### Option D: General Embedded Best Practices (No Formal Standard)

**Pros:**
- Maximum flexibility
- Faster development
- No compliance overhead

**Cons:**
- No verifiable safety properties
- Ad-hoc error handling patterns
- Harder to audit code quality
- Insufficient for medical device software

**Selected:** NO
**Rationale:** Cannot demonstrate safety commitment without formal standard

---

## Related Decisions

### Related
- [AD001: ESP-IDF v5.5.0 Framework Selection](0001-esp-idf-v5-5-0-framework-selection.md) - ESP-IDF APIs used in JPL-compliant patterns
- [AD003: C Language Selection](0003-c-language-selection.md) - JPL standard is C-specific
- [AD006: Bilateral Cycle Time Architecture](0006-bilateral-cycle-time-architecture.md) - Timing implementation uses JPL-compliant delays
- [AD007: FreeRTOS Task Architecture](0007-freertos-task-architecture.md) - Task patterns follow JPL rules

---

## Implementation Notes

### Code References

All source files implement JPL patterns:
- `src/motor_task.c` - Static allocation, error checking, no recursion
- `src/ble_manager.c` - Bounded loops, explicit error handling
- `src/button_task.c` - State machine without goto statements
- `test/single_device_demo_jpl_queued.c` - Phase 0.4 JPL-compliant reference

### Verification Strategy

**Static Analysis:**
- Automated complexity analysis for all functions (target: cyclomatic complexity ≤ 10)
- Stack usage analysis with defined limits
- No malloc/free calls in codebase

**Code Review Checklist:**
- [ ] No dynamic memory allocation
- [ ] No recursion
- [ ] All return values checked
- [ ] All parameters validated
- [ ] Single entry/exit points
- [ ] Variables explicitly initialized
- [ ] No goto (except error cleanup)
- [ ] Cyclomatic complexity ≤ 10

**Build System Integration:**
- Compiler warnings set to maximum (`-Wall -Wextra`)
- Static analysis tools configured for JPL compliance
- Pre-commit hooks for automated checking

### Testing & Verification

**JPL Compliance Verified:**
- ✅ Phase 0.4 (`single_device_demo_jpl_queued.c`) - Full JPL compliance demonstrated
- ✅ Phase 1c modular architecture - JPL patterns in all tasks
- ✅ Stack watermark logging - No stack overflows observed
- ✅ 20+ minute sessions - No memory degradation

**Known Limitations:**
- ESP-IDF framework itself may not be JPL-compliant (uses malloc internally)
- NimBLE stack uses dynamic allocation (acceptable as external dependency)
- Focus on application code JPL compliance, not framework internals

---

## JPL Coding Standards Compliance

This decision ESTABLISHES the JPL compliance framework for the project:

- ✅ Rule #1: No dynamic memory allocation - All application structures statically allocated
- ✅ Rule #2: Fixed loop bounds - All loops have deterministic termination
- ✅ Rule #3: No recursion - No recursive function calls in application code
- ✅ Rule #4: No goto statements - State machines replace goto (exception: error cleanup)
- ✅ Rule #5: Return value checking - ESP_ERROR_CHECK() wrapper for all ESP-IDF calls
- ✅ Rule #6: No unbounded waits - All FreeRTOS delays have timeouts
- ✅ Rule #7: Watchdog compliance - TWDT subscription with 1ms dead time feeding
- ✅ Rule #8: Defensive logging - Comprehensive ESP_LOGI() for debugging

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: AD002 (Development Platform and Framework Decisions)
Git commit: Current working tree

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
