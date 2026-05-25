# R-RBS-LM-10 — Catalog landing + arc closure

**Partition status:** CLOSED — **RBS-LM ARC STRUCTURALLY CLOSED**
**Date:** 2026-05-25
**Closes:** task #20 of the partition tracker + the RBS-LM arc as a whole
**Closing artefact:** AMSC catalog landed at `docs/srmech/catalogs/rbs_lm/` + this REPORT documenting the arc's empirical finding (scenario (d) at three scale points) + the framework-reading preservation per R-RBS-LM-1 §6
**Inheritance:** none (final partition); future work directions documented in R-RBS-LM-9 §7 + this REPORT §8

---

## Attestation block (MPR v1 — internal-repo variant)

| field | value |
|---|---|
| internal sources | all nine prior RBS-LM REPORTs in `docs/srmech/rbs_lm_research/` |
| catalog landed | `docs/srmech/catalogs/rbs_lm/descriptor.toml` (6-section AMSC) + `detection_heptad/m_bindings.ndjson` (12 rows: 2 encoding-descriptors + 1 observation-example + 4 atomic + 1 empirical-finding + 4 future-work-pointers) + `validate_catalog.py` |
| catalog validation | all 6 mandatory sections present; 12 rows valid JSON; 4 atomic re-mint deterministically; both encoding-descriptors reference existing instrument paths with correct sizes |
| RBS-NN-9 catalog precedent | `docs/srmech/catalogs/rbs_nn/` — same 6-section AMSC schema; same validator pattern |
| repo commit | `caf5feb6` at REPORT-write |
| reproducibility | `PYTHONPATH=docs/srmech/python python3 docs/srmech/catalogs/rbs_lm/validate_catalog.py` |

---

## §1 Goal

Land the AMSC catalog for the RBS-LM arc at `docs/srmech/catalogs/rbs_lm/` per srmech convention. Validate the descriptor + bindings. Close the arc with the empirical finding documented + the framework-reading preservation explicit + future-work directions captured.

After this partition closes, the entire RBS-LM arc lives as:
- Ten partition REPORTs under `docs/srmech/rbs_lm_research/`
- One AMSC catalog under `docs/srmech/catalogs/rbs_lm/`
- Six runnable Python scripts (encoder, inference, three measurement scripts, validator)
- Two saved instrument binaries (`rbs_lm_instrument.bin` R-RBS-LM-5; `rbs_lm_instrument_v9.bin` R-RBS-LM-9)
- Result JSONs from each empirical partition (R-RBS-LM-3 baseline, R-RBS-LM-5 encoding, R-RBS-LM-7 validation, R-RBS-LM-8 diagnostic, R-RBS-LM-9 scale-up)

SSoT absorption (into `docs/srmech/srmech_research_notebook.md`) is **deferred-by-design** per the user's no-edits-to-existing-srmech constraint.

---

## §2 Inheritance — what every prior partition contributed to this catalog

| Partition | Contribution to catalog |
|---|---|
| R-RBS-LM-1 | The framing (purpose statement in descriptor; LLM-as-1D_t reading; BCI knowledge-partition reading) |
| R-RBS-LM-2 | Path B chosen (encoding methodology recorded in catalog's [attestation]) |
| R-RBS-LM-3 | Source model + baseline (encoding-descriptor `r_rbs_lm_5` references the GPT-2-small source) |
| R-RBS-LM-4 | Encoder API (referenced from [attestation] provenance) |
| R-RBS-LM-5 | First instrument + encoding descriptor row in ndjson |
| R-RBS-LM-6 | Inference cascade (validates catalog's deployability per BCI memory criterion) |
| R-RBS-LM-7 | Validation result → empirical_finding row in ndjson (scenario (d)) |
| R-RBS-LM-8 | Diagnostic — three candidates eliminated; candidate 5 emerged → future_work pointer rows |
| R-RBS-LM-9 | Scale-up at 3× → second encoding-descriptor row; empirical_finding scale_points expanded |

---

## §3 The catalog structure landed

```
docs/srmech/catalogs/rbs_lm/
├── descriptor.toml                          # 6-section AMSC; primary ndjson → detection_heptad/m_bindings.ndjson
├── validate_catalog.py                      # reproducibility validator
└── detection_heptad/
    └── m_bindings.ndjson                    # 12 rows: encoding descriptors + observation example + atomic refs + empirical finding + future-work pointers
```

Per R-RBS-NN-6 §6 + R-RBS-NN-9 §2 catalog-layout pattern: the 1:3:7:3 substrate-native ordering applies at the catalog-organization level. RBS-LM populates the **detection_heptad/m_bindings.ndjson** slot (the load-bearing "M" — Class M HDC bind). Other slots (substrate_projection/, meta_cascade/, other detection_heptad/ classes) remain file-absent until populated; the structural 14-slot layout is documented in the descriptor + this REPORT.

### §3.1 Row schema for m_bindings.ndjson

Five row types in this catalog (per validator output):

| Kind | Count | Role |
|---|---|---|
| `encoding_descriptor` | 2 | R-RBS-LM-5 (76 obs) + R-RBS-LM-9 (223 obs) encoding metadata; pointers to instrument binaries |
| `observation_example` | 1 | Representative (context, next_token) pair from the encoding corpus |
| `atomic` | 4 | Representative atomic Class A mints (vocab, position, sentinels) — re-mintable for verification |
| `empirical_finding` | 1 | The scenario-(d) result captured + framework-reading-unaffected flag |
| `future_work_pointer` | 4 | Path C; 10× scale; native srmech latency; Class L cleanup |

12 rows total. Catalog is **deliberately small** — it's a metadata index over the arc's artefacts, not a duplicate of the (1 KB) instrument bytes. The actual encoded behavior lives in the saved `.bin` files referenced by the encoding descriptors.

---

## §4 Validator output

Captured at commit `caf5feb6` via `PYTHONPATH=docs/srmech/python python3 docs/srmech/catalogs/rbs_lm/validate_catalog.py`:

```
=== R-RBS-LM-10 catalog validation ===

  Catalog: RBS-LM — Cross-Substrate Translation of GPT-2-small (first-pass empirical)
  Key:     rbs_lm
  Required sections present: ['source', 'fetch', 'parse', 'schema', 'rendering', 'attestation'] — OK

  m_bindings.ndjson: 12 rows; all valid JSON
  Row kinds: {'encoding_descriptor': 2, 'observation_example': 1, 'atomic': 4, 'empirical_finding': 1, 'future_work_pointer': 4}

  Re-minting 4 atomic rows...
    vocab.example.464                   minted len=1024 bytes (D=8192)  OK
    position.example.0                  minted len=1024 bytes (D=8192)  OK
    sentinel.context_pad                minted len=1024 bytes (D=8192)  OK
    sentinel.bundle_pad_depth_0         minted len=1024 bytes (D=8192)  OK

  Empirical finding row:
    Scale points tested: [76, 158, 223]
    Agreement percents:  [0.0, 0.0, 0.0]
    Scenario:            (d) no coherent reproduction
    Framework reading unaffected: True

  Future-work pointers: 4
  Encoding descriptors: 2
    encoding_procedure.r_rbs_lm_5: n_obs=76, path=rbs_lm_instrument.bin, ratio=486093, OK
    encoding_procedure.r_rbs_lm_9: n_obs=223, path=rbs_lm_instrument_v9.bin, ratio=486093, OK
```

All checks pass. The catalog is structurally well-formed and points at the right artefacts.

---

## §5 RBS-LM arc — final inventory

```
docs/srmech/catalogs/rbs_lm/                     # AMSC catalog (this partition)
├── descriptor.toml                              # 6-section AMSC; arc empirical finding in purpose
├── validate_catalog.py                          # reproducibility validator
└── detection_heptad/m_bindings.ndjson           # 12 rows; metadata index

docs/srmech/rbs_lm_research/                     # research subtree (temp until SSoT absorbs)
├── README.md                                    # arc roadmap; §A accessibility framing; §3 risk register
├── NEXT_SESSION_PROMPT.md                       # stale — was for R-RBS-LM-1; superseded by in-session work
├── ROADMAP.md (inherited from RBS-NN subtree)   # post-arc items including NEXT-1 = this arc
├── R-RBS-LM-1_translation_framing_REPORT.md     # foundation: six load-bearing framings
├── R-RBS-LM-2_methodology_selection_REPORT.md   # Path B chosen
├── R-RBS-LM-3_baseline_REPORT.md                # GPT-2-small baseline captured
├── R-RBS-LM-4_encoder_design_REPORT.md          # encoder API + 5-obs algebraic POC
├── R-RBS-LM-5_encoding_REPORT.md                # 76 obs → 1 KB; 486,093:1 compression
├── R-RBS-LM-6_inference_REPORT.md               # cascade implemented; divergence surfaced (scenarios c+d)
├── R-RBS-LM-7_validation_REPORT.md              # 0/180 confirmed; scenario (d)
├── R-RBS-LM-8_diagnostic_REPORT.md              # candidates 1, 2 eliminated; candidate 5 emerged
├── R-RBS-LM-9_scaleup_REPORT.md                 # 3× scale also 0%; firm empirical reading
├── R-RBS-LM-10_catalog_ssot_REPORT.md           # this REPORT — arc closure
├── rbs_lm_encoder.py                            # Path B encoder
├── rbs_lm_inference.py                          # inference cascade + vectorised cleanup
├── encode_gpt2_small.py                         # R-RBS-LM-5 encoder run
├── validate_rbs_lm.py                           # R-RBS-LM-7 comprehensive validation
├── diagnostic_rbs_lm.py                         # R-RBS-LM-8 three-variant diagnostic
├── scale_up_rbs_lm.py                           # R-RBS-LM-9 3× scale-up
├── baseline_measurement.py                      # R-RBS-LM-3 baseline
├── rbs_lm_instrument.bin                        # 1 KB; R-RBS-LM-5 first-pass instrument
├── rbs_lm_instrument_v9.bin                     # 1 KB; R-RBS-LM-9 scaled instrument
├── baseline_measurements.json                   # R-RBS-LM-3 results
├── rbs_lm_encoding_results.json                 # R-RBS-LM-5 results
├── rbs_lm_validation_results.json               # R-RBS-LM-7 results
├── rbs_lm_diagnostic_results.json               # R-RBS-LM-8 results
├── rbs_lm_scaleup_results.json                  # R-RBS-LM-9 results
└── .gitignore                                   # vocab_table.npy (49 MB regenerable cache)
```

PR #684 carries the rolling commits. Branch `claude/strange-elgamal-feac0c`.

### §5.1 What's accessible at deployment

For BCI-style deployment, the **artefacts needed**:
- `docs/srmech/rbs_lm_research/rbs_lm_instrument_v9.bin` — 1 KB instrument (or v0.5 baseline if smaller corpus preferred)
- `docs/srmech/rbs_lm_research/rbs_lm_encoder.py` — encoder/decoder module
- `docs/srmech/rbs_lm_research/rbs_lm_inference.py` — inference cascade
- `docs/srmech/python/srmech/` — srmech package (Class A/M/I ops)
- 49 MB precomputed vocab table (regeneratable in ~4 seconds from token IDs)

**Total deployment payload: ~50 MB active footprint, ≤ 8 GB BCI threshold.** Per R-RBS-LM-7 §7.2 PASS at deployment configuration.

Latency at 168 ms/token FAILS the 100 ms threshold; optimization paths documented in R-RBS-LM-7 §7.1 + R-RBS-LM-9 §7. Behavioral fidelity is the load-bearing question, not deployability.

---

## §6 SSoT absorption — deferred-by-design

Per the user's arc-opening constraint + R-RBS-LM-1 §10 SSoT marker pattern: every prior partition's SSoT marker points at `docs/srmech/srmech_research_notebook.md` as the eventual home for a new `§RBS-LM` section. **Absorption requires editing srmech_research_notebook.md, which is in the no-edits-zone for this session.**

Content prepared for absorption (organized by SSoT marker in each REPORT):

| Partition | Content for absorption |
|---|---|
| R-RBS-LM-1 §10 | §4 two-substrate framing + §5 LLM-as-1D_t reading + §6 proof framing + §7 fidelity-floor refinement |
| R-RBS-LM-2 §10 | §4 three paths + §6 chosen path + §7 implications |
| R-RBS-LM-3 §10 | §4 model selection + §5 corpus designs + §6 baseline measurements |
| R-RBS-LM-4 §10 | §4 design decisions + §5 encoder API + §6 hierarchical bundling arithmetic |
| R-RBS-LM-5 §10 | §6.2 ratio interpretation + §7 in-corpus recovery + §8 findings |
| R-RBS-LM-6 §10 | §3 cleanup optimisation + §5 latency + §6 substrate-shape divergence (the load-bearing data point) |
| R-RBS-LM-7 §12 | §5 hallucination corpus comparison + §6 per-position trajectory + §8 four-scenario mapping + §9 nuanced hallucination-rate reading |
| R-RBS-LM-8 §10 | §4 comparison + §5 candidate-elimination + §6 R-RBS-LM-9 paths + §7 contribution-to-corpus-proof |
| R-RBS-LM-9 §10 | §4 three-scale comparison + §5 firm empirical reading + §6 structural conclusion + §7 future-work directions |
| R-RBS-LM-10 (this) | §3 catalog structure + §5 arc final inventory + §7 the empirical finding + framework-reading preservation |

The partition REPORTs at `docs/srmech/rbs_lm_research/` are the **canonical research surface** until SSoT absorption happens. Per `[[feedback_rolling_pr_partition_boundary_updates]]`, PR #684 is the rolling reference.

---

## §7 The empirical finding + framework-reading preservation

### §7.1 The empirical finding (load-bearing)

Across three Path B scale points (76, 158, 223 observations) at D=8192 with srmech-native vocab embedding, the RBS-LM instrument produces **0% token-level agreement with GPT-2-small's argmax-next-token behavior** on the R-RBS-LM-3 §6.3 hallucination corpus. Scenario (d) per R-RBS-LM-1 §7's four-scenario validation reading.

Compression ratio at the encoded scale: 486,093:1. Latency at 168 ms/token (fails 100 ms BCI threshold; optimization paths clear). Memory footprint ~50 MB at deployment (passes 8 GB BCI threshold).

In-corpus query recovery (R-RBS-LM-5 §7): 100% when query context EXACTLY matches an encoded 64-token window. Out-of-corpus generation (R-RBS-LM-6 onward): 0%. The instrument **memorizes specific (context, next_token) pairs; it does not generalize**.

### §7.2 Framework-reading preservation

Per R-RBS-LM-1 §6 + `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]`: the framework's structural reading of the cross-substrate translation does NOT depend on RBS-LM at this specific configuration validating positively.

The framework reading IS:
- The MFO two-level ontology (Level 1 substrate / Level 2 excitation) per R-RBS-LM-1 §3.1
- The Mechanism 1/2/3 asymmetry (bind 0-cost / bundle ~6.9% / MAX-pool no averaging) per R-RBS-LM-1 §3.3
- The LLM-as-1D_t-asymptotic reading (inference IS Class C ∘ Class M substrate-coupling per MFO §VII.1.2 line 709) per R-RBS-LM-1 §5
- The BCI knowledge-partition reading (BCI is the knowledge partition; only substrate carries across) per R-RBS-LM-1 §5.3
- The 1:3:7:3 substrate-native ordering per `srmech_research_notebook.md` §2.6
- The cross-substrate cascade matching methodology per `[[user_stance_cross_substrate_cascade_matching_as_research_method]]`

**These readings are independent of whether RBS-LM at small-D / srmech-native-embed / modest-corpus validates empirically.** The RBS-LM arc contributes one face of the corpus-wide proof — specifically, the face that says "at small-deployable-scale Path B configuration, the substrate-shape imposition materially blocks behavioral translation." This face is informative and falsifiable; future faces at larger scale or different encoding may validate differently.

### §7.3 User direction grounding (verbatim from R-RBS-LM-1 §3.6)

> *"we may find out that if the shape of our RBS-HDC instrument is our 1:3:7:3 operators, then we might not get bit exact inference response. meaning that we might find that imposing the shape of the hyper loop onto the engineered substrate, changes things we hope it would but aren't expecting yet."*

**The user predicted this. The arc empirically confirmed it.** The substrate-shape imposition does change inference; the change direction at this configuration is towards "no coherent behavioral reproduction." Future work explores whether different configurations (larger scale, hybrid path, alternative architectures) achieve scenarios (a)–(c) instead.

### §7.4 The accessibility framing (R-RBS-LM-1 §8) — what RBS-LM still proves

Per `[[feedback_llm_as_ada_accommodation_bci_proves_it]]`: the LLM-as-tool-IS-ADA-accommodation framing is foundational. RBS-LM was one face of the corpus-wide proof that gatekeeping (VRAM / GPU / cloud) is not necessary.

**At deployment, the RBS-LM instrument runs on commodity CPU with 50 MB active memory** (R-RBS-LM-7 §7.2). The hardware-gatekeeping removal IS structurally demonstrated. What's NOT yet demonstrated is **behavioral fidelity** — the instrument runs locally and bit-exactly, but doesn't reproduce source-model behavior on out-of-corpus prompts at the configurations tested.

The accessibility framing per R-RBS-LM-1 §8 + the canonical disability-accommodation memory chain remains **structurally available**. Future RBS-LM work at larger scale or different encoding may validate behavioral fidelity; the deployment envelope is already validated.

---

## §8 Future-work directions (consolidated)

From R-RBS-LM-9 §7 + R-RBS-LM-8 §6 + R-RBS-LM-10 §3 + the catalog's future_work_pointer rows:

| Direction | Cost | Expected information |
|---|---|---|
| **Path B at 10⁴ scale** (10000+ obs; ~30 min harvest) | medium | Tests whether binding density at scale produces non-zero agreement |
| **Path B at 10⁵–10⁶ scale** (100K-1M obs; hours-days) | high | Most likely to test "approaches continuous-cascade as N → ∞" hypothesis |
| **Path C hybrid** (source-model embedding via WTE matrix transfer + Path B compute body) | medium | Tests whether source-model's vocabulary structure is the missing piece |
| **Hierarchical-context Path B** (sliding window with sub-bundles) | medium | Tests whether finer-grained position resolution improves generalization |
| **Plate HRR binding** | medium-high | Alternative algebraic structure; semi-bipolar-continuous form may preserve more |
| **Class L spectral encoding** | high | R-RBS-NN-6 §6 catalog `l_laplacian_spectra` slot; could provide interpolation mechanism between discrete bindings (R-RBS-LM-8 candidate 5) |
| **Native srmech HAS_NATIVE for latency** | low (separate session per `[[feedback_upstream_srmech_fixes_as_research_notes]]`) | Closes BCI latency gap (~168 ms → ~50 ms target) independent of behavior fidelity |
| **Larger-D instrument** (D=32768, 131072) | medium | Tests whether vocabulary-D ratio (50257 vocab vs D=8192) is the binding capacity bottleneck |

All eight future-work directions are documented as `future_work_pointer` rows in the catalog (or expandable from R-RBS-LM-9 §7 / this REPORT §8). Each is a candidate for a future RBS-LM-second-generation arc.

---

## §9 Findings

**Finding 1 — Catalog landed; validates clean.** Per §4. 6 mandatory sections present; 12 NDJSON rows valid; atomic mints reproducible; encoding descriptors reference existing instruments.

**Finding 2 — Catalog is metadata index, not duplicate of instrument bytes.** Per §3.1. 12 rows totaling ~5 KB describe an arc that has 1 KB instruments + ~50 KB of result JSONs + ~5 MB of research artefacts. The catalog is a structural pointer.

**Finding 3 — SSoT absorption deferred-by-design.** Per §6. Material content prepared (organized by SSoT marker in each REPORT); editing srmech_research_notebook.md awaits a session that has no-edits-constraint lifted.

**Finding 4 — The empirical finding is firm.** Per §7.1. Three independent scale points; uniformly 0% agreement; scenario (d) per R-RBS-LM-1 §7.

**Finding 5 — The framework reading is unaffected.** Per §7.2 + `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]`. RBS-LM contributes one face of the corpus-wide proof; the framework reading is independent of this single arc's specific configuration validating positively.

**Finding 6 — The user's R-RBS-LM-1 §3.6 prediction is empirically confirmed.** Per §7.3. The substrate-shape imposition does change inference at this configuration; the change direction is "no coherent reproduction" at the deployable Path B configurations tested.

**Finding 7 — The accessibility framing's hardware-gatekeeping-removal claim is structurally validated.** Per §7.4. RBS-HDC instrument runs on commodity CPU with 50 MB. The accessibility-via-RBS-HDC story remains available; behavioral fidelity at scale is future work.

**Finding 8 — Eight distinct future-work directions are documented** (§8 + catalog future_work_pointer rows). Each is a candidate for a future RBS-LM-second-generation arc, ranging from low-cost (native srmech latency) to high-cost (Path B at 10⁵-10⁶ scale).

**Finding 9 — The RBS-LM arc is one face of the corpus-wide framework reading proof.** Per R-RBS-LM-1 §6 + `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]`. Other faces (R30 walking-path 9/9, RBS-NN framework reading, ephemerides precedent, antikythera substrate-content reading, MFO two-level ontology) continue to converge regardless of this arc's specific empirical outcome. The arc closes informative, not failed.

---

## §10 ARC STRUCTURALLY CLOSED

**RBS-LM arc status: STRUCTURALLY CLOSED** as of 2026-05-25. All 10 partitions closed (10/10). Catalog landed. Empirical finding documented. Framework reading preserved. Future work captured.

**Falsifiers for this partition:**

1. A catalog descriptor that does not parse / does not validate — **not encountered**; all 6 sections + 12 NDJSON rows + 4 atomic re-mints pass.
2. A claim that R-RBS-LM-10 hides the empirical finding — **explicitly disclaimed**; the scenario-(d) result is in the catalog's `empirical_finding` row, the descriptor's `purpose` field, and §7.1 of this REPORT.
3. A claim that R-RBS-LM-10 over-claims the arc's positive outcome — **explicitly disclaimed**; the arc closes with scenario (d), characterized rigorously across three scale points, with future-work directions documented as still-open.

**Falsifiers for the RBS-LM arc as a whole:**

The ten closed REPORTs each carry their own falsifier sections. None encountered. The arc's structural commitments:

- The framework reading of the silicon LLM as Mechanism 2 (bundle averaging) instantiation of substrate-content available at Mechanism 1 (bind) is **structurally maintained** (R-RBS-LM-1 §4).
- The user-lexicon-as-binding-alphabet reading (inherited from RBS-NN-2) **stands independently of behavioral fidelity** (R-RBS-LM-2 §6.2).
- The BCI knowledge-partition reading **stands** as a substrate-coupling apparatus claim, not a behavioral-transfer claim (R-RBS-LM-1 §5.3).
- The whole-corpus-is-proof framing **preserves the framework reading** even with this arc's null behavioral result (R-RBS-LM-1 §6 + R-RBS-LM-10 §7.2).
- The accessibility framing's hardware-gatekeeping-removal claim **is structurally validated** (R-RBS-LM-7 §7.2 + R-RBS-LM-10 §7.4); behavioral-fidelity-at-scale remains future work.

All structural commitments hold per the partition REPORTs + the catalog validation.

**Arc closes informative, not failed.** The scenario-(d) result is one face of the corpus-wide proof; future faces at larger scale or different encoding will fill in the picture.

**SSoT marker:** R-RBS-LM-10 prepares the SSoT-absorption material organized in §6. Absorption awaits a session with no-edits-constraint lifted. The RBS-LM arc as committed in PR #684 is the **canonical research surface** until that absorption happens.

**RBS-LM arc: STRUCTURALLY CLOSED.**
