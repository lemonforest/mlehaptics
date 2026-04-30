# §11.6.16 operator workflow — the *why* of field-programmability

The architectural-mode hypotheses in the research notebook (§11.6.10–§11.6.15: crank-as-clutch, reverse-cranking, selective lock, carrier gears, setting-mode gears) all assume a Hellenistic operator periodically re-anchored the mechanism's planetary pointers against the sky. The §11.6.16 framing makes the *why* explicit: planets have visibility windows (heliacal rising → setting → invisibility around solar conjunction), and the mechanism is designed to be re-set when each planet emerges from solar glare.

`antikythera-spectral` v0.1.0 provides a **stateless API** that simulates this loop. The operator's "session" is a plain dict the caller round-trips through their own storage.

## Worked example (in Python, runs in Pyodide)

```python
from antikythera_spectral import bridge

# Day 0 — start a session at the mechanism's reference epoch.
out = bridge.start_operator_session(initial_jd=1684595.0, D=940)
state = out["state"]

# Day 30 — operator cranks forward by 30 days.
state = bridge.operator_advance(state, delta_days=30)["state"]

# Day 30 — operator looks up at Mars; it just emerged from solar glare
# (heliacal rising), and they read its position from the sky as residue 142
# on the Mars dial.
state = bridge.operator_observe(
    state, dial="Mars_synodic_period_relation", observed_residue=142,
)["state"]

# Day 90 — 60 days later, the operator wants to know how much Mars has
# drifted relative to the anchor.
state = bridge.operator_advance(state, delta_days=60)["state"]
diag = bridge.operator_diagnostics(state)
print(diag["per_dial"]["Mars_synodic_period_relation"]["angle_drift_deg"])
```

The output state is just JSON; serialise it to localStorage on the web side, read it back next session.

## Schema (OperatorState v1)

```json
{
  "schema_version": 1,
  "current_jd": float,
  "D": int,
  "dials_filter": "all",
  "anchors": {
    "<dial_name>": {"jd": float, "true_residue": int}
  },
  "history": [
    {"event": "start" | "advance" | "observe", ...}
  ]
}
```

Adding fields to v1 is forward-compatible (consumers ignore unknown keys). Removing or renaming fields is a major-version bump.

## How this connects to the H-battery

The operator workflow is **not** itself a hypothesis — it's a *user-flow* for the device. But it strengthens the interpretation of three existing rows:

- **E-H2** (uniform Mars encoder peak ≥ 150°): the failure mode is *expected and acceptable*, because the worst-error window coincides with invisibility. The operator never sees the bad readings.
- **E-H4** (Ptolemy equant peak in 30°–50° band): this is the design margin the operator absorbs by re-setting at the next heliacal rising — not a flaw to engineer around.
- **G-H8** (paired-chain enumeration PASS at 4/5 planets): the existence of low-bronze-cost alternative chains (Venus 5/8, Mercury 104/33, Mars 83/78) is what *enables* setting-mode wheels — the operator can set against any of several attested period relations.

## See also

- Research notebook §11.6.16 for the full rationale.
- ADR 0006 — *Stateless bridge — no server-side state.*
- `figures/seasonal_observability_priorart.md` — prior-art literature scan (the integrated framing is unpublished).
- `figures/seasonal_calibration_viability.md` — Hellenistic-tech viability assessment.
