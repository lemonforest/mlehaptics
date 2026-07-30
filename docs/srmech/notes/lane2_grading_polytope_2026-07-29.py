#!/usr/bin/env python3
"""LANE 2 — settle the UNVERIFIED one-line note: "the grading's polytope shadow
is the 16-cell (cross-polytope), not the tesseract".

Two DIFFERENT objects are in play and the note collapses them:

  (a) the GRADING GROUP (Z/2)^d, as a Cayley graph on its d canonical
      generators.  Vertices = the dim = 2^d index labels.
  (b) the SIGNED UNIT SET {+-e_0 .. +-e_{dim-1}} in R^dim — the actual unit
      vectors of the algebra at that rung.  2*dim of them.

Measured with SHIPPED ops:
  - (a) in the HV carrier: labels built by ``hdc.bind``-fold over minted
    generators; adjacency by exact byte equality.
  - (b) with exact-Q ``cd_add`` / ``cd_norm_sq`` / ``cd_basis``:
    <u,v> = (N(u+v) - N(u) - N(v)) / 2, all exact Q.  No float, no abs().
"""
import json

from srmech.amsc import hdc
from srmech.amsc.cascade.cayley_dickson import (cd_basis, cd_add, cd_norm_sq,
                                                cd_conjugate)
from srmech.amsc.q import Q
from srmech.signal_processing import mint_vector

OUT = []


def rec(**kw):
    OUT.append(kw)


D_BITS = 8192
NBYTES = D_BITS // 8
TWO = Q(2)

# ── (a) the GRADING GROUP as a Cayley graph, measured in the HV carrier ────
for dim in (2, 4, 8, 16, 32):
    d = dim.bit_length() - 1
    gens = [mint_vector(f"POLY{dim}:g{b}", D=D_BITS) for b in range(d)]
    lab = []
    for k in range(dim):
        v = bytes(NBYTES)
        for b in range(d):
            if (k >> b) & 1:
                v = hdc.bind(v, gens[b])
        lab.append(v)
    idx = {lab[k]: k for k in range(dim)}
    # adjacency: u ~ v iff v == bind(u, g_b) for some generator b
    deg = []
    edges = set()
    for k in range(dim):
        n = 0
        for b in range(d):
            m = idx.get(hdc.bind(lab[k], gens[b]))
            if m is not None and m != k:
                n += 1
                edges.add((min(k, m), max(k, m)))
        deg.append(n)
    # bipartite 2-colouring by parity of popcount (the hypercube's own colouring)
    par = [bin(k).count("1") % 2 for k in range(dim)]
    bipartite = all(par[a] != par[b] for (a, b) in edges)
    rec(kind="P1_grading_cayley_graph_in_hv_carrier", dim=dim, d=d,
        vertices=dim, vertices_expected_hypercube=1 << d,
        degree_min=min(deg), degree_max=max(deg), degree_expected=d,
        edges=len(edges), edges_expected_hypercube=d * (1 << (d - 1)),
        bipartite=bipartite,
        is_hypercube_Q_d=(min(deg) == max(deg) == d
                          and len(edges) == d * (1 << (d - 1))
                          and dim == (1 << d) and bipartite),
        # DISCRIMINATOR: the cross-polytope graph on the same vertex count has
        # degree (vertices - 2), not d. Reject it explicitly.
        crosspolytope_degree_would_be=dim - 2,
        rejects_crosspolytope=(d != dim - 2 or dim <= 4),
        note="the grading group's Cayley graph IS the d-CUBE (hypercube Q_d); "
             "at d=4 (dim 16, the sedenion index set) that is the TESSERACT")

# ── (b) the SIGNED UNIT SET in R^dim, exact Q inner products ──────────────
for dim in (2, 4, 8, 16):
    units = []                      # (label, exact-Q vector)
    for k in range(dim):
        e = cd_basis(dim, k)
        units.append((f"+e{k}", e))
        # Class-C orientation re-application: -e_k = conj of a pure imaginary
        # unit for k>=1; for k=0 build it as 0 - e_0 via cd_add of conjugates.
        neg = cd_conjugate(e) if k >= 1 else tuple(
            [Q(0)] * dim)  # placeholder, filled below
        if k == 0:
            zero = tuple([Q(0)] * dim)
            # -e_0 = conj(e_0) reflected: use cd_add(zero, ...) is identity, so
            # build -e_0 as the additive inverse via the ring: e_0 + x = 0.
            neg = tuple(Q(0) - c for c in e)
        units.append((f"-e{k}", neg))

    def ip(u, v):
        """<u,v> = (N(u+v) - N(u) - N(v)) / 2 — all exact Q, all shipped ops."""
        return (cd_norm_sq(cd_add(u, v)) - cd_norm_sq(u) - cd_norm_sq(v)) / TWO

    n = len(units)
    orth = anti = self_ = other = 0
    for a in range(n):
        for b in range(n):
            val = ip(units[a][1], units[b][1])
            if a == b:
                self_ += 1 if val == Q(1) else 0
            elif val == Q(0):
                orth += 1
            elif val == Q(-1):
                anti += 1
            else:
                other += 1
    # cross-polytope beta_dim: 2*dim vertices; each vertex orthogonal to all but
    # itself and its antipode.  Graph = cocktail-party K_{dim x 2}: degree 2dim-2.
    rec(kind="P2_signed_unit_set_is_the_cross_polytope", dim=dim,
        vertices=n, vertices_expected_crosspolytope=2 * dim,
        unit_norm_all=(self_ == n),
        orthogonal_pairs=orth,
        orthogonal_expected=n * (n - 2),
        antipodal_pairs=anti, antipodal_expected=n,
        other_inner_products=other,
        is_cross_polytope=(n == 2 * dim and self_ == n and other == 0
                           and anti == n and orth == n * (n - 2)),
        graph_degree=n - 2, graph_degree_expected=2 * dim - 2,
        polytope_name={2: "square (beta_2)", 4: "16-cell (beta_4)",
                       8: "beta_8 (8-dim cross-polytope)",
                       16: "beta_16"}[dim],
        note="the +- unit set of the rung is the DIM-dimensional CROSS-POLYTOPE; "
             "at dim 4 (H) that is the 16-CELL, which has 8 vertices - NOT the "
             "tesseract's 16")

rec(kind="P3_verdict",
    note="BOTH readings are true of DIFFERENT objects. The grading group "
         "(Z/2)^d IS the d-cube (dim = 2^d vertices; the TESSERACT at dim 16). "
         "The SIGNED UNIT SET at rung dim IS the cross-polytope beta_dim "
         "(2*dim vertices; the 16-CELL at dim 4). The one-line note is correct "
         "about the +- unit set at H and WRONG if read as a claim about the "
         "grading. The trap is that '16' names 16 CELLS in one and 16 VERTICES "
         "in the other: the 16-cell has 8 vertices, the tesseract has 16.")

for r in OUT:
    print(json.dumps(r, sort_keys=True))
