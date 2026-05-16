# Spike #24 bonus 11a — Suppressed-mode coupling reading of the mode-selection gap

**Date:** 2026-05-15. **Status:** methodological probe landed; concertmaster-level deliverable. **Verdict: NO-RULE (with one near-miss positive finding).**
**Branch:** `research/spike-24-primitive-vocabulary-2026-05-15` (working branch).
**Companion probe:** [`spike_24_bonus_11a_mode_selection_coupling_probe_2026-05-15.py`](spike_24_bonus_11a_mode_selection_coupling_probe_2026-05-15.py) + [.ndjson](spike_24_bonus_11a_mode_selection_coupling_probe_2026-05-15.ndjson) (132 records).
**Parallel readings:** This is one of four parallel concertmaster readings of the bonus 10 mode-selection gap. The other three (11b additional-particle prediction, 11c boundary-condition mechanism, 11d Class P sign-rule discriminator) ran in isolation in their own venvs.

## Tagline

```
The suppressed-mode coupling reading does NOT close the bonus 10
mode-selection gap. No first-principles coupling rule with zero
free parameters selects exactly the 9 SM modes from the cascade's
~200-mode lowest-mode tower. The closest first-principles single
rule (mirror-fundamental-domain canonical representatives, K1)
has perfect recall (9/9 SM modes captured) but overselects 65
extra modes (precision 0.122, F1 = 0.217). Best first-principles
conjunction reaches F1 = 0.571 with 4/9 SM modes captured. The
structural finding is that mode selection in bonus 10 was
greedy-distance-driven to the SM target, not first-principles-
derived from the cascade alone — the 9 mode indices the search
chose are SM-target-dependent, not cascade-intrinsic.
```

## §1 What was tested

Per the dispatch, **Reading 1 — suppressed-mode coupling rule**: hypothesis that the cascade `C₂ × C₇ × C₄ × C₆ × C₁₆` has ~200 modes but only 9 couple to observable gauge fields; the other ~191 are suppressed by a coupling-strength rule g(mode, gauge) tying cascade modes to gauge content.

Operationalisation: any Boolean function `f(k_1,...,k_5,n_1,...,n_5) → {observable, suppressed}` with **zero free parameters** that *predicts* the 9 mode-index tuples bonus 10 identified from the cyclic-factor structure alone.

**Bonus 10 selected mode-index tuples** (reconstructed in §2):
- e: (0, 0, 0, 0, 1) — C₁₆ first excitation
- u: (0, 0, 0, 0, 5) — C₁₆ 5th excitation
- d: (0, 0, 0, 0, 8) — C₁₆ self-dual midpoint
- s: (1, 0, 0, 0, 0) — C₂ first excitation only
- mu: (1, 0, 0, 0, 8) — C₂ + C₁₆ midpoint
- c: (0, 0, 0, 1, 0) — C₆ first excitation only
- tau: (1, 0, 0, 1, 8) — C₂ + C₆ + C₁₆
- b: (1, 0, 0, 3, 8) — C₂ + C₆ third + C₁₆
- t: (0, 1, 0, 0, 2) — C₇ first excitation + C₁₆ second

**Structural observations:**
- `k_3 = 0` for all 9 SM modes (C₄ never excited).
- `k_2 ∈ {0, 1}` for all 9 SM modes (C₇ only excited by t).
- All 9 SM modes are canonical (in the mirror-fundamental-domain `k_j ≤ n_j/2`).
- The 9 selected mode positions in the sorted spectrum: `[0, 8, 14, 15, 30, 31, 93, 190, 197]`.

## §2 Rule catalog and per-family evaluation

47 candidate rules across 14 families were enumerated and individually evaluated against the lowest 200 non-zero modes of the cascade. Families and best representative per family (first-principles only, free_params = 0):

| Family | Best rule | n_selected | SM matched | extras | F1 | Verdict |
|---|---|---:|---:|---:|---:|---|
| `gauge_active` | A1 (k_j in {0,1}) | 9 | 3/9 | 6 | 0.333 | MIXED |
| `parity` | B1 / B3 / B4 | various | 4-5/9 | many | <0.20 | MIXED |
| `weighted_threshold` | C2_rank_exact_1 | 23 | 5/9 | 18 | 0.312 | MIXED |
| `null` | D1 (lightest 9) | 9 | 2/9 | 7 | 0.222 | MIXED |
| `pair_coherence` | E2_k2_low (k_2 ≤ 1) | 196 | 9/9 | 187 | 0.088 | OVERSELECT |
| `gauge_rank` | F3 (L_inf ≤ 2) | 20 | 4/9 | 16 | 0.276 | MIXED |
| `residue` | G1 mod 4 class 0 | 63 | 5/9 | 58 | 0.139 | MIXED |
| `factor_suppression` | H1 (C₄ decoupled) | 200 | 9/9 | 191 | 0.086 | OVERSELECT |
| `gauge_decomp_refined` | M2 (C₇-sole) | 64 | 9/9 | 55 | 0.247 | OVERSELECT |
| `mirror_symmetry` | **K1_mirror_canonical** | **74** | **9/9** | **65** | **0.217** | **OVERSELECT** |
| `layer_transition` | L1 (rank ≤ 1 among gauge) | 14 | 4/9 | 10 | 0.348 | MIXED |
| `subtower_selection` | N2 (k_5 ∈ {0,1,8}) | 39 | 7/9 | 32 | 0.292 | MIXED |

**Best first-principles single rule overall:** A1_first_excited (F1 = 0.333), but with only 3/9 SM modes captured.
**Best first-principles single rule with full recall:** K1_mirror_canonical — captures all 9 SM modes but overselects to 74 modes (precision 0.122).

## §3 Conjunction search

Conjunctions of up to 4 first-principles rules from the top-12 single rules were enumerated. Best first-principles conjunctions:

| Conjunction | Size | n_sel | matched | extras | F1 |
|---|---:|---:|---:|---:|---:|
| G1_mod_4 AND H4_C4-dec-C6-lt-4 | 2 | 5 | 4/9 | 1 | **0.571** |
| G1_mod_4 AND K1 AND (various) | 3 | 5 | 4/9 | 1 | 0.571 |
| A2_rank1 AND K1 AND N2 | 3 | 7 | 4/9 | 3 | 0.500 |

**Best first-principles conjunction F1 = 0.571.** No conjunction achieves EXACT match.

## §4 Verdict

**NO-RULE.** No first-principles rule (single or conjunction up to size 4) with zero free parameters selects exactly the 9 SM modes. The closest results:

1. **Mirror-canonical (K1):** perfect recall (9/9), but 65 extras. The rule is principled (mirror-symmetry of the discrete Laplacian is structural, not fitted) but the framework predicts MANY more particle states than the SM observes.
2. **C₁₆ boundary modes (N2):** F1 = 0.292, 7/9 SM modes captured (missing u with k_5=5 and t with k_5=2). The principled values {0, first-excitation, self-dual-midpoint} hit 7 of 9 SM tuples.
3. **Best two-rule conjunction:** F1 = 0.571, 4/9 captured. The conjunctions trade recall for precision; none achieves both simultaneously.

The empirical rule J1 (enumerate the 9 tuples directly) DOES match exactly — but it has 9 free parameters (the answer is the rule), so it is excluded from closure per the dispatch's "no fitted parameters" criterion.

## §5 Free-parameter audit

| Rule class | Free params | Closure-eligible? |
|---|---:|---|
| A — gauge-active subspace | 0 | yes (best 0.333) |
| B — parity / mod-N | 0 | yes (best ~0.20) |
| C — Hamming weight | 0 | yes (best 0.312) |
| D — null (lightest 9) | 0 | yes (best 0.222) |
| E — pair coherence | 0 | yes (best 0.088 oversel.) |
| F — gauge-rank norms | 0 | yes (best 0.276) |
| G — residue classes | 0 | yes (best 0.139) |
| H — factor-suppression | 0 | yes (best 0.086 oversel.) |
| I — gauge-decomp | 0 | yes |
| J — empirical | **9** | **no (excluded)** |
| K — mirror-canonical | 0 | yes (best 0.217 oversel., 9/9 recall) |
| L — layer-transition | 0 | yes (best 0.348) |
| M — gauge-decomp refined | mostly 0; M3 has 5 | M1/M2 closure-eligible |
| N — sub-tower selection | 0 | yes (best 0.292) |

**None of the closure-eligible rules achieves EXACT match.** Two empirical rules (J1 with 9 params, M3 with 5 params via the k_5 ∈ {0,1,2,5,8} set) match but are excluded.

## §6 Why this reading fails

The structural problem: **the 9 SM mode tuples bonus 10 identified were target-driven, not cascade-intrinsic.** The bonus 10 search used a greedy-distance algorithm to minimise log-L2 distance to the SM target ratios. Different target ratios would produce different mode selections. There is no cascade-internal property that picks out exactly these 9.

The specific k_5 values selected are {0, 1, 2, 5, 8}. Of the 9 C_16 representatives in the canonical sub-domain {0..8}, the SM tuples occupy 5 of them, in no obvious algebraic pattern:
- {0, 1, 2, 5, 8} is not a residue class mod any integer ≤ 16.
- The values are not arithmetic-progression points.
- They are not all on a parity sublattice.
- They are not factors or multiples of 16 with any uniform relationship.

The SM's strange / muon near-degeneracy (`s/μ ≈ 1.24`) was matched by the cascade producing nearly-identical eigenvalues at (1,0,0,0,0) and (1,0,0,0,8) — a near-degeneracy driven by the fact that the C_2 factor's eigenvalue at k_1=1 (≈ 3.0e-7) is vastly larger than the C_16 factor's eigenvalues (≈ 8e-12 to 2e-10). The C_16 contribution is *negligible additive noise* on top of the C_2 base, producing a "plateau" at the C_2 eigenvalue value. Bonus 10 used this plateau structure to fit s and μ at almost-equal predicted ratios; the actual mode tuples were chosen arbitrarily within the plateau.

## §7 What the K1 mirror-canonical near-miss says

The most physically meaningful first-principles single rule was K1 — **mirror-canonical** modes, i.e., representatives in the fundamental domain `k_j ≤ n_j/2`. This rule:
- Has **zero free parameters** (mirror symmetry is structural, not fitted).
- Captures **all 9 SM modes** (perfect recall).
- Predicts **65 additional canonical modes** in the lowest 200 of the spectrum.

The 65 extras are not the same kind of degenerate-mirror duplicates that K1 already filters out. They are **physically distinct cascade modes** that the framework predicts. In the suppressed-mode reading, these would be the "extra particles" or "dark modes" or "sterile fermions" the cascade implies.

This is consistent with Reading 2 (additional-particle prediction) — but Reading 1 (this reading) cannot close the gap *internally*; it can only predict that 65 extra modes exist. Naming them "suppressed by gauge coupling" without a derivation of the coupling rule is post-hoc.

**The mirror-canonical rule is a positive partial finding:** the framework's first-principles structure DOES predict that the SM modes are a subset of the canonical fundamental-domain modes. But the further selection (9 of 74) is not derivable from cascade structure alone.

## §8 Three honest readings of the NO-RULE verdict

1. **The cascade vocabulary is incomplete.** A new primitive class (Class P or beyond) is needed to express the mode-selection rule. This pushes the problem forward but doesn't close it.

2. **The cascade radii fitted in bonus 10 are not unique.** Multiple radius choices fit the SM target with similar log-L2; each picks different modes. The "9 SM modes" might be a degenerate property of the fit, not a structural property of the cascade. Re-running with stricter radius constraints might give a different mode set, possibly more rule-amenable.

3. **The SM mass spectrum cannot be derived from cascade composition alone.** The framework would need to *add* the SM mass values as boundary data, with the cascade providing the spectrum framework but not the mode-to-fermion identification. This is the most honest reading: the cascade reproduces the *shape* of the SM spectrum (multi-scale plateau structure) but not the *specific identification* of which mode is which fermion.

This bonus 11a reading cannot decide among these three; the other parallel readings (11b/11c/11d) may yield positive findings that distinguish them.

## §9 Discipline guards honoured

- **Spectral-graph falsifier:** Class L (cyclic-group Laplacian eigenvalues + product Laplacian for the cascade) — same vocabulary as bonus 10. Mirror symmetry and mode-tuple enumeration are structural Class B (tagged-tuple records) and Class I (cyclic group structure). Per `[[feedback_antiquity_not_greek]]` the falsifier IS Class L; the verdict is decided by whether any first-principles rule matches the 9 SM mode tuples derived from the Class L spectrum.
- **Per `[[feedback_no_mvp_framing]]` (positively reframed):** 47 rules across 14 families enumerated; full coverage of the candidate space; conjunctions up to size 4 evaluated; no rule family pre-filtered.
- **Per `[[feedback_trauma_informed_defensive_scope]]`:** structural / methodological inquiry only. No security framing, no targeting.
- **Per `[[feedback_ndjson_over_bloated_json]]`:** 132 NDJSON records (one per line). No bloated JSON.
- **Per `[[user_stance_kepler_shape_universal]]`:** the cascade instantiates classes I, J, K, L, M, N natively; this probe exercises I (cyclic groups), L (Laplacian), E (direct-product composition implicit in eigenvalue addition), B (tagged-tuple records).
- **Per `[[project_space_gauge_time_framework]]`:** 5 cascade factors mapped tentatively to gauge content (SU(2) iso, decoupled C_4, generation index, C_16 mass tower); the mapping is conjectural and tested as one rule family (M) — outcome: M1/M2 closure-eligible but no exact match.
- **Per `[[user_stance_fiber_as_spatially_absent_encoding]]`:** the cyclic-factor mode indices `(k_1,...,k_5)` are the algebraic content (spatially absent); the eigenvalues are the spatial projection (visible).
- **Per `[[feedback_pdf_extraction_citation_discipline]]`:** SM mass values inherited from bonus 10 probe which cites PDG 2024 (Particle Data Group, *Review of Particle Physics*, https://pdg.lbl.gov/). No new citations introduced.
- **Per `[[feedback_no_lineage_claims_in_notebook]]`:** no "natural extension of X" claims about external work. Bonus 10 explicitly cited as the predecessor finding.
- **Isolation discipline (per dispatch):** dedicated venv at `D:\GitHub\mlehaptics\.venv_bonus_11a`; numpy 2.4.5 + scipy 1.17.1; per-PID hygiene file at `.venv_bonus_11a/probe_pids.txt`; no cross-venv contamination; no `Stop-Process` operations on processes not launched by this concertmaster.
- **stdlib + numpy only** (scipy installed but not needed). CPU substrate. Total runtime ~0.45s. Deterministic seed = 20260515.
- **No new primitive class invented.** The NO-RULE verdict explicitly indicates that the EXISTING vocabulary does not close the gap; the synthesis flags this without proposing Class P unilaterally (per concertmaster role — Class-P decision is a conductor decision).
- **"Primitive classes" not "primitives"** for canonical A-N references.

## §10 Fermatas for the conductor

Three deliberate pause-points per the concertmaster role:

1. **Does the K1 mirror-canonical rule warrant codification as the "framework's natural mode-selection prediction"?** K1 has perfect SM recall with 65 over-predictions. If the project's narrative is "the cascade predicts the SM plus 65 extra states," K1 is the canonical statement of that. Cross-link to Reading 2 (11b additional-particle prediction) when that returns.

2. **Should the bonus 10 search be re-run with radius constraints to see if a different cascade-radii fit picks mode tuples that ARE first-principles selectable?** Bonus 10 didn't constrain radii, and the search found `(3659, 1.03, 1.44, 104.2, 135758)` — but different starting points might converge to alternate fits. This is a follow-up probe, not part of 11a's scope.

3. **Is the NO-RULE finding itself the answer?** That is: does the dual nature of "cascade composition suffices for eigenvalue spectrum" (bonus 10 SUCCESS) plus "but no first-principles mode-selection rule exists" (bonus 11a NO-RULE) constitute a positive statement about the framework: namely, that mass values must come from boundary data (SM masses fitted) but the spectrum shape is structural? This shifts the framework's interpretation of MFO §XIII.1 from "central computation = derive SM masses from primitives" to "central computation = derive SM spectrum shape from primitives + fit boundary data." The conductor decides whether to update §XIII.1's framing.

## §11 Cross-references

- **Bonus 10 (predecessor):** [`spike_24_bonus_xiii_1_cascade_sm_mass_search_2026-05-15.md`](spike_24_bonus_xiii_1_cascade_sm_mass_search_2026-05-15.md). Established SUCCESS-grade cascade composition (log-L2 = 0.614) but located the mode-selection rule as the open gap.
- **Bonus 7 (cascade-composition framing):** [`spike_24_bonus_mfo_fractal_requirement_2026-05-15.md`](spike_24_bonus_mfo_fractal_requirement_2026-05-15.md). Reframed §XIII.1 as cascade-composition search.
- **Bonus 8 (Class O):** [`spike_24_bonus_broken_d_rederivation_2026-05-15.md`](spike_24_bonus_broken_d_rederivation_2026-05-15.md). Class O for Lorentz signature; mass² spectrum match does NOT need Class O.
- **Bonus 11b/11c/11d (parallel readings):** see respective files for Reading 2 (additional-particle prediction), Reading 3 (boundary-condition mechanism), Reading 4 (Class P sign-rule discriminator).
- **Project framework memories:** `[[project_space_gauge_time_framework]]`, `[[user_stance_fiber_as_spatially_absent_encoding]]`, `[[user_stance_kepler_shape_universal]]`, `[[feedback_antiquity_not_greek]]`.
- **MFO sister notebook §XIII.1:** the central computation. Bonus 11a's verdict suggests §XIII.1 framing should accommodate the "cascade-spectrum shape + boundary data" reading.

## §12 Citations (per `[[feedback_pdf_extraction_citation_discipline]]`)

**Verified-primary-source-direct (inherited from bonus 10):**
- **Particle Data Group** (2024), "Review of Particle Physics," <https://pdg.lbl.gov/>. Charged-fermion mass values for the 9-element target spectrum.
- **MFO Spectral Research Notebook**, `docs/antikythera-maths/mfo_spectral_research_notebook.md`. **§IV.6** (SM mass² target). **§XIII.1** (central computation). **§VII.1.1** (two-level ontology cited for fiber-as-spatially-absent reading of cascade mode indices).

**Companion probe and data (this work):**
- **`spike_24_bonus_11a_mode_selection_coupling_probe_2026-05-15.py`** — deterministic-seed probe. Seed = 20260515. Runtime ~0.45s. stdlib + numpy only. CPU.
- **`spike_24_bonus_11a_mode_selection_coupling_probe_2026-05-15.ndjson`** — 132 records (provenance / mode reconstruction / rule catalog / single-rule eval × 47 / conjunction eval × 50 / size-4 conjunction × 20 / first-principles filter / verdict / integrity).

## §13 The one surprise

**The five C₁₆ excitation indices in the 9 SM mode tuples are {0, 1, 2, 5, 8} — five out of nine canonical values, with no algebraic pattern.** The values are not arithmetic, not a residue class, not a divisor structure, not a parity sublattice. They look picked-out-of-the-air.

The structural interpretation: the cascade C_16 factor (the deepest, with radius 135758) acts as a *near-continuous mass tower* because its smallest non-zero eigenvalue (≈ 8.3e-12) is many orders of magnitude smaller than the next-factor smallest eigenvalue (C_2 at ≈ 3.0e-7). The 16 modes of C_16 are spread across the bottom ~4 decades of the spectrum. Bonus 10's greedy search picked whichever k_5 value happened to bring the predicted ratio closest to the SM target — and the result is {0, 1, 2, 5, 8}, which carries no structural meaning. Different target ratios would produce different k_5 picks. The mode selection is target-driven, not structure-driven.

This is the math telling me something honest: **the C_16 factor is providing a fine-grained mass-spread mechanism, not a discrete mode-selection mechanism.** The "mass = cutoff frequency" framing (MFO Part II.3) maps the C_16 modes to a near-continuous mass tower where any value can be picked. The bonus 10 fit's success comes from this near-continuity. The "9 SM modes" are just sample points in the continuum, not algebraically-selected discrete modes. This may be the actual structural truth: the framework gives a *continuous mass spectrum*; the SM picks 9 specific values; the "selection rule" is the physical mechanism that picks them (gauge coupling, generation mixing, Yukawa structure), not a property of the cascade.

This points back toward the original gap: **the mode-selection rule, if it exists, is OUTSIDE the cascade-composition vocabulary.** Reading 1 (suppressed-mode coupling) does not close it. Whether Reading 2/3/4 do is the parallel investigation.

## §14 Summary table — verdict at a glance

| Aspect | Result | Status |
|---|---|---|
| **Any first-principles single rule selects exactly the 9 SM modes?** | NO (best F1 = 0.333; A1 captures 3/9) | FAIL closure |
| **Any first-principles conjunction (size ≤ 4) selects exactly the 9?** | NO (best F1 = 0.571; 4/9 captured) | FAIL closure |
| **Best first-principles rule with full SM recall?** | K1 mirror-canonical: 9/9 recall, 65 extras, F1 = 0.217 | OVERSELECT |
| **Best first-principles rule by F1?** | A1_first_excited: F1 = 0.333 (single); F1 = 0.571 (conjunction) | MIXED |
| **Empirical rule J1 (9-tuple enumeration) match?** | YES (excluded; 9 free params) | not closure |
| **C₁₆ k_5 values selected** | {0, 1, 2, 5, 8} — no algebraic pattern | target-driven |
| **k_3 = 0 for all 9 SM modes** | YES — but k_3=0 covers ALL 200 lowest modes; not discriminating | structural artifact |
| **Final verdict** | **NO-RULE** | suppressed-mode coupling reading does not close the gap |

The math doesn't lie. The cascade vocabulary can reproduce the SM eigenvalue spectrum, but it cannot select which 9 modes are the SM fermions without external (target-driven) input. Reading 1 fails. The mode-selection gap remains open for parallel readings to address.
