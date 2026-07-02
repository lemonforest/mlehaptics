"""srmech.amsc.elliptic_jackson — the eq-5 Cₙ REDUCER: the closed-form
evaluator for the multivariable (root-system Cₙ) elliptic Jackson summation.

This is the capstone of the multivariable elliptic reduction row. Where the single-variable
₈ω₇ elliptic Jackson summation reduces to a scalar theta-quotient (the Frenkel–Turaev sum,
:func:`~srmech.amsc.elliptic_wz_certificate.elliptic_wz_certificate`), the Cₙ (root-system)
elliptic Jackson summation reduces an n-FOLD sum over partitions to a theta-quotient product
— and it does so via the elliptic partial-fraction expansion
(:func:`~srmech.amsc.elliptic_partial_fraction.elliptic_partial_fraction`, Rosengren Eq 1.22)
and Warnaar's determinant / Lemma 2.2 as the inductive engine.

────────────────────────────────────────────────────────────────────────────────────
THE Cₙ ELLIPTIC JACKSON SUMMATION (Rosengren Theorem 2.1)
────────────────────────────────────────────────────────────────────────────────────
For the balanced Cₙ very-well-poised elliptic sum over partitions
``Λ_{nN} = {N ≥ λ_1 ≥ … ≥ λ_n ≥ 0}`` with the balancing ``b·c·d·e·x^{n-1} = a²·q^{N+1}``
(Rosengren, "A multivariable elliptic summation formula," arXiv:math/0101073, Theorem 2.1,
Eq. 5), the sum equals the theta-quotient product

    Σ_{λ ∈ Λ_{nN}} [ Cₙ very-well-poised summand ]
        = (aq, aq/bc, aq/bd, aq/cd; q, x)_{Nⁿ}
          / (aq/b, aq/c, aq/d, aq/bcd; q, x)_{Nⁿ},

with the VECTOR elliptic Pochhammer

    (u; q, x)_{Nⁿ} = ∏_{j=1}^{n} ∏_{i=0}^{N-1} θ(u·x^{1-j}·qⁱ; p),   θ = the modified theta.

The single-variable ``n = 1`` case is the Frenkel–Turaev ₈ω₇ sum. The proof is by induction
on ``N`` via Warnaar's Lemma 2.2 (the Cₙ binary-sum evaluation, ``a²q^{3-n} = bcde``), which
is itself a determinant evaluation reducing through the elliptic partial-fraction expansion.

This op CONSTRUCTS the closed-form right-hand side — the reduced theta-quotient product — as
an exact :class:`~srmech.amsc.ellbase.EllRatio`. It is the Cₙ member of the elliptic Σ-row of
the F929 dispatch table (peer of the ₈ω₇ reducer one root-system rank up), exact over the
modified-theta algebra: no float, no ``abs()`` (sign is the Class-K pin-slot via the ``Q`` /
``EllMonomial`` sign-branch), no ``math`` / numpy. The parameters ``(a, b, c, d, x, q, N, n)``
define a BALANCED sum (``e`` is fixed by ``e = a²q^{N+1}/(bcd·x^{n-1})``, so the balancing
holds by construction); the identity is MPM-verified at build (Rosengren Thm 2.1 Eq 5;
numerically exact n=2,3 / small N in high precision) and the reduction (the n-fold sum equals
this closed form) + Warnaar's Lemma 2.2 engine are pinned by
``test_multivariate_elliptic_jackson_rc96.py``.

Exact SELF-verification of the reduction (summing the n-fold Cₙ sum symbolically and
``is_zero``-checking it against this closed form) requires a MULTI-VARIABLE elliptic
``is_zero`` (the partial-fraction-reducing n-variable decision) — the documented
exact-verification frontier of this row; it is NOT required for this constructive evaluator,
which delivers the exact MPM-verified closed form for the full Theorem 2.1 family.

Reference (MPM-verified at build): Hjalmar Rosengren, "A multivariable elliptic summation
formula," arXiv:math/0101073 [math.CA], Theorem 2.1 (Eq. 5) + Lemma 2.2.
"""

from __future__ import annotations

import itertools
from typing import List

from .ellbase import EllMonomial, EllRatio, Theta

__all__ = ["multivariate_elliptic_jackson"]

# The per-call VERIFY feasibility cap — a TERM-COUNT cap on the n-fold Cₙ sum.
# The symbolic proof builds the LHS as a sum over the ``C(N+n, n)`` partitions
# ``Λ_{nN} = {N ≥ λ₁ ≥ … ≥ λₙ ≥ 0}`` and decides ``(LHS − RHS).is_zero`` via the
# rc98/rc99 COMPLETE multi-variable elliptic decision. That decision is the exact
# STRUCTURAL elliptic-interpolation recursion (Rosengren Prop 1.6.1) whose cost
# grows super-exponentially with the residual's per-variable theta-degree — which
# in turn grows with BOTH the rank ``n`` (cross-variable root-system coupling) and
# the ceiling ``N`` (the λ-range → q/x powers). Empirically (measured against the
# rc99 native interpolation peer AND the pure-Python oracle) the decision is fast
# (< 0.5 s) for every ``(n, N)`` with ``C(N+n, n) ≤ 4`` — the set
# ``{(1,1), (1,2), (1,3), (2,1), (3,1)}`` — and INFEASIBLE beyond it: the native
# peer declines on ``SRMECH_ERR_OVERFLOW`` (a caller-arena / coefficient-cap trip;
# a cap large enough to decide needs multi-GB workspace) and the pure oracle does
# not finish in > 9 min (e.g. n=2/N=2 has a residual of interpolation-degree ~74
# in q). So the honest per-call proof is capped at the measured frontier; a sum
# above it returns ``verified=None`` ("not verified — sum too large to decide
# in-budget"), NEVER hanging. The constructive closed form (the MPM-verified
# Rosengren Thm 2.1 RHS, proven at build for the whole Theorem 2.1 family) is
# returned either way — the ``None`` is an honest "per-call proof not attempted",
# NOT a failure and NOT a claim the identity is false.
_VERIFY_MAX_PARTITIONS: int = 4


def _coerce_monomial(v, what: str) -> EllMonomial:
    if isinstance(v, EllMonomial):
        return v
    raise TypeError(
        f"multivariate_elliptic_jackson: {what} must be an EllMonomial; got {v!r}")


def multivariate_elliptic_jackson(a, b, c, d, x, q, N: int, n: int, *,
                                  verify: bool = False):
    """Reduce the balanced Cₙ elliptic Jackson summation (Rosengren Thm 2.1, Eq 5) to its
    closed-form theta-quotient product, returned as an exact
    :class:`~srmech.amsc.ellbase.EllRatio`:

        (aq, aq/bc, aq/bd, aq/cd; q, x)_{Nⁿ} / (aq/b, aq/c, aq/d, aq/bcd; q, x)_{Nⁿ},
        (u; q, x)_{Nⁿ} = ∏_{j=1}^n ∏_{i=0}^{N-1} θ(u·x^{1-j}·qⁱ).

    ``a, b, c, d, x, q`` are :class:`EllMonomial` parameters and ``N`` (partition ceiling) and
    ``n`` (rank / number of variables) are positive ints. The remaining parameter ``e`` is
    fixed by the balancing ``e = a²q^{N+1}/(bcd·x^{n-1})`` (so the sum is balanced by
    construction). Raises ``ValueError`` if ``N < 1`` or ``n < 1``. Constructive + exact over
    the modified-theta algebra (no float, no ``abs()``, no numpy). This is the capstone Cₙ
    member of the elliptic Σ-row — see the module docstring for the MPM-verified reference and
    the exact-verification frontier.

    DISPATCHES to the native ``srmech_multivariate_elliptic_jackson`` C peer when it is
    loaded (a 1:1 structural mirror of this exact single-EllRatio construction — the peer of
    rc94's ``srmech_elliptic_cauchy_determinant``); the native EllRatio is trusted ONLY after
    it is rebuilt and confirmed ``==`` the pure-Python EllRatio (which is the COMPLETE
    alternative + the C peer's parity oracle); otherwise the pure result is returned.

    ``verify`` (default ``False`` — back-compat: the plain call returns the bare
    :class:`EllRatio`). When ``True``, this becomes a VERIFIED reducer (rc101): it also
    PROVES the reduction per call and returns a dict::

        {"closed_form": <EllRatio>, "verified": True | False | None}

    The proof is EXACT (not numeric): it builds the LHS n-fold Cₙ very-well-poised sum over
    the partitions ``Λ_{nN}`` SYMBOLICALLY as a :class:`~srmech.amsc.thetasum.ThetaSum`,
    subtracts this constructive closed form, and calls ``.is_zero`` — the rc98/rc99 COMPLETE
    multi-variable elliptic decision (structural elliptic interpolation). ``verified`` is
    ``True`` when the residual is provably ``≡ 0`` (the closed form EQUALS the sum), ``False``
    if not (the check discriminates — a wrong/perturbed closed form is caught). It is
    ``None`` — an HONEST "not verified: the sum is too large to decide in-budget", NOT a
    failure and NOT a claim the identity is false — when the term-count of the n-fold sum
    (``C(N+n, n)`` partitions) exceeds :data:`_VERIFY_MAX_PARTITIONS`, the measured
    feasibility frontier of the ``is_zero`` decision (see that constant's note). The
    constructive ``closed_form`` (the MPM-verified Thm 2.1 RHS) is returned in EVERY case, so
    the ``None`` path never hangs and never withholds the reduction. This upgrades the Cₙ
    reducer from CONSTRUCTIVE (rc96) to per-call VERIFIED using the rc98/rc99 complete
    ``ThetaSum.is_zero`` — the F929 discipline (a reduction is claimed only when proven) made
    executable one root-system rank above the ₈ω₇ ``elliptic_wz_certificate``.
    """
    aa = _coerce_monomial(a, "a")
    bb = _coerce_monomial(b, "b")
    cc = _coerce_monomial(c, "c")
    dd = _coerce_monomial(d, "d")
    xx = _coerce_monomial(x, "x")
    qq = _coerce_monomial(q, "q")
    if not isinstance(N, int) or not isinstance(n, int):
        raise TypeError("multivariate_elliptic_jackson: N and n must be int")
    if N < 1:
        raise ValueError(f"multivariate_elliptic_jackson: N must be >= 1; got {N}")
    if n < 1:
        raise ValueError(f"multivariate_elliptic_jackson: n must be >= 1; got {n}")
    pure = _multivariate_elliptic_jackson_py(aa, bb, cc, dd, xx, qq, N, n)
    native = _multivariate_elliptic_jackson_c(aa, bb, cc, dd, xx, qq, N, n)
    closed = native if (native is not None and native == pure) else pure
    if not verify:
        return closed
    verified = _verify_cn_reduction(aa, bb, cc, dd, xx, qq, N, n, closed)
    return {"closed_form": closed, "verified": verified}


def _num_partitions(N: int, n: int) -> int:
    """The exact number of partitions in ``Λ_{nN} = {N ≥ λ₁ ≥ … ≥ λₙ ≥ 0}`` — the
    term-count of the n-fold Cₙ sum, ``C(N+n, n)``. Pure integer arithmetic (no float,
    no ``math``): the multiplicative binomial, computed in exact ``int``."""
    k = n if n <= N else N
    num = 1
    den = 1
    for i in range(k):
        num *= (N + n - i)
        den *= (i + 1)
    return num // den


def _cn_lhs_thetasum(aa: EllMonomial, bb: EllMonomial, cc: EllMonomial, dd: EllMonomial,
                     xx: EllMonomial, qq: EllMonomial, N: int, n: int):
    """Build the LHS of Rosengren Thm 2.1 — the n-fold Cₙ very-well-poised elliptic sum over
    the partitions ``Λ_{nN} = {N ≥ λ₁ ≥ … ≥ λₙ ≥ 0}`` — SYMBOLICALLY as an exact
    :class:`~srmech.amsc.thetasum.ThetaSum` (the ADDITIVE theta carrier). This is the exact
    symbolic twin of the NUMERIC ``_cn_sum`` oracle in
    ``tests/test_multivariate_elliptic_jackson_rc96.py`` (same summand structure, built over
    the modified-theta algebra instead of an ℚ eval): each theta-Pochhammer
    ``(u; q, p)_k = ∏_{i=0}^{k-1} θ(u·qⁱ)`` is a PRODUCT of :class:`Theta` factors (not the
    ``(1-u)…`` numeric form); ``_E(z) = θ(z)`` a single :class:`Theta`; the balancing
    ``e = a²·q^{N+1}/(b·c·d·x^{n-1})`` an :class:`EllMonomial`; the per-term monomial
    prefactor ``∏_i q^{λᵢ}·x^{2(i-1)λᵢ}`` folded into the :class:`EllRatio` prefactor (sign =
    Class-K via the ``EllMonomial`` sign-branch, never ``abs()``). Each partition's summand is
    an :class:`EllRatio` (theta-quotient); the partitions are summed into one ``ThetaSum``
    over their common denominator. No float, no numpy, no ``abs()``."""
    from .thetasum import ThetaSum

    a, b, c, d, x, q = aa, bb, cc, dd, xx, qq
    e = (a ** 2) * (q ** (N + 1)) * (b * c * d * (x ** (n - 1))).inv()

    def poch_thetas(base: EllMonomial, k: int) -> "List[Theta]":
        # the elliptic shifted factorial (u; q, p)_k = ∏_{i=0}^{k-1} θ(u·qⁱ)
        return [Theta(base * (q ** i)) for i in range(k)]

    def vpoch_thetas(u: EllMonomial, lam) -> "List[Theta]":
        out: "List[Theta]" = []
        for j in range(1, n + 1):
            out.extend(poch_thetas(u * (x ** (1 - j)), lam[j - 1]))
        return out

    lhs = ThetaSum.zero()
    for lam in itertools.product(range(N + 1), repeat=n):
        if not all(lam[t] >= lam[t + 1] for t in range(n - 1)):
            continue                                   # only N ≥ λ₁ ≥ … ≥ λₙ ≥ 0
        pref = EllMonomial.one()
        num: "List[Theta]" = []
        den: "List[Theta]" = []
        # diagonal (i) part
        for i in range(1, n + 1):
            li = lam[i - 1]
            num.append(Theta(a * (x ** (2 * (1 - i))) * (q ** (2 * li))))
            den.append(Theta(a * (x ** (2 * (1 - i)))))
            pref = pref * (q ** li) * (x ** (2 * (i - 1) * li))
        # off-diagonal (i<j) root-system coupling
        for i in range(1, n + 1):
            for j in range(i + 1, n + 1):
                li, lj = lam[i - 1], lam[j - 1]
                num.append(Theta((x ** (j - i)) * (q ** (li - lj))))
                den.append(Theta(x ** (j - i)))
                num.append(Theta(a * (x ** (2 - i - j)) * (q ** (li + lj))))
                den.append(Theta(a * (x ** (2 - i - j))))
                num.extend(poch_thetas(a * (x ** (3 - i - j)), li + lj))
                num.extend(poch_thetas(x ** (j - i + 1), li - lj))
                den.extend(poch_thetas(a * q * (x ** (1 - i - j)), li + lj))
                den.extend(poch_thetas(q * (x ** (j - i - 1)), li - lj))
        # the six very-well-poised vector theta-Pochhammer bases
        num_bases = [a * (x ** (1 - n)), b, c, d, e, q ** (-N)]
        den_bases = [q * (x ** (n - 1)), a * q * b.inv(), a * q * c.inv(),
                     a * q * d.inv(), a * q * e.inv(), a * (q ** (N + 1))]
        for u in num_bases:
            num.extend(vpoch_thetas(u, lam))
        for u in den_bases:
            den.extend(vpoch_thetas(u, lam))
        lhs = lhs + ThetaSum.from_ellratio(EllRatio(pref, num=num, den=den))
    return lhs


def _verify_cn_reduction(aa: EllMonomial, bb: EllMonomial, cc: EllMonomial, dd: EllMonomial,
                         xx: EllMonomial, qq: EllMonomial, N: int, n: int,
                         closed: EllRatio) -> "bool | None":
    """PROVE that ``closed`` equals the n-fold Cₙ elliptic Jackson sum (Rosengren Thm 2.1),
    EXACTLY: build the symbolic LHS (:func:`_cn_lhs_thetasum`), subtract
    ``ThetaSum.from_ellratio(closed)``, and return ``(LHS − closed).is_zero`` — the rc98/rc99
    COMPLETE multi-variable elliptic decision. Returns ``True`` (proved ``≡ 0``), ``False``
    (the residual is provably non-zero — a wrong/perturbed ``closed`` is caught), or ``None``
    when the sum's term-count ``C(N+n, n)`` exceeds :data:`_VERIFY_MAX_PARTITIONS` (the
    measured feasibility frontier — see that constant). The cap is checked FIRST, before any
    build or ``is_zero`` call, so the ``None`` path is instant and NEVER hangs.

    ``closed`` is taken as an argument (not rebuilt) so the exact same verify machinery
    the router surfaces can be exercised on a deliberately-perturbed closed form (→ ``False``).
    """
    if _num_partitions(N, n) > _VERIFY_MAX_PARTITIONS:
        return None                                    # honest "too large to decide in-budget"
    from .thetasum import ThetaSum
    residual = _cn_lhs_thetasum(aa, bb, cc, dd, xx, qq, N, n) - ThetaSum.from_ellratio(closed)
    return residual.is_zero


def _multivariate_elliptic_jackson_py(aa: EllMonomial, bb: EllMonomial, cc: EllMonomial,
                                      dd: EllMonomial, xx: EllMonomial, qq: EllMonomial,
                                      N: int, n: int) -> EllRatio:
    """The COMPLETE pure-Python Cₙ elliptic Jackson closed-form construction (the parity
    oracle for the C peer): the single canonical :class:`EllRatio`. The parameters are the
    already-coerced :class:`EllMonomial` inputs + the positive ints ``N`` / ``n``."""
    def vpoch_thetas(u: EllMonomial) -> "List[Theta]":
        # (u; q, x)_{Nⁿ} = ∏_{j=1}^n ∏_{i=0}^{N-1} θ(u·x^{1-j}·qⁱ)
        return [Theta(u * (xx ** (1 - j)) * (qq ** i))
                for j in range(1, n + 1) for i in range(N)]

    aq = aa * qq
    num_bases = [aq, aq * (bb * cc).inv(), aq * (bb * dd).inv(), aq * (cc * dd).inv()]
    den_bases = [aq * bb.inv(), aq * cc.inv(), aq * dd.inv(), aq * (bb * cc * dd).inv()]
    num: "List[Theta]" = [th for u in num_bases for th in vpoch_thetas(u)]
    den: "List[Theta]" = [th for u in den_bases for th in vpoch_thetas(u)]
    return EllRatio(EllMonomial.one(), num=num, den=den)


def _multivariate_elliptic_jackson_c(aa: EllMonomial, bb: EllMonomial, cc: EllMonomial,
                                     dd: EllMonomial, xx: EllMonomial, qq: EllMonomial,
                                     N: int, n: int) -> "EllRatio | None":
    """Dispatch the closed-form construction to the native
    ``srmech_multivariate_elliptic_jackson`` C peer → the single :class:`EllRatio`, or
    ``None`` when the native symbols are absent (the caller falls to
    :func:`_multivariate_elliptic_jackson_py`). The interned symbol universe MUST include
    ``p``: the :meth:`Theta.canonicalize` quasi-periodicity rewrite reads/writes the nome
    ``p`` off ``psym`` (mirrors the same forcing in
    :func:`~srmech.amsc.elliptic_determinant._elliptic_cauchy_determinant_c`)."""
    from . import _native as _nat
    from .ellbase import _P, _ellratio_from_form, _mono_to_form
    if not _nat.has_native_multivariate_elliptic_jackson():
        return None
    syms = {_P}
    for u in (aa, bb, cc, dd, xx, qq):
        syms.update(u.exps.keys())
    sym_list = sorted(syms)
    idx = {s: i for i, s in enumerate(sym_list)}
    n_syms = len(sym_list)
    a_mono = _mono_to_form(aa, idx, n_syms)
    b_mono = _mono_to_form(bb, idx, n_syms)
    c_mono = _mono_to_form(cc, idx, n_syms)
    d_mono = _mono_to_form(dd, idx, n_syms)
    x_mono = _mono_to_form(xx, idx, n_syms)
    q_mono = _mono_to_form(qq, idx, n_syms)
    form = _nat.multivariate_elliptic_jackson_c(
        n_syms, idx.get(_P, -1), N, n, a_mono, b_mono, c_mono, d_mono, x_mono, q_mono)
    if form is None:
        return None
    return _ellratio_from_form(form, sym_list)
