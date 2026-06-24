"""srmech.amsc.qbipoly — the framework-native EXACT bivariate-q CARRIER
(``QBiPoly``): a polynomial in ``Y = q**k`` whose coefficients are
:class:`~srmech.amsc.qpoly.QPoly` in ``X = q**n`` (themselves Laurent in ``X`` over
``ℚ[q]``). The q-analog of :class:`~srmech.amsc.zeilberger.BiPoly`, and the working
substrate the q-Zeilberger creative-telescoping recurrence-finder (rc56) rides.

Where :class:`~srmech.amsc.zeilberger.BiPoly` carries a bivariate polynomial in the
*ordinary* shift variables ``(n, k)`` — a polynomial in ``k`` whose coefficients are
:class:`~srmech.amsc.poly.Poly` in ``n``, with the ordinary shifts ``n ↦ n+1`` /
``k ↦ k+1`` as its summation payload — ``QBiPoly`` carries the object q-summation
operates on, one ring up: a polynomial in ``Y = q**k`` whose coefficients are
:class:`~srmech.amsc.qpoly.QPoly` in ``X = q**n`` over the ground ring ``ℚ[q]``, and
the load-bearing operations are the two **q-shifts**

  * ``σ_x : X ↦ q·X``   (``F(q**n, q**k) ↦ F(q**(n+1), q**k)``, the n-direction
    q-shift) — applied to every ``QPoly`` cell via :meth:`QPoly.qshift`;
  * ``σ_y : Y ↦ q·Y``   (``F(q**n, q**k) ↦ F(q**n, q**(k+1))``, the k-direction
    q-shift) — multiplies the ``Y**d`` cell by ``q**(s·d)`` (a pure ``ℚ[q]`` shift,
    leaving the ``QPoly`` cell's X-window unchanged).

These are the two-dimensional analog of :meth:`BiPoly.shift_n` / :meth:`BiPoly.
shift_k`, which is exactly what the q-Zeilberger ansatz needs: ``ρ_j(X,Y) =
F(n+j,k)/F(n,k) = ∏_{i<j} r_n(q**i·X, Y)`` (a product of σ_x-shifts of the
``n``-term-ratio), and the q-Gosper-in-k certificate equation (the ``k ↦ k+1`` shift
is σ_y). The q-coefficient field denominators in ``q`` enter ONLY at the
undetermined-coefficient LINEAR SOLVE stage (handled over the field ``ℚ(q)`` by the
rc55 q-Gosper solve internals, NOT by the carrier), so the minimal sufficient ground
ring for the carrier algebra (``+``, ``−``, ``*``, the two q-shifts) is ``ℚ[q]`` —
each cell a :class:`~srmech.amsc.qpoly.QPoly` over ``ℚ[q]``.

Representation (mirrors :class:`~srmech.amsc.zeilberger.BiPoly`): a list of
``QPoly``-in-``X``, indexed by ``Y``-degree. ``terms[d]`` is the coefficient of
``Y**d`` and is itself a ``QPoly`` (Laurent in ``X = q**n`` over ``ℚ[q]``). Trailing
zero ``QPoly`` cells are trimmed, so the zero ``QBiPoly`` is the empty list and the
``Y``-degree is ``len(terms) − 1``. The ``Y`` part is non-Laurent (ascending from
``Y**0``) — the q-hypergeometric TERM RATIOS the q-Zeilberger op consumes are given
as ``num / den`` with non-negative ``Y`` powers, exactly as ``BiPoly`` carries the
ordinary ratios non-Laurent in ``k``; the ``X`` (n-direction) part carries the full
Laurent window inside each ``QPoly`` cell.

Everything stays exact over ``ℚ[q]`` (each cell a bigint ``QPoly``); ``+`` / ``−`` /
``*`` ride ``QPoly``'s exact ``ℚ[q]`` arithmetic; the q-shifts ride
:meth:`QPoly.qshift` (σ_x) and a pure ``ℚ[q]`` ``Y``-degree monomial multiply (σ_y).
Sign is the **Class-K** pin-slot via the ``QPoly`` / ``Poly`` / ``Q`` sign-branches
(never an ALU ``abs()``). No ``math`` module, no numpy.

The carrier is internal-to-the-q-Zeilberger-arc (like ``BiPoly`` is to
``zeilberger`` — not a standalone ToolEntry); it is the q-row peer of ``BiPoly`` /
``TriPoly``.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

from .poly import Poly
from .q import Q
from .qpoly import QPoly

__all__ = ["QBiPoly"]

_POLY_ONE = Poly.one()


def _qb_trim(cells: Sequence[QPoly]) -> Tuple[QPoly, ...]:
    """Drop trailing-zero (high-``Y``-degree) ``QPoly`` coefficients → canonical
    form."""
    n = len(cells)
    while n > 0 and cells[n - 1].is_zero:
        n -= 1
    return tuple(cells[:n])


class QBiPoly:
    """An exact bivariate-q polynomial in ``(X, Y) = (q**n, q**k)`` — a polynomial in
    ``Y = q**k`` whose coefficients are :class:`~srmech.amsc.qpoly.QPoly` in ``X =
    q**n`` (Laurent over ``ℚ[q]``). Immutable, trimmed of trailing-zero ``Y``-cells
    (the zero polynomial is the empty term list). The q-analog of
    :class:`~srmech.amsc.zeilberger.BiPoly`; the exact substrate the q-Zeilberger
    term-ratio ``r_n(X,Y)`` / ``r_k(X,Y)`` operands ride. No float, no ``abs()``
    (Class-K sign), no ``math`` / numpy. See the module docstring."""

    __slots__ = ("_t",)

    def __init__(self, terms: Sequence[QPoly] = ()) -> None:
        cells: List[QPoly] = []
        for c in terms:
            cells.append(c if isinstance(c, QPoly) else _as_xcell(c))
        self._t = _qb_trim(cells)

    # ── construction ────────────────────────────────────────────────────────
    @classmethod
    def _wrap(cls, trimmed: Tuple[QPoly, ...]) -> "QBiPoly":
        b = cls.__new__(cls)
        b._t = trimmed
        return b

    @classmethod
    def zero(cls) -> "QBiPoly":
        """The zero bivariate-q polynomial."""
        return cls._wrap(())

    @classmethod
    def one(cls) -> "QBiPoly":
        """The constant ``1`` (a single ``Y**0`` cell carrying the ``QPoly`` ``1``)."""
        return cls._wrap((QPoly.one(),))

    @classmethod
    def from_x_qpoly(cls, p: QPoly) -> "QBiPoly":
        """A ``QPoly`` in ``X = q**n`` ALONE (no ``Y``) → the constant-in-``Y``
        ``QBiPoly`` (a single ``Y**0`` cell)."""
        return cls._wrap(() if p.is_zero else (p,))

    @classmethod
    def from_y_qpoly(cls, p: QPoly) -> "QBiPoly":
        """A ``QPoly`` whose formal variable is to be read as ``Y = q**k`` (no ``X``)
        → a ``QBiPoly`` (each ``Y``-cell the constant-in-``X`` ``QPoly`` of that
        ``ℚ[q]`` coefficient). The ``QPoly``'s x-window becomes the ``Y``-degree
        window; only a non-Laurent (``x_low ≥ 0``) input is accepted (a term-ratio
        denominator/numerator in ``Y`` is a genuine polynomial in ``Y``)."""
        if p.is_zero:
            return cls._wrap(())
        if p.x_low < 0:
            raise ValueError(
                "QBiPoly.from_y_qpoly: a Laurent-in-Y input (negative Y exponent) "
                "is not a polynomial in Y; the q-term-ratio Y-part is non-Laurent")
        cells: List[QPoly] = [QPoly.zero()] * p.x_low
        for c in p.cells:
            cells.append(QPoly.from_q_poly(c) if not c.is_zero else QPoly.zero())
        return cls._wrap(_qb_trim(cells))

    @classmethod
    def coerce(cls, value) -> "QBiPoly":
        """Coerce a ``q_zeilberger`` term-ratio operand to a ``QBiPoly``. A
        ``QBiPoly`` passes through; a :class:`~srmech.amsc.qpoly.QPoly` is read as a
        polynomial in ``Y = q**k`` (the no-``X`` case — the common acceptance form,
        the q-analog of ``BiPoly.coerce`` reading a ``Poly`` as a polynomial in
        ``k``); a :class:`~srmech.amsc.poly.Poly` in ``q`` is the constant ``ℚ[q]``
        scalar (a single ``Y**0 · X**0`` cell); an ascending-``Y``-degree sequence
        whose entries are themselves ``QPoly``-in-``X`` (or ``QPoly``-coercible cells)
        is wrapped term-by-term."""
        if isinstance(value, QBiPoly):
            return value
        if isinstance(value, QPoly):
            return cls.from_y_qpoly(value)
        if isinstance(value, Poly):
            return cls.from_x_qpoly(QPoly.from_q_poly(value))
        if isinstance(value, tuple):
            value = list(value)
        # a sequence of Y-degree coefficients (each a QPoly-in-X or QPoly-coercible).
        return cls([c if isinstance(c, QPoly) else _as_xcell(c) for c in value])

    # ── accessors ───────────────────────────────────────────────────────────
    @property
    def terms(self) -> Tuple[QPoly, ...]:
        """The trimmed ``Y``-ascending tuple of ``QPoly``-in-``X`` coefficients."""
        return self._t

    @property
    def y_degree(self) -> int:
        """The degree in ``Y = q**k`` (``-1`` for the zero polynomial)."""
        return len(self._t) - 1

    @property
    def is_zero(self) -> bool:
        return len(self._t) == 0

    def coeff(self, d: int) -> QPoly:
        """The ``QPoly``-in-``X`` coefficient of ``Y**d`` (the zero ``QPoly`` past the
        ``Y``-degree)."""
        return self._t[d] if 0 <= d < len(self._t) else QPoly.zero()

    def __eq__(self, other) -> bool:
        if not isinstance(other, QBiPoly):
            try:
                other = QBiPoly.coerce(other)
            except (TypeError, ValueError):
                return NotImplemented
        return self._t == other._t

    def __hash__(self) -> int:
        return hash(self._t)

    def __repr__(self) -> str:
        return f"QBiPoly(y_degree={self.y_degree}, exact bivariate-ℚ[q] in (X,Y))"

    # ── exact arithmetic over ℚ[q] in (X, Y) (Class-K sign via QPoly) ────────
    def __add__(self, other: "QBiPoly") -> "QBiPoly":
        o = QBiPoly.coerce(other)
        m = max(len(self._t), len(o._t))
        out = [self.coeff(d) + o.coeff(d) for d in range(m)]
        return QBiPoly._wrap(_qb_trim(out))

    def __sub__(self, other: "QBiPoly") -> "QBiPoly":
        o = QBiPoly.coerce(other)
        m = max(len(self._t), len(o._t))
        out = [self.coeff(d) - o.coeff(d) for d in range(m)]
        return QBiPoly._wrap(_qb_trim(out))

    def __neg__(self) -> "QBiPoly":
        return QBiPoly._wrap(tuple(-c for c in self._t))

    def __mul__(self, other: "QBiPoly") -> "QBiPoly":
        o = QBiPoly.coerce(other)
        if self.is_zero or o.is_zero:
            return QBiPoly._wrap(())
        out = [QPoly.zero()] * (len(self._t) + len(o._t) - 1)
        for i, ci in enumerate(self._t):
            if ci.is_zero:
                continue
            for j, cj in enumerate(o._t):
                if cj.is_zero:
                    continue
                out[i + j] = out[i + j] + ci * cj            # QPoly-in-X product
        return QBiPoly._wrap(_qb_trim(out))

    def scale_x(self, p: QPoly) -> "QBiPoly":
        """Multiply every ``Y``-coefficient by a ``QPoly``-in-``X`` ``p`` (exact)."""
        if p.is_zero or self.is_zero:
            return QBiPoly._wrap(())
        return QBiPoly._wrap(_qb_trim([c * p for c in self._t]))

    def qshift_x(self, s: int) -> "QBiPoly":
        """``F(q**n, q**k) ↦ F(q**(n+s), q**k)`` — the **n-direction q-shift** ``σ_x:
        X ↦ q**s·X``, applied to every ``QPoly`` cell via :meth:`QPoly.qshift` (the
        q-analog of :meth:`BiPoly.shift_n`). Exact over ``ℚ[q]``."""
        if s == 0 or self.is_zero:
            return self
        return QBiPoly._wrap(_qb_trim([c.qshift(s) for c in self._t]))

    def qshift_y(self, s: int) -> "QBiPoly":
        """``F(q**n, q**k) ↦ F(q**n, q**(k+s))`` — the **k-direction q-shift** ``σ_y:
        Y ↦ q**s·Y`` (the q-analog of :meth:`BiPoly.shift_k`). Under ``Y ↦ q**s·Y``
        the ``Y**d`` cell ``c_d(X)·Y**d`` becomes ``c_d(X)·q**(s·d)·Y**d`` — so the
        ``Y``-degree-``d`` ``QPoly`` cell is multiplied by the ``ℚ[q]`` monomial
        ``q**(s·d)`` (the ``Y``-window UNCHANGED). For ``s·d ≥ 0`` this is a pure
        ``ℚ[q]`` multiply; the q-Zeilberger ansatz feeds only non-negative ``s·d``
        here (``s = 1``, ``d ≥ 0``). Exact over ``ℚ[q]``."""
        if s == 0 or self.is_zero:
            return self
        out: List[QPoly] = []
        for d, c in enumerate(self._t):
            if c.is_zero or s * d == 0:
                out.append(c)
                continue
            sd = s * d
            if sd < 0:
                raise ValueError(
                    "QBiPoly.qshift_y: a negative q-power (s·d < 0) would leave ℚ[q]; "
                    f"the q-Zeilberger ansatz feeds s·d ≥ 0 (s={s}, d={d})")
            out.append(c * Poly.monomial(sd))               # ·q**(s·d), a ℚ[q] mul
        return QBiPoly._wrap(_qb_trim(out))


def _as_xcell(value) -> QPoly:
    """Coerce a ``Y``-cell input to a ``QPoly``-in-``X``: a ``QPoly`` passes through;
    a ``Poly``-in-``q`` is the constant ``X**0`` cell; otherwise the value is handed
    to :meth:`QPoly.from_coeffs` (an ascending-x ``ℚ[q]`` cell sequence)."""
    if isinstance(value, QPoly):
        return value
    if isinstance(value, Poly):
        return QPoly.from_q_poly(value)
    return QPoly.from_coeffs(value)


# ── the C bridge wire form (mirror BiPoly._bi_pairs, one ring up) ─────────────
def _qb_pairs(b: "QBiPoly") -> "Tuple[List[int], List[List[List[Tuple[int, int]]]]]":
    """A ``QBiPoly`` → the ``(y_xlow[], [[[(num, den), …]_q]_x]_Y)`` bridge form the
    C peer consumes: a per-``Y``-cell ``x_low`` list plus a ``Y``-ascending list, each
    entry the ``QPoly`` x-row of ascending-``q`` ``(num, den)`` runs (the SAME per-cell
    row form :func:`srmech.amsc.qpoly._qp_pairs` emits). The zero cell rides as
    ``x_low = 0`` with an empty x-row."""
    y_xlow: List[int] = []
    rows: List[List[List[Tuple[int, int]]]] = []
    for cell in b.terms:
        lo, cell_rows = _qp_pairs_of(cell)
        y_xlow.append(lo)
        rows.append(cell_rows)
    return y_xlow, rows


def _qp_pairs_of(p: QPoly) -> "Tuple[int, List[List[Tuple[int, int]]]]":
    from .qpoly import _qp_pairs
    return _qp_pairs(p)
