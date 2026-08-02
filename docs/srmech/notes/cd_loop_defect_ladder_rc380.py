#!/usr/bin/env python3
"""rc380 (`#T1055`) — computational provenance for the Cayley–Dickson
LOOP-DEFECT LADDER, reproduced THROUGH the two ops the k=3 triangle-holonomy
research added.

The srmech notebook §3.29.3 records the ladder as load-bearing prose:

* the COMMUTATOR ``[x,y] = x·y − y·x`` (k=2, the square loop) turns on at ℍ —
  ``6`` noncommuting ordered basis pairs at dim 4 — while the associator is
  still 0 there;
* the 3-CYCLE HOLONOMY / ASSOCIATOR (k=3, the triangle loop) turns on only at
  𝕆 — ``168`` non-closing ordered basis triangles at dim 8, ``1848`` at 𝕊
  (dim 16) — and is identically closed on every associative rung.

Those numbers are the instruments the notebook describes, so this script
computes them WITH the instruments (``cd_commutator`` / ``cd_cycle_holonomy``),
not beside them. Each is also checked against an INDEPENDENT route so agreement
is a differential, not a tautology:

* commutator count vs the closed form ``(dim−1)(dim−2)`` (derived from the
  anticommutation structure, not the op);
* holonomy non-closing count vs the ``associator`` op's own vanishing census
  (a different surface — the bare trilinear tuple — over the same triples).

Exact integers end to end: no float, no epsilon, no ``abs()``, no numpy, no
stdlib ``fractions``. NDJSON to stdout, one record per rung per op.

    python3 notes/cd_loop_defect_ladder_rc380.py > notes/cd_loop_defect_ladder_rc380.ndjson
"""
from __future__ import annotations

import itertools
import json

from srmech.cascade import (associator, cd_basis, cd_commutator,
                                 cd_cycle_holonomy)

#: The load-bearing counts the notebook §3.29.3 pins, per rung.
#: commutator noncommuting ordered pairs;  holonomy non-closing ordered triples.
COMMUTATOR_PINNED = {1: 0, 2: 0, 4: 6, 8: 42, 16: 210}
HOLONOMY_PINNED = {1: 0, 2: 0, 4: 0, 8: 168, 16: 1848}


def commutator_noncommuting(dim: int) -> int:
    """Ordered basis pairs (eᵢ, eⱼ) with a NONZERO commutator — through the op."""
    b = [cd_basis(dim, i) for i in range(dim)]
    return sum(1 for i in range(dim) for j in range(dim)
               if any(v != 0 for v in cd_commutator(b[i], b[j])))


def holonomy_open(dim: int) -> int:
    """Ordered basis triangles that do NOT close — through the holonomy op."""
    b = [cd_basis(dim, i) for i in range(dim)]
    return sum(1 for i, j, k in itertools.product(range(dim), repeat=3)
               if not cd_cycle_holonomy(b[i], b[j], b[k])["closed"])


def associator_nonassociating(dim: int) -> int:
    """Ordered basis triples with a NONZERO associator — the independent route
    (the bare trilinear tuple, not the loop dict)."""
    b = [cd_basis(dim, i) for i in range(dim)]
    return sum(1 for i, j, k in itertools.product(range(dim), repeat=3)
               if any(v != 0 for v in associator(b[i], b[j], b[k])))


def emit(rec: dict) -> None:
    print(json.dumps(rec, separators=(",", ":"), sort_keys=True), flush=True)


def main() -> int:
    dims = (1, 2, 4, 8, 16)

    # Rung 0 turn-on: the COMMUTATOR (k=2 square loop).
    prev_zero = True
    for dim in dims:
        n = commutator_noncommuting(dim)
        closed_form = (dim - 1) * (dim - 2)
        turn_on = (n != 0) and prev_zero
        prev_zero = prev_zero and (n == 0)
        emit({
            "record": "commutator_noncommuting_census",
            "op": "cd_commutator",
            "arity": 2,
            "loop": "square",
            "dim": dim,
            "noncommuting_ordered_pairs": n,
            "ordered_pairs": dim * dim,
            "closed_form_(dim-1)(dim-2)": closed_form,
            "agrees_with_closed_form": n == closed_form,
            "pinned": COMMUTATOR_PINNED[dim],
            "agrees_with_notebook": n == COMMUTATOR_PINNED[dim],
            "is_turn_on_rung": turn_on,
        })

    # Rung 1 turn-on: the 3-CYCLE HOLONOMY / ASSOCIATOR (k=3 triangle loop).
    prev_zero = True
    for dim in dims:
        opn = holonomy_open(dim)
        na = associator_nonassociating(dim)
        turn_on = (opn != 0) and prev_zero
        prev_zero = prev_zero and (opn == 0)
        emit({
            "record": "cycle_holonomy_open_census",
            "op": "cd_cycle_holonomy",
            "arity": 3,
            "loop": "triangle",
            "dim": dim,
            "open_ordered_triangles": opn,
            "ordered_triples": dim ** 3,
            "associator_nonassociating": na,
            "holonomy_defect_is_associator": opn == na,
            "pinned": HOLONOMY_PINNED[dim],
            "agrees_with_notebook": opn == HOLONOMY_PINNED[dim],
            "is_turn_on_rung": turn_on,
        })

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
