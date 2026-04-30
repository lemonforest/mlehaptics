# ADR 0006: Stateless bridge — no server-side state

**Status:** Accepted (2026-04-29)

## Context

The §11.6.16 operator workflow simulation is a multi-step interaction (start → advance → observe → diagnostics → repeat). The naive design uses a session ID + server-side state map: `session_id → OperatorState`. The Pyodide-friendly design is stateless: every method takes the prior state in, returns a new state out.

## Decision

The operator-workflow methods (`start_operator_session`, `operator_advance`, `operator_observe`, `operator_diagnostics`, `set_anchor`, `apply_anchor`) are **stateless**. Each accepts an `OperatorState` dict, returns a new `OperatorState` dict. The package does not retain any session storage; the caller is responsible for persisting the state between calls.

```python
out = bridge.start_operator_session(initial_jd=1684595.0)
state = out["state"]
state = bridge.operator_advance(state, 30)["state"]
state = bridge.operator_observe(state, "Mars_synodic_period_relation", 142)["state"]
# ... save state to localStorage / wherever
```

## Consequences

- Pyodide consumers serialise the state to JSON between page loads with no special infrastructure.
- The package has no "session map" / "GC stale sessions" complexity.
- Multiple concurrent sessions trivially work — they're just independent state dicts.
- Schema (`OperatorState` v1) is part of the v0.1.0 freeze; field additions are forward-compatible, removals are major-version bumps.

## Alternatives considered

- **Server-side session state with explicit teardown.** Doesn't fit Pyodide (single-process, no fork/exec, no persistence story).
- **Implicit state in module globals.** Even worse — concurrent users in the same Pyodide instance would clobber each other.
