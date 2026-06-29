"""srmech.amsc.eisenstein — ``Eisenstein``, a WEIGHT-axis operand carrier.

THE OBJECT
==========

The normalized Eisenstein series of even weight ``k ≥ 4`` is the EXACT-RATIONAL
q-series modular form

    E_k(τ) = 1 − (2k / B_k) · Σ_{n≥1} σ_{k−1}(n) qⁿ,   q = e^{2πiτ},

where ``B_k`` is the ``k``-th Bernoulli number (an exact rational, e.g.
``B_4 = −1/30``, ``B_6 = 1/42``, ``B_12 = −691/2730``) and
``σ_{k−1}(n) = Σ_{d|n} d^{k−1}`` is the exact-integer divisor power sum. The
coefficients are rational in GENERAL — for ``k = 4, 6, 8, 10, 14`` the prefactor
``−2k/B_k`` happens to be an integer (240, −504, 480, −264, −24), but for
``k = 12`` it is ``65520/691`` and for ``k = 16`` it is ``16320/3617`` — so the
carrier keeps EVERY coefficient as an exact :class:`~srmech.amsc.q.Q` rational,
never collapsing to a float (the whole reason the coefficients are ``Q`` not
``int``).

``Eisenstein`` is a STRUCTURAL-CONSTRUCT carrier: the q-series + the weight + the
leading power are COMPUTED from ``k`` exactly (Bernoulli recurrence + divisor
power sum), NOT a solve. It is the peer of
:class:`~srmech.amsc.eta_quotient.EtaQuotient` /
:class:`~srmech.amsc.unary_theta.UnaryTheta` /
:class:`~srmech.amsc.riemann_theta.RiemannTheta` on the WEIGHT axis — the SECOND
weight rung after the rc82 eta-quotient.

THE TWO GRADINGS
================

  * the **q-scale grading** — the exact-:class:`~srmech.amsc.q.Q` q-series is the
    q-graded structure (the SAME scale structure the eta-quotient / elliptic
    carriers grade by); and
  * the **WEIGHT** ``k`` — the modular AUTOMORPHY covariance, the ``(cτ+d)^k``
    degree of ``E_k`` under ``τ → −1/τ`` (an EVEN INTEGER ``≥ 4`` for the
    level-1 holomorphic Eisenstein series). THE WEIGHT AXIS.

WHY E_k GENERATES THE RING (the carrier's place)
================================================

``E_4`` and ``E_6`` generate the WHOLE graded ring of level-1 modular forms,

    M_*(SL₂(ℤ)) = ℂ[E_4, E_6]

(a classical structure theorem — Serre, *A Course in Arithmetic*, GTM 7 (1973),
Ch. VII §3; Zagier, *Elliptic Modular Forms and Their Applications*, in *The
1-2-3 of Modular Forms*, Springer (2008), §2.2). Every level-1 holomorphic
modular form is a polynomial in ``E_4`` and ``E_6``; the higher even weights are
PRODUCTS of these two — the carrier proves this on its own ladder:

  * ``E_4² = E_8``  (the space ``M_8`` is 1-dimensional);
  * ``E_4·E_6 = E_10``  (``M_10`` is 1-dimensional); and
  * the CROSS-RUNG keystone tying the WEIGHT axis back to rc82:

        E_4³ − E_6² = 1728·Δ = 1728·η²⁴

    — the q-series of ``E_4³ − E_6²`` (an exact-:class:`~srmech.amsc.q.Q`
    convolution; the constant term is 0, a CUSP form) equals ``1728`` times the
    Ramanujan discriminant ``Δ = η²⁴``, i.e. ``(E_4³ − E_6²)[n] = 1728·τ(n)``.
    Validated against the PUBLISHED rc82 carrier
    :class:`~srmech.amsc.eta_quotient.EtaQuotient` ``({1: 24})`` — the carrier
    ladder validates itself.

The rc84 ring rung will build the polynomial-in-(E_4, E_6) decomposition ON this
carrier.

THE OPERAND-IRREPRESENTABLE BOUNDARY (the honest OPEN)
=====================================================

(1) **the k = 2 QUASIMODULAR boundary.** ``E_2`` is NOT a modular form: the
    weight-2 space ``M_2(SL₂(ℤ))`` is ``{0}``, and ``E_2`` picks up a
    non-holomorphic correction under ``τ → −1/τ`` (it is QUASIMODULAR — Zagier,
    op. cit., §2.3; ``E_2(−1/τ) = τ²E_2(τ) + 12τ/(2πi)``). The carrier REJECTS
    ``k = 2`` — it NAMES the quasimodular boundary rather than silently producing
    a non-modular series. The natural next-theory is the QUASIMODULAR RING
    ``ℂ[E_2, E_4, E_6]`` (the ring of quasimodular forms), NOT built here.

(2) **the LEVEL boundary.** This carrier is the LEVEL-1 (``SL₂(ℤ)``) Eisenstein
    series. The higher-level / nebentypus Eisenstein series ``E_{k,χ}`` (the
    weight-``k`` Eisenstein series attached to a Dirichlet character pair on
    ``Γ₀(N)`` — Diamond & Shurman, *A First Course in Modular Forms*, GTM 228
    (2005), §4.5–4.8) are the boundary, NOT built here.

Both are the operand-side dual of the genus-axis Schottky / eta-quotient-subspace
OPENs: the level-1 even-``k`` Eisenstein series is REPRESENTABLE here exactly;
the quasimodular ``E_2`` and the higher-level ``E_{k,χ}`` are NAMED-OPEN beyond
this carrier (a representable family with an irrepresentable enlargement, dual to
the :class:`~srmech.amsc.eta_quotient.EtaQuotient` proper-subspace OPEN and the
:class:`~srmech.amsc.riemann_theta.SchottkyFormG4` membership-decision OPEN).

# OPEN: E_2 is QUASIMODULAR, not modular (M_2(SL₂(ℤ)) = {0}); named, not built —
#       the next-theory is the quasimodular ring ℂ[E_2, E_4, E_6].
# OPEN: level-1 only; higher-level / nebentypus Eisenstein E_{k,χ} on Γ₀(N) is the
#       level boundary — not built here (operand-irrepresentable enlargement).

THE C PEER
==========

The C peer ``srmech_eisenstein_qseries`` (``c/src/srmech_eisenstein.c``) mirrors
the compute kernel — the EXACT-RATIONAL coefficient list — over the caller-arena
``srmech_bigint`` substrate (the same exact-integer foundation as ``srmech_poly``
/ ``srmech_eta_quotient``, here carrying reduced ``num/den`` pairs). It computes
``B_k`` as an exact rational by the Bernoulli recurrence over bignum rationals,
``σ_{k−1}(n)`` as an exact integer, and the reduced rational coefficient
``c_n = −(2k/B_k)·σ_{k−1}(n)`` — covering the GENUINE rational case
(``k = 12 → 65520/691``), NOT just the integer-coeff weights. The pure-Python
body here is the COMPLETE alternative + the C peer's parity oracle; both emit
byte-identical reduced ``(num, den)`` coefficients. malloc-free + JPL-clean;
additive symbols → ABI unchanged (stays 3). Carrier-internal (like
``srmech_poly`` / ``srmech_eta_quotient``): NOT a Rosetta ledger op.
"""

from __future__ import annotations

from typing import List

from .q import Q

__all__ = ["Eisenstein", "eisenstein"]


def _native():
    """The native ``_native`` module IF the rc83 ``srmech_eisenstein_qseries``
    peer is present + bound, else ``None`` — so the carrier dispatches the exact-
    rational q-series to C when available and falls cleanly to the pure-Python
    body (the complete alternative + the parity oracle). Imported lazily to avoid
    a bootstrap cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    probe = getattr(nat, "has_native_eisenstein", None)
    return nat if (probe is not None and probe()) else None


def _bernoulli(k: int) -> Q:
    """The ``k``-th Bernoulli number ``B_k`` as an exact :class:`~srmech.amsc.q.Q`.

    Standard recurrence (the convention ``B_1 = −1/2``; only even ``k ≥ 0`` are
    used here, so the convention is immaterial): from
    ``Σ_{j=0}^{m} C(m+1, j) B_j = 0`` with ``B_0 = 1``,

        B_m = −(1 / (m+1)) · Σ_{j=0}^{m−1} C(m+1, j) B_j .

    Pure exact rational — integer binomials :func:`_binomial`, exact ``Q``
    accumulation; no float, no stdlib ``math``."""
    bern: List[Q] = [Q(0, 1)] * (k + 1)
    bern[0] = Q(1, 1)
    for m in range(1, k + 1):
        acc = Q(0, 1)
        for j in range(m):
            acc = acc + Q(_binomial(m + 1, j), 1) * bern[j]
        # B_m = −acc / C(m+1, m) = −acc / (m+1)
        bern[m] = Q(-1, m + 1) * acc
    return bern[k]


def _binomial(n: int, r: int) -> int:
    """The exact integer binomial coefficient ``C(n, r)`` by the multiplicative
    recurrence (no stdlib ``math.comb``, no float). ``0 ≤ r ≤ n``."""
    if r < 0 or r > n:
        return 0
    # symmetry: fewer multiplies
    rr = r if r + r <= n else n - r
    num = 1
    for i in range(rr):
        num = num * (n - i)
    den = 1
    for i in range(1, rr + 1):
        den = den * i
    return num // den


def _divisor_power_sum(e: int, n: int) -> int:
    """The exact-integer divisor power sum ``σ_e(n) = Σ_{d|n} d^e`` by
    divisor-pair trial division (each divisor ``d ≤ √n`` pairs with ``n/d``).
    All exact integer; no float, no stdlib ``math``."""
    total = 0
    d = 1
    while d * d <= n:
        if n % d == 0:
            total += d ** e
            cofactor = n // d
            if cofactor != d:
                total += cofactor ** e
        d += 1
    return total


class Eisenstein:
    """A numpy-free EXACT-RATIONAL normalized Eisenstein series

        E_k(τ) = 1 − (2k / B_k) · Σ_{n≥1} σ_{k−1}(n) qⁿ

    — an operand carrier on the WEIGHT axis. Immutable. Holds the even weight
    ``k ≥ 4``. The :attr:`weight` ``= Q(k)`` (exact); the q-series
    (:meth:`q_series`) is exact-:class:`~srmech.amsc.q.Q` (rational in general —
    e.g. ``E_12`` has ``c_1 = 65520/691``); :meth:`is_modular` is ``True`` for
    every even ``k ≥ 4`` (the constructor gate). See the module docstring for the
    keystones (esp. the cross-rung ``E_4³ − E_6² = 1728·η²⁴``) + the honest-OPENs
    (``k = 2`` quasimodular; level > 1)."""

    __slots__ = ("_k",)

    def __init__(self, k: int) -> None:
        if isinstance(k, bool) or not isinstance(k, int):
            raise TypeError(
                f"Eisenstein takes an even int weight k ≥ 4; got {type(k).__name__}")
        if k == 2:
            raise ValueError(
                "k = 2 is the QUASIMODULAR boundary: E_2 is NOT a modular form "
                "(M_2(SL₂(ℤ)) = {0}; E_2 picks up a non-holomorphic correction "
                "under τ → −1/τ). It is named, not built — the natural next-theory "
                "is the quasimodular ring ℂ[E_2, E_4, E_6]. An honest boundary, "
                "not a fabricated reduction.")
        if k < 4:
            raise ValueError(
                f"the Eisenstein weight k must be an even int ≥ 4 (k=2 is the "
                f"quasimodular boundary, rejected separately); got {k!r}")
        if k % 2 != 0:
            raise ValueError(
                f"the level-1 Eisenstein series E_k vanishes for ODD k (M_k = "
                f"{{0}}); k must be EVEN ≥ 4; got {k!r}")
        self._k = k

    # ── accessors ──────────────────────────────────────────────────────────────
    @property
    def k(self) -> int:
        """The (even, ``≥ 4``) integer weight ``k``."""
        return self._k

    @property
    def weight(self) -> Q:
        """The modular WEIGHT ``k`` — the ``(cτ+d)^k`` automorphy covariance grade
        (an EVEN INTEGER ``≥ 4`` for the level-1 holomorphic Eisenstein series →
        exact :class:`~srmech.amsc.q.Q`). THE WEIGHT AXIS."""
        return Q(self._k, 1)

    @property
    def leading_power(self) -> Q:
        """The leading q-power: the constant term of ``E_k`` is ``1`` (``q^0``), so
        ``E_k`` is HOLOMORPHIC AND NON-VANISHING at the cusp ``∞`` — it is NOT a
        cusp form (contrast ``Δ = η²⁴``, leading power ``q^1``). Exact
        :class:`~srmech.amsc.q.Q` ``Q(0, 1)``."""
        return Q(0, 1)

    @property
    def prefactor(self) -> Q:
        """The exact-rational normalization prefactor ``−2k / B_k`` (so
        ``c_n = prefactor·σ_{k−1}(n)``). Integer for ``k = 4, 6, 8, 10, 14`` (240,
        −504, 480, −264, −24); a genuine rational for ``k = 12`` (``65520/691``),
        ``k = 16`` (``16320/3617``), … — an exact :class:`~srmech.amsc.q.Q`."""
        return Q(-2 * self._k, 1) / _bernoulli(self._k)

    # ── the q-series (exact rational coefficients) ─────────────────────────────
    def q_series(self, n_terms: int) -> List[Q]:
        """The exact-:class:`~srmech.amsc.q.Q` coefficient list
        ``[c_0, c_1, …, c_{n_terms−1}]`` of

            E_k(τ) = 1 − (2k / B_k) · Σ_{n≥1} σ_{k−1}(n) qⁿ ,

        i.e. ``c_0 = Q(1, 1)`` and ``c_n = −(2k/B_k)·σ_{k−1}(n)`` for ``n ≥ 1``
        (exact rational — e.g. ``E_4`` is ``[1, 240, 2160, 6720, 17520]`` while
        ``E_12`` has ``c_1 = Q(65520, 691)``). DISPATCHES to the native
        ``srmech_eisenstein_qseries`` C peer when loaded (a 1:1 exact-rational
        mirror — the C ``(num, den)`` pairs EQUAL the Python coefficients, trusted
        only on a native hit); else the pure-Python :meth:`_q_series_py` body (the
        COMPLETE alternative + the parity oracle). No numpy / ``math`` / ``abs``."""
        if not isinstance(n_terms, int) or n_terms < 1:
            raise ValueError(f"n_terms must be a positive int; got {n_terms!r}")
        nat = _native()
        if nat is not None:
            try:
                got = nat.eisenstein_qseries_c(self._k, n_terms)
                if got is not None:
                    return [Q(num, den) for (num, den) in got]
            except (RuntimeError, OverflowError, ValueError):
                pass  # fall to the pure path
        return self._q_series_py(n_terms)

    def _q_series_py(self, n_terms: int) -> List[Q]:
        """The COMPLETE pure-Python ``q_series`` (the parity oracle for the C peer):
        the exact-:class:`~srmech.amsc.q.Q` coefficients of
        ``1 − (2k/B_k)·Σ σ_{k−1}(n) qⁿ`` to ``n_terms`` terms. The prefactor
        ``−2k/B_k`` is computed ONCE (exact-``Q`` Bernoulli :func:`_bernoulli`);
        each ``c_n`` is ``prefactor · σ_{k−1}(n)`` (exact-int
        :func:`_divisor_power_sum`). All exact rational; no float / numpy /
        ``math`` / ``abs``."""
        e = self._k - 1
        pref = Q(-2 * self._k, 1) / _bernoulli(self._k)
        coeffs: List[Q] = [Q(1, 1)]
        for n in range(1, n_terms):
            coeffs.append(pref * Q(_divisor_power_sum(e, n), 1))
        return coeffs

    # ── the modularity decision (anchors the honest boundary) ──────────────────
    def is_modular(self) -> bool:
        """``True`` — every even ``k ≥ 4`` level-1 Eisenstein series E_k IS a
        modular form on ``SL₂(ℤ)`` (it generates the ring ``ℂ[E_4, E_6]``).
        Trivially true given the constructor gate (which rejects ``k = 2`` —
        QUASIMODULAR, the honest boundary — and odd ``k`` / ``k < 4``); kept for
        carrier-idiom symmetry with :meth:`~srmech.amsc.eta_quotient.EtaQuotient.is_modular`
        and to ANCHOR the ``k = 2`` honest-OPEN at the constructor."""
        return True

    # ── equality / repr ────────────────────────────────────────────────────────
    def equals(self, other: "Eisenstein") -> bool:
        """``True`` iff ``other`` is an :class:`Eisenstein` of the SAME weight ``k``
        (the carrier-idiom value equality)."""
        return isinstance(other, Eisenstein) and self._k == other._k

    def __eq__(self, other) -> bool:
        if isinstance(other, Eisenstein):
            return self._k == other._k
        return NotImplemented

    def __ne__(self, other):
        r = self.__eq__(other)
        return r if r is NotImplemented else (not r)

    def __hash__(self) -> int:
        return hash(("Eisenstein", self._k))

    def __repr__(self) -> str:
        return f"Eisenstein(k={self._k}, weight={self.weight})"


def eisenstein(k: int) -> Eisenstein:
    """Construct an :class:`Eisenstein` series

        E_k(τ) = 1 − (2k / B_k) · Σ_{n≥1} σ_{k−1}(n) qⁿ

    — the public construction helper for the WEIGHT-axis Eisenstein carrier (the
    SECOND weight rung after the rc82 eta-quotient). ``k`` is an EVEN int ``≥ 4``.
    The keystones:

    - ``eisenstein(4).q_series(5)`` → ``[1, 240, 2160, 6720, 17520]`` (240·σ₃),
      weight ``Q(4)``;
    - ``eisenstein(6).q_series(5)`` → ``[1, −504, −16632, −122976, −532728]``
      (−504·σ₅), weight ``Q(6)``;
    - ``eisenstein(12).q_series(2)[1]`` → ``Q(65520, 691)`` (the genuine rational
      coefficient — the whole reason coefficients are ``Q`` not ``int``);
    - the CROSS-RUNG: ``E_4³ − E_6² = 1728·Δ = 1728·η²⁴`` (validated against the
      published rc82 :class:`~srmech.amsc.eta_quotient.EtaQuotient` ``({1: 24})``).

    ``k = 2`` is REJECTED as the QUASIMODULAR boundary (``E_2`` is not modular);
    odd ``k`` and ``k < 4`` are rejected. Exact-rational q-series; exact-``Q``
    weight / prefactor; no float, no ``abs()``, no numpy / ``math``."""
    return Eisenstein(k)
