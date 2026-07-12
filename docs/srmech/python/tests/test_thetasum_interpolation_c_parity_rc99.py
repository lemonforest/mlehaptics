"""rc99 — the ThetaSum ``is_zero`` STRUCTURAL-INTERPOLATION C-peer FULL-PARITY suite.

The native ``srmech_thetasum_is_zero_interpolation`` is the COMPLETE multi-variable
elliptic decision — a 1:1 STRUCTURAL MIRROR of the pure-Python
:meth:`srmech.amsc.thetasum.ThetaSum._is_zero_interpolation` (Rosengren
arXiv:1608.06161v3 Prop 1.6.1 / eq 1.22 + Cor 1.3.5; MPM-verified in
:mod:`srmech.amsc.thetasum`). Unlike the rc63 ±-pair peer (SOUND fast path only),
this peer's verdict is trusted DIRECTLY — True AND False — so this suite asserts
FULL parity ``c == py`` (not just the no-false-accept invariant):

  (1) the Weierstrass three-term identity + a broken variant;
  (2) THE COMPLETION — Warnaar's Cₙ elliptic ``Lemma 2.2`` (the cross-variable ``√a``
      obstruction the whole rc98/rc99 arc exists to decide) + perturbations;
  (3) SOUNDNESS — single-term theta products are never proved ≡0;
  (4) a randomized fuzz of ≥300 mixed identity / non-identity cases where the C
      interpolation verdict EQUALS the Python interpolation verdict on EVERY case.

A divergence between a NON-None C verdict and Python on ANY case is a BLOCKER. The C
peer may return ``None`` (declining to the pure oracle) only on a genuine
``SRMECH_ERR_OVERFLOW`` size-guard trip; those cases are counted but never a mismatch.
When the native peer is absent every parity assertion is skipped (the pure-Python body
is the complete alternative)."""

import random

import pytest

from srmech.amsc import ThetaSum
from srmech.amsc.ellbase import EllMonomial as M, Theta, EllRatio as R
from srmech.amsc.q import Q
from srmech.amsc import _native

_A, _B, _C, _D = M.symbol("a"), M.symbol("b"), M.symbol("c"), M.symbol("d")
_X, _Y = M.symbol("x"), M.symbol("y")


# ── the Warnaar Cₙ elliptic Lemma 2.2 (n=2) residual — reconstructed from the rc98
# keystone (Rosengren, *A proof of a multivariable elliptic summation formula
# conjectured by Warnaar*, arXiv:math/0101073, eq (6)) — the cross-variable identity
# whose ±-pair midpoint carries the √a obstruction, so ONLY the interpolation decides it.
def _lemma22_cert():
    a, b, c, d, X, Y = _A, _B, _C, _D, _X, _Y

    def qp(k):
        return M.symbol("q", k)

    q = qp(1)
    e = a * a * q * (b * c * d).inv()
    xs = [X, Y]

    def th(m):
        return Theta(m)

    def term(k1, k2):
        ks = [k1, k2]
        num, den = [], []
        for i in range(2):
            xi, ki = xs[i], ks[i]
            if ki == 1:
                for u in (b, c, d, e):
                    num.append(th(u * xi))
                for u in (b, c, d, e):
                    den.append(th(a * q * xi * u.inv()))
        num.append(th(qp(k1 - k2) * X * Y.inv()))
        num.append(th(a * X * Y * qp(k1 + k2)))
        den.append(th(X * Y.inv()))
        den.append(th(a * X * Y * q))
        return R(M.scalar(Q((-1) ** ((k1 + k2) % 2), 1)) * qp(k2), num=num, den=den)

    lhs = ThetaSum.zero()
    for k1 in (0, 1):
        for k2 in (0, 1):
            lhs = lhs + ThetaSum.from_ellratio(term(k1, k2))
    rnum, rden = [], []
    for pr in (b * c, b * d, c * d):
        rnum.append(th(a * q * pr.inv()))
        rnum.append(th(a * pr.inv()))
    for xi in xs:
        rnum.append(th(a * q * xi * xi))
        rden.append(th(a * (b * c * d * xi).inv()))
        rden.append(th(a * q * xi * b.inv()))
        rden.append(th(a * q * xi * c.inv()))
        rden.append(th(a * q * xi * d.inv()))
    rhs = ThetaSum.from_ellratio(R(M.one(), num=rnum, den=rden))
    return lhs - rhs

_HAS_C = _native.has_native_thetasum_interpolation()
_skip = pytest.mark.skipif(
    not _HAS_C, reason="native srmech_thetasum_is_zero_interpolation not loaded")


def _pm(u, v):
    """The plus/minus pair θ(u·v^±) = θ(uv)·θ(u/v) as its two Theta factors."""
    return (Theta(u * v), Theta(u / v))


def _py_interp(ts):
    """The pure-Python interpolation verdict (the parity ORACLE) — ``True`` for an
    empty numerator, else :meth:`ThetaSum._is_zero_interpolation`."""
    return True if not ts._terms else ts._is_zero_interpolation()


def _assert_full_parity(ts, expect):
    """FULL parity (rc99): the pure interpolation verdict EQUALS ``expect``, and a
    NON-None C interpolation verdict EQUALS it too (True AND False). A ``None`` C
    verdict is a legitimate OVERFLOW decline (the pure oracle then decides) — allowed,
    never a mismatch."""
    py = _py_interp(ts)
    assert py is expect, f"Python interpolation mismatch: got {py}, expect {expect}"
    if _HAS_C:
        c = ts._is_zero_interpolation_c()
        assert c is None or c is py, (
            f"C-vs-Python interpolation DIVERGENCE: C={c} PY={py} (BLOCKER)")


# ── (1) the Weierstrass three-term identity + broken variant ───────────────────
def test_three_term_identity_full_parity():
    _assert_full_parity(ThetaSum.three_term(_A, _B, _C), True)
    _assert_full_parity(ThetaSum.three_term(_A, _B, _C, x=_Y), True)
    _assert_full_parity(ThetaSum.three_term(_A, _D, _C), True)


def test_broken_three_term_full_parity():
    broken = ThetaSum(terms=(
        (Q(1, 1), M.one(), _pm(_A, _X) + _pm(_B, _C)),
        (Q(-1, 1), M.one(), _pm(_B, _X) + _pm(_A, _C)),
        (Q(-1, 1), M.one(), _pm(_C, _X) + _pm(_B, _A)),   # weight 1, should be a/c
    ))
    _assert_full_parity(broken, False)


# ── (2) THE COMPLETION — the cross-variable Cₙ identity + perturbations ─────────
def test_lemma22_multivariate_full_parity():
    cert = _lemma22_cert()
    _assert_full_parity(cert, True)


def test_lemma22_perturbations_full_parity():
    cert = _lemma22_cert()
    terms = cert._terms
    pert = ThetaSum(
        terms=tuple((Q(2, 1) if i == 0 else Q(1, 1), pr, th)
                    for i, (pr, th) in enumerate(terms)),
        den_prefactor=cert._den_pref, den_thetas=cert._den_thetas)
    _assert_full_parity(pert, False)
    dropped = ThetaSum(terms=tuple((Q(1, 1), pr, th) for (pr, th) in terms[1:]),
                       den_prefactor=cert._den_pref, den_thetas=cert._den_thetas)
    _assert_full_parity(dropped, False)


# ── (3) SOUNDNESS — single-term products are never proved ≡0 ────────────────────
def test_single_term_products_full_parity():
    prod = ThetaSum(terms=((Q(-1, 2), M.one(),
                            tuple(_pm(_A, M.symbol("f")) + _pm(_B, _C) + _pm(_B, _D)
                                  + _pm(_D, _X))),))
    _assert_full_parity(prod, False)
    _assert_full_parity(ThetaSum(terms=((Q(1, 1), M.one(), _pm(_A, _X)),)), False)
    _assert_full_parity(
        ThetaSum(terms=((Q(1, 1), M.one(), _pm(_A, _X) + _pm(_A, _B)),)), False)
    _assert_full_parity(
        ThetaSum(terms=((Q(1, 1), M.one(), _pm(_A, _X * _X)),)), False)  # even θ(a x²)


# ── (4) randomized FULL-parity fuzz (C interp == Python interp on EVERY case) ────
@_skip
def test_randomized_interpolation_full_parity_fuzz():
    """≥300 randomized ThetaSums (true-zero three-terms + sums, broken variants,
    random theta products, cancelling sums) — the NON-None C interpolation verdict
    EQUALS the Python interpolation verdict on EVERY one (a divergence is a BLOCKER)."""
    syms = ["a", "b", "c", "d", "e", "f"]
    ms = {s: M.symbol(s) for s in syms}
    rng = random.Random(990099)

    def rp():
        return ms[rng.choice(syms)]

    def pmv(u, v):
        return (Theta(u * v), Theta(u / v))

    mism = 0
    decided = 0
    declined = 0
    for _ in range(360):
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
        c = ts._is_zero_interpolation_c()
        py = _py_interp(ts)
        if c is None:
            declined += 1
            continue
        decided += 1
        if c is not py:
            mism += 1
    assert mism == 0, f"{mism} C-vs-Python interpolation DIVERGENCES (BLOCKER)"
    assert decided >= 300, (
        f"only {decided} cases got a native verdict ({declined} declined) — "
        "the peer must actually DECIDE, not always fall back")


# ── the native peer is ACTUALLY dispatched on the keystone (not always None) ────
@_skip
def test_lemma22_decided_by_native_interpolation_c():
    """``has_native_thetasum_interpolation`` is True AND the C peer DECIDES the
    genuine Cₙ Lemma 2.2 residual (== True) — proving the dispatch is live."""
    assert _native.has_native_thetasum_interpolation() is True
    cert = _lemma22_cert()
    assert cert._is_zero_interpolation_c() is True


def test_has_native_thetasum_interpolation_flag_present():
    """The ``has_native_thetasum_interpolation`` probe exists + returns a bool (False
    on a pure / no-C build — the pure-Python interpolation body is then the decider)."""
    assert isinstance(_native.has_native_thetasum_interpolation(), bool)
