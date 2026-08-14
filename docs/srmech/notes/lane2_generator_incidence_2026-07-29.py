#!/usr/bin/env python3
"""LANE 2 follow-up — PER-INDEX INCIDENCE in the failing set, and an
INDEPENDENT re-derivation of the "e_n is never touched" result through the
SHIPPED table_product composition only (no fast path).

The headline from the main sweep is that ZERO of the 1008 alternativity-failing
(``neither``) basis triples at dim 16 contain the designated new generator
``e_8`` — and the same at dim 32 for ``e_16``.  A zero is exactly the kind of
number an off-by-one in a partition helper manufactures, so it is re-derived
here by a DIFFERENT route: enumerate only the triples that DO contain ``e_n``
and classify each one through ``table_product`` end to end.

Also emits, for each rung, the incidence histogram over all 2n indices — the
DISTRIBUTION the lane's non-empty question is actually about.
"""
from __future__ import annotations

import itertools
import json
import sys

from srmech.amsc.cascade.cayley_dickson import (
    algebra_table, table_product, cd_add, cd_basis,
)

PERMS = (((0, 1, 2), +1), ((1, 2, 0), +1), ((2, 0, 1), +1),
         ((0, 2, 1), -1), ((2, 1, 0), -1), ((1, 0, 2), -1))


def emit(rec):
    sys.stdout.write(json.dumps(rec, sort_keys=True) + "\n")


def assoc_shipped(table, dim, i, j, k):
    a, b, c = cd_basis(dim, i), cd_basis(dim, j), cd_basis(dim, k)
    lhs = table_product(table, table_product(table, a, b), c)
    rhs = table_product(table, a, table_product(table, b, c))
    minus = [0] * dim
    minus[0] = -1
    v = cd_add(lhs, table_product(table, minus, rhs))
    return tuple(sorted((idx, int(val)) for idx, val in enumerate(v)
                        if val != 0))


def classify_shipped(table, dim, i, j, k):
    base = assoc_shipped(table, dim, i, j, k)
    negbase = tuple(sorted((idx, -c) for idx, c in base))
    trip = (i, j, k)
    alternating = True
    for order, par in PERMS:
        v = assoc_shipped(table, dim, trip[order[0]], trip[order[1]],
                          trip[order[2]])
        if v != (base if par > 0 else negbase):
            alternating = False
            break
    return alternating, base


def main():
    for dim in (16,):
        old = dim // 2
        t = algebra_table(dim, None)
        # ── (a) INDEPENDENT re-derivation: every triple containing e_old ──
        checked = nonalt = 0
        witnesses = []
        idxs = range(dim)
        for i, j, k in itertools.product(idxs, repeat=3):
            if old not in (i, j, k):
                continue
            checked += 1
            alt, base = classify_shipped(t, dim, i, j, k)
            if not alt:
                nonalt += 1
                if len(witnesses) < 3:
                    witnesses.append([i, j, k])
        emit({"record": "generator_incidence_independent_recheck",
              "dim": dim, "designated_generator": old,
              "route": "shipped table_product only (no monomial fast path)",
              "triples_containing_e_n": checked,
              "of_those_non_alternating": nonalt,
              "witnesses": witnesses,
              "expected_count_3n2_minus_3n_plus_1": 3 * dim * dim - 3 * dim + 1})

        # ── (b) per-index incidence over the whole failing set ──
        # fast monomial read, licensed by (a) agreeing with the main sweep
        mono = [[None] * dim for _ in range(dim)]
        for i in range(dim):
            for j in range(dim):
                nz = [(k, t[i][j][k]) for k in range(dim) if t[i][j][k]]
                mono[i][j] = nz[0]

        def af(i, j, k):
            p, s1 = mono[i][j]
            q, s2 = mono[p][k]
            r, t1 = mono[j][k]
            u, t2 = mono[i][r]
            lhs, rhs = s1 * s2, t1 * t2
            if q == u:
                d = lhs - rhs
                return () if d == 0 else ((q, d),)
            return tuple(sorted(((q, lhs), (u, -rhs))))

        inc_neither = [0] * dim
        inc_nonassoc = [0] * dim
        inc_all = [0] * dim
        n_neither = n_nonassoc = 0
        for i, j, k in itertools.product(idxs, repeat=3):
            base = af(i, j, k)
            negbase = tuple(sorted((x, -c) for x, c in base))
            trip = (i, j, k)
            alt = True
            for order, par in PERMS:
                v = af(trip[order[0]], trip[order[1]], trip[order[2]])
                if v != (base if par > 0 else negbase):
                    alt = False
                    break
            seen = set(trip)
            for s in seen:
                inc_all[s] += 1
            if base:
                n_nonassoc += 1
                for s in seen:
                    inc_nonassoc[s] += 1
            if not alt:
                n_neither += 1
                for s in seen:
                    inc_neither[s] += 1
        emit({"record": "per_index_incidence", "dim": dim,
              "designated_generator": old,
              "n_non_alternating_triples": n_neither,
              "n_non_associating_triples": n_nonassoc,
              "incidence_in_non_alternating": inc_neither,
              "incidence_in_non_associating": inc_nonassoc,
              "incidence_over_all_triples": inc_all,
              "note": "incidence[m] = # triples whose index SET contains m"})


if __name__ == "__main__":
    main()
