# ephemerides-spectral CHANGELOG

All notable changes to this package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

(no entries yet — next entries land after v0.1.0)

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
