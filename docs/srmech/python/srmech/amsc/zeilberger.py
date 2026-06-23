"""srmech.amsc.zeilberger — Zeilberger's creative telescoping (the SECOND public
op of the §76 "telescope" Σ-row closed-form prover, F929).

Where :func:`srmech.amsc.gosper.gosper` decides INDEFINITE summation of a single
hypergeometric term in ``k``, Zeilberger's algorithm (D. Zeilberger, "The method
of creative telescoping", J. Symbolic Computation 11(3):195–204, 1991; "A fast
algorithm for proving terminating hypergeometric identities", Discrete Math.
80(2):207–211, 1990; the canonical modern reference is Petkovšek, Wilf &
Zeilberger, *A = B*, A K Peters 1996, ch. 6) handles a DEFINITE sum
``f(n) = Σ_k F(n,k)`` of a *proper hypergeometric term* ``F(n,k)`` and produces
the **linear recurrence with polynomial coefficients**

    Σ_{j=0}^{L} a_j(n) · f(n+j) = 0

that ``f`` satisfies — the minimal-order such recurrence, with each ``a_j(n)`` an
exact polynomial in ``ℚ[n]``.

Input — the **two term ratios** of ``F``, each a rational function of ``(n,k)``:

  * ``r_n(n,k) = F(n+1,k) / F(n,k)``   (the ``rn_num`` / ``rn_den`` operands)
  * ``r_k(n,k) = F(n,k+1) / F(n,k)``   (the ``rk_num`` / ``rk_den`` operands)

each given as two *bivariate* exact-``ℚ[n,k]`` polynomials — see :class:`BiPoly`
below (a polynomial in ``k`` whose coefficients are :class:`~srmech.amsc.poly.Poly`
in ``n``). A plain :class:`~srmech.amsc.poly.Poly` (a polynomial in ``k`` only, no
``n``) or an ascending-degree coefficient sequence is coerced.

Method — **creative telescoping** (the rational-certificate form), for
``L = 0, 1, 2, …, max_order``:

  1. Form the ansatz term ``T(n,k) = Σ_{j=0}^{L} a_j(n)·F(n+j,k)``, where
     ``F(n+j,k)/F(n,k) = ∏_{i=0}^{j-1} r_n(n+i,k)`` is rational in ``(n,k)``, so
     ``T = F(n,k)·P(n,k)`` with ``P = Σ_j a_j(n)·ρ_j(n,k)`` a rational function of
     ``k`` (coefficients in ``ℚ[n]`` — the unknown polynomials ``a_j(n)``).
  2. Apply **Gosper in k** to ``T``: its k-term-ratio is ``r_k(n,k)·P(n,k+1)/
     P(n,k)``. Running the Gosper–Petkovšek machinery with the ``a_j(n)`` carried
     as additional unknowns makes the Gosper equation LINEAR in
     ``{a_j(n) coeffs} ∪ {certificate-poly coeffs}`` — one exact-``ℚ`` linear
     system (solved with the exact Gauss-Jordan :class:`~srmech.amsc.qmat.QMat`).
  3. The first ``L`` with a nonzero solution gives the recurrence coefficients
     ``a_j(n)`` and the rational certificate ``R(n,k)`` (the Gosper certificate of
     ``T``): ``Σ_j a_j(n) F(n+j,k) = G(n,k+1) − G(n,k)`` with ``G = R·F``. Summing
     over ``k`` (natural boundary: ``G`` vanishes at the ``k``-limits) gives
     ``Σ_j a_j(n) f(n+j) = 0``.

The whole pipeline stays EXACT over ``ℚ`` — every polynomial is built on the
bigint :class:`~srmech.amsc.q.Q` / :class:`~srmech.amsc.poly.Poly` carriers (no
magnitude ceiling), every solve is exact Gauss-Jordan over ``ℚ``. There is NO
float anywhere; sign is the **Class-K** pin-slot via the ``Q`` sign-branch (never
an ALU ``abs()``); no ``math`` module, no numpy.

C peer: ``srmech_zeilberger`` (``c/src/srmech_zeilberger.c``) orchestrates the
SAME existing C kernels — the ``srmech_poly_*`` algebra (the bivariate handling
rides ``srmech_poly_mul`` / ``srmech_poly_add`` / ``srmech_poly_shift`` over ``n``)
+ ``srmech_qmat_rref`` (the parametrized exact-``ℚ`` solve) — into one
caller-arena, JPL-clean symbol. ``zeilberger`` routes through it when
``HAS_NATIVE`` (:func:`srmech.amsc._native.has_native_zeilberger`); the
pure-Python body here is the COMPLETE alternative (and the byte-identical parity
oracle): both emit the same recurrence + certificate at any magnitude.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from .poly import Poly
from .q import Q

__all__ = ["zeilberger", "BiPoly"]

_Q_ZERO = Q(0, 1)
_Q_ONE = Q(1, 1)


def _native():
    """The native ``_native`` module IF the rc42 ``srmech_zeilberger`` peer is
    present and bound, else ``None`` — so ``zeilberger`` dispatches to C when
    available and falls cleanly to the pure-Python body (the complete alternative
    + the parity oracle) otherwise. Imported lazily to avoid a bootstrap cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    probe = getattr(nat, "has_native_zeilberger", None)
    return nat if (probe is not None and probe()) else None


# ── BiPoly: an exact-ℚ bivariate polynomial in (n, k) ─────────────────────────
#
# Representation: a list of Poly-in-n, indexed by k-degree. ``terms[d]`` is the
# coefficient of ``k**d`` and is itself a Poly over ℚ[n]. Trailing zero Poly
# coefficients are trimmed, so the zero BiPoly is the empty list and the
# "k-degree" is ``len(terms) - 1``. Everything is exact Q (no float, no abs()).


class BiPoly:
    """An exact-ℚ bivariate polynomial in ``(n, k)`` — a polynomial in ``k`` whose
    coefficients are :class:`~srmech.amsc.poly.Poly` in ``n``. Immutable, trimmed
    of trailing-zero ``k``-coefficients (the zero polynomial is the empty term
    list). The exact substrate the Zeilberger term-ratio ``r_n(n,k)`` / ``r_k(n,k)``
    operands ride. No float, no ``abs()`` (Class-K sign), no ``math`` / numpy."""

    __slots__ = ("_t",)

    def __init__(self, terms: Sequence[Poly] = ()) -> None:
        cells: List[Poly] = []
        for c in terms:
            cells.append(c if isinstance(c, Poly) else Poly.from_coeffs(c))
        self._t = _bi_trim(cells)

    # ── construction ───────────────────────────────────────────────────────
    @classmethod
    def _wrap(cls, trimmed: Tuple[Poly, ...]) -> "BiPoly":
        b = cls.__new__(cls)
        b._t = trimmed
        return b

    @classmethod
    def zero(cls) -> "BiPoly":
        """The zero bivariate polynomial."""
        return cls._wrap(())

    @classmethod
    def one(cls) -> "BiPoly":
        """The constant ``1``."""
        return cls._wrap((Poly.one(),))

    @classmethod
    def from_k_poly(cls, p: Poly) -> "BiPoly":
        """A polynomial in ``k`` ALONE (no ``n``) → a ``BiPoly`` (each ``k``-coeff
        is the constant Poly-in-n of that ``Q``)."""
        return cls._wrap(tuple(Poly.from_coeffs([c]) for c in p.coeffs))

    @classmethod
    def from_n_poly(cls, p: Poly) -> "BiPoly":
        """A polynomial in ``n`` ALONE (no ``k``) → the constant-in-``k`` ``BiPoly``."""
        return cls._wrap(() if p.is_zero else (p,))

    @classmethod
    def coerce(cls, value) -> "BiPoly":
        """Coerce a ``zeilberger`` term-ratio operand to a ``BiPoly``. A ``BiPoly``
        passes through; a :class:`~srmech.amsc.poly.Poly` is read as a polynomial
        in ``k`` (the no-``n`` case — the common acceptance form); an
        ascending-``k``-degree sequence whose entries are themselves
        ``Poly``-in-``n`` (or coefficient sequences) is wrapped term-by-term."""
        if isinstance(value, BiPoly):
            return value
        if isinstance(value, Poly):
            return cls.from_k_poly(value)
        # a sequence of k-degree coefficients (each a Poly-in-n or coeff seq).
        return cls([c if isinstance(c, Poly) else Poly.from_coeffs(c) for c in value])

    # ── accessors ──────────────────────────────────────────────────────────
    @property
    def terms(self) -> Tuple[Poly, ...]:
        """The trimmed ``k``-ascending tuple of Poly-in-n coefficients."""
        return self._t

    @property
    def k_degree(self) -> int:
        """The degree in ``k`` (``-1`` for the zero polynomial)."""
        return len(self._t) - 1

    @property
    def is_zero(self) -> bool:
        return len(self._t) == 0

    def coeff(self, d: int) -> Poly:
        """The Poly-in-n coefficient of ``k**d`` (zero Poly past the ``k``-degree)."""
        return self._t[d] if 0 <= d < len(self._t) else Poly.zero()

    def __eq__(self, other) -> bool:
        if not isinstance(other, BiPoly):
            try:
                other = BiPoly.coerce(other)
            except (TypeError, ValueError):
                return NotImplemented
        return self._t == other._t

    def __hash__(self) -> int:
        return hash(self._t)

    def __repr__(self) -> str:
        return f"BiPoly(k_degree={self.k_degree}, exact-ℚ[n,k])"

    # ── exact arithmetic over ℚ[n,k] (Class-K sign via Poly/Q) ──────────────
    def __add__(self, other: "BiPoly") -> "BiPoly":
        o = BiPoly.coerce(other)
        m = max(len(self._t), len(o._t))
        out = [self.coeff(d) + o.coeff(d) for d in range(m)]
        return BiPoly._wrap(_bi_trim(out))

    def __sub__(self, other: "BiPoly") -> "BiPoly":
        o = BiPoly.coerce(other)
        m = max(len(self._t), len(o._t))
        out = [self.coeff(d) - o.coeff(d) for d in range(m)]
        return BiPoly._wrap(_bi_trim(out))

    def __neg__(self) -> "BiPoly":
        return BiPoly._wrap(tuple(-c for c in self._t))

    def __mul__(self, other: "BiPoly") -> "BiPoly":
        o = BiPoly.coerce(other)
        if self.is_zero or o.is_zero:
            return BiPoly._wrap(())
        out = [Poly.zero()] * (len(self._t) + len(o._t) - 1)
        for i, ci in enumerate(self._t):
            if ci.is_zero:
                continue
            for j, cj in enumerate(o._t):
                if cj.is_zero:
                    continue
                out[i + j] = out[i + j] + ci * cj          # Poly-in-n product
        return BiPoly._wrap(_bi_trim(out))

    def scale_n(self, p: Poly) -> "BiPoly":
        """Multiply every ``k``-coefficient by a Poly-in-n ``p`` (exact)."""
        if p.is_zero or self.is_zero:
            return BiPoly._wrap(())
        return BiPoly._wrap(_bi_trim([c * p for c in self._t]))

    def shift_n(self, h: int) -> "BiPoly":
        """``BiPoly(n, k) → BiPoly(n+h, k)`` — shift every Poly-in-n coefficient by
        ``+h`` (the :meth:`srmech.amsc.poly.Poly.shift` dispersion over ``n``)."""
        return BiPoly._wrap(_bi_trim([c.shift(Q(h, 1)) for c in self._t]))

    def shift_k(self, h: int) -> "BiPoly":
        """``BiPoly(n, k) → BiPoly(n, k+h)`` — substitute ``k → k+h`` (each ``k``
        monomial expands binomially over the Poly-in-n coefficients). Exact."""
        if self.is_zero:
            return BiPoly._wrap(())
        # synthetic Horner over the linear (k + h): acc = acc*(k+h) + coeff.
        acc = BiPoly._wrap(())
        kh = BiPoly._wrap((Poly.from_coeffs([h]), Poly.one()))   # k + h
        for c in reversed(self._t):
            acc = acc * kh + BiPoly.from_n_poly(c)
        return acc


def _bi_trim(cells: Sequence[Poly]) -> Tuple[Poly, ...]:
    """Drop trailing-zero (high-``k``-degree) Poly coefficients → canonical form."""
    n = len(cells)
    while n > 0 and cells[n - 1].is_zero:
        n -= 1
    return tuple(cells[:n])


def _bi_pairs(b: BiPoly) -> List[List[Tuple[int, int]]]:
    """A ``BiPoly`` → a k-ascending list of (per-k-coefficient) ascending-n
    ``(num, den)`` int-pair lists — the flat bridge form for the C peer."""
    return [[(c.numerator, c.denominator) for c in kp.coeffs] for kp in b.terms]


# ── the public op ─────────────────────────────────────────────────────────────

def zeilberger(rn_num, rn_den, rk_num, rk_den, max_order: int = 6
               ) -> Optional[Dict[str, object]]:
    """Zeilberger's creative-telescoping recurrence for the definite hypergeometric
    sum ``f(n) = Σ_k F(n,k)``.

    ``rn_num`` / ``rn_den`` are the numerator / denominator of the ``n``-term-ratio
    ``r_n(n,k) = F(n+1,k)/F(n,k)``; ``rk_num`` / ``rk_den`` likewise for the
    ``k``-term-ratio ``r_k(n,k) = F(n,k+1)/F(n,k)``. Each is a :class:`BiPoly`
    (exact-``ℚ[n,k]``), or a :class:`~srmech.amsc.poly.Poly` (read as a polynomial
    in ``k`` alone), or an ascending-``k``-degree coefficient sequence.

    Returns the minimal-order recurrence ``{"order": L, "coeffs": [Poly_in_n, …],
    "certificate": BiPoly}`` such that ``Σ_{j=0}^{L} coeffs[j](n)·f(n+j) = 0``, or
    ``None`` when no such recurrence of order ≤ ``max_order`` exists.

    Exact over ``ℚ`` (bigint, no magnitude ceiling); no float, no ``abs()`` (the
    sign is the Class-K pin-slot), no ``math`` / numpy. See the module docstring
    for the creative-telescoping pipeline. ``rn_den`` / ``rk_den`` must be nonzero
    (a term ratio has a nonzero denominator) — ``ValueError`` otherwise."""
    rn_n = BiPoly.coerce(rn_num)
    rn_d = BiPoly.coerce(rn_den)
    rk_n = BiPoly.coerce(rk_num)
    rk_d = BiPoly.coerce(rk_den)
    if rn_d.is_zero or rk_d.is_zero:
        raise ValueError(
            "zeilberger: the term-ratio denominators r_n den / r_k den must be "
            "NONZERO bivariate polynomials")
    if not isinstance(max_order, int) or max_order < 0:
        raise ValueError("zeilberger: max_order must be a non-negative int")

    nat = _native()
    if nat is not None:
        try:
            got = nat.zeilberger_c(_bi_pairs(rn_n), _bi_pairs(rn_d),
                                   _bi_pairs(rk_n), _bi_pairs(rk_d), max_order)
            # The C peer accelerates the POSITIVE (recurrence-found) case only: a
            # has=1 result is byte-identical to the pure path. A has=0 (the C found
            # nothing within its own order cap) is NOT trusted as a definitive
            # "no recurrence" — the C caps its ansatz order below an unbounded
            # search — so it falls through to the complete pure-Python path, which
            # is the parity oracle AND the full-coverage decider.
            if got is not None:
                has, order, coeff_pairs, cert_pairs = got
                if has:
                    coeffs = [Poly.from_coeffs([Q(a, b) for a, b in cp])
                              for cp in coeff_pairs]
                    cert = BiPoly([Poly.from_coeffs([Q(a, b) for a, b in kp])
                                   for kp in cert_pairs])
                    return {"order": order, "coeffs": coeffs, "certificate": cert}
        except (RuntimeError, OverflowError, ValueError):
            pass                                  # fall to the pure path

    return _zeilberger_pure(rn_n, rn_d, rk_n, rk_d, max_order)


# ── pure-Python Zeilberger (the COMPLETE alternative + the parity oracle) ──────

def _zeilberger_pure(rn_n: BiPoly, rn_d: BiPoly, rk_n: BiPoly, rk_d: BiPoly,
                     max_order: int) -> Optional[Dict[str, object]]:
    """The exact-ℚ pure-Python creative-telescoping pipeline. Tries ansatz orders
    ``L = 0..max_order``; the first nonzero solution is the minimal recurrence."""
    for order in range(max_order + 1):
        got = _try_order(rn_n, rn_d, rk_n, rk_d, order)
        if got is not None:
            return got
    return None


def _rho(rn_n: BiPoly, rn_d: BiPoly, j: int) -> Tuple[BiPoly, BiPoly]:
    """``ρ_j(n,k) = F(n+j,k)/F(n,k) = ∏_{i=0}^{j-1} r_n(n+i,k)`` as a reduced-by-
    construction rational ``(num, den)`` pair of :class:`BiPoly`. ``ρ_0 = 1``."""
    num = BiPoly.one()
    den = BiPoly.one()
    for i in range(j):
        num = num * rn_n.shift_n(i)
        den = den * rn_d.shift_n(i)
    return num, den


def _try_order(rn_n: BiPoly, rn_d: BiPoly, rk_n: BiPoly, rk_d: BiPoly,
               order: int) -> Optional[Dict[str, object]]:
    """Attempt the order-``order`` ansatz. Build the parametrized Gosper-in-k
    linear system over ℚ in the unknowns ``{a_j(n) coeffs} ∪ {x(n,k) coeffs}`` and
    solve it; on a nonzero solution return the recurrence + certificate."""
    # ρ_j rationals; the common k-denominator D(n,k) = lcm-free product of all dens.
    rhos = [_rho(rn_n, rn_d, j) for j in range(order + 1)]
    # P(n,k) = Σ_j a_j(n) ρ_j = N_P / D_P with D_P = Π_j den_j (a common den).
    den_p = BiPoly.one()
    for _, dj in rhos:
        den_p = den_p * dj
    # numerators of each ρ_j over the common den_p: num_j * (D_P / den_j).
    rho_over_common: List[BiPoly] = []
    for nj, dj in rhos:
        cofactor = _bi_exact_div(den_p, dj)
        rho_over_common.append(nj * cofactor)

    # The Gosper-in-k term ratio of T = F·P is
    #   ρ_T(k) = r_k(n,k) · P(n,k+1)/P(n,k)
    #          = (rk_n · N_P(k+1) · D_P(k)) / (rk_d · N_P(k) · D_P(k+1)).
    # Apply Gosper's equation: find x(n,k) (rational, written over D_P) with
    #   A(k)·x(k+1) − B(k−1)·x(k) = C(k),  the undetermined-coefficient system,
    # all coefficients LINEAR in the unknown a_j(n) (they enter N_P linearly).
    #
    # We carry the a_j(n) as a coefficient VECTOR. Each P-quantity is therefore an
    # n,k polynomial that is LINEAR in the unknowns: N_P = Σ_j a_j(n)·rho_over_common[j].
    # Both sides of the Gosper relation are linear in {a_j}; matching (n,k)-powers
    # gives a homogeneous ℚ-linear system. A nonzero kernel vector = a recurrence.
    return _solve_parametrized(rho_over_common, den_p, rk_n, rk_d, order)


def _bi_exact_div(a: BiPoly, b: BiPoly) -> BiPoly:
    """Exact division ``a / b`` of bivariate polynomials when ``b`` divides ``a``
    (used for the ``D_P / den_j`` cofactors — exact by construction since ``den_j``
    is a factor of the product ``D_P``). Performed as a multivariate long division
    in ``k`` with exact Poly-in-n coefficient arithmetic; raises if it does not
    divide cleanly (a guard, never hit on the cofactor inputs)."""
    if b.is_zero:
        raise ZeroDivisionError("BiPoly exact-div by zero")
    if a.is_zero:
        return BiPoly._wrap(())
    rem = list(a.terms)
    b_terms = b.terms
    bdeg = b.k_degree
    blead = b_terms[bdeg]                               # leading Poly-in-n of b
    quo = [Poly.zero()] * (max(len(rem) - len(b_terms), -1) + 1) if len(rem) >= len(b_terms) else []
    while len(rem) - 1 >= bdeg and _bi_trim(rem):
        rdeg = len(rem) - 1
        shift = rdeg - bdeg
        fq, fr = rem[rdeg].divmod(blead)               # Poly-in-n exact divide
        if not fr.is_zero:
            raise ValueError("BiPoly exact-div: non-exact division (internal)")
        quo[shift] = fq
        for jj in range(len(b_terms)):
            rem[shift + jj] = rem[shift + jj] - fq * b_terms[jj]
        rem = list(_bi_trim(rem))
        if not rem:
            break
    if _bi_trim(rem):
        raise ValueError("BiPoly exact-div: non-zero remainder (internal)")
    return BiPoly._wrap(_bi_trim(quo))


def _solve_parametrized(rho_common: List[BiPoly], den_p: BiPoly,
                        rk_n: BiPoly, rk_d: BiPoly, order: int
                        ) -> Optional[Dict[str, object]]:
    """Build + solve the homogeneous exact-ℚ linear system for the order-``order``
    creative-telescoping ansatz. The unknowns are the polynomial coefficients of
    each ``a_j(n)`` (degree-bounded in ``n``) and of the Gosper certificate
    numerator ``x(n,k)``. A nonzero kernel vector yields the recurrence + the
    rational certificate ``R(n,k) = x(n,k) / D_P(n,k)`` (times the Gosper b/c
    bookkeeping, folded in below)."""
    from .qmat import QMat

    # The Gosper-in-k relation, written over the common denominator D_P:
    #   T(n,k+1) − T(n,k) summed telescopes ⇒ we need x(n,k) with
    #     N_P(n,k) = x(n,k+1)·rk_n(n,k)·U(n,k) − x(n,k)·rk_d(n,k)·V(n,k)
    #   where the cofactors U,V make the two terms share the common k-denominator.
    # Concretely (multiplying the Gosper telescoping G(k+1)−G(k)=T by D_P·D_k):
    #   Let Dk_n = rk_n, Dk_d = rk_d. With G = R·F = (x/D_P)·F:
    #     G(k+1) − G(k) = T  ⇒  x(k+1)·rk_n·D_P(k) − x(k)·rk_d·D_P(k+1)
    #                              = N_P(k)·rk_d·D_P(k+1)/D_P(k) ... (cleared below)
    # We clear to a single polynomial identity in k (coeffs polynomial in n,
    # linear in the unknowns) and match coefficients.
    #
    # Bound the n-degree of each a_j and the (n,k)-degrees of x from the inputs,
    # then assemble the homogeneous matrix and read a kernel vector.
    n_deg = _ansatz_n_degree(rho_common, den_p, rk_n, rk_d, order)
    xk_deg, xn_deg = _ansatz_x_degree(rho_common, den_p, rk_n, rk_d, order, n_deg)

    # Unknown layout: a_0..a_order each (n_deg+1) coeffs, then x's (xk_deg+1)*(xn_deg+1).
    n_a = order + 1
    a_block = n_a * (n_deg + 1)
    x_block = (xk_deg + 1) * (xn_deg + 1)
    n_unknowns = a_block + x_block

    rows = _assemble_rows(rho_common, den_p, rk_n, rk_d, order,
                          n_deg, xk_deg, xn_deg, n_unknowns, a_block)
    if not rows:
        return None
    kernel = _homogeneous_kernel(QMat, rows, n_unknowns, a_block)
    if kernel is None:
        return None
    a_coeffs, x_coeffs = kernel
    coeffs = [Poly.from_coeffs(a_coeffs[j * (n_deg + 1):(j + 1) * (n_deg + 1)])
              for j in range(n_a)]
    coeffs = [c for c in coeffs]
    # all-zero a ⇒ trivial; reject (the kernel picker already excludes it).
    if all(c.is_zero for c in coeffs):
        return None
    # The certificate R(n,k) = x(n,k)/D_P(n,k); represent x as a BiPoly.
    cert = _x_to_bipoly(x_coeffs, xk_deg, xn_deg)
    return {"order": order, "coeffs": coeffs, "certificate": cert}


def _x_to_bipoly(x_coeffs: List[Q], xk_deg: int, xn_deg: int) -> BiPoly:
    """Pack the flat x-coefficient vector (``k``-major, then ``n``) into a
    :class:`BiPoly` ``x(n,k)``."""
    terms: List[Poly] = []
    for dk in range(xk_deg + 1):
        seg = x_coeffs[dk * (xn_deg + 1):(dk + 1) * (xn_deg + 1)]
        terms.append(Poly.from_coeffs(seg))
    return BiPoly(terms)


# ── degree bounds + matrix assembly ───────────────────────────────────────────

def _bi_n_degree(b: BiPoly) -> int:
    """The max ``n``-degree across all ``k``-coefficients (``-1`` for zero)."""
    d = -1
    for c in b.terms:
        if c.degree > d:
            d = c.degree
    return d


def _ansatz_n_degree(rho_common, den_p, rk_n, rk_d, order: int) -> int:
    """A degree bound in ``n`` for the unknown ``a_j(n)`` — the max ``n``-degree
    appearing across the assembled-identity inputs, plus one. For a proper
    hypergeometric term the recurrence coefficients have ``n``-degree comparable
    to the inputs, so this tight bound carries the acceptance set; a too-small
    bound at a given order simply yields no kernel there and the search advances to
    the next order (the C peer mirrors this bound exactly for parity)."""
    d = 1
    for b in (den_p, rk_n, rk_d, *rho_common):
        nd = _bi_n_degree(b)
        if nd > d:
            d = nd
    return d + 1


def _ansatz_x_degree(rho_common, den_p, rk_n, rk_d, order: int, n_deg: int
                     ) -> Tuple[int, int]:
    """Degree bounds ``(k-degree, n-degree)`` for the Gosper certificate numerator
    ``x(n,k)`` written over ``D_P`` — the ``k``-degree from the assembled identity
    (the max input ``k``-degree, +1), the ``n``-degree from the input ``n``-degrees
    (+1). Tight (keeps the parametrized linear system small + exact); the C peer
    mirrors these bounds for byte-parity."""
    kd = den_p.k_degree
    for b in rho_common:
        if b.k_degree > kd:
            kd = b.k_degree
    kd = max(kd, rk_n.k_degree, rk_d.k_degree) + 1
    nd = 1
    for b in (den_p, rk_n, rk_d, *rho_common):
        bn = _bi_n_degree(b)
        if bn > nd:
            nd = bn
    nd = nd + 1
    return kd, nd


def _assemble_rows(rho_common, den_p, rk_n, rk_d, order, n_deg, xk_deg, xn_deg,
                   n_unknowns, a_block):
    """Assemble the homogeneous ℚ-linear system rows. Each row is the coefficient
    of one ``n^p · k^q`` monomial in the cleared Gosper identity

        Σ_j a_j(n)·M_j(n,k)  −  [ x(n,k+1)·P_xp(n,k) − x(n,k)·P_xm(n,k) ]  =  0,

    expanded with each unknown (an ``a_j``-coeff or an ``x``-coeff) carrying its
    monomial contribution. Returns the list of rows (each ``n_unknowns`` wide)."""
    # The cleared identity multiplies the telescoping relation through by D_P(k):
    #   N_P(n,k)·rk_d(n,k)·D_P(n,k+1)
    #       = x(n,k+1)·rk_n(n,k)·D_P(n,k)·D_P(n,k+1)/D_P(n,k+1)  ... see below.
    # To stay polynomial we clear to the LCD; the assembled per-unknown monomial
    # maps are computed by substituting unit unknowns and reading coefficients.
    dp_k1 = den_p.shift_k(1)                      # D_P(n, k+1)

    # The a_j contribution: column for a_j(n)'s n^p coeff is the (n,k)-polynomial
    #   A_jp(n,k) = n^p · rho_common[j](n,k) · rk_d(n,k) · D_P(n,k+1)
    # (this is N_P's j-th piece times the LHS clearing factor rk_d·D_P(k+1)).
    lhs_clear = (rk_d * dp_k1)
    # The x contributions: x(n,k+1)·rk_n(n,k)·D_P(n,k)  and  x(n,k)·rk_d(n,k)·D_P(n,k+1).
    xp_clear = (rk_n * den_p)                     # multiplies x(n,k+1)
    xm_clear = (rk_d * dp_k1)                     # multiplies x(n,k)

    monomials: Dict[Tuple[int, int], List[Q]] = {}

    def _add_bipoly(contrib: BiPoly, col: int, sign: int) -> None:
        for dk, kp in enumerate(contrib.terms):
            for dn, q in enumerate(kp.coeffs):
                if q == 0:
                    continue
                key = (dn, dk)
                row = monomials.get(key)
                if row is None:
                    row = [_Q_ZERO] * n_unknowns
                    monomials[key] = row
                row[col] = row[col] + (q if sign > 0 else -q)

    # a_j columns
    for j in range(order + 1):
        base = rho_common[j] * lhs_clear
        for p in range(n_deg + 1):
            col = j * (n_deg + 1) + p
            contrib = base.scale_n(Poly.monomial(p))
            _add_bipoly(contrib, col, +1)

    # x columns: x(n,k+1) term (positive) and x(n,k) term (negative).
    for dk in range(xk_deg + 1):
        for dn in range(xn_deg + 1):
            col = a_block + dk * (xn_deg + 1) + dn
            # the monomial x = n^dn · k^dk
            x_mono = BiPoly([Poly.monomial(dn) if d == dk else Poly.zero()
                             for d in range(dk + 1)])
            xp = x_mono.shift_k(1) * xp_clear      # x(n,k+1)·rk_n·D_P(k)
            xm = x_mono * xm_clear                 # x(n,k)·rk_d·D_P(k+1)
            _add_bipoly(xp, col, -1)               # moved to LHS ⇒ minus
            _add_bipoly(xm, col, +1)

    return [row for _, row in sorted(monomials.items())]


# The Zeilberger undetermined-coefficient solve is the consumer that hit the dense
# Hadamard-arena wall (the order-2 Franel 484x154 / order-3 2790x780 homogeneous
# systems). rc47 routes it through the bounded-memory CRT re-fibration:
# QMat.rref_crt() is byte-identical to the dense QMat.rref() but solves mod several
# bounded primes (zero coefficient swell) and reconstructs once, so high-order
# definite sums solve at bounded memory — there is no dense-arena cap to work
# around on the Python path any more (the rc44 dense order-≥2 backfill is
# dissolved). Tiny systems stay on the faster dense rref (auto-by-size dispatch).
_CRT_KERNEL_CELL_THRESHOLD: int = 4096


def _kernel_rref(QMat, rows):
    """The exact-ℚ RREF of the homogeneous Zeilberger system, byte-identical
    whichever path runs. Auto-by-size: a large system (cell count past the
    threshold — the order-2/order-3 creative-telescoping matrices that hit the
    dense Hadamard-envelope arena) reduces through the bounded-memory
    :meth:`~srmech.amsc.qmat.QMat.rref_crt` (CRT re-fibration); a tiny system stays
    on the faster dense :meth:`~srmech.amsc.qmat.QMat.rref`. Returns the RREF as a
    list-of-rows of ``Q`` (the form ``_homogeneous_kernel`` consumes)."""
    m = QMat.from_rows([list(r) for r in rows])
    use_crt = m.n_rows * m.n_cols > _CRT_KERNEL_CELL_THRESHOLD
    reduced = m.rref_crt() if use_crt else m.rref()
    return reduced.to_lists()


def _homogeneous_kernel(QMat, rows, n_unknowns, a_block):
    """Find a nonzero kernel vector of the homogeneous system ``rows·v = 0`` whose
    ``a``-block (the first ``a_block`` unknowns) is NOT all zero — that is a genuine
    recurrence (a kernel vector with zero ``a``-block is a spurious certificate-only
    solution). Returns ``(a_coeffs, x_coeffs)`` as exact ``Q`` lists, or ``None``
    when the only kernel vectors have a zero ``a``-block (no recurrence at this
    order). Uses the exact Gauss-Jordan RREF of :class:`~srmech.amsc.qmat.QMat`."""
    if not rows:
        return None
    rref = _kernel_rref(QMat, rows)
    # pivot columns
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
        return None                                # only the trivial solution
    # Try each free column as the lone nonzero free variable (set it to 1); the
    # first that produces a non-trivial a-block is our recurrence (minimal: free
    # columns are scanned low→high, and the a-block columns precede the x-block).
    for f in free:
        vec = [_Q_ZERO] * n_unknowns
        vec[f] = _Q_ONE
        for pc in pivots:
            row = pivot_row_of[pc]
            # pivot value is 1 in rref; x_pc = − Σ_{free} row[free]·x_free
            s = _Q_ZERO
            for g in free:
                if row[g] != 0:
                    s = s + row[g] * vec[g]
            vec[pc] = -s
        a_part = vec[:a_block]
        if any(q != 0 for q in a_part):
            return a_part, vec[a_block:]
    return None
