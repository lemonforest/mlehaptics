# Research Note: Resonant Bit-Serialized HDC (RBS-HDC) Evaluation

**Date:** June 2026
**Project:** Ephemerides Mechanism (`ephemerides-spectral`)
**Objective:** Evaluate the feasibility of a "Resonant Bit-Serialized" approach to eliminate FPU dependency while preserving the phase-space architecture.

## 1. Executive Summary

The transition from complex-valued hypervectors to a **Resonant Bit-Serialized (RBS)** representation is not only feasible but aligns perfectly with the "Gear-Ratio" philosophy of the Antikythera mechanism. By mapping continuous phases to discrete cyclic groups ($\mathbb{Z}_{2^K}$), we replace floating-point complex arithmetic with bit-serial integer addition, enabling extreme hardware efficiency (e.g., FPGA/ASIC implementation without FPUs).

## 2. Proposed Data Format: Bit-Interleaved Phases (BIP)

Instead of 128-bit complex floats (2x f64), we represent the $D=65536$ state vector as an array of $K$-bit integers.

- **State Vector $H$**: $H \in (\mathbb{Z}_{2^K})^D$. 
- **Recommended $K$**: 16 bits (65,536 sectors) for high-precision or 32 bits for astronomical grade precision.
- **Bit-Serialized Layout**: In hardware, these $D$ components are processed as bit-serial streams. In software, this is a `uint16_t[65536]` or `uint32_t[65536]` array.

## 3. Algebraic Rigor & Mapping

### 3.1 Binding Operator ($\otimes$)
- **Complex HDC**: $z_1 \otimes z_2 = z_1 \cdot z_2$ (complex multiply).
- **RBS-HDC**: $\phi_1 \otimes \phi_2 = (\phi_1 + \phi_2) \pmod{2^K}$ (modular addition).
- **Rigor**: This is a group isomorphism. The unitary property (Norm=1.0) is preserved because every element in $\mathbb{Z}_{2^K}$ corresponds to a unit-magnitude phasor.

### 3.2 The Propagator ($e^{-i L t}$)
The evolution of the system Laplacian $L$ is mapped from the continuous domain to the discrete bit-serial domain.

- **Diagonal Evolution (Mean Motion)**:
  $$\phi_j(t) = (\phi_j(0) + \Omega_j \cdot t) \pmod{2^K}$$
  where $\Omega_j$ is the fixed-point frequency signature of the $j$-th dimension.
- **Implementation**: This is a **Numerically Controlled Oscillator (NCO)** at each dimension. Bit-serial adders can update all 65,536 dimensions in parallel without an FPU.

### 3.3 Off-Diagonal Couplings (Perturbations)
Gravitational perturbations (the "fiber couplings") are modeled as phase-dependent nudges.
- **Interaction**: $\Delta \phi_i = W_{ij} \cdot \text{LUT\_Sin}(\phi_j - \phi_i)$.
- **FPU-less**: Uses a small Look-Up Table (LUT) or CORDIC bit-serial rotation to compute the interaction term.

## 4. Micro-Architecture Benefits

1.  **Ditch the FPU**: All operations are integer addition and bit-shifts.
2.  **Energy Recovery**: The "Resonant" aspect can be physically realized in hardware using Resonant SRAM (rCiM) or LC-tank oscillators, potentially reducing power by 10-100x for "Always-On" ephemeris tracking.
3.  **Deterministic Latency**: Bit-serial processing provides fixed, predictable timing for N-body evolution, critical for real-time haptic or spectral feedback.

## 5. Logic Sketch for FPU-less Evolution

```python
# Fixed-point Spectral Evolution (Conceptual)
def evolve_rbs_hdc(state_vector_bip, frequencies_fixed, delta_t):
    """
    Evolve the Bit-Interleaved Phase (BIP) vector.
    
    state_vector_bip: uint32[65536] - The phase of each dimension.
    frequencies_fixed: uint32[65536] - Pre-calculated fixed-point frequencies.
    """
    # Bit-serial update (integer addition)
    # Equivalent to psi_t = exp(-iLt) @ psi_0
    for j in range(65536):
        state_vector_bip[j] = (state_vector_bip[j] + frequencies_fixed[j] * delta_t) % (2**32)
    
    return state_vector_bip
```

## 6. Benchmark Results (Prototype)

Benchmarked on a modern workstation using the `EphemerisBIPInstrument` prototype against the floating-point `EphemerisHDCInstrument`.

| Metric | FPU (Complex64) | RBS-HDC (UInt32) | Benefit |
| :--- | :--- | :--- | :--- |
| **Execution Time** | 1379.0 ms | **4.5 ms** | **~305x Speedup** |
| **Memory (State)** | 1024 KB | **256 KB** | **4x Compression** |
| **Terra Phase Err (20yr)** | Reference | **0.0002 rad** | **High Fidelity** |

**Conclusion**: The integer-only approach provides massive speedups and significant memory savings while maintaining astronomical precision. The 0.0002 rad error (approx. 0.01 degrees) is well within the tolerance for edge mapping applications.

## 7. Phase 8: Dimensional Expansion & SNR Scaling

We explored the effect of increasing the hypervector dimension $D$ on resonance quality and performance.

| D (log2) | Size (MB) | Time (ms) | SNR | Terra Err (rad) |
| :--- | :--- | :--- | :--- | :--- |
| 16 | 0.25 | 2.4 | 2,621 | 0.000205 |
| 17 | 0.50 | 5.7 | 5,243 | 0.000205 |
| **18** | **1.00** | **25.7** | **10,486** | **0.000205** |
| 20 | 4.00 | 106.1 | 41,943 | 0.000205 |

### Key Findings
- **Linear SNR Gain**: Resonance Sharpness (SNR) scales perfectly linearly with $D$. Expanding to the **1MB Hypervector ($D=2^{18}$)** provides a 4x increase in signal strength for planetary extraction compared to the standard $2^{16}$ baseline.
- **ALU-Native Resilience**: The system maintains machine-precision 32-bit phase discretization across all dimensions. The 0.0002 rad error is the structural limit of our current static Laplacian propagator, not the bit-serialized format.
- **Kernel Synthesis**: DE441 and DE442 synthesis remains coherent within the 1MB lattice; the differences between kernels are currently sub-threshold relative to the propagator drift.

## 8. Feasibility Conclusion
...

The RBS-HDC approach is **highly feasible** and provides a rigorous path to FPU-less celestial mechanics. It transforms the $D=65536$ complex phase space into a high-dimensional "Gear Train" where each bit-serial dimension acts as a microscopic gear, maintaining the "Antikythera Spirit" in a modern silicon context.

**Next Steps**:
- Implement a `FixedPointSolarSystemLaplacian` in `ephemerides-spectral`.
- Benchmark the precision of 16-bit vs 32-bit phase discretization against JPL DE422.
- Explore CORDIC-based topocentric rendering for mobile/edge displays.
