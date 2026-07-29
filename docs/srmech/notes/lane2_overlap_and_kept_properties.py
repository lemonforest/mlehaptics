#!/usr/bin/env python3
"""LANE 2 — the overlap counting, and what is kept across the tiers.

Generating code for every load-bearing number in the Lane-2 probe
(2026-07-29).  Run from ``docs/srmech/python`` on WSL2::

    cd /mnt/d/GitHub/mlehaptics/docs/srmech/python
    python3 ../notes/lane2_overlap_and_kept_properties.py

Emits NDJSON on stdout (one record per measurement).

DISCIPLINE
----------
* Exact integers / exact ``Q`` end to end.  No float, no tolerance, no numpy,
  no ``fractions``.
* NEVER ``abs()``.  Sign re-application is the shipped Class-C
  ``reorient(value, orientation=-1)``.
* The SUBJECT is the shipped srmech surface: ``cd_mult``, ``cd_add``,
  ``cd_norm_sq(x, gammas=)``, ``algebra_table(dim, gammas)``,
  ``table_product``, ``inertia_signature``, ``left_mult_is_invertible``,
  ``sedenion_zero_divisor_witness``, ``hamming_encode`` / ``hamming_syndrome``.
* Hand-rolled code appears ONLY as a labelled CONTROL (the random
  anticommutative table, the disjoint-parity-check code) — never as the thing
  under test.

MISSING SURFACE (a finding, not something to route around): srmech ships no
dimension-general exact associator.  ``hdc.loop_associator`` is dim-8 and
``list[float]``; ``genome.genome_octonion_associator`` is octonion-fold
specific.  The associator below is therefore COMPOSED from shipped ops
(``table_product`` / ``cd_add`` / ``reorient``) rather than called.
"""
from __future__ import annotations

import json
import random
import sys
from itertools import combinations, permutations

from srmech.amsc.cascade import (
    algebra_table,
    cd_add,
    cd_mult,
    cd_norm_sq,
    hamming_encode,
    hamming_syndrome,
    inertia_signature,
    left_mult_is_invertible,
    reorient,
    sedenion_zero_divisor_witness,
    table_product,
)
from srmech.amsc.q import Q

OUT = []


def emit(**rec):
    OUT.append(rec)
    sys.stdout.write(json.dumps(rec, sort_keys=True) + "\n")
    sys.stdout.flush()


# ---------------------------------------------------------------------------
# helpers — all exact, all built on shipped ops
# ---------------------------------------------------------------------------

def neg(v):
    """Elementwise Class-C sign re-application.  NEVER ``abs()``/unary minus."""
    return tuple(reorient(x, orientation=-1) for x in v)


def assoc_tbl(tbl, a, b, c):
    """[a,b,c] = (a·b)·c − a·(b·c).

    ``tbl is None`` routes the product through the shipped ``cd_mult`` (the
    DEFINITE Cayley–Dickson ladder, native-dispatched); a table routes it
    through the shipped ``table_product`` (needed for split twists and for the
    hand-rolled control tables).  The two agree on the definite ladder — that
    equivalence is itself asserted in M0 below rather than assumed.
    """
    mul = (lambda u, v: cd_mult(u, v)) if tbl is None else (
        lambda u, v: table_product(tbl, u, v))
    left = mul(mul(a, b), c)
    right = mul(a, mul(b, c))
    return cd_add(left, neg(right))


def basis(dim, i):
    e = [0] * dim
    e[i] = 1
    return tuple(e)


def rand_elem(rng, dim, lo=-4, hi=4):
    return tuple(rng.randint(lo, hi) for _ in range(dim))


def rand_nonzero(rng, dim):
    while True:
        v = rand_elem(rng, dim)
        if any(x != 0 for x in v):
            return v


def _q(x):
    return x if isinstance(x, Q) else Q(x)


def eq(u, v):
    return tuple(_q(x) for x in u) == tuple(_q(x) for x in v)


def is_zero(v):
    return all(_q(x) == 0 for x in v)


# ---------- CONTROL constructor (hand-rolled, LABELLED) --------------------
def random_anticommutative_table(rng, dim):
    """CONTROL — a unital anticommutative table with e_i² = −1, no CD cocycle.

    Hand-rolled ON PURPOSE: this is the negative control required by
    ``[[feedback_negative_controls_for_carrier_claims_split_octonion_and_random_anticommutative]]``.
    It is never the subject of a claim.
    """
    t = [[[0] * dim for _ in range(dim)] for _ in range(dim)]
    t[0][0][0] = 1
    for j in range(1, dim):
        t[0][j][j] = 1
        t[j][0][j] = 1
        t[j][j][0] = -1
    for i in range(1, dim):
        for j in range(i + 1, dim):
            k = rng.randrange(1, dim)
            s = rng.choice((1, -1))
            t[i][j][k] = s
            t[j][i][k] = -s
    return t


DIMS = (1, 2, 4, 8, 16, 32)
ALG = {1: "R", 2: "C", 4: "H", 8: "O", 16: "S", 32: "T(32)"}


# ===========================================================================
# M1 — THE LOSS LADDER: which property dies at which rung
# ===========================================================================
def m0_route_equivalence():
    """The two product routes agree on the definite ladder — asserted, not
    assumed, because M1 uses ``cd_mult`` and M2/M3 controls use
    ``table_product``."""
    rng = random.Random(11)
    for dim in (2, 4, 8, 16):
        tbl = algebra_table(dim)
        ok = sum(1 for _ in range(120)
                 for x, y in [(rand_elem(rng, dim), rand_elem(rng, dim))]
                 if eq(cd_mult(x, y), table_product(tbl, x, y)))
        emit(m="M0_route_equivalence", dim=dim,
             cd_mult_eq_table_product=f"{ok}/120", agree=ok == 120)


def m1_loss_ladder():
    rng = random.Random(20260729)
    for dim in DIMS:
        tbl = algebra_table(dim)          # for inertia_signature only
        prod = None                        # None => shipped cd_mult route

        # --- ordering (rung instrument: trace-form inertia) ---
        ins = inertia_signature(tbl)
        orderable = not ins["has_negative_direction"]

        # --- commutativity: basis pairs + random elements ---
        comm_basis = sum(
            1 for i in range(dim) for j in range(dim)
            if eq(cd_mult(basis(dim, i), basis(dim, j)),
                  cd_mult(basis(dim, j), basis(dim, i))))
        comm_rand = sum(
            1 for _ in range(200)
            for x, y in [(rand_elem(rng, dim), rand_elem(rng, dim))]
            if eq(cd_mult(x, y), cd_mult(y, x)))

        # --- associativity: basis triples + random elements ---
        assoc_basis = sum(
            1 for i in range(dim) for j in range(dim) for k in range(dim)
            if is_zero(assoc_tbl(prod, basis(dim, i), basis(dim, j),
                                 basis(dim, k))))
        assoc_rand = sum(
            1 for _ in range(60)
            for x, y, z in [(rand_elem(rng, dim), rand_elem(rng, dim),
                             rand_elem(rng, dim))]
            if is_zero(assoc_tbl(prod, x, y, z)))

        # --- alternativity: [x,x,y] == 0 and [x,y,y] == 0 ---
        alt_basis = sum(
            1 for i in range(dim) for j in range(dim)
            if is_zero(assoc_tbl(prod, basis(dim, i), basis(dim, i),
                                 basis(dim, j)))
            and is_zero(assoc_tbl(prod, basis(dim, i), basis(dim, j),
                                  basis(dim, j))))
        alt_rand = sum(
            1 for _ in range(60)
            for x, y in [(rand_elem(rng, dim), rand_elem(rng, dim))]
            if is_zero(assoc_tbl(prod, x, x, y))
            and is_zero(assoc_tbl(prod, x, y, y)))

        # --- composition N(xy) = N(x)N(y) (SHIPPED norm, definite ladder) ---
        comp_ok = 0
        comp_first_fail = None
        for _ in range(200):
            x, y = rand_elem(rng, dim), rand_elem(rng, dim)
            lhs = cd_norm_sq(cd_mult(x, y))
            rhs = cd_norm_sq(x) * cd_norm_sq(y)
            if lhs == rhs:
                comp_ok += 1
            elif comp_first_fail is None:
                comp_first_fail = {"x": list(x), "y": list(y),
                                   "N_xy": str(lhs), "NxNy": str(rhs)}

        # --- division / reversibility ---
        div_ok = sum(1 for _ in range(120)
                     if left_mult_is_invertible(rand_nonzero(rng, dim)))

        emit(m="M1_loss_ladder", dim=dim, algebra=ALG[dim],
             ordering_orderable=orderable,
             inertia=list(ins["signature"]),
             commutative_basis_pairs=f"{comm_basis}/{dim * dim}",
             commutative=comm_basis == dim * dim and comm_rand == 200,
             associative_basis_triples=f"{assoc_basis}/{dim ** 3}",
             associative=assoc_basis == dim ** 3 and assoc_rand == 60,
             alternative_basis_pairs=f"{alt_basis}/{dim * dim}",
             alternative=alt_basis == dim * dim and alt_rand == 60,
             composition=f"{comp_ok}/200", composition_holds=comp_ok == 200,
             composition_first_counterexample=comp_first_fail,
             left_mult_invertible=f"{div_ok}/120",
             division=div_ok == 120)

    w = sedenion_zero_divisor_witness()
    emit(m="M1_zero_divisor_witness", dim=16,
         x_form=w["x_form"], y_form=w["y_form"],
         x_norm_sq=str(w["x_norm_sq"]), y_norm_sq=str(w["y_norm_sq"]),
         product_is_zero=bool(w["product_is_zero"]),
         norms_nonzero=(_q(w["x_norm_sq"]) != 0 and _q(w["y_norm_sq"]) != 0),
         note=("random sampling does NOT find this: left_mult_is_invertible "
               "is 120/120 at dim 16 because zero divisors are a measure-zero "
               "set. The wall is EXHIBITED, not sampled."))


# ===========================================================================
# M2 — COMPOSITION under the GATED norm, and the split negative control
# ===========================================================================
def m2_composition_gated():
    rng = random.Random(770099)
    for dim in (2, 4, 8, 16):
        rungs = dim.bit_length() - 1
        splits = [g for g in _pm_vectors(rungs) if any(v > 0 for v in g)]
        if dim >= 8:                      # representative: first-rung and all-rung
            splits = [splits[0], splits[-1]]
        for gammas in [None] + splits:
            tbl = algebra_table(dim, gammas)
            gated_ok = coord_ok = 0
            gated_fail = coord_fail = None
            for _ in range(200):
                x, y = rand_elem(rng, dim), rand_elem(rng, dim)
                xy = table_product(tbl, x, y)
                # GATED form (rc352) — the norm of the algebra the table names
                g_l = cd_norm_sq(xy, gammas=gammas)
                g_r = cd_norm_sq(x, gammas=gammas) * cd_norm_sq(y, gammas=gammas)
                if g_l == g_r:
                    gated_ok += 1
                elif gated_fail is None:
                    gated_fail = {"x": list(x), "y": list(y),
                                  "N_xy": str(g_l), "NxNy": str(g_r)}
                # COORDINATE form (the pre-rc352 read) — control
                c_l = cd_norm_sq(xy)
                c_r = cd_norm_sq(x) * cd_norm_sq(y)
                if c_l == c_r:
                    coord_ok += 1
                elif coord_fail is None:
                    coord_fail = {"x": list(x), "y": list(y),
                                  "N_xy": str(c_l), "NxNy": str(c_r)}
            emit(m="M2_composition", dim=dim, algebra=ALG[dim],
                 gammas=(None if gammas is None else list(gammas)),
                 split=(gammas is not None and any(v > 0 for v in gammas)),
                 gated_norm=f"{gated_ok}/200", gated_holds=gated_ok == 200,
                 gated_first_counterexample=gated_fail,
                 coordinate_norm=f"{coord_ok}/200",
                 coordinate_holds=coord_ok == 200,
                 coordinate_first_counterexample=coord_fail)

    # CONTROL: random anticommutative table
    for dim in (4, 8):
        tbl = random_anticommutative_table(rng, dim)
        ok = 0
        for _ in range(200):
            x, y = rand_elem(rng, dim), rand_elem(rng, dim)
            if cd_norm_sq(table_product(tbl, x, y)) == cd_norm_sq(x) * cd_norm_sq(y):
                ok += 1
        emit(m="M2_composition_CONTROL_random_anticommutative", dim=dim,
             composition=f"{ok}/200", composition_holds=ok == 200)


def _pm_vectors(n):
    if n == 0:
        return [()]
    out = []
    for tail in _pm_vectors(n - 1):
        out.append((-1,) + tail)
        out.append((1,) + tail)
    return out


# ===========================================================================
# M3 — THE ASSOCIATOR'S S3 SYMMETRY: does a MIDDLE become observable?
# ===========================================================================
PERMS = list(permutations((0, 1, 2)))
SGN = {(0, 1, 2): 1, (1, 2, 0): 1, (2, 0, 1): 1,
       (0, 2, 1): -1, (1, 0, 2): -1, (2, 1, 0): -1}
# which permutations KEEP the middle (index 1) fixed?
MIDDLE_FIXED = [p for p in PERMS if p[1] == 1]          # (0,1,2) and (2,1,0)
MIDDLE_MOVED = [p for p in PERMS if p[1] != 1]


def _classify(tbl, trip):
    """Return (alternating?, middle_fixed_is_sign?, middle_moved_is_sign?)."""
    base = assoc_tbl(tbl, *trip)
    alternating = True
    mf_sign = True
    mm_sign = True
    for p in PERMS:
        val = assoc_tbl(tbl, trip[p[0]], trip[p[1]], trip[p[2]])
        want = base if SGN[p] == 1 else neg(base)
        ok = eq(val, want)
        if not ok:
            alternating = False
            if p in MIDDLE_FIXED:
                mf_sign = False
            else:
                mm_sign = False
    return base, alternating, mf_sign, mm_sign


def m3_associator_symmetry():
    rng = random.Random(31337)
    # --- SUBJECT: the definite ladder, EXHAUSTIVE over imaginary basis triples
    for dim in (4, 8, 16, 32):
        trips = [tuple(basis(dim, i) for i in t)
                 for t in combinations(range(1, dim), 3)]
        if dim == 32:                       # C(31,3) = 4495; sample for cost
            trips = [trips[i] for i in
                     sorted(random.Random(5).sample(range(len(trips)), 300))]
        _run_symmetry(f"{ALG[dim]} definite [imaginary basis triples]",
                      dim, None, trips)
    # --- CONTROL: split twists (still composition algebras at dim 8)
    for dim, gammas in ((8, (1, -1, -1)), (16, (1, -1, -1, -1))):
        tbl = algebra_table(dim, gammas)
        all_t = [tuple(basis(dim, i) for i in t)
                 for t in combinations(range(1, dim), 3)]
        trips = all_t if dim == 8 else [
            all_t[i] for i in sorted(random.Random(7).sample(range(len(all_t)), 150))]
        _run_symmetry(f"split-{ALG[dim]} CONTROL gammas={list(gammas)} [basis]",
                      dim, tbl, trips)
    # --- CONTROL: random anticommutative table
    for dim in (8, 16):
        tbl = random_anticommutative_table(rng, dim)
        all_t = [tuple(basis(dim, i) for i in t)
                 for t in combinations(range(1, dim), 3)]
        trips = all_t if dim == 8 else [
            all_t[i] for i in sorted(random.Random(9).sample(range(len(all_t)), 150))]
        _run_symmetry(f"random-anticommutative CONTROL dim {dim} [basis]",
                      dim, tbl, trips)
    # --- GENERAL exact elements (not basis) on the definite ladder
    for dim in (8, 16):
        trips = [tuple(rand_elem(rng, dim) for _ in range(3))
                 for _ in range(200)]
        _run_symmetry(f"{ALG[dim]} definite [random exact elements]",
                      dim, None, trips)


def _run_symmetry(label, dim, tbl, triples):
    n = len(triples)
    n_alt = n_nonzero = n_mf = n_mm = 0
    n_nonzero_alt = 0
    example = None
    for trip in triples:
        base, alternating, mf, mm = _classify(tbl, trip)
        nz = not is_zero(base)
        if nz:
            n_nonzero += 1
            if alternating:
                n_nonzero_alt += 1
        if alternating:
            n_alt += 1
        if mf:
            n_mf += 1
        if mm:
            n_mm += 1
        if nz and not alternating and example is None:
            bac = assoc_tbl(tbl, trip[1], trip[0], trip[2])
            cba = assoc_tbl(tbl, trip[2], trip[1], trip[0])
            example = {
                "abc": [str(v) for v in base],
                "bac": [str(v) for v in bac],
                "cba": [str(v) for v in cba],
                "cba_eq_minus_abc": eq(cba, neg(base)),
                "bac_eq_minus_abc": eq(bac, neg(base)),
                "bac_eq_plus_abc": eq(bac, base),
            }
    emit(m="M3_associator_S3", label=label, dim=dim, n_triples=n,
         alternating=f"{n_alt}/{n}",
         nonzero_associator=f"{n_nonzero}/{n}",
         alternating_among_nonzero=f"{n_nonzero_alt}/{n_nonzero}",
         middle_FIXED_perms_are_sign_only=f"{n_mf}/{n}",
         middle_MOVED_perms_are_sign_only=f"{n_mm}/{n}",
         first_non_alternating_example=example)


# ===========================================================================
# M4 — THE OVERLAP LEMMA, exhaustive; and Hamming overlap vs disjoint checks
# ===========================================================================
def m4_overlap_lemma():
    """Exhaustive: with k copies over an alphabet of size q and AT MOST one
    corrupted copy, can the comparison pattern LOCATE the corrupted one?"""
    q = 4
    for k in (2, 3, 4):
        n_pairs = k - 1              # adjacent pairs in a chain
        n_overlaps = k - 2           # adjacent pairs sharing an element
        n_all_pairs = k * (k - 1) // 2
        total = locatable = 0
        # true value v; corrupted position p (or None); corrupted value w != v
        for v in range(q):
            for p in list(range(k)) + [None]:
                for w in range(q):
                    if p is not None and w == v:
                        continue
                    word = [v] * k
                    if p is not None:
                        word[p] = w
                    total += 1
                    # decoder sees ONLY the adjacent equality pattern
                    pat = tuple(word[i] == word[i + 1] for i in range(k - 1))
                    cands = _consistent_positions(pat, k)
                    if len(cands) == 1 and cands[0] == p:
                        locatable += 1
                    elif p is None and cands == [None]:
                        locatable += 1
        # ENUMERATED (not asserted): is overlap FORCED at this k?  i.e. does
        # every pair of distinct 2-subsets of [k] intersect?
        subsets = list(combinations(range(k), 2))
        disjoint = [(s, t) for s, t in combinations(subsets, 2)
                    if not (set(s) & set(t))]
        emit(m="M4_overlap_lemma", k=k, alphabet=q,
             adjacent_pairs=n_pairs, adjacent_overlaps=n_overlaps,
             all_pairs=n_all_pairs,
             n_disjoint_comparison_pairs=len(disjoint),
             overlap_is_FORCED=(len(subsets) >= 2 and not disjoint),
             two_comparisons_possible=len(subsets) >= 2,
             cases=total, located=locatable,
             locates_every_single_error=(locatable == total))


def _consistent_positions(pat, k):
    """Which single-corruption hypotheses reproduce this equality pattern?"""
    out = []
    for p in list(range(k)) + [None]:
        word = [0] * k
        if p is not None:
            word[p] = 1
        if tuple(word[i] == word[i + 1] for i in range(k - 1)) == pat:
            out.append(p)
    return out


def m5_chain_vs_majority():
    """Does the k=3 CHAIN decoder (2 adjacent comparisons, one overlap — the
    'distinguished middle' framing) agree with the canon's k=3 MAJORITY
    decoder (§3.32.1 / F266, 2-of-3, no middle)?  And is the chain's answer
    INVARIANT under which of the 3 orderings you pick as the chain?

    This is the k=2/k=3 analogue of the M3 associator question: the middle is
    real in the CONSTRUCTION; is it visible in the RESULT?
    """
    q = 4
    k = 3
    agree = total = 0
    order_invariant = 0
    for v in range(q):
        for p in list(range(k)) + [None]:
            for w in range(q):
                if p is not None and w == v:
                    continue
                word = [v] * k
                if p is not None:
                    word[p] = w
                total += 1
                # canon decoder: 2-of-3 majority (order-free)
                maj = max(set(word), key=word.count)
                # chain decoder under EACH of the 3 orderings (3 middles)
                chain_answers = set()
                for perm in permutations(range(k)):
                    if perm[0] > perm[2]:
                        continue          # a chain and its reversal coincide
                    ordered = [word[i] for i in perm]
                    pat = tuple(ordered[i] == ordered[i + 1] for i in range(2))
                    cands = _consistent_positions(pat, 3)
                    bad = cands[0] if len(cands) == 1 else None
                    rest = [ordered[i] for i in range(3)
                            if bad is None or i != bad]
                    chain_answers.add(rest[0])
                if len(chain_answers) == 1:
                    order_invariant += 1
                if chain_answers == {maj}:
                    agree += 1
    emit(m="M5_chain_vs_majority", k=k, alphabet=q, cases=total,
         chain_agrees_with_majority=f"{agree}/{total}",
         chain_answer_independent_of_which_ordering=f"{order_invariant}/{total}",
         middle_visible_in_result=(order_invariant != total),
         note=("the chain construction picks a MIDDLE; if the recovered value "
               "is the same for all 3 orderings the middle is not observable "
               "in the RESULT — the same path-vs-object split M3 measures."))


def m4_hamming_overlap():
    """SHIPPED Hamming (overlapping checks) vs a hand-rolled DISJOINT-check
    control, at the same (n, r).  Metric = number of DISTINCT single-error
    syndromes = how finely the code can LOCATE."""
    n, r = 7, 3          # Hamming(7,4): 7 positions, 3 parity checks
    data = [1, 0, 1, 1]
    cw = hamming_encode(data, r)   # shipped arg is the EXPONENT r (n = 2^r - 1)
    syn = {}
    for i in range(n):
        bad = list(cw)
        bad[i] ^= 1
        syn[i] = hamming_syndrome(bad)
    emit(m="M4_hamming_shipped_overlapping", n=n, r=r,
         codeword=list(cw), clean_syndrome=hamming_syndrome(cw),
         single_error_syndromes={str(i): s for i, s in syn.items()},
         distinct_syndromes=len(set(syn.values())),
         locates_all_positions=(len(set(syn.values())) == n
                                and 0 not in set(syn.values())))

    # CONTROL (hand-rolled): r DISJOINT parity checks partitioning n positions
    blocks = [[0, 1, 2], [3, 4], [5, 6]]
    dsyn = {}
    for i in range(n):
        s = 0
        for b, blk in enumerate(blocks):
            if i in blk:
                s |= (1 << b)
        dsyn[i] = s
    emit(m="M4_hamming_CONTROL_disjoint_checks", n=n, r=r,
         blocks=blocks,
         single_error_syndromes={str(i): s for i, s in dsyn.items()},
         distinct_syndromes=len(set(dsyn.values())),
         locates_all_positions=(len(set(dsyn.values())) == n))

    # CONTROL: the TRIVIAL regime — r == n disjoint checks DO locate.
    n2 = 2
    tsyn = {0: 1, 1: 2}
    emit(m="M4_hamming_CONTROL_disjoint_r_equals_n", n=n2, r=n2,
         single_error_syndromes={str(k): v for k, v in tsyn.items()},
         distinct_syndromes=len(set(tsyn.values())),
         locates_all_positions=True,
         note="overlap is NOT necessary for localisation when r >= n; "
              "it is necessary only in the efficient regime r < n")


STAGES = {"m0": m0_route_equivalence, "m1": m1_loss_ladder,
          "m2": m2_composition_gated, "m3": m3_associator_symmetry,
          "m4": m4_overlap_lemma, "m4h": m4_hamming_overlap,
          "m5": m5_chain_vs_majority}

if __name__ == "__main__":
    want = sys.argv[1:] or list(STAGES)
    for name in want:
        STAGES[name]()
