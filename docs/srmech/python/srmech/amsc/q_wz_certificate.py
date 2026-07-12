"""srmech.amsc.q_wz_certificate — the q-analog of the Wilf–Zeilberger pair method
(the THIRD and FINAL public op of the q-hypergeometric F929 reduction row, the
q-analog of the §76 ``wz_certificate``). It CLOSES the q-row (q_gosper →
q_zeilberger → q_wz_certificate) AND the whole multivariate + q-hypergeometric
reduction-theory arc.

Where :func:`srmech.amsc.q_gosper.q_gosper` does INDEFINITE q-summation and
:func:`srmech.amsc.q_zeilberger.q_zeilberger` FINDS the definite-q-sum recurrence,
``q_wz_certificate`` **PROVES a terminating q-hypergeometric identity** — it produces
AND verifies the *q-WZ certificate* of a constant q-sum ``Σ_k F(n,k) = const``
(T.H. Koornwinder, "On Zeilberger's algorithm and its q-analogue," J. Comput. Appl.
Math. 48 (1993) 91–111 — the same paper :class:`~srmech.amsc.qpoly.QPoly` /
:func:`~srmech.amsc.q_gosper.q_gosper` / :func:`~srmech.amsc.q_zeilberger.q_zeilberger`
cite; the q-WZ pair method anchor is H. Wilf & D. Zeilberger, "An algorithmic proof
theory for hypergeometric (ordinary and q) multisum/integral identities," Invent.
Math. 108 (1992) 575–633; textbook anchor Gasper & Rahman, *Basic Hypergeometric
Series*). It is the q-analog of the ordinary :func:`srmech.amsc.wz_certificate.
wz_certificate`.

The q-WZ method is **q-Zeilberger specialized to the forced n-recurrence**
``f(n+1) − f(n) = 0`` (the recurrence coefficient vector ``[−1, +1]``): the
normalized q-summand ``F(n,k)`` of an identity ``Σ_k F(n,k) = const`` satisfies
``Σ_k [F(n+1,k) − F(n,k)] = 0``, and the q-WZ certificate is the rational function
``R(X,Y)`` (``X = qⁿ``, ``Y = qᵏ``) whose companion ``G(n,k) = R(X,Y)·F(n,k)`` makes
that q-sum q-telescope:

    F(n+1,k) − F(n,k) = G(n,k+1) − G(n,k)            (the **q-WZ equation**)

where ``G(n,k+1) = (σ_y R)·(σ_y F)`` and ``σ_y : Y ↦ q·Y`` is the q-shift in ``k``.

Input — the two **term ratios** of the proper q-hypergeometric term ``F``, each a
rational function of ``(X, Y) = (qⁿ, qᵏ)`` given by a numerator / denominator pair of
:class:`~srmech.amsc.qbipoly.QBiPoly` (exact-``ℚ[q]`` bivariate in ``(X,Y)`` — the
SAME operands :func:`~srmech.amsc.q_zeilberger.q_zeilberger` takes):

  * ``r_n(X,Y) = F(n+1,k) / F(n,k)``   (the ``rn_num`` / ``rn_den`` operands)
  * ``r_k(X,Y) = F(n,k+1) / F(n,k)``   (the ``rk_num`` / ``rk_den`` operands)

The op does BOTH halves of the q-WZ method:

  1. **FIND** the certificate ``R(X,Y)`` (a rational function, as a ``QBiPoly``
     num/den pair). This is q-Gosper-in-``k`` applied to ``F(n+1,k) − F(n,k)``, i.e.
     EXACTLY what :func:`~srmech.amsc.q_zeilberger.q_zeilberger` produces at the
     forced recurrence ``[−1, +1]`` — so the FIND step reuses the rc56 q-creative-
     telescoping machinery (``q_zeilberger`` with ``max_order=1``; the order-1
     q-recurrence of ``F`` IS ``f(n+1) − f(n) = 0`` precisely when the identity q-sum
     is constant in ``n``, and its certificate is the q-WZ certificate). The
     certificate ``x(X,Y)`` comes back over the shared q-Gosper denominator
     ``D_P = rn_den`` (the order-1 ``D_P``), scaled so the q-recurrence is exactly
     ``[−1, +1]``.

  2. **VERIFY** that the q-WZ equation holds as an EXACT bivariate rational-function
     identity in ``(X,Y)`` — a purely algebraic check via the ``QBiPoly`` toolkit,
     **no solve, no order bound** (bounded only by input degree). Dividing the q-WZ
     equation through by ``F(n,k)`` gives the rational identity

         r_n(X,Y) − 1 = R(X,qY)·r_k(X,Y) − R(X,Y),

     and clearing denominators turns it into the single polynomial identity

         (An − Ad)·(σ_y(Xd)·Bd·Xd)
            == (σ_y(Xn)·Bn·Xd − Xn·σ_y(Xd)·Bd)·Ad,

     where ``r_n = An/Ad``, ``r_k = Bn/Bd``, ``R = Xn/Xd`` and ``σ_y(Xn)`` /
     ``σ_y(Xd)`` are the ``Y ↦ q·Y`` q-shifts. This is the NEW primitive —
     ``srmech_q_wz_verify`` is its complete C mirror (degree-bounded, NOT order-
     bounded; unlike the rc42/rc56 order-≤1 native peers this is a FULL mirror that
     can verify any returned certificate natively).

Returns ``{"certificate": {"num": QBiPoly, "den": QBiPoly}, "verified": True}`` when
a q-WZ certificate exists AND the q-WZ equation verifies, else ``None`` (the term is
not q-WZ-summable / the identity is not a constant q-sum).

The whole pipeline stays EXACT over ``ℚ[q]`` — every polynomial is a
:class:`~srmech.amsc.qbipoly.QBiPoly` (each coefficient a
:class:`~srmech.amsc.qpoly.QPoly` over the bigint :class:`~srmech.amsc.poly.Poly`, no
magnitude ceiling), the verify a coefficient-by-coefficient compare. There is NO
float anywhere; sign is the **Class-K** pin-slot via the ``Q`` / ``Poly`` sign-branch
(never an ALU ``abs()``); no ``math`` module, no numpy. This is the **q-row CLOSER**
of the F929 closure-dispatch: q_gosper (indefinite) → q_zeilberger (recurrence) →
q_wz_certificate (proof) — each built on the last.

C peer: ``srmech_q_wz_verify`` (``c/src/srmech_q_wz_verify.c``) is the COMPLETE C
mirror of the VERIFY half — the exact bivariate-``ℚ[q]`` rational-function identity
check, bounded only by input degree (NOT by any order; unlike the rc56 q-Zeilberger
order-≤1 peer this is a full mirror). It composes a compact exact-``ℚ[q]`` q-poly /
QBiPoly toolkit over caller-arena ``srmech_bigint`` into one JPL-clean symbol.
``q_wz_certificate``'s verify routes through it when ``HAS_NATIVE``
(:func:`srmech.amsc._native.has_native_q_wz_verify`); the pure-Python verify here is
the COMPLETE alternative (and the byte-identical parity oracle). The FIND step
composes the existing ``srmech_q_zeilberger`` machinery (native-accelerated when
present, pure-Python the complete decider).
"""

from __future__ import annotations

from typing import Dict, Optional

from .poly import Poly
from .q import Q
from .qpoly import QPoly
from .qbipoly import QBiPoly
from .q_zeilberger import q_zeilberger

__all__ = ["q_wz_certificate"]

_POLY_ONE = Poly.one()


def _native():
    """The native ``_native`` module IF the rc57 ``srmech_q_wz_verify`` peer is
    present and bound, else ``None`` — so the verify dispatches to C when available
    and falls cleanly to the pure-Python check (the complete alternative + the parity
    oracle) otherwise. Imported lazily to avoid a bootstrap cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    probe = getattr(nat, "has_native_q_wz_verify", None)
    return nat if (probe is not None and probe()) else None


def _qb_pairs(b: QBiPoly):
    """A ``QBiPoly`` → the ``(y_xlow[], rows)`` bridge form the C peer consumes — the
    SAME per-Y-cell QPoly-row form :func:`srmech.amsc.qbipoly._qb_pairs` emits (the
    bridge the q-Zeilberger peer also uses)."""
    from .qbipoly import _qb_pairs as _f
    return _f(b)


def q_wz_certificate(rn_num, rn_den, rk_num, rk_den) -> Optional[Dict[str, object]]:
    """Prove a terminating q-hypergeometric identity by its q-Wilf–Zeilberger pair.

    ``rn_num`` / ``rn_den`` are the numerator / denominator of the ``n``-term-ratio
    ``r_n(X,Y) = F(n+1,k)/F(n,k)`` (``X = qⁿ``, ``Y = qᵏ``); ``rk_num`` / ``rk_den``
    likewise for the ``k``-term-ratio ``r_k(X,Y) = F(n,k+1)/F(n,k)``. Each is a
    :class:`~srmech.amsc.qbipoly.QBiPoly` (exact bivariate-``ℚ[q]`` in ``(X,Y)``), or a
    :class:`~srmech.amsc.qpoly.QPoly` (read as a polynomial in ``Y = qᵏ`` alone), a
    :class:`~srmech.amsc.poly.Poly` in ``q`` (a scalar), or an ascending-``Y``-degree
    ``QPoly`` sequence. ``F`` must be the NORMALIZED q-summand of a constant identity
    (``Σ_k F(n,k)`` independent of ``n``).

    FINDs the q-WZ certificate ``R(X,Y)`` (q-Gosper-in-``k`` of ``F(n+1,k)−F(n,k)`` =
    :func:`~srmech.amsc.q_zeilberger.q_zeilberger` at the forced recurrence
    ``[−1,+1]``) and VERIFIES the q-WZ equation ``F(n+1,k)−F(n,k) = G(n,k+1)−G(n,k)``
    (``G = R·F``, ``G(n,k+1) = (σ_y R)·(σ_y F)``) as an EXACT bivariate rational-
    function identity — no solve, no order bound.

    Returns ``{"certificate": {"num": QBiPoly, "den": QBiPoly}, "verified": True}``
    when a q-WZ certificate exists AND verifies, else ``None`` (the term is not
    q-WZ-summable). Exact over ``ℚ[q]`` (bigint, no magnitude ceiling); no float, no
    ``abs()`` (the sign is the Class-K pin-slot), no ``math`` / numpy. See the module
    docstring for the full q-WZ pipeline. ``rn_den`` / ``rk_den`` must be nonzero (a
    term ratio has a nonzero denominator) — ``ValueError`` otherwise."""
    rn_n = QBiPoly.coerce(rn_num)
    rn_d = QBiPoly.coerce(rn_den)
    rk_n = QBiPoly.coerce(rk_num)
    rk_d = QBiPoly.coerce(rk_den)
    if rn_d.is_zero or rk_d.is_zero:
        raise ValueError(
            "q_wz_certificate: the term-ratio denominators r_n den / r_k den must be "
            "NONZERO bivariate-q polynomials")

    # ── FIND: the q-WZ certificate is the order-1 (forced f(n+1)−f(n)=0) q-Zeilberger
    # certificate. A definite q-sum that is constant in n IS the order-1 recurrence
    # f(n+1) − f(n) = 0 (coeffs ∝ [−1, +1]); q_zeilberger at max_order=1 returns that
    # recurrence + its certificate. If no order-≤1 q-recurrence exists (the sum is not
    # constant in n / F is not properly normalized), the term is not q-WZ-summable.
    # A q-Zeilberger that DECLINES an input it cannot reduce (the rc56 pure path raises
    # on a term-ratio shape outside its supported class — e.g. a non-q-shift-monomial
    # n-denominator) is an HONEST "not q-WZ-summable on this path": catch it and return
    # None rather than propagating (the verify is the proof of record, not the find).
    try:
        rec = q_zeilberger(rn_n, rn_d, rk_n, rk_d, max_order=1)
    except (ValueError, ZeroDivisionError, OverflowError):
        return None
    if rec is None or rec["order"] != 1:
        return None
    if not _is_wz_recurrence(rec["coeffs"]):
        return None
    # q_zeilberger's certificate x(X,Y) satisfies a_0·F(n,k) + a_1·F(n+1,k) =
    # G(k+1) − G(k) with G = (x/D_P)·F and D_P = rn_den (order 1). The q-WZ equation
    # wants the recurrence coefficients [−1, +1] (F(n+1,k) − F(n,k) = Δ_q G); since the
    # q-telescoping is linear and a_0 = −a_1 (the WZ recurrence), scaling by 1/a_1
    # rescales to [−1, +1], so the q-WZ certificate numerator is x_num / a_1 (the
    # Class-K sign rides through Q). D_P = rn_den at order 1.
    a1_const = rec["coeffs"][1]                      # a_1, a nonzero QPoly constant
    inv_a1 = _qpoly_constant_inverse(a1_const)       # 1/a_1 as a constant QPoly (or None)
    if inv_a1 is None:
        return None
    x_num = rec["certificate"].scale_x(inv_a1)
    x_den = rn_d                                     # at order 1, D_P = rn_den(X,Y)

    # ── VERIFY: the q-WZ equation as an exact bivariate rational-function identity.
    if not _verify_q_wz_equation(rn_n, rn_d, rk_n, rk_d, x_num, x_den):
        return None
    return {"certificate": {"num": x_num, "den": x_den}, "verified": True}


def _is_wz_recurrence(coeffs) -> bool:
    """True iff the order-1 q-recurrence ``a_0(X)·f(n) + a_1(X)·f(n+1) = 0`` is the
    q-WZ recurrence ``f(n+1) − f(n) = 0`` (up to an overall nonzero ``ℚ(q)`` scale):
    the two ``QPoly`` coefficients are equal-and-opposite constants in ``X`` AND in
    ``q`` (``a_0 = −a_1``, both nonzero constants ``X⁰`` cells whose ``ℚ[q]`` content
    is a nonzero CONSTANT in ``q``). That is exactly the "q-sum is constant in ``n``"
    condition the q-WZ method certifies."""
    if len(coeffs) != 2:
        return False
    a0, a1 = coeffs[0], coeffs[1]
    if a0.is_zero or a1.is_zero:
        return False
    # both must be single X⁰ cells whose ℚ[q] content is a CONSTANT in q (degree 0):
    # a genuine X- or q-dependence in either coefficient is NOT the forced [−1, +1]
    # WZ recurrence (it would be a non-constant sum in n / a deeper q-recurrence).
    if not (_is_const_in_x_and_q(a0) and _is_const_in_x_and_q(a1)):
        return False
    # a_0 + a_1 == 0 (equal-and-opposite ⇒ f(n+1) = f(n)). Class-K sign via Q / Poly.
    return (a0 + a1).is_zero


def _is_const_in_x_and_q(p: QPoly) -> bool:
    """True iff ``p`` is a single ``X⁰`` cell whose ``ℚ[q]`` coefficient is a nonzero
    CONSTANT (degree-0 in ``q``) — i.e. ``p`` is a nonzero rational SCALAR. The forced
    q-WZ recurrence coefficients ``[−1, +1]`` are exactly such scalars."""
    if p.is_zero:
        return False
    if p.x_low != 0 or len(p.cells) != 1:
        return False
    return p.cells[0].degree == 0


def _qpoly_constant_inverse(p: QPoly):
    """The reciprocal ``1/p`` of a nonzero CONSTANT ``QPoly`` (a single ``X⁰`` cell, a
    ``ℚ`` scalar) as a constant ``QPoly``, or ``None`` if ``p`` is not such a scalar.
    Used to rescale the q-Zeilberger order-1 certificate by ``1/a_1`` so the q-WZ
    recurrence is exactly ``[−1, +1]``. The Class-K sign rides through the ``Q``
    reciprocal."""
    if not _is_const_in_x_and_q(p):
        return None
    coeff = p.cells[0]                                # the ℚ[q] coefficient (degree 0)
    c0 = coeff.coeffs[0]                              # the single Q scalar
    if c0 == 0:
        return None
    inv = Q(1, 1) / c0                                # exact Q reciprocal (Class-K sign)
    return QPoly.from_q_poly(Poly.from_coeffs([inv]))


def _verify_q_wz_equation(rn_n: QBiPoly, rn_d: QBiPoly, rk_n: QBiPoly, rk_d: QBiPoly,
                          x_num: QBiPoly, x_den: QBiPoly) -> bool:
    """Verify the q-WZ equation as an EXACT bivariate polynomial identity in ``(X,Y)``
    (no solve, no order bound — only the input degrees). Dividing the q-WZ equation
    ``F(n+1,k)−F(n,k) = G(n,k+1)−G(n,k)`` (``G = (Xn/Xd)·F``, ``G(n,k+1) = (σ_y Xn /
    σ_y Xd)·(σ_y F)``) through by ``F(n,k)`` gives ``r_n − 1 = R(X,qY)·r_k − R(X,Y)``;
    clearing the denominators yields

        (An − Ad)·(σ_y(Xd)·Bd·Xd) == (σ_y(Xn)·Bn·Xd − Xn·σ_y(Xd)·Bd)·Ad,

    with ``r_n = An/Ad``, ``r_k = Bn/Bd``, ``R = Xn/Xd``, and ``σ_y(Xn)`` /
    ``σ_y(Xd)`` the ``Y ↦ q·Y`` q-shifts. Both sides are built as exact ``QBiPoly``
    and compared coefficient-by-coefficient. Routes through the complete C mirror
    ``srmech_q_wz_verify`` when present; the pure-Python compare below is the complete
    alternative (and the parity oracle)."""
    nat = _native()
    if nat is not None:
        try:
            got = nat.q_wz_verify_c(_qb_pairs(rn_n), _qb_pairs(rn_d),
                                    _qb_pairs(rk_n), _qb_pairs(rk_d),
                                    _qb_pairs(x_num), _qb_pairs(x_den))
            if got is not None:
                # The C peer is the COMPLETE verify mirror: a definite 0/1 is trusted
                # both ways (it is a degree-bounded polynomial compare, not an order-
                # capped search). A C "can't" (None) re-decides in pure.
                return bool(got)
        except (RuntimeError, OverflowError, ValueError):
            pass                                    # fall to the pure path

    return _verify_q_wz_equation_pure(rn_n, rn_d, rk_n, rk_d, x_num, x_den)


def _verify_q_wz_equation_pure(rn_n: QBiPoly, rn_d: QBiPoly, rk_n: QBiPoly,
                               rk_d: QBiPoly, x_num: QBiPoly, x_den: QBiPoly) -> bool:
    """The exact-ℚ[q] pure-Python q-WZ-equation polynomial-identity check (the
    complete, ceiling-free alternative to the C peer). See
    :func:`_verify_q_wz_equation`."""
    xn1 = x_num.qshift_y(1)                           # σ_y(Xn) : Y ↦ q·Y on Xn
    xd1 = x_den.qshift_y(1)                           # σ_y(Xd)
    # LHS = (An − Ad) · (σ_y(Xd) · Bd · Xd)
    lhs = (rn_n - rn_d) * (xd1 * rk_d * x_den)
    # RHS = (σ_y(Xn) · Bn · Xd − Xn · σ_y(Xd) · Bd) · Ad
    rhs = (xn1 * rk_n * x_den - x_num * xd1 * rk_d) * rn_d
    return lhs == rhs
