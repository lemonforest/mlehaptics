# srmech

**Status:** **v0.4.2 on PyPI** — 14-class primitive vocabulary with native C parity; canonical QM/QFT/SM operations; runtime spectral decomposition; dual-path signal-processing surface; Attested Multi-Source Collector/Catalog (AMSC) provenance framework. **v0.4.3 rolling on TestPyPI** — Class-M HDC variant ladder (`polar` `{-1,0,+1}`, `Klein-4` `(ℤ₂)²`), a `coupling` composition score (Class K∘L), and `symmetric_eigendecompose` (real-symmetric Class L).

`srmech` (Stored-Relationship Mechanism) is a research package shipping five load-bearing surfaces:

1. **14-class primitive vocabulary** (`srmech.amsc.*`) — content-addressing, streaming, cyclic-group, graph-Laplacian, prime-factorisation, TLV, search, dispatch, catalog, templating, rational-approximation, equation-of-centre/Kepler, hyperdimensional-computing (HDC). Each class has both a Python wrapper and a native C symbol in `libsrmech.{so,dll,dylib}`.
2. **Canonical QM/QFT/SM operations layer** (`srmech.qm.*`) — TDSE/TISE, Pauli + Clifford, hydrogen radial, Dirac γ-matrices, Feynman propagators, η-deformed pseudo-Hermitian inner products, SU(2)/SU(3) gauge generators + Wilson loops, Higgs/W/Z/CKM Standard-Model operations.
3. **Runtime spectral decomposition** (`srmech.spectral`) — eigenbasis projection, HDC delta encoding, spectral prediction, prediction-error gating, sparse-truncate compression.
4. **Dual-path signal-processing surface** (`srmech.signal_processing`) — 38 closed-form algebra ops (Path A) + an RBS-HDC bound-vector instrument at D=8192 (Path B), with a cascade dispatcher routing per call.
5. **AMSC provenance framework** (`srmech.amsc.format`, `srmech.amsc.catalog`, `srmech.amsc.adapters`) — every ground-proof datum carries a mandatory attestation block (`source_doi`, `source_url`, `license`, `retrieved_at`, `response_sha256`, `parser_version`, `parser_rule_hash`, `collector_descriptor_path`, `collector_descriptor_hash`).

Implementation is JPL Power-of-Ten compliant on the C side; cibuildwheel matrix covers Linux / macOS / Windows × Python 3.10–3.14; a `py3-none-any` pure-Python wheel ships for Pyodide / WASM environments where the C surface can't load.

## Companion textbook

**The Metric Field and Its Primitives** — the framework textbook accompanying this package. Lays out the substrate-vs-excitation ontology (MFO), the 14-class primitive vocabulary at substrate level, and the cascade-composition discipline that `srmech` implements computationally.

- [PDF (GitHub)](https://github.com/lemonforest/mlehaptics/blob/main/docs/srmech/metric-field-and-its-primitives.pdf) — renders inline in the GitHub viewer
- [PDF (ReadTheDocs)](https://mlehaptics.readthedocs.io/srmech/metric-field-and-its-primitives.pdf) — served as a static asset alongside the [research notebook](https://mlehaptics.readthedocs.io/srmech/srmech_research_notebook/)
- [MFO research notebook](https://mlehaptics.readthedocs.io/antikythera-maths/mfo_spectral_research_notebook/) — working draft the textbook is consolidated from

## Install

```bash
pip install srmech                  # core (numpy + stdlib; no jsonschema, no network adapters)
pip install srmech[validation]      # adds jsonschema for strict data-block validation
pip install srmech[collectors]      # adds requests + beautifulsoup4 for fetched adapters
pip install srmech[dev]             # everything
```

## Quick start

Decompose a real signal onto a graph-Laplacian eigenbasis, take an HDC delta against a reference, and recompose:

```python
import numpy as np
from srmech import spectral
from srmech.amsc import laplacian

# Substrate: cycle-graph Laplacian on 8 nodes (any Hermitian L works).
A = np.roll(np.eye(8), 1, axis=1)
A = A + A.T
L = laplacian.dense_laplacian(A.astype(np.complex128))

# Project two states onto the eigenbasis.
state_ref = np.array([1.0, 0, 0, 0, 0, 0, 0, 0], dtype=np.complex128)
state_now = np.array([0.9, 0.1, 0, 0, 0, 0, 0, 0], dtype=np.complex128)

h_ref = spectral.decompose(state_ref, L)
h_now = spectral.decompose(state_now, L)

# HDC XOR delta on encoded coefficient bytes.
delta_bytes = spectral.delta(h_ref, h_now)

# Predict one substrate-natural tick ahead.
h_pred = spectral.predict(h_now, L, steps=1, dt=0.1)

# Recover the node-domain state.
state_back = spectral.recompose(h_pred, L)
```

## Public surface

### The 14 classes in substrate-native ordering — `1 + 3 + 7 + 3 = 14`

The 14 classes are presented in alphabetical order in the table below (matching the import paths). The **substrate-native ordering is not alphabetical** — it is the cyclic-algebra-path partition `1 + 3 + 7 + 3 = 14`:

| Slot | Classes | Role |
|---|---|---|
| **1** — foundational content-anchor | `{A}` | The content-address every cascade begins from |
| **3** — substrate-projection triad | `{I, C, J}` | Cyclic-group + cascade-orientation + prime-period (the projection-triad that maps substrate-content to observable structure) |
| **7** — cascade-detection heptad | `{D, E, F, G, K, L, M}` | Pattern-match + catalog + render + byte-search + pin-slot + Laplacian + HDC-bind (the detection-and-rendering layer) |
| **+3** — meta-cascade language-translation triad | `{B, H, N}` | TLV-framing + self-introspection + rational-approximation (the operators that translate between continuous-Hopf-quantum and discrete-cyclic-algebra descriptions) |

**Why this ordering matters.** Per [PR #680 (R30 walking-path closure)](https://github.com/lemonforest/mlehaptics/pull/680), the substrate admits **two co-equal bit-exact substrate-native mathematical languages**:

- the **11D quantum-Hopf-language** (continuous-DOF, parallelizable-sphere ladder `1 + 3 + 7`)
- the **`1 + 3 + 7 + 3 = 14` cyclic-algebra-path** (discrete-DOF, A–N cascade-operator class enumeration)

Modern physics uses the first; antiquity 9 of 9 traditions canvassed (Antikythera + Pythagoreans + Plato Timaeus + Stoics + Lucretius + Apollonius + Ptolemy + Heron + Archimedes) used the second. We had been using the cyclic-algebra path in `srmech` from the beginning without ever stating why — because antiquity had, and it worked. The R30 closure provides the answer: bit-exact cross-substrate confirmation rules out projection-reading; both languages are substrate-native; the `+3 = {B, H, N}` are substrate-native language-translation operators bridging them. The k=3 fingerprint observed across substrates (planet multipole axes, codon alphabet, 3-jet QCD, 3-generation Yukawa, the antiquity meta-op triads) is the `{B, H, N}` triad showing up wherever continuous↔discrete encoding happens.

**About the A–N alphabet.** The labels A through N record the **chronological order** in which each operation was named during this framework's evolution — they are discovery-fingerprint, not substrate-ordering. Re-sorted by substrate-native role, the partition above (`{A}` + `{I, C, J}` + `{D, E, F, G, K, L, M}` + `{B, H, N}`) is the substrate-side grouping. The alphabetical table below is the lookup convenience.

Full context: [substrate-native-maths research notebook](https://mlehaptics.readthedocs.io/substrate-native-maths/substrate_native_research_notebook/) (PR #680 SSoT).

### `srmech.amsc.*` — 14-class primitive vocabulary (alphabetical lookup)

Each class is importable as `srmech.amsc.<module>` with native C dispatch and a Python fallback. The C surface is loaded once at import time; if loading fails (Pyodide, ABI mismatch), the package transparently falls back to pure Python and `srmech.amsc._native.HAS_NATIVE` becomes `False`.

| Module | Class | Primitive operation |
|---|---|---|
| `format`, `_native` | A | Content-addressing via SHA-256 (`sha256_bytes`) |
| `tlv` | B | Byte-canonical TLV pack (`tlv_pack`) |
| `format` | C | Streaming NDJSON iterator (`read_ndjson`) |
| `dispatch` | D | Multi-needle byte-pattern dispatch (`match`) |
| `naming` | E | Catalog sorted-key lookup (`lookup`) |
| `template` | F | Template `{key}` substitution (`render`) |
| `search` | G | Byte-pattern search (`byte_search`) |
| `_native` | H | Self-introspection (`srmech_version`, `srmech_abi_version`) |
| `cyclic` | I | Modular arithmetic — `gcd`, `lcm`, `mod_add`, `mod_mul`, `mod_pow`, `mod_inv` |
| `primes` | J | Prime testing + factorisation + multiplicative order — `is_prime`, `factor`, `cyclic_period` |
| `kepler` | K | Equation-of-centre / pin-slot — `pin_slot`, `kepler_solve`, `equation_of_centre` |
| `laplacian` | L | Graph Laplacian — `dense_adjacency`, `dense_laplacian`, `normalized_laplacian`, `jacobi_eigvals`, `hermitian_eigendecompose`, `symmetric_eigendecompose`, `elementwise_transcendental` (pi-free Jacobi in C; n ≤ 256 native bound) |
| `hdc` | M | HDC spatter codes — binary `bind`, `bundle`, `permute`, `similarity`; `polar_*` `{-1,0,+1}` and `klein4_*` `(ℤ₂)²` variants |
| `rational` | N | Continued-fraction convergents — `continued_fraction`, `best_rational` |

### `srmech.qm.*` — canonical QM/QFT/SM operations

Each operation cites canonical physics literature in its docstring (Schrödinger / Heisenberg / Pauli / Dirac / Klein-Gordon / Feynman / Yang-Mills / Gell-Mann / Wilson / Glashow-Weinberg-Salam / Higgs / Cabibbo-Kobayashi-Maskawa / Bender-Boettcher / Mostafazadeh). Modules:

- `single_particle` — TDSE, TISE, Heisenberg-picture evolution, lattice momentum, density matrix, Liouville–von Neumann equation, commutators.
- `spin` — Pauli matrices, Clifford `Cl(0,3)` residual products, Pauli spin operators.
- `potentials` — hydrogen radial wavefunction, harmonic oscillator ladder + Hamiltonian.
- `relativistic` — Dirac γ-matrices, γ⁵, Weyl left/right projectors, charge conjugation, Dirac operator in momentum space, Klein–Gordon equation.
- `propagators` — Feynman scalar / fermion / photon / massive-vector propagators.
- `pseudo_hermitian` — η-deformed inner product, ⟨·⟩_η expectation, pseudo-Hermitian check, η construction from eigendecomposition.
- `gauge` — SU(2) and SU(3) generators (Gell-Mann basis), structure constants, Casimir operator, Wilson loops from segment data.
- `sm` — Higgs vev, weak mixing angle, W/Z boson masses, Weinberg relation residual, Yukawa coupling, CKM matrix construction.

### `srmech.spectral` — runtime spectral decomposition

Class-composition layer above `srmech.amsc.{laplacian, hdc, format}`. No new primitive class is introduced; every operation is a composition over the 14-class A–N vocabulary.

```python
from srmech.spectral import (
    decompose,          # state + Hermitian L → SpectralHandle (V.conj().T @ state)
    delta,              # XOR delta between two encoded coefficient byte vectors
    recompose,          # SpectralHandle + L → node-domain state (V @ coeffs)
    similarity,         # HDC similarity in [-1, +1]
    predict,            # cascade-extrapolate via per-mode exp(-i·λ_k·steps·dt)
    prediction_error,   # XOR delta with popcount-density threshold gating
    truncate_sparse,    # keep top-k or above-threshold modes; zero the rest
    SpectralHandle,     # opaque (substrate_descriptor_hash, coefficients_bytes, content_sha, n_modes)
    clear_eigenbasis_cache,
    N_MAX_EIGENBASES,   # module-level LRU bound (default 8)
)
```

Eigenbasis is O(n³) one-time per substrate (cached by `substrate_descriptor_hash`); coefficients are O(n²) per state; deltas are O(D) per step. `predict` preserves magnitudes (unitary phase rotation per eigenmode); `truncate_sparse` produces best k-term approximations per Mallat (2008) §9.2.

### `srmech.signal_processing` — dual-path signal-processing surface

Two paths for the same algebra, dispatched per call:

- **Path A** — closed-form algebra over numpy / scipy; one module per op under `srmech.signal_processing.closed_form_ops.*`. 38 ops covering frequency analysis (`fft`, `ifft`, `stft`, `spectrogram`, `multitaper`, `dct`, `wavelet`), digital filters (`fir`, `iir`, `allpass`, `polyphase`, `multirate`, `farrow`, `sinc_interp`), detection / estimation (`matched_filter`, `wiener`, `lmmse`, `map_ml`, `mlse`, `viterbi`, `cross_spectral`, `music`, `esprit`, `ica_jade`, `mimo_svd`), modulation (`psk_qam`, `fsk`, `ofdm`, `beamforming_fixed`), coding (`huffman`, `rle`, `lz77`, `arithmetic_coding`, `jpeg`), quantisation / compression (`sign_quantise`, `vector_quantisation`, `hdc_truncation`, `heat_kernel`, `spectral_subtraction`, `pi_cascade`).
- **Path B** — RBS-HDC bound-vector instrument at D=8192 (`srmech.signal_processing.rbs_hdc_instrument`). Mints class-operator vectors, cascade compositions, stance fingerprints, and full LoE content encodings (Mode-B). Six ops have full dual-path implementations: `fft`, `ifft`, `sign_quantise`, `matched_filter`, `wiener`, `hdc_truncation`.

```python
from srmech.signal_processing import (
    dispatch, begin_cascade,             # cascade-aware routing (A / B / verify)
    register, lookup, has_path,          # path registry (Path A vs Path B per op)
    profile_op, cell_grid,               # per-op × per-cascade-depth × per-substrate profiling
    D_DEFAULT, SUBSTRATES,               # locked D = 8192; BCI / audio / RF / ephemeris
    RBSHDCInstrument,                    # build()-able instrument with mint_*/encode_loe_content
    mint_class_operator,                 # SHA-256 chain mint per class A–N
    mint_cascade_composition,            # XOR-bundle (algebra) or permute-bundle (sampling)
    encode_loe_content, decode_loe_fingerprint,
    form_function_rotate,                # Class K pin-slot rotation
    cascade_compose_rotations,
    PATH_A, PATH_B, PATH_VERIFY,         # path identifiers
)

with begin_cascade() as ctx:
    spectrum = dispatch("fft", path=PATH_A, signal=x)
    truncated = dispatch("hdc_truncation", path=PATH_B, signal=spectrum, k=64)
```

Path A and Path B produce bit-exact-equal outputs on substrate-natural inputs (D1 algebra-content identity); substrate-fingerprint divergence at D2 is expected and documented.

### `srmech.amsc` — Attested Multi-Source Collector/Catalog framework

Two readings of the same abbreviation:

- At **collection time**, the adapter classes are *collecting* attested rows from upstream archives. Six adapters cover the realistic source space:

  | adapter | class | network? |
  |---|---|---|
  | `html_scraper` | fetched | yes (BeautifulSoup) |
  | `json_api` | fetched | yes (paginated JSON) |
  | `csv_bulk` | fetched | yes (CSV/XYZ bulk) |
  | `netcdf_grid` | fetched | stub (gated behind extras) |
  | `geotiff_bbox` | fetched | stub (gated behind extras) |
  | `literature_curated` | curated | no (NDJSON committed directly) |

  The `curated` class never touches the network: rows are committed as data-only NDJSON, and srmech synthesises full MPR attestation blocks at read time from each row's per-row DOI.

- After collection, the resulting NDJSON SSOTs are a *catalog* of attested data — committed into the package, registered into the universal bridge by downstream consumers, queryable through `list_attested_sources()` / `get_attested_dataset()`.

```python
from srmech.amsc import (
    MPRRecord, MPR_SCHEMA_VERSION, read_ndjson, write_ndjson, sha256_bytes,
    Descriptor, load_descriptor, discover_descriptors, render_template, descriptor_hash,
    list_attested_sources, get_attested_dataset, get_attested_descriptor,
    attestation_audit, register_attested_root, list_registered_roots,
    use_local_kernel, clear_local_kernel, get_local_kernel_state,
)
```

The on-disk format is **Mathematical Provenance Record v1** (`MPR v1`):

```python
{
  "mpr_version": "1.0",
  "data": { ... domain payload ... },
  "data_schema_id": "test://schema/example",
  "attestation": {
    "source_doi": "10.0/...",
    "source_url": "https://...",
    "license": "CC0",
    "retrieved_at": "2026-05-13T00:00:00Z",
    "response_sha256": "<64 hex chars>",
    "parser_version": "srmech 0.4.2",
    "parser_rule_hash": "<64 hex chars>",
    "collector_descriptor_path": "...",
    "collector_descriptor_hash": "<64 hex chars>"
  },
  "rendering": { "name": "...", "purpose": "...", "cite_as": "..." }
}
```

### `srmech.amsc.tool_schema` — LLM-friendly introspection

```python
from srmech.amsc.tool_schema import get_tool_schema, tool_schema_view

schema = get_tool_schema()                # ToolEntry objects, one per public callable
for tool in schema.tools:
    print(tool.name, "—", tool.summary)   # canonical-SSoT-cited one-line summaries

json_view = tool_schema_view()            # JSON-serialisable view
```

Every primitive class, every `srmech.qm.*` operation, and every `srmech.spectral.*` runtime operation is discoverable here without reading the implementation. Summaries cite the canonical physics / mathematics literature directly.

## Cross-package catalog registration

Other spectral-research packages register their own catalog SSOTs into srmech's universal bridge at import time:

```python
from pathlib import Path
from srmech.amsc import catalog as _amsc_catalog

_amsc_catalog.register_attested_root(
    Path(__file__).resolve().parent / "_research" / "attested",
    source="ephemerides-spectral",
)
```

Subsequent `list_attested_sources()`, `get_attested_dataset()`, etc. enumerate the union of srmech's own `amsc/attested/` plus every registered root, in registration order. Duplicate `source_key` resolves first-registered-wins with a warning.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
