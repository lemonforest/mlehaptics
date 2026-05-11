# Phase F — Conductor synthesis

## MFO L=5 SG × CP² × S¹ candidate — MPM verdict 2026-05-11

Tested via 4-phase srmech-native orchestration (sparse-integer graph-Laplacian + Phase-N BIP HDC + product manifold + principled gauge-quantum-number rules). Phase E (CKM) skipped as predictably downstream-dependent. Phase F is the conductor's synthesis, not new computation.

## Verdict

**Framework's central computation §XIII.1 remains OPEN.** The specific L=5 SG × CP² × S¹ candidate is falsified at multiple levels under MPM-honest principled fitting. Real structural findings stand (notably the 18-block geometric count); mass-magnitude closure not achieved.

## What stands (MPM-verified, not fit)

1. **L=5 SG direct-graph spectrum**: 366 vertices, 729 edges, 72 distinct eigenvalues in [0,6]. Multiplicities sum to |V_5|; high-multiplicity localised modes match Fukushima-Shima 1992. Closed-form anchor eigenvalues (5−√17)/2 and (5+√5)/2 reproduce abstract-recurrence values to machine precision.

2. **Direct-graph fit beats abstract recurrence by 24%** under framework-honest multiplicity-aware constraints (S=0.547, total_err=0.319 vs abstract 0.421). Modest improvement; both leave within-generation residuals.

3. **18-block geometric count from D₃ representation theory.** λ=6 eigenspace dim 120 decomposes as 22A + 18B + 40E (integer-exact); min(22, 18, 40) = 18 candidate (1A + 1B + 1E) generation blocks. **SM has 3 generations × 6 charged-fermion components per generation = 18.** Match exact, count-as-structural-prediction (not fit-parameter).

4. **Generation-degeneracy structure**: G1 u/d at 0.4384, G2 s/μ at 1.356/1.377, G3 c/τ/b at 2.0, t at 3.618 — qualitative match per notebook §IV.5 three-fold self-similarity prediction.

5. **Strange + muon mass to ~1% from 1-parameter SG fit**. Notable for any first-principles framework but doesn't extend to full SM.

6. **Non-monotonic d_S(σ) flow on direct-graph SG**: peak 1.84 at σ≈0.54, plateau 1.329 vs theory 1.365 (3% finite-size error), peak stable to Δ = 5×10⁻⁴ under grid doubling. SG alone — not the full product-spectrum number §V.4 predicts.

7. **Reference provenance clean**: Baptista (×2), Ibarra-Singh-Vempati, Teplyaev, Hinz-Teplyaev all real and correctly cited (modulo minor framing corrections — Kosmann derivative attribution, Singh missing).

## What falls (MPM-falsified)

1. **Gemini gauge_couplings α₃(M_Pl) = −0.029**: sign error in formula. Textbook 1-loop gives +0.019. Implementation bug.

2. **Phase-N BIP HDC binding alone derives QN→generation-block (TAUTOLOGY verdict)**. 720/720 permutations of within-generation QN table produce identical 9/9 success — BIP-cosine is identity-matching same-QN hypervectors, not geometric derivation. BIP-alone is structurally insufficient.

3. **L=5 SG × CP² × S¹ + principled rules reproduces SM mass spectrum (FALSIFIED at 3 global parameters)**. n_S¹=6Q rule with global S, R, c_CP² gives total_err 0.594 — 86% WORSE than 1-param SG-only fit (0.319). Optimizer collapses S¹ out (R4_zero with n_S¹≡0 ties exactly). The principled rules push fermions away from their already-good SG-only positions.

4. **Spectral dimension peak ~7.34 (Gemini)**: actually 1.84 for SG alone per direct heat-kernel computation. Gemini may have intended a SG+S¹+CP² total but the published number doesn't separate contributions.

5. **"Glass Box is Open" / "Glass Box is Universal" rhetorical closes**: not supported by data. Every load-bearing claim either fails (gauge RG sign), partially holds with caveats (mass match), or stands only as qualitative pattern (generation structure).

## Open recommendations for future extension

Per Phase D anomaly investigation:
1. More CP² modes per fermion (richer flavor structure)
2. Per-fermion S¹ radii (breaking single-S¹; needs principled mechanism)
3. Multiplicative rather than additive λ combination

Per Phase C: non-D₃-invariant per-block observables (E-pair orientation under individual reflections, corner-subtriangle support, dipole moments) — candidates for QN discrimination that neither C nor D tested.

Per notebook §IX.2 roadmap, untouched by this orchestration:
- #1 Baptista non-Killing extension to 7-manifold (§XIII.2 "most important calculation")
- #2 Full Kigami Dirac operator on SG for spin geometry
- Read **Ibarra-Singh-Vempati arXiv:2509.04811** carefully — published Sierpinski-LIKE construction with three iterations reproducing lepton masses + mixings with few parameters; may differ from L=5 SG and may close part of what L=5 SG doesn't

## Recommended notebook §IV.4 status update text

Status: "Numerically demonstrated qualitative" + "Not yet computed specific match" (both unchanged from §IX.1 status table), but with **two new entries on the record**:

- **New structural prediction (stands under MPM)**: 18 = 3 generations × 6 charged-fermion components, derived from D₃ irrep multiplicities (22A + 18B + 40E → min = 18) on the λ=6 eigenspace of L=5 SG decimation. Geometric, not fit-parameter.

- **New falsification (under MPM)**: principled CP² × S¹ product-manifold rules with 3 global parameters underperform 1-parameter SG-only by 86% in total error on SM mass² ratio target. The framework prediction that within-generation splitting comes from CP² × S¹ is not vindicated by the L=5 SG candidate at this level of geometric structure.

## Orchestration summary

| Phase | Role | Verdict |
|---|---|---|
| A | Section principal | SG direct-graph spectrum verified; anomaly: [0,6] not [0,5] |
| B | Section principal | Direct-graph beats abstract by 24%; λ=6 mult=120 (Phase A prose error caught); d_S=1.84 peak real |
| C | Concertmaster | BIP-alone TAUTOLOGY; 18-block geometric count discovered |
| D | Section principal | CP² × S¹ FALSIFIED at principled rules |
| E | Skipped | CKM downstream-dependent; would compound, not extend |
| F | Conductor | This synthesis |

## Coda

Math doesn't lie. The framework's specific L=5 SG × CP² × S¹ candidate is not the closure of §XIII.1. The 18-block geometric prediction is a real structural finding worth carrying forward. The next iteration of this work (whether by us or by the published community per Ibarra-Singh-Vempati) needs richer structure than this orchestration tested — and the project's instruments (graph-Laplacian + HDC + integer-ALU) are exactly the right tools for it; the limitation is the geometric candidate, not the instrument.
