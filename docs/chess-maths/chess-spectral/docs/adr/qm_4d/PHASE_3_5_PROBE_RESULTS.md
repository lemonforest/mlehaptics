# Phase 3.5 Probe Results: Empirical validation of Track B ADRs

**Date:** 2026-04-29
**Branch:** `chess-spectral/phase-3.5-probes`
**Probes:** [`python/research/track_b_*_probe.py`](../../../python/research/) (4 files)
**Results:** [`python/research/track_b_*_results.json`](../../../python/research/) (4 files) + [`track_b_pawn_pt_symmetry_findings.md`](../../../python/research/track_b_pawn_pt_symmetry_findings.md)

This document is the authoritative empirical-validation record for the five [Track B ADRs](README.md). Each ADR has a probe (or is unconditional). The probes report pass/fail vs the acceptance criterion the ADR itself specified. Where a probe fails, this document records the **amendment** to the ADR's design decision.

ADRs themselves are preserved as the design record *at the time of the decision*; this doc captures the empirical reality that came back when those decisions were tested. Phase 4 implementation reads ADR + this doc together — when the two disagree, **this doc wins** for design-level decisions; the ADR's reasoning still stands as the rationale.

## Summary

| ADR | Probe | Acceptance gate | Result | Status |
|---|---|---|---|---|
| 001 | phase distinguishability | ≥80% pairs `|⟨ψ_A|ψ_B⟩| < 0.99` | **100%** below threshold | ✅ **PASS — ship as-is** |
| 002 | (no probe; not gated) | — | — | ✅ **PASS — ship as-is** |
| 003 | ε / cond percentiles | FIB ε p95 ≤ 0.10; FD_DIAG cond ≤ 100 | FIB ε p95 = 5.6 / 6.8 / 46.8 ❌; FD_DIAG cond p95 = 8.6 ✅ | ⚠️ **AMEND** — FIB falls back to measurement-only re-encode |
| 004 | U_move ↔ J_op anti-commutation | per-channel residual ≤ 1e-10 | residual p95 = 128 ❌ | ⚠️ **AMEND** — §3.4 weakened |
| 005 | pawn PT-realness + pseudo-Hermiticity | `|Im(spec)| ≤ 1e-10` AND `‖M^T − P_w·M·P_w⁻¹‖ ≤ 1e-10` | spec real (nilpotent, 0 throughout) ✅; pseudo-Hermiticity holds for single-push only ⚠️ | ⚠️ **AMEND** — decompose M_pawn = M_single + M_double |

Phase 4 readiness post-amendments:

| Milestone | Gate | Status |
|---|---|---|
| **B1** A_1 channel move-as-permutation | ADR-001 ✅ | ✅ **UNBLOCKED** |
| **B2** Zeno-style evolution + H_0 | ADR-002 ✅ | ✅ **UNBLOCKED** |
| **B3a** strict A_1 + STD4 channels | ADR-003 ✅ | ✅ **UNBLOCKED** with ADR-004 §3.4 caveat |
| **B3b** pawn-antisym channels | ADR-003 ✅ | ✅ **UNBLOCKED** with ADR-004 §3.4 caveat |
| **B3c** FIB_SYM 1/2/3 | ADR-003 ⚠️ | ⚠️ **REVISED PATH**: ship as measurement-only re-encode in v1.5 (per ADR-003 §3.3 fallback) |
| **B3d/e** FD_DIAG | ADR-003 ✅ | ✅ **UNBLOCKED** (rank-1 update path validated) |
| **B4** Z_2 grading + tests | ADR-004 ⚠️ | ⚠️ **REVISED**: §3.4 weakened to sector-flip-via-state_to_psi; tests must reflect this |
| **B5** pawn observables | ADR-005 ⚠️ | ⚠️ **REVISED**: decompose M_pawn for η-metric; v1.5 Hermitian-projection unchanged |

---

## Probe 1 (ADR-001): phase distinguishability — PASS

**Hypothesis:** Per-channel phase formula in ADR-001 (Option D, B_4-irrep-derived) produces distinguishable post-move quantum states.

**Acceptance:** ≥80% of pairs (A, B) with distinct from→to coords have `|⟨ψ_A|ψ_B⟩| < 0.99`.

**Method:** 50 seeded positions × 20 distinct legal moves each → 9,500 (A, B) move pairs on the same starting state. For each pair: encode the post-move position classically, multiply each channel block by ADR-001's phase factor, renormalize, compute inner product.

**Result:**
- Inner-product overlap percentiles: p5=0.065, p50=0.325, p95=0.759
- Fraction below 0.99: **100.00%** (gate: ≥80%)
- Fraction below 0.50 (strong distinguishability): 73.6%

**Verdict:** ADR-001 ships as-is. The Aaronson escape valve is empirically open — channel-distinct phases produce real interference, not notational restatement of classical permutations. The 73.6% strong-distinguishability rate suggests the QM mapping has genuine quantum content beyond the trivial.

**File:** [`track_b_phase_distinguishability_probe.py`](../../../python/research/track_b_phase_distinguishability_probe.py).

---

## Probe 2 (ADR-003): ε / cond percentiles — PARTIAL PASS

**Hypothesis:** FIB_SYM channels admit best-effort linearization with ε ≤ 0.10; FD_DIAG admits a rank-1 update with cond ≤ 100.

**Acceptance:** 95th percentile of ε ≤ 0.10 per FIB channel; 95th percentile of cond ≤ 100 for FD_DIAG.

**Method:** 934 (state, move) pairs across the seeded corpus. Per pair: compute pre-move and post-move encoded vectors; estimate per-channel Jacobian J_c numerically via finite differences; compute ε = `‖ψ_post_actual − (ψ_pre + J_c · δv)‖ / ‖ψ_post_actual‖`. For FD_DIAG: build rank-1 update matrix and compute `np.linalg.cond`.

**Result:**

| Channel | Acceptance gate | p95 result | Outcome |
|---|---|---|---|
| FIB_SYM_1 | ε ≤ 0.10 | **5.64** | ❌ **FAIL by ~56×** |
| FIB_SYM_2 | ε ≤ 0.10 | **6.82** | ❌ **FAIL by ~68×** |
| FIB_SYM_3 | ε ≤ 0.10 | **46.76** | ❌ **FAIL by ~468×** |
| FD_DIAG (synth-capture) | cond ≤ 100 | **8.60** | ✅ PASS |

**Diagnosis:** Dominant source of error is the **occupancy-change term**: when a piece moves from origin to destination, origin's `contrib_k` term disappears and destination's appears. This is structurally non-linear in `delta_sig` — no Jacobian J_c can capture it because the perturbation is not infinitesimal in the right space. The Jacobian model assumes `δψ = J_c · δposition`, but the true map is *piecewise* with a non-smooth boundary at every move.

**Amendment to ADR-003:** Phase 4 milestone B3c **must** ship FIB channels under the §3.3 fallback path: **measurement-only re-encode** (apply move classically, re-encode the post-move position, project channel-wise). This is honest within the QM formalism (a measurement-then-evolution sequence) and matches the ADR's original §3.3 fallback. The "best-effort linearization" path is closed for FIB channels in v1.5; revisit in v1.7+ if a linearization-friendly reformulation surfaces.

**File:** [`track_b_linearization_quality_probe.py`](../../../python/research/track_b_linearization_quality_probe.py).

---

## Probe 3 (ADR-005): pawn PT-realness + pseudo-Hermiticity — PARTIAL PASS

**Hypothesis:** M_pawn (specifically `phase_operators_4d.P_pawn_w_white` lifted to a 4096×4096 matrix) is pseudo-Hermitian under η = P_w (W-axis parity flip), satisfying M^T = P_w · M · P_w⁻¹. This implies real spectrum — necessary for coherent QM treatment of pawn dynamics.

**Acceptance:** `|Im(spec)| ≤ 1e-10` AND Frobenius `‖M^T − P_w · M · P_w⁻¹‖ ≤ 1e-10`.

**Method:** Build M_pawn from predicate; build P_w as the permutation `(x,y,z,w) → (x,y,z,7-w)`; compute the residual; compute spectrum via eigs.

**Result:**

| Variant | nnz | spec real? | η = P_w residual | Outcome |
|---|---|---|---|---|
| Full (push + double-push + captures) | 10,368 | ✅ (all 0; nilpotent) | **32.0** | ❌ FAIL pseudo-Herm |
| Single-push + captures (no double-push) | (smaller) | ✅ | **0.000e+00** | ✅ PASS exact |
| Single-push only | (smallest) | ✅ | **0.000e+00** | ✅ PASS exact |

The duality `P_w · M_white · P_w = M_black` holds **exactly** (residual 0.0) in all variants — this is the strongest structural identity in the pawn algebra.

**Diagnosis:** ADR-005 §3.3.1's claim `M_white^T = M_black` (which would imply pseudo-Hermiticity under η = P_w via `P_w · M_white · P_w = M_black = M_white^T`) holds in the no-double-push idealization. The starting-rank double-push breaks the transpose identity, contributing a residual of 32.0 in Frobenius norm.

**Amendment to ADR-005:** Decompose `M_pawn_w_white = M_single_push + M_double_push`. The η-metric (P_w pseudo-Hermitian) applies to `M_single_push` exactly; `M_double_push` is treated separately as a non-pseudo-Hermitian rank-deficient operator outside the QM framework. Spectrum-realness is trivially satisfied (full M_pawn is nilpotent — every eigenvalue is 0 — which is real).

**v1.5 unchanged:** Track A's Hermitian-part projection (`H_pawn_w_4_herm = (M + M^T)/2`) ships as designed; this probe doesn't affect v1.5 deliverables.

**v1.6+ promotion path remains open** with the decomposition correction documented.

**File:** [`track_b_pawn_pt_symmetry_probe.py`](../../../python/research/track_b_pawn_pt_symmetry_probe.py) + [`track_b_pawn_pt_symmetry_findings.md`](../../../python/research/track_b_pawn_pt_symmetry_findings.md).

---

## Probe 4 (ADR-004): U_move ↔ J_op anti-commutation — FAIL

**Hypothesis:** ADR-004 §3.4 declares U_move odd-parity under J_op (Z_2 grading from central-inversion + color-flip). For each strict-unitary channel: `{U_move, J_op} = U_move · J_op + J_op · U_move = 0` within 1e-10.

**Acceptance:** Per-channel anti-commutator residual ≤ 1e-10 averaged over 100 sampled (state, move) pairs.

**Method:** Build J_op as the linear map (x,y,z,w) → (7-x, 7-y, 7-z, 7-w) with sign flip; for each strict-unitary channel, construct U_move per ADR-001's phase formula × ADR-003's permutation; compute the anti-commutator's Frobenius norm.

**Result:**
- All 5 strict-unitary channels: anti-commutator p95 = **1.280e+02** (target < 1e-10) — fails by 30 orders of magnitude
- Commutator p95 = 2.83 (also non-zero — neither commutes nor anti-commutes for non-J-symmetric moves)
- 0 of 200 sampled moves are J-symmetric (J(origin) = destination) — typical move geometry doesn't preserve central inversion
- Global -1 prefactor (testing side-to-move sign hypothesis) gives identical residual since `‖cM‖_F = |c|·‖M‖_F`

**Diagnosis:** §3.4's strict anti-commutation `{J_op, U_move} = 0` is **mathematically impossible** for the swap-permutation construction in ADR-001 / ADR-003. For non-J-symmetric moves (which is essentially all real moves), the swap matrix on (origin, destination) and the global central-inversion+color-flip do not commute or anti-commute as algebraic operators on ℂ^4096. The Z_2 sector flip happens at a different layer.

**Amendment to ADR-004:** Replace §3.4 with:

> The Z_2 sector flip is mediated by `state_to_psi`'s side-to-move sign multiplier (per Pre-flight 1's Z_2 superselection finding). The per-channel `Π_c` and `U_move` are **not** required to formally anti-commute with `J_op` as algebraic operators. Instead: applying U_move and updating side-to-move via state_to_psi's sign convention together implement the parity sector change at the state-vector level. Tests should verify that `state_to_psi(applied_state, new_side_to_move)` returns ψ in the correct parity sector, **not** that `Π_c · J_op = -J_op · Π_c`.

This is a documentation/design clarification with no code architectural change. Phase 4 B4 ships with the weakened §3.4 understanding; B4's test suite must be designed around the state-level parity check, not the operator-level anti-commutation.

**File:** [`track_b_zsuperselection_parity_probe.py`](../../../python/research/track_b_zsuperselection_parity_probe.py).

---

## Phase 4 readiness — final

After applying the three amendments above, Phase 4 milestones are unblocked as follows:

- **B1, B2** ship as designed (ADR-001 + ADR-002 unmodified).
- **B3** ships in 4 sub-paths:
  - **B3a** (A_1, STD4) strict permutation × phase per ADR-001 + ADR-003.
  - **B3b** (pawn antisymmetric) strict permutation × phase per ADR-001 + ADR-003.
  - **B3c** (FIB_SYM 1/2/3) **measurement-only re-encode** per ADR-003 §3.3 fallback (revised).
  - **B3d/e** (FD_DIAG) rank-1 update + renormalization per ADR-003 (validated).
- **B4** ships with revised §3.4 — sector-flip-via-state_to_psi tests, not operator-anti-commutation tests.
- **B5** ships v1.5 Hermitian-part projection unchanged. v1.6+ promotion path uses the M_single_push / M_double_push decomposition.

The three amendments are **documentation-level**; no probe revealed a need to redesign at the architectural level. Phase 4 implementation can begin immediately on B1.

---

## Reproducing the probes

```bash
cd python
python research/track_b_phase_distinguishability_probe.py
python research/track_b_linearization_quality_probe.py
python research/track_b_pawn_pt_symmetry_probe.py
python research/track_b_zsuperselection_parity_probe.py
```

Total runtime ~50s on a modern CPU. Each script writes its own JSON results file to `python/research/`. All probes are deterministic (seeded RNG); reruns produce bit-identical outputs.
