#!/usr/bin/env python3
"""LANE 2 follow-up — partition the LINEARISED alternativity failures by index.

The main sweep partitioned the ``neither`` (symmetry-type) failures and found
ZERO of them touch the designated new generator ``e_n``.  The symmetry-type
classification is not a linear condition, so this repeats the partition on the
condition that IS decisive: the associator is TRILINEAR, so

    [x,y,z] + [y,x,z] == 0  on every ordered basis triple

is a COMPLETE decision procedure for left-alternativity of the whole algebra
(not a sample).  Same for right-alternativity and flexibility.  This probe
partitions those exact failure sets by index, so the ``e_n`` result is stated
about the decisive identity rather than only about the symmetry type.
"""
from __future__ import annotations

import itertools
import json
import sys

from srmech.amsc.cascade.cayley_dickson import algebra_table


def emit(rec):
    sys.stdout.write(json.dumps(rec, sort_keys=True) + "\n")
    sys.stdout.flush()


def main():
    for dim in (8, 16, 32):
        t = algebra_table(dim, None)
        gen = dim // 2
        mono = [[None] * dim for _ in range(dim)]
        for i in range(dim):
            for j in range(dim):
                mono[i][j] = [(k, t[i][j][k]) for k in range(dim)
                              if t[i][j][k]][0]

        def af(i, j, k):
            p, s1 = mono[i][j]
            q, s2 = mono[p][k]
            r, u1 = mono[j][k]
            u, u2 = mono[i][r]
            lhs, rhs = s1 * s2, u1 * u2
            if q == u:
                d = lhs - rhs
                return () if d == 0 else ((q, d),)
            return tuple(sorted(((q, lhs), (u, -rhs))))

        def add(a, b):
            acc = {}
            for x, c in a:
                acc[x] = acc.get(x, 0) + c
            for x, c in b:
                acc[x] = acc.get(x, 0) + c
            return tuple(sorted((x, c) for x, c in acc.items() if c != 0))

        for name, perm in (("left_alt", (1, 0, 2)),
                           ("right_alt", (0, 2, 1)),
                           ("flex", (2, 1, 0))):
            fails = 0
            inc = [0] * dim
            part = {"all_old": 0, "touches_gen": 0, "new_no_gen": 0,
                    "n_new_0": 0, "n_new_1": 0, "n_new_2": 0, "n_new_3": 0}
            for i, j, k in itertools.product(range(dim), repeat=3):
                trip = (i, j, k)
                if add(af(i, j, k),
                       af(trip[perm[0]], trip[perm[1]], trip[perm[2]])):
                    fails += 1
                    for s in set(trip):
                        inc[s] += 1
                    nnew = len([x for x in trip if x >= gen])
                    part["n_new_%d" % nnew] += 1
                    if nnew == 0:
                        part["all_old"] += 1
                    elif gen in trip:
                        part["touches_gen"] += 1
                    else:
                        part["new_no_gen"] += 1
            emit({"record": "linearised_partition", "dim": dim,
                  "identity": name, "designated_generator": gen,
                  "ordered_triples": dim ** 3, "failures": fails,
                  "partition": part, "incidence_by_index": inc,
                  "decision_procedure": "EXHAUSTIVE — the associator is "
                                        "trilinear, so vanishing on all basis "
                                        "triples proves the identity"})


if __name__ == "__main__":
    main()
