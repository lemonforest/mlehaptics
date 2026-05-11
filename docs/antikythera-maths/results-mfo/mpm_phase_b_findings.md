# MFO Phase B: Direct-graph spectrum — mass-fit, λ=6 generation probe, d_S flow

**Date:** 2026-05-11 · **Phase:** B (downstream of Phase A direct-graph eigenvalues)

## B.1 — Mass-fit redo against direct-graph spectrum (level 5)

1-parameter scale-only fit `predicted_log10(m²/m_e²) = mapped_eigenvalue / S` with nearest-eigenvalue assignment per fermion. Four variants tested.

| variant | S_opt | total quad error | mean log err/fermion | n unique eigvals used |
|:---|---:|---:|---:|---:|
| (a) direct, full distinct (72), no-mult | 0.0280 | 0.000753 | 0.009146 | 8 |
| (b) direct, full distinct (72), mult-aware | 0.0280 | 0.000761 | 0.009195 | – |
| (c) direct, gap-anchored, no-mult | 0.0180 | 0.012193 | 0.036807 | 2 |
| (d) direct, gap-anchored, mult-aware | 0.5467 | 0.319014 | 0.188271 | – |
| **baseline: P3 SG level 5 abstract recurrence** | 0.4707 | 0.4213 | 0.2164 | – |
| baseline: level 4 abstract recurrence | – | 0.5624 | 0.2500 | – |

**B.1 verdict:**

- Variant (a): S_opt squeezes very small (S≈0.0280); all 9 fermions collapse onto 8 unique eigenvalues in the dense low-lying region. The tiny error (0.0008) is a **degenerate squeezing pathology**, not a meaningful fit — multi-fermion-per-eigval collapse is unphysical. Discard as a fit-quality claim.
- Variant (b) on full distinct spectrum: mult-aware constraint prevents the squeeze in principle, but with 72 distinct eigenvalues and 9 fermions the capacity is unused. S_opt = 0.0280, total error = 0.000761. BEATS abstract baseline (0.4213).
- **Variant (c) — gap-anchored, apples-to-apples with the abstract-recurrence anchor fit**: S_opt = 0.0180, total error = 0.0122, mean log err = 0.0368. BEATS abstract recurrence baseline (0.4213, 0.2164); ratio = 0.029.
- Variant (d) — gap-anchored + mult-aware (framework-honest): S_opt = 0.5467, total error = 0.3190, mean log err = 0.1883. BEATS abstract baseline; ratio = 0.757.

Variants (a)/(b) on the full 72-eigenvalue distinct spectrum produce trivially small errors via squeezing into the dense low-λ region — they are **fit-by-collapse pathologies**, not informative. Variants (c)/(d) on gap-anchored eigenvalues are the apples-to-apples comparison with the abstract-recurrence baseline.

## B.2 — λ=6 eigenspace as candidate three-generation signature (level 5)

λ=6 has multiplicity **120** at level 5 (NDJSON-verified; Phase A findings.md prose erroneously stated 'mult 5 at level 5', but the ndjson record and the findings-table both correctly recorded mult=120). Built D₃ permutations on the integer-lattice coordinates (verified r³ = e and σ² = e by exact integer match) and computed the trace character χ of the rep on the 120-dim eigenspace.

| class | members | χ measured |
|:---|:---|---:|
| e (identity) | {e} | +120.0000 |
| rotation | {r, r²} | -0.0000 |
| reflection | {σ₀, σ₁, σ₂} | +4.0000 |

Irrep decomposition (D₃ has 1D-trivial A, 1D-sign B, 2D-standard E):

- n_A (trivial) = +22.0000 → rounded **22**
- n_B (sign)    = +18.0000 → rounded **18**
- n_E (2D std)  = +40.0000 → rounded **40**

Dim check: 22·1 + 18·1 + 40·2 = 120 (must equal 120).  ✓ CLEAN INTEGER DECOMPOSITION

**B.2 verdict:** the 120-dim λ=6 eigenspace decomposes cleanly into D₃ irreps: **22A + 18B + 40E**. χ_e = 120 (subspace dimension), χ_rot = 0 (rotations leave no fixed eigendirection), χ_refl = 4 (a small residual reflection-symmetric net). The χ values are integers to numerical precision, so the eigenspace is **a clean D₃-equivariant subspace, not a boundary artifact**.

For three generations under the §IV.5 interpretation, one natural 'generation block' is (1A + 1B + 1E) = 4-dim — a triplet of symmetric, sign, and 2D-mixing modes. The λ=6 eigenspace alone hosts min(22, 18, 40) = **18 complete generation blocks** (plus excess: 4 extra A, 0 extra B, 22 extra E modes). This is **far more than three** — the eigenspace carries enough representation theory for 30+ generation triplets. 

**Interpretation:** λ=6 is the *interior-vertex localised-mode eigenspace* (Fukushima-Shima 1992 §2 pre-localised eigenfunctions; on a level-5 SG with 360 interior-triangle corner vertices, the localised modes form a large degenerate eigenspace). Its D₃ irrep multiplicities (22, 18, 40) reflect how the 120 localised modes split under the global D₃ symmetry — they are a clean equivariant decomposition of the interior-localisation eigenspace, not specifically a three-generation signature. **The framework's §IV.5 three-generation claim would need to pick out *one* (1A + 1B + 1E) block from the 18 candidates, with the selection coming from additional structure (CP² or S¹ factor in the product manifold, or HDC binding). λ=6 alone is necessary but not sufficient.**

## B.3 — d_S(σ) flow, fine σ grid (200 pts log-spaced 1e-2 to 1e3)

- d_S theory = 2 ln 3 / ln 5 = 1.3652
- d_S peak (200 pts) = 1.8398 at σ = 5.4159e-01
- d_S peak (400 pts) = 1.8403
- |Δ peak| on grid doubling = 0.0005
- plateau mean = 1.3288564144660804
- d_S at large σ (IR) = 0.0732  (drops back toward 0 as only zero mode survives on finite graph)

**B.3 verdict:** the d_S(σ) curve rises through a transient peak, settles into a plateau matching the SG theoretical value, then rolls off toward 0 as IR is reached — i.e. the curve IS non-monotonic in the [UV → plateau → IR] sense, but the peak is a transient crossover, not a separate physical feature. The peak's position and amplitude are stable on grid doubling (Δ = 0.0005), so it is a real feature of the finite-pre-gasket spectrum, NOT a σ-grid discretisation artifact. The peak is genuinely a real overshoot above the plateau before settling.

## Anomalies investigated

- **Phase A multiplicity prose error:** Phase A findings.md said 'λ=6 carries multiplicity 5 at level 5'. The actual multiplicity (level 5) is **120** (level 3: 12; level 4: 39; level 5: 120 — verifiable from mpm_phase_a_eigenvalues.ndjson). The corresponding Phase A summary table correctly stated 'max multiplicity 120 at level 5'. The prose statement 'multiplicity 5' was an inference error not supported by the NDJSON. Phase B uses the correct multiplicity throughout.
- **B.1 squeezing pathology:** unconstrained nearest-eigenvalue fit (variants a/b) drives S → 0.028, collapsing all fermions onto 8 eigenvalues near 0. The trivially small error is not informative. Gap-anchored fits (variants c/d) avoid the worst of this by removing dense low-λ accumulation points; (c) still squeezes mildly (S≈0.018 onto only 2 unique anchors), (d) with multiplicity constraint settles at S ≈ 0.547 and is the framework-honest comparison. (d) beats the abstract-recurrence baseline by ~24% in total error.
- **B.2 D₃ decomposition integrality:** χ values are exactly (+120, -0, +4) → irrep multiplicities (22, 18, 40) integer to machine precision, dim check 120 = 120. The eigenspace is a CLEAN D₃-equivariant subspace, not a numerical degeneracy artifact. Combined with the Fukushima-Shima pre-localised interpretation, λ=6 IS the interior-vertex localised-mode eigenspace under global symmetry.
- **B.3 peak stability:** the d_S peak position and amplitude are stable on grid doubling (200→400 σ-points, |Δ peak| = 0.0005). It is a real feature of the finite pre-gasket spectrum (overshoot before settling into the SG plateau), not a numerical artifact. Boundary-localised modes contribute when σ is comparable to the boundary length, locally enhancing the apparent dimension above the bulk SG value.
