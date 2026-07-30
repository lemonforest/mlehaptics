#!/usr/bin/env python3
"""LANE 2 correction — the zero-divisor probe in the main sweep searched only
x = e_i + s*e_j with 1 <= i < j, i.e. it EXCLUDED e_0.  At dim 2 that search
space is EMPTY, so it reported "no zero divisor" for split-C — a FALSE
NEGATIVE, since (1+j)(1-j) = 0 is precisely split-C's zero divisor and the
rung-1 probe in the same run exhibited it.

This re-runs the zero-divisor decision over 0 <= i < j < dim (e_0 included),
for every algebra in the control family at dims 2/4/8/16, so the
alternative x composition x zero-divisor contingency table is stated on a
search space that can actually see the dim-2 and definiteness-driven cases.

Decision is EXHIBITION, not sampling: left_mult_kernel is the exact rational
nullspace of L(x).
"""
from __future__ import annotations

import itertools
import json
import sys

from srmech.amsc.cascade.cayley_dickson import (
    algebra_table, table_product, left_mult_kernel, inertia_signature,
)


def emit(rec):
    sys.stdout.write(json.dumps(rec, sort_keys=True) + "\n")
    sys.stdout.flush()


def zd(table, dim):
    for i in range(dim):
        for j in range(i + 1, dim):
            for s in (1, -1):
                x = [0] * dim
                x[i] = 1
                x[j] = s
                ker = left_mult_kernel(x, table)
                if ker:
                    y = ker[0]
                    prod = table_product(table, x, y)
                    return {"has_zero_divisor": True,
                            "x_form": "e%d %s e%d" % (i, "+" if s > 0 else "-", j),
                            "y": [str(v) for v in y],
                            "product_is_zero": all(v == 0 for v in prod)}
    return {"has_zero_divisor": False}


def main():
    for dim in (2, 4, 8, 16):
        rungs = dim.bit_length() - 1
        for g in itertools.product((-1, 1), repeat=rungs):
            t = algebra_table(dim, None if all(v == -1 for v in g) else g)
            name = ("CD-definite" if all(v == -1 for v in g)
                    else "SPLIT-" + "".join("+" if v > 0 else "-" for v in g))
            sig = inertia_signature(t)
            r = zd(t, dim)
            r.update({"record": "zero_divisor_corrected", "dim": dim,
                      "algebra": name, "gammas": list(g),
                      "norm_signature": list(sig["norm_signature"]),
                      "norm_is_definite": sig["norm_signature"][1] == 0
                                          and sig["norm_signature"][2] == 0,
                      "search_space": "x = e_i +/- e_j, 0 <= i < j < dim "
                                      "(e_0 INCLUDED — the fix)"})
            emit(r)


if __name__ == "__main__":
    main()
