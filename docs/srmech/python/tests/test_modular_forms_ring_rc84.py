"""rc84 — ``srmech.amsc.modular_forms_ring.ModularFormsRing``, the THIRD WEIGHT-axis
rung (after rc82 eta-quotient + rc83 Eisenstein): the level-1 ℂ[E₄,E₆] modular-
forms-ring carrier + its EXACT membership decision.

The build gates (the no-shell proof; the construction IS the answer, no search):

  (a) the graded basis: dim(k) == len(weight_monomials(k)) for every even k; the
      published weight_monomials(12) == [(0,2),(3,0)];
  (b) the membership keystones — Δ=(E₄³−E₆²)/1728 @12 → {(3,0):1/1728,(0,2):−1/1728},
      E₈ @8 → {(2,0):1}, E₁₀ @10 → {(1,1):1}, E₁₄ @14 → {(2,1):1} (the verified
      oracle is the hardcoded known reps, NOT the carrier re-running itself);
  (c) the honest rejection: a non-modular q-series @12 → None;
  (d) the Δ source-of-truth cross-check against the PUBLISHED rc82 EtaQuotient
      ({1:24}) = η²⁴ (Ramanujan τ) — the carrier ladder validates itself;
  (e) the level-axis OPEN: a genuinely-higher-level form (X₀(11), N=11) @2 → None;
  (f) Python==C parity on .represent for the keystones (guarded by the native-skip;
      do NOT trust the C — compare element-for-element);
  (g) the carrier source has no numpy / math / abs() (the ratchet);
  (h) the REDUCER ``modular_forms_ring_represent`` IS a ToolEntry → tools.total 342
      (rc84 took it 340→341; rc89 quasimodular reducer → 342); the bare carrier
      constructor + weight_monomials/dim are NOT ToolEntries.
"""
from __future__ import annotations

import os
import re
import tokenize

import pytest

from srmech.amsc.modular_forms_ring import (
    ModularForm,
    ModularFormsRing,
    modular_forms_ring,
    modular_forms_ring_represent,
)
from srmech.amsc.eisenstein import Eisenstein
from srmech.amsc.eta_quotient import EtaQuotient
from srmech.amsc.q import Q
from srmech.amsc import _native


# ── exact-Q q-series helpers (local, no carrier re-use for the oracle) ─────────
def _qmul(a, b, nt):
    out = [Q(0, 1)] * nt
    for i in range(nt):
        for j in range(nt - i):
            out[i + j] = out[i + j] + a[i] * b[j]
    return out


def _qsub(a, b):
    return [x - y for x, y in zip(a, b)]


def _delta(nt):
    """Δ = (E₄³ − E₆²)/1728 as an exact-Q q-series (nt terms)."""
    e4 = Eisenstein(4).q_series(nt)
    e6 = Eisenstein(6).q_series(nt)
    diff = _qsub(_qmul(_qmul(e4, e4, nt), e4, nt), _qmul(e6, e6, nt))
    return [c * Q(1, 1728) for c in diff]


# the VERIFIED ORACLE — the hardcoded known reps (NOT the carrier itself)
TAU_1_7 = [1, -24, 252, -1472, 4830, -6048, -16744]   # η²⁴ Ramanujan τ
X0_11 = [1, -2, -1, 2, 1, 2, -2]                       # η²η²(11τ) X₀(11) newform


# ── gate (a): the graded basis ────────────────────────────────────────────────
def test_dim_and_monomials_published():
    R = modular_forms_ring()
    assert R.dim(12) == 2
    assert R.dim(8) == 1
    assert R.dim(4) == 1
    assert R.dim(24) == 3
    assert R.dim(0) == 1            # the constants
    assert R.dim(2) == 0           # M₂ = {0}
    assert R.weight_monomials(12) == [(0, 2), (3, 0)]
    assert R.weight_monomials(8) == [(2, 0)]
    assert R.weight_monomials(24) == [(0, 4), (3, 2), (6, 0)]


def test_dim_equals_monomial_count_for_all_even_k():
    R = modular_forms_ring()
    for k in range(0, 61, 2):
        assert R.dim(k) == len(R.weight_monomials(k)), k
    for k in (1, 3, 5, 7, 9, 11, 13):
        assert R.dim(k) == 0 and R.weight_monomials(k) == [], k


# ── gate (b): the membership keystones (the structure theorem) ────────────────
def test_keystone1_delta_is_polynomial_in_E4_E6():
    """Δ = (E₄³ − E₆²)/1728 → {(3,0): 1/1728, (0,2): −1/1728} (the structure
    theorem: the cusp form Δ IS a polynomial in E₄, E₆)."""
    rep = modular_forms_ring_represent(_delta(14), 12)
    assert rep == {(3, 0): Q(1, 1728), (0, 2): Q(-1, 1728)}


def test_keystone2_E8_is_E4_squared():
    rep = modular_forms_ring_represent(Eisenstein(8).q_series(14), 8)
    assert rep == {(2, 0): Q(1, 1)}


def test_keystone3_E10_is_E4_E6():
    rep = modular_forms_ring_represent(Eisenstein(10).q_series(14), 10)
    assert rep == {(1, 1): Q(1, 1)}


def test_keystone4_E14_is_E4sq_E6():
    rep = modular_forms_ring_represent(Eisenstein(14).q_series(14), 14)
    assert rep == {(2, 1): Q(1, 1)}


# ── gate (c): the honest rejection (non-modular → None) ───────────────────────
def test_keystone5_non_modular_series_rejected():
    """A non-modular q-series (e.g. [1, 1, 0, 0, …]) @ weight 12 → None (honest
    rejection — it is NOT a level-1 weight-12 modular form)."""
    series = [Q(1, 1), Q(1, 1)] + [Q(0, 1)] * 12
    assert modular_forms_ring_represent(series, 12) is None


def test_random_garbage_series_rejected():
    series = [Q(1, 1), Q(7, 1), Q(-3, 1), Q(2, 1)] + [Q(0, 1)] * 12
    assert modular_forms_ring_represent(series, 12) is None


# ── gate (d): the Δ source-of-truth cross-check vs the rc82 EtaQuotient ────────
def test_delta_source_is_published_eta24_ramanujan_tau():
    """The Δ q-series oracle == 1728·shift of the PUBLISHED rc82 EtaQuotient({1:24})
    = η²⁴ (Ramanujan τ): (E₄³−E₆²)[1:] == 1728·τ(n). The carrier ladder validates
    itself against the prior published rung."""
    N = 14
    e4 = Eisenstein(4).q_series(N)
    e6 = Eisenstein(6).q_series(N)
    diff = _qsub(_qmul(_qmul(e4, e4, N), e4, N), _qmul(e6, e6, N))
    assert diff[0] == Q(0, 1)                       # a CUSP form
    lhs = [c * Q(1, 1728) for c in diff[1:]]
    assert all(c.denominator == 1 for c in lhs)     # exactly divisible by 1728
    tau = EtaQuotient({1: 24}).q_series(N)[:N - 1]
    assert [int(c.numerator) for c in lhs] == tau
    assert tau[:7] == TAU_1_7


# ── gate (e): the level-axis OPEN (a higher-level form correctly → None) ──────
def test_level_axis_open_higher_level_form_returns_none():
    """The honest LEVEL-axis OPEN: the X₀(11) weight-2 newform η²η²(11τ) is a
    GENUINELY higher-level (Γ₀(11)) form — NOT a level-1 form. M₂(SL₂(ℤ))={0}, so
    it correctly returns None here (out of this carrier's ring). The boundary, not
    a bug."""
    x0_11 = [Q(a, 1) for a in (1, -2, -1, 2, 1, 2, -2, 0, -2, -2)]
    assert x0_11[:7] == [Q(a, 1) for a in X0_11]      # the published newform a(n)
    assert modular_forms_ring_represent(x0_11, 2) is None
    # a weight-4 level>1 nonzero series that is not a level-1 form → None
    not_lvl1 = [Q(1, 1), Q(5, 1), Q(0, 1), Q(1, 1)] + [Q(0, 1)] * 10
    assert modular_forms_ring_represent(not_lvl1, 4) is None


# ── zero series + odd-weight edge ─────────────────────────────────────────────
def test_zero_series_and_odd_weight():
    # the zero series at an odd weight (M_k = {0}) → the empty rep {}
    assert modular_forms_ring_represent([Q(0, 1)] * 6, 3) == {}
    # a nonzero series at an odd weight → None (M_k = {0})
    assert modular_forms_ring_represent([Q(1, 1)] + [Q(0, 1)] * 5, 3) is None
    # E₄ itself @4 → {(1,0):1}
    assert modular_forms_ring_represent(Eisenstein(4).q_series(14), 4) == {(1, 0): Q(1, 1)}


def test_too_few_terms_raises():
    with pytest.raises(ValueError):
        modular_forms_ring_represent([Q(1, 1), Q(0, 1)], 12)   # need ≥ dim+2 = 4


# ── a linear combination (a genuine non-monomial level-1 form) ────────────────
def test_linear_combination_of_monomials():
    """A genuine ℚ-combination 2·E₄³ + 3·E₆² (weight 12) round-trips to its rep."""
    N = 14
    e4 = Eisenstein(4).q_series(N)
    e6 = Eisenstein(6).q_series(N)
    e4cubed = _qmul(_qmul(e4, e4, N), e4, N)
    e6sq = _qmul(e6, e6, N)
    f = [Q(2, 1) * a + Q(3, 1) * b for a, b in zip(e4cubed, e6sq)]
    rep = modular_forms_ring_represent(f, 12)
    assert rep == {(3, 0): Q(2, 1), (0, 2): Q(3, 1)}


# ── gate (f): Python==C parity on .represent ─────────────────────────────────
@pytest.mark.skipif(not _native.has_native_modular_forms_ring(),
                    reason="native srmech_modular_forms_ring not loaded")
def test_python_c_parity_keystones():
    """The native path and the pure-Python oracle emit IDENTICAL reps / None (do
    NOT trust the C — compare element-for-element)."""
    R = ModularFormsRing()
    cases = [
        (_delta(14), 12),
        (Eisenstein(8).q_series(14), 8),
        (Eisenstein(10).q_series(14), 10),
        (Eisenstein(14).q_series(14), 14),
        (Eisenstein(4).q_series(14), 4),
        ([Q(1, 1), Q(1, 1)] + [Q(0, 1)] * 12, 12),    # non-modular → None
    ]
    for series, k in cases:
        f = [c if isinstance(c, Q) else Q(c, 1) for c in series]
        mono = R.weight_monomials(k)
        got_c = _native.modular_forms_ring_represent_c([c.as_pair() for c in f], k)
        assert got_c is not None
        has, pairs = got_c
        c_rep = ({mono[i]: Q(pairs[i][0], pairs[i][1]) for i in range(len(mono))}
                 if has else None)
        py_rep = R._represent_py(f, k, mono)
        assert c_rep == py_rep, (k, c_rep, py_rep)


@pytest.mark.skipif(not _native.has_native_modular_forms_ring(),
                    reason="native srmech_modular_forms_ring not loaded")
def test_python_c_parity_stress_sweep():
    R = ModularFormsRing()
    for k in (4, 6, 8, 10, 12, 14, 16, 18, 20, 24):
        f = Eisenstein(k).q_series(2 * R.dim(k) + 6)
        got_c = _native.modular_forms_ring_represent_c([c.as_pair() for c in f], k)
        assert got_c is not None
        has, pairs = got_c
        mono = R.weight_monomials(k)
        c_rep = ({mono[i]: Q(pairs[i][0], pairs[i][1]) for i in range(len(mono))}
                 if has else None)
        py_rep = R._represent_py(f, k, mono)
        assert c_rep == py_rep, (k, c_rep, py_rep)


def test_pure_python_oracle_matches_targets_without_native():
    """The COMPLETE pure-Python body alone reproduces the keystones (so the carrier
    is correct on a no-C host)."""
    R = ModularFormsRing()
    rep = R._represent_py(_delta(14), 12, R.weight_monomials(12))
    assert rep == {(3, 0): Q(1, 1728), (0, 2): Q(-1, 1728)}
    assert R._represent_py(Eisenstein(8).q_series(14), 8,
                           R.weight_monomials(8)) == {(2, 0): Q(1, 1)}


# ── ModularForm wrapper + equality / repr ─────────────────────────────────────
def test_modular_form_wrapper_roundtrips():
    R = modular_forms_ring()
    rep = R.represent(_delta(14), 12)
    mf = ModularForm(12, rep)
    assert mf.weight == 12
    assert mf.rep == {(3, 0): Q(1, 1728), (0, 2): Q(-1, 1728)}
    # the reconstructed q-series equals Δ (round-trip)
    assert mf.q_series(14) == _delta(14)
    # E₈ wrapper reconstructs E₄²
    e8 = ModularForm(8, {(2, 0): Q(1, 1)})
    assert e8.q_series(10) == Eisenstein(8).q_series(10)


def test_modular_form_weight_mismatch_rejected():
    with pytest.raises(ValueError):
        ModularForm(12, {(2, 0): Q(1, 1)})    # (2,0) has weight 8, not 12


def test_ring_equality_and_repr():
    a = modular_forms_ring()
    b = ModularFormsRing()
    assert a == b and a.equals(b)
    assert hash(a) == hash(b)
    assert "ModularFormsRing" in repr(a)
    assert "ℂ[E₄,E₆]" in repr(a)


# ── gate (g): the carrier source is numpy / math / abs() free ────────────────
def test_modular_forms_ring_source_is_numpy_math_abs_free():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "modular_forms_ring.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert re.search(r"abs\([^)]", text) is None    # no bare abs() CALL
    assert "float(" not in text                     # no float in the carrier body


# ── gate (h): the REDUCER is a ToolEntry → tools.total 342; carrier accessors not
def test_represent_is_a_tool_entry_total_341():
    """``modular_forms_ring_represent`` is a genuine REDUCER (the WEIGHT-axis analog
    of the Σ-row gosper/zeilberger/wz_certificate) → it IS a registered ToolEntry,
    which took the shipped tool count 340 → 341 at rc84 (now 342 with the rc89
    quasimodular reducer). The bare carrier constructor + weight_monomials/dim are
    NOT ToolEntries."""
    from srmech.amsc.tool_schema import get_tool_schema
    shipped = [t for t in get_tool_schema().tools if not t.name.startswith("test.")]
    assert len(shipped) == 384
    names = {t.name for t in shipped}
    assert "srmech.amsc.modular_forms_ring.modular_forms_ring_represent" in names
    # the carrier constructor + the pure accessors are NOT ToolEntries
    assert "srmech.amsc.modular_forms_ring.modular_forms_ring" not in names
    assert not any(nm.endswith(".weight_monomials") for nm in names)
    assert not any(nm.endswith(".dim") for nm in names)


def test_exported_from_amsc():
    from srmech.amsc import (
        ModularFormsRing as ExportedRing,
        ModularForm as ExportedForm,
        modular_forms_ring as exported_ctor,
        modular_forms_ring_represent as exported_rep,
    )
    assert ExportedRing is ModularFormsRing
    assert ExportedForm is ModularForm
    assert exported_ctor is modular_forms_ring
    assert exported_rep is modular_forms_ring_represent
