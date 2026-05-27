"""Polar {-1, 0, +1} Class M variant — algebraic properties + C/Python parity.

The polar variant (v0.4.3rc1) is rank-1 Class M with an *absorbing* zero
(Class M ∘ Class K): int8 hypervectors over {-1, 0, +1}, bind = multiplicative
sign-product (0 absorbing), bundle = sticky majority (ties → 0). See
``srmech.amsc.hdc.polar_*`` + UPSTREAM_NOTES §5.

Two tiers:
  - Algebraic-property tests on the numpy reference — always run.
  - C↔Python bit-exact parity — run only when the native polar surface is
    present (built in the cibuildwheel matrix; skipped on a pure-Python or
    pre-polar install).
"""

import ctypes

import numpy as np
import pytest

from srmech.amsc import _native
from srmech.amsc import hdc


_POLAR_NATIVE = _native.HAS_NATIVE and hasattr(_native.LIB, "srmech_polar_bind")
_requires_native = pytest.mark.skipif(
    not _POLAR_NATIVE,
    reason="native polar surface not present (pure-Python or pre-polar lib)",
)


# --------------------------------------------------------------------------
# Algebraic properties (numpy reference) — always run
# --------------------------------------------------------------------------

def test_polar_bind_zero_absorbing():
    rng = np.random.default_rng(1)
    a = hdc.polar_random(128, rng)
    b = hdc.polar_random(128, rng)
    c = hdc.polar_bind(a, b)
    assert set(np.unique(c).tolist()) <= {-1, 0, 1}
    # 0 is absorbing: wherever either operand is 0, the product is 0.
    assert (c[(a == 0) | (b == 0)] == 0).all()
    # On the joint ±1 sub-alphabet it is the ordinary sign-product.
    both_nz = (a != 0) & (b != 0)
    assert (c[both_nz] == (a[both_nz] * b[both_nz])).all()


def test_polar_bind_commutative():
    rng = np.random.default_rng(2)
    a = hdc.polar_random(64, rng)
    b = hdc.polar_random(64, rng)
    assert (hdc.polar_bind(a, b) == hdc.polar_bind(b, a)).all()


def test_polar_bind_associative():
    rng = np.random.default_rng(3)
    a, b, c = (hdc.polar_random(64, rng) for _ in range(3))
    left = hdc.polar_bind(hdc.polar_bind(a, b), c)
    right = hdc.polar_bind(a, hdc.polar_bind(b, c))
    assert (left == right).all()


def test_polar_unbind_recovers_on_pm1_only():
    rng = np.random.default_rng(4)
    a = hdc.polar_random(256, rng)
    b = hdc.polar_random(256, rng)
    rec = hdc.polar_unbind(hdc.polar_bind(a, b), a)
    nz = a != 0
    assert (rec[nz] == b[nz]).all()          # self-inverse on ±1
    assert (rec[~nz] == 0).all()             # 0 is destructive


def test_polar_bundle_sticky_majority_ties_to_zero():
    v1 = np.array([1, 1, 0, -1], dtype=np.int8)
    v2 = np.array([1, -1, 0, -1], dtype=np.int8)
    v3 = np.array([-1, -1, 0, 1], dtype=np.int8)
    # sums: +1, -1, 0, -1  → +1, -1, 0, -1
    assert list(hdc.polar_bundle(v1, v2, v3)) == [1, -1, 0, -1]
    # even count with an exact tie → 0
    assert list(hdc.polar_bundle(np.array([1], dtype=np.int8),
                                 np.array([-1], dtype=np.int8))) == [0]


def test_polar_similarity_skip_and_include_zero():
    x = np.array([1, 0, -1, 1], dtype=np.int8)
    y = np.array([1, 0, -1, -1], dtype=np.int8)
    # skip-zero: positions where both != 0 → idx 0, 2, 3; matches at 0, 2 → 2/3
    assert hdc.polar_similarity(x, y) == pytest.approx(2.0 / 3.0)
    # include-zero: idx1 (0 == 0) also counts → 3/4
    assert hdc.polar_similarity(x, y, skip_zero=False) == pytest.approx(0.75)
    # no jointly-informative positions → 0.0
    z0 = np.array([0, 0], dtype=np.int8)
    assert hdc.polar_similarity(z0, z0) == 0.0


def test_polar_density():
    assert hdc.polar_density(np.array([1, 0, -1, 1], dtype=np.int8)) == pytest.approx(0.75)
    assert hdc.polar_density(np.array([0, 0, 0], dtype=np.int8)) == 0.0
    assert hdc.polar_density(np.array([1, -1], dtype=np.int8)) == 1.0


def test_polar_from_real_bridge_dead_band():
    # 0.5 → +1, -0.2 → -1, ±0.05 within dead-band → 0
    out = hdc.polar_from_real(
        np.array([0.5, -0.2, 0.05, -0.05]), threshold=0.0, dead_band=0.1
    )
    assert list(out) == [1, -1, 0, 0]
    assert out.dtype == np.int8


def test_polar_validation_rejects_out_of_alphabet():
    with pytest.raises(ValueError):
        hdc.polar_bind(np.array([2, 0], dtype=np.int8), np.array([1, 1], dtype=np.int8))
    with pytest.raises(ValueError):
        hdc.polar_bundle()  # empty


# --------------------------------------------------------------------------
# C ↔ Python bit-exact parity (native only)
# --------------------------------------------------------------------------

def _c_bind(a, b):
    n = a.size
    a_buf = (ctypes.c_int8 * n).from_buffer_copy(a.astype(np.int8).tobytes())
    b_buf = (ctypes.c_int8 * n).from_buffer_copy(b.astype(np.int8).tobytes())
    out = (ctypes.c_int8 * n)()
    rc = _native.LIB.srmech_polar_bind(a_buf, b_buf, n, out)
    assert rc == _native.SRMECH_OK
    return np.frombuffer(bytes(out), dtype=np.int8).copy()


def _c_bundle(vecs):
    n = vecs[0].size
    nv = len(vecs)
    bufs = [(ctypes.c_int8 * n).from_buffer_copy(v.astype(np.int8).tobytes()) for v in vecs]
    ptr_arr = (ctypes.POINTER(ctypes.c_int8) * nv)(
        *(ctypes.cast(b, ctypes.POINTER(ctypes.c_int8)) for b in bufs)
    )
    out = (ctypes.c_int8 * n)()
    rc = _native.LIB.srmech_polar_bundle(ptr_arr, nv, n, out)
    assert rc == _native.SRMECH_OK
    return np.frombuffer(bytes(out), dtype=np.int8).copy()


def _c_similarity(a, b, skip_zero):
    n = a.size
    a_buf = (ctypes.c_int8 * n).from_buffer_copy(a.astype(np.int8).tobytes())
    b_buf = (ctypes.c_int8 * n).from_buffer_copy(b.astype(np.int8).tobytes())
    out = ctypes.c_double(0.0)
    rc = _native.LIB.srmech_polar_similarity(
        a_buf, b_buf, n, 1 if skip_zero else 0, ctypes.byref(out)
    )
    assert rc == _native.SRMECH_OK
    return out.value


def _c_density(v):
    n = v.size
    v_buf = (ctypes.c_int8 * n).from_buffer_copy(v.astype(np.int8).tobytes())
    out = ctypes.c_double(0.0)
    rc = _native.LIB.srmech_polar_density(v_buf, n, ctypes.byref(out))
    assert rc == _native.SRMECH_OK
    return out.value


@_requires_native
def test_parity_bind():
    rng = np.random.default_rng(10)
    for _ in range(20):
        a = hdc.polar_random(257, rng)
        b = hdc.polar_random(257, rng)
        assert (_c_bind(a, b) == hdc.polar_bind(a, b)).all()


@_requires_native
def test_parity_bundle():
    rng = np.random.default_rng(11)
    for nv in (1, 2, 3, 8, 33):
        vecs = [hdc.polar_random(129, rng) for _ in range(nv)]
        assert (_c_bundle(vecs) == hdc.polar_bundle(*vecs)).all()


@_requires_native
def test_parity_similarity():
    rng = np.random.default_rng(12)
    for _ in range(20):
        a = hdc.polar_random(200, rng)
        b = hdc.polar_random(200, rng)
        for sz in (True, False):
            assert _c_similarity(a, b, sz) == pytest.approx(hdc.polar_similarity(a, b, skip_zero=sz))


@_requires_native
def test_parity_density():
    rng = np.random.default_rng(13)
    for _ in range(20):
        v = hdc.polar_random(200, rng)
        assert _c_density(v) == pytest.approx(hdc.polar_density(v))
