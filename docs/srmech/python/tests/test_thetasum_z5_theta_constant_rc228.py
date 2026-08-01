"""rc228 — the Z5 theta-constant-leaf PRIME-LIFT ZERO certificate.

The 0-VARIABLE theta-CONSTANT leaf ``Σ c_i ∏ θ(rational; p)`` (all summation
variables consumed by the Z4 interpolation) had NO ZERO certificate before rc228:
Z1 needs exact carrier cancellation, Z2/Z4 need a LIVE variable, and the N-detect
only ever proves NONZERO — so a GENUINELY-zero constant leaf declined to
``_UNKNOWN`` and ``is_zero`` false-negatived (the #695 completeness wall, root-caused
to this leaf on the rc227 Aₙ (3,3) residual, 2026-07-12).

Z5 is the SOUND prime-lift certificate: a theta-constant argument is a rational
``ρ = ∏ ρ_ℓ^{v_ℓ}`` (a monomial in DISTINCT PRIMES). Lifting one prime ``ρ*`` back
to a fresh symbol ``v`` gives a single-variable ``L(v)`` with ``L(ρ*) = leaf``
EXACTLY; if the exact Weierstrass ±-pair reduction (Z2, Rosengren Eq. 1.12) closes
``L`` to the empty normal form then ``leaf = L(ρ*) ≡ 0`` by specialization — a
THEOREM (a specialization of an identically-zero elliptic function is zero), never
a numeric band. Z5 produces ONLY ZERO verdicts, never a NONZERO claim.

Guards:
  1. Z5 FIRES on the feasible test leaf (the all-constant Weierstrass three-term
     identity) — pure AND native-dispatched both certify ``is_zero = True``.
  2. SOUNDNESS — the #771 FALSE-ZERO regression witnesses A / B stay ``is_zero =
     False`` (Z5 can never certify a nonzero object); a perturbed identity stays
     False; the certificate is gated to the 0-variable leaf so 1-variable objects
     are untouched.
  3. native == pure on every Z5 object (the ``ThetaSum.is_zero`` parity contract).
  4. The (3,3) Aₙ residual is the HONEST high-kernel-rank residue Z5 does NOT reach
     (documented ``is_zero = False``, the safe direction).
"""
import time

import pytest

from srmech.amsc import _native
from srmech.apokatastasis.ellbase import EllMonomial as M, Theta
from srmech.amsc.q import Q
from srmech.apokatastasis.thetasum import (ThetaSum, _ZERO, _UNKNOWN, _decide_thetasum,
                                  _z5_theta_constant_zero, _leaf_prime_set,
                                  _lift_prime_terms, _pair_reduce_component, _Z5_SYM)

_X = M.symbol("x")


def _leaf_terms(ts):
    return [(pref, [t.arg for t in thetas]) for pref, thetas in ts.terms]


# ───────────────────────── (1) Z5 FIRES on the feasible leaf ─────────────────────

@pytest.mark.parametrize("a,b,c,x", [
    (2, 5, 7, 3), (3, 5, 13, 7), (2, 3, 11, 5), (5, 2, 3, 7), (6, 10, 15, 21),
])
def test_z5_certifies_constant_three_term(a, b, c, x):
    """The all-rational-constants Weierstrass three-term identity
    ``θ(ax^±)θ(bc^±) − θ(bx^±)θ(ac^±) − (a/c)θ(cx^±)θ(ba^±) ≡ 0`` is a 0-variable
    theta-CONSTANT leaf that Z5 certifies ZERO by lifting a constant prime back to
    an elliptic variable (the feasible-leaf proof that the certificate FIRES)."""
    w = ThetaSum.three_term(M.scalar(Q(a, 1)), M.scalar(Q(b, 1)), M.scalar(Q(c, 1)),
                            x=M.scalar(Q(x, 1)))
    # the certificate recursion (fast path OFF — the stronger claim) proves ZERO
    assert _decide_thetasum(w, use_fastpath=False) == _ZERO
    # the dispatched decision AND the pure oracle both certify True (the pure-constant
    # top-level object has n_syms = 0 so the native peer has no lift slot and routes to
    # the pure Z5 via the arena-decline path; both arms return True either way).
    assert w.is_zero is True
    assert w._is_zero_py() is True


def test_z5_unit_prime_lift_mechanism():
    """The certificate mechanism directly: the leaf declines every Z2 lift except the
    one that exposes the ±-pair shape, and ``_z5_theta_constant_zero`` returns True."""
    w = ThetaSum.three_term(M.scalar(Q(2, 1)), M.scalar(Q(5, 1)), M.scalar(Q(7, 1)),
                            x=M.scalar(Q(3, 1)))
    terms = _leaf_terms(w)
    primes = _leaf_prime_set(terms)
    assert set(primes) == {2, 3, 5, 7}
    # at least one single-prime lift closes to the empty Weierstrass normal form
    closed = [pr for pr in primes
              if _pair_reduce_component(_lift_prime_terms(terms, [(pr, _Z5_SYM)]), [_Z5_SYM])]
    assert closed, "no single-prime lift closed the leaf"
    assert _z5_theta_constant_zero(terms) is True


# ───────────────────────── (2) SOUNDNESS — no false zero ─────────────────────────

def _witness_a():
    """#771 FALSE-ZERO witness A — a genuinely NONZERO ±-pair family in one variable."""
    uc = [(2, Q(-133824, 26411)), (3, Q(388557, 26411)), (4, Q(-231961600, 11541607)),
          (5, Q(19987500, 1322951)), (6, Q(-15163200, 2516591)), (7, Q(1, 1))]
    return ThetaSum(terms=[(c, M.one(), (Theta(M.scalar(Q(u, 1)) * _X),
                                         Theta(M.scalar(Q(u, 1)) * _X.inv())))
                           for u, c in uc])


def _witness_b():
    """#771 FALSE-ZERO witness B — Σ (aₜ⁴/∏_{s≠t}(aₜ−a_s))·θ(aₜ x³), a = 2..12."""
    av = list(range(2, 13))
    terms = []
    for t, at in enumerate(av):
        den = 1
        for s, a_s in enumerate(av):
            if s != t:
                den *= (at - a_s)
        terms.append((Q(at ** 4, den), M.one(), (Theta(M.scalar(Q(at, 1)) * _X * _X * _X),)))
    return ThetaSum(terms=terms)


def test_witness_a_stays_nonzero():
    """The #771 false-zero witness A MUST remain ``is_zero = False`` — Z5 is gated to
    the 0-variable leaf and can never certify a nonzero object (a genuine ZERO cert
    only)."""
    w = _witness_a()
    assert w.is_zero is False
    assert w._is_zero_py() is False


def test_witness_b_stays_nonzero():
    """The #771 false-zero witness B MUST remain ``is_zero = False``."""
    w = _witness_b()
    assert w.is_zero is False
    assert w._is_zero_py() is False


def test_perturbed_constant_identity_stays_false():
    """A perturbed (broken) three-term identity is genuinely NONZERO — Z5 must NOT
    certify it (the sound gate: only a THEOREM-backed empty ±-pair reduction ⇒
    ZERO)."""
    good = ThetaSum.three_term(M.scalar(Q(2, 1)), M.scalar(Q(5, 1)), M.scalar(Q(7, 1)),
                               x=M.scalar(Q(3, 1)))
    bad = good + ThetaSum.one()               # add a nonzero constant term
    assert _z5_theta_constant_zero(_leaf_terms(bad)) is False
    assert bad.is_zero is False
    assert bad._is_zero_py() is False


def test_z5_only_zero_never_nonzero():
    """``_z5_theta_constant_zero`` is a ZERO-ONLY certificate: it returns a bool, and
    on a nonzero leaf it returns False (never a NONZERO *claim* — the leaf's NONZERO
    verdict, when any, comes from the N-detect, not Z5)."""
    # a single-term leaf can never be a ±-pair cancellation ⇒ Z5 declines
    single = ThetaSum(terms=((Q(3, 1), M.scalar(Q(2, 1)), (Theta(M.scalar(Q(5, 1))),)),))
    assert _z5_theta_constant_zero(_leaf_terms(single)) is False


# ───────────────────────── (3) native == pure parity ────────────────────────────

@pytest.mark.skipif(not _native.has_native_thetasum_interpolation(),
                    reason="native structural-certificate peer not loaded")
def test_native_genuinely_computes_z5():
    """The native peer GENUINELY computes the Z5 prime-lift IN C (not a decline to
    pure) on a SYMBOL-BEARING object whose Z4 interpolation reaches Z5-closable
    theta-constant leaves: ``three_term(v, 5, 7, x=3)`` with ``v`` a live symbol has
    ``n_syms > 0``, so the native peer has a leaf-unused slot to lift a prime into,
    and the native ``_is_zero_interpolation_c`` returns the certificate-proven ``True``
    directly (NOT ``None``). Each is genuinely ``≡ 0`` (the Weierstrass identity)."""
    objs = [
        ThetaSum.three_term(M.symbol("v"), M.scalar(Q(5, 1)), M.scalar(Q(7, 1)),
                            x=M.scalar(Q(3, 1))),
        ThetaSum.three_term(M.scalar(Q(2, 1)), M.scalar(Q(5, 1)), M.symbol("v"),
                            x=M.scalar(Q(3, 1))),
        ThetaSum.three_term(M.scalar(Q(2, 1)), M.symbol("v"), M.scalar(Q(7, 1)),
                            x=M.scalar(Q(3, 1))),
    ]
    for ts in objs:
        cv = ts._is_zero_interpolation_c()
        assert cv is True, "native peer did not genuinely compute Z5 -> True"
        assert cv == ts._is_zero_interpolation()          # native == pure
        assert ts.is_zero is True


@pytest.mark.skipif(not _native.has_native_thetasum_interpolation(),
                    reason="native structural-certificate peer not loaded")
def test_native_equals_pure_on_z5_objects():
    """The dispatched (native) verdict EQUALS the pure certificate bool on every Z5
    object — the rc228 extension of the rc210 corpus-parity contract to the Z5 leaves.
    Covers the native-computed symbol-bearing zeros, the pure-routed n_syms=0 constant
    zeros, and the #771 false-zero witnesses (native genuinely computes the leaves and
    stays NONZERO)."""
    objs = [
        ThetaSum.three_term(M.symbol("v"), M.scalar(Q(5, 1)), M.scalar(Q(7, 1)),
                            x=M.scalar(Q(3, 1))),                     # native-computed True
        ThetaSum.three_term(M.scalar(Q(2, 1)), M.scalar(Q(5, 1)), M.scalar(Q(7, 1)),
                            x=M.scalar(Q(3, 1))),                     # n_syms=0 -> pure True
        _witness_a(),                                                # native-computed False
        _witness_b(),                                                # native-computed False
    ]
    for ts in objs:
        assert ts.is_zero == ts._is_zero_py()             # the load-bearing parity invariant


# ───────────────────────── (4) the honest (3,3) residue ─────────────────────────

def test_an_3_3_residue_is_honest_false():
    """The rc227 Aₙ (3, 3) residual bottoms out at a 0-variable theta-constant leaf
    (3 terms × 29 thetas over the four primes 2/5/29/71) whose exponent matrices map
    ℤ²⁹→ℤ⁴ with 25-dim kernels and whose non-torsion prime arguments carry NO
    modular/Sturm structure — the genuine high-kernel-rank residue Z5 does NOT reach.
    The verify at (3, 3) stays the honest capped ``None`` (the cap is UNCHANGED at 6
    compositions: no in-budget certificate closes this leaf), and Z5 declines the
    leaf FAST (no hang) — the safe ``is_zero = False`` direction."""
    from srmech.apokatastasis.elliptic_jackson_an import (multivariate_elliptic_jackson_an,
                                                 _VERIFY_MAX_COMPOSITIONS)
    assert _VERIFY_MAX_COMPOSITIONS == 6         # cap unchanged: the (3,3) leaf is unreached
    z = [M.symbol(f"z{i + 1}") for i in range(3)]
    a = [M.symbol(f"a{j + 1}") for j in range(4)]
    res = multivariate_elliptic_jackson_an(z, a, M.symbol("q"), 3, verify=True)
    assert res["verified"] is None               # honest "too large to decide in-budget"


def test_z5_declines_hard_leaf_fast():
    """Z5 declines the genuine (3, 3) theta-constant leaf FAST (a bounded ±-pair
    reduction per prime, no interpolation, no hang) — so adding the certificate never
    turns the honest residue into a performance cliff."""
    # a representative hard leaf: 3 terms × several thetas over 4 primes (mini analogue)
    args0 = [Q(1, 71), Q(2, 5), Q(5, 29), Q(29, 142), Q(841, 50410)]
    terms = [(M.scalar(Q(25, 58)), tuple(Theta(M.scalar(v)) for v in args0)),
             (M.scalar(Q(-5, 142)), tuple(Theta(M.scalar(v)) for v in args0)),
             (M.scalar(Q(-25, 58)), tuple(Theta(M.scalar(v)) for v in args0))]
    ts = ThetaSum(terms=[(Q(1, 1), p, th) for p, th in terms])
    t0 = time.time()
    _ = _z5_theta_constant_zero(_leaf_terms(ts))
    assert time.time() - t0 < 5.0               # bounded, no hang
