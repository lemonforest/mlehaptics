"""rc93 — ThetaSum.is_zero is a TOTAL function: a native size-guard trip
(SRMECH_ERR_OVERFLOW on a large / multivariate cleared certificate) never crashes the
decision; it degrades to the exact pure-Python path, and the native provisioning is
sized with headroom for intermediate reduction growth.

Regression for the bug found probing the multivariate Cₙ elliptic row: the
`srmech_thetasum_is_zero` C peer returned non-OK status 4 on a large cleared
certificate (the caller-arena / bigint limb bound was sized to the INPUT coefficients,
but the Weierstrass reduction multiplies them). Fix: (1) `_is_zero_c` catches the native
failure and falls back to `_is_zero_py` (the complete parity oracle); (2) the native
coefficient-limb provisioning gets intermediate-growth headroom. numpy-free.
"""

from srmech.amsc.ellbase import EllMonomial as M, Theta, EllRatio as R, _X, _Q_SYM
from srmech.amsc.thetasum import ThetaSum, _Y


def _big_cross_variable_cert():
    """A large 2-variable cleared certificate (the Rosengren Lemma 2.2, n=2 shape) whose
    cleared numerator tripped the native arena bound — the exact regression case."""
    a = M.symbol("a"); b = M.symbol("b"); c = M.symbol("c"); d = M.symbol("d")
    X = M.symbol(_X); Yv = M.symbol(_Y)

    def qp(k):
        return M.symbol(_Q_SYM, k)

    q = qp(1)
    e = a * a * q * (b * c * d).inv()
    xs = [X, Yv]

    def th(m):
        return Theta(m)

    def term(k1, k2):
        ks = [k1, k2]; num = []; den = []
        for i in range(2):
            xi = xs[i]; ki = ks[i]
            if ki == 1:
                for u in (b, c, d, e):
                    num.append(th(u * xi))
                    den.append(th(a * q * xi * u.inv()))
        num.append(th(qp(k1 - k2) * X * Yv.inv()))
        num.append(th(a * X * Yv * qp(k1 + k2)))
        den.append(th(X * Yv.inv()))
        den.append(th(a * X * Yv * q))
        from srmech.amsc.q import Q
        pref = M.scalar(Q((-1) ** ((k1 + k2) % 2), 1)) * qp(k2)
        return R(pref, num=num, den=den)

    lhs = ThetaSum.zero()
    for k1 in (0, 1):
        for k2 in (0, 1):
            lhs = lhs + ThetaSum.from_ellratio(term(k1, k2))
    return lhs


def test_is_zero_is_total_on_large_cert():
    """The large certificate: is_zero must NOT raise, and must equal the complete
    pure-Python decision (native fast path OR its fallback — both are the SAME verdict)."""
    cert = _big_cross_variable_cert()
    pure = cert._is_zero_py()          # the complete alternative (parity oracle)
    got = cert.is_zero                 # dispatches to C (with fallback); must not raise
    assert got == pure                 # total function: C verdict == pure verdict


def test_known_zero_identity_still_decides_true():
    """No regression: a known-zero identity (the Weierstrass three-term) still decides
    True through the (native) is_zero path."""
    tt = ThetaSum.three_term(M.symbol("a"), M.symbol("b"), M.symbol("c"))
    assert tt.is_zero is True
    assert tt._is_zero_py() is True


def test_known_nonzero_still_decides_false():
    """No regression: a non-identity theta-sum still decides False."""
    a = M.symbol("a"); X = M.symbol(_X)
    ts = ThetaSum(terms=[(1, M.one(), (Theta(a * X),))])   # a single theta, not ≡ 0
    assert ts.is_zero is False
    assert ts.is_zero == ts._is_zero_py()
