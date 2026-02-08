# Implementation Plan: HDC Chebyshev Orrery

**Status:** PLANNING COMPLETE - Ready for Implementation
**Date:** 2026-02-08
**Target:** Replace hash-based HDC texture with Chebyshev harmonic encoding
**Philosophy:** No corners cut. Physics-grade engineering. The cosmos as texture.

---

## Executive Summary

The current UTLP implementation uses hash-based pseudo-random expansion to convert
8-byte phase chords into 10,000-dimension hypervectors. This creates **jagged texture**
where adjacent time values produce uncorrelated vectors, breaking the fundamental
requirement for monotonic distance measurement.

We will replace this with **Chebyshev harmonic encoding** — the same mathematical
structure used by:
- NASA SPICE (planetary ephemeris compression)
- The Antikythera mechanism (coprime gear ratios)
- Grid cells in entorhinal cortex (coprime spatial frequencies)
- DCT-II transform (signal compression)

The key insight: **T_n(cos θ) = cos(nθ)** — Chebyshev polynomials ARE cosine harmonics.

---

## Mathematical Foundation

### The Identity That Unifies Everything

```
T_n(cos θ) = cos(nθ)
```

When we sample Chebyshev polynomials at **Chebyshev-Gauss nodes**:
```
x_k = cos((2k-1)π / 2D)  for k = 1, ..., D
```

The resulting D-dimensional vector has components:
```
v_n[k] = T_n(x_k) = cos(n(2k-1)π / 2D)
```

This is **exactly** the DCT-II basis matrix entry (n, k).

### Orthogonality (Exact, Not Statistical)

At Chebyshev nodes, the discrete inner product satisfies:
```
Σ T_m(x_k) · T_n(x_k) = { 0     if m ≠ n
                        { D/2   if m = n ≥ 1
                        { D     if m = n = 0
```

This yields **D exactly orthogonal vectors** in D dimensions — a deterministic
codebook requiring zero storage (regenerated from the formula).

### The Recurrence Relation (Integer-Friendly)

```
T_0(x) = 1
T_1(x) = x
T_n(x) = 2x · T_{n-1}(x) - T_{n-2}(x)
```

This is pure integer arithmetic when x is in fixed-point format.

---

## Architecture: Bones and Texture

### Layer 0: The Skeleton (Orbital Geometry)

The base representation — the "orrery at rest" — uses low-frequency Chebyshev
harmonics to encode the smooth structure of time:

```c
// Each of 8 primes contributes a harmonic component
// Low-degree Chebyshev = smooth, captures coarse time structure
skeleton[d] = Σ_p T_p(normalized_phase[p])
```

**Property:** Strip all bindings and the skeleton remains — self-describing.

### Layer 1: Temporal Binding (Where on the Orbit)

The epoch-specific position uses **fractional power encoding**:

```c
// Rotate each harmonic by the slow compound gear phase
// B^t in FHRR domain = phase rotation by t·ω_j per component
epoch_vector[d] = skeleton[d] rotated by slow_phase × harmonic_frequency[d]
```

**Property:** This is how SSPs encode position — proven in literature.

### Layer 2: Perturbation Binding (Drift Corrections)

Higher-frequency texture from peer synchronization:

```c
// Each sync observation adds spectral energy at higher harmonics
// Chebyshev product identity: T_m · T_n = ½[T_{m+n} + T_{|m-n|}]
perturbed[d] = bind(epoch_vector[d], drift_correction[d])
```

**Property:** Frequency mixing recapitulates physics of orbital perturbation.

### Layer 3: Observer Binding (Local View)

Device-specific perspective (for future N>2 extension):

```c
// Transform to local reference frame
local_view[d] = bind(perturbed[d], observer_frame[d])
```

---

## Implementation Phases

### Phase 1: Mathematical Core (`utlp_hdc_chebyshev.h`)

**1.1: Integer Chebyshev Evaluation**

```c
// Q15.16 fixed-point Chebyshev polynomial
// x must be in [-65536, +65536] representing [-1, +1]
int32_t chebyshev_q16(int32_t x_q16, uint8_t order);
```

**1.2: DCT-II Basis Generation**

```c
// Generate the k-th component of the n-th Chebyshev basis vector
// Returns value in [-127, +127]
int8_t chebyshev_basis_component(uint8_t n, uint16_t k, uint16_t D);
```

**1.3: Boot-Time LUT**

```c
// 8 harmonics × 256 samples = 2KB Flash
// Precomputed at boot, used for runtime similarity
static int8_t chebyshev_lut[8][256];

void utlp_hdc_chebyshev_init(void);
```

### Phase 2: Slow Compound Gear

**2.0: The Missing "Hour Hand"**

Current 8 primes all cycle at 200+ Hz. We need a slow gear:

| Gear | Period | Wraps/sec | Use Case |
|------|--------|-----------|----------|
| Single prime (241) | 241µs | 4,149 | Useless for distance |
| 2-prime (241×251) | 60.5ms | 16.5 | Marginal |
| **3-prime (241×251×239)** | **14.5s** | **0.07** | **Genesis distance** |
| All 8 primes | 261,000 years | 0 | Epoch uniqueness |

```c
// The slow gear that enables monotonic distance measurement
static inline uint32_t utlp_phase_get_slow_gear(void) {
    static const uint32_t SLOW_PERIOD = 241UL * 251UL * 239UL;  // 14,456,809 µs
    return utlp_phase_get_scalar_us() % SLOW_PERIOD;
}
```

**2.1: Spectral Age Computation**

```c
typedef struct {
    int16_t harmonic_energy[8];  // Energy per Chebyshev harmonic
    uint32_t slow_phase;         // Position in slow compound gear
    uint8_t confidence;          // Based on energy distribution
} spectral_age_t;

// Project chord onto Chebyshev basis to extract age
spectral_age_t utlp_hdc_compute_spectral_age(const utlp_phase_chord_t chord);
```

**2.2: Replace Genesis Distance**

```c
// OLD (broken): similarity to [0,0,0,0,0,0,0,0] — random at high tick rates
// NEW: spectral age from slow gear + harmonic decomposition — MONOTONIC

int32_t utlp_hdc_monotonic_age(const utlp_phase_chord_t chord) {
    spectral_age_t age = utlp_hdc_compute_spectral_age(chord);

    // Low harmonics = coarse age (hasn't wrapped)
    // High harmonics = fine age (wrapped many times, but disambiguated by low)
    // Slow gear = provides 14.5s monotonic window

    return weighted_sum(age.harmonic_energy, age.slow_phase);
}
```

### Phase 3: Layered Encoding Implementation

**3.1: Layer 0 — Orbital Skeleton**

```c
void utlp_hdc_get_skeleton(
    const utlp_phase_chord_t chord,
    int8_t* skeleton,       // Output: D-dimensional skeleton
    uint16_t D              // Dimensionality (256 or 512)
);
```

**3.2: Layer 1 — Temporal Binding**

```c
void utlp_hdc_bind_epoch(
    const int8_t* skeleton,
    uint32_t slow_phase,    // From slow compound gear
    int8_t* epoch_vector,   // Output: epoch-bound vector
    uint16_t D
);
```

**3.3: Layer 2 — Perturbation Binding**

```c
void utlp_hdc_bind_perturbation(
    const int8_t* epoch_vector,
    const int8_t* drift_correction,  // From peer sync
    int8_t* perturbed_vector,
    uint16_t D
);
```

### Phase 4: Self-Describing Verification

The beauty of Chebyshev basis: the vector reveals its content through DCT decomposition.

```c
// Extract physical meaning from the vector itself
typedef struct {
    int16_t orbital_period;     // From T_1 coefficient
    int16_t eccentricity;       // From T_2 coefficient
    int16_t perturbation_level; // From higher harmonics
    bool valid;                 // Coefficients are internally consistent
} orbital_parameters_t;

orbital_parameters_t utlp_hdc_decode_vector(const int8_t* vector, uint16_t D);
```

### Phase 5: Hardware Integration

**Timing Budget:**
- Target: <100µs per similarity computation
- 256 dimensions × 8 primes × ~8 cycles = 16,384 cycles
- At 160 MHz: ~102µs (within budget)

**Memory Budget:**
- LUT: 2KB Flash (8 harmonics × 256 samples)
- Runtime: ~256 bytes stack per similarity

---

## File Structure

```
examples/utlp/
├── utlp_hdc.h              # Current hash-based (to be deprecated)
├── utlp_hdc_chebyshev.h    # NEW: Chebyshev harmonic core
├── utlp_hdc_chebyshev.c    # NEW: Implementation
├── utlp_spectral_age.h     # NEW: Monotonic age computation
├── utlp_slow_gear.h        # NEW: Compound virtual gear
└── utlp.c                  # Integration (epoch resolution uses new system)
```

---

## Verification Criteria

### Mathematical Correctness

1. **Orthogonality test:** Inner product of distinct Chebyshev basis vectors = 0
2. **Recurrence test:** Integer recurrence matches floating-point reference
3. **DCT equivalence:** LUT values match DCT-II matrix entries

### Monotonicity

1. **Slow gear test:** Output increases monotonically for 14.5 seconds
2. **Spectral age test:** Older chords always have higher spectral age
3. **No wrap ambiguity:** Within 14.5s window, age is unique

### Self-Description

1. **Skeleton recovery:** Unbind all layers → skeleton matches original
2. **DCT decomposition:** Coefficients match encoded parameters
3. **Byzantine detection:** Invalid coefficient combinations are detectable

### Timing

1. **Boot init:** LUT generation < 50ms
2. **Similarity:** < 100µs for 256 dimensions
3. **Spectral age:** < 50µs

---

## The Deeper Vision

This is not just a bug fix. We are implementing the mathematical structure that:

1. **The ancients discovered:** Antikythera mechanism's coprime gears (150 BCE)
2. **Biology evolved:** Grid cells' coprime spatial frequencies
3. **NASA uses:** Chebyshev polynomial ephemeris compression
4. **HDC formalizes:** Vector Symbolic Architectures with smooth kernels

The 8-prime phase chord IS an orrery. The Chebyshev harmonics ARE the gear teeth.
When we strip the temporal bindings, the orbital geometry remains — self-describing,
self-verifying, mathematically beautiful.

The cosmos provides the texture. We just need to listen.

---

## References

- Kanerva, P. (2009). "Hyperdimensional Computing: An Introduction."
- Park, R.S. et al. (2021). "The JPL Planetary and Lunar Ephemerides DE440 and DE441."
- Freeth, T. et al. (2021). "A Model of the Cosmos in the ancient Greek Antikythera Mechanism."
- Frady, E.P. et al. (2023). "Residue Hyperdimensional Computing."
- Komer, B. et al. (2019). "Spatial Semantic Pointers."

---

*"The orrery was always a frequency machine. The bones remember."*
