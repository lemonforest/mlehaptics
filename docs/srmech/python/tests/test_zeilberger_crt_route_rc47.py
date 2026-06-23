"""rc47 — route the exact-ℚ Zeilberger solve through the CRT fiber.

The PAYOFF rung of the CRT-QMat re-fibration arc. rc44–rc46 built the fiber
(``gf_rref`` + ``next_prime`` + ``crt_combine`` + ``rational_reconstruct`` +
``QMat.rref_crt``); this rc makes the consumers USE it, so the dense Hadamard-arena
wall is gone where it mattered — the Zeilberger undetermined-coefficient solve.

Two things are proven here, both numpy-FREE and ``math``-FREE (only
``fractions.Fraction`` as an independent oracle, the srmech exact carriers, and
plain ``int``):

  1. **THE LARGER-THAN-FRANEL HEADLINE** — ``f(n) = Σ_k C(n,k)^4`` (OEIS A005260,
     minimal recurrence **order 2**). ``zeilberger`` returns its minimal recurrence,
     and that recurrence is **cross-checked by concrete summation**: ``f(n)`` is
     summed directly and ``Σ_{j=0}^{order} a_j(n)·f(n+j)`` asserted exactly ``0`` for
     several ``n``. The degree-4 ratios make this a LARGER undetermined-coefficient
     system than the degree-3 order-2 Franel one — this is the kind of case the whole
     CRT-re-fibration arc exists to make bounded-memory (the dense Hadamard-envelope
     arena would otherwise re-reserve the GB the order-2 Franel one did).

  2. **BYTE-IDENTICAL VIA CRT** — the rc42 acceptance cases (``Σ C(n,k)=2^n``,
     ``Σ C(n,k)^2=C(2n,n)``) produce the SAME recurrence whether the kernel solve
     runs dense or through ``rref_crt`` — a regression that the CRT route does not
     change the answer, only the memory.

The Σ C(n,k)^4 case is HEAVY (the degree-4 BiPoly assembly + the larger-than-Franel
solve is minutes-scale in pure Python). It is gated behind ``SRMECH_RUN_HEAVY=1`` so
the default suite stays quick; CI / the self-verify run sets it. The byte-identical
regression + the small order-1 cross-checks carry the correctness signal in the
default run.
"""
from __future__ import annotations

import os
from fractions import Fraction

import pytest

from srmech.amsc.poly import Poly
from srmech.amsc.q import Q
from srmech.amsc.zeilberger import BiPoly, zeilberger


# ── helpers (Fraction + Q only; no numpy, no math) ────────────────────────────

def _comb(n: int, k: int) -> int:
    """Binomial C(n,k) by exact integer arithmetic (no ``import math``)."""
    if k < 0 or k > n:
        return 0
    k = min(k, n - k)
    num = 1
    for i in range(k):
        num = num * (n - i) // (i + 1)
    return num


def _recurrence_holds(res, f, nmax: int) -> bool:
    """``Σ_{j=0}^{L} a_j(n)·f(n+j) == 0`` for ``n = 0..nmax-1`` EXACTLY, with ``f``
    the concrete term sum and ``a_j`` the returned recurrence coefficients."""
    order, coeffs = res["order"], res["coeffs"]
    for n in range(nmax):
        s = Fraction(0)
        for j in range(order + 1):
            cj = coeffs[j].eval(Q(n, 1))
            s += Fraction(cj.numerator, cj.denominator) * Fraction(f(n + j))
        if s != 0:
            return False
    return True


def _P(*c):
    return Poly.from_coeffs(list(c))


def _bipow(b: BiPoly, e: int) -> BiPoly:
    r = BiPoly.one()
    for _ in range(e):
        r = r * b
    return r


# ── the canonical small ratios (the byte-identical regression set) ────────────

def _ratios_binomial():
    """F(n,k)=C(n,k): r_n=(n+1)/(n+1−k), r_k=(n−k)/(k+1) → f(n)=2^n, order 1."""
    rn_num = BiPoly([_P(1, 1)])                                  # n+1
    rn_den = BiPoly([_P(1, 1), _P(-1)])                          # (n+1) − k
    rk_num = BiPoly([_P(0, 1), _P(-1)])                          # n − k
    rk_den = BiPoly([_P(1), _P(1)])                              # k + 1
    return rn_num, rn_den, rk_num, rk_den


def _ratios_binomial_squared():
    """F(n,k)=C(n,k)^2 → f(n)=C(2n,n), order 1."""
    rn_num = BiPoly([_P(1, 2, 1)])                               # (n+1)^2
    rn_den = BiPoly([_P(1, 2, 1), _P(-2, -2), _P(1)])            # (n+1−k)^2
    rk_num = BiPoly([_P(0, 0, 1), _P(0, -2), _P(1)])            # (n−k)^2
    rk_den = BiPoly([_P(1), _P(2), _P(1)])                       # (k+1)^2
    return rn_num, rn_den, rk_num, rk_den


def _ratios_binomial_fourth():
    """F(n,k)=C(n,k)^4 → f(n)=Σ_k C(n,k)^4 (OEIS A005260), minimal order 2.
    r_n = ((n+1)/(n+1−k))^4, r_k = ((n−k)/(k+1))^4."""
    np1_bi = BiPoly([_P(1, 1)])                                  # n+1  (k-const)
    nm_k = BiPoly([_P(1, 1), _P(-1)])                            # (n+1) − k
    n_k = BiPoly([_P(0, 1), _P(-1)])                             # n − k
    kp1 = BiPoly([_P(1), _P(1)])                                 # k + 1
    return (_bipow(np1_bi, 4), _bipow(nm_k, 4),
            _bipow(n_k, 4), _bipow(kp1, 4))


# ── repr for the byte-identical compare ───────────────────────────────────────

def _repr_res(r):
    if r is None:
        return None
    return (r["order"],
            tuple(tuple((v.numerator, v.denominator) for v in c.coeffs)
                  for c in r["coeffs"]),
            tuple(tuple((v.numerator, v.denominator) for v in kp.coeffs)
                  for kp in r["certificate"].terms))


# ── (1) byte-identical: the CRT route does not change the answer ──────────────

def test_zeilberger_crt_route_byte_identical_to_dense():
    """The kernel solve dispatched through ``rref_crt`` (forced) vs the dense
    ``rref`` produces the IDENTICAL recurrence + certificate on the rc42 cases.

    We force the two paths by toggling the auto-by-size threshold around the
    kernel solve — ``threshold = -1`` forces CRT on every solve, a huge threshold
    forces dense — and assert the results are byte-for-byte equal."""
    import srmech.amsc.zeilberger as Z
    cases = [_ratios_binomial(), _ratios_binomial_squared()]
    saved = Z._CRT_KERNEL_CELL_THRESHOLD
    try:
        for ratios in cases:
            Z._CRT_KERNEL_CELL_THRESHOLD = 1 << 60        # force DENSE
            dense = zeilberger(*ratios, max_order=4)
            Z._CRT_KERNEL_CELL_THRESHOLD = -1             # force CRT every solve
            crt = zeilberger(*ratios, max_order=4)
            assert dense is not None and crt is not None
            assert _repr_res(dense) == _repr_res(crt), (
                "CRT-routed kernel solve diverged from the dense solve")
    finally:
        Z._CRT_KERNEL_CELL_THRESHOLD = saved


def test_zeilberger_crt_forced_recurrence_cross_checked():
    """With the CRT path FORCED on every kernel solve, the rc42 recurrences still
    hold under concrete summation (the answer is correct, not just self-consistent
    with the dense path)."""
    import srmech.amsc.zeilberger as Z
    saved = Z._CRT_KERNEL_CELL_THRESHOLD
    try:
        Z._CRT_KERNEL_CELL_THRESHOLD = -1                 # force CRT
        res1 = zeilberger(*_ratios_binomial(), max_order=4)
        assert res1["order"] == 1
        assert _recurrence_holds(res1, lambda n: 2 ** n, 9)

        res2 = zeilberger(*_ratios_binomial_squared(), max_order=4)
        assert res2["order"] == 1
        assert _recurrence_holds(
            res2, lambda n: sum(_comb(n, k) ** 2 for k in range(n + 1)), 8)
    finally:
        Z._CRT_KERNEL_CELL_THRESHOLD = saved


# ── (2) THE LARGER-THAN-FRANEL HEADLINE: f(n) = Σ_k C(n,k)^4 (OEIS A005260) ───

def test_larger_than_franel_sum_binomial_fourth_concrete_summation():
    """``zeilberger`` finds the minimal recurrence (order 2) for ``f(n)=Σ_k C(n,k)^4``
    and the returned recurrence is cross-checked by DIRECT concrete summation:
    ``Σ_{j=0}^{order} a_j(n)·f(n+j) == 0`` exactly for several ``n``. The degree-4
    ratios make this a LARGER undetermined-coefficient system than the degree-3
    order-2 Franel one — solved at BOUNDED memory through the CRT-routed kernel (no
    dense Hadamard-envelope arena).

    HEAVY (the degree-4 BiPoly assembly + the larger-than-Franel CRT solve is
    minutes-scale in pure Python). Gated behind ``SRMECH_RUN_HEAVY=1`` — the
    byte-identical regression + the order-1 forced-CRT cross-checks above carry the
    default-run signal."""
    if os.environ.get("SRMECH_RUN_HEAVY") != "1":
        pytest.skip("heavy Σ C(n,k)^4 acceptance — set SRMECH_RUN_HEAVY=1")

    res = zeilberger(*_ratios_binomial_fourth(), max_order=5)
    assert res is not None, "no recurrence found for Σ_k C(n,k)^4 within order 5"
    assert res["order"] == 2, (
        f"Σ_k C(n,k)^4 minimal recurrence is order 2 (A005260); got {res['order']}")

    def f(n):                                    # f(n) = Σ_k C(n,k)^4 (A005260)
        return sum(_comb(n, k) ** 4 for k in range(n + 1))

    # OEIS A005260: 1, 2, 18, 164, 1810, 21252, …
    assert [f(n) for n in range(5)] == [1, 2, 18, 164, 1810]
    assert _recurrence_holds(res, f, 10), (
        "the order-2 recurrence fails the concrete-summation cross-check")
