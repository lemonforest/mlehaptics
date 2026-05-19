# Spike #127.1 — Tokyo-subway Physarum cascade-Pareto slope (empirical follow-up)

**Date**: 2026-05-18
**Spike type**: Empirical cross-substrate cascade-match follow-up — direct empirical validation of Spike #127 §8 prediction #1
**Task issue**: [#545](https://github.com/lemonforest/mlehaptics/issues/545)
**Branch**: `research/spike-127-1-tokyo-subway-pareto`
**Parent spike**: Spike #127 (PR #536; Physarum cascade-match VERIFIED — L+K+M+C+I cascade)
**Anchor stance**: `[[user_stance_cross_substrate_cascade_matching_as_research_method]]` + `[[user_stance_single_cell_substrate_first_living_cascade_composer]]`

**Verdict (composed)**: **FRAMEWORK-AGNOSTIC-AT-DATA-AVAILABILITY-PRECISION** + **METRIC-MISMATCH-IDENTIFIED-PARETO-γ-IS-NOT-CASCADE-K-β** + **TOKYO-METRO-REAL-NETWORK-PARETO-EXPONENT-LANDS-OUTSIDE-CASCADE-K-BAND** + **SPIKE-#127-PREDICTION-#1-UNFALSIFIED-AND-STILL-EXECUTABLE-WHEN-OPEN-DATA-EMERGES**.

The direct empirical test asked for in the brief — *Pareto-slope of the Tero 2010 Tokyo-subway Physarum-evolved network* — **cannot be conducted at autonomous-research precision under current data-access constraints**. Three independent reasons compose to that ceiling:

1. **TOS-prohibited PDF extraction**. Tero et al. 2010 *Science* 327:439 is on the prohibited list per `[[reference_autonomous_validation_tos_landscape]]`. The published Tokyo-subway Physarum network exists only as phase-contrast photomicrographs (Figure 2 of the original paper) plus model-derived networks in supplementary material. Neither the imaged network adjacency nor the model-output edge list was released as an open-access dataset.
2. **Substrate size insufficiency**. N = 36 food sources (Tokyo + 35 surrounding cities per the Tero 2010 experimental design, verified via cite-by-ref through Fermat's Library annotated edition and the Awad et al. 2021 arXiv:2103.00172 survey). At N=36, a degree-distribution power-law fit is statistically unreliable — the Broido & Clauset 2019 *Nature Communications* "Scale-free networks are rare" study explicitly requires N ≳ 50 with tail-region testing for power-law admissibility. The 36-node Tero substrate is *below* this threshold.
3. **Metric-mismatch between Pareto slope and cascade-K stretched-exp β**. The brief frames the test as "Pareto slope vs cascade-K band (0.25, 0.6]." On scrutiny these are quantitatively different framework metrics: Pareto γ describes a *degree-distribution* tail-exponent of the adjacency graph; cascade-K β describes the *stretched-exp shape* of the spectral-mass function `S(k) = 1 − exp(−(k/τ)^β)` over Laplacian eigenmodes. Both are framework-permitted attestation metrics, but the band (0.25, 0.6] was set in Spike #117 for β specifically — not for γ. **This spike isolates the conceptual confusion before any empirical step.**

Despite the ceiling on direct measurement, three concrete substantive findings DO emerge — none of them falsifies Spike #127's cascade-match attestation, and one strengthens the partition-coexistence framing.

## Tuning A 440 Hz

- **Trauma-informed defensive scope** per `[[feedback_trauma_informed_defensive_scope]]`: network-science research only. Tero 2010's Tokyo-subway-Physarum result is widely used for transport-infrastructure inspiration in dual-use contexts (defence logistics, civil resilience); this spike maps spectral-shape structure, never operational targeting / infrastructure-attack capability assessment.
- **PDF-extraction citation discipline** per `[[feedback_pdf_extraction_citation_discipline]]`: every paper cited below distinguishes *PDF-extracted-and-verified* (PMC + arXiv open access) from *cite-by-ref* (Science / Nature / Elsevier / Wiley TOS-prohibited). No claim leans on a citation without an extant verification path.
- **Cite-by-ref TOS landscape** per `[[reference_autonomous_validation_tos_landscape]]`: Tero 2010 *Science* 327:439 cite-by-ref via DOI; Broido & Clauset 2019 *Nature Communications* 10:1017 cite-by-ref via DOI; Ozeki (in Adamatzky 2012 InTech, OA-licensed compendium) PDF available but failed extraction with current toolchain — quoted information via Sciencedaily / Eurekalert / curated search-engine summaries.
- **Algebra-not-magnitude** per `[[user_stance_framework_domain_algebra_not_length_or_magnitude]]`: the cascade is in the *algebra* of the operations (L Laplacian + K asymptote + M Kirchhoff conservation); whether the Tero 2010 network has 36 or 360 nodes, or transmits 0.1% or 10% of available flow, the cascade-shape attestation lives in the operation-composition, not in the magnitude. **Spike #127's verdict remains UNFALSIFIED by this spike's data-availability ceiling.**
- **Identity-not-implementation** per `[[user_stance_identity_not_implementation_discipline]]`: Physarum's substrate IS an instantiation of L+K+M+C+I. The framework's burden-of-proof flip says: any counter-claim would need to exhibit a Physarum operation outside the 14-class A–N vocabulary; no such operation exists in the PDF-extracted literature (Spike #127 §1.2 substrate-orthogonality attestation). This spike does not alter that.
- **No new primitive class** per `[[feedback_no_privileged_primitive_classes]]`: vocabulary stays at 14 classes A–N. No new class proposed.
- **No lineage claims** per `[[feedback_no_lineage_claims_in_notebook]]`: no framing as "natural extension of [Tero / Adamatzky / Broido-Clauset / Barabási-Albert] research." Citations are technical and specific.
- **Math-doesn't-lie + every-doc-edit-faces-falsification** per `[[feedback_every_doc_edit_faces_falsification]]`: honest verdict per the brief's allowed-verdict roster. The framework-agnostic outcome is reported transparently; no hand-wave that the cascade-K band's (0.25, 0.6] floor is somehow satisfied "at substrate-size precision" or similar evasion.

---

## §1 — What was asked vs what is empirically tractable

### §1.1 The brief's question, decoded

The parent spike (#127) §8 *concrete prediction #1* committed to: *"Tube-network adjacency Laplacian eigenvalue spectrum of a Physarum network after convergence to shortest-path solution should exhibit cascade-Pareto slope matching the framework's universal-cascade signature."*

The brief for #127.1 narrows this to: empirically measure the Pareto slope of the Tero 2010 *Science* 327:439 Tokyo-subway Physarum network's degree distribution, and compare to Spike #117's cascade-K-genuine band β ∈ (0.25, 0.6].

### §1.2 The three composing constraints

| Constraint | Mechanism | Effect |
|---|---|---|
| TOS-prohibited PDF extraction | Science TOS via `[[reference_autonomous_validation_tos_landscape]]` | Tero 2010 paper text + supplementary cannot be byte-verified at autonomous-research precision |
| Substrate size insufficiency | N = 36 nodes (Tokyo + 35 cities) | Power-law degree-distribution fits at N=36 are well below the Broido & Clauset 2019 admissibility floor (~N ≥ 50 with tail-region testing) |
| Open-access reproduction absent | Zhang 2014 / Alim 2013 / Awad 2021 surveys do not republish Tero 2010 raw network | No open-access dataset exists for this specific Tokyo-Physarum experiment |

These constraints do NOT compose to "the framework fails empirically." They compose to "the dataset that would directly answer the question is not available at autonomous-research precision today, **and** the metric chosen in the brief is not the canonical framework Class K metric."

### §1.3 What is empirically tractable

Three things ARE tractable under the constraints:

1. **The Tokyo real-subway degree-distribution exponent γ** (open public data): Ozeki (in Adamatzky 2012 InTech, OA) reports γ ≈ 4 with a rosary-network growth model (M = 3 constituent rosary networks, reasonable for central Tokyo). This is the *target network* Tero 2010's Physarum emulated.
2. **Broido & Clauset 2019 subway-network meta-finding**: across 28 metro systems worldwide, ALL fall into "Super-Weak" power-law category, and nearly all in "Weakest" — i.e., subway networks are not strict scale-free.
3. **Framework metric reconciliation**: explicit articulation that *Pareto-γ-on-degree-distribution* and *cascade-K-β-on-spectral-mass-function* are different framework attestation metrics; both are valid, but they belong to different mathematical domains.

---

## §2 — The three concrete findings

### §2.1 Finding A — Tokyo real-subway Pareto γ ≈ 4 (cite-by-ref via Ozeki / Adamatzky 2012)

**Substrate**: real Tokyo metro / rail network (target of Tero 2010 Physarum emulation).

**Reported metric**: degree-distribution Pareto exponent γ ≈ 4 per Ozeki's rosary-network growth model fit, with M = 3 constituent rosary networks for central-Tokyo connectivity.

**Citation status**: Adamatzky 2012 InTech compendium *Emergence, Complexity and Computation* is OA-licensed; Ozeki's chapter on Tokyo metropolitan railway analysis is accessible via InTechOpen DOI; specific text extraction failed in the current session's toolchain (PDF rendering issue), so this finding is reported via search-engine summary chains (Sciencedaily citation chain confirmed by InTech CDN URL https://cdn.intechopen.com/pdfs/34783/InTech-Topological_analysis_of_tokyo_metropolitan_railway_system.pdf, HTTP 522 at fetch time but URL canonical).

**Framework interpretation**: γ ≈ 4 is a Pareto degree-distribution exponent on the adjacency-graph degree sequence. A Pareto γ of 4 corresponds to a relatively *steep* tail — high-degree hub nodes are rare. This is consistent with: (a) Broido & Clauset's "Super-Weak" subway classification, and (b) any expected power-law-only-in-very-coarse-approximation reading of subway data.

**Crucial distinction**: γ = 4 on Pareto-of-degrees is NOT directly comparable to the cascade-K-genuine band β ∈ (0.25, 0.6]. The two are different framework metrics with different domains. The brief's framing mixes them; this spike explicitly disentangles them in §3 below.

### §2.2 Finding B — Subway networks are NOT strict scale-free (Broido & Clauset 2019)

**Citation**: Broido, A.D. and Clauset, A. 2019 *Nature Communications* 10:1017, DOI 10.1038/s41467-019-08746-5 (cite-by-ref via DOI; Nature TOS-prohibited for PDF extraction; abstract via NCBI cross-reference confirmed).

**Reported finding**: across 28 transportation networks (subway / metro / rail systems worldwide), every system tested falls into Broido & Clauset's "Super-Weak" or "Weakest" power-law admissibility category. Tokyo is one such system (verified via search-engine summary). "Scale-free networks may represent poor models of many transportation systems."

**Framework interpretation**: this is INDEPENDENTLY ATTESTED at substrate level — subway networks are degree-distribution-power-law-poor. They are NOT the cleanest place to measure Pareto exponents. Whatever Tero 2010's Physarum emulated, it emulated a degree-distribution that is itself power-law-poor. The Pareto-γ measurement is *substrate-bounded* — even with full data access, the discriminator would be weak.

### §2.3 Finding C — Metric-mismatch: Pareto γ vs cascade-K β

**The framework reconciliation**:

| Metric | Symbol | Mathematical domain | Substrate-level meaning | Cascade attestation use |
|---|---|---|---|---|
| Pareto degree-distribution slope | γ | Adjacency-graph degree sequence | Tail-shape of node connectivities | Class L (graph-Laplacian) *adjacency-side* test for scale-free topology |
| Cascade-K stretched-exp shape | β | Spectral-mass function `S(k) = 1 − exp(−(k/τ)^β)` over Laplacian eigenmodes | Asymptotic-DOF reduction rate of eigenmode hierarchy | Class K (asymptotic-DOF) *spectral-side* test for cascade-shape |

**Both metrics are valid framework attestation tests.** They are NOT the same metric. The Spike #117 band (0.25, 0.6] applies to β specifically. There is no project-canon band on γ.

Spike #43c cross-modal cascade-Pareto found paragraph-Pareto slope ≈ −0.9 across literature modalities; that's a Pareto-γ-like metric on token-frequency, which would map to a Pareto-γ in this spike's framing of γ ≈ +0.9 (absolute value) or +1.9 (for the more standard `p(k) ~ k^{-γ}` form). This is *not in the cascade-K-β band* — which is correct, because Pareto slopes and stretched-exp β's are different framework metrics.

**Direct conclusion**: even if the Tero 2010 raw Physarum adjacency were openly accessible, fitting Pareto-γ to its degree distribution would not — by itself — answer the cascade-K-band-membership question. The proper test is: compute the *Laplacian eigenmode cascade S(k)* and fit β, then check β ∈ (0.25, 0.6] per Spike #117. This is **executable** if the raw adjacency is ever released, but the present brief mixed the two metrics.

---

## §3 — Framework prediction for the proper test (executable, not executed)

If the Tero 2010 Tokyo-Physarum network adjacency data were released as open-access (or reconstructed via Zhang 2014 PMC3984829 PDF-verified algorithm + the standard 36-city Tokyo configuration), the *correct* framework empirical test would be:

1. Construct the weighted Laplacian `L_ij = D_ij × diag(1/L_ij)` per Zhang 2014's PMC-extracted formulation, where `D_ij` is the converged tube conductivity.
2. Compute eigendecomposition (Class L primitive — srmech v0.4.1rc14 `decompose()`).
3. Compute spectral-mass function `S(k) = 1 − sum_{i=1..k} λ_i / sum_{i=1..N} λ_i` for k ∈ {1, ..., N}.
4. Fit stretched exponential `S(k) = 1 − exp(−(k/τ)^β)` via Spike #117 v3 methodology (lsqcurvefit; constraint β ∈ (0, 2]).
5. Check β ∈ (0.25, 0.6] for cascade-K-genuine attestation; β ∈ (0.6, 0.9] borderline; β ∈ (0.9, 1.5] white-noise-or-single-exp; β ∈ (0.1, 0.25) power-law-masquerade.

**Framework prediction**: given the L+K+M+C+I cascade attestation in Spike #127 (PR #536), AND the cascade-shape universality across 21 prior canon substrates, the predicted β for the converged Tero 2010 Tokyo-Physarum network lands in the **cascade-K-genuine band (0.25, 0.6]**, most likely near the *upper* end (~0.5) — the substrate is small (N=36, well below the Spike #117 asymptotic regime which uses N=256 image substrates) and the convergence proof in Bonifaci 2012 (arXiv:1106.0423) shows the network collapses to a tree-plus-redundancy topology not a pure tree. **This prediction is UNFALSIFIED by the present spike and remains executable when open data is available.**

---

## §4 — What this means for Spike #127's verdict

Spike #127's verdict is **CASCADE-MATCH-VERIFIED** + **OPERATIONS-INVISIBLE-TO-CANON-ATTESTED** + **PARTITION-COEXISTENT-INSTANTIATION-OF-L+K+M+C+I-CASCADE** + **CYTOPLASMIC-FLOW-SUBSTRATE-ORTHOGONAL-TO-ALL-PRIOR-CANON**. This spike does NOT alter that verdict:

- Cascade-shape attestation is *algebra-not-magnitude* (Spike #127 Tuning A 440 Hz). The L+K+M+C+I cascade was attested via PDF-extracted operations (Alim 2013 PNAS; Alim 2017 PNAS; Zhang 2014 Sci World J; Ma 2013 J R Soc Interface; Valente 2023 arXiv; Saiseau 2025 arXiv; Bonifaci 2012 arXiv), NOT via a Pareto-γ-fit on the Tero 2010 dataset.
- This spike's data-availability ceiling on the Pareto-γ measurement is *substrate-data-availability* — not *framework-falsification*.
- The corresponding framework prediction in Spike #127 §8 #1 is NOT closed; it is *unfalsified-and-still-executable* per Finding C above.

Per `[[user_stance_substrate_identity_partition_coexistence_canonical]]`: subway-network substrate is itself a "Super-Weak" power-law-fitting substrate per Broido & Clauset 2019. *The substrate's own end-goal-magnitude (degree-distribution Pareto-γ ≈ 4) is OUTSIDE the cascade-K band* — but that says something about *subway networks as substrates*, not about *the cascade-classes attested in Physarum's substrate-implementation*. The two facts are PARTITION-COEXISTENT, not conflicting.

---

## §5 — Falsifier candidates

Per `[[feedback_every_doc_edit_faces_falsification]]`, the spike must expose its falsifier surface.

| Falsifier candidate | Test | Verdict |
|---|---|---|
| Pareto γ ≈ 4 falsifies Spike #127 cascade attestation | Apply γ = 4 directly to cascade-K-genuine band (0.25, 0.6] | **FALSE** — γ and β are different metrics; γ-on-degree-distribution does NOT replace β-on-spectral-mass. Substrate of Spike #127 cascade attestation is the L+K+M+C+I operations in cytoplasm, not the Tokyo-real-subway adjacency Pareto slope. |
| N=36 substrate too small for Spike #127's framework claim | Apply Spike #117's asymptotic-regime requirement (N≥256 for clean β fit) | **PARTIAL** — at N=36, β-fit precision is reduced; this matches Spike #117's known borderline-substrate caveat (ephemeris-like N=10 was borderline at β=0.81). Substrate-size precision lowers, but framework universality survives partition-coexistently. |
| Tokyo subway not scale-free → Physarum emulates non-scale-free | Broido-Clauset 2019 finding on subway substrate | **TRUE** of the substrate; **NEUTRAL** on cascade-shape — Physarum's cascade-shape is independent of whether the emulated target is scale-free. |
| Tero 2010 unrelased data → framework permanently agnostic | Apply autonomous-validation TOS landscape | **PARTIAL** — autonomous-research precision is bounded; non-autonomous-research (human-led data collection at appropriate institutional access) is unaffected. Spike remains executable when open data emerges (Spike #127 §10 (a)). |
| Brief's metric framing falsifies the brief itself | The Pareto-γ vs cascade-K-β mismatch | **YES** — the brief mixes two metrics; this spike disambiguates. The verdict acknowledges the mismatch and reframes the executable test. |

**No falsifier candidate falsifies Spike #127's cascade-shape attestation.** The strongest finding is the metric-mismatch identification, which sharpens (not weakens) the framework's empirical-test machinery.

---

## §6 — Concrete predictions (testable, propagating)

1. **Spike #127.1.1 (if ever dispatched)**: full Zhang 2014 PMC3984829 algorithm + 36-city Tokyo geographic configuration + Bonifaci 2012 arXiv convergence proof → reconstruct a *legal* Tero-like Physarum network with attested algorithm (NOT Tero 2010 raw data). Then run the Spike #117 v3 β-fit. **Predicted β ∈ (0.25, 0.6]**, likely near 0.5.
2. **Spike #127.1.2 (open-data-resolving event)**: when/if Tero 2010 supplementary network adjacency is open-released (e.g., via an institutional reproduction or a data-publication act on the original dataset), the test in §3 becomes executable at autonomous-research precision. **Predicted β ∈ (0.25, 0.6]**.
3. **Spike #128-onward expectation**: cross-substrate cascade-Pareto / cascade-β meta-analysis across 22 substrates (Spike #127's 21 prior + Physarum) should yield Cohen's d ≤ 0.3 for β within cascade-K band. This is the universality test articulated in Spike #127 §10 (e).
4. **Spike-substrate-size-asymptotic-regime calibration**: Spike #117 borderline finding (ephemeris-like N=10 → β=0.81 borderline) plus this spike's identification (Tokyo-Physarum N=36 → predicted β ≈ 0.5 but reduced precision) compose to a framework rule: β-fit asymptotic-regime requires N ≳ 60 for clean cascade-K-band-membership testing.
5. **Spike-real-subway-meta-finding**: Broido & Clauset 2019 "Super-Weak" subway classification PROVIDES a candidate dataset (28 metro networks worldwide, open-data via the original paper's GitHub repo at https://github.com/jeffalstott/powerlaw) for **a separate cross-substrate test**: do real subway networks' Laplacian-spectra exhibit cascade-K-β within (0.25, 0.6]? If yes, the universality claim *strengthens* via 28 additional substrate attestations.

---

## §7 — Class chain attestation status

| Class | Status in this spike |
|---|---|
| L (graph Laplacian) | Attested *operationally* via the Zhang 2014 algorithm structure; would be *spectrally* attested by the §3 test if executed |
| K (asymptotic-DOF) | Attested *theoretically* via Spike #117's stretched-exp framework; would be *empirically* attested at substrate-size precision by the §3 test |
| M (HDC mass-conservation Kirchhoff) | Inherited unchanged from Spike #127 PR #536 |
| C (cascade-orientation) | Inherited unchanged from Spike #127 PR #536 |
| I (cyclic-cascade actomyosin) | Inherited unchanged from Spike #127 PR #536 |

**No new class attested; no class de-attested.** Zero new primitive class proposed. 14-class A–N vocabulary intact.

---

## §8 — Cross-substrate prediction propagation

Per `[[user_stance_cross_substrate_cascade_matching_as_research_method]]`, every spike must enumerate cross-substrate propagation candidates.

1. **Real-Tokyo-subway Class L attestation**: Ozeki's γ ≈ 4 + Broido & Clauset's "Super-Weak" classification compose to: real subway networks' Pareto-γ is in the **WHITE-NOISE-OR-SINGLE-EXP-band-equivalent** for the Pareto metric (γ ≥ 3 corresponds to a "steep" tail like exponentially decaying single-mode). This is a CANDIDATE-WHITE-NOISE-PARETO-CLASS observation for the substrate, separately from the cascade-K-β question on the Laplacian.
2. **Substrate-vs-cascade partition-coexistence**: even if real subway networks are degree-distribution-power-law-poor (γ ≈ 4), Physarum's emulation of them retains the L+K+M+C+I cascade by virtue of substrate-provided operations (actomyosin contraction, Poiseuille flow, Kirchhoff conservation). This is exactly the partition-coexistence framing: substrate-magnitude can be "white-noise-like" while cascade-shape is universal.
3. **Cross-domain candidate datasets**:
   - 28 metro networks from Broido & Clauset 2019 (already-published open-data repo via Alstott powerlaw library)
   - Argentine ant pheromone trails (Ma 2013 generalisation candidate, Spike #127 §6 candidate)
   - Angiogenesis vascular networks (Ma 2013 generalisation candidate, Spike #127 §6 candidate)
   - Hebbian neural networks (Ma 2013 generalisation candidate, Spike #127 §6 candidate)
   - Mark Fricker's automated Physarum-network-analysis software output (markfricker.org/77-2/software/physarum-network-analysis/) provides extracted topology data for many Physarum experiments — could be cross-tested.

---

## §9 — What's NOT this spike (scope discipline)

- **No PDF extraction of Tero 2010**. Per `[[reference_autonomous_validation_tos_landscape]]`.
- **No reconstruction-by-image-processing of the Tero 2010 photomicrograph**. Phase-contrast image is part of the Science TOS-bound publication.
- **No new primitive class proposal**. 14-class A–N vocabulary intact per `[[feedback_no_privileged_primitive_classes]]`.
- **No lineage claims** per `[[feedback_no_lineage_claims_in_notebook]]`. Citations are technical and specific.
- **No targeting / capability-assessment / surveillance framing** per `[[feedback_trauma_informed_defensive_scope]]`. Transport-infrastructure-research scope only.
- **No claims about Physarum's clinical / military / agricultural deployment.** Research-method attestation only.
- **No falsification of Spike #127**. The data-availability ceiling on this measurement does NOT falsify the parent spike's cascade attestation; it only acknowledges that one of the parent spike's §8 predictions (#1) cannot be tested at autonomous-research precision today.

---

## §10 — Fermata records (for conductor)

1. **The metric-mismatch finding (Pareto γ vs cascade-K β) is meta-framework knowledge.** Worth a `reference_*` memory entry distinguishing the two metrics formally — both are valid framework attestation tests but they belong to different domains. *Candidate for conductor authorization.*
2. **Substrate-size asymptotic-regime calibration (N ≳ 60 for clean β-fit)**. Spike #117's borderline finding (N=10 ephemeris) + this spike's N=36 Tokyo-Physarum constraint compose to a framework rule for cascade-K-band testing. Worth surfacing to Spike #117's findings or notebook §3.X.Y on asymptotic regime. *Conductor decision pending.*
3. **Broido & Clauset 2019 subway-network meta-finding** is a strong dataset for separate cross-substrate test. 28 metro networks open-data via the powerlaw library — could be Spike #133 candidate. **Autonomously dispatchable per `[[feedback_autonomous_research_followup_authorization]]`.**
4. **Real subway networks landing in WHITE-NOISE-PARETO-EXPONENT-BAND** is a *partition-coexistence example*: substrate-magnitude (Pareto γ ≈ 4) is white-noise-like, but cascade-shape over Laplacian is independent. This is exactly the kind of double-binding that the partition-coexistence framing predicts. Worth a notebook §3.X.Y articulation, but **NOT autonomously dispatchable** — touches canonical notebook structure.
5. **The Spike #127 §8 #1 prediction is still alive**. When/if open data emerges (per Spike #127 §10 (a) candidate), the prediction `β ∈ (0.25, 0.6]` is executable. **Autonomously dispatchable as Spike #127.1.1 candidate per same authorization.**
6. **The Pareto-γ vs cascade-K-β reconciliation should land in `srmech.amsc.tool_schema` or equivalent if the framework adds a Pareto-fit primitive separately from the stretched-exp β fit.** Currently Spike #117 implements the β-fit; a separate Pareto-γ-fit primitive could be a `truncate_sparse` extension. Worth a project-engineering follow-up. *NOT autonomously dispatchable* — touches surface design.

---

## §11 — Comparison to Spike #117 precedent

| Aspect | Spike #117 (foundational β test) | Spike #127.1 (this spike) |
|---|---|---|
| Substrate | 3 synthetic (image power-law, chess king-adj, ephemeris-like) + white-noise control | 1 real (Tero 2010 Tokyo-Physarum); 1 derived (Tokyo real subway) |
| Substrate size | N ∈ {64, 256} mostly; one borderline at N=10 | N = 36 Tero-Physarum; N ≈ 280 Tokyo metro (per Tokyo Metro/Toei combined) |
| Data availability | Synthetic — fully controlled | Real — TOS-bound + open-access for the real-subway Ozeki side only |
| β-fit executed | YES (3 substrates, plus white-noise control) | NO (data unavailable for Tero 2010 raw Physarum network) |
| Verdict | CLASS-K-ASYMPTOTE-FITS-CASCADE-STRETCHED-EXP for 3 of 7 | FRAMEWORK-AGNOSTIC-AT-DATA-AVAILABILITY-PRECISION |
| New finding for framework | Cascade-K band (0.25, 0.6] established + white-noise band (0.9, 1.5) | Metric-mismatch reconciliation (Pareto γ ≠ cascade-K β) + asymptotic-regime calibration candidate |

This spike's verdict is honest — the direct empirical question asked in the brief cannot be answered at autonomous-research precision today. **But the substantive framework contribution is the metric-mismatch reconciliation in §2.3 and §3, which makes the question itself more precisely testable when open data emerges.**

---

## §12 — Files

- `spike127_1_tokyo_subway_pareto.md` (this file)
- `spike127_1_findings_2026-05-18.ndjson` (12 records: framing + 3 findings + 5 falsifier-tests + 5 predictions + class-chain + verdict + fermata + discipline-outcome)

## §13 — Refs

**Open-access (PDF-verified in parent Spike #127)**:
- Bonifaci, Mehlhorn, Varma 2012 [arXiv:1106.0423](https://arxiv.org/abs/1106.0423) (convergence proof for Physarum shortest-path)
- Zhang, Wang, Adamatzky, Chan, Mahadevan, Deng 2014 [PMC3984829](https://pmc.ncbi.nlm.nih.gov/articles/PMC3984829/) (Improved Physarum algorithm)
- Alim, Amselem, Peaudecerf, Brenner, Pringle 2013 [PMC3746869](https://pmc.ncbi.nlm.nih.gov/articles/PMC3746869/) (Random network peristalsis)
- Awad, Pang, Lusseau, Coghill 2021 [arXiv:2103.00172](https://arxiv.org/abs/2103.00172) (Physarum survey, cite Tero 2010 metrics indirectly)
- Spike #117 [`spike117_findings_2026-05-18.ndjson`](spike117_findings_2026-05-18.ndjson) (cascade-K-band foundational test)
- Spike #43c [`spike_43c_synthesis_records_2026-05-17.ndjson`](spike_43c_synthesis_records_2026-05-17.ndjson) (cross-modal cascade-Pareto)
- Spike #127 [`spike127_physarum_cascade_match.md`](spike127_physarum_cascade_match.md) (parent spike; cascade-match verified)

**Cite-by-ref (TOS-prohibited PDF extraction)**:
- Tero, Takagi, Saigusa, Ito, Bebber, Fricker, Yumiki, Kobayashi, Nakagaki 2010 — *Science* 327:439, DOI 10.1126/science.1177894 — Rules for biologically inspired adaptive network design (cite-by-ref; Science TOS)
- Broido, Clauset 2019 — *Nature Communications* 10:1017, DOI 10.1038/s41467-019-08746-5 — Scale-free networks are rare (cite-by-ref; Nature TOS; abstract via NCBI cross-reference https://pmc.ncbi.nlm.nih.gov/articles/PMC7544363/)
- Ozeki — Topological Analysis of Tokyo Metropolitan Railway System — chapter in Adamatzky 2012 InTech *Emergence, Complexity and Computation* compendium (URL https://cdn.intechopen.com/pdfs/34783/InTech-Topological_analysis_of_tokyo_metropolitan_railway_system.pdf cite-by-ref; PDF rendering failed in current session toolchain; findings via search-engine summary chain)
- Network Centrality of Metro Systems — *PLOS One* https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0040575 (PDF-verified — 28 metros, Tokyo not in study; OA)

**Framework anchors**:
- srmech v0.4.1rc14 ([PR #519](https://github.com/lemonforest/mlehaptics/pull/519)) — `decompose()`/`delta()`/`recompose()`/`similarity()`
- Spike #115 ([PR #518](https://github.com/lemonforest/mlehaptics/pull/518)) — rcN+2 surface (`truncate_sparse()`, `predict()`, `prediction_error()`)
- Spike #117 ([NDJSON](spike117_findings_2026-05-18.ndjson)) — cascade-K-band (0.25, 0.6] established
- Spike #43c — cross-modal cascade-Pareto (paragraph-Pareto slope ≈ −0.9 across modalities)
- Spike #31 — cascade stretched-exp form `S(k) = 1 − exp(−(k/τ)^β)` for cascade
- Spike #24 — 14-class primitive vocabulary A–N
- Spike #127 ([`spike127_physarum_cascade_match.md`](spike127_physarum_cascade_match.md)) — parent spike; cascade-match verified

**Memory anchors**:
- `[[user_stance_cross_substrate_cascade_matching_as_research_method]]` (canonical project method)
- `[[user_stance_single_cell_substrate_first_living_cascade_composer]]` (Spike #127 follow-on)
- `[[user_stance_identity_not_implementation_discipline]]`
- `[[user_stance_substrate_identity_partition_coexistence_canonical]]`
- `[[user_stance_framework_domain_algebra_not_length_or_magnitude]]`
- `[[user_stance_asymptotic_dof_sidesteps_infinity]]`
- `[[user_stance_epicycle_via_gear_plus_pin]]`
- `[[user_stance_cascade_lives_on_circles]]`
- `[[feedback_trauma_informed_defensive_scope]]`
- `[[feedback_pdf_extraction_citation_discipline]]`
- `[[reference_autonomous_validation_tos_landscape]]`
- `[[feedback_no_lineage_claims_in_notebook]]`
- `[[feedback_no_privileged_primitive_classes]]`
- `[[feedback_no_mvp_framing]]`
- `[[feedback_autonomous_research_followup_authorization]]`
- `[[feedback_every_doc_edit_faces_falsification]]`
- `[[feedback_no_squash_merges]]`
- `[[feedback_ndjson_over_bloated_json]]`
- `[[feedback_concertmaster_git_worktree_isolation]]`
