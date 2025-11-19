# EMDR Bilateral Stimulation Research Platform Features

**Last Updated:** November 11, 2025
**Project Version:** Research Platform v1.0
**Hardware:** Dual Seeed XIAO ESP32-C6
**Framework:** ESP-IDF v5.5.0 via PlatformIO

---

## Overview

This document describes the research platform capabilities of the EMDR bilateral stimulation device, which extends beyond standard therapeutic parameters to enable scientific investigation of bilateral stimulation mechanisms.

**Dual Purpose:**
1. **Clinical Tool**: Standard EMDR therapy (0.5-2 Hz, fixed patterns)
2. **Research Platform**: Extended parameters (0.25-2 Hz, multiple patterns)

---

## Research Platform Architecture

### BLE Service Structure

**Configuration Service** (Mobile App Control)
- UUID: `6E400002-B5A3-F393-E0A9-E50E24DCCA9E`
- Purpose: User interface for parameter configuration

**Bilateral Control Service** (Device-to-Device)
- UUID: `6E400001-B5A3-F393-E0A9-E50E24DCCA9E`
- Purpose: Real-time bilateral coordination

---

## Stimulation Patterns

### 1. BILATERAL_FIXED (Standard EMDR)

Traditional bilateral stimulation with fixed motor directions:

```
Time (ms)    Server Device    Client Device
0-250        FORWARD ON       OFF
250-500      OFF             REVERSE ON
500-750      FORWARD ON       OFF
750-1000     OFF             REVERSE ON
```

**Applications:**
- Standard EMDR therapy
- Baseline measurements
- Control condition

**Research Questions:**
- Optimal frequency for different conditions
- Relationship between frequency and processing speed

### 2. BILATERAL_ALTERNATING (Research Mode)

Both devices alternate motor direction each cycle:

```
Time (ms)    Server Device        Client Device
0-250        FORWARD ON          OFF
250-500      OFF                REVERSE ON
500-750      REVERSE ON         OFF
750-1000     OFF               FORWARD ON
1000-1250    FORWARD ON         OFF
1250-1500    OFF               REVERSE ON
```

**Applications:**
- Direction preference studies
- Habituation reduction research
- Motor adaptation studies

**Research Questions:**
- Does alternating direction improve outcomes?
- Impact on sensory habituation
- User preference for direction patterns

### 3. UNILATERAL (Control Studies)

Single device operation for research controls:

```
Time (ms)    Server Device    Client Device
0-250        ON              OFF (always)
250-500      OFF             OFF (always)
500-750      ON              OFF (always)
750-1000     OFF             OFF (always)
```

**Applications:**
- Control conditions
- Baseline comparisons
- Single-sided stimulation studies

**Research Questions:**
- Bilateral vs unilateral effectiveness
- Necessity of bilateral alternation
- Hemispheric processing differences

---

## Extended Parameter Ranges

### Frequency Range: 0.25-2 Hz

| Frequency | Cycle Time | Classification | Research Application |
|-----------|------------|----------------|---------------------|
| 0.25 Hz | 4000ms | Ultra-slow | Dissociative disorders, slow processing |
| 0.5 Hz | 2000ms | Slow | Standard EMDR minimum, elderly populations |
| 0.75 Hz | 1333ms | Moderate-slow | Attention disorders |
| 1.0 Hz | 1000ms | Standard | Typical therapeutic rate |
| 1.25 Hz | 800ms | Moderate-fast | Enhanced processing |
| 1.5 Hz | 667ms | Fast | Anxiety disorders |
| 1.75 Hz | 571ms | Very fast | ADHD applications |
| 2.0 Hz | 500ms | Ultra-fast | Standard EMDR maximum |

### Motor Intensity: 30-80% PWM

**Safety Constraints:**
- **Minimum 30%**: Ensures perceptible stimulation
- **Maximum 80%**: Prevents motor damage and tissue irritation

**Research Applications:**
- Sensory threshold studies (30-40%)
- Standard therapy (40-60%)
- Enhanced stimulation (60-80%)

### Duty Cycle: 10-50%

| Duty Cycle | On Time (1Hz) | Application |
|------------|---------------|-------------|
| 10% | 50ms | Micro-stimulation research |
| 15% | 75ms | Minimal effective dose studies |
| 25% | 125ms | Standard therapy (battery efficient) |
| 35% | 175ms | Enhanced stimulation |
| 50% | 250ms | Moderate duty (battery efficient) |
| 75% | 375ms | High intensity stimulation |
| 100% | 500ms | Maximum duty (uses entire ACTIVE period, respects INACTIVE period) |
n**Note:** All duty levels guarantee motor is OFF for at least 50% of total cycle time. Duty cycle is percentage of ACTIVE period only.

### Session Duration: 20-90 minutes

- **20 minutes**: Minimum research protocol
- **30 minutes**: Short therapy session
- **45 minutes**: Standard therapy session
- **60 minutes**: Extended therapy session
- **90 minutes**: Maximum research session

---

## Research Protocol Examples

### Protocol 1: Direction Preference Study

**Objective:** Determine if motor direction affects therapeutic outcome

**Design:** Within-subjects, counterbalanced

**Procedure:**
```
1. Baseline Assessment (5 min)
   - BILATERAL_FIXED at 1 Hz, 40% PWM

2. Condition A (10 min)
   - BILATERAL_FIXED pattern
   - Record subjective ratings

3. Rest Period (5 min)
   - No stimulation

4. Condition B (10 min)
   - BILATERAL_ALTERNATING pattern
   - Record subjective ratings

5. Post Assessment (5 min)
   - Compare conditions
```

### Protocol 2: Minimal Stimulation Threshold

**Objective:** Determine minimum effective stimulation parameters

**Design:** Ascending method of limits

**Procedure:**
```
1. Start: 10% duty cycle, 30% PWM, 1 Hz
2. Increment: +5% duty cycle every 5 minutes
3. Measure: Subjective perception threshold
4. Continue: Until therapeutic effect reported
5. Verify: Repeat at identified threshold
```

### Protocol 3: Frequency Optimization

**Objective:** Find optimal frequency for specific populations

**Design:** Randomized blocks

**Procedure:**
```
Day 1: 0.5 Hz (20 min)
Day 2: 1.0 Hz (20 min)
Day 3: 1.5 Hz (20 min)
Day 4: 2.0 Hz (20 min)
Day 5: 0.25 Hz (20 min) - research extension

Measure: Processing speed, subjective comfort, therapeutic outcome
```

---

## Data Collection

### Real-Time Parameters

Logged every stimulation cycle:

```c
typedef struct {
    uint32_t timestamp_ms;        // Millisecond timestamp
    uint16_t commanded_cycle_ms;  // Target cycle time
    uint16_t actual_cycle_ms;     // Measured cycle time
    uint8_t motor_intensity;      // PWM percentage (30-80)
    uint8_t duty_cycle;           // On-time percentage (10-50)
    uint8_t pattern_type;         // FIXED/ALTERNATING/UNILATERAL
    uint8_t device_role;          // SERVER/CLIENT
    uint16_t sequence_number;     // For packet loss detection
    uint8_t battery_percent;      // Battery level
    int16_t back_emf_mv;         // Motor back-EMF (if enabled)
} research_data_t;
```

### Session Metadata

Stored at session start/end:

```c
typedef struct {
    uint32_t session_id;          // Unique session identifier
    uint32_t start_time;          // Unix timestamp
    uint32_t duration_ms;         // Total session length
    uint8_t protocol_version;     // Research protocol ID
    uint16_t total_cycles;        // Number of bilateral cycles
    uint16_t packet_loss_count;   // BLE reliability metric
    uint8_t pattern_changes;      // Number of pattern switches
} session_metadata_t;
```

---

## Safety Features

### Hard Limits (Cannot Override)

- **PWM Range**: 30-80% (enforced in firmware)
- **Non-overlapping**: Devices never stimulate simultaneously
- **Emergency Stop**: 5-second button hold always active
- **Watchdog Timer**: 2-second timeout prevents lockups

### Soft Limits (User Warnings)

- **Session > 60 min**: "Extended session - confirm to continue"
- **Duty > 40%**: "High duty cycle may cause motor heating"
- **Frequency < 0.5 Hz**: "Below standard EMDR range"
- **PWM > 70%**: "High intensity - monitor for comfort"

### Research Mode Indicators

LED patterns indicate research vs clinical mode:

- **Clinical Mode**: Solid green during operation
- **Research Mode**: Pulsing blue during operation
- **Parameter Change**: Brief yellow flash
- **Safety Limit**: Red flash with warning

---

## BLE Characteristic Reference

### Bilateral Control Service Characteristics

| Characteristic | UUID Suffix | Type | Range | Access |
|---------------|-------------|------|-------|--------|
| Bilateral Command | 0101 | uint8 | 0-6 | Write |
| Total Cycle Time | 0201 | uint16 | 500-4000ms | R/W |
| Motor Intensity | 0301 | uint8 | 30-80% | R/W |
| Stimulation Pattern | 0401 | uint8 | 0-2 | R/W |
| Device Role | 0501 | uint8 | 0-2 | Read |
| Session Duration | 0601 | uint32 | 20-90 min | R/W |
| Sequence Number | 0701 | uint16 | 0-65535 | Read |
| Emergency Shutdown | 0801 | uint8 | 1 | Write |
| Duty Cycle | 0901 | uint8 | 10-50% | R/W |

---

## Implementation Status

### Completed Features
- ✅ Basic bilateral coordination (BILATERAL_FIXED)
- ✅ BLE Configuration Service
- ✅ Standard EMDR frequencies (0.5-2 Hz)
- ✅ Motor PWM control (30-90%)
- ✅ Battery monitoring
- ✅ Session timing

### In Development
- 🚧 BILATERAL_ALTERNATING pattern
- 🚧 Extended frequency range (0.25 Hz)
- 🚧 Research data logging
- 🚧 Bilateral Control Service

### Future Features
- ⏳ Real-time data streaming
- ⏳ Physiological sensor integration
- ⏳ Machine learning optimization
- ⏳ Cloud data synchronization

---

## Comparison with Clinical Standards

| Parameter | EMDR Standard | Research Platform | Rationale |
|-----------|--------------|-------------------|-----------|
| Frequency | 0.5-2 Hz | 0.25-2 Hz | Explore slow processing |
| Pattern | Fixed bilateral | Fixed/Alternating/Uni | Study mechanisms |
| Intensity | Not specified | 30-80% PWM | Safety + variability |
| Duty Cycle | Not specified | 10-50% | Energy + comfort |
| Session | 60-90 min typical | 20-90 min | Research flexibility |

---

## Research Ethics Considerations

### Required for Human Studies
1. IRB approval for research protocols
2. Informed consent with research disclosure
3. Data anonymization (no PII stored)
4. Right to withdraw from research
5. Clear clinical vs research mode indication

### Device Labeling
- "Research features are investigational"
- "Standard EMDR mode for clinical use"
- "Extended parameters for research only"

---

## Future Research Directions

### Phase 2: Sensor Integration
- Heart rate variability (HRV)
- Galvanic skin response (GSR)
- EEG correlates
- Eye tracking

### Phase 3: Closed-Loop Control
- Adaptive frequency based on HRV
- Intensity modulation via GSR
- Pattern switching on habituation
- Personalized protocols

### Phase 4: Multi-Site Studies
- Standardized research protocols
- Cloud data aggregation
- Cross-population comparisons
- Efficacy meta-analysis

### Phase 5: AI Optimization
- Machine learning parameter selection
- Predictive therapeutic outcomes
- Personalized treatment protocols
- Real-time adaptation algorithms

---

## References

1. Shapiro, F. (2001). Eye Movement Desensitization and Reprocessing (EMDR): Basic Principles, Protocols, and Procedures.

2. EMDRIA Standards: https://www.emdria.org

3. ESP-IDF Documentation: https://docs.espressif.com/projects/esp-idf/

4. NimBLE Documentation: https://mynewt.apache.org/latest/network/

---

## Contact & Contributing

**Repository:** https://github.com/lemonforest/mlehaptics
**License:** GPL v3 (Software), CERN-OHL-S v2 (Hardware)
**Research Collaboration:** Open to academic partnerships

---

**This document describes research capabilities that extend beyond standard EMDR therapy. Research features should only be used in appropriate research contexts with proper oversight and consent.**