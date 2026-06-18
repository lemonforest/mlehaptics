"""Polar {-1, 0, +1} Class M variant — algebraic properties + C/Python parity.

The polar variant (v0.4.3rc1) is rank-1 Class M with an *absorbing* zero
(Class M ∘ Class K): int8 hypervectors over {-1, 0, +1}, bind = multiplicative
sign-product (0 absorbing), bundle = sticky majority (ties → 0). See
``srmech.amsc.hdc.polar_*`` + UPSTREAM_NOTES §5.

Two tiers:
  - Algebraic-property tests on the substrate reference — always run.
  - C↔Python bit-exact parity — run only when the native polar surface is
    present (built in the cibuildwheel matrix; skipped on a pure-Python or
    pre-polar install).

rc125 (numpy-free, #564): this test is itself numpy-FREE — the polar family
carries ``array('b')`` (int8) buffers and ``polar_random`` takes a stdlib
``random.Random``; the C parity helpers marshal the ``array('b')`` straight
into ctypes (no numpy oracle, per
`[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]`).
"""

import ctypes
import random
from array import array

import pytest

from srmech.amsc import _native
from srmech.amsc import hdc
from srmech.amsc.q import Q


_POLAR_NATIVE = _native.HAS_NATIVE and hasattr(_native.LIB, "srmech_polar_bind")
_requires_native = pytest.mark.skipif(
    not _POLAR_NATIVE,
    reason="native polar surface not present (pure-Python or pre-polar lib)",
)

_I8P = ctypes.POINTER(ctypes.c_int8)


# --------------------------------------------------------------------------
# Algebraic properties (substrate reference) — always run
# --------------------------------------------------------------------------

def test_polar_bind_zero_absorbing():
    rng = random.Random(1)
    a = hdc.polar_random(128, rng)
    b = hdc.polar_random(128, rng)
    c = hdc.polar_bind(a, b)
    assert set(c) <= {-1, 0, 1}
    # 0 is absorbing: wherever either operand is 0, the product is 0.
    assert all(c[i] == 0 for i in range(len(c)) if a[i] == 0 or b[i] == 0)
    # On the joint ±1 sub-alphabet it is the ordinary sign-product.
    assert all(c[i] == a[i] * b[i] for i in range(len(c)) if a[i] != 0 and b[i] != 0)


def test_polar_bind_commutative():
    rng = random.Random(2)
    a = hdc.polar_random(64, rng)
    b = hdc.polar_random(64, rng)
    assert list(hdc.polar_bind(a, b)) == list(hdc.polar_bind(b, a))


def test_polar_bind_associative():
    rng = random.Random(3)
    a, b, c = (hdc.polar_random(64, rng) for _ in range(3))
    left = hdc.polar_bind(hdc.polar_bind(a, b), c)
    right = hdc.polar_bind(a, hdc.polar_bind(b, c))
    assert list(left) == list(right)


def test_polar_unbind_recovers_on_pm1_only():
    rng = random.Random(4)
    a = hdc.polar_random(256, rng)
    b = hdc.polar_random(256, rng)
    rec = hdc.polar_unbind(hdc.polar_bind(a, b), a)
    assert all(rec[i] == b[i] for i in range(len(a)) if a[i] != 0)   # self-inverse on ±1
    assert all(rec[i] == 0 for i in range(len(a)) if a[i] == 0)      # 0 is destructive


def test_polar_bundle_sticky_majority_ties_to_zero():
    v1 = array("b", [1, 1, 0, -1])
    v2 = array("b", [1, -1, 0, -1])
    v3 = array("b", [-1, -1, 0, 1])
    # sums: +1, -1, 0, -1  → +1, -1, 0, -1
    assert list(hdc.polar_bundle(v1, v2, v3)) == [1, -1, 0, -1]
    # even count with an exact tie → 0
    assert list(hdc.polar_bundle(array("b", [1]), array("b", [-1]))) == [0]


def test_polar_similarity_skip_and_include_zero():
    x = array("b", [1, 0, -1, 1])
    y = array("b", [1, 0, -1, -1])
    # skip-zero: positions where both != 0 → idx 0, 2, 3; matches at 0, 2 → 2/3.
    # v0.9.0 (F868): polar_similarity returns the EXACT Q — 2/3 is NOT a finite
    # float (off by 1 ULP), so assert the exact rational, never pytest.approx.
    assert hdc.polar_similarity(x, y) == Q(2, 3)
    # include-zero: idx1 (0 == 0) also counts → 3/4.
    assert hdc.polar_similarity(x, y, skip_zero=False) == Q(3, 4)
    # no jointly-informative positions → exact 0.
    z0 = array("b", [0, 0])
    assert hdc.polar_similarity(z0, z0) == Q(0, 1)


def test_polar_density():
    assert hdc.polar_density(array("b", [1, 0, -1, 1])) == Q(3, 4)
    assert hdc.polar_density(array("b", [0, 0, 0])) == Q(0, 1)
    assert hdc.polar_density(array("b", [1, -1])) == Q(1, 1)


def test_polar_from_real_bridge_dead_band():
    # 0.5 → +1, -0.2 → -1, ±0.05 within dead-band → 0
    out = hdc.polar_from_real([0.5, -0.2, 0.05, -0.05], threshold=0.0, dead_band=0.1)
    assert list(out) == [1, -1, 0, 0]
    assert out.typecode == "b"   # int8 array (was an int8 ndarray)


def test_polar_validation_rejects_out_of_alphabet():
    with pytest.raises(ValueError):
        hdc.polar_bind(array("b", [2, 0]), array("b", [1, 1]))
    with pytest.raises(ValueError):
        hdc.polar_bundle()  # empty


# --------------------------------------------------------------------------
# C ↔ Python bit-exact parity (native only)
# --------------------------------------------------------------------------

def _c_bind(a, b):
    n = len(a)
    a_buf = (ctypes.c_int8 * n).from_buffer_copy(a)
    b_buf = (ctypes.c_int8 * n).from_buffer_copy(b)
    out = (ctypes.c_int8 * n)()
    rc = _native.LIB.srmech_polar_bind(
        ctypes.cast(a_buf, _I8P), ctypes.cast(b_buf, _I8P), n, ctypes.cast(out, _I8P))
    assert rc == _native.SRMECH_OK
    return array("b", out)


def _c_bundle(vecs):
    n = len(vecs[0])
    nv = len(vecs)
    bufs = [(ctypes.c_int8 * n).from_buffer_copy(v) for v in vecs]
    ptr_arr = (_I8P * nv)(*(ctypes.cast(b, _I8P) for b in bufs))
    out = (ctypes.c_int8 * n)()
    rc = _native.LIB.srmech_polar_bundle(ptr_arr, nv, n, ctypes.cast(out, _I8P))
    assert rc == _native.SRMECH_OK
    return array("b", out)


def _c_similarity(a, b, skip_zero):
    n = len(a)
    a_buf = (ctypes.c_int8 * n).from_buffer_copy(a)
    b_buf = (ctypes.c_int8 * n).from_buffer_copy(b)
    out = ctypes.c_double(0.0)
    rc = _native.LIB.srmech_polar_similarity(
        ctypes.cast(a_buf, _I8P), ctypes.cast(b_buf, _I8P), n,
        1 if skip_zero else 0, ctypes.byref(out)
    )
    assert rc == _native.SRMECH_OK
    return out.value


def _c_density(v):
    n = len(v)
    v_buf = (ctypes.c_int8 * n).from_buffer_copy(v)
    out = ctypes.c_double(0.0)
    rc = _native.LIB.srmech_polar_density(
        ctypes.cast(v_buf, _I8P), n, ctypes.byref(out))
    assert rc == _native.SRMECH_OK
    return out.value


@_requires_native
def test_parity_bind():
    rng = random.Random(10)
    for _ in range(20):
        a = hdc.polar_random(257, rng)
        b = hdc.polar_random(257, rng)
        assert list(_c_bind(a, b)) == list(hdc.polar_bind(a, b))


@_requires_native
def test_parity_bundle():
    rng = random.Random(11)
    for nv in (1, 2, 3, 8, 33):
        vecs = [hdc.polar_random(129, rng) for _ in range(nv)]
        assert list(_c_bundle(vecs)) == list(hdc.polar_bundle(*vecs))


@_requires_native
def test_parity_similarity():
    rng = random.Random(12)
    for _ in range(20):
        a = hdc.polar_random(200, rng)
        b = hdc.polar_random(200, rng)
        for sz in (True, False):
            assert _c_similarity(a, b, sz) == pytest.approx(
                hdc.polar_similarity(a, b, skip_zero=sz))


@_requires_native
def test_parity_density():
    rng = random.Random(13)
    for _ in range(20):
        v = hdc.polar_random(200, rng)
        assert _c_density(v) == pytest.approx(hdc.polar_density(v))
