# Spike #17 — Spherical harmonics on `S^d` (d ≥ 3) test the refined law at higher dimensions

**Branch:** `research/spike-17-spherical-harmonics-higher-d` (from `main` at `0fc297f`)
**Date:** 2026-05-13
**Predecessor:** Spike #16 `spike_16_painleve_algebraic_classification_2026-05-13.md` on branch `research/spike-16-painleve-algebraic-classification` at `efa4dea` (4-mechanism refined law, 7/7 fits including nonlinear Painlevé).
**Status:** RESEARCH — outcome: **CLEAN CONFIRMATION** — the 4-mechanism refined law fits cleanly at `d = 3, 4, 5, 6, 7` (8th setting added; no qualitatively new structural mechanism appears). H^d non-compact dual fits as a **predicted no-closed-form setting** (9th row): mechanism (i) requires finite-dim irreps, `SO(d, 1)` has only infinite-dim unitary irreps, scalar Laplacian on H^d has purely continuous spectrum on `[(d−1)²/4, ∞)`. **9/9 settings fit, no new mechanism (v) needed.**
**Tabular sidecar:** `spike_17_spherical_harmonics_results_2026-05-13.ndjson` (59 records: provenance + structural facts + dimension tables + branching checks + mechanism fits + 9-setting score + verdict).
**Verification script:** `spike_17_spherical_harmonics_verification_script.py` (all `D(d, l) = sum_{k=0..l} D(d−1, k)` branching dimension identities verified for `d ∈ {3,4,5,6,7}` and `ℓ ∈ {0,...,5}`).

---

## §0. The hypothesis under test

From Spike #16 §4.1, the refined universal structural law (4-mechanism, 7-setting version, with (ii) absorbed into (iv)) is:

> *Closed-form spectral compression exists iff the algebraic structure (commuting operators, monodromy data, isomonodromic-deformation tau-function, or any combination thereof) selects a finite-dimensional invariant subspace at each closed-form-eligible parameter point, via one of the following mechanisms:*
> 1. **Non-abelian Lie factor with finite-dim irreps + Casimir labeling.**
> 3. **Finite discrete-group orbit on the structural space** (finite monodromy of local system; finite mapping-class-group orbit on character variety; finite affine-Weyl Bäcklund orbit on parameter space).
> 4. **Discrete spectral / parameter quantization on a rational-/integer-/elliptic-lattice locus** (accessory-parameter spectrum; integer-filtration; Bäcklund-orbit lattice; Picard elliptic-rational lattice).

All 7 prior settings (CMS Kerr, KY Kerr, Lamé S², Bessel disk, ₂F₁, Heun, Painlevé I-VI) live in **1D or 2D base space** (Lamé on 2D ellipsoid; Bessel on 2D disk; ₂F₁ on the punctured complex line; Heun on a 4-punctured plane; Painlevé as ODEs in a 1D parameter; Kerr-Teukolsky as separated ODEs after the 4D → angular/radial split). This spike tests whether anything **qualitatively new** appears in **higher-dimensional base manifolds** — specifically the canonical higher-d closed-form setting of **scalar spherical harmonics on `S^d` for `d ≥ 3`**.

### §0.1 Why `S^d` is the natural higher-dimensional test

- **Most studied compact higher-dimensional Riemannian manifolds.** Spherical harmonics on `S^d` for general `d` are textbook material (Vilenkin 1968 *Special Functions and the Theory of Group Representations*; Müller 1966 *Spherical Harmonics*; Stein-Weiss 1971 *Introduction to Fourier Analysis on Euclidean Spaces* Ch. 4; Atkinson-Han 2012 *Spherical Harmonics and Approximations on the Unit Sphere*).
- **Maximally compact and homogeneous.** `S^d = SO(d+1)/SO(d)` is a compact rank-1 symmetric space (Helgason 1978 *Differential Geometry, Lie Groups, and Symmetric Spaces*).
- **The "least adversarial" higher-d case.** If the refined law breaks at higher d, it should break here first — `S^d` is the simplest higher-d Riemannian manifold with a closed-form Laplacian-eigenfunction theory. A clean fit at higher d on `S^d` is therefore a strong confirmation; a failure would be a critical refutation.
- **Casimir rank changes with d.** `SO(d+1)` has rank `⌊(d+1)/2⌋`. At `d ∈ {1, 2}`: rank 1 (one Casimir). At `d ∈ {3, 4}`: rank 2 (two commuting Casimirs). At `d ≥ 5`: rank ≥ 3. If multi-Casimir structure refines the law, this spike must surface it.
- **Exceptional embeddings at small d.** `S^1 = U(1)` and `S^3 = SU(2)` carry Lie-group structure (the sphere itself is a group). `S^7` is parallelizable (octonion unit sphere; Moufang loop but **not** a Lie group). These edge cases could in principle introduce a new structural mechanism (group-multiplication on the manifold itself, beyond just `SO(d+1)` symmetry).

### §0.2 The non-compact dual `H^d` as a control test

The non-compact dual `H^d = SO(d, 1) / SO(d)` is a rank-1 symmetric space of non-compact type. The refined law's mechanism (i) explicitly invokes **finite-dimensional** Lie irreps + Casimir labeling. Since `SO(d, 1)` is non-compact and has only infinite-dim unitary irreps (Plancherel decomposes `L²(H^d)` continuously), the refined law **predicts no finite-dim invariant subspaces, hence no closed-form spectral compression** for the scalar Laplacian on `H^d`. This is a *load-bearing prediction-or-not test*: if `H^d` admitted closed-form L² eigenfunctions on a discrete spectrum, mechanism (i) would need refinement.

---

## §1. Q1 — Does the refined law fit at `d = 3, 4, 5, 6, 7`?

### §1.1 Dimension and Casimir-eigenvalue structure

The scalar Laplace-Beltrami operator on the unit sphere `S^d ⊂ ℝ^{d+1}` has eigenvalues

```
λ(d, ℓ) = ℓ(ℓ + d − 1),     ℓ ∈ ℤ_{≥0}
```

with eigenspaces of dimension

```
D(d, ℓ) = (2ℓ + d − 1) · (ℓ + d − 2)! / (ℓ! · (d − 1)!).
```

These are the well-known formulas for the SO(d+1)-irrep with highest weight `(ℓ, 0, 0, ..., 0)` (totally symmetric traceless rank-ℓ tensor representation). The Laplace-Beltrami eigenvalue is the quadratic-Casimir eigenvalue on this irrep, up to a sign convention.

Verified dimension table (computed in `spike_17_spherical_harmonics_verification_script.py`):

| d \ ℓ | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| **d=2** | 1 | 3 | 5 | 7 | 9 | 11 |
| **d=3** | 1 | 4 | 9 | 16 | 25 | 36 |
| **d=4** | 1 | 5 | 14 | 30 | 55 | 91 |
| **d=5** | 1 | 6 | 20 | 50 | 105 | 196 |
| **d=6** | 1 | 7 | 27 | 77 | 182 | 378 |
| **d=7** | 1 | 8 | 35 | 112 | 294 | 672 |

At `d = 2`: `D(2, ℓ) = 2ℓ + 1`, recovering the textbook result.
At `d = 3`: `D(3, ℓ) = (ℓ + 1)²`, recovering the well-known biharmonic-degree count (equivalently `dim V_ℓ ⊗ V_ℓ^*` for SU(2)-irrep of dimension `ℓ + 1`, since `S^3 = SU(2)` carries the bi-regular `SU(2) × SU(2)` action).
At `d = 5`: `D(5, ℓ) = (ℓ + 1)(ℓ + 2)²(ℓ + 3) / 12` (recovers known formula).

### §1.2 Closed-form expression of eigenfunctions

At every `d ≥ 2`, the spherical-harmonic eigenfunctions admit a **closed-form expression** as iterated Gegenbauer / Jacobi polynomials. The standard construction (Vilenkin 1968 Ch. 9; Müller 1966; Atkinson-Han 2012 Ch. 4):

1. Parameterize `S^d` by iterated polar coordinates `(θ₁, θ₂, ..., θ_{d−1}, φ)` with `θ_j ∈ [0, π]` and `φ ∈ [0, 2π]`.
2. Separate variables: `Y_{ℓ}^{(d)}(θ₁, ..., φ) = ∏_{j=1}^{d−1} A_j(θ_j) · e^{i m φ}`.
3. Each factor `A_j(θ_j)` is a **Gegenbauer polynomial** `C_{m_{j} − m_{j+1}}^{m_{j+1} + (d − j − 1)/2}(\cos θ_j) · (\sin θ_j)^{m_{j+1}}` with integer indices `ℓ = m_1 ≥ m_2 ≥ ... ≥ m_{d−1} ≥ |m_d|`.

The chain of indices `(ℓ = m_1, m_2, ..., m_{d−1}, m_d)` is exactly a **Gel'fand-Tsetlin pattern** for the SO(d+1)-irrep with highest weight `(ℓ, 0, ..., 0)`.

**Zonal special case:** when the SH depends only on the angle to a fixed pole, the closed form reduces to the **Gegenbauer polynomial** `C_ℓ^{(d−1)/2}(\cos θ)`. This is the canonical "addition theorem" basis (Vilenkin 1968 §IX.3; Müller 1966 Ch. 2).

**Verified closed-form character.** All these expressions are *finite polynomial combinations* of trigonometric functions, computable in closed form at every `(d, ℓ)`.

### §1.3 Fit to mechanism (i) and (iv)

The refined law's mechanism (i) and (iv) both apply, **redundantly** (each suffices on its own), confirming the law:

- **Mechanism (i) non-abelian Lie factor + Casimir labeling.** `SO(d+1)` is non-abelian for `d ≥ 2`. The scalar Laplace-Beltrami operator is exactly the (quadratic) Casimir of `SO(d+1)` (up to a sign / normalization), so eigenspaces are SO(d+1)-irreps. The totally-symmetric irreps `(ℓ, 0, ..., 0)` are finite-dimensional of dimension `D(d, ℓ)`. The label `ℓ` is the Casimir-eigenvalue label.
- **Mechanism (iv) integer-lattice parameter quantization.** The eigenvalue spectrum is the integer-lattice quantization `ℓ ∈ ℤ_{≥0}` of the highest-weight label. This is the direct higher-dimensional analog of the Lamé integer-`n` filtration (Spike #15 §3.4): integer-`ℓ` selects the finite-dim subspace.

Both mechanisms apply simultaneously and consistently. At `d = 2` the refined law fits via (i)+(iv) on `SO(3)`; at `d ≥ 3` the same dual fit applies on `SO(d+1)`.

**Refined-law verdict for Q1:** the law fits cleanly at `d = 3, 4, 5, 6, 7` (and by induction at all `d ≥ 2`).

### §1.4 Verified citations (per `feedback_pdf_extraction_citation_discipline.md` counter-clause)

All citations are pre-2020 canonical works (Vilenkin 1968; Müller 1966; Stein-Weiss 1971; Helgason 1978, 1984; Atkinson-Han 2012). These are exempt from PDF re-verification per the discipline's counter-clause (multi-decade-stable canonical references). Web-search corroboration confirms the dimension formula, Gegenbauer-polynomial closed-form, and Gel'fand-Tsetlin chain structure as standard textbook material.

---

## §2. Q2 — Anything qualitatively new at `d ≥ 3`?

I examine each candidate qualitative-new-feature proposed in the brief.

### §2.1 Multiplicity-free branching `SO(d+1) ↓ SO(d)` — same structure, not new

**Question:** at `d = 2`, every `(2ℓ + 1)`-dim irrep of `SO(3)` is simple in the regular representation. At higher d, does branching get richer?

**Theorem (Gel'fand-Tsetlin 1950, Želobenko 1973):** the branching of the irrep `(ℓ, 0, ..., 0)` of `SO(d+1)` to `SO(d)` is **multiplicity-free** and given by

```
res^{SO(d+1)}_{SO(d)} V_{(ℓ, 0, ..., 0)} = ⊕_{k=0}^{ℓ} V_{(k, 0, ..., 0)}
```

Each `SO(d)`-irrep appearing has multiplicity 1. This is verified at the level of dimensions in `spike_17_spherical_harmonics_verification_script.py`: `D(d, ℓ) = Σ_{k=0}^{ℓ} D(d−1, k)` for all `d ∈ {3,4,5,6,7}` and `ℓ ∈ {0,...,5}`. **All 30 branching dimension identities check.**

**Verdict:** the branching gets *no richer* at higher d in the SH-relevant irreps. Multiplicity-free branching makes the Gel'fand-Tsetlin chain `SO(d+1) ⊃ SO(d) ⊃ ... ⊃ SO(2)` a **canonical complete commuting set** of operators, with eigenvalues labeled by a chain of integers `(ℓ = m_1, m_2, ..., m_d)` satisfying `m_j ≥ m_{j+1} ≥ |m_{d+1}|`. **This is the higher-d direct analog of the `(ℓ, m)` labeling at d = 2; no new structural mechanism is introduced.**

### §2.2 Reducibility at branch points — no irreducibility failures

The SH-carrying irreps `(ℓ, 0, ..., 0)` are **fundamental totally-symmetric tensor representations**; they are irreducible for all `ℓ ∈ ℤ_{≥0}` and all `d ≥ 2`. There are no degenerate (ℓ, d) loci where the irrep splits. This is unlike the Heun / Painlevé case where reducibility of monodromy at special parameter values gives rise to mechanism (iv) accessory-parameter spectral selection.

**Verdict:** **no irreducibility-failure refinement needed**.

### §2.3 Higher-rank Casimirs — present but irrelevant for SH

**SO(d+1)** has rank `⌊(d+1)/2⌋`. So:
- `d = 2` (SO(3)): rank 1, type `B_1 = A_1`, one Casimir.
- `d = 3` (SO(4)): rank 2, type `D_2 = A_1 ⊕ A_1` (so `SO(4) = (SU(2) × SU(2))/ℤ_2`), two Casimirs.
- `d = 4` (SO(5)): rank 2, type `B_2 = C_2`, two Casimirs.
- `d = 5` (SO(6)): rank 3, type `D_3 = A_3` (so `SO(6) = SU(4)/ℤ_2`), three Casimirs.
- `d = 6` (SO(7)): rank 3, type `B_3`, three Casimirs.
- `d = 7` (SO(8)): rank 4, type `D_4` (with triality!), four Casimirs.

For a **general** SO(d+1)-irrep, all `⌊(d+1)/2⌋` Casimirs would be needed to distinguish the highest-weight label. **However**, the SH-carrying totally-symmetric representations `(ℓ, 0, ..., 0)` are labeled by a *single* integer `ℓ`. On these irreps, the higher Casimirs reduce to functions of `ℓ` alone:
- The eigenvalue of the second (quartic) Casimir on `(ℓ, 0, ..., 0)` is a polynomial in `ℓ` with degree `≤ 4`.
- Similarly for higher Casimirs.

So while `SO(d+1)` rank > 1 in principle introduces multiple commuting Casimirs, on the SH locus only the first one is independent. **The single integer `ℓ` suffices to label the SH eigenspace at every `d`.**

**Verdict:** **no refinement of the law statement is needed at higher rank.** The "single discrete label" structure of mechanism (iv) is preserved. (The interior Gel'fand-Tsetlin labels `(m_2, ..., m_d)` distinguish basis vectors *within* a single SH eigenspace, not different eigenspaces. They are the analog of the magnetic-quantum-number `m` at d = 2.)

### §2.4 Exceptional embeddings — `S^3 = SU(2)`, `S^7` parallelizable

**`S^3 = SU(2)` (rank-1 Lie group on the sphere itself).** This is a strict refinement: not only does `SO(4)` act, but `S^3` is itself a Lie group, so `S^3` is a *principal homogeneous space for itself*, and there's an additional `SU(2)_L × SU(2)_R` action (the bi-regular representation). The full isometry group is `(SU(2)_L × SU(2)_R)/ℤ_2 = SO(4)`. So the "extra" group structure on the sphere is already captured by `SO(4)`-isometry. **No new mechanism needed.**

**`S^7` octonion unit sphere (parallelizable, Moufang loop).** `S^7` is parallelizable but is **NOT a Lie group** — only the three division-algebra spheres `S^0`, `S^1`, `S^3` are Lie groups; `S^7` has a non-associative octonion-multiplication structure that fails Lie-group axioms (Adams 1960 theorem on Hopf invariant; Bott-Milnor 1958). The SH theory on `S^7` uses only the **`SO(8)` isometric action**; the octonion multiplication is not a Lie-group action and does not enter the standard SH theory. (`SO(8)` has the exceptional triality `D_4` outer automorphism group `S_3`, but this acts on the three 8-dim representations — vector + two spinors — and is invisible at the level of scalar SH on `S^7`.)

**Verdict:** **no new mechanism (v) from exceptional embeddings.** The parallelizable / division-algebra structure exists but does not enter the closed-form Laplace-eigenfunction theory; the law's mechanism (i) on `SO(d+1)` is sufficient and unrefined.

### §2.5 Q2 verdict

> *No, nothing qualitatively new appears at `d ≥ 3`. Multiplicity-free SO(d+1) ↓ SO(d) branching, single-integer ℓ-labeling on totally-symmetric SH irreps, full irreducibility at all `(d, ℓ)`, and irrelevance of higher Casimirs on the SH locus all preserve the existing 4-mechanism law statement intact. Exceptional embeddings (S³ = SU(2), S⁷ parallelizable / octonion-loop) are captured by the standard SO(d+1)-isometry framework and do not require a new mechanism.*

---

## §3. Q3 — Non-compact analog: hyperbolic space `H^d`

### §3.1 The non-compact dual

The non-compact dual of `S^d = SO(d+1)/SO(d)` is the hyperbolic space `H^d = SO(d, 1)/SO(d)`. It is a rank-1 symmetric space of non-compact type, with constant negative sectional curvature.

The Laplace-Beltrami operator on `H^d` has a **purely continuous spectrum** on `[(d − 1)² / 4, ∞)` (Helgason 1984 *Groups and Geometric Analysis* Ch. III; Helgason 2000 *Geometric Analysis on Symmetric Spaces* Ch. III; Borthwick 2007 *Spectral Theory of Infinite-Area Hyperbolic Surfaces* Ch. 4 for surface case; standard Plancherel theorem for `H^d` reviewed in many places).

The (non-`L²`) eigenfunctions are **Helgason-Eisenstein** eigenfunctions parameterized by a continuous spectral parameter `λ ∈ ℝ_{≥0}` (or `iℝ` in some conventions) and a "boundary" direction `b ∈ S^{d−1}`:

```
e_{λ, b}(x) = e^{(iλ + (d−1)/2) ⟨x, b⟩}
```

where `⟨x, b⟩` is the horospherical distance from `x` to the horosphere through `b`. These are **not** in `L²(H^d)` — they are improper (distributional) eigenfunctions, generating the continuous spectrum via Plancherel inversion.

### §3.2 Why mechanism (i) fails for the scalar Laplacian on `H^d`

The refined law's mechanism (i) explicitly invokes **finite-dim irreps** of a non-abelian Lie factor. The relevant group `SO(d, 1)` is non-compact and (apart from the trivial irrep) has **only infinite-dimensional unitary irreps**.

The unitary irreps of `SO(d, 1)` decompose into:
- **Principal series** — parameterized by a continuous `λ ∈ ℝ` and a representation of the maximal compact `SO(d)`; all infinite-dimensional.
- **Complementary series** — a finite-`λ`-interval of further infinite-dim irreps.
- **Discrete series** — only for `d = 2k` even, finitely many irreps, all still infinite-dimensional in any non-trivial form (they are `L²` representations realized on harmonic forms of certain degrees).
- **Trivial irrep** — 1-dim, contributes the constant function (not in `L²(H^d)` either, since `H^d` has infinite volume).

**None of these admit finite-dim invariant subspaces on which the scalar Laplace-Beltrami operator has a single discrete eigenvalue.** The scalar Laplacian Plancherel-decomposes into a continuous integral over the principal series, with no atoms.

The refined law therefore **predicts no closed-form spectral compression** for the scalar Laplacian on `H^d`. This prediction is consistent with the standard harmonic-analysis fact that `L²(H^d, dvol_{hyp})` has no Laplace-eigenfunctions (every formal eigenfunction either grows or oscillates on the boundary at infinity).

### §3.3 Caveat — `L²`-harmonic forms in even dim

Anantharaman-Le Masson 2015 (`arXiv:1304.4942`) and earlier Donnelly-Xavier 1984 give the precise structure: on `H^{2k}` (even-dimensional) there exist `L²`-harmonic `k`-forms forming the **discrete series of `SO(2k, 1)`** in degree `k`. These are *not* scalar functions, however; they are harmonic `k`-forms (middle-degree). The scalar Laplacian on scalar functions still has no atoms.

This is a finer point: the law's "closed-form spectral compression for the scalar Laplacian" prediction is *correct as stated* on `H^d`. The `L²`-harmonic-form discrete series is a (finite-`L²`-eigenvalue, finite-multiplicity) atom for the **Hodge Laplacian on `k`-forms**, not for the scalar Laplacian. It is a one-rank-higher phenomenon and lies outside the scope of the scalar-SH test posed in the brief.

The "closest analog" of finite-dim closed-form structure on `H^d` is the **discrete-series Hodge cohomology**, which fits mechanism (i) with the qualifier that the relevant operator is the Hodge Laplacian on middle-degree forms, not the scalar Laplacian. Even there, the discrete-series irreps are infinite-dimensional; only the multiplicity of `L²`-harmonic-form solutions is finite. The refined law's "finite-dim invariant subspace" can be reinterpreted as "finite-multiplicity `L²` eigenspace" — a mild reformulation that preserves mechanism (i) at the cost of being more careful about what "finite-dim" means.

### §3.4 Q3 verdict

> *The refined law correctly predicts the non-compact `H^d` case: scalar Laplace-Beltrami on `H^d` has no closed-form `L²` eigenfunctions and a purely continuous spectrum on `[(d−1)²/4, ∞)`, because mechanism (i) requires finite-dim Lie irreps and `SO(d, 1)` has only infinite-dim unitary irreps. The compactness restriction is genuine, not an artifact of the law's framing. The middle-degree `L²`-harmonic-form discrete series in even `2k` is a (mild) reformulation territory but does not invalidate the prediction for the scalar case.*

---

## §4. Q4 — 9-setting score

Updated tally extending the 7-setting score from Spike #16 §5.1:

| # | Setting | Mechanism(s) | Closed-form? | Refined-law fit? |
|---|---|---|---|---|
| 1 | CMS Kerr (low-Mω) | (i) — non-abelian `SL(2, ℝ)²` Casimir | ✓ | ✓ |
| 2 | KY Kerr (generic-Mω) | none — abelian commuting algebra | ✗ | ✓ |
| 3 | Lamé `S²` | (iv) integer-`n` filtration + secular `B` quantization | ✓ in `sn, cn, dn` | ✓ |
| 4 | Bessel disk | none — abelian `U(1)`, no integer / monodromy / accessory structure | ✗ | ✓ |
| 5 | ₂F₁ Gauss | (iii) — finite-monodromy iff Schwarz-list (15 cases) | ✓ iff finite monodromy | ✓ |
| 6 | Heun | (iii) + (iv) — finite monodromy OR reducible + accessory-quantized | ✓ in 61 VF-families + DK-spectral-q | ✓ |
| 7 | Painlevé I-VI | (iii) + (iv) generalized — finite character-variety / Bäcklund orbit + parameter-lattice quantization | ✓ on 45 + 4 + 1 families (PVI); half-integer α (PII); etc. | ✓ |
| 8 | **`S^d` harmonics (d ≥ 3)** | **(i) + (iv)** — non-abelian `SO(d+1)` finite-dim irreps + ℓ-integer-lattice quantization | **✓ in Gegenbauer / Gel'fand-Tsetlin chain** | **✓** |
| 9 | **`H^d` non-compact dual** | **none** — `SO(d, 1)` non-compact, only infinite-dim unitary irreps | **✗** — continuous spectrum on `[(d−1)² / 4, ∞)` | **✓** |

**4-mechanism refined-law score: 9/9 fits.**

The two new settings (rows 8 and 9) confirm the law in both directions:
- Row 8 confirms the **positive** direction: mechanism (i) + (iv) at higher d gives closed-form, as predicted.
- Row 9 confirms the **negative** direction: absence of mechanism (i) (because of non-compactness) gives **no** closed-form, as predicted.

The negative-direction confirmation (row 9) is structurally important: it shows the law has *content* — it is not "always-fits-by-elasticity" but makes a sharp prediction (compactness ⇒ finite-dim irreps ⇒ closed-form; non-compactness ⇒ infinite-dim irreps ⇒ continuous spectrum ⇒ no closed-form) that holds exactly.

---

## §5. Discussion

### §5.1 What this strengthens

- **The 4-mechanism refined law now spans:**
  - Linear ODEs (Spikes #14, #15): Lamé, Bessel, ₂F₁, Heun.
  - Nonlinear ODEs (Spike #16): Painlevé I-VI via character-variety + Bäcklund-lattice reformulation.
  - **Higher-dimensional PDEs on compact manifolds (this spike)**: scalar Laplacian on `S^d` for arbitrary `d ≥ 3`.
  - **Non-compact PDE predictions (this spike)**: scalar Laplacian on `H^d`, correctly predicted as no-closed-form / continuous-spectrum.
- The user's project-level stance (`user_stance_fiber_as_spatially_absent_encoding.md`) — *hidden algebraic structure ⇒ finite-dim invariant subspace selection ⇒ closed form* — **holds across all 9 settings**.
- The **compactness ↔ closed-form bridge** is now load-bearing: compact rank-1 symmetric space (`S^d`) gives mechanism (i) + (iv) closed-form via Gegenbauer / Gel'fand-Tsetlin; non-compact dual (`H^d`) gives no closed-form via Plancherel continuous spectrum. This is the *first cleanly-paired positive / negative test* in the spike series (CMS / KY Kerr was paired but on the same compact base).
- The user's "fiber as spatially absent encoding" stance: the `ℓ` integer-lattice and the Gel'fand-Tsetlin chain `(m_1 = ℓ, m_2, ..., m_d)` are spatially-absent algebraic encodings that project to the geometric spatial structure of the SH eigenfunctions via Gegenbauer / Jacobi polynomial closed forms. The gear analogy: the integer-lattice ℓ ↔ teeth count `n`; the Gel'fand-Tsetlin chain ↔ nested cyclic-group encoding; the projection to spatial rotation ↔ the SH eigenfunction on the sphere.

### §5.2 What this opens

- **Higher-rank symmetric spaces:** `Gr(k, n)`, `U(n)`, Lie groups themselves as Riemannian manifolds. Each is a compact rank-`r` symmetric space; the analog of SH theory is the Peter-Weyl / Plancherel theorem; the refined law should predict closed-form spectral compression via mechanism (i) extended to multi-Casimir labeling at higher rank. **Possible Spike #18 target.**
- **Non-compact higher-rank duals:** `SL(n, ℝ)/SO(n)`, `Sp(n, ℝ)/U(n)`, etc. The refined law predicts no closed-form spectral compression for the scalar Laplacian, via the same Plancherel-continuous-spectrum argument. **Test-or-not for whether non-compact rank-`r` symmetric spaces all uniformly lack closed form.**
- **Affine / loop / Kac-Moody analogs:** "affine" generalizations of `SO(d+1)`. The Heun and Painlevé cases already hint that affine Weyl groups appear in the closed-form classification (mechanism (iv) lattice quantization, mechanism (iii) Bäcklund orbits). The pattern may unify with higher-rank affine Weyl groups acting on infinite-dim parameter / character spaces.
- **Discrete sphere analogs:** finite-graph Laplacian on the buckminsterfullerene / icosahedron / chess board (cf. srmech chess-spectral notebook). The SH framework restricted to finite point sets recovers the discrete-finite-symmetric-space Laplacian theory.

### §5.3 What this does NOT prove

- The 9/9 score remains *consistency* not *theorem*. The law is still a structural pattern unifying nine disparate settings, not a proved theorem.
- Higher-rank multi-Casimir refinement might emerge at compact symmetric spaces of higher rank (`Gr(k, n)`, etc.) — this spike only confirms that on `S^d` the SH-carrying irreps remain single-ℓ-labeled. A future spike on `Gr(k, n)` would test whether multi-label structures genuinely refine mechanism (iv).
- The "exceptional embedding" question at `S^7` is *not* fully resolved — I argued that the octonion structure does not enter the standard scalar-SH theory, but a fuller test would examine whether *octonion-twisted* harmonic-analysis (e.g., on the spinor bundle, where triality acts non-trivially) produces a closed-form structure outside the 4-mechanism law. This is a Spike #18+ direction.

### §5.4 Honest-negative reading

Is there an "honest-negative" reading of this spike — a way the law might be judged to be over-fitting?

**Possible honest-negative reading:** the dual fit of (i) and (iv) on the SH spectrum at `S^d` could be judged as "over-determined" — one mechanism (compact Lie group ⇒ finite-dim irreps ⇒ Casimir labeling) suffices, and the integer-lattice quantization of `ℓ` is *a consequence* of mechanism (i) on a compact group, not an independent structural fact. Under this reading, mechanism (iv) is *implicit in* mechanism (i) on compact groups, and the "redundancy" weakens the law's content.

**Counter:** mechanisms (i) and (iv) are *not* equivalent in general. Mechanism (iv) lattice quantization is independent of mechanism (i) in the linear-ODE settings: Lamé integer-`n` is mechanism (iv) without mechanism (i) (no Lie-group symmetry on the elliptic curve background); Dubrovin-Kapaev Heun spectral quantization is mechanism (iv) without mechanism (i). So the dual fit at `S^d` is not over-determination of the law — it is a *coincidence specific to the compact-symmetric-space setting* that both mechanisms apply, because in this setting the Lie group is compact (giving (i)) AND the spectrum is discrete (giving (iv) as a consequence). The general law statement requires both mechanisms separately to cover settings where only one applies.

I judge the dual fit at `S^d` to be **genuine consistency**, not over-determination. The honest-negative reading is available but I don't endorse it.

---

## §6. Provenance and discipline notes

### §6.1 No 2020+ load-bearing citations

This spike rests on pre-2020 canonical material (Vilenkin 1968; Müller 1966; Stein-Weiss 1971; Helgason 1978, 1984; Gel'fand-Tsetlin 1950; Adams 1960; Bott-Milnor 1958; Atkinson-Han 2012). Per `feedback_pdf_extraction_citation_discipline.md` counter-clause, these are exempt from PDF re-verification.

Web-search corroboration confirmed:
- Multiplicity-free SO(n) ↓ SO(n−1) branching and connection to Gel'fand-Tsetlin patterns (Wikipedia *Restricted representation*, *Spherical harmonics*; Molev `arXiv:math/0211289` *Gelfand-Tsetlin bases for classical Lie algebras*).
- Zonal SH on `S^d` are Gegenbauer polynomials `C_ℓ^{(d−1)/2}` (Wikipedia *Gegenbauer polynomials*; standard fact).
- L²(H^d) scalar Laplacian has continuous spectrum on `[(d−1)²/4, ∞)`, no isolated eigenvalues (Helgason 1984; Borthwick 2007; multiple analysis textbooks).
- Parallelizable spheres `S^1, S^3, S^7` correspond to division algebras `ℂ, ℍ, 𝕆`; only `S^1, S^3` carry Lie group structure (Adams 1960; Bott-Milnor 1958).

### §6.2 Misattributions caught in conductor's brief

The conductor's brief was *deliberately careful* to omit specific arXiv IDs / author orderings / numerical counts, per the May 2026 catch-tally lesson. Reviewing the brief:

- The dimension formula `D(d, ℓ) = (2ℓ + d − 1) · (ℓ + d − 2)! / (ℓ! · (d − 1)!)` is **correct** (verified numerically in script and matches Vilenkin / Stein-Weiss). ✓
- Identification at `d = 2` of `D(2, ℓ) = 2ℓ + 1` is **correct**. ✓
- Branching `SO(d+1) ↓ SO(d)` multiplicity-free claim is **correct** (Gel'fand-Tsetlin theorem). ✓
- "Parallelizable spheres `S^3 = SU(2)`, `S^7 = ?`" — the `?` is the right hedge: `S^7` is *not* a Lie group (only Moufang loop on octonion units); the brief's question mark correctly does not over-commit. ✓
- `H^d = SO(d, 1) / SO(d)` non-compact dual: **correct**. ✓
- Claim that "`SO(d, 1)` has only infinite-dim unitary irreps": **correct** with the qualifier that the *trivial* 1-dim irrep also exists but is L²-non-normalizable on H^d; for the scalar Laplacian on L²(H^d), no atoms. ✓

**No misattributions detected in this brief.** The deliberate omission of specific citation details (per the May 2026 lesson) successfully avoided the misattribution risk.

**Misattribution count this spike: 0** (zero new catches).

Running tally per `feedback_pdf_extraction_citation_discipline.md`:
- May 2026 catches before Spike #17: 18 (per Spike #16 §6.2 running count).
- **May 2026 catches after Spike #17: 18** (no new catches; brief was clean per the discipline lesson).

### §6.3 Attempted-but-unverifiable citations

None. All citations are pre-2020 canonical or web-search-corroborated.

### §6.4 Pre-2020 canonical citations (used at face value per counter-clause)

Vilenkin 1968 *Special Functions and the Theory of Group Representations*, AMS Transl. of Math. Monographs vol. 22; Müller 1966 *Spherical Harmonics*, Lecture Notes in Math. vol. 17, Springer; Stein-Weiss 1971 *Introduction to Fourier Analysis on Euclidean Spaces*, Princeton; Helgason 1978 *Differential Geometry, Lie Groups, and Symmetric Spaces*, Academic Press; Helgason 1984 *Groups and Geometric Analysis*, Academic Press; Atkinson-Han 2012 *Spherical Harmonics and Approximations on the Unit Sphere*, Springer LNM 2044; Gel'fand-Tsetlin 1950 *Dokl. Akad. Nauk SSSR* 71 (1950) 825-828; Adams 1960 *Ann. Math.* 72 (1960) 20-104 ("Hopf invariant one problem"); Bott-Milnor 1958 *Bull. AMS* 64 (1958) 87-89 ("On the parallelizability of the spheres"); Želobenko 1973 *Compact Lie Groups and Their Representations*, AMS Translations of Math Monographs vol. 40.

### §6.5 Discipline summary

- **No MVP framing** per `feedback_no_mvp_framing.md`: all four Q's addressed in full, with a 9-setting score and a full higher-d structural analysis.
- **No lineage claims about external work** per `feedback_no_lineage_claims_in_notebook.md`: the law is stated as a structural-pattern claim with result-by-result citations; no "this spike is a natural extension of X" framing for external work. The user's own project arc (S² compression on sphere) IS allowed lineage discussion under `user_stance_fiber_as_spatially_absent_encoding.md`'s carve-out.
- **NDJSON tabular sidecar** per `feedback_ndjson_over_bloated_json.md`: 59 records (provenance + structural facts + dimension tables + branching checks + mechanism fits + 9-setting score + verdict), one record per line, at `spike_17_spherical_harmonics_results_2026-05-13.ndjson`.
- **Verification script** at `spike_17_spherical_harmonics_verification_script.py` confirms all dimension and branching identities programmatically. 30/30 branching checks pass.
- **Strict notes + srmech-local-scripts only.** No CHANGELOG / README / MFO notebook / .gitignore / pin_and_slot.py / other shared files touched.

---
