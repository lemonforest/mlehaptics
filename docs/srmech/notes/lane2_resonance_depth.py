"""LANE 2 phase 5 -- does the ONE-BIT order-content grow with cascade LENGTH or
with carrier DIMENSION?

Phase 1-4 measured, exactly: on octonions and split-octonions the exact spectral
signature of a k=3 / k=4 cascade takes exactly TWO values over all orderings,
and that 2-valued split is carried entirely by the accumulator's REAL PART.
If order were being recorded, longer cascades or a bigger carrier should widen
it.  Measure k = 3,4,5,6 at dim 8 and k = 3,4 at dim 16 (sedenions, where zero
divisors exist).
"""
import itertools
import json
import sys
import time

from srmech.amsc.cascade.cayley_dickson import (
    algebra_table, left_mult_matrix, table_product, cd_basis,
)
from srmech.amsc.cascade.matrix_cascades import char_poly
from srmech.amsc.q import Q

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from lane2_resonance_probe import (                                    # noqa: E402
    _int_matrix, trivial_cocycle_table, random_anticommutative_table,
)


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


def counts(table, dim, ms):
    cps, elems, traces = set(), set(), set()
    for w in itertools.permutations(ms):
        acc = run(table, dim, w)
        elems.add(tuple(q.as_pair() for q in acc))
        cp = tuple(char_poly(_int_matrix(left_mult_matrix(acc, table))))
        cps.add(cp)
        traces.add(cp[1])
    return len(elems), len(cps), len(traces)


def main():
    t0 = time.time()

    # ---------------------------------------------------------------- dim 8, k = 3..6
    DIM = 8
    algs = [("octonion", algebra_table(DIM)),
            ("split_octonion", algebra_table(DIM, (1, -1, -1))),
            ("TRIVIAL_COCYCLE_control", trivial_cocycle_table(DIM)),
            ("random_anticomm_0", random_anticommutative_table(
                DIM, "lane2-random-anticommutative-0"))]
    for k in (3, 4, 5, 6):
        msets = list(itertools.combinations(range(1, DIM), k))
        for name, tbl in algs:
            ne, nc, nt = set(), set(), set()
            for ms in msets:
                e, c, t = counts(tbl, DIM, ms)
                ne.add(e); nc.add(c); nt.add(t)
            emit({"kind": "depth", "dim": DIM, "k": k, "algebra": name,
                  "n_multisets": len(msets), "orderings": 1 if k == 0 else
                  __import__("math").factorial(k),
                  "N_element": sorted(ne), "N_charpoly": sorted(nc),
                  "N_trace_only": sorted(nt),
                  "charpoly_adds_nothing_over_trace": sorted(nc) == sorted(nt),
                  "seconds": round(time.time() - t0, 1)})

    # ---------------------------------------------------------------- dim 16, k = 3,4
    DIM = 16
    S = algebra_table(DIM)                                   # sedenions
    SS = algebra_table(DIM, (1, -1, -1, -1))                 # a split twist, same dim
    TR = trivial_cocycle_table(DIM)
    RA = random_anticommutative_table(DIM, "lane2-random-anticommutative-16")
    algs16 = [("sedenion", S), ("split_sedenion_g1", SS),
              ("TRIVIAL_COCYCLE_control", TR), ("random_anticomm", RA)]
    # GL(4,F2)-orbit sample: 10 linearly INDEPENDENT triples + 10 DEPENDENT ones
    allt = list(itertools.combinations(range(1, DIM), 3))
    dep = [m for m in allt if (m[0] ^ m[1] ^ m[2]) == 0][:10]
    ind = [m for m in allt if (m[0] ^ m[1] ^ m[2]) != 0][:10]
    for name, tbl in algs16:
        for label, sample in (("dependent", dep), ("independent", ind)):
            ne, nc, nt = set(), set(), set()
            for ms in sample:
                e, c, t = counts(tbl, DIM, ms)
                ne.add(e); nc.add(c); nt.add(t)
            emit({"kind": "depth16", "dim": DIM, "k": 3, "algebra": name,
                  "orbit": label, "sample": len(sample),
                  "N_element": sorted(ne), "N_charpoly": sorted(nc),
                  "N_trace_only": sorted(nt),
                  "charpoly_adds_nothing_over_trace": sorted(nc) == sorted(nt),
                  "seconds": round(time.time() - t0, 1)})
    for name, tbl in algs16[:3]:
        sample = [m for m in itertools.combinations(range(1, DIM), 4)][:8]
        ne, nc, nt = set(), set(), set()
        for ms in sample:
            e, c, t = counts(tbl, DIM, ms)
            ne.add(e); nc.add(c); nt.add(t)
        emit({"kind": "depth16", "dim": DIM, "k": 4, "algebra": name,
              "orbit": "mixed_sample", "sample": len(sample),
              "N_element": sorted(ne), "N_charpoly": sorted(nc),
              "N_trace_only": sorted(nt),
              "charpoly_adds_nothing_over_trace": sorted(nc) == sorted(nt),
              "seconds": round(time.time() - t0, 1)})

    emit({"kind": "timing", "phase": "depth_total", "seconds": round(time.time() - t0, 1)})


if __name__ == "__main__":
    main()
