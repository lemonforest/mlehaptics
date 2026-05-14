# srmech changelog

All notable changes to this package will be documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this package uses semantic versioning.

## [Unreleased]

## [0.2.0] - 2026-05-14

### Task #201 Phase B7 — production cut to PyPI

First **production PyPI** release of native-C-accelerated srmech.
Content is functionally identical to **`0.2.0rc2`** on TestPyPI;
only the version string changes (rc-suffix stripped) and the
docs lose the rc-cycle commentary. The tag-routing claim in
`srmech-publish.yml` directs a non-rc tag to the production PyPI
trusted-publisher environment.

#### What v0.2.0 ships, headline

The Task #201 build-out (rc3 → rc9 + rc1 → rc2 = 11 TestPyPI
rcs across phases B1 through B7) turned srmech from a pure-Python
AMSC framework (the v0.1.0 ship) into a native-C-accelerated
multi-platform package at peer quality with ephemerides-spectral:

- **Native C library** (`srmech_sha256_hex`, `srmech_ndjson_iter`,
  + version / ABI accessors) shipped under `srmech/_native/`
  inside platform-tagged wheels.
- **15-cell cibuildwheel matrix** — Linux (manylinux_2_28) × macOS
  × Windows × py3.10 / 3.11 / 3.12 / 3.13 / 3.14. Each cell runs
  `test_native_sha256.py` + `test_format.py` to verify the wheel's
  native dispatch + sha256 parity post-build.
- **scikit-build-core + CMake** build backend (Phase B2). Pure-
  Python fallback for Pyodide / WASM lives in `pyproject-pure.toml`
  (hatchling backend, swapped in for the `build-pure-wheel` CI
  job).
- **All `hashlib.sha256` callsites** in `srmech.amsc` route through
  `format.sha256_bytes()` → native dispatch when available;
  hashlib fallback otherwise.
- **JPL Power-of-Ten audit** complete (Phase B6). 10/10 rules
  satisfied modulo one documented Rule 9 callback deviation; ratchet
  enforced by `tests/test_jpl_audit.py` (6 mechanical tests, pinned
  exemption list) + `pedantic-build` CI job (3-cell:
  Linux gcc / macOS clang / Windows MSVC × `-DSRMECH_PEDANTIC=ON`
  → `-Werror` / `/WX`).
- **Description-match guard** between `pyproject.toml` and
  `pyproject-pure.toml` (rc9 post-mortem). Both descriptions
  carry the same 450-char Summary: "*Stored-Relationship
  Mechanism research package: home of the Attested Multi-Source
  Collector/Catalog (AMSC) framework — ...*".
- **AMSC dual-name framing** (rc2). Both *Collector* (at fetch
  time) and *Catalog* (at read time) work; same abbreviation;
  pick whichever fits the lifecycle stage.
- **Development Status classifier** bumped `3 - Alpha` → `4 - Beta`
  (rc9).

#### Cross-package readiness

ephemerides-spectral 0.26.1rc1 (the parallel-session ship) pins
`srmech>=0.1.1rc9` with a TestPyPI `PIP_EXTRA_INDEX_URL` override
to exercise the cibuildwheel matrix against the TestPyPI srmech
rcs. With v0.2.0 now on production PyPI, the next
ephemerides-spectral release will bump that floor to
`srmech>=0.2.0` and drop the TestPyPI override.

#### v0.1.0 status

Still on PyPI as the historical release. `pip install srmech`
without any version constraint now resolves to v0.2.0; users on
older Python paths can still pin `srmech==0.1.0` for the
pure-Python wheel.

#### History

See the rc-by-rc entries below for the full per-phase record:

- `0.2.0rc2` — AMSC "Collector/Catalog" dual-name wording
- `0.2.0rc1` — Phase B7 final TestPyPI gate (no-op version bump
  from rc9)
- `0.1.1rc9` — Metadata drift sweep ("Pure Python." → "Native C
  dispatch"; Dev Status 3-Alpha → 4-Beta; description-match guard)
- `0.1.1rc8` — Phase B6 JPL Power-of-Ten audit + ratchet
- `0.1.1rc7` — Phase B5 sha256 callsites routed through native
- `0.1.1rc6` — Phase B4 NDJSON streaming reader C port
- `0.1.1rc5` — Phase B3 SHA-256 C port + cibuildwheel matrix
- `0.1.1rc4` — Phase B2 scikit-build-core + pyproject-pure
- `0.1.1rc3` — Phase B1 C tree scaffolding
- `0.1.1rc1` / `rc2` — Earlier infrastructure cycles
- `0.1.0` — Initial AMSC-to-srmech refactor (pure-Python)

## [0.2.0rc2] - 2026-05-14

### Added — Task #201 Phase B7: AMSC dual-name wording ("Collector / Catalog")

Documents the dual reading of the **AMSC** abbreviation across
srmech's user-facing surface. **No code, no API, no ABI change**
— pure documentation polish discovered while reviewing the
0.2.0rc1 TestPyPI metadata.

#### The framing

**AMSC** abbreviates both:

- **Attested Multi-Source Collector** — at collection time
  (T1 fetch / T3 live query / re-bake lifecycle stages), the
  framework's adapter classes are *collecting* attested rows
  from upstream archives.
- **Attested Multi-Source Catalog** — after collection, the
  committed NDJSON SSOTs constitute a *catalog* of attested
  data that downstream packages register and query through the
  universal bridge.

Both names are correct; both abbreviate to AMSC; pick whichever
fits the lifecycle stage you're describing. One framework wearing
two hats.

#### Surfaces updated

- **`pyproject.toml` + `pyproject-pure.toml`** `[project].description`
  — "Attested Multi-Source Collector (AMSC)" →
  "Attested Multi-Source Collector/Catalog (AMSC)". 442 chars →
  450 chars (still under both the 480 soft cap and PyPI's 512
  hard cap).
- **`python/README.md`** — package-intro paragraph updated;
  new "Why 'Collector/Catalog'?" subsection explains the dual
  reading with the T1/T3-fetch vs read-time-query lifecycle
  framing.
- **`python/srmech/__init__.py`** docstring — package-level
  framing now leads with the dual name and gives a paragraph on
  the lifecycle-stage interpretation.
- **`python/srmech/amsc/__init__.py`** docstring — same dual-
  name framing at the AMSC subpackage level.
- **`docs/srmech/srmech_research_notebook.md` §0** — three-layer
  architecture's L1 paragraph gains a "Naming aside" note
  introducing both readings, with explicit lifecycle-stage
  cross-references (`list_attested_sources` etc.).
- **`docs/srmech/CLAUDE.md`** state snapshot bumped to reflect
  the rc2 ship.

#### Why TestPyPI rc rather than land-as-unreleased

Initial intent (per maintainer's "leave this as an unreleased
update" guidance) was to land the doc change on `main` without a
new rc; but per the project's TestPyPI-before-PyPI discipline,
any text that goes to production PyPI's Summary metadata should
have been visible on TestPyPI first. PyPI Summary drift (the
"Pure Python." bug at rc8 → rc9) was the specific failure mode
that motivated the description-match guard; landing the dual-name
wording without a TestPyPI round-trip would re-open the same
exposure. So we ship rc2 to TestPyPI and verify there, then v0.2.0
(no rc suffix) cuts to production PyPI carrying the rc2 text.

#### No code change

C ABI still **2**. Python public API surface unchanged. Wheel
content identical to rc1 modulo the description string +
docstrings. Pytest matrix unaffected (the
`test_native_version_and_abi` rc9-bump fix from rc1 keeps working).

## [0.2.0rc1] - 2026-05-13

### Task #201 Phase B7 — final TestPyPI rc before v0.2.0 production cut

No code changes from `0.1.1rc9`. This release exists to validate
the **v0.2.0** version string itself through one more TestPyPI
round-trip before the clean `srmech-v0.2.0` tag goes to
**production PyPI**. Discipline: TestPyPI before PyPI, always —
the rc-suffix auto-routing in `srmech-publish.yml` means a clean
non-rc tag IS the production gate; we want one last sanity
verification on the version string + metadata immediately before
the gate-passing tag.

#### Why a minor bump (0.1.1 → 0.2.0)

The rc3 → rc9 series turned srmech from a pure-Python AMSC
framework into a native-C-accelerated package with cibuildwheel
matrix + JPL Power-of-Ten audit + per-platform parity tests
covering 3 OS × 5 Python versions. That's a real capability
boundary, large enough that consumers of `srmech==0.1.0`
upgrading via `pip install -U srmech` are going on a substantive
ride. Minor bump signals that.

#### Cross-package readiness (parallel session shipped this)

While the srmech rc series was iterating, a parallel Claude
Code session verified srmech rc9 against the sister package
**ephemerides-spectral** (which depends on srmech as its AMSC
substrate per Task #197). The verification result lives at
[`docs/antikythera-maths/ephemerides-spectral/CHANGELOG.md`](../../antikythera-maths/ephemerides-spectral/python/CHANGELOG.md)
under `ephemerides-spectral 0.26.1rc1`. That rc shipped to
TestPyPI with `srmech>=0.1.1rc9` pinned + a
`PIP_EXTRA_INDEX_URL=https://test.pypi.org/simple/` test-env
override (Option B from the verification prompt), confirming
the cibuildwheel test matrix actually exercises against the
TestPyPI srmech rc rather than silently falling back to PyPI's
`srmech==0.1.0`. Cross-package integration confirmed green.

After srmech v0.2.0 ships to production PyPI, ephemerides-spectral
will bump its srmech floor `>=0.1.1rc9` → `>=0.2.0` and drop the
TestPyPI test-env override in its own follow-up release. That's
ephemerides-spectral's ship to plan, not srmech's.

#### Path forward

1. **This rc1** auto-ships to TestPyPI via the rc-suffix routing.
2. Maintainer verifies wheel install + native dispatch + sha256
   parity + ndjson parity end-to-end from a clean venv outside
   the repo tree.
3. If clean, maintainer bumps `0.2.0rc1` → `0.2.0` (drop the
   `rcN` suffix in all four SSOT files), merges that bump, and
   tags `srmech-v0.2.0`. That clean tag auto-routes to
   **production PyPI** via the workflow's environment-name claim.
4. After v0.2.0 lands on PyPI, ephemerides-spectral can bump
   its srmech floor; downstream consumers can upgrade via
   `pip install -U srmech`.

#### No ABI / API / behaviour change

C ABI version unchanged (still 2). Python public surface
unchanged. Wheel content identical to rc9 modulo the version
string. The `SRMECH_VERSION` macro updates in lockstep
(`0.1.1rc9` → `0.2.0rc1`) and the Python `_native.py` reads it
back through `srmech_version()` at load time.

## [0.1.1rc9] - 2026-05-13

### Fixed — PyPI metadata drift after Phase B3 (native code) landed

User-spotted drift on the TestPyPI project page: the Summary still
read "...Pure Python." even though Phase B3 (rc5) shipped native C
dispatch and Phase B4 (rc6) added the second native symbol. Both
`pyproject.toml` and `pyproject-pure.toml` had the stale claim
verbatim because the description text was copy-pasted between them
without revisiting the trailing sentence after each phase.

#### Fixed

- **`pyproject.toml` + `pyproject-pure.toml` `[project].description`**
  — replaced "Pure Python." with "Native C dispatch (SHA-256 +
  NDJSON line reader) with pure-Python fallback for Pyodide / WASM."
  Both files now carry identical 442-char descriptions (well under
  the 480-char soft cap; well under PyPI's 512-char hard limit).
- **`README.md` Status line** — refreshed to reflect the rc3→rc8
  arc and the impending v0.2.0 cut. Adds a one-liner clarifying
  the native-C + pure-Python-fallback architecture in the package
  intro paragraph.
- **`Development Status` classifier** — bumped from
  `3 - Alpha` → `4 - Beta` on both pyproject files. After 6 rc
  iterations including cibuildwheel matrix, JPL Power-of-Ten audit,
  Python/C parity tests, and pedantic-build CI on three platforms,
  "Beta" is the honest label. Same status ephemerides-spectral
  carries.

#### Added — description-match guard (defensive ratchet)

The publish workflow (`srmech-publish.yml`) and CI workflow
(`srmech-ci.yml`) already enforce **version-match** between
`pyproject.toml` and `pyproject-pure.toml`. The same guard pattern
now also asserts **description-match**: any drift between the two
descriptions fails CI with a clear error message including both
char counts. This catches future copy-paste drift before it can
reach a TestPyPI / PyPI upload.

PyPI's Summary metadata is per-project-version (not per-wheel), so
both wheels uploaded under the same version must carry the same
Summary text. The match guard formalises that invariant.

#### Audit scope

Reviewed every user-facing PyPI metadata surface for similar drift:

- ✅ `description` — fixed (both files).
- ✅ `Development Status` classifier — bumped.
- ✅ README Status line — refreshed.
- ✅ `keywords` — accurate (stored-relationship, mechanism, attested,
  provenance, ndjson, ground-proof, research). No change.
- ✅ `Topic :: Scientific/Engineering` classifier — accurate.
- ✅ `Programming Language ::` classifiers — match `requires-python`.
- ✅ `[project.urls]` — Homepage, Repository, Issues, Changelog,
  Notebook. Stable, no drift.
- ✅ Docstrings in `_native.py` / `format.py` / `c/README.md` that
  mention "pure-Python" — all referring to the fallback path
  correctly; no drift.

#### No ABI change

C surface unchanged from rc8. `SRMECH_ABI_VERSION` stays at 2.

## [0.1.1rc8] - 2026-05-13

### Added — Task #201 Phase B6: JPL Power-of-Ten audit

Formal audit of srmech's native C library against
[Holzmann's JPL Power-of-Ten rules](https://web.eecs.umich.edu/~imarkov/10rules.pdf).
Mirrors the pattern ephemerides-spectral applied via Tasks
#105–#110. **All ten rules satisfied** for srmech's C surface,
modulo one documented Rule 9 deviation (callback-based iterator).

#### Audit deliverables (`docs/srmech/c/JPL_AUDIT.md`)

- **Rule-by-rule compliance review** across all 3 C source files
  (`srmech_meta.c`, `srmech_sha256.c`, `srmech_ndjson.c`) + the
  public header `srmech.h`. ~500 LOC total.
- **Per-function line + assertion counts** with explicit exemption
  policy for trivial accessors (`srmech_version`,
  `srmech_abi_version`) and `static inline` arithmetic primitives
  (sha256 bit-rotation helpers).
- **Rule 9 deviation rationale** documented: the `srmech_ndjson_iter`
  callback is the smallest API surface satisfying Rules 3 + 4 simultaneously.

#### Code fix shipped in this audit pass

- **`srmech_ndjson_iter`** at rc6 was **76 lines** (Rule 4 violation:
  > 60 lines). The chunk-byte-loop body extracted into a new
  `static srmech_ndjson_process_chunk` helper along its natural
  state-update seam. Post-refactor: 51-line `iter` + 43-line
  `process_chunk`. Byte semantics identical; 18 ndjson parity
  tests re-ran clean.

#### Tests + CI ratchet

- **`tests/test_jpl_audit.py`** *(NEW)* — 6 mechanically-detectable
  ratchet tests:
  - Rule 1: no `goto` / `setjmp` / `longjmp` anywhere.
  - Rule 3: no `malloc` / `calloc` / `realloc` / `free` / `alloca`.
  - Rule 4: every function ≤ 60 lines (line-count regex + brace-
    depth scanner).
  - Rule 5: every non-exempt function has ≥ 2 assertions.
    Exempt list pinned (8 entries: 2 trivial accessors, 6 inline
    helpers); adding to the exempt list requires documenting
    rationale in JPL_AUDIT.md AND updating the test.
  - Rule 8: no multi-line macros / token-paste / `__VA_ARGS__`.
  - Audit doc present-and-mentions-all-rules sanity check.
- **`.github/workflows/srmech-ci.yml`** gains a **`pedantic-build`
  job** (3-cell matrix: Linux gcc / macOS clang / Windows MSVC)
  that runs `cmake -DSRMECH_PEDANTIC=ON` → builds with `-Werror`
  (POSIX) or `/WX` (MSVC). Any new warning fails CI. Rule 10
  toolchain-side enforcement.
- All 100 existing tests still pass; pytest collects 106 tests +
  the JPL ratchet's 6 = 112 total Python tests.

#### Verification (local)

- ``gcc -std=c11 -Wall -Wextra -Wpedantic -Werror -O2`` builds all
  3 C files clean.
- `pytest tests/test_jpl_audit.py` → 6/6 pass.
- Full pytest suite (rc8 wheel install) → 106 passed + 1 skipped
  (1 native-dispatch skip when run from source tree).

#### Phase plan progress

| B1 | C tree scaffolding (rc3)                          | ✅ |
| B2 | scikit-build-core + pyproject-pure (rc4)          | ✅ |
| B3 | SHA-256 + cibuildwheel matrix (rc5)               | ✅ |
| B4 | NDJSON streaming reader (rc6)                     | ✅ |
| B5 | Route remaining sha256 callsites (rc7)            | ✅ |
| B6 | JPL Power-of-Ten audit (rc8)                      | this ship |
| B7 | v0.2.0rc1 final TestPyPI verify → v0.2.0 to PyPI  | next |

## [0.1.1rc7] - 2026-05-13

### Changed — Task #201 Phase B5: route remaining sha256 callsites through native dispatch

Phase B5's nominal title was "TOML canonical-serialization C port".
The shipped scope is narrower and better-fit: the actual hot work
(SHA-256 over canonicalised bytes) already has a native C path
from Phase B3. **B5 routes the four remaining ``hashlib.sha256``
callsites in srmech through ``sha256_bytes``** so every per-row
attestation hash benefits from the native dispatch.

Vendoring a TOML parser in C — the original phase plan's
implication — was rejected. CPython's ``tomllib`` + ``json.dumps``
canonicalisation is small, fast, and well-tested; replicating it
in C would 3× srmech's native-code surface area for no measurable
gain on the inputs srmech actually processes.

#### Wired callsites

- **`descriptor.descriptor_hash`** — the load-bearing one. Used by
  every adapter's ``attest()`` step to compute
  ``collector_descriptor_hash`` per row.
- **`catalog._file_sha256`** — hashes overlay NDJSON files for T2
  user-runtime-kernel attestation. Small files (< few MB), so
  slurp-and-hash via ``sha256_bytes`` is fine; streaming hashlib
  (which we'd need for huge files) would require a separate
  C-side multi-update API not yet ported.
- **`catalog._kernel_cache_hash`** — cache-key hash over the
  registered T2 overlay summary.
- **`adapters._base.parser_rule_hash`** — per-row attestation field
  documenting the parse-section rules.

#### What stays in Python

- TOML parsing (``tomllib.loads``) — stdlib, already C-accelerated.
- Canonical JSON serialisation (``json.dumps(sort_keys=True, ...)``) —
  stdlib, already C-accelerated.
- Streaming hashlib for the (currently unused) very-large-file case.

#### Tests

- **`tests/test_native_descriptor_hash.py`** *(NEW)* — 7 parity
  tests:
  - 3 descriptor-shape fixtures (minimal, comments + odd-spacing,
    deeply-nested keys) comparing native-routed ``descriptor_hash``
    to a pure-Python hashlib reference computation.
  - ``catalog._file_sha256`` parity vs streaming hashlib.
  - ``adapters._base.parser_rule_hash`` parity vs hashlib.
  - Defensive ratchet asserting all four wired callsites resolve to
    the same native path (catches accidental re-introduction of
    direct ``hashlib.sha256`` calls).
- Full pytest suite (100 tests + 1 skip) all green under native
  wheel install on Windows MSVC + Python 3.14.

#### No ABI change

C surface area unchanged from rc6. SRMECH_ABI_VERSION stays at 2.

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
