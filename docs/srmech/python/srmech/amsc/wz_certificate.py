"""srmech.amsc.wz_certificate — the Wilf–Zeilberger pair method (the THIRD and
FINAL public op of the §76 "telescope" Σ-row closed-form prover, F929).

Where :func:`srmech.amsc.gosper.gosper` does INDEFINITE summation and
:func:`srmech.amsc.zeilberger.zeilberger` FINDS the definite-sum recurrence,
``wz_certificate`` **PROVES a hypergeometric identity** — it produces AND
verifies the *WZ certificate* of a terminating identity ``Σ_k F(n,k) = const``
(Wilf & Zeilberger, "Rational functions certify combinatorial identities",
J. Amer. Math. Soc. 3(1):147–158, 1990; the canonical modern reference is
Petkovšek, Wilf & Zeilberger, *A = B*, A K Peters 1996, ch. 7).

The WZ method is **Zeilberger specialized to the forced n-recurrence**
``f(n+1) − f(n) = 0`` (the recurrence coefficient vector ``[−1, +1]``): the
normalized summand ``F(n,k)`` of an identity ``Σ_k F(n,k) = const`` satisfies
``Σ_k [F(n+1,k) − F(n,k)] = 0``, and the WZ certificate is the rational function
``R(n,k)`` whose companion ``G(n,k) = R(n,k)·F(n,k)`` makes that sum telescope:

    F(n+1,k) − F(n,k) = G(n,k+1) − G(n,k)            (the **WZ equation**)

Input — the two **term ratios** of the proper hypergeometric term ``F``, each a
rational function of ``(n,k)`` given by a numerator / denominator pair of
:class:`~srmech.amsc.zeilberger.BiPoly` (exact-``ℚ[n,k]``):

  * ``r_n(n,k) = F(n+1,k) / F(n,k)``   (the ``rn_num`` / ``rn_den`` operands)
  * ``r_k(n,k) = F(n,k+1) / F(n,k)``   (the ``rk_num`` / ``rk_den`` operands)

The op does BOTH halves of the WZ method:

  1. **FIND** the certificate ``R(n,k)`` (a rational function, as a ``BiPoly``
     num/den pair). This is Gosper-in-``k`` applied to ``F(n+1,k) − F(n,k)``, i.e.
     EXACTLY what :func:`~srmech.amsc.zeilberger.zeilberger` produces at the
     forced recurrence ``[−1, +1]`` — so the FIND step reuses the rc42 creative-
     telescoping machinery (``zeilberger`` with ``max_order=1``; the order-1
     recurrence of ``F`` IS ``f(n+1) − f(n) = 0`` precisely when the identity sum
     is constant in ``n``, and its certificate is the WZ certificate).

  2. **VERIFY** that the WZ equation holds as an EXACT bivariate rational-function
     identity in ``(n,k)`` — a purely algebraic check via the ``BiPoly`` toolkit,
     **no solve, no order bound** (bounded only by input degree). Dividing the WZ
     equation through by ``F(n,k)`` gives the rational identity

         r_n(n,k) − 1 = R(n,k+1)·r_k(n,k) − R(n,k),

     and clearing denominators turns it into the single polynomial identity

         (rn_num − rn_den)·(Xd(k+1)·rk_den·Xd)
            == (Xn(k+1)·rk_num·Xd − Xn·Xd(k+1)·rk_den)·rn_den,

     where ``R = Xn/Xd`` (``Xn(k+1)`` / ``Xd(k+1)`` are the ``k→k+1`` shifts). This
     is the NEW primitive — ``srmech_wz_verify`` is its complete C mirror.

Returns ``{"certificate": {"num": BiPoly, "den": BiPoly}, "verified": True}`` when
a WZ certificate exists AND the WZ equation verifies, else ``None`` (the term is
not WZ-summable / the identity is not a constant sum).

The whole pipeline stays EXACT over ``ℚ`` — every polynomial is a
:class:`~srmech.amsc.zeilberger.BiPoly` (each coefficient a
:class:`~srmech.amsc.poly.Poly` over the bigint :class:`~srmech.amsc.q.Q`, no
magnitude ceiling), the verify a coefficient-by-coefficient compare. There is NO
float anywhere; sign is the **Class-K** pin-slot via the ``Q`` sign-branch (never
an ALU ``abs()``); no ``math`` module, no numpy. This is the **Σ-row closer** of
the F929 closure-dispatch: gosper (indefinite) → zeilberger (recurrence) →
wz_certificate (proof).

C peer: ``srmech_wz_verify`` (``c/src/srmech_wz.c``) is the COMPLETE C mirror of
the VERIFY half — the exact bivariate-``ℚ`` rational-function identity check,
bounded only by input degree (NOT by any order; unlike rc42's order-≤1 peer this
is a full mirror). It composes the existing ``srmech_poly_*`` algebra over
caller-arena ``srmech_bigint`` into one JPL-clean symbol. ``wz_certificate``'s
verify routes through it when ``HAS_NATIVE``
(:func:`srmech.amsc._native.has_native_wz_verify`); the pure-Python verify here is
the COMPLETE alternative (and the byte-identical parity oracle). The FIND step
composes the existing ``srmech_zeilberger`` machinery (native-accelerated when
present, pure-Python the complete decider).
"""

from __future__ import annotations

from typing import Dict, Optional

from .poly import Poly
from .q import Q
from .zeilberger import BiPoly, zeilberger

__all__ = ["wz_certificate"]


def _native():
    """The native ``_native`` module IF the rc43 ``srmech_wz_verify`` peer is
    present and bound, else ``None`` — so the verify dispatches to C when available
    and falls cleanly to the pure-Python check (the complete alternative + the
    parity oracle) otherwise. Imported lazily to avoid a bootstrap cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    probe = getattr(nat, "has_native_wz_verify", None)
    return nat if (probe is not None and probe()) else None


def _bi_pairs(b: BiPoly):
    """A ``BiPoly`` → a k-ascending list of (per-k-coefficient) ascending-n
    ``(num, den)`` int-pair lists — the flat bridge form for the C peer (mirrors
    ``zeilberger._bi_pairs``)."""
    return [[(c.numerator, c.denominator) for c in kp.coeffs] for kp in b.terms]


def wz_certificate(rn_num, rn_den, rk_num, rk_den) -> Optional[Dict[str, object]]:
    """Prove a terminating hypergeometric identity by its Wilf–Zeilberger pair.

    ``rn_num`` / ``rn_den`` are the numerator / denominator of the ``n``-term-ratio
    ``r_n(n,k) = F(n+1,k)/F(n,k)``; ``rk_num`` / ``rk_den`` likewise for the
    ``k``-term-ratio ``r_k(n,k) = F(n,k+1)/F(n,k)``. Each is a
    :class:`~srmech.amsc.zeilberger.BiPoly` (exact-``ℚ[n,k]``), or a
    :class:`~srmech.amsc.poly.Poly` (read as a polynomial in ``k`` alone), or an
    ascending-``k``-degree coefficient sequence. ``F`` must be the NORMALIZED
    summand of a constant identity (``Σ_k F(n,k)`` independent of ``n``).

    FINDs the WZ certificate ``R(n,k)`` (Gosper-in-``k`` of ``F(n+1,k)−F(n,k)`` =
    :func:`~srmech.amsc.zeilberger.zeilberger` at the forced recurrence ``[−1,+1]``)
    and VERIFIES the WZ equation ``F(n+1,k)−F(n,k) = G(n,k+1)−G(n,k)`` (``G=R·F``)
    as an EXACT bivariate rational-function identity — no solve, no order bound.

    Returns ``{"certificate": {"num": BiPoly, "den": BiPoly}, "verified": True}``
    when a WZ certificate exists AND verifies, else ``None`` (the term is not
    WZ-summable). Exact over ``ℚ`` (bigint, no magnitude ceiling); no float, no
    ``abs()`` (the sign is the Class-K pin-slot), no ``math`` / numpy. See the
    module docstring for the full WZ pipeline. ``rn_den`` / ``rk_den`` must be
    nonzero (a term ratio has a nonzero denominator) — ``ValueError`` otherwise."""
    rn_n = BiPoly.coerce(rn_num)
    rn_d = BiPoly.coerce(rn_den)
    rk_n = BiPoly.coerce(rk_num)
    rk_d = BiPoly.coerce(rk_den)
    if rn_d.is_zero or rk_d.is_zero:
        raise ValueError(
            "wz_certificate: the term-ratio denominators r_n den / r_k den must be "
            "NONZERO bivariate polynomials")

    # ── FIND: the WZ certificate is the order-1 (forced f(n+1)−f(n)=0) Zeilberger
    # certificate. A definite sum that is constant in n IS the order-1 recurrence
    # f(n+1) − f(n) = 0 (coeffs ∝ [−1, +1]); zeilberger at max_order=1 returns that
    # recurrence + its certificate. If no order-≤1 recurrence exists (the sum is not
    # constant in n / F is not properly normalized), the term is not WZ-summable.
    rec = zeilberger(rn_n, rn_d, rk_n, rk_d, max_order=1)
    if rec is None or rec["order"] != 1:
        return None
    if not _is_wz_recurrence(rec["coeffs"]):
        return None
    # zeilberger's certificate x(n,k) satisfies a_0·F(n,k) + a_1·F(n+1,k) =
    # G(k+1) − G(k) with G = (x/D_P)·F and D_P = rn_den (order 1). The WZ equation
    # wants the recurrence coefficients [−1, +1] (F(n+1,k) − F(n,k) = ΔG_WZ); since
    # the telescoping is linear and a_0 = −a_1 (the WZ recurrence), scaling by 1/a_1
    # rescales to [−1, +1], so the WZ certificate numerator is x_num / a_1 (the
    # Class-K sign rides through Q). D_P = rn_den at order 1.
    a1_const = rec["coeffs"][1].coeffs[0]           # a_1 is a nonzero Q constant
    inv_a1 = Poly.from_coeffs([Q(1, 1) / a1_const])  # the constant 1/a_1 as a Poly-in-n
    x_num = rec["certificate"].scale_n(inv_a1)
    x_den = rn_d                                    # at order 1, D_P = rn_den(n,k)

    # ── VERIFY: the WZ equation as an exact bivariate rational-function identity.
    if not _verify_wz_equation(rn_n, rn_d, rk_n, rk_d, x_num, x_den):
        return None
    return {"certificate": {"num": x_num, "den": x_den}, "verified": True}


def _is_wz_recurrence(coeffs) -> bool:
    """True iff the order-1 recurrence ``a_0(n)·f(n) + a_1(n)·f(n+1) = 0`` is the
    WZ recurrence ``f(n+1) − f(n) = 0`` (up to an overall nonzero ``ℚ`` scale): the
    two coefficient polynomials are equal-and-opposite constants (``a_0 = −a_1``,
    both nonzero constants in ``n``). That is exactly the "sum is constant in ``n``"
    condition the WZ method certifies."""
    if len(coeffs) != 2:
        return False
    a0, a1 = coeffs[0], coeffs[1]
    if a0.is_zero or a1.is_zero:
        return False
    if a0.degree != 0 or a1.degree != 0:           # both constants in n
        return False
    # a_0 + a_1 == 0 (equal-and-opposite ⇒ f(n+1) = f(n)). Class-K sign via Q.
    return (a0 + a1).is_zero


def _verify_wz_equation(rn_n: BiPoly, rn_d: BiPoly, rk_n: BiPoly, rk_d: BiPoly,
                        x_num: BiPoly, x_den: BiPoly) -> bool:
    """Verify the WZ equation as an EXACT bivariate polynomial identity in ``(n,k)``
    (no solve, no order bound — only the input degrees). Dividing the WZ equation
    ``F(n+1,k)−F(n,k) = G(n,k+1)−G(n,k)`` (``G = (Xn/Xd)·F``) through by ``F(n,k)``
    gives ``r_n − 1 = R(n,k+1)·r_k − R(n,k)``; clearing the denominators yields

        (An − Ad)·(Xd1·Bd·Xd) == (Xn1·Bn·Xd − Xn·Xd1·Bd)·Ad,

    with ``A = r_n = An/Ad``, ``B = r_k = Bn/Bd``, ``R = Xn/Xd``, and ``Xn1/Xd1``
    the ``k→k+1`` shifts. Both sides are built as exact ``BiPoly`` and compared
    coefficient-by-coefficient. Routes through the complete C mirror
    ``srmech_wz_verify`` when present; the pure-Python compare below is the complete
    alternative (and the parity oracle)."""
    nat = _native()
    if nat is not None:
        try:
            got = nat.wz_verify_c(_bi_pairs(rn_n), _bi_pairs(rn_d),
                                  _bi_pairs(rk_n), _bi_pairs(rk_d),
                                  _bi_pairs(x_num), _bi_pairs(x_den))
            if got is not None:
                # The C peer is the COMPLETE verify mirror: a definite 0/1 is
                # trusted both ways (it is a degree-bounded polynomial compare, not
                # an order-capped search). A C "can't" (None) re-decides in pure.
                return bool(got)
        except (RuntimeError, OverflowError, ValueError):
            pass                                    # fall to the pure path

    return _verify_wz_equation_pure(rn_n, rn_d, rk_n, rk_d, x_num, x_den)


def _verify_wz_equation_pure(rn_n: BiPoly, rn_d: BiPoly, rk_n: BiPoly,
                             rk_d: BiPoly, x_num: BiPoly, x_den: BiPoly) -> bool:
    """The exact-ℚ pure-Python WZ-equation polynomial-identity check (the complete,
    ceiling-free alternative to the C peer). See :func:`_verify_wz_equation`."""
    xn1 = x_num.shift_k(1)                           # Xn(n, k+1)
    xd1 = x_den.shift_k(1)                           # Xd(n, k+1)
    # LHS = (An − Ad) · (Xd1 · Bd · Xd)
    lhs = (rn_n - rn_d) * (xd1 * rk_d * x_den)
    # RHS = (Xn1 · Bn · Xd − Xn · Xd1 · Bd) · Ad
    rhs = (xn1 * rk_n * x_den - x_num * xd1 * rk_d) * rn_d
    return lhs == rhs
