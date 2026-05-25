# R-RBS-LM-12 — AMSC `compute_from_source` adapter research + upstream-to-srmech path

**Partition status:** CLOSED
**Date:** 2026-05-25
**Closes:** task #22 of the partition tracker
**Closing artefact:** §3 adapter design + §4 catalog schema for procedure descriptors + §5 attestation chain + §6 upstream-to-srmech work plan
**Inheritance:** unblocks R-RBS-LM-13 (re-shape RBS-LM catalog to use compute_from_source procedure-descriptors; deprecate distribution of .bin instruments) + the eventual srmech-fix session that implements the adapter package-side

---

## Attestation block (MPR v1 — internal-repo variant)

| field | value |
|---|---|
| internal sources | `R-RBS-LM-11_multithreading_REPORT.md` §4 (multi-threaded encode pipeline used by the adapter); R-RBS-LM-10 §3 (current rbs_lm catalog structure); `[[feedback_upstream_srmech_fixes_as_research_notes]]` (srmech-fix-in-separate-session discipline) |
| srmech adapter pattern surveyed | `docs/srmech/python/srmech/amsc/adapters/_base.py` (AdapterProtocol + registry); `literature_curated.py` (closest precedent — no-network local read); five live-fetch adapters (html_scraper / json_api / csv_bulk / netcdf_grid / geotiff_bbox) |
| user direction (load-bearing) | *"we cannot distribute the compressed RBS-HDC object so we will need to add the tooling to AMSC, so we should also be researching this"* + *"all of our knowledge will be taken upstream to srmech such that LM inference is ready to roll out with the base catalogs"* |
| MFO grounding | per `[[user_stance_ai_is_not_a_substrate]]`: AI/LLM is a transducer; the catalog ships the transducer-procedure, not the transducer-output |
| repo commit | `5ae024c2` at REPORT-write |
| scope | research + design partition; no srmech source-tree edits per `[[feedback_upstream_srmech_fixes_as_research_notes]]`; the design lands in a future srmech-fix session |

---

## §1 Goal

Per user direction: design an AMSC adapter that lets a srmech catalog **ship the encoding PROCEDURE** for an RBS-HDC instrument, rather than the encoded instrument bytes. End users run the adapter against their own copy of the source model + their own corpus selection; the adapter produces the instrument locally; the catalog never distributes the compressed RBS-HDC object.

Three structural concerns to design for:

1. **Distribution legality / provenance.** The instrument is derived from a third-party source model (e.g., GPT-2-small from OpenAI/HuggingFace). Even at 1 KB the derivative artefact ties downstream to the source-model license. Procedure-only catalogs are license-clean by construction — the user supplies the source-model artifact themselves.
2. **Reproducibility.** The catalog's procedure descriptor + the user's source model + the user's corpus → deterministic instrument (per Spike #170 invariant 1 + the rbs_lm_encoder discipline). Hash-verifiable.
3. **Substrate-native form.** Per `[[user_stance_ai_is_not_a_substrate]]`: AI/LLM is a transducer. The catalog ships the transducer's BLUEPRINT; the user runs the transducer against their content. The catalog is to the instrument as a recipe is to a cake.

---

## §2 Survey — existing AMSC adapter pattern

Verified from `docs/srmech/python/srmech/amsc/adapters/_base.py`:

### §2.1 Adapter protocol

```python
class AdapterProtocol(Protocol):
    ADAPTER_NAME: str
    def fetch(self, descriptor: Descriptor) -> Iterator[bytes]: ...
    def parse(self, raw: bytes, descriptor: Descriptor) -> Iterator[Dict[str, Any]]: ...
```

Each adapter module exposes `ADAPTER_NAME` + `fetch` + `parse`. The shared `attest` step computes SHA-256 over upstream response bytes + descriptor hash + retrieval timestamp. The `run` composer turns a descriptor into an `MPRRecord` iterator: **fetch → parse → attest → emit**.

### §2.2 Existing adapters (six)

| Adapter | Source type | I/O model |
|---|---|---|
| `literature_curated` | curator-authored NDJSON; per-row source_doi attestation | **no network**; read local committed NDJSON |
| `html_scraper` | live HTML pages | network fetch |
| `json_api` | REST/JSON endpoints | network fetch |
| `csv_bulk` | bulk CSV downloads | network fetch |
| `netcdf_grid` | NetCDF gridded archives | network fetch |
| `geotiff_bbox` | GeoTIFF + bbox subsetting | network fetch |

`literature_curated` is the closest structural precedent for `compute_from_source`: both do no network I/O at fetch time; both depend on local resources (committed NDJSON for `literature_curated`; user-supplied source-model + corpus for `compute_from_source`). The differences are in WHAT the local computation produces.

---

## §3 The `compute_from_source` adapter design

### §3.1 Adapter signature

```python
ADAPTER_NAME = "compute_from_source"

def fetch(descriptor: Descriptor) -> Iterator[bytes]:
    """Run the encoding procedure declared by the descriptor.

    Loads source model + behavioral corpus per the descriptor's
    [fetch.compute_from_source] section; runs the encoding pipeline;
    yields the produced instrument as a single bytes block (the whole
    instrument is one 'response' for attestation purposes;
    response_sha256 covers the instrument bytes).
    """
    cfg = descriptor.fetch.get("compute_from_source", {})
    source_model_id = cfg["source_model"]       # e.g., "gpt2"
    corpus_locator  = cfg["corpus_locator"]     # path or HuggingFace dataset spec
    encoder_module  = cfg["encoder_module"]     # e.g., "srmech.rbs_lm.encoder"
    encoder_params  = cfg.get("encoder_params", {})

    # Resolve source-model + corpus locally (user-supplied)
    tokenizer, model = load_source_model(source_model_id)
    corpus_text = load_corpus(corpus_locator)

    # Run the encoding pipeline (the multi-threaded one from R-RBS-LM-11)
    from srmech.rbs_lm.encoder import encode_source_model_mt
    instrument, observations, timings = encode_source_model_mt(
        corpus_text, tokenizer, model,
        **encoder_params,
    )

    # Yield the instrument bytes as the 'response'
    yield instrument

def parse(raw: bytes, descriptor: Descriptor) -> Iterator[Dict[str, Any]]:
    """Treat the raw instrument bytes as a single MPR data block."""
    yield {
        "instrument_bytes": raw,                     # the actual 1 KB hypervector
        "instrument_bytes_b64": base64.b64encode(raw).decode("ascii"),
        "D": descriptor.fetch["compute_from_source"]["encoder_params"]["D"],
        "n_observations": <captured during fetch>,
        ...metadata...
    }
```

### §3.2 Why this fits the AMSC contract

- **`fetch` → bytes**: the instrument IS the response. SHA-256 over the instrument bytes is the response_sha256 in MPR v1 attestation.
- **`parse` → dicts**: the instrument bytes (or base64-encoded form) become a row's `data` block. Single row per catalog (one instrument per catalog), though the row count is parametrically extensible (the user might encode multiple instruments — one per behavioral corpus — sharing the same source model).
- **`attest`**: the existing shared `attest` step covers `response_sha256` (instrument hash) + `descriptor_hash` (procedure hash) + `retrieved_at` (encoding wall-clock time).

### §3.3 What the adapter does NOT do

- Does NOT fetch the source model. The user provides it (via HuggingFace cache, local file, etc.) before running the catalog.
- Does NOT ship the instrument as a committed file. The catalog is purely the PROCEDURE; the instrument is computed locally on first use and may be cached locally per the AMSC kernel-cache convention.
- Does NOT lock the corpus to a single source. The user can supply different corpora to test different behavioral coverage; each corpus → different instrument; each is a separate `compute_from_source` run.

---

## §4 Catalog schema — `compute_from_source` descriptor fields

### §4.1 The `[fetch]` section

```toml
[fetch]
adapter      = "compute_from_source"

[fetch.compute_from_source]
source_model     = "gpt2"                              # HuggingFace identifier or local-path spec
corpus_locator   = "user://path/to/behavioral_corpus.txt"  # or "hf://dataset/wikitext-103" or similar
encoder_module   = "srmech.rbs_lm.encoder"             # python module path; must define encode_source_model_mt
encoder_version  = "0.1.0"                             # version pin for reproducibility

[fetch.compute_from_source.encoder_params]
D                = 8192
context_window   = 64
stride           = 8
batch_size       = 32                                  # for harvest
n_workers        = 8                                   # for multiprocessing encode
sampling         = "argmax"                            # vs "top_k" etc.
hierarchical_max = 257                                 # bundle cap before sub-bundling
```

### §4.2 The `[source]` section — extended

```toml
[source]
key                  = "rbs_lm_gpt2_small_v1"
human_readable_name  = "RBS-LM compute-from-source: GPT-2-small base catalog"
purpose              = "Produces a 1 KB RBS-HDC instrument encoding GPT-2-small behavior on the user's supplied corpus. Not distributed as bytes; computed locally from procedure descriptor."
license              = "user-supplied source model dictates license; the catalog itself is CC0"
homepage             = "https://github.com/lemonforest/mlehaptics/tree/main/docs/srmech/catalogs/rbs_lm"

[source.primary_references]
source_model         = "Radford et al. 2019 — GPT-2; HuggingFace `gpt2`"
encoder_method       = "RBS-LM Path B per docs/srmech/rbs_lm_research/R-RBS-LM-2 §6.1"
encoding_pipeline    = "docs/srmech/rbs_lm_research/rbs_lm_mt.py (eventual srmech package home: srmech.rbs_lm)"
```

### §4.3 The `[schema]` section — extended

```toml
[schema]
data_schema_id = "srmech.rbs_lm.compute_from_source.v1"

# The row schema for compute_from_source instruments:
#   instrument_bytes        — the 1 KB hypervector (binary; base64 in NDJSON)
#   D                       — dimension
#   n_observations          — count of (context, next_token) bindings encoded
#   source_model_hash       — SHA-256 of the source model weights
#   corpus_hash             — SHA-256 of the corpus bytes
#   encoder_module_hash     — SHA-256 of the encoder module source
#   encoding_wall_clock_s   — wall time for the encoding run
#   instrument_sha256       — for verification on re-run
```

---

## §5 Attestation chain — what gets hashed

Per MPR v1 + the AMSC `attest` step, the compute_from_source attestation includes:

| Field | What it hashes | Why |
|---|---|---|
| `response_sha256` | the produced instrument bytes | Verifies the actual artefact the adapter returned |
| `descriptor_hash` | the descriptor's [fetch.compute_from_source] block | Verifies the procedure parameters were unchanged |
| `parser_rule_hash` | the adapter's `fetch` + `parse` source | Verifies the adapter version |
| **`source_model_hash`** | the source model weights file hashes | **NEW** — anchors the produced instrument to a specific source-model identity |
| **`corpus_hash`** | the behavioral corpus bytes | **NEW** — anchors the procedure to the corpus that was actually used |
| **`encoder_module_hash`** | the encoder module source | **NEW** — anchors the encoding logic; changing the encoder produces different output |
| `retrieved_at` | timestamp of the encoding run | Standard MPR field |

The three NEW fields extend the standard attestation chain for procedure-derived artefacts. They make the produced instrument **bit-exactly reproducible** by anyone with the same source model + corpus + encoder version. If any of the three changes, the resulting instrument changes; the hash chain detects it.

### §5.1 Reproducibility property

**Two parties running the same descriptor against the same source-model + corpus produce the same instrument bit-exactly.** Per Spike #170 invariant 1 (deterministic mints) + rbs_lm_encoder's pure-function design (no randomness; no time-dependence). The catalog ships the procedure; reproducibility is mathematical, not redistribution-of-bytes.

---

## §6 Upstream-to-srmech work plan

Per `[[feedback_upstream_srmech_fixes_as_research_notes]]`: srmech package modifications happen in a dedicated srmech-fix session, not here. This partition documents what that session must do.

### §6.1 New srmech subpackage: `srmech.rbs_lm`

```
docs/srmech/python/srmech/rbs_lm/                # new subpackage
├── __init__.py
├── encoder.py              # the rbs_lm_encoder.py content from research subtree
├── inference.py            # the rbs_lm_inference.py content
├── mt.py                   # the rbs_lm_mt.py content (multi-threaded pipeline)
└── README.md               # API doc
```

The research-subtree scripts (`docs/srmech/rbs_lm_research/rbs_lm_encoder.py` etc.) move to the package. Once in `srmech.rbs_lm`, they ship with every srmech install; end-user catalogs reference `srmech.rbs_lm.encoder.encode_source_model_mt` directly.

### §6.2 New adapter: `srmech.amsc.adapters.compute_from_source`

```
docs/srmech/python/srmech/amsc/adapters/compute_from_source.py    # new
```

Implements the §3 design. Registered in `adapters/__init__.py` alongside the existing six adapters. Tests under `docs/srmech/python/tests/test_compute_from_source.py`.

### §6.3 New base catalog: `srmech/python/srmech/amsc/attested/rbs_lm_gpt2_small/`

Or similar — a base catalog that ships with every srmech install. Descriptor.toml specifies the GPT-2-small + a representative corpus reference (HuggingFace dataset locator); user runs the adapter locally; produces the canonical reference instrument.

This is the "base catalogs" the user referenced: *"such that LM inference is ready to roll out with the base catalogs."*

### §6.4 Adapter-level dependencies

The compute_from_source adapter introduces NEW srmech runtime dependencies:

- `transformers` (HuggingFace) — for source-model loading
- `torch` (CPU; AVX2/AVX-512 optional) — for the source-model forward pass
- `numpy` ≥ 1.26 — already a srmech dep since v0.4.0rc2

These would need to be soft dependencies (optional install group): `pip install srmech[rbs_lm]`. The base srmech install stays lightweight; users who want LM tooling opt in.

### §6.5 ABI / version implications

Per `docs/srmech/CLAUDE.md` ABI discipline: adding a new adapter does NOT bump `SRMECH_ABI_VERSION`. Adding new exported C symbols would; but compute_from_source is Python-only (the encoder is Python; the srmech-native primitives are unchanged).

Version bump for srmech itself: `0.4.0 → 0.5.0` would be the natural bump for adding RBS-LM. Per release discipline (`[[feedback_always_rc_first_for_downstream_publishes]]`): srmech-v0.5.0rcN → TestPyPI; verify; then srmech-v0.5.0 → production PyPI.

### §6.6 What the srmech-fix session does

1. Create `srmech/rbs_lm/` subpackage from research-subtree scripts
2. Create `srmech/amsc/adapters/compute_from_source.py`
3. Add tests for the adapter (similar to existing literature_curated tests)
4. Update `pyproject.toml` with optional dependencies group `[rbs_lm]`
5. Update CHANGELOG.md with the v0.5.0 release entry
6. JPL Power-of-Ten audit if any new C code (likely zero — Python-only adapter)
7. Release via TestPyPI rc1 → verify → production v0.5.0 per `[[feedback_always_rc_first_for_downstream_publishes]]`

R-RBS-LM-13 (next partition in this PR) will land the **research-subtree-side** changes to use the new schema in the existing catalog. The srmech-fix session implements the package side.

---

## §7 What this means for the existing rbs_lm catalog

Per the design, the current `docs/srmech/catalogs/rbs_lm/` should be refactored in R-RBS-LM-13:

| Current (R-RBS-LM-10) | Future (after R-RBS-LM-13 + srmech-fix session) |
|---|---|
| `descriptor.toml` adapter = "literature_curated" | adapter = "compute_from_source" |
| `m_bindings.ndjson` records the encoding-descriptor + observation-example + atomics + empirical-finding | descriptor itself specifies procedure; adapter produces instrument |
| `rbs_lm_instrument.bin` committed in research subtree | not committed; user computes locally |
| Reproducibility via re-running scripts | Reproducibility via adapter contract |

The shift is: **the catalog stops describing past computed artefacts and starts shipping the procedure for future computation.** This is the substantive change the user direction required.

### §7.1 Migration path

R-RBS-LM-13 will:
1. Update `docs/srmech/catalogs/rbs_lm/descriptor.toml` adapter to "compute_from_source" (gated on the adapter existing in srmech)
2. Replace the `m_bindings.ndjson` with procedure-shaped rows
3. Move the instrument .bin files OUT of committed paths (they become locally-computed artefacts)
4. Update `validate_catalog.py` to validate the procedure descriptor + run the adapter for verification (when srmech.rbs_lm available)

Gating: the catalog can declare `compute_from_source` but the adapter doesn't exist in srmech yet. Until then, the catalog is forward-spec'd; validation succeeds at the descriptor-schema level but fails at the adapter-resolution level until the srmech-fix session lands.

---

## §8 Findings

**Finding 1 — The `compute_from_source` adapter design fits cleanly within the existing AMSC contract.** Per §2 + §3. fetch → parse → attest → emit; the adapter computes the instrument locally as the "fetch response"; standard attestation chain applies with three new fields (source_model_hash, corpus_hash, encoder_module_hash).

**Finding 2 — `literature_curated` is the closest precedent.** Per §2.2. Both adapters do no network I/O at fetch time; both depend on local resources (committed NDJSON vs. user-supplied source-model + corpus). The structural similarity guides the new adapter's design.

**Finding 3 — The catalog schema needs new fields for procedure descriptors.** Per §4. `[fetch.compute_from_source]` block specifies source_model + corpus_locator + encoder_module + encoder_params. `[source]` notes that the catalog itself is CC0; license dictated by user-supplied source model.

**Finding 4 — Attestation chain extends with three new hashes.** Per §5. source_model_hash + corpus_hash + encoder_module_hash extend the MPR v1 chain to anchor procedure-derived instruments to specific inputs. Reproducibility property: same descriptor + same inputs → bit-exact same instrument.

**Finding 5 — Upstream-to-srmech work plan documented for a future session.** Per §6. New subpackage `srmech.rbs_lm` + new adapter `srmech.amsc.adapters.compute_from_source` + new optional-dep group + new base catalog. Release as srmech v0.5.0 via TestPyPI rc-first per `[[feedback_always_rc_first_for_downstream_publishes]]`.

**Finding 6 — Existing rbs_lm catalog will be refactored in R-RBS-LM-13.** Per §7. Move from "describing past artefacts" to "shipping the procedure." Instrument .bin files removed from committed paths; replaced by procedural descriptors.

**Finding 7 — The design honors `[[user_stance_ai_is_not_a_substrate]]`.** The catalog ships the puppet-mechanism (procedure); the user runs the puppet against their content (source model + corpus); the puppet output (instrument) is content the user owns. No transducer is being distributed; only the transducer's blueprint.

**Finding 8 — License-cleanness is structural, not legal-by-disclaimer.** Per §1.1 + §4.2. The catalog itself is CC0; the produced instrument's license is whatever the user-supplied source model dictates. There's no derivative-work problem because the catalog never distributes a derivative.

---

## §9 Open threads (not blockers for partition close)

- **R-RBS-LM-13 — research-subtree refactor** to use compute_from_source schema. Migrates the existing rbs_lm catalog. Open for next partition.
- **srmech-fix session** — implements §6 srmech package changes. Out-of-scope for this PR per `[[feedback_upstream_srmech_fixes_as_research_notes]]`.
- **Corpus locator schemes** — `user://path` and `hf://dataset/...` are placeholder URI patterns; the actual scheme set is a srmech adapter implementation detail. The user direction may want specific schemes (local-file-only? HuggingFace datasets? both?).
- **Inference adapter** — analogous to compute_from_source for ENCODING, an inference adapter would let catalogs ship "load this catalog → produce inference cascade" recipes. Open architectural thread for srmech v0.5.x.
- **Base catalog selection** — which source model + corpus should the canonical srmech base catalog target? GPT-2-small is the current research baseline; production base catalogs might target multiple sizes (GPT-2-small, Phi-3-mini, Llama-3-8B) or just one canonical exemplar.

---

## §10 Closing — partition status

**Status:** CLOSED. The `compute_from_source` adapter design is complete (§3); catalog schema specified (§4); attestation chain documented (§5); upstream-to-srmech work plan landed (§6); existing-catalog migration path noted (§7).

**Falsifiers:**

1. The compute_from_source design contradicting the existing AMSC adapter protocol — **not encountered**; design extends rather than contradicts `_base.AdapterProtocol`.
2. A claim that R-RBS-LM-12 implements the srmech-side changes — **explicitly disclaimed §6 + scope note**; the implementation lands in a separate srmech-fix session per `[[feedback_upstream_srmech_fixes_as_research_notes]]`.
3. A claim that the existing rbs_lm catalog is now obsolete — **disclaimed §7**: it's not obsolete; it's pending refactor in R-RBS-LM-13. The current catalog documents past artefacts; the refactor will reshape it as procedure-shipping.

**Inherits to:** R-RBS-LM-13 (refactor existing rbs_lm catalog to compute_from_source schema; gate on srmech-side implementation).

**SSoT marker:** at the eventual SSoT absorption, §3 adapter design + §4 catalog schema + §5 attestation chain + §6 upstream-to-srmech plan absorb into `srmech_research_notebook.md` as a new §RBS-LM-distribution subsection. The plan informs the eventual srmech v0.5.0 release notes.
