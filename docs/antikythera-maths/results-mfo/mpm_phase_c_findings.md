# MFO Phase C: Phase-N BIP HDC binding for λ=6 generation-block selection

**Date:** 2026-05-11 · **Phase:** C (concertmaster scope; cross-cutting between B.2 eigenspace structure + §II.8 gauge-quantum-number geometry + srmech HDC binding architecture)

## The load-bearing question

Phase B established that λ=6 (level-5 SG, dim 120) decomposes under D₃ as **22A + 18B + 40E**, hosting **18 candidate (1A + 1B + 1E) generation blocks** — far more than the 3 the framework needs. Phase C asks: does **principled** Phase-N BIP HDC binding — using only standard-model gauge quantum numbers (color, T₃, Y, generation), with no per-particle free integers — select among those 18 blocks uniquely per fermion?

This is the central srmech question: does the project's existing HDC instrument (cousin of chess BIP, ephemerides BIP, SkPhase9BIP, AudioPhase12BIP, doom Phase9BIP) resolve within-generation splitting that abstract-recurrence anchor fits could not?

## Verdict

**Principled HDC binding result: TAUTOLOGY — BIP-cosine identity-matches per QN but does not derive QN from geometry**

The raw cosine-assignment numbers look clean (9/9 unique, 9/9 QN-match), but the C.3b permutation stress test (all 720 within-generation table orderings tested) is the load-bearing diagnostic. Honest one-line summary:

- Raw cosine assignment: 9 fermions across 9 distinct blocks (of 18 candidates); 9/9 exact-QN matches.
- Permutation stress test: **720/720** within-gen QN-table orderings produce the SAME 9/9-unique outcome.
- **Interpretation:** because every permutation of the QN-table succeeds, the BIP-cosine is doing **identity-matching per QN** — it confirms that fermions and blocks with the same (color, T₃, Y, gen) signature bind to identical hypervectors, but does NOT derive QN from geometry. The geometric data (D₃-irrep + radial-variance ordering) supplies 18 ordered slots; the *labelling* of those slots by SM QN signatures is an exogenous rule, not a geometric consequence. λ=6 alone is geometrically sufficient to count 18 generation blocks, but not sufficient to derive which SM (color, T₃, Y, gen) goes into which block.
- Spearman ρ(block_idx vs mass-rank) = +0.9667 (p = 0.0000) — tests whether radial-variance rank correlates with observed mass ordering. Note: under the tautology, this number reflects only the *choice* of table ordering, not a derived geometric prediction.

## C.1 — Fermion hypervectors

Bipolar Phase-N BIP at D=512; coprime cyclic-roll shifts (67 / 7 / 31 / 11 / 47) for {color, T₃, Y, generation, block}. Bind via element-wise multiplication. Quantum numbers Y normalized to integer ×6; T₃ to ×2; standard SM conventions. Electromagnetic charge Q = T₃/2 + Y/12 verified per fermion (electron Q=-1, up Q=+2/3 (encoded as left-handed isospin partner: Q=-1/3 for the down-component of the L doublet; right-handed singlets as appropriate).

## C.2 — D₃ irrep projectors on the 120-dim λ=6 eigenspace

Standard projector formula P_ρ = (d_ρ/|G|) Σ_g χ_ρ(g) · ρ_V(g) within the 120-dim invariant subspace V. Image dimensions:

| irrep | dim | expected (Phase B) | found |
|:---|---:|---:|---:|
| A (trivial) | 1 | 22 | 22 |
| B (sign) | 1 | 18 | 18 |
| E (2D std) image | 2 | 80 (=40 pairs) | 80 |

✓ matches Phase B character-decomposition exactly.

**Anomaly C.A.1 (investigated, resolved):** initial design ordered irrep copies by L₂ centroid distance from SG centroid (S/3, S/3). This degenerated to ~0 for ALL A and B projector images (max |centroid_dist| < 1e-14 across all 22 A + 18 B copies). Reason: A is the trivial irrep (D₃-symmetric ⇒ centroid at SG centroid by construction); B is the sign irrep (also centroid-fixed). Centroid distance is geometrically incapable of discriminating copies after D₃-projection. **Resolution:** use radial-variance ⟨r²⟩ (also D₃-invariant, but second-moment NOT zero-by-symmetry). Observed range across 22 A copies: ~99-200; clean non-degenerate discriminator.

**18 generation-blocks indexed by radial-variance rank:** order each irrep's copies by ⟨r²⟩ from SG centroid. Block k pairs k-th A copy with k-th B copy with k-th E pair (k = 0, ..., 17). Extra 4 A copies + 22 E pairs sit outside the 18 blocks. The 18-block count is geometrically derived (min(22, 18, 40) = 18 from D₃ irrep multiplicities); the radial-variance ordering is deterministic.

**Block-QN inference (deterministic, rule-based, no tuning):** block_rank → (generation = (rank // 6) + 1, (color, T₃, Y_×6) from a fixed table of 6 within-generation positions covering {lepton-L, lepton-R, down-L, down-R, up-L, up-R}). This produces 18 distinct (color, T₃, Y_×6, generation) signatures, exactly matching the 18 block candidates from Phase B.

## C.3 — Cosine assignment

Cosine matrix (9 fermions × 18 blocks) computed with QN-only block hypervectors (no block-rank tag baked into the block hv). Argmax per fermion:

| fermion | mass (GeV) | obs-QN (color, T₃×2, Y×6, gen) | assigned block | inferred block-QN | cos(best) | cos(gap) | QN match? |
|:---|---:|:---|---:|:---|---:|---:|:---:|
| electron | 0.000511 | (0, -1, -6, 1) | 0 | (0, -1, -6, 1) | +1.000 | +0.914 | ✓ |
| up | 0.0022 | (3, +1, +2, 1) | 4 | (3, +1, +2, 1) | +1.000 | +0.938 | ✓ |
| down | 0.0047 | (3, -1, +2, 1) | 2 | (3, -1, +2, 1) | +1.000 | +0.938 | ✓ |
| strange | 0.095 | (3, -1, +2, 2) | 8 | (3, -1, +2, 2) | +1.000 | +0.875 | ✓ |
| muon | 0.1057 | (0, -1, -6, 2) | 6 | (0, -1, -6, 2) | +1.000 | +0.914 | ✓ |
| charm | 1.275 | (3, +1, +2, 2) | 10 | (3, +1, +2, 2) | +1.000 | +0.875 | ✓ |
| tau | 1.777 | (0, -1, -6, 3) | 12 | (0, -1, -6, 3) | +1.000 | +0.930 | ✓ |
| bottom | 4.18 | (3, -1, +2, 3) | 14 | (3, -1, +2, 3) | +1.000 | +0.875 | ✓ |
| top | 173.0 | (3, +1, +2, 3) | 16 | (3, +1, +2, 3) | +1.000 | +0.875 | ✓ |

**Summary of C.3:**
- 9 unique blocks used across 9 fermions (one-to-one).
- 9 / 9 fermion-block QN match (block infers the right (color, T₃, Y, gen) signature).

## C.3b — Permutation stress test (anomaly self-check)

**Concertmaster discipline:** the 9/9 result is suspiciously clean. If the BIP cosine assignment is *truly* selective, only the specific within-generation QN-table ordering (lepton-L, lepton-R, down-L, down-R, up-L, up-R) should succeed; other permutations should produce many-to-one assignments. If many permutations succeed, the test is tautological (BIP-cosine is just identity-checking).

Tested all 720 = 6! permutations of the within-generation block-QN table. Results:

- Permutations achieving 9/9 unique blocks AND 9/9 exact-QN matches: **720** of 720.
- Permutations achieving 9/9 unique blocks (any QN match): **720** of 720.
- Permutations achieving ≥5/9 QN matches: **720** of 720.

**Stress-test verdict: TAUTOLOGY confirmed.** Many permutations achieve 9/9, meaning the BIP-cosine isn't distinguishing the right from the wrong ordering — every QN signature finds its own block trivially. The within-generation QN-table is the residual arbitrariness Phase C surfaces honestly.

## C.4 — Mass prediction at λ=6 alone

All 18 blocks live at the **same eigenvalue λ = 6**. Therefore, any scale fit predicted_log_m² = 6/S yields **the same mass for every fermion** — total error 104.505 for any S, vs the optimum S_centroid = 1.064 which produces total error = 104.505.

This is **expected** — λ=6 alone is the wrong eigenvalue to fit the mass hierarchy. λ=6 hosts generation/within-generation structure (the 18 blocks); mass-magnitude information lives in the full spectrum (Phase B's gap-anchored fit (c) achieves total error 0.012; (d) achieves 0.319). Phase C is testing block-LABELLING, not mass-MAGNITUDE.

**Structure check via Spearman ρ:** block-rank vs mass-rank correlation = +0.9667 (p = 2.155e-05). The number is high, but see Anomaly C.A.3 — under the C.A.2 tautology, this correlation reflects only the *chosen* QN-table ordering (we put lepton-L first within each generation and the lightest fermion in each generation IS lepton-like; this is correlation by table-choice, not by geometric derivation). Honest interpretation: ρ does not measure a derived prediction here.

## Anomalies investigated

- **Anomaly C.A.1 — centroid-distance degeneracy under D₃-irrep projection.** Centroid distance from SG centroid (S/3, S/3) is identically 0 for all 22 A copies and all 18 B copies (numerical: max |centroid_dist| < 1e-14). Reason: A is the trivial irrep (necessarily centroid-symmetric); B is the sign irrep (also centroid-fixed under D₃). Centroid cannot distinguish copies within an irrep image; this would make the radial-rank ordering arbitrary. **Resolution:** use radial-VARIANCE ⟨r²⟩ instead — also D₃-invariant (irrep-preserving), but a second-moment observable that varies meaningfully (~99-200 across 22 A copies, ~103-? across 18 B). The corrected ordering IS a genuine geometric invariant of the eigenstructure.

- **Anomaly C.A.2 — Permutation stress test reveals BIP-cosine tautology.** The principled-BIP claim was: rule-based block-QN inference (no per-particle tunable integers, vs Gemini's 9 free (s1_n, cp2_k) pairs in cp2_assignment) selects 1-of-18 blocks per fermion principally. Stress test: 720 = 6! permutations of the within-generation 6 QN positions ({lepton-L, lepton-R, down-L, down-R, up-L, up-R}) ALL produce 9/9 unique-block 9/9 QN-match outcomes. The BIP-cosine machinery has the property that two hypervectors with identical (color, T₃, Y, gen) signatures cosine-match at +1.0; therefore, once the QN-table contains all 9 SM fermion signatures (in any order), each fermion finds its own match trivially. The geometric ordering (radial-variance) is NOT entering the binding — only the QN-set membership is. **BIP-cosine alone cannot derive which (color, T₃, Y, gen) signature lives in which geometric block.**

- **Anomaly C.A.3 — Spearman ρ = +0.9667 (strong, p=2.155e-05).** Block-radial-variance rank correlates with mass ordering, BUT under the tautology this only reflects the *choice* of QN-table ordering (lepton-L first → low mass first; we chose this; geometry didn't pick it). Under a permuted table, the same fermions would land on different blocks with different rank-order, and ρ would change accordingly. The ρ value is an artifact of table choice, not a derived prediction.

## What stands / falls / opens

**Stands:**
- The 22A + 18B + 40E D₃ decomposition of λ=6 (Phase B re-verified here via independent projector construction; characters match exactly).
- The 18 candidate generation-block COUNT is geometrically derived (min(22, 18, 40) = 18 from D₃ irrep multiplicities). This is a real structural prediction of the SG-pre-gasket geometry, matching the SM 18 charged-fermion-component count (3 gens × 6 = 18 if we count {lepton-L, lepton-R, down-L, down-R, up-L, up-R}).
- Radial-variance ⟨r²⟩ is a non-degenerate D₃-invariant geometric ordering on irrep copies — it imposes a deterministic rank on the 22 A, 18 B, 40 E-pairs without per-particle tuning.
- The Phase-N BIP architecture works as designed: hypervectors with identical (color, T₃, Y, gen) BIP-cosine to +1.0; orthogonality between distinct QN signatures observed (off-diagonal cosines all <0.13 in absolute value; see C.3 matrix).

**Falls:**
- The claim that 'principled HDC binding alone selects 1-of-18 blocks per fermion' falls under the C.A.2 stress test. BIP-cosine is identity-matching on QN, not QN-derivation from geometry. The 720 permutations of within-gen QN-table all succeed equally.
- λ=6 alone DOES NOT predict mass magnitudes (eigenvalue degenerate; all blocks at λ=6 ⇒ identical predicted_log_m² for any S_opt).
- The Spearman ρ = +0.97 number is contaminated by table-choice (see C.A.3); not a derived geometric prediction.

**Open (what additional structure is needed):**
- **The within-generation 6-position labelling must come from non-D₃-invariant geometric structure.** Candidates: (i) E-pair orientation under a *specific* D₃ reflection (would distinguish T₃ sign? the E irrep IS the 2D-mixing irrep; the two members of each E pair carry the SU(2) doublet structure naturally). (ii) Spatial support on the 3 corner subtriangles vs interior (color singlet ↔ corner-vanishing vs color triplet ↔ corner-supported, since CP² color = 0 lepton, color = 12 first non-trivial quark mode). (iii) Higher D₃ moments (⟨r⁴⟩) or non-isotropic centroid moments (mass dipole under reflections).
- **Mass-magnitude prediction across generations requires the wider λ-spectrum, not λ=6 alone.** This is Phase D scope: SG × CP² × S¹ product manifold (notebook §IV.4). SG provides the generation/block COUNT (Phase C confirmed: 3 × 6 = 18); CP² provides color anchor (eigenvalues 0, 12, 32, 60, ...); S¹ provides the within-generation mass-ratio fine structure (R₁, R₂, R₃ radii per §III.3).
- **Fermata for the conductor:** Phase C concertmaster recommends Phase D dispatch should NOT try to extend BIP-binding alone — extend with the product-manifold computation (CP² eigenvalue assignment + S¹ radius fit per generation) and use BIP-binding only at the integration layer (combining SG block-membership × CP²-bucket × S¹-mode into a final hypervector that DOES have geometric content per axis).
