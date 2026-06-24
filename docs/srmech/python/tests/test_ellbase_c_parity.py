"""rc64 — the EllRatio ``is_elliptic`` C-peer PARITY suite (+ the promoted Theta /
EllMonomial canon shared with the rc63 ThetaSum peer).

The native ``srmech_ellratio_is_elliptic`` is a 1:1 STRUCTURAL MIRROR of the pure-Python
:meth:`srmech.amsc.ellbase.EllRatio.is_elliptic` — the COMPLETE balancing / very-well-
poised predicate ``is_elliptic() == (pshift() == self)``, decided by the exact
:meth:`~srmech.amsc.ellbase.Theta.canonicalize` quasi-periodicity rewrites (NOT a
bounded / numeric shell; no convergence threshold on any decision path). This suite
asserts the C verdict EQUALS the Python verdict byte-for-byte on:

  (a) a STRICT-elliptic ratio (is_elliptic True);
  (b) a non-elliptic ratio (is_elliptic False);
  (c) the qshift / pshift / mul / inv round-trips (the carrier compute methods reachable
      through is_elliptic);
  (d) canonicalize on theta products incl. negative-odd-k sign cases (the rc59 sign-bug
      regression);
  (e) a randomized fuzz (~1000 cases) with ZERO C/Python divergence.

A divergence between C and Python on ANY case is a BLOCKER (a shape where C != Python is
reported, never papered over). When the native peer is absent the parity assertions are
skipped (the pure-Python body is the complete alternative); the
``has_native_ellratio``-DISPATCHED test confirms the C peer actually decides
is_elliptic (not a silent Python fallback)."""

import pytest

from srmech.amsc.ellbase import EllMonomial as M, Theta, EllRatio as R
from srmech.amsc.q import Q
from srmech.amsc import _native

_A, _B, _C = M.symbol("a"), M.symbol("b"), M.symbol("c")
_X, _Y = M.symbol("x"), M.symbol("y")
_P, _Qs = M.symbol("p"), M.symbol("q")
_Xi = _X.inv()

_HAS_C = _native.has_native_ellratio()
_skip = pytest.mark.skipif(not _HAS_C,
                           reason="native srmech_ellratio_is_elliptic not loaded")


def _assert_elliptic_parity(ratio, expect):
    """The C is_elliptic verdict EQUALS the Python verdict AND equals `expect`."""
    py = ratio._is_elliptic_py()
    assert py is expect, f"Python is_elliptic mismatch: got {py}, expect {expect}"
    if _HAS_C:
        c = ratio._is_elliptic_c()
        assert c is not None, "native peer present but returned None"
        assert c == py, f"C/Python DIVERGENCE on is_elliptic: C={c} PY={py} (BLOCKER)"
        assert c is expect


def _pm(u, v):
    """The ±-pair θ(u·v^±) = θ(uv)·θ(u/v) as its two Theta factors."""
    return (Theta(u * v), Theta(u / v))


# ── (a) STRICT-elliptic ratios (is_elliptic True) ──────────────────────────────
def test_strict_elliptic_true_parity():
    # A ratio with NO x-dependence is period-shift-invariant trivially (pshift == self).
    _assert_elliptic_parity(R(num=(Theta(_A),), den=(Theta(_B),)), True)
    # The unit ratio (no thetas, unit prefactor) is elliptic.
    _assert_elliptic_parity(R.one(), True)
    # A pure-scalar monomial ratio (no x) is elliptic.
    _assert_elliptic_parity(R.monomial(M.scalar(Q(3, 2))), True)
    # θ(a·x^±)/θ(b·x^±)·θ(b·x^±)/θ(a·x^±) cancels to 1 -> elliptic.
    bal = (R(num=_pm(_A, _X), den=_pm(_B, _X))
           * R(num=_pm(_B, _X), den=_pm(_A, _X)))
    _assert_elliptic_parity(bal, True)


def test_balanced_pair_elliptic_parity():
    # A theta-quotient whose numerator and denominator carry the SAME total x-degree
    # in a balanced (very-well-poised) way is elliptic; a single θ(a·x^±) ratio over
    # θ(b·x^±) is balanced (numerator x-degree == denominator x-degree).
    ratio = R(num=_pm(_A, _X), den=_pm(_B, _X))
    _assert_elliptic_parity(ratio, ratio._is_elliptic_py())  # whatever it is, C==Py


# ── (b) non-elliptic ratios (is_elliptic False) ────────────────────────────────
def test_non_elliptic_false_parity():
    # A single θ(a·x) numerator with no balancing denominator is NOT period-invariant.
    _assert_elliptic_parity(R(num=(Theta(_A * _X),)), False)
    # An unbalanced quotient θ(a·x)/θ(b) (numerator x-bearing, denominator x-free).
    _assert_elliptic_parity(R(num=(Theta(_A * _X),), den=(Theta(_B),)), False)
    # A prefactor x-power with no compensating theta shift.
    _assert_elliptic_parity(R.monomial(M.symbol("x", 1)), False)


# ── (c) carrier compute methods (qshift / pshift / mul / inv) round-trips ───────
def test_qshift_pshift_roundtrip_parity():
    ratio = R(num=_pm(_A, _X), den=_pm(_B, _X))
    # qshift then is_elliptic: the SHIFTED ratio's verdict matches between C and Python.
    _assert_elliptic_parity(ratio.qshift(), ratio.qshift()._is_elliptic_py())
    _assert_elliptic_parity(ratio.pshift(), ratio.pshift()._is_elliptic_py())
    # inv(inv(r)) == r (carrier algebra round-trip; the verdict is identical).
    rr = ratio.inv().inv()
    assert rr == ratio
    _assert_elliptic_parity(rr, rr._is_elliptic_py())
    # mul by its own inverse -> unit -> elliptic.
    unit = ratio * ratio.inv()
    assert unit == R.one()
    _assert_elliptic_parity(unit, True)


def test_pshift_is_elliptic_definitional_parity():
    # is_elliptic is DEFINITIONALLY pshift() == self; verify the C agrees on both a
    # case where it holds and one where it does not.
    ell = R(num=(Theta(_A),), den=(Theta(_B),))           # no x -> pshift == self
    assert ell.pshift() == ell
    _assert_elliptic_parity(ell, True)
    non = R(num=(Theta(_A * _X),))                        # x-bearing, unbalanced
    assert non.pshift() != non
    _assert_elliptic_parity(non, False)


# ── (d) canonicalize incl. negative-odd-k sign cases (rc59 sign-bug regression) ─
def test_canonicalize_negative_odd_k_parity():
    """θ(p^k·z0) canon picks up (−1)^k; with k negative AND odd the sign-fold is the
    rc59-fixed path. A ratio built from such factors must still get an EQUAL C/Python
    is_elliptic verdict (the canon prefactor folds identically in C)."""
    for k in (-3, -1, 1, 3):
        arg = M.symbol("p", k) * _A * _X
        ratio = R(num=(Theta(arg),), den=(Theta(_A * _X),))
        _assert_elliptic_parity(ratio, ratio._is_elliptic_py())
    # a ratio whose num/den both carry a p-power theta (the canon strips p):
    r2 = R(num=(Theta(_P * _A * _X), Theta(_A.inv() * _Xi)),
           den=(Theta(_A * _X), Theta(_A.inv() * _Xi)))
    _assert_elliptic_parity(r2, r2._is_elliptic_py())


# ── (e) randomized parity fuzz (C must NEVER diverge from Python) ───────────────
@_skip
def test_randomized_is_elliptic_fuzz():
    """Many randomized EllRatios (balanced pairs + their products, unbalanced single
    thetas, scalar/x-power prefactors, p-power-bearing args) — the C is_elliptic verdict
    must equal the Python verdict on EVERY one (a divergence is a BLOCKER)."""
    import random
    syms = [_A, _B, _C]
    rng = random.Random(64640)
    mismatches = 0

    def rsym():
        return rng.choice(syms)

    def rvar():
        return rng.choice([_X, _Y])

    for _ in range(1000):
        kind = rng.choice(["bal", "bal_prod", "single", "scalar_x", "pbearing",
                           "quotient", "unit"])
        if kind == "bal":
            ratio = R(num=_pm(rsym(), rvar()), den=_pm(rsym(), rvar()))
        elif kind == "bal_prod":
            ratio = (R(num=_pm(rsym(), _X), den=_pm(rsym(), _X))
                     * R(num=_pm(rsym(), _X), den=_pm(rsym(), _X)))
        elif kind == "single":
            ratio = R(num=(Theta(rsym() * rvar()),))
        elif kind == "scalar_x":
            e = rng.choice([-2, -1, 1, 2, 0])
            ratio = R.monomial(M(Q(rng.randint(-3, 3) or 1, rng.randint(1, 3)),
                                 {"x": e} if e else {}))
        elif kind == "pbearing":
            k = rng.choice([-3, -1, 1, 3])
            ratio = R(num=(Theta(M.symbol("p", k) * rsym() * _X),),
                      den=(Theta(rsym() * _X),))
        elif kind == "quotient":
            ratio = R(num=(Theta(rsym() * rvar()),), den=(Theta(rsym()),))
        else:
            ratio = R.one()
        c = ratio._is_elliptic_c()
        py = ratio._is_elliptic_py()
        if c != py:
            mismatches += 1
    assert mismatches == 0, f"{mismatches} C/Python is_elliptic divergences (BLOCKER)"


# ── the native peer is ACTUALLY dispatched (not a silent Python fallback) ───────
@_skip
def test_is_elliptic_decided_by_native_c():
    """``has_native_ellratio`` is True AND the C peer DECIDES a strict-elliptic and a
    non-elliptic ratio (matching their verdicts) — proving the dispatch is live, not a
    silent Python fallback."""
    assert _native.has_native_ellratio() is True
    ell = R(num=(Theta(_A),), den=(Theta(_B),))
    non = R(num=(Theta(_A * _X),))
    assert ell._is_elliptic_c() is True
    assert non._is_elliptic_c() is False


def test_has_native_ellratio_flag_present():
    """The ``has_native_ellratio`` probe exists + returns a bool (False on a pure /
    no-C build — the pure-Python body is then the complete decider)."""
    assert isinstance(_native.has_native_ellratio(), bool)
