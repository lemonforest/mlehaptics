# srmech

**Status:** v0.1.0 on PyPI (initial pure-Python ship from the Task #197 AMSC-to-srmech refactor). v0.1.1rc3 → rc9 + v0.2.0rc1 on TestPyPI complete the Task #201 build-out to peer quality with ephemerides-spectral: native C dispatch for SHA-256 + NDJSON line reader, scikit-build-core + CMake build, cibuildwheel matrix (Linux/macOS/Windows × py3.10–3.14), pure-Python fallback for Pyodide / WASM, and JPL Power-of-Ten audit. v0.2.0rc1 cross-package verification against ephemerides-spectral 0.26.1rc1 confirmed green on TestPyPI. **v0.2.0 production cut to PyPI is the only remaining step.**

`srmech` (Stored-Relationship Mechanism) is a research package. It ships the **Attested Multi-Source Collector (AMSC) framework** — the Mathematical Provenance Record (MPR) v1 on-disk format, descriptor TOML loader, six fetch/parse adapters, and a universal catalog bridge surface that downstream packages register their own catalog SSOTs with at import time. **Native C** for the SHA-256 attestation hash + NDJSON streaming reader; pure-Python fallback for Pyodide / WASM environments.

The package was extracted from `ephemerides-spectral`'s `_research/` mirror in Task #197 so that other spectral-research packages can consume the AMSC framework without depending on ephemerides-spectral. The catalog SSOTs themselves do NOT migrate — each downstream package registers its own root via `srmech.amsc.catalog.register_attested_root(path, source=...)`.

## Public API

```python
from srmech.amsc import (
    MPRRecord, MPR_SCHEMA_VERSION, read_ndjson, write_ndjson, sha256_bytes,
    Descriptor, load_descriptor, discover_descriptors, render_template, descriptor_hash,
    list_attested_sources, get_attested_dataset, get_attested_descriptor,
    attestation_audit, register_attested_root, list_registered_roots,
    use_local_kernel, clear_local_kernel, get_local_kernel_state,
)
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
