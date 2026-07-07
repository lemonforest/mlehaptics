"""rc171 — the ORCHESTRATION→C spine, batch 1: the op-provenance verdict /
carry / re-verify logic gains C peers (v0.9.0rc171).

The five ``srmech.amsc.op_provenance`` verdict/carry ops move
``owed_orchestration`` → ``composes_c`` — each now dispatches its provenance
LOGIC to a C peer so a bare-C host (no Python, no ``json.dumps``) builds +
compares op-provenance records:

    op_verdict              -> srmech_op_verdict            (EQUAL/UNKNOWN over
                                                             the canonical chain hash)
    family_verdict          -> srmech_family_verdict        (SAME_TARGET/UNKNOWN)
    carry (the RECORD)      -> srmech_op_carry              (input_sha256 + chain)
    lossy_projection_record -> srmech_lossy_projection_record
    reproject (the RE-VERIFY)-> srmech_op_reproject         (input_sha256 re-hash)

Each composes the existing kernels (``srmech_op_provenance_hash`` / the
``srmech_json`` parser+writer / ``srmech_sha256_hex``) — no new parser, no new
hash. This file proves, per op, that the native path == the forced-pure path
(byte/structurally-identical) across a representative sweep, AND that the native
peers are genuinely EXERCISED (return non-None) under HAS_NATIVE — not silently
shimmed to Python.

numpy-free (stdlib json / fractions only); no ``abs()``; no libm.
"""
from __future__ import annotations

import copy
from fractions import Fraction

import pytest

from srmech.amsc import _native
from srmech.amsc import op_provenance as op

_HAS_NATIVE = _native.HAS_NATIVE and _native.LIB is not None


def _both(fn):
    """(native_result, forced_pure_result) for a zero-arg callable."""
    native_result = fn()
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = False
        pure_result = fn()
    finally:
        _native.HAS_NATIVE = saved
    return native_result, pure_result


def _flatten_floats(x, out):
    """Append x's scalar float components to `out`; False if x isn't numeric.

    Handles numbers (int/float/Fraction/complex) and nested numeric carriers
    (Vec/Mat/tuple/list are iterable → recurse). Strings are NOT numeric.
    """
    if isinstance(x, bool):  # bool is an int subclass; treat as non-numeric here
        return False
    if isinstance(x, (int, float, Fraction)):
        out.append(float(x))
        return True
    if isinstance(x, complex):
        out.append(x.real)
        out.append(x.imag)
        return True
    if isinstance(x, str):
        return False
    try:
        items = list(x)
    except TypeError:
        return False
    for e in items:
        if not _flatten_floats(e, out):
            return False
    return True


def _values_close(a, b, tol=1e-9):
    """Exact-equal for exact-valued ops; within-tol for NUMERIC carriers.

    ``carry`` faithfully wraps the op's OUTPUT value — but the two Class-L
    numeric eigensolvers (jacobi_eigvals / symmetric_eigendecompose) agree
    native-vs-pure only within FP tolerance (the F2 within-tol foundation,
    not byte-identical). The carry PROVENANCE is byte-identical regardless
    (asserted separately); only the raw numeric value floats at the ULP.
    """
    if a == b:
        return True
    fa, fb = [], []
    if not _flatten_floats(a, fa) or not _flatten_floats(b, fb):
        return False
    if len(fa) != len(fb):
        return False
    return all(-tol <= (x - y) <= tol for x, y in zip(fa, fb))


# The registered carry ops exercised (an INTERIOR series tower, an EDGE
# CF tower, and the Class-L float-leaf frontier).
_CARRY_CASES = [
    ("srmech.amsc.rational.sin_series_truncate",
     {"numerator": 1, "denominator": 1}, {"num_terms": 8}),
    ("srmech.amsc.rational.cos_series_truncate",
     {"numerator": 2, "denominator": 3}, {"num_terms": 10}),
    ("srmech.amsc.rational.exp_series_truncate",
     {"numerator": -1, "denominator": 4}, {"num_terms": 12}),
    ("srmech.amsc.rational.best_rational",
     {"numerator": 355, "denominator": 113}, {"max_denominator": 1000}),
    ("srmech.amsc.laplacian.jacobi_eigvals",
     {"matrix": [[2.0, -1.0, 0.0], [-1.0, 2.0, -1.0], [0.0, -1.0, 2.0]]}, None),
    ("srmech.amsc.laplacian.symmetric_eigendecompose",
     {"matrix": [[4.0, 0.0], [0.0, 9.0]]}, None),
]

# The lossy-projection input sets: exact int, exact rational/bigint, an
# inexact float leaf, a NESTED inexact leaf (the C tree scan must find it),
# and the empty-inputs edge.
_LOSSY_INPUTS = [
    {"R": 7, "lossy": [1, 2, 3]},
    {"R": 7, "big": 10 ** 25, "r": Fraction(3, 7)},
    {"R": 7, "x": 1.5},
    {"nested": [1, {"deep": 2.5}]},
    {"z": complex(1.5, -2.5)},
    {},
]


# ──────────────────────────────────────────────────────────────────────
# The native peers are genuinely exercised (not silently shimmed).
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.skipif(not _HAS_NATIVE, reason="native lib absent")
def test_native_peers_are_exercised():
    r = op.carry("srmech.amsc.rational.sin_series_truncate",
                 {"numerator": 1, "denominator": 1}, {"num_terms": 8})
    prov = r["provenance"]
    assert op._verdict_native(prov, prov) == "EQUAL"
    assert op._family_verdict_native(prov, prov) == "SAME_TARGET"
    assert op._reproject_verify_native(prov, r["inputs"]) is True
    cn = op._carry_record_native(
        "srmech.amsc.rational.sin_series_truncate", r["inputs"],
        prov["params"], prov["family"], prov["rung"])
    assert isinstance(cn, dict) and cn == prov
    ln = op._lossy_record_native("o.p", {"a": 1}, "hdc")
    assert isinstance(ln, dict)


# ──────────────────────────────────────────────────────────────────────
# carry — the RECORD (native == pure), plus the value + canonical inputs.
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("opname,inp,params", _CARRY_CASES)
def test_carry_native_equals_pure(opname, inp, params):
    nat, pure = _both(lambda: op.carry(opname, inp, params))
    assert nat["provenance"] == pure["provenance"]
    # value: exact for exact-valued ops; within-tol for the numeric
    # eigensolvers (native/pure agree within FP tol, not byte-identical —
    # the F2 within-tol foundation). The provenance above is byte-identical.
    assert _values_close(nat["value"], pure["value"])
    assert nat["inputs"] == pure["inputs"]
    # the chain hash is present + well-formed 64-hex
    ch = nat["provenance"]["chain_sha256"]
    assert isinstance(ch, str) and len(ch) == 64


def test_carry_family_override_native_equals_pure():
    nat, pure = _both(lambda: op.carry(
        "srmech.amsc.rational.best_rational",
        {"numerator": 1, "denominator": 1}, {"max_denominator": 50},
        family={"target_id": "sin(1/1)"}))
    assert nat["provenance"] == pure["provenance"]
    assert nat["provenance"]["family"]["target_id"] == "sin(1/1)"
    assert nat["provenance"]["family"]["tower_kind"] == "edge"


def test_carry_float_leaf_marks_inexact_and_no_family():
    # a float-leaf matrix is an UNNAMED target: leaves_exact False, family None.
    nat, pure = _both(lambda: op.carry(
        "srmech.amsc.laplacian.jacobi_eigvals",
        {"matrix": [[2.0, -1.0], [-1.0, 2.0]]}))
    assert nat["provenance"] == pure["provenance"]
    assert nat["provenance"]["leaves_exact"] is False
    assert nat["provenance"]["family"] is None


# ──────────────────────────────────────────────────────────────────────
# lossy_projection_record — native == pure across exact / inexact / nested.
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("inputs", _LOSSY_INPUTS)
def test_lossy_projection_record_native_equals_pure(inputs):
    nat, pure = _both(lambda: op.lossy_projection_record("o.p", inputs))
    assert nat == pure
    assert nat["family"] is None
    assert nat["params"] == {} and nat["rung"] == {}
    assert nat["projection_kind"] == "hdc"


def test_lossy_nested_inexact_leaf_detected():
    # the C leaves_exact tree scan must reach a float nested inside a list.
    nat, pure = _both(
        lambda: op.lossy_projection_record("o.p", {"nested": [1, {"d": 2.5}]}))
    assert nat == pure
    assert nat["leaves_exact"] is False


# ──────────────────────────────────────────────────────────────────────
# op_verdict — EQUAL / UNKNOWN (never a false UNEQUAL).
# ──────────────────────────────────────────────────────────────────────

def test_op_verdict_equal_and_unknown_native_equals_pure():
    a = op.carry("srmech.amsc.rational.sin_series_truncate",
                 {"numerator": 1, "denominator": 1}, {"num_terms": 8})
    b = op.carry("srmech.amsc.rational.sin_series_truncate",
                 {"numerator": 1, "denominator": 1}, {"num_terms": 8})
    c = op.carry("srmech.amsc.rational.sin_series_truncate",
                 {"numerator": 1, "denominator": 1}, {"num_terms": 9})
    d = op.carry("srmech.amsc.rational.exp_series_truncate",
                 {"numerator": 1, "denominator": 1}, {"num_terms": 8})
    for x, y, want in [(a, b, "EQUAL"), (a, c, "UNKNOWN"), (a, d, "UNKNOWN")]:
        nat, pure = _both(lambda x=x, y=y: op.op_verdict(x, y))
        assert nat == pure == want


# ──────────────────────────────────────────────────────────────────────
# family_verdict — SAME_TARGET / UNKNOWN (unnamed targets always UNKNOWN).
# ──────────────────────────────────────────────────────────────────────

def test_family_verdict_native_equals_pure():
    a = op.carry("srmech.amsc.rational.sin_series_truncate",
                 {"numerator": 1, "denominator": 1}, {"num_terms": 8})
    c = op.carry("srmech.amsc.rational.sin_series_truncate",
                 {"numerator": 1, "denominator": 1}, {"num_terms": 9})
    d = op.carry("srmech.amsc.rational.cos_series_truncate",
                 {"numerator": 1, "denominator": 1}, {"num_terms": 8})
    j = op.carry("srmech.amsc.laplacian.jacobi_eigvals",
                 {"matrix": [[2.0, -1.0], [-1.0, 2.0]]})
    # same target, different rung -> SAME_TARGET; different target -> UNKNOWN;
    # unnamed (float-leaf) family None -> UNKNOWN.
    for x, y, want in [(a, c, "SAME_TARGET"), (a, d, "UNKNOWN"),
                       (j, j, "UNKNOWN")]:
        nat, pure = _both(lambda x=x, y=y: op.family_verdict(x, y))
        assert nat == pure == want


# ──────────────────────────────────────────────────────────────────────
# reproject — the RE-VERIFY: family preserved, value recomputed, and the
# mismatched-inputs guard raises on BOTH paths.
# ──────────────────────────────────────────────────────────────────────

def test_reproject_verbatim_and_override_native_equals_pure():
    a = op.carry("srmech.amsc.rational.sin_series_truncate",
                 {"numerator": 1, "denominator": 1}, {"num_terms": 8})
    nat, pure = _both(lambda: op.reproject(a))
    assert nat["provenance"] == pure["provenance"] == a["provenance"]
    nato, pureo = _both(lambda: op.reproject(a, num_terms=12))
    assert nato["provenance"] == pureo["provenance"]
    assert op.family_verdict(a, nato) == "SAME_TARGET"
    expect = op.carry("srmech.amsc.rational.sin_series_truncate",
                      {"numerator": 1, "denominator": 1}, {"num_terms": 12})
    assert nato["value"] == expect["value"]


def test_reproject_mismatched_inputs_raises_both_paths():
    a = op.carry("srmech.amsc.rational.sin_series_truncate",
                 {"numerator": 1, "denominator": 1}, {"num_terms": 8})
    bare = copy.deepcopy(a["provenance"])
    with pytest.raises(ValueError):
        op.reproject(bare, inputs={"numerator": 2, "denominator": 1})
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = False
        with pytest.raises(ValueError):
            op.reproject(bare, inputs={"numerator": 2, "denominator": 1})
    finally:
        _native.HAS_NATIVE = saved
