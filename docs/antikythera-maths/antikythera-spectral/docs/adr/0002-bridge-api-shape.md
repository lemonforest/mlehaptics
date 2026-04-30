# ADR 0002: Bridge API shape

**Status:** Accepted (2026-04-29)

## Context

Pyodide / web consumers need a stable contract. The chess-spectral `qm_4d_bridge.py` pattern is the proven model; we mirror it.

## Decision

Every bridge method returns a Pyodide-JSON-serializable dict carrying `'ok'`:

```python
# Success
{"ok": True, ...}

# Caller-side input error
{"ok": False, "error": "..."}

# Internal failure: raise (caught at JS/Pyodide boundary)
```

Complex state vectors serialise as **real+imag interleaved Float32** of length `2*D` so JS uses `new Float32Array(...)` directly. Numpy arrays elsewhere are real-valued.

Validations run **before** any expensive computation. Names like `dial`, `kernel`, `planet`, `era`, `source`, `layout`, `format` validate against frozen tuples (see ADR 0003 for the security implication).

## Consequences

- 36 methods all share one error model, easy to wrap in JS.
- Frozen at v0.1.0; additions are minor-version bumps, breaking changes are major.
- ADR 0006 extends this with the stateless-bridge rule for the operator workflow.

## Alternatives considered

- **Throw on caller-side errors instead of returning `ok=False`.** Rejected: Pyodide → JS exception translation is awkward; explicit dict is cleaner across the WASM boundary.
- **Async methods.** Not needed in v0.1.0; everything is synchronous. May revisit if streaming animation export is added in v0.2.
