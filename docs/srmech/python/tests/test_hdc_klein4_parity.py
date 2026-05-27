"""Klein-4 {0,1,2,3} Class M variant — algebraic properties + C/Python parity.

Klein-4 (v0.4.3rc2) is rank-2 abelian Class M over (F₂)² = Z₂×Z₂: uint8
hypervectors over {0,1,2,3}, bind = component-wise XOR (self-inverse, abelian,
identity 0), bundle = per-bit majority (ties → 0). The four states map to the
four (γ₅, iω₇) chirality sectors. See ``srmech.amsc.hdc.klein4_*`` +
UPSTREAM_NOTES §4.

Two tiers: numpy-reference property tests (always run) + C↔Python bit-exact
parity (native only; built in the cibuildwheel matrix).
"""

import ctypes

import numpy as np
import pytest

from srmech.amsc import _native
from srmech.amsc import hdc


_K4_NATIVE = _native.HAS_NATIVE and hasattr(_native.LIB, "srmech_klein4_bind")
_requires_native = pytest.mark.skipif(
    not _K4_NATIVE,
    reason="native klein-4 surface not present (pure-Python or pre-klein4 lib)",
)


# --------------------------------------------------------------------------
# Algebraic properties (numpy reference) — always run
# --------------------------------------------------------------------------

def test_klein4_group_axioms():
    rng = np.random.default_rng(1)
    a, b, c = (hdc.klein4_random(128, rng) for _ in range(3))
    assert set(np.unique(a).tolist()) <= {0, 1, 2, 3}
    # identity 0, self-inverse, commutative, associative
    assert (hdc.klein4_bind(a, np.zeros_like(a)) == a).all()
    assert (hdc.klein4_bind(a, hdc.klein4_bind(a, b)) == b).all()
    assert (hdc.klein4_bind(a, b) == hdc.klein4_bind(b, a)).all()
    assert (hdc.klein4_bind(hdc.klein4_bind(a, b), c)
            == hdc.klein4_bind(a, hdc.klein4_bind(b, c))).all()
    # every element is its own inverse (Klein-four group property)
    assert (hdc.klein4_bind(a, a) == 0).all()


def test_klein4_unbind():
    rng = np.random.default_rng(2)
    a = hdc.klein4_random(256, rng); b = hdc.klein4_random(256, rng)
    assert (hdc.klein4_unbind(hdc.klein4_bind(a, b), a) == b).all()


def test_klein4_chirality_flips():
    rng = np.random.default_rng(3)
    a = hdc.klein4_random(64, rng)
    # γ₅ = XOR 2, iω₇ = XOR 1, CPT = XOR 3 = both flips composed
    assert (hdc.klein4_chirality_flip_omega7(hdc.klein4_chirality_flip_gamma5(a))
            == hdc.klein4_cpt_mirror(a)).all()
    # each flip is an involution
    for flip in (hdc.klein4_chirality_flip_gamma5,
                 hdc.klein4_chirality_flip_omega7,
                 hdc.klein4_cpt_mirror):
        assert (flip(flip(a)) == a).all()
    # explicit sector map
    base = np.array([0, 1, 2, 3], dtype=np.uint8)
    assert list(hdc.klein4_chirality_flip_gamma5(base)) == [2, 3, 0, 1]
    assert list(hdc.klein4_chirality_flip_omega7(base)) == [1, 0, 3, 2]
    assert list(hdc.klein4_cpt_mirror(base)) == [3, 2, 1, 0]


def test_klein4_bundle_per_bit_majority():
    v1 = np.array([0, 3, 1], dtype=np.uint8)
    v2 = np.array([0, 3, 2], dtype=np.uint8)
    v3 = np.array([1, 0, 3], dtype=np.uint8)
    # pos0: bit0 {0,0,1}->0, bit1 {0,0,0}->0 => 0
    # pos1: states 3,3,0: bit0 {1,1,0}->1, bit1 {1,1,0}->1 => 3
    # pos2: states 1,2,3: bit0 {1,0,1}->1, bit1 {0,1,1}->1 => 3
    assert list(hdc.klein4_bundle(v1, v2, v3)) == [0, 3, 3]
    # even count, exact tie on a bit → 0
    assert list(hdc.klein4_bundle(np.array([1], np.uint8), np.array([2], np.uint8))) == [0]


def test_klein4_similarity_and_sector_count():
    rng = np.random.default_rng(4)
    a = hdc.klein4_random(200, rng)
    assert hdc.klein4_similarity(a, a) == 1.0
    x = np.array([0, 1, 2, 3], np.uint8); y = np.array([0, 1, 3, 3], np.uint8)
    assert hdc.klein4_similarity(x, y) == pytest.approx(0.75)
    assert hdc.klein4_sector_count(np.array([0, 0, 1, 2, 2, 2, 3], np.uint8)).tolist() == [2, 1, 3, 1]


def test_klein4_validation():
    with pytest.raises(ValueError):
        hdc.klein4_bind(np.array([4, 0], np.uint8), np.array([1, 1], np.uint8))
    with pytest.raises(ValueError):
        hdc.klein4_bundle()


# --------------------------------------------------------------------------
# C ↔ Python bit-exact parity (native only)
# --------------------------------------------------------------------------

def _c_bind(a, b):
    n = a.size
    ab = (ctypes.c_uint8 * n).from_buffer_copy(a.astype(np.uint8).tobytes())
    bb = (ctypes.c_uint8 * n).from_buffer_copy(b.astype(np.uint8).tobytes())
    out = (ctypes.c_uint8 * n)()
    assert _native.LIB.srmech_klein4_bind(ab, bb, n, out) == _native.SRMECH_OK
    return np.frombuffer(bytes(out), dtype=np.uint8).copy()


def _c_bundle(vecs):
    n = vecs[0].size; nv = len(vecs)
    bufs = [(ctypes.c_uint8 * n).from_buffer_copy(v.astype(np.uint8).tobytes()) for v in vecs]
    ptr = (ctypes.POINTER(ctypes.c_uint8) * nv)(
        *(ctypes.cast(b, ctypes.POINTER(ctypes.c_uint8)) for b in bufs)
    )
    out = (ctypes.c_uint8 * n)()
    assert _native.LIB.srmech_klein4_bundle(ptr, nv, n, out) == _native.SRMECH_OK
    return np.frombuffer(bytes(out), dtype=np.uint8).copy()


def _c_similarity(a, b):
    n = a.size
    ab = (ctypes.c_uint8 * n).from_buffer_copy(a.astype(np.uint8).tobytes())
    bb = (ctypes.c_uint8 * n).from_buffer_copy(b.astype(np.uint8).tobytes())
    out = ctypes.c_double(0.0)
    assert _native.LIB.srmech_klein4_similarity(ab, bb, n, ctypes.byref(out)) == _native.SRMECH_OK
    return out.value


@_requires_native
def test_parity_klein4_bind():
    rng = np.random.default_rng(10)
    for _ in range(20):
        a = hdc.klein4_random(257, rng); b = hdc.klein4_random(257, rng)
        assert (_c_bind(a, b) == hdc.klein4_bind(a, b)).all()


@_requires_native
def test_parity_klein4_bundle():
    rng = np.random.default_rng(11)
    for nv in (1, 2, 3, 8, 33):
        vecs = [hdc.klein4_random(129, rng) for _ in range(nv)]
        assert (_c_bundle(vecs) == hdc.klein4_bundle(*vecs)).all()


@_requires_native
def test_parity_klein4_similarity():
    rng = np.random.default_rng(12)
    for _ in range(20):
        a = hdc.klein4_random(200, rng); b = hdc.klein4_random(200, rng)
        assert _c_similarity(a, b) == pytest.approx(hdc.klein4_similarity(a, b))
