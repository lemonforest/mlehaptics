# Spike #38 — Mass-spec fingerprint FFT against project SM primitive classes (molecular-substrate exploration)

**Date:** 2026-05-17
**Research spike artifact.** Concertmaster dispatch per user direction *"generate a research agent to get a mostly known, commonly accepted, complex with undefined noise datapoint of a mass spec fingerprint and see if we can FFT it against the SM that we've already mapped. This is either be a refine or fail I think because I don't know that we have molecular modeling catalog yet."*

> **Discipline.** Closed-form deterministic code; NDJSON outputs per `[[feedback_ndjson_over_bloated_json]]`; falsifier controls run before claiming positive findings (50 random-graph seeds × 50 random-mass-spec seeds + 5 named molecular controls); canonical citation provenance verified at API level per `[[feedback_pdf_extraction_citation_discipline]]`; no commercial-publisher access per `[[reference_autonomous_validation_tos_landscape]]`.

---

## §1 Bottom line

**Overall verdict: FAIL at spectral-shape level + PARTIAL at binding-level overlay.**

The user anticipated this: *"I don't know that we have molecular modeling catalog yet."* Confirmed. The project's SM spectral signatures (K-ladder, L-FFT-match, cascade-β) do not bolt onto molecular mass spec at the spectral-shape level. The 14-class information-instrument overlay applies at the binding level by cataloguing assignment — consistent with Spike #37 but not a substrate-FFT-match result.

| Signature tested | Verdict | Notes |
|---|---|---|
| **Class K** Kepler-shape `c_k = ε^k/k` ladder (Spike #30B v3 three-criteria) | **ABSENT** | eps_fit=1.081 (outside 0.001–0.5); r²=0.156; not monotonic-decreasing. All three criteria fail. Honest absence, not failure — per `[[user_stance_kepler_shape_universal]]` K appears *where Kepler-shape appears*; molecular mass spec is not such a substrate. |
| **Class L** graph-Laplacian FFT-correlation (Spike #30B / #35-Q3 method) | **FALSIFIED at FFT-match level / trivially present at existence level** | Initial cosine-sim 0.8115 appeared tantalising; falsifier controls demoted it. 50 random 14-node graphs gave mean 0.857 ± 0.043 (caffeine self −1.06 σ BELOW random); glucose gave 0.879 (higher than caffeine). Methodology breaks at n~14 substrate size. |
| **Cascade-β** = d_S/(d_S+2) (Spike #31 v3 dual-signature) | **ABSENT with substrate-too-small caveat** | Predicted β=0.497, empirical β=0.817 (Δβ=+0.32). Spike #31 documents Weyl-fit quality below n~100 is poor; n=14 in unreliable regime. Not a clean falsifier; substrate-too-small-to-test. Side observation: intensity rank-distribution shows Zipf-like power law (slope −1.83, r²=0.95). |
| **Information-instrument identity** (Spike #37 14-class overlay) | **APPLIES at 12/14 classes by binding-level assignment** | Cataloguing claim consistent with Spike #37 substrate-portability table; NOT a falsifiable spectral measurement. K tested in row 1; H ("self-introspection") only no (molecules are objects, not agents). |

## §2 Provenance — MassBank EU caffeine record

**Subject:** caffeine (C₈H₁₀N₄O₂, MW 194.08038)
**Accession:** `MSBNK-Fac_Eng_Univ_Tokyo-JP003477` ("CAFFEINE; EI-B; MS")
**Authors:** Mass Spectroscopy Soc. of Japan (MSSJ)
**Instrument:** HITACHI M-60 magnetic-sector, 20 eV electron ionization
**License:** CC BY-NC-SA (permitted per `[[reference_autonomous_validation_tos_landscape]]`)
**Peak count:** 58 (m/z 41–196, base peak M⁺ at m/z 194, rel=999)
**SPLASH:** `splash10-0a4l-4900000000-3ff72dace6687d242f1f`
**API URL:** `https://massbank.eu/MassBank-api/records/MSBNK-Fac_Eng_Univ_Tokyo-JP003477`

**Source-acquisition trail:**

- **NIST WebBook** caffeine spectrum (ID C58082) **declined**: "Due to licensing restrictions, this spectrum cannot be downloaded." Catalog entry exists but data is not served as API.
- **MoNA REST** returned **401 (auth required)** as of 2026-05-17 — appears to have moved to auth-gated access post prior project session.
- **MassBank EU API** (`/MassBank-api/records/{accession}`) returned **full JSON including raw `(m/z, intensity, rel)` triples** — this is the working academic-open ingress for permitted mass-spec data.

The raw record fixture is committed alongside the analysis as `spike_38_caffeine_JP003477.json` (4.8KB). Provenance from raw JSON: accession + license + authors + instrument + ionization energy + ChemOnt classification + InChI + SMILES + 58 peak triples + SPLASH.

## §3 Per-signature verdicts (detail)

### §3.1 Class K Kepler-shape ladder — ABSENT

Using Spike #30B v3 strict three-criteria test (eps in physical range 0.001–0.5; r² > 0.99; monotonic-decreasing):

| Criterion | Caffeine result | Pass? |
|---|---|---|
| eps_fit physical | 1.081 | NO (out of range) |
| r² > 0.99 | 0.156 | NO |
| monotonic-decreasing | False | NO |

Coefficients oscillate (chess / Sierpinski / SHA pattern), not Kepler ladder. Per `[[user_stance_kepler_shape_universal]]`, K is universal *where Kepler-shape appears*; caffeine mass spec is not such a substrate. **Honest absence, not framework failure** — the framework correctly says "no" when no Kepler-shape signature is present.

### §3.2 Class L graph-Laplacian FFT-correlation — FALSIFIED at FFT-match / trivially present at existence

Initial finding looked positive: cosine similarity between caffeine molecular-graph (14 heavy atoms, 15 edges) Laplacian eigval-density histogram and caffeine mass-spec FFT power = **0.8115**.

Falsifier controls demoted this to artifact:

| Control | Cosine similarity |
|---|---|
| Caffeine self (C1) | 0.8115 |
| Ethane (C₂H₆, n=2) | 0.5088 |
| Benzene (C₆H₆, n=6) | 0.5452 |
| Glucose (C₆H₁₂O₆, n=12) | **0.8793** |
| Path graph n=14 | 0.7945 |
| Cycle graph n=14 | 0.6435 |
| Random 14-node graph mean ± std (50 seeds) | **0.8569 ± 0.043** |
| Random 14-node graph max | **0.9314** |
| Random mass-spec vs caffeine-L mean (50 seeds) | **0.8274** |

Caffeine self-similarity is **−1.06 σ BELOW random mean**. Glucose gives HIGHER similarity than caffeine itself. The eigval-density-histogram cosine-similarity methodology does not discriminate at n=14 substrate size — too few eigenvalues, histogram becomes effectively flat for any reasonable distribution.

**Class L instantiates trivially** (every graph has a Laplacian eigenbasis — spectral theorem); the cross-substrate FFT-matching CLAIM is falsified. This is exactly the discipline `[[feedback_no_privileged_primitive_classes]]` wants — methodology breakdown caught by controls before promotion to result.

### §3.3 Cascade-β = d_S/(d_S+2) — ABSENT (with caveat)

On caffeine molecular graph: predicted β=0.497, empirical β=0.817 (Δβ=+0.32, outside ±0.05 tolerance, r²=0.987 of stretched-exp fit). Δα=−0.167 on the power-law primary side.

**Caveat**: Spike #31 documents that Weyl-fit quality below n~100 is poor; n=14 is in the unreliable regime. This is **not a clean falsifier**; it's substrate-too-small-to-test.

Side observation worth flagging for `[[user_stance_fractal_shadow]]`: mass-spec intensity rank-distribution shows Zipf-like power law (slope −1.83, r²=0.95). Heavy-tail, but not cascade-β. Power-law-in-rank is a different shape from cascade-stretched-exp-in-time.

### §3.4 Information-instrument identity — APPLIES at 12/14 by binding-level assignment

Cataloguing the 14 classes against caffeine substrate properties (NOT spectral measurements):

| Class | Information-instrument identity | Caffeine binding-level instantiation? |
|---|---|---|
| A | channel-fingerprint / collision-resistant identifier | YES — InChI hash `RYYVLZVUVIJVGH-UHFFFAOYSA-N` |
| B | source-frame / addressable-symbol-layout | YES — Hill TLV `C8H10N4O2` |
| C | channel-input-source / time-indexed-stream | YES — fragmentation cascade as streaming |
| D | decision-tree-routing / branch-coding | YES — ionization-mode dispatch (EI vs ESI) |
| E | dictionary / stored-symbol-table | YES — NIST library lookup |
| F | variable-binding / source-expansion | YES — xanthine scaffold + methyl-substitution slots |
| G | sub-stream-search / compression-primitive | YES — library-search by sub-pattern |
| H | channel-state-metadata / self-reflective-info | **NO** — molecules are objects, not agents |
| I | group-structured-alphabet / symmetric-channel-primitive | YES — purine ring = cyclic group |
| J | alphabet-decomposition / period-bound-primitive | YES — atom-count multiset |
| K | discrete-to-continuous projection / cascade-shadow | tested in §3.1; ABSENT |
| L | channel-eigenbasis / spectral-capacity-primitive | YES — molecular graph (existence-level only; §3.2 falsifier) |
| M | distributed-representation / VSA-channel-coding | YES — ECFP fingerprint |
| N | rate-distortion-primitive / best-rational-approximation | YES — isotope-ratio rational approximation |

Per Spike #37's substrate-portability table (silicon / bronze / biological / optical), this is consistent — molecular substrate is a fifth row, with 12/14 classes admitting binding-level identifications and class H exempt (objecthood). **NOT a falsifiable spectral measurement**, just a cataloguing claim. Reinforces `[[user_stance_information_instrument_form_function_bound]]` at the binding level.

## §4 Framework-boundary characterisation

What's specifically different about molecular substrate that produces the FAIL-at-spectral-shape result:

1. **Scale**: n=14 heavy atoms vs n=10²–10⁴ in cosmic / mechanical / fractal substrates the SM was developed on. Cascade-β methodology needs n>100 reliably; eigval-density-histogram cosine-similarity becomes degenerate at n~14.
2. **Topology**: caffeine = fused bicyclic ring + 3 pendant methyls + 2 pendant oxygens. The cyclic-group structure (Class I row of Spike #37, "U(1) gauge phase / benzene D₆h") lives in **aromatic-ring electron density**, not in the fragmentation m/z grid. The ring is in the substrate; the spectrum is in the chemistry-of-cleavage layer above.
3. **Spectrum domain**: m/z is integer-valued on a uniform grid; FFT extracts no Kepler-shape because fragments are bond-cleavage products (McLafferty rearrangement / α-cleavage / charge migration), not eccentric-orbit projections.
4. **Noise model**: mass-spec intensity noise is shot-noise / ion-count Poisson / instrument-tail — not the loop-down decay envelope cascade-β is designed for.

Caffeine chemistry is governed by bond-dissociation energetics + McLafferty rearrangement + charge migration on purine-with-pendants. **Not** Kepler / pin-slot / cascade / cyclic-group spectral signatures at the FFT-match level.

## §5 If/when molecular-modeling catalog becomes scope

A molecular-modeling catalog WOULD have its own signatures — NOT a transplant of the cosmic/mechanical SM. Candidate-Spike #39 framing:

- **Vibrational normal modes** via reduced Hessian (IR/Raman spectroscopy-canonical) — Class L on a different operator
- **ECFP hyperdimensional fingerprints** (Class M; canonical cheminformatics; already in Spike #37 Class M row)
- **McLafferty rearrangement enumeration** (Class C streaming iteration; each cleavage rule = streaming step)
- **Isotope-ratio rational approximation** (Class N; Stadler-Beynon-style 12C/13C prediction)

Status: **NOT YET; user-call required.** This spike's result is *"if you want this, build it fresh, don't transplant."*

## §6 Anomalies investigated

1. **Initial 0.81 cosine-similarity appeared positive.** Falsifier controls (50 random-graph seeds, 50 random-mass-spec seeds, glucose / benzene / ethane / path / cycle controls) demoted it to artifact. The eigval-density-histogram methodology breaks down at n~14 substrate size — too few eigenvalues, histogram becomes effectively flat for any reasonable distribution. **Real structural finding** — methodology limit, not framework limit.
2. **MoNA REST API became auth-gated** post-prior session — MassBank EU API is the working academic-open ingress for caffeine.
3. **NIST WebBook spectra remain not-downloadable** by deliberate licensing (different from TOS-prohibited; just data-not-served-as-API). MassBank EU CC BY-NC-SA records are the working path.

## §7 Open extensions / fermatas for conductor

1. **Should this become a srmech notebook §X dedicated-updates entry?** Default: **no** — this is research-spike-finding, not framework-affecting. The 14-class vocabulary and substrate-portability stances stand. Could be referenced as a falsifier-style negative example in cross-domain scope statements.
2. **Does this falsifier deserve canonical-stance authoring?** Candidate stance: *"spectral-SM does not generalise to molecular-spec-mass FFT shape; molecular substrate is form-function-bound at binding level only, NOT at substrate-shape FFT-match level."* Conductor lean: **no new stance** — this is empirical confirmation that `[[user_stance_kepler_shape_universal]]` and `[[user_stance_information_instrument_form_function_bound]]` are correctly bounded (K honest-absent where Kepler-shape isn't, information-instrument applies at binding level). The framework correctly says "no" when no signature is present; that's good behaviour, not a new stance.
3. **Spike #39 molecular-modeling-catalog?** Awaits user direction. Not implied by this spike's result; this spike's result says *"build fresh, don't transplant."*

## §8 Citation provenance

- **MassBank EU** caffeine record `MSBNK-Fac_Eng_Univ_Tokyo-JP003477`: full record verified at API level (accession + license + authors + instrument + ionization energy + ChemOnt classification + InChI + SMILES + 58 peak triples + SPLASH hash). Fixture committed at `spike_38_caffeine_JP003477.json`.
- **NIST WebBook** caffeine entry ID C58082: verified to exist; spectrum data declined-licensed.
- **McLafferty 1980** *Interpretation of Mass Spectra* / Fitch 2000: cited as canonical SSoT for the bond-cleavage / rearrangement framework in §4 — NOT independently PDF-extracted within spike scope; flagged honestly per `[[feedback_pdf_extraction_citation_discipline]]`.
- **MoNA REST API** 401-auth-gated: observation only, no claim made.

## §9 Discipline guards honoured

- `[[user_stance_kepler_shape_universal]]` — K's absence is honest, not framework failure
- `[[user_stance_information_instrument_form_function_bound]]` — binding-level overlay applies at 12/14 (consistent with Spike #37)
- `[[user_stance_partition_for_understanding]]` — molecular substrate is NOT a new spectral partition; COULD become a binding-level partition with future Spike #39
- `[[feedback_science_is_ssot_not_project]]` — MassBank EU as academic SSoT; McLafferty rearrangement cited as canonical mass-spec literature reference
- `[[feedback_pdf_extraction_citation_discipline]]` — MassBank API ingress verified (accession / license / author / instrument / ionization / SPLASH); McLafferty cited but not PDF-extracted (flagged honestly)
- `[[reference_autonomous_validation_tos_landscape]]` — MassBank EU CC BY-NC-SA, permitted; commercial publisher access avoided
- `[[feedback_ndjson_over_bloated_json]]` — NDJSON outputs throughout (3 NDJSON files, no bloated JSON)
- `[[feedback_concertmaster_md_writes]]` + `[[feedback_concertmaster_git_worktree_isolation]]` — concertmaster reported inline; conductor captured-and-saved; no git operations performed by agent
- `[[feedback_no_privileged_primitive_classes]]` — molecular-modeling candidate is a NEW partition at binding level (Spike #39 candidate), NOT a 15th class
- `[[user_stance_string_theory_instrument_first]]` — instrument-first; no claims about "what molecules are" beyond what FFT + Laplacian extraction directly measures

## §10 Artifacts

- [`spike_38_caffeine_sm_fft.py`](spike_38_caffeine_sm_fft.py) — primary analysis script (Steps 2-3-4: Class K Kepler-ladder test + Class L eigval-density FFT-match + cascade-β fit + information-instrument cataloguing)
- [`spike_38_falsifier_controls.py`](spike_38_falsifier_controls.py) — falsifier controls (50 random-graph seeds + 50 random-mass-spec seeds + 5 molecular controls)
- [`spike_38_synthesis.py`](spike_38_synthesis.py) — final synthesis (overall verdict + framework-boundary characterisation + fermatas)
- [`spike_38_caffeine_JP003477.json`](spike_38_caffeine_JP003477.json) — raw MassBank EU record fixture (4.8 KB; full provenance)
- [`spike_38_records_2026-05-17.ndjson`](spike_38_records_2026-05-17.ndjson) — primary analysis NDJSON (9 records)
- [`spike_38_falsifier_records_2026-05-17.ndjson`](spike_38_falsifier_records_2026-05-17.ndjson) — falsifier NDJSON (9 records)
- [`spike_38_synthesis_records_2026-05-17.ndjson`](spike_38_synthesis_records_2026-05-17.ndjson) — final synthesis NDJSON (3 records)

---

*End of spike artifact.*
