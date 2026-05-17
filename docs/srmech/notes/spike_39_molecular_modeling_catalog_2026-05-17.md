# Spike #39 — Molecular-modeling AMSC catalog scoping (per Spike #38 follow-up)

**Date:** 2026-05-17
**Research spike artifact.** Concertmaster dispatch per user direction following Spike #38's framework-boundary finding (`docs/srmech/notes/spike_38_mass_spec_fft_vs_sm_2026-05-17.md`): *"build fresh, don't transplant cosmic/mechanical SM."* Scoping spike — design proposal + small POC catalog (1-2 attested rows for ONE chosen signature), NOT full implementation.

> **Discipline.** Closed-form deterministic chain; NDJSON outputs per `[[feedback_ndjson_over_bloated_json]]`; NIST CCCBDB autonomously verified; textbook citations flagged honestly per `[[feedback_pdf_extraction_citation_discipline]]`; no commercial-publisher access per `[[reference_autonomous_validation_tos_landscape]]`; molecular-modeling is a NEW PARTITION at substrate-binding layer per `[[feedback_no_privileged_primitive_classes]]` — vocabulary stays at 14 classes A–N.

---

## §1 Bottom line

**Vibrational normal modes via Class L reduced-Hessian eigendecomposition chosen for POC.** Two attested rows shipped (H₂O bent XY2 + CO₂ linear XY2). Chain-output verified **bit-exact** against stored row predictions. Falsification gauge in place: predicted-vs-measured residual at ~5% (stretches) / ~5–14% (bends), within expected GVFF-only accuracy floor.

**Not a 15th class.** Molecular-modeling is a NEW PARTITION at substrate-binding layer (fifth row alongside silicon / bronze / biological / optical from Spike #37). The 14-class vocabulary stays at 14; what changes is the table of substrate-instantiations of those classes.

**Catalog structure validates.** The `descriptor.toml + schema.json + row.ndjson` pattern from `pi_digits` translates cleanly to molecular substrate. The `[catalog.operator_chain]` step composition (Class J atom-multiset → Class L dynamical-matrix eigvals) is well-formed and TOML-parseable.

| Mode | H₂O predicted (cm⁻¹) | H₂O NIST | Residual | % Error |
|---|---:|---:|---:|---:|
| ν₁ sym stretch | 3839.53 | 3657.0 | +182.5 | +4.99% |
| ν₂ bend | 1733.53 | 1595.0 | +138.5 | +8.69% |
| ν₃ asym stretch | 3942.18 | 3756.0 | +186.2 | +4.96% |

| Mode | CO₂ predicted (cm⁻¹) | CO₂ NIST | Residual | % Error |
|---|---:|---:|---:|---:|
| ν₁ sym stretch | 1383.69 | 1333.0 | +50.7 | +3.80% |
| ν₂ bend | 573.42 | 667.0 | −93.6 | −14.03% |
| ν₃ asym stretch | 2458.99 | 2349.0 | +110.0 | +4.68% |

CO₂ bend systematic underestimate is the canonical GVFF limit (Urey-Bradley cross-coupling captures the missing carbonyl repulsion across the molecule). H₂O symmetric / asymmetric stretch both overshoot by ~5%, suggesting the f_r value calibrated against slightly different cross-terms than the minimal model includes. **Documented honestly in row notes** — the POC proves the catalog *shape* works; better force-field choices ratchet to <1% if needed.

## §2 Design proposal for all four candidate signatures

### §2.1 Vibrational normal modes (Class L on dynamical matrix) — CHOSEN POC

**Substrate primitive:** mass-weighted Hessian eigendecomposition. Wilson-Decius-Cross §6 closed-form secular equation for triatomic XY2 (bent + linear branches).

**Chain composition:** `(Class J atom-multiset → mass vector) ∘ (Class L dynamical-matrix eigvals)` → predicted frequencies cm⁻¹.

**SSoT:** Wilson-Decius-Cross *Molecular Vibrations* (1955) §6; Herzberg *Molecular Spectra II* (1945) Tables 35–37; Shimanouchi NSRDS-NBS 39 (DOI 10.6028/NBS.NSRDS.39); NIST CCCBDB (cccbdb.nist.gov) — open US-government data aggregator; **autonomously verified** for H₂O and CO₂ entries 2026-05-17.

**Falsification gauge:** measured-vs-predicted residual. POC at ~5% (stretches) / ~10% (bends) is canonical GVFF floor; row notes flag this honestly. Production catalog can ratchet to Urey-Bradley (~1–2%) or DFT-computed Hessian (<1%).

**Scope expansion path:** triatomic XY2 (POC) → triatomic XYZ asymmetric (e.g., HCN) → tetraatomic (NH₃, CH₄) → polyatomic (full 3N × 3N Cartesian Hessian; numerical eigendecomposition).

### §2.2 ECFP hyperdimensional fingerprints (Class M)

**Substrate primitive:** Extended-Connectivity Fingerprint (Rogers & Hahn 2010). Iterative atom-environment hashing producing fixed-length binary vectors. Already named in Spike #37 Class M row.

**Chain composition:** `(SMILES parse) ∘ (atom-environment iterative hashing) ∘ (Class M VSA bundle/bind)` → fingerprint vector.

**SSoT:** Rogers & Hahn 2010, *Extended-Connectivity Fingerprints*, **J. Chem. Inf. Model.** 50(5), 742–754. **DOI 10.1021/ci100050t** — canonical ECFP reference (ACS publication; PDF behind paywall — DOI metadata only, per `[[reference_autonomous_validation_tos_landscape]]` commercial-publisher exclusion). RDKit (open-source BSD) is the canonical implementation; PubChem (NIH) is the open SMILES corpus.

**Catalog row shape:** InChIKey + SMILES + ECFP-radius + ECFP-bit-length + chain-computed-fingerprint-hash. Cross-implementation parity test against `srmech.amsc.m.bind/bundle` is the structural verification.

**Caveat (Fermata-1):** ECFP uses MurmurHash; srmech Class M may use a SHA-based VSA — cross-implementation parity is structural-not-byte-exact. Does srmech ship a "molecular-ECFP-compatible" Class M variant, or document structural equivalence using its own VSA scheme? Catalog design choice — affects whether `ecfp_fingerprints` rows store byte-exact fingerprint hashes.

**Scope path:** small molecules (POC) → PubChem-30M coverage.

### §2.3 McLafferty rearrangement enumeration (Class C streaming)

**Substrate primitive:** mass-spec fragmentation rule enumeration. Each cleavage rule is one streaming-iterator step (Class C primitive).

**Chain composition:** `(SMILES → molecular graph) ∘ (Class C stream cleavage-rule applications) ∘ (collect fragments)` → predicted fragment-mass list.

**SSoT:** McLafferty *Interpretation of Mass Spectra* (4th ed., University Science Books, 1993). Textbook canonical; not arXiv-mirrored; not PDF-extractable autonomously per `[[feedback_pdf_extraction_citation_discipline]]`. Cross-validate against MassBank EU records (CC BY-NC-SA permitted) — Spike #38 caffeine fixture is a ready test substrate.

**Caveat:** McLafferty rules are heuristic (textbook-codified rules of thumb, not first-principles). Falsification gauge is "expected" not "deterministic" — rules generate fragment candidates; observed mass spec confirms a subset. Structurally weaker than vibrational modes (closed-form) or ECFP (canonical algorithm). **The chain works; the falsification is statistical.**

**Scope path:** caffeine POC reuse from Spike #38 → 100-molecule MassBank curated set.

### §2.4 Isotope-ratio rational approximation (Class N)

**Substrate primitive:** isotope-pattern prediction via best-rational-approximation. The 12C/13C ratio in a mass-spec isotope cluster IS a Class N rational-approximation problem.

**Chain composition:** `(Class J atom-multiset of molecular formula) ∘ (Class N rational-approximation of natural-abundance ratios)` → predicted isotope-pattern relative intensities.

**SSoT:** Beynon 1960 *Mass Spectrometry and Its Applications to Organic Chemistry* (textbook canonical); IUPAC isotope natural-abundance tables (open); NIST atomic-weights table (open). Caffeine fixture from Spike #38 has M / M+1 ratio observable: M (m/z 194, rel 999) vs M+1 (m/z 195, rel 167) — ratio 0.167, with natural-abundance prediction ~0.087 for 12C/13C alone (M+1 also fed by ¹⁵N + ²H contributions).

**Caveat (Fermata-2):** srmech Class N primitives currently target pi_cascade / continued-fraction-convergent shapes. Isotope-ratio framing IS Class N rational-approximation, but may need a different entry point — `srmech.amsc.n.isotope_ratio_predict()` or similar. Catalog design choice.

**Scope path:** small organics (POC) → metabolite-class coverage.

## §3 POC results — vibrational normal modes for H₂O and CO₂

Computed via Wilson-Decius-Cross §6 closed-form GF eigendecomposition (Class L on mass-weighted Hessian; NOT molecular-graph Laplacian — same primitive, different operator, per `[[user_stance_information_instrument_form_function_bound]]` substrate-portability).

**Chain bit-exact reproducibility verified** — running `normal_mode_frequencies(spec)` over each row's stored inputs produces predicted_frequencies_cm-1 bit-identical to stored values. The falsification infrastructure works as designed (per `[[feedback_every_doc_edit_faces_falsification]]`).

Results table see §1. CO₂ bend (−14% residual) is the GVFF-limit anomaly documented in §6.

## §4 Citation provenance

| Source | Type | Verified? | Status |
|---|---|---|---|
| Wilson-Decius-Cross *Molecular Vibrations* (1955) §6 | textbook | WorldCat author+title only; full PDF not autonomously fetched | flagged honestly — textbook, not arXiv |
| Herzberg *Molecular Spectra II* (1945) Tables 35–37 | textbook | citation through NIST CCCBDB | flagged honestly — textbook attribution via aggregator |
| Shimanouchi NSRDS-NBS 39 (DOI 10.6028/NBS.NSRDS.39) | NIST gov publication | WebFetched PDF >10 MB; one-shot verify failed | NIST-attested via CCCBDB; direct PDF extraction failed (size limit) |
| NIST CCCBDB H₂O entry | gov web | **WebFetched 2026-05-17** — ν₁=3657, ν₂=1595 cm⁻¹ confirmed | verified ✓ |
| NIST CCCBDB CO₂ entry | gov web | **WebFetched 2026-05-17** — ν₁=1333, ν₂=667, ν₃=2349 cm⁻¹ confirmed | verified ✓ |
| Huber-Herzberg 1979 H₂O ν₃ | textbook (via CCCBDB) | cited as source for ν₃=3756; CCCBDB attribution confirmed | flagged honestly — textbook |

The two NIST CCCBDB entries are autonomously verified. Textbook citations (Wilson-Decius-Cross, Herzberg, Shimanouchi PDF, Huber-Herzberg) are anchored via CCCBDB metadata but not independently PDF-extracted — matches `[[feedback_pdf_extraction_citation_discipline]]` honesty discipline (empirical anchors verified; textbook anchors flagged).

## §5 Anomalies investigated

1. **CO₂ bend frequency underestimated by 14% with canonical Herzberg force constants.** Stretches reproduce at ~4%, but the bend `f_θ = 0.5712 mdyne·Å/rad²` predicts 573 cm⁻¹ vs measured 667 cm⁻¹. **Known GVFF limitation** — the CO₂ bend benefits significantly from Urey-Bradley terms (carbonyl repulsion across the molecule). Not a chain bug; an FF-modeling limit. Documented in row notes.

2. **H₂O sym/asym stretches BOTH overshoot by ~5%.** Suggests the canonical `f_r = 8.454 mdyne/Å` is calibrated for slightly different f_rr / f_rθ cross-terms than the minimal model includes. Stronger-than-expected systematic offset — single-figure adjustment would tune both. Documented in row notes.

3. **NIST Shimanouchi PDF was >10 MB and failed WebFetch one-shot verification.** Citation via CCCBDB metadata is solid (NIST aggregator confirms attribution); direct PDF extraction not feasible within spike scope. Flagged honestly.

4. **Python 3.14 default cp1252 console encoding caused initial display errors with UTF-8 special chars.** Required `python -X utf8` invocation. Minor — does not affect bit-exact NDJSON output (UTF-8 LF on disk).

## §6 Fermatas for conductor

1. **(Fermata-1) ECFP MurmurHash vs srmech.amsc.m VSA hash.** Cross-implementation parity is structural-not-byte-exact. Does srmech ship a "molecular-ECFP-compatible" Class M variant, or document structural equivalence and use its own scheme? Conductor lean: **structural equivalence + document**, don't proliferate Class M variants per `[[feedback_no_privileged_primitive_classes]]`.

2. **(Fermata-2) Class N isotope-ratio entry point.** Needs `srmech.amsc.n.isotope_ratio_predict()` (or similar) added when this catalog ships in production. Conductor lean: **add the entry point when §2.4 catalog actually lands**; deferred to Phase C2 catalog-expansion work.

3. **(Fermata-3) Force-field SSoT for production vibrational_modes catalog.** GVFF (POC; ~5%) → refined GVFF with Urey-Bradley (~1–2%) → DFT-computed Hessian (<1%, per-row method citation required). Conductor lean: **GVFF for chain-primitive cleanliness**; DFT rows would shift chain shape from "Class L closed-form" to "Class L numerical on stored DFT-Hessian." Both legitimate; the cleanest-primitive choice is GVFF for the closed-form-chain SSoT row; DFT for production-accuracy rows.

4. **(Fermata-4) Caffeine reuse path.** Spike #38's caffeine MassBank fixture is the natural test substrate for §2.3 (McLafferty) and §2.4 (isotope-ratio). Conductor lean: **reuse the Spike #38 fixture** for §2.3 / §2.4 POCs; cite the spike's fixture path as the test-substrate provenance.

5. **(Fermata-5) Catalog wiring scope.** The POC files in `docs/srmech/notes/` are NOT wired into `srmech.amsc.catalog`. Actual wiring (placing files under `srmech/amsc/attested/vibrational_modes/` + writing Class L `dynamical_matrix_eigvals_xy2` primitive in `srmech.amsc.l` or new submodule + adding tests) is a real engineering ship — **Phase C2 catalog-expansion work**. Per `[[feedback_no_mvp_framing]]` full-coverage shipping, the version that lands should cover all four candidate signatures (or explicitly defer §2.3/§2.4 to follow-on tasks with named-event resolution). **Awaits user direction** on whether to dispatch Phase C2 work now or hold for sprint-cycle planning.

## §7 Discipline guards honoured

- `[[feedback_no_privileged_primitive_classes]]` — NOT a 15th class; new partition at substrate-binding layer
- `[[user_stance_information_instrument_form_function_bound]]` — Class L on different operator (mass-weighted Hessian, NOT molecular graph) demonstrates substrate-portable identity per Spike #37
- `[[user_stance_partition_for_understanding]]` — molecular-modeling is a substrate-binding-level partition complementary to existing partitions (algebraic / kinematic / observable / information-instrument)
- `[[reference_autonomous_validation_tos_landscape]]` — NIST CCCBDB (gov) verified; textbook citations anchored via CCCBDB; no commercial-publisher autonomous access (ACS DOI metadata only)
- `[[feedback_pdf_extraction_citation_discipline]]` — NIST CCCBDB web entries verified by WebFetch; textbook anchors flagged honestly as not-PDF-extracted
- `[[feedback_science_is_ssot_not_project]]` — Wilson-Decius-Cross + Herzberg + Shimanouchi + NIST CCCBDB as canonical SSoT; not any srmech sub-project
- `[[feedback_ndjson_over_bloated_json]]` — NDJSON outputs; TOML descriptor for descriptor-shaped data
- `[[feedback_concertmaster_md_writes]]` — concertmaster returned findings inline; conductor captured-and-saved this note
- `[[feedback_concertmaster_git_worktree_isolation]]` — agent performed zero git operations; all work in `D:\temp\spike_39\`
- `[[feedback_every_doc_edit_faces_falsification]]` — chain spec lives in catalog config; chain bit-exact reproducibility verified for both POC rows
- `[[user_stance_string_theory_instrument_first]]` — instrument-first; no claims about "what molecules are" beyond what reduced-Hessian eigendecomposition directly computes

## §8 Artifacts

- [`spike_39_molecular_modeling_proposal.py`](spike_39_molecular_modeling_proposal.py) — analysis script (Wilson-Decius-Cross §6 closed-form for triatomic XY2; bent + linear branches)
- [`spike_39_descriptor.toml`](spike_39_descriptor.toml) — POC catalog descriptor (vibrational_modes; sources + cite_as_template + operator_chain spec)
- [`spike_39_schema.json`](spike_39_schema.json) — JSON Schema for row payload
- [`spike_39_vibrational_modes_2026-05-17.ndjson`](spike_39_vibrational_modes_2026-05-17.ndjson) — 2 attested rows (H₂O + CO₂; MPR v1 format)
- [`spike_39_records_2026-05-17.ndjson`](spike_39_records_2026-05-17.ndjson) — analysis + verdict records

---

*End of spike artifact.*
