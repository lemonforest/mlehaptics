# antikythera-spectral CHANGELOG

All notable changes to this package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

(no entries yet — added after v0.1.0)

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
