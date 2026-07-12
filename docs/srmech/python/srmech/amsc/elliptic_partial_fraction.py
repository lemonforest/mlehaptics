"""srmech.amsc.elliptic_partial_fraction — the ELLIPTIC PARTIAL-FRACTION expansion, the
reduction ENGINE of the multivariable (root-system Cₙ) elliptic reduction row.

Where the single-variable ₈ω₇ reduces to the Weierstrass THREE-TERM relation
(:meth:`~srmech.amsc.thetasum.ThetaSum.three_term`), the multivariable Cₙ objects — the
elliptic Cauchy / Frobenius determinant (:func:`~srmech.amsc.elliptic_determinant.
elliptic_cauchy_determinant`), Warnaar's Lemma 2.2, and the Cₙ elliptic Jackson summation —
all reduce to THIS: the elliptic partial-fraction expansion (Rosengren, "Elliptic
Hypergeometric Functions," arXiv:1608.06161v3, Eq. 1.22).

────────────────────────────────────────────────────────────────────────────────────
THE ELLIPTIC PARTIAL-FRACTION EXPANSION (Rosengren Eq. 1.22)
────────────────────────────────────────────────────────────────────────────────────
For distinct ``z_1,…,z_n`` and ``y_1,…,y_n`` and the variable ``x`` (with the modified
theta ``θ(x; p) = ∏_{k≥0}(1 − x pᵏ)(1 − x⁻¹ p^{k+1})``):

    ∏_{k=1}^{n} θ(x/z_k; p)/θ(x/y_k; p)
        = 1/θ(Y/Z; p) · Σ_{j=1}^{n}
              [ ∏_{k=1}^{n} θ(y_j/z_k; p) / ∏_{k≠j} θ(y_j/y_k; p) ]
              · [ θ(x·Y/(y_j·Z); p) / θ(x/y_j; p) ],

where ``Y = y_1···y_n`` and ``Z = z_1···z_n``. The overall ``1/θ(Y/Z)`` factor is the
``1/θ(t)`` of the interpolation Proposition 1.6.1 with ``t = Y/Z`` (the multiplier that
places ``∏_k θ(x/z_k)`` in the space ``V`` of the interpolation basis). It is proved by the
elliptic Lagrange interpolation of Prop. 1.6.1 (uniqueness of a theta function by its zeros),
and it is the reduction engine "using (1.22)" that Exercise 1.6.6 (Frobenius's determinant)
and Warnaar's Cₙ summation rest on.

This op CONSTRUCTS the right-hand side — the partial-fraction expansion of the left-hand
product ``∏_k θ(x/z_k)/θ(x/y_k)`` — as an exact :class:`~srmech.amsc.thetasum.ThetaSum`
(a sum of ``n`` theta-quotient terms). It is a CONSTRUCTIVE elliptic identity op (the
multivariable peer of :meth:`ThetaSum.three_term`), exact over the modified-theta algebra:
no float, no ``abs()`` (sign is the Class-K pin-slot via the ``Q`` / ``EllMonomial``
sign-branch), no ``math`` / numpy. The identity is MPM-verified at build (Rosengren Eq. 1.22;
numerically exact n=2,3,4 in high precision, INCLUDING the ``1/θ(Y/Z)`` factor) and pinned
by ``test_elliptic_partial_fraction_rc95.py`` (the constructed sum's exact-ℚ truncated-theta
eval equals the left-hand product).

Reference (MPM-verified at build): Hjalmar Rosengren, "Elliptic Hypergeometric Functions,"
arXiv:1608.06161v3 [math.CA] (20 Jun 2017), Proposition 1.6.1 + Eq. (1.22).
"""

from __future__ import annotations

from typing import List, Sequence

from .ellbase import EllMonomial, EllRatio, Theta
from .thetasum import ThetaSum

__all__ = ["elliptic_partial_fraction"]


def _coerce_monomial(v, what: str) -> EllMonomial:
    if isinstance(v, EllMonomial):
        return v
    raise TypeError(
        f"elliptic_partial_fraction: {what} must be an EllMonomial; got {v!r}")


def elliptic_partial_fraction(x, zs: "Sequence", ys: "Sequence") -> ThetaSum:
    """Expand the elliptic product ``∏_{k=1}^n θ(x/z_k)/θ(x/y_k)`` into its partial-fraction
    sum (Rosengren Eq. 1.22), returned as an exact :class:`~srmech.amsc.thetasum.ThetaSum`:

        1/θ(Y/Z) · Σ_j [∏_k θ(y_j/z_k) / ∏_{k≠j}θ(y_j/y_k)] · [θ(x·Y/(y_j·Z)) / θ(x/y_j)],

    with ``Y = ∏ y_k`` and ``Z = ∏ z_k``. ``x`` is the variable and ``zs`` / ``ys`` are the
    two equal-length lists of distinct parameters (all :class:`EllMonomial`). Raises
    ``ValueError`` if ``len(zs) != len(ys)`` or the lists are empty. Constructive + exact over
    the modified-theta algebra (no float, no ``abs()``, no numpy). This is the reduction engine
    of the multivariable (root-system Cₙ) elliptic reduction row — see the module docstring
    for the MPM-verified reference (the ``1/θ(Y/Z)`` factor is load-bearing).

    DISPATCHES to the native ``srmech_elliptic_partial_fraction`` C peer when it is loaded.
    Because the returned object is a :class:`ThetaSum` (a SUM of ``n`` :class:`EllRatio`
    terms) — a novel pattern where the C peer builds the ``n`` term EllRatios and the
    summation happens in pure carrier algebra — the native ThetaSum is trusted ONLY after
    it is rebuilt and confirmed ``==`` the pure-Python ThetaSum (which is the COMPLETE
    alternative + the C peer's parity oracle); otherwise the pure result is returned.
    """
    xx = _coerce_monomial(x, "x")
    zl = [_coerce_monomial(v, "each z") for v in zs]
    yl = [_coerce_monomial(v, "each y") for v in ys]
    n = len(zl)
    if n == 0:
        raise ValueError("elliptic_partial_fraction: zs / ys must be non-empty")
    if len(yl) != n:
        raise ValueError(
            f"elliptic_partial_fraction: len(zs)={n} != len(ys)={len(yl)}")
    pure = _elliptic_partial_fraction_py(xx, zl, yl)
    native = _elliptic_partial_fraction_c(xx, zl, yl)
    if native is not None and native == pure:
        return native
    return pure


def _elliptic_partial_fraction_py(xx: EllMonomial, zl: "List[EllMonomial]",
                                  yl: "List[EllMonomial]") -> ThetaSum:
    """The COMPLETE pure-Python elliptic partial-fraction construction (the parity oracle
    for the C peer): the ``n``-term :class:`ThetaSum` of Rosengren Eq. 1.22. ``xx`` / ``zl``
    / ``yl`` are the already-coerced variable + equal-length parameter lists."""
    n = len(zl)
    prodz = EllMonomial.one()
    for v in zl:
        prodz = prodz * v
    prody = EllMonomial.one()
    for v in yl:
        prody = prody * v
    yz = prody * prodz.inv()                                          # Y/Z = θ(t) argument

    result = ThetaSum.zero()
    for j in range(n):
        num: "List[Theta]" = [Theta(yl[j] * zl[k].inv()) for k in range(n)]   # θ(y_j/z_k)
        num.append(Theta(xx * prody * yl[j].inv() * prodz.inv()))            # θ(x·Y/(y_j·Z))
        den: "List[Theta]" = [Theta(yl[j] * yl[k].inv())                      # θ(y_j/y_k)
                              for k in range(n) if k != j]
        den.append(Theta(xx * yl[j].inv()))                                  # θ(x/y_j)
        den.append(Theta(yz))                                                # 1/θ(Y/Z)
        result = result + ThetaSum.from_ellratio(
            EllRatio(EllMonomial.one(), num=num, den=den))
    return result


def _elliptic_partial_fraction_c(xx: EllMonomial, zl: "List[EllMonomial]",
                                 yl: "List[EllMonomial]") -> "ThetaSum | None":
    """Dispatch the partial-fraction construction to the native
    ``srmech_elliptic_partial_fraction`` C peer → the ``n``-term :class:`ThetaSum` (each
    term an :class:`EllRatio` the C peer builds byte-exact to the pure carrier, summed here
    identically to the pure path via :meth:`ThetaSum.from_ellratio` + ``+``), or ``None``
    when the native symbols are absent (the caller uses the pure result). The interned
    symbol universe MUST include ``p``: the :meth:`Theta.canonicalize` quasi-periodicity
    rewrite reads/writes the nome ``p`` off ``psym`` (mirrors the forcing in
    :func:`~srmech.amsc.elliptic_determinant._elliptic_cauchy_determinant_c`)."""
    from . import _native as _nat
    from .ellbase import _P, _ellratio_from_form, _mono_to_form
    if not _nat.has_native_elliptic_partial_fraction():
        return None
    n = len(zl)
    syms = {_P}
    syms.update(xx.exps.keys())
    for u in zl:
        syms.update(u.exps.keys())
    for u in yl:
        syms.update(u.exps.keys())
    sym_list = sorted(syms)
    idx = {s: i for i, s in enumerate(sym_list)}
    n_syms = len(sym_list)
    x_mono = _mono_to_form(xx, idx, n_syms)
    z_monos = [_mono_to_form(u, idx, n_syms) for u in zl]
    y_monos = [_mono_to_form(u, idx, n_syms) for u in yl]
    forms = _nat.elliptic_partial_fraction_c(
        n_syms, idx.get(_P, -1), n, x_mono, z_monos, y_monos)
    if forms is None:
        return None
    result = ThetaSum.zero()
    for f in forms:
        result = result + ThetaSum.from_ellratio(_ellratio_from_form(f, sym_list))
    return result
