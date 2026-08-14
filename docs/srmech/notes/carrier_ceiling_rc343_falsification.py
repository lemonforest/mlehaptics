"""rc343 (`#T972`) — the falsification harness for the rc339 ceiling defect.

WHY THIS FILE EXISTS
--------------------
rc343 adds a ratchet asserting that a capability ceiling which some carrier
BEATS must be scoped to the family it is a fact about. A ratchet that has not
been run against the defect it targets is not proven, and the rc343 test module
cannot itself be run against rc339 — it imports ``CEILING_MECHANISMS``, which
rc339 does not have, so it would ERROR on import rather than FAIL on the
contradiction. That distinction matters: an import error proves nothing about
whether the RULE detects the defect.

So the rule is factored out here, expressed against nothing but surfaces rc339
already publishes, and run against BOTH trees.

THE RULE
--------
For a capability with a published ``max_dim``:

  If any carrier whose row claims the capability in FULL can be MEASURED
  delivering it above ``max_dim``, then ``max_dim`` is not a universal ceiling.
  The payload must then carry ``family`` (what the number IS a fact about) and
  name the carrier in ``exceeded_by``.

  Independently: ``bounded_by`` must not restate the capability's own ``means``.

The trigger is a MEASUREMENT on the shipped carrier, so it needs no key rc339
lacks — which is exactly what lets it fire on the rc339 payload.

USAGE
-----
    cd docs/srmech/python && PYTHONPATH=$PWD python3 \\
        ../notes/carrier_ceiling_rc343_falsification.py

Exits 0 if the payload SATISFIES the rule, 1 if it violates it. Run against an
rc339/rc342 checkout it exits 1 (two violations); against rc343+, 0.
"""
from __future__ import annotations

import sys

from srmech.amsc.carrier_schema import _CAPABILITY
from srmech.amsc.cascade.cayley_dickson import CD_TURN_MAX_DIM
from srmech.amsc.mat import Mat
from srmech.introspect import describe

#: Which verdict means "this capability holds in FULL".
FULL_VERDICT = {"address": "exact", "compose": "full", "turn": "non_commuting"}

#: Reasons that merely restate what the capability already means.
DEFINITIONAL_NON_REASONS = {
    "turn": ("associativity", "associative", "non_associativity"),
    "compose": ("zero_divisors", "composition", "no_zero_divisors"),
    "address": ("addressing", "addressability", "exactness"),
}


def _mat_unit(n, r, c):
    rows = [[0] * n for _ in range(n)]
    rows[r][c] = 1
    return Mat.from_rows(rows)


def measure_mat_turn(n):
    """Exhaustive over the n**2 matrix units of M_n: (composing, of which
    non-commuting, total). The algebra dim is n**2, so n=3 -> dim 9."""
    units = [_mat_unit(n, r, c) for r in range(n) for c in range(n)]
    compose = non_commuting = 0
    for x in units:
        for y in units:
            xy = x @ y
            if all((x @ (y @ z)) == (xy @ z) for z in units):
                compose += 1
                if xy != (y @ x):
                    non_commuting += 1
    return compose, non_commuting, len(units) ** 2


def main() -> int:
    payload = describe()
    caps = payload["limits"]["capabilities"]
    violations = []

    print(f"srmech {payload['srmech_version']} — auditing "
          f"limits.capabilities against the rc343 scoping rule")
    print()

    # ---- the MEASUREMENT that triggers the rule -----------------------------
    n = 3
    compose, non_commuting, total = measure_mat_turn(n)
    mat_dim = n * n
    print(f"MEASURED  Mat / M_{n}(R), algebra dim {mat_dim}:")
    print(f"            turn-composing pairs      {compose}/{total}")
    print(f"            of those NON-COMMUTING    {non_commuting}/{total}")
    print(f"            Mat's declared turn row   "
          f"{_CAPABILITY['Mat']['turn']!r}")
    print(f"            published turn ceiling    {caps['turn']['max_dim']} "
          f"(CD_TURN_MAX_DIM = {CD_TURN_MAX_DIM})")
    mat_beats_turn = (non_commuting > 0
                      and mat_dim > caps["turn"]["max_dim"]
                      and _CAPABILITY["Mat"]["turn"] == FULL_VERDICT["turn"])
    print(f"            -> Mat BEATS the ceiling: {mat_beats_turn}")
    print()

    # ---- violation 1: an unscoped ceiling with a measured counterexample ----
    if mat_beats_turn:
        cap = caps["turn"]
        if not cap.get("family"):
            violations.append(
                "limits.capabilities['turn'].max_dim == "
                f"{cap['max_dim']} is beaten by a MEASURED carrier (Mat, "
                f"{non_commuting} non-commuting turn-composing pairs at algebra "
                f"dim {mat_dim}) but carries no `family` — it is published as a "
                "UNIVERSAL ceiling while being a Cayley-Dickson fact")
        if "Mat" not in (cap.get("exceeded_by") or []):
            violations.append(
                "limits.capabilities['turn'].exceeded_by does not name Mat, so "
                "the payload does not disclose its own counterexample "
                f"(exceeded_by = {cap.get('exceeded_by')!r})")

    # ---- violation 2: bounded_by restates the definition -------------------
    for name, banned in DEFINITIONAL_NON_REASONS.items():
        cap = caps.get(name) or {}
        reason = cap.get("bounded_by")
        if reason in banned:
            violations.append(
                f"limits.capabilities[{name!r}].bounded_by == {reason!r} "
                f"RESTATES `means` ({cap.get('means')!r}) — it cannot "
                "discriminate and cannot be falsified")

    # ---- report -------------------------------------------------------------
    for name in ("address", "compose", "turn"):
        cap = caps[name]
        print(f"  {name:8s} max_dim={str(cap.get('max_dim')):5s} "
              f"family={str(cap.get('family')):16s} "
              f"bounded_by={str(cap.get('bounded_by')):14s} "
              f"exceeded_by={cap.get('exceeded_by')!r}")
    print()

    if violations:
        print(f"VIOLATIONS: {len(violations)}")
        for i, v in enumerate(violations, 1):
            print(f"  {i}. {v}")
        print()
        print("VERDICT: the payload FAILS the rc343 scoping rule.")
        return 1
    print("VERDICT: the payload SATISFIES the rc343 scoping rule.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
