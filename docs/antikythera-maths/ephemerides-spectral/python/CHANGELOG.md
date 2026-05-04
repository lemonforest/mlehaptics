# ephemerides-spectral CHANGELOG

Per-version change log for the `ephemerides-spectral` PyPI package.
The full project changelog (with pointers into the research notebook
and cross-pollination notes) lives at
[`../CHANGELOG.md`](../CHANGELOG.md).

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

(no entries yet — next entries land after v0.1.0)

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
