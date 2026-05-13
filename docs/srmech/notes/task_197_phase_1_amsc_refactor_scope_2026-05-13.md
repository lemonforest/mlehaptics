# Task #197 Phase 1 — AMSC-to-srmech refactor scope

**Branch:** `refactor/amsc-to-srmech-phase-1-scope` (from `main`)
**Date:** 2026-05-13
**Predecessors:**
- Spike #22 (`spike_22_amsc_citations_curated_scope_2026-05-13.md`) — discovered srmech has no AMSC subtree; named the architectural pressure that produced this refactor.
- `memory/reference_amsc_catalog_full_ship_procedure.md` — the 4-commit ship procedure that any catalog ratchet must respect.
- `memory/project_amsc_handcurated_consumption_channel.md` — `literature_curated` as the universal hand-curated channel.
- `memory/feedback_pdf_extraction_citation_discipline.md` — the citation-hygiene discipline the catalogs operationalize.
- `memory/reference_autonomous_validation_tos_landscape.md` — TOS landscape; relevant for what `srmech[collectors]` extra pulls in.
- User directive 2026-05-13: *"srmech with amsc must be able to support ephemerides-spectral unconditionally, not a works most the time sort of thing."*

**Status:** SCOPE-ONLY. Phase 1 of a 4-phase refactor. No code touched; no files moved; no PR opened. Phase 2 begins after this lands.

**Tabular sidecar:** None. This is a refactor-plan document; the per-file inventory tables are inline in §1.

---

## §0. The discipline and the load-bearing constraint

The user's directive establishes one non-negotiable: **unconditional support**. Translated to mechanical gates:

1. **Byte-identical wheel parity at Phase 3.** When ephemerides-spectral cuts over from its internal `_research/attested_collector_*.py` to `srmech.amsc.*`, the built wheel must differ from the pre-cutover wheel only in the `Requires-Dist: srmech>=X.Y.Z` METADATA line. No `.py` byte differences. No `.json`/`.toml` byte differences. No `.pyc` differences (the `wheel.exclude = ["*.pyc", "__pycache__"]` setting in pyproject already prevents this; the parity gate confirms it).

2. **Full test parity at Phase 3.** `pytest` against ephemerides-spectral pre-cutover and post-cutover must produce identical pass/fail counts and identical test names. Test timings are noise-tolerant; results are not.

3. **Codegen determinism unchanged at every phase boundary.** `python codegen/regenerate.py` must produce a byte-identical `_data/manifest.json` pre and post each phase. The manifest's per-file SHA-256 sums are the canonical reproducibility receipt.

4. **CI green on a fresh runner with a fresh install.** Not "passes on my machine"; the GitHub Actions workflows must pass.

5. **Each phase commit is cherry-pick-revertable.** If Phase 3 surfaces an unforeseen problem, reverting Phase 3 must leave the repo in the Phase-2 state — buildable, testable, shippable. Phase 4 cannot remove what Phase 3 depends on until Phase 3 is settled.

These five gates apply to every subsequent phase. They are the operationalization of "unconditional."

---

## §1. Q1 — AMSC framework file inventory in ephemerides-spectral

### §1.1 Framework code (SSOT in `docs/antikythera-maths/research/`)

The AMSC framework's source-of-truth lives in the antikythera research scaffold. The codegen mirrors it into the wheel-shipped `_research/` subtree.

**Top-level framework modules** (all under `docs/antikythera-maths/research/`):

| File | LOC | Description |
|---|---:|---|
| `attested_collector_format.py` | 359 | `MPRRecord` dataclass, NDJSON IO (`read_ndjson`, `write_ndjson`), `sha256_bytes`, `validate_mpr_record`, constants (`MPR_SCHEMA_VERSION`, `MANDATORY_ATTESTATION_FIELDS`, `MANDATORY_RENDERING_FIELDS`). Stdlib-only. |
| `attested_collector_descriptor.py` | 388 | Descriptor TOML loader (`load_descriptor`, `discover_descriptors`), `DescriptorValidationError`, `descriptor_hash`, `render_template`. Uses `tomllib` (3.11+) / `tomli` fallback. |
| `attested_collector_catalog.py` | 870 | Universal accessor surface: `list_attested_sources`, `get_attested_dataset`, `get_attested_descriptor`, `iter_attested_dataset`, `attestation_audit`, T2 overlay (`use_local_kernel`, `clear_local_kernel`, `get_local_kernel_state`). Imports from sibling format/descriptor modules — load-bearing coupling for the refactor. |
| `attested_collector_gap_suggester.py` | 233 | Gap analysis (`suggest_gap_collections`); imports from descriptor sibling. |

**Adapter subtree** (`docs/antikythera-maths/research/attested_adapters/`):

| File | LOC | Description |
|---|---:|---|
| `__init__.py` | 55 | Package re-exports: `ADAPTERS`, `AdapterError`, `attest`, `get_adapter`, `run`. |
| `_base.py` | 237 | `AdapterProtocol`, `AdapterError`, `attest()` SHA-256 fingerprinting, `run()` composer, `get_adapter()`, `ADAPTERS` registry. Imports from `..attested_collector_descriptor` and `..attested_collector_format`. |
| `html_scraper.py` | 140 | BeautifulSoup HTML scraper. Lazy `requests` + `bs4` import inside `fetch()`. |
| `json_api.py` | 189 | JSON-endpoint adapter with pagination. Lazy `requests`. |
| `csv_bulk.py` | 144 | CSV/ASCII XYZ bulk adapter. Lazy `requests`. |
| `netcdf_grid.py` | 58 | NetCDF reanalysis (fixture-only; real impl gated behind `collector-netcdf` extra). |
| `geotiff_bbox.py` | 55 | GeoTIFF raster (fixture-only; gated behind `collector-geotiff` extra). |
| `literature_curated.py` | 166 | Hand-curated NDJSON adapter (no network I/O); universal ingestion path per memory. |

**Total AMSC framework LOC:** ~2,894 lines across 12 files (4 top-level + 8 adapter-subtree). Plus 419 LOC for `tool_schema.py` *if it migrated* — but per §1.3, it does NOT migrate.

### §1.2 `tool_schema.py` — NOT framework, stays in ephemerides

`docs/antikythera-maths/research/tool_schema.py` (419 LOC) is **ephemerides-specific**, not AMSC-framework. It introspects `ephemerides_spectral.bridge` to emit Anthropic / OpenAI / MCP / JSON-Schema tool descriptions. Its docstring explicitly names the bridge module ("Introspects `ephemerides_spectral.bridge` and emits machine-readable tool descriptions"). It would not function inside `srmech.amsc.*` because srmech has no bridge analogue. **Decision: stays in ephemerides; out of refactor scope.** The codegen emit list for `_INCLUDED_MODULES` continues to include it; the file does not move.

### §1.3 Codegen mirror (`docs/antikythera-maths/ephemerides-spectral/python/ephemerides_spectral/_research/`)

Mirrored copies of the SSOT framework files (byte-identical to research/ except LF normalization on `.py` files per `emit_research_modules.py:145`). These are wheel-included files; consumers `from ephemerides_spectral._research.attested_collector_format import ...`.

| File | Source | Notes |
|---|---|---|
| `_research/attested_collector_format.py` | mirror | Identical to SSOT except LF-normalized. |
| `_research/attested_collector_descriptor.py` | mirror | Identical. |
| `_research/attested_collector_catalog.py` | mirror | Identical. |
| `_research/attested_collector_gap_suggester.py` | mirror | Identical. |
| `_research/attested_adapters/__init__.py` | mirror | Identical. |
| `_research/attested_adapters/_base.py` | mirror | Identical. |
| `_research/attested_adapters/{html_scraper,json_api,csv_bulk,netcdf_grid,geotiff_bbox,literature_curated}.py` | mirror | Identical. |

After Phase 4, these mirrored files no longer exist; the codegen's `_INCLUDED_MODULES` list drops their entries; the codegen's `_INCLUDED_SUBDIRS` list drops `attested_adapters`.

### §1.4 Codegen scripts

| File | LOC | Role | Refactor impact |
|---|---:|---|---|
| `codegen/regenerate.py` | 90 | Orchestrator. Calls `emit_research_modules.emit()`, `emit_attested_collections.emit()`, `emit_initial_phases.emit()`. Writes `manifest.json`. | Unchanged in structure. The `emit_research_modules.emit()` call returns fewer paths after Phase 4 (framework files dropped from `_INCLUDED_MODULES`); manifest size shrinks correspondingly. |
| `codegen/emit_research_modules.py` | 169 | Copies framework `.py` files from `research/` to `_research/` with LF normalization. | **Modified Phase 4:** drop entries `attested_collector_format.py`, `attested_collector_descriptor.py`, `attested_collector_catalog.py`, `attested_collector_gap_suggester.py` from `_INCLUDED_MODULES`; drop `attested_adapters` from `_INCLUDED_SUBDIRS`. |
| `codegen/emit_attested_collections.py` | 73 | Byte-exact recursive mirror of `research/attested/` → `_research/attested/`. **Currently has no allowlist — copies every subdirectory.** | **Modified Phase 2/4:** add `_INCLUDED_CATALOGS` allowlist (see §6). Phase 2 sets the allowlist to the current 19 ephemerides catalog directory names so behavior is unchanged. Phase 4 (or a coordinated Spike #23 ship) excludes `citations_curated/` from ephemerides's mirror once that catalog is added to the srmech side. |
| `codegen/emit_initial_phases.py` | (not read; orthogonal to AMSC) | Emits SPICE-free BIP fallback. | Unchanged. |
| `codegen/run_collectors.py` | 50+ | T1 CI collector runner. Imports from `research.attested_adapters._base`, `research.attested_collector_descriptor`, `research.attested_collector_format` directly (bypasses `ephemerides_spectral._research`). | **Modified Phase 3:** rewrite three imports to `srmech.amsc.adapters._base`, `srmech.amsc.descriptor`, `srmech.amsc.format`. The script imports the SSOT path, not the wheel path, so it becomes a direct srmech consumer. |
| `codegen/_paths.py` | 29 | Shared path helpers. Defines `RESEARCH_ROOT`, `ATTESTED_SRC`, `ATTESTED_DST`, `DATA_DIR`. | Unchanged. The `ATTESTED_SRC` still points at `docs/antikythera-maths/research/attested/` because the catalog SSOTs do NOT migrate to srmech in this refactor — only framework code does. |

### §1.5 Ephemerides consumer code

| File | Lines that import AMSC | Refactor change |
|---|---|---|
| `python/ephemerides_spectral/bridge.py` | 2 lines: `from ._research import attested_collector_catalog as _attested_catalog` (line 5985); `from ._research import attested_collector_gap_suggester as _suggester` (line 6170, inside function body). | Phase 3: rewrite to `from srmech.amsc import catalog as _attested_catalog` and `from srmech.amsc import gap_suggester as _suggester`. |
| `python/ephemerides_spectral/_research/cmb_anomalies_catalog.py` | 1 line: `from .attested_collector_catalog import get_attested_dataset` (line 33). | Phase 3: rewrite to `from srmech.amsc.catalog import get_attested_dataset`. **Note: this is a consumer module, NOT framework. It stays in `_research/` because it's an ephemerides-specific accessor wrapper for the CMB catalog.** |
| `python/ephemerides_spectral/_research/cmb_power_spectrum_catalog.py` | 1 line: `from .attested_collector_catalog import get_attested_dataset` (line 35). | Phase 3: rewrite as above. |
| `python/ephemerides_spectral/_research/body_kernel_registry.py` | 0 import lines (comment only at line 23 mentioning `attested_collector_catalog.use_local_kernel`). | No change. Comment can be updated optionally; non-load-bearing. |
| `python/tests/test_attested_collector.py` | 18 occurrences of `_research.attested_(collector|adapters)`. | Phase 3: rewrite all 18 to `srmech.amsc.*`. See §4.2 for the regex pattern. |
| `python/tests/test_tool_schema.py` | 0 lines import AMSC. | No change. |
| Other tests (any of the `*_amsc_helpers.py` / `test_*_dual_author.py`) | 0 lines (per grep — none import `attested_collector_*` directly). | No change. |

**Total ephemerides-side import lines to rewrite in Phase 3: 22 lines** (2 in `bridge.py` + 2 in `cmb_*_catalog.py` + 18 in `test_attested_collector.py`).

### §1.6 Catalog SSOT subtree (NOT framework — stays put)

`docs/antikythera-maths/research/attested/` contains 19 catalog directories (axial_seamount, cmb_anomalies, cmb_power_spectrum, dynamical_regime, dynamical_regime_probes, earthref_sc, gmrt, hawaii_chain, loki_patera, luna_dynamical_spectrum, mars_dynamical_spectrum, mars_tharsis, mercury_dynamical_spectrum, petdb_v4, pluto_charon_dynamical_spectrum, saturn_rings, sun_dynamical_spectrum, toroidal_residual, yarkovsky_yorp). Each contains `descriptor.toml`, `row.schema.json` (or `*.schema.json`), and `row.ndjson` (or `*.ndjson`).

**These do not move.** They are ephemerides catalogs; their SSOT location is correct. Spike #22's `citations_curated` is the only srmech-primary catalog being planned, and that catalog is being scoped separately as an srmech-side asset.

The catalog SSOT location is orthogonal to the framework code location: the framework reads from `Path(__file__).resolve().parent / "attested"` (per `attested_collector_catalog._attested_root`). Post-refactor, when `srmech.amsc.catalog` is imported by ephemerides, it resolves the attested-root relative to its **own** module location inside the srmech wheel. **This is a problem** — see §3.3 for the resolution.

---

## §2. Q2 — srmech's current state

Discovery result: **srmech has no Python package, no PyPI/TestPyPI presence, and no publish workflow.** The conductor brief noted that the user confirmed `srmech-publish.yml` exists, but a thorough grep across `.github/workflows/`, `docs/`, and the full tree returns zero matches for any `srmech*.yml` file or any `pyproject.toml` referencing srmech. The current state at `main` (commit `a39a28a`) is:

```
docs/srmech/
├── .pages
├── srmech_research_notebook.md       # 76 KB notebook
├── hoodoos/                          # PDB / XML holdout fixtures
└── notes/                            # ~190 files: .md spikes, .ndjson sidecars, .py scripts, .png plots
```

No `srmech/` Python package directory. No `srmech-spectral/` directory. No `srmech-publish.yml` or `srmech-ci.yml` in `.github/workflows/`. The `.github/workflows/` directory contains only antikythera-spectral, chess-spectral, ephemerides-spectral, and codeql workflows.

**Implication for Phase 2:** Phase 2 must bootstrap srmech as a Python package from scratch. This is significantly larger than the conductor brief assumed. The implication is recorded explicitly in §9.2 (Phase 2 effort estimate) and §7 (risk register).

**Implication for the user's stated confirmation:** Either the publish workflow was planned but not yet committed, or it lives on a branch not visible from `main`. Phase 1 documents the discovered state; the user can correct from authoritative knowledge after reviewing.

---

## §3. Q3 — `srmech/amsc/` submodule layout

### §3.1 Rename decision — terse names under `amsc/` namespace

**Decision: terse names (`format.py`, `descriptor.py`, `catalog.py`, `gap_suggester.py`, `adapters/`).** The `attested_collector_` prefix carried meaningful disambiguation when these modules sat alongside `geodetic_catalog.py`, `magnetic_multipole_catalog.py`, `cmb_anomalies_catalog.py` in a flat `research/` directory — the prefix told the reader "this is the universal framework, not a per-source catalog wrapper." Inside an `amsc/` namespace package, the disambiguation is structural: `srmech.amsc.catalog` is unambiguously the framework catalog accessor; the per-source wrappers (still in ephemerides) are `ephemerides_spectral._research.cmb_anomalies_catalog` etc., which keep their own prefixes.

The rename is purely cosmetic at the module-symbol level: `MPRRecord`, `Descriptor`, `discover_descriptors`, `get_attested_dataset` are unchanged. Only the import paths change.

### §3.2 Target layout

```
srmech/
├── __init__.py                       # Package marker; thin (imports/version)
├── py.typed                          # PEP 561 marker for type-checking consumers
├── version.py                        # Single source of truth for __version__
└── amsc/
    ├── __init__.py                   # Re-exports common names (MPRRecord, Descriptor, get_attested_dataset, etc.) for ergonomic import
    ├── format.py                     # From: research/attested_collector_format.py
    ├── descriptor.py                 # From: research/attested_collector_descriptor.py
    ├── catalog.py                    # From: research/attested_collector_catalog.py
    ├── gap_suggester.py              # From: research/attested_collector_gap_suggester.py
    └── adapters/
        ├── __init__.py               # Adapter registry exports (mirrors current research/attested_adapters/__init__.py)
        ├── _base.py                  # From: research/attested_adapters/_base.py
        ├── html_scraper.py
        ├── json_api.py
        ├── csv_bulk.py
        ├── netcdf_grid.py
        ├── geotiff_bbox.py
        └── literature_curated.py
```

Plus, ONLY for the eventual `citations_curated` ship and other future srmech-primary catalogs:

```
srmech/
└── amsc/
    └── attested/                     # srmech-primary AMSC catalog SSOTs (when they exist)
        └── citations_curated/        # Spike #23's destination (eventual)
            ├── descriptor.toml
            ├── row.schema.json
            └── row.ndjson
```

In Phase 2, `srmech/amsc/attested/` exists as an empty directory with just `__init__.py`. No catalogs are added in this refactor; Spike #23 adds the first one.

### §3.3 Resolution for `_attested_root()` cross-package access

The current `attested_collector_catalog._attested_root()` resolves the attested-root via `Path(__file__).resolve().parent / "attested"`. This is the load-bearing design that lets the same code work both in the SSOT (`research/attested/`) and the mirror (`_research/attested/`). It breaks under the refactor because `srmech.amsc.catalog.__file__` resolves to `<sitepackages>/srmech/amsc/catalog.py`, and ephemerides's 19 catalog SSOTs live at `<sitepackages>/ephemerides_spectral/_research/attested/` — not next to srmech's module.

**Resolution: add a runtime overlay-registration API on `srmech.amsc.catalog`.** Add `register_attested_root(path: Path, *, source: str)` that lets downstream packages push additional catalog roots beyond srmech's own. ephemerides-spectral imports `srmech.amsc.catalog` and at package-import time calls `_amsc_catalog.register_attested_root(Path(__file__).resolve().parent / "_research" / "attested", source="ephemerides-spectral")`. The `_descriptors()` cache then enumerates the union of all registered roots (srmech's own `amsc/attested/` plus externally-registered ones).

**Failure-mode discipline:** if two registered roots contain the same `source_key`, the registration order wins and a warning is logged. (Realistic future: a `citations_curated` row could exist in both srmech and ephemerides during a migration window; the registration order disambiguates.)

This is the cleanest path because:
1. It preserves the SSOT-mirror byte-identity discipline (each package's `_research/attested/` mirror is still its own subtree).
2. It does not require ephemerides catalogs to physically move to srmech.
3. It supports the future scenario where srmech has its own catalogs (`citations_curated`) while ephemerides continues to ship its 19 catalogs from its own subtree.
4. The registration call is one line of bootstrap code per consuming package.

**Alternative considered and rejected:** pass `attested_root` as an explicit argument to every accessor (`get_attested_dataset(source_key, attested_root=...)`). Rejected because (a) it breaks the existing 22 call sites in ephemerides that don't pass `attested_root`; (b) it pushes path-knowledge into every consumer, which violates the encapsulation the AMSC framework was designed to provide; (c) it makes a clean import-swap impossible — the call sites would have to change beyond just imports.

### §3.4 Inter-module imports inside `srmech.amsc`

Internal imports inside the framework rewrite identically:

| Current (`docs/antikythera-maths/research/`) | After Phase 2 (`srmech/amsc/`) |
|---|---|
| `from .attested_collector_descriptor import Descriptor, discover_descriptors` (in `catalog.py`) | `from .descriptor import Descriptor, discover_descriptors` |
| `from .attested_collector_format import MPRRecord, read_ndjson` (in `catalog.py`) | `from .format import MPRRecord, read_ndjson` |
| `from .attested_collector_descriptor import ...` (in `gap_suggester.py`) | `from .descriptor import ...` |
| `from ..attested_collector_descriptor import Descriptor, descriptor_hash, render_template` (in `adapters/_base.py`) | `from ..descriptor import Descriptor, descriptor_hash, render_template` |
| `from ..attested_collector_format import MPR_SCHEMA_VERSION, MPRRecord, sha256_bytes` (in `adapters/_base.py`) | `from ..format import MPR_SCHEMA_VERSION, MPRRecord, sha256_bytes` |
| `from ..attested_collector_descriptor import Descriptor` (in each adapter file) | `from ..descriptor import Descriptor` |

Six framework-internal import lines to rewrite during Phase 2 (the COPY step). These are mechanical sed-rewrites.

---

## §4. Q4 — ephemerides-spectral import-swap (Phase 3)

<think>
The user wants extended thinking on this. Let me work through the rewrite mechanically and identify edge cases.

Call sites identified:
1. bridge.py line 5985: `from ._research import attested_collector_catalog as _attested_catalog`
2. bridge.py line 6170: `from ._research import attested_collector_gap_suggester as _suggester`
3. cmb_anomalies_catalog.py line 33: `from .attested_collector_catalog import get_attested_dataset`
4. cmb_power_spectrum_catalog.py line 35: `from .attested_collector_catalog import get_attested_dataset`
5. test_attested_collector.py: 18 occurrences (lines 30-something for adapters import, 43-50 for descriptor, 51-61 for format, then several function-local imports later).

The grep showed the import patterns:
- `from ephemerides_spectral._research.attested_collector_descriptor import ...` (lines 43, 287, 316, 341)
- `from ephemerides_spectral._research.attested_collector_format import ...` (lines 51, 775)
- `from ephemerides_spectral._research.attested_collector_catalog import ...` (lines 218, 284, 313, 338, 362)
- `from ephemerides_spectral._research.attested_collector_gap_suggester import ...` (line 1083)
- `from ephemerides_spectral._research.attested_adapters import (` (the multi-line one)

Three rewrite shapes:
1. `from ephemerides_spectral._research.attested_collector_X import ...` → `from srmech.amsc.X import ...` (where X loses the `attested_collector_` prefix and is renamed: format/descriptor/catalog/gap_suggester)
2. `from ephemerides_spectral._research.attested_adapters import ...` → `from srmech.amsc.adapters import ...`
3. `from ._research import attested_collector_X as ...` (relative form in bridge.py) → `from srmech.amsc import X as ...`
4. `from .attested_collector_catalog import get_attested_dataset` (cmb_*_catalog.py inside _research/) → `from srmech.amsc.catalog import get_attested_dataset`

The rename table:
- attested_collector_format → format
- attested_collector_descriptor → descriptor
- attested_collector_catalog → catalog
- attested_collector_gap_suggester → gap_suggester
- attested_adapters → adapters (the subpackage name)

One sed pattern per shape. The patterns must be ordered most-specific first to avoid mis-rewriting.

Now, the bootstrap registration call. Where does it go?

The ephemerides codegen output includes `_research/__init__.py`. Let me check that file...

Actually I haven't read it. Let me note this as a dependency to verify in Phase 2 prep, and propose putting the registration call in `_research/__init__.py` since it's the natural bootstrap for the `_research/attested/` subtree.

Alternative: put it in `ephemerides_spectral/__init__.py` (the package root) so it runs on `import ephemerides_spectral`. This is cleaner because users importing the bridge get the registration "for free" without having to think about `_research`.

Decision: register in `ephemerides_spectral/__init__.py`. This is the most consumer-friendly path.

Now codegen impact:

run_collectors.py currently:
```python
from research.attested_adapters._base import run as adapter_run
from research.attested_collector_descriptor import discover_descriptors
from research.attested_collector_format import write_ndjson
```

After Phase 3, srmech is installed in the codegen venv (it's a dev dep). These become:
```python
from srmech.amsc.adapters._base import run as adapter_run
from srmech.amsc.descriptor import discover_descriptors
from srmech.amsc.format import write_ndjson
```

The `ensure_research_importable()` call is no longer needed for AMSC imports (it remains for the other `research/*.py` files the script doesn't currently use but might in the future). Actually, looking again, run_collectors.py only uses these three AMSC imports — so the `ensure_research_importable()` call could be removed entirely. But removing it is a Phase 4 concern (it's defensive, not causing harm).

Codegen emit_research_modules.py:
- Phase 4: drop `attested_collector_*.py` entries from `_INCLUDED_MODULES`
- Phase 4: drop `"attested_adapters"` from `_INCLUDED_SUBDIRS`

emit_attested_collections.py:
- Allowlist needed in Phase 2 (defensive — list current catalogs so behavior is unchanged) OR Phase 4 (when we want to actually start excluding catalogs).
- Decision: ADD the allowlist in Phase 2 with the current 19 catalogs explicitly enumerated. This documents the current state and creates the mechanism. The allowlist is a no-op when it lists every directory in `research/attested/`; it becomes load-bearing only when srmech ships `citations_curated` and ephemerides should exclude it.

Wait — but adding the allowlist in Phase 2 changes the codegen behavior potentially. If the allowlist contains everything currently in `research/attested/`, the output should be byte-identical to no-allowlist (modulo iteration order, which sorted() already controls). Let me confirm: `emit_attested_collections.py` uses `sorted(ATTESTED_SRC.rglob("*"))`. An allowlist filters this list. If the allowlist contains every directory, the filter is a no-op. Byte-identity preserved.

But the test parity gate is concerned with manifest.json — and the manifest is sorted by filename, so allowlist ordering doesn't matter. Good.

Phase 3 ordering matters: the import swap and the framework code removal can't happen in the same commit if we want cherry-pick-revertable phases. Phase 3 = swap imports only (framework still mirrored in _research/ as redundancy); Phase 4 = remove the mirror.

Actually wait — Phase 3 needs to import from `srmech.amsc.*` AND the redundant mirror to coexist without conflict. The mirror at `_research/attested_collector_*.py` is still imported by... no one, after Phase 3. The 22 import sites all moved to srmech.amsc. So the mirror is dead code after Phase 3.

But codegen still emits the mirror until Phase 4 removes it from `_INCLUDED_MODULES`. That's the safe state: Phase 3 leaves dead code in the wheel temporarily; Phase 4 cleans it up.

The wheel parity check at Phase 3: the wheel before Phase 3 has the framework code in `_research/`. The wheel after Phase 3 ALSO has the framework code in `_research/` (because codegen still emits it) — but the wheel additionally has `Requires-Dist: srmech>=X.Y.Z` in METADATA. The framework code is in BOTH places (unused in `_research/`, used via `srmech.amsc`). The wheel diff is exactly: METADATA gains the Requires-Dist line, and the .py files that imported AMSC now have different import lines (so they have different bytes).

WAIT. That means the wheel is NOT byte-identical at Phase 3 in the strict sense. The .py files in the wheel that consume AMSC (bridge.py, cmb_*_catalog.py, and the test files if shipped) have changed bytes.

The user's "byte-identical wheel parity" must mean "byte-identical except for the import lines that necessarily change and the METADATA Requires-Dist line." That's the correct interpretation.

So the parity protocol I need to specify is:
- METADATA file: differs only by adding `Requires-Dist: srmech>=X.Y.Z`
- Python files: differ only in the 22 import lines mapped per the rewrite rules
- All other files (NDJSON, JSON schemas, TOML descriptors, manifest.json) must be byte-identical
- manifest.json's per-file SHA-256 sums change ONLY for the .py files whose import lines changed

Yes, that's the right framing. Let me write it that way.

Actually, an even cleaner gate: do BYTE diff on the wheel; then human-verify the diff is exactly the expected set of import-line changes + Requires-Dist. The byte diff is mechanical; the human verification is the GO/NO-GO.

For test parity: pytest output must be identical in pass/fail count + test names. Timings noise-tolerant.

For codegen determinism: manifest.json's structure is identical (same files listed); SHA-256 sums of unchanged files are identical; SHA-256 sums of changed files (the 4 .py files: bridge.py, cmb_anomalies_catalog.py, cmb_power_spectrum_catalog.py, test_attested_collector.py if it ships in wheel — but tests typically don't ship) differ deterministically.

I think test files don't ship in the wheel based on the pyproject.toml. Let me confirm: `wheel.packages = ["ephemerides_spectral"]` — tests are in `python/tests/`, which is outside `python/ephemerides_spectral/`, so they don't ship. Good. The test_attested_collector.py changes don't affect the wheel.

So the wheel diff narrows to: METADATA (Requires-Dist added) + 3 .py files (bridge.py, cmb_anomalies_catalog.py, cmb_power_spectrum_catalog.py). Manifest.json's SHA-256 sums change for those 3 files; the manifest's structure is otherwise identical.
</think>

### §4.1 The 22 call sites and their rewrites

Phase 3 rewrites **22 import lines** across **4 files**.

**File 1: `python/ephemerides_spectral/bridge.py`** (2 lines)

| Line | Before | After |
|---:|---|---|
| 5985 | `from ._research import attested_collector_catalog as _attested_catalog` | `from srmech.amsc import catalog as _attested_catalog` |
| 6170 | `from ._research import attested_collector_gap_suggester as _suggester` | `from srmech.amsc import gap_suggester as _suggester` |

**File 2: `python/ephemerides_spectral/_research/cmb_anomalies_catalog.py`** (1 line)

| Line | Before | After |
|---:|---|---|
| 33 | `from .attested_collector_catalog import get_attested_dataset` | `from srmech.amsc.catalog import get_attested_dataset` |

**File 3: `python/ephemerides_spectral/_research/cmb_power_spectrum_catalog.py`** (1 line)

| Line | Before | After |
|---:|---|---|
| 35 | `from .attested_collector_catalog import get_attested_dataset` | `from srmech.amsc.catalog import get_attested_dataset` |

**File 4: `python/tests/test_attested_collector.py`** (18 lines)

The 18 occurrences fall into 5 shape categories:

| Shape | Count | Rewrite rule (regex/sed) |
|---|---:|---|
| `from ephemerides_spectral._research.attested_collector_format import ...` | 2 | `s|from ephemerides_spectral\._research\.attested_collector_format|from srmech.amsc.format|g` |
| `from ephemerides_spectral._research.attested_collector_descriptor import ...` | 4 | `s|from ephemerides_spectral\._research\.attested_collector_descriptor|from srmech.amsc.descriptor|g` |
| `from ephemerides_spectral._research.attested_collector_catalog import ...` | 5 | `s|from ephemerides_spectral\._research\.attested_collector_catalog|from srmech.amsc.catalog|g` |
| `from ephemerides_spectral._research.attested_collector_gap_suggester import ...` | 1 | `s|from ephemerides_spectral\._research\.attested_collector_gap_suggester|from srmech.amsc.gap_suggester|g` |
| `from ephemerides_spectral._research.attested_adapters import ...` | 1 (multi-line tuple unpacking) | `s|from ephemerides_spectral\._research\.attested_adapters|from srmech.amsc.adapters|g` |
| Function-local `from ephemerides_spectral._research.attested_collector_format import write_ndjson` etc. | 5 | covered by the first 5 patterns |

The five sed patterns can be applied in any order because none is a prefix of another. The total set of imports rewrites cleanly with one pass.

**File 5: `codegen/run_collectors.py`** (3 lines — codegen, not wheel-included)

| Line | Before | After |
|---:|---|---|
| 32 | `from research.attested_adapters._base import run as adapter_run  # noqa: E402` | `from srmech.amsc.adapters._base import run as adapter_run  # noqa: E402` |
| 33 | `from research.attested_collector_descriptor import (  # noqa: E402` | `from srmech.amsc.descriptor import (  # noqa: E402` |
| 36 | `from research.attested_collector_format import (  # noqa: E402` | `from srmech.amsc.format import (  # noqa: E402` |

`run_collectors.py` is collector machinery, not part of the wheel. It runs in the CI collector-workflow only. The rewrite removes the dependency on `research/` for AMSC framework imports; the `ensure_research_importable()` call remains useful for other `research/*.py` modules the script may later use.

**Total: 25 import lines across 5 files in Phase 3** (22 wheel-affecting + 3 codegen-only).

### §4.2 Compat-shim decision — none

The `_research/attested_collector_*.py` files in the wheel become **dead code after Phase 3** (nothing imports them). They are NOT used as compat-shims because:

1. The four files (format / descriptor / catalog / gap_suggester) all live inside `ephemerides_spectral._research`, a `_`-prefixed private subpackage. No external consumers should import them; they have no documented public API beyond `bridge.py`.
2. Compat-shims would require maintaining two copies of the same code (the srmech.amsc original + the ephemerides shim re-exporting it). The maintenance burden is gratuitous because the actual call sites are all internal to ephemerides.
3. The shim path adds a transparent indirection that complicates the wheel parity check (the shims have different bytes than the originals — the bytes are now `from srmech.amsc.format import *` not `class MPRRecord: ...`).

**Decision: Phase 4 deletes `_research/attested_collector_*.py` and `_research/attested_adapters/` entirely.** Phase 3 leaves them as dead code (no consumers) so Phase 3 is independently revertable.

### §4.3 Codegen impact in Phase 4

`emit_research_modules.py` is modified at Phase 4 to drop the AMSC framework entries from `_INCLUDED_MODULES`:

```python
# Phase 4 — these entries are REMOVED:
#   "attested_collector_format.py",
#   "attested_collector_descriptor.py",
#   "attested_collector_catalog.py",
#   "attested_collector_gap_suggester.py",
# And from _INCLUDED_SUBDIRS:
#   "attested_adapters",
```

This shrinks the wheel by ~2,900 LOC and ~100 KB. The wheel still ships every catalog-specific consumer module (e.g., `cmb_anomalies_catalog.py`); only the framework is dropped.

### §4.4 Bootstrap registration call

ephemerides-spectral must register its `_research/attested/` subtree with `srmech.amsc.catalog` at package-import time. The registration call lives in **`python/ephemerides_spectral/__init__.py`** (the package root) and reads: `from pathlib import Path; from srmech.amsc import catalog as _amsc_catalog; _amsc_catalog.register_attested_root(Path(__file__).resolve().parent / "_research" / "attested", source="ephemerides-spectral")`. This is the single net-new code addition in Phase 3 beyond the import-line rewrites. One location, three lines, idempotent on re-import.

The `register_attested_root` function is new in `srmech.amsc.catalog` (added in Phase 2) and replaces the implicit "look next to me" behavior of the current `_attested_root()` function. The Phase 2 design must:
- Keep `_attested_root()` as the default (for srmech's own `amsc/attested/` subtree).
- Add `_REGISTERED_ROOTS: List[Tuple[Path, str]]` as module-level state.
- `register_attested_root(path, *, source)` appends to the list.
- `_descriptors()` enumerates the union of `_attested_root()` and all registered roots.
- Conflict policy: first-registered wins; duplicate-source-key logs a warning.

---

## §5. Q5 — Parity protocol (the load-bearing discipline)

<think>
This is the most load-bearing section. The user's "unconditional support" gate operationalizes here. Let me design 5 concrete go/no-go gates and specify the protocols mechanically.

Wheel parity:
- Build wheel pre-Phase-3 from clean tree
- Build wheel post-Phase-3 from clean tree
- Unpack both wheels (they're zips)
- Diff each file
- Expected diffs:
  - METADATA: gains `Requires-Dist: srmech>=X.Y.Z` line
  - bridge.py: 2 import-line diffs
  - _research/cmb_anomalies_catalog.py: 1 import-line diff
  - _research/cmb_power_spectrum_catalog.py: 1 import-line diff
  - _data/manifest.json: SHA-256 changes for those 3 .py files (mechanically computed from the changed bytes)
- Forbidden diffs: any NDJSON, JSON schema, TOML, or other .py file

Test parity:
- pytest pre/post, compare output
- Expected: identical pass/fail counts, identical test names
- Tolerance: timings (test ordering can differ slightly with parallelism)
- Forbidden: any test transitions from passing to failing or vice versa

Codegen parity:
- Run codegen pre and post
- Compare manifest.json byte-for-byte (sort order is already stable per regenerate.py:78)
- Expected: differences ONLY in the SHA-256 sums of changed .py files
- Forbidden: any new/removed file entries; any structural change to manifest

Bridge surface parity:
- list_attested_sources() pre and post — must return identical dict
- get_attested_descriptor(key) for each of 19 keys pre and post — identical
- get_attested_dataset(key) for each of 19 keys pre and post — identical row contents
- attestation_audit(key) for each key — identical
- suggest_gap_collections() pre and post — identical

CLI parity:
- For every CLI subcommand that touches AMSC (need to check cli.py for which ones do)
- Run with canonical input
- Compare exit code + stdout

Actually I noticed earlier that cli.py grep returned no matches for attested_collector. Let me check more carefully... I did `Grep -P "attested_collector_|attested_adapters|from\s+\.\._research"` and got no matches. So CLI doesn't directly import AMSC. But it might call bridge functions that do. The bridge parity gate covers that.

Let me also think about whether tests are byte-identical at the bytes level — the test files have 18 import-line changes, so the test files themselves change. But tests don't ship in the wheel. The wheel parity gate ignores them. Test parity is about pytest's behavior, not test file bytes.

Five gates, each with concrete protocol. Each is GO/NO-GO.
</think>

Five GO/NO-GO gates. All must pass before Phase 3's PR merges.

### §5.1 Gate 1 — Wheel byte-diff protocol

**Procedure:**
1. From clean checkout of `main` at Phase-2's tip, run `cd docs/antikythera-maths/ephemerides-spectral/python && python -m build --wheel`. Save the wheel as `wheel-pre.whl`.
2. Apply Phase 3 changes; rebuild the wheel; save as `wheel-post.whl`.
3. Unpack both: `wheelhouse-pre/` and `wheelhouse-post/`.
4. `diff -r wheelhouse-pre/ wheelhouse-post/` (or equivalent on Windows: `Compare-Object -ReferenceObject (Get-ChildItem -Recurse wheelhouse-pre)`).

**Expected diff set (the ONLY acceptable differences):**

| File | Diff | Acceptance criterion |
|---|---|---|
| `ephemerides_spectral-X.Y.Z.dist-info/METADATA` | Gains `Requires-Dist: srmech>=X.Y.Z` line (alphabetically positioned). | Diff is EXACTLY one added line matching that pattern. |
| `ephemerides_spectral/bridge.py` | 2 lines changed (lines 5985 and 6170 per §4.1). | Diff is EXACTLY those two import lines. |
| `ephemerides_spectral/_research/cmb_anomalies_catalog.py` | 1 line changed (line 33). | Diff is EXACTLY that line. |
| `ephemerides_spectral/_research/cmb_power_spectrum_catalog.py` | 1 line changed (line 35). | Diff is EXACTLY that line. |
| `ephemerides_spectral/_data/manifest.json` | SHA-256 sums change for exactly the 4 files above (bridge.py, the 2 cmb catalog files, and the package __init__.py if Phase 3 adds the bootstrap call there). | Diff is in only those 4 SHA-256 entries; total bytes / file-count entries identical. |
| `ephemerides_spectral/__init__.py` | Gains the 3-line bootstrap registration block (per §4.4). | Diff is EXACTLY that block. |

**Forbidden diff set:**
- Any `.ndjson` byte difference.
- Any `.schema.json` byte difference.
- Any `.toml` (descriptor) byte difference.
- Any `.py` file outside the 5 listed above.
- Any structural change to `manifest.json` (added/removed file entries; reordered keys).
- Any `.dist-info/RECORD` change that doesn't trace mechanically to the above file changes.

**Gate verdict:** GO if and only if every diff line falls in the Expected set and no diff appears in the Forbidden set.

### §5.2 Gate 2 — Pytest parity protocol

**Procedure:**
1. Pre-Phase-3: from clean checkout, run `pytest python/tests/ -p no:randomly --tb=no -q | tee pytest-pre.log`.
2. Pre-Phase-3: also `pytest python/tests/ --collect-only -q | tee pytest-pre-collect.log`.
3. Apply Phase 3 changes.
4. Post-Phase-3: same commands; save as `pytest-post.log` and `pytest-post-collect.log`.
5. `diff pytest-pre-collect.log pytest-post-collect.log` and `diff <(grep -E '^(PASSED|FAILED|ERROR|SKIPPED)' pytest-pre.log | sort) <(grep -E '^(PASSED|FAILED|ERROR|SKIPPED)' pytest-post.log | sort)`.

**Acceptance criterion:** Both diffs are empty. Every test name is collected identically; every test produces the same status (PASSED / FAILED / ERROR / SKIPPED).

**Tolerance:** Test timing differences are ignored (they vary with system load). Test ORDER differences are normalized by `-p no:randomly` + `sort`. Warnings emitted via Python's `warnings` module are not part of the gate (they appear in `-q` mode but are not compared).

**Forbidden:** Any test transitioning from PASSED to FAILED / ERROR, or vice versa. Any test that exists pre but not post (or vice versa).

**Gate verdict:** GO if both diffs are empty; NO-GO otherwise.

### §5.3 Gate 3 — Codegen determinism protocol

**Procedure:**
1. Pre-Phase-3: from clean checkout, `cd docs/antikythera-maths/ephemerides-spectral && python codegen/regenerate.py`. Save `python/ephemerides_spectral/_data/manifest.json` as `manifest-pre.json`.
2. Apply Phase 3 changes.
3. Post-Phase-3: same command. Save `manifest-post.json`.
4. `diff manifest-pre.json manifest-post.json`.

**Acceptance criterion:** The diff is EXACTLY:
- 4 SHA-256 entries changed (the 3 .py files modified in Phase 3 plus `__init__.py`'s bootstrap addition).
- 4 corresponding `size_bytes` entries changed (mechanical consequence of the file-byte changes).
- No file-key additions or removals.
- No reordering (the manifest is `sort_keys=True` per `regenerate.py:78`).

**Forbidden:** Any new key in `manifest['files']`. Any removed key. Any SHA-256 change in a file not modified by Phase 3.

**Gate verdict:** GO if the diff matches exactly; NO-GO otherwise.

**Note:** Per `memory/feedback_run_wsl_smoke_before_amsc_push.md`, this gate must run under WSL (or a real Linux box) AS WELL AS Windows-local Python before any push. The libm last-bit divergence has bitten before; running codegen on Windows only is insufficient.

### §5.4 Gate 4 — Bridge surface parity protocol

**Procedure:**
1. Pre-Phase-3: from clean checkout with wheel installed, run a snapshot script that calls `list_attested_sources()` (with and without each `adapter_class` filter), then for each of the 19 source keys calls `get_attested_descriptor(k)`, `get_attested_dataset(k)`, `attestation_audit(k)`, and finally `suggest_gap_collections(ood_threshold=0.5)`. Serialize the union with `json.dumps(snapshot, sort_keys=True, default=str)` and save as `bridge-snapshot-pre.json`.
2. Apply Phase 3 changes; rebuild and reinstall the wheel; install `srmech` from local source.
3. Post-Phase-3: run the same script; save `bridge-snapshot-post.json`.
4. Compare SHA-256 hashes; if equal, gate passes. If not, `diff` the JSON files to identify the divergence.

**Acceptance criterion:** SHA-256 of `bridge-snapshot-pre.json` and `bridge-snapshot-post.json` are equal.

**Forbidden:** Any divergence in row contents, descriptor metadata, attestation blocks, or rendered citation strings.

**Gate verdict:** GO if hashes match.

**Note:** This gate is the strongest functional check. Wheel byte parity (Gate 1) is necessary but not sufficient — a subtle bug in `register_attested_root` could cause divergent descriptor enumeration (e.g., catalogs missing from `list_attested_sources` output) without changing any wheel byte. Gate 4 catches this.

### §5.5 Gate 5 — CLI parity protocol

**Procedure:**
1. Pre-Phase-3: identify every `ephemerides-spectral` CLI subcommand that touches AMSC. Per `cli.py` grep result, the CLI does not directly import `attested_collector_*`, but it likely delegates to bridge functions. Audit `cli.py` for any subcommand whose output depends on AMSC catalogs (e.g., a hypothetical `ephemerides-spectral list-attested-sources`).
2. For each such subcommand, run with canonical input; capture exit code + stdout.
3. Post-Phase-3: same commands; capture and compare.

**Acceptance criterion:** Exit codes identical; stdout byte-identical (modulo timestamp lines, which should be filtered).

**Tolerance:** Lines containing `retrieved_at`, `entered_locally_at`, or current-time stamps are filtered before comparison.

**Forbidden:** Any divergent stdout that doesn't reduce to filtered timestamps.

**Gate verdict:** GO if all subcommands produce identical filtered output.

**Note:** If `cli.py` does not currently expose any AMSC-touching subcommand (likely, given the grep), Gate 5 is vacuously satisfied. Confirm during Phase 3 prep.

### §5.6 Aggregate gate logic

Phase 3 PR merges if and only if ALL FIVE gates are GO. A single NO-GO blocks the merge until the divergence is understood and either:
- A Phase 3 code fix resolves the divergence (preferred), or
- The Expected diff set is amended to cover the new diff (only if the diff is provably non-load-bearing — e.g., a deterministic byte-stable change in build-system metadata that doesn't affect behavior).

The five-gate protocol is the operationalization of the user's "unconditional support" discipline. Every gate is a mechanical comparison; no human judgment is needed beyond verifying that observed diffs fall in the Expected set.

### §5.7 Parity viability assessment

All five gates are achievable. The only design choice that could threaten parity is the `register_attested_root` mechanism — if its implementation has any non-determinism (e.g., a `dict` iteration on Python <3.7 — not relevant for `requires-python = ">=3.10"`), Gate 4 could fail. The Phase 2 implementation of `register_attested_root` must use `list` (insertion-ordered) for `_REGISTERED_ROOTS` and must sort the union of catalogs by source_key in `_descriptors()` to guarantee determinism. This is documented as a Phase 2 acceptance criterion in §9.2.

---

## §6. Q6 — Allowlist mechanism for ephemerides-spectral codegen

### §6.1 Current state — no allowlist

`emit_attested_collections.py` currently has no allowlist. It mirrors EVERY subdirectory under `research/attested/` into `_research/attested/`. Today this is fine because the only directory there is ephemerides-owned catalogs. Once srmech ships its own catalogs (e.g., `citations_curated/` per Spike #22), if those land in `research/attested/`, they would be unintentionally mirrored into ephemerides's wheel.

**Decision: srmech-primary catalogs land in `srmech/amsc/attested/`, NOT `research/attested/`.** Spike #22's design committed to landing `citations_curated` in `research/attested/` because srmech had no AMSC subtree at the time. Phase 1 of this refactor creates that subtree; Spike #22's "final home" is now `srmech/amsc/attested/citations_curated/` (Spike #23 will execute the ship into that location once Phase 2 lands).

This means `research/attested/` continues to hold ONLY ephemerides catalogs, and the no-allowlist mirror is technically still correct. But a defensive allowlist documents the contract: ephemerides's wheel ships ephemerides's catalogs, period.

### §6.2 Allowlist design (Phase 2)

Add `_INCLUDED_CATALOGS: List[str]` to `emit_attested_collections.py` containing the 19 current ephemerides catalog keys: `axial_seamount`, `cmb_anomalies`, `cmb_power_spectrum`, `dynamical_regime`, `dynamical_regime_probes`, `earthref_sc`, `gmrt`, `hawaii_chain`, `loki_patera`, `luna_dynamical_spectrum`, `mars_dynamical_spectrum`, `mars_tharsis`, `mercury_dynamical_spectrum`, `petdb_v4`, `pluto_charon_dynamical_spectrum`, `saturn_rings`, `sun_dynamical_spectrum`, `toroidal_residual`, `yarkovsky_yorp`.

Modify `emit()`'s `rglob` loop to filter: for each path, compute `rel = src.relative_to(ATTESTED_SRC)`; if `rel.parts[0]` is neither in `_INCLUDED_CATALOGS` nor `"__init__.py"`, skip the file. Everything else (LF normalization, byte-exact NDJSON, dot-prefix skip, `.pyc` skip) is unchanged. Output is byte-identical to pre-Phase-2 because the allowlist enumerates every existing catalog.

**Allowlist count: 19 catalogs.** Identical to the current 19 directories in `research/attested/`. Phase 2's diff against pre-Phase-2 manifest is therefore zero (allowlist is a no-op when it lists everything).

### §6.3 Allowlist load-bearing moment

The allowlist becomes load-bearing the moment a non-ephemerides directory appears in `research/attested/`. Worked example: if Spike #23 (hypothetically) chooses to land `citations_curated/` at `research/attested/citations_curated/` despite Phase 1's decision otherwise, the ephemerides codegen would automatically EXCLUDE it because `"citations_curated"` is not in `_INCLUDED_CATALOGS`. The allowlist is the safety net against accidental cross-contamination.

The cleaner path remains: srmech-primary catalogs live in `srmech/amsc/attested/`. The allowlist is belt-and-suspenders.

### §6.4 Symmetric allowlist on srmech side (future-scoped)

When Phase 2 creates `srmech/amsc/`, the (then-empty) `srmech/amsc/attested/` subtree is mirrored into the srmech wheel via a srmech-side codegen. Phase 2 must include a stub codegen for srmech (analogous to ephemerides's `emit_attested_collections.py` but targeting srmech's own `_research/attested/` mirror — if srmech has a `_research/` mirror at all; for an installable Python package the catalogs may live directly under `srmech/amsc/attested/` with no separate mirror needed).

**Decision: srmech does NOT use a mirror.** srmech's catalogs live at `srmech/amsc/attested/<key>/` and ship directly from there. No codegen mirror needed because srmech is the SSOT for its own catalogs. The catalog files are pure data (NDJSON, schemas, TOML) and have no LF normalization concern beyond what git autocrlf handles.

This is simpler than ephemerides because ephemerides's separation of `research/` (SSOT) and `_research/` (mirror) was a historical accident: ephemerides's framework code lives in `docs/antikythera-maths/research/` outside the wheel layout, so codegen mirrors it. srmech's framework code lives at `srmech/amsc/` directly inside the wheel layout; no mirror step is needed.

---

## §7. Q7 — Risk register

| # | Risk | Severity | Mitigation | Rollback if fires |
|---:|---|---|---|---|
| R1 | Import-path migration introduces subtle bugs in untested code paths (e.g., a code path that reads `__file__` on a framework module breaks because the module's location moved). | **Medium** | The `register_attested_root` mechanism (§3.3) is the primary risk surface. Phase 2 ships with a unit test that exercises the registration path with multiple roots and confirms catalog enumeration order is deterministic. Gate 4 (bridge surface parity) catches any divergence in observable behavior. | Revert Phase 3 PR; ephemerides goes back to internal `_research/attested_collector_*.py`. |
| R2 | ephemerides-spectral wheel build process breaks if `Requires-Dist: srmech>=X.Y.Z` isn't met at install time (e.g., srmech not yet on TestPyPI when ephemerides's CI builds). | **High** | Phase 2 ships srmech to TestPyPI BEFORE Phase 3 PR is opened. Phase 3 PR cannot be merged until srmech is on PyPI (not just TestPyPI) at the pinned version. CI workflow updated to install srmech from PyPI explicitly. | Revert Phase 3 PR; ephemerides has no external srmech dep. |
| R3 | srmech's TestPyPI release latency delays ephemerides-spectral's next release. | **Medium** | TestPyPI ships are fast (~minutes). The dependency is one-way and not circular. The latency risk is bounded by srmech's own publish-workflow timing. | Pin srmech to the last known-good version; ephemerides ships from the last green CI. |
| R4 | Circular-dep risk if srmech ever wants to import from ephemerides-spectral. | **Low** | srmech is the LOWER layer; it must not depend on ephemerides. Architecture decision documented in this scope file. Any future violation surfaces immediately at `pip install srmech` (cycle detection). | Refactor: srmech should never import ephemerides. |
| R5 | AMSC adapter tests in ephemerides may have hard-coded paths that break (e.g., a test that constructs a Path to `_research/attested_adapters/_base.py` for some introspection check). | **Low** | grep result shows no such hard-coded paths in `test_attested_collector.py`. Phase 3 prep step: full repo grep for `attested_collector_` and `attested_adapters` to catch any I missed. | Fix the test or update the path; Phase 3 amendment commit. |
| R6 | The `_research/attested_collector_*.py` mirror files may have circular or near-circular import relationships with codegen or other tests. | **Low** | Discovery shows mirror files import only from sibling mirror files via relative imports (`from .attested_collector_format`). No cross-package circularity. | None expected. |
| R7 | Pre-2010 canonical citations and cross-references between catalogs (if any) require revalidation post-refactor. | **Low** | Catalog SSOTs do not move; their bytes are unchanged. Citation hygiene is invariant. | None expected. |
| R8 | srmech package doesn't exist yet (no Python package, no publish workflow). Phase 2 must bootstrap from scratch — significantly more work than the conductor brief assumed. | **High** | Phase 2 scope is expanded to include: create `srmech/` package skeleton, `pyproject.toml`, `srmech/version.py`, `srmech/py.typed`, `.github/workflows/srmech-publish.yml`, `.github/workflows/srmech-ci.yml`, README, CHANGELOG. ~6-8 hours of bootstrap work beyond the framework-copy step. | Phase 2 cannot be reverted (it creates files in a previously-empty namespace); a "rollback" means deleting the srmech subtree. Documented in §8.2. |
| R9 | Two registered AMSC roots contain the same `source_key` (e.g., a `cmb_anomalies` in srmech's tree AND ephemerides's tree during a future migration). | **Low** | `register_attested_root` logs a warning and applies first-wins policy. Phase 2 unit test exercises this. The current state (Phase 1 through Phase 4) does NOT trigger this — all 19 ephemerides catalogs are unique. | First-wins is the policy; downstream consumers can audit via `get_local_kernel_state()`-style introspection. |
| R10 | The `byte-identical` parity guarantee at Phase 3 turns out to be impossible because some tool (e.g., scikit-build-core) emits non-deterministic build metadata. | **Medium** | Wheel build determinism is already a project requirement (`wheel.exclude = ["*.pyc", "__pycache__"]` in pyproject; manifest with `sort_keys=True`). If a non-determinism is discovered, Phase 3's parity gate is downgraded to "byte-identical except for documented build-system metadata fields" and the documented fields are enumerated in this scope file. | Honest-negative: amend the parity protocol to permit specific known-non-deterministic fields. |
| R11 | NimBLE-style "double init" mistake in the srmech bootstrap: if both srmech and ephemerides try to register the same root (e.g., ephemerides registers ephemerides's root, but a future srmech update also enumerates ephemerides's root by some discovery mechanism). | **Low** | The registration mechanism is push-only: srmech does NOT discover external roots. ephemerides PUSHES its root to srmech via `register_attested_root`. The asymmetry prevents double-registration by design. | None expected if the architecture is honored. |

**Top risk: R8 (srmech package doesn't exist).** This is the discovery that most expands Phase 2's scope. The conductor brief described Phase 2 as "create `srmech/amsc/` submodule, COPY framework code, srmech builds as a Python package with AMSC." That phrasing assumed srmech was already a buildable package; the discovery shows it is not. Phase 2 must bootstrap the package itself.

**Honest-negative on R8:** Without an existing srmech publish workflow, Phase 2 must include CI setup that the original brief did not anticipate. This adds an estimated 4-6 hours to Phase 2's effort. Phase 2's Pull Request will be larger than originally scoped. The user should be aware before approving Phase 1.

---

## §8. Q8 — Rollback protocol per phase

### §8.1 Phase 2 rollback

**Definition of rollback:** Delete the entire `srmech/` Python package subtree, the `.github/workflows/srmech-*.yml` files, the srmech entry on TestPyPI, and any references to srmech in this repo's documentation.

**Test that confirms rollback succeeded:** From clean checkout, `git status` shows zero new files under `srmech/`, `.github/workflows/srmech-*.yml`, or related paths. `pio run -e single_device_demo_jpl_queued` builds successfully (Phase 2 should not have touched anything in the EMDR project). `cd docs/antikythera-maths/ephemerides-spectral && pytest python/tests/` passes (Phase 2 should not have touched ephemerides).

**Blast radius:** Low. Phase 2 is purely additive: it creates a new package and copies framework code into it. Ephemerides-spectral is untouched. Rollback is `git revert <Phase-2-commit>` (or `rm -rf srmech/`).

**Cherry-pick-revertable:** Yes. Phase 2 is a single PR; reverting that PR restores the pre-Phase-2 state.

### §8.2 Phase 3 rollback

**Definition of rollback:** Revert the import-line changes in `bridge.py`, `cmb_anomalies_catalog.py`, `cmb_power_spectrum_catalog.py`, and `test_attested_collector.py`. Remove the `Requires-Dist: srmech` line from pyproject. Remove the bootstrap call from `ephemerides_spectral/__init__.py`. Revert `run_collectors.py` imports.

**Test that confirms rollback succeeded:** Wheel parity check between pre-Phase-3 and post-rollback wheels — they must be byte-identical (manifest.json's SHA-256 sums match, no `Requires-Dist: srmech`). Pytest suite passes.

**Blast radius:** Medium. Phase 3 touches 5 files plus pyproject.toml. Rollback is `git revert <Phase-3-PR-merge-commit>`. If Phase 3 has been on PyPI (i.e., a release was cut between Phase 3 and rollback), the release is yanked.

**Cherry-pick-revertable:** Yes. Phase 3 is a single PR; reverting that PR restores Phase 2's state.

### §8.3 Phase 4 rollback

**Definition of rollback:** Restore the deleted `_research/attested_collector_*.py` files and `_research/attested_adapters/` subtree. Restore the dropped entries in `emit_research_modules.py`'s `_INCLUDED_MODULES` and `_INCLUDED_SUBDIRS`. Restore the allowlist removal in `emit_attested_collections.py` (if Phase 4 removed it — though it should remain).

**Test that confirms rollback succeeded:** `python codegen/regenerate.py` produces `_research/attested_collector_*.py` files in the wheel-layout. The wheel built from the rollback state is byte-identical to the Phase 3 wheel (modulo the unused framework files).

**Blast radius:** Low. Phase 4 is purely subtractive (deletes dead code). Rollback is `git revert <Phase-4-commit>`.

**Cherry-pick-revertable:** Yes.

### §8.4 Aggregate rollback discipline

Each phase is a single PR (or a single merge commit on the protected branch). Reverting a phase reverts to the previous phase's state. This is the cherry-pick-revertable contract the user's directive requires.

**Mid-flight blast radius:** If a phase is half-applied (e.g., Phase 3 PR is open but not merged), no production state is affected. The branch can be force-pushed or closed.

**Post-release rollback:** If a phase has been released to PyPI and a critical bug surfaces, the release is YANKED on PyPI (not deleted — that breaks pip's resolution for downstream consumers who already pinned). A patch release is cut from the rollback state. This is the standard PyPI escape hatch and is independent of the refactor.

---

## §9. Q9 — Phase 2/3/4 PR plan

### §9.1 Phase 2 — Extract: bootstrap srmech + copy AMSC framework

**Branch name:** `refactor/amsc-to-srmech-phase-2-extract`

**Changeset:**

**Created files (~15 files + 12 framework files = 27 total):**
- `srmech/__init__.py` (minimal package marker, version export)
- `srmech/py.typed` (empty PEP 561 marker)
- `srmech/version.py` (SSOT for `__version__`)
- `srmech/pyproject.toml` (build configuration; `[project.optional-dependencies] collectors = [...]`)
- `srmech/README.md` (brief description; canonical homepage link)
- `srmech/CHANGELOG.md` (initial entry: "v0.1.0 — initial extract of AMSC framework from ephemerides-spectral")
- `srmech/LICENSE` (GPL-3.0-or-later, matching ephemerides)
- `srmech/amsc/__init__.py` (re-exports: `MPRRecord`, `Descriptor`, `get_attested_dataset`, etc.)
- `srmech/amsc/format.py` (COPY of `docs/antikythera-maths/research/attested_collector_format.py`; rewrite internal imports)
- `srmech/amsc/descriptor.py` (COPY of `attested_collector_descriptor.py`)
- `srmech/amsc/catalog.py` (COPY of `attested_collector_catalog.py`; add `register_attested_root` API and the registered-roots state per §3.3)
- `srmech/amsc/gap_suggester.py` (COPY of `attested_collector_gap_suggester.py`)
- `srmech/amsc/adapters/__init__.py` (COPY of `attested_adapters/__init__.py`)
- `srmech/amsc/adapters/_base.py` (COPY; rewrite internal imports per §3.4)
- `srmech/amsc/adapters/{html_scraper,json_api,csv_bulk,netcdf_grid,geotiff_bbox,literature_curated}.py` (COPIES)
- `srmech/amsc/attested/__init__.py` (empty; future catalog SSOT root)
- `srmech/tests/__init__.py`
- `srmech/tests/test_register_attested_root.py` (new — unit test for the cross-package root registration mechanism)
- `srmech/tests/test_amsc_import.py` (smoke test: `from srmech.amsc.catalog import get_attested_dataset` works)
- `.github/workflows/srmech-ci.yml` (mirrors ephemerides-spectral-ci.yml shape: pytest on push/PR)
- `.github/workflows/srmech-publish.yml` (mirrors ephemerides-spectral-publish.yml: build wheel, twine upload to TestPyPI on tag, optional PyPI on manual dispatch)
- `.github/workflows/srmech-autotag.yml` (mirrors ephemerides pattern)

**Modified files (small):**
- `docs/antikythera-maths/ephemerides-spectral/codegen/emit_attested_collections.py` (add `_INCLUDED_CATALOGS` allowlist per §6.2; behavior unchanged because allowlist contains all 19 current catalogs)

**Untouched:** ephemerides-spectral package source code, tests, codegen orchestrator (regenerate.py), other antikythera-maths packages, EMDR firmware.

**Test-pass criteria:**
- `srmech-ci.yml` workflow: green on push (pytest passes for srmech's own tests).
- `ephemerides-spectral-ci.yml` workflow: green (unchanged behavior; allowlist is no-op).
- Local `pip install -e srmech/` succeeds.
- Local `cd srmech && pytest tests/` passes (6+ unit tests including registration test).
- Local `cd docs/antikythera-maths/ephemerides-spectral && python codegen/regenerate.py` produces a manifest byte-identical to pre-Phase-2 (Gate 3 of the parity protocol).
- Manual: `pip install srmech` from TestPyPI smoke test confirms package is installable.

**Estimated effort:** 12-16 hours (4h package skeleton + CI workflows; 3h copy + internal-import rewrite + `register_attested_root`; 3h unit tests; 2h TestPyPI publish + smoke; 2h allowlist + manifest determinism; 2-4h debugging).

**Dependencies on earlier phases:** Phase 1 (this scope document) must land.

### §9.2 Phase 3 — Bridge: ephemerides imports `srmech.amsc`

**Branch name:** `refactor/amsc-to-srmech-phase-3-bridge`

**Changeset:**

**Modified files (5 + pyproject):**
- `docs/antikythera-maths/ephemerides-spectral/python/ephemerides_spectral/bridge.py` (2 import lines per §4.1)
- `docs/antikythera-maths/ephemerides-spectral/python/ephemerides_spectral/_research/cmb_anomalies_catalog.py` (1 line)
- `docs/antikythera-maths/ephemerides-spectral/python/ephemerides_spectral/_research/cmb_power_spectrum_catalog.py` (1 line)
- `docs/antikythera-maths/ephemerides-spectral/python/tests/test_attested_collector.py` (18 lines via 5 sed patterns)
- `docs/antikythera-maths/ephemerides-spectral/codegen/run_collectors.py` (3 lines)
- `docs/antikythera-maths/ephemerides-spectral/python/ephemerides_spectral/__init__.py` (add bootstrap registration block per §4.4)
- `docs/antikythera-maths/ephemerides-spectral/python/pyproject.toml` (add `srmech>=X.Y.Z` to `dependencies`)

**Created files:** None.

**Deleted files:** None.

**Test-pass criteria:**
- All five parity gates pass (§5.1-5.5).
- `ephemerides-spectral-ci.yml` workflow: green.
- WSL smoke (`wsl bash scripts/smoke_local.sh`): green (per `memory/feedback_run_wsl_smoke_before_amsc_push.md`).
- Pre-merge smoke install: `pip install ephemerides-spectral` from a TestPyPI build of Phase 3 succeeds and the bridge surface returns identical output to Phase 2's wheel.

**Estimated effort:** 6-8 hours (2h rewrites + bootstrap; 3h run all five parity gates; 2h divergence handling; 1h WSL smoke + review).

**Dependencies on earlier phases:** Phase 2 must land AND srmech must be on PyPI (not just TestPyPI) at the pinned version. Phase 3 PR cannot merge until that pin resolves.

### §9.3 Phase 4 — Cleanup: remove duplicate framework code from ephemerides

**Branch name:** `refactor/amsc-to-srmech-phase-4-cleanup`

**Changeset:**

**Deleted files (~12 from the wheel layout):**
- `docs/antikythera-maths/research/attested_collector_format.py` (SSOT — deleted because srmech is now SSOT for AMSC framework)
- `docs/antikythera-maths/research/attested_collector_descriptor.py`
- `docs/antikythera-maths/research/attested_collector_catalog.py`
- `docs/antikythera-maths/research/attested_collector_gap_suggester.py`
- `docs/antikythera-maths/research/attested_adapters/{__init__,_base,html_scraper,json_api,csv_bulk,netcdf_grid,geotiff_bbox,literature_curated}.py` (8 files)
- `docs/antikythera-maths/ephemerides-spectral/python/ephemerides_spectral/_research/attested_collector_*.py` (mirrored copies; these regenerate from `_INCLUDED_MODULES` so deletion is via the codegen modification)
- `docs/antikythera-maths/ephemerides-spectral/python/ephemerides_spectral/_research/attested_adapters/` (subdir; deletion via `_INCLUDED_SUBDIRS` modification)

**Modified files:**
- `docs/antikythera-maths/ephemerides-spectral/codegen/emit_research_modules.py` (drop framework entries from `_INCLUDED_MODULES`; drop `attested_adapters` from `_INCLUDED_SUBDIRS`)
- `docs/antikythera-maths/ephemerides-spectral/python/CHANGELOG.md` (document the cleanup release)

**Test-pass criteria:**
- `python codegen/regenerate.py` produces a manifest WITHOUT entries for the deleted framework files. Manifest's `n_files` decreases by ~12.
- ephemerides wheel size decreases by ~100 KB.
- All five parity gates pass when COMPARING Phase 4 against Phase 3 (the wheel diff is exactly: ~12 files removed from `_research/`; bridge behavior identical).
- ephemerides-spectral test suite passes against Phase 4 wheel.

**Estimated effort:** 3-4 hours (1h delete files + update codegen; 1h regenerate + verify manifest; 1h pytest + parity checks; 1h CHANGELOG + PR).

**Dependencies on earlier phases:** Phase 3 must land.

### §9.4 Aggregate effort estimate

| Phase | Effort |
|---|---:|
| Phase 1 (this scope) | 3-4 hours |
| Phase 2 (extract + bootstrap) | 12-16 hours |
| Phase 3 (bridge) | 6-8 hours |
| Phase 4 (cleanup) | 3-4 hours |
| **Total Phases 2-4** | **21-28 hours** (~3-4 working days) |

Plus contingency for the discovered R8 risk (srmech package didn't exist), which is already baked into Phase 2's estimate.

### §9.5 Ship sequencing dependencies

```
main → Phase 1 (this scope) → Phase 2 → srmech on TestPyPI → srmech on PyPI → Phase 3 → Phase 4
```

The critical-path bottleneck is the TestPyPI-to-PyPI promotion of srmech between Phase 2 and Phase 3. The user must explicitly promote srmech to PyPI; this is not automated in the publish workflow.

---

## §10. Summary

Phase 1 scopes a four-phase refactor with five GO/NO-GO parity gates at Phase 3 (wheel byte-diff, pytest, codegen manifest, bridge surface, CLI).

**AMSC framework:** 12 files (~2,894 LOC) at `research/attested_collector_*.py` + `research/attested_adapters/`. `tool_schema.py` stays in ephemerides (ephemerides-specific introspection).

**srmech current state:** no Python package, no workflow, no PyPI. Phase 2 must bootstrap from scratch (~12-16 hours).

**Layout:** terse names under `srmech/amsc/` (`format.py`, `descriptor.py`, `catalog.py`, `gap_suggester.py`, `adapters/`).

**Import-swap (Phase 3):** 22 wheel-affecting lines across 4 files + 3 codegen-only lines + 1 bootstrap registration block. The load-bearing design is `register_attested_root(path, *, source)` on `srmech.amsc.catalog` letting ephemerides push its `_research/attested/` subtree at import time. The catalog SSOTs do NOT migrate.

**Allowlist:** Phase 2 adds `_INCLUDED_CATALOGS` (19 catalog names) to `emit_attested_collections.py`; no-op today, defensive against future cross-contamination.

**Top risks:** R8 (srmech package doesn't exist — Phase 2 expanded) and R2 (Phase 3 blocked until srmech on PyPI).

**Rollback:** each phase = single revertable PR. Phase 2 purely additive; Phase 3 = import-swap revert; Phase 4 = restore framework files via codegen revert.

**Aggregate Phase 2-4 effort:** 21-28 hours.

The plan honors "unconditional support" via mechanical parity gates. **Recommendation: scope-only**; Phase 2 PR opens after Phase 1 lands.
