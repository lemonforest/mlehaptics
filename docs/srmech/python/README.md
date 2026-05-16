# srmech

**Status:** **v0.4.0 on PyPI** (Task #217 Phase C1 close — full 14-class C-parity primitive vocabulary + canonical QM/QFT/SM operations layer on top of the AMSC framework). The Phase C1 rc-stack accumulated as `0.4.0rc1` → `0.4.0rc12` on TestPyPI before the clean-semver ship.

`srmech` (Stored-Relationship Mechanism) is a research package shipping three load-bearing surfaces:

1. **14-class primitive vocabulary** — every Spike #24 primitive class with both a Python wrapper (`srmech.amsc.*`) and a native C surface (`srmech_*` symbols in `libsrmech.{so,dll,dylib}`). Classes: A (content-addressing / SHA-256), B (TLV byte-canonical), C (streaming / NDJSON), D (multi-needle dispatch), E (catalog sorted-key lookup), F (template `{key}` substitution), G (byte-pattern search), H (self-introspection), I (cyclic-group / modular arithmetic), J (prime-factorisation / period), K (equation-of-centre / pin-slot — Kepler shape), L (graph Laplacian; pi-free Jacobi), M (HDC binary spatter codes), N (rational-approximation / continued-fraction convergents). JPL Power-of-Ten compliant; cibuildwheel matrix (Linux / macOS / Windows × py3.10–3.14); pure-Python fallback for Pyodide / WASM.

2. **Canonical QM/QFT/SM operations layer** (`srmech.qm.*`) — sourced from canonical physics literature (Schrödinger / Heisenberg / Pauli / Dirac / Klein-Gordon / Feynman / Yang-Mills / Gell-Mann / Wilson / Glashow-Weinberg-Salam / Higgs / Cabibbo-Kobayashi-Maskawa / Bender-Boettcher / Mostafazadeh) per the "science is the SSoT of science" discipline. Modules: `single_particle` (TDSE / TISE / Heisenberg / lattice momentum / Liouville-vN), `spin` (Pauli matrices + Clifford Cl(0,3)), `potentials` (hydrogen radial + harmonic oscillator), `relativistic` (Dirac γ-matrices + Weyl projectors + charge conjugation + Klein-Gordon), `propagators` (Feynman scalar / fermion / photon / massive vector), `pseudo_hermitian` (η-deformed inner product framework — closes chess-spectral ADR-005 gap), `gauge` (SU(2) / SU(3) Gell-Mann generators + Casimirs + Wilson loops), `sm` (Higgs vev + W/Z masses + Weinberg relation + Yukawa + CKM).

3. **Attested Multi-Source Collector/Catalog (AMSC) framework** — Mathematical Provenance Record (MPR) v1 on-disk format, descriptor TOML loader, six fetch/parse adapters, and a universal catalog bridge surface that downstream packages register their own catalog SSOTs with at import time.

**Tool-schema introspection** (`srmech.amsc.tool_schema`) surfaces all ~87 operations to LLM consumers with canonical-SSoT-cited summaries — every primitive class and every `srmech.qm.*` operation is discoverable without reading the implementation.

### Why "Collector/Catalog"?

Both readings of **AMSC** are correct and the abbreviation is the same either way:

- At **collection time** (T1 / T3 lifecycle stages — fetch / live-query / re-bake), the adapter classes are *collecting* attested rows from upstream archives. The framework's name describes what it's doing in that moment: **Attested Multi-Source Collector**.
- After collection, the resulting NDJSON SSOTs are a *catalog* of attested data — committed into the package, registered into the universal bridge by downstream consumers, queryable through `list_attested_sources()` / `get_attested_dataset()`. The same framework name describes the post-collection state: **Attested Multi-Source Catalog**.

Both names abbreviate to AMSC. Pick whichever fits the lifecycle stage you're describing — the framework is one thing wearing two hats.

The package was extracted from `ephemerides-spectral`'s `_research/` mirror in Task #197 so that other spectral-research packages can consume the AMSC framework without depending on ephemerides-spectral. The catalog SSOTs themselves do NOT migrate — each downstream package registers its own root via `srmech.amsc.catalog.register_attested_root(path, source=...)`.

## Public API

**AMSC framework + bridge surfaces**:

```python
from srmech.amsc import (
    MPRRecord, MPR_SCHEMA_VERSION, read_ndjson, write_ndjson, sha256_bytes,
    Descriptor, load_descriptor, discover_descriptors, render_template, descriptor_hash,
    list_attested_sources, get_attested_dataset, get_attested_descriptor,
    attestation_audit, register_attested_root, list_registered_roots,
    use_local_kernel, clear_local_kernel, get_local_kernel_state,
)
```

**14-class primitive vocabulary** (each available as `srmech.amsc.<module>` with native C dispatch + Python fallback):

```python
from srmech.amsc import (
    cyclic,     # Class I: gcd, lcm, mod_add, mod_mul, mod_pow, mod_inv
    laplacian,  # Class L: dense_adjacency, dense_laplacian, normalized_laplacian, jacobi_eigvals
    primes,     # Class J: is_prime, factor, cyclic_period
    tlv,        # Class B: tlv_pack
    search,     # Class G: byte_search
    dispatch,   # Class D: match
    naming,     # Class E: lookup
    template,   # Class F: render
    rational,   # Class N: continued_fraction, best_rational
    kepler,     # Class K: pin_slot, kepler_solve, equation_of_centre
    hdc,        # Class M: bind, bundle, permute, similarity
)
```

**Canonical QM/QFT/SM operations layer**:

```python
from srmech.qm import (
    single_particle,    # TDSE, TISE, Heisenberg, lattice_momentum, density_matrix, liouville_evolve
    spin,               # pauli_matrices, pauli_clifford_residuals, pauli_spin_operator
    potentials,         # hydrogen_radial, harmonic_oscillator_ladder, harmonic_oscillator_hamiltonian
    relativistic,       # gamma_matrices, gamma_5, weyl_left/right_projector, dirac_operator_momentum_space
    propagators,        # feynman_scalar/fermion/photon/massive_vector_propagator
    pseudo_hermitian,   # inner_product_eta, expectation_eta, is_pseudo_hermitian, construct_eta_from_eigendecomposition
    gauge,              # su2/su3_generators, su2/su3_structure_constants, casimir_operator, wilson_loop_from_segments
    sm,                 # higgs_vev, weak_mixing_angle, w/z_boson_mass, weinberg_relation_residual, ckm_matrix
)
```

**Tool-schema introspection**:

```python
from srmech.amsc.tool_schema import get_tool_schema, tool_schema_view

schema = get_tool_schema()                # ~87 ToolEntry objects
for tool in schema.tools:
    print(tool.name, "—", tool.summary)   # canonical-SSoT-cited summaries

json_view = tool_schema_view()            # JSON-serialisable view
```

## Cross-package catalog registration

The load-bearing API for cross-package use:

```python
from pathlib import Path
from srmech.amsc import catalog as _amsc_catalog

_amsc_catalog.register_attested_root(
    Path(__file__).resolve().parent / "_research" / "attested",
    source="ephemerides-spectral",
)
```

Call this once at package-import time. Subsequent `list_attested_sources()`, `get_attested_dataset()`, etc. enumerate the union of srmech's own `amsc/attested/` plus every registered root, in registration order. Duplicate `source_key` resolves first-registered-wins with a warning.

## Adapter classes

Six adapters cover the realistic source space:

| adapter | class | network? |
|---|---|---|
| `html_scraper` | fetched | yes (BeautifulSoup) |
| `json_api` | fetched | yes (paginated JSON) |
| `csv_bulk` | fetched | yes (CSV/XYZ bulk) |
| `netcdf_grid` | fetched | stub (gated behind extras) |
| `geotiff_bbox` | fetched | stub (gated behind extras) |
| `literature_curated` | curated | no (NDJSON committed directly) |

The `curated` class never touches the network: rows are committed as data-only NDJSON and srmech synthesises full MPR attestation blocks at read time from each row's per-row DOI.

## Install

```bash
pip install srmech                  # core (no jsonschema, no network adapters)
pip install srmech[validation]      # adds jsonschema for strict data-block validation
pip install srmech[collectors]      # adds requests + beautifulsoup4 for fetched adapters
pip install srmech[dev]             # everything
```

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
