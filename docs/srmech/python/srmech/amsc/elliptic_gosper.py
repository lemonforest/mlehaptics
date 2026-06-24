"""srmech.amsc.elliptic_gosper — the ELLIPTIC analog of Gosper's indefinite
hypergeometric summation (the FIRST engine op of the ELLIPTIC F929 reduction row,
the top of the base-axis degeneration tower ``elliptic → q → ordinary``).

Where :func:`srmech.amsc.gosper.gosper` decides whether an ordinary
hypergeometric term ``t(k)`` has a hypergeometric antidifference and
:func:`srmech.amsc.q_gosper.q_gosper` decides the same for a q-hypergeometric term
(term-ratio rational in ``x = qᵏ``), the **elliptic Gosper** algorithm decides it
for a **theta-hypergeometric** (elliptic-hypergeometric) term, whose term-ratio
``r(x) = t(n+1)/t(n)`` is an :class:`~srmech.amsc.ellbase.EllRatio` — a ratio of
modified-theta products ``∏θ(αx;p)/∏θ(βx;p)`` over an exact-``ℚ`` monomial
prefactor (``x = qⁿ``; the summation shift ``σ : x ↦ q·x``):

    t(n+1)/t(n) = r(x),   x = qⁿ,   σ : x ↦ q·x   (the elliptic summation shift).

This op takes that term-ratio and decides whether ``t(n)`` has an
elliptic-hypergeometric **antidifference** ``T(n) = R(x)·t(n)`` (so ``T(n+1) −
T(n) = t(n)`` and the sum telescopes: ``Σ_{n=a}^{b} t(n) = T(b+1) − T(a)``), where
``R(x)`` is itself an :class:`~srmech.amsc.ellbase.EllRatio` (a theta-quotient)
satisfying the **elliptic Gosper equation**

    R(qx)·r(x) − R(x) = 1                  (R(qx) = R.qshift())

— the elliptic analogue of the ordinary Gosper identity ``R(k+1)·r(k) − R(k) = 1``
and the q-Gosper identity ``R(qx)·r(x) − R(x) = 1``, ONE algebra up (the atoms are
theta-factors, not Laurent monomials). If no elliptic-hypergeometric antidifference
exists, returns ``None`` (the honest un-summable residue, like ``gosper`` on the
harmonic term).

Reference (MPM-verified at build — the actual arXiv PDF extracted, authors + title
+ venue + year confirmed, NOT a training-data attribution):

    George Gasper and Michael Schlosser, "Summation, transformation, and expansion
    formulas for multibasic theta hypergeometric series," Adv. Stud. Contemp. Math.
    (Kyungshang) 11, no. 1 (2005), 67–84 (arXiv:math/0505215). The abstract states
    the results are derived "using indefinite summation" — the elliptic / theta
    analogue of Gosper's indefinite-summation telescoping. The elliptic balancing
    (very-well-poised) condition that gates the row is Gasper–Schlosser Eq. (2.4):
    ``a₁a₂…a_{r+1} = (b₁…b_r)q`` makes ``g(x) = z·∏θ(a_kqˣ;p)/θ(b_kqˣ;p)`` an
    elliptic (doubly-periodic) function — exactly the
    :meth:`~srmech.amsc.ellbase.EllRatio.is_elliptic` predicate (``g`` invariant
    under the period shift ``x ↦ p·x``). Secondary anchor (already cited by
    :mod:`srmech.amsc.ellbase`): S. O. Warnaar, *Constr. Approx.* 18 (2002)
    479–502; keystone identity = the Frenkel–Turaev ₁₀E₉ sum.

The algorithm, exact over the modified-theta algebra (no float in the carrier; the
ONE numeric materialisation is the exact-``ℚ`` truncated theta product
:meth:`~srmech.amsc.ellbase.EllRatio.eval_trunc`, the additive-verification oracle —
theta-quotients form a multiplicative group but are NOT additively closed, so the
additive Gosper equation is decided structurally and CERTIFIED by an exact-``ℚ``
eval cross-check):

  1. **Row gate.** ``r`` must be elliptically balanced (``r.is_elliptic()`` True —
     a genuine function on the elliptic curve ``ℂ*/⟨p⟩``); an unbalanced ratio is
     honestly out of the row → ``None``. (This is the structural balancing /
     very-well-poised gate, Gasper–Schlosser Eq. (2.4).)

  2. **Theta-Gosper–Petkovšek normal form.** Write ``r`` as a theta-quotient and
     bring it to ``r = (a/b)·(σc/c)`` with ``a``/``b``/``c`` theta-products and
     ``a``, ``b`` **theta-dispersion-coprime** (the elliptic analogue of the
     q-Gosper GP form): two theta factors ``θ(αx;p)`` and ``θ(β·qᵏx;p)`` collide
     iff ``α = β·qᵏ`` for an integer ``k ≥ 0`` (the **theta-dispersion**, the q-step
     alignment of theta arguments, since ``θ(z;p)`` is the elliptic σ-shift atom).
     Peel the colliding factor at the smallest non-negative dispersion ``k`` into
     ``c`` (the Gosper–Petkovšek bookkeeping that keeps ``r`` invariant).

  3. **Solve the elliptic Gosper equation.** The certificate has the shape ``R(x) =
     (σ⁻¹b)·y / c`` (the same shape as the ordinary / q-Gosper certificate), where
     ``y`` is a theta-quotient solving ``a(x)·y(qx) − σ⁻¹b(x)·y(x) = c(x)``. The
     structurally-decidable summable class this engine certifies is the one with a
     theta-MONOMIAL-quotient ``y`` (the elliptic analogue of the q-geometric closed
     form) — its candidate ``R`` is built directly from the GP factors, and the
     **additive Gosper equation is VERIFIED exactly** (``R.qshift()·r − R == 1``)
     through the exact-``ℚ`` :meth:`~srmech.amsc.ellbase.EllRatio.eval_trunc` oracle
     at several rational sample points (the additive ``−`` lives in ``ℚ``, where the
     carrier evaluates exactly — there is no float, no ``math``, no numpy). A
     verified candidate is returned; otherwise ``None``.

The public op returns the certificate ``R`` as its ``EllRatio`` operands —
``{"prefactor": EllMonomial-as-(coeff, exps), "num": [theta-arg, …], "den":
[theta-arg, …]}`` — or ``None``. Sign is the **Class-K** pin-slot via the ``Q`` /
``EllMonomial`` sign-branch (never an ALU ``abs()``); no ``math`` module, no numpy.
This is the **elliptic-Gosper** rung of the ELLIPTIC F929 row (the row continues
with the elliptic-Zeilberger recurrence-finder rc62, which parametrizes THIS engine,
then the elliptic-WZ proof op rc63); the internals are factored to be reused there.

C peer: ``srmech_elliptic_gosper`` (``c/src/srmech_elliptic_gosper.c``) is a
BOUNDED-SCOPE accelerator (the ``srmech_q_gosper`` precedent): it completes the
structurally-simplest elliptic-summable case natively over the integer theta-
exponent lattice + exact-``ℚ`` prefactor, byte-identical to the Python certificate,
and DECLINES the rest (``out_has = 0`` → the Python dispatch re-runs the COMPLETE
pure-Python body here, the parity oracle AND the full-coverage decider — a ``has=0``
is never a definitive "no certificate"). Caller-arena, malloc-free, JPL-clean.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .cascade import magnitude
from .ellbase import EllMonomial, EllRatio, Theta, _P, _Q_SYM, _X
from .q import Q

__all__ = ["elliptic_gosper"]

_Q_ZERO = Q(0, 1)
_Q_ONE = Q(1, 1)

# The exact-ℚ sample points at which the additive elliptic Gosper equation
# R(qx)·r(x) − R(x) = 1 is verified (the theta-quotient carrier is NOT additively
# closed, so the additive relation is decided structurally + CERTIFIED in exact ℚ).
# Several independent points pin the rational identity. A point with |p| < 1 makes
# the truncated modified-theta product the exact-ℚ value the verifier reads; a
# certificate is accepted ONLY when the residual is EXACTLY 0 there (Class-K
# magnitude, never an ALU abs()). All exact rationals (no float, no math, no numpy).
_VERIFY_POINTS: Tuple[Dict[str, Q], ...] = (
    {_Q_SYM: Q(2, 1), _P: Q(1, 9), _X: Q(2, 3), "a": Q(3, 5), "b": Q(4, 7),
     "c": Q(5, 8), "d": Q(2, 9), "e": Q(7, 4), "f": Q(3, 8)},
    {_Q_SYM: Q(3, 1), _P: Q(1, 16), _X: Q(3, 4), "a": Q(2, 5), "b": Q(5, 7),
     "c": Q(3, 8), "d": Q(4, 9), "e": Q(2, 3), "f": Q(5, 6)},
)

# The truncation depth the EXACT verifier reads. A certificate is accepted ONLY when
# the Gosper-equation residual is EXACTLY 0 at every sample — which holds iff the
# residual carries NO surviving theta factor (the theta-free / elliptic-geometric
# core), whose exact-ℚ truncated value IS the true value at any finite depth. So the
# depth is immaterial to a genuine certificate; it only bounds the near-miss reject.
_VERIFY_TRUNC = 12

# The largest theta-dispersion q-step the GP-form scan reaches (the elliptic analogue
# of the q-Gosper x-degree / q-dispersion bound). A genuine elliptic-summable term's
# theta arguments align within this q-step window; beyond it the C/Python decline.
_MAX_DISPERSION = 24


def _native():
    """The native ``_native`` module IF the rc61 ``srmech_elliptic_gosper`` peer is
    present and bound, else ``None`` — so ``elliptic_gosper`` dispatches to C when
    available and falls cleanly to the pure-Python body (the complete alternative +
    the parity oracle) otherwise. Imported lazily to avoid a bootstrap cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    probe = getattr(nat, "has_native_elliptic_gosper", None)
    return nat if (probe is not None and probe()) else None


def _coerce_ratio(value) -> EllRatio:
    """Coerce the term-ratio operand to an :class:`~srmech.amsc.ellbase.EllRatio`.
    An ``EllRatio`` passes through; an ``EllMonomial`` (a pure-monomial ratio) /
    a ``Theta`` (a single numerator theta) is lifted."""
    if isinstance(value, EllRatio):
        return value
    if isinstance(value, EllMonomial):
        return EllRatio.monomial(value)
    if isinstance(value, Theta):
        return EllRatio.theta(value)
    raise TypeError(
        "elliptic_gosper: the term-ratio operand must be an EllRatio (or an "
        f"EllMonomial / Theta the carrier lifts); got {value!r}")


# ── theta-dispersion: the q-step alignments of two theta arguments ─────────────


def _x_coeff_monomial(arg: EllMonomial) -> EllMonomial:
    """The "x-free coefficient" monomial of a theta argument ``arg`` — strip the
    ``x`` and ``q`` powers, leaving the parameter-and-sign part (the ``α`` of
    ``θ(α·qᵏx; p)``). Two theta arguments ``θ(αx)``, ``θ(β·qᵏx)`` align under the
    q-shift iff their x-and-q-free parts agree; the q-step ``k`` is then read off."""
    out = arg * EllMonomial.symbol(_X, -arg.exp_of(_X))
    out = out * EllMonomial.symbol(_Q_SYM, -out.exp_of(_Q_SYM))
    return out


def _theta_dispersion(num_args: List[EllMonomial],
                      den_args: List[EllMonomial]) -> List[int]:
    """The theta-dispersion set ``{ k ≥ 0 : some θ(α x) in num collides with some
    θ(β qᵏ x) in den }`` — the q-step shifts at which a numerator theta argument
    equals a ``qᵏ``-shifted denominator theta argument (the elliptic analogue of the
    q-dispersion). A collision needs the x-exponents equal AND the x-free parts equal
    after a ``qᵏ`` shift, so ``k = (q-exp of num arg) − (q-exp of den arg)``. Ascending,
    deduplicated, ``0 ≤ k ≤`` :data:`_MAX_DISPERSION`."""
    out: List[int] = []
    for na in num_args:
        nx = na.exp_of(_X)
        ncoef = _x_coeff_monomial(na)
        for da in den_args:
            if da.exp_of(_X) != nx:
                continue
            if _x_coeff_monomial(da) != ncoef:
                continue
            k = na.exp_of(_Q_SYM) - da.exp_of(_Q_SYM)
            if 0 <= k <= _MAX_DISPERSION and k not in out:
                out.append(k)
    out.sort()
    return out


# ── the additive elliptic Gosper equation verifier (exact-ℚ eval oracle) ───────


def _gap_to_one(cert: EllRatio, lhs_mul: EllRatio, vals: Dict[str, Q],
                trunc: int) -> "Q | None":
    """The exact-``ℚ`` Class-K magnitude of ``(R(qx)·r − R) − 1`` at ``vals``,
    truncated at ``trunc`` — the gap to the elliptic Gosper-equation target. The
    multiplicative pieces are formed in the carrier; only the final difference is a
    ``ℚ`` subtraction; the magnitude is the **Class-K** pin-slot (never an ALU
    ``abs()``). ``None`` if evaluation fails (a denominator theta vanished)."""
    try:
        a = lhs_mul.eval_trunc(vals, trunc)
        b = cert.eval_trunc(vals, trunc)
    except (ZeroDivisionError, KeyError, TypeError):
        return None
    return magnitude((a - b) - _Q_ONE)                # |R(qx)·r − R − 1|, Class-K


def _verifies_gosper_equation(cert: EllRatio, r: EllRatio) -> bool:
    """Decide ``R(qx)·r(x) − R(x) = 1`` (the elliptic Gosper equation) EXACTLY. A
    certificate is accepted ONLY when the equation's residual is EXACTLY zero in
    exact ``ℚ`` at every sample in :data:`_VERIFY_POINTS` — which holds iff the
    certificate's Gosper-equation difference carries NO surviving theta factor (the
    theta-free / elliptic-geometric core), whose exact-``ℚ`` truncated value IS the
    true value at every finite depth. A candidate whose residual is merely small or
    converging is REJECTED, not accepted: **a certificate is an exact proof object,
    never a numerically-converging witness** — the same no-hallucination, exact-
    verification standard the §76 ``gosper`` / ``zeilberger`` / ``wz_certificate`` ops
    hold. Genuine single-x theta telescopers (which need the multi-x ``q**(2n)``
    lattice, a future carrier extension) therefore return honest ``None`` here, never
    a numerically-witnessed certificate. The theta-quotient carrier is
    multiplicatively but NOT additively closed, so the additive ``−`` of the residual
    is taken in exact ``ℚ`` via :meth:`~srmech.amsc.ellbase.EllRatio.eval_trunc`."""
    lhs_mul = cert.qshift() * r                       # R(qx)·r(x), in the carrier
    for vals in _VERIFY_POINTS:
        gap = _gap_to_one(cert, lhs_mul, vals, _VERIFY_TRUNC)
        if gap is None or gap != _Q_ZERO:             # accept ONLY an EXACT-0 residual
            return False
    return True


# ── candidate certificate construction (the theta-monomial-quotient class) ─────


def _candidate_certificates(r: EllRatio) -> List[EllRatio]:
    """The candidate antidifference theta-quotients ``R`` for the term-ratio ``r``,
    in the structurally-decidable elliptic-summable class (a theta-MONOMIAL-quotient
    ``y`` in the GP form — the elliptic analogue of the q-geometric closed form).

    The certificate ``R = (σ⁻¹b)·y / c`` of an elliptic-summable term is itself a
    theta-quotient over the SAME theta arguments as ``r`` (q-shifted), times a
    monomial prefactor. Rather than re-derive the GP factorisation symbolically (the
    theta algebra has no ring addition to drive an undetermined-coefficient solve),
    the engine enumerates the bounded family of such ``R`` directly from ``r``'s
    theta factors + the theta-dispersion q-steps, and lets the exact-``ℚ`` additive
    verifier (:func:`_verifies_gosper_equation`) pick the one (if any) that solves
    the Gosper equation. The family is finite (bounded by the dispersion window and
    the prefactor-monomial degrees), so this is a complete decision over the class —
    not a heuristic: a term is certified summable iff a member verifies."""
    num = list(r.num)
    den = list(r.den)
    # the dispersion q-steps that can shift r's theta args into alignment.
    disp = _theta_dispersion([t.arg for t in num], [t.arg for t in den])
    shifts = sorted({0, 1} | set(disp) | {k - 1 for k in disp if k >= 1})
    cands: List[EllRatio] = []
    seen = set()

    def _add(cert: EllRatio) -> None:
        key = (cert.prefactor, cert.num, cert.den)
        if key not in seen:
            seen.add(key)
            cands.append(cert)

    # Family 0 — the elliptic-geometric core: a CONSTANT term ratio r = z (a
    # pure-scalar prefactor, no thetas) has the constant certificate R = 1/(z − 1)
    # (then R(qx)·r − R = R·(z − 1) = 1 exactly), the direct elliptic analogue of the
    # ordinary / q-geometric closed form. Only a pure-scalar prefactor admits the
    # ℚ subtraction ``z − 1`` (Class-K sign via the exact Q); z = 1 has no finite
    # certificate.
    if not num and not den and not r.prefactor.symbols():
        z = r.prefactor.coeff
        if z != _Q_ONE:
            _add(EllRatio.monomial(EllMonomial.scalar(_Q_ONE / (z - _Q_ONE))))

    # Family 1 — R = (den theta-quotient) shifted by σ⁻ᵏ, times a small monomial
    # prefactor. This is the (σ⁻¹b)/c shape: the certificate's theta factors are r's
    # denominator factors (the GP b/c carriers) under a q-shift.
    for k in shifts:
        den_shift_num = [Theta(t.arg * EllMonomial.symbol(_Q_SYM, -k)) for t in den]
        for pref in _prefactor_candidates(r):
            _add(EllRatio(pref, num=den_shift_num, den=()))
            _add(EllRatio(pref, num=den_shift_num, den=tuple(num)))
    # Family 2 — R = (num/den theta-quotient) of r itself shifted, times a monomial.
    # Covers the elliptic-geometric core where R rides r's own theta structure.
    for k in shifts:
        num_shift = [Theta(t.arg * EllMonomial.symbol(_Q_SYM, -k)) for t in num]
        den_shift = [Theta(t.arg * EllMonomial.symbol(_Q_SYM, -k)) for t in den]
        for pref in _prefactor_candidates(r):
            _add(EllRatio(pref, num=tuple(num_shift), den=tuple(den_shift)))
    return cands


def _prefactor_candidates(r: EllRatio) -> List[EllMonomial]:
    """The small family of exact-``ℚ`` monomial prefactors to try on a candidate
    certificate. The certificate prefactor is the inverse of ``r``'s prefactor (the
    σc/c bookkeeping unit) times a low-degree x/q correction; the unit and a handful
    of ±1 x-power corrections cover the theta-monomial-quotient class. Class-K sign
    via the exact ``Q`` coefficient — never an ALU ``abs()``."""
    base = r.prefactor
    out: List[EllMonomial] = []
    seen = set()
    # the unit, the inverse-prefactor, and ±1 x-power / ±1 sign corrections.
    for unit in (EllMonomial.one(), base.inv(), base):
        for xshift in (0, 1, -1):
            for sign in (_Q_ONE, Q(-1, 1)):
                m = unit * EllMonomial(sign, {_X: xshift}) \
                    if xshift != 0 else unit * EllMonomial.scalar(sign)
                if m not in seen:
                    seen.add(m)
                    out.append(m)
    return out


# ── the wire form for the C bridge (theta-arg integer-exponent lattice) ────────


def _ratio_to_form(r: EllRatio) -> Dict[str, object]:
    """An :class:`~srmech.amsc.ellbase.EllRatio` → the bridge form the C peer
    consumes: the exact-``ℚ`` prefactor ``(coeff_num, coeff_den, [(sym, exp), …])``
    plus the numerator / denominator theta-argument exponent maps (each
    ``[(coeff_num, coeff_den, [(sym, exp), …]), …]``). Pure integer exponents +
    exact-``ℚ`` coefficients — no float."""
    def _mono(m: EllMonomial):
        return (m.coeff.numerator, m.coeff.denominator,
                sorted(m.exps.items()))

    return {
        "prefactor": _mono(r.prefactor),
        "num": [_mono(t.arg) for t in r.num],
        "den": [_mono(t.arg) for t in r.den],
    }


def _form_to_ratio(form) -> EllRatio:
    """Rebuild an :class:`~srmech.amsc.ellbase.EllRatio` from the bridge form (from
    the C peer)."""
    def _mono(triple) -> EllMonomial:
        cn, cd, exps = triple
        return EllMonomial(Q(cn, cd), {s: e for s, e in exps})

    pref = _mono(form["prefactor"])
    num = tuple(Theta(_mono(t)) for t in form["num"])
    den = tuple(Theta(_mono(t)) for t in form["den"])
    return EllRatio(pref, num=num, den=den)


def _cert_to_result(cert: EllRatio) -> Dict[str, object]:
    """The verified certificate ``EllRatio`` → the public return dict. The certificate
    is returned as its ``EllRatio`` operands (prefactor coeff + exponent map, and the
    numerator / denominator theta-argument exponent maps) so the caller can rebuild
    the carrier and re-verify ``R.qshift()·r − R == 1`` independently."""
    form = _ratio_to_form(cert)
    return {
        "prefactor": {"coeff": (form["prefactor"][0], form["prefactor"][1]),
                      "exps": dict(form["prefactor"][2])},
        "num": [dict(exps) for _cn, _cd, exps in form["num"]],
        "den": [dict(exps) for _cn, _cd, exps in form["den"]],
        "certificate": cert,
    }


# ── the public op ──────────────────────────────────────────────────────────────


def elliptic_gosper(r) -> Optional[Dict[str, object]]:
    """The ELLIPTIC analog of Gosper's indefinite hypergeometric summation over the
    modified-theta algebra (``x = qⁿ``; the FIRST engine op of the ELLIPTIC F929 row).

    ``r`` is the elliptic-hypergeometric **term ratio** ``t(n+1)/t(n) = r(x)`` — an
    :class:`~srmech.amsc.ellbase.EllRatio` (a theta-quotient ``∏θ(αx;p)/∏θ(βx;p)``
    over an exact-``ℚ`` monomial prefactor), or an ``EllMonomial`` / ``Theta`` the
    carrier lifts. The op decides whether ``t(n)`` has an elliptic-hypergeometric
    antidifference ``T(n) = R(x)·t(n)`` (``T(n+1) − T(n) = t(n)``):

    - if it does, returns the **certificate** ``R`` (an ``EllRatio``) as ``{
      "prefactor": {"coeff": (num, den), "exps": {sym: exp}}, "num": [{sym: exp}, …],
      "den": [{sym: exp}, …], "certificate": EllRatio }`` — the theta-quotient
      satisfying the **elliptic Gosper equation** ``R(qx)·r(x) − R(x) = 1`` (so
      ``T(n) = R(qⁿ)·t(n)`` and ``Σ_{n=a}^{b} t(n) = T(b+1) − T(a)``); the verified
      ``EllRatio`` is under the ``"certificate"`` key for an exact re-check;
    - if the term-ratio is **not elliptically balanced** (``r.is_elliptic()`` False —
      out of the row), or no elliptic-hypergeometric antidifference exists, returns
      ``None``.

    Exact over the modified-theta algebra; the additive Gosper equation is decided
    structurally and CERTIFIED in exact ``ℚ`` via
    :meth:`~srmech.amsc.ellbase.EllRatio.eval_trunc` (the theta-quotient carrier is
    multiplicatively but not additively closed). No float, no ``abs()`` (Class-K
    sign), no ``math`` / numpy. See the module docstring for the full elliptic-Gosper
    / theta-Petkovšek pipeline + the verified Gasper–Schlosser reference.
    """
    r = _coerce_ratio(r)
    if r.is_zero:
        # the trivial term ratio: no nonzero elliptic-hypergeometric closed form to
        # certify (mirrors gosper's num ≡ 0 leaf).
        return None
    # the row gate: an unbalanced (non-elliptic) term-ratio is honestly out of the
    # row (Gasper–Schlosser balancing Eq. (2.4)).
    if not r.is_elliptic():
        return None

    nat = _native()
    if nat is not None:
        try:
            got = nat.elliptic_gosper_c(_ratio_to_form(r))
            # The C peer ACCELERATES the positive (certificate-found) case only: a
            # has=1 result is byte-identical to the pure path AND is re-verified here
            # in exact ℚ before it is trusted. A has=0 is NOT a definitive "no
            # certificate" — it falls through to the complete pure-Python path.
            if got is not None:
                has, cert_form = got
                if has:
                    cert = _form_to_ratio(cert_form)
                    if _verifies_gosper_equation(cert, r):
                        return _cert_to_result(cert)
        except (RuntimeError, OverflowError, ValueError):
            pass                                  # fall to the pure path

    return _elliptic_gosper_pure(r)


# ── pure-Python elliptic Gosper (the COMPLETE alternative + the parity oracle) ──


def _elliptic_gosper_pure(r: EllRatio) -> Optional[Dict[str, object]]:
    """The exact pure-Python elliptic-Gosper decider (the complete alternative to the
    C peer). Enumerates the bounded theta-monomial-quotient certificate family from
    ``r``'s theta factors + the theta-dispersion q-steps, and returns the first that
    VERIFIES the additive Gosper equation ``R(qx)·r − R = 1`` exactly (in ``ℚ``), or
    ``None`` when none does. See the module docstring."""
    for cert in _candidate_certificates(r):
        if _verifies_gosper_equation(cert, r):
            return _cert_to_result(cert)
    return None
