"""LANE 1 stage 7 — ADDED candidates (not in the brief's list) + orbit closure.

Added by this sweep, and named as added:
  A1  SUB-LOOP ORDER MULTISET -- the order of each signed basis unit +-e_i in the
      Moufang loop, and the order of the sub-loop each PAIR generates.  This is
      the closest thing to a "path" statistic available on the table.
      MISSING SURFACE: the shipped left_orbit / closure / min_generating_set
      (srmech.amsc.cascade.cayley_dickson) take (dim, idx) only -- NO table=
      parameter -- so they are hard-wired to the DEFINITE ladder and cannot be
      run on split-O at all.  The negative control the discipline mandates is
      un-runnable on the shipped op; the table-driven version below is an
      explicitly LABELLED ORACLE.
  A2  GRADED-SUBALGEBRA CENSUS -- every 2-dim subspace of the grading group spans
      a 4-dim graded subalgebra (H or its split form); every 3-dim subspace spans
      an 8-dim one.  Census by definite/split.
  A3  GL-ORBIT CLOSURE -- do the 7 split-O gauge classes form ONE GL(3,F2) orbit?
      (If yes, "split-O in any basis" is exactly those 7, so the stage-6
      bijection covers every presentation of the algebra.)

Exact integers / F2.  No float, no abs(), no numpy.
"""

import json
import sys

sys.path.append("../notes")
from fossil_sweep_lane1_gauge_gl_dim import (   # noqa: E402
    coboundary_gens, eps_from_table, gamma_family, gl_perms, pack, relabel,
)
from fossil_sweep_lane1_circularity import echelon, reduce_by  # noqa: E402
from srmech.amsc.cascade import algebra_table   # noqa: E402
from srmech.amsc.cascade.cayley_dickson import (  # noqa: E402
    closure as shipped_closure, min_generating_set as shipped_min_gen,
)


def emit(**r):
    sys.stdout.write(json.dumps(r, sort_keys=True) + "\n")
    sys.stdout.flush()


def loop_mult(E, a, b):
    """LABELLED ORACLE — signed-basis-unit product over an ARBITRARY eps."""
    return (a[0] * b[0] * (-1 if E[a[1]][b[1]] else 1), a[1] ^ b[1])


def unit_order(E, i):
    cur = (1, i)
    n = 1
    while cur != (1, 0):
        cur = loop_mult(E, cur, (1, i))
        n += 1
        assert n <= 64
    return n


def subloop_order(E, gens):
    elems = {(1, 0)} | {(1, g) for g in gens}
    changed = True
    while changed:
        changed = False
        for a in list(elems):
            for b in list(elems):
                p = loop_mult(E, a, b)
                if p not in elems:
                    elems.add(p)
                    changed = True
    return len(elems)


def sub_eps(E, sub):
    """Restrict eps to a subGROUP of the grading group (given as a sorted list of
    indices closed under XOR), re-indexed 0..len-1."""
    idx = {v: k for k, v in enumerate(sub)}
    n = len(sub)
    return [[E[sub[i]][sub[j]] for j in range(n)] for i in range(n)]


def is_definite(Es):
    """A graded sub-table is the DEFINITE rung iff every nonzero unit squares
    to -1 (Class-K pin-slot read of the diagonal; never abs())."""
    return all(Es[i][i] == 1 for i in range(1, len(Es)))


def subspaces(dim, k):
    """Every k-dim subspace of F2^d, as a sorted index list."""
    out = set()
    idxs = [i for i in range(1, dim)]
    def rec(chosen, span):
        if len(chosen) == k:
            out.add(tuple(sorted(span)))
            return
        for v in idxs:
            if v in span:
                continue
            rec(chosen + [v], span | {v ^ s for s in span})
    rec([], {0})
    return sorted(out)


def main():
    # ---- A3 orbit closure at dim 8 ---------------------------------------
    dim = 8
    ech = echelon(coboundary_gens(dim))
    perms = gl_perms(3)
    fam = gamma_family(dim)
    cls = {}
    for g, T in sorted(fam.items()):
        E = eps_from_table(T)
        cls[g] = reduce_by(ech, pack(E))
    split_classes = {c for g, c in cls.items() if any(v > 0 for v in g)}
    def_class = [c for g, c in cls.items() if all(v < 0 for v in g)][0]
    E_split = eps_from_table(algebra_table(8, [-1, -1, 1]))
    orb = {reduce_by(ech, pack(relabel(E_split, p))) for p in perms}
    E_def = eps_from_table(algebra_table(8))
    orb_def = {reduce_by(ech, pack(relabel(E_def, p))) for p in perms}
    emit(kind="orbit_closure", dim=8,
         n_split_gamma_classes=len(split_classes),
         gl_orbit_of_split_class=len(orb),
         orbit_equals_split_family=(orb == split_classes),
         gl_orbit_of_definite_class=len(orb_def),
         definite_class_is_gl_fixed=(orb_def == {def_class}),
         definite_and_split_disjoint=(orb.isdisjoint(orb_def)))

    # ---- A1 sub-loop orders + A2 subalgebra census -----------------------
    for dim in (4, 8, 16):
        d = dim.bit_length() - 1
        for gam, lbl in ((None, "definite"), ([-1] * (d - 1) + [1], "split")):
            T = algebra_table(dim, gam)
            E = eps_from_table(T)
            orders = {}
            for i in range(1, dim):
                o = unit_order(E, i)
                orders[o] = orders.get(o, 0) + 1
            pair = {}
            for i in range(1, dim):
                for j in range(i + 1, dim):
                    o = subloop_order(E, [i, j])
                    pair[o] = pair.get(o, 0) + 1
            census = {}
            for k in (2, 3):
                if k > d:
                    continue
                defn = spl = 0
                for sub in subspaces(dim, k):
                    if is_definite(sub_eps(E, list(sub))):
                        defn += 1
                    else:
                        spl += 1
                census[f"{1 << k}dim_graded_subalgebras"] = {
                    "definite": defn, "split": spl}
            emit(kind="added_candidates", dim=dim, label=lbl,
                 A1_unit_order_multiset={str(k): v for k, v in sorted(orders.items())},
                 A1_pair_subloop_order_multiset={str(k): v for k, v in sorted(pair.items())},
                 A2_subalgebra_census=census)

    # ---- the MISSING SURFACE, demonstrated --------------------------------
    try:
        shipped_closure(8, [1, 2], table=algebra_table(8, [-1, -1, 1]))
        got = "accepted a table= parameter"
    except TypeError as exc:
        got = f"TypeError: {exc}"
    emit(kind="missing_surface",
         op="srmech.amsc.cascade.cayley_dickson.closure",
         probe="closure(8, [1,2], table=<split-O table>)", result=got,
         note="closure / left_orbit / min_generating_set ride cd_basis_product "
              "directly (the DEFINITE ladder only). No table= parameter, so the "
              "mandated split-O negative control cannot be run on the shipped "
              "op. Same for min_generating_set.",
         shipped_definite_min_generating_set=shipped_min_gen(8, [1, 2, 3, 4, 5, 6, 7]))


if __name__ == "__main__":
    main()
