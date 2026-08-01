"""Exact-rational Bessel primitives — the Class-N kernel the membrane needs.

**Promoted, not rewritten.** These are the Spike #40 exact primitives
(``docs/srmech/notes/spike_40_exact_primitives.py``, GAP-1 / GAP-2) lifted into
the shipped package. The algorithm is unchanged — DLMF 10.2.2 ascending series
summed by an integer recurrence in a declared fixed-point scale, then McMahon
(DLMF 10.21.19) + Newton for the zeros — with ONE deliberate change made for
multi-implementation parity (ADR-0009):

**Sign lives in the orientation, not in the divisor.** The note's loop wrote the
alternation as ``term = -((term * H2) >> bits) // d``, which leans on Python's
FLOOR semantics for ``>>`` and ``//`` on negative integers. C bignums are
sign-magnitude and truncate, so that spelling cannot be made bit-identical
across implementations without emulating Python's floor. Here the running term
is a NON-NEGATIVE magnitude and the alternation is an explicit **Class-K**
sign-flip re-applied by **Class-C** ``reorient`` — every shift and divide then
runs on a magnitude, where floor and truncate agree, so the C peer is
bit-identical by construction. This is also the cascade-honest spelling the
``abs()`` ban asks for: there is no ``abs()`` and no reliance on ALU sign
semantics anywhere below.

**What is NOT claimed.** Nothing here asserts that a Bessel zero is
transcendental, algebraic-irrational, or rational. DLMF 10.21 was fetched and
contains no transcendence statement; Siegel's theorem was never fetched. The
returned values are exact rationals *of declared precision* standing in for
values whose field-theoretic status is **OPEN**, and the ``spectrum_tier`` layer
tags them Tier 3 for exactly that reason.
"""

from __future__ import annotations

from typing import Tuple

from srmech.amsc.cascade.atoms import pin_slot_at_zero, reorient
from srmech.math.q import Q

__all__ = ["bessel_j_fixed", "bessel_zero_fixed"]

#: The default declared fixed-point scale, in bits. The value is a *declared
#: precision*, never a claim about the exactness of the underlying constant.
DEFAULT_SCALE_BITS: int = 256

#: Loop guard. The ascending series converges for every finite argument; a term
#: magnitude that has not underflowed the declared scale by here means the
#: argument is far outside any acoustically meaningful range.
_MAX_TERMS: int = 4000

_FACT = [1]


def _factorial(n: int) -> int:
    """Memoised exact integer factorial (pure int; no math module)."""
    while len(_FACT) <= n:
        _FACT.append(_FACT[-1] * len(_FACT))
    return _FACT[n]


def _check_order(order: int, who: str) -> None:
    if not isinstance(order, int) or isinstance(order, bool) or order < 0:
        raise ValueError(f"{who}: order must be an int >= 0; got {order!r}")


def _check_scale_bits(scale_bits: int, who: str) -> None:
    if (not isinstance(scale_bits, int) or isinstance(scale_bits, bool)
            or scale_bits < 8 or scale_bits > 4096):
        raise ValueError(
            f"{who}: scale_bits must be an int in [8, 4096]; got {scale_bits!r}")


def bessel_j_fixed(order: int,
                   numerator: int,
                   denominator: int,
                   *,
                   scale_bits: int = DEFAULT_SCALE_BITS) -> Tuple[int, int]:
    """``J_order(numerator/denominator)`` as an exact rational of declared scale.

    The DLMF 10.2.2 / Watson (1922) §3.1 ascending series

        ``J_k(x) = Σ_m (−1)^m (x/2)^(2m+k) / (m! (m+k)!)``

    summed by the exact integer recurrence ``t_{m+1} = t_m · (x/2)² /
    ((m+1)(m+k+1))`` in a declared ``2^-scale_bits`` fixed-point scale. The
    series alternates, so truncating when the running term underflows the scale
    bounds the truncation error by that term — i.e. by ``2^-scale_bits``.

    The whole body is integer arithmetic on NON-NEGATIVE magnitudes. The
    alternating sign is carried as an explicit Class-K orientation and
    re-applied by Class-C ``reorient`` at the accumulation, so no shift or
    divide ever sees a negative operand and the C peer agrees bit-for-bit.
    There is no ``abs()``, no float and no math module anywhere in the cascade.

    Args:
        order: the integer Bessel order ``k >= 0``.
        numerator: the argument's numerator; the argument must be ``>= 0``
            (the Class-K real-axis domain — use the reflection
            ``J_k(−x) = (−1)^k J_k(x)`` for the other half-line).
        denominator: the argument's denominator, ``> 0``.
        scale_bits: the DECLARED fixed-point scale, in bits. Default 256.

    Returns:
        ``(num, den)`` with ``den == 2**scale_bits`` — the exact rational value
        at the declared precision. NOT a claim that ``J_k(x)`` is rational.

    Raises:
        ValueError: bad order, non-positive denominator, negative argument, an
            out-of-range ``scale_bits``, or a series that did not terminate.
    """
    _check_order(order, "bessel_j_fixed")
    _check_scale_bits(scale_bits, "bessel_j_fixed")
    if not isinstance(denominator, int) or isinstance(denominator, bool) or denominator <= 0:
        raise ValueError(
            f"bessel_j_fixed: denominator must be a positive int; got {denominator!r}")
    if not isinstance(numerator, int) or isinstance(numerator, bool):
        raise ValueError(
            f"bessel_j_fixed: numerator must be an int; got {numerator!r}")
    arg_orientation, arg_magnitude = pin_slot_at_zero(numerator)
    if arg_orientation < 0:
        raise ValueError(
            "bessel_j_fixed: argument must be >= 0 (the Class-K real-axis "
            f"domain); got {numerator}/{denominator}. Use the reflection "
            "J_k(-x) = (-1)^k J_k(x).")

    scale = 1 << scale_bits

    # Native path (bit-identical by construction — see the module docstring on
    # why the sign lives in the orientation). Returns None when the symbol is
    # absent, and the pure-Python body below is then the complete alternative
    # AND the parity oracle.
    from srmech import _native
    native = _native.bessel_j_fixed_c(order, arg_magnitude, denominator,
                                      scale_bits)
    if native is not None:
        return native, scale

    # (x/2) and (x/2)^2 on the declared grid — both non-negative.
    half = (arg_magnitude * scale) // (2 * denominator)
    half_sq = (half * half) >> scale_bits

    # The leading term (x/2)^k / k!, as a magnitude.
    term = scale
    for _ in range(order):
        term = (term * half) >> scale_bits
    term = term // _factorial(order)

    total = term                       # m = 0 carries orientation +1
    orientation = +1
    m = 0
    while True:
        _zero_orientation, term = pin_slot_at_zero(term)
        if term == 0:
            break
        term = (term * half_sq) >> scale_bits
        term = term // ((m + 1) * (m + order + 1))
        # Class-K: the alternation IS a sign-flip at the term boundary.
        # Class-C: re-apply the captured orientation to the magnitude.
        orientation = -orientation
        total = total + reorient(term, orientation=orientation)
        m += 1
        if m > _MAX_TERMS:
            raise ValueError(
                f"bessel_j_fixed: series did not terminate within {_MAX_TERMS} "
                f"terms for order={order}, x={numerator}/{denominator}")
    return total, scale


def _bessel_dj(order: int, x: "Q", scale_bits: int) -> "Q":
    """``J_order'(x)`` via DLMF 10.6.1 — ``J_k' = (J_{k-1} − J_{k+1}) / 2``,
    with ``J_0' = −J_1``. Exact ``Q`` throughout."""
    if order == 0:
        num, den = bessel_j_fixed(1, x.numerator, x.denominator,
                                  scale_bits=scale_bits)
        return Q(0, 1) - Q(num, den)
    lo_num, lo_den = bessel_j_fixed(order - 1, x.numerator, x.denominator,
                                    scale_bits=scale_bits)
    hi_num, hi_den = bessel_j_fixed(order + 1, x.numerator, x.denominator,
                                    scale_bits=scale_bits)
    return (Q(lo_num, lo_den) - Q(hi_num, hi_den)) / Q(2, 1)


def _quantise(q: "Q", scale_bits: int) -> "Q":
    """Snap an exact ``Q`` back onto the declared ``2^-scale_bits`` grid, so a
    Newton iterate cannot grow an unbounded denominator. Sign is handled as a
    Class-K split + Class-C re-application — never ``abs()``, and never a
    negative floor-divide (which C would truncate instead)."""
    scale = 1 << scale_bits
    orientation, magnitude = pin_slot_at_zero(q)
    snapped = (magnitude.numerator * scale) // magnitude.denominator
    return Q(reorient(snapped, orientation=orientation), scale)


def _pi_exact(scale_bits: int) -> "Q":
    """π as an exact rational at (a little more than) the declared scale, via
    the shipped Chudnovsky digit cascade. The digits are integers; the only
    thing that happens here is placing the decimal point exactly."""
    from srmech.math import rational as _rational
    # ~0.302 decimal digits per bit; ask for a comfortable margin.
    digits = (scale_bits * 4) // 10 + 12
    text = _rational.pi_chudnovsky_digits(digits).replace(".", "")
    return Q(int(text), 10 ** (len(text) - 1))


def bessel_zero_fixed(order: int,
                      index: int,
                      *,
                      scale_bits: int = DEFAULT_SCALE_BITS,
                      newton_steps: int = 8) -> Tuple[int, int]:
    """The ``index``-th positive zero of ``J_order`` at the declared precision.

    McMahon's asymptotic start (DLMF 10.21.19)

        ``j ≈ β − (μ−1)/(8β)``,  ``β = π(4·index + 2·order − 1)/4``,
        ``μ = 4·order²``

    refined by exact-rational Newton on :func:`bessel_j_fixed`, with the
    derivative from DLMF 10.6.1. Every iterate is snapped back onto the declared
    ``2^-scale_bits`` grid so the denominator stays bounded; the body is exact
    ``Q`` and the only division by a computed quantity is the Newton quotient.

    **This asserts nothing about the true zero.** It is a rational of declared
    precision. Whether Bessel zeros are transcendental or algebraic-irrational
    is an OPEN question in this project — DLMF 10.21 states nothing on it, and
    no source establishing otherwise has been fetched and attested. The
    ``spectrum_tier`` layer therefore tags a membrane spectrum **Tier 3**, and a
    commensurability verdict over one returns **"open"**, never "harmonic".

    Args:
        order: the integer Bessel order ``n >= 0``.
        index: which positive zero, ``1``-based (``1`` = the first).
        scale_bits: the DECLARED fixed-point scale, in bits. Default 256.
        newton_steps: Newton refinements after the McMahon start. Default 8.

    Returns:
        ``(num, den)`` on the declared ``2^-scale_bits`` grid. ``den`` is a
        power of two ``2**k`` with ``k <= scale_bits``, NOT unconditionally
        ``2**scale_bits``: the value is an exact :class:`~srmech.math.q.Q` and
        therefore comes back REDUCED, so an even numerator cancels powers of
        two out of the denominator. Measured — ``bessel_zero_fixed(0, 1,
        scale_bits=64)`` returns ``(5545150200591220465, 2305843009213693952)``
        and ``2305843009213693952 == 2**61``. (This differs from
        :func:`bessel_j_fixed`, which returns the accumulator and its scale
        directly and so really does always carry ``den == 2**scale_bits``.)

    Raises:
        ValueError: bad order / index / scale_bits / newton_steps.
    """
    _check_order(order, "bessel_zero_fixed")
    _check_scale_bits(scale_bits, "bessel_zero_fixed")
    if not isinstance(index, int) or isinstance(index, bool) or index < 1:
        raise ValueError(
            f"bessel_zero_fixed: index must be an int >= 1 (1-based); got {index!r}")
    if (not isinstance(newton_steps, int) or isinstance(newton_steps, bool)
            or newton_steps < 1 or newton_steps > 64):
        raise ValueError(
            f"bessel_zero_fixed: newton_steps must be an int in [1, 64]; "
            f"got {newton_steps!r}")

    pi = _pi_exact(scale_bits)
    beta = pi * Q(4 * index + 2 * order - 1, 4)
    mu = 4 * order * order
    x = beta - Q(mu - 1, 8) / beta
    x = _quantise(x, scale_bits)
    for _ in range(newton_steps):
        num, den = bessel_j_fixed(order, x.numerator, x.denominator,
                                  scale_bits=scale_bits)
        slope = _bessel_dj(order, x, scale_bits)
        if slope == 0:
            raise ValueError(
                f"bessel_zero_fixed: Newton stalled (J_{order}' = 0) at "
                f"order={order}, index={index}")
        x = x - Q(num, den) / slope
        x = _quantise(x, scale_bits)
    return x.numerator, x.denominator
