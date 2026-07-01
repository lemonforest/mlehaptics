"""srmech.amsc.elliptic_determinant — the ELLIPTIC-DETERMINANT primitive: Frobenius's
elliptic Cauchy determinant evaluation, the exact closed form of
``det_{1≤i,j≤n}[θ(t·x_i·y_j; p)/θ(x_i·y_j; p)]`` as a single theta-quotient.

This is the foundation of the multivariable (root-system Cₙ) elliptic reduction row: the
elliptic Cauchy / Frobenius determinant is the canonical exact elliptic determinant, and
Warnaar's determinant evaluation (the engine of the Cₙ elliptic Jackson summation, the
multivariable ₈ω₇ analogue) is a member of the same family. Where the single-variable ₈ω₇
reduces to the Weierstrass THREE-TERM relation (:meth:`~srmech.amsc.thetasum.ThetaSum.
three_term`), the multivariable Cₙ objects reduce to the elliptic PARTIAL-FRACTION
expansion (Rosengren eq. 1.22) and this DETERMINANT — a genuinely larger primitive.

────────────────────────────────────────────────────────────────────────────────────
THE FROBENIUS ELLIPTIC CAUCHY DETERMINANT (the closed form this op constructs)
────────────────────────────────────────────────────────────────────────────────────
For distinct ``x_1,…,x_n`` and ``y_1,…,y_n`` and a parameter ``t`` (Rosengren, "Elliptic
Hypergeometric Functions," arXiv:1608.06161v3, Exercise 1.6.6; classically Frobenius 1882):

    det_{1≤i,j≤n} [ θ(t·x_i·y_j; p) / θ(x_i·y_j; p) ]
        = θ(t; p)^{n-1} · θ(t·x_1···x_n·y_1···y_n; p)
          · ∏_{1≤i<j≤n} [ x_j·y_j · θ(x_i/x_j; p)·θ(y_i/y_j; p) ]
          / ∏_{i,j=1}^{n} θ(x_i·y_j; p),

with the modified theta ``θ(x; p) = ∏_{k≥0}(1 − x pᵏ)(1 − x⁻¹ p^{k+1})``. It is proved
"using (1.22)" — the elliptic partial-fraction expansion — the same reduction engine the
Cₙ elliptic Jackson summation rests on. At ``n = 1`` it is the trivial identity
``θ(t x_1 y_1)/θ(x_1 y_1)``.

This op CONSTRUCTS the closed form (the right-hand side) as an exact
:class:`~srmech.amsc.ellbase.EllRatio` — a single theta-quotient with the exact
``EllMonomial`` prefactor ``∏_{i<j} x_j y_j`` and the theta numerator / denominator above.
It is a CONSTRUCTIVE elliptic identity op (the peer of :meth:`ThetaSum.three_term`), exact
over the modified-theta algebra: no float, no ``abs()`` (sign is the Class-K pin-slot via
the ``Q`` / ``EllMonomial`` sign-branch), no ``math`` / numpy. The identity is MPM-verified
at build (Rosengren Ex 1.6.6; numerically exact n=2,3,4 in high precision) and pinned by
``test_elliptic_determinant_rc94.py`` (the constructed closed form's exact-ℚ truncated-theta
eval equals the determinant of the theta matrix, computed by cofactor expansion).

Reference (MPM-verified at build): Hjalmar Rosengren, "Elliptic Hypergeometric Functions,"
arXiv:1608.06161v3 [math.CA] (20 Jun 2017), Exercise 1.6.6 (Frobenius's determinant
evaluation), proved via the elliptic partial-fraction expansion Eq. (1.22).
"""

from __future__ import annotations

from typing import List, Sequence

from .ellbase import EllMonomial, EllRatio, Theta

__all__ = ["elliptic_cauchy_determinant"]


def _coerce_monomial(v, what: str) -> EllMonomial:
    """Coerce a variable / parameter to an :class:`~srmech.amsc.ellbase.EllMonomial`."""
    if isinstance(v, EllMonomial):
        return v
    raise TypeError(
        f"elliptic_cauchy_determinant: {what} must be an EllMonomial; got {v!r}")


def elliptic_cauchy_determinant(t, xs: "Sequence", ys: "Sequence") -> EllRatio:
    """Evaluate the elliptic Cauchy (Frobenius) determinant
    ``det_{1≤i,j≤n}[θ(t·x_i·y_j)/θ(x_i·y_j)]`` to its exact closed form, returned as an
    :class:`~srmech.amsc.ellbase.EllRatio` (Rosengren Ex 1.6.6):

        θ(t)^{n-1} · θ(t·∏x·∏y) · ∏_{i<j}[x_j·y_j·θ(x_i/x_j)·θ(y_i/y_j)] / ∏_{i,j}θ(x_i·y_j).

    ``t`` is a parameter and ``xs`` / ``ys`` are the two equal-length lists of distinct
    variables (all :class:`EllMonomial`). Raises ``ValueError`` if ``len(xs) != len(ys)``
    or the lists are empty. Constructive + exact over the modified-theta algebra (no float,
    no ``abs()``, no numpy); see the module docstring for the MPM-verified reference. This
    is the foundation of the multivariable-elliptic (root-system Cₙ) reduction row.

    DISPATCHES to the native ``srmech_elliptic_cauchy_determinant`` C peer when it is
    loaded (a 1:1 structural mirror of this exact construction — the C EllRatio EQUALS the
    Python EllRatio byte-for-byte, so it is trusted unconditionally); otherwise the
    pure-Python :func:`_elliptic_cauchy_determinant_py` body builds it (it is the COMPLETE
    alternative + the C peer's parity oracle).
    """
    tt = _coerce_monomial(t, "t")
    xl = [_coerce_monomial(v, "each x") for v in xs]
    yl = [_coerce_monomial(v, "each y") for v in ys]
    n = len(xl)
    if n == 0:
        raise ValueError("elliptic_cauchy_determinant: xs / ys must be non-empty")
    if len(yl) != n:
        raise ValueError(
            f"elliptic_cauchy_determinant: len(xs)={n} != len(ys)={len(yl)}")
    c = _elliptic_cauchy_determinant_c(tt, xl, yl)
    if c is not None:
        return c
    return _elliptic_cauchy_determinant_py(tt, xl, yl)


def _elliptic_cauchy_determinant_py(tt: EllMonomial, xl: "List[EllMonomial]",
                                    yl: "List[EllMonomial]") -> EllRatio:
    """The COMPLETE pure-Python Frobenius closed-form construction (the parity oracle for
    the C peer): the single canonical :class:`EllRatio`. ``tt`` / ``xl`` / ``yl`` are the
    already-coerced parameter + equal-length variable lists."""
    n = len(xl)
    prodx = EllMonomial.one()
    for v in xl:
        prodx = prodx * v
    prody = EllMonomial.one()
    for v in yl:
        prody = prody * v

    num: "List[Theta]" = [Theta(tt) for _ in range(n - 1)]           # θ(t)^{n-1}
    num.append(Theta(tt * prodx * prody))                            # θ(t·∏x·∏y)
    pref = EllMonomial.one()
    for i in range(n):
        for j in range(i + 1, n):
            num.append(Theta(xl[i] * xl[j].inv()))                   # θ(x_i/x_j)
            num.append(Theta(yl[i] * yl[j].inv()))                   # θ(y_i/y_j)
            pref = pref * xl[j] * yl[j]                              # · x_j·y_j
    den: "List[Theta]" = [Theta(xl[i] * yl[j]) for i in range(n) for j in range(n)]
    return EllRatio(pref, num=num, den=den)


def _elliptic_cauchy_determinant_c(tt: EllMonomial, xl: "List[EllMonomial]",
                                   yl: "List[EllMonomial]") -> "EllRatio | None":
    """Dispatch the closed-form construction to the native
    ``srmech_elliptic_cauchy_determinant`` C peer → the single :class:`EllRatio`, or
    ``None`` when the native symbols are absent (the caller falls to
    :func:`_elliptic_cauchy_determinant_py`). The interned symbol universe MUST include
    ``p``: the :meth:`Theta.canonicalize` quasi-periodicity rewrite reads/writes the nome
    ``p`` off ``psym`` (mirrors the same forcing in :meth:`EllRatio._is_elliptic_c` /
    :func:`elliptic_lagrange_basis`)."""
    from . import _native as _nat
    from .ellbase import _P, _ellratio_from_form, _mono_to_form
    if not _nat.has_native_elliptic_cauchy_determinant():
        return None
    n = len(xl)
    syms = {_P}
    syms.update(tt.exps.keys())
    for u in xl:
        syms.update(u.exps.keys())
    for u in yl:
        syms.update(u.exps.keys())
    sym_list = sorted(syms)
    idx = {s: i for i, s in enumerate(sym_list)}
    n_syms = len(sym_list)
    t_mono = _mono_to_form(tt, idx, n_syms)
    x_monos = [_mono_to_form(u, idx, n_syms) for u in xl]
    y_monos = [_mono_to_form(u, idx, n_syms) for u in yl]
    form = _nat.elliptic_cauchy_determinant_c(
        n_syms, idx.get(_P, -1), n, t_mono, x_monos, y_monos)
    if form is None:
        return None
    return _ellratio_from_form(form, sym_list)
