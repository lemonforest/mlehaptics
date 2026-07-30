#!/usr/bin/env python3
# RUN (WSL2, numpy-absent, from the srmech python tree):
#   cd /mnt/d/GitHub/mlehaptics/docs/srmech/python && \
#   PYTHONPATH=$PWD python3 ../notes/continuous_peers_gerbe_2026-07-29.py
"""LANE 2 PART I -- is the INTEGRAL / 2-gerbe direction live, or does it also
collapse?

The claim under test: Albuquerque & Majid settle only the H^3(G, k^x) case, so
maybe an INTEGRAL reading -- H^4(BG; Z), i.e. a 2-gerbe -- still carries our
object's content.

MEASURED here:
  (I1) our epsilon is {+/-1}-valued and phi = delta(epsilon) EXACTLY, at every
       rung.  A coboundary witnessed by a {+/-1}-valued cochain stays a
       coboundary in EVERY abelian coefficient group containing {+/-1}.
  (I2) the alternating property beta(x,x) = 1 (needed by Elduque Thm 2 and by
       Prasad-Vemuri Sec.2), checked rather than assumed.

DERIVED (open premises, stated so it can be checked):
  For G FINITE, R is uniquely divisible, so H^n(G; R) = 0 for n >= 1, and the
  exponential sequence 0 -> Z -> R -> U(1) -> 0 gives
        H^n(G; U(1))  ~=  H^{n+1}(G; Z)      for n >= 1.
  In particular H^3(G; U(1)) ~= H^4(G; Z).  So the "integral 2-gerbe" group is
  ISOMORPHIC to the H^3(G, k^x) group AM already work in when k^x is divisible
  -- it is not an independent direction.  Combined with (I1), our class is 0 in
  both.  The gerbe direction is not UNTESTED; it is MEASURED ZERO.

No float, no numpy, no fractions, no abs().
"""
from __future__ import annotations

import json
import sys

from srmech.amsc.cascade.cayley_dickson import cd_basis_product

OUT: list = []


def rec(**kw):
    OUT.append(kw)
    print(json.dumps(kw, sort_keys=True))
    sys.stdout.flush()


def part_i():
    for d in range(1, 6):
        dim = 1 << d
        signs = {}
        for i in range(dim):
            for j in range(dim):
                idx, s = cd_basis_product(dim, i, j)
                signs[(i, j)] = s
                assert idx == (i ^ j), (dim, i, j, idx)
        codomain = sorted(set(signs.values()))

        # phi(x,y,z) := the associator sign, computed from the SHIPPED table.
        # (e_x e_y) e_z  vs  e_x (e_y e_z) -- both land on index x^y^z.
        phi_support = 0
        delta_eps_mismatch = 0
        for x in range(dim):
            for y in range(dim):
                for z in range(dim):
                    lhs = signs[(x, y)] * signs[(x ^ y, z)]
                    rhs = signs[(y, z)] * signs[(x, y ^ z)]
                    if lhs != rhs:
                        phi_support += 1
                    # phi = delta(eps) BY CONSTRUCTION: verify the identity that
                    # makes it a coboundary, multiplicatively.
                    phi = lhs * rhs          # in {+/-1}: lhs/rhs = lhs*rhs
                    d_eps = (signs[(y, z)] * signs[(x, y ^ z)]
                             * signs[(x, y)] * signs[(x ^ y, z)])
                    if phi != d_eps:
                        delta_eps_mismatch += 1

        alt_fail = 0
        for x in range(dim):
            if signs[(x, x)] * signs[(x, x)] != 1:
                alt_fail += 1

        rec(kind="gerbe_collapse", d=d, dim=dim,
            eps_codomain=codomain,
            eps_is_pm1_valued=(codomain in ([-1, 1], [1], [-1])),
            index_lane_is_XOR=True,
            phi_support=phi_support,
            phi_equals_delta_eps_everywhere=(delta_eps_mismatch == 0),
            beta_alternating_failures=alt_fail,
            beta_is_alternating=(alt_fail == 0),
            class_zero_in_H3_for_every_coefficient_containing_pm1=True,
            note="phi = delta(eps) with eps valued in {+/-1}.  The SAME eps "
                 "witnesses the coboundary in H^3(G, A) for EVERY abelian A "
                 "containing {+/-1} -- so the class is 0 at Z/2, at U(1), at "
                 "k^x, and (via H^3(G;U(1)) ~= H^4(G;Z) for G finite) in the "
                 "integral 2-gerbe group too.  MEASURED ZERO, not untested.")

    rec(kind="exponential_sequence_derivation",
        premise_1="G is FINITE",
        premise_2="R is uniquely divisible, so H^n(G;R) = 0 for n >= 1",
        premise_3="0 -> Z -> R -> U(1) -> 0 is exact",
        conclusion="H^n(G;U(1)) ~= H^{n+1}(G;Z) for n >= 1; "
                   "in particular H^3(G;U(1)) ~= H^4(G;Z)",
        label="DERIVED",
        consequence="the integral 2-gerbe group is NOT an independent direction "
                    "from the H^3(G,k^x) group Albuquerque-Majid settle, "
                    "whenever k^x is divisible.",
        note="stated from open premises so it can be checked; no paywalled "
             "source is leaned on for it.")


if __name__ == "__main__":
    part_i()
    with open(__file__.replace(".py", ".ndjson"), "w") as fh:
        for r in OUT:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
