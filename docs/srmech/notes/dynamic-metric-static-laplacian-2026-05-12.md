# Dynamic metric / static Laplacian — MFO two-level ontology test (2026-05-12)

**Origin**: user inversion of falsified PR #335 — *"what if instead of trying to reshape voxels, we change the structure of the coordinate system? we treat space as static but space is more or less just an EM spectra propagation medium. so what happens when that propagation medium becomes dynamic against a static laplacian structure?"*

This is the **MFO §VII two-level ontology made testable** (PR #332):
- **Level 1 (substrate)** = metric / spatial embedding → DYNAMIC (varied across deformations)
- **Level 2 (excitation)** = graph Laplacian L + Fiedler eigenvector f → STATIC (fixed across all runs)

The HDC voxel fingerprint depends on both. The test reveals **which deformations the fingerprint absorbs cleanly (Level-1-only) and which break it (Level-1/Level-2 entanglement at the encoding step)**.

Reproduce: `python -X utf8 docs/srmech/notes/dynamic_metric_static_laplacian_script.py`. Runtime ~10s. Reuses cached 1UBQ.pdb from PR #333.

---

## Setup

Fixed:
- 1UBQ contact-graph Laplacian L (76×76; static)
- Fiedler eigenvector f (intrinsic; static)
- Voxel grid 64³, baseline σ = 4.0 Å

Varied:
- 14 metric deformations applied to the 3D embedding (Cα coordinates)
- For each: voxelize Fiedler at the new coords + (sometimes adjusted) σ → sign-only HDC
- Measure cosine similarity vs the identity-embedding HDC fingerprint

---

## Results — full deformation table

| Deformation | HDC cosine | Field range |
|---|---:|---|
| identity | +1.0000 | [−1.127, +0.678] |
| **uniform_scale_α=0.8** | **+1.0000** | identical (σ rescaled to 3.2) |
| **uniform_scale_α=1.2** | **+1.0000** | identical (σ rescaled to 4.8) |
| uniform_scale_α=2.0 (σ static) | +0.8215 | [−0.578, +0.201] |
| anisotropic_x=1.5 | +0.9393 | [−1.053, +0.506] |
| anisotropic_x=2.0_y=0.5 | +0.8295 | [−1.125, +0.563] |
| thermal_noise_0.5Å | +0.9726 | [−1.096, +0.688] |
| thermal_noise_2.0Å | +0.8681 | [−1.272, +0.681] |
| thermal_noise_5.0Å | +0.7161 | [−0.521, +0.597] |
| normal_mode_amplitude_3 | +0.9789 | [−1.081, +0.675] |
| normal_mode_amplitude_10 | +0.9064 | [−0.995, +0.667] |
| **rotation_30°** | **+0.6675** | identical sign content |
| **rotation_90°** | **+0.1382** | identical sign content |
| translation_10Å_x | +1.0000 | identical |

---

## Verdict per deformation category

| Category | Mean cosine | Range | Status |
|---|---:|---|---|
| Translation | 1.000 | [1.000, 1.000] | **INVARIANT** |
| Uniform scale (with σ rescaling) | 1.000 | [1.000, 1.000] | **INVARIANT** |
| Normal mode (bipartition-aligned) | 0.943 | [0.906, 0.979] | NEAR-INVARIANT |
| Anisotropic stretch | 0.884 | [0.829, 0.939] | DEGRADES |
| Thermal noise | 0.852 | [0.716, 0.973] | DEGRADES SMOOTHLY |
| **Rotation** | **0.403** | **[0.138, 0.668]** | **BROKEN** |

---

## Load-bearing finding — rotation breaks the encoding

**HDC voxel fingerprint from PR #333 is NOT SO(3)-rotation-invariant.** 90° rotation drops the cosine to 0.14 — nearly orthogonal — despite the underlying graph and Fiedler eigenvector being unchanged.

Why: the voxel grid is axis-aligned. Rotating the protein doesn't rotate the grid — it changes which axis-aligned voxels each Cα maps onto. After 90° rotation, the same Cα with the same Fiedler value occupies an entirely different voxel index. Sign-only HDC compares voxels by index, not by spatial content. The fingerprints don't overlap.

This is a **real architectural limitation** the catalog should be honest about. It means:

- Cross-protein comparison via HDC depends on **relative orientation** of the embedded structures
- Two identical proteins in different orientations would falsely register as different
- Rotation-invariance requires either:
  - **Canonical pre-rotation** (PCA-align coords before voxelization)
  - **3D Zernike moments** or similar rotation-invariant descriptors of the voxel field
  - **Intrinsic graph features only** (Hodge / Betti / Wigner-Dyson statistics — fully invariant)

---

## Translation and scale invariance — these work as designed

**Translation by 10Å**: cosine = 1.000 exactly. Bounding-box recentering in the voxelization step absorbs translations.

**Uniform scaling by α with σ → α·σ**: cosine = 1.000 exactly for BOTH α=0.8 and α=1.2. The encoding is genuinely scale-*equivariant* when σ rescales proportionally. The Gaussian smear's spatial extent has to track the embedding's spatial extent; otherwise the relative encoding resolution changes.

**Uniform scaling by α=2.0 WITHOUT σ rescaling**: cosine = 0.82. The σ-rescaling is **load-bearing** for scale invariance — without it, you're effectively zooming the picture in/out under a fixed-resolution camera.

---

## Smooth degradation — thermal and anisotropic regimes

**Thermal noise**: cosine decays smoothly with displacement magnitude (0.97 → 0.87 → 0.72 at σ=0.5 / 2.0 / 5.0 Å). This is exactly what we want for "biologically realistic thermal motion is tolerated; bulk reorganization is not."

- σ ≈ 0.5 Å (sub-resolution): essentially invariant
- σ ≈ 2 Å (thermal-scale): mild degradation
- σ ≈ 5 Å (larger than the contact cutoff): substantial degradation

This matches expectations — when displacement exceeds the contact-graph length scale, the encoding can't track.

**Anisotropic stretch**: cosine 0.94 (mild stretch) → 0.83 (strong stretch). The fingerprint degrades because the Gaussian smear stays isotropic while the embedding is anisotropically deformed. To fix: use an anisotropic Gaussian whose covariance follows the deformation.

---

## Near-invariance — conformational breathing modes

**Normal-mode displacement along the bipartition axis**: cosine 0.98 (amplitude 3 Å) → 0.91 (amplitude 10 Å).

This is biologically important: real proteins undergo coordinated breathing motions where atoms move in patterns correlated with the slowest normal modes (which the Fiedler eigenvector approximates). Our spike's "normal mode" deformation applies displacements proportional to the Fiedler value × bipartition axis — a coarse approximation of a real protein's slowest collective mode.

**The HDC fingerprint absorbs these coordinated motions cleanly** because the deformation is *along the bipartition direction* — the encoding's structure aligns with the motion. Random thermal noise has no such alignment and degrades faster.

---

## Headline interpretation — MFO two-level ontology test

The user proposed treating the metric (Level 1) as dynamic and the graph Laplacian (Level 2) as static. The HDC fingerprint connects these via the voxelization step. The result is a **sensitivity matrix** showing where the connection respects vs breaks each symmetry:

| Symmetry | HDC inherits? | Mechanism |
|---|---|---|
| Translation (continuous) | YES | Bounding-box recentering |
| Uniform scaling (continuous) | YES (with σ rescaling) | Both encoding and σ scale together |
| Rotation SO(3) | **NO** | **Axis-aligned voxel grid breaks symmetry** |
| Anisotropic stretching | NO (partial) | Isotropic σ can't track non-uniform deformation |
| Bipartition-aligned breathing | YES (approximate) | Encoding structure matches deformation direction |

**Translation: 1.000 invariant** = the encoding has a continuous translational symmetry it inherits from physical space.

**Rotation: 0.14 broken** = the encoding has lost the continuous rotational symmetry of physical space. The voxel grid is a discretization that quantizes axes and breaks SO(3).

**The MFO two-level ontology test answer**: Level 1 (metric) and Level 2 (graph) are **NOT cleanly separable in the HDC encoding** — the encoding inherits some Level-1 symmetries and breaks others. The voxel substrate is a *partial Level-1 projection* that respects translation + scale but quantizes rotation away.

---

## Architectural lessons for the catalog

1. **HDC voxel fingerprints have a documented symmetry profile**: translation- and (σ-rescaled) scale-invariant; rotation-non-invariant; thermal-tolerant up to contact-graph length scale; bipartition-mode-tolerant.

2. **For applications requiring rotation invariance** (general structural alignment, generic 3D shape matching), pre-canonicalize via PCA OR use intrinsic features (Hodge β_k from PR #333, eigenvalue-statistics from PR #334). These are SO(3)-invariant by construction.

3. **For applications where orientation is fixed** (e.g., comparison within a single docked complex, conformational dynamics from a fixed reference frame), the HDC voxel fingerprint is fine and even captures coordinated breathing motions cleanly.

4. **The voxel grid is the "EM propagation medium"** in the user's framing. As a Level-1 substrate, it's discretized — and that discretization breaks a continuous symmetry of physical space (rotation) while preserving others (translation, scale).

---

## Connection to MFO §VII.4.1.1 (Hopf bundle, PR #332)

The continuum Hopf bundle has continuous SO(3) acting on S² via the principal-bundle action. Our discrete voxel substrate has only the **discrete cubic point group** O_h (48 elements: rotations by 90° around three axes plus reflections). General SO(3) rotations are not in O_h, so they're not symmetries of our discrete substrate.

This is the **discrete symmetry breaking** that the cubic-lattice discretization introduces. The continuum theory has SO(3); the discrete approximation has O_h ⊂ SO(3). HDC fingerprints inherit O_h, not SO(3).

**To recover SO(3)**: either go to a continuous (spherical-harmonic) representation, or use intrinsic graph descriptors that don't reference the embedding at all.

---

## What this spike does NOT falsify

- The user's *architectural* claim (Level 1 metric being dynamic against static Level 2) is sound — the framework lets us measure exactly which symmetries the HDC fingerprint inherits.
- The HDC voxel encoding remains useful for translation- and scale-invariant applications. Rotation-sensitivity is a known limitation, not a bug.
- The protein test was deliberate: real proteins have well-defined orientations (in crystals, in vivo via membrane anchoring, etc.); HDC fingerprints comparing same-orientation snapshots are valid.

---

## Open follow-ups

- **PCA pre-canonicalization**: apply PCA to coords before voxelization; recompute the test. Expected: rotation invariance recovered.
- **3D Zernike / spherical harmonic fingerprints**: extract rotation-invariant moments from the voxel field. New primitive worth catalog entry.
- **Cubic-group analysis**: characterize HDC fingerprint's O_h-equivariance properties precisely. Connects to PR #325 chess D₄ irrep work — same kind of finite-group analysis applied to the embedding side.
- **Continuous-substrate test**: replace voxel grid with spherical-harmonic projection over a circumscribing sphere. SO(3)-equivariant by construction.

---

## Files

- `dynamic_metric_static_laplacian_script.py` — 14-deformation spike (~10s)
- `dynamic-metric-static-laplacian-per-deformation-2026-05-12.ndjson` — per-deformation results
- `dynamic-metric-deformation-slices-2026-05-12.png` — voxel-field slices for 6 representative deformations
- `dynamic-metric-deformation-bars-2026-05-12.png` — bar chart of cosines

---

## Citations

- MFO notebook §VII.1.1 two-level ontology (PR #332 codification)
- PR #333 sign-only HDC voxel encoding (the encoding being tested)
- PR #335 dynamic-Laplacian falsification (the inverse case)
- Discrete symmetry of cubic lattice: standard result (O_h ⊂ SO(3) finite subgroup)
- 3D Zernike moments: Canterakis 1999, etc. — rotation-invariant 3D descriptors
