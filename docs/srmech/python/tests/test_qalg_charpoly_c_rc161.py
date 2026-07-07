"""Qalg TAIL Batch 5 (0.9.0rc161): the exact-INTEGER characteristic polynomial
(``char_poly``, Faddeev–LeVerrier) earns a srmech_bigint-backed C path — the
FOUNDATION of the exact-LA tail (``eigvals_exact`` / ``eig_exact`` / the Jordan
ops all reduce to the roots of this polynomial), so it ships first.

The NEW C kernel ``srmech_faddeev_leverrier`` runs the exact-integer FL recursion
over srmech_bigint::

    M_1 = I ; for k in 1..n:  AM = A·M ;  c_k = -tr(AM)/k  (EXACT: k | tr) ;
    M <- AM + c_k·I

composing srmech_bigint mul/add (the A·M matmul + trace accumulate) with the exact
srmech_bigint divmod (the /k step). Integer matrix -> integer coefficients, so
there is NO ℚ carrier here — it is byte-identical to the pure ``_char_poly_int``.

This test pins:
  1. the native ``srmech_faddeev_leverrier`` symbol is actually loaded (so parity
     exercises C, not a silent pure fallback on BOTH sides);
  2. ``char_poly`` native == FORCED-PURE is BYTE-IDENTICAL (the SAME integer
     coefficient list) across many integer matrices — diagonal, companion,
     repeated-eigenvalue, mixed-sign, and large-magnitude (bignum) entries;
  3. the value oracles — ``diag(1,2,3) -> [1,-6,11,-6]``; a companion matrix ->
     its defining polynomial; ``I_n -> (x-1)^n``; and the Cayley–Hamilton identity
     ``p(A) == 0`` (A satisfies its own characteristic polynomial);
  4. ``char_poly`` dispatches when native + falls back to the byte-identical pure
     oracle;
  5. the Rosetta row: ``char_poly`` -> ``c_dispatched``.

Numpy-free (pure stdlib + srmech).
"""
from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from srmech.amsc import _native
from srmech.amsc.cascade import matrix_cascades as mc
from srmech.amsc.cascade.matrix_cascades import char_poly


def _force(has_native: bool, fn, *args, **kw):
    """Run ``fn`` with ``_native.HAS_NATIVE`` pinned, then restore."""
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = has_native
        return fn(*args, **kw)
    finally:
        _native.HAS_NATIVE = saved


# ---- integer-matrix helpers (numpy-free Cayley–Hamilton check) -------------

def _matmul(a, b):
    n = len(a)
    return [[sum(a[i][t] * b[t][j] for t in range(n)) for j in range(n)]
            for i in range(n)]


def _ident(n):
    return [[1 if i == j else 0 for j in range(n)] for i in range(n)]


def _scale_add(acc, scalar, mat):
    n = len(acc)
    return [[acc[i][j] + scalar * mat[i][j] for j in range(n)] for i in range(n)]


def _eval_poly_at_matrix(coeffs, a):
    """p(A) = Σ_k coeffs[k]·A^(n-k), coeffs HIGH→LOW. Horner over integer
    matrices: R starts coeffs[0]·I, then R <- R·A + coeffs[k]·I."""
    n = len(a)
    r = [[coeffs[0] if i == j else 0 for j in range(n)] for i in range(n)]
    for k in range(1, len(coeffs)):
        r = _scale_add(_matmul(r, a), coeffs[k], _ident(n))
    return r


def _is_zero_matrix(m):
    return all(v == 0 for row in m for v in row)


def _companion(coeffs_low_to_high_monic):
    """Companion matrix whose char-poly is x^n + Σ c_i x^i. Bottom-companion form:
    subdiagonal ones, last column = -c_i."""
    c = coeffs_low_to_high_monic
    n = len(c) - 1
    m = [[0 for _ in range(n)] for _ in range(n)]
    for i in range(1, n):
        m[i][i - 1] = 1
    for i in range(n):
        m[i][n - 1] = -c[i]
    return m


# A spread of integer matrices: diagonal, companion, repeated eigenvalues,
# mixed-sign, and large-magnitude (bignum) entries.
_MATRICES = [
    [[5]],
    [[2, 1], [1, 2]],
    [[0, -1], [1, 0]],
    [[1, 0, 0], [0, 2, 0], [0, 0, 3]],
    [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
    [[2, 1, 0], [0, 2, 1], [0, 0, 2]],          # repeated eigenvalue (Jordan block)
    [[5, -2, 7], [3, 11, -4], [-8, 1, 6]],
    [[0, 0, 0, -6], [1, 0, 0, 11], [0, 1, 0, -6], [0, 0, 1, 0]],
    [[10 ** 15, -3, 7, 2], [5, 10 ** 14, -9, 1],
     [-8, 4, 10 ** 16, 6], [2, -1, 3, -10 ** 13]],
]


# ---- native symbol present -------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_symbol_present():
    # The rc161 srmech_faddeev_leverrier symbol is actually loaded.
    assert _native.has_native_char_poly()
    # diag(1,2,3) -> (x-1)(x-2)(x-3) = x³-6x²+11x-6 via the C kernel.
    assert _native.char_poly_int_c([[1, 0, 0], [0, 2, 0], [0, 0, 3]]) == \
        [1, -6, 11, -6]


# ---- native == pure byte-identical -----------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("mat", _MATRICES)
def test_char_poly_native_equals_pure(mat):
    nat = _force(True, char_poly, mat)
    pure = _force(False, char_poly, mat)
    assert nat == pure                       # byte-identical integer coefficients
    # The C path actually RAN (returned non-None, not a silent OVERFLOW fallback).
    assert _native.char_poly_int_c(mat) == pure


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_char_poly_random_byte_identical():
    rng = random.Random(20260707)
    for _ in range(120):
        n = rng.randint(1, 5)
        mat = [[rng.randint(-30, 30) for _ in range(n)] for _ in range(n)]
        assert _force(True, char_poly, mat) == _force(False, char_poly, mat)


# ---- value oracles ---------------------------------------------------------

def test_oracle_diagonal():
    # char_poly of diag(1,2,3) is (x-1)(x-2)(x-3) = [1,-6,11,-6].
    assert char_poly([[1, 0, 0], [0, 2, 0], [0, 0, 3]]) == [1, -6, 11, -6]
    # diag(2,-3,5,-7): Π(x-λ) elementary symmetric functions.
    assert char_poly([[2, 0, 0, 0], [0, -3, 0, 0], [0, 0, 5, 0], [0, 0, 0, -7]]) \
        == [1, 3, -39, -47, 210]


def test_oracle_identity_is_x_minus_one_power():
    # char_poly(I_n) = (x-1)^n → binomial coefficients with alternating sign.
    from math import comb
    for n in range(1, 7):
        expect = [((-1) ** k) * comb(n, k) for k in range(n + 1)]
        assert char_poly(_ident(n)) == expect


def test_oracle_companion_recovers_defining_poly():
    # A companion matrix's char-poly IS its defining polynomial (high→low).
    # defining poly x⁴ + 6x² - 11x + 6  (c = [6,-11,6,0,1] low→high).
    low_to_high = [6, -11, 6, 0, 1]
    comp = _companion(low_to_high)
    high_to_low = list(reversed(low_to_high))
    assert char_poly(comp) == high_to_low
    # A second companion: x³ - 2x² + 0x + 5  (c = [5,0,-2,1]).
    low2 = [5, 0, -2, 1]
    assert char_poly(_companion(low2)) == list(reversed(low2))


def test_oracle_cayley_hamilton():
    # Every matrix satisfies its own characteristic polynomial: p(A) = 0.
    for mat in _MATRICES:
        cp = char_poly(mat)
        assert _is_zero_matrix(_eval_poly_at_matrix(cp, mat)), mat


# ---- dispatch + fallback ---------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_dispatch_and_fallback_agree():
    for mat in _MATRICES:
        nat = _force(True, char_poly, mat)
        pure = _force(False, char_poly, mat)
        assert nat == pure
    # The forced-pure path never touches C (proves the fallback is self-contained).
    assert _force(False, _native.has_native_char_poly) is False


def test_char_poly_int_c_none_without_native():
    # With HAS_NATIVE pinned False, the C helper returns None (caller falls back).
    assert _force(False, _native.char_poly_int_c, [[1, 2], [3, 4]]) is None


# ---- Rosetta classification ------------------------------------------------

def test_rosetta_char_poly_is_c_dispatched():
    fixture = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
    rows = {}
    with fixture.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            rows[r["defined_at"]] = r["bucket"]
    assert rows["srmech.amsc.cascade.matrix_cascades.char_poly"] == "c_dispatched"


def test_char_poly_float_path_untouched():
    # A non-integer matrix still uses the float FL fallback (no C integer path).
    cp = mc.char_poly([[1.5, 0.0], [0.0, 2.5]])
    assert cp[0] == 1
    # (x-1.5)(x-2.5) = x² - 4x + 3.75
    assert abs(cp[1] - (-4.0)) < 1e-9 and abs(cp[2] - 3.75) < 1e-9
