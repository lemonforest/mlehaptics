# ephemerides-spectral CHANGELOG

Per-version change log for the `ephemerides-spectral` PyPI package.
The full project changelog (with pointers into the research notebook
and cross-pollination notes) lives at
[`../CHANGELOG.md`](../CHANGELOG.md).

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

(no entries yet — next entries land after v0.3.1)

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
