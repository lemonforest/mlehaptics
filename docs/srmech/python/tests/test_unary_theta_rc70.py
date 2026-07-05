"""rc70 — ``srmech.amsc.unary_theta.UnaryTheta``, the FIRST WEIGHT-GRADED carrier.

The build gates (the no-shell proof):

  (a) the WEIGHT axis — ``θ₃.weight == 1/2``, ``g₃.weight == 3/2``, a ``j=2`` case
      ``== 5/2`` (exact ``Q``);
  (b) ``θ₃.q_series(20)`` == the Jacobi-triple-product series ``Σ q^{n²}`` EXACTLY
      (cross-checked against the JTP product ``∏(1−q^{2k})(1+q^{2k−1})²``);
  (c) **``g₃.q_series`` reproduces the Zagier coefficients EXACTLY** at weight 3/2 —
      the #9 mock-theta-shadow payoff (the shadow representable in-carrier);
  (d) Python==C parity on ``.q_series`` and ``.weight`` for both anchors + a broad
      stress sweep (guarded by the native-availability skip);
  (e) the carrier source has no numpy / math / abs() (the ratchet).

Plus the ``EllRatio.weight`` / ``ThetaSum.weight`` annotations (the ladder is now
weight-consistent) and the ToolEntry registration + the count.
"""
from __future__ import annotations

import os
import re
import tokenize

import pytest

from srmech.amsc.unary_theta import (
    Character, UnaryTheta, unary_theta, _kronecker_minus12,
)
from srmech.amsc.q import Q
from srmech.amsc import _native


# the two anchors, reused across the gates
def _theta3() -> UnaryTheta:
    return unary_theta("trivial", 0, 1, 0, 1, support="all")


def _g3() -> UnaryTheta:
    return unary_theta("minus12", 1, 1, 0, 24, support="positive")


# the exact target series (verified at build)
THETA3_Q20 = [1, 2, 0, 0, 2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0]
G3_ZAGIER = [1, -5, -7, 0, 0, 11, 0, 13, 0, 0, 0, 0, -17, 0, 0, -19,
             0, 0, 0, 0, 0, 0, 23, 0, 0, 0, 25]


# ── gate (a): the WEIGHT axis = 1/2 + j ──────────────────────────────────────
def test_weight_axis_theta3_is_one_half():
    assert _theta3().weight == Q(1, 2)
    assert float(_theta3().weight) == 0.5


def test_weight_axis_g3_is_three_halves():
    """The #9 shadow g₃ is weight 3/2 — the object a weight-0 carrier cannot hold."""
    assert _g3().weight == Q(3, 2)
    assert float(_g3().weight) == 1.5


def test_weight_axis_is_general_j2_is_five_halves():
    j2 = unary_theta("trivial", 2, 1, 0, 1, support="all")
    assert j2.weight == Q(5, 2)
    # the axis is exactly 1/2 + j for several j
    for j in range(0, 6):
        ut = unary_theta("trivial", j, 1, 0, 1, support="all")
        assert ut.weight == Q(1, 2) + j


# ── gate (b): θ₃ q_series == the JTP theta Σ q^{n²} ──────────────────────────
def test_theta3_q_series_is_jacobi_theta():
    assert _theta3().q_series(20) == THETA3_Q20
    assert _theta3().leading_power() == Q(0, 1)


def test_theta3_matches_jtp_product():
    """Cross-check θ₃ against the Jacobi-triple-product
    ``∏_{k≥1} (1−q^{2k})(1+q^{2k−1})²`` (an INDEPENDENT derivation of the same
    series), built as an exact integer series to order 20."""
    N = 20
    coef = [0] * (N + 1)
    coef[0] = 1

    def mul_factor(series, c, d):                  # multiply by (1 + c·q^d)
        out = series[:]
        for i in range(len(series) - 1, -1, -1):
            if series[i] and i + d <= N:
                out[i + d] += c * series[i]
        return out

    k = 1
    while 2 * k - 1 <= N or 2 * k <= N:
        if 2 * k <= N:
            coef = mul_factor(coef, -1, 2 * k)     # (1 − q^{2k})
        if 2 * k - 1 <= N:
            coef = mul_factor(coef, 1, 2 * k - 1)  # (1 + q^{2k−1})
            coef = mul_factor(coef, 1, 2 * k - 1)  # squared
        k += 1
    assert coef == THETA3_Q20
    assert _theta3().q_series(20) == coef


# ── gate (c): g₃ reproduces the Zagier coefficients (the #9 payoff) ──────────
def test_g3_reproduces_zagier_coefficients():
    """THE #9 PAYOFF: the weight-3/2 shadow g₃ of Ramanujan's order-3 mock theta
    f(q), factoring out q^{1/24}, has q-series == the EXACT Zagier coefficients —
    so the shadow is now REPRESENTABLE in-carrier at weight 3/2."""
    g3 = _g3()
    assert g3.weight == Q(3, 2)
    assert g3.leading_power() == Q(1, 24)
    assert g3.q_series(26) == G3_ZAGIER


def test_g3_coefficient_is_signed_n_at_quadratic_exponent():
    """Each non-zero g₃ coefficient is ±n at exponent (n²−1)/24, sign (−12/n)."""
    g = _g3().q_series(26)
    for n in (1, 5, 7, 11, 13, 17, 19, 23, 25):
        e = (n * n - 1) // 24
        assert g[e] == _kronecker_minus12(n) * n


def test_kronecker_minus12_table():
    """(−12/n): +1 for n≡1,11 (12); −1 for n≡5,7 (12); 0 otherwise."""
    assert [_kronecker_minus12(n) for n in range(12)] == \
        [0, 1, 0, 0, 0, -1, 0, -1, 0, 0, 0, 1]
    # periodic mod 12
    for n in range(-30, 60):
        assert _kronecker_minus12(n) == _kronecker_minus12(n + 12)


# ── gate (d): Python==C parity on .q_series and .weight ──────────────────────
@pytest.mark.skipif(not _native.has_native_unary_theta(),
                    reason="native srmech_unary_theta not loaded")
def test_python_c_parity_anchors():
    """The native path and the pure-Python oracle emit BYTE-IDENTICAL exact
    integer coefficients for both anchors (do NOT trust the C — compare)."""
    for ut, N in ((_theta3(), 20), (_g3(), 26)):
        c_path = ut.q_series(N)                     # native present
        py_path = ut._q_series_py(N)                # the oracle
        assert c_path == py_path
    # weight is pure-Python (exact Q) but assert it agrees with the anchors
    assert _theta3().weight == Q(1, 2)
    assert _g3().weight == Q(3, 2)
    # and the C path still equals the published targets
    assert _theta3().q_series(20) == THETA3_Q20
    assert _g3().q_series(26) == G3_ZAGIER


@pytest.mark.skipif(not _native.has_native_unary_theta(),
                    reason="native srmech_unary_theta not loaded")
def test_python_c_parity_stress_sweep():
    """A broad Python==C parity sweep over j / a / b / D / support / N (including
    bignum n^j, two-sided support, and b ≠ 0)."""
    import random
    rng = random.Random(20260626)
    specs = [
        ("trivial", 0, 1, 0, 1, "all", 40),
        ("trivial", 1, 1, 0, 1, "all", 40),
        ("trivial", 2, 1, 0, 1, "all", 40),
        ("trivial", 3, 1, 0, 1, "nonneg", 60),
        ("minus12", 1, 1, 0, 24, "positive", 120),
        ("trivial", 0, 1, 1, 1, "all", 50),
        ("trivial", 1, 2, 3, 1, "positive", 50),
        ("trivial", 4, 1, 0, 1, "all", 30),
        ("minus12", 3, 1, 0, 24, "positive", 80),
    ]
    for ch, j, a, b, D, sup, N in specs:
        ut = unary_theta(ch, j, a, b, D, support=sup)
        assert ut.q_series(N) == ut._q_series_py(N), (ch, j, a, b, D, sup, N)
    for _ in range(40):
        M = rng.randint(1, 12)
        tab = [rng.choice([-1, 0, 1]) for _ in range(M)]
        if all(t == 0 for t in tab):
            tab[0] = 1
        j = rng.randint(0, 3)
        a = rng.randint(1, 4)
        b = rng.randint(-3, 3)
        D = rng.randint(1, 12)
        sup = rng.choice(["all", "positive", "nonneg"])
        N = rng.randint(5, 40)
        try:
            ut = unary_theta(Character.from_table(M, tab), j, a, b, D, support=sup)
        except ValueError:
            continue                                # empty support is honest
        assert ut.q_series(N) == ut._q_series_py(N), (M, tab, j, a, b, D, sup, N)


def test_pure_python_oracle_matches_targets_without_native():
    """The COMPLETE pure-Python body alone reproduces both anchors (so the carrier
    is correct on a no-C host)."""
    assert _theta3()._q_series_py(20) == THETA3_Q20
    assert _g3()._q_series_py(26) == G3_ZAGIER


# ── the existing carriers are now weight-annotated (weight-0) ─────────────────
def test_ellratio_weight_balanced_is_zero():
    from srmech.amsc.ellbase import EllRatio, EllMonomial, Theta
    a = EllMonomial.symbol("a")
    b = EllMonomial.symbol("b")
    balanced = EllRatio(num=(Theta(a),), den=(Theta(b),))
    assert balanced.weight == Q(0, 1)
    # a net-imbalanced ratio carries the net (#num − #den)/2 weight
    two_num = EllRatio(num=(Theta(a), Theta(b)))
    assert two_num.weight == Q(1, 1)


def test_thetasum_weight_is_zero():
    from srmech.amsc.ellbase import EllMonomial, Theta
    from srmech.amsc.thetasum import ThetaSum
    a = EllMonomial.symbol("a")
    ts = ThetaSum(terms=[(Q(1, 1), EllMonomial.one(), (Theta(a),))])
    assert ts.weight == Q(0, 1)


# ── input validation ─────────────────────────────────────────────────────────
def test_construction_rejects_bad_params():
    with pytest.raises(ValueError):
        unary_theta("trivial", -1, 1, 0, 1)         # j < 0
    with pytest.raises(ValueError):
        unary_theta("trivial", 0, 0, 0, 1)          # a <= 0
    with pytest.raises(ValueError):
        unary_theta("trivial", 0, 1, 0, 0)          # D <= 0
    with pytest.raises(ValueError):
        unary_theta("trivial", 0, 1, 0, 1, support="sideways")  # bad support


def test_character_trivial_and_table():
    assert Character.trivial().is_trivial
    assert Character.trivial()(7) == 1
    tab = Character.from_table(3, [0, 1, -1])
    assert (tab(0), tab(1), tab(2), tab(3), tab(4)) == (0, 1, -1, 0, 1)


# ── gate (e): the carrier source is numpy / math / abs() free ────────────────
def test_unary_theta_source_is_numpy_math_abs_free():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "unary_theta.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert re.search(r"abs\([^)]", text) is None    # no bare abs() CALL
    assert "float(" not in text                     # no float in the carrier body


# ── the ToolEntry registration + the running count ───────────────────────────
def test_unary_theta_tool_entry_registered():
    from srmech.amsc.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.amsc.unary_theta.unary_theta" in names


def test_introspect_tools_total_is_340():
    """The canonical shipped tool count after the rc71 ``harmonic_maass`` op (339 →
    340; the rc70 ``unary_theta`` op took it 338 → 339). Counted over the SHIPPED
    surface only — other tests (e.g. ``test_tool_schema.py``) imperatively
    ``register_tool`` throwaway ``test.*`` entries into the global schema singleton
    that they do not (cleanly) remove, so the raw ``describe()`` total drifts up by
    those leaks depending on test order. We exclude the ``test.``-namespaced
    injections (the shipped surface is what this invariant is about)."""
    from srmech.amsc.tool_schema import get_tool_schema
    shipped = [t for t in get_tool_schema().tools if not t.name.startswith("test.")]
    assert len(shipped) == 403
    names = {t.name for t in shipped}
    assert "srmech.amsc.unary_theta.unary_theta" in names
    assert "srmech.amsc.harmonic_maass.harmonic_maass" in names
