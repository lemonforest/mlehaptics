# `docs/srmech/` — Claude Code session brief

You have been opened into the **srmech** subdirectory of the
`mlehaptics` monorepo. The repo's top-level `CLAUDE.md` is about an
EMDR bilateral-stimulation firmware project (ESP32-C6, Phase 7
pattern playback) — **that's not what you're working on here**.

This subtree is part of a **spectral-research portfolio** of
several Python research packages sharing one mathematical-
provenance discipline. Read this whole file before doing anything
beyond a single-file read.

---

## What srmech IS

**srmech** is short for **Stored-Relationship Mechanism**. It is:

- A Python research package, published as **`srmech`** on PyPI
  (`v0.1.0` shipped, rc-series at `0.1.1rc9` on TestPyPI; about
  to cut **`v0.2.0`** to production PyPI).
- The home of the **Attested Multi-Source Collector (AMSC)
  framework** — every ground-proof datum carries a mandatory
  attestation block (`source_doi`, `source_url`, `license`,
  `retrieved_at`, `response_sha256`, `parser_version`,
  `parser_rule_hash`, `collector_descriptor_path`,
  `collector_descriptor_hash`). This is the on-disk crystallisation
  of the **Mathematical Provenance Method** (MPM).
- A **native-C-accelerated** pure-Python package (Task #201
  build-out: rc3 → rc9). Native dispatch covers SHA-256
  attestation hashes and NDJSON streaming line tokenisation;
  pure-Python fallback for Pyodide / WASM environments.
- The dependency surface that downstream spectral-research
  packages (`ephemerides-spectral` today; more later) register
  their catalog SSOTs with via `srmech.amsc.catalog.register_attested_root()`.

The package directory layout:

```
docs/srmech/
├── CLAUDE.md                          ← you are here
├── CMakeLists.txt                     ← top-level CMake driver
├── srmech_research_notebook.md        ← canonical notebook
├── notes/                             ← research scratchpads, NDJSON outputs
├── hoodoos/                           ← protein-fold PDB fixtures used by some spikes
├── c/                                 ← native C library
│   ├── include/srmech.h               ← public API: srmech_sha256_hex,
│   │                                    srmech_ndjson_iter, srmech_version,
│   │                                    srmech_abi_version
│   ├── src/srmech_sha256.c            ← FIPS 180-4 SHA-256, JPL-clean
│   ├── src/srmech_ndjson.c            ← streaming NDJSON reader, JPL-clean
│   ├── src/srmech_meta.c              ← version + ABI accessors
│   ├── test/                          ← C-side smoke tests
│   ├── Makefile                       ← local build flow
│   ├── README.md
│   └── JPL_AUDIT.md                   ← Power-of-Ten rule-by-rule audit
└── python/
    ├── pyproject.toml                 ← scikit-build-core (primary)
    ├── pyproject-pure.toml            ← hatchling (Pyodide fallback)
    ├── README.md                      ← PyPI long-description
    ├── CHANGELOG.md                   ← per-rc changelog
    ├── srmech/
    │   ├── __init__.py
    │   ├── version.py                 ← SSOT for __version__
    │   ├── amsc/                      ← the AMSC framework
    │   │   ├── format.py              ← MPRRecord, read_ndjson, sha256_bytes
    │   │   ├── descriptor.py          ← TOML descriptor loader, descriptor_hash
    │   │   ├── catalog.py             ← register_attested_root, bridge surfaces
    │   │   ├── _native.py             ← ctypes shim; HAS_NATIVE / sha256_hex_c / ndjson_lines_c
    │   │   ├── gap_suggester.py
    │   │   └── adapters/              ← html / json / csv / netcdf / geotiff / literature_curated
    │   └── _native/                   ← (wheel install only) libsrmech.so/.dll/.dylib
    └── tests/                         ← pytest suite
```

---

## What srmech IS NOT

**srmech is not a CAD-grade fabrication tool.** It produces
**provenance metadata** about scientific datasets — DOI, retrieval
timestamp, response SHA-256, parser version, descriptor hash. It
does not model physical geometry, mesh contact, axle wobble,
fabrication tolerances, or any of that machinery.

The sister package `docs/antikythera-maths/CLAUDE.md` documents an
explicit **CAD-grade scope ban** for its own subtree (modelling at
the *algebra / eigenbasis* level, projecting to spatial motion,
NOT modelling at the CAD level). **The same ban applies in
srmech**: if a request reads as "vendor a TOML parser in C" or
"reconstruct the surface from raw bytes" or "compile-time-decode
the JSON" — push back. srmech keeps **parsing in Python**
(`tomllib`, `json`, `MPRRecord.from_json_line`) and uses C **only
for the byte-pushing hot paths** (SHA-256, file IO, line
tokenisation). Don't expand the native surface area beyond that.

**srmech is not the EMDR firmware.** The repo root `CLAUDE.md`
describes the EMDR bilateral-stimulation device (`src/`, `test/`,
`platformio.ini`, ESP32-C6, motor PWM). That's a separate project
in the same monorepo. **Do not edit files outside this subtree or
its sister `docs/*-maths/` subtrees** unless the user explicitly
asks.

---

## Sister spectral notebooks (the family srmech belongs to)

srmech is one node in a portfolio of spectral-research Python
packages and notebooks. Each notebook applies the same MPM
discipline to a different domain object:

| Path | Notebook title | What it studies |
|------|----------------|-----------------|
| `../srmech/srmech_research_notebook.md` | **Stored-Relationship Mechanism** | The unifying framework — relationships stored in cyclic-group / spectral representations, projected back to observable behaviour. *Canonical to this directory.* |
| `../antikythera-maths/antikythera_spectral_research_notebook.md` | The Antikythera Mechanism as a Resonant HDC Object | Bronze gear-DAG, cyclic-group algebra, Almagest / Freeth parameter sets |
| `../antikythera-maths/ephemerides_spectral_research_notebook.md` | The Ephemerides Mechanism: High-Precision Resonant HDC Instrument | Sol star system — 52-body roster, geodetic / magnetic / fluid / dynamical catalogs, JPL DE441 anchor. **srmech depends on this one (it consumes AMSC).** |
| `../antikythera-maths/mfo_spectral_research_notebook.md` | MFO Spectral Research Notebook | **Metric Field Ontology** — substrate-vs-excitation framing of the spectral metric field. User's foundational ontology layer (sister to all the others). |
| `../antikythera-maths/doom_spectral_research_notebook.md` | DOOM as a Spectral Lattice System | Map encoding, level topology, gameplay-system spectral analysis |
| `../chess-maths/chess_spectral_research_notebook.md` | Chess as a Spectral Lattice Fermion System | Piece-graph spectra, D_4 / B_4 reps, irrep multiplicities — the original spectral-mechanic spike |
| `../chess-maths/chess_spectral_4d_notebook.md` | 4D Chess Spectral — v1 Validation Notebook | Higher-dimensional chess extension |
| `../logo-maths/logo_research_notebook.md` | LOGO HDC — Research Notebook | LOGO turtle graphics → cyclic-group encoder |
| `../othello-maths/othello_spectral_research_notebook.md` | Othello as a Dynamic Spectral Lattice System | Reversi piece-flip dynamics |

**Discipline shared across all of these**: algebra / eigenbasis /
cyclic-group / spectral side. **Not** CAD / fabrication /
mechanical-engineering side. See
`docs/antikythera-maths/CLAUDE.md` for the canonical scope
statement; it applies to all sister notebooks, srmech included.

---

## The Mathematical Provenance Method (MPM) — srmech's reason for being

Every ground-proof datum srmech ships carries a mandatory
attestation block. The on-disk crystallisation is the
**Mathematical Provenance Record v1** format (`MPR v1`),
implemented in `srmech.amsc.format`:

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
    "parser_version": "srmech 0.1.1rcN",
    "parser_rule_hash": "<64 hex chars>",
    "collector_descriptor_path": "...",
    "collector_descriptor_hash": "<64 hex chars>"
  },
  "rendering": { "name": "...", "purpose": "...", "cite_as": "..." }
}
```

Why this matters: the discipline catches the most common LLM-side
error mode — citation hallucination. A citation without
attestation is not real; an attestation that can't be re-verified
is broken. The whole AMSC framework is the project's defence
against citation drift. **Be paranoid about citations.** When a
user asks you to add a paper reference, prefer to extract the
actual PDF and verify authors + title + arXiv ID over trusting
training-data attribution.

---

## Build / release stack — read before touching anything publish-adjacent

### Two-pyproject pattern

- **`pyproject.toml`** — scikit-build-core backend, drives CMake,
  produces **platform wheels** (`cp3XX-cp3XX-{linux,macosx,win}_*`)
  with `srmech/_native/lib*.{so,dll,dylib}` inside.
- **`pyproject-pure.toml`** — hatchling backend, produces **one
  `py3-none-any` wheel** for Pyodide / WASM environments where
  native binaries can't run. Swapped in via `mv` over
  `pyproject.toml` in the `build-pure-wheel` CI job; restored
  afterward.

Both files **MUST** carry identical `version` and `description`
fields. The publish workflow's "Verify pyproject-pure.toml version
+ description match main" step fails CI on any drift. That guard
exists because rc3-rc8 shipped with stale `"Pure Python."` in
both descriptions; the user spotted it on the TestPyPI project
page (rc9 fix). Read [CHANGELOG.md §0.1.1rc9](python/CHANGELOG.md)
for the post-mortem.

### Versioning + tag-push routing

- Version SSOT lives in **three places** that must agree:
  `python/pyproject.toml`, `python/pyproject-pure.toml`,
  `python/srmech/version.py`. **Plus** `c/include/srmech.h`
  (`SRMECH_VERSION_PRE` / `SRMECH_VERSION`).
- **rc-suffix auto-routing** in `.github/workflows/srmech-publish.yml`:
  - Tag `srmech-vX.Y.ZrcN` (lowercase `rc`, no separator) →
    **TestPyPI** auto-publish.
  - Tag `srmech-vX.Y.Z` (no `rc` suffix) → **PyPI** auto-publish.
    Tagging without `rc` IS the human-in-loop production gate.
  - The tag-version regex: `r"srmech-v(\d+\.\d+\.\d+(?:rc\d+)?)"`.
- **User discipline (mandatory)**: TestPyPI rc-verification BEFORE
  a clean tag goes to production PyPI. Every release between
  v0.1.0 and v0.2.0 has shipped this way (rc3 → rc9 on TestPyPI;
  v0.2.0 will be preceded by at least `0.2.0rc1` on TestPyPI).

### Tag flow for a new rc

```bash
# 1. Make changes on a feature branch
git checkout -b task-XXX-or-feat-name
# 2. Bump version in 4 SSOT files:
#    python/pyproject.toml         version = "0.1.1rcN"
#    python/pyproject-pure.toml    version = "0.1.1rcN"
#    python/srmech/version.py      __version__ = "0.1.1rcN"
#    c/include/srmech.h            SRMECH_VERSION_PRE + SRMECH_VERSION
# 3. Add CHANGELOG.md entry under [0.1.1rcN] header
# 4. PR → review → MERGE (NOT squash, see "Never squash" below)
git checkout main && git pull
# 5. Tag at the merge commit
git tag srmech-v0.1.1rcN HEAD
git push origin srmech-v0.1.1rcN
# 6. Watch the publish workflow run; verify TestPyPI install
#    in a clean venv (cd outside the repo first; namespace-package
#    shadowing will silently load the source-tree _native.py with
#    no .dll/.so attached and HAS_NATIVE=False).
```

### Native-dispatch architecture

The Python `srmech.amsc._native` module:
- Searches three locations for the shared library:
  1. Each entry in `srmech.__path__` (regular wheel install)
  2. Relative to `_native.py`'s own file (defensive)
  3. `importlib.metadata.files("srmech")` manifest (editable installs)
- Verifies `srmech_abi_version()` matches `EXPECTED_ABI_VERSION`
  at load time; mismatch → `HAS_NATIVE = False`, `LOAD_ERROR`
  populated, pure-Python fallback runs.
- Exposes `sha256_hex_c(bytes) -> str` and
  `ndjson_lines_c(path) -> list[(lineno, bytes)]`.

The dispatching wrappers live in `srmech.amsc.format`:
- `sha256_bytes(data)` → uses native if `HAS_NATIVE`, else hashlib.
- `read_ndjson(path)` → uses native if `HAS_NATIVE`, else stdlib.

Other hot callsites (`catalog._file_sha256`,
`catalog._kernel_cache_hash`, `adapters._base.parser_rule_hash`)
route through `sha256_bytes` so they pick up the native dispatch
transparently. **Do not introduce new `hashlib.sha256(...)` direct
calls** — go through `sha256_bytes` (Phase B5 discipline).

### ABI compatibility

C ABI version is currently **2** (`SRMECH_ABI_VERSION = 2` in
`c/include/srmech.h`; `EXPECTED_ABI_VERSION = 2` in
`python/srmech/amsc/_native.py`). **Bump in lockstep** whenever
the wire format of any existing exported function changes. Adding
a new symbol does NOT bump ABI (the Python shim just doesn't bind
unknown symbols). v1 was Phase B3 (sha256 only); v2 added the
`lineno` param to the NDJSON callback typedef.

### JPL Power-of-Ten audit

The C library passes all 10 Holzmann Power-of-Ten rules
(see [c/JPL_AUDIT.md](c/JPL_AUDIT.md)). Enforcement:

1. **`tests/test_jpl_audit.py`** — pytest ratchet, mechanically
   detects Rules 1 (no goto), 3 (no malloc), 4 (≤60-line
   functions), 5 (≥2 asserts per non-exempt function), 8 (no
   multi-line macros). **Violations can only go DOWN**, never up.
2. **`pedantic-build` CI job** (3-cell: Linux gcc / macOS clang /
   Windows MSVC) — `cmake -DSRMECH_PEDANTIC=ON` enables
   `-Werror` (POSIX) / `/WX` (MSVC). Any new warning fails CI.
   Rule 10 toolchain-side enforcement.
3. **Rule 5 exempt list** in `test_jpl_audit.py` has 8 entries
   (2 trivial accessors + 6 sha256 inline arithmetic helpers).
   Adding to it requires documenting rationale in JPL_AUDIT.md
   AND updating the test. Don't expand silently.

---

## Critical project memories (load-bearing across sessions)

These come from the user's persistent memory directory at the
repo root. They are NOT auto-loaded into this session because the
session's cwd is `docs/srmech/` not the repo root. **Internalise
them anyway** — they're load-bearing for any work in this subtree:

- **Never squash-merge PRs.** Project history depends on per-step
  commits being preserved. Use `gh pr merge --merge` (preferred)
  or `--rebase`; never `--squash`.
- **TestPyPI before PyPI, always.** Every release between now and
  v0.2.0 ships as `vX.Y.ZrcN` to TestPyPI; only clean
  (non-rc) tags route to production PyPI.
- **No MVP framing.** Don't scope ships as "minimum-viable" or
  "quick-tier subsets"; commit to full-coverage per ship version.
- **PDF-extraction citation discipline.** When citing a paper,
  extract the actual PDF and verify authors + title + arXiv ID;
  don't trust prior attributions. Several catches in the
  May 2026 spike series prove this is load-bearing.
- **NDJSON over bloated JSON for results.** New results-style
  outputs should be NDJSON (one record per line), not indented
  JSON. TOML accepted for descriptor-shaped data. (Existing
  bloated JSONs in tree are what they are; the discipline
  applies to NEW outputs.)
- **No lineage claims about external work.** Don't ship "natural
  extension of X" claims about prior researchers' work without
  explicit user direction. Cite specific results technically.
  (The user has explicitly authorised "natural extension" framing
  for *their own* intellectual arc — distinct from academic-
  lineage assertions about others.)
- **WSL smoke before AMSC pushes.** For AMSC-touching PRs, run
  `wsl bash scripts/smoke_local.sh` before push if available;
  Windows-local pytest can't catch libm last-bit divergence
  between platforms. Less critical for srmech (data-pipeline, not
  math-heavy) but watch for it on any C-touching PR.
- **Fiber as spatially-absent encoding.** The user's
  intellectual stance — a fiber over a manifold encodes
  algebraic content that is spatially absent until projected.
  Worked example: a gear's tooth count is `ℤ/n` algebra; the
  spatial dynamics only appear under external rotation. This
  framing applies across all the spectral notebooks (chess
  pieces, gear ratios, Antikythera dials, ephemerides bodies)
  and is the conceptual unifier the project hangs on.
- **Hyper as 3D-spatial-interface.** The user's two-level
  ontology refinement (May 2026): "hyper" denotes 3D-spatial-
  interface, NOT hyperdimensional-algebraic constructions.
  Spherical compression scopes to 3D-spatial-physical phenomena.
  Formalised in MFO §VII.1.1.
- **Trauma-informed defensive scope.** Security/defense-adjacent
  ships are defensive preparedness, NOT offence. Ship physics +
  textbook refs; never targeting / capability-assessment.

---

## If your task is "verify ephemerides-spectral on TestPyPI"

That's the user's stated reason for opening this session. The
ephemerides-spectral package lives at
`../antikythera-maths/ephemerides-spectral/` (sister subtree under
the same monorepo). It depends on `srmech` as a hard runtime
dependency.

Plan:

1. **Check what's on TestPyPI now.** The release index lives at
   <https://test.pypi.org/project/ephemerides-spectral/>. Find
   the most-recent rc version (the publish workflow is
   `.github/workflows/ephemerides-spectral-publish.yml` at the
   repo root).
2. **Create a fresh venv** outside the repo tree (e.g. under
   `/tmp/verify_ephemerides_spectral/`). Source-tree shadowing
   will otherwise import the editable namespace package and
   `HAS_NATIVE` will spuriously read False.
3. **Install via TestPyPI** with PyPI as the fallback index for
   transitive deps:
   ```bash
   pip install --no-cache-dir \
     --index-url https://test.pypi.org/simple/ \
     --extra-index-url https://pypi.org/simple/ \
     "ephemerides-spectral==<rc-version>"
   ```
   Note: this will pull `srmech>=0.1.0` from TestPyPI too
   (or PyPI if floor is satisfied there). The latest srmech rc
   on TestPyPI is `0.1.1rc9` (see this session's PR #394).
4. **Verify imports, native dispatch, key API surfaces.** Pattern:
   ```python
   import ephemerides_spectral, srmech
   print(ephemerides_spectral.__version__, srmech.__version__)
   # ephemerides-spectral has bridge.* surfaces; the AMSC ones
   # route through srmech.amsc.* after the Task #197 refactor.
   from srmech.amsc import _native
   print("srmech HAS_NATIVE:", _native.HAS_NATIVE, "ABI:", _native.NATIVE_ABI_VERSION)
   from ephemerides_spectral import bridge
   print(bridge.list_attested_sources()["n_sources"])
   ```
5. **Run the ephemerides-spectral tests** if installable that way
   (its publish workflow runs them as part of cibuildwheel
   per-cell — but a post-install end-to-end re-run is a real
   verification).
6. **Report** to the user: what version is on TestPyPI, did it
   install cleanly, are native dispatch + cross-package
   integration working, what's the diff vs. last good release.

The user's broader intent: before they cut **srmech v0.2.0** to
**production PyPI**, they want a parallel session validating that
the latest **ephemerides-spectral on TestPyPI** still works
correctly against the recent srmech rc series. If it does, the
v0.2.0 cut is safe. If it doesn't, debug the breakage before any
production publish.

---

## What NOT to do in this session

- Don't edit anything outside `docs/srmech/`, `docs/antikythera-maths/`,
  `docs/chess-maths/`, `docs/logo-maths/`, `docs/othello-maths/`, or
  the relevant root-level workflow files
  (`.github/workflows/srmech-*.yml`, `.github/workflows/ephemerides-spectral-*.yml`).
  In particular: **don't touch `src/`, `test/`, `platformio.ini`,
  `sdkconfig.*`** — those are the EMDR firmware project at the
  repo root.
- Don't introduce CAD-grade fabrication geometry, mesh-contact,
  axle-precession, lubricant, or related machinery. srmech models
  *data provenance*, not physical artefacts.
- Don't vendor a TOML parser or JSON parser in C. Phase B5
  explicitly rejected this; canonicalisation stays in Python.
- Don't introduce a new `hashlib.sha256(...)` direct call;
  route through `format.sha256_bytes(...)`.
- Don't add a new function > 60 lines or remove an assertion
  from an existing non-exempt function — the JPL ratchet fails.
- Don't squash-merge any PR. `gh pr merge --merge` only.
- Don't push to **production PyPI** without a TestPyPI rc
  verification round first. The auto-routing in the publish
  workflow makes a clean (non-rc) tag the production gate;
  treat it as a deliberate human-only action.
- Don't make new citations without verifying the underlying PDF
  (authors + title + arXiv ID).
- Don't write a long planning doc unless the user explicitly
  asks. Work from conversation context.

---

## Quick orientation commands

```bash
# Where am I?
pwd                                            # docs/srmech
ls                                             # CMakeLists.txt c/ notes/ python/ srmech_research_notebook.md ...

# What's the current rc on TestPyPI?
pip index versions srmech \
    --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/

# What's the current rc on TestPyPI for ephemerides-spectral?
pip index versions ephemerides-spectral \
    --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/

# Latest commits relevant to srmech
git log --oneline -20 -- 'docs/srmech/' '.github/workflows/srmech-*.yml'

# Latest CHANGELOG entry
head -100 python/CHANGELOG.md
```

---

## Where the parent-session memory + state lives

For deeper context the user might reference in conversation:

- **User's persistent memory** (auto-loaded only at repo root,
  not at this cwd):
  `C:\Users\sckir\.claude\projects\D--GitHub-mlehaptics\memory\MEMORY.md`
  and the per-topic `.md` files alongside it.
- **Repo-root CLAUDE.md** — describes the EMDR firmware
  project. Ignore unless the user explicitly asks about it.
- **Sister scope-doc** — `docs/antikythera-maths/CLAUDE.md`
  states the algebra/eigenbasis-only discipline for that
  subtree. The same discipline applies here.
- **srmech research notebook** — `srmech_research_notebook.md`
  (this directory) is the canonical statement of the
  Stored-Relationship Mechanism concept.

If you need to know what was true *as of this session's open*
without the parent's persistent memory:

- `srmech` is at **`0.2.0rc1` on TestPyPI** (Phase B7 final rc
  before the production cut), with `v0.1.0` on production PyPI.
  Earlier rc series: `0.1.1rc3` → `0.1.1rc9` on TestPyPI.
- Task #201 phases B1–B6 + metadata-drift rc9 fix all shipped.
  See `python/CHANGELOG.md` for the per-rc record.
- **Phase B7 status**: 0.2.0rc1 published to TestPyPI; cross-
  package verification against ephemerides-spectral 0.26.1rc1
  confirmed green. The final clean tag `srmech-v0.2.0` →
  production PyPI is gated on one more end-to-end install check
  from a clean venv outside the repo tree.
- The C library is at ABI v2 with two native symbols
  (`srmech_sha256_hex`, `srmech_ndjson_iter`) plus version /
  ABI accessors.
- **ephemerides-spectral 0.26.1rc1** (sibling subtree) pins
  `srmech>=0.1.1rc9` for the parallel-session verification round.
  After srmech v0.2.0 lands on production PyPI, ephemerides-
  spectral will bump that floor to `>=0.2.0` in its own follow-up
  release.
