#!/usr/bin/env python3
"""LANE 2 follow-up — CLAIM (2) on GENERAL elements, EXHIBITED not sampled.

Claim (2) says the rungs above H narrow WHICH SHAPE of triple still associates:
  H  associativity  (a,b,c)  ALL          O  alternativity (a,a,b)/(a,b,b)
  S  flexibility    (a,b,a)  PALINDROME
The main sweep found that on BASIS triples ALL THREE diagonal shapes still
vanish at dim 16 AND dim 32 — so the basis-diagonal read cannot see the
narrowing and is a FALSE GREEN (the random-anticommutative control has
``aba_nonzero = 0`` while failing flexibility outright).

This probe settles the shapes on GENERAL elements:
  - the REPEAT shape is broken by EXHIBITING x, y with [x,x,y] != 0;
  - the PALINDROME shape is decided EXACTLY, not sampled: [x,y,z] + [z,y,x] is
    TRILINEAR, so vanishing on every ordered basis triple is a complete proof
    that it vanishes identically.  The main sweep already did that sweep in
    full (32768/32768 at dim 32); here the exhibited repeat-witness is fed
    back through [x,y,x] to show the two shapes genuinely separate on the SAME
    element.
"""
from __future__ import annotations

import json
import sys

from srmech.amsc.cascade.cayley_dickson import (
    algebra_table, table_product, cd_add, cd_basis, cd_norm_sq,
)


def emit(rec):
    sys.stdout.write(json.dumps(rec, sort_keys=True) + "\n")


def assoc(t, dim, x, y, z):
    lhs = table_product(t, table_product(t, x, y), z)
    rhs = table_product(t, x, table_product(t, y, z))
    minus = [0] * dim
    minus[0] = -1
    return cd_add(lhs, table_product(t, minus, rhs))


def nonzero(v):
    return any(c != 0 for c in v)


def main():
    for dim in (8, 16, 32):
        t = algebra_table(dim, None)
        found = None
        # search x = e_i + e_j (i<j), y = e_k : the smallest possible witness
        for i in range(1, dim):
            for j in range(i + 1, dim):
                x = [0] * dim
                x[i] = 1
                x[j] = 1
                for k in range(1, dim):
                    y = cd_basis(dim, k)
                    a_xxy = assoc(t, dim, x, x, y)
                    if nonzero(a_xxy):
                        found = (i, j, k, x, list(y), a_xxy)
                        break
                if found:
                    break
            if found:
                break
        if found is None:
            emit({"record": "shape_general", "dim": dim,
                  "repeat_shape_witness": None,
                  "repeat_shape_aab_breaks": False,
                  "note": "no [x,x,y] != 0 witness of the form (e_i+e_j, e_k)"})
            continue
        i, j, k, x, y, a_xxy = found
        a_xyx = assoc(t, dim, x, y, x)
        a_xyy = assoc(t, dim, x, y, y)
        yy = [0] * dim
        yy[k] = 1
        emit({
            "record": "shape_general", "dim": dim,
            "x_form": "e%d + e%d" % (i, j), "y_form": "e%d" % k,
            "x_norm_sq": str(cd_norm_sq(x)), "y_norm_sq": str(cd_norm_sq(y)),
            "assoc_xxy_REPEAT_left": [str(v) for v in a_xxy],
            "assoc_xxy_is_nonzero": nonzero(a_xxy),
            "assoc_xyy_REPEAT_right": [str(v) for v in a_xyy],
            "assoc_xyy_is_nonzero": nonzero(a_xyy),
            "assoc_xyx_PALINDROME": [str(v) for v in a_xyx],
            "assoc_xyx_is_nonzero": nonzero(a_xyx),
            "designated_generator": dim // 2,
            "witness_touches_designated_generator": (dim // 2) in (i, j, k),
            "note": ("REPEAT broken / PALINDROME intact on the SAME element "
                     "is the separation claim (2) needs"),
        })


if __name__ == "__main__":
    main()
