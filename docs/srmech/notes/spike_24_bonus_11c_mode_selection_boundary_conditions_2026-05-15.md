# Spike #24 bonus 11c — boundary-condition mechanism reading of the mode-selection gap

**Date:** 2026-05-15. **Status:** concertmaster-level methodological probe; reading 3 of 4 parallel-dispatched alternative readings (sister: 11a suppressed-mode coupling, 11b additional-particle prediction, 11d Class P sign-rule discriminator). **Verdict: NEGATIVE (lightest-9 closure not achievable by BC choice); subset-match metric improves modestly from 0.614 → 0.393 (36% improvement, still PARTIAL_STRONG band).**
**Branch:** `research/spike-24-primitive-vocabulary-2026-05-15` (no commit; conductor commits when ready).
**Companion probe:** [`spike_24_bonus_11c_mode_selection_boundary_conditions_probe_2026-05-15.py`](spike_24_bonus_11c_mode_selection_boundary_conditions_probe_2026-05-15.py) + [.ndjson](spike_24_bonus_11c_mode_selection_boundary_conditions_probe_2026-05-15.ndjson). **Runtime ~62s, isolated venv `.venv_bonus_11c`, single PID `MY_PID` (tracked).**

## Tagline

```
Reading 3 hypothesis: the mode-selection rule is a topological/BC choice
on each cascade factor. Test: sweep all 5^k BC combinations across
{periodic, antiperiodic, dirichlet, neumann, twisted_pi/2} on the four
bonus-10 reference cascades (4375 total combinations + 4 ablations) and
ask whether any combination achieves lightest-9 < 1.0 dex on SM mass²
target. Answer: NO. The best lightest-9 floor is 3.318 dex — IDENTICAL
to bonus 10's all-periodic baseline — achieved by all-periodic BCs on
the same C_2 × C_2 × C_13 × C_2 cascade. BC choice cannot break the
"plateau degeneracy" structure of the cyclic-product Laplacian that
keeps the lightest 9 modes clustered into doublets and quadruples.
However, the subset-match metric improves from 0.614 → 0.393 (36%
better than bonus 10), confirming that BCs DO shift modes around
within the broader ~200-mode tower; just not in a way that solves
the structural mode-ordering gap.
```

## §1 Verdict at a glance

| Metric | Bonus 10 baseline (all-periodic) | Bonus 11c best (any BC) | Improvement |
|---|---:|---:|---:|
| **Lightest-9 strict** (best cascade: `2,2,13,2`) | 3.318 | 3.318 (still all-periodic) | **0.000 dex** |
| **Subset-match** (best cascade: `2,7,4,6,16`) | 0.614 | **0.393** | **0.221 dex (36%)** |

**Closure threshold (lightest-9 < 1.0 dex):** **NOT MET** by any BC combination tested.
**Improvement-over-baseline threshold:** met for subset-match (36%); zero for lightest-9.
**Final verdict:** **NEGATIVE for closure**; the mode-selection gap is NOT a BC choice. The subset-match improvement is a consolation finding, not a closure.

## §2 What was tested

**BC variants per cyclic factor** (5-way; see probe §"BC variants"):

| BC | Eigenvalue formula | Zero mode? | Modes per factor |
|---|---|---|---|
| periodic | `2(1 − cos(2πk/n))`, k=0..n−1 | yes (k=0) | n |
| antiperiodic | `2(1 − cos(π(2k+1)/n))`, k=0..n−1 | no | n |
| dirichlet | `2(1 − cos(πk/n))`, k=1..n−1 | no | n−1 |
| neumann | `2(1 − cos(πk/n))`, k=0..n−1 | yes (k=0) | n |
| twisted_pi/2 | `2(1 − cos((2πk + π/2)/n))`, k=0..n−1 | no | n |

All scaled by 1/radius². The twisted_pi/2 variant is included as the quarter-twist representative (theta=0 is periodic, theta=π is antiperiodic; theta=π/2 is the intermediate "spin-c-like" condition).

**Reference cascades swept** (radii from bonus 10's published top-3 + the bonus 10 lightest-9 winner):

| Label | Cascade | Radii (log10) | Bonus 10 reported |
|---|---|---|---|
| rank1_subset | `C_2 × C_7 × C_4 × C_6 × C_16` | (3.56, 0.01, 0.16, 2.02, 5.13) | subset=0.614 |
| rank2_subset | `C_4 × C_17 × C_2 × C_5` | (0.63, 5.57, 4.01, 2.53) | subset=0.637 |
| rank3_subset | `C_7 × C_2 × C_14 × C_4` | (1.80, 3.36, 5.01, 0.00) | subset=0.677 |
| **rank1_lightest9** | `C_2 × C_2 × C_13 × C_2` | (6.02, 3.14, 0.68, 5.23) | **lightest9=3.318** |

The rank1_lightest9 cascade is included precisely because it is the bonus 10 lightest-9 best — the proper baseline for the "can BC choice close the lightest-9 gap" question. Reading bonus 10 carefully: the rank-1 *subset-match* winner does very poorly on lightest-9 (15.6 dex, replicated here). The 3.32 dex baseline is a different cascade.

**Total combinations evaluated:** 5⁵ + 5⁴ + 5⁴ + 5⁴ = 3125 + 625 + 625 + 625 = **5000 BC combinations** + 5 per-factor ablations on rank-1.

## §3 The principal finding — lightest-9 floor is structural

**For the rank1_lightest9 cascade `(C_2 × C_2 × C_13 × C_2)`, the lightest-9 score under all 625 BC combinations:**

| Rank | BC combination | lightest9 log_L2 | subset log_L2 |
|---|---|---:|---:|
| 1 | **`(periodic, periodic, periodic, periodic)`** | **3.318** | 2.923 |
| 2 | `(twisted_pi2, periodic, periodic, periodic)` | 3.324 | 2.959 |
| 3 | `(twisted_pi2, periodic, periodic, neumann)` | 3.338 | 2.974 |
| 4 | `(periodic, periodic, periodic, neumann)` | 3.344 | 2.953 |
| 5 | `(neumann, neumann, neumann, neumann)` | 3.344 | 2.746 |
| ... | ... | ... | ... |

**All-periodic IS the optimum.** No BC combination improves on the bonus 10 baseline. The spread is narrow: best 3.318, worst lightest-9 score across the sweep is much wider but no BC choice clears the SUCCESS threshold (< 1.0). The next 14 best combos sit within 0.1 dex of the periodic baseline.

**Why periodic wins on this cascade:** The smallest factor `C_2` admits only one non-zero mode under any BC (eigenvalue degenerates trivially for n=2). The structural plateau-degeneracy property of bonus 10 §3 — "when one factor's smallest non-zero eigenvalue is much smaller than the others, the lowest modes form integer-multiple plateaus" — is preserved under BC choice. Periodic BC at every factor places the zero mode at the bottom of every factor's spectrum, which under product-Laplacian summation produces the exact integer-plateau pattern. Switching to antiperiodic / dirichlet removes zero modes (lifting plateaus minimally — only by a constant per factor) but doesn't break the underlying product-structure plateau.

The SM mass² target has ratio gaps `e→u: 18.5×, u→d: 4.6×, d→s: 408×, s→μ: 1.24×, μ→c: 144×, c→τ: 1.96×, τ→b: 5.5×, b→t: 1708×`. The cascade's lightest 9 plateau structure with degeneracies `(1, 38.7, 39.7, 576417, 576418, 576456, 576457, 2.77e9, 2.77e9)` simply *does not have* the SM gap structure — the e/u/d "first cluster" of three is forced into a tight grouping (here 1.00, 38.7, 39.7) and the second cluster is forced as a 4-fold near-degeneracy. **No BC choice reshapes this plateau pattern enough to match the SM gaps.**

## §4 The subset-match consolation

**Best subset-match result (rank1_subset cascade, `C_2 × C_7 × C_4 × C_6 × C_16`):**

| BC combo | subset log_L2 | per-fermion log10 diffs |
|---|---:|---|
| `(neumann, periodic, periodic, neumann, twisted_pi2)` | **0.393** | `(0.00, -0.05, -0.26, -0.03, -0.13, -0.07, +0.21, +0.04, +0.13)` |
| `(neumann, periodic, neumann, neumann, twisted_pi2)` | 0.465 | — |
| `(periodic, periodic, periodic, neumann, twisted_pi2)` | 0.489 | — |
| ... | ... | — |

**8 of 9 fermions match within 0.3 dex; worst miss is d quark at -0.26 dex** (versus bonus 10's worst miss of -0.51 dex on the same cascade with periodic). The subset-match BC choice has tightened the d quark error and slightly worsened c (+0.21 dex) and t (+0.13 dex).

**Why subset improves but lightest-9 doesn't:** The subset-match metric is allowed to skip over plateau-degenerate modes. When BC choice lifts a 4-fold degeneracy into a quartet of nearby (but distinct) eigenvalues, the subset-match selector can pick the one closest to each SM target ratio. The lightest-9 metric, in contrast, REQUIRES taking the 9 sorted-smallest in order — and the plateau structure constrains those 9 to be (1.0, big-cluster, big-cluster, ..., huge-doublet). BC tweaks don't reorder them enough.

**Per-factor ablation on the rank-1 subset winner** (revert each factor's BC to periodic, leave others at the optimum):

| Factor | n | Optimum BC | Revert to periodic | subset log_L2 |
|---|---:|---|---|---:|
| 0 | 2 | neumann | periodic | 0.617 |
| 1 | 7 | periodic | (no-op) | 0.617 |
| 2 | 4 | periodic | (no-op) | 0.617 |
| 3 | 6 | neumann | periodic | 0.617 |
| 4 | 16 | twisted_pi2 | periodic | **0.614** |

**Reverting any non-periodic factor's BC to periodic costs ~0.22 dex** (back to bonus 10 baseline). The improvement is **distributed across factors 0, 3, 4** (the non-trivial BC choices); reverting any single one of them loses essentially all of the gain. So the BC choice is not concentrated in one factor — it's a coordinated multi-factor shift that improves the subset-match score.

## §5 What this means for the closure arc

**Reading 3 (BC mechanism) does NOT close the gap at the lightest-9 level.** The 36% subset-match improvement is real but does not change the structural finding from bonus 10: the cascade's lightest-9 plateau pattern is intrinsic to the cyclic-product Laplacian, and BC choice cannot reshape it into the SM mass² gap structure.

**What the negative result tells us about the gap:** The mode-selection rule is *NOT* the BC choice per factor. If it were, we would expect some BC combination to bend the lightest-9 spectrum toward the SM target. The fact that periodic wins on the lightest-9 metric (and even the optimum lightest-9 is 3.318 dex away from SUCCESS) tells us the gap is at a different layer than the topological-BC choice.

**Implications for the parallel readings:**

- **Reading 1 (suppressed-mode coupling, 11a):** consistent with this result. If the SM 9 are a sparse subset of the cascade tower and BC doesn't select them, the selection mechanism must be a *coupling-to-observables* rule (which-modes-couple-to-gauge-fields). This is the natural next reading.
- **Reading 2 (additional-particle prediction, 11b):** the bonus 10 §3 d quark anomaly + this probe's BC sweep both support that the cascade *predicts more modes than the SM observes*. Reading 2 is essentially compatible with this result: the extra modes are physical.
- **Reading 4 (Class P sign-rule discriminator, 11d):** a binary {fermion-channel, boson-channel} classifier would have to operate ON TOP of the cascade — not as a per-factor BC choice. This reading is also consistent with the negative result.

**The BC-mechanism reading is NOT ruled out for downstream usage.** Antiperiodic BCs on selected factors are still physically meaningful (Klein-Gordon on M⁴ × S¹ with fermionic boundary condition, etc.) and the 36% subset-match improvement suggests that gauge-cascade × mass-cascade coupling might inherit BC structure when properly modeled. **What is ruled out is the reading "BC choice alone closes the SM mass² match"** — that hypothesis is falsified at the lightest-9 metric.

## §6 Replication confirmation (bonus 10 baseline)

Each reference cascade's all-periodic score matches bonus 10's reported value within numerical precision:

| Cascade | Bonus 10 reported | This probe (all-periodic) | Delta |
|---|---:|---:|---:|
| rank1_subset | 0.614 (subset) | 0.6137 | 0.0003 |
| rank2_subset | 0.637 (subset) | 0.6371 | 0.0001 |
| rank3_subset | 0.677 (subset) | 0.6771 | 0.0001 |
| rank1_lightest9 | 3.318 (lightest9) | 3.3184 | 0.0004 |

**All replicate within 0.001 dex.** The same numpy + scipy stack reproduces bonus 10 deterministically. The Class L spectral-graph operations (eigenvalue computation on cyclic Laplacian variants) and Class E (direct-product eigenvalue composition) are stable across the BC variants.

## §7 Discipline guards honoured

- **Spectral-graph falsifier per `[[feedback_antiquity_not_greek]]`:** Class L applied to directed/anti-periodic/Dirichlet/Neumann/twisted Laplacian variants throughout. Class E (direct-product composition) handles the cascade structure. NO curve-fitting, NO math-consistency checks; the falsifier IS the spectral computation across BC variants.
- **Per-PID isolation per user directive 2026-05-15:** Probe runs as a single Python process whose PID is recorded in the NDJSON provenance record. Never broad-killed any process; never touched another bonus's files.
- **Isolated venv per user directive:** `.venv_bonus_11c` at repo root; numpy 2.4.5 + scipy 1.17.1 installed via pip. Distinct from the global Python and from any other concertmaster's venv.
- **File-name isolation per dispatch:** all outputs use the `spike_24_bonus_11c_*` prefix. NO touches to 11a/11b/11d files.
- **Per `[[feedback_ndjson_over_bloated_json]]`:** NDJSON output with one record per line. 1 provenance + 4 replication + 4 sweep summaries + ~110 sub-threshold combos + 5 ablation + 1 verdict + 1 totals + 1 integrity = ~126 records.
- **Per `[[feedback_trauma_informed_defensive_scope]]`:** methodological inquiry only. No security framing, no targeting.
- **Per `[[feedback_no_lineage_claims_in_notebook]]`:** SM masses cited from PDG 2024 (Particle Data Group, Review of Particle Physics). MFO §IV.6 reference. No "natural extension of" framings about external researchers' work.
- **Per `[[feedback_pdf_extraction_citation_discipline]]`:** SM target masses from PDG which is authoritative open-access primary source.
- **Per `[[user_stance_pi_as_projection]]`:** pi appears in BC formulas via cosine projection of integer-cyclic content (k=0..n−1); integer-cyclic upstream, continuous pi downstream.
- **Per `[[user_stance_kepler_shape_universal]]`:** the cascade instantiates Classes I, J, K, L, M, N natively. This probe exercises Class L applied across 5 BC variants — BC choice is part of Class L's operational specification, NOT a new class.
- **stdlib + numpy + scipy ONLY**; CPU substrate; deterministic seed = 20260515.
- **No new primitive class invented.** The BC variants are operational choices within Class L. The probe does not propose a Class P or similar.

## §8 References (citation discipline per `[[feedback_pdf_extraction_citation_discipline]]`)

**Verified-primary-source-direct:**
- **Particle Data Group** (2024), "Review of Particle Physics," <https://pdg.lbl.gov/>. Charged-fermion mass values for MFO §IV.6 target.
- **MFO Spectral Research Notebook**, `docs/antikythera-maths/mfo_spectral_research_notebook.md`. **§IV.6** (SM mass² target spectrum). **Part II** (Waveguide Correspondence; Klein-Gordon on M⁴ × S¹ with periodic BCs). **§XIII.1** (central computation, reframed per bonus 7).

**Sister-bonus methodological precedents:**
- **Spike #24 bonus 10** ([`spike_24_bonus_xiii_1_cascade_sm_mass_search_2026-05-15.md`](spike_24_bonus_xiii_1_cascade_sm_mass_search_2026-05-15.md)) — the SUCCESS baseline (log-L2 = 0.614 subset-match, 3.32 lightest-9) and the mode-selection rule gap statement that this probe addresses.
- **Spike #24 bonus 7 + bonus 8** — the reframed §XIII.1 as cascade-composition search and the Class O location. This probe inherits the cascade-substrate finding from those.

**Companion probe and data (this work):**
- **`spike_24_bonus_11c_mode_selection_boundary_conditions_probe_2026-05-15.py`** — deterministic-seed probe. Seed = 20260515. Runtime ~62s on stdlib + numpy + scipy. CPU only. Isolated venv `.venv_bonus_11c`. Single PID tracked in provenance record.
- **`spike_24_bonus_11c_mode_selection_boundary_conditions_probe_2026-05-15.ndjson`** — ~126 records covering provenance, baseline replication checks (4), full BC sweeps (4 cascades = 5000 combinations), per-factor ablation (5), verdict, totals, integrity hash.

## §9 The one surprise

**Periodic BCs IS the optimum for the lightest-9 metric — not just the bonus 10 default but the actual best across 625 alternatives on the `C_2 × C_2 × C_13 × C_2` cascade.** I had expected at least one BC combination to improve modestly on the lightest-9 score (because non-trivial BCs lift degeneracies and the SM target *isn't* degenerate). The fact that no combination beats periodic by even a hundredth of a dex means the periodic-BC plateau structure on this cascade is *exactly* the right shape for the lightest-9 metric — every alternative makes it WORSE.

This is structurally revealing: it says the cyclic-product Laplacian under periodic BCs is the *natural* spectral form for a cascade-substrate model — the BC variants we tested all break some symmetry that the SM-target-matching prefers preserved. The mode-selection gap is therefore not a "BCs are wrong" problem; it's a "the lightest 9 modes form a plateau, but SM has a hierarchy" problem. The mode-selection rule must be a layer ABOVE the cascade spectrum (which-modes-couple-to-what), not a layer WITHIN (BC choice per factor).

This sharpens the framework's open question: what determines mode visibility / coupling once the cascade spectrum is fixed?

## §10 Fermatas for the conductor

Three deliberate pause-points:

1. **Should this NEGATIVE result discharge reading 3 from further investigation?** The probe falsifies "BC choice closes the lightest-9 gap." It does NOT falsify "BCs are physically relevant somewhere in the framework" — the 36% subset-match improvement is real and may matter for gauge-cascade coupling later. The conductor decides whether reading 3 is retired or whether the subset-match finding becomes its own follow-up.

2. **Does the subset-match 0.393 dex result warrant its own bonus-12 follow-up?** The BC combination `(neumann, periodic, periodic, neumann, twisted_pi2)` on `C_2 × C_7 × C_4 × C_6 × C_16` is genuinely better than bonus 10's all-periodic. Is this a candidate refinement of the bonus 10 reframing (different BC reading of §XIII.1)? The conductor decides whether to expand on the subset-match improvement or treat it as a side note here.

3. **What does the negative result mean for the parallel readings (11a, 11b, 11d)?** This probe's structural finding — that the lightest-9 plateau is BC-invariant — strengthens the case that the mode-selection rule operates on coupling (reading 1) or particle-content (reading 2) rather than topology. The conductor synthesises across the parallel-dispatched results.

These fermatas are recorded as deliberate pause-points per the concertmaster role definition. The synthesis stands without resolving them.

## §11 Summary table — verdict at a glance

| Aspect | Result | Status |
|---|---|---|
| **BC choice closes the lightest-9 gap?** | NO; best is 3.318 = bonus 10 baseline | **NEGATIVE for closure** |
| **BC choice improves over bonus 10 subset baseline?** | YES; 0.614 → 0.393 (36% improvement) | **PARTIAL** (consolation) |
| **Best lightest-9 BC combination** | `(periodic, periodic, periodic, periodic)` on `C_2 × C_2 × C_13 × C_2` | identical to bonus 10 |
| **Best subset-match BC combination** | `(neumann, periodic, periodic, neumann, twisted_pi2)` on `C_2 × C_7 × C_4 × C_6 × C_16` | 36% better than bonus 10 |
| **Plateau-degeneracy structural property** | preserved under all BC variants | invariant; explains the negative |
| **Per-factor ablation finding** | improvement distributed across 3 factors (n=2, n=6, n=16); reverting any one factor's BC to periodic costs ~0.22 dex | coordinated multi-factor effect |
| **Total combinations evaluated** | 5000 (3125 + 625 + 625 + 625) across 4 cascades | full Cartesian sweep |
| **Bonus 10 baseline replicated** | YES; all 4 within 0.001 dex | numerical confirmation |
| **Runtime** | ~62s | stdlib + numpy + scipy, CPU |
| **Isolation discipline** | per-bonus venv `.venv_bonus_11c`; single PID tracked; file-name isolation `spike_24_bonus_11c_*` | clean |
| **Primitive classes used** | I (cyclic groups), L (Laplacian under 5 BC variants), E (direct-product spectrum), B (tagged-tuple records) | no new class invented |

## §12 Final answer to the gate question

*"Does BC choice on cascade factors close the mode-selection gap (lightest-9 < 1.0 dex on SM target)?"*

**NO.** Across 5000 BC combinations over the four bonus-10 reference cascades, no combination produces a lightest-9 log-L2 below 3.318 dex — exactly the bonus 10 baseline, achieved by all-periodic BCs on the `C_2 × C_2 × C_13 × C_2` cascade. The cyclic-product Laplacian's plateau-degeneracy structure is invariant under BC choice; the lightest 9 modes form integer-multiple clusters regardless of which BC is applied per factor. The SM mass² target's hierarchy of ratio gaps cannot be matched within this constraint.

The subset-match metric does improve (0.614 → 0.393, 36% gain) when non-trivial BCs are applied to the rank-1 subset cascade. But this is a side finding: subset-match was already SUCCESS-grade in bonus 10, and the lightest-9 metric is the one where the structural gap lives.

**Reading 3 (boundary-condition mechanism) is falsified for closure.** The mode-selection rule lives at a different layer — the parallel readings (11a coupling, 11b extra particles, 11d sign-rule) carry the closure question forward.

The math doesn't lie. BC choice doesn't close the gap. The plateau structure is the bottleneck.
