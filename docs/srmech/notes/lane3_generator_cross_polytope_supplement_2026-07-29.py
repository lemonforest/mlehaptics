#!/usr/bin/env python3
"""LANE 3 supplement — WHERE the hypercube/cross-polytope duality actually is.

The main lane-3 script showed the two addressings live in R^d (label cube Q_d)
and R^(2^d) (signed-unit cross-polytope beta_(2^d)), which are never the same
space, so THOSE two are not a dual pair.  This supplement asks the sharper
question the count-coincidence was pointing at:

    Q_d has 2^d vertices and 2d facets.  Which of our objects has 2d vertices?

Answer, MEASURED: the SIGNED GENERATORS.  The d generators of the grading are
the weight-one labels e_(2^k); with signs that is 2d points, they are
orthonormal, they span a d-dimensional subspace of R^(2^d), and inside that
subspace they are exactly the vertices of beta_d — the honest dual of Q_d.

The bijection is then checked to be structure-preserving, not just a count
match: facets of beta_d are the 2^d orthants sigma in {+-1}^d; the map
g |-> (-1)^g from G = (Z/2)^d to {+-1}^d is a GROUP ISOMORPHISM, and it carries
Q_d-adjacency (Hamming 1) to beta_d ridge-sharing (one sign flipped).

Exact integers / exact Q.  No numpy, no float, no abs().
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PY = _HERE.parent / "python"
if str(_PY) not in sys.path:
    sys.path.insert(0, str(_PY))

from srmech.amsc.q import Q                                       # noqa: E402
from srmech.amsc.qmat import QMat                                 # noqa: E402
from srmech.amsc.cascade.cayley_dickson import (                  # noqa: E402
    cd_basis, cd_basis_product, cd_norm_sq,
)

OUT = []


def rec(**kw):
    OUT.append(kw)


def main() -> int:
    for d in range(1, 7):
        dim = 1 << d
        gen_labels = [1 << k for k in range(d)]        # weight-one labels

        # the 2d SIGNED generators as points of R^(2^d)
        pts = []
        for g in gen_labels:
            e = cd_basis(dim, g)                       # SHIPPED
            pts.append(e)
            pts.append(tuple(Q(0) - v for v in e))

        norms = sorted({cd_norm_sq(p).as_pair() for p in pts})     # SHIPPED
        ips = set()
        for a in range(len(pts)):
            for b in range(len(pts)):
                s = Q(0)
                for k in range(dim):
                    s = s + pts[a][k] * pts[b][k]
                ips.add(s.as_pair())

        # do they span exactly d dimensions?  exact rank on the shipped QMat.
        rank = QMat.from_rows([list(p) for p in pts]).rank()       # SHIPPED

        # do the d generators GENERATE the whole label group under the shipped
        # product?  (if not, "generator count = d" would be the wrong parameter)
        seen = {0}
        frontier = [0]
        while frontier:
            cur = frontier.pop()
            for g in gen_labels:
                nxt, _sgn = cd_basis_product(dim, cur, g)          # SHIPPED
                if nxt not in seen:
                    seen.add(nxt)
                    frontier.append(nxt)

        # STRUCTURE-PRESERVING MAP, checked cell by cell.
        # vertices(Q_d) = G ;  facets(beta_d) = {+-1}^d (the orthants).
        # phi(g) = ((-1)^g_1, ..., (-1)^g_d).  Two checks:
        #   (1) phi is a group isomorphism  (G, xor) -> ({+-1}^d, pointwise x)
        #   (2) g ~ h in Q_d (Hamming 1)  iff  phi(g), phi(h) share a ridge
        #       (differ in exactly one sign)
        def phi(g):
            return tuple(1 if ((g >> k) & 1) == 0 else -1 for k in range(d))

        iso_fail = 0
        for g in range(dim):
            for h in range(dim):
                pg, ph, pgh = phi(g), phi(h), phi(g ^ h)
                if tuple(pg[k] * ph[k] for k in range(d)) != pgh:
                    iso_fail += 1
        injective = (len({phi(g) for g in range(dim)}) == dim)

        adj_fail = 0
        for g in range(dim):
            for h in range(dim):
                cube_adj = (bin(g ^ h).count("1") == 1)
                pg, ph = phi(g), phi(h)
                ridge = (sum(1 for k in range(d) if pg[k] != ph[k]) == 1)
                if cube_adj != ridge:
                    adj_fail += 1

        rec(kind="F1_generator_cross_polytope", d=d, algebra_dim=dim,
            signed_generators=2 * d,
            distinct_norms=norms,
            distinct_pairwise_inner_products=sorted(ips),
            exact_rank_of_span=rank,
            spans_exactly_d_dimensions=(rank == d),
            generators_generate_whole_label_group=(len(seen) == dim),
            label_polytope="Q_%d" % d,
            label_vertices=dim, label_facets=2 * d,
            generator_polytope="beta_%d" % d,
            generator_vertices=2 * d, generator_facets=dim,
            same_ambient_space=True,
            group_iso_failures=iso_fail, group_iso_injective=injective,
            adjacency_vs_ridge_failures=adj_fail,
            structure_preserving_duality=(iso_fail == 0 and injective
                                          and adj_fail == 0),
            note="Q_d and beta_d are a DUAL PAIR in the same R^d; vertices(Q_d)"
                 " = facets(beta_d) = G, and the identification is the group "
                 "isomorphism g -> (-1)^g. The 2d vertices of beta_d are the "
                 "SIGNED GENERATORS, not the signed units.")

        # NEGATIVE CONTROL: the same map against the CYCLIC label group Z/2^d.
        # If the adjacency check cannot fail, it is not measuring anything.
        cyc_adj_fail = 0
        for g in range(dim):
            for h in range(dim):
                cyc_adj = ((g - h) % dim in {1, dim - 1})
                pg, ph = phi(g), phi(h)
                ridge = (sum(1 for k in range(d) if pg[k] != ph[k]) == 1)
                if cyc_adj != ridge:
                    cyc_adj_fail += 1
        rec(kind="F2_control_cyclic_labels", d=d, algebra_dim=dim,
            adjacency_vs_ridge_failures=cyc_adj_fail,
            probe_can_fail=(cyc_adj_fail > 0))

    for r in OUT:
        print(json.dumps(r, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
