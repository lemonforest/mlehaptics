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

**Cross-gcd-first multiply (0.9.0rc211, #786 — Knuth TAOCP Vol 2, §4.5.1).**
``Q.__mul__``/``__rmul__`` divide the two CROSS gcds out of the operands
BEFORE multiplying (``g1 = gcd(|a|, d)``, ``g2 = gcd(|c|, b)``, result
``= (a/g1 · c/g2) / (b/g2 · d/g1)``) instead of multiplying-then-reducing —
the same discipline CPython's ``fractions.Fraction._mul`` applies, INCLUDING
its second half: for two REDUCED operands the cross-reduced product is
already in lowest terms (Knuth's theorem — every prime of ``a/g1`` is
excluded from ``b·d/(g1·g2)`` by ``a⊥b`` and by ``a/g1 ⊥ d/g1``; likewise for
``c/g2``), so the product pair is constructed directly with NO product-scale
gcd at all (the ``Fraction._from_coprime_ints`` fast constructor). The result
is byte-identical (the same fully-reduced pair either way); only the
INTERMEDIATE products shrink (for a cross-cancelling ``a/b × b/a`` the
multiply collapses to ``1·1/1·1`` instead of two double-width products fed to
a double-width gcd). u64-fit operands skip the cross-reduce and keep riding
the fused scalar C op unchanged (see :data:`_CROSS_REDUCE_MIN_BITS`); a raw
house-form ``(num, den)`` tuple operand may be UNREDUCED, so it takes the
general validating path (cross-reduce + full ``rational_mul`` reduce).

**Self-hosted coprime product (0.9.0rc220, #786 — the rc212 honest-note
follow-up).** The fast path's final product pair (proven coprime by Knuth's
theorem) now rides srmech's OWN caller-arena C bignum at/above the
``rational._BIGQ_MIN_BITS`` threshold via the new RAW ``_native.
bigint_mul_c`` (``srmech_bigint_mul`` / the rc168 Karatsuba arena entry — no
fused gcd, unlike ``bigq_mul_c`` whose product-scale reduce is exactly the
work the theorem eliminates). CPython ``int`` multiply remains the complete
below-threshold / no-native alternative — byte-identical either way. This
completes the #765 self-hosting discipline for the cross-gcd multiply: the
two cross gcds already dispatched to ``srmech_bigint_gcd`` (via
``cyclic.gcd``); the product was the one leg still on CPython ``int``.
"""

from __future__ import annotations

import numbers
from typing import Tuple

from . import _native
from . import cyclic as _cyclic
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


# 0.9.0rc211 (#786) — the cross-gcd-first multiply threshold. 64 is
# attested-to-structure (Class A): it is the u64 native scalar domain boundary
# — operands whose magnitudes all fit below 64 bits ride `srmech_rational_mul`
# as ONE fused C call (multiply + gcd-reduce together), so two extra Python-
# side cross-gcd calls there are pure dispatch/FFI overhead on inputs whose
# intermediates cannot blow up anyway. At/above 64 bits the operands miss the
# fused scalar C path, and Knuth's cross-reduction (TAOCP Vol 2, §4.5.1) keeps
# the intermediate products near OPERAND scale instead of PRODUCT scale.
_CROSS_REDUCE_MIN_BITS: int = 64


def _cross_reduce(a_num: int, a_den: int, b_num: int, b_den: int):
    """Divide the two CROSS gcds out of the multiply operands (Knuth TAOCP
    Vol 2, §4.5.1): ``g1 = gcd(|a_num|, b_den)`` off the main diagonal,
    ``g2 = gcd(|b_num|, a_den)`` off the anti-diagonal. Requires positive
    denominators. Returns the four cross-reduced parts (signs stay on the
    numerators; dividing by a positive gcd of the magnitude is exact). The
    gcds ride the Class-I :func:`srmech.amsc.cyclic.gcd` on Class-K
    sign-branch magnitudes (never an ALU ``abs()``)."""
    # Class-K magnitude via EXPLICIT sign-branches, never an ALU abs().
    a_mag = a_num if a_num >= 0 else -a_num
    b_mag = b_num if b_num >= 0 else -b_num
    g1 = _cyclic.gcd(a_mag, b_den)
    if g1 > 1:
        a_num //= g1
        b_den //= g1
    g2 = _cyclic.gcd(b_mag, a_den)
    if g2 > 1:
        b_num //= g2
        a_den //= g2
    return a_num, a_den, b_num, b_den


def _coprime_product(x: int, y: int) -> int:
    """``x · y`` for the cross-reduced (proven-coprime-product) fast path —
    0.9.0rc220 (#786, closing the rc212 honest-note follow-up). At/above the
    measured :data:`srmech.amsc.rational._BIGQ_MIN_BITS` threshold the product
    rides srmech's OWN caller-arena C bignum via :func:`_native.bigint_mul_c`
    (the RAW ``srmech_bigint_mul`` / rc168 Karatsuba product — NO fused gcd;
    the fused ``bigq_mul_c``'s product-scale reduce is exactly the work
    Knuth's theorem eliminates), completing the #765 self-hosting discipline
    for the one leg of the big-ℚ multiply that still rode CPython ``int``.
    CPython ``int`` multiply remains the complete below-threshold / no-native
    alternative — byte-identical either way (the integer product is
    unique). Attested-to-measurement (Class B, WSL2 gcc 13.4 -O2, Python
    3.10): the routed leg alone is marshal-overhead-dominated at the low
    band (0.14–0.83× vs CPython int at 2048–20000 bits), landing the WHOLE
    ``Q.__mul__`` at 0.81–0.99× — inside the rc167 self-hosting acceptance
    band (0.59–1.24×): the dispatch buys the architecture at ≈cost-parity,
    exactly the #765 trade. Cross-cancelling shapes are untouched (their
    cancelled products sit below the gate)."""
    if _rational._bigq_max_bits(x, y) >= _rational._BIGQ_MIN_BITS:
        out = _native.bigint_mul_c(x, y)
        if out is not None:
            return out
    return x * y


def _mul_cross_reduced(a: Tuple[int, int], b: Tuple[int, int]) -> Tuple[int, int]:
    """Cross-gcd-first rational multiply over ARBITRARY house-form pairs
    (possibly unreduced, e.g. a raw ``(6, 4)`` tuple operand): cross-reduce,
    then the full :func:`~srmech.amsc.rational.rational_mul` reduce — for an
    unreduced input the cross gcds alone do not reach lowest terms, so the
    final reduce stays. BYTE-IDENTICAL to ``rational_mul(a, b)`` (dividing
    shared factors out early never changes the value; the final reduce
    canonicalises) — purely an intermediate-size optimisation. Below
    :data:`_CROSS_REDUCE_MIN_BITS` (and for the non-positive-denominator
    error path) it delegates to ``rational_mul`` unchanged, preserving the
    fused u64 scalar C fast path and the exact validation contract."""
    a_num, a_den = a[0], a[1]
    b_num, b_den = b[0], b[1]
    if a_den <= 0 or b_den <= 0:
        # Bad denominators: rational_mul raises the canonical ValueError —
        # the contract is unchanged.
        return _rational.rational_mul(a, b)
    # Class-K magnitude via EXPLICIT sign-branches, never an ALU abs().
    a_mag = a_num if a_num >= 0 else -a_num
    b_mag = b_num if b_num >= 0 else -b_num
    if (a_mag.bit_length() < _CROSS_REDUCE_MIN_BITS
            and a_den.bit_length() < _CROSS_REDUCE_MIN_BITS
            and b_mag.bit_length() < _CROSS_REDUCE_MIN_BITS
            and b_den.bit_length() < _CROSS_REDUCE_MIN_BITS):
        # Small operands: the fused scalar C op (mul + reduce in ONE call)
        # owns this tier — delegate with ZERO re-marshalling (the gate above
        # is four bit_length probes on already-int pairs).
        return _rational.rational_mul(a, b)
    a_num, a_den, b_num, b_den = _cross_reduce(a_num, a_den, b_num, b_den)
    return _rational.rational_mul((a_num, a_den), (b_num, b_den))


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
    def _from_coprime(cls, num: int, den: int) -> "Q":
        """PRIVATE trusted constructor (0.9.0rc211, #786 — the
        ``fractions.Fraction._from_coprime_ints`` pattern): build a ``Q``
        from a pair the CALLER has proven already reduced (coprime, positive
        denominator), skipping ``__init__``'s ``_reduce_rational``. Only the
        cross-gcd multiply fast path may call this — its coprimality is
        Knuth's TAOCP 4.5.1 theorem over two reduced operands, never an
        assumption about raw input."""
        obj = object.__new__(cls)
        obj._n = num
        obj._d = den
        return obj

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

    def _mul(self, other):
        """0.9.0rc211 (#786): cross-gcd-first multiply (Knuth TAOCP 4.5.1,
        the full ``fractions.Fraction._mul`` discipline) — byte-identical
        result, operand-scale intermediates. Three tiers:

        - raw house-form tuple/list operand (possibly UNREDUCED) → the
          general validating path (cross-reduce + full ``rational_mul``
          reduce) via :func:`_mul_cross_reduced`;
        - u64-fit operands → delegate to ``rational_mul`` unchanged (the
          fused mul+reduce scalar C op owns that tier);
        - big REDUCED operands (self is reduced by invariant; an
          ``int``/``bool`` pair ``(n, 1)`` and a ``float``'s
          ``as_integer_ratio()`` are reduced by construction) → cross-reduce
          and build the product DIRECTLY via :meth:`_from_coprime` — by
          Knuth's theorem the cross-reduced product of two reduced fractions
          is already in lowest terms, so NO product-scale gcd runs at all.
          0.9.0rc220 (#786): the two coprime products ride
          :func:`_coprime_product` — srmech's own C bignum (raw
          ``bigint_mul_c``) at/above the 1024-bit ``_BIGQ_MIN_BITS``
          threshold, CPython ``int`` below — byte-identical either way.
        """
        pair = _as_pair(other)
        if pair is None:
            return NotImplemented
        if isinstance(other, (tuple, list)):
            # may be unreduced / negative-den — full validate + reduce
            return Q.from_pair(_mul_cross_reduced((self._n, self._d), pair))
        a_num, a_den = self._n, self._d
        b_num, b_den = pair
        # Class-K magnitude via EXPLICIT sign-branches, never an ALU abs().
        a_mag = a_num if a_num >= 0 else -a_num
        b_mag = b_num if b_num >= 0 else -b_num
        if (a_mag.bit_length() < _CROSS_REDUCE_MIN_BITS
                and a_den.bit_length() < _CROSS_REDUCE_MIN_BITS
                and b_mag.bit_length() < _CROSS_REDUCE_MIN_BITS
                and b_den.bit_length() < _CROSS_REDUCE_MIN_BITS):
            return Q.from_pair(
                _rational.rational_mul((a_num, a_den), pair))
        a_num, a_den, b_num, b_den = _cross_reduce(
            a_num, a_den, b_num, b_den)
        return Q._from_coprime(_coprime_product(a_num, b_num),
                               _coprime_product(a_den, b_den))

    def __mul__(self, other):
        return self._mul(other)

    def __rmul__(self, other):
        return self._mul(other)

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
