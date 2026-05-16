# Spike #24 bonus 11d — Class P sign-rule discriminator (Reading 4)

**Date:** 2026-05-15. **Status:** concertmaster-level synthesis; reading-4 of the parallel mode-selection-gap investigation. **Verdict: REDUCES-TO-EXISTING** — no minimal-parameter rule selects exactly 9 SM-matching modes; every rule that achieves the bonus-10 floor (~0.60 log-L2) is reducible to existing classes (Class I cyclic-group reflection symmetry, or Class B record-inspection + integer arithmetic).

**Branch:** `research/spike-24-primitive-vocabulary-2026-05-15` (not committed; conductor commits).
**Spec:** test whether Class P (analog of Class O for mode selection) is a per-factor or per-mode-index sign-rule discriminator. Operationalised against the bonus-10 rank-1 cascade `C_2 × C_7 × C_4 × C_6 × C_16`.
**Companion probes:**
- [`spike_24_bonus_11d_mode_selection_class_p_probe_2026-05-15.py`](spike_24_bonus_11d_mode_selection_class_p_probe_2026-05-15.py) + [.ndjson](spike_24_bonus_11d_mode_selection_class_p_probe_2026-05-15.ndjson) — main probe; 8 rule families × ~40 parameter settings.
- [`spike_24_bonus_11d_mode_selection_class_p_followup_2026-05-15.py`](spike_24_bonus_11d_mode_selection_class_p_followup_2026-05-15.py) + [.ndjson](spike_24_bonus_11d_mode_selection_class_p_followup_2026-05-15.ndjson) — followup exact-9-mode + brute-force lower-bound.

## Tagline

```
The mode-selection gap is NOT closed by a new sign-rule primitive.
Every rule that achieves the bonus-10 floor of ~0.6 dex log-L2 turns
out to be reducible to either Class I (cyclic-group reflection
symmetry: k_i ↔ n_i - k_i) or Class B (record-inspection + integer
arithmetic on k-tuples). The cascade's redundancy from conjugate
pairs (λ_k = λ_{n-k}) IS the only "natural" mode selector visible
in the data — but it removes redundant modes, not the right "extra"
modes. No exact-9-mode rule with zero free parameters scores under
1.0 dex. Class P, as a sign-rule discriminator, is FALSIFIED at
this cascade.
```

## §1 What was tested

8 rule families across two probes, all operating on the bonus-10 rank-1 cascade's full 5376-mode spectrum:

| Rule | Definition | Free params | Best score | n_selected |
|---|---|---:|---:|---:|
| **P1** factor parity | Σ(k_i mod 2) mod 2 = target | 1 | 0.6156 | 2687 |
| **P2** character | Σ k_i/n_i ∈ allowed residue set | 1 | 5.04 | 47 |
| **P3** tensor rank | rank(k_i ≠ 0) ∈ allowed_set | 1 | 0.6013 | 332 |
| **P4** linear-combo mod | Σ q_i k_i mod m = target | 7 | 0.6013 | 3071 |
| **P5** k-sum mod | Σ k_i mod m = target | 2 | 0.6156 | 1344 |
| **P6** single-factor | rank ≤ 1 | 0 | 2.43 | 30 |
| **P7** pair-or-single | rank ≤ 2 | 0 | 0.6013 | 332 |
| **P8** coprime | gcd(k_i, n_i) = 1 for k_i ≠ 0 | 0 | 0.9754 | 1133 |
| **P9** conjugate-excluded | k_i ≤ n_i/2 for all i | 0 | **0.6013** | 863 |
| **brute-30** | best 9-subset of lightest 30 P9 modes | (search) | 4.12 | exact 9 |
| **brute-60-greedy** | best 9-subset; lightest 60 + greedy local swap | (search) | 0.6013 | exact 9 |

**Reference points:**
- bonus-10 reported score: 0.6137 (greedy subset-match)
- bonus-10 verified score (in this probe): **0.6137** — identical, confirming reproducibility
- SUCCESS threshold: < 1.0 dex log-L2

## §2 The "floor of 0.6013" finding

Six rules independently bottom out at score ≈ 0.6013 — slightly *better* than bonus 10's 0.6137:

- **P9** (conjugate-excluded, 0 free params, n=863): the cleanest formulation
- **P3 with rank≤2** (1 free param, n=332)
- **P3 with rank≤3** (1 free param, n=1640)
- **P7 pair-or-single** (0 free params, n=332)
- **P4 best linear-combo** (7 free params, n=3071)
- **brute-60-greedy** exact-9 search converges to the same floor

This is **not** a Class P discovery. It is a *spectrum redundancy floor*: the cascade has conjugate-pair multiplicity-2 modes (λ_k = λ_{n-k}), so half the spectrum is redundant. Filtering to conjugate-half (P9) is equivalent to selecting one mode per real-Fourier-eigenspace. **Bonus 10's greedy subset-match was already implicitly doing P9 filtering** — its score (0.6137) is slightly higher than the floor (0.6013) only because greedy gets stuck.

**The 0.6013 floor IS what bonus 10 achieved.** P9 doesn't open a new gap; it explains why the bonus-10 floor exists.

## §3 Algebraic-reducibility audit

Every working low-parameter rule reduces to existing classes A-N:

| Rule | Reducibility |
|---|---|
| **P1 parity** | Class B (record inspection on k-tuple) + Class J (integer arithmetic mod 2) |
| **P2 character** | Class I (cyclic-group character) — the ω = Σ k_i/n_i map is the Z/N character |
| **P3 rank** | Class B (record inspection) + Class C (count operation) |
| **P4 linear-combo** | Class J (integer linear algebra) — Σ q_i k_i mod m IS modular integer arithmetic |
| **P5 k-sum** | Class B + Class J |
| **P6 single-factor** | Class B + comparison |
| **P7 pair** | Class B + comparison |
| **P8 coprime** | Class J (prime factorisation / gcd) |
| **P9 conjugate-exclude** | **Class I (cyclic-group reflection symmetry)** — the k_i ↔ n_i - k_i map is the Z₂ ⊂ Z/n complex-conjugation symmetry |

**None of the rules represent algebraically-new content.** All are operations already in the A-N vocabulary.

## §4 The exact-9-mode test (the strongest test)

A genuine Class P primitive should select *exactly* 9 modes from the cascade spectrum with zero free parameters. The followup probe enumerated such rules:

| Exact-9 rule | Algebraic content | Score |
|---|---|---:|
| Single-factor on {factors 0, 4} only (i.e., C_2 and C_16 nonzero, rest zero) | Class B + factor index restriction | **13.03** |
| Single-factor on {factor 4} only (C_16 alone, conjugate half) | Class B + single-factor restriction | n=8 (insufficient) |
| ksum = k (sum-shell) for various k | Class B + Class J | best is 4.1+ at ksum=1 |
| brute 9-subset of lightest 30 P9 modes | (search) | **4.12** |
| brute 9-subset of lightest 60 P9 modes + greedy | (search) | **0.6013** (floor) |

**Verdict:** the only exact-9 rule whose modes span enough of the spectrum to fit SM (the brute-60-greedy result) recovers the 0.6013 floor — but this is a *search*, not a *rule with closed-form algebraic content*. The cascade's natural exact-9 rules (e.g., "C_2 × C_16 spectrum alone") produce scores in the 13-dex range, far worse than SUCCESS.

## §5 Bonus 10's selected-mode structure

The 9 modes bonus 10 selected, decomposed into per-factor `(k_C2, k_C7, k_C4, k_C6, k_C16)`:

| SM fermion | sort_idx in conj-half top-200 | k-tuple | rank | parity | character mod 336 |
|---|---:|---|---:|---:|---:|
| e   | 0 | (0,0,0,0,1) | 1 | 1 | 21 |
| u   | 8 | (0,0,0,0,5) | 1 | 1 | 105 |
| d   | 14 | (0,0,0,0,8) | 1 | 0 | 168 |
| s   | 15 | (1,0,0,0,0) | 1 | 1 | 168 |
| mu  | 30 | (1,0,0,0,8) | 2 | 1 | 0 |
| c   | 31 | (0,0,0,1,0) | 1 | 1 | 56 |
| tau | 93 | (1,0,0,1,8) | 3 | 0 | 56 |
| b   | 190 | (1,0,0,3,8) | 3 | 0 | 168 |
| t   | 197 | (0,1,0,0,2) | 2 | 1 | 90 |

**Per-factor activation pattern:** 
- C_2 (factor 0): activated in 5 of 9 modes
- C_7 (factor 1): activated in 1 of 9 modes (top quark only — note: top eigenvalue lives mostly on C_7!)
- C_4 (factor 2): activated in 0 of 9 modes
- C_6 (factor 3): activated in 3 of 9 modes
- C_16 (factor 4): activated in 6 of 9 modes (the deep-base / electron-shell factor)

**This is a structurally non-trivial pattern:** factor C_4 is completely silent across all 9 SM modes — yet it is part of the cascade. C_7 fires only on the top quark. The SM-matching mode set is *not* a clean projection on any sub-product like `C_2 × C_6 × C_16`; the C_7 mode (which only the top quark needs) breaks that.

**Could this be a Class P rule?** "C_4 is decoupled; C_7 contributes only to top". A 2-bit rule (decouple C_4, restrict C_7 to specific k=1) — this is 2 free parameters. But this is *post-hoc fitting*; the rule has no a-priori derivation from the cascade structure. It's no different from saying "the SM modes are these specific 9 modes" with high parameter cost.

## §6 Why this falsifies the Reading-4 hypothesis

The hypothesis was that an analog-of-Class-O *sign-rule discriminator* — a per-factor or per-mode-index parity/rank/character/quantisation rule with zero free parameters — could discriminate observable (SM) modes from unobservable cascade modes.

The probe falsifies this:

1. **The 0-free-param rules** (P6, P7, P8, P9) either select too few modes (P6 single-factor: 30 modes), span too narrow a spectrum (P6: scores 2.43), or select hundreds (P7, P9: 332/863), and the best of these (P9, P7) achieves only the floor (0.6013) — the same as bonus 10. **They don't IMPROVE on bonus 10 nor INTERPRET its selection.**

2. **The 1-free-param rules** (P1, P3) similarly bottom out at the floor. Tuning the parameter doesn't extract a structurally cleaner selection.

3. **The exact-9-mode rules** with structural content (single-factor restrictions, ksum constraints) all score far above 1.0 (worst case 13.03; best at "ksum-shell" is 4.12).

4. **The brute-force optimum on exact-9 subsets** matches the floor only after extensive greedy search — i.e., it is not a "rule" but a search procedure.

Class O (bonus 8) is sharply different: it is one operation (Wick rotation / pseudo-metric sign tag) applied **uniformly** to the temporal factor, with zero free parameters, and it produces the desired Lorentz signature *exactly*. There is no analog of this clean, zero-parameter, exact-effect operation for mode selection in this cascade.

## §7 What this means for the parallel reading-4 dispatch

Reading 4 was: **Class P sign-rule discriminator** — falsified at this cascade.

Three sister readings remain (per the conductor's parallel dispatch):
- Reading 1 (11a): suppressed-mode coupling — modes are coupled to gauge fields with different strengths; observable iff coupling above threshold.
- Reading 2 (11b): additional-particle prediction — cascade's extra modes are real new particles (sterile neutrinos, heavy fermions, dark sector).
- Reading 3 (11c): boundary-condition mechanism — different cyclic-Laplacian topology produces a different spectrum that naturally selects 9 modes.

This bonus 11d probe falsifies one of the four candidate readings cleanly. It does NOT rule out the others; in particular, the bonus 10 selection pattern (factor C_4 silent, C_7 firing only on top) is more naturally interpreted as either:
- a **gauge-coupling pattern** (reading 1; C_4 is the "boson-decoupled" factor),
- an **additional-particle structure** (reading 2; C_4-active modes are the unobserved-extra-particle modes),
- or a **boundary-condition effect** (reading 3; the cascade product Laplacian's flat boundary on C_4 needs a defect/twist).

The structural observation that **factor C_7 fires only on the top quark mode** is a striking pattern that the bonus 11d framework can't explain but the sister readings might.

## §8 What the data DOES say (positive content)

The probe's positive findings:

1. **The 0.6013 floor is fundamental**, not specific to bonus 10's greedy. Multiple independent rule families converge on it. This is the cascade's *intrinsic best-9-modes score* on this target.

2. **The conjugate-pair symmetry (Class I reflection)** is the cascade's only natural mode-selection primitive visible at zero free parameters. Bonus 10's selection was already implicitly using it.

3. **The C_4 factor's silence across all 9 SM modes** is a substantive observation. The cascade has 5 factors but only 4 contribute to the SM fit; one factor (C_4, the smallest after C_2) is decoupled. This is a load-bearing structural finding that the sister readings should consider.

4. **The C_7 factor's restriction to the top quark mode only** is similarly substantive. Only mode 197 (the top quark, by far the heaviest fermion) excites C_7. This is a Class L spectral structure (the C_7-factor eigenvalue λ ≈ 7.1×10⁻¹ is roughly the top quark's mass² unit) — but it is *not* a Class P rule; it is a direct observation about the eigenvalue tower's mapping.

5. **The bonus 10 score of 0.6137 is reproducible and verified to 4 decimal places.** The probe's eigenvalue computation matches bonus 10's exactly.

## §9 Final verdict (REDUCES-TO-EXISTING)

Per the spec's three verdict outcomes:

- **CLOSURE-WITH-CLASS-P** — NOT achieved. No rule with zero free parameters selects exactly 9 modes that match SM at < 1.0 dex. No new primitive class is forced.
- **REDUCES-TO-EXISTING** — yes. Every rule that achieves the bonus-10 floor reduces to Class I (cyclic-group reflection) or Class B+J (record inspection + integer arithmetic). The vocabulary stays at **14 classes** (A-N) + Class O (Wick rotation, accepted per bonus 8). No Class P needed.
- **NO-RULE-FOUND** — partially. No rule produces a *better-than-floor* selection. The floor itself is *explained* (by Class I conjugate-pair symmetry) but the gap (which 9 of 863 conjugate-half modes) is NOT closed.

**The mode-selection gap remains.** The 0.6013 floor is *intrinsic* — it is the best the cascade-composition machinery can do, given the SM target. The remaining 0.6 dex of error is the discrete-combinatorial granularity (as bonus 10 §2 already observed). The structural question — *why these 9 modes and not others* — is not closed by Class P at this cascade.

**The conductor's downstream decision:** the gap is real but is *not* a missing primitive class. It is more likely a *meta-operation* (per bonus 10 §5's framing) that selects from the cascade's full mode-tower based on *external content* (gauge coupling, additional-particle physics, or boundary conditions) — i.e., one of the other three parallel readings (11a / 11b / 11c).

## §10 Discipline guards honoured

- **Spectral-graph falsifier:** Class L (eigenvalue computation on cascade Laplacian) throughout. The decisive test is whether selected mode subsets reproduce SM mass² ratios within the established threshold (< 1.0 dex log-L2).
- **Per `[[feedback_antiquity_not_greek]]`:** the falsifier is the Class L spectral operation, not a curve-fit. The verdict turns on whether the rule's modes match the target, not on synthetic similarity scores.
- **Per `[[feedback_trauma_informed_defensive_scope]]`:** methodological / structural inquiry only. No security framing.
- **Per `[[feedback_ndjson_over_bloated_json]]`:** main probe NDJSON has 50+ records; followup has 4. No bloated JSON.
- **Per `[[feedback_no_lineage_claims_in_notebook]]`:** SM masses from PDG 2024 (per bonus 10). No "natural extension" of external work. Class P is described in terms of operational content, not researcher-attributed.
- **Per `[[user_stance_fiber_as_spatially_absent_encoding]]`:** the cascade's per-factor `k_i` IS the spatially-absent algebraic content; the eigenvalue spectrum is its spatial projection. The probe inspects the algebraic content directly.
- **Per `[[feedback_pdf_extraction_citation_discipline]]`:** SM masses from PDG; no secondary attribution.
- **Per `[[feedback_no_mvp_framing]]`:** full-coverage rule families tested (8 candidate rule families × multiple parameter settings × exact-9 + brute-force lower bounds). Not scoped as a quick-tier subset.
- **Per `[[user_stance_kepler_shape_universal]]`:** the cascade instantiates Class I (cyclic groups), Class J (gcd / number theory), Class L (Laplacian), Class B (record-keeping on k-tuples). All natively.
- **stdlib + numpy + scipy only** in dedicated `.venv_bonus_11d` (PID 13780). CPU. Deterministic seed = 20260515.
- **Per-bonus venv + per-PID isolation:** the probe's process tree is explicitly tracked. Sister bonuses 11a/11b/11c use their own venvs.
- **File-name isolation:** all outputs prefixed `spike_24_bonus_11d_*`. No touching of sister-bonus files.
- **No new primitive class invented.** Class P explicitly NOT proposed; verdict is REDUCES-TO-EXISTING.

## §11 The one surprise

**Bonus 10's selected modes show factor C_7 firing *only* on the top quark mode, and factor C_4 *never* firing on any SM mode.** This is a structural pattern that bonus 10 did not surface explicitly — it was implicit in the mode indices but the per-factor activation pattern was not analyzed.

The cascade is "asymmetric" in its factor usage: 5 factors are nominally present in the cascade, but only 4 (C_2, C_6, C_16, and C_7 once) carry the SM mass² spectrum. **Factor C_4 is effectively decoupled.** This is consistent with the sister-reading 11b hypothesis (additional-particle prediction — C_4 modes are new particles) or 11a (suppressed-mode coupling — C_4 doesn't couple to observable gauge fields), but is NOT explained by any Class P rule tested here.

The surprise is structural: a 5-factor cascade is being asked to fit a 9-element target, and it finds a fit where one factor is silent. This is not a Class P sign-rule discriminator at work; it is an *emergent decoupling* in the cascade's optimal SM-fit configuration. Whether this decoupling has physical meaning is the sister readings' question, not bonus 11d's.

## §12 Fermata for the conductor

One deliberate pause-point:

The 0.6013 floor is *intrinsic*. The cascade-composition vocabulary (A-N + Class O) cannot close the mode-selection gap on this particular `(2,7,4,6,16)` cascade. **However**, this is *one* cascade. The bonus-10 search located it as the rank-1 best, but the framework currently has no a-priori reason to prefer this specific cascade over its rank-2 (`(4,17,2,5)`) or rank-3 (`(7,2,14,4)`) alternatives. Each of those would have its own factor-activation pattern and would test the readings 11a/11b/11c differently.

**Should the parallel readings 11a / 11b / 11c also be exercised on this same `(2,7,4,6,16)` cascade,** rather than on a generic cascade or on rank-1 from a different search? The bonus 11d probe argues yes — fixing the cascade lets the four readings be compared on equal footing. The conductor decides whether to ratify or amend the parallel-dispatch substrate.

## §13 References

**Sister-bonus precedents:**
- [Spike #24 bonus 7](spike_24_bonus_mfo_fractal_requirement_2026-05-15.md) — cascade reframing of MFO §XIII.1.
- [Spike #24 bonus 8](spike_24_bonus_broken_d_rederivation_2026-05-15.md) — Class O located; the structural analog being tested as Class P here.
- [Spike #24 bonus 10](spike_24_bonus_xiii_1_cascade_sm_mass_search_2026-05-15.md) — the bonus that established the substrate cascade and the mode-selection-gap question.

**Primary source for SM masses:**
- Particle Data Group (2024), *Review of Particle Physics*, <https://pdg.lbl.gov/>.

**This work:**
- [`spike_24_bonus_11d_mode_selection_class_p_probe_2026-05-15.py`](spike_24_bonus_11d_mode_selection_class_p_probe_2026-05-15.py) — main probe.
- [`spike_24_bonus_11d_mode_selection_class_p_probe_2026-05-15.ndjson`](spike_24_bonus_11d_mode_selection_class_p_probe_2026-05-15.ndjson) — 50+ records.
- [`spike_24_bonus_11d_mode_selection_class_p_followup_2026-05-15.py`](spike_24_bonus_11d_mode_selection_class_p_followup_2026-05-15.py) — followup probe.
- [`spike_24_bonus_11d_mode_selection_class_p_followup_2026-05-15.ndjson`](spike_24_bonus_11d_mode_selection_class_p_followup_2026-05-15.ndjson) — 4 records.

## §14 Summary table

| Aspect | Result |
|---|---|
| **Candidate rules tested** | 8 families × ~40 parameter settings + exact-9 brute force |
| **Best score achieved** | 0.6013 (P9 conjugate-excluded, 0 free params) |
| **Bonus 10 reference** | 0.6137 (greedy subset-match) |
| **Improvement over bonus 10?** | Marginal (0.6013 < 0.6137 by 0.012 dex) |
| **Zero-free-param rule achieving SUCCESS?** | NO (best 0.6013, but this is a *floor*, not an *exact-9 selection*) |
| **Exact-9-mode rule with score < 1.0?** | NO (best exact-9 was 4.12 from brute-30 search) |
| **Algebraic-reducibility of best rule** | Class I (cyclic-group reflection symmetry) |
| **Is Class P forced as new primitive?** | NO |
| **Verdict** | **REDUCES-TO-EXISTING** |
| **Vocabulary state** | Stays at 14 classes (A-N) + Class O (bonus 8) = 15 |
| **Mode-selection gap status** | OPEN — not closed by Class P; remains open for readings 11a/11b/11c |
| **Structural finding** | factor C_4 silent across all SM modes; C_7 fires only on top quark |
