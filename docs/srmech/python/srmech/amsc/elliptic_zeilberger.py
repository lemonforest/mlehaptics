"""srmech.amsc.elliptic_zeilberger — the ELLIPTIC analog of Zeilberger's creative
telescoping (the SECOND engine op of the ELLIPTIC F929 reduction row, the top of the
base-axis degeneration tower ``elliptic → q → ordinary``).

Where :func:`srmech.amsc.elliptic_gosper.elliptic_gosper` decides INDEFINITE
elliptic summation of a single theta-hypergeometric term in ``n`` (its term ratio an
:class:`~srmech.amsc.ellbase.EllRatio`), the **elliptic Zeilberger** algorithm handles
a DEFINITE elliptic-hypergeometric sum ``f(n) = Σ_k F(n,k)`` of a *theta-hypergeometric
term* ``F(n,k)`` (bivariate-elliptic, in ``n`` via ``x = qⁿ`` and ``k`` via ``y = qᵏ``)
and produces the **linear recurrence with theta-coefficient (``EllRatio``-in-``n``)
coefficients**

    Σ_{j=0}^{L} a_j(n) · f(n+j) = 0

that ``f`` satisfies — the minimal-order such recurrence, each ``a_j(n)`` an
:class:`~srmech.amsc.ellbase.EllRatio` in ``n`` only (no ``y``) — together with the
**companion certificate** ``G(n,k)`` (a theta-quotient ``EllRatio`` in ``(x,y)``)
making the **creative-telescoping identity**

    Σ_j a_j(n) · F(n+j,k) = G(n,k+1) − G(n,k)

hold. This is the elliptic analog of the §76 :func:`srmech.amsc.zeilberger.zeilberger`
and of :func:`srmech.amsc.q_zeilberger.q_zeilberger`, ONE algebra up — the atoms are
theta-factors, not (Laurent-)monomials.

Input — the **two bivariate-elliptic term ratios** of ``F``, each an
:class:`~srmech.amsc.ellbase.EllRatio` over symbols including BOTH the n-summation
variable ``x = qⁿ`` and the k-summation variable ``y = qᵏ``:

  * ``r_n(x,y) = F(n+1,k) / F(n,k)``   (the ``rn`` operand; ``σ_x : x ↦ q·x``)
  * ``r_k(x,y) = F(n,k+1) / F(n,k)``   (the ``rk`` operand; ``σ_y : y ↦ q·y``)

(The ``EllRatio`` carrier is already MULTIVARIATE — its theta arguments are monomials
over arbitrary symbols, so a second summation variable ``y`` is just another symbol.)

Reference (MPM-verified at build — the actual sources read, authors + title + book /
journal + editors + year + pages confirmed, NOT a training-data attribution):

    The elliptic (theta) analogues of hypergeometric series were introduced by I.B.
    Frenkel and V.G. Turaev, "Elliptic solutions of the Yang–Baxter equation and
    modular hypergeometric functions," in *The Arnold–Gelfand Mathematical Seminars*,
    eds. V.I. Arnold, I.M. Gelfand, V.S. Retakh & M. Smirnov (Birkhäuser Boston, 1997),
    pp. 171–204. The keystone identity that gates the row is the terminating,
    very-well-poised **Frenkel–Turaev ₁₀E₉ sum** (equivalently the elliptic Jackson
    ₈W₇ sum) — stated as Corollary 2.2 / Eq. (2.11) of S.O. Warnaar, "Summation and
    transformation formulas for elliptic hypergeometric series," *Constr. Approx.* 18
    (2002) 479–502 (arXiv:math/0001006), where (Eq. 2.3) the elliptic function
    ``E(x) = E(x;p) = (x;p)_∞ (p/x;p)_∞`` is the modified theta ``θ(x;p)`` this module
    carries, its quasi-periodicity ``E(x) = (−x)ᵏ p^{C(k,2)} E(xpᵏ)`` (Eq. 2.5) and
    inversion ``E(x) = −x E(1/x)`` (Eq. 2.4) are exactly
    :meth:`~srmech.amsc.ellbase.Theta.canonicalize`, and the elliptic shifted factorial
    ``(a;q,p)_n = ∏_{k=0}^{n-1} E(aqᵏ)`` (Eq. 2.6) is
    :meth:`~srmech.amsc.ellbase.Theta.pochhammer`. The ₁₀E₉'s closed form is a ratio of
    such theta-Pochhammers in ``n`` — and that closed form's exact n-recurrence is the
    keystone this op certifies (see below). Secondary anchor (already cited by
    :mod:`srmech.amsc.elliptic_gosper`): George Gasper & Michael Schlosser, "Summation,
    transformation, and expansion formulas for multibasic theta hypergeometric series,"
    *Adv. Stud. Contemp. Math.* (Kyungshang) 11, no. 1 (2005), 67–84
    (arXiv:math/0505215), whose Eq. (2.4) balancing condition is
    :meth:`~srmech.amsc.ellbase.EllRatio.is_elliptic`.

⚠ EXACT VERIFICATION — the rc61 standard, NON-NEGOTIABLE. A recurrence + certificate
is a PROOF object: it is accepted ONLY when the creative-telescoping identity is
verified EXACTLY, never on a merely-converging residual (the §76 / rc61
no-hallucination standard). The theta-quotient carrier is multiplicatively but NOT
additively closed, so the additive residual ``Σ_j a_j(n)·F(n+j,k) − (G(n,k+1) −
G(n,k))`` cannot be exact-subtracted in the carrier — AND a truncated modified-theta
product only CONVERGES (it is not exact at any finite depth), so a raw ``eval_trunc``
of a theta-bearing residual is NOT an exact test. The verifier uses the
**FUNDAMENTAL THEOREM OF ELLIPTIC FUNCTIONS (the elliptic degree bound)** the way
:func:`~srmech.amsc.q_wz_certificate.q_wz_certificate` verifies degree-bounded: divide
the identity through by ``F(n,k)`` to the rational-of-theta-quotients form

    Σ_j a_j(n)·ρ_j(x,y) = R(x,qy)·r_k(x,y) − R(x,y)         (G = R·F; ρ_j = ∏_{i<j} σ_x^i r_n)

and CLEAR it to a comparison of theta-quotients whose surviving difference is a
*totally-elliptic* function of bounded elliptic degree ``d`` (the theta-factor count).
A nonzero elliptic function of degree ``d`` has exactly ``d`` zeros per fundamental
domain, so the residual is identically zero IFF it is EXACTLY 0 at MORE THAN ``d``
distinct exact-``ℚ`` sample points. When the identity holds, the cleared two sides are
the **SAME carrier object** (the multiplicative theta collapse of
:meth:`~srmech.amsc.ellbase.Theta.canonicalize` is exact), so each side's
``eval_trunc`` returns the IDENTICAL truncated rational at every point — the agreement
is EXACT (Class-K magnitude difference ``== 0`` in ``ℚ``), not numerical. A candidate
whose cleared residual is not provably-exactly-0 by this degree-bound test → honest
``None`` (the rc61 lesson: never accept on a converging witness).

The structurally-decidable, EXACTLY-certifiable class this engine certifies (the
elliptic analogue of the elliptic-Gosper theta-free core, and of the
:func:`~srmech.amsc.q_zeilberger.q_zeilberger` C peer's k-free q-geometric scope) is
the **order-1 recurrence of a ``k``-free-``r_n`` term** — a term whose n-shift ratio
``r_n(x,y) = r_n(x)`` is independent of the summation variable ``k`` (a theta-quotient
in ``x`` only). Such an ``F(n,k) = c(n)·H(k)`` (the n-part is a theta-Pochhammer ratio)
has ``f(n) = c(n)·Σ_k H(k)`` and satisfies the EXACT order-1 recurrence

    rₙ_den(x)·f(n+1) − rₙ_num(x)·f(n) = 0          (a_1 = rₙ_den, a_0 = −rₙ_num)

with the trivial certificate ``G ≡ 0`` (no k-telescoping is needed — the recurrence IS
the term ratio). Its degree-bound residual ``a_0 + a_1·r_n`` collapses in the carrier
to the ZERO function (degree ``d = 0``, theta-free), and ``eval_trunc`` of a theta-free
``EllRatio`` is EXACT — so the verification is exact with NO truncation, NO convergence.
**This is the FT ₁₀E₉ keystone:** the Frenkel–Turaev sum's closed form is a ratio of
theta-Pochhammers in ``n``, and THAT closed form satisfies precisely this exact
order-1 elliptic recurrence, with the recurrence coefficients its very theta factors.

The GENUINE ``k``-dependent-``r_n`` creative telescoping (where the certificate ``G``
is a nontrivial theta-quotient and the residual carries surviving theta factors that
must cancel by the *additive* theta addition formula) lies OUTSIDE the multiplicative
``EllRatio`` carrier's exactly-decidable reach — the SAME boundary
:func:`~srmech.amsc.elliptic_gosper.elliptic_gosper` honestly hits (a genuine theta
telescoper needs the additive theta lattice, a future carrier extension). For such an
input this op returns honest ``None`` rather than a numerically-witnessed certificate.

The whole pipeline stays EXACT over the modified-theta algebra; the ONE numeric
materialisation is the exact-``ℚ`` truncated theta product
:meth:`~srmech.amsc.ellbase.EllRatio.eval_trunc`, used ONLY on the theta-free
(degree-``d``) cleared residual where it is exact. There is NO float anywhere; sign is
the **Class-K** pin-slot via the ``Q`` / ``EllMonomial`` sign-branch (never an ALU
``abs()``); no ``math`` module, no numpy. This op PARAMETRIZES the rc61 elliptic-Gosper
engine (it reuses the candidate-enumeration + exact-``ℚ`` degree-bound verification
shape); the elliptic row continues with the elliptic-WZ proof op (rc63).

C peer: ``srmech_elliptic_zeilberger`` (``c/src/srmech_elliptic_zeilberger.c``) mirrors
the ``srmech_q_zeilberger`` scope — it COMPLETES the canonical native case (the
``k``-free-``r_n`` order-1 elliptic-geometric recurrence) over the integer theta-
exponent lattice + exact-``ℚ`` prefactor, byte-identical to the Python recurrence, and
DECLINES the rest (``out_has = 0`` → the Python dispatch re-runs the COMPLETE
pure-Python body here, the parity oracle AND the full-coverage decider — a ``has=0`` is
NEVER a definitive "no recurrence"). Caller-arena, malloc-free, JPL-clean.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .cascade import magnitude
from .ellbase import EllMonomial, EllRatio, Theta, _P, _Q_SYM, _X
from .q import Q

__all__ = ["elliptic_zeilberger"]

_Q_ZERO = Q(0, 1)
_Q_ONE = Q(1, 1)

# The k-summation-variable symbol (y = qᵏ); the second elliptic variable. The
# k-shift σ_y (k ↦ k+1, i.e. y ↦ q·y) and the k-period shift (y ↦ p·y) act on y.
_Y = "y"

# The exact-ℚ sample points at which the degree-bound creative-telescoping residual is
# verified. Several independent (x, y, params) points pin the rational identity past
# the elliptic degree bound. A point with |p| < 1 makes the truncated modified-theta
# product the exact-ℚ value the verifier reads on a theta-FREE residual (where the
# truncation is exact); a recurrence is accepted ONLY when the residual is EXACTLY 0 at
# every sample (Class-K magnitude, never an ALU abs()). All exact rationals — no float.
_VERIFY_POINTS: Tuple[Dict[str, Q], ...] = (
    {_Q_SYM: Q(2, 1), _P: Q(1, 9), _X: Q(2, 3), _Y: Q(3, 5), "a": Q(3, 5),
     "b": Q(4, 7), "c": Q(5, 8), "d": Q(2, 9), "e": Q(7, 4), "f": Q(3, 8)},
    {_Q_SYM: Q(3, 1), _P: Q(1, 16), _X: Q(3, 4), _Y: Q(4, 9), "a": Q(2, 5),
     "b": Q(5, 7), "c": Q(3, 8), "d": Q(4, 9), "e": Q(2, 3), "f": Q(5, 6)},
    {_Q_SYM: Q(2, 1), _P: Q(1, 25), _X: Q(4, 5), _Y: Q(5, 8), "a": Q(6, 7),
     "b": Q(3, 10), "c": Q(7, 9), "d": Q(5, 11), "e": Q(8, 5), "f": Q(2, 7)},
)

# The truncation depth the EXACT verifier reads. A recurrence is accepted ONLY when the
# degree-bound residual is EXACTLY 0 at every sample — which holds iff the residual
# carries NO surviving theta factor (the theta-free / elliptic-geometric core), whose
# exact-ℚ truncated value IS the true value at any finite depth. So the depth is
# immaterial to a genuine recurrence; it only bounds the near-miss reject.
_VERIFY_TRUNC = 12

# The largest ansatz order the bounded search reaches by default (a generous cap; the
# native peer + the exactly-decidable class are order ≤ 1 — the rest is the owed
# additive-theta-lattice extension, where the search finds nothing and returns None).
_DEFAULT_MAX_ORDER = 6


def _native():
    """The native ``_native`` module IF the rc62 ``srmech_elliptic_zeilberger`` peer is
    present and bound, else ``None`` — so ``elliptic_zeilberger`` dispatches to C when
    available and falls cleanly to the pure-Python body (the complete alternative + the
    parity oracle) otherwise. Imported lazily to avoid a bootstrap cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    probe = getattr(nat, "has_native_elliptic_zeilberger", None)
    return nat if (probe is not None and probe()) else None


def _coerce_ratio(value, name: str) -> EllRatio:
    """Coerce a term-ratio operand to an :class:`~srmech.amsc.ellbase.EllRatio` (the
    same lift :func:`srmech.amsc.elliptic_gosper._coerce_ratio` performs): an
    ``EllRatio`` passes through; an ``EllMonomial`` (a pure-monomial ratio) / a
    ``Theta`` (a single numerator theta) is lifted."""
    if isinstance(value, EllRatio):
        return value
    if isinstance(value, EllMonomial):
        return EllRatio.monomial(value)
    if isinstance(value, Theta):
        return EllRatio.theta(value)
    raise TypeError(
        f"elliptic_zeilberger: the {name} term-ratio operand must be an EllRatio (or "
        f"an EllMonomial / Theta the carrier lifts); got {value!r}")


# ── y-structure probe (is the n-shift ratio independent of the k-variable?) ────


def _depends_on(ratio: EllRatio, sym: str) -> bool:
    """True iff the ``EllRatio`` ``ratio`` carries the symbol ``sym`` (in its prefactor
    OR in any theta argument). The ``k``-free-``r_n`` exactly-decidable class is exactly
    ``not _depends_on(r_n, 'y')``."""
    if ratio.prefactor.exp_of(sym) != 0:
        return True
    for t in tuple(ratio.num) + tuple(ratio.den):
        if t.arg.exp_of(sym) != 0:
            return True
    return False


# ── the EXACT degree-bound creative-telescoping verifier (exact-ℚ eval oracle) ──


def _residual_is_zero(lhs: EllRatio, rhs: EllRatio) -> bool:
    """Decide the cleared creative-telescoping residual ``lhs − rhs = 0`` EXACTLY by
    the elliptic degree bound. ``lhs`` and ``rhs`` are the two cleared theta-quotient
    sides; when the identity holds they are the SAME elliptic function. The
    multiplicative theta collapse of :meth:`~srmech.amsc.ellbase.Theta.canonicalize` is
    exact, so an identity holds iff ``lhs == rhs`` as canonical carrier objects — and
    then each side's :meth:`~srmech.amsc.ellbase.EllRatio.eval_trunc` returns the
    IDENTICAL truncated rational at every sample, so the residual is EXACTLY 0 at every
    one of the :data:`_VERIFY_POINTS` (more than the elliptic degree bound ``d`` = the
    theta-factor count). A side carrying a surviving theta whose partner does not cancel
    it makes the carrier forms unequal → rejected (it would only CONVERGE under
    ``eval_trunc``, never hit exact 0, the rc61 no-hallucination reject). This is EXACT:
    exact-``ℚ`` evals + a carrier-equality / degree count; no float, no convergence
    threshold (Class-K magnitude, never an ALU ``abs()``)."""
    # the degree bound d = total surviving theta-factor count across both sides; the
    # _VERIFY_POINTS supply strictly more than any small d (a genuine elliptic identity
    # of this engine's scope is degree 0 after the carrier collapse).
    if lhs == rhs:
        # the carrier forms agree exactly → the residual is the zero function; confirm
        # the exact-ℚ degree-bound evals AGREE at every sample (a theta-free or
        # carrier-identical residual evaluates exactly, not merely convergently).
        return _evals_agree(lhs, rhs)
    return False


def _evals_agree(lhs: EllRatio, rhs: EllRatio) -> bool:
    """Confirm ``lhs`` and ``rhs`` evaluate to the EXACT same exact-``ℚ`` value at every
    sample in :data:`_VERIFY_POINTS` (the degree-bound check made concrete). For
    carrier-equal sides this is exact (identical truncated products); a sample whose
    denominator theta vanishes is skipped. At least one sample must evaluate."""
    seen = 0
    for vals in _VERIFY_POINTS:
        try:
            a = lhs.eval_trunc(vals, _VERIFY_TRUNC)
            b = rhs.eval_trunc(vals, _VERIFY_TRUNC)
        except (ZeroDivisionError, KeyError, TypeError):
            continue
        if magnitude(a - b) != _Q_ZERO:      # accept ONLY an EXACT-0 residual
            return False
        seen += 1
    return seen > 0


def _verify_order1_kfree(rn: EllRatio, a0: EllRatio, a1: EllRatio) -> bool:
    """Verify the order-1 ``k``-free creative-telescoping identity EXACTLY: with the
    certificate ``G ≡ 0`` the identity ``a_0(x)·F(n,k) + a_1(x)·F(n+1,k) = 0`` divides
    (by ``F(n,k)``) to ``a_0(x) + a_1(x)·r_n(x) = 0``, i.e. ``a_1·r_n == −a_0`` as
    elliptic functions. The carrier product ``a_1·r_n`` and ``−a_0`` must be the SAME
    canonical object (the exact multiplicative theta collapse), then verified by the
    exact-``ℚ`` degree-bound evals. Exact — the residual is the ZERO function (degree
    ``d = 0``), no truncation tail, no convergence."""
    lhs = a1 * rn                                  # a_1(x)·r_n(x), in the carrier
    rhs = a0 * EllRatio.monomial(EllMonomial.scalar(Q(-1, 1)))   # −a_0(x)
    return _residual_is_zero(lhs, rhs)


# ── the exactly-decidable order-1 k-free recurrence builder ─────────────────────


def _order1_kfree_recurrence(rn: EllRatio) -> Optional[Dict[str, object]]:
    """Build + EXACTLY verify the order-1 recurrence of a ``k``-free-``r_n`` elliptic
    term: ``rₙ_den(x)·f(n+1) − rₙ_num(x)·f(n) = 0`` (``a_1 = rₙ_den``, ``a_0 =
    −rₙ_num``), certificate ``G ≡ 0``. ``r_n`` must be a theta-quotient in ``x`` only
    (``not _depends_on(r_n, 'y')``); returns the recurrence dict when the degree-bound
    verifier accepts (it always does for a genuine ``k``-free ``r_n``), else ``None``."""
    if rn.is_zero:
        # r_n ≡ 0 (no proper term) — no nonzero elliptic-hypergeometric recurrence.
        return None
    if rn.is_unit:
        # r_n ≡ 1 (f(n) constant in n) → the order-1 WZ recurrence f(n+1) − f(n) = 0
        # (coeffs [−1, +1]), certificate G ≡ 0. Verified exactly (residual ≡ 0).
        a0 = EllRatio.monomial(EllMonomial.scalar(Q(-1, 1)))
        a1 = EllRatio.one()
        if _verify_order1_kfree(rn, a0, a1):
            return _recurrence_result(1, [a0, a1], _zero_certificate())
        return None
    # a_1 = rₙ_den (the denominator theta-quotient), a_0 = −rₙ_num (the numerator
    # theta-quotient, sign = Class-K). r_n = num/den as EllRatios:
    num_n = EllRatio._wrap(rn.prefactor, rn.num, ())       # the numerator theta-quotient
    den_n = EllRatio._wrap(EllMonomial.one(), rn.den, ())  # the denominator theta-quotient
    a1 = den_n
    a0 = num_n * EllRatio.monomial(EllMonomial.scalar(Q(-1, 1)))   # −rₙ_num
    if not _verify_order1_kfree(rn, a0, a1):
        return None
    return _recurrence_result(1, [a0, a1], _zero_certificate())


def _zero_certificate() -> EllRatio:
    """The trivial companion certificate ``G ≡ 0`` (no k-telescoping needed for the
    ``k``-free order-1 recurrence) — the zero ``EllRatio``."""
    return EllRatio.monomial(EllMonomial.scalar(_Q_ZERO))


def _ratio_to_operand(r: EllRatio) -> Dict[str, object]:
    """An :class:`~srmech.amsc.ellbase.EllRatio` → the public operand dict (prefactor
    coeff + exponent map, and the numerator / denominator theta-argument exponent
    maps), so a caller can rebuild the carrier and re-verify the recurrence
    independently."""
    def _mono(m: EllMonomial):
        return (m.coeff.numerator, m.coeff.denominator, dict(m.exps))

    pn, pd, pexps = _mono(r.prefactor)
    return {
        "prefactor": {"coeff": (pn, pd), "exps": pexps},
        "num": [dict(t.arg.exps) for t in r.num],
        "den": [dict(t.arg.exps) for t in r.den],
        "ratio": r,
    }


def _recurrence_result(order: int, coeffs: List[EllRatio],
                       cert: EllRatio) -> Dict[str, object]:
    """The verified recurrence → the public return dict. ``coeffs`` are the ``a_j(n)``
    (``EllRatio`` in ``n`` only) and ``cert`` is the companion ``G(n,k)``; both are
    returned as their carrier objects (under ``"coeffs"`` / ``"certificate"``) AND as
    operand dicts (so a caller can rebuild + re-verify independently)."""
    return {
        "order": order,
        "coeffs": coeffs,
        "coeff_operands": [_ratio_to_operand(c) for c in coeffs],
        "certificate": cert,
        "certificate_operand": _ratio_to_operand(cert),
    }


# ── the wire form for the C bridge (theta-arg integer-exponent lattice) ─────────


def _ratio_to_form(r: EllRatio) -> Dict[str, object]:
    """An :class:`~srmech.amsc.ellbase.EllRatio` → the bridge form the C peer consumes
    (the SAME form :func:`srmech.amsc.elliptic_gosper._ratio_to_form` emits): the
    exact-``ℚ`` prefactor ``(coeff_num, coeff_den, [(sym, exp), …])`` plus the
    numerator / denominator theta-argument exponent maps. Pure integer exponents +
    exact-``ℚ`` coefficients — no float."""
    def _mono(m: EllMonomial):
        return (m.coeff.numerator, m.coeff.denominator, sorted(m.exps.items()))

    return {
        "prefactor": _mono(r.prefactor),
        "num": [_mono(t.arg) for t in r.num],
        "den": [_mono(t.arg) for t in r.den],
    }


def _form_to_ratio(form) -> EllRatio:
    """Rebuild an :class:`~srmech.amsc.ellbase.EllRatio` from the bridge form (from the
    C peer)."""
    def _mono(triple) -> EllMonomial:
        cn, cd, exps = triple
        return EllMonomial(Q(cn, cd), {s: e for s, e in exps})

    pref = _mono(form["prefactor"])
    num = tuple(Theta(_mono(t)) for t in form["num"])
    den = tuple(Theta(_mono(t)) for t in form["den"])
    return EllRatio(pref, num=num, den=den)


# ── the public op ──────────────────────────────────────────────────────────────


def elliptic_zeilberger(rn, rk, max_order: int = _DEFAULT_MAX_ORDER
                        ) -> Optional[Dict[str, object]]:
    """The ELLIPTIC analog of Zeilberger's creative telescoping for the definite
    elliptic-hypergeometric sum ``f(n) = Σ_k F(n,k)`` over ``(x, y) = (qⁿ, qᵏ)`` (the
    SECOND engine op of the ELLIPTIC F929 row).

    ``rn`` is the n-term-ratio ``r_n(x,y) = F(n+1,k)/F(n,k)`` (``σ_x : x ↦ q·x``); ``rk``
    is the k-term-ratio ``r_k(x,y) = F(n,k+1)/F(n,k)`` (``σ_y : y ↦ q·y``). Each is an
    :class:`~srmech.amsc.ellbase.EllRatio` over symbols including the n-variable
    ``x = qⁿ`` and the k-variable ``y = qᵏ`` (an ``EllMonomial`` / ``Theta`` is lifted).

    Returns the minimal-order recurrence
    ``{"order": L, "coeffs": [EllRatio_in_n, …], "certificate": EllRatio}`` such that
    ``Σ_{j=0}^{L} coeffs[j](n)·f(n+j) = 0`` with the companion ``G = certificate``
    satisfying ``Σ_j coeffs[j](n)·F(n+j,k) = G(n,k+1) − G(n,k)``, or ``None`` when no
    such recurrence is EXACTLY certifiable in the elliptic carrier (the honest residue).
    The ``coeffs[j]`` are ``EllRatio`` in ``n`` only; ``certificate`` is an ``EllRatio``
    in ``(x,y)`` (``G ≡ 0`` for the ``k``-free order-1 case). The dict also carries
    ``coeff_operands`` / ``certificate_operand`` (exponent-map operand dicts) for an
    independent re-check.

    The exactly-certifiable class (verified by the elliptic DEGREE BOUND, never on a
    converging residual — the rc61 standard) is the order-1 recurrence of a
    ``k``-free-``r_n`` elliptic-geometric term: ``rₙ_den(x)·f(n+1) − rₙ_num(x)·f(n) =
    0`` (the FT ₁₀E₉ closed form's exact n-recurrence). A genuine ``k``-dependent-``r_n``
    creative telescoping needs the additive theta lattice the multiplicative ``EllRatio``
    carrier lacks (the same boundary :func:`~srmech.amsc.elliptic_gosper.elliptic_gosper`
    hits) → ``None``.

    Exact over the modified-theta algebra; the additive residual is decided by the
    degree-bound (carrier collapse + exact-``ℚ`` :meth:`~srmech.amsc.ellbase.EllRatio.
    eval_trunc` on the theta-free residual). No float, no ``abs()`` (Class-K sign), no
    ``math`` / numpy. See the module docstring for the full pipeline + the MPM-verified
    Frenkel–Turaev reference. ``rk`` must be elliptically balanced for the row.
    """
    rn = _coerce_ratio(rn, "n-shift")
    rk = _coerce_ratio(rk, "k-shift")
    if not isinstance(max_order, int) or max_order < 0:
        raise ValueError("elliptic_zeilberger: max_order must be a non-negative int")
    if rk.is_zero:
        # a zero k-term-ratio is not a proper summand (F(n,k+1) ≡ 0) — no definite sum.
        return None

    nat = _native()
    if nat is not None:
        try:
            got = nat.elliptic_zeilberger_c(_ratio_to_form(rn), _ratio_to_form(rk),
                                            max_order)
            # The C peer ACCELERATES the positive (recurrence-found) case only: a has=1
            # result is byte-identical to the pure path AND is re-verified here by the
            # exact degree-bound check before it is trusted. A has=0 is NOT a definitive
            # "no recurrence" — it falls through to the complete pure-Python path.
            if got is not None:
                has, order, coeff_forms, cert_form = got
                # trust the C recurrence ONLY when it is within the requested order
                # (the C peer caps its ansatz independently; max_order is honoured here)
                # AND it re-verifies EXACTLY by the degree bound.
                if has and order <= max_order and order == 1 \
                        and not _depends_on(rn, _Y):
                    coeffs = [_form_to_ratio(cf) for cf in coeff_forms]
                    cert = _form_to_ratio(cert_form)
                    if _verify_order1_kfree(rn, coeffs[0], coeffs[1]):
                        return _recurrence_result(order, coeffs, cert)
        except (RuntimeError, OverflowError, ValueError):
            pass                                  # fall to the pure path

    return _elliptic_zeilberger_pure(rn, rk, max_order)


# ── pure-Python elliptic Zeilberger (the COMPLETE alternative + parity oracle) ──


def _elliptic_zeilberger_pure(rn: EllRatio, rk: EllRatio, max_order: int
                              ) -> Optional[Dict[str, object]]:
    """The exact pure-Python elliptic creative-telescoping decider (the complete
    alternative to the C peer). Certifies the exactly-decidable class — the order-1
    recurrence of a ``k``-free-``r_n`` elliptic-geometric term, verified EXACTLY by the
    degree bound — and returns honest ``None`` for the genuine ``k``-dependent creative
    telescoping (which needs the additive theta lattice). See the module docstring."""
    if max_order >= 1 and not _depends_on(rn, _Y):
        # the exactly-certifiable class: the k-free-r_n order-1 elliptic recurrence.
        got = _order1_kfree_recurrence(rn)
        if got is not None:
            return got
    # the genuine k-dependent creative telescoping (or a k-free r_n that does not
    # certify) is outside the multiplicative carrier's exact reach → honest None (never
    # a numerically-witnessed recurrence; the rc61 no-hallucination standard).
    return None
