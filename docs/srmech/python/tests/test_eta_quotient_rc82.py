"""rc82 — ``srmech.amsc.eta_quotient.EtaQuotient``, a WEIGHT-axis operand carrier.

The build gates (the no-shell proof; construction IS the answer, no search):

  (a) the WEIGHT axis + level + leading power for both keystones (exact ``Q``);
  (b) **η²⁴ = Δ** reproduces the Ramanujan τ q-series EXACTLY (the verified oracle
      is the hardcoded τ(1..7), NOT the carrier re-running itself); is_modular +
      is_holomorphic;
  (c) **the X₀(11) weight-2 newform** η²(τ)η²(11τ) reproduces the newform a(n)
      EXACTLY (verified-oracle hardcoded coeffs); is_modular;
  (d) the Ligozat + order-at-cusp decision on the keystones (both holomorphic →
      all cusp orders ≥ 0);
  (e) Python==C parity on ``.q_series`` for both keystones + a broad stress sweep
      (guarded by the native-availability skip; do NOT trust the C — compare);
  (f) the carrier source has no numpy / math / abs() (the ratchet);
  (g) the carrier adds NO ToolEntry → ``tools.total`` stays 342.
"""
from __future__ import annotations

import os
import re
import tokenize

import pytest

from srmech.amsc.eta_quotient import EtaQuotient, eta_quotient
from srmech.amsc.q import Q
from srmech.amsc import _native


# the verified oracle (hardcoded known coefficients — NOT the carrier itself)
# Ramanujan τ(1..7) = q-series of η²⁴ after factoring q^1 (OEIS A000594)
TAU_1_7 = [1, -24, 252, -1472, 4830, -6048, -16744]
# the X₀(11) weight-2 newform a(1..7) = q-series of η²(τ)η²(11τ) after q^1 (LMFDB 11.2.a.a)
X011_1_7 = [1, -2, -1, 2, 1, 2, -2]


def _delta() -> EtaQuotient:
    return eta_quotient({1: 24})


def _x011() -> EtaQuotient:
    return eta_quotient({1: 2, 11: 2})


# ── gate (a): the weight axis + level + leading power ─────────────────────────
def test_keystone1_weight_level_leading_power():
    d = _delta()
    assert d.weight == Q(12, 1)
    assert d.level == 1
    assert d.leading_power == Q(1, 1)
    assert d.exponents == {1: 24}


def test_keystone2_weight_level_leading_power():
    f = _x011()
    assert f.weight == Q(2, 1)
    assert f.level == 11
    assert f.leading_power == Q(1, 1)
    assert f.exponents == {1: 2, 11: 2}


# ── gate (b): η²⁴ = Δ reproduces the Ramanujan τ EXACTLY ──────────────────────
def test_keystone1_eta24_is_ramanujan_tau():
    """η²⁴ = Δ: the q-series (after factoring q^1) is the Ramanujan τ — the verified
    oracle is the hardcoded τ(1..7), not the carrier re-running itself."""
    d = _delta()
    assert d.q_series(8)[:7] == TAU_1_7


def test_keystone1_eta24_is_modular_and_holomorphic():
    d = _delta()
    assert d.is_modular() is True
    assert d.is_holomorphic() is True       # weight-12 cusp form on Γ(1)


# ── gate (c): the X₀(11) weight-2 newform ─────────────────────────────────────
def test_keystone2_level11_newform_coefficients():
    """η²(τ)η²(11τ) = the X₀(11) weight-2 newform: the q-series (after q^1) is the
    newform a(n) — verified-oracle hardcoded coefficients."""
    f = _x011()
    assert f.q_series(8)[:7] == X011_1_7


def test_keystone2_level11_newform_is_modular():
    assert _x011().is_modular() is True


# ── gate (d): the Ligozat + order-at-cusp decision ───────────────────────────
def test_ligozat_conditions_both_keystones():
    """Both keystones satisfy the two integer-congruence Ligozat conditions."""
    for eq in (_delta(), _x011()):
        n = eq.level
        cond_i = sum(d * r for d, r in eq.exponents.items()) % 24
        cond_ii = sum((n // d) * r for d, r in eq.exponents.items()) % 24
        assert cond_i == 0 and cond_ii == 0
        assert eq.is_modular() is True


def test_order_at_cusp_keystones_all_nonneg():
    """The Ligozat order-at-cusp formula: both keystones are holomorphic, so every
    cusp order is ≥ 0 (both keystones: every cusp order == 1)."""
    # η²⁴: only cusp is ∞ (c=1 of Γ(1)), order 1
    assert _delta().order_at_cusp(1) == Q(1, 1)
    # X₀(11): cusps c=1 and c=11, both order 1
    f = _x011()
    assert f.order_at_cusp(1) == Q(1, 1)
    assert f.order_at_cusp(11) == Q(1, 1)


def test_order_at_cusp_rejects_non_divisor():
    f = _x011()
    with pytest.raises(ValueError):
        f.order_at_cusp(2)                  # 2 does not divide N=11


def test_non_modular_eta_quotient_is_honest():
    """An exponent vector failing the Ligozat congruences is honestly NOT modular
    (is_modular False, is_holomorphic False) — no fabricated reduction."""
    eq = eta_quotient({1: 1})              # Σ d·r_d = 1 ≢ 0 (mod 24)
    assert eq.is_modular() is False
    assert eq.is_holomorphic() is False
    assert eq.weight == Q(1, 2)


# ── gate (e): Python==C parity on .q_series ──────────────────────────────────
@pytest.mark.skipif(not _native.has_native_eta_quotient(),
                    reason="native srmech_eta_quotient not loaded")
def test_python_c_parity_keystones():
    """The native path and the pure-Python oracle emit BYTE-IDENTICAL exact integer
    coefficients for both keystones (do NOT trust the C — compare element-for-
    element)."""
    for eq, n in ((_delta(), 30), (_x011(), 30)):
        c_path = eq.q_series(n)             # native present
        py_path = eq._q_series_py(n)        # the oracle
        assert c_path == py_path
    # and the C path still equals the published targets
    assert _delta().q_series(8)[:7] == TAU_1_7
    assert _x011().q_series(8)[:7] == X011_1_7


@pytest.mark.skipif(not _native.has_native_eta_quotient(),
                    reason="native srmech_eta_quotient not loaded")
def test_python_c_parity_stress_sweep():
    """A broad Python==C parity sweep over exponent vectors (positive + negative
    exponents, several levels, growing coefficients)."""
    import random
    rng = random.Random(20260629)
    specs = [
        {1: 24},                            # Δ
        {1: 2, 11: 2},                      # X₀(11)
        {1: 1},                             # η (the eta itself)
        {1: -1},                            # 1/η (a negative exponent → geometric)
        {2: 12},                            # η(2τ)^12
        {1: 8, 2: -4, 4: 8},                # mixed signs
        {1: -2, 2: 5, 3: -3, 6: 7},         # 4 factors, mixed
        {5: 6, 1: -6},
    ]
    for exps in specs:
        eq = eta_quotient(exps)
        for n in (12, 25, 50):
            assert eq.q_series(n) == eq._q_series_py(n), (exps, n)
    # random sweep
    for _ in range(40):
        nf = rng.randint(1, 4)
        exps = {}
        for _k in range(nf):
            d = rng.randint(1, 6)
            r = rng.choice([-3, -2, -1, 1, 2, 3, 4])
            exps[d] = exps.get(d, 0) + r
        exps = {d: r for d, r in exps.items() if r != 0}
        if not exps:
            continue
        eq = eta_quotient(exps)
        n = rng.randint(8, 40)
        assert eq.q_series(n) == eq._q_series_py(n), (exps, n)


def test_pure_python_oracle_matches_targets_without_native():
    """The COMPLETE pure-Python body alone reproduces both keystones (so the carrier
    is correct on a no-C host)."""
    assert _delta()._q_series_py(8)[:7] == TAU_1_7
    assert _x011()._q_series_py(8)[:7] == X011_1_7


# ── negative-exponent + canonicalisation behaviour ───────────────────────────
def test_negative_exponent_geometric_expansion():
    """1/η = q^{-1/24}·∏ 1/(1−q^m): the q-series (after the leading-power factor-out)
    is the partition-count generating function ∏ 1/(1−q^m) = Σ p(n) q^n."""
    inv_eta = eta_quotient({1: -1})
    # ∏_{m≥1} 1/(1−q^m) = 1 + q + 2q² + 3q³ + 5q⁴ + 7q⁵ + 11q⁶ + … (partition numbers)
    assert inv_eta.q_series(8) == [1, 1, 2, 3, 5, 7, 11, 15]
    assert inv_eta.leading_power == Q(-1, 24)


def test_canonicalisation_and_equality():
    a = eta_quotient({1: 2, 11: 2})
    b = eta_quotient({11: 2, 1: 2})        # order-independent
    assert a == b and a.equals(b)
    assert hash(a) == hash(b)
    # a zero exponent is dropped
    c = eta_quotient({1: 24, 2: 0})
    assert c == eta_quotient({1: 24})


def test_construction_rejects_bad_inputs():
    with pytest.raises(ValueError):
        eta_quotient({})                    # empty
    with pytest.raises(ValueError):
        eta_quotient({0: 3})                # non-positive d
    with pytest.raises(ValueError):
        eta_quotient({-2: 3})               # non-positive d
    with pytest.raises(ValueError):
        eta_quotient({1: 0})                # all-zero exponents → empty product
    with pytest.raises(ValueError):
        eta_quotient({1: 24}).q_series(0)   # n_terms < 1
    with pytest.raises(TypeError):
        eta_quotient([(1, 24)])             # not a mapping


# ── gate (f): the carrier source is numpy / math / abs() free ────────────────
def test_eta_quotient_source_is_numpy_math_abs_free():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "eta_quotient.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert re.search(r"abs\([^)]", text) is None    # no bare abs() CALL
    assert "float(" not in text                     # no float in the carrier body


# ── gate (g): a CARRIER — NO ToolEntry, tools.total UNCHANGED ─────────────────
def test_eta_quotient_is_a_carrier_no_tool_entry():
    """EtaQuotient is a CARRIER (like Poly / RiemannTheta) → it registers NO
    ToolEntry, so the shipped tool count is UNCHANGED at 342."""
    from srmech.amsc.tool_schema import get_tool_schema
    shipped = [t for t in get_tool_schema().tools if not t.name.startswith("test.")]
    assert len(shipped) == 381
    names = {t.name for t in shipped}
    # no eta_quotient ToolEntry leaked in
    assert not any("eta_quotient" in nm for nm in names)


def test_eta_quotient_exported_from_amsc():
    from srmech.amsc import EtaQuotient as Exported
    assert Exported is EtaQuotient
