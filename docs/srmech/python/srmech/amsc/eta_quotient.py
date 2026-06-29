"""srmech.amsc.eta_quotient — ``EtaQuotient``, a WEIGHT-axis operand carrier.

THE OBJECT
==========

A Dedekind-eta QUOTIENT is

    Q(τ) = ∏_{d | N} η(dτ)^{r_d}

over a finite exponent vector ``{d: r_d}`` (each ``d ≥ 1`` an integer, each
``r_d`` a nonzero integer). With the Dedekind eta

    η(τ) = q^{1/24} · ∏_{m≥1} (1 − q^{m}),   q = e^{2πiτ},

the eta-quotient is an EXACT q-series

    Q(τ) = q^{(Σ_d d·r_d)/24} · ∏_{d} ∏_{m≥1} (1 − q^{dm})^{r_d}

— a leading FRACTIONAL q-power ``q^{leading_power}`` (the order at the ∞ cusp /
the q-valuation) times an EXACT INTEGER power series. ``EtaQuotient`` represents
this object exactly: the integer power series (:meth:`q_series`) is numpy-free
exact Python ``int`` (the coefficients grow — e.g. the Ramanujan τ — and are
kept EXACT, no float, no int64 ceiling), the :attr:`weight` and
:attr:`leading_power` are exact :class:`~srmech.amsc.q.Q` rationals.

THE TWO GRADINGS
================

This carrier lives on the **WEIGHT axis** (peer of
:class:`~srmech.amsc.unary_theta.UnaryTheta` / the harmonic-Maass +
:class:`~srmech.amsc.riemann_theta.RiemannTheta` genus carriers), and it carries
TWO distinct gradings:

  * the **q-scale grading** — the exact q-series is the q-graded structure (the
    SAME scale structure the elliptic carrier's ``qshift σ`` grades by); and
  * the **WEIGHT** ``k = ½ Σ_d r_d`` — the modular AUTOMORPHY covariance, the
    ``(cτ+d)^k`` degree of ``Q`` under ``τ → −1/τ`` (a half-integer in general,
    so it is the natural home for the exact-:class:`~srmech.amsc.q.Q` weight axis,
    exactly as :class:`~srmech.amsc.unary_theta.UnaryTheta` carries a
    half-integral weight).

THE EXACT MODULARITY DECISION (Ligozat; the carrier's CORE)
==========================================================

``EtaQuotient`` is a STRUCTURAL-CONSTRUCT carrier: the q-series + the weight +
the leading power are COMPUTED from the exponents exactly, and modularity is
DECIDED by EXACT INTEGER congruences (NOT a solve). The decision is the
**Ligozat criterion** (Ono, *The Web of Modularity: Arithmetic of the
Coefficients of Modular Forms and q-Series*, CBMS 102 (2004), Theorem 1.64 / 1.65;
G. Ligozat, *Courbes modulaires de genre 1*, Bull. SMF Mém. 43 (1975)). With
``N = lcm(d)`` the Γ₀(N) level:

  * :meth:`is_modular` — ``Q`` is a modular form on Γ₀(N) (with a character)
    iff BOTH integer-congruence conditions hold:

        (i)  Σ_d  d·r_d   ≡ 0  (mod 24)
        (ii) Σ_d (N/d)·r_d ≡ 0 (mod 24)

    Pure integer arithmetic; the Class-K sign of a residue is an explicit branch,
    never an ALU ``abs()``.

  * :meth:`order_at_cusp` ``(c)`` for ``c | N`` — the order of vanishing of ``Q``
    at the cusp ``c`` of Γ₀(N), the standard Ligozat order-at-cusp formula
    (Ono Thm 1.65):

        ord_c = (N / 24) · Σ_{d|N} gcd(c, d)² · r_d / (gcd(c, N/c) · c · d)

    an exact :class:`~srmech.amsc.q.Q`; and :meth:`is_holomorphic` =
    :meth:`is_modular` AND ``order_at_cusp(c) ≥ 0`` for every ``c | N`` (the
    Class-K sign branch, not ``abs()``).

The keystones (the build gates; the construction IS the answer, no search):

  * **η²⁴ = Δ** — ``EtaQuotient({1: 24})`` is Ramanujan's modular discriminant:
    weight 12, level 1, leading power 1, ``q_series`` (after factoring
    ``q^{1}``) ``= [1, −24, 252, −1472, 4830, −6048, −16744, …]`` (Ramanujan τ);
    a weight-12 cusp form on Γ(1) → ``is_modular`` and ``is_holomorphic``.
  * **the X₀(11) weight-2 newform** — ``EtaQuotient({1: 2, 11: 2})`` =
    η(τ)²η(11τ)²: weight 2, level 11, leading power 1, ``q_series`` ``= [1, −2,
    −1, 2, 1, 2, −2, …]`` (the elliptic-curve newform a(n)); ``is_modular``.

THE OPERAND-IRREPRESENTABLE BOUNDARY (the honest OPEN)
=====================================================

The carrier REPRESENTS eta-quotient modular forms exactly, and DECIDES the
modularity of a GIVEN exponent vector exactly. But the eta-quotient subspace of
``M_k(Γ₀(N))`` is a PROPER subspace: not every weight-``k`` form is an
eta-quotient (Rouse & Webb, *On spaces of modular forms spanned by eta-quotients*,
Adv. Math. 272 (2015) — the eta-quotients span only certain spaces). So deciding
"is a GIVEN q-series an eta-quotient?" is the honest-OPEN — a search over exponent
vectors with no finite closed cutter in general — the operand-IRREPRESENTABLE
boundary, dual to the genus-axis Schottky membership decision (a representable
FORM whose Jacobian-membership DECISION is irrepresentable; the
:class:`~srmech.amsc.riemann_theta.SchottkyFormG4` precedent). This carrier does
NOT build a general "is-eta-quotient" solver — it represents an eta-quotient + and
decides the modularity OF a given exponent vector.

# OPEN: deciding "is a given q-series an eta-quotient?" (a search over exponent
#       vectors; no finite exact cutter in general) is the operand-irrepresentable
#       boundary of this carrier — NOT built here (dual of the Schottky membership
#       decision: representable form, irrepresentable membership decision).

THE C PEER
==========

The C peer ``srmech_eta_quotient_qseries`` (``c/src/srmech_eta_quotient.c``)
mirrors the compute kernel — the EXACT INTEGER product expansion
``∏_d ∏_{m≥1} (1 − q^{dm})^{r_d}`` — over the caller-arena ``srmech_bigint``
substrate (the same exact-integer substrate as ``srmech_poly`` /
``srmech_unary_theta``; the coefficients grow without an int64 ceiling), malloc-
free + JPL-clean. The pure-Python body here is the COMPLETE alternative + the C
peer's parity oracle — both emit byte-identical exact integer coefficients. The
Ligozat/cusp DECISION logic stays Python-only (the carrier precedent: the
``EllRatio.is_elliptic`` decision is Python while its compute kernel is the C
peer) — the q-series expansion is the compute kernel that needs the C peer.
"""

from __future__ import annotations

from typing import Dict, List, Mapping

from . import cyclic as _cyclic
from .q import Q

__all__ = ["EtaQuotient", "eta_quotient"]


def _native():
    """The native ``_native`` module IF the rc82 ``srmech_eta_quotient_qseries``
    peer is present + bound, else ``None`` — so the carrier dispatches the exact-
    integer q-series product to C when available and falls cleanly to the pure-
    Python body (the complete alternative + the parity oracle). Imported lazily to
    avoid a bootstrap cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    probe = getattr(nat, "has_native_eta_quotient", None)
    return nat if (probe is not None and probe()) else None


class EtaQuotient:
    """A numpy-free EXACT Dedekind-eta QUOTIENT

        Q(τ) = ∏_{d | N} η(dτ)^{r_d}
             = q^{(Σ_d d·r_d)/24} · ∏_d ∏_{m≥1} (1 − q^{dm})^{r_d}

    — an operand carrier on the WEIGHT axis. Immutable. Holds the exponent vector
    ``{d: r_d}`` (each ``d ≥ 1`` int, each ``r_d`` nonzero int). The
    :attr:`weight` ``= ½ Σ_d r_d`` (exact :class:`~srmech.amsc.q.Q`, the modular
    automorphy grade); the q-series (:meth:`q_series`) is exact-integer; the
    modularity decision (:meth:`is_modular`) is the exact-integer Ligozat
    criterion. See the module docstring for the keystones + the operand-side OPEN
    (the proper eta-quotient subspace)."""

    __slots__ = ("_exps",)

    def __init__(self, exponents: Mapping[int, int]) -> None:
        if not isinstance(exponents, Mapping):
            raise TypeError(
                f"EtaQuotient takes a mapping {{d: r_d}}; got {type(exponents).__name__}")
        canon: Dict[int, int] = {}
        for d, r in exponents.items():
            di, ri = int(d), int(r)
            if di < 1:
                raise ValueError(
                    f"each eta-argument multiplier d must be a positive int; got {d!r}")
            if ri == 0:
                continue  # a zero exponent contributes η^0 = 1 → drop it (canonicalise)
            canon[di] = canon.get(di, 0) + ri
        # a re-collapse may zero a key (e.g. {1: 2, 1: -2} via a non-dict mapping)
        canon = {d: r for d, r in canon.items() if r != 0}
        if not canon:
            raise ValueError(
                "EtaQuotient must have at least one nonzero exponent (the empty "
                "product η^0 ≡ 1 is not an eta-quotient form)")
        # canonical order: sorted by d (deterministic repr / equality)
        self._exps = tuple(sorted(canon.items()))

    # ── accessors ──────────────────────────────────────────────────────────────
    @property
    def exponents(self) -> Dict[int, int]:
        """The canonical exponent vector ``{d: r_d}`` (sorted by ``d``, no zeros)."""
        return dict(self._exps)

    @property
    def level(self) -> int:
        """The Γ₀(N) level ``N = lcm(d)`` over the eta-argument multipliers ``d``
        (Class-I ``cyclic.lcm``)."""
        n = 1
        for d, _r in self._exps:
            n = _cyclic.lcm(n, d)
        return n

    @property
    def weight(self) -> Q:
        """The modular WEIGHT ``k = ½ Σ_d r_d`` — the ``(cτ+d)^k`` automorphy
        covariance grade (a half-integer in general → exact
        :class:`~srmech.amsc.q.Q`). THE WEIGHT AXIS."""
        return Q(sum(r for _d, r in self._exps), 2)

    @property
    def leading_power(self) -> Q:
        """The leading q-power ``(Σ_d d·r_d)/24`` — the q-valuation / order at the
        ∞ cusp (the fractional ``q``-power factored out so :meth:`q_series` returns
        an INTEGER series). Exact :class:`~srmech.amsc.q.Q` (e.g. ``Q(1, 1)`` for
        η²⁴ and η²η²(11τ))."""
        return Q(sum(d * r for d, r in self._exps), 24)

    # ── the q-series (exact integer coefficients) ──────────────────────────────
    def q_series(self, n_terms: int) -> List[int]:
        """The exact INTEGER coefficient list ``[c_0, c_1, …, c_{n_terms−1}]`` of
        the power series

            ∏_d ∏_{m≥1} (1 − q^{dm})^{r_d}

        (the eta-quotient AFTER factoring the leading ``q^{leading_power}``; the
        actual form is ``q^{leading_power} · Σ_e c_e q^e``). The coefficients are
        exact Python ``int`` (they grow — e.g. the Ramanujan τ — and are kept
        EXACT, no float, no int64 ceiling). A negative ``r_d`` rides the
        geometric ``1/(1 − x)`` expansion (Class-K sign branch, no ``abs()``).

        For η²⁴ this is ``[1, −24, 252, −1472, 4830, −6048, −16744, …]`` (Ramanujan
        τ); for η²η²(11τ) it is ``[1, −2, −1, 2, 1, 2, −2, …]`` (the X₀(11)
        newform). DISPATCHES to the native ``srmech_eta_quotient_qseries`` C peer
        when loaded (a 1:1 exact-integer mirror — the C coefficients EQUAL the
        Python coefficients, trusted only on a native hit); else the pure-Python
        :meth:`_q_series_py` body (the COMPLETE alternative + the parity oracle).
        No numpy / ``math``."""
        if not isinstance(n_terms, int) or n_terms < 1:
            raise ValueError(f"n_terms must be a positive int; got {n_terms!r}")
        nat = _native()
        if nat is not None:
            try:
                ds = [d for d, _r in self._exps]
                rs = [r for _d, r in self._exps]
                got = nat.eta_quotient_qseries_c(ds, rs, n_terms)
                if got is not None:
                    return got
            except (RuntimeError, OverflowError, ValueError):
                pass  # fall to the pure path
        return self._q_series_py(n_terms)

    def _q_series_py(self, n_terms: int) -> List[int]:
        """The COMPLETE pure-Python ``q_series`` (the parity oracle for the C peer):
        the exact integer coefficients of ``∏_d ∏_{m≥1} (1 − q^{dm})^{r_d}`` to
        ``n_terms`` terms (``q^0 .. q^{n_terms−1}``). Builds the product factor by
        factor: ``(1 − q^e)`` multiplies are a backward subtract-shift; the
        reciprocal ``1/(1 − q^e)`` is the forward add-shift geometric expansion
        (the Class-K sign branch chooses which, never an ALU ``abs()``). All exact
        integer, no float / numpy / ``math``."""
        res = [0] * n_terms
        res[0] = 1
        for d, r in self._exps:
            m = 1
            while d * m < n_terms:
                e = d * m
                if r > 0:
                    # multiply by (1 − q^e), |r| times: res[i] -= res[i − e]
                    for _ in range(r):
                        for i in range(n_terms - 1, e - 1, -1):
                            res[i] -= res[i - e]
                else:
                    # r < 0 (Class-K sign branch): multiply by 1/(1 − q^e), |r|
                    # times via the forward add-shift geometric expansion
                    times = -r
                    for _ in range(times):
                        for i in range(e, n_terms):
                            res[i] += res[i - e]
                m += 1
        return res

    # ── the Ligozat modularity decision (the carrier's core) ───────────────────
    def is_modular(self) -> bool:
        """The exact-integer LIGOZAT decision: ``Q`` is a modular form on Γ₀(N)
        (with a character) iff BOTH integer congruences hold (Ono, *The Web of
        Modularity*, Thm 1.64):

            (i)  Σ_d  d·r_d   ≡ 0 (mod 24)
            (ii) Σ_d (N/d)·r_d ≡ 0 (mod 24)

        ``N = lcm(d)``. Pure integer arithmetic — no float, no ``abs()``. (A
        Python ``%`` on a negative numerator already floor-reduces into
        ``{0, …, 23}``, so the congruence test is sign-clean without a branch.)"""
        n = self.level
        cond_i = sum(d * r for d, r in self._exps) % 24 == 0
        cond_ii = sum((n // d) * r for d, r in self._exps) % 24 == 0
        return cond_i and cond_ii

    def order_at_cusp(self, c: int) -> Q:
        """The order of vanishing of ``Q`` at the cusp ``c`` of Γ₀(N) (``c | N``),
        the standard Ligozat order-at-cusp formula (Ono Thm 1.65):

            ord_c = (N / 24) · Σ_{d|N} gcd(c, d)² · r_d / (gcd(c, N/c) · c · d)

        an exact :class:`~srmech.amsc.q.Q`. ``c`` must be a positive divisor of
        ``N`` (a cusp representative) — rejected loudly otherwise (an honest
        boundary). Class-I ``cyclic.gcd``; exact rational accumulation; no float,
        no ``abs()``."""
        if not isinstance(c, int) or c < 1:
            raise ValueError(f"the cusp c must be a positive int divisor of N; got {c!r}")
        n = self.level
        if n % c != 0:
            raise ValueError(
                f"the cusp c={c} must divide the level N={n} (a cusp representative "
                "of Γ₀(N)); an honest boundary, not a fabricated reduction")
        # the per-cusp denominator factor gcd(c, N/c)·c (constant across d)
        g_outer = _cyclic.gcd(c, n // c)
        total = Q(0, 1)
        for d, r in self._exps:
            g = _cyclic.gcd(c, d)
            # gcd(c,d)² · r_d / (gcd(c,N/c) · c · d) — exact Q term
            total = total + Q(g * g * r, g_outer * c * d)
        return Q(n, 24) * total

    def is_holomorphic(self) -> bool:
        """True iff ``Q`` is a HOLOMORPHIC modular form on Γ₀(N): :meth:`is_modular`
        AND :meth:`order_at_cusp` ``(c) ≥ 0`` for EVERY positive divisor ``c | N``
        (every cusp). The non-negativity is a Class-K sign branch on the exact
        :class:`~srmech.amsc.q.Q` order (the rational ``num/den`` with a positive
        reduced denominator is ``≥ 0`` iff its numerator is ``≥ 0`` — an explicit
        sign test, never an ALU ``abs()``). Both keystones are holomorphic (every
        cusp order ``= 1 ≥ 0``)."""
        if not self.is_modular():
            return False
        n = self.level
        for c in range(1, n + 1):
            if n % c != 0:
                continue
            o = self.order_at_cusp(c)
            # Class-K sign branch: o ≥ 0 iff numerator ≥ 0 (denominator > 0, reduced)
            if o.numerator < 0:
                return False
        return True

    # ── equality / repr ────────────────────────────────────────────────────────
    def equals(self, other: "EtaQuotient") -> bool:
        """True iff ``other`` is an :class:`EtaQuotient` with the SAME canonical
        exponent vector (the carrier-idiom value equality)."""
        return isinstance(other, EtaQuotient) and self._exps == other._exps

    def __eq__(self, other) -> bool:
        if isinstance(other, EtaQuotient):
            return self._exps == other._exps
        return NotImplemented

    def __ne__(self, other):
        r = self.__eq__(other)
        return r if r is NotImplemented else (not r)

    def __hash__(self) -> int:
        return hash(self._exps)

    def __repr__(self) -> str:
        body = ", ".join(f"{d}:{r}" for d, r in self._exps)
        return (f"EtaQuotient({{{body}}}, weight={self.weight}, level={self.level}, "
                f"leading_power={self.leading_power})")


def eta_quotient(exponents: Mapping[int, int]) -> EtaQuotient:
    """Construct an :class:`EtaQuotient`

        Q(τ) = ∏_{d | N} η(dτ)^{r_d}

    — the public construction helper for the WEIGHT-axis eta-quotient carrier. The
    two keystones:

    - ``eta_quotient({1: 24})`` → η²⁴ = Δ, weight 12, level 1, leading power 1,
      ``q_series = [1, −24, 252, −1472, 4830, −6048, −16744, …]`` (Ramanujan τ);
      ``is_modular`` and ``is_holomorphic``.
    - ``eta_quotient({1: 2, 11: 2})`` → η(τ)²η(11τ)², weight 2, level 11, leading
      power 1, ``q_series = [1, −2, −1, 2, 1, 2, −2, …]`` (the X₀(11) newform);
      ``is_modular``.

    ``exponents`` is a mapping ``{d: r_d}`` (each ``d ≥ 1`` int, each ``r_d``
    nonzero int). Exact-integer q-series, exact-``Q`` weight / leading power /
    cusp orders; no float, no ``abs()``, no numpy / ``math``."""
    return EtaQuotient(exponents)
