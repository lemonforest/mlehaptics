"""srmech.apokatastasis.elliptic_jackson — the eq-5 Cₙ REDUCER: the closed-form
evaluator for the multivariable (root-system Cₙ) elliptic Jackson summation.

This is the capstone of the multivariable elliptic reduction row. Where the single-variable
₈ω₇ elliptic Jackson summation reduces to a scalar theta-quotient (the Frenkel–Turaev sum,
:func:`~srmech.apokatastasis.elliptic_wz_certificate.elliptic_wz_certificate`), the Cₙ (root-system)
elliptic Jackson summation reduces an n-FOLD sum over partitions to a theta-quotient product
— and it does so via the elliptic partial-fraction expansion
(:func:`~srmech.apokatastasis.elliptic_partial_fraction.elliptic_partial_fraction`, Rosengren Eq 1.22)
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
an exact :class:`~srmech.apokatastasis.ellbase.EllRatio`. It is the Cₙ member of the elliptic Σ-row of
the F929 dispatch table (peer of the ₈ω₇ reducer one root-system rank up), exact over the
modified-theta algebra: no float, no ``abs()`` (sign is the Class-K pin-slot via the ``Q`` /
``EllMonomial`` sign-branch). :func:`multivariate_elliptic_jackson` returns that closed form
as an ``EllRatio`` (or, with ``verify=True``, a ``{"closed_form": EllRatio, "verified":
bool}`` mapping), while :func:`cn_vwp_multisum_lhs` returns the LEFT side as a ``ThetaSum``;
both carry exact :class:`~srmech.math.q.Q` coefficients.
The parameters ``(a, b, c, d, x, q, N, n)``
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

Both sides of the identity are first-class ops (rc216): :func:`cn_vwp_multisum_lhs` builds
the LEFT-hand side (the n-fold Cₙ VWP sum, symbolically, as an exact ``ThetaSum`` — the
rc96 test oracle → rc101 symbolic-verify engine promoted public) and
:func:`multivariate_elliptic_jackson` constructs the RIGHT-hand side (the closed-form
theta-quotient product); ``(LHS − RHS).is_zero`` is the rc101 per-call proof.

Reference (MPM-verified at build from the extracted PDF): Hjalmar Rosengren, "A proof of a
multivariable elliptic summation formula conjectured by Warnaar," arXiv:math/0101073v1
[math.CA] (9 Jan 2001), Theorem 2.1 (Eq. 5) + Lemma 2.2.
"""

from __future__ import annotations

import itertools
from typing import List

from .ellbase import EllMonomial, EllRatio, Theta

__all__ = ["multivariate_elliptic_jackson", "cn_vwp_multisum_lhs"]

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


def _coerce_monomial(v, what: str, op: str = "multivariate_elliptic_jackson") -> EllMonomial:
    if isinstance(v, EllMonomial):
        return v
    raise TypeError(
        f"{op}: {what} must be an EllMonomial; got {v!r}")


def multivariate_elliptic_jackson(a, b, c, d, x, q, N: int, n: int, *,
                                  verify: bool = False):
    """Reduce the balanced Cₙ elliptic Jackson summation (Rosengren Thm 2.1, Eq 5) to its
    closed-form theta-quotient product, returned as an exact
    :class:`~srmech.apokatastasis.ellbase.EllRatio`:

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
    the partitions ``Λ_{nN}`` SYMBOLICALLY as a :class:`~srmech.apokatastasis.thetasum.ThetaSum`,
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


def cn_vwp_multisum_lhs(a, b, c, d, x, q, N: int, n: int):
    """Build the LEFT-hand side of the Cₙ elliptic Jackson summation — the n-fold Cₙ
    very-well-poised (VWP) elliptic sum over the partitions
    ``Λ_{nN} = {N ≥ λ₁ ≥ … ≥ λₙ ≥ 0}`` — SYMBOLICALLY, as an exact
    :class:`~srmech.apokatastasis.thetasum.ThetaSum` (the ADDITIVE theta carrier):

        Σ_{λ∈Λ_{nN}} ∏_{i=1}^n [θ(a·x^{2(1-i)}·q^{2λᵢ})/θ(a·x^{2(1-i)}) · q^{λᵢ}x^{2(i-1)λᵢ}]
            · ∏_{1≤i<j≤n} [θ(x^{j-i}q^{λᵢ-λⱼ})/θ(x^{j-i})
                           · θ(a·x^{2-i-j}q^{λᵢ+λⱼ})/θ(a·x^{2-i-j})
                           · (a·x^{3-i-j};q)_{λᵢ+λⱼ}(x^{j-i+1};q)_{λᵢ-λⱼ}
                             / ((aq·x^{1-i-j};q)_{λᵢ+λⱼ}(q·x^{j-i-1};q)_{λᵢ-λⱼ})]
            · (a·x^{1-n}, b, c, d, e, q^{-N}; q, x)_λ
              / (q·x^{n-1}, aq/b, aq/c, aq/d, aq/e, a·q^{N+1}; q, x)_λ,

    with the theta-Pochhammer ``(u; q)_k = ∏_{t=0}^{k-1} θ(u·qᵗ)``, the VECTOR
    theta-Pochhammer ``(u; q, x)_λ = ∏_{j=1}^n (u·x^{1-j}; q)_{λⱼ}``, and the remaining
    parameter ``e`` fixed by the balancing ``b·c·d·e·x^{n-1} = a²·q^{N+1}`` (so the sum is
    balanced by construction). By Rosengren's Theorem 2.1 this sum EQUALS the closed-form
    theta-quotient product :func:`multivariate_elliptic_jackson` constructs — subtracting
    the two and deciding ``.is_zero`` is exactly the rc101 per-call proof, now exposed as
    first-class ops on both sides of the identity.

    ``a, b, c, d, x, q`` are :class:`~srmech.apokatastasis.ellbase.EllMonomial` parameters and
    ``N`` (partition ceiling) / ``n`` (rank) are positive ints. Raises ``TypeError`` on a
    non-EllMonomial parameter and ``ValueError`` if ``N < 1`` or ``n < 1``. Each
    partition's summand is an :class:`~srmech.apokatastasis.ellbase.EllRatio` (theta-quotient; the
    per-term monomial prefactor ``∏ᵢ q^{λᵢ}·x^{2(i-1)λᵢ}`` carries sign in the Class-K
    ``EllMonomial`` coeff branch, never ``abs()``); the partitions are summed into one
    exact ``ThetaSum``. No float, no numpy, no ``math``. NOTE the term-count is
    ``C(N+n, n)`` — the build cost grows combinatorially, and DECIDING anything about the
    result (``is_zero``) has the measured feasibility frontier documented at
    :data:`_VERIFY_MAX_PARTITIONS`; the CONSTRUCTION itself is exact at any size you can
    afford to hold.

    This is the rc96 test-oracle / rc101 symbolic-verify LHS builder (the private
    ``_cn_lhs_thetasum``) promoted to a first-class public op (rc216): the exact symbolic
    twin of the independent numeric ``_cn_sum`` oracle in
    ``tests/test_multivariate_elliptic_jackson_rc96.py``.

    DISPATCHES to the native ``srmech_cn_vwp_multisum_lhs`` C peer when it is loaded.
    Because the returned object is a :class:`ThetaSum` (a SUM of ``C(N+n, n)``
    :class:`EllRatio` terms) — the rc95 ``elliptic_partial_fraction`` pattern, where the
    C peer builds the term EllRatios and the summation happens in pure carrier algebra —
    the native ThetaSum is trusted ONLY after it is rebuilt and confirmed ``==`` the
    pure-Python ThetaSum (which is the COMPLETE alternative + the C peer's parity
    oracle); otherwise the pure result is returned.

    Reference (MPM-verified at build from the extracted PDF, sha256
    be4a18685749cf05a358cf4b56170ac929940eb0d100ea550d72b1b1cab6fee9): Hjalmar Rosengren,
    "A proof of a multivariable elliptic summation formula conjectured by Warnaar",
    arXiv:math/0101073v1 [math.CA] (9 Jan 2001), Theorem 2.1, Eq. (5).
    """
    aa = _coerce_monomial(a, "a", op="cn_vwp_multisum_lhs")
    bb = _coerce_monomial(b, "b", op="cn_vwp_multisum_lhs")
    cc = _coerce_monomial(c, "c", op="cn_vwp_multisum_lhs")
    dd = _coerce_monomial(d, "d", op="cn_vwp_multisum_lhs")
    xx = _coerce_monomial(x, "x", op="cn_vwp_multisum_lhs")
    qq = _coerce_monomial(q, "q", op="cn_vwp_multisum_lhs")
    if not isinstance(N, int) or not isinstance(n, int):
        raise TypeError("cn_vwp_multisum_lhs: N and n must be int")
    if N < 1:
        raise ValueError(f"cn_vwp_multisum_lhs: N must be >= 1; got {N}")
    if n < 1:
        raise ValueError(f"cn_vwp_multisum_lhs: n must be >= 1; got {n}")
    pure = _cn_lhs_thetasum(aa, bb, cc, dd, xx, qq, N, n)
    native = _cn_vwp_multisum_lhs_c(aa, bb, cc, dd, xx, qq, N, n)
    if native is not None and native == pure:
        return native
    return pure


def _cn_vwp_multisum_lhs_c(aa: EllMonomial, bb: EllMonomial, cc: EllMonomial,
                           dd: EllMonomial, xx: EllMonomial, qq: EllMonomial,
                           N: int, n: int):
    """Dispatch the Cₙ VWP multisum LHS construction to the native
    ``srmech_cn_vwp_multisum_lhs`` C peer → the ``C(N+n, n)``-term
    :class:`~srmech.apokatastasis.thetasum.ThetaSum` (each term an :class:`EllRatio` the C peer
    builds byte-exact to the pure carrier, in the same lexicographic partition order,
    summed here identically to the pure path via :meth:`ThetaSum.from_ellratio` + ``+``),
    or ``None`` when the native symbols are absent (the caller uses the pure result).
    The interned symbol universe MUST include ``p``: the :meth:`Theta.canonicalize`
    quasi-periodicity rewrite reads/writes the nome ``p`` off ``psym`` (mirrors the same
    forcing in :func:`_multivariate_elliptic_jackson_c`)."""
    from .. import _native as _nat
    from .ellbase import _P, _ellratio_from_form, _mono_to_form
    from .thetasum import ThetaSum
    if not _nat.has_native_cn_vwp_multisum_lhs():
        return None
    syms = {_P}
    for u in (aa, bb, cc, dd, xx, qq):
        syms.update(u.exps.keys())
    sym_list = sorted(syms)
    idx = {s: i for i, s in enumerate(sym_list)}
    n_syms = len(sym_list)
    monos = [_mono_to_form(u, idx, n_syms) for u in (aa, bb, cc, dd, xx, qq)]
    forms = _nat.cn_vwp_multisum_lhs_c(
        n_syms, idx.get(_P, -1), N, n, monos[0], monos[1], monos[2], monos[3],
        monos[4], monos[5], _num_partitions(N, n), _max_thetas_per_side(N, n))
    if forms is None:
        return None
    result = ThetaSum.zero()
    for f in forms:
        result = result + ThetaSum.from_ellratio(_ellratio_from_form(f, sym_list))
    return result


def _max_thetas_per_side(N: int, n: int) -> int:
    """The per-side MAX theta count of one partition summand (mirrors the C peer's
    ``cvl_nt_max``): ``n`` diagonal args + ``(2 + 2λᵢ) ≤ (2 + 2N)`` per (i, j) pair +
    the six vector theta-Pochhammers of ``≤ n·N`` each. Sizes the native output row
    buffers. Pure integer arithmetic."""
    return n + (n * (n - 1) // 2) * (2 + 2 * N) + 6 * n * N


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
    :class:`~srmech.apokatastasis.thetasum.ThetaSum` (the ADDITIVE theta carrier). This is the exact
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
    :func:`~srmech.apokatastasis.elliptic_determinant._elliptic_cauchy_determinant_c`)."""
    from .. import _native as _nat
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
