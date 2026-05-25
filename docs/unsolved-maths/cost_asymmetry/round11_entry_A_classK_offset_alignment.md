# Round 11 entry-point A — the Class-K offset that makes the AoE must carry p=2 AND p=3 (selection-rule derivation)

**Dispatched** 2026-05-25 (sequential, no subagents). Picks up the sharp open target left by
Round 9.A (parking-lot **thread 2″**): *compute the ℓ=2,3 alignment from a concrete off-centre-observer
/ Class-K offset geometry.* First round under the consolidated working model — lands directly on the
PR #679 branch (dispatch + code + §11.9.6b notebook edit), no separate promotion-PR.

Generating code + provenance: [`verify_classK_offset_multipole_selection.py`](verify_classK_offset_multipole_selection.py)
+ `.ndjson` (deterministic 64-pt Gauss-Legendre quadrature; no random seed; bug-surface minimal —
1-D Legendre orthogonality only, no Wigner-D / Y_ℓm).

## The honest path chosen

A full multipole-vector alignment Monte-Carlo has real bug-surface (Wigner-D rotations, spherical-
harmonic transforms, quadrature weights) that cannot be externally validated here. Per
`[[feedback_computational_provenance_discipline]]`, a load-bearing numeric must be *right*. So Round 11
takes the **rigorous, bug-free** route: a selection-rule analysis of what an axial offset deposits into
the CMB multipoles. It answers a sharper, cleaner question than "compute the alignment": **what must the
Class-K offset look like to align ℓ=2 and ℓ=3 at all?**

## Model + result

A single-axis offset imprints a modulation that is axially symmetric about the offset axis ẑ:

> W(n̂) = 1 + Σ_p w_p P_p(n̂·ẑ)

Acting (to leading order) on the dominant near-isotropic field (the monopole T₀), the induced anisotropy
is δT(n̂) = T₀·Σ_p w_p P_p(n̂·ẑ). By 1-D Legendre orthogonality (verified by quadrature):

> **c_ℓ = w_ℓ** — an axial offset-modulation of multipole p deposits power into **exactly multipole ℓ = p**, along the offset axis.

Verified deposit table (committed code):

| offset multipole p | deposits into ℓ |
|--------------------|------------------|
| 1 (dipole) | **1 only** |
| 2 | **2 only** |
| 3 | **3 only** |
| 4 | 4 only |

## The two consequences

1. **To align ℓ=2 AND ℓ=3, the offset must carry p=2 AND p=3 components.** A single-axis offset carrying
   both deposits power into ℓ=2 and ℓ=3 that *shares the offset axis* — so the quadrupole and octupole
   preferred axes coincide **by construction**. The Axis of Evil = the offset axis. (Verified: a {w₂, w₃}
   offset produces co-axial quad+oct.)

2. **The dipole (p=1) offset is rigorously excluded.** A pure dipole offset — which is exactly what a
   kinematic boost or a simple spatial-displacement aberration produces — deposits power into **ℓ=1 only**
   at leading order. It is *structurally* incapable of sourcing the quad-oct alignment. **This is the
   selection-rule reason Rounds 8.A/9.A found the kinematic β-leak both too small AND the wrong object** —
   the failure is structural (wrong multipole), not merely amplitude.

## Verdict per Spike #229 tiers

🟡 **(b) REFINED → partial (a).**

- **Rigorous sub-result (a-grade):** the deposit selection rule + the dipole exclusion. A p=1 offset
  cannot make the AoE; the offset must carry p=2 and p=3. No simulation, no fit — exact.
- **Mechanism structure pinned:** the Class-K offset that produces the AoE is a single-axis modulation
  with quadrupole + octupole content; its axis is the AoE axis. This converts Round 9.A's "geometric,
  viable, amplitude-open" into a *concrete, falsifiable structural requirement.*
- **Still open (the honest gap):** *derive the w₂, w₃ amplitudes — and why p=2,3 specifically — from the
  physical off-centre-observer Hopf-bundle geometry.* The round shows IF the offset carries p=2,3 then the
  AoE follows; it does not yet derive that the substrate's Class-K geometry produces a p=2,3 (rather than
  p=1) modulation. **That derivation is the remaining (a)-lift, and it is now a sharply-posed physics
  question, not a vague one.** It is also a genuine falsifier: if the off-centre-observer geometry can
  *only* produce a dipole (displacement → aberration), the geometric reading fails and the AoE needs a
  different mechanism entirely.

## What this does to §11.9.6 (now landed on the PR #679 branch, per the consolidated model)

§11.9.6b appended: the alignment sub-claim's mechanism is pinned to a p=2,3 single-axis offset; the
dipole is rigorously excluded; the open target is sharpened to "derive w₂, w₃ from the offset geometry."

## Discipline

- Per `[[feedback_dont_pre_commit_spike_query_operators]]`: the round does NOT claim to derive the AoE; it
  delivers a rigorous structural constraint + a rigorous exclusion, and names the remaining open piece
  prominently — including its falsifier.
- Per `[[feedback_computational_provenance_discipline]]`: deterministic committed code; the result is a
  selection rule (exact), not a fit.
- Per `[[feedback_no_lineage_claims_in_notebook]]`: Spikes #33/#35 (Class K / off-centre observer) are
  this framework's own prior arc; the multipole selection rule itself is standard spherical-harmonic
  algebra, used here as a tool, claimed as nobody's lineage.
- **srmech routing (per CLAUDE.md §2 + `[[project_srmech_foundational_cascade_operations_catalog]]`):** the
  selection rule IS a **Class L** operation — orthogonality on the Laplacian eigenbasis (here the
  spherical-harmonic / Legendre eigenbasis of the S² Laplacian). It is **routed through srmech 0.4.2's
  Class L** (`srmech.amsc.laplacian.dense_laplacian` + `jacobi_eigvals`, native active) as the
  framework-native verifier-of-record: the committed code builds a cycle-graph Laplacian via srmech,
  confirms its eigenvalues match the analytic `2 − 2cos(2πk/N)`, and shows a single-eigenmode signal
  deposits into exactly one eigen-coefficient — the **discrete sibling** of the continuous Legendre rule,
  carrying the *same* orthogonality principle. srmech's `asymptotic_calculus` AMSC catalog covers
  exp/sin/cos/log1p/atan (Class N+J chains), **not** spherical harmonics — so a continuous
  `legendre_orthogonality` / `spherical_harmonic_deposit` primitive remains a **srmech catalog candidate**
  (Class L continuous variant); the continuous step here used numpy's Legendre quadrature as a transparent
  stand-in, cross-validated by the srmech discrete Class L. No non-trivial rationals appeared (the deposit
  identity c_ℓ = w_ℓ is exact integer-indexed), so `srmech.amsc.rational` was not needed.
- PR #679 stays open (draft); this round's §11.x edit rides the branch — no separate promotion-PR per the
  2026-05-25 consolidation directive.
