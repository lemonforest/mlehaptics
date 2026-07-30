"""Spike #40 EXACT PORT — shared exact-arithmetic kit (2026-07-30).

Port target: the six 2026-05-17 ``spike_40_*.py`` scripts, which are
float-throughout and import ``numpy`` / ``scipy``. Neither exists in the
srmech 0.9.0rcN tree any more. This module is the substrate-native
replacement layer.

STRUCTURAL DIFFERENCE FROM THE 2026-05-17 ORIGINALS
---------------------------------------------------
The originals compute in IEEE-754 double from the first line to the last.
These ports carry ``srmech.amsc.q.Q`` (exact rational) — and, where the
generating form is an algebraic irrational, ``srmech.amsc.qalg.Qalg`` —
all the way through, and lift to ``float`` ONLY at the readout that is
compared against the committed 2026-05-17 NDJSON oracle. Every deliberate
early lift is registered in :data:`FLOAT_LIFTS` and printed by the ports.

DISCIPLINE OBSERVED
-------------------
* no ``numpy``, no ``scipy``, no ``fractions`` — carriers are ``Q`` / ``Qalg``
* no Python ``abs()`` anywhere — sign is Class-K ``pin_slot_at_zero`` and
  Class-K ``magnitude`` (``srmech.amsc.cascade``); orientation re-application
  is Class-C ``reorient``
* every hand-rolled operation is registered in :data:`PRIMITIVE_GAPS` with
  its A–N class letter, and the gap table is emitted into every port's
  NDJSON output so it is visible in the result, not buried here

WHAT SRMECH ALREADY SHIPS AND IS USED AS-IS (no hand-roll)
----------------------------------------------------------
``srmech.amsc.rational.log`` / ``.exp`` / ``.sqrt`` / ``.sin`` / ``.cos``
    Class-N exact-rational transcendental cascade. All four accept a ``Q``
    and return an EXACT ``Q`` (the Q61 fixed-point model, denominator
    ~2**59). Measured against the CPython ``math`` peers on this tree they
    agree to the last bit, so they are strictly better than the float
    pipeline they replace, not a compromise.
``srmech.amsc.rational.best_rational``
    Class-N denominator cap (Stern-Brocot convergent) — used to keep the
    Levenberg-Marquardt parameter vector bounded without leaving ℚ.
``srmech.amsc.rational.pi_cascade_digits``
    Class-N π, used for the DFT twiddles and the McMahon Bessel-zero start.
``srmech.amsc.cascade.magnitude`` / ``.pin_slot_at_zero``
    Class-K pin-slot. NOTE their type annotations say ``float`` but the
    implementations are type-preserving and return ``Q`` for a ``Q`` input —
    verified on this tree. (Filed below as a DOC defect, not a code gap.)
``srmech.amsc.laplacian.jacobi_eigvals``
    Class-L symmetric spectrum, replacing ``scipy.linalg.eigvalsh``.
"""

from __future__ import annotations

import json
import math
from typing import Dict, List, Sequence, Tuple

from srmech.amsc.q import Q
from srmech.amsc.qalg import Qalg
from srmech.amsc.cascade import magnitude, pin_slot_at_zero, reorient
from srmech.amsc.rational import (
    best_rational,
    cos as qcos,
    exp as qexp,
    log as qlog,
    pi_cascade_digits,
    sin as qsin,
    sqrt as qsqrt,
)

ZERO = Q(0, 1)
ONE = Q(1, 1)


# ===========================================================================
# PRIMITIVE-GAP REGISTER  (emitted into every port's NDJSON)
# ===========================================================================

PRIMITIVE_GAPS: List[Dict[str, object]] = [
    {
        "gap_id": "GAP-1",
        "an_class": "N",
        "missing_op": "Bessel function of the first kind J_k(x), integer order",
        "replaced": "scipy.special.jv",
        "srmech_search": (
            "regex bessel|drum|membrane|vibrat|acoust over all 516 registered op "
            "names/categories/summaries -> zero real hits. 'bell' resolves to "
            "srmech.qm.bell (CHSH/Tsirelson), 'plate' matches 'template'; the only "
            "literal 'Bessel' in the tree is prose at laplacian.py:6123."
        ),
        "hand_rolled_as": "bessel_j",
        "method": (
            "ascending power series DLMF 10.2.2 / Watson 1922 Sec 3.1, "
            "J_k(x) = sum_m (-1)^m/(m!(m+k)!)*(x/2)^(2m+k), evaluated by exact "
            "integer recurrence in a declared 2**-256 fixed-point scale — the same "
            "precision-contract shape as srmech's own Q61 log/exp."
        ),
        "verification": (
            "vs the 2026-05-17 oracle |J_k(beta)| values for beta in {1/2, 3/2, 3}: "
            "agreement to 0-2 ulp, with the series value the more accurate side."
        ),
        "status": "HAND-ROLLED (rigorous, bounded)",
    },
    {
        "gap_id": "GAP-2",
        "an_class": "N + K",
        "missing_op": "positive zeros j_{n,m} of J_n  (Bessel-zero finder)",
        "replaced": "scipy.special.jn_zeros",
        "srmech_search": "same sweep as GAP-1 — no peer.",
        "hand_rolled_as": "bessel_j_zero / bessel_zero_table",
        "method": (
            "McMahon asymptotic start (DLMF 10.21.19) then exact-rational Newton on "
            "the GAP-1 series, J_n'(x) = (J_{n-1}-J_{n+1})/2 (DLMF 10.6.1). Class-K "
            "pin-slot supplies the sign discipline; no abs()."
        ),
        "verification": (
            "THREE independent checks, all reported in the output: (a) residual "
            "|J_n(j_nm)| < 1e-70 at the returned rational; (b) the interlacing "
            "invariant j_{n,m} < j_{n+1,m} < j_{n,m+1} (Watson 1922 Sec 15.22) holds "
            "for all 36; (c) agreement to 6 dp with the published table "
            "Abramowitz & Stegun 1964 Table 9.5 p.409 — NOTE that table was "
            "reproduced from model memory, NOT from a verified PDF, so it is a "
            "CORROBORATION only and is NOT an MPM attestation."
        ),
        "status": (
            "HAND-ROLLED (rigorous). The brief offered (a) vendor hard-coded zeros "
            "with a citation, or (b) skip the leg UNSUPPORTED. Neither was taken: "
            "vendoring would have meant shipping table digits recalled from memory "
            "as if attested, which the MPM discipline forbids; computing them with a "
            "self-contained bound + three cross-checks is strictly stronger. The "
            "A&S digits are still printed, labelled as unattested corroboration."
        ),
        "open_question": (
            "Tier-3 UNRESOLVED in this project: whether Bessel zeros are "
            "transcendental or merely algebraic-irrational. DLMF 10.21 carries no "
            "transcendence statement. NOTHING here asserts either way — the zeros "
            "are handled as rationals of declared precision, never as exact algebraic "
            "objects, and no Qalg field is built over them."
        ),
    },
    {
        "gap_id": "GAP-3",
        "an_class": "L (over N)",
        "missing_op": "exact-rational degree-1 least squares (the polyfit(x, y, 1) leg)",
        "replaced": "numpy.polyfit",
        "srmech_search": (
            "srmech.amsc.laplacian.mat_lstsq and "
            "srmech.amsc.cascade.matrix_cascades.lstsq both ship, but both are "
            "Mat-carrier ops backed by array('d') — i.e. float-only. There is no "
            "exact-rational least-squares surface."
        ),
        "hand_rolled_as": "lstsq_line",
        "method": "closed-form normal equations over Q (n*Sxy - Sx*Sy) / (n*Sxx - Sx^2).",
        "status": "HAND-ROLLED (exact, closed-form)",
        "note": (
            "This is the single most reusable missing op in the whole port — it is "
            "hit by strict_kepler_test, by all four decay models, and by the "
            "decay-log-slope fingerprint. A Q/Qalg-native mat_lstsq peer would "
            "close it."
        ),
    },
    {
        "gap_id": "GAP-4",
        "an_class": "K (over N)",
        "missing_op": "bounded nonlinear least squares (Levenberg-Marquardt)",
        "replaced": "scipy.optimize.curve_fit",
        "srmech_search": (
            "regex optimi|minimi|newton|levenberg|gauss.?newton|nonlinear|curve.?fit "
            "over all 516 ops -> no optimiser surface of any kind. srmech has "
            "iterate-to-convergence Class-K ops (kepler_solve, eigvals shifted-QR) "
            "but no general parameter fit."
        ),
        "hand_rolled_as": "lm_fit",
        "method": (
            "Levenberg-Marquardt over Q: exact Jacobian, damped normal equations "
            "solved exactly by 3x3 Gaussian elimination over Q, residuals "
            "accumulated in a declared 2**-180 fixed-point scale so the 500-point "
            "sum has ONE common denominator, parameters capped each step by "
            "Class-N best_rational."
        ),
        "verification": (
            "bell envelope: recovers the exact minimiser (E0, tau, beta) = "
            "(1, 2, 1) with residual identically zero; drum: (1, 2/3, 1) likewise; "
            "piano: lands 1.2e-12 LOWER on the exact objective than scipy's "
            "curve_fit did (measured by profiling E0 out analytically at both "
            "parameter pairs, not asserted)."
        ),
        "caveat": (
            "A plain damped LM is NOT curve_fit's 'trf' trust-region reflective "
            "method. From the published p0 the plain LM descends into a genuine "
            "local minimum on the drum envelope (E0 pins to its upper bound, "
            "tau -> 5.6e-5, beta -> 0.14, SSE genuinely decreasing) where trf "
            "escapes. The falsifier port therefore runs a DECLARED deterministic "
            "4-point multi-start whose first start is the original p0 verbatim, and "
            "reports the single-start result alongside. A bounded trust-region "
            "peer would close this properly."
        ),
        "status": "HAND-ROLLED",
    },
    {
        "gap_id": "GAP-5",
        "an_class": "I",
        "missing_op": "seeded uniform-[0,1) pseudorandom stream",
        "replaced": "numpy.random.default_rng(seed).uniform(0, 1, size)",
        "srmech_search": (
            "regex random|seed|prng|entropy over all 516 ops -> only DETERMINISTIC "
            "seed-expansion ops (hdc.polar_random, hdc.klein4_expand, "
            "hdc.klein4_role). None produces a uniform real stream, and none "
            "reproduces the numpy stream the oracle was generated from."
        ),
        "hand_rolled_as": "PCG64 (class) / pcg64_uniform_exact",
        "method": (
            "bit-exact replica of the two published algorithms numpy composes: "
            "numpy SeedSequence (32-bit hashmix/mix pool, pool_size 4) and the "
            "PCG64 XSL-RR 128/64 generator (O'Neill 2014, PCG paper, "
            "PCG_DEFAULT_MULTIPLIER_128). Entirely mod-2^32 / mod-2^128 integer "
            "arithmetic — Class I cyclic. Draws are returned EXACTLY as "
            "Q(next_uint64 >> 11, 2**53), which is precisely what numpy's "
            "next_double is, so the random amplitudes are exact rationals."
        ),
        "verification": (
            "SEED SOURCE PINNED = numpy PCG64 + SeedSequence, seeds 0..49, "
            "reproduced bit-exactly: the whole 2026-05-17 falsifier record "
            "(eps_fit_mean/std/min/max, r2_mean/max, monotonic_count, "
            "K_present_count) comes back to <= 2 ulp. That is a positive proof the "
            "replica is the same stream, not a different pinned source."
        ),
        "status": "HAND-ROLLED (bit-exact replica)",
    },
    {
        "gap_id": "GAP-6",
        "an_class": "I / L",
        "missing_op": "exact-rational real DFT (the eigenvalue-density-FFT leg)",
        "replaced": "numpy.fft.rfft",
        "srmech_search": (
            "srmech.amsc.cascade.spectral_cascades.dft / .fft DO ship and are the "
            "right op — but their signature is Sequence[complex], i.e. they lift to "
            "float on entry. No Q-carrier DFT exists."
        ),
        "hand_rolled_as": "exact_rdft_magnitudes",
        "method": (
            "the SAME Antikythera epicycle-sum the shipped dft computes, but over Q "
            "with the 128 distinct twiddles precomputed once from srmech's exact "
            "cos/sin at a Q pi from pi_cascade_digits."
        ),
        "status": "HAND-ROLLED (exact peer of a shipped float op)",
    },
    {
        "gap_id": "GAP-7",
        "an_class": "E",
        "missing_op": "fixed-width histogram / density binning",
        "replaced": "numpy.histogram(..., density=True)",
        "srmech_search": "regex histogram|bin over all 516 ops -> no peer.",
        "hand_rolled_as": "histogram_density",
        "method": "exact Q bin edges, integer counts, density = count/(N*width) in Q.",
        "status": "HAND-ROLLED (exact)",
    },
    {
        "gap_id": "DOC-1",
        "an_class": "K",
        "missing_op": "(not a gap — a documentation defect found during the port)",
        "replaced": "-",
        "srmech_search": "-",
        "hand_rolled_as": "-",
        "method": (
            "srmech.amsc.cascade.magnitude is annotated (x: 'float') -> 'float' and "
            "pin_slot_at_zero as (x: 'float') -> 'Tuple[int, float]', but BOTH are "
            "type-preserving: magnitude(Q(-3,4)) -> Q(3,4) and "
            "pin_slot_at_zero(Q(-3,4)) -> (-1, Q(3,4)), likewise for int. The "
            "annotation actively discourages the exact-cascade use that the Class-K "
            "ban on abs() requires. Signature should read (x: 'float | int | Q')."
        ),
        "status": "DEFECT (annotation only; behaviour is correct)",
    },
    {
        "gap_id": "DOC-2",
        "an_class": "-",
        "missing_op": "(not a gap — a Q-carrier ergonomics trap found during the port)",
        "replaced": "-",
        "srmech_search": "-",
        "hand_rolled_as": "-",
        "method": (
            "Q(n, 2**k) REDUCES the fraction, so Q(n, 2**k).numerator is NOT n. Any "
            "fixed-point accumulation that round-trips through Q silently loses its "
            "scale. This port therefore keeps fixed-point values as RAW ints "
            "(see fixnum) and only wraps in Q at the boundary. Cost one real bug "
            "during development."
        ),
        "status": "TRAP (documented here so the next port does not re-hit it)",
    },
    {
        "gap_id": "DEFECT-2",
        "an_class": "K",
        "missing_op": (
            "(NEW defect found by this port) pin_slot_at_zero / magnitude break "
            "their own documented type contract AT THE ORIGIN"
        ),
        "replaced": "-",
        "srmech_search": "-",
        "hand_rolled_as": "mag() / orient() guard in this module",
        "method": (
            "srmech/amsc/cascade.py pin_slot_at_zero ends `return 0, 0.0` on the "
            "x == 0 branch, unconditionally. So pin_slot_at_zero(0) -> (0, 0.0) "
            "(float, not int) and pin_slot_at_zero(Q(0,1)) -> (0, 0.0) (float, not "
            "Q) — and magnitude() inherits it. The op's OWN docstring promises "
            "'the int-in / int-magnitude-out type contract is preserved "
            "bit-identically'. The +/- branches DO preserve type (verified: "
            "magnitude(Q(-3,4)) -> Q(3,4)); only the origin branch drops it. That "
            "origin IS the Class-K phase boundary, i.e. the one point the op exists "
            "to name, so an exact cascade silently leaves the rationals exactly "
            "where sign-handling matters most. Fix: return the ZERO of the input's "
            "own type (`x - x`, or a type-dispatched zero)."
        ),
        "status": "DEFECT (found in this port; NOT fixed here, guarded locally)",
    },
    {
        "gap_id": "DEFECT-1",
        "an_class": "-",
        "missing_op": "(pre-existing filed defect, worked around not fixed)",
        "replaced": "-",
        "srmech_search": "-",
        "hand_rolled_as": "-",
        "method": (
            "Qalg.__eq__ does not coerce int or Q into the field: "
            "Qalg.alpha([-2,0,1])**2 == Qalg.rational(2, m) is True but == 2 and "
            "== Q(2,1) are both False. This port always compares element-to-element."
        ),
        "status": "WORKED AROUND (per brief; not fixed here)",
    },
]


FLOAT_LIFTS: List[Dict[str, str]] = [
    {
        "lift_id": "LIFT-1",
        "where": "spike_40_musical_epicycle_analysis_exact.random_graph_laplacian_eigvals",
        "what": "jacobi_eigvals(L) on the 50 Erdos-Renyi integer Laplacians (n=36)",
        "why": (
            "The Laplacians ARE integer matrices, so jacobi_eigvals(L, exact=True) is "
            "in-contract and would keep the spectrum exact. MEASURED on this tree: a "
            "single 36x36 exact call does not finish inside 120 s (char-poly "
            "Faddeev-LeVerrier -> Yun -> Sturm isolation), and this leg needs 50 of "
            "them. The float Jacobi path is the shipped Class-L op's own default "
            "contract and is what the leg's downstream readout (a 128-bin density "
            "histogram + cosine similarity) can resolve. Documented, not silent."
        ),
        "downstream_effect": "reported per-record in the oracle-agreement table",
    },
    {
        "lift_id": "LIFT-2",
        "where": "bessel_j / bessel_j_zero",
        "what": "declared 2**-256 fixed-point scale instead of unbounded exact rationals",
        "why": (
            "An unbounded-denominator evaluation of the Bessel series at a Newton "
            "iterate blows the denominator past 2**11000 and the 36-zero solve does "
            "not finish in 120 s. The fixed scale is still EXACT RATIONAL arithmetic "
            "(denominator 2**256) with a stated bound — the same precision-contract "
            "shape as srmech's own Q61 log/exp — it is NOT an FPU lift."
        ),
        "downstream_effect": "residual |J_n(j_nm)| < 1e-70, i.e. ~54 digits below double",
    },
    {
        "lift_id": "LIFT-3",
        "where": "lm_fit residual accumulation",
        "what": "declared 2**-180 fixed-point scale for residuals and Jacobian entries",
        "why": (
            "Summing 500 Q values with pairwise-coprime ~2**300 denominators produces "
            "a common denominator past 2**100000. Rounding each to one shared scale "
            "makes the sum a single integer. Again exact rational, not float."
        ),
        "downstream_effect": "~36 decimal digits, ~20 beyond double",
    },
    {
        "lift_id": "LIFT-4",
        "where": "every port's final record fields",
        "what": "Q -> float via Q.as_float()",
        "why": "the intended terminal readout; this is the ONLY genuine FPU lift.",
        "downstream_effect": "none",
    },
]


# ===========================================================================
# Class-K sign discipline  (never Python abs())
# ===========================================================================

def mag(x):
    """Class-K pin-slot magnitude, with the DEFECT-2 origin guard.

    ``magnitude`` is type-preserving on the +/- branches but hard-returns the
    float ``0.0`` at the origin, so an exact cascade leaves ℚ exactly at the
    Class-K phase boundary. Re-typed here from the input itself.
    """
    o, m = pin_slot_at_zero(x)
    if o == 0:
        return x - x  # the ZERO of x's own type; DEFECT-2 guard
    return m


def orient(x) -> int:
    """Class-K pin-slot orientation in {-1, 0, +1}."""
    o, _m = pin_slot_at_zero(x)
    return o


def signed(value, orientation: int):
    """Class-C re-application of a captured orientation."""
    return reorient(value, orientation=orientation)


# ===========================================================================
# Exact rational helpers
# ===========================================================================

def qfrom_decimal(text: str) -> Q:
    """The EXACT rational a decimal literal denotes.

    ``qfrom_decimal("0.7") -> Q(7, 10)`` — NOT the double nearest 0.7. Every
    decimal literal in the 2026-05-17 originals is read this way; where the
    double and the decimal differ the divergence is reported, not hidden.
    """
    text = text.strip()
    o = 1
    if text.startswith("-"):
        o, text = -1, text[1:]
    if "e" in text or "E" in text:
        mant, _, ex = text.replace("E", "e").partition("e")
        base = qfrom_decimal(mant)
        k = int(ex)
        return Q(o * base.numerator, base.denominator) * (
            Q(10 ** k, 1) if k >= 0 else Q(1, 10 ** (-k))
        )
    if "." in text:
        whole, _, frac = text.partition(".")
        return Q(o * int((whole or "0") + frac), 10 ** len(frac))
    return Q(o * int(text), 1)


def fixnum(q: Q, bits: int) -> int:
    """RAW fixed-point integer ``n`` with ``q ~= n / 2**bits``.

    See DOC-2: ``Q(n, 2**bits).numerator`` is NOT ``n`` because ``Q``
    reduces, so fixed-point values must be carried as bare ints.
    """
    return q.numerator * (1 << bits) // q.denominator


def qcap(q: Q, max_bits: int = 72) -> Q:
    """Class-N denominator cap via the Stern-Brocot best-rational convergent."""
    if q.denominator.bit_length() <= max_bits:
        return q
    o, m = pin_slot_at_zero(q.numerator)
    p, r = best_rational(m, q.denominator, 1 << max_bits)
    if r == 0:
        return q
    return signed(Q(p, r), o)


_PI_CACHE: Dict[int, Q] = {}


def q_pi(digits: int = 60) -> Q:
    """Exact rational pi to ``digits`` decimals, via Class-N pi_cascade_digits."""
    if digits not in _PI_CACHE:
        s = pi_cascade_digits(digits).replace(".", "")
        _PI_CACHE[digits] = Q(int(s), 10 ** (len(s) - 1))
    return _PI_CACHE[digits]


def qpow_q(base: Q, expo: Q) -> Q:
    """``base ** expo`` for rational base > 0 and rational exponent, exact Q.

    An INTEGER exponent takes the exact Class-N integer-power route
    (``(p/q)**n``), NOT ``exp(n*log(base))`` — routing an integer power
    through the transcendental cascade would inject ~1 ulp of avoidable
    error. (This mattered: ``0.1**2/2`` is EXACTLY 1/200, and the exact
    route reproduces it while the transcendental route did not.)
    """
    if expo.denominator == 1:
        n = expo.numerator
        if n >= 0:
            return Q(base.numerator ** n, base.denominator ** n)
        return Q(base.denominator ** (-n), base.numerator ** (-n))
    return qexp(expo * qlog(base))


def qhypot(a: Q, b: Q) -> Q:
    return qsqrt(a * a + b * b)


# ===========================================================================
# GAP-1 / GAP-2 — Bessel
# ===========================================================================

_BESSEL_SCALE_BITS = 256
_FACT: List[int] = [1]


def _fact(n: int) -> int:
    while len(_FACT) <= n:
        _FACT.append(_FACT[-1] * len(_FACT))
    return _FACT[n]


def bessel_j(k: int, x: Q, scale_bits: int = _BESSEL_SCALE_BITS) -> Q:
    """GAP-1 — ``J_k(x)`` for integer ``k >= 0`` and rational ``x >= 0``.

    DLMF 10.2.2 / Watson 1922 Sec 3.1 ascending series, summed by the exact
    integer recurrence ``t_{m+1} = -t_m * (x/2)^2 / ((m+1)(m+k+1))`` in a
    declared ``2**-scale_bits`` fixed-point scale (LIFT-2 — exact rational,
    not float). Terminates when the running term underflows the scale, which
    for the alternating series bounds the truncation error by that term.
    """
    if k < 0:
        raise ValueError("bessel_j: integer order k >= 0 only")
    if x < ZERO:
        raise ValueError("bessel_j: rational x >= 0 only (Class-K domain)")
    scale = 1 << scale_bits
    h_num = x.numerator
    h_den = 2 * x.denominator
    H = (h_num * scale) // h_den
    H2 = (H * H) >> scale_bits
    term = scale
    for _ in range(k):
        term = (term * H) >> scale_bits
    term //= _fact(k)
    total = term
    m = 0
    while True:
        _o, m_term = pin_slot_at_zero(term)
        if m_term == 0:
            break
        term = -((term * H2) >> scale_bits) // ((m + 1) * (m + k + 1))
        total += term
        m += 1
        if m > 4000:
            raise RuntimeError("bessel_j: series did not terminate")
    return Q(total, scale)


def _bessel_dj(n: int, x: Q) -> Q:
    """``J_n'(x)`` via DLMF 10.6.1: ``J_n' = (J_{n-1} - J_{n+1}) / 2``."""
    if n == 0:
        return ZERO - bessel_j(1, x)
    return (bessel_j(n - 1, x) - bessel_j(n + 1, x)) / Q(2, 1)


def bessel_j_zero(n: int, m: int, newton_steps: int = 8) -> Q:
    """GAP-2 — the ``m``-th positive zero of ``J_n`` as an exact rational.

    McMahon start (DLMF 10.21.19) then exact-rational Newton on :func:`bessel_j`.
    NOTHING here claims the true zero is rational or algebraic — the return is a
    rational of declared precision whose residual is reported by the caller.
    """
    pi = q_pi(60)
    beta = pi * Q(4 * m + 2 * n - 1, 4)
    mu = 4 * n * n
    x = beta - Q(mu - 1, 8) / beta
    scale = 1 << _BESSEL_SCALE_BITS
    x = Q(fixnum(x, _BESSEL_SCALE_BITS), scale)
    for _ in range(newton_steps):
        x = x - bessel_j(n, x) / _bessel_dj(n, x)
        x = Q(fixnum(x, _BESSEL_SCALE_BITS), scale)
    return x


# Abramowitz & Stegun 1964, Table 9.5 p.409.  ***UNATTESTED*** — reproduced
# from model memory, NOT from a verified PDF.  Used ONLY as a corroborating
# cross-check on the computed zeros; never as an input to any result.
AS_TABLE_9_5_UNATTESTED: Dict[Tuple[int, int], float] = {
    (0, 1): 2.404826, (0, 2): 5.520078, (0, 3): 8.653728,
    (0, 4): 11.791534, (0, 5): 14.930918, (0, 6): 18.071064,
    (1, 1): 3.831706, (1, 2): 7.015587, (1, 3): 10.173468,
    (1, 4): 13.323692, (1, 5): 16.470630, (1, 6): 19.615859,
    (2, 1): 5.135622, (2, 2): 8.417244, (2, 3): 11.619841,
    (2, 4): 14.795952, (2, 5): 17.959819, (2, 6): 21.116997,
    (3, 1): 6.380162, (3, 2): 9.761023, (3, 3): 13.015201,
    (3, 4): 16.223466, (3, 5): 19.409415, (3, 6): 22.582730,
    (4, 1): 7.588342, (4, 2): 11.064709, (4, 3): 14.372537,
    (4, 4): 17.615966, (4, 5): 20.826933, (4, 6): 24.019020,
    (5, 1): 8.771484, (5, 2): 12.338604, (5, 3): 15.700174,
    (5, 4): 18.980134, (5, 5): 22.217800, (5, 6): 25.430341,
}

_ZERO_CACHE: Dict[Tuple[int, int], Q] = {}


def bessel_zero_table(n_orders: int, m_zeros: int) -> Dict[Tuple[int, int], Q]:
    out: Dict[Tuple[int, int], Q] = {}
    for n in range(n_orders):
        for m in range(1, m_zeros + 1):
            key = (n, m)
            if key not in _ZERO_CACHE:
                _ZERO_CACHE[key] = bessel_j_zero(n, m)
            out[key] = _ZERO_CACHE[key]
    return out


def bessel_zero_verification(zeros: Dict[Tuple[int, int], Q]) -> Dict[str, object]:
    """The three cross-checks GAP-2 promises, as a record."""
    worst_resid = 0.0
    for (n, _m), z in zeros.items():
        worst_resid = max(worst_resid, float(mag(bessel_j(n, z)).as_float()))
    orders = sorted({n for n, _ in zeros})
    ms = sorted({m for _, m in zeros})
    interlace_ok = True
    for n in orders[:-1]:
        for m in ms[:-1]:
            a = zeros[(n, m)].as_float()
            b = zeros[(n + 1, m)].as_float()
            c = zeros[(n, m + 1)].as_float()
            if not (a < b < c):
                interlace_ok = False
    worst_as = 0.0
    n_as = 0
    for key, z in zeros.items():
        if key in AS_TABLE_9_5_UNATTESTED:
            n_as += 1
            d = z.as_float() - AS_TABLE_9_5_UNATTESTED[key]
            worst_as = max(worst_as, float(mag(d)))
    return {
        "check_a_worst_residual_abs_J_n_at_zero": worst_resid,
        "check_b_interlacing_watson_15_22_holds": interlace_ok,
        "check_c_vs_AS_table_9_5_n_compared": n_as,
        "check_c_vs_AS_table_9_5_worst_delta": worst_as,
        "check_c_caveat": (
            "A&S Table 9.5 digits reproduced from model memory, NOT PDF-verified. "
            "Corroboration only — NOT an MPM attestation."
        ),
        "transcendence_claim": (
            "NONE. Whether Bessel zeros are transcendental or algebraic-irrational "
            "is an OPEN Tier-3 question in this project; DLMF 10.21 states nothing. "
            "These values are rationals of declared precision only."
        ),
    }


# ===========================================================================
# GAP-3 — exact-rational degree-1 least squares
# ===========================================================================

def lstsq_line(xs: Sequence[Q], ys: Sequence[Q]) -> Tuple[Q, Q]:
    """GAP-3 — exact ``polyfit(xs, ys, 1)``: returns ``(slope, intercept)``.

    Closed-form normal equations over Q. numpy's polyfit reaches the same
    minimiser through an SVD of the Vandermonde matrix; this is that
    minimiser exactly.
    """
    n = len(xs)
    if n < 2:
        raise ValueError("lstsq_line needs >= 2 points")
    nq = Q(n, 1)
    sx = sum(xs, ZERO)
    sy = sum(ys, ZERO)
    sxx = sum((x * x for x in xs), ZERO)
    sxy = sum((x * y for x, y in zip(xs, ys)), ZERO)
    den = nq * sxx - sx * sx
    if den == ZERO:
        raise ZeroDivisionError("lstsq_line: degenerate design")
    slope = (nq * sxy - sx * sy) / den
    intercept = (sy - slope * sx) / nq
    return slope, intercept


def r_squared(ys: Sequence[Q], yhat: Sequence[Q]) -> Tuple[Q, Q, Q]:
    """Return ``(r2, ss_res, ss_tot)`` exactly, with the originals' guard."""
    n = Q(len(ys), 1)
    mean = sum(ys, ZERO) / n
    ss_res = sum(((a - b) * (a - b) for a, b in zip(ys, yhat)), ZERO)
    ss_tot = sum(((a - mean) * (a - mean) for a in ys), ZERO)
    ratio = ss_res / ss_tot if ss_tot > Q(1, 10 ** 15) else ONE
    return ONE - ratio, ss_res, ss_tot


# ===========================================================================
# GAP-4 — bounded Levenberg-Marquardt over Q
# ===========================================================================

_LM_SCALE_BITS = 180


def lm_fit(model, jac, ts, ys, p0, lo, hi, max_iter: int = 60,
           inner_tries: int = 10, cap_bits: int = 72):
    """GAP-4 — bounded nonlinear least squares over Q.

    ``model(t, params) -> Q``; ``jac(t, params) -> [Q, Q, Q]``.
    Residuals are accumulated in the declared 2**-180 fixed-point scale
    (LIFT-3); the damped normal equations are solved exactly over Q.
    Returns ``(params, sse_fixed_int, n_iter, converged)``.
    """
    params = list(p0)
    lam = Q(1, 1000)

    def sse(pars) -> int:
        s = 0
        for t, y in zip(ts, ys):
            r = fixnum(y - model(t, pars), _LM_SCALE_BITS)
            s += r * r
        return s

    cur = sse(params)
    converged = False
    it = 0
    for it in range(1, max_iter + 1):
        jtj = [[0] * 3 for _ in range(3)]
        jtr = [0, 0, 0]
        for t, y in zip(ts, ys):
            row = [fixnum(v, _LM_SCALE_BITS) for v in jac(t, params)]
            rn = fixnum(y - model(t, params), _LM_SCALE_BITS)
            for a in range(3):
                jtr[a] += row[a] * rn
                for b in range(a, 3):
                    jtj[a][b] += row[a] * row[b]
        for a in range(3):
            for b in range(a):
                jtj[a][b] = jtj[b][a]
        improved = False
        for _try in range(inner_tries):
            amat = [[Q(jtj[a][b], 1) * (ONE + lam if a == b else ONE)
                     for b in range(3)] for a in range(3)]
            try:
                step = _solve3(amat, [Q(v, 1) for v in jtr])
            except ZeroDivisionError:
                lam = lam * Q(10, 1)
                continue
            cand = []
            for v, d, l, h in zip(params, step, lo, hi):
                nv = qcap(v + d, cap_bits)
                if nv < l:
                    nv = l
                if nv > h:
                    nv = h
                cand.append(nv)
            ns = sse(cand)
            if ns < cur:
                rel_gain = cur - ns
                params, cur = cand, ns
                lam = lam / Q(10, 1)
                improved = True
                if rel_gain * (1 << 40) < cur:
                    converged = True
                break
            lam = lam * Q(10, 1)
        if not improved:
            converged = True
            break
        if cur == 0 or converged:
            converged = True
            break
    return params, cur, it, converged


def _solve3(a, b):
    """Exact 3x3 solve by Gaussian elimination over Q (Class-K partial pivot)."""
    m = [list(a[i]) + [b[i]] for i in range(3)]
    for c in range(3):
        piv = max(range(c, 3), key=lambda r: float(mag(m[r][c])))
        m[c], m[piv] = m[piv], m[c]
        if m[c][c] == ZERO:
            raise ZeroDivisionError("singular")
        p = m[c][c]
        m[c] = [v / p for v in m[c]]
        for r in range(3):
            if r != c and m[r][c] != ZERO:
                f = m[r][c]
                m[r] = [m[r][j] - f * m[c][j] for j in range(4)]
    return [m[i][3] for i in range(3)]


# ===========================================================================
# GAP-5 — numpy PCG64 + SeedSequence, bit-exact replica (Class I)
# ===========================================================================

_M32 = 0xFFFFFFFF
_M64 = 0xFFFFFFFFFFFFFFFF
_M128 = (1 << 128) - 1
_XSHIFT = 16
_INIT_A = 0x43B0D7E5
_MULT_A = 0x931E8875
_INIT_B = 0x8B51F9DD
_MULT_B = 0x58F38DED
_MIX_L = 0xCA01F9DD
_MIX_R = 0x4973F715
_PCG_MULT = (2549297995355413924 << 64) | 4865540595714422341


def _seed_sequence_pool(seed_int: int, pool_size: int = 4) -> List[int]:
    """numpy SeedSequence entropy pool. Class-I mod-2**32 cascade."""
    s = int(seed_int)
    entropy: List[int] = []
    if s == 0:
        entropy = [0]
    else:
        while s:
            entropy.append(s & _M32)
            s >>= 32
    mixer = [0] * pool_size
    hc = [_INIT_A]

    def hashmix(v: int) -> int:
        v = (v ^ hc[0]) & _M32
        hc[0] = (hc[0] * _MULT_A) & _M32
        v = (v * hc[0]) & _M32
        return (v ^ (v >> _XSHIFT)) & _M32

    def mix(x: int, y: int) -> int:
        r = (_MIX_L * x - _MIX_R * y) & _M32
        return (r ^ (r >> _XSHIFT)) & _M32

    for i in range(pool_size):
        mixer[i] = hashmix(entropy[i] if i < len(entropy) else 0)
    for i_src in range(pool_size):
        for i_dst in range(pool_size):
            if i_src != i_dst:
                mixer[i_dst] = mix(mixer[i_dst], hashmix(mixer[i_src]))
    for i_src in range(pool_size, len(entropy)):
        for i_dst in range(pool_size):
            mixer[i_dst] = mix(mixer[i_dst], hashmix(entropy[i_src]))
    return mixer


class PCG64:
    """numpy's default_rng bit generator: PCG64 XSL-RR 128/64 (O'Neill 2014)."""

    def __init__(self, seed: int):
        pool = _seed_sequence_pool(seed)
        hc = _INIT_B
        w32: List[int] = []
        for i in range(8):
            v = (pool[i % len(pool)] ^ hc) & _M32
            hc = (hc * _MULT_B) & _M32
            v = (v * hc) & _M32
            w32.append((v ^ (v >> _XSHIFT)) & _M32)
        w64 = [w32[2 * i] | (w32[2 * i + 1] << 32) for i in range(4)]
        initstate = (w64[0] << 64) | w64[1]
        initseq = (w64[2] << 64) | w64[3]
        self.inc = ((initseq << 1) | 1) & _M128
        self.state = 0
        self._step()
        self.state = (self.state + initstate) & _M128
        self._step()

    def _step(self) -> None:
        self.state = (self.state * _PCG_MULT + self.inc) & _M128

    def next_uint64(self) -> int:
        self._step()
        s = self.state
        v = ((s >> 64) ^ (s & _M64)) & _M64
        rot = (s >> 122) & 63
        return ((v >> rot) | (v << ((-rot) & 63))) & _M64

    def next_double_q(self) -> Q:
        """numpy's next_double, EXACTLY: (u >> 11) / 2**53 as a rational."""
        return Q(self.next_uint64() >> 11, 1 << 53)


def pcg64_uniform_exact(seed: int, n: int) -> List[Q]:
    """``numpy.random.default_rng(seed).uniform(0, 1, n)`` as exact rationals."""
    g = PCG64(seed)
    return [g.next_double_q() for _ in range(n)]


# ===========================================================================
# GAP-6 / GAP-7 — exact density histogram and exact real DFT magnitudes
# ===========================================================================

def histogram_density(values: Sequence[Q], n_bins: int, lo: Q, hi: Q) -> List[Q]:
    """GAP-7 — ``numpy.histogram(values, bins=n_bins, range=(lo, hi), density=True)``.

    Exact: integer counts, ``density = count / (n_in_range * width)`` in Q.
    numpy normalises by ``n.sum()`` (the count that LANDED IN BINS), not by
    ``len(values)`` — values outside ``range`` are dropped before the
    normalisation. Reproduced here; the last bin is closed on the right.
    """
    width = (hi - lo) / Q(n_bins, 1)
    counts = [0] * n_bins
    n_in = 0
    for v in values:
        if v < lo or v > hi:
            continue
        idx = int(((v - lo) / width).as_float())
        # exact placement: walk back/forward off the float hint
        while idx > 0 and v < lo + width * Q(idx, 1):
            idx -= 1
        while idx < n_bins - 1 and v >= lo + width * Q(idx + 1, 1):
            idx += 1
        counts[idx] += 1
        n_in += 1
    if n_in == 0:
        return [ZERO] * n_bins
    total = Q(n_in, 1)
    return [Q(c, 1) / (total * width) for c in counts]


_DFT_SCALE_BITS = 160
_TWIDDLE_CACHE: Dict[int, Tuple[List[int], List[int]]] = {}


def _twiddles_fixed(n: int) -> Tuple[List[int], List[int]]:
    """cos/sin of ``-2*pi*j/n``, j = 0..n-1, as 2**-160 fixed-point integers.

    Values come from srmech's Class-N exact ``cos`` / ``sin`` at a Q pi from
    ``pi_cascade_digits``; only the COMMON DENOMINATOR is imposed, so the
    accumulation below is one integer sum rather than a 128-way denominator
    blow-up (LIFT-3 in kind, still exact rational).
    """
    if n not in _TWIDDLE_CACHE:
        pi = q_pi(60)
        cs, sn = [], []
        for j in range(n):
            theta = ZERO - (Q(2, 1) * pi * Q(j, 1) / Q(n, 1))
            cs.append(fixnum(qcos(theta), _DFT_SCALE_BITS))
            sn.append(fixnum(qsin(theta), _DFT_SCALE_BITS))
        _TWIDDLE_CACHE[n] = (cs, sn)
    return _TWIDDLE_CACHE[n]


def exact_rdft_magnitudes(x: Sequence[Q]) -> List[Q]:
    """GAP-6 — ``|numpy.fft.rfft(x)|`` for real ``x``, exact over Q.

    The same Antikythera epicycle-sum ``X_k = sum_n x_n * e^(-2 pi i k n / N)``
    that ``srmech.amsc.cascade.spectral_cascades.dft`` computes, but with the
    ``N`` distinct twiddles taken exactly from srmech's Class-N cos/sin at a Q
    pi, so nothing leaves the rationals.
    """
    n = len(x)
    cs, sn = _twiddles_fixed(n)
    xf = [fixnum(v, _DFT_SCALE_BITS) for v in x]
    scale2 = 1 << (2 * _DFT_SCALE_BITS)
    out: List[Q] = []
    for k in range(n // 2 + 1):
        re = 0
        im = 0
        for j, xv in enumerate(xf):
            if xv == 0:
                continue
            idx = (k * j) % n
            re += xv * cs[idx]
            im += xv * sn[idx]
        out.append(qhypot(Q(re, scale2), Q(im, scale2)))
    return out


def cosine_similarity_q(a: Sequence[Q], b: Sequence[Q]) -> Q:
    """Exact cosine similarity, with the originals' 1e-15 norm guard."""
    dot = sum((x * y for x, y in zip(a, b)), ZERO)
    na = qsqrt(sum((x * x for x in a), ZERO))
    nb = qsqrt(sum((x * x for x in b), ZERO))
    guard = Q(1, 10 ** 15)
    if na < guard or nb < guard:
        return ZERO
    return dot / (na * nb)


# ===========================================================================
# The Spike #30B v3 strict K-test, exact
# ===========================================================================

def strict_kepler_test(coeffs: Sequence[Q], k_max: int = 6) -> Dict[str, object]:
    """Spike #30B v3 strict three-criteria Kepler test, exact through to readout.

    Identical decision procedure to the 2026-05-17 float original:
      (1) eps_fit in (0.001, 0.5)   (2) r2 > 0.99   (3) |c_k| strictly decreasing
    All three gates are evaluated in Q, so no threshold is decided by a float
    round.
    """
    abs_c = [mag(c) for c in coeffs]
    if len(abs_c) <= k_max:
        k_max = len(abs_c) - 1
    cs = abs_c[1:k_max + 1]
    ks = [Q(i + 1, 1) for i in range(len(cs))]
    cmax = max(abs_c) if abs_c else ZERO
    floor = max(Q(1, 10 ** 15), cmax * Q(1, 10 ** 12))
    keep = [i for i, c in enumerate(cs) if c > floor]
    if len(keep) < 3:
        return {
            "eps_fit": float("nan"),
            "r2": 0.0,
            "monotonic_decreasing": False,
            "in_physical_range": False,
            "high_r2": False,
            "kepler_signature_present": False,
            "n_harmonics_used": len(keep),
            "c1_c2_c3": [0.0, 0.0, 0.0],
        }
    ks_used = [ks[i] for i in keep]
    cs_used = [cs[i] for i in keep]
    log_c = [qlog(c) for c in cs_used]
    slope, intercept = lstsq_line(ks_used, log_c)
    eps_fit = qexp(slope)
    yhat = [slope * k + intercept for k in ks_used]
    r2, _ss_res, _ss_tot = r_squared(log_c, yhat)
    monotonic = all(cs_used[i + 1] - cs_used[i] < ZERO for i in range(len(cs_used) - 1))
    in_range = Q(1, 1000) < eps_fit < Q(1, 2)
    high_r2 = r2 > Q(99, 100)
    return {
        "eps_fit": eps_fit.as_float(),
        "r2": r2.as_float(),
        "monotonic_decreasing": bool(monotonic),
        "in_physical_range": bool(in_range),
        "high_r2": bool(high_r2),
        "kepler_signature_present": bool(monotonic and in_range and high_r2),
        "n_harmonics_used": len(ks_used),
        "c1_c2_c3": [
            cs_used[i].as_float() if i < len(cs_used) else 0.0 for i in range(3)
        ],
        "_exact": {"eps_fit": eps_fit, "r2": r2, "slope": slope},
    }


def clean_for_json(x):
    """NDJSON serialiser. Q/Qalg -> float; the internal ``_exact`` key is dropped."""
    if isinstance(x, dict):
        return {k: clean_for_json(v) for k, v in x.items() if not k.startswith("_")}
    if isinstance(x, (list, tuple)):
        return [clean_for_json(v) for v in x]
    if isinstance(x, Q):
        return x.as_float()
    if isinstance(x, Qalg):
        return x.to_float()
    if isinstance(x, bool):
        return bool(x)
    if x is None or isinstance(x, (str, int, float)):
        return x
    return str(x)


def write_ndjson(path: str, records: Sequence[dict]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(clean_for_json(r)) + "\n")


def provenance_records(script: str) -> List[dict]:
    """The gap + float-lift disclosure block every port emits FIRST."""
    return [
        {
            "kind": "port_provenance",
            "script": script,
            "ported_from": script.replace("_exact", "") + " (2026-05-17)",
            "port_date": "2026-07-30",
            "removed_dependencies": ["numpy", "scipy", "fractions"],
            "carriers": ["srmech.amsc.q.Q", "srmech.amsc.qalg.Qalg"],
            "srmech_version_note": "ported against srmech 0.9.0rcN (516 registered ops)",
        },
        {"kind": "primitive_gap_register", "gaps": PRIMITIVE_GAPS},
        {"kind": "float_lift_register", "lifts": FLOAT_LIFTS},
    ]


__all__ = [
    "ZERO", "ONE", "Q", "Qalg",
    "PRIMITIVE_GAPS", "FLOAT_LIFTS", "provenance_records",
    "mag", "orient", "signed",
    "qfrom_decimal", "fixnum", "qcap", "q_pi", "qpow_q", "qhypot",
    "qlog", "qexp", "qsqrt", "qsin", "qcos",
    "bessel_j", "bessel_j_zero", "bessel_zero_table", "bessel_zero_verification",
    "AS_TABLE_9_5_UNATTESTED",
    "lstsq_line", "r_squared",
    "lm_fit",
    "PCG64", "pcg64_uniform_exact",
    "histogram_density", "exact_rdft_magnitudes", "cosine_similarity_q",
    "strict_kepler_test", "clean_for_json", "write_ndjson",
]
