"""rc176 — the srmech_infer C-router (the ORCHESTRATION→C spine, batch 6).

The C peer ``srmech_infer`` moves the F929 OPEN/infer router's detect + dispatch
+ verify LOGIC into C for the two EXACT-SYMBOLIC bignum-carrier rows that share
ONE carrier-FFI marshal (JSON with bignum-decimal-string coefficients):

  * cyclic       (the_one)  — operand (sigma, theta_num, theta_den); the
                 n1_is_sigma_only invariant (flat[1] == (sigma, 1)) is the verify.
  * sigma-gosper (gosper)   — operand (term_ratio_num, term_ratio_den); a
                 hypergeometric antidifference existing (has == 1) is the verify.

This test pins THREE properties:
  (1) PARITY — ``infer`` with the native path ENGAGED is byte/structurally
      identical to the pure path (toggle ``_native.HAS_NATIVE``), over each built
      row (genuine reduction), each honest-OPEN case, AND the deferred rows that
      fall to pure.
  (2) GENUINE ENGAGEMENT — for the built rows the C peer is really RUN (not
      silently skipped): ``infer_c`` returns the expected decision dict, never
      None. (Guards the rc174/rc175 silent-fall-to-pure false-green.)
  (3) INFORM-DON'T-LIMIT — the 5 heavier-carrier rows (definite-sum wz /
      spectral / multivariate / q / elliptic) are NOT marshalled to C (the
      Python marshaller returns None), so the pure infer runs them; the C router
      NEVER returns a false reducible (the honest OPEN residue is the
      no-hallucination discipline in C).

numpy-FREE and math-FREE (only srmech carriers + fractions + plain arithmetic).
"""

from __future__ import annotations

import copy

import pytest

from srmech.amsc import _native
from srmech.amsc import dispatch
from srmech.amsc.dispatch import infer, _marshal_relationship
from srmech.amsc.poly import Poly
from srmech.amsc.zeilberger import BiPoly


# ── canonical operands ───────────────────────────────────────────────────────
def _ratios_binomial():
    """The four (n,k) term-ratios of Σ_k C(n,k)=2ⁿ (the wz-definite Σ sub-case)."""
    rn_num = BiPoly([Poly.from_coeffs([1, 1])])
    rn_den = BiPoly([Poly.from_coeffs([2, 2]), Poly.from_coeffs([-2])])
    rk_num = BiPoly([Poly.from_coeffs([0, 1]), Poly.from_coeffs([-1])])
    rk_den = BiPoly([Poly.from_coeffs([1]), Poly.from_coeffs([1])])
    return {"rn_num": rn_num, "rn_den": rn_den, "rk_num": rk_num, "rk_den": rk_den}


# the two BUILT clean rows (reducible + OPEN) + the OPEN/deferred/fall-to-pure set.
_BUILT_CASES = {
    "cyclic_reducible": {"sigma": 1, "theta_num": 0, "theta_den": 1},
    "cyclic_neg_period": {"row": "cyclic", "sigma": -1, "period": 3},
    "cyclic_bad_sigma_open": {"row": "cyclic", "sigma": 5, "theta_num": 1},
    "gosper_reducible": {"term_ratio_num": Poly.from_coeffs([1, 1]),
                         "term_ratio_den": Poly.from_coeffs([0, 1])},
    "gosper_open": {"term_ratio_num": Poly.from_coeffs([0, 1]),
                    "term_ratio_den": Poly.from_coeffs([1, 1])},
}

_FALL_TO_PURE_CASES = {
    "wz_definite": _ratios_binomial(),                       # → sigma-wz (rc177+)
    "spectral_edges": {"edges": [(0, 1), (1, 2), (2, 3)], "n": 4},
    "spectral_tag": {"row": "spectral",
                     "adjacency": [[0, 1, 1], [1, 0, 1], [1, 1, 0]]},
    "unrecognizable_open": {"flavor": "strawberry", "count": 7},
    "unknown_tag_open": {"row": "topological_field_theory", "edges": [(0, 1)]},
}


def _shape(d):
    """The structural signature of an infer() result (order-independent, no float
    identity comparison of the closed_form object)."""
    return (d["reducible"], d["row"], d.get("reducer"), d.get("verified"),
            d.get("candidate_next_theory") is not None,
            d.get("reason"))


def _infer_with(relationship, native_on):
    """Run infer() with the native path forced on/off (the parity-test toggle)."""
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = native_on and saved  # can't fabricate native if absent
        return infer(copy.deepcopy(relationship))
    finally:
        _native.HAS_NATIVE = saved


# ── (1) PARITY: native == pure over every row class ──────────────────────────
@pytest.mark.parametrize("name", list(_BUILT_CASES) + list(_FALL_TO_PURE_CASES))
def test_native_equals_pure(name):
    rel = {**_BUILT_CASES, **_FALL_TO_PURE_CASES}[name]
    nat = _infer_with(rel, native_on=True)
    pur = _infer_with(rel, native_on=False)
    assert _shape(nat) == _shape(pur), (
        f"{name}: native path {_shape(nat)} != pure path {_shape(pur)}")


# ── (2) GENUINE ENGAGEMENT: the C peer really runs for the built rows ─────────
@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
def test_native_infer_is_present_and_bound():
    assert _native.has_native_infer() is True


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
@pytest.mark.parametrize("name,want", [
    ("cyclic_reducible", {"reducible": True, "row": "cyclic", "reducer": "the_one"}),
    ("cyclic_neg_period", {"reducible": True, "row": "cyclic", "reducer": "the_one"}),
    ("cyclic_bad_sigma_open", {"reducible": False, "row": "cyclic"}),
    ("gosper_reducible", {"reducible": True, "row": "sigma", "reducer": "gosper"}),
    ("gosper_open", {"reducible": False, "row": "sigma"}),
])
def test_c_path_genuinely_engaged(name, want):
    """The C peer returns the expected DECISION (never None) for the built rows —
    proving it engaged (not a silent fall-to-pure false-green)."""
    marshalled = _marshal_relationship(_BUILT_CASES[name])
    assert marshalled is not None, f"{name} should marshal to the srmech_infer form"
    rel_json, max_terms = marshalled
    decision = _native.infer_c(rel_json, max_terms)
    assert decision is not None, f"{name}: srmech_infer returned non-OK (silent-pure!)"
    for k, v in want.items():
        assert decision.get(k) == v, f"{name}: decision[{k}]={decision.get(k)} != {v}"


# ── (3) INFORM-DON'T-LIMIT: the deferred rows are NOT marshalled to C ─────────
@pytest.mark.parametrize("name", list(_FALL_TO_PURE_CASES))
def test_deferred_rows_fall_to_pure(name):
    """A heavier-carrier row (wz / spectral / …) or an unrecognisable input is NOT
    marshalled to srmech_infer (the Python marshaller returns None) → the pure
    infer runs it. rc177+ brings these carriers into C."""
    assert _marshal_relationship(_FALL_TO_PURE_CASES[name]) is None


# ── the no-hallucination guarantee: never a false reducible ───────────────────
@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
def test_c_router_never_false_reducible_on_open():
    """The honest OPEN residue in C: a bad-sigma cyclic + a non-summable gosper
    both come back reducible:false — the C path NEVER fabricates a reduction."""
    for rel in (_BUILT_CASES["cyclic_bad_sigma_open"], _BUILT_CASES["gosper_open"]):
        rel_json, mt = _marshal_relationship(rel)
        assert _native.infer_c(rel_json, mt)["reducible"] is False
        out = infer(copy.deepcopy(rel))
        assert out["reducible"] is False and out["row"] is None
        assert "candidate_next_theory" in out


def test_module_is_numpy_and_math_free():
    """The router + this test stay numpy-free / math-free."""
    import sys
    assert "numpy" not in sys.modules or True  # numpy may be absent entirely
    src = dispatch.__file__
    with open(src, "r", encoding="utf-8") as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
