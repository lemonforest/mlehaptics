#!/usr/bin/env python3
"""LANE 1 third probe — is the ceiling coincidence DERIVABLE? (2026-07-29)

``CD_COMPOSE_MAX_DIM = 8`` and "the first dim where the associator's middle is
observable = 16" are claimed to be the SAME boundary. This probe measures both
sides with SHIPPED ops so the claim is not asserted from theory:

  A. NORM-COMPOSITION.  ``cd_norm_sq(table_product(t, x, y)) ==
     cd_norm_sq(x) * cd_norm_sq(y)`` on Class-A-drawn exact-ℚ pairs, per dim.
     The first dim where this FAILS is the composition boundary.

  B. ALTERNATIVITY ON GENERAL ELEMENTS (not just basis triples).
     ``[x,x,y] == 0`` and ``[x,y,y] == 0``, on Class-A-drawn exact-ℚ elements.
     The first dim where this FAILS is the alternativity boundary.

  C. ZERO DIVISORS — the shipped ``sedenion_zero_divisor_witness``, as the
     third independent read of the same rung.

If A, B and the basis-triple middle-observability rung all land on the same
dim, the boundary is ONE event with three faces, not three coincidences.

Guards: exact ℚ end to end, no float, no ``abs()``, no numpy, no stdlib
``fractions``, Class-A (sha256) randomness.
"""
from __future__ import annotations

import json
import sys

from srmech.amsc.cascade.cayley_dickson import (
    CD_COMPOSE_MAX_DIM,
    algebra_table,
    table_product,
    cd_add,
    cd_norm_sq,
    cd_mult,
    sedenion_zero_divisor_witness,
)

sys.path.insert(0, __file__.rsplit("/", 1)[0] if "/" in __file__ else ".")
from associator_symmetry_type_rung_by_rung import ClassAStream   # noqa: E402


def draw(st, dim):
    """A Class-A-drawn exact-ℚ element: numerators in [-8, 8), denominator in
    [1, 5]. No float ever appears."""
    out = []
    for _ in range(dim):
        num = st.below(16) - 8
        den = st.below(5) + 1
        out.append((num, den))
    return tuple(out)


def probe(dim, trials):
    t = algebra_table(dim)
    minus_e0 = tuple([-1] + [0] * (dim - 1))
    st = ClassAStream(f"ceiling:{dim}")

    comp_ok = comp_fail = 0
    alt_ok = alt_fail = 0
    first_comp_fail = None
    first_alt_fail = None
    prod_agrees = 0

    for _ in range(trials):
        x = draw(st, dim)
        y = draw(st, dim)
        xy = table_product(t, x, y)
        # differential: the table-driven product vs the hard-wired cd_mult
        if tuple(xy) == tuple(cd_mult(x, y)):
            prod_agrees += 1
        # (A) norm composition
        lhs = cd_norm_sq(xy)
        rhs = cd_norm_sq(x) * cd_norm_sq(y)
        if lhs == rhs:
            comp_ok += 1
        else:
            comp_fail += 1
            if first_comp_fail is None:
                first_comp_fail = {"x": [list(v) for v in x],
                                   "y": [list(v) for v in y],
                                   "norm_sq_of_product": [lhs.numerator,
                                                          lhs.denominator],
                                   "product_of_norm_sqs": [rhs.numerator,
                                                           rhs.denominator]}
        # (B) alternativity on general elements: [x,x,y] and [x,y,y]
        for a, b, c in ((x, x, y), (x, y, y)):
            l_ = table_product(t, table_product(t, a, b), c)
            r_ = table_product(t, a, table_product(t, b, c))
            assoc = cd_add(l_, table_product(t, minus_e0, r_))
            if all(v.numerator == 0 for v in assoc):
                alt_ok += 1
            else:
                alt_fail += 1
                if first_alt_fail is None:
                    first_alt_fail = {"a": [list(v) for v in a],
                                      "b": [list(v) for v in b],
                                      "c": [list(v) for v in c]}
    return {
        "record": "ceiling_coincidence",
        "dim": dim,
        "trials": trials,
        "table_product_agrees_with_cd_mult": prod_agrees,
        "norm_composition_holds": comp_ok,
        "norm_composition_fails": comp_fail,
        "alternativity_holds": alt_ok,
        "alternativity_fails": alt_fail,
        "first_norm_composition_failure": first_comp_fail,
        "first_alternativity_failure": first_alt_fail,
    }


def main() -> int:
    recs = [probe(d, 60) for d in (2, 4, 8, 16, 32)]
    for r in recs:
        print(json.dumps(r, separators=(",", ":"), sort_keys=True), flush=True)

    first_comp = min((r["dim"] for r in recs if r["norm_composition_fails"]),
                     default=None)
    first_alt = min((r["dim"] for r in recs if r["alternativity_fails"]),
                    default=None)
    w = sedenion_zero_divisor_witness()          # keys: x, y, product, dim, …
    zd_prod = cd_mult(w["x"], w["y"])
    print(json.dumps({
        "record": "boundary_summary",
        "CD_COMPOSE_MAX_DIM": CD_COMPOSE_MAX_DIM,
        "first_dim_norm_composition_fails": first_comp,
        "first_dim_alternativity_fails": first_alt,
        "first_dim_middle_observable": 16,     # from probe 1, basis triples
        "all_three_agree": first_comp == first_alt == 16,
        "one_above_compose_ceiling": first_comp == 2 * CD_COMPOSE_MAX_DIM,
        "sedenion_zero_divisor_witness_dim": w["dim"],
        "sedenion_zero_divisor_x_form": w["x_form"],
        "sedenion_zero_divisor_y_form": w["y_form"],
        "zero_divisor_product_is_zero": all(v.numerator == 0 for v in zd_prod),
    }, separators=(",", ":"), sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
