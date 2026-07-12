"""rc95 — elliptic_partial_fraction: the elliptic partial-fraction expansion (Rosengren
Eq. 1.22), the reduction engine of the multivariable Cₙ elliptic row.

The constructed partial-fraction SUM must equal the left-hand product
∏_k θ(x/z_k)/θ(x/y_k) — verified by the carrier's own exact-ℚ truncated-theta eval at
exact-ℚ sample points (the 1/θ(Y/Z) factor is load-bearing). numpy-free.
"""

import pytest

from srmech.amsc.ellbase import EllMonomial as M, Theta
from srmech.amsc.q import Q
from srmech.amsc.elliptic_partial_fraction import elliptic_partial_fraction

_TRUNC = 20
_ZV = [Q(2, 3), Q(5, 4), Q(9, 8), Q(7, 11)]
_YV = [Q(3, 5), Q(7, 6), Q(11, 10), Q(4, 13)]


def _setup(n):
    x = M.symbol("x")
    zs = [M.symbol(f"z{k}") for k in range(n)]
    ys = [M.symbol(f"y{k}") for k in range(n)]
    vals = {"p": Q(1, 19), "x": Q(4, 7)}
    for k in range(n):
        vals[f"z{k}"] = _ZV[k]
        vals[f"y{k}"] = _YV[k]
    return x, zs, ys, vals


@pytest.mark.parametrize("n", [1, 2, 3, 4])
def test_partial_fraction_sum_equals_product(n):
    x, zs, ys, vals = _setup(n)
    lhs = Q(1, 1)
    for k in range(n):
        lhs = lhs * (Theta(x * zs[k].inv()).eval_trunc(vals, _TRUNC)
                     / Theta(x * ys[k].inv()).eval_trunc(vals, _TRUNC))
    rhs = elliptic_partial_fraction(x, zs, ys).eval_trunc(vals, _TRUNC)
    rel = abs(float(lhs - rhs)) / (abs(float(lhs)) + abs(float(rhs)) + 1e-40)
    assert rel < 1e-10


def test_returns_n_term_thetasum():
    # the expansion is a sum of exactly n theta-quotient terms.
    x, zs, ys, _ = _setup(3)
    ts = elliptic_partial_fraction(x, zs, ys)
    assert len(ts._terms) == 3


def test_shape_validation():
    a = M.symbol("a")
    with pytest.raises(ValueError):
        elliptic_partial_fraction(a, [a, a], [a])   # len mismatch
    with pytest.raises(ValueError):
        elliptic_partial_fraction(a, [], [])        # empty
    with pytest.raises(TypeError):
        elliptic_partial_fraction(a, [1], [a])      # non-EllMonomial parameter
