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

### 7.1 The Structural Limit (Newtonian/LTI)
The current 0.0002 rad (~0.01°) residual error represents the **Structural Limit** of the Phase 8 model. This limit arises from two primary factors:
1.  **LTI Assumption**: The `SolarSystemLaplacian` is currently a Linear Time-Invariant (LTI) system. It uses a static snapshot of gravitational couplings, ignoring the fact that off-diagonal interaction strengths "breathe" with the epochs.
2.  **Newtonian Limit**: The model follows purely Newtonian mean motions. At this level of precision, General Relativistic effects (time dilation, frame-dragging) start to bleed through as phase drift.

## 8. Phase 9: Dynamic Perturbations & Relativistic Friction

Phase 9 attacks the LTI limit (§7.1) by making the `SolarSystemLaplacian` *breathe* — off-diagonal couplings now modulate with the resonant phase difference between the bodies they connect, and a small Post-Newtonian correction is applied to the diagonal (Mercury's 43"/century relativistic precession is the canonical entry).

### 8.1 Breathing Couplings (Algebraic Form)
The static fiber coupling $W_{ij}$ between two bodies is replaced by a phase-dependent form:

$$W_{ij}(\phi) = W_{ij}^{(0)} \cdot \left(1 + \alpha \cos(n_{ij} \phi_i - m_{ij} \phi_j)\right)$$

where $(n_{ij}, m_{ij})$ is the resonance ratio (e.g. $5{:}2$ for the Jupiter–Saturn Great Conjunction) and $\alpha$ is the modulation depth (10% in the prototype). This is the "fiber bundle" framing applied at the level of the propagator: the connection form depends on where in the bundle you are, not just on the static graph topology.

**Mathematical positioning.** The Phase-9 phrase "breathing Laplacian" is a project codename. The formal name is **state-dependent (non-autonomous) graph Laplacian**: the matrix $L = L(\phi(t))$ depends on the current state, so $\dot\psi = -i L(\phi)\,\psi$ is no longer a single matrix exponential but a chunk-wise integration. Equivalently, in the dynamical-systems literature this is an **adaptive Kuramoto-family network with phase-difference-dependent coupling (PDDP)**: standard Kuramoto fixes $K_{ij}$ and varies $\phi$; we let $K_{ij}$ be a smooth function of $(\phi_i, \phi_j)$. The **vibrating-lattice intuition** (the instantaneous spectrum of $L(\phi)$ defines phonon-like normal modes at each instant) is correct as a static-snapshot picture; the dynamics, however, is 1st-order phase rotation rather than 2nd-order Newtonian, so "vibrating lattice" describes the snapshot but not the flow. See the ephemerides notebook §1.4 for the full positioning across the three vocabularies (spectral graph theory / dynamical systems / DNLS-on-a-graph) and the connection to nonlinear-mode bookkeeping a future Hamilton/Delaunay derivation would unlock.

### 8.2 ALU-Native Implementation
The breathing term is implemented without exiting the integer ALU. The continuous $\cos(\cdot)$ is replaced by a precomputed integer cosine LUT (1024 × `int32`, Q1.14 amplitude) keyed on the top 10 bits of the residue $(n_{ij} \phi_i - m_{ij} \phi_j) \bmod 2^{32}$. The modulation is then applied as integer scaling:

```python
nudge = base_nudge + (NUM * base_nudge * cos_q14) // (DEN * AMP)
```

— all integer ops, zero FPU calls in the inner loop. The LUT itself fits in 4 KB, three orders of magnitude smaller than the 256 KB hypervector it modulates.

### 8.3 Fixed-Point Frequency Discipline
Mean motions are stored as signed `int64` in **residues per day** (Q-format: `MODULO = 2^32` residues per revolution). The conversion is:

$$\omega_{\text{int}} = \mathrm{round}\left(\frac{\omega_{\text{rad/day}}}{2\pi} \cdot 2^{32}\right)$$

Range/precision properties:
- Earth's mean motion → ~11.76 M residues/day; Phobos (smallest period) → ~13.5 G residues/day.
- The pre-flight bounds check rejects `|delta_t| > 6.8 × 10^8 days` (~1.86 Myr) so `omega * delta_t` cannot saturate `int64`.
- Q-format underflow (frequencies that round to zero residues/day) emits a `RuntimeWarning` at construction time. The floor is ~13 Gyr period — never trips for real bodies, but the guard exists so the assumption is checkable.

### 8.4 Overflow Discipline
The encode path distinguishes two kinds of overflow:
- **Signed `int64` saturation** in `omega * step`: a real bug. Wrapped in `np.errstate(over='raise')`, raised as `OverflowError` with a useful message.
- **Unsigned `uint64` wraparound** on the phase accumulator: *intentional* — the cyclic-group reduction we want. Run under `np.errstate(over='ignore')` plus `warnings.filterwarnings(..., 'overflow encountered')` so callers who promote `RuntimeWarning` to error don't see spurious noise.

The combination is: pre-flight bounds check (primary defense) + scoped `errstate` (catches genuine overflow) + lenient cyclic-group context (preserves the modular-arithmetic semantics).

## 9. Conclusion

The RBS-HDC approach is **highly feasible** and provides a rigorous path to FPU-less celestial mechanics. It transforms the $D=65536$ complex phase space into a high-dimensional "Gear Train" where each bit-serial dimension acts as a microscopic gear, maintaining the "Antikythera Spirit" in a modern silicon context. Phase 9 extends that gear train with phase-dependent fiber couplings: the breathing Laplacian is the modular-arithmetic version of a connection form, integrated as integer chunks plus a single fractional-day remainder.

**Cross-pollination note.** The chess-spectral `Z_{640}` phase-operator engine (§20.13–§20.17 of the chess notebook) is algebraically isomorphic to this BIP design at the group level. The two projects differ only in the modulus: chess uses a non-power-of-2 ($640 = 2^7 \cdot 5$) and pays an explicit `% 640` per op; ephemerides uses $2^{32}$ and gets cyclic-group reduction for free as `uint32` overflow. The off-diagonal LUT pattern documented here transfers directly.

**Next Steps**:
- Re-measure the $0.0002$ rad floor with breathing couplings active across the full 26-body Laplacian (Phase 9 currently exercises only the J–S 5:2 term).
- Add resonance entries for Neptune–Pluto $3{:}2$, Io–Europa $1{:}2$, Earth–Moon (precession), and the Trojan asteroids.
- Benchmark 16-bit vs 32-bit phase discretization against JPL DE442 across a 200-year window.
- Explore CORDIC-based topocentric rendering for mobile/edge displays (the cosine LUT is the first step; CORDIC handles the trickier topocentric transforms).
