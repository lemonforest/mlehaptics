"""LANE 2 — ask the RESONANCE surface directly: is the exact spectral signature
of a cascade a FOSSIL of the order its steps were applied in?

SUBJECT (shipped srmech ops only — no hand-rolled math in the measured path):
  - ``srmech.amsc.cascade.cayley_dickson.algebra_table``   (O / split-O / control tables)
  - ``srmech.amsc.cascade.cayley_dickson.left_mult_matrix`` (the cascade STEP, as a map)
  - ``srmech.amsc.cascade.cayley_dickson.table_product``    (the cascade STEP, applied)
  - ``srmech.amsc.qmat.QMat.matmul``                        (exact-Q composition of steps)
  - ``srmech.amsc.cascade.matrix_cascades.char_poly``       (the EXACT spectral signature)
  - ``srmech.amsc.harmonics.classify_chirality_harmonic``   (the shipped harmonic surface)

THE CASCADE.  An accumulator ``u`` in a dim-D algebra; each STEP is a left
multiplication ``u <- e_i . u``.  A cascade is a WORD in the step generators.
The composite linear map of the whole cascade is the matrix product of the step
matrices, and its EXACT spectral signature is the integer characteristic
polynomial.  The question: over all orderings of the SAME multiset of steps, how
many DISTINCT exact signatures appear?

  N_distinct(multiset) := |{ char_poly(composite(order)) : order in perms(multiset) }|

THE FOSSIL TEST.  A quantity is a fossil of cascade order iff BOTH
  (i)  GAUGE-INVARIANT   — unchanged under all 2^(D-1) diagonal +/-1 rebasings
       e_i -> d_i e_i (d_0 = +1, so e_0 stays the identity), which act on the
       structure constants as  s'[i][j][k] = d_i d_j d_k s[i][j][k]; and
  (ii) NOT DIM-DETERMINED — it must DIFFER between octonions and SPLIT-octonions,
       both dim 8.

Everything exact: integer / exact-Q.  No floats, no tolerances, no numpy, no
stdlib ``fractions``, no ``abs()`` (sign is Class-K pin-slot + Class-C
re-orientation).

Run:  cd docs/srmech/python && python3 ../notes/lane2_resonance_order_fossil.py
"""
from __future__ import annotations

import itertools
import sys
from typing import Dict, List, Sequence, Tuple

from srmech.amsc.cascade.cayley_dickson import (
    algebra_table,
    cd_basis,
    left_mult_matrix,
    table_product,
)
from srmech.amsc.cascade.matrix_cascades import char_poly
from srmech.amsc.harmonics import classify_chirality_harmonic, _spectral_scores
from srmech.amsc.mat import Mat
from srmech.amsc.qmat import QMat

# ── Class-K pin-slot / Class-C re-orientation (never ``abs()``) ───────────────


def pin_magnitude(v: int) -> int:
    """Class K pin-slot at zero, then Class C re-orientation to the + branch."""
    return v if v >= 0 else -v


# ── exact coercion helpers (Q -> int, with the exactness assertion) ───────────


def q_to_int(q) -> int:
    """An exact Q with denominator 1 -> its integer.  Loud otherwise."""
    if q.denominator != 1:
        raise ValueError(f"q_to_int: not an integer: {q!r}")
    return int(q.numerator)


def qmat_to_int_rows(m: "QMat") -> List[List[int]]:
    return [[q_to_int(v) for v in row] for row in m.to_lists()]


# ── control tables ───────────────────────────────────────────────────────────
# ORACLE (labelled): srmech ships NO random-anticommutative / group-algebra
# table constructor, only ``algebra_table`` (the gamma-family).  These three are
# hand-built DATA fed to the SHIPPED ``left_mult_matrix`` / ``table_product``
# ops, exactly as ``algebra_table``'s docstring contemplates ("or hand-built").
# The measured path stays shipped-op-only.


def xor_group_algebra_table(dim: int) -> List[List[List[int]]]:
    """ORDER-FREE CONTROL A.  Group algebra of (Z/2)^log2(dim): e_i.e_j = +e_{i^j}.

    SAME monomial XOR skeleton as O / split-O — only every sign is +1.  The
    algebra is commutative AND associative, so every ordering of a multiset of
    steps composes to the SAME map.  A probe that reports order-dependence here
    is broken.
    """
    t = [[[0] * dim for _ in range(dim)] for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            t[i][j][i ^ j] = 1
    return t


def cyclic_group_algebra_table(dim: int) -> List[List[List[int]]]:
    """ORDER-FREE CONTROL B.  Group algebra of Z/dim: e_i.e_j = +e_{(i+j) mod dim}.

    Commutative + associative; the step matrices are circulants, which provably
    commute.  A second, structurally different order-free control.
    """
    t = [[[0] * dim for _ in range(dim)] for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            t[i][j][(i + j) % dim] = 1
    return t


def _lcg(seed: int):
    """Deterministic reproducible integer stream (no stdlib ``random``)."""
    state = seed & 0xFFFFFFFF
    while True:
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        yield state


def random_anticommutative_table(dim: int, seed: int,
                                 random_squares: bool = False
                                 ) -> List[List[List[int]]]:
    """NEGATIVE CONTROL.  Random signs on the XOR skeleton, anticommutative.

    e_0 is the identity; for i, j >= 1 with i != j the sign is random +/-1 with
    s(j, i) = -s(i, j); squares are -1 (or random +/-1 when ``random_squares``).
    Mandatory per the negative-controls discipline — a quantity that "works" on
    a random table is measuring nothing.
    """
    rng = _lcg(seed)
    t = [[[0] * dim for _ in range(dim)] for _ in range(dim)]
    sign: Dict[Tuple[int, int], int] = {}
    for i in range(dim):
        sign[(0, i)] = 1
        sign[(i, 0)] = 1
    for i in range(1, dim):
        sign[(i, i)] = (1 if (next(rng) & 1) else -1) if random_squares else -1
    for i in range(1, dim):
        for j in range(i + 1, dim):
            s = 1 if (next(rng) & 1) else -1
            sign[(i, j)] = s
            sign[(j, i)] = -s
    for i in range(dim):
        for j in range(dim):
            t[i][j][i ^ j] = sign[(i, j)]
    return t


# ── the gauge action on a structure-constant table ───────────────────────────


def gauge_table(table: Sequence[Sequence[Sequence[int]]],
                d: Sequence[int]) -> List[List[List[int]]]:
    """Rebase e_i -> d_i e_i (d_i in {+1,-1}, d_0 = +1).

    s'[i][j][k] = d_i d_j d_k s[i][j][k].  Derivation: e'_i e'_j = d_i d_j
    sum_k s_ijk e_k = d_i d_j sum_k s_ijk d_k e'_k (d_k^2 = 1).  With d_0 = +1
    the identity is preserved: s'[0][j][k] = d_j d_k delta_jk = delta_jk.
    """
    dim = len(table)
    return [[[d[i] * d[j] * d[k] * table[i][j][k] for k in range(dim)]
             for j in range(dim)] for i in range(dim)]


def all_gauges(dim: int) -> List[Tuple[int, ...]]:
    """The 2^(dim-1) diagonal +/-1 rebasings fixing e_0."""
    return [(1,) + tail
            for tail in itertools.product((1, -1), repeat=dim - 1)]


# ── the cascade, composed two independent ways ───────────────────────────────


def step_matrices(table, dim: int) -> List["QMat"]:
    """L_i = the matrix of the STEP ``u -> e_i . u``, via the SHIPPED
    ``left_mult_matrix`` over the given structure-constant table."""
    return [QMat.from_rows(left_mult_matrix(cd_basis(dim, i), table))
            for i in range(dim)]


def composite_via_qmat(L: List["QMat"], order: Sequence[int]) -> "QMat":
    """The composite map of the cascade, as an exact-Q matrix product.

    Steps are applied LEFT-TO-RIGHT in ``order`` (step ``order[0]`` acts on the
    accumulator first), so the composite map is L_{i_k} ... L_{i_1}.
    """
    acc = L[order[-1]]
    for idx in reversed(order[:-1]):
        acc = acc.matmul(L[idx])
    return acc


def composite_via_table_product(table, dim: int,
                                order: Sequence[int]) -> List[List[int]]:
    """DIFFERENTIAL ROUTE (two-route check).  Run the cascade itself on each
    basis vector using the shipped ``table_product`` and read off the columns.
    Must agree with :func:`composite_via_qmat` byte-for-byte.
    """
    cols = []
    for c in range(dim):
        u = cd_basis(dim, c)
        for idx in order:
            u = table_product(table, cd_basis(dim, idx), u)
        cols.append([q_to_int(v) for v in u])
    return [[cols[c][r] for c in range(dim)] for r in range(dim)]


def signature(L: List["QMat"], order: Sequence[int]) -> Tuple[int, ...]:
    """The EXACT spectral signature of the cascade: the integer char-poly of its
    composite map (Faddeev-LeVerrier, shipped, C-dispatched)."""
    return tuple(char_poly(qmat_to_int_rows(composite_via_qmat(L, order))))


def distinct_signatures(L: List["QMat"],
                        multiset: Sequence[int]) -> Tuple[int, int]:
    """(#distinct exact signatures, #orderings) over the distinct permutations
    of ``multiset``."""
    orders = sorted(set(itertools.permutations(multiset)))
    sigs = {signature(L, o) for o in orders}
    return len(sigs), len(orders)


# ── the harmonic surface, asked directly ─────────────────────────────────────


def harmonic_readout(L: List["QMat"], order: Sequence[int]):
    """The SHIPPED harmonic surface applied to the cascade's composite map:
    the 1/2/3 label and the three EXACT Q symmetry scores."""
    rows = qmat_to_int_rows(composite_via_qmat(L, order))
    m = Mat.from_rows([[float(v) for v in r] for r in rows])
    label = classify_chirality_harmonic(m)
    dc, mirror, three = _spectral_scores(rows)
    return label, (dc.as_pair(), mirror.as_pair(), three.as_pair())


# ── reporting ────────────────────────────────────────────────────────────────


def profile(name: str, table, dim: int, multisets: Sequence[Sequence[int]],
            verbose: bool = True) -> Tuple[int, ...]:
    """The order-memory profile of an algebra: N_distinct per multiset."""
    L = step_matrices(table, dim)
    prof = tuple(distinct_signatures(L, ms)[0] for ms in multisets)
    if verbose:
        hist: Dict[int, int] = {}
        for v in prof:
            hist[v] = hist.get(v, 0) + 1
        print(f"  {name:<34s} N_distinct histogram {dict(sorted(hist.items()))}"
              f"  sum={sum(prof)}")
    return prof


def main() -> int:
    dim = 8
    gens = list(range(1, dim))
    ms4 = [tuple(c) for c in itertools.combinations(gens, 4)]      # 35 multisets
    ms3 = [tuple(c) for c in itertools.combinations(gens, 3)]      # 35 multisets

    O = algebra_table(dim)
    SPLIT = algebra_table(dim, gammas=[1, -1, -1])
    XORG = xor_group_algebra_table(dim)
    ZN = cyclic_group_algebra_table(dim)
    RANDS = [(f"random-anticomm seed={s}", random_anticommutative_table(dim, s))
             for s in (1, 7, 12345, 999983)]
    RANDS += [(f"random-anticomm(rand sq) seed={s}",
               random_anticommutative_table(dim, s, random_squares=True))
              for s in (3, 42)]

    print("=" * 78)
    print("STEP 0 — TWO-ROUTE CHECK: QMat composition == running the cascade")
    print("=" * 78)
    bad = 0
    for name, tbl in (("octonion", O), ("split-octonion", SPLIT),
                      ("xor-group", XORG), ("Z/8-group", ZN),
                      (RANDS[0][0], RANDS[0][1])):
        L = step_matrices(tbl, dim)
        for order in ((1, 2, 3), (3, 1, 2), (5, 6, 7, 1)):
            a = qmat_to_int_rows(composite_via_qmat(L, order))
            b = composite_via_table_product(tbl, dim, order)
            if a != b:
                bad += 1
                print(f"  MISMATCH {name} {order}")
    print(f"  routes agree on all checked (mismatches={bad})")
    if bad:
        return 1

    print()
    print("=" * 78)
    print("STEP 3 — DISCRIMINATION CHECK (run FIRST): order-free controls")
    print("  a commutative+associative algebra MUST give N_distinct == 1 always")
    print("=" * 78)
    p_xor = profile("XOR group algebra (all +1)", XORG, dim, ms4)
    p_zn = profile("Z/8 group algebra (circulant)", ZN, dim, ms4)
    probe_ok = set(p_xor) == {1} and set(p_zn) == {1}
    print(f"  order-free controls collapse to 1: {probe_ok}")

    print()
    print("  ... and a NONCOMMUTATIVE but ASSOCIATIVE algebra (quaternions,"
          " dim 4)")
    H = algebra_table(4)
    ms3_h = [tuple(c) for c in itertools.combinations(range(1, 4), 3)]
    p_h = profile("quaternions H (associative)", H, 4, ms3_h)
    print(f"     -> H profile {p_h}  (associativity kills the order memory)")

    print()
    print("=" * 78)
    print("STEP 2 — THE MEASUREMENT: N_distinct over orderings of one multiset")
    print("=" * 78)
    print(f"  k=4 steps, {len(ms4)} multisets (all 4-subsets of e1..e7),"
          f" 24 orderings each")
    p_o = profile("OCTONIONS", O, dim, ms4)
    p_s = profile("SPLIT-OCTONIONS", SPLIT, dim, ms4)
    for nm, tbl in RANDS:
        profile(nm, tbl, dim, ms4)
    print()
    print(f"  k=3 steps, {len(ms3)} multisets, 6 orderings each")
    p_o3 = profile("OCTONIONS", O, dim, ms3)
    p_s3 = profile("SPLIT-OCTONIONS", SPLIT, dim, ms3)
    for nm, tbl in RANDS[:2]:
        profile(nm, tbl, dim, ms3)

    print()
    print("=" * 78)
    print("STEP 4(ii) — NOT-DIM-DETERMINED?  octonion vs split-octonion, dim 8")
    print("=" * 78)
    print(f"  k=4: O profile == split-O profile ? {p_o == p_s}")
    print(f"       sum(O)={sum(p_o)}  sum(split-O)={sum(p_s)}")
    print(f"  k=3: O profile == split-O profile ? {p_o3 == p_s3}")
    print(f"       sum(O)={sum(p_o3)}  sum(split-O)={sum(p_s3)}")

    print()
    print("=" * 78)
    print("STEP 4(i) — GAUGE INVARIANCE: all 2^(8-1)=128 diagonal +/-1 rebasings")
    print("=" * 78)
    gauges = all_gauges(dim)
    ms_g = ms4[:6]
    for name, tbl, base in (("OCTONIONS", O, None), ("SPLIT-OCTONIONS", SPLIT, None),
                            (RANDS[0][0], RANDS[0][1], None)):
        ref = profile("(ungauged)", tbl, dim, ms_g, verbose=False)
        n_bad = 0
        first_bad = None
        for d in gauges:
            gt = gauge_table(tbl, d)
            got = profile("", gt, dim, ms_g, verbose=False)
            if got != ref:
                n_bad += 1
                if first_bad is None:
                    first_bad = (d, got, ref)
        print(f"  {name:<24s} ref={ref}  gauges checked={len(gauges)}  "
              f"DIFFERING={n_bad}")
        if first_bad is not None:
            print(f"      first differing gauge {first_bad[0]} -> {first_bad[1]}")

    print()
    print("  ... and what the gauge does to the RAW signature set (not the count)")
    L0 = step_matrices(O, dim)
    ref_sigs = {signature(L0, o) for o in itertools.permutations((1, 2, 3, 4))}
    same_set = 0
    sign_flip = 0
    other = 0
    for d in gauges:
        Lg = step_matrices(gauge_table(O, d), dim)
        got = {signature(Lg, o) for o in itertools.permutations((1, 2, 3, 4))}
        if got == ref_sigs:
            same_set += 1
        elif got == {tuple(((-1) ** k) * c for k, c in enumerate(s))
                     for s in ref_sigs}:
            sign_flip += 1
        else:
            other += 1
    print(f"    of 128 gauges: identical sig-set={same_set}  "
          f"c_k -> (-1)^k c_k={sign_flip}  neither={other}")

    print()
    print("=" * 78)
    print("STEP 1/5 — THE HARMONIC SURFACE ASKED DIRECTLY")
    print("=" * 78)
    L0 = step_matrices(O, dim)
    labels = {}
    scores = set()
    for o in itertools.permutations((1, 2, 3, 4)):
        lab, sc = harmonic_readout(L0, o)
        labels[o] = lab
        scores.add(sc)
    print(f"  classify_chirality_harmonic over 24 orderings: labels="
          f"{sorted(set(labels.values()))}  distinct exact score-triples="
          f"{len(scores)}")
    lab_ref = sorted(set(labels.values()))
    sc_ref = scores
    lab_var = 0
    sc_var = 0
    for d in gauges:
        Lg = step_matrices(gauge_table(O, d), dim)
        labs = set()
        scs = set()
        for o in itertools.permutations((1, 2, 3, 4)):
            lab, sc = harmonic_readout(Lg, o)
            labs.add(lab)
            scs.add(sc)
        if sorted(labs) != lab_ref:
            lab_var += 1
        if scs != sc_ref:
            sc_var += 1
    print(f"  under 128 gauges: label-set changed in {lab_var}/128, "
          f"exact score-set changed in {sc_var}/128")
    return 0


if __name__ == "__main__":
    sys.exit(main())
