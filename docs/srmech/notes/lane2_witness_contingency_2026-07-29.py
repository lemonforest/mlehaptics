#!/usr/bin/env python3
"""LANE 2 follow-up — CLAIM (1): is the alternativity failure CONSTRUCTIVELY
the same event as the zero-divisor / composition failure, or does it merely
accompany it?

"composition => alternative" is a THEOREM, so observing that the sedenions
violate both measures NOTHING.  What is NOT forced is whether the SAME element
carries both failures.  This builds the full 2x2 contingency over every
two-term element ``x = e_i + s*e_j`` at dim 16 (and 32):

    LEFT-ALT-BROKEN   := exists y with [x,x,y] != 0
    ZERO-DIVISOR      := left_mult_kernel(x) is nonempty
    COMPOSITION-BROKEN:= exists y with N(x*y) != N(x)*N(y)

If the three sets coincide element-for-element, "one loss and two corollaries"
has constructive content.  If they merely overlap, it does not.

SUBJECT ops: algebra_table / table_product / cd_norm_sq / left_mult_kernel /
cd_basis / cd_add.  Exact integers + exact Q; no float, no abs().
"""
from __future__ import annotations

import json
import sys

from srmech.amsc.cascade.cayley_dickson import (
    algebra_table, table_product, cd_add, cd_basis, cd_norm_sq,
    left_mult_kernel,
)


def emit(rec):
    sys.stdout.write(json.dumps(rec, sort_keys=True) + "\n")


def assoc(t, dim, x, y, z):
    lhs = table_product(t, table_product(t, x, y), z)
    rhs = table_product(t, x, table_product(t, y, z))
    minus = [0] * dim
    minus[0] = -1
    return cd_add(lhs, table_product(t, minus, rhs))


def nz(v):
    return any(c != 0 for c in v)


def main():
    for dim in (16,):
        t = algebra_table(dim, None)
        gen = dim // 2
        cells = {}
        alt_broken = set()
        zd_set = set()
        comp_broken = set()
        touches_gen_alt = 0
        touches_gen_zd = 0
        total = 0
        for i in range(1, dim):
            for j in range(i + 1, dim):
                for s in (1, -1):
                    total += 1
                    key = (i, j, s)
                    x = [0] * dim
                    x[i] = 1
                    x[j] = s
                    # LEFT-ALT: exists basis y with [x,x,y] != 0
                    ab = any(nz(assoc(t, dim, x, x, cd_basis(dim, k)))
                             for k in range(dim))
                    # ZERO DIVISOR (EXHIBITED via the exact kernel, not sampled)
                    ker = left_mult_kernel(x, t)
                    zd = len(ker) > 0
                    # COMPOSITION: exists basis y with N(xy) != N(x)N(y)
                    nx = cd_norm_sq(x)
                    cb = False
                    for k in range(dim):
                        y = cd_basis(dim, k)
                        if cd_norm_sq(table_product(t, x, y)) != nx * cd_norm_sq(y):
                            cb = True
                            break
                    if ab:
                        alt_broken.add(key)
                        if gen in (i, j):
                            touches_gen_alt += 1
                    if zd:
                        zd_set.add(key)
                        if gen in (i, j):
                            touches_gen_zd += 1
                    if cb:
                        comp_broken.add(key)
                    cell = "%s/%s/%s" % ("ALTBRK" if ab else "alt-ok",
                                         "ZD" if zd else "no-zd",
                                         "COMPBRK" if cb else "comp-ok")
                    cells[cell] = cells.get(cell, 0) + 1
        emit({
            "record": "witness_contingency", "dim": dim,
            "two_term_elements_tested": total,
            "designated_generator": gen,
            "n_left_alt_broken": len(alt_broken),
            "n_zero_divisor": len(zd_set),
            "n_composition_broken": len(comp_broken),
            "alt_equals_zd": alt_broken == zd_set,
            "alt_subset_of_zd": alt_broken <= zd_set,
            "zd_subset_of_alt": zd_set <= alt_broken,
            "alt_minus_zd": len(alt_broken - zd_set),
            "zd_minus_alt": len(zd_set - alt_broken),
            "comp_equals_alt": comp_broken == alt_broken,
            "comp_minus_alt": len(comp_broken - alt_broken),
            "alt_minus_comp": len(alt_broken - comp_broken),
            "cells": cells,
            "alt_broken_touching_designated_generator": touches_gen_alt,
            "zd_touching_designated_generator": touches_gen_zd,
            "two_term_elements_touching_generator":
                2 * 2 * (dim - 1),
            "note": ("a two-term x = e_i + s*e_j; the generator-touching count "
                     "is the lane-3 read on ELEMENTS rather than triples"),
        })


if __name__ == "__main__":
    main()
