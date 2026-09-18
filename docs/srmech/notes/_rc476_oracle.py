"""rc476 (`#T1188`) D1 — the correctly-rounded-root ORACLE, in Python ``int`` only.

No ``libm``, no ``numpy``, no ``math``, no ``fractions``.  Every rounding
question below is decided by an EXACT INTEGER comparison and the integers are
printable, so a reader can re-derive any verdict by hand.

Two independent pieces, deliberately:

* :func:`cr_sqrt_bits` DERIVES the correctly rounded double of ``√(p/q)`` as an
  IEEE-754 bit pattern, by integer ``isqrt`` on a scaled radicand plus one
  midpoint comparison;
* :func:`certify` CHECKS a candidate ``(m, f)`` against the midpoint
  inequalities without using the derivation at all.

The check is not a restatement of the derivation — it is the definition.  A
derivation bug has to survive both, and the can-fail controls in
:func:`self_test` prove the certificate rejects the two neighbours of a known
answer rather than accepting anything handed to it.

Class N (rational anchors) composed with Class K (the pin-slot sign/parity
boundary); no ``abs()`` anywhere.
"""
from __future__ import annotations

import struct

__all__ = [
    "float_bits",
    "bits_float",
    "cr_sqrt_bits",
    "certify",
    "ulps_between",
    "self_test",
]

_MANT = 1 << 52
_MANT_HI = 1 << 53


def _int_isqrt(n: int) -> int:
    """``floor(√n)`` by integer Newton — no ``math``, no float anywhere.

    The oracle refuses to borrow the stdlib here on purpose: ``math.isqrt``
    would be correct, but this module's whole claim is that every step is
    integer arithmetic a reader can re-derive, and importing the answer is not
    re-derivable.  Terminates because the Newton iterate is strictly decreasing
    above the root.
    """
    assert n >= 0, "isqrt: non-negative only"
    if n < 2:
        return n
    r = 1 << ((n.bit_length() + 1) // 2)      # r >= floor(sqrt(n)), 1 bit over
    while True:
        nxt = (r + n // r) >> 1
        if nxt >= r:
            break
        r = nxt
    assert r * r <= n < (r + 1) * (r + 1)
    return r


def float_bits(x: float) -> int:
    """The IEEE-754 binary64 bit pattern of ``x`` as an unsigned integer."""
    return struct.unpack("<Q", struct.pack("<d", x))[0]


def bits_float(bits: int) -> float:
    """The binary64 value of an unsigned 64-bit pattern."""
    return struct.unpack("<d", struct.pack("<Q", bits & ((1 << 64) - 1)))[0]


def _pack(m: int, f: int) -> int:
    """Bit pattern of the POSITIVE normal double ``m * 2**f``, ``m`` 53 bits."""
    assert _MANT <= m < _MANT_HI, "mantissa must be exactly 53 bits"
    biased = f + 52 + 1023
    assert 1 <= biased <= 2046, f"exponent out of the normal range: {biased}"
    return (biased << 52) | (m - _MANT)


def _floor_root_scaled(p: int, q: int, t: int) -> int:
    """``floor(√(p/q) · 2**t)`` exactly, for ANY sign of ``t``.

    ``floor(√(floor(z))) == floor(√z)`` for real ``z >= 0``, so flooring the
    scaled radicand first costs nothing.

    ``t`` must be allowed to go NEGATIVE. A first draft asserted ``t >= 0`` and
    aborted on the max double and on ``hypot(2**500, 2**500)`` — both of whose
    roots need the radicand scaled DOWN, not up. Recorded because the abort
    looked like a defect in the code under test rather than in the instrument.
    """
    assert p > 0 and q > 0
    if t >= 0:
        return _int_isqrt((p << (2 * t)) // q)
    return _int_isqrt(p // (q << (-2 * t)))


def cr_sqrt_bits(p: int, q: int) -> int:
    """The bit pattern of the correctly rounded binary64 nearest ``√(p/q)``.

    ``p, q`` positive integers.  Round-to-nearest, ties-to-even, decided by one
    exact integer comparison ``(2m+1)**2 * q  ⋚  p * 2**(2t)``.
    """
    assert p > 0 and q > 0, "cr_sqrt_bits: positive rational radicand only"
    # First bracket the exponent: pick t so the floor root carries 54 bits.
    t = 53 - ((p.bit_length() - q.bit_length()) // 2)
    v = _floor_root_scaled(p, q, t)
    while v.bit_length() < 54:
        t += 1
        v = _floor_root_scaled(p, q, t)
    while v.bit_length() > 54:
        t -= 1
        v = _floor_root_scaled(p, q, t)
    assert v.bit_length() == 54
    m0 = v >> 1                       # 53 bits: the truncated mantissa
    # √(p/q)·2^(t-1) ⋚ m0 + 1/2  ⟺  p·2^(2t) ⋚ (2m0+1)²·q, shifted whichever
    # way the exponent points so both sides stay integers.
    e = 2 * t
    if e >= 0:
        lhs, rhs = p << e, ((2 * m0 + 1) ** 2) * q
    else:
        lhs, rhs = p, (((2 * m0 + 1) ** 2) * q) << (-e)
    if lhs > rhs:
        m = m0 + 1
    elif lhs < rhs:
        m = m0
    else:                             # exact midpoint: ties-to-even
        m = m0 if (m0 & 1) == 0 else m0 + 1
    f = -(t - 1)
    if m == _MANT_HI:                 # carried out of the binade
        m >>= 1
        f += 1
    return _pack(m, f)


def certify(m: int, f: int, p: int, q: int) -> bool:
    """Is ``m · 2**f`` the correctly rounded double of ``√(p/q)``?

    Decided WITHOUT the derivation, from the midpoint inequalities alone::

        lo · 2**(f-1)  <  √(p/q)  <  (2m+1) · 2**(f-1)

    with ``lo = 2m-1`` normally and ``lo = (4m-1)/2`` at the binade floor
    (``m == 2**52``), where the double below is half as widely spaced.  Both
    sides are squared into integer comparisons.  An exact midpoint is accepted
    only when ``m`` is even (ties-to-even).
    """
    assert _MANT <= m < _MANT_HI and p > 0 and q > 0
    # upper midpoint: p/q  <  (2m+1)**2 · 2**(2f-2)   [<= when 2m+1 even: never]
    hi_num = (2 * m + 1) ** 2 * q
    e_hi = 2 * f - 2
    if e_hi >= 0:
        hi_lhs, hi_rhs = p, hi_num << e_hi
    else:
        hi_lhs, hi_rhs = p << (-e_hi), hi_num
    if hi_lhs > hi_rhs:
        return False
    if hi_lhs == hi_rhs and (m & 1) != 0:
        return False                  # tie that must round to the even neighbour
    # lower midpoint
    if m == _MANT:                    # binade floor: spacing halves below
        lo_num = (4 * m - 1) ** 2 * q
        e_lo = 2 * f - 4
    else:
        lo_num = (2 * m - 1) ** 2 * q
        e_lo = 2 * f - 2
    if e_lo >= 0:
        lo_lhs, lo_rhs = p, lo_num << e_lo
    else:
        lo_lhs, lo_rhs = p << (-e_lo), lo_num
    if lo_lhs < lo_rhs:
        return False
    if lo_lhs == lo_rhs and (m & 1) != 0:
        return False
    return True


def unpack_positive(bits: int) -> tuple:
    """``(m, f)`` with ``value == m * 2**f`` and ``m`` 53 bits, for a positive
    NORMAL double bit pattern."""
    biased = (bits >> 52) & 0x7FF
    assert 1 <= biased <= 2046, "unpack_positive: normal doubles only"
    m = (bits & (_MANT - 1)) | _MANT
    return m, biased - 1023 - 52


def ulps_between(got_bits: int, want_bits: int) -> int:
    """Signed ulp distance for two POSITIVE finite doubles (IEEE ordering is
    monotonic there, so the bit patterns subtract directly).  Class K keeps the
    sign; no ``abs()``."""
    return got_bits - want_bits


def self_test() -> None:
    """Can-fail controls.  Each must FAIL when the code is right."""
    # 1. a known answer: CR(√2) = 0x3ff6a09e667f3bcd
    b = cr_sqrt_bits(2, 1)
    assert b == 0x3FF6A09E667F3BCD, hex(b)
    m, f = unpack_positive(b)
    assert certify(m, f, 2, 1), "certificate rejected the true CR(sqrt 2)"
    # 2. the certificate must REJECT both neighbours
    for nb in (b - 1, b + 1):
        mm, ff = unpack_positive(nb)
        assert not certify(mm, ff, 2, 1), f"certificate accepted a neighbour {hex(nb)}"
    # 3. exact squares are exact
    assert cr_sqrt_bits(4, 1) == float_bits(2.0)
    assert cr_sqrt_bits(1, 4) == float_bits(0.5)
    assert cr_sqrt_bits(9, 16) == float_bits(0.75)
    # 4. the scaled-window search survives extreme magnitudes
    assert cr_sqrt_bits(1, 1 << 2000) == float_bits(bits_float(cr_sqrt_bits(1, 1 << 2000)))
    # 5. round-trip of the packer
    for probe in (1.0, 2.0, 0.5, 1.7320508075688772):
        mm, ff = unpack_positive(float_bits(probe))
        assert _pack(mm, ff) == float_bits(probe)


if __name__ == "__main__":
    self_test()
    print("oracle self-test: OK (CR(sqrt2)=0x%016x, both neighbours rejected)"
          % cr_sqrt_bits(2, 1))
