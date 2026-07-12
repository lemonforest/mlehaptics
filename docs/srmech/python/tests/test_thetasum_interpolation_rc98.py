"""rc98 — the ThetaSum ``is_zero`` STRUCTURAL ELLIPTIC-INTERPOLATION completion.

``_is_zero_py`` is now the COMPLETE multi-variable elliptic decision: the ±-pair three-term
FAST PATH (complete for the single-variable ₈ω₇ class, a proved ``≡0`` returned immediately)
+ the STRUCTURAL INTERPOLATION COMPLETION (:meth:`ThetaSum._is_zero_interpolation`) for the
shapes the ±-pair cannot reach — the cross-variable root-system Cₙ coupling
``θ(x_i/x_j)·θ(a·x_i·x_j)`` whose geometric-mean midpoint ``x_i·√a`` is not a perfect square,
so no pair forms. By the elliptic Lagrange interpolation (Rosengren arXiv:1608.06161 Prop
1.6.1 / eq 1.22 + Cor 1.3.5): interpolate in ONE variable at ``D_v+1`` distinct points
(θ-factor zeros, which kill terms via ``θ(1)=0``, augmented with GLOBALLY-DISTINCT PRIMES so
no two variables collide to a spurious ``θ(1)``), recurse to the single-variable degree-bound.
Exact-ℚ, no q-grid, no float — SOUND (never false-accepts) and COMPLETE.

The keystone identity is Warnaar's Cₙ elliptic ``Lemma 2.2`` (Rosengren, *A proof of a
multivariable elliptic summation formula conjectured by Warnaar*, arXiv:math/0101073, eq (6))
— the cross-variable case the whole rc98 arc exists to decide.
"""

import gc
import random

from srmech.amsc import ThetaSum
from srmech.amsc.ellbase import EllMonomial as M, Theta, EllRatio as R
from srmech.amsc.thetasum import _Y, _VERIFY_POINTS, _VERIFY_TRUNC
from srmech.amsc.q import Q

_A, _B, _C, _D = M.symbol("a"), M.symbol("b"), M.symbol("c"), M.symbol("d")
_X = M.symbol("x")
_YM = M.symbol(_Y)
_QS = M.symbol("q")


def _pm(u, v):
    return (Theta(u * v), Theta(u / v))


# ── the Warnaar Cₙ elliptic Lemma 2.2 (n=2) residual — a genuine cross-variable identity ──
def _lemma22_cert():
    """LHS − RHS of Warnaar's Cₙ Lemma 2.2 at n=2 — a genuine multi-variable elliptic
    identity whose ±-pair midpoint carries the ``√a`` obstruction, so ONLY the interpolation
    completion decides it (``≡0``)."""
    a, b, c, d, X, Y = _A, _B, _C, _D, _X, _YM

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


# ── (1) the ±-pair fast path is UNCHANGED (regression) ─────────────────────────────────
def test_three_term_fast_path_regression():
    assert ThetaSum.three_term(_A, _B, _C).is_zero is True
    assert ThetaSum.three_term(_A, _B, _C, x=_YM).is_zero is True
    # a broken three-term stays nonzero
    broken = ThetaSum(terms=(
        (Q(1, 1), M.one(), _pm(_A, _X) + _pm(_B, _C)),
        (Q(-1, 1), M.one(), _pm(_B, _X) + _pm(_A, _C)),
        (Q(-1, 1), M.one(), _pm(_C, _X) + _pm(_B, _A)),   # weight 1, should be a/c
    ))
    assert broken.is_zero is False


# ── (2) THE COMPLETION — the cross-variable Cₙ identity the ±-pair CANNOT decide ────────
def test_lemma22_multivariate_cn_identity_is_zero():
    cert = _lemma22_cert()
    # the ±-pair fast path alone cannot prove it (cross-variable √a obstruction) ...
    from srmech.amsc.thetasum import _net_period_multiplier_exps, _class_is_zero
    classes = {}
    for pref, th in cert._terms:
        classes.setdefault(_net_period_multiplier_exps(th), []).append((pref, th))
    fast_only = all(_class_is_zero(m) for m in classes.values())
    assert fast_only is False, "the ±-pair should NOT prove Lemma 2.2 (it is the completion's job)"
    # ... but the structural interpolation COMPLETION proves it exactly.
    assert cert._is_zero_interpolation() is True
    assert cert._is_zero_py() is True
    assert cert.is_zero is True


def test_lemma22_perturbations_are_nonzero():
    cert = _lemma22_cert()
    terms = cert._terms
    # scale one term -> breaks the identity -> must be False (SOUND, no false-accept)
    pert = ThetaSum(
        terms=tuple((Q(2, 1) if i == 0 else Q(1, 1), pr, th) for i, (pr, th) in enumerate(terms)),
        den_prefactor=cert._den_pref, den_thetas=cert._den_thetas)
    assert pert.is_zero is False
    # drop one term -> breaks the identity -> False
    dropped = ThetaSum(terms=tuple((Q(1, 1), pr, th) for (pr, th) in terms[1:]),
                       den_prefactor=cert._den_pref, den_thetas=cert._den_thetas)
    assert dropped.is_zero is False


# ── (3) SOUNDNESS — single-term products are nonzero (the distinct-prime-node fix) ──────
def test_single_term_products_are_nonzero():
    # a single non-zero theta product must NEVER be proved ≡0 (the augment-node collision bug:
    # reusing constants made θ(x_i/x_j)|subst = θ(1) a spurious zero; distinct primes fix it).
    prod = ThetaSum(terms=((Q(-1, 2), M.one(),
                            tuple(_pm(_A, M.symbol("f")) + _pm(_B, _C) + _pm(_B, _D)
                                  + _pm(_D, _X))),))
    assert prod.is_zero is False
    # a few more single-term products across shared variables
    assert ThetaSum(terms=((Q(1, 1), M.one(), _pm(_A, _X)),)).is_zero is False
    assert ThetaSum(terms=((Q(1, 1), M.one(), _pm(_A, _X) + _pm(_A, _B)),)).is_zero is False
    assert ThetaSum(terms=((Q(1, 1), M.one(), _pm(_A, _X * _X)),)).is_zero is False  # even θ(a x²)


# ── (4) the completion is SOUND vs an INDEPENDENT eval-truncation oracle ────────────────
def _oracle(ts):
    """genuine ``≡0`` iff the truncated theta-series value is ~0 at every verify point —
    independent of ``is_zero`` (an identity truncates to ~|p|^N, a nonzero sum to O(1))."""
    for pt in _VERIFY_POINTS:
        try:
            v = ts.eval_trunc(pt, _VERIFY_TRUNC)
        except Exception:
            return None
        av = v if v.numerator >= 0 else Q(-v.numerator, v.denominator)
        if av > Q(1, 10 ** 6):
            return False
    return True


def test_interpolation_sound_vs_eval_oracle():
    syms = ["a", "b", "c", "d", "e", "f"]
    ms = {s: M.symbol(s) for s in syms}
    rng = random.Random(20260701)

    def rp():
        return ms[rng.choice(syms)]

    def pmv(u, v):
        return (Theta(u * v), Theta(u / v))

    checked = 0
    for i in range(120):
        var = rng.choice([_X, _YM])
        kind = rng.choice(["tt", "tt_sum", "broken", "rand", "tt_minus", "scaled"])
        if kind == "tt":
            ts = ThetaSum.three_term(rp(), rp(), rp(), x=var)
        elif kind == "tt_sum":
            ts = (ThetaSum.three_term(rp(), rp(), rp(), x=_X)
                  + ThetaSum.three_term(rp(), rp(), rp(), x=_YM))
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
            for _j in range(n):
                facs.extend(pmv(rp(), rng.choice([var, rp()])))
            ts = ThetaSum(terms=((Q(rng.randint(-3, 3) or 1, rng.randint(1, 3)),
                                  M.one(), tuple(facs)),))
        orc = _oracle(ts)
        if orc is None:
            continue
        checked += 1
        assert ts._is_zero_py() is orc, f"case {i} kind={kind}: Python={ts._is_zero_py()} oracle={orc}"
        if i % 30 == 0:
            gc.collect()
    assert checked >= 90, f"only {checked} cases had a usable oracle"
