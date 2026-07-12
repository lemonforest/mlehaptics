"""rc122 (task #694, anomaly A-1) — the ``is_zero`` FAST-PATH quasi-periodicity-class
KEY hygiene.

``ThetaSum._is_zero_py`` groups the cleared numerator's terms by QUASI-PERIODICITY CLASS
before the ±-pair three-term FAST PATH. The class key used to be the FULL net
period-multiplier monomial :func:`~srmech.amsc.thetasum._net_period_multiplier_exps`
(Rosengren Eq. 1.6 via :meth:`Theta.canonicalize`) — which carries, besides the genuine
period-lattice ``x``/``y`` exponents, the UNIT exponents of the nome ``p``, the base ``q``,
and the elliptic parameters ``a, b, c, …``. Those units are INDEPENDENCE-BLIND (invertible
in the coefficient field ``ℚ(q,p)(params)``), so including them SPLIT one genuine
quasi-periodicity character across buckets (the spurious ``p^{−k(k−1)/2}`` power +
parameter powers).

The fix: the fast path now keys on :func:`~srmech.amsc.thetasum._quasi_period_class_key`,
which keeps ONLY the ``x``/``y`` exponents.

Two guarantees are tested here:

  * THE WITNESS — the key coarsens a REAL over-split (fewer buckets after), for BOTH a
    non-reducible product shape AND a reducible ±-pair shape (so the fix is not confined to
    shapes the fast path can never reduce). The reducible witness ALSO differs in a
    PARAMETER exponent, proving that dropping only ``p`` is insufficient — the genuine
    character is recovered ONLY by keeping ``x``/``y`` alone.

  * VERDICT-INVARIANCE — the key is a fast-path BUCKETING only (:func:`_class_is_zero` is
    exact, a miss defers to the complete :meth:`ThetaSum._is_zero_interpolation`), so every
    ``is_zero`` verdict is UNCHANGED: a true FT/three-term/interpolation zero stays ``True``,
    a non-zero stays ``False``, and ``_is_zero_py`` decides identically under the OLD full
    key and the NEW ``x``/``y`` key.

  * NON-REGRESSION — :func:`_net_period_multiplier_exps` still returns the FULL monomial
    (its ``p``-coordinate is the Class-L p-character block label
    :func:`~srmech.amsc.carrier_spectrum._block_of_thetas` needs); only the fast-path
    CONSUMER was repointed.
"""

from srmech.amsc import ThetaSum
from srmech.amsc.ellbase import EllMonomial as M, Theta, EllRatio as R
from srmech.amsc.q import Q
from srmech.amsc.thetasum import (
    _net_period_multiplier_exps, _quasi_period_class_key, _class_is_zero,
    _recover_pairs, _Y,
)

_A, _B, _C, _D = M.symbol("a"), M.symbol("b"), M.symbol("c"), M.symbol("d")
_X = M.symbol("x")
_YM = M.symbol(_Y)


def _pm(u, v):
    return (Theta(u * v), Theta(u / v))


def _pair(mid, half):
    """θ(mid·half^±) = θ(mid·half)·θ(mid/half) — a clean ±-pair (two Theta factors)."""
    return (Theta(mid * half), Theta(mid * half.inv()))


def _buckets(terms, keyfn):
    d = {}
    for pref, th in terms:
        d.setdefault(keyfn(th), []).append((pref, th))
    return d


def _old_is_zero_py(ts):
    """A faithful reconstruction of ``_is_zero_py`` under the OLD (full-monomial) fast-path
    key — the same two-stage decision, but bucketing on
    :func:`_net_period_multiplier_exps`. Used to prove the key change is verdict-invariant."""
    if not ts._terms:
        return True
    classes = _buckets(ts._terms, _net_period_multiplier_exps)
    if all(_class_is_zero(m) for m in classes.values()):
        return True
    return ts._is_zero_interpolation()


# ── the Warnaar Cₙ Lemma 2.2 (n=2) residual — a genuine cross-variable interpolation zero ──
def _lemma22_cert():
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


# ══════════════════════════ THE WITNESS (fewer buckets after) ══════════════════════════

def test_witness_reducible_pair_over_split_is_coarsened():
    """Two REDUCIBLE ±-pair products of the SAME x-character (x⁻⁴) get DIFFERENT full keys
    (one carries a spurious p-power, the other a spurious p AND parameter power) — so the
    OLD key splits them into 2 buckets; the NEW x/y key merges them into 1."""
    prodA = _pair(_A, _X) + _pair(_B, _X)              # → full (p:-2, x:-4)
    prodB = _pair(_A, _X) + _pair(_B, _X * _A)         # → full (a:-2, p:-3, x:-4)
    ts = ThetaSum(terms=((Q(1, 1), M.one(), prodA), (Q(1, 1), M.one(), prodB)))
    # both terms ARE clean ±-pair products (the shape the fast path reduces)
    for _pref, th in ts._terms:
        assert _recover_pairs(th) is not None
    full = _buckets(ts._terms, _net_period_multiplier_exps)
    xyk = _buckets(ts._terms, _quasi_period_class_key)
    assert len(full) == 2, f"expected the spurious over-split into 2 buckets; got {len(full)}"
    assert len(xyk) == 1, f"the x/y key must merge the genuine character into 1; got {len(xyk)}"
    # the two full keys share the x-character but differ in a UNIT coordinate
    fk = sorted(full.keys())
    assert all(("x", -4) in k for k in fk)
    # dropping ONLY p would NOT merge them — they also differ in the parameter 'a'
    drop_p = {tuple((s, e) for (s, e) in k if s != "p") for k in fk}
    assert len(drop_p) == 2, "dropping only p leaves a parameter split -> keep-only-x/y is required"


def test_witness_nonreducible_over_split_is_coarsened():
    """A non-reducible witness: θ(x⁻⁵) and θ(x⁻³)·θ(x⁻⁴) share the x-character (x⁻²⁵) but the
    full key splits them by p (−15 vs −16). The x/y key merges them (2 → 1 buckets)."""
    ts = ThetaSum(terms=(
        (Q(1, 1), M.one(), (Theta(M.symbol("x", -5)),)),
        (Q(1, 1), M.one(), (Theta(M.symbol("x", -3)), Theta(M.symbol("x", -4)))),
    ))
    full = _buckets(ts._terms, _net_period_multiplier_exps)
    xyk = _buckets(ts._terms, _quasi_period_class_key)
    assert len(full) == 2 and len(xyk) == 1


def test_quasi_period_key_drops_every_unit_symbol():
    """The fast-path key is the x/y-only subset of the full multiplier monomial, and carries
    NO unit symbol (nome p, base q, or any elliptic parameter)."""
    cases = [
        _pair(_A, _X) + _pair(_B, _X * _A),                # p + parameter units
        (Theta(_A * _X), Theta(_B * _X.inv())),            # cross product w/ params
        ThetaSum.three_term(_A, _B, _C).shift_x()._terms[0][1],  # q introduced by the shift
    ]
    for th in cases:
        full = dict(_net_period_multiplier_exps(th))
        key = _quasi_period_class_key(th)
        assert key == tuple((s, e) for (s, e) in sorted(full.items()) if s in ("x", "y"))
        assert all(s in ("x", "y") for (s, _e) in key)
        assert "p" not in dict(key) and "q" not in dict(key)


def test_q_is_introduced_by_shift_and_excluded():
    """The summation shift x↦q·x puts the base ``q`` into the full multiplier monomial;
    the fast-path key must exclude it (q is a ℚ(q,p) unit)."""
    th = ThetaSum.three_term(_A, _B, _C).shift_x()._terms[0][1]
    assert "q" in dict(_net_period_multiplier_exps(th)), "shift should introduce q into the full key"
    assert "q" not in dict(_quasi_period_class_key(th))


# ═══════════════════════════════ VERDICT-INVARIANCE ═══════════════════════════════

def _battery():
    """A battery of ThetaSums (true zeros AND non-zeros, ±-pair AND cross-variable AND the
    over-split witnesses) with their KNOWN is_zero verdicts."""
    r = R(num=(Theta(_A * _X),), den=(Theta(_X),))       # θ(ax)/θ(x)
    ts = ThetaSum.from_ellratio(r)
    broken = ThetaSum(terms=(
        (Q(1, 1), M.one(), _pm(_A, _X) + _pm(_B, _C)),
        (Q(-1, 1), M.one(), _pm(_B, _X) + _pm(_A, _C)),
        (Q(-1, 1), M.one(), _pm(_C, _X) + _pm(_B, _A)),  # weight 1, should be a/c
    ))
    over_red = ThetaSum(terms=(
        (Q(1, 1), M.one(), _pair(_A, _X) + _pair(_B, _X)),
        (Q(1, 1), M.one(), _pair(_A, _X) + _pair(_B, _X * _A)),
    ))
    return [
        (ThetaSum.zero(), True),
        (ThetaSum.one(), False),
        (ThetaSum.three_term(_A, _B, _C), True),
        (ThetaSum.three_term(_A, _B, _C, x=_YM), True),
        (ThetaSum.three_term(_A, _B, _C).shift_x(), True),
        (ThetaSum.three_term(_A, _B, _C, x=M.symbol("x", 2)), True),
        (ts - ts, True),
        (ts + ts, False),
        (ts.scalar_mul(2) - ts - ts, True),
        (broken, False),
        (_lemma22_cert(), True),
        (over_red, False),
    ]


def test_verdict_invariance_known_verdicts():
    """Every known verdict is UNCHANGED under the new fast-path key (True stays True, False
    stays False)."""
    for ts, expected in _battery():
        assert ts.is_zero is expected, f"verdict flipped for {ts!r}: expected {expected}"


def test_verdict_invariance_old_key_vs_new_key():
    """``_is_zero_py`` decides IDENTICALLY under the OLD full-monomial key and the NEW x/y
    key — the KEY change only alters the fast-vs-completion PATH, never the verdict."""
    for ts, _expected in _battery():
        assert ts._is_zero_py() == _old_is_zero_py(ts), (
            f"the key change flipped _is_zero_py for {ts!r}")


def test_lemma22_completion_still_needed_not_falsely_fast_pathed():
    """The cross-variable Lemma 2.2 zero is NOT provable by the ±-pair fast path under either
    key (its √a midpoint blocks pairing) — the interpolation COMPLETION does the work, and
    the coarser key does not spuriously fast-path it."""
    cert = _lemma22_cert()
    xy_fast = all(_class_is_zero(m)
                  for m in _buckets(cert._terms, _quasi_period_class_key).values())
    assert xy_fast is False
    assert cert.is_zero is True


# ═══════════════════════════════ NON-REGRESSION ═══════════════════════════════

def test_net_period_multiplier_exps_still_full_monomial():
    """The shared :func:`_net_period_multiplier_exps` is UNCHANGED — it still returns the FULL
    multiplier monomial INCLUDING the nome p (the carrier_spectrum p-character block label).
    Only the is_zero fast-path consumer was repointed to the unit-stripped key."""
    th = _pair(_A, _X) + _pair(_B, _X)
    full = dict(_net_period_multiplier_exps(th))
    assert "p" in full and full["p"] == -2          # the p-coordinate is still present
    assert "p" not in dict(_quasi_period_class_key(th))
