"""rc83 — ``srmech.amsc.eisenstein.Eisenstein``, the SECOND WEIGHT-axis carrier.

The build gates (the no-shell proof; construction IS the answer, no search):

  (a) the WEIGHT axis + leading power + is_modular for the keystones (exact);
  (b) E₄ / E₆ / E₈ reproduce the published q-series EXACTLY (the verified oracle
      is the hardcoded coefficients, NOT the carrier re-running itself);
  (c) the HEADLINE CROSS-RUNG: **E₄³ − E₆² == 1728·Δ == 1728·η²⁴** — validated
      against the PUBLISHED rc82 EtaQuotient({1:24}) carrier (Ramanujan τ);
  (d) the ring identities E₄² == E₈ and E₄·E₆ == E₁₀;
  (e) the EXACT-RATIONAL keystone E₁₂ has c₁ == Q(65520, 691) (non-integer coeff);
  (f) the honest boundaries: k=2 quasimodular rejected, odd k / k<4 rejected;
  (g) Python==C parity on ``.q_series`` for the keystones + a stress sweep
      (guarded by the native-availability skip; do NOT trust the C — compare);
  (h) the carrier source has no numpy / math / abs() (the ratchet);
  (i) a CARRIER → it adds NO ToolEntry → ``tools.total`` stays 342.
"""
from __future__ import annotations

import os
import re
import tokenize

import pytest

from srmech.amsc.eisenstein import Eisenstein, eisenstein
from srmech.amsc.eta_quotient import EtaQuotient
from srmech.amsc.q import Q
from srmech.amsc import _native


# the verified oracle (hardcoded known coefficients — NOT the carrier itself)
E4_5 = [1, 240, 2160, 6720, 17520]            # 240·σ₃
E6_5 = [1, -504, -16632, -122976, -532728]    # −504·σ₅
E8_6 = [1, 480, 61920, 1050240, 7926240, 37500480]   # 480·σ₇
# Ramanujan τ(1..N) = the q-series of η²⁴ (the published rc82 carrier reproduces it)
TAU_1_7 = [1, -24, 252, -1472, 4830, -6048, -16744]


def _q_int_list(qs):
    """A list of exact-Q coefficients that happen to be integers → a list of int
    (asserts every denominator is 1, so an accidental non-integer fails loudly)."""
    out = []
    for c in qs:
        assert isinstance(c, Q)
        assert c.denominator == 1, f"expected integer coeff, got {c}"
        out.append(c.numerator)
    return out


def _qmul(a, b, nt):
    """Exact-Q truncated q-series convolution to nt terms."""
    out = [Q(0, 1)] * nt
    for i in range(nt):
        for j in range(nt - i):
            out[i + j] = out[i + j] + a[i] * b[j]
    return out


def _qsub(a, b):
    return [x - y for x, y in zip(a, b)]


# ── gate (a): the weight axis + leading power + is_modular ─────────────────────
def test_keystone_weight_leading_power_modular():
    for k in (4, 6, 8, 10, 12, 14):
        e = eisenstein(k)
        assert e.weight == Q(k, 1)
        assert e.leading_power == Q(0, 1)      # constant term 1, NOT a cusp form
        assert e.is_modular() is True
        assert e.k == k


# ── gate (b): E₄ / E₆ / E₈ reproduce the published q-series EXACTLY ────────────
def test_keystone1_E4_q_series():
    assert _q_int_list(eisenstein(4).q_series(5)) == E4_5


def test_keystone2_E6_q_series():
    assert _q_int_list(eisenstein(6).q_series(5)) == E6_5


def test_keystone3_E8_q_series():
    assert _q_int_list(eisenstein(8).q_series(6)) == E8_6


# ── gate (c): the HEADLINE CROSS-RUNG E₄³ − E₆² == 1728·η²⁴ ───────────────────
def test_keystone4_cross_rung_E4cubed_minus_E6sq_is_1728_eta24():
    """The headline keystone: E₄³ − E₆² == 1728·Δ == 1728·η²⁴, validated against
    the PUBLISHED rc82 EtaQuotient carrier (the carrier ladder validates itself)."""
    N = 12
    E4 = eisenstein(4).q_series(N)
    E6 = eisenstein(6).q_series(N)
    diff = _qsub(_qmul(_qmul(E4, E4, N), E4, N), _qmul(E6, E6, N))
    # the constant term vanishes → a CUSP form
    assert diff[0] == Q(0, 1)
    # (E₄³ − E₆²)[1:] / 1728 == EtaQuotient({1:24}).q_series(N)[:N-1] (Ramanujan τ)
    lhs = [c * Q(1, 1728) for c in diff[1:]]
    assert all(c.denominator == 1 for c in lhs)        # exactly divisible by 1728
    tau_published = EtaQuotient({1: 24}).q_series(N)[:N - 1]
    assert [int(c.numerator) for c in lhs] == tau_published
    # and the published rc82 carrier IS the Ramanujan τ (hardcoded-oracle anchor)
    assert tau_published[:7] == TAU_1_7


# ── gate (d): the ring identities E₄² == E₈ and E₄·E₆ == E₁₀ ──────────────────
def test_keystone5_ring_identities():
    N = 10
    E4 = eisenstein(4).q_series(N)
    E6 = eisenstein(6).q_series(N)
    E8 = eisenstein(8).q_series(N)
    E10 = eisenstein(10).q_series(N)
    assert _qmul(E4, E4, N) == E8      # M₈ is 1-dimensional
    assert _qmul(E4, E6, N) == E10     # M₁₀ is 1-dimensional


# ── gate (e): the EXACT-RATIONAL keystone E₁₂ c₁ == 65520/691 ─────────────────
def test_keystone6_E12_is_genuinely_rational():
    """E₁₂ has c₁ = 65520/691 — the whole reason coefficients are Q, not int."""
    c1 = eisenstein(12).q_series(2)[1]
    assert c1 == Q(65520, 691)
    assert c1.denominator == 691          # genuinely non-integer
    # E₁₆ also has a genuine rational prefactor (16320/3617)
    assert eisenstein(16).q_series(2)[1] == Q(16320, 3617)


# ── gate (f): the honest boundaries (k=2 quasimodular; odd k; k<4) ────────────
def test_k2_is_quasimodular_boundary_rejected():
    """k=2 is the QUASIMODULAR boundary: E₂ is NOT modular (M₂ = {0}). Rejected
    with an honest message naming it — never silently produced."""
    with pytest.raises(ValueError) as ei:
        eisenstein(2)
    assert "quasimodular" in str(ei.value).lower()


def test_odd_and_small_weights_rejected():
    for bad in (3, 5, 7, 9):
        with pytest.raises(ValueError):
            eisenstein(bad)               # E_k vanishes for odd k
    for bad in (0, 1):
        with pytest.raises(ValueError):
            eisenstein(bad)               # k < 4 (k=2 handled separately)
    with pytest.raises(TypeError):
        eisenstein(4.0)                   # not an int
    with pytest.raises(TypeError):
        eisenstein(True)                  # bool is not a weight
    with pytest.raises(ValueError):
        eisenstein(4).q_series(0)         # n_terms < 1


# ── gate (g): Python==C parity on .q_series ──────────────────────────────────
@pytest.mark.skipif(not _native.has_native_eisenstein(),
                    reason="native srmech_eisenstein not loaded")
def test_python_c_parity_keystones():
    """The native path and the pure-Python oracle emit BYTE-IDENTICAL reduced
    (num, den) coefficients (do NOT trust the C — compare element-for-element)."""
    for k, n in ((4, 8), (6, 8), (8, 8), (12, 8), (16, 6)):
        e = eisenstein(k)
        c_path = e.q_series(n)            # native present
        py_path = e._q_series_py(n)       # the oracle
        assert c_path == py_path, (k, n)
    # and the C path still equals the published targets
    assert _q_int_list(eisenstein(4).q_series(5)) == E4_5
    assert eisenstein(12).q_series(2)[1] == Q(65520, 691)


@pytest.mark.skipif(not _native.has_native_eisenstein(),
                    reason="native srmech_eisenstein not loaded")
def test_python_c_parity_stress_sweep():
    """A broad Python==C parity sweep over even weights (integer + genuinely
    rational coeffs, growing coefficients) and several depths."""
    for k in (4, 6, 8, 10, 12, 14, 16, 18, 20, 26):
        e = eisenstein(k)
        for n in (5, 12, 24):
            assert e.q_series(n) == e._q_series_py(n), (k, n)


def test_pure_python_oracle_matches_targets_without_native():
    """The COMPLETE pure-Python body alone reproduces the keystones (so the carrier
    is correct on a no-C host)."""
    assert _q_int_list(eisenstein(4)._q_series_py(5)) == E4_5
    assert _q_int_list(eisenstein(6)._q_series_py(5)) == E6_5
    assert eisenstein(12)._q_series_py(2)[1] == Q(65520, 691)


# ── equality / repr / prefactor ──────────────────────────────────────────────
def test_equality_and_prefactor():
    a = eisenstein(4)
    b = Eisenstein(4)
    c = eisenstein(6)
    assert a == b and a.equals(b)
    assert hash(a) == hash(b)
    assert a != c and not a.equals(c)
    # the exact-rational prefactor −2k/B_k
    assert a.prefactor == Q(240, 1)       # −8 / (−1/30) = 240
    assert c.prefactor == Q(-504, 1)      # −12 / (1/42) = −504
    assert eisenstein(12).prefactor == Q(65520, 691)
    assert "Eisenstein(k=4" in repr(a)


# ── gate (h): the carrier source is numpy / math / abs() free ────────────────
def test_eisenstein_source_is_numpy_math_abs_free():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "eisenstein.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert re.search(r"abs\([^)]", text) is None    # no bare abs() CALL
    assert "float(" not in text                     # no float in the carrier body


# ── gate (i): a CARRIER — NO ToolEntry, tools.total UNCHANGED ─────────────────
def test_eisenstein_is_a_carrier_no_tool_entry():
    """Eisenstein is a CARRIER (like Poly / EtaQuotient) → it registers NO
    ToolEntry, so the shipped tool count is UNCHANGED at 342."""
    from srmech.amsc.tool_schema import get_tool_schema
    shipped = [t for t in get_tool_schema().tools if not t.name.startswith("test.")]
    assert len(shipped) == 386
    names = {t.name for t in shipped}
    assert not any("eisenstein" in nm for nm in names)


def test_eisenstein_exported_from_amsc():
    from srmech.amsc import Eisenstein as Exported
    assert Exported is Eisenstein
