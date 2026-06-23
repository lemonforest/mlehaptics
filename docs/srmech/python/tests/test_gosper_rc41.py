"""§76 (F929) — Gosper's indefinite hypergeometric summation ``gosper.gosper``.

The FIRST public op of the §76 "telescope" Σ-row closed-form prover. Given a
hypergeometric term by its term ratio ``t(k+1)/t(k) = num(k)/den(k)`` (two
exact-ℚ[k] ``Poly``), it returns the rational certificate ``R(k)`` with
antidifference ``T(k) = R(k)·t(k)`` (so ``Σ t(k)`` telescopes), or ``None`` when
no hypergeometric closed form exists.

This test is numpy-FREE and math-FREE (no ``import numpy`` / ``import math``): it
uses only ``fractions.Fraction`` + the srmech ``Q`` / ``Poly`` carriers + plain
Python arithmetic. **Every certificate is cross-checked by CONCRETE SUMMATION** —
the actual term values are summed and compared to ``T(n) − T(0)`` evaluated at
integers (never trusting the algorithm symbolically).

Coverage (the rc41 acceptance set):
  (1) t(k)=k          ratio (k+1)/k    -> Σ_{0..n-1} k = n(n-1)/2
  (2) t(k)=k·k!       ratio (k+1)²/k   -> Σ_{0..n-1} k·k! = n! − 1
  (3) t(k)=1/k harmonic ratio k/(k+1)  -> None  (the load-bearing NEGATIVE test)
  (4) t(k)=1/(k(k+1)) ratio k/(k+2)    -> telescopes to −1/k
  plus geometric Σ 2^k and a Python-op == C-peer parity check.
"""

from fractions import Fraction

import pytest

from srmech.amsc.gosper import gosper
from srmech.amsc.poly import Poly
from srmech.amsc.q import Q


# ── helpers (Fraction + Q only; no numpy, no math) ────────────────────────────

def _qf(q: Q) -> Fraction:
    """An exact ``Q`` -> a stdlib ``Fraction`` (for the cross-check arithmetic)."""
    return Fraction(q.numerator, q.denominator)


def _factorial(k: int) -> int:
    """Plain-Python factorial (no ``import math``)."""
    r = 1
    for i in range(2, k + 1):
        r *= i
    return r


def _poly_eval_frac(p: Poly, k: int) -> Fraction:
    """Evaluate a ``Poly`` at integer ``k`` as a ``Fraction`` (exact Horner)."""
    return _qf(p.eval(Q(k, 1)))


def _R_at(cert, k: int) -> Fraction:
    """The certificate rational ``R(k) = num(k)/den(k)`` as a ``Fraction``."""
    num = _poly_eval_frac(cert["num"], k)
    den = _poly_eval_frac(cert["den"], k)
    return num / den


# ── the four acceptance cases ─────────────────────────────────────────────────

def test_case1_t_equals_k():
    """t(k)=k, ratio (k+1)/k. Antidifference T(k)=R(k)·t(k); assert
    Σ_{k=0}^{n−1} k == T(n) − T(0) == n(n−1)/2 for n = 1..8 EXACTLY."""
    cert = gosper(Poly.from_coeffs([1, 1]), Poly.from_coeffs([0, 1]))
    assert cert is not None, "t(k)=k must have a hypergeometric antidifference"
    assert set(cert) == {"num", "den"}
    assert isinstance(cert["num"], Poly) and isinstance(cert["den"], Poly)

    def t(k):                                    # the term t(k) = k
        return Fraction(k)

    def big_t(k):                                # T(k) = R(k) · t(k)
        return _R_at(cert, k) * t(k)

    for n in range(1, 9):
        s = sum((t(k) for k in range(n)), Fraction(0))
        assert s == big_t(n) - big_t(0), f"telescope failed at n={n}"
        assert s == Fraction(n * (n - 1), 2), f"closed form failed at n={n}"


def test_case2_t_equals_k_times_kfactorial():
    """t(k)=k·k!, ratio (k+1)²/k. Antidifference k! (R=1/k). Assert the concrete
    Σ_{k=0}^{n−1} k·k! == n! − 1 for n=1..7, and the pole-free Gosper identity
    R(k+1)·(num/den) − R(k) == 1 (so R is a genuine certificate)."""
    num = Poly.from_coeffs([1, 2, 1])            # (k+1)² = k²+2k+1
    den = Poly.from_coeffs([0, 1])               # k
    cert = gosper(num, den)
    assert cert is not None

    def t(k):
        return Fraction(k * _factorial(k))

    # concrete sum: Σ_{0..n-1} k·k! == n! − 1  (term values; t(0)=0 so no pole)
    for n in range(1, 8):
        s = sum((t(k) for k in range(n)), Fraction(0))
        assert s == Fraction(_factorial(n) - 1), f"sum failed at n={n}"

    # pole-free certificate identity: R(k+1)·num(k)/den(k) − R(k) == 1
    for k in range(1, 8):
        ratio = _poly_eval_frac(num, k) / _poly_eval_frac(den, k)
        lhs = _R_at(cert, k + 1) * ratio - _R_at(cert, k)
        assert lhs == Fraction(1), f"Gosper identity failed at k={k}"

    # and the antidifference IS k!: T(k)=R(k)·t(k)=k! for k>=1 (t(k)!=0 there)
    for k in range(1, 8):
        assert _R_at(cert, k) * t(k) == Fraction(_factorial(k))


def test_case3_harmonic_has_no_closed_form():
    """t(k)=1/k harmonic, ratio k/(k+1) -> None (the load-bearing NEGATIVE test:
    the harmonic numbers have NO hypergeometric closed form)."""
    cert = gosper(Poly.from_coeffs([0, 1]), Poly.from_coeffs([1, 1]))
    assert cert is None


def test_case4_t_equals_one_over_k_kplus1_telescopes():
    """t(k)=1/(k(k+1)), ratio k/(k+2). Telescopes to −1/k. Assert
    Σ_{k=1}^{n} 1/(k(k+1)) == T(n+1) − T(1) == n/(n+1) (T(k)=R(k)·t(k))."""
    cert = gosper(Poly.from_coeffs([0, 1]), Poly.from_coeffs([2, 1]))
    assert cert is not None

    def t(k):                                    # t(k) = 1/(k(k+1)), k>=1
        return Fraction(1, k * (k + 1))

    def big_t(k):
        return _R_at(cert, k) * t(k)

    for n in range(1, 9):
        s = sum((t(k) for k in range(1, n + 1)), Fraction(0))
        assert s == big_t(n + 1) - big_t(1), f"telescope failed at n={n}"
        assert s == Fraction(n, n + 1), f"closed form failed at n={n}"

    # the antidifference reduces to R(k) = −(k+1) (so T(k)=−1/k)
    for k in range(1, 8):
        assert big_t(k) == Fraction(-1, k)


def test_case5_geometric_two_to_the_k():
    """t(k)=2^k, ratio 2 (a constant). Antidifference 2^k (R=1); assert
    Σ_{k=0}^{n−1} 2^k == 2^n − 1 == T(n) − T(0)."""
    cert = gosper(Poly.from_coeffs([2]), Poly.from_coeffs([1]))
    assert cert is not None
    # R == 1 (constant)
    assert cert["num"].coeffs == (Q(1, 1),)
    assert cert["den"].coeffs == (Q(1, 1),)

    def t(k):
        return Fraction(2 ** k)

    def big_t(k):
        return _R_at(cert, k) * t(k)

    for n in range(1, 9):
        s = sum((t(k) for k in range(n)), Fraction(0))
        assert s == big_t(n) - big_t(0)
        assert s == Fraction(2 ** n - 1)


def test_coefficient_list_inputs_accepted():
    """The term-ratio operands accept ascending-degree coefficient lists (the
    JSON / convenience form), not just Poly handles — value-identical."""
    a = gosper([1, 1], [0, 1])
    b = gosper(Poly.from_coeffs([1, 1]), Poly.from_coeffs([0, 1]))
    assert a is not None and b is not None
    assert a["num"].coeffs == b["num"].coeffs
    assert a["den"].coeffs == b["den"].coeffs


def test_zero_denominator_rejected():
    """A zero-polynomial denominator (an invalid term ratio) raises ValueError."""
    with pytest.raises(ValueError):
        gosper(Poly.from_coeffs([1, 1]), Poly.from_coeffs([]))


def test_native_matches_pure_when_present():
    """When the native srmech_gosper is loaded, its certificate is byte-identical
    to the pure-Python body (the parity oracle). Skip-clean when no native lib."""
    from srmech.amsc import _native as nat
    from srmech.amsc.gosper import _gosper_pure, _as_poly
    if not nat.has_native_gosper():
        pytest.skip("native srmech_gosper not present in this environment")

    cases = [
        ([1, 1], [0, 1]),        # k
        ([1, 2, 1], [0, 1]),     # k·k!
        ([0, 1], [1, 1]),        # harmonic -> None
        ([0, 1], [2, 1]),        # 1/(k(k+1))
        ([2], [1]),              # 2^k
        ([3], [1]),              # 3^k -> R = 1/2
        ([1, 3, 3, 1], [0, 1]),  # (k+1)³/k
        ([6, 5, 1], [2, 3, 1]),  # (k+2)(k+3)/((k+1)(k+2))
    ]

    def repr_cert(c):
        if c is None:
            return None
        return (tuple((v.numerator, v.denominator) for v in c["num"].coeffs),
                tuple((v.numerator, v.denominator) for v in c["den"].coeffs))

    for num, den in cases:
        native = gosper(num, den)                 # native path
        pure = _gosper_pure(_as_poly(num), _as_poly(den))
        assert repr_cert(native) == repr_cert(pure), (
            f"native/pure mismatch for ratio {num}/{den}")
