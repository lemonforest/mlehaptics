"""srmech.amsc.apagodu_zeilberger — the Apagodu–Zeilberger multivariate "sums of
sums" creative-telescoping recurrence-finder (the rc53 op that CLOSES the
multivariate F929 reduction row).

Where :func:`srmech.amsc.zeilberger.zeilberger` finds the linear recurrence of a
SINGLE definite sum ``f(n) = Σ_k F(n,k)``, the Apagodu–Zeilberger algorithm
(M. Apagodu & D. Zeilberger, "Multi-variable Zeilberger and Almkvist–Zeilberger
algorithms and the sharpening of Wilf–Zeilberger theory", Adv. Appl. Math. 37(2),
2006, 139–152; the multi-WZ method of H. Wilf & D. Zeilberger, "An algorithmic
proof theory for hypergeometric (ordinary and 'q') multisum/integral identities",
Invent. Math. 108(1), 1992, 575–633) handles a DEFINITE DOUBLE sum

    f(n) = Σ_{j,k} F(n,j,k)

of a proper hypergeometric term ``F(n,j,k)`` in the free variable ``n`` and TWO
summation variables ``j``, ``k`` — and produces the **linear recurrence with
polynomial coefficients**

    Σ_{i=0}^{L} a_i(n) · f(n+i) = 0

the minimal-order such recurrence, each ``a_i(n)`` an exact polynomial in
``ℚ[n]``.

Input — the **three term ratios** of ``F``, each a rational function of
``(n,j,k)``:

  * ``r_n(n,j,k) = F(n+1,j,k) / F(n,j,k)``   (the ``rn_num`` / ``rn_den`` operands)
  * ``r_j(n,j,k) = F(n,j+1,k) / F(n,j,k)``   (the ``rj_num`` / ``rj_den`` operands)
  * ``r_k(n,j,k) = F(n,j,k+1) / F(n,j,k)``   (the ``rk_num`` / ``rk_den`` operands)

each given as two *trivariate* exact-``ℚ[n,j,k]`` polynomials — a
:class:`~srmech.amsc.tripoly.TriPoly` (which this op exists FOR), or any value
:meth:`~srmech.amsc.tripoly.TriPoly._as_tripoly` coerces (a :class:`BiPoly` in
``(n,k)``, a :class:`~srmech.amsc.poly.Poly` in ``k``, a scalar). This MIRRORS the
``zeilberger`` two-ratio (``r_n`` / ``r_k``) encoding, extended to the third
direction (``r_j``).

Method — **creative telescoping with two certificates** (the rational-certificate
form), for ``L = 0, 1, 2, …, max_order``. The Apagodu–Zeilberger ansatz, divided
through by ``F(n,j,k)``, is

    Σ_{i=0}^{L} a_i(n)·ρ_i(n,j,k)
        = [ R_j(n,j+1,k)·r_j(n,j,k) − R_j(n,j,k) ]      (= Δ_j(R_j·F) / F)
        + [ R_k(n,j,k+1)·r_k(n,j,k) − R_k(n,j,k) ]      (= Δ_k(R_k·F) / F)

where ``ρ_i(n,j,k) = F(n+i,j,k)/F(n,j,k) = Π_{t<i} r_n(n+t,j,k)`` (so ``ρ_0 = 1``),
and ``R_j = x_j / D_P``, ``R_k = x_k / D_P`` are the two rational certificates over
the SHARED LHS denominator ``D_P(n,j,k) = Π_{i=0}^{L} ρ_den_i`` (the natural common
certificate support: the certificate poles are exactly the ``n``-shift poles the
ansatz LHS already carries). Multiply the whole identity through to a single common
denominator — a polynomial identity in ``ℚ[n,j,k]``, LINEAR in the unknown
``{a_i(n) coeffs} ∪ {x_j(n,j,k) coeffs} ∪ {x_k(n,j,k) coeffs}`` — and match every
``n^p·j^q·k^r`` monomial. That is one HOMOGENEOUS exact-``ℚ`` linear system (solved
with the exact Gauss-Jordan :class:`~srmech.amsc.qmat.QMat`). The first ``L`` with a
kernel vector whose ``a``-block is nonzero is the minimal recurrence; summing the
telescoping identity over all ``j,k`` (natural boundaries: ``R_j·F`` / ``R_k·F``
vanish at the summation limits) collapses the right-hand side and yields
``Σ_i a_i(n) f(n+i) = 0``.

The whole pipeline stays EXACT over ``ℚ`` — every polynomial is built on the
bigint :class:`~srmech.amsc.q.Q` / :class:`~srmech.amsc.poly.Poly` /
:class:`~srmech.amsc.zeilberger.BiPoly` / :class:`~srmech.amsc.tripoly.TriPoly`
carriers (no magnitude ceiling), every solve is exact Gauss-Jordan over ``ℚ``.
There is NO float anywhere; sign is the **Class-K** pin-slot via the ``Q``
sign-branch (never an ALU ``abs()``); no ``math`` module, no numpy.

C peer: ``srmech_apagodu_zeilberger`` (``c/src/srmech_apagodu_zeilberger.c``)
orchestrates the SAME existing C kernels — the ``srmech_tripoly_*`` /
``srmech_poly_*`` algebra (the trivariate handling rides ``srmech_tripoly_mul`` /
the n-shift dispersion) + ``srmech_qmat_rref`` (the parametrized exact-``ℚ`` solve)
— into one caller-arena, JPL-clean symbol that ACCELERATES the canonical low-order
case (order ≤ 1, the textbook double-sum identities). ``apagodu_zeilberger`` routes
through it when ``HAS_NATIVE``
(:func:`srmech.amsc._native.has_native_apagodu_zeilberger`) and the C reports a
positive (recurrence-found) result; a ``has=0`` C result is NOT trusted as a
definitive "no recurrence" (the C caps its ansatz order below an unbounded search),
so it falls through to the COMPLETE pure-Python body here — the full-coverage
decider AND the byte-identical parity oracle. A genuinely multivariate term whose
recurrence is order ≥ 2 (e.g. the Apéry-like ``Σ_{j,k} C(n,j)C(n,k)C(j+k,j)``) is
proved entirely on the pure path.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

from .poly import Poly
from .q import Q
from .tripoly import TriPoly

__all__ = ["apagodu_zeilberger"]

_Q_ZERO = Q(0, 1)
_Q_ONE = Q(1, 1)
_TP_ONE = TriPoly.one()

# How far above the structural certificate-degree base (``_ansatz_jk_base``) the
# per-order sweep reaches. The default is NARROW: a proper hypergeometric term's
# certificate degree is comparable to its inputs (the Apagodu–Zeilberger sharpened
# bound), and a wide sweep at a low order wastes enormous time on big high-degree
# systems that cannot yield a recurrence. A genuinely-2D term with a HIGH-degree
# cross-term certificate (the non-separable ``C(j+k,j)`` coupling) needs a wider
# sweep — set ``SRMECH_AZ_MAX_CERT_BUMP`` (the opt-in heavyweight path) to raise it.
try:
    _MAX_CERT_BUMP = max(1, int(os.environ.get("SRMECH_AZ_MAX_CERT_BUMP", "1")))
except (TypeError, ValueError):
    _MAX_CERT_BUMP = 1


def _native():
    """The native ``_native`` module IF the rc53 ``srmech_apagodu_zeilberger`` peer
    is present and bound, else ``None`` — so ``apagodu_zeilberger`` dispatches to C
    when available and falls cleanly to the pure-Python body (the complete
    alternative + the parity oracle) otherwise. Imported lazily to avoid a bootstrap
    cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    probe = getattr(nat, "has_native_apagodu_zeilberger", None)
    return nat if (probe is not None and probe()) else None


def _coerce_tri(value) -> TriPoly:
    """Coerce a term-ratio operand to a :class:`~srmech.amsc.tripoly.TriPoly`. A
    ``TriPoly`` passes through; a ``BiPoly`` in ``(n,k)`` / a ``Poly`` in ``k`` / an
    exact scalar / a coercible block sequence is lifted (the
    :meth:`~srmech.amsc.tripoly.TriPoly._as_tripoly` regime)."""
    if isinstance(value, TriPoly):
        return value
    lifted = TriPoly.zero()._as_tripoly(value)
    if lifted is None:
        raise TypeError(
            "apagodu_zeilberger: each term-ratio operand must be a TriPoly (or a "
            f"TriPoly-coercible value); got {value!r}")
    return lifted


# ── the public op ─────────────────────────────────────────────────────────────

def apagodu_zeilberger(rn_num, rn_den, rj_num, rj_den, rk_num, rk_den,
                       max_order: int = 4) -> Optional[Dict[str, object]]:
    """The Apagodu–Zeilberger creative-telescoping recurrence for the definite
    DOUBLE hypergeometric sum ``f(n) = Σ_{j,k} F(n,j,k)``.

    ``rn_num`` / ``rn_den`` are the numerator / denominator of the ``n``-term-ratio
    ``r_n(n,j,k) = F(n+1,j,k)/F(n,j,k)``; ``rj_num`` / ``rj_den`` the ``j``-ratio
    ``r_j = F(n,j+1,k)/F(n,j,k)``; ``rk_num`` / ``rk_den`` the ``k``-ratio
    ``r_k = F(n,j,k+1)/F(n,j,k)``. Each is a
    :class:`~srmech.amsc.tripoly.TriPoly` (exact-``ℚ[n,j,k]``), or any
    TriPoly-coercible value (a ``BiPoly`` in ``(n,k)``, a ``Poly`` in ``k``, a
    scalar).

    Returns the minimal-order recurrence ``{"order": L, "coeffs": [Poly_in_n, …],
    "certificate_j": TriPoly, "certificate_k": TriPoly}`` such that
    ``Σ_{i=0}^{L} coeffs[i](n)·f(n+i) = 0`` (``certificate_j`` / ``certificate_k``
    are the numerators ``x_j`` / ``x_k`` of the rational certificates
    ``R_j = x_j/D_P`` / ``R_k = x_k/D_P``), or ``None`` when no recurrence of order
    ≤ ``max_order`` exists.

    Exact over ``ℚ`` (bigint, no magnitude ceiling); no float, no ``abs()`` (the
    sign is the Class-K pin-slot), no ``math`` / numpy. See the module docstring for
    the two-certificate creative-telescoping pipeline. ``rn_den`` / ``rj_den`` /
    ``rk_den`` must be nonzero (a term ratio has a nonzero denominator) —
    ``ValueError`` otherwise."""
    rn_n = _coerce_tri(rn_num)
    rn_d = _coerce_tri(rn_den)
    rj_n = _coerce_tri(rj_num)
    rj_d = _coerce_tri(rj_den)
    rk_n = _coerce_tri(rk_num)
    rk_d = _coerce_tri(rk_den)
    if rn_d.is_zero or rj_d.is_zero or rk_d.is_zero:
        raise ValueError(
            "apagodu_zeilberger: the term-ratio denominators r_n den / r_j den / "
            "r_k den must be NONZERO trivariate polynomials")
    if not isinstance(max_order, int) or max_order < 0:
        raise ValueError("apagodu_zeilberger: max_order must be a non-negative int")

    nat = _native()
    if nat is not None:
        try:
            got = nat.apagodu_zeilberger_c(
                _tri_pairs(rn_n), _tri_pairs(rn_d), _tri_pairs(rj_n),
                _tri_pairs(rj_d), _tri_pairs(rk_n), _tri_pairs(rk_d), max_order)
            # The C peer ACCELERATES the positive (recurrence-found) case only: a
            # has=1 result is byte-identical to the pure path. A has=0 (the C found
            # nothing within its own order cap) is NOT trusted as a definitive "no
            # recurrence" — the C caps its ansatz order below an unbounded search —
            # so it falls through to the complete pure-Python path (the parity
            # oracle AND the full-coverage decider).
            if got is not None:
                has, order, coeff_pairs, cj_blocks, ck_blocks = got
                if has:
                    coeffs = [Poly.from_coeffs([Q(a, b) for a, b in cp])
                              for cp in coeff_pairs]
                    cert_j = _tri_from_pairs(cj_blocks)
                    cert_k = _tri_from_pairs(ck_blocks)
                    return {"order": order, "coeffs": coeffs,
                            "certificate_j": cert_j, "certificate_k": cert_k}
        except (RuntimeError, OverflowError, ValueError):
            pass                                  # fall to the pure path

    return _apagodu_pure(rn_n, rn_d, rj_n, rj_d, rk_n, rk_d, max_order)


# ── pure-Python AZ (the COMPLETE alternative + the parity oracle) ──────────────

def _apagodu_pure(rn_n: TriPoly, rn_d: TriPoly, rj_n: TriPoly, rj_d: TriPoly,
                  rk_n: TriPoly, rk_d: TriPoly,
                  max_order: int) -> Optional[Dict[str, object]]:
    """The exact-ℚ pure-Python two-certificate creative-telescoping pipeline. Tries
    ansatz orders ``L = 0..max_order``, and at each order an increasing certificate
    degree bound; the first nonzero solution is the minimal recurrence."""
    for order in range(max_order + 1):
        got = _try_order(rn_n, rn_d, rj_n, rj_d, rk_n, rk_d, order)
        if got is not None:
            return got
    return None


def _rho(rn_n: TriPoly, rn_d: TriPoly, i: int) -> Tuple[TriPoly, TriPoly]:
    """``ρ_i(n,j,k) = F(n+i,j,k)/F(n,j,k) = Π_{t=0}^{i-1} r_n(n+t,j,k)`` as a
    ``(num, den)`` pair of :class:`~srmech.amsc.tripoly.TriPoly`. ``ρ_0 = 1``."""
    num = _TP_ONE
    den = _TP_ONE
    for t in range(i):
        num = num * rn_n.shift_n(t)
        den = den * rn_d.shift_n(t)
    return num, den


def _try_order(rn_n, rn_d, rj_n, rj_d, rk_n, rk_d, order):
    """Attempt the order-``order`` ansatz over a SWEEP of certificate degree bounds
    (the Apagodu–Zeilberger sharpened-degree search). The recurrence-coefficient
    n-degree and the certificate (n,j,k)-degree bounds are read from the input term
    degrees + the order; we sweep upward until the homogeneous system admits an
    a-nonzero kernel (or the bound ceiling is reached → no recurrence at this
    order)."""
    rhos = [_rho(rn_n, rn_d, i) for i in range(order + 1)]
    # D_P = the LCM of the ρ_den_i = ρ_den_order (each ρ_den_i divides the next by
    # construction ρ_den_{i+1} = ρ_den_i · r_n den(n+i)), NOT the product — the
    # product over-counts the shared factors and inflates the certificate degree
    # (the missed-fiber red flag: a swelling intermediate is a re-fibration, not a
    # bigger dense system). With the LCM support the certificate stays low-degree.
    den_p = rhos[order][1]

    n_deg = _ansatz_n_degree(rhos, den_p, rj_n, rj_d, rk_n, rk_d, order)
    jk_base = _ansatz_jk_base(rhos, den_p, rj_n, rj_d, rk_n, rk_d)
    # sweep the certificate (n,j,k) degree bound upward by a SMALL amount; a too-small
    # bound yields no kernel and we advance, a sufficient one yields the recurrence.
    # The sweep is kept narrow: the certificate degree of a proper hypergeometric term
    # is comparable to the input structure (the Apagodu–Zeilberger sharpened bound),
    # and a WIDE sweep at a low order wastes huge time on big high-degree systems that
    # cannot yield a recurrence anyway. A genuinely-2D term whose certificate carries
    # high-degree j·k cross-terms (the non-separable C(j+k,j) coupling) raises
    # ``max_cert_bump`` — but that is the opt-in heavyweight path; the default narrow
    # sweep keeps the common (iterable / separable) double sums fast. Each solve rides
    # the bounded-memory CRT RREF (rref_crt) for the large systems.
    for bump in range(0, _MAX_CERT_BUMP + 1):
        jk_deg = jk_base + bump
        got = _solve_parametrized(rn_d, rhos, den_p, rj_n, rj_d, rk_n, rk_d, order,
                                  n_deg, jk_deg)
        if got is not None:
            return got
    return None


def _solve_parametrized(rn_d, rhos, den_p, rj_n, rj_d, rk_n, rk_d, order,
                        n_deg, jk_deg):
    """Build + solve the homogeneous exact-ℚ linear system for the order-``order``,
    certificate-degree-``jk_deg`` two-certificate ansatz. A nonzero kernel vector
    with a nonzero ``a``-block yields the recurrence + the two certificate
    numerators ``x_j`` / ``x_k`` (the rationals ``R_j = x_j/D_P`` / ``R_k =
    x_k/D_P``)."""
    from .qmat import QMat

    dp_j1 = den_p.shift_j(1)                       # D_P(n, j+1, k)
    dp_k1 = den_p.shift_k(1)                       # D_P(n, j, k+1)
    # The full common denominator the cleared identity rides:
    #   Dfull = D_P * D_P(j+1) * D_P(k+1) * rj_den * rk_den
    # Every contribution below is a TriPoly numerator over Dfull (its cofactor =
    # Dfull / that piece's own denominator, a known product).

    # a_i contribution: a_i(n)·ρ_i over Dfull. cofactor = Dfull / ρ_den_i
    #   = (D_P / ρ_den_i) · D_P(j+1) · D_P(k+1) · rj_den · rk_den, and since
    #   D_P = ρ_den_order, D_P / ρ_den_i = Π_{i≤t<order} r_n den(n+t).
    rj_d_t, rk_d_t = rj_d, rk_d

    def _dp_over_rho_den(i):
        p = _TP_ONE
        for t in range(i, order):
            p = p * rn_d.shift_n(t)
        return p

    n_a = order + 1
    jk_mons = _jk_monomials(jk_deg)
    n_x = len(jk_mons)
    a_block = n_a * (n_deg + 1)
    x_block = n_x
    n_unknowns = a_block + 2 * x_block

    rows: Dict[Tuple[int, int, int], List[Q]] = {}

    def _add_tri(contrib: TriPoly, col: int, sign: int) -> None:
        for dj, bib in enumerate(contrib.blocks):
            for dk, kp in enumerate(bib.terms):
                for dn, q in enumerate(kp.coeffs):
                    if q == 0:
                        continue
                    key = (dn, dj, dk)
                    row = rows.get(key)
                    if row is None:
                        row = [_Q_ZERO] * n_unknowns
                        rows[key] = row
                    row[col] = row[col] + (q if sign > 0 else -q)

    # a_i columns (LHS, positive)
    lhs_tail = dp_j1 * dp_k1 * rj_d_t * rk_d_t
    for i in range(order + 1):
        cof = _dp_over_rho_den(i) * lhs_tail
        base = rhos[i][0] * cof
        for p in range(n_deg + 1):
            col = i * (n_deg + 1) + p
            _add_tri(base.scale_n(Poly.monomial(p)), col, +1)

    # x_j columns: RHS_j = x_j(j+1)/D_P(j+1)·r_j − x_j/D_P, subtracted from the LHS.
    #   term1 cofactor over Dfull: Dfull / (D_P(j+1)·rj_den) = D_P·D_P(k+1)·rk_den
    #   term2 cofactor over Dfull: Dfull / D_P              = D_P(j+1)·D_P(k+1)·rj_den·rk_den
    cof_j1 = den_p * dp_k1 * rk_d_t
    cof_j2 = dp_j1 * dp_k1 * rj_d_t * rk_d_t
    for idx, (dn, dj, dk) in enumerate(jk_mons):
        col = a_block + idx
        mono = TriPoly.monomial(dn, dj, dk)
        _add_tri(mono.shift_j(1) * rj_n * cof_j1, col, -1)
        _add_tri(mono * cof_j2, col, +1)

    # x_k columns: RHS_k = x_k(k+1)/D_P(k+1)·r_k − x_k/D_P.
    cof_k1 = den_p * dp_j1 * rj_d_t
    cof_k2 = dp_j1 * dp_k1 * rj_d_t * rk_d_t
    for idx, (dn, dj, dk) in enumerate(jk_mons):
        col = a_block + x_block + idx
        mono = TriPoly.monomial(dn, dj, dk)
        _add_tri(mono.shift_k(1) * rk_n * cof_k1, col, -1)
        _add_tri(mono * cof_k2, col, +1)

    rowlist = [rows[key] for key in sorted(rows)]
    if not rowlist:
        return None
    kernel = _homogeneous_kernel(QMat, rowlist, n_unknowns, a_block)
    if kernel is None:
        return None
    a_coeffs, xj_coeffs, xk_coeffs = kernel
    coeffs = [Poly.from_coeffs(a_coeffs[i * (n_deg + 1):(i + 1) * (n_deg + 1)])
              for i in range(n_a)]
    if all(c.is_zero for c in coeffs):
        return None
    cert_j = _x_to_tripoly(xj_coeffs, jk_mons)
    cert_k = _x_to_tripoly(xk_coeffs, jk_mons)
    return {"order": order, "coeffs": coeffs,
            "certificate_j": cert_j, "certificate_k": cert_k}


def _jk_monomials(jk_deg: int) -> List[Tuple[int, int, int]]:
    """The ascending ``(dn, dj, dk)`` exponent grid the certificate numerator
    ``x(n,j,k)`` ranges over — each of ``n`` / ``j`` / ``k`` degree ≤ ``jk_deg``.
    Ordered ``n``-major then ``j`` then ``k`` (the column layout the kernel reads)."""
    return [(dn, dj, dk) for dn in range(jk_deg + 1)
            for dj in range(jk_deg + 1) for dk in range(jk_deg + 1)]


def _x_to_tripoly(x_coeffs: List[Q], jk_mons: List[Tuple[int, int, int]]) -> TriPoly:
    """Pack a flat certificate-numerator coefficient vector (one ``Q`` per
    ``jk_mons`` exponent) into a :class:`~srmech.amsc.tripoly.TriPoly`."""
    terms = {}
    for q, (dn, dj, dk) in zip(x_coeffs, jk_mons):
        if q != 0:
            terms[(dn, dj, dk)] = q
    if not terms:
        return TriPoly.zero()
    return TriPoly.from_dict(terms)


# ── degree bounds ──────────────────────────────────────────────────────────────

def _tri_n_degree(t: TriPoly) -> int:
    """The max ``n``-degree across all ``(j,k)`` coefficients (``-1`` for zero)."""
    return t.n_degree


def _ansatz_n_degree(rhos, den_p, rj_n, rj_d, rk_n, rk_d, order: int) -> int:
    """A degree bound in ``n`` for the unknown ``a_i(n)`` — the max ``n``-degree
    across the assembled-identity inputs, plus one. A too-small bound at a given
    order/degree simply yields no kernel and the search advances; the C peer mirrors
    this bound exactly for parity."""
    d = 1
    for t in (den_p, rj_n, rj_d, rk_n, rk_d):
        nd = _tri_n_degree(t)
        if nd > d:
            d = nd
    for num, den in rhos:
        for t in (num, den):
            nd = _tri_n_degree(t)
            if nd > d:
                d = nd
    return d + 1


def _ansatz_jk_base(rhos, den_p, rj_n, rj_d, rk_n, rk_d) -> int:
    """The base ``(n,j,k)`` degree bound for the certificate numerators — the max
    per-variable degree appearing across the input term ratios + ``D_P``. The
    :func:`_try_order` sweep bumps this upward until a kernel appears."""
    d = 1
    for t in (den_p, rj_n, rj_d, rk_n, rk_d):
        d = max(d, t.n_degree, t.j_degree, t.k_degree)
    for num, den in rhos:
        d = max(d, num.n_degree, num.j_degree, num.k_degree,
                den.n_degree, den.j_degree, den.k_degree)
    return d


# ── the homogeneous kernel (mirror zeilberger._homogeneous_kernel) ─────────────

_CRT_KERNEL_CELL_THRESHOLD: int = 4096


def _kernel_rref(QMat, rows):
    """The exact-ℚ RREF of the homogeneous Apagodu–Zeilberger system, byte-identical
    whichever path runs. Auto-by-size: a large system (cell count past the threshold
    — the order-≥2 double-sum matrices that hit the dense Hadamard-envelope arena)
    reduces through the bounded-memory :meth:`~srmech.amsc.qmat.QMat.rref_crt` (CRT
    re-fibration); a tiny system stays on the faster dense
    :meth:`~srmech.amsc.qmat.QMat.rref`. Returns the RREF as a list-of-rows of
    ``Q``."""
    m = QMat.from_rows([list(r) for r in rows])
    use_crt = m.n_rows * m.n_cols > _CRT_KERNEL_CELL_THRESHOLD
    reduced = m.rref_crt() if use_crt else m.rref()
    return reduced.to_lists()


def _homogeneous_kernel(QMat, rows, n_unknowns, a_block):
    """Find a nonzero kernel vector of ``rows·v = 0`` whose ``a``-block (the first
    ``a_block`` unknowns) is NOT all zero — a genuine recurrence (a zero-``a``-block
    kernel is a spurious certificate-only solution). Returns ``(a_coeffs,
    xj_coeffs, xk_coeffs)`` as exact ``Q`` lists, or ``None`` when the only kernel
    vectors have a zero ``a``-block (no recurrence at this order/degree). The
    ``x``-block splits evenly between the two certificates."""
    if not rows:
        return None
    rref = _kernel_rref(QMat, rows)
    pivots: List[int] = []
    pivot_row_of: Dict[int, List[Q]] = {}
    for row in rref:
        pc = None
        for j in range(n_unknowns):
            if row[j] != 0:
                pc = j
                break
        if pc is not None:
            pivots.append(pc)
            pivot_row_of[pc] = row
    free = [j for j in range(n_unknowns) if j not in pivots]
    if not free:
        return None
    x_block = (n_unknowns - a_block) // 2
    for f in free:
        vec = [_Q_ZERO] * n_unknowns
        vec[f] = _Q_ONE
        for pc in pivots:
            row = pivot_row_of[pc]
            s = _Q_ZERO
            for g in free:
                if row[g] != 0:
                    s = s + row[g] * vec[g]
            vec[pc] = -s
        a_part = vec[:a_block]
        if any(q != 0 for q in a_part):
            return (a_part,
                    vec[a_block:a_block + x_block],
                    vec[a_block + x_block:])
    return None


# ── the wire form for the C bridge (mirror tripoly._tri_pairs) ─────────────────

def _tri_pairs(t: TriPoly) -> List[List[List[Tuple[int, int]]]]:
    """A :class:`~srmech.amsc.tripoly.TriPoly` → the nested
    ``[[[(num, den), …]_n]_k]_j`` bridge form (j-major, then k, then ascending-n
    ``Poly`` coefficients) the C peer consumes — the SAME form
    :func:`srmech.amsc.tripoly._tri_pairs` emits."""
    out: List[List[List[Tuple[int, int]]]] = []
    for bib in t.blocks:
        kgrid: List[List[Tuple[int, int]]] = []
        for kp in bib.terms:
            kgrid.append([(c.numerator, c.denominator) for c in kp.coeffs])
        out.append(kgrid)
    return out


def _tri_from_pairs(blocks) -> TriPoly:
    """Rebuild a :class:`~srmech.amsc.tripoly.TriPoly` from the nested
    ``[[[(num, den), …]_n]_k]_j`` bridge form (from the C peer; each leaf already
    reduced) — the SAME form :func:`srmech.amsc.tripoly._tri_from_pairs` consumes."""
    from .tripoly import _tri_from_pairs as _tfp
    return _tfp(blocks)
