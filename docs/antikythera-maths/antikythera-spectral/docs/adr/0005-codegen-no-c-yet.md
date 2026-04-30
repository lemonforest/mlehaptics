# ADR 0005: Codegen yes, C binaries no (in v0.1.0)

**Status:** Accepted (2026-04-29)

## Context

Chess-spectral has both a `codegen/` directory (emits Python lookup tables) and a C source tree (handwritten encoder). For antikythera-spectral we considered: do we mirror both, or just one?

## Decision

- **Codegen yes**, mirroring chess-spectral's pattern. `codegen/emit_*.py` scripts read from `research/*.py` (SSOT) and emit `_data/*.json` + `_research/*.py` copies into the wheel. `regenerate.py` orchestrates and stamps a `manifest.json` with source-commit + per-file SHAs.
- **C binaries no** in v0.1.0. ADR 0001 documents the rationale: Antikythera-scale state vectors are tiny; pure Python is fast enough; we get C inside `jplephem` (skyfield's extension) transparently.

## Consequences

- Wheel is small (2.8 MB) and Pyodide-compatible without effort.
- Codegen pattern is ready if we ever add a C accelerator — the data-table emission would extend to also emit `cs_tables_data.c`-style files.
- `test_data_freshness.py` enforces that `research/*.py` and the codegen output stay in sync.

## Alternatives considered

- **No codegen, just check in JSON by hand.** Rejected: drift between `research/*.py` (where users edit) and `_data/*.json` (what ships) would be hard to catch.
- **Match chess-spectral's full C tree for parity.** Rejected per ADR 0001.
