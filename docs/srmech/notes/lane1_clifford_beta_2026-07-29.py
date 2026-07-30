"""LANE 1 — the identification, measured exactly.

SUBJECT = shipped srmech ops:
  srmech.amsc.cascade.cayley_dickson.algebra_table(dim, gammas)   [rc352]
  srmech.amsc.cascade.cayley_dickson.table_product(table, x, y)   [rc352]
  srmech.qm.octonion.octonion_mult_table()                        [independent route]

ORACLE (labelled, hand-rolled ON PURPOSE) = the real Clifford algebra Cl(p,q)
built from the ordered-subset basis sign rule.  It is the OBJECT UNDER
COMPARISON, not a substitute for a shipped op.

Exact integers throughout.  No float, no numpy, no fractions, no abs()
(sign is Class-K pin-slot composition: an int in {-1,+1} multiplied, never
magnitude-stripped).
"""
import json
import sys

sys.path.insert(0, "/mnt/d/GitHub/mlehaptics/docs/srmech/python")

from srmech.amsc.cascade.cayley_dickson import algebra_table, table_product
from srmech.qm.octonion import octonion_mult_table

OUT = []


def emit(rec):
    OUT.append(rec)
    print(json.dumps(rec, sort_keys=True))


# ---------------------------------------------------------------- helpers
def eps_from_table(dim, table):
    """eps[a][b] in {-1,+1} from the SHIPPED monomial structure tensor.

    Also returns the count of cells that are NOT monomial-at-a^b, which must
    be 0 for the (Z/2)^d twisted-group-algebra reading to even be posable.
    """
    eps = [[0] * dim for _ in range(dim)]
    offband = 0
    for a in range(dim):
        for b in range(dim):
            row = table[a][b]
            for k in range(dim):
                if row[k] != 0 and k != (a ^ b):
                    offband += 1
            s = row[a ^ b]
            if s not in (-1, 1):
                offband += 1
            eps[a][b] = s
    return eps, offband


def rescalings(dim, fix_identity=True):
    """All diagonal gauge rescalings c: G -> {+-1}.

    fix_identity=True  -> c(0) = +1, 2^(dim-1) of them (the prompt's count).
    fix_identity=False -> all 2^dim.
    """
    lo = 1 if fix_identity else 0
    n_free = dim - lo
    for mask in range(1 << n_free):
        c = [1] * dim
        for i in range(n_free):
            if (mask >> i) & 1:
                c[lo + i] = -1
        yield c


def coboundary(dim, c):
    """(delta c)(a,b) = c(a)*c(b)/c(a^b); in {+-1} division IS multiplication."""
    return [[c[a] * c[b] * c[a ^ b] for b in range(dim)] for a in range(dim)]


def cl_sign(S, T):
    """LABELLED ORACLE: sign of e_S * e_T in the real Clifford algebra
    Cl(p,q) with generators ordered 1..d, using bitmask subsets.

    e_S = prod_{i in S, ascending} g_i.  Concatenating S then T and bubbling
    into ascending order costs one (-1) per inversion; each surviving repeated
    generator g_i contributes g_i^2 = sq[i].
    Returns (index, sign) with index = S ^ T.
    """
    return None  # replaced below by cl_sign_full


def cl_table(d, sq):
    """LABELLED ORACLE: full structure tensor of Cl(p,q), p+q = d,
    sq[i] in {+1,-1} is g_i^2.  Basis indexed by bitmask subsets of {0..d-1}.
    """
    dim = 1 << d
    tbl = [[[0] * dim for _ in range(dim)] for _ in range(dim)]
    for S in range(dim):
        for T in range(dim):
            sign = 1
            # bubble the T-generators leftwards past the S-generators.
            # generator j of T must cross every generator i of S with i > j.
            for j in range(d):
                if not ((T >> j) & 1):
                    continue
                crossings = 0
                for i in range(j + 1, d):
                    if (S >> i) & 1:
                        crossings += 1
                if crossings % 2 == 1:
                    sign = -sign
            # now every repeated generator is adjacent: g_i g_i = sq[i]
            for i in range(d):
                if ((S >> i) & 1) and ((T >> i) & 1):
                    sign = sign * sq[i]
            tbl[S][T][S ^ T] = sign
    return tbl


# ---------------------------------------------------------------- run
NAMES = {2: "C", 4: "H", 8: "O", 16: "S(sedenion)"}

for dim in (2, 4, 8, 16):
    d = dim.bit_length() - 1
    table = algebra_table(dim)                 # SHIPPED
    eps, offband = eps_from_table(dim, table)

    # ---- M1a monomiality + associativity (the cocycle condition) ---------
    cocycle_fail = 0
    fail_examples = []
    for a in range(dim):
        for b in range(dim):
            for c in range(dim):
                lhs = eps[a][b] * eps[a ^ b][c]
                rhs = eps[b][c] * eps[a][b ^ c]
                if lhs != rhs:
                    cocycle_fail += 1
                    if len(fail_examples) < 3:
                        fail_examples.append([a, b, c])

    # ---- M1b associativity read through the SHIPPED PRODUCT (independent) -
    prod_fail = 0
    if dim <= 8:
        def basis(k):
            return [1 if i == k else 0 for i in range(dim)]
        for a in range(dim):
            for b in range(dim):
                for c in range(dim):
                    left = table_product(table, table_product(table, basis(a), basis(b)), basis(c))
                    right = table_product(table, basis(a), table_product(table, basis(b), basis(c)))
                    if tuple(left) != tuple(right):
                        prod_fail += 1
    emit({"kind": "M1_cocycle_and_associativity", "algebra": NAMES[dim], "dim": dim,
          "monomial_offband_cells": offband,
          "cocycle_failures_of_%d_triples" % (dim ** 3): cocycle_fail,
          "eps_is_a_2_cocycle": cocycle_fail == 0,
          "shipped_table_product_associativity_failures": prod_fail if dim <= 8 else None,
          "first_failing_triples_abc": fail_examples,
          "note": "eps is a 2-COCHAIN always; a 2-COCYCLE only where associativity holds"})

    # ---- M1c generators, squares, anticommutation (via SHIPPED product) ---
    gens = [1 << k for k in range(d)]
    def bvec(k):
        return [1 if i == k else 0 for i in range(dim)]
    squares = []
    anti = []
    for k, g in enumerate(gens):
        sq = table_product(table, bvec(g), bvec(g))
        squares.append(int(sq[0]))          # coefficient of e_0
    for i in range(d):
        for j in range(i + 1, d):
            ab = table_product(table, bvec(gens[i]), bvec(gens[j]))
            ba = table_product(table, bvec(gens[j]), bvec(gens[i]))
            summ = tuple(int(x + y) for x, y in zip(ab, ba))
            anti.append({"pair": [gens[i], gens[j]],
                         "anticommutes": all(v == 0 for v in summ)})
    emit({"kind": "M1_generators", "algebra": NAMES[dim], "dim": dim,
          "generators_e_index": gens,
          "generator_squares_coeff_of_e0": squares,
          "all_squares_minus_one": all(s == -1 for s in squares),
          "generator_pairs_all_anticommute": all(r["anticommutes"] for r in anti),
          "n_generator_pairs": len(anti)})

    # ---- M1d EXACT isomorphism test against Cl(p,q), all signatures -------
    iso_rows = []
    for negs in range(d + 1):                 # q = negs negative squares
        sq = [-1] * negs + [1] * (d - negs)
        ctab = cl_table(d, sq)
        ceps = [[ctab[a][b][a ^ b] for b in range(dim)] for a in range(dim)]
        # cohomologous?  exists c with eps = ceps * delta c  (exhaustive sweep)
        found = None
        n_found = 0
        for c in rescalings(dim, fix_identity=True):
            db = coboundary(dim, c)
            ok = True
            for a in range(dim):
                for b in range(dim):
                    if eps[a][b] != ceps[a][b] * db[a][b]:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                n_found += 1
                if found is None:
                    found = list(c)
        exact_equal = all(eps[a][b] == ceps[a][b] for a in range(dim) for b in range(dim))
        iso_rows.append({"signature_Cl_p_q": [d - negs, negs],
                         "cochains_equal_on_the_nose": exact_equal,
                         "cohomologous_gauges_found": n_found,
                         "witness_gauge": found})
    emit({"kind": "M1_clifford_identification", "algebra": NAMES[dim], "dim": dim,
          "gauge_orbit_size": 1 << (dim - 1),
          "rows": iso_rows,
          "note": "cohomologous cochains <=> ISOMORPHIC twisted group algebras "
                  "(graded iso rescaling basis vectors).  Oracle = hand-rolled "
                  "Cl(p,q) ordered-subset sign rule, LABELLED."})

    # ---- M2 beta ---------------------------------------------------------
    beta = [[eps[a][b] * eps[b][a] for b in range(dim)] for a in range(dim)]
    supp_ordered = frozenset((a, b) for a in range(dim) for b in range(dim) if beta[a][b] == -1)
    supp_unordered = frozenset(frozenset((a, b)) for (a, b) in supp_ordered)

    # (c) alternating / symmetric
    diag_ok = all(beta[a][a] == 1 for a in range(dim))
    inv_ok = all(beta[a][b] * beta[b][a] == 1 for a in range(dim) for b in range(dim))
    sym_ok = all(beta[a][b] == beta[b][a] for a in range(dim) for b in range(dim))

    # THE NON-TRIVIAL ONE: is beta BIMULTIPLICATIVE (a bicharacter)?
    bichar_fail = 0
    bichar_ex = []
    for a in range(dim):
        for b in range(dim):
            for c in range(dim):
                if beta[a ^ b][c] != beta[a][c] * beta[b][c]:
                    bichar_fail += 1
                    if len(bichar_ex) < 3:
                        bichar_ex.append([a, b, c])
    radical = [a for a in range(dim) if all(beta[a][b] == 1 for b in range(dim))]
    emit({"kind": "M2c_beta_alternating_and_bicharacter", "algebra": NAMES[dim], "dim": dim,
          "beta_diag_all_plus1": diag_ok,
          "beta_is_its_own_inverse": inv_ok,
          "beta_symmetric": sym_ok,
          "beta_bimultiplicative_failures_of_%d" % (dim ** 3): bichar_fail,
          "beta_IS_a_bicharacter": bichar_fail == 0,
          "first_failing_triples_abc": bichar_ex,
          "beta_radical": radical,
          "radical_size": len(radical),
          "support_ordered_size": len(supp_ordered),
          "support_unordered_size": len(supp_unordered),
          "note": "diag/inverse/symmetry are FORCED for {+-1} coefficients "
                  "(x^2=1) and carry zero information; bimultiplicativity is NOT forced"})

    # (b) gauge invariance of beta, EXHAUSTIVE sweep
    n_gauge = 0
    n_beta_changed = 0
    residue_masks = {}
    for c in rescalings(dim, fix_identity=True):
        n_gauge += 1
        db = coboundary(dim, c)
        changed = False
        mask = 0
        bit = 0
        for a in range(dim):
            for b in range(dim):
                e2 = eps[a][b] * db[a][b]
                if e2 == -1:
                    mask |= (1 << bit)
                bit += 1
        for a in range(dim):
            for b in range(dim):
                b2 = (eps[a][b] * db[a][b]) * (eps[b][a] * db[b][a])
                if b2 != beta[a][b]:
                    changed = True
        if changed:
            n_beta_changed += 1
        residue_masks[mask] = residue_masks.get(mask, 0) + 1
    # popcount of each residue mask = coboundary distance for that gauge
    dists = set()
    for m in residue_masks:
        cnt = 0
        v = m
        while v:
            cnt += v & 1
            v >>= 1
        dists.add(cnt)
    # is beta's support EVER a residue set?
    beta_mask = 0
    bit = 0
    for a in range(dim):
        for b in range(dim):
            if beta[a][b] == -1:
                beta_mask |= (1 << bit)
            bit += 1
    emit({"kind": "M2b_gauge_sweep", "algebra": NAMES[dim], "dim": dim,
          "gauges_swept": n_gauge,
          "gauges_that_changed_beta": n_beta_changed,
          "beta_is_gauge_invariant": n_beta_changed == 0,
          "distinct_residue_SETS": len(residue_masks),
          "distinct_residue_DISTANCES": sorted(dists),
          "beta_support_is_SOME_residue_set": beta_mask in residue_masks,
          "note": "distinct distances = 1 (pre-refuted, zero information); "
                  "distinct SETS is the live number"})

    # (a) SET-WISE: residue set (identity gauge) vs beta support
    ident_res = frozenset((a, b) for a in range(dim) for b in range(dim) if eps[a][b] == -1)
    only_res = sorted(tuple(x) for x in (ident_res - supp_ordered))
    only_beta = sorted(tuple(x) for x in (supp_ordered - ident_res))
    # diagonal cells present in each
    res_diag = sorted(a for (a, b) in ident_res if a == b)
    emit({"kind": "M2a_setwise_residue_vs_beta", "algebra": NAMES[dim], "dim": dim,
          "residue_set_identity_gauge_size": len(ident_res),
          "beta_support_ordered_size": len(supp_ordered),
          "SAME_CARDINALITY": len(ident_res) == len(supp_ordered),
          "SAME_SET": ident_res == supp_ordered,
          "in_residue_not_in_beta": only_res if len(only_res) <= 40 else only_res[:40],
          "in_beta_not_in_residue": only_beta if len(only_beta) <= 40 else only_beta[:40],
          "n_only_residue": len(only_res), "n_only_beta": len(only_beta),
          "residue_diagonal_cells": res_diag,
          "beta_diagonal_cells": [a for a in range(dim) if beta[a][a] == -1],
          "note": "diagonal cells are gauge-FIXED when c(0)=+1: eps'(a,a)=eps(a,a); "
                  "beta(a,a)=+1 identically -> the two objects cannot coincide"})

    # ---- M3 does beta already ship?  commutator via the SHIPPED product ---
    if dim <= 16:
        mism = 0
        for a in range(dim):
            for b in range(dim):
                ab = table_product(table, bvec(a), bvec(b))
                ba = table_product(table, bvec(b), bvec(a))
                comm = tuple(int(x - y) for x, y in zip(ab, ba))
                nonzero = any(v != 0 for v in comm)
                if nonzero != (beta[a][b] == -1):
                    mism += 1
        emit({"kind": "M3_beta_equals_shipped_commutator_support", "algebra": NAMES[dim],
              "dim": dim, "cells": dim * dim, "mismatches": mism,
              "beta_IS_the_commutator_vanishing_predicate": mism == 0,
              "route": "table_product(algebra_table(dim), e_a, e_b) - table_product(..., e_b, e_a)"})

# independent route control: qm.octonion table vs algebra_table(8)
o1 = octonion_mult_table()
o2 = algebra_table(8)
emit({"kind": "M0_independent_route_control",
      "octonion_mult_table_equals_algebra_table_8":
          all(o1[i][j][k] == o2[i][j][k] for i in range(8) for j in range(8) for k in range(8)),
      "cells": 512})

with open("/mnt/d/GitHub/mlehaptics/docs/srmech/notes/lane1_clifford_beta_2026-07-29.ndjson", "w") as f:
    for r in OUT:
        f.write(json.dumps(r, sort_keys=True) + "\n")
print("WROTE", len(OUT), "records", file=sys.stderr)
