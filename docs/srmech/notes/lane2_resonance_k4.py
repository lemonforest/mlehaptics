"""LANE 2 phase 3 -- is the k=3 result an ARTIFACT of k=3?

At k=3, S_3 has only two cosets of A_3, so "the signature classes are the parity
classes" is nearly forced once only 2 classes appear, and order-REVERSAL
((a,b,c)->(c,b,a) = the transposition (1 3)) is necessarily ODD, so it
necessarily flips a parity class.  At k=4 both of those coincidences BREAK:
S_4 has A_4 / V_4 / cosets available, and reversal ((1 4)(2 3)) is EVEN, so if
the classes were parity classes reversal would PRESERVE them.

So k=4 is the real discriminator.  Same exact machinery, k=4, dim 8 and dim 16.
"""
import itertools
import json
import sys
import time

from srmech.amsc.cascade.cayley_dickson import algebra_table, left_mult_matrix
from srmech.amsc.cascade.matrix_cascades import char_poly
from srmech.music.harmonics import _spectral_scores

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from lane2_resonance_probe import (                                    # noqa: E402
    _int_matrix, trivial_cocycle_table, random_anticommutative_table,
    gl_maps, gl_transport, gauge_transport,
)
from srmech.amsc.cascade.cayley_dickson import table_product, cd_basis  # noqa: E402
from srmech.amsc.q import Q                                             # noqa: E402


def emit(rec):
    sys.stdout.write(json.dumps(rec, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def step_element(dim, a):
    return tuple(Q(1) if i in (0, a) else Q(0) for i in range(dim))


def run(table, dim, word):
    acc = cd_basis(dim, 0)
    for a in word:
        acc = table_product(table, step_element(dim, a), acc)
    return acc


def cp_of(acc, table):
    return tuple(char_poly(_int_matrix(left_mult_matrix(acc, table))))


def parity(word, base):
    pos = {v: i for i, v in enumerate(base)}
    idx = [pos[v] for v in word]
    inv = 0
    for i in range(len(idx)):
        for j in range(i + 1, len(idx)):
            if idx[i] > idx[j]:
                inv += 1
    return inv % 2


def analyse(table, dim, multiset):
    base = tuple(sorted(multiset))
    words = list(itertools.permutations(base))
    cps = [cp_of(run(table, dim, w), table) for w in words]
    uniq = []
    for c in cps:
        if c not in uniq:
            uniq.append(c)
    cls = [uniq.index(c) for c in cps]
    par = [parity(w, base) for w in words]
    widx = {w: i for i, w in enumerate(words)}
    class_is_parity = all((cls[i] == cls[j]) == (par[i] == par[j])
                          for i in range(len(words)) for j in range(len(words)))
    reversal_preserves = all(cls[widx[w]] == cls[widx[tuple(reversed(w))]] for w in words)
    reversal_flips = all(cls[widx[w]] != cls[widx[tuple(reversed(w))]] for w in words)
    # class sizes
    sizes = sorted(cls.count(c) for c in range(len(uniq)))
    # is the class a function of the CYCLIC rotation only?  (char_poly(XY)==char_poly(YX)
    # makes a MATRIX product cyclic-invariant; the ALGEBRA cascade need not be)
    def rot(w, k):
        return tuple(w[k:] + w[:k])
    cyclic_invariant = all(cls[widx[w]] == cls[widx[rot(w, k)]]
                           for w in words for k in range(len(base)))
    return {"n": len(uniq), "class_is_parity": class_is_parity,
            "reversal_preserves_class": reversal_preserves,
            "reversal_flips_class": reversal_flips,
            "class_sizes": sizes, "cyclic_invariant": cyclic_invariant,
            "traces": sorted({-c[1] for c in uniq})}


def main():
    t0 = time.time()
    DIM = 8
    O = algebra_table(DIM)
    SO = algebra_table(DIM, (1, -1, -1))
    TRIV = trivial_cocycle_table(DIM)
    RAND = [random_anticommutative_table(DIM, "lane2-random-anticommutative-%d" % k)
            for k in range(3)]

    G = gl_maps(3)
    quads = list(itertools.combinations(range(1, DIM), 4))

    # GL(3,F2) orbits on 4-subsets, computed (not assumed)
    seen, orbits = set(), []
    for q in quads:
        if q in seen:
            continue
        orb = {tuple(sorted(p[a] for a in q)) for p in G}
        orbits.append(sorted(orb))
        seen |= orb
    emit({"kind": "k4_orbits", "n_quads": len(quads),
          "orbit_sizes": [len(o) for o in orbits],
          "orbit_reps": [list(o[0]) for o in orbits]})

    def orbit_id(q):
        for i, o in enumerate(orbits):
            if tuple(q) in o:
                return i
        raise KeyError(q)

    for name, tbl in (("octonion", O), ("split_octonion", SO),
                      ("TRIVIAL_COCYCLE_control", TRIV),
                      ("random_anticomm_0", RAND[0]),
                      ("random_anticomm_1", RAND[1]),
                      ("random_anticomm_2", RAND[2])):
        per_orbit = {}
        for q in quads:
            r = analyse(tbl, DIM, q)
            per_orbit.setdefault(orbit_id(q), []).append(r)
        for oid, rows in sorted(per_orbit.items()):
            emit({"kind": "k4", "algebra": name, "dim": DIM, "orbit": oid,
                  "orbit_size": len(rows),
                  "n_values": sorted({r["n"] for r in rows}),
                  "constant_on_orbit": len({r["n"] for r in rows}) == 1,
                  "class_is_parity_all": all(r["class_is_parity"] for r in rows),
                  "reversal_preserves_all": all(r["reversal_preserves_class"] for r in rows),
                  "reversal_flips_all": all(r["reversal_flips_class"] for r in rows),
                  "class_sizes": sorted({tuple(r["class_sizes"]) for r in rows}),
                  "cyclic_invariant_all": all(r["cyclic_invariant"] for r in rows),
                  "traces": sorted({tuple(r["traces"]) for r in rows})})
    emit({"kind": "timing", "phase": "k4_dim8", "seconds": round(time.time() - t0, 1)})

    # ------------------------------------------------------------------ gauge at k=4
    # SCOPE: the k=3 job sweeps all 128 gauges / all 168 GL maps against ALL 35
    # index-triples.  At k=4 an ordering costs 24 cascades, so the sweeps here run
    # against one representative quad PER GL-ORBIT (every orbit covered) rather
    # than all 35 -- stated, not hidden.
    reps = [o[0] for o in orbits]
    t1 = time.time()
    gauges = [(1,) + s for s in itertools.product((1, -1), repeat=DIM - 1)]
    for name, tbl in (("octonion", O), ("split_octonion", SO)):
        base_map = {q: analyse(tbl, DIM, q)["n"] for q in reps}
        viol = 0
        for s in gauges:
            t = gauge_transport(tbl, s)
            for q in reps:
                if analyse(t, DIM, q)["n"] != base_map[q]:
                    viol += 1
        emit({"kind": "k4_i_gauge", "algebra": name, "n_gauges": len(gauges),
              "quads": [list(q) for q in reps],
              "checks": len(gauges) * len(reps), "violations": viol,
              "gauge_invariant": viol == 0, "seconds": round(time.time() - t1, 1)})

    # ------------------------------------------------------------------ GL at k=4
    t1 = time.time()
    for name, tbl in (("octonion", O), ("split_octonion", SO)):
        base_map = {q: analyse(tbl, DIM, q)["n"] for q in reps}
        viol = 0
        for p in G:
            t = gl_transport(tbl, p)
            for q in reps:
                tq = tuple(sorted(p[a] for a in q))
                if analyse(t, DIM, tq)["n"] != base_map[q]:
                    viol += 1
        emit({"kind": "k4_ii_gl", "algebra": name, "n_maps": len(G),
              "quads": [list(q) for q in reps],
              "checks": len(G) * len(reps), "violations": viol,
              "gl_invariant": viol == 0, "seconds": round(time.time() - t1, 1)})

    emit({"kind": "timing", "phase": "k4_total", "seconds": round(time.time() - t0, 1)})


if __name__ == "__main__":
    main()
