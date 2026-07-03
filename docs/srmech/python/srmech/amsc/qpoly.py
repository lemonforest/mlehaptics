"""srmech.amsc.qpoly — the framework-native EXACT q-shift CARRIER (``QPoly``): a
Laurent polynomial in ``x = q**n`` whose coefficients are exact polynomials in
``q`` (``ℚ[q]``). The q-analog of :class:`srmech.amsc.poly.Poly`, and the
foundation carrier of the q-hypergeometric F929 reduction row (q-Gosper →
q-Zeilberger → q-WZ).

Where :class:`~srmech.amsc.poly.Poly` carries a univariate polynomial over ℚ and
the ordinary shift ``p(k) ↦ p(k+1)`` is its summation payload, ``QPoly`` carries
the object q-summation operates on — a *Laurent* polynomial in the formal
variable ``x = q**n`` over the ground ring ``ℚ[q]`` — and the load-bearing new
operation is the **q-shift** ``σ : x ↦ q·x`` (i.e. ``f(q**n) ↦ f(q**(n+1))``),
the q-analog of the ordinary shift. The q-difference ``Δ_q f = σf − f`` is the
q-summation telescoping payload (the q-antidifference solver q-Gosper consumes
exactly :meth:`qshift` / :meth:`qdelta`).

Why ``ℚ[q]`` (the polynomial ring) and NOT ``ℚ(q)`` (rational functions): the
q-Gosper / q-Zeilberger machinery (Koornwinder, T.H., "On Zeilberger's algorithm
and its q-analogue," J. Comput. Appl. Math. 48 (1993) 91–111; textbook anchor
Gasper & Rahman, *Basic Hypergeometric Series*) manipulates the q-shift on
*polynomial* (q-)coefficients, and denominators in ``q`` enter ONLY at the
undetermined-coefficient LINEAR SOLVE stage — which is handled by the exact-``ℚ``
:class:`~srmech.amsc.qmat.QMat` Gauss-Jordan downstream, not by the carrier. So
the minimal sufficient ground ring for the carrier algebra (``+``, ``−``, ``*``,
the q-shift, the q-difference) is ``ℚ[q]``; carrying ``ℚ(q)`` here would be
premature denominators with no caller. Each q-coefficient is therefore a
:class:`~srmech.amsc.poly.Poly` over ℚ (a ``ℚ[q]`` element — exact bigint, no
magnitude ceiling), and ``QPoly`` reuses ``Poly``'s exact polynomial algebra for
every q-coefficient operation (the ``Poly`` C peer ``srmech_poly_*`` accelerates
those byte-identically).

Representation (mirrors ``Poly`` / ``BiPoly`` / ``TriPoly``):

- The carrier is a contiguous run of ``ℚ[q]`` coefficient *cells* over an
  x-exponent window ``[x_low, x_low + len)``: ``cells[i]`` (a ``Poly`` in ``q``)
  is the coefficient of ``x**(x_low + i)``. A *Laurent* polynomial needs the
  ``x_low`` offset because the q-shift's term-ratio algebra produces negative
  x-powers (``x**(-1)`` etc.) — unlike ``Poly`` (ascending-degree from 0),
  ``QPoly`` carries a signed low exponent.
- **Canonical form**: trim trailing-zero (high-x) AND leading-zero (low-x) cells,
  then renormalize ``x_low`` so the lowest-x cell is nonzero. The zero ``QPoly``
  is the empty cell tuple with ``x_low == 0`` (``x_degree == None`` / a degenerate
  span). Two ``QPoly`` are equal iff their trimmed cell tuples AND ``x_low``
  agree (exact ``Poly`` equality per q-coefficient).

Everything stays exact over ``ℚ[q]`` (each cell a bigint ``Poly``); ``+`` / ``−``
/ scalar-and-q-poly ``*`` / x-convolution ``*`` ride ``Poly``'s exact ℚ
arithmetic; :meth:`eval` substitutes an exact ``(q, x)`` to a single exact ``Q``;
:meth:`qshift` multiplies each x-cell by the monomial ``q**(s·e)`` (a pure
``ℚ[q]`` shift, the q-analog of the ordinary shift); :meth:`qdelta` is
``qshift(1) − self``. Sign is the **Class-K** pin-slot via ``Poly`` / ``Q``
sign-branches (never an ALU ``abs()``). The ONE place a ``float`` appears is
:meth:`to_floats` — the terminal ALU→FPU rotation (the exact analogue of
:meth:`srmech.amsc.poly.Poly.to_floats`). No ``math`` module, no numpy.

C peer: ``srmech_qpoly_*`` (``c/src/srmech_qpoly.c``) mirrors ``srmech_poly_*``'s
add/sub/mul + the q-shift, over caller-arena bignum (no int64/Q61 ceiling). The
pure-Python body here is the COMPLETE alternative (and the byte-identical parity
oracle); the native path falls cleanly back to it on any NativeError.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Sequence, Tuple

from .poly import Poly
from .q import Q

__all__ = ["QPoly", "qpoly_from_coeffs"]

_Q_ZERO = Q(0, 1)
_Q_ONE = Q(1, 1)
_POLY_ZERO = Poly.zero()
_POLY_ONE = Poly.one()


def _native():
    """The native ``_native`` module IF the rc54 ``srmech_qpoly_*`` peer is
    present and bound, else ``None`` — so the carrier dispatches to C when
    available and falls cleanly to the pure-Python body (the complete alternative
    + the parity oracle) otherwise. Imported lazily to avoid a bootstrap cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    probe = getattr(nat, "has_native_qpoly", None)
    return nat if (probe is not None and probe()) else None


def _as_qcoeff(value) -> "Poly | None":
    """Coerce ``value`` to an exact ``ℚ[q]`` coefficient (a :class:`Poly` in
    ``q``), or ``None`` if not coercible. A bare exact scalar (``Q`` / ``int`` /
    ``(num, den)`` / ``Fraction``) becomes the constant ``Poly``; a ``Poly``
    passes through; a coefficient sequence is read as an ascending-``q``-degree
    ``Poly``. A ``float`` is REJECTED (returns ``None``) — exact only."""
    if isinstance(value, Poly):
        return value
    if isinstance(value, float):
        return None
    if isinstance(value, (Q, int, Fraction, bool)):
        try:
            return Poly.from_coeffs([value])
        except (TypeError, ValueError):
            return None
    if (isinstance(value, (tuple, list)) and len(value) == 2
            and isinstance(value[0], int) and isinstance(value[1], int)
            and value[1] != 0):
        return Poly.from_coeffs([Q(value[0], value[1])])
    try:
        return Poly.from_coeffs(value)
    except (TypeError, ValueError):
        return None


def _qp_canon(cells: Sequence[Poly], x_low: int) -> "Tuple[Tuple[Poly, ...], int]":
    """Canonicalize an x-cell sequence + low exponent: drop trailing-zero (high-x)
    and leading-zero (low-x) cells, renormalizing ``x_low`` so the lowest-x cell is
    nonzero. The zero polynomial → ``((), 0)``."""
    lo, hi = 0, len(cells)
    while lo < hi and cells[lo].is_zero:
        lo += 1
    while hi > lo and cells[hi - 1].is_zero:
        hi -= 1
    if lo >= hi:
        return (), 0
    return tuple(cells[lo:hi]), x_low + lo


class QPoly:
    """A numpy-free EXACT q-shift carrier: a Laurent polynomial in ``x = q**n``
    with exact ``ℚ[q]`` (``Poly``-in-``q``) coefficients, immutable. The q-analog
    of :class:`srmech.amsc.poly.Poly`. The carrier ships with its q-algebra
    (``+`` / ``−`` / ``*`` / :meth:`qshift` / :meth:`qdelta`), peer of
    ``Poly`` / ``BiPoly`` / ``TriPoly``. Collapses to floats only via
    :meth:`to_floats`. See the module docstring."""

    __slots__ = ("_c", "_lo")

    def __init__(self, cells: Sequence[Poly] = (), x_low: int = 0) -> None:
        if not isinstance(x_low, int):
            raise TypeError("QPoly x_low must be an int (the lowest x-exponent)")
        coerced: List[Poly] = []
        for c in cells:
            p = _as_qcoeff(c)
            if p is None:
                if isinstance(c, float):
                    raise TypeError(
                        "QPoly q-coefficients must be EXACT (Poly / Q / int / "
                        "(num, den) / Fraction / coeff-seq); a float must enter "
                        f"via QPoly.from_floats, never silently — got float {c!r}")
                raise TypeError(
                    "QPoly q-coefficients must be exact-rational ℚ[q] (Poly / Q / "
                    f"int / (num, den) / Fraction / coeff-seq); got {type(c).__name__}")
            coerced.append(p)
        self._c, self._lo = _qp_canon(coerced, x_low)

    # ── construction ───────────────────────────────────────────────────────
    @classmethod
    def _wrap(cls, cells: Tuple[Poly, ...], x_low: int) -> "QPoly":
        """Internal: wrap an ALREADY-canonical (trimmed both ends, normalized
        ``x_low``) cell tuple with no re-coercion. Callers MUST pass canonical
        input (use :meth:`_make` to canonicalize)."""
        q = cls.__new__(cls)
        q._c = cells
        q._lo = x_low if cells else 0
        return q

    @classmethod
    def _make(cls, cells: Sequence[Poly], x_low: int) -> "QPoly":
        """Internal: canonicalize a (cells, x_low) pair → a wrapped ``QPoly``."""
        c, lo = _qp_canon(list(cells), x_low)
        return cls._wrap(c, lo)

    @classmethod
    def from_coeffs(cls, seq, x_low: int = 0) -> "QPoly":
        """Build a ``QPoly`` from an ascending-x-exponent coefficient sequence (the
        canonical constructor, mirroring :meth:`Poly.from_coeffs`). ``seq[i]`` is
        the ``ℚ[q]`` coefficient of ``x**(x_low + i)`` — each coerced via
        :func:`_as_qcoeff` (a ``Poly`` in ``q``, a bare exact scalar → a constant
        ``Poly``, or an ascending-``q``-degree coefficient sequence). ``x_low`` is
        the (possibly negative) lowest x-exponent — default 0."""
        return cls(seq, x_low)

    @classmethod
    def from_dict(cls, terms) -> "QPoly":
        """Build from a sparse ``{(e, d): coeff}`` mapping — ``coeff`` is the exact
        ``Q`` (``Q`` / ``int`` / ``(num, den)`` / ``Fraction``) coefficient of the
        monomial ``x**e · q**d`` (``e`` the x-exponent, possibly negative; ``d`` the
        q-degree, ``≥ 0``). The natural constructor for a q-hypergeometric term
        written monomial-by-monomial. A ``float`` coefficient is rejected; a
        negative q-degree is rejected."""
        if not terms:
            return cls._wrap((), 0)
        e_lo = min(e for (e, _d) in terms)
        e_hi = max(e for (e, _d) in terms)
        # gather {e: {d: q}} then build a Poly-in-q per x-exponent cell.
        grid: Dict[int, Dict[int, Q]] = {}
        for key, coeff in terms.items():
            e, d = key
            if not (isinstance(e, int) and isinstance(d, int)):
                raise TypeError("QPoly.from_dict keys must be (e, d) ints")
            if d < 0:
                raise ValueError("QPoly.from_dict: q-degree d must be non-negative")
            qv = _as_qcoeff(coeff)
            if qv is None or qv.degree > 0:
                raise TypeError(
                    "QPoly.from_dict coefficients must be exact-rational scalars "
                    f"(Q / int / (num, den) / Fraction); got {coeff!r}")
            cell = grid.setdefault(e, {})
            scalar = qv[0] if not qv.is_zero else _Q_ZERO
            cell[d] = cell.get(d, _Q_ZERO) + scalar
        cells: List[Poly] = []
        for e in range(e_lo, e_hi + 1):
            cell = grid.get(e, {})
            if not cell:
                cells.append(_POLY_ZERO)
                continue
            dmax = max(cell)
            cells.append(Poly.from_coeffs([cell.get(d, _Q_ZERO) for d in range(dmax + 1)]))
        return cls._make(cells, e_lo)

    @classmethod
    def zero(cls) -> "QPoly":
        """The zero q-polynomial (empty cell tuple; degree span ``None``)."""
        return cls._wrap((), 0)

    @classmethod
    def one(cls) -> "QPoly":
        """The constant q-polynomial ``1`` (a single ``x**0`` cell carrying the
        constant ``Poly`` ``1``)."""
        return cls._wrap((_POLY_ONE,), 0)

    @classmethod
    def x_monomial(cls, e: int, coeff=_Q_ONE) -> "QPoly":
        """The single x-monomial ``coeff · x**e`` (``e`` any int; ``coeff`` an
        exact ``ℚ[q]`` coefficient — ``Poly`` / scalar / coeff-seq). The q-analog
        of :meth:`Poly.monomial`."""
        if not isinstance(e, int):
            raise TypeError(f"QPoly.x_monomial: e must be an int; got {e!r}")
        p = _as_qcoeff(coeff)
        if p is None:
            raise TypeError(f"QPoly.x_monomial: coeff not exact ℚ[q]: {coeff!r}")
        if p.is_zero:
            return cls._wrap((), 0)
        return cls._wrap((p,), e)

    @classmethod
    def from_q_poly(cls, p: Poly, e: int = 0) -> "QPoly":
        """A polynomial in ``q`` ALONE (a ``ℚ[q]`` element) → the single-x-cell
        ``QPoly`` ``p(q) · x**e`` (default the ``x**0`` constant)."""
        if not isinstance(e, int):
            raise TypeError("QPoly.from_q_poly: e must be an int")
        return cls._wrap(() if p.is_zero else (p,), e)

    @classmethod
    def from_floats(cls, seq, x_low: int = 0, *, max_denominator=None) -> "QPoly":
        """Lift an ascending-x sequence of FLOAT-coefficient ``ℚ[q]`` cells into
        the exact carrier — each entry an ascending-``q``-degree float sequence
        promoted via :meth:`Poly.from_floats` (the one place a float legitimately
        enters). ``max_denominator`` snaps each q-coefficient to the best rational
        at or below that bound; ``None`` promotes to the EXACT ratio."""
        cells = [Poly.from_floats(run, max_denominator=max_denominator) for run in seq]
        return cls._make(cells, x_low)

    # ── accessors ──────────────────────────────────────────────────────────
    @property
    def cells(self) -> Tuple[Poly, ...]:
        """The trimmed ascending-x ``ℚ[q]`` coefficient cells (each a ``Poly`` in
        ``q``); ``cells[i]`` is the coefficient of ``x**(x_low + i)``."""
        return self._c

    @property
    def x_low(self) -> int:
        """The lowest x-exponent carried (the offset of ``cells[0]``). 0 for the
        zero polynomial."""
        return self._lo

    @property
    def x_high(self) -> int:
        """The highest x-exponent carried (``x_low + len - 1``). For the zero
        polynomial this is ``x_low - 1`` (an empty span)."""
        return self._lo + len(self._c) - 1

    @property
    def is_laurent(self) -> bool:
        """True iff this carries a negative x-exponent (a genuine Laurent tail)."""
        return self._lo < 0

    @property
    def is_zero(self) -> bool:
        """True iff this is the zero q-polynomial (empty cell tuple)."""
        return len(self._c) == 0

    def q_degree(self) -> int:
        """The maximum ``q``-degree across all x-cells (the degree in ``q`` of the
        ground-ring ``ℚ[q]`` content). The zero polynomial returns ``-1``."""
        d = -1
        for c in self._c:
            if c.degree > d:
                d = c.degree
        return d

    def x_coeff(self, e: int) -> Poly:
        """The ``ℚ[q]`` coefficient (``Poly`` in ``q``) of ``x**e`` — the zero
        ``Poly`` outside the carried span."""
        i = e - self._lo
        if 0 <= i < len(self._c):
            return self._c[i]
        return _POLY_ZERO

    def __len__(self) -> int:
        """The x-cell count (``x_high − x_low + 1`` for nonzero; 0 for zero)."""
        return len(self._c)

    def __eq__(self, other) -> bool:
        """Exact equality: same canonical cell tuple AND same ``x_low``. Accepts
        another ``QPoly`` (a bare coefficient sequence is NOT coerced — the
        x_low offset is ambiguous, so only QPoly compares)."""
        if other is self:
            return True
        if isinstance(other, QPoly):
            return self._lo == other._lo and self._c == other._c
        return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        return result if result is NotImplemented else (not result)

    def __hash__(self) -> int:
        return hash((self._lo, self._c))

    def __repr__(self) -> str:
        if self.is_zero:
            return "QPoly(zero)"
        return (f"QPoly(x_low={self._lo}, x_high={self.x_high}, "
                f"q_degree={self.q_degree()}, exact ℚ[q])")

    # ── exact arithmetic (cellwise over ℚ[q]; Class-K sign) ──────────────────
    def _as_qpoly(self, other) -> "QPoly | None":
        """Coerce ``other`` to a ``QPoly`` (a ``QPoly`` passes through; a bare exact
        ``ℚ[q]`` scalar/Poly becomes an ``x**0`` cell), or ``None`` if not
        coercible."""
        if isinstance(other, QPoly):
            return other
        p = _as_qcoeff(other)
        if p is not None:
            return QPoly._wrap(() if p.is_zero else (p,), 0)
        return None

    def __add__(self, other):
        o = self._as_qpoly(other)
        if o is None:
            return NotImplemented
        return self._addsub(o, sub=False)

    __radd__ = __add__

    def __neg__(self) -> "QPoly":
        # The Class-K sign-flip over every q-cell (Poly.__neg__; no ALU abs).
        return QPoly._wrap(tuple(-c for c in self._c), self._lo)

    def __sub__(self, other):
        o = self._as_qpoly(other)
        if o is None:
            return NotImplemented
        return self._addsub(o, sub=True)

    def __rsub__(self, other):
        o = self._as_qpoly(other)
        if o is None:
            return NotImplemented
        return o._addsub(self, sub=True)

    def _addsub(self, other: "QPoly", *, sub: bool) -> "QPoly":
        """Exact cellwise ``self ± other`` over the union x-window. Each overlapping
        cell is a ``Poly`` add/sub (riding the ``Poly`` ℚ arithmetic + its C peer);
        non-overlapping cells pass through (negated for ``sub``)."""
        if self.is_zero:
            return (-other) if sub else other
        if other.is_zero:
            return self
        nat = _native()
        if nat is not None:
            try:
                got = nat.qpoly_addsub_c(_qp_pairs(self), _qp_pairs(other), sub)
                if got is not None:
                    return _qp_from_pairs(got)
            except (RuntimeError, OverflowError, ValueError):
                pass                                  # fall to the pure path
        lo = min(self._lo, other._lo)
        hi = max(self.x_high, other.x_high)
        out: List[Poly] = []
        for e in range(lo, hi + 1):
            a = self.x_coeff(e)
            b = other.x_coeff(e)
            out.append((a - b) if sub else (a + b))
        return QPoly._make(out, lo)

    def __mul__(self, other):
        """Scalar / ``ℚ[q]`` multiply (a ``Q`` / ``int`` / ``Fraction`` /
        ``(num, den)`` / ``Poly``-in-``q``), OR the x-convolution product when
        ``other`` is a ``QPoly``."""
        if isinstance(other, QPoly):
            return self._mul_qpoly(other)
        p = _as_qcoeff(other)
        if p is not None:
            if p.is_zero:
                return QPoly._wrap((), 0)
            return QPoly._wrap(tuple(c * p for c in self._c), self._lo)
        return NotImplemented

    __rmul__ = __mul__

    def _mul_qpoly(self, other: "QPoly") -> "QPoly":
        """The exact x-convolution product over ``ℚ[q]``: each output x-cell is a
        sum of ``Poly``-in-``q`` products (the q-coefficient ring multiply). The
        result x-window is ``[x_low_a + x_low_b, x_high_a + x_high_b]``."""
        if self.is_zero or other.is_zero:
            return QPoly._wrap((), 0)
        nat = _native()
        if nat is not None:
            try:
                got = nat.qpoly_mul_c(_qp_pairs(self), _qp_pairs(other))
                if got is not None:
                    return _qp_from_pairs(got)
            except (RuntimeError, OverflowError, ValueError):
                pass
        a, b = self._c, other._c
        out: List[Poly] = [_POLY_ZERO] * (len(a) + len(b) - 1)
        for i, ai in enumerate(a):
            if ai.is_zero:
                continue
            for j, bj in enumerate(b):
                if bj.is_zero:
                    continue
                out[i + j] = out[i + j] + ai * bj
        return QPoly._make(out, self._lo + other._lo)

    # ── the q-shift / q-difference (the q-summation payload) ─────────────────
    def qshift(self, s: int = 1) -> "QPoly":
        """The **q-shift** ``σ**s : x ↦ q**s · x`` (i.e. ``f(q**n) ↦ f(q**(n+s))``),
        the q-analog of the ordinary shift and the load-bearing q-summation
        operation. Under ``x ↦ q**s · x`` the ``x**e`` cell ``c_e(q)·x**e`` becomes
        ``c_e(q)·q**(s·e)·x**e`` — so every x-cell is multiplied by the monomial
        ``q**(s·e)`` (a pure exact ``ℚ[q]`` shift; the x-window is UNCHANGED).
        ``s`` may be any int (``s = 1`` is ``σ``, ``s = -1`` is ``σ**(-1)``).
        Exact over ``ℚ[q]``, no float. This is exactly what a q-antidifference
        solver (q-Gosper, rc55) consumes."""
        if not isinstance(s, int):
            raise TypeError("QPoly.qshift: s must be an int")
        if s == 0 or self.is_zero:
            return self
        nat = _native()
        if nat is not None:
            try:
                got = nat.qpoly_qshift_c(_qp_pairs(self), s)
                if got is not None:
                    return _qp_from_pairs(got)
            except (RuntimeError, OverflowError, ValueError):
                pass
        out: List[Poly] = []
        for i, c in enumerate(self._c):
            if c.is_zero:
                out.append(_POLY_ZERO)
                continue
            e = self._lo + i
            shift = s * e
            if shift == 0:
                out.append(c)
            elif shift > 0:
                # multiply by q**shift: prepend `shift` zero q-degrees.
                out.append(Poly.monomial(shift)._mul_poly(c))
            else:
                # q**shift with shift < 0 would leave ℚ[q] — only happens when an
                # input already carries the matching q-content; q-Gosper feeds
                # non-negative shifts here (e cells with s·e ≥ 0). Guard honestly.
                raise ValueError(
                    "QPoly.qshift: q-shift by a NEGATIVE q-power would leave ℚ[q] "
                    f"(s={s}, e={e}, s·e={shift}); the carrier ground ring is ℚ[q]. "
                    "A genuine Laurent-in-q result needs the ℚ(q) carrier (a future "
                    "QPolyRational); q-Gosper feeds only non-negative s·e here.")
        return QPoly._make(out, self._lo)

    def qdelta(self) -> "QPoly":
        """The **q-difference** ``Δ_q f = σf − f = f(q**(n+1)) − f(q**n)`` (``=
        qshift(1) − self``), the q-summation telescoping payload. A q-telescoping
        identity ``Σ Δ_q T = T(top) − T(bottom)`` holds exactly (the carrier's
        cellwise exactness), so q-Gosper's antidifference ``T`` with ``Δ_q T = t``
        is verified here byte-exact."""
        return self.qshift(1) - self

    # ── evaluation ──────────────────────────────────────────────────────────
    def eval(self, q_val, x_val) -> Q:
        """Evaluate at exact ``(q, x)`` (each a ``Q`` / ``int`` / ``(num, den)`` /
        ``Fraction``) → a single exact ``Q``: substitute ``q`` into every ``ℚ[q]``
        cell, then sum ``cell(q)·x**e`` over the x-window. A negative x-exponent
        needs ``x ≠ 0`` (a Laurent term ``x**(-1)``); ``x == 0`` with a Laurent tail
        raises ``ZeroDivisionError``. The zero polynomial evaluates to ``Q(0)``."""
        qq = _coerce_scalar(q_val)
        qx = _coerce_scalar(x_val)
        if qq is None or qx is None:
            raise TypeError(
                f"QPoly.eval: q, x must be exact-rational; got {q_val!r}, {x_val!r}")
        if self.is_zero:
            return _Q_ZERO
        if qx == 0 and self._lo < 0:
            raise ZeroDivisionError(
                "QPoly.eval: x == 0 with a negative x-exponent (Laurent) term")
        acc = _Q_ZERO
        # x**x_low factored out: acc = (Σ cell_i(q) · x**i) · x**x_low.
        inner = _Q_ZERO
        for c in reversed(self._c):                  # Horner in x over the cells
            inner = inner * qx + c.eval(qq)
        if self._lo == 0:
            acc = inner
        elif self._lo > 0:
            acc = inner * (qx ** self._lo)
        else:
            # x**x_low with x_low < 0 (qx != 0 guaranteed above): exact ℚ power.
            acc = inner * (_Q_ONE / (qx ** (-self._lo)))
        return acc

    # ── the boundary collapse — the ONE rotation (ALU → FPU) ────────────────
    def to_floats(self) -> "Tuple[List[List[float]], int]":
        """Collapse to ``(cells_as_float_runs, x_low)`` — each x-cell a list of
        float64 ``q``-coefficients (ascending q-degree) — the single ALU→FPU
        rotation / "rotation last" (the body stayed exact ``Poly`` until here). The
        ONLY place ``float()`` appears in the carrier (the exact analogue of
        :meth:`srmech.amsc.poly.Poly.to_floats`). The zero polynomial → ``([], 0)``."""
        return [c.to_floats() for c in self._c], self._lo


# ── module-level helpers (coercion + the C bridge wire form) ──────────────────
def _coerce_scalar(value) -> "Q | None":
    """Coerce an exact scalar (``Q`` / ``int`` / ``(num, den)`` / ``Fraction``) to
    a ``Q``, or ``None``. A ``float`` is rejected."""
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
    return None


# The C bridge wire form: a QPoly → (x_low, [ [(num, den), …]_q ]_x) — the x-low
# offset plus an ascending-x list, each entry an ascending-q-degree list of
# (num, den) Poly coefficients. The C peer flattens the x-row of q-runs into a
# single concatenated _SrmechBigint pair (mirroring the Poly/TriPoly bridge).
def _qp_pairs(p: "QPoly") -> "Tuple[int, List[List[Tuple[int, int]]]]":
    """A ``QPoly`` → the ``(x_low, [[(num, den), …]_q]_x)`` bridge form the C peer
    consumes (x-major, then ascending-``q`` ``Poly`` coefficients)."""
    rows: List[List[Tuple[int, int]]] = []
    for c in p._c:
        rows.append([(co.numerator, co.denominator) for co in c.coeffs])
    return p._lo, rows


def _qp_from_pairs(form) -> "QPoly":
    """Rebuild a ``QPoly`` from the ``(x_low, [[(num, den), …]_q]_x)`` bridge form
    (from the C peer; each leaf already reduced)."""
    x_low, rows = form
    cells = [Poly.from_coeffs([Q(int(n), int(d)) for n, d in run]) for run in rows]
    return QPoly._make(cells, int(x_low))


# ── the PROSE-SIDE constructor (rc113; #1239 / F1027 / UPSTREAM §85) ──────────
def _prose_qcell(entry, *, where: str) -> Poly:
    """One prose-side x-cell — an exact ``ℚ[q]`` coefficient from integer
    leaves ONLY:

    - an ``int`` → the constant coefficient (a degree-0 ``Poly`` in ``q``);
    - a ``list`` / ``tuple`` of ints → the **ascending-q-degree** coefficient
      ``[c0, c1, …] = c0 + c1·q + …`` (a ``Poly`` in ``q``).

    UNLIKE the in-process :func:`_as_qcoeff` (where a 2-int list is a
    ``(num, den)`` RATIONAL pair), a list here is ALWAYS the ascending-q form —
    ``[0, 1]`` is ``q``, never ``0/1`` — so the prose contract is unambiguous
    at every nesting depth. A ``bool`` / ``float`` / ``str`` leaf is an honest
    ``TypeError`` (the exact-ℚ discipline; integers are exact)."""
    if isinstance(entry, bool):
        raise TypeError(
            f"{where}: a bool is not a coefficient; use plain ints")
    if isinstance(entry, int):
        return Poly.from_coeffs([entry])
    if isinstance(entry, (list, tuple)):
        out = []
        for v in entry:
            if isinstance(v, bool) or not isinstance(v, int):
                raise TypeError(
                    f"{where}: an ascending-q coefficient list must hold plain "
                    f"ints (the exact-ℚ prose contract — [0, 1] is q, never a "
                    f"rational pair); got {v!r}")
            out.append(v)
        return Poly.from_coeffs(out)
    raise TypeError(
        f"{where}: each cell must be an int (a constant ℚ[q] coefficient) or "
        f"an ascending-q-degree list of ints; got {type(entry).__name__}")


def qpoly_from_coeffs(coeffs, x_low: int = 0) -> QPoly:
    """Build the exact q-shift carrier :class:`QPoly` from an ascending-x list
    of INTEGER-LEAF coefficient cells — the PROSE-SIDE constructor ToolEntry
    (rc113; issue #1239 / F1027 / UPSTREAM §85). ``coeffs[i]`` is the ``ℚ[q]``
    coefficient of ``x**(x_low + i)`` (``x = q**k``), where each cell is:

    - an ``int`` — a constant-in-``q`` coefficient;
    - a ``list`` of ints — the **ascending-q-degree** coefficient
      (``[0, 1]`` is ``q``; ``[0, 2]`` is ``2q``; ``[0, 0, 1]`` is ``q²``).

    Worked forms (the mock-theta / q-row operands the pipeline needs):

    - the q-geometric ratio ``x``: ``qpoly_from_coeffs([0, 1])``;
    - the order-3 mock-theta term ratio ``q·x² / (1+q·x)²``:
      numerator ``qpoly_from_coeffs([0, 0, [0, 1]])``,
      denominator ``qpoly_from_coeffs([1, [0, 2], [0, 0, 1]])``.

    ``x_low`` (optional int, default 0) is the lowest x-exponent — a negative
    value carries a genuine Laurent tail.

    Why it exists: the conversational grounded-inference loop binds only
    utterance-expressible operands and chains returned carriers via its result
    register — and before rc113 no registered tool RETURNED a ``QPoly``, so
    the q-row engine (``q_gosper`` / ``q_zeilberger`` / ``q_wz_certificate``)
    was unreachable by prose. A **non_compute BUILDER** (the
    ``coupling.from_bodies`` / ``text.cooccurrence_edges`` precedent).

    NOTE the deliberate contrast with the in-process ``QPoly.from_coeffs``
    cell coercion: there a 2-int list is a ``(num, den)`` rational pair; HERE a
    list is ALWAYS ascending-q-degree ints (unambiguous prose grammar; exact
    rationals enter via the in-process constructor). No float, no ``abs()``,
    no numpy / ``math``."""
    if isinstance(coeffs, tuple):
        coeffs = list(coeffs)
    if not isinstance(coeffs, list):
        raise TypeError(
            "qpoly_from_coeffs: coeffs must be an ascending-x list of integer "
            f"cells (int, or ascending-q list of ints); got {type(coeffs).__name__}")
    if isinstance(x_low, bool) or not isinstance(x_low, int):
        raise TypeError(
            f"qpoly_from_coeffs: x_low must be an int; got {x_low!r}")
    cells = [_prose_qcell(e, where="qpoly_from_coeffs") for e in coeffs]
    return QPoly(cells, x_low)
