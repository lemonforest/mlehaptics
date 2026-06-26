"""srmech.amsc.elliptic_recurrence — the ELLIPTIC Σ-row ORDER-1 RECURRENCE op for the
Frenkel–Turaev ₈ω₇ summation, a STRUCTURAL (beat-decomposition) finder that builds the
order-1 recurrence coefficient ``ρ(n)`` from the elementary symmetric functions of the
free parameters — NOT a coefficient nullspace solve (which is provably dead for the
elliptic case; the anti-brute-force discipline).

This is the recurrence-finder rung that sits between :func:`~srmech.amsc.elliptic_gosper.
elliptic_gosper` (the indefinite-summation antidifference, rc65) and a future
elliptic-WZ proof op, specialised to the very-well-poised ₈ω₇ keystone. Where
:func:`~srmech.amsc.zeilberger.zeilberger` / :func:`~srmech.amsc.q_zeilberger.q_zeilberger`
find the recurrence ``f(n+1) = ρ(n)·f(n)`` for an ordinary / q-hypergeometric DEFINITE
sum by creative telescoping over a polynomial / Laurent carrier, the elliptic
₈ω₇ recurrence is read off STRUCTURALLY from the term-ratio's very-well-poised shape:

    f(n) = the ₈ω₇ sum  ⟹  f(n+1)/f(n) = ρ(n),   an :class:`~srmech.amsc.ellbase.EllRatio`
    in ``y = qⁿ`` (the recurrence axis), the order-1 recurrence ``[a0, a1] = [-ρ, 1]``.

The Frenkel–Turaev ₈ω₇ summation (Warnaar, *Constr. Approx.* 18 (2002) 479–502,
**Corollary 2.2**, with the balancing condition ``bcde = a²q^{n+1}``) has the closed
product form

    f(n) = (aq, aq/bc, aq/bd, aq/cd; q, p)_n / (aq/b, aq/c, aq/d, aq/bcd; q, p)_n,

so its ratio ``f(n+1)/f(n)`` is the order-1 coefficient ``ρ(n)`` — a ratio of FOUR
numerator thetas over FOUR denominator thetas (in ``y = qⁿ``), balanced (an elliptic
function on the recurrence axis). This op RECOGNIZES a canonical ₈ω₇ term-ratio
``r(x) = t(n+1)/t(n)`` (the summand ratio in ``x = qⁿ``: the very-well-poised core
``θ(aq²x²)θ(ax)/[θ(ax²)θ(qx)]`` over five Pochhammer pairs ``θ(ux)/θ(aqx/u)`` with the
balancing ``bcde = a²q^{n+1}``), DECOMPOSES it into ``a`` plus the three free parameters
``[b, c, d]`` (beat decomposition), and CONSTRUCTS ``ρ`` from the elementary symmetric
functions ``s₂ = {bc, bd, cd}`` and ``s₃ = bcd``:

    numerator endpoints  : ``{aq} ∪ {aq/(bc), aq/(bd), aq/(cd)}``      (4 thetas in y)
    denominator endpoints: ``{aq/b, aq/c, aq/d} ∪ {aq/(bcd)}``        (4 thetas in y)
    ρ = ∏ θ(end·y; p) over the numerator endpoints / ∏ θ(end·y; p) over the den endpoints.

The construction IS the answer (decompose-and-compute) — there is NO search over an
undetermined-coefficient family. The op VERIFIES the recurrence end-to-end: it returns
``ρ`` only after checking that ``ρ(n)`` equals the actual ₈ω₇ sum's ``f(n+1)/f(n)`` (the
verification GATE; the closed product form above is the independent oracle). A ratio
that is NOT a canonical ₈ω₇ (wrong very-well-poised shape, wrong Pochhammer-pair count,
or unbalanced) is honestly out of class → ``None`` (the honest residue, like
``elliptic_gosper`` declining an un-summable term).

Reference (MPM-verified at build — the actual published result, NOT a training-data
attribution): S. Ole Warnaar, "Summation and transformation formulas for elliptic
hypergeometric series," *Constructive Approximation* 18 (2002), no. 4, 479–502
(arXiv:math/0001006). **Corollary 2.2** gives the Frenkel–Turaev ₈ω₇ summation in the
product form above; the very-well-poised balancing condition ``bcde = a²q^{n+1}`` is the
₈ω₇ structure this op recognizes. (The summand's very-well-poised core
``θ(aq²ˣ)θ(aqˣ)/[θ(aq²ˣ⁻¹)θ(q)]`` and the theta-Pochhammer carrier are
:mod:`srmech.amsc.ellbase`.)

Exact over the modified-theta algebra (no float in the carrier; the verification GATE
uses the carrier's own truncated-theta eval :meth:`~srmech.amsc.ellbase.EllRatio.
eval_trunc`, an exact-ℚ truncated product — NOT a standalone numeric theta). Sign is the
**Class-K** pin-slot via the ``Q`` / ``EllMonomial`` sign-branch (the ``|e| == 2``
very-well-poised detection is a ``e == 2 or e == -2`` Class-K branch, never an ALU
``abs()``); no ``math`` module, no numpy.

C peer: ``srmech_elliptic_recurrence_8w7`` (``c/src/srmech_elliptic_recurrence.c``) is a
1:1 mirror of this recognize-decompose-construct pipeline over the integer
theta-exponent lattice — it reads the input term-ratio's wire form, runs the SAME
very-well-poised decomposition (the ``a`` / free-param extraction) + the SAME elementary-
symmetric endpoint construction, and emits ``ρ`` as an EllRatio byte-identical to the
Python certificate. It builds on the shared ``srmech_ellbase_*`` (monomial algebra /
canonicalize) + ``er_build`` (the EllRatio constructor) kernels (the everything-mirrors
no-double-copy discipline). The Python dispatch trusts a native result ONLY after
re-verifying ``ρ`` byte-for-byte against the pure-Python construction AND re-running the
₈ω₇ verification GATE in exact ℚ. Caller-arena, malloc-free, JPL-clean; no ``abs()``
(Class-K sign), no ``math`` / numpy.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .ellbase import EllMonomial, EllRatio, Theta, _Q_SYM, _X
from .q import Q
from .thetasum import _Y

__all__ = ["elliptic_recurrence_8w7"]

_Q_ONE = Q(1, 1)

# The exact-ℚ verification points for the GATE (an INDEPENDENT cross-check that the
# constructed ρ(n) equals the actual ₈ω₇ sum's f(n+1)/f(n) — the closed product form is
# the oracle). All exact rationals (no float); |p| < 1 for the truncated theta to
# converge; q / a / b / c / d distinct so the very-well-poised structure is non-degenerate.
_GATE_PARAMS: "Dict[str, Q]" = {
    "q": Q(2, 1), "p": Q(1, 17), "a": Q(3, 5),
    "b": Q(5, 7), "c": Q(7, 11), "d": Q(11, 13),
}
# The truncation depth of the modified-theta product in the GATE. With |p| = 1/17 the
# truncated product's tail shrinks like |p|^depth, so depth 24 gives a ~|p|^24 ≈ 10^-30
# residual — ample margin under the 1e-9 gate (a genuine ₈ω₇ recurrence closes to machine-
# tiny well before this; the depth is immaterial to the EXACT carrier, only to the eval).
_GATE_TRUNC = 24
# The recurrence indices n the GATE checks (the prototype's n = 1, 2, 3).
_GATE_N = (1, 2, 3)
# The closeness bound the GATE demands (the prototype passes at exact 0; <1e-9 is the spec).
_GATE_TOL_NUM = 1
_GATE_TOL_DEN = 1_000_000_000          # 1e-9 as an exact ℚ (no float threshold)


def _coerce_ratio(value) -> EllRatio:
    """Coerce the ₈ω₇ term-ratio operand to an :class:`~srmech.amsc.ellbase.EllRatio`.
    An ``EllRatio`` passes through; an ``EllMonomial`` / ``Theta`` the carrier lifts is
    lifted (though a genuine ₈ω₇ ratio always arrives as a full theta-quotient)."""
    if isinstance(value, EllRatio):
        return value
    if isinstance(value, EllMonomial):
        return EllRatio.monomial(value)
    if isinstance(value, Theta):
        return EllRatio.theta(value)
    raise TypeError(
        "elliptic_recurrence_8w7: the term-ratio operand must be an EllRatio (or an "
        f"EllMonomial / Theta the carrier lifts); got {value!r}")


def _is_x_power(theta: Theta, magnitude: int) -> bool:
    """True iff the theta's argument has x-exponent ``+magnitude`` OR ``-magnitude`` — the
    Class-K sign-branch that replaces ``|x-exponent| == magnitude`` (sign-flip is the
    Class-K pin-slot, never an ALU ``abs()``). ``magnitude`` is 1 (a Pochhammer / linear
    factor) or 2 (the very-well-poised quadratic core)."""
    e = theta.arg.exp_of(_X)
    return e == magnitude or e == -magnitude


def _real_base(theta: Theta) -> EllMonomial:
    """Un-invert the carrier's ``θ(z) ↔ θ(1/z)`` canonicalization to recover the REAL base
    monomial ``b`` of a theta ``θ(b·xᵏ)`` (``k = ±1`` for a linear factor). Strip the
    ``x``-power, then re-orient: the canonical form may have flipped ``θ(b·x) → θ(1/(b·x))``
    (x-exponent ``−1``), so a negative x-exponent means the stored argument is the inverse
    of the real base — invert it back. The orientation flip is a Class-K / Class-C chirality
    resolution (no ``abs()``)."""
    k = theta.arg.exp_of(_X)
    core = theta.arg * EllMonomial.symbol(_X, -k)        # the base, x stripped
    return core if k > 0 else core.inv()


def _decompose_8w7(r: EllRatio) -> "Optional[Tuple[EllMonomial, List[EllMonomial]]]":
    """RECOGNIZE the very-well-poised ₈ω₇ structure of the term-ratio ``r`` and DECOMPOSE
    it into ``(a, [b, c, d])`` — the base ``a`` plus the three FREE (n-independent)
    parameters (the beat decomposition). Returns ``None`` if ``r`` is not a canonical
    ₈ω₇ (no quadratic very-well-poised core, or not exactly three free linear params).

    The very-well-poised core is the denominator quadratic ``θ(a·x²)`` (x-exponent ±2);
    its real base is ``a``. The Pochhammer denominators ``θ(a·q·x·u⁻¹)`` are the linear
    (x-exponent ±1) den factors; ``aq · (real_base)⁻¹`` recovers each parameter ``u``. The
    spurious ``(q)``-factor (which recovers ``u == a``) is dropped; the parameters carrying
    the recurrence variable ``y = qⁿ`` (the ``e = a²qⁿ⁺¹/(bcd)`` and ``q⁻ⁿ`` Pochhammers)
    are n-DEPENDENT (nonzero y-exponent) and dropped — leaving the three free params."""
    quad_den = [t for t in r.den if _is_x_power(t, 2)]
    if len(quad_den) != 1:
        return None                                       # no unique VWP quadratic core
    a_mono = _real_base(quad_den[0])
    aq = a_mono * EllMonomial.symbol(_Q_SYM)
    params = [aq * _real_base(t).inv() for t in r.den if _is_x_power(t, 1)]
    # drop the (q)-factor partner that recovers u == a (the θ(qx) very-well-poised factor).
    params = [u for u in params if dict(u.exps) != dict(a_mono.exps)]
    # the FREE params are n-independent (no y); the n-carriers (e and q^{-n}) carry y.
    free = [u for u in params if u.exp_of(_Y) == 0]
    if len(free) != 3:
        return None                                       # not a canonical ₈ω₇ (≠ 3 free)
    return a_mono, free


def _build_rho(a_mono: EllMonomial, free: "List[EllMonomial]") -> EllRatio:
    """CONSTRUCT the order-1 recurrence coefficient ``ρ`` (an :class:`EllRatio` in
    ``y = qⁿ``) from the base ``a`` and the three free params ``[b, c, d]`` via the
    elementary symmetric functions (Warnaar Cor 2.2):

        numerator endpoints  : ``{aq} ∪ {aq/(bc), aq/(bd), aq/(cd)}``   (``s₂`` pairs)
        denominator endpoints: ``{aq/b, aq/c, aq/d} ∪ {aq/(bcd)}``      (singles + ``s₃``)
        ρ = ∏ θ(end·y; p) over the num endpoints / ∏ θ(end·y; p) over the den endpoints.

    This is the structural construction — NO undetermined-coefficient solve. Returns a
    balanced ``EllRatio`` with 4 numerator + 4 denominator thetas."""
    aq = a_mono * EllMonomial.symbol(_Q_SYM)
    s2 = [free[0] * free[1], free[0] * free[2], free[1] * free[2]]
    s3 = free[0] * free[1] * free[2]
    num_end = [aq] + [aq * pp.inv() for pp in s2]
    den_end = [aq * s.inv() for s in free] + [aq * s3.inv()]
    y = EllMonomial.symbol(_Y)
    return EllRatio(num=[Theta(end * y) for end in num_end],
                    den=[Theta(end * y) for end in den_end])


# ── the ₈ω₇ sum's closed product form (the independent verification oracle) ──────────


def _poch_value(u_mono: EllMonomial, n: int, params: "Dict[str, Q]", trunc: int) -> Q:
    """The theta-Pochhammer ``(u; q, p)_n = ∏_{j=0}^{n-1} θ(u·qʲ; p)`` evaluated to a single
    exact ``Q`` via the carrier's truncated modified-theta product (the eval ORACLE; no
    float). ``u_mono`` is an ``EllMonomial`` in the parameter symbols (a, b, c, d, q)."""
    acc = _Q_ONE
    for j in range(n):
        arg = u_mono * EllMonomial.symbol(_Q_SYM, j)
        acc = acc * Theta(arg).eval_trunc(params, trunc)
    return acc


def _f_sum_value(n: int, params: "Dict[str, Q]", trunc: int) -> Q:
    """The Frenkel–Turaev ₈ω₇ DEFINITE sum ``f(n)`` via Warnaar Cor 2.2's closed product
    form ``(aq, aq/bc, aq/bd, aq/cd; q,p)_n / (aq/b, aq/c, aq/d, aq/bcd; q,p)_n`` — the
    INDEPENDENT oracle for the recurrence GATE (an exact-ℚ truncated-theta evaluation, NOT
    the constructed ρ). ``n ≥ 0``; ``f(0) = 1`` (empty Pochhammers)."""
    a = EllMonomial.symbol("a"); b = EllMonomial.symbol("b")
    c = EllMonomial.symbol("c"); d = EllMonomial.symbol("d")
    q = EllMonomial.symbol(_Q_SYM)
    aq = a * q
    num_u = [aq, aq * (b * c).inv(), aq * (b * d).inv(), aq * (c * d).inv()]
    den_u = [aq * b.inv(), aq * c.inv(), aq * d.inv(), aq * (b * c * d).inv()]
    acc = _Q_ONE
    for u in num_u:
        acc = acc * _poch_value(u, n, params, trunc)
    for u in den_u:
        acc = acc / _poch_value(u, n, params, trunc)
    return acc


def _close_enough(lhs: Q, rhs: Q) -> bool:
    """Decide ``|lhs − rhs| < 1e-9`` in EXACT ℚ (no float threshold): the magnitude of the
    difference's numerator over its denominator vs ``1/1e9``. The sign of the difference is
    a Class-K pin-slot (compare numerators with the sign carried by ``Q``); ``abs`` is
    avoided by forming ``diff`` and ``−diff`` and taking the positive representative."""
    diff = lhs - rhs
    # the magnitude |diff| as an exact ℚ, via the Class-K sign-branch (not ALU abs()).
    mag = diff if diff.numerator >= 0 else (Q(0, 1) - diff)
    # mag < 1e-9  ⟺  mag.num * 1e9_den < 1e-9_num * mag.den  (cross-multiply, exact ints).
    return mag.numerator * _GATE_TOL_DEN < _GATE_TOL_NUM * mag.denominator


def _verifies_recurrence(rho: EllRatio) -> bool:
    """The VERIFICATION GATE: ``ρ(n)`` (evaluated at ``y = qⁿ`` via the carrier's truncated
    theta) equals the actual ₈ω₇ sum's ``f(n+1)/f(n)`` (the closed product form) to
    ``< 1e-9`` for every ``n`` in :data:`_GATE_N`. The gate uses the carrier's OWN exact-ℚ
    theta eval (:meth:`~srmech.amsc.ellbase.EllRatio.eval_trunc`), never a standalone
    numeric theta. A ρ that fails the gate is NOT trusted (the no-hallucination standard:
    the construction is only accepted as the recurrence after it is verified to BE the
    recurrence)."""
    for n in _GATE_N:
        vals = dict(_GATE_PARAMS)
        vals[_Y] = _GATE_PARAMS["q"] ** n
        lhs = rho.eval_trunc(vals, _GATE_TRUNC)
        f_n = _f_sum_value(n, _GATE_PARAMS, _GATE_TRUNC)
        if f_n == Q(0, 1):
            return False                                  # degenerate sample (no division)
        rhs = _f_sum_value(n + 1, _GATE_PARAMS, _GATE_TRUNC) / f_n
        if not _close_enough(lhs, rhs):
            return False
    return True


# ── the wire form for the C bridge (mirrors elliptic_gosper's _ratio_to_form) ────────


def _ratio_to_form(r: EllRatio) -> Dict[str, object]:
    """An :class:`~srmech.amsc.ellbase.EllRatio` → the bridge form the C peer consumes:
    the exact-``ℚ`` prefactor ``(coeff_num, coeff_den, [(sym, exp), …])`` plus the
    numerator / denominator theta-argument exponent maps (each the same triple). Pure
    integer exponents + exact-``ℚ`` coefficients — no float. (Same convention as
    :func:`srmech.amsc.elliptic_gosper._ratio_to_form`.)"""
    def _mono(m: EllMonomial):
        return (m.coeff.numerator, m.coeff.denominator, sorted(m.exps.items()))

    return {
        "prefactor": _mono(r.prefactor),
        "num": [_mono(t.arg) for t in r.num],
        "den": [_mono(t.arg) for t in r.den],
    }


def _form_to_ratio(form) -> EllRatio:
    """Rebuild an :class:`~srmech.amsc.ellbase.EllRatio` from the bridge form (from the C
    peer)."""
    def _mono(triple) -> EllMonomial:
        cn, cd, exps = triple
        return EllMonomial(Q(cn, cd), {s: e for s, e in exps})

    pref = _mono(form["prefactor"])
    num = tuple(Theta(_mono(t)) for t in form["num"])
    den = tuple(Theta(_mono(t)) for t in form["den"])
    return EllRatio(pref, num=num, den=den)


def _rho_to_result(rho: EllRatio) -> Dict[str, object]:
    """The verified order-1 recurrence ``ρ`` → the public return dict. The recurrence is
    ``f(n+1) = ρ(n)·f(n)`` (order 1; coefficients ``[a0, a1] = [-ρ, 1]``); ``ρ`` is
    returned as its ``EllRatio`` operands (prefactor + the numerator / denominator
    theta-argument exponent maps) PLUS the live carrier objects under ``'rho'`` /
    ``'coeffs'`` so the caller can rebuild and re-verify ``ρ(n) == f(n+1)/f(n)``
    independently."""
    form = _ratio_to_form(rho)
    neg_rho = EllRatio.monomial(EllMonomial.scalar(Q(-1, 1))) * rho     # -ρ (Class-K sign)
    return {
        "order": 1,
        "coeffs": [neg_rho, EllRatio.one()],          # [a0, a1] = [-ρ, 1]: f(n+1)=ρ·f(n)
        "rho": rho,
        "prefactor": {"coeff": (form["prefactor"][0], form["prefactor"][1]),
                      "exps": dict(form["prefactor"][2])},
        "num": [dict(exps) for _cn, _cd, exps in form["num"]],
        "den": [dict(exps) for _cn, _cd, exps in form["den"]],
    }


def _native():
    """The native ``_native`` module IF the ``srmech_elliptic_recurrence_8w7`` peer is
    present and bound, else ``None`` — so the op dispatches to C when available and falls
    cleanly to the pure-Python body (the complete alternative + the parity oracle).
    Imported lazily to avoid a bootstrap cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    probe = getattr(nat, "has_native_elliptic_recurrence_8w7", None)
    return nat if (probe is not None and probe()) else None


# ── the public op ────────────────────────────────────────────────────────────────────


def elliptic_recurrence_8w7(r) -> Optional[Dict[str, object]]:
    """The ELLIPTIC Σ-row ORDER-1 RECURRENCE for the Frenkel–Turaev ₈ω₇ summation — a
    STRUCTURAL (beat-decomposition) finder.

    ``r`` is the ₈ω₇ summand's **term ratio** ``t(n+1)/t(n) = r(x)`` (``x = qⁿ``) — an
    :class:`~srmech.amsc.ellbase.EllRatio`: the very-well-poised core
    ``θ(aq²x²)θ(ax)/[θ(ax²)θ(qx)]`` over five Pochhammer pairs ``θ(ux)/θ(aqx/u)`` with the
    ₈ω₇ balancing ``bcde = a²q^{n+1}`` (an ``EllMonomial`` / ``Theta`` the carrier lifts is
    lifted). The op RECOGNIZES the ₈ω₇ structure, DECOMPOSES it into ``a`` plus the three
    free params ``[b, c, d]``, and CONSTRUCTS the order-1 recurrence coefficient ``ρ(n)``
    (an ``EllRatio`` in ``y = qⁿ``) from the elementary symmetric functions of the free
    params (Warnaar, *Constr. Approx.* 18 (2002) 479–502, **Corollary 2.2**):

    - if ``r`` is a canonical ₈ω₇ AND the constructed ``ρ`` PASSES the verification GATE
      (``ρ(n)`` equals the actual ₈ω₇ sum's ``f(n+1)/f(n)`` for ``n = 1, 2, 3`` to
      ``< 1e-9``, the closed product form the independent oracle), returns ``{'order': 1,
      'coeffs': [-ρ, 1], 'rho': ρ, 'prefactor': …, 'num': [{sym: exp}, …], 'den': […]}`` —
      the order-1 recurrence ``f(n+1) = ρ(n)·f(n)`` (so ``[a0, a1] = [-ρ, 1]``);
    - if ``r`` is **not** a canonical ₈ω₇ (wrong very-well-poised shape / Pochhammer count
      / unbalanced) or the constructed ``ρ`` fails the gate, returns ``None`` (the honest
      out-of-class residue).

    The construction IS the answer (decompose-and-compute, NOT enumerate-and-test); the
    gate uses the carrier's own exact-ℚ truncated-theta eval (no standalone numeric theta).
    No float, no ``abs()`` (Class-K sign), no ``math`` / numpy. See the module docstring
    for the full recognize-decompose-construct pipeline + the verified Warnaar reference.
    """
    r = _coerce_ratio(r)
    if r.is_zero:
        return None
    # the row gate: a ₈ω₇ term-ratio is very-well-poised (an elliptic / balanced function);
    # an unbalanced ratio is honestly out of the row before any decomposition.
    if not r.is_elliptic():
        return None

    nat = _native()
    if nat is not None:
        try:
            got = nat.elliptic_recurrence_8w7_c(_ratio_to_form(r))
            # The C peer is trusted ONLY after the Python rebuild re-verifies it byte-for-
            # byte AND the ₈ω₇ gate passes in exact ℚ. A has=0 (declined / not ₈ω₇) falls
            # through to the complete pure-Python path.
            if got is not None:
                has, rho_form = got
                if has:
                    rho = _form_to_ratio(rho_form)
                    pure = _elliptic_recurrence_8w7_pure(r)
                    if (pure is not None and pure["rho"] == rho
                            and _verifies_recurrence(rho)):
                        return _rho_to_result(rho)
        except (RuntimeError, OverflowError, ValueError):
            pass                                          # fall to the pure path

    return _elliptic_recurrence_8w7_pure(r)


def _elliptic_recurrence_8w7_pure(r: EllRatio) -> Optional[Dict[str, object]]:
    """The exact pure-Python ₈ω₇ order-1 recurrence finder (the complete alternative to the
    C peer + its parity oracle) — STRUCTURAL recognize-decompose-construct. (1) RECOGNIZE +
    DECOMPOSE the very-well-poised ₈ω₇ into ``a`` + the three free params
    (:func:`_decompose_8w7`; ``None`` out of class). (2) CONSTRUCT ``ρ`` from the elementary
    symmetric functions (:func:`_build_rho`). (3) VERIFY ``ρ(n) == f(n+1)/f(n)`` for the
    ₈ω₇ sum (:func:`_verifies_recurrence`, the GATE) before returning — a ρ that fails the
    gate is ``None``. Returns the recurrence dict (verified) or ``None``."""
    decomp = _decompose_8w7(r)
    if decomp is None:
        return None
    a_mono, free = decomp
    rho = _build_rho(a_mono, free)
    if not _verifies_recurrence(rho):
        return None
    return _rho_to_result(rho)
