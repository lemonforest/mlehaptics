"""Qalg TAIL Batch 4 (0.9.0rc160): the Cayley–Dickson MULTIPLICATION core earns
a C path — 5 rows leave ``bignum_reference``.

The NEW C kernel ``srmech_cd_mult`` computes the arbitrary-rational CD product
``x·y`` as the bilinear form ``(x·y)_{i⊕j} = Σ x_i·y_j·sign(i,j)``, composing the
integer cocycle ``srmech_cd_basis_product`` with the SAME qmat exact-ℚ arithmetic
the rc159 Qvec kernels use (no duplicated ℚ algebra). Its two dependents ride the
same C — ``left_mult_matrix`` (each column ``x·e_c`` is a ``cd_mult``) and
``left_mult_kernel`` (``srmech_qmat_nullspace`` over ``left_mult_matrix``) — and
the two hypercomplex-exp Taylor oracles ``octonion``/``quaternion``.
``exp_series_truncate`` (which just pack the already-``c_dispatched``
``rational.{cos,sin}_series_truncate`` into the Euler-formula tuple) reclassify to
``composition_of_c``.

This test pins:
  1. the native ``srmech_cd_mult`` symbol is actually loaded (parity exercises C,
     not a silent pure fallback on BOTH sides);
  2. each op native == FORCED-PURE is BYTE-IDENTICAL exact-ℚ (the SAME reduced
     canonical (num, den) as Python's Fraction) across many CD ℚ-vectors;
  3. the value oracles — quaternion units ``i·j = k``; the octonion
     NON-ASSOCIATIVITY witness ``(e1·e2)·e4 ≠ e1·(e2·e4)``;
     ``left_mult_matrix(unit)`` is a signed permutation; a sedenion zero divisor's
     ``left_mult_kernel`` is NON-empty while an invertible element's is empty; the
     hypercomplex exp of a pure-imaginary axis matches the exact Taylor;
  4. each dispatches when native + falls back to the byte-identical pure oracle;
  5. the Rosetta rows: ``cd_mult`` → ``c_dispatched``; ``left_mult_matrix`` /
     ``left_mult_kernel`` / the two exp ops → ``composition_of_c``.

Numpy-free (pure stdlib + srmech).
"""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import pytest

from srmech.amsc import _native
from srmech.amsc.cascade import cayley_dickson as cd
from srmech.amsc import rational as _rational
from srmech.qm import octonion as octo
from srmech.qm import quaternion as quat


def _force(has_native: bool, fn, *args, **kw):
    """Run ``fn`` with ``_native.HAS_NATIVE`` pinned, then restore."""
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = has_native
        return fn(*args, **kw)
    finally:
        _native.HAS_NATIVE = saved


def _canon_eq(a, b) -> bool:
    """BYTE-IDENTICAL exact-ℚ vector: same length + each component's reduced
    (numerator, denominator) matches exactly (Fraction is always canonical)."""
    a = tuple(a)
    b = tuple(b)
    if len(a) != len(b):
        return False
    return all(x.numerator == y.numerator and x.denominator == y.denominator
               for x, y in zip(a, b))


def _mat_eq(a, b) -> bool:
    """BYTE-IDENTICAL exact-ℚ matrix (list of rows)."""
    if len(a) != len(b):
        return False
    return all(_canon_eq(ra, rb) for ra, rb in zip(a, b))


def _basis_eq(a, b) -> bool:
    """BYTE-IDENTICAL kernel basis: same number of vectors, each byte-identical."""
    if len(a) != len(b):
        return False
    return all(_canon_eq(va, vb) for va, vb in zip(a, b))


F = Fraction

# A spread of power-of-two-dim CD ℚ-vectors: integers, mixed-sign rationals,
# zeros, and larger magnitudes (to exercise the bignum path + gcd-reduce).
_VECTORS = [
    [F(1)],
    [F(-3)],
    [F(1, 2), F(1, 3)],
    [F(-5, 4), F(7, 8)],
    [F(0), F(0)],
    [F(1), F(2), F(3), F(4)],
    [F(1, 2), F(-2, 3), F(3, 4), F(-4, 5)],
    [F(0), F(1), F(-1), F(0)],
    [F(1), F(2), F(3), F(4), F(5), F(6), F(7), F(8)],
    [F(10 ** 18, 3), F(-7, 10 ** 12), F(0), F(123456789, 987654321),
     F(5), F(-11, 13), F(2, 7), F(-1)],
    [F((-1) ** i * (i + 1), 2 * i + 3) for i in range(16)],
]


# ---- native symbol present ------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_symbol_present():
    # The rc160 srmech_cd_mult symbol is actually loaded (so parity exercises C).
    assert _native.has_native_cd_mult()
    # i·j = k over the dim-4 quaternions: e1·e2 = e3.
    prod = _native.cd_mult_c([(0, 1), (1, 1), (0, 1), (0, 1)],
                             [(0, 1), (0, 1), (1, 1), (0, 1)])
    assert prod == [(0, 1), (0, 1), (0, 1), (1, 1)]


# ---- cd_mult --------------------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("vec", _VECTORS)
def test_cd_mult_native_equals_pure(vec):
    other = [F(3, 7) - v for v in vec]            # a second same-dim vector
    nat = _force(True, cd.cd_mult, vec, other)
    pure = _force(False, cd.cd_mult, vec, other)
    assert _canon_eq(nat, pure), vec
    # and the reverse order (non-commutative in general; both paths agree)
    assert _canon_eq(_force(True, cd.cd_mult, other, vec),
                     _force(False, cd.cd_mult, other, vec)), vec


def test_cd_mult_quaternion_units_ijk():
    # i·j = k, j·k = i, k·i = j (the oriented quaternion triple {1,2,3}).
    e = [cd.cd_basis(4, n) for n in range(4)]
    assert cd.cd_mult(e[1], e[2]) == (F(0), F(0), F(0), F(1))   # i·j = k
    assert cd.cd_mult(e[2], e[3]) == (F(0), F(1), F(0), F(0))   # j·k = i
    assert cd.cd_mult(e[3], e[1]) == (F(0), F(0), F(1), F(0))   # k·i = j
    # i² = j² = k² = −1 (= −e0)
    assert cd.cd_mult(e[1], e[1]) == (F(-1), F(0), F(0), F(0))
    # anticommutativity: j·i = −k
    assert cd.cd_mult(e[2], e[1]) == (F(0), F(0), F(0), F(-1))


def test_cd_mult_octonion_non_associativity():
    # 𝕆 is NON-associative: (e1·e2)·e4 ≠ e1·(e2·e4) — they differ by SIGN.
    e = [cd.cd_basis(8, n) for n in range(8)]
    left = cd.cd_mult(cd.cd_mult(e[1], e[2]), e[4])
    right = cd.cd_mult(e[1], cd.cd_mult(e[2], e[4]))
    assert left != right                         # the associator is nonzero
    # both live entirely on the e7 axis, with OPPOSITE signs (Class-K, no abs)
    assert all(left[k] == 0 for k in range(8) if k != 7)
    assert all(right[k] == 0 for k in range(8) if k != 7)
    assert left[7] == -right[7] and left[7] != 0


def test_cd_mult_norm_multiplicative_through_octonions():
    # Composition N(x·y) = N(x)·N(y) holds for dims ≤ 8 (Hurwitz). A concrete
    # octonion check with mixed-sign rationals.
    x = [F(1, 2), F(-1, 3), F(2), F(0), F(-5, 7), F(1), F(0), F(3, 4)]
    y = [F(-2), F(1, 5), F(0), F(4, 3), F(1), F(-1, 6), F(7, 8), F(0)]
    p = cd.cd_mult(x, y)
    assert cd.cd_norm_sq(p) == cd.cd_norm_sq(x) * cd.cd_norm_sq(y)


# ---- left_mult_matrix -----------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("vec", _VECTORS)
def test_left_mult_matrix_native_equals_pure(vec):
    nat = _force(True, cd.left_mult_matrix, vec)
    pure = _force(False, cd.left_mult_matrix, vec)
    assert _mat_eq(nat, pure), vec


def test_left_mult_matrix_unit_is_signed_permutation():
    # L(e_i) for a unit e_i: column j is e_i·e_j = ±e_{i⊕j}, so every row and
    # every column has exactly ONE nonzero entry, and it is ±1.
    for i in range(1, 8):
        m = cd.left_mult_matrix(cd.cd_basis(8, i))
        n = len(m)
        for r in range(n):
            row_nz = [m[r][c] for c in range(n) if m[r][c] != 0]
            col_nz = [m[c][r] for c in range(n) if m[c][r] != 0]
            assert len(row_nz) == 1 and row_nz[0] in (F(1), F(-1)), (i, r)
            assert len(col_nz) == 1, (i, r)


# ---- left_mult_kernel -----------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_left_mult_kernel_native_equals_pure():
    # a division-algebra element (empty kernel) + a sedenion zero divisor
    # (non-empty kernel): both byte-identical native == pure.
    w = cd.sedenion_zero_divisor_witness()
    cases = [
        [F(1), F(2), F(3), F(4), F(5), F(6), F(7), F(8)],   # invertible octonion
        list(w["x"]),                                        # zero divisor (dim 16)
        [cd.cd_basis(8, 1)[k] for k in range(8)],            # a unit
    ]
    for x in cases:
        nat = _force(True, cd.left_mult_kernel, x)
        pure = _force(False, cd.left_mult_kernel, x)
        assert _basis_eq(nat, pure), x


def test_left_mult_kernel_zero_divisor_nonempty_invertible_empty():
    # The §VII.6.23.4 falsifier: a sedenion zero divisor has NO backward
    # direction (non-empty left-mult kernel); a division-algebra element does.
    w = cd.sedenion_zero_divisor_witness()
    ker = cd.left_mult_kernel(list(w["x"]))
    assert len(ker) >= 1                          # left zero divisor
    # y (the witness partner) is annihilated: x·y = 0, so y ∈ ker(L(x)).
    assert cd.cd_mult(w["x"], w["y"]) == tuple(F(0) for _ in range(16))
    # a nonzero octonion is invertible: empty kernel.
    assert cd.left_mult_kernel(
        [F(1), F(-2), F(3), F(0), F(5), F(0), F(-7), F(8)]) == []
    # a nonzero real / complex / quaternion unit: empty kernel.
    assert cd.left_mult_kernel(cd.cd_basis(4, 2)) == []


# ---- hypercomplex exp (octonion / quaternion) -----------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("axis", [1, 2, 3])
def test_quaternion_exp_series_native_equals_pure(axis):
    for (p, q, nt) in [(0, 1, 5), (1, 2, 12), (-3, 5, 16), (22, 7, 20)]:
        nat = _force(True, quat.quaternion_exp_series_truncate, p, q, nt, axis)
        pure = _force(False, quat.quaternion_exp_series_truncate, p, q, nt, axis)
        assert nat == pure, (axis, p, q, nt)


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("axis", [1, 3, 5, 7])
def test_octonion_exp_series_native_equals_pure(axis):
    for (p, q, nt) in [(0, 1, 5), (1, 2, 12), (-3, 5, 16), (22, 7, 20)]:
        nat = _force(True, octo.octonion_exp_series_truncate, p, q, nt, axis)
        pure = _force(False, octo.octonion_exp_series_truncate, p, q, nt, axis)
        assert nat == pure, (axis, p, q, nt)


def test_hypercomplex_exp_matches_exact_taylor():
    # exp(e_axis·θ) = cos θ·1 + sin θ·e_axis: slot 0 = the exact cos Taylor,
    # slot `axis` = the exact sin Taylor (the Euler formula on a unit axis).
    p, q, nt = 1, 2, 14
    c_pair = tuple(_rational.cos_series_truncate(p, q, nt))
    s_pair = tuple(_rational.sin_series_truncate(p, q, nt))
    quat_out = quat.quaternion_exp_series_truncate(p, q, nt, axis=2)
    assert quat_out[0] == c_pair and quat_out[2] == s_pair
    assert quat_out[1] == (0, 1) and quat_out[3] == (0, 1)
    octo_out = octo.octonion_exp_series_truncate(p, q, nt, axis=5)
    assert octo_out[0] == c_pair and octo_out[5] == s_pair
    # exp(e_axis·0) = 1 exactly (cos 0 = 1, sin 0 = 0), even truncated.
    z = quat.quaternion_exp_series_truncate(0, 1, 6, axis=3)
    assert z == ((1, 1), (0, 1), (0, 1), (0, 1))


# ---- dispatch + fallback --------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_dispatch_and_fallback_agree_everywhere():
    for vec in _VECTORS:
        other = [F(1, 3) + v for v in vec]
        assert _canon_eq(_force(True, cd.cd_mult, vec, other),
                         _force(False, cd.cd_mult, vec, other))
        assert _mat_eq(_force(True, cd.left_mult_matrix, vec),
                       _force(False, cd.left_mult_matrix, vec))
        assert _basis_eq(_force(True, cd.left_mult_kernel, vec),
                         _force(False, cd.left_mult_kernel, vec))


# ---- invalid input parity (both reject non-power-of-two / mismatch) -------

def test_invalid_input_rejected_both_paths():
    for bad in ([1, 2, 3], [F(1, 2)] * 5):
        with pytest.raises(ValueError):
            _force(True, cd.cd_mult, bad, bad)
        with pytest.raises(ValueError):
            _force(False, cd.cd_mult, bad, bad)
    # dimension mismatch
    with pytest.raises(ValueError):
        cd.cd_mult([1, 2], [1, 2, 3, 4])


# ---- ledger ---------------------------------------------------------------

def test_ledger_rows():
    """cd_mult → c_dispatched; left_mult_matrix / left_mult_kernel + the two
    hypercomplex-exp ops → composition_of_c (all left bignum_reference)."""
    fixture = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
    rows = {json.loads(l)["defined_at"]: json.loads(l)["bucket"]
            for l in fixture.read_text(encoding="utf-8").splitlines() if l.strip()}
    assert rows.get("srmech.amsc.cascade.cayley_dickson.cd_mult") == "c_dispatched"
    for da in (
        "srmech.amsc.cascade.cayley_dickson.left_mult_matrix",
        "srmech.amsc.cascade.cayley_dickson.left_mult_kernel",
        "srmech.qm.octonion.octonion_exp_series_truncate",
        "srmech.qm.quaternion.quaternion_exp_series_truncate",
    ):
        assert rows.get(da) == "composition_of_c", (da, rows.get(da))
