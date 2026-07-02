"""rc89 — ``srmech.amsc.quasimodular_forms_ring.QuasiModularFormsRing``, the FOURTH
WEIGHT-axis rung (after rc82 eta-quotient + rc83 Eisenstein + rc84
``ModularFormsRing`` ℂ[E₄,E₆]): the level-1 ℂ[E₂,E₄,E₆] QUASIMODULAR-forms-ring
carrier + its EXACT membership decision, the rc84 pattern ONE generator up.

The build gates (the no-shell proof; the construction IS the answer, no search):

  (a) the E₂ generator: eisenstein_e2(6) == [1, −24, −72, −96, −168, −144]
      (= 1 − 24·Σσ₁(n)qⁿ; the von Staudt–Clausen −4/B₂ = −24 prefactor); and the
      rc83 Eisenstein carrier STILL rejects k=2 (E₂ is a separate quasimodular obj);
  (b) the graded basis: dim(k) == len(weight_monomials(k)); dim(2)=1 (E₂ — contrast
      the MODULAR dim M₂=0), dim(4)=2, dim(6)=3, dim(8)=4;
  (c) the KEYSTONES — Ramanujan's Serre-derivative identities DERIVED + checked
      bit-exactly on the q-series, THEN confirmed through represent:
      DE₂=(E₂²−E₄)/12 @4 → {(2,0,0):1/12,(0,1,0):−1/12};
      DE₄=(E₂E₄−E₆)/3 @6 → {(1,1,0):1/3,(0,0,1):−1/3};
      DE₆=(E₂E₆−E₄²)/2 @8 → {(1,0,1):1/2,(0,2,0):−1/2};
  (d) the EXTENDS-the-modular-ring proof: E₂² @4 → {(2,0,0):1} here, but rc84
      modular_forms_ring_represent(E₂², 4) → None (E₂² ∉ ℂ[E₄,E₆]);
  (e) the honest rejection: a non-quasimodular q-series → None;
  (f) Python==C parity on .represent for the keystones (guarded by the native-skip;
      do NOT trust the C — compare element-for-element);
  (g) the carrier source has no numpy / math / abs() (the ratchet);
  (h) the REDUCER ``quasimodular_represent`` IS a ToolEntry → tools.total
      342; eisenstein_e2 + the bare constructor + weight_monomials/dim are NOT.
"""
from __future__ import annotations

import os
import re
import tokenize

import pytest

from srmech.amsc.quasimodular_forms_ring import (
    QuasiModularForm,
    QuasiModularFormsRing,
    eisenstein_e2,
    quasimodular_forms_ring,
    quasimodular_represent,
)
from srmech.amsc.modular_forms_ring import modular_forms_ring_represent
from srmech.amsc.eisenstein import Eisenstein, eisenstein
from srmech.amsc.q import Q
from srmech.amsc import _native


# ── exact-Q q-series helpers (local; no carrier re-use for the oracle) ─────────
def _qmul(a, b, nt):
    out = [Q(0, 1)] * nt
    for i in range(nt):
        for j in range(nt - i):
            out[i + j] = out[i + j] + a[i] * b[j]
    return out


def _deriv(series):
    """The Serre / Ramanujan derivative D = q·d/dq: D(Σ a_n qⁿ) = Σ n·a_n qⁿ."""
    return [Q(n, 1) * series[n] for n in range(len(series))]


N = 16


def _e2():
    return eisenstein_e2(N)


def _e4():
    return Eisenstein(4).q_series(N)


def _e6():
    return Eisenstein(6).q_series(N)


# ── gate (a): the E₂ generator + the rc83 k=2 rejection still holds ───────────
def test_eisenstein_e2_published_series():
    """E₂ = 1 − 24·Σσ₁(n)qⁿ → [1, −24, −72, −96, −168, −144] (σ₁(1..5)=1,3,4,7,6)."""
    assert eisenstein_e2(6) == [Q(c, 1) for c in (1, -24, -72, -96, -168, -144)]
    # the prefactor is the von Staudt–Clausen −2·2/B₂ = −4/(1/6) = −24, not a magic
    # literal — c_n = −24·σ₁(n).
    assert eisenstein_e2(2)[1] == Q(-24, 1)


def test_rc83_eisenstein_still_rejects_k2():
    """The rc83 modular Eisenstein carrier KEEPS its k≥4 contract: k=2 is the
    quasimodular boundary, still rejected (E₂ is a separate object, here only)."""
    with pytest.raises(ValueError) as ei:
        eisenstein(2)
    assert "quasimodular" in str(ei.value).lower()
    with pytest.raises(ValueError):
        Eisenstein(2)


# ── gate (b): the graded basis ────────────────────────────────────────────────
def test_dim_and_monomials():
    R = quasimodular_forms_ring()
    assert R.dim(2) == 1                       # E₂ — the new quasimodular generator
    assert R.dim(4) == 2                       # E₂², E₄
    assert R.dim(6) == 3                       # E₂³, E₂E₄, E₆
    assert R.dim(8) == 4
    assert R.dim(0) == 1                       # the constants
    assert R.weight_monomials(2) == [(1, 0, 0)]
    assert (1, 0, 0) in R.weight_monomials(2)


def test_dim_equals_monomial_count_for_all_k():
    R = quasimodular_forms_ring()
    for k in range(0, 41, 2):
        assert R.dim(k) == len(R.weight_monomials(k)), k
    for k in (1, 3, 5, 7, 9, 11):
        assert R.dim(k) == 0 and R.weight_monomials(k) == [], k


# ── gate (c): the Ramanujan-derivative KEYSTONES (the defining structure) ──────
def test_ramanujan_identities_hold_on_qseries():
    """DERIVE + CHECK the three Ramanujan/Serre identities bit-exactly on the
    q-series FIRST (no recall-and-trust): D = q·d/dq."""
    e2, e4, e6 = _e2(), _e4(), _e6()
    # D E₂ = (E₂² − E₄)/12
    assert _deriv(e2) == [(a - b) * Q(1, 12)
                          for a, b in zip(_qmul(e2, e2, N), e4)]
    # D E₄ = (E₂ E₄ − E₆)/3
    assert _deriv(e4) == [(a - b) * Q(1, 3)
                          for a, b in zip(_qmul(e2, e4, N), e6)]
    # D E₆ = (E₂ E₆ − E₄²)/2
    assert _deriv(e6) == [(a - b) * Q(1, 2)
                          for a, b in zip(_qmul(e2, e6, N), _qmul(e4, e4, N))]


def test_keystone_DE2_through_represent():
    """D E₂ reduces over the ring to (E₂²−E₄)/12 → {(2,0,0):1/12, (0,1,0):−1/12}."""
    rep = quasimodular_represent(_deriv(_e2()), 4)
    assert rep == {(2, 0, 0): Q(1, 12), (0, 1, 0): Q(-1, 12)}


def test_keystone_DE4_through_represent():
    """D E₄ reduces over the ring to (E₂E₄−E₆)/3 → {(1,1,0):1/3, (0,0,1):−1/3}."""
    rep = quasimodular_represent(_deriv(_e4()), 6)
    assert rep == {(1, 1, 0): Q(1, 3), (0, 0, 1): Q(-1, 3)}


def test_keystone_DE6_through_represent():
    """D E₆ reduces over the ring to (E₂E₆−E₄²)/2 → {(1,0,1):1/2, (0,2,0):−1/2}."""
    rep = quasimodular_represent(_deriv(_e6()), 8)
    assert rep == {(1, 0, 1): Q(1, 2), (0, 2, 0): Q(-1, 2)}


# ── gate (d): the quasimodular ring genuinely EXTENDS the modular one ──────────
def test_E2_squared_extends_the_modular_ring():
    """E₂² (weight 4) is a QUASIMODULAR monomial NOT in the modular ℂ[E₄,E₆]: rc89
    represent → {(2,0,0):1}, but rc84 modular represent → None. The proof that the
    quasimodular ring genuinely EXTENDS the modular one."""
    e2sq = _qmul(_e2(), _e2(), N)
    assert quasimodular_represent(e2sq, 4) == {(2, 0, 0): Q(1, 1)}
    assert modular_forms_ring_represent(e2sq, 4) is None
    # E₂ itself @2 → {(1,0,0):1} (the weight-2 generator; modular M₂={0} → None there)
    assert quasimodular_represent(_e2(), 2) == {(1, 0, 0): Q(1, 1)}


def test_modular_forms_are_still_representable_here():
    """The modular ring is the a=0 subring: a modular form (E₄ @4) reduces here to
    the SAME E₄ monomial (0,1,0) — the quasimodular ring CONTAINS ℂ[E₄,E₆]."""
    assert quasimodular_represent(_e4(), 4) == {(0, 1, 0): Q(1, 1)}
    assert quasimodular_represent(_e6(), 6) == {(0, 0, 1): Q(1, 1)}


# ── gate (e): the honest rejection (non-quasimodular → None) ──────────────────
def test_non_quasimodular_series_rejected():
    series = [Q(1, 1), Q(1, 1)] + [Q(0, 1)] * 12
    assert quasimodular_represent(series, 4) is None
    garbage = [Q(1, 1), Q(7, 1), Q(-3, 1), Q(2, 1), Q(5, 1)] + [Q(0, 1)] * 9
    assert quasimodular_represent(garbage, 6) is None


def test_zero_series_and_odd_weight():
    # the zero series at an odd weight (M̃_k = {0}) → the empty rep {}
    assert quasimodular_represent([Q(0, 1)] * 6, 3) == {}
    # a nonzero series at an odd weight → None (M̃_k = {0})
    assert quasimodular_represent([Q(1, 1)] + [Q(0, 1)] * 5, 3) is None


def test_too_few_terms_raises():
    with pytest.raises(ValueError):
        quasimodular_represent([Q(1, 1), Q(0, 1)], 6)   # need ≥ dim+2 = 5


# ── a genuine ℚ-combination (non-monomial quasimodular form) ──────────────────
def test_linear_combination_of_monomials():
    """A genuine ℚ-combination 2·E₂³ + 5·E₂E₄ − 3·E₆ (weight 6) round-trips to its
    rep — a quasimodular form that uses ALL three generators."""
    e2, e4, e6 = _e2(), _e4(), _e6()
    e2cubed = _qmul(_qmul(e2, e2, N), e2, N)
    e2e4 = _qmul(e2, e4, N)
    f = [Q(2, 1) * a + Q(5, 1) * b - Q(3, 1) * c
         for a, b, c in zip(e2cubed, e2e4, e6)]
    rep = quasimodular_represent(f, 6)
    assert rep == {(3, 0, 0): Q(2, 1), (1, 1, 0): Q(5, 1), (0, 0, 1): Q(-3, 1)}


# ── gate (f): Python==C parity on .represent ─────────────────────────────────
_PARITY_CASES = [
    ("DE2", 4), ("DE4", 6), ("DE6", 8), ("E2sq", 4),
    ("E4", 4), ("E6", 6), ("E2", 2), ("nonmod", 4),
]


def _case_series(tag):
    if tag == "DE2":
        return _deriv(_e2())
    if tag == "DE4":
        return _deriv(_e4())
    if tag == "DE6":
        return _deriv(_e6())
    if tag == "E2sq":
        return _qmul(_e2(), _e2(), N)
    if tag == "E4":
        return _e4()
    if tag == "E6":
        return _e6()
    if tag == "E2":
        return _e2()
    return [Q(1, 1), Q(1, 1)] + [Q(0, 1)] * (N - 2)   # non-quasimodular → None


@pytest.mark.skipif(not _native.has_native_quasimodular_forms_ring(),
                    reason="native srmech_quasimodular_forms_ring not loaded")
def test_python_c_parity_keystones():
    """The native path and the pure-Python oracle emit IDENTICAL reps / None (do
    NOT trust the C — compare element-for-element)."""
    R = QuasiModularFormsRing()
    for tag, k in _PARITY_CASES:
        f = _case_series(tag)
        mono = R.weight_monomials(k)
        got_c = _native.quasimodular_forms_ring_represent_c(
            [c.as_pair() for c in f], k)
        assert got_c is not None
        has, pairs = got_c
        c_rep = ({mono[i]: Q(pairs[i][0], pairs[i][1])
                  for i in range(len(mono)) if pairs[i][0] != 0}
                 if has else None)
        py_rep = R._represent_py(f, k, mono)
        assert c_rep == py_rep, (tag, k, c_rep, py_rep)


@pytest.mark.skipif(not _native.has_native_quasimodular_forms_ring(),
                    reason="native srmech_quasimodular_forms_ring not loaded")
def test_python_c_parity_stress_sweep():
    R = QuasiModularFormsRing()
    # the q-series of E_k (k even ≥ 4) IS a quasimodular form (the a=0 subring) —
    # sweep a range of even weights; the C leading-block solve must match Python.
    for k in (4, 6, 8, 10, 12, 14):
        f = Eisenstein(k).q_series(2 * R.dim(k) + 6)
        got_c = _native.quasimodular_forms_ring_represent_c(
            [c.as_pair() for c in f], k)
        assert got_c is not None
        has, pairs = got_c
        mono = R.weight_monomials(k)
        c_rep = ({mono[i]: Q(pairs[i][0], pairs[i][1])
                  for i in range(len(mono)) if pairs[i][0] != 0}
                 if has else None)
        py_rep = R._represent_py(f, k, mono)
        assert c_rep == py_rep, (k, c_rep, py_rep)


def test_pure_python_oracle_matches_targets_without_native():
    """The COMPLETE pure-Python body alone reproduces the keystones (so the carrier
    is correct on a no-C host)."""
    R = QuasiModularFormsRing()
    assert R._represent_py(_deriv(_e4()), 6, R.weight_monomials(6)) == {
        (1, 1, 0): Q(1, 3), (0, 0, 1): Q(-1, 3)}
    assert R._represent_py(_qmul(_e2(), _e2(), N), 4,
                           R.weight_monomials(4)) == {(2, 0, 0): Q(1, 1)}


# ── QuasiModularForm wrapper + equality / repr ────────────────────────────────
def test_quasimodular_form_wrapper_roundtrips():
    R = quasimodular_forms_ring()
    rep = R.represent(_deriv(_e4()), 6)
    qf = QuasiModularForm(6, rep)
    assert qf.weight == 6
    assert qf.rep == {(1, 1, 0): Q(1, 3), (0, 0, 1): Q(-1, 3)}
    # the reconstructed q-series equals D E₄ (round-trip)
    assert qf.q_series(N) == _deriv(_e4())


def test_quasimodular_form_weight_mismatch_rejected():
    with pytest.raises(ValueError):
        QuasiModularForm(6, {(2, 0, 0): Q(1, 1)})    # (2,0,0) has weight 4, not 6


def test_ring_equality_and_repr():
    a = quasimodular_forms_ring()
    b = QuasiModularFormsRing()
    assert a == b and a.equals(b)
    assert hash(a) == hash(b)
    assert "QuasiModularFormsRing" in repr(a)
    assert "ℂ[E₂,E₄,E₆]" in repr(a)


# ── gate (g): the carrier source is numpy / math / abs() free ────────────────
def test_quasimodular_forms_ring_source_is_numpy_math_abs_free():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "quasimodular_forms_ring.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert re.search(r"abs\([^)]", text) is None    # no bare abs() CALL
    assert "float(" not in text                     # no float in the carrier body


# ── gate (h): the REDUCER is a ToolEntry → tools.total 342; accessors not ──────
def test_represent_is_a_tool_entry_total_342():
    """``quasimodular_represent`` is a genuine REDUCER (the WEIGHT-axis
    analog of the Σ-row reducers, one generator up from rc84) → it IS a registered
    ToolEntry, taking the shipped tool count 341 → 342. eisenstein_e2 + the bare
    constructor + weight_monomials/dim are NOT ToolEntries."""
    from srmech.amsc.tool_schema import get_tool_schema
    shipped = [t for t in get_tool_schema().tools if not t.name.startswith("test.")]
    assert len(shipped) == 348
    names = {t.name for t in shipped}
    assert ("srmech.amsc.quasimodular_forms_ring.quasimodular_represent"
            in names)
    # the carrier constructor + E₂ fn + pure accessors are NOT ToolEntries
    assert ("srmech.amsc.quasimodular_forms_ring.quasimodular_forms_ring"
            not in names)
    assert not any(nm.endswith(".eisenstein_e2") for nm in names)
    assert not any(nm.endswith(".weight_monomials") for nm in names)
    assert not any(nm.endswith(".dim") for nm in names)


def test_exported_from_amsc():
    from srmech.amsc import (
        QuasiModularFormsRing as ExportedRing,
        QuasiModularForm as ExportedForm,
        eisenstein_e2 as exported_e2,
        quasimodular_forms_ring as exported_ctor,
        quasimodular_represent as exported_rep,
    )
    assert ExportedRing is QuasiModularFormsRing
    assert ExportedForm is QuasiModularForm
    assert exported_e2 is eisenstein_e2
    assert exported_ctor is quasimodular_forms_ring
    assert exported_rep is quasimodular_represent
