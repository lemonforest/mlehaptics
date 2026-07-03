"""srmech.amsc.poly — the framework-native EXACT-rational polynomial carrier (``Poly``).

The 1-D *polynomial* peer of the exact-matrix carrier
:class:`srmech.amsc.qmat.QMat` and the exact-scalar carrier
:class:`srmech.amsc.q.Q`. Where ``Q`` carries one exact rational and ``QMat`` a
dense grid of them, ``Poly`` carries a univariate polynomial over ℚ — a finite
sequence of exact :class:`~srmech.amsc.q.Q` coefficients in **ascending degree**
(``coeffs[i]`` is the coefficient of ``x**i``). Each coefficient is a reduced
``(num, den)`` integer pair over Python ``int`` bigint, so there is **no
magnitude ceiling**: a coefficient numerator or denominator may freely exceed
``2**64`` (unlike a native int64 fixed-point path).

This is the FOUNDATION carrier of the §76 "telescope" Σ-row closed-form prover
(F929): the Gosper / Zeilberger / WZ machinery reduces a hypergeometric sum by
manipulating exact polynomials in ℚ[k] — long division, the polynomial GCD, the
dispersion ``p(x+h)`` shift — so they need an exact, ceiling-free polynomial
substrate FIRST. ``Poly`` is that substrate (the Class-N rational arithmetic over
the Class-J prime-field is what the telescope sits on).

rc39 (Layer A) completes the polynomial-algebra foundation on top of the rc38
carrier: the deferred single-call ``srmech_poly_gcd`` C peer (now routing
:meth:`gcd` natively, with a chain-scaled arena — see ``srmech_poly.c``), plus
:meth:`resultant` (exact subresultant-style PRS) and :meth:`dispersion` (the
non-negative integer roots of ``Res_k(p(k), q(k+h))``). ``gosper`` itself — the
indefinite hypergeometric summation that consumes these — is DEFERRED to rc40:
shipping it as a public op requires a ``srmech_gosper`` C peer (the Rosetta
ratchet forbids a Python-only compute op), and that peer needs an exact-ℚ
LINEAR SOLVE in malloc-free caller-arena C (the undetermined-coefficient Gosper
equation ``a(k)·x(k+1) − b(k−1)·x(k) = c(k)``) — i.e. the ``QMat`` exact
Gauss-Jordan rref/solve backfilled into the C surface, a large build not sound
in one rc. rc40 ships that ℚ-solve-in-C, then ``gosper`` + ``srmech_gosper``.

Why a carrier and not a bare list of ``Q`` (mirrors the ``Q`` / ``QMat``
rationale):

- **The stay-rational discipline** (F868). A polynomial whose coefficients are
  exactly rational — a hypergeometric certificate, a characteristic polynomial,
  a Bernoulli generating polynomial — must stay two integers per coefficient the
  whole way and collapse to float64 **only at the display boundary**
  (:meth:`to_floats`). A float list is just ``best_rational`` at ``max_d`` near
  ``2**52`` with the provenance thrown away.
- Like a ``QMat`` handle forces exact rational linear algebra, a ``Poly`` handle
  forces **exact** polynomial algebra — long division pivoting on ``Q != 0``
  (never a float tolerance), a monic-normalized Euclidean GCD, exact Horner
  evaluation — and keeps every intermediate attestable.

Canonical form: the coefficient tuple is always **trimmed** of trailing-zero
(high-degree) coefficients, so the zero polynomial is the empty tuple ``()`` and
``degree`` is ``-1`` for it (the standard convention). Two ``Poly`` are equal iff
their trimmed coefficient tuples are equal.

Everything stays exact: ``+`` / ``-`` / ``-x`` / scalar ``*`` / polynomial ``*``
(convolution) ride the Class-N ``Q`` arithmetic; :meth:`divmod` is exact
polynomial long division over ℚ; :meth:`gcd` is the exact monic Euclidean GCD;
:meth:`eval` is exact Horner; :meth:`shift` is the exact dispersion ``p(x+h)``.
Sign in the GCD / leading-coefficient normalization is the **Class-K** pin-slot
via an explicit ``Q`` sign-branch (the ``Q`` reduced denominator is positive, so
the numerator carries the sign), never an ALU ``abs()``. There is exactly ONE
place a ``float`` appears — :meth:`to_floats`, the terminal ALU→FPU rotation
(like :meth:`srmech.amsc.qmat.QMat.to_mat` / :meth:`srmech.amsc.q.Q.__float__`).
No ``math`` module, no numpy; a future ``QiPoly`` would carry Gaussian-rational
(``Qi``) coefficients.
"""

from __future__ import annotations

from fractions import Fraction
from typing import List, Sequence, Tuple

from .q import Q

__all__ = ["Poly", "poly_from_coeffs"]

_Q_ZERO = Q(0, 1)
_Q_ONE = Q(1, 1)


def _native():
    """The native ``_native`` module IF the rc38 ``srmech_poly_*`` peer is
    present, else ``None`` — so the carrier dispatches to C when available and
    falls cleanly to the pure-Python body (the complete alternative + the
    parity oracle) otherwise. Imported lazily to avoid a bootstrap cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    return nat if nat.has_native_poly() else None


def _pairs(coeffs) -> List[Tuple[int, int]]:
    """A tuple of ``Q`` → a list of ``(num, den)`` int pairs for the C bridge."""
    return [(c.numerator, c.denominator) for c in coeffs]


def _from_pairs(pairs) -> Tuple[Q, ...]:
    """A list of ``(num, den)`` int pairs (from the C bridge) → a tuple of ``Q``
    (already reduced + trimmed by the C op)."""
    return tuple(Q(int(n), int(d)) for n, d in pairs)


def _to_q(value):
    """Coerce ``value`` to an exact :class:`~srmech.amsc.q.Q`, or ``None`` if it
    is not an exact-rational-coercible coefficient (mirrors ``qmat._to_q``).

    A ``float`` is REJECTED (returns ``None``) — a ``Poly`` coefficient must be
    exact. Accepts ``Q`` / ``int`` / ``Fraction`` / a ``(num, den)`` integer
    pair / anything exposing ``as_pair`` / ``as_integer_ratio``."""
    if isinstance(value, Q):
        return value
    if isinstance(value, bool):
        return Q(int(value), 1)
    if isinstance(value, int):
        return Q(value, 1)
    if isinstance(value, Fraction):
        return Q(value.numerator, value.denominator)
    if isinstance(value, float):
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


def _trim(coeffs: Sequence[Q]) -> Tuple[Q, ...]:
    """Drop trailing-zero (high-degree) coefficients → canonical form. The zero
    polynomial trims to the empty tuple ``()``."""
    n = len(coeffs)
    while n > 0 and coeffs[n - 1] == 0:
        n -= 1
    return tuple(coeffs[:n])


class Poly:
    """A numpy-free EXACT-rational univariate polynomial over ℚ: a trimmed tuple
    of exact ``Q`` coefficients in ascending degree, immutable. The polynomial
    peer of :class:`srmech.amsc.qmat.QMat`. Collapses to a list of float64 only
    via :meth:`to_floats`. See the module docstring."""

    __slots__ = ("_c",)

    def __init__(self, coeffs=()) -> None:
        cells: List[Q] = []
        for x in coeffs:
            q = _to_q(x)
            if q is None:
                if isinstance(x, float):
                    raise TypeError(
                        "Poly coefficients must be EXACT (Q / int / (num, den) / "
                        "Fraction); a float must enter via Poly.from_floats, never "
                        f"silently — got float {x!r}")
                raise TypeError(
                    "Poly coefficients must be exact-rational (Q / int / "
                    f"(num, den) / Fraction); got {type(x).__name__}")
            cells.append(q)
        self._c = _trim(cells)

    # ── construction ───────────────────────────────────────────────────────
    @classmethod
    def from_coeffs(cls, seq) -> "Poly":
        """Build a ``Poly`` from an ascending-degree coefficient sequence (the
        canonical constructor). Each entry is coerced to an exact ``Q`` (``Q`` /
        ``int`` / ``(num, den)`` pair / ``Fraction``); a ``float`` is rejected —
        use :meth:`from_floats`."""
        return cls(seq)

    @classmethod
    def from_ints(cls, seq) -> "Poly":
        """Build from a sequence of integer coefficients (ascending degree)."""
        return cls([int(x) for x in seq])

    @classmethod
    def _wrap(cls, trimmed: Tuple[Q, ...]) -> "Poly":
        """Internal: wrap an ALREADY-trimmed tuple of ``Q`` with no re-coercion."""
        p = cls.__new__(cls)
        p._c = trimmed
        return p

    @classmethod
    def zero(cls) -> "Poly":
        """The zero polynomial (empty coefficient tuple; degree ``-1``)."""
        return cls._wrap(())

    @classmethod
    def one(cls) -> "Poly":
        """The constant polynomial ``1``."""
        return cls._wrap((_Q_ONE,))

    @classmethod
    def monomial(cls, deg: int, coeff=_Q_ONE) -> "Poly":
        """The single-term polynomial ``coeff * x**deg`` (``deg >= 0``)."""
        if not isinstance(deg, int) or deg < 0:
            raise ValueError(f"Poly.monomial: deg must be a non-negative int; got {deg!r}")
        q = _to_q(coeff)
        if q is None:
            raise TypeError(f"Poly.monomial: coeff not exact-rational: {coeff!r}")
        if q == 0:
            return cls._wrap(())
        return cls._wrap(tuple([_Q_ZERO] * deg + [q]))

    @classmethod
    def from_floats(cls, seq, *, max_denominator=None) -> "Poly":
        """Lift an ascending-degree sequence of FLOATS into the exact carrier —
        the explicit float→rational boundary (the one place a float legitimately
        enters). ``max_denominator is None`` promotes each float to its EXACT
        ratio (:meth:`srmech.amsc.q.Q.from_float`); a ``max_denominator`` instead
        SNAPS each coefficient to the best rational with denominator at or below
        that bound (Class-N :func:`srmech.amsc.rational.best_rational`)."""
        if max_denominator is None:
            return cls([Q.from_float(float(x)) for x in seq])
        from . import rational as _rational
        out: List[Q] = []
        for x in seq:
            exact = Q.from_float(float(x))
            num, den = exact.as_pair()
            p, q = _rational.best_rational(num, den, int(max_denominator))
            out.append(Q(p, q) if (p, q) != (0, 1) or exact == 0 else exact)
        return cls(out)

    # ── accessors ──────────────────────────────────────────────────────────
    @property
    def coeffs(self) -> Tuple[Q, ...]:
        """The trimmed ascending-degree coefficient tuple (each an exact ``Q``)."""
        return self._c

    @property
    def degree(self) -> int:
        """The polynomial degree. The zero polynomial has degree ``-1`` by
        convention (so ``deg(p*q) == deg p + deg q`` holds with the zero
        polynomial as the additive identity)."""
        return len(self._c) - 1

    @property
    def leading(self) -> Q:
        """The leading (highest-degree) coefficient; the zero polynomial returns
        ``Q(0)``."""
        return self._c[-1] if self._c else _Q_ZERO

    @property
    def is_zero(self) -> bool:
        """True iff this is the zero polynomial (empty coefficient tuple)."""
        return len(self._c) == 0

    def __len__(self) -> int:
        """The coefficient count (``degree + 1`` for a nonzero polynomial, ``0``
        for the zero polynomial)."""
        return len(self._c)

    def __getitem__(self, i: int) -> Q:
        """``p[i]`` → the exact ``Q`` coefficient of ``x**i`` (``Q(0)`` past the
        degree; a negative index is rejected — coefficients index by power)."""
        if not isinstance(i, int):
            raise TypeError("Poly index must be an int power i (the coeff of x**i)")
        if i < 0:
            raise IndexError("Poly index must be a non-negative power i")
        return self._c[i] if i < len(self._c) else _Q_ZERO

    def __iter__(self):
        """Iterate the trimmed coefficients in ascending degree."""
        return iter(self._c)

    def __eq__(self, other) -> bool:
        """Exact equality. Accepts another ``Poly`` or a coefficient sequence
        (coerced + trimmed for the compare)."""
        if other is self:
            return True
        if isinstance(other, Poly):
            return self._c == other._c
        try:
            o = Poly.from_coeffs(other)
        except (TypeError, ValueError):
            return NotImplemented
        return self._c == o._c

    def __ne__(self, other):
        result = self.__eq__(other)
        return result if result is NotImplemented else (not result)

    def __hash__(self) -> int:
        # Immutable (trimmed tuple of Q); equal polynomials hash equal.
        return hash(self._c)

    def __repr__(self) -> str:
        return f"Poly(degree={self.degree}, exact-rational)"

    # ── exact arithmetic (coefficientwise over Q; Class-K sign) ─────────────
    def __add__(self, other):
        o = self._as_poly(other)
        if o is None:
            return NotImplemented
        nat = _native()
        if nat is not None:
            try:
                pairs = nat.poly_add_c(_pairs(self._c), _pairs(o._c))
                if pairs is not None:
                    return Poly._wrap(_from_pairs(pairs))
            except (RuntimeError, OverflowError, ValueError):
                pass                                 # fall to the pure path
        n = max(len(self._c), len(o._c))
        out = [self[i] + o[i] for i in range(n)]
        return Poly._wrap(_trim(out))

    __radd__ = __add__

    def __neg__(self) -> "Poly":
        # The Class-K sign-flip over every coefficient (Q.__neg__; no ALU abs).
        return Poly._wrap(tuple(-a for a in self._c))

    def __sub__(self, other):
        o = self._as_poly(other)
        if o is None:
            return NotImplemented
        nat = _native()
        if nat is not None:
            try:
                pairs = nat.poly_sub_c(_pairs(self._c), _pairs(o._c))
                if pairs is not None:
                    return Poly._wrap(_from_pairs(pairs))
            except (RuntimeError, OverflowError, ValueError):
                pass
        n = max(len(self._c), len(o._c))
        out = [self[i] - o[i] for i in range(n)]
        return Poly._wrap(_trim(out))

    def __rsub__(self, other):
        o = self._as_poly(other)
        if o is None:
            return NotImplemented
        return o.__sub__(self)

    def __mul__(self, other):
        """Scalar multiply by a ``Q`` / ``int`` / ``Fraction`` / ``(num, den)``,
        OR the polynomial product (convolution) when ``other`` is a ``Poly`` /
        coercible coefficient sequence."""
        if isinstance(other, Poly):
            return self._mul_poly(other)
        q = _to_q(other)
        if q is not None:
            if q == 0:
                return Poly._wrap(())
            return Poly._wrap(tuple(a * q for a in self._c))
        o = self._as_poly(other)
        if o is None:
            return NotImplemented
        return self._mul_poly(o)

    __rmul__ = __mul__

    def _mul_poly(self, other: "Poly") -> "Poly":
        """The exact polynomial product (coefficient convolution) over ``Q``."""
        if self.is_zero or other.is_zero:
            return Poly._wrap(())
        nat = _native()
        if nat is not None:
            try:
                pairs = nat.poly_mul_c(_pairs(self._c), _pairs(other._c))
                if pairs is not None:
                    return Poly._wrap(_from_pairs(pairs))
            except (RuntimeError, OverflowError, ValueError):
                pass
        a, b = self._c, other._c
        out = [_Q_ZERO] * (len(a) + len(b) - 1)
        for i, ai in enumerate(a):
            if ai == 0:
                continue
            for j, bj in enumerate(b):
                out[i + j] = out[i + j] + ai * bj
        return Poly._wrap(_trim(out))

    def _as_poly(self, other) -> "Poly | None":
        """Coerce ``other`` to a ``Poly`` (a ``Poly`` passes through; a coercible
        coefficient sequence is wrapped), or ``None`` if not coercible."""
        if isinstance(other, Poly):
            return other
        q = _to_q(other)
        if q is not None:
            return Poly._wrap(() if q == 0 else (q,))
        try:
            return Poly.from_coeffs(other)
        except (TypeError, ValueError):
            return None

    # ── exact long division / GCD over ℚ ────────────────────────────────────
    def divmod(self, other) -> "Tuple[Poly, Poly]":
        """Polynomial long division over ℚ: returns ``(quotient, remainder)``
        with ``self == quotient * other + remainder`` and ``remainder`` either
        the zero polynomial or of degree strictly below ``other``. Raises
        ``ZeroDivisionError`` when ``other`` is the zero polynomial. Exact over
        ℚ, bigint — no float, no magnitude ceiling."""
        o = self._as_poly(other)
        if o is None:
            raise TypeError("Poly.divmod requires a Poly / coercible coefficient sequence")
        if o.is_zero:
            raise ZeroDivisionError("Poly.divmod by the zero polynomial")
        nat = _native()
        if nat is not None:
            try:
                got = nat.poly_divmod_c(_pairs(self._c), _pairs(o._c))
                if got is not None:
                    qp, rp = got
                    return Poly._wrap(_from_pairs(qp)), Poly._wrap(_from_pairs(rp))
            except (RuntimeError, OverflowError, ValueError):
                pass
        # Work on a mutable list of the remainder coefficients (ascending).
        rem = list(self._c)
        d_deg = o.degree
        d_lead = o.leading
        quo = [_Q_ZERO] * (max(len(rem) - len(o._c), -1) + 1) if len(rem) >= len(o._c) else []
        while len(rem) - 1 >= d_deg and _trim(rem):
            r_deg = len(rem) - 1
            shift = r_deg - d_deg
            factor = rem[r_deg] / d_lead          # exact ℚ leading-coeff divide
            quo[shift] = factor
            # rem -= factor * x**shift * other
            for j in range(len(o._c)):
                rem[shift + j] = rem[shift + j] - factor * o._c[j]
            rem = list(_trim(rem))
            if not rem:
                break
        return Poly._wrap(_trim(quo)), Poly._wrap(_trim(rem))

    def __divmod__(self, other):
        return self.divmod(other)

    def __floordiv__(self, other):
        o = self._as_poly(other)
        if o is None:
            return NotImplemented
        return self.divmod(o)[0]

    def __mod__(self, other):
        o = self._as_poly(other)
        if o is None:
            return NotImplemented
        return self.divmod(o)[1]

    def monic(self) -> "Poly":
        """The monic associate — divide through by the leading coefficient so the
        leading coefficient becomes ``1`` (the zero polynomial stays zero). The
        canonical-form normalization the GCD returns."""
        if self.is_zero:
            return Poly._wrap(())
        inv = _Q_ONE / self.leading
        return Poly._wrap(tuple(a * inv for a in self._c))

    def gcd(self, other) -> "Poly":
        """The Euclidean polynomial GCD over ℚ, **monic-normalized** (leading
        coefficient ``1``) so it is canonical. ``gcd(0, 0)`` is the zero
        polynomial; ``gcd(p, 0)`` is ``monic(p)``. Exact over ℚ, bigint."""
        o = self._as_poly(other)
        if o is None:
            raise TypeError("Poly.gcd requires a Poly / coercible coefficient sequence")
        # rc39: a dedicated single-call srmech_poly_gcd C peer now carries the
        # whole monic Euclidean chain natively when present. Its arena is
        # chain-scaled (per-step MONIC NORMALIZATION tames the ℚ-coefficient
        # growth from ~92× to ~23× input bits, and the cap carries degree-squared
        # headroom past that), so the native path runs the full Euclid loop in C.
        # The pure-Python bigint Euclid below is the COMPLETE alternative + the
        # parity oracle: it has no magnitude ceiling, and its inner long divisions
        # still route through srmech_poly_divmod when native is present. The
        # native peer falls back to it on ANY NativeError (incl. an OVERFLOW from
        # an input past the chain-scaled bound).
        nat = _native()
        if nat is not None and nat.has_native_poly_gcd():
            try:
                pairs = nat.poly_gcd_c(_pairs(self._c), _pairs(o._c))
                if pairs is not None:
                    return Poly._wrap(_from_pairs(pairs))
            except (RuntimeError, OverflowError, ValueError):
                pass                                  # fall to the pure path
        a, b = self, o
        # Euclid: a, b -> b, a mod b until b is zero; the last nonzero is the GCD.
        while not b.is_zero:
            a, b = b, a.divmod(b)[1]
        return a.monic()

    # ── evaluation / calculus / dispersion ──────────────────────────────────
    def eval(self, x) -> Q:
        """Evaluate at ``x`` (a ``Q`` / ``int`` / ``(num, den)`` / ``Fraction``)
        by exact Horner → an exact ``Q``. The empty (zero) polynomial evaluates
        to ``Q(0)``."""
        q = _to_q(x)
        if q is None:
            raise TypeError(f"Poly.eval: x not exact-rational: {x!r}")
        if self.is_zero:
            return _Q_ZERO
        nat = _native()
        if nat is not None:
            try:
                got = nat.poly_eval_c(_pairs(self._c), (q.numerator, q.denominator))
                if got is not None:
                    return Q(int(got[0]), int(got[1]))
            except (RuntimeError, OverflowError, ValueError):
                pass
        acc = _Q_ZERO
        for c in reversed(self._c):
            acc = acc * q + c
        return acc

    def derivative(self) -> "Poly":
        """The exact derivative ``p'(x)`` (coefficient ``i * coeffs[i]`` lands at
        degree ``i - 1``); a constant / the zero polynomial differentiates to the
        zero polynomial."""
        if len(self._c) <= 1:
            return Poly._wrap(())
        out = [self._c[i] * Q(i, 1) for i in range(1, len(self._c))]
        return Poly._wrap(_trim(out))

    def shift(self, h) -> "Poly":
        """The dispersion ``p(x + h)`` for an exact ``h`` (``Q`` / ``int`` /
        ``(num, den)`` / ``Fraction``) — the substrate primitive the §76
        Gosper / Zeilberger machinery needs to compare ``p(k)`` against
        ``p(k + 1)``. Computed by exact Horner on the polynomial ``(x + h)``
        (synthetic, no binomial table): start from the leading coefficient and
        fold ``acc = acc * (x + h) + c_i`` down the coefficients, where ``acc``
        is itself a ``Poly``. Exact over ℚ, no float."""
        qh = _to_q(h)
        if qh is None:
            raise TypeError(f"Poly.shift: h not exact-rational: {h!r}")
        if self.is_zero:
            return Poly._wrap(())
        nat = _native()
        if nat is not None:
            try:
                pairs = nat.poly_shift_c(_pairs(self._c), (qh.numerator, qh.denominator))
                if pairs is not None:
                    return Poly._wrap(_from_pairs(pairs))
            except (RuntimeError, OverflowError, ValueError):
                pass
        # linear = x + h  (ascending: [h, 1]).
        linear = Poly._wrap((qh, _Q_ONE)) if qh != 0 else Poly._wrap((_Q_ZERO, _Q_ONE))
        acc = Poly._wrap(())
        for c in reversed(self._c):
            acc = acc._mul_poly(linear) + Poly._wrap(() if c == 0 else (c,))
        return acc

    # ── resultant / dispersion (the §76 Gosper substrate; exact over ℚ) ──────
    def resultant(self, other) -> Q:
        """The EXACT resultant ``Res(self, other)`` as a ``Q``, via the
        subresultant-style **polynomial-remainder sequence** — NO matrix, NO
        determinant. The resultant is zero iff the two polynomials share a
        non-constant common factor, and it is the substrate the §76 Gosper
        **dispersion** rides on (the dispersion is the non-negative integer roots
        of ``Res_k(p(k), q(k+h))`` as a polynomial in ``h``).

        Reduction recurrence (each step exact over ℚ): for ``deg p = m ≥ deg q =
        n ≥ 1`` and ``r = p mod q``, ``Res(p, q) = (-1)^(m·n) · lc(q)^(m - deg r)
        · Res(q, r)``; the base cases are ``Res(p, c) = c^deg p`` for a constant
        ``c``, ``Res(p, q) = (-1)^(m·n) Res(q, p)`` when ``deg p < deg q``, and a
        zero result the instant a remainder vanishes (a shared factor). The sign
        is the **Class-K** pin-slot (an integer ``±1`` from the parity of ``m·n``,
        never an ALU ``abs()``). Exact, bigint, no float; matches the
        product-of-differences definition ``lc(p)^deg q · ∏ q(roots of p)``."""
        o = self._as_poly(other)
        if o is None:
            raise TypeError("Poly.resultant requires a Poly / coercible sequence")
        return _resultant(self, o)

    def dispersion(self, other) -> List[int]:
        """The EXACT **dispersion set** ``{ h ≥ 0 integer : deg gcd(self(k),
        other(k + h)) ≥ 1 }`` (the standard Gosper–Petkovšek convention: the
        SECOND argument is shifted by ``+h``). It is the set of non-negative
        integer shifts at which the two polynomials share a root, i.e. the
        non-negative integer roots of ``R(h) = Res_k(self(k), other(k + h))`` (a
        polynomial in ``h`` of degree ``≤ deg self · deg other``).

        Computed EXACTLY (no float): ``R(h)`` is reconstructed by Lagrange
        interpolation through ``deg self · deg other + 1`` exact ``(h_i,
        Res_k(self, other.shift(h_i)))`` points, then its non-negative integer
        roots are found by the rational-root theorem on the integer-cleared
        ``R(h)`` (each candidate confirmed by an exact ``R(h) == 0`` check). The
        list is sorted ascending; it is empty when the polynomials never overlap
        under a non-negative integer shift.

        Note on convention: the §76 Gosper / Petkovšek normal form needs exactly
        this set — the ``h`` at which ``gcd(a(k), b(k + h))`` is non-trivial,
        peeled to make ``gcd(a(k), b(k + h)) = 1 ∀ h ≥ 0``."""
        o = self._as_poly(other)
        if o is None:
            raise TypeError("Poly.dispersion requires a Poly / coercible sequence")
        return _dispersion(self, o)

    # ── the boundary collapse — the ONE rotation (ALU → FPU) ────────────────
    def to_floats(self) -> List[float]:
        """Collapse to a list of float64 coefficients (ascending degree) — the
        single ALU→FPU rotation / "rotation last" (the body stayed exact ``Q``
        until here). This is the ONLY place ``float()`` appears in the carrier,
        the exact analogue of :meth:`srmech.amsc.qmat.QMat.to_mat` /
        :meth:`srmech.amsc.q.Q.__float__` — the opt-in display boundary. The zero
        polynomial returns an empty list."""
        return [float(c) for c in self._c]


# ── exact resultant (subresultant-style PRS; module-level so it is iterative —
#    no recursion limit, JPL-spirit Rule 1) ─────────────────────────────────────
def _resultant(p: "Poly", q: "Poly") -> Q:
    """The exact resultant ``Res(p, q)`` via the polynomial-remainder sequence,
    written ITERATIVELY (the recurrence unrolled into a loop so a deep chain
    never trips Python's recursion limit). Exact ``Q``; the sign is the Class-K
    ``±1`` parity of ``deg p · deg q`` at each reduction. See :meth:`Poly.resultant`."""
    if p.is_zero or q.is_zero:
        return _Q_ZERO
    acc = _Q_ONE                                      # the running scale factor
    while True:
        dp, dq = p.degree, q.degree
        if dp == 0 and dq == 0:
            return acc                                # Res of two nonzero constants
        if dq == 0:                                   # Res(p, c) = c^deg p
            return acc * (q.leading ** dp)
        if dp == 0:                                   # Res(c, q) = c^deg q
            return acc * (p.leading ** dq)
        if dp < dq:                                   # swap, carry the (-1)^(mn) sign
            sgn = -1 if ((dp * dq) % 2) else 1
            acc = acc * Q(sgn, 1)
            p, q = q, p
            continue
        r = p.divmod(q)[1]
        if r.is_zero:
            return _Q_ZERO                            # a shared factor ⇒ resultant 0
        sgn = -1 if ((dp * dq) % 2) else 1
        acc = acc * Q(sgn, 1) * (q.leading ** (dp - r.degree))
        p, q = q, r


# ── exact dispersion (non-negative integer roots of Res_k(p(k), q(k+h))) ──────
def _int_divisors(n: int) -> List[int]:
    """The positive divisors of ``|n|`` (``[1]`` for ``n == 0``; the rational-root
    theorem only needs the divisors of the nonzero leading / trailing terms)."""
    n = n if n >= 0 else -n                           # Class-K magnitude, no abs()
    if n == 0:
        return [1]
    out: List[int] = []
    i = 1
    while i * i <= n:
        if n % i == 0:
            out.append(i)
            if i != n // i:
                out.append(n // i)
        i += 1
    return sorted(out)


def _dispersion(p: "Poly", q: "Poly") -> List[int]:
    """The non-negative integer roots of ``R(h) = Res_k(p(k), q(k + h))``,
    reconstructed exactly by Lagrange interpolation then sieved by the
    rational-root theorem. See :meth:`Poly.dispersion`."""
    if p.is_zero or q.is_zero:
        return []
    dp, dq = p.degree, q.degree
    if dp < 1 or dq < 1:
        return []                                     # a constant shares no root
    deg_h = dp * dq                                   # deg_h R(h) ≤ deg p · deg q
    # exact sample points (h_i, Res_k(p, q.shift(h_i))) for h_i = 0 .. deg_h
    rh = _interpolate([(Q(hi, 1), _resultant(p, q.shift(Q(hi, 1))))
                       for hi in range(deg_h + 1)])
    if rh.is_zero:
        # R(h) ≡ 0 ⇒ p, q share a factor at EVERY shift (degenerate); the
        # non-negative integer "roots" are unbounded — return [] (Gosper's GP-form
        # peeling only consumes a FINITE dispersion set; this degenerate input is
        # handled upstream). This never arises for the squarefree inputs Gosper
        # feeds dispersion (a, b coprime-after-content).
        return []
    return _nonneg_int_roots(rh)


def _interpolate(points) -> "Poly":
    """Exact Lagrange interpolation through ``(x_i, y_i)`` exact-``Q`` points →
    the unique ``Poly`` of degree ``< len(points)`` hitting them. Exact over ℚ."""
    result = Poly._wrap(())
    n = len(points)
    for i in range(n):
        xi, yi = points[i]
        if yi == 0:
            continue
        term = Poly._wrap((yi,))                      # the i-th Lagrange basis · y_i
        denom = _Q_ONE
        for j in range(n):
            if j == i:
                continue
            xj = points[j][0]
            term = term._mul_poly(Poly._wrap((-xj, _Q_ONE)))   # · (x - x_j)
            denom = denom * (xi - xj)
        inv = _Q_ONE / denom
        term = Poly._wrap(tuple(a * inv for a in term._c))
        result = result + term
    return result


def _nonneg_int_roots(rh: "Poly") -> List[int]:
    """The sorted non-negative INTEGER roots of an exact ``Poly`` ``R(h)``, via
    the rational-root theorem on its integer-cleared coefficients (each candidate
    confirmed by an exact ``R(h) == 0`` check — no float). ``h = 0`` is included
    iff the constant term is zero."""
    coeffs = list(rh._c)
    # clear denominators: multiply through by the lcm of the denominators
    lcm = 1
    for c in coeffs:
        d = c.denominator
        lcm = lcm // _gcd_int(lcm, d) * d
    ic = [int(c.numerator * (lcm // c.denominator)) for c in coeffs]
    roots: List[int] = []
    # strip a factor of h for each trailing-zero coefficient (h = 0 is a root)
    shift0 = 0
    while ic and ic[0] == 0:
        ic.pop(0)
        shift0 += 1
    if shift0 > 0:
        roots.append(0)
    while ic and ic[-1] == 0:
        ic.pop()
    if len(ic) <= 1:
        return sorted(set(roots))                     # only the h = 0 root (if any)
    a0, an = ic[0], ic[-1]
    cands = set()
    for pdiv in _int_divisors(a0):
        for qdiv in _int_divisors(an):
            if qdiv != 0 and pdiv % qdiv == 0:
                cands.add(pdiv // qdiv)               # integer candidates only
    for h in cands:
        if h > 0 and rh.eval(Q(h, 1)) == 0:
            roots.append(h)
    return sorted(set(roots))


def _gcd_int(a: int, b: int) -> int:
    """Integer GCD via the Class-I cyclic Euclid (no ``math.gcd`` import)."""
    a = a if a >= 0 else -a                            # Class-K magnitude, no abs()
    b = b if b >= 0 else -b
    while b:
        a, b = b, a % b
    return a


# ── the PROSE-SIDE constructor (rc113; #1239 / F1027 / UPSTREAM §85) ──────────
def _prose_int(value, *, where: str) -> int:
    """One prose-side integer coefficient: a plain ``int`` only (a ``bool`` /
    ``float`` / ``str`` / anything else is an honest ``TypeError``). Utterance
    leaves are integers — integers ARE exact ℚ, so the exact-carrier discipline
    is kept without a rational-pair grammar at the prose boundary (exact
    rationals enter via the in-process constructors)."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            f"{where}: coefficients must be plain ints (the exact-ℚ prose "
            f"contract; an exact rational enters via the in-process carrier "
            f"constructor, a float never enters); got {value!r}")
    return value


def poly_from_coeffs(coeffs) -> Poly:
    """Build the exact-ℚ polynomial carrier :class:`Poly` from an
    ascending-degree list of INTEGER coefficients — the PROSE-SIDE constructor
    ToolEntry (rc113; issue #1239 / F1027 / UPSTREAM §85). ``coeffs[i]`` is the
    coefficient of ``k**i``: ``poly_from_coeffs([0, 1])`` is ``k``,
    ``poly_from_coeffs([1, 1])`` is ``1 + k`` (the ordinary-row term-ratio
    building blocks the ``gosper`` / ``zeilberger`` / ``wz_certificate`` ops
    consume).

    Why it exists: the conversational grounded-inference loop binds only
    utterance-expressible operands (ints / floats / strs / bytes / edge-pairs)
    plus carriers CHAINED from a result register — and before rc113 no
    registered tool RETURNED a ``Poly``, so the Σ-row engines were unreachable
    by prose. This is a **non_compute BUILDER** (the ``coupling.from_bodies`` /
    ``text.cooccurrence_edges`` precedent): it constructs an operand; every
    computation lives in the ops that consume it.

    Ints only (a ``bool`` / ``float`` / ``str`` coefficient is an honest
    ``TypeError`` — the exact-ℚ discipline; integers are exact). No float, no
    ``abs()``, no numpy / ``math``."""
    if isinstance(coeffs, tuple):
        coeffs = list(coeffs)
    if not isinstance(coeffs, list):
        raise TypeError(
            "poly_from_coeffs: coeffs must be an ascending-degree list of "
            f"ints; got {type(coeffs).__name__}")
    return Poly.from_coeffs(
        [_prose_int(v, where="poly_from_coeffs") for v in coeffs])
