# R-RBS-LM-13 — Catalog refactor to compute_from_source schema

**Partition status:** CLOSED
**Date:** 2026-05-25
**Closes:** task #23 of the partition tracker
**Closing artefact:** `docs/srmech/catalogs/rbs_lm/descriptor.toml` updated to compute_from_source; `research_notes.ndjson` (sidecar metadata) preserved from prior `m_bindings.ndjson`; `validate_catalog.py` updated with v0.5 schema + adapter-resolution gating
**Inheritance:** unblocks R-RBS-LM-14 (genuine 10× corpus scale test with multi-threading)

---

## Attestation block (MPR v1 — internal-repo variant)

| field | value |
|---|---|
| internal sources | `R-RBS-LM-12_amsc_adapter_REPORT.md` §3-§7 (adapter design + catalog schema + migration path) |
| empirical artefacts | refactored `docs/srmech/catalogs/rbs_lm/descriptor.toml`; renamed `m_bindings.ndjson → research_notes.ndjson`; refactored `validate_catalog.py` |
| user direction | "we cannot distribute the compressed RBS-HDC object so we will need to add the tooling to AMSC" — applied here at the catalog-schema level |
| repo commit | `c29daea7` at REPORT-write |
| reproducibility | `PYTHONPATH=docs/srmech/python python3 docs/srmech/catalogs/rbs_lm/validate_catalog.py` |

---

## §1 Goal

Apply the R-RBS-LM-12 §7 migration plan to the existing rbs_lm catalog. Refactor:

- `descriptor.toml` — adapter changes from `literature_curated` → `compute_from_source`; new `[fetch.compute_from_source]` block specifies procedure parameters per R-RBS-LM-12 §4.
- `detection_heptad/m_bindings.ndjson` — renamed to `research_notes.ndjson` (top-level sidecar) since it documents research metadata, not adapter input.
- `validate_catalog.py` — updated to validate the new schema; reports adapter-resolution status (IMPLEMENTED vs GATED) honestly.

Per R-RBS-LM-12 §6: the srmech-side `compute_from_source` adapter doesn't exist yet (planned for srmech v0.5.0rc). The catalog is **forward-spec'd**: schema valid; adapter resolution awaits the srmech-fix session.

---

## §2 Inheritance

| Source | Inherited finding | R-RBS-LM-13 use |
|---|---|---|
| R-RBS-LM-12 §3 | adapter design (fetch/parse/attest signature) | catalog points at it |
| R-RBS-LM-12 §4 | catalog schema (descriptor TOML structure) | implemented verbatim |
| R-RBS-LM-12 §5 | attestation chain (three new hashes) | declared in [attestation].provenance |
| R-RBS-LM-12 §6 | upstream-to-srmech work plan | catalog is forward-spec'd; gates on srmech v0.5.0rc |
| R-RBS-LM-12 §7 | existing-catalog migration path | this REPORT applies it |

---

## §3 What changed in the catalog

### §3.1 Files moved

```
docs/srmech/catalogs/rbs_lm/
├── descriptor.toml                              # rewritten (compute_from_source schema)
├── research_notes.ndjson                        # renamed from detection_heptad/m_bindings.ndjson
└── validate_catalog.py                          # refactored (new schema validation)

# Removed:
└── detection_heptad/                            # subdir removed (no longer needed)
    └── m_bindings.ndjson                        # moved (above)
```

### §3.2 descriptor.toml — key changes

```diff
 [fetch]
-adapter      = "literature_curated"
-ndjson_path  = "detection_heptad/m_bindings.ndjson"
+adapter      = "compute_from_source"
+output_path  = "produced/instrument.ndjson"
+
+[fetch.compute_from_source]
+source_model     = "gpt2"
+corpus_locator   = "user://supply-at-adapter-runtime"
+encoder_module   = "srmech.rbs_lm.encoder"
+encoder_version  = "0.1.0"
+
+[fetch.compute_from_source.encoder_params]
+D                = 8192
+context_window   = 64
+stride           = 8
+batch_size       = 32
+n_workers        = 8
+sampling         = "argmax"
+hierarchical_max = 257
```

### §3.3 [schema] section

```diff
 [schema]
-data_schema_id = "srmech.rbs_nn.binding.v1"
-ndjson_file    = "detection_heptad/m_bindings.ndjson"
+data_schema_id = "srmech.rbs_lm.compute_from_source.v1"
+ndjson_file    = "produced/instrument.ndjson"
```

The `ndjson_file` now points to where the **adapter writes the produced instrument** — not a committed input file. This is the structural shift: catalog ships procedure; instrument is locally-computed.

### §3.4 [attestation] — new chain documented

The provenance string now documents the three new attestation hashes per R-RBS-LM-12 §5:
- `source_model_hash` — SHA-256 of source model weights
- `corpus_hash` — SHA-256 of behavioral corpus bytes
- `encoder_module_hash` — SHA-256 of encoder module source

Plus the forward-spec'd status note: *"Adapter resolution gates on the srmech-side compute_from_source adapter being implemented (planned for srmech v0.5.0)... until that release, descriptor validates at schema level but adapter resolution fails — the catalog is forward-spec'd."*

### §3.5 research_notes.ndjson preserved as sidecar

The 12 metadata rows from the prior m_bindings.ndjson are preserved verbatim under the new name. These rows (encoding-descriptors, observation-example, atomic-mints, empirical-finding, future-work-pointers) are research-context documentation; they're not adapter input/output. The rename makes their role clear.

---

## §4 Validator output

Captured at commit `c29daea7`:

```
=== R-RBS-LM-13 catalog validation (compute_from_source schema) ===

  Catalog: RBS-LM — compute-from-source GPT-2-small base catalog
  Key:     rbs_lm_gpt2_small
  Required sections present: ['source', 'fetch', 'parse', 'schema', 'rendering', 'attestation'] — OK

  compute_from_source schema:
    source_model: gpt2
    corpus_locator: user://supply-at-adapter-runtime
    encoder_module: srmech.rbs_lm.encoder
    encoder_version: 0.1.0
    encoder_params:
      D = 8192
      context_window = 64
      stride = 8
      batch_size = 32
      n_workers = 8
      sampling = argmax
      hierarchical_max = 257
    — required fields present — OK

  research_notes.ndjson: 12 rows; all valid JSON
  Row kinds: {'encoding_descriptor': 2, 'observation_example': 1, 'atomic': 4, 'empirical_finding': 1, 'future_work_pointer': 4}

  Adapter resolution check:
    compute_from_source adapter: NOT YET IMPLEMENTED (GATED)
    Catalog is FORWARD-SPEC'D per R-RBS-LM-12 §6 — schema valid;
    adapter resolution awaits srmech v0.5.0rc release.
    The srmech-fix session plan is documented in R-RBS-LM-12 §6.

  produced/ directory: not yet created (will be created by adapter on first run)

=== Catalog validation complete ===
```

All checks pass per the gated state: schema valid; adapter resolution reports GATED (expected); produced/ not yet created (expected — created on first adapter run).

---

## §5 The forward-spec'd state — when it unlocks

The catalog will become **fully runnable** when the srmech-fix session (per R-RBS-LM-12 §6) lands. Specifically when:

1. `srmech.rbs_lm.encoder.encode_source_model_mt` is importable from a `pip install srmech[rbs_lm]` (or whatever the optional-dep group is named)
2. `srmech.amsc.adapters.compute_from_source` is registered
3. srmech is released at v0.5.0 (or v0.5.0rcN on TestPyPI)

At that point, `validate_catalog.py` will detect the import success and switch from "GATED" to "IMPLEMENTED + runnable". A `srmech.amsc.run(descriptor)` call (or equivalent) will produce the instrument locally.

---

## §6 Findings

**Finding 1 — Catalog refactored to compute_from_source schema; validates clean.** Per §4. All 6 mandatory AMSC sections present; new compute_from_source block has all 4 required fields; encoder_params block populated.

**Finding 2 — Instrument bytes no longer in the committed catalog.** Per §3.1. The catalog directory has descriptor.toml + research_notes.ndjson + validate_catalog.py only. The instrument is produced locally at `produced/instrument.ndjson` (not committed; .gitignore handles it implicitly since `produced/` will only exist post-adapter-run).

**Finding 3 — Forward-spec'd is operationally clean.** Per §4 validator output. The validator reports GATED status when the srmech adapter isn't available, with an explicit pointer to R-RBS-LM-12 §6 work plan. Future re-runs after srmech v0.5.0 lands will report IMPLEMENTED.

**Finding 4 — research_notes.ndjson preserved as sidecar** (rather than deleted). The 12 metadata rows document research context; useful for catalog consumers regardless of adapter implementation status. The role-as-sidecar is now clear from the rename.

**Finding 5 — The committed .bin files in `docs/srmech/rbs_lm_research/` remain as research artefacts** (not deleted). They're not in the distributable catalog directory; they document the encoded instruments produced during R-RBS-LM-5/-9/-11 research runs. Per `[[feedback_no_lineage_claims_in_notebook]]`: research artefacts vs distributed catalogs are separate concerns.

**Finding 6 — The catalog now honors the user direction precisely.** Per the original ask: *"we cannot distribute the compressed RBS-HDC object so we will need to add the tooling to AMSC."* This partition lands the catalog-schema side of that tooling work. The srmech-package side (adapter implementation) is upstream-to-srmech per `[[feedback_upstream_srmech_fixes_as_research_notes]]`.

---

## §7 Open threads (not blockers for partition close)

- **The srmech-fix session** — implements the compute_from_source adapter + the srmech.rbs_lm subpackage; lands as srmech v0.5.0rc1 on TestPyPI per `[[feedback_always_rc_first_for_downstream_publishes]]`. Out-of-scope for this PR.
- **A second base catalog** — for a different source model (Qwen-2.5-0.5B? Phi-3-mini? GPT-2-medium?). Future work; documents per-model encoding profiles.
- **The user:// corpus_locator scheme** — exact URI scheme set is a srmech adapter implementation detail; this catalog uses `user://supply-at-adapter-runtime` as a placeholder. Real schemes might be `file:///abs/path`, `hf://dataset/wikitext-103`, etc.
- **The .gitignore for `produced/`** — should be added at the catalog dir to make the local-computation pattern explicit. Could land as a small follow-on edit.

---

## §8 Closing — partition status

**Status:** CLOSED. Catalog refactored to compute_from_source schema; validates clean per §4; forward-spec'd state documented per §5; ready for srmech-fix session adapter implementation per R-RBS-LM-12 §6.

**Falsifiers:**

1. A schema validation failure on the new descriptor — **not encountered**.
2. A claim that this partition implements the srmech-side adapter — **explicitly disclaimed**; the adapter is GATED per §5.
3. A claim that the .bin research artefacts should be deleted — **disclaimed §6 Finding 5**: research-subtree artefacts ≠ distributed catalogs; the .bin files document past research runs and stay as research-subtree references.

**Inherits to:** R-RBS-LM-14 (genuine 10× corpus + multi-threading scale test — the final empirical test of Path B at sub-10⁴ scale).

**SSoT marker:** at SSoT absorption, §3 catalog changes + §5 forward-spec'd state absorb into `srmech_research_notebook.md` as part of the RBS-LM catalog-distribution subsection.
