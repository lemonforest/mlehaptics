# ADR 0001: Pure-Python only in v0.1.0

**Status:** Accepted (2026-04-29)

## Context

Chess-spectral ships hand-written C alongside its Python — encoding a 100-game PGN runs 30–60× faster in C than pure Python. Antikythera state vectors are tiny (940–13 440 dim); a typical query is one date → one state. Even bulk operations (visibility windows, animation export) fit in pure Python at well under user-noticeable latency.

## Decision

`antikythera-spectral` v0.1.0 ships only Python. Single hatchling wheel, `py3-none-any`. No native binaries. No `pyproject-pure.toml` dual-wheel pattern (chess-spectral has one because the C version's the fast path; we'd be carrying the dual-wheel infrastructure with no benefit).

## Consequences

- Wheel is 2.8 MB (frozen `_data/` dominates), installable in seconds.
- No cibuildwheel matrix in CI — single Linux job builds once.
- Pyodide compatibility is automatic.
- If a future profiling case lands or a non-Python consumer (firmware, pure-WASM, Rust) shows up, we can add C in v0.3+. Plan §11.

## Alternatives considered

- **Match chess-spectral's full C tree.** Rejected: the perf case doesn't apply to Antikythera-scale data, and the non-perf reasons (project uniformity, "feels more substantial") are cosmetic.
- **Codegen-emitted C only (no hand-written C).** Considered for the `_research/` bake step. Rejected: pure-Python `_research/*.py` works just as well and is easier to debug.
