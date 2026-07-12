"""srmech.amsc.thetasum — ``ThetaSum``, the ADDITIVE theta-function CARRIER that
unblocks GENUINE elliptic creative telescoping (the foundation under a rebuilt
``elliptic_gosper`` / ``elliptic_zeilberger`` / ``elliptic_wz_certificate``).

Where :class:`~srmech.amsc.ellbase.EllRatio` (rc60) carries a single
MULTIPLICATIVE theta-quotient ``prefactor · ∏(num θ) / ∏(den θ)``, it is NOT
additively closed: theta-quotients do not add or subtract within the carrier
(``θ(a) + θ(b)`` is not a theta-quotient). Genuine creative telescoping's residual

    Σ_j a_j(n)·F(n+j,k) − (G(n,k+1) − G(n,k))

is exactly such a SUM / DIFFERENCE of theta-quotients, so it cannot be decided in
``EllRatio`` — the boundary that forced both the rc61 ``elliptic_gosper`` and the
(now-closed) partial ``elliptic_zeilberger`` to honestly hit ``None`` on the
``k``-dependent case. ``ThetaSum`` is the ADDITIVE layer over rc59 ``Theta`` /
rc60 ``EllRatio`` that closes that gap.

The carrier (a CLEARED rational theta-function):

    ThetaSum = (ℚ(q,p)-linear SUM of theta-products) / (single theta-product
               denominator)

Concretely: the numerator is a list of TERMS, each a triple
``(Q coeff, EllMonomial prefactor, tuple-of-Theta factors)``; the denominator is
``(EllMonomial prefactor, tuple-of-Theta factors)``. All exact — ``Q`` coeffs,
``Theta`` symbols over the ``q, p, x, y, param`` lattice; sign is the **Class-K**
pin-slot via the ``Q`` / ``EllMonomial`` sign-branch, never an ALU ``abs()``; no
``math`` module, no numpy, no float (the one place a number is materialised is the
exact-``ℚ`` truncated modified-theta product, used ONLY inside the degree-bound
``is_zero`` test).


================================  THE TWO MPM-VERIFIED THEOREMS  ================================

Both load-bearing forms below were verified at build by reading the ACTUAL source
PDF (extracted + read in full, equation numbers + statement confirmed — NOT a
training-data attribution), per the project's Mathematical-Provenance discipline:

    Hjalmar Rosengren, "Elliptic Hypergeometric Functions" (Lectures at OPSF-S6,
    College Park, MD, 11–15 July 2016), arXiv:1608.06161v3 [math.CA], 20 Jun 2017.

The modified theta function there (his §1.2, the eq. after Lemma 1.2.1) is exactly
the one this package carries: ``θ(x; p) = (x; p)_∞ (p/x; p)_∞ = ∏_{k≥0}(1 − x pᵏ)
(1 − x⁻¹ p^{k+1})``, with the §1.2 shorthand ``θ(a₁,…,aₘ; p) = θ(a₁;p)···θ(aₘ;p)``
and (his Eq. 1.4) ``θ(ax^±; p) = θ(ax; p) θ(a/x; p)``.

(1) THE THETA ADDITION FORMULA — the **Weierstrass three-term theta relation**,
    Rosengren §1.4 "The three-term identity", **Eq. (1.12)** (page 12; "a certain
    three-term relation for theta functions due to Weierstrass", proved there from
    scratch via Liouville's theorem):

        θ(ax^±, bc^±; p) = θ(bx^±, ac^±; p) + (a/c)·θ(cx^±, ba^±; p)

    i.e. in the fully-expanded modified-theta product form (using Eq. 1.4):

        θ(ax)θ(a/x)θ(bc)θ(b/c)
            = θ(bx)θ(b/x)θ(ac)θ(a/c) + (a/c)·θ(cx)θ(c/x)θ(ba)θ(b/a)

    — equivalently the zero identity (the canonical certificate-shaped ThetaSum
    whose :meth:`is_zero` must return True):

        θ(ax)θ(a/x)θ(bc)θ(b/c) − θ(bx)θ(b/x)θ(ac)θ(a/c)
            − (a/c)·θ(cx)θ(c/x)θ(ba)θ(b/a)  ≡  0.

    :meth:`ThetaSum.three_term` constructs this exact identity; the addition
    formula is implemented as an exact REDUCTION (it is the constructive tool the
    genuine engine needs, and the keystone known-identity for the ``is_zero`` test).

(2) THE DEGREE BOUND — the **Fundamental Theorem of Elliptic Functions**,
    Rosengren §1.3 "Factorization of elliptic functions", **Lemma 1.3.2** (page
    10): "Let f be multiplicatively elliptic with period p. Then, f has as many
    poles as zeroes, counted with multiplicity, in each period annulus
    A = {x; pr ≤ |x| < r}." Its corollary (the Liouville argument Rosengren spells
    out in the §1.4 proof of Eq. 1.12): a NON-CONSTANT elliptic function must have
    poles, so an elliptic function that is a pole-free combination of theta-factors
    of total degree ``d`` (≤ ``d`` zeros per period annulus) and which actually
    vanishes (has a zero) must be **identically zero**. Operationally: a sum of
    theta-products of bounded elliptic degree ``d`` is ``≡ 0`` IFF it is EXACTLY 0
    at MORE THAN ``d`` distinct points of a period annulus.


====================  WHY ``is_zero`` IS SOUND (rc210 certificate rebuild)  ====================

``is_zero`` NEVER accepts on a converging witness (the rc61 / §76 no-hallucination
standard — a truncated modified-theta product only CONVERGES, it is not exact at
any finite depth, so a raw ``eval_trunc`` of a theta-bearing residual is NOT an
exact test) — and, as of rc210, it NEVER accepts on a numeric p-order band either.
The contract is SOUND-TRUE-ONLY: ``True`` ⟺ certificate-proven identically zero;
``False`` = "not proven" (a proven-nonzero object or an honest decline). The
pre-rc210 decision claimed COMPLETENESS via a single-variable degree-band
q-expansion + a mixed-character node count; both were UNSOUND (they certified
provably-NONZERO objects as zero — a multi-term cancellation gap outruns the
max-single-term band, and a mixed-character sum lies in no single section space),
so completeness on the True side was RETIRED, not repaired.

  1. CLEAR to the numerator. The denominator theta-product is a nonzero elliptic
     function, so ``self == 0 ⟺ numerator ≡ 0`` (a sum of theta-products); the
     empty / exactly-cancelled numerator is proven zero outright [Z1].

  2. FAST PATH — GROUP the numerator's terms by QUASI-PERIODICITY CLASS (the net
     multiplier monomial under ``x ↦ p·x`` and ``y ↦ p·y``; Rosengren Eq. 1.6 via
     :meth:`~srmech.amsc.ellbase.Theta.canonicalize`; different classes are linearly
     independent over ``ℚ(q,p)``) and REDUCE each class by the EXACT Weierstrass
     three-term relation (theorem (1) below): ``±``-pairs ``θ(α·β^±) = θ(αβ)θ(α/β)``
     recovered by the exact midpoint / geometric-mean test, driven to a canonical
     additive normal form by a strictly-decreasing (hence terminating) rewrite.
     EVERY class reduced to the empty normal form ⇒ proven zero [Z2].

  3. COMPLETION — the three-valued CERTIFICATE RECURSION (:func:`_decide_struct`):
     split by the exact per-symbol character ``(D_v, μ_v)`` (degree + full Eq.-1.6
     multiplier; all components proven zero ⇒ zero [Z3s]); inside one character,
     retry the three-term reduction over the component's ACTUAL variables [Z2];
     else interpolate ONE variable at ``D_v+1`` PAIRWISE-DISTINCT nodes of
     ``ℂ*/p^ℤ`` (theta-factor zeros + deduplicated distinct primes) — a
     degree-``D_v`` section vanishing (recursively PROVEN) at ``D_v+1`` distinct
     points is identically zero (Rosengren Cor. 1.3.5, theorem (2) below) [Z4].
     Anything else is honestly ``False``. The NONZERO side (a singleton term, an
     exact nonzero lattice coefficient, a nonzero node, a nonzero component) is
     DETECTION ONLY — it can label an object proven-nonzero for diagnostics, but
     no detection depth ever produces a ``True``. :meth:`eval_trunc` materialises
     a value ONLY as a truncated-product convergence ORACLE for tests — it is NOT
     on the ``is_zero`` decision path.

C peer: ``srmech_thetasum_is_zero`` (the ±-pair fast path, sound-True) +
``srmech_thetasum_is_zero_interpolation`` (+ the rc103 parallel variant), the
latter REBUILT in rc210 as the 1:1 mirror of the certificate recursion's bool —
the old band/mixed-character C decision was the live false-zero surface on native
builds. The pure-Python body here is the parity oracle (the committed corpus suite
pins native == pure).
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Mapping, Tuple

from . import _native as _nat
from .ellbase import EllMonomial, EllRatio, Theta, _P, _X, _coerce_q
from .q import Q

__all__ = ["ThetaSum"]

_Q_ZERO = Q(0, 1)
_Q_ONE = Q(1, 1)
_Y = "y"        # the k-summation-variable symbol (y = qᵏ); the second elliptic var

# A term of the cleared numerator: (Q coeff, EllMonomial prefactor, tuple of Theta).
# The coeff is folded into the prefactor on construction (kept separate in the type
# only for the public-builder ergonomics); internally a term is (prefactor, thetas).
_Term = Tuple[EllMonomial, Tuple[Theta, ...]]


# Exact-ℚ sample points for the :meth:`ThetaSum.eval_trunc` CONVERGENCE ORACLE — used by
# the TESTS as an independent cross-check (a genuine theta identity's truncated value
# converges to 0 as the depth grows), NOT by the exact symbolic :meth:`ThetaSum.is_zero`
# decision (which never evaluates). All exact rationals — no float. Several independent
# (x, y, params) points with |p| < 1.
_VERIFY_POINTS: Tuple[Dict[str, Q], ...] = (
    {"q": Q(2, 1), _P: Q(1, 9), _X: Q(2, 3), _Y: Q(3, 5), "a": Q(3, 5),
     "b": Q(4, 7), "c": Q(5, 8), "d": Q(2, 9), "e": Q(7, 4), "f": Q(3, 8)},
    {"q": Q(3, 1), _P: Q(1, 16), _X: Q(3, 4), _Y: Q(4, 9), "a": Q(2, 5),
     "b": Q(5, 7), "c": Q(3, 8), "d": Q(4, 9), "e": Q(2, 3), "f": Q(5, 6)},
    {"q": Q(2, 1), _P: Q(1, 25), _X: Q(4, 5), _Y: Q(5, 8), "a": Q(6, 7),
     "b": Q(3, 10), "c": Q(7, 9), "d": Q(5, 11), "e": Q(8, 5), "f": Q(2, 7)},
    {"q": Q(2, 1), _P: Q(1, 36), _X: Q(5, 6), _Y: Q(2, 7), "a": Q(4, 9),
     "b": Q(7, 8), "c": Q(3, 7), "d": Q(6, 11), "e": Q(5, 9), "f": Q(8, 7)},
    {"q": Q(3, 1), _P: Q(1, 49), _X: Q(6, 7), _Y: Q(3, 8), "a": Q(5, 11),
     "b": Q(2, 9), "c": Q(8, 9), "d": Q(7, 10), "e": Q(4, 7), "f": Q(9, 8)},
)

# The truncation depth the eval_trunc convergence oracle reads in tests. Larger = closer
# convergence (a genuine identity shrinks ~|p|^depth toward 0). Immaterial to is_zero.
_VERIFY_TRUNC = 16


# ── shared support for the SOUND structural certificate recursion (rc210 rebuild;
# the recursion itself is `_decide_struct` below). The Z4 interpolation certificate is
# Rosengren arXiv:1608.06161 Cor 1.3.5: a SINGLE-character component of v-degree D that
# vanishes (recursively PROVEN) at D+1 nodes pairwise distinct mod p^ℤ is ≡ 0. Nodes =
# the θ-FACTOR ZEROS (monomials in the remaining vars, killing terms via θ(1)=0) +
# deduplicated augment constants; SUBSTITUTING nodes (never MERGING ±-pairs) dissolves
# the √ obstruction the three-term reduction stalls on. Exact-ℚ, no q-grid; the pure
# parity oracle for the native peer.
#
# The augment constants MUST be GLOBALLY DISTINCT PRIMES threaded through the recursion (not a
# reused pool): substituting two variables to the SAME constant would make a cross-variable
# factor θ(x_i/x_j) → θ(1)=0 a SPURIOUS zero, wrongly proving a non-zero product ≡0. With
# distinct integer primes, θ(∏ pᵢ^{eᵢ}) = θ(1) IFF ∏ pᵢ^{eᵢ}=1 IFF every eᵢ=0 (unique
# factorization; an integer is never a nome power p^k) — so the ONLY vanishings are genuine.
#
# _STRUCT_MARGIN survives rc210 ONLY as the N2 detection-depth floor (and the #693 test's
# band arithmetic) — there is NO band on the True side anymore.
_STRUCT_MARGIN = 3
_STRUCT_PRIMES: "Tuple[int, ...]" = (
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83,
    89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151, 157, 163, 167, 173, 179,
    181, 191, 193, 197, 199, 211, 223, 227, 229, 233, 239, 241, 251, 257, 263, 269, 271, 277,
    281, 283, 293, 307, 311, 313, 317, 331, 337, 347, 349, 353, 359, 367, 373, 379, 383, 389,
    397, 401, 409, 419, 421, 431, 433, 439, 443, 449, 457, 461, 463, 467, 479, 487, 491, 499,
    503, 509, 521, 523, 541, 547, 557, 563, 569, 571, 577, 587, 593, 599, 601, 607, 613, 617)


def _struct_mono(coeff: Q, exps: "Dict[str, int]") -> EllMonomial:
    m = EllMonomial(coeff)
    for s, ee in exps.items():
        bs = EllMonomial.symbol(s) if ee >= 0 else EllMonomial.symbol(s).inv()
        for _ in range(ee if ee >= 0 else -ee):
            m = m * bs
    return m


def _struct_subst(mono: EllMonomial, v: str, node: EllMonomial) -> EllMonomial:
    """Substitute v -> node (a zero-MONOMIAL or a rational-CONSTANT EllMonomial) in mono."""
    out = EllMonomial(mono.coeff)
    for s, e in mono.exps.items():
        base = (node if e >= 0 else node.inv()) if s == v else (
            EllMonomial.symbol(s) if e >= 0 else EllMonomial.symbol(s).inv())
        for _ in range(e if e >= 0 else -e):
            out = out * base
    return out


def _struct_combine(terms: "List") -> "List":
    """Canonicalize each term's thetas (theta(1)=0 kills it) + merge genuinely-identical terms
    (same prefactor monomial AND theta multiset) by adding Q coeffs; drop zero."""
    acc: "Dict" = {}
    for pref, args in terms:
        canon_args = []
        dead = False
        for a in args:
            pr, canon = Theta(a).canonicalize()
            pref = pref * pr
            arg = canon.arg
            if not arg.exps and arg.coeff == _Q_ONE:            # theta(1) = 0
                dead = True
                break
            canon_args.append(arg)
        if dead or pref.is_zero:
            continue
        canon_args.sort(key=lambda m: m._sort_key())
        key = (tuple(sorted(pref.exps.items())), tuple(m._sort_key() for m in canon_args))
        if key in acc:
            acc[key] = (acc[key][0] + pref.coeff, dict(pref.exps), tuple(canon_args))
        else:
            acc[key] = (pref.coeff, dict(pref.exps), tuple(canon_args))
    return [(_struct_mono(c, e), list(a)) for (c, e, a) in acc.values() if c != _Q_ZERO]


def _struct_variables(terms: "List") -> "set":
    """ALL non-``p`` symbols on the theta arguments AND the prefactors.

    The prefactor scan is LOAD-BEARING (rc210 defect D3): scanning theta args only
    silently dropped prefactor-only symbols, so ``a·θ(2x) − b·θ(2x)`` (a ≠ b) was
    treated as the single-variable object ``(1−1)·θ(2x)`` and falsely certified
    zero. With prefactor symbols included, ``a`` / ``b`` carry distinct characters
    (their prefactor exponents differ), the character split separates the terms,
    and each singleton is honestly NOT proven zero."""
    s: "set" = set()
    for pref, args in terms:
        for sym in pref.exps:
            if sym != _P:
                s.add(sym)
        for a in args:
            for sym in a.exps:
                if sym != _P:
                    s.add(sym)
    return s


def _struct_zero_nodes(terms: "List", v: str) -> "List[EllMonomial]":
    """distinct zero-MONOMIAL nodes of the LINEAR (exp +/-1) v-thetas: theta(alpha*v^e)=0 at
    v=(alpha without v)^(-1/e) — substituting kills that term (theta(1)=0)."""
    seen: "Dict" = {}
    for pref, args in terms:
        for a in args:
            e = a.exps.get(v, 0)
            if e in (1, -1):
                rest = EllMonomial(a.coeff)
                for s, ee in a.exps.items():
                    if s == v:
                        continue
                    bb = EllMonomial.symbol(s) if ee >= 0 else EllMonomial.symbol(s).inv()
                    for _ in range(ee if ee >= 0 else -ee):
                        rest = rest * bb
                node = rest.inv() if e == 1 else rest
                seen[(tuple(sorted(node.exps.items())), node.coeff)] = node
    return list(seen.values())


def _struct_pexp_mul(a: "Dict", b: "Dict", k: int) -> "Dict":
    out: "Dict" = {}
    for pa, la in a.items():
        for pb, lb in b.items():
            pk = pa + pb
            if pk > k:
                continue
            dst = out.setdefault(pk, {})
            for ka, va in la.items():
                for kb, vb in lb.items():
                    kk = ka + kb
                    dst[kk] = dst.get(kk, _Q_ZERO) + va * vb
    return out


def _struct_theta_p(coeff: Q, e: int, k: int) -> "Dict":
    """theta(coeff*w^e ; p) to p^k over the single kept var w -> {p_pow: {w-exp: Q}}."""
    acc = {0: {0: _Q_ONE}}
    ci = _Q_ONE / coeff
    for j in range(0, k + 1):
        f1 = {0: {0: _Q_ONE}}
        d = f1.setdefault(j, {})
        d[e] = d.get(e, _Q_ZERO) - coeff
        acc = _struct_pexp_mul(acc, f1, k)
        if j + 1 <= k:
            f2 = {0: {0: _Q_ONE}}
            d = f2.setdefault(j + 1, {})
            d[-e] = d.get(-e, _Q_ZERO) - ci
            acc = _struct_pexp_mul(acc, f2, k)
    return acc


# ── the SOUND three-valued structural decision (rc210 — the is_zero soundness rebuild) ──
#
# The rc98–rc103 "structural interpolation" completion above was replaced WHOLESALE in
# rc210: the shipped decision certified provably-NONZERO objects as zero via two unsound
# devices — (D1) the single-variable p-order BAND k = max-term(Σe²)−1+3 in the old
# `_struct_one_var`, which under-counts MULTI-TERM cancellation gaps (a 6-term
# one-character pair family θ(u·x^±) hides its first nonzero coefficient at p⁶ > band 4),
# and (D2) a MIXED-character node count d = max-term Σe² in the old `_structural_is_zero`,
# which has no supporting theorem (a sum of terms of DIFFERENT quasi-periodicity is in no
# single theta-section space, so "degree-d section ⇒ d+1 nodes" does not apply to it).
# Two further defects rode along: (D3) `_struct_variables` dropped prefactor-only symbols
# (fixed above) and (D4) augment primes were not deduplicated against zero-node constants
# (a duplicate node under-counts the interpolation).
#
# The replacement is the three-valued CERTIFICATE recursion `_decide_struct`:
#
#     ZERO     — proven identically zero (certificate-backed; the ONLY source of True)
#     NONZERO  — proven not identically zero (an exact nonzero coefficient / a singleton
#                term / a nonzero node substitution / a nonzero character component)
#     UNKNOWN  — declined (honest "not proven"); the consumer bool is False
#
# Sound TRUE certificates (each exact / theorem-backed; NO numeric band anywhere):
#   Z1  empty-after-combine: exact carrier cancellation + θ(1)=0 kills          [trivial]
#   Z2  ±-pair three-term reduction to the EMPTY normal form (Rosengren Eq. 1.12,
#       value-faithful rewrites; empty ⟺ the component IS zero)                  [exact]
#   Z3s character split, ZERO direction: all components zero ⇒ the sum is zero  [trivial]
#   Z4  per-character elliptic interpolation: a SINGLE-character component of
#       v-degree D ≥ 1 vanishing (recursively PROVEN) at D+1 nodes pairwise
#       distinct mod p^ℤ is identically zero (Rosengren Cor. 1.3.5: a nonzero
#       degree-D section has at most D zero classes mod p^ℤ)                    [theorem]
#
# Sound FALSE (NONZERO) certificates — DETECTION ONLY, they can never yield a True:
#   N1  singleton component: a nonzero-coeff monomial × a product of thetas of
#       non-unit canonical args is a nonzero formal series
#   N2  the exact lattice expansion to a FINITE depth exhibits a nonzero coefficient
#       (the depth influences only how often we can say NONZERO instead of UNKNOWN)
#   N3  a node substitution proven NONZERO ⇒ the component is nonzero (substitution
#       is a homomorphism)
#   N4  a character component proven NONZERO ⇒ the sum is nonzero (character
#       independence; affects only the False label, never True)
#
# The CHARACTER of a term in a symbol v is its exact quasi-periodicity datum under
# v ↦ p·v: the degree D_v = Σₐ e_{v,a}² together with the full Rosengren Eq. 1.6
# multiplier monomial μ_v (ℚ*-coefficient included, the v-part dropped — it IS D_v).
# Terms of different (D_v, μ_v) for ANY v lie in different section spaces and are
# linearly independent over ℚ(q,p), so the split is exact in both directions.
#
# COMPLETENESS WALL (diagnosed 2026-07-12 on the rc227 Aₙ (n=3, N=3) residual —
# the genuinely-zero 10-composition frontier the rc227 verify cap sits below):
# the recursion is SOUND but INCOMPLETE at multivariate scale, and the
# incompleteness is NOT a provisioning bug. On that residual (11 terms, ONE joint
# character) every Z4 frame receives its full D+1 pairwise-distinct nodes (the
# substitution path a1→a2→a3→a4→z2→z3→z1→q with D = 9/6/6/6/13/19/22/70; the
# node-shortage branch never fires) — the recursion bottoms out where ALL
# variables are consumed: a nonempty 0-VARIABLE theta-CONSTANT sum (3 terms × 29
# rational-argument thetas) that is GENUINELY ZERO (exact p-expansion identically
# 0 through order 80) by a nontrivial theta-constant identity, and the
# certificate system has NO ZERO certificate for that shape: Z1 needs exact
# carrier cancellation (3 terms survive combine), Z2/Z4 need a live variable,
# N2 only ever proves NONZERO. The honest UNKNOWN → False is the #695
# interpolation wall, sharpened to its root: the wall is the 0-variable LEAF
# certificate gap, not the interpolation step. NO widening (more nodes / deeper
# detection / larger arena) can close it — closing it needs a NEW zero
# certificate for theta-constant sums (a different algorithm). Note the C peer's
# fast False vs the pure path's non-finish at this scale is the SAME verdict at
# different cost: ti_decide short-circuits at the first unproven leaf (~0.7 s);
# the pure three-valued recursion exhaustively evaluates every child of every
# Z4 frame (~10⁹ frames at (3,3)); an early-exit pure mirror of this body
# returns the same verdict in ~14 s.

_ZERO, _NONZERO, _UNKNOWN = "ZERO", "NONZERO", "UNKNOWN"

# The N2 detection-depth cap. SOUNDNESS-IRRELEVANT: detection only ever proves NONZERO
# (an exact nonzero coefficient at a finite order); it never proves ZERO. Chosen so the
# known gap families are detected: a T-term one-character pair family hides its first
# nonzero functional no deeper than ~((T−1)·emax)²/4.
_STRUCT_DETECT_CAP = 80

# ── the Z5 theta-constant-leaf ZERO certificate (rc228) ──────────────────────────────
# The 0-VARIABLE theta-CONSTANT leaf ``Σ c_i ∏ θ(rational; p)`` (all summation variables
# consumed by the Z4 interpolation path) had NO ZERO certificate before rc228: Z1 needs
# exact carrier cancellation (a surviving multi-term sum is not empty), Z2/Z4 need a LIVE
# variable, and N2 only ever proves NONZERO — so a GENUINELY-zero constant leaf declined
# to _UNKNOWN → is_zero false-negatived (the #695 completeness wall, root-caused to this
# leaf on the rc227 Aₙ (3,3) residual, diagnosed 2026-07-12).
#
# Z5 is the SOUND PRIME-LIFT certificate. A theta-constant argument is a rational
# ``ρ = ∏ ρ_ℓ^{v_ℓ}`` (a monomial in the DISTINCT PRIMES the Z4 interpolation substituted
# — unique factorization). Lifting ONE such prime ρ* back to a fresh symbol ``v`` yields a
# LIFTED single-variable ThetaSum ``L(v)`` with the EXACT specialization property
# ``L(v = ρ*) = leaf`` (substituting the integer ρ* back reproduces every argument and
# coefficient identically). Therefore, if the EXACT Weierstrass ±-pair reduction (Z2,
# Rosengren Eq. 1.12 — a value-faithful rewrite proving ``L ≡ 0`` as a function of v)
# closes ``L`` to the empty normal form, then ``leaf = L(ρ*) ≡ 0`` by specialization. This
# is a THEOREM (a specialization of an identically-zero elliptic function is zero), NOT a
# numeric band: Z5 produces ONLY ZERO verdicts, NEVER a NONZERO claim (the reduction never
# certifies nonzero — a False from _pair_reduce_component is "not proven here"). Soundness:
# a genuinely-NONZERO leaf has ``L(ρ*) ≠ 0`` so ``L ≢ 0`` in v, and the SOUND ±-pair
# reduction then never reaches the empty form (never a false ZERO). Fast + terminating:
# every attempt is a bounded three-term reduction (_REDUCE_MAX_PASSES) with NO
# interpolation, NO re-lift, NO _decide_struct recursion — so Z5 cannot loop and adds only
# a bounded constant-factor cost. It CLOSES the class of theta-constant identities that are
# specializations of the addition (three-term) theorem; it does NOT reach a genuinely
# high-kernel-rank leaf (e.g. the Aₙ (3,3) residual, 3 terms × 29 thetas over the four
# primes 2/5/29/71, whose exponent matrices map ℤ²⁹→ℤ⁴ with 25-dim kernels and whose
# non-torsion prime arguments carry no modular/Sturm structure) — that residue stays an
# honest ``is_zero = False`` (the #695 residue, now sharpened to "kernel-rank ≥ 2, no
# ±-pair lift closes it").
_Z5_MAX_PRIMES = 16          # bound the single-prime lift attempts (each is one Z2 pass)
_Z5_SYM = "\x1fz5lift"       # the lift variable — a control-char name that CANNOT collide
                             # with a real elliptic symbol (x/y/p/q/params are identifiers)


def _leaf_prime_set(terms: "List") -> "List[int]":
    """The DISTINCT primes dividing any numerator/denominator of a prefactor coeff OR a
    theta-argument coeff across the 0-variable leaf's terms, sorted ascending. Class-J
    trial-division factoring on the EXACT integers (no float); the ``|x|`` magnitude is a
    Class-K sign branch, never ``abs()``. Bounded by the integers' size (the leaf's
    constants are products of the small interpolation primes)."""
    ps: "set" = set()
    for pref, args in terms:
        for m in [pref] + list(args):
            for x in (m.coeff.numerator, m.coeff.denominator):
                xa = x if x >= 0 else -x                  # Class-K magnitude (no abs())
                d = 2
                while d * d <= xa:
                    while xa % d == 0:
                        ps.add(d)
                        xa //= d
                    d += 1
                if xa > 1:
                    ps.add(xa)
    return sorted(ps)


def _lift_prime_terms(terms: "List", prime_syms: "List[Tuple[int, str]]") -> "List":
    """Lift each ``(prime, sym)`` in ``prime_syms`` to its symbol in EVERY ``EllMonomial``
    coeff (prefactor AND theta args): factor the prime out of the coeff and move its net
    integer valuation onto ``sym``'s exponent. The lift is EXACT — substituting each
    ``sym := prime`` reproduces the input coeff (hence the whole leaf) identically — so a
    proof that the lifted object ``≡ 0`` SPECIALIZES to the leaf ``≡ 0``. No float; the
    prime-adic valuation is exact integer division (a negative numerator divides cleanly:
    ``-p·k`` mod ``p`` is 0, so the sign rides through unchanged, Class-K)."""
    def lift_mono(m: EllMonomial) -> EllMonomial:
        num, den = m.coeff.numerator, m.coeff.denominator
        exps: "Dict[str, int]" = dict(m.exps)
        for prime, sym in prime_syms:
            e = 0
            while num % prime == 0:
                num //= prime
                e += 1
            while den % prime == 0:
                den //= prime
                e -= 1
            if e:
                exps[sym] = exps.get(sym, 0) + e
        return EllMonomial(Q(num, den), exps)
    return [(lift_mono(pref), [lift_mono(a) for a in args]) for pref, args in terms]


def _z5_theta_constant_zero(terms: "List") -> bool:
    """Z5: the SOUND prime-lift ZERO certificate for a 0-VARIABLE theta-CONSTANT leaf.
    Lift each present prime ``ρ`` (bounded) back to the fresh single variable
    :data:`_Z5_SYM`; a lifted object closed to the EMPTY Weierstrass ±-pair normal form
    (:func:`_pair_reduce_component`, Rosengren Eq. 1.12 — a value-faithful rewrite proving
    ``L ≡ 0`` as a function of the lift variable) proves the leaf ``= L(ρ) ≡ 0`` by
    specialization (see the block comment above). Returns ``True`` ONLY on such a proof (a
    genuine ZERO certificate); ``False`` = "not proven by a ±-pair lift" (NEVER a NONZERO
    claim). Terminating: only bounded ±-pair reductions, no interpolation, no recursion.
    The C peer :func:`_is_zero_interpolation_c` mirrors this EXACT single-prime-lift loop
    (reusing a leaf-unused symbol slot as the lift variable)."""
    primes = _leaf_prime_set(terms)
    if not primes:
        return False
    for pr in primes[:_Z5_MAX_PRIMES]:
        lifted = _lift_prime_terms(terms, [(pr, _Z5_SYM)])
        if _pair_reduce_component(lifted, [_Z5_SYM]):
            return True
    return False


def _term_char_v(pref: EllMonomial, args: "List[EllMonomial]", v: str) -> "Tuple[int, Tuple]":
    """The EXACT v-character of one term: ``(D_v, μ_v-key)``.

    Under ``v → p·v`` the term ``κ·v^d·∏ θ(z_a)`` (``z_a`` canonical, p-exp 0) acquires
    the multiplier ``p^d · ∏_a [(−1)^{e_a} p^{−e_a(e_a−1)/2} z_a^{−e_a}] · v^{−D_v}``,
    with ``D_v = Σ e_a²`` (Rosengren Eq. 1.6 per factor; ``e_a`` = the v-exponent of
    ``z_a``). ``μ_v`` is that multiplier WITHOUT the ``v^{−D_v}`` part, kept as an exact
    ``(Q coeff, exponent-monomial)`` key, p-power included."""
    d = pref.exp_of(v)
    D = 0
    coeff = _Q_ONE
    exps: "Dict[str, int]" = {_P: d}
    for z in args:
        e = z.exp_of(v)
        if e == 0:
            continue
        D += e * e
        if e % 2:
            coeff = coeff * Q(-1, 1)
        exps[_P] = exps.get(_P, 0) - (e * (e - 1)) // 2
        # z^{-e}: coefficient part c^{-e}, monomial part exps scaled by -e
        c = z.coeff
        if e > 0:
            for _ in range(e):
                coeff = coeff / c
        else:
            for _ in range(-e):
                coeff = coeff * c
        for s, se in z.exps.items():
            exps[s] = exps.get(s, 0) - e * se
    exps.pop(v, None)                      # the v^{-D} part IS D, tracked separately
    key_exps = tuple(sorted((s, e2) for s, e2 in exps.items() if e2 != 0))
    return D, (coeff.numerator, coeff.denominator, key_exps)


def _joint_char(pref: EllMonomial, args: "List[EllMonomial]", syms: "List[str]") -> "Tuple":
    """The joint character of a term over the ordered symbol list: one ``(v, D_v, μ_v)``
    triple per symbol. Two terms with different joint characters are linearly independent
    over ``ℚ(q,p)`` (character independence), so the partition is exact."""
    out = []
    for v in syms:
        dc = _term_char_v(pref, args, v)
        out.append((v, dc[0], dc[1]))
    return tuple(out)


def _pair_reduce_component(terms: "List", syms: "List[str]") -> bool:
    """Z2 generalized: the exact Weierstrass three-term reduction over the component's
    ACTUAL live variables (the shipped fast path hardcoded x/y). True ONLY on the empty
    normal form (proven zero — every rewrite is a value-faithful instance of Rosengren
    Eq. 1.12). False = "not proven here" (a term outside the clean ±-pair shape, or a
    non-empty normal form) — never a nonzero claim."""
    rterms = []
    for pref, args in terms:
        rec = _recover_pairs(tuple(Theta(a) for a in args))
        if rec is None:
            return False
        rpref, pairs = rec
        rterms.append((pref * rpref, tuple(pairs)))
    work = _combine_rterms(rterms)
    for _ in range(_REDUCE_MAX_PASSES):
        changed = False
        for s in sorted(syms):
            nxt = []
            pass_changed = False
            for pref, pairs in work:
                rw = _three_term_rewrite(list(pairs), pref, s)
                if rw is None:
                    nxt.append((pref, pairs))
                else:
                    nxt.extend(rw)
                    pass_changed = True
            work = _combine_rterms(nxt)
            changed = changed or pass_changed
        if not changed:
            break
    return len(work) == 0


def _lattice_nonzero_upto(terms: "List", w: str, k: int) -> bool:
    """N2 detection: the exact p-expansion of the component to order ``k`` (``w`` = the
    single live variable, or a dummy for the 0-variable case). True iff some coefficient
    is exactly nonzero ⇒ the component is proven NONZERO. NEVER used to prove zero (a
    truncation can only ever witness a NONZERO coefficient exactly)."""
    total: "Dict" = {}
    for pref, args in terms:
        term = {0: {pref.exps.get(w, 0): pref.coeff}}
        for a in args:
            term = _struct_pexp_mul(term, _struct_theta_p(a.coeff, a.exps.get(w, 0), k), k)
        for pp, lp in term.items():
            dst = total.setdefault(pp, {})
            for kk, vv in lp.items():
                dst[kk] = dst.get(kk, _Q_ZERO) + vv
    for lp in total.values():
        for vv in lp.values():
            if vv != _Q_ZERO:
                return True
    return False


def _node_key(m: EllMonomial) -> "Tuple":
    """The exact node identity key (coefficient + exponent monomial) — two nodes with
    the same key are the SAME point of ℂ*/p^ℤ (canonical p-exp-0 monomials)."""
    return (m.coeff.numerator, m.coeff.denominator, tuple(sorted(m.exps.items())))


def _pick_nodes(terms: "List", v: str, D: int, offset: int
                ) -> "Tuple[List[EllMonomial], int]":
    """The D+1 interpolation nodes, pairwise DISTINCT (canonical p-exp-0 monomials, so
    exact-key distinctness = distinctness mod p^ℤ). rc210 defect-D4 fix: the augment
    primes are deduplicated against the zero-node constants too (a θ(x/5) zero node IS
    the constant 5 — appending the prime 5 again would double-count one node and
    under-count the interpolation). Returns ``(nodes[:D+1], offset+consumed)``."""
    nodes: "List[EllMonomial]" = []
    seen: "set" = set()
    for nd in _struct_zero_nodes(terms, v):
        kk = _node_key(nd)
        if kk not in seen:
            seen.add(kk)
            nodes.append(nd)
    used = 0
    npr = len(_STRUCT_PRIMES)
    guard = 0
    while len(nodes) < D + 1 and guard < 4 * npr:
        cand = EllMonomial(Q(_STRUCT_PRIMES[(offset + used) % npr], 1))
        used += 1
        guard += 1
        kk = _node_key(cand)
        if kk in seen:
            continue
        seen.add(kk)
        nodes.append(cand)
    return nodes[:D + 1], offset + used


def _decide_struct(terms: "List", offset: int = 0, depth: int = 0) -> str:
    """The sound three-valued decision on a cleared-numerator term list
    ``[(EllMonomial prefactor, [EllMonomial theta-args])]`` → ``_ZERO`` / ``_NONZERO`` /
    ``_UNKNOWN``. The DEFAULT is decline: ``_ZERO`` is returned ONLY through the Z1/Z2/
    Z3s/Z4 certificates (see the block comment above); there is NO numeric band on the
    True side. ``offset`` threads the globally-distinct augment-prime cursor down the
    interpolation path (spurious θ(1) collision guard)."""
    terms = _struct_combine(terms)
    if not terms:
        return _ZERO                                           # Z1
    syms = _struct_variables(terms)

    # ---- exact joint-character split (Z3s: the True direction is trivially sound) ----
    comps: "Dict[Tuple, List]" = {}
    for pref, args in terms:
        comps.setdefault(_joint_char(pref, args, sorted(syms)), []).append((pref, args))
    if len(comps) > 1:
        verdicts = [_decide_struct(c, offset, depth) for c in comps.values()]
        if all(v == _ZERO for v in verdicts):
            return _ZERO
        if any(v == _NONZERO for v in verdicts):
            return _NONZERO                                    # N4 (character independence)
        return _UNKNOWN

    # ---- single joint character ----
    # Strip symbols of theta-degree 0 (same character ⇒ same prefactor exponent):
    # factor v^d out of every prefactor; v disappears from the object.
    live: "List[str]" = []
    for v in sorted(syms):
        D0 = max(sum(a.exp_of(v) ** 2 for a in args) for _pref, args in terms)
        if D0 == 0:
            dvals = {pref.exp_of(v) for pref, _args in terms}
            if len(dvals) != 1:
                raise AssertionError("joint-char split broken: unequal d_v in one class")
            terms = [(_struct_subst(pref, v, EllMonomial.one()), args)
                     for pref, args in terms]
        else:
            live.append(v)

    if len(terms) == 1:
        return _NONZERO                                        # N1

    if not live:
        # 0-variable: a sum of θ(rational-constant) products. Combine already merged
        # carrier-equal terms. Z5 (rc228): the SOUND prime-lift ZERO certificate — lift a
        # constant prime back to an elliptic variable and close the lift by the exact
        # Weierstrass ±-pair reduction; a proof there SPECIALIZES to the leaf ≡ 0.
        if _z5_theta_constant_zero(terms):
            return _ZERO                                       # Z5
        # else a surviving multi-term theta-constant sum is decided NONZERO only by exact
        # finite detection, else HONESTLY declined.
        if _lattice_nonzero_upto(terms, "__none__", min(_STRUCT_DETECT_CAP, 24)):
            return _NONZERO                                    # N2
        return _UNKNOWN                                        # honest decline

    if len(live) == 1:
        w = live[0]
        if _pair_reduce_component(terms, [w]):
            return _ZERO                                       # Z2
        # last-variable interpolation (Z4 still valid at one variable; the children are
        # 0-variable objects that may empty-combine to a proven ZERO)
        D = max(sum(a.exp_of(w) ** 2 for a in args) for _pref, args in terms)
        nodes, child_offset = _pick_nodes(terms, w, D, offset)
        if len(nodes) == D + 1:
            sub = [_decide_struct([(_struct_subst(pref, w, nd),
                                    [_struct_subst(a, w, nd) for a in args])
                                   for pref, args in terms], child_offset, depth + 1)
                   for nd in nodes]
            if all(v == _ZERO for v in sub):
                return _ZERO                                   # Z4
            if any(v == _NONZERO for v in sub):
                return _NONZERO                                # N3
        # exact detection (N2): band-informed + term-count-informed depth (Class-K
        # sign branches, never abs()).
        emax = 1
        for _p, args in terms:
            for a in args:
                e = a.exp_of(w)
                if e == 0:
                    continue
                mag = e if e >= 0 else -e
                if mag > emax:
                    emax = mag
        band = max(D - 1, 0) + _STRUCT_MARGIN
        kdet = min(_STRUCT_DETECT_CAP,
                   max(band, ((len(terms) - 1) * emax) ** 2 // 4 + _STRUCT_MARGIN))
        if _lattice_nonzero_upto(terms, w, kdet):
            return _NONZERO                                    # N2
        return _UNKNOWN

    # ---- multivariate single character: per-character interpolation (Z4) ----
    if _pair_reduce_component(terms, live):
        return _ZERO                                           # Z2
    Dv = {v: max(sum(a.exp_of(v) ** 2 for a in args) for _pref, args in terms)
          for v in live}
    v = min(live, key=lambda s: (Dv[s], s))
    D = Dv[v]
    nodes, child_offset = _pick_nodes(terms, v, D, offset)
    if len(nodes) < D + 1:
        return _UNKNOWN
    sub = [_decide_struct([(_struct_subst(pref, v, nd),
                            [_struct_subst(a, v, nd) for a in args])
                           for pref, args in terms], child_offset, depth + 1)
           for nd in nodes]
    if all(vv == _ZERO for vv in sub):
        return _ZERO                                           # Z4
    if any(vv == _NONZERO for vv in sub):
        return _NONZERO                                        # N3
    return _UNKNOWN


def _decide_thetasum(ts: "ThetaSum", use_fastpath: bool = True) -> str:
    """The three-valued sound decision on a ``ThetaSum`` (cleared numerator) — the
    internal diagnostic / test surface behind :attr:`ThetaSum.is_zero` (which is
    ``_decide_thetasum(self) == _ZERO`` on the pure path). ``use_fastpath=False``
    skips the ±-pair fast path so the certificate recursion alone is exercised."""
    if not ts.terms:
        return _ZERO
    import sys as _sys
    old = _sys.getrecursionlimit()
    if old < 100000:                                     # srmech's Q gcd recurses on big ints
        _sys.setrecursionlimit(100000)
    try:
        if use_fastpath:
            classes: "Dict" = {}
            for pref, thetas in ts.terms:
                classes.setdefault(_quasi_period_class_key(thetas), []).append(
                    (pref, thetas))
            if all(_class_is_zero(m) for m in classes.values()):
                return _ZERO
        term_list = [(pref, [t.arg for t in thetas]) for pref, thetas in ts.terms]
        return _decide_struct(term_list)
    finally:
        _sys.setrecursionlimit(old)

def _net_period_multiplier_exps(thetas: "Tuple[Theta, ...]") -> "Tuple[Tuple[str, int], ...]":
    """The QUASI-PERIODICITY CLASS key of a theta-product: the net multiplier monomial
    the product ``∏ θ(z_i; p)`` acquires under the period shifts ``x ↦ p·x`` AND
    ``y ↦ p·y`` (Rosengren Eq. 1.6, applied through
    :meth:`~srmech.amsc.ellbase.Theta.canonicalize`). Two theta-products of DIFFERENT
    key transform by different multipliers under the period lattice, hence are linearly
    independent over ``ℚ(q,p)``. Returned as a sorted exponent tuple (the dict key),
    coefficient-free (a ``ℚ`` scalar multiplier never breaks the independence; only the
    symbol-exponent monomial classifies). EXACT — integer exponents only, no float."""
    net = EllMonomial.one()
    for sym in (_X, _Y):
        # Substitute the chosen summation symbol s ↦ p·s in every theta argument and
        # read the EllMonomial prefactor the canonicalization emits — that prefactor
        # IS the quasi-periodicity multiplier for this period direction.
        for t in thetas:
            shifted_arg = t.arg * EllMonomial.symbol(_P, t.arg.exp_of(sym))
            if shifted_arg.is_zero:
                continue
            pref, _t0 = Theta(shifted_arg).canonicalize()
            net = net * pref
    # classify by the exponent monomial only (the ℚ coefficient is independence-blind).
    # NOTE: this returns the FULL multiplier monomial, INCLUDING the nome ``p`` (and, on a
    # shifted carrier, the base ``q``) and any elliptic-parameter exponents. That full
    # monomial is what :func:`~srmech.amsc.carrier_spectrum._block_of_thetas` needs — its
    # ``p``-coordinate IS the Class-L *p-character* block label (carrier_spectrum strips only
    # ``q``). The ``is_zero`` FAST-PATH bucketing must NOT split on those unit coordinates —
    # it uses :func:`_quasi_period_class_key` (below), which keeps only the ``x``/``y``
    # exponents. Keep this function's return the FULL monomial; do NOT unit-strip it here.
    return tuple(sorted(net.exps.items()))


def _quasi_period_class_key(thetas: "Tuple[Theta, ...]"
                            ) -> "Tuple[Tuple[str, int], ...]":
    """The ``is_zero`` FAST-PATH quasi-periodicity-CLASS key: the net period-multiplier's
    SUMMATION-VARIABLE (``x``, ``y``) exponents ONLY. It is :func:`_net_period_multiplier_exps`
    with every UNIT-symbol exponent dropped.

    Under the period shifts ``x ↦ p·x`` and ``y ↦ p·y`` a theta-product ``∏ θ(z_i; p)``
    acquires the Rosengren Eq. 1.6 multiplier ``(−1)ᵏ·p^{−k(k−1)/2}·z₀⁻ᵏ``. The genuine
    quasi-periodicity CHARACTER — the datum that decides linear (in)dependence over the
    coefficient field — is how the multiplier scales in the period-lattice variables ``x``
    and ``y``. Every OTHER symbol is a UNIT in that field and is therefore
    INDEPENDENCE-BLIND: the nome ``p`` (its ``p^{−k(k−1)/2}`` power is invertible — the very
    ``ℚ(q,p)`` scalar the docstring above calls independence-blind), the base ``q`` (a unit
    that only appears after a :meth:`ThetaSum.shift_x` / :meth:`ThetaSum.shift_y`), and the
    elliptic PARAMETERS ``a, b, c, …`` (constants w.r.t. the shift). Their exponents ride in
    ``net.exps`` only as an artefact of the argument monomial, so including them SPLITS one
    genuine character across buckets (task #694 anomaly A-1 — e.g. two reducible ±-pair
    products of the SAME ``x``-character but different ``p``/parameter power land in different
    buckets, so the fast-path three-term reduction never sees them together).

    Dropping the unit exponents restores the genuine grouping. Keeping ONLY ``x``/``y`` is
    the coarsest CORRECT partition (soundness is not at stake — the key is a fast-path
    bucketing only; :func:`_class_is_zero` proves a bucket ``≡0`` EXACTLY and any miss defers
    to the complete :meth:`ThetaSum._is_zero_interpolation`, so merging or splitting buckets
    changes only the PATH, never the VERDICT). EXACT — integer exponents only, no float."""
    return tuple((s, e) for (s, e) in _net_period_multiplier_exps(thetas)
                 if s in (_X, _Y))


def _canonical_theta_key(thetas: "Tuple[Theta, ...]"
                         ) -> "Tuple[Tuple[Tuple[str, int], ...], ...]":
    """The CANONICAL theta-multiset key of a theta-product (after
    :meth:`~srmech.amsc.ellbase.Theta.canonicalize` on each factor): a sorted tuple of
    canonical theta-argument exponent tuples. Two terms with the same key are the SAME
    product up to a monomial prefactor → they combine exactly in the carrier (their
    prefactor coefficients add). The canonicalization prefactors are folded by the
    caller, so the key is the orientation-fixed, p-exponent-0 theta-argument multiset."""
    keys: "List[Tuple[Tuple[str, int], ...]]" = []
    for t in thetas:
        _pref, t0 = t.canonicalize()
        keys.append(tuple(sorted(t0.arg.exps.items())))
    keys.sort()
    return tuple(keys)


def _canonicalize_term(pref: EllMonomial, thetas: "Tuple[Theta, ...]") -> _Term:
    """Fold each theta-factor's canonicalization prefactor into the term prefactor and
    canonicalize the theta multiset (orientation-fixed, p-exponent 0, sorted). Returns
    the canonical ``(prefactor, sorted-canonical-thetas)`` term — the exact
    representative used for carrier-equality combination."""
    p = pref
    canon: "List[Theta]" = []
    for t in thetas:
        pr, t0 = t.canonicalize()
        p = p * pr
        canon.append(t0)
    canon.sort(key=lambda th: th.arg._sort_key())
    return p, tuple(canon)


class ThetaSum:
    """A numpy-free EXACT cleared rational theta-function: a ``ℚ(q,p)``-linear SUM of
    theta-products over a single theta-product denominator — the ADDITIVE layer over
    :class:`~srmech.amsc.ellbase.Theta` / :class:`~srmech.amsc.ellbase.EllRatio` that
    GENUINE elliptic creative telescoping needs (theta-quotients are not additively
    closed). Immutable.

        numerator   = Σ_i (prefactor_i · ∏ thetas_i)        [a list of canonical terms]
        denominator = den_prefactor · ∏ den_thetas          [a single theta-product]

    Every coefficient is an exact ``Q`` (folded into the term ``EllMonomial`` prefactor,
    sign = **Class-K**, never ``abs()``); every theta is canonicalized on construction.
    The carrier is the peer of ``EllRatio`` / ``QMat`` / ``TriPoly`` — a CARRIER, not a
    ToolEntry (invisible to the tool-schema / Rosetta coverage walks: it exposes only a
    class + ``_``-prefixed helpers, no public module-level function).

    The load-bearing method is :meth:`is_zero` — the EXACT degree-bound decision (the
    rc61 / §76 no-hallucination standard: quasi-periodicity grouping + the Fundamental
    Theorem of Elliptic Functions degree bound; NEVER a convergence threshold). See the
    module docstring for the two MPM-verified theorems and the exactness proof-sketch.
    """

    __slots__ = ("_terms", "_den_pref", "_den_thetas")

    def __init__(self,
                 terms: "Iterable[Tuple[object, EllMonomial, Iterable[Theta]]]" = (),
                 den_prefactor: "EllMonomial | None" = None,
                 den_thetas: "Iterable[Theta]" = ()) -> None:
        """Build from explicit numerator ``terms`` (each ``(coeff, prefactor, thetas)``
        — ``coeff`` an exact scalar folded into the prefactor) over a denominator
        ``den_prefactor · ∏ den_thetas``. The denominator must be nonzero. Use
        :meth:`from_ellratio` / :meth:`zero` / :meth:`one` for the ergonomic
        constructors."""
        dpref = EllMonomial.one() if den_prefactor is None else den_prefactor
        if not isinstance(dpref, EllMonomial):
            raise TypeError("ThetaSum den_prefactor must be an EllMonomial")
        if dpref.is_zero:
            raise ZeroDivisionError("ThetaSum: the denominator prefactor is zero")
        dthetas: "List[Theta]" = []
        dp = dpref
        for t in den_thetas:
            if not isinstance(t, Theta):
                raise TypeError("ThetaSum denominator factors must be Theta")
            pr, t0 = t.canonicalize()
            dp = dp * pr
            dthetas.append(t0)
        dthetas.sort(key=lambda th: th.arg._sort_key())
        self._den_pref = dp
        self._den_thetas: "Tuple[Theta, ...]" = tuple(dthetas)
        built: "List[_Term]" = []
        for coeff, pref, thetas in terms:
            c = _coerce_q(coeff)
            if c is None:
                raise TypeError("ThetaSum term coeff must be exact-rational (no float)")
            if not isinstance(pref, EllMonomial):
                raise TypeError("ThetaSum term prefactor must be an EllMonomial")
            p0 = pref * EllMonomial.scalar(c)
            if p0.is_zero:
                continue
            built.append(_canonicalize_term(p0, tuple(thetas)))
        self._terms = self._combine(built)

    # ── internal: exact like-term combination (carrier equality) ─────────────
    @staticmethod
    def _combine(terms: "List[_Term]") -> "Tuple[_Term, ...]":
        """Combine LIKE terms — same canonical theta-multiset AND same prefactor
        symbol-monomial — by adding their exact ``Q`` scalar coefficients (the exact
        carrier-equality step). Two terms with the same thetas but DIFFERENT prefactor
        monomials (e.g. ``a²bc·θ… + a²b²·θ…``) are NOT a single monomial × θ, so they stay
        SEPARATE. Drops terms whose coefficient cancels to 0. Order-stable, then sorted."""
        # key = (theta-multiset, prefactor-symbol-monomial); value = (Q-sum, mono, thetas)
        groups: "Dict[Tuple, Tuple[Q, EllMonomial, Tuple[Theta, ...]]]" = {}
        order: "List[Tuple]" = []
        for pref, thetas in terms:
            if pref.is_zero:
                continue
            theta_key = tuple(sorted(t.arg._sort_key() for t in thetas))
            key = (theta_key, tuple(sorted(pref.exps.items())))
            if key in groups:
                qc, mono, th = groups[key]
                groups[key] = (qc + pref.coeff, mono, th)
            else:
                groups[key] = (pref.coeff, EllMonomial(_Q_ONE, pref.exps), thetas)
                order.append(key)
        out: "List[_Term]" = []
        for key in order:
            qc, mono, thetas = groups[key]
            if qc != _Q_ZERO:
                out.append((mono * EllMonomial.scalar(qc), thetas))
        out.sort(key=lambda term: tuple(t.arg._sort_key() for t in term[1]))
        return tuple(out)

    # ── ergonomic constructors ───────────────────────────────────────────────
    @classmethod
    def zero(cls) -> "ThetaSum":
        """The zero theta-sum ``0`` (empty numerator, unit denominator)."""
        return cls(terms=(), den_prefactor=EllMonomial.one(), den_thetas=())

    @classmethod
    def one(cls) -> "ThetaSum":
        """The unit theta-sum ``1`` (a single unit-prefactor, theta-free term)."""
        return cls(terms=((Q(1, 1), EllMonomial.one(), ()),),
                   den_prefactor=EllMonomial.one(), den_thetas=())

    @classmethod
    def from_ellratio(cls, r: EllRatio) -> "ThetaSum":
        """Lift a single-term :class:`~srmech.amsc.ellbase.EllRatio`
        ``prefactor · ∏(num θ) / ∏(den θ)`` to the equivalent ``ThetaSum`` (one
        numerator term over the den theta-product). The zero ratio → :meth:`zero`."""
        if not isinstance(r, EllRatio):
            raise TypeError("ThetaSum.from_ellratio: r must be an EllRatio")
        if r.is_zero:
            return cls.zero()
        return cls(terms=((Q(1, 1), r.prefactor, r.num),),
                   den_prefactor=EllMonomial.one(), den_thetas=r.den)

    # ── accessors ────────────────────────────────────────────────────────────
    @property
    def terms(self) -> "Tuple[_Term, ...]":
        """The canonical numerator terms, each ``(EllMonomial prefactor, tuple Theta)``
        (the ``Q`` coeff is folded into the prefactor; sign = Class-K)."""
        return self._terms

    @property
    def den_prefactor(self) -> EllMonomial:
        """The denominator's exact ``EllMonomial`` prefactor."""
        return self._den_pref

    @property
    def den_thetas(self) -> "Tuple[Theta, ...]":
        """The denominator's canonical theta multiset (sorted)."""
        return self._den_thetas

    @property
    def is_unit(self) -> bool:
        """True iff this is exactly ``1`` (one unit-prefactor theta-free numerator term,
        unit denominator)."""
        return (len(self._terms) == 1 and self._terms[0][0].is_unit
                and not self._terms[0][1] and self._den_pref.is_unit
                and not self._den_thetas)

    @property
    def weight(self) -> Q:
        """The modular WEIGHT on the operand ladder — **0** (exact
        :class:`~srmech.amsc.q.Q`). ``ThetaSum`` is the additive carrier of a
        BALANCED (genuine-elliptic) theta rational function: the creative-
        telescoping residual it holds is a weight-0 elliptic object on
        ``ℂ*/⟨p⟩`` (a sum of balanced theta-quotients over a common balanced
        denominator), so its grade is 0 — like every carrier below
        :class:`srmech.amsc.unary_theta.UnaryTheta`, the ladder before the weight
        axis was introduced. Constant (the carrier represents balanced data); the
        weight axis is :attr:`srmech.amsc.unary_theta.UnaryTheta.weight`."""
        return Q(0, 1)

    # ── additive algebra (common denominator → sum / subtract numerators) ────
    def _num_over(self, target_pref: EllMonomial,
                  target_thetas: "Tuple[Theta, ...]") -> "List[_Term]":
        """Re-express this carrier's numerator over a COMMON denominator
        ``target_pref · ∏ target_thetas`` (a superset of every term's needs): multiply
        each numerator term by the extra denominator factors not already in self's
        denominator. Returns the re-based term list (un-combined)."""
        # the common denominator must contain self's denominator; the surplus factors
        # (common ∖ self.den) multiply self's numerator.
        extra_pref = target_pref / self._den_pref
        extra_thetas = list(_multiset_diff(target_thetas, self._den_thetas))
        rebased: "List[_Term]" = []
        for pref, thetas in self._terms:
            rebased.append(_canonicalize_term(pref * extra_pref,
                                              tuple(thetas) + tuple(extra_thetas)))
        return rebased

    def _common_denominator(self, other: "ThetaSum"
                            ) -> "Tuple[EllMonomial, Tuple[Theta, ...]]":
        """The least common denominator of ``self`` and ``other``: the prefactor product
        and the theta-multiset UNION (max multiplicity per canonical theta). Exact."""
        pref = self._den_pref * other._den_pref
        union = _multiset_union(self._den_thetas, other._den_thetas)
        return pref, union

    def __add__(self, other) -> "ThetaSum":
        if isinstance(other, ThetaSum):
            dpref, dthetas = self._common_denominator(other)
            num = self._num_over(dpref, dthetas) + other._num_over(dpref, dthetas)
            return ThetaSum._wrap(ThetaSum._combine(num), dpref, dthetas)
        c = _coerce_q(other)
        if c is not None:
            return self + ThetaSum.one()._scaled(c)
        return NotImplemented

    __radd__ = __add__

    def __neg__(self) -> "ThetaSum":
        neg = [(pref * EllMonomial.scalar(Q(-1, 1)), thetas)
               for pref, thetas in self._terms]
        return ThetaSum._wrap(tuple(neg), self._den_pref, self._den_thetas)

    def __sub__(self, other) -> "ThetaSum":
        if isinstance(other, ThetaSum):
            return self + (-other)
        c = _coerce_q(other)
        if c is not None:
            return self + ThetaSum.one()._scaled(-c)
        return NotImplemented

    def __rsub__(self, other) -> "ThetaSum":
        c = _coerce_q(other)
        if c is not None:
            return ThetaSum.one()._scaled(c) + (-self)
        return NotImplemented

    def _scaled(self, c: Q) -> "ThetaSum":
        """Exact scalar-``Q`` multiply (folds into every term prefactor)."""
        if c == _Q_ZERO:
            return ThetaSum._wrap((), self._den_pref, self._den_thetas)
        scaled = [(pref * EllMonomial.scalar(c), thetas)
                  for pref, thetas in self._terms]
        return ThetaSum._wrap(tuple(scaled), self._den_pref, self._den_thetas)

    def scalar_mul(self, coeff) -> "ThetaSum":
        """Multiply by an exact scalar (``Q`` / int / ``(num, den)`` / ``Fraction``)."""
        c = _coerce_q(coeff)
        if c is None:
            raise TypeError("ThetaSum.scalar_mul: coeff must be exact-rational (no float)")
        return self._scaled(c)

    def __mul__(self, other) -> "ThetaSum":
        if isinstance(other, ThetaSum):
            num: "List[_Term]" = []
            for pa, ta in self._terms:
                for pb, tb in other._terms:
                    num.append(_canonicalize_term(pa * pb, tuple(ta) + tuple(tb)))
            dpref = self._den_pref * other._den_pref
            dthetas = tuple(self._den_thetas) + tuple(other._den_thetas)
            # canonicalize the product denominator (fold prefactors)
            dp, dth = _canonicalize_term(dpref, dthetas)
            num = [(pref / dp, thetas) for pref, thetas in num] if not dp.is_unit else num
            return ThetaSum._wrap(ThetaSum._combine(num), EllMonomial.one(), dth)
        c = _coerce_q(other)
        if c is not None:
            return self._scaled(c)
        if isinstance(other, EllMonomial):
            scaled = [(pref * other, thetas) for pref, thetas in self._terms]
            return ThetaSum._wrap(ThetaSum._combine(list(scaled)),
                                  self._den_pref, self._den_thetas)
        return NotImplemented

    __rmul__ = __mul__

    # ── the two summation shifts (σ_x : x↦qx ; σ_y : y↦qy) ───────────────────
    def _shift(self, sym: str) -> "ThetaSum":
        """Substitute the summation symbol ``sym ↦ q·sym`` in the prefactor and every
        theta argument (numerator AND denominator) — the elliptic summation shift on a
        chosen variable. Generalises rc60's :meth:`EllRatio._shift` (which shifts ``x``
        only) to shift either summation symbol. Re-canonicalizes."""
        qsym = "q"

        def sm(m: EllMonomial) -> EllMonomial:
            return m * EllMonomial.symbol(qsym, m.exp_of(sym))

        terms = [(sm(pref), tuple(Theta(sm(t.arg)) for t in thetas))
                 for pref, thetas in self._terms]
        terms = [_canonicalize_term(p, th) for p, th in terms]
        den_pref = sm(self._den_pref)
        den_thetas = tuple(Theta(sm(t.arg)) for t in self._den_thetas)
        return ThetaSum(terms=[(Q(1, 1), p, th) for p, th in terms],
                        den_prefactor=den_pref, den_thetas=den_thetas)

    def shift_x(self) -> "ThetaSum":
        """The summation shift ``σ_x`` on the n-variable (``n ↦ n+1`` / ``x ↦ q·x``)."""
        return self._shift(_X)

    def shift_y(self) -> "ThetaSum":
        """The summation shift ``σ_y`` on the k-variable (``k ↦ k+1`` / ``y ↦ q·y``)."""
        return self._shift(_Y)

    # ── equality / zero (the load-bearing EXACT decision; NO eval) ───────────
    @property
    def is_zero(self) -> bool:
        """Decide ``self == 0`` by a SOUND-TRUE-ONLY certificate architecture (rc210):
        ``True`` ⟺ the cleared numerator is PROVEN identically zero by an exact /
        theorem-backed certificate; ``False`` = "not proven" (a proven-nonzero object
        or an honest decline). NEVER a convergence threshold, NEVER a numerically-
        witnessed eval, and — the rc210 stop-the-line fix — NEVER a numeric p-order
        band on the True side (the pre-rc210 "complete" band/mixed-character decision
        certified provably-NONZERO objects as zero).

        The True-side certificates (see :func:`_decide_struct`):

        (1) CLEAR → the denominator theta-product is a nonzero elliptic function, so
        ``self == 0 ⟺ numerator ≡ 0``; the empty / fully-cancelled numerator is
        ``≡ 0`` with no work [Z1]. (2) the ±-pair FAST PATH: group by quasi-periodicity
        class (Rosengren Eq. 1.6 via :meth:`~srmech.amsc.ellbase.Theta.canonicalize`)
        and reduce each class by the EXACT Weierstrass three-term relation (Rosengren
        §1.4 Eq. 1.12, MPM-verified — module docstring) to a canonical additive normal
        form; every class empty ⇒ proven zero [Z2]. (3) the CERTIFICATE RECURSION:
        split by the exact per-symbol character ``(D_v, μ_v)`` (all components proven
        zero ⇒ zero [Z3s]), retry the three-term reduction over the component's actual
        variables [Z2], and interpolate one variable at ``D_v+1`` pairwise-distinct
        nodes of ℂ*/p^ℤ — a degree-``D_v`` section vanishing (recursively PROVEN) at
        ``D_v+1`` distinct points is identically zero (Rosengren Cor. 1.3.5) [Z4].
        A shape none of the certificates prove is HONESTLY reported False — the
        no-hallucination standard: ``is_zero`` never asserts a theorem it cannot back.

        The decision DISPATCHES to the native ``srmech_thetasum_is_zero_interpolation``
        C peer when loaded — rebuilt in rc210 as the 1:1 mirror of the SAME certificate
        recursion (its bool equals the pure bool; a mirror bug is caught by the
        committed corpus-parity suite), with the ±-pair ``srmech_thetasum_is_zero``
        peer as a sound-True fast path — otherwise the pure-Python
        :meth:`_is_zero_py` body decides (the parity oracle)."""
        if not self._terms:
            return True
        # The structural-certificate C peer (``srmech_thetasum_is_zero_interpolation``,
        # rebuilt rc210) mirrors the pure :meth:`_is_zero_interpolation` bool 1:1 —
        # True ⟺ certificate-proven, False = not proven — so its verdict is used in
        # both directions (parity is enforced by the committed corpus suite, and a
        # False is never a nonzero CLAIM, just "no proof"). It returns ``None`` only
        # when absent OR when it declines (SRMECH_ERR_OVERFLOW: the caller arena /
        # coeff cap outgrown), in which case we fall through to the complete pure path
        # below. The rc103 CHIRALITY-PRESERVING parallel peer is OPT-IN (env
        # ``SRMECH_THETASUM_PARALLEL_ISZERO``): it returns the BYTE-FOR-BYTE same
        # verdict as the sequential peer, so the default dispatch is correct either
        # way (parallel → sequential → pure).
        import os as _os
        _par = _os.environ.get("SRMECH_THETASUM_PARALLEL_ISZERO", "") not in (
            "", "0", "false", "False", "no", "off")
        ci = self._is_zero_interpolation_c(parallel=_par)
        if ci is not None:
            return ci
        # No complete peer (or it declined): the native ±-pair peer is SOUND (a ``True``
        # is a genuine proof) but not COMPLETE — trust a native ``True`` as a fast path,
        # otherwise the pure :meth:`_is_zero_py` (FAST ±-pair stage + structural-
        # interpolation COMPLETION) is the complete decision.
        if self._is_zero_c() is True:
            return True
        return self._is_zero_py()

    def _is_zero_py(self) -> bool:
        """The pure-Python ``is_zero`` decision (the parity oracle for the C peer): a
        TWO-STAGE sound-True-only decision. (FAST PATH) the quasi-periodicity grouping +
        exact Weierstrass three-term reduction — a proved ``≡0`` here is a genuine
        certificate and is returned immediately; a class it cannot reduce means ONLY
        "the fast path did not prove it". (COMPLETION) the three-valued CERTIFICATE
        RECURSION (:meth:`_is_zero_interpolation` → :func:`_decide_struct`): the exact
        per-symbol character split + the generalized ±-pair reduction + per-character
        elliptic interpolation, ``True`` only on a proof [Z1/Z2/Z3s/Z4], honest
        ``False`` otherwise. See :meth:`is_zero` for the theorems + the rc210
        soundness rebuild."""
        if not self._terms:
            return True
        # FAST PATH — the ±-pair three-term reduction (a proved ≡0 is SOUND). Partition
        # by quasi-periodicity class; a class it cannot reduce returns False, which here
        # means ONLY "the fast path did not prove it".
        classes: "Dict[Tuple, List[_Term]]" = {}
        for pref, thetas in self._terms:
            key = _quasi_period_class_key(thetas)
            classes.setdefault(key, []).append((pref, thetas))
        if all(_class_is_zero(members) for members in classes.values()):
            return True
        # COMPLETION — the sound certificate recursion decides the whole numerator
        # (True only on a Z1/Z2/Z3s/Z4 certificate; honest False otherwise).
        return self._is_zero_interpolation()

    def _is_zero_interpolation(self) -> bool:
        """The SOUND structural completion of :meth:`is_zero` (rc210 rebuild) — the
        consumer bool of the three-valued certificate recursion :func:`_decide_struct`:
        ``True`` ⟺ the cleared numerator is CERTIFICATE-PROVEN identically zero
        (Z1 exact cancellation / Z2 Weierstrass ±-pair reduction to the empty normal
        form, Rosengren Eq. 1.12 / Z3s all character components proven zero / Z4
        per-character elliptic interpolation at ``D_v+1`` pairwise-distinct nodes,
        Rosengren Cor. 1.3.5); ``False`` = "not proven" (a proven-NONZERO object OR an
        honest decline — the two are deliberately indistinguishable to the consumer:
        the contract is sound-True-only). There is NO numeric p-order band anywhere on
        the True side — the pre-rc210 band/mixed-character decision certified genuinely
        NONZERO objects as zero (defects D1/D2; see the ``_decide_struct`` block
        comment). Exact-``ℚ``, no q-grid, no float; the pure parity oracle for the
        native ``srmech_thetasum_is_zero_interpolation`` peer (rebuilt in rc210 as the
        1:1 mirror of this certificate recursion's bool)."""
        if not self._terms:
            return True
        import sys as _sys
        _old = _sys.getrecursionlimit()
        if _old < 100000:                                    # srmech's Q gcd recurses on big ints
            _sys.setrecursionlimit(100000)
        try:
            term_list = [(pref, [t.arg for t in thetas]) for (pref, thetas) in self._terms]
            return _decide_struct(term_list) == _ZERO
        finally:
            _sys.setrecursionlimit(_old)

    def _is_zero_c(self) -> "bool | None":
        """Dispatch the ``is_zero`` decision to the native ``srmech_thetasum_is_zero`` C
        peer → the bool verdict, or ``None`` when the native symbols are absent (the
        caller falls to :meth:`_is_zero_py`). The cleared numerator terms are marshalled
        over an interned symbol table (the distinct symbols across every term prefactor +
        canonical theta argument, sorted by NAME so the C dense exponent vector
        reproduces the :meth:`~srmech.amsc.ellbase.EllMonomial._sort_key` tuple order)."""
        if not _nat.has_native_thetasum():
            return None
        # the interned symbol universe = every symbol on a prefactor or a theta arg.
        syms: "set" = set()
        for pref, thetas in self._terms:
            syms.update(pref.exps.keys())
            for t in thetas:
                syms.update(t.arg.exps.keys())
        sym_list = sorted(syms)
        idx = {s: i for i, s in enumerate(sym_list)}
        n_syms = len(sym_list)

        def row(m: EllMonomial) -> "List[int]":
            r = [0] * n_syms
            for s, e in m.exps.items():
                r[idx[s]] = e
            return r

        monomials: "List[Tuple[int, int, List[int]]]" = []
        term_nthetas: "List[int]" = []
        for pref, thetas in self._terms:
            monomials.append((pref.coeff.numerator, pref.coeff.denominator, row(pref)))
            for t in thetas:
                a = t.arg
                monomials.append((a.coeff.numerator, a.coeff.denominator, row(a)))
            term_nthetas.append(len(thetas))
        try:
            return _nat.thetasum_is_zero_c(
                n_syms, idx.get(_X, -1), idx.get(_Y, -1), idx.get(_P, -1),
                term_nthetas, monomials)
        except (RuntimeError, OverflowError, ValueError):
            # The native peer DECLINED (e.g. SRMECH_ERR_OVERFLOW when a large /
            # multivariate cleared certificate outgrows the caller-arena's provisioned
            # bounds). The C peer is an OPTIMIZATION, never the sole authority — fall
            # back to the COMPLETE pure-Python decision (:meth:`_is_zero_py`, the parity
            # oracle). This keeps ``is_zero`` a TOTAL function: a native size-guard trip
            # never crashes the decision, it degrades to the exact pure path.
            return None

    def _is_zero_c_marshal(self) -> "Tuple[int, int, int, int, List[int], List] | None":
        """Marshal the cleared numerator terms into the interned-symbol wire form the
        thetasum C peers consume — ``(n_syms, xsym, ysym, psym, term_nthetas,
        monomials)`` — or ``None`` when the numerator is empty. The symbol universe is
        every symbol on a prefactor or a theta argument, sorted by NAME so the C dense
        exponent vector reproduces :meth:`~srmech.amsc.ellbase.EllMonomial._sort_key`."""
        if not self._terms:
            return None
        syms: "set" = set()
        for pref, thetas in self._terms:
            syms.update(pref.exps.keys())
            for t in thetas:
                syms.update(t.arg.exps.keys())
        sym_list = sorted(syms)
        idx = {s: i for i, s in enumerate(sym_list)}
        n_syms = len(sym_list)

        def row(m: EllMonomial) -> "List[int]":
            r = [0] * n_syms
            for s, e in m.exps.items():
                r[idx[s]] = e
            return r

        monomials: "List[Tuple[int, int, List[int]]]" = []
        term_nthetas: "List[int]" = []
        for pref, thetas in self._terms:
            monomials.append((pref.coeff.numerator, pref.coeff.denominator, row(pref)))
            for t in thetas:
                a = t.arg
                monomials.append((a.coeff.numerator, a.coeff.denominator, row(a)))
            term_nthetas.append(len(thetas))
        return (n_syms, idx.get(_X, -1), idx.get(_Y, -1), idx.get(_P, -1),
                term_nthetas, monomials)

    def _is_zero_interpolation_c(self, parallel: bool = False) -> "bool | None":
        """Dispatch the structural CERTIFICATE-recursion ``is_zero`` decision to the
        native ``srmech_thetasum_is_zero_interpolation`` C peer (rebuilt rc210 as the
        1:1 mirror of :meth:`_is_zero_interpolation`'s sound bool: True ⟺ certificate-
        proven, False = not proven) → the bool verdict, or ``None`` when the native
        symbols are absent OR the peer declines (a ``SRMECH_ERR_OVERFLOW`` size-guard
        trip → the caller falls to the pure path, which is sound). Keeps ``is_zero`` a
        TOTAL function: a native size-guard never crashes the decision, it degrades to
        the exact pure oracle.

        ``parallel=True`` opts in to the rc103 CHIRALITY-PRESERVING parallel peer
        (``srmech_thetasum_is_zero_interpolation_parallel``) — an ACCELERATOR whose
        verdict is BYTE-FOR-BYTE the sequential peer's; on a ``None`` (absent / decline)
        it falls to the sequential peer, then the pure oracle. So the verdict is
        identical whether or not the parallel peer is used."""
        marshalled = self._is_zero_c_marshal()
        if marshalled is None:
            return True
        n_syms, xsym, ysym, psym, term_nthetas, monomials = marshalled
        if parallel and _nat.has_native_thetasum_interpolation_parallel():
            try:
                pv = _nat.thetasum_is_zero_interpolation_parallel_c(
                    n_syms, xsym, ysym, psym, term_nthetas, monomials)
            except (RuntimeError, OverflowError, ValueError):
                pv = None
            if pv is not None:
                return pv
        if not _nat.has_native_thetasum_interpolation():
            return None
        try:
            return _nat.thetasum_is_zero_interpolation_c(
                n_syms, xsym, ysym, psym, term_nthetas, monomials)
        except (RuntimeError, OverflowError, ValueError):
            return None

    def is_zero_ws_estimate_bytes(self) -> "int | None":
        """The ESTIMATED memory (BYTES) the exact structural-interpolation :attr:`is_zero`
        decision would allocate for this ThetaSum's cleared numerator — computed WITHOUT
        allocating it (reuses the rc102 C sizer; no new C op). The **"inform, don't LIMIT"**
        query: a memory-constrained / edge caller checks the cost BEFORE deciding a heavy
        elliptic residual (the hardest Frenkel–Turaev ₁₀E₉ cases size to tens of GB), so it
        KNOWS what is and is not holdable on its hardware. ``is_zero`` itself is NEVER capped
        by this — it runs wherever the arena fits; the estimate only informs the caller.

        Returns the byte estimate, ``0`` for a numerator that clears to trivially zero (no
        arena), or ``None`` on a pure / pre-rc102 build (the native sizer is absent — the
        cost cannot be estimated, and the complete pure oracle decides regardless)."""
        marshalled = self._is_zero_c_marshal()
        if marshalled is None:
            return 0
        n_syms, xsym, ysym, psym, term_nthetas, monomials = marshalled
        return _nat.thetasum_is_zero_ws_estimate_bytes(
            n_syms, xsym, ysym, psym, term_nthetas, monomials)

    def __eq__(self, other) -> bool:
        if other is self:
            return True
        if isinstance(other, ThetaSum):
            return (self - other).is_zero
        c = _coerce_q(other)
        if c is not None:
            return (self - ThetaSum.one()._scaled(c)).is_zero
        return NotImplemented

    def __ne__(self, other):
        r = self.__eq__(other)
        return r if r is NotImplemented else (not r)

    # ── evaluation (exact-ℚ; used only inside the degree-bound test) ─────────
    def eval_trunc(self, values: "Mapping[str, object]", n_terms: int) -> Q:
        """Evaluate to a single exact ``Q`` (no float): the summed numerator
        theta-products over the denominator theta-product, each theta read by the
        exact-``ℚ`` truncated modified-theta product (:meth:`Theta.eval_trunc`).
        ``values`` supplies ``p`` and every argument symbol. Used ONLY inside the
        degree-bound :meth:`is_zero` test (on a bounded-degree residual, where the
        truncation past the degree bound certifies the value). A zero denominator
        theta raises ``ZeroDivisionError``."""
        num_acc = _Q_ZERO
        for pref, thetas in self._terms:
            term = pref.eval(values)
            for t in thetas:
                term = term * t.eval_trunc(values, n_terms)
            num_acc = num_acc + term
        if num_acc == _Q_ZERO:
            return _Q_ZERO
        den_acc = self._den_pref.eval(values)
        for t in self._den_thetas:
            d = t.eval_trunc(values, n_terms)
            if d == _Q_ZERO:
                raise ZeroDivisionError("ThetaSum.eval_trunc: denominator theta is zero")
            den_acc = den_acc * d
        if den_acc == _Q_ZERO:
            raise ZeroDivisionError("ThetaSum.eval_trunc: denominator is zero")
        return num_acc / den_acc

    def __repr__(self) -> str:
        return (f"ThetaSum({len(self._terms)} term(s), "
                f"den={len(self._den_thetas)}θ)")

    # ── the MPM-verified Weierstrass three-term addition identity ────────────
    @classmethod
    def three_term(cls, a: EllMonomial, b: EllMonomial, c: EllMonomial,
                   x: "EllMonomial | None" = None) -> "ThetaSum":
        """Construct the Weierstrass three-term theta relation as a ``ThetaSum`` that is
        IDENTICALLY ZERO (Rosengren §1.4 Eq. 1.12, MPM-verified at build — see the
        module docstring): with ``θ(uv^±) = θ(uv)θ(u/v)``,

            θ(ax^±)θ(bc^±) − θ(bx^±)θ(ac^±) − (a/c)·θ(cx^±)θ(ba^±)  ≡  0.

        The ``a/c`` weight is an exact ``EllMonomial`` (the ratio of the two scalars /
        monomials). ``x`` defaults to the symbol ``x``. Returns the certificate-shaped
        ``ThetaSum`` whose :meth:`is_zero` is True — the known-identity keystone of the
        degree-bound test AND the constructive addition formula the genuine engine
        needs. (To get the ADDITION FORMULA as a rewrite, ``three_term(...) == 0`` is the
        identity ``θ(ax^±)θ(bc^±) = θ(bx^±)θ(ac^±) + (a/c)·θ(cx^±)θ(ba^±)``.)"""
        for nm, m in (("a", a), ("b", b), ("c", c)):
            if not isinstance(m, EllMonomial):
                raise TypeError(f"ThetaSum.three_term: {nm} must be an EllMonomial")
        xx = EllMonomial.symbol(_X) if x is None else x
        if not isinstance(xx, EllMonomial):
            raise TypeError("ThetaSum.three_term: x must be an EllMonomial")

        def pm(u: EllMonomial, v: EllMonomial) -> "Tuple[Theta, Theta]":
            """θ(uv^±) = θ(uv)·θ(u/v) as the two Theta factors."""
            return (Theta(u * v), Theta(u / v))

        # term 1:  +1 · θ(ax^±) θ(bc^±)
        t1 = (Q(1, 1), EllMonomial.one(), pm(a, xx) + pm(b, c))
        # term 2:  −1 · θ(bx^±) θ(ac^±)
        t2 = (Q(-1, 1), EllMonomial.one(), pm(b, xx) + pm(a, c))
        # term 3:  −(a/c) · θ(cx^±) θ(ba^±)
        t3 = (Q(1, 1), EllMonomial(Q(-1, 1)) * (a / c), pm(c, xx) + pm(b, a))
        return cls(terms=(t1, t2, t3),
                   den_prefactor=EllMonomial.one(), den_thetas=())

    @classmethod
    def _wrap(cls, terms: "Tuple[_Term, ...]", den_pref: EllMonomial,
              den_thetas: "Tuple[Theta, ...]") -> "ThetaSum":
        """Internal: wrap ALREADY-canonical, ALREADY-combined ``(terms, den)`` with no
        re-canon (the fast path for the algebra)."""
        s = cls.__new__(cls)
        s._terms, s._den_pref, s._den_thetas = terms, den_pref, den_thetas
        return s


# ── module helpers (private — invisible to the tool-schema / Rosetta walks) ──


def _ellmono_add(a: EllMonomial, b: EllMonomial) -> EllMonomial:
    """Exact SUM of two LIKE monomials (same symbol-exponent map) → the monomial with
    summed ``Q`` coefficients (sign = Class-K). The zero monomial is the additive
    identity; otherwise the two must share the same exponent monomial (the combine step
    only ever adds canonical like-terms). No float, no ``abs()``."""
    if a.is_zero:
        return b
    if b.is_zero:
        return a
    if a.exps != b.exps:
        raise ValueError("_ellmono_add: only like monomials add (same exponent map)")
    return EllMonomial(a.coeff + b.coeff, a.exps)


def _multiset_union(xs: "Tuple[Theta, ...]", ys: "Tuple[Theta, ...]"
                    ) -> "Tuple[Theta, ...]":
    """The theta MULTISET UNION (max multiplicity per canonical theta) — the least
    common denominator's theta factors. Plain multiset bookkeeping (not a Counter
    spectral proxy)."""
    cx: "Dict[Theta, int]" = {}
    for t in xs:
        cx[t] = cx.get(t, 0) + 1
    cy: "Dict[Theta, int]" = {}
    for t in ys:
        cy[t] = cy.get(t, 0) + 1
    out: "List[Theta]" = []
    for t in set(cx) | set(cy):
        mult = cx.get(t, 0) if cx.get(t, 0) >= cy.get(t, 0) else cy.get(t, 0)
        out.extend([t] * mult)
    out.sort(key=lambda th: th.arg._sort_key())
    return tuple(out)


def _multiset_diff(xs: "Tuple[Theta, ...]", ys: "Tuple[Theta, ...]"
                   ) -> "Tuple[Theta, ...]":
    """The theta MULTISET DIFFERENCE ``xs ∖ ys`` (xs assumed to contain ys; used to find
    the surplus denominator factors that multiply a numerator when re-basing over a
    common denominator). Plain multiset bookkeeping."""
    cy: "Dict[Theta, int]" = {}
    for t in ys:
        cy[t] = cy.get(t, 0) + 1
    out: "List[Theta]" = []
    for t in xs:
        if cy.get(t, 0) > 0:
            cy[t] -= 1
        else:
            out.append(t)
    out.sort(key=lambda th: th.arg._sort_key())
    return tuple(out)


# ── the EXACT Weierstrass three-term-relation reducer (the is_zero decision) ──
#
# A genuine theta identity (terms with DIFFERENT theta multisets, e.g. the Weierstrass
# relation) is NEVER exactly 0 at any finite eval_trunc depth — a truncated modified-
# theta product only CONVERGES. So is_zero is decided SYMBOLICALLY: reduce every
# theta-product to a canonical additive normal form via the EXACT three-term relation
# (Rosengren Eq. 1.12), then check exact carrier cancellation. No float, no eval.
#
# Each theta-product is recognised as a multiset of plus/minus PAIRS theta(a*b^pm) =
# theta(ab)*theta(a/b), recovered by the MIDPOINT (geometric mean): two canonical thetas
# theta(z1), theta(z2) form a pair iff z1*z2 is a perfect-square monomial, midpoint
# alpha = sqrt(z1 z2), half beta = sqrt(z1/z2).

# the bounded fixpoint cap for the Weierstrass reduction (the non-ref s-pair count
# strictly decreases each pass, so a small cap suffices; an over-cap term is left
# un-reduced and the class honestly reports NOT-zero rather than looping).
_REDUCE_MAX_PASSES = 64


def _int_sqrt(n: int) -> "int | None":
    """The exact integer square root of a non-negative ``int``, or ``None`` if ``n`` is
    not a perfect square. Class-K (no abs); a negative input has no real sqrt -> None."""
    if n < 0:
        return None
    if n == 0:
        return 0
    lo, hi = 1, n
    while lo <= hi:
        mid = (lo + hi) // 2
        sq = mid * mid
        if sq == n:
            return mid
        if sq < n:
            lo = mid + 1
        else:
            hi = mid - 1
    return None


def _monomial_sqrt(z: EllMonomial) -> "EllMonomial | None":
    """The exact monomial square-root ``sqrt(z)`` (halve every integer exponent; the
    ``Q`` coefficient must be a perfect rational square) or ``None`` if ``z`` is not a
    perfect-square monomial. Exact, integer-exponent only -- no float."""
    if z.is_zero:
        return None
    exps: "Dict[str, int]" = {}
    for s, e in z.exps.items():
        if e % 2 != 0:
            return None
        if e:
            exps[s] = e // 2
    rn = _int_sqrt(z.coeff.numerator)
    rd = _int_sqrt(z.coeff.denominator)
    if rn is None or rd is None:
        return None
    return EllMonomial(Q(rn, rd), exps)


def _canon_pair(u: EllMonomial, v: EllMonomial
                ) -> "Tuple[EllMonomial, Tuple[EllMonomial, EllMonomial]]":
    """Canonicalize an arbitrary plus/minus pair ``theta(u*v^pm) = theta(uv)*theta(u/v)``
    to a TOTALLY-fixed representative ``(alpha, beta)``, folding the EXACT inversion
    prefactor every reorientation costs. The pair is the unordered theta-set
    ``{theta(uv), theta(u/v)}``; canonicalization picks a deterministic rep using two
    exact, build-verified rules:

      (1)  theta(alpha*beta^pm) == theta(alpha*(1/beta)^pm)        (HALF flip -- FREE)
      (2)  theta(u*v^pm)        == -(u/v) * theta(v*u^pm)          (MIDPOINT<->HALF swap)

    Returns ``(prefactor, (alpha, beta))`` with ``theta(u*v^pm) == prefactor *
    theta(alpha*beta^pm)`` (``prefactor`` exact, sign = Class-K). The rep is unique: the
    two halves ``{uv, u/v}`` (modulo the simultaneous inversion of BOTH, which is the
    midpoint<->half swap) are ordered canonically, so equivalent pairs collapse to the
    same key and combine exactly in :func:`_combine_rterms`."""
    # the two theta arguments of the pair (an unordered set up to global inversion).
    arg1 = u * v
    arg2 = u * v.inv()
    # rule (1): each theta arg may be inverted freely IF we fix the orientation by a
    # canonical choice; but inverting ONE arg changes the pair. The pair as a whole has
    # exactly two reps: (u, v) and (v, u) [the midpoint<->half swap, rule (2)] -- plus the
    # free half-flip (u, 1/v) == (u, v). So enumerate the two swap reps, each half-flipped
    # to its canonical half, and pick the lexicographically smaller, with its prefactor.
    cand: "List[Tuple[EllMonomial, EllMonomial, EllMonomial]]" = []
    # rep A: midpoint u, half v  -> prefactor 1
    aA, bA = _canon_half(u, v)
    cand.append((EllMonomial.one(), aA, bA))
    # rep B: midpoint v, half u  -> theta(u*v^pm) = -(u/v) theta(v*u^pm); prefactor -(u/v)
    aB, bB = _canon_half(v, u)
    cand.append((EllMonomial(Q(-1, 1)) * (u / v), aB, bB))
    cand.sort(key=lambda t: (t[1]._sort_key(), t[2]._sort_key()))
    pref, alpha, beta = cand[0]
    return pref, (alpha, beta)


def _canon_half(alpha: EllMonomial, beta: EllMonomial
                ) -> "Tuple[EllMonomial, EllMonomial]":
    """Fix the half ``beta`` to its canonical orientation (FREE by rule (1)): a positive
    leading summation-symbol exponent (``x`` then ``y``), else the lexicographically-
    smaller of ``{beta, 1/beta}``. ``alpha`` (the midpoint) is untouched."""
    binv = beta.inv()
    for s in (_X, _Y):
        eb = beta.exp_of(s)
        if eb != 0:
            return alpha, (beta if eb > 0 else binv)
    return alpha, (beta if beta._sort_key() <= binv._sort_key() else binv)


def _recover_pairs(thetas: "Tuple[Theta, ...]"
                   ) -> "Tuple[EllMonomial, List[Tuple[EllMonomial, EllMonomial]]] | None":
    """Recover the plus/minus-pair decomposition of a canonical theta-product: pair the
    canonical thetas (after :meth:`Theta.canonicalize`) by the MIDPOINT test (two thetas
    ``theta(z1), theta(z2)`` pair iff ``z1*z2`` is a perfect-square monomial). Returns
    ``(prefactor, pairs)`` where ``pairs`` are the totally-canonical ``(alpha, beta)``
    (each via :func:`_canon_pair`, its inversion prefactor folded into ``prefactor``), or
    ``None`` if the product is not a clean product of plus/minus-pairs (odd count, no
    consistent pairing). EXACT -- the prefactor keeps the recovery value-faithful."""
    canon: "List[EllMonomial]" = []
    for t in thetas:
        _pr, t0 = t.canonicalize()
        canon.append(t0.arg)
    if len(canon) % 2 != 0:
        return None
    used = [False] * len(canon)
    pairs: "List[Tuple[EllMonomial, EllMonomial]]" = []
    pref = EllMonomial.one()
    for i in range(len(canon)):
        if used[i]:
            continue
        matched = False
        for j in range(i + 1, len(canon)):
            if used[j]:
                continue
            alpha = _monomial_sqrt(canon[i] * canon[j])
            if alpha is None:
                continue
            beta = _monomial_sqrt(canon[i] / canon[j])
            if beta is None:
                continue
            pr, ab = _canon_pair(alpha, beta)
            pref = pref * pr
            pairs.append(ab)
            used[i] = used[j] = True
            matched = True
            break
        if not matched:
            return None
    return pref, pairs


# A reduced symbolic term: (prefactor, tuple of canonical plus/minus-pairs (alpha, beta)).
_RTerm = Tuple[EllMonomial, "Tuple[Tuple[EllMonomial, EllMonomial], ...]"]


def _rterm_key(pairs: "Tuple[Tuple[EllMonomial, EllMonomial], ...]") -> "Tuple":
    """A canonical multiset key for a reduced term's pairs (orientation-fixed), so like
    normal-form terms combine. Coefficient-free (coefficients add)."""
    return tuple(sorted((a._sort_key(), b._sort_key()) for a, b in pairs))


def _three_term_rewrite(pairs: "List[Tuple[EllMonomial, EllMonomial]]",
                        pref: EllMonomial, s: str
                        ) -> "List[_RTerm] | None":
    """Apply ONE EXACT Weierstrass three-term rewrite (Rosengren Eq. 1.12, build-verified
    by convergence) that STRICTLY LOWERS the term's largest ``s``-pair midpoint, so the
    multiset of ``s``-pair midpoints decreases in the well-founded multiset order and the
    reduction TERMINATES (no cycling). In ``(midpoint, half)`` pair notation, with the
    ``s``-pair ``theta(a*s^pm)`` (``a`` = its midpoint) and a partner CONSTANT pair
    ``theta(pa*pb^pm)``, Eq. 1.12 with ``(a, b, c, x) = (a, pa, pb, s)`` gives

        theta(a*s^pm)*theta(pa*pb^pm)
            = theta(pa*s^pm)*theta(a*pb^pm) + (a/pb)*theta(pb*s^pm)*theta(pa*a^pm).

    The new ``s``-pair midpoints are ``pa`` and ``pb``; we fire ONLY when BOTH are
    strictly smaller than ``a`` (so the largest ``s``-midpoint strictly drops). The
    orientations are LOAD-BEARING: ``theta(pa*a^pm)`` is midpoint ``pa``, half ``a`` (NOT
    ``a, pa`` -- they differ by an inversion prefactor :func:`_canon_pair` folds). The
    summation VARIABLE is the pair half that carries ``s`` (e.g. ``x`` or, after a
    :meth:`ThetaSum.shift_x`, ``q*x``); it is preserved across the rewrite. Returns the
    two reduced terms, or ``None`` when no such strictly-decreasing rewrite applies."""
    # an s-pair is one whose HALF carries the summation symbol s (exponent != 0); the
    # variable is that half (e.g. x, or q*x after a shift). Pick the s-pair with the
    # LARGEST midpoint and read off its variable.
    s_idx = None
    a_mid = None
    s_var = None
    for idx, (a, b) in enumerate(pairs):
        if b.exp_of(s) != 0 and (a_mid is None or a._sort_key() > a_mid._sort_key()):
            s_idx, a_mid, s_var = idx, a, b
    if s_idx is None:
        return None
    # a partner CONSTANT pair (both halves s-free) whose BOTH halves' midpoints are
    # strictly < a_mid (guarantees the new s-midpoints pa, pb are smaller -> termination).
    partner_idx = None
    for idx, (pa, pb) in enumerate(pairs):
        if idx == s_idx:
            continue
        if pa.exp_of(s) != 0 or pb.exp_of(s) != 0:
            continue
        if pa._sort_key() < a_mid._sort_key() and pb._sort_key() < a_mid._sort_key():
            partner_idx = idx
            break
    if partner_idx is None:
        return None
    pa, pb = pairs[partner_idx]
    rest = [pr for k, pr in enumerate(pairs) if k not in (s_idx, partner_idx)]
    # term A:  theta(pa*svar^pm)*theta(a_mid*pb^pm)              coeff 1
    cA1, pairA1 = _canon_pair(pa, s_var)
    cA2, pairA2 = _canon_pair(a_mid, pb)
    termA = rest + [pairA1, pairA2]
    coeffA = cA1 * cA2
    # term B:  (a_mid/pb)*theta(pb*svar^pm)*theta(pa*a_mid^pm)   [midpoint pa, half a_mid]
    cB1, pairB1 = _canon_pair(pb, s_var)
    cB2, pairB2 = _canon_pair(pa, a_mid)
    termB = rest + [pairB1, pairB2]
    coeffB = (a_mid / pb) * cB1 * cB2
    return [(pref * coeffA, tuple(termA)), (pref * coeffB, tuple(termB))]


def _combine_rterms(rterms: "List[_RTerm]") -> "List[_RTerm]":
    """Combine LIKE reduced terms — same canonical pair-multiset AND same prefactor
    symbol-monomial — by adding their exact ``Q`` scalar coefficients; drop terms whose
    coefficient cancels to 0. Two terms with the same thetas but DIFFERENT prefactor
    monomials are NOT like-terms (``a²b·θ… + a²c·θ…`` is not a single monomial × θ), so
    they stay separate — exact carrier algebra, no spurious merge."""
    groups: "Dict[Tuple, Tuple[Q, EllMonomial, Tuple]]" = {}
    order: "List[Tuple]" = []
    for pref, pairs in rterms:
        if pref.is_zero:
            continue
        key = (_rterm_key(pairs), tuple(sorted(pref.exps.items())))
        if key in groups:
            qc, mono, pp = groups[key]
            groups[key] = (qc + pref.coeff, mono, pp)
        else:
            # store the scalar Q separately from the symbol-only monomial
            mono_only = EllMonomial(_Q_ONE, pref.exps)
            groups[key] = (pref.coeff, mono_only, pairs)
            order.append(key)
    out: "List[_RTerm]" = []
    for key in order:
        qc, mono, pairs = groups[key]
        if qc != _Q_ZERO:
            out.append((mono * EllMonomial.scalar(qc), pairs))
    return out


def _reduce_class(members: "List[_Term]") -> "List[_RTerm] | None":
    """Reduce a quasi-periodicity class to canonical Weierstrass normal form by repeatedly
    applying the strictly-decreasing three-term rewrite (:func:`_three_term_rewrite`) on
    BOTH summation symbols, then combining like terms exactly. Returns the combined reduced
    terms (zero-coefficient dropped), or ``None`` if a term is not a clean product of
    plus/minus-pairs (outside this carrier's reducible shape). Pure symbolic carrier
    algebra -- no evaluation. The rewrite lowers the largest ``s``-pair midpoint each
    step, so the bounded fixpoint TERMINATES; the canonical-pair combine
    (:func:`_combine_rterms`, using :func:`_canon_pair`'s exact inversion prefactors)
    collapses the surviving like terms."""
    rterms: "List[_RTerm]" = []
    for pref, thetas in members:
        rec = _recover_pairs(thetas)
        if rec is None:
            return None
        rpref, pairs = rec
        rterms.append((pref * rpref, tuple(pairs)))
    rterms = _combine_rterms(rterms)
    work = list(rterms)
    for _ in range(_REDUCE_MAX_PASSES):
        changed = False
        for s in (_X, _Y):
            nxt: "List[_RTerm]" = []
            pass_changed = False
            for pref, pairs in work:
                rewritten = _three_term_rewrite(list(pairs), pref, s)
                if rewritten is None:
                    nxt.append((pref, pairs))
                else:
                    nxt.extend(rewritten)
                    pass_changed = True
            work = _combine_rterms(nxt)
            changed = changed or pass_changed
        if not changed:
            break
    return work


def _class_is_zero(members: "List[_Term]") -> bool:
    """Decide whether ONE quasi-periodicity class's term-sum is ``== 0`` EXACTLY, by the
    Weierstrass three-term-relation reduction (:func:`_reduce_class`) to canonical normal
    form -- NO evaluation, NO convergence (a genuine theta identity is never exactly 0 at
    any finite ``eval_trunc`` depth; the decision is symbolic). The class is ``== 0`` IFF
    its reduced normal form is empty (every coefficient cancelled).

    If a term is not a clean product of plus/minus-pairs (outside the reducible shape this
    carrier covers), :func:`_reduce_class` returns ``None`` and the class CANNOT be
    certified ``== 0`` symbolically here -> honestly report NOT-zero (never accept on a
    converging eval -- the rc61 no-hallucination standard). The construction-time combine
    already cancels carrier-equal like-terms, so the common cases reduce cleanly."""
    if not members:
        return True
    reduced = _reduce_class(members)
    if reduced is None:
        return False
    return len(reduced) == 0
