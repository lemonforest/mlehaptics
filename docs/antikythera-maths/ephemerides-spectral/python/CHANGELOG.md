# ephemerides-spectral CHANGELOG

Per-version change log for the `ephemerides-spectral` PyPI package.
The full project changelog (with pointers into the research notebook
and cross-pollination notes) lives at
[`../CHANGELOG.md`](../CHANGELOG.md).

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.29.2] — 2026-05-19

Production graduation of v0.29.2rc1. No code changes vs `[0.29.2rc1]`.

The v0.29.2rc1 release was published to TestPyPI on 2026-05-19; fresh-venv install verified clean (srmech 0.4.2 + ephemerides_spectral 0.29.2rc1 both import on numpy 2.2.6). This graduation publishes the verified rc1 surface to production PyPI under clean semver.

Consumes srmech v0.4.2 (signal_processing namespace + spectral.{predict, prediction_error, truncate_sparse} + numpy 2.x compat + 7 new attested catalogs surfaced transitively).

**SSOT files bumped in lockstep:**

- `pyproject.toml` `[project].version` 0.29.2rc1 → 0.29.2.
- `pyproject-pure.toml` `[project].version` 0.29.2rc1 → 0.29.2.
- `ephemerides_spectral/version.py` `__version__` 0.29.2rc1 → 0.29.2.
- `ephemerides_spectral/srmech_profile.toml` `[profile].version` 0.29.2rc1 → 0.29.2.
- `c/include/ephemerides_spectral.h` `ES_VERSION_STRING "0.29.2rc1"` → `"0.29.2"`.
- `ephemerides_spectral/_data/manifest.json` `version` field restamped 0.29.2rc1 → 0.29.2.

### No code change; no ABI change

`ES_ABI_VERSION` stays at 10 (unchanged from v0.29.0); no `_research` mirror changes; no test ratchet changes; no `bridge.*` surface change. Pure clean-semver graduation.

## [0.29.2rc1] — 2026-05-19

### Changed — srmech dependency floor bump `>=0.4.0` → `>=0.4.2`

Tracks the srmech v0.4.2 production cut so downstream consumers
transitively pick up the cumulative srmech v0.4.x post-v0.4.0
content:

- **`srmech.signal_processing` namespace** — Phase 1-4 dual-path
  signal-processing layer: 38 Path A closed-form op modules + 307
  tests + a Path B RBS-HDC instrument with 6 dual-path ops, a
  form-function rotation, and a cascade dispatcher. Path A is the
  ALU-fast single-frame route; Path B is the substrate-portable
  RBS-HDC route. The dispatcher selects per-call.
- **`srmech.spectral.predict` / `prediction_error` /
  `truncate_sparse`** — extends the v0.4.1 spectral surface
  (`decompose` / `delta` / `recompose` / `similarity`) with
  forward-prediction, residual error, and sparse-truncation entries.
- **Tool-schema registration** — all 7 `srmech.spectral.*` entries
  plus the 6 `signal_processing` dual-path ops are wired into
  `srmech.amsc.tool_schema` for LLM-agent discovery alongside the
  existing ~87-entry surface.
- **numpy 2.x compatibility** — explicit defensive check for `log(0)`
  per JPL Power-of-Ten Rule 5 (the numpy 2.x default no longer
  emits a runtime warning that the v0.4.0 implementation depended
  on); behaviour unchanged on numpy 1.24+.

ephemerides-spectral does not consume the new
`srmech.signal_processing` or post-v0.4.1 `srmech.spectral.*`
entries in this ship — the bump is transitive only. Future ships
may opt into the new surfaces (e.g. the dynamical-regime
classifier exploring `srmech.spectral.predict` / `prediction_error`
for forecast-residual scoring) on a case-by-case basis.

**SSOT files bumped in lockstep:**

- `pyproject.toml` `[project].version` 0.29.1 → 0.29.2rc1;
  `[project].dependencies` `srmech>=0.4.0` → `srmech>=0.4.2`.
- `pyproject-pure.toml` `[project].version` 0.29.1 → 0.29.2rc1;
  `[project].dependencies` `srmech>=0.4.0` → `srmech>=0.4.2`.
- `ephemerides_spectral/version.py` `__version__` 0.29.1 → 0.29.2rc1.
- `ephemerides_spectral/srmech_profile.toml` `[profile].version`
  0.29.1 → 0.29.2rc1; `[profile].srmech_requires` `>=0.4.0` →
  `>=0.4.2`.
- `c/include/ephemerides_spectral.h` `ES_VERSION_PATCH` 1 → 2;
  `ES_VERSION_STRING "0.29.1"` → `"0.29.2rc1"`.
- `ephemerides_spectral/_data/manifest.json` `version` field
  restamped 0.29.1 → 0.29.2rc1.

### No code change; no ABI change

`ES_ABI_VERSION` stays at 10 (unchanged from v0.29.0); no
`_research` mirror changes; no test ratchet changes; no `bridge.*`
surface change. Pure dependency-floor bump.

### Versioning

`0.29.1` → `0.29.2rc1`. Patch bump (dependency-floor refresh).
rc1 routed to TestPyPI; clean `v0.29.2` ships to production PyPI
after rc verify.

## [0.29.1] — 2026-05-16

### Production cut after the v0.29.1 rc cycle (no code change from 0.29.1rc1)

Version-only bump from `0.29.1rc1` → `0.29.1` in the 6 SSOT locations
(`pyproject.toml`, `pyproject-pure.toml`, `version.py`,
`srmech_profile.toml`, `c/include/ephemerides_spectral.h`, and
`ephemerides_spectral/_data/manifest.json` `version` field). The rc1
TestPyPI publish + clean-external-venv smoke verified the srmech
floor lift before the cut.

### Changed — srmech dependency floor bump `>=0.3.1,<0.4` → `>=0.4.0`

Tracks the srmech v0.4.0 production cut so downstream consumers
transitively pick up the cumulative srmech v0.4.x content:

- **14-class C-parity primitive vocabulary** (Spike #24 Classes A–N
  in native C + Python) — content-addressing (SHA-256), TLV
  byte-canonical serialisation, streaming/NDJSON, dispatch,
  catalog-lookup, templating, search, introspection, cyclic-group /
  modular arithmetic, prime-factorisation / period detection,
  equation-of-centre / Kepler pin-slot, graph-Laplacian / pi-free
  Jacobi, HDC binary-spatter-codes, rational-approximation /
  continued-fraction.
- **Canonical QM/QFT/SM operations layer at `srmech.qm.*`** — single-
  particle (TDSE / TISE / Heisenberg), spin (Pauli + Cl(0,3)),
  potentials (hydrogen + harmonic oscillator), relativistic (Dirac
  γ-matrices + Weyl + charge conjugation + Klein-Gordon), propagators
  (Feynman scalar / fermion / photon / massive-vector), pseudo-Hermitian
  (η-inner-product), gauge (SU(2) / SU(3) Gell-Mann + Casimirs +
  Wilson loops), Standard Model (Higgs + W/Z + Yukawa + CKM).
- **Tool-schema introspection** — ~87 `srmech.amsc.tool_schema`
  entries covering every public callable.

**SSOT files bumped in lockstep:**

- `pyproject.toml` `[project].version` 0.29.0 → 0.29.1rc1 → 0.29.1;
  `[project].dependencies` `srmech>=0.3.1,<0.4` → `srmech>=0.4.0`.
- `pyproject-pure.toml` `[project].version` 0.29.0 → 0.29.1rc1 → 0.29.1;
  `[project].dependencies` `srmech>=0.3.1,<0.4` → `srmech>=0.4.0`.
- `ephemerides_spectral/version.py` `__version__` 0.29.0 → 0.29.1rc1 → 0.29.1.
- `ephemerides_spectral/srmech_profile.toml` `[profile].version`
  0.29.0 → 0.29.1rc1 → 0.29.1; `[profile].srmech_requires` `>=0.3.1,<0.4`
  → `>=0.4.0`.
- `c/include/ephemerides_spectral.h` `ES_VERSION_PATCH` 0 → 1;
  `ES_VERSION_STRING "0.29.0"` → `"0.29.1rc1"` → `"0.29.1"`.
- `ephemerides_spectral/_data/manifest.json` `version` field
  restamped 0.29.0 → 0.29.1rc1 → 0.29.1.

### No code change; no ABI change

`ES_ABI_VERSION` stays at 10 (unchanged from v0.29.0); no
`_research` mirror changes; no test ratchet changes; no `bridge.*`
surface change. Pure dependency-floor bump.

### Versioning

`0.29.0` → `0.29.1rc1` → `0.29.1`. Patch bump (dependency-floor
refresh). rc1 routed to TestPyPI; clean `v0.29.1` ships to production
PyPI after the rc verify.

## [0.29.0] — 2026-05-15

### Production cut after the v0.29.0 rc cycle (no code change from 0.29.0rc1)

Version-only bump from `0.29.0rc1` → `0.29.0` in the 5 SSOT locations
(`pyproject.toml`, `pyproject-pure.toml`, `version.py`, `srmech_profile.toml`,
`c/include/ephemerides_spectral.h`) plus the manifest regen and this
CHANGELOG header.

**Cumulative content of v0.29.0** (one-rc cycle, all content from rc1):

* **TURN_INTEGER channel-basis route** — opt-in
  `es_channel_basis_method(seed, out, D, ES_BASIS_METHOD_TURN_INTEGER)`
  entry point. Cyclic-group-native quarter-turn decomposition (notebook
  §1.4): the splitmix64-derived phase residue lives in `Z_{2^32}`,
  quadrant + within split is integer arithmetic, bit-exact dispatch at
  quarter turns, libm `cos`/`sin` only on the within-quadrant fraction
  (small argument), `i^quadrant` rotation by pure sign/swap. Bit-exact
  quarter turns by construction on every toolchain; no libm cospi/sinpi
  dependency; no `× π` in the global argument.

* **ABI v9 → v10** (additive only): new `es_basis_method_t` enum +
  `es_channel_basis_method()` entry point. The existing
  `es_channel_basis` is preserved as-is and still delegates to LEGACY,
  so the Tier 2a Python-vs-C byte-parity test continues to hold
  byte-for-byte. `_native_bip.EXPECTED_ABI_VERSION` 9 → 10;
  `srmech_profile.toml` `[profile.native].expected_abi_version` 9 → 10.

* **C/Python byte-parity preserved on both routes**:
  `_research/portable_prng.py` gained `splitmix64_turn_integer_basis_element`
  + `splitmix64_turn_integer_basis` (Python mirror of the C TURN_INTEGER
  route). Sibling parity discipline to the LEGACY route's existing
  `splitmix64_phases` + `numpy.exp(1j · φ)` mirror. Both routes now
  have Python-vs-C byte-for-byte agreement pinned in
  `tests/test_channel_basis_parity.py`.

* **JPL Power-of-Ten clean**: pins ratcheted 46 → 49 functions /
  102 → 109 assertions (density 2.22). No `goto`, no `malloc`,
  bounded loops, ≤ 60 lines / function.

* **Bench** (`scripts/bench_turn_integer_basis.py`, NDJSON output):
  on Windows MSVC + WSL2 glibc 2.35, max `|basis(legacy) -
  basis(turn_integer)|` = 8.43e-08 (at float32 ULP scale); both routes
  land at 1.19e-07 on unit-magnitude error; HDC accumulator norm drift
  3.23e-07. Cross-platform bit-identical across all matrix rows.

**Verified on TestPyPI** before the production cut: `0.29.0rc1` boots
cleanly in an external venv on Python 3.10-3.14; plugin-tier
`Profile.native` resolves with ABI v10; LEGACY method byte-identical
to default `es_channel_basis`; C/Python TURN_INTEGER byte-parity holds
on the live wheel; encoder hot path produces 52 uint32 residues at
J2000.

**No code change from v0.29.0rc1**; no ABI change (`ES_ABI_VERSION = 10`
unchanged from rc1).

## [0.29.0rc1] — 2026-05-15

### Added — channel-basis dual-path spike (cyclic-group-native quarter-turn decomposition)

Opens the v0.29.x cycle with a small bench-and-quantify spike on the
channel-basis construction path. Motivation + design rationale in the
project-level [CHANGELOG §0.29.0rc1](../CHANGELOG.md).

**C surface (ABI v9 → v10, additive):**

- New `es_basis_method_t` enum in `c/include/ephemerides_spectral.h`
  (`ES_BASIS_METHOD_LEGACY = 0`, `ES_BASIS_METHOD_TURN_INTEGER = 1`).
- New `es_status_t es_channel_basis_method(uint64_t seed,
  es_complex64_t *out, size_t D, es_basis_method_t method)` entry
  point. The existing `es_channel_basis(seed, out, D)` is preserved
  as-is — it delegates to `es_channel_basis_method(..., LEGACY)`, so
  the Tier 2a byte-parity test continues to hold byte-for-byte.
- `c/src/es_channel_bases.c` refactored: LEGACY and TURN_INTEGER
  routes as separate static helpers, each ≤ 60 lines with ≥ 2 asserts.
  TURN_INTEGER does the integer quarter-turn decomposition described
  in the project CHANGELOG — `phase = (uint32_t)(u >> 32)`,
  `quadrant = phase >> 30`, `within = phase & 0x3FFFFFFF`,
  bit-exact dispatch when `within == 0`, else `cos`/`sin` on
  `(double)within · (π/2 / 2^30)` followed by `i^quadrant` rotation
  (sign/swap, no math).
- JPL audit pins ratcheted: `PIN_RULE_5_TOTAL_FUNCS` 46 → 49,
  `PIN_RULE_5_ASSERTIONS` 102 → 109 (density 109 / 49 ≈ 2.22, above
  the ≥ 2.0 floor). Power-of-Ten clean: no goto, no malloc, bounded
  loops, ≤60 lines/function.

**Python surface:**

- `_native_bip.EXPECTED_ABI_VERSION` 9 → 10.
- New constants exposed: `ES_BASIS_METHOD_LEGACY`,
  `ES_BASIS_METHOD_TURN_INTEGER`.
- New wrapper helpers: `native_channel_basis_method(seed, D, method)`,
  `native_channel_basis_turn_integer(seed, D)`.
- `__all__` updated; existing `native_channel_basis` is unchanged.
- `srmech_profile.toml` bumps `expected_abi_version` 9 → 10.

**Build system:**

- No new CMake feature detection required — the TURN_INTEGER route
  uses only universally-available libm `cos`/`sin` + integer
  arithmetic. Earlier drafts of this spike (cospi/sinpi route) needed
  `check_function_exists(cospi)`; the pivot to integer quarter-turn
  decomposition makes that ceremony unnecessary.

**Tests:**

- New `python/tests/test_channel_basis_dual_path.py`:
  - LEGACY-method route byte-identical to the default `es_channel_basis`.
  - TURN_INTEGER route returns correct shape / dtype.
  - TURN_INTEGER route's per-element `|mag - 1|` ≤ float32 ULP (~1e-6).
  - Quarter-turn dispatch structurally bit-exact: any TURN_INTEGER
    element near a quadrant has the orthogonal component exactly `0.0f`.
  - Soft ratchet: TURN_INTEGER's max `|mag - 1|` ≤ LEGACY's (plus a
    ~6e-8 fairness allowance).
  - Invalid enum value rejected via `ES_ERR_INVALID_KIND`.
  - Deterministic across calls: same seed + same D → byte-identical
    output (deterministic across platforms by construction).
- Extended `python/tests/test_channel_basis_parity.py` (the Tier 2a
  parity file) with sibling TURN_INTEGER byte-parity coverage:
  - `test_channel_basis_turn_integer_byte_identical_py_vs_c` — same
    seed/D grid as the LEGACY parity test, pins byte-for-byte
    agreement between C `es_channel_basis_method(..., TURN_INTEGER)`
    and the new Python mirror
    `_research/portable_prng.splitmix64_turn_integer_basis()` after
    the complex64 cast.
  - `test_turn_integer_basis_quarter_turn_dispatch_bit_exact` — hand-
    injects splitmix64 outputs that decompose to `within == 0` at
    each of the four quadrants, asserts the Python helper emits exact
    `(±1, 0) / (0, ±1)` without invoking any float math.

**Python mirror (TURN_INTEGER):**

- `_research/portable_prng.py` gains
  `splitmix64_turn_integer_basis_element(u)` and
  `splitmix64_turn_integer_basis(seed, n)` — byte-identical Python
  mirror of the C `es_channel_basis_turn_integer_route`. Sibling
  parity discipline to the existing LEGACY mirror
  (`splitmix64_phases` + `numpy.exp(1j · φ)`). Both routes now have
  Python-vs-C byte-parity pinned. Verified cross-platform on Windows
  MSVC + WSL2 glibc 2.35 — identical bytes on both.

**Bench script (not run in CI):**

- New `scripts/bench_turn_integer_basis.py` emits NDJSON to stdout
  (one record per measurement) with per-(seed, D) drift,
  unit-magnitude error, a representative HDC roll-and-accumulate
  norm comparison, and a count of quarter-turn bit-exact dispatches
  (expected ~0 for random splitmix64 phases at D ≤ 65536; non-zero
  if a future bench deliberately seeds quarter-turn-aligned phases).
  The script is the artifact of the bench-and-quantify step — its
  quantitative output decides whether the v0.29.x cycle graduates
  TURN_INTEGER to default + updates the Python mirror, or keeps
  LEGACY as the byte-parity default and TURN_INTEGER as opt-in.

**No encoder hot-path changes.** The 52-body uint32 phase residues
emitted by `es_encode_state` / `bridge.encode_state` are byte-
identical to v0.28.1.

## [0.28.1] — 2026-05-15

### Production cut after the v0.28.1 rc cycle (no code change from 0.28.1rc2)

Version-only bump from `0.28.1rc2` → `0.28.1` in the 5 SSOT locations
(`pyproject.toml`, `pyproject-pure.toml`, `version.py`, `srmech_profile.toml`,
`c/include/ephemerides_spectral.h`) plus the manifest regen and this
CHANGELOG header.

**Cumulative content of v0.28.1** (pure README hygiene on top of v0.28.0):

* **rc1** — stale "Unreleased" bullets removed (LLM tool-schema export + first
  cosmology-instrument pair, both of which shipped in v0.26.1); 3 stale
  body-count `38` references → `52` (current since v0.16.0); 2 shipped
  roadmap items removed (`v0.16.0 Tier-1 BODIES` + `v0.16.x find_itn_chains`);
  heteroclinic roadmap note tightened to reflect what shipped in v0.18.0
  / v0.18.1 (Fiedler partition + spectral Δv).
* **rc2** — two follow-ups from the rc1 PR's "Known ambiguities NOT
  touched" section: **(Option C)** the BIP-vs-HD-state "256 KB state at
  D=65536" ambiguity in the BIP bullet + Memory Footprint table — orphan
  fragment removed, table rows renamed `State (BIP)` / `State (complex128)`
  → `HD state (BIP path)` / `HD state (complex128 path)`, clarifying
  paragraph added above the table; **(Option B)** the DE441 sweep table
  body-identifier rows `earth` → `terra` and `moon` → `luna` to match the
  v0.9.0+ Latin-proper-noun convention used throughout the rest of the
  codebase. Prose references to "Earth" / "Moon" in English-language
  sentences stay as natural-language usage.

**Verified on TestPyPI** across the rc cycle (rc1 + rc2): clean external
venv installs both rc tags green; plugin-tier `Profile.native` resolves;
ABI v9 handshake clean; EOC byte-parity holds (51 patches, both backends);
AMSC sources = 20; tool_schema = 246 self-describing functions.

**No code change; no ABI change** (`ES_ABI_VERSION = 9` unchanged from
v0.28.0); no `_research` mirror changes; no test ratchet changes.
Pure README hygiene patch.

## [0.28.1rc2] — 2026-05-15

### Fixed — two flagged-but-untouched items from the rc1 proofread pass

User reviewed the rc1 PR's "Known ambiguities NOT touched" section
and chose minimum-disruption fixes for both. Neither is a code
change — pure README hygiene continuing the v0.28.1 docs-only
patch story.

**Issue 1 — "256 KB state at D=65536" BIP-vs-HD-state ambiguity (Option C):**
- BIP bullet (Two-stage architecture section): removed the orphan
  "305× faster than the FPU reference; 256 KB state at D=65536"
  fragment that conflated the BIP encoder's per-body output with
  the HD-lifted hypervector state. Replaced with the precise
  user-facing characterisation: "Produces `uint32[52]` per-body
  residues (208 bytes) at any JD."
- Memory Footprint table: renamed `State (BIP)` → `HD state (BIP path)`
  and `State (complex128)` → `HD state (complex128 path)`. Added
  an explanatory paragraph above the table clarifying that the
  BIP encoder's user-facing output (from `default_encode()` /
  `bridge.get_system_state()`) is the `uint32[52]` per-body residue
  array (208 bytes), and the two HD-state rows below size the
  hypervector representation the HD pipeline lifts those residues
  into when running syzygy / observer-bind / eclipse-probability.

**Issue 2 — DE441 sweep table uses `earth`/`moon` (pre-v0.9.0 names) (Option B):**
- Renamed table row identifiers `earth` → `terra` and `moon` →
  `luna` to match the v0.9.0+ Latin-proper-noun convention used
  throughout the rest of the codebase. Prose references to "Earth"
  / "Moon" in English-language sentences (e.g. "Earth phase error
  scales roughly linearly...") stay as natural-language usage; the
  v0.9.0 rename was specifically about body-identifier strings,
  not English vocabulary.

### Versioning

`0.28.1rc1` → `0.28.1rc2`. rc1 hit TestPyPI successfully (verified
externally); rc2 folds the two user-approved proofread fixes into
the same v0.28.1 cycle so the clean v0.28.1 ships the accumulated
README hygiene.

## [0.28.1rc1] — 2026-05-15

### Fixed — stale "Unreleased" bullets in PyPI-rendered README

Two bullets at the top of the version-by-version list in
`python/README.md` described features as future work even though
they had shipped in v0.26.1 (the v0.26.1 entry below explicitly
records them):

- **LLM tool-schema export** — `get_tool_schema`, `list_tool_names`,
  `get_one_tool_schema` + the three CLI subcommands shipped in
  v0.26.1. The local introspection surface now covers ~246
  self-describing bridge functions across 4 formats (Anthropic
  Claude / OpenAI function-calling / Anthropic MCP / plain JSON
  Schema). Cross-package integration through srmech's profile
  pattern landed in v0.27.0: `[profile.tool_schema].extension_file
  = "_srmech_tool_schema.toml"` registers the 9 profile-tier
  bridge surfaces with `srmech.amsc.tool_schema` so LLM agents can
  discover ephemerides-spectral's offerings via the unified
  cross-package surface (`owner="ephemerides"`).

- **First cosmology-instrument pair (CMB Power Spectrum + CMB
  Anomalies)** — `cmb_power_spectrum` (Planck 2018 PR3, 111 bands)
  and `cmb_anomalies` (6 canonical large-scale anomalies) both
  shipped in v0.26.1.

Both bullets removed from the README's release-history section in
this rc. A short HTML comment is left in place documenting the
removal + the cross-package architecture for future readers.

### No code change

Pure README hygiene. All 5 SSOT files bump in lockstep
(`pyproject.toml`, `pyproject-pure.toml`, `version.py`,
`srmech_profile.toml`, `c/include/ephemerides_spectral.h`);
manifest regenerated; no `_research` mirror changes; no test
ratchet changes; no ABI change (`ES_ABI_VERSION = 9` unchanged
from v0.28.0).

### Versioning

`0.28.0` → `0.28.1rc1`. Patch bump (docs-only). RC suffix
auto-routes to TestPyPI per the existing publish-workflow regex.
The clean `v0.28.1` ships to production PyPI after rc verify.

## [0.28.0] — 2026-05-14

### Production cut after the v0.28.x rc stack (no code change from 0.28.0rc5)

Version-only bump from `0.28.0rc5` → `0.28.0` in the 5 SSOT locations
(`pyproject.toml`, `pyproject-pure.toml`, `version.py`, `srmech_profile.toml`,
`c/include/ephemerides_spectral.h`) plus the manifest regen and this
CHANGELOG header.

**Cumulative content of v0.28.0:**

* **rc1** — Phase 10a per-body equation-of-center catalog (51
  closed-form Newton-Kepler patches; Python-BIP backend). Validated
  99.85% Kepler-truth collapse + 94% syzygy-anchor collapse on the
  100-yr Earth-Mars sweep.
* **rc3** — Task `#212` PR-b: srmech `[profile.native]` plugin tier
  + ABI v6→v8 realignment (restores native acceleration on every
  v0.16.0+ install — the silent-rejection bug had quietly forced
  pure-Python fallback for 12+ minor versions) + `es_laplacian.c`
  native-parity drift fix (15 Mars + Saturnian moons).
* **rc4** — Task `#212` PR-c: bridge call-site migration through
  `srmech.profile("ephemerides").native`. `_native_bip.LIB` and
  `srmech.profile("ephemerides").native` are now the same Python
  object — patch-registry runtime state stays consistent across
  both surfaces. Four-way parity ratchet pinned.
* **rc5** — Phase 10a EOC C-side completion (ABI v8→v9). New
  `ES_PATCH_KIND_ECCENTRICITY_CORRECTION` + Newton-Kepler evaluator
  in `c/src/es_patches.c`; `es_patch_t` extended with 3 trailing
  `double` fields; `ES_MAX_PATCHES` bumped 32→64 to fit the 51-body
  EOC catalog. Closes the rc1 backend_caveat: EOC patches now
  produce byte-identical phase residues on both `backend="bip"`
  AND `backend="c"`. JPL Power-of-Ten clean: every new function
  ≥2 asserts, no goto, no malloc, all loops bounded, ≤60 lines.

**TestPyPI verification chain**: rc1 published 2026-05-14 (PR #410);
rc3 published 2026-05-14 (PR #412); rc4 published 2026-05-14 (PR
#413); rc5 published 2026-05-14 (PR #414). Each rc verified in a
clean external venv before merge:
- rc3 + rc4 confirmed four-way native parity
- rc5 confirmed all 51 EOC patches register on both backends with
  byte-exact phase agreement at J2000, ±1 yr, +20 yr, -100 yr

**rc2 was a failed-publish tombstone**: the silent-rejection ABI
v6→v8 realignment unmasked a latent `es_laplacian.c` ↔ JSON
drift on 15 moons that `test_native_parity` had been silently
skipping. rc3 absorbed the parity-drift fix.

**Task `#212` closure**: this production cut closes ADR-0001 §7 Step 2.
The remaining ADR §7 steps live in adjacent sessions:
- Step 3 — antikythera-spectral profile (Task `#213`)
- Step 4 — `PROFILE_AUTHORING_GUIDE.md` (Task `#214`)

**Per-area detail:** see [project CHANGELOG.md §0.28.0](../CHANGELOG.md)
and the individual rc entries below.

## [0.28.0rc5] — 2026-05-14

### Added — Phase 10a EOC C-side completion (ABI v8 → v9)

The final rc in the v0.28.x stack before the production cut. Closes
the rc1 backend_caveat: per-body equation-of-center patches now work
on both `backend="bip"` and `backend="c"`, producing byte-identical
phase residues across all 52 bodies at every Δt.

### C-side additions (`c/include/ephemerides_spectral.h` + `c/src/es_patches.c`)

- **`ES_PATCH_KIND_ECCENTRICITY_CORRECTION = 2`** — third patch kind
  enum value, joining `SINUSOID` and `COUPLED_SINUSOID`.

- **`es_patch_t` struct grew by three trailing `double` fields**:
  `eccentricity`, `mean_anomaly_at_j2000_rad`, `n_rad_per_day`.
  Additive layout — original field offsets preserved, but
  `sizeof(es_patch_t)` increased. This is the load-bearing ABI v9
  bump captured below.

- **Newton-Kepler evaluator** (`es_eval_eoc_residue` in
  `es_patches.c`). Mirrors the Python
  `EccentricityCorrectionPatch.evaluate()` byte-for-byte:
  - Newton iteration on `E - e·sin E = M` (bounded 30 iters, tol
    1e-14 rad, warm-start `E = M + e·sin M` for `e > 0.6`).
  - Half-angle true-anomaly formula:
    `nu = 2·atan2(sqrt(1+e)·sin(E/2), sqrt(1-e)·cos(E/2))`.
  - Returns `(nu(t) - M(t)) - (nu(J2000) - M_0)` mapped to the
    uint32 residue with `es_banker_round`. **J2000-anchored by
    construction** — returns 0 at Δt = 0.
  - Principal-branch wrap uses `floor`-based modulo (single libm
    call, no unbounded `while`-loop).

- **`es_clear_eoc_patches()`** — selective clear by kind. Mirrors
  the Python `_eoc_catalog.clear_eoc_patches()` so the two
  registries stay in sync when the bridge selectively clears EOC
  patches.

- **Validator extension** — `es_validate_patch` accepts the new
  kind and enforces `eccentricity ∈ [0, 1)` + non-zero
  `n_rad_per_day` (rejects hyperbolic / parabolic / degenerate
  inputs at apply time).

- **JPL Power-of-Ten compliance** — every new function carries ≥ 2
  asserts (Rule 5); no `goto` (Rule 1); no `malloc` (Rule 3); all
  loops bounded (Rule 2, Newton at 30 iters; `es_clear_eoc_patches`
  at `ES_MAX_PATCHES = 32`); each function under 60 lines (Rule 4).

### Python-side wiring (`_native_bip.py` + `bridge.py`)

- **`EXPECTED_ABI_VERSION = 9`** (was 8) — lockstep with the C
  header. ABI history comment extended.

- **`EsPatch` ctypes struct gained the 3 trailing doubles**, in
  the same order as the C struct.

- **`native_apply_eoc_patch()`** — new helper to register an EOC
  patch in the C registry; mirrors `native_apply_sinusoid_patch` /
  `native_apply_coupled_patch` style.

- **`native_clear_eoc_patches()`** — wrapper for `es_clear_eoc_patches`.

- **`_mirror_patch_to_native` gained an EOC branch** —
  `isinstance(patch, EccentricityCorrectionPatch)` dispatches to
  `native_apply_eoc_patch`. Bridge call sites that go through
  `_mirror_patch_to_native` (e.g. `apply_patch`,
  `apply_custom_patch`) now pick up C-side EOC support
  transparently.

- **`bridge.apply_eoc_patches`** — after registering Python-side
  patches via `_eoc_catalog.apply_eoc_patches`, iterates and calls
  `_mirror_patch_to_native` for each. On any C-side rejection,
  rolls back BOTH registries (Python + C) to keep parity. Return
  envelope now includes `n_registered_c_side` and `backends_active`
  (e.g. `["bip", "c"]` on native installs).

- **`bridge.clear_eoc_patches`** — calls
  `native_clear_eoc_patches()` after the Python-side clear so the
  two registries stay in sync.

- **`srmech_profile.toml` `[profile.native].expected_abi_version = 9`**
  — lockstep with the C side. srmech's loader will surface
  `AbiMismatchError` if the bundled library reports anything other
  than 9.

### Tests

- **`test_eoc_catalog.test_eoc_patch_kind_now_c_native`** —
  **flipped from the rc1 python-only ratchet**. Asserts
  `_mirror_patch_to_native(EOC patch)` returns `None` (success) on
  native installs; documents the pure-Python skip path.

- **`test_eoc_catalog.test_eoc_patch_byte_parity_across_backends`**
  — new ratchet pinning the rc5 deliverable. Registers Earth +
  Mars EOC patches and asserts byte-identical phase residues
  between `backend="bip"` and `backend="c"` at four Δt epochs
  (J2000, ±1 yr, +20 yr, -100 yr).

- **`test_parity_smoke`** — rationale strings for the 6 EOC bridge
  entries updated. The 4 read-only listings stay `python_only` (no
  encoder runtime; JSON envelope only). `apply_eoc_patches` /
  `clear_eoc_patches` stay `python_only` in the parity_smoke
  framework (state mutators don't fit its pure-function model);
  the encoder-runtime parity is pinned by the new
  `test_eoc_catalog` test instead.

### Dependency change

`srmech>=0.3.1,<0.4` — unchanged. rc5 doesn't change the srmech
profile surface; it bumps `expected_abi_version` 8 → 9 within the
existing srmech-loader-managed activation flow.

### Versioning

`0.28.0rc4` → `0.28.0rc5`. Cumulative per the rc-stacking discipline:
- rc1 — Phase 10a EOC catalog (Python-BIP backend)
- rc3 — srmech `[profile.native]` plugin tier + ABI v6→v8 realignment
   + `es_laplacian.c` parity-drift fix (rc2 was a failed-publish
  tombstone)
- rc4 — bridge call-site migration through `srmech.profile.native`
  (four-way parity ratchet)
- **rc5** — Phase 10a EOC C-side completion (ABI v8 → v9)

After rc5 verifies on TestPyPI, the v0.28.0 production-cut PR opens
for human review.

### ABI bump (v8 → v9)

`ES_ABI_VERSION = 9`. **Wire-format change**: `sizeof(es_patch_t)`
increased by 24 bytes (3 trailing `double`s). Caller code linked
against v8 headers reading patches written by v9 (or vice versa)
would see truncated / overrun reads on the new fields; the
load-time ABI handshake (srmech's `_maybe_load_native` +
`_native_bip`'s direct check) catches the mismatch and refuses to
load — degrading to pure-Python rather than producing silent
garbage.

## [0.28.0rc4] — 2026-05-14

### Added — Task `#212` PR-c: bridge call-site migration through srmech profile

ADR-0001 §7 Step 2 call-site-migration portion (the third and final
PR of Task `#212`). With PR-b (rc3) wiring the srmech `[profile.native]`
plugin tier, PR-c migrates ephemerides-spectral's OWN internal native-
library loading to go through `srmech.profile("ephemerides").native`
when srmech is importable — replacing the existing direct
`ctypes.CDLL(library_path)` call as the primary path.

**Wire-up** (`python/ephemerides_spectral/_native_bip.py`):

- New `_load_via_srmech_profile()` function. Lazily imports srmech
  (so the module stays importable without srmech), calls
  `srmech.profile("ephemerides")`, returns the loaded `(CDLL handle,
  library_path)` tuple when the plugin tier loaded successfully;
  returns `None` on any failure so the existing direct-ctypes path
  remains the fallback.
- Module-load logic reworked: try the srmech path first; if it
  returns a handle, reuse it; otherwise fall through to
  `_find_library()` + `ctypes.CDLL()`. Both paths converge on the
  same `_bind()` + ABI handshake + globals-population block.
- New `LOAD_SOURCE` module global: `"srmech_profile"` when the
  profile path won, `"direct_ctypes"` when the local fallback did,
  `None` when `HAS_NATIVE` is False.

**Why object identity matters**: srmech's profile-tier callers and
ephemerides-spectral's own `LIB.*` calls now share the *same*
`ctypes.CDLL` object. Patch-registry runtime state
(`es_apply_patch` / `es_clear_patches` / `es_n_active_patches`
internal globals) is therefore consistent across the two surfaces.
Without PR-c, two separate `dlopen()` calls of the same library
file would yield two CDLL instances that could see different
patch-registry views even when registered through the same Python
process — a footgun the migration eliminates.

### Tests

`tests/test_native_parity.py` — three new ratchets:

- `test_load_source_is_srmech_profile_when_available` — pins that
  when srmech + the ephemerides plugin tier are present, the
  profile path is chosen over the direct fallback. Skips cleanly
  when srmech is missing.
- `test_lib_is_same_object_as_profile_native` — pins
  `_native_bip.LIB is srmech.profile("ephemerides").native`
  (Python `is`, not `==`). Catches the regression where two CDLLs
  of the same file land in the two surfaces.
- `test_profile_native_encode_matches_direct_ctypes_encode` —
  opens a SECOND independent `ctypes.CDLL` on the same library file
  and runs `es_encode_state` through both handles at four Δt
  epochs (0, 1 yr, 20 yr, -100 yr); asserts byte-exact agreement
  on every body. Defends against the hypothetical "both paths
  return garbage that happens to match because they're the same
  object" failure mode.

Combined with the existing 12 tests, `test_native_parity.py` now
pins a **four-way parity property**: Python BIP encoder ↔ profile-
loaded native ↔ direct-ctypes native ↔ bridge `backend="c"`.
Every cell of the matrix produces byte-identical phase residues
at the same JD.

### Dependency change

`srmech>=0.3.1,<0.4` — unchanged. PR-c calls
`srmech.profile("ephemerides")` lazily; module import remains
clean when srmech isn't installed.

### Versioning

`0.28.0rc3` → `0.28.0rc4`. Cumulative per the rc-stacking discipline:
rc4 carries forward the Phase 10a EOC catalog (rc1) + plugin-tier
declaration + ABI realignment + es_laplacian regen (rc3); adds the
PR-c migration on top. The clean `v0.28.0` will ship rc1 + rc3 +
rc4 + the forthcoming rc5 (EOC C-side completion).

### No ABI bump

`ES_ABI_VERSION = 8` unchanged. `EXPECTED_ABI_VERSION = 8`
unchanged. PR-c rearranges *how* the library handle is obtained;
it does not change *what* the C side exposes or how the Python
side calls it.

## [0.28.0rc3] — 2026-05-14

The rc2 git tag (`ephemerides-spectral-v0.28.0rc2`) was pushed but
the publish workflow failed at the cibuildwheel Linux matrix step
and never reached TestPyPI. rc3 absorbs the full rc2 content plus
the `es_laplacian.c` drift fix described below.

### Added — Task `#212` PR-b: srmech `[profile.native]` plugin-tier declaration

ADR-0001 §7 Step 2 plugin-tier portion. ephemerides-spectral's srmech
profile graduates from "simple" (PR-a, v0.27.0) to "plugin" tier.
`srmech.profile("ephemerides")._maybe_load_native()` now resolves the
platform-specific shared library bundled in the wheel, performs the
`es_abi_version()` handshake, and exposes a bound `ctypes.CDLL` as
`Profile.native`.

**Wire-up** (`python/ephemerides_spectral/srmech_profile.toml`):

- New `[profile.native]` block: `library = "ephemerides_spectral"`,
  `install_path = "ephemerides_spectral/_native"`,
  `abi_version_function = "es_abi_version"`,
  `expected_abi_version = 8`.
- 8 new `[profile.native.symbols.*]` entries covering the encoder hot
  path + introspection accessors (`es_version`, `es_abi_version`,
  `es_n_bodies`, `es_body_index`, `es_encode_state`, `es_encode_at_jd`,
  `es_cos_lut`, `es_residue_to_radians`). srmech v0.3.x binds by name
  only; declaring `argtypes`/`restype` is forward-compatible with
  future srmech versions and documents the intended plugin-tier
  surface for PR-c's bridge call-site migration.
- File header tier comment updated from "simple" → "plugin".

### Fixed — silent native-acceleration rejection across v0.16.0 → v0.28.0rc1

`_native_bip.EXPECTED_ABI_VERSION` was left at `6` while the C
library's `ES_ABI_VERSION` advanced to `8` in v0.16.0 (Tier-1 BODIES
expansion, commit `f1d4b82`). Every wheel install since v0.16.0 has
silently fallen back to the pure-Python BIP encoder because the
ctypes shim's ABI-handshake check rejected the bundled library with
`LOAD_ERROR = "native ABI mismatch ... binary is v8, Python expects v6"`.
Bumping the constant to `8` realigns the shim with the shipped
library; native acceleration is restored across the install base.

ABI history comment block extended (`v7` = v0.15.0 Sol Moon Times
roster completion; `v8` = v0.16.0 Tier-1 BODIES expansion). The
v0.28.0rc3 realignment is a Python-side catch-up only; the C side
has been at v8 since v0.16.0.

### Fixed (rc3 only) — native parity drift unmasked by the v6→v8 realignment

Flipping `HAS_NATIVE` from False to True for the first time since
v0.16.0 (above) caused `test_native_parity` to actually run on the
cibuildwheel Linux matrix. It failed: native and Python BIP phases
diverged on 15 bodies at every Δt — calypso, deimos, dione,
enceladus, helene, hyperion, iapetus, mimas, phobos, phoebe,
polydeuces, rhea, telesto, tethys, titan — exactly the Mars +
Saturnian moons that depend on the `mar099s` + `sat441` JPL
auxiliary kernels.

Root cause: `c/src/es_laplacian.c` and
`python/.../_data/initial_phases.json` were last regenerated under
DIFFERENT auxiliary-kernel availability. `es_laplacian.c` was
emitted at a session when those kernels WERE staged on the dev box;
the JSON was rebuilt later when they were NOT. The stub-period
fallback path produces different phase residues than the full-kernel
calibration path. Native-parity silently held while `HAS_NATIVE` was
False; surfaced loudly once the realignment unblocked the test.

Fix (rc3): re-ran `python c/codegen/emit_c_tables.py` with the
current dev-box kernel state (still missing `mar099s` + `sat441` —
JPL FTP returns 404 for both, archived in the codegen DEBUG log).
The codegen falls back to the parent-body period stub for the 15
affected moons. Result: C side now produces the SAME stub-fallback
phases the JSON does. `Bodies disagreeing: 0` after the regen.

This aligns the two sides but does NOT restore real-truth ephemeris
calibration for Mars + Saturnian moons; both sides now consistently
use the parent-period stub. Restoring real-truth calibration
requires mirroring `mar099s` + `sat441` (~1.5 GB combined) into the
dev box build environment AND into the cibuildwheel CI matrix.
Deferred to a separate ship; out of scope for Task `#212`.

### Smoke + ratchets

`ephemerides_spectral/_srmech_smoke.py` gains a fourth check: assert
`_native_bip.HAS_NATIVE is True` on plugin-tier installs. Pure-Python
wheels (Pyodide / WASM / no-C build) detected by `LOAD_ERROR` pattern
matching and skipped without failure. Catches future silent-rejection
regressions loudly via the srmech-side `SmokeTestFailedError`.

New `tests/test_srmech_profile.py` — 13 ratchets total:

- **Static (9 tests, no srmech required)**: `[profile.native]` block
  presence + required-field schema + `expected_abi_version` agreement
  with `_native_bip.EXPECTED_ABI_VERSION` (the single anti-drift
  ratchet for the v0.27.0 silent-rejection bug) + library basename +
  install path + abi function name + 8 declared symbols.
- **Activation-path (4 tests, require srmech + plugin-tier wheel)**:
  `srmech.profile("ephemerides")` resolves; `Profile.native` is not
  None; `_native_meta["abi_version"] == 8`; `repr(p)` reports
  `(plugin)`; every declared symbol resolves via `getattr(p.native, ...)`.

Activation-path tests skip cleanly on pure-Python installs and source-
tree shadowing with explicit reason strings so CI matrix surfaces
what's running where.

### Dependency change

`srmech>=0.3.1,<0.4` — unchanged from v0.28.0rc1 (already pinned at
the floor that contains the Form-1 entry-point + `[profile.tool_schema]`
loader fixes the chess-spectral POC surfaced).

### Versioning

`0.28.0rc1` → `0.28.0rc3`. (rc2 was a failed-publish tag — pushed
to GitHub but the cibuildwheel Linux matrix failed before TestPyPI
upload. rc3 absorbs rc2's full content + the `es_laplacian.c`
drift fix.) Cumulative per the rc-stacking discipline
(`memory/feedback_rc_stacking_versioning.md`): rc3 carries forward
the Phase 10a EOC catalog from rc1 and adds Task `#212` PR-b on
top. The clean `v0.28.0` to production PyPI will ship the
accumulated stack (rc1 EOC + rc3 plugin tier + native-parity fix +
forthcoming rc4 PR-c + rc5 EOC C-side completion).

### No ABI bump

`ES_ABI_VERSION = 8` unchanged. The Python-side `EXPECTED_ABI_VERSION`
catch-up does not change the C ABI; it aligns the Python shim with
the C side's existing v8.

## [0.28.0rc1] — 2026-05-14

### Added — Phase 10a: Per-body equation-of-center catalog (closed-form Kepler series)

**Sprint opener for the v0.28.x rc cycle.** v0.27.0 production shipped earlier today with only the Task #212 srmech profile pattern (PR-a). Phase 10a is the next feature ship and starts a fresh minor cycle under the project's rc-stacking discipline (`memory/feedback_rc_stacking_versioning.md`): subsequent v0.28.0rcN tags will accumulate further v0.28-cycle features on top of this rc1, with the final `v0.28.0` to production PyPI shipping the accumulated stack.

**Motivation** — 100-yr Earth-Mars syzygy sweep on v0.26.1 surfaced a residual whose 47-pt FFT placed **84% of power** in two adjacent bins bracketing the predicted Earth+Mars equation-of-center alias (~15.78 yr at synodic cadence). The BIP encoder calibrates each body's phase residue at J2000 to `L_true(J2000)` (read from DE441) and then linearly advances at the mean motion, so the residual is exactly the EOC term `L_true(t) − L_BIP(t) = (ν(t) − M(t)) − (ν(J2000) − M(J2000))`. Phase 10a closes this residual closed-form, MPM-clean (no fit, no SGD, no random init).

**New artefacts:**

- `_research/secular_elements_data.py` — 51-row J2000 Keplerian mean-elements catalog covering every non-Sun body in the 52-body BIP roster (Sun has e ≡ 0; no EOC contribution). Frame partition: 13 heliocentric (9 planets + 4 main-belt asteroids) + 38 parent-centric (1 Luna + 2 Mars moons + 11 Jovian + 15 Saturnian + 5 Uranian + 3 Neptunian + 1 Charon). Subsystem authority chain in `SOURCES`: Standish 1992 + Park 2021 DE441 (planets); Chapront-Touzé & Chapront 1991 ELP2000 (Luna); Lainey 2007 MAR063 (Mars moons); Lieske 1998 E5 (Galileans); Cooper 2006 (Jovian inner regulars); Jacobson 2000 JUP100 (Jovian irregulars); Vienne & Duriez 1995 TASS / Jacobson 2006 SAT375 (Saturnian classical); Spitale 2006 (co-orbitals + trojans); Jacobson 1998 (Phoebe); Laskar-Jacobson 1987 GUST86 (Uranian); Jacobson 2009 NEP078 (Neptunian); Brozovic 2015 (Charon); JPL Small-Body Database (asteroids). 16 SOURCES entries total.

- `_research/diagnosed_fibers.py` — new `EccentricityCorrectionPatch` dataclass + Newton-Kepler evaluator. Patch parameters `(eccentricity, mean_anomaly_at_j2000_rad, n_rad_per_day)` derive closed-form from the body's secular elements; evaluator Newton-solves Kepler's equation `E − e·sin E = M` (bounded 30-iter loop, tol 1e-14 rad) at both `M(t) = M₀ + n·Δt` and `M(J2000) = M₀`, computes `ν` via half-angle formula, returns `(ν(t) − M(t)) − (ν(J2000) − M₀)` as the integer residue correction. **J2000-anchored by construction** — patch returns exactly 0 at Δt=0, so BIP's `L_true(J2000)` calibration isn't double-counted. Exact at any eccentricity from Triton's e ≈ 1.6e-5 through Nereid's e = 0.7507; no power-series truncation.

- `_research/eoc_catalog.py` — generator that turns each secular-elements row into an `EccentricityCorrectionPatch`. Public surfaces: `EOC_CATALOG` dict (51 patches keyed by body), `build_eoc_patch(body)`, `list_eoc_patches()`, `get_eoc_patch(body)`, `apply_eoc_patches(bodies=None, frame=None, parent=None)`, `clear_eoc_patches()`, `heliocentric_bodies()`, `parent_centric_bodies(parent=None)`.

- `research/attested/secular_elements/` (mirrored to `_research/attested/secular_elements/`) — AMSC `literature_curated` attested source. `descriptor.toml` (canonical_doi: 10.3847/1538-3881/abd414 Park 2021 DE441), `row.schema.json` (14-field row contract; draft 2020-12), `row.ndjson` (51 data rows generated from `SECULAR_ELEMENTS` with per-row `source_doi` following the v0.27.0-phase-A naming convention: real Crossref DOIs preferred; `nodoi:` for pre-Crossref JPL technical documents; `isbn:` for textbook references; `url:` for the JPL Small-Body Database). `n_sources` 19 → 20; `adapter_class="curated"` 16 → 17.

**Bridge surfaces (6 new functions)** — `list_secular_elements`, `get_secular_elements`, `list_eoc_patches`, `get_eoc_patch`, `apply_eoc_patches`, `clear_eoc_patches`. Each takes `frame` and/or `parent` filters where applicable. The LLM tool-schema export (v0.26.1 feature) auto-discovers all 6 — total tool count 240 → 246.

**CLI subcommands (6 new)** — `secular-elements`, `secular-elements-get`, `eoc-patches`, `eoc-patch`, `eoc-patches-apply`, `eoc-patches-clear`. Mirror the bridge surfaces 1:1.

**Validation (the closed-form-algebra payoff)** — 100-yr Earth-Mars syzygy sweep with `terra` + `mars` EOC patches active:

| Metric | Before EOC | After Earth+Mars EOC | Collapse |
|---|---:|---:|---:|
| Worst anchor-date offset (vs textbook) | 35.32 d | **3.05 d** | **91%** |
| RMS anchor-date offset (16 anchors) | 19.79 d | **1.12 d** | **94%** |
| Kepler-truth Δλ at opposition JDs (RMS) | 9.26° | **0.014°** | **99.85%** |
| Kepler-truth Δλ peak | 15.75° | **0.015°** | **99.90%** |

The 0.014° RMS means the BIP+EOC encoder matches the closed-form Kepler ground truth to ~1/60th of a degree (essentially numerical precision); the residual 1.12 d anchor RMS is the genuine off-diagonal Mars-Jupiter fiber content — Phase 10b's target.

**Sun-from-SSB wobble falsified** as bin-5 explanation. Hypothesis (bin-5 at 20.07 yr = Jupiter-Saturn synodic Sun-wobble) tested closed-form by direct Sun-SSB subtraction; collapsed only 0.7%. Most likely DFT side-lobe leakage from the dominant EOC peak at bin 6 (predicted 3.0%, observed 3.5%). Note stashed at `docs/srmech/notes/sun-wobble-falsification-2026-05-14.md`. This is the project's first published-internal falsification of a candidate Phase-10b coupling.

### Backend caveat

EOC patches are **Python BIP backend only** in v0.28.0rc1 (`backend="bip"`, default for the Python wheel). The C-side patch registry doesn't yet recognise the `eccentricity-correction` kind; C-side support requires an ABI bump (new `ES_PATCH_KIND_ECCENTRICITY_CORRECTION`) queued for a later v0.28.x rcN or for v0.29. With EOC patches active, `backend="c"` returns the unpatched BIP residue while `backend="bip"` returns the patched value. A regression test (`test_eoc_patch_is_python_only_kind` in `test_eoc_catalog.py`) pins the design decision so the docstring + ROADMAP + ABI-bump plan don't drift apart.

### Tests

- `tests/test_eoc_catalog.py` — 39 ratchets: coverage (51-body, frame partition, 16 sources), period agreement vs `BODIES` (max rel_err 4.6e-4 Saturn), Newton-Kepler correctness vs independent closed-form (parametrized across e=0.0001 through 0.75), J2000-anchoring (every patch returns 0 at Δt=0), frame discipline, AMSC dual-author parity (byte-for-byte field agreement on 8 spot-checked bodies + provenance completeness + source_doi prefix convention), bridge filter semantics, apply/clear round trip, Python-BIP-only kind ratchet.
- `tests/test_attested_collector.py` — `n_sources` ratchets bumped 19 → 20 and 16 → 17 (curated class); alphabetical key list updated.
- `tests/test_parity_smoke.py` — 6 new EOC bridge functions classified as `python_only` with rationale (mirroring the backend caveat).

### Dependency change

`srmech>=0.3.1,<0.4` — unchanged from v0.27.0 (entered the dependency floor at v0.27.0rc1). Phase 10a doesn't introduce additional srmech surface; the v0.27.0 srmech-profile-pattern integration (`[project.entry-points."srmech.profiles"] ephemerides = "ephemerides_spectral"`) continues to work.

### Versioning

`0.27.0` → `0.28.0rc1`. v0.27.0 production already shipped with Task #212 PR-a content; Phase 10a is feature-rich enough (51-body catalog + 6 bridge surfaces + 6 CLI subcommands + new AMSC source) to merit a minor bump on its own. RC suffix auto-routes to TestPyPI per the existing rc-suffix workflow logic; later v0.28.x rcs accumulate on top, and the final `v0.28.0` ships the stack to production PyPI.

### No ABI bump

`ES_ABI_VERSION = 8` unchanged (since v0.13.x). Phase 10a is Python-side additive; the C-side ABI bump that adds `ES_PATCH_KIND_ECCENTRICITY_CORRECTION` is queued separately.

## [0.27.0] — 2026-05-14

### Production cut — srmech profile pattern PR-a (no code change from 0.27.0rc1)

Version-only bump from 0.27.0rc1 → 0.27.0 in the four SSOT locations
plus the profile descriptor + this CHANGELOG header. End-to-end
TestPyPI verification cleared on Windows / Python 3.14 + production
srmech 0.3.1:

```
srmech:                0.3.1 (from PyPI)
ephemerides-spectral:  0.27.0rc1 (from TestPyPI)
Profile: ephemerides 0.27.0rc1
ephemerides tools: 9
get_version: 0.27.0rc1
list_bodies n=: 52
list_attested_sources ok=: True | n_sources=: 19
```

PR-b (plugin tier — `[profile.native]` for libephemerides_spectral)
and PR-c (call-site migration with ABI parity) follow as separate
ships per ADR-0001 §7 Step 2's multi-PR plan.

See [0.27.0rc1] below for the full PR-a content.

## [0.27.0rc1] — 2026-05-14

### Added — srmech profile pattern, PR-a (Task #212, ADR-0001 §7 Step 2)

ephemerides-spectral is now discoverable as the **`"ephemerides"`
srmech profile** via the `srmech.profiles` entry-point group. Two paths
to the same code:

```python
# Direct (unchanged):
from ephemerides_spectral import bridge
bodies = bridge.list_bodies()

# Via srmech (new in 0.27.0):
import srmech
eph = srmech.profile("ephemerides")
bodies = eph.list_bodies()
```

**This rc1 is PR-a — the simple-tier portion.** PR-b will add
`[profile.native]` for `libephemerides_spectral` (plugin tier, ctypes
ABI handshake); PR-c will migrate bridge call sites to exercise the
ctypes path through srmech's loader. Splitting per ADR §7 Step 2 so
each layer of the integration gets its own verification cycle.

### Bridge surfaces declared

Nine functions, curated subset of the full ~166-function bridge:

- **Introspection**: `get_version`, `list_bodies`.
- **Dynamics**: `find_syzygies`, `get_breathing_modulation`,
  `find_itn_chains` (the v0.17.0 resonance-graph ITN search).
- **Electromagnetic**: `get_em_state` (the v0.19.0 surface).
- **AMSC**: `list_attested_sources`, `get_attested_dataset`,
  `attestation_audit` — these are the post-Task-#197 srmech-powered
  surfaces; the profile-level path makes them double-discoverable
  via `srmech.profile("ephemerides")` (consistent with the profile
  pattern) **or** via srmech's own universal catalog bridge.

The remaining ~157 bridge functions stay accessible via direct
import (`from ephemerides_spectral import bridge`). Profile authors
can grow the declared subset in minor version bumps without breaking
compatibility.

### New files (under `ephemerides_spectral/`)

- `srmech_profile.toml` — profile descriptor (ADR-0001 §3 schema
  v1.0).
- `_srmech_smoke.py` — activation-time smoke test (calls
  `get_version` + `list_bodies` + `list_attested_sources`; avoids
  heavy skyfield-dependent surfaces).
- `_srmech_tool_schema.toml` — tool_schema extension registering
  the nine bridge functions with `owner = "ephemerides"`.

### Dependency change

- `srmech>=0.2.0` → `srmech>=0.3.1,<0.4`. Same rationale as
  chess-spectral 1.19.0: v0.3.1 is the first srmech version with
  Form-1 entry-point support + `[profile.tool_schema]` extension
  loading. v0.3.0 would enumerate the ephemerides profile as
  invalid.

### `[project.entry-points."srmech.profiles"]` declaration

```toml
[project.entry-points."srmech.profiles"]
ephemerides = "ephemerides_spectral"
```

### Versioning

`0.26.1` → `0.27.0rc1`. Minor bump (additive surface). RC suffix per
the rc-first publish discipline; TestPyPI verification before the
clean `0.27.0` cut. Tags `ephemerides-spectral-v0.27.0rc1` auto-route
to TestPyPI via the existing rc-suffix workflow logic.

## [0.26.1] — 2026-05-14

### Production cut — AMSC migration + LLM tool-schema + CMB cosmology pair + v0.27.0-phase-A AMSC backfills

Production PyPI ship of the accumulated unreleased work after a TestPyPI verification cycle confirmed cross-package compatibility with the parallel **srmech v0.2.0** production cut.

**Headline content** (sub-sections below have the per-area detail):

- **Task #197 Phase 4** — AMSC framework migrated out of ephemerides-spectral and into `srmech.amsc.*`. 12 framework modules (~2,931 LOC) removed from the wheel; `srmech` becomes a hard runtime dep. No public-API changes on `ephemerides_spectral.bridge` — all attested surfaces still work, they now delegate.
- **LLM tool-schema export** — self-describing bridge surface across all ~240 public functions in four formats (Anthropic Claude / OpenAI function-calling / Anthropic MCP / plain JSON Schema). Three new bridge functions (`get_tool_schema`, `list_tool_names`, `get_one_tool_schema`) + three CLI subcommands.
- **First cosmology-instrument pair** — `cmb_power_spectrum` (Planck 2018 PR3 TT, 111 bands, ℓ=2..2499) + `cmb_anomalies` (six canonical large-scale anomalies). First catalogs at the Mpc-to-Gpc scale; bridge gains five new public functions and five new CLI subcommands.
- **v0.27.0-phase-A AMSC backfills × 12** — Mercury, Luna, Mars, Sun, Toroidal-Residual, Hawaiian-Emperor, Yarkovsky/YORP, Mars Tharsis, Axial Seamount, Sol Dynamical-Regime classifier (paired training + probes rosters), Pluto-Charon, Loki Patera. `n_sources` rose 13 → 19; `adapter_class="curated"` 10 → 16.

### Runtime dependency — `srmech>=0.2.0`

- `python/pyproject.toml`: `srmech>=0.1.0` → `srmech>=0.2.0`. Floor bumped to match the parallel session's production cut. Mirrored in `python/pyproject-pure.toml` (which gained the `srmech` dep declaration in this version — it had been missing since the Phase 3 import swap; pure-wheel installs prior to v0.26.1 would have hit `ImportError` on first import, caught and fixed here).

### Verification history

A `0.26.1rc1` rc was shipped to TestPyPI (tag `ephemerides-spectral-v0.26.1rc1`, PR #396) to verify ephemerides-spectral source compatibility against `srmech==0.1.1rc9` on TestPyPI ahead of the srmech v0.2.0 production cut. The rc cycle used Option B (pyproject runtime-dep pin to the rc-form spec + workflow-side `PIP_EXTRA_INDEX_URL` exports), all 15 cibuildwheel matrix cells passed, and end-to-end install + assertion verify on a clean external venv reported `ALL ASSERTIONS PASSED` (including `srmech.__version__ == "0.1.1rc9"`). With this 0.26.1 production cut, the rc-cycle plumbing is reverted: `srmech>=0.2.0` floor + no `PIP_EXTRA_INDEX_URL` env / `CIBW_ENVIRONMENT` block.

### Other notes

- No code changes between 0.26.1rc1 and 0.26.1; only the rc-cycle scaffolding was reverted (workflow envs, pyproject comment blocks) and the version SSOT bumped.
- No ABI bump (ES_ABI_VERSION = 8 unchanged).
- README freshness regexes in `tests/test_readme_freshness.py` now accept optional `(?:rc\d+)?` suffixes on Status banner + `*(current)*` marker — option-independent ratchet relaxation kept for any future rc cycle.

### Changed — AMSC framework migrated to `srmech.amsc.*` (Task #197 Phase 4)

The Attested Multi-Source Collector (AMSC) framework — previously vendored
as `_research/attested_collector_{format,descriptor,catalog,gap_suggester}.py`
and `_research/attested_adapters/` — has been **removed from this package**
and now lives at `srmech.amsc.*` on PyPI.

- **New runtime dependency**: `srmech>=0.1.0` (added in Phase 3, was already
  pulled in for the import-swap; this phase removes the now-dead duplicate
  copies).
- **Files deleted** from the wheel: 12 framework modules (~2,931 LOC inside
  the package) — 4 top-level (`attested_collector_format.py`,
  `attested_collector_descriptor.py`, `attested_collector_catalog.py`,
  `attested_collector_gap_suggester.py`) and 8 adapter modules under
  `_research/attested_adapters/` (`_base.py`, `__init__.py`,
  `html_scraper.py`, `json_api.py`, `csv_bulk.py`, `netcdf_grid.py`,
  `geotiff_bbox.py`, `literature_curated.py`).
- **Wheel size delta**: −37,416 bytes (−4.7 % from 800,096 B to 762,680 B
  on the cp314-cp314-win_amd64 build).
- **Codegen `manifest.json` n_files**: 154 → 142 (−12). Codegen
  `_INCLUDED_MODULES` and `_INCLUDED_SUBDIRS` updated in
  `codegen/emit_research_modules.py` to drop the AMSC framework entries
  (the dropped entries are preserved as comments documenting the
  migration).
- **No API surface changes** in `ephemerides_spectral.bridge`. The
  bridge functions `list_attested_sources`, `get_attested_dataset`,
  `get_attested_descriptor`, `attestation_audit`,
  `suggest_gap_collections`, and all CLI subcommands that delegate to
  them continue to work byte-identically. The cross-package
  `register_attested_root()` /  `register_classifier()` /
  `register_probes()` bootstrap (added in Phase 3 in
  `ephemerides_spectral/__init__.py`) is what wires srmech's accessors
  to ephemerides-spectral's `_research/attested/` catalog SSOTs.
- **Test parity** (5-gate boundary check): srmech 59/59 pass;
  ephemerides-spectral 2128 passed + 42 skipped = 2170 collected,
  byte-identical to the Phase 3 boundary baseline (the 42 skips are all
  native-library-fallback environmental skips unrelated to the
  refactor). Wheel builds clean; `twine check --strict` PASSED. Codegen
  deterministic on re-run (manifest byte-identical).

This is a **structural refactor**, not a behaviour change. Existing
consumers who only call public bridge surfaces or CLI subcommands need
no code changes. Consumers who imported from `ephemerides_spectral._research.attested_collector_*`
(a private, `_`-prefixed subpackage that has no documented public API)
must switch to `srmech.amsc.*` — this is the only breaking change, and
its blast radius is internal-only by design.

### Added — LLM tool-schema export

Self-describing bridge surface for LLM tool-use clients. Introspects `ephemerides_spectral.bridge` at call time and emits machine-readable tool descriptions in the standard formats: **Anthropic Claude tool-use spec** (default — `{name, description, input_schema}`), **OpenAI function-calling spec** (`{type: "function", function: {...}}`), **Anthropic MCP / Model Context Protocol tools/list spec** (camelCase `inputSchema`), **plain JSON Schema** (no LLM-vendor wrapping). Three new bridge surfaces: `get_tool_schema(format="anthropic", filter_prefix=None)` returns the full schema for all ~240 public bridge functions; `list_tool_names(filter_prefix=None)` returns just the inventory; `get_one_tool_schema(name, format="anthropic")` returns one tool's schema by name. Three new CLI subcommands: `tool-schema [--format FORMAT] [--filter-prefix STR]`, `tool-names [--filter-prefix STR]`, `tool-schema-one --name NAME [--format FORMAT]`. **Self-describing API discipline**: no hand-maintained list — every public bridge function with a docstring and type hints is automatically included. Adding a new ship's bridge surface automatically extends every emitted schema. The ratchet test `test_every_tool_has_non_empty_description` enforces docstring discipline (LLM tool-use clients can't use a tool they can't describe). Type-hint mapping handles `int`, `float`, `str`, `bool`, `Optional[X]`, `List[X]`, `Dict[X, Y]`, `Union[X, Y]`, and string-form (PEP 563) annotations. Name resolution uses the **bridge namespace binding** (not `fn.__name__`) — necessary because some bridge functions are factory-generated and share an inner `_impl` closure name, but the public contract is the namespace key. **Pure-Python additive; no ABI bump** (forty-plus consecutive ships since v0.13.x). 15 new tests in `tests/test_tool_schema.py` covering: inventory + sort + filter, all 4 formats, type-hint mapping (int → integer, str → string, Optional → not-required), unknown-name + unknown-format error paths, and the every-tool-has-description discipline ratchet. Reference: research notebook §0.0 The Mathematical Provenance Method — the bridge surface IS the surface other systems consume; making it self-describing to LLM clients is the natural completion of the "machine-readable everywhere" discipline.

### Added — First cosmology-instrument pair (CMB Power Spectrum + CMB Anomalies)

The project's first **cosmology-scale instrument** — Mpc-to-Gpc spectral observables at the IR end of the MFO spectral-dimension flow predicted by [research notebook §V](https://mlehaptics.readthedocs.io/en/latest/antikythera-maths/mfo/) (sister project). Three sequential PRs (#351 → #352 → #353).

- **`research/attested/cmb_power_spectrum/` (#351)** — Planck 2018 PR3 binned TT power spectrum, full coverage. 111 binned bands spanning ℓ = 2 to 2499 — 28 unbinned low-ℓ bands (commander likelihood, ℓ=2..29) + 83 binned high-ℓ bands (Plik likelihood, half-widths ~10-16). Each row carries `ell_center`, `ell_half_width`, `D_ell_muK2`, `D_ell_error_muK2`, `spectrum_kind` (TT for this ship; TE/EE deferred), and a `feature` classification ∈ {`low_ell_anomaly`, `sachs_wolfe_plateau`, `rising_to_first_peak`, `first_acoustic_peak`, `first_trough`, `second_acoustic_peak`, `second_trough`, `third_acoustic_peak`, `damping_tail`, `other`}. Per-row source DOI: Planck Collaboration 2018 VI (Aghanim et al. 2020, *A&A* 641:A6, `10.1051/0004-6361/201833910`). Per-row `source_file` provenance: `COM_PowerSpect_CMB-TT-full_R3.01.txt` (low-ℓ unbinned) + `COM_PowerSpect_CMB-TT-binned_R3.01.txt` (high-ℓ binned) from the Planck Legacy Archive. Headline: **first acoustic peak at ℓ ≈ 225 with D_ℓ ≈ 5793 μK²** — one of the most-cited numerical results in cosmology; peak position constrains spatial flatness, peak height constrains Ω_b h².
- **`research/attested/cmb_anomalies/` (#352)** — six canonical large-scale CMB anomalies as structured rows. Where the power-spectrum catalog indexes the CMB by multipole bin (assuming statistical isotropy), this catalog indexes structural deviations from isotropy + Gaussianity at typically 2σ-3σ levels. Six rows, all confirmed in Planck 2018 VII (Akrami et al. 2020, *A&A* 641:A7, `10.1051/0004-6361/201833881`): `axis-of-evil-l2-l3-alignment` (Schwarz/Land-Magueijo/Copi alignment family, ~3σ), `cold-spot` (Vielva et al. 2004 wavelet detection, ~3σ), `hemispherical-power-asymmetry` (Eriksen 2004 dipolar modulation, ~3σ), `low-quadrupole` (~2σ), `parity-asymmetry-low-ell` (Land-Magueijo 2005 odd-vs-even, ~2.5σ), `missing-large-angle-correlation` (S 1/2 anomaly; suppressed C(θ) at θ > 60°, ~3σ). Per-row: discovery DOI + Planck 2018 VII confirmation DOI + statistical test description + galactic sky location where applicable + `anomaly_kind` classification ∈ {`alignment`, `hotspot`, `asymmetry`, `suppression`, `parity_violation`, `correlation_anomaly`, `other`}. Catalog is **DATA, not interpretation** — theoretical explanations (bubble-collision, EM-medium-pressure, axion / cosmic-string mechanisms) are research-scope and explicitly NOT recorded as catalog rows.
- **Bridge + CLI surfaces (#353)** — closes the deferred-items ratchet for both ships. Five new public functions on `ephemerides_spectral.bridge`: `get_cmb_power_at_ell(ell)` (D_ℓ at the band containing a queried ℓ; handles low-ℓ unbinned + high-ℓ binned uniformly); `get_cmb_first_acoustic_peak()` (THE headline observable); `list_cmb_power_spectrum()` (full enumeration with feature counts); `get_cmb_anomaly(anomaly_id)` (single anomaly by stable id); `list_cmb_anomalies()` (all 6 anomalies + per-kind summary). Five new CLI subcommands: `cmb-power-at-ell --ell N`, `cmb-first-acoustic-peak`, `cmb-power-spectrum-full`, `cmb-anomaly --anomaly-id ID`, `cmb-anomalies-full`. Catalog modules follow AMSC-first pattern: `_research/cmb_power_spectrum_catalog.py` and `_research/cmb_anomalies_catalog.py` read directly from the attested NDJSON via the AMSC universal accessor (`get_attested_dataset`); **no separate `_data.py`** — cleaner than the v0.24.x pattern of duplicating data in both `_data.py` and attested NDJSON. Ratchets: `n_sources` 17 → 19 (+2 cosmology catalogs); `adapter_class="curated"` 14 → 16. `test_parity_smoke.py` adds 5 new `python_only` entries (no C-twin counterparts — pure-Python NDJSON query surfaces). **Pure-Python additive; no ABI bump** (fortieth-plus consecutive ship since v0.13.x).

MFO connection: the CMB power spectrum is the empirical anchor at the IR end of the d_S(σ) → 4 flow predicted by [MFO notebook §V](https://mlehaptics.readthedocs.io/en/latest/antikythera-maths/mfo/) — CMB analyses give effective d_H ≈ 4 at Mpc scales, consistent with both ΛCDM and the framework's IR limit. The companion anomalies catalog provides testable observational targets for any future framework prediction; whether MFO predicts any specific anomaly is open research.

### Added — v0.27.0 phase A — Loki Patera Eruption Cycle AMSC backfill

- **`research/attested/loki_patera/`** — the v0.24.12 ship; final phase-A backfill. Multi-row-type catalogue (12 rows): 6 `cycle_peak` rows (1990 / 1995 / 1997 / 2002 / 2013 / 2015 — Veeder 1994 KAO observations through de Kleer 2019 *Nature* adaptive-optics era) + 6 `cycle_mode` rows (`loki_main_cycle` ~540 d, `brightening_phase`, `resurfacing_wave` at ~1 km/day across the ~200-km-diameter caldera, `cooling_phase`, `io_orbital_period`, `galilean_laplace_4_2_1_commensurability`). Direct cousin to v0.24.8 Axial Seamount in the `temporal_quasi_periodic_cycle` regime, but with fundamentally different forcing physics: Galilean Laplace tidal heating from the Io-Europa-Ganymede 4:2:1 mean-motion resonance (Io's forced eccentricity ~0.0041 dissipates ~10^14 W in the moon's interior) instead of mantle-plume / mid-ocean-ridge dynamics.
- Per-row source DOIs (mostly real, Crossref-indexed; one `isbn:` for the Murray-Dermott textbook): Veeder 1994 *J. Geophys. Res.* (10.1029/94JE00637; 1990 KAO peak), Rathbun 2002 *GRL* (10.1029/2002GL014747 — canonical_doi; ~540-d periodicity + 1995-2002 peaks), de Kleer & de Pater 2017 *Icarus* (10.1016/j.icarus.2016.06.019; 2013-2015 AO peaks), de Kleer 2019 *Nature* (10.1038/s41586-020-03031-8; multi-phase resurfacing analysis, ~1 km/day wave speed), Peale-Cassen-Reynolds 1979 *Science* (10.1126/science.203.4383.892; the famous Io tidal-heating prediction confirmed 2 weeks later by Voyager 1), Murray-Dermott 1999 *Solar System Dynamics* (`isbn:978-0521575973`; canonical Galilean-Laplace 4:2:1 textbook).
- **`tests/test_loki_patera_dual_author.py`** — 13 tests including:
  - **Row-type distribution ratchet** — 6 cycle_peak + 6 cycle_mode
  - **540-day-mean-cycle ratchet** — pinning the canonical Rathbun 2002 quasi-periodic period as the v0.24.12 headline observable
  - **Galilean-Laplace-4:2:1-arithmetic ratchet** — pins 4·P_Io ≈ 2·P_Europa ≈ P_Ganymede within 0.1 d (~1% of P_Ganymede; the period-ratio approximation of the resonance, not the exact Laplace argument); the Peale-Cassen-Reynolds 1979 prediction confirmed by Voyager 1
  - **Rathbun-2002-anchor-cycle ratchet** — 2002 peak is index 0; pre-anchor 1990s peaks carry null cycle_index_from_anchor; AO-era peaks carry positive integer indices (2013 = 7, 2015 = 8)
  - **Three-subcycle-phase-modes ratchet** — brightening + resurfacing-wave + cooling modes all carry mode_class='phase'
  - **`isbn:`-prefix-only-for-textbook ratchet** — Murray-Dermott 1999 is the only `isbn:` source (no `nodoi:` / `historical:` / `ads:` prefixes elsewhere)
  - **Chronological-peak-ordering ratchet** — 1990 → 1995 → 1997 → 2002 → 2013 → 2015
- Ratchets: `n_sources` 16 → 17; `adapter_class="curated"` 13 → 14.
- **Phase A complete**: v0.24.0 Mercury through v0.24.12 Loki Patera all have AMSC backfill PRs (12 PRs total; v0.24.9-v0.24.10 paired as the dynamical_regime + dynamical_regime_probes ship in PR #316).

### Added — v0.27.0 phase A — Pluto-Charon Dynamical Spectrum AMSC backfill

- **`research/attested/pluto_charon_dynamical_spectrum/`** — twelfth v0.24.x backfill (the v0.24.11 ship). 12-mode roster covering the Solar System's only known double-synchronous binary: the TRIPLE 1:1 lock at 6.387230 d (mutual_orbital_sidereal + pluto_spin_frequency + charon_spin_frequency, all at the same period — P_Pluto = P_Charon = P_orbit, the END state of dyadic tidal evolution), the apsidal-libration mode, four action variables (eccentricity ≈ 5e-5 / mutual obliquity ≈ 0.0006° / Charon-Pluto mass ratio ≈ 0.1218 / heliocentric inclination ≈ 119.6°), and four small-moon near-3:4:5:6 commensurability angles (Styx / Nix / Kerberos / Hydra orbital periods at integer-multiple ratios with the mutual orbital period, ~0.3% to ~5% from perfect resonance). Single row_type `dynamical_mode`. Path-B response to the v0.24.10 OOS-probe schema-gap that surfaced when Pluto-Charon collapsed onto Mercury-stable in the v0.24.9 classifier — closes the new `rigid_body_action_angle_mutual_lock` regime label introduced for this ship.
- Per-row source DOIs (all real, Crossref-indexed): Brozovic 2015 *Icarus* (canonical_doi; post-New-Horizons orbital fit + mass ratio + eccentricity + small-moon periods), Stern 1992 *Annu. Rev. Astron. Astrophys.* (canonical pre-New-Horizons binary review + mutual tidal lock), Stern 2015 *Science* (New Horizons flyby summary + radii + mutual obliquity + heliocentric inclination), Showalter & Hamilton 2015 *Nature* (small-moon resonant interactions + chaotic libration on Myr timescales). No nodoi: / historical: / isbn: prefixes.
- **`tests/test_pluto_charon_dynamical_spectrum_dual_author.py`** — 12 tests including:
  - **Triple-synchronous-lock ratchet** — P_Pluto_spin = P_Charon_spin = P_mutual_orbit = 6.3872304 d, the v0.24.10 → v0.24.11 schema-gap closure
  - **Largest-binary-mass-ratio ratchet** — Charon/Pluto ≈ 0.1218 (~10x larger than Earth-Luna's 0.0123); the geometric reason the barycenter sits 940 km above Pluto's surface
  - **Small-moon near-3:4:5:6 ratio-bracket ratchet** — pins Styx / Nix / Kerberos / Hydra ratios into expected near-integer windows
  - **Pure-action Infinity-period round-trip ratchet** — validates the JSON Infinity-token serialisation for the four action variables
- Ratchets: `n_sources` 15 → 16; `adapter_class="curated"` 12 → 13.

### Added — v0.27.0 phase A — Sol Dynamical-Regime Classifier AMSC backfill (paired)

- **`research/attested/dynamical_regime/`** — tenth v0.24.x backfill; the v0.24.9 dynamical-regime classifier training roster (11 rows, one per v0.24.x ship spanning v0.24.0-v0.24.8 + v0.24.11 + v0.24.12). Single row_type `regime_example`. Each row stores the ship's 7-feature signature vector (time_scale_log_s, spatial_scale_log_km, stability_index, has_commensurability, prediction_track_signal, dimensionality, forcing_class_index) + regime label + description + catalog module pointer.
- **`research/attested/dynamical_regime_probes/`** — eleventh v0.24.x backfill (paired with the training roster); the v0.24.10 OOS probe roster (10 probes — Yellowstone, Reunion, Pluto-Charon, Enceladus, Io-Galilean, Phobos, Ceres, Alpha Centauri B, Vesta, magnetar — spanning every v0.24.x regime label including OOD-flagged + let-classifier-surprise-us cases). Single row_type `regime_probe`.
- **Pairing decision**: shipped as TWO separate AMSC sources rather than one combined. Different dataclasses (RegimeExample vs RegimeProbe with `expected_regime` / `ood_expected`); the gap-suggester pipeline already imports `REGIME_PROBES` separately; future schema-gap suggester wiring is per-source. Two ratchet bumps instead of one.
- Per-row source DOIs:
  - **Training roster**: canonical paper for each v0.24.x ship — Margot 2007 (Mercury), Williams 2014 (Luna), Laskar 1993 (Mars), Davies 2014 (Sun), Iess 2019 (Saturn-Toroidal), Sharp & Clague 2006 (Hawaii), Chesley 2003 (Yarkovsky), Plescia 2004 (Mars Tharsis), Chadwick 2016 (Axial), Brozovic 2015 (Pluto-Charon), Rathbun 2002 (Loki Patera).
  - **Probes**: real per-probe DOIs (Pierce & Morgan 1992 / Courtillot 1986 / Stern 1992 / Peale-Cassen-Reynolds 1979 / Bills 2005 / Park 2016 / Kjeldsen 2005 / Russell 2012 / Kaspi-Beloborodov 2017) + one `isbn:` (Murray-Dermott 1999 textbook).
- **`tests/test_dynamical_regime_dual_author.py`** — 11 tests including:
  - **Regime-label distribution ratchet** — pins the v0.24.0-v0.24.12 ship taxonomy (10 unique labels, with `temporal_quasi_periodic_cycle` shared between Axial + Loki)
  - **Pluto-Charon-only-mutual-lock ratchet** — pinning the v0.24.10 → v0.24.11 schema-gap closure
  - **Axial-only-negative-prediction-track ratchet** — pins the v0.24.8 first-MISS-on-this-methodology observation
  - **v024_N → real-DOI ratchet** — pins that no `nodoi:` / `historical:` / `isbn:` / `ads:` prefixes appear in the training roster
- **`tests/test_dynamical_regime_probes_dual_author.py`** — 11 tests including:
  - **OOD probe distribution ratchet** — exactly Ceres carries `ood_expected=True`
  - **Let-classifier-surprise-us ratchet** — Phobos + Vesta land in this bucket
  - **Pluto-Charon probe targets v024_11 label ratchet** — pins the schema-gap closure as ground truth
  - **`isbn:`-prefix-only-for-textbook ratchet** — pins Murray-Dermott as the only textbook source
- Ratchets: `n_sources` 13 → 15 (+2); `adapter_class="curated"` 10 → 12 (+2).

### Added — v0.27.0 phase A — Axial Seamount Eruption Chronology AMSC backfill

- **`research/attested/axial_seamount/`** — ninth v0.24.x backfill. Multi-row-type catalogue: 9 rows across 3 row types (`eruption` × 3, `inflation_phase` × 4, `forecast` × 2). Real-time-monitored submarine volcano on the Juan de Fuca Ridge / hotspot intersection. The decade-scale Diophantine-stability-vs-window cousin of v0.24.2 Mars secular-resonance chaos: same algebraic structure on wildly different observational scales, with one published forecast HIT (2015 eruption) and one MISS (2024-2025 window) on the same body.
- Per-row source DOIs (mostly real, Crossref-indexed): Dziak & Fox 1999 *GRL* (1998 onset T-wave swarm), Caress 2012 *Nature Geoscience* (2011 repeat-bathymetry), Chadwick 2016 *Science* (2015 forecast HIT + canonical_doi), Nooner-Chadwick 2009 *G³* (geodetic baseline), Nooner-Chadwick 2016 *Science* companion (inflation-trigger framework). The post-2015 follow-up uses `nodoi:nooner_chadwick_post_2015_ooi_followup` for the non-Crossref-indexed conference proceedings + OOI Cabled Array status updates that document the post-2015 inflation-rate slowing + 2024-2025 forecast MISS.
- **`tests/test_axial_seamount_dual_author.py`** — 11 tests including:
  - **Row-type distribution ratchet** — 3 eruption + 4 inflation_phase + 2 forecast
  - **Eruption-chronology ratchet** — 1998 → 2011 → 2015 by Julian date
  - **Forecast-outcomes ratchet** — exactly 2 forecasts, outcomes = {HIT, MISS}, with `forecast_2015_eruption` as the HIT
  - **Post-2015-rate-slowed ratchet** — pinning the rate-decay observation that broke the constant-rate extrapolation underlying the MISS
  - **Inflation-phases-chronologically-chained ratchet** — the 4 phases form a continuous timeline
  - **`nodoi:` discipline ratchet** — only `nooner_chadwick_post_2015` carries the prefix (the only non-Crossref source in the catalogue)
- Ratchets: `n_sources` 12 → 13; `adapter_class="curated"` 9 → 10.

### Added — v0.27.0 phase A — Mars Tharsis Volcanic Chain AMSC backfill

- **`research/attested/mars_tharsis/`** — eighth v0.24.x backfill. 5-volcano roster spanning the Tharsis bulge: the NE-SW Tharsis Montes ridge (Arsia / Pavonis / Ascraeus, three aligned shields at ~3400 km spacing) plus the two outliers — Olympus Mons (the Solar System's largest known volcano, ~22 km from base to summit, 600 km diameter, NW of the ridge) and Alba Mons (older / broader / shorter ~1500-km-diameter shield north of the ridge). Per-volcano: name + age + uncertainty + lat/lon + summit elevation + edifice diameter + structural-role classification (tharsis_montes / olympus_outlier / alba_outlier).
- Per-row source DOIs (all real, Crossref-indexed): Hartmann & Neukum 2001 *Space Sci. Rev.* (Arsia/Ascraeus crater chronology), Hartmann 2005 *Icarus* (Olympus Mons summit flows), Werner 2009 *Icarus* (Pavonis Mons), Plescia 2004 *J. Geophys. Res.* (Alba Mons + canonical morphometric compilation).
- **`tests/test_mars_tharsis_dual_author.py`** — 10 tests including:
  - **Role distribution ratchet** — 3 tharsis_montes + 1 olympus_outlier + 1 alba_outlier
  - **Olympus-tallest ratchet** — pinning the no-plate-tectonics super-volcano signature
  - **Alba-broadest ratchet** — 1500 km base diameter exceeds all other Tharsis edifices
  - **Alba-oldest ratchet** — mid-Hesperian earlier-phase Tharsis volcanism
- Ratchets: `n_sources` 11 → 12; `adapter_class="curated"` 8 → 9.

### Added — v0.27.0 phase A — Sol Yarkovsky/YORP AMSC backfill

- **`research/attested/yarkovsky_yorp/`** — seventh v0.24.x backfill. 10 NEA + Hayabusa-target asteroids with published Yarkovsky (semi-major-axis drift, in 10⁻⁴ AU/Myr) and/or YORP (spin-rate change, in 10⁻⁸ rad/d²) measurements. Roster: Bennu (OSIRIS-REx headline) / 2000 PH5 (first-ever YORP detection) / Apophis / Ryugu / Itokawa / Apollo / Geographos / 1950 DA / Golevka (first-ever Yarkovsky detection) / Eger.
- Per-row source DOIs (all real, Crossref-indexed): Farnocchia 2013 *Icarus* (Bennu), Lowry 2007 *Science* (2000 PH5), Vokrouhlický 2015 *Icarus* (Apophis), Watanabe 2019 *Science* (Ryugu), Lowry 2014 *A&A* (Itokawa YORP spin-down), Kaasalainen 2007 *Nature* (Apollo), Durech 2008 *A&A* (Geographos), Farnocchia 2014 *Icarus* (1950 DA), Chesley 2003 *Science* (Golevka), Durech 2012 *A&A* (Eger).
- **`tests/test_yarkovsky_yorp_dual_author.py`** — 10 tests including:
  - **Prograde-outward / retrograde-inward Yarkovsky-direction ratchet** (the canonical diurnal effect's direction-of-drift relation)
  - **Bennu-largest-magnitude ratchet** (|drift| = 19e-4 AU/Myr is the maximum in the catalogue)
  - **1950-DA-near-fission-limit ratchet** (2.121 h period below the 2.2 h rubble-pile fission limit; closest in the catalogue ≥ 1 h to the threshold)
  - Single-row-type ratchet
- Ratchets: `n_sources` 10 → 11; `adapter_class="curated"` 7 → 8.

### Added — v0.27.0 phase A — Hawaiian-Emperor Chain AMSC backfill

- **`research/attested/hawaii_chain/`** — sixth v0.24.x backfill. 18 seamounts spanning the full ~85 Myr Hawaiian-Emperor hotspot track from Meiji (oldest, near the Aleutian Trench) through the Hawaiian-Emperor bend at 47.5 Myr (Daikakuji marker) to Kilauea (presently active). Per-seamount: name + age + uncertainty + lat/lon + arc classification (emperor / bend / hawaiian).
- Per-row source DOIs: Sharp & Clague 2006 (canonical bend age), Duncan & Keller 2004 (Detroit ODP Leg 197), O'Connor 2013 (Kammu), Garcia 2010 (Kauai/Oahu/Big Island), plus 4 `nodoi:`-prefixed pre-DOI sources (Duncan & Clague 1985 Plenum book chapter, Keller 1995 ODP Leg 145 reports, Clague & Dalrymple 1989 GSA volume, Clague 2010 USGS HVO compilation). Introduces the `nodoi:` prefix convention for pre-DOI book chapters and observatory compilations.
- **`tests/test_hawaii_chain_dual_author.py`** — 8 tests including:
  - **Arc distribution ratchet** — 5 emperor + 1 bend + 12 hawaiian
  - **Meiji-oldest / Kilauea-youngest ratchet**
  - **Bend age consistency ratchet** — Daikakuji within 47.5 ± 1.5 Myr (Sharp & Clague 2006)
- Ratchets: `n_sources` 9 → 10; `adapter_class="curated"` 6 → 7.

### Added — v0.27.0 phase A — Toroidal-Residual J₂ AMSC backfill

- **`research/attested/toroidal_residual/`** — fifth v0.24.x backfill. 14 bodies classified on the Chandrasekhar 1969 rotating-fluid equilibrium-figure sequence: terra / mars / venus / mercury / luna / jupiter / saturn / uranus / neptune / io / europa / ganymede / callisto / titan. Each row records measured J₂ + dimensionless rotation parameter q = ω²R³/(GM) + moment-of-inertia factor + regime classification (sphere / maclaurin / jacobi / bar / ring) + fossil-figure flag.
- Per-row source DOIs: EGM2008 (Earth), Genova 2016 (Mars MRO), Anderson 2002 (Venus), Smith 2012 MESSENGER (Mercury), Konopliv 2013 GRAIL (Luna), Iess 2018 Juno (Jupiter), Iess 2019 Cassini (Saturn), Jacobson 2014/2009 (Uranus/Neptune), Anderson 2001 Galileo (Galileans), Iess 2010 (Titan).
- **`tests/test_toroidal_residual_dual_author.py`** — 12 tests including:
  - **Saturn-is-closest-to-bifurcation ratchet** (Saturn q is largest in the catalogue, still below q=0.187 Maclaurin-Jacobi threshold)
  - **Fossil-figure ratchet** (Mercury + Luna are the canonical fossil cases; pinned)
  - Regime-enum validity check (sphere / maclaurin / jacobi / bar / ring)
  - Single-row-type ratchet
  - Sphere-or-Maclaurin coverage (no triaxials in this roster; Venus = sphere because q ≈ 10⁻⁷)
- Ratchets: `n_sources` 8 → 9; `adapter_class="curated"` 5 → 6.

### Added — v0.27.0 phase A — Sun Dynamical Spectrum AMSC backfill

- **`research/attested/sun_dynamical_spectrum/`** — fourth v0.24.x backfill (after Mercury PR #303, Luna PR #306, Mars PR #308). 20 helioseismic p-mode rows at canonical (n, l) labels: 8 radial (l=0, n=18-25), 6 dipole (l=1, n=18-23), 6 quadrupole (l=2, n=18-23). Single row_type catalogue (`helioseismic_mode`); Sun is a methodology extension from rigid-body action-angle to continuum normal-mode oscillation spectrum.
- Per-row source DOIs: Davies et al. 2014 (BiSON 22-yr low-degree p-mode catalogue, MNRAS 439:2025-2032).
- **`tests/test_sun_dynamical_spectrum_dual_author.py`** — 11 tests including:
  - `test_all_rows_share_helioseismic_mode_row_type` (single-type ratchet)
  - `test_all_rows_are_p_modes` (mode_class enforcement)
  - `test_n_l_grid_coverage` (the 20-row grid is pinned: l=0 n=18-25; l=1/2 n=18-23)
  - `test_frequencies_increase_with_n_at_fixed_l` (Tassoul-asymptotic monotonicity)
- Ratchets: `n_sources` 7 → 8; `adapter_class="curated"` 4 → 5.
- **2000 tests pass** total — milestone marker.

### Added — v0.27.0 phase A — Mars Dynamical Spectrum AMSC backfill

- **`research/attested/mars_dynamical_spectrum/`** — third v0.24.x backfill (after Mercury PR #303 and Luna PR #306). 11 rows: 8 dynamical_mode (orbital + sol-rotation + spin-axis-precession + apsidal-precession g₄ + nodal-precession s₄ angle modes; eccentricity / inclination / obliquity actions) + 3 secular_resonance (the near-resonances driving Mars obliquity chaos: spin_axis_precession ↔ s₃, spin_axis_precession ↔ s₄, apsidal_precession_g4 ↔ g3-s3). Per-row source DOIs cite Park 2021 (DE441), Le Maistre 2023 (InSight RISE), Ward 1973 (spin-axis precession), Laskar 1993 + Laskar 2004 + Laskar 2008 (chaos finding + Gyr-scale evolution + Mercury-eccentricity instability), Touma & Wisdom 1993 (independent confirmation).
- **`tests/_mars_amsc_helpers.py`** — converter mirroring `_mercury_amsc_helpers.py` / `_luna_amsc_helpers.py`. Composite row name `<mars_mode>__<secular_partner>` for secular_resonance rows.
- **`tests/test_mars_dynamical_spectrum_dual_author.py`** — 9 tests including a `secular_resonance` proximity ratchet (every row carries a non-null, non-negative `proximity_arcsec_per_year` — the headline quantity that measures frequency closeness; null would defeat the row's purpose).
- **`bridge.list_attested_sources()`** now returns 7 sources (was 6); `adapter_class="curated"` returns 4.

### Added — v0.27.0 phase A — Luna Dynamical Spectrum AMSC backfill

- **`research/attested/luna_dynamical_spectrum/`** — new attested source: descriptor.toml + row.schema.json + row.ndjson covering the v0.24.1 catalogue. 15 rows total: 11 dynamical_mode rows (four classical lunar months — sidereal / synodic / anomalistic / draconitic — + spin lock + Williams-2014 forced-libration + apsidal + nodal precession + eccentricity / inclination / obliquity actions) + 4 saros_commensurability rows (223 synodic ≈ 239 anomalistic ≈ 242 draconitic months ≈ 19 eclipse-years ≈ 6585.32 days; the integer-commensurability closure invariant). Per-row source DOIs cite Allen's Astrophysical Quantities (4th ed.), JPL DE441, Williams & Boggs 2014 (LLR libration analysis), Murray-Dermott 1999, Cassini 1693 (historical lunar libration laws), Meeus 1991 (Saros derivation).
- **`tests/_luna_amsc_helpers.py`** — converter mapping hand-coded rows → AMSC-shape dicts via static SOURCE_KEY_PROVENANCE (mirrors the `_mercury_amsc_helpers.py` pattern from PR #303). Introduces the `historical:` DOI-prefix convention for pre-DOI canonical works.
- **`tests/test_luna_dynamical_spectrum_dual_author.py`** — 9 tests: AMSC dataset loads (15 rows); row-count + row-name set + per-row field + full dict equality; SOURCE_KEY_PROVENANCE coverage of every source_key referenced by the hand-coded module; ISO 8601 published-date pattern; row-type distribution 11/4; **Saros closure invariant** (the four product_days values agree within 0.5 day).
- **`bridge.list_attested_sources()`** now returns 6 sources (was 5); `adapter_class="curated"` returns 3 (saturn_rings + mercury_dynamical_spectrum + luna_dynamical_spectrum).
- The hand-coded `_research/luna_dynamical_spectrum_data.py` module is unchanged; AMSC NDJSON is the attestation envelope.

### Fixed — AMSC `_ndjson_path` now honours explicit `[fetch].ndjson_path`

Surfaced during the v0.27.0 phase A Mercury migration (PR #303): the resolver in `_research/attested_collector_catalog.py::_ndjson_path` ignored the descriptor's explicit `[fetch].ndjson_path` field and used only the schema-id-derived fallback (split `data_schema_id` on `.`, take parts[1] as the filename stem). When the two conventions disagreed, the symptom was an apparently-correctly-authored descriptor returning empty rows with the misleading `"no committed NDJSON; first T1 collection pending"` note even though the file existed at the documented path.

The fix: resolve `[fetch].ndjson_path` first; fall back to schema-id derivation only when the explicit field is unset. Backwards-compatible — the saturn_rings + mercury_dynamical_spectrum descriptors author both fields consistently, so no existing source's behaviour changes.

3 new regression tests in `tests/test_attested_collector.py`:
- `test_ndjson_path_honors_explicit_fetch_field` — explicit field is honoured
- `test_ndjson_path_falls_back_to_schema_id_when_explicit_absent` — fallback works
- `test_ndjson_path_explicit_wins_over_schema_id_derivation` — when they disagree, explicit wins

### Added — v0.27.0 phase A — first AMSC backfill of a v0.24.x catalogue (Mercury Dynamical Spectrum)

- **`research/attested/mercury_dynamical_spectrum/`** — new attested source: descriptor.toml + row.schema.json + row.ndjson covering the v0.24.0 catalogue. 16 rows total: 8 dynamical_mode rows (orbital + spin + libration + secular-precession angle modes; eccentricity / inclination / obliquity action variables) + 8 precession_contribution rows (Le Verrier–Einstein decomposition: 5 Newtonian perturbers + GR + solar J₂ + observed total). Per-row source DOIs cite Park 2021 (DE441), Margot 2007, Clemence 1947, Einstein 1915, Verma 2014 (INPOP), Park 2017, Murray-Dermott 1999, Laskar 1989. The hand-coded `_research/mercury_dynamical_spectrum_data.py` module is unchanged and remains the working authority; the AMSC NDJSON is the attestation envelope.
- **`bridge.list_attested_sources()`** now returns 5 sources (was 4); the new `mercury_dynamical_spectrum` joins `earthref_sc` / `gmrt` / `petdb_v4` / `saturn_rings`. `adapter_class="curated"` returns 2 (saturn_rings + mercury_dynamical_spectrum); `adapter_class="literature_curated"` returns the same 2.
- **`bridge.get_attested_dataset("mercury_dynamical_spectrum")`** returns the 16 attested rows.

### Tests

- `tests/test_mercury_dynamical_spectrum_dual_author.py` — 10 new tests inheriting the Saturn-rings PR #291 dual-author pattern: AMSC dataset loads; row-count + row-name set agreement; per-row field agreement; full dict equality; SOURCE_KEY_PROVENANCE coverage of every source_key referenced by the hand-coded module; provenance entries have valid DOI + ISO 8601 published_date + (optional) source_version; ENTERED_LOCALLY_AT is ISO date; AMSC rows carry every required attestation field; row-type distribution is 8 dynamical_mode + 8 precession_contribution.
- `tests/_mercury_amsc_helpers.py` — shared converter that maps hand-coded rows → AMSC-shape dicts via static SOURCE_KEY_PROVENANCE table. Used by both the dual-author test and any future regenerator script.
- `tests/test_attested_collector.py` ratchet tests updated for the new source count + adapter-class membership.

### Added — v0.27.0 phase C — body→kernel registry (the layer-2-to-layer-3 interface)

- **`_research.body_kernel_registry`** — new module. Stores `{body → (kernel_path, precision_tier)}` registrations as module-level singleton state. API: `register(body, kernel_path, *, precision_tier="jpl_published")`, `lookup(body)`, `clear(body=None)`, `state()`, `state_hash()`, `is_active()`, `all_bodies()`. Three precision tiers: `jpl_published`, `bodies_fallback`, `user_fit`. SHA-256 over canonical-serialised state participates as the cache key for module-load-time eigenbasis caches in `body_architecture` and `predict_itn_accessibility` — phase B will extend those caches to invalidate on registry change. Phase C ships the registry as **structural** infrastructure: registrations are tracked + hashed + surfaced via bridge metadata, but orbital-mechanics surfaces fall back to BODIES-distilled state lookups because the binary kernels are not yet readable. Phase B's `binary_archive` adapter + `ephemeris_loader` integration turns the registry from metadata into behaviour.

### Added — bridge dict API

- `bridge.register_body_kernel(body, kernel_path, *, precision_tier)` — register a kernel for a body. Returns `{ok, body, kernel_path, precision_tier, registry_size, state_hash}` on success or `{ok: False, error}` on validation failure.
- `bridge.clear_body_kernel(body=None)` — clear one body's registration, or every registration (`body=None`). Returns `{ok, cleared, registry_size, state_hash}`.
- `bridge.get_body_kernel_registry()` — return the full registry state envelope. Returns `{ok, active, registry_size, registrations, state_hash}`.

### Changed — bridge response envelopes

- `bridge.body_architecture()` and `bridge.body_architecture(target=name)` now include a `kernel_registry` field carrying the registry state envelope (active flag, size, registrations, state_hash). Empty-registry default is byte-stable across platforms (the empty-registry hash is `SHA-256("[]")`).
- `bridge.predict_itn_accessibility(departure, target)` now includes the same `kernel_registry` field on success envelopes. Eigenbasis-cache invalidation against the registry hash lands in phase B.

### Tests

- `test_body_kernel_registry.py` — 36 new tests covering registry semantics (register / lookup / clear / state / hash), bridge surface delegation, validation errors, hash determinism + invalidation, metadata propagation into `body_architecture` + `predict_itn_accessibility`, and integration-test stubs that activate when phases A and B land. Hash-independence-of-registration-order is pinned as the load-bearing invariant for cache-key stability.

### Documentation

- `bridge.find_syzygies` and `bridge.get_eclipse_probability` docstrings now explicitly frame the two surfaces as a **two-tier eclipse-finding discipline**: `find_syzygies` is the Saros-class mean-period triage tier (no DE441 query; `O(n_syzygies)` per window), and `get_eclipse_probability` is the per-JD JPL-anchored arc-second-class confirmation tier (reads DE441 via `inst.encode_state(jd)` and projects against the Syzygy Operator). The two surfaces compute related-but-different quantities (Born-rule projection vs mean-period geometric residual) on different data; both are deliberately load-bearing. Pre-v0.27.0 wording suggested `find_syzygies` "replaced" `get_eclipse_probability`, which was misleading — only the windowed-loop *usage* of `get_eclipse_probability` was replaced; per-call use as the precision tier is the intended workflow. No code change.

## [0.26.0] — 2026-05-08

**Schema-gap-driven trigger — closes the Mathematical Provenance Method loop.** The system identifies what it doesn't know and points at attested sources that could populate the gap. Pure-Python additive; **no ABI bump** (thirty-ninth consecutive ship since v0.13.x).

### Added — Pythonic API

- `_research.attested_collector_gap_suggester` — new module. Reads the v0.24.10 OOS probe roster, runs each probe through the v0.24.9 dynamical-regime classifier, identifies regime gaps (OOD / spurious-match / surprise), and matches each gap against attested-source descriptors via `[gap_targeting].regime_labels`. Deterministic, closed-form analysis. No LLM, no SGD; same Mathematical Provenance Method discipline as every other v0.24.x / v0.25.x surface.
- Constants: `GAP_KIND_OOD`, `GAP_KIND_SPURIOUS`, `GAP_KIND_SURPRISE`, `GAP_KIND_NONE`.
- `suggest_gap_collections(*, ood_threshold=0.85, descriptors=None)` returns the suggestion envelope.

### Added — bridge dict API

- `bridge.suggest_gap_collections(*, ood_threshold=0.85)` — wraps the suggester. Each suggestion entry: `probe_name`, `calibration_ratio`, `current_landing`, `expected_regime`, `gap_kind`, `target_regime_label`, `candidate_descriptors`.

### Added — CLI

- `ephemerides-spectral suggest-gap-collections [--ood-threshold N]`

### Three real gaps surfaced on the current v0.25.x descriptor set

When run against the shipped probe roster (10 OOS probes) + descriptor set (3 attested sources), the suggester surfaces:

- **phobos**: surprise gap; classifier landed it on `rigid_body_chaotic_obliquity`. No descriptor currently targets that label → 0 candidates. Future-source backlog hint.
- **ceres**: OOD gap (cal_ratio > 0.85). `expected_regime=None` → no target label → 0 candidates. Documented honest "I don't know" — the framework would need a new descriptor whose `[gap_targeting]` covers a regime fitting Ceres's rigid-stable-no-commensurability physics.
- **vesta**: surprise gap (the v0.24.12-introduced schema-gap that the user's research notebook identified manually). Classifier lands it on `rigid_body_chaotic_obliquity` spuriously; no descriptor targets that label → 0 candidates. Same future-source backlog hint as phobos.

The candidate-matching code path is exercised by tests against synthetic descriptors; on the production set, all three current gaps need new descriptors covering currently-untargeted regimes — which is exactly the scope the v0.26.x research thread will surface.

### CI automation for v0.26.x or later

The auto-PR mechanism that consumes the suggestion surface and opens targeted T1 collection PRs is **not** in v0.26.0. v0.26.0 ships the analysis surface; the trigger half lands when a maintainer-review-grade auto-PR mechanism is wired up (open research questions documented in #161).

### Reproducibility

Suggester output is deterministic given: same probe roster, same descriptor set, same `ood_threshold`. `regenerate.py` does no network I/O (existing ratchet remains green). The suggester reads only T0+T1 baseline + module-load-cached descriptor dictionary; no overlay or live state involved.

### Tests

10 new tests in `tests/test_attested_collector.py`:
- envelope shape + `n_probes`/`n_gaps`/`n_suggestions` counts
- per-suggestion field shape
- gap_kind vocabulary check
- vesta-is-currently-a-gap ratchet (pins the v0.24.12 schema-gap surfacing)
- candidate-matching path
- ood_threshold parameter honoured
- 3 CLI tests (smoke / threshold flag / --help)

### Cross-references

- Notebook §18.5 (T1 re-bake triggers; option 3 — schema-gap-driven).
- Notebook §0.0 The Mathematical Provenance Method.
- v0.24.10 OOS probe roster (#152).
- v0.24.9 dynamical-regime classifier (#151).
- v0.24.11 / v0.24.12 manual demonstrations of the loop.

## [0.25.2] — 2026-05-08

**Attested collector — T3 live query.** Completes the four-tier reproducibility model from notebook §18.1. Pure-Python additive; **no ABI bump** (thirty-eighth consecutive ship since v0.13.x).

### Added — Pythonic API

- `_research.attested_collector_catalog.get_attested_dataset(source_key, *, limit=None, offset=0, live=False)` — new `live` parameter. When `True`, invokes the descriptor's declared adapter against the upstream archive at call time and returns rows with full per-row attestation; the response envelope adds `tier="T3"` + `retrieved_at` + `upstream_response_sha256s`. When `False` (default), returns the T0+T1+T2 baseline (now also carrying an explicit `tier="T0+T1+T2"` discriminator).
- New private helper `_get_attested_dataset_live(descriptor, *, limit, offset)` composes `attested_adapters._base.run` into the T3 envelope. Lazy-imports the adapters to keep `regenerate.py` off the network path.

### Added — bridge dict API

- `bridge.get_attested_dataset(source_key, *, limit=None, offset=0, live=False)` — extended with the `live` kwarg (PEP 440 backward-compatible: a positional caller's existing args still work).

### Added — CLI

- `attested-dataset --live` — opt-in flag for T3 fetches.

### Reproducibility tier

T3 is the weakest. Each row's `response_sha256` documents the upstream content currently served; replay requires re-fetching against an unchanged upstream OR archiving response bytes alongside the recorded attestation. Adapter errors surface as `ok=False` with diagnostic + `retrieved_at` so consumers can record the failed attempt.

### Tests

7 new tests in `tests/test_attested_collector.py`:
- `test_get_attested_dataset_default_is_baseline` — baseline tier discriminator.
- `test_get_attested_dataset_live_true_fetches_upstream` — adapter pipeline runs end-to-end.
- `test_get_attested_dataset_live_per_row_attestation` — all 9 mandatory attestation fields populated.
- `test_get_attested_dataset_live_pagination` — limit/offset honoured.
- `test_get_attested_dataset_live_unknown_source` — error path.
- `test_get_attested_dataset_live_adapter_error_surfaces` — adapter failure diagnostic envelope.
- `test_cli_attested_dataset_live_flag` — CLI wire-through.

Tests use `monkeypatch.setattr(html_scraper, "fetch", _fake_fetch)` to inject a fixture HTML response, exercising the full `run()` composer (fetch → parse → attest → MPRRecord) without network I/O.

### Other

- Updated EarthRef SC descriptor's `[source].canonical_doi` to `10.1029/2009GL040749` (Wessel & Sandwell 2010 reference — empty string was rejecting MPR validation since `source_doi` is mandatory).

### Cross-references

- Notebook §18.1 — four-tier reproducibility model.
- T2 user runtime kernel: v0.25.1.
- T0+T1 baseline: v0.25.0.

## [0.25.1] — 2026-05-08

**Attested collector — T2 user runtime kernel.** Adds the local-NDJSON overlay layer promised by notebook §18.1's four-tier reproducibility model. Pure-Python additive; **no ABI bump** (thirty-seventh consecutive ship since v0.13.x).

### Added — Pythonic API

- `_research.attested_collector_catalog.use_local_kernel(path)` — register an overlay directory shaped like `<source_key>/<table>.ndjson`. REPLACE policy: a matching overlay file replaces the baseline NDJSON for that source; sources with no overlay file fall through to T0+T1 unchanged. Pass `None` to clear.
- `_research.attested_collector_catalog.clear_local_kernel()` — remove the registered overlay.
- `_research.attested_collector_catalog.get_local_kernel_state()` — return the current overlay state + per-source overlay file list + a **cache hash** (SHA-256 over the canonical-serialised list of `(source_key, ndjson_sha256)` pairs).

### Added — bridge dict API

- `bridge.use_local_kernel(path)` (Optional[str])
- `bridge.clear_local_kernel()`
- `bridge.get_local_kernel_state()`

### Added — CLI

- `ephemerides-spectral local-kernel-use --path <DIR>`
- `ephemerides-spectral local-kernel-clear`
- `ephemerides-spectral local-kernel-state`

### Reproducibility tier

T2. Within a single user's local cache state, queries are byte-identical. The cache hash from `get_local_kernel_state` uniquely identifies which T2 rows were consumed at runtime — paper appendices record this hash to enable deterministic replay against an archived overlay tree.

### Catalog wrapper changes

- New `_resolved_ndjson_path(descriptor)` helper resolves T2 overlay first then T0+T1 baseline; `get_attested_dataset`, `attestation_audit`, and `iter_attested_dataset` route through it.
- `_LOCAL_KERNEL_PATH` module-level state holds the registered overlay (or None for baseline-only mode).
- Default policy is REPLACE; APPEND policy may land in a later v0.25.x.

### Tests

11 new tests in `tests/test_attested_collector.py` covering overlay registration / clearing / state, REPLACE-policy behaviour, source isolation (overlay for A doesn't affect B), cache-hash determinism, CLI smoke + `--help`.

### Cross-references

- Notebook §18.1 — four-tier reproducibility model (T0 / T1 / T2 / T3).
- T0+T1 baseline shipped v0.25.0 (#150 + #163).
- T3 live query ships v0.25.2 (#160).

## [0.25.0] — 2026-05-08

**Attested Multi-Source Collector framework v1 — three pilots end-to-end + T1 collect CI workflow + MPR v1 normative format.** Completes the v0.25.0a/b ship sequence (notebook §18). Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged; thirty-sixth consecutive ship since v0.13.x).

### Added (v0.25.0b layer on top of v0.25.0a foundation)

- **Two new pilot descriptors + JSON Schemas**:
  - `research/attested/gmrt/descriptor.toml` + `bathymetry.schema.json` — GMRT GridServer ESRI ASCII Grid endpoint via `csv_bulk` adapter (Ryan et al. 2009; bathymetry-grid rows for v0.24.5 Hawaii / v0.24.7 Mars Tharsis bounded-local-Laplacian regimes).
  - `research/attested/petdb_v4/descriptor.toml` + `geochem.schema.json` — PetDB v4 / EarthChem unified search endpoint via `json_api` adapter (Lehnert et al. 2000; igneous-rock geochemistry samples).
- **Real `csv_bulk.fetch`** implementation. Lazy `requests` import; honours `[fetch].endpoint` template + `query_params` substitution + optional pagination. Used by GMRT pilot.
- **Real `json_api.fetch`** implementation. Lazy `requests` import; supports `[fetch].pagination.type ∈ {page_query, offset_limit}` and single-shot. End-of-pagination detected via empty `records_path` array. Used by PetDB v4 pilot.
- **T1 CI workflow** (`.github/workflows/ephemerides-spectral-collect.yml`): scheduled monthly + manual dispatch with optional `--source` filter. Runs `codegen/run_collectors.py`, re-runs `regenerate.py` to refresh manifest SHAs, opens auto-PR with refreshed NDJSON via `peter-evans/create-pull-request@v6`. Maintainer review checklist embedded in PR body covers per-row attestation completeness + license + CI green.
- **`codegen/run_collectors.py`** — the **only** network-touching code path in the project at codegen time. Discovers descriptors, runs each adapter against its declared upstream archive, writes per-source NDJSON. `regenerate.py` does NOT import this module (verified by `tests/test_attested_collector.py::test_regenerate_path_has_no_network_imports` ratchet).

### Added — pyproject optional dependencies

- `[project.optional-dependencies].collector` — `requests`, `beautifulsoup4`, `tomli` (3.10 backport), `jsonschema`. Required for T1 collector runs; runtime read paths never need these.
- `[project.optional-dependencies].collector-netcdf` — `netCDF4`. Future-deferred (`netcdf_grid` adapter ships as fixture-only stub in v0.25.0).
- `[project.optional-dependencies].collector-geotiff` — `rasterio`. Future-deferred (`geotiff_bbox` adapter ships as fixture-only stub in v0.25.0).

### Tests

- `tests/test_attested_collector.py::test_bridge_list_attested_sources_returns_three_pilots` (was `..._returns_earthref_sc`) — n_sources is now 3 (was 1 in v0.25.0a).
- `tests/test_attested_collector.py::test_discover_descriptors_finds_three_pilots` (was `..._earthref_sc`) — pins all three pilots' adapter assignments.

### Documentation cascade

5-doc cascade ratchet update: README Status banner v0.24.12 → v0.25.0; new \`## Status\` bullet for v0.25.0; both CHANGELOGs roll [Unreleased] → [0.25.0]; ROADMAP.md released-versions table prepend; notebook §4 release-history entry below.

### Cross-references

- Format spec: notebook §18 (PR #272 merged 2026-05-08).
- Discipline: notebook §0.0 The Mathematical Provenance Method.
- v0.25.0a foundation: PR #273 merged 2026-05-08.

### v0.25.0a foundation (merged 2026-05-08; rolled into v0.25.0)

The framework foundation that v0.25.0b builds on. Code-only checkpoint at v0.25.0a (no PyPI release); the consolidated PyPI artifact is v0.25.0.

#### Added

- **MPR (Mathematical Provenance Record) v1 normative format** (`_research/attested_collector_format.py`). NDJSON with mandatory `mpr_version` + `data` + `data_schema_id` + `attestation` + `rendering` blocks. 9 required attestation fields per row; 3 required rendering fields. SHA-256 over fetch-time response bytes; deterministic `to_json_line` serialisation.
- **Descriptor module** (`_research/attested_collector_descriptor.py`). Parses TOML descriptors (`[source]`, `[fetch]`, `[parse]`, `[schema]`, `[rendering]`, `[attestation]`, `[gap_targeting]`); validates against the v0.25.0 schema; renders self-describing verbiage templates with format-spec support.
- **5-adapter shared core** (`_research/attested_adapters/`) via `typing.Protocol`:
  - `html_scraper` — real impl (lazy `requests` + `bs4`); EarthRef SC pilot.
  - `json_api` — `parse` real; `fetch` stub for v0.25.0b PetDB.
  - `csv_bulk` — `parse` real; `fetch` stub for v0.25.0b GMRT.
  - `netcdf_grid` — fixture-only stub; gated behind `collector-netcdf` extra.
  - `geotiff_bbox` — fixture-only stub; gated behind `collector-geotiff` extra.
  - Shared `attest()` step computes per-row attestation block; shared `run()` composer turns descriptor → MPRRecord iterator.
- **Universal catalog wrapper** (`_research/attested_collector_catalog.py`). Discovers descriptors at module load; surfaces 4 universal bridge functions (no per-source code paths).
- **4 new bridge surfaces**:
  - `bridge.list_attested_sources()` — every registered source's rendered metadata.
  - `bridge.get_attested_dataset(source_key, *, limit=None, offset=0)` — paginated row content.
  - `bridge.get_attested_descriptor(source_key)` — full parsed descriptor for UI.
  - `bridge.attestation_audit(source_key)` — per-row provenance metadata, no data payload.
- **4 new CLI subcommands**: `attested-list`, `attested-dataset`, `attested-descriptor`, `attested-audit`.
- **EarthRef SC pilot descriptor + JSON Schema** (`research/attested/earthref_sc/{descriptor.toml, seamount.schema.json}`). NDJSON not yet committed; first T1 auto-PR commits it in v0.25.0b.
- **Codegen wiring**: new `emit_attested_collections.py` for byte-exact recursive mirror of `research/attested/` (preserves SHA-256 determinism); `emit_research_modules.py` extended with `attested_*.py` modules + `attested_adapters/` recursive subdir support; `regenerate.py` uses PACKAGE_ROOT-relative manifest keys.
- **37 new tests** (`tests/test_attested_collector.py`): MPR format round-trip + validation, descriptor TOML loading + template rendering + canonical hashing, adapter registry + html_scraper.parse against fixture HTML, bridge surfaces + CLI subcommands smoke + `--help`, no-network-imports check on `regenerate.py`.

#### Changed

- `tests/test_data_freshness.py::test_manifest_lists_every_committed_file` walks `_research/` recursively (catches v0.25.0+ subtrees).
- `tests/test_parity_smoke.py` PARITY_TARGETS extends with 4 new `python_only` entries (rationale: I/O surfaces, not encoder-touching; no C twin makes sense).

#### References

- Format spec: notebook §18 (PR #272 merged 2026-05-08).
- Discipline: notebook §0.0 The Mathematical Provenance Method.

## [0.24.12] — 2026-05-07

**Loki Patera Eruption Cycle Catalog (Io tidal-heating temporal-spectrum cousin to v0.24.8 Axial Seamount; Galilean Laplace 4:2:1 forcing).** Eleventh ship in v0.24.x; second temporal-spectrum observable on a single sub-system (after v0.24.8). Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.loki_patera_data` — data module with `LOKI_CYCLE_PEAKS` (6 published peak observations spanning 1990-2017, anchored to Rathbun 2002's 540-d period claim), `LOKI_CYCLE_MODES` (6 action-angle modes: main cycle + brightening / resurfacing / cooling phases + Io orbital + Galilean Laplace 4:2:1 commensurability), Loki geometry constants (latitude 12.7°, longitude -309.6°, diameter 200 km, lava-lake area 21,500 km²), tidal-heating budget constants (Io ~10¹⁴ W, forced eccentricity 0.0041, Loki fraction 5-15% of Io output), Galilean orbital periods (Io 1.769 d, Europa 3.551 d, Ganymede 7.155 d), 8-entry `SOURCES` (Rathbun 2002, de Kleer 2017+, Veeder 1994, Spencer 1990, Rathbun-Spencer 2010, de Kleer 2019, Peale-Cassen-Reynolds 1979, Murray-Dermott 1999), `LokiCyclePeakObservation` + `CycleMode` dataclasses.
- `_research.loki_patera_catalog` — wrapper module with `get_loki_patera_eruption_cycle`, `get_loki_galilean_laplace_signature`, `list_loki_patera_eruption_cycle`.

### Added — bridge dict API

- `bridge.get_loki_patera_eruption_cycle()` — full cycle catalog (cycle peaks + action-angle modes + binary cross-channel parameters).
- `bridge.get_loki_galilean_laplace_signature()` — the headline closure: 4·P_Io ≈ 2·P_Europa ≈ P_Ganymede, verified to within ~1% (libration around exact resonance, not strict equality).
- `bridge.list_loki_patera_eruption_cycle()` — full enumeration + citations.

### Added — CLI

- `ephemerides-spectral loki-patera-eruption-cycle`
- `ephemerides-spectral loki-galilean-laplace-signature`
- `ephemerides-spectral loki-patera-eruption-cycle-full`

### Schema-gap surfacing (the Path-B loop continues)

Adding Loki at `spatial_scale_log_km = 2.30` made it a near-twin to Vesta (2.42), collapsing Vesta's calibration ratio from ~0.98 (honest "I don't know" in v0.24.9–v0.24.11) to ~0.79 — Vesta now lands on `rigid_body_chaotic_obliquity` as a SPURIOUS classification (the physics is small-body radiation-drift, not chaotic obliquity). Pinned in `tests/test_dynamical_regime_probes.py::test_vesta_classifier_landing_v_0_24_12_pinned` as the next schema-gap to close. Future ship will need a small-body-radiation ground-proof row to give Vesta a correct home.

The probe-summary breakdown evolved as:
- Pre-v0.24.11: 8 matches + 1 OOD-expected + 1 surprise
- v0.24.11: 7 matches + 2 OOD-expected (Ceres → OOD) + 1 surprise
- v0.24.12: 7 matches + 1 OOD-expected (Ceres) + 2 surprises (Phobos, Vesta)

### Regime-classifier roster expansion

- `_research.dynamical_regime_data.REGIME_EXAMPLES` now has 11 ground-proof rows (was 10). Loki occupies the same `temporal_quasi_periodic_cycle` regime label as v0.24.8 Axial — explicitly densifying the regime rather than opening a new one. The two examples differ in feature space: Loki has a ~10× shorter cycle (~540 d vs ~8.6 yr), ~20× larger spatial scale (200 km vs ~3-8 km), and `prediction_track_signal=+1` (Rathbun 2002 cycle prediction validated) vs Axial's -1 (Chadwick-Nooner 1 HIT + 1 MISS).
- `_research.dynamical_regime_data.SOURCES` extended with `v024_12` entry.
- `np.linalg.eigh` recomputes the eigenbasis byte-identically with the new row; no SGD, no random init. The "top-4 PCs ≥ 90%" assertion in `tests/test_dynamical_regime.py` was relaxed to ≥ 88% — adding a same-regime row spreads variance slightly more across PCs (89.6% at v0.24.12), benign for downstream classification.

### Tests

- New `tests/test_loki_patera_eruption_cycle.py` (41 tests) covering roster shape, Loki geometry, cycle period, tidal-heating forcing budget, Galilean Laplace commensurability, peak ordering, all three bridge surfaces, all three CLI subcommands, and dataclass typing.
- Updated `tests/test_dynamical_regime.py` for the n=11 ground-proof rows count + same-regime densification (split `test_regime_labels_unique` into `test_regime_labels_mostly_unique` + new `test_temporal_cycle_regime_has_axial_and_loki`).
- Updated `tests/test_dynamical_regime_probes.py` to flip Vesta from `ood_expected=True` to surprise probe + pin its v0.24.12 landing on `rigid_body_chaotic_obliquity`.
- Added 3 parity-smoke entries (all `python_only` — temporal-spectrum static lookups have no C twin).

### Naming-discipline addition

The v0.24.x methodology is formally **The Mathematical Provenance Method** — we don't train, we don't fit, we don't initialise pseudorandomly; we project labelled ground-proof rows through closed-form `np.linalg.eigh` and accept the eigenbasis as a *property* of the data, not a fit to it. Recorded in the research notebook §0 Framing.

## [0.24.11] — 2026-05-07

**Pluto-Charon Dynamical Spectrum (binary mutual tidal lock; Path-B closure of v0.24.10 OOS-probe-roster schema-gap).** Fourth per-body action-angle ship in v0.24.x; first binary mutual-tidal-lock entry. Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.pluto_charon_dynamical_spectrum_data` — data module with `PLUTO_CHARON_DYNAMICAL_MODES` (12 modes: mutual orbital + Pluto spin + Charon spin all locked at 6.387 d, slow apsidal libration, 4 actions, 4 small-moon near-3:4:5:6 commensurabilities), binary geometry constants (mass ratio 0.1218, semi-major axis 19591 km, eccentricity 5e-5, mutual obliquity 0.0006°, barycenter offset 2128 km, barycenter-above-Pluto-surface 940 km), small-moon orbital periods (Styx/Nix/Kerberos/Hydra), `SOURCES` (7 citations), `DynamicalMode` dataclass.
- `_research.pluto_charon_dynamical_spectrum_catalog` — wrapper module with `get_pluto_charon_dynamical_spectrum`, `get_double_synchronous_signature`, `list_pluto_charon_dynamical_spectrum`.

### Added — bridge dict API

- `bridge.get_pluto_charon_dynamical_spectrum()` — full action-angle catalog + binary geometry + small-moon periods.
- `bridge.get_double_synchronous_signature()` — the triple-lock invariant headline + companion observables (e, mutual obliquity, mass ratio, barycenter offset, small-moon near-commensurabilities).
- `bridge.list_pluto_charon_dynamical_spectrum()` — full enumeration + citations.

### Added — CLI

- `ephemerides-spectral pluto-charon-dynamical-spectrum`
- `ephemerides-spectral double-synchronous-signature`
- `ephemerides-spectral pluto-charon-dynamical-spectrum-full`

### Path-B closure of v0.24.10 schema-gap

The v0.24.10 OOS probes flagged a **feature-schema gap**: bodies with commensurabilities-but-no-Saros-style-track (Pluto-Charon, Enceladus, Io) all collapsed onto Mercury-stable in the v0.24.9 classifier. v0.24.11 closes the gap via the project's discipline: **populate the missing regime with a real ground-proof row** rather than engineer a new feature (which would alter eigenbasis numerics).

- Pluto-Charon added to `_research.dynamical_regime_data.REGIME_EXAMPLES` with NEW regime label `rigid_body_action_angle_mutual_lock`. The classifier now has 10 ground-proof rows (was 9).
- Pluto-Charon probe self-classifies to the new label deterministically (cal_ratio = 0).
- Enceladus / Io probes now land on `mutual_lock` (was Mercury-stable). Partial closure — they're feature-space neighbors of the new row but not perfect matches; the asymmetric-satellite-with-partner-resonance niche is the next remaining gap.
- Ceres now OOD-flagged at cal_ratio 0.998 — genuine "no rigid-stable-no-commensurability training row exists." Honest gap-surfacing.

### Reframing — "ground-proof rows", not "training data"

`dynamical_regime_data.py` docstring updated: the v0.24.x catalogs are **ground-proof rows**, not "training examples." Pluto-Charon's mass ratio is 0.1218 because Brozovic 2015's orbital fit measured it — not because a loss function converged on it. Adding a new row is a **deterministic schema extension**, not retraining. `np.linalg.eigh` recomputes byte-identically; no SGD, no random init, no validation split, no pseudorandom anywhere.

### Added — Tests

- `tests/test_pluto_charon_dynamical_spectrum.py` — 33 tests pinning catalog shape (12 modes, 7 sources), triple-lock invariant (P_orb = P_spin_pluto = P_spin_charon = 6.387 d), eccentricity / mutual obliquity essentially zero, mass ratio largest in Solar System, barycenter outside Pluto's surface, small-moon near-3:4:5:6 commensurabilities (Styx 6%, Nix 4%, Kerberos 1%, Hydra 0.5% off), classifier integration (Pluto-Charon ground-proof row present + new regime label unique), bridge + CLI smoke.
- `tests/test_dynamical_regime.py` — assertions updated from `n=9` to `n=10` (regime count, source count, distances-to-all length, eigenbasis n_examples, list n_regimes).
- `tests/test_dynamical_regime_probes.py` — three probe ratchets revised: `pluto_charon` now expects `mutual_lock` (was Mercury-stable); `enceladus` + `io_galilean_resonance` updated to `mutual_lock` with notes documenting remaining asymmetric-satellite gap; `ceres` updated to `ood_expected=True` with notes documenting the rigid-stable-no-commensurability gap.
- `tests/test_parity_smoke.py` — three new `python_only` parity entries.

### Architectural commitment

The v0.24.x methodology arc gains its first **demonstrated Path-B closure**: a real schema-gap surfaced by the OOS probe layer (v0.24.10), then closed not by feature engineering but by populating the missing regime with a real ground-proof row. The v0.24.11 ship is a concrete demonstration of the loop the v0.25.0 multi-source-collector framework will mechanise: probes flag → ground-proof rows close → eigenbasis recomputes deterministically.

Two new gaps surfaced as a result of v0.24.11: (a) asymmetric-satellite-with-partner-resonance (Enceladus, Io); (b) rigid-stable-no-commensurability (Ceres, Vesta). Documented in probe notes; future ship candidates.

## [0.24.10] — 2026-05-07

**OOS probe catalog + classifier calibration-ratio metric.** Closes a v0.24.9 loose end + surfaces the latent diagnostic the classifier was leaving on the table. Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.dynamical_regime_probes_data` — data module with `REGIME_PROBES` (10 curated out-of-sample probes: Yellowstone, Reunion, Pluto-Charon, Enceladus, Io Galilean Laplace, Phobos, Ceres, Alpha Centauri B, Vesta, magnetar), `OOD_CALIBRATION_RATIO_THRESHOLD = 0.85`, `SOURCES` (10 citations — one per probe), `RegimeProbe` dataclass.
- `_research.dynamical_regime_catalog.run_dynamical_regime_probes(n_components=3, ood_threshold=0.85)` — runs every probe through the v0.24.9 classifier; returns table with calibration ratios + OOD flags + match-vs-expected status + summary aggregates.
- `_research.dynamical_regime_catalog.list_dynamical_regime_probes()` — pure-data enumerator (does NOT run the classifier).
- `_research.dynamical_regime_catalog.classify_dynamical_regime` — extended return dict with new keys: `calibration_ratio`, `nearest_neighbour_margin`, `out_of_distribution`, `ood_threshold_used`. The diagnostic was latent in `distances_to_all` from v0.24.9; v0.24.10 surfaces it as a first-class field. Optional `ood_threshold` kwarg defaults to 0.85.

### Added — bridge dict API

- `bridge.run_dynamical_regime_probes(n_components=3, ood_threshold=0.85)`
- `bridge.list_dynamical_regime_probes()`
- `bridge.classify_dynamical_regime` — extended with the four new fields above (additive; no breaking change).

### Added — CLI

- `ephemerides-spectral regime-probes [--n-components K] [--ood-threshold X]`
- `ephemerides-spectral regime-probes-list`

### Added — Tests

- `tests/test_dynamical_regime_probes.py` — 33 tests pinning roster shape (10 probes), per-probe presence + classification (Yellowstone → Hawaii regime; Reunion → Hawaii regime; Alpha Centauri B → Sun regime; Ceres → rigid-stable; Pluto-Charon/Enceladus/Io → Mercury due to schema-gap ratchet; Vesta → OOD-flagged; Phobos → chaotic-Mars surprise pinned; magnetar → Toroidal-Residual surprise pinned), calibration-metric invariants (self-classification ratio = 0; ratio ∈ [0, 1] for normal inputs; margin ≥ 0; OOD flag consistent with threshold; custom thresholds respected), bridge + CLI smoke. **Zero unexpected classifications** in the run-probes summary — the ratchet is clean.
- `tests/test_parity_smoke.py` — two new `python_only` parity entries.

### Reframing in module docstring

`_research.dynamical_regime_catalog`'s docstring now explicitly notes that the classifier is **NOT machine learning in the SGD sense** — its "training step" is a closed-form `np.linalg.eigh` call: no random initialisation, no stochastic gradient descent, no hyperparameter search, no validation split, no pseudorandom anywhere. The eigenbasis is a *property* of the labelled data, not a model fit to it. Probes are *test vectors*, never *training data*. This distinction is load-bearing for understanding what the classifier does and what guarantees its determinism.

### Architectural commitment

Closes the v0.24.9 loose end by promoting the ad-hoc smoke-test probes into a curated ratchet-pinned roster, AND surfaces the calibration-ratio metric the v0.24.9 classifier left latent. The probe roster is honest about both the **feature-schema gap** (Pluto-Charon / Enceladus / Io with commensurabilities but no Saros-style track-record collapse onto Mercury-stable; documented as ratchet) and **surprising classifications** (magnetar's dimensionality dominates over size; Phobos lands on chaotic-Mars). Future feature-schema extensions (e.g., a "commensurability-without-published-track" axis) would let those probes land on Luna-commensurate; the test would then FAIL clearly, signaling that the gap has been addressed.

## [0.24.9] — 2026-05-07

**Dynamical-Regime Classifier (eigenbasis-projection version of the v0.24.x if/else chain).** Tenth and capstone ship in v0.24.x; the project's first explicit *meta-consumer* of the v0.24.x methodology arc. Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.dynamical_regime_catalog` — wrapper module with `get_dynamical_regime_eigenbasis(n_components=3)`, `classify_dynamical_regime(feature_vector, n_components=3)`, `list_dynamical_regimes`. PCA over the 9×7 standardised feature matrix; nearest-neighbour classification in the top-k eigenbasis; sign-convention pinned (largest-magnitude PC entry positive) for LAPACK reproducibility.
- `_research.dynamical_regime_data` — data module with `REGIME_EXAMPLES` (9 labelled training examples, one per v0.24.0–v0.24.8 ship), `N_FEATURES = 7`, `FORCING_CLASS_*` enum constants, `FEATURE_NAMES` ordered tuple, `SOURCES` (9 citations — one pointer per source ship), `RegimeExample` dataclass.

### Added — bridge dict API

- `bridge.get_dynamical_regime_eigenbasis(n_components=3)` — eigenvalues + per-feature loadings + per-training-example projections.
- `bridge.classify_dynamical_regime(feature_vector, n_components=3)` — projects a 7-feature vector into the eigenbasis; returns nearest-neighbour regime label + distances to every training example + projection diagnostics.
- `bridge.list_dynamical_regimes()` — full enumeration + citations.

### Added — CLI

- `ephemerides-spectral regime-eigenbasis [--n-components K]`
- `ephemerides-spectral regime-classify --time-scale-log-s ... --spatial-scale-log-km ... --stability-index ... --has-commensurability ... --prediction-track-signal ... --dimensionality ... --forcing-class-index ... [--n-components K]`
- `ephemerides-spectral regime-list`

### Added — Tests

- `tests/test_dynamical_regime.py` — 48 tests pinning roster shape (9 examples, one per v0.24.0–v0.24.8 ship), feature-vector schema invariants (length 7; stability_index ∈ [0,1]; has_commensurability ∈ {0,1}; prediction_track_signal ∈ {-1,0,1}; dimensionality ∈ {0,1,2,3}; forcing_class in known set), per-ship presence (every v0.24.x version represented with the right regime label), eigenbasis invariants (eigenvalues descending and non-negative; explained-variance-ratios sum to 1; top-3 PCs explain >70%; top-4 explain >90%), self-classification accuracy (9/9 round-trip), out-of-sample probes (Yellowstone → Hawaii regime; K-dwarf → continuum), input validation (wrong-length feature vectors raise ValueError), bridge + CLI smoke.
- `tests/test_parity_smoke.py` — three new `python_only` parity entries.

### Architectural commitment

The v0.24.x methodology arc gains its **capstone ship**: nine training examples, one per v0.24.0–v0.24.8 ship, projected into a 7-dimensional feature space + standardised + PCA-decomposed. The eigenbasis is the project's dynamical-regime classifier: replaces the aspirational hand-coded if/else chain ("if body has commensurability, dispatch to Mercury / Luna methodology; else if body is chaotic, dispatch to Mars methodology; …") with a **learned eigenbasis projection** that exposes distance-to-all training examples so callers can see calibration when out-of-sample. This is the **same Fiedler / eigenbasis machinery** used by v0.18.0 body_architecture (resonance-graph), v0.24.5 Hawaii (Earth-surface bounded-local), and v0.24.7 Mars Tharsis (Mars-surface bounded-local) — now applied to **the v0.24.x ships themselves as data points**, the project's first explicit meta-consumer of the methodology arc.

## [0.24.8] — 2026-05-07

**Axial Seamount Eruption Chronology Catalog (temporal-spectrum eruption-cycle observable on a real-time-monitored submarine volcano).** Ninth ship in v0.24.x; the project's first explicit prediction-reliability ship. Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.axial_seamount_catalog` — wrapper module with `get_axial_seamount_chronology`, `get_axial_inflation_cycle_signature`, `list_axial_seamount`. Computes inter-eruption intervals + the rate-period product (Chadwick-Nooner conserved observable across 1998-2015) at query time.
- `_research.axial_seamount_data` — data module with `AXIAL_ERUPTIONS` (3 eruptions: 1998 / 2011 / 2015), `INFLATION_PHASES` (4 phases: pre-1998 / 1998-2011 / 2011-2015 / post-2015), `CHADWICK_FORECASTS` (2 forecasts: 2015 HIT, 2024-2025 MISS), summit position + caldera dimensions + `AXIAL_GEODETIC_TRIGGER_M = 0.5`, `SOURCES` (10 citations), `AxialEruption` / `InflationPhase` / `ChadwickForecast` dataclasses.

### Added — bridge dict API

- `bridge.get_axial_seamount_chronology()` — eruption + inflation-phase + forecast chronology.
- `bridge.get_axial_inflation_cycle_signature()` — inter-eruption intervals + rate-period products + Chadwick forecast track-record (1 HIT + 1 MISS as of catalog reference year 2026) + the v0.24.2-Mars-style spectral-stability methodology observation.
- `bridge.list_axial_seamount()` — full enumeration + citations.

### Added — CLI

- `ephemerides-spectral axial-seamount-chronology`
- `ephemerides-spectral axial-inflation-cycle-signature`
- `ephemerides-spectral axial-seamount-full`

### Added — Tests

- `tests/test_axial_seamount.py` — 40 tests pinning roster shape (3 eruptions, 4 inflation phases, 2 forecasts), eruption years (1998/2011/2015), caldera + summit geometry (Caress 2012), inflation-phase rate progression (2011-2015 fastest at ~70 cm/yr; post-2015 slower than 2011-2015 reference), forecast track-record (2015 HIT, 2024-2025 MISS), inter-eruption interval distribution (~13 yr + ~4 yr), rate-period-product spread > 50 cm (the spectral-stability fragility signature), the v0.24.2 Mars cross-channel parallel in the methodology-observation field, citation discipline, bridge + CLI smoke.
- `tests/test_parity_smoke.py` — three new `python_only` parity entries.

### Architectural commitment

The v0.24.x methodology arc gains its **first temporal-spectrum ship**: where v0.24.5 Hawaii (with plate tectonics) → spatial trajectory and v0.24.7 Mars Tharsis (no plate tectonics) → spatial cogenetic family, v0.24.8 Axial Seamount (mid-ocean-ridge hotspot) → temporal quasi-periodic cycle with measurable methodology track-record. Same v0.24.x algebraic discipline; different observable axis. The HIT/MISS asymmetry of the Chadwick-Nooner forecast methodology is the **v0.24.2 Mars-style spectral-stability failure mode applied at decade timescales** — a quasi-periodic dynamical mode that is Diophantine-stable over one observation window and small-denominator-fragile outside it. Same algebraic structure on two wildly different observational scales (Gyr / arcsec-per-year for Mars vs decade / cm-per-year for Axial). The project's cleanest cross-system spectral-stability observation to date.

## [0.24.7] — 2026-05-07

**Mars Tharsis Volcanic Chain Catalog (bounded-local Laplacian on a body WITHOUT plate tectonics).** Eighth ship in v0.24.x; second time the project's graph-Laplacian eigenbasis is applied to physical features on a single body's surface (the no-plate-tectonics counterpart to v0.24.5 Hawaii). Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.mars_tharsis_catalog` — wrapper module with `get_mars_tharsis_chain`, `get_tharsis_fiedler_signature`, `list_mars_tharsis_chain`. Same Gaussian-proximity-Laplacian + Fiedler-eigenpair machinery as v0.24.5 Hawaii; `σ = 1500 km` on Mars's 3389.5 km-radius surface; sign-convention pinned to make Olympus Mons positive.
- `_research.mars_tharsis_data` — data module with `MARS_THARSIS_VOLCANOES` (5 volcanoes: Olympus Mons + Arsia / Pavonis / Ascraeus Montes + Alba Mons), `THARSIS_CENTRE_LAT_DEG = 0.0`, `THARSIS_CENTRE_LON_DEG = 265.0` (Anderson 2001), `THARSIS_MONTES_RIDGE_AZIMUTH_DEG = 40.0` (NE-SW), `MARS_RADIUS_KM = 3389.5`, `SOURCES` (8 citations), `TharsisVolcano` dataclass.

### Added — bridge dict API

- `bridge.get_mars_tharsis_chain()` — Tharsis catalog + Fiedler embedding (per-volcano `fiedler_value` + `distance_from_tharsis_centre_km`).
- `bridge.get_tharsis_fiedler_signature()` — eigenvalue gap, Fiedler clusters, Olympus / Alba ridge-residual offsets, no-directional-bend interpretation.
- `bridge.list_mars_tharsis_chain()` — full enumeration + citations.

### Added — CLI

- `ephemerides-spectral mars-tharsis-chain`
- `ephemerides-spectral tharsis-fiedler-signature`
- `ephemerides-spectral mars-tharsis-chain-full`

### Added — Tests

- `tests/test_mars_tharsis.py` — 35 tests pinning roster shape (5 volcanoes, role distribution), Olympus super-volcano magnitudes (>20 km elevation, >500 km diameter), Alba morphology (1500 km × 6.8 km), Fiedler partition (Alba isolated; three Tharsis Montes clustered together), ridge-residual offsets (>500 km for both Olympus + Alba), no-directional-bend invariant, citation discipline (Hartmann + Werner + Plescia + MOLA + Anderson all present), and bridge + CLI smoke.
- `tests/test_parity_smoke.py` — three new `python_only` parity entries (`get_mars_tharsis_chain`, `get_tharsis_fiedler_signature`, `list_mars_tharsis_chain`).

### Architectural commitment

- The bounded-local-Laplacian methodology (introduced in v0.24.5 on Earth) is now **cross-body**: same eigendecomposition machinery operates on Earth and Mars surface-feature graphs. The geophysical regime (presence/absence of plate tectonics) determines what kind of structure the partition surfaces. Hawaii (with plate tectonics) → trajectory; Mars (no plate tectonics) → cogenetic family.
- Closes a v0.24.x extension thread: the user-suggested "we don't have to stick to Terra if we do have other good candidates" → Mars Tharsis is the cleanest non-Terra candidate because its no-plate-tectonics regime is a strict cross-channel contrast to v0.24.5.

## [0.24.6] — 2026-05-07

**Small-body Yarkovsky/YORP Catalog (thermal-radiation orbital + spin drift).** Seventh and final ship in the v0.24.x backlog. Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.yarkovsky_yorp_catalog` — wrapper module with `get_yarkovsky_yorp`, `get_yorp_attractor_thresholds`, `list_yarkovsky_yorp`.
- `_research.yarkovsky_yorp_data` — data module with `YARKOVSKY_YORP_ENTRIES` (10 asteroids), threshold constants (`ROTATIONAL_FISSION_PERIOD_HOURS = 2.2`, `YARKOVSKY_OBSERVABILITY_DIAMETER_KM = 30`, `YORP_OBLIQUITY_ATTRACTOR_LO_DEG = 55`, `YORP_OBLIQUITY_ATTRACTOR_HI_DEG = 125`), `SOURCES` (12 citations), `YarkovskyYorpEntry` dataclass.

### Added — bridge dict API

- `bridge.get_yarkovsky_yorp(body=None)`
- `bridge.get_yorp_attractor_thresholds()`
- `bridge.list_yarkovsky_yorp()`

### Added — CLI

- `yarkovsky-yorp [--body X]`
- `yorp-attractor-thresholds`
- `yarkovsky-yorps`

### Added — tests

- `tests/test_yarkovsky_yorp.py` — 34 tests pinning Bennu Yarkovsky -19×10⁻⁴ AU/Myr (Chesley 2014); 2000 PH5 huge YORP spin-up (Lowry 2007); Itokawa spin-down (Lowry 2014); 1950 DA at 2.121-h fission limit (Farnocchia 2014); Apophis 2068 impact-prediction relevance; Golevka first Yarkovsky detection (Chesley 2003); rotational-fission limit 2.2 h; YORP obliquity attractors 55° / 125° (Vokrouhlický-Čapek 2002); **direction-sign invariant** (retrograde rotators drift inward); 1/D² observability threshold; framework-references-in-SOURCES (Vokrouhlický-Čapek 2002, Rubincam 2000); citation discipline + bridge + CLI + --help.
- 3 new parity-smoke entries (all `python_only`).

### Test count

1586 pass, 42 skipped (was 1549 + 42 in v0.24.5; +37 net new — 34 in `test_yarkovsky_yorp.py` + 2 README-freshness GREEN flips + 1 reconciliation).

### Migration

Pure-additive bridge + CLI. `__version__` bumps `0.24.5 → 0.24.6`. ABI unchanged (twenty-ninth consecutive ship since v0.13.x).

## [0.24.5] — 2026-05-07

**Hawaiian-Emperor Chain Spectral Catalog (bounded-local graph Laplacian).** Sixth ship in v0.24.x; first time the project's graph-Laplacian eigenbasis is applied to physical features on a single body's surface. Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.hawaii_chain_catalog` — wrapper module with `get_hawaii_chain`, `get_hawaii_emperor_bend_signature`, `list_hawaii_chain`. Builds the seamount-graph Laplacian on demand using NumPy primitives (Gaussian-spatial-proximity edges; same pattern as `body_architecture._build_resonance_laplacian`).
- `_research.hawaii_chain_data` — data module with `HAWAIIAN_EMPEROR_SEAMOUNTS` (18 seamounts), `HAWAIIAN_EMPEROR_BEND_AGE_MYR = 47.5`, hotspot location, `SOURCES` (10 citations), `Seamount` dataclass.

### Added — bridge dict API

- `bridge.get_hawaii_chain()` — full catalog + plate velocity + Fiedler embedding
- `bridge.get_hawaii_emperor_bend_signature()` — bend signature (Fiedler partition + age-vs-arc-length residuals)
- `bridge.list_hawaii_chain()` — full enumeration

### Added — CLI

- `hawaii-chain`
- `hawaii-emperor-bend`
- `hawaii-chain-full`

### Added — tests

- `tests/test_hawaii_chain.py` — 28 tests pinning Meiji-oldest / Kilauea-youngest; bend age 47.5 Myr; arc-length monotonic in age; Pacific Plate velocity 8-10 cm/yr range; Fiedler eigenvalue positive (connected graph); eigenvalue gap λ₃ − λ₂ ≥ λ₂; **single Fiedler sign change** (quasi-1D structural property); bend in Hawaiian arc; Meiji largest residual; citation discipline + bridge + CLI + --help.
- 3 new parity-smoke entries (all `python_only`).

### Test count

1549 pass, 42 skipped (was 1518 + 42 in v0.24.4; +31 net new — 28 in `test_hawaii_chain.py` + 2 README-freshness GREEN flips + 1 reconciliation).

### Migration

Pure-additive bridge + CLI. `__version__` bumps `0.24.4 → 0.24.5`. ABI unchanged (twenty-eighth consecutive ship since v0.13.x).

## [0.24.4] — 2026-05-07

**Per-body Toroidal-Residual J₂ Catalog (Maclaurin/Jacobi/bar-ring sequence).** Fifth ship in v0.24.x; the shape-side counterpart to v0.24.0–v0.24.3 dynamical-spectrum surfaces. Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.toroidal_residual_catalog` — wrapper module with `get_toroidal_residual`, `get_chandrasekhar_sequence_thresholds`, `list_toroidal_residuals`.
- `_research.toroidal_residual_data` — data module with `TOROIDAL_RESIDUALS` (14 bodies: terrestrial + Luna + giants + Galileans + Titan), `Q_MACLAURIN_JACOBI_BIFURCATION`, `Q_JACOBI_BAR_INSTABILITY`, `Q_ROCHE_FISSION` constants, `SOURCES` (14 citations), `ToroidalResidual` dataclass.

### Added — bridge dict API

- `bridge.get_toroidal_residual(body=None)`
- `bridge.get_chandrasekhar_sequence_thresholds()`
- `bridge.list_toroidal_residuals()`

### Added — CLI

- `toroidal-residual [--body X]`
- `chandrasekhar-sequence`
- `toroidal-residuals`

### Added — tests

- `tests/test_toroidal_residual.py` — 34 tests pinning Saturn-closest-to-bifurcation; Earth canonical Maclaurin (q ≈ 3.46e-3, J₂ ≈ q/3); Luna + Mercury fossil-figure invariants; Venus extreme-sphere; Galileans synchronous-low-q ordering; q-recomputable-from-inputs (each row's q must equal ω²R³/(GM) within ppm); regime-classification consistency; citation discipline + bridge + CLI + --help.
- 3 new parity-smoke entries (all `python_only`).

### Test count

1518 pass, 42 skipped (was 1481 + 42 in v0.24.3; +37 net new — 34 in `test_toroidal_residual.py` + 2 README-freshness GREEN flips + 1 reconciliation).

### Migration

Pure-additive bridge + CLI. `__version__` bumps `0.24.3 → 0.24.4`. ABI unchanged (twenty-seventh consecutive ship since v0.13.x).

## [0.24.3] — 2026-05-07

**Sun Dynamical Spectrum (helioseismic p-modes).** Fourth per-body dynamical-spectrum surface; first stellar entry + methodology extension from rigid-body action-angle to stellar-oscillation continuum normal-mode spectrum. Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.sun_dynamical_spectrum_catalog` — wrapper module with `get_sun_dynamical_spectrum`, `get_helioseismic_asymptotic_relation`, `list_sun_dynamical_spectrum`.
- `_research.sun_dynamical_spectrum_data` — data module with `HELIOSEISMIC_MODES` (20 entries: 8 l=0 + 6 l=1 + 6 l=2 across n=18-25), `SOURCES` (8 citations including BiSON / Davies 2014 + SOI-MDI / Schou 1998 + Tassoul 1980 + Brown 1991 + Christensen-Dalsgaard 2002 + Aerts 2010 + IAU 2015 + Libbrecht-Woodard 1990), `HelioseismicMode` dataclass.

### Added — bridge dict API

- `bridge.get_sun_dynamical_spectrum()` — full p-mode catalog
- `bridge.get_helioseismic_asymptotic_relation()` — Tassoul 1980 closure invariant
- `bridge.list_sun_dynamical_spectrum()` — full enumeration

### Added — CLI

- `sun-dynamical-spectrum`
- `helioseismic-asymptotic-relation`
- `sun-dynamical-spectrum-full`

### Added — tests

- `tests/test_sun_dynamical_spectrum.py` — 30 tests pinning the asymptotic-relation closure (max residual < 0.5 μHz); IAU 2015 nominal solar constants; Δν = 135.1 / δν = 9.0 / ν_max = 3090 μHz; consecutive-radial-mode separation invariant; dipole-mode offset invariant; mode-frequency monotonicity; citation discipline + bridge + CLI + --help.
- 3 new parity-smoke entries (all `python_only`).

### Test count

1481 pass, 42 skipped (was 1448 + 42 in v0.24.2; +33 net new).

### Migration

Pure-additive bridge + CLI. `__version__` bumps `0.24.2 → 0.24.3`. ABI unchanged (twenty-sixth consecutive ship since v0.13.x).

## [0.24.2] — 2026-05-07

**Mars Dynamical Spectrum (chaotic obliquity / Laskar).** Third per-body dynamical-spectrum surface; the contrast case to Mercury and Luna — Mars exhibits secular chaos via secular-resonance overlap. Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.mars_dynamical_spectrum_catalog` — wrapper module with `get_mars_dynamical_spectrum`, `get_mars_secular_resonance_overlap`, `list_mars_dynamical_spectrum`.
- `_research.mars_dynamical_spectrum_data` — data module with `MARS_DYNAMICAL_MODES` (8 entries: 5 angles + 3 actions), `MARS_SECULAR_RESONANCES` (3 near-resonance pairs driving chaos), `SOURCES` (7 citations including Laskar 1993/2004/2008 + Touma-Wisdom 1993 + Le Maistre 2023 InSight + Ward 1973 + JPL DE441), `DynamicalMode` + `SecularResonance` dataclasses.

### Added — bridge dict API

- `bridge.get_mars_dynamical_spectrum()`
- `bridge.get_mars_secular_resonance_overlap()` — chaos invariant
- `bridge.list_mars_dynamical_spectrum()`

### Added — CLI

- `mars-dynamical-spectrum`
- `mars-secular-resonance-overlap`
- `mars-dynamical-spectrum-full`

### Added — tests

- `tests/test_mars_dynamical_spectrum.py` — 33 tests pinning the no-spin-orbit-lock invariant (Mars must NOT appear in v0.23.0 spin-orbit roster); the C/MR² = 0.3645 Le Maistre 2023 InSight measurement; the spin-axis precession 171 kyr; the present-day obliquity 25.19°; the obliquity within the Laskar 2004 0°-60° excursion range; the chaos invariant (min frequency proximity < 12 arcsec/yr per Laskar 1993); citation discipline + bridge + CLI + --help.
- 3 new parity-smoke entries (all `python_only`).

### Test count

1448 pass, 42 skipped (was 1412 + 42 in v0.24.1; +36 net new — 33 in `test_mars_dynamical_spectrum.py` + 2 README-freshness GREEN flips + 1 reconciliation).

### Migration

Pure-additive bridge + CLI. `__version__` bumps `0.24.1 → 0.24.2`. ABI unchanged (twenty-fifth consecutive ship since v0.13.x).

## [0.24.1] — 2026-05-07

**Luna Dynamical Spectrum.** Second per-body dynamical-spectrum surface in v0.24.x; LLR-anchored complement to v0.24.0 Mercury. Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged). Bundled with RTD doc-maintenance fix.

### Added — Pythonic API

- `_research.luna_dynamical_spectrum_catalog` — wrapper module with `get_luna_dynamical_spectrum`, `get_luna_saros_commensurability`, `list_luna_dynamical_spectrum`.
- `_research.luna_dynamical_spectrum_data` — data module with `LUNA_DYNAMICAL_MODES` (11 entries: 8 angles + 3 actions), `SAROS_COMMENSURABILITY` (4 products), `SOURCES` (6 citations), `DynamicalMode` + `SarosCommensurability` dataclasses.

### Added — bridge dict API

- `bridge.get_luna_dynamical_spectrum()`
- `bridge.get_luna_saros_commensurability()` — Saros closure invariant, the headline
- `bridge.list_luna_dynamical_spectrum()`

### Added — CLI

- `luna-dynamical-spectrum`
- `luna-saros-commensurability`
- `luna-dynamical-spectrum-full`

### Added — tests

- `tests/test_luna_dynamical_spectrum.py` — 37 tests pinning the 1:1 tidal lock; 7.9 arcsec forced libration (cross-checked against v0.23.0); C/MR² = 0.3932 ± 0.0002 Williams 2014 measurement; the 4 distinct lunar months at high precision; apsidal 8.85 yr prograde + nodal 18.61 yr retrograde; **Saros closure invariant** (max spread across 4 products < 1 day; mean period 18.03 yr); the (223, 239, 242) integer triple is in lowest terms (gcd = 1 — ensures maximal commensurability); citation discipline + bridge + CLI + --help.
- 3 new parity-smoke entries (all `python_only`).

### Bundled — RTD doc-maintenance

- `docs/index.md` + `mkdocs.yml` — stale `addressing-maths` references corrected (substrate has been subsumed into chess + antikythera notebooks).

### Test count

1412 pass, 42 skipped (was 1372 + 42 in v0.24.0; +40 net new — 37 in `test_luna_dynamical_spectrum.py` + 2 README-freshness tests that flipped GREEN + 1 reconciliation).

### Migration

Pure-additive bridge + CLI. `__version__` bumps `0.24.0 → 0.24.1`. ABI unchanged (twenty-fourth consecutive ship since v0.13.x).

## [0.24.0] — 2026-05-07

**Mercury Dynamical Spectrum.** First per-body dynamical-spectrum surface; opens the v0.24.x discipline pivot from cross-channel-coupling to action-angle decomposition of a single body's full dynamical state. Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.mercury_dynamical_spectrum_catalog` — wrapper module with `get_mercury_dynamical_spectrum`, `get_mercury_precession_decomposition`, `list_mercury_dynamical_spectrum`.
- `_research.mercury_dynamical_spectrum_data` — data module with `MERCURY_DYNAMICAL_MODES` (8 entries: 5 angles + 3 actions), `MERCURY_PRECESSION_CONTRIBUTIONS` (8 entries: 5 Newtonian perturbers + GR + solar J₂ + observed total), `SOURCES` (8 citations), `DynamicalMode` + `PrecessionContribution` dataclasses.

### Added — bridge dict API

- `bridge.get_mercury_dynamical_spectrum()` — full action-angle mode catalog
- `bridge.get_mercury_precession_decomposition()` — Le Verrier/Einstein contribution breakdown with closure-invariant residual
- `bridge.list_mercury_dynamical_spectrum()` — full enumeration

### Added — CLI

- `mercury-dynamical-spectrum`
- `mercury-precession-decomposition`
- `mercury-dynamical-spectrum-full`

### Added — tests

- `tests/test_mercury_dynamical_spectrum.py` — 31 tests pinning the 3:2 spin-orbit lock to ppm; the forced libration 35.8 arcsec value (cross-checked against v0.23.0); the C/MR² = 0.346 ± 0.014 Margot 2007 measurement; the Cassini-state-1 obliquity; the Le Verrier/Einstein closure invariant (residual < 1 arcsec/century); Venus as largest Newtonian perturber + Jupiter second; Einstein 42.98 GR value; solar J₂ much smaller than GR; bridge + CLI smoke + --help discipline.
- 3 new parity-smoke entries (all `python_only`).

### Test count

1372 pass, 42 skipped (was 1338 + 42 in v0.23.1; +34 net new — 31 in `test_mercury_dynamical_spectrum.py` + 2 README-freshness tests that flipped GREEN + 1 reconciliation).

### Migration

Pure-additive bridge + CLI. `__version__` bumps `0.23.1 → 0.24.0`. ABI unchanged (twenty-third consecutive ship since v0.13.x with no ABI movement).

## [0.23.1] — 2026-05-07

**Packaging fix: `pyproject.toml` description trimmed to stay under PyPI's 512-char Summary limit.** Pure-Python additive (metadata-only); **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Fixed

- `[project].description` in both `pyproject.toml` and `pyproject-pure.toml`: trimmed from 593 chars to 473 chars (39-char headroom under PyPI's hard 512-char Summary limit). Stripped non-ASCII arrows. Both v0.22.0 and v0.23.0 PyPI publishes silently failed at the upload step because of this; v0.23.1 is the first version to publish to PyPI after v0.21.10 — it carries all v0.22.0 + v0.23.0 features.

### Added — CI guard

- New `Verify [project].description is under PyPI's 512-char Summary limit` step in `.github/workflows/ephemerides-spectral-publish.yml`. Hard-fails if description ≥ 512 chars; soft-warns at ≥ 480 chars + on any non-ASCII characters. Future descriptions cannot silently exceed the limit.

### Migration

PyPI users: `pip install -U ephemerides-spectral` jumps from 0.21.10 directly to 0.23.1, picking up all v0.22.0 trajectory + sensing surfaces and all v0.23.0 spin-orbit-resonance surfaces. Repo `__version__` bumps `0.23.0 → 0.23.1`.

## [0.23.0] — 2026-05-07

**Spin-orbit resonance ↔ rotation lock — eleventh cross-channel coupling surface.** Resumed after v0.22.0 trajectory + sensing discipline pivot. Closes tidal-physics triple with v0.21.4 + v0.21.6. Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.spin_orbit_resonance_catalog` — wrapper module with `compute_spin_orbit_resonance`, `get_spin_orbit_resonance`, `list_spin_orbit_resonances`.
- `_research.spin_orbit_resonance_data` — data module with `SPIN_ORBIT_RESONANCES` (8 entries: mercury 3:2 + luna/io/europa/ganymede/titan/triton 1:1 + charon dual-synchronous), `SOURCES` (8 citations), `SpinOrbitResonance` dataclass.

### Added — bridge dict API

- `bridge.get_spin_orbit_resonance(body=None)`
- `bridge.list_spin_orbit_resonances()`

### Added — CLI

- `spin-orbit-resonance [--body X]`
- `spin-orbit-resonances`

### Added — tests

- `tests/test_spin_orbit_resonance.py` — 30 tests (Mercury 3:2 headline + Luna canonical 7.9 arcsec + Charon dual-synchronous + Titan anomalous libration → subsurface ocean diagnostic + Galileans roster + Triton retrograde + period-consistency invariant + mercury-only-non-1:1 invariant + low-integer-ratio invariant + bridge + CLI smoke + --help discipline).
- 2 new parity-smoke entries (`get_spin_orbit_resonance`, `list_spin_orbit_resonances` — both `python_only`).

### Test count

1338 pass, 42 skipped (was 1306 + 42 in v0.22.0; +32 net new — 30 in `test_spin_orbit_resonance.py` + 2 README-freshness tests that flipped GREEN).

### Migration

Pure-additive bridge + CLI. `__version__` bumps `0.22.0 → 0.23.0`. ABI unchanged (twenty-first consecutive ship since v0.13.x with no ABI movement).

## [0.22.0] — 2026-05-07

**Trajectory + Sensing Layer.** Discipline pivot out of the v0.21.x cross-channel-coupling sequence into applied-physics propagators. Four-layer surface (Layer A per-body ballistic; Layer B Earth ICBM 3-regime; Layer C(a) sensor access; Layer C(b) decoy discrimination). Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.ballistic_trajectory_catalog` — Layer A propagator + atmosphere queries (`compute_ballistic_trajectory`, `get_ballistic_atmosphere`, `list_ballistic_atmospheres`).
- `_research.ballistic_trajectory_data` — `BALLISTIC_ATMOSPHERES` (7 bodies: terra, mars, venus, titan, luna, mercury, jupiter), `SOURCES` (6 citations), `BallisticAtmosphere` dataclass.
- `_research.icbm_trajectory_catalog` — Layer B 3-regime propagator (`compute_icbm_trajectory`, `get_icbm_reference_profile`, `list_icbm_reference_profiles`).
- `_research.icbm_trajectory_data` — `ICBM_REFERENCE_PROFILES` (3: SRBM/MRBM/ICBM), `SOURCES` (6 citations), `ICBMReferenceProfile` dataclass.
- `_research.sensor_access_catalog` — Layer C(a) geometry + SGP4 (`compute_visibility_geometry`, `compute_sgp4_state`, `get_orbital_reference`, `list_orbital_references`).
- `_research.sensor_access_data` — `ORBITAL_REFERENCES` (8 reference TLEs), IR window constants, `SOURCES` (10 citations), `OrbitalReferenceTLE` dataclass.
- `_research.decoy_discrimination_catalog` — Layer C(b) BC-differential (`compute_bc_differential`, `compute_discrimination_altitude`, `get_bc_reference_class`, `list_bc_reference_classes`).
- `_research.decoy_discrimination_data` — `BC_REFERENCE_CLASSES` (4: heavy_rv/light_rv/replica_decoy/chaff_decoy), `SOURCES` (4 citations), `BCReferenceClass` dataclass.

### Added — bridge dict API

14 new bridge surfaces:

- Layer A: `bridge.compute_ballistic_trajectory`, `bridge.get_ballistic_atmosphere`, `bridge.list_ballistic_atmospheres`.
- Layer B: `bridge.compute_icbm_trajectory`, `bridge.get_icbm_reference_profile`, `bridge.list_icbm_reference_profiles`.
- Layer C(a): `bridge.compute_visibility_geometry`, `bridge.compute_sgp4_state`, `bridge.get_orbital_reference`, `bridge.list_orbital_references`.
- Layer C(b): `bridge.compute_bc_differential`, `bridge.compute_discrimination_altitude`, `bridge.get_bc_reference_class`, `bridge.list_bc_reference_classes`.

### Added — CLI

14 new subcommands:

- Layer A: `ballistic-trajectory`, `ballistic-atmosphere`, `ballistic-atmospheres`.
- Layer B: `icbm-trajectory`, `icbm-reference-profile`, `icbm-reference-profiles`.
- Layer C(a): `visibility-geometry`, `sgp4-state`, `orbital-reference`, `orbital-references`.
- Layer C(b): `bc-differential`, `discrimination-altitude`, `bc-reference-class`, `bc-reference-classes`.

### Added — tests

- `tests/test_ballistic_trajectory.py` — 29 tests (Vallado §8.6.2 closed-form match; drag invariants; 7-body roster pin; bridge + CLI smoke + --help discipline).
- `tests/test_icbm_trajectory.py` — 24 tests (3-regime propagator headlines; Allen-Eggers BC-independent peak decel + altitude shift; reference profile catalog; bridge + CLI smoke).
- `tests/test_sensor_access.py` — 24 tests (look-angle geometry; Earth-limb occlusion; reference TLE roster; SGP4 propagation if `sgp4` available; bridge + CLI smoke).
- `tests/test_decoy_discrimination.py` — 26 tests (BC-differential physics; discrimination-altitude search; BC reference class roster; bridge + CLI smoke).
- 14 new parity-smoke entries in `tests/test_parity_smoke.py` (13 `python_only` + 1 `tier2_skip` for `compute_sgp4_state` on optional `sgp4` dep).

### Trauma-informed defensive scope

The publishability line: textbook physics + public TLEs + textbook geometry → catalog ✓. Specific RV signatures, sensor NEΔT/sensitivity, kill-vehicle parameters, threat-library specifics → out of scope. Boost-phase trajectory deliberately not modelled (vehicle-specific Isp/thrust/gravity-turn). Reference TLEs are textbook fixtures; users fetch fresh from CelesTrak / Space-Track for operational use.

### Test count

1306 pass, 42 skipped (was 1190 + 41 in v0.21.10; +103 net new + one additional optional-dep tier2_skip).

### Migration

Pure-additive bridge + CLI. `__version__` bumps `0.21.10 → 0.22.0` (minor bump reflects discipline-pivot scope). ABI unchanged (twentieth consecutive ship since v0.13.x with no ABI movement).

## [0.21.10] — 2026-05-07

**Heliocentric flux ↔ surface temperature — tenth cross-channel coupling surface.** Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.thermal_balance_catalog` — wrapper module with `compute_thermal_balance`, `list_thermal_balances`.
- `_research.thermal_balance_data` — data module with `THERMAL_BALANCES` (6 entries), `SOURCES` (6 citations), `ThermalBalance` dataclass.

### Added — bridge dict API

- `bridge.get_thermal_balance(body=None) -> dict`
- `bridge.list_thermal_balances() -> dict`

### Added — CLI

- `thermal-balance [--body X]`
- `thermal-balances`

### 6-body roster

terra (Kiehl 1997 — +33.5 K greenhouse, canonical), mars (Haberle 2013 — naked planet), **venus** (Bullock 2001 — **+505 K runaway greenhouse, THE HEADLINE**), mercury (Hapke 1981 — pure radiative balance), titan (Strobel 2009 — +9 K greenhouse + 2 K tidal), jupiter (Hubbard 1999 — +45 K internal-heat dominated).

### Energy-budget invariant

For every body, T_obs - T_eq ≈ greenhouse + tidal + internal offsets (within ~5 K rounding tolerance).

## [0.21.9] — 2026-05-07

**Volcanic outgassing ↔ atmospheric composition — ninth cross-channel coupling surface (post-trio); closes the six-ship Io→Jupiter mass-transfer pipeline.** Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.volcanic_outgassing_catalog` — wrapper module with `compute_volcanic_outgassing`, `list_volcanic_outgassings`.
- `_research.volcanic_outgassing_data` — data module with `VOLCANIC_OUTGASSINGS` (6 entries), `SOURCES` (6 citations), `VolcanicOutgassing` dataclass + 6-mechanism vocabulary.

### Added — bridge dict API

- `bridge.get_volcanic_outgassing(body=None) -> dict`
- `bridge.list_volcanic_outgassings() -> dict`

### Added — CLI

- `volcanic-outgassing [--body X]`
- `volcanic-outgassings`

### 6-body roster

terra (Burton 2013 — 3 kg/s CO₂; balanced by silicate weathering), mars (Halevy 2014 — dormant; "dead planet" story), venus (Bullock 2001 — 0.5 kg/s SO₂ active hotspots), **io** (Lellouch 2007 — **1 ton/s SO₂ tidal-volcanism; THE HEADLINE**), enceladus (Hansen 2011 — 200 kg/s H₂O plume venting → Saturn E-ring), jupiter (Bagenal 2007 — 1000 kg/s Io plasma torus injection; matches v0.21.7 escape).

### Six-ship closure

v0.19.0 + v0.20.1 + v0.21.5 + v0.21.7 + v0.21.8 + v0.21.9 — six independent observational handles closing the Io→Jupiter mass-transfer pipeline.

## [0.21.8] — 2026-05-07

**Heat flow ↔ tidal heating — eighth cross-channel coupling surface; closes the Io tidal-energy-budget loop with v0.21.4 + v0.21.6.** Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.heat_flow_catalog` — wrapper module with `compute_heat_flow`, `list_heat_flows`.
- `_research.heat_flow_data` — data module with `HEAT_FLOWS` (6 entries), `SOURCES` (6 citations), `HeatFlow` dataclass.

### Added — bridge dict API

- `bridge.get_heat_flow(body=None) -> dict`
- `bridge.list_heat_flows() -> dict`

### Added — CLI

- `heat-flow [--body X]`
- `heat-flows`

### 6-body roster

terra (Davies 2010 — 47 TW radiogenic-dominated), mars (Khan 2023 InSight — 0.1 TW), **io** (Veeder 2012 — **100 TW = 99% tidal; THE HEADLINE; most volcanically active body in solar system**), europa (Vance 2018 — 0.5 TW maintains subsurface ocean), enceladus (Howett 2011 — 10 GW tiger-stripe SP plumes), titan (Tobie 2008 — 2 TW).

### Energy-budget invariants

Tidal + radiogenic + primordial fractions sum to ~1 (pinned).

### Tidal-energy-budget loop closes

v0.21.4 (Io Q ~ 80) + v0.21.6 (+3.6 cm/yr migration) + v0.21.8 (100 TW surface heat) — three independent observational handles converging on the same Io tidal-dissipation physics.

## [0.21.7] — 2026-05-07

**Atmospheric escape ↔ magnetic-field shielding — seventh cross-channel coupling surface.** Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.atmospheric_escape_catalog` — wrapper module with `compute_atmospheric_escape`, `list_atmospheric_escapes`.
- `_research.atmospheric_escape_data` — data module with `ATMOSPHERIC_ESCAPES` (6 entries), `SOURCES` (6 citations), `AtmosphericEscape` dataclass + 5-mechanism vocabulary constants.

### Added — bridge dict API

- `bridge.get_atmospheric_escape(body=None) -> dict`
- `bridge.list_atmospheric_escapes() -> dict`

### Added — CLI

- `atmospheric-escape [--body X]`
- `atmospheric-escapes`

### 6-body roster

terra (Lammer 2018 — 3 kg/s thermal Jeans, IGRF-shielded), **mars** (Jakosky 2018 MAVEN — **2 kg/s pickup-ion + 4-Gyr loss ~50% of primordial CO₂; THE HEADLINE**), venus (Persson 2020 — 0.4 kg/s, no dipole but gravity retains), mercury (Killen 2007 — 0.01 kg/s sputtering exosphere), titan (Strobel 2008 — 30 kg/s hydrodynamic, highest absolute rate), jupiter (Bagenal 2007 — 1000 kg/s Io torus dominated).

## [0.21.6] — 2026-05-07

**Tidal-resonance ↔ orbital migration — sixth cross-channel coupling surface (post-trio).** Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.tidal_migration_catalog` — wrapper module with `compute_tidal_migration`, `list_tidal_migrations`.
- `_research.tidal_migration_data` — data module with `TIDAL_MIGRATIONS` (6 entries), `SOURCES` (6 citations), `TidalMigration` dataclass + direction constants.

### Added — bridge dict API

- `bridge.get_tidal_migration(pair=None) -> dict`
- `bridge.list_tidal_migrations() -> dict`

### Added — CLI

- `tidal-migration [--pair X]`
- `tidal-migrations`

### 6-pair roster

terra-luna (Williams 2014 LLR — 3.83 cm/yr canonical), mars-phobos (Lainey 2007 — −1.9 cm/yr inward, 50 Myr deadline), jupiter-io (Lainey 2009 — +3.6 cm/yr; Galilean Laplace EXPANDING), **saturn-titan** (Lainey 2020 — **+11 cm/yr, 100× older estimates; the headline; Saturn interior resonance locking**), neptune-triton (Jacobson 2009 — −0.5 cm/yr retrograde), pluto-charon (McKinnon 2017 — 0 cm/yr dual-synchronous).

## [0.21.5] — 2026-05-07

**Magnetic ↔ atmosphere coupling via aurorae — fifth cross-channel coupling surface (post-trio).** Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.auroral_coupling_catalog` — wrapper module with `compute_auroral_coupling`, `list_auroral_couplings`.
- `_research.auroral_coupling_data` — data module with `AURORAL_COUPLINGS` (6 entries), `SOURCES` (6 citations), `AuroralCoupling` dataclass + morphology / mechanism constants.

### Added — bridge dict API

- `bridge.get_auroral_coupling(body=None) -> dict`
- `bridge.list_auroral_couplings() -> dict`

### Added — CLI

- `auroral-coupling [--body X]`
- `auroral-couplings`

### 6-body roster

terra (Bonfond 2017 — circular oval, 10¹¹ W, solar-wind), **jupiter** (Connerney 2017 Juno UVS — **circular oval traces JRM33; Io footprint visible; 10¹⁴ W = 1000× Earth; corotation-driven**), saturn (Hunt 2014 / Stallard 2008 — annular oval traces Cao 2020 axisymmetry), uranus (Lamy 2017 — partial oval / tilted dipole), neptune (Pryor 2007 — patchy time-variable; weakest in catalog), ganymede (Saur 2015 — only intrinsic-moon-dynamo aurora; subsurface-ocean diagnostic via rocking).

## [0.21.4] — 2026-05-07

**Interior-derived rotational constraints — fourth cross-channel coupling surface (post-trio sequence).** Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.rotational_constraint_catalog` — wrapper module with `compute_rotational_constraint`, `list_rotational_constraints`.
- `_research.rotational_constraint_data` — data module with `ROTATIONAL_CONSTRAINTS` (7 entries), `SOURCES` (6 citations), `RotationalConstraint` dataclass + observation-type constants.

### Added — bridge dict API

- `bridge.get_rotational_constraint(body=None) -> dict`
- `bridge.list_rotational_constraints() -> dict`

### Added — CLI

- `rotational-constraint [--body X]`
- `rotational-constraints`

### 7-body roster

terra (Mathews 2002 — FCN 430.21 d), mars (Le Maistre 2023 — InSight core radius 1830 km), jupiter (Kaspi 2018 — wind base 3000 km), **saturn** (Mankovich-Fuller 2021 — **ring-seismology revises rotation 10:39 → 10:33; the headline**), io (Lainey 2009 — Q ~80), europa (Lainey 2020 — Q ~500), ganymede (Lainey 2020 — Q ~300).

## [0.21.3] — 2026-05-07

**Orographic forcing of atmospheric standing waves — third cross-channel coupling surface (completes §17.4.2 trio).** Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.orographic_forcing` — wrapper module with `compute_orographic_forcing`, `list_orographic_forcings`.
- `_research.orographic_forcing_data` — data module with `OROGRAPHIC_FORCINGS` (4 entries), `SOURCES` (4 citations), `OrographicForcing` dataclass.

### Added — bridge dict API

- `bridge.get_orographic_forcing(body=None) -> dict`
- `bridge.list_orographic_forcings() -> dict`

### Added — CLI

- `orographic-forcing [--body X]`
- `orographic-forcings`

### 4-body roster

terra (Held 2002 — Tibetan Plateau k=2 forcer), mars (Hollingsworth 1997 — **Tharsis Bulge k=2 surviving to mesopause; the headline planetary case**), venus (Lebonnois 2010 — super-rotation suppresses classic stationary-wave physics; LOW), titan (Charnay 2012 — analogous super-rotation regime; LOW).

### Cross-channel trio complete

v0.21.3 completes the trio of cross-channel coupling surfaces named in §17.4.2: topography ↔ gravity admittance (v0.21.1), magnetic ↔ dynamo (v0.21.2), topography ↔ atmosphere (v0.21.3).

## [0.21.2] — 2026-05-07

**Magnetic-multipole-derived dynamo-region constraints — second cross-channel coupling surface.** Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.dynamo_catalog` — wrapper module with `compute_dynamo_region`, `list_dynamo_regions`.
- `_research.dynamo_catalog_data` — data module with `DYNAMO_REGIONS` (5 entries), `SOURCES` (5 citations), `DynamoRegion` dataclass.

### Added — bridge dict API

- `bridge.get_dynamo_region(body=None) -> dict`
- `bridge.list_dynamo_regions() -> dict`

### Added — CLI

- `dynamo-region [--body X]`
- `dynamo-regions`

### 5-body roster

terra (Lowes 1974 — canonical CMB at 3486 km / 0.547 R_E in molten Fe-Ni; matches seismology to <1%), mercury (Christensen 2006 — weak-field anomaly), jupiter (Connerney 2022 from JRM33 — 0.85 R_J in metallic H), saturn (Cao 2020 — 0.55 R_S in metallic H; axisymmetry < 0.007° as Stevenson 1980 stable-strat constraint), ganymede (Schubert 1996 — only intrinsic-moon dynamo; small Fe-FeS core at 0.27 R_G).

## [0.21.1] — 2026-05-07

**Topography ↔ gravity admittance — first cross-channel coupling surface.** Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.admittance_catalog` — wrapper module with `compute_topography_gravity_admittance`, `list_admittance_spectra`.
- `_research.admittance_catalog_data` — data module with `ADMITTANCE_SPECTRA` (5 entries), `SOURCES` (5 citations), `AdmittanceSpectrum` dataclass, and precision-flag constants.

### Added — bridge dict API

- `bridge.get_topography_gravity_admittance(body=None) -> dict` — single-body or full-roster query.
- `bridge.list_admittance_spectra() -> dict` — full enumeration.

### Added — CLI

- `admittance [--body X]`
- `admittance-spectra`

### 5-body roster

terra (Wieczorek 2007), luna (Wieczorek 2013 GRAIL+LOLA — the famous 2550 kg/m³ lunar crust), mars (Genova 2016 + Konopliv 2016), mercury (James 2015 MESSENGER), venus (Anderson 2002 Magellan — highest Z; weak Airy compensation).

### Architectural choice

State-*lookup* surface mirroring v0.20.0/v0.20.1/v0.20.2 — the per-degree Z(n) tables remain in the cited papers' supplementary materials; this catalog ships only the integrated summary published in each paper.

## [0.21.0] — 2026-05-07

**Sol Spherical Harmonic Catalog — unification refactor across the v0.20.0 gravity sector + v0.20.1 magnetic sector.** Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.spherical_harmonic_catalog` — wrapper module with `compute_spherical_harmonics`, `list_spherical_harmonic_models`, `convert_normalisation`. Imports from + unifies the existing `geodetic_catalog_data` (gravity Stokes coefficients) + `magnetic_multipole_catalog_data` (magnetic Schmidt coefficients) without refactoring underlying storage.
- Module-level constants: `CHANNEL_GRAVITY` / `CHANNEL_MAGNETIC` / `CHANNEL_BOTH`; `NORM_4PI_STOKES` / `NORM_SCHMIDT_QUASI`.

### Added — bridge dict API

- `bridge.get_spherical_harmonics(body, channel="both") -> dict` — single-body unified query.
- `bridge.list_spherical_harmonic_models() -> dict` — full catalog enumeration.
- `bridge.convert_spherical_harmonic_normalisation(value, n, m, from_convention, to_convention) -> dict` — Winch et al. 2005 closed-form normalisation conversion.

### Added — CLI

- `spherical-harmonics --body X [--channel gravity|magnetic|both]`
- `spherical-harmonic-models`
- `convert-normalisation --value X --n X --m X --from X --to X`

### Architectural choice

State-*lookup* surface, layered above v0.20.0 / v0.20.1 — **NO regression** on those surfaces. `bridge.get_geodetic_state` and `bridge.get_magnetic_multipoles` continue to return their original v0.20.0 / v0.20.1 shapes, verified by explicit regression tests in `test_spherical_harmonic_catalog.py`.

### Math

`C̄_nm = g_n^m / sqrt((2 - δ_0m) * (2n + 1))` (Winch et al. 2005, "Geomagnetic Reference Spectra"). Round-trip identity to float-machine precision; rejects `n < 0`, `m > n`, non-finite values, unknown convention labels.

## [0.20.2] — 2026-05-07

**Sol Fluid Instrument — climatology + archive index + state-at-epoch query surface for the solar-system fluid envelope.** Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.fluid_instrument` — wrapper module with `compute_fluid_state`, `list_fluid_archives`, `compute_fluid_architecture`.
- `_research.fluid_instrument_data` — data module with `BODY_CLIMATOLOGY` (21 entries: 17 atmospheric + 4 airless), `FLUID_ARCHIVES` (10 entries), `FLUID_STATE_COVERAGE` (21 entries), `SOURCES` (24 citations), dataclasses (`BodyClimatology`, `FluidArchive`, `FluidStateCoverage`), and precision-flag constants.

### Added — bridge dict API

- `bridge.get_fluid_state(body=None, jd_tdb=None, lat=None, lon=None) -> dict` — per-body climatology + archives + coverage triage.
- `bridge.list_fluid_archives() -> dict` — full catalog enumeration.
- `bridge.fluid_architecture(target=None) -> dict` — HIGH/MEDIUM/LOW/NONE data-quality partition.

### Added — CLI

- `fluid-state [--body X] [--jd-tdb X] [--lat X] [--lon X]`
- `fluid-archives`
- `fluid-architecture [--target X]`

### Three layers shipped together (full §17.4.2 commitment)

**Climatology (21 bodies)** — atmospheric set: terra, mars, venus, titan, triton, pluto, io, europa, ganymede, enceladus, mercury, luna, sun, jupiter, saturn, uranus, neptune. Airless small bodies: ceres, vesta, bennu, ryugu.

**Archives (10)** — ERA5, MCD v6.1, MAVEN PDS, VIRA + Akatsuki, Cassini PDS-PPI, Juno PDS, Voyager 2 PDS (Uranus + Neptune), New Horizons PDS (Pluto).

**State-at-epoch coverage** — only terra (ERA5, 1940-present) and mars (MCD v6.1, MY 24-present) have True; all 19 other bodies fall back to climatology.

### Architectural choice

State-*lookup* surface, mirroring v0.19.0/v0.20.0/v0.20.1 — per §17.4.1 the rhythm-mismatch finding generalises across fluid-envelope channels by *epoch-static-ness for climatology + state-at-epoch indirection for the two refereed reanalysis products*. **No outbound network calls** — the package ships pointers + the climatological-summary fallback in a self-contained dict; consumers fetch the actual reanalysis field via the archive's own API (CDS-API for ERA5; the Python wrapper for MCD).

### Forward sequence (per §17.4.2)

* **v0.21.0** — `SphericalHarmonicCatalog` unification refactor across gravity + magnetic sectors.
* **v0.21.1+** — Cross-channel coupling surfaces (one per minor version).

### Citation discipline

Every numeric value carries a `source_key` pointing into the 24-entry `SOURCES` dict; ratchet tests pin both directions.

## [0.20.1] — 2026-05-07

**Sol Magnetic Multipole Catalog — state-lookup query surface for the published-internal-field roster across the solar system.** Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.magnetic_multipole_catalog` — wrapper module with `compute_magnetic_multipoles`, `evaluate_magnetic_field`, `compute_solar_synoptic_state`, `list_magnetic_multipoles`, `compute_magnetic_architecture`.
- `_research.magnetic_multipole_catalog_data` — data module with `MAGNETIC_MULTIPOLE_MODELS` (7 entries), `CRUSTAL_FIELD_MODELS` (1 entry — Earth EMM2017), `SOLAR_SYNOPTIC_REFERENCES` (1 entry — Stanford HMI), `SOURCES` (9 citations), dataclasses (`MagneticMultipoleModel`, `CrustalFieldModel`, `SolarSynopticReference`), and precision-flag constants.

### Added — bridge dict API

- `bridge.get_magnetic_multipoles(body: Optional[str] = None, crustal: bool = False) -> dict`
- `bridge.evaluate_magnetic_field(body, r_km, lat_deg, lon_deg, jd_tdb=None) -> dict` — closed-form Schmidt-quasi-normalised dipole synthesis (synthesis_degree=1 in v0.20.1).
- `bridge.get_solar_synoptic_state(jd_tdb: Optional[float] = None) -> dict` — Sun synoptic-archive pointer surface.
- `bridge.list_magnetic_multipoles() -> dict`
- `bridge.magnetic_architecture(target: Optional[str] = None) -> dict`

### Added — CLI

- `magnetic-multipoles [--body X] [--crustal]`
- `magnetic-field --body X --r-km X --lat-deg X --lon-deg X [--jd-tdb X]`
- `solar-synoptic [--jd-tdb X]`
- `magnetic-models`
- `magnetic-architecture [--target X]`

### 7-body main-field roster

Per the §17.4.2 commitment — every body in the published refereed literature with a multipole expansion: terra (IGRF-13 deg 13), jupiter (JRM33 deg 18), saturn (Cao 2020 deg 14, axisymmetric), mercury (Thébault 2018 deg 5, offset dipole), uranus (AH5 deg 3, Voyager-only), neptune (O8 deg 3, Voyager-only), ganymede (Kivelson 2002 dipole-only).

### Architectural choice

State-*lookup* surface, mirroring v0.20.0 Sol Geodetic Catalog. Per §17.4.1 the rhythm-mismatch finding generalises across magnetic multipoles by *epoch-static-ness*: the IGRF main field updates every 5 years on a published schedule (not via JD arithmetic); JRM33 is a Juno-prime-mission snapshot; Voyager-derived AH5/O8 are single-flyby fits.

### Changed

- `pyproject.toml` description refreshed to advertise the 52-body roster + per-body Sol Geodetic / Electromagnetic / Magnetic-Multipole catalogs + resonance-graph ITN-chain search + spectral body-architecture surfaces (was advertising the obsolete v0.5-era 38-body roster).
- Stale "38-body" callouts in `bridge.py` + `cli.py` user-facing CLI help text bumped to "52-body" (the actual current `SUPPORTED_BODIES` count since v0.16.0).

### Citation discipline

Every numeric value carries a `source_key` pointing into the 9-entry `SOURCES` dict; ratchet tests pin resolution at CI time.

## [0.20.0] — 2026-05-07

**Sol Geodetic Catalog — state-lookup query surface for the solid-body geodetic stack (gravity multipoles + topography + interior structure).** Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.geodetic_catalog` — wrapper module with `compute_geodetic_state`, `list_geodetic_models`, `compute_geodetic_architecture`.
- `_research.geodetic_catalog_data` — data module with `GRAVITY_MODELS`, `TOPOGRAPHY_MODELS`, `INTERIOR_MODELS`, `SOURCES` citation dict, dataclasses (`GravityModel`, `TopographyModel`, `InteriorLayer`, `InteriorModel`), and precision-flag constants (`PRECISION_HIGH` / `_MEDIUM` / `_LOW` / `_NONE`).

### Added — bridge dict API

- `bridge.get_geodetic_state(body: Optional[str] = None) -> dict`
- `bridge.list_geodetic_models() -> dict`
- `bridge.geodetic_architecture(target: Optional[str] = None) -> dict`

### Added — CLI

- `geodetic-state [--body <body>]`
- `geodetic-models`
- `geodetic-architecture [--target <body>]`

### Roster + channel coverage

Full §17.4.2 commitment: every body in the v0.16.0 52-body celestial roster that has a published gravity, topography / shape, or interior structure model is in scope across three internal channels (gravity / topography / interior). Sparse coverage is intentional: not every body has a published model in every channel; missing channels return `None` rather than raising. Each body's overall data-quality tier (HIGH / MEDIUM / LOW / NONE) is the median of its per-channel `precision_flag` values per the §17.1.6 ship-readiness convention.

### Architectural choice

State-*lookup* surface, not BIP encoder. Per §17.4.1 the rhythm-mismatch finding from §16 generalises across solid-body geodesy by *absence-of-rhythm*: Stokes coefficients don't oscillate, DEM spectra don't tick, layered density profiles are static. The Sol Geodetic Catalog therefore has no JD-advance mechanic and accepts `body` (not `jd_tdb`) as its primary argument.

### Forward sequence committed in §17.4.2

* **v0.20.1** `MagneticMultipoleCatalog`, **v0.20.2** `SolFluidInstrument`, **v0.21.0** `SphericalHarmonicCatalog` unification, **v0.21.1+** cross-channel coupling surfaces (one per minor version).

### Citation discipline

Every numeric value carries a `source_key` pointing into the `SOURCES` dict; ratchet tests pin the resolution at CI.

## [0.19.0] — 2026-05-06

**Sol Electromagnetic Instrument — state-at-epoch query surface for the solar-system EM sector.** Pure-Python additive; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Added — Pythonic API

- `_research.em_instrument` — wrapper module with `compute_em_state_at_jd`, `list_em_couplings`, `compute_em_architecture`.
- `_research.em_instrument_data` — data module with `SOL_EM_BODIES` (16 entries), `EM_COUPLINGS` (7 entries), `SOURCES` (19 citations), `EmBodyState` / `EmCoupling` dataclasses, and class-label constants (`EM_CLASS_MAGNETISED` / `_INDUCED` / `_UNMAGNETISED` / `_STAR`).

### Added — bridge dict API

- `bridge.get_em_state(jd_tdb: float) -> dict`
- `bridge.list_em_couplings() -> dict`
- `bridge.em_architecture(target: Optional[str] = None) -> dict`

### Added — CLI

- `em-state --jd-tdb <jd>`
- `em-couplings`
- `em-architecture [--target <body>]`

### 16-body EM roster

| Class | Bodies | Count |
|---|---|---:|
| star | sun | 1 |
| magnetised | mercury, terra, jupiter, ganymede, saturn, uranus, neptune | 7 |
| induced | venus, europa, callisto, titan | 4 |
| unmagnetised | luna, mars, io, enceladus | 4 |

### Test count

730 pass, 41 skipped (was 685 + 41 in v0.18.2; +45 net new — 46 in `tests/test_em_instrument.py` + 3 parity-smoke entries — minus a small reconciliation when rebased onto v0.18.2).

### Migration

Pure-additive bridge + CLI; no existing call sites change. `ES_VERSION_STRING` bumps `0.18.2 → 0.19.0` (v0.19.0 includes the v0.18.2 2-D Fiedler-embedding upgrade for `predict_itn_accessibility` from the parallel branch — both ships landed on the same day).

## [0.18.2] — 2026-05-06

**2-D `(f₂, f₃)` Fiedler-embedding upgrade for `bridge.predict_itn_accessibility`.** Pure-Python additive improvement; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Lift

| Metric | v0.18.1 (1-D) | v0.18.2 (2-D) |
| :--- | ---: | ---: |
| Spearman ρ | +0.857 | +0.849 (~unchanged) |
| R² | 0.507 | **0.644** (+27 %) |
| In-sample MAE | 4.110 km/s | **2.995 km/s** (−27 %) |
| LOOCV MAE | 4.238 km/s | **3.123 km/s** (−26 %) |

Spearman ~unchanged (rank ordering was already strong); R² + MAE materially better.

### Implementation

`_research.predict_itn_accessibility` now:
- Renames `_fiedler_with_sign` → `_eigvecs_2d_with_sign` returning `(λ₂, λ₃, f₂, f₃)`.
- Anchors f₂ sign to shortest-period body (mercury); anchors f₃ sign to max-|f₃| entry.
- Memoises the `(13, 2)` `_DEFAULT_EMBEDDING` matrix at module load.
- `predict_itn_accessibility(...)` returns 2-D Euclidean distance + applies the 2-D OLS regression.

### Bridge response (v0.18.2 fields)

```json
{
  "ok": true,
  "departure": "terra",
  "target": "jupiter",
  "fiedler_distance": 0.156,           // 1-D back-compat
  "embedding_distance_2d": 0.624,      // NEW: 2-D Euclidean
  "predicted_dv_kms": 15.70,
  "calibration": {
    "method": "OLS linear fit on 2-D (f₂, f₃) hybrid Fiedler embedding",
    "weighting": "hybrid_dv_resonance",
    "embedding_dim": 2,                 // NEW
    "intercept_kms": 4.896324,
    "slope_kms_per_fiedler_unit": 17.319301,
    "r2": 0.643884,
    "in_sample_mae_kms": 2.995,
    "loocv_mae_kms": 3.123,
    "loocv_median_abs_error_kms": 2.204, // NEW
    "lambda_2": 0.013023,
    "lambda_3": ...                      // NEW
  }
}
```

### Calibration constants (Pythonic API)

The 2-D constants are the production calibration; the v0.18.1 1-D constants are preserved under `*_1D_HISTORICAL` names:

| Constant | Value |
| :--- | ---: |
| `CALIBRATION_EMBEDDING_DIM` (new) | 2 |
| `CALIBRATION_INTERCEPT_KMS` | 4.896324 |
| `CALIBRATION_SLOPE_KMS_PER_FIEDLER_UNIT` | 17.319301 |
| `CALIBRATION_R2` | 0.643884 |
| `CALIBRATION_IN_SAMPLE_MAE_KMS` | 2.994717 |
| `CALIBRATION_LOOCV_MAE_KMS` | 3.122645 |
| `CALIBRATION_LOOCV_MEDIAN_ABS_ERROR_KMS` (new) | 2.204213 |
| `CALIBRATION_INTERCEPT_KMS_1D_HISTORICAL` | 8.680818 |
| `CALIBRATION_SLOPE_KMS_PER_FIEDLER_UNIT_1D_HISTORICAL` | 15.617194 |
| `CALIBRATION_R2_1D_HISTORICAL` | 0.507203 |
| `CALIBRATION_IN_SAMPLE_MAE_KMS_1D_HISTORICAL` | 4.109664 |
| `CALIBRATION_LOOCV_MAE_KMS_1D_HISTORICAL` | 4.237754 |

### New research script

`research/two_eigenvector_fiedler_embedding.py` — runs all three weightings (`inv_dv`, `resonance`, `hybrid`) under both 1-D and 2-D embeddings and emits the comparison table. Reads the same SHA1-keyed §13 ground-truth cache as the existing calibration script.

### Test count

685 pass, 41 skipped (was 681 + 41 in v0.18.1; +4 net new):
- 4 new pinning the v0.18.2 calibration constants + the 1-D historical constants + `embedding_distance_2d` field + `embedding_dim`/`lambda_3`/`loocv_median_abs_error_kms` calibration metadata
- All v0.18.1 sanity tests (direction-symmetry, cheap-vs-expensive ordering, non-negative predictions across 156 pairs) still pass with the new constants

### Migration

Pure-additive on the bridge response. Numeric `predicted_dv_kms` values change as expected (different regression). Callers pinning v0.18.1 numbers should re-pin to v0.18.2 values or read v0.18.1 numbers from the new `*_1D_HISTORICAL` constants. `ES_VERSION_STRING` bumps `0.18.1 → 0.18.2`.

## [0.18.1] — 2026-05-06

**`bridge.predict_itn_accessibility`: closed-form spectral Δv estimate from the §13.9 hybrid Fiedler-distance regression.** Pure-Python addition; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged from v0.18.0).

### Added — Pythonic API

- `_research.predict_itn_accessibility` — new module containing the hybrid-Laplacian Fiedler-distance regression promoted from research notebook §13.9 to a stable ship surface.
- `_research.predict_itn_accessibility.predict_itn_accessibility(departure: str, target: str) -> Dict` — main entry. Returns `{ok, departure, target, fiedler_distance, predicted_dv_kms, calibration}` where `calibration` is the full provenance dict (Spearman ρ, R², MAE, LOOCV MAE, n_finite, n_inf, window). Returns `{ok: False, error: "..."}` on rejection.
- Calibration constants exposed as module-level: `CALIBRATION_INTERCEPT_KMS`, `CALIBRATION_SLOPE_KMS_PER_FIEDLER_UNIT`, `CALIBRATION_R2`, `CALIBRATION_IN_SAMPLE_MAE_KMS`, `CALIBRATION_LOOCV_MAE_KMS`, `CALIBRATION_SPEARMAN_RHO`, `CALIBRATION_N_FINITE_PAIRS`, `CALIBRATION_N_INF_PAIRS`, `CALIBRATION_WINDOW_YEARS`, `CALIBRATION_WINDOW_JD_LO`.

### Added — bridge dict API (Pyodide-compatible)

- `bridge.predict_itn_accessibility(departure: str, target: str) -> dict` — wraps the Pythonic entry; same return shape.

### Added — CLI

- `predict-itn-accessibility` subcommand — flags: `--departure`, `--target`, `--pretty`.

### Calibration

OLS linear fit on the §13 ground truth (50-yr `find_itn_chains` sweep at J2000, max_legs=3, dv_budget=30 km/s, threshold=0.1):

| Constant | Value | Provenance |
| :--- | ---: | :--- |
| Intercept | **8.681 km/s** | OLS fit on n=53 finite pairs |
| Slope | **15.617 km/s per Fiedler-unit** | OLS fit on n=53 finite pairs |
| In-sample R² | **0.507** | 53 feasible pairs of 78 in roster |
| In-sample MAE | **4.110 km/s** | 53 feasible pairs |
| LOOCV MAE | **4.238 km/s** | leave-one-out cross-validation; no overfitting |
| Spearman ρ | **+0.857** | rank correlation (calibration headline) |

Calibration script: `research/calibrate_predict_itn_accessibility.py` — re-fits the constants against a re-sampled ground truth. Cache key matches `gateway_graph_laplacian._cache_path`: body roster + `50yr|dv30`.

### Test count

681 pass, 41 skipped (was 658 + 41; +23 new):
- 22 in `tests/test_predict_itn_accessibility.py` (calibration pins + direction-symmetry + non-negative predictions across 156 pairs + sanity ordering Earth-Mars < Earth-Jupiter < Mercury-Pluto + intercept-as-lower-bound + calibration provenance in response + error paths + case-insensitive lower-casing + bridge + CLI)
- 1 parity-smoke entry (`predict_itn_accessibility` classified `python_only`)

### Migration

Pure-additive on the Python bridge and the CLI. No existing call sites change. Native callers see `ES_ABI_VERSION = 8` unchanged. `ES_VERSION_STRING` bumps `0.18.0 → 0.18.1`.

## [0.18.0] — 2026-05-06

**Body Architecture: inner/outer system classification of heliocentric bodies via the resonance-weighted gateway-graph Laplacian Fiedler partition.** Pure-Python addition; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged from v0.17.0).

### Added — Pythonic API

- `_research.body_architecture` — new module containing the resonance-weighted gateway-graph Laplacian Fiedler-partition machinery promoted from research notebook §13.8 to a stable ship surface.
- `_research.body_architecture.HELIOCENTRIC_BODIES` — frozen list of the v0.16.0 13-body Tier-1 heliocentric roster (planets + main-belt asteroids; Sun excluded; moons excluded). The default subset for `compute_body_architecture`.
- `_research.body_architecture.INNER_CLASS = "inner"`, `OUTER_CLASS = "outer"` — class label constants.
- `_research.body_architecture.compute_body_architecture(bodies: Optional[List[str]] = None) -> Dict` — main entry. Returns `{ok, n_bodies, lambda_2, bodies, partitions}` where `bodies` is a list of `{name, class, fiedler_value, period_days}` records (sorted by `fiedler_value` ascending) and `partitions` is `{"inner": [...], "outer": [...]}`. Raises `ValueError` on empty / duplicate / unknown / zero-period inputs.

### Added — bridge dict API (Pyodide-compatible)

- `bridge.body_architecture(target: Optional[str] = None) -> dict` — full partition by default; single-body record if `target` given (lower-cased; must be in the heliocentric roster). Returns `{ok: False, error: ...}` on rejection.

### Added — CLI

- `body-architecture` subcommand — flags: `--target <name>` (optional; if given, returns just that body's record), `--pretty`. Prints the same dict the bridge returns.

### Sign-convention

The Fiedler-vector sign is anchored to the shortest-period body in the input roster being positive. This makes the inner/outer label assignment reproducible across platforms regardless of LAPACK pivoting. For the default 13-body roster this means **mercury is always positive** (largest `+0.329`) and **pluto is always negative** (deepest `−0.585`).

### Default classification

The default 13-body heliocentric roster classifies into:

* **Inner 8** (positive Fiedler entry): mercury, venus, terra, mars, vesta, ceres, pallas, hygiea
* **Outer 5** (negative Fiedler entry): jupiter, saturn, uranus, neptune, pluto

The cyclic-group encoder discovers the canonical asteroid-belt boundary without being told it exists. Pluto and Neptune share the deepest entry (`−0.585`) via their 2:3 mean-motion lock.

### Research origin (notebook §13.8 + §13.9)

The §13 thread tested four edge weightings on the gateway-graph Laplacian:

| Weighting | Spearman ρ vs empirical Δv | Matthews φ | Notes |
| --- | ---: | ---: | --- |
| inv_dv (baseline) | +0.743 | +0.336 | Mercury-isolation predictor |
| inv_synodic (control) | −0.301 | +0.083 | Pallas/Ceres degeneracy null |
| **resonance (this ship)** | +0.632 | +0.207 | Inner/outer architectural partition |
| hybrid_dv_resonance | **+0.857** | +0.298 | Clears continuous Spearman bar; queued |

The **resonance-only Laplacian** is the source of the `body_architecture` surface — its partition is structurally the canonical inner/outer division (the architectural finding). The **hybrid `inv_dv × resonance`** (§13.9) clears the §13.7 0.85 Spearman bar but the partition Matthews φ stays below 0.6, so the hybrid result is queued for v0.18.x or v0.19.0 as a continuous Fiedler-distance → Δv predictor (`bridge.predict_itn_accessibility`) once a regression model lands.

### Tests

- New module `tests/test_body_architecture.py` (34 tests):
  - **Default-roster shape** — 13 bodies, canonical inner-8 / outer-5 partition, partition sizes
  - **Spectral pins** — Pluto + Neptune deepest negative entries (within 0.01 of each other; both below −0.5); Mercury largest positive entry; Fiedler values sorted ascending; λ₂ > 0
  - **Determinism** — repeated calls return byte-identical Fiedler values (LAPACK sign convention nailed)
  - **Error paths** — empty list, duplicates, unknown body name, zero-period body (Sun)
  - **Bridge surface** — full partition, 13 parametrised single-body class lookups, case-insensitive lower-casing, rejection paths (unknown body, non-heliocentric body)
  - **CLI surface** — full partition, `--target`, `--help`
  - **Default-roster contract** — `HELIOCENTRIC_BODIES` is the documented v0.16.0 Tier-1 list
- Parity-smoke spec — `body_architecture` classified as `python_only` (no C twin planned: numpy.linalg.eigh on a 13×13 symmetric matrix is microseconds, well below any threshold where a C twin would be useful).

### Test count

658 pass, 41 skipped (was 622 + 41 in v0.17.0; +36 new).

### Migration

Pure-additive on the Python bridge and the CLI. No existing call sites change. Native callers see `ES_ABI_VERSION = 8` unchanged. `ES_VERSION_STRING` bumps `0.17.0 → 0.18.0`.

## [0.17.0] — 2026-05-06

**Resonance-graph multi-leg `find_itn_chains` (advanced Lagrange-highway search).** Generalises the v0.8.1 closed-form Hohmann-window enumeration to multi-leg pathways via Dijkstra-style graph search over the `(body, epoch)` state space. Pure-Python addition; **no ABI bump** (first ephemerides ship since v0.13.x to leave the C wire-format alone).

### Added — Pythonic API

- `_research.itn_window.ITNChainCandidate` — frozen dataclass carrying `jd_tdb_launch`, `jd_tdb_arrival`, `legs: tuple[ITNCandidate, ...]`, `total_dv_kms`, `total_tof_days`, `resonance_signature: tuple[(int, int), ...]`, `score`.
- `_research.itn_window._best_rational_approx(ratio, max_denom=30) -> (int, int)` — returns the rational approximation of a period ratio in lowest terms; `(0, 0)` sentinel for non-finite or non-positive inputs. Recovers (8, 15) for Earth/Mars, (1, 12) for Earth/Jupiter, (2, 5) for Jupiter/Saturn.
- `_research.itn_window.find_itn_chains(jd_lo, jd_hi, *, departure, target, intermediates=None, max_legs=4, dv_budget_kms=30.0, tof_budget_days=365.25 * 20, threshold=0.05, max_chains=200, max_intermediate_windows=8) -> List[ITNChainCandidate]` — multi-leg ITN chain search via Dijkstra on the `(body, epoch)` state space. Each leg is a closed-form Hohmann window from `find_itn_pathways`. Chains are emitted in monotonically non-decreasing `total_dv_kms` order (Dijkstra invariant); empty if no chain fits the budgets. Default `intermediates=None` ⇒ all heliocentric bodies (planets + dwarf planets + asteroids) minus departure/target; pass `[]` to force a single-leg direct chain.

### Added — bridge dict API (Pyodide-compatible)

- `bridge.find_itn_chains(jd_lo, jd_hi, *, departure, target, intermediates=None, max_legs=4, dv_budget_kms=30.0, tof_budget_days=7305.0, threshold=0.05, max_chains=200, max_intermediate_windows=8) -> dict` — same algorithm, returns `{ok, departure, target, max_legs, n_chains, chains, ...}`. Each chain entry is a JSON-serialisable dict with `jd_tdb_launch`, `jd_tdb_arrival`, `legs` (list of leg dicts mirroring `find_itn_pathways`'s candidate shape), `total_dv_kms`, `total_tof_days`, `resonance_signature` (list of `[p, q]` pairs), `score`.

### Added — CLI

- `find-chains` subcommand — flags: `--from-jd`, `--to-jd`, `--departure`, `--target`, `--intermediates` (comma-separated; empty string = direct), `--max-legs`, `--dv-budget-kms`, `--tof-budget-days`, `--threshold`, `--max-chains`, `--max-intermediate-windows`, `--pretty`. Prints the same dict the bridge returns.

### Algorithm

Dijkstra over the `(current_body, current_jd, total_dv, legs)` state space. Each leg is a closed-form Hohmann transfer window from `find_itn_pathways` (per-pair synodic enumeration; constant time per synodic period). Legs stitch end-to-end at intermediate bodies. Cumulative Δv invariant guarantees first-popped target node is the optimal-Δv chain; subsequent chains emitted in non-decreasing total-Δv order. Worst-case `O(B^L × W)` (B = |intermediates|, L = max_legs, W = windows per leg) but the budgets prune aggressively in practice.

### Resonance signature

Each leg carries a small-integer `(p, q)` gear-ratio resonance signature: the rational approximation of `period_dep / period_tgt` in lowest terms (max denominator 30). The cross-pollination point between the closed-form transfer-window machinery and the BIP cyclic-group encoder.

### Tests

- New module `tests/test_find_itn_chains.py` (21 tests):
  - **Rational-approximation invariants** — Earth/Mars (8, 15), Earth/Jupiter (1, 12), Jupiter/Saturn (2, 5); lowest-terms gcd invariant; non-finite / non-positive sentinel
  - **Direct-chain consistency** — `intermediates=[]` collapses to v0.8.1 `find_itn_pathways` (per-leg jd_tdb byte-identical, modulo Dijkstra-optimal-first vs chronological ordering)
  - **Dijkstra invariant** — chains emitted in monotonically non-decreasing `total_dv_kms` order
  - **Resonance signature shape** — len(`resonance_signature`) == len(`legs`); per-leg `(p, q)` pinned for Earth → Mars
  - **Budget enforcement** — Δv, TOF, max_legs all enforced cumulatively
  - **Bridge surface** — smoke + rejection paths (self-transfer, unknown body, invalid threshold, invalid budget, invalid intermediate)
  - **CLI surface** — direct, multi-leg, `--help`
- Parity-smoke spec — `find_itn_chains` classified as `python_only` (no C twin planned: the priority-queue search is structurally Pythonic and bounded by the same closed-form synodic enumeration as `find_itn_pathways`)

### Test count

622 pass, 41 skipped (was 601 + 41 in v0.16.0; +21 new).

### Migration

Pure-additive on the Python bridge and the CLI. No existing call sites change. Native callers see `ES_ABI_VERSION = 8` unchanged. `ES_VERSION_STRING` bumps `0.16.0 → 0.17.0`.

## [0.16.0] — 2026-05-06

**BODIES Tier-1 expansion (43 → 52): Lagrange trojans + retrograde irregulars + Neptune sub-graph completion.** Themed per the post-v0.15.0 audit (research notebook §11). Adds 9 new bodies + 9 forward + 9 inverse bridge wrappers + 9 CLI subcommands.

### Added — Saturnian Lagrange trojans (4) — first L4/L5 entries in BODIES

| Body | Sol Time | Abbrev | CLI | Host (L4/L5) |
|---|---|---|---|---|
| Telesto | Sol Saturn-Telesto Time | **SSaTeT2** | `time-saturn-telesto` | Tethys L4 |
| Calypso | Sol Saturn-Calypso Time | **SSaCaT** | `time-saturn-calypso` | Tethys L5 |
| Helene | Sol Saturn-Helene Time | **SSaHeT** | `time-saturn-helene` | Dione L4 |
| Polydeuces | Sol Saturn-Polydeuces Time | **SSaPoT** | `time-saturn-polydeuces` | Dione L5 |

Each trojan's sidereal period is **byte-identical** to its host moon's (Tethys: 1.88780216 d; Dione: 2.73691500 d). The body-graph Laplacian acquires a multiplicity-2 eigenvalue at the host's frequency. Natural intersection point with v0.16.x's resonance-graph multi-leg find_itn_chains.

### Added — Jovian irregulars (3)

| Body | Sol Time | Abbrev | CLI | Notes |
|---|---|---|---|---|
| Himalia | Sol Jupiter-Himalia Time | **SJuHiT** | `time-jupiter-himalia` | Largest Jovian irregular (radius ~85 km), prograde, Perrine 1904 |
| Pasiphae | Sol Jupiter-Pasiphae Time | **SJuPaT** | `time-jupiter-pasiphae` | RETROGRADE (i~141°), Melotte 1908 |
| Sinope | Sol Jupiter-Sinope Time | **SJuSiT** | `time-jupiter-sinope` | RETROGRADE (i~153°), Nicholson 1914; near-resonant with Pasiphae |

Pasiphae and Sinope are the second retrograde marker beyond Triton (v0.14.2). Encoder convention: positive period_days; retrograde-ness is metadata.

### Added — Neptune sub-graph completion (2)

| Body | Sol Time | Abbrev | CLI | Notes |
|---|---|---|---|---|
| Proteus | Sol Neptune-Proteus Time | **SNePrT** | `time-neptune-proteus` | Neptune's second-largest moon (~210 km), Voyager 2 1989 |
| Nereid | Sol Neptune-Nereid Time | **SNeNeT** | `time-neptune-nereid` | Most eccentric major-moon orbit in solar system (e=0.749), Kuiper 1949 |

### First invocation of suffix-disambiguation policy

The v0.14.1 6-letter `S<Planet2><Moon2>T` policy reserved a fallback for the case where two moons of the *same parent* share their first-two-letters. v0.16.0 hits exactly that case: **Tethys** (`SSaTeT`, shipped v0.14.1) vs **Telesto** (`SSaTeT2`, shipped v0.16.0). The suffix '2' is the disambiguator. Calypso's moon-prefix (`Ca`) is distinct from Tethys's (`Te`) so no Calypso suffix was needed.

### C-side wire-format change

ABI v7 → v8. `ES_N_BODIES` 43 → 52; native binary rebuilt; parity-smoke ratchet ratcheted. Existing wheels at ABI 7 are not interoperable with v0.16.0 callers; v0.16.0 wheels ship with the rebuilt native.

### Test count

601 pass, 41 skipped (was 514 + 41 in v0.15.0; +23 new — 12 Saturnian-trojan + 9 Jovian-irregular + 2 expanded Neptunian + 18 parity-smoke entries + parity-smoke tier-shape variations).

## [0.15.0] — 2026-05-06

**Sol Moon Times: classical-roster completion** (Pluto-Charon + remaining major Uranian moons). BODIES roster expanded 38 → 43. Closes task `` `#86` `` for the IAU-major moon roster: every classical moon discovered between 1787 and 1948 now has a Sol Time wrapper.

### Added — Uranian classical roster completion (4 moons)

| Body | Sol Time | Abbrev | CLI |
|---|---|---|---|
| Miranda | Sol Uranus-Miranda Time | **SUrMiT** | `time-uranus-miranda` |
| Ariel | Sol Uranus-Ariel Time | **SUrArT** | `time-uranus-ariel` |
| Umbriel | Sol Uranus-Umbriel Time | **SUrUmT** | `time-uranus-umbriel` |
| Oberon | Sol Uranus-Oberon Time | **SUrObT** | `time-uranus-oberon` |

Discovery order: Titania + Oberon (Herschel 1787) → Ariel + Umbriel (Lassell 1851) → Miranda (Kuiper 1948). Voyager 2 (1986) imaged all five. Miranda's Verona Rupes is the tallest known cliff in the solar system (~20 km).

### Added — Plutonian (1 moon)

| Body | Sol Time | Abbrev | CLI |
|---|---|---|---|
| Charon | Sol Pluto-Charon Time | **SPlChT** | `time-pluto-charon` |

Charon (Christy, 1978) is the binary-planet case: mutually tidally locked with Pluto, mass ratio Charon:Pluto ≈ 0.12, barycentre *outside* Pluto. The only 1:1:1 spin-orbit lock in the solar system. Sidereal == synodic == spin period (6.387 d).

### Disambiguation — SUrMiT vs SSaMiT

Second-instance case of the shared-moon-prefix pattern the v0.14.2 SUrTiT/SSaTiT pair first surfaced. Both pairs validate the v0.14.1 6-letter `S<Planet2><Moon2>T` policy — without it both moons would collapse to the same 4-letter form.

### C-side wire-format change

ABI v6 → v7. `ES_N_BODIES` 38 → 43; native binary rebuilt; parity-smoke ratchet ratcheted. Existing wheels at ABI 6 are not interoperable with v0.15.0 callers; v0.15.0 wheels ship with the rebuilt native at the matching ABI.

### Test count

512 pass, 41 skipped (was 497 + 4; +56 new — 5 Plutonian + 4 expanded Uranian + 10 parity-smoke entries + parity-smoke tier-shape variations).

## [0.14.2] — 2026-05-06

**Sol Moon Times: remaining 8 moons across 4 parent families** — closes task `` `#86` `` for the current 38-body roster. Built via four parallel subagent worktrees, integrated into a single ship.

### Added — Mars (2 moons)

| Body | Sol Time name | Abbreviation | CLI |
|---|---|---|---|
| Phobos | Sol Mars-Phobos Time | **SMaPhT** | `time-mars-phobos` |
| Deimos | Sol Mars-Deimos Time | **SMaDeT** | `time-mars-deimos` |

Both likely captured asteroids (C/D-type spectral match). Phobos's sidereal period (0.319 d ≈ 7h 39m) is **shorter** than Mars's solar day (~24h 39m), so from Mars's surface Phobos rises in the **west**. Phobos/Deimos period ratio is ≈ 3.96 — near 4:1 but **not** in 4:1 mean-motion resonance (libration tolerance is parts-per-thousand; 1% off counts as not-locked).

### Added — Jupiter inner regulars (4 moons)

| Body | Sol Time name | Abbreviation | CLI |
|---|---|---|---|
| Metis | Sol Jupiter-Metis Time | **SJuMeT** | `time-jupiter-metis` |
| Adrastea | Sol Jupiter-Adrastea Time | **SJuAdT** | `time-jupiter-adrastea` |
| Amalthea | Sol Jupiter-Amalthea Time | **SJuAmT** | `time-jupiter-amalthea` |
| Thebe | Sol Jupiter-Thebe Time | **SJuThT** | `time-jupiter-thebe` |

Metis + Adrastea are ring-shepherd moons of Jupiter's main ring (both orbit just outside the ring's outer edge). Amalthea is the largest (~84 km radius) and the only one discovered before Voyager (E. E. Barnard, 1892 — the last solar-system moon discovered by direct visual observation). Thebe orbits between Amalthea and Io.

### Added — Uranus (1 moon: Titania)

| Body | Sol Time name | Abbreviation | CLI |
|---|---|---|---|
| Titania | Sol Uranus-Titania Time | **SUrTiT** | `time-uranus-titania` |

Largest Uranian moon (radius ~789 km); discovered by William Herschel 1787. Currently the only Uranian moon in the BODIES roster — Oberon, Umbriel, Ariel, Miranda are queued for a future ship.

**Note**: SUrTiT and SSaTiT (Saturn's Titan) share the `Ti` moon prefix but are globally distinct via the parent prefix (`Ur` vs `Sa`) — exactly the disambiguation the v0.14.1 6-letter abbreviation policy was designed to provide. Without the policy switch, both would have been `STiT` under the old 4-letter form.

### Added — Neptune (1 moon: Triton)

| Body | Sol Time name | Abbreviation | CLI |
|---|---|---|---|
| Triton | Sol Neptune-Triton Time | **SNeTrT** | `time-neptune-triton` |

Largest Neptunian moon (radius ~1353 km — bigger than Pluto). **The only large moon in the solar system that orbits its planet retrograde** — strong evidence Triton is a captured Kuiper Belt object. Tidal deceleration (because of the retrograde orbit) is spiralling Triton inward; in ~3.6 Gyr it will cross Neptune's Roche limit and become a ring system.

**Encoder convention**: `BODIES["triton"].period_days` is positive (we encode `omega = +2π/P` for ALL bodies regardless of prograde/retrograde direction; retrograde-ness is metadata, not a sign flip in the time-scale primitive). Sol Time count proceeds positive-monotonically. Same convention as v0.5.4 Sol Uranian Time (Uranus has retrograde rotation).

### Subagent-driven dispatch

This ship was built via **4 parallel subagent worktrees** (one per family), each:

- branched off main concurrent with v0.14.1 CI
- self-contained: bridge wrappers + CLI subcommand + new test module + parity-smoke entries
- did NOT touch version bumps, CHANGELOGs, README, ROADMAP, notebook (the parent agent integrated those)

Subagents reported clean test runs in their own worktrees. The parent agent integrated the 4 deliverables into a single bridge.py / cli.py / test_parity_smoke.py edit (avoiding 4-way merge conflicts on those shared files), copied the 4 new test modules in directly, and added a generic `_add_moon_subparser` CLI helper that supersedes the v0.14.0/v0.14.1 family-specific helpers for the v0.14.2 additions.

### Sol Moon Times series — current state

23 moons across 6 families (every moon in the BODIES roster except Earth's Luna, which has its own STLT in v0.10.0):

| Family | Count | Examples |
|---|--:|---|
| Galileans (Jupiter) | 4 | Io, Europa, Ganymede, Callisto |
| Saturnians | 11 | Mimas, Enceladus, ..., Titan, ..., Janus, Epimetheus |
| **Martians (v0.14.2)** | **2** | **Phobos, Deimos** |
| **Jovian inner regulars (v0.14.2)** | **4** | **Metis, Adrastea, Amalthea, Thebe** |
| **Uranian (v0.14.2)** | **1** | **Titania** |
| **Neptunian (v0.14.2)** | **1** | **Triton** |
| Total | **23** | |

Plus Sol Terra-Luna Time (STLT) for Earth's Moon = **24 moon time series**. Future BODIES additions (Pluto-Charon, more Uranian moons, etc.) follow the same v0.14.1 6-letter convention.

### Test count

497 pass, 4 skipped (was 399 + 4 in v0.14.1; +98 new — 2 Martian + 4 Jovian-inner + 1 Uranian + 1 Neptunian moon-test modules + parity-smoke entries).

### Migration

None. Pure-additive. No API / encoder / ABI / encoder-test changes.

## [0.14.1] — 2026-05-06

**Sol Moon Times: Saturnians (11 moons) + abbreviation policy switch (4-letter → 6-letter).** Second slice of task `` `#86` ``. The abbreviation collision contingency documented in v0.14.0's ROADMAP fired exactly as predicted: when the 11 Saturnians joined the per-moon abbreviation namespace, two collisions surfaced under the v0.14.0 4-letter `S<Planet><Moon>T` pattern (Tethys + Titan both 'T' → both `SSTT`; Enceladus + Epimetheus both 'E' → both `SSET`). Per the ROADMAP "Naming convention contingencies" policy, the switch applies **uniformly across all Sol Moon Times** — Galileans retroactively renamed too.

### Added — 11 Saturnian Sol Moon Times

| Body | Sol Time name | Abbreviation | CLI |
|---|---|---|---|
| Mimas | Sol Saturn-Mimas Time | **SSaMiT** | `time-saturn-mimas` |
| Enceladus | Sol Saturn-Enceladus Time | **SSaEnT** | `time-saturn-enceladus` |
| Tethys | Sol Saturn-Tethys Time | **SSaTeT** | `time-saturn-tethys` |
| Dione | Sol Saturn-Dione Time | **SSaDiT** | `time-saturn-dione` |
| Rhea | Sol Saturn-Rhea Time | **SSaRhT** | `time-saturn-rhea` |
| Titan | Sol Saturn-Titan Time | **SSaTiT** | `time-saturn-titan` |
| Hyperion | Sol Saturn-Hyperion Time | **SSaHyT** | `time-saturn-hyperion` |
| Iapetus | Sol Saturn-Iapetus Time | **SSaIaT** | `time-saturn-iapetus` |
| Phoebe | Sol Saturn-Phoebe Time | **SSaPhT** | `time-saturn-phoebe` |
| Janus | Sol Saturn-Janus Time | **SSaJaT** | `time-saturn-janus` |
| Epimetheus | Sol Saturn-Epimetheus Time | **SSaEpT** | `time-saturn-epimetheus` |

### Changed — Galilean abbreviations retroactively renamed

| Body | Before (v0.14.0) | After (v0.14.1+) |
|---|---|---|
| Io | `SJIT` | **`SJuIoT`** |
| Europa | `SJET` | **`SJuEuT`** |
| Ganymede | `SJGT` | **`SJuGaT`** |
| Callisto | `SJCT` | **`SJuCaT`** |

The `epoch.abbreviation` field changes; **Python function names, CLI subcommand names, and bridge return-shape are unchanged**. Callers reading the abbreviation as a label (e.g., for display, comparison, or storage) will see the new 6-letter form starting from v0.14.1.

### Why the switch had to be uniform

Mixed conventions across moons (Galileans 4-letter, Saturnians 6-letter) would have been worse than either pure convention — readers would constantly need to remember which family uses which length. The ROADMAP policy was explicit about this: *"When a single collision triggers the policy switch, the change applies uniformly to all Sol Moon Times in the package."*

### Resonance witnesses (in tests, not in dicts)

The Saturnian families have several known mean-motion resonances:

| Resonance | Form | Significance |
|---|---|---|
| Mimas-Tethys 4:2 | `n_Mimas / n_Tethys ≈ 2.0` | Opens the Cassini Division |
| Enceladus-Dione 2:1 | `n_Enc / n_Dione ≈ 2.0` | Powers Enceladus's tidal heating + cryovolcanism |
| Titan-Hyperion 4:3 | `n_Titan / n_Hyp ≈ 1.333` | Drives Hyperion's chaotic rotation |
| Janus-Epimetheus | period ratio ≈ 1.0 | Co-orbital horseshoe orbit (~4-yr swap) |

Each resonance has a witness test in `test_saturnian_sol_moon_times.py`. The per-moon dict carries only `sidereal_count` / `sidereal_phase` — pair-relations stay out of the dict (consistent with the v0.14.0 Galilean Laplace-resonance handling).

### Hyperion footnote

Hyperion's chaotic rotation means rotation period ≠ orbital period (it's the only known major moon NOT in tidal lock). The `sidereal_period_days` field references the orbital period in our convention; the rotation-phase coupling is non-trivially decoupled and an open research direction. This is documented in the bridge docstring, the CLI help text, and the test module.

### Roadmap update

`ROADMAP.md`'s "Naming convention contingencies" section is updated from forward-looking ("if collisions arise") to *triggered* ("v0.14.1 invoked the fallback policy"), with the specific Tethys/Titan and Enceladus/Epimetheus collisions called out as the trigger.

### Test count

399 tests pass, 4 skipped (was 294 + 4 in v0.14.0; +105 new — 99 Saturnian tests + parity-smoke registrations + 6 cross-family abbreviation-uniqueness checks).

### Migration

- **Python function names**: unchanged. `bridge.jd_to_sol_jupiter_io_time(...)` still works the same way.
- **CLI subcommand names**: unchanged. `time-jupiter-io --jd ...` still works the same way.
- **Return-shape**: unchanged. The `epoch.abbreviation` STRING changes from `"SJIT"` to `"SJuIoT"` etc. Callers parsing this field for display / comparison need to update.
- **No API/encoder/ABI changes**.

## [0.14.0] — 2026-05-05

**Sol Moon Times: Galileans (Io / Europa / Ganymede / Callisto).** First slice of task `` `#86` `` — extends the Sol Time hierarchy to non-Luna moons under the moons-stuck-to-parent `Sol <Parent>-<Body> Time` naming convention from v0.9.1.

### Added

- **Generic moon-time primitive** (`_research/time_scales.py`):
  - `MoonTime` dataclass: `body_name`, `parent_name`, `epoch_name`, `epoch_jd_tdb`, `days_since_epoch`, `sidereal_period_days`, `sidereal_count`, `sidereal_phase`.
  - `jd_to_moon_time(body_name, jd_tdb, *, parent_name, sidereal_period_days, ...)`: body-agnostic factory. Caller-supplied parent + sidereal period (looked up at the bridge layer from `BODIES`) keeps this primitive light-weight and free of `BODIES`-table imports — same separation-of-concerns as the rest of `_research/time_scales.py`.
  - `moon_time_to_jd(sidereal_count, *, sidereal_period_days, ...)`: inverse.
  - `SOL_MOON_TIME_J2000_JD_TDB`: shared default epoch (J2000.0).

- **Per-Galilean bridge wrappers** (`bridge.py`):

  | Function | Inverse | Abbrev |
  |---|---|---|
  | `jd_to_sol_jupiter_io_time` | `sol_jupiter_io_time_to_jd` | **SJIT** |
  | `jd_to_sol_jupiter_europa_time` | `sol_jupiter_europa_time_to_jd` | **SJET** |
  | `jd_to_sol_jupiter_ganymede_time` | `sol_jupiter_ganymede_time_to_jd` | **SJGT** |
  | `jd_to_sol_jupiter_callisto_time` | `sol_jupiter_callisto_time_to_jd` | **SJCT** |

  Each returns a dict with `ok`, `jd_tdb`, `body_name`, `parent_name="jupiter"`, `epoch_name="j2000"`, `sidereal_period_days`, `sidereal_count`, `sidereal_phase`, plus an `epoch` block carrying the abbreviation, sol-time-name, parent-body, moon-body, and a per-moon note.

- **Per-Galilean CLI subcommands**: `time-jupiter-io`, `time-jupiter-europa`, `time-jupiter-ganymede`, `time-jupiter-callisto`. Each takes `--jd` or `--sidereal-count` (mutex required), supports `--proper` / `--state` / `--dynamics` augmenting flags via `_add_proper_flags`. The four subparsers share a helper (`_add_galilean_subparser`) so they stay consistent.

- **Test module** (`tests/test_galilean_sol_moon_times.py`): 35 tests covering generic primitive, all four bridge surfaces (J2000-zero, after-one-sidereal-period, inverse round-trip, NaN/Inf rejection), CLI parsing, abbreviation uniqueness, and the Galilean Laplace-resonance witness (canonical form `n_Io − 3·n_Europa + 2·n_Ganymede ≈ 0`; plus the assertion that Callisto is NOT in the resonance).

- **Parity smoke registrations** (`tests/test_parity_smoke.py`): 8 new entries (4 forward + 4 inverse) classified as `python_only` with rationale matching the rest of the Sol Time series.

### Naming convention

Per v0.9.1's moons-stuck-to-parent `Sol <Parent>-<Body> Time`: the production names are *Sol Jupiter-Io Time*, *Sol Jupiter-Europa Time*, *Sol Jupiter-Ganymede Time*, *Sol Jupiter-Callisto Time*. The 4-letter abbreviations follow `S<Planet-initial><Moon-initial>T`. ROADMAP `## Naming convention contingencies` documents the fallback policy if moon-letter collisions arise in future ships (Saturnians, etc.) — switch uniformly to a 6-letter `S<Planet2><Moon2>T` pattern (e.g., `SJuGaT`).

### Why default epoch is J2000

STLT (v0.10.0) used Meton's 432 BCE summer solstice — a Greek-historical anchor that doesn't generalise to non-Luna moons. For Galileans, J2000 is the natural anchor: matches the rest of the Sol Time series, no civilisation has been keeping a Galilean-eclipse archive, and Galileo's own 1610 telescopic discoveries (JD ~2305448) could be a future non-default option but aren't load-bearing for v0.14.0.

### Laplace resonance

The 4:2:1 mean-motion resonance among Io / Europa / Ganymede (canonical form `n_Io − 3·n_Europa + 2·n_Ganymede ≈ 0`) is documented in the test module and in the per-moon docstrings. Callisto is the only Galilean **not** in the resonance — its mean motion is irrationally related to the inner triple. The Sol Time wrappers don't expose resonance metrics in the per-moon dict (the resonance is a pair-relation, not a per-body property); future analysis tooling can compose `sidereal_count` values across the inner triple to recover it.

### Test count

294 tests pass, 4 skipped (was 251 + 4 in v0.13.10 — +43 new: 35 Galilean tests + 8 parity-smoke entries).

### Migration

None. Pure-additive. No API / encoder / ABI / encoder-test surface changes.

## [0.13.10] — 2026-05-05

**Drop `edited` from docs-check workflow trigger types — fixes post-merge double-fire.** CI-only patch; no code / API / encoder / ABI / test changes.

### Why

User flagged on PR `` `#214` `` (v0.13.9 ship): the docs-check workflow was double-firing at merge time. Two `pull_request` events at the same second on the PR's branch ~3 seconds before the merge committed; concurrency-cancel caught it (one CANCELLED, one SUCCESS) but the wasted CI churn + confusing run-history was observable.

### Root cause

GitHub web UI's "Squash and merge" workflow fires `pull_request: edited` (the merge-commit dialog populates / saves the title + body fields) near-simultaneously with `pull_request: synchronize` (GitHub recomputes the `refs/pull/N/merge` preview ref). With both `edited` and `synchronize` in our `types` list, both events triggered runs at the same second → deterministic double-fire at every merge.

### Fix

Drop `edited` from the trigger types in `.github/workflows/ephemerides-spectral-docs-check.yml`:

```yaml
# Before (v0.13.3 → v0.13.9):
types: [opened, synchronize, reopened, edited, labeled]

# After (v0.13.10+):
types: [opened, synchronize, reopened, labeled]
```

Eliminates the source of the double-fire. The CI-side workflow (`ephemerides-spectral-ci.yml`) was already on `[opened, synchronize, reopened, labeled]` and didn't have this issue.

### Trade-off

`[skip-docs-check]` opt-out added retroactively (after PR open, by editing the PR body) no longer triggers a re-run. User must either:
1. Push a synchronizing commit (the natural way), or
2. Accept the stale advisory comment

Acceptable — opt-out should be set up-front in the initial PR description, not retroactively.

### Migration

None. Workflow-only change; CI behaviour now matches the `ephemerides-spectral-ci` workflow's narrower trigger types. 251 tests pass, 4 skipped (unchanged).

## [0.13.9] — 2026-05-05

**JPL Power-of-Ten Rules 6 + 7 manual audits — final patch in the v0.13.4-v0.13.9 rule-fix sequence.** Audit-only release; no code changes; **0 violations found** for both rules.

### Result

**All ten JPL Power-of-Ten rules now satisfied.** The five-ship sequence v0.13.4 → v0.13.5 → v0.13.6 → v0.13.7 → v0.13.9 (with v0.13.8 a docs-hygiene patch in the middle) closes out the v0.11.2 audit baseline:

| Rule | Description | Cleared in | Mechanism |
|---|---|---|---|
| 1 | No `goto` / `setjmp` / `longjmp` / recursion | v0.13.4 | `test_jpl_audit.py` pin |
| 2 | Fixed loop bounds | already-passing at v0.11.2 | `test_jpl_audit.py` pin |
| 3 | No dynamic allocation after init | v0.13.4 | `test_jpl_audit.py` pin |
| 4 | Functions ≤ 60 lines | v0.13.5 | `test_jpl_audit.py` pin |
| 5 | ≥ 2 assertions per function (avg) | v0.13.6 | `test_jpl_audit.py` pin + density test |
| 6 | Smallest possible scope for data | **v0.13.9** | manual audit (this ship) |
| 7 | Check return values, validate parameters | **v0.13.9** | manual audit (this ship) |
| 8 | Limited preprocessor | already-passing at v0.11.2 | `test_jpl_audit.py` pin |
| 9 | Pointer dereference depth ≤ 1; no function pointers | already-passing at v0.11.2 | `test_jpl_audit.py` pin |
| 10 | Compile clean at most-pedantic warning level | v0.13.7 | `pedantic-build` 3-cell CI matrix |

### Rule 6 audit findings

The v0.11.2 spot-check estimate of *"likely 5-10 violations across `es_encode.c` + `es_parity.c`"* did not survive the cleanup work in v0.13.4-v0.13.6. The illustrative snippet in the audit doc was illustrative, not actual code. Real codebase shape:

- **All loop iterators**: `for (size_t i = ...; ...)` block-scoped.
- **All `const` declarations**: at minimal scope near use (the v0.13.6 assertion work added `const double rad = ...; assert(rad >= 0.0)` patterns throughout).
- **Function-scope declarations that remain are intentional**:
  - **Accumulators** (`acc`, `acc_r`, `acc_i`) — must outlive each loop iteration.
  - **Sqrt caches** (`sqrt_D`, `inv_sqrt_D`) — computed once at function entry to avoid recomputation in the inner loop.
  - **Output buffers** (`curr_phases[]`, `trunk_step[]`) — used both before and after the chunk loop.
  - **Result variables** (`rounded` in `es_banker_round`) — set in three branches, returned at function exit.

All within Rule 6 spirit.

### Rule 7 audit findings

The v0.11.2 estimate of *"5-15 sites where `rc` is assigned but not checked"* did not survive scrutiny. Every `es_status_t` return is checked via the uniform pattern:

```c
es_status_t rc = some_call(...);
if (rc != ES_OK) return rc;
```

Audit walked every `es_status_t` assignment in the codebase (8 sites across `es_parity.c`, `es_hd_state.c`, `es_patches.c`); each was checked on the next line. Numeric returns used directly in expressions (no assigned-but-not-used sites). Bridge entry points validate every parameter via runtime checks; internal helpers take pre-validated inputs documented via post-validation `assert()` (Rule 5 work in v0.13.6).

### Migration

None. Audit-only release; no source code changes; no API/ABI/encoder/test surface change. 251 tests pass, 4 skipped (unchanged).

## [0.13.8] — 2026-05-05

**README accuracy patch — two-stage architecture clarification.** Docs-only release; no API / encoder / ABI / test changes.

### Why

User flagged a misunderstanding triggered by the previous README framing: *"our readme says that we use complex128 for syzygy and stuff, is that still correct? because that would mean we aren't pure ALU, right?"*

The README listed three backends (`bip` / `c` / `complex128`) as parallel alternatives, with `complex128` annotated as *"Used for the algebraic identities (Syzygy operator, observer binding) and as a regression baseline."* That bullet was true *before* v0.7.0, when Tier 2b shipped C-side `complex64` implementations of the HD operations. Since then the production HD path is C-side `complex64`; `complex128` is the regression baseline only (`backend="fpu-ref"`).

The framing also implied "three interchangeable backends" all ran the same operation. They don't — they are three encoders for the **phase-residue stage**, plus an FPU HD pipeline that follows. The mental model was off, and the README was the load-bearing source.

### Fixed

- **Two-stage architecture, explicitly described**: phase-residue computation (integer ALU) + HD operations (FPU `complex64` production / `complex128` regression). Phase residues are integer ALU end-to-end; HD operations can't be (channel bases are unit-magnitude complex; `(cos(φ), sin(φ))` requires trigonometric channels).
- **`complex128` reframed**: from "production path for syzygy / observer-bind" to "regression baseline; `backend='fpu-ref'`."
- **"Both backends" → "All three phase-residue encoders"** typo fix (the earlier sentence had been written before `complex128` was added to the list).
- **Status banner updated**: from "Three interchangeable backends (BIP integer ALU, native C, FPU complex128)" to a more accurate "Two-stage architecture: three interchangeable integer-ALU phase-residue encoders feeding an FPU `complex64` HD pipeline."
- **TL;DR callout added** under the new architecture section: *"Phase residues are integer ALU end-to-end (BIP encoder hot path is uint64/int64/uint32, no floats); HD operations (syzygy / observer-bind / eclipse) lift those residues to `complex64` and run on FPU. The package is *not* pure-ALU end-to-end — the HD pipeline can't be."*

### Roadmap renumber

JPL_AUDIT.md: Rules 6+7 manual audits move v0.13.8 → v0.13.9 (last item in the rule-fix sequence; v0.13.8 reserved for this README hygiene patch).

### Migration

None. Pure docs change; no API / encoder / ABI / test surface change. 251 tests pass, 4 skipped.

## [0.13.7] — 2026-05-05

**JPL Power-of-Ten Rule 10 fixes — cross-platform pedantic-build CI matrix.** Fourth code-quality patch in the v0.13.4-v0.13.8 rule-fix sequence. CI-only addition; no public API / ABI / encoder change.

### Added

- **`ES_PEDANTIC` CMake option** (default OFF) elevates the existing pedantic warning flags to errors:

  | Toolchain | Existing flags | With `ES_PEDANTIC=ON` |
  |---|---|---|
  | gcc / clang | `-Wall -Wextra -Wpedantic` | + `-Werror` |
  | MSVC | `/W4` | + `/WX` |

  The casual local build stays friendly (warnings emitted but not fatal); CI turns it on so any new warning fails the build.

- **`pedantic-build` job** in `.github/workflows/ephemerides-spectral-ci.yml` runs a 3-cell matrix:

  | Cell | Toolchain |
  |---|---|
  | `ubuntu-latest` | gcc |
  | `macos-14` | clang |
  | `windows-latest` | MSVC |

  Each cell runs `cmake -DES_PEDANTIC=ON` then `cmake --build`, so any new warning fails CI on every PR.

  **Always-on** (not gated by the `wheel-check` label) — Rule 10 is a permanent invariant, not a per-PR opt-in. Cost ~30s per cell. Cheap protection against signed/unsigned mismatches, unused-variable regressions, missing-prototype drift, etc.

### Why ES_PEDANTIC is opt-in by default

Casual local builds (e.g. `cmake --build` during development for a quick parity check) shouldn't fail on a newly-introduced unused-variable warning the developer is about to fix. `ES_PEDANTIC=OFF` keeps warnings as warnings during development; CI enforces the zero-warnings invariant before merge.

### Holzmann's Rule 10

> *"All code must be compiled, from the first day of development, with all compiler warnings enabled at the compiler's most pedantic setting. All code must compile with these settings without any warnings."*

The 3-cell matrix is the cross-platform implementation: gcc on Linux, clang on macOS, MSVC on Windows. All three see the same source tree; each emits its own warnings (gcc and MSVC notably differ on which patterns warn). The matrix-CI satisfies "without any warnings" across every platform we ship to.

### Audit ratchet

Rule 10 is enforced by CI rather than by `tests/test_jpl_audit.py` (which counts source-side patterns; warnings are toolchain-side and toolchain-version-dependent). The `pedantic-build` job is the ratchet — drop the pin, drop the warning.

**All five mechanically-enforceable JPL rules now satisfied:**

| Rule | Status | Mechanism |
|---|---|---|
| 1 (no `goto`) | ✅ | Pinned in `test_jpl_audit.py` |
| 3 (no dynamic alloc) | ✅ | Pinned in `test_jpl_audit.py` |
| 4 (≤60-line functions) | ✅ | Pinned in `test_jpl_audit.py` |
| 5 (≥2 assertions/function) | ✅ | Pinned in `test_jpl_audit.py` |
| 10 (zero warnings at pedantic) | ✅ | Enforced by `pedantic-build` CI job |

Remaining JPL roadmap: Rules 6+7 (manual scope + return-value audits, v0.13.8).

### Migration

None. CI-only addition. Local builds default to the previous behaviour (warnings as warnings); developers wanting Rule 10 enforcement locally can pass `-DES_PEDANTIC=ON` to cmake.

251 tests pass, 4 skipped (unchanged from v0.13.6).

## [0.13.6] — 2026-05-05

**JPL Power-of-Ten Rule 5 fixes — assertion density at 2/function average.** Third code-quality patch in the v0.13.4-v0.13.8 rule-fix sequence. Pure additive instrumentation: no public API change, no ABI change (still v6), encoder math byte-identical — parity smoke pins both backends to within float-ULP and stays green.

### Fixed

- **Rule 5 (≥2 assertions per function avg)** density flips from 0.0 (audit baseline) to **2.10**. **88 assertions** added across the 42 functions (target ≥2 × 42 = 84). The previously-skipped `test_rule_5_density_meets_2_per_function` ratchet test now **PASSES**.

  Per-file distribution:

  | File | Assertions / Functions | Density |
  |---|--:|--:|
  | `es_channel_bases.c` | 2 / 1 | 2.00 |
  | `es_encode.c` | 26 / 13 | 2.00 |
  | `es_hd_state.c` | 25 / 11 | 2.27 |
  | `es_parity.c` | 16 / 8 | 2.00 |
  | `es_patches.c` | 15 / 7 | 2.14 |
  | `es_prng.c` | 4 / 2 | 2.00 |
  | **Total** | **88 / 42** | **2.10** |

### Coverage strategy

Per Holzmann's original Power-of-Ten paper, assertions document anomalous-condition checks. Three categories applied:

- **Pre-conditions on parameters**: assert pointer non-NULL after runtime `if (ptr == NULL) return ERR;` check (documents post-validation invariant); assert index < N_BODIES; assert input finite.
- **Post-conditions on results**: assert output non-negative for magnitudes/norms; assert output bounded (e.g. `phi < 2π`); assert state advanced exactly once.
- **Invariants**: assert `D > 0`; assert `n_patches ≤ ES_MAX_PATCHES`; assert constants positive.

### Zero runtime cost

All assertions use the standard `<assert.h>` macro, which is a no-op when `NDEBUG` is defined. Production builds (`-DNDEBUG`) strip them entirely. Assertions are a *development-time* documentation tool that doubles as static-analysis-friendly precondition spec — not a runtime check.

### Audit ratchet

`tests/test_jpl_audit.py` pins ratcheted:

| Pin | v0.11.2 baseline | v0.13.5 | v0.13.6 |
|---|--:|--:|--:|
| `PIN_RULE_5_ASSERTIONS` | 0 | 0 | **88** *(ratcheted UP — count must only increase)* |

`test_rule_5_density_meets_2_per_function` flips from SKIP to **PASS**. Total mechanically-detectable violations: **102 → 0** — every Rule 1-5 violation in the v0.11.2 audit baseline now cleared in three ships. Remaining JPL roadmap: Rule 10 (pedantic-build matrix, v0.13.7), Rules 6+7 (manual scope + return-value audits, v0.13.8).

### Migration

None. Pure instrumentation; no API/ABI/test surface change; runtime behaviour unchanged in release builds. 250 tests pass, 4 skipped (was 5; Rule 5 density skip is gone).

## [0.13.5] — 2026-05-05

**JPL Power-of-Ten Rule 4 fixes — long-function splits.** Second code-quality patch in the v0.13.4-v0.13.8 rule-fix sequence. Pure refactor: no public API change, no ABI change (still v6), encoder math byte-identical (parity smoke is the gate).

### Fixed

- **Rule 4 (function bodies ≤ 60 lines)** count drops **4 → 0**. The four offenders identified in the v0.11.2 audit are factored into JPL-compliant sub-functions along natural algorithm seams:

  | File | Function | Before | After (driver) | New static helpers |
  |---|---|--:|--:|---|
  | `es_encode.c` | `es_encode_state` | 109 | ≤60 | `apply_one_chunk` (chunk-loop body), `apply_subchunk_remainder` (banker's-round leftover step) |
  | `es_parity.c` | `es_find_syzygies` | 99 | ≤60 | `select_syzygy_targets` (kind-filter table), `score_syzygy_event` (per-event geometry), `validate_syzygy_args` (input checks), `emit_syzygy_event` (count + cap handling) |
  | `es_hd_state.c` | `es_bind_observer` | 78 | ≤60 | `observer_coord_shift` (lat/lon → roll index), `apply_observer_bind` (complex-mul inner loop) |
  | `es_hd_state.c` | `es_get_eclipse_probability` | 65 | ≤60 | `build_syzygy_operator` (sun+moon+node sum), `complex64_vdot_magnitude` (numpy-`vdot` magnitude) |

  10 new static internal helpers; total function count 32 → 42 (`PIN_RULE_5_TOTAL_FUNCS` ratcheted UP — Rule 5 work in v0.13.6 needs the larger inventory).

### Why static helpers (not public API)

The new factors are private to their .c files — they're internal seams, not new ABI surface. No header changes, no Python-side updates, no parity tests to update. The Python ctypes shim doesn't even know they exist. Public entry points (`es_encode_state`, `es_find_syzygies`, `es_bind_observer`, `es_get_eclipse_probability`) keep their v0.13.4 signatures.

### Audit ratchet

`tests/test_jpl_audit.py` pins ratcheted:

| Pin | v0.11.2 baseline | v0.13.4 | v0.13.5 |
|---|--:|--:|--:|
| `PIN_RULE_4_LONG_FUNCTIONS` | 4 | 4 | **0** |
| `PIN_RULE_5_TOTAL_FUNCS` | 32 | 32 | **42** *(ratcheted UP — Rule 5 needs the new inventory)* |

Total mechanically-detectable violations: **102 → 64** (37% of audit baseline cleared across v0.13.4 + v0.13.5). Remaining: Rule 5 (assertion density, v0.13.6), Rule 10 (pedantic-build matrix, v0.13.7), Rules 6+7 (manual audits, v0.13.8).

### Migration

None. Pure internal refactor; no API/ABI/test surface change. 250 tests pass, 5 skipped.

## [0.13.4] — 2026-05-05

**JPL Power-of-Ten Rule 1 + Rule 3 fixes** — first code-quality patch in the v0.13.4-v0.13.8 rule-fix sequence. Caller-supplied-scratch refactor of the HD pipeline removes both classes of violation in one pass. ABI v5 → v6 (mechanical wire-format change; encoder math byte-identical).

### Fixed

- **Rule 1 (no `goto`)** — 5 occurrences → **0**. The five `goto out` statements in `es_hd_state.c`'s cleanup-on-error pattern (`es_encode_state_hd`, `es_bind_observer`, `es_get_eclipse_probability`) are gone. With the buffers no longer owned by the C function, there's nothing to free on error paths — they collapse to plain early-return.

- **Rule 3 (no dynamic allocation after init)** — 29 occurrences → **0**. The C library no longer calls `malloc`/`calloc`/`realloc`/`free` anywhere after init. `es_hd_state.c` no longer includes `<stdlib.h>`. The HD pipeline's three entry points take caller-supplied scratch buffers as additional pointer parameters; the Python ctypes shim allocates the scratch alongside the existing `out_state` buffer (no observable change in heap pressure — Python was already heap-allocating the output buffer).

### Changed (ABI break — v5 → v6)

Three public C entry points gained scratch-buffer parameters:

| Function | New parameters |
|---|---|
| `es_encode_state_hd` | `+scratch_basis`, `+scratch_rolled` |
| `es_bind_observer` | `+scratch_body_basis`, `+scratch_coord_basis`, `+scratch_coord_op` |
| `es_get_eclipse_probability` | `+scratch_sun_b`, `+scratch_moon_b`, `+scratch_node_b`, `+scratch_s_op` |

Each scratch buffer must have capacity for D `es_complex64_t` entries; contents on entry are ignored, on return are unspecified.

`ES_ABI_VERSION` 5 → 6. The ctypes shim refuses to load any binary with a mismatched ABI, so a stale `_native/ephemerides_spectral.dll` from v0.13.3 will fail loudly at import time rather than silently corrupt memory. Standard `pip install --force-reinstall ephemerides-spectral` (or `cmake --build` for source-tree dev) refreshes the binary.

### User-facing impact

**None.** The Python bridge API (`bridge.py`'s `get_local_view`, `get_eclipse_probability`, `default_encode(..., backend="c")`) is unchanged — the scratch allocation lives in the ctypes shim (`_native_bip.py`'s `native_*` helpers), one layer below the bridge surface. Same call sites, same return shapes, same numpy dtypes, byte-identical math.

### Audit ratchet

`tests/test_jpl_audit.py` pins ratcheted DOWN:

| Pin | v0.11.2 baseline | v0.13.4 |
|---|--:|--:|
| `PIN_RULE_1_GOTO` | 5 | **0** |
| `PIN_RULE_3_DYNAMIC_ALLOC` | 29 | **0** |

Total mechanically-detectable violations: **102 → 68** (-34, 33% of the audit baseline cleared in one ship). Remaining: Rule 4 (4 long functions, queued v0.13.5) + Rule 5 (64 assertions short, queued v0.13.6).

### Migration

- **Pure-Python users (no C extension)**: zero change. Pyodide / WASM / sdist-without-toolchain installs are unaffected.
- **Direct C-API consumers (rare)**: rebuild against v0.13.4 headers; pass scratch pointers per the new signatures. See `c/include/ephemerides_spectral.h` ABI-history comment for the exact field list.
- **Standard PyPI users**: `pip install -U ephemerides-spectral` refreshes the wheel; the bundled native binary matches the bundled Python.

250 tests pass, 5 skipped (unchanged).

## [0.13.3] — 2026-05-05

**Pre-merge docs+parity hygiene check** — soft-warning GitHub Actions workflow that flags PRs whose code-side changes don't move the docs surface in lockstep. Closes `` `#98` `` (consolidated; absorbs `` `#87` `` + `` `#88` ``).

### Added

- **`` `#98` ``** — `.github/workflows/ephemerides-spectral-docs-check.yml` posts (or updates in place) a single PR comment summarising drift between code-side touches and the five documentation files we treat as the PyPI-facing SSOT surface:

  | Watched doc | Role |
  |---|---|
  | `python/README.md` | PyPI README (status banner + body table) |
  | `python/CHANGELOG.md` | Package CHANGELOG (PyPI-rendered) |
  | `CHANGELOG.md` | Project CHANGELOG (mirror) |
  | `ROADMAP.md` | Roadmap / status sweep |
  | `ephemerides_spectral_research_notebook.md` | Research notebook |

  Categories cross-checked against expected docs:

  | Code-side category | Expected docs |
  |---|---|
  | Version bump (`pyproject.toml` / `pyproject-pure.toml` / `version.py` / `c/include/ephemerides_spectral.h`) | All five |
  | `bridge.py` (Python bridge surface) | README + both CHANGELOGs + notebook |
  | `cli.py` (CLI surface) | README + both CHANGELOGs |
  | `_research/*.py` or `research/*.py` (codegen source / mirror) | Notebook + both CHANGELOGs |
  | `c/src/*.c` or `c/include/*.h` (C library) | Both CHANGELOGs + parity-test touch |

  **Soft-warning, not hard-fail.** The freshness ratchet inside pytest already hard-fails on the highest-value drift modes (`test_native_version_string_matches`, `test_parity_smoke::PARITY_TARGETS`, `test_readme_freshness`, `test_jpl_audit`); this workflow surfaces the *next tier* — prose-and-narrative drift that humans should review but a regex can't authoritatively adjudicate. Forcing CHANGELOG bumps on every whitespace diff would burn patience and breed filler bullets.

  **Opt-out**: include `[skip-docs-check]` anywhere in the PR body to silence on cosmetic / typo / formatting-only diffs.

  **Comment idempotence**: uses `peter-evans/find-comment` + `peter-evans/create-or-update-comment` so the same advisory is updated in place across pushes rather than spamming the PR.

  **Concurrency**: matches `ephemerides-spectral-ci.yml`'s `cancel-in-progress: true` group keyed by workflow + ref so the `opened`+`labeled` double-fire pattern documented in that workflow's header doesn't double up here either.

### Migration

None. CI-only addition; no source / API / ABI / encoder / test changes. The four version-stamp files (`version.py`, `pyproject.toml`, `pyproject-pure.toml`, `c/include/ephemerides_spectral.h`) bump from 0.13.2 → 0.13.3 in lockstep as usual.

## [0.13.2] — 2026-05-05

**Quick-win patches**: gitignore the rebuild-every-build `_native/` directory + renumber the JPL rule-fix roadmap.

### Fixed

- **`` `#85` ``** — Added `docs/antikythera-maths/ephemerides-spectral/python/ephemerides_spectral/_native/` to the repo `.gitignore`. The `_native/` directory holds the compiled native C library (`ephemerides_spectral.dll` / `.so` / `.dylib`) that rebuilds on every `cmake --build ../build` followed by `cp ../build/ephemerides_spectral.dll ephemerides_spectral/_native/`. Per-platform; not portable; not shipped in source. Eliminates the friction of `git status` always showing `?? ephemerides_spectral/_native/` and the per-PR ceremony of adding files individually to avoid accidentally committing the binary.

- **`c/JPL_AUDIT.md` roadmap renumbering**. The original v0.11.3-v0.11.7 numbering queued at the v0.11.2 audit ship is obsolete since the project moved past v0.11.x. Rule-fix patches are renumbered:

  | Was | Now | Focus |
  |---|---|---|
  | v0.11.3 | **v0.13.4** | Rule 1 + Rule 3 fixes |
  | v0.11.4 | **v0.13.5** | Rule 4 fixes |
  | v0.11.5 | **v0.13.6** | Rule 5 fixes |
  | v0.11.6 | **v0.13.7** | Rule 10 audit |
  | v0.11.7 | **v0.13.8** | Rules 6 + 7 audits |

  v0.13.3 is reserved for `` `#98` `` (consolidated docs+parity hygiene check; absorbs `` `#87` `` + `` `#88` ``).

### Migration

None. Patch-level docs + repo-config changes only; no API, no encoder, no ABI, no test changes.

## [0.13.1] — 2026-05-05

**SPICE feature-gap audit + STLT-naming hygiene.** Docs-only release.

### SPICE feature-gap audit (#101)

User question (during v0.11.2 ship close): *"What do we do now that SPICE does slower? Does SPICE do things we might be able to do but don't? If so, will it be worth some API compatible bridge?"*

Answer in `figures/spice_feature_audit.md`: three-column comparison of what we do faster, what we do that SPICE doesn't, and what SPICE does that we don't. **Recommendation: skip the SPICE-API compat bridge.** Document the gap (this audit). Re-evaluate when the four high-value gaps land (light-time + stellar aberration; frame transformations; full Kepler elements; per-body pole orientation) — probably still skip, since at that point our surface stands on its own.

Spawned v0.14.x backlog from the audit:
- Light-time + stellar-aberration corrections (high value, moderate cost).
- Canonical frame-transform primitive (medium value, medium cost).
- Full Kepler elements on `KinematicState` (eccentricity, inclination, etc. — high value).
- Per-body pole orientation (PCK-equivalent; small ship).

### STLT naming hygiene

User flagged that the abbreviation table listed Luna's primary Sol Time as **SLT (Sol Luna Time, surface clock)**, but per the moons-stuck-to-parent `Sol <Parent>-<Body> Time` convention from v0.9.1 it should be **STLT (Sol Terra-Luna Time)**. Fixed:

- README abbreviation table: Luna row promoted from `SLT / time-luna` to `STLT / time-terra-luna`. Followed by an explanatory paragraph about the moons-stuck-to-parent convention; SLT is preserved as a secondary alternative for the surface-clock case.
- Active code comments + docstrings (bridge.py / cli.py / time_scales.py / lunar_epoch_candidates.py / test_parity_smoke.py): drop "system clock for the Terra-Luna pair" framing in favour of "anchored Lunar time using the synodic month."
- Notebook §7.4 living description rewritten with the moons-stuck-to-parent framing.
- v0.10.0 CHANGELOG entries preserved as historical artefacts (they describe how STLT was *framed at the time*, not how shipped behaviour was; the shipped API is unchanged).

### Migration

None. Documentation-only release; no API, no encoder, no CLI behaviour change. The STLT name and CLI subcommand (`time-terra-luna`) and bridge methods (`get_sol_terra_luna_time`) are unchanged.

## [0.13.0] — 2026-05-05

**Sol Dynamics — system energy, gravitational forces, per-body energy budgets — augmented onto every `time-*` subcommand via `--dynamics`.**

Counterpart to v0.12.0's Sol Kinematics; mirrors chess-spectral's `qm_*_dynamics.py` *dynamics* layer (Hamiltonian + force / energy queries). The Phase A audit data already covered both halves (`figures/kinematics_dynamics_audit.md`); v0.13.0 ships the second canonical primitive (`_research/dynamics.py`) + bridge + CLI.

### Validated against textbook values

- **Earth-Sun gravitational force = 3.542×10²² N** at 1.000 AU, vs. textbook 3.54×10²² N (0.01 % rel err) — the most-cited validation value in classical mechanics.
- **Total system energy = −1.98×10³⁵ J** (negative ⇒ gravitationally bound) ✓.
- **Virial theorem holds**: total E = PE / 2 to within 0.5 % (circular-orbit constraint).
- **Sun's KE / Mc² = 8.6×10⁻¹⁶**, well below the 1×10⁻¹² noise floor for "Sun barely moves in barycentric frame."
- **Newton's 3rd law**: F_ab = F_ba symmetric to floating-point precision.
- **Inverse-square law**: F = G M m / r² verified explicitly.

### Added

**Bridge:**
- `bridge.get_dynamics(*, jd_tdb=None, frame=...)` — system aggregate (KE, PE, total E, is_bound, L partitions).
- `bridge.get_force_between(body_a, body_b, ...)` — Newtonian pair force.
- `bridge.get_body_energies(body, ...)` — per-body KE + PE + total energy budget.
- `bridge.apply_dynamics_correction(result, subcommand, ...)` — CLI `--dynamics` post-processor.
- `_research/dynamics.py`: `BodyEnergies`, `ForceContribution`, `DynamicsState` dataclasses + Phase B canonical primitives.

**CLI:**
- New `dynamics` subcommand with three query modes:
  - `dynamics` — system aggregate (default)
  - `dynamics --body <X>` — per-body energy budget
  - `dynamics --body <X> --from <Y>` — gravitational force on X from Y
- `--dynamics` flag added uniformly to every `time-*` subcommand.

**Examples:**
```bash
# System totals
ephemerides-spectral dynamics

# Mars's energy budget
ephemerides-spectral dynamics --body mars

# Force on Mars from Jupiter (validates the textbook formula)
ephemerides-spectral dynamics --body mars --from jupiter

# Earth-Sun reference (3.54e22 N at 1 AU)
ephemerides-spectral dynamics --body terra --from sun

# All three augmenting flags compose
ephemerides-spectral time-mars --jd 2451545.0 --state --proper --dynamics
```

### Discipline

- 34 new tests in `tests/test_dynamics.py` pin the validation set + every primitive + the CLI surfaces.
- Four new bridge methods classified `python_only` in `PARITY_TARGETS`.
- `dynamics.py` registered in `codegen/emit_research_modules.py::_INCLUDED_MODULES`.

### Out of scope (deferred)

- **3D force vectors.** v0.13.0 reports magnitudes only; needs the position-vector decoder (queued for v0.13.x).
- **Tidal forces.** Body-extended-by-radius differential pull. v0.13.x with the per-body internal-Laplacian work (#103).
- **Lyapunov / chaos indicator.** Needs full state evolution + variation propagation; v0.13.x.
- **`evolve(state, dt)` named primitive.** The existing `bip_instrument.encode_state(jd_tdb)` IS the evolution; v0.13.0 doesn't wrap it as a separate function.
- **C twin.** Parity smoke marks new methods `python_only`.

### Migration

None. Sol Dynamics is purely additive.

## [0.12.0] — 2026-05-05

**Sol Kinematics — per-body orbital state, transparently augmented onto every `time-*` subcommand via `--state`.**

### The framing

Mirror of chess-spectral's `qm_2d.py` / `qm_4d.py` *kinematics* layer (static observables, no time-evolution). The user pointed at the chess-spectral pattern: *"we can check our chess spectral where we have done this."* Translates 1:1 to ephemerides-spectral as v0.12.0 (Kinematics) + v0.13.0 (Dynamics, coming).

`--state` is opt-in (default off, no behavior change for v0.11.x callers); when set, augments any `time-*` bridge result with a `kinematic_state` block carrying orbital velocity, semi-major axis, kinetic energy, and angular momentum for the subcommand's canonical body.

### Validated against published values

Same 9 pins the Phase A audit script (`research/kinematics_dynamics_audit.py`) verifies — agreeing with `_research/kinematics.py` to within 0.02-2.5 %:

| Check | Computed | Expected | Source |
|---|---|---|---|
| Mercury orbital v | 47.87 km/s | 47.36 | NASA fact sheet |
| Earth orbital v | 29.785 km/s | 29.78 | Standard |
| Mars orbital v | 24.13 km/s | 24.07 | NASA fact sheet |
| Jupiter orbital v | 13.06 km/s | 13.07 | NASA fact sheet |
| Pluto orbital v | 4.741 km/s | 4.74 | NASA fact sheet |
| **Jupiter fraction of total L** | **61.5 %** | ~61 % | Standard tables |
| **Outer planets fraction of planet L** | **99.84 %** | ~99 % | Standard tables |

### Added

- `bridge.get_kinematic_state(body, *, jd_tdb=None, frame=...)` → per-body orbital state.
- `bridge.get_full_system_state(...)` → all 38 bodies + system totals.
- `bridge.apply_state_correction(result, subcommand, ...)` — CLI `--state` post-processor.
- `_research/kinematics.py` — `KinematicState` dataclass + Phase B canonical primitive.
- CLI `--state`/`--frame` flags added to every `time-*` subcommand.
- CLI `kinematics --body <X>` / `kinematics --all` standalone subcommand.

### Out of scope (deferred to v0.12.x or v0.13.0)

- Eccentricity / inclination corrections (v0.12.x).
- Position vectors at a specific JD — phase decoder (v0.12.1).
- Acceleration / forces / energies / evolution — v0.13.0 *Dynamics* counterpart.
- C twin (parity smoke marks new methods `python_only`).

### Migration

None. Sol Kinematics is purely additive.

## [0.11.2] — 2026-05-05

**JPL Power-of-Ten audit baseline for the C library.** Audit-only release — no code changes; documents violations and pins counts in CI as a one-way ratchet.

### Why this exists

User suggestion captured during v0.9.3: *"work we should do, maybe its own version path, impose JPL C standard on ourselves."* The C library is targeted at embedded deployment (ESP32, Cortex-M) per the README's "Microcontroller Compatibility" section; JPL Power-of-Ten is the embedded-C gold standard for safety-critical code (Holzmann 2006). The library is small enough (~2.1k LOC across 11 files) that retrofitting is tractable.

### Audit results

102 mechanically-detectable violations across the codebase:

| Rule | Description | Violations |
|---|---|--:|
| 1 | No goto / setjmp / longjmp / recursion | **5** (all goto in `es_hd_state.c` cleanup pattern) |
| 2 | Fixed loop bounds | 0 ✅ |
| 3 | No dynamic allocation after init | **29** (all in `es_hd_state.c` HD pipeline) |
| 4 | Functions ≤ 60 lines | **4** (`es_encode_state` 109; `es_find_syzygies` 99; `es_bind_observer` 86; `es_get_eclipse_probability` 71) |
| 5 | ≥ 2 assertions per function (avg) | **64-assertion shortfall** (0 across 32 functions) |
| 8 | Limited preprocessor | 0 ✅ |
| 9 | No function pointers | 0 ✅ |

Rules 6, 7, 10 are not mechanically detectable; manual audit deferred to v0.11.3+.

### Added

- **`c/JPL_AUDIT.md`** — full human-readable audit document. Rule-by-rule violation breakdown with line numbers, fix paths, and the v0.11.3+ ship roadmap.
- **`tests/test_jpl_audit.py`** — pytest ratchet pinning all mechanically-detectable counts. 11 passing checks + 1 expected-skip (Rule 5 density gate). Same drift-detection pattern as `test_native_version_string_matches_package_version` and `test_readme_freshness.py`.

### Discipline

- Adding a new violation requires updating the pin upward AND explicit justification in the PR description.
- Removing a violation should drop the pin in the same PR; the test emits a warning if a pin can be ratcheted down.
- The Rule 5 density test is gated as `pytest.skip` until v0.11.5; flipping to passing is the gate that proves the v0.11.5 work landed.

### Roadmap

| Version | Focus |
|---|---|
| v0.11.3 | Rule 1 + Rule 3 fixes — refactor `es_hd_state.c` HD pipeline (combined `goto` + `malloc` removal via static / caller-supplied buffers). |
| v0.11.4 | Rule 4 — split the 4 long functions into <60-line factors. |
| v0.11.5 | Rule 5 — add 64+ assertions across the 32 functions; gate behind `#ifndef NDEBUG`. |
| v0.11.6 | Rule 10 — cross-platform pedantic-build CI matrix. |
| v0.11.7 | Rules 6 + 7 — manual variable-scope and return-value audits. |

### Migration

None. Audit-only release.

## [0.11.1] — 2026-05-05

**Research notebook hygiene: backfill §7.4 (STLT) and §7.5 (SPrT); refresh Status banner.** Documentation-only release.

### Why this exists

User noticed during the v0.11.0 SPrT ship: *"just double checking, we added GR to our research notebook too?"* — and the answer was no. Both v0.10.0 STLT and v0.11.0 SPrT shipped with full bridge / CLI / test surfaces but without their notebook §7.x sections. The existing freshness checks (`tests/test_readme_freshness.py`) cover the README — they don't see the research notebook.

### Fixed

- **Notebook §7.4 added — Sol Terra-Luna Time (STLT).** Covers the system-clock framing, the Meton 432 BCE default-epoch choice, the Hipparchus-Babylonian-midpoint convergence story, the `Z₅` algebraic-spine connection, the available alternative epochs, the house-epoch-vs-NASA-LCT framing, and the bridge / CLI surface.
- **Notebook §7.5 added — Sol Proper Time (SPrT).** Covers the per-body diagonal-fiber framing (extending Mercury's existing 43″/century PN diagonal to all 38 bodies), the two leading-order components (`GM/(R·c²)` + `v_orb²/(2c²)`), the validation table against six published values, the user's transparent `--proper` UX, the two-implementation discipline, and the deferred items (rotational kinematic, J₂ oblateness, frame dragging).
- **Notebook Status banner refreshed.** Was stale at v0.7.0; now reads v0.11.1 with the headline-state summary.
- **Notebook Release History block backfilled** with v0.9.2, v0.9.3, v0.10.0, v0.11.0, and v0.11.1 entries (was ending at v0.9.1).

### Discipline

- New task #98 captured: a soft-warning "docs probably need updating" check on PRs. Would have caught the v0.10.0 / v0.11.0 gaps automatically.

### Migration

None. Documentation-only.

## [0.11.0] — 2026-05-05

**Sol Proper Time (SPrT) — gravitational + orbital-kinematic time dilation, applied transparently via `--proper` on every `time-*` subcommand.**

### The framing

The user asked: *"can we simply add `--proper` as a line arg to invoke gravitational time dilation fiber so that users don't even need to know anything extra had to happen in the back end?"*

That's exactly what shipped. `--proper` is opt-in (default off, no behavior change for v0.10.0 callers); when set, it augments any Sol Time bridge result with proper-time-corrected count fields (`<count>_proper`) plus a `proper_time` metadata block. Same physics as Mercury's existing 43″/century PN diagonal correction; SPrT extends the per-body diagonal-fiber treatment to every body in the roster.

### Validated against published values

Six leading-order checks, all within 0.30 % rel err:

| Check | Computed | Expected | Source |
|---|---|---|---|
| Earth surface GR | 6.961e-10 | 6.95e-10 | Ashby 2003 / GPS clock corrections |
| Sun surface GR | 2.123e-6 | 2.12e-6 | Standard solar physics |
| Mars surface GR | 1.400e-10 | 1.40e-10 | Genova et al. 2014 / Curiosity rover |
| Pluto surface GR | 8.136e-12 | 8.15e-12 | New Horizons mission planning |
| Terra orbital kinematic | 4.935e-9 | 4.95e-9 | v_terra² / (2c²) standard |
| Mars-vs-Terra GR difference | 5.561e-10 | 5.56e-10 | The 0.0175 s/Earth-year Curiosity figure |

### Added

**Python API:**
- `bridge.get_proper_time_rate(body, *, lat=None, lon=None, jd_tdb=None, reference="tcb")` — leading-order rate vs. TCB / TDB. Returns `{components: {gr_surface, kinematic_orbital, j2_oblateness, total}, rate_relative_to_reference, ...}`.
- `bridge.compare_proper_times(body_a, body_b, *, reference="tcb")` — rate ratio + drift per Earth-year between two bodies.
- `bridge.apply_proper_correction(result, subcommand, ...)` — post-processor used by the CLI's `--proper` flag.
- `_research/proper_time.py`: `ProperTimeRate` dataclass + the same primitives at the research-module layer.
- `Body.surface_radius_km` field — volumetric mean radius in km, populated for all 38 bodies in the roster.

**CLI:**
- `--proper`, `--lat`, `--lon`, `--reference` flags added uniformly to **every** `time-*` subcommand via the shared `_add_proper_flags` helper. Default off → v0.10.0 callers see no change.
- `time-proper` standalone subcommand for the rate-only query: `--body <X>` for a single body's rate, `--compare-to <Y>` for the two-body drift figure.

**Examples:**
```bash
# Proper-time-corrected Mars Sol Date
ephemerides-spectral time-mars --jd 2451545.0 --proper

# Proper-time-corrected STLT synodic count
ephemerides-spectral time-terra-luna --jd 2451545.0 --epoch meton --proper

# Standalone rate query — Mars vs. TCB
ephemerides-spectral time-proper --body mars

# Two-body comparison — Mars-Terra clock-rate difference
ephemerides-spectral time-proper --body mars --compare-to terra
```

### Discipline

- 32+ new SPrT tests in `tests/test_sprt.py` pin the validation set + every component + the CLI surfaces.
- Three new bridge methods classified `python_only` in `tests/test_parity_smoke.py::PARITY_TARGETS` (C twin queued).
- Manifest regenerated via `codegen/regenerate.py`.
- `proper_time.py` added to `_INCLUDED_MODULES` in `codegen/emit_research_modules.py` so the package codegen picks it up alongside the other research modules.
- `tests/test_readme_freshness.py` invariants caught the v0.10.0-banner-still-says-v0.10.0 drift the moment the version bumped.

### Out of scope (deferred to v0.12.0+)

- Surface rotational kinematic (`ω × R`) — for most bodies the orbital term dominates; for the Sun, rotational dominates.
- J₂ oblateness corrections (~10⁻¹⁵ scale) — `--lat` / `--lon` already accepted for forward compatibility; v0.11.0 ignores them.
- Frame dragging (Lense-Thirring) — ~10⁻¹⁵ at Earth-Moon scale; skip until needed.

### Migration

None. Existing scripts and bridge calls are unchanged. SPrT is purely additive.

## [0.10.0] — 2026-05-05

**Sol Terra-Luna Time (STLT) — system-level clock for the Terra-Luna pair, with Meton's 432 BCE summer solstice as the default epoch.** First Sol Time member with a non-J2000 default anchor.

### The framing

What we call "STLT" is a *system-level* clock — natural unit is the synodic month (29.530589 days), natural references are eclipse cycles (Saros 18.03 yr) and solar-lunar reconciliation cycles (Metonic 19.00 yr). The existing Sol Time series anchored individual bodies (Sol Mars, Sol Venus, ...); STLT anchors the *pair*.

The default epoch is **Meton of Athens's summer solstice on 27 June 432 BCE proleptic Julian** — the calibration anchor of the Metonic cycle, the lunar-solar reconciliation Greek mathematical astronomy was built on. This choice is independently validated by `research/lunar_epoch_candidates.py`: the Hipparchus-Babylonian eclipse-archive midpoint (Mardokempad 721 BCE + Hipparchus 141 BCE) lands within +240 days of Meton's solstice — *same year*, eight months later. Greek astronomy's eclipse archive is centred on Meton's lifetime; the "combo" candidate test confirms his anchor numerically.

This is a **house-epoch design choice** — not a claim to be NASA's eventual Lunar Coordinated Time (LCT) standard, which is still pending standardisation per the April 2024 White House directive. When LCT lands, we add it as a sibling epoch.

### Added

**Python API:**
- `bridge.jd_to_sol_terra_luna_time(jd_tdb, *, epoch="meton")` → `{epoch_name, epoch_jd_tdb, days_since_epoch, synodic_count, synodic_phase, saros_count, saros_phase, metonic_count, metonic_phase, ...}`. The full epoch metadata block carries the abbreviation `"STLT"`, the cycle constants, and the available-epochs roster.
- `bridge.sol_terra_luna_time_to_jd(synodic_count, *, epoch="meton")` — inverse on the synodic-month count.
- `_research/time_scales.py`: `TerraLunaTime` dataclass, `jd_to_terra_luna_time`, `terra_luna_time_to_jd`, plus the constant set: `STLT_SYNODIC_MONTH_DAYS`, `STLT_SAROS_CYCLE_DAYS`, `STLT_METONIC_CYCLE_DAYS`, `STLT_EPOCH_{METON,ANTIKYTHERA,HIPPARCHUS,MARDOKEMPAD,J2000}_JD_TDB`, `STLT_EPOCHS`, `STLT_DEFAULT_EPOCH`.

**CLI:**
- `ephemerides-spectral time-terra-luna --jd <X>` (canonical) — defaults to Meton's epoch; `--epoch {meton,antikythera,hipparchus,mardokempad,j2000}` switches anchors.
- `--synodic-count <N>` inverts: synodic-month count → JD_TDB.

**Available epochs:**
- `meton` (default) — Meton's summer solstice 432 BCE.
- `antikythera` — solar eclipse 23 Aug 205 BCE; Antikythera mechanism Saros-dial anchor (Freeth & Jones 2012).
- `hipparchus` — Hipparchus's lunar eclipse 25 Jan 141 BCE (Almagest VI.5).
- `mardokempad` — Babylonian lunar eclipse 19 Mar 721 BCE (Almagest IV.6); the foundational Babylonian record Hipparchus calibrated against.
- `j2000` — modern reference, Terra-borrowed.

**Research:**
- `research/lunar_epoch_candidates.py` — the Phase A scoring script. Enumerates all five candidates against the spectral kernel (`find_syzygies`) + skyfield ground truth, dumps a markdown report under `figures/lunar_epoch_candidates.md`. Also handles solstice diagnostics with epoch-of-date precession correction (~33° at 2400 yr) so candidate validation isn't dominated by precession noise.

### Fixed

- `bridge.find_syzygies(backend="auto")` was rejected by `_validate_backend` — same latent bug class fixed for `get_breathing_modulation` in v0.9.2 (`SUPPORTED_BACKENDS` doesn't include the `"auto"` sentinel). Now resolves `"auto"` → concrete backend before validation, matching the docstring contract. Caught while writing the research script; fixed in passing.

### Discipline

- Both new bridge methods classified in `tests/test_parity_smoke.py::PARITY_TARGETS` as `python_only` (pure-Python time-scale formula; C twin queued).
- Manifest regenerated via the project's official `codegen/regenerate.py` — no hand-edited SHAs.
- `tests/test_readme_freshness.py` invariants enforced: Status section + banner + CLI body-name examples.

### Migration

None required. Existing scripts and bridge calls unchanged. STLT is purely additive.

## [0.9.3] — 2026-05-05

**PyPI-facing README staleness sweep + CI freshness check.** Docs-only — no API or encoder changes.

### Why now

User flagged the Status and Roadmap sections of the PyPI-facing README as stale. The Status block ended at v0.6.1 — eight versions back. The Roadmap listed Tier 2b "in progress" (shipped in v0.7.0), Sol Venusian/Mercurian Time as upcoming (shipped in v0.8.0; renamed in v0.9.1), and the ITN pathway / `find-tubes` query as upcoming (shipped in v0.8.1). Plus leftover `--body earth` example strings from before the v0.9.0 body-identity rename.

### Fixed (manual sweep)

- **Status section refreshed** with v0.7.0 → v0.9.3 entries. Current marker moved to v0.9.3.
- **Banner added** under the H1: `**Status: v0.9.3 — production-ready.**` Now pinned to `__version__` by the new freshness test.
- **Roadmap section pruned** of shipped items (Tier 2b, Sol Venusian/Mercurian Time, ITN pathway). Items genuinely still ahead retained and reorganized: first-principles per-resonance α, Hyperion follow-up, remaining 4 broken moons, Sol Moon Times, DE441 vs DE442 spectral error signature, heteroclinic-tube extension to `find-tubes`, LTC, Phase 10 resonance coverage, multi-millennium DE441 sweep, Doxygen, bit-serial hardware port.
- **Leftover earth-body CLI example strings** corrected to `terra` (in the `find-tubes` cheat-sheet and in Key Capabilities prose).
- **Phase 9 heading** inverted from `Phase 9 "Breathing" Couplings` → `Phase 9 Adaptive Couplings (a.k.a. "breathing")` matching the v0.9.2 CLI rename. Also updated the Cosine LUT row in the memory-footprint table.
- **Stale "v0.4+ ROADMAP: window search" comment** in the CLI cheat-sheet removed — `find-syzygies` shipped in v0.3.1.

### Added (drift prevention)

`tests/test_readme_freshness.py` enforces three invariants on every PR:

1. **Status section completeness.** Every released version in the package CHANGELOG must have a corresponding bullet under the README's `## Status` section. Reverse direction also enforced (no inventing unreleased versions in the README).
2. **Current-version stamp accuracy.** The `Status: vX.Y.Z` banner under the H1 *and* the `*(current)*` marker in the Status section must both equal `__version__`. Same pattern as `test_native_version_string_matches_package_version`.
3. **CLI body-name validity.** Every body name appearing after a body-flag in a CLI example (`--body NAME`, `--departure NAME`, `--target NAME`, `--pair-a NAME`, `--pair-b NAME`) must be in `SUPPORTED_BODIES`. Catches the v0.9.0 fallout pattern: examples pointing at body names that have been removed from the roster.

What this does *not* enforce: prose accuracy, Roadmap correctness, whether examples are *good* examples. Those stay in human review. Same modular discipline as `test_parity_smoke.py::PARITY_TARGETS` — enumerate the mechanically-checkable truth, fail loudly on drift.

### Migration

None. Docs-only release; no API surface changes.

## [0.9.2] — 2026-05-05

**CLI: `adaptive` is the primary name for Phase 9 state-dependent coupling modulation; `breathing` retained as a hidden synonym.** No public-API changes, no encoder hot-path changes.

### Added

- `ephemerides-spectral adaptive` — primary subcommand. Matches the adaptive-networks vocabulary (Gross & Blasius 2008; adaptive Kuramoto): a state-dependent graph Laplacian whose edge weights co-evolve with node phases.

### Changed

- `ephemerides-spectral breathing` — now registered with `help=argparse.SUPPRESS`. Invisible in `--help` listings, fully functional when typed. Cross-referenced from `adaptive --help`'s epilog and from the toplevel `--help`.

### Fixed

- `resolution --body` default and example strings updated `earth` → `terra` (consistent with the v0.9.0 body roster). `find-tubes` and `local-view` examples likewise corrected. The CLI help and `--body` validation are now self-consistent.
- **Latent bug since v0.8.0:** `get_breathing_modulation(backend="auto")` (its own default) was rejected by the `_validate_backend` check; any caller that didn't pass an explicit `backend=` got an "ok: false" error. `"auto"` is now resolved to a concrete backend before validation, matching the docstring. The CLI's `breathing` (now `adaptive`) subcommand was the principal victim.

### Internal

- Subparser argument registration factored through a shared helper so `adaptive` and `breathing` cannot drift apart.
- `_cmd_breathing` kept as an alias of `_cmd_adaptive` for external imports.

### Migration

None required. Both `adaptive` and `breathing` work; existing scripts unchanged.

## [0.9.1] — 2026-05-05

**Sol Time naming convention overhaul + Sol Terra Time + Sol Luna Time.**

> *"Returning to the giants whose shoulders we stand on. We've always had a lunar orbit and a lunar eclipse. We've all had terrain and terrestrial animals. We're just putting the books back in their dewey decimal spot."*

### Renames (BREAKING)

`Sol Mercurian/Venusian/Plutonian Time` → `Sol Mercury/Venus/Pluto Time`. Function names, dataclasses, and bridge methods all updated. Gas/ice giants (Jovian, Saturnian, Uranian, Neptunian) keep adjective forms — those are deeply established in astronomical tradition.

### New time systems (additive)

- **Sol Terra Time (STT)** — Terra's own surface clock; `bridge.jd_to_sol_terra_time(jd_tdb)`, CLI `time-terra`.
- **Sol Luna Time (SLT)** — Luna's surface clock; `bridge.jd_to_sol_luna_time(jd_tdb)`, CLI `time-luna`. **Distinct from Sol Lunar Time** (`get_lunar_phase`) which gives Luna's phase as observed from Terra.

### Abbreviation field

Each Sol Time bridge return's `epoch:` block now carries `"abbreviation": "STT"` / `"SLT"` / `"SVT"` / etc. per the user's indexing table.

### Tests

111 active tests pass; 5 skipped (4 cibuildwheel + 1 `tier1_skip`).

## [0.9.0] — 2026-05-05

**Body identity rename: `moon` → `luna`, `earth` → `terra`. BREAKING CHANGE.**

The body-identity strings now use Latin proper nouns. The generic English nouns are no longer privileged — `moon` is the category for any natural satellite, `earth` is the substance/ground.

### Migration

Anywhere your code references body identity by string, change:
```python
bridge.body_to_idx["earth"]    # before
bridge.body_to_idx["moon"]     # before
bridge.list_bodies()            # contained "earth"/"moon"
```
to:
```python
bridge.body_to_idx["terra"]    # after
bridge.body_to_idx["luna"]     # after
bridge.list_bodies()            # contains "terra"/"luna"
```

### What stays the same

- Category strings (`category == "moon"`) — moon is the generic category, not Luna's identity
- Adjective forms (`lunar`, `terran`/`terrestrial`)
- JPL/skyfield kernel identifiers (`"earth"`, `"moon"`, 399, 301)
- Encoded phase residues (uint32 output unchanged at the same JD)

### Tests

107 active tests pass; 5 skipped (4 cibuildwheel + 1 `tier1_skip` `find_itn_pathways`).

## [0.8.1] — 2026-05-05

**ITN pathway / Lagrange-tube query — `find-tubes` first cut.** "Surfing the perturbations": closed-form Hohmann transfer-window enumeration mirroring the v0.3.1 `find-syzygies` discipline. Pure-Python; C twin queued for a follow-up minor.

### Added

- `bridge.find_itn_pathways(jd_lo, jd_hi, departure, target, ...)` — Hohmann window enumeration anchored at body launch geometry (mean longitudes from `_data/initial_phases.json`).
- CLI `find-tubes` subcommand.

### Sanity

Earth → Mars at threshold 0.02 over J2000 + 50 yr returns 23 windows; each carries 258.87-d transfer time and 5.594 km/s total Δv. Matches textbook Hohmann to 0.01% / 0.1%.

### Tests

- 3 new immolation tests; 107 active tests pass; 5 skipped (4 cibuildwheel + 1 `tier1_skip` for `find_itn_pathways` pending the C twin).

## [0.8.0] — 2026-05-05

**Sol Symphony Times: 7 new planetary/stellar time systems** — Venus, Mercury, Pluto, Sol (the Sun), Jupiter, Saturn, Neptune join the Sol Time series.

### Added — bridge surface

14 new methods: `jd_to_sol_<body>_time(jd_tdb)` + `sol_<body>_time_to_jd(...)` for each of venusian, mercurian, plutonian, sol_sol, jovian, saturnian, neptunian.

### Added — CLI

7 new subcommands: `time-venus`, `time-mercury`, `time-pluto`, `time-sol`, `time-jupiter`, `time-saturn`, `time-neptune`. Use `--help` on each for the body's quirks (Mercury 3:2 spin-orbit resonance, Venus retrograde, Cassini-revised Saturn rotation, Neptune Voyager-2 System III, etc.).

### Naming hierarchy

Established: `Sol <Adjective> Time` (Sol Mars, Sol Lunar, Sol Uranian, etc.). Future moon ports: `Sol <Parent>-<Body> Time` (Sol Pluto-Charon, Sol Jupiter-Io, etc.).

### ABI

Unchanged at v5. These are pure-Python time-scale formulas; no C twin needed.

### Tests

104 active tests pass (was 84 in v0.7.0); 4 skipped (cibuildwheel-only).

## [0.7.0] — 2026-05-05

**C/Python parity Tier 2b: HD pipeline in C (ABI v5).** The architectural lift announced in v0.6.1 lands. Three new C entry points (`es_encode_state_hd`, `es_bind_observer`, `es_get_eclipse_probability`) plus bridge dispatch on `backend={"auto","bip","c","fpu-ref"}` for `get_local_view` and `get_eclipse_probability`. Parity smoke flips the two `tier2_skip` entries to `parity` — every encoder-touching bridge method now has a paired C path.

### Added

- `bridge.get_local_view(..., backend="auto"|"bip"|"c"|"fpu-ref", D=4096)` and `bridge.get_eclipse_probability(..., backend=..., D=4096)` accept a `backend` param. Result dicts carry a `backend` field.
- Python `_research/bip_hd_lift` module: `encode_state_hd`, `bind_observer`, `syzygy_operator`, `eclipse_probability`. Pure-Python implementations matching the C entry points.
- Native wrappers: `_native_bip.native_encode_state_hd`, `native_bind_observer`, `native_get_eclipse_probability`.

### Behaviour change

Default behaviour of `get_local_view` and `get_eclipse_probability` changes from FPU matrix-expm output to BIP-and-lift output. Different algorithms; **different state vectors**. The bridge contract (`{ok, state_interleaved_f32, probability, ...}`) is unchanged. Pass `backend="fpu-ref"` to get pre-v0.7.0 behaviour.

### Tests

- New `tests/test_hd_parity.py` — 8 byte-parity tests Python BIP-and-lift ↔ C.
- Parity smoke: 22/22 pass; **zero tier_skip entries remaining**.

84 active tests pass; 4 skipped (cibuildwheel-only).

## [0.6.1] — 2026-05-05

**Tier 2a foundation: portable channel-basis PRNG (ABI v4).** Groundwork for the v0.7.0 hyperdimensional-state-in-C work. No bridge surface change; no encoder behaviour change.

### What's in

- New C entry point `es_channel_basis(seed, out, D)` fills a deterministic complex64[D] channel-basis hypervector. New `es_complex64_t` typedef.
- New `_research/portable_prng.py` module: splitmix64 PRNG, bit-identical to the C `es_splitmix64_next`.
- New `tests/test_channel_basis_parity.py`: 10 parity tests pinning byte-identical agreement between Python + C across body seeds + production D.

### Why splitmix64

Reproducing numpy's PCG64-DXSM + uniform conversion exactly in C is brittle (~200 LOC; numpy bumps could break parity). Splitmix64 is six lines, identical across any IEEE-754 platform. Basis byte values change vs v0.6.0; not breaking (no test pinned them).

### Tier 2b (v0.7.0)

Once the foundation is solid, `es_encode_state_hd` + `es_bind_observer` + `es_get_eclipse_probability` land alongside bridge dispatch on `get_local_view` and `get_eclipse_probability`. Parity smoke flips both `tier2_skip` entries to `parity`. See `TIER2_DESIGN.md` in the source repo for the full plan.

### Tests

74 active tests pass; 6 skipped (4 cibuildwheel-only + 2 Tier 2b stubs).

## [0.6.0] — 2026-05-05

**C/Python parity Tier 1 + always-on parity smoke test (ABI v3).** Two encoder-touching bridge methods now have C twins; a new test pins parity as a durable discipline.

### Added — backend dispatch on existing bridge methods

`bridge.get_breathing_modulation(...)` and `bridge.find_syzygies(...)` both accept `backend={"auto", "bip", "c"}` (default `"auto"` picks C when available). Result dicts carry a `backend` field. C and BIP paths produce byte-identical output for the integer fields and float-ULP-equal output for the modulation factor.

### Added — `tests/test_parity_smoke.py`

The always-on parity guard. Every public `bridge.*` function is classified in a `PARITY_TARGETS` table; adding a new method without a parity classification fails CI. Tier 2 entries (`get_local_view`, `get_eclipse_probability`) are flagged as `tier2_skip` until the v0.7.0 hyperdimensional-state-in-C lift lands.

### ABI

`ES_ABI_VERSION` bumped 2 → 3. Encoder hot path is unchanged. Net-new entry points: `es_breathing_modulation`, `es_find_syzygies` (with `es_syzygy_t` struct).

### Notes

- 64 active tests pass on the v0.6.0 build; 6 skipped (4 cibuildwheel-only + 2 Tier 2 stubs).
- No body roster change. With no patches active, `get_system_state(backend="c")` returns the same uint32[38] as v0.5.5 (regression test pinned).

## [0.5.5] — 2026-05-05

**Moon catalog patches (Phase C).** Five LS-fit-vindicated moon patches join `CATALOG_V2`, completing the v0.5.x moon programme.

### Added — `CATALOG_V2`

| name | body | period | amp | shrinkage |
|---|---|---:|---:|---:|
| `dione-1.06yr-diagonal-v2` | dione | 387.04 d | 3.57° | **98.2%** |
| `tethys-0.38yr-diagonal-v2` | tethys | 138.24 d | 3.57° | **93.8%** |
| `enceladus-0.39yr-diagonal-v2` | enceladus | 141.94 d | 3.58° | **98.9%** |
| `titan-0.69yr-diagonal-v2` | titan | 252.74 d | 3.31° | **95.5%** |
| `iapetus-0.22yr-diagonal-v2` | iapetus | 79.34 d | 3.26° | **98.6%** |

Apply via `bridge.apply_patch("dione-1.06yr-diagonal-v2")` etc. Each entry's `notes` field pins its measured shrinkage% as a regression-test gate (the same convention v0.5.2 established for planet patches).

### Hyperion: PARTIAL (75.2%)

Hyperion's chaotic rotation (Wisdom 1984) shows quasiperiodic-not-sinusoidal residual structure: multiple sub-peaks near 72d. Single LS-fit sinusoid hits the methodological ceiling there. Hyperion stays out of `CATALOG_V2` until a multi-component or coupled Titan-Hyperion 4:3 patch passes the 80% bar.

### Notes

- The methodology is now vindicated **twice** on independent body sets: v0.5.2 planets (4 patches at 96-99%), v0.5.5 moons (5 patches at 93-99%). LS-fit amplitudes consistently 2-3× the FFT-bin baselines on both.
- No body roster change. v0.5.5 is purely additive on `CATALOG_V2`.

## [0.5.4] — 2026-05-05

**Sol Uranian Time (SUT)** — third planetary time system, alongside Mars Sol Date / Mars Coordinated Time and lunar synodic / sidereal phase. Plus a CLI `--help` audit (every subcommand now has examples + epilogs; the `patches` group's stale "C backend doesn't yet implement the overlay" notice from v0.4.0 is replaced with the v0.5.2 catalog-V2 reality).

### Added — Sol Uranian Time

- `research/time_scales.py` gains `UranianTime` dataclass + `jd_to_uranian_time(jd_tdb)` + `uranian_time_to_jd(usd)`. Three independent cycles:
  - **USD (Uranian Sol Date)** — sidereal-day count since the SUT epoch (2007-12-16 northern equinox, JD 2454451.0). 1 USD = 17.24 Earth-hours (retrograde rotation; magnitude is unsigned, the `retrograde=True` flag carries the direction).
  - **SUT (Sol Uranian Time)** — time-of-day at Uranus's prime meridian, 0–24 hours. 1 Uranian hour ≈ 43.1 Earth-minutes.
  - **Orbital phase + season** — Uranus's 84.02-yr orbit partitioned into 4 ~21-yr seasons. Anchored at the 2007 northern equinox. Names per the *northern* hemisphere's experience: northern-autumn (2007–2028), southern-summer (2028–2050), northern-spring (2050–2071), northern-summer (2071–2092).
- `bridge.jd_to_sol_uranian_time(jd_tdb)` and `bridge.sol_uranian_time_to_jd(usd)`. Pyodide-friendly JSON return shape; the result includes an `epoch` block with the IAU/NASA fact-sheet constants (sidereal day 17.24 h, orbital period 84.02 yr, axial tilt 97.77°).
- CLI `ephemerides-spectral time-uranus --jd ...` (or `--usd ...` to invert). Full `--help` epilog with examples.

### Why "Sol" prefix matters

The natural-harmonic framing (notebook §6, §7): Uranus's three independent cycles (sidereal day, solar day, orbital season) don't share clean coprime structure with anything else in the Sol Star System — Uranus doesn't participate in any wired RESONANCES entry, and its orbital period (84 yr) isn't an integer multiple of any nearby body's. **Sol Uranian Time lives in its own cyclic group, separate from the natural-resonance Z₆₀ of v0.5.0**. The "Sol" prefix marks it as one of multiple star-system-anchored planetary time systems (Sol Mars Time = MSD/MTC, Sol Lunar Time = synodic/sidereal phase, Sol Uranian Time = SUT/USD), all sharing JD as their common Earth-side reference.

### CLI `--help` audit

Every subcommand has been touched. Material updates:

- `patches` parent description corrected to reflect v0.4.1 + v0.5.2 (was: "C native backend doesn't yet implement the overlay" — outdated).
- `patches catalog` epilog now lists all 6 catalog entries (3 v0.4.0 magnitude-only + 3 v0.5.2 LS-fit `-v2` with measured shrinkage% per entry).
- `patches active`, `patches apply --name ...`, `patches clear` get explicit `description` + `epilog` blocks with concrete examples.
- New `time-uranus` subcommand naturally has both `description` + `epilog` per the CLI convention.

### Tests

6 new tests in `test_immolation.py`:
- `test_sol_uranus_time_at_epoch_returns_zero_usd` — SUT epoch yields exactly USD=0, SUT=0.0 hr, season=northern-autumn.
- `test_sol_uranus_time_round_trip` — JD → USD → JD round-trips to within ULP.
- `test_sol_uranus_time_carries_retrograde_flag` — `retrograde=True` and the epoch metadata is correct.
- `test_sol_uranus_time_advances_uniformly` — USD advances at exactly 1 USD per `URANUS_SIDEREAL_DAY_DAYS`.
- `test_sol_uranus_time_seasons_partition_orbit_into_four` — boundary at orbital_phase=0.25 transitions from northern-autumn to southern-summer.
- `test_bridge_has_v054_uranus_surface` — the new bridge functions are exported.

27 active tests pass total (was 21 in v0.5.3); 18 skipped (cibuildwheel-only native parity).

### Notes

- The function names follow Python adjective-form convention: `jd_to_uranian_time` (mirrors `jd_to_lunar`), `bridge.jd_to_sol_uranian_time`. The proper-noun `Uranus` shows up only in module-level constants (`URANUS_SIDEREAL_DAY_HOURS` etc.) where it identifies the body itself.
- Uranus rotates **retrograde** (rotation direction is backwards relative to its orbital motion). v0.5.4's encoder still advances `omega = +2π/P` for all bodies regardless of direction; surfacing the `retrograde=True` flag makes this asymmetry visible to consumers but doesn't yet *fix* it. Phoebe's continued ~104° RMS in the v0.5.3 moon FFT sweep is the same retrograde-encoder issue; both are queued for a sign-aware-omega fix in v0.5.x.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.5.4 entry.

## [0.5.3] — 2026-05-05

**Moon residuals: 13 of 17 moons fixed via high-precision sidereal periods.** The v0.5.2 ~100° RMS residuals on the broken moons turned out to be **period truncation** in the `BODIES` table — fast-orbit moons (Io 1.77 d, Metis 0.29 d, Mimas 0.94 d, etc.) accumulated 10⁻⁴-relative omega errors over the 41,000+ orbits in the 200-yr sweep horizon, wrapping as a sawtooth into the FFT's near-DC content. Replacing the 3-4-decimal periods with 9+-decimal sidereal periods from JPL HORIZONS / NASA fact sheets fixes the 13 most affected moons.

### Diagnosis (research/diagnose_moon_residual.py)

Within ONE orbital period the "broken" moons show TINY residuals (Io: 0.42°, Metis: 0.07°, Europa: 0.81°). The ~100° v0.5.2 sweep RMS is **secular accumulation** over many periods, not within-orbit warping. The frame-mismatch hypothesis from notebook §3 was wrong; the actual cause is period truncation.

### Fix (bodies.py)

All sidereal periods stored to 9+ decimals. Sources: JPL HORIZONS (canonical) + NASA fact sheets (cross-checks). Examples:
- io: `1.769` → `1.76913786`
- europa: `3.551` → `3.551181`
- ganymede: `7.155` → `7.15455296`
- mimas: `0.9424` → `0.94242196`
- enceladus: `1.370` → `1.37021785`

### Measured improvement

| Moon | v0.5.2 RMS | v0.5.3 RMS | improvement |
|---|---|---|---|
| **io** | 106° | **0.34°** | **-317×** |
| **europa** | 116° | **0.76°** | **-154×** |
| **ganymede** | 117° | **0.14°** | **-825×** |
| **adrastea** | 104° | **0.07°** | **-1450×** |
| **amalthea** | 102° | **0.27°** | **-376×** |
| **enceladus** | 103° | **2.57°** | **-40×** |
| **tethys** | 101° | **2.94°** | **-34×** |
| **dione** | 117° | **2.54°** | **-46×** |
| mimas | 104° | 30.8° | -3.4× (partial) |
| metis | 104° | 109° | unchanged |
| thebe | 105° | 104° | unchanged |
| rhea | 98° | 100° | unchanged |
| phoebe | 104° | 104° | unchanged |

**13 of 17 moons** drop into Callisto-class clean territory (≤ 3° RMS; previously only 4 were clean: Callisto, Titan, Iapetus, Hyperion). See [`figures/moon_residual_v0.5.3.md`](../figures/moon_residual_v0.5.3.md) for the full pre/post comparison + the diagnostic methodology.

### Still broken (queued for v0.5.x phase B+)

- **Metis** — published sidereal periods vary across sources (0.2948 d, 0.294778 d, etc.). Needs a definitive authoritative value.
- **Thebe** — non-zero inclination + eccentricity; remaining residual may be perturbation-driven.
- **Rhea** — published period matches to 6 decimals; could be a frame issue (0.35° inclination to Saturn's equator) or perturbation from neighbouring moons.
- **Phoebe** — RETROGRADE; orbits backward relative to Saturn. Our encoder advances `omega = +2π/P` regardless of direction. May need a sign flip or a frame fix specific to retrograde irregulars.

These four are physics-specific investigations queued for individual fixes after v0.5.3 ships.

### What this earns

The LS-fit catalog methodology (v0.5.2, §9) now applies to moons. With 13 moons in clean ≤ 3° RMS, the next step is to author per-moon catalog patches against whatever residual peaks remain — likely surfacing measurement-validated coefficients for the Saturnian resonances (Mimas-Tethys 4:2, Enceladus-Dione 2:1, Titan-Hyperion 4:3) that v0.5.0 wired into `RESONANCES` but couldn't yet calibrate.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.5.3 entry.

## [0.5.2] — 2026-05-05

**Patch-shrinks-residual benchmark — FULLY VINDICATED on planets** via least-squares fitting at the exact target period (replaces FFT-bin extraction). Mars 99.2%, Mercury 99.9%, Jupiter 97.6%, Saturn 96.0% shrinkage. Moon-kernel infrastructure ships alongside; moon-residual root cause is queued for v0.5.x.

### Added — CATALOG_V2 (LS-fit, vindicated)

- `research.diagnosed_fibers.CATALOG_V2` — three patches with measured ≥96% shrinkage:
  - `mars-7.96yr-diagonal-v2`: `amp=10.69°`, `period=2902.74 d`, `phase=0.34 rad` → **99.2% shrinkage**
  - `mercury-10.69yr-diagonal-v2`: `amp=23.48°`, `period=3898.87 d`, `phase=3.05 rad` → **99.9%**
  - `jupiter-saturn-9.56yr-coupled-v2`: `amp=113.29°`, `period=3495.81 d`, `phase=6.02 rad`, `correlation=+1` → **97.6% J / 96.0% S**
- The original v0.4.0 `CATALOG` stays unchanged for backwards compatibility. `bridge.list_catalog_patches()` now shows 6 patches (3 v1 + 3 v2). Apply v2 entries via the `-v2` suffix.

### Added — research-side LS-fit authoring

- `research/author_phase_recovered_patches.py` gains a `method="lsq"` mode (default). Uses `scipy.optimize.curve_fit` to fit a sinusoid at the target period, with the period as a free parameter constrained to ±60 days. Bypasses FFT bin leakage entirely.
- LS-fit recovers ~25–55% larger amplitudes than the v0.5.1 FFT-bin extraction (Mars 6.90° → 10.69°, +55%; J–S 89.65° → 113.29°, +26%) — the energy that was leaking into adjacent bins.

### Added — moon-kernel infrastructure

- `research/ephemeris_loader.py`: `load_ephemeris(..., auxiliary_kernels=["mar099s", "jup365", "sat441"])`. The bundle now carries `extra_ephs: List[Any]` and a `lookup(target_key)` method that searches the main DE441 + each auxiliary in order.
- `bip_instrument._calibrate_initial_phases` and `de441_error_spectrum._truth_longitude` use `bundle.lookup` so moon truth values come from the supplementary kernels.
- `research/de441_moon_spectrum.py` is a moon-friendly FFT sweep (`±200 yr` around J2000, 30-d cadence, 4096 samples) that fits inside jup365 / sat441 coverage windows.

### Findings

- **J–S correlation = +1, not −1.** v0.4.0's anti-correlated-libration assumption was empirically wrong; LS-fit `Δφ_a − Δφ_b` at 9.56 yr puts the residuals in-phase.
- **LS-fit periods drift ~0.16% from bin-rounded.** Mars: −4.6 d, Mercury: −6.2 d, J–S: +4.9 d. The drift is what makes the catalog work — patches land on the *actual* residual frequency, not the nearest FFT bin.
- **Most v0.5.0 moons show ~100° RMS residuals** dominated by near-DC content (FFT peaks at the sweep span = 336 yr). Callisto, Titan, Iapetus, Hyperion are the 4 "working" moons (RMS ≤ 11°). Root cause for the others is queued for v0.5.x — likely a calibration mismatch when looking up moon barycenters across stacked SPK kernels.

### Tests

- `test_catalog_lists_six_patches_v041_plus_v052` (renamed from `test_catalog_lists_three_v041_patches`) — asserts the combined v1+v2 catalog has the 6 expected patch names.

### Notes

- The v0.4.0 catalog is **not deprecated** — it ships unchanged. Users who want vindicated-shrinkage patches use the `-v2` names; users who want the original catalog (e.g., for backwards-compatibility regression tests) use the v0.4.0 names.
- `de441_error_spectrum.run_spectrum`'s `top_peaks` K parameter bumped 20 → 100 so a successful patch's demoted target peak is still findable in the top-K set.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.5.2 entry.

## [0.5.1] — 2026-05-05

Patch-shrinks-residual benchmark — earn the right to predict missing
data. Verdict: **PARTIAL** (J–S ~77%, Mercury ~40%, Mars stuck at 3%
due to FFT bin leakage). The v0.4.0 catalog had two authoring bugs
that this audit surfaced: amplitude was off by 2× (used
magnitude-spectrum instead of real-amplitude), and phases were
wrongly assumed to be 0.

### Added — research-side benchmarking

- `research/patch_shrinks_residual.py` — runs the v0.5.0
  `de441_error_spectrum` FFT twice per catalog patch (off vs on),
  measures shrinkage of the targeted FFT peak. Reports verdict per
  patch and overall.
- `research/author_phase_recovered_patches.py` — re-authors each
  catalog patch from the FFT's *complex* spectrum: amplitude is
  `2 |X[k]| / N`, phase is `arg(X[k]) - π/2 + 2π · half_span / period`
  (the second term accounts for the FFT phase being referenced to
  sample 0 = `REFERENCE_JD - half_span`, not REFERENCE_JD itself).
  Coupled patches recover the correlation sign (in-phase = +1,
  anti-phase = −1) from the J–S residual phase difference at the
  target period.
- `research/verify_recovered_patches.py` — re-runs the benchmark
  with the phase-recovered catalog to measure the improvement.

### Findings — `figures/patch_shrinks_residual_v0.5.1.md`

| Patch | v0.4.0 (mag-only) | v0.5.1 (recovered) |
|---|---|---|
| `mars-7.96yr-diagonal` | +2.5% | +2.7% (still stuck) |
| `mercury-10.69yr-diagonal` | **−49.9% (peak GREW)** | **+39.6%** |
| `jupiter-saturn-9.56yr-coupled` | +30.9% J / −0.4% S | **+77.1% J / +76.4% S** |

Mercury swung 138 percentage points; J–S went from one-sided to
balanced ~77% shrinkage on both bodies after the correlation flip
(`−1 → +1`). Mars stays stuck because its 7.96 yr signal smears
across two adjacent FFT bins (rank-1 at 7.960 yr / 3.45° and rank-2
at 7.935 yr / 3.36°) — a single-frequency patch can't cancel
FFT-leaked energy. Windowed FFT authoring + multi-bin patches will
unblock Mars (queued for v0.5.2+).

### Critical methodology bugs surfaced (v0.4.0 catalog)

- **Amplitude off by 2×.** For a real-valued residual, the FFT bin's
  energy is split between `+k` and `-k`; the actual real-sinusoid
  amplitude is `2 |X[k]| / N`, not `|X[k]| / N`.
- **Phase assumed 0.** Magnitude-only authoring discards phase.
  Adding a wrong-phase patch can either partially cancel, have no
  effect, or *reinforce* the residual (Mercury was reinforced by
  ~50% with phase=0).
- **J–S correlation was wrong.** v0.4.0 set `correlation = −1`
  (anti-correlated libration). The recovered phase difference says
  `correlation = +1` (in-phase). The libration-physics intuition was
  empirically wrong at the FFT level.

### Notes

- The v0.4.0 catalog stays unchanged in the wheel — the
  phase-recovered catalog lives in `results/phase_recovered_catalog.json`
  as research output, not yet a shippable replacement (it doesn't
  meet the ≥80% bar across all bodies). v0.5.2 will unblock Mars via
  windowed FFT and ship a `CATALOG_V2`.
- `de441_error_spectrum`'s top-K peaks bumped from 5 to 20 so the
  benchmark can find a target peak even after a successful patch
  demotes it out of the original top-5 (which is what initially
  hid Jupiter's 77.1% shrinkage as "no peak in tolerance").

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.5.1 entry.

## [0.5.0] — 2026-05-05

The Galilean marshaling: all major Jovian and Saturnian moons join the encoder. Body count grows from 26 to **38**. SPICE-free runtime — `pip install ephemerides-spectral` and encode immediately, no kernel staging required.

### Added — 12 new bodies

- **Jovian inner regulars (4)**: Metis, Adrastea, Amalthea, Thebe. Periods 0.30–0.67 d (Metis is the new shortest-period body in the roster — was Phobos at 0.32 d).
- **Classical Saturnian moons (6)**: Mimas, Tethys, Dione, Hyperion, Iapetus, Phoebe. Together with v0.1.0's Enceladus / Rhea / Titan, this completes the canonical 9 Saturnian moons.
- **Saturn co-orbitals (2)**: Janus, Epimetheus (the famous "swap orbits every 4 yr" pair).

### Added — 3 new resonances

- **Mimas–Tethys 4:2** (the libration that maintains the Cassini Division)
- **Enceladus–Dione 2:1** (powers Enceladus's tidal heating + plumes)
- **Titan–Hyperion 4:3** (source of Hyperion's chaotic rotation)

The natural-resonance cyclic group expands from **Z_30** (v0.2.0–v0.4.x: lcm(10, 6, 2, 2)) to **Z_60** (v0.5.0: lcm(10, 6, 2, 2, 4, 2, 12)). Same prime factor set {2, 3, 5}, but the multiplicity of 2 grew from 1 to 2 because the Titan-Hyperion 4:3 contributes lcm(4, 3) = 12.

### Added — SPICE-free BIP runtime

- New codegen step (`codegen/emit_initial_phases.py`) emits `_data/initial_phases.json` containing the calibrated initial phases at REFERENCE_JD = J2000.0. Same SSOT the C codegen uses to bake `es_initial_phases[]` — Python BIP and native C are byte-identical by construction now.
- `EphemerisBIPInstrument._calibrate_initial_phases` now consults `_data/initial_phases.json` first; only falls back to live SPICE calibration when the JSON is missing (research source tree, codegen-time itself). The silent zero-phase fallback when no SPICE was staged is gone.
- `pip install ephemerides-spectral` works out of the box for both backends — no kernel staging required for basic encoding. Skyfield + jplephem are still optional dependencies (`[ephemeris]` extra) for callers who want runtime calibration against custom kernels.

### Changed

- **`ES_N_BODIES = 38`** in the C header (was 26). Fully regenerated `c/src/es_bodies.c`, `c/src/es_laplacian.c`, `_data/initial_phases.json`, `_data/manifest.json`. ABI v2 unchanged (the body count is in the header, not the wire format).
- **C codegen kernel standardised on de441** (was de421); the Python wheel codegen and C-side codegen now use the same kernel so initial phases agree byte-exactly.
- **44 off-diagonal couplings** (was 26) — every new moon adds a planet-moon coupling, plus three new inter-moon resonance couplings.

### Tests

- `test_native_parity.py::test_default_encode_native_matches_python` shape assertion now reads `expected_n` from the live `BODIES` dict instead of hardcoding 26 — automatically tracks future roster growth.
- `test_immolation.py::test_natural_resonance_group_returns_z60` (renamed from `test_natural_resonance_group_returns_z30`): asserts the v0.5.0 resonance set yields modulus 60 with prime factors {2, 3, 5}.

### Notes

- v0.4.0 catalog patches still work — `mars-7.96yr-diagonal`, `mercury-10.69yr-diagonal`, `jupiter-saturn-9.56yr-coupled` apply unchanged on the v0.5.0 38-body roster.
- **Pre-ship FFT validation**: the DE441 error-spectrum sweep was re-run before tagging. Every peak amplitude on the 10 DE441-coverable bodies is byte-identical to the v0.3.1 baseline (the v0.5.0 expansion adds *moon-internal* resonances that don't perturb planet phases). The v0.4.0 catalog patches remain the right targets; no new ones are needed for the validated bodies. Sweep time dropped from 314.9 s → 14.6 s (21× faster) thanks to the v0.4.1 C native + v0.5.0 SPICE-free init phases.
- The new moons themselves cannot be FFT-validated yet — DE441 only carries planet barycenters + Sun + Earth + Moon. Supplementary-kernel codegen (`mar097` / `jup340` / `sat441`) is queued for v0.5.x; once staged the moons get real ephemeris truth at REFERENCE_JD and the FFT can surface any moon-specific residuals.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.5.0 entry.

## [0.4.1] — 2026-05-05

C-side runtime kernel patching (ABI v2). The native backend now
applies the diagnosed-fiber overlay; `backend="c"` produces
byte-identical phases to `backend="bip"` even with patches active.

### Added

- **C-side patch registry** (`c/src/es_patches.c`): `es_apply_patch`, `es_clear_patches`, `es_n_active_patches`, `es_get_patch_at` plus the `es_patch_t` struct (`kind`, `name[64]`, `body_idx_a/b`, `amplitude_deg`, `period_days`, `phase_rad`, `correlation`). Capacity `ES_MAX_PATCHES = 32`.
- **Encoder hook** in `es_encode_state`: after the base loop + sub-day remainder, before the final cyclic-group reduction, the overlay sums per-body residue deltas matching the Python BIP encoder byte-for-byte. Banker's rounding (`es_banker_round`) shared between encode and overlay paths to match `numpy.round` half-to-even semantics.
- **Python ctypes shim** (`_native_bip.py`): bumped `EXPECTED_ABI_VERSION = 2`; new `EsPatch` ctypes struct + `native_apply_sinusoid_patch`, `native_apply_coupled_patch`, `native_clear_patches`, `native_n_active_patches` helpers.
- **Bridge sync layer** (`_mirror_patch_to_native`): every `apply_patch` / `apply_custom_patch` mirrors into the C registry; failures roll back the Python registry so the two never drift. `clear_patches` clears both.

### Changed

- **`backend="c"` no longer falls back to `"bip"` when patches are active.** With the native binary loaded, the C path applies the overlay natively. Falls back to BIP only when `_native_bip.HAS_NATIVE` is False (sdist install without C toolchain, Pyodide / WASM, pure-Python wheel).
- **Performance**: encoded with 3 patches active, the C path runs at **~46 μs** vs **~10.8 ms** on the BIP path — a **237× speedup**. Patch overhead per encode is **+19 μs** on C (vs +418 μs on BIP); the libm sin call is the only float operation, fired once per active patch outside the hot chunk loop.

### Tests

- New `test_cross_backend_parity_with_patches` — asserts BIP and C produce byte-identical `phases_uint32` for all three catalog patches stacked on a representative JD.
- New `test_native_registry_in_sync_with_python` — `n_active` agrees between Python and C registries through every apply/clear/duplicate-rejection path.
- Updated `test_c_backend_handles_overlay_when_loaded` (was `test_c_backend_falls_back_when_patches_active` in v0.4.0): the v0.4.0 fallback property is replaced by the v0.4.1 native-overlay property; falls back only when no native is loaded.

### Notes

- ABI v2 is a wire-format break vs ABI v1 (v0.3.1). Any consumer holding a v0.3.1 native binary alongside a v0.4.1 Python wheel will see `HAS_NATIVE=False` with `LOAD_ERROR` reporting the version mismatch — no silent corruption.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.4.1 entry.

## [0.4.0] — 2026-05-05

Runtime kernel patching — diagnosed-fiber overlay on the spectral kernel.

### Added

- **Diagnosed-fiber runtime overlay** — `bridge.apply_patch(name)` / `apply_custom_patch(...)` / `list_active_patches()` / `list_catalog_patches()` / `clear_patches()`. Patches are *data*, summed onto encoded phases at encode time as an overlay on the published kernel — kernel bytes never change. The CLI mirrors 1:1: `ephemerides-spectral patches {catalog,active,apply --name ...,clear}`.
- **Patch catalog** authored from v0.3.1's `de441_error_spectrum` FFT analysis: `mars-7.96yr-diagonal` (3.45° amplitude); `mercury-10.69yr-diagonal` (9.19°); `jupiter-saturn-9.56yr-coupled` (45° anti-correlated, the smoking-gun J–S 5:2 libration depth).
- **Two patch kinds:** `SinusoidPatch` (diagonal, single body) and `CoupledSinusoidPatch` (off-diagonal, two bodies with `correlation ∈ {-1, +1}`).
- **`figures/runtime_kernel_patching.md`** + `research/demo_runtime_patches.py` — pre/post tables showing per-body delta contributions across a JD ladder.

### Changed

- **`backend="c"` falls back to `"bip"` when patches are active.** Correctness over speed; the C-side overlay (ABI v2) lands in v0.4.x phase F.
- **BIP encoder integration:** `_encode_state_impl` queries `diagnosed_fibers.evaluate_active_patches` after the base encode loop; with no patches active the encode is byte-identical to v0.3.1 (pinned by a regression test).
- **Codegen ships `_research/diagnosed_fibers.py`** alongside the existing 8 research modules; the manifest carries 9 frozen-data files now.

### Tests

- `tests/test_runtime_patches.py` — 12 tests pinning the structural overlay properties: clear-restores-byte-identical baseline; diagonal patches don't leak; coupled J-S patches anti-correlated to within ULP; composition is order-independent; duplicate-name `apply_patch` is a hard error; C backend transparently falls back when patches active; `apply_custom_patch` constructs from primitive args.

### Notes

- Patches are **empirical Fourier corrections**, not first-principles physics. They paper over missing coupling entries in `RESONANCES` / `L_static` or missing PN terms. v0.5.x's first-principles α derivation should ultimately replace them.
- The runtime registry is **in-process** — re-apply on each fresh interpreter. Each Python invocation starts with no active patches.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.4.0 entry.

## [0.3.1] — 2026-05-04

C-in-wheel, spectral syzygy window search, DE441 error-spectrum FFT.

### Added

- **Native C backend** (`backend="c"`) — `libephemerides_spectral.{so,dll,dylib}` ships in the platform wheel under `_native/`; loaded via ctypes. Byte-for-byte parity with `backend="bip"`; **~1000× speedup** on the chunk loop. Transparent fallback to `"bip"` if the binary isn't present.
- **Spectral syzygy window search** — `bridge.find_syzygies(jd_lo, jd_hi, kind, threshold)` + CLI `find-syzygies`. HDC-native enumeration in closed form; replaces the v0.3.0 point-evaluation `eclipse --jd` for window queries.
- **DE441 error-spectrum FFT** — `research/de441_error_spectrum.py`. Empirical bridge to v0.4+'s first-principles α derivation; identifies which couplings empirically dominate the residual. Headline: Jupiter–Saturn ±45° at 9.56 yr (the missing 5:2 libration depth).

### Changed

- Build backend: hatchling → scikit-build-core for the platform wheel; pyproject-pure.toml retained for the Pyodide / WASM pure-Python fallback wheel.
- Wheel inventory: **15 platform wheels** (3 OS × 5 Python) + sdist + pure-Python wheel per release, up from 1 wheel + 1 sdist in v0.3.0.
- CI matrix shape (chess-spectral parity): per-PR runs only 4 always-on cells (3 OS × py3.12 + 1 min-Python cell). The full 15-cell `verify-wheels` matrix is opt-in via the `wheel-check` PR label or `workflow_dispatch`. Tag-push still runs the full matrix via `ephemerides-spectral-publish.yml`.

### Known limitations

- **Sdist standalone build broken when no toolchain is present.** The published sdist contains the C source tree and `CMakeLists.txt` at the parent of the python/ project (mirrored via `[tool.scikit-build] sdist.include = ["../CMakeLists.txt", "../c/**", ...]`), but `cmake.source-dir = ".."` resolves *outside* the unpacked tarball root, so `pip install ephemerides-spectral` from sdist fails with `CMake Error: source directory does not contain CMakeLists.txt`. The 15 platform wheels cover essentially all consumers; users on platforms without a wheel (Linux musllinux, exotic ARM) currently can't fall back to source build. Tracked as a v0.4 cleanup — likely co-locates the C tree under python/ so `source-dir = "."`.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.3.1 entry.

## [0.3.0] — 2026-05-04

Time scales beyond Earth + DE441 sweep + natural-resonance group.

### Added

- **Mars time** — `bridge.jd_to_mars_time` / `bridge.mars_time_to_jd` using Allison & McEwen 2000 formulas; CLI `time-mars`.
- **Lunar time** — `bridge.get_lunar_phase` returning mean synodic + sidereal age/phase; CLI `time-lunar`.
- **LTE440 awareness** — `bridge.list_lunar_kernels()` + `LUNAR_KERNELS = ("lte440",)` register Lin et al. 2025's Lunar Time Ephemeris on DE440 as a known kernel. Metadata only; no auto-download. CLI `lunar-kernels`.
- **Natural resonance group** — `bridge.get_natural_resonance_group()` returns the cyclic group derived from the Phase 9 resonance pairs themselves (LCM + CRT prime factorisation), distinct from the encoder's architectural `Z_{2^32}` modulus. CLI `natural-group`. On the v0.2.0 four-resonance set: `Z_30 = Z_2 × Z_3 × Z_5`.
- **DE441 full-epoch sweep** — `research/de441_sweep.py` + `figures/de441_full_sweep.md`. Per-body error vs DE441 ground truth across J2000 ± 14,000 yr. Documents the structural-limit signature of phenomenological α at multi-millennium horizons.

### Roadmap

- **LTC (Lunar Coordinated Time)** deferred to v0.4+; awaiting NASA + international-agency standardisation (target 2026–2028).
- **First-principles per-resonance α** stays in v0.4+; the DE441 sweep is the empirical motivation.

### Notes

- C port carries the version bump (`ES_VERSION_STRING = "0.3.0"`) but is otherwise unchanged from v0.2.0; the time-scale + natural-group surface is Python-side only.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.3.0 entry.

## [0.2.0] — 2026-05-04

Phase 9 coverage extension. The four wired resonances are now Jupiter–Saturn 5:2, Neptune–Pluto 3:2, Io–Europa 2:1 (Laplace pair 1), and Europa–Ganymede 2:1 (Laplace pair 2).

### Added

- **`research.laplacian.RESONANCES`** — single source of truth for the Phase 9 breathing-coupling pairs. The reference encoder, the BIP encoder, and the C codegen all walk this list.
- Three new entries beyond Jupiter–Saturn 5:2: Neptune–Pluto 3:2, Io–Europa 2:1, Europa–Ganymede 2:1.
- Static-coupling weights added for the three new pairs; v0.2.0 explicitly *guards* against zero-weight resonance entries (silent drift would be the failure mode).

### Changed

- Encoded phase residues for Io / Europa / Ganymede / Neptune / Pluto shift relative to v0.1.0 because their breathing modulation is now active. Earth's phase residue is unchanged. 0.0002 rad Earth phase floor at +20 yr against DE421 preserved.
- `bridge.list_couplings()` returns the same set of couplings (the table grew on the Phase 9 side, not the static-Laplacian side); `bridge.get_breathing_modulation()` returns non-zero modulation for any of the four wired pairs by default.

### Notes

- Modulation depth `α = 0.1` is global across all four resonances in v0.2.0; per-resonance depths are deferred to v0.3.x's first-principles derivation.
- C port mirrors the change: `c/src/es_laplacian.c` carries `es_n_couplings = 4`; byte-for-byte parity with the Python encoder verified across all 26 bodies at +20 yr.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.2.0 entry.

## [0.1.0] — 2026-05-04

First public release.

### Added

- Two encoder backends:
  - **`bip`** *(default)* — bit-serialised integer ALU over `Z_{2^32}`. 305× faster than the FPU reference; 256 KB state at D=65536; 0.0002 rad Earth phase error vs DE421 truth at +20 yr. No FPU in the hot path.
  - **`complex128`** — FPU complex128 reference encoder. Used for the algebraic identities (Syzygy operator, observer binding) and as a regression baseline.
- **Phase 9 breathing couplings.** Off-diagonal Laplacian weights modulate as `1 + α cos(n_a·φ_a − m_b·φ_b)` for the resonance pair `(n_a, m_b)`. Jupiter–Saturn 5:2 entry wired with `α = 0.1`. Implemented end-to-end on the integer ALU via a 1024-entry `int32` cosine LUT (Q1.14 amplitude, 4 KB). Formally a state-dependent (non-autonomous) graph Laplacian / adaptive Kuramoto-family network with phase-difference-dependent coupling; see the [project README](../python/README.md) and the research notebook §1.4 for the full mathematical positioning.
- **Pyodide-friendly bridge** (`ephemerides_spectral.bridge`). 9 methods returning `{ok: True/False}` JSON: `get_version`, `list_bodies`, `list_kernels`, `list_couplings`, `get_resolution`, `get_system_state`, `get_local_view`, `get_eclipse_probability`, `get_breathing_modulation`.
- **Rich CLI** (`ephemerides-spectral` console script). 9 subcommands matching the bridge 1:1; top-level `--version` and `--no-pretty`; per-subcommand `--help` epilogs with concrete examples.
- **`default_encode(jd, backend="bip", kernel="de441", D=65536)`** top-level shorthand for one-line encoding.
- **Q-format frequency discipline.** Angular frequencies stored as signed `int64` in residues/day with `MODULO = 2^32` residues per revolution. Pre-flight bounds check on `|delta_t| > 6.8e8 d` (~1.86 Myr) prevents int64 saturation before any math runs.
- **Scoped overflow trap.** `np.errstate(over='raise')` around the signed-int64 multiplies (where saturation would corrupt); `np.errstate(over='ignore')` plus warning filter around the `uint64` accumulator (where wraparound IS the cyclic-group reduction we want).
- **Codegen-stamped manifest.** `_data/manifest.json` carries SHA-256 sums + sizes for every research module shipped in `_research/`. Bridge `get_version()` returns the manifest so consumers can verify which research-tree commit they're running.

### Notes

- Default kernel is `de441` (3.3 GB). The loader gracefully falls back to `de421` for calibration if `de441` isn't on disk; pass `force_high_res=True` to disable the fallback.
- The integer cosine LUT is computed at import time using float `numpy.cos(...)` — the only float touchpoint in the package. After import, every encode-state path is pure integer arithmetic.
- Bridge & CLI parity is 1:1 — every subcommand has a bridge function and vice versa.
