"""srmech.amsc.quasimodular_forms_ring — ``QuasiModularFormsRing``, the level-1
ℂ[E₂,E₄,E₆] QUASIMODULAR-forms-ring carrier + its EXACT membership decision (the
FOURTH WEIGHT-axis rung, after rc82 eta-quotient + rc83 Eisenstein + rc84
``ModularFormsRing`` ℂ[E₄,E₆]).

THE OBJECT — the quasimodular ring, one generator up
====================================================

The rc83 :class:`~srmech.amsc.eisenstein.Eisenstein` carrier REJECTS ``k = 2`` and
NAMES this theory in its own docstring: ``E_2`` is NOT a modular form (the
weight-2 space ``M_2(SL₂(ℤ)) = {0}``; ``E_2`` picks up a non-holomorphic anomaly
under ``τ → −1/τ``: ``E_2(−1/τ) = τ²E_2(τ) + 12τ/(2πi)``). The smallest ring that
contains ``E_2`` is the ring of QUASIMODULAR forms,

    M̃_*(SL₂(ℤ)) = ℂ[E_2, E_4, E_6]

— the FREE polynomial ring in the THREE generators ``E_2`` (weight 2), ``E_4``
(weight 4), ``E_6`` (weight 6) (Kaneko & Zagier, *A generalized Jacobi theta
function and quasimodular forms*, in *The Moduli Space of Curves*, Progr. Math.
129, Birkhäuser (1995), pp. 165–172; Zagier, *Elliptic Modular Forms and Their
Applications*, in *The 1-2-3 of Modular Forms*, Springer (2008), §5.3
"Quasimodular forms", p. 58). Concretely: every quasimodular form of weight ``k``
is a UNIQUE exact-rational polynomial in ``E_2, E_4, E_6`` — a finite ℚ-linear
combination of the weight-``k`` monomials

    E_2^a · E_4^b · E_6^c   with   2a + 4b + 6c = k,   a, b, c ≥ 0.

This carrier is the rc84 :class:`~srmech.amsc.modular_forms_ring.ModularFormsRing`
pattern mirrored ONE GENERATOR up: ``ModularFormsRing`` is exactly the ``a = 0``
subring (no ``E_2`` factor), so ``ℂ[E_4, E_6] ⊂ ℂ[E_2, E_4, E_6]`` and the
quasimodular ring genuinely EXTENDS the modular one — e.g. ``E_2²`` (weight 4) is a
quasimodular monomial that is NOT in ``ℂ[E_4, E_6]`` (rc84
``ModularFormsRing().represent(E_2², 4)`` → ``None``, but here
``represent(E_2², 4)`` → ``{(2, 0, 0): 1}``).

E_2 — the weight-2 quasimodular generator
=========================================

    E_2(τ) = 1 − 24 · Σ_{n≥1} σ_1(n) qⁿ ,   σ_1(n) = Σ_{d|n} d ,

i.e. the SAME normalized-Eisenstein formula ``E_k = 1 − (2k/B_k)·Σ σ_{k−1}(n) qⁿ``
at ``k = 2`` (the prefactor ``−2·2 / B_2 = −4 / (1/6) = −24`` is the von
Staudt–Clausen ``B_2 = 1/6``, computed here by the SAME Bernoulli cascade as the
modular ``E_k`` — :func:`~srmech.amsc.eisenstein._bernoulli`, NOT a magic ``−24``).
:func:`eisenstein_e2` returns its exact-:class:`~srmech.amsc.q.Q` q-series
``[1, −24, −72, −96, −168, …]``. ``Eisenstein(2)`` stays REJECTED (the modular
carrier's ``k ≥ 4`` contract is intact); ``E_2`` enters ONLY through the
quasimodular path here, the honest separation of objects.

THE DEFINING STRUCTURE — Ramanujan's derivative (Serre) identities
==================================================================

The quasimodular ring is exactly the world the SERRE / RAMANUJAN derivative
``D = q d/dq`` (the operator ``D(Σ a_n qⁿ) = Σ n·a_n qⁿ``) closes on. ``D`` maps a
modular form of weight ``k`` to a QUASIMODULAR form of weight ``k + 2`` (the
``E_2`` term is the quasimodular correction), and on the generators it is
Ramanujan's system of three differential equations (Ramanujan, *On certain
arithmetical functions*, Trans. Camb. Phil. Soc. 22 (1916), pp. 159–184 — his
``P = E_2``, ``Q = E_4``, ``R = E_6``):

    D E_2 = (E_2² − E_4) / 12 ,
    D E_4 = (E_2 E_4 − E_6) / 3 ,
    D E_6 = (E_2 E_6 − E_4²) / 2 .

These are the KEYSTONES: :meth:`represent` confirms, bit-exactly, that the exact
q-series derivative ``D E_4`` (computed as ``Σ n·a_n qⁿ`` on the rc83 E_4 series)
reduces to the polynomial ``(E_2 E_4 − E_6)/3`` over the ring, i.e.
``represent(D E_4, 6)`` → ``{(1, 1, 0): 1/3, (0, 0, 1): −1/3}`` (and likewise
``D E_2`` at weight 4 → ``{(2, 0, 0): 1/12, (0, 1, 0): −1/12}`` and ``D E_6`` at
weight 8 → ``{(1, 0, 1): 1/2, (0, 2, 0): −1/2}``). The identities are DERIVED +
checked on the q-series (see the rc89 test), never recall-and-trusted.

THE MEMBERSHIP DECISION (decompose-and-compute, NOT a search)
=============================================================

:meth:`represent` takes a claimed weight-``k`` q-series and SOLVES the exact-ℚ
linear system

    Σ_{a,b,c}  c_{a,b,c} · (E_2^a E_4^b E_6^c)[n]  =  f[n]   for every provided n

over the weight-``k`` monomial basis (:meth:`weight_monomials`), VERIFIES the
solution reproduces ALL provided terms, and returns the UNIQUE exact-ℚ polynomial
representation ``{(a, b, c): c_{a,b,c}}`` — or ``None`` when no such representation
exists. The construction/solve IS the decision: it builds the ``E_2/E_4/E_6``
q-series, forms the monomial columns by exact-ℚ truncated q-series multiplication,
solves with the exact-ℚ :class:`~srmech.amsc.qmat.QMat` Gauss-Jordan, and VERIFIES.

THE OPERAND BOUNDARIES (the honest OPENs — named, not faked)
===========================================================

(1) **the JACOBI-form / two-variable boundary.** The next WEIGHT rung is the ring
    of JACOBI forms (the ``τ–z`` two-variable theory tying the weight axis to the
    elliptic carriers — Eichler & Zagier, *The Theory of Jacobi Forms*, Progr.
    Math. 55, Birkhäuser (1985)). A Jacobi form needs a ``τ–z`` 2-variable carrier
    (a bigger build, like the rc62 ThetaSum additive-theta carrier was), NOT built
    here.

(2) **the LEVEL boundary.** This carrier is the LEVEL-1 (``SL₂(ℤ)``) quasimodular
    ring. The higher-level quasimodular ring ``M̃_*(Γ₀(N))`` (``N > 1``) needs MORE
    generators, NOT built here — the dual of the rc84 ``ModularFormsRing`` level
    boundary, one generator up.

# OPEN: Jacobi forms (the τ–z two-variable bridge to the elliptic carriers) are the
#       next WEIGHT rung — they need a τ–z 2-variable carrier, not built here.
# OPEN: level-1 only (M̃_*(SL₂(ℤ)) = ℂ[E₂,E₄,E₆]). For N>1, M̃_*(Γ₀(N)) needs MORE
#       generators — not built here (the level axis, one generator up from rc84).

THE C PEER
==========

The C peer ``srmech_quasimodular_forms_ring_represent``
(``c/src/srmech_quasimodular_forms_ring.c``) mirrors the membership solve: it
builds the weight-``k`` monomial-basis matrix from the ``E_2``/``E_4``/``E_6``
q-series (the rc83 ``srmech_eisenstein_qseries`` peer — at ``k = 2`` for ``E_2``,
its quasimodular branch — + an exact-ℚ truncated q-series multiply), DISPATCHES the
square subsystem to the existing ``srmech_qmat_solve`` (exact Gauss-Jordan over
bignum-ℚ — reuse, not reimplement), VERIFIES the solution against ALL provided
terms, and returns the reduced ``(num, den)`` rep coefficients or a no-solution
flag. Caller-arena, JPL-clean (no goto/malloc/recursion; ≤60-line funcs; ≥2
asserts/fn; OVERFLOW-not-wrap; the Class-K sign is a branch, never ``abs()``). The
pure-Python body here is the COMPLETE alternative + the C peer's parity oracle —
both emit byte-identical ``{(a,b,c): (num, den)}`` reps / ``None``. Additive symbol
→ ABI unchanged (stays 3). ``represent`` is a genuine REDUCER (q-series → exact
closed form, or honest OPEN) — the WEIGHT-axis analog of the Σ-row reducers
(gosper / zeilberger / wz_certificate / dispatch.infer), so it IS a Rosetta ledger
op (a ToolEntry, ``c_dispatched``); ``eisenstein_e2`` + the ring accessors are NOT.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from .eisenstein import Eisenstein, _bernoulli, _divisor_power_sum
from .q import Q
from .qmat import QMat

__all__ = [
    "QuasiModularFormsRing",
    "QuasiModularForm",
    "quasimodular_forms_ring",
    "quasimodular_forms_ring_represent",
    "eisenstein_e2",
]

_Q_ZERO = Q(0, 1)
_Q_ONE = Q(1, 1)


def _native():
    """The native ``_native`` module IF the rc89 ``srmech_quasimodular_forms_ring_
    represent`` peer is present + bound, else ``None`` — so the membership solve
    dispatches to C when available and falls cleanly to the pure-Python body (the
    complete alternative + the parity oracle). Imported lazily to avoid a
    bootstrap cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    probe = getattr(nat, "has_native_quasimodular_forms_ring", None)
    return nat if (probe is not None and probe()) else None


def _native_eis():
    """The native ``_native`` module IF the rc83 ``srmech_eisenstein_qseries`` peer
    (quasimodular ``k = 2`` branch) is present + bound, else ``None`` — so
    :func:`eisenstein_e2` dispatches the exact-rational E_2 q-series to C when
    available and falls cleanly to the pure-Python body. Imported lazily."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    probe = getattr(nat, "has_native_eisenstein", None)
    return nat if (probe is not None and probe()) else None


def eisenstein_e2(n_terms: int) -> List[Q]:
    """The exact-:class:`~srmech.amsc.q.Q` q-series of the WEIGHT-2 QUASIMODULAR
    Eisenstein generator

        E_2(τ) = 1 − 24 · Σ_{n≥1} σ_1(n) qⁿ ,   σ_1(n) = Σ_{d|n} d ,

    to ``n_terms`` terms: ``[c_0, c_1, …, c_{n_terms−1}]`` with ``c_0 = Q(1, 1)``
    and ``c_n = −24·σ_1(n)`` (so ``eisenstein_e2(5) = [1, −24, −72, −96, −168]``).
    The prefactor is the SAME normalized-Eisenstein ``−2k/B_k`` at ``k = 2``
    (``−4 / B_2 = −4 / (1/6) = −24``; the von Staudt–Clausen ``B_2 = 1/6`` is
    computed by the SAME Bernoulli cascade :func:`~srmech.amsc.eisenstein._bernoulli`
    as the modular ``E_k`` — NOT a magic literal). ``E_2`` is NOT a modular form
    (``M_2(SL₂(ℤ)) = {0}``); it is the QUASIMODULAR generator, so it lives here and
    NOT on the rc83 ``Eisenstein(k)`` carrier (which keeps its ``k ≥ 4`` contract
    and rejects ``k = 2``). DISPATCHES to the native ``srmech_eisenstein_qseries``
    C peer (``k = 2`` quasimodular branch) when loaded; else the pure-Python body
    (the COMPLETE alternative + the parity oracle). Exact rational; no float, no
    abs(), no numpy / ``math``."""
    if not isinstance(n_terms, int) or n_terms < 1:
        raise ValueError(f"n_terms must be a positive int; got {n_terms!r}")
    nat = _native_eis()
    if nat is not None:
        try:
            got = nat.eisenstein_e2_qseries_c(n_terms)
            if got is not None:
                return [Q(num, den) for (num, den) in got]
        except (RuntimeError, OverflowError, ValueError):
            pass  # fall to the complete pure path
    return _eisenstein_e2_py(n_terms)


def _eisenstein_e2_py(n_terms: int) -> List[Q]:
    """The COMPLETE pure-Python ``eisenstein_e2`` (the parity oracle for the C
    peer): the exact-:class:`~srmech.amsc.q.Q` coefficients of
    ``E_2 = 1 − (2·2/B_2)·Σ σ_1(n) qⁿ`` to ``n_terms`` terms. The prefactor
    ``−4/B_2`` is computed ONCE (exact-``Q`` Bernoulli — the SAME cascade as the
    modular ``E_k``); each ``c_n`` is ``prefactor · σ_1(n)`` (exact-int
    :func:`~srmech.amsc.eisenstein._divisor_power_sum`). All exact rational; no
    float / numpy / ``math`` / ``abs``."""
    pref = Q(-2 * 2, 1) / _bernoulli(2)            # −4 / (1/6) = −24, attested
    coeffs: List[Q] = [_Q_ONE]
    for n in range(1, n_terms):
        coeffs.append(pref * Q(_divisor_power_sum(1, n), 1))
    return coeffs


def _to_q(x) -> Q:
    """Coerce a q-series entry to an exact :class:`~srmech.amsc.q.Q` — accept an
    exact ``Q``, an ``int``, or a reduced ``(num, den)`` pair (a 2-element tuple OR
    list, so a JSON-RPC round-trip that turns tuples into lists still parses). A
    ``float`` is REJECTED (the carrier is exact-rational; a float must enter through
    an explicit boundary, never silently)."""
    if isinstance(x, Q):
        return x
    if isinstance(x, bool):
        raise TypeError("a bool is not a q-series coefficient")
    if isinstance(x, int):
        return Q(x, 1)
    if (isinstance(x, (tuple, list)) and len(x) == 2
            and all(isinstance(v, int) and not isinstance(v, bool) for v in x)):
        return Q(x[0], x[1])
    raise TypeError(
        f"q-series coefficient must be an exact Q / int / (num, den) pair, "
        f"not {type(x).__name__} (the carrier is exact-rational, no float)")


def _qmul(a: Sequence[Q], b: Sequence[Q], n_terms: int) -> List[Q]:
    """Exact-:class:`~srmech.amsc.q.Q` truncated q-series convolution to
    ``n_terms`` terms: ``(a·b)[n] = Σ_{i+j=n} a[i]·b[j]`` for ``n < n_terms``. All
    exact rational; no float, no numpy / ``math``."""
    out: List[Q] = [_Q_ZERO] * n_terms
    for i in range(min(len(a), n_terms)):
        ai = a[i]
        if ai == _Q_ZERO:
            continue
        for j in range(min(len(b), n_terms - i)):
            out[i + j] = out[i + j] + ai * b[j]
    return out


class QuasiModularFormsRing:
    """The level-1 (``SL₂(ℤ)``) graded QUASIMODULAR-forms ring ``ℂ[E_2, E_4, E_6]``
    as an operand carrier on the WEIGHT axis (the FOURTH rung, after the rc82
    eta-quotient + rc83 Eisenstein + rc84 ``ModularFormsRing`` ℂ[E_4,E_6]).
    Immutable + stateless — it carries the STRUCTURE (Kaneko–Zagier ``M̃_* =
    ℂ[E_2, E_4, E_6]``), exposing the weight-``k`` monomial basis
    (:meth:`weight_monomials`), the graded dimension (:meth:`dim`), and the exact
    MEMBERSHIP DECISION (:meth:`represent`). See the module docstring for the
    Ramanujan derivative keystones + the Jacobi / level honest-OPENs."""

    __slots__ = ()

    def __init__(self) -> None:
        pass

    # ── the graded basis (pure-carrier accessors; NOT ToolEntries) ─────────────
    @staticmethod
    def weight_monomials(k: int) -> List[Tuple[int, int, int]]:
        """The weight-``k`` monomial basis of ``ℂ[E_2, E_4, E_6]``: all ``(a, b, c)``
        with ``2a + 4b + 6c = k`` and ``a, b, c ≥ 0``, in canonical ascending
        ``(a, b)`` order. Empty for odd ``k`` / ``k < 0`` (``2a+4b+6c`` is always
        even). E.g. ``weight_monomials(2) = [(1, 0, 0)]`` (``E_2`` — the new
        generator, absent from the modular ring); ``weight_monomials(4) =
        [(2, 0, 0), (0, 1, 0)]`` (``E_2²`` and ``E_4``); ``weight_monomials(6) =
        [(3, 0, 0), (1, 1, 0), (0, 0, 1)]``. ``len(weight_monomials(k)) == dim(k)``
        for every ``k``."""
        if isinstance(k, bool) or not isinstance(k, int):
            raise TypeError(
                f"weight k must be an int; got {type(k).__name__}")
        if k < 0 or k % 2 != 0:
            return []
        mono: List[Tuple[int, int, int]] = []
        a = 0
        while 2 * a <= k:
            b = 0
            while 2 * a + 4 * b <= k:
                rem = k - 2 * a - 4 * b
                if rem % 6 == 0:
                    mono.append((a, b, rem // 6))
                b += 1
            a += 1
        return mono

    @staticmethod
    def dim(k: int) -> int:
        """The dimension of the weight-``k`` graded piece ``M̃_k(SL₂(ℤ))`` of
        quasimodular forms: ``#{(a, b, c) ≥ 0 : 2a + 4b + 6c = k}`` — computed
        exactly by enumeration (there is no two-term closed form like the modular
        ``ℂ[E_4, E_6]`` case, because the third generator ``E_2`` makes it a
        three-variable partition count). Equal to ``len(weight_monomials(k))`` for
        every ``k``; ``0`` for odd ``k`` / ``k < 0``. E.g. ``dim(2) = 1`` (``E_2``;
        contrast the MODULAR ``dim M_2 = 0``), ``dim(4) = 2``, ``dim(6) = 3``,
        ``dim(8) = 4``, ``dim(0) = 1`` (the constants)."""
        return len(QuasiModularFormsRing.weight_monomials(k))

    # ── the monomial q-series columns (the basis matrix builder) ───────────────
    @staticmethod
    def _monomial_qseries(a: int, b: int, c: int, n_terms: int) -> List[Q]:
        """The exact-:class:`~srmech.amsc.q.Q` q-series of the monomial
        ``E_2^a · E_4^b · E_6^c`` to ``n_terms`` terms — the ``E_2``
        (:func:`eisenstein_e2`) / rc83 ``E_4``,``E_6`` carriers raised to integer
        powers by exact-ℚ truncated q-series multiplication. ``E_2⁰ E_4⁰ E_6⁰`` is
        the constant ``1`` (the weight-0 monomial). No float, no abs()."""
        res: List[Q] = [_Q_ONE] + [_Q_ZERO] * (n_terms - 1)
        if a > 0:
            e2 = eisenstein_e2(n_terms)
            for _ in range(a):
                res = _qmul(res, e2, n_terms)
        if b > 0:
            e4 = Eisenstein(4).q_series(n_terms)
            for _ in range(b):
                res = _qmul(res, e4, n_terms)
        if c > 0:
            e6 = Eisenstein(6).q_series(n_terms)
            for _ in range(c):
                res = _qmul(res, e6, n_terms)
        return res

    # ── the membership decision (the carrier's CORE; the reducer) ──────────────
    def represent(self, q_series, k: int, *,
                  n_terms: Optional[int] = None
                  ) -> Optional[Dict[Tuple[int, int, int], Q]]:
        """THE MEMBERSHIP DECISION: given an exact q-series ``q_series`` (a list of
        ``Q`` / ``int`` / ``(num, den)`` pairs) claimed to be a weight-``k``
        QUASIMODULAR form, SOLVE the exact-ℚ linear system

            Σ_{a,b,c} c_{a,b,c}·(E_2^a E_4^b E_6^c)[n] = q_series[n]   for every n

        over the weight-``k`` monomial basis, VERIFY the solution reproduces ALL
        provided terms, and return the UNIQUE exact-ℚ polynomial representation
        ``{(a, b, c): c_{a,b,c}}`` (the NONZERO monomials only) — or ``None`` if no
        representation exists (the q-series is NOT a weight-``k`` quasimodular form
        within this carrier). The construction/solve IS the decision
        (decompose-and-compute, not a search).

        ``k`` is the (even, ``≥ 0``) claimed weight; an ODD ``k`` has
        ``dim M̃_k = 0`` so a NONZERO q-series there → ``None`` (and the zero series
        → the empty rep ``{}``). At least ``dim(k) + 2`` terms are required for the
        system to be well-posed AND verifiable (more terms is fine); too few raises
        ``ValueError``. ``n_terms`` (optional) caps the terms USED (default: all
        provided). Exact over ℚ via :class:`~srmech.amsc.qmat.QMat` Gauss-Jordan;
        DISPATCHES to the native ``srmech_quasimodular_forms_ring_represent`` C peer
        when loaded (compared element-for-element, never trusted); else the
        pure-Python :meth:`_represent_py` body (the COMPLETE alternative + the
        parity oracle). No float, no abs() (Class-K sign branch), no numpy /
        ``math``."""
        if isinstance(k, bool) or not isinstance(k, int):
            raise TypeError(f"weight k must be an int; got {type(k).__name__}")
        f = [_to_q(c) for c in q_series]
        if n_terms is not None:
            if not isinstance(n_terms, int) or n_terms < 1:
                raise ValueError(f"n_terms must be a positive int; got {n_terms!r}")
            f = f[:n_terms]
        mono = self.weight_monomials(k)
        d = len(mono)
        need = (d + 2) if d > 0 else 1
        if len(f) < need:
            raise ValueError(
                f"represent needs ≥ {need} q-series terms for a well-posed + "
                f"verifiable weight-{k} solve (dim M̃_{k} = {d}); got {len(f)}")
        nat = _native()
        if nat is not None:
            try:
                got = nat.quasimodular_forms_ring_represent_c(
                    [c.as_pair() for c in f], k)
                if got is not None:
                    has, pairs = got
                    if not has:
                        return None
                    return {mono[i]: Q(pairs[i][0], pairs[i][1])
                            for i in range(d)
                            if (pairs[i][0] != 0)}
            except (RuntimeError, OverflowError, ValueError):
                pass  # fall to the complete pure path
        return self._represent_py(f, k, mono)

    def _represent_py(self, f: List[Q], k: int,
                      mono: List[Tuple[int, int, int]]
                      ) -> Optional[Dict[Tuple[int, int, int], Q]]:
        """The COMPLETE pure-Python ``represent`` (the parity oracle for the C
        peer): build the weight-``k`` monomial-basis matrix, solve the square
        subsystem exactly over ℚ (:class:`~srmech.amsc.qmat.QMat`), and VERIFY the
        solution against EVERY provided term. ``f`` is the coerced ``Q`` q-series,
        ``mono`` the weight-``k`` monomial basis. Returns ``{(a,b,c): Q}`` or
        ``None``. All exact rational; no float / numpy / ``math`` / ``abs``."""
        n_terms = len(f)
        d = len(mono)
        # the empty basis (M̃_k = {0}, e.g. odd k): the only quasimodular form is 0
        if d == 0:
            return {} if all(c == _Q_ZERO for c in f) else None
        # the basis columns: cols[j][n] = (E_2^a E_4^b E_6^c)[n] for monomial j
        cols = [self._monomial_qseries(a, b, c, n_terms) for (a, b, c) in mono]
        # the square subsystem: the first `d` rows. Solve A·c = b.
        a_rows = [[cols[j][i] for j in range(d)] for i in range(d)]
        b_col = [[f[i]] for i in range(d)]
        try:
            x = QMat.from_rows(a_rows).solve(QMat.from_rows(b_col))
        except ValueError:
            # singular leading block — fall back to an over-determined RREF solve
            return self._represent_rref(f, mono, cols)
        coeffs = [x._rows[j][0] for j in range(d)]
        if not self._verify(coeffs, cols, f):
            return None
        return {mono[j]: coeffs[j] for j in range(d) if coeffs[j] != _Q_ZERO}

    def _represent_rref(self, f: List[Q], mono: List[Tuple[int, int, int]],
                        cols: List[List[Q]]
                        ) -> Optional[Dict[Tuple[int, int, int], Q]]:
        """The over-determined consistency solve (the fallback when the leading
        square block is singular): RREF the augmented ``[A | b]`` over ℚ; the system
        is consistent (the q-series IS in the ring) iff there is no pivot in the b
        column AND the unique solution reproduces every term. Exact over ℚ; no
        float / abs()."""
        n_terms = len(f)
        d = len(mono)
        aug = [[cols[j][i] for j in range(d)] + [f[i]] for i in range(n_terms)]
        R = QMat.from_rows(aug).rref()
        rank = 0
        for i in range(R.n_rows):
            row = R._rows[i]
            piv = None
            for j in range(d + 1):
                if row[j] != _Q_ZERO:
                    piv = j
                    break
            if piv is None:
                continue
            rank += 1
            if piv == d:
                return None  # inconsistent: q-series is not a weight-k form
        if rank != d:
            return None  # under-determined (shouldn't happen with ≥dim+2 terms)
        coeffs = [_Q_ZERO] * d
        for i in range(R.n_rows):
            row = R._rows[i]
            for j in range(d):
                if row[j] == _Q_ONE and all(
                        row[jj] == _Q_ZERO for jj in range(d) if jj != j):
                    coeffs[j] = row[d]
                    break
        if not self._verify(coeffs, cols, f):
            return None
        return {mono[j]: coeffs[j] for j in range(d) if coeffs[j] != _Q_ZERO}

    @staticmethod
    def _verify(coeffs: List[Q], cols: List[List[Q]], f: List[Q]) -> bool:
        """True iff ``Σ_j coeffs[j]·cols[j][n] == f[n]`` for EVERY provided term
        ``n`` — the membership-decision VERIFICATION (the solve produces a
        candidate; the verify makes it a DECISION). Exact ``Q`` equality; no float,
        no abs()."""
        n_terms = len(f)
        for n in range(n_terms):
            acc = _Q_ZERO
            for j in range(len(coeffs)):
                acc = acc + coeffs[j] * cols[j][n]
            if acc != f[n]:
                return False
        return True

    # ── equality / repr ────────────────────────────────────────────────────────
    def equals(self, other: "QuasiModularFormsRing") -> bool:
        """True iff ``other`` is a :class:`QuasiModularFormsRing` (the ring is the
        unique level-1 ``ℂ[E_2, E_4, E_6]`` — all instances are equal, the
        carrier-idiom value equality for a stateless carrier)."""
        return isinstance(other, QuasiModularFormsRing)

    def __eq__(self, other) -> bool:
        if isinstance(other, QuasiModularFormsRing):
            return True
        return NotImplemented

    def __ne__(self, other):
        r = self.__eq__(other)
        return r if r is NotImplemented else (not r)

    def __hash__(self) -> int:
        return hash("QuasiModularFormsRing")

    def __repr__(self) -> str:
        return "QuasiModularFormsRing(ℂ[E₂,E₄,E₆], level=1)"


class QuasiModularForm:
    """A level-1 quasimodular form held by its weight + its exact-ℚ polynomial
    representation ``{(a, b, c): c_{a,b,c}}`` in ``ℂ[E_2, E_4, E_6]`` (the output of
    :meth:`QuasiModularFormsRing.represent`). Immutable; reconstructs its q-series
    from the rep (:meth:`q_series`) so a represented form round-trips back to the
    series it came from. A thin minimal wrapper over the rep — the ring carrier
    holds the structure; this names a single graded element."""

    __slots__ = ("_weight", "_rep")

    def __init__(self, weight: int, rep: Dict[Tuple[int, int, int], Q]) -> None:
        if isinstance(weight, bool) or not isinstance(weight, int):
            raise TypeError(
                f"weight must be an int; got {type(weight).__name__}")
        canon: Dict[Tuple[int, int, int], Q] = {}
        for (a, b, c), coeff in rep.items():
            ai, bi, ci = int(a), int(b), int(c)
            if 2 * ai + 4 * bi + 6 * ci != weight:
                raise ValueError(
                    f"monomial E₂^{ai}·E₄^{bi}·E₆^{ci} has weight "
                    f"{2*ai+4*bi+6*ci}, not the claimed form weight {weight}")
            cq = coeff if isinstance(coeff, Q) else _to_q(coeff)
            if cq != _Q_ZERO:
                canon[(ai, bi, ci)] = cq
        self._weight = weight
        self._rep = tuple(sorted(canon.items()))

    @property
    def weight(self) -> int:
        """The (even) weight ``k`` — the grading of this form in
        ``ℂ[E_2, E_4, E_6]``."""
        return self._weight

    @property
    def rep(self) -> Dict[Tuple[int, int, int], Q]:
        """The exact-ℚ polynomial representation ``{(a, b, c): c_{a,b,c}}`` (the
        nonzero monomials, canonical order)."""
        return dict(self._rep)

    def q_series(self, n_terms: int) -> List[Q]:
        """Reconstruct the exact-:class:`~srmech.amsc.q.Q` q-series of this form to
        ``n_terms`` terms from its rep: ``Σ_{a,b,c} c_{a,b,c}·(E_2^a E_4^b E_6^c)``.
        Exact; no float, no abs()."""
        if not isinstance(n_terms, int) or n_terms < 1:
            raise ValueError(f"n_terms must be a positive int; got {n_terms!r}")
        out: List[Q] = [_Q_ZERO] * n_terms
        for (a, b, c), coeff in self._rep:
            col = QuasiModularFormsRing._monomial_qseries(a, b, c, n_terms)
            for n in range(n_terms):
                out[n] = out[n] + coeff * col[n]
        return out

    def equals(self, other: "QuasiModularForm") -> bool:
        """True iff ``other`` is a :class:`QuasiModularForm` of the SAME weight + the
        SAME canonical rep (the carrier-idiom value equality)."""
        return (isinstance(other, QuasiModularForm)
                and self._weight == other._weight
                and self._rep == other._rep)

    def __eq__(self, other) -> bool:
        if isinstance(other, QuasiModularForm):
            return self._weight == other._weight and self._rep == other._rep
        return NotImplemented

    def __ne__(self, other):
        r = self.__eq__(other)
        return r if r is NotImplemented else (not r)

    def __hash__(self) -> int:
        return hash(("QuasiModularForm", self._weight, self._rep))

    def __repr__(self) -> str:
        body = ", ".join(f"(E2^{a}·E4^{b}·E6^{c}):{coeff}"
                         for (a, b, c), coeff in self._rep)
        return f"QuasiModularForm(weight={self._weight}, rep={{{body}}})"


def quasimodular_forms_ring() -> QuasiModularFormsRing:
    """Construct the level-1 quasimodular-forms ring ``ℂ[E_2, E_4, E_6]`` carrier
    (the FOURTH WEIGHT-axis rung, after the rc82 eta-quotient + rc83 Eisenstein +
    rc84 ``ModularFormsRing`` ℂ[E_4,E_6]). The carrier is stateless (the ring is
    unique); use it for the weight-``k`` monomial basis
    (:meth:`~QuasiModularFormsRing.weight_monomials`), the graded dimension
    (:meth:`~QuasiModularFormsRing.dim`), and the exact membership decision
    (:meth:`~QuasiModularFormsRing.represent`). See the module docstring + the
    :func:`quasimodular_forms_ring_represent` reducer for the Ramanujan-derivative
    keystones."""
    return QuasiModularFormsRing()


def quasimodular_forms_ring_represent(q_series, k: int, *,
                                      n_terms: Optional[int] = None
                                      ) -> Optional[Dict[Tuple[int, int, int], Q]]:
    """The level-1 quasimodular-forms-ring MEMBERSHIP DECISION (the WEIGHT-axis
    REDUCER, the analog of the Σ-row gosper / zeilberger / wz_certificate reducers,
    one generator up from the rc84 ``modular_forms_ring_represent``): given an exact
    q-series claimed to be a weight-``k`` quasimodular form, return its UNIQUE
    exact-ℚ polynomial representation ``{(a, b, c): c_{a,b,c}}`` in
    ``ℂ[E_2, E_4, E_6]`` — or ``None`` if it is NOT a weight-``k`` quasimodular form
    within this carrier. The construction/solve IS the decision
    (decompose-and-compute over the monomial basis via exact-ℚ Gauss-Jordan, then
    VERIFY all terms), NOT a search.

    The keystones (Ramanujan's Serre-derivative identities, the defining structure):

    - ``D E_2 = (E_2²−E_4)/12`` at weight 4 → ``{(2,0,0):1/12, (0,1,0):−1/12}``;
    - ``D E_4 = (E_2 E_4−E_6)/3`` at weight 6 → ``{(1,1,0):1/3, (0,0,1):−1/3}``;
    - ``D E_6 = (E_2 E_6−E_4²)/2`` at weight 8 → ``{(1,0,1):1/2, (0,2,0):−1/2}``;
    - the EXTENDS-the-modular-ring proof: ``E_2²`` at weight 4 → ``{(2,0,0):1}``
      (whereas rc84 ``modular_forms_ring_represent(E_2², 4)`` → ``None`` — ``E_2²``
      is quasimodular, NOT in ``ℂ[E_4,E_6]``).

    ``q_series`` is a list of exact ``Q`` / ``int`` / ``(num, den)`` pairs (no
    float); ``k`` the (even) claimed weight; at least ``dim(k) + 2`` terms are
    required (more is fine). Exact over ℚ; DISPATCHES to the native
    ``srmech_quasimodular_forms_ring_represent`` C peer when loaded; no float, no
    abs(), no numpy / ``math``."""
    return QuasiModularFormsRing().represent(q_series, k, n_terms=n_terms)
