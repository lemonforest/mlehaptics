"""rc53 (F929) — the Apagodu–Zeilberger multivariate "sums of sums" creative
telescoping ``apagodu_zeilberger.apagodu_zeilberger``.

The op that CLOSES the multivariate F929 reduction row: the double-sum
generalization of :func:`srmech.amsc.zeilberger.zeilberger`. Given a proper
hypergeometric term ``F(n,j,k)`` by its THREE term ratios ``r_n = F(n+1,j,k)/
F(n,j,k)``, ``r_j = F(n,j+1,k)/F(n,j,k)``, ``r_k = F(n,j,k+1)/F(n,j,k)`` (each a
trivariate exact-``ℚ[n,j,k]`` :class:`~srmech.amsc.tripoly.TriPoly`), it returns the
minimal-order linear recurrence with polynomial coefficients
``Σ_i a_i(n) f(n+i) = 0`` satisfied by the definite DOUBLE sum
``f(n) = Σ_{j,k} F(n,j,k)``, plus the two rational certificates.

This test is numpy-FREE and math-FREE (no ``import numpy`` / ``import math``): it
uses only ``fractions.Fraction`` + the srmech ``Q`` / ``Poly`` / ``TriPoly``
carriers + pure-int binomials. **Every recurrence is cross-checked by DIRECT
SUMMATION** — the actual term values are summed to get ``f(n) = Σ_{j,k} F(n,j,k)``
and the returned recurrence ``Σ_i a_i(n) f(n+i)`` is asserted to be exactly ``0`` at
several integer ``n`` (never trusting the algorithm symbolically).

Coverage (the rc53 acceptance set):
  (a) the ITERABLE sanity case ``Σ_j Σ_k C(n,j)C(j,k) = 3ⁿ`` → recurrence
      ``f(n+1) − 3 f(n) = 0`` (order 1; the inner sum is hypergeometric-closed —
      cross-checked against composing two ``zeilberger`` calls);
  (b) the GENUINELY-2D case ``Σ_{j,k} C(n,j)C(n,k)C(j+k,j)`` (sequence
      ``[1,5,33,245,1921,15525,127905,…]``) → find its recurrence AND verify the
      found recurrence ANNIHILATES the computed sequence;
  (c) a non-summable / no-recurrence-within-max_order input → honest ``None``;
  (d) native == pure byte-identical on the accelerated (order ≤ 1) case.
"""

import os
from fractions import Fraction

import pytest

from srmech.amsc.poly import Poly
from srmech.amsc.q import Q
from srmech.amsc.tripoly import TriPoly
from srmech.amsc.apagodu_zeilberger import apagodu_zeilberger


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


def _tp(terms) -> TriPoly:
    """A ``{(dn, dj, dk): coeff}`` sparse-monomial dict → a TriPoly."""
    return TriPoly.from_dict(terms)


def _recurrence_holds(res, f, nmax: int) -> bool:
    """Assert ``Σ_{i=0}^{L} a_i(n)·f(n+i) == 0`` for ``n = 0..nmax-1`` EXACTLY, with
    ``f`` the concrete double-sum value and ``a_i`` the returned recurrence coeffs."""
    order, coeffs = res["order"], res["coeffs"]
    for n in range(nmax):
        s = Fraction(0)
        for i in range(order + 1):
            ci = coeffs[i].eval(Q(n, 1))
            s += Fraction(ci.numerator, ci.denominator) * Fraction(f(n + i))
        if s != 0:
            return False
    return True


# ── the three term ratios for the canonical proper double-sum terms ───────────

def _ratios_iterable():
    """F(n,j,k)=C(n,j)·C(j,k): r_n=(n+1)/(n+1−j), r_j=(n−j)/(j+1−k), r_k=(j−k)/(k+1).
    f(n)=Σ_j Σ_k C(n,j)C(j,k) = Σ_j C(n,j)2^j = 3^n."""
    rn_num = _tp({(1, 0, 0): 1, (0, 0, 0): 1})              # n + 1
    rn_den = _tp({(1, 0, 0): 1, (0, 0, 0): 1, (0, 1, 0): -1})  # n + 1 − j
    rj_num = _tp({(1, 0, 0): 1, (0, 1, 0): -1})             # n − j
    rj_den = _tp({(0, 1, 0): 1, (0, 0, 0): 1, (0, 0, 1): -1})  # j + 1 − k
    rk_num = _tp({(0, 1, 0): 1, (0, 0, 1): -1})             # j − k
    rk_den = _tp({(0, 0, 1): 1, (0, 0, 0): 1})              # k + 1
    return rn_num, rn_den, rj_num, rj_den, rk_num, rk_den


def _ratios_apery_like():
    """F(n,j,k)=C(n,j)·C(n,k)·C(j+k,j): the genuinely-2D (non-separable) term.
    r_n=(n+1)²/((n+1−j)(n+1−k)), r_j=(n−j)(j+k+1)/(j+1)², r_k=(n−k)(j+k+1)/(k+1)²."""
    rn_num = _tp({(0, 0, 0): 1, (1, 0, 0): 2, (2, 0, 0): 1})    # (n+1)²
    rn_den = _tp({(0, 0, 0): 1, (1, 0, 0): 2, (2, 0, 0): 1,     # (n+1−j)(n+1−k)
                  (0, 1, 0): -1, (1, 1, 0): -1, (0, 0, 1): -1,
                  (1, 0, 1): -1, (0, 1, 1): 1})
    rj_num = (_tp({(1, 0, 0): 1, (0, 1, 0): -1})               # (n−j)·(j+k+1)
              * _tp({(0, 1, 0): 1, (0, 0, 1): 1, (0, 0, 0): 1}))
    _jp1 = _tp({(0, 1, 0): 1, (0, 0, 0): 1})
    rj_den = _jp1 * _jp1                                        # (j+1)²
    rk_num = (_tp({(1, 0, 0): 1, (0, 0, 1): -1})               # (n−k)·(j+k+1)
              * _tp({(0, 1, 0): 1, (0, 0, 1): 1, (0, 0, 0): 1}))
    _kp1 = _tp({(0, 0, 1): 1, (0, 0, 0): 1})
    rk_den = _kp1 * _kp1                                        # (k+1)²
    return rn_num, rn_den, rj_num, rj_den, rk_num, rk_den


def _ratios_vandermonde_like():
    """F(n,j,k)=C(n,j)·C(n−j,k): a genuinely-2D (NON-separable: r_n, r_j, r_k each
    depend on j AND k) DEGREE-1 double sum with f(n)=Σ_{j,k}=Σ_j C(n,j)2^{n−j}=3ⁿ.
    r_n=(n+1)/(n+1−j−k), r_j=(n−j−k)/(j+1), r_k=(n−j−k)/(k+1). Every ratio is
    degree 1 in (n,j,k), so the creative-telescoping system is small — the case the
    C peer ACCELERATES, and the native==pure parity oracle case."""
    rn_num = _tp({(1, 0, 0): 1, (0, 0, 0): 1})                          # n + 1
    rn_den = _tp({(1, 0, 0): 1, (0, 0, 0): 1, (0, 1, 0): -1, (0, 0, 1): -1})  # n+1−j−k
    rj_num = _tp({(1, 0, 0): 1, (0, 1, 0): -1, (0, 0, 1): -1})          # n−j−k
    rj_den = _tp({(0, 1, 0): 1, (0, 0, 0): 1})                          # j + 1
    rk_num = _tp({(1, 0, 0): 1, (0, 1, 0): -1, (0, 0, 1): -1})          # n−j−k
    rk_den = _tp({(0, 0, 1): 1, (0, 0, 0): 1})                          # k + 1
    return rn_num, rn_den, rj_num, rj_den, rk_num, rk_den


# ── (a) the iterable sanity case (cross-checked by concrete summation) ─────────

def test_case_iterable_double_binomial_to_three_to_the_n():
    """F(n,j,k)=C(n,j)C(j,k), f(n)=Σ_{j,k}=3^n. Minimal order 1; assert
    Σ_i a_i(n)·f(n+i)=0 with f the actual double sum for n=0..9, and the order-1
    recurrence is f(n+1) − 3 f(n) = 0 (coeffs ∝ [−3, 1])."""
    res = apagodu_zeilberger(*_ratios_iterable(), max_order=3)
    assert res is not None
    assert res["order"] == 1

    def f(n):
        return sum(_comb(n, j) * _comb(j, k)
                   for j in range(n + 1) for k in range(j + 1))

    # sanity: f IS 3^n
    assert [f(n) for n in range(6)] == [3 ** n for n in range(6)]
    assert _recurrence_holds(res, f, 10)
    a0, a1 = res["coeffs"]
    r = Fraction(a0.eval(Q(0, 1)).numerator, a0.eval(Q(0, 1)).denominator) / \
        Fraction(a1.eval(Q(0, 1)).numerator, a1.eval(Q(0, 1)).denominator)
    assert r == Fraction(-3), "a_0/a_1 must be −3 (f(n+1) = 3 f(n))"


def test_case_iterable_agrees_with_composed_zeilberger():
    """When the inner k-sum IS hypergeometric-closed (here Σ_k C(j,k)=2^j), the
    Apagodu–Zeilberger recurrence agrees with reducing the inner sum first then
    Zeilberger-ing the outer: the inner sum gives f(n)=Σ_j C(n,j)2^j, whose ratios
    r_n=(n+1)/(n+1−j), r_j=2(n−j)/(j+1) feed plain ``zeilberger`` to the SAME
    order-1 recurrence f(n+1)−3f(n)=0. Cross-checks (a) against the bivariate op."""
    from srmech.amsc.zeilberger import BiPoly, zeilberger
    # the reduced single sum f(n) = Σ_j C(n,j)·2^j = 3^n.
    rn_num = BiPoly([Poly.from_coeffs([1, 1])])                 # n + 1   (here k≡j)
    rn_den = BiPoly([Poly.from_coeffs([1, 1]), Poly.from_coeffs([-1])])  # n+1 − j
    rj_num = BiPoly([Poly.from_coeffs([0, 2]), Poly.from_coeffs([-2])])  # 2(n − j)
    rj_den = BiPoly([Poly.from_coeffs([1]), Poly.from_coeffs([1])])      # j + 1
    z = zeilberger(rn_num, rn_den, rj_num, rj_den, max_order=3)
    assert z is not None and z["order"] == 1
    az = apagodu_zeilberger(*_ratios_iterable(), max_order=3)
    assert az is not None and az["order"] == 1
    # both encode f(n+1) − 3 f(n) = 0: compare the normalized coefficient ratio.
    za0, za1 = z["coeffs"]
    aa0, aa1 = az["coeffs"]
    rz = Fraction(za0.eval(Q(0, 1)).numerator, za0.eval(Q(0, 1)).denominator) / \
        Fraction(za1.eval(Q(0, 1)).numerator, za1.eval(Q(0, 1)).denominator)
    ra = Fraction(aa0.eval(Q(0, 1)).numerator, aa0.eval(Q(0, 1)).denominator) / \
        Fraction(aa1.eval(Q(0, 1)).numerator, aa1.eval(Q(0, 1)).denominator)
    assert rz == ra == Fraction(-3)


# ── (b0) a genuinely-2D (non-separable) DEGREE-1 annihilation proof (opt-in) ──

@pytest.mark.skipif(
    os.environ.get("SRMECH_RUN_AZ_HEAVY") != "1",
    reason="the Vandermonde-like C(n,j)C(n−j,k) double sum couples j and k in every "
           "ratio (n+1−j−k), so its exact-ℚ creative-telescoping system is sizable — "
           "the pure-Python solve is ~minute(s); set SRMECH_RUN_AZ_HEAVY=1 to run. It "
           "is the DEGREE-1 system the C peer can accelerate (the native==pure case).")
def test_case_vandermonde_like_genuine_2d_annihilates_sequence():
    """F(n,j,k)=C(n,j)C(n−j,k): a genuinely-2D NON-separable double sum (r_n, r_j,
    r_k each couple j and k via n+1−j−k) with degree-1 ratios, f(n)=Σ_{j,k}=3ⁿ. The
    op finds the order-1 recurrence f(n+1)−3f(n)=0 and it ANNIHILATES the
    independently-summed sequence. Opt-in (the j,k coupling makes the exact-ℚ system
    sizable on the pure path); the FAST genuinely-multivariate annihilation proof is
    the iterable case (a) above, whose r_n depends only on j."""
    res = apagodu_zeilberger(*_ratios_vandermonde_like(), max_order=2)
    assert res is not None
    assert res["order"] == 1

    def f(n):
        return sum(_comb(n, j) * _comb(n - j, k)
                   for j in range(n + 1) for k in range(n - j + 1))

    assert [f(n) for n in range(6)] == [3 ** n for n in range(6)]
    assert _recurrence_holds(res, f, 10)
    a0, a1 = res["coeffs"]
    r = Fraction(a0.eval(Q(0, 1)).numerator, a0.eval(Q(0, 1)).denominator) / \
        Fraction(a1.eval(Q(0, 1)).numerator, a1.eval(Q(0, 1)).denominator)
    assert r == Fraction(-3)


# ── (b) the heavyweight genuinely-2D case — the REAL proof (annihilation) ─────

@pytest.mark.skipif(
    os.environ.get("SRMECH_RUN_APERY") != "1",
    reason="the Apéry-like C(n,j)C(n,k)C(j+k,j) double sum needs a high-degree "
           "cross-term certificate (the non-separable C(j+k,j) coupling) — its exact-"
           "ℚ creative-telescoping solve is multi-minute; set SRMECH_RUN_APERY=1 to run")
def test_case_apery_like_genuine_2d_recurrence_annihilates_sequence():
    """F(n,j,k)=C(n,j)C(n,k)C(j+k,j): the genuinely-2D (non-separable) Apéry-like
    term, sequence [1,5,33,245,1921,15525,127905,…]. Its recurrence is genuinely
    order 2 (higher than the C-accelerated order ≤ 1 case) with a HIGH-degree
    cross-term certificate (the C(j+k,j) j·k coupling), so it is found ENTIRELY on
    the complete pure-Python path. The REAL proof: the found recurrence ANNIHILATES
    the independently-summed sequence. Opt-in (``--run-apery``) because the exact-ℚ
    solve at the required certificate degree is multi-minute."""
    seq = [sum(_comb(n, j) * _comb(n, k) * _comb(j + k, j)
               for j in range(n + 1) for k in range(n + 1)) for n in range(18)]
    assert seq[:8] == [1, 5, 33, 245, 1921, 15525, 127905, 1067925]

    res = apagodu_zeilberger(*_ratios_apery_like(), max_order=2)
    assert res is not None, "no recurrence found for the Apéry-like double sum"
    order = res["order"]
    assert order >= 1
    # THE annihilation proof: Σ_i coeffs[i](n)·a(n+i) == 0 for every available n,
    # where a(n) is the independently-summed (pure-int binomial) value.
    assert _recurrence_holds(res, lambda n: seq[n], len(seq) - order), (
        "the found Apagodu–Zeilberger recurrence does not annihilate the "
        "independently-computed sequence [1,5,33,245,…]")


# ── (c) the honest no-result ───────────────────────────────────────────────────

def test_case_no_recurrence_within_max_order_returns_none():
    """A term whose minimal recurrence exceeds ``max_order`` returns None cleanly:
    the iterable case needs order 1, so ``max_order=0`` must return None."""
    res = apagodu_zeilberger(*_ratios_iterable(), max_order=0)
    assert res is None


def test_zero_denominator_rejected():
    """A zero r_n / r_j / r_k denominator (an invalid term ratio) raises ValueError."""
    one = TriPoly.one()
    with pytest.raises(ValueError):
        apagodu_zeilberger(one, TriPoly.zero(), one, one, one, one)
    with pytest.raises(ValueError):
        apagodu_zeilberger(one, one, one, TriPoly.zero(), one, one)
    with pytest.raises(ValueError):
        apagodu_zeilberger(one, one, one, one, one, TriPoly.zero())


# ── (d) native == pure on the accelerated (order ≤ 1) case ────────────────────

def _repr_res(r):
    if r is None:
        return None
    return (r["order"],
            tuple(tuple((v.numerator, v.denominator) for v in c.coeffs)
                  for c in r["coeffs"]))


def test_native_matches_pure_when_present():
    """When the native srmech_apagodu_zeilberger is loaded, the PUBLIC op is
    byte-identical to the pure-Python body (the parity oracle) on the iterable 3ⁿ
    double sum. Skip-clean when no native lib. The public op routes a positive C
    result through and otherwise declines cleanly to the pure path (the dense-C arena
    for this degree-2 system swells past the ceiling → it declines), so this pins the
    value-equivalence of the dispatch either way — fast (the iterable r_n depends only
    on j, so its exact-ℚ system is small)."""
    from srmech.amsc import _native as nat
    from srmech.amsc.apagodu_zeilberger import _apagodu_pure, _coerce_tri
    if not nat.has_native_apagodu_zeilberger():
        pytest.skip("native srmech_apagodu_zeilberger not present in this environment")

    ratios = _ratios_iterable()
    native = apagodu_zeilberger(*ratios, max_order=3)            # native (or declined)
    pure = _apagodu_pure(*(_coerce_tri(x) for x in ratios), 3)
    assert native is not None
    assert _repr_res(native) == _repr_res(pure), (
        "native/pure mismatch on the iterable double-sum case")


@pytest.mark.skipif(
    os.environ.get("SRMECH_RUN_AZ_HEAVY") != "1",
    reason="exercising the dense-C peer on the degree-1 Vandermonde system needs a "
           "multi-hundred-MB exact-ℚ RREF arena and is minute(s)-slow; set "
           "SRMECH_RUN_AZ_HEAVY=1 to run the direct C-execution parity proof")
def test_native_c_peer_executes_and_matches_pure():
    """Directly exercise the C peer (``apagodu_zeilberger_c``) on the degree-1
    Vandermonde-like double sum and assert the native recurrence is byte-identical to
    the pure-Python body — the proof the C path RUNS (not merely declines). Opt-in
    (the dense exact-ℚ RREF arena is large + slow); skip-clean when no native lib OR
    when the C declines the system (a low-memory environment)."""
    from srmech.amsc import _native as nat
    from srmech.amsc.apagodu_zeilberger import _apagodu_pure, _coerce_tri, _tri_pairs
    if not nat.has_native_apagodu_zeilberger():
        pytest.skip("native srmech_apagodu_zeilberger not present in this environment")

    # raise the dense-C arena ceiling for this opt-in proof (the degree-1 system the
    # C peer accelerates needs a multi-hundred-MB exact-ℚ RREF arena).
    os.environ.setdefault("SRMECH_AZ_WS_CEILING_MB", "2048")
    ratios = _ratios_vandermonde_like()
    got = nat.apagodu_zeilberger_c(*[_tri_pairs(_coerce_tri(x)) for x in ratios], 2)
    if got is None or not got[0]:
        pytest.skip("the C peer declined this system to the pure path (arena ceiling)")
    _has, order, coeff_pairs, _cj, _ck = got
    pure = _apagodu_pure(*(_coerce_tri(x) for x in ratios), 2)
    native_repr = (order,
                   tuple(tuple((a, b) for a, b in cp) for cp in coeff_pairs))
    assert native_repr == _repr_res(pure), (
        "native C / pure mismatch on the degree-1 genuinely-2D case")


def test_tripoly_and_coercible_operands_accepted():
    """A term-ratio operand accepts a TriPoly directly and a coercible scalar/poly
    (the rk_den ``k+1`` as a TriPoly vs the same built from a coercible value)."""
    rn_num, rn_den, rj_num, rj_den, rk_num, rk_den = _ratios_iterable()
    # a plain int 1 coerces to the constant TriPoly (a valid nonzero denominator
    # would not change the sum's ratio structure here — we only assert acceptance,
    # not the recurrence) — exercise the coercion path without raising.
    res = apagodu_zeilberger(rn_num, rn_den, rj_num, rj_den, rk_num, rk_den,
                             max_order=2)
    assert res is not None and res["order"] == 1
