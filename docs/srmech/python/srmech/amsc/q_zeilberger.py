"""srmech.amsc.q_zeilberger — the q-analog of Zeilberger's creative telescoping (the
SECOND public op of the q-hypergeometric F929 reduction row, the q-analog of the §76
``zeilberger``).

Where :func:`srmech.amsc.q_gosper.q_gosper` decides INDEFINITE q-summation of a
single q-hypergeometric term in ``k`` (its term ratio a rational function of ``x =
q**k``), the **q-Zeilberger** algorithm (T.H. Koornwinder, "On Zeilberger's algorithm
and its q-analogue," J. Comput. Appl. Math. 48 (1993) 91–111 — the same paper the
:class:`~srmech.amsc.qpoly.QPoly` carrier and :func:`~srmech.amsc.q_gosper.q_gosper`
cite; textbook anchor Gasper & Rahman, *Basic Hypergeometric Series*) handles a
DEFINITE q-sum ``f(n) = Σ_k F(n,k)`` of a *proper q-hypergeometric term* ``F(n,k)``
and produces the **linear q-recurrence with ℚ[q**n] coefficients**

    Σ_{j=0}^{L} a_j(q**n) · f(n+j) = 0

that ``f`` satisfies — the minimal-order such recurrence, each ``a_j(q**n)`` an exact
polynomial in ``q**n`` over ``ℚ(q)`` (the q-analog of the ordinary recurrence's
``ℚ[n]`` coefficients).

Input — the **two bivariate-q term ratios** of ``F``, each a rational function of
``(X, Y) = (q**n, q**k)``:

  * ``r_n(X, Y) = F(n+1,k) / F(n,k)``   (the ``rn_num`` / ``rn_den`` operands)
  * ``r_k(X, Y) = F(n,k+1) / F(n,k)``   (the ``rk_num`` / ``rk_den`` operands)

each given as two :class:`~srmech.amsc.qbipoly.QBiPoly` (exact bivariate-``ℚ[q]`` in
``(X, Y)`` — a polynomial in ``Y = q**k`` whose coefficients are
:class:`~srmech.amsc.qpoly.QPoly` in ``X = q**n``). A plain
:class:`~srmech.amsc.qpoly.QPoly` (a polynomial in ``Y`` alone, no ``X``), a
:class:`~srmech.amsc.poly.Poly` in ``q`` (a scalar), or an ascending-``Y``-degree
``QPoly`` sequence is coerced.

Method — **q-creative telescoping** (the rational-certificate form, the q-analog of
Zeilberger's), for ``L = 0, 1, 2, …, max_order``:

  1. Form the ansatz ``T(n,k) = Σ_{j=0}^{L} a_j(X)·F(n+j,k)``, where
     ``F(n+j,k)/F(n,k) = ∏_{i=0}^{j-1} r_n(q**i·X, Y)`` is the n-direction q-shift
     product (a rational function of ``(X,Y)``), so ``T = F·P`` with ``P = Σ_j
     a_j(X)·ρ_j(X,Y)`` a rational function of ``Y`` (coefficients in ``ℚ(q)[X]`` — the
     unknown polynomials ``a_j(X)``).
  2. Apply **q-Gosper in k** to ``T``: its k-term-ratio is ``r_k(X,Y)·P(X,qY)/
     P(X,Y)`` (the ``k ↦ k+1`` shift is ``σ_y : Y ↦ q·Y``). Running the q-Gosper
     telescoping with the ``a_j(X)`` carried as additional unknowns makes the
     q-Gosper equation LINEAR in ``{a_j(X) coeffs} ∪ {certificate-poly coeffs}`` —
     one exact-``ℚ(q)`` linear system (solved with the SAME exact Gauss-Jordan over
     the field ``ℚ(q)`` the rc55 q-Gosper carries: :func:`srmech.amsc.q_gosper.
     _rref_cq`, the ``_Cq`` rational-function-in-``q`` field layer).
  3. The first ``L`` with a nonzero solution gives the recurrence coefficients
     ``a_j(X)`` and the rational certificate ``R(X,Y) = x(X,Y)/D_P(X,Y)`` (the
     q-Gosper certificate of ``T``): ``Σ_j a_j(X) F(n+j,k) = G(n,k+1) − G(n,k)`` with
     ``G = R·F``. Summing over ``k`` (natural boundary: ``G`` vanishes at the
     ``k``-limits) gives ``Σ_j a_j(q**n) f(n+j) = 0``.

The whole pipeline stays EXACT over ``ℚ(q)`` — every q-coefficient is an exact
rational function of ``q`` (the rc55 ``_Cq``: a reduced ``(num, den)`` pair of
:class:`~srmech.amsc.poly.Poly` over ℚ, bigint, no magnitude ceiling), every solve is
exact Gauss-Jordan over ``ℚ(q)``. There is NO float anywhere; sign is the **Class-K**
pin-slot via the ``Q`` / ``Poly`` sign-branch (never an ALU ``abs()``); no ``math``
module, no numpy. This op PARAMETRIZES the rc55 q-Gosper engine (it imports and
reuses the ``_Cq`` field + the ``_rref_cq`` ℚ(q) Gauss-Jordan rather than
re-deriving them); the q-row continues with the q-WZ proof op (rc57), which reuses
this op's order-1 path + the certificate/verify shape.

C peer: ``srmech_q_zeilberger`` (``c/src/srmech_q_zeilberger.c``) mirrors
``srmech_zeilberger``'s scope — it orchestrates the SAME existing C kernels (the
``srmech_qpoly_*`` q-shift algebra + an exact-``ℚ(q)`` undetermined-coefficient solve
riding ``srmech_qmat_rref``) into one caller-arena, JPL-clean symbol that ACCELERATES
the canonical low-order case (**order ≤ 1**, the textbook q-identities). It routes
through it when ``HAS_NATIVE`` (:func:`srmech.amsc._native.has_native_q_zeilberger`)
and the C reports a positive (recurrence-found) result; a ``has=0`` C result is NOT
trusted as a definitive "no recurrence" (the C caps its ansatz order below an
unbounded search), so it falls through to the COMPLETE pure-Python body here — the
full-coverage decider AND the byte-identical parity oracle.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .poly import Poly
from .q import Q
from .qpoly import QPoly
from .qbipoly import QBiPoly
# Reuse the rc55 q-Gosper engine's exact-ℚ(q) field layer (the ``_Cq`` rational-
# function-in-q field) — the parametrization payoff: q-Zeilberger does NOT re-derive
# the ℚ(q) coefficient arithmetic the q-Gosper undetermined-coefficient solve runs on.
from .q_gosper import _Cq

__all__ = ["q_zeilberger"]

_Q_ZERO = Q(0, 1)
_Q_ONE = Q(1, 1)
_POLY_ZERO = Poly.zero()
_POLY_ONE = Poly.one()


def _native():
    """The native ``_native`` module IF the rc56 ``srmech_q_zeilberger`` peer is
    present and bound, else ``None`` — so ``q_zeilberger`` dispatches to C when
    available and falls cleanly to the pure-Python body (the complete alternative +
    the parity oracle) otherwise. Imported lazily to avoid a bootstrap cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    probe = getattr(nat, "has_native_q_zeilberger", None)
    return nat if (probe is not None and probe()) else None


# ── the (X, Y) → _Cq monomial form (X Laurent over ℚ(q); Y ascending) ─────────
#
# For the linear algebra a QBiPoly is read as a sparse ``{(x_exp, y_exp): _Cq}``
# mapping — the x-coefficient ring lifted to the FIELD ℚ(q) (each ℚ[q] cell over the
# unit denominator), exactly as q-Gosper lifts a QPoly. The Y part is ascending
# (the term ratios are polynomials in Y); the X part carries the Laurent window.


def _qb_to_xy(b: QBiPoly) -> Dict[Tuple[int, int], _Cq]:
    """A :class:`~srmech.amsc.qbipoly.QBiPoly` → the working ``{(x_exp, y_exp):
    _Cq}`` form (the q-coefficients lifted to ``ℚ(q)`` over the unit denominator)."""
    out: Dict[Tuple[int, int], _Cq] = {}
    for yd, cell in enumerate(b.terms):
        if cell.is_zero:
            continue
        for i, qcell in enumerate(cell.cells):
            if qcell.is_zero:
                continue
            out[(cell.x_low + i, yd)] = _Cq.from_poly(qcell)
    return out


def _xy_mul(a: Dict[Tuple[int, int], _Cq], b: Dict[Tuple[int, int], _Cq]
            ) -> Dict[Tuple[int, int], _Cq]:
    """Exact (X, Y)-monomial convolution over the field ``ℚ(q)`` (the X-window is
    Laurent; the Y-window ascending)."""
    out: Dict[Tuple[int, int], _Cq] = {}
    for (xa, ya), ca in a.items():
        for (xb, yb), cb in b.items():
            key = (xa + xb, ya + yb)
            prev = out.get(key)
            out[key] = (prev + ca * cb) if prev is not None else (ca * cb)
    return {k: v for k, v in out.items() if not v.is_zero}


def _xy_qshift_x(d: Dict[Tuple[int, int], _Cq], s: int
                 ) -> Dict[Tuple[int, int], _Cq]:
    """``σ_x**s : X ↦ q**s·X`` — the ``x_exp = e`` monomial picks up ``q**(s·e)`` (the
    n-direction q-shift; ``_Cq.q_power`` carries any negative q-power exactly)."""
    out: Dict[Tuple[int, int], _Cq] = {}
    for (xe, ye), c in d.items():
        out[(xe, ye)] = c * _Cq.q_power(s * xe)
    return {k: v for k, v in out.items() if not v.is_zero}


def _xy_qshift_y(d: Dict[Tuple[int, int], _Cq], s: int
                 ) -> Dict[Tuple[int, int], _Cq]:
    """``σ_y**s : Y ↦ q**s·Y`` — the ``y_exp = d`` monomial picks up ``q**(s·d)`` (the
    k-direction q-shift)."""
    out: Dict[Tuple[int, int], _Cq] = {}
    for (xe, ye), c in d.items():
        out[(xe, ye)] = c * _Cq.q_power(s * ye)
    return {k: v for k, v in out.items() if not v.is_zero}


def _xy_add(a: Dict[Tuple[int, int], _Cq], b: Dict[Tuple[int, int], _Cq],
            sub: bool = False) -> Dict[Tuple[int, int], _Cq]:
    out = dict(a)
    for k, c in b.items():
        prev = out.get(k)
        nv = (prev - c) if (prev is not None and sub) else \
             (prev + c) if prev is not None else (-c if sub else c)
        out[k] = nv
    return {k: v for k, v in out.items() if not v.is_zero}


def _xy_scale(d: Dict[Tuple[int, int], _Cq], c: _Cq) -> Dict[Tuple[int, int], _Cq]:
    if c.is_zero:
        return {}
    return {k: v * c for k, v in d.items() if not (v * c).is_zero}


# ── the public op ─────────────────────────────────────────────────────────────

def q_zeilberger(rn_num, rn_den, rk_num, rk_den, max_order: int = 6
                 ) -> Optional[Dict[str, object]]:
    """The q-analog of Zeilberger's creative-telescoping recurrence for the definite
    q-hypergeometric sum ``f(n) = Σ_k F(n,k)`` over ``(X, Y) = (q**n, q**k)``.

    ``rn_num`` / ``rn_den`` are the numerator / denominator of the n-term-ratio
    ``r_n(X,Y) = F(n+1,k)/F(n,k)``; ``rk_num`` / ``rk_den`` likewise for the
    k-term-ratio ``r_k(X,Y) = F(n,k+1)/F(n,k)``. Each is a
    :class:`~srmech.amsc.qbipoly.QBiPoly` (exact bivariate-``ℚ[q]`` in ``(X,Y)``), or
    a :class:`~srmech.amsc.qpoly.QPoly` (read as a polynomial in ``Y`` alone), a
    :class:`~srmech.amsc.poly.Poly` in ``q`` (a scalar), or an ascending-``Y``-degree
    ``QPoly`` sequence.

    Returns the minimal-order q-recurrence ``{"order": L, "coeffs": [QPoly_in_X, …],
    "certificate": QBiPoly}`` such that ``Σ_{j=0}^{L} coeffs[j](q**n)·f(n+j) = 0``, or
    ``None`` when no such recurrence of order ≤ ``max_order`` exists (the honest
    no-q-recurrence residue). The ``coeffs[j]`` are exact ``QPoly`` in ``X = q**n``;
    the ``certificate`` is the q-Gosper certificate numerator ``x(X,Y)`` (``R = x/
    D_P``).

    Exact over ``ℚ(q)`` (bigint, no magnitude ceiling); no float, no ``abs()`` (the
    sign is the Class-K pin-slot), no ``math`` / numpy. ``rn_den`` / ``rk_den`` must
    be nonzero (a term ratio has a nonzero denominator) — ``ValueError`` otherwise."""
    rn_n = QBiPoly.coerce(rn_num)
    rn_d = QBiPoly.coerce(rn_den)
    rk_n = QBiPoly.coerce(rk_num)
    rk_d = QBiPoly.coerce(rk_den)
    if rn_d.is_zero or rk_d.is_zero:
        raise ValueError(
            "q_zeilberger: the term-ratio denominators r_n den / r_k den must be "
            "NONZERO bivariate-q polynomials")
    if not isinstance(max_order, int) or max_order < 0:
        raise ValueError("q_zeilberger: max_order must be a non-negative int")

    nat = _native()
    if nat is not None:
        try:
            got = nat.q_zeilberger_c(_qb_pairs(rn_n), _qb_pairs(rn_d),
                                     _qb_pairs(rk_n), _qb_pairs(rk_d), max_order)
            # The C peer accelerates the POSITIVE (recurrence-found) case only: a
            # has=1 result is byte-identical to the pure path. A has=0 (the C found
            # nothing within its own order cap) is NOT trusted as a definitive "no
            # recurrence" (the C caps its ansatz order below an unbounded search), so
            # it falls through to the complete pure-Python path — the parity oracle
            # AND the full-coverage decider.
            if got is not None:
                has, order, coeff_forms, cert_form = got
                if has:
                    coeffs = [_qg_from_pairs(cf) for cf in coeff_forms]
                    cert = _qb_from_pairs(cert_form)
                    return {"order": order, "coeffs": coeffs, "certificate": cert}
        except (RuntimeError, OverflowError, ValueError):
            pass                                  # fall to the pure path

    return _q_zeilberger_pure(rn_n, rn_d, rk_n, rk_d, max_order)


# ── pure-Python q-Zeilberger (the COMPLETE alternative + the parity oracle) ────

def _q_zeilberger_pure(rn_n: QBiPoly, rn_d: QBiPoly, rk_n: QBiPoly, rk_d: QBiPoly,
                       max_order: int) -> Optional[Dict[str, object]]:
    """The exact-ℚ(q) pure-Python q-creative-telescoping pipeline. Tries ansatz
    orders ``L = 0..max_order``; the first nonzero solution is the minimal
    recurrence."""
    rn_n_xy = _qb_to_xy(rn_n)
    rn_d_xy = _qb_to_xy(rn_d)
    rk_n_xy = _qb_to_xy(rk_n)
    rk_d_xy = _qb_to_xy(rk_d)
    for order in range(max_order + 1):
        got = _try_order(rn_n_xy, rn_d_xy, rk_n_xy, rk_d_xy, order)
        if got is not None:
            return got
    return None


def _rho(rn_n_xy, rn_d_xy, j: int) -> Tuple[Dict, Dict]:
    """``ρ_j(X,Y) = F(n+j,k)/F(n,k) = ∏_{i=0}^{j-1} r_n(q**i·X, Y)`` as a rational
    ``(num, den)`` pair of (X,Y)-monomial dicts over ℚ(q). ``ρ_0 = 1``."""
    num = {(0, 0): _Cq.one()}
    den = {(0, 0): _Cq.one()}
    for i in range(j):
        num = _xy_mul(num, _xy_qshift_x(rn_n_xy, i))
        den = _xy_mul(den, _xy_qshift_x(rn_d_xy, i))
    return num, den


def _try_order(rn_n_xy, rn_d_xy, rk_n_xy, rk_d_xy, order: int
               ) -> Optional[Dict[str, object]]:
    """Attempt the order-``order`` q-ansatz. Build the parametrized q-Gosper-in-k
    homogeneous linear system over ℚ(q) in the unknowns ``{a_j(X) coeffs} ∪ {x(X,Y)
    coeffs}`` and solve it; on a nonzero solution return the recurrence +
    certificate."""
    rhos = [_rho(rn_n_xy, rn_d_xy, j) for j in range(order + 1)]
    # D_P(X,Y) = Π_j ρ_den_j (the shared certificate denominator).
    den_p: Dict[Tuple[int, int], _Cq] = {(0, 0): _Cq.one()}
    for _, dj in rhos:
        den_p = _xy_mul(den_p, dj)
    # numerators of each ρ_j over the common D_P: ρ_num_j · (D_P / ρ_den_j).
    rho_over_common: List[Dict[Tuple[int, int], _Cq]] = []
    for nj, dj in rhos:
        cofactor = _xy_exact_div(den_p, dj)
        rho_over_common.append(_xy_mul(nj, cofactor))
    return _solve_parametrized(rho_over_common, den_p, rk_n_xy, rk_d_xy, order)


def _xy_exact_div(a: Dict[Tuple[int, int], _Cq], b: Dict[Tuple[int, int], _Cq]
                  ) -> Dict[Tuple[int, int], _Cq]:
    """Exact division ``a / b`` of (X,Y)-monomial dicts over ℚ(q) when ``b`` divides
    ``a`` (the ``D_P / ρ_den_j`` cofactors — exact by construction since ``ρ_den_j``
    is a factor of the product ``D_P``). A multivariate long division in ``Y`` with
    exact ``ℚ(q)[X]``-Laurent leading-term arithmetic; raises if it does not divide
    cleanly (a guard, never hit on the cofactor inputs)."""
    if not b:
        raise ZeroDivisionError("QBiPoly exact-div by zero")
    if not a:
        return {}
    rem = dict(a)
    bdeg = max(ye for (_xe, ye) in b)
    # the leading-Y term of b: the X-Laurent poly at the highest Y-degree.
    blead = {xe: c for (xe, ye), c in b.items() if ye == bdeg}
    quo: Dict[Tuple[int, int], _Cq] = {}
    guard = 0
    while rem and guard <= 4096:
        rdeg = max(ye for (_xe, ye) in rem)
        if rdeg < bdeg:
            break
        rlead = {xe: c for (xe, ye), c in rem.items() if ye == rdeg}
        # divide the leading X-Laurent terms: fac(X) = rlead / blead (a single
        # X-monomial quotient times a _Cq ratio — exact only when the X-windows align
        # as a single shift; for the cofactor inputs the leads are X-monomials).
        fac = _xlaurent_div(rlead, blead)
        if fac is None:
            raise ValueError("QBiPoly exact-div: non-monomial leading divide (internal)")
        fx, fc = fac
        ydelta = rdeg - bdeg
        # subtract fac · b from rem (shifted by Y**ydelta · X**fx · fc).
        for (xe, ye), c in b.items():
            key = (xe + fx, ye + ydelta)
            prev = rem.get(key)
            nv = (prev - c * fc) if prev is not None else (-(c * fc))
            if nv.is_zero:
                rem.pop(key, None)
            else:
                rem[key] = nv
        quo[(fx, ydelta)] = fc
        guard += 1
    if rem:
        raise ValueError("QBiPoly exact-div: non-zero remainder (internal)")
    return {k: v for k, v in quo.items() if not v.is_zero}


def _xlaurent_div(num: Dict[int, _Cq], den: Dict[int, _Cq]
                  ) -> Optional[Tuple[int, _Cq]]:
    """Divide two single-Y-slice X-Laurent ``{x_exp: _Cq}`` leads when the quotient is
    a single X-monomial ``X**fx · fc`` — i.e. both are single X-monomials. Returns
    ``(fx, fc)`` or ``None`` (a non-monomial divisor, which the cofactor path never
    produces — ρ_den_j leads are single X-monomials by the q-shift product
    structure)."""
    nz_n = {e: c for e, c in num.items() if not c.is_zero}
    nz_d = {e: c for e, c in den.items() if not c.is_zero}
    if len(nz_d) != 1 or len(nz_n) != 1:
        return None
    (xn, cn), = nz_n.items()
    (xd, cd), = nz_d.items()
    return xn - xd, cn / cd


def _solve_parametrized(rho_common: List[Dict[Tuple[int, int], _Cq]],
                        den_p: Dict[Tuple[int, int], _Cq], rk_n_xy, rk_d_xy,
                        order: int) -> Optional[Dict[str, object]]:
    """Build + solve the homogeneous exact-ℚ(q) linear system for the order-``order``
    q-creative-telescoping ansatz. The unknowns are the ℚ(q)-coefficients of each
    ``a_j(X)`` (X-degree-bounded) and of the q-Gosper certificate numerator
    ``x(X,Y)``. A nonzero kernel vector yields the recurrence + the rational
    certificate ``R(X,Y) = x(X,Y)/D_P(X,Y)`` (the cleared-Gosper bookkeeping folded
    in below)."""
    # The cleared q-Gosper telescoping identity (the q-analog of Zeilberger's), over
    # the common denominator D_P. With G = R·F = (x/D_P)·F and the k-shift σ_y:Y↦qY:
    #   N_P(X,Y)·rk_d(X,Y)·D_P(X,qY)
    #       = x(X,qY)·rk_n(X,Y)·D_P(X,Y) − x(X,Y)·rk_d(X,Y)·D_P(X,qY),
    # with N_P(X,Y) = Σ_j a_j(X)·rho_common[j](X,Y). Both sides are LINEAR in the
    # unknowns {a_j coeffs} ∪ {x coeffs}; matching each (X,Y) monomial gives a
    # homogeneous ℚ(q)-linear system. A nonzero kernel with a nonzero a-block = a
    # q-recurrence.
    x_deg = _ansatz_x_degree(rho_common, den_p, rk_n_xy, rk_d_xy)
    xk_deg, xn_lo, xn_hi = _ansatz_cert_degree(rho_common, den_p, rk_n_xy, rk_d_xy)

    n_a = order + 1
    a_slots = x_deg + 1                       # a_j(X) X-degrees 0..x_deg
    a_block = n_a * a_slots
    xn_span = xn_hi - xn_lo + 1               # certificate X-exponents xn_lo..xn_hi
    x_block = (xk_deg + 1) * xn_span
    n_unknowns = a_block + x_block
    if n_unknowns == 0:
        return None

    rows, col_layout = _assemble_rows(rho_common, den_p, rk_n_xy, rk_d_xy, order,
                                      x_deg, xk_deg, xn_lo, xn_hi, a_block, n_a,
                                      a_slots, xn_span)
    if not rows:
        return None
    kernel = _homogeneous_kernel(rows, n_unknowns, a_block)
    if kernel is None:
        return None
    a_coeffs, x_coeffs = kernel
    # Clear the WHOLE solution {a_j coeffs} ∪ {x coeffs} by ONE shared ℚ(q)
    # factor (the monic LCM of every _Cq denominator) so each lands in ℚ[q] AND
    # the recurrence ↔ certificate RELATIVE scaling is preserved (load-bearing
    # for the q-WZ relation Σ_j a_j F = Δ_q(R·F) the rc57 q_wz verifies — a
    # per-cell clear would rescale a and x independently and break it).
    shared_den = _shared_cq_den(a_coeffs + x_coeffs)
    a_cleared = [_clear_with(c, shared_den) for c in a_coeffs]
    x_cleared = [_clear_with(c, shared_den) for c in x_coeffs]
    coeffs = [QPoly.from_coeffs(a_cleared[j * a_slots:(j + 1) * a_slots])
              for j in range(n_a)]
    if all(c.is_zero for c in coeffs):
        return None
    cert = _x_cleared_to_qbipoly(x_cleared, xk_deg, xn_lo, xn_span)
    return {"order": order, "coeffs": coeffs, "certificate": cert}


def _shared_cq_den(cells: List[_Cq]) -> Poly:
    """The monic LCM (over ``ℚ[q]``) of every ``_Cq`` denominator across the whole
    ``(a, x)`` solution — the single factor that clears the entire solution into
    ``ℚ[q]`` while preserving the recurrence ↔ certificate relative scaling."""
    den = _POLY_ONE
    for c in cells:
        if c.is_zero:
            continue
        den = _lcm_poly(den, c.den)
    return den


def _lcm_poly(a: Poly, b: Poly) -> Poly:
    """The monic LCM of two ``ℚ[q]`` polynomials (``a·b / gcd(a,b)``), monic (the
    q_gosper ``_lcm_poly`` peer; kept local to avoid a cross-module private import)."""
    if a.is_zero or b.is_zero:
        return _POLY_ZERO
    g = a.gcd(b)
    lcm = (a * b).divmod(g)[0]
    return lcm.monic()


def _clear_with(c: _Cq, shared_den: Poly) -> Poly:
    """Multiply a ``_Cq`` by the shared ``ℚ[q]`` denominator ``shared_den`` → an
    exact ``ℚ[q]`` numerator (``c.num · (shared_den / c.den)``; the division is exact
    because ``shared_den`` is a multiple of every ``c.den``)."""
    if c.is_zero:
        return _POLY_ZERO
    scale = shared_den.divmod(c.den)[0]
    return c.num * scale


def _x_cleared_to_qbipoly(x_cells: List[Poly], xk_deg: int, xn_lo: int,
                          xn_span: int) -> QBiPoly:
    """Pack the cleared (``ℚ[q]``) certificate-coefficient vector (Y-major, then X)
    into a :class:`~srmech.amsc.qbipoly.QBiPoly` ``x(X,Y)``."""
    terms: List[QPoly] = []
    for dk in range(xk_deg + 1):
        run = x_cells[dk * xn_span:(dk + 1) * xn_span]
        terms.append(QPoly.from_coeffs(run, xn_lo))
    return QBiPoly(terms)


def _assemble_rows(rho_common, den_p, rk_n_xy, rk_d_xy, order, x_deg, xk_deg,
                   xn_lo, xn_hi, a_block, n_a, a_slots, xn_span):
    """Assemble the homogeneous ℚ(q)-linear system rows. Each row is the ℚ(q)
    coefficient of one ``X**p · Y**q`` monomial in the cleared q-Gosper identity,
    expanded with each unknown (an ``a_j``-coeff or an ``x``-coeff) carrying its
    monomial contribution. Returns ``(rows, None)``."""
    dp_qy = _xy_qshift_y(den_p, 1)                # D_P(X, qY)
    lhs_clear = _xy_mul(rk_d_xy, dp_qy)           # rk_d · D_P(qY) (the LHS clearing)
    xp_clear = _xy_mul(rk_n_xy, den_p)            # multiplies x(X,qY): rk_n · D_P(Y)
    xm_clear = _xy_mul(rk_d_xy, dp_qy)            # multiplies x(X,Y):  rk_d · D_P(qY)

    monomials: Dict[Tuple[int, int], List[_Cq]] = {}

    def _add(contrib: Dict[Tuple[int, int], _Cq], col: int, sign: int) -> None:
        for key, c in contrib.items():
            if c.is_zero:
                continue
            row = monomials.get(key)
            if row is None:
                row = [_Cq.zero()] * n_unknowns
                monomials[key] = row
            row[col] = row[col] + (c if sign > 0 else -c)

    n_unknowns = a_block + (xk_deg + 1) * xn_span

    # a_j columns: column for a_j(X)'s X**p coeff is
    #   X**p · rho_common[j](X,Y) · rk_d(X,Y) · D_P(X,qY)
    for j in range(order + 1):
        base = _xy_mul(rho_common[j], lhs_clear)
        for p in range(a_slots):
            col = j * a_slots + p
            contrib = _xy_mul(base, {(p, 0): _Cq.one()})
            _add(contrib, col, +1)

    # x columns: x(X,qY) term (negative, moved to LHS) and x(X,Y) term (positive).
    for dk in range(xk_deg + 1):
        for di in range(xn_span):
            xe = xn_lo + di
            col = a_block + dk * xn_span + di
            x_mono = {(xe, dk): _Cq.one()}        # x = X**xe · Y**dk
            xp = _xy_mul(_xy_qshift_y(x_mono, 1), xp_clear)   # x(X,qY)·rk_n·D_P(Y)
            xm = _xy_mul(x_mono, xm_clear)                    # x(X,Y)·rk_d·D_P(qY)
            _add(xp, col, -1)
            _add(xm, col, +1)

    return [monomials[key] for key in sorted(monomials)], None


# ── degree bounds ──────────────────────────────────────────────────────────────

def _x_window(d: Dict[Tuple[int, int], _Cq]) -> Tuple[int, int]:
    """The (min, max) X-exponent across an (X,Y)-monomial dict (``(0, -1)`` for the
    empty dict — an empty span)."""
    if not d:
        return 0, -1
    xs = [xe for (xe, _ye) in d]
    return min(xs), max(xs)


def _y_degree(d: Dict[Tuple[int, int], _Cq]) -> int:
    """The max Y-degree across an (X,Y)-monomial dict (``-1`` for empty)."""
    if not d:
        return -1
    return max(ye for (_xe, ye) in d)


def _ansatz_x_degree(rho_common, den_p, rk_n_xy, rk_d_xy) -> int:
    """A degree bound (X-EXTENT) for the unknown ``a_j(X)`` — the max X-span across
    the assembled-identity inputs, plus one. A proper q-hypergeometric term's
    recurrence coefficients have X-extent comparable to the inputs; a too-small bound
    at a given order simply yields no kernel there and the search advances (the C peer
    mirrors this bound exactly for parity)."""
    d = 1
    for b in (den_p, rk_n_xy, rk_d_xy, *rho_common):
        lo, hi = _x_window(b)
        ext = hi - lo if hi >= lo else 0
        if ext > d:
            d = ext
    return d + 1


def _ansatz_cert_degree(rho_common, den_p, rk_n_xy, rk_d_xy
                        ) -> Tuple[int, int, int]:
    """Degree bounds ``(Y-degree, X-lo, X-hi)`` for the q-Gosper certificate numerator
    ``x(X,Y)`` written over ``D_P`` — the Y-degree from the assembled identity (the
    max input Y-degree, +1), the X-window from the input X-windows (extended by one
    each way to carry the Laurent tail). Tight (keeps the system small + exact); the C
    peer mirrors these for byte-parity."""
    kd = _y_degree(den_p)
    for b in rho_common:
        kd = max(kd, _y_degree(b))
    kd = max(kd, _y_degree(rk_n_xy), _y_degree(rk_d_xy)) + 1
    lo, hi = _x_window(den_p)
    for b in (rk_n_xy, rk_d_xy, *rho_common):
        blo, bhi = _x_window(b)
        if bhi >= blo:
            lo = min(lo, blo)
            hi = max(hi, bhi)
    if hi < lo:
        lo, hi = 0, 0
    return kd, lo - 1, hi + 1


# ── the homogeneous ℚ(q) kernel pick (mirror zeilberger._homogeneous_kernel) ──

def _homogeneous_kernel(rows: List[List[_Cq]], n_unknowns: int, a_block: int
                        ) -> Optional[Tuple[List[_Cq], List[_Cq]]]:
    """Find a nonzero kernel vector of the homogeneous ℚ(q) system ``rows·v = 0``
    whose ``a``-block (the first ``a_block`` unknowns) is NOT all zero — that is a
    genuine q-recurrence. Returns ``(a_coeffs, x_coeffs)`` as exact ``_Cq`` lists, or
    ``None`` when the only kernel vectors have a zero ``a``-block (no q-recurrence at
    this order). The elimination is the SAME exact-ℚ(q) Gauss-Jordan q-Gosper runs,
    over the shared ``_Cq`` field layer (the parametrization payoff) — here in the
    homogeneous (no-RHS) kernel form."""
    if not rows:
        return None
    # The homogeneous system has rhs ≡ 0, so the RREF + a free-column scan reads the
    # kernel directly (the same shape the ordinary zeilberger kernel pick uses).
    rref = _rref_homogeneous(rows, n_unknowns)
    pivots: List[int] = []
    pivot_row_of: Dict[int, List[_Cq]] = {}
    for row in rref:
        pc = None
        for j in range(n_unknowns):
            if not row[j].is_zero:
                pc = j
                break
        if pc is not None:
            pivots.append(pc)
            pivot_row_of[pc] = row
    free = [j for j in range(n_unknowns) if j not in pivots]
    if not free:
        return None
    for f in free:
        vec = [_Cq.zero()] * n_unknowns
        vec[f] = _Cq.one()
        for pc in pivots:
            row = pivot_row_of[pc]
            s = _Cq.zero()
            for g in free:
                if not row[g].is_zero:
                    s = s + row[g] * vec[g]
            vec[pc] = -s
        a_part = vec[:a_block]
        if any(not c.is_zero for c in a_part):
            return a_part, vec[a_block:]
    return None


def _rref_homogeneous(rows: List[List[_Cq]], n_cols: int) -> List[List[_Cq]]:
    """Exact-ℚ(q) Gauss-Jordan RREF of the homogeneous system (no RHS column). The
    SAME elimination :func:`q_gosper._rref_cq` runs, returned as a list-of-rows (the
    pivot read-off lives in :func:`_homogeneous_kernel`)."""
    m = [list(r) for r in rows]
    n_rows = len(m)
    pr = 0
    for col in range(n_cols):
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
                m[r] = [m[r][i] - f * m[pr][i] for i in range(n_cols)]
        pr += 1
        if pr >= n_rows:
            break
    return m[:pr]


# ── the C bridge wire form ─────────────────────────────────────────────────────

def _qb_pairs(b: QBiPoly):
    """A :class:`~srmech.amsc.qbipoly.QBiPoly` → the ``(y_xlow[], rows)`` bridge form
    the C peer consumes (the SAME per-Y-cell QPoly row form
    :func:`srmech.amsc.qbipoly._qb_pairs` emits)."""
    from .qbipoly import _qb_pairs as _f
    return _f(b)


def _qb_from_pairs(form) -> QBiPoly:
    """Rebuild a :class:`~srmech.amsc.qbipoly.QBiPoly` from the ``(y_xlow[], rows)``
    bridge form (from the C peer; each leaf already reduced)."""
    y_xlow, rows = form
    from .qpoly import _qp_from_pairs
    cells = [_qp_from_pairs((lo, run)) for lo, run in zip(y_xlow, rows)]
    return QBiPoly(cells)


def _qg_from_pairs(form) -> QPoly:
    """Rebuild a :class:`~srmech.amsc.qpoly.QPoly` (an ``a_j(X)`` recurrence
    coefficient) from the ``(x_low, rows)`` bridge form (from the C peer)."""
    from .qpoly import _qp_from_pairs
    return _qp_from_pairs(form)
