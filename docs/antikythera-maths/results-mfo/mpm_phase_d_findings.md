# MFO Phase D: Product-manifold mass prediction (SG × CP² × S¹)

**Date:** 2026-05-09 · **Phase:** D (downstream of A spectrum, B mass-fit, C QN-binding)

## The load-bearing question

Notebook §IV.4 predicts: product geometry F × CP² × S¹ inherits large-scale gaps from F (between generations), fine structure from gauge manifolds (within generations), and multiplet degeneracies from gauge group reps. **Does a principled gauge-quantum-number-to-mode rule (no per-particle freedom) on top of the Phase B (d) SG assignment, with CP² × S¹ as fine-structure factors, beat the SG-only baseline?**

## Setup

- **λ_total = λ_SG + c_CP² · λ_CP² + λ_S¹**, with electron subtracted.
- λ_SG from Phase B (d) mult-aware gap-anchored fit (fixed, not refit).
- λ_CP² rule (single, fixed): lepton (color singlet) → 0; quark (color triplet) → 12 (smallest nontrivial Fubini-Study eigenvalue).
- λ_S¹ = n² / R² with several principled n(QN) rules tested:
  - R1_6Q: n = round(6·Q)
  - R3_Y6: n = Y × 6 (right-handed singlet hypercharge)
  - R4_zero: n = 0 (degeneracy check, no S¹)
  - R5_2Q: n = round(2·Q)
  - R6_3Q: n = round(3·Q)
  - R7_Y3: n = Y × 3
  - R2_3times_2T3: n = 0 for R-singlets (degeneracy)

- **3 global parameters** fit jointly: S (scale), R (S¹ radius), c_CP² (CP² weight). No per-particle freedom.

## Results

| rule | S | R | c_CP² | total_err | vs Phase B (d) |
|:---|---:|---:|---:|---:|:---|
| **baseline: Phase B (d) SG-only** | 0.5467 | – | – | **0.3190** | – |
| baseline: Gemini cp2_assignment (18 per-particle params) | – | – | – | 1.262 | – |
| R5_2Q | 0.5716 | 2.2089 | 0.0709 | 0.5941 | 86.2% worse |
| R4_zero | 0.5716 | 0.3800 | 0.0196 | 0.5941 | 86.2% worse |
| R2_3times_2T3 | 0.5716 | 0.3800 | 0.0196 | 0.5941 | 86.2% worse |
| R6_3Q | 0.5745 | 5.6818 | 0.0380 | 0.6517 | 104.3% worse |
| R7_Y3 | 0.5745 | 5.6818 | 0.0380 | 0.6517 | 104.3% worse |
| R1_6Q | 0.5803 | 6.3000 | 0.0789 | 1.0551 | 230.7% worse |
| R3_Y6 | 0.5803 | 6.3000 | 0.0789 | 1.0551 | 230.7% worse |

## Verdict

**Best principled rule (R5_2Q) DOES NOT BEAT the SG-only baseline (total_err 0.5941 vs 0.3190; product-manifold fit is 86.2% WORSE than SG-alone).**

No principled S¹ harmonic rule, combined with the fixed color → CP² rule, improves the SG-only baseline. The §IV.4 'fine structure from gauge manifolds' prediction is **not borne out** by L=5 SG + first-CP² mode + simple-rule S¹ with 3 global parameters. Either the per-particle rules are wrong, the SG λ-assignment (Phase B (d)) is already absorbing the fine structure, or the product-spectrum addition λ_F + λ_CP² + λ_S¹ is the wrong combination operation.

**Degeneracy check:** rule R4_zero (n_S¹ ≡ 0 for all fermions) lands at total_err = 0.5941 with c_CP² = 0.0196. If a non-zero S¹ rule produces total_err near this value, the optimizer is collapsing S¹ out (R → ∞ or n → 0 effective). Best non-zero S¹ rule: R5_2Q at 0.5941 (+0.0000 vs R4_zero 0.5941). **Gap < 0.02 — S¹ is being optimised away.** The data does not demand the S¹ factor.

## Per-fermion residuals for best rule

Best rule: **R5_2Q**, S = 0.5716, R = 2.2089, c_CP² = 0.0709.

| fermion | obs mass (GeV) | pred mass (GeV) | residual log m² | within ±30% mass | Q | color |
|:---|---:|---:|---:|:---:|---:|---:|
| electron | 0.000511 | 0.000511 | +0.0000 | ✓ | -1.000 | 0 |
| up | 0.0022 | 0.002963 | +0.2586 | ✗ | +0.667 | 3 |
| down | 0.0047 | 0.004809 | +0.0200 | ✓ | -0.333 | 3 |
| strange | 0.095 | 0.07637 | -0.1896 | ✓ | -0.333 | 3 |
| muon | 0.1057 | 0.2151 | +0.6172 | ✗ | -1.000 | 0 |
| charm | 1.275 | 1.2 | -0.0526 | ✓ | +0.667 | 3 |
| tau | 1.777 | 1.306 | -0.2675 | ✗ | -1.000 | 0 |
| bottom | 4.18 | 4.766 | +0.1140 | ✓ | -0.333 | 3 |
| top | 173 | 145.5 | -0.1504 | ✓ | +0.667 | 3 |

## Residual decomposition by quantum number

- Lepton residuals (electron, muon, tau, n=3): mean = +0.1166, |RMS| = 0.3884
- Quark residuals (n=6): mean = -0.0000, |RMS| = 0.1536
- Up-type quark residuals (u, c, t): mean = +0.0185, |RMS| = 0.1754
- Down-type quark residuals (d, s, b): mean = -0.0185, |RMS| = 0.1282

## What this means for notebook §IV.4

**Status update suggestion for §IV.4:** the 'fine structure from gauge manifolds' claim is **not vindicated** by L=5 SG + first-CP² mode + simple charge→S¹ rules with 3 global parameters. The SG λ-assignment already saturates the available mass-magnitude information; adding CP² × S¹ with simple principled rules does not improve the fit. Either the framework needs (i) more CP² modes per fermion, (ii) per-fermion S¹ radii (breaking the 'single S¹' assumption), or (iii) a different combination operation (multiplicative rather than additive) — all of which dilute the §IV.4 prediction's principled character.

## Anomaly authority

- If R4_zero (n_S¹ ≡ 0) ties the non-zero rules: S¹ is being optimised away. Reported in the degeneracy-check paragraph above.
- If c_CP² → 0 in the optimum: CP² is being optimised away. Check the best-fit c_CP² value above.
- The per-fermion SG λ from Phase B (d) is held fixed in Phase D — this is the **multiplicity-aware mult-anchored** Phase B fit, framework-honest. We did NOT re-search SG assignments; if we did, we'd be re-fitting Phase B inside Phase D and the comparison would be unfair.
