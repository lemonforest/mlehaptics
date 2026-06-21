"""srmech.amsc.qi — the framework-native EXACT-complex scalar carrier (``Qi``).

The exact cousin of :class:`srmech.amsc.complex128.Complex128`. Where
``Complex128`` carries a **float** complex scalar (two ``float64``, the display
boundary for genuinely-irrational complex values), ``Qi`` carries an **exact**
Gaussian rational — ``Qi = (re: Q, im: Q)``, two exact :class:`srmech.amsc.q.Q`
rationals — the exact :class:`numbers.Complex` over ℚ. It completes the carrier
family: ``Q`` is the exact real (``numbers.Rational``), ``Complex128`` the float
complex, and ``Qi`` the **exact** complex that was the gap.

**The sign sector is a Klein-4 quadrant.** The four sign-quadrants of a complex
value — ``(++) (-+) (+-) (--)`` — ARE the group ℤ₂×ℤ₂ = Klein-4 (the MFO
§VII.4.1.7 4-way, ``hdc.KLEIN4_STATES``). So ``Qi`` is **klein4 quadrant ⊗
magnitude**: :meth:`quadrant` returns a Klein-4 element (an int in
``KLEIN4_STATES``, ``bit0 = re<0``, ``bit1 = im<0``) and :meth:`conjugate` — the
Class-K sign-flip on ``im`` — is exactly XOR with the imaginary bit
(``quadrant() ^ 2``). Chirality (Class C/K) is kept separate from magnitude, the
srmech split, and :meth:`from_quadrant_magnitudes` round-trips a quadrant + two
non-negative magnitudes back to the value exactly.

Everything stays exact: ``+`` / ``-`` / ``*`` / ``/`` are the Gaussian-rational
identities over the Class-N ``Q`` arithmetic — ``(a+bi)(c+di) = (ac-bd)+(ad+bc)i``
(Class M bilinear bind ∘ Class C cross-term order), division through the real
norm ``c²+d²`` (Class N). ``complex(qi)`` is the one boundary collapse back to the
builtin; ``abs(qi)`` rides the Class-N :func:`srmech.amsc.rational.sqrt`
(exact ``Q`` when the squared modulus is a perfect rational square, else the
stay-rational boundary). No ``math`` module, no numpy.
"""

from __future__ import annotations

import numbers

from . import rational as _rational
from .hdc import KLEIN4_STATES
from .q import Q

__all__ = ["Qi"]

_Q_ZERO = Q(0, 1)
_Q_ONE = Q(1, 1)


def _to_q(value):
    """Coerce ``value`` to an exact :class:`~srmech.amsc.q.Q`, or ``None`` if it
    is not an exact-rational-coercible scalar."""
    if isinstance(value, Q):
        return value
    if isinstance(value, bool):
        return Q(int(value), 1)
    if isinstance(value, int):
        return Q(value, 1)
    if isinstance(value, float):
        try:
            return Q.from_float(value)               # exact ratio of the float
        except (OverflowError, ValueError):
            return None
    if (isinstance(value, (tuple, list)) and len(value) == 2
            and isinstance(value[0], int) and isinstance(value[1], int)
            and value[1] != 0):
        return Q(value[0], value[1])
    pair = getattr(value, "as_pair", None) or getattr(value, "as_integer_ratio", None)
    if pair is not None:
        try:
            n, d = pair()
            return Q(int(n), int(d))
        except (TypeError, ValueError, ZeroDivisionError):
            return None
    return None


def _int_exponent(exp):
    """The int value of ``exp`` if it is an integer-valued exponent (a plain
    ``int``, ``bool`` excluded, or a rational with denominator 1), else ``None``
    — matching ``fractions.Fraction`` (``** 2.0`` is a float, not exact)."""
    if isinstance(exp, bool):
        return None
    if isinstance(exp, int):
        return exp
    den = getattr(exp, "denominator", None)
    num = getattr(exp, "numerator", None)
    if den is not None and num is not None:
        try:
            if den == 1:
                return int(num)
        except (TypeError, ValueError):
            return None
    return None


def _coerce(value):
    """Coerce ``value`` to a ``Qi`` for arithmetic / comparison, or ``None`` (so
    the dunder returns ``NotImplemented`` and Python tries the reflected op)."""
    if isinstance(value, Qi):
        return value
    if isinstance(value, complex):
        try:
            return Qi(Q.from_float(value.real), Q.from_float(value.imag))
        except (OverflowError, ValueError):
            return None
    q = _to_q(value)
    return None if q is None else Qi(q, _Q_ZERO)


class Qi:
    """An exact Gaussian-rational complex scalar — two exact ``Q`` (re, im), the
    framework-native EXACT complex carrier. Collapses to the builtin ``complex``
    only via ``complex(z)``. See the module docstring."""

    __slots__ = ("_re", "_im")

    def __init__(self, re=_Q_ZERO, im=_Q_ZERO) -> None:
        if isinstance(re, Qi):                        # Qi(another_qi)
            self._re, self._im = re._re, re._im
            return
        r = _to_q(re)
        i = _to_q(im)
        if r is None or i is None:
            raise TypeError(
                f"Qi(re, im) takes exact-rational re/im; got "
                f"{type(re).__name__}, {type(im).__name__}")
        self._re, self._im = r, i

    # ── construction helpers ────────────────────────────────────────────────
    @classmethod
    def from_pairs(cls, re_pair, im_pair) -> "Qi":
        """Build from two ``(num, den)`` integer pairs."""
        return cls(Q.from_pair(re_pair), Q.from_pair(im_pair))

    @classmethod
    def from_quadrant_magnitudes(cls, quadrant: int, mag_re, mag_im) -> "Qi":
        """Reconstruct from a **Klein-4 quadrant** + two non-negative magnitudes —
        the inverse of :meth:`quadrant` + ``abs(re)`` / ``abs(im)``. ``quadrant``
        bit0 applies the ``re`` sign, bit1 the ``im`` sign (Class-C orientation)."""
        if quadrant not in KLEIN4_STATES:
            raise ValueError(f"quadrant must be a Klein-4 element 0..3; got {quadrant!r}")
        r = _to_q(mag_re)
        i = _to_q(mag_im)
        if r is None or i is None:
            raise TypeError("magnitudes must be exact-rational")
        if r < 0 or i < 0:
            raise ValueError("magnitudes must be non-negative")
        if quadrant & 1:
            r = -r
        if quadrant & 2:
            i = -i
        return cls(r, i)

    # ── exact components (each a Q) ─────────────────────────────────────────
    @property
    def real(self) -> Q:
        return self._re

    @property
    def imag(self) -> Q:
        return self._im

    def as_pairs(self):
        """The exact ``((re_num, re_den), (im_num, im_den))`` integer pairs."""
        return (self._re.as_pair(), self._im.as_pair())

    def __iter__(self):
        """Unpack as ``re, im = z`` (each a ``Q``)."""
        yield self._re
        yield self._im

    # ── the boundary collapse to the builtin complex ────────────────────────
    def __complex__(self) -> complex:
        return complex(float(self._re), float(self._im))

    # ── reprs ───────────────────────────────────────────────────────────────
    def __repr__(self) -> str:
        return f"Qi({self._re!r}, {self._im!r})"

    def __str__(self) -> str:
        # Class-K sign-branch (never an ALU abs): split the im sign from its
        # magnitude via a Q negation, never `abs()` (per the cascade-honesty
        # discipline — sign is the Class-K pin-slot, not an ALU op).
        nonneg = self._im >= 0
        mag = self._im if nonneg else -self._im
        return f"({self._re}{'+' if nonneg else '-'}{mag}i)"

    def __bool__(self) -> bool:
        return bool(self._re) or bool(self._im)

    def __hash__(self) -> int:
        # A real Qi (im == 0) hashes like its Q (so Qi(3,4) == Q(3,4) == 0.75 all
        # hash equal); a genuinely-complex Qi mirrors the builtin complex it ==.
        if self._im == 0:
            return hash(self._re)
        try:
            return hash(complex(self))
        except OverflowError:
            return hash((self._re.as_pair(), self._im.as_pair()))

    def __eq__(self, other) -> bool:
        z = _coerce(other)
        if z is None:
            return NotImplemented
        return self._re == z._re and self._im == z._im

    def __ne__(self, other) -> bool:
        z = _coerce(other)
        if z is None:
            return NotImplemented
        return self._re != z._re or self._im != z._im

    # ── exact Gaussian-rational arithmetic (Class M bind ∘ Class C order) ───
    def __add__(self, other):
        z = _coerce(other)
        if z is None:
            return NotImplemented
        return Qi(self._re + z._re, self._im + z._im)

    __radd__ = __add__

    def __sub__(self, other):
        z = _coerce(other)
        if z is None:
            return NotImplemented
        return Qi(self._re - z._re, self._im - z._im)

    def __rsub__(self, other):
        z = _coerce(other)
        if z is None:
            return NotImplemented
        return Qi(z._re - self._re, z._im - self._im)

    def __mul__(self, other):
        z = _coerce(other)
        if z is None:
            return NotImplemented
        a, b, c, d = self._re, self._im, z._re, z._im
        return Qi(a * c - b * d, a * d + b * c)       # (ac-bd) + (ad+bc)i

    __rmul__ = __mul__

    def __truediv__(self, other):
        z = _coerce(other)
        if z is None:
            return NotImplemented
        return self._divide_by(z)

    def __rtruediv__(self, other):
        z = _coerce(other)
        if z is None:
            return NotImplemented
        return z._divide_by(self)

    def _divide_by(self, z: "Qi") -> "Qi":
        """``self / z`` exactly: numerator ``self · conj(z)`` over the real norm
        ``|z|² = c²+d²`` (Class N rational anchor). Raises on ``z == 0``."""
        a, b, c, d = self._re, self._im, z._re, z._im
        denom = c * c + d * d                          # exact real Q
        if denom == 0:
            raise ZeroDivisionError("Qi division by zero")
        return Qi((a * c + b * d) / denom, (b * c - a * d) / denom)

    def __neg__(self) -> "Qi":
        return Qi(-self._re, -self._im)

    def __pos__(self) -> "Qi":
        return Qi(self._re, self._im)

    def __pow__(self, exp):
        """``z ** w`` — an integer (or integer-valued) exponent stays an EXACT
        ``Qi`` (repeated Gaussian-rational multiply; negative → reciprocal); a
        genuinely non-integer exponent collapses to the builtin float-complex
        boundary. Part of the :class:`numbers.Complex` contract."""
        e = _int_exponent(exp)
        if e is not None:
            if e == 0:
                return Qi(_Q_ONE, _Q_ZERO)
            base = self if e > 0 else (Qi(_Q_ONE, _Q_ZERO) / self)
            result = Qi(_Q_ONE, _Q_ZERO)
            for _ in range(e if e > 0 else -e):
                result = result * base
            return result
        if not isinstance(exp, (int, float, complex)) and _coerce(exp) is None:
            return NotImplemented
        return complex(self) ** complex(exp)           # irrational → float boundary

    def __rpow__(self, other):
        z = _coerce(other)
        if z is None:
            return NotImplemented
        return z.__pow__(self)

    # ── complex-specific ────────────────────────────────────────────────────
    def conjugate(self) -> "Qi":
        """Complex conjugate — the **Class-K** sign-flip on the imaginary part
        (never an ALU ``abs``). On the Klein-4 quadrant this XORs the imaginary
        bit: ``z.conjugate().quadrant() == z.quadrant() ^ 2`` for ``im ≠ 0`` (a
        no-op for a real value, whose im-bit is already 0)."""
        return Qi(self._re, -self._im)

    def quadrant(self) -> int:
        """The sign sector as a **Klein-4 element** (ℤ₂×ℤ₂; an int in
        ``hdc.KLEIN4_STATES`` 0..3): ``bit0 = re < 0``, ``bit1 = im < 0``. Zero
        components count as non-negative. This IS the klein4 surface — the four
        sign-quadrants ARE the group, with conjugation XOR-ing the im bit."""
        bit_re = 1 if self._re < 0 else 0
        bit_im = 1 if self._im < 0 else 0
        return bit_re | (bit_im << 1)

    def norm_sq(self) -> Q:
        """``|z|² = re² + im²`` — the EXACT squared modulus as a ``Q`` (Class N
        rational anchor; pure exact mult/add, no sqrt, no ``math``)."""
        return self._re * self._re + self._im * self._im

    def __abs__(self):
        """Modulus ``|z| = √(re² + im²)`` via the srmech Class-N
        :func:`srmech.amsc.rational.sqrt` over the EXACT squared modulus — an
        exact ``Q`` when ``|z|²`` is a perfect rational square (e.g. ``3+4i`` →
        ``5``), else the stay-rational ``Q`` boundary. A ``Q`` IS a
        :class:`numbers.Real`, so ``abs(z)`` is a Real as the
        :class:`numbers.Complex` contract requires."""
        return _rational.sqrt(self.norm_sq())


# ``Qi`` implements the full :class:`numbers.Complex` surface — ``real`` / ``imag``
# (each a ``Q``) / ``conjugate`` / ``__complex__`` / ``__abs__`` / ``__bool__`` /
# ``==`` / the arithmetic ring incl. ``__pow__`` / ``__rpow__`` — over EXACT
# Gaussian rationals, so it IS a genuine ``numbers.Complex`` (hence
# ``numbers.Number``) but NOT a ``numbers.Real`` (it is genuinely complex). The
# exact-complex peer of ``Complex128``'s float-complex registration.
numbers.Complex.register(Qi)
