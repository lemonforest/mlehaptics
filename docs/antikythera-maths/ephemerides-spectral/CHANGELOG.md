# ephemerides-spectral CHANGELOG

All notable changes to this package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

(no entries yet — next entries land after v0.4.1)

## [0.4.1] — 2026-05-05

C-side runtime kernel patching (ABI v2). Native overlay surface; cross-backend byte-exact parity with patches active.

### Architecture: completing the v0.4.0 overlay design

v0.4.0 shipped the diagnosed-fiber overlay on the BIP (pure-Python) encoder and gated `backend="c"` to fall back to BIP when patches were active. v0.4.1 closes that gap: the native C library now carries its own patch registry, and the encode-state path consults it after the base loop / before the final reduction, mirroring the BIP encoder's overlay step exactly.

The Python and C registries are kept in lockstep via a sync layer in the bridge: every `apply_patch` mirrors into both; `clear_patches` clears both; rejection on either side rolls back the other. Two registries, one source of truth, byte-exact parity verified.

### Added — C-side overlay (`es_patches.c`)

- **`es_patch_t` struct** with `kind` (sinusoid / coupled-sinusoid), `name[64]`, `body_idx_a/b`, `amplitude_deg`, `period_days`, `phase_rad`, `correlation`. Plain-data layout for stable ctypes binding.
- **Registry API**: `es_apply_patch(const es_patch_t *)`, `es_clear_patches()`, `es_n_active_patches()`, `es_get_patch_at(idx, *out)`. Status codes for capacity / duplicate-name / bad-index / bad-param errors. Capacity `ES_MAX_PATCHES = 32`.
- **Encoder hook** in `es_encode_state`: `es_apply_overlay_to_phases(delta_t_days, curr_phases)` runs after the sub-day remainder step, before the final `& MODULO_MASK` reduction. Zero-cost when registry is empty (single early-return).
- **Banker's rounding sharing**: `es_banker_round` (was `static inline` in `es_encode.c`) is now external linkage so `es_patches.c` can match Python's `round()` half-to-even semantics on the overlay delta. Required for byte-exact parity.

### Added — ABI v2 ctypes binding

- `EXPECTED_ABI_VERSION = 2` in `_native_bip.py`. The load-time check refuses any binary reporting a different ABI — silent corruption from a stale wheel can't happen.
- `EsPatch` ctypes structure mirroring `es_patch_t` field-for-field; locked by the load-time ABI assertion.
- High-level helpers: `native_apply_sinusoid_patch(name, body_idx, amplitude_deg, period_days, phase_rad)`, `native_apply_coupled_patch(name, body_idx_a, body_idx_b, amplitude_deg, period_days, phase_rad, correlation)`, `native_clear_patches()`, `native_n_active_patches()`. All no-ops when `HAS_NATIVE=False`.

### Added — bridge sync layer

- **`_mirror_patch_to_native(patch)`** — applies a Python `Patch` into the C-side registry by name + integer body index; rolls back the Python-side change on C-side rejection so registries can't drift. Called from `apply_patch` and `apply_custom_patch`.
- **`_native_clear_patches()`** — wraps the native helper; called from `clear_patches` after the Python-side wipe.
- **`_body_index(name)`** — resolves a Python body name to its integer index, mirroring the canonical sorted body order baked into the C codegen.

### Changed

- **`backend="c"` now applies the overlay natively** when the binary is loaded. The v0.4.0 fallback gate on `_patches.has_active_patches()` is removed. Falls back to BIP only when `HAS_NATIVE=False`.
- **Performance** with 3 catalog patches active (encoded at +20 yr against DE421):
  - `backend="bip"` — 10.8 ms / encode (+418 μs vs no-patches)
  - `backend="c"`   — 0.046 ms / encode (+19 μs vs no-patches)
  - **C is 237× faster than BIP** with patches active.
- **Test `test_c_backend_falls_back_when_patches_active`** renamed to `test_c_backend_handles_overlay_when_loaded` and asserts the v0.4.1 behavior (native applies overlay; falls back only when not loaded).

### Tests

- **`test_cross_backend_parity_with_patches`** — encodes `TEST_JD = J2000 + 20 yr` with all 3 catalog patches active on both backends; asserts `bip["phases_uint32"] == c["phases_uint32"]` byte-for-byte.
- **`test_native_registry_in_sync_with_python`** — verifies `n_active` agrees between registries through apply / clear / duplicate-rejection paths.

### ABI breakage (intentional)

ABI v1 (v0.3.1, v0.4.0) → ABI v2 (v0.4.1). Any v0.4.1 Python wheel paired with a v0.3.1 native binary will refuse to load native (`HAS_NATIVE=False` with a clear `LOAD_ERROR` message); the package falls back to pure-Python BIP. PyPI ships matching Python+C versions in every wheel, so consumers using `pip install ephemerides-spectral==0.4.1` always get a matched pair.

### Build

- `CMakeLists.txt` adds `c/src/es_patches.c` to the shared library sources. `WINDOWS_EXPORT_ALL_SYMBOLS ON` already in place; the new exports surface automatically. No new build flags / no toolchain version bumps.

## [0.4.0] — 2026-05-05

Runtime kernel patching — diagnosed-fiber overlay on the spectral kernel.

### Architecture: overlay, not bones-mutation

The spectral kernel — the static `RESONANCES` table, the Laplacian construction, the integer Q-format frequencies — is the **published truth**. We don't mutate it to chase residuals.

Patches are **overlays**. They live in a module-level registry, are authored as data (not code edits), and contribute per-body residue deltas at encode time AFTER the base encode loop has finished. The base encoder bytes never change. Inspired by Linux ksplice / kpatch.

This is the application surface for the v0.4.x diagnosed-fiber-patches roadmap entry: patches are *authored* from FFT residual peaks (per the v0.3.1 `de441_error_spectrum` analysis), but *applied* via the overlay so the published kernel hash stays pinned forever. A bricked patch is unloadable / disposable; the kernel keeps shipping clean.

### Added — `diagnosed_fibers` runtime overlay

- **`research/diagnosed_fibers.py`** — `DiagnosedPatch` dataclass family (`SinusoidPatch` for diagonal, `CoupledSinusoidPatch` for off-diagonal pairs); module-level `_ACTIVE` registry (RLock-guarded); `apply_patch` / `clear_patches` / `list_patches` / `snapshot` / `evaluate_active_patches` / `has_active_patches` / `apply_catalog_patch`; bundled `CATALOG` keyed by patch name. Mirrors to `_research/diagnosed_fibers.py` via codegen so it ships in the wheel.
- **`bridge.apply_patch(name)`** loads a named CATALOG entry; **`bridge.apply_custom_patch(name=, kind=, body=..., amplitude_deg=..., period_days=..., ...)`** constructs a patch from JSON-friendly primitive args (Pyodide-safe); **`bridge.list_active_patches()`** / **`bridge.list_catalog_patches()`** / **`bridge.clear_patches()`** mirror the registry surface.
- **CLI** (`patches` subcommand group):
  - `ephemerides-spectral patches catalog` — list bundled patches with metadata
  - `ephemerides-spectral patches apply --name ...` — load a named patch
  - `ephemerides-spectral patches active` — list currently-active patches
  - `ephemerides-spectral patches clear` — wipe all patches
- **BIP encoder runtime-overlay integration** — `_encode_state_impl` queries `diagnosed_fibers.evaluate_active_patches(date_jd, body_to_idx)` after the base encode loop; per-body deltas are added to `curr_phases` BEFORE the final `& (MODULO - 1)` reduction. Wraparound is the cyclic-group reduction we want; correctness verified by `test_runtime_patches.py::test_clear_restores_byte_identical_baseline`.

### Added — patch CATALOG (v0.4.0 baseline, three patches)

Each entry was authored directly from a v0.3.1 FFT residual peak — see [`figures/de441_error_spectrum_analysis.md`](figures/de441_error_spectrum_analysis.md) for the source data and [`figures/runtime_kernel_patching.md`](figures/runtime_kernel_patching.md) for the per-patch contribution shape across a JD ladder.

- **`mars-7.96yr-diagonal`** — `SinusoidPatch(body="mars", amplitude_deg=3.45, period_days=2907.3)`. Targets Mars's rank-1 FFT peak (suspect: missing Mars-Saturn or Mars-Jupiter sub-resonance not in the v0.2.0 RESONANCES table).
- **`mercury-10.69yr-diagonal`** — `SinusoidPatch(body="mercury", amplitude_deg=9.19, period_days=3905.1)`. Targets Mercury's rank-1 peak (suspect: higher-order PN beat with Jupiter that the v0.1.0 43"/century PN entry doesn't capture).
- **`jupiter-saturn-9.56yr-coupled`** — `CoupledSinusoidPatch(body_a="jupiter", body_b="saturn", amplitude_deg=45.0, period_days=3490.9, correlation=-1)`. The smoking-gun missing-coupling signal: J and S show identical 9.56-yr peaks at ~45° amplitude. The v0.2.0 `α=0.1` modulation depth undershoots the actual J–S 5:2 libration by ~5×; the anti-correlated coupled patch shrinks both peaks simultaneously (libration is +Jupiter / −Saturn around the conjunction).

### Changed

- **C native backend (`backend="c"`) transparently falls back to `"bip"` when patches are active.** The C-side overlay isn't yet implemented — fallback guarantees correctness while the C ABI v2 surface is designed for v0.4.x phase F. Zero overhead when the registry is empty (`has_active_patches()` is a single-cycle empty-list check).
- **`bridge.get_system_state()`** returns `backend="bip"` (not `"c"`) when the C backend was requested but patches forced a fallback. The new `backend_requested` field always preserves the original ask.
- **Codegen ships 9 modules now** (was 8): added `_research/diagnosed_fibers.py`. The manifest's per-file SHA-256 sums update accordingly; `test_data_freshness.py` enforces the new module is present.

### Tests

- New `tests/test_runtime_patches.py` — 12 tests pinning every structural property of the overlay:
  1. `apply` + `clear` round-trip is byte-identical to baseline
  2. diagonal patch shifts only the targeted body
  3. composition of two disjoint-body patches is order-independent
  4. coupled J-S patch is anti-correlated to within cyclic-group ULP
  5. duplicate-name `apply_patch` is a hard error (no silent shadow)
  6. `backend="c"` falls back to `"bip"` when patches are active
  7. `apply_custom_patch` constructs sinusoid + coupled-sinusoid kinds
  8. unknown kinds + invalid `correlation` are surfaced as `{ok: False}`
  9. `list_catalog_patches` carries name / kind / amplitude / period / notes
  10. fresh process starts with `n_active=0`
- `test_immolation.py` — added `CATALOG_PATCHES` to the `_BRIDGE_CONSTANTS` set (it's a tuple, not a callable).

### Documentation

- **`figures/runtime_kernel_patching.md`** — overlay design rationale, ksplice/kpatch comparison, per-patch contribution tables, what-this-doesn't-claim section (patches are empirical Fourier corrections, not first-principles physics; v0.5.x's α derivation should ultimately replace them).
- **`figures/runtime_kernel_patching_demo.md`** — reproducible per-patch JD-ladder output from `python -m research.demo_runtime_patches`.
- **`research/demo_runtime_patches.py`** — small reproducible demonstration (D=4096 for speed); shows the patch contribution shape across `[-20, -5, 0, +5, +20]` yr from REFERENCE_JD.

### CI

- `pure-wheel-build` job promoted to always-on (added in the v0.3.1 hotfix). Mirrors the publish workflow's `build-pure-wheel` step exactly so any TOML-syntax / hatchling-config drift in `pyproject-pure.toml` fails on the PR, not at release time.

## [0.3.1] — 2026-05-04

C-in-wheel + spectral syzygy window search + DE441 error-spectrum FFT.

### Added — native C backend

- **scikit-build-core** build system replaces hatchling for the platform wheels. CMake compiles `c/src/{es_encode,es_bodies,es_laplacian,es_cosine_lut}.c` into `libephemerides_spectral.{so,dll,dylib}` and bundles the binary under `ephemerides_spectral/_native/` in the wheel.
- **`ephemerides_spectral._native_bip`** — `ctypes` shim that loads the bundled binary, verifies the ABI version (v1) at load time, and exposes `HAS_NATIVE`, `LIB_PATH`, `encode_state`, `encode_at_jd`, `native_version`. Caller-side guard discipline: check `HAS_NATIVE` before invoking; transparent fallback to pure-Python BIP if the binary isn't loadable (sdist installs without a C toolchain, Pyodide / WASM, the pure-Python fallback wheel).
- **`backend="c"`** dispatch in `default_encode()` and `bridge.get_system_state()`. Byte-for-byte identical phase residues to `backend="bip"` (verified by `tests/test_native_parity.py`'s 12-cell three-way parity test); **~1000× speedup** on the chunk loop (encode at +20 yr: 46.5 ms Python → 0.04 ms C). Falls back transparently to `"bip"` when the binary isn't present.
- **`pyproject-pure.toml`** for the Pyodide / WASM `py3-none-any` fallback wheel. Same package name + version as the platform wheel; sanity-checks ensure no `_native/` binaries leak in. Built by the publish workflow's `build-pure-wheel` job alongside the platform-specific `cibuildwheel` matrix.
- **C ABI accessors** in the header: `es_abi_version()`, `es_n_bodies()`. ABI bumps are wire-format breaks; the Python shim refuses to load mismatched binaries.
- **C banker's-rounding** (`es_banker_round`) added to `es_encode.c` to match numpy's `np.round` half-to-even semantics in the sub-day remainder step. Required for byte-exact parity with the Python BIP encoder when the multiplication produces an exact half-integer (verified at the +/-1 yr parity test cases).
- **`ephemerides-spectral-publish.yml`** rewritten to a `cibuildwheel`-style matrix: 3 OS × 5 Python = 15 platform-specific wheels + sdist + pure-Python wheel.
- **`.gitattributes`** unchanged from v0.3.0 (already in place); CMake-generated build artifacts excluded from sdist.

### Added — spectral syzygy window search

- **`research/syzygy_window.py`** — `find_syzygies(jd_lo, jd_hi, kind, threshold)`. Enumerates candidate syzygies in closed form by walking new-moon and full-moon multiples of the synodic month + confirming against the draconic-month phase. **HDC-native** pattern: cost goes from `O(window_days × encode)` to `O(n_syzygies × confirmation)` because syzygies are rare events on the calendar (~5/yr combined solar+lunar).
- **`bridge.find_syzygies(jd_lo, jd_hi, kind, threshold, max_candidates)`** wraps the research-side function with input validation + Pyodide-friendly JSON return shape.
- **CLI `find-syzygies --from-jd ... --to-jd ... [--kind] [--threshold]`**.
- The v0.3.0 point-evaluation `eclipse --jd` (`bridge.get_eclipse_probability(jd_tdb)`) is **kept for backward compatibility** but documented as the deprecated encode-then-check pattern. The bronze antikythera's Saros dial doesn't encode-and-check either — it turns gears whose ratios *are* the Saros cycle.

### Added — DE441 error-spectrum FFT

- **`research/de441_error_spectrum.py`** — uniform-spaced sweep + per-body FFT of the linear-detrended residual against DE441 truth. Native C path used when available (1024 samples × 6 ms = ~6 s total; otherwise 315 s on Python).
- **`figures/de441_error_spectrum_analysis.md`** — hand-curated interpretation of the peaks. Headline: **Jupiter–Saturn show identical 9.56-yr peaks at ±45° amplitude** — that's the smoking-gun missing-coupling signal, the empirical motivation for v0.4+'s first-principles α derivation. The current Phase-9 `α = 0.1` undershoots the actual J–S libration depth by ~5×.
- Outer planets (Uranus, Neptune, Pluto) peak at their own orbital periods — Q-format precision floor signals, not Phase-9 missing-coupling signals; addressed by `K_BITS > 32` future work.
- Mars at 7.96 yr / 3.45° suggests a missing Mars–Saturn coupling. Mercury at 10.69 yr / 9.19° suggests higher-order PN beat with Jupiter.

### Changed

- `SUPPORTED_BACKENDS` now includes `"c"`. Backwards compatible: `"bip"` and `"complex128"` still work unchanged.
- `bridge.get_system_state(backend="c", ...)` returns `backend="c"` on success or `backend="bip"` on transparent fallback (the new `backend_requested` field always preserves the original ask).

### Notes

- v0.3.1 is the first release with platform-specific wheels. Expect **15 wheels** on the PyPI release page (3 OS × 5 Python) plus 1 sdist plus 1 pure-Python wheel for Pyodide.
- Encode timings on the C path: 0.2 ms at J2000; 0.04 ms at +20 yr; ~6 ms at +1000 yr; ~6 ms at +14000 yr (chunk loop is so cheap the body iteration dominates). The DE441 sweep that took 6.4 s in Python at +14,000 yr lands well under 10 ms in C.
- The eclipse-prediction story now has two surfaces: the v0.3.0 point-evaluation `eclipse --jd` (kept; cheap; appropriate for "what's the alignment at this single JD") and the v0.3.1 `find-syzygies --from-jd … --to-jd …` (HDC-native window search; appropriate for everything else).

### CI shape (chess-spectral parity)

- Per-PR runs **4 always-on cells** (`build-and-test`: 3 OS × py3.12 + 1 min-Python cell on Linux), `codegen-determinism` (single Linux job), and `fallback-test` (pure-Python no-native path on Linux). Wall time on the green path is ~3 min per PR.
- The full **15-cell `verify-wheels`** matrix (3 OS × 5 Python via `cibuildwheel`) plus a Linux platform-wheel + sdist `verify-build-artefacts` job are **opt-in** at PR time via the `wheel-check` label or `workflow_dispatch`. Apply the label when touching package layout, `pyproject.toml`, scikit-build-core config, the C source tree, or any `vX.Y.Z`-ship release PR.
- The full matrix still runs unconditionally on tag push via `ephemerides-spectral-publish.yml` — the load-bearing release gate is unchanged.

### Known limitations

- **Sdist standalone build broken when no toolchain is present.** The published sdist contains the C source tree and `CMakeLists.txt` at the parent of the python/ project (mirrored via `[tool.scikit-build] sdist.include = ["../CMakeLists.txt", "../c/**", ...]`), but the parent-relative `cmake.source-dir = ".."` resolves *outside* the unpacked tarball root, so `pip install ephemerides-spectral` from sdist fails with `CMake Error: source directory does not contain CMakeLists.txt`. The 15 platform wheels cover essentially all consumers (3 OS × 5 Python, x86_64 + arm64); users on platforms without a wheel (Linux musllinux, exotic ARM) currently can't fall back to source build. Tracked as a v0.4 cleanup — likely co-locates the C tree under `python/` so `source-dir = "."`. CI's wheel-build path uses `python -m build --wheel` and `python -m build --sdist` as separate invocations to avoid the broken sdist-round-trip codepath.

## [0.3.0] — 2026-05-04

Time scales beyond Earth + DE441 full-epoch sweep + the natural-resonance gear group.

### Added

- **`research/time_scales.py`** — Mars Sol Date / Mars Coordinated Time per Allison & McEwen 2000 (`jd_to_msd` / `msd_to_jd` with documented leap-second handling); mean lunar synodic + sidereal age/phase primitives (`jd_to_lunar`, `MarsTime`, `LunarTime` dataclasses).
- **Bridge methods** (Pyodide-friendly JSON surface):
  - `bridge.jd_to_mars_time(jd_utc, leap_seconds=37)` → `{ok, jd_utc, msd, mtc_hours, mtc_seconds, sol_number, leap_seconds}`
  - `bridge.mars_time_to_jd(msd, leap_seconds=37)` → MSD → JD_UTC inverse
  - `bridge.get_lunar_phase(jd_tdb)` → synodic + sidereal age/phase
  - `bridge.list_lunar_kernels()` → LTE440 metadata + `ltc_status` flag
  - `bridge.get_natural_resonance_group()` → resonance-derived natural cyclic group (LCM, CRT prime factorisation)
- **`LUNAR_KERNELS = ("lte440",)`** — registers LTE440 (Lin et al. 2025, A&A 704 A76) as a known lunar-time ephemeris. Metadata only; no auto-download. The kernel is ~100 MB and must be staged separately from `github.com/xlucn/LTE440` releases when needed.
- **CLI subcommands**:
  - `time-mars --jd 2451545.0` (or `--msd 50000`) — Mars Sol Date / Mars Coordinated Time
  - `time-lunar --jd 2451545.0` — mean lunar synodic + sidereal phase
  - `lunar-kernels` — LTE440 metadata + LTC status
  - `natural-group` — resonance-derived natural cyclic group
- **`research/de441_sweep.py`** — runs the BIP encoder across J2000 ± 14,000 yr (15 sample points) against DE441 truth; writes `results/de441_sweep_summary.json` + `results/de441_sweep_table.md`.
- **[`figures/de441_full_sweep.md`](../figures/de441_full_sweep.md)** — honest interpretation of the sweep. Earth / Venus / Uranus stay <10° at multi-millennium horizons; Mars 14°; Mercury 84°; Jupiter / Saturn / Neptune / Pluto / Moon all hit >150° — the structural-limit signature of phenomenological `α = 0.1`. Documents the three follow-ups that would each visibly improve specific bodies (per-resonance derived α, higher-order PN for Mercury, more resonance entries).

### Notebook updates

- New §6: **Natural gear group, leaf structure, concert frequency** — distinguishes the encoder's architectural `Z_{2^32}` modulus from the resonance-derived natural cyclic group `Z_30 = Z_2 × Z_3 × Z_5`. Connects to chess-spectral §19's non-Markovian sheaf framing (let structure come from the data, don't impose it via the encoding).
- New §7: **Time scales** — JD vs MSD/MTC vs lunar primitives vs LTC roadmap.
- §4 Release History extended with the v0.3.0 entry.

### Roadmap

- **LTC (Lunar Coordinated Time)** deferred to v0.4+ — pending NASA + international agencies' formal definition (target ~2026–2028 per the April 2024 White House directive). LTE440 ships the underlying SPICE-format conversion ephemeris; the bridge will gain runtime LTC↔UTC↔JD_TDB conversions when the standard lands.
- **First-principles per-resonance α** — replaces the phenomenological `α = 0.1` with values from a Hamilton/Delaunay-variable Lagrangian. The DE441 sweep documents *why* this matters: bodies inside the resonance set (Jupiter, Saturn, Neptune, Pluto, Moon) phase-scramble at multi-millennium horizons because their `α` values are wrong-in-detail.
- **DE441 vs DE442 spectral error signature** *(experiment)*: build two BIP instruments calibrated separately from DE441 and DE442; encode the same JD on both; project per-body residue deltas onto the Laplacian eigenbasis. If the deltas have a coherent spectral signature, DE442's corrections to DE441 live in a specific eigenmode subspace — letting us *predict* where ephemeris error correction is structurally needed without needing the corrected kernel.
- **Spectral syzygy window search** — replaces v0.3.0's point-evaluation `eclipse --jd` (encode-then-check) with a window-search `find-syzygies` that uses the natural cyclic-group decomposition (Saros / Metonic / synodic month / lunar nodes) to enumerate candidate JDs in closed form, then confirms each by spectral projection. The HDC-native usage; the bronze antikythera's Saros dial works the same way (turn the gears, don't re-encode).

### C port

- Header version macro bumped to `0.3.0` (`include/ephemerides_spectral.h`).
- No C-side functional changes; the time-scale conversions and natural-group introspection are Python-side surface.

## [0.2.0] — 2026-05-04

Phase 9 coverage extension. The hardcoded Jupiter–Saturn 5:2 entry is promoted to a structured `RESONANCES` table; three new resonance pairs are wired alongside it. The encode path, the reference-instrument breathing Laplacian, and the C codegen all walk the same table — single source of truth in `research/laplacian.py`.

### Added

- **`research.laplacian.RESONANCES`** — frozen-dataclass list of `(body_a, body_b, n_a, m_b, label)` entries. v0.2.0 ships four:
  - **Jupiter–Saturn 5:2 (Great Conjunction)** — refactored from the v0.1.0 hardcoded path; phases unchanged when this is the only active entry.
  - **Neptune–Pluto 3:2** — Pluto's stable orbital resonance with Neptune. Smaller mass-product than J–S; coupling weight follows the `1e-5 · √(m_a·m_b)` scaling the J–S entry uses.
  - **Io–Europa 2:1 (Laplace pair 1)** — first leg of the Jovian Laplace resonance (Io–Europa–Ganymede share a 4:2:1 mean-motion lock).
  - **Europa–Ganymede 2:1 (Laplace pair 2)** — second leg of the same Laplace resonance.
- **Static-coupling weights** for the three new pairs are added to `_define_couplings`. The Phase 9 modulation scales an existing static weight; pairs without a non-zero weight would no-op silently, so the codegen + Python encoder both *guard* against zero-weight resonance entries (a hard error rather than a silent drift).
- **`SolarSystemLaplacian.get_dynamic_laplacian`** now walks the table instead of hardcoding J–S. The reference-instrument breathing path picks up all four resonances automatically.

### Changed

- **Encoded phase residues for Io / Europa / Ganymede / Neptune / Pluto** shift relative to v0.1.0 because their Phase 9 modulation is now active. Earth's phase residue is unchanged (no resonance touches Earth in v0.2.0). The 0.0002 rad Earth phase floor against DE421 at +20 yr is preserved.
- **Bridge `list_couplings()` and `breathing` CLI subcommand** continue to accept any body pair, but the wired-in resonances are now four entries — `bridge.get_breathing_modulation()` for any of the four returns a non-zero modulation factor by default.

### C port

- **`c/src/es_laplacian.c`** regenerated: `es_n_couplings = 4`. Each entry carries `(idx_a, idx_b, n_a, m_b, weight_rpd)` so the C inner loop is a flat iteration over the table — no per-resonance branching.
- **`c/test/test_parity_python.py`** still asserts byte-for-byte parity with the Python reference encoder. **All 26 bodies match exactly at +20 yr** even with the expanded breathing surface, confirming the encoder's floor-division semantics scale cleanly across multiple resonance entries.
- **Stack + `.rodata` footprint** unchanged at the per-body / per-LUT level. Coupling-table grew from 1 entry × 24 B = 24 B to 4 × 24 B = 96 B in `.rodata` — still negligible.

### Notes

- The modulation depth `α = 0.1` is global across all four resonances in v0.2.0; per-resonance depths derived from a Hamilton/Delaunay-variable Lagrangian are deferred to v0.3.x (see ROADMAP).
- The convention `cos(n_a · φ_a − m_b · φ_b)` matches the v0.1.0 J–S wiring (`n_a` is the multiplier on the *faster* body). The cosine is symmetric, so this is equivalent under the modulation envelope to the canonical "slow" resonance angle `m_b · φ_a − n_a · φ_b` — kept this way to preserve byte-exact parity with v0.1.0 for the J–S pair.

## [0.1.0] — 2026-05-04

First public release on PyPI.

### Added

- **Sol Star System Laplacian** (`research/laplacian.py`). 26 bodies — sun + 9 planets (incl. Pluto) + 12 major moons + 4 main-belt asteroids. The static Laplacian decomposes as `L_LTI = L_trunk + L_pn + L_static`: diagonal Newtonian mean motions (`2π / period_days`), Mercury's 43"/century post-Newtonian frequency shift on the diagonal, and a symmetric off-diagonal of gravitational fiber weights (planet–sun / moon–planet / Jupiter–Saturn 5:2 resonance / asteroid–Jupiter). The LTI snapshot remains accessible via the `L_lti` property as the Phase 8 regression baseline.
- **Phase 9 breathing couplings.** `SolarSystemLaplacian.get_dynamic_laplacian(current_phases)` returns the state-dependent matrix where each off-diagonal weight is multiplied by `1 + α cos(n_ij·φ_i − m_ij·φ_j)` for the resonance pair `(n_ij, m_ij)`. The Jupiter–Saturn 5:2 entry is wired with `α = 0.1`. Formally a state-dependent (non-autonomous) graph Laplacian / adaptive Kuramoto-family network with phase-difference-dependent (PDDP) coupling — see [research notebook §1.4](../ephemerides_spectral_research_notebook.md#14-mathematical-positioning-of-the-breathing-laplacian) for the full positioning across spectral-graph-theory / dynamical-systems / DNLS-on-a-graph vocabularies.
- **EphemerisHDCInstrument** (`research/ephemeris_reference_instrument.py`). FPU complex128 reference encoder with unit-norm complex Gaussian bases; supports the algebraic identities (Syzygy operator, observer binding via coprime cyclic rolls, Metonic / J–S resonance projection). Phase 9 evolution path runs `expm(-i·L_dyn(φ)·step)` chunk-wise in 30-day steps.
- **EphemerisBIPInstrument** (`research/bip_instrument.py`). ALU-native bit-serialised encoder over `Z_{2^32}` — phase composition is `(φ₁ + φ₂) mod 2³²`, which is implicit `uint32` overflow on hardware with no explicit modulo. 305× faster than the FPU reference at +20 yr; 256 KB state at D=65536; same 0.0002 rad Earth phase error vs DE421 truth.
- **Integer cosine LUT** for the breathing-coupling path. 1024 × `int32` (Q1.14 amplitude, 4 KB) keyed on the top 10 bits of the resonant-phase residue. Replaces `np.cos(...)` in the inner loop — pure integer table lookup at runtime; the LUT is computed once at import time.
- **Fixed-point Q-format frequency discipline.** All angular frequencies stored as signed `int64` in residues/day with `MODULO = 2³²` residues per revolution. Conversion: `omega_int = round(omega_rad_per_day / (2π) · MODULO)`. Q-format underflow guard at construction time emits a `RuntimeWarning` if any frequency rounds to zero residues/day (the floor is ~13 Gyr period — never trips for real bodies, but the guard exists so the assumption is checkable).
- **Pre-flight bounds check** on `encode_state`. Rejects `|delta_t_days| > 6.8e8` (≈ 1.86 Myr) before any math runs — keeps `omega · delta_t` inside the int64 envelope. The primary defense against silent saturation; the scoped `np.errstate(over='raise')` on the signed-int64 multiply is the secondary safety net.
- **Scoped overflow trap.** `np.errstate(over='raise')` around `omega * step_signed` (where saturation would corrupt); `np.errstate(over='ignore')` plus `warnings.filterwarnings('overflow encountered')` around the `uint64` accumulator (where wraparound IS the cyclic-group reduction we want). Means callers who promote `RuntimeWarning` to error don't see spurious noise from the modular arithmetic.
- **Bridge API** (`ephemerides_spectral.bridge`). 9 Pyodide-friendly methods, all returning `{ok: True, ...}` / `{ok: False, error: ...}`: `get_version()`, `list_bodies()`, `list_kernels()`, `list_couplings()`, `get_resolution()`, `get_system_state()`, `get_local_view()`, `get_eclipse_probability()`, `get_breathing_modulation()`. Validation helpers reject malformed `jd` (non-finite or out-of-envelope) / `body` (off the 26-body list) / `backend` (off `{bip, complex128}`) / `kernel` (off `{de421, de440, de441, de442}`) / `lat-lon` (out-of-range) inputs without ever raising.
- **Console script** (`ephemerides-spectral`). 9 subcommands: `version`, `bodies`, `kernel list`, `resolution`, `encode`, `local-view`, `eclipse`, `couplings`, `breathing`. Top-level `--version` and `--no-pretty` (compact JSON for piping into `jq`). Rich `--help` epilogs with concrete examples on every subcommand.
- **`default_encode(jd, backend="bip", kernel="de441", D=65536)`** top-level shorthand. `backend="bip"` returns the per-body `uint32[26]` phase residue array; `backend="complex128"` returns the FPU reference's `complex128[D]` unit-norm state.
- **Codegen** (`codegen/regenerate.py`, `codegen/emit_research_modules.py`). Mirrors `research/{__init__, ephemeris_reference_instrument, ephemeris_loader, bodies, laplacian, bip_instrument}.py` into `python/ephemerides_spectral/_research/`; reads version from `pyproject.toml` (single source of truth); stamps SHA-256 sums + sizes into `_data/manifest.json`.
- **`ephemerides-spectral-publish.yml`** GitHub Actions workflow. Pure-Python wheel + sdist build; OIDC trusted publishing; `workflow_dispatch` with `target ∈ {testpypi, pypi}` (default `testpypi`); tag-push on `ephemerides-spectral-v*` triggers PyPI publish; tag-version-vs-pyproject-version verification step.

### Documentation

- [`README.md`](README.md) — top-level orientation; subtree layout; how this relates to `../research/` and `../antikythera-spectral/`.
- [`ROADMAP.md`](ROADMAP.md) — released-versions table, next-planned versions, phase status, bridge↔CLI parity inspection.
- [`python/README.md`](python/README.md) — PyPI long description; CLI cheat-sheet; Python API surface.
- [`../ephemerides_spectral_research_notebook.md`](../ephemerides_spectral_research_notebook.md) — research notebook, §1.4 mathematical positioning of the breathing Laplacian.
- [`../research/resonant_bit_serialized_hdc_evaluation.md`](../research/resonant_bit_serialized_hdc_evaluation.md) — RBS-HDC evaluation; Phase 9 algebraic form; ALU-native LUT design; Q-format discipline; overflow trap rationale.

### Cross-pollination

The chess-spectral notebook §20.13–§20.20 explicitly aligns the chess `Z_{640}` phase-operator engine with this BIP design at the group-theoretic level. Both projects share the cyclic-group integer-ALU substrate, the Q-format scaling rules, and the cosine-LUT pattern. Chess pays an explicit `% 640` per op (non-power-of-2 modulus); ephemerides gets cyclic-group reduction free as `uint32` overflow (power-of-2 modulus). Antikythera-spectral is the bronze-mechanism sibling — different evidentiary object, same spectral / Laplacian-eigenbasis framing.
