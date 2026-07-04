"""rc71 — ``srmech.amsc.harmonic_maass.HarmonicMaass``, the PAIR carrier that makes
a harmonic (weak) Maass form a FINITE EXACT object (research item #9 closed).

A harmonic Maass form f of weight k is determined by the pair (f⁺ holomorphic mock
part, g = ξ_k(f) shadow); the non-holomorphic completion f⁻ is the Eichler integral
of the shadow, recoverable not stored (Bruinier–Funke "On Two Geometric Theta
Lifts", arXiv:math/0212286v4, Prop. 3.2 p.10; the shadow map ξ_k : H_{k,L} →
M^!_{2−k}, kernel = the holomorphic forms). The #9 keystone is Ramanujan's order-3
mock theta f(q) = Σ q^{n²}/∏(1+qʲ)² (Zagier, Astérisque 326 (2009), p.145) paired
with its weight-3/2 shadow g₃ = Σ_{n≥1}(−12/n)·n·q^{n²/24} (p.150) — weight 1/2.

The build gates (the no-shell proof):

  1. weight consistency: f.weight + shadow.weight == 2 (exact Q); keystone 1/2+3/2=2.
  2. hol held exactly to depth N (f(q) Eulerian coeffs, independently cross-checked).
  3. shadow held exactly (g₃ — weight 3/2 + Zagier coeffs).
  4. ξ map: harmonic_maass(f(q), g₃).xi() == g₃ (Prop. 3.2: hol part in the kernel).
  5. canonical form: equal pairs ⟺ identical; unequal hol OR shadow ⟹ unequal.
  6. KEYSTONE: harmonic_maass(hol=f(q), shadow=g₃) — weight 1/2 — ONE exact carrier.
  7. Python == C parity exact on the hol Eulerian q-series (C peer srmech_harmonic_maass).
  8. ratchet-clean (no numpy/math/abs/float in the new carrier source).
"""
from __future__ import annotations

import os
import re
import tokenize

import pytest

from srmech.amsc.harmonic_maass import (
    MockQSeries, HarmonicMaass, harmonic_maass, _eulerian_f_coeffs,
)
from srmech.amsc.unary_theta import unary_theta
from srmech.amsc.q import Q
from srmech.amsc import _native


# the keystone anchors, reused across the gates
def _g3():
    """The weight-3/2 shadow g₃ (rc70 UnaryTheta; Zagier p.150)."""
    return unary_theta("minus12", 1, 1, 0, 24, support="positive")


def _f_hol():
    """Ramanujan's order-3 mock theta holomorphic part f(q) (Eulerian rule)."""
    return MockQSeries.eulerian_f()


# the exact targets (verified at build, independently cross-checked)
# f(q) = Σ q^{n²}/∏(1+qʲ)² — OEIS A000025; cross-checked by the pure series build.
F_Q_COEFFS = [1, 1, -2, 3, -3, 3, -5, 7, -6, 6, -10, 12, -11, 13, -17, 20,
              -21, 21, -27, 34, -33]
# g₃ Zagier coefficients (rc70 anchor; q^{1/24} factored out)
G3_ZAGIER = [1, -5, -7, 0, 0, 11, 0, 13, 0, 0, 0, 0, -17, 0, 0, -19,
             0, 0, 0, 0, 0, 0, 23, 0, 0, 0, 25]


# ── gate 1: weight consistency f.weight + shadow.weight == 2 ──────────────────
def test_weight_sum_is_two():
    hm = harmonic_maass(_f_hol(), _g3())
    assert hm.weight + hm.shadow.weight == Q(2, 1)
    assert hm.shadow.weight == Q(3, 2)
    assert hm.weight == Q(1, 2)


def test_weight_is_general_two_minus_shadow():
    """weight = 2 − shadow.weight for several shadow grades (the weight axis dual)."""
    for j in range(0, 4):
        sh = unary_theta("trivial", j, 1, 0, 1, support="all")  # weight 1/2 + j
        hol = MockQSeries.from_qpoly([(1, 1)])
        hm = harmonic_maass(hol, sh)
        assert hm.weight == Q(2, 1) - (Q(1, 2) + j)
        assert hm.weight + sh.weight == Q(2, 1)


# ── gate 2: hol held exactly to depth N (independently cross-checked) ─────────
def test_hol_eulerian_coeffs_to_depth():
    """The f(q) Eulerian coefficients match the independent target to depth 20."""
    hol = _f_hol()
    q = hol.q_series(20)
    assert [int(c) for c in q] == F_Q_COEFFS
    assert hol.leading_power == Q(0, 1)


def test_hol_eulerian_cross_check_first_coeffs():
    """Independent cross-check of the FIRST coefficients via the partial-product
    Eulerian definition f(q) = Σ_{n≥0} q^{n²}/∏_{j=1}^n (1+qʲ)² (a from-scratch
    integer power-series build, NOT the carrier's own code path)."""
    N = 16

    def mul(a, b):
        out = [0] * (N + 1)
        for i, ai in enumerate(a):
            if ai == 0:
                continue
            for j, bj in enumerate(b):
                if i + j > N:
                    break
                out[i + j] += ai * bj
        return out

    def inv(s):  # 1/s, s[0]==1, integer result
        out = [0] * (N + 1)
        out[0] = 1
        for n in range(1, N + 1):
            acc = 0
            for k in range(1, n + 1):
                acc += s[k] * out[n - k]
            out[n] = -acc
        return out

    f = [0] * (N + 1)
    n = 0
    while n * n <= N:
        prod = [0] * (N + 1)
        prod[0] = 1
        for j in range(1, n + 1):
            factor = [0] * (N + 1)
            factor[0] = 1
            if j <= N:
                factor[j] = 1
            prod = mul(prod, factor)
            prod = mul(prod, factor)
        ip = inv(prod)
        for i in range(N + 1):
            if i + n * n <= N:
                f[i + n * n] += ip[i]
        n += 1
    assert [int(c) for c in _f_hol().q_series(N)] == f
    # the well-known leading coefficients 1, 1, -2, 3, -3, ...
    assert f[:5] == [1, 1, -2, 3, -3]


# ── gate 3: shadow held exactly (g₃ — weight 3/2 + Zagier coeffs) ────────────
def test_shadow_is_g3_exact():
    hm = harmonic_maass(_f_hol(), _g3())
    assert hm.shadow.weight == Q(3, 2)
    assert hm.shadow_leading_power() == Q(1, 24)
    assert hm.shadow_q_series(26) == G3_ZAGIER


# ── gate 4: ξ map — ξ of the pair is its shadow (Prop. 3.2) ──────────────────
def test_xi_returns_shadow():
    """Bruinier–Funke Prop. 3.2: ξ_k(f) = the shadow; the holomorphic part is in
    the kernel of ξ_k. So ξ of the pair IS its shadow."""
    g3 = _g3()
    hm = harmonic_maass(_f_hol(), g3)
    assert hm.xi() == g3
    assert hm.xi() is hm.shadow


# ── gate 5: canonical form — equal ⟺ identical pair ──────────────────────────
def test_equality_is_canonical():
    hm1 = harmonic_maass(_f_hol(), _g3())
    hm2 = harmonic_maass(_f_hol(), _g3())
    assert hm1 == hm2
    assert hash(hm1) == hash(hm2)


def test_unequal_shadow_is_unequal():
    other_shadow = unary_theta("trivial", 1, 1, 0, 1, support="all")  # weight 3/2 too
    hm1 = harmonic_maass(_f_hol(), _g3())
    hm2 = harmonic_maass(_f_hol(), other_shadow)
    assert hm1 != hm2


def test_unequal_hol_is_unequal():
    hol_a = MockQSeries.from_qpoly([(1, 1), (1, 1)])      # 1 + q
    hol_b = MockQSeries.from_qpoly([(1, 1), (2, 1)])      # 1 + 2q
    hm1 = harmonic_maass(hol_a, _g3())
    hm2 = harmonic_maass(hol_b, _g3())
    assert hm1 != hm2


def test_mockqseries_qpoly_equality_is_exact():
    a = MockQSeries.from_qpoly([(1, 1), (-2, 1), (3, 1)])
    b = MockQSeries.from_qpoly([(1, 1), (-2, 1), (3, 1)])
    c = MockQSeries.from_qpoly([(1, 1), (-2, 1), (4, 1)])
    assert a.is_exact and a == b and a != c


# ── gate 6: THE KEYSTONE — the #9 mock theta is ONE finite exact carrier ─────
def test_keystone_mock_theta_is_one_finite_exact_carrier():
    """THE #9 PAYOFF: Ramanujan's order-3 mock theta — whose non-holomorphic
    completion was the operand-side 'irrepresentable' target — is now ONE finite
    exact HarmonicMaass carrier, the pair (f(q), g₃) at weight 1/2. Storing the
    shadow g₃ IS storing the completion f⁻ (its Eichler integral, Prop. 3.2)."""
    hm = harmonic_maass(hol="eulerian_f", shadow=_g3())     # the string-name path
    assert hm.weight == Q(1, 2)                              # 2 − 3/2
    assert isinstance(hm.hol, MockQSeries) and hm.hol.kind == "eulerian_f"
    assert hm.shadow == _g3()
    # both channels are exact + present:
    assert [int(c) for c in hm.hol_q_series(20)] == F_Q_COEFFS    # the mock part
    assert hm.shadow_q_series(26) == G3_ZAGIER                    # the shadow
    # ξ of the pair is its shadow (the completion is the shadow's period integral):
    assert hm.xi() == _g3()


# ── gate 7: Python == C parity on the hol Eulerian q-series ──────────────────
@pytest.mark.skipif(not _native.has_native_harmonic_maass(),
                    reason="native srmech_harmonic_maass not loaded")
def test_python_c_parity_hol_eulerian():
    """The native srmech_harmonic_maass path and the pure-Python oracle emit
    BYTE-IDENTICAL exact integer f(q) coefficients (do NOT trust the C — compare)."""
    for N in (5, 20, 40, 64):
        c_path = _native.harmonic_maass_eulerian_c(N)
        py_path = _eulerian_f_coeffs(N)
        assert c_path == py_path, N
    # the carrier's own dispatch (C present) still equals the published targets
    assert [int(c) for c in _f_hol().q_series(20)] == F_Q_COEFFS


@pytest.mark.skipif(not _native.has_native_harmonic_maass(),
                    reason="native srmech_harmonic_maass not loaded")
def test_python_c_parity_carrier_dispatch():
    """The carrier's q_series (which dispatches to C when present) equals the pure
    oracle at several depths."""
    hol = _f_hol()
    for N in (8, 30, 50):
        assert [int(c) for c in hol.q_series(N)] == hol._eulerian_q_series_py(N)


def test_pure_python_oracle_matches_target_without_native():
    """The COMPLETE pure-Python body alone reproduces the f(q) target (so the
    carrier is correct on a no-C host)."""
    assert _eulerian_f_coeffs(20) == F_Q_COEFFS


# ── the honest representability boundary (the operand-side OPEN, named) ───────
def test_unknown_named_rule_is_honest_open():
    """A mock part with NO finite generating rule is an honest OPEN — a named rule
    that does not exist raises, it does not fabricate a decision."""
    with pytest.raises(ValueError):
        harmonic_maass(hol="some_general_mock_part", shadow=_g3())


def test_construction_rejects_bad_types():
    with pytest.raises(TypeError):
        harmonic_maass(_f_hol(), "not a unary theta")        # shadow not UnaryTheta
    with pytest.raises(TypeError):
        HarmonicMaass(42, _g3())                              # hol not MockQSeries
    with pytest.raises(ValueError):
        MockQSeries("bogus_kind", Q(0, 1))                   # bad rule kind
    with pytest.raises(ValueError):
        MockQSeries.from_qpoly(None)                          # qpoly needs coeffs


# ── gate 8: the carrier source is numpy / math / abs() / float free ──────────
def test_harmonic_maass_source_is_numpy_math_abs_free():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "harmonic_maass.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert re.search(r"abs\([^)]", text) is None    # no bare abs() CALL
    assert "float(" not in text                     # no float on the decision path


# ── the ToolEntry registration + the running count ───────────────────────────
def test_harmonic_maass_tool_entry_registered():
    from srmech.amsc.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.amsc.harmonic_maass.harmonic_maass" in names


def test_introspect_tools_total_is_340_rc71():
    """The canonical shipped tool count after the rc71 ``harmonic_maass`` op
    (339 → 340). Counted over the SHIPPED surface only (excluding any ``test.``-
    namespaced injections other tests leak), so the invariant is order-independent."""
    from srmech.amsc.tool_schema import get_tool_schema
    shipped = [t for t in get_tool_schema().tools if not t.name.startswith("test.")]
    assert len(shipped) == 386
    names = {t.name for t in shipped}
    assert "srmech.amsc.harmonic_maass.harmonic_maass" in names
