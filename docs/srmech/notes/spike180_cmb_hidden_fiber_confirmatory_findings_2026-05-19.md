# Spike #180 — CMB Hidden-Fiber Confirmatory Test (PR #585) — **H0-NOT-REPRODUCED**

**Date:** 2026-05-19. **Verdict tag:** **H0-NOT-REPRODUCED** with chain-construction-bias diagnosis.

**Bottom line:** PR #585's p=0.041 finding does not survive (a) multi-seed Monte-Carlo replication, (b) researcher-degrees-of-freedom analysis, OR (c) testing on the continuous-form chain derived faithfully from Planck CMB acoustic peaks. The reported finding rests on a chain selection that occupies the **top 3.1%** of 23,760 possible integer chains still within 1.6% of Planck peak positions. Recommended action: **mark PR #585 as "preliminary positive; not reproduced on independent data" and close the canonical-promotion path on this specific finding.**

## §1 Methodology audit — what the chain actually is

The "empirical selection-mask chain" `{2, 12, 28, 52, 84, 126, 178, 244}` referenced by PR #585 is NOT raw observational CMB data. It was **constructed** in Spike #47 R4-1 (commit `c73565b`, 2026-05-17) by selecting integer substrate-Λ values whose `√Λ` ratios reproduce Planck 2018 PR3 acoustic-peak multipoles ℓ ≈ {220, 540, 810, 1120, 1420, 1755, 2050, 2350} within ~1.6%.

Per Spike #47 Round 4 documentation: "F-α PASS (10% per-ratio): 8-peak match within ~1.6%". The chain values are therefore a **proxy** for Planck acoustic peaks through the substrate `√Λ → k_observer` projection. PR #585's squashed-S⁷ fit test against this chain is an **indirect test against Planck**, not against a fresh independent dataset.

For an actual independent confirmatory test of "does squashed-S⁷ correlate with CMB acoustic-peak structure?", we need to:
1. Replicate the methodology on the **continuous** chain derived directly from Planck acoustic peaks (no rounding manipulation), AND
2. Run the test against **other CMB experiments** (WMAP, ACT, SPT, Planck PR4) using the same construction.

## §2 Multi-seed Monte-Carlo replication of PR #585's original test

PR #585 reports p=0.041 from a null test: 50 random uniform eigs in [0, 250], 10,000 trials, comparison to squashed-S⁷'s median |Δ| = 0.7778. Reproducing this exact test with 10 different random seeds (no seed documented in PR):

| Seed | p-value |
|---:|---:|
| 12345 | 0.0566 |
| 54321 | 0.0542 |
| 77777 | 0.0557 |
| 11111 | 0.0518 |
| 99999 | 0.0555 |
| 0 | 0.0539 |
| 1 | 0.0573 |
| 2 | 0.0546 |
| 3 | 0.0584 |
| 4 | 0.0540 |

**Range: 0.0518–0.0584; mean 0.0552.** All 10 replications give p > 0.05. PR #585's claimed p=0.041 is below ALL 10 reproduced values, suggesting it was drawn from an outlier seed (not documented). Under conventional 0.05 threshold, the finding **does not reach significance** under proper Monte-Carlo replication.

## §3 Researcher-degrees-of-freedom analysis (chain selection bias)

Given Planck peaks {220, 540, 810, 1120, 1420, 1755, 2050, 2350} and the 1.6%-tolerance criterion from Spike #47 Round 4, how many distinct integer chains could have been chosen?

Per-peak acceptable Λ ranges:
| Peak ℓ | Continuous Λ | Integer candidates within 1.6% |
|---:|---:|---|
| 220 | 2.00 | {2} |
| 540 | 12.05 | {12} |
| 810 | 27.11 | {27} only |
| 1120 | 51.83 | {51, 52, 53} |
| 1420 | 83.32 | {81–86} |
| 1755 | 127.27 | {124–131} |
| 2050 | 173.66 | {169–179} |
| 2350 | 228.20 | {221–235} |

**Total combinatorial space: 23,760 acceptable chains.**

Distribution of `median |Δ|` (squashed-S⁷ fit) across all 23,760 chains:
- Min: 0.278
- 25%ile: 1.278
- Median: 1.611
- 75%ile: 1.889
- Max: 2.778

**PR #585's chain `{2, 12, 28, 52, 84, 126, 178, 244}` has median |Δ| = 0.778, ranking 745 of 23,760 = top 3.1 percentile.**

Critical anomaly: **PR #585's third chain entry is Λ=28, but the per-peak 1.6% tolerance for peak 810 yields ONLY Λ=27** (Λ=28 produces predicted peak 823.2, error 1.63% — just outside tolerance). PR #585's chain includes an entry that violates the stated 1.6% criterion in the direction that improves the squashed-S⁷ fit.

## §4 Best-Planck-fit integer chain — what does p look like?

The chain that most faithfully fits Planck peaks (each entry the nearest integer to its continuous-chain value, within tolerance):

`Best-Planck chain = {2, 12, 27, 52, 83, 127, 174, 228}`

Per-peak fit errors: all within 0.04%–0.21% of Planck peaks (10× tighter than PR #585's chain).

Test results against this best-Planck chain:
- Squashed-S⁷ median |Δ| = **1.111** (vs PR #585's 0.778)
- p-value (vs 52-eig random uniform null): **0.171**

So under the chain that most faithfully represents Planck acoustic peaks, the squashed-S⁷ correlation has **p = 0.17 — clearly null**.

## §5 Independent-dataset confirmatory tests

Tested the squashed-S⁷ correlation against acoustic-peak positions from 4 independent CMB experiments (continuous-chain form, no integer rounding):

| Dataset | n_peaks | sq_med | round_med | ratio | p_sq_uniform | p_sq_density-matched | Citation |
|---|---:|---:|---:|---:|---:|---:|---|
| D0 PR #585 (integer) | 8 | 0.78 | 3.50 | 4.50× | 0.0594 | 0.0645 | (synthetic) |
| D1 Planck PR3 (continuous) | 8 | 1.03 | 5.87 | 5.68× | 0.1911 | 0.1606 | Aghanim+ 2020 arXiv:1807.06209 |
| D2 WMAP 9-year | 3 | 2.00 | 2.00 | 1.00× | 1.0000 | 0.6295 | Hinshaw+ 2013 arXiv:1212.5226 |
| D3 ACT DR4 | 8 | 0.93 | 5.81 | 6.28× | 0.1393 | 0.1160 | Aiola+ 2020 arXiv:2007.07288 |
| D4 SPT-3G | 6 | 1.56 | 3.09 | 1.98× | 0.8723 | 0.4106 | Dutcher+ 2021 arXiv:2101.01684 |
| D5 Planck PR4 (NPIPE) | 8 | 1.03 | 5.87 | 5.68× | 0.1911 | 0.1606 | Akrami+ 2020 arXiv:2007.04997 |

**No independent dataset shows p < 0.05** under the continuous-chain null. The strongest signal (D3 ACT DR4, p=0.14) is well above the conventional threshold and far above any Bonferroni-corrected threshold.

The ratio `round_med / sq_med` does indicate squashed-S⁷ fits ~5–6× tighter than round-S⁷ in 3 of 5 datasets. This is a real **structural** observation, not a statistical fluke — but it does NOT survive proper null testing because the squashed-S⁷ spectrum is densely populated in the chain range (208 eigs in [0, 1618]) and any moderately-dense spectrum would match better than the sparse round-S⁷ (25 eigs in [0, 720]). This density-asymmetry inflates the apparent fit advantage.

## §6 Power analysis / Bonferroni correction

Spike #47 R4-1 tested 5 candidate selection rules (j₄ mod 4, Hopf-cycle phase 1/8, j₂+j₄ parity, pure-winding, and selection-mask). PR #585 then tested a 6th hypothesis (squashed-S⁷ correlation).

- Nominal threshold α = 0.05
- Bonferroni (5 tests): α = 0.010
- Bonferroni (6 tests including squashed): α = 0.0083
- Bonferroni (10 tests, conservative): α = 0.005

PR #585's p=0.041 (even taking it at face value) **fails ALL Bonferroni-corrected significance thresholds**. The replicated p ≈ 0.055 fails the nominal threshold as well.

## §7 What the structural signal actually is

The data DOES show that squashed-S⁷ spectrum has higher eigenvalue density in [0, 250] (208 unique eigs) than round-S⁷ (8 unique eigs in same range). For any chain of 8 integers spaced like Planck acoustic peaks, squashed-S⁷ will produce smaller median |Δ| than round-S⁷ simply because of density.

This is a **density-of-states observation**, not a structural correlation. It is consistent with the Spike #51.D primary finding (1/12 BIT-EXACT only at λ=0; spectrally distinct manifolds) and the broader Spike #51 R4 PARTITION-COEXISTENCE-CANONICAL framing. **It does not promote any new claim about CMB physics or hidden-fiber substrate-identity.**

## §8 Verdict

### H0-NOT-REPRODUCED

Under the conventional p < 0.05 significance criterion:
- PR #585's specific finding (p=0.041 with integer chain `{2,12,28,52,84,126,178,244}`) does not survive multi-seed replication (mean p ≈ 0.055 across 10 seeds).
- The continuous-chain Planck-faithful test gives p = 0.19.
- All 4 independent CMB experiments (WMAP, ACT, SPT-3G, Planck PR4) give p > 0.05 under the continuous-chain null.
- The integer chain in PR #585 occupies the top 3.1 percentile of 23,760 acceptable chains; this is consistent with **chain selection bias** (researcher degrees of freedom).
- Bonferroni correction at the Spike #47 5-rule hypothesis count drives the threshold to 0.01; PR #585 fails this even at face value.

The structural observation (squashed-S⁷ has denser eigenvalue packing than round-S⁷ in the relevant range, producing smaller median |Δ| against any Planck-derived chain) IS real but is a **density-of-states diagnostic**, not a hidden-fiber correlation.

## §9 PR #585 closure recommendation

**Recommended action**: amend PR #585 body to reflect Spike #180 finding:

1. **Strike** the "p=0.041" significance claim.
2. **Reframe** the CMB-fit finding from "NEW POSITIVE" to "DENSITY-OF-STATES OBSERVATION":
   - Squashed-S⁷ spectrum is denser than round-S⁷ in the chain range, producing tighter median |Δ| by ~5×.
   - This is consistent with two spectrally-distinct manifolds with different effective densities of states.
   - It does NOT constitute statistically significant evidence for substrate-identity, hidden-fiber correlation, or canonical-stance promotion.
3. **Preserve** the bit-exact spectrum comparison result (1/12 BIT-EXACT at λ=0 only; spectra distinct) as the load-bearing finding.
4. **Preserve** the Combined M-theory-instantiation-test verdict (across #582 + #584 + #585) but remove "CMB R4-1 chain correlation with squashed-S⁷ (hidden-fiber positive at p=0.04)" from the INSTANTIATED list. Move to "NOT INSTANTIATED" or "spectrally-distinct-density-observation".
5. **Flip PR #585** to ready-for-merge in this reduced-claim form OR close as researched-without-promotion.

This finding does NOT affect the Spike #51.D core verdict (CANNOT INSTANTIATE M-theory's bit-exact KK spectrum). That finding stands independently.

## §10 Fermatas / open questions for conductor

- **F-180-1**: PR #585 body text states "Null-hypothesis test (50 random uniform eigs in [0, 250], 10000 trials): p = 0.041" but the actual `spike_51_d_kk_spectrum.py` script in the worktree contains NO random null-test code. The p=0.041 record is only in the NDJSON output at line 33. Where was this test executed? Was it run with a different script? Was a specific seed used and not documented? Conductor decision: investigate whether this p value was actually computed and where the methodology lives.
- **F-180-2**: Spike #47 R4-1 itself reported p=0.027 for the chain's 8-peak match. That p-value was against a different null (substrate Λ-catalog randomization). This is a separate test from PR #585's chain-vs-random-uniform null. Both are now under suspicion. Conductor decision: should Spike #47 R4-1's F-α PASS verdict (which depends on the 8-peak ~1.6% match) be re-examined in light of the researcher-DOF analysis (only 3 of 8 peaks have unique integer candidates within tolerance)?
- **F-180-3**: The density-of-states observation (squashed-S⁷ denser than round-S⁷, producing tighter fits to any moderately-spaced chain) is itself a structural diagnostic with potential canonical value. Conductor decision: dispatch a follow-up spike to formalise this as a substrate-density-of-states comparison test? It would replace the spurious "hidden-fiber correlation" framing with the honest underlying signal.

## §11 R2 candidates (if conductor wishes to continue chain-related work)

- **R2-a**: Density-of-states test — for any geometric manifold M, compute eigenvalue density in [0, λ_max] and characterise the median |Δ| floor vs Planck chain. Establish the null distribution properly under varying spectral density. Distinguish "this manifold fits CMB" from "this manifold is dense in the relevant range".
- **R2-b**: Direct ℓ-space test — skip the substrate-Λ proxy entirely. Test whether `220 · √(Λ/2)` for various integer-Λ catalogs (round-S⁷, squashed-S⁷, S³ × S⁷, T⁷, etc.) lands near Planck peaks under proper KS-test methodology. This is the actual CMB-peak prediction test.
- **R2-c**: Pre-registered analysis — define the chain construction rule BEFORE seeing Planck data (e.g., "lowest 8 distinct eigenvalues of squashed-S⁷ in [0, 250]"), then test if those predicted peak positions match Planck. This is the only test free of researcher DOF.

## §12 Citations (PDF-verified per `[[feedback_pdf_extraction_citation_discipline]]`)

**arXiv open-access (PDF-verified):**
- Aghanim N., Akrami Y., Ashdown M., et al. 2020, "Planck 2018 results. VI. Cosmological parameters", arXiv:1807.06209 (Planck PR3 acoustic peaks)
- Hinshaw G., Larson D., Komatsu E., et al. 2013, "Nine-year WMAP Observations: Cosmological Parameter Results", arXiv:1212.5226 (WMAP 9-year)
- Aiola S., Calabrese E., Maurin L., et al. 2020, "The Atacama Cosmology Telescope: DR4 Maps and Cosmological Parameters", arXiv:2007.07288 (ACT DR4)
- Dutcher D., Balkenhol L., Ade P.A.R., et al. 2021, "Measurements of the E-Mode Polarization and Temperature-E-Mode Correlation of the CMB from SPT-3G 2018 Data", arXiv:2101.01684 (SPT-3G 2018)
- Akrami Y., Andersen K.J., Ashdown M., et al. 2020, "Planck intermediate results. LVII. Joint Planck LFI and HFI data processing", arXiv:2007.04997 (Planck PR4/NPIPE)
- Ekhammar S., Nilsson B.E.W. 2021, "On the squashed seven-sphere operator spectrum", arXiv:2105.05229 (squashed-S⁷ Casimir formulas; replicated from PR #585)
- Nilsson B.E.W. 2024, "Squashed 7-spheres, octonions and the swampland", arXiv:2412.04208 (r=p constraint; replicated from PR #585)

All citations verified by PDF / abstract page check; authors+title+arXiv-ID consistent. Reach-only paywalled sources (Awada-Duff-Pope 1983 PRL; Duff-Nilsson-Pope 1986 Phys.Rep.) cited by reference only.

## §13 Discipline guards honoured

- `[[user_stance_string_theory_instrument_first]]`: honest scoring; PR #585 p=0.041 reframed not inflated; density-of-states diagnostic preserved as honest underlying signal
- `[[feedback_no_privileged_primitive_classes]]`: 14 A-N intact; squashed-S⁷ vs round-S⁷ remains Class L sub-question of substrate-instantiation
- `[[feedback_algebra_not_magnitude]]`: marginal magnitude finding REJECTED for canonical promotion; magnitude-level findings need replication on independent data which they have not received
- `[[feedback_pdf_extraction_citation_discipline]]`: all 7 CMB-experiment citations PDF-verified
- `[[reference_autonomous_validation_tos_landscape]]`: only arXiv consulted; no paywalled sources accessed
- `[[feedback_trauma_informed_defensive_scope]]`: cosmology research-only; no targeting/capability
- `[[feedback_concertmaster_md_writes]]`: findings returned in this Markdown + NDJSON per conductor brief
- `[[feedback_concertmaster_git_worktree_isolation]]`: operating in worktree; no `git checkout -b`; no commits; conductor will integrate
- `[[feedback_ndjson_over_bloated_json]]`: NDJSON output with one record per finding per dataset
- `[[user_stance_identity_not_implementation_discipline]]`: tested PR #585's stated correlation hypothesis without redefining; null hypothesis applied as documented

## §14 Files written

- `docs/srmech/notes/spike180_cmb_hidden_fiber_confirmatory_prototype.py` — runnable analysis script (full methodology)
- `docs/srmech/notes/spike180_records_2026-05-19.ndjson` — 14 NDJSON records (spectrum summaries, per-dataset analyses, researcher-DOF analysis, best-Planck-chain null test, multi-seed robustness, final verdict)
- `docs/srmech/notes/spike180_cmb_hidden_fiber_confirmatory_findings_2026-05-19.md` — this findings document

## §15 Status

**COMPLETED — H0-NOT-REPRODUCED with chain-construction-bias diagnosis.** PR #585's marginal positive does NOT survive proper Monte-Carlo replication, faithful Planck-derived continuous-chain testing, OR independent-dataset confirmation. Recommend reduced-claim PR amendment per §9. The density-of-states observation underlying the spurious correlation IS structural and may be worth a separate spike (R2-a) but should NOT be sold as "CMB hidden-fiber correlation."

Math doesn't lie. The p-value didn't survive replication; the chain construction had researcher degrees of freedom; the independent datasets don't reproduce. Honest closure.

---

*End of Spike #180 findings. Conductor decision needed on PR #585 amendment scope (full close vs reduced-claim amendment vs density-of-states reframing).*
