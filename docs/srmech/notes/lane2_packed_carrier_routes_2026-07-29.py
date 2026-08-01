#!/usr/bin/env python3
"""LANE 2 — the SHIPPED packed (sign|index) byte carrier, and its differential.

The phantom-gap check that paid off: srmech ALREADY ships a per-slot carrier
that holds the sign lane in the SAME byte as the index lane —

    srmech.amsc.octonion.oct_mult   (octonion.py:139)  o = (sign<<3) | index
    srmech.amsc.octonion.oct_bind   (octonion.py:202)  the buffer form
    srmech.biology.q8.q8_mult          (q8.py:133)        o = (sign<<2) | index
    srmech.biology.q8.q8_bind          (q8.py:195)

with C peers srmech_oct_mult / srmech_oct_bind / srmech_q8_mult / srmech_q8_bind.
oct_mult's own docstring states the split exactly:

    (s_a . e_{x_a})(s_b . e_{x_b}) = (s_a ^ s_b ^ F[x_a][x_b]) . e_{x_a ^ x_b}

so the INDEX lane is pure XOR (= what hdc.bind does) and the SIGN lane is
XOR **plus a per-pair table lookup F** derived from cd_basis_product at dim 8.
That extra term IS the cocycle epsilon.

R1/R2 confirm the shipped packed carriers ARE the shipped cocycle.
R3 is the INDEPENDENT route: exact-Q cd_mult on one-hot basis vectors reaches
   the same (index, sign) through the recursive doubling, never calling the
   cocycle shortcut - the differential any general-rung packed op would need.
R4 shows the whole delta between hdc.bind and oct_mult is one bit, set on
   exactly C(8,2) = 28 of the 64 basis pairs.

Exact integers / exact Q. No float, no numpy, no abs().
"""
import json

from srmech.amsc.octonion import oct_mult
from srmech.biology.q8 import q8_mult
from srmech.amsc.cascade.cayley_dickson import cd_basis_product, cd_basis, cd_mult
from srmech.amsc.q import Q

OUT = []


def rec(**kw):
    OUT.append(kw)


agree = idx_ok = 0
for i in range(8):
    for j in range(8):
        k, s = cd_basis_product(8, i, j)
        got = oct_mult(i, j)                       # +e_i * +e_j (sign bit 0)
        want = ((0 if s == 1 else 1) << 3) | k
        agree += (got == want)
        idx_ok += ((got & 7) == (i ^ j))
rec(kind="R1_oct_mult_IS_the_cocycle", cells=64,
    agrees_with_cd_basis_product=agree, index_lane_xor=idx_ok,
    note="the shipped packed (sign<<3)|index byte carrier already carries the "
         "sign lane - a general-rung version is an EXTENSION, not a new idea")

agree = 0
for i in range(4):
    for j in range(4):
        k, s = cd_basis_product(4, i, j)
        agree += (q8_mult(i, j) == (((0 if s == 1 else 1) << 2) | k))
rec(kind="R2_q8_mult_IS_the_cocycle", cells=16, agrees=agree)

for dim in (4, 8, 16, 32, 64):
    ok = tot = 0
    step = 1 if dim <= 16 else 4
    for i in range(0, dim, step):
        for j in range(0, dim, step):
            k, s = cd_basis_product(dim, i, j)
            prod = cd_mult(cd_basis(dim, i), cd_basis(dim, j))   # exact Q route
            want = [Q(0)] * dim
            want[k] = Q(s)
            tot += 1
            ok += (list(prod) == want)
    rec(kind="R3_independent_route_exact_Q", dim=dim, checked=tot, agree=ok,
        stride=step,
        index_bits=dim.bit_length() - 1,
        packable_in_one_byte=(dim.bit_length() - 1) + 1 <= 8,
        note="cd_mult recurses the Cayley-Dickson doubling over exact-Q "
             "coefficients and never calls the cocycle shortcut - a genuinely "
             "independent route to the same (index, sign)")

d = sum(1 for i in range(8) for j in range(8) if (oct_mult(i, j) >> 3) != 0)
rec(kind="R4_delta_is_only_the_sign_bit", pairs=64, sign_bit_set=d,
    binom_8_2=28, equals_binom=(d == 28),
    note="hdc.bind gives the low 3 bits; oct_mult adds exactly the top bit, "
         "set on C(8,2) of the 64 pairs")

for r in OUT:
    print(json.dumps(r, sort_keys=True))
