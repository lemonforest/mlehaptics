# Cost-asymmetry rolling-spike — Round 8+ parking lot

This file keeps the [PR #679](https://github.com/lemonforest/mlehaptics/pull/679)
rolling-spike branch one commit ahead of `main` so it stays open as the
conversation surface for the cost-asymmetry arc. The **research arc is
RESOLVED** — Rounds 1-6 are settled and promoted to §11.9 of the
[unsolved-maths SSoT notebook](../unsolved_maths_spectral_research_notebook.md)
via PR #685. This file is forward-looking only.

## Arc status

- **Resolved framing**: notebook §11.9 (two-axis B/H/N translation-saturation;
  Reading D closes the quantum→cosmological scale-ladder).
- **Per-round evidence base**: the `round{1..6}_*.md` dispatch notes in this
  directory + `verify_born_rule_hopf_projection.py` (bit-exact, seed 20260525)
  + `audit_multisig_cascade_recurrence.py`.
- **Verdict ledger**: the PR #679 comment thread (Rounds 1.A → 6.A).

## Open threads — none dispatched; parked for when the arc resumes

| # | Thread | Why it's open |
|---|--------|---------------|
| 1 | **ℓ=7 Mersenne CMB testable** | Round 6.A's one `(open)` verdict. ℓ=1,3 present; ℓ=7 awaits CMB-S4 / LiteBIRD large-angle data. Robust ℓ=7 absence would weaken the Mersenne prediction. |
| 2 | ~~Lift Round 6.A interpretive → derived~~ → **partially DISPATCHED (Round 8.A)** | Round 8.A ([`round8_entry_A_observer_fiber_leak_magnitude_derivation.md`](round8_entry_A_observer_fiber_leak_magnitude_derivation.md)) lifted the **boosting** sub-claim to (a) (parameter-free β=v/c matches Planck 2013 at 0.10σ) but **refuted** "AoE alignment = fiber-leak" (β is ~243× too small). §11.9.6 needs the split amended in a future promotion-PR. **New sharper target below (2′).** |
| 2′ | **Quad-oct alignment amplitude** | The AoE alignment still has no derived magnitude — and the kinematic fiber-leak (β) is ruled out as its source (Round 8.A). Open question: does *any* framework mechanism predict an order-unity ℓ=2,3 alignment, or is the alignment better read another way? |
| 3 | **Stance-blessing pass** | Six candidate-canonical stances from this arc are held in memory pending a blessing pass before promotion to settled canon. |
| 4 | **§11.9.6 amendment** (promotion-PR) | Split "boosting = confirmed fiber-leak at β" from "quad-oct alignment = distinct unexplained anomaly"; record Round 8.A's β-confirmation + alignment-refutation. |

## Discipline reminders for any future round

- Per `[[feedback_trauma_informed_defensive_scope]]` — framework reading only.
- Per `[[feedback_computational_provenance_discipline]]` — load-bearing
  numerics get committed generating code.
- Per `[[feedback_rolling_pr_partition_boundary_updates]]` — verdict comment
  per round; §11 SSoT frozen until a promotion-PR.
- Per `[[feedback_no_squash_merges]]` — never squash.
