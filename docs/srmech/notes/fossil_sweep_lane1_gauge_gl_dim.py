"""LANE 1 — fossil sweep of multiplication-table invariants under the THREE-part test.

Subject = SHIPPED srmech ops:
  * ``srmech.amsc.cascade.algebra_table(dim, gammas)``  — the generalised
    Cayley–Dickson structure tensor (gammas=None IS the definite ladder and IS
    ``octonion_mult_table()``; a +1 makes it split from that rung up).
  * ``srmech.amsc.cascade.cd_basis_product(dim, i, j)`` — the ONE-entry cocycle.
  * ``srmech.amsc.cascade.table_product(table, x, y)``  — the EXACT-ℚ table-driven
    product; used as the ground-truth associator oracle (Q carrier, no float).
  * ``srmech.amsc.cascade.left_mult_kernel(x, table)``  — zero-divisor detector.
  * ``srmech.amsc.cascade.inertia_signature(table)``    — metric signature.
  * ``srmech.amsc.modular_linalg.gf_rref(rows, p=2)``   — GF(2) rank (Class L/I).
  * ``srmech.amsc.q.Q``                                 — the exact rational carrier.

HAND-ROLLED, EXPLICITLY LABELLED ORACLES (a missing shipped surface is a FINDING):
  * ``rand_anticomm_table``  — no shipped random-anticommutative-table constructor
    exists (``algebra_table`` only spans the 2^log2(dim)-member gamma family).
  * the gauge (coboundary) group, the GL(d,F2) enumeration, and the delta of a
    2-cochain — no shipped surface for any of the three.
  * an EXACT associator over an ARBITRARY structure-constant table — the shipped
    ``srmech.amsc.hdc.loop_associator`` is float-carriered AND hard-wired to the
    definite dim-8 loop (no ``table=`` parameter), so it cannot be run on
    split-O at all.  Composed here from the shipped exact ``table_product``.

Exact integers / exact ℚ / F2 only.  No float, no tolerance, no numpy, no
stdlib fractions, no abs() (sign is the Class-K pin-slot; sign re-application is
Class C).

Run:  cd docs/srmech/python && python3 ../notes/fossil_sweep_lane1_gauge_gl_dim.py
Emits NDJSON on stdout (one record per measurement).
"""

import json
import sys

from srmech.amsc.cascade import (
    algebra_table,
    cd_basis_product,
    inertia_signature,
    left_mult_kernel,
    table_product,
)
from srmech.amsc.modular_linalg import gf_rref
from srmech.amsc.q import Q

OUT = []


def emit(**rec):
    OUT.append(rec)
    sys.stdout.write(json.dumps(rec, sort_keys=True) + "\n")


# ──────────────────────────────────────────────────────────────────────
# F2 cochain layer.  E[i][j] in {0,1};  0 encodes +1, 1 encodes -1.
# (Class-K pin-slot as an F2 bit — never abs().)
# ──────────────────────────────────────────────────────────────────────

def eps_from_table(T):
    """Extract the sign 2-cochain from a MONOMIAL structure tensor; asserts
    monomiality and that the index lane is XOR (both are then MEASURED facts)."""
    dim = len(T)
    E = [[0] * dim for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            row = T[i][j]
            nz = [t for t in range(dim) if row[t] != 0]
            assert len(nz) == 1, f"table not monomial at ({i},{j}): {nz}"
            assert nz[0] == (i ^ j), f"index lane != XOR at ({i},{j}): {nz[0]}"
            v = row[nz[0]]
            assert v == 1 or v == -1, f"structure constant {v} not +-1"
            E[i][j] = 0 if v == 1 else 1
    return E


def pack(E):
    """256/... -bit int packing of a dim x dim F2 cochain (row-major)."""
    dim = len(E)
    n = 0
    for i in range(dim):
        for j in range(dim):
            if E[i][j]:
                n |= 1 << (i * dim + j)
    return n


def unpack(n, dim):
    return [[(n >> (i * dim + j)) & 1 for j in range(dim)] for i in range(dim)]


def delta_columns(dim):
    """Column representation of the F2-linear map delta: C^2 -> C^3.

    delta(E)(a,b,c) = E[b][c] ^ E[a][b^c] ^ E[a][b] ^ E[a^b][c].
    Returns col[p] = a dim^3-bit int; delta(E) = XOR of col[p] over set bits p of
    pack(E).  Exact F2, no float."""
    col = [0] * (dim * dim)
    for a in range(dim):
        for b in range(dim):
            for c in range(dim):
                t = (a * dim + b) * dim + c
                for (p, q) in ((b, c), (a, b ^ c), (a, b), (a ^ b, c)):
                    col[p * dim + q] ^= 1 << t
    return col


def delta_of(packed, col, dim):
    out = 0
    n = packed
    while n:
        low = n & -n
        p = low.bit_length() - 1
        out ^= col[p]
        n ^= low
    return out


def coboundary_gens(dim):
    """The dim-1 generators of the gauge (coboundary) subgroup B^2, packed.

    gauge s: index -> {+-1}, s(0)=+1, so t in F2^dim with t[0]=0.
    (delta t)(i,j) = t[i] ^ t[j] ^ t[i^j].  Generator k = indicator of index k."""
    gens = []
    for k in range(1, dim):
        n = 0
        for i in range(dim):
            for j in range(dim):
                bit = (1 if i == k else 0) ^ (1 if j == k else 0) ^ (1 if (i ^ j) == k else 0)
                if bit:
                    n |= 1 << (i * dim + j)
        gens.append(n)
    return gens


def all_coboundaries(dim):
    """EXPLICIT enumeration of all 2^(dim-1) gauge rescalings, as packed ints."""
    gens = coboundary_gens(dim)
    out = [0]
    for g in gens:
        out = out + [x ^ g for x in out]
    return out


# ──────────────────────────────────────────────────────────────────────
# GL(d, F2) — explicit enumeration (168 at d=3, 20160 at d=4), rank via the
# SHIPPED gf_rref over GF(2).
# ──────────────────────────────────────────────────────────────────────

def gl_perms(d, use_shipped_rref=True):
    """Every g in GL(d,F2), returned as the induced permutation of [0, 2^d)."""
    dim = 1 << d
    perms = []
    for m in range(1 << (d * d)):
        rows = [[(m >> (r * d + c)) & 1 for c in range(d)] for r in range(d)]
        if use_shipped_rref:
            if gf_rref(rows, 2)["rank"] != d:
                continue
        perm = [0] * dim
        for i in range(dim):
            v = 0
            for r in range(d):
                s = 0
                for c in range(d):
                    s ^= rows[r][c] & ((i >> c) & 1)
                if s:
                    v |= 1 << r
            perm[i] = v
        assert len(set(perm)) == dim
        # linearity check (MEASURED, not assumed): g(i^j) == g(i)^g(j)
        for i in range(dim):
            for j in range(dim):
                assert perm[i ^ j] == perm[i] ^ perm[j]
        perms.append(tuple(perm))
    return perms


def relabel(E, perm):
    dim = len(E)
    return [[E[perm[i]][perm[j]] for j in range(dim)] for i in range(dim)]


# ──────────────────────────────────────────────────────────────────────
# Tables under test.
# ──────────────────────────────────────────────────────────────────────

def gamma_family(dim):
    """Every member of the shipped gamma family at this dim (definite + splits)."""
    n = dim.bit_length() - 1
    out = {}
    for m in range(1 << n):
        g = tuple(1 if (m >> k) & 1 else -1 for k in range(n))
        out[g] = algebra_table(dim, None if all(v < 0 for v in g) else list(g))
    return out


class _Lcg:
    """LABELLED ORACLE — deterministic integer LCG (no float, no random module
    state leaking into a load-bearing number).  Numerical Recipes ranqd1."""

    def __init__(self, seed):
        self.s = seed & 0xFFFFFFFF

    def bit(self):
        self.s = (1664525 * self.s + 1013904223) & 0xFFFFFFFF
        return (self.s >> 30) & 1


def rand_anticomm_table(dim, seed, diagonal=None):
    """LABELLED ORACLE — a random ANTICOMMUTATIVE monomial table.

    e0 is a two-sided identity; e_i e_j = -e_j e_i for i != j nonzero; the
    diagonal e_i^2 is either forced (``diagonal`` = list of +-1 over i>=1) or
    drawn.  NO shipped constructor exists for this (algebra_table spans only the
    gamma family), which is itself a FINDING."""
    rng = _Lcg(seed)
    E = [[0] * dim for _ in range(dim)]
    for i in range(1, dim):
        E[i][i] = 0 if (diagonal[i - 1] == 1 if diagonal else rng.bit() == 0) else 1
    for i in range(1, dim):
        for j in range(i + 1, dim):
            b = rng.bit()
            E[i][j] = b
            E[j][i] = b ^ 1
    T = [[[0] * dim for _ in range(dim)] for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            T[i][j][i ^ j] = -1 if E[i][j] else 1
    return T


# ──────────────────────────────────────────────────────────────────────
# CROSS-VALIDATION: the F2 delta MUST agree with the SHIPPED exact-Q product.
# ──────────────────────────────────────────────────────────────────────

def basis_vec(dim, i):
    return tuple(Q(1) if k == i else Q(0) for k in range(dim))


def crossvalidate(T, label):
    """Associativity of every basis triple, read TWO independent ways:
    (1) the F2 coboundary delta(eps) of the extracted cochain;
    (2) the SHIPPED exact-Q table_product, compared exactly.
    Reports 0 disagreements or the whole thing is void."""
    dim = len(T)
    E = eps_from_table(T)
    col = delta_columns(dim)
    d = delta_of(pack(E), col, dim)
    dis = 0
    fails_q = 0
    for a in range(dim):
        ea = basis_vec(dim, a)
        for b in range(dim):
            eb = basis_vec(dim, b)
            ab = table_product(T, ea, eb)
            for c in range(dim):
                ec = basis_vec(dim, c)
                lhs = table_product(T, ab, ec)
                rhs = table_product(T, ea, table_product(T, eb, ec))
                q_fail = 1 if any(x != y for x, y in zip(lhs, rhs)) else 0
                fails_q += q_fail
                t = (a * dim + b) * dim + c
                if ((d >> t) & 1) != q_fail:
                    dis += 1
    emit(kind="crossvalidate", label=label, dim=dim,
         f2_delta_failures=bin(d).count("1"), exact_q_failures=fails_q,
         disagreements=dis)
    return dis


# ──────────────────────────────────────────────────────────────────────
# Candidate measurements.
# ──────────────────────────────────────────────────────────────────────

def independent_triples(dim):
    """{(a,b,c)} linearly independent in F2^d, as a packed dim^3-bit int."""
    n = 0
    for a in range(dim):
        for b in range(dim):
            for c in range(dim):
                dep = (a == 0 or b == 0 or c == 0 or a == b or a == c
                       or b == c or (a ^ b ^ c) == 0)
                if not dep:
                    n |= 1 << ((a * dim + b) * dim + c)
    return n


def _subspace_split(d, dim):
    """How the cocycle failure set sits inside the 3-dim SUBSPACES of the grading
    group: each independent triple spans exactly one 3-dim subspace, so the
    failure set is a union of (part of) those.  GL(d,F2) is TRANSITIVE on them,
    so a GL-stable failure set must hit ALL of them equally."""
    per = {}
    for a in range(dim):
        for b in range(dim):
            for c in range(dim):
                if (a == 0 or b == 0 or c == 0 or a == b or a == c
                        or b == c or (a ^ b ^ c) == 0):
                    continue
                sub = frozenset({0, a, b, c, a ^ b, a ^ c, b ^ c, a ^ b ^ c})
                fail = (d >> ((a * dim + b) * dim + c)) & 1
                ok, bad = per.get(sub, (0, 0))
                per[sub] = (ok + (0 if fail else 1), bad + (1 if fail else 0))
    return {
        "n_3dim_subspaces": len(per),
        "all_nonassociative": sum(1 for v in per.values() if v[0] == 0),
        "all_associative": sum(1 for v in per.values() if v[1] == 0),
        "mixed": sum(1 for v in per.values() if v[0] and v[1]),
        "failures_per_subspace": sorted({v[1] for v in per.values()}),
    }


def candidates(T, label, dim, col):
    """Every candidate invariant, as exact integers / canonical tuples."""
    E = eps_from_table(T)
    P = pack(E)
    d = delta_of(P, col, dim)
    fail_bits = bin(d).count("1")

    # C1  failure set of the cocycle condition
    indep = independent_triples(dim)
    c1_set_equals_indep = (d == indep)

    # C2  diagonal q(i) = eps(i,i)  -- the SIGNATURE
    neg_diag = sum(E[i][i] for i in range(dim))

    # C3  commutator sign b(i,j) = eps(i,j)*eps(j,i)
    anti = sum(1 for i in range(dim) for j in range(dim) if (E[i][j] ^ E[j][i]))

    # C6  span of the associators: the set of RESULT indices a^b^c over the
    #     failure set (associator of basis units is +-2 e_{a^b^c} or 0), and its
    #     F2-span dimension via the SHIPPED gf_rref.
    res = set()
    for a in range(dim):
        for b in range(dim):
            for c in range(dim):
                if (d >> ((a * dim + b) * dim + c)) & 1:
                    res.add(a ^ b ^ c)
    dd = dim.bit_length() - 1
    if res:
        rows = [[(k >> t) & 1 for t in range(dd)] for k in sorted(res)]
        f2_rank = gf_rref(rows, 2)["rank"]
    else:
        f2_rank = 0
    coord_span = len(res)

    # C4/C5  gauge stabiliser + orbit -- EXPLICIT sweep over all 2^(dim-1)
    cobs = all_coboundaries(dim)
    assert len(cobs) == 1 << (dim - 1)
    stab = sum(1 for cb in cobs if cb == 0 or (P ^ cb) == P)
    orbit = {P ^ cb for cb in cobs}
    ham = {}
    orb = sorted(orbit)
    for x in range(len(orb)):
        for y in range(x + 1, len(orb)):
            h = bin(orb[x] ^ orb[y]).count("1")
            ham[h] = ham.get(h, 0) + 1

    return {
        "label": label, "dim": dim,
        "c1_cocycle_failures": fail_bits,
        "c1_assoc_triples": dim ** 3 - fail_bits,
        "c1_failset_is_independent_triples": c1_set_equals_indep,
        "c1_failset_packed_sha_proxy": fail_bits,
        "c2_neg_diagonal_count": neg_diag,
        "c3_anticommuting_pairs": anti,
        "c6_associator_coord_span": coord_span,
        "c6_associator_f2_rank": f2_rank,
        "c4_gauge_stabiliser_order": stab,
        "c5_gauge_orbit_size": len(orbit),
        "c5_hamming_multiset": {str(k): v for k, v in sorted(ham.items())},
        "_delta": d, "_packed": P, "_E": E,
    }


def gauge_sweep(T, dim, col):
    """CONDITION (i): explicit sweep over ALL 2^(dim-1) diagonal +-1 rescalings.
    Returns, for each candidate, whether it is constant across the whole orbit."""
    E = eps_from_table(T)
    P = pack(E)
    base = None
    const = {}
    for cb in all_coboundaries(dim):
        Ep = unpack(P ^ cb, dim)
        d = delta_of(P ^ cb, col, dim)
        vals = {
            "c1_failset": d,
            "c1_failcount": bin(d).count("1"),
            "c2_neg_diagonal_count": sum(Ep[i][i] for i in range(dim)),
            "c3_anticommuting_pairs": sum(1 for i in range(dim) for j in range(dim)
                                          if (Ep[i][j] ^ Ep[j][i])),
        }
        if base is None:
            base = vals
            const = {k: True for k in vals}
        else:
            for k in vals:
                if vals[k] != base[k]:
                    const[k] = False
    return const


def gl_sweep(T, dim, perms, col):
    """CONDITION (ii): explicit sweep over ALL of GL(d,F2)."""
    E = eps_from_table(T)
    d0 = delta_of(pack(E), col, dim)
    base = None
    const = {}
    gauge_equiv = 0
    gens = coboundary_gens(dim)
    # echelon basis of the coboundary space B^2 (F2 Gaussian elimination on
    # packed ints -- exact, no float)
    ech = []
    for g in gens:
        v = g
        for e in ech:
            hi = e.bit_length() - 1
            if (v >> hi) & 1:
                v ^= e
        if v:
            ech.append(v)
            ech.sort(key=lambda z: -z.bit_length())
    P0 = pack(E)
    for perm in perms:
        Eg = relabel(E, perm)
        Pg = pack(Eg)
        d = delta_of(Pg, col, dim)
        vals = {
            "c1_failset": d,
            "c1_failcount": bin(d).count("1"),
            "c2_neg_diagonal_count": sum(Eg[i][i] for i in range(dim)),
            "c3_anticommuting_pairs": sum(1 for i in range(dim) for j in range(dim)
                                          if (Eg[i][j] ^ Eg[j][i])),
        }
        if base is None:
            base = {"c1_failset": d0, "c1_failcount": bin(d0).count("1"),
                    "c2_neg_diagonal_count": sum(E[i][i] for i in range(dim)),
                    "c3_anticommuting_pairs": sum(1 for i in range(dim)
                                                  for j in range(dim)
                                                  if (E[i][j] ^ E[j][i]))}
            const = {k: True for k in vals}
        for k in vals:
            if vals[k] != base[k]:
                const[k] = False
        # is the RELABELLED table gauge-equivalent to the original?
        v = Pg ^ P0
        for e in ech:
            hi = e.bit_length() - 1
            if (v >> hi) & 1:
                v ^= e
        if v == 0:
            gauge_equiv += 1
    return const, gauge_equiv


def main():
    emit(kind="env", srmech=__import__("srmech").__version__,
         has_native=__import__("srmech.amsc._native", fromlist=["x"]).HAS_NATIVE)

    # ---- 0. the PREDICTION, exhaustively, at d = 2, 3, 4 ----------------
    for dim in (4, 8, 16):
        col = delta_columns(dim)
        T = algebra_table(dim)
        E = eps_from_table(T)
        d = delta_of(pack(E), col, dim)
        indep = independent_triples(dim)
        dd = dim.bit_length() - 1
        # ordered INDEPENDENT TRIPLES in F2^dd  = (N-1)(N-2)(N-4), N = 2^dd
        indep_formula = (dim - 1) * (dim - 2) * (dim - 4) if dd >= 3 else 0
        # ordered BASES of F2^dd = |GL(dd,F2)| -- the same number ONLY at dd = 3
        gl_order = 1
        for k in range(dd):
            gl_order *= (dim - (1 << k))
        emit(kind="prediction", dim=dim, d=dd,
             cocycle_failures=bin(d).count("1"),
             independent_triples=bin(indep).count("1"),
             independent_triple_formula=indep_formula,
             gl_order_formula=gl_order,
             sets_identical=(d == indep),
             fail_minus_indep=bin(d & ~indep).count("1"),
             indep_minus_fail=bin(indep & ~d).count("1"),
             subspace_split=_subspace_split(d, dim))

    # ---- 1. cross-validate the F2 machinery against the SHIPPED exact-Q op --
    for dim, gam in ((4, None), (8, None), (8, [-1, -1, 1]), (8, [1, -1, -1])):
        T = algebra_table(dim, gam)
        assert crossvalidate(T, f"dim{dim}_gammas{gam}") == 0

    # ---- 2. candidate table over the whole gamma family + controls --------
    for dim in (4, 8, 16):
        col = delta_columns(dim)
        fam = gamma_family(dim)
        for g, T in sorted(fam.items()):
            lbl = "definite" if all(v < 0 for v in g) else "split"
            rec = candidates(T, f"gamma{list(g)}_{lbl}", dim, col)
            sig = inertia_signature(T)
            rec.pop("_delta"); rec.pop("_packed"); rec.pop("_E")
            rec["kind"] = "candidate"
            rec["gammas"] = list(g)
            rec["family"] = lbl
            rec["inertia_trace"] = list(sig["signature"])
            emit(**rec)
        # controls: random anticommutative, and random-with-O's-diagonal
        for seed in (12345, 777, 20260729):
            T = rand_anticomm_table(dim, seed)
            rec = candidates(T, f"random_anticomm_seed{seed}", dim, col)
            rec.pop("_delta"); rec.pop("_packed"); rec.pop("_E")
            rec["kind"] = "control"
            rec["control"] = "random_anticommutative"
            emit(**rec)
        T = rand_anticomm_table(dim, 999, diagonal=[-1] * (dim - 1))
        rec = candidates(T, "random_anticomm_O_diagonal", dim, col)
        rec.pop("_delta"); rec.pop("_packed"); rec.pop("_E")
        rec["kind"] = "control"
        rec["control"] = "random_anticommutative_with_O_diagonal"
        emit(**rec)

    # ---- 3. CONDITION (i) explicit gauge sweep ---------------------------
    for dim in (4, 8, 16):
        col = delta_columns(dim)
        for gam, lbl in ((None, "definite"), ([-1] * (dim.bit_length() - 2) + [1], "split")):
            T = algebra_table(dim, gam)
            const = gauge_sweep(T, dim, col)
            emit(kind="gauge_sweep", dim=dim, label=lbl,
                 n_rescalings=1 << (dim - 1), constant=const)
        T = rand_anticomm_table(dim, 12345)
        emit(kind="gauge_sweep", dim=dim, label="random_anticomm_control",
             n_rescalings=1 << (dim - 1), constant=gauge_sweep(T, dim, col))

    # ---- 4. CONDITION (ii) explicit GL(d,F2) sweep -----------------------
    for dim in (4, 8, 16):
        d = dim.bit_length() - 1
        perms = gl_perms(d)
        col = delta_columns(dim)
        emit(kind="gl_group", d=d, order=len(perms))
        for gam, lbl in ((None, "definite"), ([-1] * (d - 1) + [1], "split")):
            T = algebra_table(dim, gam)
            const, ge = gl_sweep(T, dim, perms, col)
            emit(kind="gl_sweep", dim=dim, label=lbl, gl_order=len(perms),
                 constant=const, relabellings_gauge_equivalent=ge)
        T = rand_anticomm_table(dim, 12345)
        const, ge = gl_sweep(T, dim, perms, col)
        emit(kind="gl_sweep", dim=dim, label="random_anticomm_control",
             gl_order=len(perms), constant=const,
             relabellings_gauge_equivalent=ge)


if __name__ == "__main__":
    main()
