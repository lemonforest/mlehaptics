#!/usr/bin/env python3
"""rc354 (F1336) — the UNIT-LABEL cube: generating code for the fourth sense of
"the cube", and for every number the ``describe()`` collision note publishes.

Run from ``docs/srmech/python``::

    python3 ../notes/unit_label_cube_rc354.py            # human table
    python3 ../notes/unit_label_cube_rc354.py --ndjson   # the committed record

WHAT THIS ADDS TO rc353
=======================
rc353's collision note is TRUE and INCOMPLETE, and an incomplete note is as
dangerous as a false one the moment a planner acts on the gap. It separated
three senses of a small power of two:

  1. ``slots`` (8, 4, 2)      — ONE algebra (O) re-addressed at three widths;
  2. ``BLOCK_DIMS`` (2, 4, 8) — the real dims of THREE algebras (C, H, O);
  3. the (Z/2)^d GRADING cube — a dim-2^d algebra has 2^d basis DIRECTIONS, so
     the 4-cube (tesseract) grades the SEDENIONS at dim 16, and H's grading
     cube is the SQUARE (Z/2)^2;
  (+ the 16 half-integer Hurwitz unit POINTS of R^4, which are not a grading.)

THE MISSING FOURTH SENSE — the SIGNED UNIT LABEL
================================================
An algebra of real dim n does not have n units. It has **2n signed units**
(±e_0 … ±e_{n-1}), and labelling those needs **log2(n) + 1** bits: log2(n) for
the basis index and ONE MORE for the sign. So

    H (dim 4) -> 8 signed units  -> 3 bits -> a 3-CUBE
    O (dim 8) -> 16 signed units -> 4 bits -> a 4-CUBE (a TESSERACT)

The 16-vertex tesseract is therefore ALSO **O's unit-label cube**, not only S's
grading cube. Two different 16s: S has 16 basis DIRECTIONS, O has 16 signed
UNITS. That is a fourth collision on the same number, and it is the one that
explains why 8 is the middle ground — O has 16 units addressable in 4 bits AND
contains H seven times over (the seven Fano lines, verified below).

THE SHADOW RESULT — where the flat hypercube is WRONG
====================================================
Treat a signed unit as a (d+1)-bit label and ask whether the product is the XOR
of the labels. DERIVED, then MEASURED on ``cascade.cd_basis_product``:

  * the low ``d = log2(n)`` bits XOR **exactly** — e_i · e_j is always ±e_(i^j),
    at every rung, with zero violations;
  * the TOP (sign) bit does **NOT**. The violating ordered pairs of signed units
    number exactly ``2 * dim * (dim - 1)``.

The derivation is three lines. e_0 = 1 is a two-sided identity, so no pair
involving it violates. e_a² = -1 for a != 0 gives ``dim - 1`` violating index
pairs. For a != b both nonzero the basis elements ANTICOMMUTE, so of the ordered
pair (a,b) / (b,a) exactly one carries the minus sign — another
``(dim-1)(dim-2)/2``. The cocycle sign does not depend on the input signs, so
each violating index pair lifts to 4 signed pairs:

    4 * [ (dim-1) + (dim-1)(dim-2)/2 ] = 2 * dim * (dim - 1)

and the fraction of all ``(2*dim)^2`` ordered signed pairs that the flat cube
gets wrong is ``(dim-1) / (2*dim)`` -> 1/4, 3/8, 7/16, 15/32, ... -> **1/2**.

**THE FLAT HYPERCUBE IS WRONG EXACTLY WHERE THE ALGEBRA ANTICOMMUTES**, and it
gets worse up the ladder, approaching a coin flip.

HONEST BOUNDS — read these before quoting any number above
==========================================================
* The closed form is DERIVED and then CHECKED at six rungs (dim 2, 4, 8, 16, 32,
  64). It is **not proved for all n**; nothing here is a theorem about the whole
  tower.
* "O is THE right carrier" is a **DESIGN argument** — 16 units in 4 bits, and H
  seven times inside it — **not a measurement**. Nothing measured here selects a
  carrier.
* ``(dim-1)/(2*dim)`` is a statement about **BASIS-PAIR PRODUCTS** under a flat
  XOR label. It is **not** a strand-misread rate, an error rate of any encoder,
  or a probability of anything in a running cascade. Do not carry it into an
  error budget.

Everything below is MEASURED on the shipped surface. No numpy, no float, and no
``abs()`` — a sign is a Class-K pin-slot read.
"""

from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path

# SCRIPT-MODE path bootstrap: run from anywhere, resolve srmech from the tree.
_HERE = Path(__file__).resolve().parent
_PY = _HERE.parent / "python"
if str(_PY) not in sys.path:
    sys.path.insert(0, str(_PY))

from srmech.amsc.cascade.cayley_dickson import cd_basis_product  # noqa: E402

#: the rungs checked. NOT "all n" — see HONEST BOUNDS above.
RUNGS = (2, 4, 8, 16, 32, 64)


def label_bits(dim: int) -> int:
    """``log2(dim) + 1`` — the bits a SIGNED unit label needs.

    ``dim.bit_length() - 1`` is ``log2(dim)`` for a power of two (Class-I
    exponent read, no libm), and the ``+ 1`` is the sign bit that the grading
    cube does not carry.
    """
    return (dim.bit_length() - 1) + 1


def measure_rung(dim: int) -> dict:
    """One rung: index-lane exactness + the sign-lane violation count."""
    index_violations = 0
    minus_index_pairs = 0
    for i in range(dim):
        for j in range(dim):
            index, sign = cd_basis_product(dim, i, j)
            if index != (i ^ j):
                index_violations += 1
            # Class-K pin-slot read of the sign, never abs().
            if sign < 0:
                minus_index_pairs += 1
    # each violating INDEX pair lifts to 4 SIGNED pairs (the cocycle sign does
    # not depend on the input signs).
    signed_violations = 4 * minus_index_pairs
    total_signed_pairs = (2 * dim) ** 2
    return {
        "dim": dim,
        "signed_units": 2 * dim,
        "label_bits": label_bits(dim),
        "grading_cube_vertices": dim,          # basis DIRECTIONS
        "unit_label_cube_vertices": 2 * dim,   # signed UNITS
        "index_lane_violations": index_violations,
        "sign_lane_violations": signed_violations,
        "sign_lane_violations_closed_form": 2 * dim * (dim - 1),
        "total_ordered_signed_pairs": total_signed_pairs,
        "fraction_wrong": [dim - 1, 2 * dim],  # exact (num, den), never a float
    }


def fano_lines() -> list:
    """The seven XOR-closed nonzero triples of O, each spanning a copy of H.

    ``{0, a, b, c}`` closed under ``cd_basis_product`` IS a 4-dim subalgebra;
    verified rather than asserted, because "O contains H seven times" is half
    the middle-ground argument.
    """
    out = []
    for a, b, c in combinations(range(1, 8), 3):
        if a ^ b != c:
            continue
        sub = {0, a, b, c}
        closed = all(cd_basis_product(8, i, j)[0] in sub for i in sub for j in sub)
        out.append({"line": [a, b, c], "spans_quaternion_subalgebra": closed})
    return out


def main() -> int:
    rungs = [measure_rung(d) for d in RUNGS]
    lines = fano_lines()

    for r in rungs:
        assert r["index_lane_violations"] == 0, r
        assert r["sign_lane_violations"] == r["sign_lane_violations_closed_form"], r
    assert len(lines) == 7 and all(l["spans_quaternion_subalgebra"] for l in lines)

    if "--ndjson" in sys.argv:
        for r in rungs:
            print(json.dumps({"record": "unit_label_cube_rung", **r}, sort_keys=True))
        print(json.dumps({"record": "fano_lines", "n": len(lines),
                          "lines": lines}, sort_keys=True))
        return 0

    print("dim  signed  label   grading-cube   unit-label-cube   index-lane   "
          "sign-lane   closed form      wrong")
    print("     units   bits    vertices       vertices          violations   "
          "violations  2*dim*(dim-1)")
    for r in rungs:
        num, den = r["fraction_wrong"]
        print("%3d  %6d  %5d   %12d   %16d   %10d   %10d  %13d      %d/%d"
              % (r["dim"], r["signed_units"], r["label_bits"],
                 r["grading_cube_vertices"], r["unit_label_cube_vertices"],
                 r["index_lane_violations"], r["sign_lane_violations"],
                 r["sign_lane_violations_closed_form"], num, den))
    print()
    print("H (dim 4): 8 signed units -> 3 bits -> a 3-CUBE")
    print("O (dim 8): 16 signed units -> 4 bits -> a 4-CUBE (TESSERACT)")
    print("S (dim 16): 16 basis DIRECTIONS -> the tesseract as a GRADING cube")
    print("  => two different 16s on the same tesseract.")
    print()
    print("O contains H %d times (the Fano lines): %s"
          % (len(lines), [l["line"] for l in lines]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
