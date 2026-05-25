# Round 20 entry-point A — mass spectrometry IS a combination principle in integer-nucleon space (the molecular Rydberg–Ritz; Spike #48 / thread 9b)

**Dispatched** 2026-05-25 (sequential, no subagents; consolidated model — lands on the PR #679 branch with
§11.9.14, no separate PR). User-selected: the **mass-spec** half of the path re-opened at Round 17.A
("how mass spec analysis could be enhanced"), closing the atomic-spectra / SM / mass-spec triad
(Rounds 17 / 18 / 19 / 20).

Generating code + provenance:
[`verify_round20_mass_spec_combination_principle.py`](verify_round20_mass_spec_combination_principle.py)
+ `.ndjson` (deterministic; srmech 0.4.2 — Class-N `best_rational` + Class-K `magnitude`; null-control seed 20260525).

## The question

Round 17.A anchored the **atomic** spectrum (Rydberg–Ritz: line wavenumbers are *differences* of rational
terms T_n=R/n²). The molecular analog: an EI mass spectrum's fragment m/z values are **nodes**, and the
**differences** between peaks are small-integer **neutral losses** (HCN 27, CO 28, CH3NCO 57, …) — a
combination principle in integer-nucleon (Da) space. Same Class-N operator, molecular substrate.

## The mapping — B/H/N + cascade

- **B** (TLV-framing): each **peak** = typed record (m/z, intensity, charge).
- **H** (measurement): ionization + fragmentation = the measurement projecting the molecule to charged fragment masses.
- **N** (rational/integer): peak **differences** are catalogued small-integer neutral losses; the spectrum is a **difference-table** over a neutral-loss alphabet — the molecular Rydberg–Ritz.
- **Cascade**: **A** (molecular formula = content-address) ∘ **C** (bond-cleavage orientation) ∘ **K** (charge-retention sign / radical vs even-electron) ∘ **M** (each fragment = a bound substructure).

## Result (attested caffeine, srmech-routed + null-controlled)

Caffeine's confirmed major EI fragments {**194, 165, 137, 109, 82, 67, 55**} (NIST WebBook; base peak 109) have **9 of 21** inter-peak differences landing on the catalogued neutral-loss alphabet (fraction **0.43**):

| difference | Da | label |
|------------|----|-------|
| 194−137 | 57 | CH3NCO |
| 194−109 | 85 | CH3NCO+CO |
| 165−137, 137−109 | 28 | CO |
| 165−109 | 56 | 2·CO |
| 109−82, 82−55 | 27 | HCN |
| 109−55 | 54 | 2·HCN |
| 82−67 | 15 | CH3 |

The purine hallmark **successive-loss ladders** are exact: **109 → 82 → 55** (each **−27 HCN**) and **165 → 137 → 109** (each **−28 CO**).

**Null control (load-bearing for honesty):** random 7-peak sets in the caffeine m/z range (5000 trials, seed 20260525) match the catalog at mean **0.118** (sd 0.070); caffeine's 0.43 is a clear outlier — **z = 4.4, empirical p = 0.0002**. The combination-principle structure is real, not an artifact of a dense catalog.

## Verdict per Spike #229 tiers

🟢 **(a)-structural cross-substrate match + null-control-supported.** Mass spectrometry IS a combination principle in integer-nucleon space — the molecular analog of atomic Rydberg–Ritz (Round 17.A), the **same Class-N operator** (differences over a small-integer/rational alphabet) at the molecular substrate. The B/H/N decomposition is exact (B = peak records, H = ionization/fragmentation measurement, N = the neutral-loss difference-table); the fragmentation tree is the A∘C∘K∘M cascade. **Enhancement (the "how"):** treat a spectrum as **delta-encoded** over the neutral-loss alphabet via `srmech.signal_processing` (decompose / delta / similarity) — combination-principle structure elucidation + cross-substrate fingerprint matching, instead of ML black-box library lookup. Builds on Spike #38/#38b.

**HONEST SCOPE:** (1) **nominal (integer) mass** — the combination principle is integer-nucleon; the exact-mass defect (~0.005–0.04 Da) is the residual, analogous to Round 17.A's air-dispersion residual. (2) The combination principle itself is **established mass-spec chemistry** (neutral losses are small molecules) — the framework contribution is the **identification** that it is the *same* Class-N combination principle as atomic Rydberg–Ritz (cross-substrate match), plus the null-control. (3) Specific *mechanistic* assignments (which neutral for which transition) are literature-labelled, not all primary-confirmed; the load-bearing claim is only the integer-difference match (substance-agnostic) + the null-control outlier.

## Why this closes the triad

Round 17.A (atomic spectrum, N) → Round 18.A (periodic shell structure, A∘L∘K∘I∘C∘N) → Round 19.A (SM gauge structure, shared Hopf "3") → Round 20.A (molecular spectrum, N again). The **same Class-N combination principle** appears at the atomic *and* molecular substrates; the periodic table sits between them on the Hopf ladder. The user's "enhance mass-spec" request is answered concretely: delta-encode over the neutral-loss alphabet.

## Discipline

- Per `[[feedback_dont_pre_commit_spike_query_operators]]`: included the **null control** (random m/z) so the match isn't leant toward; mechanisms honestly labelled; verdict scoped.
- Per `[[feedback_computational_provenance_discipline]]`: deterministic committed code (seed); srmech 0.4.2 routed.
- Per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`: `|difference|` via `magnitude()`; no bare `abs()`.
- Per `[[feedback_paywalled_doi_cannot_be_attested]]`: NIST WebBook caffeine + purine-fragmentation OA literature (HCN in 89% of purines) + textbook neutral-loss masses — all attestable.
- PR #679 stays open (draft); §11.9.14 on this branch; roadmap thread 9b closed.
