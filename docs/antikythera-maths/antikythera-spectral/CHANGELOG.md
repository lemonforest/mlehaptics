# antikythera-spectral CHANGELOG

All notable changes to this package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

(no entries yet — next entries land after v0.3.0)

## [0.3.0] — 2026-05-02

Two themes in v0.3.0, both incarnations of ADR 0012's "algebra/eigenbasis modelling, not CAD/fabrication" discipline:

1. **Mars planetary models — bronze projection + named param sets.** New `mars_models` facade exposes the four Mars longitude models (uniform, epicycle-only, equant, **bronze**) together with three reconstruction-source-specific parameter sets (`PTOLEMY_MARS_PARAMS`, `FREETH_2012_MARS_PARAMS`, `FREETH_2021_MARS_PARAMS`). The new `bronze` model is the algebra/eigenbasis projection of the gear-ratio cyclic-group representation back to the pointer's spatial longitude — same transform as `epicycle-only` but derived through the pin-and-slot phase-space map applied inline. Consistent with the research-scaffold's Mars 38° gap audit (PR #153 / 10-analysis decomposition); see [`docs/antikythera-maths/figures/mars_38deg_gap_findings.md`](../figures/mars_38deg_gap_findings.md).

2. **Bit-packed HDC ALU — first run.** New `bit_alu` facade exposes a binary-hypervector backend where every operation reduces to integer bit-ops (XOR, popcount, shift) on packed `uint64` words. Same algebraic structure as the `complex128` reference encoder; 125× smaller per hypervector (120 B vs 15 KB at D=940); 2-10× faster `bind` scaling with D. Permute and similarity have known optimisation paths deferred to v0.4.x. Includes a benchmark harness and the solar-vs-sidereal-day cycle-alignment investigation: `permute(v, 1, D)` ⇔ ONE Julian / mean-solar day = ONE turn of the Antikythera mechanism's hand-crank. See [`docs/antikythera-maths/figures/bit_alu_findings.md`](../figures/bit_alu_findings.md) for the full benchmark + findings.

### Added

- **`antikythera_spectral.mars_models` facade** — re-exports `mars_longitude_uniform`, `mars_longitude_epicycle_only`, `mars_longitude_equant`, `mars_longitude_bronze`, plus the three named param sets. ADR 0012 documents the algebra-first scope discipline. New module sits alongside the existing 16 facades; not exposed via top-level `antikythera_spectral.*` (matches established per-module facade pattern).
- **`mars_longitude_bronze`** — the cyclic-group / graph-Laplacian eigenbasis projection of the deferent gear ratios via the pin-and-slot phase-space transform `atan2(sin θ, cos θ + e/R)`. Constructed inline (not by importing `_research/pin_and_slot.py`, whose semantics are scoped to the D-H1 lunar mechanism). Numerically agrees with `mars_longitude_epicycle_only` to ~10⁻¹³ deg under all three named param sets — same transform, two derivation pathways. Pinned by `tests/test_mars_models.py::test_bronze_parity`.
- **`PTOLEMY_MARS_PARAMS`** — Almagest IX-X canonical: R=60, r=39.5, e=6, equant_offset=12, Almagest IX.6 mean motions.
- **`FREETH_2012_MARS_PARAMS`** — Freeth & Jones 2012 (ISAW Papers 4 §3.10 + Fig 39) pre-Hipparchian: bare deferent + epicycle, no eccentricity, no equant. The setup behind F&J's "nearly 38°" Mars peak error.
- **`FREETH_2021_MARS_PARAMS`** — Freeth 2021 (Sci. Rep. 11:5821) reconstruction. Same kinematic class as F&J 2012; gear-train-derived 133/125 synodic ratio. Bundled as a label-distinct param set.
- **`mars_models.fj_38deg_finding()`** — lazy, kernel-conditional reproduction of F&J 2012 Fig 39's "nearly 38°" Mars peak error from the bare deferent + epicycle on the middle 7 retrogrades vs JPL DE422. Returns the unfit RMS shape error (~38.85°, within 1° of F&J's 38°), the 7 opposition JDs, and the kernel used. Raises `RuntimeError` if no DE-series kernel is cached.
- **`antikythera_spectral.bit_alu` facade** — bit-packed binary HDC ALU. Pure-bitwise primitives (`bind` = XOR, `bundle_majority`, `permute` = cyclic bit-rotation, `hamming_distance`, `similarity` = `1 − 2H/D`) plus an encoder analogue (`encode_ant_bit`) and a per-dial decoder (`decode_dial_bit`). 125× smaller per hypervector, 2-10× faster `bind` than the `complex128` reference (scaling with D). Establishes the "ALU only" backend — every operation reduces to integer bit-ops on packed uint64s. Lives alongside the existing `encoder` facade; both implement the same algebraic substrate.
- **`research/bit_alu.py`** — bit-packed BSC (Binary Spatter Code) primitives bundled into the package via codegen.
- **`research/bit_alu_benchmark.py`** — microbenchmark harness comparing `bit_alu` vs the `complex128` reference for the four core HDC ops + full encoder round-trip. CLI: `python -m research.bit_alu_benchmark`.
- **`research/cycle_alignment_investigation.py`** — empirical solar-vs-sidereal-day analysis for `permute = sigma_day`. Confirms `permute(v, 1, D)` ⇔ one Julian / mean-solar day; sidereal framing would shift the Callippic residue by 1 over a full 940-tick rotation. CLI: `python -m research.cycle_alignment_investigation`.
- **`figures/bit_alu_findings.md`** — full benchmark table + cycle-alignment conclusion + "what an actual hardware ALU would look like" discussion.
- **ADR 0012** — algebra/eigenbasis modelling, not CAD/fabrication. Documents the scope discipline that runs through `mars_longitude_bronze`, the new param sets, the audit refactor below, AND the bit_alu backend (which is the cleanest possible incarnation of the algebra-first discipline — every op is bitwise).
- **Tests:** `tests/test_mars_models.py` — 9 tests covering facade smoke, param-set distinction, get_params resolver, bronze parity (parametrised over the three param sets), and kernel-conditional FJ-38° fact reproduction. `tests/test_bit_alu.py` — 10 tests covering facade smoke, n_words arithmetic, random_hv top-bit-zeroing, bind self-inverse, permute period = D, permute step composition, bundle of clones, similarity extremes, random-pair similarity ≈ 0, and encode/decode round-trip on the Callippic dial.

### Changed

- **`compare.compare_models_at_jd`** accepts `"bronze"` as a model name and a new optional `params: str = "ptolemy"` argument selecting among `{"ptolemy", "freeth_2012", "freeth_2021"}`. v0.2.x callers continue to work unchanged.
- **`bridge.compare_models`** mirrors the above change. New optional `params` keyword; `"bronze"` added to documented model whitelist.
- **Audit refactor: phase-math forms throughout the equant_encoder.** `mars_longitude_epicycle_only`, `mars_longitude_equant`, and `mars_longitude_bronze` now express their geocentric-distance / equation-of-center math via law-of-cosines / pure-trig forms (`R_eff = sqrt(e² + R² + 2eR cos M)`, `atan2(R' sin M, 2e + R' cos M)`) rather than via Cartesian `(px, py)` decomposition. Mathematically a no-op — the Almagest IX.5 cross-check (peak 11.3654° at M=90°), bronze parity (1.14e-13 deg), and F&J Fig 39 reproduction (95.56° / 99.30° / 102.60° peaks) all reproduce exactly. The change makes the algebra-first framing explicit at the implementation level (ADR 0012). Same change propagated to the bundled `_research/equant_encoder.py` via codegen.

### Notes

- **Mars 38° gap audit** (research scaffold, PR #153). v0.3.0's `mars_models` is the public surface for the package consumers; the full ten-analysis decomposition lives in [`figures/mars_38deg_gap_findings.md`](../figures/mars_38deg_gap_findings.md). Three coherent readings of F&J's "nearly 38°" emerge from the audit; the cleanest is **unfit RMS of bare deferent + epicycle on the retrograde subset vs DE422 = 38.85° within 0.85° of F&J's number** — directly accessible via `mars_models.fj_38deg_finding()`.

## [0.2.1] — 2026-04-30

### Added

- **PyPI project URL: `Demo`** — points to <https://lemonforest.github.io/antikythera-mechanism-the-movie/>, the project's GitHub Pages site. Showed up missing on PyPI's project page after the v0.2.0 release; this patch lands it for the kiosk audience that arrives via PyPI rather than the GitHub repo.

### Notes

Pure metadata change. No code, no API, no behaviour difference. Wheel content is byte-identical to 0.2.0 except for `METADATA`/`RECORD` (which contain the version string and the new project URL).

## [0.2.0] — 2026-04-30

**Self-contained mode** — all bridge methods except `compare_ephemerides` now work without `[ephemeris]` extras. Kiosks and Pyodide consumers can `pip install antikythera-spectral` and immediately call every method at Antikythera-grade precision (~±1 day on heliacal events, ~±5° on elongation queries). Skyfield becomes a strict opt-in for "research mode" sub-arcsec validation against modern ephemerides. ADR 0011 documents the discipline.

### Added

- `antikythera_spectral.visibility_algebraic` — closed-form synodic-cycle propagation for solar elongation, heliacal rising, visibility windows.
- `antikythera_spectral.eclipses_algebraic` — Saros-cycle propagation from frozen Hellenistic + modern anchors (the device's actual job).
- `_data/visibility_anchors.json` — per-planet anchor data (synodic period, one heliacal-rising anchor JD near J2000, threshold, max-elongation, inferior/superior bool, visibility-fraction-per-cycle).
- ADR 0011 (algebraic default, ephemeris opt-in).

### Changed

- `bridge.get_visibility_windows` — new `precise=False` keyword (default). Algebraic mode always succeeds; `precise=True` uses skyfield, returns `ok=False` if kernel missing.
- `bridge.get_next_heliacal_rising` — same `precise` switch.
- `bridge.get_solar_elongation` — same `precise` switch.
- `bridge.find_eclipses` — same `precise` switch (algebraic = Saros-cycle propagation; precise = sky-driven syzygy enumeration).
- Return shapes gain a `mode: "algebraic" | "ephemeris"` field on the four affected methods.
- CLI: `--precise` flag added to `visibility`, `heliacal`, `elongation`, `eclipses` subcommands.

### Unchanged

- `compare_ephemerides` is by definition a JPL-kernel diff tool — it stays ephemeris-only and requires `[ephemeris]` extras.
- All other 30+ bridge methods were already ephemeris-free in v0.1.0.

## [0.1.0] — 2026-04-30

First public release on PyPI: <https://pypi.org/project/antikythera-spectral/0.1.0/>.

Verified on TestPyPI as `0.1.0rc1` ([run 25176133737](https://github.com/lemonforest/mlehaptics/actions/runs/25176133737)) before the version-bump promotion. Same wheel content; only the version label differs.

### Added

- **Package skeleton** — pure-Python wheel via hatchling. `pyproject.toml`, `__init__.py`, `version.py`, `py.typed`. ADR 0001.
- **Codegen subtree** mirroring `chess-spectral/codegen/`:
  - `emit_cycles.py`, `emit_gears.py`, `emit_anchors.py`, `emit_periods.py`, `emit_fragment_inventory.py`, `emit_basis_vectors.py`, `emit_research_modules.py`, `regenerate.py`.
  - Outputs: `_data/{cycles,gears,anchors,periods,fragments}.json`, `_data/basis_vectors_d{940,13440}.npz`, `_data/manifest.json` with package version + `git rev-parse HEAD` + per-file SHA-256, `_research/*.py` (23 copied research modules).
  - ADR 0004 (JSON not pickle), ADR 0005 (codegen yes / C no in v0.1.0).
- **9 facade modules** re-exporting curated public APIs from `_research/*.py`: encoder, decoder, dials, render, hypotheses, ephemeris, eclipses, periods, gears.
- **36-method Pyodide Bridge API** in `bridge.py`:
  - §5.1 state ← date (5): `get_dial_state`, `get_dial_angle`, `get_pointer_xy`, `get_all_dial_metadata`, `get_version`.
  - §5.2 date ← state (2): `decode_dial`, `decode_to_jd`.
  - §5.3 calendar (5): `jd_to_gregorian`, `gregorian_to_jd`, `jd_to_julian_calendar`, `jd_to_athenian`, `jd_to_olympiad`. ADR 0007.
  - §5.4 astronomy (6): `get_visibility_windows`, `get_next_heliacal_rising`, `get_solar_elongation`, `get_eclipse_anchors`, `get_period_relations`, `find_eclipses`.
  - §5.5 operator workflow (6): `start_operator_session`, `operator_advance`, `operator_observe`, `operator_diagnostics`, `set_anchor`, `apply_anchor`. ADR 0006.
  - §5.6 cross-comparators (3): `compare_ephemerides`, `compare_models`, `compare_reconstructions`.
  - §5.7 what-if + archaeology (3): `encode_with_custom_train`, `compare_to_ground_truth`, `get_fragment_inventory`. ADR 0008.
  - §5.8 Babylonian Goal-Year (2): `goalyear_predict`, `goalyear_compare`.
  - §5.9 animation (2): `encode_range`, `export_animation`.
  - §5.10 H-battery (2): `run_hypothesis_battery`, `get_hypothesis`.
  - All methods return Pyodide-JSON-serializable `{"ok": True, ...}` / `{"ok": False, "error": "..."}` dicts. Complex states serialise as real+imag-interleaved Float32 of length `2*D`. ADR 0002.
- **`antikythera-spectral` CLI** — subcommand-driven console script with rich `--help`. Each subcommand maps to one bridge method and prints JSON to stdout (or CSV for `hypotheses`).
- **Frozen `_data/` shipped in the wheel** — 8 files (5 JSON + 2 NPZ + manifest.json), 2.8 MB total.
- **PyPI publish + autotag workflows** — `antikythera-spectral-publish.yml` (TestPyPI / PyPI dual-target via `workflow_dispatch` input), `antikythera-spectral-autotag.yml` (strict-semver only; pre-release versions skipped). ADR 0009 / 0010.
- **CI workflow** — test matrix on `[ubuntu-latest, macos-14, windows-latest] × [3.10, 3.11, 3.12, 3.13, 3.14]`; wheel + sdist build verification; codegen reproducibility check.
- **CodeQL paths** updated in `.github/codeql/codeql-config.yml` and `.github/workflows/codeql.yml` to scan the new subtree.
- **Documentation** — bridge_api.md, DELTA_T_MODEL.md, EPHEMERIS_KERNELS.md, CALENDAR_SYSTEMS.md, OPERATOR_WORKFLOW.md, 10 ADRs, ROADMAP.md, repo-root + `python/` READMEs.

### Tests

- 64 passing tests / 1 skipped (skyfield-kernel-gated):
  - `test_data_freshness.py` (3) — manifest completeness, SHA matching, codegen determinism.
  - `test_facades.py` (9) — every facade imports cleanly + `__all__` resolves + one round-trip-style call.
  - `test_bridge_state_date.py` (29) — happy-path + input-validation negatives for §5.1 + §5.2.
  - `test_bridge_calendar.py` (12) — round-trip through J2000, 200 BCE, Olympiad anchor.
  - `test_bridge_astronomy.py` (11) — frozen-data methods + skyfield-graceful-degradation.

### CodeQL discipline (per ADR 0003)

- `bridge/ephemeris_bridge.py` is the only URL builder; `ALLOWED_KERNELS` allowlist gates inputs before any URL/path construction.
- Logging redacts paths; `test_codeql_allowlist.py` will grep the source for violations (test scaffolded; greps active in phase 16).
- What-if input gates `p, q ∈ [1, 500]` and `gcd(p, q) == 1` before enumeration.

### Release pipeline (all phases ✅)

- Phase 17 ✅ TestPyPI dry-run — published `0.1.0rc1` to test.pypi.org via [run 25176133737](https://github.com/lemonforest/mlehaptics/actions/runs/25176133737); verified install + import + CLI smoke from a clean Python 3.13 venv.
- Phase 18 ✅ §15.1 acceptance gate — all 8 verifiable boxes ticked on PR #111.
- Phase 19 ✅ Version bump `0.1.0rc1` → `0.1.0` (this commit).
- Phase 20 → main → autotag fires → production PyPI release.
