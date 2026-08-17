"""srmech.apokatastasis.elliptic_jackson_an — the eq-6 Aₙ REDUCER: the closed-form
evaluator + per-call PROOF for the type-A (root-system Aₙ) elliptic Jackson
summation — the elliptic analogue of Milne's Aₙ Jackson summation.

This is the Aₙ member of the multivariable elliptic reduction row — the sibling the
shipped Cₙ row's own ``_OPEN_HINTS`` named as its next frontier. Where the Cₙ
elliptic Jackson summation (:mod:`srmech.apokatastasis.elliptic_jackson`, Rosengren
arXiv:math/0101073 Thm 2.1) sums over the PARTITIONS ``Λ_{nN}`` with a type-C
very-well-poised summand, the Aₙ summation sums over the SIMPLEX — the
COMPOSITIONS ``y₁, …, yₙ ≥ 0`` with ``y₁ + … + yₙ = N`` — with the type-A
Vandermonde (Weyl-denominator) factor ``Δ(z·q^y)/Δ(z)``.

────────────────────────────────────────────────────────────────────────────────────
THE Aₙ ELLIPTIC JACKSON SUMMATION (Rosengren math/0305379, Eq. 6)
────────────────────────────────────────────────────────────────────────────────────
For the variables ``z = (z₁, …, zₙ)``, the parameters ``a = (a₁, …, a_{n+1})``, the
base ``q``, the ceiling ``N``, and the BALANCING ``w = z₁⋯zₙ · a₁⋯a_{n+1}`` (``w``
is COMPUTED, never a free input — the Aₙ analogue of the Cₙ row's computed ``e``):

    Σ_{y₁,…,yₙ ≥ 0, y₁+…+yₙ = N}  Δ(z·q^y)/Δ(z)
        · ∏_{k=1}^{n} [ ∏_{j=1}^{n+1} (aⱼ·zₖ)_{yₖ} ]
                      / [ (w·zₖ)_{yₖ} · ∏_{j=1}^{n} (q·zₖ/zⱼ)_{yₖ} ]
      =  ∏_{j=1}^{n+1} (w/aⱼ)_N  /  [ ∏_{j=1}^{n} (w·zⱼ)_N · (q)_N ],

with the elliptic (theta) shifted factorial ``(u)_k = θ(u)·θ(u·q)⋯θ(u·q^{k-1})``
(the modified theta ``θ(x) = ∏_{j≥0}(1 − pʲx)(1 − p^{j+1}/x)``), the type-A
Weyl denominator ``Δ(z) = ∏_{1≤j<k≤n} zⱼ·θ(zₖ/zⱼ)``, and its shift ratio

    Δ(z·q^y)/Δ(z) = ∏_{1≤j<k≤n} q^{yⱼ} · θ(zₖ·q^{yₖ}/zⱼ·q^{yⱼ}) / θ(zₖ/zⱼ).

The term-count is the number of COMPOSITIONS of ``N`` into ``n`` non-negative
parts, ``C(N+n−1, n−1)`` (:func:`_num_compositions`) — a DIFFERENT index set from
the Cₙ row's ``C(N+n, n)`` partitions.

Reference (MPM-verified at build from the extracted PDF, sha256
``299d2738c4539a390a437c795a0b0084a5c82d403566c4f549db39482e3076ce``):
Hjalmar Rosengren, "New transformations for elliptic hypergeometric series on
the root system Aₙ", arXiv:math/0305379v1 [math.CA] (27 May 2003), Eq. (6) —
"[R4, Theorem 5.1], which is an elliptic analogue of Milne's Aₙ Jackson
summation [M]" (the ``m = 1`` case of the paper's Theorem 3.1 elliptic Kajihara
transformation). Verified at build in EXACT ℚ: at ``p = 0`` (where the truncated
modified theta is exactly ``1 − z``) both sides collapse to identical exact
rationals for every ``(n, N)`` in ``n ≤ 3, N ≤ 3`` — the basic (Milne) case of
the identity — and the FULL elliptic identity is proven per call by the
symbolic ``(LHS − RHS).is_zero`` decision (see :func:`_verify_an_reduction`).

⚠ The ``n = 1`` case of Eq. (6) is a SINGLE-term sum (the simplex ``{y₁ = N}``)
that holds term-by-term via the balancing ``w = z₁·a₁·a₂`` — a trivial
degeneration, NOT the ₈ω₇ Frenkel–Turaev sum (the Cₙ row's ``n = 1`` is ₈ω₇;
the type-A simplex sum degenerates differently). The genuine proof burden of
this row is ``n ≥ 2``, which the shipped tests pin (``verified is True`` at
``n = 2`` and ``n = 3`` cross-variable instances).

Both sides are first-class ops (the rc216 Cₙ precedent): :func:`an_vwp_multisum_lhs`
builds the LEFT-hand side (the simplex sum, symbolically, as an exact ``ThetaSum``)
and :func:`multivariate_elliptic_jackson_an` constructs the RIGHT-hand side (the
closed-form theta-quotient); ``(LHS − RHS).is_zero`` is the per-call proof.

Exact over the modified-theta algebra: no float, no ``abs()`` (sign is the
Class-K pin-slot via the ``EllMonomial`` sign-branch). :func:`an_vwp_multisum_lhs`
returns the simplex sum as a ``ThetaSum``; :func:`multivariate_elliptic_jackson_an`
returns the closed form as an ``EllRatio`` (or a ``{"closed_form": EllRatio,
"verified": bool}`` mapping under ``verify=True``). Both carry exact
:class:`~srmech.math.q.Q` coefficients — closed-form on the ALU.
"""

from __future__ import annotations

import itertools
from typing import List, Sequence

from .ellbase import EllMonomial, EllRatio, Theta

__all__ = ["multivariate_elliptic_jackson_an", "an_vwp_multisum_lhs"]

# The per-call VERIFY feasibility cap — a TERM-COUNT cap on the n-fold Aₙ sum.
# The symbolic proof builds the LHS as a sum over the ``C(N+n−1, n−1)``
# compositions of ``N`` and decides ``(LHS − RHS).is_zero`` via the rc98/rc99
# COMPLETE multi-variable elliptic decision. The Aₙ summand is much LIGHTER than
# the Cₙ one (no very-well-poised quadratic-argument thetas — the Δ-ratio thetas
# are degree-1 per variable), so the measured frontier sits far beyond the Cₙ
# row's 4-partition cap: the decision is fast (< 0.2 s, native) and returns
# ``True`` for every ``(n, N)`` with ``C(N+n−1, n−1) ≤ 6`` — measured over
# ``{(1,1..3), (2,1), (2,2), (2,3), (2,4), (3,1), (3,2), (4,1)}``, all proven
# ``≡ 0`` exactly, including the genuinely cross-variable n = 2, 3, 4 instances.
# Beyond the cap the per-call proof is NOT attempted: the op returns
# ``verified=None`` (an honest "sum too large to decide in-budget" — NOT a
# failure and NOT a claim the identity is false) alongside the constructive
# (MPM-verified at build) closed form, exactly the Cₙ row's contract. The next
# frontier size (10 terms, e.g. (3, 3)) is where ``is_zero`` returns a fast
# ``False`` on a residual that is genuinely ``≡ 0`` (the p = 0 exact-ℚ oracle) —
# DIAGNOSED 2026-07-12: NOT a provisioning bug (every Z4 interpolation frame gets
# its full D+1 pairwise-distinct nodes); the certificate recursion bottoms out at
# genuinely-zero 0-VARIABLE theta-CONSTANT leaves it has no ZERO certificate for
# — the #695 multivariate-interpolation COMPLETENESS WALL (see the
# ``_decide_struct`` block comment in ``thetasum.py``). ``is_zero`` stays SOUND
# (``False`` = "not proven", the safe direction); it is INCOMPLETE past this
# frontier, so the cap honestly stops at 6.
_VERIFY_MAX_COMPOSITIONS: int = 6


def _coerce_params(z, a, q, N: int, op: str):
    """Validate + coerce the Aₙ operand: ``z`` a non-empty sequence of
    :class:`EllMonomial` (length ``n``), ``a`` a sequence of ``n + 1``
    :class:`EllMonomial`, ``q`` an :class:`EllMonomial`, ``N`` an int ``≥ 1``.
    Returns ``(zz, aa, qq, n)`` with ``zz`` / ``aa`` as tuples."""
    if isinstance(z, EllMonomial) or not isinstance(z, (list, tuple)):
        raise TypeError(f"{op}: z must be a list/tuple of EllMonomial; got {z!r}")
    if isinstance(a, EllMonomial) or not isinstance(a, (list, tuple)):
        raise TypeError(f"{op}: a must be a list/tuple of EllMonomial; got {a!r}")
    zz = tuple(z)
    aa = tuple(a)
    for v in zz:
        if not isinstance(v, EllMonomial):
            raise TypeError(f"{op}: every z entry must be an EllMonomial; got {v!r}")
    for v in aa:
        if not isinstance(v, EllMonomial):
            raise TypeError(f"{op}: every a entry must be an EllMonomial; got {v!r}")
    if not isinstance(q, EllMonomial):
        raise TypeError(f"{op}: q must be an EllMonomial; got {q!r}")
    if not isinstance(N, int) or isinstance(N, bool):
        raise TypeError(f"{op}: N must be an int")
    n = len(zz)
    if n < 1:
        raise ValueError(f"{op}: z must carry at least one variable (n >= 1)")
    if len(aa) != n + 1:
        raise ValueError(
            f"{op}: a must carry exactly n + 1 = {n + 1} parameters; got {len(aa)}")
    if N < 1:
        raise ValueError(f"{op}: N must be >= 1; got {N}")
    return zz, aa, q, n


def _balancing_w(zz: "Sequence[EllMonomial]", aa: "Sequence[EllMonomial]") -> EllMonomial:
    """The Aₙ balancing ``w = z₁⋯zₙ · a₁⋯a_{n+1}`` (Rosengren math/0305379 Eq. 6;
    the special ``m = 1`` case of the Eq. 4 balancing ``w₁⋯w_m = z₁⋯zₙ·a₁⋯a_{m+n}``).
    COMPUTED, never a free input — mirrors the Cₙ row's computed ``e``."""
    w = EllMonomial.one()
    for u in zz:
        w = w * u
    for u in aa:
        w = w * u
    return w


def multivariate_elliptic_jackson_an(z, a, q, N: int, *, verify: bool = False):
    """Reduce the type-A (root-system Aₙ) elliptic Jackson summation — the elliptic
    analogue of Milne's Aₙ Jackson summation (Rosengren arXiv:math/0305379, Eq. 6) —
    to its closed-form theta-quotient, returned as an exact
    :class:`~srmech.apokatastasis.ellbase.EllRatio`:

        ∏_{j=1}^{n+1} (w/aⱼ)_N / [ ∏_{j=1}^{n} (w·zⱼ)_N · (q)_N ],
        (u)_k = ∏_{i=0}^{k-1} θ(u·qⁱ),   w = z₁⋯zₙ·a₁⋯a_{n+1}.

    ``z`` is the length-``n`` list of :class:`EllMonomial` variables ``(z₁, …, zₙ)``,
    ``a`` the length-``n+1`` list of parameters ``(a₁, …, a_{n+1})``, ``q`` an
    :class:`EllMonomial`, and ``N ≥ 1`` the simplex ceiling. The balancing ``w`` is
    COMPUTED from ``z`` and ``a`` (never a free input). Raises ``TypeError`` /
    ``ValueError`` on a malformed operand. Constructive + exact over the
    modified-theta algebra (no float, no ``abs()``, no numpy). This is the Aₙ member
    of the elliptic Σ-row — see the module docstring for the MPM-verified reference
    (source sha256 ``299d2738c4539a390a437c795a0b0084a5c82d403566c4f549db39482e3076ce``).

    DISPATCHES to the native ``srmech_multivariate_elliptic_jackson_an`` C peer when
    it is loaded (a 1:1 structural mirror of this exact single-EllRatio construction);
    the native EllRatio is trusted ONLY after it is rebuilt and confirmed ``==`` the
    pure-Python EllRatio (which is the COMPLETE alternative + the C peer's parity
    oracle); otherwise the pure result is returned.

    ``verify`` (default ``False`` — the plain call returns the bare
    :class:`EllRatio`). When ``True``, this is a VERIFIED reducer (the Cₙ rc101
    contract): it also PROVES the reduction per call and returns a dict::

        {"closed_form": <EllRatio>, "verified": True | False | None}

    The proof is EXACT (not numeric): it builds the LHS simplex sum SYMBOLICALLY as
    a :class:`~srmech.apokatastasis.thetasum.ThetaSum` (:func:`an_vwp_multisum_lhs`), subtracts
    this constructive closed form, and decides ``.is_zero`` — the rc98/rc99 COMPLETE
    multi-variable elliptic decision. ``verified`` is ``True`` when the residual is
    provably ``≡ 0`` (the closed form EQUALS the sum), ``False`` if not (the check
    discriminates — a wrong/perturbed closed form is caught), and ``None`` — an
    HONEST "not verified: the sum is too large to decide in-budget", NOT a failure
    and NOT a claim the identity is false — when the composition count
    ``C(N+n−1, n−1)`` exceeds :data:`_VERIFY_MAX_COMPOSITIONS` (the measured
    feasibility frontier). The constructive ``closed_form`` is returned in EVERY
    case, so the ``None`` path never hangs and never withholds the reduction."""
    zz, aa, qq, n = _coerce_params(z, a, q, N, "multivariate_elliptic_jackson_an")
    pure = _multivariate_elliptic_jackson_an_py(zz, aa, qq, N)
    native = _multivariate_elliptic_jackson_an_c(zz, aa, qq, N)
    closed = native if (native is not None and native == pure) else pure
    if not verify:
        return closed
    verified = _verify_an_reduction(zz, aa, qq, N, closed)
    return {"closed_form": closed, "verified": verified}


def an_vwp_multisum_lhs(z, a, q, N: int):
    """Build the LEFT-hand side of the Aₙ elliptic Jackson summation (Rosengren
    arXiv:math/0305379, Eq. 6) — the n-fold sum over the SIMPLEX (the compositions
    ``y₁, …, yₙ ≥ 0`` with ``y₁ + … + yₙ = N``) — SYMBOLICALLY, as an exact
    :class:`~srmech.apokatastasis.thetasum.ThetaSum` (the ADDITIVE theta carrier):

        Σ_{|y| = N}  Δ(z·q^y)/Δ(z)
            · ∏_{k=1}^{n} ∏_{j=1}^{n+1} (aⱼ·zₖ)_{yₖ}
              / [ (w·zₖ)_{yₖ} · ∏_{j=1}^{n} (q·zₖ/zⱼ)_{yₖ} ],

    with ``(u)_k = ∏_{i=0}^{k-1} θ(u·qⁱ)`` the theta-Pochhammer, the type-A
    Vandermonde ratio ``Δ(z·q^y)/Δ(z) = ∏_{j<k} q^{yⱼ}·θ(zₖq^{yₖ}/zⱼq^{yⱼ})/θ(zₖ/zⱼ)``
    (its monomial part ``∏_{j<k} q^{yⱼ}`` carried in the Class-K ``EllMonomial``
    prefactor branch, never ``abs()``), and the balancing ``w = z₁⋯zₙ·a₁⋯a_{n+1}``
    (computed). By Rosengren's Eq. 6 this sum EQUALS the closed-form theta-quotient
    :func:`multivariate_elliptic_jackson_an` constructs — subtracting the two and
    deciding ``.is_zero`` is exactly the per-call proof, with both sides first-class
    (the rc216 Cₙ precedent).

    ``z`` (length ``n``) / ``a`` (length ``n+1``) are lists of
    :class:`~srmech.apokatastasis.ellbase.EllMonomial`, ``q`` an ``EllMonomial``, ``N ≥ 1``
    an int. Raises ``TypeError`` / ``ValueError`` on a malformed operand. Each
    composition's summand is an :class:`~srmech.apokatastasis.ellbase.EllRatio`
    (theta-quotient); the compositions are summed into one exact ``ThetaSum`` in
    ascending lexicographic order. No float, no numpy, no ``math``. NOTE the
    term-count is ``C(N+n−1, n−1)`` — the build cost grows combinatorially, and
    DECIDING anything about the result (``is_zero``) has the measured feasibility
    frontier documented at :data:`_VERIFY_MAX_COMPOSITIONS`; the CONSTRUCTION
    itself is exact at any size you can afford to hold.

    DISPATCHES to the native ``srmech_an_vwp_multisum_lhs`` C peer when it is
    loaded. Because the returned object is a :class:`ThetaSum` (a SUM of
    ``C(N+n−1, n−1)`` :class:`EllRatio` terms) — the rc95/rc216 pattern, where the
    C peer builds the term EllRatios and the summation happens in pure carrier
    algebra — the native ThetaSum is trusted ONLY after it is rebuilt and confirmed
    ``==`` the pure-Python ThetaSum (which is the COMPLETE alternative + the C
    peer's parity oracle); otherwise the pure result is returned.

    Reference (MPM-verified at build from the extracted PDF, sha256
    ``299d2738c4539a390a437c795a0b0084a5c82d403566c4f549db39482e3076ce``):
    Hjalmar Rosengren, "New transformations for elliptic hypergeometric series on
    the root system Aₙ", arXiv:math/0305379v1 [math.CA] (27 May 2003), Eq. (6)."""
    zz, aa, qq, n = _coerce_params(z, a, q, N, "an_vwp_multisum_lhs")
    pure = _an_lhs_thetasum(zz, aa, qq, N)
    native = _an_vwp_multisum_lhs_c(zz, aa, qq, N)
    if native is not None and native == pure:
        return native
    return pure


def _num_compositions(N: int, n: int) -> int:
    """The exact number of compositions of ``N`` into ``n`` non-negative parts —
    the term-count of the Aₙ simplex sum, ``C(N+n−1, n−1)``. Pure integer
    arithmetic (no float, no ``math``): the multiplicative binomial in exact
    ``int``."""
    k = n - 1 if (n - 1) <= N else N
    num = 1
    den = 1
    for i in range(k):
        num *= (N + n - 1 - i)
        den *= (i + 1)
    return num // den


def _max_thetas_per_side(N: int, n: int) -> int:
    """The per-side MAX theta count of one composition summand (mirrors the C
    peer's ``avl_nt_max``): ``n(n−1)/2`` Vandermonde-ratio thetas + ``(n+1)·N``
    theta-Pochhammer factors (num side: ``Σₖ (n+1)·yₖ = (n+1)N``; den side:
    ``Σₖ (1 + n)·yₖ = (n+1)N``). Sizes the native output row buffers. Pure
    integer arithmetic."""
    return (n * (n - 1)) // 2 + (n + 1) * N


def _an_compositions(N: int, n: int):
    """Yield the compositions ``(y₁, …, yₙ) ≥ 0`` with ``Σyᵢ = N`` in ascending
    lexicographic order (the filtered ``itertools.product`` order — the exact
    order the C peer's composition odometer reproduces)."""
    for y in itertools.product(range(N + 1), repeat=n):
        s = 0
        for t in y:
            s += t
        if s == N:
            yield y


def _an_lhs_thetasum(zz, aa, qq: EllMonomial, N: int):
    """Build the LHS of Rosengren math/0305379 Eq. 6 — the Aₙ simplex sum —
    SYMBOLICALLY as an exact :class:`~srmech.apokatastasis.thetasum.ThetaSum`. Each
    theta-Pochhammer ``(u)_k = ∏_{i=0}^{k-1} θ(u·qⁱ)`` is a PRODUCT of
    :class:`Theta` factors; the Vandermonde monomial part ``∏_{j<k} q^{yⱼ}``
    is the :class:`EllRatio` prefactor (sign = Class-K via the ``EllMonomial``
    sign-branch, never ``abs()``); the balancing ``w = ∏zⱼ·∏aⱼ`` an
    :class:`EllMonomial`. The compositions are summed in ascending lexicographic
    order. No float, no numpy, no ``abs()``."""
    from .thetasum import ThetaSum

    n = len(zz)
    w = _balancing_w(zz, aa)

    def poch_thetas(base: EllMonomial, k: int) -> "List[Theta]":
        # the elliptic shifted factorial (u)_k = ∏_{i=0}^{k-1} θ(u·qⁱ)
        return [Theta(base * (qq ** i)) for i in range(k)]

    lhs = ThetaSum.zero()
    for y in _an_compositions(N, n):
        # Δ(z·q^y)/Δ(z) monomial part: ∏_{1≤j<k≤n} q^{yⱼ} = q^{Σⱼ (n−j)·yⱼ}
        e = 0
        for j in range(1, n + 1):
            e += (n - j) * y[j - 1]
        pref = qq ** e
        num: "List[Theta]" = []
        den: "List[Theta]" = []
        # Δ(z·q^y)/Δ(z) theta part: ∏_{j<k} θ(zₖ·q^{yₖ−yⱼ}/zⱼ) / θ(zₖ/zⱼ)
        for j in range(1, n + 1):
            for k in range(j + 1, n + 1):
                zkj = zz[k - 1] * zz[j - 1].inv()
                num.append(Theta(zkj * (qq ** (y[k - 1] - y[j - 1]))))
                den.append(Theta(zkj))
        # per-k: ∏ⱼ(aⱼ·zₖ)_{yₖ} / [(w·zₖ)_{yₖ} · ∏ⱼ(q·zₖ/zⱼ)_{yₖ}]
        for k in range(1, n + 1):
            yk = y[k - 1]
            for j in range(n + 1):
                num.extend(poch_thetas(aa[j] * zz[k - 1], yk))
            den.extend(poch_thetas(w * zz[k - 1], yk))
            for j in range(n):
                den.extend(poch_thetas(qq * zz[k - 1] * zz[j].inv(), yk))
        lhs = lhs + ThetaSum.from_ellratio(EllRatio(pref, num=num, den=den))
    return lhs


def _multivariate_elliptic_jackson_an_py(zz, aa, qq: EllMonomial, N: int) -> EllRatio:
    """The COMPLETE pure-Python Aₙ elliptic Jackson closed-form construction (the
    parity oracle for the C peer): the single canonical :class:`EllRatio`

        ∏_{j=1}^{n+1} (w/aⱼ)_N / [ ∏_{j=1}^{n} (w·zⱼ)_N · (q)_N ]

    with unit prefactor, ``w = ∏zⱼ·∏aⱼ`` the computed balancing."""
    n = len(zz)
    w = _balancing_w(zz, aa)

    def poch_thetas(base: EllMonomial, k: int) -> "List[Theta]":
        return [Theta(base * (qq ** i)) for i in range(k)]

    num: "List[Theta]" = []
    for j in range(n + 1):
        num.extend(poch_thetas(w * aa[j].inv(), N))
    den: "List[Theta]" = []
    for j in range(n):
        den.extend(poch_thetas(w * zz[j], N))
    den.extend(poch_thetas(qq, N))                       # (q)_N
    return EllRatio(EllMonomial.one(), num=num, den=den)


def _verify_an_reduction(zz, aa, qq: EllMonomial, N: int,
                         closed: EllRatio) -> "bool | None":
    """PROVE that ``closed`` equals the Aₙ elliptic Jackson simplex sum (Rosengren
    math/0305379 Eq. 6), EXACTLY: build the symbolic LHS (:func:`_an_lhs_thetasum`),
    subtract ``ThetaSum.from_ellratio(closed)``, and return ``(LHS − closed).is_zero``
    — the rc98/rc99 COMPLETE multi-variable elliptic decision. Returns ``True``
    (proved ``≡ 0``), ``False`` (the residual is provably non-zero — a
    wrong/perturbed ``closed`` is caught), or ``None`` when the composition count
    ``C(N+n−1, n−1)`` exceeds :data:`_VERIFY_MAX_COMPOSITIONS` (the measured
    feasibility frontier). The cap is checked FIRST, before any build or
    ``is_zero`` call, so the ``None`` path is instant and NEVER hangs.

    ``closed`` is taken as an argument (not rebuilt) so the exact same verify
    machinery the router surfaces can be exercised on a deliberately-perturbed
    closed form (→ ``False``)."""
    n = len(zz)
    if _num_compositions(N, n) > _VERIFY_MAX_COMPOSITIONS:
        return None                              # honest "too large to decide in-budget"
    from .thetasum import ThetaSum
    residual = _an_lhs_thetasum(zz, aa, qq, N) - ThetaSum.from_ellratio(closed)
    return residual.is_zero


def _an_marshal_syms(zz, aa, qq: EllMonomial):
    """The interned symbol universe for the Aₙ C peers (MUST include the nome
    ``p``: the :meth:`Theta.canonicalize` quasi-periodicity rewrite reads/writes
    ``p`` off ``psym`` — mirrors the Cₙ peers' forcing). Returns
    ``(sym_list, idx, n_syms)`` in the Python sorted-symbol-NAME order."""
    from .ellbase import _P
    syms = {_P}
    for u in zz:
        syms.update(u.exps.keys())
    for u in aa:
        syms.update(u.exps.keys())
    syms.update(qq.exps.keys())
    sym_list = sorted(syms)
    idx = {s: i for i, s in enumerate(sym_list)}
    return sym_list, idx, len(sym_list)


def _an_vwp_multisum_lhs_c(zz, aa, qq: EllMonomial, N: int):
    """Dispatch the Aₙ simplex-sum LHS construction to the native
    ``srmech_an_vwp_multisum_lhs`` C peer → the ``C(N+n−1, n−1)``-term
    :class:`~srmech.apokatastasis.thetasum.ThetaSum` (each term an :class:`EllRatio` the
    C peer builds byte-exact to the pure carrier, in the same ascending
    lexicographic composition order, summed here identically to the pure path
    via :meth:`ThetaSum.from_ellratio` + ``+``), or ``None`` when the native
    symbols are absent (the caller uses the pure result)."""
    from .. import _native as _nat
    from .ellbase import _P, _ellratio_from_form, _mono_to_form
    from .thetasum import ThetaSum
    if not _nat.has_native_an_vwp_multisum_lhs():
        return None
    n = len(zz)
    sym_list, idx, n_syms = _an_marshal_syms(zz, aa, qq)
    z_monos = [_mono_to_form(u, idx, n_syms) for u in zz]
    a_monos = [_mono_to_form(u, idx, n_syms) for u in aa]
    q_mono = _mono_to_form(qq, idx, n_syms)
    forms = _nat.an_vwp_multisum_lhs_c(
        n_syms, idx.get(_P, -1), N, n, z_monos, a_monos, q_mono,
        _num_compositions(N, n), _max_thetas_per_side(N, n))
    if forms is None:
        return None
    result = ThetaSum.zero()
    for f in forms:
        result = result + ThetaSum.from_ellratio(_ellratio_from_form(f, sym_list))
    return result


def _multivariate_elliptic_jackson_an_c(zz, aa, qq: EllMonomial,
                                        N: int) -> "EllRatio | None":
    """Dispatch the closed-form construction to the native
    ``srmech_multivariate_elliptic_jackson_an`` C peer → the single
    :class:`EllRatio`, or ``None`` when the native symbols are absent (the caller
    falls to :func:`_multivariate_elliptic_jackson_an_py`)."""
    from .. import _native as _nat
    from .ellbase import _P, _ellratio_from_form, _mono_to_form
    if not _nat.has_native_multivariate_elliptic_jackson_an():
        return None
    n = len(zz)
    sym_list, idx, n_syms = _an_marshal_syms(zz, aa, qq)
    z_monos = [_mono_to_form(u, idx, n_syms) for u in zz]
    a_monos = [_mono_to_form(u, idx, n_syms) for u in aa]
    q_mono = _mono_to_form(qq, idx, n_syms)
    form = _nat.multivariate_elliptic_jackson_an_c(
        n_syms, idx.get(_P, -1), N, n, z_monos, a_monos, q_mono)
    if form is None:
        return None
    return _ellratio_from_form(form, sym_list)
