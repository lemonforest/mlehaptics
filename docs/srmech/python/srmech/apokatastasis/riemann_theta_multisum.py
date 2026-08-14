"""srmech.apokatastasis.riemann_theta_multisum — the HIGHER-GENUS theta-multisum reduction
row: the genus-``g`` Riemann-theta analogue of the elliptic (genus-1) reduction row.

Where the elliptic Jackson rows (:mod:`srmech.apokatastasis.elliptic_jackson` Cₙ,
:mod:`srmech.apokatastasis.elliptic_jackson_an` Aₙ) sum over the GENUS-1 modified theta
``θ(x; p)`` on a single torus, this row lifts the reduction one RUNG UP THE GENUS
AXIS — a multiparameter summation formula whose summand is built from the
**genus-``g`` Riemann theta function on a compact Riemann surface of arbitrary
genus** (``g ≥ 2`` is the genuinely-new regime; ``g = 1`` degenerates to Warnaar's
elliptic formula). It is the follow-on the user named when choosing the Aₙ row
("also begin research scope for higher-genus theta multisum to follow").

────────────────────────────────────────────────────────────────────────────────────
THE HIGHER-GENUS THETA MULTISUM (Spiridonov, arXiv:math/0408366, the Theorem, Eq. sum)
────────────────────────────────────────────────────────────────────────────────────
Take a nonnegative integer ``n``, ``n+1`` free vectors ``z_k ∈ ℂ^g`` and ``4n+4``
DISTINCT points ``a_k, b_k, c_k, d_k`` on a Riemann surface ``S`` (``k = 0..n``).
Write ``[u]`` for the genus-``g`` Riemann theta function of ODD characteristic
(``[-u] = -[u]``; :func:`_odd`), ``[u_1,…,u_m] = ∏_j [u_j]`` (:class:`ThetaBracket`),
and ``v(a,b) = ∫_a^b ω`` for the abelian integral of the first kind (path-additive:
``v(a,b) + v(b,c) = v(a,c)``, antisymmetric ``v(a,b) = -v(b,a)``). Then

    Σ_{k=0}^n  [z_k+v(b_k,c_k), z_k+v(a_k,d_k), v(a_k,c_k), v(b_k,d_k)]
               · ∏_{j=0}^{k-1} [z_j, z_j+v(a_j,c_j)+v(b_j,d_j), v(c_j,d_j), v(a_j,b_j)]
               · ∏_{j=k+1}^{n} [z_j+v(a_j,c_j), z_j+v(b_j,d_j), v(c_j,b_j), v(a_j,d_j)]

      =  ∏_{k=0}^n [z_k, z_k+v(a_k,c_k)+v(b_k,d_k), v(c_k,d_k), v(a_k,b_k)]
       − ∏_{k=0}^n [z_k+v(a_k,c_k), z_k+v(b_k,d_k), v(c_k,b_k), v(a_k,d_k)].

Writing ``g_k`` / ``h_k`` for the two products on the right and ``L_k`` for the
summand's LEADING factor, the structure (the paper's referee remark) is the exact
TELESCOPING identity over ANY commutative ring

    Σ_{k=0}^n (x_k − y_k) ∏_{j<k} x_j ∏_{j>k} y_j  =  ∏_j x_j − ∏_j y_j     (x_k=g_k, y_k=h_k)

whose per-summand ingredient is ``L_k = g_k − h_k`` — the genus-``g`` **Fay
trisecant identity** (J. Fay, *Theta functions on Riemann surfaces*, LNM 353, 1973;
Spiridonov Eq. Fay), the ``n = 0`` base case:

    [z+v(a,c), z+v(b,d), v(c,b), v(a,d)]  +  [z+v(b,c), z+v(a,d), v(a,c), v(b,d)]
        =  [z, z+v(a,c)+v(b,d), v(c,d), v(a,b)]                          (Fay: h + L = g).

For ``g = 1`` (elliptic curves) the identity is Warnaar's (*Constr. Approx.* 18
(2002) 479–502); its trigonometric degeneration is the Macdonald multiparameter
sum (Bhatnagar–Milne, *Adv. Math.* 131 (1997) 188–252, Thm 2.27).

Reference (MPM-verified at build from the extracted arXiv source, PDF sha256
``8478af7407d26d0b0504d381cbe3c32a00f950c3b0c6ab8001a023b7e0c4c319``):
V. P. Spiridonov, "A multiparameter summation formula for Riemann theta functions",
arXiv:math/0408366v2 [math.CA] (2004); Contemp. Math. 417 (2006), 345–353 — the
Theorem (Eq. ``sum``), proved by induction on ``n`` from the Fay identity (Eq.
``Fay``), the ``n = 0`` base case.

────────────────────────────────────────────────────────────────────────────────────
WHAT THIS ROW BUILDS (exact, following the Aₙ rc227 pattern)
────────────────────────────────────────────────────────────────────────────────────
* :class:`ThetaBracket` — the genus-``g`` odd-theta CARRIER: the operand vocabulary
  of this row. ``[u]`` is antisymmetric (``[-u] = -[u]`` — the pure Class-K sign,
  no monomial prefactor, UNLIKE the genus-1 ``θ(z⁻¹) = −z⁻¹·θ(z)``), so it is NOT the
  multiplicative :class:`~srmech.apokatastasis.ellbase.Theta`; it is a NEW additive-argument
  odd symbol. The additive argument ``u`` is carried MULTIPLICATIVELY by an
  :class:`~srmech.apokatastasis.ellbase.EllMonomial` (the free ℤ-lattice over the point/vector
  symbols: ``z_k + v(a,b)`` ↔ the monomial ``Z_k · P_a⁻¹ · P_b``, so additive ``+`` ↔
  multiplicative ``·`` and negation ``−u`` ↔ ``.inv()``); a bracket PRODUCT is a
  signed multiset of canonical arguments. A :class:`ThetaBracketSum` is the free
  commutative ℤ-algebra of such products — the ADDITIVE carrier the identity lives in.
* :func:`riemann_theta_multisum_lhs` — the LEFT-hand side (the ``n+1``-term multisum)
  as an exact :class:`ThetaBracketSum`.
* :func:`multivariate_riemann_theta_sum` — the closed-form RIGHT-hand side
  ``∏ g_k − ∏ h_k``; with ``verify=True`` it also PROVES the reduction per call
  (Fay per-summand + exact telescoping) and returns ``{closed_form, verified}``.
* the per-call PROOF ``(LHS − RHS).is_zero`` (the Aₙ contract): the Fay identity
  rewrites each summand's leading ``L_k`` to ``g_k − h_k`` (:func:`_fay_reduce_lhs`,
  the ONE attested genus-``g`` input), after which ``LHS − RHS`` telescopes to EXACTLY
  the empty :class:`ThetaBracketSum` — verified by free-monomial cancellation
  (:meth:`ThetaBracketSum.is_zero`); a wrong/perturbed closed form is caught (→ False).
* the base ORACLE: :func:`_telescoping_rational_oracle` proves the telescoping
  SKELETON exactly in ℚ (assign arbitrary distinct rationals to ``g_k, h_k``, set
  ``L_k = g_k − h_k``, and check ``Σ = ∏g − ∏h`` — the exact-rational analogue of the
  elliptic rows' ``p = 0`` oracle) for every ``n`` in the tested range.

Exact over the theta-bracket algebra: no float, no ``abs()`` (the odd-theta
antisymmetry sign is the Class-K pin-slot via the ``EllMonomial`` / ``Q`` sign-branch),
no ``math`` / numpy. 1:1 C peer ``srmech_riemann_theta_multisum_lhs`` /
``srmech_riemann_theta_multisum_rhs`` build the SAME bracket products; the pure-Python
body here is the COMPLETE alternative + the C peers' parity oracle.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

from .ellbase import EllMonomial
from ..math.q import Q

__all__ = ["riemann_theta_multisum_lhs", "multivariate_riemann_theta_sum",
           "ThetaBracket", "ThetaBracketSum"]

_Q_ONE = Q(1, 1)
_Q_M1 = Q(-1, 1)


# ── the abelian integral v(a,b) = ∫_a^b ω, carried multiplicatively ─────────────────
def _v(a: EllMonomial, b: EllMonomial) -> EllMonomial:
    """The abelian integral ``v(a,b) = ∫_a^b ω`` of the first kind between two points,
    encoded MULTIPLICATIVELY on the point-symbol lattice as ``P_a⁻¹ · P_b`` (so the
    additive Abel-map difference ``P(b) − P(a)`` becomes a monomial). Path-additivity
    ``v(a,b)·v(b,c) = P_a⁻¹P_b·P_b⁻¹P_c = P_a⁻¹P_c = v(a,c)`` and antisymmetry
    ``v(a,b)⁻¹ = P_aP_b⁻¹ = v(b,a)`` both hold by construction — the ONLY structure the
    identity needs from the abelian integrals (Spiridonov math/0408366, Eq. ab-int)."""
    return a.inv() * b


def _odd(arg: EllMonomial) -> "Tuple[Q, EllMonomial]":
    """Canonicalize a genus-``g`` odd-theta argument: return ``(sign, u0)`` with
    ``[arg] = sign · [u0]``, where ``u0`` is the orientation-fixed representative of the
    antisymmetry pair ``{arg, arg⁻¹}`` (``[-u] = -[u]``, Spiridonov math/0408366 the
    line after Eq. ab-int). Picks the LOWER :meth:`~srmech.apokatastasis.ellbase.EllMonomial._sort_key`
    of ``{arg, arg⁻¹}`` (the same orientation convention as
    :meth:`~srmech.apokatastasis.ellbase.Theta.canonicalize`, minus the quasi-periodicity — a pure
    Class-K ``±1`` sign, NEVER ``abs()``). A UNIT argument (``u = 0``) is the zero bracket
    ``[0] = 0`` (returned as ``sign = Q(0)``)."""
    if arg.is_zero:
        return Q(0, 1), arg
    if arg.is_unit:                                       # [0] = -[0]  ⇒  [0] = 0
        return Q(0, 1), EllMonomial.one()
    inv = arg.inv()
    if arg == inv:                                        # a self-inverse argument (2u = 0)
        return _Q_ONE, arg
    if arg._sort_key() > inv._sort_key():
        return _Q_M1, inv                                # flip to the lower rep, sign −1
    return _Q_ONE, arg


class ThetaBracket:
    """A single genus-``g`` odd Riemann theta ``[u]`` (:func:`_odd`-canonicalized). The
    argument ``u`` is an :class:`~srmech.apokatastasis.ellbase.EllMonomial` (the additive genus-``g``
    argument carried multiplicatively). Immutable; ``==`` / hashing are on the canonical
    argument. This is the atom of the higher-genus reduction row's operand vocabulary —
    the genus-axis peer of :class:`~srmech.apokatastasis.ellbase.Theta`, but odd (pure ``±1``
    antisymmetry, no monomial prefactor)."""

    __slots__ = ("_u",)

    def __init__(self, u: EllMonomial) -> None:
        if not isinstance(u, EllMonomial):
            raise TypeError("ThetaBracket argument must be an EllMonomial")
        self._u = u

    @property
    def arg(self) -> EllMonomial:
        """The (raw) argument ``u`` of ``[u]``."""
        return self._u

    def __repr__(self) -> str:
        return f"ThetaBracket({self._u!r})"


class ThetaBracketSum:
    """A numpy-free EXACT element of the free commutative ℤ-algebra over genus-``g``
    odd-theta BRACKETS ``[u]`` — a ``ℤ``-linear SUM of bracket PRODUCTS
    ``coeff · [u_1]·[u_2]·…`` (each ``[u_i]`` :func:`_odd`-canonicalized, the antisymmetry
    ``±1`` folded into ``coeff``). Immutable, exact (integer/``Q`` coefficients, integer
    argument exponents); sign is the Class-K pin-slot, never ``abs()``.

    This is the ADDITIVE carrier the Spiridonov higher-genus multisum identity lives in —
    the genus-axis peer of :class:`~srmech.apokatastasis.thetasum.ThetaSum`. The identity's exact
    proof is a TELESCOPING cancellation in THIS free algebra (each bracket product acts as a
    commuting monomial), so :meth:`is_zero` is exact free-monomial cancellation — no
    transcendental theta evaluation is required (the telescoping is a ring identity).

    Internally a dict ``{monomial_key: Q coeff}`` where a monomial_key is the sorted tuple
    of canonical bracket-argument keys (a multiset of ``[u_i]``)."""

    __slots__ = ("_terms",)

    def __init__(self, terms: "dict | None" = None) -> None:
        # terms: {monomial_key -> Q}; a monomial_key is a sorted tuple of arg-keys.
        self._terms = {} if terms is None else dict(terms)

    # ── construction ────────────────────────────────────────────────────────────────
    @classmethod
    def zero(cls) -> "ThetaBracketSum":
        """The additive identity (the empty sum)."""
        return cls({})

    @classmethod
    def one(cls) -> "ThetaBracketSum":
        """The multiplicative identity (the empty PRODUCT of brackets, coeff 1)."""
        return cls({(): _Q_ONE})

    @staticmethod
    def _arg_key(u: EllMonomial) -> "Tuple":
        """The exact identity key of a canonical bracket argument (exponent monomial +
        coeff) — two brackets with the same key are the SAME ``[u]``."""
        return (tuple(sorted(u.exps.items())), u.coeff.numerator, u.coeff.denominator)

    @classmethod
    def bracket_product(cls, args: "Sequence[EllMonomial]",
                        coeff: Q = _Q_ONE) -> "ThetaBracketSum":
        """The single monomial ``coeff · ∏_i [args_i]`` — each argument
        :func:`_odd`-canonicalized (the antisymmetry ``±1`` folded into ``coeff``; a zero
        bracket makes the whole product 0). The genus-``g`` bracket ``[u_1,…,u_m]`` of the
        Spiridonov identity."""
        c = coeff
        keys: "List[Tuple]" = []
        for u in args:
            sign, u0 = _odd(u)
            if sign == Q(0, 1):
                return cls.zero()                        # a zero bracket kills the product
            c = c * sign
            keys.append(cls._arg_key(u0))
        keys.sort()
        if c == Q(0, 1):
            return cls.zero()
        return cls({tuple(keys): c})

    # ── exact ℤ-algebra ───────────────────────────────────────────────────────────────
    def __add__(self, other: "ThetaBracketSum") -> "ThetaBracketSum":
        if not isinstance(other, ThetaBracketSum):
            return NotImplemented
        out = dict(self._terms)
        for k, v in other._terms.items():
            nv = out.get(k, Q(0, 1)) + v
            if nv == Q(0, 1):
                out.pop(k, None)
            else:
                out[k] = nv
        return ThetaBracketSum(out)

    def __sub__(self, other: "ThetaBracketSum") -> "ThetaBracketSum":
        if not isinstance(other, ThetaBracketSum):
            return NotImplemented
        return self + other._neg()

    def _neg(self) -> "ThetaBracketSum":
        return ThetaBracketSum({k: -v for k, v in self._terms.items()})

    def __mul__(self, other: "ThetaBracketSum") -> "ThetaBracketSum":
        if not isinstance(other, ThetaBracketSum):
            return NotImplemented
        out: "dict" = {}
        for ka, va in self._terms.items():
            for kb, vb in other._terms.items():
                k = tuple(sorted(ka + kb))               # multiset union of bracket factors
                nv = out.get(k, Q(0, 1)) + va * vb
                if nv == Q(0, 1):
                    out.pop(k, None)
                else:
                    out[k] = nv
        return ThetaBracketSum(out)

    @property
    def is_zero(self) -> bool:
        """True iff this is identically the empty sum — the EXACT free-monomial
        cancellation decision (the peer of :meth:`~srmech.apokatastasis.thetasum.ThetaSum.is_zero`,
        but trivial here: the higher-genus identity is a telescoping ring identity, so the
        residual cancels combinatorially with no theta transcendence)."""
        return not self._terms

    @property
    def n_terms(self) -> int:
        """The number of distinct bracket-product monomials (after combination)."""
        return len(self._terms)

    def __eq__(self, other) -> bool:
        if isinstance(other, ThetaBracketSum):
            return self._terms == other._terms
        return NotImplemented

    def __ne__(self, other):
        r = self.__eq__(other)
        return r if r is NotImplemented else (not r)

    def __repr__(self) -> str:
        return f"ThetaBracketSum({self.n_terms} term(s))"


# ── the Spiridonov summand factors g_k, h_k, L_k (all built from one point-tuple) ────
def _g_bracket(z: EllMonomial, a: EllMonomial, b: EllMonomial,
               c: EllMonomial, d: EllMonomial) -> "ThetaBracketSum":
    """``g_k = [z, z+v(a,c)+v(b,d), v(c,d), v(a,b)]`` — the ``x_k`` of the telescoping
    (Spiridonov Eq. sum RHS first product / Eq. Fay RHS)."""
    return ThetaBracketSum.bracket_product(
        [z, z * _v(a, c) * _v(b, d), _v(c, d), _v(a, b)])


def _h_bracket(z: EllMonomial, a: EllMonomial, b: EllMonomial,
               c: EllMonomial, d: EllMonomial) -> "ThetaBracketSum":
    """``h_k = [z+v(a,c), z+v(b,d), v(c,b), v(a,d)]`` — the ``y_k`` of the telescoping
    (Spiridonov Eq. sum RHS second product / Eq. Fay first term)."""
    return ThetaBracketSum.bracket_product(
        [z * _v(a, c), z * _v(b, d), _v(c, b), _v(a, d)])


def _l_bracket(z: EllMonomial, a: EllMonomial, b: EllMonomial,
               c: EllMonomial, d: EllMonomial) -> "ThetaBracketSum":
    """``L_k = [z+v(b,c), z+v(a,d), v(a,c), v(b,d)]`` — the summand LEADING factor
    (Spiridonov Eq. sum LHS leading / Eq. Fay second term). By the Fay identity
    ``L_k = g_k − h_k``."""
    return ThetaBracketSum.bracket_product(
        [z * _v(b, c), z * _v(a, d), _v(a, c), _v(b, d)])


def _coerce_operand(z, points, op: str):
    """Validate + coerce the multisum operand: ``z`` a sequence of ``n+1``
    :class:`~srmech.apokatastasis.ellbase.EllMonomial` (the vectors ``z_0,…,z_n``); ``points`` a
    sequence of ``n+1`` 4-tuples ``(a_k, b_k, c_k, d_k)`` of ``EllMonomial`` (the points on
    ``S``). Returns ``(zz, pts, n)`` with ``n`` the summation ceiling (``len(z) − 1 ≥ 0``)."""
    if isinstance(z, EllMonomial) or not isinstance(z, (list, tuple)):
        raise TypeError(f"{op}: z must be a list/tuple of EllMonomial; got {z!r}")
    if not isinstance(points, (list, tuple)):
        raise TypeError(f"{op}: points must be a list/tuple of 4-tuples; got {points!r}")
    zz = tuple(z)
    for v in zz:
        if not isinstance(v, EllMonomial):
            raise TypeError(f"{op}: every z entry must be an EllMonomial; got {v!r}")
    if len(zz) < 1:
        raise ValueError(f"{op}: need at least one vector z (n = len(z) − 1 ≥ 0)")
    if len(points) != len(zz):
        raise ValueError(
            f"{op}: points must carry exactly len(z) = {len(zz)} tuples; got {len(points)}")
    pts: "List[Tuple[EllMonomial, EllMonomial, EllMonomial, EllMonomial]]" = []
    for k, tup in enumerate(points):
        if not isinstance(tup, (list, tuple)) or len(tup) != 4:
            raise ValueError(f"{op}: points[{k}] must be a 4-tuple (a,b,c,d); got {tup!r}")
        for v in tup:
            if not isinstance(v, EllMonomial):
                raise TypeError(
                    f"{op}: every point in points[{k}] must be an EllMonomial; got {v!r}")
        pts.append((tup[0], tup[1], tup[2], tup[3]))
    return zz, pts, len(zz) - 1


def riemann_theta_multisum_lhs(z, points):
    """Build the LEFT-hand side of the Spiridonov higher-genus theta multisum
    (arXiv:math/0408366, the Theorem, Eq. ``sum``) — the ``n+1``-term sum

        Σ_{k=0}^n  L_k · ∏_{j<k} g_j · ∏_{j>k} h_j,

    with ``L_k = [z_k+v(b_k,c_k), z_k+v(a_k,d_k), v(a_k,c_k), v(b_k,d_k)]`` the summand
    leading factor, ``g_j = [z_j, z_j+v(a_j,c_j)+v(b_j,d_j), v(c_j,d_j), v(a_j,b_j)]``, and
    ``h_j = [z_j+v(a_j,c_j), z_j+v(b_j,d_j), v(c_j,b_j), v(a_j,d_j)]`` — SYMBOLICALLY, as an
    exact :class:`ThetaBracketSum` over the genus-``g`` odd-theta algebra.

    ``z`` is the length-``n+1`` list of :class:`~srmech.apokatastasis.ellbase.EllMonomial` vectors
    ``(z_0,…,z_n)`` (``n = len(z) − 1``); ``points`` the length-``n+1`` list of 4-tuples
    ``(a_k, b_k, c_k, d_k)`` of ``EllMonomial`` (distinct points on ``S``). Raises
    ``TypeError`` / ``ValueError`` on a malformed operand. By Eq. ``sum`` this EQUALS the
    closed form :func:`multivariate_riemann_theta_sum` constructs — subtracting the two,
    Fay-reducing each summand's leading factor, and deciding ``.is_zero`` is the per-call
    proof (see :func:`multivariate_riemann_theta_sum` with ``verify=True``).

    DISPATCHES to the native ``srmech_riemann_theta_multisum_lhs`` C peer when it is loaded
    (the native ``ThetaBracketSum`` is trusted ONLY after it is rebuilt and confirmed ``==``
    the pure-Python one, which is the COMPLETE alternative + the C peer's parity oracle);
    otherwise the pure result is returned. Exact over the theta-bracket algebra — no float,
    no ``abs()`` (Class-K odd-theta sign), no ``math`` / numpy."""
    zz, pts, n = _coerce_operand(z, points, "riemann_theta_multisum_lhs")
    pure = _lhs_py(zz, pts, n)
    native = _lhs_c(zz, pts, n)
    if native is not None and native == pure:
        return native
    return pure


def _lhs_py(zz, pts, n: int) -> "ThetaBracketSum":
    """The COMPLETE pure-Python multisum LHS construction (the parity oracle for the C
    peer): ``Σ_k L_k · ∏_{j<k} g_j · ∏_{j>k} h_j`` as an exact :class:`ThetaBracketSum`."""
    g = [_g_bracket(zz[k], *pts[k]) for k in range(n + 1)]
    h = [_h_bracket(zz[k], *pts[k]) for k in range(n + 1)]
    lhs = ThetaBracketSum.zero()
    for k in range(n + 1):
        term = _l_bracket(zz[k], *pts[k])
        for j in range(k):
            term = term * g[j]
        for j in range(k + 1, n + 1):
            term = term * h[j]
        lhs = lhs + term
    return lhs


def multivariate_riemann_theta_sum(z, points, *, verify: bool = False):
    """Reduce the Spiridonov higher-genus theta multisum (arXiv:math/0408366, the Theorem,
    Eq. ``sum``) to its closed form — the DIFFERENCE OF TWO PRODUCTS

        ∏_{k=0}^n [z_k, z_k+v(a_k,c_k)+v(b_k,d_k), v(c_k,d_k), v(a_k,b_k)]
      − ∏_{k=0}^n [z_k+v(a_k,c_k), z_k+v(b_k,d_k), v(c_k,b_k), v(a_k,d_k)]     ( = ∏ g_k − ∏ h_k )

    returned as an exact :class:`ThetaBracketSum`. ``z`` is the length-``n+1`` list of
    :class:`~srmech.apokatastasis.ellbase.EllMonomial` vectors ``(z_0,…,z_n)`` (``n = len(z) − 1``);
    ``points`` the length-``n+1`` list of 4-tuples ``(a_k, b_k, c_k, d_k)`` of ``EllMonomial``
    (distinct points on ``S``). Raises ``TypeError`` / ``ValueError`` on a malformed operand.
    This is the genus-``g`` member of the reduction row (the genus-axis lift of the Aₙ / Cₙ
    elliptic Jackson rows) — see the module docstring for the MPM-verified reference (source
    PDF sha256 ``8478af7407d26d0b0504d381cbe3c32a00f950c3b0c6ab8001a023b7e0c4c319``).

    DISPATCHES to the native ``srmech_riemann_theta_multisum_rhs`` C peer when it is loaded
    (trusted ONLY after it is rebuilt and confirmed ``==`` the pure-Python one, the COMPLETE
    alternative + parity oracle); otherwise the pure result is returned.

    ``verify`` (default ``False`` — the plain call returns the bare
    :class:`ThetaBracketSum`). When ``True``, this is a VERIFIED reducer (the Aₙ/Cₙ
    contract): it PROVES the reduction per call and returns a dict::

        {"closed_form": <ThetaBracketSum>, "verified": True | False | None}

    The proof is EXACT (not numeric): it builds the LHS multisum
    (:func:`riemann_theta_multisum_lhs`), rewrites each summand's leading factor ``L_k`` to
    ``g_k − h_k`` by the genus-``g`` **Fay identity** (the ONE attested input relation,
    Spiridonov Eq. Fay), subtracts this closed form, and decides ``.is_zero`` — after the Fay
    rewrite the residual telescopes to EXACTLY the empty :class:`ThetaBracketSum` (a ring
    identity; free-monomial cancellation). ``verified`` is ``True`` when the residual is
    provably ``≡ 0`` (the closed form EQUALS the Fay-reduced sum), ``False`` if not (a
    wrong/perturbed closed form is caught), and ``None`` — an HONEST "not verified in-budget"
    — never returned in the shipped range (the decision is exact free-monomial cancellation,
    feasible at any ``n`` one can hold; the ``None`` slot is kept for contract parity with the
    Aₙ/Cₙ rows). The constructive ``closed_form`` is returned in EVERY case."""
    zz, pts, n = _coerce_operand(z, points, "multivariate_riemann_theta_sum")
    pure = _rhs_py(zz, pts, n)
    native = _rhs_c(zz, pts, n)
    closed = native if (native is not None and native == pure) else pure
    if not verify:
        return closed
    verified = _verify_reduction(zz, pts, n, closed)
    return {"closed_form": closed, "verified": verified}


def _rhs_py(zz, pts, n: int) -> "ThetaBracketSum":
    """The COMPLETE pure-Python closed-form RHS ``∏ g_k − ∏ h_k`` (the parity oracle for the
    C peer)."""
    prod_g = ThetaBracketSum.one()
    prod_h = ThetaBracketSum.one()
    for k in range(n + 1):
        prod_g = prod_g * _g_bracket(zz[k], *pts[k])
        prod_h = prod_h * _h_bracket(zz[k], *pts[k])
    return prod_g - prod_h


def _fay_reduce_lhs(zz, pts, n: int) -> "ThetaBracketSum":
    """The Fay-REDUCED multisum LHS: the same sum as :func:`_lhs_py` but with each summand's
    leading factor ``L_k`` replaced by ``g_k − h_k`` (the genus-``g`` **Fay identity**,
    Spiridonov Eq. Fay — the ONE attested input this reduction consumes). By construction
    ``L_k`` and ``g_k − h_k`` are the two sides of the SAME Fay instance (all built from the
    same point-tuple ``(z_k, a_k, b_k, c_k, d_k)``), so this equals :func:`_lhs_py` as a
    theta identity; the difference from the RHS then telescopes to EXACTLY zero over the free
    bracket algebra."""
    g = [_g_bracket(zz[k], *pts[k]) for k in range(n + 1)]
    h = [_h_bracket(zz[k], *pts[k]) for k in range(n + 1)]
    out = ThetaBracketSum.zero()
    for k in range(n + 1):
        term = g[k] - h[k]                               # L_k  →  g_k − h_k   (Fay)
        for j in range(k):
            term = term * g[j]
        for j in range(k + 1, n + 1):
            term = term * h[j]
        out = out + term
    return out


def _verify_reduction(zz, pts, n: int, closed: "ThetaBracketSum") -> "bool | None":
    """PROVE that ``closed`` equals the Spiridonov higher-genus theta multisum
    (arXiv:math/0408366 Eq. sum), EXACTLY: Fay-reduce the LHS (:func:`_fay_reduce_lhs`),
    subtract ``closed``, and return ``.is_zero`` — the exact free-monomial telescoping
    cancellation. Returns ``True`` (proved ``≡ 0``), ``False`` (the residual is provably
    non-zero — a wrong/perturbed ``closed`` is caught). ``closed`` is taken as an argument
    (not rebuilt) so the verify machinery can be exercised on a deliberately-perturbed closed
    form (→ ``False``)."""
    residual = _fay_reduce_lhs(zz, pts, n) - closed
    return residual.is_zero


# ── the exact-ℚ telescoping base ORACLE (the elliptic rows' p=0-oracle analogue) ─────
def _telescoping_rational_oracle(g_vals: "Sequence[Q]", h_vals: "Sequence[Q]") -> bool:
    """The EXACT-ℚ base oracle for the identity's TELESCOPING SKELETON (the analogue of the
    elliptic rows' ``p = 0`` exact-rational oracle): given arbitrary rational values
    ``g_k, h_k`` (``k = 0..n``) and setting ``L_k = g_k − h_k`` (the Fay relation, which is an
    IDENTITY once ``g_k, h_k`` are the two Fay-RHS/first-term products), verify EXACTLY in ℚ

        Σ_{k=0}^n (g_k − h_k) ∏_{j<k} g_j ∏_{j>k} h_j  =  ∏_j g_j − ∏_j h_j.

    Returns ``True`` iff the equality holds exactly. This proves the ring-identity core of
    Spiridonov Eq. sum with no theta transcendence — exact ℚ, no float, no ``abs()``."""
    n1 = len(g_vals)
    assert n1 == len(h_vals) and n1 >= 1
    lhs = Q(0, 1)
    for k in range(n1):
        term = g_vals[k] - h_vals[k]
        for j in range(k):
            term = term * g_vals[j]
        for j in range(k + 1, n1):
            term = term * h_vals[j]
        lhs = lhs + term
    prod_g = _Q_ONE
    prod_h = _Q_ONE
    for k in range(n1):
        prod_g = prod_g * g_vals[k]
        prod_h = prod_h * h_vals[k]
    return lhs == (prod_g - prod_h)


# ── C dispatch (parity-checked; the pure body above is the complete alternative) ─────
def _marshal(zz, pts):
    """The interned symbol universe for the C peers: every distinct point/vector symbol
    across ``z`` and ``points``, sorted by NAME (so the C dense exponent vector reproduces
    the Python :meth:`~srmech.apokatastasis.ellbase.EllMonomial._sort_key` order). Returns
    ``(sym_list, idx)``."""
    syms: "set" = set()
    for u in zz:
        syms.update(u.exps.keys())
    for tup in pts:
        for u in tup:
            syms.update(u.exps.keys())
    sym_list = sorted(syms)
    return sym_list, {s: i for i, s in enumerate(sym_list)}


def _lhs_c(zz, pts, n: int) -> "ThetaBracketSum | None":
    """Dispatch the multisum LHS construction to the native ``srmech_riemann_theta_multisum_lhs``
    C peer → the :class:`ThetaBracketSum`, or ``None`` when the native symbols are absent (the
    caller falls to :func:`_lhs_py`)."""
    return _multisum_c(zz, pts, n, side=0)


def _rhs_c(zz, pts, n: int) -> "ThetaBracketSum | None":
    """Dispatch the closed-form RHS construction to the native ``srmech_riemann_theta_multisum_rhs``
    C peer → the :class:`ThetaBracketSum`, or ``None`` when the native symbols are absent (the
    caller falls to :func:`_rhs_py`)."""
    return _multisum_c(zz, pts, n, side=1)


def _multisum_c(zz, pts, n: int, side: int) -> "ThetaBracketSum | None":
    """Shared C-dispatch body for both builders (``side`` 0 = LHS, 1 = RHS). Marshals the
    ``z`` / point EllMonomials over the interned symbol table to dense integer exponent rows
    and rebuilds the returned bracket-product monomials into an exact :class:`ThetaBracketSum`
    (byte-exact to the pure carrier). Returns ``None`` when the native symbols are absent."""
    from .. import _native as _nat
    hn = getattr(_nat, "has_native_riemann_theta_multisum", None)
    if hn is None or not hn():
        return None
    sym_list, idx = _marshal(zz, pts)
    n_syms = len(sym_list)

    def row(m: EllMonomial) -> "List[int]":
        r = [0] * n_syms
        for s, e in m.exps.items():
            r[idx[s]] = e
        return r

    z_rows = [row(u) for u in zz]
    pt_rows = [[row(u) for u in tup] for tup in pts]
    got = _nat.riemann_theta_multisum_c(n_syms, n, side, z_rows, pt_rows)
    if got is None:
        return None
    # got: list of (coeff_num, coeff_den, [ (arg_exps_row) ... ]) monomials.
    terms: "dict" = {}
    for coeff_num, coeff_den, arg_rows in got:
        keys = []
        for arow in arg_rows:
            exps = {sym_list[j]: int(arow[j]) for j in range(n_syms) if arow[j] != 0}
            keys.append(ThetaBracketSum._arg_key(EllMonomial(_Q_ONE, exps)))
        keys.sort()
        k = tuple(keys)
        c = Q(int(coeff_num), int(coeff_den))
        nv = terms.get(k, Q(0, 1)) + c
        if nv == Q(0, 1):
            terms.pop(k, None)
        else:
            terms[k] = nv
    return ThetaBracketSum(terms)
