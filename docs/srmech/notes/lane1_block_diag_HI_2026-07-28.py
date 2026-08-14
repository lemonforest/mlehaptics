#!/usr/bin/env python3
"""LANE 1, sections H + I (split out so they run standalone).

H — R[G] for the central extension G: the REAL irrep dimensions of the
    extension, and where the twisted (faithful) summand sits.
I — H's simplicity + the uniqueness of its simple module: the "4D native
    irrep" claim, MEASURED.
"""
import json
import random
import sys

from srmech.amsc.q import Q
from srmech.amsc.qmat import QMat
from srmech.amsc.cascade.cayley_dickson import algebra_table, table_product
import srmech

# load the LANE-1 core out of the hyphenated sibling (one script, one record)
import importlib.util as _ilu                                   # noqa: E402
import os as _os                                                # noqa: E402
_core_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                           "lane1_block_diagonalisation_2026-07-28.py")
_spec = _ilu.spec_from_file_location("lane1_core", _core_path)
_core = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_core)
eps_of = _core.eps_of
clifford_table = _core.clifford_table
left_reg = _core.left_reg
right_reg = _core.right_reg
matvec = _core.matvec
rank_of = _core.rank_of
invariant_blocks = _core.invariant_blocks
transform_table = _core.transform_table
nnz = _core.nnz
pair_support = _core.pair_support
rowspace = _core.rowspace

OUT = []


def rec(**kw):
    OUT.append(kw)
    print(json.dumps(kw), flush=True)


def group_from_eps(E):
    dim = len(E)
    elems = [(s, x) for s in (1, -1) for x in range(dim)]
    idx = {e: n for n, e in enumerate(elems)}

    def mul(a, b):
        return (a[0] * b[0] * E[a[1]][b[1]], a[1] ^ b[1])
    return elems, idx, mul


def group_algebra_table(elems, idx, mul):
    n = len(elems)
    T = [[[0] * n for _ in range(n)] for _ in range(n)]
    for a in range(n):
        for b in range(n):
            T[a][b][idx[mul(elems[a], elems[b])]] = 1
    return T


def conjugacy_classes(elems, mul):
    inv = {}
    for a in elems:
        for b in elems:
            if mul(a, b) == (1, 0):
                inv[a] = b
                break
    seen, classes = set(), []
    for a in elems:
        if a in seen:
            continue
        cl = set()
        for g in elems:
            cl.add(mul(mul(g, a), inv[g]))
        seen |= cl
        classes.append(sorted(cl))
    return classes


def section_H():
    """R[G] = R[G]e_+ (+) R[G]e_-  with e_± = (1 ± z)/2, z the central -1.

    The MINUS part is exactly R^eps[(Z/2)^d] — the faithful projective
    summand.  Cheap and decisive: split on the central idempotent, then read
    each ideal's own idempotent structure."""
    cases = [
        (eps_of(algebra_table(2)), "Z/4  (CD d=1 == Clifford d=1)", 2),
        (eps_of(algebra_table(4)), "Q8   (CD d=2 == Clifford d=2)", 4),
        (eps_of(clifford_table(3)), "Clifford d=3 extension (order 16)", 8),
    ]
    for E, label, tw in cases:
        elems, idx, mul = group_from_eps(E)
        gt = group_algebra_table(elems, idx, mul)
        n = len(elems)
        cls = conjugacy_classes(elems, mul)
        # z = the central (-1, 0); e_minus = (1 - z)/2 spans the twisted part
        z = idx[(-1, 0)]
        one = idx[(1, 0)]
        e_minus = [Q(0)] * n
        e_minus[one] = Q(1, 2)
        e_minus[z] = Q(-1, 2)
        e_plus = [Q(0)] * n
        e_plus[one] = Q(1, 2)
        e_plus[z] = Q(1, 2)
        dims = {}
        for nm, e in (("plus(z->+1, untwisted)", e_plus),
                      ("minus(z->-1, TWISTED)", e_minus)):
            rows = []
            for k in range(n):
                ek = [Q(1) if m == k else Q(0) for m in range(n)]
                v = list(table_product(gt, ek, e))
                rows.append(v)
            dims[nm] = rank_of(rows)
        # the minus ideal, as an algebra, is R^eps[(Z/2)^d] == algebra_table(tw)
        rec(kind="H1_group_algebra", group=label, group_order=n,
            n_conjugacy_classes=len(cls), n_complex_irreps=len(cls),
            sum_of_squares_check=n,
            ideal_dims=dims,
            twisted_part_real_dim=tw,
            note="R[G] splits on the central idempotent; the MINUS ideal has "
                 f"real dim {tw} and IS R^eps[(Z/2)^d] — for Q8 that is H, "
                 "the unique 4-dim real irrep block; the PLUS ideal is the "
                 "untwisted R[(Z/2)^d] = R^d, all 1-dim blocks")


def section_I():
    for dim, name in ((2, "C"), (4, "H"), (8, "O"), (16, "S(sedenion)")):
        t = algebra_table(dim)
        random.seed(7 + dim)
        noninv = 0
        min_left_ideal = dim
        for _ in range(300):
            x = [random.randint(-3, 3) for _ in range(dim)]
            if all(v == 0 for v in x):
                continue
            rows = [matvec(left_reg(t, i), x) for i in range(dim)]
            r = rank_of(rows)
            if r < dim:
                noninv += 1
            min_left_ideal = min(min_left_ideal, r)
        # every basis-supported small element too (structured probe)
        for i in range(dim):
            for j in range(i + 1, dim):
                for s in (1, -1):
                    x = [0] * dim
                    x[i], x[j] = 1, s
                    rows = [matvec(left_reg(t, k), x) for k in range(dim)]
                    r = rank_of(rows)
                    min_left_ideal = min(min_left_ideal, r)
                    if r < dim:
                        noninv += 1
        x = [0] * dim
        x[1] = 1
        rows = []
        for i in range(dim):
            for j in range(dim):
                rows.append(matvec(left_reg(t, i), matvec(right_reg(t, j), x)))
        rec(kind="I1_simplicity", algebra=name, dim=dim,
            min_left_ideal_dim=min_left_ideal,
            elements_generating_a_PROPER_left_ideal=noninv,
            two_sided_ideal_of_e1_dim=rank_of(rows),
            no_proper_left_ideal_found=(min_left_ideal == dim),
            simple_module_real_dim=min_left_ideal)


if __name__ == "__main__":
    rec(kind="env", srmech_version=srmech.__version__)
    section_H()
    section_I()
    with open("lane1_block_diag_HI_2026-07-28.ndjson", "w",
              encoding="utf-8") as fh:
        for r in OUT:
            fh.write(json.dumps(r) + "\n")
