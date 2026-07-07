"""srmech.amsc.q — the framework-native exact-rational scalar carrier (``Q``).

The scalar peer of the array carriers :class:`srmech.amsc.mat.Mat` (2-D),
:class:`srmech.amsc.vec.Vec` (1-D) and :class:`srmech.amsc.hv.HV` (hypervector).
Where those carry collections of numbers, ``Q`` carries **one** exact rational —
a reduced ``(num, den)`` integer pair — and behaves like a float in comparisons
while *never* collapsing to one until you explicitly ask (``float(q)``).

Why a carrier and not a bare ``(num, den)`` tuple or a Python ``float``:

- **The stay-rational discipline** (F868, `[[feedback_stay_rational_collapse_only_at_display]]`):
  a quantity that is exactly rational — a match-fraction ``matches / D``, a
  Casimir eigenvalue, a softmax weight — must stay two integers the whole way and
  collapse to a decimal **only at the display boundary**. A ``float`` is just
  ``best_rational`` with ``max_d ≈ 2⁵²`` and the provenance thrown away — a
  strictly *worse* version of the rational we already hold (the continuous
  number line is the obstacle, `[[feedback_continuous_number_line_pedagogical_obstacle]]`).
- A bare ``(num, den)`` tuple loses float-like behaviour: ``(3, 4) != 0.75`` and
  ``(3, 4) < (7, 8)`` compares by *numerator*, not value — so ranking breaks. A
  ``Q`` compares by **integer cross-multiply** (``a/b`` vs ``c/d`` ⇒ ``a·d`` vs
  ``c·b``; F868 mechanism #2), so ``Q(3, 4) == 0.75``, ``Q(D, D) == 1.0`` and
  ``max(qs)`` / ``sorted(qs)`` are all exact and correct.
- Like ``Mat``/``HV`` force the srmech cascade instead of inviting ``np.linalg``,
  a ``Q`` handle forces exact rational arithmetic (Class-N ``rational_*``) and
  keeps the value attestable, instead of inviting a lossy ``float`` divide.

Everything stays exact: reduction rides the Class-N
:func:`srmech.amsc.rational._reduce_rational` (Euclidean GCD over big ints, no
stdlib ``math``); arithmetic rides Class-N ``rational_add`` / ``rational_mul`` /
``rational_div``. ``(num, den)`` is always recoverable — ``q.numerator`` /
``q.denominator`` or unpacking ``num, den = q``.

**Native dispatch (0.9.0rc167, #765 — self-hosting).** The Class-N ops beneath
``Q`` are size-adaptive THREE-TIER: u64-fit operands ride the scalar C ops
(``srmech_rational_*``); mid-size bignums ride CPython ``int`` (the complete
fallback); at/above the measured ``rational._BIGQ_MIN_BITS`` threshold the
WHOLE op (cross-multiplies + gcd-reduce + exact divisions) runs on srmech's
OWN caller-arena C bignum via ``_native.bigq_add_c/bigq_mul_c/bigq_div_c/
bigq_reduce_c`` (existing ``srmech_bigint_*`` symbols; one linear binary limb
marshal in, one out — #770). So the Python side's big exact-ℚ arithmetic runs
on the SAME substrate a bare-C host uses; CPython ``int`` is the demoted
below-threshold / no-native alternative — byte-identical either way. The
dispatch touches only the two scalar components; no carrier structure above
``Q`` is affected (the sparse-tower guardrail).
"""

from __future__ import annotations

import numbers
from typing import Tuple

from . import rational as _rational

__all__ = ["Q"]


def _integer_exponent(exp):
    """The int value of ``exp`` IF it is an integer-valued exponent — a plain
    ``int`` (``bool`` excluded) or a rational with denominator 1 (e.g. ``Q(2, 1)``,
    ``Fraction(2, 1)``) — else ``None``. An integer-valued *float* (``2.0``) is
    NOT integer here, matching ``fractions.Fraction`` (``Fraction ** 2.0`` is a
    float, not an exact rational)."""
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


def _as_pair(value):
    """Coerce ``value`` to an exact ``(num, den)`` integer pair, or return
    ``None`` if it is a type ``Q`` cannot exactly compare/combine with (so the
    dunder returns ``NotImplemented`` and Python tries the reflected op /
    ``pytest.approx``). ``bool`` is rejected as a number per Python convention
    leaking ``True == 1``; we accept it as the int it is for ergonomics."""
    if isinstance(value, Q):
        return (value._n, value._d)
    if isinstance(value, int):                      # includes bool
        return (value, 1)
    if isinstance(value, float):
        # Exact two-int form of the incoming float (no precision lost). Raises
        # on inf/nan — those are not rationals, so Q cannot compare with them.
        try:
            return value.as_integer_ratio()
        except (OverflowError, ValueError):
            return None
    # A 2-tuple/list of ints IS srmech's ``(num, den)`` rational house form
    # (what ``rational_*`` / ``One.to_scalar`` / ``to_flat_rational`` speak), so
    # ``Q(3, 4) == (3, 4)`` and ``Q + (1, 2)`` interoperate seamlessly.
    if (isinstance(value, (tuple, list)) and len(value) == 2
            and isinstance(value[0], int) and isinstance(value[1], int)
            and value[1] != 0):
        return (value[0], value[1])
    return None


class Q:
    """An exact rational scalar — a reduced ``(num, den)`` integer pair that
    behaves like a float in comparisons and collapses to one only via
    ``float(q)``. See the module docstring for the stay-rational rationale."""

    __slots__ = ("_n", "_d")

    def __init__(self, num: int, den: int = 1) -> None:
        if not isinstance(num, int) or not isinstance(den, int):
            raise TypeError(
                f"Q(num, den) takes two ints; got {type(num).__name__}, "
                f"{type(den).__name__}")
        # Reduce via the Class-N canonical reducer (Euclidean GCD, big-int safe,
        # no stdlib math). Raises ZeroDivisionError on den == 0.
        self._n, self._d = _rational._reduce_rational(num, den)

    # ── construction helpers ────────────────────────────────────────────────
    @classmethod
    def from_pair(cls, pair: Tuple[int, int]) -> "Q":
        """Build from a ``(num, den)`` pair (e.g. a Class-N ``rational`` op
        return), the inverse of unpacking ``num, den = q``."""
        num, den = pair
        return cls(num, den)

    @classmethod
    def from_float(cls, x: float) -> "Q":
        """The EXACT rational of a float (``x.as_integer_ratio()``) — promotes a
        boundary float back into the rationals without precision loss. (To
        *approximate* to a small denominator instead, use Class-N
        ``rational.best_rational``.)"""
        num, den = float(x).as_integer_ratio()
        return cls(num, den)

    # ── exact accessors (num/den always recoverable) ────────────────────────
    @property
    def numerator(self) -> int:
        return self._n

    @property
    def denominator(self) -> int:
        return self._d

    def as_pair(self) -> Tuple[int, int]:
        """The exact reduced ``(num, den)`` integer pair."""
        return (self._n, self._d)

    def as_integer_ratio(self) -> Tuple[int, int]:
        """The exact reduced ``(num, den)`` — the standard numeric protocol so a
        ``Q`` is a first-class :class:`~fractions.Fraction` source. This is what
        lets ``Fraction(q)`` / ``int(q)`` (and so ``cascade.cd_mult`` over the
        exact-rational ``Q`` twiddle ``hypercomplex_exp``) coerce without a float
        rotation. Alias of :meth:`as_pair` (``int``/``float``/``Fraction`` all
        expose ``as_integer_ratio``)."""
        return (self._n, self._d)

    def __iter__(self):
        """Unpack as ``num, den = q``."""
        yield self._n
        yield self._d

    # ── the display-boundary collapse (the ONLY place a decimal appears) ────
    def __float__(self) -> float:
        return self._n / self._d

    def as_float(self) -> float:
        """Collapse to a Python ``float`` — the opt-in display/boundary cast.
        Equivalent to ``float(q)``; named for call-site intent."""
        return self._n / self._d

    # ── reprs ───────────────────────────────────────────────────────────────
    def __repr__(self) -> str:
        return f"Q({self._n}, {self._d})"

    def __str__(self) -> str:
        return f"{self._n}/{self._d}" if self._d != 1 else f"{self._n}"

    def __bool__(self) -> bool:
        return self._n != 0

    def __hash__(self) -> int:
        # Equal Q's (same reduced pair) hash equal; a Q that == an int/float
        # collapses to the same float value, so its hash matches (finite case),
        # keeping the data-model invariant. Huge One-scale rationals overflow
        # float → fall back to the pair hash (they never == a finite float).
        try:
            return hash(self._n / self._d)
        except OverflowError:
            return hash((self._n, self._d))

    # ── comparisons: exact, by integer cross-multiply (F868 mechanism #2) ───
    def _cmp(self, other):
        """Sign of ``self - other`` as an int, or ``None`` if incomparable.
        Denominators are positive (reduced), so cross-multiply preserves the
        inequality direction."""
        pair = _as_pair(other)
        if pair is None:
            return None
        on, od = pair
        left = self._n * od
        right = on * self._d
        return (left > right) - (left < right)

    def __eq__(self, other) -> bool:
        c = self._cmp(other)
        return NotImplemented if c is None else c == 0

    def __ne__(self, other) -> bool:
        c = self._cmp(other)
        return NotImplemented if c is None else c != 0

    def __lt__(self, other) -> bool:
        c = self._cmp(other)
        return NotImplemented if c is None else c < 0

    def __le__(self, other) -> bool:
        c = self._cmp(other)
        return NotImplemented if c is None else c <= 0

    def __gt__(self, other) -> bool:
        c = self._cmp(other)
        return NotImplemented if c is None else c > 0

    def __ge__(self, other) -> bool:
        c = self._cmp(other)
        return NotImplemented if c is None else c >= 0

    # ── exact arithmetic via Class-N rational primitives ────────────────────
    def _combine(self, other, op):
        pair = _as_pair(other)
        if pair is None:
            return NotImplemented
        return Q.from_pair(op((self._n, self._d), pair))

    def __add__(self, other):
        return self._combine(other, _rational.rational_add)

    def __radd__(self, other):
        return self._combine(other, _rational.rational_add)

    def __sub__(self, other):
        pair = _as_pair(other)
        if pair is None:
            return NotImplemented
        return Q.from_pair(_rational.rational_add((self._n, self._d),
                                                  (-pair[0], pair[1])))

    def __rsub__(self, other):
        pair = _as_pair(other)
        if pair is None:
            return NotImplemented
        return Q.from_pair(_rational.rational_add(pair,
                                                  (-self._n, self._d)))

    def __mul__(self, other):
        return self._combine(other, _rational.rational_mul)

    def __rmul__(self, other):
        return self._combine(other, _rational.rational_mul)

    def __truediv__(self, other):
        return self._combine(other, _rational.rational_div)

    def __rtruediv__(self, other):
        pair = _as_pair(other)
        if pair is None:
            return NotImplemented
        return Q.from_pair(_rational.rational_div(pair, (self._n, self._d)))

    def __neg__(self) -> "Q":
        return Q(-self._n, self._d)

    def __pos__(self) -> "Q":
        return Q(self._n, self._d)

    def __abs__(self) -> "Q":
        # Class-K magnitude via explicit sign-branch, never an ALU abs() on the
        # value (`[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`).
        return Q(self._n if self._n >= 0 else -self._n, self._d)

    def __pow__(self, exp):
        """Exact rational power for an INTEGER exponent — the EXACT rational
        ``(num/den)**exp``, staying in the integer ALU (rides the Class-N
        :func:`~srmech.amsc.rational.rational_pow_uint`, native-dispatched). An
        integer-valued exponent may be an ``int`` OR an integer-valued rational
        (``Q(2, 1)``). A genuinely non-integer exponent (a rational with
        denominator > 1, or a float) leaves the rationals, so it collapses to the
        float boundary EXACTLY like :class:`fractions.Fraction` (the result is
        irrational; ``float`` is where srmech holds irrationals). This keeps
        ``cos(x)**2`` / ``r**3`` exact while ``q ** 0.5`` stays honest instead of
        raising — Q is a faithful :class:`numbers.Rational`."""
        k = _integer_exponent(exp)
        if k is not None:
            if k == 0:
                return Q(1, 1)
            if k > 0:
                return Q.from_pair(_rational.rational_pow_uint((self._n, self._d), k))
            if self._n == 0:
                raise ZeroDivisionError("Q: 0 cannot be raised to a negative power")
            if self._n < 0:
                # (a/b)^(-k) = (b/a)^k with a < 0: normalise the reciprocal's
                # sign onto the NUMERATOR (b/a == (-b)/(-a)) so rational_pow_
                # uint's positive-denominator contract holds; the sign then
                # rides (-b)^k exactly as Fraction does (even k → +, odd → −).
                # Pre-rc168 this branch passed (d, n) with n < 0 and raised
                # ValueError("denominator must be positive") — the
                # negative-base/negative-exponent bug.
                return Q.from_pair(
                    _rational.rational_pow_uint((-self._d, -self._n), -k))
            return Q.from_pair(_rational.rational_pow_uint((self._d, self._n), -k))
        base = self._n / self._d
        if isinstance(exp, complex):
            return base ** exp
        pair = _as_pair(exp)
        if pair is None:
            return NotImplemented
        return base ** (pair[0] / pair[1])

    def __rpow__(self, other):
        """``base ** self``. Exact when ``self`` is integer-valued (``base`` raised
        to ``int(self)`` rides the exact integer-power path); otherwise the result
        is irrational and collapses to the float boundary, Fraction-consistent."""
        pair = _as_pair(other)
        if pair is None:
            return NotImplemented
        if self._d == 1:
            return Q.from_pair(pair) ** int(self._n)
        return (pair[0] / pair[1]) ** (self._n / self._d)

    # ── numbers.Rational conformance: the integer-rounding family (exact, via the
    #    integer ALU; sign handled by an explicit branch, never an ALU abs()) ────
    def __trunc__(self) -> int:
        """Truncate toward zero (``math.trunc``). Exact: denominators are positive
        (reduced), so the sign is carried by an explicit Class-K branch."""
        n, d = self._n, self._d
        if n >= 0:
            return n // d
        return -((-n) // d)

    def __int__(self) -> int:
        """``int(q)`` — truncates toward zero (the numeric-protocol contract)."""
        return self.__trunc__()

    def __floor__(self) -> int:
        """Floor toward −∞ (``math.floor``), EXACT — Python ``//`` over a positive
        reduced denominator already floors toward −∞ (no lossy ``float`` detour)."""
        return self._n // self._d

    def __ceil__(self) -> int:
        """Ceil toward +∞ (``math.ceil``), EXACT (no lossy ``float`` detour)."""
        return -((-self._n) // self._d)

    def _round_half_even(self) -> int:
        """Round to the nearest integer, ties to even (Python ``round`` / Fraction
        semantics). Exact integer arithmetic; ``r`` lands in ``[0, d)`` because the
        reduced denominator is positive."""
        n, d = self._n, self._d
        q = n // d
        r = n - q * d
        twice = 2 * r
        if twice < d:
            return q
        if twice > d:
            return q + 1
        return q if (q % 2 == 0) else q + 1

    def __round__(self, ndigits=None):
        """``round(q)`` → nearest int (ties-to-even); ``round(q, ndigits)`` → a
        ``Q`` rounded to that many decimal places — Fraction-consistent, exact."""
        if ndigits is None:
            return self._round_half_even()
        if ndigits >= 0:
            shift = 10 ** ndigits
            scaled = Q(self._n * shift, self._d)
            return Q(scaled._round_half_even(), shift)
        shift = 10 ** (-ndigits)
        scaled = Q(self._n, self._d * shift)
        return Q(scaled._round_half_even() * shift, 1)

    # ── numbers.Complex accessors (a real number's real part is itself) ─────────
    @property
    def real(self) -> "Q":
        return self

    @property
    def imag(self) -> "Q":
        return Q(0, 1)

    def conjugate(self) -> "Q":
        """A real number is its own conjugate."""
        return self

    def __complex__(self) -> complex:
        return complex(self._n / self._d)

    # ── numbers.Real floor-division / modulo (Fraction return-types: ``//`` and
    #    ``divmod`` yield an int quotient, ``%`` yields a Q remainder) ───────────
    def __floordiv__(self, other):
        pair = _as_pair(other)
        if pair is None:
            return NotImplemented
        return Q.from_pair(_rational.rational_div((self._n, self._d), pair)).__floor__()

    def __rfloordiv__(self, other):
        pair = _as_pair(other)
        if pair is None:
            return NotImplemented
        return Q.from_pair(_rational.rational_div(pair, (self._n, self._d))).__floor__()

    def __mod__(self, other):
        pair = _as_pair(other)
        if pair is None:
            return NotImplemented
        return self - (self // other) * Q.from_pair(pair)

    def __rmod__(self, other):
        pair = _as_pair(other)
        if pair is None:
            return NotImplemented
        o = Q.from_pair(pair)
        return o - (o // self) * self

    def __divmod__(self, other):
        pair = _as_pair(other)
        if pair is None:
            return NotImplemented
        return (self // other, self % other)

    def __rdivmod__(self, other):
        pair = _as_pair(other)
        if pair is None:
            return NotImplemented
        o = Q.from_pair(pair)
        return (o // self, o % self)


# ``Q`` IS an exact rational with the full real/rational interface above, so it is
# a genuine :class:`numbers.Rational` (hence ``numbers.Real`` / ``numbers.Complex``
# / ``numbers.Number``). Registering makes ``isinstance(q, numbers.Rational)`` True
# and — load-bearing across Python versions — lets ``Fraction(q)`` read
# ``q.numerator`` / ``q.denominator`` directly (``Fraction`` only consults
# ``as_integer_ratio`` on Python ≥3.14; on 3.10–3.13 it requires a registered
# ``Rational``). See `[[feedback_fraction_of_q_carrier_needs_as_integer_ratio_route_pre_314]]`.
numbers.Rational.register(Q)
