#!/usr/bin/env python3
# RUN (WSL2, numpy-absent, from the srmech python tree):
#   cd docs/srmech/python && \n#   PYTHONPATH=$PWD python3 <this file>
"""LANE 1 PART A — the F2 group-cohomology DEGREE LADDER for G = (Z/2)^d.

SUBJECT of every rank measurement: the SHIPPED srmech GF(2) op
``srmech.amsc.modular_linalg.gf_rref(rows, p=2)`` (rc350).
LABELLED ORACLE: ``_oracle_f2_rank_bitpacked`` — a bit-packed column
elimination used ONLY where the dense gf_rref matrix does not fit
(d=4, n=3: 4096 x 65536).  It is validated rank-identical to gf_rref on
EVERY case where both run.

CONVENTION (stated, per the brief):
  * INHOMOGENEOUS (bar) cochains, TRIVIAL G-action, coefficients F2.
    C^n = Maps(G^n, F2), dim = 2^(d*n)   <- the UNNORMALISED bar complex,
    exactly the dimension the brief specifies.
  * (delta f)(g_1..g_{n+1}) = f(g_2..g_{n+1})
                              + sum_{k=1..n} f(..,g_k+g_{k+1},..)
                              + f(g_1..g_n)
    All signs are +1 because char = 2; the leading g_1 . f(...) term is
    f(...) because the action is trivial.
  * The NORMALISED subcomplex Ctilde^n = {f : f vanishes if any argument is
    the identity}, dim (2^d - 1)^n, is computed too as an INDEPENDENT
    convention check: it must give the SAME H^n.
  * WHY unnormalised is primary: it is the complex whose dimension the brief
    fixes (2^(d n)), and it needs no unitality assumption about epsilon.
    WHY normalised is also computed: srmech's shipped sign cochain IS unital
    (e_0 = 1), so the normalised complex is where the shipped object natively
    lives, and agreement of the two is the convention's own falsification test.

No float, no numpy, no fractions, no abs().  Exact F2 throughout.
"""
import itertools
import json
import sys

from srmech.amsc import _native as _N
from srmech.amsc.modular_linalg import gf_rref

OUT = []


def rec(**kw):
    OUT.append(kw)
    print(json.dumps(kw, sort_keys=True))
    sys.stdout.flush()


# ── LABELLED ORACLE (hand-rolled; used only past the gf_rref size wall) ────
def _oracle_f2_rank_bitpacked(columns):
    """F2 rank of a matrix given as an iterable of COLUMN bitmasks (Python
    ints).  rank(M) = dim span(columns).  Pure integer XOR elimination."""
    piv = {}
    for c in columns:
        v = c
        while v:
            p = v.bit_length() - 1
            w = piv.get(p)
            if w is None:
                piv[p] = v
                break
            v ^= w
    return len(piv)


# ── the bar-complex face maps ─────────────────────────────────────────────
def faces(s):
    """The n+2 face maps of the inhomogeneous bar complex applied to a tuple
    s = (g_1,...,g_{n+1}); group law is XOR."""
    out = [s[1:]]
    for k in range(len(s) - 1):
        out.append(s[:k] + (s[k] ^ s[k + 1],) + s[k + 2:])
    out.append(s[:-1])
    return out


def cochain_basis(d, n, normalised):
    lo = 1 if normalised else 0
    return list(itertools.product(range(lo, 1 << d), repeat=n))


def delta_columns(d, n, normalised):
    """delta_n : C^n -> C^{n+1} as COLUMN bitmasks over the C^n basis order.
    One column per element of G^{n+1} (the normalised complex restricts to
    tuples with no identity entry, and drops faces that acquire one)."""
    rows = cochain_basis(d, n, normalised)
    ridx = {t: i for i, t in enumerate(rows)}
    cols = []
    for s in cochain_basis(d, n + 1, normalised):
        v = 0
        for f in faces(s):
            i = ridx.get(f)
            if i is not None:                      # normalised: face may die
                v ^= (1 << i)
        cols.append(v)
    return len(rows), cols


def delta_dense_rows(n_rows, cols):
    """The same map as a dense row list for the SHIPPED gf_rref."""
    return [[(c >> r) & 1 for c in cols] for r in range(n_rows)]


def binom(n, k):
    if k < 0 or k > n:
        return 0
    num, den = 1, 1
    for i in range(k):
        num *= (n - i)
        den *= (i + 1)
    return num // den


# ── the ladder ────────────────────────────────────────────────────────────
GF_RREF_CELL_CAP = 4_000_000      # dense-matrix size wall for gf_rref

rec(kind="environment",
    has_native=bool(_N.HAS_NATIVE),
    gf_rref_native=bool(_N.has_native_gf_rref()),
    note="gf_rref is the SUBJECT op for every rank below")

for normalised in (False, True):
    label = "normalised" if normalised else "unnormalised"
    for d in (1, 2, 3, 4):
        ranks = {}
        dims = {}
        for n in range(0, 4):
            n_rows, cols = delta_columns(d, n, normalised)
            dims[n] = n_rows
            cells = n_rows * len(cols)
            r_oracle = _oracle_f2_rank_bitpacked(cols)
            r_subject = None
            agree = None
            if cells <= GF_RREF_CELL_CAP and n_rows > 0:
                dense = delta_dense_rows(n_rows, cols)
                r_subject = gf_rref(dense, 2)["rank"]
                agree = (r_subject == r_oracle)
                del dense
            ranks[n] = r_subject if r_subject is not None else r_oracle
            rec(kind="delta_rank", complex=label, d=d, n=n,
                dim_C_n=n_rows, dim_C_n_plus_1=len(cols),
                matrix_cells=cells,
                rank_gf_rref_SUBJECT=r_subject,
                rank_bitpacked_ORACLE=r_oracle,
                subject_oracle_agree=agree,
                used=("gf_rref" if r_subject is not None else "oracle"))
        # cohomology
        for n in range(0, 4):
            Zn = dims[n] - ranks[n]
            Bn = ranks[n - 1] if n >= 1 else 0
            Hn = Zn - Bn
            pred = binom(n + d - 1, d - 1)
            rec(kind="cohomology", complex=label, d=d, n=n,
                dim_C_n=dims[n], rank_delta_n=ranks[n],
                dim_Z_n=Zn, dim_B_n=Bn, dim_H_n=Hn,
                oracle_poly_ring_dim=pred, matches_oracle=(Hn == pred),
                oracle="H^*((Z/2)^d;F2) = F2[x_1..x_d], deg x_i = 1 "
                       "=> dim H^n = C(n+d-1, d-1)")
