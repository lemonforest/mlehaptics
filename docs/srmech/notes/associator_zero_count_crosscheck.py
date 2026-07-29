#!/usr/bin/env python3
"""LANE 1 cross-check — reconcile with the SHIPPED sign-cocycle table.

``cayley_dickson.py`` (the ``CD_TURN_MAX_DIM`` block, ~line 176) publishes a
"SIGN COCYCLE assoc" column: the count of ordered BASIS triples whose
associator VANISHES —  8/8 at dim 2, 64/64 at 4, **344/512** at 8,
**2248/4096** at 16, and "(cost-skipped)" at 32.

This probe recomputes that column from the symmetry-type sweep's own machinery
(a THIRD, independent route: ``algebra_table`` → monomial map → associator),
which is what makes agreement a differential rather than a tautology — and it
fills the cost-skipped dim-32 cell.

Exact integers; no float, no ``abs()``, no numpy, no stdlib ``fractions``.
"""
from __future__ import annotations

import itertools
import json
import sys

from srmech.amsc.cascade.cayley_dickson import algebra_table

sys.path.insert(0, __file__.rsplit("/", 1)[0] if "/" in __file__ else ".")
from associator_symmetry_type_rung_by_rung import (   # noqa: E402
    assoc_fast, monomial_map,
)

SHIPPED = {2: (8, 8), 4: (64, 64), 8: (344, 512), 16: (2248, 4096),
           32: None}          # None == "(cost-skipped)" in the shipped table


def main() -> int:
    for dim in (2, 4, 8, 16, 32):
        mono = monomial_map(algebra_table(dim))
        zero = 0
        for i, j, k in itertools.product(range(dim), repeat=3):
            if assoc_fast(mono, i, j, k) == ():
                zero += 1
        rec = {
            "record": "sign_cocycle_assoc_crosscheck",
            "dim": dim,
            "zero_associator_ordered_triples": zero,
            "ordered_triples": dim ** 3,
            "shipped_claim": (list(SHIPPED[dim]) if SHIPPED.get(dim) else None),
            "agrees_with_shipped": (
                None if SHIPPED.get(dim) is None
                else [zero, dim ** 3] == list(SHIPPED[dim])),
        }
        print(json.dumps(rec, separators=(",", ":"), sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
