# Spike #181 — Retroactive Re-Grading of Spike #47 R4-1 Under Researcher-DOF + Bonferroni Rigor

**Date**: 2026-05-19. **Branch**: `research/spike-181-spike-47-r4-1-researcher-dof-regrading`.
**Verdict**: **H0-VERDICT-NEEDS-RETRACTION** (recommended amendment: F-α PASS → F-α NOT-CONFIRMED; chain-level claim was already implicitly superseded by Spike #91 Run F Direction F, but R4-1's original PASS verdict text remains uncorrected in `spike_47_round4_results_2026-05-17.md`).

## §1 Original methodology summary

Per `spike_47_round4_results_2026-05-17.md` §1:

- **Substrate Λ catalog**: integer eigenvalues of S³ × S⁷ Hopf-bundle products, λ = j₃(j₃+1) + j₇(j₇+3) producing `{2, 4, 6, 10, 12, 16, 18, 20, 22, 24, 28, …}` (this audit replicates: 151 distinct values up to Λ=500, 80 values up to Λ=250).
- **Claimed chain**: `Λ = {2, 12, 28, 52, 84, 126, 178, 244}` — all 8 entries verified in substrate catalog.
- **F-α verdict**: PASS at "10% per-ratio … 8-peak match within ~1.6% (peaks 7-8 within 0.4% extrapolation)".
- **Statistical significance claim**: `p ≈ 0.027` ("a different null").
- **Process-integrity gap (F-180-1 shape)**: **NO COMMITTED SCRIPT** computes the `p ≈ 0.027`. The claim exists only in markdown `spike_47_round4_results_2026-05-17.md:20`. Same auditable-provenance gap that PR #585 hit per Spike #180.

## §2 Test-by-test results

### T1 — Methodology located, no source code

The `p ≈ 0.027` and "within ~1.6%" claims have no underlying committed Python. The substrate Λ catalog rule (j₃(j₃+1) + j₇(j₇+3) sums) IS documented in `spike_47_r3p1_asymptotic_dof_reframe_2026-05-17.md` §1.

### T2 — Per-peak error audit (math doesn't lie)

Mapping `ℓ_n = 220·√(Λ_n/2)` per F-α projection:

| n | Λ_n | predicted ℓ | observed ℓ (Planck PR3) | error |
|---|---|---|---|---|
| 1 | 2   | 220.00 | 220  | 0.000% |
| 2 | 12  | 538.89 | 540  | 0.206% |
| 3 | 28  | 823.16 | 810  | **1.625%** |
| 4 | 52  | 1121.78 | 1120 | 0.159% |
| 5 | 84  | 1425.76 | 1420 | 0.406% |
| 6 | 126 | 1746.20 | 1755 | 0.502% |
| 7 | 178 | 2075.48 | 2050 | 1.243% |
| 8 | 244 | 2429.98 | 2350 | **3.403%** |

**Max-per-peak error = 3.40%, NOT 1.6%**.
**Mean-per-peak error = 0.943%**.
**6/8 peaks within 1.6%** (peak 3 marginal at 1.625%, peak 8 at 3.40%).

The R4-1 claim "8-peak match within ~1.6% (peaks 7-8 within 0.4% extrapolation)" is **misleading** — peak 8 is at 3.40% error, peak 3 is just over 1.6%. The "extrapolation" qualifier may refer to deriving peak ℓ_n values from the chain rather than measuring them against Planck, but if so, peaks 7-8 are not Planck-anchored and the F-α claim only covers 6 peaks honestly.

### T2 — Multi-seed null replication

10 seeds × 10,000 trials × uniform-random Λ ∈ [0, 250], n=8 chain, max-per-peak-error null:

| metric | value |
|---|---|
| p_min | 0.0000 |
| p_max | 0.0000 |
| p_mean | 0.0000 |
| R4-1 claimed | 0.027 |

R4-1's claimed p=0.027 does not reproduce under the simplest uniform-random null. The chain's 3.4% max-err is too tight for uniform random 8-Λ chains in [0, 250] to achieve.

This suggests R4-1's claimed "different null" was *much* narrower in support (e.g., lam_max ~ 30 or peak-by-peak windowed) but is undocumented.

### T2b — Substrate-aware null (Λ_1 = 2 anchored)

Drawing 7 of 8 from substrate catalog at the anchor Λ_1=2:

| metric | value |
|---|---|
| n_trials | 10,000 |
| p_value_by_max_err | 0.0000 |
| p_value_by_mean_err | 0.0000 |

1M extended sampling: 0/1,000,000 random catalog-anchored 8-chains achieve max-err ≤ 3.4% or mean-err ≤ 0.943%. The chain is REAL signal — not a random catalog draw.

**But this is the wrong null** — the R4-1 chain was constructed by FITTING the substrate catalog Λs to Planck peaks (each Λ_n chosen to minimize ℓ_n error). Random catalog samples are not the comparison set; the comparison set is "all valid Planck-anchored chains."

### T3 — Researcher-degrees-of-freedom audit (the load-bearing finding)

Enumeration of strict-monotonic chains from substrate catalog satisfying per-peak tolerance:

| tolerance | n valid chains | R4-1 rank | R4-1 percentile | best mean-err |
|---|---|---|---|---|
| 1.6% (claimed) | 0     | n/a | n/a | n/a (no chain qualifies) |
| 2.5%           | 672   | n/a | n/a (R4-1 itself doesn't qualify) | 0.353% |
| 3.5% (actual)  | 3,240 | 576 | **17.78 percentile** | 0.353% |
| 5.0%           | 20,800 | 651 | 3.13 percentile | 0.353% |

**Critical finding**: At the chain's own achievable tolerance (3.5%), **3,240 distinct strict-monotonic chains exist from the substrate catalog matching Planck peaks within tolerance**. R4-1's chain ranks 576/3240 (17.78 percentile) — NOT exceptional within the constrained-search space.

The best-fit chain achieves 0.353% mean-error — 2.7× better than R4-1's 0.943%. The substrate catalog is dense enough that thousands of integer chains can be Planck-faithfully selected.

### T4 — Bonferroni correction

Per `spike_47_round4_results_2026-05-17.md` §1, R4-1 tested **5 candidate selection rules** (j₄ mod 4, Hopf-cycle phase 1/8, j₂+j₄ parity, pure-winding, selection-mask). Plus 5 falsifiers (F1-F5) tested in the same round.

| threshold | corrected α | p=0.027 survives? | replicated p=0 survives? |
|---|---|---|---|
| nominal (no correction) | 0.05  | YES | YES (trivially) |
| Bonferroni 5 rules      | 0.010 | **NO** | YES |
| Bonferroni 10 combined  | 0.005 | **NO** | YES |
| Bonferroni 25 combined  | 0.002 | **NO** | YES |

R4-1's reported `p ≈ 0.027` FAILS Bonferroni at any non-trivial multiplicity. The F-α PASS verdict assumed nominal α=0.05 without correction.

### T5 — Independent-dataset replication

Same `Λ = {2, 12, 28, 52, 84, 126, 178, 244}` chain applied to independent CMB datasets:

| dataset (citation, arXiv-verified) | n peaks | max-err | within 1.6%? |
|---|---|---|---|
| Planck PR3 (Aghanim+ 2020 arXiv:1807.06209) | 8 | 3.40% | NO |
| WMAP 9-yr (Hinshaw+ 2013 arXiv:1212.5226)    | 3 | 1.72% | NO |
| ACT DR4 (Aiola+ 2020 arXiv:2007.07288)        | 8 | 3.40% | NO |
| SPT-3G (Dutcher+ 2021 arXiv:2101.01684)       | 6 | 1.00% | **YES** |
| Planck PR4 (Akrami+ 2020 arXiv:2007.04997)    | 8 | 3.40% | NO |

**Only 1/5 independent datasets passes the 1.6% claim** (SPT-3G, but only because its peak count truncates to 6 — the same first-6-peaks subset that passes on all datasets).

When peak 8 is included, NO dataset passes 1.6%.

### T6 — Density-of-states diagnosis

| metric | value |
|---|---|
| Substrate catalog density in [0, 250] | 0.32 chains/Λ |
| Planck-implied chain density (8 peaks / 244 Λ-range) | 0.033 chains/Λ |
| **Density ratio (substrate / Planck-implied)** | **9.68×** |

The substrate catalog has ~10× the density needed to populate 8 Planck-matched values. **This is a density artifact** — any 10× over-dense integer catalog with constrained-search produces thousands of Planck-faithful chains.

Same diagnosis as Spike #180 found for the squashed-S⁷ vs round-S⁷ test on the same chain.

## §3 Re-graded F-α verdict

R4-1's original verdict text:
> **F-α PASS** (10% per-ratio): 8-peak match within ~1.6% (peaks 7-8 within 0.4% extrapolation)

**Recommended amendment**:
> **F-α NOT-CONFIRMED** (re-graded 2026-05-19 per Spike #181):
> - "Within ~1.6%" claim is true only for 6/8 peaks; peak 8 is at 3.40% error.
> - At the chain's actual achievable tolerance (3.5%), 3,240 alternative Planck-faithful chains exist from the substrate catalog. R4-1's chain ranks 576/3240 (17.78 percentile) — non-exceptional.
> - Reported `p ≈ 0.027` is unverifiable (no committed source) and fails Bonferroni correction at 5-rule multiplicity (corrected α=0.010).
> - Cross-dataset: chain does not pass 1.6% tolerance on 4/5 independent CMB datasets when 8 peaks tested.
> - Substrate-catalog density (~10× Planck-implied) is sufficient to populate any moderate-tolerance integer chain — density artifact, not structural correspondence.

**This re-grading is operationally consistent with Spike #91 Run F Direction F** (notebook §3.8.7), which already softened the chain-level claim and reframed the framework's CMB load-bearing prediction as **arithmetic peak-spacing pattern via Class I cyclic-cascade**, NOT the {2,12,28,…} chain on Class L sphere Laplacian.

Spike #91 RF DF therefore stands as the framework's current canonical CMB stance; Spike #181 closes the open loop by retracting R4-1's original PASS verdict text.

## §4 Downstream impact catalog

Found in srmech notebook + sister-notebook + memory directory:

| location | citation | status after re-grading |
|---|---|---|
| `srmech/srmech_research_notebook.md:731` (§3.8.7) | "Spike #47 R4-1 re-task verdict" (Spike #91 Run F Direction F) | **already softened**; cites R4-1 only as historical context |
| `srmech/notes/spike_47_round4_results_2026-05-17.md` | original F-α PASS text | **REQUIRES AMENDMENT** (text uncorrected; this finding) |
| `srmech/notes/spike_47_round3_results_2026-05-17.md` | F1 PARTIAL preserved | unaffected (still PARTIAL) |
| `srmech/notes/spike_47_r3p1_asymptotic_dof_reframe_2026-05-17.md` | asymptotic-DOF reframe candidate | unaffected (R4-1 itself was meant to test the reframe; reframe REFUTED at math level per R4-1; that part stands) |
| memory `user_stance_big_bang_as_projection_shadow.md` | candidate stance | does NOT cite the chain or "p=0.027"; no action needed |
| sister `mfo_spectral_research_notebook.md` (cited grep hit) | Spike #47 referenced | check for chain-level dependence (likely just R4-2 178-Gyr resolution) |
| memory `user_stance_dark_sector_ring_down_rate_is_cascade_stretched.md` | 178 Gyr / R4-2 | unaffected (R4-2 is independent of R4-1) |

**No canonical-committed (`memory/user_stance_*.md`) file cites R4-1's chain or the p=0.027 claim**, per grep on `R4-1|F-alpha|1\.6%|0\.027|chain.*\{2,?\s*12,?\s*28|selection.mask`. The downstream blast radius is limited to:

1. **`spike_47_round4_results_2026-05-17.md`** — text amendment recommended (this is the actionable downstream).
2. **`spike_51` series files** (5 cite R4-1, mostly for context).
3. **`spike_49`** (mentions R4-1 chain in cross-spike framing).

Spike #91 Run F Direction F is the upstream re-task that already shifted load-bearing weight away from the chain. R4-1 PASS amendment is housekeeping consistent with the existing notebook §3.8.7 reframe.

## §5 Recommendation for #47 R4-1 amendment

Mirror Spike #180's PR #585 amendment pattern:

1. **Strike "F-α PASS" verdict** in `spike_47_round4_results_2026-05-17.md:19`; replace with "F-α NOT-CONFIRMED (per Spike #181 2026-05-19 re-grading)".
2. **Strike `p ≈ 0.027`** claim in `:20`; replace with note: "No committed script supports this p-value; under uniform-random null over [0,250], p=0.0000 (chain max-err 3.40% never reached by random); under researcher-DOF audit, chain ranks 576/3240 (17.78 percentile) of valid Planck-anchored chains; chain-level F-α PASS retracted per Spike #181".
3. **Strike "8-peak match within ~1.6%"** claim; replace with "6/8 peaks within 1.6% (Λ=28 at 1.63% marginal; Λ=244 at 3.40% outside tolerance)".
4. **Update R4-1 score** from `5/10 [PASS, FAIL, PASS, PASS, PARTIAL]` to `4/10 [NOT-CONFIRMED, FAIL, PASS, PASS, PARTIAL]`. Spike #47 R2 total from 9/10 to **8.5/10** (F1 still PARTIAL as named-gap; F-α individual element changed within F1).
5. **Preserve** R4-1's PROCESS findings (g(Λ) ansatz REFUTED at math level; FFT-cosine 0.997 / L2 12.62 diagnostic; growing-with-n modulation inconsistent with Class K rate-of-approach). Those are real negative findings that stand.
6. **Reference** Spike #91 Run F Direction F (notebook §3.8.7) as the existing re-task verdict that ALREADY shifted load-bearing CMB prediction to Class I cyclic-cascade.
7. **Reference** Spike #181 (this finding) as the auditable closure on R4-1's original PASS verdict.

## §6 Verified literature citations (arXiv-only per `[[reference_autonomous_validation_tos_landscape]]`)

- **Aghanim N. et al. (Planck Collaboration)**, "Planck 2018 results. VI. Cosmological parameters", arXiv:1807.06209 (PDF-verified per Spike #76 + #180; PR3 TT acoustic-peak positions).
- **Hinshaw G. et al. (WMAP Collaboration)**, "Nine-Year Wilkinson Microwave Anisotropy Probe (WMAP) Observations: Cosmological Parameter Results", arXiv:1212.5226 (PDF-verified per Spike #180).
- **Aiola S. et al. (ACT Collaboration)**, "The Atacama Cosmology Telescope: DR4 Maps and Cosmological Parameters", arXiv:2007.07288 (PDF-verified per Spike #180).
- **Dutcher D. et al. (SPT-3G Collaboration)**, "Measurements of the E-mode polarization and temperature-E-mode correlation of the CMB from SPT-3G 2018 data", arXiv:2101.01684 (PDF-verified per Spike #180).
- **Akrami Y. et al. (Planck Collaboration)**, "Planck 2018 results. I. Overview, and the cosmological legacy of Planck", arXiv:2007.04997 (PDF-verified per Spike #180; PR4 reprocessing).

No new external citations beyond what Spike #180 already PDF-verified. No prohibited-source queries.

## §7 Discipline summary

- **14 A-N intact** per `[[feedback_no_privileged_primitive_classes]]` (no class promotion; substrate Λ catalog is S³ × S⁷ Hopf-base sum; primitive vocabulary unchanged).
- **Identity-not-implementation** per `[[user_stance_identity_not_implementation_discipline]]`: re-graded the chain-level VERDICT only; framework-level identity claim (Big Bang as projection-shadow; substrate as S¹×S³×S⁷ hyperring) untouched. Spike #91 Run F Direction F's Class I cyclic-cascade reframe is the framework's current CMB-pattern stance and is unaffected by this re-grading.
- **Math-doesn't-lie** per `[[user_stance_string_theory_instrument_first]]`: peak-8 error of 3.40% IS not "within ~1.6%"; the claim is falsified by per-peak audit. No fiat preservation.
- **Trauma-informed defensive scope** per `[[feedback_trauma_informed_defensive_scope]]`: cosmology research/educational; no targeting / capability-assessment content.
- **PDF-extraction citation discipline** per `[[feedback_pdf_extraction_citation_discipline]]`: all 5 arXiv references PDF-verified upstream (Spike #76 + #180).
- **No MVP framing** per `[[feedback_no_mvp_framing]]`: full-coverage re-grading across T1-T6; complete 8-peak audit; cross-dataset on all 5 attested CMB datasets.
- **NDJSON output** per `[[feedback_ndjson_over_bloated_json]]`: 16 records, one per line.

## §8 Status

**Verdict: H0-VERDICT-NEEDS-RETRACTION**. Recommended action: edit `spike_47_round4_results_2026-05-17.md` per §5 above. **Spike #91 Run F Direction F's reframe stands as framework's current CMB stance** — the re-grading is a housekeeping operation closing the loop on the R4-1 original PASS verdict text.

**Conductor decision needed**: should the amendment go in directly (notebook edit) or via a new PR? Recommend new PR for auditability + commit history (matches Spike #180's PR #585 amendment pattern).

**Files written** (absolute paths per worktree-isolated dispatch):
- `D:/GitHub/mlehaptics/.claude/worktrees/agent-spike181-spike-47-r4-1-regrading/docs/srmech/notes/spike181_spike_47_r4_1_regrading_prototype.py` (~615 lines, runnable analysis)
- `D:/GitHub/mlehaptics/.claude/worktrees/agent-spike181-spike-47-r4-1-regrading/docs/srmech/notes/spike181_records_2026-05-19.ndjson` (16 records)
- `D:/GitHub/mlehaptics/.claude/worktrees/agent-spike181-spike-47-r4-1-regrading/docs/srmech/notes/spike181_spike_47_r4_1_regrading_findings_2026-05-19.md` (this file)

---

*End of Spike #181. Math doesn't lie. The chain's max-per-peak error is 3.40% at Λ=244, NOT ~1.6%; researcher-DOF audit places R4-1 at 17.8 percentile of 3,240 valid chains; original p=0.027 has no auditable provenance; F-α PASS verdict needs retraction. Spike #91 Run F Direction F's Class I cyclic-cascade reframe stands as the framework's current CMB-pattern claim.*
