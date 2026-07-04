"""#693 — the ThetaSum ``is_zero`` interpolation DEGREE bound is Σe², NOT Σ|e|.

This is a *prover-completeness* (soundness) guard. ``is_zero`` is a zero-PROVER; a bound too
small makes it return ``True`` on a genuinely-non-zero object — a FALSE THEOREM in the elliptic
reduction row. #693 determined the Σe²→Σ|e| tighten is UNSOUND and NOT adopted; the node-count /
p-order band must bound the TRUE elliptic degree (quasi-period index = zeros per annulus) of a
theta-product in the interpolation variable, which is Σe² (a factor θ(c·vᵉ;p) gains multiplier
v^{−e²} under v↦p·v; Rosengren Eq. 1.6 / ellbase.Theta.canonicalize). See
``notes/thetasum_is_zero_degree_bound_693.md``.

This test pins the CURRENT (correct) behavior on the explicit witness, so a future well-meaning
tighten to Σ|e| — under which ``is_zero`` would falsely return ``True`` here — fails loudly.
"""
from srmech.amsc import ThetaSum
from srmech.amsc.ellbase import EllMonomial as M, Theta
from srmech.amsc.q import Q
from srmech.amsc.thetasum import _struct_theta_p, _STRUCT_MARGIN

# The #693 discriminating witness: single variable x, one theta per term, exponent e=3
# (per-term Σ|e|=3 ⇒ k_ABS=5; Σe²=9 ⇒ k_SQ=11). Its true p-adic order is 6, in the gap (5,11].
#   N(x) = 2·θ(2x³) −27·θ(3x³) +120·θ(4x³) −250·θ(5x³) +270·θ(6x³) −147·θ(7x³) +32·θ(8x³)   (all ;p)
_CE_TERMS = ((2, 2), (-27, 3), (120, 4), (-250, 5), (270, 6), (-147, 7), (32, 8))
_E = 3


def _counterexample():
    terms = tuple((Q(c, 1), M.one(), (Theta(M.symbol("x", _E, coeff=Q(t, 1))),))
                  for (c, t) in _CE_TERMS)
    return ThetaSum(terms=terms)


def _lowest_nonzero_coeff(K):
    """Lowest (p_pow, x_exp, coeff) of the exact-ℚ q-expansion of N — an INDEPENDENT non-zero
    witness that does not route through is_zero."""
    total = {}
    for (c, t) in _CE_TERMS:
        for pp, lp in _struct_theta_p(Q(t, 1), _E, K).items():
            dst = total.setdefault(pp, {})
            for xe, vv in lp.items():
                dst[xe] = dst.get(xe, Q(0, 1)) + Q(c, 1) * vv
    for pp in sorted(total):
        for xe in sorted(total[pp]):
            if total[pp][xe] != Q(0, 1):
                return pp, xe, total[pp][xe]
    return None


def test_bands_have_a_real_gap():
    """The two candidate bounds genuinely disagree here (Σ|e| < Σe²), so this object exercises
    the soundness question rather than a case where the tighten is a no-op."""
    sum_abs = _E                 # one theta, |e|=3
    sum_sq = _E * _E             # e² = 9
    k_abs = max(sum_abs - 1, 0) + _STRUCT_MARGIN     # = 5
    k_sq = max(sum_sq - 1, 0) + _STRUCT_MARGIN       # = 11
    assert (sum_abs, sum_sq, k_abs, k_sq) == (3, 9, 5, 11)


def test_witness_is_exactly_nonzero():
    """Independent of is_zero: the exact q-expansion has a non-zero coefficient at (p⁶, x⁻⁹),
    a p-order (6) that sits ABOVE the Σ|e| band (k_ABS=5) and inside the Σe² band (k_SQ=11)."""
    lo = _lowest_nonzero_coeff(K=_E * _E + _STRUCT_MARGIN + 6)
    assert lo is not None, "the witness must not be identically zero"
    p_pow, x_exp, coeff = lo
    assert coeff != Q(0, 1)
    assert (p_pow, x_exp, coeff) == (6, -9, Q(-1, 112))
    # the p-order lands strictly in the gap (k_ABS, k_SQ] = (5, 11]
    assert 5 < p_pow <= 11


def test_shipped_sum_e2_bound_correctly_reports_nonzero():
    """The shipped Σe² bound sees the p⁶ coefficient (k_SQ=11 ≥ 6) → is_zero is False (correct).
    A tighten to Σ|e| (k_ABS=5 < 6) would MISS it and return True — a false theorem. If this
    assertion ever flips to True, the degree bound has been tightened to an UNSOUND Σ|e|."""
    obj = _counterexample()
    assert obj.is_zero is False


def test_moderate_p_eval_confirms_nonzero():
    """A truncation-independent cross-check: at |p|=½ the truncated value STABILISES to a
    non-zero number (a genuine zero would shrink ~|p|^depth → ~5.7e-14 by depth 44)."""
    obj = _counterexample()
    v22 = obj.eval_trunc({"p": Q(1, 2), "x": Q(3, 4)}, 22)
    v44 = obj.eval_trunc({"p": Q(1, 2), "x": Q(3, 4)}, 44)

    def _abs(q):
        return q if q.numerator >= 0 else Q(-q.numerator, q.denominator)

    # both truncation depths give an APPRECIABLE value (~0.18) — decisively non-zero: a genuine
    # zero object would shrink like |p|^depth to ~(1/2)^44 ≈ 5.7e-14, far below 1/100.
    assert _abs(v22) > Q(1, 100)
    assert _abs(v44) > Q(1, 100)
    # and the two depths have CONVERGED (truncated products only match toward ∞, not exactly at
    # finite depth): the depth-22→44 change is < 1e-3, i.e. the value has stabilised, not grown.
    diff = v44 - v22
    assert _abs(diff) < Q(1, 1000)


def test_true_zero_is_preserved():
    """A tighten cannot break a true-zero (fewer checks still see the exact cancellation); the
    Weierstrass three-term identity stays is_zero == True. Recorded for completeness — the #693
    failure is on true-NON-zeros, not here."""
    A, B, C = M.symbol("a"), M.symbol("b"), M.symbol("c")
    assert ThetaSum.three_term(A, B, C).is_zero is True
    assert ThetaSum.three_term(A, B, C, x=M.symbol("x", 2)).is_zero is True
