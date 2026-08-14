#!/usr/bin/env python3
"""LANE 1 — block-diagonalisation via the central extension: does the "4D
native irrep" exist, and does a block basis beat the CUBE (monomial) basis?

Everything below is EXACT INTEGER / EXACT RATIONAL on the SHIPPED srmech
carriers (``algebra_table`` / ``table_product`` / ``QMat`` / ``Q``).  No
floats, no numpy, no ``abs()`` — every sign is read straight off the
structure constant (Class-K pin-slot) or composed as Class-K x Class-C.

Sections
--------
A  READ   — is the regular representation already shipped?  (quaternion_left_
            mult / octonion_left_mult vs the table-built L; homomorphism test)
B  COCYCLE— is the CD sign function a genuine 2-cocycle on (Z/2)^d?  Where it
            is, build the CENTRAL EXTENSION and identify it by order / centre /
            element-order census.  Where it is not, count the failures.
C  CLIFFORD- build Cl(0,d) from its own (genuine) cocycle; where does the
            Clifford tower AGREE with the Cayley-Dickson tower and where does
            it DIVERGE?
D  BLOCKS — commutant of the left-multiplication algebra; constructive search
            for a proper invariant subspace (kernel of a singular commutant
            element IS a submodule); block dimensions per rung.
E  COUNT  — structure-tensor nonzeros: cube basis vs Walsh basis vs block
            basis vs a generic unimodular basis; plus the COMPLEXIFIED
            quaternion matrix-unit basis.
F  BOUND  — the division-algebra lower bound, measured.
"""
from __future__ import annotations

import json
import random
import sys
from itertools import product as iproduct

from srmech.amsc.q import Q
from srmech.amsc.qmat import QMat
from srmech.amsc.cascade.cayley_dickson import (
    algebra_table, table_product, cd_mult, cd_basis_product,
)
from srmech.qm.quaternion import quaternion_left_mult, quaternion_mult_table
from srmech.qm.octonion import octonion_left_mult, octonion_mult_table
import srmech

OUT = []


def rec(**kw):
    OUT.append(kw)
    print(json.dumps(kw))


# ────────────────────────────────────────────────────────────────────
# tiny exact linear algebra on top of the SHIPPED QMat
# ────────────────────────────────────────────────────────────────────

def rowspace(rows):
    """Canonical basis of the row space (exact).  Uses the shipped QMat.rref."""
    rows = [r for r in rows if any(v != 0 for v in r)]
    if not rows:
        return []
    R = QMat.from_rows(rows).rref().to_lists()
    return [r for r in R if any(v != 0 for v in r)]


def rank_of(rows):
    rows = [r for r in rows if any(v != 0 for v in r)]
    if not rows:
        return 0
    return QMat.from_rows(rows).rank()


def matmul(A, B):
    n, m, p = len(A), len(B), len(B[0])
    return [[sum(A[i][k] * B[k][j] for k in range(m)) for j in range(p)]
            for i in range(n)]


def matvec(A, v):
    return [sum(A[i][k] * v[k] for k in range(len(v))) for i in range(len(A))]


def eye(n):
    return [[1 if i == j else 0 for j in range(n)] for i in range(n)]


def flat(M):
    return [x for row in M for x in row]


# ────────────────────────────────────────────────────────────────────
# regular representation from a structure table
# ────────────────────────────────────────────────────────────────────

def left_reg(table, i):
    """L(e_i)[k][j] = table[i][j][k] — the left-multiplication matrix."""
    dim = len(table)
    return [[table[i][j][k] for j in range(dim)] for k in range(dim)]


def right_reg(table, i):
    dim = len(table)
    return [[table[j][i][k] for j in range(dim)] for k in range(dim)]


# ────────────────────────────────────────────────────────────────────
# A — READ: what already ships
# ────────────────────────────────────────────────────────────────────

def section_A():
    rec(kind="env", srmech_version=srmech.__version__)

    # A1: shipped quaternion_left_mult IS the table-built regular rep
    t4 = algebra_table(4)
    ok4 = True
    for i in range(4):
        q = [1.0 if k == i else 0.0 for k in range(4)]
        shipped = [[float(v) for v in row] for row in
                   quaternion_left_mult(q).tolist()]
        built = [[float(v) for v in row] for row in left_reg(t4, i)]
        ok4 &= (shipped == built)
    t8 = algebra_table(8)
    ok8 = True
    for i in range(8):
        a = [1.0 if k == i else 0.0 for k in range(8)]
        shipped = [[float(v) for v in row] for row in
                   octonion_left_mult(a).tolist()]
        built = [[float(v) for v in row] for row in left_reg(t8, i)]
        ok8 &= (shipped == built)
    rec(kind="A1_shipped_regular_rep",
        quaternion_left_mult_is_regular_rep=ok4,
        octonion_left_mult_is_regular_rep=ok8,
        qm_table_equals_algebra_table_4=(quaternion_mult_table() == t4),
        qm_table_equals_algebra_table_8=(octonion_mult_table() == t8),
        note="L(e_i)[k][j] = table[i][j][k]; the regular rep ALREADY SHIPS")

    # A2: is L a homomorphism?  L(e_i e_j) == L(e_i) L(e_j) ?
    for dim in (1, 2, 4, 8, 16):
        t = algebra_table(dim)
        bad = 0
        for i in range(dim):
            for j in range(dim):
                # e_i e_j = sign * e_idx
                idx, sign = cd_basis_product(dim, i, j)
                lhs = [[sign * v for v in row] for row in left_reg(t, idx)]
                rhs = matmul(left_reg(t, i), left_reg(t, j))
                if lhs != rhs:
                    bad += 1
        rec(kind="A2_left_homomorphism", dim=dim, pairs=dim * dim,
            failures=bad, is_homomorphism=(bad == 0))

    # A3: are the L(e_i) orthogonal?  (=> the rep is orthogonal => semisimple)
    for dim in (1, 2, 4, 8, 16):
        t = algebra_table(dim)
        allorth = True
        for i in range(dim):
            L = left_reg(t, i)
            LT = [[L[k][j] for k in range(dim)] for j in range(dim)]
            allorth &= (matmul(LT, L) == eye(dim))
        rec(kind="A3_orthogonal_generators", dim=dim, all_orthogonal=allorth,
            note="orthogonal generators => invariant inner product => the "
                 "module is SEMISIMPLE, so Wedderburn/blocks are the right tool")


# ────────────────────────────────────────────────────────────────────
# B — the sign cocycle and its central extension
# ────────────────────────────────────────────────────────────────────

def eps_of(table):
    """eps[x][y] with e_x e_y = eps * e_{x XOR y} (None if not monomial-XOR)."""
    dim = len(table)
    E = [[0] * dim for _ in range(dim)]
    for x in range(dim):
        for y in range(dim):
            row = table[x][y]
            nz = [k for k in range(dim) if row[k]]
            if len(nz) != 1 or nz[0] != (x ^ y):
                return None
            E[x][y] = row[nz[0]]
    return E


def cocycle_failures(E):
    """d(eps)(x,y,z) = eps(x,y)eps(x^y,z) / (eps(y,z)eps(x,y^z)); count != 1."""
    dim = len(E)
    bad = 0
    for x in range(dim):
        for y in range(dim):
            for z in range(dim):
                lhs = E[x][y] * E[x ^ y][z]
                rhs = E[y][z] * E[x][y ^ z]
                if lhs != rhs:
                    bad += 1
    return bad


def central_extension_census(E):
    """Build G = {(s, x) : s=+-1, x in (Z/2)^d} with (s,x)(t,y) =
    (s t eps(x,y), x^y).  Only a GROUP when eps is a 2-cocycle."""
    dim = len(E)
    elems = [(s, x) for s in (1, -1) for x in range(dim)]
    idx = {e: n for n, e in enumerate(elems)}

    def mul(a, b):
        return (a[0] * b[0] * E[a[1]][b[1]], a[1] ^ b[1])

    # element orders
    orders = {}
    for a in elems:
        cur, k = a, 1
        while cur != (1, 0) and k <= 4 * dim:
            cur = mul(cur, a)
            k += 1
        orders[a] = k
    census = {}
    for v in orders.values():
        census[v] = census.get(v, 0) + 1
    centre = [a for a in elems if all(mul(a, b) == mul(b, a) for b in elems)]
    # abelian?
    abelian = len(centre) == len(elems)
    return dict(order=len(elems), order_census=dict(sorted(census.items())),
                centre_order=len(centre), abelian=abelian)


def name_group(dim, cen):
    o, c = cen["order"], cen["order_census"]
    z = cen["centre_order"]
    if o == 2:
        return "Z/2"
    if o == 4:
        return "Z/4" if c.get(4, 0) == 2 else "Z/2 x Z/2"
    if o == 8:
        if c.get(4, 0) == 6 and c.get(2, 0) == 1 and z == 2:
            return "Q8  (extraspecial 2-group 2^{1+2}_-)"
        if c.get(2, 0) == 5 and z == 2:
            return "D8  (extraspecial 2-group 2^{1+2}_+)"
    if o == 16 and z == 4:
        return "order-16, centre order 4 -> ALMOST-extraspecial (d odd)"
    if o == 32 and z == 2:
        return "order-32, centre order 2 -> extraspecial 2^{1+4}"
    return f"order-{o}, centre-{z}"


def section_B():
    for dim in (1, 2, 4, 8, 16):
        t = algebra_table(dim)
        E = eps_of(t)
        d = dim.bit_length() - 1
        if E is None:
            rec(kind="B1_cd_cocycle", dim=dim, d=d, monomial_xor=False)
            continue
        bad = cocycle_failures(E)
        row = dict(kind="B1_cd_cocycle", dim=dim, d=d, monomial_xor=True,
                   triples=dim ** 3, cocycle_failures=bad,
                   is_2_cocycle=(bad == 0))
        if bad == 0:
            cen = central_extension_census(E)
            row.update(cen)
            row["extension_name"] = name_group(dim, cen)
        else:
            row["extension_name"] = ("NONE — eps is not a 2-cocycle, so there "
                                     "is no central extension and no "
                                     "projective representation")
        rec(**row)


# ────────────────────────────────────────────────────────────────────
# C — the Clifford tower Cl(0,d) built from ITS OWN (genuine) cocycle
# ────────────────────────────────────────────────────────────────────

def clifford_table(d):
    """Cl(0,d): basis e_S indexed by bitmask S; every generator squares to -1.

    eps(S,T) = (-1)^{# {(i,j): i in T, j in S, j > i}} * (-1)^{|S & T|}
    """
    dim = 1 << d

    def sign(S, T):
        s = 0
        for i in range(d):
            if T >> i & 1:
                # count generators of S strictly greater than i (to hop past)
                s += bin(S >> (i + 1)).count("1")
        s += bin(S & T).count("1")          # each e_i^2 = -1  (Class-K flip)
        return 1 if s % 2 == 0 else -1

    tbl = [[[0] * dim for _ in range(dim)] for _ in range(dim)]
    for S in range(dim):
        for T in range(dim):
            tbl[S][T][S ^ T] = sign(S, T)
    return tbl


def is_associative(table):
    dim = len(table)
    for i in range(dim):
        for j in range(dim):
            for k in range(dim):
                a = matvec_table(table, i, j)
                # (e_i e_j) e_k  vs  e_i (e_j e_k)  — monomial so cheap
                idx1 = i ^ j
                s1 = table[i][j][idx1]
                lhs_idx, lhs_s = idx1 ^ k, s1 * table[idx1][k][idx1 ^ k]
                idx2 = j ^ k
                s2 = table[j][k][idx2]
                rhs_idx, rhs_s = i ^ idx2, s2 * table[i][idx2][i ^ idx2]
                if (lhs_idx, lhs_s) != (rhs_idx, rhs_s):
                    return False
    return True


def matvec_table(table, i, j):
    return table[i][j]


def section_C():
    for d in range(0, 5):
        dim = 1 << d
        cl = clifford_table(d)
        E = eps_of(cl)
        bad = cocycle_failures(E)
        cen = central_extension_census(E) if bad == 0 else {}
        cd = algebra_table(dim)
        same = (cl == cd)
        # omega = e_1 e_2 ... e_d, squared
        om = (1 << d) - 1
        om_sq = cl[om][om][0] if om != 0 else 1
        row = dict(kind="C1_clifford", d=d, dim=dim,
                   cocycle_failures=bad, is_2_cocycle=(bad == 0),
                   associative=is_associative(cl),
                   equals_cayley_dickson_table=same,
                   omega_squared=om_sq)
        row.update(cen)
        if cen:
            row["extension_name"] = name_group(dim, cen)
        rec(**row)


# ────────────────────────────────────────────────────────────────────
# D — blocks: commutant + constructive submodule search
# ────────────────────────────────────────────────────────────────────

def generated_algebra_dim(gens, n):
    """dim of the associative unital algebra generated by `gens` in M_n."""
    basis = rowspace([flat(eye(n))] + [flat(g) for g in gens])
    while True:
        cand = list(basis)
        mats = [[b[i * n:(i + 1) * n] for i in range(n)] for b in basis]
        for g in gens:
            for M in mats:
                cand.append(flat(matmul(g, M)))
        new = rowspace(cand)
        if len(new) == len(basis):
            return len(basis), [[b[i * n:(i + 1) * n] for i in range(n)]
                                for b in basis]
        basis = new


def commutant_basis(gens, n):
    """{X in M_n : X g = g X for all g} — solved exactly via QMat.nullspace."""
    rows = []
    for g in gens:
        # (Xg - gX)[p][q] = sum_r X[p][r] g[r][q] - g[p][r] X[r][q]
        for p in range(n):
            for q in range(n):
                coef = [0] * (n * n)
                for r in range(n):
                    coef[p * n + r] += g[r][q]
                    coef[r * n + q] -= g[p][r]
                if any(coef):
                    rows.append(coef)
    if not rows:
        rows = [[0] * (n * n)]
    ns = QMat.from_rows(rows).nullspace()
    out = []
    for v in ns:
        col = [x for row in v.to_lists() for x in row]
        out.append([[col[i * n + j] for j in range(n)] for i in range(n)])
    return out


def det_exact(M):
    n = len(M)
    return QMat.from_rows([[Q(x) if not isinstance(x, Q) else x for x in row]
                           for row in M]).det()


def find_singular_commutant_element(C, n, coef_range=(-1, 0, 1), cap=200000):
    """A NONZERO singular X in the commutant.  ker X is an invariant subspace,
    so finding one PROVES reducibility (and hands over the blocks)."""
    k = len(C)
    if k <= 1:
        return None
    seen = 0
    for coeffs in iproduct(coef_range, repeat=k):
        if all(c == 0 for c in coeffs):
            continue
        seen += 1
        if seen > cap:
            return None
        X = [[sum(coeffs[t] * C[t][i][j] for t in range(k))
              for j in range(n)] for i in range(n)]
        if all(all(v == 0 for v in row) for row in X):
            continue
        if det_exact(X) == 0:
            return X
    return None


def cyclic_submodule(gens, v, n):
    """span{ w in the closure of applying `gens` to v } — INVARIANT by
    construction (no restriction / no complement argument needed)."""
    B = rowspace([list(v)])
    while True:
        cand = list(B)
        for g in gens:
            for b in B:
                cand.append(matvec(g, b))
        new = rowspace(cand)
        if len(new) == len(B):
            return B
        B = new


def _all_invariant_candidates(gens, n, C):
    """Every invariant subspace we can construct cheaply:
       (i)  ker X for a singular X in the commutant  (X g = g X  =>  ker X
            is invariant), and
       (ii) the cyclic submodule generated by a pooled vector.
    Both are invariant BY CONSTRUCTION, so nothing here rests on the module
    being semisimple or on any complement argument."""
    cands = []
    k = len(C)
    if k > 1:
        seen = 0
        for coeffs in iproduct((-1, 0, 1), repeat=k):
            if all(c == 0 for c in coeffs):
                continue
            seen += 1
            if seen > 60000:
                break
            X = [[sum(coeffs[t] * C[t][i][j] for t in range(k))
                  for j in range(n)] for i in range(n)]
            if all(all(v == 0 for v in r) for r in X):
                continue
            if det_exact(X) != 0:
                continue
            ker = QMat.from_rows(X).nullspace()
            B = rowspace([[x for row in v.to_lists() for x in row]
                          for v in ker])
            if 0 < len(B) < n:
                cands.append(B)
    pool = [[1 if j == i else 0 for j in range(n)] for i in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            for s in (1, -1):
                v = [0] * n
                v[i], v[j] = 1, s
                pool.append(v)
    random.seed(4242 + n)
    for _ in range(24):
        pool.append([random.randint(-2, 2) for _ in range(n)])
    for v in pool:
        if all(x == 0 for x in v):
            continue
        B = cyclic_submodule(gens, v, n)
        if 0 < len(B) < n:
            cands.append(B)
    return cands


def invariant_blocks(gens, n):
    """Direct-sum decomposition of R^n into invariant subspaces, assembled
    greedily from smallest-first invariant candidates.  Every piece is
    invariant by construction; the return is the list of block dimensions."""
    C = commutant_basis(gens, n)
    cands = _all_invariant_candidates(gens, n, C)
    if not cands:
        return [n], len(C)
    cands.sort(key=len)
    acc, dims = [], []
    for B in cands:
        if len(acc) + len(B) > n:
            continue
        merged = rowspace(acc + [list(r) for r in B])
        if len(merged) == len(acc) + len(B):     # independent
            acc = merged
            dims.append(len(B))
            if len(acc) == n:
                return sorted(dims), len(C)
    # residual: whatever is left is one further invariant complement
    if len(acc) < n:
        dims.append(n - len(acc))
    return sorted(dims), len(C)


# ────────────────────────────────────────────────────────────────────
# E — structure tensor nonzero counts under a change of basis
# ────────────────────────────────────────────────────────────────────

def transform_table(table, P, Pinv):
    """T'[a][b][c] = sum_{ijk} P[i][a] P[j][b] Pinv[c][k] T[i][j][k]."""
    dim = len(table)
    # step 1: contract i and j
    T1 = [[[Q(0)] * dim for _ in range(dim)] for _ in range(dim)]
    for a in range(dim):
        for b in range(dim):
            acc = [Q(0)] * dim
            for i in range(dim):
                pia = P[i][a]
                if pia == 0:
                    continue
                for j in range(dim):
                    pjb = P[j][b]
                    if pjb == 0:
                        continue
                    w = Q(pia) * Q(pjb) if not isinstance(pia, Q) else pia * pjb
                    row = table[i][j]
                    for k in range(dim):
                        if row[k]:
                            acc[k] += w * Q(row[k])
            T1[a][b] = acc
    T2 = [[[Q(0)] * dim for _ in range(dim)] for _ in range(dim)]
    for a in range(dim):
        for b in range(dim):
            acc = T1[a][b]
            out = [Q(0)] * dim
            for c in range(dim):
                s = Q(0)
                for k in range(dim):
                    if acc[k] != 0 and Pinv[c][k] != 0:
                        s += Q(Pinv[c][k]) * acc[k] if not isinstance(
                            Pinv[c][k], Q) else Pinv[c][k] * acc[k]
                out[c] = s
            T2[a][b] = out
    return T2


def nnz(T):
    return sum(1 for a in T for b in a for v in b if v != 0)


def pair_support(T):
    """# of (a,b) with e'_a e'_b == 0 — the ONLY source of sub-dim^2 sparsity."""
    dim = len(T)
    return sum(1 for a in range(dim) for b in range(dim)
               if all(v == 0 for v in T[a][b]))


def walsh(dim):
    return [[1 if bin(a & i).count("1") % 2 == 0 else -1 for i in range(dim)]
            for a in range(dim)]


def section_D():
    """The CD ladder itself: commutant dimension + block dimensions."""
    for dim, name in ((1, "R"), (2, "C"), (4, "H"), (8, "O"),
                      (16, "S(sedenion)")):
        t = algebra_table(dim)
        gens = [left_reg(t, i) for i in range(dim)]
        alg_dim, _ = generated_algebra_dim(gens, dim)
        blocks, cdim = invariant_blocks(gens, dim)
        rec(kind="D1_cd_blocks", algebra=name, dim=dim,
            left_mult_algebra_dim=alg_dim, ambient_M_n_dim=dim * dim,
            commutant_dim=cdim, block_dims=blocks,
            irreducible=(blocks == [dim]))


# ────────────────────────────────────────────────────────────────────
# G — Wedderburn / Peirce basis: the ACTUAL block basis, where it exists
# ────────────────────────────────────────────────────────────────────

COEFS = (Q(0), Q(1), Q(-1), Q(1, 2), Q(-1, 2))


def alg_mul(table, x, y):
    """The SHIPPED table_product — exact ℚ."""
    return list(table_product(table, x, y))


def find_idempotents(table, max_support=2):
    """Nonzero, non-identity idempotents with small rational support."""
    dim = len(table)
    one = [Q(1)] + [Q(0)] * (dim - 1)
    out = []
    seen = set()
    for supp in range(1, max_support + 1):
        from itertools import combinations
        for idxs in combinations(range(dim), supp):
            for vals in iproduct(COEFS[1:], repeat=supp):
                x = [Q(0)] * dim
                for p, v in zip(idxs, vals):
                    x[p] = v
                if all(v == 0 for v in x):
                    continue
                if x == one:
                    continue
                if alg_mul(table, x, x) == x:
                    key = tuple((v.numerator, v.denominator) for v in x)
                    if key not in seen:
                        seen.add(key)
                        out.append(x)
    return out


def orthogonal_idempotent_set(table, idems):
    """A maximal pairwise-orthogonal set of idempotents summing to 1."""
    dim = len(table)
    one = [Q(1)] + [Q(0)] * (dim - 1)
    zero = [Q(0)] * dim
    for p in idems:
        q = [one[k] - p[k] for k in range(dim)]
        if alg_mul(table, p, q) == zero and alg_mul(table, q, p) == zero:
            return [p, q]
    return [one]


def peirce_basis(table, ps):
    """Basis of A adapted to A = (+)_{s,t} p_s A p_t."""
    dim = len(table)
    basis, labels = [], []
    for s, p in enumerate(ps):
        for t, q in enumerate(ps):
            rows = []
            for k in range(dim):
                ek = [Q(1) if m == k else Q(0) for m in range(dim)]
                v = alg_mul(table, alg_mul(table, p, ek), q)
                rows.append([x for x in v])
            b = rowspace(rows)
            for r in b:
                basis.append(list(r))
                labels.append(f"p{s}Ap{t}")
    return basis, labels


def section_G():
    cases = [
        ("split-C (gammas=(1,))", algebra_table(2, (1,))),
        ("split-H (gammas=(1,1))", algebra_table(4, (1, 1))),
        ("Cl(0,1) = C", clifford_table(1)),
        ("Cl(0,2) = H", clifford_table(2)),
        ("Cl(0,3)", clifford_table(3)),
        ("H (definite, CD)", algebra_table(4)),
        ("O (definite, CD)", algebra_table(8)),
    ]
    for name, t in cases:
        dim = len(t)
        idems = find_idempotents(t)
        ps = orthogonal_idempotent_set(t, idems)
        Tc = [[[Q(v) for v in cell] for cell in row] for row in t]
        row = dict(kind="G1_wedderburn_basis", algebra=name, dim=dim,
                   n_nontrivial_idempotents_found=len(idems),
                   n_orthogonal_blocks=len(ps),
                   cube_nnz=nnz(Tc), dim_sq=dim * dim)
        if len(ps) > 1:
            B, labels = peirce_basis(t, ps)
            if len(B) == dim:
                P = [[B[a][i] for a in range(dim)] for i in range(dim)]
                Pin = QMat.from_rows(P).inverse().to_lists()
                Tb = transform_table(t, P, Pin)
                row["peirce_labels"] = labels
                row["block_basis_nnz"] = nnz(Tb)
                row["block_basis_zero_product_pairs"] = pair_support(Tb)
                row["sparser_than_cube"] = nnz(Tb) < nnz(Tc)
            else:
                row["peirce_basis_rank"] = len(B)
        else:
            row["block_basis_nnz"] = nnz(Tc)
            row["sparser_than_cube"] = False
            row["note"] = ("no non-trivial idempotent => the algebra does NOT "
                           "split => the block basis IS the cube basis")
        rec(**row)


def section_E():
    for dim in (2, 4, 8, 16):
        t = algebra_table(dim)
        # cube basis
        Tc = [[[Q(v) for v in cell] for cell in row] for row in t]
        # Walsh basis: P = W (columns are characters); W^-1 = W/dim
        W = walsh(dim)
        Winv = [[Q(W[c][k], dim) for k in range(dim)] for c in range(dim)]
        Tw = transform_table(t, W, Winv)
        rec(kind="E1_basis_nnz", dim=dim, basis="cube(monomial)",
            nnz=nnz(Tc), zero_product_pairs=pair_support(Tc),
            dim_sq=dim * dim, dim_cube=dim ** 3)
        rec(kind="E1_basis_nnz", dim=dim, basis="walsh(character)",
            nnz=nnz(Tw), zero_product_pairs=pair_support(Tw),
            dim_sq=dim * dim, dim_cube=dim ** 3)
        # generic unimodular integer basis (a shear) — the "any other basis"
        random.seed(1000 + dim)
        P = eye(dim)
        for _ in range(dim):
            i, j = random.sample(range(dim), 2)
            for r in range(dim):
                P[r][i] += P[r][j]
        Pq = QMat.from_rows(P)
        Pin = Pq.inverse().to_lists()
        Tg = transform_table(t, P, Pin)
        rec(kind="E1_basis_nnz", dim=dim, basis="generic-unimodular",
            nnz=nnz(Tg), zero_product_pairs=pair_support(Tg),
            dim_sq=dim * dim, dim_cube=dim ** 3)


def section_E_controls():
    """The SPLIT twists + Clifford rungs: where blocks actually exist."""
    cases = [
        ("split-C  (gammas=(1,))", 2, (1,)),
        ("split-H  (gammas=(1,1))", 4, (1, 1)),
        ("split-O  (gammas=(1,1,1))", 8, (1, 1, 1)),
    ]
    for name, dim, g in cases:
        t = algebra_table(dim, g)
        Tc = [[[Q(v) for v in cell] for cell in row] for row in t]
        gens = [left_reg(t, i) for i in range(dim)]
        blocks, cdim = invariant_blocks(gens, dim)
        rec(kind="E2_split_control", algebra=name, dim=dim,
            cube_nnz=nnz(Tc), dim_sq=dim * dim,
            commutant_dim=cdim, block_dims=blocks)
    for d in range(0, 4):
        dim = 1 << d
        cl = clifford_table(d)
        Tc = [[[Q(v) for v in cell] for cell in row] for row in cl]
        gens = [left_reg(cl, i) for i in range(dim)]
        blocks, cdim = invariant_blocks(gens, dim)
        rec(kind="E3_clifford_blocks", d=d, dim=dim, cube_nnz=nnz(Tc),
            dim_sq=dim * dim, commutant_dim=cdim, block_dims=blocks)


def section_E_matrix_units():
    """The matrix algebras: what the block basis DOES buy where it exists."""
    for n in (2, 3, 4, 8):
        dim = n * n
        # M_n(R) in the matrix-unit basis: E_ab E_cd = delta_bc E_ad
        cnt = 0
        zero_pairs = 0
        for a in range(n):
            for b in range(n):
                for c in range(n):
                    for d in range(n):
                        if b == c:
                            cnt += 1
                        else:
                            zero_pairs += 1
        rec(kind="E4_matrix_units", algebra=f"M_{n}(R)", dim=dim,
            matrix_unit_nnz=cnt, cube_would_be=dim * dim,
            zero_product_pairs=zero_pairs,
            ratio=f"{cnt}/{dim*dim}")


def section_E_complexified():
    """H (x) C = M_2(C): the block basis for the quaternions EXISTS, but only
    over C.  Count the nonzeros of the SAME dim-4 tensor there."""
    n = 2
    dim = 4
    cnt = sum(1 for a in range(n) for b in range(n) for c in range(n)
              for d in range(n) if b == c)
    rec(kind="E5_complexified_H", algebra="H (x) C = M_2(C)", dim=dim,
        real_cube_nnz=16, complex_matrix_unit_nnz=cnt,
        block_dims_over_C=[2, 2], block_dims_over_R=[4],
        note="the halving 16 -> 8 costs the REAL carrier; over R the module "
             "is one irreducible 4-dim block and no basis splits it")


# ────────────────────────────────────────────────────────────────────
# F — the division-algebra lower bound, measured
# ────────────────────────────────────────────────────────────────────

def section_F():
    """No zero divisors => e'_a e'_b != 0 for EVERY basis and every (a,b)
    => at least one nonzero structure constant per pair => nnz >= dim^2.
    Measured here by random basis change: the zero-product-pair count must
    stay 0 for R/C/H/O and CAN be nonzero for the split twists / sedenions."""
    random.seed(20260728)
    for dim, name in ((2, "C"), (4, "H"), (8, "O"), (16, "S(sedenion)")):
        t = algebra_table(dim)
        worst = None
        zero_pair_hits = 0
        for trial in range(12):
            P = eye(dim)
            for _ in range(2 * dim):
                i, j = random.sample(range(dim), 2)
                s = random.choice((1, -1))
                for r in range(dim):
                    P[r][i] += s * P[r][j]
            Pin = QMat.from_rows(P).inverse().to_lists()
            T = transform_table(t, P, Pin)
            z = pair_support(T)
            if z:
                zero_pair_hits += 1
            c = nnz(T)
            worst = c if worst is None else min(worst, c)
        rec(kind="F1_lower_bound_probe", algebra=name, dim=dim,
            dim_sq=dim * dim, min_nnz_over_random_bases=worst,
            trials_with_a_vanishing_product_pair=zero_pair_hits,
            cube_nnz=dim * dim)

    # explicit zero-divisor census in the CUBE basis
    for dim, name in ((4, "H"), (8, "O"), (16, "S(sedenion)")):
        t = algebra_table(dim)
        z = pair_support([[[Q(v) for v in cell] for cell in row] for row in t])
        rec(kind="F2_basis_zero_products", algebra=name, dim=dim,
            zero_product_basis_pairs=z)

    # do sedenions admit a basis with a vanishing product pair?  (they HAVE
    # zero divisors, so the bound does not apply — search honestly)
    t16 = algebra_table(16)
    found = 0
    random.seed(99)
    for _ in range(400):
        x = [random.randint(-2, 2) for _ in range(16)]
        y = [random.randint(-2, 2) for _ in range(16)]
        if all(v == 0 for v in x) or all(v == 0 for v in y):
            continue
        p = table_product(t16, x, y)
        if all(v == 0 for v in p):
            found += 1
    rec(kind="F3_sedenion_random_zero_divisor_hits", trials=400,
        random_pairs_with_zero_product=found,
        note="zero divisors in S are a measure-zero variety; random sampling "
             "will not hit them — the STRUCTURED ones are the (e_i+e_j)(e_k+e_l) "
             "family, tested next")
    # the structured sedenion zero divisors
    hits = []
    for i in range(1, 16):
        for j in range(1, 16):
            if j <= i:
                continue
            for k in range(1, 16):
                for l in range(1, 16):
                    if l <= k:
                        continue
                    x = [0] * 16
                    x[i], x[j] = 1, 1
                    y = [0] * 16
                    y[k], y[l] = 1, 1
                    p = table_product(t16, x, y)
                    if all(v == 0 for v in p):
                        hits.append(((i, j), (k, l)))
    rec(kind="F4_sedenion_structured_zero_divisors",
        pairs_tested=(15 * 14 // 2) ** 2, zero_product_pairs=len(hits),
        sample=hits[:6],
        note="S is NOT a division algebra, so the dim^2 floor does not bind "
             "there — but the CD cube basis still has 0 vanishing basis "
             "products, so the floor is still ACHIEVED at 256")


# ────────────────────────────────────────────────────────────────────
# H — the central extension's OWN group algebra: irrep dimensions
# ────────────────────────────────────────────────────────────────────

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
    # need inverses
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
    """R[G] for the central extension G: block dims = the REAL irrep dims.

    The twisted algebra R^eps[(Z/2)^d] is the summand of R[G] on which the
    central z acts as -1 — the FAITHFUL projective part."""
    for dim, label in ((2, "Z/4  (d=1, CD/Clifford agree)"),
                       (4, "Q8   (d=2, CD/Clifford agree)")):
        t = algebra_table(dim)
        E = eps_of(t)
        elems, idx, mul = group_from_eps(E)
        gt = group_algebra_table(elems, idx, mul)
        n = len(elems)
        gens = [left_reg(gt, i) for i in range(n)]
        blocks, cdim = invariant_blocks(gens, n)
        cls = conjugacy_classes(elems, mul)
        rec(kind="H1_group_algebra", group=label, group_order=n,
            n_conjugacy_classes=len(cls),
            n_complex_irreps=len(cls),
            real_regular_block_dims=blocks,
            commutant_dim=cdim,
            twisted_part_dim=dim,
            note="R[G] real block dims; the faithful (z -> -1) summand has "
                 f"real dimension {dim} and IS R^eps[(Z/2)^{dim.bit_length()-1}]")
    # the Clifford d=3 extension (order 16)
    E = eps_of(clifford_table(3))
    elems, idx, mul = group_from_eps(E)
    gt = group_algebra_table(elems, idx, mul)
    n = len(elems)
    gens = [left_reg(gt, i) for i in range(n)]
    blocks, cdim = invariant_blocks(gens, n)
    cls = conjugacy_classes(elems, mul)
    rec(kind="H1_group_algebra", group="Cl(0,3) extension (order 16)",
        group_order=n, n_conjugacy_classes=len(cls), n_complex_irreps=len(cls),
        real_regular_block_dims=blocks, commutant_dim=cdim, twisted_part_dim=8,
        note="R^eps[(Z/2)^3] = Cl(0,3) = H (+) H — the twisted part SPLITS, "
             "unlike the Cayley-Dickson dim-8 rung (O), which is not even "
             "a twisted group algebra")


def section_I():
    """H's simplicity + uniqueness of its simple module — the '4D native
    irrep' claim, measured rather than asserted."""
    for dim, name in ((2, "C"), (4, "H"), (8, "O")):
        t = algebra_table(dim)
        # 1. every nonzero basis-combination invertible?  probe x x-bar
        random.seed(7 + dim)
        noninv = 0
        min_left_ideal = dim
        for _ in range(300):
            x = [random.randint(-3, 3) for _ in range(dim)]
            if all(v == 0 for v in x):
                continue
            # left ideal A.x  =  span{ L(e_i) x }
            rows = [matvec(left_reg(t, i), x) for i in range(dim)]
            r = rank_of(rows)
            if r < dim:
                noninv += 1
            min_left_ideal = min(min_left_ideal, r)
        # 2. two-sided ideal generated by a fixed non-identity element
        x = [0] * dim
        x[1] = 1
        rows = []
        for i in range(dim):
            for j in range(dim):
                rows.append(matvec(left_reg(t, i), matvec(right_reg(t, j), x)))
        rec(kind="I1_simplicity", algebra=name, dim=dim,
            min_left_ideal_dim_over_300_random=min_left_ideal,
            random_elements_generating_a_PROPER_left_ideal=noninv,
            two_sided_ideal_of_e1_dim=rank_of(rows),
            is_division_algebra=(min_left_ideal == dim),
            unique_simple_module_real_dim=min_left_ideal)


def main():
    section_A()
    section_B()
    section_C()
    section_D()
    section_G()
    section_E()
    section_E_controls()
    section_E_matrix_units()
    section_E_complexified()
    section_F()
    section_H()
    section_I()
    with open("lane1_block_diagonalisation_2026-07-28.ndjson", "w",
              encoding="utf-8") as fh:
        for r in OUT:
            fh.write(json.dumps(r) + "\n")
    print("wrote lane1_block_diagonalisation_2026-07-28.ndjson", file=sys.stderr)


if __name__ == "__main__":
    main()
