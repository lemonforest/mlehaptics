"""Qalg TAIL Batch 2 (0.9.0rc158): the 4 Cayley–Dickson INTEGER-cocycle
NAVIGATION ops earn a C path — ``bignum_reference → c_dispatched``.

FOUR new C kernels give the signed-basis-unit loop navigation a standalone-C
surface, COMPOSED over the existing ``srmech_cd_basis_product`` cocycle:

  * ``srmech_cd_closure``              (sub-loop fixpoint)
  * ``srmech_cd_left_orbit``          (one left-multiplication cycle)
  * ``srmech_cd_min_generating_set``  (min spanning cardinality; composes closure)
  * ``srmech_cd_zero_divisor_witness``(first sedenion basis-pair zero divisor)

They are genuinely INTEGER (signed units ±e_i, bounded ≤ 2·dim ≤ 128; NO bignum,
NO ℚ, NO new carrier) — a bare-C host navigates the whole Moufang loop with no
Python.

This test pins:
  1. the native symbols are actually loaded (parity exercises C, not a silent
     pure fallback on BOTH sides);
  2. each op native == FORCED-PURE is BYTE-IDENTICAL, INCLUDING set / list
     ordering (closure is a set → element-identical; left_orbit is a list → same
     cycle order; min_generating_set is an int; the witness is a dict);
  3. the value oracles (octonion / quaternion sub-loops, the order-4 left orbit,
     the min-generating cardinalities, the known ``(e1+e10)(e4−e15)=0`` witness);
  4. each dispatches when native + falls back to the byte-identical pure oracle;
  5. the 4 Rosetta rows are ``c_dispatched``.

Numpy-free (pure stdlib + srmech).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from srmech.amsc import _native
from srmech.amsc.cascade import cayley_dickson as cd


def _force(has_native: bool, fn, *args, **kw):
    """Run ``fn`` with ``_native.HAS_NATIVE`` pinned, then restore."""
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = has_native
        return fn(*args, **kw)
    finally:
        _native.HAS_NATIVE = saved


# The full navigation surface exercised for parity.
_CLOSURE_CASES = [
    (2, [1]),
    (4, [1, 2, 3]),
    (4, [1, 2]),
    (8, [1]),
    (8, [1, 2]),
    (8, [1, 2, 4]),
    (8, list(range(1, 8))),
    (16, [1, 2]),
    (16, list(range(1, 16))),
]
_MGS_CASES = [
    (2, [1]),
    (4, [1, 2, 3]),
    (8, list(range(1, 8))),
    (16, list(range(1, 16))),
    (8, [1]),          # NO spanning subset → ValueError (0 from C)
]


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_symbols_present():
    # The 4 CD navigation C symbols are actually loaded, so parity exercises C.
    assert _native.has_native_cd_closure()
    # The raw helpers reach the loop with no Python-side navigation loop.
    assert _native.cd_closure_c(8, [1, 2]) is not None
    assert _native.cd_left_orbit_c(8, 1, 1) is not None
    assert _native.cd_min_generating_set_c(8, list(range(1, 8))) == 3
    assert _native.cd_zero_divisor_witness_c() == (1, 10, 4, 15, -1)


# ---- closure --------------------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("dim,gens", _CLOSURE_CASES)
def test_closure_native_equals_pure(dim, gens):
    """closure native == FORCED-PURE, element-identical (a set)."""
    nat = _force(True, cd.closure, dim, gens)
    pure = _force(False, cd.closure, dim, gens)
    assert isinstance(nat, set) and isinstance(pure, set)
    assert nat == pure, (dim, gens)
    # genuinely a sub-loop: closed under products (structural cross-check)
    for a in nat:
        for b in nat:
            assert cd._loop_mult(dim, a, b) in nat


def test_closure_value_oracles():
    assert cd.closure(8, [1]) == {(1, 0), (1, 1), (-1, 0), (-1, 1)}
    assert len(cd.closure(8, [1, 2])) == 8          # quaternion sub-loop
    assert len(cd.closure(8, list(range(1, 8)))) == 16   # full octonion loop
    assert len(cd.closure(16, list(range(1, 16)))) == 32  # full sedenion loop


# ---- left_orbit -----------------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("dim", [2, 4, 8, 16])
def test_left_orbit_native_equals_pure(dim):
    """left_orbit native == FORCED-PURE, BYTE-IDENTICAL cycle order (a list)."""
    for start in range(dim):
        for gen in range(dim):
            nat = _force(True, cd.left_orbit, dim, start, gen)
            pure = _force(False, cd.left_orbit, dim, start, gen)
            assert isinstance(nat, list) and isinstance(pure, list)
            assert nat == pure, (dim, start, gen)


def test_left_orbit_value_oracles():
    # e_1 under repeated left-mult by e_1: e_1·e_1 = -e_0 → order 4.
    assert cd.left_orbit(8, 1, 1) == [(1, 1), (-1, 0), (-1, 1), (1, 0)]
    # left-mult by e_0 (identity) fixes every unit → orbit length 1.
    assert cd.left_orbit(8, 3, 0) == [(1, 3)]


# ---- min_generating_set ---------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("dim,units", _MGS_CASES)
def test_min_generating_set_native_equals_pure(dim, units):
    """min_generating_set native == FORCED-PURE (int OR the same ValueError)."""
    def run(hn):
        try:
            return ("k", _force(hn, cd.min_generating_set, dim, units))
        except ValueError as e:
            return ("err", "full loop" in str(e))
    assert run(True) == run(False), (dim, units)


def test_min_generating_set_value_oracles():
    assert cd.min_generating_set(2, [1]) == 1           # ℂ
    assert cd.min_generating_set(4, [1, 2, 3]) == 2      # ℍ
    assert cd.min_generating_set(8, list(range(1, 8))) == 3   # 𝕆
    assert cd.min_generating_set(16, list(range(1, 16))) == 4  # 𝕊
    with pytest.raises(ValueError, match="full loop"):
        cd.min_generating_set(8, [1])                   # single unit cannot span


# ---- sedenion_zero_divisor_witness ----------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_zero_divisor_witness_native_equals_pure():
    """The witness dict native == FORCED-PURE, byte-identical."""
    nat = _force(True, cd.sedenion_zero_divisor_witness)
    pure = _force(False, cd.sedenion_zero_divisor_witness)
    assert nat == pure


def test_zero_divisor_witness_value_oracle():
    """The KNOWN first sedenion basis-pair zero divisor: (e1+e10)(e4−e15)=0."""
    w = cd.sedenion_zero_divisor_witness()
    assert w["dim"] == 16
    assert w["x_form"] == "e1 + e10"
    assert w["y_form"] == "e4 - e15"
    assert w["x_norm_sq"] == 2 and w["y_norm_sq"] == 2   # both factors nonzero
    assert w["product_is_zero"] is True
    assert all(v == 0 for v in w["product"])             # x·y = 0


# ---- ledger ---------------------------------------------------------------

def test_ledger_rows():
    """All 4 ops → c_dispatched (left bignum_reference)."""
    fixture = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
    rows = {json.loads(l)["defined_at"]: json.loads(l)["bucket"]
            for l in fixture.read_text(encoding="utf-8").splitlines() if l.strip()}
    for op in ("closure", "left_orbit", "min_generating_set",
               "sedenion_zero_divisor_witness"):
        da = f"srmech.amsc.cascade.cayley_dickson.{op}"
        assert rows.get(da) == "c_dispatched", (op, rows.get(da))
