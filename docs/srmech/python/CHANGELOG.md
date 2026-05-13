# srmech changelog

All notable changes to this package will be documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this package uses semantic versioning.

## [Unreleased]

## [0.1.1rc1] - 2026-05-13

### Infrastructure — Task #200 Phase A: revert cibuildwheel + add rc-routing

This release reverts the premature cibuildwheel adoption from PR #383
and introduces **rc-suffix auto-routing** in the publish workflow.

#### Reverted (the cibuildwheel mis-application)

- **`.github/workflows/srmech-publish.yml`** restored to the
  single-build-job shape (``python -m build`` produces sdist +
  py3-none-any wheel). cibuildwheel v3.x rejects pure-Python builds
  by design ("Build failed because a pure Python wheel was
  generated") — the matrix that PR #383 introduced was structurally
  incompatible with srmech's current pure-Python state. The
  ``ephemerides-spectral-publish.yml`` template adopted there
  legitimately uses cibuildwheel because that package ships a
  native C library; srmech does not (yet).
- **`docs/srmech/python/pyproject.toml`** ``[tool.cibuildwheel]``
  configuration block removed. Replaced with an explanatory comment
  documenting that cibuildwheel returns once srmech grows the
  C/Python parity surface (Task #201 Phase B).
- The failed ``srmech-v0.1.1`` tag was deleted before any artifact
  reached TestPyPI or PyPI; ``v0.1.0`` remains the current TestPyPI
  release.

#### Added — rc-suffix auto-routing (`srmech-publish.yml`)

- Tag ``srmech-vX.Y.ZrcN`` → publishes to **TestPyPI** (testpypi
  environment) automatically. No manual workflow_dispatch needed.
- Tag ``srmech-vX.Y.Z`` (no rc suffix) → publishes to **PyPI**
  (pypi environment). The act of tagging a non-rc version IS the
  human-in-loop gate for production releases.
- ``workflow_dispatch`` with ``target ∈ {testpypi, pypi}`` retained
  as a manual override path.
- Tag-version regex extended to accept rcN suffix:
  ``r"srmech-v(\d+\.\d+\.\d+(?:rc\d+)?)"``. The version-match
  check now also logs the routing decision so the run page makes
  TestPyPI-vs-PyPI obvious.
- Same rc-routing pattern simultaneously added to
  ``ephemerides-spectral-publish.yml`` for sibling consistency.

#### Version-discipline policy (going forward)

- **Every srmech release between now and peer-quality with
  ephemerides-spectral** ships as an rc on TestPyPI:
  ``0.1.1rc1``, ``0.1.1rc2``, ``0.1.2rc1``, …
- **No non-rc tag pushed** until srmech has Python/C parity, JPL
  Power-of-Ten C standard discipline, scikit-build-core build,
  and cibuildwheel matrix legitimately producing platform wheels.
- Each rc-tagged release is auto-shipped to TestPyPI; the next rc
  iteration is the response to whatever the prior rc-test surfaced.

#### Tests + parity

- All 59 srmech tests pass post-revert (no test changes).
- ephemerides-spectral tests still pass with this srmech version
  (the `srmech>=0.1.0` floor in ephemerides-spectral's
  `pyproject.toml` is satisfied by `0.1.1rc1`; pre-release versions
  resolve normally as PEP 440 allows).

#### History link

Task #200 Phase 1 cibuildwheel adoption (PR #383, merged) → Phase A
revert (this release). The premature cibuildwheel adoption was
caught by the publish workflow's own pure-Python-wheel sanity check
failing under cibuildwheel v3.x's defensive build-time error.

### Notes — Task #197 Phase 4 cleanup (2026-05-13)

Phase 4 is the **final phase** of the AMSC-to-srmech refactor (Task #197). It does
not change the srmech package itself; it cleans up the upstream duplicate copies in
ephemerides-spectral now that Phase 3's import-swap has settled:

- ephemerides-spectral deletes 12 vendored AMSC framework modules (4 top-level +
  8 adapters) from its `_research/` mirror and its `docs/antikythera-maths/research/`
  SSOT. ephemerides-spectral's codegen `_INCLUDED_MODULES` / `_INCLUDED_SUBDIRS`
  are updated to no longer mirror the deleted framework into the wheel.
- ephemerides-spectral's wheel shrinks by ~37 KB (~4.7 %) and its codegen
  `manifest.json` n_files drops from 154 to 142.
- All 5 Phase 1 parity gates remain green at the Phase 4 boundary; srmech
  in-isolation 59/59 tests pass (unchanged from Phase 3); ephemerides-spectral
  pytest is byte-identical to the Phase 3 baseline (2128 passed + 42 skipped
  = 2170 collected).
- `srmech v0.1.0` is now ready for the **first TestPyPI release**. See
  `TESTPYPI_RELEASE_NOTES_v0.1.0.md` in this directory for the release
  procedure (autonomous TestPyPI publish via the `srmech-v0.1.0` tag through
  `.github/workflows/srmech-publish.yml`; PyPI release remains human-in-loop).

## [0.1.0] - 2026-05-13

### Added

- **Initial extract of the AMSC framework from `ephemerides-spectral`** as part of Task #197 (AMSC-to-srmech refactor, Phase 2). The framework lives under `srmech.amsc.*`:
  - `srmech.amsc.format` — Mathematical Provenance Record (MPR) v1 format: `MPRRecord` dataclass, NDJSON streaming IO (`read_ndjson` / `write_ndjson`), `validate_mpr_record`, `sha256_bytes`, schema-version + mandatory-field constants.
  - `srmech.amsc.descriptor` — descriptor TOML loader: `Descriptor`, `load_descriptor`, `discover_descriptors`, `render_template` (deliberately minimal name-substitution + Python format-spec; no Jinja), `descriptor_hash` (canonical-serialised), `DescriptorValidationError`.
  - `srmech.amsc.catalog` — universal bridge surface: `list_attested_sources` (with `adapter_class` filter), `get_attested_dataset` (paginated, T0+T1+T2+T3 tiered), `get_attested_descriptor`, `attestation_audit`, `iter_attested_dataset`, T2 local-kernel overlay (`use_local_kernel` / `clear_local_kernel` / `get_local_kernel_state`).
  - `srmech.amsc.gap_suggester` — schema-gap-driven trigger (`suggest_gap_collections`); the lazy-imported classifier + probe sources are ephemerides-specific and remain in ephemerides-spectral.
  - `srmech.amsc.adapters` — six adapter modules: `html_scraper`, `json_api`, `csv_bulk`, `netcdf_grid` (stub), `geotiff_bbox` (stub), `literature_curated`; plus `_base.py` (`ADAPTERS` registry, `attest`, `parser_rule_hash`, `run` composer).
- **`register_attested_root(path, *, source)`** — the load-bearing cross-package API added in `srmech.amsc.catalog`. Downstream packages whose catalog SSOTs live outside `srmech/amsc/attested/` push their roots at package-import time; subsequent `_descriptors()` calls enumerate the union of srmech's own root + all registered roots in registration order. Conflict policy: first-registered wins with a warning.
- **`list_registered_roots()`** — introspection of currently-registered roots (srmech's own + every external). Used by tests and diagnostic output.
- **`srmech/amsc/attested/`** — empty SSOT subtree reserved for future srmech-primary catalogs (e.g. the `citations_curated` catalog planned for Spike #23).
- **CI workflows** under `.github/workflows/`:
  - `srmech-ci.yml` — pytest on push/PR against `docs/srmech/python/**`, 4-cell matrix (Ubuntu/macOS/Windows × Py3.12 + Ubuntu × Py3.10 floor).
  - `srmech-publish.yml` — build sdist + py3-none-any wheel on `srmech-v*` tag, publish to PyPI via trusted OIDC; manual workflow_dispatch can target TestPyPI.
  - `srmech-autotag.yml` — autotag on `pyproject.toml` version bump.

### Notes

- **Phase 2 is purely additive.** No ephemerides-spectral files are touched. Phase 3 (separate PR, not yet open) will rewire ephemerides-spectral's bridge to import from `srmech.amsc.*`; the byte-identical-wheel parity gate from the Phase 1 scope document applies there, not here.
- **Cross-package gap_suggester deviation.** `srmech.amsc.gap_suggester.suggest_gap_collections()` lazy-imports `.dynamical_regime_catalog` and `.dynamical_regime_probes_data`, which are ephemerides-specific and not shipped by srmech. Calling the function from a context where those modules aren't reachable (e.g. srmech in isolation, no ephemerides installed) will raise `ImportError` at call time. The Phase 1 scope did not flag this; ephemerides-spectral consumers (the only known caller) are unaffected because the relative imports resolve inside ephemerides's `_research/` mirror until Phase 3, then via Phase 3's import-swap.
- **`parser_version` stamp.** Changed from `"ephemerides-spectral X.Y.Z"` to `"srmech X.Y.Z"` in T3 live-fetch attestation blocks: srmech is now the parser. Committed NDJSON files retain whatever `parser_version` was stamped at collection time; only future T3 runs differ. No effect on the Phase 3 wheel parity gate (T3 is runtime, not committed bytes).
