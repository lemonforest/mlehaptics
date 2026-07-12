"""Qalg TAIL Batch 6 (0.9.0rc162): the exact real-AND-complex eigenvalue
ISOLATION (``eigvals_exact``) earns a srmech_bigint-backed C path — the exact
ROOTS of the characteristic polynomial (``char_poly``, rc161).

Two NEW C kernels:
  * ``srmech_sturm_isolate`` — the REAL eigenvalues: char_poly -> Yun square-free
    factorisation -> STURM sign-sequence isolation -> rational bisection, returning
    the exact isolating ``(lo, hi)`` rational intervals with multiplicity;
  * ``srmech_complex_isolate`` (built on ``srmech_poly_root_box_certify``, the exact
    ARGUMENT-PRINCIPLE box certifier) — the COMPLEX eigenvalues: pure rational-box
    subdivision over the upper half-plane, each box certified by the winding number
    in exact Fraction arithmetic, refined to 2^-bits.

Both compose the exact-Q ``srmech_poly_*`` kernels + scalar exact-Q srmech_bigint
arithmetic — byte/structurally-identical to the pure ``_square_free_factors`` +
``_isolate_real_roots`` + ``_isolate_complex_roots_upper``.

This test pins:
  1. the native ``srmech_sturm_isolate`` / ``srmech_complex_isolate`` /
     ``srmech_poly_root_box_certify`` symbols are actually loaded (so parity
     exercises C, not a silent pure fallback on BOTH sides);
  2. ``eigvals_exact`` native == FORCED-PURE is BYTE-IDENTICAL — the exact isolating
     intervals (``return_intervals=True``) AND the include_complex spectrum — across
     diagonal / symmetric / repeated / companion / complex / bignum matrices;
  3. the value oracles — diag(1,2,3) -> {1,2,3}; [[2,1],[1,2]] -> {1,3}; 2·I3 ->
     {2,2,2} (multiplicity 3); a companion matrix -> the roots of its polynomial;
     [[0,-1],[1,0]] -> {±i}; the isolating intervals CONTAIN the true eigenvalues;
  4. ``eigvals_exact`` dispatches when native + falls back to the byte-identical
     pure oracle;
  5. the Rosetta row: ``eigvals_exact`` -> ``c_dispatched``.

Numpy-free (pure stdlib + srmech).
"""
from __future__ import annotations

import json
import random
from fractions import Fraction
from pathlib import Path

import pytest

from srmech.amsc import _native
from srmech.amsc.cascade import matrix_cascades as mc
from srmech.amsc.cascade.matrix_cascades import eigvals_exact


def _force(has_native: bool, fn, *args, **kw):
    """Run ``fn`` with ``_native.HAS_NATIVE`` pinned, then restore."""
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = has_native
        return fn(*args, **kw)
    finally:
        _native.HAS_NATIVE = saved


def _companion(coeffs_low_to_high_monic):
    """Bottom-companion matrix whose char-poly is x^n + Σ c_i x^i."""
    c = coeffs_low_to_high_monic
    n = len(c) - 1
    m = [[0 for _ in range(n)] for _ in range(n)]
    for i in range(1, n):
        m[i][i - 1] = 1
    for i in range(n):
        m[i][n - 1] = -c[i]
    return m


# A spread: diagonal, symmetric, companion, repeated eigenvalues, mixed-sign,
# complex-spectrum, and large-magnitude (bignum) entries.
_MATRICES = [
    [[5]],
    [[2, 1], [1, 2]],                            # {1, 3}
    [[1, 0, 0], [0, 2, 0], [0, 0, 3]],          # {1, 2, 3}
    [[2, 0, 0], [0, 2, 0], [0, 0, 2]],          # {2, 2, 2}  (multiplicity 3)
    [[2, 1, 0], [0, 2, 1], [0, 0, 2]],          # Jordan block -> {2, 2, 2}
    [[5, -2, 7], [3, 11, -4], [-8, 1, 6]],
    _companion([-6, 11, -6, 1]),                # (x-1)(x-2)(x-3)
    [[4, 1, 0], [1, 4, 1], [0, 1, 4]],          # symmetric tridiagonal
    [[10 ** 12, -3, 7], [5, -10 ** 11, -9], [-8, 4, 10 ** 13]],
]

# Matrices with genuinely-complex spectra (for the include_complex path).
_COMPLEX_MATRICES = [
    [[0, -1], [1, 0]],                          # {±i}
    [[0, -4], [1, 0]],                          # {±2i}
    [[1, -1], [1, 1]],                          # {1±i}
    [[2, -3], [3, 2]],                          # {2±3i}
    _companion([1, 0, 0, 1]),                   # x^3 - 1 -> {1, -1/2 ± (√3/2)i}
    [[0, -1, 0], [1, 0, 0], [0, 0, 5]],         # {±i, 5}
]


# ---- native symbols present ------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_symbols_present():
    assert _native.has_native_sturm_isolate()
    assert _native.has_native_complex_isolate()
    assert hasattr(_native.LIB, "srmech_poly_root_box_certify")
    # diag(1,2,3) real eigenvalues via the C kernel.
    assert _force(True, eigvals_exact, [[1, 0, 0], [0, 2, 0], [0, 0, 3]]) == \
        [1.0, 2.0, 3.0]


# ---- native == pure byte-identical (real: exact intervals) -----------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("mat", _MATRICES)
def test_eigvals_real_intervals_native_equals_pure(mat):
    nat = _force(True, eigvals_exact, mat, return_intervals=True)
    pure = _force(False, eigvals_exact, mat, return_intervals=True)
    assert nat == pure                          # byte-identical Fraction intervals
    # The C path actually RAN (returned non-None, not a silent OVERFLOW fallback).
    assert _native.sturm_isolate_c(mc.char_poly(mat), 64) is not None
    # the isolating intervals bracket the eigenvalues (rational sanity, no float).
    for lo, hi in nat:
        assert isinstance(lo, Fraction) and isinstance(hi, Fraction)
        assert lo <= hi


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_eigvals_real_random_byte_identical():
    rng = random.Random(20260707)
    for _ in range(60):
        n = rng.randint(1, 5)
        m = [[rng.randint(-8, 8) for _ in range(n)] for _ in range(n)]
        sym = [[m[i][j] + m[j][i] for j in range(n)] for i in range(n)]
        for a in (m, sym):
            assert _force(True, eigvals_exact, a, return_intervals=True) == \
                _force(False, eigvals_exact, a, return_intervals=True)


# ---- native == pure byte-identical (complex: full spectrum) ----------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("mat", _COMPLEX_MATRICES)
def test_eigvals_complex_native_equals_pure(mat):
    nat = _force(True, eigvals_exact, mat, include_complex=True)
    pure = _force(False, eigvals_exact, mat, include_complex=True)
    assert len(nat) == len(pure)
    for x, y in zip(nat, pure):
        assert type(x) is type(y)
        if isinstance(x, complex):
            assert x.real == y.real and x.imag == y.imag   # bit-identical floats
        else:
            assert x == y
    # the C complex path actually RAN.
    assert _native.complex_isolate_c(mc.char_poly(mat), 64) is not None


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_eigvals_complex_random_byte_identical():
    rng = random.Random(31337)
    checked = 0
    for _ in range(24):
        n = rng.randint(2, 4)
        m = [[rng.randint(-5, 5) for _ in range(n)] for _ in range(n)]
        nat = _force(True, eigvals_exact, m, include_complex=True, bits=48)
        pure = _force(False, eigvals_exact, m, include_complex=True, bits=48)
        assert len(nat) == len(pure)
        for x, y in zip(nat, pure):
            assert type(x) is type(y)
            if isinstance(x, complex):
                assert x.real == y.real and x.imag == y.imag
            else:
                assert x == y
        if any(isinstance(x, complex) for x in nat):
            checked += 1
    assert checked >= 3, "expected some random matrices to have complex spectra"


# ---- value oracles ---------------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_value_oracles():
    assert eigvals_exact([[1, 0, 0], [0, 2, 0], [0, 0, 3]]) == [1.0, 2.0, 3.0]
    assert eigvals_exact([[2, 1], [1, 2]]) == [1.0, 3.0]
    # repeated eigenvalue with correct multiplicity (3 copies of 2).
    assert eigvals_exact([[2, 0, 0], [0, 2, 0], [0, 0, 2]]) == [2.0, 2.0, 2.0]
    assert eigvals_exact([[2, 1, 0], [0, 2, 1], [0, 0, 2]]) == [2.0, 2.0, 2.0]
    # companion of (x-1)(x-2)(x-4) -> {1, 2, 4}.
    comp = _companion([-8, 14, -7, 1])
    assert eigvals_exact(comp) == [1.0, 2.0, 4.0]
    # complex conjugate pair ±i.
    ev = eigvals_exact([[0, -1], [1, 0]], include_complex=True)
    assert len(ev) == 2
    assert all(isinstance(z, complex) for z in ev)
    assert abs(ev[0].imag + 1.0) < 1e-12 and abs(ev[1].imag - 1.0) < 1e-12


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_intervals_contain_eigenvalues():
    # diag(3, -5, 7): the exact isolating intervals must each bracket one eigenvalue.
    ivs = eigvals_exact([[3, 0, 0], [0, -5, 0], [0, 0, 7]], return_intervals=True)
    roots = sorted([Fraction(-5), Fraction(3), Fraction(7)], key=lambda r: r)
    got = sorted(ivs, key=lambda iv: iv[0] + iv[1])
    for (lo, hi), r in zip(got, roots):
        assert lo <= r <= hi                    # exact rational bracketing


# ---- dispatch + fallback ---------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_dispatch_and_fallback_agree():
    a = [[5, -2, 7], [3, 11, -4], [-8, 1, 6]]
    assert _force(True, eigvals_exact, a) == _force(False, eigvals_exact, a)


# ---- Rosetta row -----------------------------------------------------------

def test_rosetta_eigvals_is_c_dispatched():
    fixture = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
    rows = {json.loads(l)["defined_at"]: json.loads(l)["bucket"]
            for l in fixture.read_text(encoding="utf-8").splitlines() if l.strip()}
    assert rows["srmech.amsc.cascade.matrix_cascades.eigvals_exact"] == "c_dispatched"
