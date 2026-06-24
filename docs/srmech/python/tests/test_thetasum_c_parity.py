"""rc63 — the ThetaSum ``is_zero`` C-peer PARITY suite.

The native ``srmech_thetasum_is_zero`` is a 1:1 STRUCTURAL MIRROR of the pure-Python
:meth:`srmech.amsc.thetasum.ThetaSum.is_zero` — the EXACT Weierstrass three-term
reduction partitioned by quasi-periodicity class (Rosengren arXiv:1608.06161v3 §1.4
Eq. 1.12 + §1.3 Lemma 1.3.2, MPM-verified in :mod:`srmech.amsc.thetasum`). This suite
asserts the C verdict EQUALS the Python verdict byte-for-byte on:

  (a) the GENUINE theta-telescoper keystone residual ``R(qx)·r − R − 1`` (is_zero=True)
      built from the Weierstrass relation with ``c = qb`` (the closed-branch
      ``_genuine_keystone`` construction) — the case the rc63 ThetaSum exists to decide;
  (b) PERTURBATIONS of that keystone (is_zero=False);
  (c) the zero / one / degenerate-θ(1;p) / odd-single-theta cases;
  (d) the Weierstrass three-term identity + a deliberately-broken variant;
  (e) the quasi-periodicity two-class grouping.

A divergence between C and Python on ANY case is a BLOCKER (sound, never false-accept).
When the native peer is absent the parity assertions are skipped (the pure-Python body
is the complete alternative); the `has_native_thetasum`-DISPATCHED test confirms the C
peer actually decides the keystone (not a silent Python fallback)."""

import pytest

from srmech.amsc import ThetaSum
from srmech.amsc.ellbase import EllMonomial as M, Theta, EllRatio as R
from srmech.amsc.q import Q
from srmech.amsc import _native

_A, _B, _C, _D, _E = (M.symbol("a"), M.symbol("b"), M.symbol("c"),
                      M.symbol("d"), M.symbol("e"))
_X, _Y = M.symbol("x"), M.symbol("y")
_Q = M.symbol("q")
_Xi = _X.inv()

_HAS_C = _native.has_native_thetasum()
_skip = pytest.mark.skipif(not _HAS_C,
                           reason="native srmech_thetasum_is_zero not loaded")


def _pm(u, v):
    """The plus/minus pair θ(u·v^±) = θ(uv)·θ(u/v) as its two Theta factors."""
    return (Theta(u * v), Theta(u / v))


def _pmx(al):
    """The same-α theta ±-pair θ(α·x^±) over the x-summation variable."""
    return (Theta(al * _X), Theta(al * _Xi))


def _assert_parity(ts, expect):
    """The C verdict EQUALS the Python verdict AND equals `expect`."""
    py = ts._is_zero_py()
    assert py is expect, f"Python is_zero mismatch: got {py}, expect {expect}"
    if _HAS_C:
        c = ts._is_zero_c()
        assert c is not None, "native peer present but returned None"
        assert c == py, f"C/Python DIVERGENCE: C={c} PY={py} (BLOCKER)"
        assert c is expect


# ── (a) the GENUINE theta-telescoper keystone (the rc63 capability) ────────────
def _genuine_keystone():
    """The Weierstrass-relation theta telescoper with c = qb (the closed-branch
    ``feat/srmech-rc63-elliptic-gosper-genuine`` ``_genuine_keystone``):
        R(x) = θ(bx^±)θ(ac^±) / [ (a/c)·θ(cx^±)θ(ba^±) ]            (c = qb)
        r    = (R(x) + 1) / R(qx)
    so the elliptic Gosper equation R(qx)·r − R = 1 holds IDENTICALLY; the residual
    R(qx)·r − R − 1 is a genuine SUM/DIFFERENCE of theta-quotients whose is_zero is
    True only via the exact Weierstrass reduction."""
    c = _Q * _B
    Rc = R(prefactor=(_A.inv() * c), num=_pmx(_B) + _pm(_A, c),
           den=_pmx(c) + _pm(_B, _A))
    n_plus_d = R(num=_pmx(_A) + _pm(_B, c))
    d_q = R(prefactor=(_A / c), num=_pmx(c) + _pm(_B, _A)).qshift()
    n_q = R(num=_pmx(_B) + _pm(_A, c)).qshift()
    d_x = R(prefactor=(_A / c), num=_pmx(c) + _pm(_B, _A))
    r = n_plus_d * d_q * (d_x * n_q).inv()
    return r, Rc


def _residual(cert, r):
    return (ThetaSum.from_ellratio(cert.qshift() * r)
            - ThetaSum.from_ellratio(cert) - ThetaSum.one())


def test_genuine_keystone_residual_is_zero_parity():
    """The genuine theta-telescoper residual R(qx)·r − R − 1 ≡ 0 — C verdict equals
    Python verdict equals True (the load-bearing rc63 parity case)."""
    r, cert = _genuine_keystone()
    res = _residual(cert, r)
    # genuinely theta-bearing (not the geometric core): the residual carries thetas.
    assert sum(len(th) for _p, th in res.terms) >= 4
    _assert_parity(res, True)


def test_genuine_keystone_perturbations_are_nonzero_parity():
    """Perturbed (wrong) certificates → residual NOT identically zero — C equals Python
    equals False (never a false-accept)."""
    r, cert = _genuine_keystone()
    # scale the certificate prefactor by 2 (breaks R(qx)·r − R = 1).
    bad1 = cert * M.scalar(Q(2, 1))
    _assert_parity(_residual(bad1, r), False)
    # multiply the prefactor by a parameter monomial.
    bad2 = R(prefactor=cert.prefactor * _A, num=cert.num, den=cert.den)
    _assert_parity(_residual(bad2, r), False)


# ── (b) the Weierstrass three-term identity + broken variant ───────────────────
def test_weierstrass_three_term_identity_parity():
    _assert_parity(ThetaSum.three_term(_A, _B, _C), True)
    _assert_parity(ThetaSum.three_term(_A, _D, _E), True)
    _assert_parity(ThetaSum.three_term(_A, _B, _C, x=_Y), True)


def test_broken_three_term_is_nonzero_parity():
    broken = ThetaSum(terms=(
        (Q(1, 1), M.one(), _pm(_A, _X) + _pm(_B, _C)),
        (Q(-1, 1), M.one(), _pm(_B, _X) + _pm(_A, _C)),
        (Q(-1, 1), M.one(), _pm(_C, _X) + _pm(_B, _A)),   # weight 1, should be a/c
    ))
    _assert_parity(broken, False)


# ── (c) zero / one / degenerate / odd-single-theta ─────────────────────────────
def test_zero_one_degenerate_parity():
    _assert_parity(ThetaSum.zero(), True)
    _assert_parity(ThetaSum.one(), False)
    # an odd single theta is outside the clean ±-pair shape -> honest False.
    odd = ThetaSum(terms=((Q(1, 1), M.one(), (Theta(_A * _X),)),))
    _assert_parity(odd, False)
    # a degenerate θ(1;p) factor in an even product (the unit-monomial argument).
    deg = ThetaSum(terms=((Q(1, 1), M.one(),
                           (Theta(M.one()), Theta(_A * _X))),))
    # decided by the same reduction in C + Python (whatever the verdict, it matches).
    assert deg._is_zero_py() == (deg._is_zero_c() if _HAS_C else deg._is_zero_py())


def test_additive_algebra_parity():
    r = R(num=(Theta(_A * _X),), den=(Theta(_X),))
    ts = ThetaSum.from_ellratio(r)
    _assert_parity(ts - ts, True)
    _assert_parity(ts + ts, False)
    _assert_parity(ts.scalar_mul(2) - ts - ts, True)
    _assert_parity((ThetaSum.one() + Q(2, 1)) - Q(3, 1), True)


# ── (d) quasi-periodicity two-class grouping ───────────────────────────────────
def test_two_class_grouping_parity():
    idx = ThetaSum.three_term(_A, _B, _C)               # x-class identity
    idy = ThetaSum.three_term(_A, _B, _C, x=_Y)         # y-class identity
    _assert_parity(idx + idy, True)                     # both classes vanish
    broken_y = ThetaSum(terms=(
        (Q(1, 1), M.one(), _pm(_A, _Y) + _pm(_B, _C)),
        (Q(-1, 1), M.one(), _pm(_B, _Y) + _pm(_A, _C)),
        (Q(-1, 1), M.one(), _pm(_C, _Y) + _pm(_B, _A)),
    ))
    _assert_parity(idx + broken_y, False)               # one class nonzero


# ── (e) shifts preserve identities ─────────────────────────────────────────────
def test_shift_identities_parity():
    ident = ThetaSum.three_term(_A, _B, _C)
    _assert_parity(ident.shift_x(), True)
    _assert_parity(ident.shift_y(), True)
    _assert_parity(ident.shift_x().shift_x(), True)
    r = R(num=(Theta(_A * _X),), den=(Theta(_X),))
    ts = ThetaSum.from_ellratio(r)
    _assert_parity(ts.shift_x() - ts, False)


# ── randomized parity fuzz (C must NEVER diverge from Python) ───────────────────
@_skip
def test_randomized_parity_fuzz():
    """Many randomized ThetaSums (true-zero three-terms + their sums, broken variants,
    random theta products, θ(1) collapses) — the C verdict must equal the Python verdict
    on EVERY one (a divergence is a BLOCKER)."""
    import random
    syms = ["a", "b", "c", "d", "e", "f"]
    ms = {s: M.symbol(s) for s in syms}
    rng = random.Random(12345)

    def rp():
        return ms[rng.choice(syms)]

    def pmv(u, v):
        return (Theta(u * v), Theta(u / v))

    mismatches = 0
    for _ in range(1500):
        var = rng.choice([_X, _Y])
        kind = rng.choice(["tt", "tt_sum", "broken", "rand", "tt_minus", "scaled"])
        if kind == "tt":
            ts = ThetaSum.three_term(rp(), rp(), rp(), x=var)
        elif kind == "tt_sum":
            ts = (ThetaSum.three_term(rp(), rp(), rp(), x=_X)
                  + ThetaSum.three_term(rp(), rp(), rp(), x=_Y))
        elif kind == "broken":
            a, b, c = rp(), rp(), rp()
            w = rng.choice([Q(1, 1), Q(2, 1), Q(-1, 1), Q(3, 2)])
            ts = ThetaSum(terms=(
                (Q(1, 1), M.one(), pmv(a, var) + pmv(b, c)),
                (Q(-1, 1), M.one(), pmv(b, var) + pmv(a, c)),
                (w, M.one(), pmv(c, var) + pmv(b, a)),
            ))
        elif kind == "tt_minus":
            t = ThetaSum.three_term(rp(), rp(), rp(), x=var)
            ts = t - t
        elif kind == "scaled":
            t = ThetaSum.three_term(rp(), rp(), rp(), x=var)
            ts = t.scalar_mul(3) - t - t - t
        else:
            n = rng.choice([1, 2, 2, 4])
            facs = []
            for _i in range(n):
                facs.extend(pmv(rp(), rng.choice([var, rp()])))
            ts = ThetaSum(terms=((Q(rng.randint(-3, 3) or 1, rng.randint(1, 3)),
                                  M.one(), tuple(facs)),))
        c = ts._is_zero_c()
        py = ts._is_zero_py()
        if c != py:
            mismatches += 1
    assert mismatches == 0, f"{mismatches} C/Python parity divergences (BLOCKER)"


# ── the native peer is ACTUALLY dispatched (not a silent Python fallback) ───────
@_skip
def test_keystone_is_decided_by_native_c():
    """``has_native_thetasum`` is True AND the C peer DECIDES the genuine keystone
    residual (== True) — proving the dispatch is live, not a silent Python fallback."""
    assert _native.has_native_thetasum() is True
    r, cert = _genuine_keystone()
    res = _residual(cert, r)
    assert res._is_zero_c() is True


def test_has_native_thetasum_flag_present():
    """The ``has_native_thetasum`` probe exists + returns a bool (False on a pure /
    no-C build — the pure-Python body is then the complete decider)."""
    assert isinstance(_native.has_native_thetasum(), bool)
