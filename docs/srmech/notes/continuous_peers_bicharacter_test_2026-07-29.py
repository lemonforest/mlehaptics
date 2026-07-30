#!/usr/bin/env python3
# RUN (WSL2, numpy-absent, from the srmech python tree):
#   cd /mnt/d/GitHub/mlehaptics/docs/srmech/python && \
#   PYTHONPATH=$PWD python3 ../notes/continuous_peers_bicharacter_test_2026-07-29.py
"""LANE 2 PART J -- THE CRUX.  Is our beta even a BICHARACTER?

Elduque & Rodrigo-Escudero (arXiv:1801.07002v1, p.3, the paragraph before
Theorem 2) derive bimultiplicativity of beta FROM ASSOCIATIVITY:

    "The associativity of F^sigma G gives, for any g,h,k in G: ...
     and therefore beta is multiplicative in the first variable,
     beta(gh,k) = beta(g,k) beta(h,k), and likewise in the second; so beta is
     an alternating ... bicharacter on G."

So the derivation is UNAVAILABLE the moment the twist stops being a 2-cocycle.
This part MEASURES whether beta is nonetheless bimultiplicative at each rung.
If it is NOT, then at that rung beta is not an object Elduque Thm 2 or
Prasad-Vemuri Sec.2 can even accept as input -- the bridge does not merely lose
its classifying power, it loses its DOMAIN.

SUBJECT: the shipped cd_basis_product cocycle, and the shipped algebra_table
gamma family as a control.

No float, no numpy, no fractions, no abs().
"""
from __future__ import annotations

import itertools
import json
import sys

from srmech.amsc.cascade.cayley_dickson import algebra_table, cd_basis_product

OUT: list = []


def rec(**kw):
    OUT.append(kw)
    print(json.dumps(kw, sort_keys=True))
    sys.stdout.flush()


def k_pin_slot(sign: int) -> int:
    return 0 if sign == 1 else 1


def eps_bits(dim: int):
    return [[k_pin_slot(cd_basis_product(dim, i, j)[1]) for j in range(dim)]
            for i in range(dim)]


def eps_bits_gamma(dim: int, gammas):
    tab = algebra_table(dim, gammas)
    out = []
    for i in range(dim):
        row = []
        for j in range(dim):
            col = tab[i][j]
            idx = [k for k in range(dim) if col[k] != 0]
            row.append(k_pin_slot(col[idx[0]]))
        out.append(row)
    return out


def beta_of(eps):
    dim = len(eps)
    return [[(eps[i][j] + eps[j][i]) % 2 for j in range(dim)] for i in range(dim)]


def bimultiplicativity_failures(R):
    """R is the F2 additive form; bimultiplicative means
       R(x^y, z) == R(x,z) + R(y,z)  and  R(x, y^z) == R(x,y) + R(x,z)."""
    dim = len(R)
    left = right = 0
    witness = None
    for x in range(dim):
        for y in range(dim):
            for z in range(dim):
                if R[x ^ y][z] != (R[x][z] + R[y][z]) % 2:
                    left += 1
                    if witness is None:
                        witness = {"x": x, "y": y, "z": z,
                                   "R_xy_z": R[x ^ y][z],
                                   "R_x_z_plus_R_y_z": (R[x][z] + R[y][z]) % 2}
                if R[x][y ^ z] != (R[x][y] + R[x][z]) % 2:
                    right += 1
    return left, right, witness


def clifford_eps(d: int, mu_bits):
    dim = 1 << d
    out = []
    for x in range(dim):
        xb = [(x >> t) & 1 for t in range(d)]
        row = []
        for y in range(dim):
            yb = [(y >> t) & 1 for t in range(d)]
            s = 0
            for i in range(d):
                for j in range(i):
                    s += xb[i] * yb[j]
            for i in range(d):
                if xb[i] and yb[i]:
                    s += mu_bits[i]
            row.append(s % 2)
        out.append(row)
    return out


def is_cocycle_failures(eps):
    dim = len(eps)
    bad = 0
    for x in range(dim):
        for y in range(dim):
            for z in range(dim):
                if (eps[x][y] + eps[x ^ y][z]) % 2 != (eps[y][z] + eps[x][y ^ z]) % 2:
                    bad += 1
    return bad


def part_j():
    names = ("R", "C", "H", "O", "S", "T")
    for d in range(0, 6):
        dim = 1 << d
        eps = eps_bits(dim)
        R = beta_of(eps)
        left, right, wit = bimultiplicativity_failures(R)
        cyc = is_cocycle_failures(eps)
        rec(kind="is_beta_a_bicharacter", d=d, dim=dim, algebra=names[d],
            n_triples=dim ** 3,
            bimult_failures_left=left, bimult_failures_right=right,
            beta_is_a_bicharacter=(left == 0 and right == 0),
            delta_eps_failures=cyc, eps_is_a_2_cocycle=(cyc == 0),
            first_witness=wit,
            note="Elduque arXiv:1801.07002 p.3 derives bimultiplicativity of "
                 "beta FROM associativity.  Measured here independently.")

    # CONTROL 1: the Clifford twist at the same groups -- must be a bicharacter
    # at every d, because it IS a 2-cocycle at every d.
    for d in range(1, 6):
        cl = clifford_eps(d, [1] * d)
        R = beta_of(cl)
        left, right, _ = bimultiplicativity_failures(R)
        rec(kind="control_clifford_beta_is_a_bicharacter", d=d, dim=1 << d,
            bimult_failures_left=left, bimult_failures_right=right,
            beta_is_a_bicharacter=(left == 0 and right == 0),
            delta_eps_failures=is_cocycle_failures(cl),
            note="Cl_{0,d} to Elduque Sec.4 spec: associative at every rung, so "
                 "beta must be (and is) a bicharacter at every rung.  This is "
                 "the negative control that the probe is not stuck on zero.")

    # CONTROL 2: the whole shipped gamma family at d = 3 -- do the SPLIT forms
    # behave differently from definite O?
    for gam in itertools.product((-1, 1), repeat=3):
        eps = eps_bits_gamma(8, list(gam))
        R = beta_of(eps)
        left, right, _ = bimultiplicativity_failures(R)
        rec(kind="control_gamma_family_bicharacter", d=3, gammas=list(gam),
            bimult_failures_left=left, bimult_failures_right=right,
            beta_is_a_bicharacter=(left == 0 and right == 0),
            delta_eps_failures=is_cocycle_failures(eps),
            note="all 8 gamma tables at d=3, definite and split alike")


if __name__ == "__main__":
    part_j()
    with open(__file__.replace(".py", ".ndjson"), "w") as fh:
        for r in OUT:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
