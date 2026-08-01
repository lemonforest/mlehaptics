"""rc235 (#833) — the ``ThetaSum.is_zero`` Z6 COLLAPSE / re-arrangement ZERO certificate.

The 0-VARIABLE theta-CONSTANT leaf ``Σ cᵢ ∏ θ(rational; p)`` (all summation variables
consumed by the Z4 interpolation) is NOT generally undecidable — it is SOMETIMES open:
its VALUE is genuinely zero, but the certificate FRAME cannot SEE the collapse until the
right RE-ARRANGEMENT / GRADING aligns the "seam" (the ``the_one`` ``S(σ,θ)`` shape: right
value, not correct across the metacycle seams until the winding grading ``w`` was added in
rc137). Z5 (rc228) lifts ONE prime back to an elliptic variable and closes a leaf iff a
SINGLE summation seam suffices; a leaf carrying TWO OR MORE INDEPENDENT seams — a genuine
high-kernel-rank sum, e.g. the SUM of two three-term identities over DISJOINT prime
alphabets — declines to ``is_zero = False``.

**Z6 is that missing rung.** It searches a BOUNDED family of value-preserving re-gradings:
lift a SUBSET ``S`` (size 2..3) of the leaf's distinct primes SIMULTANEOUSLY, each to its
own fresh elliptic variable (the un-lifted primes stay as the constant partner pairs), then
close the lifted object by the EXACT Weierstrass ±-pair reduction. The lift is exact so
``L(S := primes) = leaf``; a proof ``L ≡ 0`` SPECIALIZES to ``leaf ≡ 0`` (a THEOREM, not a
numeric band). Z6 produces ONLY ZERO verdicts (never a false zero — a genuinely-nonzero
leaf has ``L ≢ 0`` so the sound ±-pair reduction never empties).

This suite proves:
  1. Z6 CLOSES a REAL rank-2 (and rank-3) family the current system DECLINES — with the
     explicit ``_z5`` DECLINE / ``_z6`` CLOSE contrast proving it is NEW coverage.
  2. SOUNDNESS — perturbed / broken siblings stay ``is_zero = False`` (Z6 declines each),
     cross-checked by an INDEPENDENT exact-``Fraction`` ``p``-expansion oracle
     (``oracle nonzero ⇒ is_zero MUST be False`` — the rc234 pattern).
  3. the (3,3) RESIDUE — HONEST: Z6 does NOT close the rc227 Aₙ (3,3) leaf (it needs the
     Riemann-quartic rung, not the ±-pair three-term reduction); it declines FAST, staying
     the correct ``is_zero = False``.
  4. native == pure on the Z6 corpus. rc255: the native peer now DECIDES the top-level
     all-constant leaves directly (reserves synthetic lift + p slots for the Z5/Z6
     certificates) — it PROVES the Z6 zeros True rather than deferring to pure.

No result routes through the machinery under test; the oracle is stdlib ``Fraction``
(deliberately NOT srmech's ``Q``), a definitive one-sided nonzero-detector.
"""
import random
import time

from fractions import Fraction

import pytest

from srmech.amsc import ThetaSum, _native
from srmech.apokatastasis.ellbase import EllMonomial as M, Theta
from srmech.math.q import Q
from srmech.apokatastasis.thetasum import (
    _NONZERO, _UNKNOWN, _ZERO, _decide_thetasum, _leaf_prime_set,
    _z5_theta_constant_zero, _z6_theta_constant_zero,
)

_X = M.symbol("x")


def _leaf_terms(ts):
    return [(pref, [t.arg for t in thetas]) for pref, thetas in ts.terms]


# ─────────────────────────  exact-Fraction (p, x, y) series oracle (rc234 pattern)  ──
# Independent of srmech's Q / is_zero. A DEFINITIVE one-sided nonzero-detector.


def _fmul(a, b, K):
    out = {}
    for (p1, x1, y1), v1 in a.items():
        for (p2, x2, y2), v2 in b.items():
            pk = p1 + p2
            if pk > K:
                continue
            key = (pk, x1 + x2, y1 + y2)
            out[key] = out.get(key, Fraction(0)) + v1 * v2
    return {k: v for k, v in out.items() if v != 0}


def _factor(key, coeff):
    f = {(0, 0, 0): Fraction(1)}
    f[key] = f.get(key, Fraction(0)) + coeff
    return {k: v for k, v in f.items() if v != 0}


def _theta_f(c, ex, ey, K):
    acc = {(0, 0, 0): Fraction(1)}
    ci = Fraction(1) / c
    for k in range(K + 1):
        acc = _fmul(acc, _factor((k, ex, ey), -c), K)
        if k + 1 <= K:
            acc = _fmul(acc, _factor((k + 1, -ex, -ey), -ci), K)
    return acc


def _spec_mono(m, spec):
    scal = Fraction(m.coeff.numerator, m.coeff.denominator)
    ps = xe = ye = 0
    for s, e in m.exps.items():
        if s == "p":
            ps += e
        elif s == "x":
            xe += e
        elif s == "y":
            ye += e
        else:
            scal *= spec[s] ** e
    return ps, xe, ye, scal


def _numerator_pexp(ts, spec, K):
    total = {}
    for pref, thetas in ts.terms:
        ps, xe, ye, scal = _spec_mono(pref, spec)
        term = {(ps, xe, ye): scal}
        for t in thetas:
            zps, zxe, zye, zscal = _spec_mono(t.arg, spec)
            assert zps == 0, "a canonical theta argument must be p-exponent 0"
            term = _fmul(term, _theta_f(zscal, zxe, zye, K), K)
        for key, v in term.items():
            total[key] = total.get(key, Fraction(0)) + v
    return {k: v for k, v in total.items() if v != 0}


_ORACLE_PRIMES = (101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151, 157, 163, 167,
                  173, 179, 181, 191, 193, 197, 199, 211, 223, 227, 229, 233, 239, 241)


def _oracle_nonzero(ts, K, n_spec=4, seed=90210):
    """``True`` iff the exact ``p``-expansion (to order K) is nonzero under SOME parameter
    specialisation — a DEFINITIVE proof the numerator is genuinely NONZERO. ``False`` is
    inconclusive (a genuine zero, or a nonzero whose first coefficient is above K)."""
    syms = set()
    for pref, thetas in ts.terms:
        for s in pref.exps:
            if s not in ("x", "y", "p"):
                syms.add(s)
        for t in thetas:
            for s in t.arg.exps:
                if s not in ("x", "y", "p"):
                    syms.add(s)
    syms = sorted(syms)
    if not syms:
        return bool(_numerator_pexp(ts, {}, K))
    rng = random.Random(seed)
    need = 2 * len(syms)
    for _ in range(n_spec):
        pool = rng.sample(_ORACLE_PRIMES, need)
        spec = {s: Fraction(pool[2 * i], pool[2 * i + 1]) for i, s in enumerate(syms)}
        if _numerator_pexp(ts, spec, K):
            return True
    return False


# ─────────────────────────  the disjoint-seam builders  ──────────────────────────────


def _seam(a, b, c, x):
    """A single Weierstrass three-term seam as an all-constant leaf (a·b·c·x distinct
    primes) — ``three_term(a,b,c,x) ≡ 0``, a 0-variable theta-constant identity."""
    return ThetaSum.three_term(M.scalar(Q(a, 1)), M.scalar(Q(b, 1)),
                               M.scalar(Q(c, 1)), x=M.scalar(Q(x, 1)))


# A over primes {2,3,5,7}; B over {11,13,17,19}; C over {23,29,31,37} — DISJOINT alphabets.
_A = _seam(2, 5, 7, 3)
_B = _seam(11, 13, 17, 19)
_C = _seam(23, 29, 31, 37)


# ─────────────────────────  (1) Z6 CLOSES the rank-2 disjoint-seam family  ────────────


def test_z6_certifies_rank2_disjoint_seam():
    """``A + B`` (two three-term seams over disjoint primes) is genuinely ZERO but Z5's
    single-prime lift DECLINES it (only one seam's variable can be freed); Z6's multi-prime
    re-grading CLOSES it. The dispatched decision, the pure oracle, and the certificate
    recursion (fast path OFF) all certify ZERO."""
    S = _A + _B
    tt = _leaf_terms(S)
    assert len(S.terms) == 6                              # a genuine 6-term rank-2 leaf
    # NEW COVERAGE: Z5 declines, Z6 closes — the exact contrast proving it is a new rung
    assert _z5_theta_constant_zero(tt) is False
    assert _z6_theta_constant_zero(tt) is True
    # the shipped verdicts
    assert S.is_zero is True
    assert S._is_zero_py() is True
    assert _decide_thetasum(S, use_fastpath=False) == _ZERO
    # the independent oracle AGREES it is genuinely zero (no nonzero coefficient)
    assert _oracle_nonzero(S, K=18) is False


def test_z6_certifies_rank3_disjoint_seam():
    """``A + B + C`` (three disjoint seams, rank-3) closes via a size-3 subset re-grading
    (one lifted prime per seam) — Z5 and any size-≤2 re-grading DECLINE it."""
    S = _A + _B + _C
    tt = _leaf_terms(S)
    assert len(S.terms) == 9
    assert _z5_theta_constant_zero(tt) is False
    assert _z6_theta_constant_zero(tt) is True
    assert S.is_zero is True
    assert S._is_zero_py() is True
    assert _oracle_nonzero(S, K=16) is False


# ─────────────────────────  (2) SOUNDNESS — no false zero  ────────────────────────────


def _scale_first_term(ts, factor):
    """Rebuild ``ts`` with its FIRST numerator term's coefficient scaled by ``factor`` — a
    genuine perturbation that breaks the identity (the whole is no longer ≡ 0)."""
    terms = []
    for i, (pref, thetas) in enumerate(ts.terms):
        c = Q(factor.numerator, factor.denominator) if i == 0 else Q(1, 1)
        terms.append((c, pref, tuple(thetas)))
    return ThetaSum(terms=terms)


def test_z6_soundness_perturbed_siblings_stay_false():
    """Perturbed / broken siblings of the disjoint-seam family are GENUINELY NONZERO; Z6
    must DECLINE every one (a false zero here is the soundness bug #833 targets). The exact
    ``Fraction`` oracle proves each is genuinely nonzero, so the assertion is not vacuous."""
    S = _A + _B
    siblings = [
        S + ThetaSum.one(),                               # + a nonzero constant term
        _scale_first_term(_A, Fraction(2, 1)) + _B,       # break seam A's first coefficient
        _scale_first_term(_A, Fraction(3, 2)) + _B,       # a rational break
        S + _seam(23, 29, 31, 37)._scaled(Q(1, 1)) + ThetaSum.one()._scaled(Q(1, 7)),
    ]
    for sib in siblings:
        if not sib.terms:
            continue
        assert _oracle_nonzero(sib, K=16) is True, f"oracle should prove nonzero: {sib!r}"
        assert _z6_theta_constant_zero(_leaf_terms(sib)) is False
        assert sib.is_zero is False, f"FALSE ZERO (dispatched): {sib!r}"
        assert sib._is_zero_py() is False, f"FALSE ZERO (pure): {sib!r}"
        assert _decide_thetasum(sib, use_fastpath=False) in (_NONZERO, _UNKNOWN)


def test_z6_only_zero_never_nonzero():
    """``_z6_theta_constant_zero`` is a ZERO-ONLY certificate: a bool, ``False`` on any
    leaf it cannot prove zero (never a NONZERO *claim*). A single-term leaf (no possible
    ±-pair cancellation) and a fewer-than-two-prime leaf both decline."""
    single = ThetaSum(terms=((Q(3, 1), M.scalar(Q(2, 1)), (Theta(M.scalar(Q(5, 1))),)),))
    assert _z6_theta_constant_zero(_leaf_terms(single)) is False
    # a leaf whose only prime is 2 (< 2 distinct primes) → Z6 needs ≥2 to lift a subset
    one_prime = ThetaSum(terms=(
        (Q(1, 1), M.one(), (Theta(M.scalar(Q(2, 1))),)),
        (Q(-1, 1), M.one(), (Theta(M.scalar(Q(4, 1))),)),
    ))
    tp = _leaf_terms(one_prime)
    assert len(_leaf_prime_set(tp)) == 1
    assert _z6_theta_constant_zero(tp) is False


def test_z6_leaves_the_rc228_witnesses_nonzero():
    """The #771 FALSE-ZERO witnesses (genuinely-nonzero, symbol-bearing objects) stay
    ``is_zero = False`` — Z6 is gated to the 0-variable constant leaf and can never certify
    a nonzero object (it only ADDS zero proofs)."""
    uc = [(2, Q(-133824, 26411)), (3, Q(388557, 26411)), (4, Q(-231961600, 11541607)),
          (5, Q(19987500, 1322951)), (6, Q(-15163200, 2516591)), (7, Q(1, 1))]
    wa = ThetaSum(terms=[(c, M.one(), (Theta(M.scalar(Q(u, 1)) * _X),
                                       Theta(M.scalar(Q(u, 1)) * _X.inv())))
                         for u, c in uc])
    assert wa.is_zero is False
    assert wa._is_zero_py() is False


# ─────────────────────────  (3) the (3,3) residue — HONEST decline  ───────────────────


def test_an_3_3_residue_stays_honest_false_with_z6():
    """The rc227 Aₙ (3,3) verify path is UNCHANGED by Z6: the composition cap is unmoved
    (Z6 does not close the (3,3) leaf, so no in-budget certificate justifies raising it),
    and the (3,3) reduction stays the honest ``verified = None`` (too large to decide
    in-budget) — the safe ``is_zero`` direction."""
    from srmech.apokatastasis.elliptic_jackson_an import (multivariate_elliptic_jackson_an,
                                                 _VERIFY_MAX_COMPOSITIONS)
    assert _VERIFY_MAX_COMPOSITIONS == 6                  # cap unmoved: Z6 does not reach it
    z = [M.symbol(f"z{i + 1}") for i in range(3)]
    a = [M.symbol(f"a{j + 1}") for j in range(4)]
    res = multivariate_elliptic_jackson_an(z, a, M.symbol("q"), 3, verify=True)
    assert res["verified"] is None


def _capture_an_3_3_leaf():
    """Descend the REAL rc227 Aₙ (3,3) ``(LHS − closed).is_zero`` recursion and capture the
    FIRST 0-variable all-constant theta leaf it bottoms out on (3 terms × 29 thetas over
    primes {2,5,29,71}), by instrumenting :func:`_decide_struct` to raise on that leaf. The
    recursion consumes all 8 variables (z1..z3, a1..a4, q) via Z4 interpolation before the
    leaf appears, so this is a genuine — if slow — extraction of the #695/#833 residue."""
    from srmech.apokatastasis import thetasum as _ts
    from srmech.apokatastasis.elliptic_jackson_an import (multivariate_elliptic_jackson_an,
                                                 _an_lhs_thetasum)

    captured = {}
    orig = _ts._decide_struct

    class _Got(Exception):
        pass

    def _patched(terms, offset=0, depth=0, **kw):
        t2 = _ts._struct_combine(terms)
        if t2:
            syms = _ts._struct_variables(t2)
            live = [v for v in sorted(syms)
                    if max(sum(a.exp_of(v) ** 2 for a in args) for _p, args in t2) != 0]
            if (not live and len(t2) >= 2
                    and all(all(set(a.exps.keys()) <= {"p"} for a in args)
                            for _p, args in t2)):
                captured["leaf"] = list(t2)
                raise _Got()
        return orig(terms, offset, depth, **kw)

    z = [M.symbol(f"z{i + 1}") for i in range(3)]
    a = [M.symbol(f"a{j + 1}") for j in range(4)]
    closed = multivariate_elliptic_jackson_an(z, a, M.symbol("q"), 3, verify=False)
    residual = _an_lhs_thetasum(z, a, M.symbol("q"), 3) - ThetaSum.from_ellratio(closed)
    _ts._decide_struct = _patched
    try:
        residual._is_zero_interpolation()
    except _Got:
        pass
    finally:
        _ts._decide_struct = orig
    return captured.get("leaf")


def test_z6_declines_the_real_3_3_residue_leaf():
    """The HEADLINE, HONEST answer: Z6 does NOT close the rc227 Aₙ (3,3) residue. The REAL
    0-variable leaf it bottoms out on (3 terms × 29 thetas over primes {2,5,29,71}, the
    25-dim-kernel high-rank residue) is NOT an independent-seam sum — no bounded subset
    re-grading exposes a ±-pair collapse — so BOTH Z5 and Z6 DECLINE it, and Z6 declines
    FAST (bounded ±-pair reductions, no interpolation, no hang). It stays the correct
    ``is_zero = False``; closing it needs the higher Riemann-quartic / Sogo-n=3 rung."""
    leaf = _capture_an_3_3_leaf()
    if leaf is None:                                      # recursion shape changed upstream
        pytest.skip("could not capture the (3,3) constant leaf")
    assert len(leaf) == 3                                 # 3 terms — the residue shape
    assert max(len(args) for _p, args in leaf) == 29      # 29 thetas per term
    assert set(_leaf_prime_set(leaf)) == {2, 5, 29, 71}   # the residue's four primes
    assert _z5_theta_constant_zero(leaf) is False         # Z5 declines (single seam)
    t0 = time.time()
    assert _z6_theta_constant_zero(leaf) is False         # Z6 DECLINES — the honest residual
    assert time.time() - t0 < 5.0                         # bounded, no hang


# ─────────────────────────  (4) native == pure on the Z6 corpus  ──────────────────────


@pytest.mark.skipif(not _native.has_native_thetasum_interpolation(),
                    reason="native structural-certificate peer not loaded")
def test_z6_native_equals_pure():
    """The dispatched (native) verdict EQUALS the pure certificate bool on every Z6 object —
    the rc235 extension of the rc210 corpus-parity contract. The Z6 leaves are TOP-LEVEL
    all-constant objects (n_syms = 0); rc255 the native peer DECIDES them directly (reserves
    synthetic lift + p slots and runs the Z5/Z6 constant-leaf certificates) instead of
    declining — so native == pure holds AND the Z6 zeros are PROVEN True by native, not
    merely deferred (int64-overflow coeffs still decline → None, sound)."""
    corpus = [
        (_A + _B, True),                                  # Z6 True (rank-2)
        (_A + _B + _C, True),                             # Z6 True (rank-3)
        ((_A + _B) + ThetaSum.one(), False),              # perturbed → False
        (_scale_first_term(_A, Fraction(2, 1)) + _B, False),   # broken → False
        (_seam(2, 5, 7, 3), True),                        # Z5 True (single seam)
    ]
    for ts, expect in corpus:
        if not ts.terms:
            continue
        cv = ts._is_zero_interpolation_c()
        pv = ts._is_zero_interpolation()
        if cv is not None:
            assert cv == pv, f"NATIVE≠PURE (BLOCKER): c={cv} py={pv} terms={len(ts.terms)}"
            # rc255: native now PROVES these constant leaves (a bool, not a decline).
            assert cv is expect, f"native verdict {cv} != expected {expect}"
        assert ts.is_zero == ts._is_zero_py()
        # rc255 completeness: native decides (never declines) these int64-fitting leaves.
        assert cv is expect, f"native declined (None) where rc255 must decide {expect}"
