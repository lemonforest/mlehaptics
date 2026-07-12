"""srmech.amsc.q_gosper — the q-analog of Gosper's indefinite hypergeometric
summation (the FIRST public op of the q-hypergeometric F929 reduction row, the
q-analog of the §76 ``gosper``).

Where :func:`srmech.amsc.gosper.gosper` decides whether an ordinary hypergeometric
term ``t(k)`` has a hypergeometric antidifference ``T(k)`` (``T(k+1) − T(k) =
t(k)``, ``T(k+1)/T(k)`` rational in ``k``), the **q-Gosper** algorithm
(T.H. Koornwinder, "On Zeilberger's algorithm and its q-analogue," J. Comput.
Appl. Math. 48 (1993) 91–111 — the same paper :class:`~srmech.amsc.qpoly.QPoly`
cites; textbook anchor Gasper & Rahman, *Basic Hypergeometric Series*) decides the
same for a **q-hypergeometric** term, whose term ratio is a rational function of
``x = qᵏ``:

    t(k+1)/t(k) = r(x),   x = qᵏ,   σ : x ↦ q·x   (the q-shift).

A q-hypergeometric term is fully described by that rational term ratio
``r(x) = num(x)/den(x)`` — two Laurent polynomials in ``x`` over ``ℚ[q]``, i.e.
two :class:`~srmech.amsc.qpoly.QPoly`. This op takes that ratio and decides whether
``t(k)`` has a q-hypergeometric antidifference ``T(k)`` (``T(k+1) − T(k) = t(k)``,
``R(x) = T(k)/t(k)`` rational in ``x``):

  1. reduce ``r = num/den`` to lowest terms over ``ℚ(q)[x]`` (strip the common
     factor in ``x``, the q-coefficients carried as exact rational functions in
     ``q``);
  2. put ``r`` in **q-Gosper–Petkovšek normal form** ``r(x) = (a(x)/b(x)) ·
     (c(qx)/c(x))`` with ``gcd(a(x), b(qʲx)) = 1`` for every integer ``j ≥ 0`` —
     peeling ``g(x) = gcd(a(x), b(qʲx))`` at each ``j`` in the **q-dispersion**
     set (the q-analog of the ordinary dispersion: ``a ← a/g(x)``, ``b ←
     b/g(q⁻ʲx)``, ``c ← c · Π_{i=1}^{j} g(q⁻ⁱx)``);
  3. solve the **q-Gosper equation** ``a(x)·y(qx) − b(q⁻¹x)·y(x) = c(x)`` for a
     Laurent polynomial ``y(x)`` of bounded x-degree, via undetermined coefficients
     — a small EXACT-``ℚ`` linear system (the q-coefficients cleared to ``ℚ``)
     solved with the exact Gauss-Jordan :class:`~srmech.amsc.qmat.QMat`;
  4. if ``y`` exists, return the **rational certificate** ``R(x) = (b(q⁻¹x)·y(x)) /
     c(x)`` (the q-antidifference is ``T(k) = R(qᵏ)·t(k)``, so ``Σ t`` telescopes:
     ``Σ_{k=a}^{b} t(k) = T(b+1) − T(a)``); else ``None`` (no q-hypergeometric
     closed form — the honest un-summable residue, like ``gosper`` on the harmonic
     term).

The certificate identity it satisfies is the q-analog of the ordinary Gosper
identity ``R(k+1)·r(k) − R(k) = 1``: here ``R(qx)·r(x) − R(x) = 1`` (so ``T(k) =
R(qᵏ)·t(k)`` is the antidifference). The op verifies nothing internally — the
caller checks ``Δ_q(R·t) = t`` exactly (over ``ℚ`` via :meth:`QPoly.eval`); the
returned ``R`` is the certificate of record.

The whole pipeline stays EXACT — every q-coefficient is an exact rational function
of ``q`` (a reduced ``(num, den)`` pair of :class:`~srmech.amsc.poly.Poly` over ℚ,
bigint, no magnitude ceiling), every solve is exact Gauss-Jordan over ``ℚ``. There
is NO float anywhere; sign is the **Class-K** pin-slot via the ``Q`` / ``Poly``
sign-branch (never an ALU ``abs()``); no ``math`` module, no numpy. This is the
**q-Gosper** rung of the q-hypergeometric F929 row (the row continues with the
q-Zeilberger recurrence-finder rc56, which parametrizes THIS engine with unknown
``a_j(n)``); the internals are factored to be reused there.

C peer: ``srmech_q_gosper`` (``c/src/srmech_q_gosper.c``) orchestrates the SAME
existing C kernels — the ``srmech_qpoly_*`` q-shift algebra (+ a q-gcd / q-dispersion
over ``ℚ(q)[x]``) + ``srmech_qmat_rref`` (the exact-ℚ linear solve) — into one
caller-arena, JPL-clean symbol. ``q_gosper`` routes through it when ``HAS_NATIVE``
(:func:`srmech.amsc._native.has_native_q_gosper`) and the C reports a positive
(certificate-found) result; a ``has=0`` C result is NOT trusted as a definitive "no
certificate" (the C path may decline an input past its bound), so it falls through
to the COMPLETE pure-Python body here — the full-coverage decider AND the
byte-identical parity oracle.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .poly import Poly
from .q import Q
from .qpoly import QPoly

__all__ = ["q_gosper"]

_Q_ZERO = Q(0, 1)
_Q_ONE = Q(1, 1)
_POLY_ZERO = Poly.zero()
_POLY_ONE = Poly.one()

# The largest x-degree of the unknown q-Gosper-equation Laurent solution y(x) the
# undetermined-coefficient sweep reaches before declaring "no certificate". The
# certificate of a proper q-hypergeometric term has a y-degree comparable to the
# input term-ratio structure; this bound is the safe ceiling.
_MAX_Y_DEGREE = 16


# ── the exact ℚ(q) rational-function-in-q coefficient layer (Class-N over J) ────
#
# A q-Gosper coefficient is an exact rational function of ``q`` — a reduced
# ``(num, den)`` pair of :class:`~srmech.amsc.poly.Poly` over ℚ. The carrier QPoly
# rides ``ℚ[q]`` (no denominators) because its own algebra never needs them; but
# the q-Gosper x-polynomial GCD / long division need a FIELD for the x-coefficient
# ring, and that field is ``ℚ(q)``. So this op carries each x-coefficient as a
# ``_Cq`` (a reduced rational function in ``q``), exactly as the ordinary gosper
# carries each k-coefficient as a ``Q``. Everything is exact bigint; the field
# layer is local to the op (the carrier stays ``ℚ[q]``).


class _Cq:
    """An exact rational function of ``q``: a reduced ``(num, den)`` pair of
    :class:`~srmech.amsc.poly.Poly` over ℚ (``den`` monic, ``gcd(num, den) = 1``).
    The x-coefficient ring of the q-Gosper algebra — a field over ``ℚ(q)``."""

    __slots__ = ("num", "den")

    def __init__(self, num: Poly, den: Poly = _POLY_ONE) -> None:
        if den.is_zero:
            raise ZeroDivisionError("_Cq denominator must be nonzero")
        if num.is_zero:
            self.num = _POLY_ZERO
            self.den = _POLY_ONE
            return
        g = num.gcd(den)
        if not g.is_zero and g.degree >= 1:
            num = num.divmod(g)[0]
            den = den.divmod(g)[0]
        # normalize: den monic (leading coeff 1), the sign carried by num (Class-K).
        lead = den.leading
        if lead != _Q_ONE:
            inv = _Q_ONE / lead
            num = num * inv
            den = den * inv
        self.num = num
        self.den = den

    @classmethod
    def zero(cls) -> "_Cq":
        return cls(_POLY_ZERO, _POLY_ONE)

    @classmethod
    def one(cls) -> "_Cq":
        return cls(_POLY_ONE, _POLY_ONE)

    @classmethod
    def from_poly(cls, p: Poly) -> "_Cq":
        """A ``ℚ[q]`` element (a ``Poly`` in ``q``) → a ``_Cq`` over the unit
        denominator."""
        return cls(p, _POLY_ONE)

    @classmethod
    def q_power(cls, e: int) -> "_Cq":
        """``q**e`` as a ``_Cq`` (``e`` any int; a negative ``e`` rides the
        denominator)."""
        if e >= 0:
            return cls(Poly.monomial(e), _POLY_ONE)
        return cls(_POLY_ONE, Poly.monomial(-e))

    @property
    def is_zero(self) -> bool:
        return self.num.is_zero

    def __add__(self, o: "_Cq") -> "_Cq":
        return _Cq(self.num * o.den + o.num * self.den, self.den * o.den)

    def __sub__(self, o: "_Cq") -> "_Cq":
        return _Cq(self.num * o.den - o.num * self.den, self.den * o.den)

    def __mul__(self, o: "_Cq") -> "_Cq":
        return _Cq(self.num * o.num, self.den * o.den)

    def __truediv__(self, o: "_Cq") -> "_Cq":
        if o.is_zero:
            raise ZeroDivisionError("_Cq divide by zero")
        return _Cq(self.num * o.den, self.den * o.num)

    def __neg__(self) -> "_Cq":
        return _Cq(-self.num, self.den)

    def __eq__(self, o) -> bool:
        if isinstance(o, _Cq):
            return self.num == o.num and self.den == o.den
        return NotImplemented


# ── a Laurent polynomial in x over ℚ(q): the q-Gosper working object ───────────
#
# Represented as a dict ``{x_exp: _Cq}`` (sparse; the GP-form's q⁻ʲ shifts produce
# both high and low x-powers). The x-coefficient ring is the field ``_Cq``, so
# polynomial GCD / long division are well-defined. Mirrors the ordinary-gosper
# ``Poly`` x-algebra, one ring up (ℚ → ℚ(q)) and Laurent (x⁻¹ allowed).


def _xp_trim(d: Dict[int, _Cq]) -> Dict[int, _Cq]:
    return {e: c for e, c in d.items() if not c.is_zero}


def _xp_from_qpoly(p: QPoly) -> Dict[int, _Cq]:
    """A carrier :class:`~srmech.amsc.qpoly.QPoly` (Laurent in ``x`` over ``ℚ[q]``)
    → the working ``{x_exp: _Cq}`` form (the q-coefficients lifted to ``ℚ(q)`` over
    the unit denominator)."""
    out: Dict[int, _Cq] = {}
    for i, cell in enumerate(p.cells):
        if not cell.is_zero:
            out[p.x_low + i] = _Cq.from_poly(cell)
    return out


def _xp_qden(d: Dict[int, _Cq]) -> Poly:
    """The shared ``q``-denominator (the monic LCM of every x-cell's ``_Cq``
    denominator) needed to clear ``d`` into ``ℚ[q]`` coefficients."""
    den = _POLY_ONE
    for c in _xp_trim(d).values():
        den = _lcm_poly(den, c.den)
    return den


def _xp_to_qpoly(d: Dict[int, _Cq], clear_den: Poly = _POLY_ONE) -> QPoly:
    """The working ``{x_exp: _Cq}`` form → a carrier :class:`~srmech.amsc.qpoly.QPoly`
    after multiplying through by ``clear_den`` (a ``ℚ[q]`` polynomial chosen so every
    resulting q-coefficient lands in ``ℚ[q]`` — the carrier's ground ring).

    The certificate ``R = num/den`` is a ratio of two ``ℚ(q)[x]`` polynomials; to
    carry both as ``QPoly`` (whose coefficients are ``ℚ[q]``, NOT ``ℚ(q)``) the
    caller passes the SAME ``clear_den`` (the LCM of every q-denominator across BOTH
    num and den) for each — multiplying num and den by the same ``ℚ[q]`` factor
    leaves the rational ``R`` unchanged. Each x-cell ``c`` contributes ``c.num ·
    (clear_den / c.den)`` (exact, since ``clear_den`` is a multiple of ``c.den``)."""
    d = _xp_trim(d)
    if not d:
        return QPoly.zero()
    terms: Dict[Tuple[int, int], Q] = {}
    for e, c in d.items():
        scale = clear_den.divmod(c.den)[0]      # clear_den / c.den, exact
        num = c.num * scale                     # c.num · (clear_den / c.den) ∈ ℚ[q]
        for dq, coeff in enumerate(num.coeffs):
            if coeff != 0:
                terms[(e, dq)] = terms.get((e, dq), _Q_ZERO) + coeff
    if not terms:
        return QPoly.zero()
    return QPoly.from_dict(terms)


def _lcm_poly(a: Poly, b: Poly) -> Poly:
    """The monic LCM of two ``ℚ[q]`` polynomials (``a·b / gcd(a,b)``), monic."""
    if a.is_zero or b.is_zero:
        return _POLY_ZERO
    g = a.gcd(b)
    lcm = (a * b).divmod(g)[0]
    return lcm.monic()


def _xp_normalize(d: Dict[int, _Cq]) -> Tuple[int, Dict[int, _Cq]]:
    """Factor the lowest x-power out (a unit ``x**low``): return ``(low, shifted)``
    with the result's minimal x-exponent 0 (a genuine non-Laurent polynomial whose
    GCD / dispersion is well-defined)."""
    d = _xp_trim(d)
    if not d:
        return 0, {}
    low = min(d)
    return low, {e - low: c for e, c in d.items()}


def _xp_qshift(d: Dict[int, _Cq], s: int) -> Dict[int, _Cq]:
    """The q-shift ``σ**s : x ↦ q**s·x`` — coefficient of ``x**e`` is multiplied by
    ``q**(s·e)`` (the ``_Cq`` carries the negative powers exactly). x-window
    unchanged."""
    out: Dict[int, _Cq] = {}
    for e, c in d.items():
        out[e] = c * _Cq.q_power(s * e)
    return _xp_trim(out)


def _xp_mul(a: Dict[int, _Cq], b: Dict[int, _Cq]) -> Dict[int, _Cq]:
    out: Dict[int, _Cq] = {}
    for e1, c1 in a.items():
        for e2, c2 in b.items():
            key = e1 + e2
            out[key] = out.get(key, _Cq.zero()) + c1 * c2
    return _xp_trim(out)


def _xp_sub(a: Dict[int, _Cq], b: Dict[int, _Cq]) -> Dict[int, _Cq]:
    out = dict(a)
    for e, c in b.items():
        out[e] = out.get(e, _Cq.zero()) - c
    return _xp_trim(out)


# ── non-Laurent x-polynomial-list (ascending _Cq) gcd / divmod over ℚ(q) ───────


def _xl_from_dict(d: Dict[int, _Cq]) -> List[_Cq]:
    """A non-Laurent (min x-exp 0) ``{x_exp: _Cq}`` → an ascending list of ``_Cq``."""
    if not d:
        return [_Cq.zero()]
    hi = max(d)
    return [d.get(i, _Cq.zero()) for i in range(hi + 1)]


def _xl_to_dict(lst: List[_Cq]) -> Dict[int, _Cq]:
    return _xp_trim({i: c for i, c in enumerate(lst)})


def _xl_deg(a: List[_Cq]) -> int:
    d = len(a) - 1
    while d > 0 and a[d].is_zero:
        d -= 1
    return d


def _xl_divmod(a: List[_Cq], b: List[_Cq]) -> Tuple[List[_Cq], List[_Cq]]:
    """Exact long division of two ascending-``_Cq`` x-polynomials over the field
    ``ℚ(q)``: ``(quotient, remainder)``."""
    a = list(a)
    b = list(b)
    while len(b) > 1 and b[-1].is_zero:
        b = b[:-1]
    q = [_Cq.zero()] * max(len(a) - len(b) + 1, 0)
    while len(a) >= len(b) and any(not x.is_zero for x in a):
        sh = len(a) - len(b)
        fac = a[-1] / b[-1]
        q[sh] = fac
        for j in range(len(b)):
            a[sh + j] = a[sh + j] - fac * b[j]
        while len(a) > 1 and a[-1].is_zero:
            a.pop()
        if all(x.is_zero for x in a):
            a = [_Cq.zero()]
            break
    while len(a) > 1 and a[-1].is_zero:
        a.pop()
    while len(q) > 1 and q[-1].is_zero:
        q.pop()
    return q, a


def _xl_gcd(a: List[_Cq], b: List[_Cq]) -> List[_Cq]:
    """The Euclidean GCD of two ascending-``_Cq`` x-polynomials over ``ℚ(q)``,
    monic-normalized (leading ``_Cq`` = 1)."""
    a = list(a)
    b = list(b)
    while any(not x.is_zero for x in b):
        a, b = b, _xl_divmod(a, b)[1]
    lead = a[-1]
    if lead.is_zero:
        return [_Cq.zero()]
    return [x / lead for x in a]


# ── q-dispersion: the non-negative integer shifts where gcd(a(x), b(qʲx)) ≠ 1 ──


def _q_dispersion(a: List[_Cq], b: List[_Cq]) -> List[int]:
    """The q-dispersion set ``{ j ≥ 0 integer : deg_x gcd(a(x), b(qʲ·x)) ≥ 1 }`` —
    the q-analog of the ordinary dispersion (Petkovšek convention: the SECOND
    argument is q-shifted by ``+j``). A common x-root forces ``qʲ = (root of b)/(root
    of a)``, so the integer ``j`` is bounded by the degrees; we scan ``j`` up to the
    structural bound ``deg a + deg b`` (a sufficient bound — beyond it the two
    polynomials' roots cannot align under an integer q-step), each tested with the
    exact ``ℚ(q)[x]`` gcd. Ascending."""
    da, db = _xl_deg(a), _xl_deg(b)
    if da < 1 or db < 1:
        return []
    out: List[int] = []
    bound = da * db + da + db + 2
    bdict = _xl_to_dict(b)
    for j in range(0, bound + 1):
        _, bshift = _xp_normalize(_xp_qshift(bdict, j))      # b(qʲx), re-based to x⁰
        g = _xl_gcd(a, _xl_from_dict(bshift))
        if _xl_deg(g) >= 1:
            out.append(j)
    return out


# ── the q-Gosper–Petkovšek normal form ────────────────────────────────────────


def _q_gp_form(num: Dict[int, _Cq], den: Dict[int, _Cq]
               ) -> Tuple[List[_Cq], List[_Cq], List[_Cq]]:
    """The q-Gosper–Petkovšek normal form of ``r = num/den``: returns ``(a, b, c)``
    (ascending-``_Cq`` non-Laurent x-poly lists) with ``r(x) = (a(x)/b(x)) ·
    (c(qx)/c(x))`` and ``gcd(a(x), b(qʲx)) = 1`` for every integer ``j ≥ 0``. Peels
    ``g(x) = gcd(a(x), b(qʲx))`` at the smallest non-negative q-dispersion shift
    ``j``: ``a ← a/g(x)``, ``b ← b/g(q⁻ʲx)``, ``c ← c · Π_{i=1}^{j} g(q⁻ⁱx)``."""
    a = _xl_from_dict(_xp_normalize(num)[1])
    b = _xl_from_dict(_xp_normalize(den)[1])
    c = [_Cq.one()]
    guard = 0
    while guard <= _MAX_Y_DEGREE * 2 + 8:
        disp = [j for j in _q_dispersion(a, b) if j >= 0]
        if not disp:
            break
        j = disp[0]
        bdict = _xl_to_dict(b)
        _, bshift = _xp_normalize(_xp_qshift(bdict, j))      # b(qʲx)
        g = _xl_gcd(a, _xl_from_dict(bshift))
        if _xl_deg(g) < 1:
            break
        gdict = _xl_to_dict(g)
        a = _xl_divmod(a, g)[0]                              # a ← a / g(x)
        _, g_mj = _xp_normalize(_xp_qshift(gdict, -j))       # g(q⁻ʲx)
        b = _xl_divmod(b, _xl_from_dict(g_mj))[0]            # b ← b / g(q⁻ʲx)
        for i in range(1, j + 1):
            _, g_mi = _xp_normalize(_xp_qshift(gdict, -i))   # g(q⁻ⁱx)
            c = _xl_from_dict(_xp_mul(_xl_to_dict(c), g_mi)) # c ← c · g(q⁻ⁱx)
        guard += 1
    return a, b, c


# ── the q-Gosper equation solve (undetermined coefficients over ℚ) ─────────────


def _solve_q_gosper(a: List[_Cq], b: List[_Cq], c: List[_Cq]
                    ) -> Optional[Dict[int, _Cq]]:
    """Solve the q-Gosper equation ``a(x)·y(qx) − b(q⁻¹x)·y(x) = c(x)`` for a
    polynomial ``y(x)`` (non-Laurent, x-degree ``0..D`` swept up to
    :data:`_MAX_Y_DEGREE`) via undetermined coefficients. Column ``j`` is the
    x-polynomial contribution of the unknown ``y_j``: ``P_j(x) = a(x)·q**j·x**j −
    b(q⁻¹x)·x**j`` (since ``y(qx)`` sends ``x**j ↦ q**j·x**j``). The linear system
    ``Σ_j y_j·P_j(x) = c(x)`` over the unknowns ``y_0..y_D ∈ ℚ(q)`` is matched
    x-power by x-power and solved EXACTLY over the field ``ℚ(q)`` (the q-analog of
    ordinary Gosper's exact-``ℚ`` solve — the x-coefficient field is ``ℚ(q)`` here,
    not ``ℚ``, so an unknown ``y_j`` is itself a rational function in ``q``, e.g.
    ``1/(q−1)`` for ``Σ qᵏ``). Returns ``y`` as ``{x_exp: _Cq}`` (the free slots set
    to 0 — any choice is a valid antidifference) or ``None`` when no polynomial ``y``
    of degree ≤ :data:`_MAX_Y_DEGREE` solves it."""
    bdict = _xl_to_dict(b)
    _, b_over_q = _xp_normalize(_xp_qshift(bdict, -1))       # b(q⁻¹x), re-based
    bq = _xl_from_dict(b_over_q)
    c_deg = _xl_deg(c)
    for deg in range(0, _MAX_Y_DEGREE + 1):
        cols: List[Dict[int, _Cq]] = []
        max_deg = c_deg
        for j in range(deg + 1):
            qj = _Cq.q_power(j)
            t1 = _xp_mul(_xl_to_dict(a), {j: qj})            # a(x)·q**j·x**j
            t2 = _xp_mul(_xl_to_dict(bq), {j: _Cq.one()})    # b(q⁻¹x)·x**j
            p_j = _xp_sub(t1, t2)
            cols.append(p_j)
            if p_j:
                d = max(p_j)
                if d > max_deg:
                    max_deg = d
        sol = _solve_exact_cq(cols, _xl_to_dict(c), deg + 1, max_deg)
        if sol is not None and any(not v.is_zero for v in sol.values()):
            return sol
    return None


def _solve_exact_cq(cols: List[Dict[int, _Cq]], rhs: Dict[int, _Cq],
                    n_cols: int, max_deg: int) -> Optional[Dict[int, _Cq]]:
    """Solve the exact-``ℚ(q)`` linear system ``Σ_j y_j·cols[j] = rhs`` (``j =
    0..n_cols−1``) by matching x-power by x-power (rows ``0..max_deg``) and running an
    exact Gauss-Jordan RREF over the field ``ℚ(q)``.

    The augmented matrix entries are :class:`_Cq` (exact rational functions in ``q``);
    the elimination is the SAME Gauss-Jordan the exact-``ℚ`` :class:`~srmech.amsc.qmat.QMat`
    runs — pivoting on a nonzero entry, scaling the pivot row by the pivot's inverse,
    clearing the column — one ring UP (``ℚ`` → ``ℚ(q)``). Each pivot / scale / clear is
    an exact ``_Cq`` op (built on the ``Poly``-over-``Q`` arithmetic + its C peer), so
    the whole solve stays exact bigint with no float and no ``abs()``. A free column →
    ``0`` (any choice is a valid antidifference); a pivot in the RHS column → the system
    is inconsistent → ``None``. Returns ``y`` as ``{x_exp: _Cq}``."""
    # build {x_power: row of _Cq over the n_cols unknowns + RHS} (one equation per
    # x-power; the x-coefficient ring is the FIELD ℚ(q), so each y_j is a _Cq).
    rows: Dict[int, List[_Cq]] = {}

    def _row(xe: int) -> List[_Cq]:
        row = rows.get(xe)
        if row is None:
            row = [_Cq.zero()] * (n_cols + 1)
            rows[xe] = row
        return row

    for j in range(n_cols):
        for xe, cq in cols[j].items():
            r = _row(xe)
            r[j] = r[j] + cq
    for xe, cq in rhs.items():                               # the RHS column = c(x)
        r = _row(xe)
        r[n_cols] = r[n_cols] + cq

    if not rows:
        # 0 = 0: the all-zero system. y ≡ 0 is the only solution → not a certificate.
        return None
    aug = [rows[xe] for xe in sorted(rows)]
    solved = _rref_cq(aug, n_cols)
    if solved is None:
        return None                                          # inconsistent
    return {i: v for i, v in enumerate(solved) if not v.is_zero}


def _rref_cq(aug: List[List[_Cq]], n_cols: int) -> Optional[List[_Cq]]:
    """Exact Gauss-Jordan RREF of the augmented ``ℚ(q)`` system ``aug`` (``n_cols``
    unknowns + a trailing RHS column) → the solution vector (``n_cols`` ``_Cq``, free
    slots ``0``), or ``None`` when inconsistent (a pivot in the RHS column). The exact
    field analog of :meth:`~srmech.amsc.qmat.QMat.rref` (the leaf ``ℚ`` arithmetic
    lives inside each ``_Cq``)."""
    m = [list(r) for r in aug]
    n_rows = len(m)
    total = n_cols + 1
    pivot_col_of: List[int] = []
    pr = 0
    for col in range(total):
        prow = None
        for r in range(pr, n_rows):
            if not m[r][col].is_zero:
                prow = r
                break
        if prow is None:
            continue
        m[pr], m[prow] = m[prow], m[pr]
        inv = _Cq.one() / m[pr][col]
        m[pr] = [inv * v for v in m[pr]]
        for r in range(n_rows):
            if r != pr and not m[r][col].is_zero:
                f = m[r][col]
                m[r] = [m[r][i] - f * m[pr][i] for i in range(total)]
        pivot_col_of.append(col)
        pr += 1
        if pr >= n_rows:
            break
    y = [_Cq.zero()] * n_cols
    for ri, col in enumerate(pivot_col_of):
        if col == n_cols:
            return None                                      # 0 = nonzero ⇒ inconsistent
        y[col] = m[ri][n_cols]
    return y


# ── the public op ──────────────────────────────────────────────────────────────


def _native():
    """The native ``_native`` module IF the rc55 ``srmech_q_gosper`` peer is present
    and bound, else ``None`` — so ``q_gosper`` dispatches to C when available and
    falls cleanly to the pure-Python body (the complete alternative + the parity
    oracle) otherwise. Imported lazily to avoid a bootstrap cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    probe = getattr(nat, "has_native_q_gosper", None)
    return nat if (probe is not None and probe()) else None


def _coerce_qpoly(value) -> QPoly:
    """Coerce a term-ratio operand to a :class:`~srmech.amsc.qpoly.QPoly`. A
    ``QPoly`` passes through; a lower carrier (a ``Poly`` in ``q`` → an ``x**0``
    cell) or the nested-list form (``QPoly.from_coeffs`` — an ascending-x list of
    ``ℚ[q]`` cells) is lifted. A tuple is read as a list."""
    if isinstance(value, QPoly):
        return value
    if isinstance(value, Poly):
        return QPoly.from_q_poly(value)
    if isinstance(value, tuple):
        value = list(value)
    try:
        return QPoly.from_coeffs(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(
            "q_gosper: each term-ratio operand must be a QPoly (or a Poly / "
            f"ascending-x ℚ[q] coefficient list); got {value!r}") from exc


def q_gosper(rn_num, rn_den) -> Optional[Dict[str, QPoly]]:
    """The q-analog of Gosper's indefinite hypergeometric summation over
    ``ℚ(q)[x]`` (``x = qᵏ``).

    ``rn_num`` and ``rn_den`` are the numerator / denominator of the
    q-hypergeometric **term ratio** ``t(k+1)/t(k) = r(qᵏ) = rn_num(x)/rn_den(x)`` —
    each a :class:`~srmech.amsc.qpoly.QPoly` (a Laurent polynomial in ``x = qᵏ`` over
    ``ℚ[q]``), or any value :func:`_coerce_qpoly` lifts (a ``Poly`` in ``q``, the
    nested-list ``QPoly`` form). The op decides whether ``t(k)`` has a
    q-hypergeometric antidifference ``T(k)`` (``T(k+1) − T(k) = t(k)``):

    - if it does, returns the **rational certificate** ``{"num": QPoly, "den":
      QPoly}`` — the reduced ``R(x)`` such that ``T(k) = R(qᵏ)·t(k)`` is the
      antidifference (so ``Σ_{k=a}^{b} t(k) = T(b+1) − T(a)``, with ``R(qx)·r(x) −
      R(x) = 1``);
    - if no q-hypergeometric closed form exists, returns ``None`` (the honest
      un-summable residue, like ``gosper`` on the harmonic term).

    Exact over ``ℚ(q)`` (bigint, no magnitude ceiling); no float, no ``abs()`` (the
    sign is the Class-K pin-slot), no ``math`` / numpy. See the module docstring for
    the full q-Gosper / q-Petkovšek pipeline. ``rn_den`` must not be the zero
    polynomial (a term ratio has a nonzero denominator) — ``ValueError`` otherwise.
    """
    num_p = _coerce_qpoly(rn_num)
    den_p = _coerce_qpoly(rn_den)
    if den_p.is_zero:
        raise ValueError(
            "q_gosper: the term-ratio denominator must be a NONZERO QPoly "
            "(t(k+1)/t(k) = num(x)/den(x) has a nonzero den)")
    if num_p.is_zero:
        # r ≡ 0 ⇒ the term vanishes after the first step; no NONZERO q-hypergeometric
        # closed form to certify. Mirrors gosper's num ≡ 0 leaf.
        return None

    nat = _native()
    if nat is not None:
        try:
            got = nat.q_gosper_c(_qg_pairs(num_p), _qg_pairs(den_p))
            # The C peer ACCELERATES the positive (certificate-found) case only: a
            # has=1 result is byte-identical to the pure path. A has=0 is NOT trusted
            # as a definitive "no certificate" — it falls through to the complete
            # pure-Python path (the parity oracle AND the full-coverage decider).
            if got is not None:
                has, r_num_form, r_den_form = got
                if has:
                    return _canonicalize_cert(_qg_from_pairs(r_num_form),
                                              _qg_from_pairs(r_den_form))
        except (RuntimeError, OverflowError, ValueError):
            pass                                  # fall to the pure path

    return _q_gosper_pure(num_p, den_p)


# ── pure-Python q-Gosper (the COMPLETE alternative + the parity oracle) ────────


def _q_gosper_pure(num_p: QPoly, den_p: QPoly) -> Optional[Dict[str, QPoly]]:
    """The exact-ℚ(q) pure-Python q-Gosper pipeline (the complete, ceiling-free
    alternative to the C peer). See the module docstring."""
    num = _xp_from_qpoly(num_p)
    den = _xp_from_qpoly(den_p)
    a, b, c = _q_gp_form(num, den)
    y = _solve_q_gosper(a, b, c)
    if y is None or all(v.is_zero for v in y.values()):
        return None                               # no q-hypergeometric antidifference
    # R(x) = b(q⁻¹x)·y(x) / c(x), reduced to lowest terms over ℚ(q)[x].
    bdict = _xl_to_dict(b)
    _, b_over_q = _xp_normalize(_xp_qshift(bdict, -1))
    r_num = _xp_mul(b_over_q, y)
    r_den = _xl_to_dict(c)
    r_num, r_den = _reduce_ratio(r_num, r_den)
    # Clear BOTH num and den by the SAME shared q-denominator (the LCM of every
    # q-denominator across both) so each lands in ℚ[q] AND the rational R is
    # unchanged (multiplying num and den by the same ℚ[q] factor is a unit on R).
    clear_den = _lcm_poly(_xp_qden(r_num), _xp_qden(r_den))
    if clear_den.is_zero:
        clear_den = _POLY_ONE
    num_qp = _xp_to_qpoly(r_num, clear_den)
    den_qp = _xp_to_qpoly(r_den, clear_den)
    return _canonicalize_cert(num_qp, den_qp)


def _canonicalize_cert(num_qp: QPoly, den_qp: QPoly) -> Dict[str, QPoly]:
    """Put the certificate ratio ``R = num/den`` (two ``QPoly`` over ``ℚ[q]``) in a
    SINGLE canonical form so the native and pure paths are byte-identical: scale both
    by the common integer that clears every ``Q`` coefficient denominator (across BOTH
    num and den) to an integer, strip the shared integer content (the gcd of all
    integer coefficients), and pin the sign so the LOWEST nonzero ``den`` coefficient
    is positive (the Class-K sign pin — never an ALU ``abs()``). Multiplying num and
    den by the same rational is a unit on ``R``, so the rational is unchanged."""
    from . import cyclic
    pairs: List[Tuple[int, int]] = []
    for qp in (num_qp, den_qp):
        for cell in qp.cells:
            for coeff in cell.coeffs:
                pairs.append((coeff.numerator, coeff.denominator))
    if not pairs:
        return {"num": num_qp, "den": den_qp}
    # the common integer multiplier = LCM of all coefficient denominators.
    den_lcm = 1
    for _n, d in pairs:
        g = cyclic.gcd(den_lcm, d)
        den_lcm = den_lcm // g * d
    # the shared integer content = gcd of all (coeff · den_lcm) integer numerators.
    content = 0
    int_pairs: List[int] = []
    for n, d in pairs:
        iv = n * (den_lcm // d)
        int_pairs.append(iv)
        content = cyclic.gcd(content, iv if iv >= 0 else -iv)
    if content == 0:
        content = 1
    scale = Q(den_lcm, content)                       # multiply both num + den by this
    # the sign pin: the LOWEST-degree nonzero den coefficient must be positive.
    sign = 1
    for cell in den_qp.cells:
        found = False
        for coeff in cell.coeffs:
            if coeff != 0:
                if coeff.numerator < 0:
                    sign = -1
                found = True
                break
        if found:
            break
    factor = scale * Q(sign, 1)
    return {"num": _qp_scale(num_qp, factor), "den": _qp_scale(den_qp, factor)}


def _qp_scale(qp: QPoly, factor: Q) -> QPoly:
    """Multiply every ``ℚ[q]`` coefficient of ``qp`` by the exact ``factor`` (a
    ``Q``), preserving the x-window. The Class-K sign rides inside ``factor``."""
    if qp.is_zero or factor == 0:
        return QPoly.zero()
    cells = [cell * factor for cell in qp.cells]       # Poly · Q scalar multiply
    return QPoly.from_coeffs(cells, qp.x_low)


def _reduce_ratio(num: Dict[int, _Cq], den: Dict[int, _Cq]
                  ) -> Tuple[Dict[int, _Cq], Dict[int, _Cq]]:
    """Strip the common x-polynomial factor of ``num/den`` over ``ℚ(q)[x]`` (and the
    shared ``x**low`` unit), so the returned certificate ratio is in lowest terms."""
    lo_n, nn = _xp_normalize(num)
    lo_d, dd = _xp_normalize(den)
    nl = _xl_from_dict(nn)
    dl = _xl_from_dict(dd)
    g = _xl_gcd(nl, dl)
    if _xl_deg(g) >= 1:
        nl = _xl_divmod(nl, g)[0]
        dl = _xl_divmod(dl, g)[0]
    # re-apply the relative x-shift (lo_n − lo_d) onto the numerator (a unit power).
    shift = lo_n - lo_d
    num_d = _xl_to_dict(nl)
    den_d = _xl_to_dict(dl)
    if shift > 0:
        num_d = {e + shift: c for e, c in num_d.items()}
    elif shift < 0:
        den_d = {e - shift: c for e, c in den_d.items()}
    return _xp_trim(num_d), _xp_trim(den_d)


# ── the wire form for the C bridge (mirror qpoly._qp_pairs) ────────────────────


def _qg_pairs(p: QPoly) -> "Tuple[int, List[List[Tuple[int, int]]]]":
    """A :class:`~srmech.amsc.qpoly.QPoly` → the ``(x_low, [[(num, den), …]_q]_x)``
    bridge form the C peer consumes — the SAME form
    :func:`srmech.amsc.qpoly._qp_pairs` emits."""
    from .qpoly import _qp_pairs
    return _qp_pairs(p)


def _qg_from_pairs(form) -> QPoly:
    """Rebuild a :class:`~srmech.amsc.qpoly.QPoly` from the ``(x_low, [[(num, den),
    …]_q]_x)`` bridge form (from the C peer; each leaf already reduced) — the SAME
    form :func:`srmech.amsc.qpoly._qp_from_pairs` consumes."""
    from .qpoly import _qp_from_pairs
    return _qp_from_pairs(form)
