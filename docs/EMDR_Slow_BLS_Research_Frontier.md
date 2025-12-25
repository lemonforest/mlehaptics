# EMDR Bilateral Stimulation: The Slow Frequency Research Frontier

## Addendum to Evidence-Based Parameters Report

---

## The Undefined "Slow": A Gap in EMDR Research

Clinical EMDR guidance consistently distinguishes between "fast" bilateral stimulation for trauma processing and "slow" bilateral stimulation for resourcing, stabilization, and relaxation. However, **"slow" is never defined in Hz**.

### What the literature actually says:

| Source | Guidance | Frequency Specified? |
|--------|----------|---------------------|
| Shapiro (2018) | "Slower and shorter sets for resource installation" | No |
| PMC/Frontiers (2021) | "Speed of BLS in resource installation procedures is in general slow" | No |
| EMDR Solutions (2020) | "Slow eye movements or hand taps in short sets (4-6 passes) for RDI" | No |
| Practitioner app guidance | "1.1 to 1.7 seconds between taps for calm place" | **Implied 0.6-0.9 Hz** |

The closest specification found in clinical literature translates to approximately **0.6-0.9 Hz** for resourcing—but this is practitioner convention, not peer-reviewed research. **No RCT has compared different slow frequencies against each other.**

---

## Theoretical Rationale for Sub-0.5 Hz Bilateral Stimulation

### 1. Brainwave Entrainment Alignment

The brain naturally oscillates at frequencies that map to specific states:

| Band | Frequency | State | BLS Rate to Entrain |
|------|-----------|-------|---------------------|
| **Delta** | 0.5–4 Hz | Deep sleep, healing | 0.5–2 Hz (standard EMDR) |
| **Slow oscillation** | <1 Hz | Memory consolidation | 0.5–1 Hz |
| **Infraslow** | <0.1 Hz | Brain state modulation | 0.01–0.1 Hz |

Standard EMDR processing (1 Hz) targets delta-band entrainment. **Sub-0.5 Hz BLS may target deeper restorative states**—the slow oscillation and infraslow bands associated with profound relaxation and healing.

### 2. Cardiac Coherence Resonance

A substantial body of research documents that breathing at **0.1 Hz (6 breaths/minute)** produces "cardiac coherence"—a state where heart rate variability becomes highly ordered, vagal tone increases, and parasympathetic activation dominates.

Key findings from cardiac coherence research:

- **0.1 Hz = "resonance frequency"**: Breathing at this rate maximizes heart-brain coherence and vagal tone
- Coherence at 0.1 Hz produces "improved vagally-mediated heart rate variability and baroreflex sensitivity"
- Training at 0.1 Hz "improves CO2 homeostasis and relaxation"

**Critical finding**: A 2025 study of 1.8 million HRV biofeedback sessions found that while 0.1 Hz was most common, **users with the highest coherence scores often fell in the 0.04–0.10 Hz range**:

> "The relatively high average coherence scores at these lower frequencies may indicate that these users are achieving a more stable and relaxed physiological state at these lower frequencies."

This suggests **individual variation in optimal resonance frequency**, with some people achieving deeper states at frequencies below 0.1 Hz.

### 3. Breathing Rhythm Synchronization

Bilateral stimulation frequency can synchronize with breathing patterns:

| BLS Frequency | Cycle Duration | Breathing Equivalent |
|---------------|----------------|---------------------|
| 1 Hz | 1 second | Too fast for breathing sync |
| 0.5 Hz | 2 seconds | Rapid breathing (30/min) |
| **0.25 Hz** | **4 seconds** | **Normal relaxed breathing (15/min)** |
| **0.1 Hz** | **10 seconds** | **Deep breathing / cardiac coherence (6/min)** |
| 0.05 Hz | 20 seconds | OM chanting / pranayama (3/min) |
| 0.01 Hz | 100 seconds | Infraslow meditation cycles |

At **0.25 Hz**, bilateral stimulation naturally aligns with relaxed breathing rhythms. At **0.1 Hz**, it aligns with the cardiac coherence "sweet spot." This may explain practitioner observations that slower BLS feels "more relaxing."

### 4. Slow Oscillation and Memory

The brain's **slow oscillation (<1 Hz)** is critical for memory consolidation during sleep. EMDR's proposed mechanism involves reprocessing traumatic memories. The slow oscillation:

- Synchronizes firing patterns in large neuronal populations
- Drives memory consolidation from hippocampus to neocortex
- Facilitates the "depotentiation" (weakening) of traumatic memory traces

Bilateral stimulation at 0.5–1 Hz may be mimicking slow-wave sleep mechanisms. **Slower BLS (0.1–0.5 Hz) may access even deeper consolidation processes.**

---

## The Infraslow Frontier: 0.01–0.1 Hz

### What neuroscience says about infraslow oscillations:

Infraslow oscillations (ISOs) at <0.1 Hz are an active research area:

- Found in thalamus, cortex, and distributed brain networks
- Associated with "brain state modulation" and "excitability cycling"
- Present during deep sleep, meditation, and spiritual experiences
- One study linked delta wave activity with reported spiritual experiences during meditation

The **Cyclic Alternating Pattern (CAP)** in sleep has a periodicity of ~20-40 seconds (0.025–0.05 Hz)—directly in your proposed range.

### Ultra-slow breathing research:

OM chanting at approximately **0.05 Hz (3 cycles/minute)** has been studied:

> "OM chanting induces slow breathing at approximately 3 cycles per minute. This breathing rate is considerably slower than breathing at 6 cycles per minute which is often associated to 'slow breathing.' It leads to a strong coordination and interaction of cardiovascular oscillations with respiration, involving central and peripheral neural networks."

This demonstrates that **rhythmic stimulation below 0.1 Hz has documented physiological effects**.

---

## Proposed Frequency Taxonomy for EMDR Devices

Based on the research gaps and theoretical rationale, here is a proposed taxonomy for bilateral stimulation frequencies:

| Category | Frequency Range | Primary Use | Evidence Level |
|----------|-----------------|-------------|----------------|
| **Standard Processing** | 1–2 Hz | Trauma desensitization, Phase 4 reprocessing | High (EMDRIA standard) |
| **Moderate Processing** | 0.5–1 Hz | Lighter processing, sensitive clients | Moderate (clinical practice) |
| **Standard Resourcing** | 0.5–0.75 Hz | Resource installation, calm place | Low (convention, not researched) |
| **Deep Resourcing** | 0.25–0.5 Hz | Extended stabilization, profound relaxation | **Research frontier** |
| **Cardiac Coherence Zone** | 0.08–0.12 Hz | Vagal activation, HRV optimization | **Moderate (HRV research, not EMDR)** |
| **Infraslow Exploration** | 0.01–0.08 Hz | Meditative states, experimental | **Low (neuroscience, not clinical)** |

---

## Device Implementation Recommendations

### For clinicians:

1. **0.5–2 Hz**: Standard EMDRIA-aligned range; safe for all applications
2. **0.25–0.5 Hz**: Reasonable extension for resourcing; theoretical support, limited clinical data
3. **0.1–0.25 Hz**: Cardiac coherence alignment; may enhance relaxation; mark as "experimental" or "research"
4. **<0.1 Hz**: Infraslow range; insufficient clinical data; mark clearly as "research only"

### For device developers:

Consider implementing frequency ranges with clear labeling:

```
FREQUENCY PRESETS:
├── EMDRIA Standard (0.5–2.0 Hz)
│   ├── Processing: 1.0–2.0 Hz
│   └── Resourcing: 0.5–1.0 Hz
├── Extended Range (0.1–0.5 Hz)
│   ├── Deep Resourcing: 0.25–0.5 Hz
│   └── Cardiac Coherence: 0.08–0.12 Hz
└── Research/Experimental (<0.1 Hz)
    ├── Infraslow: 0.01–0.1 Hz
    └── Custom: User-defined
```

### Safety considerations:

- No known contraindications for slow BLS—if anything, slower is likely safer than faster
- The concern with fast BLS (seizure risk with light bars) does not apply to slow frequencies
- Ultra-slow frequencies may simply feel "boring" or lose the dual-attention mechanism that EMDR relies on for processing

---

## Research Opportunities

The following represent **unpublished research gaps** where new data would be valuable:

### 1. Comparative effectiveness of slow BLS frequencies

**Study design**: RCT comparing 0.75 Hz vs 0.5 Hz vs 0.25 Hz for resource installation
**Measures**: Subjective relaxation, HRV changes, resource accessibility

### 2. Cardiac coherence integration with EMDR resourcing

**Study design**: Add HRV biofeedback to standard resourcing protocols; compare 0.1 Hz BLS to standard
**Measures**: Coherence scores, session outcomes, client preference

### 3. Frequency preference by population

**Study design**: Survey EMDR clients on subjective experience at different slow frequencies
**Populations**: Standard PTSD, complex trauma, dissociative disorders, TBI

### 4. Infraslow BLS for extended stabilization

**Study design**: Case series using 0.05–0.1 Hz BLS for severely dysregulated clients
**Measures**: Window of tolerance, dissociation symptoms, session tolerance

---

## Conclusion: Turtles All the Way Down

The EMDR field's lack of specification for "slow" BLS represents both a research gap and an opportunity. The theoretical case for sub-0.5 Hz bilateral stimulation is supported by:

1. **Brainwave science**: Slower frequencies map to deeper restorative states
2. **Cardiac coherence research**: 0.1 Hz is the "sweet spot" for vagal activation, with some individuals showing higher coherence at even slower rates (0.04–0.1 Hz)
3. **Breathing physiology**: Ultra-slow breathing (0.05 Hz) has documented cardiovascular and neural effects
4. **Clinical observation**: Practitioners report that slower BLS "feels more relaxing"

Your device supporting 0.25 Hz—and potentially down to 0.1 Hz or 0.01 Hz—is exploring a legitimate frontier. The "for research" labeling is appropriate given the evidence levels, but the theoretical foundation is sound.

**The turtles go down at least to 0.01 Hz.** Below that, you're in territory where a 100-second cycle may no longer function as "bilateral stimulation" in any meaningful sense—it becomes more like meditation pacing or breathing guidance. But that boundary is itself worth exploring.

---

## Quick Reference: Frequency-to-Experience Mapping

| Hz | Seconds/cycle | Subjective Experience | Theoretical Mechanism |
|----|--------------|----------------------|----------------------|
| 2.0 | 0.5s | Alert, activating | Working memory taxation (max) |
| 1.0 | 1.0s | Standard processing | Delta entrainment, dual attention |
| 0.5 | 2.0s | Calming, grounding | Slow oscillation approach |
| 0.25 | 4.0s | **Relaxing, breathing-aligned** | Natural respiration sync |
| 0.1 | 10.0s | **Deep relaxation, coherence** | Cardiac resonance, vagal activation |
| 0.05 | 20.0s | Meditative, expansive | OM chanting / pranayama territory |
| 0.01 | 100.0s | Unknown—meditation pacing? | Infraslow brain oscillations |

---

## References

### EMDR Clinical Literature
- Shapiro, F. (2018). *EMDR Therapy: Basic Principles, Protocols, and Procedures* (3rd ed.)
- Hase, M. et al. (2021). "The Structure of EMDR Therapy: A Guide for the Therapist." *Frontiers in Psychology*.
- Leeds, A.M. (2009). *A Guide to the Standard EMDR Protocols for Clinicians, Supervisors, and Consultants*.

### Cardiac Coherence and HRV
- Sevoz-Couche, C., & Laborde, S. (2022). "Heart rate variability and slow-paced breathing: when coherence meets resonance." *Neuroscience & Biobehavioral Reviews*, 135, 104576.
- McCraty, R. et al. (2025). "Heart rate variability biofeedback in a global study of the most common coherence frequencies." *Scientific Reports*.
- HeartMath Institute. (2025). "The Science of HeartMath."

### Brainwave and Infraslow Research
- Pagani, M. et al. (2017). "Eye Movement Desensitization and Reprocessing and Slow Wave Sleep: A Putative Mechanism of Action." *Frontiers in Psychology*.
- Hughes, S.W. et al. (2011). "Infraslow oscillations in thalamic relay nuclei: basic mechanisms and significance." *Progress in Brain Research*.
- Vanhatalo, S. et al. (2004). "Infraslow oscillations modulate excitability and interictal epileptic activity." *PNAS*.

### Ultra-Slow Breathing
- Bayer, H. et al. (2022). "Unexpected Cardiovascular Oscillations at 0.1 Hz During Slow Speech Guided Breathing (OM Chanting) at 0.05 Hz." *Frontiers in Physiology*.
- Szulczewski, M.T. (2019). "Training of Paced Breathing at 0.1 Hz Improves CO2 Homeostasis and Relaxation." *PLoS ONE*.

---

*This addendum accompanies the main EMDR Bilateral Stimulation Evidence-Based Parameters report. It documents an emerging research frontier and should not be interpreted as clinical guidance. Frequencies below 0.5 Hz are not currently specified in EMDRIA standards.*
