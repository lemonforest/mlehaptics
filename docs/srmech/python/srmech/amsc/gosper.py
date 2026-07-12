"""srmech.amsc.gosper — Gosper's indefinite hypergeometric summation (the FIRST
public op of the §76 "telescope" Σ-row closed-form prover, F929).

Gosper's algorithm (R. W. Gosper, "Decision procedure for indefinite
hypergeometric summation", Proc. Natl. Acad. Sci. USA 75(1):40–42, 1978; the
canonical modern reference is Petkovšek, Wilf & Zeilberger, *A = B*, A K Peters
1996, ch. 5) decides whether a hypergeometric term ``t(k)`` has a *hypergeometric
antidifference* ``T(k)`` — a term with ``T(k+1) − T(k) = t(k)`` and
``T(k+1)/T(k)`` rational — and, when it does, RETURNS one. With an antidifference
in hand the sum telescopes: ``Σ_{k=a}^{b} t(k) = T(b+1) − T(a)``.

A hypergeometric term is fully described by its **term ratio**
``t(k+1)/t(k) = num(k)/den(k)`` (two exact-rational polynomials in ``ℚ[k]``).
This op takes that ratio — the two :class:`~srmech.amsc.poly.Poly` operands — and:

  1. reduces ``r = num/den`` (strip the common polynomial factor);
  2. puts ``r`` in **Gosper–Petkovšek normal form** ``r(k) = (a(k)/b(k)) ·
     (c(k+1)/c(k))`` with ``gcd(a(k), b(k+h)) = 1`` for every integer ``h ≥ 0``,
     by peeling ``g = gcd(a(k), b(k+h))`` at each ``h`` in the
     :meth:`~srmech.amsc.poly.Poly.dispersion` set (Class-N over Class-J: exact
     ``ℚ[k]`` GCD / long division / dispersion shift);
  3. solves the **Gosper equation** ``a(k)·x(k+1) − b(k−1)·x(k) = c(k)`` for a
     polynomial ``x`` of bounded degree — the classic Gosper degree bound from
     the degrees + leading coefficients of ``a(k) ± b(k−1)`` — via undetermined
     coefficients: a small EXACT-ℚ linear system solved with the exact
     Gauss-Jordan :class:`~srmech.amsc.qmat.QMat` (C-accelerated as of rc40);
  4. if ``x`` exists, returns the **rational certificate** ``R(k) = b(k−1)·x(k) /
     c(k)`` (the antidifference is ``T(k) = R(k)·t(k)``); else returns ``None``
     (no hypergeometric closed form — e.g. the harmonic ``t(k) = 1/k``).

The whole pipeline stays EXACT over ``ℚ`` — every polynomial is a
:class:`~srmech.amsc.poly.Poly` (two bigint :class:`~srmech.amsc.q.Q` integers per
coefficient, no magnitude ceiling), every solve is exact Gauss-Jordan over ``ℚ``.
There is NO float anywhere; sign is the **Class-K** pin-slot via ``Q`` sign-branch
(never an ALU ``abs()``); no ``math`` module, no numpy. This is the **Σ-row** of
the F929 closure-dispatch: the 14 A–N classes read as a dispatch table over
closed-form reduction theories, and ``gosper`` is the indefinite-summation
reduction (Class-N rational arithmetic over the Class-J prime-field, on the
exact-``ℚ[k]`` polynomial substrate).

C peer: ``srmech_gosper`` (``c/src/srmech_gosper.c``) orchestrates the SAME
existing C kernels — ``srmech_poly_gcd`` / ``srmech_poly_divmod`` /
``srmech_poly_shift`` / ``srmech_poly_mul`` + ``srmech_qmat_solve`` (the exact-ℚ
linear solve) — into one caller-arena, JPL-clean symbol. ``gosper`` routes through
it when ``HAS_NATIVE`` (:func:`srmech.amsc._native.has_native_gosper`); the
pure-Python body here is the COMPLETE alternative (and the byte-identical parity
oracle): both emit the same reduced ``(num, den)`` certificate at any magnitude.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from .poly import Poly
from .q import Q

__all__ = ["gosper"]

_Q_ZERO = Q(0, 1)
_Q_ONE = Q(1, 1)


def _native():
    """The native ``_native`` module IF the rc41 ``srmech_gosper`` peer is present
    and bound, else ``None`` — so ``gosper`` dispatches to C when available and
    falls cleanly to the pure-Python body (the complete alternative + the parity
    oracle) otherwise. Imported lazily to avoid a bootstrap cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    probe = getattr(nat, "has_native_gosper", None)
    return nat if (probe is not None and probe()) else None


def _as_poly(value) -> Poly:
    """Coerce a ``gosper`` operand to a :class:`~srmech.amsc.poly.Poly` (a ``Poly``
    passes through; an ascending-degree coefficient sequence is wrapped via
    :meth:`Poly.from_coeffs`)."""
    if isinstance(value, Poly):
        return value
    return Poly.from_coeffs(value)


def _pairs(p: Poly) -> List[Tuple[int, int]]:
    """A ``Poly``'s coefficients as an ascending ``(num, den)`` int-pair list."""
    return [(c.numerator, c.denominator) for c in p.coeffs]


def gosper(num, den) -> Optional[Dict[str, Poly]]:
    """Gosper's indefinite hypergeometric summation over ``ℚ[k]``.

    ``num`` and ``den`` are the numerator / denominator of the hypergeometric
    **term ratio** ``t(k+1)/t(k) = num(k)/den(k)`` — each a
    :class:`~srmech.amsc.poly.Poly` (or an ascending-degree coefficient sequence
    coerced to one). The op decides whether ``t(k)`` has a hypergeometric
    antidifference ``T(k)`` (a term with ``T(k+1) − T(k) = t(k)``):

    - if it does, returns the **rational certificate** ``{"num": Poly, "den":
      Poly}`` — the reduced rational function ``R(k)`` such that ``T(k) =
      R(k)·t(k)`` is the antidifference (so ``Σ_{k=a}^{b} t(k) = T(b+1) − T(a)``);
    - if no hypergeometric closed form exists (e.g. the harmonic ``t(k) = 1/k``,
      ratio ``k/(k+1)``), returns ``None``.

    Exact over ``ℚ`` (bigint, no magnitude ceiling); no float, no ``abs()`` (the
    sign is the Class-K pin-slot), no ``math`` / numpy. See the module docstring
    for the full Gosper / PWZ pipeline. ``den`` must not be the zero polynomial
    (a term ratio has a nonzero denominator) — ``ValueError`` otherwise.
    """
    num_p = _as_poly(num)
    den_p = _as_poly(den)
    if den_p.is_zero:
        raise ValueError(
            "gosper: the term-ratio denominator must be a NONZERO polynomial "
            "(t(k+1)/t(k) = num(k)/den(k) has a nonzero den)")
    if num_p.is_zero:
        # t(k+1)/t(k) = 0 ⇒ the term vanishes after the first step; the trivial
        # antidifference is R(k) = 0 → None (no NONZERO hypergeometric closed
        # form to certify). Mirrors the x ≡ 0 leaf below.
        return None

    nat = _native()
    if nat is not None:
        try:
            got = nat.gosper_c(_pairs(num_p), _pairs(den_p))
            if got is not None:
                has, r_num_pairs, r_den_pairs = got
                if not has:
                    return None
                return {"num": Poly.from_coeffs([Q(n, d) for n, d in r_num_pairs]),
                        "den": Poly.from_coeffs([Q(n, d) for n, d in r_den_pairs])}
        except (RuntimeError, OverflowError, ValueError):
            pass                                  # fall to the pure path

    return _gosper_pure(num_p, den_p)


# ── pure-Python Gosper (the COMPLETE alternative + the parity oracle) ──────────

def _gosper_pure(num_p: Poly, den_p: Poly) -> Optional[Dict[str, Poly]]:
    """The exact-ℚ pure-Python Gosper pipeline (the complete, ceiling-free
    alternative to the C peer). See the module docstring."""
    a, b, c = _gosper_petkovsek_form(num_p, den_p)
    x = _solve_gosper_equation(a, b, c)
    if x is None or x.is_zero:
        return None                               # no hypergeometric antidifference
    # R(k) = b(k−1)·x(k) / c(k), reduced to lowest terms over ℚ[k].
    r_num = b.shift(Q(-1, 1)) * x
    r_den = c
    g = r_num.gcd(r_den)
    if not g.is_zero and g.degree >= 1:
        r_num = r_num.divmod(g)[0]
        r_den = r_den.divmod(g)[0]
    return {"num": r_num, "den": r_den}


def _gosper_petkovsek_form(a: Poly, b: Poly) -> Tuple[Poly, Poly, Poly]:
    """The Gosper–Petkovšek normal form of ``r = a/b``: returns ``(a', b', c)`` with
    ``r(k) = (a'(k)/b'(k))·(c(k+1)/c(k))`` and ``gcd(a'(k), b'(k+h)) = 1`` for every
    integer ``h ≥ 0``.

    Peels the common factor at each non-negative integer shift in the
    :meth:`~srmech.amsc.poly.Poly.dispersion` set: for ``h`` with ``g(k) =
    gcd(a(k), b(k+h))`` non-constant, divide ``g(k)`` out of ``a``, divide
    ``g(k−h)`` out of ``b``, and accumulate ``c ·= Π_{j=1}^{h} g(k−j)`` (the
    Petkovšek bookkeeping that keeps ``r`` invariant). Exact over ``ℚ[k]``."""
    c = Poly.one()
    while True:
        # the standard GP convention: the SECOND argument is shifted by +h.
        disp = [h for h in a.dispersion(b) if h >= 0]
        if not disp:
            break
        h = disp[0]
        g = a.gcd(b.shift(Q(h, 1)))               # g(k) = gcd(a(k), b(k+h)), monic
        if g.is_zero or g.degree < 1:
            break
        a = a.divmod(g)[0]                         # a ← a / g(k)   (exact)
        b = b.divmod(g.shift(Q(-h, 1)))[0]        # b ← b / g(k−h) (exact)
        for j in range(1, h + 1):
            c = c * g.shift(Q(-j, 1))             # c ← c · g(k−j)
    return a, b, c


def _gosper_degree_bound(a: Poly, b_minus: Poly, c: Poly) -> int:
    """The Gosper degree bound on ``x`` in ``a(k)·x(k+1) − b(k−1)·x(k) = c(k)``
    (PWZ *A=B* §5.3). With ``s = a + b(k−1)`` and ``d = a − b(k−1)``:

    - if ``a(k) = b(k−1)`` (so ``d ≡ 0``): ``deg x = deg c − deg a + 1``;
    - else if ``deg d ≥ deg s``: ``deg x = deg c − deg d``;
    - else: a candidate ``deg x`` from the leading-coefficient ratio
      ``−2·lc(d)/lc(s)`` (used only when it is a non-negative integer), taken with
      ``deg c − deg s + 1``.

    Returns the bound, or ``-1`` when it is negative (no polynomial solution)."""
    s = a + b_minus
    d = a - b_minus
    if a == b_minus:
        return c.degree - a.degree + 1
    s_deg = s.degree
    if d.degree >= s_deg:
        return c.degree - d.degree
    # leading-coefficient ratio candidate (Class-N exact ℚ; used iff a non-neg int)
    ratio = (Q(-2, 1) * d.leading) / s.leading
    base = c.degree - s_deg + 1
    if ratio.denominator == 1 and ratio.numerator >= 0:
        return base if base >= ratio.numerator else ratio.numerator
    return base


def _solve_gosper_equation(a: Poly, b: Poly, c: Poly) -> Optional[Poly]:
    """Solve ``a(k)·x(k+1) − b(k−1)·x(k) = c(k)`` for a polynomial ``x`` over ``ℚ``,
    via undetermined coefficients of bounded degree. Returns the ``x`` ``Poly`` (the
    free-coefficient slots set to ``0`` — any choice is a valid antidifference) or
    ``None`` when the linear system is inconsistent (no polynomial solution)."""
    b_minus = b.shift(Q(-1, 1))                   # b(k−1)
    deg_bound = _gosper_degree_bound(a, b_minus, c)
    if deg_bound < 0:
        return None
    # Column j (j = 0..deg_bound) is the polynomial contribution of the unknown
    # coefficient x_j: P_j(k) = a(k)·(k+1)^j − b(k−1)·k^j. The linear system over
    # the unknowns x_0..x_deg_bound is Σ_j x_j · P_j(k) = c(k), matched coefficient
    # by coefficient.
    cols: List[Poly] = []
    max_deg = c.degree
    for j in range(deg_bound + 1):
        k_pow = Poly.monomial(j)                  # k^j
        p_j = a * k_pow.shift(Q(1, 1)) - b_minus * k_pow
        cols.append(p_j)
        if p_j.degree > max_deg:
            max_deg = p_j.degree
    n_rows = max_deg + 1
    n_cols = deg_bound + 1
    # the exact augmented matrix [A | c]: row r, column j is the coeff of k^r in P_j.
    aug_rows = [
        [cols[j][r] for j in range(n_cols)] + [c[r]]
        for r in range(n_rows)
    ]
    return _solve_exact(aug_rows, n_cols)


def _solve_exact(aug_rows: Sequence[Sequence[Q]], n_cols: int) -> Optional[Poly]:
    """Solve the (possibly over-determined) exact-ℚ linear system whose augmented
    ``[A | c]`` rows are ``aug_rows`` (the last column the RHS), over ``n_cols``
    unknowns. Routes the elimination through the exact Gauss-Jordan RREF of the
    :class:`~srmech.amsc.qmat.QMat` (C-accelerated when present): a free column →
    ``0`` (any choice is valid), a pivot in the RHS column → inconsistent →
    ``None``. Returns the solution as an ascending-degree ``Poly`` ``x``."""
    from .qmat import QMat
    if not aug_rows:
        return Poly.zero()
    rref = QMat.from_rows([list(r) for r in aug_rows]).rref()
    x = [_Q_ZERO] * n_cols
    for row in rref.to_lists():
        pivot = None
        for j in range(n_cols + 1):
            if row[j] != 0:
                pivot = j
                break
        if pivot is None:
            continue                              # an all-zero row
        if pivot == n_cols:
            return None                           # 0 = nonzero ⇒ inconsistent
        x[pivot] = row[n_cols]                    # rref ⇒ value is the RHS entry
    return Poly.from_coeffs(x)
