# ADR 0004: Frozen data as JSON / NPZ, not pickle

**Status:** Accepted (2026-04-29)

## Context

The codegen step emits SSOT data (cycles, gears, anchors, periods, fragments) for inclusion in the wheel. Three serialisation choices: JSON, NPZ, pickle.

## Decision

- **JSON** for everything text-shaped (cycles, gears, anchors, periods, fragments, manifest).
- **NPZ** for numerical arrays only (deterministic HDC channel basis vectors).
- **No pickle anywhere.**

## Consequences

- JSON is human-readable, language-agnostic, and CodeQL-clean.
- NPZ is the standard numpy serialisation for arrays; smaller than JSON for big numerical data.
- Pickle is forbidden — it executes arbitrary code on load (CWE-502); a malicious downstream consumer who tampered with `_data/` could execute code in the user's interpreter.
- Frozen-data drift caught by `test_data_freshness.py`'s manifest-SHA check.

## Alternatives considered

- **Pickle.** Rejected on security grounds.
- **Protobuf / msgpack.** Would add a runtime dependency for what's already a tiny corpus; not worth it.
- **CSV.** Considered for tabular data (gears) but JSON's nested structure is a better fit for `teeth: dict[reconstruction] -> int`.
