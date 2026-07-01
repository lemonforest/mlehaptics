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

from typing import List

from .ellbase import EllMonomial, EllRatio, Theta

__all__ = ["multivariate_elliptic_jackson"]


def _coerce_monomial(v, what: str) -> EllMonomial:
    if isinstance(v, EllMonomial):
        return v
    raise TypeError(
        f"multivariate_elliptic_jackson: {what} must be an EllMonomial; got {v!r}")


def multivariate_elliptic_jackson(a, b, c, d, x, q, N: int, n: int) -> EllRatio:
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
    if native is not None and native == pure:
        return native
    return pure


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
