# NNNN: [Title]

**Date:** YYYY-MM-DD
**Phase:** [0.1, 1, 1b, 1b.3, 1c, 2, 3, etc.]
**Status:** Proposed | Accepted | Superseded | Deprecated | Approved
**Type:** Architecture | Build System | Security | Testing | Documentation

---

## Summary (Y-Statement)

In the context of [functional requirement/architectural component],
facing [non-functional requirement/concern/constraint],
we decided for [chosen solution],
and neglected [rejected alternative],
to achieve [primary benefit/quality attribute],
accepting that [acknowledged drawback/tradeoff].

---

## Problem Statement

[Clear articulation of what decision needs to be made and why it matters]

---

## Context

[Background forces, constraints, and information that led to this decision:
- Technical constraints (hardware, software, standards)
- Business requirements (cost, timeline, user needs)
- Team capabilities and expertise
- External dependencies or regulations]

---

## Decision

[The actual decision made - present tense, active voice]

We will [specific action/approach]...

[Implementation details, boundaries, and scope of the decision]

---

## Consequences

### Benefits

- [Concrete measurable benefit 1]
- [Positive outcome 2]
- [Advantage 3]

### Drawbacks

- [Specific tradeoff or limitation 1]
- [Resource impact or cost 2]
- [Accepted constraint 3]

---

## Options Considered

### Option A: [Name/Description]

**Pros:**
- [Advantage 1]
- [Advantage 2]

**Cons:**
- [Disadvantage 1]
- [Disadvantage 2]

**Selected:** YES | NO
**Rationale:** [Brief explanation of why chosen or rejected]

### Option B: [Name/Description]

**Pros:**
- [Advantage 1]

**Cons:**
- [Disadvantage 1]

**Selected:** YES | NO
**Rationale:** [Brief explanation]

[Add more options as needed]

---

## Related Decisions

### Supersedes
- [ADXXX: Title] - [Brief note on what this replaces]

### Superseded By
- [ADXXX: Title] - [Brief note on what replaces this]

### Related
- [ADXXX: Title] - [How they relate]
- [ADXXX: Title] - [How they relate]

---

## Implementation Notes

### Code References

- `src/filename.c` lines XXX-YYY ([brief description])
- `src/filename.h` lines XXX ([brief description])

### Build Environment

- **Environment Name:** `xiao_esp32c6` | `xiao_esp32c6_ble_no_nvs` | `single_device_*`
- **Configuration File:** `sdkconfig.xiao_esp32c6`
- **Build Flags:** [Any special compiler or linker flags]

### Testing & Verification

[How this decision was validated:]
- Hardware testing performed: [description]
- Unit tests: [if applicable]
- Integration tests: [if applicable]
- Known limitations or edge cases

---

## JPL Coding Standards Compliance

[If applicable to code-related decisions:]

- ✅ Rule #1: No dynamic memory allocation - [status/notes]
- ✅ Rule #2: Fixed loop bounds - [status/notes]
- ✅ Rule #3: No recursion - [status/notes]
- ✅ Rule #4: No goto statements - [status/notes]
- ✅ Rule #5: Return value checking - [status/notes]
- ✅ Rule #6: No unbounded waits - [status/notes]
- ✅ Rule #7: Watchdog compliance - [status/notes]
- ✅ Rule #8: Defensive logging - [status/notes]

---

## Migration Notes

[If this AD was migrated from the monolithic architecture_decisions.md:]

Migrated from `docs/architecture_decisions.md` on [DATE]
Original location: [Section reference]
Git commit: [hash]

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
