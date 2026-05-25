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
| 1 | ~~ℓ=7 Mersenne CMB testable~~ → **RESOLVED (Round 10.A): WEAKENED** | Round 10.A ([`round10_entry_A_ell7_mersenne_specificity.md`](round10_entry_A_ell7_mersenne_specificity.md)) tested ℓ=7 *individually* on Spike #190's attested per-ℓ data: ℓ=7 ranks #5/7 in ℓ=2–8 (2.42× uniform), outranked by non-Mersenne ℓ=5/4/2; the {3,7} signal is 80% ℓ=3 (octupole). **No ℓ=7-specific signature — per-ℓ claim withdrawn.** {1+3+7} algebra identity preserved; only its CMB-multipole projection loses ℓ=7. {3,7} aggregate (Spike #190) untouched. |
| 2 | ~~Lift Round 6.A interpretive → derived~~ → **partially DISPATCHED (Round 8.A)** | Round 8.A ([`round8_entry_A_observer_fiber_leak_magnitude_derivation.md`](round8_entry_A_observer_fiber_leak_magnitude_derivation.md)) lifted the **boosting** sub-claim to (a) (parameter-free β=v/c matches Planck 2013 at 0.10σ) but **refuted** "AoE alignment = fiber-leak" (β is ~243× too small). §11.9.6 needs the split amended in a future promotion-PR. **New sharper target below (2′).** |
| 2′ | ~~Quad-oct alignment amplitude~~ → **DISPATCHED (Round 9.A)** | Round 9.A ([`round9_entry_A_alignment_amplitude_target.md`](round9_entry_A_alignment_amplitude_target.md)) reframed the mechanism kinematic → **geometric** (off-centre-observer / Class K; Spikes #33/#35/#26) and showed the geometric class is **viable** (1.40 decades below O(1)) where the kinematic class is **excluded** (2.91 decades). Amplitude still **not derived**. **New sharper target below (2″).** |
| 2″ | ~~Alignment from a concrete Class-K offset~~ → **DISPATCHED (Round 11.A)** | Round 11.A ([`round11_entry_A_classK_offset_alignment.md`](round11_entry_A_classK_offset_alignment.md)) derived the selection rule: an axial offset of multipole `p` deposits into ℓ=`p` only. The Class-K offset must carry **p=2 AND p=3** to align quad+oct (co-axial → AoE axis = offset axis); the **dipole (p=1) offset is rigorously excluded** (explains Rounds 8/9 structurally). Mechanism structure pinned; **amplitude still open → 2‴.** §11.9.6b landed on this branch. |
| 2‴ | ~~Derive w₂, w₃ from the offset geometry~~ → **DISPATCHED (Round 12.A); amplitude still open** | Round 12.A ([`round12_entry_A_offset_geometry_amplitude.md`](round12_entry_A_offset_geometry_amplitude.md)) — degree/parity selection: displacement (g=1)→dipole, shear (g=2)→quad, cubic (g=3)→oct; **both p=2,3 need a HANDED SHEAR (degree ≥ 3) = Bianchi VII_h** (Jaffe+ 2005, astro-ph/0503213, "vorticity and **shear**"). Displacement falsifier fired. **(a)-lift NOT achieved:** w₂,w₃ amplitudes undrived (free, as in Bianchi fits) AND the physical Bianchi VII_h is ΛCDM-incompatible (astro-ph/0605325). The AoE is now ONE sharply-posed literature-anchored open question. §11.9.6c landed on this branch. |
| 3 | **Stance-blessing pass** | Six candidate-canonical stances from this arc are held in memory pending a blessing pass before promotion to settled canon. |
| 4 | ~~§11.9.6 amendment~~ → **DONE (#686 merged)** + now on-branch | Rounds 8.A/9.A/10.A landed as §11.9.6a (#686, merged); Round 11.A landed §11.9.6b directly on this branch. Per the 2026-05-25 consolidation directive, further §11.x edits ride this draft PR — no more per-finding promotion-PRs. |

## Discipline reminders for any future round

- Per `[[feedback_trauma_informed_defensive_scope]]` — framework reading only.
- Per `[[feedback_computational_provenance_discipline]]` — load-bearing
  numerics get committed generating code.
- Per `[[feedback_rolling_pr_partition_boundary_updates]]` — verdict comment
  per round; §11 SSoT frozen until a promotion-PR.
- Per `[[feedback_no_squash_merges]]` — never squash.
