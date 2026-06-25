"""rc66 foundation — the degree-d elliptic Lagrange interpolation basis (``ellbase``).

The certificate-numerator ansatz for the GENUINE order>=1 ``elliptic_zeilberger`` (the
degree-d elliptic Gosper-Petkovsek construction): the unknown elliptic certificate's
numerator is a higher-order theta function of fixed degree k, which lives in the
k-dimensional space V_t = {f : f(px) = t x^{-k} f(x)}; ``elliptic_lagrange_basis`` returns
the Lagrange basis of V_t at k interpolation points, so the certificate is a LINEAR
combination Sum_i c_i L_i with exact-Q (or parameter-polynomial) coefficients c_i.

Reference (MPM-verified at build against the actual PDF): Hjalmar Rosengren, *Elliptic
Hypergeometric Functions* (arXiv:1608.06161v3 [math.CA]), section 1.3 Corollary 1.3.5 (the
factorization f = C*theta(x/a_1,...,x/a_k;p) with (-1)^k a_1...a_k = t) and Eq. (1.5)
(theta(px;p) = -x^{-1} theta(x;p), the pin-slot multiplier).
"""

import pytest

from srmech.amsc.ellbase import (EllMonomial as M, Theta, EllRatio as R, _X, _P,
                                 elliptic_lagrange_basis)
from srmech.amsc.q import Q

_x = M.symbol(_X)


def test_multiplier_is_exactly_t_x_minus_k():
    """Every L_i has multiplier EXACTLY t*x^{-k} under x -> p*x (Cor 1.3.5 / Eq 1.5): each
    theta(x/c) contributes the pin-slot prefactor -c*x^{-1}, so the product over the k
    zeros is (-1)^k * (prod of zeros) * x^{-k} = (-1)^k * (-1)^k * t * x^{-k} = t*x^{-k}."""
    u = [M.symbol("u1"), M.symbol("u2"), M.symbol("u3")]
    t = M.symbol("t"); k = 3
    target = t * M.symbol(_X, -k)
    basis = elliptic_lagrange_basis(u, t)
    assert len(basis) == k
    for L in basis:
        assert len(L.num) == k and not L.den          # degree-k theta product
        pref = M.one()
        for th in L.num:
            c = _x * th.arg.inv()                      # the pole c of theta(x/c)
            pref = pref * (M.scalar(Q(-1, 1)) * c * M.symbol(_X, -1))
        assert pref == target


def test_balancing_product_of_zeros():
    """The product of each L_i's k zeros equals (-1)^k * t (the Cor 1.3.5 condition that
    makes every L_i land in the SAME space V_t)."""
    u = [M.symbol("u1"), M.symbol("u2"), M.symbol("u3")]
    t = M.symbol("t"); k = 3
    sgn = M.scalar(Q((-1) ** k, 1))
    for L in elliptic_lagrange_basis(u, t):
        prod = M.one()
        for th in L.num:
            prod = prod * (_x * th.arg.inv())          # the pole c
        assert prod == sgn * t


def test_lagrange_zero_placement_and_independence():
    """L_i(u_j) = 0 for j != i (the theta(x/u_j) factor is zero at x = u_j since
    theta(1;p) = 0) and != 0 at u_i — the elliptic-Lagrange interpolation property. The
    eval matrix is thus diagonal, so the k functions are linearly INDEPENDENT and span
    V_t. Verified with the carrier's exact ``eval_trunc`` (theta(1;p) = 0 exactly, so the
    zeros are exact, not truncation artifacts)."""
    uv = [Q(2, 1), Q(5, 1), Q(3, 1)]                   # distinct interpolation points
    u = [M.scalar(v) for v in uv]
    t = M.scalar(Q(7, 1)); pval = Q(1, 7)
    basis = elliptic_lagrange_basis(u, t)
    for i, L in enumerate(basis):
        for j, ujv in enumerate(uv):
            val = L.eval_trunc({_X: ujv, _P: pval}, 24)
            if i == j:
                assert val != Q(0, 1)                  # non-zero at its own node u_i
            else:
                assert val == Q(0, 1)                  # zero at every other node u_j


def test_degree_one_basis():
    """k = 1: V_t is 1-dimensional, basis = {theta(x/v)} with v = -t (the lone balancing
    point), multiplier -v*x^{-1} = t*x^{-1}."""
    t = M.symbol("t")
    basis = elliptic_lagrange_basis([M.symbol("u1")], t)
    assert len(basis) == 1
    L = basis[0]
    assert len(L.num) == 1
    c = _x * L.num[0].arg.inv()
    assert c == M.scalar(Q(-1, 1)) * t                 # v = (-1)^1 * t / (empty) = -t


def test_empty_points_rejected():
    with pytest.raises(ValueError):
        elliptic_lagrange_basis([], M.symbol("t"))
