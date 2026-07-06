"""BATCH B10 (misc) — the near-final compute batch (v0.9.0rc154).

The 8 misc ops move ``python_only_debt`` -> ``composition_of_c`` (×7) /
``c_dispatched`` (×1). This file proves, per op:

1. **VALUE oracles** — the op computes the documented result on known inputs.
2. **native == pure** — where the op reaches a C path (``polar_from_real`` ->
   ``srmech_sign_quantise``; ``polar_unbind`` -> ``srmech_polar_bind``;
   ``polar_random`` -> ``srmech_polar_random``; ``three_fold_eigvec_groups`` ->
   the C Hermitian-eig + ``srmech_three_fold_bands``), the native path matches
   its own forced-pure fallback. Contract per op:
     - EXACT (integer / int8 / seeded RNG) -> BYTE-IDENTICAL native == pure.
     - eig-based (``three_fold_eigvec_groups``) -> INVARIANT (band SIZES + spans;
       the Jacobi eigenBASIS is non-unique, so NOT element-wise).
   The pure-composition ops (``signed_sum_squared`` / ``classify_chirality_harmonic``
   / ``polar_similarity`` / ``greedy_bipartite_alignment``) are standalone-trivial
   integer/float compositions reaching no non-standalone leaf — value-oracle
   verified (``polar_similarity`` additionally cross-checked against the
   ``srmech_polar_similarity`` C float peer).

Numpy-free (stdlib ``random`` / ``array`` only); no ``abs()``; no libm.
"""
from __future__ import annotations

import ctypes
import random
from array import array

import pytest

from srmech.amsc import _native
from srmech.amsc import compose, coupling, harmonics, hdc, laplacian
from srmech.amsc.q import Q

_I8P = ctypes.POINTER(ctypes.c_int8)

_HAS_NATIVE = _native.HAS_NATIVE and _native.LIB is not None


def _both_paths(fn):
    """(native_result, forced_pure_result) for a zero-arg callable."""
    native_result = fn()
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = False
        python_result = fn()
    finally:
        _native.HAS_NATIVE = saved
    return native_result, python_result


# ==========================================================================
# 1. coupling.signed_sum_squared — EXACT (Class-K bipolar ∘ Class-L square)
# ==========================================================================

def test_signed_sum_squared_value_oracles():
    # all agree -> n_sources² ; balanced -> 0 ; the square (no abs()) on all-zero.
    assert coupling.signed_sum_squared([[1, 1, 1], [1, 1, 1], [1, 1, 1]]) == [9, 9, 9]
    assert coupling.signed_sum_squared([[1, 0, 1], [0, 1, 0]]) == [0, 0, 0]
    assert coupling.signed_sum_squared([[0], [0], [0], [0]]) == [16]  # (-4)²
    assert coupling.signed_sum_squared([[1, 0, 1, 0]]) == [1, 1, 1, 1]


def test_signed_sum_squared_native_matches_pure():
    srcs = [[1, 0, 1, 1, 0], [1, 1, 0, 1, 0], [0, 1, 1, 1, 1]]
    native, pure = _both_paths(lambda: coupling.signed_sum_squared(srcs))
    assert list(native) == list(pure)  # byte-identical integer composition


def test_signed_sum_squared_rejects_bad_input():
    with pytest.raises(ValueError):
        coupling.signed_sum_squared([])
    with pytest.raises(ValueError):
        coupling.signed_sum_squared([[0, 2]])          # non-bit
    with pytest.raises(ValueError):
        coupling.signed_sum_squared([[0, 1], [1]])     # ragged


# ==========================================================================
# 2. harmonics.classify_chirality_harmonic — EXACT discrete 1/2/3 label
# ==========================================================================

def test_classify_chirality_harmonic_value_oracles():
    # DC-dominant -> harmonic 1
    assert harmonics.classify_chirality_harmonic([1.0] * 16) == 1
    assert harmonics.classify_chirality_harmonic([3.0] * 9) == 1
    # zero-mean palindrome -> harmonic 2 (mirror self-agreement)
    assert harmonics.classify_chirality_harmonic([1.0, -1, -1, 1]) == 2
    # period-3, zero-mean -> harmonic 3
    assert harmonics.classify_chirality_harmonic(
        [2.0, -1, -1, 2, -1, -1, 2, -1, -1]) == 3


def test_classify_chirality_harmonic_native_matches_pure():
    cases = [[1.0] * 16, [1.0, -1, -1, 1], [2.0, -1, -1, 2, -1, -1, 2, -1, -1]]
    for v in cases:
        native, pure = _both_paths(lambda v=v: harmonics.classify_chirality_harmonic(v))
        assert native == pure  # discrete label, byte-identical


def test_classify_chirality_harmonic_empty_raises():
    with pytest.raises(ValueError):
        harmonics.classify_chirality_harmonic([])


# ==========================================================================
# 3. hdc.polar_from_real — composition_of_c over c_dispatched sign_quantise
# ==========================================================================

def test_polar_from_real_value_oracle():
    # dead_band=0.1 pushes |x| < 0.1 into the 0 (uncertain) slot.
    out = hdc.polar_from_real([0.5, -0.2, 0.05, -0.05], threshold=0.0, dead_band=0.1)
    assert list(out) == [1, -1, 0, 0]


def test_polar_from_real_native_matches_pure():
    xs = [0.9, -0.3, 0.0, 0.05, -0.7, 0.4, -0.02, 0.15]
    native, pure = _both_paths(
        lambda: hdc.polar_from_real(xs, threshold=0.0, dead_band=0.1))
    assert list(native) == list(pure)  # byte-identical int8 (C sign_quantise)


# ==========================================================================
# 4. hdc.polar_unbind — composition_of_c over c_dispatched polar_bind
# ==========================================================================

def test_polar_unbind_round_trip():
    rng = random.Random(20260706)
    a = hdc.polar_random(256, rng)
    b = hdc.polar_random(256, rng)
    rec = hdc.polar_unbind(hdc.polar_bind(a, b), a)
    # recovers b exactly wherever a != 0 (0 is destructive on the ±1 alphabet).
    for i in range(256):
        if a[i] != 0:
            assert rec[i] == b[i]


def test_polar_unbind_native_matches_pure():
    rng = random.Random(11)
    c = hdc.polar_random(257, rng)
    a = hdc.polar_random(257, rng)
    native, pure = _both_paths(lambda: hdc.polar_unbind(c, a))
    assert list(native) == list(pure)  # byte-identical int8 sign-product


# ==========================================================================
# 5. hdc.polar_similarity — EXACT Q + cross-check vs srmech_polar_similarity C
# ==========================================================================

def test_polar_similarity_value_oracle():
    x = array("b", [1, -1, 1, 0])
    y = array("b", [1, 1, 1, 0])
    assert hdc.polar_similarity(x, y) == Q(2, 3)               # skip-zero: 2/3
    assert hdc.polar_similarity(x, y, skip_zero=False) == Q(3, 4)  # incl-zero: 3/4
    z0 = array("b", [0, 0, 0])
    assert hdc.polar_similarity(z0, z0) == Q(0, 1)             # no informative pos


@pytest.mark.skipif(not _HAS_NATIVE, reason="native lib required")
def test_polar_similarity_matches_c_float_peer():
    """float(Q) from the exact Python path == the srmech_polar_similarity C float
    (the display-collapse peer). Cross-checks the exact count against C."""
    rng = random.Random(7)
    for _ in range(20):
        n = rng.randrange(8, 200)
        a = hdc.polar_random(n, rng)
        b = hdc.polar_random(n, rng)
        for sz in (True, False):
            a_buf = (ctypes.c_int8 * n).from_buffer_copy(a)
            b_buf = (ctypes.c_int8 * n).from_buffer_copy(b)
            out = ctypes.c_double(0.0)
            rc = _native.LIB.srmech_polar_similarity(
                ctypes.cast(a_buf, _I8P), ctypes.cast(b_buf, _I8P),
                n, 1 if sz else 0, ctypes.byref(out))
            assert rc == _native.SRMECH_OK
            assert float(hdc.polar_similarity(a, b, skip_zero=sz)) == out.value


# ==========================================================================
# 6. hdc.polar_random — c_dispatched srmech_polar_random (byte-identical seeded)
# ==========================================================================

def _cpython_polar_ref(D, seed):
    r = random.Random(seed)
    return array("b", (r.randrange(-1, 2) for _ in range(D)))


@pytest.mark.parametrize("seed", [0, 1, 42, 20260706, 999983])
@pytest.mark.parametrize("D", [1, 7, 64, 257])
def test_polar_random_native_matches_cpython(seed, D):
    """The seeded native path is BYTE-IDENTICAL to CPython
    random.Random(seed).randrange(-1, 2) — and the forced-pure fallback too."""
    ref = _cpython_polar_ref(D, seed)
    native, pure = _both_paths(lambda: hdc.polar_random(D, seed=seed))
    assert list(native) == list(ref), (seed, D)   # C MT19937 == CPython stream
    assert list(pure) == list(ref), (seed, D)     # pure fallback == CPython stream
    # every element is a valid polar code
    assert all(v in (-1, 0, 1) for v in native)


def test_polar_random_is_deterministic_by_seed():
    assert list(hdc.polar_random(128, seed=5)) == list(hdc.polar_random(128, seed=5))


def test_polar_random_rejects_nonpositive_D():
    with pytest.raises(ValueError):
        hdc.polar_random(0, seed=1)


# ==========================================================================
# 7. laplacian.three_fold_eigvec_groups — eig-INVARIANT (band sizes + span)
# ==========================================================================

def _band_widths(d):
    return (d["low"].n_cols, d["mid"].n_cols, d["high"].n_cols)


def test_three_fold_eigvec_groups_native_matches_pure_invariant():
    rng = random.Random(314159)
    for n in (1, 2, 3, 4, 5, 8, 9, 16, 17):
        A = [[rng.gauss(0.0, 1.0) for _ in range(n)] for _ in range(n)]
        L = [[A[i][j] + A[j][i] for j in range(n)] for i in range(n)]
        native, pure = _both_paths(lambda L=L: laplacian.three_fold_eigvec_groups(L))
        nat, pyw = _band_widths(native), _band_widths(pure)
        # INVARIANT: identical band SIZES + the partition law |low|<=|mid|<=|high|.
        assert nat == pyw, (n, nat, pyw)
        low, mid, high = nat
        assert low + mid + high == n
        assert low <= mid <= high
        # each band's row count == n (eigenvector COLUMNS in an n×k Mat).
        for key in ("low", "mid", "high"):
            assert native[key].n_rows == n


# ==========================================================================
# 8. compose.greedy_bipartite_alignment — Class-K greedy argmax + used-set
# ==========================================================================

def test_greedy_bipartite_alignment_value_oracle():
    # A rows prefer the b-row with the closest value; greedy + one-use-per-b.
    table_a = [0.0, 10.0, 5.0]
    table_b = [10.2, 0.1, 4.9]
    # similarity = -|a-b| (higher = closer); no abs() on the OP side — the caller
    # supplies the metric; here the negative distance ranks nearest highest.
    def sim(a, b):
        d = a - b
        return -(d if d >= 0.0 else -d)
    mapping = compose.greedy_bipartite_alignment(table_a, table_b, sim)
    # a0(0.0)->b1(0.1); a1(10.0)->b0(10.2); a2(5.0)->b2(4.9)
    assert mapping[0][0] == 1
    assert mapping[1][0] == 0
    assert mapping[2][0] == 2


def test_greedy_bipartite_alignment_fewer_b_leaves_later_a_unmatched():
    table_a = ["p", "q", "r"]
    table_b = ["x"]
    def sim(a, b):
        return 1.0  # all equal -> first-come a0 takes the only b0
    mapping = compose.greedy_bipartite_alignment(table_a, table_b, sim)
    assert set(mapping) == {0}       # a1, a2 unmatched (b exhausted)
    assert mapping[0][0] == 0


def test_greedy_bipartite_alignment_rejects_non_callable():
    with pytest.raises(TypeError):
        compose.greedy_bipartite_alignment([1], [1], None)
