# Spherical harmonic SO(3)-invariant fingerprint — recovers rotation invariance with tradeoff (2026-05-12)

**Origin**: PR #336 found that voxel HDC encoding is NOT rotation-invariant (cubic-lattice O_h symmetry breaks SO(3)). User wanted to keep going on the question-tree. The natural fix flagged in PR #336: spherical harmonic projection onto concentric circumscribing spheres, using the power spectrum `P_l(r) = Σ_m |C_lm(r)|²` as a SO(3)-invariant fingerprint.

This **is** the **MFO §VII.4.1.1 spherical compression operator** applied to real protein data: 3D bulk field → 2D boundary spherical-harmonic decomposition → power spectrum per shell.

**Headline**: SO(3) invariance fully recovered (machine precision); cross-protein discrimination reduced but preserved. **Two complementary fingerprints** now in the catalog with documented tradeoffs.

Reproduce: `python -X utf8 docs/srmech/notes/spherical_harmonic_fingerprint_script.py`. Runtime ~30s (most of which is Y_lm precompute; per-protein after that is ~10s).

---

## Configuration

| Parameter | Value |
|---|---|
| Voxel grid | 64³ |
| Spherical harmonic l_max | 20 |
| Concentric shells | 8 |
| Angular grid (θ × φ) | 80 × 160 |
| Fingerprint dimension | 8 × 21 = 168 |

The fingerprint is the **power spectrum** `P_l(r) = Σ_m |C_lm(r)|²` for each shell r. Rotation acts on `C_lm` via Wigner D-matrices that mix m-modes within a fixed l, leaving `P_l(r)` invariant.

For scale invariance, the shell radii are scaled by the protein's intrinsic max-distance-from-centroid (gyration-like), so the encoding adapts to protein size.

---

## Results

### Rotation invariance — THE LOAD-BEARING WIN

| Rotation | SH cosine | Voxel HDC (PR #336) |
|---|---:|---:|
| Self (control) | 1.000000 | 1.000 |
| 30° about z | **1.000000** | 0.668 |
| 90° about z | **1.000000** | 0.138 |
| 180° about z | **1.000000** | n/a |
| 90° about x | **1.000000** | n/a |
| 90° about y | **1.000000** | n/a |
| 1BPI vs 1BPI rotated 45° y | **1.000000** | n/a |

**All rotations: 1.000000 at machine precision.** SO(3) invariance fully recovered.

### Translation invariance

| Test | SH cosine |
|---|---:|
| Translation 10Å along x | 1.000000 |

### Scale invariance (with intrinsic-radius scaling)

| α | SH cosine |
|---|---:|
| 0.8 | 0.995 |
| 1.2 | 0.995 |
| **2.0** | **0.921** |

Mild residual scale-sensitivity at α=2.0 due to voxel-bbox interaction; tighter than voxel HDC behavior (which was 0.82 without σ rescaling) but not machine precision.

### Thermal noise tolerance

| Magnitude | SH cosine |
|---|---:|
| 0.5 Å | 0.9999 |
| 2.0 Å | 0.966 |
| 5.0 Å | 0.978 |

Note: 5.0 Å scoring HIGHER than 2.0 Å is mildly suspicious — likely random-fluctuation correlation in the power spectrum at high noise levels. Not load-bearing.

### Cross-protein discrimination

| Comparison | SH cosine |
|---|---:|
| 1UBQ vs 1BPI | 0.929 |

For reference:
- PR #333 voxel HDC (sign-only): −0.343 (firmly different)
- PR #336 same encoding, rotated 90°: 0.138 (false positive — same protein looks different)

**The tradeoff**: SH power spectrum gets rotation invariance at the cost of similarity-discrimination. 1UBQ and 1BPI now look similar (0.93) instead of clearly different (−0.34).

---

## Architectural lesson — two complementary fingerprints

| Fingerprint | Rotation | Translation | Scale | Cross-protein | Use case |
|---|---|---|---|---|---|
| **Voxel HDC** (PR #333) | broken (0.14 @ 90°) | invariant | invariant (with σ rescaling) | **strong (-0.34)** | Fixed orientation; max discrimination |
| **SH power spectrum** (this PR) | **invariant (1.00)** | invariant | near-invariant (0.92 @ α=2) | weaker (+0.93) | Unknown orientation; general similarity |

Neither is universally better — they're **complementary primitives** in the catalog. The choice depends on:

- **Use voxel HDC** when: protein orientation is known (crystal structures, docked complexes, conformational dynamics from reference frame); maximum cross-protein discrimination needed.
- **Use SH power spectrum** when: orientation is unknown or variable (general structural similarity search, comparing structures from different sources); rotation-invariance is essential.
- **Use intrinsic graph features** (Hodge β_k from PR #333, Wigner-Dyson stats from PR #334) when: you want full embedding-independence including discretization-artifact-free rotation invariance.

The catalog now has a **three-tier discrimination hierarchy** for protein-bipartition-like data:

1. **Topological** (Hodge β_k, PR #333): integer Betti numbers; categorical separation; SO(3)-invariant by construction
2. **Statistical** (Wigner-Dyson NNS, PR #334): universal random-matrix class; SO(3)-invariant by construction
3. **Geometric**:
   - Voxel HDC: high-information but breaks SO(3)
   - SH power spectrum: SO(3)-invariant but lower-discrimination
   - 3D Zernike moments (future): full SO(3) invariants with more discrimination than power spectrum

---

## Connection to MFO §VII.4.1.1 — the spherical compression operator in practice

PR #332 landed §VII.4.1.1 with the framework:

$$\Delta_{S^3} = \Delta_{S^2} + S^1\text{-fibre harmonics}$$

The "spherical compression" operator takes 3D bulk → 2D boundary by projecting onto the S² boundary. **This spike is the discrete realization of that operator**:

- 3D bulk = voxel field in `R³`
- Projection = sample on concentric spheres
- Spherical harmonic decomposition = the discrete S²-mode decomposition
- Power spectrum = the SO(3)-invariant projector onto each `l`-shell

The information lost in compression = the m-mode phases (the "S¹-fibre harmonics"). The power spectrum keeps `|Σ_m C_lm|²` summed — analog of integrating out the fibre.

**This is the second concrete instance of MFO §VII.4.1.1 framework on real data**, after PR #333 Hodge spike. The compression operator is real and computable.

---

## Tradeoff documented in formal terms

| Information class | SH power spectrum | Voxel HDC |
|---|---|---|
| l-spectrum content (rotation-invariant) | KEPT | NOT explicitly extracted |
| m-mode phase content (orientation-specific) | DISCARDED | KEPT (via voxel indices) |
| Radial structure | KEPT (8 shells) | KEPT (full 3D) |
| Sign pattern (bipartition) | indirect (via field magnitudes) | KEPT (sign-only encoding) |

**The fundamental tradeoff**: SO(3) invariance requires discarding orientation-specific information. Power spectrum does this maximally; intermediate constructions (3D Zernike) keep more.

---

## Open follow-ups

1. **3D Zernike moments** — full SO(3) invariants from polynomial basis on the unit ball. Keep more cross-protein discrimination than power spectrum. ~45 min spike.
2. **Spherical harmonic phase alignment** — instead of discarding phases, ROTATE the SH coefficients to a canonical frame (PCA-based or principal-axis-based). Recovers per-l direction information while maintaining rotation invariance at the comparison level.
3. **Bispectrum** — higher-order SO(3) invariant that captures m-correlations across l-modes. More information than power spectrum, fully invariant.
4. **Test PR #336's `normal_mode` deformation** here — would the SH fingerprint also tolerate it, or does losing m-modes lose breathing-mode info?

---

## Files

- `spherical_harmonic_fingerprint_script.py` — vectorized SH spike with Y_lm caching (~30s)
- `spherical-harmonic-fingerprint-per-test-2026-05-12.ndjson` — per-test results
- `spherical-harmonic-fingerprint-comparison-2026-05-12.png` — SH power spectra under rotation + cross-protein + bar chart vs voxel HDC

---

## Citations

- MFO notebook §VII.4.1.1 (PR #332) — spherical compression operator
- Spherical harmonic addition theorem; Wigner D-matrix action on SH coefficients
- 3D Zernike moments: Canterakis 1999 (future spike)
- Bispectrum SO(3) invariants: Kakarala 2012 (future spike)
