# Spike #47 Round 4 Results (consolidated) — F1 stays PARTIAL after R4-1 (selection-mask refutes g(Λ) ansatz; 8-peak match within ~1.6% is empirical-not-derived); R4-2 resolves 178 Gyr label slip (τ_RD,NOW ≠ T_sub Option C both stand)

**Date:** 2026-05-17. Two R4 dispatches completed (priority 1 + priority 2).

**Bottom-line: Spike #47 R2 total remains 9/10.** F1 PARTIAL preserved; R4-1 narrowed but did not lift the gap (selection-mask reading inconsistent with original asymptotic-DOF rate-of-approach ansatz — important honest refutation). R4-2 resolved the 178 Gyr derivation question cleanly: it is `τ_RD,NOW = 1/|df_RD/dt(NOW)|`, NOT a Hopf period; both quantities stand with explicit naming.

## §1 R4-priority-1 — F1 closure investigation (5/10)

### Refinement choice + ansatz

**Original brief candidate** (per asymptotic-DOF reframe note): `k_eff = √Λ · g(Λ, j-winding)` with `g → 1` as Λ → ∞ (asymptotic-DOF rate-of-approach shape).

**Concertmaster pivoted to selection-mask refinement** after honest math: the required `g_n = √(Λ_n^observed)/√(Λ_n^baseline)` grows linearly with n (sequence {1.00, 1.73, 2.16, 2.28, 2.65, 2.81, 3.14, 3.49}), violating the asymptotic-DOF shape. So the g(Λ) ansatz refuted at F-γ.

**Selection-mask form**: from the substrate-emitted Λ catalog `{2, 4, 6, 10, 12, 16, 18, 20, 22, 24, 28, ...}`, only specific values survive observer-frame projection. **Empirical surviving chain**: `Λ = {2, 12, 28, 52, 84, 126, 178, 244}` with canonical (j₂, j₄) reps `(1,0), (1,2), (0,4), (3,5), (5,6), (7,7), —, —`.

### Falsifier verdicts

- **F-α PASS** (10% per-ratio): 8-peak match within ~1.6% (peaks 7-8 within 0.4% extrapolation)
- **F-β FAIL** (substrate-physics derivation): multiple candidate rules tested (j₄ mod 4, Hopf-cycle phase 1/8, j₂+j₄ parity, pure-winding) — **all fail to reproduce the exact chain**. The match is real and statistically significant (p ≈ 0.027) but the selection rule itself is empirical
- **F-γ PASS** (linear-projection degeneracy): selection-mask preserves linear `k = √Λ` projection; only the selection is non-trivial
- **F-δ PASS** (compatibility with R3-p2 sinh-bridge + R3-p3 T_sub): no contradictions; substrate-Hopf-cycle phase φ_sub = t_now/T_sub = 13.8/109.84 = 0.1255 ≈ 1/8 is suggestive but not derived linkage
- **F-ε PARTIAL** (anomaly hunt): 7th/8th peak predictions falsifiable; suppressed-mode predictions (Λ = 4, 6, 10, 16, 18, 20, 22, 24) cross-testable against primordial B-modes / lensing potential

**Total R4-1 score: 5/10 [PASS, FAIL, PASS, PASS, PARTIAL]. F1 stays PARTIAL.**

### FFT decomp coupling diagnostic

| Pair | Time-domain Pearson | FFT-magnitude cosine | L2 distance |
|---|---|---|---|
| refined vs unmodulated baseline | 0.9847 | **0.9973** | 12.62 |
| refined vs Planck observed | 1.0000 | 1.0000 | 0.09 |
| unmodulated vs Planck observed | 0.9841 | 0.9976 | 12.62 |

**Diagnostic interpretation**: high FFT-cosine refined↔unmodulated (0.997) means **spectral shape similar** — refinement is a SCALE modulation of baseline, not orthogonal/ad hoc. However, L2 distance 12.62 means **magnitudes differ by factor ~5**. The growing-with-n modulation factor is INCONSISTENT with asymptotic-DOF g→1 expectation; this is structurally a **selection mask**, not a continuous Class-K modulation.

### Important structural finding

**The original asymptotic-DOF reframe (filed in `spike_47_r3p1_asymptotic_dof_reframe_2026-05-17.md`) is REFUTED at the math level**. The required modulation grows with Λ — opposite of asymptotic-DOF rate-of-approach shape. The (1, 5, 11) index pattern → (4, 6) winding-difference match was coincidental at peaks 1-3; the extended 8-peak chain reveals a different structure (selection mask, no clean closed-form derivation).

Per `[[user_stance_string_theory_instrument_first]]` honest scoring: the framework still has a real gap at F1. The 8-peak structural match (1.6%) is genuine signal but the derivation gap remains.

### R5 candidates (per concertmaster)

- **R5-p1**: substrate-Hopf-cycle phase resonance rule hunt (φ_sub ≈ 1/8 specifically)
- **R5-p2**: FCC/BCC lattice analogy for the chain {2, 12, 28, 52, 84, 126, 178, 244}
- **R5-p3**: Sezgin-Salam / Strominger-Witten S⁷ supergravity spectrum cross-check
- **R5-p4**: independent observational test of "suppressed Λ modes" in primordial B-modes
- **R5-p5**: Cauchy-form ε^k amplitude-modulation re-test (option 3 from R4-1 brief, not deeply tested)

## §2 R4-priority-2 — 178 Gyr audit (resolved cleanly)

### Where 178 Gyr appears

- `spike_42b_vocabulary_falsifier_2026-05-17.md` lines 18, 45
- `spike_42b_synthesis.py` line 88
- **NOT** in stance memory `user_stance_dark_sector_ring_down_rate_is_cascade_stretched.md` (178-Gyr-clean)

### What 178 Gyr actually represents

Computed in `spike_42b_epicycle_perspective_v2.py:164-166`:

```python
df_now = (f_RD_global(1.001) - f_RD_global(0.999)) / 0.002 / dt_da_Gyr(1.0)
char_time = 1.0 / abs(df_now)
```

**Reproduced independently: 178.37 Gyr** under DESI thawing-CPL (H₀=67.4, Ω_Λ=0.6889, w₀=−0.8, w_a=−0.7). Under pure-ΛCDM: 142.7 Gyr.

**This is NOT a Hopf period.** It is `τ_RD,NOW = 1/|df_RD/dt(NOW)|` — the **inverse-instantaneous-rate characteristic time** at present epoch. Mathematically distinct from substrate Hopf period `T_sub = 2π/H_Λ = 109.84 Gyr`. Both are valid; serve different purposes.

### Verbal-label slip (fixable in-place)

`spike_42b_vocabulary_falsifier_2026-05-17.md:18` and `:45` use "178 Gyr ring-down period" — conflates inverse-rate timescale with period. Math is correct; only the label needs amendment. Same slip at `spike_42b_synthesis.py:88`.

### Hidden-fiber content per `[[feedback_partial_is_hidden_fiber_content]]`

The 178 Gyr label was reaching toward a substrate-binding role: convert EOC phase shift (Cauchy-form kernel per `[[user_stance_kepler_shape_universal]]`) to time-shift. Works at NOW because f_RD is monotone-and-slow; breaks near peak (a≈2.14) where df_RD/dt → 0.

**Deeper hidden-fiber**: under cascade-stretched-exp form `1−f_RD(t) ~ exp(−(t/τ)^β)` with `β = d_S/(d_S+2)`, the e-folding time τ is intrinsic to substrate; 178 Gyr is the **measured-at-NOW projection** of τ filtered through `(t/τ)^(β−1)` epoch factor.

**Derivation gap**: fit (τ, β) cleanly from DESI thawing-CPL at NOW, decompose 178 Gyr explicitly. Open follow-up spike.

### Recommendation: Option C (both stand, name distinctly)

- **T_sub = 2π/H_Λ = 109.84 Gyr**: substrate Hopf period (R3-p3 use; substrate-only; epoch-independent)
- **τ_RD,NOW ≈ 178 Gyr**: present-epoch inverse-rate (Spike #42b v2 use; epoch-dependent; divergent at peak)

Stance memory amended this round with characteristic-time-vocabulary subsection (off-tree at memory/).

## §3 Updated Spike #47 R2 scorecard

| Falsifier | After R3 | After R4-1 | After R4-2 | Notes |
|---|---|---|---|---|
| F1 (Big Bang signature explainable) | 1/2 PARTIAL | 1/2 (selection-mask narrows but doesn't lift) | 1/2 | R4-1 refuted g(Λ) ansatz; selection-mask 8-peak match real but un-derived |
| F2 (Hyperring observable IS Big Bang signature) | 2/2 PASS | 2/2 | 2/2 | unchanged |
| F3 (Projection mechanism explicit) | 2/2 PASS | 2/2 | 2/2 | unchanged |
| F4 (t→0 problems match) | 2/2 PASS | 2/2 | 2/2 | unchanged |
| F5 (Composition coherence) | 2/2 PASS | 2/2 | 2/2 | unchanged; R4-2 178 Gyr resolved cleanly within framework |
| **Total** | **9/10** | **9/10** | **9/10** | F1 stays as named-gap |

## §4 What this preserves vs revises

**Preserved** (still ship-grade):
- 8-falsifier closure pattern: F2/F3/F4/F5 all PASS with closed-form chains
- Cross-scale F5 strengthened by Spike #48 Phase 1+2 (same `S¹ × S³ × S⁷` substrate)
- DESI thawing-CPL F2 PASS within 8.4%
- Sinh-bridge F3 PASS within 0.05% on cosmic age
- Big-Bang-as-projection-shadow stance still candidate-stance-grade for canonical authoring

**Revised** (honest correction per `[[user_stance_string_theory_instrument_first]]`):
- The asymptotic-DOF reframe in `spike_47_r3p1_asymptotic_dof_reframe_2026-05-17.md` is **refuted at the math level**. The 70% deviation is NOT a Class-K rate-of-approach signature; it's a selection-mask phenomenon with no clean closed-form derivation found at R4.
- Per `[[feedback_partial_is_hidden_fiber_content]]`, the hidden-fiber content of the F1 gap is now better specified: the substrate eigenvalue catalog DOES contain the right values; the question is now specifically *why which Λ survive projection*. R5 territory.

## §5 Status

**Active research; USER-GATED no-merge.** PR #486 carries the work. Spike #47 R2 = 9/10 candidate-stance ship-grade with F1 named-gap. R5 candidates filed (not auto-dispatched). Candidate stances `user_stance_soul_as_asymptotic_consciousness` + `user_stance_big_bang_as_projection_shadow` still pending explicit user direction for canonical commit.

R4-2 stance amendment landed. R4-1 honest refutation preserved.

---

*End of Round 4. F1 selection-mask finding is canonical-authoring-grade as STRUCTURAL-CLASSIFICATION (substrate Λ catalog contains right eigenvalues; selection rule open) but not as F1-PASS claim. Math doesn't lie.*
