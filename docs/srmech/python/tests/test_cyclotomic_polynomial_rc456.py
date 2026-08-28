"""rc456 — ``srmech.math.poly.cyclotomic_polynomial`` (Φ_n, exact ints).

Three things, each a VALUE and not a shape:

1. literal coefficient tuples for n = 1..12 (hand list);
2. degree == φ(n), with φ computed INDEPENDENTLY from ``primes.factor``;
3. the ring identity ∏_{d|n} Φ_d == x^n − 1 by exact integer polynomial
   multiplication;
4. the exact_dft CROSS-PIN: the only other general-Φ_N derivation in the
   tree is the PRIVATE ``srmech.cascade.exact_dft._cyclotomic_reduction``.
   rc456 deliberately did NOT refactor it onto the public op (the
   adjudicated fallback of the plan's 3.10): the refactored call would sit
   within depth-2 helper reach of registered riemann_theta callers, moving
   FOREIGN rows' composes-adjudication tiers (the LEAF equality is a
   depth-3 AST walk) — exactly the "unexpected coupling" the fallback
   clause names.  The pin below is what prevents drift instead: the two
   derivations are asserted EQUAL for n ∈ 1..30, so neither can move
   without this file going red.

No sympy; no floats; exact integers only.
"""
from __future__ import annotations

import pytest

from srmech.cascade.exact_dft import _cyclotomic_reduction
from srmech.math.groups import _zeta_power_table
from srmech.math.poly import cyclotomic_polynomial
from srmech.math.primes import factor

#: Hand list, low→high monic (Φ_1 = x−1, Φ_2 = x+1, Φ_4 = x²+1,
#: Φ_6 = x²−x+1, Φ_12 = x⁴−x²+1, …).
LITERALS = {
    1: (-1, 1),
    2: (1, 1),
    3: (1, 1, 1),
    4: (1, 0, 1),
    5: (1, 1, 1, 1, 1),
    6: (1, -1, 1),
    7: (1, 1, 1, 1, 1, 1, 1),
    8: (1, 0, 0, 0, 1),
    9: (1, 0, 0, 1, 0, 0, 1),
    10: (1, -1, 1, -1, 1),
    11: (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
    12: (1, 0, -1, 0, 1),
}


def _totient(n: int) -> int:
    """φ(n) computed independently from the prime factorisation."""
    phi = 1
    for p, e in factor(n):
        phi *= (p - 1) * p ** (e - 1)
    return phi if n > 1 else 1


def _poly_mul(a, b):
    out = [0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        if ai:
            for j, bj in enumerate(b):
                out[i + j] += ai * bj
    return out


def test_literal_coefficients_1_through_12():
    for n, want in LITERALS.items():
        got = cyclotomic_polynomial(n)
        assert got["coefficients"] == want, n
        assert got["n"] == n


def test_degree_is_the_totient():
    for n in range(1, 31):
        got = cyclotomic_polynomial(n)
        assert got["degree"] == _totient(n), n
        assert len(got["coefficients"]) == got["degree"] + 1, n
        assert got["coefficients"][-1] == 1, n       # monic


@pytest.mark.parametrize("n", [6, 12, 21])
def test_product_over_divisors_is_x_n_minus_1(n):
    divisors = [d for d in range(1, n + 1) if n % d == 0]
    prod = [1]
    for d in divisors:
        prod = _poly_mul(prod, list(cyclotomic_polynomial(d)["coefficients"]))
    want = [0] * (n + 1)
    want[0] = -1
    want[n] = 1
    assert prod == want


def test_refuses_bad_input():
    with pytest.raises(ValueError):
        cyclotomic_polynomial(0)
    with pytest.raises(TypeError):
        cyclotomic_polynomial(True)
    with pytest.raises(TypeError):
        cyclotomic_polynomial("12")


def test_exact_dft_cross_pin_1_through_30():
    """The private ``exact_dft._cyclotomic_reduction`` and the public op
    must derive the SAME ring: same degree φ(n), and the same full
    ζ-power reduction table when the public coefficients are expanded
    through ``_zeta_power_table``.  Table equality implies coefficient
    equality (row φ(n) of the table IS the negated non-leading Φ_n
    coefficients), so this pins the polynomials themselves."""
    for n in range(1, 31):
        table, deg = _cyclotomic_reduction(n)
        entry = cyclotomic_polynomial(n)
        assert deg == entry["degree"], n
        mine = tuple(_zeta_power_table(list(entry["coefficients"]), n))
        assert table == mine, n
