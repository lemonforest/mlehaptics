# Spike #115 — Tool-schema surface design for `srmech.spectral.*` namespace

**Date**: 2026-05-18
**Spike type**: Concertmaster design (specifications, not implementation)
**Verdict**: `SEVEN-ENTRY-SPECIFICATIONS-COMPLETE` + `CACHING-STRATEGY-DOCUMENTED` + `CLASS-OPERATOR-CHAIN-ATTESTED-PER-ENTRY` + `C-PYTHON-PARITY-SPLIT-DOCUMENTED-PER-ENTRY` + `RC-REGISTRATION-READY` (two-rc strategy)

## Tuning A 440 Hz

This is a design spike. No new code beyond two `notes/` deliverables. Discipline:

- **No new primitive class** per `[[feedback_no_privileged_primitive_classes]]`. Vocabulary stays at 14 classes A–N. `srmech.spectral.*` IS a composition layer above `srmech.amsc.*`, not a new primitive class.
- **Identity-not-implementation** per `[[user_stance_identity_not_implementation_discipline]]`: each entry IS its class-operator composition; it does not "implement" spectral capability.
- **Algebra-not-magnitude** per `[[user_stance_framework_domain_algebra_not_length_or_magnitude]]`: tool-schema describes ALGEBRA; substrate-coupling magnitudes (D, k, threshold, predictor) are inputs.
- **C/Python parity** per `[[feedback_no_binding_layer_carveout]]`: composition layer is Python; each composed sub-op already has (or will have) a libsrmech C surface. Net-new C primitives (cascade_extrapolate, sparse_truncate) deferred to Spike #113 + #117 — enumerated, not waived.
- **Science is SSoT** per `[[feedback_science_is_ssot_not_project]]`: every `canonical_ssot` cites published literature; chess-spectral §5b cited only as cross-substrate-generalisation locator, never as substitute for canonical algebra.
- **Citation hygiene** per `[[feedback_pdf_extraction_citation_discipline]]`: every paywalled reference clearly marked as cite-by-ref pending PDF verification.

## Cross-cutting design decisions

### `SpectralHandle` opaque type

```python
@dataclass(frozen=True)
class SpectralHandle:
    substrate_descriptor_path: str   # relative path to attested-root TOML
    substrate_descriptor_hash: str   # 64-hex; Class A SHA-256 of canonical descriptor
    eigenbasis_cache_key: str        # 64-hex; SHA-256(descriptor_hash || laplacian_kind)
    coefficients_bytes: bytes        # BSC-encoded D-bit/D-byte hypervector (Class M)
    content_sha: str                 # 64-hex; Class A SHA-256(coefficients_bytes)
    D_bits: int                      # substrate-coupling magnitude
```

Substrate-descriptor + content-SHA-keyed eigenbasis cache (per Spike #112). Matches MPR-v1 attestation pattern (descriptor bytes → SHA-256 → hash key). Eigenbasis cache is keyed by descriptor+kind, NOT by per-state content (eigenbasis is one-time O(n³) substrate work; coefficients are O(n²) per-state cheap work). `content_sha` enables substrate-mismatch detection at delta-time.

### Caching strategy

| Cache | Key | Cost class | Lifetime |
|---|---|---|---|
| Eigenbasis | `(substrate_descriptor_hash, laplacian_kind)` | O(n³) one-time | Module-level LRU, bounded `N_MAX_EIGENBASES=8` |
| Coefficients | none | O(n²) per state | Recomputed each `decompose()` call |
| Delta | none | O(D) per pair | Returned directly to caller |

Persistent (on-disk) eigenbasis-as-MPR-attested artefact is out of scope for v0.4.x; future spike. Explicit `srmech.spectral.clear_eigenbasis_cache()` helper for test isolation.

### Error-handling hierarchy

- `SpectralError(ValueError)` — base class (mirrors `srmech.amsc.hdc` and `srmech.amsc.laplacian` ValueError-derived convention).
- `SubstrateMismatchError` — `delta` / `similarity` / `prediction_error` when handles' `substrate_descriptor_hash` differ.
- `UnsupportedSubstrateError` — `decompose` when `substrate.laplacian_kind` is unknown to Class L (e.g. fractional-Laplacian; Spike #119+).
- `EncoderFailureError` — `decompose` when substrate-specific encoder fails (e.g. state shape mismatches `descriptor.n_nodes`).
- `DimensionMismatchError` — `delta` / `similarity` when `D_bits` disagree (Class M precondition).
- `EmptyHistoryError` — `predict` when `handle_history` is empty.

### C/Python parity split

Every Class A–N primitive earns a C surface per `[[feedback_no_binding_layer_carveout]]`. `srmech.spectral.*` is a **composition layer**, not a new primitive class — therefore the 7 entries themselves are Python wrappers composing existing libsrmech symbols. Net-new C primitives are required for two sub-ops and are explicitly enumerated (not waived):

| Entry | Composition | Net-new C primitive required? |
|---|---|---|
| `decompose` | Class L `hermitian_eigendecompose` + substrate encoder (Py) + Class A SHA-256 | none |
| `delta` | Class M `srmech_hdc_bind` (Spike #114 Option B) | none |
| `recompose` | Class L `dense_matvec_complex` + Class M bind for delta-application + substrate decoder (Py) | none |
| `predict` | Class C `cascade_extrapolate` + Class L row-select | **`srmech_c_cascade_extrapolate` (Spike #113)** |
| `prediction_error` | Class M bind + Class K gate | **`srmech_k_gate_by_threshold` (Spike #117 / #118)** |
| `truncate_sparse` | Class K `sparse_truncate` | **`srmech_k_sparse_truncate` (Spike #117)** |
| `similarity` | Class M `srmech_hdc_similarity` | none |

Per `[[feedback_no_mvp_framing]]`: deferring entries 4/5/6 to rcN+2 with their prereq spikes named IS full-coverage by enumeration, not minimum-viable carve-out.

## Per-entry specifications

The tool-schema entries below use the existing `srmech.amsc.tool_schema.ToolEntry` shape (Phase C1 rc12; same dataclass shape currently registering 87 entries). New `category="spectral"` taxonomy hint.

### 1. `srmech.spectral.decompose`

```python
ToolEntry(
    name="srmech.spectral.decompose", owner="srmech", category="spectral",
    summary="Decompose a substrate state into spectral coefficients via Class L "
            "eigenbasis projection. Substrate descriptor + Laplacian kind determine "
            "the eigenbasis (cached by content-SHA per Spike #112). Returns "
            "SpectralHandle for downstream delta / recompose / similarity. "
            "Chung 1997 §1-2; Golub & Van Loan §8.5.",
    parameters=(P("state", "bytes | np.ndarray", True),
                P("substrate", "SpectralSubstrate", True)),
    returns=R("SpectralHandle", "dataclass with coefficients_bytes + cache keys"),
)
```

- **Class chain**: L (eigenbasis) + A (descriptor hash for cache key)
- **Canonical SSoT**: Chung (1997) *Spectral Graph Theory* §1–2; Golub & Van Loan (1996) *Matrix Computations* §8.5 (textbooks; cite-by-ref); chess-spectral §5 for cross-substrate generalisation locator (in-repo verifiable).
- **Substrate-coupling**: `descriptor_path`, `laplacian_kind`, `n_nodes`, encoder choice (delegated to `substrate.encoder_id`).
- **Implementation**: `srmech/spectral/decompose.py`
- **Test plan**: (a) `recompose(decompose(state, s)) == state` at 9.29e-17 tolerance per chess-spectral §5b on 4 substrates; (b) cache hit/miss verification; (c) substrate-coupling test (same state, two Laplacian kinds, two handles).

### 2. `srmech.spectral.delta`

```python
ToolEntry(
    name="srmech.spectral.delta", owner="srmech", category="spectral",
    summary="Bit-exact delta between two encoded spectral coefficient vectors via "
            "Class M HDC bind (XOR). Option B: directly on encoded bytes, no "
            "re-encoding (1.22x speedup vs wrapper, identity-not-implementation "
            "aligned per Spike #114). Plate 1995 §3.2; Kanerva 2009 §3.2.",
    parameters=(P("ref_coeffs", "bytes", True, "encoded coefficient vector"),
                P("current_coeffs", "bytes", True, "same D_bits as ref_coeffs")),
    returns=R("bytes", "delta vector (D_bits)"),
)
```

- **Class chain**: M (bind)
- **Canonical SSoT**: Plate (1995) *Holographic Reduced Representations* IEEE TNN 6:623, §3.2; Kanerva (2009) *Hyperdimensional Computing* Cogn Comput 1:139, §3.2 (both paywall cite-by-ref; both verified citations already present in `srmech.amsc.hdc` module docstring).
- **Substrate-coupling**: `D_bits`, BSC encoding scheme.
- **Implementation**: `srmech/spectral/delta.py` (thin wrapper around `srmech.amsc.hdc.bind`)
- **Test plan**: bit-exact 4/4 substrates per Spike #114 (chess D=768, image D=4096, ephemeris D=384, gear-DAG D=96); self-inversion + commutativity; native parity vs Python fallback.

### 3. `srmech.spectral.recompose`

```python
ToolEntry(
    name="srmech.spectral.recompose", owner="srmech", category="spectral",
    summary="Reconstruct substrate state from a SpectralHandle, optionally applying "
            "a sequence of bind-deltas before decode. Inverse of decompose; "
            "chess-spectral §5b verified at machine-zero (9.29e-17). Chung 1997 §1-2.",
    parameters=(P("handle", "SpectralHandle", True),
                P("deltas", "Sequence[bytes]", False, "default empty")),
    returns=R("bytes | np.ndarray", "reconstructed state (encoded or decoded)"),
)
```

- **Class chain**: M (bind to apply deltas) + L (`dense_matvec_complex` for U @ c)
- **Canonical SSoT**: Chung (1997) *Spectral Graph Theory* §1–2 (inverse projection f = U c).
- **Substrate-coupling**: substrate decoder, `D_bits`, coefficient quantum.
- **Implementation**: `srmech/spectral/recompose.py`
- **Test plan**: (a) roundtrip at machine-zero 9.29e-17; (b) delta-chain composition; (c) empty-deltas case.

### 4. `srmech.spectral.predict`

```python
ToolEntry(
    name="srmech.spectral.predict", owner="srmech", category="spectral",
    summary="Generate a predicted next-state SpectralHandle by extrapolating from a "
            "coefficient history. Default predictor is Class C cascade_extrapolate "
            "(Rao-Ballard 1999; Friston 2010 free-energy framing). Predictor is a "
            "substrate-coupling input. Requires Spike #113 close.",
    parameters=(P("handle_history", "Sequence[SpectralHandle]", True),
                P("predictor", "Callable | str", False, "default 'cascade_extrapolate'")),
    returns=R("SpectralHandle", "predicted handle"),
)
```

- **Class chain**: C (`cascade_extrapolate`) + L (eigenbasis preserved from `history[-1]`)
- **Canonical SSoT**: Rao & Ballard (1999) *Nat Neurosci* 2(1):79–87 (predictive coding); Friston (2010) *Nat Rev Neurosci* 11(2):127–138 (free-energy). Friston 2010 verified prior in `srmech spike_46_round1_references.ndjson`; Rao-Ballard 1999 cite-by-ref pending PDF verification at Spike #113.
- **Substrate-coupling**: predictor function, `n_history_samples`, substrate descriptor.
- **Implementation**: `srmech/spectral/predict.py` (deferred to Spike #113 close)
- **Test plan**: (a) trivial-predictor identity; (b) cascade-extrapolate on circular-orbit ephemeris; (c) mixed-substrate history raises; (d) empty history raises.

### 5. `srmech.spectral.prediction_error`

```python
ToolEntry(
    name="srmech.spectral.prediction_error", owner="srmech", category="spectral",
    summary="Spectral prediction error as Class M bind(observed, predicted), "
            "optionally gated by Class K threshold (Lisman-Grace 2005 hippocampal "
            "novelty-filter analog; Rao-Ballard 1999 error spectrum).",
    parameters=(P("observed", "SpectralHandle", True),
                P("predicted", "SpectralHandle", True),
                P("threshold", "float", False, "default 0.0; below ⇒ zero vector")),
    returns=R("bytes", "error vector (D_bits)"),
)
```

- **Class chain**: M (bind) + K (`gate_by_threshold`; Spike #117/#118 scope)
- **Canonical SSoT**: Rao & Ballard (1999) *Nat Neurosci* 2(1):79–87; Lisman & Grace (2005) *Neuron* 46(5):703–713 (hippocampal novelty gate; cite-by-ref pending); Friston (2010) *Nat Rev Neurosci* 11(2):127–138.
- **Substrate-coupling**: threshold (substrate-specific significance cutoff), substrate descriptor.
- **Implementation**: `srmech/spectral/prediction_error.py`
- **Test plan**: (a) perfect-prediction → all-zero; (b) one-bit-error → hamming-weight-1; (c) below-threshold gating returns zero-vector; (d) substrate-mismatch raises.

### 6. `srmech.spectral.truncate_sparse`

```python
ToolEntry(
    name="srmech.spectral.truncate_sparse", owner="srmech", category="spectral",
    summary="Class K asymptotic-DOF compression: keep top-k coefficients (int "
            "input) or |c_i| ≥ threshold (float input). Olshausen-Field 1996 "
            "sparse-coding analog. Lossy with bounded reconstruction error. "
            "Requires Spike #117 close.",
    parameters=(P("handle", "SpectralHandle", True),
                P("k_or_threshold", "int | float", True)),
    returns=R("SpectralHandle", "truncated handle (same substrate)"),
)
```

- **Class chain**: K (`sparse_truncate`; new sub-op per Spike #117)
- **Canonical SSoT**: Olshausen & Field (1996) *Nature* 381(6583):607–609 (cite-by-ref paywall; PDF verification deferred to Spike #117).
- **Substrate-coupling**: k or threshold, `D_bits`, substrate descriptor.
- **Implementation**: `srmech/spectral/truncate_sparse.py` (deferred to Spike #117 close)
- **Test plan**: (a) k=D no-op; (b) k=0 zero-coefficient; (c) top-k preserves argmax-set; (d) Parseval reconstruction-error bound.

### 7. `srmech.spectral.similarity`

```python
ToolEntry(
    name="srmech.spectral.similarity", owner="srmech", category="spectral",
    summary="HDC similarity between two SpectralHandles' coefficient vectors via "
            "Class M: 1 − 2·hamming(a, b)/D ∈ [−1, +1]. +1 identical; 0 orthogonal; "
            "−1 complementary. Substrate-mismatch raises. Kanerva 2009 §3.2.",
    parameters=(P("handle_a", "SpectralHandle", True),
                P("handle_b", "SpectralHandle", True)),
    returns=R("float", "in [-1, +1]"),
)
```

- **Class chain**: M (`similarity`; existing libsrmech `srmech_hdc_similarity`)
- **Canonical SSoT**: Kanerva (2009) *Hyperdimensional Computing* §3.2; Plate (1995) *HRR* §3.2 (both already cited in `srmech.amsc.hdc` docstring).
- **Substrate-coupling**: `D_bits`, substrate descriptor (both handles must match).
- **Implementation**: `srmech/spectral/similarity.py` (thin wrapper around `srmech.amsc.hdc.similarity`)
- **Test plan**: (a) self-identity = +1; (b) complement = −1; (c) orthogonality at D=1024 within ±3σ; (d) substrate-mismatch raises; (e) native parity.

## File layout

```
srmech/spectral/
├── __init__.py              # exports + _register_spectral_tools()
├── handle.py                # SpectralHandle, SpectralSubstrate, eigenbasis LRU
├── decompose.py             # entry 1
├── delta.py                 # entry 2
├── recompose.py             # entry 3
├── predict.py               # entry 4 (after Spike #113)
├── prediction_error.py      # entry 5
├── truncate_sparse.py       # entry 6 (after Spike #117)
└── similarity.py            # entry 7
```

`srmech/amsc/tool_schema.py` adds `_register_spectral_tools()` called from registration entrypoint — same pattern as `_register_amsc_tools` / `_register_qm_tools`.

## RC registration strategy

Per `[[feedback_rc_stacking_versioning]]`, two-rc ship:

- **rcN+1** (alongside Phase C1 close per user scope decision 2026-05-18): register entries 1/2/3/7 (`decompose`, `delta`, `recompose`, `similarity`). All four are fully shippable today — Class L shipped Phase C1 rc2, Class M shipped Phase C1 rc8, Class A SHA-256 shipped Phase B.
- **rcN+2**: register entries 4/5/6 (`predict`, `prediction_error`, `truncate_sparse`) after Spike #113 (cascade_extrapolate) and Spike #117 (sparse_truncate + gate_by_threshold) close.

Both rcs accumulate cleanly toward `srmech v0.4.0` production tag per the rc-stacking discipline. Per `[[feedback_no_mvp_framing]]`: this IS full-coverage by enumeration — every entry's path-to-ship is named, with prereq spikes explicitly cited. Not minimum-viable carve-out.

## Anomaly check

| Discipline | Status |
|---|---|
| New primitive class promoted? | No. Vocabulary stays at 14 classes A–N. |
| Identity-not-implementation? | Yes. Each entry IS its class composition (decompose IS Class L projection; delta IS Class M bind; etc.). |
| Algebra-not-magnitude? | Yes. Tool-schema describes algebra; D / k / threshold / predictor are substrate-coupling inputs. |
| Binding-layer carve-out? | No. Net-new C primitives (cascade_extrapolate, sparse_truncate) enumerated, deferred to Spike #113 + #117 — not waived. |
| Citation hygiene? | Yes. Every paywall reference marked cite-by-ref; Friston 2010 and Plate 1995 / Kanerva 2009 already verified in srmech sources. |
| Science is SSoT? | Yes. Every `canonical_ssot` cites published literature; chess-spectral §5b cited only as cross-substrate-generalisation locator. |
| CAD-grade scope creep? | No. All entries are algebra/eigenbasis. |

## Fermatas — for conductor decision

1. **Two-rc strategy OK?** Recommended: ship rcN+1 with entries 1/2/3/7 alongside Phase C1 close; ship rcN+2 with entries 4/5/6 after Spike #113 + #117 close. Per `[[feedback_no_mvp_framing]]` this is full-coverage-by-enumeration, not soft-MVP.
2. **`SpectralHandle` dataclass shape**: 5 fields + `D_bits` proposed. If the eigenbasis cache should fold `laplacian_kind` directly into `descriptor_hash` rather than as a second cache-key component, that's a one-line change here. Conductor's call.
3. **Entry 5 prediction_error gate**: currently composes M + K. If Class K gate-by-threshold is deemed inappropriate (Class K is asymptotic-DOF; a hard threshold gate is more naturally a free-standing predicate), the `threshold` parameter can be optional with `default=0.0` meaning "no gate, return raw bind" — current spec accommodates this.

## Discipline closure

- **Math doesn't lie**: every entry's class-chain composition is verified — bind self-inversion (Spike #114), Class L roundtrip 9.29e-17 (chess-spectral §5b), Class M similarity bounded [-1, +1] (Kanerva §3.2).
- **No new class promoted**: vocabulary stays at 14 classes A–N. `srmech.spectral.*` is composition layer above `srmech.amsc.*`, not new primitive.
- **No CAD-grade scope creep**: all entries are algebra/eigenbasis per srmech `docs/srmech/CLAUDE.md` discipline.
- **No vapourware**: entries deferred to rcN+2 are enumerated with prereq spike citations.

## Deliverables emitted

- `docs/srmech/notes/spike115_findings_2026-05-18.ndjson` (15 records: framing + 5 cross-cutting + 7 entry_spec + namespace_layout + anomaly_check + verdict)
- `docs/srmech/notes/spike115_concertmaster_tool_schema_surface_design.md` (this file)

No PR, no commit. Worktree-only per scoping-spike convention.
