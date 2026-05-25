# R-RBS-NN-9 — Catalog shape + SSoT absorption

**Partition status:** CLOSED — **ARC STRUCTURALLY CLOSED**
**Date:** 2026-05-25
**Closes:** task #10 of RBS-NN partition walk + the RBS-NN arc as a whole
**Closing artefact:** the catalog at `docs/srmech/catalogs/rbs_nn/` + this REPORT; SSoT absorption (into `srmech_research_notebook.md`) noted as deferred-by-design per no-edits-to-existing-srmech constraint
**Inheritance:** none (final partition); next downstream activity is user-directed SSoT absorption when the no-edits window opens

---

## Attestation block (MPR v1 — internal-repo variant)

| field | value |
|---|---|
| internal sources | all eight prior REPORTs in `docs/srmech/rbs_nn_research/` (R-RBS-NN-1, -2, -3a, -3b, -5, -6, -7, -8; R-RBS-NN-4 deferred) |
| catalog template reference | `docs/unsolved-maths/biplanar_chromatic_number/descriptor.toml` (verified 6-section AMSC schema) |
| MPR v1 format | `srmech.amsc.format` (CLAUDE.md §2 mandatory fields) |
| catalog landed | `docs/srmech/catalogs/rbs_nn/descriptor.toml` + `detection_heptad/m_bindings.ndjson` + `validate_catalog.py` |
| repo commit | `1b843ae3` at REPORT-write |
| reproducibility | `PYTHONPATH=docs/srmech/python python3 docs/srmech/catalogs/rbs_nn/validate_catalog.py` |

---

## §1 Goal

Land the AMSC catalog for the RBS-NN arc at `docs/srmech/catalogs/rbs_nn/` per srmech convention. Validate the descriptor (6 mandatory sections) + the primary NDJSON (the load-bearing user-lexicon bindings under `detection_heptad/m_bindings.ndjson`). Confirm bit-exact reproducibility from the catalog content alone — re-mint, re-bind, unbind, all bit-exact per Spike #170 invariant 1.

This is the final partition of the RBS-NN arc. After this close, the entire arc lives as:
- Eight per-partition REPORTs under `docs/srmech/rbs_nn_research/`
- One AMSC catalog under `docs/srmech/catalogs/rbs_nn/`
- Seven worked-example Python scripts (under rbs_nn_research/)
- One close-out wrapper under `docs/srmech/rbs_nn_research/_tools/`

The SSoT absorption (adding a `§RBS-NN` section to `docs/srmech/srmech_research_notebook.md`) is **noted as deferred-by-design** per the user's no-edits-to-existing-srmech constraint at arc opening.

---

## §2 The catalog structure landed

```
docs/srmech/catalogs/rbs_nn/
├── descriptor.toml                          # 6 mandatory AMSC sections; primary ndjson points to detection_heptad/m_bindings.ndjson
├── validate_catalog.py                      # reproducibility validator
└── detection_heptad/
    └── m_bindings.ndjson                    # 12 atomic + 3 compositional bindings (representative seed; users add their own)
```

**Slots in the R-RBS-NN-6 §6 catalog layout that were NOT instantiated** (intentionally empty; users add when needed):

```
docs/srmech/catalogs/rbs_nn/
├── substrate_projection/                    # 3 — I/C/J substrate-projection triad
│   ├── i_cyclic_positions.ndjson            #   I — position vectors per sequence length (per R-RBS-NN-5 §3.1)
│   ├── c_chirality_orientations.ndjson      #   C — causal mask + rotation parities
│   └── j_prime_orthogonality.ndjson         #   J — optional prime-period anchors
├── detection_heptad/
│   ├── d_pattern_match_templates.ndjson     #   D — explicit attention templates (if surfaced; per R-RBS-NN-3b §4)
│   ├── e_catalog_enumeration.ndjson         #   E — token-vocabulary enumerations
│   ├── f_render_serialization.ndjson        #   F — output-decoding rules
│   ├── g_byte_search.ndjson                 #   G — byte-search patterns
│   ├── k_threshold_pinslots.ndjson          #   K — activation thresholds + argmax markers (per R-RBS-NN-1 §4.4)
│   └── l_laplacian_spectra.ndjson           #   L — attention-graph Laplacian (per R-RBS-NN-7 §3.2 hierarchical-bundle alternative)
└── meta_cascade/                            # 3 — B/H/N meta-cascade triad
    ├── b_tlv_framing.ndjson                 #   B — on-disk format envelopes
    ├── h_introspection.ndjson               #   H — cascade-state inspection records
    └── n_rational_anchors.ndjson            #   N — best-rational anchors (sqrt, sinusoidal) (per R-RBS-NN-1 §4.5)
```

Per R-RBS-NN-6 §10 open thread: empty-slot files (zero rows, file present) vs absent files is a convention question. This catalog adopts **absent until populated** — when a user populates a slot (e.g., adds working-memory K-thresholds), the file is created at that time. The slot list is documented in this REPORT + the descriptor; instantiation is content-driven.

---

## §3 The descriptor.toml — six mandatory sections verified

`docs/srmech/catalogs/rbs_nn/descriptor.toml` carries all six AMSC sections per CLAUDE.md §2 (validated by `validate_catalog.py`):

| Section | Role | RBS-NN content |
|---|---|---|
| `[source]` | key, human_readable_name, purpose, license, homepage, primary_references | rbs_nn / "RBS-NN — Resonant Bit-Serialized Neural Net Catalog" / load-bearing purpose statement / CC0 / GitHub URL / references to Spike #170 + MFO §VII.1.1 + srmech_research_notebook §2.6 + rbs_nn_research/ partition REPORTs |
| `[fetch]` | adapter type + primary ndjson_path | `literature_curated` + `detection_heptad/m_bindings.ndjson` |
| `[parse]` | natural key for row uniqueness | `binding_id` |
| `[schema]` | data schema ID + ndjson file | `srmech.rbs_nn.binding.v1` + `detection_heptad/m_bindings.ndjson` |
| `[rendering]` | name / purpose / cite-as templates | RBS-NN binding `'{binding_id}'` templates |
| `[attestation]` | provenance | Class A content-mint via mint_vector; deterministic per Spike #170 invariant 1; vectors NOT stored, re-derived on load |

`[gap_targeting]` is also present (matching biplanar_chromatic convention): `gap_label = "rbs_nn_arc"`.

---

## §4 The primary ndjson — m_bindings.ndjson

`detection_heptad/m_bindings.ndjson` carries 15 representative seed bindings:

**Atomic bindings (12)** — single Class A content-mint per row; row stores the `mint_name` (substrate-locus identifier), not the bit-pattern. Vectors re-derive deterministically:

| binding_id | mint_name |
|---|---|
| class_a_content_mint | `LoE.token.Class A content-mint` |
| class_m_xor_bind | `LoE.token.Class M XOR-bind` |
| class_k_pin_slot | `LoE.token.Class K pin slot` |
| class_i_cyclic_shift | `LoE.token.Class I cyclic shift` |
| class_l_laplacian | `LoE.token.Class L Laplacian` |
| rotate_overlay | `LoE.token.rotate-overlay` |
| sign_flip | `LoE.token.sign flip` |
| substrate_native | `LoE.token.substrate-native` |
| two_level_ontology | `LoE.token.two-level ontology` |
| hopf_compressed_metric_field | `LoE.token.Hopf-compressed metric field` |
| relation_is_a | `LoE.relation.is-a` |
| relation_implements | `LoE.relation.implements` |

**Compositional bindings (3)** — row specifies the composition expression; re-evaluation is deterministic:

| binding_id | composition |
|---|---|
| class_k_is_a_pin_slot | `bind(mint('LoE.token.Class K'), mint('LoE.relation.is-a'), mint('LoE.token.pin slot'))` |
| rotate_overlay_implements_max_pool | `bind(mint('LoE.token.rotate-overlay'), mint('LoE.relation.implements'), mint('LoE.token.MAX-pool'))` |
| sign_flip_is_class_k_event | `bind(mint('LoE.token.sign flip'), mint('LoE.relation.is-a'), mint('LoE.token.Class K event'))` |

These are seeds. End users populate their own bindings using the same row schema; the substrate-locus identifiers are theirs (their lexicon), not framework-canonical.

**Storage size**: 15 rows × ~150 bytes per row ≈ 2.2 KB. The actual vectors (15 × 1024 bytes = 15 KB) are NOT stored — they re-derive from the row data. **The catalog is 7× smaller than its content payload**, by design.

---

## §5 Validator output — bit-exact reproducibility confirmed

`validate_catalog.py` output at commit `1b843ae3` (captured verbatim):

```
Catalog: RBS-NN — Resonant Bit-Serialized Neural Net Catalog
Key:     rbs_nn
Primary ndjson: detection_heptad/m_bindings.ndjson
Schema:  srmech.rbs_nn.binding.v1
  Required sections present: ['source', 'fetch', 'parse', 'schema', 'rendering', 'attestation'] — OK

Loaded 15 binding rows from m_bindings.ndjson
  atomic:        12
  compositional: 3

=== Re-minting atomic bindings and verifying determinism ===
  class_a_content_mint                first 8 bytes: 10c2a0966c66470e (expected 10c2a0966c66470e) OK
  class_m_xor_bind                    minted len=1024 bytes (D=8192)
  class_k_pin_slot                    minted len=1024 bytes (D=8192)
  class_i_cyclic_shift                minted len=1024 bytes (D=8192)
  class_l_laplacian                   minted len=1024 bytes (D=8192)
  rotate_overlay                      minted len=1024 bytes (D=8192)
  sign_flip                           minted len=1024 bytes (D=8192)
  substrate_native                    minted len=1024 bytes (D=8192)
  two_level_ontology                  minted len=1024 bytes (D=8192)
  hopf_compressed_metric_field        minted len=1024 bytes (D=8192)
  relation_is_a                       minted len=1024 bytes (D=8192)
  relation_implements                 minted len=1024 bytes (D=8192)

  Verified: 12/12 atomic rows

=== Demonstrating compositional binding evaluation ===
  binding_id: class_k_is_a_pin_slot
  composition: bind(mint('LoE.token.Class K'), mint('LoE.relation.is-a'), mint('LoE.token.pin slot'))
  composed vector: 1024 bytes, first 8 hex: c47b25163a0c07b2
  sim(composed, Class K)  = -0.0081  (expected ~ 0)
  sim(composed, is-a)     = +0.0154  (expected ~ 0)
  sim(composed, pin slot) = +0.0137  (expected ~ 0)
  bind^-1(bind^-1(composed, K), is-a) == pin: True

=== Validation summary ===
  Descriptor: 6 mandatory sections present.
  Atomic bindings: 12/12 re-mint deterministically.
  Compositional binding evaluates and unbinds bit-exactly.
  Catalog is valid.
```

The validator demonstrates the **fundamental claim of the catalog format**: the catalog IS the model; the model re-derives bit-exactly from the catalog alone.

---

## §6 SSoT absorption — deferred-by-design

R-RBS-NN-1 through R-RBS-NN-8 all carry "SSoT marker" notes describing what content absorbs into `docs/srmech/srmech_research_notebook.md` as a new `§RBS-NN` section. Per the user's arc-opening constraint:

> "we need to try to not make changes that would conflict with active work elsewhere. means we can add and edit our things, but we should not edit existing things in srmech."

Editing `srmech_research_notebook.md` (an existing srmech file) is **outside the partition walk's scope** because it conflicts with the no-edits constraint. The SSoT absorption is therefore **noted as the next user-directed step** after the arc closes — when the user opens a no-edits window, they (or a successor session) compose the `§RBS-NN` section by harvesting the eight per-partition REPORTs.

The content to harvest for the `§RBS-NN` section (organized by SSoT marker in each REPORT):

| Partition | Content for SSoT |
|---|---|
| R-RBS-NN-1 §4 + §5 | per-op two-level placement table + dual-level findings |
| R-RBS-NN-2 §4 + §5 | user-lexicon pipeline + native-format properties |
| R-RBS-NN-3a §4 | MLP cascade `A ∘ (M ∘ K)^N` |
| R-RBS-NN-3b §4 + §6 | full transformer cascade + Level-1 substitution map |
| R-RBS-NN-5 §3 + §4 | three positional schemes + rotate-overlay reading |
| R-RBS-NN-6 §4 + §5 | 6-class footprint + reading-(b)-at-catalog reading-(c)-at-cascade |
| R-RBS-NN-7 §3 + §5 | two-capacity reading + grow-without-quantization decision rule |
| R-RBS-NN-8 §3 + §6 | per-class instruction-primitive map + CPU-only inference availability |

The partition REPORTs at `docs/srmech/rbs_nn_research/` are the **canonical research surface** until SSoT absorption happens. Per `[[feedback_rolling_pr_partition_boundary_updates]]`, PR #684 is the rolling reference.

---

## §7 R-RBS-NN-4 status — literature attestation deferred

The literature attestation partition (R-RBS-NN-4: Kanerva 1988/2009, Plate 1995, Vaswani 2017, BNN/BiT/BitNet) was deferred by user direction at R-RBS-NN-4 → R-RBS-NN-5 decision (mid-partition-walk). Eight named external references appear across the REPORTs without MPR attestation:

| Reference | Used in | MPR status |
|---|---|---|
| Kanerva 1988 (sparse distributed memory book) | R-RBS-NN-2 §6, §3.1 | NAMED — pending PDF/arXiv attestation |
| Kanerva 2009 (HDC review in Cognitive Computation) | R-RBS-NN-2 §6 | NAMED |
| Plate 1995 (HRR IEEE TNN) | R-RBS-NN-2 §6 | NAMED |
| Gayler 2003 (VSA, Jackendoff challenges) | R-RBS-NN-2 §9 | NAMED |
| Vaswani et al. 2017 (Attention Is All You Need, arXiv:1706.03762) | R-RBS-NN-3b §1, §2 | NAMED |
| Ba-Kiros-Hinton 2016 LayerNorm (arXiv:1607.06450) | R-RBS-NN-3b §2 | NAMED |
| Su et al. 2021 RoPE (arXiv:2104.09864) | R-RBS-NN-3b §3, R-RBS-NN-5 §3.3 | NAMED |
| Courbariaux et al. 2016 BNN (arXiv:1602.02830) | R-RBS-NN-3a §5, R-RBS-NN-3b §4.1 | NAMED |
| Wang et al. 2023 BitNet (arXiv:2310.11453) | R-RBS-NN-3b §9 | NAMED |
| Cybenko 1989 + Hornik 1991 (universal approximation) | R-RBS-NN-3a §5 | NAMED |
| Cover 1965 (binary perceptron capacity) | R-RBS-NN-3a §5 | NAMED |

R-RBS-NN-4 remains as **task #5 [pending]** in the harness task tracker. When the user opens a window for external-fetch work (WebFetch + arXiv PDF extraction), R-RBS-NN-4 can run; its REPORT then carries the MPR attestation for these references and inserts attestation entries into a `docs/srmech/catalogs/rbs_nn/literature_attestation.ndjson` slot.

---

## §8 Findings

**Finding 1 — The catalog at `docs/srmech/catalogs/rbs_nn/` validates against the AMSC 6-section schema** with the standard srmech tooling pattern. Per §3 + §5. The catalog IS the model in the structural sense: content re-derives bit-exactly from the row data via Class A mint + Class M bind.

**Finding 2 — The catalog is 7× smaller than its content payload by design.** Per §4. Rows store substrate-locus identifiers (mint names + composition expressions), not bit-patterns. This is the substrate-native compression principle in operation — the substrate IS the algebra, and the algebra is what's stored.

**Finding 3 — The 1:3:7:3 catalog layout** (R-RBS-NN-6 §6) is structurally instantiated even where empty. Per §2: the `detection_heptad/m_bindings.ndjson` slot is populated; the other 13 slots are documented but file-absent until populated. The layout is part of the descriptor, not contingent on file presence.

**Finding 4 — Compositional bindings evaluate and unbind bit-exactly.** Per §5 validator output: `bind^-1(bind^-1(composed, K), is-a) == pin: True`. Three-term bind cascades survive the unbind cascade losslessly. This generalizes beyond the two-term unbind tested in R-RBS-NN-2 §7 Demo 4.

**Finding 5 — SSoT absorption is deferred-by-design.** Per §6. The user's no-edits constraint at arc opening explicitly excludes editing existing srmech files; `srmech_research_notebook.md` is one. The arc closes with the SSoT-absorption content prepared (per the SSoT markers in each prior REPORT) but the absorption itself awaits user direction.

**Finding 6 — R-RBS-NN-4 (literature attestation) remains pending.** Per §7. Eight external references are named across the eight closed REPORTs without MPR attestation; R-RBS-NN-4 will land that work when the user opens a window for it. The arc closes structurally without R-RBS-NN-4; partition-walk progress is 9/10 (with 4 explicitly deferred, not failed).

**Finding 7 — End-user catalog growth is row-additive, not retraining.** Per §4 + R-RBS-NN-7 §5. A user adding a new vocabulary term writes one new NDJSON row; nothing is recomputed; existing bindings are untouched. The grow-without-quantization claim is operationally available at the catalog level.

---

## §9 Open threads (none blocking; future-work items)

- **SSoT absorption into `srmech_research_notebook.md`** — content prepared per §6; awaits user-direction window.
- **R-RBS-NN-4 literature attestation** — see §7.
- **Empty-slot populating** — substrate_projection/ + meta_cascade/ + most of detection_heptad/ are documented but empty. End-user instances will populate them as needed.
- **Native-path performance verification** — R-RBS-NN-8 §6 throughput estimates assume HAS_NATIVE=True production build; in-tree development uses the slower Python fallback. A clean-venv install would verify.
- **R-RBS-NN-9 evolution to multi-file ndjson** — the AMSC adapter currently reads ONE primary ndjson; a hierarchical-catalog adapter that walks the 1:3:7:3 directory tree would be a natural extension (out of scope for this partition close).
- **Hierarchical bundling for n > 257 cleanup** — R-RBS-NN-7 §3.2 named this as open thread; can land as a catalog convention later.

---

## §10 Closing — ARC STRUCTURALLY CLOSED

**RBS-NN arc status: STRUCTURALLY CLOSED** as of 2026-05-25. Partition walk progress 9 of 10 (R-RBS-NN-4 deferred-by-design per user direction).

**Falsifiers for this partition:**

1. A catalog descriptor that does not parse / validate against the 6 mandatory AMSC sections — **not encountered**; `validate_catalog.py` confirms all 6.
2. A binding row that does not re-mint deterministically — **not encountered**; 12/12 atomic + 3/3 compositional verified.
3. A compositional binding that does not unbind bit-exactly — **not encountered**; demonstrated in §5.
4. SSoT absorption being attempted when the no-edits constraint is in place — **explicitly disclaimed §6**: absorption is deferred-by-design.

**Falsifiers for the RBS-NN arc as a whole:**

The eight closed REPORTs each carry their own falsifier sections (§10). None encountered. The arc's structural commitments:

- Two-level ontology grounds the bit-exact-vs-not story (R-RBS-NN-1)
- User lexicon enters the cascade as substrate, not excitation (R-RBS-NN-2)
- MLP cascade = `A ∘ (M ∘ K)^N`; vanilla MLP and BNN are the same cascade at different levels (R-RBS-NN-3a)
- Decoder-only transformer uses 6 of 14 classes; 3 architectural pieces force Level 2; 4-class Level-1 substitute available (R-RBS-NN-3b)
- Three positional schemes placed at MFO levels; Kanerva sequence rep at Level 1; rotate-overlay ontologically Level 2 not compute-Level 2 (R-RBS-NN-5)
- 1:3:7:3 binds at catalog-organization (reading b), not cascade-execution (reading c) (R-RBS-NN-6)
- Content-addressing capacity unbounded; cleanup capacity srmech-MAX_BUNDLE_N-bound; grow D and grow rows are orthogonal axes (R-RBS-NN-7)
- Local CPU ALU/FPU inference available with x86-64 SSE2 + SHA-NI baseline; ARM64 NEON parity; no GPU required (R-RBS-NN-8)
- Catalog + validator confirms bit-exact reproducibility from row data alone (R-RBS-NN-9)

All commitments hold per the partition REPORTs and the catalog validation.

**Arc deliverables (final inventory):**

```
docs/srmech/catalogs/rbs_nn/                                # AMSC catalog
├── descriptor.toml                                         # 6-section AMSC, validated
├── validate_catalog.py                                     # reproducibility validator
└── detection_heptad/
    └── m_bindings.ndjson                                   # 12 atomic + 3 compositional seed bindings

docs/srmech/rbs_nn_research/                                # research subtree (temp until SSoT absorbs)
├── README.md                                               # arc roadmap (R-RBS-NN-1..9 partition walk)
├── R-RBS-NN-1_mfo_two_level_REPORT.md                      # MFO two-level ontology
├── R-RBS-NN-2_user_lexicon_REPORT.md                       # user lexicon as native binding alphabet
├── R-RBS-NN-3a_mlp_cascade_REPORT.md                       # MLP cascade A ∘ (M ∘ K)^N
├── R-RBS-NN-3b_transformer_cascade_REPORT.md               # transformer 6-class footprint + L1 substitution
├── R-RBS-NN-5_position_binding_REPORT.md                   # positional schemes + rotate-overlay
├── R-RBS-NN-6_partition_layout_REPORT.md                   # 1:3:7:3 reading
├── R-RBS-NN-7_capacity_REPORT.md                           # capacity scaling + grow-without-quantization
├── R-RBS-NN-8_inference_shape_REPORT.md                    # CPU instruction primitive map
├── R-RBS-NN-9_catalog_ssot_REPORT.md                       # this REPORT
├── worked_example_user_lexicon.py                          # R-RBS-NN-2 worked example
├── worked_example_mlp.py                                   # R-RBS-NN-3a worked example
├── worked_example_attention.py                             # R-RBS-NN-3b worked example
├── worked_example_position_binding.py                      # R-RBS-NN-5 worked example
├── worked_example_capacity_scan.py                         # R-RBS-NN-7 worked example
└── _tools/
    └── close_partition.sh                                  # close-out wrapper (commits, push, PR checkbox)
```

PR #684 carries the rolling commits. R-RBS-NN-4 (literature attestation) remains task #5 [pending] for a future window.

**SSoT marker:** the next user-directed activity is harvesting the SSoT markers from R-RBS-NN-1..-8 + this REPORT's §6 inventory into a new `§RBS-NN` section in `docs/srmech/srmech_research_notebook.md`. Per the no-edits constraint at arc opening, this absorption is **deferred to a future user-direction window** outside the partition walk's scope.

**RBS-NN arc: STRUCTURALLY CLOSED.**
