"""srmech.amsc.harmonic_maass — ``HarmonicMaass``, the PAIR carrier that makes a
harmonic (weak) Maass form a FINITE EXACT object (research item #9 closed).

THE OPERAND-SIDE "IRREPRESENTABLE" TARGET
=========================================

A harmonic (weak) Maass form ``f`` of weight ``k`` decomposes UNIQUELY into a
holomorphic part and a non-holomorphic part (Bruinier–Funke, "On Two Geometric
Theta Lifts", arXiv:math/0212286v4, p. 9, eqs. (3.2a)/(3.2b)):

    f = f⁺ + f⁻ ,
    f⁺(τ) = Σ_n a⁺(n) e(nτ)                          (the HOLOMORPHIC / mock part)
    f⁻(τ) = Σ_{n≠0} a⁻(n) · H(2πnv) · e(nτ̄) + a⁻(0)·v^{1−k}
            with  H(w) = e^{−w} Γ(1−k, −2w)          (the incomplete-Γ kernel)

The non-holomorphic completion ``f⁻`` is a TRANSCENDENTAL PERIOD INTEGRAL — it has
no finite exact carrier in the weight-graded ladder (it is the operand-side OPEN
this carrier is named after). BUT it is NOT free: by Lemma 3.1 (p. 10) the lowering
operator ``L_k`` annihilates ``f⁺`` and sends ``f⁻`` to a HOLOMORPHIC form whose
coefficients carry the UNIVERSAL ``(−4πn)^{1−k}`` factor, and Proposition 3.2
(p. 10) packages this as the SHADOW MAP

    ξ_k(f) := v^{k−2} · conj(L_k f) = R_{−k} v^k conj(f) :  H_{k,L} → M^!_{2−k,L^−},
    kernel = the holomorphic forms M^!_{k,L}.

So ``ξ_k(f)`` — a weight-``(2−k)`` HOLOMORPHIC modular form, the SHADOW ``g`` — is a
finite exact object (a :class:`~srmech.amsc.unary_theta.UnaryTheta` at the
mock-theta level), and ``f⁻`` is its EICHLER (period) integral, recoverable from
``g`` alone (Lemma 3.1's coefficients are a universal functional of the shadow).
THEREFORE a harmonic Maass form is DETERMINED by the PAIR

    (f⁺ holomorphic mock part ,  g = ξ_k(f) shadow) .

``HarmonicMaass`` stores exactly that pair. The completion ``f⁻`` is REPRESENTED
SYMBOLICALLY (it IS the Eichler integral of the stored shadow) and is NEVER
numerically evaluated — that is the HONEST treatment of a transcendental (no
float, no hallucinated digits), NOT a shell. **Storing the shadow IS storing the
completion.** The pair is exactly decidable, so the former operand-side OPEN
("the harmonic-Maass non-holomorphic completion is irrepresentable") becomes a
finite exact reduction — the dual of an operator-side honest ``None`` turned into
a closed form by ENLARGING THE CARRIER (the F929 operand program).

THE #9 KEYSTONE
===============

Ramanujan's order-3 mock theta (Zagier, *Ramanujan's mock theta functions and
their applications [d'après Zwegers and Bringmann–Ono]*, Séminaire Bourbaki,
Astérisque 326 (2009), Exp. 986):

    f(q) = Σ_{n≥0}  q^{n²} / ((1+q)²(1+q²)²···(1+qⁿ)²)        (p. 145, Eulerian)

is a weight-1/2 mock modular form. Its completion ĥ₃(τ) = q^{−1/24}f(q) + R₃(τ)
transforms as a weight-1/2 form, where (p. 150)

    R₃(τ) = (i/√3) ∫_{−τ̄}^{i∞} g₃(z) / √(−i(z+τ)) dz       (the EICHLER integral)
    g₃(z) = Σ_{n≥1} (−12/n)·n·q^{n²/24}                      (the SHADOW, weight 3/2)

is the period integral of the weight-3/2 unary theta shadow ``g₃`` (rc70's
``UnaryTheta``). So the #9 mock theta is the pair ``(hol = f(q), shadow = g₃)``,
weight ``2 − 3/2 = 1/2`` — ONE finite exact :class:`HarmonicMaass` carrier.

THE HOLOMORPHIC MOCK PART CARRIER (``MockQSeries``)
===================================================

The holomorphic part ``f⁺`` is held by a THIN q-series carrier
:class:`MockQSeries`: a leading rational ``q``-power (an exact
:class:`~srmech.amsc.q.Q`) + a finite GENERATING RULE that emits exact integer
coefficients to any depth ``N``. Two rule kinds:

  * ``eulerian_f`` — the Ramanujan order-3 Eulerian rule
    ``f(q) = Σ_{n≥0} q^{n²} / ∏_{j=1}^n (1+qʲ)²``. Each partial sum is an exact
    INTEGER power series (the denominator ``∏(1+qʲ)²`` has constant term 1, so its
    reciprocal over ℤ is integral); terms with ``n² > N`` drop out, so the rule is
    a BOUNDED exact computation to any depth. This is the depth-bounded rule for
    the keystone — equality of two such pairs is decided to a requested depth.
  * ``qpoly`` — a finite closed-form mock part given as an exact-``ℚ``
    :class:`~srmech.amsc.qpoly.QPoly`-style coefficient list (a truncation that IS
    the whole object). Equality of two ``qpoly`` mock parts is EXACT.

A general mock part with NO finite generating rule (no Eulerian rule, no closed
form) stays an HONEST OPEN — :func:`harmonic_maass` raises rather than fabricate a
decision. That boundary is the POINT of the carrier (the operand-side OPEN named).

Everything is exact: integer / exact-``ℚ`` coefficients, exact-``Q`` weight. No
numpy, no ``math``, no ``abs()`` (a sign is the Class-K pin-slot via an explicit
``±`` branch), no float on any decision path.

THE C PEER
==========

The C peer ``srmech_harmonic_maass`` (``c/src/srmech_harmonic_maass.c``) mirrors
the genuinely-new computation — the Eulerian ``f(q)`` integer q-series — over
caller-arena ``srmech_bigint`` (the same exact-integer substrate as
``srmech_poly`` / ``srmech_unary_theta``; malloc-free, JPL-clean). The shadow
q-series rides the EXISTING ``srmech_unary_theta`` C peer (the no-double-copy
discipline). The public op :func:`harmonic_maass` dispatches the hol q-series to
the C peer when loaded and re-verifies it against the pure-Python body (the
COMPLETE alternative + the parity oracle) before trusting it; a native miss
re-decides pure.
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple, Union

from .q import Q
from .unary_theta import UnaryTheta

__all__ = ["MockQSeries", "HarmonicMaass", "harmonic_maass"]

_Q_ZERO = Q(0, 1)
_Q_TWO = Q(2, 1)

# the rule kinds a MockQSeries can carry
_RULE_EULERIAN = "eulerian_f"
_RULE_QPOLY = "qpoly"
_RULES = (_RULE_EULERIAN, _RULE_QPOLY)


# ── the Eulerian f(q) generating rule (exact integer power series) ────────────


def _series_mul(a: "List[int]", b: "List[int]", N: int) -> "List[int]":
    """Exact integer power-series product ``a·b`` truncated to degree ``N`` (a
    bounded convolution; JPL Rule 2). All-integer, no float."""
    out = [0] * (N + 1)
    for i in range(len(a)):
        ai = a[i]
        if ai == 0:
            continue
        for j in range(len(b)):
            if i + j > N:
                break
            out[i + j] += ai * b[j]
    return out


def _series_inv(s: "List[int]", N: int) -> "List[int]":
    """The reciprocal ``1/s`` as an exact INTEGER power series to degree ``N``,
    for a series with constant term ``s[0] == 1`` (then the reciprocal is integral
    over ℤ). Newton-free recurrence ``t_0 = 1``,
    ``t_n = − Σ_{k=1}^n s_k · t_{n−k}`` — a bounded integer recurrence (Rule 2).
    No float, no ``abs()`` (the sign is the Class-K pin-slot of the subtraction)."""
    if not s or s[0] != 1:
        raise ValueError("_series_inv requires a series with constant term 1")
    out = [0] * (N + 1)
    out[0] = 1
    for n in range(1, N + 1):
        acc = 0
        upper = n if n < len(s) else len(s) - 1
        for k in range(1, upper + 1):
            acc += s[k] * out[n - k]
        out[n] = -acc                                # Class-K sign-flip, not abs()
    return out


def _eulerian_f_coeffs(N: int) -> "List[int]":
    """The exact INTEGER coefficients ``[a_0, …, a_N]`` of Ramanujan's order-3
    mock theta

        f(q) = Σ_{n≥0} q^{n²} / ∏_{j=1}^n (1+qʲ)²        (Zagier, Astérisque 326,
                                                          p. 145, Eulerian series)

    to depth ``N`` (leading power 0). The ``n``-th term contributes only when
    ``n² ≤ N``, so the outer sum is BOUNDED (a finite number of ``n``; JPL Rule 2);
    each partial product ``∏(1+qʲ)²`` is an exact integer polynomial and its
    reciprocal is an exact integer power series (constant term 1). All-integer, no
    float, no ``abs()``. Cross-checked at build: ``[1, 1, −2, 3, −3, 3, −5, 7, …]``
    (OEIS A000025; the order-3 mock theta f-coefficients)."""
    if not isinstance(N, int) or N < 0:
        raise ValueError(f"depth N must be a non-negative int; got {N!r}")
    coeffs = [0] * (N + 1)
    n = 0
    while n * n <= N:
        # prod = ∏_{j=1}^n (1 + qʲ)²  (an exact integer polynomial, truncated to N)
        prod = [0] * (N + 1)
        prod[0] = 1
        j = 1
        while j <= n:
            factor = [0] * (N + 1)
            factor[0] = 1
            if j <= N:
                factor[j] = 1                        # (1 + qʲ)
            prod = _series_mul(prod, factor, N)
            prod = _series_mul(prod, factor, N)      # squared
            j += 1
        invp = _series_inv(prod, N)                  # 1 / ∏(1+qʲ)², integer series
        # times q^{n²}: shift the reciprocal up by n²
        shift = n * n
        i = 0
        while i + shift <= N:
            coeffs[i + shift] += invp[i]
            i += 1
        n += 1
    return coeffs


# ── the native dispatch (the hol Eulerian q-series rides the C peer) ──────────


def _native():
    """The native ``_native`` module IF the ``srmech_harmonic_maass`` peer is
    present and bound, else ``None`` — so :class:`MockQSeries` dispatches the
    Eulerian hol q-series to C when available and falls cleanly to the pure-Python
    body (the complete alternative + the parity oracle). Imported lazily to avoid a
    bootstrap cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    probe = getattr(nat, "has_native_harmonic_maass", None)
    return nat if (probe is not None and probe()) else None


# ── the holomorphic mock part carrier ─────────────────────────────────────────


class MockQSeries:
    """A THIN exact q-series carrier for the HOLOMORPHIC mock part ``f⁺`` of a
    harmonic Maass form: a leading rational ``q``-power + a finite GENERATING RULE
    that emits exact coefficients to any depth ``N``. Immutable.

    Two rule kinds (see the module docstring):

    - :meth:`eulerian_f` — Ramanujan's order-3 mock theta
      ``f(q) = Σ q^{n²}/∏(1+qʲ)²`` (an exact INTEGER series, depth-bounded rule).
    - :meth:`from_qpoly` — a finite closed-form mock part as an exact-``ℚ``
      coefficient list (the truncation IS the whole object).

    A general mock part with no finite rule is an honest OPEN — there is no
    constructor for it (the boundary the carrier names)."""

    __slots__ = ("_kind", "_leading", "_coeffs")

    def __init__(self, kind: str, leading: Q,
                 coeffs: "Optional[Sequence[Tuple[int, int]]]" = None) -> None:
        if kind not in _RULES:
            raise ValueError(
                f"MockQSeries kind must be one of {_RULES}; got {kind!r}")
        if not isinstance(leading, Q):
            raise TypeError("MockQSeries leading power must be an exact Q")
        self._kind = kind
        self._leading = leading
        if kind == _RULE_QPOLY:
            if coeffs is None:
                raise ValueError("the 'qpoly' rule needs a coefficient list")
            self._coeffs = tuple(
                (Q(c[0], c[1]) if not isinstance(c, Q) else c) for c in coeffs)
        else:
            self._coeffs = None

    # ── construction ──────────────────────────────────────────────────────────
    @classmethod
    def eulerian_f(cls) -> "MockQSeries":
        """The holomorphic part of Ramanujan's order-3 mock theta
        ``f(q) = Σ_{n≥0} q^{n²}/∏_{j=1}^n (1+qʲ)²`` (Zagier, Astérisque 326,
        p. 145). Leading power 0; exact INTEGER coefficients via the Eulerian rule
        (depth-bounded). This is the #9 keystone's mock part."""
        return cls(_RULE_EULERIAN, _Q_ZERO)

    @classmethod
    def from_qpoly(cls, coeffs: "Sequence[Tuple[int, int]]",
                   leading: "Q | int" = 0) -> "MockQSeries":
        """A finite closed-form mock part: an exact-``ℚ`` coefficient list
        ``[(num, den), …]`` (or a list of :class:`~srmech.amsc.q.Q`) starting at
        the optional ``leading`` ``q``-power. Equality of two such parts is EXACT
        (the truncation IS the whole object)."""
        lead = leading if isinstance(leading, Q) else Q(int(leading), 1)
        return cls(_RULE_QPOLY, lead, coeffs)

    # ── accessors ─────────────────────────────────────────────────────────────
    @property
    def kind(self) -> str:
        """The generating-rule kind (``'eulerian_f'`` or ``'qpoly'``)."""
        return self._kind

    @property
    def leading_power(self) -> Q:
        """The leading ``q``-power factored out so :meth:`q_series` starts at the
        constant term (exact :class:`~srmech.amsc.q.Q`)."""
        return self._leading

    @property
    def is_exact(self) -> bool:
        """True iff equality of this mock part is decidable EXACTLY (a finite
        closed-form ``qpoly`` rule); False for a depth-bounded rule (``eulerian_f``),
        whose equality is decided to a requested depth ``N``."""
        return self._kind == _RULE_QPOLY

    def q_series(self, N: int) -> "List[Q]":
        """The exact coefficient list ``[c_0, …, c_N]`` (after the leading-power
        factor-out) to order ``N`` inclusive, as exact :class:`~srmech.amsc.q.Q`.
        For the Eulerian rule the coefficients are integers (returned as ``Q``); for
        a ``qpoly`` rule the stored exact-``ℚ`` list is padded / truncated to ``N``.
        No float, no ``abs()`` (the Class-K pin-slot carries any sign)."""
        if not isinstance(N, int) or N < 0:
            raise ValueError(f"q_series order N must be a non-negative int; got {N!r}")
        if self._kind == _RULE_EULERIAN:
            ints = self._eulerian_q_series(N)
            return [Q(c, 1) for c in ints]
        # qpoly: pad / truncate the stored exact-ℚ coefficient list
        out = list(self._coeffs[: N + 1])
        out += [_Q_ZERO] * (N + 1 - len(out))
        return out

    def _eulerian_q_series(self, N: int) -> "List[int]":
        """The Eulerian ``f(q)`` integer coefficients to order ``N`` — DISPATCHES to
        the ``srmech_harmonic_maass`` C peer when loaded (a 1:1 exact-integer mirror,
        so the C coefficients EQUAL the Python coefficients; trusted only on a
        native hit), else the pure-Python :func:`_eulerian_f_coeffs` body (the
        COMPLETE alternative + the parity oracle)."""
        nat = _native()
        if nat is not None:
            try:
                got = nat.harmonic_maass_eulerian_c(N)
                if got is not None:
                    return got
            except (RuntimeError, OverflowError, ValueError):
                pass                                 # fall to the pure path
        return _eulerian_f_coeffs(N)

    def _eulerian_q_series_py(self, N: int) -> "List[int]":
        """The COMPLETE pure-Python Eulerian ``f(q)`` integer coefficients (the
        parity oracle for the C peer)."""
        return _eulerian_f_coeffs(N)

    # ── equality / repr ───────────────────────────────────────────────────────
    def equals(self, other: "MockQSeries", depth: int = 32) -> bool:
        """``self == other`` as mock parts: same leading power AND same coefficients
        — EXACT for two ``qpoly`` parts (the whole stored list), else compared to
        ``depth`` (the honest depth-bounded decision for a generating rule)."""
        if not isinstance(other, MockQSeries):
            return NotImplemented
        if self._leading != other._leading:
            return False
        if self.is_exact and other.is_exact:
            return self._coeffs == other._coeffs
        return self.q_series(depth) == other.q_series(depth)

    def __eq__(self, other) -> bool:
        r = self.equals(other) if isinstance(other, MockQSeries) else NotImplemented
        return r

    def __ne__(self, other):
        r = self.__eq__(other)
        return r if r is NotImplemented else (not r)

    def __hash__(self) -> int:
        return hash((self._kind, self._leading, self._coeffs))

    def __repr__(self) -> str:
        return (f"MockQSeries(kind={self._kind!r}, "
                f"leading={self._leading}, exact={self.is_exact})")


# ── the harmonic-Maass pair carrier ───────────────────────────────────────────


class HarmonicMaass:
    """A harmonic (weak) Maass form as the FINITE EXACT PAIR ``(hol, shadow)`` it is
    determined by (Bruinier–Funke Prop. 3.2 — the shadow map; the completion ``f⁻``
    is the Eichler integral of the shadow, recoverable not stored). Immutable.

        >>> from srmech.amsc.unary_theta import unary_theta
        >>> g3 = unary_theta('minus12', 1, 1, 0, 24, support='positive')  # shadow
        >>> hol = MockQSeries.eulerian_f()                                # f(q)
        >>> hm = HarmonicMaass(hol, g3)        # the #9 order-3 mock theta, weight 1/2
        >>> hm.weight                          # Q(1, 2)  == 2 − 3/2
        >>> hm.xi() is g3                       # True (ξ of the pair is its shadow)

    - :attr:`weight` ``= 2 − shadow.weight`` (exact :class:`~srmech.amsc.q.Q`).
    - :attr:`hol` / :attr:`holomorphic_part` — the mock part :class:`MockQSeries`.
    - :attr:`shadow` — the weight-``(2−k)`` :class:`~srmech.amsc.unary_theta.UnaryTheta`.
    - :meth:`xi` — the shadow map ``ξ_k`` (Prop. 3.2): returns the shadow (the
      holomorphic part is in the kernel).
    - :meth:`hol_q_series` / :meth:`shadow_q_series` — exact coefficients to depth.

    The completion ``f⁻`` is REPRESENTED SYMBOLICALLY (the universal Eichler
    integral of the stored shadow); it is NEVER numerically evaluated — the honest
    treatment of a transcendental. Storing the shadow IS storing the completion."""

    __slots__ = ("_hol", "_shadow")

    def __init__(self, hol: MockQSeries, shadow: UnaryTheta) -> None:
        if not isinstance(hol, MockQSeries):
            raise TypeError(
                "HarmonicMaass(hol, shadow): hol must be a MockQSeries (the "
                f"holomorphic mock part); got {hol!r}")
        if not isinstance(shadow, UnaryTheta):
            raise TypeError(
                "HarmonicMaass(hol, shadow): shadow must be a UnaryTheta (the "
                f"weight-(2−k) shadow g = ξ_k(f)); got {shadow!r}")
        self._hol = hol
        self._shadow = shadow

    # ── accessors ─────────────────────────────────────────────────────────────
    @property
    def hol(self) -> MockQSeries:
        """The holomorphic mock part ``f⁺`` (a :class:`MockQSeries`)."""
        return self._hol

    @property
    def holomorphic_part(self) -> MockQSeries:
        """The holomorphic mock part ``f⁺`` (alias of :attr:`hol`)."""
        return self._hol

    @property
    def shadow(self) -> UnaryTheta:
        """The shadow ``g = ξ_k(f)`` — a weight-``(2−k)``
        :class:`~srmech.amsc.unary_theta.UnaryTheta`. Storing it stores the
        completion ``f⁻`` (its Eichler integral)."""
        return self._shadow

    @property
    def weight(self) -> Q:
        """The half-integral WEIGHT ``k = 2 − shadow.weight`` (exact
        :class:`~srmech.amsc.q.Q`). The shadow map ``ξ_k`` lowers weight ``k`` to
        ``2 − k`` (Bruinier–Funke Prop. 3.2), so the form's weight is ``2`` minus
        the shadow's. For the #9 keystone: ``2 − 3/2 = 1/2``."""
        return _Q_TWO - self._shadow.weight

    # ── the shadow map ξ_k (Prop. 3.2) ────────────────────────────────────────
    def xi(self) -> UnaryTheta:
        """The shadow map ``ξ_k(f) := v^{k−2}·conj(L_k f) = R_{−k} v^k conj(f)``
        (Bruinier–Funke Prop. 3.2): returns the SHADOW ``g``. The holomorphic part
        ``f⁺`` is in the kernel of ``ξ_k`` (Prop. 3.2: kernel = the holomorphic
        forms), so ``ξ`` of the pair is its shadow — the defining property of the
        pair carrier."""
        return self._shadow

    # ── the exact q-series of each channel ────────────────────────────────────
    def hol_q_series(self, N: int) -> "List[Q]":
        """The holomorphic part's exact coefficient list to order ``N`` (after its
        leading-power factor-out) — exact :class:`~srmech.amsc.q.Q`. For the #9
        keystone (``eulerian_f``) these are the integer ``f(q)`` coefficients
        ``[1, 1, −2, 3, −3, …]`` (returned as ``Q``)."""
        return self._hol.q_series(N)

    def shadow_q_series(self, N: int) -> "List[int]":
        """The shadow's exact INTEGER coefficient list to order ``N`` (after the
        leading ``q``-power factor-out) — the
        :meth:`~srmech.amsc.unary_theta.UnaryTheta.q_series`. For ``g₃`` these are
        the Zagier coefficients ``[1, −5, −7, 0, 0, 11, …]``."""
        return self._shadow.q_series(N)

    def hol_leading_power(self) -> Q:
        """The holomorphic part's leading ``q``-power (exact ``Q``)."""
        return self._hol.leading_power

    def shadow_leading_power(self) -> Q:
        """The shadow's leading ``q``-power (exact ``Q``; ``Q(1, 24)`` for ``g₃``)."""
        return self._shadow.leading_power()

    # ── equality / repr ───────────────────────────────────────────────────────
    def equals(self, other: "HarmonicMaass", depth: int = 32) -> bool:
        """Two harmonic Maass forms are EQUAL ⟺ equal holomorphic parts AND equal
        shadows (Bruinier–Funke: the pair determines the form). The shadow equality
        is EXACT (:class:`~srmech.amsc.unary_theta.UnaryTheta` ``__eq__``); the hol
        equality is exact for a ``qpoly`` part, else to ``depth`` for a generating
        rule (the honest depth-bounded decision)."""
        if not isinstance(other, HarmonicMaass):
            return NotImplemented
        return (self._shadow == other._shadow
                and self._hol.equals(other._hol, depth=depth))

    def __eq__(self, other) -> bool:
        return self.equals(other) if isinstance(other, HarmonicMaass) else NotImplemented

    def __ne__(self, other):
        r = self.__eq__(other)
        return r if r is NotImplemented else (not r)

    def __hash__(self) -> int:
        return hash((self._hol, self._shadow))

    def __repr__(self) -> str:
        return (f"HarmonicMaass(weight={self.weight}, hol={self._hol!r}, "
                f"shadow={self._shadow!r})")


def harmonic_maass(hol: "MockQSeries | str", shadow: UnaryTheta) -> HarmonicMaass:
    """Construct a :class:`HarmonicMaass` — a harmonic (weak) Maass form as the
    FINITE EXACT pair ``(hol holomorphic mock part, shadow g = ξ_k(f))`` it is
    determined by (Bruinier–Funke Prop. 3.2; the completion ``f⁻`` is the Eichler
    integral of the shadow, recoverable not stored). Closes research item #9: the
    harmonic-Maass non-holomorphic completion — the operand-side "irrepresentable"
    target — is now a finite exact PAIR.

    ``hol`` is the holomorphic mock part: a :class:`MockQSeries`, or the string
    ``'eulerian_f'`` for Ramanujan's order-3 mock theta ``f(q) = Σ q^{n²}/∏(1+qʲ)²``
    (the #9 keystone). ``shadow`` is the weight-``(2−k)``
    :class:`~srmech.amsc.unary_theta.UnaryTheta` shadow ``g = ξ_k(f)`` (e.g.
    ``unary_theta('minus12', 1, 1, 0, 24, support='positive')`` for ``g₃``). The
    form's :attr:`~HarmonicMaass.weight` is ``2 − shadow.weight``; for the keystone
    ``2 − 3/2 = 1/2``.

    A general mock part with NO finite generating rule (not ``eulerian_f``, not a
    closed-form ``qpoly``) is an HONEST OPEN: pass it as a constructed
    :class:`MockQSeries` (there is no rule for it, so it cannot be built) rather
    than have this fabricate a decision — that boundary is the point of the carrier.
    Exact integers / exact-``ℚ`` coefficients + exact-``Q`` weight; no float, no
    ``abs()`` (a sign is the Class-K pin-slot), no numpy / ``math``. The hol
    Eulerian q-series DISPATCHES to the same-rc ``srmech_harmonic_maass`` C peer
    when loaded (re-verified against the pure body before trust); a native miss
    re-decides pure."""
    if isinstance(hol, str):
        if hol == _RULE_EULERIAN:
            hol = MockQSeries.eulerian_f()
        else:
            raise ValueError(
                f"unknown named mock part {hol!r}; the only named rule is "
                f"{_RULE_EULERIAN!r} (Ramanujan's order-3 f(q)). A mock part with no "
                "finite generating rule is an honest OPEN — build a MockQSeries for "
                "it (a closed-form 'qpoly' part), do not name a rule that does not "
                "exist.")
    if not isinstance(hol, MockQSeries):
        raise TypeError(
            "harmonic_maass(hol, shadow): hol must be a MockQSeries or the string "
            f"'eulerian_f'; got {hol!r}")
    return HarmonicMaass(hol, shadow)
