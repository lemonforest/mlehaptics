# srmech changelog

All notable changes to this package will be documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this package uses semantic versioning.

## [Unreleased]

## [0.1.1rc6] - 2026-05-13

### Added — Task #201 Phase B4: NDJSON streaming reader C port

Second C/Python parity surface. Native ``srmech_ndjson_iter`` does
file-IO + line tokenisation in C; JSON parsing stays in Python.
Byte-exact line-set agreement pinned by the new pytest parity
suite in ``tests/test_native_ndjson.py`` (18 tests including
chunk-boundary span + max-line-overflow + CRLF / mixed-EOL fixtures).

#### C side (`docs/srmech/c/`)

- **`src/srmech_ndjson.c`** *(NEW)* — streaming line reader.
  Reads 64 KiB chunks via ``fread``; assembles partial lines into a
  static 1 MiB buffer (single-thread contract); invokes the caller's
  callback with ``(line, line_len, lineno, user)`` per non-empty
  line. Empty lines are silently skipped but ``lineno`` still
  advances, so callback-side error messages line up byte-exactly
  with the file (verified by ``test_read_ndjson_malformed_line_lineno_correct``).
  CR-stripping at line boundaries matches Python's
  ``raw.rstrip("\r\n")``.
- **`include/srmech.h`** — callback typedef gains ``size_t lineno``
  parameter; ``SRMECH_ABI_VERSION`` bumped to **2**.
- **`src/srmech_meta.c`** — ``srmech_abi_version()`` now returns the
  macro indirectly so a missed manual bump can't silently lie.

#### Python side (`docs/srmech/python/srmech/amsc/`)

- **`_native.py`** —
  - ``EXPECTED_ABI_VERSION = 2`` (matches C-side bump).
  - ``_NDJSON_LINE_CB`` — ctypes ``CFUNCTYPE`` mirroring the
    4-argument C callback typedef.
  - ``ndjson_lines_c(path) -> list[(lineno, bytes)]`` — Python
    wrapper that runs the native iterator under a ctypes callback
    and collects ``(lineno, line_bytes)`` tuples.
  - ``NativeNDJsonError`` — distinct from ``MPRValidationError``
    because the failure is upstream of JSON parsing (file IO or
    overflow). Translated to ``OSError`` at the ``format.read_ndjson``
    boundary so callers see consistent semantics.
- **`format.py`** — ``read_ndjson()`` dispatches via the native
  iterator when ``HAS_NATIVE`` is True; pure-Python streaming path
  remains unchanged. JSON parsing (``json.loads`` +
  ``MPRRecord.from_json_line``) stays in Python on both paths.

#### Tests

- **`tests/test_native_ndjson.py`** *(NEW)* — 18 parity tests:
  12 fixture inputs (empty file, no-trailing-newline, CRLF / mixed-EOL,
  blank-line patterns, long lines, 100-record stress, etc.) + the
  ``format.read_ndjson`` dispatch test + lineno-fidelity test +
  missing-file ``OSError`` test + 1000-record stress + chunk-
  boundary span test + ``SRMECH_ERR_OVERFLOW`` test (1.25 MiB line
  rejection).
- All 59 existing tests still pass; all 18 native-sha256 tests
  still pass (ABI v2 lift didn't break the v1 surface).

#### Notes on design

- **No JSON parsing in C.** srmech's hot path is the file-IO + line
  tokenisation overhead (Python's text-mode line iteration has
  per-line allocator pressure that adds up across thousand-row
  catalogs). Doing the JSON parse in C would need a vendored JSON
  parser; bytes returned to Python and parsed via
  ``MPRRecord.from_json_line`` is byte-equivalent and avoids that
  surface-area expansion.
- **Static 1 MiB line buffer.** Trade-off: ``srmech_ndjson_iter`` is
  not thread-safe. The two callsites today (Python
  ``format.read_ndjson`` and any future C-side parity test) are
  serial. Phase B6 audit may revisit, but for srmech's data-pipeline
  workload — read a catalog file once, iterate — single-thread is
  the correct model.
- **Eager line collection.** The native path returns a list rather
  than a generator. For the catalog files srmech actually reads
  (small, few KB to a few MB), the eager materialisation is fine.
  If a future use case wants a true generator, the callback can be
  wired to a ``queue.Queue`` + worker thread, but we're not paying
  that complexity until a real need surfaces.

## [0.1.1rc5] - 2026-05-13

### Added — Task #201 Phase B3: SHA-256 C port (first native symbol)

First C/Python parity surface in srmech. Native ``srmech_sha256_hex``
replaces ``hashlib.sha256`` on the hot path used by every adapter's
``attest()`` step. Byte-exact agreement pinned by the new pytest
parity suite in ``tests/test_native_sha256.py`` (18 tests) plus the
C-side smoke tests in ``c/test/test_srmech_sha256.c`` (12 assertions
against FIPS 180-4 fixtures + padding-boundary edge cases).

#### C side (`docs/srmech/c/src/`)

- **`srmech_sha256.c`** — self-contained SHA-256 (FIPS 180-4). No
  OpenSSL / libcrypto dependency. ~200 lines, JPL-Power-of-Ten-
  compatible (bounded loops, no malloc, no goto, ≥2 asserts/fn).
  Public entry: ``srmech_sha256_hex(data, data_len, out_hex)``.
- **`srmech_meta.c`** — ``srmech_version()`` + ``srmech_abi_version()``
  metadata accessors. Called by the Python ctypes shim at load time
  to verify ABI agreement before binding.

The header (`docs/srmech/c/include/srmech.h`) grows
``SRMECH_ABI_VERSION = 1`` and declarations for the three new
symbols.

#### Python side (`docs/srmech/python/srmech/amsc/`)

- **`_native.py`** *(NEW)* — ctypes wrapper mirroring
  ``ephemerides_spectral/_native_bip.py``:
  - ``HAS_NATIVE`` boolean — guards every callsite.
  - ABI-version check at load time; mismatch falls back to Python
    silently (LOAD_ERROR is populated).
  - Three-strategy library discovery: ``srmech.__path__`` walk,
    relative-to-module-file, ``importlib.metadata.files()`` fallback.
    The third strategy is load-bearing for scikit-build-core editable
    installs where the .py files live in the source tree but the
    CMake-installed .so/.dll/.dylib lives in site-packages.
  - ``sha256_hex_c(data) -> str`` — native entry. Handles empty
    bytes correctly (mirrors hashlib.sha256(b"") semantics).
- **`format.py`** — ``sha256_bytes()`` now dispatches to native
  when available, falls back to ``hashlib`` otherwise. The
  user-facing API is unchanged; the implementation is one
  branch deeper.

#### Tests

- **`tests/test_native_sha256.py`** *(NEW)* — 18 parity tests:
  15 fixture inputs (empty, FIPS B.2, B.3, padding boundaries at
  55/56/63/64/65/119/128 bytes, 1 KiB, 64 KiB, 256 KiB),
  ``format.sha256_bytes`` dispatch test, version/ABI lock test,
  200-input randomised parity test. Auto-skipped when
  ``HAS_NATIVE`` is False (pure-Python wheel / Pyodide install).
- **`c/test/test_srmech_sha256.c`** *(NEW)* — 12 C-side asserts
  against FIPS 180-4 vectors + padding edge cases. Exits 0 on
  all-pass.

#### Build

- **`pyproject.toml`** — Phase B2's ``wheel.py-api = "py3"`` +
  ``wheel.platlib = false`` overrides REMOVED. The wheel is now
  legitimately platform-tagged (e.g.
  ``srmech-0.1.1rc5-cp312-cp312-linux_x86_64.whl``) and contains
  ``srmech/_native/libsrmech.{so,dll,dylib}``.
- **`.github/workflows/srmech-publish.yml`** —
  ``build-wheel`` sanity check inverted: rejects py3-none-any
  output (would indicate CMake short-circuited and the .so is
  missing), requires ``srmech/_native/`` to contain a .so / .dll /
  .dylib in the wheel.

#### Phase B7 follow-up

The ``build-wheel`` job still runs on a single Ubuntu cell, so only
the Linux wheel is published at rc5. Mac / Windows users on TestPyPI
get the pure-Python wheel (built by ``build-pure-wheel``) and the
pure-Python ``hashlib`` fallback. Phase B7 adds the cibuildwheel
matrix that produces wheels for all platform/Python combinations.

## [0.1.1rc4] - 2026-05-13

### Infrastructure — Task #201 Phase B2: scikit-build-core + pyproject-pure swap

Switches srmech's build backend from hatchling to **scikit-build-core +
CMake**, mirroring ephemerides-spectral. Adds the
`pyproject-pure.toml` hatchling-fallback file for the Pyodide / WASM
build path. Rewrites `srmech-publish.yml` with the three-job shape
(scikit-build-core wheel + sdist + pure-Python wheel) that mirrors
`ephemerides-spectral-publish.yml`.

**Phase B2 still ships py3-none-any wheels** — until Phase B3 lands
real C code in `docs/srmech/c/src/`, the CMake step short-circuits
to "no library" and the wheel is tagged py3-none-any via the
`wheel.py-api = "py3"` + `wheel.platlib = false` overrides in
pyproject.toml. Both overrides come back OUT at Phase B3 so the
wheel becomes legitimately platform-tagged once the native binary
is real.

#### Added — `pyproject-pure.toml`

Parallel pyproject mirroring `docs/antikythera-maths/ephemerides-spectral/python/pyproject-pure.toml`:

- Uses `hatchling` backend instead of `scikit-build-core`.
- Same `[project]` block (name, version, deps, classifiers, urls) so
  the pure wheel and the platform wheel are interchangeable at
  install time.
- Excludes `srmech/_native/*` from both wheel + sdist so accidental
  rebuild artifacts can't leak in.
- Version-locked to `pyproject.toml`'s version by a workflow guard
  (see "Verify pyproject-pure.toml version matches main" step).

#### Changed — `pyproject.toml`: hatchling → scikit-build-core

- `build-system.requires = ["scikit-build-core>=0.10", "cmake>=3.23"]`
- `build-system.build-backend = "scikit_build_core.build"`
- New `[tool.scikit-build]` block:
  - `cmake.source-dir = ".."` points at `docs/srmech/CMakeLists.txt`
  - `wheel.packages = ["srmech"]`
  - `wheel.py-api = "py3"` + `wheel.platlib = false` — Phase B2 only,
    keeps the wheel py3-none-any while CMake validates the
    infrastructure. Removed at Phase B3.
  - `sdist.include` adds the C tree one directory up (the same
    pattern ephemerides-spectral uses for its CMakeLists.txt + c/).
- `[project.optional-dependencies].dev` gains `scikit-build-core>=0.10`
  and `cmake>=3.23`; retains `hatchling` for the pyproject-pure swap
  build path.

#### Changed — `.github/workflows/srmech-publish.yml`

Replaced the single-`build` job with a three-job pattern mirroring
`ephemerides-spectral-publish.yml`:

- **`build-wheel`** — scikit-build-core wheel via `python -m build
  --wheel` (the `--wheel` flag skips the sdist→wheel detour that
  trips scikit-build-core's `cmake.source-dir=".."` indirection when
  the sdist is unpacked).
- **`build-sdist`** — `python -m build --sdist`, twine-strict-check.
- **`build-pure-wheel`** — swaps in `pyproject-pure.toml` over
  `pyproject.toml` (saved as `.platform`), runs hatchling build,
  restores. Includes the version-match guard + PyPI 512-char
  description guard, copied wholesale from ephemerides-spectral's
  workflow.
- **`publish`** — `needs: [build-wheel, build-sdist, build-pure-wheel]`.
  Same rc-routing logic; `cp -n` dedupe in the artefact-collection
  step handles the case where build-wheel and build-pure-wheel produce
  identically-named wheels at Phase B2 (will not happen at Phase B3+
  when build-wheel becomes platform-tagged).

#### Phase B7 follow-up

`build-wheel` at Phase B7 graduates from a single Ubuntu cell to a
cibuildwheel matrix (Linux / macOS / Windows × py3.10–3.14). The
trigger for that promotion: C/Python parity tests passing in CI
across all three platforms (Phase B5 complete).

## [0.1.1rc3] - 2026-05-13

### Infrastructure — Task #201 Phase B1: srmech C scaffolding

First phase of the **srmech build-out to peer-quality with
ephemerides-spectral** (Task #201). Ships the C tree scaffolding so
Phase B2 can wire scikit-build-core in next. **Pure-Python wheel
contents are byte-identical to rc2** — this release adds files outside
the wheel, no API changes, no behaviour changes.

#### Added — C tree scaffolding (`docs/srmech/c/` + `docs/srmech/CMakeLists.txt`)

Mirrors `docs/antikythera-maths/ephemerides-spectral/c/` layout:

- `c/include/srmech.h` — public C API header. Status enum
  (`srmech_status_t`), version macros, and forward declarations
  for the three planned symbols (`srmech_sha256_hex`,
  `srmech_ndjson_iter`, `srmech_toml_canonical_hash`). No
  definitions yet — those land in Phases B3–B5.
- `c/src/.gitkeep` — empty source directory placeholder.
- `c/test/.gitkeep` — empty test directory placeholder.
- `c/Makefile` — local build/test/parity flow mirroring
  ephemerides-spectral's Makefile. Phase B1 targets noop
  gracefully (no .c files → no .a archive); Phase B3 onward they
  do real work.
- `c/README.md` — phase plan, layout, build instructions.
- `c/JPL_AUDIT.md` — JPL Power-of-Ten audit log placeholder
  (populated in Phase B6).
- `c/.gitignore` — `build/`.
- `c/.pages` — mkdocs nav stub.
- `CMakeLists.txt` (at `docs/srmech/`) — top-level CMake driver,
  mirrors `docs/antikythera-maths/ephemerides-spectral/CMakeLists.txt`.
  At Phase B1 it short-circuits library creation when `c/src/*.c`
  is empty; Phase B2 wires it into pyproject.toml via
  scikit-build-core's `cmake.source-dir = ".."`.

#### Why Phase B1 stops here

The scaffolding is intentionally **inert at rc3**: no .c files means
no library is built, the existing hatchling pyproject.toml backend is
unchanged, and the wheel content is byte-identical to rc2. This
verifies the scaffolding doesn't disturb the existing build before
Phase B2 starts moving the build backend.

#### Phase plan (Task #201 B1–B7)

| Phase | Deliverable                                    | Version    |
| ----- | ---------------------------------------------- | ---------- |
| B1    | C tree scaffolding (this release)              | `0.1.1rc3` |
| B2    | scikit-build-core + CMake + pyproject-pure     | `0.1.1rc4` |
| B3    | `srmech_sha256_hex` — first symbol + parity test | `0.1.1rc5` |
| B4    | `srmech_ndjson_iter` — streaming NDJSON reader | `0.1.1rc6` |
| B5    | `srmech_toml_canonical_hash` — descriptor hash | `0.1.1rc7` |
| B6    | JPL Power-of-Ten audit + JPL_AUDIT.md          | `0.1.1rc8` |
| B7    | cibuildwheel matrix + production v0.2.0 cut    | `0.2.0`    |

Each rc auto-routes to TestPyPI via `srmech-publish.yml`'s rc-suffix
gate; the non-rc `0.2.0` tag is the human-in-loop gate for
production PyPI.

## [0.1.1rc2] - 2026-05-13

### Fixed — hallucination in shipped metadata

- **`pyproject.toml` description, `README.md`, `srmech/__init__.py` docstring**: corrected the package's expanded name from the hallucinated "spectral-resonance mechanism" to the correct **Stored-Relationship Mechanism** (per the srmech research notebook title `# Stored-Relationship Mechanism (srmech) — Research Notebook` and the project memory `project_stored_relationship_mechanism_spike.md`). The error was caught in the TestPyPI verification of v0.1.1rc1 — the wrong text shipped to TestPyPI as srmech-0.1.1rc1's PyPI Summary metadata; rc2 corrects it.
- **`pyproject.toml` keywords**: `"spectral-resonance"` → `"stored-relationship"`.
- **`README.md` Status line** updated to reflect current state (v0.1.0 on PyPI, v0.1.1rcN iterating on TestPyPI toward Task #201 peer-quality cut).

No behaviour or API changes. Wheel + sdist content identical to rc1 except for metadata fields.

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
