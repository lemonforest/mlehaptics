# ADR 0008: What-if mode bounded input

**Status:** Accepted (2026-04-29)

## Context

`encode_with_custom_train(jd, dial, p, q)` lets a user re-encode a dial with arbitrary `p / q` gear ratio (proxy for missing-gear search; supports the Venus 5/8 exploration etc.). Without bounds, a malicious or curious user could submit `p = 9999, q = 9997` and trigger pathological enumeration in `pareto_analysis.best_pq_constrained()` (used by other bridge methods downstream that share the gear-ratio code path).

## Decision

`encode_with_custom_train` validates inputs **before** calling into the gear-ratio machinery:

```python
if dial not in DIAL_SPECS:
    raise ValueError(f"unknown dial {dial!r}")
if not (1 <= p <= 500):
    raise ValueError(f"p must be in 1..500, got {p}")
if not (1 <= q <= 500):
    raise ValueError(f"q must be in 1..500, got {q}")
if math.gcd(p, q) != 1:
    raise ValueError(f"p/q must be reduced (gcd != 1)")
```

The 500 ceiling is the Greek bronze cuttability ceiling (A-H1 of the H-battery). Beyond it, no historical Greek workshop could have cut the gear; restricting the user to that range matches the device's empirical constraints AND prevents pathological enumeration.

## Consequences

- Worst-case enumeration is bounded: `O(500²) = 250 000` candidate pairs per call.
- The bridge layer catches `ValueError` and returns `{"ok": False, "error": ...}`.
- Future expansion (e.g. ultra-large primes if some hypothetical Greek-engineering paper finds them) requires a PR + ADR update to widen the bounds.

## Alternatives considered

- **Unbounded.** Rejected — pathological inputs could starve a Pyodide process for seconds.
- **Wider bounds (e.g. 1000).** No archaeological evidence for >500-tooth gears; sticking with the documented ceiling.
- **Server-side timeout.** Doesn't help in Pyodide (single-threaded, no preemption).
