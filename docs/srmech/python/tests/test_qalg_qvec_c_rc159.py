"""Qalg TAIL Batch 3 (0.9.0rc159): the 4 TRIVIAL Cayley–Dickson EXACT-ℚ
arithmetic ops earn a C path — ``bignum_reference → c_dispatched``.

A Cayley–Dickson element of dim ``2^k`` is a ℚ-vector of ``dim`` components,
each an exact rational num/den ``srmech_bigint`` pair. FOUR new C kernels — the
new ``srmech_cd_qvec`` exact-ℚ VECTOR carrier (the 1-D sibling of
``srmech_qmat``, reusing its exact-ℚ scalar machinery in-TU) — give a bare-C
host the CD ℚ-vector surface:

  * ``srmech_cd_qbasis``    (the unit vector e_i; Class-A basis convention)
  * ``srmech_cd_qconjugate``(negate the imaginary half; Class-K sign-flip)
  * ``srmech_cd_qadd``      (component-wise exact-ℚ sum)
  * ``srmech_cd_qnorm_sq``  (Σ x_i² as one exact-ℚ scalar; Class-N anchor)

This test pins:
  1. the native symbols are actually loaded (parity exercises C, not a silent
     pure fallback on BOTH sides);
  2. each op native == FORCED-PURE is BYTE-IDENTICAL exact-ℚ (the SAME reduced
     canonical (num, den) as Python's Fraction — gcd-reduced, sign on
     numerator, positive denominator) across many power-of-two vectors of
     mixed-sign rationals;
  3. the value oracles (cd_basis(4,2); cd_conjugate([1,2,3,4]);
     cd_add([1/2,1/3],[1/6,1/3]); cd_norm_sq([1,2,2,0])=9; cd_norm_sq([1/2,1/2])
     =1/2; and the non-trivial reduced 181/144);
  4. each dispatches when native + falls back to the byte-identical pure oracle;
  5. the 4 Rosetta rows are ``c_dispatched``.

Numpy-free (pure stdlib + srmech).
"""
from __future__ import annotations

import json
from fractions import Fraction
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


def _canon_eq(a, b) -> bool:
    """BYTE-IDENTICAL exact-ℚ: same length + each component's reduced
    (numerator, denominator) matches exactly (Fraction is always canonical, so
    this is the reduced-form-identity check)."""
    a = tuple(a)
    b = tuple(b)
    if len(a) != len(b):
        return False
    return all(x.numerator == y.numerator and x.denominator == y.denominator
               for x, y in zip(a, b))


F = Fraction

# A spread of power-of-two-dim CD ℚ-vectors: integers, mixed-sign rationals,
# zeros, and larger magnitudes (to exercise the bignum path + gcd-reduce).
_VECTORS = [
    [F(1)],
    [F(-3)],
    [F(1, 2), F(1, 3)],
    [F(1, 6), F(1, 3)],
    [F(-5, 4), F(7, 8)],
    [F(0), F(0)],
    [F(1), F(2), F(3), F(4)],
    [F(1, 2), F(-2, 3), F(3, 4), F(-4, 5)],
    [F(0), F(1), F(-1), F(0)],
    [F(10 ** 20, 3), F(-7, 10 ** 15), F(0), F(123456789, 987654321)],
    [F(i - 4, i + 5) for i in range(8)],
    [F((-1) ** i * (i + 1), 2 * i + 3) for i in range(16)],
]


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_symbols_present():
    # The rc159 CD exact-ℚ vector C symbols are actually loaded, so parity
    # exercises C (not a silent pure fallback on both sides).
    assert _native.has_native_cd_qvec()
    assert _native.cd_qbasis_c(4, 2) == [(0, 1), (0, 1), (1, 1), (0, 1)]
    assert _native.cd_qadd_c([(1, 2), (1, 3)], [(1, 6), (1, 3)]) == [(2, 3), (2, 3)]
    assert _native.cd_qnorm_sq_c([(1, 1), (2, 1), (2, 1), (0, 1)]) == (9, 1)


# ---- cd_basis -------------------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("dim", [1, 2, 4, 8, 16])
def test_cd_basis_native_equals_pure(dim):
    for i in range(dim):
        nat = _force(True, cd.cd_basis, dim, i)
        pure = _force(False, cd.cd_basis, dim, i)
        assert _canon_eq(nat, pure), (dim, i)


def test_cd_basis_value_oracle():
    assert cd.cd_basis(4, 2) == (F(0), F(0), F(1), F(0))
    assert cd.cd_basis(1, 0) == (F(1),)
    assert cd.cd_basis(8, 7) == tuple(F(1) if k == 7 else F(0) for k in range(8))


# ---- cd_conjugate ---------------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("vec", _VECTORS)
def test_cd_conjugate_native_equals_pure(vec):
    nat = _force(True, cd.cd_conjugate, vec)
    pure = _force(False, cd.cd_conjugate, vec)
    assert _canon_eq(nat, pure), vec


def test_cd_conjugate_value_oracle():
    # component 0 kept; the imaginary half (1..dim-1) negated (Class-K).
    assert cd.cd_conjugate([1, 2, 3, 4]) == (F(1), F(-2), F(-3), F(-4))
    assert cd.cd_conjugate([F(-1, 2), F(3, 4)]) == (F(-1, 2), F(-3, 4))
    assert cd.cd_conjugate([5]) == (F(5),)      # real: nothing to flip


# ---- cd_add ---------------------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("vec", _VECTORS)
def test_cd_add_native_equals_pure(vec):
    other = [F(3, 7) - v for v in vec]           # a second same-dim vector
    nat = _force(True, cd.cd_add, vec, other)
    pure = _force(False, cd.cd_add, vec, other)
    assert _canon_eq(nat, pure), vec


def test_cd_add_value_oracle():
    assert cd.cd_add([F(1, 2), F(1, 3)], [F(1, 6), F(1, 3)]) == (F(2, 3), F(2, 3))
    assert cd.cd_add([1, 2, 3, 4], [4, 3, 2, 1]) == (F(5), F(5), F(5), F(5))
    # exact-ℚ with reduction: 1/2 + 1/2 = 1/1 (den collapses to 1).
    assert cd.cd_add([F(1, 2), F(1, 4)], [F(1, 2), F(3, 4)]) == (F(1), F(1))


# ---- cd_norm_sq -----------------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("vec", _VECTORS)
def test_cd_norm_sq_native_equals_pure(vec):
    nat = _force(True, cd.cd_norm_sq, vec)
    pure = _force(False, cd.cd_norm_sq, vec)
    assert isinstance(nat, Fraction) and isinstance(pure, Fraction)
    assert nat.numerator == pure.numerator and nat.denominator == pure.denominator, vec


def test_cd_norm_sq_value_oracle():
    assert cd.cd_norm_sq([1, 2, 2, 0]) == F(9)          # 1+4+4+0
    assert cd.cd_norm_sq([F(1, 2), F(1, 2)]) == F(1, 2)  # 1/4+1/4
    assert cd.cd_norm_sq([F(3, 4), F(5, 6)]) == F(181, 144)  # non-trivial reduce
    assert cd.cd_norm_sq([5]) == F(25)


# ---- dispatch + fallback --------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_dispatch_and_fallback_agree_everywhere():
    """Every op: native path and forced-pure path are byte-identical (so the
    fallback is a genuine complete alternative, not an approximation)."""
    for vec in _VECTORS:
        assert _canon_eq(_force(True, cd.cd_conjugate, vec),
                         _force(False, cd.cd_conjugate, vec))
        other = [F(1, 3) + v for v in vec]
        assert _canon_eq(_force(True, cd.cd_add, vec, other),
                         _force(False, cd.cd_add, vec, other))
        assert _force(True, cd.cd_norm_sq, vec) == _force(False, cd.cd_norm_sq, vec)


# ---- invalid input parity (both reject non-power-of-two identically) ------

def test_non_power_of_two_rejected_both_paths():
    for bad in ([1, 2, 3], [F(1, 2)] * 5, [0] * 6):
        with pytest.raises(ValueError):
            _force(True, cd.cd_norm_sq, bad)
        with pytest.raises(ValueError):
            _force(False, cd.cd_norm_sq, bad)


# ---- ledger ---------------------------------------------------------------

def test_ledger_rows():
    """All 4 ops → c_dispatched (left bignum_reference)."""
    fixture = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
    rows = {json.loads(l)["defined_at"]: json.loads(l)["bucket"]
            for l in fixture.read_text(encoding="utf-8").splitlines() if l.strip()}
    for op in ("cd_basis", "cd_conjugate", "cd_add", "cd_norm_sq"):
        da = f"srmech.amsc.cascade.cayley_dickson.{op}"
        assert rows.get(da) == "c_dispatched", (op, rows.get(da))
