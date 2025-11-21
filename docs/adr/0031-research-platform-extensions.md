# 0031: Research Platform Extensions

**Date:** 2025-11-11
**Phase:** Phase 1b
**Status:** Approved
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of serving dual purposes as both a clinical EMDR therapy tool and research platform,
facing the need to study bilateral stimulation parameters beyond standard EMDR ranges,
we decided to extend platform capabilities with broader frequency ranges (0.25-2 Hz), duty cycles (10-100%), and motor intensities (0-80% PWM),
and neglected limiting the device to only standard EMDR parameters (0.5-2 Hz),
to achieve comprehensive research capabilities for studying therapeutic boundaries,
accepting increased complexity in safety validation and user configuration.

---

## Problem Statement

Standard EMDR therapy uses 0.5-2 Hz bilateral stimulation, but research into optimal therapeutic parameters requires exploring extended ranges. The device must support both clinical therapy (standard parameters) and research applications (extended parameters) while maintaining safety constraints and preventing harmful operation.

---

## Context

**Background:**
- Device serves dual purpose: clinical EMDR therapy tool AND research platform
- Standard EMDR: 0.5-2 Hz frequency range
- Research requires extended ranges to explore therapeutic boundaries
- Safety constraints must prevent motor damage and user discomfort
- Single-device bilateral constraint: one motor alternates forward/reverse sequentially

**Requirements:**
- Support standard EMDR parameters for clinical use
- Enable extended parameters for research studies
- Maintain safety through hard limits
- Collect data for research analysis
- Clear distinction between therapy and research modes

---

## Decision

Extend platform capabilities beyond standard EMDR while maintaining safety constraints:

### 1. Extended Frequency Range (0.25-2 Hz vs Standard 0.5-2 Hz)

**Rationale for 0.25 Hz (4000ms cycle):**
- Explore slow bilateral processing for trauma with dissociation
- Study attention and working memory at slower rates
- Investigate relationship between stimulation rate and processing speed
- Research applications for elderly or cognitively impaired populations

**Rationale for Full 2 Hz (500ms cycle):**
- Match fastest standard EMDR rate for complete compatibility
- Study rapid bilateral stimulation effects
- Research applications for ADHD and high-arousal states

### 2. Bilateral Alternating Pattern

**Research Questions Enabled:**
- Does motor direction (forward vs reverse) affect therapeutic outcome?
- Is alternating direction more/less effective than fixed direction?
- How does direction change impact habituation?
- Can direction alternation reduce motor adaptation?

**Implementation:**
```c
// Each device alternates its own direction
typedef enum {
    RESEARCH_PATTERN_FIXED,        // Standard: Server=forward, Client=reverse
    RESEARCH_PATTERN_ALTERNATING,  // Both alternate direction each cycle
    RESEARCH_PATTERN_UNILATERAL    // Control: single device only
} research_pattern_t;
```

### 3. Duty Cycle Research (10-100%)

**Single-Device Bilateral Constraint:**
In single-device mode, one motor alternates forward/reverse in sequential half-cycles:
- **Cycle pattern:** [Forward active] → [Forward coast] → [Reverse active] → [Reverse coast]
- **Maximum 50% duty cycle** ensures adequate coast time between direction changes
- **Above 50% causes motor overlap:** Motor attempts to reverse before fully stopped

**Research Applications:**
- **10% = 50ms pulses:** Micro-stimulation studies, minimum perceptible timing pattern
- **25% = 125ms pulses:** Standard therapy baseline (4× battery life improvement)
- **50% = 250ms pulses:** Moderate bilateral stimulation
- **100% = 500ms pulses:** Maximum bilateral stimulation (motor ON entire active half-cycle)

**Important Note:** Duty cycle controls TIMING pattern (when motor/LED active), NOT motor strength. For LED-only mode (pure visual stimulation), set PWM intensity = 0% instead of duty = 0%.

**Safety Note:** Duty cycle is percentage of ACTIVE half-cycle only. Even at 100% duty, motor guaranteed OFF for 50% of total cycle time (during INACTIVE period).

### 4. Motor Intensity Research (0-80% PWM)

**Safety Rationale:**
- **0% (LED-only mode):** Disables motor vibration, maintains LED pattern (pure visual therapy)
- **10-30%:** Gentle stimulation for sensitive users
- **40-60%:** Standard therapeutic range
- **70-80%:** Strong stimulation (maximum prevents overheating and tissue irritation)
- **Research Range:** 80% variation allows comprehensive intensity studies

### 5. Session Duration Flexibility (20-90 minutes)

**Applications:**
- **20 minutes:** Minimum for research protocols
- **45 minutes:** Standard therapy session
- **60 minutes:** Extended therapy session
- **90 minutes:** Maximum research session

### 6. Data Collection Capabilities

**Logged Parameters:**
- Timestamp of each stimulation cycle
- Actual vs commanded timing (drift analysis)
- BLE packet loss rate (sequence number gaps)
- Battery voltage during session
- Motor back-EMF readings (when implemented)
- Pattern changes mid-session

**Storage Format:**
```c
typedef struct {
    uint32_t timestamp_ms;
    uint16_t cycle_time_ms;
    uint8_t motor_intensity;
    uint8_t pattern_type;
    uint8_t device_role;
    uint16_t sequence_num;
    uint8_t battery_percent;
} research_data_point_t;
```

### 7. Safety Constraints

**Hard Limits (Cannot Override):**
- PWM maximum: 80% (prevents motor damage)
- PWM minimum: 30% (ensures perception)
- Non-overlapping stimulation (safety-critical)
- Emergency shutdown always available

**Soft Limits (Configurable with Warning):**
- Session > 60 minutes: Requires confirmation
- Duty cycle > 40%: Warning about motor heating
- Frequency < 0.5 Hz: Outside standard EMDR range

---

## Consequences

### Benefits

- ✅ **Scientific Rigor:** Controlled parameter manipulation enables research studies
- ✅ **Safety Maintained:** Hard limits prevent harmful operation
- ✅ **Clinical + Research:** Dual-purpose platform maximizes device utility
- ✅ **Open Source:** Enables collaborative research across institutions
- ✅ **Data-Driven:** Built-in logging supports rigorous analysis
- ✅ **Expandable:** Architecture supports future physiological sensors

### Drawbacks

- Increased complexity in safety validation
- More extensive user configuration required for research mode
- Need for clear documentation distinguishing therapy vs research modes
- Potential for user confusion between standard and extended parameters
- Additional testing required for extended parameter ranges

---

## Options Considered

### Option A: Standard EMDR Only (0.5-2 Hz fixed)

**Pros:**
- Simple, well-validated parameter range
- Minimal safety validation needed
- Clear clinical focus

**Cons:**
- No research capabilities
- Limited scientific contribution
- Can't explore therapeutic boundaries

**Selected:** NO
**Rationale:** Eliminates primary value proposition as research platform

### Option B: Extended Parameters with Research Extensions (Selected)

**Pros:**
- Dual-purpose: therapy AND research
- Enables parameter exploration
- Scientific contribution potential
- Safety maintained through hard limits

**Cons:**
- More complex implementation
- Requires careful documentation

**Selected:** YES
**Rationale:** Best balance of clinical utility and research capability

### Option C: Unlimited Parameters

**Pros:**
- Maximum flexibility
- No artificial constraints

**Cons:**
- Safety risks (motor damage, user discomfort)
- No protection against harmful operation
- Regulatory compliance challenges

**Selected:** NO
**Rationale:** Safety risks unacceptable for therapeutic device

---

## Related Decisions

### Related
- AD028: Command-and-Control Architecture - Defines how research parameters are transmitted between devices
- AD032: BLE Configuration Service Architecture - Defines GATT characteristics for parameter control
- AD029: Time Synchronization Accuracy Requirements - Defines timing accuracy for research data collection

---

## Implementation Notes

### Code References

**Configuration Service (Mobile App Control):**
- `src/ble_manager.c` - GATT characteristics for research parameter configuration
- Custom Frequency: uint16 (25-200 = 0.25-2.0 Hz)
- Custom Duty Cycle: uint8 (10-100%)
- PWM Intensity: uint8 (0-80%, 0%=LED-only)

**Research Protocol Support:**
```c
// Example: Direction Preference Study
1. Baseline: 5 min BILATERAL_FIXED at 1 Hz
2. Condition A: 5 min BILATERAL_ALTERNATING at 1 Hz
3. Rest: 2 min no stimulation
4. Condition B: 5 min BILATERAL_FIXED reversed roles
5. Data: Compare subjective ratings and physiological measures

// Example: Minimal Stimulation Study
1. Standard: 10 min at 25% duty cycle, 1 Hz
2. Minimal: 10 min at 10% duty cycle, 1 Hz
3. Micro: 10 min at 10% duty cycle, 2 Hz
4. Data: Compare therapeutic efficacy
```

### Build Environment

- **Environment Name:** `xiao_esp32c6`
- **Configuration File:** `sdkconfig.xiao_esp32c6`
- Research features available in all production environments

### Testing & Verification

**Testing Required:**
- Extended frequency range validation (0.25 Hz, 2 Hz)
- Duty cycle safety testing (10%, 50%, 100%)
- Motor heating tests at high duty cycles
- Battery life measurement across parameter ranges
- Data logging accuracy verification
- Emergency shutdown at all parameter combinations

**Known Limitations:**
- Single-device mode limited to 50% max duty (motor reversal constraint)
- Dual-device mode supports full 10-100% duty range

---

## JPL Coding Standards Compliance

- ✅ Rule #1: No dynamic memory allocation - Research data structures statically allocated
- ✅ Rule #2: Fixed loop bounds - All data logging loops bounded
- ✅ Rule #5: Return value checking - All configuration writes validated
- ✅ Rule #7: Watchdog compliance - Timing loops feed watchdog
- ✅ Rule #8: Defensive logging - All parameter changes logged

---

## Compliance Notes

- Research features require explicit opt-in via Configuration Service
- Standard EMDR mode uses only approved parameters (0.5-2 Hz, fixed pattern)
- Research mode displays clear indication via LED patterns
- All research data is anonymous (no patient identifiers)

**Future Research Directions:**
1. **Phase 2**: Integration with physiological sensors (HR, HRV, GSR)
2. **Phase 3**: Closed-loop stimulation based on physiological feedback
3. **Phase 4**: Machine learning optimization of parameters
4. **Phase 5**: Multi-site research protocol coordination

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: AD031 (lines 2803-2966)
Git commit: TBD (migration commit)

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
