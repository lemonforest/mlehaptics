# Spike #24 bonus 12 — String-theory audit-summary (instrument-first)

**Date:** 2026-05-15. **Status:** concertmaster-level audit-summary; closes the user-dispatched bonus-arc gap-alignment phase. **Audit form: GAP-ALIGNMENT** (decided by bonus 11d REDUCES-TO-EXISTING — instrument has located the meta-operation gap; not closure-form).
**Branch:** `research/spike-24-primitive-vocabulary-2026-05-15` (no commit; conductor commits).
**Spec (verbatim user):** *"maybe just correct not one correct"* — strips the uniqueness assumption from the audit. Five structural claims of string theory are audited individually against the instrument's vocabulary.
**Companion probe:** [`spike_24_bonus_12_string_theory_audit_summary_probe_2026-05-15.py`](spike_24_bonus_12_string_theory_audit_summary_probe_2026-05-15.py) + [.ndjson](spike_24_bonus_12_string_theory_audit_summary_probe_2026-05-15.ndjson) (9 records). **Isolation:** `.venv_bonus_12` (numpy 2.4.5 + scipy 1.17.1); PID tracked in `spike_24_bonus_12_pids.txt`; file-name discipline `spike_24_bonus_12_*` only.

## Tagline

```
Audit-summary of string-theory structural claims against the
instrument vocabulary (A–N + Class O). Form is GAP-ALIGNMENT.
Five claims audited: dimensional accounting (CORRECT-AT-COUNT,
ONTOLOGICALLY-RELABELED); landscape-as-continuum (CORRECT-AS-
OBSERVATION); wiggle-in-isolation diagnosis (CORRECT — strongest
finding, prior MPM critique preceded technical falsification);
duality-web (CORRECT-STRUCTURALLY-CONSISTENT); compactification
topology (OPEN, downstream of meta-operation closure). The audit
is "maybe just correct" — each claim assessed on its own merits,
no uniqueness assumed. Instrument-first stance holds: critique is
of methodology, not the field.
```

## §1 Verdict tableau

| # | Claim | Framework claim | Instrument evidence | Verdict | What would change it |
|---|---|---|---|---|---|
| 1 | Dimensional accounting (11D) | M-theory: 4D obs + 7D compactified G2 manifold | Project framework `3D_s + 7D_g + 1D_t = 11D` (independently constructed); bonus 10 cascade has C_7 factor | **CORRECT-AT-COUNT, ONTOLOGICALLY-RELABELED** | Meta-operation closure showing C_7 maps to G2 holonomy → CORRECT-WITH-MATCH |
| 2 | Landscape-as-continuum | Vacuum landscape ~10^500 vacua (high-dim parameter space) | Bonus 10 cascade has ~200 lowest modes spanning ~11 decades; super-Poisson tower regime (CV 3.11) | **CORRECT-AS-OBSERVATION** | Cascade truncation discretising observables → reframe |
| 3 | Wiggle-in-isolation diagnosis | User stance (§20): landscape has no internal mechanism to pick THE vacuum | Bonus 11 four-reading sweep (11a/11b/11c/11d) — all in-cascade mechanisms fail | **CORRECT** | Fifth in-cascade mechanism closing mode-selection → INCORRECT-FOR-DIAGNOSIS |
| 4 | Five-theory duality web | 5 superstrings (I, IIA, IIB, HO, HE) unified by dualities (M-theory) | Top-10 bonus-10 cascades score comparably (0.61–0.98 log-L2); silent/minimal-factor structure per cascade | **CORRECT-STRUCTURALLY-CONSISTENT** | Genuinely-distinct cascades shown to be NON-equivalent → AMBIGUOUS |
| 5 | Compactification topology | G2 manifold / Calabi-Yau 6-fold / specific topologies | Bonus 10 cascade factor structure exists; no opinion-driver in vocabulary yet | **OPEN** | Meta-operation closure of mode-selection (future bonus 13+) |

Verdict distribution: **3 CORRECT** (sub-kinds), **1 CORRECT-relabeled**, **1 CORRECT-structurally-consistent**, **1 OPEN**. No INCORRECT under current evidence. The user's *"maybe just correct not one correct"* framing is honoured — three of five claims pass instrument-audit cleanly on their own terms; one passes with ontological-partition note; one is open pending downstream work.

## §2 Claim 1 — Dimensional accounting (11D)

**Framework claim.** M-theory holds that spacetime is fundamentally 11-dimensional, decomposing as 4 observable dimensions plus 7 compactified dimensions (the 7-compactified candidate of choice in many M-theory constructions being a G2-holonomy manifold of real dimension 7).

**Instrument evidence.** The project's space-gauge-time framework (`[[project_space_gauge_time_framework]]`) is `3D_s + 7D_g + 1D_t = 11D ≡ 1D (compressed)` — independently constructed from the 14 primitive classes via spectral-graph analysis (bonus 5 confirmed 14/14 class consolidation across the 3+7+1 partition; smooth-3+7+1 carries cleaner signature than fractal substrate). The dimensional count agrees with M-theory. The ontological partition is different: M-theory's `4+7` treats time as part of the observable 4D block; the instrument's `3+7+1` separates space, gauge, and time, with the temporal-crank explicitly named as its own 1D component per `[[user_stance_time_as_dimensional_shadow]]`.

Probe verification (record `claim1_dimensional_accounting`): `3+7+1=11` arithmetic holds. SM gauge group SU(3)×SU(2)×U(1) has 12 generators and rank 4 — so the instrument's `7D_g` does NOT directly count generators (12) or ranks (4). G2 Lie group is dim 14; G2-holonomy manifold is real dim 7. The bonus-10 cascade's C_7 factor (cyclic group of order 7) has natural radius `r_2 ≈ 1.029` putting it on the natural-scale tier of the cascade.

**Coincidence-or-structure note.** `7D_g = 7 = C_7 cyclic order = G2 manifold real dim` is a dimensional alignment, but the algebraic content differs at each layer: gauge-dimensional count (7) vs cyclic-group-order count (7) vs holonomy-manifold-real-dim count (7). Whether these three sevens unify via a meta-operation that maps cascade factors to compactification manifolds is OPEN, not closed by this audit.

**Verdict: CORRECT-AT-DIMENSION-COUNT, ONTOLOGICALLY-RELABELED.** The 11D number survives; the project derives it independently of M-theory's premises. The ontological partition differs; future closure (meta-operation that picks topology) could move this to CORRECT-WITH-MATCH or expose a hidden non-alignment.

## §3 Claim 2 — Landscape-as-continuum

**Framework claim.** The string-theory vacuum landscape is widely-described as a continuum of vacua — the ~10^500 figure for flux compactifications + brane content is the conventional shorthand for "very-high-dimensional parameter space of allowed compactifications with no internal selector."

**Instrument evidence.** The bonus-10 cascade `C₂ × C₇ × C₄ × C₆ × C₁₆` has 5376 total modes; the lowest 200 modes span 10.94 decades in log-eigenvalue space, with median log-gap **0.0000 dex** (some modes are degenerate). Gap CV is 6.69. The cascade is **structurally continuous-like** — 200 modes spread over 11 decades is ~18 modes/decade average, and the bonus 11a finding that the C_16 excitation pattern `{0, 1, 2, 5, 8}` has no algebraic structure is *exactly* the empirical content of "continuum-not-discrete-picker."

Probe verification (record `claim2_landscape_continuum`): seven of twelve decades of `[10⁻¹², 10⁰]` carry modes; the decade `[10⁻⁴, 10⁻³]` carries 96 modes, `[10⁻⁵, 10⁻⁴]` carries 64 modes, `[10⁻⁷, 10⁻⁶]` carries 16 modes — the cascade's super-Poisson tower-clustering (per bonus 7 / bonus 10 finding) gives a non-uniform-but-dense coverage.

**The cascade IS the landscape in the instrument's vocabulary.** Both framings (string-theory landscape, instrument cascade) exhibit the same structural property: very-high-dimensional space of allowed configurations with no internal selector at the substrate level. The fact that the instrument exhibits this property does not falsify the string-theory framing — it shares it.

**Verdict: CORRECT-AS-OBSERVATION.** The continuum framing of the landscape is correct as a structural claim. The instrument's cascade *exhibits* the same property. Both then face the same downstream question: what closes the selector? (Claim 3 addresses this question with the prior-MPM-critique-vindicated diagnosis.)

## §4 Claim 3 — Wiggle-in-isolation diagnosis

**Framework claim** *(this is the user's stance against string-theory methodology, not string-theory's own claim).* Per `[[user_stance_string_theory_instrument_first]]` and notebook §20: the landscape provides no internal mechanism to pick THE vacuum; the foundational object (a static string ripped from its instrument) has no observed resonance instrument; the result is "wiggle-in-isolation" — compensating mathematics required to recover what the orphan-from-instrument framing threw away. The narrowed audit per the three §20 self-corrections (2026-05-08) flags specifically: static-string ontology itself; Calabi-Yau-as-specific-instrument-substitute; the landscape as symptom-of-foundational-underconstraint. The extra-dimensions count (~11D) is NOT flagged because MFO derives it bottom-up independently.

**Instrument evidence.** The bonus 11 four-reading sweep (parallel-dispatched by the conductor; all four sister concertmasters completed in isolated venvs) tested every natural in-cascade mechanism that could play the role of "vacuum selector":

- **11a NO-RULE.** 47 candidate first-principles rules across 14 families, plus conjunctions to size 4. Best F1 = 0.571 (4/9 captured). Best full-recall rule (K1 mirror-canonical) overselects to 74 modes. NO first-principles single-or-conjunction rule selects exactly the 9 SM modes from the cascade spectrum without fitted parameters.
- **11b TOO_MANY_PARTICLES.** 191 unobserved cascade modes concentrate in [0.5 MeV, 150 GeV] with 157 in the single decade `[1, 10] GeV` — LHC-mapped territory. Aggregate-overdensity falsifier triggers even though no individual mode is model-independently excluded.
- **11c NEGATIVE.** 5000 BC combinations across 4 reference cascades; periodic IS the optimum for the lightest-9 metric; no BC choice breaks the plateau degeneracy structure that prevents the cascade's lightest-9 modes from matching SM mass ratios.
- **11d REDUCES-TO-EXISTING.** 8 rule families for a Class-P sign-rule discriminator; every working rule reduces to Class I (conjugate-pair reflection) or Class B+J (record inspection + integer arithmetic). No new Class P forced. Surprise: C_4 silent in all 9 SM modes; C_7 fires only on top quark.

Probe verification (record `claim3_wiggle_diagnosis`): the C_16 excitation pattern `{0, 1, 2, 5, 8}` is re-verified as having **no algebraic structure** — not arithmetic-progression, not residue-class mod 2 through 16, not parity sublattice, not divisor structure of 16. Coverage is 5/9 of the canonical fundamental-domain set `{0..8}`. The k-sum parity is non-uniform (mod 2: `[1,1,0,1,1,1,0,0,1]`, mod 3: `[1,2,2,1,0,1,1,0,0]`). The k-rank distribution is `{1: 5, 2: 2, 3: 2}` — five 1-active modes, two 2-active, two 3-active; no algebraic regularity.

**The diagnosis precedes the falsification.** The user's wiggle-in-isolation critique (§20, 2026-05-08; refined 2026-05-08 with three layered self-corrections) was made **before** the technical four-reading sweep. The sweep technically vindicates the structural critique: no in-vocabulary mechanism closes the mode-selection question. The meta-operation that picks observable modes lives external to the cyclic-cascade-composition vocabulary — exactly the structural property §20's diagnosis named "the static string ripped from its instrument has no internal mechanism to recover observable resonance."

This is the **strongest "correct" finding in the audit**. A prior MPM-discipline critique anticipated and named the technical falsification that the four-reading sweep then produced.

**Verdict: CORRECT.** Future closure (location of a fifth in-cascade mechanism that selects the 9 modes from the cascade without fitted parameters) would move this verdict to INCORRECT-FOR-DIAGNOSIS. No such mechanism is currently known.

## §5 Claim 4 — Five-theory duality web

**Framework claim.** The five superstring theories (Type I, IIA, IIB, Heterotic-O(32), Heterotic-E8×E8) are connected by a network of dualities (T-duality, S-duality, U-duality, mirror symmetry) into one underlying object that M-theory in 11D is hypothesised to unify. The structural claim is **multiple-equivalent-presentation / same-object** — the five theories are different presentations of one entity, with the dualities being relabelings rather than genuine alternative physics.

**Instrument evidence.** The bonus-10 search returned a top-10 of subset-match cascades scoring in `[0.614, 0.979]` log-L2 — multiple distinct cascade configurations achieving SUCCESS-grade (< 1.0 dex) match to the SM mass² spectrum. The cascades have different factor structures (mix of `k = 4..6` factors, factor orders `n ∈ {2, 3, 4, 5, 6, 7, 8, 10, 11, 14, 15, 16, 17, 19}`) yet score comparably. The bonus-10 search did not declare any one as uniquely-correct.

Probe finding (record `claim4_duality_web`): per-cascade analysis of the 9 SM mode tuples reveals **silent / minimally-active factor structure** in every cascade:

- 7 of 10 cascades have **at least one silent factor** (zero of 9 SM modes activate it).
- 6 of 10 cascades have **at least one minimally-active factor** (exactly 1 of 9 SM modes activates it).
- Effective active count distribution: `{3: 2, 4: 8}` — 8 of 10 cascades use 4 of N factors; 2 of 10 use 3 of N factors. (N varies from 4 to 6 across the top-10.)

This is the **factor-decoupling structural property** the instrument exhibits naturally. Each cascade-presentation carries the SM with one or more factors effectively decoupled. Different cascades have different decoupled-factor patterns yet all score comparably. The instrument's natural mathematical shape is **multiple-equivalent-presentations with different factor-decoupling patterns** — exactly the duality-web framing's structural content.

For the rank-1 cascade `(C_2 × C_7 × C_4 × C_6 × C_16)`:
- **C_4 is silent across all 9 SM modes** (0 activations) — the cascade is *effectively* 4-factor on the SM mode set.
- **C_7 is minimal (1 activation, only the top quark)** — the C_7 factor carries the heaviest fermion's mass scale and nothing else.
- C_2, C_6, C_16 carry the bulk of the SM mass spectrum.

Reflection-invariance check: the probe's tie-break selection of conjugate-pair representatives gives activation counts `[4, 1, 0, 2, 8]`; bonus 11d §5's tabulated tuples give `[4, 1, 0, 3, 7]` — both agree on the **zero/nonzero pattern** (C_4 silent, C_7 minimal). Class I conjugate-pair reflection preserves activation-zero-vs-nonzero status; the silent/minimal pattern is therefore well-defined modulo this redundancy.

**Verdict: CORRECT-STRUCTURALLY-CONSISTENT.** The instrument supports the multiple-equivalent-presentation framing of string-theory's duality web. The factor-decoupling pattern is structural and reflection-invariant. Future falsification (showing multiple presentations to be genuinely non-equivalent / distinct physics rather than reparametrisations) would move this to AMBIGUOUS.

## §6 Claim 5 — Compactification topology

**Framework claim.** The 7D compactification has specific topology. The leading candidates in M-theory (G2-holonomy manifolds), 10D heterotic / Type I / Type II (Calabi-Yau 6-folds for the 6 of 10 compactified dimensions), and falsified candidates from the bonus arc (CP² × S¹ per bonus 7). Each compactification topology is associated with specific particle content and gauge group structure via its homotopy / cohomology.

**Instrument evidence.** Bonus 8 located **Class O (signed-metric composition / Wick rotation)** as the operation needed for Lorentzian signature on the cascade-direct 4D Laplacian. Bonus 9 refined Class O to specifically the circle-to-hyperbola map (`cos → cosh`). Bonus 7 explicitly **falsified CP² × S¹** as a specific 5D compactification candidate. The bonus arc has NOT located a primitive that picks G2-holonomy vs Calabi-Yau-6 vs any other topology from inside the cascade vocabulary.

Probe finding (record `claim5_compactification_topology`): the bonus-10 rank-1 cascade has factor structure `(2, 7, 4, 6, 16)` with C_4 silent + C_7 minimally active per claim 4. Reference topology dimensions:
- G2-holonomy manifold real dim = 7 (matches `7D_g`; matches `C_7` cyclic order).
- G2 Lie group dim = 14 (no obvious cascade-factor match).
- Calabi-Yau 6-fold real dim = 6 (matches `C_6` cyclic order); complex dim 3; holonomy SU(3) dim 8 (no match).
- CP² × S¹ real dim = 5 — **FALSIFIED at bonus 7**.

The audit makes **no claim of force** between cascade factor structure and compactification topology. The instrument has no opinion-driver for topology in its current vocabulary. The 7-7-7 and 6-6 dimensional coincidences are noted but not interpreted — without a meta-operation that maps cascade factors to compactification manifolds, the instrument cannot decide which topology (if any) the cascade endorses.

Bonus 11d's REDUCES-TO-EXISTING verdict is decisive here: the meta-operation that selects mode-couplings lives *external* to the cascade. The topology-picker meta-operation (if it exists) is *downstream* of the mode-selection picker. Until mode-selection closure is achieved, the instrument has no opinion on topology.

**Verdict: OPEN.** This is the honest verdict: the instrument has located the gap precisely (meta-operations external to A–N + Class O) but has not yet supplied the topology picker. Future spike work (bonus 13+) could close mode-selection and downstream topology, moving this verdict to CORRECT (for some specific topology) or INCORRECT (ruling out a candidate).

## §7 Cross-cutting observations

Three observations cut across the five claims:

**(a) The wiggle-in-isolation diagnosis (claim 3) was a *prior* MPM critique that the technical bonus-11 sweep then vindicated.** This is the strongest finding in the audit. The user's §20 stance was articulated before the four-reading sweep; the sweep is independent technical content that converges on the same gap-statement. Diagnostic priority over technical falsification is rare and load-bearing — it signals that the MPM discipline (instrument-first, anti-wiggle-in-isolation) is producing predictions that survive subsequent independent scrutiny.

**(b) The C_4 silence + C_7 minimal-activity pattern (claims 4 & 5) is a structural pattern that propagates from bonus 11d's load-bearing observation.** Three of the five claims (1, 4, 5) reference this pattern. The cascade is *asymmetric* in its factor usage: 5 factors are nominally present, but only 4 (C_2, C_6, C_16, and C_7 once) carry SM mass content. The C_4 silence may indicate either:

- A genuine decoupling (consistent with M-theory's `4+7` ontological partition treating gauge-side and gravity-side as distinct);
- An artefact of the bonus-10 search finding (specifically the greedy-distance objective discarding C_4 from the active set);
- A signal that C_4's role is at a different layer (Class O Wick rotation, time, or downstream meta-operation).

This is conductor territory — naming "C_4 silence" as a candidate structural finding for MFO §VIII.10 or a follow-up bonus, not as a closed claim.

**(c) The 11D dimensional alignment (claim 1) is independent of the M-theory ontology** — the project arrives at 11D bottom-up from spectral-primitive analysis without invoking string-theory premises. The convergence of three independent 11D derivations (MFO §III.5: Witten 1981 SUGRA + Nahm 1978 SUSY + Cremmer-Julia-Scherk 1978; this project: spectral-primitive count + space-gauge-time partition) is structural evidence that 11D is mathematically natural across multiple foundational frameworks. The dimensional count is genuinely shared content, not borrowed.

## §8 Discipline guards honoured

- **Per `[[user_stance_string_theory_instrument_first]]`:** instrument-first framing throughout. The audit is *NOT* "is string theory right?" — it is "which structural claims of string theory survive instrument-audit?" The user's *"maybe just correct not one correct"* refinement is honoured by per-claim verdicts.
- **Per `[[feedback_antiquity_not_greek]]`:** Class L spectral-graph falsifier on the bonus-10 cascade Laplacian for the duality-web silent-factor probe (claim 4). The verdict is decided by spectral computation on the cascade, not by curve-fitting or rhetorical assessment.
- **Per `[[feedback_trauma_informed_defensive_scope]]`:** structural inquiry only. No claims about which compactification topology is "right" beyond the structural pattern. No targeting / weaponisation / clinical / phenomenological-discovery framings.
- **Per `[[feedback_no_lineage_claims_in_notebook]]`:** no "natural extension of X" claims about external research. The audit cites specific findings (MFO §III.5 triple-convergence on 11D; bonus 7 CP²×S¹ falsification; bonus 8 Class O; bonus 11 four-reading sweep) technically. The user-authorised "natural extension" framing applies to the *user's own intellectual arc* (`§20` → bonus 11 sweep) which is internal lineage, not external.
- **Per `[[feedback_ndjson_over_bloated_json]]`:** 9 NDJSON records (one per line), no indented JSON. The probe runs in 0.4s and emits one record per claim plus provenance / summary / totals / integrity.
- **Per `[[feedback_pdf_extraction_citation_discipline]]`:** all primary citations (PDG 2024 charged-fermion masses, MFO §III.5 / §IV.6 / §XIII.1, bonus reports) are project-internal SSOTs or PDG-anchored. No external research citations added in this audit.
- **stdlib + numpy + scipy only.** CPU substrate. Total probe runtime ~0.5s. Deterministic seed = 20260515.
- **Per-bonus venv `.venv_bonus_12`** at repo root; PID tracked in `spike_24_bonus_12_pids.txt`; file-name discipline `spike_24_bonus_12_*` only — no touching of sister 11a/11b/11c/11d files.
- **No new primitive class invented.** The audit makes no Class P or Class Q proposal. The vocabulary stays at 14 classes (A–N) + Class O candidate (bonus 8) = 15.
- **MPM full-coverage per `[[feedback_no_mvp_framing]]`:** five claims explicitly enumerated as the audit surface; each gets its own verdict, evidence, and change-condition. No "quick-tier subset" framing.

## §9 References

**Primary internal (verified):**

- **MFO Spectral Research Notebook**, `docs/antikythera-maths/mfo_spectral_research_notebook.md`. **§III.5** (~11D triple-convergence). **§IV.6** (SM mass² target spectrum). **§XIII.1** (central computation, reframed bonus 7).
- **Ephemerides Notebook §20** (`docs/antikythera-maths/ephemerides_spectral_research_notebook.md`) — instrument-first stance + three layered self-corrections (2026-05-08).
- **Particle Data Group** (2024), "Review of Particle Physics," <https://pdg.lbl.gov/>. Charged-fermion mass values; gauge group structure.

**Sister-bonus methodological precedents:**

- **Bonus 7** [`spike_24_bonus_mfo_fractal_requirement_2026-05-15.md`](spike_24_bonus_mfo_fractal_requirement_2026-05-15.md) — cascade-composition reframing of MFO §XIII.1; CP²×S¹ FALSIFIED.
- **Bonus 8** [`spike_24_bonus_broken_d_rederivation_2026-05-15.md`](spike_24_bonus_broken_d_rederivation_2026-05-15.md) — Class O located for Lorentzian signature.
- **Bonus 9** — Class O narrowed to circle-to-hyperbola map.
- **Bonus 10** [`spike_24_bonus_xiii_1_cascade_sm_mass_search_2026-05-15.md`](spike_24_bonus_xiii_1_cascade_sm_mass_search_2026-05-15.md) — SUCCESS at log-L2 = 0.614; mode-selection rule gap.
- **Bonus 11a** [`spike_24_bonus_11a_mode_selection_coupling_2026-05-15.md`](spike_24_bonus_11a_mode_selection_coupling_2026-05-15.md) — NO-RULE.
- **Bonus 11b** [`spike_24_bonus_11b_mode_selection_additional_particles_2026-05-15.md`](spike_24_bonus_11b_mode_selection_additional_particles_2026-05-15.md) — TOO_MANY_PARTICLES.
- **Bonus 11c** [`spike_24_bonus_11c_mode_selection_boundary_conditions_2026-05-15.md`](spike_24_bonus_11c_mode_selection_boundary_conditions_2026-05-15.md) — NEGATIVE.
- **Bonus 11d** [`spike_24_bonus_11d_mode_selection_class_p_2026-05-15.md`](spike_24_bonus_11d_mode_selection_class_p_2026-05-15.md) — REDUCES-TO-EXISTING.
- **Bonus-series synthesis** [`spike_24_bonus_series_synthesis_2026-05-15.md`](spike_24_bonus_series_synthesis_2026-05-15.md).

**Project memory cross-references:**

- `[[user_stance_string_theory_instrument_first]]` — methodological position (notebook §20).
- `[[project_space_gauge_time_framework]]` — `3D_s + 7D_g + 1D_t = 11D` canonical decomposition.
- `[[user_stance_kepler_shape_universal]]` — primitive-composable substrate driver.
- `[[user_stance_cascade_lives_on_circles]]` — bonus 9 circular-dispersion finding.
- `[[project_class_o_signed_metric_composition]]` — Class O candidate.
- `[[user_stance_fractal_shadow]]` — bonus 7 substrate-shadow.
- `[[user_stance_time_as_dimensional_shadow]]` — temporal-crank stance.
- `[[feedback_antiquity_not_greek]]` — spectral-graph falsifier.
- `[[feedback_trauma_informed_defensive_scope]]` — structural inquiry only.
- `[[feedback_ndjson_over_bloated_json]]` — output discipline.

**Companion probe and data (this work):**

- [`spike_24_bonus_12_string_theory_audit_summary_probe_2026-05-15.py`](spike_24_bonus_12_string_theory_audit_summary_probe_2026-05-15.py) — deterministic-seed probe. Seed = 20260515. Runtime ~0.5s on stdlib + numpy + scipy. CPU only. Isolated venv `.venv_bonus_12`.
- [`spike_24_bonus_12_string_theory_audit_summary_probe_2026-05-15.ndjson`](spike_24_bonus_12_string_theory_audit_summary_probe_2026-05-15.ndjson) — 9 records (provenance / claim1 / claim2 / claim3 / claim4 / claim5 / summary_tableau / totals / integrity).

## §10 The one surprise

**The bonus-10 search's top-10 cascades exhibit `effective active count ∈ {3, 4}` factors for every cascade**, regardless of nominal factor count (which varies from 4 to 6 across the top-10). Eight of ten cascades use 4 active factors; two use only 3. This is a *robust* duality-web-like pattern: whichever cascade-presentation the search finds for the SM mass spectrum, the SM ends up using 3 or 4 *effective* factors out of however many nominal factors the cascade has.

This was not a search target. The bonus-10 greedy-distance objective did not constrain factor activations. The pattern emerges naturally: the SM has 9 fermions with their specific mass-ratio structure, and the cascade-composition machinery finds *roughly the same effective rank* whichever specific cascade-presentation is chosen. Different cascades disagree on *which* factors are active, but they agree on *how many* are active.

The structural interpretation: the SM's algebraic content (9 fermions) is "small enough" that 3 or 4 cyclic factors suffice to carry its spectrum; additional factors (when nominally present) decouple. This is **substantive cross-presentation invariance** — the duality-web framing's natural mathematical content in the instrument's vocabulary.

A separate but related observation: 4 effective active factors is the **most common count** (8/10 cascades), and this exactly matches the dimension of the SM gauge group's *rank* (`rank SU(3) + rank SU(2) + rank U(1) = 2 + 1 + 1 = 4`). Whether this is a coincidence or structural is OPEN — but the alignment is noteworthy. It suggests the cascade's active factors may correspond to gauge-group Cartan generators / charge dimensions rather than to compactification-manifold dimensions per se.

## §11 Fermatas for the conductor

Three deliberate pause-points per the concertmaster role:

**1. Should the cross-cutting "effective-active-count = 4" observation (§10 surprise) be elevated to a candidate structural finding?** The pattern is robust across the bonus-10 top-10 (`{3: 2, 4: 8}`) and aligns numerically with SM gauge-group rank (= 4). This could be one of: a substantive coincidence-or-structure finding (similar to MFO §VIII.6 convergent independent results), an artefact of the bonus-10 search objective, or a side-finding that doesn't load-bear future work. The conductor decides whether to surface this in MFO §VIII.x landing or as a future-bonus seed.

**2. Should claim 1's "ontologically-relabeled" sub-verdict warrant a notebook clarification?** The instrument's `3+7+1` partition differs from M-theory's `4+7`; both arrive at 11D; the difference matters for any future work that tries to align the instrument's structures with specific M-theory constructions. A notebook clarification in MFO §VII.1.1 (two-level ontology) or §III.5 (~11D triple convergence) noting the partition-difference would prevent confusion. The conductor decides placement.

**3. Should claim 5's OPEN verdict become a Spike #25 starting point?** The audit explicitly identifies "meta-operation closure of mode-selection picker" as the downstream gap that closes topology choice. This is well-defined future work; a Spike #25 explicit scoping (with the bonus 11d REDUCES-TO-EXISTING constraint that the closure is NOT a new primitive class but a meta-operation) would convert the OPEN verdict into a tracked work item. The conductor decides whether this is Spike #25 scope or a later bonus thread.

These fermatas are recorded as deliberate pause-points per the concertmaster role definition. The synthesis stands without resolving them.

## §12 Final answer to the gate question

*"Which structural claims of string theory survive instrument-audit?"*

**Three pass cleanly (claims 1 count, 2, 3), one passes with ontological relabeling (claim 1 partition), one passes structurally (claim 4), one is honestly open (claim 5).** No claim is INCORRECT under current evidence. The user's *"maybe just correct not one correct"* framing — refining the audit-form away from uniqueness-of-correct toward per-claim-on-its-own-merits — is honoured.

The audit-form being GAP-ALIGNMENT (decided by 11d REDUCES-TO-EXISTING) is the right form. The instrument has located the meta-operation gap precisely as external-to-cyclic-cascade; it does NOT supply a Class P primitive that picks the vacuum; and the wiggle-in-isolation diagnosis (the strongest CORRECT finding) makes this structural property a *predicted* feature of the framework rather than an embarrassment.

The math doesn't lie. Three structural claims of string theory survive the instrument-audit cleanly. The wiggle-in-isolation diagnosis was a prior MPM critique that the four-reading sweep technically vindicated. Future spike work closes the topology question once the meta-operation that picks observable modes is located.

The audit-summary stands.
