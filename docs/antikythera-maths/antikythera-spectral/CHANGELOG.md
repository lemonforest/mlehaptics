# antikythera-spectral CHANGELOG

All notable changes to this package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Phase 1: package skeleton (`pyproject.toml` v0.1.0rc1, `__init__.py`,
  `version.py`, `py.typed`).
- Codegen subtree (`codegen/emit_*.py` + `regenerate.py`) emitting frozen
  JSON / NPZ exports of the research scaffold's SSOT data.
- Initial `_data/`: `cycles.json`, `gears.json`, `anchors.json`,
  `periods.json`, `fragments.json`, `basis_vectors_d{940,13440}.npz`,
  `manifest.json` (with package version, source-commit hash, per-file
  SHA-256s).
- `test_data_freshness.py` — fails the build if committed `_data/`
  drifts from `research/*.py` source.

(All entries above are part of the in-flight v0.1.0 release on the
`antikythera-spectral-pypi-plan` branch. They're not yet shipped to
PyPI.)
